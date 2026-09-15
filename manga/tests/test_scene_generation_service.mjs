/** PLAY5 GenerationService Scene route contract against a fake backend. */
import test from "node:test";
import assert from "node:assert/strict";
import http from "node:http";
import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { randomUUID } from "node:crypto";
import { GenerationService } from "../service/generation_service.mjs";
import { GenerationJournal } from "../service/generation_journal.mjs";

const DIGEST = "a".repeat(64);
const documentValue = {
    schema_id: "TEGAKI_AUTHORING_DOCUMENT", schema_version: "1.0.0", pages: [{
        page_id: "page_1", width_px: 832, height_px: 1216,
        style_prompt: "manga", style_negative_prompt: "blur",
        scenes: [{ scene_id: "scene_one", order: 1, prompt: "outdoor", negative_prompt: "", input_mode: "simple",
            area: { shape_type: "rect", x: 0.1, y: 0.1, w: 0.8, h: 0.35 }, metadata: {} }],
        visual_frames: [], cast: [], character_instances: [], guides: [], generation: { seed: 0 }, metadata: {}
    }], metadata: {}
};
const settings = () => ({
    mode: "scene", checkpoint_id: "Illustrious.safetensors", authoring_document: structuredClone(documentValue), page_index: 0,
    sampler_id: "euler", scheduler_id: "normal", steps: 4, cfg: 5, seed_requested: "0", capability_revision: "scene-r1"
});
const json = (res, status, value) => { res.writeHead(status, { "Content-Type": "application/json" }); res.end(JSON.stringify(value)); };
const close = server => new Promise(resolve => server.close(resolve));

class SceneBackend {
    constructor() {
        this.promptCalls = 0;
        this.promptId = randomUUID();
        this.server = http.createServer((req, res) => this.handle(req, res));
    }
    async start() {
        await new Promise(resolve => this.server.listen(0, "127.0.0.1", resolve));
        this.origin = `http://127.0.0.1:${this.server.address().port}`;
    }
    async handle(req, res) {
        const target = new URL(req.url, "http://127.0.0.1");
        if (target.pathname === "/object_info/TegakiMinimumHandSceneEditor") return json(res, 200, { TegakiMinimumHandSceneEditor: { input: {} } });
        if (target.pathname === "/queue") return json(res, 200, { queue_running: [], queue_pending: [] });
        if (target.pathname === "/tegaki/manga/generation/capabilities") return json(res, 200, { ok: true, revision: "scene-r1" });
        if (target.pathname === "/tegaki/manga/generation/compile-scene") {
            let body = "";
            for await (const chunk of req) body += chunk;
            const request = JSON.parse(body);
            const graph = {
                "1": { class_type: "CheckpointLoaderSimple", inputs: { ckpt_name: request.checkpoint_id } },
                "2": { class_type: "TegakiMangaPagePlanFromJSON", inputs: { page_compile_plan_json: "{}" } },
                "3": { class_type: "TegakiMangaConditioningBuilder", inputs: { page_compile_plan: ["2", 0], panel_strength: 1, mask_feather: 16 } },
                "4": { class_type: "EmptyLatentImage", inputs: { width: 832, height: 1216, batch_size: 1 } },
                "5": { class_type: "KSampler", inputs: { model: ["1", 0], positive: ["3", 0], negative: ["3", 1], latent_image: ["4", 0] } },
                "6": { class_type: "VAEDecode", inputs: { samples: ["5", 0], vae: ["1", 2] } },
                "7": { class_type: "SaveImage", inputs: { images: ["6", 0], filename_prefix: "Manga/Playable/compiled" } }
            };
            const refAsset = request.authoring_document?.pages?.[0]?.cast?.[0]?.reference_asset;
            if (refAsset) {
                graph["8"] = { class_type: "CLIPVisionLoader", inputs: { clip_name: "CLIP-ViT-H-14-laion2B-s32B-b79K.safetensors" } };
                graph["9"] = { class_type: "IPAdapterModelLoader", inputs: { ipadapter_file: "ip-adapter-plus_sdxl_vit-h.safetensors" } };
                graph["10"] = { class_type: "LoadImage", inputs: { image: `${refAsset} [input]` } };
                graph["11"] = { class_type: "IPAdapterAdvanced", inputs: {
                    model: ["1", 0], ipadapter: ["9", 0], image: ["10", 0], clip_vision: ["8", 0], attn_mask: ["3", 3],
                    weight: 0.7, weight_type: "linear", combine_embeds: "concat", start_at: 0.0, end_at: 1.0, embeds_scaling: "V only"
                }};
                graph["5"].inputs.model = ["11", 0];
            }
            return json(res, 200, { ok: true, normalized_request: request, effective_seed: Number(request.seed_requested),
                capability_revision: "scene-r1", graph, graph_digest: DIGEST, page_compile_plan_digest: "b".repeat(64),
                audit_trail: { global: {}, scenes: [], scene_ids: ["scene_one"] }, resolved_loras: [],
                effective_authoring_document: request.authoring_document, page_compile_plan: {}, scene_ids: ["scene_one"],
                resolution: { width: 832, height: 1216 }, wildcard_root: "manga/wildcards", dynamicprompts_version: "test", dynamic_seed_domains: {} });
        }
        if (target.pathname === "/prompt") {
            this.promptCalls += 1;
            let body = "";
            for await (const chunk of req) body += chunk;
            this.payload = JSON.parse(body);
            return json(res, 200, { prompt_id: this.promptId, number: 1, node_errors: {} });
        }
        return json(res, 404, { error: "unknown route" });
    }
}

