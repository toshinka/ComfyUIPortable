/**
 * scene_result_index.mjs — Persistent query & association index for immutable Scene Result Manifests.
 *
 * Provides:
 * 1. Canonical job_id -> manifest_id association (immutable, conflict-checked).
 * 2. Deterministic Scene result history lookup (document_id, page_id, scene_id).
 * 3. Safe repeat retrieval of previously finalized results.
 * 4. Recovery mechanism for unindexed stored manifests (indexManifest).
 */

import fs from "node:fs/promises";
import path from "node:path";
import { randomUUID } from "node:crypto";
import { fileURLToPath } from "node:url";

import { SceneResultStore, SceneResultStoreError } from "./scene_result_store.mjs";

const here = path.dirname(fileURLToPath(import.meta.url));
export const DEFAULT_SCENE_RESULT_INDEX_DIR = path.resolve(here, "..", "data", "scene_results_index");

export const INDEX_SCHEMA_ID = "TEGAKI_SCENE_RESULT_INDEX";
export const INDEX_SCHEMA_VERSION = "1.0.0";

const UUID_V4_REGEX = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
const UUID_ANY_REGEX = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

export class SceneResultIndexError extends Error {
    constructor(code, message, options = {}) {
        super(message, options);
        this.name = "SceneResultIndexError";
        this.code = code;
    }
}

function isNonEmptyString(val) {
    return typeof val === "string" && val.trim().length > 0;
}

export class SceneResultIndex {
    /**
     * @param {object} [options]
     * @param {string} [options.directory] - Directory for storing index.json.
     * @param {SceneResultStore} [options.store] - Trusted manifest store.
     * @param {typeof fs} [options.fsApi] - Filesystem API implementation.
     */
    constructor({ directory = DEFAULT_SCENE_RESULT_INDEX_DIR, store = null, fsApi = fs } = {}) {
        this.directory = path.resolve(directory);
        this.store = store || new SceneResultStore();
        this.fs = fsApi;
        this.tail = Promise.resolve();
    }

    _file() {
        return path.join(this.directory, "scene_result_index.json");
    }

