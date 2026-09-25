/**
 * page_composite_store.mjs — Store for Immutable Page Composite Bundles.
 *
 * Persists and retrieves immutable bundles containing:
 *   <composite_id>/
 *     manifest.json
 *     artifact.png
 *
 * Enforces atomic create-only bundle publication, exact byte persistence,
 * fresh store-boundary artifact verification, and strict integrity checks.
 */

import fs from "node:fs/promises";
import path from "node:path";
import { randomUUID } from "node:crypto";

import {
    SCHEMA_ID,
    SCHEMA_VERSION,
    PageCompositeManifestError,
    validateCompositionPlan,
    validatePageCompositeManifest,
    computeCompositionPlanDigest,
} from "./page_composite_manifest.mjs";
import { analyzePngArtifact, PngArtifactAnalyzerError } from "./png_artifact_analyzer.mjs";

const DEFAULT_STORE_DIR = path.resolve("manga/data/page_composites");
const UUID_V4_REGEX = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

export class PageCompositeStoreError extends Error {
    constructor(code, message, options = {}) {
        super(message, options);
        this.name = "PageCompositeStoreError";
        this.code = code;
    }
}

function isObject(val) {
    return val !== null && typeof val === "object" && !Array.isArray(val);
}

function isNonEmptyString(val) {
    return typeof val === "string" && val.trim().length > 0;
}

export class PageCompositeStore {
    /**
     * @param {string} [directory] - Store root directory.
     * @param {object} [options]
     * @param {() => string} [options.idFactory=randomUUID] - Factory for composite UUIDs.
     * @param {object} [options.fsModule=fs] - Injected file system module.
     */
    constructor(directory = DEFAULT_STORE_DIR, options = {}) {
        this.directory = path.resolve(directory);
        this.idFactory = options.idFactory || randomUUID;
        this.fs = options.fsModule || fs;
    }

    _validateCompositeId(compositeId) {
        if (!isNonEmptyString(compositeId) || !UUID_V4_REGEX.test(compositeId)) {
            throw new PageCompositeStoreError(
                "INVALID_COMPOSITE_ID",
                `composite_id must be a valid UUIDv4 string, got '${compositeId}'`
            );
        }
    }

    _bundleDir(compositeId) {
        this._validateCompositeId(compositeId);
        const resolved = path.resolve(this.directory, compositeId);
        // Ensure path remains strictly inside store directory
        if (path.dirname(resolved) !== this.directory) {
            throw new PageCompositeStoreError("PATH_TRAVERSAL_DETECTED", "composite_id escapes store root");
        }
        return resolved;
    }

