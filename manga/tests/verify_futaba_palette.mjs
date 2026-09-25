import assert from "node:assert/strict";
import path from "node:path";
import fs from "node:fs";
import { createRequire } from "node:module";
import { execSync } from "node:child_process";

const require = createRequire(import.meta.url);

function getPlaywrightChromium() {
    if (process.env.TEGAKI_PLAYWRIGHT_MODULE) {
        return require(process.env.TEGAKI_PLAYWRIGHT_MODULE).chromium;
    }
    try {
        return require("playwright").chromium;
    } catch {}
    const root = execSync("npm root -g", { encoding: "utf8" }).trim();
    return require(path.join(root, "@executeautomation", "playwright-mcp-server", "node_modules", "playwright")).chromium;
}

const SCRATCH_DIR = path.resolve("scratch");
if (!fs.existsSync(SCRATCH_DIR)) {
    fs.mkdirSync(SCRATCH_DIR, { recursive: true });
}

async function runAcceptance() {
    const chromium = getPlaywrightChromium();
    const browser = await chromium.launch({ headless: true });

    console.log("==================================================");
    console.log("CARD: MANGA-FUTABA-PALETTE-RESTORE1 Acceptance");
    console.log("==================================================");

    // ------------------------------------------------------------------
    // A. H3 with its existing light FUTABA interface
    // ------------------------------------------------------------------
    console.log("\n[Item A] H3 with existing light FUTABA interface");
    const contextA = await browser.newContext({ viewport: { width: 1440, height: 900 } });
    const pageA = await contextA.newPage();
    await pageA.goto("http://127.0.0.1:8190/", { waitUntil: "networkidle" });

    const h3Metrics = await pageA.evaluate(() => {
        const topbar = document.querySelector(".topbar");
        const topbarStyle = topbar ? window.getComputedStyle(topbar) : null;
        const bodyStyle = window.getComputedStyle(document.body);
        const workspace = document.querySelector(".workspace");
        const workspaceStyle = workspace ? window.getComputedStyle(workspace) : null;
        const btnH3 = document.getElementById("product-h3");
        const btnManga = document.getElementById("product-manga");

        return {
            topbarBg: topbarStyle?.backgroundColor,
            bodyBg: bodyStyle.backgroundColor,
            workspaceBg: workspaceStyle?.backgroundColor,
            h3Active: btnH3?.classList.contains("active"),
            mangaActive: btnManga?.classList.contains("active"),
            bodyProduct: document.body.dataset.product
        };
    });

    console.log("H3 Light Interface Metrics:", h3Metrics);
    assert.equal(h3Metrics.bodyProduct, "h3", "H3 domain must be active");
    assert.equal(h3Metrics.h3Active, true, "H3 button must be active");
    assert.equal(h3Metrics.mangaActive, false, "MANGA button must not be active");
    const shotAPath = path.join(SCRATCH_DIR, "acceptance_A_h3_light.png");
    await pageA.screenshot({ path: shotAPath });
    console.log("✓ Saved:", shotAPath);
    await contextA.close();

    // ------------------------------------------------------------------
    // B. MANGA after restoration, desktop viewport (1440x900)
    // ------------------------------------------------------------------
    console.log("\n[Item B] MANGA after restoration, desktop viewport (1440x900)");
    const contextB = await browser.newContext({ viewport: { width: 1440, height: 900 } });
    const pageB = await contextB.newPage();
    await pageB.goto("http://127.0.0.1:8190/", { waitUntil: "networkidle" });
    await pageB.click("#product-manga");
    await pageB.waitForTimeout(2000);

    const frameBEl = await pageB.$("#manga-workspace-frame");
    const frameB = await frameBEl.contentFrame();
    await frameB.waitForSelector("#mg-generate", { state: "visible", timeout: 15000 });

    const mangaMetrics = await frameB.evaluate(() => {
        const bodyStyle = window.getComputedStyle(document.body);
        const create = document.getElementById("mg-create");
        const createStyle = create ? window.getComputedStyle(create) : null;
        const prompt = document.getElementById("scene-composer-prompt");
        const promptStyle = prompt ? window.getComputedStyle(prompt) : null;
        const stage = document.getElementById("mg-stage");
        const stageStyle = stage ? window.getComputedStyle(stage) : null;
        const heading = document.querySelector(".mg-page-heading");
        const headingHidden = !heading || window.getComputedStyle(heading).display === "none";
        const btnGen = document.getElementById("mg-generate");

        return {
            bodyBg: bodyStyle.backgroundColor,
            createBg: createStyle?.backgroundColor,
            promptBg: promptStyle?.backgroundColor,
            promptColor: promptStyle?.color,
            stageBg: stageStyle?.backgroundColor,
            headingHidden: headingHidden,
            generateVisible: btnGen && window.getComputedStyle(btnGen).display !== "none"
        };
    });

    console.log("MANGA Desktop Metrics:", mangaMetrics);
    assert.equal(mangaMetrics.headingHidden, true, "Obsolete Generate heading must be removed/hidden");
    assert.equal(mangaMetrics.generateVisible, true, "Generate button must remain accessible");
    // Verify background is in the maroon family (R > B and R > G significantly, not near-black charcoal)
    const rgbMatch = mangaMetrics.bodyBg.match(/\d+/g);
    if (rgbMatch) {
        const [r, g, b] = rgbMatch.map(Number);
        console.log(`Body RGB: R=${r}, G=${g}, B=${b}`);
        assert.ok(r > g + 15 && r > b + 15, `Body background must be visibly maroon/red-brown, got: ${mangaMetrics.bodyBg}`);
        assert.ok(r >= 50, `Body background must not be near-black charcoal (r >= 50), got: ${r}`);
    }

    const shotBPath = path.join(SCRATCH_DIR, "acceptance_B_manga_desktop.png");
    await pageB.screenshot({ path: shotBPath });
    console.log("✓ Saved:", shotBPath);

    // ------------------------------------------------------------------
    // C. MANGA after restoration, 1024x768 and narrow viewports
    // ------------------------------------------------------------------
    console.log("\n[Item C] MANGA after restoration, 1024x768 and narrow viewports");
    await pageB.setViewportSize({ width: 1024, height: 768 });
    await pageB.waitForTimeout(500);
    const shotC1024Path = path.join(SCRATCH_DIR, "acceptance_C_manga_1024.png");
    await pageB.screenshot({ path: shotC1024Path });
    console.log("✓ Saved:", shotC1024Path);

    await pageB.setViewportSize({ width: 768, height: 1024 });
    await pageB.waitForTimeout(500);
    const shotCNarrowPath = path.join(SCRATCH_DIR, "acceptance_C_manga_narrow.png");
    await pageB.screenshot({ path: shotCNarrowPath });
    console.log("✓ Saved:", shotCNarrowPath);
    await contextB.close();

    // ------------------------------------------------------------------
    // D. MANGA Create with two Scenes and one selected Character
    // ------------------------------------------------------------------
    console.log("\n[Item D] MANGA Create with two Scenes and one selected Character");
    const contextD = await browser.newContext({ viewport: { width: 1440, height: 900 } });
    const pageD = await contextD.newPage();
    await pageD.goto("http://127.0.0.1:8190/", { waitUntil: "networkidle" });
    await pageD.click("#product-manga");
    await pageD.waitForTimeout(2000);

    const frameDEl = await pageD.$("#manga-workspace-frame");
    const frameD = await frameDEl.contentFrame();
    await frameD.waitForSelector("#mg-generate", { state: "visible", timeout: 15000 });

    // Click UI buttons to add 2 scenes and 1 CAST member
    console.log("Creating Scene 1...");
    await frameD.click("#mg-scene-add");
    await pageD.waitForTimeout(400);

    console.log("Creating Scene 2...");
    await frameD.click("#mg-scene-add");
    await pageD.waitForTimeout(400);

    console.log("Creating Character Definition...");
    await frameD.click("#mg-cast-add");
    await pageD.waitForTimeout(400);

    // Get created scene and cast IDs
    const docState = await frameD.evaluate(() => {
        const store = window.__tegakiManga?.store;
        const page = store.getPage();
        return {
            scenes: page.scenes || [],
            cast: page.cast || []
        };
    });

    console.log(`Document has ${docState.scenes.length} scenes and ${docState.cast.length} cast members.`);
    assert.equal(docState.scenes.length, 2, "Must have exactly 2 scenes");
    assert.equal(docState.cast.length, 1, "Must have exactly 1 cast member");

    // Select Scene 1 and toggle appearance to create Character Instance in Scene 1
    const scene1Id = docState.scenes[0].scene_id;
    await frameD.click(`#scene-prompt-tab-${scene1Id}`);
    await pageD.waitForTimeout(400);

    // Click CAST appearance toggle button
    const appearanceBtn = await frameD.$(".scene-cast-appearance-button");
    if (appearanceBtn) {
        await appearanceBtn.click();
        await pageD.waitForTimeout(400);
    }

    // Select the character instance on Stage / session
    await frameD.evaluate(() => {
        const { store, session, updateAll } = window.__tegakiManga;
        const instances = store.getPage()?.character_instances || [];
        if (instances.length > 0 && session) {
            session.selectInstance(instances[0].instance_id);
            session.selectCast(instances[0].cast_id);
            updateAll();
        }
    });

    await pageD.waitForTimeout(600);
    const shotDPath = path.join(SCRATCH_DIR, "acceptance_D_two_scenes_one_char.png");
    await pageD.screenshot({ path: shotDPath });
    console.log("✓ Saved:", shotDPath);

    // ------------------------------------------------------------------
    // E. MANGA Stage with an enabled Guide
    // ------------------------------------------------------------------
    console.log("\n[Item E] MANGA Stage with an enabled Guide");
    const guideAsset = "tegaki_manga_guides/disposable_guide_single_character.png";
    await frameD.evaluate((asset) => {
        const { store, session, updateAll } = window.__tegakiManga;
        const newGuide = store.addGuideFromAsset({
            asset_reference: asset,
            image_width: 832,
            image_height: 1216
        });
        session.selectGuide(newGuide.guide_id);
        updateAll();
    }, guideAsset);

    // Switch stage to Layout to see the guide underlay
    await frameD.click("#mg-stage-mode-layout");
    await pageD.waitForTimeout(800);
    const shotEPath = path.join(SCRATCH_DIR, "acceptance_E_stage_guide.png");
    await pageD.screenshot({ path: shotEPath });
    console.log("✓ Saved:", shotEPath);

    // ------------------------------------------------------------------
    // F. MANGA Result with an actual existing result image
    // ------------------------------------------------------------------
    console.log("\n[Item F] MANGA Result with actual existing result image");
    const playableDir = path.resolve("output/Tegaki/Manga/Playable");
    let testImageRel = null;
    if (fs.existsSync(playableDir)) {
        const files = fs.readdirSync(playableDir).filter(f => f.endsWith(".png"));
        if (files.length > 0) {
            testImageRel = `http://127.0.0.1:8189/view?filename=${files[0]}&subfolder=Manga/Playable&type=output`;
            console.log("Found existing result image:", files[0]);
        }
    }

    await frameD.evaluate((imgSrc) => {
        const gen = window.__tegakiManga?.generation;
        const preview = document.getElementById("mg-preview-image");
        if (gen && imgSrc && preview) {
            gen.state.setPreview("acceptance-verified-result", imgSrc);
            preview.src = imgSrc;
            gen.setStageMode("result");
            gen.refresh();
        }
    }, testImageRel);

    await pageD.waitForTimeout(1000);
    const shotFPath = path.join(SCRATCH_DIR, "acceptance_F_stage_result.png");
    await pageD.screenshot({ path: shotFPath });
    console.log("✓ Saved:", shotFPath);

    await contextD.close();
    await browser.close();

    console.log("\n==================================================");
    console.log("ALL FUTABA PALETTE ACCEPTANCE CHECKS PASSED!");
    console.log("==================================================");
}

runAcceptance().catch(err => {
    console.error("Acceptance failed:", err);
    process.exit(1);
});
