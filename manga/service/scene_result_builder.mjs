/**
 * scene_result_builder.mjs — Pure builder for finalized isolated-Scene result manifests.
 *
 * Assembles an immutable, schema-compliant isolated-Scene result manifest from
 * complete, explicitly supplied execution provenance. Validates cross-stage consistency
 * between original Authoring identity, isolated-Scene plan, compile metadata, completed
 * generation job, reference asset analysis, output PNG artifact facts, and placement.
 */

import {
    SCHEMA_ID,
    SCHEMA_VERSION,
    REQUIRED_DIGEST_CONTRACT_VERSION_V1_1,
    validateSceneResultManifest,
} from "./scene_result_manifest.mjs";
import { computeSceneEffectiveInputDigest } from "./scene_effective_input_digest.mjs";

export class SceneResultBuilderError extends Error {
    constructor(code, message, options = {}) {
        super(message, options);
        this.name = "SceneResultBuilderError";
        this.code = code;
    }
}

const UUID_V4_REGEX = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
const UUID_ANY_REGEX = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
const SHA256_HEX_REGEX = /^[0-9a-f]{64}$/i;

function isObject(val) {
    return val !== null && typeof val === "object" && !Array.isArray(val);
}

function isNonEmptyString(val) {
    return typeof val === "string" && val.trim().length > 0;
}

function isPositiveInteger(val) {
    return typeof val === "number" && Number.isInteger(val) && val > 0;
}

function isFiniteNumber(val) {
    return typeof val === "number" && Number.isFinite(val);
}

/**
 * Builds and finalizes an isolated-Scene result manifest from complete execution evidence.
 *
 * @param {object} evidence - Structured provenance evidence.
 * @returns {object} Finalized manifest validated against validateSceneResultManifest.
 * @throws {SceneResultBuilderError} On missing, inconsistent, or invalid evidence.
 */
