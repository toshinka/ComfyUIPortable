/**
 * verify_m1b_browser.mjs — Playwright Real Browser Gate Suite (M1B)
 * =================================================================
 * Verifies all 17 steps (A through Q) from Card Section 25:
 * A. page loads standalone
 * B. add a Scene
 * C. edit its prompt
 * D. move/resize Scene
 * E. add at least two CAST entries
 * F. select explicit CAST
 * G. place Character into Scene
 * H. move/resize Character
 * I. edit acting prompt
 * J. attempt referenced CAST deletion -> visibly rejected
 * K. export JSON -> edits present
 * L. re-import -> edits preserved
 * M. session selection changes -> exported durable JSON unchanged except intended edits
 * N. backend Manga-ready detection still works
 * O. prepare Standard/no-Guide succeeds
 * P. queue remains known IDLE
 * Q. real generations = 0
 */

import assert from "node:assert";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { createRequire } from "node:module";
import fs from "node:fs";
import { execSync } from "node:child_process";

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

console.log(`--- Running verify_m1b_browser.mjs against ${WORKSPACE_URL} (Backend: ${BACKEND_URL}) ---`);

const browser = await chromium.launch({
    headless: true,
    args: ["--no-sandbox", "--disable-setuid-sandbox"]
});

const page = await browser.newPage();

