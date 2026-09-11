/**
 * verify_m1a_browser.mjs — Playwright Real Browser Gate Suite (M1A)
 * =================================================================
 * Verifies all Card requirements in a real browser session:
 * Gate A: Standalone page loads without ComfyUI LiteGraph UI.
 * Gate B: Default TEGAKI_AUTHORING_DOCUMENT 1.0.0 renders.
 * Gate C: Scene geometry visibly renders on the standalone canvas.
 * Gate D: Fixture containing CAST / Character Instance / Frame / Guide renders those layers.
 * Gate E: Switching standalone view/layer selection does not mutate exported document JSON.
 * Gate F: Import/export document round-trip PASS.
 * Gate G: Backend indicator distinguishes Manga-capable runtime.
 * Gate H: Prepare Standard Draft succeeds through the existing Manga endpoint.
 * Gate I: Backend /queue remains empty.
 * Gate J: No image generation occurs.
 */

import assert from "node:assert";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { createRequire } from "node:module";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const require = createRequire(import.meta.url);

import fs from "node:fs";
import { execSync } from "node:child_process";

function resolvePlaywright() {
    // 1. Explicit environment variable (Card Section 7)
    if (process.env.TEGAKI_PLAYWRIGHT_MODULE) {
        try {
            const mod = require(process.env.TEGAKI_PLAYWRIGHT_MODULE);
            if (mod?.chromium) return mod.chromium;
        } catch (e) {}
    }

    // 2. Normal installed module resolution
    try {
        const mod = require("playwright");
        if (mod?.chromium) return mod.chromium;
    } catch (e) {}

    // 3. Machine-independent discovery from npm global root
    try {
        const npmRoot = execSync("npm root -g", { encoding: "utf8" }).trim();
        if (npmRoot) {
            const candidates = [
                path.join(npmRoot, "playwright"),
                path.join(npmRoot, "@executeautomation", "playwright-mcp-server", "node_modules", "playwright")
            ];
            for (const cand of candidates) {
                if (fs.existsSync(cand)) {
                    try {
                        const mod = require(cand);
                        if (mod?.chromium) return mod.chromium;
                    } catch (e) {}
                }
            }
        }
    } catch (e) {}

    // 4. Platform APPDATA fallback
    const appData = process.env.APPDATA;
    if (appData) {
        const winCand = path.join(appData, "npm", "node_modules", "@executeautomation", "playwright-mcp-server", "node_modules", "playwright");
        if (fs.existsSync(winCand)) {
            try {
                const mod = require(winCand);
                if (mod?.chromium) return mod.chromium;
            } catch (e) {}
        }
    }

    throw new Error(
        "Playwright could not be resolved. Please set TEGAKI_PLAYWRIGHT_MODULE or ensure Playwright is installed."
    );
}

const chromium = resolvePlaywright();

const WORKSPACE_URL = process.env.MANGA_WORKSPACE_URL || "http://127.0.0.1:8191";
const BACKEND_URL = process.env.MANGA_BACKEND_URL || "http://127.0.0.1:8189";

console.log(`--- Running verify_m1a_browser.mjs against ${WORKSPACE_URL} (Backend: ${BACKEND_URL}) ---`);

const browser = await chromium.launch({
    headless: true,
    args: ["--no-sandbox", "--disable-setuid-sandbox"]
});

const page = await browser.newPage();

