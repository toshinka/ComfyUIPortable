/**
 * page_composite_current.mjs — Page Composite Current / Stale / Unknown Classifier.
 *
 * Classifies one immutable Page Composite against current authoring/generation inputs
 * and current composition plan semantics.
 *
 * Strictly separates:
 * 1. Historical plan provenance digest (composition_plan_digest over whole plan)
 * 2. Semantic composition digest (excludes volatile IDs, timestamps, diagnostics;
 *    includes page canvas dimensions, background, scene order, states, selected results,
 *    artifact digests, and placements).
 *
 * Statuses:
 * - CURRENT: Stored semantic composition equals current semantic composition.
 * - STALE: Semantic composition differs (pixels/placement/selection changed).
 * - UNKNOWN: Incomparable (unsupported version, prep unavailable, owner mismatch).
 */

import { createHash } from "node:crypto";
import { canonicalizeJson } from "./page_composite_manifest.mjs";
import { PageCompositeStore } from "./page_composite_store.mjs";
import { PageCompositeIndex } from "./page_composite_index.mjs";
import { preparePageComposition } from "./page_compositor_prep.mjs";

export const PAGE_COMPOSITE_SEMANTIC_DIGEST_VERSION = "1.0.0";
export const EXPECTED_PLAN_SCHEMA_ID = "TEGAKI_PAGE_COMPOSITION_PLAN";
export const EXPECTED_PLAN_SCHEMA_VERSION = "1.0.0";

export const CURRENT_STATUS = Object.freeze({
    CURRENT: "CURRENT",
    STALE: "STALE",
    UNKNOWN: "UNKNOWN",
});

export const CURRENT_REASON = Object.freeze({
    SEMANTIC_PLAN_MATCH: "SEMANTIC_PLAN_MATCH",
    SEMANTIC_PLAN_MISMATCH: "SEMANTIC_PLAN_MISMATCH",
    STORED_COMPOSITE_UNAVAILABLE: "STORED_COMPOSITE_UNAVAILABLE",
    CURRENT_PLAN_UNAVAILABLE: "CURRENT_PLAN_UNAVAILABLE",
    UNSUPPORTED_STORED_PLAN_VERSION: "UNSUPPORTED_STORED_PLAN_VERSION",
    UNSUPPORTED_CURRENT_PLAN_VERSION: "UNSUPPORTED_CURRENT_PLAN_VERSION",
    OWNER_MISMATCH: "OWNER_MISMATCH",
    CANONICALIZATION_FAILED: "CANONICALIZATION_FAILED",
});

export class PageCompositeCurrentError extends Error {
    constructor(code, message, options = {}) {
        super(message, options);
        this.name = "PageCompositeCurrentError";
        this.code = code;
    }
}

const FORBIDDEN_CALLER_FIELDS = Object.freeze([
    "stored_manifest",
    "stored_plan",
    "current_plan",
    "composition_plan",
    "stored_digest",
    "semantic_digest",
    "selected_manifest_id",
    "selected_manifest_ids",
    "artifact_locator",
    "placement",
    "placement_overrides",
]);

const UUID_V4_REGEX = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

function isObject(val) {
    return val !== null && typeof val === "object" && !Array.isArray(val);
}

function isNonEmptyString(val) {
    return typeof val === "string" && val.trim().length > 0;
}

/**
 * Builds the canonical semantic payload for a Page Composition Plan,
 * excluding volatile/non-pixel metadata (plan_id, created_at, diagnostics).
 *
 * @param {object} plan
 * @returns {object}
 */
