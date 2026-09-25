import test from "node:test";
import assert from "node:assert/strict";
import {
    buildGlobalGenerationSettings,
    buildSceneGenerationSettings
} from "../app/src/view/generation_view.js";

function createDocument() {
    return {
        schema_id: "TEGAKI_AUTHORING_DOCUMENT",
        schema_version: "1.0.0",
        pages: [{
            page_id: "page_1",
            width_px: 832,
            height_px: 1216,
            style_prompt: "GLOBAL_BASE",
            style_negative_prompt: "GLOBAL_NEGATIVE",
            scenes: [{
                scene_id: "scene_1",
                order: 1,
                input_mode: "cast",
                prompt: "SCENE_ACTION",
                negative_prompt: "",
                area: { shape_type: "rect", x: 0.1, y: 0.1, w: 0.8, h: 0.8 }
            }],
            visual_frames: [],
            cast: [
                { cast_id: "unused", identity_prompt: "UNUSED_IDENTITY" },
                { cast_id: "hero", identity_prompt: "CHARACTER_IDENTITY" }
            ],
            character_instances: [{
                instance_id: "instance_1",
                cast_id: "hero",
                scene_id: "scene_1",
                area: { shape_type: "rect", x: 0.25, y: 0.2, w: 0.2, h: 0.3 },
                acting_prompt: "",
                negative_prompt_override: ""
            }],
            guides: []
        }],
        metadata: {}
    };
}

function createState(document) {
    const bounds = {
        steps: { min: 1, max: 100 },
        cfg: { min: 0, max: 30 },
        width: { min: 256, max: 2048 },
        height: { min: 256, max: 2048 }
    };
    const page = document.pages[0];
    return {
        catalog: {
            revision: "scene-r1",
            scene_generation: { available: true },
            checkpoints: [{ id: "model.safetensors", available: true }],
            samplers: ["euler"],
            schedulers: ["normal"],
            product_bounds: { ...structuredClone(bounds), max_pixels: 2097152 },
            backend_bounds: structuredClone(bounds)
        },
        draft: {
            checkpoint_id: "model.safetensors",
            sampler_id: "euler",
            scheduler_id: "normal",
            steps: "4",
            cfg: "5",
            width: "832",
            height: "1216",
            seed_requested: "0"
        },
        sceneDraft: { mask_feather: 16, panel_strength: 1 },
        authoringStore: {
            getDocument: () => document,
            getPage: () => page
        }
    };
}

test("Scenes entry passes one bound CAST instance and preserves the canonical document", () => {
    const document = createDocument();
    const state = createState(document);
    const settings = buildSceneGenerationSettings(state);

    assert.equal(settings.mode, "scene");
    assert.strictEqual(settings.authoring_document, document);
    assert.equal(settings.authoring_document.pages[0].scenes[0].prompt, "SCENE_ACTION");
    assert.equal(settings.authoring_document.pages[0].cast[1].identity_prompt, "CHARACTER_IDENTITY");
    assert.deepEqual(settings.authoring_document.pages[0].character_instances[0].area,
        { shape_type: "rect", x: 0.25, y: 0.2, w: 0.2, h: 0.3 });
});

test("Scenes entry fails closed for unsupported CAST shapes or invalid bindings", () => {
    const expectBlocked = (document, message) => {
        assert.throws(() => buildSceneGenerationSettings(createState(document)), new RegExp(message));
    };

    const missingCast = createDocument();
    missingCast.pages[0].character_instances[0].cast_id = "missing";
    expectBlocked(missingCast, "unavailable CAST");

    const wrongParent = createDocument();
    wrongParent.pages[0].character_instances[0].scene_id = "missing";
    expectBlocked(wrongParent, "only Scene");

    const outsideScene = createDocument();
    outsideScene.pages[0].character_instances[0].area.x = 0.75;
    expectBlocked(outsideScene, "inside its parent Scene");

    const unplacedCastScene = createDocument();
    unplacedCastScene.pages[0].character_instances = [];
    expectBlocked(unplacedCastScene, "requires one placed Character Instance");

    const multipleInstances = createDocument();
    multipleInstances.pages[0].character_instances.push({
        ...structuredClone(multipleInstances.pages[0].character_instances[0]),
        instance_id: "instance_2"
    });
    expectBlocked(multipleInstances, "exactly one Scene and one Character Instance");

    const multipleScenes = createDocument();
    multipleScenes.pages[0].scenes.push({
        ...structuredClone(multipleScenes.pages[0].scenes[0]),
        scene_id: "scene_2", order: 2, input_mode: "simple"
    });
    expectBlocked(multipleScenes, "exactly one Scene and one Character Instance");
});

test("Unplaced CAST is ignored by Scene eligibility and Global-only stays independent", () => {
    const document = createDocument();
    document.pages[0].scenes[0].input_mode = "simple";
    document.pages[0].character_instances = [];
    const state = createState(document);

    assert.strictEqual(buildSceneGenerationSettings(state).authoring_document, document);
    const global = buildGlobalGenerationSettings(state);
    assert.equal(global.positive_raw, "GLOBAL_BASE");
    assert.equal(global.negative_raw, "GLOBAL_NEGATIVE");
    assert.equal(Object.hasOwn(global, "authoring_document"), false);
});
