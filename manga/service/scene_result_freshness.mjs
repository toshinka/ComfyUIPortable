/**
 * scene_result_freshness.mjs — Pure freshness classifier for stored Scene Result Manifests.
 *
 * Compares an existing immutable Scene Result Manifest's effective-input digest against
 * current Scene-specific generation inputs to return exactly:
 * - CURRENT: Same supported digest contract version and digests match.
 * - STALE: Same supported digest contract version and digests differ.
 * - UNKNOWN: A valid comparable digest cannot be established safely.
 *
 * Semantic authority:
 * Current effective evidence is obtained exclusively from the canonical compile-only
 * backend boundary (/tegaki/manga/generation/compile-isolated-scene) rather than
 * reconstructing planner semantics in Node.
 */

import {
    computeSceneEffectiveInputDigest,
    CONTRACT_VERSION,
    SceneEffectiveInputDigestError,
} from "./scene_effective_input_digest.mjs";
import { SceneResultStore, SceneResultStoreError } from "./scene_result_store.mjs";

export const FRESHNESS_STATUS = Object.freeze({
    CURRENT: "CURRENT",
    STALE: "STALE",
    UNKNOWN: "UNKNOWN",
});

export const REASON_CODES = Object.freeze({
    DIGEST_MATCH: "DIGEST_MATCH",
    DIGEST_MISMATCH: "DIGEST_MISMATCH",
    LEGACY_CONTRACT_UNKNOWN: "LEGACY_CONTRACT_UNKNOWN",
    UNSUPPORTED_CONTRACT_VERSION: "UNSUPPORTED_CONTRACT_VERSION",
    CURRENT_EVIDENCE_UNAVAILABLE: "CURRENT_EVIDENCE_UNAVAILABLE",
    CURRENT_REFERENCE_EVIDENCE_UNAVAILABLE: "CURRENT_REFERENCE_EVIDENCE_UNAVAILABLE",
    SCENE_NOT_RESOLVABLE: "SCENE_NOT_RESOLVABLE",
});

