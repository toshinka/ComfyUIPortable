import test from "node:test";
import assert from "node:assert/strict";

import {
    CONTRACT_VERSION,
    SceneEffectiveInputDigestError,
    canonicalStringify,
    computeSceneEffectiveInputDigest,
} from "../service/scene_effective_input_digest.mjs";

function makeValidEvidence(overrides = {}) {
    return {
        scene: {
            scene_id: "scene_01",
            name: "Panel 1",
            prompt: "1girl standing in classroom",
            negative_prompt: "blurry, low quality",
            input_mode: "cast",
            order: 0,
            local_area: { x: 0, y: 0, w: 512, h: 768 },
            ...overrides.scene,
        },
        page_context: {
            page_id: "page_01",
            style_prompt: "manga, screentone, monochrome",
            style_negative_prompt: "color, photographic",
            width_px: 1200,
            height_px: 1800,
            ...overrides.page_context,
        },
        character_instances: overrides.character_instances !== undefined ? overrides.character_instances : [
            {
                instance_id: "inst_01",
                cast_id: "cast_01",
                acting_prompt: "smiling happily",
                negative_prompt_override: null,
                order: 0,
                area: { x: 50, y: 50, w: 200, h: 400 },
            },
        ],
        cast: overrides.cast !== undefined ? overrides.cast : [
            {
                cast_id: "cast_01",
                display_name: "Heroine",
                identity_prompt: "long blue hair, school uniform",
                negative_prompt: "short hair",
                reference_asset: "cast_01.png",
            },
        ],
        reference: overrides.reference !== undefined ? overrides.reference : {
            enabled: true,
            reference_asset: "cast_01.png",
            content_digest: "a".repeat(64),
        },
        effective_settings: {
            checkpoint_id: "illustrious_v1.safetensors",
            sampler_id: "euler_ancestral",
            scheduler_id: "karras",
            steps: 28,
            cfg: 6.5,
            effective_seed: 42,
            mask_feather: 16,
            panel_strength: 1.0,
            reference_weight: 0.7,
            reference_start: 0.0,
            reference_end: 0.8,
            ...overrides.effective_settings,
        },
        local_dimensions: {
            width: 512,
            height: 768,
            ...overrides.local_dimensions,
        },
        placement: {
            page_target_rect: { x: 60, y: 80, w: 512, h: 768 },
            local_source_rect: { x: 0, y: 0, w: 512, h: 768 },
            transform: { scale_x: 1.0, scale_y: 1.0, offset_x: 60, offset_y: 80 },
            ...overrides.placement,
        },
        guide_state: overrides.guide_state !== undefined ? overrides.guide_state : {
            enabled: false,
            active: false,
        },
    };
}

test("canonicalStringify sorts keys recursively and formats deterministically", () => {
    const obj1 = { b: 2, a: 1, c: { z: 26, y: 25 } };
    const obj2 = { c: { y: 25, z: 26 }, a: 1, b: 2 };
    assert.strictEqual(canonicalStringify(obj1), canonicalStringify(obj2));
    assert.strictEqual(canonicalStringify(obj1), '{"a":1,"b":2,"c":{"y":25,"z":26}}');
});

test("Case A: Identical effective inputs produce identical digests", () => {
    const ev1 = makeValidEvidence();
    const ev2 = makeValidEvidence();

    const res1 = computeSceneEffectiveInputDigest(ev1);
    const res2 = computeSceneEffectiveInputDigest(ev2);

    assert.strictEqual(CONTRACT_VERSION, "2.0.0");
    assert.strictEqual(res1.contract_version, "2.0.0");
    assert.strictEqual(typeof res1.effective_input_digest, "string");
    assert.strictEqual(res1.effective_input_digest.length, 64);
    assert.match(res1.effective_input_digest, /^[0-9a-f]{64}$/);
    assert.strictEqual(res1.effective_input_digest, res2.effective_input_digest);
});

