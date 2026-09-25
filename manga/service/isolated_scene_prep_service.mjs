/**
 * isolated_scene_prep_service.mjs — Node-side compile-only preparation service for isolated Scenes.
 *
 * Captures an immutable Authoring Document snapshot, compiles the isolated Scene via the
 * backend Python compiler endpoint (/tegaki/manga/generation/compile-isolated-scene),
 * enforces Reference-disabled and Guide-disabled policies, persists the original Authoring Document
 * snapshot only upon complete validation, and yields a prepared provenance bundle for future execution.
 */

import { randomUUID } from "node:crypto";
import { isDeepStrictEqual } from "node:util";
import {
    AuthoringSnapshotStore,
    validateAuthoringDocumentEnvelope,
} from "./authoring_snapshot_store.mjs";

export class IsolatedScenePrepError extends Error {
    constructor(code, message, status = 400, details = null) {
        super(message);
        this.name = "IsolatedScenePrepError";
        this.code = code;
        this.status = status;
        this.details = details;
    }
}

function isObject(val) {
    return val !== null && typeof val === "object" && !Array.isArray(val);
}

function isNonEmptyString(val) {
    return typeof val === "string" && val.trim().length > 0;
}

export class IsolatedScenePrepService {
    /**
     * @param {object} [options]
     * @param {string} [options.backendUrl] - Fixed loopback HTTP origin for Manga backend.
     * @param {AuthoringSnapshotStore} [options.snapshotStore] - Snapshot storage instance.
     * @param {typeof fetch} [options.fetchFn] - Fetch implementation (injectable for testing).
     * @param {number} [options.timeoutMs] - Request timeout in milliseconds.
     * @param {() => string} [options.idFactory] - UUID factory for snapshot IDs.
     */
    constructor({
        backendUrl = "http://127.0.0.1:8189",
        snapshotStore = null,
        fetchFn = fetch,
        timeoutMs = 10000,
        idFactory = randomUUID,
    } = {}) {
        const target = new URL(backendUrl);
        if (target.protocol !== "http:" || !["127.0.0.1", "localhost"].includes(target.hostname) ||
            target.pathname !== "/" || target.search || target.hash) {
            throw new IsolatedScenePrepError(
                "BACKEND_TARGET_INVALID",
                "Manga backend must be a fixed loopback HTTP origin",
                500
            );
        }
        this.origin = target.origin;
        this.snapshotStore = snapshotStore || new AuthoringSnapshotStore();
        this.fetchFn = fetchFn;
        this.timeoutMs = timeoutMs;
        this.idFactory = idFactory;
    }

    /**
     * Prepares one selected isolated Scene for generation.
     *
     * @param {object} input
     * @param {object} input.authoring_document - Complete original Authoring Document snapshot.
     * @param {string} input.scene_id - Selected Scene ID to prepare.
     * @param {object} input.generation_params - Execution settings (checkpoint_id, sampler_id, etc.).
     * @param {string} [input.page_id] - Optional page ID override.
     * @param {number} [input.page_index] - Optional page index override.
     * @param {object} [input.local_dimensions] - Optional canvas dimensions { width, height }.
     * @param {number} [input.random_seed] - Optional explicit random seed.
     * @returns {Promise<object>} Prepared provenance bundle.
     */
    async prepareIsolatedScene(input) {
        // 1. Validate envelope shape before backend dispatch
        if (!isObject(input)) {
            throw new IsolatedScenePrepError("INVALID_REQUEST", "Input must be a non-null object", 400);
        }
        if (!isObject(input.authoring_document)) {
            throw new IsolatedScenePrepError("INVALID_REQUEST", "authoring_document must be a non-null object", 400);
        }
        try {
            validateAuthoringDocumentEnvelope(input.authoring_document);
        } catch (envelopeError) {
            throw new IsolatedScenePrepError(
                envelopeError.code || "INVALID_REQUEST",
                envelopeError.message,
                400
            );
        }
        if (!isNonEmptyString(input.scene_id)) {
            throw new IsolatedScenePrepError("INVALID_REQUEST", "scene_id must be a non-empty string", 400);
        }
        if (!isObject(input.generation_params)) {
            throw new IsolatedScenePrepError("INVALID_REQUEST", "generation_params must be a non-null object", 400);
        }

        const requestedSceneId = input.scene_id.trim();

        // 2. Document Capture: create an independent immutable working copy
        const capturedDocument = structuredClone(input.authoring_document);

        // 3. Construct backend compile payload
        const compileRequest = {
            authoring_document: capturedDocument,
            scene_id: requestedSceneId,
            generation_params: input.generation_params,
        };
        if (input.page_id !== undefined) compileRequest.page_id = input.page_id;
        if (input.page_index !== undefined) compileRequest.page_index = input.page_index;
        if (input.local_dimensions !== undefined) compileRequest.local_dimensions = input.local_dimensions;
        if (input.random_seed !== undefined) compileRequest.random_seed = input.random_seed;

        // 4. Backend Compile Call: POST /tegaki/manga/generation/compile-isolated-scene
        let response;
        try {
            response = await this.fetchFn(`${this.origin}/tegaki/manga/generation/compile-isolated-scene`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(compileRequest),
                signal: AbortSignal.timeout(this.timeoutMs),
            });
        } catch (error) {
            throw new IsolatedScenePrepError(
                error.name === "TimeoutError" ? "BACKEND_TIMEOUT" : "BACKEND_UNAVAILABLE",
                error.name === "TimeoutError" ? "Backend request timed out" : `Backend request failed: ${error.message}`,
                502
            );
        }

