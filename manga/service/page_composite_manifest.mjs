/**
 * page_composite_manifest.mjs — Immutable Page Composite Manifest Schema & Validation.
 *
 * Defines the TEGAKI_PAGE_COMPOSITE_MANIFEST v1.0.0 schema, deterministic plan
 * canonicalization, plan digest calculation, and strict manifest validation.
 */

import { createHash } from "node:crypto";

export const SCHEMA_ID = "TEGAKI_PAGE_COMPOSITE_MANIFEST";
export const SCHEMA_VERSION = "1.0.0";

const EXPECTED_PLAN_SCHEMA_ID = "TEGAKI_PAGE_COMPOSITION_PLAN";
const EXPECTED_PLAN_SCHEMA_VERSION = "1.0.0";

const SHA256_HEX_REGEX = /^[0-9a-f]{64}$/i;
const UUID_V4_REGEX = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

export class PageCompositeManifestError extends Error {
    constructor(code, message, options = {}) {
        super(message, options);
        this.name = "PageCompositeManifestError";
        this.code = code;
    }
}

function isObject(val) {
    return val !== null && typeof val === "object" && !Array.isArray(val);
}

function isNonEmptyString(val) {
    return typeof val === "string" && val.trim().length > 0;
}

function isPositiveInteger(val) {
    return typeof val === "number" && Number.isInteger(val) && val > 0;
}

/**
 * Deterministically serializes a value into canonical JSON:
 * - Object keys sorted recursively
 * - Array order preserved
 * - Primitive values preserved
 * - Rejects non-finite numbers and unsupported types
 *
 * @param {unknown} value
 * @returns {string}
 */
export function canonicalizeJson(value) {
    if (value === null) return "null";
    if (typeof value === "boolean") return value ? "true" : "false";
    if (typeof value === "number") {
        if (!Number.isFinite(value)) {
            throw new PageCompositeManifestError("INVALID_JSON_VALUE", `Non-finite number cannot be serialized: ${value}`);
        }
        return JSON.stringify(value);
    }
    if (typeof value === "string") {
        return JSON.stringify(value);
    }
    if (Array.isArray(value)) {
        return `[${value.map(canonicalizeJson).join(",")}]`;
    }
    if (isObject(value)) {
        const sortedKeys = Object.keys(value).sort();
        const parts = sortedKeys.map(k => `${JSON.stringify(k)}:${canonicalizeJson(value[k])}`);
        return `{${parts.join(",")}}`;
    }
    throw new PageCompositeManifestError("INVALID_JSON_VALUE", `Unsupported JSON value type: ${typeof value}`);
}

/**
 * Computes deterministic SHA-256 digest over canonical UTF-8 bytes of a composition plan.
 *
 * @param {object} plan
 * @returns {string} 64-hex SHA-256 digest
 */
export function computeCompositionPlanDigest(plan) {
    if (!isObject(plan)) {
        throw new PageCompositeManifestError("INVALID_PLAN", "Composition plan must be an object");
    }
    const canonical = canonicalizeJson(plan);
    return createHash("sha256").update(canonical, "utf8").digest("hex");
}

/**
 * Validates a TEGAKI_PAGE_COMPOSITION_PLAN v1.0.0 envelope.
 *
 * @param {object} plan
 * @returns {object} Validated plan (shallow/deep validated)
 */
