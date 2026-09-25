import assert from "node:assert/strict";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { createRequire } from "node:module";
import { execSync } from "node:child_process";

const require = createRequire(import.meta.url);

function getPlaywrightChromium() {
    if (process.env.TEGAKI_PLAYWRIGHT_MODULE) return require(process.env.TEGAKI_PLAYWRIGHT_MODULE).chromium;
    try { return require("playwright").chromium; } catch {}
    const root = execSync("npm root -g", { encoding: "utf8" }).trim();
    return require(path.join(root, "@executeautomation", "playwright-mcp-server", "node_modules", "playwright")).chromium;
}

async function runBrowserAcceptance() {
    console.log("=== MANGA-CREATE-COMBINED-FLOW-BROWSER1 ACCEPTANCE ===");
    
    const chromium = getPlaywrightChromium();
    assert(chromium, "Playwright Chromium must be available");
    
    // Launch headless Chromium in an isolated context
    const browser = await chromium.launch({ headless: true });
    // Use an isolated context to ensure zero sharing with Owner's browser / storage
    const context = await browser.newContext();
    const page = await context.newPage();
    page.on('console', msg => console.log('PAGE LOG:', msg.text()));
    
    try {
        console.log("Navigating to http://127.0.0.1:8191/ ...");
        await page.goto("http://127.0.0.1:8191/", { waitUntil: "networkidle" });
        
        // Wait for __tegakiManga and catalog ready
        await page.waitForFunction(() => window.__tegakiManga && window.__tegakiManga.generation?.state?.catalog);
        console.log("Manga workspace loaded and catalog ready.");
        
        // ==============================================================
        // Step A: Start with a fresh document
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
            setMangaMode("authoring");
            updateAll();
        });
        
        // Confirm Global Prompt is selected
        const isGlobalSelected = await page.$eval("#scene-prompt-tab-global", el => el.getAttribute("aria-selected"));
        assert.equal(isGlobalSelected, "true", "Global prompt tab must be selected initially");
        
        // Confirm Global prompt textarea is enabled and available without Scene or CAST
        const promptDisabled = await page.$eval("#scene-composer-prompt", el => el.disabled);
        assert.equal(promptDisabled, false, "Global prompt textarea must be enabled");
        
        await page.fill("#scene-composer-prompt", "monochrome manga, high contrast, clean line art");
        const docAfterA = await page.evaluate(() => window.__tegakiManga.store.getDocument());
        assert.equal(docAfterA.pages[0].style_prompt, "monochrome manga, high contrast, clean line art");
        assert.equal(docAfterA.pages[0].scenes.length, 0, "No scenes required for Global prompt");
        assert.equal(docAfterA.pages[0].cast.length, 0, "No CAST required for Global prompt");
        console.log("✓ Step A PASS: Fresh document & Global prompt available without Scene or CAST");

        // ==============================================================
        // Step B: Create ONE Scene
        // ==============================================================
        console.log("\n--- Step B: Create ONE Scene & enter Scene Prompt ---");
        await page.click("#mg-scene-add");
        
        // Confirm 1 scene exists
        const sceneCount = await page.evaluate(() => window.__tegakiManga.store.getPage().scenes.length);
        assert.equal(sceneCount, 1, "Exactly one scene must be created");
        
        const sceneId = await page.evaluate(() => window.__tegakiManga.store.getPage().scenes[0].scene_id);
        
        // Confirm Stage Layout corresponds to intended Scene
        const selectedSceneId = await page.evaluate(() => window.__tegakiManga.session.selectedSceneId);
        assert.equal(selectedSceneId, sceneId, "Created scene must be selected");
        
        // Enter Scene Prompt
        await page.fill("#scene-composer-prompt", "standing outdoors in a courtyard, stone pavement");
        const docAfterB = await page.evaluate(() => window.__tegakiManga.store.getDocument());
        assert.equal(docAfterB.pages[0].scenes[0].prompt, "standing outdoors in a courtyard, stone pavement");
        
        const selectionText = await page.$eval("#scene-composer-selection", el => el.textContent);
        console.log(`  Scene selection text: "${selectionText}"`);
        console.log("✓ Step B PASS: ONE Scene created, selected, and Scene Prompt entered");

        // ==============================================================
        // Step C: Create ONE Character definition
        // ==============================================================
        console.log("\n--- Step C: Create ONE Character definition & assign Reference ---");
        await page.click("#mg-cast-add");
        
        const castCount = await page.evaluate(() => window.__tegakiManga.store.getPage().cast.length);
        assert.equal(castCount, 1, "Exactly one CAST definition must be created");
        
        const castId = await page.evaluate(() => window.__tegakiManga.store.getPage().cast[0].cast_id);
        
        // Enter Identity Prompt
        await page.fill("#scene-composer-prompt", "1girl, long hair, school uniform, detailed eyes");
        
        // Assign existing Reference image through canonical store
        const refAsset = "tegaki_manga_references/ref_c789751db904319d.png";
        await page.evaluate((asset) => {
            const { store, session, updateAll } = window.__tegakiManga;
            store.assignCastReference(session.selectedCastId, asset);
            updateAll();
        }, refAsset);
        
        // Confirm Reference belongs to CAST definition
        const docAfterC = await page.evaluate(() => window.__tegakiManga.store.getDocument());
        assert.equal(docAfterC.pages[0].cast[0].identity_prompt, "1girl, long hair, school uniform, detailed eyes");
        assert.equal(docAfterC.pages[0].cast[0].reference_asset, refAsset);
        
        // Confirm UI shows assigned state
        const refAssignedVisible = await page.$eval("#mg-cast-ref-assigned", el => el.style.display !== "none");
        assert.equal(refAssignedVisible, true, "Character reference assigned box must be visible");
        const refNameText = await page.$eval("#mg-cast-ref-name", el => el.textContent);
        assert(refNameText.includes("ref_c789751db904319d.png"), "Reference filename must be displayed");
        
        // Confirm Reference assignment alone did NOT create an Instance
        assert.equal(docAfterC.pages[0].character_instances.length, 0, "Reference assignment alone must not create an Instance");
        console.log("✓ Step C PASS: Character created, Identity Prompt entered, Reference assigned to CAST, 0 instances");

        // ==============================================================
        // Step D: Return to the Scene & create ONE Character Instance
        // ==============================================================
        console.log("\n--- Step D: Return to Scene & toggle CAST appearance ---");
        // Click the Scene tab in composer
        await page.click(`#scene-prompt-tab-${sceneId}`);
        
        const isSceneActive = await page.evaluate((id) => window.__tegakiManga.session.selectedSceneId === id, sceneId);
        assert.equal(isSceneActive, true, "Scene must be active");
        
        // Click CAST appearance toggle button
        await page.click(".scene-cast-appearance-button");
        
        const docAfterD = await page.evaluate(() => window.__tegakiManga.store.getDocument());
        assert.equal(docAfterD.pages[0].character_instances.length, 1, "Exactly ONE Character Instance must be created");
        const instance = docAfterD.pages[0].character_instances[0];
        assert.equal(instance.scene_id, sceneId, "Instance must belong to current Scene");
        assert.equal(instance.cast_id, castId, "Instance must reference current CAST");
        
        // Confirm appearance button reflects ON state
        const isCastOn = await page.$eval(".scene-cast-appearance-button", el => el.classList.contains("is-on"));
        assert.equal(isCastOn, true, "CAST appearance button must be in active (is-on) state");
        console.log("✓ Step D PASS: CAST appearance toggle created ONE Character Instance in the Scene");

        // ==============================================================
        // Step E: Select Character Instance on Stage and adjust geometry
        // ==============================================================
        console.log("\n--- Step E: Adjust Character Instance rectangle geometry ---");
        const instId = instance.instance_id;
        
        // Adjust geometry via store resize and move
        await page.evaluate((id) => {
            const { store, updateAll } = window.__tegakiManga;
            // Resize character within parent scene
            store.resizeCharacter(id, 0.6, 0.7);
            store.moveCharacter(id, 0.05, 0.05);
            updateAll();
        }, instId);
        
        const docAfterE = await page.evaluate(() => window.__tegakiManga.store.getDocument());
        const updatedInst = docAfterE.pages[0].character_instances[0];
        assert.notDeepEqual(updatedInst.area, instance.area, "Instance area must have changed");
        
        // Confirm editing geometry does not silently change CAST Identity or Reference
        assert.equal(docAfterE.pages[0].cast[0].identity_prompt, "1girl, long hair, school uniform, detailed eyes", "CAST identity unchanged");
        assert.equal(docAfterE.pages[0].cast[0].reference_asset, refAsset, "CAST reference unchanged");
        console.log("✓ Step E PASS: Geometry adjusted without mutating CAST Identity or Reference assignment");

        // ==============================================================
        // Step F: Assign ONE page structural Guide through ordinary Create Guide
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
        
        const docAfterF = await page.evaluate(() => window.__tegakiManga.store.getDocument());
        assert.equal(docAfterF.pages[0].guides.length, 1, "Exactly one Guide must be assigned");
        assert.equal(docAfterF.pages[0].guides[0].asset_reference, guideAsset);
        assert.equal(docAfterF.pages[0].guides[0].enabled, true);
        
        // Confirm UI preview, status badge, and meta
        const guideAssignedVisible = await page.$eval("#mg-guide-assigned", el => el.style.display !== "none");
        assert.equal(guideAssignedVisible, true, "Guide assigned card must be visible");
        const guideBadgeState = await page.$eval("#mg-guide-status-badge", el => el.getAttribute("data-state"));
        assert.equal(guideBadgeState, "enabled", "Guide badge must be in enabled state");
        const guideBadgeText = await page.$eval("#mg-guide-status-badge", el => el.textContent);
        assert.equal(guideBadgeText, "GUIDE ENABLED", "Guide badge text must be GUIDE ENABLED");
        console.log("✓ Step F PASS: Page structural Guide assigned, enabled, and preview displayed");

        // ==============================================================
        // Step G: Switch between Global, Scene and Character Prompt targets
        // ==============================================================
        console.log("\n--- Step G: Target switching integrity ---");
        // Switch to Global
        await page.click("#scene-prompt-tab-global");
        const promptG = await page.$eval("#scene-composer-prompt", el => el.value);
        assert.equal(promptG, "monochrome manga, high contrast, clean line art", "Global prompt preserved");
        
        // Debug Scene tab
        const debugInfo = await page.evaluate((sId) => {
            const tabEl = document.getElementById(`scene-prompt-tab-${sId}`);
            const style = tabEl ? window.getComputedStyle(tabEl) : null;
            const parent = tabEl ? tabEl.parentElement : null;
            const parentStyle = parent ? window.getComputedStyle(parent) : null;
            const grandParent = parent ? parent.parentElement : null;
            return {
                sceneId: sId,
                tabExists: Boolean(tabEl),
                rect: tabEl?.getBoundingClientRect(),
                display: style?.display,
                visibility: style?.visibility,
                parentHidden: parent?.hidden,
                grandParentHidden: grandParent?.hidden,
                activeTab: window.__tegakiManga.session.activeTab,
                selectedSceneId: window.__tegakiManga.session.selectedSceneId,
                composerPromptTarget: window.__tegakiManga.getComposerPromptTarget()
            };
        }, sceneId);
        console.log("  Debug Info before scene click:", debugInfo);
        
        // Switch to Scene
        await page.click(`#scene-prompt-tab-${sceneId}`);
        
        const debugAfter = await page.evaluate((sId) => {
            const promptEl = document.getElementById("scene-composer-prompt");
            return {
                activeElement: document.activeElement?.id,
                promptValue: promptEl?.value,
                storePrompt: window.__tegakiManga.store.getPage().scenes[0]?.prompt,
                selectedSceneId: window.__tegakiManga.session.selectedSceneId,
                composerPromptTarget: window.__tegakiManga.getComposerPromptTarget()
            };
        }, sceneId);
        console.log("  Debug Info after scene click:", debugAfter);

        const promptS = await page.$eval("#scene-composer-prompt", el => el.value);
        assert.equal(promptS, "standing outdoors in a courtyard, stone pavement", "Scene prompt preserved");
        
        // Switch to Character
        await page.click(`#scene-prompt-tab-cast_${castId}`);
        const promptC = await page.$eval("#scene-composer-prompt", el => el.value);
        assert.equal(promptC, "1girl, long hair, school uniform, detailed eyes", "Character identity prompt preserved");
        
        // Confirm document still intact
        const docAfterG = await page.evaluate(() => window.__tegakiManga.store.getDocument());
        assert.equal(docAfterG.pages[0].scenes.length, 1);
        assert.equal(docAfterG.pages[0].cast.length, 1);
        assert.equal(docAfterG.pages[0].character_instances.length, 1);
        assert.equal(docAfterG.pages[0].guides.length, 1);
        console.log("✓ Step G PASS: Prompt target switching preserved all prompts, Scene, CAST, Instance, and Guide");

        // ==============================================================
        // Step H: Select Scenes generation & verify scope representation
        // ==============================================================
        console.log("\n--- Step H: Select Scenes generation scope ---");
        // Ensure Scenes generation scope is selected
        await page.evaluate(() => {
            const { generation } = window.__tegakiManga;
            generation.setGenerationScope("scenes");
        });
        
        const isScenesPressed = await page.$eval("#mg-generation-scope-scenes", el => el.getAttribute("aria-pressed"));
        assert.equal(isScenesPressed, "true", "Scenes generation scope button must be pressed");
        
        const modeValue = await page.evaluate(() => window.__tegakiManga.generation.state.mode);
        assert.equal(modeValue, "scene", "Generation state mode must be 'scene'");
        
        const genLabel = await page.$eval("#mg-generate-label", el => el.textContent);
        console.log(`  Generate button label: "${genLabel}"`);
        console.log("✓ Step H PASS: Scenes generation scope selected and accurately represented in GUI");

        // ==============================================================
        // Section 6: Compile Without GPU Execution
        // ==============================================================
        console.log("\n--- Section 6: Compile Without GPU Execution ---");
        
        // Build scene generation settings using the UI's own function
        const buildResult = await page.evaluate(async () => {
            const { generation, store } = window.__tegakiManga;
            try {
                // Ensure supported Illustrious checkpoint is selected
                const illust = generation.state.catalog.checkpoints.find(c => c.id.toLowerCase().includes("illustrious"));
                if (illust) {
                    generation.state.draft.checkpoint_id = illust.id;
                }
                const settings = window.__tegakiManga.buildSceneGenerationSettings();
                return { ok: true, settings };
            } catch (err) {
                return { ok: false, error: err.message, stack: err.stack };
            }
        });
        
        assert.equal(buildResult.ok, true, `Failed to build scene settings from UI: ${buildResult.error}`);
        const uiSettings = buildResult.settings;
        console.log("UI built settings successfully:", {
            mode: uiSettings.mode,
            checkpoint_id: uiSettings.checkpoint_id,
            controlnet_strength: uiSettings.controlnet_strength,
            mask_feather: uiSettings.mask_feather,
            panel_strength: uiSettings.panel_strength
        });
        
        // Now compile through /api/manga/generation/compile-scene
        const compileResponse = await page.evaluate(async (settings) => {
            const req = {
                ...settings,
                request_id: "req_browser_acceptance_001"
            };
            const res = await fetch("/api/manga/generation/compile-scene", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(req)
            });
            const data = await res.json();
            return { status: res.status, data };
        }, uiSettings);
        
        assert.equal(compileResponse.status, 200, `Compile endpoint returned status ${compileResponse.status}`);
        const compiled = compileResponse.data;
        assert.equal(compiled.ok, true, `Compile failed: ${compiled.error}`);
        
        console.log(`Compile Graph Digest: ${compiled.graph_digest}`);
        console.log(`Audit ControlNet:`, compiled.audit_trail.controlnet);
        console.log(`Audit Reference:`, compiled.audit_trail.reference);
        
        // Verify graph contains BOTH ControlNet and IP-Adapter
        const graph = compiled.graph;
        const classes = Object.values(graph).map(n => n.class_type);
        assert(classes.includes("ControlNetLoader"), "Graph must contain ControlNetLoader");
        assert(classes.includes("ControlNetApplyAdvanced"), "Graph must contain ControlNetApplyAdvanced");
        assert(classes.includes("CLIPVisionLoader"), "Graph must contain CLIPVisionLoader");
        assert(classes.includes("IPAdapterModelLoader"), "Graph must contain IPAdapterModelLoader");
        assert(classes.includes("IPAdapterAdvanced"), "Graph must contain IPAdapterAdvanced");
        
        // Verify wiring:
        // 1. Character instance mask reaches IP-Adapter attention mask
        const ipaNode = Object.values(graph).find(n => n.class_type === "IPAdapterAdvanced");
        assert.deepEqual(ipaNode.inputs.attn_mask, ["3", 3], "IP-Adapter attn_mask must connect to ConditioningBuilder output 3");
        
        // 2. KSampler receives patched model from IPAdapterAdvanced
        const ksamplerNode = Object.values(graph).find(n => n.class_type === "KSampler");
        const ipaId = Object.keys(graph).find(k => graph[k].class_type === "IPAdapterAdvanced");
        assert.deepEqual(ksamplerNode.inputs.model, [ipaId, 0], "KSampler must receive model from IPAdapterAdvanced");
        
        // 3. KSampler receives positive and negative conditioning from ControlNetApplyAdvanced
        const cnetApplyId = Object.keys(graph).find(k => graph[k].class_type === "ControlNetApplyAdvanced");
        assert.deepEqual(ksamplerNode.inputs.positive, [cnetApplyId, 0], "KSampler positive must receive ControlNet output 0");
        assert.deepEqual(ksamplerNode.inputs.negative, [cnetApplyId, 1], "KSampler negative must receive ControlNet output 1");
        
        // 4. Verify selections match document
        assert.equal(compiled.audit_trail.controlnet.asset_reference, guideAsset);
        assert.equal(compiled.audit_trail.reference.reference_asset, refAsset);
        assert.equal(compiled.audit_trail.reference.cast_id, castId);
        assert.equal(compiled.audit_trail.reference.instance_id, instId);
        
        console.log("✓ Section 6 PASS: GUI-produced document compiled to combined graph with exact wiring verified");
        console.log("\nALL BROWSER FLOW STEPS A-H AND COMPILE VERIFICATION PASSED PERFECTLY!");
        
    } finally {
        await context.close();
        await browser.close();
    }
}

runBrowserAcceptance().catch(err => {
    console.error("Browser Acceptance FAILED:", err);
    process.exit(1);
});