export class SceneResultFreshnessError extends Error {
    constructor(code, message, options = {}) {
        super(message, options);
        this.name = "SceneResultFreshnessError";
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
 * Mechanical adapter that maps canonical backend plan and compiler metadata
 * into the evidence structure expected by computeSceneEffectiveInputDigest.
 *
 * Does NOT perform independent planner selection, geometry parsing, or instance filtering.
 *
 * @param {object} plan - Canonical isolated-Scene plan from backend.
 * @param {object} compileMetadata - Canonical compiler metadata from backend.
 * @returns {object} Canonical effective input evidence for computeSceneEffectiveInputDigest.
 */
export function adaptCanonicalPlanToDigestEvidence(plan, compileMetadata) {
    if (!isObject(plan) || !isObject(compileMetadata)) {
        throw new SceneResultFreshnessError(
            REASON_CODES.CURRENT_EVIDENCE_UNAVAILABLE,
            "plan and compile_metadata must be non-null objects"
        );
    }

    const ref = plan.reference || { enabled: false, reference_asset: null };
    if (ref.enabled === true || isNonEmptyString(ref.reference_asset)) {
        throw new SceneResultFreshnessError(
            REASON_CODES.CURRENT_REFERENCE_EVIDENCE_UNAVAILABLE,
            "Active reference current plan without canonical content evidence is unsupported"
        );
    }

    return {
        scene: plan.scene,
        page_context: plan.page_context,
        character_instances: plan.character_instances,
        cast: plan.cast,
        guide_state: plan.guide_state,
        local_dimensions: compileMetadata.local_dimensions,
        placement: compileMetadata.placement_mapping,
        effective_settings: compileMetadata.effective_settings,
        reference: {
            enabled: false,
            reference_asset: null,
            content_digest: null,
        },
    };
}

/**
 * Calls the canonical compile-only Python endpoint to derive authoritative
 * isolated-Scene plan and compiler metadata without side effects.
 *
 * @param {object} params
 * @param {string} [params.backendUrl] - Fixed loopback HTTP origin for Manga backend.
 * @param {typeof fetch} [params.fetchFn] - Fetch implementation (injectable for testing).
 * @param {number} [params.timeoutMs] - Request timeout.
 * @param {object} params.authoring_document - Complete Authoring Document.
 * @param {string} params.scene_id - Selected Scene ID.
 * @param {object} [params.generation_params] - Generation parameters.
 * @param {string} [params.page_id] - Optional page ID.
 * @param {number} [params.page_index] - Optional page index.
 * @param {object} [params.local_dimensions] - Optional canvas dimensions.
 * @param {number} [params.random_seed] - Optional explicit seed.
 * @returns {Promise<object>} Adapted canonical effective input evidence.
 */
export async function buildCanonicalCurrentSceneEvidence({
    backendUrl = "http://127.0.0.1:8189",
    fetchFn = fetch,
    timeoutMs = 10000,
    authoring_document,
    scene_id,
    generation_params = {},
    page_id = null,
    page_index = null,
    local_dimensions = null,
    random_seed = null,
} = {}) {
    if (!isObject(authoring_document)) {
        throw new SceneResultFreshnessError("INVALID_DOCUMENT", "authoring_document must be a non-null object");
    }
    if (!isNonEmptyString(scene_id)) {
        throw new SceneResultFreshnessError("INVALID_SCENE_ID", "scene_id must be a non-empty string");
    }

    const target = new URL(backendUrl);
    if (target.protocol !== "http:" || !["127.0.0.1", "localhost"].includes(target.hostname) ||
        target.pathname !== "/" || target.search || target.hash) {
        throw new SceneResultFreshnessError("BACKEND_TARGET_INVALID", "Manga backend must be a fixed loopback HTTP origin");
    }
    const origin = target.origin;

    const compilePayload = {
        authoring_document,
        scene_id: scene_id.trim(),
        generation_params,
    };
    if (page_id !== null && page_id !== undefined) compilePayload.page_id = page_id;
    if (page_index !== null && page_index !== undefined) compilePayload.page_index = page_index;
    if (local_dimensions !== null && local_dimensions !== undefined) compilePayload.local_dimensions = local_dimensions;
    if (random_seed !== null && random_seed !== undefined) compilePayload.random_seed = random_seed;

    let response;
    try {
        response = await fetchFn(`${origin}/tegaki/manga/generation/compile-isolated-scene`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(compilePayload),
            signal: AbortSignal.timeout(timeoutMs),
        });
    } catch (err) {
        throw new SceneResultFreshnessError(
            REASON_CODES.CURRENT_EVIDENCE_UNAVAILABLE,
            `Backend compile request failed: ${err.message}`,
            { cause: err }
        );
    }

    let result;
    try {
        result = await response.json();
    } catch (err) {
        throw new SceneResultFreshnessError(
            REASON_CODES.CURRENT_EVIDENCE_UNAVAILABLE,
            "Backend returned non-JSON response",
            { cause: err }
        );
    }

    if (!response.ok || !result || result.ok !== true) {
        const code = result?.error_code || REASON_CODES.CURRENT_EVIDENCE_UNAVAILABLE;
        const msg = result?.error || `Compile failed with status ${response.status}`;
        throw new SceneResultFreshnessError(code, msg);
    }

    const { plan, compile_metadata } = result;
    if (!isObject(plan) || !isObject(compile_metadata)) {
        throw new SceneResultFreshnessError(
            REASON_CODES.CURRENT_EVIDENCE_UNAVAILABLE,
            "Backend compile result missing plan or compile_metadata"
        );
    }

    return adaptCanonicalPlanToDigestEvidence(plan, compile_metadata);
}

/**
 * Classifies the freshness of ONE validated stored Scene Result Manifest against
 * current Scene-specific generation inputs using canonical backend planning evidence.
 *
 * @param {object} params
 * @param {string} params.manifest_id - Stored result manifest ID.
 * @param {object} [params.authoring_document] - Current Authoring Document JSON.
 * @param {object} [params.generation_params] - Current generation parameters.
 * @param {SceneResultStore} [params.store] - Store to load the target manifest.
 * @param {string} [params.backendUrl] - Loopback backend URL.
 * @param {typeof fetch} [params.fetchFn] - Injectable fetch implementation.
 * @param {number} [params.timeoutMs] - Request timeout.
 * @param {string} [params.page_id] - Optional page ID hint.
 * @param {number} [params.page_index] - Optional page index hint.
 * @param {object} [params.local_dimensions] - Optional local dimensions hint.
 * @param {number} [params.random_seed] - Optional seed hint.
 * @param {object} [params._canonicalEvidence] - Internal test hook ONLY.
 * @param {object} [params._manifest] - Internal test hook ONLY.
 * @returns {Promise<{
 *   manifest_id: string,
 *   status: "CURRENT" | "STALE" | "UNKNOWN",
 *   manifest_digest: string | null,
 *   current_digest: string | null,
 *   effective_input_contract_version: string | null,
 *   reason_code: string
 * }>}
 */
export async function classifySceneResultFreshness({
    manifest_id,
    authoring_document = null,
    generation_params = null,
    store = null,
    backendUrl = "http://127.0.0.1:8189",
    fetchFn = fetch,
    timeoutMs = 10000,
    page_id = null,
    page_index = null,
    local_dimensions = null,
    random_seed = null,
    _canonicalEvidence = null,
    _manifest = null,
} = {}) {
    if (!isNonEmptyString(manifest_id)) {
        throw new SceneResultFreshnessError("INVALID_MANIFEST_ID", "manifest_id must be a non-empty string");
    }

    // 1. Load target manifest from SceneResultStore
    let manifest = _manifest;
    if (!manifest) {
        const manifestStore = store || new SceneResultStore();
        try {
            manifest = await manifestStore.getManifest(manifest_id, { required: true });
        } catch (err) {
            throw new SceneResultFreshnessError(
                "MANIFEST_NOT_FOUND",
                `Failed to load manifest ${manifest_id}: ${err.message}`,
                { cause: err }
            );
        }
    }

    const manifestDigest = manifest.input_provenance?.effective_input_digest || null;
    const manifestContractVersion = manifest.input_provenance?.effective_input_contract_version || null;

    // Rule A: Manifest has no effective-input contract version
    if (!isNonEmptyString(manifestContractVersion)) {
        return {
            manifest_id,
            status: FRESHNESS_STATUS.UNKNOWN,
            manifest_digest: manifestDigest,
            current_digest: null,
            effective_input_contract_version: null,
            reason_code: REASON_CODES.LEGACY_CONTRACT_UNKNOWN,
        };
    }

    // Rule B: Manifest version is unsupported
    if (manifestContractVersion !== CONTRACT_VERSION) {
        return {
            manifest_id,
            status: FRESHNESS_STATUS.UNKNOWN,
            manifest_digest: manifestDigest,
            current_digest: null,
            effective_input_contract_version: manifestContractVersion,
            reason_code: REASON_CODES.UNSUPPORTED_CONTRACT_VERSION,
        };
    }

    const targetSceneId = manifest.owner?.scene_id;
    if (!isNonEmptyString(targetSceneId)) {
        return {
            manifest_id,
            status: FRESHNESS_STATUS.UNKNOWN,
            manifest_digest: manifestDigest,
            current_digest: null,
            effective_input_contract_version: CONTRACT_VERSION,
            reason_code: REASON_CODES.SCENE_NOT_RESOLVABLE,
        };
    }

    // 2. Resolve current effective-input evidence exclusively through canonical backend path
    let evidence = _canonicalEvidence;
    if (!evidence) {
        if (!authoring_document || !generation_params) {
            return {
                manifest_id,
                status: FRESHNESS_STATUS.UNKNOWN,
                manifest_digest: manifestDigest,
                current_digest: null,
                effective_input_contract_version: CONTRACT_VERSION,
                reason_code: REASON_CODES.CURRENT_EVIDENCE_UNAVAILABLE,
            };
        }

        try {
            evidence = await buildCanonicalCurrentSceneEvidence({
                backendUrl,
                fetchFn,
                timeoutMs,
                authoring_document,
                scene_id: targetSceneId,
                generation_params,
                page_id: page_id || manifest.owner?.page_id,
                page_index,
                local_dimensions: local_dimensions || manifest.artifact?.dimensions,
                random_seed,
            });
        } catch (err) {
            if (err instanceof SceneResultFreshnessError) {
                if (err.code === "SCENE_NOT_FOUND" || err.code === "AMBIGUOUS_SCENE_ID" || err.code === REASON_CODES.SCENE_NOT_RESOLVABLE) {
                    return {
                        manifest_id,
                        status: FRESHNESS_STATUS.UNKNOWN,
                        manifest_digest: manifestDigest,
                        current_digest: null,
                        effective_input_contract_version: CONTRACT_VERSION,
                        reason_code: REASON_CODES.SCENE_NOT_RESOLVABLE,
                    };
                }
                if (err.code === REASON_CODES.CURRENT_REFERENCE_EVIDENCE_UNAVAILABLE) {
                    return {
                        manifest_id,
                        status: FRESHNESS_STATUS.UNKNOWN,
                        manifest_digest: manifestDigest,
                        current_digest: null,
                        effective_input_contract_version: CONTRACT_VERSION,
                        reason_code: REASON_CODES.CURRENT_REFERENCE_EVIDENCE_UNAVAILABLE,
                    };
                }
            }
            return {
                manifest_id,
                status: FRESHNESS_STATUS.UNKNOWN,
                manifest_digest: manifestDigest,
                current_digest: null,
                effective_input_contract_version: CONTRACT_VERSION,
                reason_code: REASON_CODES.CURRENT_EVIDENCE_UNAVAILABLE,
            };
        }
    }

    if (!isObject(evidence)) {
        return {
            manifest_id,
            status: FRESHNESS_STATUS.UNKNOWN,
            manifest_digest: manifestDigest,
            current_digest: null,
            effective_input_contract_version: CONTRACT_VERSION,
            reason_code: REASON_CODES.CURRENT_EVIDENCE_UNAVAILABLE,
        };
    }

    // 3. Compute current canonical digest under the same supported version
    let currentDigestResult;
    try {
        currentDigestResult = computeSceneEffectiveInputDigest(evidence);
    } catch (err) {
        return {
            manifest_id,
            status: FRESHNESS_STATUS.UNKNOWN,
            manifest_digest: manifestDigest,
            current_digest: null,
            effective_input_contract_version: CONTRACT_VERSION,
            reason_code: REASON_CODES.CURRENT_EVIDENCE_UNAVAILABLE,
        };
    }

    const currentDigest = currentDigestResult.effective_input_digest;

    // Rule D: Same supported version + digest equal
    if (currentDigest === manifestDigest) {
        return {
            manifest_id,
            status: FRESHNESS_STATUS.CURRENT,
            manifest_digest: manifestDigest,
            current_digest: currentDigest,
            effective_input_contract_version: CONTRACT_VERSION,
            reason_code: REASON_CODES.DIGEST_MATCH,
        };
    }

    // Rule E: Same supported version + digest differs
    return {
        manifest_id,
        status: FRESHNESS_STATUS.STALE,
        manifest_digest: manifestDigest,
        current_digest: currentDigest,
        effective_input_contract_version: CONTRACT_VERSION,
        reason_code: REASON_CODES.DIGEST_MISMATCH,
    };
}