    /**
     * Atomically saves an immutable page composite bundle (<composite_id>/manifest.json + artifact.png).
     *
     * @param {object} input
     * @param {object} input.composition_plan - Trusted TEGAKI_PAGE_COMPOSITION_PLAN
     * @param {Buffer} input.composite_bytes - Exact composite PNG bytes
     * @returns {Promise<{ composite_id: string, manifest: object }>}
     */
    async saveComposite({ composition_plan, composite_bytes } = {}) {
        if (!isObject(composition_plan)) {
            throw new PageCompositeStoreError("INVALID_INPUT", "composition_plan must be an object");
        }
        if (!Buffer.isBuffer(composite_bytes) || composite_bytes.length === 0) {
            throw new PageCompositeStoreError("INVALID_INPUT", "composite_bytes must be a non-empty Buffer");
        }

        // 1. Validate composition plan
        let plan;
        try {
            plan = validateCompositionPlan(composition_plan);
        } catch (err) {
            throw new PageCompositeStoreError(
                err.code || "INVALID_PLAN",
                `Composition plan validation failed: ${err.message}`,
                { cause: err }
            );
        }

        // 2. Fresh store-boundary analysis of composite PNG bytes
        let analyzed;
        try {
            analyzed = analyzePngArtifact(composite_bytes, {
                width: plan.page.width,
                height: plan.page.height,
            });
        } catch (err) {
            throw new PageCompositeStoreError(
                err.code || "INVALID_ARTIFACT",
                `Composite artifact verification failed: ${err.message}`,
                { cause: err }
            );
        }

        // 3. Generate server-owned identifiers & facts
        const compositeId = this.idFactory();
        this._validateCompositeId(compositeId);

        const createdAt = new Date().toISOString();
        const planDigest = computeCompositionPlanDigest(plan);
        const artifactRef = `page-composites/${compositeId}/artifact.png`;

        const totalScenes = plan.scenes.length;
        const composedScenes = plan.scenes.filter(s => s.state === "CURRENT_RESULT").length;
        const unfilledScenes = plan.scenes.filter(s => s.state === "UNFILLED").length;

        // 4. Construct manifest
        const manifestCandidate = {
            schema_id: SCHEMA_ID,
            schema_version: SCHEMA_VERSION,
            composite_id: compositeId,
            created_at: createdAt,
            owner: {
                document_id: plan.page.document_id,
                page_id: plan.page.page_id,
            },
            composition_plan: structuredClone(plan),
            composition_plan_digest: planDigest,
            artifact: {
                artifact_ref: artifactRef,
                content_digest: analyzed.content_digest,
                declared_width: analyzed.declared_width,
                declared_height: analyzed.declared_height,
                byte_length: analyzed.byte_length,
                media_type: "image/png",
            },
            statistics: {
                total_scenes: totalScenes,
                composed_scenes: composedScenes,
                unfilled_scenes: unfilledScenes,
            },
        };

        // 5. Validate manifest
        let manifest;
        try {
            manifest = validatePageCompositeManifest(manifestCandidate);
        } catch (err) {
            throw new PageCompositeStoreError(
                err.code || "INVALID_MANIFEST",
                `Page composite manifest validation failed: ${err.message}`,
                { cause: err }
            );
        }

        // 6. Ensure root store directory exists
        try {
            await this.fs.mkdir(this.directory, { recursive: true });
        } catch (err) {
            throw new PageCompositeStoreError(
                "STORE_DIR_FAILED",
                `Failed to create store directory: ${err.message}`,
                { cause: err }
            );
        }

        // 7. Atomic Create-Only Publication
        const targetDir = this._bundleDir(compositeId);

        // Check if target directory already exists
        try {
            await this.fs.stat(targetDir);
            throw new PageCompositeStoreError(
                "COMPOSITE_EXISTS",
                `Composite bundle '${compositeId}' already exists and cannot be overwritten`
            );
        } catch (err) {
            if (err.code === "COMPOSITE_EXISTS") throw err;
            // File/dir does not exist (ENOENT) -> proceed
        }

        const tempDir = path.join(this.directory, `.tmp_${compositeId}_${randomUUID()}`);
        try {
            await this.fs.mkdir(tempDir, { recursive: true });

            // Write artifact.png
            const artifactFile = path.join(tempDir, "artifact.png");
            let artHandle = null;
            try {
                artHandle = await this.fs.open(artifactFile, "wx");
                await artHandle.writeFile(composite_bytes);
                await artHandle.sync();
            } finally {
                if (artHandle) await artHandle.close();
            }

            // Write manifest.json
            const manifestFile = path.join(tempDir, "manifest.json");
            const manifestSerialized = JSON.stringify(manifest, null, 2) + "\n";
            let manHandle = null;
            try {
                manHandle = await this.fs.open(manifestFile, "wx");
                await manHandle.writeFile(manifestSerialized, "utf8");
                await manHandle.sync();
            } finally {
                if (manHandle) await manHandle.close();
            }

            // Final atomic publication via rename
            await this.fs.rename(tempDir, targetDir);
        } catch (writeErr) {
            // Failure cleanup: remove only the temporary directory created during this call
            try {
                await this.fs.rm(tempDir, { recursive: true, force: true });
            } catch {}

            if (writeErr instanceof PageCompositeStoreError) {
                throw writeErr;
            }
            if (writeErr.code === "EEXIST" || writeErr.code === "EPERM") {
                throw new PageCompositeStoreError(
                    "COMPOSITE_EXISTS",
                    `Composite bundle '${compositeId}' already exists and cannot be overwritten`,
                    { cause: writeErr }
                );
            }
            throw new PageCompositeStoreError(
                "STORE_WRITE_FAILED",
                `Failed to write composite bundle: ${writeErr.message}`,
                { cause: writeErr }
            );
        }

        return {
            composite_id: compositeId,
            manifest,
        };
    }

