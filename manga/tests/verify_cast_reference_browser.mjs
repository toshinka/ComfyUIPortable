/**
 * verify_cast_reference_browser.mjs — Playwright Real Browser Gate Suite (MANGA-CAST-REFERENCE-DATA1)
 * ================================================================================================
 * Verifies end-to-end:
 * 1. Load Standalone Workspace
 * 2. Add CAST member
 * 3. Ingest reference PNG via file picker (+ Reference)
 * 4. Verify thumbnail preview rendered with naturalWidth > 0 and readout set to canonical ref
 * 5. Verify exported JSON document contains reference_asset under CAST
 * 6. Verify roundtrip persistence across default reset and JSON re-import
 * 7. Replace reference asset with WEBP, verify updated in store and UI
 * 8. Clear reference asset, verify readout returns to (none), thumbnail hidden, store set to null
 * 9. Regressions & Invariants:
 *    - Scene creation works (+ Scene tool)
 *    - Character placement works
 *    - Autocomplete remains operational
 *    - 0 /prompt calls, 0 GPU operations
 */

import assert from "node:assert/strict";
import path from "node:path";
import http from "node:http";
import { fileURLToPath } from "node:url";
import { createRequire } from "node:module";
import fs from "node:fs";
import os from "node:os";
import { execSync } from "node:child_process";

// Hard 10-minute wall-clock timeout guard
const testTimeout = setTimeout(() => {
    console.error("FATAL: Browser verification test timed out after 10 minutes");
    process.exit(1);
}, 10 * 60 * 1000);
testTimeout.unref();

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const require = createRequire(import.meta.url);

function resolvePlaywright() {
    if (process.env.TEGAKI_PLAYWRIGHT_MODULE) {
        try {
            const mod = require(process.env.TEGAKI_PLAYWRIGHT_MODULE);
            if (mod?.chromium) return mod.chromium;
        } catch (e) {}
    }

    try {
        const mod = require("playwright");
        if (mod?.chromium) return mod.chromium;
    } catch (e) {}

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

    throw new Error("Cannot resolve playwright in current runtime environment");
}

// Minimal valid PNG (1x1)
const TINY_PNG = Buffer.from([
    0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,
    0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52,
    0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,
    0x08, 0x06, 0x00, 0x00, 0x00, 0x1F, 0x15, 0xC4, 0x89,
    0x00, 0x00, 0x00, 0x0A, 0x49, 0x44, 0x41, 0x54,
    0x78, 0x9C, 0x63, 0x00, 0x01, 0x00, 0x00, 0x05, 0x00, 0x01, 0x0D, 0x0A, 0x2D, 0xB4,
    0x00, 0x00, 0x00, 0x00, 0x49, 0x45, 0x4E, 0x44,
    0xAE, 0x42, 0x60, 0x82
]);

// Minimal valid WEBP (1x1)
const TINY_WEBP = Buffer.from([
    0x52, 0x49, 0x46, 0x46, 0x1A, 0x00, 0x00, 0x00,
    0x57, 0x45, 0x42, 0x50, 0x56, 0x50, 0x38, 0x4C,
    0x0E, 0x00, 0x00, 0x00, 0x2F, 0x00, 0x00, 0x00,
    0x00, 0x07, 0x88, 0x88, 0x08, 0x00, 0x00, 0x00
]);

const FIXTURE_TAGS = [
    { tag: "1girl", category: "general", ranking: 900 },
    { tag: "solo", category: "general", ranking: 700 }
];

