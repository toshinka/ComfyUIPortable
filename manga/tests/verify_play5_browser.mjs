/** PLAY5 Scene Layout browser fixture.
 * Uses a fake backend and in-page job adapter. It verifies the same-origin
 * compile-scene proxy and the real Generate/Authoring mode surface without
 * loading a model, calling /prompt, or running generation.
 */
import assert from "node:assert/strict";
import http from "node:http";
import os from "node:os";
import path from "node:path";
import fs from "node:fs/promises";
import { createRequire } from "node:module";
import { execSync } from "node:child_process";

const require = createRequire(import.meta.url);
function resolveChromium() {
    if (process.env.TEGAKI_PLAYWRIGHT_MODULE) {
        try { return require(process.env.TEGAKI_PLAYWRIGHT_MODULE).chromium; } catch {}
    }
    try { return require("playwright").chromium; } catch {}
    const root = execSync("npm root -g", { encoding: "utf8" }).trim();
    return require(path.join(root, "@executeautomation", "playwright-mcp-server", "node_modules", "playwright")).chromium;
}

const capabilityCatalog = {
    ok: true,
    revision: "play5-browser-fixture",
    checkpoints: [{ id: "Illustrious.safetensors", available: true }],
    samplers: ["euler"],
    schedulers: ["normal"],
    scene_generation: {
        available: true,
        required_nodes: ["TegakiMangaPagePlanFromJSON", "TegakiMangaConditioningBuilder"],
        supported_scene_count: { min: 1, max: 6 },
        mask_feather: { default: 16, min: 0, max: 64 },
        panel_strength: { default: 1, min: 0, max: 2 }
    },
    product_bounds: {
        steps: { min: 1, max: 100 }, cfg: { min: 0, max: 30 },
        width: { min: 256, max: 2048, step: 8 }, height: { min: 256, max: 2048, step: 8 },
        max_pixels: 2097152
    },
    backend_bounds: {
        steps: { min: 1, max: 100 }, cfg: { min: 0, max: 30 },
        width: { min: 256, max: 2048, step: 8 }, height: { min: 256, max: 2048, step: 8 },
        seed: { min: 0, max: 4294967295 }
    }
};

const json = (res, status, body) => {
    res.writeHead(status, { "Content-Type": "application/json; charset=utf-8" });
    res.end(JSON.stringify(body));
};
const listen = server => new Promise(resolve => server.listen(0, "127.0.0.1", resolve));
const close = server => new Promise(resolve => server.close(resolve));
const readBody = async req => {
    const chunks = [];
    for await (const chunk of req) chunks.push(chunk);
    return Buffer.concat(chunks).toString("utf8");
};

let promptCalls = 0;
const backend = http.createServer(async (req, res) => {
    const url = new URL(req.url, "http://127.0.0.1");
    if (req.method === "POST" && url.pathname === "/prompt") {
        promptCalls += 1;
        return json(res, 500, { error: "PLAY5 browser fixture forbids /prompt" });
    }
    if (req.method === "GET" && url.pathname === "/queue") return json(res, 200, { queue_running: [], queue_pending: [] });
    if (req.method === "GET" && url.pathname === "/object_info/TegakiMinimumHandSceneEditor") {
        return json(res, 200, { TegakiMinimumHandSceneEditor: { input: {} } });
    }
    if (req.method === "GET" && url.pathname === "/tegaki/manga/generation/capabilities") return json(res, 200, capabilityCatalog);
    if (req.method === "POST" && url.pathname === "/tegaki/manga/generation/compile-scene") {
        const request = JSON.parse(await readBody(req));
        if (!request.authoring_document?.pages?.[0]) {
            return json(res, 422, { ok: false, error_code: "INVALID_REQUEST", error: "fixture request is incomplete" });
        }
        if (request.authoring_document?.pages?.[0]?.scenes?.some(scene => /<lora:/i.test(scene.prompt || ""))) {
            return json(res, 422, { ok: false, error_code: "SCENE_LORA_UNSUPPORTED", error: "Scene LoRA prompt notation is unavailable in PLAY5" });
        }
        const graph = {
            "1": { class_type: "CheckpointLoaderSimple", inputs: { ckpt_name: request.checkpoint_id } },
            "2": { class_type: "TegakiMangaPagePlanFromJSON", inputs: { page_compile_plan_json: "{}" } },
            "3": { class_type: "TegakiMangaConditioningBuilder", inputs: { page_compile_plan: ["2", 0], mask_feather: 16, panel_strength: 1 } },
            "4": { class_type: "EmptyLatentImage", inputs: { width: 832, height: 1216, batch_size: 1 } },
            "5": { class_type: "KSampler", inputs: { model: ["1", 0], positive: ["3", 0], negative: ["3", 1], latent_image: ["4", 0] } },
            "6": { class_type: "VAEDecode", inputs: { samples: ["5", 0], vae: ["1", 2] } },
            "7": { class_type: "SaveImage", inputs: { images: ["6", 0], filename_prefix: "Manga/Playable/compiled" } }
        };
        return json(res, 200, {
            ok: true, schema_version: "scene-1", normalized_request: request,
            effective_seed: Number(request.seed_requested), capability_revision: capabilityCatalog.revision,
            graph, graph_digest: "a".repeat(64), page_compile_plan_digest: "b".repeat(64),
            audit_trail: { scene_ids: (request.authoring_document.pages[0].scenes || []).map(scene => scene.scene_id) },
            resolved_loras: [], resolution: { width: 832, height: 1216 }
        });
    }
    return json(res, 404, { error: "PLAY5 fixture route not found" });
});