    /**
     * Retrieves and validates a stored Page Composite Manifest by composite_id.
     *
     * @param {string} compositeId
     * @param {object} [options]
     * @param {boolean} [options.required=false]
     * @returns {Promise<object|null>}
     */
    async getManifest(compositeId, { required = false } = {}) {
        const bundleDir = this._bundleDir(compositeId);
        const manifestFile = path.join(bundleDir, "manifest.json");

        let raw;
        try {
            raw = await this.fs.readFile(manifestFile, "utf8");
        } catch (err) {
            if (err.code === "ENOENT") {
                if (required) {
                    throw new PageCompositeStoreError("COMPOSITE_NOT_FOUND", `Composite '${compositeId}' not found`);
                }
                return null;
            }
            throw new PageCompositeStoreError("STORE_READ_FAILED", `Failed to read manifest: ${err.message}`, { cause: err });
        }

        let parsed;
        try {
            parsed = JSON.parse(raw);
        } catch (err) {
            throw new PageCompositeStoreError("COMPOSITE_CORRUPT", `Manifest JSON corrupt: ${err.message}`, { cause: err });
        }

        try {
            return validatePageCompositeManifest(parsed);
        } catch (err) {
            throw new PageCompositeStoreError("COMPOSITE_CORRUPT", `Stored manifest invalid: ${err.message}`, { cause: err });
        }
    }

    /**
     * Retrieves and verifies exact stored artifact PNG bytes by composite_id.
     *
     * @param {string} compositeId
     * @param {object} [options]
     * @param {boolean} [options.required=false]
     * @returns {Promise<Buffer|null>}
     */
    async getArtifactBytes(compositeId, { required = false } = {}) {
        const bundleDir = this._bundleDir(compositeId);
        const artifactFile = path.join(bundleDir, "artifact.png");

        let bytes;
        try {
            bytes = await this.fs.readFile(artifactFile);
        } catch (err) {
            if (err.code === "ENOENT") {
                if (required) {
                    throw new PageCompositeStoreError("ARTIFACT_NOT_FOUND", `Artifact for composite '${compositeId}' not found`);
                }
                return null;
            }
            throw new PageCompositeStoreError("STORE_READ_FAILED", `Failed to read artifact: ${err.message}`, { cause: err });
        }

        // Verify against stored manifest
        const manifest = await this.getManifest(compositeId, { required: true });

        let analyzed;
        try {
            analyzed = analyzePngArtifact(bytes, {
                width: manifest.artifact.declared_width,
                height: manifest.artifact.declared_height,
            });
        } catch (err) {
            throw new PageCompositeStoreError("ARTIFACT_CORRUPT", `Stored artifact invalid: ${err.message}`, { cause: err });
        }

        if (analyzed.content_digest !== manifest.artifact.content_digest || bytes.length !== manifest.artifact.byte_length) {
            throw new PageCompositeStoreError(
                "ARTIFACT_CORRUPT",
                `Stored artifact digest/length mismatch with manifest: expected ${manifest.artifact.content_digest}, got ${analyzed.content_digest}`
            );
        }

        return bytes;
    }

    /**
     * Retrieves both manifest and verified artifact bytes for composite_id.
     *
     * @param {string} compositeId
     * @param {object} [options]
     * @param {boolean} [options.required=false]
     * @returns {Promise<{ manifest: object, artifact_bytes: Buffer }|null>}
     */
    async getComposite(compositeId, { required = false } = {}) {
        const manifest = await this.getManifest(compositeId, { required });
        if (!manifest) return null;
        const artifact_bytes = await this.getArtifactBytes(compositeId, { required: true });
        return {
            manifest,
            artifact_bytes,
        };
    }
}