        let result;
        try {
            result = await response.json();
        } catch {
            throw new IsolatedScenePrepError(
                "BACKEND_INVALID_RESPONSE",
                "Backend returned non-JSON response",
                502
            );
        }

        if (!response.ok || !result || result.ok !== true) {
            const code = result?.error_code || "COMPILE_FAILED";
            const message = result?.error || `Backend compile rejected with status ${response.status}`;
            throw new IsolatedScenePrepError(code, message, response.status || 502, result);
        }

        // 5. Compile Response Consistency Checks
        const {
            plan,
            graph,
            graph_digest,
            save_node_id,
            page_compile_plan,
            page_compile_plan_digest,
            compile_metadata,
        } = result;

        if (!isObject(plan) || !isObject(graph) || !isNonEmptyString(graph_digest) ||
            !isNonEmptyString(save_node_id) || !isObject(page_compile_plan) ||
            !isNonEmptyString(page_compile_plan_digest) || !isObject(compile_metadata)) {
            throw new IsolatedScenePrepError(
                "COMPILE_RESPONSE_INCOMPLETE",
                "Backend response missing required compile fields",
                502
            );
        }

        const planSceneId = plan.owner?.scene_id || plan.scene?.scene_id;
        if (planSceneId !== requestedSceneId) {
            throw new IsolatedScenePrepError(
                "COMPILE_CONSISTENCY_MISMATCH",
                `Plan scene_id (${planSceneId}) does not match requested scene_id (${requestedSceneId})`,
                502
            );
        }

        if (compile_metadata.scene_id !== planSceneId) {
            throw new IsolatedScenePrepError(
                "COMPILE_CONSISTENCY_MISMATCH",
                `Metadata scene_id (${compile_metadata.scene_id}) does not match plan scene_id (${planSceneId})`,
                502
            );
        }

        if (compile_metadata.graph_digest !== graph_digest) {
            throw new IsolatedScenePrepError(
                "DIGEST_MISMATCH",
                "Metadata graph_digest does not match root graph_digest",
                502
            );
        }

        if (compile_metadata.page_compile_plan_digest !== page_compile_plan_digest) {
            throw new IsolatedScenePrepError(
                "DIGEST_MISMATCH",
                "Metadata page_compile_plan_digest does not match root page_compile_plan_digest",
                502
            );
        }

        // 6. Reference-Disabled First Policy
        if (!plan.reference || plan.reference.enabled !== false || plan.reference.reference_asset !== null) {
            throw new IsolatedScenePrepError(
                "ISOLATED_REFERENCE_UNSUPPORTED",
                "Active Reference is unsupported in isolated-Scene preparation",
                422
            );
        }

        if (compile_metadata.reference !== undefined &&
            !isDeepStrictEqual(compile_metadata.reference, plan.reference)) {
            throw new IsolatedScenePrepError(
                "COMPILE_CONSISTENCY_MISMATCH",
                "Metadata reference does not match plan reference",
                502
            );
        }

        // 7. Guide Policy (must be explicitly disabled and consistent)
        if (!isObject(plan.guide_state) ||
            plan.guide_state.enabled !== false ||
            plan.guide_state.active !== false) {
            throw new IsolatedScenePrepError(
                "ISOLATED_GUIDE_STATE_INVALID",
                "Isolated plan must have explicit disabled guide_state { enabled: false, active: false }",
                422
            );
        }

        if (!isDeepStrictEqual(compile_metadata.guide_state, plan.guide_state)) {
            throw new IsolatedScenePrepError(
                "COMPILE_CONSISTENCY_MISMATCH",
                "Metadata guide_state does not match plan guide_state",
                502
            );
        }

        // 8. Snapshot Persistence: persist the SAME captured original Authoring Document
        const snapshotId = this.idFactory();
        let snapshotProvenance;
        try {
            snapshotProvenance = await this.snapshotStore.saveSnapshot(snapshotId, capturedDocument);
        } catch (error) {
            throw new IsolatedScenePrepError(
                "SNAPSHOT_SAVE_FAILED",
                `Failed to persist Authoring Document snapshot: ${error.message}`,
                500,
                { cause: error }
            );
        }

        // 9. Prepared Output Bundle
        const documentId = plan.owner?.document_id || capturedDocument.document_id;
        const pageId = plan.owner?.page_id || plan.page_context?.page_id || compile_metadata.page_id;
        const sceneId = plan.owner?.scene_id || compile_metadata.scene_id || requestedSceneId;

        const bundle = {
            owner: {
                document_id: documentId,
                page_id: pageId,
                scene_id: sceneId,
            },
            snapshot: {
                snapshot_id: snapshotProvenance.snapshot_id,
                snapshot_ref: snapshotProvenance.snapshot_ref,
                content_digest: snapshotProvenance.content_digest,
            },
            plan: structuredClone(plan),
            graph: structuredClone(graph),
            graph_digest,
            save_node_id,
            page_compile_plan: structuredClone(page_compile_plan),
            page_compile_plan_digest,
            compile_metadata: structuredClone(compile_metadata),
        };

        if (result.audit_trail !== undefined) {
            bundle.audit_trail = structuredClone(result.audit_trail);
        }

        return bundle;
    }
}

/**
 * Convenience function for preparing an isolated Scene.
 *
 * @param {object} input
 * @param {object} [options]
 * @returns {Promise<object>}
 */
export async function prepareIsolatedScene(input, options = {}) {
    const service = new IsolatedScenePrepService(options);
    return service.prepareIsolatedScene(input);
}
