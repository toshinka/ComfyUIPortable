/**
 * authoring_snapshot_store.mjs — Immutable storage for original Manga Authoring Document snapshots.
 *
 * Implements atomic, immutable storage for full Authoring Document snapshots supplied
 * for generation requests. Preserves exact JSON bytes, calculates SHA-256 content digests,
 * and guarantees create-only publication preventing overwrites and concurrent writer races.
 */

import fs from "node:fs/promises";
import path from "node:path";
import { createHash, randomUUID } from "node:crypto";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
export const DEFAULT_SNAPSHOT_DIR = path.resolve(here, "..", "data", "snapshots");

export const AUTHORING_SCHEMA_ID = "TEGAKI_AUTHORING_DOCUMENT";
export const AUTHORING_SCHEMA_VERSION = "1.0.0";

const UUID_V4_REGEX = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

export class AuthoringSnapshotStoreError extends Error {
    constructor(code, message, options = {}) {
        super(message, options);
        this.name = "AuthoringSnapshotStoreError";
        this.code = code;
    }
}

function isObject(val) {
    return val !== null && typeof val === "object" && !Array.isArray(val);
}

function isNonEmptyString(val) {
    return typeof val === "string" && val.trim().length > 0;
}

/**
 * Validates the minimum required envelope of a Manga Authoring Document snapshot.
 * Preserves all document payload contents without stripping or altering fields.
 *
 * @param {unknown} doc
 * @throws {AuthoringSnapshotStoreError}
 */
export function validateAuthoringDocumentEnvelope(doc) {
    if (!isObject(doc)) {
        throw new AuthoringSnapshotStoreError(
            "INVALID_DOCUMENT_ENVELOPE",
            "Authoring Document must be a non-null object"
        );
    }
    if (doc.schema_id !== AUTHORING_SCHEMA_ID) {
        throw new AuthoringSnapshotStoreError(
            "INVALID_DOCUMENT_ENVELOPE",
            `Invalid schema_id: expected "${AUTHORING_SCHEMA_ID}", got "${doc.schema_id}"`
        );
    }
    if (!isNonEmptyString(doc.schema_version)) {
        throw new AuthoringSnapshotStoreError(
            "INVALID_DOCUMENT_ENVELOPE",
            "Authoring Document must have a non-empty schema_version"
        );
    }
    if (!isNonEmptyString(doc.document_id)) {
        throw new AuthoringSnapshotStoreError(
            "INVALID_DOCUMENT_ENVELOPE",
            "Authoring Document must have a non-empty document_id"
        );
    }
    if (!Array.isArray(doc.pages)) {
        throw new AuthoringSnapshotStoreError(
            "INVALID_DOCUMENT_ENVELOPE",
            "Authoring Document must contain a pages array"
        );
    }
}

export class AuthoringSnapshotStore {
    /**
     * @param {string} [directory] - Storage directory path. Defaults to DEFAULT_SNAPSHOT_DIR.
     * @param {typeof fs} [fsApi] - Filesystem promises API implementation.
     */
    constructor(directory = DEFAULT_SNAPSHOT_DIR, fsApi = fs) {
        this.directory = path.resolve(directory);
        this.fs = fsApi;
    }

    /**
     * Resolves the physical path for a validated snapshot_id.
     * Rejects path traversal or non-UUIDv4 identifiers before any filesystem interaction.
     *
     * @param {string} snapshotId
     * @returns {string}
     */
    _file(snapshotId) {
        if (typeof snapshotId !== "string" || !UUID_V4_REGEX.test(snapshotId)) {
            throw new AuthoringSnapshotStoreError(
                "INVALID_SNAPSHOT_ID",
                `Invalid snapshot_id: "${snapshotId}". Must be an RFC 4122 UUIDv4.`
            );
        }
        return path.join(this.directory, `${snapshotId}.json`);
    }

    /**
     * Constructs a durable opaque store reference for a snapshot ID.
     *
     * @param {string} snapshotId
     * @returns {string}
     */
    _ref(snapshotId) {
        return `snapshots/${snapshotId}.json`;
    }

