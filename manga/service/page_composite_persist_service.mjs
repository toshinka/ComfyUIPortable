/**
 * page_composite_persist_service.mjs — Trusted Page Composite Persistence Orchestration.
 *
 * Connects PageCompositorBridge to PageCompositeStore:
 *   Authoring/generation input
 *   -> PageCompositorBridge.composeCurrentPage
 *   -> trusted composition plan + exact composite PNG bytes
 *   -> PageCompositeStore.saveComposite
 *   -> validated retrieval (getComposite)
 *   -> stored result response
 *
 * Enforces zero modification to Authoring Document, single bridge and store calls,
 * byte and plan continuity, and fail-closed post-save consistency checks without
 * rolling back immutable bundles.
 */

import { canonicalizeJson } from "./page_composite_manifest.mjs";

export class PageCompositePersistError extends Error {
    /**
     * @param {string} code
     * @param {string} message
     * @param {object} [options]
     * @param {string} [options.composite_id]
     * @param {Error} [options.cause]
     */
    constructor(code, message, options = {}) {
        super(message, options);
        this.name = "PageCompositePersistError";
        this.code = code;
        if (options.composite_id) {
            this.composite_id = options.composite_id;
        }
    }
}

export const FORBIDDEN_CALLER_FIELDS = Object.freeze([
    "composition_plan",
    "composite_bytes",
    "composite_id",
    "manifest",
    "artifact_ref",
    "content_digest",
    "backend_url",
    "output_path",
]);

function isObject(val) {
    return val !== null && typeof val === "object" && !Array.isArray(val);
}

export class PageCompositePersistService {
    /**
     * @param {object} dependencies
     * @param {object} dependencies.bridge - PageCompositorBridge instance
     * @param {object} dependencies.store - PageCompositeStore instance
     * @param {object} [dependencies.index=null] - PageCompositeIndex instance
     */
    constructor({ bridge, store, index = null } = {}) {
        if (!bridge || typeof bridge.composeCurrentPage !== "function") {
            throw new PageCompositePersistError(
                "INVALID_DEPENDENCY",
                "PageCompositorBridge instance with composeCurrentPage is required"
            );
        }
        if (!store || typeof store.saveComposite !== "function" || typeof store.getComposite !== "function") {
            throw new PageCompositePersistError(
                "INVALID_DEPENDENCY",
                "PageCompositeStore instance with saveComposite and getComposite is required"
            );
        }
        if (index && typeof index.indexComposite !== "function") {
            throw new PageCompositePersistError(
                "INVALID_DEPENDENCY",
                "PageCompositeIndex instance must provide indexComposite"
            );
        }

        this.bridge = bridge;
        this.store = store;
        this.index = index;
    }

