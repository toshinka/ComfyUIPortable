/**
 * page_composite_index.mjs — Persistent History Index for Page Composite Manifests.
 *
 * Provides:
 * 1. Validated composite registration (indexComposite).
 * 2. Document/page history lookup (listByPage, listByPlanDigest).
 * 3. Deterministic ordering: created_at descending, composite_id descending tie-breaker.
 * 4. Idempotent composite_id indexing with fail-closed consistency checks.
 * 5. Validated composite resolution through PageCompositeStore (resolveComposite).
 *
 * Implements atomic temporary-write + rename publication and in-process concurrency serialization.
 */

import fs from "node:fs/promises";
import path from "node:path";
import { randomUUID } from "node:crypto";
import { fileURLToPath } from "node:url";

import { PageCompositeStore, PageCompositeStoreError } from "./page_composite_store.mjs";

const here = path.dirname(fileURLToPath(import.meta.url));
export const DEFAULT_PAGE_COMPOSITE_INDEX_DIR = path.resolve(here, "..", "data", "page_composites_index");

export const INDEX_SCHEMA_ID = "TEGAKI_PAGE_COMPOSITE_INDEX";
export const INDEX_SCHEMA_VERSION = "1.0.0";

const UUID_V4_REGEX = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
const HEX_SHA256_REGEX = /^[0-9a-f]{64}$/i;

export class PageCompositeIndexError extends Error {
    constructor(code, message, options = {}) {
        super(message, options);
        this.name = "PageCompositeIndexError";
        this.code = code;
        if (options.composite_id) {
            this.composite_id = options.composite_id;
        }
    }
}

function isNonEmptyString(val) {
    return typeof val === "string" && val.trim().length > 0;
}

function isObject(val) {
    return val !== null && typeof val === "object" && !Array.isArray(val);
}

export class PageCompositeIndex {
    /**
     * @param {object} [options]
     * @param {string} [options.directory=DEFAULT_PAGE_COMPOSITE_INDEX_DIR]
     * @param {PageCompositeStore} [options.store]
     * @param {typeof fs} [options.fsApi=fs]
     */
    constructor({
        directory = DEFAULT_PAGE_COMPOSITE_INDEX_DIR,
        store = null,
        fsApi = fs,
    } = {}) {
        this.directory = path.resolve(directory);
        this.store = store || new PageCompositeStore();
        this.fs = fsApi;
        this.tail = Promise.resolve();
    }

    _file() {
        return path.join(this.directory, "page_composite_index.json");
    }

    _exclusive(work) {
        const result = this.tail.then(work);
        this.tail = result.catch(() => {});
        return result;
    }

    _validateCompositeId(id) {
        if (!isNonEmptyString(id) || !UUID_V4_REGEX.test(id)) {
            throw new PageCompositeIndexError(
                "INVALID_COMPOSITE_ID",
                `composite_id must be an RFC 4122 UUIDv4 string, got '${id}'`
            );
        }
    }

    async _readIndex() {
        const file = this._file();
        let raw;
        try {
            raw = await this.fs.readFile(file, "utf8");
        } catch (err) {
            if (err.code === "ENOENT") {
                return {
                    schema_id: INDEX_SCHEMA_ID,
                    schema_version: INDEX_SCHEMA_VERSION,
                    entries: [],
                };
            }
            throw new PageCompositeIndexError(
                "INDEX_READ_FAILED",
                `Failed to read page composite index: ${err.message}`,
                { cause: err }
            );
        }

        try {
            const data = JSON.parse(raw);
            if (!isObject(data) || data.schema_id !== INDEX_SCHEMA_ID || !Array.isArray(data.entries)) {
                throw new Error("Invalid index format or missing schema_id");
            }
            return data;
        } catch (err) {
            throw new PageCompositeIndexError(
                "INDEX_CORRUPT",
                `Malformed page composite index file: ${err.message}`,
                { cause: err }
            );
        }
    }