export function buildSceneResultManifest(evidence, options = {}) {
    if (!isObject(evidence)) {
        throw new SceneResultBuilderError(
            "INVALID_EVIDENCE",
            "Evidence must be a non-null object"
        );
    }

    // 1. Caller-supplied UUIDv4 manifest_id
    const manifestId = evidence.manifest_id;
    if (!isNonEmptyString(manifestId) || !UUID_V4_REGEX.test(manifestId)) {
        throw new SceneResultBuilderError(
            "INVALID_MANIFEST_ID",
            `manifest_id must be an explicit, valid UUIDv4 string, got "${manifestId}"`
        );
    }

    // 2. Explicit Creation Timestamp
    const createdAt = evidence.created_at;
    if (!isNonEmptyString(createdAt) || Number.isNaN(Date.parse(createdAt))) {
        throw new SceneResultBuilderError(
            "INVALID_TIMESTAMP",
            `created_at must be an explicit ISO 8601 string, got "${createdAt}"`
        );
    }

    // 3. Original Owning Identity
    const owner = isObject(evidence.owner) ? evidence.owner : evidence;
    const documentId = owner.document_id;
    const pageId = owner.page_id;
    const sceneId = owner.scene_id;

    if (!isNonEmptyString(documentId) || !isNonEmptyString(pageId) || !isNonEmptyString(sceneId)) {
        throw new SceneResultBuilderError(
            "MISSING_OWNER_IDENTITY",
            "Evidence must explicitly supply document_id, page_id, and scene_id"
        );
    }

    // 4. Durable Original Authoring Snapshot Provenance
    const inputProv = isObject(evidence.input_provenance) ? evidence.input_provenance : evidence;
    const snapshotRef = inputProv.authoring_snapshot_ref || evidence.snapshot_ref;
    const snapshotDigest = inputProv.authoring_snapshot_digest || evidence.snapshot_digest || evidence.content_digest;

    if (!isNonEmptyString(snapshotRef)) {
        throw new SceneResultBuilderError(
            "MISSING_SNAPSHOT_PROVENANCE",
            "Original authoring snapshot reference (snapshot_ref) must be a non-empty string"
        );
    }
    if (!isNonEmptyString(snapshotDigest) || !SHA256_HEX_REGEX.test(snapshotDigest)) {
        throw new SceneResultBuilderError(
            "MISSING_SNAPSHOT_PROVENANCE",
            "Original authoring snapshot content digest must be a 64-hex SHA-256 digest"
        );
    }

    // 5. Isolated-Scene Plan & Compiler Metadata
    const plan = evidence.plan;
    const compileMeta = evidence.compile_metadata;

    if (!isObject(plan)) {
        throw new SceneResultBuilderError(
            "MISSING_PLAN",
            "Evidence must contain isolated-Scene plan object"
        );
    }
    if (!isObject(compileMeta)) {
        throw new SceneResultBuilderError(
            "MISSING_COMPILE_METADATA",
            "Evidence must contain compile_metadata object"
        );
    }

    // Cross-check Scene identity
    const planSceneId = plan.scene?.scene_id || plan.scene_id;
    if (planSceneId !== sceneId) {
        throw new SceneResultBuilderError(
            "IDENTITY_MISMATCH",
            `Plan scene_id "${planSceneId}" does not match owning scene_id "${sceneId}"`
        );
    }
    const compileSceneId = compileMeta.scene_id || compileMeta.scene?.scene_id;
    if (compileSceneId !== sceneId) {
        throw new SceneResultBuilderError(
            "IDENTITY_MISMATCH",
            `Compiler metadata scene_id "${compileSceneId}" does not match owning scene_id "${sceneId}"`
        );
    }

    // Cross-check Page identity
    const planPageId = plan.page_context?.page_id || plan.page_id;
    if (planPageId !== pageId) {
        throw new SceneResultBuilderError(
            "IDENTITY_MISMATCH",
            `Plan page_id "${planPageId}" does not match owning page_id "${pageId}"`
        );
    }
    const compilePageId = compileMeta.page_context?.page_id || compileMeta.page_id;
    if (compilePageId !== undefined && compilePageId !== pageId) {
        throw new SceneResultBuilderError(
            "IDENTITY_MISMATCH",
            `Compiler metadata page_id "${compilePageId}" does not match owning page_id "${pageId}"`
        );
    }

    // Cross-check local canvas dimensions
    const planCanvas = plan.local_canvas || plan.scene?.local_area;
    const compileDims = compileMeta.local_dimensions;
    if (!isObject(compileDims) || !isPositiveInteger(compileDims.width) || !isPositiveInteger(compileDims.height)) {
        throw new SceneResultBuilderError(
            "MISSING_DIMENSIONS",
            "compile_metadata must contain positive integer local_dimensions width and height"
        );
    }
    if (isObject(planCanvas) && planCanvas.width !== undefined && planCanvas.height !== undefined) {
        if (planCanvas.width !== compileDims.width || planCanvas.height !== compileDims.height) {
            throw new SceneResultBuilderError(
                "DIMENSION_MISMATCH",
                `Plan canvas dimensions [${planCanvas.width}x${planCanvas.height}] do not match compiler dimensions [${compileDims.width}x${compileDims.height}]`
            );
        }
    }

    // 6. Placement Mapping & Original Page Geometry
    const placementMapping = compileMeta.placement_mapping || plan.placement_mapping || evidence.placement;
    if (!isObject(placementMapping)) {
        throw new SceneResultBuilderError(
            "MISSING_PLACEMENT",
            "Evidence must contain placement mapping object"
        );
    }

    const pageTargetRect = placementMapping.page_target_rect || placementMapping.target_rect;
    const localSourceRect = placementMapping.local_source_rect || placementMapping.source_rect;
    const transform = placementMapping.transform;
    const targetPageDims = placementMapping.target_page_dimensions || placementMapping.page_dimensions || {
        width: plan.page_context?.width_px,
        height: plan.page_context?.height_px,
    };

    if (!isObject(pageTargetRect) || !isObject(localSourceRect) || !isObject(transform) || !isObject(targetPageDims)) {
        throw new SceneResultBuilderError(
            "INVALID_PLACEMENT",
            "Placement must include page_target_rect, local_source_rect, transform, and target_page_dimensions"
        );
    }

    // Verify consistency between plan page_context and placement target page dimensions
    if (plan.page_context?.width_px && targetPageDims.width && plan.page_context.width_px !== targetPageDims.width) {
        throw new SceneResultBuilderError(
            "DIMENSION_MISMATCH",
            `Plan page width (${plan.page_context.width_px}) does not match placement page width (${targetPageDims.width})`
        );
    }
    if (plan.page_context?.height_px && targetPageDims.height && plan.page_context.height_px !== targetPageDims.height) {
        throw new SceneResultBuilderError(
            "DIMENSION_MISMATCH",
            `Plan page height (${plan.page_context.height_px}) does not match placement page height (${targetPageDims.height})`
        );
    }

    // 7. Completed Generation Job Record
    const job = isObject(evidence.job) ? evidence.job : (isObject(evidence.execution) ? evidence.execution : null);
    if (!isObject(job)) {
        throw new SceneResultBuilderError(
            "MISSING_JOB_EVIDENCE",
            "Evidence must contain completed generation job record"
        );
    }
    if (!isNonEmptyString(job.job_id) || !UUID_ANY_REGEX.test(job.job_id)) {
        throw new SceneResultBuilderError(
            "INVALID_JOB_EVIDENCE",
            `job.job_id must be a valid UUID, got "${job.job_id}"`
        );
    }
    if (!isNonEmptyString(job.prompt_id) || !UUID_ANY_REGEX.test(job.prompt_id)) {
        throw new SceneResultBuilderError(
            "INVALID_JOB_EVIDENCE",
            `job.prompt_id must be a valid UUID, got "${job.prompt_id}"`
        );
    }
    if (job.state !== "SUCCEEDED") {
        throw new SceneResultBuilderError(
            "JOB_NOT_SUCCEEDED",
            `Generation job must be in "SUCCEEDED" state to assemble result, got "${job.state}"`
        );
    }

    // Cross-check graph_digest and page_compile_plan_digest
    const jobGraphDigest = job.graph_digest;
    const compileGraphDigest = compileMeta.graph_digest;
    if (!isNonEmptyString(jobGraphDigest) || !SHA256_HEX_REGEX.test(jobGraphDigest)) {
        throw new SceneResultBuilderError(
            "INVALID_JOB_EVIDENCE",
            "job.graph_digest must be a 64-hex SHA-256 digest"
        );
    }
    if (!isNonEmptyString(compileGraphDigest) || !SHA256_HEX_REGEX.test(compileGraphDigest)) {
        throw new SceneResultBuilderError(
            "INVALID_COMPILE_METADATA",
            "compile_metadata.graph_digest must be a 64-hex SHA-256 digest"
        );
    }
    if (jobGraphDigest !== compileGraphDigest) {
        throw new SceneResultBuilderError(
            "DIGEST_MISMATCH",
            `Job graph_digest "${jobGraphDigest}" does not match compile_metadata graph_digest "${compileGraphDigest}"`
        );
    }

    const jobPlanDigest = job.page_compile_plan_digest || job.compile_plan_digest;
    const compilePlanDigest = compileMeta.page_compile_plan_digest;
    if (!isNonEmptyString(jobPlanDigest) || !SHA256_HEX_REGEX.test(jobPlanDigest)) {
        throw new SceneResultBuilderError(
            "INVALID_JOB_EVIDENCE",
            "job page_compile_plan_digest must be a 64-hex SHA-256 digest"
        );
    }
    if (!isNonEmptyString(compilePlanDigest) || !SHA256_HEX_REGEX.test(compilePlanDigest)) {
        throw new SceneResultBuilderError(
            "INVALID_COMPILE_METADATA",
            "compile_metadata.page_compile_plan_digest must be a 64-hex SHA-256 digest"
        );
    }
    if (jobPlanDigest !== compilePlanDigest) {
        throw new SceneResultBuilderError(
            "DIGEST_MISMATCH",
            `Job compile plan digest "${jobPlanDigest}" does not match compiler page_compile_plan_digest "${compilePlanDigest}"`
        );
    }

    if (job.scene_id !== undefined && job.scene_id !== sceneId) {
        throw new SceneResultBuilderError(
            "IDENTITY_MISMATCH",
            `Job scene_id "${job.scene_id}" does not match owning scene_id "${sceneId}"`
        );
    }
    if (job.page_id !== undefined && job.page_id !== pageId) {
        throw new SceneResultBuilderError(
            "IDENTITY_MISMATCH",
            `Job page_id "${job.page_id}" does not match owning page_id "${pageId}"`
        );
    }

    // 8. Effective Generation Settings Consistency
    const compileSettings = compileMeta.effective_settings;
    const jobSettings = job.effective_settings;
    if (!isObject(compileSettings)) {
        throw new SceneResultBuilderError(
            "MISSING_SETTINGS",
            "compile_metadata must contain effective_settings"
        );
    }
    if (!isObject(jobSettings)) {
        throw new SceneResultBuilderError(
            "MISSING_SETTINGS",
            "job must contain effective_settings"
        );
    }

    for (const key of ["checkpoint_id", "sampler_id", "scheduler_id"]) {
        if (!isNonEmptyString(compileSettings[key]) || !isNonEmptyString(jobSettings[key])) {
            throw new SceneResultBuilderError(
                "MISSING_SETTINGS",
                `effective_settings.${key} must be a non-empty string in compiler and job`
            );
        }
        if (compileSettings[key] !== jobSettings[key]) {
            throw new SceneResultBuilderError(
                "SETTINGS_MISMATCH",
                `effective_settings.${key} mismatch: compiler has "${compileSettings[key]}", job has "${jobSettings[key]}"`
            );
        }
    }

    for (const key of ["steps", "cfg", "effective_seed"]) {
        if (compileSettings[key] === undefined || jobSettings[key] === undefined) {
            throw new SceneResultBuilderError(
                "MISSING_SETTINGS",
                `effective_settings.${key} must be defined in compiler and job`
            );
        }
        if (compileSettings[key] !== jobSettings[key]) {
            throw new SceneResultBuilderError(
                "SETTINGS_MISMATCH",
                `effective_settings.${key} mismatch: compiler has ${compileSettings[key]}, job has ${jobSettings[key]}`
            );
        }
    }

    const seedRequested = jobSettings.seed_requested !== undefined
        ? jobSettings.seed_requested
        : compileSettings.seed_requested;
    if (typeof seedRequested !== "string" && typeof seedRequested !== "number") {
        throw new SceneResultBuilderError(
            "MISSING_SETTINGS",
            "effective_settings.seed_requested must be an explicit string or number"
        );
    }
    if (jobSettings.seed_requested !== undefined && compileSettings.seed_requested !== undefined) {
        if (jobSettings.seed_requested !== compileSettings.seed_requested) {
            throw new SceneResultBuilderError(
                "SETTINGS_MISMATCH",
                `effective_settings.seed_requested mismatch: compiler has "${compileSettings.seed_requested}", job has "${jobSettings.seed_requested}"`
            );
        }
    }

    // 9. Reference Provenance Consistency
    const refEvidence = isObject(evidence.reference)
        ? evidence.reference
        : (isObject(evidence.reference_evidence)
            ? evidence.reference_evidence
            : (isObject(evidence.reference_analysis) ? evidence.reference_analysis : plan.reference));

    if (!isObject(refEvidence) || typeof refEvidence.enabled !== "boolean") {
        throw new SceneResultBuilderError(
            "MISSING_REFERENCE_PROVENANCE",
            "Evidence must contain explicit reference evidence with boolean enabled property"
        );
    }

    const planRef = plan.reference;
    if (isObject(planRef) && typeof planRef.enabled === "boolean") {
        if (planRef.enabled !== refEvidence.enabled) {
            throw new SceneResultBuilderError(
                "REFERENCE_PROVENANCE_ERROR",
                `Plan reference enabled (${planRef.enabled}) disagrees with reference evidence enabled (${refEvidence.enabled})`
            );
        }
    }

    let activeRefAsset = null;
    let activeRefDigest = null;

    if (refEvidence.enabled) {
        const refAssetId = refEvidence.reference_asset || refEvidence.asset_reference;
        const planAssetId = planRef?.reference_asset;

        if (!isNonEmptyString(refAssetId)) {
            throw new SceneResultBuilderError(
                "REFERENCE_PROVENANCE_ERROR",
                "Active reference evidence must specify a non-empty reference_asset"
            );
        }
        if (isNonEmptyString(planAssetId) && planAssetId !== refAssetId) {
            throw new SceneResultBuilderError(
                "REFERENCE_PROVENANCE_ERROR",
                `Plan reference_asset "${planAssetId}" does not match analyzed reference_asset "${refAssetId}"`
            );
        }

        const digest = refEvidence.content_digest;
        if (!isNonEmptyString(digest) || !SHA256_HEX_REGEX.test(digest)) {
            throw new SceneResultBuilderError(
                "REFERENCE_PROVENANCE_ERROR",
                "Active reference must contain a verified 64-hex SHA-256 content_digest"
            );
        }

        activeRefAsset = refAssetId;
        activeRefDigest = digest;
    } else {
        if (refEvidence.content_digest !== null && refEvidence.content_digest !== undefined) {
            throw new SceneResultBuilderError(
                "REFERENCE_PROVENANCE_ERROR",
                "Disabled reference must have content_digest: null"
            );
        }
    }

    // 10. Artifact Provenance (PNG Analysis & Locator)
    const locator = evidence.locator || evidence.artifact_locator || evidence.artifact?.locator;
    if (!isObject(locator)) {
        throw new SceneResultBuilderError(
            "MISSING_ARTIFACT_PROVENANCE",
            "Evidence must supply verified artifact locator"
        );
    }
    if (!isNonEmptyString(locator.filename) || !locator.filename.endsWith(".png")) {
        throw new SceneResultBuilderError(
            "INVALID_ARTIFACT_LOCATOR",
            `artifact locator.filename must be a non-empty string ending with .png, got "${locator.filename}"`
        );
    }
    if (!isNonEmptyString(locator.subfolder) || !isNonEmptyString(locator.type)) {
        throw new SceneResultBuilderError(
            "INVALID_ARTIFACT_LOCATOR",
            "artifact locator must contain non-empty subfolder and type"
        );
    }

    const pngAnalysis = evidence.png_analysis || evidence.artifact?.png_analysis || evidence.artifact;
    if (!isObject(pngAnalysis)) {
        throw new SceneResultBuilderError(
            "MISSING_ARTIFACT_PROVENANCE",
            "Evidence must contain PNG analysis result"
        );
    }

    const pngDigest = pngAnalysis.content_digest;
    if (!isNonEmptyString(pngDigest) || !SHA256_HEX_REGEX.test(pngDigest)) {
        throw new SceneResultBuilderError(
            "ARTIFACT_PROVENANCE_ERROR",
            "PNG analysis must provide a verified 64-hex SHA-256 content_digest"
        );
    }

    const declaredWidth = pngAnalysis.declared_width !== undefined ? pngAnalysis.declared_width : pngAnalysis.dimensions?.width;
    const declaredHeight = pngAnalysis.declared_height !== undefined ? pngAnalysis.declared_height : pngAnalysis.dimensions?.height;

    if (!isPositiveInteger(declaredWidth) || !isPositiveInteger(declaredHeight)) {
        throw new SceneResultBuilderError(
            "ARTIFACT_PROVENANCE_ERROR",
            "PNG analysis must provide positive integer declared dimensions"
        );
    }

    if (declaredWidth !== compileDims.width || declaredHeight !== compileDims.height) {
        throw new SceneResultBuilderError(
            "ARTIFACT_PROVENANCE_ERROR",
            `PNG declared dimensions [${declaredWidth}x${declaredHeight}] do not match compiler local canvas dimensions [${compileDims.width}x${compileDims.height}]`
        );
    }

    // 11. Compute Effective-Input Digest using the existing function
    const digestEvidence = {
        scene: plan.scene,
        page_context: plan.page_context,
        character_instances: plan.character_instances,
        cast: plan.cast,
        reference: {
            enabled: refEvidence.enabled,
            reference_asset: activeRefAsset,
            content_digest: activeRefDigest,
        },
        effective_settings: {
            checkpoint_id: compileSettings.checkpoint_id,
            sampler_id: compileSettings.sampler_id,
            scheduler_id: compileSettings.scheduler_id,
            steps: compileSettings.steps,
            cfg: compileSettings.cfg,
            effective_seed: compileSettings.effective_seed,
            mask_feather: compileSettings.mask_feather,
            panel_strength: compileSettings.panel_strength,
            reference_weight: compileSettings.reference_weight,
            reference_start: compileSettings.reference_start,
            reference_end: compileSettings.reference_end,
        },
        local_dimensions: compileDims,
        placement: {
            page_dimensions: targetPageDims,
            page_target_rect: pageTargetRect,
            local_source_rect: localSourceRect,
            transform: transform,
        },
        guide_state: plan.guide_state,
    };

    const digestFn = (options && typeof options._computeDigest === "function")
        ? options._computeDigest
        : computeSceneEffectiveInputDigest;

    let effectiveInputDigest;
    let digestContractVersion;
    try {
        const digestResult = digestFn(digestEvidence);
        if (!isObject(digestResult)) {
            throw new SceneResultBuilderError(
                "EFFECTIVE_INPUT_DIGEST_FAILED",
                "computeSceneEffectiveInputDigest did not return a valid result object"
            );
        }
        effectiveInputDigest = digestResult.effective_input_digest;
        digestContractVersion = digestResult.contract_version;
    } catch (digestError) {
        if (digestError instanceof SceneResultBuilderError) {
            throw digestError;
        }
        throw new SceneResultBuilderError(
            "EFFECTIVE_INPUT_DIGEST_FAILED",
            `Failed to compute effective-input digest: ${digestError.message}`,
            { cause: digestError }
        );
    }

    if (!isNonEmptyString(digestContractVersion)) {
        throw new SceneResultBuilderError(
            "MISSING_DIGEST_VERSION",
            `computeSceneEffectiveInputDigest returned missing or empty contract_version: "${digestContractVersion}"`
        );
    }

    if (digestContractVersion !== REQUIRED_DIGEST_CONTRACT_VERSION_V1_1) {
        throw new SceneResultBuilderError(
            "UNSUPPORTED_DIGEST_CONTRACT_VERSION",
            `computeSceneEffectiveInputDigest returned unsupported contract_version: expected "${REQUIRED_DIGEST_CONTRACT_VERSION_V1_1}", got "${digestContractVersion}"`
        );
    }

    // Fail closed if caller provided an inconsistent digest contract version
    const callerProv = isObject(evidence.input_provenance) ? evidence.input_provenance : evidence;
    const callerDigestVersion = callerProv.effective_input_contract_version || evidence.effective_input_contract_version;
    if (callerDigestVersion !== undefined && callerDigestVersion !== digestContractVersion) {
        throw new SceneResultBuilderError(
            "INCONSISTENT_DIGEST_VERSION",
            `Caller-provided effective_input_contract_version "${callerDigestVersion}" does not match computed digest contract_version "${digestContractVersion}"`
        );
    }

    // 12. Assemble Candidate Finalized Manifest
    const candidate = {
        schema_id: SCHEMA_ID,
        schema_version: SCHEMA_VERSION,
        manifest_id: manifestId,
        owner: {
            document_id: documentId,
            page_id: pageId,
            scene_id: sceneId,
        },
        input_provenance: {
            authoring_snapshot_ref: snapshotRef,
            authoring_snapshot_digest: snapshotDigest,
            effective_input_digest: effectiveInputDigest,
            effective_input_contract_version: digestContractVersion,
            reference_content_digest: activeRefDigest,
        },
        execution: {
            job_id: job.job_id,
            prompt_id: job.prompt_id,
            state: "SUCCEEDED",
            graph_digest: compileGraphDigest,
            page_compile_plan_digest: compilePlanDigest,
            effective_settings: {
                checkpoint_id: compileSettings.checkpoint_id,
                sampler_id: compileSettings.sampler_id,
                scheduler_id: compileSettings.scheduler_id,
                steps: compileSettings.steps,
                cfg: compileSettings.cfg,
                seed_requested: seedRequested,
                effective_seed: compileSettings.effective_seed,
            },
        },
        artifact: {
            locator: {
                filename: locator.filename,
                subfolder: locator.subfolder,
                type: locator.type,
            },
            dimensions: {
                width: declaredWidth,
                height: declaredHeight,
            },
            content_digest: pngDigest,
        },
        placement: {
            page_target_rect: {
                x: Number(pageTargetRect.x),
                y: Number(pageTargetRect.y),
                w: Number(pageTargetRect.w),
                h: Number(pageTargetRect.h),
            },
            local_source_rect: {
                x: Number(localSourceRect.x),
                y: Number(localSourceRect.y),
                w: Number(localSourceRect.w),
                h: Number(localSourceRect.h),
            },
            transform: {
                scale_x: Number(transform.scale_x),
                scale_y: Number(transform.scale_y),
                offset_x: Number(transform.offset_x),
                offset_y: Number(transform.offset_y),
            },
            target_page_dimensions: {
                width: Number(targetPageDims.width),
                height: Number(targetPageDims.height),
            },
        },
        created_at: createdAt,
    };

    // 13. Validate using the existing validateSceneResultManifest contract
    // This validates schema conformity, UUID variants, placement bounds, epsilon consistency, and deep-clones.
    return validateSceneResultManifest(candidate);
}