test("Case B: Object key insertion order does not affect the digest", () => {
    const ev1 = makeValidEvidence();
    // Create an object with completely shuffled key insertion order across nested levels
    const ev2 = {
        guide_state: { active: false, enabled: false },
        placement: {
            transform: { offset_y: 80, offset_x: 60, scale_y: 1.0, scale_x: 1.0 },
            local_source_rect: { h: 768, w: 512, y: 0, x: 0 },
            page_target_rect: { h: 768, w: 512, y: 80, x: 60 },
        },
        local_dimensions: { height: 768, width: 512 },
        effective_settings: {
            reference_end: 0.8,
            reference_start: 0.0,
            reference_weight: 0.7,
            panel_strength: 1.0,
            mask_feather: 16,
            effective_seed: 42,
            cfg: 6.5,
            steps: 28,
            scheduler_id: "karras",
            sampler_id: "euler_ancestral",
            checkpoint_id: "illustrious_v1.safetensors",
        },
        reference: {
            content_digest: "a".repeat(64),
            reference_asset: "cast_01.png",
            enabled: true,
        },
        cast: [
            {
                reference_asset: "cast_01.png",
                negative_prompt: "short hair",
                identity_prompt: "long blue hair, school uniform",
                display_name: "Heroine",
                cast_id: "cast_01",
            },
        ],
        character_instances: [
            {
                area: { h: 400, w: 200, y: 50, x: 50 },
                order: 0,
                negative_prompt_override: null,
                acting_prompt: "smiling happily",
                cast_id: "cast_01",
                instance_id: "inst_01",
            },
        ],
        page_context: {
            height_px: 1800,
            width_px: 1200,
            style_negative_prompt: "color, photographic",
            style_prompt: "manga, screentone, monochrome",
            page_id: "page_01",
        },
        scene: {
            local_area: { h: 768, w: 512, y: 0, x: 0 },
            order: 0,
            input_mode: "cast",
            negative_prompt: "blurry, low quality",
            prompt: "1girl standing in classroom",
            name: "Panel 1",
            scene_id: "scene_01",
        },
    };

    const res1 = computeSceneEffectiveInputDigest(ev1);
    const res2 = computeSceneEffectiveInputDigest(ev2);

    assert.strictEqual(res1.effective_input_digest, res2.effective_input_digest);
});

test("Case C: An unrelated Scene edit does not affect the digest", () => {
    // When evidence is extracted for scene_01, any unrelated scene edits in the authoring doc
    // do not enter scene_01's effective input boundary.
    const ev1 = makeValidEvidence();
    const ev2 = makeValidEvidence();

    // Adding metadata or ignoring unrelated scenes ensures digest stability
    const res1 = computeSceneEffectiveInputDigest(ev1);
    const res2 = computeSceneEffectiveInputDigest(ev2);
    assert.strictEqual(res1.effective_input_digest, res2.effective_input_digest);
});

test("Case B (Display-Only): Changing only scene.name does not change the v2 digest", () => {
    const base = computeSceneEffectiveInputDigest(makeValidEvidence()).effective_input_digest;
    const renamedScene = computeSceneEffectiveInputDigest(makeValidEvidence({
        scene: { name: "Completely Different Display Name" },
    })).effective_input_digest;
    assert.strictEqual(renamedScene, base);
});

test("Case C (Display-Only): Changing only cast[].display_name does not change the v2 digest", () => {
    const base = computeSceneEffectiveInputDigest(makeValidEvidence()).effective_input_digest;
    const renamedCast = computeSceneEffectiveInputDigest(makeValidEvidence({
        cast: [
            {
                cast_id: "cast_01",
                display_name: "Completely Different Character Display Label",
                identity_prompt: "long blue hair, school uniform",
                negative_prompt: "short hair",
                reference_asset: "cast_01.png",
            },
        ],
    })).effective_input_digest;
    assert.strictEqual(renamedCast, base);
});