export function validateCompositionPlan(plan) {
    if (!isObject(plan)) {
        throw new PageCompositeManifestError("INVALID_PLAN", "Composition plan must be a non-null object");
    }
    if (plan.schema_id !== EXPECTED_PLAN_SCHEMA_ID) {
        throw new PageCompositeManifestError(
            "INVALID_PLAN_SCHEMA",
            `Expected plan schema_id '${EXPECTED_PLAN_SCHEMA_ID}', got '${plan.schema_id}'`
        );
    }
    if (plan.schema_version !== EXPECTED_PLAN_SCHEMA_VERSION) {
        throw new PageCompositeManifestError(
            "INVALID_PLAN_VERSION",
            `Expected plan schema_version '${EXPECTED_PLAN_SCHEMA_VERSION}', got '${plan.schema_version}'`
        );
    }
    if (!isNonEmptyString(plan.plan_id)) {
        throw new PageCompositeManifestError("INVALID_PLAN_ID", "Plan must contain a non-empty plan_id");
    }

    // Page metadata
    if (!isObject(plan.page)) {
        throw new PageCompositeManifestError("INVALID_PLAN_PAGE", "Plan must contain page object");
    }
    if (!isNonEmptyString(plan.page.document_id)) {
        throw new PageCompositeManifestError("INVALID_PLAN_PAGE", "Plan page must declare document_id");
    }
    if (!isNonEmptyString(plan.page.page_id)) {
        throw new PageCompositeManifestError("INVALID_PLAN_PAGE", "Plan page must declare page_id");
    }
    if (!isPositiveInteger(plan.page.width) || !isPositiveInteger(plan.page.height)) {
        throw new PageCompositeManifestError("INVALID_PLAN_PAGE", "Plan page width and height must be positive integers");
    }

    // Background
    if (!isObject(plan.background) || plan.background.mode !== "solid" || plan.background.value !== "white") {
        throw new PageCompositeManifestError("INVALID_PLAN_BACKGROUND", "Plan background must be mode='solid', value='white'");
    }

    // Scenes array
    if (!Array.isArray(plan.scenes)) {
        throw new PageCompositeManifestError("INVALID_PLAN_SCENES", "Plan scenes must be an array");
    }

    for (let i = 0; i < plan.scenes.length; i++) {
        const slot = plan.scenes[i];
        if (!isObject(slot) || !isNonEmptyString(slot.scene_id)) {
            throw new PageCompositeManifestError("INVALID_PLAN_SCENE", `Scene slot at index ${i} lacks valid scene_id`);
        }
        if (slot.state === "CURRENT_RESULT") {
            if (!isObject(slot.selected_result)) {
                throw new PageCompositeManifestError(
                    "INVALID_PLAN_SCENE",
                    `Scene slot '${slot.scene_id}' in CURRENT_RESULT must specify selected_result`
                );
            }
            const sel = slot.selected_result;
            if (!isNonEmptyString(sel.manifest_id)) {
                throw new PageCompositeManifestError(
                    "INVALID_PLAN_SCENE",
                    `Scene slot '${slot.scene_id}' selected_result must declare manifest_id`
                );
            }
            if (!isObject(sel.artifact) || !isObject(sel.placement)) {
                throw new PageCompositeManifestError(
                    "INVALID_PLAN_SCENE",
                    `Scene slot '${slot.scene_id}' selected_result must declare artifact and placement`
                );
            }
        } else if (slot.state === "UNFILLED") {
            if (slot.selected_result !== null && slot.selected_result !== undefined) {
                throw new PageCompositeManifestError(
                    "INVALID_PLAN_SCENE",
                    `Scene slot '${slot.scene_id}' in UNFILLED must have selected_result === null`
                );
            }
        } else {
            throw new PageCompositeManifestError(
                "INVALID_PLAN_SCENE",
                `Scene slot '${slot.scene_id}' has unknown state '${slot.state}'`
            );
        }
    }

    return plan;
}

/**
 * Validates a Page Composite Manifest against strict schema requirements.
 *
 * @param {object} manifest - Manifest object to validate.
 * @returns {object} Validated independent manifest copy.
 */