    async _writeIndex(data) {
        try {
            await this.fs.mkdir(this.directory, { recursive: true });
        } catch (err) {
            throw new PageCompositeIndexError(
                "INDEX_DIR_FAILED",
                `Failed to create index directory: ${err.message}`,
                { cause: err }
            );
        }

        const target = this._file();
        const temporary = path.join(this.directory, `page_composite_index.${randomUUID()}.tmp`);
        const serialized = JSON.stringify(data, null, 2) + "\n";

        let handle = null;
        let writeError = null;
        try {
            handle = await this.fs.open(temporary, "wx");
            await handle.writeFile(serialized, "utf8");
            await handle.sync();
        } catch (err) {
            writeError = err;
        } finally {
            if (handle) {
                try {
                    await handle.close();
                } catch (closeErr) {
                    writeError ??= closeErr;
                }
            }
        }

        if (writeError) {
            try { await this.fs.unlink(temporary); } catch {}
            throw new PageCompositeIndexError(
                "INDEX_WRITE_FAILED",
                `Failed to write temporary index file: ${writeError.message}`,
                { cause: writeError }
            );
        }

        try {
            await this.fs.rename(temporary, target);
        } catch (renameErr) {
            try { await this.fs.unlink(temporary); } catch {}
            throw new PageCompositeIndexError(
                "INDEX_PUBLISH_FAILED",
                `Failed to atomically publish page composite index: ${renameErr.message}`,
                { cause: renameErr }
            );
        }
    }

    /**
     * Indexes a validated stored composite by its composite_id.
     * Derives all index metadata from the authoritative stored manifest.
     *
     * @param {string} compositeId
     * @returns {Promise<object>} Indexed entry record
     */
    async indexComposite(compositeId) {
        this._validateCompositeId(compositeId);

        // 1. Authoritative metadata: load and validate from trusted PageCompositeStore
        let manifest;
        try {
            manifest = await this.store.getManifest(compositeId, { required: true });
        } catch (err) {
            if (err instanceof PageCompositeStoreError) {
                if (err.code === "COMPOSITE_NOT_FOUND") {
                    throw new PageCompositeIndexError(
                        "COMPOSITE_NOT_FOUND",
                        `Composite not found in store: ${compositeId}`,
                        { cause: err, composite_id: compositeId }
                    );
                }
                throw new PageCompositeIndexError(
                    "INVALID_COMPOSITE",
                    `Stored composite validation failed: ${err.message}`,
                    { cause: err, composite_id: compositeId }
                );
            }
            throw err;
        }

        const docId = manifest.owner?.document_id;
        const pageId = manifest.owner?.page_id;
        const planDigest = manifest.composition_plan_digest;
        const createdAt = manifest.created_at;

        if (!isNonEmptyString(docId) || !isNonEmptyString(pageId)) {
            throw new PageCompositeIndexError("INVALID_COMPOSITE", "Manifest missing owner document_id or page_id");
        }
        if (!isNonEmptyString(planDigest) || !HEX_SHA256_REGEX.test(planDigest)) {
            throw new PageCompositeIndexError("INVALID_COMPOSITE", "Manifest missing valid composition_plan_digest");
        }
        if (!isNonEmptyString(createdAt) || Number.isNaN(Date.parse(createdAt))) {
            throw new PageCompositeIndexError("INVALID_COMPOSITE", "Manifest missing valid created_at timestamp");
        }

        // 2. Concurrency-safe index update
        return this._exclusive(async () => {
            const indexData = await this._readIndex();

            const existing = indexData.entries.find(e => e.composite_id === compositeId);
            if (existing) {
                // Idempotence check: must match authoritative metadata
                if (
                    existing.document_id === docId &&
                    existing.page_id === pageId &&
                    existing.composition_plan_digest === planDigest &&
                    existing.created_at === createdAt
                ) {
                    return structuredClone(existing);
                }
                throw new PageCompositeIndexError(
                    "INDEX_CONSISTENCY_ERROR",
                    `Existing index entry for composite '${compositeId}' differs from authoritative store manifest`,
                    { composite_id: compositeId }
                );
            }

            const newEntry = {
                composite_id: compositeId,
                document_id: docId,
                page_id: pageId,
                composition_plan_digest: planDigest,
                created_at: createdAt,
            };

            indexData.entries.push(newEntry);
            await this._writeIndex(indexData);

            return structuredClone(newEntry);
        });
    }

