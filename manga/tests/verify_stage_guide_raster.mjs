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

const SCREENSHOT_DIR = path.resolve("scratch/stage_guide_raster_screenshots");
fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });

async function runStageGuideRasterAcceptance() {
    console.log("=== MANGA-STAGE-GUIDE-RASTER-PREVIEW1 ACCEPTANCE ===");
    
    const chromium = getPlaywrightChromium();
    assert(chromium, "Playwright Chromium must be available");
    
    const browser = await chromium.launch({ headless: true });
    
    const viewports = [
        { name: "desktop", width: 1440, height: 900 },
        { name: "narrow", width: 1024, height: 768 }
    ];

    for (const vp of viewports) {
        console.log(`\n==================================================`);
        console.log(`Testing with viewport: ${vp.name} (${vp.width}x${vp.height})`);
        console.log(`==================================================`);
        
        const context = await browser.newContext({
            viewport: { width: vp.width, height: vp.height }
        });
        const page = await context.newPage();
        page.on('console', msg => {
            const txt = msg.text();
            if (txt.includes('Error') || txt.includes('error') || txt.includes('exception')) {
                console.log(`[PAGE LOG ${vp.name}]:`, txt);
            }
        });

        console.log("Navigating to http://127.0.0.1:8191/ ...");
        await page.goto("http://127.0.0.1:8191/", { waitUntil: "networkidle" });
        await page.waitForFunction(() => window.__tegakiManga && window.__tegakiManga.generation?.state?.catalog);

        // ==============================================================
        // Step A: No Guide -> No raster underlay
        // ==============================================================
        console.log("\n--- Step A: No Guide (Verify no raster underlay) ---");
        await page.evaluate(() => {
            const { store, session, setMangaMode, updateAll } = window.__tegakiManga;
            const doc = store.getDocument();
            doc.pages[0].scenes = [];
            doc.pages[0].cast = [];
            doc.pages[0].character_instances = [];
            doc.pages[0].guides = [];
            doc.pages[0].style_prompt = "";
            doc.pages[0].style_negative_prompt = "";
            store.setDocument(doc);
            session.selectScene(null);
            session.selectCast(null);
            session.selectInstance(null);
            session.selectGuide(null);
            session.selectFigure(null);
            setMangaMode("authoring");
            updateAll();
        });

        // Add 1 Scene and switch Stage to Layout
        await page.click("#mg-scene-add");
        await page.waitForSelector("#scene-prompt-tab-scene_1", { timeout: 3000 });
        await page.click("#mg-stage-mode-layout");
        assert.equal(await page.getAttribute("#mg-stage-mode-layout", "aria-selected"), "true");

        // Verify NO raster underlay exists in SVG
        const rasterCountA = await page.locator("svg#mg-stage-overlay image.mg-stage-guide-raster").count();
        assert.equal(rasterCountA, 0, "No raster underlay should exist when there are no guides");

        const screenshotA = path.join(SCREENSHOT_DIR, `01_no_guide_layout_${vp.name}.png`);
        await page.screenshot({ path: screenshotA });
        console.log(`✓ Step A PASS (${vp.name}). Screenshot saved: ${screenshotA}`);

        // ==============================================================
        // Step B: One Enabled Guide -> Actual raster underlay in Layout
        // ==============================================================
        console.log("\n--- Step B: One Enabled Guide (Verify raster underlay rendered) ---");
        const guideAsset = "tegaki_manga_guides/disposable_guide_single_character.png";
        await page.evaluate((asset) => {
            const { store, session, updateAll } = window.__tegakiManga;
            const newGuide = store.addGuideFromAsset({
                asset_reference: asset,
                image_width: 832,
                image_height: 1216
            });
            session.selectGuide(newGuide.guide_id);
            updateAll();
        }, guideAsset);

        // Verify raster underlay in SVG
        const rasterLocator = page.locator("svg#mg-stage-overlay image.mg-stage-guide-raster");
        await rasterLocator.waitFor({ state: "attached", timeout: 3000 });
        
        const href = await rasterLocator.getAttribute("href");
        assert(href.includes("/api/guide-assets/view?ref=tegaki_manga_guides%2Fdisposable_guide_single_character.png"),
            `Href must use canonical endpoint: ${href}`);
        
        const preserveRatio = await rasterLocator.getAttribute("preserveAspectRatio");
        assert.equal(preserveRatio, "xMidYMid meet", "preserveAspectRatio must be 'xMidYMid meet'");

        // Verify pointer events are disabled
        const pointerEvents = await rasterLocator.evaluate(el => window.getComputedStyle(el).pointerEvents);
        assert.equal(pointerEvents, "none", "Guide raster must have pointer-events: none");

        const screenshotB = path.join(SCREENSHOT_DIR, `02_guide_raster_underlay_${vp.name}.png`);
        await page.screenshot({ path: screenshotB });
        console.log(`✓ Step B PASS (${vp.name}). Screenshot saved: ${screenshotB}`);

        // ==============================================================
        // Step C: Scene Geometry Manipulation over Underlay
        // ==============================================================
        console.log("\n--- Step C: Scene move & resize over raster underlay ---");
        const sceneRect = page.locator("svg#mg-stage-overlay rect.mg-stage-scene-region.is-active");
        await sceneRect.waitFor({ state: "visible", timeout: 3000 });

        const docBBefore = await page.evaluate(() => window.__tegakiManga.store.getPage().scenes[0]);
        const sceneBox = await sceneRect.boundingBox();
        assert(sceneBox, "Scene rect must have bounding box");

        // Drag scene
        await page.mouse.move(sceneBox.x + sceneBox.width / 2, sceneBox.y + sceneBox.height / 2);
        await page.mouse.down();
        await page.mouse.move(sceneBox.x + sceneBox.width / 2 - 15, sceneBox.y + sceneBox.height / 2 + 25, { steps: 5 });
        await page.mouse.up();

        const docBAfterMove = await page.evaluate(() => window.__tegakiManga.store.getPage().scenes[0]);
        assert(docBAfterMove.area.x !== docBBefore.area.x || docBAfterMove.area.y !== docBBefore.area.y,
            "Scene must move over the underlay without interference");

        // Resize scene via SE handle
        const seHandle = page.locator("svg#mg-stage-overlay rect.mg-stage-resize-handle[data-handle='se']");
        await seHandle.waitFor({ state: "visible", timeout: 3000 });
        const handleBox = await seHandle.boundingBox();

        await page.mouse.move(handleBox.x + handleBox.width / 2, handleBox.y + handleBox.height / 2);
        await page.mouse.down();
        await page.mouse.move(handleBox.x + handleBox.width / 2 - 20, handleBox.y + handleBox.height / 2 + 25, { steps: 5 });
        await page.mouse.up();

        const docBAfterResize = await page.evaluate(() => window.__tegakiManga.store.getPage().scenes[0]);
        assert(docBAfterResize.area.w !== docBAfterMove.area.w || docBAfterResize.area.h !== docBAfterMove.area.h,
            "Scene must resize over the underlay without interference");

        const screenshotC = path.join(SCREENSHOT_DIR, `03_scene_manipulation_over_underlay_${vp.name}.png`);
        await page.screenshot({ path: screenshotC });
        console.log(`✓ Step C PASS (${vp.name}). Screenshot saved: ${screenshotC}`);

        // ==============================================================
        // Step D: Character Instance Manipulation over Underlay
        // ==============================================================
        console.log("\n--- Step D: Character Instance move & resize over raster underlay ---");
        // Create Character 1
        await page.click("#mg-cast-add");
        await page.waitForSelector("#scene-prompt-tab-cast_cast_1", { timeout: 3000 });

        // Assign Reference Asset
        const refAsset = "tegaki_manga_references/ref_c789751db904319d.png";
        await page.evaluate((asset) => {
            const { store, session, updateAll } = window.__tegakiManga;
            store.setCastReference(session.selectedCastId || "cast_1", asset);
            updateAll();
        }, refAsset);

        // Return to Scene 1 and toggle appearance
        await page.click("#scene-prompt-tab-scene_1");
        const castToggle = page.locator(".scene-cast-appearance-button");
        await castToggle.waitFor({ state: "visible", timeout: 3000 });
        await castToggle.click();

        // Confirm Character Instance on Stage
        const charRect = page.locator("svg#mg-stage-overlay rect.mg-stage-char-instance");
        await charRect.waitFor({ state: "visible", timeout: 3000 });
        const charBox = await charRect.boundingBox();

        // Drag character instance over underlay
        await page.mouse.move(charBox.x + charBox.width / 2, charBox.y + charBox.height / 2);
        await page.mouse.down();
        await page.mouse.move(charBox.x + charBox.width / 2 + 20, charBox.y + charBox.height / 2 + 10, { steps: 5 });
        await page.mouse.up();

        const docDAfterMove = await page.evaluate(() => window.__tegakiManga.store.getPage());
        const instAfterMove = docDAfterMove.character_instances[0];
        console.log("  Instance Area After Move over Underlay:", instAfterMove.area);

        // Resize instance via SE handle over underlay
        const instHandle = page.locator("svg#mg-stage-overlay rect.mg-stage-resize-handle[data-handle='se']");
        await instHandle.waitFor({ state: "visible", timeout: 3000 });
        const instHandleBox = await instHandle.boundingBox();

        await page.mouse.move(instHandleBox.x + instHandleBox.width / 2, instHandleBox.y + instHandleBox.height / 2);
        await page.mouse.down();
        await page.mouse.move(instHandleBox.x + instHandleBox.width / 2 + 25, instHandleBox.y + instHandleBox.height / 2 + 25, { steps: 5 });
        await page.mouse.up();

        const docDAfterResize = await page.evaluate(() => window.__tegakiManga.store.getPage());
        const instAfterResize = docDAfterResize.character_instances[0];
        console.log("  Instance Area After Resize over Underlay:", instAfterResize.area);

        // Verify containment
        const scArea = docDAfterResize.scenes[0].area;
        assert(instAfterResize.area.x >= scArea.x - 0.001);
        assert(instAfterResize.area.y >= scArea.y - 0.001);
        assert(instAfterResize.area.x + instAfterResize.area.w <= scArea.x + scArea.w + 0.001);
        assert(instAfterResize.area.y + instAfterResize.area.h <= scArea.y + scArea.h + 0.001);

        const screenshotD = path.join(SCREENSHOT_DIR, `04_character_instance_over_underlay_${vp.name}.png`);
        await page.screenshot({ path: screenshotD });
        console.log(`✓ Step D PASS (${vp.name}). Screenshot saved: ${screenshotD}`);

        // ==============================================================
        // Step E: Selection & Layer Rules
        // ==============================================================
        console.log("\n--- Step E: Selection and layer rules ---");
        // Switch to Cast layer
        await page.click("#scene-prompt-tab-cast_cast_1");
        assert.equal(await page.getAttribute("#scene-prompt-tab-cast_cast_1", "aria-pressed"), "true");
        // Switch back to Scene layer
        await page.click("#scene-prompt-tab-scene_1");
        assert.equal(await page.getAttribute("#scene-prompt-tab-scene_1", "aria-selected"), "true");
        console.log("✓ Step E PASS: Selection layer rules remain intact over underlay");

        // ==============================================================
        // Step F: Guide Disabled -> Underlay hidden
        // ==============================================================
        console.log("\n--- Step F: Guide Disabled (Underlay hidden, no data loss) ---");
        await page.click("#mg-btn-toggle-guide");
        const guideBadgeOff = await page.textContent("#mg-guide-status-badge");
        assert(guideBadgeOff.includes("DISABLED"), `Badge must indicate disabled: ${guideBadgeOff}`);

        // Verify raster underlay is NOT rendered when guide is disabled
        const rasterCountDisabled = await page.locator("svg#mg-stage-overlay image.mg-stage-guide-raster").count();
        assert.equal(rasterCountDisabled, 0, "Raster underlay must NOT be displayed when guide is disabled");

        // Verify vector outline still exists and reflects disabled state
        const dashedGuide = await page.locator("svg#mg-stage-overlay rect[stroke='#ca8a04']").count();
        assert.equal(dashedGuide, 1, "Dashed guide outline must be preserved when disabled");

        // Confirm Scene and Instance geometry intact
        const docFAfterToggle = await page.evaluate(() => window.__tegakiManga.store.getPage());
        assert.deepEqual(docFAfterToggle.scenes[0].area, docDAfterResize.scenes[0].area);
        assert.deepEqual(docFAfterToggle.character_instances[0].area, docDAfterResize.character_instances[0].area);

        const screenshotF = path.join(SCREENSHOT_DIR, `05_guide_disabled_layout_${vp.name}.png`);
        await page.screenshot({ path: screenshotF });

        // Re-enable Guide
        await page.click("#mg-btn-toggle-guide");
        const guideBadgeOn = await page.textContent("#mg-guide-status-badge");
        assert.equal(guideBadgeOn.trim(), "GUIDE ENABLED");
        assert.equal(await page.locator("svg#mg-stage-overlay image.mg-stage-guide-raster").count(), 1,
            "Raster underlay must reappear when guide is re-enabled");
        console.log(`✓ Step F PASS (${vp.name}). Screenshot saved: ${screenshotF}`);

        // ==============================================================
        // Step G: Layout vs Result -> Raster only in Layout
        // ==============================================================
        console.log("\n--- Step G: Layout vs Result (Raster only in Layout) ---");
        await page.click("#mg-stage-mode-result");
        assert.equal(await page.getAttribute("#mg-stage-mode-result", "aria-selected"), "true");
        assert.equal(await page.getAttribute("#mg-stage-mode-layout", "aria-selected"), "false");

        const stageOverlayDisplay = await page.evaluate(() => document.querySelector("#mg-stage-overlay").style.display);
        assert.equal(stageOverlayDisplay, "none", "Stage overlay must be hidden in Result mode");

        await page.click("#mg-stage-mode-layout");
        assert.equal(await page.getAttribute("#mg-stage-mode-layout", "aria-selected"), "true");
        assert.equal(await page.locator("svg#mg-stage-overlay image.mg-stage-guide-raster").count(), 1,
            "Raster underlay must be visible when returning to Layout mode");
        console.log("✓ Step G PASS: Raster appears strictly in Layout mode");

        // ==============================================================
        // Step H: Target Switching Integrity
        // ==============================================================
        console.log("\n--- Step H: Target switching integrity ---");
        await page.click("#scene-prompt-tab-global");
        await page.click("#scene-composer-prompt");
        await page.fill("#scene-composer-prompt", "global prompt updated");

        await page.click("#scene-prompt-tab-scene_1");
        await page.click("#scene-composer-prompt");
        await page.fill("#scene-composer-prompt", "scene prompt updated");

        await page.click("#scene-prompt-tab-cast_cast_1");
        await page.click("#scene-composer-prompt");
        await page.fill("#scene-composer-prompt", "identity prompt updated");

        // Confirm guide raster still active and intact
        const docH = await page.evaluate(() => window.__tegakiManga.store.getPage());
        assert.equal(docH.guides.length, 1);
        assert.equal(docH.guides[0].asset_reference, guideAsset);
        assert.equal(await page.locator("svg#mg-stage-overlay image.mg-stage-guide-raster").count(), 1);
        console.log("✓ Step H PASS: Target switching preserved guide underlay and document integrity");

        // ==============================================================
        // Step I: Generation Scope & Narrow Viewport
        // ==============================================================
        console.log("\n--- Step I: Generation Scope in Layout ---");
        await page.click("#mg-generation-scope-scenes");
        assert.equal(await page.getAttribute("#mg-generation-scope-scenes", "aria-pressed"), "true");

        const screenshotI = path.join(SCREENSHOT_DIR, `06_scenes_scope_with_underlay_${vp.name}.png`);
        await page.screenshot({ path: screenshotI });
        console.log(`✓ Step I PASS (${vp.name}). Screenshot saved: ${screenshotI}`);

        await context.close();
    }

    await browser.close();
    console.log("\nALL BROWSER ACCEPTANCE CHECKS PASSED PERFECTLY!");
}

runStageGuideRasterAcceptance().catch(err => {
    console.error("TEST FAILED:", err);
    process.exit(1);
});
