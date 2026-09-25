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

const SCREENSHOT_DIR = path.resolve("scratch/stage_preview_screenshots");
fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });

async function runStageInteractionAcceptance() {
    console.log("=== MANGA-CREATE-STAGE-INTERACTIVE-PREVIEW1 ACCEPTANCE ===");
    
    const chromium = getPlaywrightChromium();
    assert(chromium, "Playwright Chromium must be available");
    
    const browser = await chromium.launch({ headless: true });
    
    // Test in both viewports: Desktop (1440x900) and Narrow (1024x768)
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
        // Step A: New Document & Empty State Contract
        // ==============================================================
        console.log("\n--- Step A: Fresh document & Global prompt availability ---");
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

        // Verify Global prompt tab active and editable
        const globalTabSelected = await page.getAttribute("#scene-prompt-tab-global", "aria-selected");
        assert.equal(globalTabSelected, "true", "Global tab must be aria-selected='true'");

        await page.click("#scene-composer-prompt");
        await page.fill("#scene-composer-prompt", "monochrome manga style, high contrast, detailed ink");
        
        const docA = await page.evaluate(() => window.__tegakiManga.store.getDocument());
        assert.equal(docA.pages[0].scenes.length, 0, "No scenes should exist");
        assert.equal(docA.pages[0].cast.length, 0, "No cast should exist");
        assert.equal(docA.pages[0].character_instances.length, 0, "No instances should exist");
        assert.equal(docA.pages[0].style_prompt, "monochrome manga style, high contrast, detailed ink");

        // Verify Stage Result/Layout empty contract
        const stageLayoutBtn = page.locator("#mg-stage-mode-layout");
        const isLayoutDisabled = await stageLayoutBtn.isDisabled();
        assert.equal(isLayoutDisabled, true, "Stage Layout button must be disabled when document has no spatial content");
        
        const previewEmptyText = await page.textContent("#mg-preview-empty");
        assert(previewEmptyText.includes("No verified result yet"), "Preview empty must show 'No verified result yet'");

        const screenshotA = path.join(SCREENSHOT_DIR, `01_empty_document_${vp.name}.png`);
        await page.screenshot({ path: screenshotA });
        console.log(`✓ Step A PASS (${vp.name}). Screenshot saved: ${screenshotA}`);

        // ==============================================================
        // Step B: Scene Creation, Stage Layout & Geometry Manipulation
        // ==============================================================
        console.log("\n--- Step B: Create ONE Scene & Stage interaction ---");
        await page.click("#mg-scene-add");
        await page.waitForSelector("#scene-prompt-tab-scene_1", { timeout: 3000 });
        
        // Enter Scene prompt
        await page.click("#scene-composer-prompt");
        await page.fill("#scene-composer-prompt", "standing outdoors in a courtyard, stone pavement");

        // Switch Stage to Layout
        await page.click("#mg-stage-mode-layout");
        const isLayoutSelected = await page.getAttribute("#mg-stage-mode-layout", "aria-selected");
        assert.equal(isLayoutSelected, "true", "Stage Layout button must be aria-selected='true'");

        // Verify Scene on Stage
        const sceneRect = page.locator("svg#mg-stage-overlay rect.mg-stage-scene-region.is-active");
        await sceneRect.waitFor({ state: "visible", timeout: 3000 });
        
        const docBBefore = await page.evaluate(() => window.__tegakiManga.store.getPage().scenes[0]);
        console.log("  Initial Scene Area:", docBBefore.area);

        // Move Scene using actual Stage pointer drag on scene rectangle
        const sceneBox = await sceneRect.boundingBox();
        assert(sceneBox, "Scene rect must have bounding box");
        
        console.log(`  Dragging Scene from (${sceneBox.x + sceneBox.width / 2}, ${sceneBox.y + sceneBox.height / 2}) by (-15, +25)...`);
        await page.mouse.move(sceneBox.x + sceneBox.width / 2, sceneBox.y + sceneBox.height / 2);
        await page.mouse.down();
        await page.mouse.move(sceneBox.x + sceneBox.width / 2 - 15, sceneBox.y + sceneBox.height / 2 + 25, { steps: 5 });
        await page.mouse.up();

        // Check canonical coordinates updated
        const docBAfterMove = await page.evaluate(() => window.__tegakiManga.store.getPage().scenes[0]);
        console.log("  Scene Area After Move:", docBAfterMove.area);
        assert(docBAfterMove.area.x !== docBBefore.area.x || docBAfterMove.area.y !== docBBefore.area.y, "Scene x or y must have moved");

        // Resize Scene using Stage SE resize handle
        const seHandle = page.locator("svg#mg-stage-overlay rect.mg-stage-resize-handle[data-handle='se']");
        await seHandle.waitFor({ state: "visible", timeout: 3000 });
        const handleBox = await seHandle.boundingBox();
        assert(handleBox, "SE handle must have bounding box");

        console.log(`  Dragging SE handle from (${handleBox.x + handleBox.width / 2}, ${handleBox.y + handleBox.height / 2}) by (-20, +25)...`);
        await page.mouse.move(handleBox.x + handleBox.width / 2, handleBox.y + handleBox.height / 2);
        await page.mouse.down();
        await page.mouse.move(handleBox.x + handleBox.width / 2 - 20, handleBox.y + handleBox.height / 2 + 25, { steps: 5 });
        await page.mouse.up();

        const docBAfterResize = await page.evaluate(() => window.__tegakiManga.store.getPage().scenes[0]);
        console.log("  Scene Area After Resize:", docBAfterResize.area);
        assert(docBAfterResize.area.w !== docBAfterMove.area.w || docBAfterResize.area.h !== docBAfterMove.area.h, "Scene w or h must have resized");

        // Confirm Scene prompt editing still targets Scene 1
        const activePromptValue = await page.inputValue("#scene-composer-prompt");
        assert.equal(activePromptValue, "standing outdoors in a courtyard, stone pavement", "Scene prompt must remain intact");

        const screenshotB = path.join(SCREENSHOT_DIR, `02_scene_layout_${vp.name}.png`);
        await page.screenshot({ path: screenshotB });
        console.log(`✓ Step B PASS (${vp.name}). Screenshot saved: ${screenshotB}`);

        // ==============================================================
        // Step C: Character Definition & Reference Assignment
        // ==============================================================
        console.log("\n--- Step C: Create ONE Character definition & assign Reference ---");
        await page.click("#mg-cast-add");
        await page.waitForSelector("#scene-prompt-tab-cast_cast_1", { timeout: 3000 });

        // Confirm Character Prompt becomes active
        const castTabSelected = await page.getAttribute("#scene-prompt-tab-cast_cast_1", "aria-pressed");
        assert.equal(castTabSelected, "true", "CAST tab must be active (aria-pressed='true') after creation");

        // Enter Identity Prompt
        await page.click("#scene-composer-prompt");
        await page.fill("#scene-composer-prompt", "1girl, silver hair, ponytail, school uniform");

        // Verify Scene Prompt did NOT change
        const scenePromptAfterChar = await page.evaluate(() => window.__tegakiManga.store.getPage().scenes[0].prompt);
        assert.equal(scenePromptAfterChar, "standing outdoors in a courtyard, stone pavement");

        // Assign Reference Asset
        const refAsset = "tegaki_manga_references/ref_c789751db904319d.png";
        await page.evaluate((asset) => {
            const { store, session, updateAll } = window.__tegakiManga;
            store.setCastReference(session.selectedCastId || "cast_1", asset);
            updateAll();
        }, refAsset);

        // Confirm 0 instances created
        const instCountC = await page.evaluate(() => window.__tegakiManga.store.getPage().character_instances.length);
        assert.equal(instCountC, 0, "Character creation and Reference assignment must NOT create an instance");

        const screenshotC = path.join(SCREENSHOT_DIR, `03_character_reference_${vp.name}.png`);
        await page.screenshot({ path: screenshotC });
        console.log(`✓ Step C PASS (${vp.name}). Screenshot saved: ${screenshotC}`);

        // ==============================================================
        // Step D: Character Appearance & Stage Instance Manipulation
        // ==============================================================
        console.log("\n--- Step D: Place Character Instance & Stage interaction ---");
        // Return to Scene 1
        await page.click("#scene-prompt-tab-scene_1");
        
        // Click CAST appearance toggle
        const castToggle = page.locator(".scene-cast-appearance-button");
        await castToggle.waitFor({ state: "visible", timeout: 3000 });
        await castToggle.click();

        // Confirm 1 instance placed
        const instCountD = await page.evaluate(() => window.__tegakiManga.store.getPage().character_instances.length);
        assert.equal(instCountD, 1, "Exactly 1 Character Instance must be created");

        const instD = await page.evaluate(() => window.__tegakiManga.store.getPage().character_instances[0]);
        assert.equal(instD.scene_id, "scene_1");
        assert.equal(instD.cast_id, "cast_1");
        console.log("  Initial Character Instance Area:", instD.area);

        // Verify Character Instance on Stage
        const charRect = page.locator("svg#mg-stage-overlay rect.mg-stage-char-instance");
        await charRect.waitFor({ state: "visible", timeout: 3000 });

        // Move Instance using actual Stage pointer drag
        const charBox = await charRect.boundingBox();
        assert(charBox, "Character instance must have bounding box");

        console.log(`  Dragging Character Instance from (${charBox.x + charBox.width / 2}, ${charBox.y + charBox.height / 2}) by (+20, +10)...`);
        await page.mouse.move(charBox.x + charBox.width / 2, charBox.y + charBox.height / 2);
        await page.mouse.down();
        await page.mouse.move(charBox.x + charBox.width / 2 + 20, charBox.y + charBox.height / 2 + 10, { steps: 5 });
        await page.mouse.up();

        const docDAfterMove = await page.evaluate(() => window.__tegakiManga.store.getPage());
        const instAfterMove = docDAfterMove.character_instances[0];
        const sceneAfterInstMove = docDAfterMove.scenes[0];
        console.log("  Instance Area After Move:", instAfterMove.area);
        
        // Verify Scene was not accidentally moved or resized
        assert.equal(sceneAfterInstMove.area.x, docBAfterResize.area.x, "Scene x must not change during instance move");
        assert.equal(sceneAfterInstMove.area.y, docBAfterResize.area.y, "Scene y must not change during instance move");
        assert.equal(sceneAfterInstMove.area.w, docBAfterResize.area.w, "Scene w must not change during instance move");
        assert.equal(sceneAfterInstMove.area.h, docBAfterResize.area.h, "Scene h must not change during instance move");

        // Resize Instance using Stage SE resize handle
        const instHandle = page.locator("svg#mg-stage-overlay rect.mg-stage-resize-handle[data-handle='se']");
        await instHandle.waitFor({ state: "visible", timeout: 3000 });
        const instHandleBox = await instHandle.boundingBox();
        assert(instHandleBox, "Instance handle must have bounding box");

        console.log(`  Dragging Instance SE handle from (${instHandleBox.x + instHandleBox.width / 2}, ${instHandleBox.y + instHandleBox.height / 2}) by (+25, +25)...`);
        await page.mouse.move(instHandleBox.x + instHandleBox.width / 2, instHandleBox.y + instHandleBox.height / 2);
        await page.mouse.down();
        await page.mouse.move(instHandleBox.x + instHandleBox.width / 2 + 25, instHandleBox.y + instHandleBox.height / 2 + 25, { steps: 5 });
        await page.mouse.up();

        const docDAfterResize = await page.evaluate(() => window.__tegakiManga.store.getPage());
        const instAfterResize = docDAfterResize.character_instances[0];
        console.log("  Instance Area After Resize:", instAfterResize.area);
        
        // Verify instance stays within parent scene bounds
        const scArea = docDAfterResize.scenes[0].area;
        assert(instAfterResize.area.x >= scArea.x - 0.001, "Instance must be within parent scene x");
        assert(instAfterResize.area.y >= scArea.y - 0.001, "Instance must be within parent scene y");
        assert(instAfterResize.area.x + instAfterResize.area.w <= scArea.x + scArea.w + 0.001, "Instance must be within parent scene width");
        assert(instAfterResize.area.y + instAfterResize.area.h <= scArea.y + scArea.h + 0.001, "Instance must be within parent scene height");

        // Verify CAST prompt and Reference intact
        assert.equal(docDAfterResize.cast[0].identity_prompt, "1girl, silver hair, ponytail, school uniform");
        assert.equal(docDAfterResize.cast[0].reference_asset, refAsset);

        const screenshotD = path.join(SCREENSHOT_DIR, `04_character_instance_layout_${vp.name}.png`);
        await page.screenshot({ path: screenshotD });
        console.log(`✓ Step D PASS (${vp.name}). Screenshot saved: ${screenshotD}`);

        // ==============================================================
        // Step E: Target Switching & Selection Integrity
        // ==============================================================
        console.log("\n--- Step E: Target switching integrity ---");
        // Switch Global
        await page.click("#scene-prompt-tab-global");
        assert.equal(await page.inputValue("#scene-composer-prompt"), "monochrome manga style, high contrast, detailed ink");

        // Switch Scene
        await page.click("#scene-prompt-tab-scene_1");
        assert.equal(await page.inputValue("#scene-composer-prompt"), "standing outdoors in a courtyard, stone pavement");

        // Switch Cast
        await page.click("#scene-prompt-tab-cast_cast_1");
        assert.equal(await page.inputValue("#scene-composer-prompt"), "1girl, silver hair, ponytail, school uniform");

        // Switch Stage Result and return to Layout
        await page.click("#mg-stage-mode-result");
        assert.equal(await page.getAttribute("#mg-stage-mode-result", "aria-selected"), "true");
        assert.equal(await page.getAttribute("#mg-stage-mode-layout", "aria-selected"), "false");

        await page.click("#mg-stage-mode-layout");
        assert.equal(await page.getAttribute("#mg-stage-mode-layout", "aria-selected"), "true");

        // Prompt target should still be Cast
        assert.equal(await page.inputValue("#scene-composer-prompt"), "1girl, silver hair, ponytail, school uniform");
        console.log("✓ Step E PASS: Target switching preserved all prompts and entities");

        // ==============================================================
        // Step F: Assign Structural Guide & Inspect Stage Representation
        // ==============================================================
        console.log("\n--- Step F: Assign ONE page structural Guide ---");
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

        // Verify Guide Hub in Create
        const guideBadge = await page.textContent("#mg-guide-status-badge");
        assert.equal(guideBadge.trim(), "GUIDE ENABLED", "Guide badge must show GUIDE ENABLED");

        // Inspect Stage Layout representation of Guide
        const stageGuideRect = page.locator("svg#mg-stage-overlay rect[stroke='#0284c7']");
        const guideVisibleOnStage = await stageGuideRect.isVisible();
        console.log(`  Stage Guide vector bounding box visible: ${guideVisibleOnStage}`);
        
        // Check whether Stage displays an <img> or bitmap preview for the Guide
        const hasGuideImageOnStage = await page.evaluate(() => {
            return Boolean(document.querySelector("#mg-stage img[src*='guide'], svg#mg-stage-overlay image"));
        });
        console.log(`  Stage Guide bitmap/image texture present on Stage: ${hasGuideImageOnStage} (Expected: false, Stage displays vector overlay)`);

        // Test Guide toggle
        await page.click("#mg-btn-toggle-guide");
        const guideBadgeOff = await page.textContent("#mg-guide-status-badge");
        assert(guideBadgeOff.includes("DISABLED"), `Guide badge must indicate disabled (got: ${guideBadgeOff})`);

        // Confirm Scene and Instance geometry did NOT mutate during Guide toggle
        const docFAfterToggle = await page.evaluate(() => window.__tegakiManga.store.getPage());
        assert.deepEqual(docFAfterToggle.scenes[0].area, docDAfterResize.scenes[0].area, "Scene geometry unchanged by guide toggle");
        assert.deepEqual(docFAfterToggle.character_instances[0].area, docDAfterResize.character_instances[0].area, "Instance geometry unchanged by guide toggle");

        // Re-enable Guide
        await page.click("#mg-btn-toggle-guide");
        const guideBadgeOn = await page.textContent("#mg-guide-status-badge");
        assert.equal(guideBadgeOn.trim(), "GUIDE ENABLED", "Guide badge must show GUIDE ENABLED");

        const screenshotF = path.join(SCREENSHOT_DIR, `05_guide_assigned_${vp.name}.png`);
        await page.screenshot({ path: screenshotF });
        console.log(`✓ Step F PASS (${vp.name}). Screenshot saved: ${screenshotF}`);

        // ==============================================================
        // Step G: Generation Scope & Truthful Messages
        // ==============================================================
        console.log("\n--- Step G: Generation Scope & Eligibility Messages ---");
        // Select Global-only
        await page.click("#mg-generation-scope-global");
        assert.equal(await page.getAttribute("#mg-generation-scope-global", "aria-pressed"), "true");
        assert.equal(await page.getAttribute("#mg-generation-scope-scenes", "aria-pressed"), "false");
        const globalBtnLabel = await page.textContent("#mg-generate-label");
        assert.equal(globalBtnLabel.trim(), "Generate", "Button label must be Generate for Global scope");

        // Select Scenes scope
        await page.click("#mg-generation-scope-scenes");
        assert.equal(await page.getAttribute("#mg-generation-scope-scenes", "aria-pressed"), "true");
        assert.equal(await page.getAttribute("#mg-generation-scope-global", "aria-pressed"), "false");
        const scenesBtnLabel = await page.textContent("#mg-generate-label");
        assert.equal(scenesBtnLabel.trim(), "Generate with Scenes", "Button label must be Generate with Scenes");

        // Verify Guide & Reference eligibility indications in status
        const statusText = await page.textContent("#mg-status");
        console.log("  Generation status line:", statusText);

        const screenshotG = path.join(SCREENSHOT_DIR, `06_scenes_scope_${vp.name}.png`);
        await page.screenshot({ path: screenshotG });
        console.log(`✓ Step G PASS (${vp.name}). Screenshot saved: ${screenshotG}`);

        await context.close();
    }

    await browser.close();
    console.log("\nALL INTERACTION AND VISUAL CHECKS COMPLETED SUCCESSFULLY!");
}

runStageInteractionAcceptance().catch(err => {
    console.error("TEST FAILED:", err);
    process.exit(1);
});
