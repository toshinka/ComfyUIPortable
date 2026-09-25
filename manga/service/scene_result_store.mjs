/**
 * scene_result_store.mjs — Minimal durable store for completed isolated-Scene result manifests.
 *
 * Implements atomic, immutable storage for finalized result manifests validated
 * by validateSceneResultManifest(). Prevents partial writes, concurrent overwrite races,
 * and silent record replacement.
 */

import fs from "node:fs/promises";
import path from "node:path";
import { randomUUID } from "node:crypto";
import { fileURLToPath } from "node:url";

import {
    validateSceneResultManifest,
    SceneResultManifestError,
} from "./scene_result_manifest.mjs";

const here = path.dirname(fileURLToPath(import.meta.url));
export const DEFAULT_SCENE_RESULT_DIR = path.resolve(here, "..", "data", "scene_results");

const UUID_V4_REGEX = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

export class SceneResultStoreError extends Error {
    constructor(code, message, options = {}) {
        super(message, options);
        this.name = "SceneResultStoreError";
        this.code = code;
    }
}

export class SceneResultStore {
    /**
     * @param {string} [directory] - Storage directory path. Defaults to DEFAULT_SCENE_RESULT_DIR.
     * @param {typeof fs} [fsApi] - Filesystem promises API implementation.
     */
    constructor(directory = DEFAULT_SCENE_RESULT_DIR, fsApi = fs) {
        this.directory = path.resolve(directory);
        this.fs = fsApi;
    }

    /**
     * Resolves the physical path for a validated manifest_id.
     * Rejects path-traversal or non-UUIDv4 identifiers before any filesystem interaction.
     *
     * @param {string} manifestId
     * @returns {string}
     */
    _file(manifestId) {
        if (typeof manifestId !== "string" || !UUID_V4_REGEX.test(manifestId)) {
            throw new SceneResultStoreError(
                "INVALID_MANIFEST_ID",
                `Invalid manifest_id: "${manifestId}". Must be an RFC 4122 UUIDv4.`
            );
        }
        return path.join(this.directory, `${manifestId}.json`);
    }

    /**
     * Atomically saves a completed and valid isolated-Scene result manifest.
     * Rejects invalid manifests and prevents overwriting existing records.
     *
     * @param {object} manifest - Candidate result manifest object.
     * @returns {Promise<object>} Validated, stored manifest record.
     */
    async saveCompletedManifest(manifest) {
        // 1. Validate candidate manifest with canonical contract
        let validated;
        try {
            validated = validateSceneResultManifest(manifest);
        } catch (error) {
            if (error instanceof SceneResultManifestError) {
                throw new SceneResultStoreError(
                    "INVALID_MANIFEST",
                    `Manifest validation failed: ${error.message}`,
                    { cause: error }
                );
            }
            throw error;
        }

        const manifestId = validated.manifest_id;
        const target = this._file(manifestId);
        const temporary = path.join(this.directory, `${manifestId}.${randomUUID()}.tmp`);
        const serialized = JSON.stringify(validated, null, 2) + "\n";

        // 2. Ensure storage directory exists
        try {
            await this.fs.mkdir(this.directory, { recursive: true });
        } catch (error) {
            throw new SceneResultStoreError(
                "STORE_DIR_FAILED",
                `Failed to create scene result directory: ${error.message}`,
                { cause: error }
            );
        }

        // 3. Write fully to temporary file with exclusive creation
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
            throw new SceneResultStoreError(
                "STORE_WRITE_FAILED",
                `Failed to write temporary manifest file: ${writeError.message}`,
                { cause: writeError }
            );
        }

        // 4. Atomic create-only publication via hard link.
        // On both Windows NTFS and POSIX, fs.link fails atomically with EEXIST if target already exists,
        // preventing partial-record reads, concurrent writer clobbering, and accidental overwrites.
        try {
            await this.fs.link(temporary, target);
        } catch (linkError) {
            try {
                await this.fs.unlink(temporary);
            } catch {}

            if (linkError.code === "EEXIST") {
                throw new SceneResultStoreError(
                    "MANIFEST_EXISTS",
                    `Manifest record ${manifestId} already exists and is immutable.`
                );
            }
            throw new SceneResultStoreError(
                "STORE_WRITE_FAILED",
                `Failed to publish manifest atomically: ${linkError.message}`,
                { cause: linkError }
            );
        }

        // 5. Clean up temporary link entry (target remains intact)
        try {
            await this.fs.unlink(temporary);
        } catch {
            // Temporary link unlink failure does not compromise the published target
        }

        return validated;
    }

    /**
     * Loads and validates a stored isolated-Scene result manifest.
     *
     * @param {string} manifestId - RFC 4122 UUIDv4 manifest identity.
     * @param {object} [options]
     * @param {boolean} [options.required=false] - If true, throws MANIFEST_NOT_FOUND when record is missing.
     * @returns {Promise<object|null>} Validated manifest record or null if not found.
     */
    async getManifest(manifestId, options = {}) {
        const target = this._file(manifestId);
        let raw;
        try {
            raw = await this.fs.readFile(target, "utf8");
        } catch (error) {
            if (error.code === "ENOENT") {
                if (options.required) {
                    throw new SceneResultStoreError(
                        "MANIFEST_NOT_FOUND",
                        `Manifest record not found: ${manifestId}`
                    );
                }
                return null;
            }
            throw new SceneResultStoreError(
                "STORE_READ_FAILED",
                `Failed to read manifest file ${manifestId}: ${error.message}`,
                { cause: error }
            );
        }

        let parsed;
        try {
            parsed = JSON.parse(raw);
        } catch (error) {
            throw new SceneResultStoreError(
                "STORE_CORRUPT",
                `Malformed JSON in stored manifest record ${manifestId}: ${error.message}`,
                { cause: error }
            );
        }

        try {
            const validated = validateSceneResultManifest(parsed);
            if (validated.manifest_id !== manifestId) {
                throw new SceneResultStoreError(
                    "STORE_CORRUPT",
                    `Stored manifest record ${manifestId} contains mismatched manifest_id "${validated.manifest_id}"`
                );
            }
            return validated;
        } catch (error) {
            if (error instanceof SceneResultStoreError) throw error;
            throw new SceneResultStoreError(
                "STORE_CORRUPT",
                `Stored manifest record ${manifestId} failed schema validation: ${error.message}`,
                { cause: error }
            );
        }
    }
}

/**
 * Convenience wrapper for saving a completed manifest.
 *
 * @param {object} manifest
 * @param {object|SceneResultStore} [storeOrOptions]
 * @returns {Promise<object>}
 */
export async function saveCompletedManifest(manifest, storeOrOptions = {}) {
    const store = storeOrOptions instanceof SceneResultStore
        ? storeOrOptions
        : new SceneResultStore(storeOrOptions.directory || DEFAULT_SCENE_RESULT_DIR, storeOrOptions.fs || fs);
    return store.saveCompletedManifest(manifest);
}

/**
 * Convenience wrapper for getting a stored manifest.
 *
 * @param {string} manifestId
 * @param {object|SceneResultStore} [storeOrOptions]
 * @returns {Promise<object|null>}
 */
export async function getManifest(manifestId, storeOrOptions = {}) {
    const store = storeOrOptions instanceof SceneResultStore
        ? storeOrOptions
        : new SceneResultStore(storeOrOptions.directory || DEFAULT_SCENE_RESULT_DIR, storeOrOptions.fs || fs);
    return store.getManifest(manifestId, storeOrOptions);
}
