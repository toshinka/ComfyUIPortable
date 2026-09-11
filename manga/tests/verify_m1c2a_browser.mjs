/**
 * verify_m1c2a_browser.mjs — Playwright Real Browser Gate Suite (MANGA-M1C2A)
 * ===========================================================================
 * Verifies:
 * Part 1: Guide / Figure Direct Authoring Suite (Card Section 32)
 * 1. Load Rich Fixture
 * 2. Switch to Guides layer
 * 3. Select Guide
 * 4. Select existing Figure
 * 5. Actual canvas pointer-drag Figure
 * 6. Actual pointer resize via at least two Figure corner handles (SE and NW)
 * 7. Add Figure
 * 8. Associate new Figure to an available Character Instance
 * 9. Attempt duplicate association -> visible rejection
 * 10. Unassign
 * 11. Toggle Guide disabled/enabled
 * 12. Remove one Figure
 * 13. Export
 * 14. Re-import
 * 15. Verify Guide/Figure durable data survives
 *
 * Part 2: M1C1 Frame Pointer Regression (Card Section 27 & 34)
 * - Switch to Frames layer
 * - Frame move via actual canvas mousedown, mousemove, mouseup
 * - Frame resize via actual canvas corner handle SE (mousedown, mousemove, mouseup)
 * - Frame resize via actual canvas corner handle NW/SW/NE (mousedown, mousemove, mouseup)
 * - Store only read to assert resulting geometry change
 * - Zero backend queueing, 0 real generations.
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

    throw new Error("Cannot resolve playwright in current runtime environment");
}

const chromium = resolvePlaywright();
const WORKSPACE_URL = process.env.MANGA_WORKSPACE_URL || "http://127.0.0.1:8191";

console.log(`--- Running verify_m1c2a_browser.mjs against ${WORKSPACE_URL} ---`);

const browser = await chromium.launch({
    headless: true,
    args: ["--no-sandbox", "--disable-setuid-sandbox"]
});

const page = await browser.newPage();

try {
    // ----------------------------------------------------
    // Step 1: Load Rich Fixture
    // ----------------------------------------------------
    await page.goto(WORKSPACE_URL, { waitUntil: "networkidle", timeout: 10000 });
    await page.click("#btn-load-fixture");
    await page.waitForTimeout(100);
    const countInitGuides = await page.textContent("#count-guides");
    assert.equal(countInitGuides.trim(), "1", "Step 1: Rich fixture must have 1 guide");
    console.log("✓ Step 1 PASS: Loaded rich fixture");

    // ----------------------------------------------------
    // Step 2: Switch to Guides layer
    // ----------------------------------------------------
    await page.click("#tab-guides");
    await page.waitForTimeout(100);
    const activeLayer = await page.textContent("#session-active-layer");
    assert.equal(activeLayer.trim(), "guides", "Step 2: Active layer must be guides");
    console.log("✓ Step 2 PASS: Switched to Guides layer");

    // ----------------------------------------------------
    // Step 3: Select Guide
    // ----------------------------------------------------
    await page.click("#list-guides .list-item:first-child");
    await page.waitForTimeout(100);
    const isGuideEditorVisible = await page.$eval("#guide-editor-container", el => el.style.display !== "none");
    assert.equal(isGuideEditorVisible, true, "Step 3: Guide editor container visible");
    const guideIdLabel = await page.textContent("#guide-edit-id-label");
    assert.ok(guideIdLabel.includes("guide_rough_1"), "Step 3: Selected guide is guide_rough_1");
    console.log("✓ Step 3 PASS: Selected Guide");

    // ----------------------------------------------------
    // Step 4: Select existing Figure
    // ----------------------------------------------------
    await page.click("#list-figures .list-item:first-child");
    await page.waitForTimeout(100);
    const isFigureEditorVisible = await page.$eval("#figure-editor-container", el => el.style.display !== "none");
    assert.equal(isFigureEditorVisible, true, "Step 4: Figure editor container visible");
    const figIdLabel = await page.textContent("#figure-edit-id-label");
    assert.ok(figIdLabel.includes("fig_ren"), "Step 4: Selected figure is fig_ren");
    console.log("✓ Step 4 PASS: Selected existing Figure fig_ren");

    // ----------------------------------------------------
    // Step 5: Actual canvas pointer-drag Figure
    // ----------------------------------------------------
    const canvasBox = await page.$eval("#manga-canvas", el => {
        const r = el.getBoundingClientRect();
        return { left: r.left, top: r.top, width: r.width, height: r.height };
    });

    const figBeforeMove = await page.evaluate(() => {
        const g = window.__tegakiManga.store.getPage().guides[0];
        return {
            placement: { ...g.placement },
            area: { ...g.figure_regions.find(f => f.figure_id === "fig_ren").area }
        };
    });

    // Compute center of fig_ren in page pixels:
    // pageFigX = placement.x + fig.area.x * placement.w
    // pageFigY = placement.y + fig.area.y * placement.h
    const pfxCenter = (figBeforeMove.placement.x + (figBeforeMove.area.x + figBeforeMove.area.w / 2) * figBeforeMove.placement.w) * canvasBox.width;
    const pfyCenter = (figBeforeMove.placement.y + (figBeforeMove.area.y + figBeforeMove.area.h / 2) * figBeforeMove.placement.h) * canvasBox.height;

    // Physical pointer drag: mousedown, mousemove (+30px, +30px), mouseup
    await page.mouse.move(canvasBox.left + pfxCenter, canvasBox.top + pfyCenter);
    await page.mouse.down();
    await page.mouse.move(canvasBox.left + pfxCenter + 30, canvasBox.top + pfyCenter + 30, { steps: 5 });
    await page.mouse.up();
    await page.waitForTimeout(100);

    const figAfterMove = await page.evaluate(() => {
        const g = window.__tegakiManga.store.getPage().guides[0];
        return { ...g.figure_regions.find(f => f.figure_id === "fig_ren").area };
    });

    assert.ok(figAfterMove.x > figBeforeMove.area.x, "Step 5: Figure moved right in local coordinates");
    assert.ok(figAfterMove.y > figBeforeMove.area.y, "Step 5: Figure moved down in local coordinates");
    console.log("✓ Step 5 PASS: Actual canvas pointer-drag Figure succeeded");

    // ----------------------------------------------------
    // Step 6: Actual pointer resize via at least two corner handles (SE and NW)
    // ----------------------------------------------------
    // Handle 1: SE handle
    const figBeforeSE = await page.evaluate(() => {
        const g = window.__tegakiManga.store.getPage().guides[0];
        return {
            placement: { ...g.placement },
            area: { ...g.figure_regions.find(f => f.figure_id === "fig_ren").area }
        };
    });

    const pfxSE = (figBeforeSE.placement.x + (figBeforeSE.area.x + figBeforeSE.area.w) * figBeforeSE.placement.w) * canvasBox.width;
    const pfySE = (figBeforeSE.placement.y + (figBeforeSE.area.y + figBeforeSE.area.h) * figBeforeSE.placement.h) * canvasBox.height;

    await page.mouse.move(canvasBox.left + pfxSE, canvasBox.top + pfySE);
    await page.mouse.down();
    await page.mouse.move(canvasBox.left + pfxSE + 25, canvasBox.top + pfySE + 25, { steps: 5 });
    await page.mouse.up();
    await page.waitForTimeout(100);

    const figAfterSE = await page.evaluate(() => {
        const g = window.__tegakiManga.store.getPage().guides[0];
        return { ...g.figure_regions.find(f => f.figure_id === "fig_ren").area };
    });

    assert.ok(figAfterSE.w > figBeforeSE.area.w, "Step 6: SE resize expanded figure width");
    assert.ok(figAfterSE.h > figBeforeSE.area.h, "Step 6: SE resize expanded figure height");

    // Handle 2: NW handle
    const figBeforeNW = await page.evaluate(() => {
        const g = window.__tegakiManga.store.getPage().guides[0];
        return {
            placement: { ...g.placement },
            area: { ...g.figure_regions.find(f => f.figure_id === "fig_ren").area }
        };
    });

    const pfxNW = (figBeforeNW.placement.x + figBeforeNW.area.x * figBeforeNW.placement.w) * canvasBox.width;
    const pfyNW = (figBeforeNW.placement.y + figBeforeNW.area.y * figBeforeNW.placement.h) * canvasBox.height;

    await page.mouse.move(canvasBox.left + pfxNW, canvasBox.top + pfyNW);
    await page.mouse.down();
    await page.mouse.move(canvasBox.left + pfxNW - 15, canvasBox.top + pfyNW - 15, { steps: 5 });
    await page.mouse.up();
    await page.waitForTimeout(100);

    const figAfterNW = await page.evaluate(() => {
        const g = window.__tegakiManga.store.getPage().guides[0];
        return { ...g.figure_regions.find(f => f.figure_id === "fig_ren").area };
    });

    assert.ok(figAfterNW.x < figBeforeNW.area.x, "Step 6: NW resize moved figure top-left x left");
    assert.ok(figAfterNW.y < figBeforeNW.area.y, "Step 6: NW resize moved figure top-left y up");
    console.log("✓ Step 6 PASS: Actual pointer resize via SE and NW corner handles succeeded");

    // ----------------------------------------------------
    // Step 7: Add Figure
    // ----------------------------------------------------
    await page.click("#btn-add-figure");
    await page.waitForTimeout(100);
    const countAfterAdd = await page.textContent("#count-figures");
    assert.equal(countAfterAdd.trim(), "3", "Step 7: Figure count increased to 3");
    console.log("✓ Step 7 PASS: Added new Figure (figure_1)");

    // ----------------------------------------------------
    // Step 8: Associate new Figure to an available Character Instance
    // ----------------------------------------------------
    // inst_ren_1 and inst_sora_1 are currently used by fig_ren and fig_sora.
    // First, select fig_sora and unassign it so inst_sora_1 is available
    await page.click("#list-figures .list-item:nth-child(2)"); // fig_sora
    await page.waitForTimeout(100);
    await page.selectOption("#select-figure-instance", ""); // Unassigned
    await page.waitForTimeout(100);

    // Now select the newly added figure (3rd item)
    await page.click("#list-figures .list-item:nth-child(3)");
    await page.waitForTimeout(100);
    await page.selectOption("#select-figure-instance", "inst_sora_1");
    await page.waitForTimeout(100);

    const assignedFigInst = await page.evaluate(() => {
        const g = window.__tegakiManga.store.getPage().guides[0];
        return g.figure_regions[2].instance_id;
    });
    assert.equal(assignedFigInst, "inst_sora_1", "Step 8: New figure associated with inst_sora_1");
    console.log("✓ Step 8 PASS: Associated new Figure with inst_sora_1");

    // ----------------------------------------------------
    // Step 9: Attempt duplicate association -> visible rejection
    // ----------------------------------------------------
    // Try to associate fig_sora (2nd item) with inst_sora_1 (which is already on 3rd item)
    await page.click("#list-figures .list-item:nth-child(2)");
    await page.waitForTimeout(100);
    await page.selectOption("#select-figure-instance", "inst_sora_1");
    await page.waitForTimeout(100);

    const errorVisible = await page.$eval("#guide-error-banner", el => el.style.display !== "none");
    const errorText = await page.textContent("#guide-error-banner");
    assert.equal(errorVisible, true, "Step 9: Error banner must be visible on duplicate association");
    assert.ok(errorText.includes("already associated"), "Step 9: Error mentions duplicate association");
    console.log("✓ Step 9 PASS: Duplicate association visibly rejected");

    // ----------------------------------------------------
    // Step 10: Unassign
    // ----------------------------------------------------
    await page.click("#list-figures .list-item:nth-child(3)"); // 3rd item (has inst_sora_1)
    await page.waitForTimeout(100);
    await page.selectOption("#select-figure-instance", "");
    await page.waitForTimeout(100);

    const unassignedVal = await page.evaluate(() => {
        const g = window.__tegakiManga.store.getPage().guides[0];
        return g.figure_regions[2].instance_id;
    });
    assert.equal(unassignedVal, null, "Step 10: Figure unassigned");
    console.log("✓ Step 10 PASS: Unassign succeeded");

    // ----------------------------------------------------
    // Step 11: Toggle Guide disabled/enabled
    // ----------------------------------------------------
    await page.click("#btn-toggle-guide-enabled");
    await page.waitForTimeout(100);
    const disabledState = await page.evaluate(() => window.__tegakiManga.store.getPage().guides[0].enabled);
    assert.equal(disabledState, false, "Step 11: Guide disabled");

    await page.click("#btn-toggle-guide-enabled");
    await page.waitForTimeout(100);
    const enabledState = await page.evaluate(() => window.__tegakiManga.store.getPage().guides[0].enabled);
    assert.equal(enabledState, true, "Step 11: Guide re-enabled");
    console.log("✓ Step 11 PASS: Guide toggle disabled/enabled verified");

    // ----------------------------------------------------
    // Step 12: Remove one Figure
    // ----------------------------------------------------
    await page.click("#list-figures .list-item:nth-child(3)");
    await page.waitForTimeout(100);
    await page.click("#btn-delete-figure");
    await page.waitForTimeout(100);
    const countAfterDel = await page.textContent("#count-figures");
    assert.equal(countAfterDel.trim(), "2", "Step 12: Figure count back to 2");
    console.log("✓ Step 12 PASS: Removed one Figure");

    // ----------------------------------------------------
    // Step 13, 14, 15: Export, Import, Verify Durable Data
    // ----------------------------------------------------
    await page.click("#btn-export-json");
    await page.waitForTimeout(100);
    const exportedJson = await page.$eval("#modal-json-text", el => el.value);
    await page.click("#btn-close-modal");
    await page.waitForTimeout(100);

    // Reset document
    await page.click("#btn-reset-default");
    await page.waitForTimeout(100);
    const guidesAfterReset = await page.textContent("#count-guides");
    assert.equal(guidesAfterReset.trim(), "0", "Reset cleared guides");

    // Import previously exported JSON
    await page.click("#btn-load-json");
    await page.waitForTimeout(100);
    await page.$eval("#modal-json-text", (el, val) => { el.value = val; }, exportedJson);
    await page.click("#btn-modal-action");
    await page.waitForTimeout(100);

    const importedGuideData = await page.evaluate(() => {
        const doc = window.__tegakiManga.store.getDocument();
        return {
            valid: doc.pages[0].guides.length === 1,
            guide: doc.pages[0].guides[0]
        };
    });

    assert.equal(importedGuideData.valid, true, "Step 15: Exactly 1 guide imported");
    assert.equal(importedGuideData.guide.guide_id, "guide_rough_1");
    assert.equal(importedGuideData.guide.enabled, true);
    assert.equal(importedGuideData.guide.figure_regions.length, 2);
    assert.equal(importedGuideData.guide.figure_regions[0].figure_id, "fig_ren");
    assert.equal(importedGuideData.guide.figure_regions[0].instance_id, "inst_ren_1");
    console.log("✓ Step 13-15 PASS: Export/re-import durable parity verified");

    // ====================================================
    // PART 2: M1C1 FRAME POINTER REGRESSION (Section 27 & 34)
    // ====================================================
    console.log("--- Running Part 2: M1C1 Frame Pointer Regression ---");

    // Switch to Visual Frames layer
    await page.click("#tab-frames");
    await page.waitForTimeout(100);

    // Select frame_1
    await page.click("#list-frames .list-item:first-child");
    await page.waitForTimeout(100);

    const frameBeforeMove = await page.evaluate(() => {
        return { ...window.__tegakiManga.store.getPage().visual_frames[0].area };
    });

    // Center of frame_1 in canvas pixels
    const framePxX = (frameBeforeMove.x + frameBeforeMove.w / 2) * canvasBox.width;
    const framePxY = (frameBeforeMove.y + frameBeforeMove.h / 2) * canvasBox.height;

    // Actual canvas pointer drag: mousedown, mousemove (-15px, -15px), mouseup
    await page.mouse.move(canvasBox.left + framePxX, canvasBox.top + framePxY);
    await page.mouse.down();
    await page.mouse.move(canvasBox.left + framePxX - 15, canvasBox.top + framePxY - 15, { steps: 5 });
    await page.mouse.up();
    await page.waitForTimeout(100);

    const frameAfterMove = await page.evaluate(() => {
        return { ...window.__tegakiManga.store.getPage().visual_frames[0].area };
    });

    assert.ok(frameAfterMove.x < frameBeforeMove.x, "Part 2: Frame moved left via actual canvas pointer drag");
    assert.ok(frameAfterMove.y < frameBeforeMove.y, "Part 2: Frame moved up via actual canvas pointer drag");
    console.log("✓ M1C1 Regression PASS: Frame canvas pointer drag verified");

    // Frame Resize Handle 1: SE Handle
    const frameBeforeSE = { ...frameAfterMove };
    const framePxSE_X = (frameBeforeSE.x + frameBeforeSE.w) * canvasBox.width;
    const framePxSE_Y = (frameBeforeSE.y + frameBeforeSE.h) * canvasBox.height;

    await page.mouse.move(canvasBox.left + framePxSE_X, canvasBox.top + framePxSE_Y);
    await page.mouse.down();
    await page.mouse.move(canvasBox.left + framePxSE_X + 20, canvasBox.top + framePxSE_Y + 20, { steps: 5 });
    await page.mouse.up();
    await page.waitForTimeout(100);

    const frameAfterSE = await page.evaluate(() => {
        return { ...window.__tegakiManga.store.getPage().visual_frames[0].area };
    });

    assert.ok(frameAfterSE.w > frameBeforeSE.w, "Part 2: Frame SE handle pointer resize expanded width");
    assert.ok(frameAfterSE.h > frameBeforeSE.h, "Part 2: Frame SE handle pointer resize expanded height");
    console.log("✓ M1C1 Regression PASS: Frame SE corner handle pointer resize verified");

    // Frame Resize Handle 2: NW Handle
    const frameBeforeNW = { ...frameAfterSE };
    const framePxNW_X = frameBeforeNW.x * canvasBox.width;
    const framePxNW_Y = frameBeforeNW.y * canvasBox.height;

    await page.mouse.move(canvasBox.left + framePxNW_X, canvasBox.top + framePxNW_Y);
    await page.mouse.down();
    await page.mouse.move(canvasBox.left + framePxNW_X - 15, canvasBox.top + framePxNW_Y - 15, { steps: 5 });
    await page.mouse.up();
    await page.waitForTimeout(100);

    const frameAfterNW = await page.evaluate(() => {
        return { ...window.__tegakiManga.store.getPage().visual_frames[0].area };
    });

    assert.ok(frameAfterNW.x < frameBeforeNW.x, "Part 2: Frame NW handle pointer resize expanded left");
    assert.ok(frameAfterNW.y < frameBeforeNW.y, "Part 2: Frame NW handle pointer resize expanded top");
    console.log("✓ M1C1 Regression PASS: Frame NW corner handle pointer resize verified");

    console.log("==================================================");
    console.log("ALL BROWSER TESTS AND POINTER REGRESSIONS PASSED (M1C2A)");
    console.log("==================================================");

} finally {
    await browser.close();
}
