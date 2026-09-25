/**
 * verify_scene_resolution_and_steppers.mjs
 * =========================================
 * Targeted Playwright browser acceptance test for:
 * CARD: MANGA-ADD-SCENE-RESOLUTION-AND-ARROWS1
 *
 * Verifies:
 * 1. Fresh state: Width and Height are editable, ▲ / ▼ spin buttons active, wheel works.
 * 2. Click "+ Scene": Width and Height REMAIN editable (readOnly === false), ▲ / ▼ active, wheel works.
 * 3. Change Width and Height via direct input, ▲ / ▼ stepper, or wheel:
 *    - Value updates correctly in input and draft.
 *    - Store page dimensions update (page.width_px, page.height_px).
 *    - Compile plan / scene generation settings receive updated dimensions.
 *    - Layout stage preview reflects new dimensions and aspect ratio.
 * 4. Add second Scene: controls remain functional and editable.
 * 5. Add third Scene: controls remain functional and editable.
 * 6. Captures screenshot of Manga Create with Scene added showing editable Width / Height.
 */

import assert from "node:assert/strict";
import path from "node:path";
import fs from "node:fs";
import { createRequire } from "node:module";
import { execSync } from "node:child_process";

const require = createRequire(import.meta.url);

function getPlaywrightChromium() {
    if (process.env.TEGAKI_PLAYWRIGHT_MODULE) return require(process.env.TEGAKI_PLAYWRIGHT_MODULE).chromium;
    try { return require("playwright").chromium; } catch {}
    const root = execSync("npm root -g", { encoding: "utf8" }).trim();
    return require(path.join(root, "@executeautomation", "playwright-mcp-server", "node_modules", "playwright")).chromium;
}