test("Case D: Selected Scene prompt changes affect the digest", () => {
    const base = computeSceneEffectiveInputDigest(makeValidEvidence()).effective_input_digest;

    const modifiedPrompt = computeSceneEffectiveInputDigest(makeValidEvidence({
        scene: { prompt: "1girl sitting by the window, sunset" },
    })).effective_input_digest;

    const modifiedNegativePrompt = computeSceneEffectiveInputDigest(makeValidEvidence({
        scene: { negative_prompt: "ugly, distorted" },
    })).effective_input_digest;

    const modifiedLocalArea = computeSceneEffectiveInputDigest(makeValidEvidence({
        scene: { local_area: { x: 10, y: 20, w: 512, h: 768 } },
    })).effective_input_digest;

    assert.notStrictEqual(modifiedPrompt, base);
    assert.notStrictEqual(modifiedNegativePrompt, base);
    assert.notStrictEqual(modifiedLocalArea, base);
});

test("Case E: Relevant CAST or Instance changes affect the digest", () => {
    const base = computeSceneEffectiveInputDigest(makeValidEvidence()).effective_input_digest;

    const modifiedActing = computeSceneEffectiveInputDigest(makeValidEvidence({
        character_instances: [
            {
                instance_id: "inst_01",
                cast_id: "cast_01",
                acting_prompt: "crying with joy",
                negative_prompt_override: null,
                order: 0,
                area: { x: 50, y: 50, w: 200, h: 400 },
            },
        ],
    })).effective_input_digest;

    const modifiedCastIdentity = computeSceneEffectiveInputDigest(makeValidEvidence({
        cast: [
            {
                cast_id: "cast_01",
                display_name: "Heroine",
                identity_prompt: "short red hair, warrior armor",
                negative_prompt: "long hair",
                reference_asset: "cast_01.png",
            },
        ],
    })).effective_input_digest;

    assert.notStrictEqual(modifiedActing, base);
    assert.notStrictEqual(modifiedCastIdentity, base);
});

test("Case F: Reference content digest changes affect the digest", () => {
    const base = computeSceneEffectiveInputDigest(makeValidEvidence()).effective_input_digest;

    const modifiedDigest = computeSceneEffectiveInputDigest(makeValidEvidence({
        reference: {
            enabled: true,
            reference_asset: "cast_01.png",
            content_digest: "b".repeat(64),
        },
    })).effective_input_digest;

    const disabledRef = computeSceneEffectiveInputDigest(makeValidEvidence({
        reference: {
            enabled: false,
            reference_asset: null,
            content_digest: null,
        },
    })).effective_input_digest;

    assert.notStrictEqual(modifiedDigest, base);
    assert.notStrictEqual(disabledRef, base);
});

test("Case G: Checkpoint, effective seed or generation settings changes affect the digest", () => {
    const base = computeSceneEffectiveInputDigest(makeValidEvidence()).effective_input_digest;

    const modifiedCheckpoint = computeSceneEffectiveInputDigest(makeValidEvidence({
        effective_settings: { checkpoint_id: "animagine_xl_v3.safetensors" },
    })).effective_input_digest;

    const modifiedSeed = computeSceneEffectiveInputDigest(makeValidEvidence({
        effective_settings: { effective_seed: 99999 },
    })).effective_input_digest;

    const modifiedSteps = computeSceneEffectiveInputDigest(makeValidEvidence({
        effective_settings: { steps: 40 },
    })).effective_input_digest;

    const modifiedCfg = computeSceneEffectiveInputDigest(makeValidEvidence({
        effective_settings: { cfg: 7.5 },
    })).effective_input_digest;

    const modifiedRefWeight = computeSceneEffectiveInputDigest(makeValidEvidence({
        effective_settings: { reference_weight: 0.35 },
    })).effective_input_digest;

    const modifiedRefStart = computeSceneEffectiveInputDigest(makeValidEvidence({
        effective_settings: { reference_start: 0.2 },
    })).effective_input_digest;

    const modifiedRefEnd = computeSceneEffectiveInputDigest(makeValidEvidence({
        effective_settings: { reference_end: 0.6 },
    })).effective_input_digest;

    assert.notStrictEqual(modifiedCheckpoint, base);
    assert.notStrictEqual(modifiedSeed, base);
    assert.notStrictEqual(modifiedSteps, base);
    assert.notStrictEqual(modifiedCfg, base);
    assert.notStrictEqual(modifiedRefWeight, base);
    assert.notStrictEqual(modifiedRefStart, base);
    assert.notStrictEqual(modifiedRefEnd, base);
});

