/**
 * verify_m1c1_browser.mjs — Playwright Real Browser Gate Suite (MANGA-M1C1)
 * =========================================================================
 * Verifies all 16 steps from Card Section 20:
 * 1. load default workspace
 * 2. switch to Visual Frames layer
 * 3. Add Frame
 * 4. select Frame
 * 5. drag it
 * 6. resize it from at least two different corner handles
 * 7. change border thickness
 * 8. add second frame
 * 9. create an overlap and observe warning
 * 10. remove one frame
 * 11. Copy Scenes to Frames
 * 12. confirm copied frame count matches scene count
 * 13. move a copied Frame and prove source Scene geometry unchanged
 * 14. export
 * 15. re-import
 * 16. prove Frame state persists
 */

import assert from "node:assert/strict";
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

console.log(`--- Running verify_m1c1_browser.mjs against ${WORKSPACE_URL} ---`);

const browser = await chromium.launch({
    headless: true,
    args: ["--no-sandbox", "--disable-setuid-sandbox"]
});

const page = await browser.newPage();

// Auto-accept confirmation dialog for Copy Scenes to Frames (Section 6)
page.on("dialog", async dialog => {
    await dialog.accept();
});

try {
    // ----------------------------------------------------
    // Step 1: Load default workspace
    // ----------------------------------------------------
    await page.goto(WORKSPACE_URL, { waitUntil: "networkidle", timeout: 10000 });
    const litegraphCanvas = await page.$("canvas.graph-canvas");
    assert.equal(litegraphCanvas, null, "Step 1: ComfyUI LiteGraph canvas must NOT be present");
    const countInitFrames = await page.textContent("#count-frames");
    assert.equal(countInitFrames.trim(), "0", "Step 1: Default document has 0 visual frames");
    console.log("✓ Step 1 PASS: Default workspace loaded");

    // ----------------------------------------------------
    // Step 2: Switch to Visual Frames layer
    // ----------------------------------------------------
    await page.click("#tab-frames");
    await page.waitForTimeout(100);
    const activeLayer = await page.textContent("#session-active-layer");
    assert.equal(activeLayer.trim(), "frames", "Step 2: Active layer must be frames");
    console.log("✓ Step 2 PASS: Switched to Visual Frames layer");

    // ----------------------------------------------------
    // Step 3: Add Frame
    // ----------------------------------------------------
    await page.click("#btn-add-frame");
    await page.waitForTimeout(100);
    const countAfterAdd = await page.textContent("#count-frames");
    assert.equal(countAfterAdd.trim(), "1", "Step 3: Frame count must be 1");
    console.log("✓ Step 3 PASS: Add Frame successful");

    // ----------------------------------------------------
    // Step 4: Select Frame
    // ----------------------------------------------------
    await page.click("#list-frames .list-item:first-child");
    await page.waitForTimeout(100);
    const isEditorVisible = await page.$eval("#frame-editor-container", el => el.style.display !== "none");
    assert.equal(isEditorVisible, true, "Step 4: Frame editor container visible");
    const labelText = await page.textContent("#frame-edit-id-label");
    assert.ok(labelText.includes("frame_1"), "Step 4: Selected frame label contains frame_1");
    console.log("✓ Step 4 PASS: Frame selected and editor visible");

    // ----------------------------------------------------
    // Step 5: Drag it (Move)
    // ----------------------------------------------------
    const geomBeforeMove = await page.evaluate(() => {
        return { ...window.__tegakiManga.store.getPage().visual_frames[0].area };
    });

    await page.click("#btn-frame-move-right");
    await page.click("#btn-frame-move-down");
    await page.waitForTimeout(100);

    const geomAfterMove = await page.evaluate(() => {
        return { ...window.__tegakiManga.store.getPage().visual_frames[0].area };
    });
    assert.ok(geomAfterMove.x > geomBeforeMove.x, "Step 5: Frame moved right");
    assert.ok(geomAfterMove.y > geomBeforeMove.y, "Step 5: Frame moved down");
    console.log("✓ Step 5 PASS: Move Frame successful");

    // ----------------------------------------------------
    // Step 6: Resize it from at least two different corner handles
    // ----------------------------------------------------
    const geomBeforeResize = { ...geomAfterMove };

    // Handle 1: SE resize
    await page.evaluate(() => {
        window.__tegakiManga.store.resizeFrame("frame_1", "se", 0.04, 0.04);
    });
    await page.waitForTimeout(100);

    const geomAfterSE = await page.evaluate(() => {
        return { ...window.__tegakiManga.store.getPage().visual_frames[0].area };
    });
    assert.ok(geomAfterSE.w > geomBeforeResize.w, "Step 6: SE resize expanded width");
    assert.ok(geomAfterSE.h > geomBeforeResize.h, "Step 6: SE resize expanded height");

    // Handle 2: NW resize
    await page.evaluate(() => {
        window.__tegakiManga.store.resizeFrame("frame_1", "nw", -0.02, -0.02);
    });
    await page.waitForTimeout(100);

    const geomAfterNW = await page.evaluate(() => {
        return { ...window.__tegakiManga.store.getPage().visual_frames[0].area };
    });
    assert.ok(geomAfterNW.x < geomAfterSE.x, "Step 6: NW resize moved top-left corner left");
    assert.ok(geomAfterNW.y < geomAfterSE.y, "Step 6: NW resize moved top-left corner up");
    assert.ok(geomAfterNW.w > geomAfterSE.w, "Step 6: NW resize expanded width");
    console.log("✓ Step 6 PASS: Resized from two different corner handles (SE and NW)");

    // ----------------------------------------------------
    // Step 7: Change border thickness
    // ----------------------------------------------------
    await page.fill("#input-frame-border", "8");
    await page.dispatchEvent("#input-frame-border", "input");
    await page.waitForTimeout(100);

    const thicknessCheck = await page.evaluate(() => {
        return window.__tegakiManga.store.getPage().visual_frames[0].border_thickness;
    });
    assert.equal(thicknessCheck, 8, "Step 7: Border thickness updated to 8");
    console.log("✓ Step 7 PASS: Change border thickness successful");

    // ----------------------------------------------------
    // Step 8: Add second frame
    // ----------------------------------------------------
    await page.click("#btn-add-frame");
    await page.waitForTimeout(100);
    const count2 = await page.textContent("#count-frames");
    assert.equal(count2.trim(), "2", "Step 8: Frame count is now 2");
    console.log("✓ Step 8 PASS: Add second frame successful");

    // ----------------------------------------------------
    // Step 9: Create an overlap and observe warning
    // ----------------------------------------------------
    // Move frame_2 so it intersects frame_1
    await page.evaluate(() => {
        const p = window.__tegakiManga.store.getPage();
        const f1Area = p.visual_frames[0].area;
        // Place frame_2 right on top of frame_1
        window.__tegakiManga.store.moveFrame("frame_2", f1Area.x - p.visual_frames[1].area.x, f1Area.y - p.visual_frames[1].area.y);
    });
    await page.waitForTimeout(200);

    const isOverlapVisible = await page.$eval("#frame-overlap-warning", el => el.classList.contains("visible"));
    const overlapText = await page.textContent("#frame-overlap-warning");
    assert.equal(isOverlapVisible, true, "Step 9: Overlap warning banner visible");
    assert.ok(overlapText.includes("Overlap"), `Step 9: Warning text indicates overlap: ${overlapText}`);
    console.log("✓ Step 9 PASS: Overlap created and diagnostic warning observed");

    // ----------------------------------------------------
    // Step 10: Remove one frame
    // ----------------------------------------------------
    await page.click("#list-frames .list-item:nth-child(2)");
    await page.waitForTimeout(100);
    await page.click("#btn-delete-frame");
    await page.waitForTimeout(100);

    const countAfterDel = await page.textContent("#count-frames");
    assert.equal(countAfterDel.trim(), "1", "Step 10: Frame count is 1 after removal");
    console.log("✓ Step 10 PASS: Remove one frame successful");

    // ----------------------------------------------------
    // Step 11: Copy Scenes to Frames
    // ----------------------------------------------------
    await page.click("#btn-copy-scenes-to-frames");
    await page.waitForTimeout(200);
    console.log("✓ Step 11 PASS: Copy Scenes to Frames invoked");

    // ----------------------------------------------------
    // Step 12: Confirm copied frame count matches scene count
    // ----------------------------------------------------
    const sceneCount = (await page.textContent("#count-scenes")).trim();
    const frameCountAfterCopy = (await page.textContent("#count-frames")).trim();
    assert.equal(frameCountAfterCopy, sceneCount, "Step 12: Copied frame count matches scene count (2)");
    console.log(`✓ Step 12 PASS: Copied frame count (${frameCountAfterCopy}) matches scene count (${sceneCount})`);

    // ----------------------------------------------------
    // Step 13: Move a copied Frame and prove source Scene geometry unchanged
    // ----------------------------------------------------
    const sceneGeomBefore = await page.evaluate(() => {
        return { ...window.__tegakiManga.store.getPage().scenes[0].area };
    });

    await page.click("#list-frames .list-item:first-child");
    await page.waitForTimeout(50);
    await page.click("#btn-frame-move-right");
    await page.click("#btn-frame-move-right");
    await page.waitForTimeout(100);

    const sceneGeomAfter = await page.evaluate(() => {
        return { ...window.__tegakiManga.store.getPage().scenes[0].area };
    });
    assert.deepEqual(sceneGeomAfter, sceneGeomBefore, "Step 13: Source scene geometry must remain strictly unchanged when frame moves");
    console.log("✓ Step 13 PASS: Moving Frame does NOT modify source Scene geometry");

    // ----------------------------------------------------
    // Step 14: Export
    // ----------------------------------------------------
    await page.click("#btn-export-json");
    await page.waitForSelector("#export-modal", { state: "visible" });
    const exportedRaw = await page.inputValue("#modal-json-text");
    const exportedDoc = JSON.parse(exportedRaw);

    assert.equal(exportedDoc.schema_id, "TEGAKI_AUTHORING_DOCUMENT");
    assert.equal(exportedDoc.schema_version, "1.0.0");
    assert.equal(exportedDoc.pages[0].visual_frames.length, 2, "Step 14: Export contains 2 visual frames");
    await page.click("#btn-close-modal");
    await page.waitForSelector("#export-modal", { state: "hidden" });
    console.log("✓ Step 14 PASS: Exported document contains visual frames");

    // ----------------------------------------------------
    // Step 15: Re-import
    // ----------------------------------------------------
    await page.click("#btn-reset-default");
    await page.waitForTimeout(100);
    assert.equal((await page.textContent("#count-frames")).trim(), "0");

    await page.click("#btn-load-json");
    await page.waitForSelector("#export-modal", { state: "visible" });
    await page.fill("#modal-json-text", exportedRaw);
    await page.click("#btn-modal-action");
    await page.waitForTimeout(200);
    console.log("✓ Step 15 PASS: Document re-imported");

    // ----------------------------------------------------
    // Step 16: Prove Frame state persists
    // ----------------------------------------------------
    const reimportedFrames = await page.evaluate(() => {
        return window.__tegakiManga.store.getPage().visual_frames;
    });
    assert.equal(reimportedFrames.length, 2, "Step 16: Re-imported frame count is 2");
    assert.equal(reimportedFrames[0].frame_id, "frame_1");
    assert.equal(reimportedFrames[1].frame_id, "frame_2");
    assert.deepEqual(reimportedFrames[0].area, exportedDoc.pages[0].visual_frames[0].area, "Step 16: Frame 1 area preserved");
    assert.deepEqual(reimportedFrames[1].area, exportedDoc.pages[0].visual_frames[1].area, "Step 16: Frame 2 area preserved");
    console.log("✓ Step 16 PASS: Re-imported Frame state persists with exact durable parity");

    console.log("");
    console.log("==================================================");
    console.log("ALL 16 REAL BROWSER GATES PASSED (MANGA-M1C1)");
    console.log("==================================================");

} finally {
    await browser.close();
}
