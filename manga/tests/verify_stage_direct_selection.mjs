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

const SCREENSHOT_DIR = path.resolve("scratch/stage_direct_selection_screenshots");
fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });

async function runStageDirectSelectionAcceptance() {
    console.log("=== MANGA-STAGE-DIRECT-TARGET-SELECTION1 ACCEPTANCE ===");
    
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

        // Setup test document: 1 Scene, 1 CAST, 1 Character Instance, 1 Guide
        console.log("\n--- Setting up test document ---");
        const setupInfo = await page.evaluate(() => {
            const { store, session, setMangaMode, updateAll } = window.__tegakiManga;
            const doc = store.getDocument();
            doc.pages[0].scenes = [
                {
                    scene_id: "scene_1",
                    name: "Upper Panel",
                    prompt: "1girl standing on rooftop, dramatic angle, sky background",
                    negative_prompt: "blurry, low quality",
                    area: { shape_type: "rect", x: 0.1, y: 0.1, w: 0.8, h: 0.4 }
                }
            ];
            doc.pages[0].cast = [
                {
                    cast_id: "hero",
                    display_name: "Heroine",
                    identity_prompt: "silver hair, blue eyes, ponytail, combat suit",
                    negative_prompt: "bad anatomy",
                    reference_asset: "tegaki_manga_references/ref_c789751db904319d.png",
                    color: "#06b6d4"
                }
            ];
            doc.pages[0].character_instances = [
                {
                    instance_id: "inst_1",
                    scene_id: "scene_1",
                    cast_id: "hero",
                    area: { shape_type: "rect", x: 0.15, y: 0.15, w: 0.25, h: 0.3 }
                }
            ];
            doc.pages[0].guides = [
                {
                    guide_id: "guide_1",
                    label: "Main Guide",
                    enabled: true,
                    asset_reference: "tegaki_manga_guides/disposable_guide_single_character.png",
                    weight: 0.8,
                    image_width: 832,
                    image_height: 1216
                }
            ];
            doc.pages[0].style_prompt = "high quality manga line art";
            doc.pages[0].style_negative_prompt = "photorealistic, colors";
            store.setDocument(doc);

            // Initially select scene_1
            session.setActiveTab("scenes");
            session.selectScene("scene_1");
            session.selectCast(null);
            session.selectInstance(null);
            setMangaMode("authoring");
            updateAll();

            return {
                sceneArea: doc.pages[0].scenes[0].area,
                instArea: doc.pages[0].character_instances[0].area
            };
        });

        // Ensure Layout mode is active
        await page.click("#mg-stage-mode-layout");
        await page.waitForTimeout(200);

        // ==============================================================
        // Test A: Initial Scene selection on Stage
        // ==============================================================
        console.log("\n--- Test A: Direct Scene selection on Stage ---");
        const stateA = await page.evaluate(() => {
            const { session, getComposerPromptTarget } = window.__tegakiManga;
            const promptVal = document.getElementById("scene-composer-prompt")?.value;
            const sceneHandles = document.querySelectorAll("svg#mg-stage-overlay .mg-stage-resize-handle").length;
            const sceneRectActive = document.querySelector("svg#mg-stage-overlay rect.mg-stage-scene-region")?.classList.contains("is-active");
            const charRectActive = document.querySelector("svg#mg-stage-overlay rect.mg-stage-char-instance")?.classList.contains("is-active");
            return {
                activeTab: session.activeTab,
                selectedSceneId: session.selectedSceneId,
                selectedInstanceId: session.selectedInstanceId,
                promptTarget: getComposerPromptTarget(),
                promptVal,
                sceneHandles,
                sceneRectActive,
                charRectActive
            };
        });

        assert.equal(stateA.activeTab, "scenes", "Active tab must be 'scenes'");
        assert.equal(stateA.selectedSceneId, "scene_1", "Selected scene must be 'scene_1'");
        assert.equal(stateA.selectedInstanceId, null, "No instance should be selected");
        assert.equal(stateA.promptTarget, "scene_1", "Prompt target must be 'scene_1'");
        assert.ok(stateA.promptVal.includes("1girl standing"), "Prompt textarea must show scene prompt");
        assert.equal(stateA.sceneHandles, 4, "Scene must have 4 resize handles");
        assert.equal(stateA.sceneRectActive, true, "Scene rect must have .is-active class");
        assert.equal(stateA.charRectActive, false, "Character rect must NOT have .is-active class");

        const screenshotA = path.join(SCREENSHOT_DIR, `01_scene_selected_${vp.name}.png`);
        await page.screenshot({ path: screenshotA });
        console.log(`✓ Test A PASS (${vp.name}). Screenshot: ${screenshotA}`);

        // ==============================================================
        // Test B: Direct Character Instance selection on Stage
        // ==============================================================
        console.log("\n--- Test B: Direct Character Instance selection on Stage ---");
        // Click directly on the Character Instance in SVG without clicking Create
        const charRect = page.locator("svg#mg-stage-overlay rect.mg-stage-char-instance");
        await charRect.click();
        await page.waitForTimeout(300);

        const stateB = await page.evaluate(() => {
            const { session, getComposerPromptTarget } = window.__tegakiManga;
            const promptVal = document.getElementById("scene-composer-prompt")?.value;
            const handles = document.querySelectorAll("svg#mg-stage-overlay .mg-stage-resize-handle").length;
            const sceneRectActive = document.querySelector("svg#mg-stage-overlay rect.mg-stage-scene-region")?.classList.contains("is-active");
            const charRectActive = document.querySelector("svg#mg-stage-overlay rect.mg-stage-char-instance")?.classList.contains("is-active");
            const castRefWrapDisplay = document.getElementById("scene-composer-cast-reference-wrap")?.style.display;
            const castRefImgSrc = document.getElementById("mg-cast-ref-img")?.src;
            return {
                activeTab: session.activeTab,
                selectedSceneId: session.selectedSceneId,
                selectedCastId: session.selectedCastId,
                selectedInstanceId: session.selectedInstanceId,
                promptTarget: getComposerPromptTarget(),
                promptVal,
                handles,
                sceneRectActive,
                charRectActive,
                castRefWrapDisplay,
                castRefImgSrc
            };
        });

        assert.equal(stateB.activeTab, "cast", "Active tab must switch to 'cast'");
        assert.equal(stateB.selectedCastId, "hero", "Selected CAST must be 'hero'");
        assert.equal(stateB.selectedInstanceId, "inst_1", "Selected instance must be 'inst_1'");
        assert.equal(stateB.selectedSceneId, "scene_1", "Parent scene 'scene_1' must remain selected");
        assert.equal(stateB.promptTarget, "cast_hero", "Prompt target must be 'cast_hero'");
        assert.ok(stateB.promptVal.includes("silver hair"), "Prompt textarea must show CAST identity prompt");
        assert.equal(stateB.handles, 4, "Character instance must have 4 resize handles");
        assert.equal(stateB.charRectActive, true, "Character rect must have .is-active class");
        assert.equal(stateB.sceneRectActive, false, "Scene rect must NOT have .is-active class");
        assert.equal(stateB.castRefWrapDisplay, "flex", "CAST Reference Hub must be visible");
        assert.ok(stateB.castRefImgSrc.includes("ref_c789751db904319d.png"), "CAST Reference Hub must display heroine reference image");

        const screenshotB = path.join(SCREENSHOT_DIR, `02_instance_selected_${vp.name}.png`);
        await page.screenshot({ path: screenshotB });
        console.log(`✓ Test B PASS (${vp.name}). Screenshot: ${screenshotB}`);

        // ==============================================================
        // Test C: Switching back to Scene directly on Stage
        // ==============================================================
        console.log("\n--- Test C: Switching back to Scene directly on Stage ---");
        // Click exposed Scene area: scene rect is at x=0.1..0.9, y=0.1..0.5.
        // inst rect is at x=0.15..0.40, y=0.15..0.45.
        // Click at top-right of scene (e.g. x=0.8, y=0.15) which is outside inst rect.
        const sceneRect = page.locator("svg#mg-stage-overlay rect.mg-stage-scene-region");
        const sceneBBox = await sceneRect.boundingBox();
        assert(sceneBBox, "Scene bounding box must be available");
        // Click near right edge of the scene box
        await page.mouse.click(sceneBBox.x + sceneBBox.width * 0.85, sceneBBox.y + sceneBBox.height * 0.3);
        await page.waitForTimeout(300);

        const stateC = await page.evaluate(() => {
            const { session, getComposerPromptTarget } = window.__tegakiManga;
            const promptVal = document.getElementById("scene-composer-prompt")?.value;
            const handles = document.querySelectorAll("svg#mg-stage-overlay .mg-stage-resize-handle").length;
            const sceneRectActive = document.querySelector("svg#mg-stage-overlay rect.mg-stage-scene-region")?.classList.contains("is-active");
            const charRectActive = document.querySelector("svg#mg-stage-overlay rect.mg-stage-char-instance")?.classList.contains("is-active");
            const castRefWrapDisplay = document.getElementById("scene-composer-cast-reference-wrap")?.style.display;
            return {
                activeTab: session.activeTab,
                selectedSceneId: session.selectedSceneId,
                selectedInstanceId: session.selectedInstanceId,
                promptTarget: getComposerPromptTarget(),
                promptVal,
                handles,
                sceneRectActive,
                charRectActive,
                castRefWrapDisplay
            };
        });

        assert.equal(stateC.activeTab, "scenes", "Active tab must switch back to 'scenes'");
        assert.equal(stateC.selectedSceneId, "scene_1", "Selected scene must be 'scene_1'");
        assert.equal(stateC.selectedInstanceId, null, "Instance selection must be cleared");
        assert.equal(stateC.promptTarget, "scene_1", "Prompt target must switch back to 'scene_1'");
        assert.ok(stateC.promptVal.includes("1girl standing"), "Prompt textarea must show scene prompt");
        assert.equal(stateC.handles, 4, "Scene must have 4 resize handles");
        assert.equal(stateC.sceneRectActive, true, "Scene rect must have .is-active class");
        assert.equal(stateC.charRectActive, false, "Character rect must NOT have .is-active class");
        assert.equal(stateC.castRefWrapDisplay, "none", "CAST Reference Hub must be hidden");

        const screenshotC = path.join(SCREENSHOT_DIR, `03_scene_reselected_${vp.name}.png`);
        await page.screenshot({ path: screenshotC });
        console.log(`✓ Test C PASS (${vp.name}). Screenshot: ${screenshotC}`);

        // ==============================================================
        // Test D: Drag and resize Scene on Stage
        // ==============================================================
        console.log("\n--- Test D: Drag and resize Scene on Stage ---");
        const initialSceneArea = await page.evaluate(() => window.__tegakiManga.store.getPage().scenes[0].area);
        
        // Drag Scene body by +20px x, +20px y
        const sBox = await sceneRect.boundingBox();
        await page.mouse.move(sBox.x + sBox.width * 0.85, sBox.y + sBox.height * 0.3);
        await page.mouse.down();
        await page.mouse.move(sBox.x + sBox.width * 0.85 + 25, sBox.y + sBox.height * 0.3 + 25, { steps: 5 });
        await page.mouse.up();
        await page.waitForTimeout(300);

        const movedSceneArea = await page.evaluate(() => window.__tegakiManga.store.getPage().scenes[0].area);
        assert.notEqual(movedSceneArea.x, initialSceneArea.x, "Scene X must update after drag");
        assert.notEqual(movedSceneArea.y, initialSceneArea.y, "Scene Y must update after drag");

        // Drag SE resize handle
        const seHandle = page.locator('svg#mg-stage-overlay rect.mg-stage-resize-handle[data-handle="se"]');
        assert.equal(await seHandle.count(), 1, "SE handle must exist for scene");
        const seBox = await seHandle.boundingBox();
        await page.mouse.move(seBox.x + seBox.width / 2, seBox.y + seBox.height / 2);
        await page.mouse.down();
        await page.mouse.move(seBox.x + seBox.width / 2 - 20, seBox.y + seBox.height / 2 - 20, { steps: 5 });
        await page.mouse.up();
        await page.waitForTimeout(300);

        const resizedSceneArea = await page.evaluate(() => window.__tegakiManga.store.getPage().scenes[0].area);
        assert.notEqual(resizedSceneArea.w, movedSceneArea.w, "Scene width must update after resize");
        assert.notEqual(resizedSceneArea.h, movedSceneArea.h, "Scene height must update after resize");

        const screenshotD = path.join(SCREENSHOT_DIR, `04_scene_dragged_resized_${vp.name}.png`);
        await page.screenshot({ path: screenshotD });
        console.log(`✓ Test D PASS (${vp.name}). Screenshot: ${screenshotD}`);

        // ==============================================================
        // Test E: Drag and resize Character Instance on Stage
        // ==============================================================
        console.log("\n--- Test E: Drag and resize Character Instance on Stage ---");
        // Click directly on Character Instance to select it
        const cRect = page.locator("svg#mg-stage-overlay rect.mg-stage-char-instance");
        const initialInstArea = await page.evaluate(() => window.__tegakiManga.store.getPage().character_instances[0].area);
        
        // Drag Character Instance by +15px, +15px
        const cBox = await cRect.boundingBox();
        await page.mouse.move(cBox.x + cBox.width / 2, cBox.y + cBox.height / 2);
        await page.mouse.down();
        await page.mouse.move(cBox.x + cBox.width / 2 + 15, cBox.y + cBox.height / 2 + 15, { steps: 5 });
        await page.mouse.up();
        await page.waitForTimeout(300);

        const movedInstArea = await page.evaluate(() => window.__tegakiManga.store.getPage().character_instances[0].area);
        assert.notEqual(movedInstArea.x, initialInstArea.x, "Instance X must update after drag");
        assert.notEqual(movedInstArea.y, initialInstArea.y, "Instance Y must update after drag");

        // Drag Instance SE resize handle
        const instSeHandle = page.locator('svg#mg-stage-overlay rect.mg-stage-resize-handle[data-handle="se"]');
        assert.equal(await instSeHandle.count(), 1, "SE handle must exist for character instance");
        const instSeBox = await instSeHandle.boundingBox();
        await page.mouse.move(instSeBox.x + instSeBox.width / 2, instSeBox.y + instSeBox.height / 2);
        await page.mouse.down();
        await page.mouse.move(instSeBox.x + instSeBox.width / 2 - 15, instSeBox.y + instSeBox.height / 2 - 15, { steps: 5 });
        await page.mouse.up();
        await page.waitForTimeout(300);

        const resizedInstArea = await page.evaluate(() => window.__tegakiManga.store.getPage().character_instances[0].area);
        assert.notEqual(resizedInstArea.w, movedInstArea.w, "Instance width must update after resize");
        assert.notEqual(resizedInstArea.h, movedInstArea.h, "Instance height must update after resize");

        const screenshotE = path.join(SCREENSHOT_DIR, `05_instance_dragged_resized_${vp.name}.png`);
        await page.screenshot({ path: screenshotE });
        console.log(`✓ Test E PASS (${vp.name}). Screenshot: ${screenshotE}`);

        // ==============================================================
        // Test F: Prompt Target Button Synchronization from Create
        // ==============================================================
        console.log("\n--- Test F: Prompt Target Button Synchronization from Create ---");
        // Click Global style prompt tab
        await page.click("#scene-prompt-tab-global");
        await page.waitForTimeout(200);

        const stateF1 = await page.evaluate(() => {
            const { session, getComposerPromptTarget } = window.__tegakiManga;
            return {
                promptTarget: getComposerPromptTarget(),
                activeTab: session.activeTab,
                sceneHandles: document.querySelectorAll("svg#mg-stage-overlay .mg-stage-resize-handle").length
            };
        });
        assert.equal(stateF1.promptTarget, "global", "Prompt target must be 'global'");
        assert.equal(stateF1.sceneHandles, 0, "No resize handles when Global tab is selected");

        // Click Scene tab in Create
        await page.click("#scene-prompt-tab-scene_1");
        await page.waitForTimeout(200);

        const stateF2 = await page.evaluate(() => {
            const { session, getComposerPromptTarget } = window.__tegakiManga;
            return {
                promptTarget: getComposerPromptTarget(),
                selectedSceneId: session.selectedSceneId,
                activeTab: session.activeTab,
                sceneHandles: document.querySelectorAll("svg#mg-stage-overlay .mg-stage-resize-handle").length
            };
        });
        assert.equal(stateF2.promptTarget, "scene_1", "Prompt target must be 'scene_1'");
        assert.equal(stateF2.selectedSceneId, "scene_1", "Selected scene must be 'scene_1'");
        assert.equal(stateF2.activeTab, "scenes", "Active tab must be 'scenes'");
        assert.equal(stateF2.sceneHandles, 4, "Scene must have 4 handles");

        // Click CAST Hero tab in Create
        await page.click("#scene-prompt-tab-cast_hero");
        await page.waitForTimeout(200);

        const stateF3 = await page.evaluate(() => {
            const { session, getComposerPromptTarget } = window.__tegakiManga;
            return {
                promptTarget: getComposerPromptTarget(),
                selectedCastId: session.selectedCastId,
                activeTab: session.activeTab
            };
        });
        assert.equal(stateF3.promptTarget, "cast_hero", "Prompt target must be 'cast_hero'");
        assert.equal(stateF3.selectedCastId, "hero", "Selected CAST must be 'hero'");
        assert.equal(stateF3.activeTab, "cast", "Active tab must be 'cast'");

        console.log(`✓ Test F PASS (${vp.name})`);

        // ==============================================================
        // Test G: Stage Mode Toggle & Persistence
        // ==============================================================
        console.log("\n--- Test G: Stage Mode Toggle & Persistence ---");
        // Switch to Result mode
        await page.click("#mg-stage-mode-result");
        await page.waitForTimeout(200);

        const resultDisplay = await page.evaluate(() => {
            return document.getElementById("mg-stage-overlay")?.style.display;
        });
        assert.equal(resultDisplay, "none", "Stage overlay must be hidden in Result mode");

        // Switch back to Layout mode
        await page.click("#mg-stage-mode-layout");
        await page.waitForTimeout(200);

        const layoutDisplay = await page.evaluate(() => {
            return document.getElementById("mg-stage-overlay")?.style.display;
        });
        assert.equal(layoutDisplay, "block", "Stage overlay must be visible in Layout mode");

        const screenshotG = path.join(SCREENSHOT_DIR, `06_stage_mode_restored_${vp.name}.png`);
        await page.screenshot({ path: screenshotG });
        console.log(`✓ Test G PASS (${vp.name}). Screenshot: ${screenshotG}`);

        // ==============================================================
        // Test H: Guide Raster Non-Interference
        // ==============================================================
        console.log("\n--- Test H: Guide Raster Non-Interference ---");
        const guideRasterInfo = await page.evaluate(() => {
            const img = document.querySelector("svg#mg-stage-overlay image.mg-stage-guide-raster");
            if (!img) return null;
            const style = window.getComputedStyle(img);
            return {
                hasRaster: true,
                pointerEvents: style.pointerEvents,
                href: img.getAttribute("href")
            };
        });
        assert.ok(guideRasterInfo, "Guide raster underlay must exist");
        assert.equal(guideRasterInfo.pointerEvents, "none", "Guide raster must have pointer-events: none");
        console.log(`✓ Test H PASS (${vp.name})`);

        // ==============================================================
        // Test I: Generation Scope Decoupling
        // ==============================================================
        console.log("\n--- Test I: Generation Scope Decoupling ---");
        // Select Scene first
        await page.click("#scene-prompt-tab-scene_1");
        await page.waitForTimeout(100);

        // Click Generation Scope: Global
        await page.click("#mg-generation-scope-global");
        await page.waitForTimeout(100);

        const scopeGlobalCheck = await page.evaluate(() => {
            const { session, getComposerPromptTarget } = window.__tegakiManga;
            return {
                promptTarget: getComposerPromptTarget(),
                selectedScene: session.selectedSceneId,
                scope: document.querySelector('#mg-generation-scope-global')?.getAttribute("aria-pressed")
            };
        });
        assert.equal(scopeGlobalCheck.promptTarget, "scene_1", "Changing scope to global must NOT change composer prompt target");
        assert.equal(scopeGlobalCheck.selectedScene, "scene_1", "Selected scene must remain intact");

        // Click Generation Scope: Scenes
        await page.click("#mg-generation-scope-scenes");
        await page.waitForTimeout(100);

        const scopeScenesCheck = await page.evaluate(() => {
            const { session, getComposerPromptTarget } = window.__tegakiManga;
            return {
                promptTarget: getComposerPromptTarget(),
                selectedScene: session.selectedSceneId,
                scope: document.querySelector('#mg-generation-scope-scenes')?.getAttribute("aria-pressed")
            };
        });
        assert.equal(scopeScenesCheck.promptTarget, "scene_1", "Changing scope to scenes must NOT change composer prompt target");
        assert.equal(scopeScenesCheck.selectedScene, "scene_1", "Selected scene must remain intact");

        console.log(`✓ Test I PASS (${vp.name})`);

        await context.close();
    }

    await browser.close();
    console.log("\n==================================================");
    console.log("ALL STAGE DIRECT SELECTION ACCEPTANCE TESTS PASSED!");
    console.log("==================================================");
}

runStageDirectSelectionAcceptance().catch(err => {
    console.error("FATAL ERROR in direct selection acceptance:", err);
    process.exit(1);
});
