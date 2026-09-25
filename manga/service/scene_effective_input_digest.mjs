/**
 * scene_effective_input_digest.mjs — Deterministic Scene-specific effective-input digest.
 *
 * Implements pure SHA-256 digest calculation over canonicalized effective inputs
 * for a single selected isolated-Scene. Covers Scene prompts and local geometry, Page style,
 * placed character instances, referenced CAST definitions, reference image content digest,
 * generation settings, local canvas dimensions, Page placement, and guide state.
 */

import { createHash } from "node:crypto";

export const CONTRACT_VERSION = "2.0.0";
const SHA256_HEX_REGEX = /^[0-9a-f]{64}$/i;

export class SceneEffectiveInputDigestError extends Error {
    constructor(code, message, options = {}) {
        super(message, options);
        this.name = "SceneEffectiveInputDigestError";
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

function isFiniteNumber(val) {
    return typeof val === "number" && Number.isFinite(val);
}

/**
 * Deterministically serializes an arbitrary JavaScript object with recursively sorted keys.
 *
 * @param {unknown} value
 * @returns {string}
 */
export function canonicalStringify(value) {
    if (Array.isArray(value)) {
        return `[${value.map(canonicalStringify).join(",")}]`;
    }
    if (value !== null && typeof value === "object") {
        const sortedKeys = Object.keys(value).sort();
        return `{${sortedKeys.map(k => `${JSON.stringify(k)}:${canonicalStringify(value[k])}`).join(",")}}`;
    }
    return JSON.stringify(value);
}

/**
 * Validates and normalizes effective input evidence for a single selected Scene,
 * then computes its deterministic SHA-256 digest.
 *
 * @param {object} evidence - Structured input evidence.
 * @returns {{ contract_version: string, effective_input_digest: string }}
 * @throws {SceneEffectiveInputDigestError} On missing, incomplete, or invalid evidence.
 */
export function computeSceneEffectiveInputDigest(evidence) {
    if (!isObject(evidence)) {
        throw new SceneEffectiveInputDigestError(
            "INVALID_EVIDENCE",
            "Effective input evidence must be a non-null object"
        );
    }

    // 1. Resolve extracted evidence sections (support either raw plan/metadata containers or direct fields)
    const plan = isObject(evidence.plan) ? evidence.plan : null;
    const compileMeta = isObject(evidence.compile_metadata) ? evidence.compile_metadata : null;

    const scene = evidence.scene || plan?.scene;
    const pageContext = evidence.page_context || plan?.page_context || compileMeta?.page_context;
    const instances = evidence.character_instances || plan?.character_instances;
    const cast = evidence.cast || plan?.cast;
    const reference = evidence.reference || evidence.reference_evidence || plan?.reference;
    const settings = evidence.effective_settings || compileMeta?.effective_settings;
    const localDims = evidence.local_dimensions || evidence.local_canvas || plan?.local_canvas || compileMeta?.local_dimensions;
    const placement = evidence.placement || evidence.placement_mapping || plan?.placement_mapping || compileMeta?.placement_mapping;
    const guideState = evidence.guide_state !== undefined ? evidence.guide_state : (plan?.guide_state !== undefined ? plan.guide_state : evidence.guides);

    // 2. Validate Selected Scene
    if (!isObject(scene) || !isNonEmptyString(scene.scene_id)) {
        throw new SceneEffectiveInputDigestError(
            "MISSING_SCENE_EVIDENCE",
            "evidence must contain a valid scene object with scene_id"
        );
    }
    const sceneLocalArea = scene.local_area || scene.area;
    if (!isObject(sceneLocalArea)) {
        throw new SceneEffectiveInputDigestError(
            "MISSING_SCENE_EVIDENCE",
            "scene must contain a valid local_area rectangle"
        );
    }
    for (const k of ["x", "y", "w", "h"]) {
        if (!isFiniteNumber(sceneLocalArea[k])) {
            throw new SceneEffectiveInputDigestError(
                "INVALID_SCENE_GEOMETRY",
                `scene.local_area.${k} must be a finite number`
            );
        }
    }

    // 3. Validate Page Style
    if (!isObject(pageContext)) {
        throw new SceneEffectiveInputDigestError(
            "MISSING_PAGE_CONTEXT",
            "evidence must contain a valid page_context object"
        );
    }

    // 4. Validate Character Instances (only placed instances in this scene)
    if (!Array.isArray(instances)) {
        throw new SceneEffectiveInputDigestError(
            "MISSING_INSTANCE_EVIDENCE",
            "evidence must contain a character_instances array"
        );
    }
    const normalizedInstances = [];
    for (const inst of instances) {
        if (!isObject(inst) || !isNonEmptyString(inst.instance_id) || !isNonEmptyString(inst.cast_id)) {
            throw new SceneEffectiveInputDigestError(
                "INVALID_INSTANCE_EVIDENCE",
                "character instance must contain instance_id and cast_id"
            );
        }
        const instArea = inst.area;
        if (!isObject(instArea)) {
            throw new SceneEffectiveInputDigestError(
                "INVALID_INSTANCE_EVIDENCE",
                `character instance ${inst.instance_id} must contain area`
            );
        }
        for (const k of ["x", "y", "w", "h"]) {
            if (!isFiniteNumber(instArea[k])) {
                throw new SceneEffectiveInputDigestError(
                    "INVALID_INSTANCE_GEOMETRY",
                    `character instance ${inst.instance_id} area.${k} must be a finite number`
                );
            }
        }
        normalizedInstances.push({
            instance_id: inst.instance_id,
            cast_id: inst.cast_id,
            acting_prompt: typeof inst.acting_prompt === "string" ? inst.acting_prompt : "",
            negative_prompt_override: typeof inst.negative_prompt_override === "string" ? inst.negative_prompt_override : null,
            order: Number.isInteger(inst.order) ? inst.order : 0,
            area: {
                x: Number(instArea.x),
                y: Number(instArea.y),
                w: Number(instArea.w),
                h: Number(instArea.h),
            },
        });
    }
    // Sort deterministically by instance_id
    normalizedInstances.sort((a, b) => a.instance_id.localeCompare(b.instance_id));

    // 5. Validate CAST definitions
    if (!Array.isArray(cast)) {
        throw new SceneEffectiveInputDigestError(
            "MISSING_CAST_EVIDENCE",
            "evidence must contain a cast array"
        );
    }
    const normalizedCast = [];
    for (const c of cast) {
        if (!isObject(c) || !isNonEmptyString(c.cast_id)) {
            throw new SceneEffectiveInputDigestError(
                "INVALID_CAST_EVIDENCE",
                "cast entry must contain cast_id"
            );
        }
        normalizedCast.push({
            cast_id: c.cast_id,
            identity_prompt: typeof c.identity_prompt === "string" ? c.identity_prompt : "",
            negative_prompt: typeof c.negative_prompt === "string" ? c.negative_prompt : "",
            reference_asset: typeof c.reference_asset === "string" && c.reference_asset.trim() ? c.reference_asset.trim() : null,
        });
    }
    // Sort deterministically by cast_id
    normalizedCast.sort((a, b) => a.cast_id.localeCompare(b.cast_id));

    // 6. Validate Reference Evidence
    if (!isObject(reference) || typeof reference.enabled !== "boolean") {
        throw new SceneEffectiveInputDigestError(
            "MISSING_REFERENCE_EVIDENCE",
            "evidence must contain reference object with boolean enabled property"
        );
    }
    if (reference.enabled) {
        if (!isNonEmptyString(reference.reference_asset)) {
            throw new SceneEffectiveInputDigestError(
                "MISSING_REFERENCE_ASSET",
                "Active reference must specify a non-empty reference_asset"
            );
        }
        if (!isNonEmptyString(reference.content_digest) || !SHA256_HEX_REGEX.test(reference.content_digest)) {
            throw new SceneEffectiveInputDigestError(
                "MISSING_REFERENCE_DIGEST",
                "Active reference must supply a verified 64-hex content_digest"
            );
        }
    } else {
        if (reference.content_digest !== null && reference.content_digest !== undefined) {
            throw new SceneEffectiveInputDigestError(
                "INVALID_REFERENCE_EVIDENCE",
                "Disabled reference must have content_digest: null"
            );
        }
    }

    // 7. Validate Generation Settings
    if (!isObject(settings)) {
        throw new SceneEffectiveInputDigestError(
            "MISSING_SETTINGS_EVIDENCE",
            "evidence must contain effective_settings object"
        );
    }
    for (const field of ["checkpoint_id", "sampler_id", "scheduler_id"]) {
        if (!isNonEmptyString(settings[field])) {
            throw new SceneEffectiveInputDigestError(
                "MISSING_SETTINGS_EVIDENCE",
                `effective_settings.${field} must be a non-empty string`
            );
        }
    }
    if (!isPositiveInteger(settings.steps)) {
        throw new SceneEffectiveInputDigestError(
            "INVALID_SETTINGS_EVIDENCE",
            "effective_settings.steps must be a positive integer"
        );
    }
    if (!isFiniteNumber(settings.cfg) || settings.cfg <= 0) {
        throw new SceneEffectiveInputDigestError(
            "INVALID_SETTINGS_EVIDENCE",
            "effective_settings.cfg must be a positive number"
        );
    }
    if (typeof settings.effective_seed !== "number" || !Number.isInteger(settings.effective_seed)) {
        throw new SceneEffectiveInputDigestError(
            "INVALID_SETTINGS_EVIDENCE",
            "effective_settings.effective_seed must be an integer"
        );
    }

    // Semantic vs execution-instance split (MANGA-ISOLATED-BASELINE-CORRECTION1 / B5):
    // CURRENT means "this result still corresponds to the current editable
    // Authoring/generation contract".  checkpoint, sampler, scheduler, steps, cfg,
    // mask_feather, panel_strength (and prompts/LoRA tags via the Scene/Page/CAST
    // sections) are deterministic user-chosen inputs and stay in the digest.
    // The seed (seed_requested / effective_seed) only identifies one execution
    // instance: with seed "-1" every fresh compile draws a new random seed, which
    // made every stored result STALE.  It is validated above and remains recorded
    // in the SceneResult manifest's execution.effective_settings, but it does not
    // participate in semantic freshness.
    const normalizedSettings = {
        checkpoint_id: settings.checkpoint_id,
        sampler_id: settings.sampler_id,
        scheduler_id: settings.scheduler_id,
        steps: settings.steps,
        cfg: settings.cfg,
        mask_feather: Number.isInteger(settings.mask_feather) ? settings.mask_feather : 16,
        panel_strength: isFiniteNumber(settings.panel_strength) ? settings.panel_strength : 1.0,
    };
    if (isFiniteNumber(settings.reference_weight)) normalizedSettings.reference_weight = settings.reference_weight;
    if (isFiniteNumber(settings.reference_start)) normalizedSettings.reference_start = settings.reference_start;
    if (isFiniteNumber(settings.reference_end)) normalizedSettings.reference_end = settings.reference_end;

    // 8. Validate Local Canvas Dimensions
    if (!isObject(localDims) || !isPositiveInteger(localDims.width) || !isPositiveInteger(localDims.height)) {
        throw new SceneEffectiveInputDigestError(
            "MISSING_DIMENSION_EVIDENCE",
            "evidence must contain positive integer local_dimensions width and height"
        );
    }

    // 9. Validate Placement Mapping & Original Page Geometry
    if (!isObject(placement)) {
        throw new SceneEffectiveInputDigestError(
            "MISSING_PLACEMENT_EVIDENCE",
            "evidence must contain placement mapping object"
        );
    }
    const pageTargetRect = placement.page_target_rect || placement.target_rect;
    const localSourceRect = placement.local_source_rect || placement.source_rect;
    const transform = placement.transform;

    if (!isObject(pageTargetRect) || !isObject(localSourceRect) || !isObject(transform)) {
        throw new SceneEffectiveInputDigestError(
            "MISSING_PLACEMENT_EVIDENCE",
            "placement must contain page_target_rect, local_source_rect, and transform"
        );
    }
    for (const k of ["x", "y", "w", "h"]) {
        if (!isFiniteNumber(pageTargetRect[k]) || !isFiniteNumber(localSourceRect[k])) {
            throw new SceneEffectiveInputDigestError(
                "INVALID_PLACEMENT_GEOMETRY",
                `placement rectangles must contain finite numeric ${k}`
            );
        }
    }
    for (const k of ["scale_x", "scale_y", "offset_x", "offset_y"]) {
        if (!isFiniteNumber(transform[k])) {
            throw new SceneEffectiveInputDigestError(
                "INVALID_PLACEMENT_GEOMETRY",
                `placement transform must contain finite numeric ${k}`
            );
        }
    }
    const pageW = pageContext.width_px || placement.target_page_dimensions?.width || placement.page_dimensions?.width;
    const pageH = pageContext.height_px || placement.target_page_dimensions?.height || placement.page_dimensions?.height;
    if (!isPositiveInteger(pageW) || !isPositiveInteger(pageH)) {
        throw new SceneEffectiveInputDigestError(
            "MISSING_DIMENSION_EVIDENCE",
            "Original Page dimensions width_px and height_px must be positive integers"
        );
    }

    // 10. Fail-closed Guide State Validation
    if (guideState === undefined || guideState === null) {
        throw new SceneEffectiveInputDigestError(
            "MISSING_GUIDE_EVIDENCE",
            "evidence must explicitly declare guide_state (missing guide evidence is rejected)"
        );
    }
    let guideActive = false;
    if (Array.isArray(guideState)) {
        guideActive = guideState.some(g => isObject(g) && g.enabled !== false && g.asset_reference);
    } else if (isObject(guideState)) {
        guideActive = guideState.active === true || guideState.enabled === true;
    } else {
        throw new SceneEffectiveInputDigestError(
            "INVALID_GUIDE_EVIDENCE",
            "guide_state must be an object or array"
        );
    }
    if (guideActive) {
        throw new SceneEffectiveInputDigestError(
            "UNSUPPORTED_ACTIVE_GUIDE",
            "Active structural guides are unsupported in isolated-Scene execution path"
        );
    }

    // 11. Assemble Canonical Digest Payload
    const canonicalPayload = {
        contract_version: CONTRACT_VERSION,
        scene: {
            scene_id: scene.scene_id,
            prompt: typeof scene.prompt === "string" ? scene.prompt : "",
            negative_prompt: typeof scene.negative_prompt === "string" ? scene.negative_prompt : "",
            input_mode: scene.input_mode || "simple",
            order: Number.isInteger(scene.order) ? scene.order : 0,
            local_area: {
                x: Number(sceneLocalArea.x),
                y: Number(sceneLocalArea.y),
                w: Number(sceneLocalArea.w),
                h: Number(sceneLocalArea.h),
            },
        },
        page_style: {
            style_prompt: typeof pageContext.style_prompt === "string" ? pageContext.style_prompt : "",
            style_negative_prompt: typeof pageContext.style_negative_prompt === "string" ? pageContext.style_negative_prompt : "",
        },
        character_instances: normalizedInstances,
        cast: normalizedCast,
        reference: {
            enabled: Boolean(reference.enabled),
            reference_asset: reference.enabled ? reference.reference_asset : null,
            content_digest: reference.enabled ? reference.content_digest : null,
        },
        effective_settings: normalizedSettings,
        local_dimensions: {
            width: Number(localDims.width),
            height: Number(localDims.height),
        },
        placement: {
            page_dimensions: {
                width: Number(pageW),
                height: Number(pageH),
            },
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
        },
        guide_state: {
            enabled: false,
            active: false,
        },
    };

    // 12. Deterministic Serialization & SHA-256 Digest
    const serialized = canonicalStringify(canonicalPayload);
    const effective_input_digest = createHash("sha256").update(serialized, "utf8").digest("hex");

    return {
        contract_version: CONTRACT_VERSION,
        effective_input_digest,
    };
}