    /**
     * Retrieves an index entry by composite_id.
     *
     * @param {string} compositeId
     * @returns {Promise<object|null>}
     */
    async getEntry(compositeId) {
        this._validateCompositeId(compositeId);
        const indexData = await this._readIndex();
        const entry = indexData.entries.find(e => e.composite_id === compositeId);
        return entry ? structuredClone(entry) : null;
    }

    /**
     * Lists indexed composite entries for a page, with deterministic ordering:
     * created_at descending, then composite_id descending as tie-breaker.
     *
     * @param {object} query
     * @param {string} query.document_id
     * @param {string} query.page_id
     * @param {string} [query.composition_plan_digest]
     * @returns {Promise<Array<object>>}
     */
    async listByPage({ document_id, page_id, composition_plan_digest = null } = {}) {
        if (!isNonEmptyString(document_id)) {
            throw new PageCompositeIndexError("INVALID_QUERY", "document_id is required");
        }
        if (!isNonEmptyString(page_id)) {
            throw new PageCompositeIndexError("INVALID_QUERY", "page_id is required");
        }
        if (composition_plan_digest !== null && (!isNonEmptyString(composition_plan_digest) || !HEX_SHA256_REGEX.test(composition_plan_digest))) {
            throw new PageCompositeIndexError("INVALID_QUERY", "composition_plan_digest must be a 64-hex SHA-256 string if provided");
        }

        const indexData = await this._readIndex();
        const filtered = indexData.entries.filter(e => {
            if (e.document_id !== document_id || e.page_id !== page_id) {
                return false;
            }
            if (composition_plan_digest && e.composition_plan_digest !== composition_plan_digest) {
                return false;
            }
            return true;
        });

        filtered.sort((a, b) => {
            const timeDiff = Date.parse(b.created_at) - Date.parse(a.created_at);
            if (timeDiff !== 0) return timeDiff;
            return b.composite_id.localeCompare(a.composite_id);
        });

        return structuredClone(filtered);
    }

    /**
     * Lists indexed composite entries matching a specific composition plan digest.
     *
     * @param {object} query
     * @param {string} query.document_id
     * @param {string} query.page_id
     * @param {string} query.composition_plan_digest
     * @returns {Promise<Array<object>>}
     */
    async listByPlanDigest({ document_id, page_id, composition_plan_digest } = {}) {
        if (!isNonEmptyString(composition_plan_digest) || !HEX_SHA256_REGEX.test(composition_plan_digest)) {
            throw new PageCompositeIndexError("INVALID_QUERY", "composition_plan_digest must be a 64-hex SHA-256 string");
        }
        return this.listByPage({ document_id, page_id, composition_plan_digest });
    }

    /**
     * Resolves a composite from the index and loads its validated data from PageCompositeStore.
     * Fails closed with INDEX_CONSISTENCY_ERROR if the index references a missing or corrupt bundle.
     *
     * @param {string} compositeId
     * @param {object} [options]
     * @param {boolean} [options.required=false]
     * @returns {Promise<{ entry: object, manifest: object, artifact_bytes: Buffer }|null>}
     */
    async resolveComposite(compositeId, { required = false } = {}) {
        this._validateCompositeId(compositeId);

        const entry = await this.getEntry(compositeId);
        if (!entry) {
            if (required) {
                throw new PageCompositeIndexError(
                    "COMPOSITE_NOT_INDEXED",
                    `Composite '${compositeId}' is not registered in the index`,
                    { composite_id: compositeId }
                );
            }
            return null;
        }

        let storeData;
        try {
            storeData = await this.store.getComposite(compositeId, { required: true });
        } catch (err) {
            throw new PageCompositeIndexError(
                "INDEX_CONSISTENCY_ERROR",
                `Index references missing or corrupt bundle in store for composite '${compositeId}': ${err.message}`,
                { cause: err, composite_id: compositeId }
            );
        }

        return {
            entry,
            manifest: storeData.manifest,
            artifact_bytes: storeData.artifact_bytes,
        };
    }

    /**
     * Alias for resolveComposite.
     */
    async getComposite(compositeId, options = {}) {
        return this.resolveComposite(compositeId, options);
    }
}
