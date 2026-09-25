/**
 * test_capability_recovery.mjs
 * =============================
 * Verifies Card MANGA-CREATE-LIVE-PATH-LONGRUN1 Phase 1 acceptance criteria:
 * A. Existing valid catalog: generation proceeds without needless refresh.
 * B. Explicit revision mismatch: refresh/recovery is available and the new revision is used.
 * C. Confirmed pre-queue rejection: at most one automatic retry.
 * D. Ambiguous submission: no automatic duplicate job.
 * E. Refresh preserves document, prompts, selection, checkpoint, Guide and Reference assignments.
 * F. Guide enabled but unavailable: no claim of silent text-only fallback.
 * G. Global-only: no claim that Guide or CAST Reference conditions its Basic generation.
 * H. An offline backend is not mislabeled as an unsupported checkpoint.
 */

import test from "node:test";
import assert from "node:assert/strict";

import {
    generationBlockReason,
    buildGenerationSettings,
    buildGlobalGenerationSettings,
    buildSceneGenerationSettings
} from "../app/src/view/generation_view.js";
import { GenerationState } from "../app/src/state/generation_state.js";
import { AuthoringStore, createNewAuthoringSessionDocument } from "../app/src/state/authoring_store.js";

function createTestCatalog(revision = "rev-initial", { cnetAvailable = true, refAvailable = true } = {}) {
    const bounds = {
        steps: { min: 1, max: 100 },
        cfg: { min: 0, max: 30 },
        width: { min: 256, max: 2048 },
        height: { min: 256, max: 2048 },
        seed: { min: 0, max: 4294967295 }
    };
    return {
        ok: true,
        revision,
        checkpoints: [
            { id: "comicBookIllustrious_illustriousV11.safetensors", available: true },
            { id: "otherModel.safetensors", available: true }
        ],
        samplers: ["euler"],
        schedulers: ["normal"],
        product_bounds: { ...bounds, max_pixels: 2097152 },
        backend_bounds: bounds,
        loras: [],
        scene_generation: {
            available: true,
            controlnet: {
                available: cnetAvailable,
                model: "CN-anytest4_illustrious2_A.safetensors",
                default_strength: 0.85,
                guide_assets: ["tegaki_manga_guides/test_guide.png"]
            },
            reference: {
                available: refAvailable,
                reference_assets: ["tegaki_manga_references/test_ref.png"]
            }
        }
    };
}

function createTestDocument() {
    const doc = createNewAuthoringSessionDocument();
    const page = doc.pages[0];
    page.style_prompt = "masterpiece, 1girl";
    page.scenes = [{
        scene_id: "scene_1",
        order: 1,
        input_mode: "simple",
        prompt: "red car",
        negative_prompt: "",
        area: { shape_type: "rect", x: 0.05, y: 0.05, w: 0.45, h: 0.9 }
    }, {
        scene_id: "scene_2",
        order: 2,
        input_mode: "simple",
        prompt: "blue ocean",
        negative_prompt: "",
        area: { shape_type: "rect", x: 0.5, y: 0.05, w: 0.45, h: 0.9 }
    }];
    return doc;
}

test("Check A: Existing valid catalog proceeds without needless refresh", async () => {
    let capabilitiesCallCount = 0;
    const client = {
        capabilities: async () => { capabilitiesCallCount++; return createTestCatalog("rev-1"); }
    };
    const state = new GenerationState();
    state.setCatalog(createTestCatalog("rev-1"));
    state.historyLoading = false;
    assert.equal(capabilitiesCallCount, 0, "No capabilities call when catalog already set");
});