const capabilityCatalog = {
    ok: true,
    revision: "cast-reference-fixture",
    checkpoints: [{ id: "Illustrious.safetensors", available: true }],
    loras: [],
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

// 1. Setup Fake Backend
const backendUploadedFiles = new Map();
let promptCalls = 0;

const fakeBackend = http.createServer((req, res) => {
    const url = new URL(req.url, `http://${req.headers.host || "127.0.0.1"}`);

    if (req.method === "POST" && url.pathname === "/prompt") {
        promptCalls += 1;
        res.writeHead(500, { "Content-Type": "application/json" });
        res.end(JSON.stringify({ error: "Generation forbidden in acceptance test" }));
        return;
    }

    if (req.method === "POST" && url.pathname === "/upload/image") {
        const chunks = [];
        req.on("data", c => chunks.push(c));
        req.on("end", () => {
            const body = Buffer.concat(chunks);
            const ct = req.headers["content-type"] || "";
            const match = ct.match(/boundary=(?:"([^"]+)"|([^;]+))/i);
            const boundary = match ? (match[1] || match[2]) : null;

            const str = body.toString("binary");
            const parts = str.split(`--${boundary}`);
            let filename = "uploaded.png";
            let subfolder = "";
            let fileBuffer = null;

            for (const part of parts) {
                if (part.includes('name="subfolder"')) {
                    const m = part.match(/\r\n\r\n([\s\S]*?)\r\n/);
                    if (m) subfolder = m[1].trim();
                } else if (part.includes('name="image"') || part.includes('filename="')) {
                    const fileMatch = part.match(/filename="([^"]+)"/);
                    if (fileMatch) filename = fileMatch[1];
                    const headerEnd = part.indexOf("\r\n\r\n");
                    if (headerEnd !== -1) {
                        const raw = part.slice(headerEnd + 4, part.lastIndexOf("\r\n"));
                        fileBuffer = Buffer.from(raw, "binary");
                    }
                }
            }

            assert.strictEqual(subfolder, "tegaki_manga_references", "Backend must receive subfolder tegaki_manga_references");
            backendUploadedFiles.set(filename, fileBuffer);

            res.writeHead(200, { "Content-Type": "application/json" });
            res.end(JSON.stringify({
                name: filename,
                subfolder: subfolder,
                type: "input"
            }));
        });
        return;
    }

    if (req.method === "GET" && url.pathname === "/view") {
        const filename = url.searchParams.get("filename");
        const subfolder = url.searchParams.get("subfolder");
        assert.strictEqual(subfolder, "tegaki_manga_references");
        const buf = backendUploadedFiles.get(filename);
        if (!buf) {
            res.writeHead(404, { "Content-Type": "text/plain" });
            res.end("Not Found");
            return;
        }
        let mime = "image/png";
        if (filename.endsWith(".webp")) mime = "image/webp";
        if (filename.endsWith(".jpg") || filename.endsWith(".jpeg")) mime = "image/jpeg";
        res.writeHead(200, { "Content-Type": mime, "Content-Length": buf.length });
        res.end(buf);
        return;
    }

    if (req.method === "GET" && url.pathname === "/queue") {
        res.writeHead(200, { "Content-Type": "application/json" });
        res.end(JSON.stringify({ queue_running: [], queue_pending: [] }));
        return;
    }

    if (req.method === "GET" && url.pathname === "/object_info/TegakiMinimumHandSceneEditor") {
        res.writeHead(200, { "Content-Type": "application/json" });
        res.end(JSON.stringify({ TegakiMinimumHandSceneEditor: { input: {} } }));
        return;
    }

    if (req.method === "GET" && url.pathname === "/tegaki/manga/generation/capabilities") {
        res.writeHead(200, { "Content-Type": "application/json" });
        res.end(JSON.stringify(capabilityCatalog));
        return;
    }

    res.writeHead(404, { "Content-Type": "application/json" });
    res.end(JSON.stringify({ error: "Route not found" }));
});

await new Promise(resolve => fakeBackend.listen(0, "127.0.0.1", resolve));
const backendPort = fakeBackend.address().port;

// 2. Prepare Temp Test Files
const tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), "manga-cast-ref-test-"));
const pngPath = path.join(tmpDir, "hero_reference.png");
const webpPath = path.join(tmpDir, "hero_reference_alt.webp");
fs.writeFileSync(pngPath, TINY_PNG);
fs.writeFileSync(webpPath, TINY_WEBP);

// 3. Start Workspace Server
process.env.MANGA_BACKEND_URL = `http://127.0.0.1:${backendPort}`;
process.env.MANGA_WORKSPACE_PORT = "0";

const { server: workspaceServer } = await import(`../service/manga_workspace_server.mjs?browser_test=${Date.now()}`);
await new Promise(resolve => {
    if (workspaceServer.listening) resolve();
    else workspaceServer.once("listening", resolve);
});
const workspacePort = workspaceServer.address().port;
const WORKSPACE_URL = `http://127.0.0.1:${workspacePort}`;

console.log(`[TEST] Workspace server listening on ${WORKSPACE_URL}`);
console.log(`[TEST] Fake backend listening on http://127.0.0.1:${backendPort}`);

// 4. Launch Playwright
const chromium = resolvePlaywright();
const browser = await chromium.launch({
    headless: true,
    args: ["--no-sandbox", "--disable-setuid-sandbox"]
});

const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
const pageErrors = [];
page.on("pageerror", err => pageErrors.push(err.message));

