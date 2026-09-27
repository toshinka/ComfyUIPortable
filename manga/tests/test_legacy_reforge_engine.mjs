// MANGA-LEGACY-EASYREFORGE-VERTICAL-MVP1: frontend engine gating + backend-neutral recipe.
import test from "node:test";
import assert from "node:assert/strict";
import { MangaGenerationClient } from "../app/src/adapters/manga_generation_client.js";
import {
    buildLegacyReforgeRecipe, createLegacyReforgeEngine, engineSamplingLists, ensureEngineState, legacyReforgeBlockReason
} from "../app/src/view/legacy_reforge_engine.js";

const CATALOG = {
    checkpoints: [{ id: "!新規SDモデル\\comic.safetensors", available: true }],
    vaes: [{ id: "Illustrious\\XlVaeC_f2.safetensors", available: true }],
    samplers: ["euler"], schedulers: ["simple"],
    product_bounds: { steps: { min: 1, max: 100 }, cfg: { min: 0, max: 30 }, width: { min: 256, max: 2048 }, height: { min: 256, max: 2048 } },
    backend_bounds: { steps: { min: 1, max: 10000 }, cfg: { min: 0, max: 100 }, width: { min: 16, max: 16384 }, height: { min: 16, max: 16384 } },
};
const page = { style_prompt: "1girl, <lora:a:0.45>, <lora:b:0.72>", style_negative_prompt: "lowres" };
const store = { getPage: () => page };

function makeState(status) {
    const state = ensureEngineState({
        catalog: CATALOG, error: "", localBusy: false,
        draft: { checkpoint_id: "!新規SDモデル\\comic.safetensors", sampler_id: "euler", scheduler_id: "simple", steps: "28", cfg: "5.5",
            width: "832", height: "1216", seed_requested: "-1", vae_id: "" },
        beginAttempt() { if (this.localBusy) return false; this.localBusy = true; return true; }, endAttempt() { this.localBusy = false; },
    });
    state.legacy.status = status;
    return state;
}
const READY = { available: true, state: "ready", port: 7862, owned: true };

function fakeClient(status = READY, resultBlob = "BLOB") {
    const calls = [];
    return { calls,
        legacyStatus: async () => status,
        legacyCapabilities: async () => ({ samplers: ["Euler a", "Euler SMEA Dy"], schedulers: ["karras", "phi"] }),
        legacyGenerate: async recipe => { calls.push(recipe); return { job_id: "j1", state: "running" }; },
        legacyJob: async () => ({ job_id: "j1", state: "completed", result: { backend: "easyreforge", seed: 5 } }),
        legacyResult: async () => resultBlob,
    };
}

test("EASYREFORGE becomes selectable only when the backend reports the Integration Runtime available", async () => {
    const state = makeState(null);
    const engine = createLegacyReforgeEngine({ state, client: fakeClient({ available: false, installed_reason: "missing python", state: "stopped" }), authoringStore: store, doc: null });
    assert.equal(engine.setEngine("easyreforge"), false, "unknown availability -> not operational");
    await engine.refreshStatus();
    assert.equal(engine.setEngine("easyreforge"), false, "unavailable -> not operational");
    assert.equal(state.engine, "comfyui", "MANGA/COMFYUI remains the route");
    assert.equal(engine.setEngine("comfyui"), true, "MANGA/COMFYUI stays selectable");
    assert.equal(engine.setEngine("h3"), false, "no H3 engine inside MANGA");
    engine.dispose();
    const readyState = makeState(null);
    const ready = createLegacyReforgeEngine({ state: readyState, client: fakeClient(), authoringStore: store, doc: null });
    await ready.refreshStatus();
    assert.equal(ready.setEngine("easyreforge"), true);
    assert.equal(readyState.engine, "easyreforge");
    ready.dispose();
});

test("external readiness makes EASYREFORGE selectable without ownership and never falls back on disappearance", async () => {
    let status = { available: true, state: "ready", port: 7862, owned: false };
    const state = makeState(null);
    const client = fakeClient(status);
    const engine = createLegacyReforgeEngine({ state, client, authoringStore: store, doc: null });
    await engine.refreshStatus();
    assert.equal(engine.setEngine("easyreforge"), true);
    assert.equal(state.engine, "easyreforge");

    status = { available: false, state: "stopped", port: 7862, owned: false };
    client.legacyStatus = async () => status;
    await engine.refreshStatus();
    assert.equal(state.engine, "easyreforge", "runtime loss does not silently switch Manga backends");
    assert.equal(await engine.generate(), null, "a vanished runtime blocks Generate instead of falling back");
    assert.equal(client.calls.length, 0, "no EasyReforge generation request is dispatched");
    assert.equal(state.engine, "easyreforge");
    engine.dispose();
});

