/** MANGA-PLAY2 Scene Composer browser fixture.
 * Real workspace server + fake capability backend; no /prompt, GPU, or model IO.
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

const catalog = {
    ok: true,
    revision: "play2-fake-revision",
    checkpoints: [{ id: "Illustrious.safetensors", available: true }],
    samplers: ["euler"],
    schedulers: ["normal"],
    product_bounds: {
        steps: { min: 1, max: 100 }, cfg: { min: 0, max: 30 },
        width: { min: 256, max: 2048 }, height: { min: 256, max: 2048 }, max_pixels: 2097152
    },
    backend_bounds: {
        steps: { min: 1, max: 100 }, cfg: { min: 0, max: 30 },
        width: { min: 256, max: 2048 }, height: { min: 256, max: 2048 }, seed: { min: 0, max: 4294967295 }
    }
};

const json = (res, status, value) => {
    res.writeHead(status, { "Content-Type": "application/json; charset=utf-8" });
    res.end(JSON.stringify(value));
};
const listen = server => new Promise(resolve => server.listen(0, "127.0.0.1", resolve));
const close = server => new Promise(resolve => server.close(resolve));

const backend = http.createServer((req, res) => {
    const url = new URL(req.url, "http://127.0.0.1");
    if (req.method === "POST" && url.pathname === "/prompt") {
        promptCalls++;
        return json(res, 500, { error: "Generation is forbidden in this fixture" });
    }
    if (req.method === "GET" && url.pathname === "/queue") return json(res, 200, { queue_running: [], queue_pending: [] });
    if (req.method === "GET" && url.pathname === "/object_info/TegakiMinimumHandSceneEditor") {
        return json(res, 200, { TegakiMinimumHandSceneEditor: { input: {} } });
    }
    if (req.method === "GET" && url.pathname === "/tegaki/manga/generation/capabilities") return json(res, 200, catalog);
    return json(res, 404, { error: "fixture route not found" });
});

const previous = Object.fromEntries(["MANGA_BACKEND_URL", "MANGA_WORKSPACE_PORT", "MANGA_GENERATION_JOURNAL_DIR"]
    .map(key => [key, process.env[key]]));
const journalDir = await fs.mkdtemp(path.join(os.tmpdir(), "manga-play2-journal-"));
let workspace;
let browser;
let checks = 0;
let promptCalls = 0;
function check(condition, message) { assert.ok(condition, message); checks++; }

try {
    await listen(backend);
    const backendOrigin = `http://127.0.0.1:${backend.address().port}`;
    process.env.MANGA_BACKEND_URL = backendOrigin;
    process.env.MANGA_WORKSPACE_PORT = "0";
    process.env.MANGA_GENERATION_JOURNAL_DIR = journalDir;
    ({ server: workspace } = await import(`../service/manga_workspace_server.mjs?play2=${Date.now()}`));
    if (!workspace.listening) await new Promise(resolve => workspace.once("listening", resolve));
    const origin = `http://127.0.0.1:${workspace.address().port}`;
    browser = await resolveChromium().launch({ headless: true, args: ["--no-sandbox", "--disable-setuid-sandbox"] });
    const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
    const pageErrors = [];
    page.on("pageerror", error => pageErrors.push(error.message));
    await page.goto(origin, { waitUntil: "networkidle" });
    await page.waitForFunction(() => Boolean(window.__tegakiManga?.store));

    check(await page.isVisible("#scene-composer-panel"), "Scene Composer is the default Authoring panel");
    check(await page.getAttribute("#scene-prompt-tabs", "role") === "tablist", "prompt tabs expose tablist semantics");
    check(await page.locator("#scene-prompt-tabs [role=tab]").count() === 3, "Global plus two scene tabs are generated");
    check(await page.getAttribute("#scene-prompt-tab-global", "aria-selected") === "true", "Global is the initial prompt target");
    await page.click("#composer-advanced-toggle");
    check(await page.getAttribute("#composer-advanced-toggle", "aria-expanded") === "true" &&
        await page.isVisible("#count-frames"), "Advanced Authoring reveals the preserved layer editors");
    await page.click("#composer-advanced-toggle");

    const initial = await page.evaluate(() => {
        const doc = window.__tegakiManga.store.getDocument();
        return { json: JSON.stringify(doc), keys: Object.keys(doc.pages[0]), scenes: doc.pages[0].scenes.map(scene => ({ ...scene })) };
    });
    check(initial.keys.includes("style_prompt") && initial.keys.includes("style_negative_prompt"), "Composer uses existing page prompt fields");

    await page.fill("#scene-composer-prompt", "global layout direction");
    await page.fill("#scene-composer-negative", "global exclusions");
    await page.click("#scene-prompt-tab-scene_top");
    check(await page.isVisible("#scene-composer-name-wrap") && await page.inputValue("#scene-composer-prompt") === initial.scenes[0].prompt,
        "Scene tab maps to scene prompt and name editor");
    await page.fill("#scene-composer-name", "Opening Room");
    await page.fill("#scene-composer-prompt", "scene one prompt");
    await page.fill("#scene-composer-negative", "scene one negative");
    await page.click("#scene-prompt-tab-scene_bottom");
    check(await page.inputValue("#scene-composer-prompt") === initial.scenes[1].prompt,
        "Scene two prompt is isolated from Scene one");
    await page.click("#scene-prompt-tab-global");
    check(await page.inputValue("#scene-composer-prompt") === "global layout direction" &&
        await page.inputValue("#scene-composer-negative") === "global exclusions",
        "Global prompt and negative persist independently");

    const canvasBox = await page.locator("#manga-canvas").boundingBox();
    const sceneTop = initial.scenes[0].area;
    await page.mouse.click(canvasBox.x + (sceneTop.x + sceneTop.w / 2) * canvasBox.width,
        canvasBox.y + (sceneTop.y + sceneTop.h / 2) * canvasBox.height);
    check((await page.textContent("#scene-composer-selection")).includes("Opening Room") &&
        await page.getAttribute("#scene-prompt-tab-scene_top", "aria-selected") === "true",
        "Canvas scene click selects the matching prompt tab");

    await page.click("#scene-tool-add");
    await page.waitForTimeout(100);
    const afterAdd = await page.evaluate(() => ({
        scenes: window.__tegakiManga.store.getPage().scenes.map(scene => ({ id: scene.scene_id, area: { ...scene.area } })),
        selected: window.__tegakiManga.session.selectedSceneId
    }));
    check(afterAdd.scenes.length === 3 && afterAdd.selected === "scene_3" &&
        afterAdd.scenes[2].area.w > 0.3 && afterAdd.scenes[2].area.h > 0.05,
        "+ Scene immediately creates a bounded normalized rectangle and selects it");
    check(await page.locator("#scene-prompt-tabs [role=tab]").count() === 4, "New Scene receives a dynamic prompt tab");
    check(await page.getAttribute("#scene-prompt-tab-scene_3", "aria-selected") === "true",
        "New Scene tab is selected immediately");

    const addedBeforeMove = afterAdd.scenes[2].area;
    const addedCenter = { x: canvasBox.x + (addedBeforeMove.x + addedBeforeMove.w / 2) * canvasBox.width,
        y: canvasBox.y + (addedBeforeMove.y + addedBeforeMove.h / 2) * canvasBox.height };
    await page.mouse.move(addedCenter.x, addedCenter.y);
    await page.mouse.down();
    await page.mouse.move(addedCenter.x + 20, addedCenter.y + 16, { steps: 3 });
    await page.mouse.up();
    const afterMove = await page.evaluate(() => ({ ...window.__tegakiManga.store.getPage().scenes.find(scene => scene.scene_id === "scene_3").area }));
    check(afterMove.x > addedBeforeMove.x && afterMove.y > addedBeforeMove.y, "Selected scene body drag moves the scene");

    const seBefore = afterMove;
    const se = { x: canvasBox.x + (seBefore.x + seBefore.w) * canvasBox.width,
        y: canvasBox.y + (seBefore.y + seBefore.h) * canvasBox.height };
    await page.mouse.move(se.x, se.y);
    await page.mouse.down();
    await page.mouse.move(se.x + 18, se.y + 18, { steps: 3 });
    await page.mouse.up();
    const afterSE = await page.evaluate(() => ({ ...window.__tegakiManga.store.getPage().scenes.find(scene => scene.scene_id === "scene_3").area }));
    check(afterSE.w > seBefore.w && afterSE.h > seBefore.h, "SE scene handle resizes without invalid geometry");

    const nwBefore = afterSE;
    const nw = { x: canvasBox.x + nwBefore.x * canvasBox.width, y: canvasBox.y + nwBefore.y * canvasBox.height };
    await page.mouse.move(nw.x, nw.y);
    await page.mouse.down();
    await page.mouse.move(nw.x - 12, nw.y - 12, { steps: 3 });
    await page.mouse.up();
    const afterNW = await page.evaluate(() => ({ ...window.__tegakiManga.store.getPage().scenes.find(scene => scene.scene_id === "scene_3").area }));
    check(afterNW.x < nwBefore.x && afterNW.y < nwBefore.y && afterNW.w > nwBefore.w && afterNW.h > nwBefore.h,
        "NW scene handle resizes from the opposite anchor");

    await page.click("#scene-prompt-tab-scene_3");
    await page.fill("#scene-composer-name", "Inserted Panel");
    await page.fill("#scene-composer-prompt", "new panel prompt");
    await page.fill("#scene-composer-negative", "new panel negative");
    const edited = await page.evaluate(() => window.__tegakiManga.store.getPage().scenes.find(scene => scene.scene_id === "scene_3"));
    check(edited.name === "Inserted Panel" && edited.prompt === "new panel prompt" && edited.negative_prompt === "new panel negative",
        "Selected scene name, prompt, and negative update through Store");
    const editedPageKeys = await page.evaluate(() => Object.keys(window.__tegakiManga.store.getDocument().pages[0]));
    check(JSON.stringify(editedPageKeys) === JSON.stringify(initial.keys), "Composer edits add no durable schema fields");

    await page.click("#scene-tool-delete");
    const afterDelete = await page.evaluate(() => ({
        scenes: window.__tegakiManga.store.getPage().scenes,
        selected: window.__tegakiManga.session.selectedSceneId
    }));
    check(afterDelete.scenes.length === 2 && afterDelete.selected === "scene_bottom",
        "Delete selects the nearest surviving scene deterministically");

    await page.evaluate(() => {
        const store = window.__tegakiManga.store;
        while (store.getPage().scenes.length < 6) store.addScene({});
    });
    await page.waitForTimeout(100);
    await page.click("#scene-tool-add");
    check((await page.textContent("#scene-tool-status")).includes("Maximum 6 scenes") &&
        (await page.evaluate(() => window.__tegakiManga.store.getPage().scenes.length)) === 6,
        "Scene creation fails closed at the six-scene limit");

    await page.evaluate(() => {
        const store = window.__tegakiManga.store;
        const doc = store.getDocument();
        doc.pages[0].scenes = [doc.pages[0].scenes[0]];
        store.setDocument(doc);
    });
    await page.waitForTimeout(100);
    await page.click("#scene-tool-delete");
    check((await page.evaluate(() => window.__tegakiManga.store.getPage().scenes.length)) === 1 &&
        (await page.textContent("#scene-composer-error")).includes("only scene"),
        "Only scene deletion is visibly rejected");

    await page.click("#btn-reset-default");
    await page.waitForTimeout(100);
    const resetKeys = await page.evaluate(() => Object.keys(window.__tegakiManga.store.getPage()));
    check(JSON.stringify(resetKeys) === JSON.stringify(initial.keys), "Reset preserves the existing document field set");

    await page.evaluate(() => window.__tegakiManga.setMangaMode("generate"));
    await page.fill("#mg-positive_raw", "draft survives authoring switch");
    await page.evaluate(() => window.__tegakiManga.setMangaMode("authoring"));
    check(await page.inputValue("#mg-positive_raw") === "draft survives authoring switch" && await page.isVisible("#scene-composer-panel"),
        "Generate draft and Authoring Composer state survive mode switches");

    await page.setViewportSize({ width: 700, height: 800 });
    const narrowCanvas = await page.locator("#canvas-container").boundingBox();
    const narrowInspector = await page.locator("#inspector-panel").boundingBox();
    check(narrowInspector.y > narrowCanvas.y && narrowInspector.width >= narrowCanvas.width,
        "Narrow layout places Canvas before the Prompt workspace");

    check(pageErrors.length === 0, `browser errors: ${pageErrors.join("; ")}`);
    console.log(`MANGA-PLAY2 BROWSER FIXTURE PASS: ${checks} checks; /prompt calls ${promptCalls}; real generation 0`);
} finally {
    if (browser) await browser.close();
    if (workspace) await close(workspace);
    await close(backend);
    for (const [key, value] of Object.entries(previous)) {
        if (value === undefined) delete process.env[key]; else process.env[key] = value;
    }
    await fs.rm(journalDir, { recursive: true, force: true });
}