export function buildSemanticPayload(plan) {
    if (!isObject(plan)) {
        throw new PageCompositeCurrentError("INVALID_PLAN", "Composition plan must be a non-null object");
    }

    const scenes = Array.isArray(plan.scenes) ? plan.scenes : [];

    return {
        semantic_version: PAGE_COMPOSITE_SEMANTIC_DIGEST_VERSION,
        page: {
            document_id: plan.page?.document_id ?? null,
            page_id: plan.page?.page_id ?? null,
            width: plan.page?.width ?? null,
            height: plan.page?.height ?? null,
        },
        background: {
            mode: plan.background?.mode ?? null,
            value: plan.background?.value ?? null,
        },
        scenes: scenes.map(scene => ({
            scene_id: scene.scene_id ?? null,
            order: scene.order ?? 0,
            state: scene.state ?? null,
            selected_result: scene.selected_result ? {
                manifest_id: scene.selected_result.manifest_id ?? null,
                artifact: {
                    locator: scene.selected_result.artifact?.locator ?? null,
                    dimensions: scene.selected_result.artifact?.dimensions ? {
                        width: scene.selected_result.artifact.dimensions.width,
                        height: scene.selected_result.artifact.dimensions.height,
                    } : null,
                    content_digest: scene.selected_result.artifact?.content_digest ?? null,
                },
                placement: scene.selected_result.placement ? {
                    page_target_rect: scene.selected_result.placement.page_target_rect ? {
                        x: scene.selected_result.placement.page_target_rect.x,
                        y: scene.selected_result.placement.page_target_rect.y,
                        width: scene.selected_result.placement.page_target_rect.width,
                        height: scene.selected_result.placement.page_target_rect.height,
                    } : null,
                    local_source_rect: scene.selected_result.placement.local_source_rect ? {
                        x: scene.selected_result.placement.local_source_rect.x,
                        y: scene.selected_result.placement.local_source_rect.y,
                        width: scene.selected_result.placement.local_source_rect.width,
                        height: scene.selected_result.placement.local_source_rect.height,
                    } : null,
                    transform: scene.selected_result.placement.transform ?? {},
                    target_page_dimensions: scene.selected_result.placement.target_page_dimensions ? {
                        width: scene.selected_result.placement.target_page_dimensions.width,
                        height: scene.selected_result.placement.target_page_dimensions.height,
                    } : null,
                } : null,
            } : null,
        })),
    };
}

/**
 * Computes deterministic SHA-256 hash over canonical JSON of the semantic plan payload.
 *
 * @param {object} plan
 * @returns {string} 64-hex SHA-256 digest
 */
export function computeSemanticCompositionDigest(plan) {
    const payload = buildSemanticPayload(plan);
    const canonical = canonicalizeJson(payload);
    return createHash("sha256").update(canonical, "utf8").digest("hex");
}

export class PageCompositeCurrentClassifier {
    /**
     * @param {object} [options]
     * @param {PageCompositeStore} [options.store]
     * @param {PageCompositeIndex} [options.index]
     * @param {Function} [options.prepFn]
     * @param {SceneResultStore} [options.sceneStore]
     * @param {SceneResultIndex} [options.sceneIndex]
     */
    constructor({
        store = null,
        index = null,
        prepFn = preparePageComposition,
        sceneStore = null,
        sceneIndex = null,
    } = {}) {
        this.store = store || new PageCompositeStore();
        this.index = index || new PageCompositeIndex({ store: this.store });
        this.prepFn = prepFn;
        this.sceneStore = sceneStore;
        this.sceneIndex = sceneIndex;
    }

