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

function createBaseThreeSceneDocument() {
    return {
        schema_id: "TEGAKI_AUTHORING_DOCUMENT",
        schema_version: "1.0.0",
        pages: [{
            page_id: "page_diag_1",
            width_px: 832,
            height_px: 1216,
            style_prompt: "monochrome manga, clean line art",
            style_negative_prompt: "blurry, low quality",
            scenes: [
                {
                    scene_id: "scene_1",
                    name: "Scene 1",
                    prompt: "courtyard, stone pavement",
                    negative_prompt: "",
                    input_mode: "simple",
                    area: { shape_type: "rect", x: 0.05, y: 0.05, w: 0.90, h: 0.28 },
                    order: 1,
                    metadata: {}
                },
                {
                    scene_id: "scene_2",
                    name: "Scene 2",
                    prompt: "indoor room, table with flower vase",
                    negative_prompt: "",
                    input_mode: "simple",
                    area: { shape_type: "rect", x: 0.05, y: 0.36, w: 0.90, h: 0.28 },
                    order: 2,
                    metadata: {}
                },
                {
                    scene_id: "scene_3",
                    name: "Scene 3",
                    prompt: "classroom corridor, windows",
                    negative_prompt: "",
                    input_mode: "simple",
                    area: { shape_type: "rect", x: 0.05, y: 0.67, w: 0.90, h: 0.28 },
                    order: 3,
                    metadata: {}
                }
            ],
            cast: [],
            character_instances: [],
            guides: [],
            visual_frames: []
        }],
        metadata: {}
    };
}