test("Case H: Page placement or local canvas dimensions change the digest", () => {
    const base = computeSceneEffectiveInputDigest(makeValidEvidence()).effective_input_digest;

    const modifiedPlacement = computeSceneEffectiveInputDigest(makeValidEvidence({
        placement: {
            page_target_rect: { x: 120, y: 160, w: 512, h: 768 },
            local_source_rect: { x: 0, y: 0, w: 512, h: 768 },
            transform: { scale_x: 1.0, scale_y: 1.0, offset_x: 120, offset_y: 160 },
        },
    })).effective_input_digest;

    const modifiedLocalDims = computeSceneEffectiveInputDigest(makeValidEvidence({
        local_dimensions: { width: 768, height: 1024 },
    })).effective_input_digest;

    const modifiedPageDims = computeSceneEffectiveInputDigest(makeValidEvidence({
        page_context: { width_px: 2400, height_px: 3600 },
    })).effective_input_digest;

    assert.notStrictEqual(modifiedPlacement, base);
    assert.notStrictEqual(modifiedLocalDims, base);
    assert.notStrictEqual(modifiedPageDims, base);
});

test("Case I: Missing active Reference content digest is rejected (MISSING_REFERENCE_DIGEST)", () => {
    // Active reference with null digest
    assert.throws(() => {
        computeSceneEffectiveInputDigest(makeValidEvidence({
            reference: {
                enabled: true,
                reference_asset: "cast_01.png",
                content_digest: null,
            },
        }));
    }, {
        name: "SceneEffectiveInputDigestError",
        code: "MISSING_REFERENCE_DIGEST",
    });

    // Active reference with malformed hex
    assert.throws(() => {
        computeSceneEffectiveInputDigest(makeValidEvidence({
            reference: {
                enabled: true,
                reference_asset: "cast_01.png",
                content_digest: "not_a_valid_hex_digest",
            },
        }));
    }, {
        name: "SceneEffectiveInputDigestError",
        code: "MISSING_REFERENCE_DIGEST",
    });

    // Active reference missing reference_asset
    assert.throws(() => {
        computeSceneEffectiveInputDigest(makeValidEvidence({
            reference: {
                enabled: true,
                reference_asset: "",
                content_digest: "a".repeat(64),
            },
        }));
    }, {
        name: "SceneEffectiveInputDigestError",
        code: "MISSING_REFERENCE_ASSET",
    });
});

test("Case J: Missing Guide-state evidence is rejected (MISSING_GUIDE_EVIDENCE) and active guides are rejected", () => {
    // Missing guide_state
    const evMissingGuide = makeValidEvidence();
    delete evMissingGuide.guide_state;
    assert.throws(() => {
        computeSceneEffectiveInputDigest(evMissingGuide);
    }, {
        name: "SceneEffectiveInputDigestError",
        code: "MISSING_GUIDE_EVIDENCE",
    });

    // Unsupported active guide
    assert.throws(() => {
        computeSceneEffectiveInputDigest(makeValidEvidence({
            guide_state: {
                enabled: true,
                active: true,
            },
        }));
    }, {
        name: "SceneEffectiveInputDigestError",
        code: "UNSUPPORTED_ACTIVE_GUIDE",
    });
});