    /**
     * Classifies one stored Page Composite against current authoring/generation inputs.
     *
     * @param {object} input
     * @param {string} input.composite_id
     * @param {object} input.authoring_document
     * @param {object} [input.generation_params={}]
     * @param {string} [input.page_id]
     * @param {number} [input.page_index]
     * @returns {Promise<{
     *   composite_id: string,
     *   status: "CURRENT"|"STALE"|"UNKNOWN",
     *   reason_code: string,
     *   historical_plan_digest: string|null,
     *   stored_semantic_digest: string|null,
     *   current_semantic_digest: string|null,
     *   semantic_contract_version: string
     * }>}
     */
    async classifyCurrentPageComposite(input) {
        if (!isObject(input)) {
            throw new PageCompositeCurrentError("INVALID_REQUEST", "Input must be a non-null object");
        }

        // 1. Enforce caller boundaries
        for (const forbidden of FORBIDDEN_CALLER_FIELDS) {
            if (forbidden in input) {
                throw new PageCompositeCurrentError(
                    "FORBIDDEN_CALLER_FIELD",
                    `Caller cannot supply authority or plan override field '${forbidden}'`
                );
            }
        }

        const compositeId = input.composite_id;
        if (!isNonEmptyString(compositeId) || !UUID_V4_REGEX.test(compositeId)) {
            throw new PageCompositeCurrentError(
                "INVALID_COMPOSITE_ID",
                `composite_id must be a valid UUIDv4 string, got '${compositeId}'`
            );
        }

        if (!isObject(input.authoring_document)) {
            throw new PageCompositeCurrentError("INVALID_REQUEST", "authoring_document object is required");
        }

        const authoringDoc = input.authoring_document;
        const genParams = input.generation_params || {};

        // 2. Resolve authoritative stored composite through Index / Store
        let storedResult;
        try {
            storedResult = await this.index.resolveComposite(compositeId, { required: true });
        } catch (err) {
            return {
                composite_id: compositeId,
                status: CURRENT_STATUS.UNKNOWN,
                reason_code: CURRENT_REASON.STORED_COMPOSITE_UNAVAILABLE,
                historical_plan_digest: null,
                stored_semantic_digest: null,
                current_semantic_digest: null,
                semantic_contract_version: PAGE_COMPOSITE_SEMANTIC_DIGEST_VERSION,
            };
        }

        const storedManifest = storedResult.manifest;
        const storedPlan = storedManifest.composition_plan;
        const historicalPlanDigest = storedManifest.composition_plan_digest || null;

        // 3. Stored plan contract validation
        if (
            !isObject(storedPlan) ||
            storedPlan.schema_id !== EXPECTED_PLAN_SCHEMA_ID ||
            storedPlan.schema_version !== EXPECTED_PLAN_SCHEMA_VERSION
        ) {
            return {
                composite_id: compositeId,
                status: CURRENT_STATUS.UNKNOWN,
                reason_code: CURRENT_REASON.UNSUPPORTED_STORED_PLAN_VERSION,
                historical_plan_digest: historicalPlanDigest,
                stored_semantic_digest: null,
                current_semantic_digest: null,
                semantic_contract_version: PAGE_COMPOSITE_SEMANTIC_DIGEST_VERSION,
            };
        }

        // 4. Compute stored semantic digest
        let storedSemanticDigest;
        try {
            storedSemanticDigest = computeSemanticCompositionDigest(storedPlan);
        } catch (err) {
            return {
                composite_id: compositeId,
                status: CURRENT_STATUS.UNKNOWN,
                reason_code: CURRENT_REASON.CANONICALIZATION_FAILED,
                historical_plan_digest: historicalPlanDigest,
                stored_semantic_digest: null,
                current_semantic_digest: null,
                semantic_contract_version: PAGE_COMPOSITE_SEMANTIC_DIGEST_VERSION,
            };
        }

        // 5. Owner consistency verification
        const storedDocId = storedManifest.owner?.document_id || storedPlan.page?.document_id;
        const storedPageId = storedManifest.owner?.page_id || storedPlan.page?.page_id;

        if (authoringDoc.document_id !== storedDocId) {
            return {
                composite_id: compositeId,
                status: CURRENT_STATUS.UNKNOWN,
                reason_code: CURRENT_REASON.OWNER_MISMATCH,
                historical_plan_digest: historicalPlanDigest,
                stored_semantic_digest: storedSemanticDigest,
                current_semantic_digest: null,
                semantic_contract_version: PAGE_COMPOSITE_SEMANTIC_DIGEST_VERSION,
            };
        }

        if (input.page_id && input.page_id !== storedPageId) {
            return {
                composite_id: compositeId,
                status: CURRENT_STATUS.UNKNOWN,
                reason_code: CURRENT_REASON.OWNER_MISMATCH,
                historical_plan_digest: historicalPlanDigest,
                stored_semantic_digest: storedSemanticDigest,
                current_semantic_digest: null,
                semantic_contract_version: PAGE_COMPOSITE_SEMANTIC_DIGEST_VERSION,
            };
        }

        // 6. Obtain current plan authority via preparePageComposition
        let currentPlan;
        try {
            currentPlan = await this.prepFn({
                authoring_document: authoringDoc,
                page_id: storedPageId,
                page_index: input.page_index ?? null,
                generation_params: genParams,
                store: this.sceneStore,
                index: this.sceneIndex,
            });
        } catch (err) {
            return {
                composite_id: compositeId,
                status: CURRENT_STATUS.UNKNOWN,
                reason_code: CURRENT_REASON.CURRENT_PLAN_UNAVAILABLE,
                historical_plan_digest: historicalPlanDigest,
                stored_semantic_digest: storedSemanticDigest,
                current_semantic_digest: null,
                semantic_contract_version: PAGE_COMPOSITE_SEMANTIC_DIGEST_VERSION,
            };
        }

        // 7. Current plan contract validation
        if (
            !isObject(currentPlan) ||
            currentPlan.schema_id !== EXPECTED_PLAN_SCHEMA_ID ||
            currentPlan.schema_version !== EXPECTED_PLAN_SCHEMA_VERSION
        ) {
            return {
                composite_id: compositeId,
                status: CURRENT_STATUS.UNKNOWN,
                reason_code: CURRENT_REASON.UNSUPPORTED_CURRENT_PLAN_VERSION,
                historical_plan_digest: historicalPlanDigest,
                stored_semantic_digest: storedSemanticDigest,
                current_semantic_digest: null,
                semantic_contract_version: PAGE_COMPOSITE_SEMANTIC_DIGEST_VERSION,
            };
        }

        // Current plan owner verification
        if (
            currentPlan.page?.document_id !== storedDocId ||
            currentPlan.page?.page_id !== storedPageId
        ) {
            return {
                composite_id: compositeId,
                status: CURRENT_STATUS.UNKNOWN,
                reason_code: CURRENT_REASON.OWNER_MISMATCH,
                historical_plan_digest: historicalPlanDigest,
                stored_semantic_digest: storedSemanticDigest,
                current_semantic_digest: null,
                semantic_contract_version: PAGE_COMPOSITE_SEMANTIC_DIGEST_VERSION,
            };
        }

        // 8. Compute current semantic digest
        let currentSemanticDigest;
        try {
            currentSemanticDigest = computeSemanticCompositionDigest(currentPlan);
        } catch (err) {
            return {
                composite_id: compositeId,
                status: CURRENT_STATUS.UNKNOWN,
                reason_code: CURRENT_REASON.CANONICALIZATION_FAILED,
                historical_plan_digest: historicalPlanDigest,
                stored_semantic_digest: storedSemanticDigest,
                current_semantic_digest: null,
                semantic_contract_version: PAGE_COMPOSITE_SEMANTIC_DIGEST_VERSION,
            };
        }

        // 9. Semantic comparison
        if (storedSemanticDigest === currentSemanticDigest) {
            return {
                composite_id: compositeId,
                status: CURRENT_STATUS.CURRENT,
                reason_code: CURRENT_REASON.SEMANTIC_PLAN_MATCH,
                historical_plan_digest: historicalPlanDigest,
                stored_semantic_digest: storedSemanticDigest,
                current_semantic_digest: currentSemanticDigest,
                semantic_contract_version: PAGE_COMPOSITE_SEMANTIC_DIGEST_VERSION,
            };
        }

        return {
            composite_id: compositeId,
            status: CURRENT_STATUS.STALE,
            reason_code: CURRENT_REASON.SEMANTIC_PLAN_MISMATCH,
            historical_plan_digest: historicalPlanDigest,
            stored_semantic_digest: storedSemanticDigest,
            current_semantic_digest: currentSemanticDigest,
            semantic_contract_version: PAGE_COMPOSITE_SEMANTIC_DIGEST_VERSION,
        };
    }
}

/**
 * Functional wrapper for classifyCurrentPageComposite.
 */
export async function classifyCurrentPageComposite(input, dependencies = {}) {
    const classifier = new PageCompositeCurrentClassifier(dependencies);
    return classifier.classifyCurrentPageComposite(input);
}