    _exclusive(work) {
        const result = this.tail.then(work);
        this.tail = result.catch(() => {});
        return result;
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
                    entries: []
                };
            }
            throw new SceneResultIndexError(
                "INDEX_READ_FAILED",
                `Failed to read result index: ${err.message}`,
                { cause: err }
            );
        }

        try {
            const data = JSON.parse(raw);
            if (!data || data.schema_id !== INDEX_SCHEMA_ID || !Array.isArray(data.entries)) {
                throw new Error("Invalid index format or schema ID");
            }
            return data;
        } catch (err) {
            throw new SceneResultIndexError(
                "INDEX_CORRUPT",
                `Malformed result index file: ${err.message}`,
                { cause: err }
            );
        }
    }

    async _writeIndex(data) {
        try {
            await this.fs.mkdir(this.directory, { recursive: true });
        } catch (err) {
            throw new SceneResultIndexError(
                "INDEX_DIR_FAILED",
                `Failed to create index directory: ${err.message}`,
                { cause: err }
            );
        }

        const target = this._file();
        const temporary = path.join(this.directory, `scene_result_index.${randomUUID()}.tmp`);
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
                } catch (closeError) {
                    writeError ??= closeError;
                }
            }
        }

        if (writeError) {
            try { await this.fs.unlink(temporary); } catch {}
            throw new SceneResultIndexError(
                "INDEX_WRITE_FAILED",
                `Failed to write temporary index file: ${writeError.message}`,
                { cause: writeError }
            );
        }

        try {
            await this.fs.rename(temporary, target);
        } catch (renameError) {
            try { await this.fs.unlink(temporary); } catch {}
            throw new SceneResultIndexError(
                "INDEX_PUBLISH_FAILED",
                `Failed to atomically publish index: ${renameError.message}`,
                { cause: renameError }
            );
        }
    }

    /**
     * Indexes a validated stored manifest by its manifest_id.
     * Derives all index metadata from the manifest content in SceneResultStore.
     * Enforces immutable canonical job_id -> manifest_id association.
     *
     * @param {string} manifestId - UUIDv4 manifest ID.
     * @returns {Promise<object>} Indexed entry record.
     */
    async indexManifest(manifestId) {
        if (!isNonEmptyString(manifestId) || !UUID_V4_REGEX.test(manifestId)) {
            throw new SceneResultIndexError(
                "INVALID_MANIFEST_ID",
                `Invalid manifest_id: "${manifestId}". Must be an RFC 4122 UUIDv4.`
            );
        }

        // 1. Authoritative metadata: load and validate from trusted store
        let manifest;
        try {
            manifest = await this.store.getManifest(manifestId, { required: true });
        } catch (err) {
            if (err instanceof SceneResultStoreError) {
                if (err.code === "MANIFEST_NOT_FOUND") {
                    throw new SceneResultIndexError("MANIFEST_NOT_FOUND", `Manifest not found: ${manifestId}`, { cause: err });
                }
                throw new SceneResultIndexError("INVALID_MANIFEST", `Manifest validation failed: ${err.message}`, { cause: err });
            }
            throw err;
        }

        const jobId = manifest.execution?.job_id;
        const docId = manifest.owner?.document_id;
        const pageId = manifest.owner?.page_id;
        const sceneId = manifest.owner?.scene_id;
        const createdAt = manifest.created_at;

        if (!isNonEmptyString(jobId) || !UUID_ANY_REGEX.test(jobId)) {
            throw new SceneResultIndexError("INVALID_MANIFEST", "Manifest missing valid execution.job_id");
        }
        if (!isNonEmptyString(docId) || !isNonEmptyString(pageId) || !isNonEmptyString(sceneId)) {
            throw new SceneResultIndexError("INVALID_MANIFEST", "Manifest missing complete owner identity");
        }
        if (!isNonEmptyString(createdAt) || Number.isNaN(Date.parse(createdAt))) {
            throw new SceneResultIndexError("INVALID_MANIFEST", "Manifest missing valid created_at timestamp");
        }

        // 2. Concurrency-safe index check and update
        return this._exclusive(async () => {
            const indexData = await this._readIndex();

            const existingByJob = indexData.entries.find(e => e.job_id === jobId);
            if (existingByJob) {
                if (existingByJob.manifest_id === manifestId) {
                    // Idempotent association
                    return structuredClone(existingByJob);
                }
                throw new SceneResultIndexError(
                    "JOB_RESULT_CONFLICT",
                    `Job "${jobId}" is already canonically associated with manifest "${existingByJob.manifest_id}", cannot associate with "${manifestId}"`
                );
            }

            const newEntry = {
                manifest_id: manifestId,
                job_id: jobId,
                document_id: docId,
                page_id: pageId,
                scene_id: sceneId,
                created_at: createdAt
            };

            indexData.entries.push(newEntry);
            await this._writeIndex(indexData);

            return structuredClone(newEntry);
        });
    }

    /**
     * Resolves the canonical manifest for a given job_id.
     * Loads the validated manifest directly from SceneResultStore.
     *
     * @param {string} jobId
     * @returns {Promise<{ manifest_id: string, manifest: object } | null>}
     */
    async getByJobId(jobId) {
        if (!isNonEmptyString(jobId) || !UUID_ANY_REGEX.test(jobId)) {
            throw new SceneResultIndexError("INVALID_JOB_ID", `Invalid jobId: "${jobId}"`);
        }

        const indexData = await this._readIndex();
        const entry = indexData.entries.find(e => e.job_id === jobId);
        if (!entry) {
            return null;
        }

        let manifest;
        try {
            manifest = await this.store.getManifest(entry.manifest_id, { required: false });
        } catch (err) {
            throw new SceneResultIndexError(
                "INDEX_CONSISTENCY_ERROR",
                `Failed to load manifest for indexed job ${jobId}: ${err.message}`,
                { cause: err }
            );
        }

        if (!manifest) {
            throw new SceneResultIndexError(
                "INDEX_CONSISTENCY_ERROR",
                `Index references missing manifest ${entry.manifest_id} for job ${jobId}`
            );
        }

        return {
            manifest_id: entry.manifest_id,
            manifest
        };
    }

    /**
     * Returns raw index entry for a job_id without loading full manifest.
     *
     * @param {string} jobId
     * @returns {Promise<object | null>}
     */
    async getEntryByJobId(jobId) {
        if (!isNonEmptyString(jobId) || !UUID_ANY_REGEX.test(jobId)) {
            throw new SceneResultIndexError("INVALID_JOB_ID", `Invalid jobId: "${jobId}"`);
        }
        const indexData = await this._readIndex();
        const entry = indexData.entries.find(e => e.job_id === jobId);
        return entry ? structuredClone(entry) : null;
    }

    /**
     * Lists result history for a Scene deterministically ordered by created_at descending,
     * with manifest_id descending as tie-breaker.
     *
     * @param {object} query
     * @param {string} query.document_id
     * @param {string} query.page_id
     * @param {string} query.scene_id
     * @param {boolean} [query.loadManifests=false]
     * @returns {Promise<Array<object>>}
     */
    async listByScene({ document_id, page_id, scene_id, loadManifests = false } = {}) {
        if (!isNonEmptyString(document_id) || !isNonEmptyString(page_id) || !isNonEmptyString(scene_id)) {
            throw new SceneResultIndexError(
                "INVALID_QUERY",
                "listByScene requires non-empty document_id, page_id, and scene_id"
            );
        }

        const indexData = await this._readIndex();
        const matched = indexData.entries.filter(e =>
            e.document_id === document_id &&
            e.page_id === page_id &&
            e.scene_id === scene_id
        );

        // Deterministic ordering: created_at descending, manifest_id descending tie-breaker
        matched.sort((a, b) => {
            const timeDiff = Date.parse(b.created_at) - Date.parse(a.created_at);
            if (timeDiff !== 0) return timeDiff;
            return b.manifest_id.localeCompare(a.manifest_id);
        });

        if (!loadManifests) {
            return structuredClone(matched);
        }

        const results = [];
        for (const entry of matched) {
            let manifest;
            try {
                manifest = await this.store.getManifest(entry.manifest_id, { required: false });
            } catch (err) {
                throw new SceneResultIndexError(
                    "INDEX_CONSISTENCY_ERROR",
                    `Failed to load manifest ${entry.manifest_id} in listByScene: ${err.message}`,
                    { cause: err }
                );
            }
            if (!manifest) {
                throw new SceneResultIndexError(
                    "INDEX_CONSISTENCY_ERROR",
                    `Index references missing manifest ${entry.manifest_id} in listByScene`
                );
            }
            results.push({
                ...structuredClone(entry),
                manifest
            });
        }
        return results;
    }
}