    /**
     * Persists the current page composite from authoring inputs.
     *
     * @param {object} input
     * @param {object} input.authoring_document
     * @param {object} input.generation_params
     * @param {string} [input.page_id]
     * @param {number} [input.page_index]
     * @returns {Promise<{
     *   composite_id: string,
     *   manifest: object,
     *   composite: {
     *     content_digest: string,
     *     declared_width: number,
     *     declared_height: number,
     *     byte_length: number
     *   }
     * }>}
     */
    async persistCurrentPageComposite(input) {
        if (!isObject(input)) {
            throw new PageCompositePersistError("INVALID_REQUEST", "Input must be a non-null object");
        }

        // 1. Enforce strict trust boundary: reject caller-supplied plan/authority fields
        for (const forbidden of FORBIDDEN_CALLER_FIELDS) {
            if (forbidden in input) {
                throw new PageCompositePersistError(
                    "FORBIDDEN_CALLER_FIELD",
                    `Caller cannot supply authority or storage field '${forbidden}'`
                );
            }
        }

        if (!isObject(input.authoring_document)) {
            throw new PageCompositePersistError("INVALID_REQUEST", "Input must contain an authoring_document object");
        }
        if (!isObject(input.generation_params)) {
            throw new PageCompositePersistError("INVALID_REQUEST", "Input must contain a generation_params object");
        }

        // 2. Prepare bounded bridge input
        const bridgeInput = {
            authoring_document: input.authoring_document,
            generation_params: input.generation_params,
        };
        if (input.page_id !== undefined) bridgeInput.page_id = input.page_id;
        if (input.page_index !== undefined) bridgeInput.page_index = input.page_index;

        // 3. Call PageCompositorBridge exactly ONCE
        let bridgeResult;
        try {
            bridgeResult = await this.bridge.composeCurrentPage(bridgeInput);
        } catch (err) {
            throw new PageCompositePersistError(
                err.code || "BRIDGE_COMPOSE_FAILED",
                `Page composition failed in bridge: ${err.message}`,
                { cause: err }
            );
        }

        if (!isObject(bridgeResult) || !isObject(bridgeResult.plan) || !Buffer.isBuffer(bridgeResult.composite_bytes)) {
            throw new PageCompositePersistError(
                "INVALID_BRIDGE_OUTPUT",
                "Bridge did not return expected plan and composite_bytes Buffer"
            );
        }

        // 4. Save to PageCompositeStore exactly ONCE with exact plan and Buffer bytes
        let saveResult;
        try {
            saveResult = await this.store.saveComposite({
                composition_plan: bridgeResult.plan,
                composite_bytes: bridgeResult.composite_bytes,
            });
        } catch (err) {
            throw new PageCompositePersistError(
                err.code || "STORE_SAVE_FAILED",
                `Failed to save composite in store: ${err.message}`,
                { cause: err }
            );
        }

        const compositeId = saveResult.composite_id;

        // 5. Validated retrieval through Store API and post-save consistency checks
        let retrieved;
        try {
            retrieved = await this.store.getComposite(compositeId, { required: true });
            if (!retrieved || !retrieved.manifest) {
                throw new Error("Retrieved composite manifest is missing");
            }

            const storedManifest = retrieved.manifest;
            const bridgeArtifact = bridgeResult.composite || {};

            // Re-verify artifact evidence against bridge analysis
            if (
                storedManifest.artifact.content_digest !== bridgeArtifact.content_digest ||
                storedManifest.artifact.declared_width !== bridgeArtifact.declared_width ||
                storedManifest.artifact.declared_height !== bridgeArtifact.declared_height ||
                storedManifest.artifact.byte_length !== bridgeArtifact.byte_length
            ) {
                throw new Error(
                    `Artifact evidence mismatch: stored=[${storedManifest.artifact.content_digest}, ${storedManifest.artifact.declared_width}x${storedManifest.artifact.declared_height}, ${storedManifest.artifact.byte_length}b] vs bridge=[${bridgeArtifact.content_digest}, ${bridgeArtifact.declared_width}x${bridgeArtifact.declared_height}, ${bridgeArtifact.byte_length}b]`
                );
            }

            // Plan consistency: stored composition_plan deep-equals bridge plan
            const canonicalStored = canonicalizeJson(storedManifest.composition_plan);
            const canonicalBridge = canonicalizeJson(bridgeResult.plan);
            if (canonicalStored !== canonicalBridge) {
                throw new Error("Stored composition_plan does not match bridge composition_plan");
            }

            // Owner consistency
            if (
                storedManifest.owner.document_id !== bridgeResult.plan.page.document_id ||
                storedManifest.owner.page_id !== bridgeResult.plan.page.page_id
            ) {
                throw new Error("Stored manifest owner does not match plan page owner");
            }
        } catch (err) {
            throw new PageCompositePersistError(
                "PERSISTED_COMPOSITE_INCONSISTENT",
                `Post-save retrieval or consistency check failed for composite '${compositeId}': ${err.message}`,
                { cause: err, composite_id: compositeId }
            );
        }

        // 6. Index publication if index dependency is provided
        if (this.index) {
            try {
                await this.index.indexComposite(compositeId);
            } catch (err) {
                throw new PageCompositePersistError(
                    "COMPOSITE_INDEX_PUBLICATION_FAILED",
                    `Store persistence succeeded for '${compositeId}' but index publication failed: ${err.message}`,
                    { cause: err, composite_id: compositeId }
                );
            }
        }

        // 7. Return response contract (excluding raw bytes and internal paths)
        return {
            composite_id: retrieved.manifest.composite_id,
            manifest: retrieved.manifest,
            composite: {
                content_digest: retrieved.manifest.artifact.content_digest,
                declared_width: retrieved.manifest.artifact.declared_width,
                declared_height: retrieved.manifest.artifact.declared_height,
                byte_length: retrieved.manifest.artifact.byte_length,
            },
        };
    }
}

/**
 * Functional wrapper for persistCurrentPageComposite.
 *
 * @param {object} input
 * @param {object} dependencies
 * @param {object} dependencies.bridge
 * @param {object} dependencies.store
 * @param {object} [dependencies.index=null]
 * @returns {Promise<object>}
 */
export async function persistCurrentPageComposite(input, { bridge, store, index = null } = {}) {
    const service = new PageCompositePersistService({ bridge, store, index });
    return service.persistCurrentPageComposite(input);
}