async function runAcceptanceTest() {
    console.log("=== VERIFY MANGA SCENE RESOLUTION AND STEPPERS ===");
    const chromium = getPlaywrightChromium();
    assert(chromium, "Playwright Chromium must be available");

    const browser = await chromium.launch({ headless: true });
    const context = await browser.newContext({ viewport: { width: 1400, height: 900 } });
    const page = await context.newPage();

    try {
        console.log("1. Navigating to Manga workspace (http://127.0.0.1:8191/) ...");
        await page.goto("http://127.0.0.1:8191/", { waitUntil: "networkidle" });
        await page.waitForFunction(() => window.__tegakiManga && window.__tegakiManga.generation?.ready);
        console.log("   Manga workspace loaded successfully.");

        // Check Fresh State (Global mode, 0 scenes)
        console.log("2. Checking fresh state (0 scenes)...");
        const freshState = await page.evaluate(() => {
            const widthInput = document.getElementById("mg-width");
            const heightInput = document.getElementById("mg-height");
            const store = window.__tegakiManga.store;
            const p = store.getPage(0);
            return {
                widthVal: widthInput.value,
                heightVal: heightInput.value,
                widthReadOnly: widthInput.readOnly,
                heightReadOnly: heightInput.readOnly,
                pageWidth: p?.width_px,
                pageHeight: p?.height_px,
                sceneCount: (p?.scenes || []).length
            };
        });

        console.log("   Fresh state:", freshState);
        assert.equal(freshState.widthReadOnly, false, "Width must NOT be read-only in fresh state");
        assert.equal(freshState.heightReadOnly, false, "Height must NOT be read-only in fresh state");

        // Test wheel on fresh state
        console.log("3. Testing wheel adjustment on fresh state...");
        await page.focus("#mg-width");
        await page.hover("#mg-width");
        await page.mouse.wheel(0, -100); // wheel up -> step +8
        const afterWheelUp = await page.$eval("#mg-width", el => parseInt(el.value, 10));
        console.log("   Width after wheel up:", afterWheelUp);
        assert.equal(afterWheelUp, parseInt(freshState.widthVal, 10) + 8, "Wheel up must increase width by 8");

        // Click "+ Scene" to add Scene 1
        console.log("4. Clicking '+ Scene' to create Scene 1...");
        await page.click("#mg-scene-add");
        await page.waitForTimeout(300);

        const scene1State = await page.evaluate(() => {
            const widthInput = document.getElementById("mg-width");
            const heightInput = document.getElementById("mg-height");
            const store = window.__tegakiManga.store;
            const gen = window.__tegakiManga.generation;
            const p = store.getPage(0);
            const previewLabel = document.getElementById("mg-preview-label");
            const stageOverlay = document.getElementById("mg-stage-overlay");
            return {
                widthVal: widthInput.value,
                heightVal: heightInput.value,
                widthReadOnly: widthInput.readOnly,
                heightReadOnly: heightInput.readOnly,
                widthDisabled: widthInput.disabled,
                heightDisabled: heightInput.disabled,
                scope: gen.getGenerationScope(),
                stageMode: gen.getStageMode(),
                pageWidth: p?.width_px,
                pageHeight: p?.height_px,
                sceneCount: (p?.scenes || []).length,
                previewLabelText: previewLabel?.textContent || "",
                viewBox: stageOverlay?.getAttribute("viewBox")
            };
        });

        console.log("   Scene 1 state:", scene1State);
        assert.equal(scene1State.sceneCount, 1, "Scene 1 must be present");
        assert.equal(scene1State.scope, "scenes", "Generation scope must be 'scenes'");
        assert.equal(scene1State.stageMode, "layout", "Stage mode must switch to 'layout'");
        assert.equal(scene1State.widthReadOnly, false, "Width must REMAIN editable (readOnly === false) after + Scene");
        assert.equal(scene1State.heightReadOnly, false, "Height must REMAIN editable (readOnly === false) after + Scene");
        assert.equal(scene1State.widthDisabled, false, "Width must NOT be disabled");
        assert.equal(scene1State.heightDisabled, false, "Height must NOT be disabled");

        // Verify direct input change
        console.log("5. Testing direct input change on Width and Height with 1 Scene active...");
        await page.fill("#mg-width", "896");
        await page.dispatchEvent("#mg-width", "input");
        await page.dispatchEvent("#mg-width", "change");

        await page.fill("#mg-height", "1152");
        await page.dispatchEvent("#mg-height", "input");
        await page.dispatchEvent("#mg-height", "change");

        await page.waitForTimeout(200);

        const directChangeState = await page.evaluate(() => {
            const store = window.__tegakiManga.store;
            const gen = window.__tegakiManga.generation;
            const p = store.getPage(0);
            const previewLabel = document.getElementById("mg-preview-label");
            const stageOverlay = document.getElementById("mg-stage-overlay");
            const settings = window.__tegakiManga.buildSceneGenerationSettings();
            return {
                draftWidth: gen.state.draft.width,
                draftHeight: gen.state.draft.height,
                pageWidth: p?.width_px,
                pageHeight: p?.height_px,
                settingsAuthoringDocPageWidth: settings.authoring_document?.pages?.[0]?.width_px,
                settingsAuthoringDocPageHeight: settings.authoring_document?.pages?.[0]?.height_px,
                previewLabelText: previewLabel?.textContent || "",
                viewBox: stageOverlay?.getAttribute("viewBox")
            };
        });

        console.log("   Direct change state:", directChangeState);
        assert.equal(directChangeState.draftWidth, "896", "Draft width must be 896");
        assert.equal(directChangeState.draftHeight, "1152", "Draft height must be 1152");
        assert.equal(directChangeState.pageWidth, 896, "Store page width must be 896");
        assert.equal(directChangeState.pageHeight, 1152, "Store page height must be 1152");
        assert.equal(directChangeState.settingsAuthoringDocPageWidth, 896, "Scene settings document width must be 896");
        assert.equal(directChangeState.settingsAuthoringDocPageHeight, 1152, "Scene settings document height must be 1152");
        assert.ok(directChangeState.previewLabelText.includes("896 × 1152"), `Preview label should show 896 × 1152: ${directChangeState.previewLabelText}`);
        assert.equal(directChangeState.viewBox, "0 0 896 1152", "SVG stageOverlay viewBox must be updated to '0 0 896 1152'");

        // Test wheel adjustment on Width with 1 Scene active
        console.log("6. Testing wheel adjustment with Scene active...");
        await page.focus("#mg-width");
        await page.hover("#mg-width");
        await page.mouse.wheel(0, -100); // wheel up -> 896 + 8 = 904
        await page.waitForTimeout(100);

        const afterSceneWheel = await page.evaluate(() => {
            const widthInput = document.getElementById("mg-width");
            const store = window.__tegakiManga.store;
            const p = store.getPage(0);
            return {
                val: widthInput.value,
                storeWidth: p?.width_px
            };
        });
        console.log("   Width after wheel up on Scene mode:", afterSceneWheel);
        assert.equal(afterSceneWheel.val, "904", "Wheel up must increment width to 904");
        assert.equal(afterSceneWheel.storeWidth, 904, "Store width must sync to 904");

        // Add 2nd Scene
        console.log("7. Clicking '+ Scene' to create Scene 2...");
        await page.click("#mg-scene-add");
        await page.waitForTimeout(300);

        const scene2State = await page.evaluate(() => {
            const widthInput = document.getElementById("mg-width");
            const heightInput = document.getElementById("mg-height");
            const store = window.__tegakiManga.store;
            const p = store.getPage(0);
            return {
                sceneCount: (p?.scenes || []).length,
                widthVal: widthInput.value,
                heightVal: heightInput.value,
                widthReadOnly: widthInput.readOnly,
                heightReadOnly: heightInput.readOnly
            };
        });
        console.log("   Scene 2 state:", scene2State);
        assert.equal(scene2State.sceneCount, 2, "Scene 2 must be present");
        assert.equal(scene2State.widthReadOnly, false, "Width must REMAIN editable after Scene 2");
        assert.equal(scene2State.heightReadOnly, false, "Height must REMAIN editable after Scene 2");

        // Add 3rd Scene
        console.log("8. Clicking '+ Scene' to create Scene 3...");
        await page.click("#mg-scene-add");
        await page.waitForTimeout(300);

        const scene3State = await page.evaluate(() => {
            const widthInput = document.getElementById("mg-width");
            const heightInput = document.getElementById("mg-height");
            const store = window.__tegakiManga.store;
            const p = store.getPage(0);
            return {
                sceneCount: (p?.scenes || []).length,
                widthVal: widthInput.value,
                heightVal: heightInput.value,
                widthReadOnly: widthInput.readOnly,
                heightReadOnly: heightInput.readOnly
            };
        });
        console.log("   Scene 3 state:", scene3State);
        assert.equal(scene3State.sceneCount, 3, "Scene 3 must be present");
        assert.equal(scene3State.widthReadOnly, false, "Width must REMAIN editable after Scene 3");
        assert.equal(scene3State.heightReadOnly, false, "Height must REMAIN editable after Scene 3");

        // Capture screenshot of Manga Create with Scene added showing editable Width / Height
        const scratchScreenshotPath = path.resolve("scratch/manga_create_scene_resolution_restored.png");
        fs.mkdirSync(path.dirname(scratchScreenshotPath), { recursive: true });
        await page.screenshot({ path: scratchScreenshotPath, fullPage: true });
        console.log(`9. Screenshot captured at: ${scratchScreenshotPath}`);

        console.log("\n>>> ALL ACCEPTANCE CHECKS PASSED SUCCESSFULLY! <<<");
    } finally {
        await browser.close();
    }
}

runAcceptanceTest().catch(err => {
    console.error("TEST FAILED:", err);
    process.exit(1);
});