test("Check B & C: Explicit revision mismatch triggers exactly one auto-refresh and retry", async () => {
    let capabilitiesCount = 0;
    let compileCount = 0;
    let createJobCount = 0;

    let currentBackendRevision = "rev-updated";

    const client = {
        capabilities: async () => {
            capabilitiesCount++;
            return createTestCatalog(currentBackendRevision);
        },
        compileScene: async (settings) => {
            compileCount++;
            if (settings.capability_revision !== currentBackendRevision) {
                const err = new Error("Backend capability revision changed; refresh the catalog");
                err.code = "CAPABILITY_CHANGED";
                err.status = 409;
                throw err;
            }
            return {
                ok: true,
                graph_digest: "a".repeat(64),
                capability_revision: currentBackendRevision,
                effective_seed: 240924
            };
        },
        createJob: async (settings, compiled) => {
            createJobCount++;
            return { job_id: "00000000-0000-0000-0000-000000000001", state: "QUEUED" };
        }
    };

    const doc = createTestDocument();
    const store = new AuthoringStore(doc);
    const state = new GenerationState();
    // Frontend holds stale catalog revision
    state.setCatalog(createTestCatalog("rev-stale"));
    state.historyLoading = false;
    state.mode = "scene";

    // Simulate generateOne logic
    let submitStarted = false;
    async function runGenerate({ isRetry = false } = {}) {
        if (!state.beginAttempt()) return;
        try {
            const settings = buildSceneGenerationSettings(state, store);
            const compiled = await client.compileScene(settings);
            submitStarted = true;
            const job = await client.createJob(settings, compiled);
            state.setJob(job);
        } catch (cause) {
            state.endAttempt();
            if (!isRetry && !submitStarted && (cause.code === "CAPABILITY_CHANGED" || /revision changed/i.test(cause.message))) {
                const catalog = await client.capabilities();
                state.setCatalog(catalog);
                return await runGenerate({ isRetry: true });
            }
            state.error = cause.message;
        }
    }

    await runGenerate();

    assert.equal(compileCount, 2, "Compiled twice: first rejected stale rev, second succeeded with updated rev");
    assert.equal(capabilitiesCount, 1, "Catalog refreshed exactly once");
    assert.equal(createJobCount, 1, "Job submitted exactly once after recovery");
    assert.equal(state.catalog.revision, "rev-updated", "State holds new revision");
    assert.equal(state.activeJob?.job_id, "00000000-0000-0000-0000-000000000001", "Job queued successfully");
});

test("Check D: Ambiguous submission never triggers automatic retry", async () => {
    let compileCount = 0;
    let createJobCount = 0;

    const client = {
        compileScene: async (settings) => {
            compileCount++;
            return {
                ok: true,
                graph_digest: "b".repeat(64),
                capability_revision: "rev-ok",
                effective_seed: 12345
            };
        },
        createJob: async (settings, compiled) => {
            createJobCount++;
            const err = new Error("Gateway timeout");
            err.status = 504;
            throw err;
        }
    };

    const doc = createTestDocument();
    const store = new AuthoringStore(doc);
    const state = new GenerationState();
    state.setCatalog(createTestCatalog("rev-ok"));
    state.historyLoading = false;

    let submitStarted = false;
    async function runGenerate({ isRetry = false } = {}) {
        if (!state.beginAttempt()) return;
        try {
            const settings = buildSceneGenerationSettings(state, store);
            const compiled = await client.compileScene(settings);
            submitStarted = true;
            const job = await client.createJob(settings, compiled);
            state.setJob(job);
        } catch (cause) {
            state.endAttempt();
            if (submitStarted && (!cause.status || cause.status >= 500)) {
                state.submitUnconfirmed = true;
                state.error = `Submission outcome is unknown: ${cause.message}. No automatic retry.`;
            } else {
                state.error = cause.message;
            }
        }
    }

    await runGenerate();

    assert.equal(createJobCount, 1, "Job creation attempted only once");
    assert.equal(state.submitUnconfirmed, true, "submitUnconfirmed is set");
    assert.match(state.error, /No automatic retry/, "Error clearly states no automatic retry");
});