try {
    // Intercept danbooru catalog
    await page.route("**/data/danbooru_tags.json", async route => {
        await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(FIXTURE_TAGS) });
    });

    // Step 1: Open standalone workspace
    await page.goto(WORKSPACE_URL, { waitUntil: "networkidle", timeout: 10000 });
    await page.waitForFunction(() => Boolean(window.__tegakiManga?.store));
    const initCastCount = await page.textContent("#count-cast");
    assert.strictEqual(initCastCount.trim(), "0", "Initial CAST count must be 0");
    console.log("✓ Step 1 PASS: Opened standalone workspace with 0 CAST members");

    // Step 2: Add CAST member via #btn-add-cast
    await page.click("#btn-add-cast");
    await page.waitForFunction(() => (document.getElementById("count-cast")?.textContent.trim() === "1"));
    const castIdLabel = (await page.textContent("#cast-edit-id-label")).trim();
    assert.ok(castIdLabel.length > 0, "Selected CAST has valid ID");
    console.log(`✓ Step 2 PASS: Added CAST member ${castIdLabel}`);

    // Step 3: Check initial reference UI state
    const initReadout = (await page.textContent("#cast-reference-readout")).trim();
    assert.strictEqual(initReadout, "(none)", "Initial reference readout must be (none)");
    const initThumbDisplay = await page.$eval("#cast-reference-thumbnail", el => el.style.display);
    assert.strictEqual(initThumbDisplay, "none", "Thumbnail preview hidden initially");
    const initBtnAddText = (await page.textContent("#btn-add-cast-reference")).trim();
    assert.strictEqual(initBtnAddText, "+ Reference", "Initial button text is + Reference");
    const initBtnClearDisplay = await page.$eval("#btn-clear-cast-reference", el => el.style.display);
    assert.strictEqual(initBtnClearDisplay, "none", "Clear button hidden initially");
    console.log("✓ Step 3 PASS: Initial CAST reference UI correctly shows (none)");

    // Step 4: Ingest PNG reference via file input
    await page.setInputFiles("#file-cast-reference", pngPath);
    await page.waitForFunction(() => {
        const readout = document.getElementById("cast-reference-readout")?.textContent || "";
        return readout.startsWith("tegaki_manga_references/ref_") && readout.endsWith(".png");
    }, { timeout: 5000 });

    const pngRefText = (await page.textContent("#cast-reference-readout")).trim();
    console.log(`✓ Step 4 PASS: Ingested PNG reference: ${pngRefText}`);

    // Step 5: Verify thumbnail preview rendered with naturalWidth > 0
    await page.waitForFunction(() => {
        const thumb = document.getElementById("cast-reference-thumbnail");
        return thumb && thumb.complete && thumb.naturalWidth > 0 && thumb.style.display !== "none";
    }, { timeout: 5000 });

    const btnAddAfterPng = (await page.textContent("#btn-add-cast-reference")).trim();
    assert.strictEqual(btnAddAfterPng, "Replace", "Button text updated to Replace");
    const btnClearAfterPng = await page.$eval("#btn-clear-cast-reference", el => el.style.display);
    assert.notStrictEqual(btnClearAfterPng, "none", "Clear button is now visible");
    console.log("✓ Step 5 PASS: Thumbnail preview rendered with naturalWidth > 0");

    // Step 6: Export document JSON -> verify reference_asset is serialized
    await page.click("#btn-export-json");
    await page.waitForTimeout(150);
    const exportedJsonStr = await page.$eval("#modal-json-text", el => el.value);
    const exportedDoc = JSON.parse(exportedJsonStr);
    assert.strictEqual(exportedDoc.pages[0].cast.length, 1, "Exported document has 1 CAST entry");
    assert.strictEqual(exportedDoc.pages[0].cast[0].reference_asset, pngRefText, "reference_asset matches in exported JSON");
    await page.click("#btn-close-modal");
    await page.waitForTimeout(100);
    console.log("✓ Step 6 PASS: Exported document contains canonical reference_asset");

    // Step 7: Reset default doc and re-import exported JSON
    await page.click("#btn-reset-default");
    await page.waitForTimeout(100);
    assert.strictEqual((await page.textContent("#count-cast")).trim(), "0", "CAST count is 0 after reset");

    await page.click("#btn-load-json");
    await page.waitForTimeout(100);
    await page.$eval("#modal-json-text", (el, val) => el.value = val, exportedJsonStr);
    await page.click("#btn-modal-action");
    await page.waitForTimeout(200);

    assert.strictEqual((await page.textContent("#count-cast")).trim(), "1", "CAST count is 1 after re-import");
    // Click CAST member in list to inspect
    await page.click("#list-cast .list-item");
    await page.waitForTimeout(100);
    const restoredRefText = (await page.textContent("#cast-reference-readout")).trim();
    assert.strictEqual(restoredRefText, pngRefText, "reference_asset preserved across re-import");
    console.log("✓ Step 7 PASS: Re-import roundtrip verified reference_asset preservation");

    // Step 8: Replace reference asset with WEBP image
    await page.setInputFiles("#file-cast-reference", webpPath);
    await page.waitForFunction((prevRef) => {
        const readout = document.getElementById("cast-reference-readout")?.textContent || "";
        return readout.startsWith("tegaki_manga_references/ref_") && readout.endsWith(".webp") && readout !== prevRef;
    }, { timeout: 5000 }, pngRefText);

    const webpRefText = (await page.textContent("#cast-reference-readout")).trim();
    assert.ok(webpRefText.endsWith(".webp"), "Reference asset updated to .webp");
    assert.notStrictEqual(webpRefText, pngRefText, "Reference asset changed to new hash");
    console.log(`✓ Step 8 PASS: Replaced reference asset with WEBP: ${webpRefText}`);

    // Step 9: Clear reference asset
    await page.click("#btn-clear-cast-reference");
    await page.waitForTimeout(100);

    const clearedReadout = (await page.textContent("#cast-reference-readout")).trim();
    assert.strictEqual(clearedReadout, "(none)", "Readout returned to (none) after clear");
    const clearedThumbDisplay = await page.$eval("#cast-reference-thumbnail", el => el.style.display);
    assert.strictEqual(clearedThumbDisplay, "none", "Thumbnail hidden after clear");
    const clearedBtnAdd = (await page.textContent("#btn-add-cast-reference")).trim();
    assert.strictEqual(clearedBtnAdd, "+ Reference", "Button returned to + Reference");
    const clearedBtnClear = await page.$eval("#btn-clear-cast-reference", el => el.style.display);
    assert.strictEqual(clearedBtnClear, "none", "Clear button hidden after clear");

    const storeCastRef = await page.evaluate(() => window.__tegakiManga.store.getPage().cast[0].reference_asset);
    assert.strictEqual(storeCastRef, null, "Store CAST reference_asset is null after clear");
    console.log("✓ Step 9 PASS: Clear reference asset resets UI and store to null");

    // Step 10: Invariants & Regressions
    // 10A: Scene creation works
    const countScenesBefore = await page.evaluate(() => window.__tegakiManga.store.getPage().scenes.length);
    await page.click("#scene-tool-add");
    await page.waitForTimeout(100);
    const countScenesAfter = await page.evaluate(() => window.__tegakiManga.store.getPage().scenes.length);
    assert.strictEqual(countScenesAfter, countScenesBefore + 1, "Scene created via tool");
    console.log("✓ Step 10A PASS: Scene creation operational");

    // 10B: Character placement works
    await page.click("#list-cast .list-item");
    await page.waitForTimeout(100);
    await page.click("#btn-place-character");
    await page.waitForTimeout(100);
    const countInstances = (await page.textContent("#count-instances")).trim();
    assert.strictEqual(countInstances, "1", "Character placed into scene");
    console.log("✓ Step 10B PASS: Character placement operational");

    // 10C: Autocomplete is operational
    const autocompleteReady = await page.evaluate(() => {
        const input = document.querySelector("#scene-composer-prompt");
        return input && input.dataset.tagAutocompleteState === "ready";
    });
    assert.ok(autocompleteReady, "Autocomplete is ready on prompt surface");
    console.log("✓ Step 10C PASS: Autocomplete intact");

    // Step 11: Generation invariants
    assert.strictEqual(promptCalls, 0, "Zero /prompt calls executed");
    assert.strictEqual(pageErrors.length, 0, `Zero page errors: ${pageErrors.join(", ")}`);
    console.log("✓ Step 11 PASS: Zero /prompt calls and zero page errors");

    console.log("==================================================");
    console.log("ALL BROWSER CAST REFERENCE DATA TESTS PASSED (DATA1)");
    console.log("==================================================");

} finally {
    await browser.close();
    workspaceServer.close();
    fakeBackend.close();
    try {
        fs.rmSync(tmpDir, { recursive: true, force: true });
    } catch (e) {}
}