async function verifyCastMultiGenerateDiagnosis() {
    console.log("=== VERIFYING MANGA-CAST-MULTI-GENERATE-DIAGNOSIS1 ===");
    const chromium = getPlaywrightChromium();
    assert(chromium, "Playwright Chromium must be available");
    const browser = await chromium.launch({ headless: true });
    const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
    const page = await context.newPage();

    console.log("Navigating to http://127.0.0.1:8191/ ...");
    await page.goto("http://127.0.0.1:8191/", { waitUntil: "networkidle" });
    await page.waitForFunction(() => window.__tegakiManga && window.__tegakiManga.generation?.state?.catalog);

    // 1. Case A: Three simple Scenes, zero CAST instances
    console.log("\n--- Check 1: Case A (3 simple scenes, 0 instances) ---");
    const docA = createBaseThreeSceneDocument();
    const resA = await page.evaluate((doc) => {
        const tm = window.__tegakiManga;
        tm.store.setDocument(doc);
        if (tm.updateAll) tm.updateAll();
        tm.generation.setGenerationScope("scenes");
        const btn = document.getElementById("mg-generate");
        const reason = document.getElementById("mg-generate-reason");
        return {
            disabled: btn.disabled,
            reason: reason ? reason.textContent.trim() : "",
            scope: tm.generation.getGenerationScope()
        };
    }, docA);
    assert.equal(resA.disabled, false, "Case A: Generate must be enabled");
    assert.equal(resA.reason, "", "Case A: No block reason");
    assert.equal(resA.scope, "scenes", "Case A: Scope is scenes");
    console.log("✓ Check 1 PASS: Case A Generate is enabled with scenes scope");

    // 2. Case B: Three Scenes and TWO CAST definitions, only ONE placed Instance
    console.log("\n--- Check 2: Case B (3 scenes, 2 CAST defs, 1 placed instance) ---");
    const docB = createBaseThreeSceneDocument();
    docB.pages[0].cast = [
        { cast_id: "cast_hero", display_name: "Hero", identity_prompt: "1boy, black hair", negative_prompt: "" },
        { cast_id: "cast_heroine", display_name: "Heroine", identity_prompt: "1girl, silver hair", negative_prompt: "" }
    ];
    docB.pages[0].scenes[0].input_mode = "cast";
    docB.pages[0].character_instances = [
        {
            instance_id: "inst_1",
            cast_id: "cast_heroine",
            scene_id: "scene_1",
            area: { shape_type: "rect", x: 0.1, y: 0.08, w: 0.4, h: 0.22 },
            acting_prompt: "standing",
            order: 1,
            metadata: {}
        }
    ];
    const resB = await page.evaluate((doc) => {
        const tm = window.__tegakiManga;
        tm.store.setDocument(doc);
        if (tm.updateAll) tm.updateAll();
        tm.generation.setGenerationScope("scenes");
        const btn = document.getElementById("mg-generate");
        const reason = document.getElementById("mg-generate-reason");
        return {
            disabled: btn.disabled,
            reason: reason ? reason.textContent.trim() : "",
            scope: tm.generation.getGenerationScope()
        };
    }, docB);
    assert.equal(resB.disabled, false, "Case B: Generate must be enabled with 1 placed instance");
    assert.equal(resB.reason, "", "Case B: No block reason");
    console.log("✓ Check 2 PASS: Multiple CAST definitions alone do not disable Generate; 1 placed instance works");

    // 3. Case C: Three Scenes and TWO CAST definitions, TWO placed Instances in different Scenes
    console.log("\n--- Check 3: Case C (3 scenes, 2 CAST defs, 2 placed instances) ---");
    const docC = createBaseThreeSceneDocument();
    docC.pages[0].cast = [
        { cast_id: "cast_hero", display_name: "Hero", identity_prompt: "1boy, black hair", negative_prompt: "" },
        { cast_id: "cast_heroine", display_name: "Heroine", identity_prompt: "1girl, silver hair", negative_prompt: "" }
    ];
    docC.pages[0].scenes[0].input_mode = "cast";
    docC.pages[0].scenes[1].input_mode = "cast";
    docC.pages[0].character_instances = [
        {
            instance_id: "inst_1",
            cast_id: "cast_heroine",
            scene_id: "scene_1",
            area: { shape_type: "rect", x: 0.1, y: 0.08, w: 0.4, h: 0.22 },
            acting_prompt: "standing",
            order: 1,
            metadata: {}
        },
        {
            instance_id: "inst_2",
            cast_id: "cast_hero",
            scene_id: "scene_2",
            area: { shape_type: "rect", x: 0.1, y: 0.39, w: 0.4, h: 0.22 },
            acting_prompt: "sitting",
            order: 2,
            metadata: {}
        }
    ];
    const resC = await page.evaluate((doc) => {
        const tm = window.__tegakiManga;
        tm.store.setDocument(doc);
        if (tm.updateAll) tm.updateAll();
        tm.generation.setGenerationScope("scenes");
        const btn = document.getElementById("mg-generate");
        const reason = document.getElementById("mg-generate-reason");
        return {
            disabled: btn.disabled,
            reason: reason ? reason.textContent.trim() : "",
            scope: tm.generation.getGenerationScope()
        };
    }, docC);
    assert.equal(resC.disabled, false, "Case C: Generate must be enabled for 2 placed instances");
    assert.equal(resC.reason, "", "Case C: No block reason");
    console.log("✓ Check 3 PASS: Two placed instances across different CAST definitions are supported and enabled");

    // 4. Case D: One CAST definition placed in TWO different Scenes
    console.log("\n--- Check 4: Case D (1 CAST def, placed in 2 different scenes) ---");
    const docD = createBaseThreeSceneDocument();
    docD.pages[0].cast = [
        { cast_id: "cast_heroine", display_name: "Heroine", identity_prompt: "1girl, silver hair", negative_prompt: "" }
    ];
    docD.pages[0].scenes[0].input_mode = "cast";
    docD.pages[0].scenes[1].input_mode = "cast";
    docD.pages[0].character_instances = [
        {
            instance_id: "inst_1",
            cast_id: "cast_heroine",
            scene_id: "scene_1",
            area: { shape_type: "rect", x: 0.1, y: 0.08, w: 0.4, h: 0.22 },
            acting_prompt: "standing",
            order: 1,
            metadata: {}
        },
        {
            instance_id: "inst_2",
            cast_id: "cast_heroine",
            scene_id: "scene_2",
            area: { shape_type: "rect", x: 0.1, y: 0.39, w: 0.4, h: 0.22 },
            acting_prompt: "walking",
            order: 2,
            metadata: {}
        }
    ];
    const resD = await page.evaluate((doc) => {
        const tm = window.__tegakiManga;
        tm.store.setDocument(doc);
        if (tm.updateAll) tm.updateAll();
        tm.generation.setGenerationScope("scenes");
        const btn = document.getElementById("mg-generate");
        const reason = document.getElementById("mg-generate-reason");
        return {
            disabled: btn.disabled,
            reason: reason ? reason.textContent.trim() : "",
            scope: tm.generation.getGenerationScope()
        };
    }, docD);
    assert.equal(resD.disabled, false, "Case D: Generate must be enabled for 2 placed instances of same CAST");
    assert.equal(resD.reason, "", "Case D: No block reason");
    console.log("✓ Check 4 PASS: One CAST placed in two different Scenes is supported and enabled");

    // 4b. Case E: Two different active Reference assets across instances
    console.log("\n--- Check 4b: Case E (2 different reference assets) ---");
    const docE = createBaseThreeSceneDocument();
    docE.pages[0].cast = [
        { cast_id: "cast_hero", display_name: "Hero", identity_prompt: "1boy", negative_prompt: "", reference_asset: "tegaki_manga_references/ref_hero.png" },
        { cast_id: "cast_heroine", display_name: "Heroine", identity_prompt: "1girl", negative_prompt: "", reference_asset: "tegaki_manga_references/ref_heroine.png" }
    ];
    docE.pages[0].scenes[0].input_mode = "cast";
    docE.pages[0].scenes[1].input_mode = "cast";
    docE.pages[0].character_instances = [
        { instance_id: "inst_1", cast_id: "cast_heroine", scene_id: "scene_1", area: { shape_type: "rect", x: 0.1, y: 0.08, w: 0.4, h: 0.22 }, acting_prompt: "standing", order: 1, metadata: {} },
        { instance_id: "inst_2", cast_id: "cast_hero", scene_id: "scene_2", area: { shape_type: "rect", x: 0.1, y: 0.39, w: 0.4, h: 0.22 }, acting_prompt: "sitting", order: 2, metadata: {} }
    ];
    const resE = await page.evaluate((doc) => {
        const tm = window.__tegakiManga;
        tm.store.setDocument(doc);
        if (tm.updateAll) tm.updateAll();
        tm.generation.setGenerationScope("scenes");
        const btn = document.getElementById("mg-generate");
        const reason = document.getElementById("mg-generate-reason");
        return {
            disabled: btn.disabled,
            reason: reason ? reason.textContent.trim() : "",
            scope: tm.generation.getGenerationScope()
        };
    }, docE);
    assert.equal(resE.disabled, true, "Case E: Generate must be disabled for 2 different reference assets");
    assert.equal(resE.reason, "Scenes generation currently supports at most one active Character Reference across instances.", "Case E: Correct block reason");
    console.log("✓ Check 4b PASS: Case E disabled with actionable error for multiple active references");

    // 4c. Case F: Three placed instances
    console.log("\n--- Check 4c: Case F (3 placed instances) ---");
    const docF = createBaseThreeSceneDocument();
    docF.pages[0].cast = [
        { cast_id: "cast_heroine", display_name: "Heroine", identity_prompt: "1girl", negative_prompt: "" }
    ];
    docF.pages[0].scenes[0].input_mode = "cast";
    docF.pages[0].scenes[1].input_mode = "cast";
    docF.pages[0].scenes[2].input_mode = "cast";
    docF.pages[0].character_instances = [
        { instance_id: "inst_1", cast_id: "cast_heroine", scene_id: "scene_1", area: { shape_type: "rect", x: 0.1, y: 0.08, w: 0.4, h: 0.22 }, acting_prompt: "standing", order: 1, metadata: {} },
        { instance_id: "inst_2", cast_id: "cast_heroine", scene_id: "scene_2", area: { shape_type: "rect", x: 0.1, y: 0.39, w: 0.4, h: 0.22 }, acting_prompt: "sitting", order: 2, metadata: {} },
        { instance_id: "inst_3", cast_id: "cast_heroine", scene_id: "scene_3", area: { shape_type: "rect", x: 0.1, y: 0.70, w: 0.4, h: 0.22 }, acting_prompt: "walking", order: 3, metadata: {} }
    ];
    const resF = await page.evaluate((doc) => {
        const tm = window.__tegakiManga;
        tm.store.setDocument(doc);
        if (tm.updateAll) tm.updateAll();
        tm.generation.setGenerationScope("scenes");
        const btn = document.getElementById("mg-generate");
        const reason = document.getElementById("mg-generate-reason");
        return {
            disabled: btn.disabled,
            reason: reason ? reason.textContent.trim() : "",
            scope: tm.generation.getGenerationScope()
        };
    }, docF);
    assert.equal(resF.disabled, true, "Case F: Generate must be disabled for 3 placed instances");
    assert.equal(resF.reason, "Scenes generation currently supports at most two placed Character Instances.", "Case F: Correct block reason");
    console.log("✓ Check 4c PASS: Case F disabled with actionable error for >2 placed instances");

    // 5. Check Global-only generation remains separate
    console.log("\n--- Check 5: Global-only generation remains separate ---");
    const resGlobal = await page.evaluate((doc) => {
        const tm = window.__tegakiManga;
        tm.store.setDocument(doc);
        if (tm.updateAll) tm.updateAll();
        // Switch to global scope
        tm.generation.setGenerationScope("global");
        const btn = document.getElementById("mg-generate");
        const reason = document.getElementById("mg-generate-reason");
        return {
            disabled: btn.disabled,
            reason: reason ? reason.textContent.trim() : "",
            scope: tm.generation.getGenerationScope()
        };
    }, docC); // Using docC which has 2 instances
    assert.equal(resGlobal.disabled, false, "Global scope Generate must remain enabled even with 2 scene instances");
    assert.equal(resGlobal.reason, "", "Global scope has no block reason");
    assert.equal(resGlobal.scope, "global", "Scope is global");
    console.log("✓ Check 5 PASS: Global scope generation is unaffected by scene CAST instances");

    // 6. Check Scene/CAST selection does not change generation scope
    console.log("\n--- Check 6: Scene/CAST selection does not change generation scope ---");
    const resScopeStability = await page.evaluate(() => {
        const tm = window.__tegakiManga;
        tm.generation.setGenerationScope("scenes");
        const initialScope = tm.generation.getGenerationScope();

        // Select scene 1
        tm.session.selectScene("scene_1");
        const scopeAfterScene = tm.generation.getGenerationScope();

        // Select instance 1
        tm.session.selectInstance("inst_1");
        const scopeAfterInstance = tm.generation.getGenerationScope();

        // Select scene 2
        tm.session.selectScene("scene_2");
        const scopeAfterScene2 = tm.generation.getGenerationScope();

        // Deselect
        tm.session.selectScene(null);
        tm.session.selectInstance(null);
        const scopeAfterDeselect = tm.generation.getGenerationScope();

        return {
            initialScope,
            scopeAfterScene,
            scopeAfterInstance,
            scopeAfterScene2,
            scopeAfterDeselect
        };
    });
    assert.equal(resScopeStability.initialScope, "scenes");
    assert.equal(resScopeStability.scopeAfterScene, "scenes");
    assert.equal(resScopeStability.scopeAfterInstance, "scenes");
    assert.equal(resScopeStability.scopeAfterScene2, "scenes");
    assert.equal(resScopeStability.scopeAfterDeselect, "scenes");
    console.log("✓ Check 6 PASS: Selection of Scenes and CAST instances does not alter generation scope");

    // 7. Check Reference and Guide assignments persist
    console.log("\n--- Check 7: Reference and Guide assignments persist ---");
    const docWithRefAndGuide = createBaseThreeSceneDocument();
    docWithRefAndGuide.pages[0].cast = [{
        cast_id: "cast_heroine",
        display_name: "Heroine",
        identity_prompt: "1girl, silver hair",
        negative_prompt: "",
        reference_asset: "tegaki_manga_references/ref_c789751db904319d.png"
    }];
    docWithRefAndGuide.pages[0].scenes[0].input_mode = "cast";
    docWithRefAndGuide.pages[0].character_instances = [{
        instance_id: "inst_1",
        cast_id: "cast_heroine",
        scene_id: "scene_1",
        area: { shape_type: "rect", x: 0.1, y: 0.08, w: 0.4, h: 0.22 },
        acting_prompt: "standing",
        order: 1,
        metadata: {}
    }];
    docWithRefAndGuide.pages[0].guides = [{
        guide_id: "guide_1",
        guide_type: "rough_manga",
        enabled: true,
        asset_reference: "tegaki_manga_guides/disposable_guide_char_vase.png",
        placement: { x: 0, y: 0, w: 1, h: 1, scale_x: 1, scale_y: 1 },
        figure_regions: [],
        metadata: {}
    }];
    const resRefGuide = await page.evaluate((doc) => {
        const tm = window.__tegakiManga;
        tm.store.setDocument(doc);
        if (tm.updateAll) tm.updateAll();
        tm.generation.setGenerationScope("scenes");

        // Select different entities
        tm.session.selectScene("scene_2");
        tm.session.selectScene("scene_1");
        tm.session.selectInstance("inst_1");

        const curDoc = tm.store.getDocument();
        const p = curDoc.pages[0];
        return {
            refAsset: p.cast[0]?.reference_asset,
            guideAsset: p.guides[0]?.asset_reference,
            guideEnabled: p.guides[0]?.enabled,
            generateDisabled: document.getElementById("mg-generate").disabled,
            reason: document.getElementById("mg-generate-reason")?.textContent.trim()
        };
    }, docWithRefAndGuide);
    assert.equal(resRefGuide.refAsset, "tegaki_manga_references/ref_c789751db904319d.png");
    assert.equal(resRefGuide.guideAsset, "tegaki_manga_guides/disposable_guide_char_vase.png");
    assert.equal(resRefGuide.guideEnabled, true);
    assert.equal(resRefGuide.generateDisabled, false, "1 placed CAST with Reference and Guide must be enabled");
    assert.equal(resRefGuide.reason, "");
    console.log("✓ Check 7 PASS: Reference and Guide assignments persist through selections and allow generation");

    await browser.close();
    console.log("\nALL CHECKS PASSED!");
}

verifyCastMultiGenerateDiagnosis().catch(err => {
    console.error("Verification failed:", err);
    process.exit(1);
});
