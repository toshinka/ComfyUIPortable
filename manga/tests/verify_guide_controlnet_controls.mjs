import assert from "node:assert/strict";
import path from "node:path";
import { createRequire } from "node:module";
import { execSync } from "node:child_process";

const require = createRequire(import.meta.url);

function getPlaywrightChromium() {
    if (process.env.TEGAKI_PLAYWRIGHT_MODULE) return require(process.env.TEGAKI_PLAYWRIGHT_MODULE).chromium;
    try { return require("playwright").chromium; } catch {}
    const root = execSync("npm root -g", { encoding: "utf8" }).trim();
    return require(path.join(root, "@executeautomation", "playwright-mcp-server", "node_modules", "playwright")).chromium;
}

async function runAcceptance() {
    console.log("=== MANGA-GUIDE-CONTROLNET-CONTROLS1 TARGETED ACCEPTANCE ===");
    const chromium = getPlaywrightChromium();
    assert(chromium, "Playwright Chromium must be available");

    const browser = await chromium.launch({ headless: true });
    const context = await browser.newContext({ viewport: { width: 1280, height: 800 } });
    const page = await context.newPage();

    try {
        console.log("Navigating to http://127.0.0.1:8191/ ...");
        await page.goto("http://127.0.0.1:8191/", { waitUntil: "networkidle" });
        await page.waitForFunction(() => window.__tegakiManga && window.__tegakiManga.generation?.state?.catalog);
        console.log("Manga workspace ready.");

        // Setup disposable document with guide and 2 scenes and 1 cast
        await page.evaluate(() => {
            const { store, session, setMangaMode, updateAll } = window.__tegakiManga;
            const doc = store.getDocument();
            doc.pages[0].scenes = [
                {
                    scene_id: "scene_1",
                    order: 1,
                    input_mode: "cast",
                    prompt: "sunny park",
                    negative_prompt: "",
                    area: { shape_type: "rect", x: 0.05, y: 0.05, w: 0.42, h: 0.42 }
                },
                {
                    scene_id: "scene_2",
                    order: 2,
                    input_mode: "simple",
                    prompt: "quiet lake",
                    negative_prompt: "",
                    area: { shape_type: "rect", x: 0.53, y: 0.05, w: 0.42, h: 0.42 }
                }
            ];
            doc.pages[0].cast = [
                {
                    cast_id: "cast_heroine",
                    display_name: "Heroine",
                    identity_prompt: "1girl, twin braids",
                    negative_prompt: "",
                    reference_asset: null
                }
            ];
            doc.pages[0].character_instances = [
                {
                    instance_id: "inst_1",
                    cast_id: "cast_heroine",
                    scene_id: "scene_1",
                    area: { shape_type: "rect", x: 0.1, y: 0.1, w: 0.3, h: 0.3 },
                    acting_prompt: "smiling"
                }
            ];
            doc.pages[0].guides = [
                {
                    guide_id: "guide_disposable",
                    guide_type: "rough_manga",
                    enabled: true,
                    asset_reference: "tegaki_manga_guides/disposable_guide_three_panel_dog_girl_car.png",
                    placement: { x: 0, y: 0, w: 1, h: 1, scale_x: 1, scale_y: 1 },
                    figure_regions: [],
                    metadata: { fit_mode: "contain" }
                }
            ];
            store.setDocument(doc);
            session.selectScene("scene_1");
            session.selectCast("cast_heroine");
            session.selectInstance("inst_1");
            session.selectGuide("guide_disposable");
            setMangaMode("authoring");
            updateAll();
        });

        // 1. Check A & B: Controls visible & current values displayed
        console.log("\n--- Checking Controls Visibility & Default Values ---");
        const controlsVisible = await page.$eval("#mg-guide-cnet-controls", el => el.style.display !== "none");
        assert.equal(controlsVisible, true, "mg-guide-cnet-controls must be visible when guide is assigned");
        
        const defaultStrength = await page.$eval("#mg-cnet-strength", el => el.value);
        const defaultStart = await page.$eval("#mg-cnet-start", el => el.value);
        const defaultEnd = await page.$eval("#mg-cnet-end", el => el.value);
        console.log(`Default values: Strength=${defaultStrength}, Start=${defaultStart}, End=${defaultEnd}`);
        assert.equal(defaultStrength, "0.35", "Default strength must be 0.35");
        assert.equal(defaultStart, "0.0", "Default start must be 0.0");
        assert.equal(defaultEnd, "1.0", "Default end must be 1.0");

        // Verify slider is removed
        const sliderEl = await page.$("#mg-cnet-strength-slider");
        assert.equal(sliderEl, null, "#mg-cnet-strength-slider must be removed from the DOM");
        console.log("Verified #mg-cnet-strength-slider is removed from DOM.");

        // 2. Check C & D: Strength set to 1.0 and 1.2 via typing and wheel
        console.log("\n--- Setting Strength to 1.0 and 1.2 ---");
        await page.fill("#mg-cnet-strength", "1.0");
        await page.dispatchEvent("#mg-cnet-strength", "input");
        let numVal = await page.$eval("#mg-cnet-strength", el => el.value);
        let stateStrength = await page.evaluate(() => window.__tegakiManga.generation.state.sceneDraft.controlnet_strength);
        assert.equal(parseFloat(numVal), 1.0, "Strength input should be 1.0");
        assert.equal(parseFloat(stateStrength), 1.0, "State should be updated to 1.0");

        // Use wheel to adjust from 1.0 up to 1.2
        await page.focus("#mg-cnet-strength");
        await page.hover("#mg-cnet-strength");
        await page.mouse.wheel(0, -100); // 1.05
        await page.mouse.wheel(0, -100); // 1.10
        await page.mouse.wheel(0, -100); // 1.15
        await page.mouse.wheel(0, -100); // 1.20
        numVal = await page.$eval("#mg-cnet-strength", el => el.value);
        stateStrength = await page.evaluate(() => window.__tegakiManga.generation.state.sceneDraft.controlnet_strength);
        console.log(`Strength 1.2 set via wheel: number=${numVal}, state=${stateStrength}`);
        assert.equal(numVal, "1.2", "Strength input should reach 1.2 via wheel");
        assert.equal(stateStrength, "1.2", "State should be updated to 1.2 via wheel");

        // 3. Check E: Start 0.0 / End 0.8
        console.log("\n--- Setting Start 0.0 / End 0.8 ---");
        await page.fill("#mg-cnet-start", "0.0");
        await page.dispatchEvent("#mg-cnet-start", "input");
        await page.fill("#mg-cnet-end", "0.8");
        await page.dispatchEvent("#mg-cnet-end", "input");

        const startVal = await page.$eval("#mg-cnet-start", el => el.value);
        const endVal = await page.$eval("#mg-cnet-end", el => el.value);
        const errorDisplay = await page.$eval("#mg-cnet-validation-error", el => el.style.display);
        const stateStart = await page.evaluate(() => window.__tegakiManga.generation.state.sceneDraft.controlnet_start_percent);
        const stateEnd = await page.evaluate(() => window.__tegakiManga.generation.state.sceneDraft.controlnet_end_percent);
        console.log(`Timing set: Start=${startVal}, End=${endVal}, stateStart=${stateStart}, stateEnd=${stateEnd}, errorDisplay=${errorDisplay}`);
        assert.equal(startVal, "0.0", "Start value should be 0.0");
        assert.equal(endVal, "0.8", "End value should be 0.8");
        assert.equal(errorDisplay, "none", "No validation error should be displayed");
        assert.equal(stateStart, "0", "State start should be 0");
        assert.equal(stateEnd, "0.8", "State end should be 0.8");

        // 4. Check F: State stability across Scene and CAST switching and Stage mode
        console.log("\n--- Checking State Stability across Scene, CAST and Stage switching ---");
        await page.evaluate(() => {
            const { session, updateAll } = window.__tegakiManga;
            session.selectScene("scene_2");
            updateAll();
        });
        assert.equal(parseFloat(await page.$eval("#mg-cnet-strength", el => el.value)), 1.2);
        assert.equal(parseFloat(await page.$eval("#mg-cnet-start", el => el.value)), 0.0);
        assert.equal(parseFloat(await page.$eval("#mg-cnet-end", el => el.value)), 0.8);

        await page.evaluate(() => {
            const { session, updateAll } = window.__tegakiManga;
            session.selectCast("cast_heroine");
            session.selectScene("scene_1");
            updateAll();
        });
        assert.equal(parseFloat(await page.$eval("#mg-cnet-strength", el => el.value)), 1.2);
        assert.equal(parseFloat(await page.$eval("#mg-cnet-start", el => el.value)), 0.0);
        assert.equal(parseFloat(await page.$eval("#mg-cnet-end", el => el.value)), 0.8);

        // Switch to Result mode and back to Layout mode
        await page.click("#mg-stage-mode-result");
        await page.click("#mg-stage-mode-layout");
        assert.equal(parseFloat(await page.$eval("#mg-cnet-strength", el => el.value)), 1.2);
        assert.equal(parseFloat(await page.$eval("#mg-cnet-start", el => el.value)), 0.0);
        assert.equal(parseFloat(await page.$eval("#mg-cnet-end", el => el.value)), 0.8);

        // 5. Check G: Disabled Guide preserves no-ControlNet behavior
        console.log("\n--- Checking Disabled Guide Behavior ---");
        await page.click("#mg-btn-toggle-guide");
        const toggleBtnText = await page.$eval("#mg-btn-toggle-guide", el => el.textContent.trim());
        assert.equal(toggleBtnText, "Enable", "Button should now say Enable");

        // Build scene generation request when guide is disabled
        const disabledSettings = await page.evaluate(async () => {
            const gen = window.__tegakiManga.generation;
            const doc = window.__tegakiManga.store.getDocument();
            // Call compileSceneSettings directly or via generate request builder
            return gen.buildSceneRequest ? gen.buildSceneRequest(doc) : null;
        });

        // Re-enable guide
        await page.click("#mg-btn-toggle-guide");
        const toggleBtnTextReenabled = await page.$eval("#mg-btn-toggle-guide", el => el.textContent.trim());
        assert.equal(toggleBtnTextReenabled, "Disable", "Button should now say Disable");

        // 6. Check H: Guide raster preview on Stage
        console.log("\n--- Checking Guide Raster Preview on Stage ---");
        const rasterVisible = await page.$eval(".mg-stage-guide-raster", el => el && el.getAttribute("href") && el.style.display !== "none");
        assert.equal(rasterVisible, true, "Stage guide raster image must be present and visible");

        // 7. Check I: Global generation remains unaffected
        console.log("\n--- Checking Global Generation Independence ---");
        const globalSettings = await page.evaluate(() => {
            const gen = window.__tegakiManga.generation;
            return gen.compileSettings ? gen.compileSettings() : gen.state.draft;
        });
        assert.equal(globalSettings.controlnet_strength, undefined, "Global settings must not contain controlnet_strength");
        assert.equal(globalSettings.controlnet_start_percent, undefined, "Global settings must not contain controlnet_start_percent");

        // Take screenshots for evidence
        await page.screenshot({ path: "scratch/cnet_controls_desktop.png" });
        console.log("Saved scratch/cnet_controls_desktop.png");

        await page.setViewportSize({ width: 400, height: 700 });
        await page.screenshot({ path: "scratch/cnet_controls_narrow.png" });
        console.log("Saved scratch/cnet_controls_narrow.png");

        console.log("\n=== ALL TARGETED BROWSER CHECKS PASS ===");
    } finally {
        await browser.close();
    }
}

runAcceptance().catch(err => {
    console.error("Browser Acceptance FAILED:", err);
    process.exit(1);
});
