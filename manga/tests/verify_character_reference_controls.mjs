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
    console.log("=== MANGA-CHARACTER-REFERENCE-CONTROLS1 TARGETED ACCEPTANCE ===");
    const chromium = getPlaywrightChromium();
    assert(chromium, "Playwright Chromium must be available");

    const browser = await chromium.launch({ headless: true });
    const context = await browser.newContext({ viewport: { width: 1280, height: 800 } });
    const page = await context.newPage();

    try {
        console.log("1. Navigating to http://127.0.0.1:8191/ ...");
        await page.goto("http://127.0.0.1:8191/", { waitUntil: "networkidle" });
        await page.waitForFunction(() => window.__tegakiManga && window.__tegakiManga.generation?.state?.catalog);
        console.log("   Manga workspace ready.");

        // 2. Setup document with 2 scenes, 2 CASTs (one with reference, one without)
        await page.evaluate(() => {
            const { store, session, setMangaMode, updateAll } = window.__tegakiManga;
            const doc = store.getDocument();
            doc.pages[0].scenes = [
                {
                    scene_id: "scene_1",
                    order: 1,
                    input_mode: "cast",
                    prompt: "classroom interior",
                    negative_prompt: "",
                    area: { shape_type: "rect", x: 0.05, y: 0.05, w: 0.42, h: 0.42 }
                },
                {
                    scene_id: "scene_2",
                    order: 2,
                    input_mode: "cast",
                    prompt: "park bench",
                    negative_prompt: "",
                    area: { shape_type: "rect", x: 0.53, y: 0.05, w: 0.42, h: 0.42 }
                }
            ];
            doc.pages[0].cast = [
                {
                    cast_id: "cast_with_ref",
                    display_name: "Heroine",
                    identity_prompt: "1girl, braided hair",
                    negative_prompt: "",
                    reference_asset: "tegaki_manga_references/ref_c789751db904319d.png"
                },
                {
                    cast_id: "cast_no_ref",
                    display_name: "Hero",
                    identity_prompt: "1boy, black hair",
                    negative_prompt: "",
                    reference_asset: null
                }
            ];
            doc.pages[0].character_instances = [
                {
                    instance_id: "inst_1",
                    cast_id: "cast_with_ref",
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
            setMangaMode("authoring");
            session.selectScene("scene_1");
            session.selectGuide("guide_disposable");
            updateAll();
        });

        // 3. Switch composer target to cast_with_ref
        console.log("2. Verifying controls visibility when CAST with reference is selected...");
        await page.evaluate(() => {
            const btn = document.querySelector('[data-prompt-target="cast_cast_with_ref"]');
            if (btn) btn.click();
        });

        const assignedVisible = await page.isVisible("#mg-cast-ref-assigned");
        assert(assignedVisible, "#mg-cast-ref-assigned must be visible");

        const weightVisible = await page.isVisible("#mg-ref-weight");
        const startVisible = await page.isVisible("#mg-ref-start");
        const endVisible = await page.isVisible("#mg-ref-end");
        assert(weightVisible, "#mg-ref-weight must be visible");
        assert(startVisible, "#mg-ref-start must be visible");
        assert(endVisible, "#mg-ref-end must be visible");

        // A. Verify neither settings group contains a slider in the DOM
        const refSlider = await page.$("#mg-ref-weight-slider");
        const cnetSlider = await page.$("#mg-cnet-strength-slider");
        assert.equal(refSlider, null, "#mg-ref-weight-slider must be removed from the DOM");
        assert.equal(cnetSlider, null, "#mg-cnet-strength-slider must be removed from the DOM");
        console.log("   [Check A] Verified neither group contains a slider in the DOM.");

        // Verify default values
        const defWeight = await page.$eval("#mg-ref-weight", el => el.value);
        const defStart = await page.$eval("#mg-ref-start", el => el.value);
        const defEnd = await page.$eval("#mg-ref-end", el => el.value);
        assert.equal(defWeight, "0.70", "Default reference weight must be 0.70");
        assert.equal(defStart, "0.0", "Default reference start must be 0.0");
        assert.equal(defEnd, "1.0", "Default reference end must be 1.0");
        console.log("   Default values verified: weight 0.70, start 0.0, end 1.0");

        // Verify thumbnail, Replace, and Clear are present
        const thumbVisible = await page.isVisible("#mg-cast-ref-img");
        const replaceVisible = await page.isVisible("#mg-btn-replace-char-ref");
        const clearVisible = await page.isVisible("#mg-btn-clear-char-ref");
        assert(thumbVisible, "Thumbnail image must be visible");
        assert(replaceVisible, "Replace button must be visible");
        assert(clearVisible, "Clear button must be visible");
        console.log("   Thumbnail, Replace, and Clear buttons are operational.");

        // B. Verify compact single-row structure and K. right-side space
        const compactCheck = await page.evaluate(() => {
            const refControls = document.querySelector("#mg-cast-ref-controls");
            const cnetControls = document.querySelector("#mg-guide-cnet-controls");
            const slot = document.querySelector(".mg-cast-ref-right-slot");
            const leftCol = document.querySelector(".mg-cast-ref-left-col");
            
            const refCols = refControls ? refControls.querySelectorAll(".mg-compact-row > .mg-compact-col").length : 0;
            const cnetCols = cnetControls ? cnetControls.querySelectorAll(".mg-compact-row > .mg-compact-col").length : 0;
            
            const slotStyle = slot ? window.getComputedStyle(slot) : null;
            const leftStyle = leftCol ? window.getComputedStyle(leftCol) : null;
            
            return {
                refCols,
                cnetCols,
                slotPreserved: !!(slotStyle && slotStyle.flexGrow === "1" && parseFloat(leftStyle.maxWidth) <= 250)
            };
        });
        assert.equal(compactCheck.refCols, 3, "Character Reference controls must have 3 compact columns in 1 row");
        assert.equal(compactCheck.cnetCols, 3, "Guide ControlNet controls must have 3 compact columns in 1 row");
        assert(compactCheck.slotPreserved, "Right slot must be preserved for later analysis preview and left col compact");
        console.log("   [Check B] Both groups retain one compact desktop row (3 cols each).");
        console.log("   [Check K] Right-side preview space remains available.");

        // Save desktop screenshot
        await page.screenshot({ path: "scratch/desktop_compact_controls.png", fullPage: false });
        console.log("   Desktop screenshot saved to scratch/desktop_compact_controls.png");

        // C. Direct typing still works
        console.log("3. Testing direct typing and validation...");
        await page.fill("#mg-ref-weight", "0.85");
        await page.dispatchEvent("#mg-ref-weight", "input");
        let directWeight = await page.$eval("#mg-ref-weight", el => el.value);
        let directStateWeight = await page.evaluate(() => window.__tegakiManga.generation.state.sceneDraft.reference_weight);
        assert.equal(directWeight, "0.85", "Direct typing into Reference Weight must update input value");
        assert.equal(directStateWeight, "0.85", "Direct typing must update effective generation setting");
        console.log("   [Check C] Direct typing works and updates effective generation setting.");

        // Direct typing invalid range test
        await page.fill("#mg-ref-start", "0.9");
        await page.fill("#mg-ref-end", "0.5");
        await page.dispatchEvent("#mg-ref-end", "input");
        let isErrVisible = await page.isVisible("#mg-ref-validation-error");
        let errText = await page.$eval("#mg-ref-validation-error", el => el.textContent);
        assert(isErrVisible, "Validation error must be visible when start >= end via direct typing");
        assert(errText.includes("strictly less"), "Error text must mention strictly less");
        // Reset to valid
        await page.fill("#mg-ref-start", "0.1");
        await page.fill("#mg-ref-end", "0.85");
        await page.dispatchEvent("#mg-ref-end", "input");
        assert(!await page.isVisible("#mg-ref-validation-error"), "Validation error must clear");

        // D. Focus Reference Weight and use wheel up/down
        console.log("4. Testing wheel interactions...");
        // Test unfocused hover + wheel (must not change)
        await page.evaluate(() => document.body.focus());
        await page.hover("#mg-ref-weight");
        await page.mouse.wheel(0, -100);
        let unfocusedWeight = await page.$eval("#mg-ref-weight", el => el.value);
        assert.equal(unfocusedWeight, "0.85", "Wheel on unfocused input must not change value");
        console.log("   [Check I/Safety] Wheel events without keyboard focus do not change values.");

        // Focus and wheel up
        await page.focus("#mg-ref-weight");
        await page.hover("#mg-ref-weight");
        await page.mouse.wheel(0, -100); // 0.85 -> 0.90
        let wheelWeight = await page.$eval("#mg-ref-weight", el => el.value);
        let wheelStateWeight = await page.evaluate(() => window.__tegakiManga.generation.state.sceneDraft.reference_weight);
        assert.equal(wheelWeight, "0.9", "Wheel up on focused Reference Weight must increment to 0.9");
        assert.equal(wheelStateWeight, "0.9", "Effective generation setting must update to 0.9");

        // Wheel down
        await page.mouse.wheel(0, 100); // 0.90 -> 0.85
        wheelWeight = await page.$eval("#mg-ref-weight", el => el.value);
        wheelStateWeight = await page.evaluate(() => window.__tegakiManga.generation.state.sceneDraft.reference_weight);
        assert.equal(wheelWeight, "0.85", "Wheel down on focused Reference Weight must decrement to 0.85");
        assert.equal(wheelStateWeight, "0.85", "Effective generation setting must update to 0.85");
        console.log("   [Check D] Reference Weight wheel up/down updates displayed value and effective setting.");

        // E. Repeat for ControlNet Strength
        await page.focus("#mg-cnet-strength");
        await page.hover("#mg-cnet-strength");
        await page.mouse.wheel(0, -100); // 0.35 -> 0.40
        let cnetVal = await page.$eval("#mg-cnet-strength", el => el.value);
        let cnetState = await page.evaluate(() => window.__tegakiManga.generation.state.sceneDraft.controlnet_strength);
        assert.equal(cnetVal, "0.4", "ControlNet Strength must increment to 0.4 on wheel up");
        assert.equal(cnetState, "0.4", "ControlNet Strength effective setting must update to 0.4");
        await page.mouse.wheel(0, 100); // 0.40 -> 0.35
        cnetVal = await page.$eval("#mg-cnet-strength", el => el.value);
        cnetState = await page.evaluate(() => window.__tegakiManga.generation.state.sceneDraft.controlnet_strength);
        assert.equal(cnetVal, "0.35", "ControlNet Strength must decrement to 0.35 on wheel down");
        assert.equal(cnetState, "0.35", "ControlNet Strength effective setting must update to 0.35");
        console.log("   [Check E] ControlNet Strength wheel up/down verified.");

        // F. Wheel behavior for Start and End
        // Reference Start: from 0.1 wheel up to 0.15
        await page.focus("#mg-ref-start");
        await page.hover("#mg-ref-start");
        await page.mouse.wheel(0, -100);
        assert.equal(await page.$eval("#mg-ref-start", el => el.value), "0.15");
        assert.equal(await page.evaluate(() => window.__tegakiManga.generation.state.sceneDraft.reference_start), "0.15");

        // Reference End: from 0.85 wheel down to 0.80
        await page.focus("#mg-ref-end");
        await page.hover("#mg-ref-end");
        await page.mouse.wheel(0, 100);
        assert.equal(await page.$eval("#mg-ref-end", el => el.value), "0.8");
        assert.equal(await page.evaluate(() => window.__tegakiManga.generation.state.sceneDraft.reference_end), "0.8");
        console.log("   [Check F] Start and End wheel behaviors confirmed.");

        // G. Min/max boundaries respected (no wrapping)
        await page.fill("#mg-ref-weight", "2.0");
        await page.dispatchEvent("#mg-ref-weight", "input");
        await page.focus("#mg-ref-weight");
        await page.hover("#mg-ref-weight");
        await page.mouse.wheel(0, -100); // at max, wheel up
        let atMax = parseFloat(await page.$eval("#mg-ref-weight", el => el.value));
        assert.equal(atMax, 2.0, "Value at max must not exceed 2.0 or wrap");
        await page.fill("#mg-ref-weight", "0.0");
        await page.dispatchEvent("#mg-ref-weight", "input");
        await page.mouse.wheel(0, 100); // at min, wheel down
        let atMin = parseFloat(await page.$eval("#mg-ref-weight", el => el.value));
        assert.equal(atMin, 0.0, "Value at min must not go below 0.0 or wrap");
        // Reset weight to 1.15
        await page.fill("#mg-ref-weight", "1.15");
        await page.dispatchEvent("#mg-ref-weight", "input");
        console.log("   [Check G] Min/max boundaries respected without wrapping.");

        // H. Invalid Start/End combinations cannot be created by wheel input
        // Set Start to 0.40 and End to 0.45
        await page.fill("#mg-ref-start", "0.4");
        await page.dispatchEvent("#mg-ref-start", "input");
        await page.fill("#mg-ref-end", "0.45");
        await page.dispatchEvent("#mg-ref-end", "input");
        // Wheel up on Start: candidate is 0.45, which would violate Start < End (0.45 < 0.45 is false)
        await page.focus("#mg-ref-start");
        await page.hover("#mg-ref-start");
        await page.mouse.wheel(0, -100);
        let rejectedStart = await page.$eval("#mg-ref-start", el => el.value);
        assert.equal(rejectedStart, "0.4", "Wheel step that would violate Start < End must be rejected");
        // Wheel down on End: candidate is 0.40, which would violate Start < End (0.40 > 0.40 is false)
        await page.focus("#mg-ref-end");
        await page.hover("#mg-ref-end");
        await page.mouse.wheel(0, 100);
        let rejectedEnd = await page.$eval("#mg-ref-end", el => el.value);
        assert.equal(rejectedEnd, "0.45", "Wheel step that would violate Start < End must be rejected");
        assert(!await page.isVisible("#mg-ref-validation-error"), "No error shown when invalid wheel step is rejected");
        console.log("   [Check H] Invalid Start/End pairs rejected by wheel input.");

        // Set stable values for persistence test
        await page.fill("#mg-ref-start", "0.1");
        await page.dispatchEvent("#mg-ref-start", "input");
        await page.fill("#mg-ref-end", "0.85");
        await page.dispatchEvent("#mg-ref-end", "input");
        await page.fill("#mg-ref-weight", "1.15");
        await page.dispatchEvent("#mg-ref-weight", "input");

        // J. Verify stability across CAST, Scene, and Stage switching
        console.log("5. Verifying stability across CAST, Scene, and Stage switching...");
        await page.evaluate(() => {
            const btn = document.querySelector('[data-prompt-target="cast_cast_no_ref"]');
            if (btn) btn.click();
        });
        const emptyVisible = await page.isVisible("#mg-cast-ref-empty");
        assert(emptyVisible, "Empty state must be visible for cast without reference");

        // Switch back to cast_with_ref
        await page.evaluate(() => {
            const btn = document.querySelector('[data-prompt-target="cast_cast_with_ref"]');
            if (btn) btn.click();
        });
        const reWeight = await page.$eval("#mg-ref-weight", el => el.value);
        const reStart = await page.$eval("#mg-ref-start", el => el.value);
        const reEnd = await page.$eval("#mg-ref-end", el => el.value);
        assert.equal(reWeight, "1.15", "Weight must persist across CAST switch");
        assert.equal(reStart, "0.1", "Start must persist across CAST switch");
        assert.equal(reEnd, "0.85", "End must persist across CAST switch");

        // Switch scene
        await page.evaluate(() => {
            const btn = document.querySelector('[data-prompt-target="scene_2"]');
            if (btn) btn.click();
        });
        // Switch back to cast_with_ref
        await page.evaluate(() => {
            const btn = document.querySelector('[data-prompt-target="cast_cast_with_ref"]');
            if (btn) btn.click();
        });
        assert.equal(await page.$eval("#mg-ref-weight", el => el.value), "1.15", "Weight must persist across Scene switch");
        assert.equal(await page.$eval("#mg-ref-start", el => el.value), "0.1", "Start must persist across Scene switch");
        assert.equal(await page.$eval("#mg-ref-end", el => el.value), "0.85", "End must persist across Scene switch");

        // Switch stage mode (Layout mode and back)
        await page.evaluate(() => {
            const btn = document.getElementById("mg-stage-mode-layout");
            if (btn) btn.click();
        });
        await page.evaluate(() => {
            const btn = document.getElementById("mg-stage-mode-switch");
            if (btn) btn.click();
        });
        assert.equal(await page.$eval("#mg-ref-weight", el => el.value), "1.15", "Weight must persist across Stage switch");
        assert.equal(await page.$eval("#mg-ref-start", el => el.value), "0.1", "Start must persist across Stage switch");
        assert.equal(await page.$eval("#mg-ref-end", el => el.value), "0.85", "End must persist across Stage switch");
        console.log("   [Check J] Values stay completely stable across CAST, Scene, and Stage switching.");

        // 8. Test responsive layout at narrow viewport
        console.log("5. Testing responsive layout at narrow viewport...");
        await page.setViewportSize({ width: 480, height: 800 });
        const responsiveCheck = await page.evaluate(() => {
            const assigned = document.querySelector(".mg-cast-ref-assigned");
            const refRow = document.querySelector("#mg-cast-ref-controls .mg-compact-row");
            const cnetRow = document.querySelector("#mg-guide-cnet-controls .mg-compact-row");
            const isColumn = window.getComputedStyle(assigned).flexDirection === "column";
            const noRefOverflow = refRow ? refRow.scrollWidth <= refRow.clientWidth + 2 : true;
            const noCnetOverflow = cnetRow ? cnetRow.scrollWidth <= cnetRow.clientWidth + 2 : true;
            return { isColumn, noRefOverflow, noCnetOverflow };
        });
        assert(responsiveCheck.isColumn, "Assigned container must wrap to column at viewport <= 600px");
        assert(responsiveCheck.noRefOverflow, "Reference compact row must not overflow horizontally on narrow viewport");
        assert(responsiveCheck.noCnetOverflow, "Guide ControlNet compact row must not overflow horizontally on narrow viewport");
        await page.evaluate(() => {
            const el = document.getElementById("mg-cast-ref-assigned");
            if (el) el.scrollIntoView();
        });
        await page.screenshot({ path: "scratch/narrow_compact_controls.png", fullPage: false });
        console.log("   Narrow viewport column layout verified. Screenshot saved to scratch/narrow_compact_controls.png");
        await page.setViewportSize({ width: 1280, height: 800 });

        // 9. Test Clear action
        console.log("6. Testing Clear button functionality...");
        await page.evaluate(() => {
            const clearBtn = document.getElementById("mg-btn-clear-char-ref");
            if (clearBtn) clearBtn.click();
        });
        const clearedEmptyVisible = await page.isVisible("#mg-cast-ref-empty");
        assert(clearedEmptyVisible, "Clear button must return reference to empty state");
        console.log("   Clear button successfully cleared reference.");

        console.log("=== BROWSER ACCEPTANCE TESTS PASSED SUCCESSFULLY ===");
    } finally {
        await browser.close();
    }
}

runAcceptance().catch(err => {
    console.error("ACCEPTANCE TEST FAILED:", err);
    process.exit(1);
});