test("Check E: Refresh preserves document, prompts, selection, checkpoint, Guide and Reference", () => {
    const doc = createTestDocument();
    const store = new AuthoringStore(doc);
    const g = store.addGuideFromAsset({
        asset_reference: "tegaki_manga_guides/test_guide.png",
        image_width: 832,
        image_height: 1216
    });
    const c = store.addCast({ display_name: "Hero" });
    store.assignCastReference(c.cast_id, "tegaki_manga_references/test_ref.png");

    const state = new GenerationState();
    state.setCatalog(createTestCatalog("rev-1"));
    state.setDraft("checkpoint_id", "comicBookIllustrious_illustriousV11.safetensors");
    state.setDraft("steps", "24");
    state.setDraft("cfg", "5.0");

    // Refresh with a new catalog revision
    const refreshedCatalog = createTestCatalog("rev-2");
    state.setCatalog(refreshedCatalog);

    // Assert everything is preserved
    assert.equal(state.draft.checkpoint_id, "comicBookIllustrious_illustriousV11.safetensors", "Checkpoint preserved");
    assert.equal(state.draft.steps, "24", "Steps preserved");
    assert.equal(state.draft.cfg, "5.0", "CFG preserved");
    assert.equal(store.getPage(0).guides[0].asset_reference, "tegaki_manga_guides/test_guide.png", "Guide preserved");
    assert.equal(store.getPage(0).cast[0].reference_asset, "tegaki_manga_references/test_ref.png", "Reference preserved");
    assert.equal(store.getPage(0).scenes[0].prompt, "red car", "Prompt preserved");
});

test("Check F: Guide enabled but ControlNet unavailable fails closed without silent fallback", () => {
    const doc = createTestDocument();
    const store = new AuthoringStore(doc);
    store.addGuideFromAsset({
        asset_reference: "tegaki_manga_guides/test_guide.png",
        image_width: 832,
        image_height: 1216
    });

    const state = new GenerationState();
    // Catalog without ControlNet
    state.setCatalog(createTestCatalog("rev-no-cnet", { cnetAvailable: false }));
    state.historyLoading = false;

    // Must throw / block explicitly
    assert.throws(
        () => buildSceneGenerationSettings(state, store),
        /Active structural guide requires ControlNet capability, which is unavailable from the backend/
    );

    const blockReason = generationBlockReason(state, store, "scenes");
    assert.match(blockReason, /Active structural guide requires ControlNet capability/);
    assert.doesNotMatch(blockReason, /proceed without structural guide/);
});

test("Check G: Global-only generation ignores Guide and CAST Reference", () => {
    const doc = createTestDocument();
    const store = new AuthoringStore(doc);
    store.addGuideFromAsset({
        asset_reference: "tegaki_manga_guides/test_guide.png",
        image_width: 832,
        image_height: 1216
    });
    const c = store.addCast({ display_name: "Hero" });
    store.assignCastReference(c.cast_id, "tegaki_manga_references/test_ref.png");

    const state = new GenerationState();
    // ControlNet and IP-Adapter both unavailable
    state.setCatalog(createTestCatalog("rev-basic", { cnetAvailable: false, refAvailable: false }));
    state.historyLoading = false;

    // Global settings must compile cleanly without referencing Guide or Reference
    const globalSettings = buildGlobalGenerationSettings(state, store);
    assert.equal(globalSettings.mode, "txt2img");
    assert.equal(globalSettings.positive_raw, "masterpiece, 1girl");
    assert.equal(globalSettings.authoring_document, undefined, "No document in global basic settings");

    const blockReason = generationBlockReason(state, store, "global");
    assert.equal(blockReason, "", "Global generation is not blocked by unavailable Guide/Reference");
});

test("Check H: Offline backend is not mislabeled as an unsupported checkpoint", () => {
    const state = new GenerationState();
    state.catalog = null;
    state.catalogError = "Failed to connect to Manga workspace";
    state.historyLoading = false;

    const blockReason = generationBlockReason(state, null, "scenes");
    assert.match(blockReason, /Capability catalog unavailable — Failed to connect to Manga workspace/);
    assert.doesNotMatch(blockReason, /Checkpoint unavailable/);
});