const previous = Object.fromEntries(["MANGA_BACKEND_URL", "MANGA_WORKSPACE_PORT", "MANGA_GENERATION_JOURNAL_DIR"]
    .map(key => [key, process.env[key]]));
const journalDir = await fs.mkdtemp(path.join(os.tmpdir(), "manga-play5-journal-"));
let workspace;
let browser;
let checks = 0;
function check(condition, message) { assert.ok(condition, message); checks += 1; }

try {
    await listen(backend);
    process.env.MANGA_BACKEND_URL = `http://127.0.0.1:${backend.address().port}`;
    process.env.MANGA_WORKSPACE_PORT = "0";
    process.env.MANGA_GENERATION_JOURNAL_DIR = journalDir;
    ({ server: workspace } = await import(`../service/manga_workspace_server.mjs?play5=${Date.now()}`));
    if (!workspace.listening) await new Promise(resolve => workspace.once("listening", resolve));
    const origin = `http://127.0.0.1:${workspace.address().port}`;

    const proxyResponse = await fetch(`${origin}/api/manga/generation/compile-scene`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ request_id: "proxy", mode: "scene" })
    });
    const proxyBody = await proxyResponse.json();
    check(proxyResponse.status === 422 && proxyBody.error_code === "INVALID_REQUEST",
        "compile-scene proxy reaches the backend route");

    browser = await resolveChromium().launch({ headless: true, args: ["--no-sandbox", "--disable-setuid-sandbox"] });
    const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
    const pageErrors = [];
    page.on("pageerror", error => pageErrors.push(error.message));
    await page.goto(origin, { waitUntil: "networkidle" });
    await page.waitForFunction(() => Boolean(window.__tegakiManga?.store));
    await page.waitForFunction(() => window.__tegakiManga.generation.state?.catalog?.scene_generation?.available === true);
    await page.evaluate(() => window.__tegakiManga.setMangaMode("generate"));

    check(await page.getAttribute("#mg-mode-basic", "aria-selected") === "true", "Basic Draft is the default mode");
    check(!(await page.locator("#mg-positive_raw").isHidden()), "Basic prompt is visible in Basic Draft");
    await page.click("#mg-mode-scene");
    check(await page.getAttribute("#mg-mode-scene", "aria-selected") === "true", "Scene Layout mode can be selected");
    check(await page.locator("[data-mg-basic-only]").first().isHidden(), "Basic prompt authority is hidden in Scene Layout");
    check(!(await page.locator("#mg-scene-summary").isHidden()), "Scene summary is visible in Scene Layout");
    check(await page.getAttribute("#mg-width", "readonly") !== null && await page.getAttribute("#mg-height", "readonly") !== null,
        "Scene resolution controls are read-only");
    check((await page.textContent("#mg-scene-resolution")).includes("832 × 1216"), "Authoring page resolution is displayed");
    check((await page.textContent("#mg-generate-label")).includes("Generate with Scenes"), "Scene action is explicit");

    const invalidCompile = await page.evaluate(async () => {
        const documentValue = window.__tegakiManga.store.getDocument();
        documentValue.pages[0].scenes[0].prompt = "<lora:scene-only:0.7>";
        const response = await fetch("/api/manga/generation/compile-scene", {
            method: "POST", headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ request_id: "scene-lora", mode: "scene", checkpoint_id: "Illustrious.safetensors",
                authoring_document: documentValue, page_index: 0, sampler_id: "euler", scheduler_id: "normal",
                steps: 4, cfg: 5, seed_requested: "0", capability_revision: "play5-browser-fixture" })
        });
        return { status: response.status, body: await response.json() };
    });
    check(invalidCompile.status === 422 && invalidCompile.body.error_code === "SCENE_LORA_UNSUPPORTED",
        "Scene LoRA compile rejection is human-readable and fail-closed");

    await page.evaluate(() => window.__tegakiManga.store.updateScene("scene_top", { prompt: "outdoor blue sky" }));
    await page.evaluate(() => window.__tegakiManga.store.updateScene("scene_bottom", { prompt: "indoor classroom", negative_prompt: "" }));
    await page.evaluate(() => {
        const captured = { compile: 0, create: 0, settings: null };
        window.__play5Captured = captured;
        const generation = window.__tegakiManga.generation;
        generation.client.compileScene = async settings => {
            captured.compile += 1; captured.settings = structuredClone(settings);
            return { capability_revision: settings.capability_revision, effective_seed: Number(settings.seed_requested), graph_digest: "a".repeat(64) };
        };
        generation.client.createJob = async settings => {
            captured.create += 1; captured.settings = structuredClone(settings);
            return { job_id: "11111111-1111-4111-8111-111111111111", state: "QUEUED", requested_settings: settings };
        };
    });
    await page.click("#mg-generate");
    await page.waitForFunction(() => window.__tegakiManga.generation.state.activeJob?.state === "QUEUED");
    const captured = await page.evaluate(() => window.__play5Captured);
    check(captured.compile === 1 && captured.create === 1, "Generate with Scenes creates one Scene job after compile");
    check(captured.settings.mode === "scene" && captured.settings.authoring_document.pages[0].scenes.length === 2,
        "Scene job receives the current AuthoringDocument");
    check(captured.settings.authoring_document.pages[0].width_px === 832 && captured.settings.authoring_document.pages[0].height_px === 1216,
        "Scene job uses document resolution authority");

    await page.evaluate(() => window.__tegakiManga.generation.state.setJob({
        job_id: "22222222-2222-4222-8222-222222222222", state: "SUCCEEDED",
        requested_settings: { mode: "scene", checkpoint_id: "Illustrious.safetensors", sampler_id: "euler", scheduler_id: "normal", steps: 5, cfg: 5, seed_requested: "0", mask_feather: 16, panel_strength: 1,
            authoring_document: window.__tegakiManga.store.getDocument(), page_index: 0 }
    }));
    await page.click(".mg-restore");
    check(await page.getAttribute("#mg-mode-scene", "aria-selected") === "true", "Restore settings preserves Scene Layout mode");
    await page.click("#mg-edit-scenes");
    check(await page.isVisible("#authoring-workspace"), "Edit Scenes returns to Authoring");
    check(pageErrors.length === 0, `browser errors: ${pageErrors.join("; ")}`);
    check(promptCalls === 0, "PLAY5 browser fixture performed no /prompt submission");
    console.log(`MANGA-PLAY5 BROWSER FIXTURE PASS: ${checks} checks; /prompt calls ${promptCalls}; real generation 0`);
} finally {
    if (browser) await browser.close();
    if (workspace) await close(workspace);
    await close(backend);
    for (const [key, value] of Object.entries(previous)) {
        if (value === undefined) delete process.env[key]; else process.env[key] = value;
    }
    await fs.rm(journalDir, { recursive: true, force: true });
}