    /**
     * Atomically saves a complete Manga Authoring Document snapshot.
     * Calculates SHA-256 over exact stored bytes. Prevents overwriting existing snapshots.
     *
     * @param {string} snapshotId - RFC 4122 UUIDv4 identifier.
     * @param {object} document - Complete Authoring Document JSON snapshot.
     * @returns {Promise<{snapshot_id: string, snapshot_ref: string, content_digest: string}>}
     */
    async saveSnapshot(snapshotId, document) {
        const target = this._file(snapshotId);
        validateAuthoringDocumentEnvelope(document);

        // Serialize snapshot to stable JSON and compute SHA-256 byte digest
        const serialized = JSON.stringify(document, null, 2) + "\n";
        const content_digest = createHash("sha256").update(serialized, "utf8").digest("hex");
        const snapshot_ref = this._ref(snapshotId);

        const temporary = path.join(this.directory, `${snapshotId}.${randomUUID()}.tmp`);

        // Ensure storage directory exists
        try {
            await this.fs.mkdir(this.directory, { recursive: true });
        } catch (error) {
            throw new AuthoringSnapshotStoreError(
                "STORE_DIR_FAILED",
                `Failed to create snapshot directory: ${error.message}`,
                { cause: error }
            );
        }

        // Write fully to temporary file with exclusive creation
        let handle = null;
        let writeError = null;
        try {
            handle = await this.fs.open(temporary, "wx");
            await handle.writeFile(serialized, "utf8");
            await handle.sync();
        } catch (error) {
            writeError = error;
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
            try {
                await this.fs.unlink(temporary);
            } catch {}
            throw new AuthoringSnapshotStoreError(
                "STORE_WRITE_FAILED",
                `Failed to write temporary snapshot file: ${writeError.message}`,
                { cause: writeError }
            );
        }

        // Atomic create-only publication via hard link.
        // Fails with EEXIST if target already exists, preventing overwrite races and partial-record visibility.
        try {
            await this.fs.link(temporary, target);
        } catch (linkError) {
            try {
                await this.fs.unlink(temporary);
            } catch {}

            if (linkError.code === "EEXIST") {
                throw new AuthoringSnapshotStoreError(
                    "SNAPSHOT_EXISTS",
                    `Snapshot record ${snapshotId} already exists and is immutable.`
                );
            }
            throw new AuthoringSnapshotStoreError(
                "STORE_WRITE_FAILED",
                `Failed to publish snapshot atomically: ${linkError.message}`,
                { cause: linkError }
            );
        }

        // Clean up temporary link entry
        try {
            await this.fs.unlink(temporary);
        } catch {}

        return {
            snapshot_id: snapshotId,
            snapshot_ref,
            content_digest,
        };
    }

    /**
     * Loads and verifies a stored Manga Authoring Document snapshot.
     * Recalculates SHA-256 from stored bytes and verifies optional expected digest.
     *
     * @param {string} snapshotId - RFC 4122 UUIDv4 identifier.
     * @param {object} [options]
     * @param {string} [options.expectedDigest] - Optional expected SHA-256 digest to verify against stored bytes.
     * @param {boolean} [options.required=false] - If true, throws SNAPSHOT_NOT_FOUND when record is missing.
     * @returns {Promise<{snapshot_id: string, snapshot_ref: string, content_digest: string, document: object}|null>}
     */
    async getSnapshot(snapshotId, options = {}) {
        const target = this._file(snapshotId);
        const expectedDigest = options.expectedDigest || options.expected_digest;
        let raw;
        try {
            raw = await this.fs.readFile(target, "utf8");
        } catch (error) {
            if (error.code === "ENOENT") {
                if (options.required) {
                    throw new AuthoringSnapshotStoreError(
                        "SNAPSHOT_NOT_FOUND",
                        `Snapshot not found: ${snapshotId}`
                    );
                }
                return null;
            }
            throw new AuthoringSnapshotStoreError(
                "STORE_READ_FAILED",
                `Failed to read snapshot file ${snapshotId}: ${error.message}`,
                { cause: error }
            );
        }

        // Verify SHA-256 byte digest
        const content_digest = createHash("sha256").update(raw, "utf8").digest("hex");
        if (expectedDigest && content_digest !== expectedDigest) {
            throw new AuthoringSnapshotStoreError(
                "DIGEST_MISMATCH",
                `Snapshot digest mismatch for ${snapshotId}: expected ${expectedDigest}, got ${content_digest}`
            );
        }

        let parsed;
        try {
            parsed = JSON.parse(raw);
        } catch (error) {
            throw new AuthoringSnapshotStoreError(
                "STORE_CORRUPT",
                `Malformed JSON in stored snapshot ${snapshotId}: ${error.message}`,
                { cause: error }
            );
        }

        try {
            validateAuthoringDocumentEnvelope(parsed);
        } catch (error) {
            throw new AuthoringSnapshotStoreError(
                "STORE_CORRUPT",
                `Stored snapshot ${snapshotId} failed envelope validation: ${error.message}`,
                { cause: error }
            );
        }

        return {
            snapshot_id: snapshotId,
            snapshot_ref: this._ref(snapshotId),
            content_digest,
            document: parsed,
        };
    }
}

/**
 * Convenience wrapper for saving an Authoring Document snapshot.
 *
 * @param {string} snapshotId
 * @param {object} document
 * @param {object|AuthoringSnapshotStore} [storeOrOptions]
 * @returns {Promise<{snapshot_id: string, snapshot_ref: string, content_digest: string}>}
 */
export async function saveSnapshot(snapshotId, document, storeOrOptions = {}) {
    const store = storeOrOptions instanceof AuthoringSnapshotStore
        ? storeOrOptions
        : new AuthoringSnapshotStore(storeOrOptions.directory || DEFAULT_SNAPSHOT_DIR, storeOrOptions.fs || fs);
    return store.saveSnapshot(snapshotId, document);
}

/**
 * Convenience wrapper for loading an Authoring Document snapshot.
 *
 * @param {string} snapshotId
 * @param {object|AuthoringSnapshotStore} [storeOrOptions]
 * @returns {Promise<{snapshot_id: string, snapshot_ref: string, content_digest: string, document: object}|null>}
 */
export async function getSnapshot(snapshotId, storeOrOptions = {}) {
    const store = storeOrOptions instanceof AuthoringSnapshotStore
        ? storeOrOptions
        : new AuthoringSnapshotStore(storeOrOptions.directory || DEFAULT_SNAPSHOT_DIR, storeOrOptions.fs || fs);
    return store.getSnapshot(snapshotId, storeOrOptions);
}
