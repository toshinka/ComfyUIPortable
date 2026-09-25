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

const SCREENSHOT_DIR = path.resolve("scratch/multi_scene_authoring_screenshots");
fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });

async function runMultiSceneAuthoringFlowAcceptance() {
    console.log("=== MANGA-CREATE-STAGE-AUTHORING-FLOW-POLISH1 ACCEPTANCE ===");
    
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

        // Reset document to empty state
        await page.evaluate(() => {
            const { store, session, setMangaMode, updateAll } = window.__tegakiManga;
            const doc = store.getDocument();
            doc.pages[0].scenes = [];
            doc.pages[0].cast = [];
            doc.pages[0].character_instances = [];
            doc.pages[0].guides = [];
            doc.pages[0].style_prompt = "high quality manga line art, ink wash";
            doc.pages[0].style_negative_prompt = "photorealistic, saturated colors";
            store.setDocument(doc);
            session.selectScene(null);
            session.selectCast(null);
            session.selectInstance(null);
            session.selectGuide(null);
            setMangaMode("authoring");
            updateAll();
        });

        // ==============================================================
        // Step 5A: CREATE BOTH SCENES
        // ==============================================================
        console.log("\n--- Step 5A: Create Scene 1 and Scene 2 with distinct prompts ---");
        
        // Create Scene 1
        await page.click("#mg-scene-add");
        await page.waitForSelector("#scene-prompt-tab-scene_1", { timeout: 3000 });
        await page.fill("#scene-composer-prompt", "Scene 1 prompt: 1girl sitting on a chair, indoor room");
        
        // Create Scene 2
        await page.click("#mg-scene-add");
        await page.waitForSelector("#scene-prompt-tab-scene_2", { timeout: 3000 });
        await page.fill("#scene-composer-prompt", "Scene 2 prompt: 1boy standing near window, sunlight streaming in");

        // Position scenes initially left and right non-overlapping
        await page.evaluate(() => {
            const { store, updateAll } = window.__tegakiManga;
            store.resizeScene("scene_1", { shape_type: "rect", x: 0.05, y: 0.10, w: 0.42, h: 0.75 });
            store.resizeScene("scene_2", { shape_type: "rect", x: 0.53, y: 0.10, w: 0.42, h: 0.75 });
            updateAll();
        });

        // Verify Scene 1 tab selection
        await page.click("#scene-prompt-tab-scene_1");
        await page.waitForTimeout(200);
        const selScene1Check = await page.evaluate(() => {
            const { session, getComposerPromptTarget } = window.__tegakiManga;
            const promptVal = document.getElementById("scene-composer-prompt")?.value;
            const scene1Active = document.querySelector('svg#mg-stage-overlay rect.mg-stage-scene-region[data-scene-id="scene_1"]')?.classList.contains("is-active");
            return {
                selectedScene: session.selectedSceneId,
                target: getComposerPromptTarget(),
                promptVal,
                scene1Active
            };
        });
        assert.equal(selScene1Check.selectedScene, "scene_1", "Scene 1 must be selected in session");
        assert.equal(selScene1Check.target, "scene_1", "Prompt target must be 'scene_1'");
        assert.ok(selScene1Check.promptVal.includes("1girl sitting"), "Scene 1 prompt must be displayed");
        assert.equal(selScene1Check.scene1Active, true, "Scene 1 rect must have .is-active class");

        // Verify Scene 2 tab selection
        await page.click("#scene-prompt-tab-scene_2");
        await page.waitForTimeout(200);
        const selScene2Check = await page.evaluate(() => {
            const { session, getComposerPromptTarget } = window.__tegakiManga;
            const promptVal = document.getElementById("scene-composer-prompt")?.value;
            const scene2Active = document.querySelector('svg#mg-stage-overlay rect.mg-stage-scene-region[data-scene-id="scene_2"]')?.classList.contains("is-active");
            return {
                selectedScene: session.selectedSceneId,
                target: getComposerPromptTarget(),
                promptVal,
                scene2Active
            };
        });
        assert.equal(selScene2Check.selectedScene, "scene_2", "Scene 2 must be selected in session");
        assert.equal(selScene2Check.target, "scene_2", "Prompt target must be 'scene_2'");
        assert.ok(selScene2Check.promptVal.includes("1boy standing"), "Scene 2 prompt must be displayed");
        assert.equal(selScene2Check.scene2Active, true, "Scene 2 rect must have .is-active class");

        const screenshotA = path.join(SCREENSHOT_DIR, `01_both_scenes_visible_${vp.name}.png`);
        await page.screenshot({ path: screenshotA });
        console.log(`✓ Step 5A PASS (${vp.name}). Screenshot: ${screenshotA}`);

        // ==============================================================
        // Step 5B: STAGE DIRECT SELECTION
        // ==============================================================
        console.log("\n--- Step 5B: Stage direct selection between Scene 1 and Scene 2 ---");
        const s1Rect = page.locator('svg#mg-stage-overlay rect.mg-stage-scene-region[data-scene-id="scene_1"]');
        const s2Rect = page.locator('svg#mg-stage-overlay rect.mg-stage-scene-region[data-scene-id="scene_2"]');
        assert.equal(await s1Rect.count(), 1, "Scene 1 rect must exist on Stage");
        assert.equal(await s2Rect.count(), 1, "Scene 2 rect must exist on Stage");

        // Click Scene 1 on Stage
        const scene1Box = await s1Rect.boundingBox();
        assert(scene1Box, "Scene 1 bounding box must be available");
        await page.mouse.click(scene1Box.x + scene1Box.width / 2, scene1Box.y + scene1Box.height / 2);
        await page.waitForTimeout(200);

        const checkStageS1 = await page.evaluate(() => {
            const { session, getComposerPromptTarget } = window.__tegakiManga;
            const promptVal = document.getElementById("scene-composer-prompt")?.value;
            const s1Active = document.querySelector('svg#mg-stage-overlay rect.mg-stage-scene-region[data-scene-id="scene_1"]')?.classList.contains("is-active");
            const s2Active = document.querySelector('svg#mg-stage-overlay rect.mg-stage-scene-region[data-scene-id="scene_2"]')?.classList.contains("is-active");
            return {
                selectedScene: session.selectedSceneId,
                target: getComposerPromptTarget(),
                promptVal,
                s1Active,
                s2Active
            };
        });
        assert.equal(checkStageS1.selectedScene, "scene_1", "Direct click on Stage must select Scene 1");
        assert.equal(checkStageS1.target, "scene_1", "Prompt target must be 'scene_1'");
        assert.ok(checkStageS1.promptVal.includes("1girl sitting"), "Scene 1 prompt must be shown");
        assert.equal(checkStageS1.s1Active, true, "Scene 1 rect must be active");
        assert.equal(checkStageS1.s2Active, false, "Scene 2 rect must NOT be active");

        // Click Scene 2 on Stage
        const scene2Box = await s2Rect.boundingBox();
        assert(scene2Box, "Scene 2 bounding box must be available");
        await page.mouse.click(scene2Box.x + scene2Box.width / 2, scene2Box.y + scene2Box.height / 2);
        await page.waitForTimeout(200);

        const checkStageS2 = await page.evaluate(() => {
            const { store, session, getComposerPromptTarget } = window.__tegakiManga;
            const promptVal = document.getElementById("scene-composer-prompt")?.value;
            const s1Active = document.querySelector('svg#mg-stage-overlay rect.mg-stage-scene-region[data-scene-id="scene_1"]')?.classList.contains("is-active");
            const s2Active = document.querySelector('svg#mg-stage-overlay rect.mg-stage-scene-region[data-scene-id="scene_2"]')?.classList.contains("is-active");
            const s1PromptInStore = store.getPage().scenes.find(s => s.scene_id === "scene_1")?.prompt;
            return {
                selectedScene: session.selectedSceneId,
                target: getComposerPromptTarget(),
                promptVal,
                s1Active,
                s2Active,
                s1PromptInStore
            };
        });
        assert.equal(checkStageS2.selectedScene, "scene_2", "Direct click on Stage must select Scene 2");
        assert.equal(checkStageS2.target, "scene_2", "Prompt target must be 'scene_2'");
        assert.ok(checkStageS2.promptVal.includes("1boy standing"), "Scene 2 prompt must be shown");
        assert.equal(checkStageS2.s2Active, true, "Scene 2 rect must be active");
        assert.equal(checkStageS2.s1Active, false, "Scene 1 rect must NOT be active");
        assert.ok(checkStageS2.s1PromptInStore.includes("1girl sitting"), "Inactive Scene 1 must retain its prompt");

        const screenshotB = path.join(SCREENSHOT_DIR, `02_scene2_selected_${vp.name}.png`);
        await page.screenshot({ path: screenshotB });

        // Click Scene 1 on Stage again
        await page.mouse.click(scene1Box.x + scene1Box.width / 2, scene1Box.y + scene1Box.height / 2);
        await page.waitForTimeout(200);

        const checkStageS1Again = await page.evaluate(() => {
            const { store, session, getComposerPromptTarget } = window.__tegakiManga;
            const promptVal = document.getElementById("scene-composer-prompt")?.value;
            const s2PromptInStore = store.getPage().scenes.find(s => s.scene_id === "scene_2")?.prompt;
            return {
                selectedScene: session.selectedSceneId,
                target: getComposerPromptTarget(),
                promptVal,
                s2PromptInStore
            };
        });
        assert.equal(checkStageS1Again.selectedScene, "scene_1", "Scene 1 must be reselected");
        assert.ok(checkStageS1Again.promptVal.includes("1girl sitting"), "Scene 1 prompt must be restored");
        assert.ok(checkStageS1Again.s2PromptInStore.includes("1boy standing"), "Scene 2 must retain its prompt");

        console.log(`✓ Step 5B PASS (${vp.name}). Screenshot: ${screenshotB}`);

        // ==============================================================
        // Step 5C: CAST DEFINITION AND APPEARANCE
        // ==============================================================
        console.log("\n--- Step 5C: Create CAST definition, assign Reference, place in Scene 1 ---");
        
        // Create CAST definition
        await page.click("#mg-cast-add");
        await page.waitForSelector(".scene-cast-identity-button", { timeout: 3000 });
        await page.fill("#scene-composer-prompt", "heroine, silver hair, combat suit, blue eyes");

        // Assign existing Reference image
        const refAsset = "tegaki_manga_references/ref_c789751db904319d.png";
        await page.evaluate((asset) => {
            const { store, session, updateAll } = window.__tegakiManga;
            store.assignCastReference(session.selectedCastId, asset);
            updateAll();
        }, refAsset);

        // Confirm Reference belongs to CAST definition and NO instance was created yet
        const checkCastSetup = await page.evaluate(() => {
            const { store } = window.__tegakiManga;
            const page = store.getPage();
            return {
                castCount: page.cast.length,
                castId: page.cast[0]?.cast_id,
                refAsset: page.cast[0]?.reference_asset,
                instanceCount: page.character_instances.length
            };
        });
        assert.equal(checkCastSetup.castCount, 1, "Exactly one CAST definition must exist");
        assert.equal(checkCastSetup.refAsset, refAsset, "Reference asset must be assigned to CAST");
        assert.equal(checkCastSetup.instanceCount, 0, "Reference assignment alone must NOT create a character instance");

        // Select Scene 1 first
        await page.click("#scene-prompt-tab-scene_1");
        await page.waitForTimeout(200);

        // Place one Character Instance inside Scene 1 using CAST appearance toggle
        const toggleButton = page.locator(".scene-cast-appearance-button");
        await toggleButton.click();
        await page.waitForTimeout(200);

        // Verify instance created and belongs ONLY to Scene 1
        const checkInstancePlacement = await page.evaluate(() => {
            const { store, session } = window.__tegakiManga;
            const page = store.getPage();
            const inst1 = page.character_instances.find(i => i.scene_id === "scene_1");
            const inst2 = page.character_instances.find(i => i.scene_id === "scene_2");
            return {
                totalInstances: page.character_instances.length,
                inst1Scene: inst1?.scene_id,
                inst1Cast: inst1?.cast_id,
                inst1Area: inst1?.area,
                hasScene2Instance: Boolean(inst2),
                sessionTab: session.activeTab,
                selectedInst: session.selectedInstanceId
            };
        });
        assert.equal(checkInstancePlacement.totalInstances, 1, "Exactly 1 character instance must exist");
        assert.equal(checkInstancePlacement.inst1Scene, "scene_1", "Instance must belong to Scene 1");
        assert.equal(checkInstancePlacement.inst1Cast, checkCastSetup.castId, "Instance must reference CAST");
        assert.equal(checkInstancePlacement.hasScene2Instance, false, "Scene 2 must have NO character instance");

        // Add structural Page Guide as Layout underlay
        const guideAsset = "tegaki_manga_guides/disposable_guide_single_character.png";
        await page.evaluate((asset) => {
            const { store, updateAll } = window.__tegakiManga;
            store.addGuideFromAsset({
                asset_reference: asset,
                image_width: 832,
                image_height: 1216
            });
            updateAll();
        }, guideAsset);

        console.log(`✓ Step 5C PASS (${vp.name})`);

        // ==============================================================
        // Step 5D: CROSS-TARGET SELECTION
        // Exact order: Scene 2 -> Scene 1 -> Character Instance -> Scene 2 -> Character Instance
        // ==============================================================
        console.log("\n--- Step 5D: Cross-target selection sequence ---");

        // 1) Select Scene 2 on Stage
        const s2BoxFresh = await s2Rect.boundingBox();
        await page.mouse.click(s2BoxFresh.x + s2BoxFresh.width / 2, s2BoxFresh.y + s2BoxFresh.height / 2);
        await page.waitForTimeout(200);

        const checkD1 = await page.evaluate(() => {
            const { session, getComposerPromptTarget } = window.__tegakiManga;
            const promptVal = document.getElementById("scene-composer-prompt")?.value;
            const handles = document.querySelectorAll("svg#mg-stage-overlay .mg-stage-resize-handle").length;
            const s2Active = document.querySelector('svg#mg-stage-overlay rect.mg-stage-scene-region[data-scene-id="scene_2"]')?.classList.contains("is-active");
            return {
                activeTab: session.activeTab,
                selectedScene: session.selectedSceneId,
                selectedInst: session.selectedInstanceId,
                target: getComposerPromptTarget(),
                promptVal,
                handles,
                s2Active
            };
        });
        assert.equal(checkD1.activeTab, "scenes", "D1: Active tab must be 'scenes'");
        assert.equal(checkD1.selectedScene, "scene_2", "D1: Scene 2 must be selected");
        assert.equal(checkD1.selectedInst, null, "D1: No instance selected");
        assert.equal(checkD1.target, "scene_2", "D1: Target must be 'scene_2'");
        assert.ok(checkD1.promptVal.includes("1boy standing"), "D1: Scene 2 prompt shown");
        assert.equal(checkD1.handles, 4, "D1: Scene 2 must have 4 handles");
        assert.equal(checkD1.s2Active, true, "D1: Scene 2 rect must be active");

        // 2) Select Scene 1 on Stage (click outside character instance)
        const s1BoxFresh = await s1Rect.boundingBox();
        await page.mouse.click(s1BoxFresh.x + s1BoxFresh.width / 2, s1BoxFresh.y + 20);
        await page.waitForTimeout(200);

        const checkD2 = await page.evaluate(() => {
            const { session, getComposerPromptTarget } = window.__tegakiManga;
            const promptVal = document.getElementById("scene-composer-prompt")?.value;
            const handles = document.querySelectorAll("svg#mg-stage-overlay .mg-stage-resize-handle").length;
            const s1Active = document.querySelector('svg#mg-stage-overlay rect.mg-stage-scene-region[data-scene-id="scene_1"]')?.classList.contains("is-active");
            const cActive = document.querySelector('svg#mg-stage-overlay rect[data-instance-id="inst_1"]')?.classList.contains("is-active");
            return {
                activeTab: session.activeTab,
                selectedScene: session.selectedSceneId,
                selectedInst: session.selectedInstanceId,
                target: getComposerPromptTarget(),
                promptVal,
                handles,
                s1Active,
                cActive
            };
        });
        assert.equal(checkD2.activeTab, "scenes", "D2: Active tab must be 'scenes'");
        assert.equal(checkD2.selectedScene, "scene_1", "D2: Scene 1 must be selected");
        assert.equal(checkD2.selectedInst, null, "D2: No instance selected");
        assert.equal(checkD2.target, "scene_1", "D2: Target must be 'scene_1'");
        assert.ok(checkD2.promptVal.includes("1girl sitting"), "D2: Scene 1 prompt shown");
        assert.equal(checkD2.handles, 4, "D2: Scene 1 must have 4 handles");
        assert.equal(checkD2.s1Active, true, "D2: Scene 1 rect active");
        assert.equal(checkD2.cActive, false, "D2: Instance rect NOT active");

        // 3) Select Character Instance on Stage
        const charRect = page.locator('svg#mg-stage-overlay rect[data-instance-id="inst_1"]');
        assert.equal(await charRect.count(), 1, "Character instance rect must exist");
        const charBox = await charRect.boundingBox();
        assert(charBox, "Character instance bounding box must be available");
        await page.mouse.click(charBox.x + charBox.width / 2, charBox.y + charBox.height / 2);
        await page.waitForTimeout(200);

        const checkD3 = await page.evaluate(() => {
            const { store, session, getComposerPromptTarget } = window.__tegakiManga;
            const promptVal = document.getElementById("scene-composer-prompt")?.value;
            const handles = document.querySelectorAll("svg#mg-stage-overlay .mg-stage-resize-handle").length;
            const cActive = document.querySelector('svg#mg-stage-overlay rect[data-instance-id="inst_1"]')?.classList.contains("is-active");
            const s1Active = document.querySelector('svg#mg-stage-overlay rect.mg-stage-scene-region[data-scene-id="scene_1"]')?.classList.contains("is-active");
            const castRefWrap = document.getElementById("scene-composer-cast-reference-wrap")?.style.display;
            const instCount = store.getPage().character_instances.length;
            return {
                activeTab: session.activeTab,
                selectedScene: session.selectedSceneId,
                selectedCast: session.selectedCastId,
                selectedInst: session.selectedInstanceId,
                target: getComposerPromptTarget(),
                promptVal,
                handles,
                cActive,
                s1Active,
                castRefWrap,
                instCount
            };
        });
        assert.equal(checkD3.activeTab, "cast", "D3: Active tab must switch to 'cast'");
        assert.equal(checkD3.selectedScene, "scene_1", "D3: Parent scene must be 'scene_1'");
        assert.equal(checkD3.selectedInst, "inst_1", "D3: Selected instance must be 'inst_1'");
        assert.ok(checkD3.target.includes("cast_1"), "D3: Target must reference cast_1");
        assert.ok(checkD3.promptVal.includes("heroine, silver hair"), "D3: CAST prompt shown");
        assert.equal(checkD3.handles, 4, "D3: Instance must have 4 handles");
        assert.equal(checkD3.cActive, true, "D3: Instance rect active");
        assert.equal(checkD3.s1Active, false, "D3: Scene 1 rect NOT active");
        assert.equal(checkD3.castRefWrap, "flex", "D3: CAST reference hub visible");
        assert.equal(checkD3.instCount, 1, "D3: Instance count must remain 1 (no silent creation/deletion)");

        const screenshotC = path.join(SCREENSHOT_DIR, `03_character_instance_selected_${vp.name}.png`);
        await page.screenshot({ path: screenshotC });

        // 4) Select Scene 2 on Stage
        await page.mouse.click(s2BoxFresh.x + s2BoxFresh.width / 2, s2BoxFresh.y + s2BoxFresh.height / 2);
        await page.waitForTimeout(200);

        const checkD4 = await page.evaluate(() => {
            const { session, getComposerPromptTarget } = window.__tegakiManga;
            const promptVal = document.getElementById("scene-composer-prompt")?.value;
            const handles = document.querySelectorAll("svg#mg-stage-overlay .mg-stage-resize-handle").length;
            const s2Active = document.querySelector('svg#mg-stage-overlay rect.mg-stage-scene-region[data-scene-id="scene_2"]')?.classList.contains("is-active");
            const cActive = document.querySelector('svg#mg-stage-overlay rect[data-instance-id="inst_1"]')?.classList.contains("is-active");
            return {
                activeTab: session.activeTab,
                selectedScene: session.selectedSceneId,
                selectedInst: session.selectedInstanceId,
                target: getComposerPromptTarget(),
                promptVal,
                handles,
                s2Active,
                cActive
            };
        });
        assert.equal(checkD4.activeTab, "scenes", "D4: Active tab must return to 'scenes'");
        assert.equal(checkD4.selectedScene, "scene_2", "D4: Scene 2 must be selected");
        assert.equal(checkD4.selectedInst, null, "D4: Instance deselected");
        assert.equal(checkD4.target, "scene_2", "D4: Target must be 'scene_2'");
        assert.ok(checkD4.promptVal.includes("1boy standing"), "D4: Scene 2 prompt shown");
        assert.equal(checkD4.handles, 4, "D4: Scene 2 has 4 handles");
        assert.equal(checkD4.s2Active, true, "D4: Scene 2 rect active");
        assert.equal(checkD4.cActive, false, "D4: Instance rect NOT active");

        // 5) Select Character Instance on Stage again
        await page.mouse.click(charBox.x + charBox.width / 2, charBox.y + charBox.height / 2);
        await page.waitForTimeout(200);

        const checkD5 = await page.evaluate(() => {
            const { session, getComposerPromptTarget } = window.__tegakiManga;
            const promptVal = document.getElementById("scene-composer-prompt")?.value;
            const handles = document.querySelectorAll("svg#mg-stage-overlay .mg-stage-resize-handle").length;
            const cActive = document.querySelector('svg#mg-stage-overlay rect[data-instance-id="inst_1"]')?.classList.contains("is-active");
            return {
                activeTab: session.activeTab,
                selectedScene: session.selectedSceneId,
                selectedInst: session.selectedInstanceId,
                target: getComposerPromptTarget(),
                promptVal,
                handles,
                cActive
            };
        });
        assert.equal(checkD5.activeTab, "cast", "D5: Active tab must switch to 'cast'");
        assert.equal(checkD5.selectedScene, "scene_1", "D5: Parent scene is Scene 1");
        assert.equal(checkD5.selectedInst, "inst_1", "D5: Selected instance is 'inst_1'");
        assert.ok(checkD5.target.includes("cast_1"), "D5: Target must reference cast_1");
        assert.equal(checkD5.handles, 4, "D5: Instance has 4 handles");
        assert.equal(checkD5.cActive, true, "D5: Instance rect active");

        console.log(`✓ Step 5D PASS (${vp.name}). Screenshot: ${screenshotC}`);

        // ==============================================================
        // Step 5E: GEOMETRY
        // ==============================================================
        console.log("\n--- Step 5E: Move and resize operations & relative placement ---");
        
        // 1) Move and resize Scene 2
        await page.mouse.click(s2BoxFresh.x + s2BoxFresh.width / 2, s2BoxFresh.y + s2BoxFresh.height / 2);
        await page.waitForTimeout(200);

        const s2InitialArea = await page.evaluate(() => window.__tegakiManga.store.getPage().scenes.find(s => s.scene_id === "scene_2").area);
        const s2FreshBox = await s2Rect.boundingBox();

        // Drag Scene 2 body
        await page.mouse.move(s2FreshBox.x + s2FreshBox.width / 2, s2FreshBox.y + s2FreshBox.height / 2);
        await page.mouse.down();
        await page.mouse.move(s2FreshBox.x + s2FreshBox.width / 2 + 15, s2FreshBox.y + s2FreshBox.height / 2 + 15, { steps: 5 });
        await page.mouse.up();
        await page.waitForTimeout(200);

        const s2MovedArea = await page.evaluate(() => window.__tegakiManga.store.getPage().scenes.find(s => s.scene_id === "scene_2").area);
        assert.notEqual(s2MovedArea.x, s2InitialArea.x, "Scene 2 X must update after drag");
        assert.notEqual(s2MovedArea.y, s2InitialArea.y, "Scene 2 Y must update after drag");

        // Drag Scene 2 SE resize handle
        const s2SeHandle = page.locator('svg#mg-stage-overlay rect.mg-stage-resize-handle[data-handle="se"]');
        assert.equal(await s2SeHandle.count(), 1, "SE handle must exist for Scene 2");
        await s2SeHandle.scrollIntoViewIfNeeded();
        const s2SeBox = await s2SeHandle.boundingBox();
        await page.mouse.move(s2SeBox.x + s2SeBox.width / 2, s2SeBox.y + s2SeBox.height / 2);
        await page.mouse.down();
        await page.mouse.move(s2SeBox.x + s2SeBox.width / 2 - 20, s2SeBox.y + s2SeBox.height / 2 - 20, { steps: 5 });
        await page.mouse.up();
        await page.waitForTimeout(200);

        const s2ResizedArea = await page.evaluate(() => window.__tegakiManga.store.getPage().scenes.find(s => s.scene_id === "scene_2").area);
        assert.notEqual(s2ResizedArea.w, s2MovedArea.w, "Scene 2 width must update after resize");
        assert.notEqual(s2ResizedArea.h, s2MovedArea.h, "Scene 2 height must update after resize");

        // 2) Move and resize Character Instance inside Scene 1
        const charFreshRect = page.locator('svg#mg-stage-overlay rect[data-instance-id="inst_1"]');
        await charFreshRect.scrollIntoViewIfNeeded();
        const charFreshBox = await charFreshRect.boundingBox();
        await page.mouse.click(charFreshBox.x + charFreshBox.width / 2, charFreshBox.y + charFreshBox.height / 2);
        await page.waitForTimeout(200);

        const instInitialArea = await page.evaluate(() => window.__tegakiManga.store.getPage().character_instances[0].area);
        
        // Drag Character Instance body
        await page.mouse.move(charFreshBox.x + charFreshBox.width / 2, charFreshBox.y + charFreshBox.height / 2);
        await page.mouse.down();
        await page.mouse.move(charFreshBox.x + charFreshBox.width / 2 + 10, charFreshBox.y + charFreshBox.height / 2 + 10, { steps: 5 });
        await page.mouse.up();
        await page.waitForTimeout(200);

        const instMovedArea = await page.evaluate(() => window.__tegakiManga.store.getPage().character_instances[0].area);
        assert.notEqual(instMovedArea.x, instInitialArea.x, "Instance X must update after drag");
        assert.notEqual(instMovedArea.y, instInitialArea.y, "Instance Y must update after drag");

        // Drag Character Instance SE handle
        const instSeHandle = page.locator('svg#mg-stage-overlay rect.mg-stage-resize-handle[data-handle="se"]');
        assert.equal(await instSeHandle.count(), 1, "SE handle must exist for character instance");
        await instSeHandle.scrollIntoViewIfNeeded();
        const instSeBox = await instSeHandle.boundingBox();
        await page.mouse.move(instSeBox.x + instSeBox.width / 2, instSeBox.y + instSeBox.height / 2);
        await page.mouse.down();
        await page.mouse.move(instSeBox.x + instSeBox.width / 2 - 12, instSeBox.y + instSeBox.height / 2 - 12, { steps: 5 });
        await page.mouse.up();
        await page.waitForTimeout(200);

        const instResizedArea = await page.evaluate(() => window.__tegakiManga.store.getPage().character_instances[0].area);
        assert.notEqual(instResizedArea.w, instMovedArea.w, "Instance width must update after resize");
        assert.notEqual(instResizedArea.h, instMovedArea.h, "Instance height must update after resize");

        // 3) Move Scene 1 with its child Instance
        const s1FreshRect = page.locator('svg#mg-stage-overlay rect.mg-stage-scene-region[data-scene-id="scene_1"]');
        await s1FreshRect.scrollIntoViewIfNeeded();
        const s1FreshBox = await s1FreshRect.boundingBox();
        
        // Click top part of Scene 1 to select Scene 1
        await page.mouse.click(s1FreshBox.x + s1FreshBox.width / 2, s1FreshBox.y + 15);
        await page.waitForTimeout(200);

        const s1BeforeDrag = await page.evaluate(() => window.__tegakiManga.store.getPage().scenes.find(s => s.scene_id === "scene_1").area);
        const instBeforeS1Drag = await page.evaluate(() => window.__tegakiManga.store.getPage().character_instances[0].area);
        const s2BeforeS1Drag = await page.evaluate(() => window.__tegakiManga.store.getPage().scenes.find(s => s.scene_id === "scene_2").area);

        // Relative offset of instance within Scene 1
        const relOffsetXBefore = instBeforeS1Drag.x - s1BeforeDrag.x;
        const relOffsetYBefore = instBeforeS1Drag.y - s1BeforeDrag.y;

        // Drag Scene 1 body by +20px, +20px
        await page.mouse.move(s1FreshBox.x + s1FreshBox.width / 2, s1FreshBox.y + 15);
        await page.mouse.down();
        await page.mouse.move(s1FreshBox.x + s1FreshBox.width / 2 + 20, s1FreshBox.y + 15 + 20, { steps: 5 });
        await page.mouse.up();
        await page.waitForTimeout(200);

        const s1AfterDrag = await page.evaluate(() => window.__tegakiManga.store.getPage().scenes.find(s => s.scene_id === "scene_1").area);
        const instAfterS1Drag = await page.evaluate(() => window.__tegakiManga.store.getPage().character_instances[0].area);
        const s2AfterS1Drag = await page.evaluate(() => window.__tegakiManga.store.getPage().scenes.find(s => s.scene_id === "scene_2").area);

        assert.notEqual(s1AfterDrag.x, s1BeforeDrag.x, "Scene 1 X must update after drag");
        assert.notEqual(s1AfterDrag.y, s1BeforeDrag.y, "Scene 1 Y must update after drag");

        // Verify child instance moved proportionally
        const relOffsetXAfter = instAfterS1Drag.x - s1AfterDrag.x;
        const relOffsetYAfter = instAfterS1Drag.y - s1AfterDrag.y;
        assert.ok(Math.abs(relOffsetXAfter - relOffsetXBefore) < 1e-3, "Relative X placement of child instance must be preserved");
        assert.ok(Math.abs(relOffsetYAfter - relOffsetYBefore) < 1e-3, "Relative Y placement of child instance must be preserved");

        // Confirm Scene 2 DID NOT MOVE
        assert.equal(s2AfterS1Drag.x, s2BeforeS1Drag.x, "Scene 2 X must remain unaffected when Scene 1 moves");
        assert.equal(s2AfterS1Drag.y, s2BeforeS1Drag.y, "Scene 2 Y must remain unaffected when Scene 1 moves");
        assert.equal(s2AfterS1Drag.w, s2BeforeS1Drag.w, "Scene 2 W must remain unaffected");
        assert.equal(s2AfterS1Drag.h, s2BeforeS1Drag.h, "Scene 2 H must remain unaffected");

        const screenshotD = path.join(SCREENSHOT_DIR, `04_scene1_after_moving_child_${vp.name}.png`);
        await page.screenshot({ path: screenshotD });
        console.log(`✓ Step 5E PASS (${vp.name}). Screenshot: ${screenshotD}`);

        // ==============================================================
        // Step 5F: GUIDE AND GENERATION SCOPE
        // ==============================================================
        console.log("\n--- Step 5F: Guide underlay & generation scope persistence ---");
        
        // Verify Guide raster is rendered as Layout underlay
        const guideRasterCount = await page.locator("svg#mg-stage-overlay image.mg-stage-guide-raster").count();
        assert.equal(guideRasterCount, 1, "Guide raster underlay must be present in Layout mode");

        // Switch generation scope to Global
        await page.click("#mg-generation-scope-global");
        await page.waitForTimeout(100);
        const checkScopeGlobal = await page.evaluate(() => {
            const { session, getComposerPromptTarget } = window.__tegakiManga;
            return {
                scope: document.querySelector('#mg-generation-scope-global')?.getAttribute("aria-pressed"),
                selectedScene: session.selectedSceneId,
                target: getComposerPromptTarget()
            };
        });
        assert.equal(checkScopeGlobal.scope, "true", "Global scope button must be pressed");
        assert.equal(checkScopeGlobal.selectedScene, "scene_1", "Editing target scene must NOT change when scope changes");
        assert.equal(checkScopeGlobal.target, "scene_1", "Prompt target must remain 'scene_1'");

        // Switch generation scope to Scenes
        await page.click("#mg-generation-scope-scenes");
        await page.waitForTimeout(100);
        const checkScopeScenes = await page.evaluate(() => {
            const { session, getComposerPromptTarget } = window.__tegakiManga;
            return {
                scope: document.querySelector('#mg-generation-scope-scenes')?.getAttribute("aria-pressed"),
                selectedScene: session.selectedSceneId,
                target: getComposerPromptTarget()
            };
        });
        assert.equal(checkScopeScenes.scope, "true", "Scenes scope button must be pressed");
        assert.equal(checkScopeScenes.selectedScene, "scene_1", "Editing target scene must NOT change when scope changes");

        // Switch to Result mode
        await page.click("#mg-stage-mode-result");
        await page.waitForTimeout(200);
        const resultDisplay = await page.evaluate(() => document.getElementById("mg-stage-overlay")?.style.display);
        assert.equal(resultDisplay, "none", "Stage overlay must be hidden in Result mode");

        // Switch back to Layout mode
        await page.click("#mg-stage-mode-layout");
        await page.waitForTimeout(200);
        const layoutDisplay = await page.evaluate(() => document.getElementById("mg-stage-overlay")?.style.display);
        assert.equal(layoutDisplay, "block", "Stage overlay must be restored in Layout mode");

        // Confirm authoring data preserved
        const finalDocCheck = await page.evaluate(() => {
            const { store, session, getComposerPromptTarget } = window.__tegakiManga;
            const p = store.getPage();
            return {
                sceneCount: p.scenes.length,
                castCount: p.cast.length,
                instCount: p.character_instances.length,
                guideCount: p.guides.length,
                s1Prompt: p.scenes.find(s => s.scene_id === "scene_1")?.prompt,
                s2Prompt: p.scenes.find(s => s.scene_id === "scene_2")?.prompt,
                castPrompt: p.cast[0]?.identity_prompt,
                selectedScene: session.selectedSceneId,
                target: getComposerPromptTarget()
            };
        });
        assert.equal(finalDocCheck.sceneCount, 2, "Both scenes must be preserved");
        assert.equal(finalDocCheck.castCount, 1, "CAST must be preserved");
        assert.equal(finalDocCheck.instCount, 1, "Character instance must be preserved");
        assert.equal(finalDocCheck.guideCount, 1, "Guide must be preserved");
        assert.ok(finalDocCheck.s1Prompt.includes("1girl sitting"), "Scene 1 prompt preserved");
        assert.ok(finalDocCheck.s2Prompt.includes("1boy standing"), "Scene 2 prompt preserved");
        assert.ok(finalDocCheck.castPrompt.includes("heroine, silver hair"), "CAST prompt preserved");

        const screenshotF = path.join(SCREENSHOT_DIR, `05_guide_underlay_scenes_scope_${vp.name}.png`);
        await page.screenshot({ path: screenshotF });
        console.log(`✓ Step 5F PASS (${vp.name}). Screenshot: ${screenshotF}`);

        await context.close();
    }

    await browser.close();
    console.log("\n==================================================");
    console.log("ALL MULTI-SCENE AUTHORING FLOW ACCEPTANCE TESTS PASSED!");
    console.log("==================================================");
}

runMultiSceneAuthoringFlowAcceptance().catch(err => {
    console.error("FATAL ERROR in multi-scene authoring acceptance:", err);
    process.exit(1);
});