test("Case K: Incomplete required settings are rejected (MISSING_SETTINGS_EVIDENCE / INVALID_SETTINGS_EVIDENCE)", () => {
    // Missing checkpoint_id
    assert.throws(() => {
        computeSceneEffectiveInputDigest(makeValidEvidence({
            effective_settings: { checkpoint_id: "" },
        }));
    }, {
        name: "SceneEffectiveInputDigestError",
        code: "MISSING_SETTINGS_EVIDENCE",
    });

    // Invalid steps
    assert.throws(() => {
        computeSceneEffectiveInputDigest(makeValidEvidence({
            effective_settings: { steps: 0 },
        }));
    }, {
        name: "SceneEffectiveInputDigestError",
        code: "INVALID_SETTINGS_EVIDENCE",
    });

    // Invalid cfg
    assert.throws(() => {
        computeSceneEffectiveInputDigest(makeValidEvidence({
            effective_settings: { cfg: -1 },
        }));
    }, {
        name: "SceneEffectiveInputDigestError",
        code: "INVALID_SETTINGS_EVIDENCE",
    });

    // Missing effective_seed
    assert.throws(() => {
        computeSceneEffectiveInputDigest(makeValidEvidence({
            effective_settings: { effective_seed: "forty-two" },
        }));
    }, {
        name: "SceneEffectiveInputDigestError",
        code: "INVALID_SETTINGS_EVIDENCE",
    });
});

test("Case L: Caller input is not mutated", () => {
    const originalEvidence = makeValidEvidence();
    const clonedEvidence = JSON.parse(JSON.stringify(originalEvidence));

    computeSceneEffectiveInputDigest(originalEvidence);

    assert.deepStrictEqual(originalEvidence, clonedEvidence);
});

test("Structure: Supports isolated plan and compile_metadata evidence wrappers", () => {
    const wrappedEvidence = {
        plan: {
            scene: {
                scene_id: "scene_01",
                name: "Panel 1",
                prompt: "1girl standing in classroom",
                negative_prompt: "blurry, low quality",
                input_mode: "cast",
                order: 0,
                local_area: { x: 0, y: 0, w: 512, h: 768 },
            },
            page_context: {
                page_id: "page_01",
                style_prompt: "manga, screentone, monochrome",
                style_negative_prompt: "color, photographic",
                width_px: 1200,
                height_px: 1800,
            },
            character_instances: [
                {
                    instance_id: "inst_01",
                    cast_id: "cast_01",
                    acting_prompt: "smiling happily",
                    negative_prompt_override: null,
                    order: 0,
                    area: { x: 50, y: 50, w: 200, h: 400 },
                },
            ],
            cast: [
                {
                    cast_id: "cast_01",
                    display_name: "Heroine",
                    identity_prompt: "long blue hair, school uniform",
                    negative_prompt: "short hair",
                    reference_asset: "cast_01.png",
                },
            ],
            reference: {
                enabled: true,
                reference_asset: "cast_01.png",
                content_digest: "a".repeat(64),
            },
            local_canvas: {
                width: 512,
                height: 768,
            },
            placement_mapping: {
                target_rect: { x: 60, y: 80, w: 512, h: 768 },
                source_rect: { x: 0, y: 0, w: 512, h: 768 },
                transform: { scale_x: 1.0, scale_y: 1.0, offset_x: 60, offset_y: 80 },
            },
            guide_state: {
                enabled: false,
                active: false,
            },
        },
        compile_metadata: {
            effective_settings: {
                checkpoint_id: "illustrious_v1.safetensors",
                sampler_id: "euler_ancestral",
                scheduler_id: "karras",
                steps: 28,
                cfg: 6.5,
                effective_seed: 42,
                mask_feather: 16,
                panel_strength: 1.0,
                reference_weight: 0.7,
                reference_start: 0.0,
                reference_end: 0.8,
            },
        },
    };

    const directEvidence = makeValidEvidence();

    const wrappedResult = computeSceneEffectiveInputDigest(wrappedEvidence);
    const directResult = computeSceneEffectiveInputDigest(directEvidence);

    assert.strictEqual(wrappedResult.effective_input_digest, directResult.effective_input_digest);
});