try {
    // ----------------------------------------------------
    // Step A: Page loads standalone
    // ----------------------------------------------------
    await page.goto(WORKSPACE_URL, { waitUntil: "networkidle", timeout: 10000 });
    const litegraphCanvas = await page.$("canvas.graph-canvas");
    assert.strictEqual(litegraphCanvas, null, "Step A: ComfyUI LiteGraph canvas must NOT be present");
    const appBrand = await page.textContent(".brand-title");
    assert.strictEqual(appBrand.trim(), "TEGAKI Manga", "Step A: Standalone brand must be visible");
    const initScenes = await page.textContent("#count-scenes");
    assert.strictEqual(initScenes.trim(), "2", "Step A: Default document has 2 scenes");
    console.log("✓ Step A PASS: Page loads standalone without LiteGraph");

    // ----------------------------------------------------
    // Step B: Add a Scene
    // ----------------------------------------------------
    await page.click("#btn-add-scene");
    await page.waitForTimeout(200);
    const countAfterAdd = await page.textContent("#count-scenes");
    assert.strictEqual(countAfterAdd.trim(), "3", "Step B: Scene count must now be 3");
    console.log("✓ Step B PASS: Add Scene successful (count: 3)");

    // ----------------------------------------------------
    // Step C: Edit its prompt
    // ----------------------------------------------------
    await page.fill("#input-scene-name", "Scene 3 Added");
    await page.fill("#input-scene-prompt", "night city skyline with glowing neon billboards");
    await page.fill("#input-scene-negative", "daylight, blurry");
    await page.waitForTimeout(100);

    const checkPrompt = await page.evaluate(() => {
        const sc = window.__tegakiManga.store.getPage().scenes.find(s => s.name === "Scene 3 Added");
        return sc ? { name: sc.name, prompt: sc.prompt, negative: sc.negative_prompt } : null;
    });
    assert.ok(checkPrompt, "Step C: Edited scene found in document");
    assert.strictEqual(checkPrompt.prompt, "night city skyline with glowing neon billboards");
    console.log("✓ Step C PASS: Edit Scene prompt successful");

    // ----------------------------------------------------
    // Step D: Move / resize Scene
    // ----------------------------------------------------
    const geomBefore = await page.evaluate(() => {
        const sc = window.__tegakiManga.store.getPage().scenes.find(s => s.name === "Scene 3 Added");
        return { ...sc.area };
    });

    await page.click("#btn-scene-move-right");
    await page.click("#btn-scene-move-down");
    await page.click("#btn-scene-grow-w");
    await page.waitForTimeout(100);

    const geomAfter = await page.evaluate(() => {
        const sc = window.__tegakiManga.store.getPage().scenes.find(s => s.name === "Scene 3 Added");
        return { ...sc.area };
    });

    assert.ok(geomAfter.x > geomBefore.x, "Step D: Scene moved right");
    assert.ok(geomAfter.y > geomBefore.y, "Step D: Scene moved down");
    assert.ok(geomAfter.w > geomBefore.w, "Step D: Scene width expanded");
    console.log("✓ Step D PASS: Move and resize Scene successful");

    // ----------------------------------------------------
    // Step E: Add at least two CAST entries
    // ----------------------------------------------------
    await page.click("#btn-add-cast");
    await page.waitForTimeout(100);
    await page.fill("#input-cast-name", "Hero Cyber");
    await page.fill("#input-cast-prompt", "cyborg hero in armored jacket");

    await page.click("#btn-add-cast");
    await page.waitForTimeout(100);
    await page.fill("#input-cast-name", "Villain Net");
    await page.fill("#input-cast-prompt", "rogue hacker in hooded trench coat");
    await page.waitForTimeout(100);

    const castCount = await page.textContent("#count-cast");
    assert.strictEqual(castCount.trim(), "2", "Step E: CAST count must be 2");
    console.log("✓ Step E PASS: Add two CAST entries successful");

    // ----------------------------------------------------
    // Step F: Select explicit CAST
    // ----------------------------------------------------
    // Select first CAST (Hero Cyber) in list
    const firstCastEl = await page.$("#list-cast .list-item:first-child");
    await firstCastEl.click();
    await page.waitForTimeout(100);

    const selCastId = await page.evaluate(() => window.__tegakiManga.session.selectedCastId);
    const heroCastId = await page.evaluate(() => {
        const c = window.__tegakiManga.store.getPage().cast.find(x => x.display_name === "Hero Cyber");
        return c?.cast_id;
    });
    assert.strictEqual(selCastId, heroCastId, "Step F: Selected CAST matches Hero Cyber");
    console.log(`✓ Step F PASS: Explicit CAST selected (${selCastId})`);

    // ----------------------------------------------------
    // Step G: Place Character into Scene
    // ----------------------------------------------------
    // Target scene is Scene 3 Added
    const scene3Id = await page.evaluate(() => {
        const sc = window.__tegakiManga.store.getPage().scenes.find(s => s.name === "Scene 3 Added");
        return sc?.scene_id;
    });
    await page.evaluate((scId) => window.__tegakiManga.session.selectScene(scId), scene3Id);

    await page.click("#btn-place-character");
    await page.waitForTimeout(200);

    const instCount = await page.textContent("#count-instances");
    assert.strictEqual(instCount.trim(), "1", "Step G: Instance count must be 1");

    const instData = await page.evaluate(() => {
        const pageObj = window.__tegakiManga.store.getPage();
        const inst = pageObj.character_instances[0];
        const sc = pageObj.scenes.find(s => s.scene_id === inst.scene_id);
        return { inst, sceneInputMode: sc.input_mode };
    });
    assert.strictEqual(instData.inst.cast_id, heroCastId, "Step G: Placed instance references Hero Cyber");
    assert.strictEqual(instData.sceneInputMode, "cast", "Step G: Parent scene input_mode switched to cast");
    console.log("✓ Step G PASS: Character placed into Scene with correct cast_id and input_mode");

    // ----------------------------------------------------
    // Step H: Move / resize Character
    // ----------------------------------------------------
    const charGeomBefore = { ...instData.inst.area };
    await page.click("#btn-char-move-right");
    await page.click("#btn-char-grow");
    await page.waitForTimeout(100);

    const charGeomAfter = await page.evaluate(() => {
        return { ...window.__tegakiManga.store.getPage().character_instances[0].area };
    });
    assert.ok(charGeomAfter.x >= charGeomBefore.x, "Step H: Character moved");
    assert.ok(charGeomAfter.w > charGeomBefore.w, "Step H: Character resized");
    console.log("✓ Step H PASS: Move / resize Character successful");

    // ----------------------------------------------------
    // Step I: Edit acting prompt
    // ----------------------------------------------------
    await page.fill("#input-instance-acting-prompt", "brandishing energy blade ready to strike");
    await page.waitForTimeout(100);

    const actCheck = await page.evaluate(() => {
        return window.__tegakiManga.store.getPage().character_instances[0].acting_prompt;
    });
    assert.strictEqual(actCheck, "brandishing energy blade ready to strike", "Step I: Acting prompt updated");
    console.log("✓ Step I PASS: Edit acting prompt successful");

    // ----------------------------------------------------
    // Step J: Attempt referenced CAST deletion -> visibly rejected
    // ----------------------------------------------------
    // Select Hero Cyber
    await page.click("#list-cast .list-item:first-child");
    await page.waitForTimeout(100);

    // Click delete cast
    await page.click("#btn-delete-cast");
    await page.waitForTimeout(100);

    // Verify visibly rejected via error banner
    const isErrorVisible = await page.$eval("#cast-error-msg", el => el.classList.contains("visible"));
    const errorText = await page.textContent("#cast-error-msg");
    assert.strictEqual(isErrorVisible, true, "Step J: Error alert must be visibly displayed");
    assert.ok(errorText.includes("referenced by active character instances"), `Step J: Error must state reference guard: ${errorText}`);

    // Verify CAST was NOT deleted
    const castCountAfterAttempt = await page.textContent("#count-cast");
    assert.strictEqual(castCountAfterAttempt.trim(), "2", "Step J: Referenced CAST delete must be blocked");
    console.log("✓ Step J PASS: Attempted referenced CAST deletion visibly rejected");

    // ----------------------------------------------------
    // Step K: Export JSON -> edits present
    // ----------------------------------------------------
    await page.click("#btn-export-json");
    await page.waitForSelector("#export-modal", { state: "visible" });
    const exportedRaw = await page.inputValue("#modal-json-text");
    const exportedDoc = JSON.parse(exportedRaw);

    assert.strictEqual(exportedDoc.schema_id, "TEGAKI_AUTHORING_DOCUMENT");
    assert.strictEqual(exportedDoc.schema_version, "1.0.0");
    const expPage = exportedDoc.pages[0];
    assert.strictEqual(expPage.scenes.length, 3, "Step K: Export contains 3 scenes");
    assert.strictEqual(expPage.cast.length, 2, "Step K: Export contains 2 cast entries");
    assert.strictEqual(expPage.character_instances.length, 1, "Step K: Export contains 1 character instance");

    const sc3Export = expPage.scenes.find(s => s.name === "Scene 3 Added");
    assert.ok(sc3Export, "Step K: Scene 3 Added present in export");
    assert.strictEqual(sc3Export.prompt, "night city skyline with glowing neon billboards");

    const heroExport = expPage.cast.find(c => c.display_name === "Hero Cyber");
    assert.ok(heroExport, "Step K: Hero Cyber present in export");

    const instExport = expPage.character_instances[0];
    assert.strictEqual(instExport.acting_prompt, "brandishing energy blade ready to strike");

    // Verify session keys excluded
    assert.strictEqual("selectedSceneId" in exportedDoc, false);
    assert.strictEqual("selectedCastId" in exportedDoc, false);

    await page.click("#btn-close-modal");
    await page.waitForSelector("#export-modal", { state: "hidden" });
    console.log("✓ Step K PASS: Export JSON contains all durable edits and zero session keys");

    // ----------------------------------------------------
    // Step L: Re-import -> edits preserved
    // ----------------------------------------------------
    // Reset to default first
    await page.click("#btn-reset-default");
    await page.waitForTimeout(200);
    assert.strictEqual(await page.textContent("#count-scenes"), "2");
    assert.strictEqual(await page.textContent("#count-cast"), "0");

    // Open import modal
    await page.click("#btn-load-json");
    await page.waitForSelector("#export-modal", { state: "visible" });
    await page.fill("#modal-json-text", exportedRaw);
    await page.click("#btn-modal-action");
    await page.waitForTimeout(200);

    // Verify all edits preserved
    assert.strictEqual(await page.textContent("#count-scenes"), "3");
    assert.strictEqual(await page.textContent("#count-cast"), "2");
    assert.strictEqual(await page.textContent("#count-instances"), "1");

    const reimportedCheck = await page.evaluate(() => {
        const p = window.__tegakiManga.store.getPage();
        return {
            scene3Prompt: p.scenes.find(s => s.name === "Scene 3 Added")?.prompt,
            heroName: p.cast.find(c => c.display_name === "Hero Cyber")?.display_name,
            instPrompt: p.character_instances[0]?.acting_prompt
        };
    });
    assert.strictEqual(reimportedCheck.scene3Prompt, "night city skyline with glowing neon billboards");
    assert.strictEqual(reimportedCheck.heroName, "Hero Cyber");
    assert.strictEqual(reimportedCheck.instPrompt, "brandishing energy blade ready to strike");
    console.log("✓ Step L PASS: Re-import preserves all edits");

    // ----------------------------------------------------
    // Step M: Session selection changes -> exported durable JSON unchanged
    // ----------------------------------------------------
    const beforeSessionSwitch = await page.evaluate(() => window.__tegakiManga.store.exportJson(false));

    await page.click("#tab-frames");
    await page.waitForTimeout(50);
    await page.click("#tab-guides");
    await page.waitForTimeout(50);
    await page.click("#tab-cast");
    await page.waitForTimeout(50);
    await page.click("#tab-scenes");
    await page.waitForTimeout(50);

    const afterSessionSwitch = await page.evaluate(() => window.__tegakiManga.store.exportJson(false));
    assert.strictEqual(beforeSessionSwitch, afterSessionSwitch, "Step M: Session selection must not alter durable JSON");
    console.log("✓ Step M PASS: Session selection changes do not mutate exported durable JSON");

    // ----------------------------------------------------
    // Step N: Backend Manga-ready detection still works
    // ----------------------------------------------------
    await page.fill("#backend-url-input", BACKEND_URL);
    await page.click("#btn-check-backend");
    await page.waitForTimeout(1000);

    const backendStatus = await page.textContent("#backend-status-text");
    console.log(`Backend status: ${backendStatus.trim()}`);
    assert.strictEqual(backendStatus.trim(), "MANGA READY", "Step N: Backend must be detected as MANGA READY");
    console.log("✓ Step N PASS: Backend Manga-ready detection still works");

    // ----------------------------------------------------
    // Step O: Prepare Standard/no-Guide succeeds
    // ----------------------------------------------------
    await page.click("#btn-prepare-draft");
    await page.waitForTimeout(1500);

    const prepareFeedback = await page.textContent("#prepare-feedback");
    console.log(`Prepare feedback: ${prepareFeedback.trim()}`);
    assert.ok(prepareFeedback.includes("Prepared route: STANDARD_NO_GUIDE"), "Step O: Route must be STANDARD_NO_GUIDE");
    console.log("✓ Step O PASS: Prepare Standard/no-Guide succeeds");

    // ----------------------------------------------------
    // Step P: Queue remains known IDLE
    // ----------------------------------------------------
    assert.ok(prepareFeedback.includes("Queue IDLE"), "Step P: Queue must remain known IDLE");
    console.log("✓ Step P PASS: Queue remains known IDLE");

    // ----------------------------------------------------
    // Step Q: Real generations = 0
    // ----------------------------------------------------
    const queueData = await page.evaluate(async () => {
        const q = await window.__tegakiManga.client.getQueue();
        return {
            running: q.queue_running?.length || 0,
            pending: q.queue_pending?.length || 0
        };
    });
    assert.strictEqual(queueData.running, 0, "Step Q: Zero running generations");
    assert.strictEqual(queueData.pending, 0, "Step Q: Zero pending generations");
    console.log("✓ Step Q PASS: Real generations = 0");

    console.log("");
    console.log("==================================================");
    console.log("ALL 17 REAL BROWSER GATES PASSED (A through Q) (M1B)");
    console.log("==================================================");

} finally {
    await browser.close();
}
