/** PLAY1c browser fixture: fake Manga backend + real workspace server; no GPU or live /prompt. */
import assert from "node:assert/strict";
import http from "node:http";
import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { randomUUID } from "node:crypto";
import { createRequire } from "node:module";
import { execSync } from "node:child_process";

const require = createRequire(import.meta.url);
function playwrightChromium() {
    if (process.env.TEGAKI_PLAYWRIGHT_MODULE) return require(process.env.TEGAKI_PLAYWRIGHT_MODULE).chromium;
    try { return require("playwright").chromium; } catch {}
    const root = execSync("npm root -g", { encoding: "utf8" }).trim();
    return require(path.join(root, "@executeautomation", "playwright-mcp-server", "node_modules", "playwright")).chromium;
}
const PNG = Buffer.from("iVBORw0KGgoAAAANSUhEUgAAAAgAAAAICAIAAABLbSncAAAAEUlEQVR4nGN4ty8TK2IYWhIAMhSFQUajvSoAAAAASUVORK5CYII=", "base64");
const DIGEST = "a".repeat(64);
const catalog = {
    ok: true, revision: "fake-revision", checkpoints: [
        { id: "Illustrious.safetensors", available: true },
        { id: "Gone.safetensors", available: false }
    ], samplers: ["euler", "dpm_2"], schedulers: ["normal", "simple"],
    product_bounds: { steps: { min: 1, max: 100 }, cfg: { min: 0, max: 30 },
        width: { min: 256, max: 2048 }, height: { min: 256, max: 2048 },
        max_pixels: 2097152 },
    backend_bounds: { steps: { min: 1, max: 100 }, cfg: { min: 0, max: 30 },
        width: { min: 256, max: 2048 }, height: { min: 256, max: 2048 },
        seed: { min: 0, max: 4294967295 } }
};
const json = (res, status, data) => {
    res.writeHead(status, { "Content-Type": "application/json" }); res.end(JSON.stringify(data));
};
const listen = server => new Promise(resolve => server.listen(0, "127.0.0.1", resolve));
const close = server => new Promise(resolve => server.close(resolve));
function graph(request) {
    const seed = request.seed_requested === "-1" ? 42 : Number(request.seed_requested);
    return {
        "1": { class_type: "CheckpointLoaderSimple", inputs: { ckpt_name: request.checkpoint_id } },
        "2": { class_type: "CLIPTextEncode", inputs: { text: request.positive_raw, clip: ["1", 1] } },
        "3": { class_type: "CLIPTextEncode", inputs: { text: request.negative_raw, clip: ["1", 1] } },
        "4": { class_type: "EmptyLatentImage", inputs: { width: request.width, height: request.height, batch_size: 1 } },
        "5": { class_type: "KSampler", inputs: { model: ["1", 0], positive: ["2", 0], negative: ["3", 0],
            latent_image: ["4", 0], seed, steps: request.steps, cfg: request.cfg,
            sampler_name: request.sampler_id, scheduler: request.scheduler_id, denoise: 1 } },
        "6": { class_type: "VAEDecode", inputs: { samples: ["5", 0], vae: ["1", 2] } },
        "7": { class_type: "SaveImage", inputs: { images: ["6", 0], filename_prefix: "Manga/Playable/compiled" } }
    };
}
class FakeBackend {
    constructor() {
        this.mode = "accept";
        this.queue_pending = [];
        this.queue_running = [];
        this.history = {};
        this.promptCalls = 0;
        this.compileCalls = 0;
        this.lastCompile = null;
        this.lastPrompt = null;
        this.server = http.createServer((req, res) => this.handle(req, res));
    }
    async handle(req, res) {
        const target = new URL(req.url, "http://127.0.0.1");
        if (req.method === "GET" && target.pathname === "/object_info/TegakiMinimumHandSceneEditor") {
            return json(res, 200, { TegakiMinimumHandSceneEditor: { input: {} } });
        }
        if (req.method === "GET" && target.pathname === "/queue") {
            return json(res, 200, { queue_running: this.queue_running, queue_pending: this.queue_pending });
        }
        if (req.method === "GET" && target.pathname === "/tegaki/manga/generation/capabilities") return json(res, 200, catalog);
        if (req.method === "POST" && target.pathname === "/tegaki/manga/generation/compile-basic") {
            let raw = ""; for await (const part of req) raw += part;
            const input = JSON.parse(raw); this.compileCalls++; this.lastCompile = input;
            if (!catalog.checkpoints.some(item => item.id === input.checkpoint_id && item.available)) {
                return json(res, 400, { ok: false, error_code: "CHECKPOINT_UNAVAILABLE", error: "Checkpoint unavailable" });
            }
            const tags = [...input.positive_raw.matchAll(/<[^<>]*>/g), ...input.negative_raw.matchAll(/<[^<>]*>/g)];
            if (tags.some(match => match[0] !== "<lora:ink:0.8>")) {
                return json(res, 400, { ok: false, error_code: "LORA_MALFORMED", error: "Malformed or unavailable LoRA tag" });
            }
            return json(res, 200, { ok: true, graph: graph(input), graph_digest: DIGEST,
                capability_revision: catalog.revision, normalized_request: input,
                effective_seed: input.seed_requested === "-1" ? 42 : Number(input.seed_requested),
                positive_raw: input.positive_raw, negative_raw: input.negative_raw,
                positive_expanded: input.positive_raw, negative_expanded: input.negative_raw,
                positive_clean: input.positive_raw, negative_clean: input.negative_raw, resolved_loras: [] });
        }
        if (req.method === "POST" && target.pathname === "/prompt") {
            this.promptCalls++;
            let raw = ""; for await (const part of req) raw += part;
            const input = JSON.parse(raw);
            assert.equal(Object.hasOwn(input, "prompt_id"), false);
            this.lastPrompt = { ...input, prompt_id: randomUUID() };
            if (this.mode === "reject") return json(res, 400, { error: { message: "Fake backend rejected" }, node_errors: {} });
            if (this.mode === "ambiguous_lost") return json(res, 408, { error: "Fake ambiguous submit" });
            this.queue_pending = [this.tuple(this.lastPrompt)];
            return json(res, 200, { prompt_id: this.lastPrompt.prompt_id, number: 1, node_errors: {} });
        }
        if (req.method === "GET" && target.pathname === "/history") return json(res, 200, this.history);
        if (req.method === "GET" && target.pathname.startsWith("/history/")) {
            const id = target.pathname.split("/").pop();
            return json(res, 200, this.history[id] ? { [id]: this.history[id] } : {});
        }
        if (req.method === "GET" && target.pathname === "/view") {
            res.writeHead(200, { "Content-Type": "image/png" }); res.end(PNG); return;
        }
        return json(res, 404, { error: "Fake route not found" });
    }
    tuple(prompt = this.lastPrompt) { return [0, prompt.prompt_id, prompt.prompt, prompt.extra_data, ["7"]]; }
    finish() {
        const p = this.lastPrompt;
        const jobId = p.extra_data.tegaki_manga.job_id;
        this.queue_pending = []; this.queue_running = [];
        this.history[p.prompt_id] = { prompt: this.tuple(p), status: { status_str: "success", completed: true, messages: [] },
            outputs: { "7": { images: [{ filename: `${jobId}_00001_.png`, subfolder: "Manga\\Playable", type: "output" }] } } };
    }
}