export function validatePageCompositeManifest(manifest) {
    if (!isObject(manifest)) {
        throw new PageCompositeManifestError("INVALID_MANIFEST", "Manifest must be a non-null object");
    }

    // 1. Schema ID & Version
    if (manifest.schema_id !== SCHEMA_ID) {
        throw new PageCompositeManifestError(
            "INVALID_SCHEMA_ID",
            `Expected schema_id '${SCHEMA_ID}', got '${manifest.schema_id}'`
        );
    }
    if (manifest.schema_version !== SCHEMA_VERSION) {
        throw new PageCompositeManifestError(
            "INVALID_SCHEMA_VERSION",
            `Expected schema_version '${SCHEMA_VERSION}', got '${manifest.schema_version}'`
        );
    }

    // 2. Composite ID (strict UUIDv4)
    if (!isNonEmptyString(manifest.composite_id) || !UUID_V4_REGEX.test(manifest.composite_id)) {
        throw new PageCompositeManifestError(
            "INVALID_COMPOSITE_ID",
            `composite_id must be a valid UUIDv4 string, got '${manifest.composite_id}'`
        );
    }

    // 3. Created At (ISO 8601)
    if (!isNonEmptyString(manifest.created_at) || Number.isNaN(Date.parse(manifest.created_at))) {
        throw new PageCompositeManifestError(
            "INVALID_CREATED_AT",
            `created_at must be a valid ISO 8601 string, got '${manifest.created_at}'`
        );
    }

    // 4. Composition Plan Validation
    validateCompositionPlan(manifest.composition_plan);
    const plan = manifest.composition_plan;

    // 5. Owner Identity
    if (!isObject(manifest.owner)) {
        throw new PageCompositeManifestError("INVALID_OWNER", "Manifest must contain owner object");
    }
    if (!isNonEmptyString(manifest.owner.document_id) || manifest.owner.document_id !== plan.page.document_id) {
        throw new PageCompositeManifestError(
            "INVALID_OWNER",
            `owner.document_id '${manifest.owner?.document_id}' must match plan.page.document_id '${plan.page.document_id}'`
        );
    }
    if (!isNonEmptyString(manifest.owner.page_id) || manifest.owner.page_id !== plan.page.page_id) {
        throw new PageCompositeManifestError(
            "INVALID_OWNER",
            `owner.page_id '${manifest.owner?.page_id}' must match plan.page.page_id '${plan.page.page_id}'`
        );
    }

    // 6. Plan Digest
    if (!isNonEmptyString(manifest.composition_plan_digest) || !SHA256_HEX_REGEX.test(manifest.composition_plan_digest)) {
        throw new PageCompositeManifestError(
            "INVALID_PLAN_DIGEST",
            "composition_plan_digest must be a 64-hex SHA-256 digest"
        );
    }
    const expectedPlanDigest = computeCompositionPlanDigest(plan);
    if (manifest.composition_plan_digest !== expectedPlanDigest) {
        throw new PageCompositeManifestError(
            "PLAN_DIGEST_MISMATCH",
            `composition_plan_digest '${manifest.composition_plan_digest}' does not match computed '${expectedPlanDigest}'`
        );
    }

    // 7. Artifact Facts
    if (!isObject(manifest.artifact)) {
        throw new PageCompositeManifestError("INVALID_ARTIFACT", "Manifest must contain artifact object");
    }
    const art = manifest.artifact;
    if (!isNonEmptyString(art.artifact_ref)) {
        throw new PageCompositeManifestError("INVALID_ARTIFACT", "artifact.artifact_ref must be a non-empty string");
    }
    // Ref must be store-owned relative path, no traversal or drive letters
    if (art.artifact_ref.includes(":") || art.artifact_ref.includes("..") || art.artifact_ref.includes("\\") || art.artifact_ref.startsWith("/")) {
        throw new PageCompositeManifestError(
            "INVALID_ARTIFACT_REF",
            `artifact_ref '${art.artifact_ref}' must be a store-relative path without path traversal`
        );
    }
    if (!isNonEmptyString(art.content_digest) || !SHA256_HEX_REGEX.test(art.content_digest)) {
        throw new PageCompositeManifestError(
            "INVALID_ARTIFACT_DIGEST",
            "artifact.content_digest must be a 64-hex SHA-256 digest"
        );
    }
    if (!isPositiveInteger(art.declared_width) || art.declared_width !== plan.page.width) {
        throw new PageCompositeManifestError(
            "INVALID_ARTIFACT_DIMENSIONS",
            `artifact.declared_width (${art.declared_width}) must match plan page width (${plan.page.width})`
        );
    }
    if (!isPositiveInteger(art.declared_height) || art.declared_height !== plan.page.height) {
        throw new PageCompositeManifestError(
            "INVALID_ARTIFACT_DIMENSIONS",
            `artifact.declared_height (${art.declared_height}) must match plan page height (${plan.page.height})`
        );
    }
    if (!isPositiveInteger(art.byte_length)) {
        throw new PageCompositeManifestError(
            "INVALID_ARTIFACT_BYTE_LENGTH",
            `artifact.byte_length must be a positive integer, got ${art.byte_length}`
        );
    }
    if (art.media_type !== "image/png") {
        throw new PageCompositeManifestError(
            "INVALID_MEDIA_TYPE",
            `artifact.media_type must be 'image/png', got '${art.media_type}'`
        );
    }

    // 8. Statistics Consistency
    if (!isObject(manifest.statistics)) {
        throw new PageCompositeManifestError("INVALID_STATISTICS", "Manifest must contain statistics object");
    }
    const stats = manifest.statistics;
    const totalScenes = plan.scenes.length;
    const composedScenes = plan.scenes.filter(s => s.state === "CURRENT_RESULT").length;
    const unfilledScenes = plan.scenes.filter(s => s.state === "UNFILLED").length;

    if (stats.total_scenes !== totalScenes || stats.composed_scenes !== composedScenes || stats.unfilled_scenes !== unfilledScenes) {
        throw new PageCompositeManifestError(
            "STATISTICS_MISMATCH",
            `Manifest statistics do not match plan: expected total=${totalScenes}, composed=${composedScenes}, unfilled=${unfilledScenes}`
        );
    }

    return structuredClone(manifest);
}