test("engine-specific sampler/scheduler lists; switching never cross-maps values silently", async () => {
    const state = makeState(null);
    const engine = createLegacyReforgeEngine({ state, client: fakeClient(), authoringStore: store, doc: null });
    await engine.refreshStatus();
    assert.equal(engineSamplingLists(state), null, "COMFYUI keeps the Comfy catalog");
    engine.setEngine("easyreforge");
    assert.deepEqual(engineSamplingLists(state), { samplers: ["Euler a", "Euler SMEA Dy"], schedulers: ["karras", "phi"] });
    assert.deepEqual([state.draft.sampler_id, state.draft.scheduler_id], ["", ""], "no Comfy value carried into EasyReforge");
    assert.match(legacyReforgeBlockReason(state, store, "global"), /Choose an EasyReforge sampler/);
    state.draft.sampler_id = "Euler SMEA Dy";
    state.draft.scheduler_id = "phi";
    engine.setEngine("comfyui");
    assert.deepEqual([state.draft.sampler_id, state.draft.scheduler_id], ["euler", "simple"], "Comfy choice restored");
    engine.setEngine("easyreforge");
    assert.deepEqual([state.draft.sampler_id, state.draft.scheduler_id], ["Euler SMEA Dy", "phi"]);
    engine.dispose();
});

test("backend-neutral recipe from the existing controls; prompt with LoRA tokens passed untouched", () => {
    const state = makeState(READY);
    state.engine = "easyreforge";
    state.legacy.samplers = ["Euler a"];
    state.legacy.schedulers = ["karras"];
    state.draft.sampler_id = "Euler a";
    state.draft.scheduler_id = "karras";
    const before = JSON.stringify(page);
    const recipe = buildLegacyReforgeRecipe(state, store);
    assert.deepEqual(recipe, { engine: "easyreforge", checkpoint_id: "!新規SDモデル\\comic.safetensors", vae_id: "",
        positive_raw: page.style_prompt, negative_raw: "lowres", sampler: "Euler a", scheduler: "karras",
        steps: 28, cfg: 5.5, width: 832, height: 1216, seed_requested: "-1" });
    assert.equal(JSON.stringify(page), before, "Authoring prompt is never mutated");
    assert.ok(!Object.keys(recipe).some(k => /script|gradio|args/i.test(k)));
    assert.match(legacyReforgeBlockReason(state, store, "scenes"), /ComfyUI-only/);
    state.legacy.status = { available: true, state: "stopped" };
    assert.match(legacyReforgeBlockReason(state, store, "global"), /not running/);
    state.legacy.status = READY;
    state.draft.vae_id = "Illustrious\\missing.safetensors";
    assert.match(legacyReforgeBlockReason(state, store, "global"), /VAE unavailable/);
});

test("generate dispatches the recipe to the EasyReforge route and returns its JPEG Blob to the Stage hook", async () => {
    const state = makeState(null);
    const jpeg = new Blob([Uint8Array.from([0xff, 0xd8, 0xff, 0xd9])], { type: "image/jpeg" });
    const client = fakeClient(READY, jpeg);
    const shown = [];
    const engine = createLegacyReforgeEngine({ state, client, authoringStore: store, doc: null, pollMs: 0, sleep: async () => {},
        hooks: { showBlob: async (id, blob) => shown.push([id, blob]) } });
    await engine.refreshStatus();
    engine.setEngine("easyreforge");
    state.draft.sampler_id = "Euler a";
    state.draft.scheduler_id = "karras";
    const job = await engine.generate();
    assert.equal(job.state, "completed");
    assert.equal(client.calls.length, 1);
    assert.equal(client.calls[0].engine, "easyreforge");
    assert.deepEqual(shown, [["j1", jpeg]]);
    assert.equal(shown[0][1].type, "image/jpeg");
    assert.equal(state.legacy.lastResult.backend, "easyreforge");
    assert.equal(state.localBusy, false);
    engine.dispose();
});

test("result clients preserve EasyReforge JPEG MIME while ComfyUI remains PNG-only", async () => {
    const client = new MangaGenerationClient();
    const originalFetch = globalThis.fetch;
    const jpegBytes = Uint8Array.from([0xff, 0xd8, 0x11, 0x22, 0xff, 0xd9]);
    const response = (mime, bytes = jpegBytes) => ({ ok: true, status: 200,
        headers: { get: name => name.toLowerCase() === "content-type" ? mime : null },
        blob: async () => new Blob([bytes], { type: mime.split(";")[0] }) });
    try {
        globalThis.fetch = async () => response("image/jpeg");
        const legacyBlob = await client.legacyResult("jpeg-job");
        assert.equal(legacyBlob.type, "image/jpeg");
        assert.deepEqual(new Uint8Array(await legacyBlob.arrayBuffer()), jpegBytes);
        await assert.rejects(client.getResult("comfy-job"), error => error.code === "RESULT_UNAVAILABLE",
            "standard Manga/Comfy result retrieval still rejects JPEG");

        globalThis.fetch = async () => response("image/webp");
        await assert.rejects(client.legacyResult("webp-job"), error => error.code === "RESULT_UNAVAILABLE");

        const pngBytes = Uint8Array.from([137, 80, 78, 71, 13, 10, 26, 10]);
        globalThis.fetch = async () => response("image/png", pngBytes);
        const comfyBlob = await client.getResult("comfy-job");
        assert.equal(comfyBlob.type, "image/png");
        assert.deepEqual(new Uint8Array(await comfyBlob.arrayBuffer()), pngBytes);
    } finally {
        globalThis.fetch = originalFetch;
    }
});