const backend = new FakeBackend();
const journalDir = await fs.mkdtemp(path.join(os.tmpdir(), "manga-play1c-journal-"));
let workspace, browser;
const previous = Object.fromEntries(["MANGA_BACKEND_URL", "MANGA_WORKSPACE_PORT", "MANGA_GENERATION_JOURNAL_DIR"].map(key => [key, process.env[key]]));
let checks = 0;
function check(condition, message) { assert.ok(condition, message); checks++; }
try {
    await listen(backend.server);
    backend.origin = `http://127.0.0.1:${backend.server.address().port}`;
    process.env.MANGA_BACKEND_URL = backend.origin;
    process.env.MANGA_WORKSPACE_PORT = "0";
    process.env.MANGA_GENERATION_JOURNAL_DIR = journalDir;
    ({ server: workspace } = await import(`../service/manga_workspace_server.mjs?play1c=${Date.now()}`));
    if (!workspace.listening) await new Promise(resolve => workspace.once("listening", resolve));
    const origin = `http://127.0.0.1:${workspace.address().port}`;
    browser = await playwrightChromium().launch({ headless: true, args: ["--no-sandbox", "--disable-setuid-sandbox"] });
    const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
    const pageErrors = [];
    const browserRequests = [];
    page.on("pageerror", error => pageErrors.push(error.message));
    page.on("request", request => browserRequests.push(request.url()));
    await page.goto(origin, { waitUntil: "networkidle" });
    check(await page.isVisible("#generate-view") &&
        await page.getAttribute("#mg-mode-basic", "aria-selected") === "true",
        "standalone mode enters unified production workspace with Basic Draft default");
    await page.click("#mg-mode-basic");
    await page.waitForFunction(() => Boolean(window.__tegakiManga?.generation?.state.catalog));
    check(await page.locator("#mg-checkpoint_id option").count() === 2, "catalog checkpoints populate");
    check(await page.inputValue("#mg-checkpoint_id") === "Illustrious.safetensors", "available checkpoint default");
    check(await page.locator("#mg-sampler_id option").count() === 2 && await page.locator("#mg-scheduler_id option").count() === 2,
        "sampler and scheduler catalog populate");
    check(await page.getAttribute("#mg-width", "min") === "256" && await page.getAttribute("#mg-steps", "max") === "100", "bounds populate");
    check(await page.getAttribute("#generate-view", "data-presentation") === "glance" &&
        await page.getAttribute("#mg-focus-toggle", "aria-label") === "Focus Preview" &&
        (await page.getAttribute("#mg-focus-toggle", "aria-pressed")) === "false", "Generate enters explicit GLANCE");
    const widePreview = await page.locator(".mg-stage").boundingBox();
    const wideCreate = await page.locator("#mg-create").boundingBox();
    const wideHistory = await page.locator(".mg-history-section").boundingBox();
    await page.screenshot({ path: path.join(os.tmpdir(), "manga-play1c-wide.png"), fullPage: true });
    check(wideCreate.x < widePreview.x && wideHistory.y > widePreview.y, "wide Create/Preview/History hierarchy");
    check(widePreview.height < 280 && wideCreate.width > 360, "empty GLANCE prioritizes usable Create controls");
    await page.fill("#mg-positive_raw", "draft survives presentation focus");
    await page.click("#mg-focus-toggle");
    const emptyFocusPreview = await page.locator(".mg-stage").boundingBox();
    check(await page.getAttribute("#generate-view", "data-presentation") === "focus" &&
        await page.getAttribute("#mg-focus-toggle", "aria-label") === "Return to Create view" &&
        emptyFocusPreview.height > widePreview.height &&
        await page.inputValue("#mg-positive_raw") === "draft survives presentation focus", "explicit GLANCE to FOCUS preserves draft");
    await page.click(".mg-page-heading");
    check(await page.getAttribute("#generate-view", "data-presentation") === "focus", "click outside does not change FOCUS");
    await page.keyboard.press("Escape");
    check(await page.getAttribute("#generate-view", "data-presentation") === "glance" &&
        await page.inputValue("#mg-positive_raw") === "draft survives presentation focus", "scoped Escape returns to GLANCE without input loss");
    await page.locator("#mg-create").evaluate(element => { element.scrollTop = element.scrollHeight; });
    check(await page.locator("#mg-create").evaluate(element => element.scrollTop > 0), "wide Create controls scroll independently");
    await page.mouse.move(wideCreate.x + wideCreate.width / 2, wideCreate.y + wideCreate.height / 2);
    await page.mouse.wheel(0, 900);
    await page.waitForTimeout(100);
    check(await page.evaluate(() => window.scrollY > 0), "page scroll reaches History after Create scroll");
    await page.evaluate(() => window.scrollTo(0, 0));

    await page.evaluate(() => window.__tegakiManga.generation.state.setDraft("checkpoint_id", "missing.safetensors"));
    await page.click("#mg-refresh-catalog");
    await page.waitForFunction(() => document.querySelector("#mg-checkpoint_id")?.value === "missing.safetensors");
    check(await page.inputValue("#mg-checkpoint_id") === "missing.safetensors" &&
        (await page.textContent("#mg-checkpoint_id")).includes("Unavailable · missing.safetensors"),
        "stale checkpoint remains visible after catalog refresh");
    check(await page.isDisabled("#mg-generate") &&
        (await page.textContent("#mg-generate-reason")).includes("Checkpoint unavailable") &&
        backend.promptCalls === 0, "stale checkpoint explains disabled Generate without fallback submit");
    await page.selectOption("#mg-checkpoint_id", "Gone.safetensors");
    check(await page.isDisabled("#mg-generate") &&
        (await page.textContent("#mg-generate-reason")).includes("Checkpoint unavailable") &&
        await page.inputValue("#mg-checkpoint_id") === "Gone.safetensors" && backend.promptCalls === 0,
        "unavailable choice remains visible with an explicit disabled reason");
    await page.selectOption("#mg-checkpoint_id", "Illustrious.safetensors");
    await page.fill("#mg-positive_raw", "hero <lora:broken>");
    await page.click("#mg-generate");
    await page.waitForFunction(() => document.querySelector("#mg-error")?.textContent.includes("LoRA"));
    check(await page.inputValue("#mg-positive_raw") === "hero <lora:broken>" && backend.promptCalls === 0,
        "malformed LoRA text retained without submit");
    await page.fill("#mg-positive_raw", "hero at sunrise <lora:ink:0.8>");
    await page.fill("#mg-negative_raw", "blur");
    await page.fill("#mg-seed_requested", "0");
    await page.evaluate(() => document.querySelector("#mg-generate").click());
    check((await page.textContent("#mg-status")).includes("SUBMITTING") && await page.isDisabled("#mg-generate"),
        "Generate immediately shows SUBMITTING and disables repeat clicks");
    await page.evaluate(() => document.querySelector("#mg-generate").click());
    await page.waitForFunction(() => window.__tegakiManga?.generation?.state.activeJob?.state === "QUEUED");
    check((await page.textContent("#mg-status")).includes("QUEUED") &&
        (await page.textContent("#mg-generate-label")) === "Generating…", "QUEUED state and active button label are visible");
    check(backend.promptCalls === 1, "double click creates one Manga job");
    check(backend.lastCompile.seed_requested === "0" && backend.lastPrompt.prompt["5"].inputs.seed === 0, "seed 0 survives compile and submit");
    check(backend.lastCompile.positive_raw === "hero at sunrise <lora:ink:0.8>", "manual LoRA notation reaches compiler as raw text");
    check(await page.isDisabled("#mg-generate") &&
        (await page.textContent("#mg-generate-reason")).includes("Job already active"),
        "Generate disabled with an owned-job reason");
    backend.finish();
    await page.waitForFunction(() => window.__tegakiManga?.generation?.state.activeJob?.state === "SUCCEEDED", { timeout: 10000 });
    await page.waitForFunction(() => document.querySelector("#mg-preview-image")?.naturalWidth > 0, { timeout: 10000 });
    check((await page.textContent("#mg-status")).includes("SUCCEEDED"), "SUCCEEDED state is visible");
    const firstPreview = await page.getAttribute("#mg-preview-image", "src");
    check(firstPreview.startsWith("blob:") && await page.isVisible("#mg-preview-image"), "validated PLAY1b PNG enters Preview");
    await page.click("#mg-focus-toggle");
    const resultFocusPreview = await page.locator(".mg-stage").boundingBox();
    check(await page.getAttribute("#generate-view", "data-result") === "validated" &&
        await page.isVisible("#mg-preview-image") && await page.getAttribute("#mg-preview-image", "src") === firstPreview &&
        resultFocusPreview.height > widePreview.height && await page.isVisible("#mg-status"), "FOCUS retains validated result and truthful status");
    await page.click("#mg-focus-toggle");
    check(await page.getAttribute("#generate-view", "data-presentation") === "glance" &&
        await page.getAttribute("#mg-preview-image", "src") === firstPreview, "return to GLANCE retains validated result identity");
    check(browserRequests.every(url => !url.startsWith(backend.origin)), "Browser never calls backend directly");

    backend.mode = "reject";
    await page.fill("#mg-seed_requested", "-1");
    await page.fill("#mg-positive_raw", "another panel");
    await page.click("#mg-generate");
    await page.waitForFunction(() => window.__tegakiManga?.generation?.state.activeJob?.state === "FAILED");
    const failed = await page.evaluate(() => window.__tegakiManga.generation.state.activeJob);
    check((await page.textContent("#mg-status")).includes("FAILED"), "FAILED state is visible");
    check(failed.requested_settings.seed_requested === "-1" && failed.effective_settings.seed_requested === "42", "random seed requested/effective truth");
    check(await page.inputValue("#mg-seed_requested") === "-1", "draft seed -1 retained");
    check(await page.getAttribute("#mg-preview-image", "src") === firstPreview &&
        (await page.textContent("#mg-preview-label")).includes("Previous verified result"), "FAILED retains previous successful Preview");
    const beforeRestoreCalls = backend.promptCalls;
    await page.fill("#mg-positive_raw", "edited draft");
    await page.locator(".mg-history-row").first().getByRole("button", { name: "Restore settings" }).click();
    check(await page.inputValue("#mg-positive_raw") === "another panel" &&
        await page.inputValue("#mg-seed_requested") === "-1" && backend.promptCalls === beforeRestoreCalls,
        "Restore settings changes controls only");

    backend.mode = "ambiguous_lost";
    await page.fill("#mg-positive_raw", "uncertain panel");
    await page.click("#mg-generate");
    await page.waitForFunction(() => window.__tegakiManga?.generation?.state.activeJob?.state === "UNKNOWN");
    check(await page.isDisabled("#mg-generate") && (await page.textContent("#mg-status")).includes("UNKNOWN"), "UNKNOWN visible and blocks new submit");
    check(await page.getAttribute("#mg-preview-image", "src") === firstPreview, "UNKNOWN retains previous successful Preview");
    const unknownPromptCount = backend.promptCalls;
    await page.waitForTimeout(1700);
    check(backend.promptCalls === unknownPromptCount, "UNKNOWN polling never resubmits");

    await page.click("#mg-mode-scene");
    check((await page.getAttribute("#btn-prepare-draft", "title")).includes("never generates") &&
        (await page.textContent("#prepare-feedback")).includes("prepare-only"),
        "Authoring prepare action is explicitly prepare-only");
    const beforeAuthoring = await page.evaluate(() => ({ json: window.__tegakiManga.store.exportJson(true),
        session: window.__tegakiManga.session.getSnapshot() }));
    await page.click("#scene-tool-add");
    const afterAuthoring = await page.evaluate(() => ({ json: window.__tegakiManga.store.exportJson(true),
        session: window.__tegakiManga.session.getSnapshot() }));
    check(beforeAuthoring.json !== afterAuthoring.json, "authoring interaction still works");
    await page.click("#mg-mode-basic");
    check(await page.inputValue("#mg-positive_raw") === "uncertain panel", "Generate draft survives tab switch");
    await page.click("#mg-mode-scene");
    const returnedAuthoring = await page.evaluate(() => ({ json: window.__tegakiManga.store.exportJson(true),
        session: window.__tegakiManga.session.getSnapshot() }));
    check(returnedAuthoring.json === afterAuthoring.json &&
        JSON.stringify(returnedAuthoring.session) === JSON.stringify(afterAuthoring.session), "AuthoringStore and session survive tab switch");
    await page.click("#mg-mode-basic");
    await page.setViewportSize({ width: 430, height: 850 });
    const narrowPreview = await page.locator(".mg-stage").boundingBox();
    const narrowCreate = await page.locator("#mg-create").boundingBox();
    const narrowHistory = await page.locator(".mg-history-section").boundingBox();
    check(narrowCreate.y > narrowPreview.y && narrowHistory.y > narrowCreate.y, "narrow Preview/Create/History order");
    await page.screenshot({ path: path.join(os.tmpdir(), "manga-play1c-narrow.png"), fullPage: true });

    const embeddedPage = await browser.newPage({ viewport: { width: 1440, height: 900 } });
    await embeddedPage.goto(`${origin}/?embedded=1`, { waitUntil: "networkidle" });
    await embeddedPage.waitForFunction(() => Boolean(window.__tegakiManga?.generation?.state.catalog));
    check(await embeddedPage.getAttribute("#mg-mode-basic", "aria-selected") === "true" &&
        await embeddedPage.isVisible("#generate-view") && await embeddedPage.isHidden("#authoring-workspace"),
        "embedded mode defaults to Generate");
    check(!await embeddedPage.isVisible(".manga-identity") && !await embeddedPage.isVisible(".mg-page-heading"),
        "embedded mode hides duplicate Manga chrome and heading");
    await embeddedPage.close();
    const beforeReload = backend.promptCalls;
    await page.reload({ waitUntil: "networkidle" });
    await page.click("#mg-mode-basic");
    await page.waitForFunction(() => document.querySelectorAll(".mg-history-row").length >= 3);
    check(backend.promptCalls === beforeReload, "reload displays journal jobs without resubmit");
    const responseLostPage = await browser.newPage();
    await responseLostPage.goto(origin, { waitUntil: "networkidle" });
    await responseLostPage.click("#mg-mode-basic");
    await responseLostPage.waitForFunction(() => Boolean(window.__tegakiManga?.generation?.state.catalog) &&
        !window.__tegakiManga.generation.state.historyLoading);
    await responseLostPage.evaluate(() => {
        window.__tegakiManga.generation.client.createJob = async () => { throw new Error("Dropped workspace response"); };
    });
    await responseLostPage.click("#mg-generate");
    await responseLostPage.waitForFunction(() => window.__tegakiManga.generation.state.submitUnconfirmed);
    check(await responseLostPage.isDisabled("#mg-generate") &&
        (await responseLostPage.textContent("#mg-status")).includes("UNKNOWN"),
        "lost job-create response stays visibly uncertain and blocks repeat click");
    check(backend.promptCalls === beforeReload, "lost response path has no second backend submit");
    await responseLostPage.close();
    check(pageErrors.length === 0, `no browser errors: ${pageErrors.join("; ")}`);
    console.log(`MANGA-PLAY1c BROWSER FIXTURE PASS: ${checks} checks; fake /prompt calls ${backend.promptCalls}; real /prompt 0`);
} finally {
    if (browser) await browser.close();
    if (workspace) await close(workspace);
    await close(backend.server);
    for (const [key, value] of Object.entries(previous)) {
        if (value === undefined) delete process.env[key]; else process.env[key] = value;
    }
    const resolved = path.resolve(journalDir);
    if (!resolved.startsWith(path.resolve(os.tmpdir()) + path.sep)) throw new Error("Unexpected journal cleanup path");
    await fs.rm(journalDir, { recursive: true, force: true });
}