try {
    // Navigate to standalone workspace
    await page.goto(WORKSPACE_URL, { waitUntil: "networkidle", timeout: 10000 });
    console.log("✓ Page loaded successfully");

    // Gate A: Standalone page loads without ComfyUI LiteGraph UI
    const litegraphCanvas = await page.$("canvas.graph-canvas");
    assert.strictEqual(litegraphCanvas, null, "Gate A: ComfyUI LiteGraph canvas must NOT be present");
    const appBrand = await page.textContent(".brand-title");
    assert.strictEqual(appBrand.trim(), "TEGAKI Manga", "Gate A: Standalone brand must be visible");
    console.log("✓ Gate A PASS: Standalone page loads without ComfyUI LiteGraph UI");

    // Gate B: Default TEGAKI_AUTHORING_DOCUMENT 1.0.0 renders
    const schemaLabel = await page.textContent("#doc-schema-label");
    assert.ok(schemaLabel.includes("TEGAKI_AUTHORING_DOCUMENT 1.0.0"), "Gate B: Schema label match");
    const sceneCount = await page.textContent("#count-scenes");
    assert.strictEqual(sceneCount.trim(), "2", "Gate B: Default doc has 2 scenes");
    console.log("✓ Gate B PASS: Default TEGAKI_AUTHORING_DOCUMENT 1.0.0 renders");

    // Gate C: Scene geometry visibly renders on standalone canvas
    const canvasBox = await page.evaluate(() => {
        const c = document.getElementById("manga-canvas");
        const ctx = c.getContext("2d");
        const imgData = ctx.getImageData(0, 0, c.width, c.height);
        let nonWhitePixels = 0;
        for (let i = 0; i < imgData.data.length; i += 4) {
            const r = imgData.data[i];
            const g = imgData.data[i + 1];
            const b = imgData.data[i + 2];
            if (r < 250 || g < 250 || b < 250) nonWhitePixels++;
        }
        return { width: c.width, height: c.height, nonWhitePixels };
    });
    assert.ok(canvasBox.nonWhitePixels > 500, "Gate C: Canvas must contain rendered non-white geometry");
    console.log(`✓ Gate C PASS: Scene geometry visibly renders on canvas (${canvasBox.nonWhitePixels} colored pixels)`);

    // Gate D: Load Rich Fixture containing CAST, Instances, Frames, Guides
    await page.click("#btn-load-fixture");
    await page.waitForTimeout(300);

    const richScenes = await page.textContent("#count-scenes");
    const richFrames = await page.textContent("#count-frames");
    const richCast = await page.textContent("#count-cast");
    const richInstances = await page.textContent("#count-instances");
    const richGuides = await page.textContent("#count-guides");

    assert.strictEqual(richScenes.trim(), "2");
    assert.strictEqual(richFrames.trim(), "2");
    assert.strictEqual(richCast.trim(), "2");
    assert.strictEqual(richInstances.trim(), "2");
    assert.strictEqual(richGuides.trim(), "1");
    console.log("✓ Gate D PASS: Fixture containing CAST / Character Instance / Frame / Guide renders all layers");

    // Gate E: Switching standalone view/layer selection does not mutate exported document JSON
    const exportedBefore = await page.evaluate(() => window.__tegakiManga.store.exportJson(false));

    // Switch tabs and select different items
    await page.click("#tab-frames");
    await page.waitForTimeout(100);
    await page.click("#tab-guides");
    await page.waitForTimeout(100);
    await page.click("#tab-cast");
    await page.waitForTimeout(100);
    await page.click("#tab-scenes");
    await page.waitForTimeout(100);

    const exportedAfter = await page.evaluate(() => window.__tegakiManga.store.exportJson(false));
    assert.strictEqual(exportedBefore, exportedAfter, "Gate E: Session selection must not mutate exported document JSON");
    console.log("✓ Gate E PASS: Switching standalone view/layer selection does not mutate exported document JSON");

    // Gate F: Import/Export document round-trip
    await page.click("#btn-export-json");
    await page.waitForSelector("#export-modal", { state: "visible" });
    const exportedModalText = await page.inputValue("#modal-json-text");
    assert.ok(exportedModalText.includes("doc_rich_fixture_m1a"));
    await page.click("#btn-close-modal");
    await page.waitForSelector("#export-modal", { state: "hidden" });

    // Reset to default then re-import exported JSON
    await page.click("#btn-reset-default");
    await page.waitForTimeout(200);
    assert.strictEqual(await page.textContent("#count-cast"), "0");

    await page.click("#btn-load-json");
    await page.waitForSelector("#export-modal", { state: "visible" });
    await page.fill("#modal-json-text", exportedModalText);
    await page.click("#btn-modal-action");
    await page.waitForTimeout(200);

    assert.strictEqual(await page.textContent("#count-cast"), "2");
    assert.strictEqual(await page.textContent("#count-frames"), "2");
    console.log("✓ Gate F PASS: Import/export document round-trip PASS");

    // Reset to default for backend prepare test
    await page.click("#btn-reset-default");
    await page.waitForTimeout(200);

    // Gate G: Backend indicator distinguishes Manga-capable runtime
    // Set backend URL in input
    await page.fill("#backend-url-input", BACKEND_URL);
    await page.click("#btn-check-backend");
    await page.waitForTimeout(1000);

    const backendStatus = await page.textContent("#backend-status-text");
    console.log(`Backend status text: ${backendStatus.trim()}`);
    assert.strictEqual(backendStatus.trim(), "MANGA READY", "Gate G: Backend indicator must show MANGA READY");
    console.log("✓ Gate G PASS: Backend indicator distinguishes Manga-capable runtime");

    // Gate H: Prepare Standard Draft succeeds through the existing Manga endpoint
    await page.click("#btn-prepare-draft");
    await page.waitForTimeout(1500);

    const prepareFeedbackText = await page.textContent("#prepare-feedback");
    console.log(`Prepare feedback: ${prepareFeedbackText}`);
    assert.ok(prepareFeedbackText.includes("Prepared route: STANDARD_NO_GUIDE"), "Gate H: Route must be STANDARD_NO_GUIDE");
    console.log("✓ Gate H PASS: Prepare Standard Draft succeeds with STANDARD_NO_GUIDE");

    // Gate I: Backend /queue remains empty
    assert.ok(prepareFeedbackText.includes("Queue IDLE"), "Gate I: Queue must remain empty and idle");
    console.log("✓ Gate I PASS: Backend /queue remains empty");

    // Gate J: No image generation occurs
    const genCheck = await page.evaluate(async () => {
        const data = await window.__tegakiManga.client.getQueue();
        return {
            running: data.queue_running?.length || 0,
            pending: data.queue_pending?.length || 0
        };
    });
    assert.strictEqual(genCheck.running, 0, "Gate J: No generations running");
    assert.strictEqual(genCheck.pending, 0, "Gate J: No generations pending");
    console.log("✓ Gate J PASS: Zero image generations occurred");

    console.log("");
    console.log("==================================================");
    console.log("ALL REAL BROWSER FEASIBILITY GATES PASSED (A - J)");
    console.log("==================================================");

} finally {
    await browser.close();
}