test("Scene job uses backend prompt authority and submits one reviewed graph", async t => {
    const directory = await fs.mkdtemp(path.join(os.tmpdir(), "manga-play5-service-"));
    const backend = new SceneBackend();
    await backend.start();
    const service = new GenerationService({ backendUrl: backend.origin, journal: new GenerationJournal(directory) });
    t.after(async () => { await close(backend.server); await fs.rm(directory, { recursive: true, force: true }); });
    const job = await service.createSceneJob({ settings: settings(), idempotency_key: "scene-one", expected_graph_digest: DIGEST });
    assert.equal(backend.promptCalls, 1);
    assert.equal(job.state, "QUEUED");
    assert.equal(job.prompt_id, backend.promptId);
    assert.notEqual(job.job_id, job.prompt_id);
    assert.equal(job.requested_settings.mode, "scene");
    assert.equal(job.resolution.width, 832);
    assert.equal(job.scene_ids[0], "scene_one");
    assert.equal(backend.payload.prompt["7"].inputs.filename_prefix, `Manga/Playable/${job.job_id}`);
});

test("Scene submission rejects unknown settings before backend submission", async t => {
    const directory = await fs.mkdtemp(path.join(os.tmpdir(), "manga-play5-service-invalid-"));
    const backend = new SceneBackend();
    await backend.start();
    const service = new GenerationService({ backendUrl: backend.origin, journal: new GenerationJournal(directory) });
    t.after(async () => { await close(backend.server); await fs.rm(directory, { recursive: true, force: true }); });
    await assert.rejects(() => service.createSceneJob({ settings: { ...settings(), width: 832 }, idempotency_key: "scene-bad", expected_graph_digest: DIGEST }),
        error => error.code === "INVALID_REQUEST");
    assert.equal(backend.promptCalls, 0);
});

test("Scene journal EPERM is a structured write failure before prompt submission", async t => {
    const directory = await fs.mkdtemp(path.join(os.tmpdir(), "manga-play5-service-journal-"));
    const backend = new SceneBackend();
    await backend.start();
    const failingFs = {
        mkdir: fs.mkdir, readdir: fs.readdir, readFile: fs.readFile, rename: fs.rename, rm: fs.rm,
        open: async () => { const error = new Error("EPERM: operation not permitted"); error.code = "EPERM"; throw error; }
    };
    const service = new GenerationService({
        backendUrl: backend.origin, journal: new GenerationJournal(directory, failingFs)
    });
    t.after(async () => { await close(backend.server); await fs.rm(directory, { recursive: true, force: true }); });
    await assert.rejects(
        () => service.createSceneJob({ settings: settings(), idempotency_key: "scene-journal-eperm", expected_graph_digest: DIGEST }),
        error => error instanceof Error && error.code === "JOURNAL_WRITE_FAILED" && /journal write failed/i.test(error.message)
    );
    assert.equal(backend.promptCalls, 0);
});

test("Scene submission rejects stale or mismatched expected_graph_digest with DIGEST_MISMATCH (409)", async t => {
    const directory = await fs.mkdtemp(path.join(os.tmpdir(), "manga-play5-service-digest-"));
    const backend = new SceneBackend();
    await backend.start();
    const service = new GenerationService({ backendUrl: backend.origin, journal: new GenerationJournal(directory) });
    t.after(async () => { await close(backend.server); await fs.rm(directory, { recursive: true, force: true }); });

    // Negative control: wrong / stale digest must fail closed before /prompt
    const staleDigest = "b".repeat(64);
    await assert.rejects(
        () => service.createSceneJob({ settings: settings(), idempotency_key: "scene-stale-digest", expected_graph_digest: staleDigest }),
        error => error.code === "DIGEST_MISMATCH" && error.status === 409
    );
    assert.equal(backend.promptCalls, 0);
});

test("Reference Scene job passes compile validation with identical digest and submits reviewed graph", async t => {
    const directory = await fs.mkdtemp(path.join(os.tmpdir(), "manga-play5-service-ref-"));
    const backend = new SceneBackend();
    await backend.start();
    const service = new GenerationService({ backendUrl: backend.origin, journal: new GenerationJournal(directory) });
    t.after(async () => { await close(backend.server); await fs.rm(directory, { recursive: true, force: true }); });

    const refDoc = structuredClone(documentValue);
    refDoc.pages[0].cast = [{ cast_id: "heroine", identity_prompt: "heroine", reference_asset: "tegaki_manga_references/ref_test.png" }];
    refDoc.pages[0].character_instances = [{
        instance_id: "inst_1", cast_id: "heroine", scene_id: "scene_one",
        area: { shape_type: "rect", x: 0.1, y: 0.1, w: 0.8, h: 0.35 }
    }];
    const refSettings = { ...settings(), authoring_document: refDoc };

    const job = await service.createSceneJob({ settings: refSettings, idempotency_key: "scene-ref-pass", expected_graph_digest: DIGEST });
    assert.equal(backend.promptCalls, 1);
    assert.equal(job.state, "QUEUED");
    assert.equal(job.prompt_id, backend.promptId);
    assert.equal(backend.payload.prompt["10"].class_type, "LoadImage");
    assert.equal(backend.payload.prompt["11"].class_type, "IPAdapterAdvanced");
    assert.equal(backend.payload.prompt["5"].inputs.model[0], "11");
});
