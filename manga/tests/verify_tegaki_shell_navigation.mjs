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

const EVIDENCE_DIR = path.resolve("scratch/navigation_evidence", `run-${process.pid}-${Date.now()}`);
if (!fs.existsSync(EVIDENCE_DIR)) {
    fs.mkdirSync(EVIDENCE_DIR, { recursive: true });
}
console.log("Evidence directory:", EVIDENCE_DIR);

async function runAcceptanceSequence() {
    const chromium = getPlaywrightChromium();
    const browser = await chromium.launch({ headless: true });

    console.log("==================================================");
    console.log("CARD: MANGA-H3-SHELL-NAVIGATION-RESTORE1 Acceptance");
    console.log("==================================================");

    // ------------------------------------------------------------------
    // Desktop Viewport: 1440x900 - Full 8-step sequence
    // ------------------------------------------------------------------
    console.log("\n[Sequence 1] Desktop (1440x900) - Full 8 Steps");
    const desktopContext = await browser.newContext({ viewport: { width: 1440, height: 900 } });
    const page = await desktopContext.newPage();

    // Step 1: Open normal TEGAKI H3 entry (http://127.0.0.1:8190/)
    console.log("Step 1: Open normal TEGAKI H3 entry (http://127.0.0.1:8190/)...");
    await page.goto("http://127.0.0.1:8190/", { waitUntil: "networkidle" });
    await page.screenshot({ path: path.join(EVIDENCE_DIR, "step1_desktop_h3_entry.png") });

    // Step 2: Confirm the H3 domain is active
    console.log("Step 2: Confirm H3 domain is active...");
    const h3State = await page.evaluate(() => {
        const topbar = document.querySelector(".topbar");
        const topbarStyle = topbar ? window.getComputedStyle(topbar) : null;
        const modeMovie = document.getElementById("mode-video");
        const modeIllust = document.getElementById("mode-still");
        const modeManga = document.getElementById("product-manga");
        const engineH3 = document.getElementById("product-h3");
        const engineComfyui = document.getElementById("creation-engine-comfyui");
        const engineEasyReforge = document.getElementById("creation-engine-easyreforge");
        const brandMode = document.getElementById("brand-mode");
        const h3Workspace = document.querySelector(".workspace");
        const mangaPanel = document.getElementById("manga-shell-panel");
        const modeSwitch = document.querySelector(".mode-switch");
        const backendPill = document.getElementById("backend-pill");

        return {
            topbarBg: topbarStyle?.backgroundColor,
            topbarBorder: topbarStyle?.borderBottomColor,
            topbarFits: topbar ? topbar.scrollWidth <= topbar.clientWidth + 1 : false,
            topbarHeight: topbar ? Math.round(topbar.getBoundingClientRect().height) : 0,
            movieSelected: modeMovie?.getAttribute("aria-pressed") === "true",
            illustSelected: modeIllust?.getAttribute("aria-pressed") === "true",
            mangaSelected: modeManga?.getAttribute("aria-pressed") === "true",
            h3Selected: engineH3?.getAttribute("aria-pressed") === "true",
            comfyuiSelected: engineComfyui?.getAttribute("aria-pressed") === "true",
            easyReforgeDisabled: engineEasyReforge?.disabled === true,
            brandMode: brandMode?.textContent.trim(),
            h3WorkspaceVisible: h3Workspace ? window.getComputedStyle(h3Workspace).display !== "none" : false,
            mangaPanelHidden: mangaPanel?.hidden === true,
            modeSwitchVisible: modeSwitch ? window.getComputedStyle(modeSwitch).display !== "none" : false,
            backendPillVisible: backendPill ? window.getComputedStyle(backendPill).display !== "none" : false,
            bodyProduct: document.body.dataset.product
        };
    });

    console.log("Step 2 Verification:", h3State);
    assert.equal(h3State.bodyProduct, "h3", "Body product must be h3");
    assert.equal(h3State.topbarFits, true, "Desktop routing header must not overflow horizontally");
    assert.ok(h3State.topbarHeight <= 80, "Desktop routing header must remain compact");
    assert.equal(h3State.movieSelected, true, "Movie mode must be selected on the H3 entry route");
    assert.equal(h3State.illustSelected, false, "Illust mode must not be selected on the H3 entry route");
    assert.equal(h3State.mangaSelected, false, "Manga mode must not be selected on the H3 entry route");
    assert.equal(h3State.h3Selected, true, "H3 engine must be selected on the H3 entry route");
    assert.equal(h3State.comfyuiSelected, false, "ComfyUI engine must not be selected on the H3 entry route");
    assert.equal(h3State.easyReforgeDisabled, true, "EasyReforge must remain unavailable");
    assert.equal(h3State.brandMode, "Video", "Brand mode should show media mode (Video)");
    assert.equal(h3State.h3WorkspaceVisible, true, "H3 workspace controls must be visible");
    assert.equal(h3State.mangaPanelHidden, true, "Manga panel must be hidden");
    assert.equal(h3State.modeSwitchVisible, true, "Existing H3 Prep/Edit control remains visible");
    await page.screenshot({ path: path.join(EVIDENCE_DIR, "step2_desktop_h3_active.png") });

    // Enter a test prompt into H3 to verify input preservation across domain switches
    const testH3Prompt = "cinematic drone flight through pine forest, 4k ultra detailed";
    const promptInput = await page.$("#prompt");
    if (promptInput) {
        await promptInput.fill(testH3Prompt);
    }

    // Step 3: Select COMFYUI and verify its supported mode is chosen.
    console.log("Step 3: Select COMFYUI...");
    await page.click("#creation-engine-comfyui");
    await page.screenshot({ path: path.join(EVIDENCE_DIR, "step3_desktop_manga_click.png") });

    // Step 4: Confirm actual Manga workspace loads with MANGA active
    console.log("Step 4: Confirm actual Manga workspace loads...");
    await page.waitForFunction(() => {
        const frame = document.getElementById("manga-workspace-frame");
        return frame && frame.getAttribute("src") && frame.getAttribute("src").includes("8191");
    });
    // Wait for the iframe DOM to settle
    await page.waitForTimeout(2000);

    const mangaShellState = await page.evaluate(() => {
        const topbar = document.querySelector(".topbar");
        const modeMovie = document.getElementById("mode-video");
        const modeIllust = document.getElementById("mode-still");
        const modeManga = document.getElementById("product-manga");
        const engineH3 = document.getElementById("product-h3");
        const engineComfyui = document.getElementById("creation-engine-comfyui");
        const brandMode = document.getElementById("brand-mode");
        const h3Workspace = document.querySelector(".workspace");
        const mangaPanel = document.getElementById("manga-shell-panel");
        const modeSwitch = document.querySelector(".mode-switch");

        return {
            topbarVisible: topbar ? window.getComputedStyle(topbar).display !== "none" : false,
            movieSelected: modeMovie?.getAttribute("aria-pressed") === "true",
            illustSelected: modeIllust?.getAttribute("aria-pressed") === "true",
            mangaSelected: modeManga?.getAttribute("aria-pressed") === "true",
            h3Selected: engineH3?.getAttribute("aria-pressed") === "true",
            comfyuiSelected: engineComfyui?.getAttribute("aria-pressed") === "true",
            brandMode: brandMode?.textContent.trim(),
            h3WorkspaceHidden: h3Workspace ? window.getComputedStyle(h3Workspace).display === "none" : true,
            mangaPanelVisible: mangaPanel ? window.getComputedStyle(mangaPanel).display !== "none" : false,
            modeSwitchHidden: modeSwitch ? window.getComputedStyle(modeSwitch).display === "none" : true,
            bodyProduct: document.body.dataset.product
        };
    });

    console.log("Step 4 Shell Verification:", mangaShellState);
    assert.equal(mangaShellState.topbarVisible, true, "Shared FUTABA topbar must remain visible");
    assert.equal(mangaShellState.bodyProduct, "manga", "Body product must be manga");
    assert.equal(mangaShellState.mangaSelected, true, "Manga mode must be selected on the Manga route");
    assert.equal(mangaShellState.movieSelected, false, "Movie mode must not be selected on the Manga route");
    assert.equal(mangaShellState.illustSelected, false, "Illust mode must not be selected on the Manga route");
    assert.equal(mangaShellState.comfyuiSelected, true, "ComfyUI engine must be selected on the Manga route");
    assert.equal(mangaShellState.h3Selected, false, "H3 engine must not be selected on the Manga route");
    assert.equal(mangaShellState.brandMode, "MANGA", "Brand mode should show MANGA");
    assert.equal(mangaShellState.h3WorkspaceHidden, true, "H3 workspace hidden");
    assert.equal(mangaShellState.mangaPanelVisible, true, "Manga panel visible");

    // Inspect inside iframe
    const frameElement = await page.$("#manga-workspace-frame");
    const frame = await frameElement.contentFrame();
    await frame.waitForSelector("#mg-generate", { state: "visible", timeout: 15000 });
    const testMangaPrompt = "Manga-only scene prompt for route retention";
    await frame.locator("#scene-composer-prompt").fill(testMangaPrompt);
    const mangaGenerationStateBefore = await frame.evaluate(() => ({
        prompt: document.getElementById("scene-composer-prompt")?.value,
        checkpoint: document.getElementById("mg-checkpoint_id")?.value
    }));
    assert.equal(mangaGenerationStateBefore.prompt, testMangaPrompt, "Manga test prompt must be set independently");
    assert.notEqual(mangaGenerationStateBefore.prompt, testH3Prompt, "H3 prompt must not be copied into Manga state");

    const mangaFrameState = await frame.evaluate(() => {
        const create = document.getElementById("mg-create");
        const stage = document.getElementById("mg-stage");
        const btnGen = document.getElementById("mg-generate");
        const nav = document.getElementById("manga-mode-nav");
        const heading = document.querySelector(".mg-page-heading");

        return {
            hasCreate: Boolean(create) && window.getComputedStyle(create).display !== "none",
            hasStage: Boolean(stage) && window.getComputedStyle(stage).display !== "none",
            hasGenerate: Boolean(btnGen) && window.getComputedStyle(btnGen).display !== "none",
            navHiddenInEmbed: nav ? window.getComputedStyle(nav).display === "none" : true,
            headingHiddenInEmbed: heading ? window.getComputedStyle(heading).display === "none" : true
        };
    });

    console.log("Step 4 Frame Verification:", mangaFrameState);
    assert.equal(mangaFrameState.hasCreate, true, "Create section must be visible");
    assert.equal(mangaFrameState.hasStage, true, "Stage section must be visible");
    assert.equal(mangaFrameState.hasGenerate, true, "Generate button must be visible");
    assert.equal(mangaFrameState.navHiddenInEmbed, true, "Embedded iframe must hide internal redundant nav");
    assert.equal(mangaFrameState.headingHiddenInEmbed, true, "Embedded iframe must hide standalone heading banner");
    await page.screenshot({ path: path.join(EVIDENCE_DIR, "step4_desktop_manga_workspace.png") });

    // Step 5: Select ILLUST and verify it reconciles to H3.
    console.log("Step 5: Select ILLUST...");
    await page.click("#mode-still");
    await page.screenshot({ path: path.join(EVIDENCE_DIR, "step5_desktop_h3_click.png") });

    // Step 6: Confirm actual H3 application loads with H3 active and preserved input
    console.log("Step 6: Confirm actual H3 application loads with H3 active...");
    await page.waitForTimeout(500);

    const h3RestoredState = await page.evaluate(() => {
        const topbar = document.querySelector(".topbar");
        const modeMovie = document.getElementById("mode-video");
        const modeIllust = document.getElementById("mode-still");
        const modeManga = document.getElementById("product-manga");
        const engineH3 = document.getElementById("product-h3");
        const engineComfyui = document.getElementById("creation-engine-comfyui");
        const brandMode = document.getElementById("brand-mode");
        const h3Workspace = document.querySelector(".workspace");
        const mangaPanel = document.getElementById("manga-shell-panel");
        const promptInput = document.getElementById("prompt");

        return {
            topbarVisible: topbar ? window.getComputedStyle(topbar).display !== "none" : false,
            bodyProduct: document.body.dataset.product,
            movieSelected: modeMovie?.getAttribute("aria-pressed") === "true",
            illustSelected: modeIllust?.getAttribute("aria-pressed") === "true",
            mangaSelected: modeManga?.getAttribute("aria-pressed") === "true",
            h3Selected: engineH3?.getAttribute("aria-pressed") === "true",
            comfyuiSelected: engineComfyui?.getAttribute("aria-pressed") === "true",
            brandMode: brandMode?.textContent.trim(),
            h3WorkspaceVisible: h3Workspace ? window.getComputedStyle(h3Workspace).display !== "none" : false,
            mangaPanelHidden: mangaPanel?.hidden === true,
            promptVal: promptInput?.value
        };
    });

    console.log("Step 6 Verification:", h3RestoredState);
    assert.equal(h3RestoredState.bodyProduct, "h3", "Body product must be h3");
    assert.equal(h3RestoredState.movieSelected, false, "Movie mode must not remain selected after choosing Illust");
    assert.equal(h3RestoredState.illustSelected, true, "Choosing Illust must activate the Illust mode");
    assert.equal(h3RestoredState.mangaSelected, false, "Manga mode must not remain selected after switching to H3");
    assert.equal(h3RestoredState.h3Selected, true, "H3 engine must be selected after switching from Manga");
    assert.equal(h3RestoredState.comfyuiSelected, false, "ComfyUI engine must not remain selected after switching to H3");
    assert.equal(h3RestoredState.brandMode, "Still", "Illust mode must use the existing H3 Still workspace behavior");
    assert.equal(h3RestoredState.h3WorkspaceVisible, true, "H3 workspace visible");
    assert.equal(h3RestoredState.mangaPanelHidden, true, "Manga panel hidden");
    if (promptInput) {
        assert.equal(h3RestoredState.promptVal, testH3Prompt, "H3 user prompt must be preserved");
    }
    await page.screenshot({ path: path.join(EVIDENCE_DIR, "step6_desktop_h3_restored.png") });

    // Step 7: Return to MANGA
    console.log("Step 7: Return to MANGA...");
    await page.click("#creation-engine-comfyui");
    await page.waitForTimeout(500);
    await page.screenshot({ path: path.join(EVIDENCE_DIR, "step7_desktop_manga_return.png") });

    // Step 8: Confirm Create, Stage and Generate remain accessible
    console.log("Step 8: Confirm Create, Stage and Generate remain accessible...");
    const mangaRetainedState = await frame.evaluate(() => {
        const create = document.getElementById("mg-create");
        const stage = document.getElementById("mg-stage");
        const btnGen = document.getElementById("mg-generate");

        return {
            createVisible: create ? window.getComputedStyle(create).display !== "none" : false,
            stageVisible: stage ? window.getComputedStyle(stage).display !== "none" : false,
            generateVisible: btnGen ? window.getComputedStyle(btnGen).display !== "none" : false,
            prompt: document.getElementById("scene-composer-prompt")?.value,
            checkpoint: document.getElementById("mg-checkpoint_id")?.value
        };
    });
    const hiddenH3State = await page.evaluate(() => ({
        prompt: document.getElementById("prompt")?.value,
        promptConnected: document.getElementById("prompt")?.isConnected === true
    }));

    console.log("Step 8 Verification:", mangaRetainedState);
    console.log("Step 8 H3 retention while Manga is active:", hiddenH3State);
    assert.equal(mangaRetainedState.createVisible, true, "Create must remain accessible");
    assert.equal(mangaRetainedState.stageVisible, true, "Stage must remain accessible");
    assert.equal(mangaRetainedState.generateVisible, true, "Generate must remain accessible");
    assert.equal(mangaRetainedState.prompt, mangaGenerationStateBefore.prompt, "Header routing must retain Manga prompt state");
    assert.equal(mangaRetainedState.checkpoint, mangaGenerationStateBefore.checkpoint, "Header routing must retain Manga checkpoint state");
    assert.equal(hiddenH3State.promptConnected, true, "H3 prompt DOM must remain mounted while Manga is active");
    assert.equal(hiddenH3State.prompt, testH3Prompt, "Manga state must not replace the retained H3 prompt");
    await page.screenshot({ path: path.join(EVIDENCE_DIR, "step8_desktop_manga_accessible.png") });

    // Step 9: Return to MOVIE/H3 and verify the H3 prompt remains isolated and intact.
    console.log("Step 9: Return to MOVIE/H3...");
    await page.click("#mode-video");
    await page.waitForTimeout(500);
    const movieRestoredState = await page.evaluate(() => ({
        bodyProduct: document.body.dataset.product,
        movieSelected: document.getElementById("mode-video")?.getAttribute("aria-pressed") === "true",
        illustSelected: document.getElementById("mode-still")?.getAttribute("aria-pressed") === "true",
        mangaSelected: document.getElementById("product-manga")?.getAttribute("aria-pressed") === "true",
        h3Selected: document.getElementById("product-h3")?.getAttribute("aria-pressed") === "true",
        comfyuiSelected: document.getElementById("creation-engine-comfyui")?.getAttribute("aria-pressed") === "true",
        brandMode: document.getElementById("brand-mode")?.textContent.trim(),
        prompt: document.getElementById("prompt")?.value
    }));
    assert.equal(movieRestoredState.bodyProduct, "h3", "Returning to Movie must restore the H3 product");
    assert.equal(movieRestoredState.movieSelected, true, "Movie mode must be selected on the H3 return route");
    assert.equal(movieRestoredState.illustSelected, false, "Illust mode must not remain selected on the Movie route");
    assert.equal(movieRestoredState.mangaSelected, false, "Manga must not remain selected on the H3 Movie route");
    assert.equal(movieRestoredState.h3Selected, true, "H3 engine must be selected on the Movie route");
    assert.equal(movieRestoredState.comfyuiSelected, false, "ComfyUI must not remain selected on the H3 Movie route");
    assert.equal(movieRestoredState.brandMode, "Video", "Movie route must use the existing H3 Video workspace");
    assert.equal(movieRestoredState.prompt, testH3Prompt, "Manga state must not replace the H3 prompt on return to Movie");
    await page.screenshot({ path: path.join(EVIDENCE_DIR, "step9_desktop_movie_h3_restored.png") });
    console.log("✓ Desktop (1440x900) 9-step sequence PASSED!");
    await desktopContext.close();

    // ------------------------------------------------------------------
    // 1024x768 Viewport
    // ------------------------------------------------------------------
    console.log("\n[Sequence 2] 1024x768 Viewport Verification");
    const context1024 = await browser.newContext({ viewport: { width: 1024, height: 768 } });
    const page1024 = await context1024.newPage();
    await page1024.goto("http://127.0.0.1:8190/", { waitUntil: "networkidle" });
    await page1024.click("#creation-engine-comfyui");
    await page1024.waitForTimeout(1500);
    const frame1024El = await page1024.$("#manga-workspace-frame");
    const frame1024 = await frame1024El.contentFrame();
    await frame1024.waitForSelector("#mg-generate", { state: "visible", timeout: 15000 });
    const header1024 = await page1024.evaluate(() => {
        const header = document.querySelector(".topbar");
        return { fits: header ? header.scrollWidth <= header.clientWidth + 1 : false };
    });
    assert.equal(header1024.fits, true, "1024px routing header must not overflow horizontally");
    await page1024.screenshot({ path: path.join(EVIDENCE_DIR, "shell_1024x768_manga.png") });
    console.log("✓ 1024x768 PASSED!");
    await context1024.close();

    // ------------------------------------------------------------------
    // Narrow Viewport (768x1024, <= 820px)
    // ------------------------------------------------------------------
    console.log("\n[Sequence 3] Narrow Viewport (768x1024 <= 820px)");
    const contextNarrow = await browser.newContext({ viewport: { width: 768, height: 1024 } });
    const pageNarrow = await contextNarrow.newPage();
    await pageNarrow.goto("http://127.0.0.1:8190/", { waitUntil: "networkidle" });
    await pageNarrow.click("#creation-engine-comfyui");
    await pageNarrow.waitForTimeout(1500);
    const frameNarrowEl = await pageNarrow.$("#manga-workspace-frame");
    const frameNarrow = await frameNarrowEl.contentFrame();
    await frameNarrow.waitForSelector("#mg-generate", { state: "visible", timeout: 15000 });
    const headerNarrow = await pageNarrow.evaluate(() => {
        const header = document.querySelector(".topbar");
        return { fits: header ? header.scrollWidth <= header.clientWidth + 1 : false };
    });
    assert.equal(headerNarrow.fits, true, "768px routing header must not overflow horizontally");
    await pageNarrow.screenshot({ path: path.join(EVIDENCE_DIR, "shell_narrow_manga.png") });
    console.log("✓ Narrow Viewport PASSED!");
    await contextNarrow.close();

    // ------------------------------------------------------------------
    // Standalone Port 8191 Viewport Verification
    // ------------------------------------------------------------------
    console.log("\n[Sequence 4] Standalone 8191 Navigation & FUTABA Header Alignment");
    const context8191 = await browser.newContext({ viewport: { width: 1440, height: 900 } });
    const page8191 = await context8191.newPage();
    await page8191.goto("http://127.0.0.1:8191/", { waitUntil: "networkidle" });

    const standaloneNav = await page8191.evaluate(() => {
        const nav = document.getElementById("manga-mode-nav");
        const navStyle = nav ? window.getComputedStyle(nav) : null;
        const movieLink = document.getElementById("standalone-mode-movie");
        const illustLink = document.getElementById("standalone-mode-illust");
        const mangaBtn = document.getElementById("standalone-product-manga");
        const h3Link = document.getElementById("standalone-product-h3");
        const comfyuiBtn = document.getElementById("standalone-engine-comfyui");
        const easyReforgeBtn = document.querySelector(".creation-route-group[aria-label='Engine'] button[disabled]");
        const heading = document.querySelector(".mg-page-heading");
        const headingStyle = heading ? window.getComputedStyle(heading) : null;
        const modeGroup = nav?.querySelector(".creation-route-group[aria-label='Creation mode']");
        const engineGroup = nav?.querySelector(".creation-route-group[aria-label='Engine']");

        return {
            navVisible: nav ? navStyle.display !== "none" : false,
            navFits: nav ? nav.scrollWidth <= nav.clientWidth + 1 : false,
            navHeight: nav ? Math.round(nav.getBoundingClientRect().height) : 0,
            navBg: navStyle?.backgroundColor,
            navBorder: navStyle?.borderBottomColor,
            modeLabel: modeGroup?.querySelector(".creation-route-label")?.textContent.trim(),
            engineLabel: engineGroup?.querySelector(".creation-route-label")?.textContent.trim(),
            activeMode: modeGroup?.querySelector(".creation-route-choice.active")?.textContent.trim(),
            activeEngine: engineGroup?.querySelector(".creation-route-choice.active")?.textContent.trim(),
            movieHref: movieLink?.getAttribute("href"),
            illustHref: illustLink?.getAttribute("href"),
            h3Href: h3Link?.getAttribute("href"),
            mangaActive: mangaBtn?.classList.contains("active"),
            comfyuiActive: comfyuiBtn?.classList.contains("active"),
            easyReforgeDisabled: easyReforgeBtn?.disabled === true,
            duplicateHeadingVisible: heading ? headingStyle?.display !== "none" : false
        };
    });

    console.log("Standalone 8191 Verification:", standaloneNav);
    assert.equal(standaloneNav.navVisible, true, "Standalone nav must be visible");
    assert.equal(standaloneNav.navFits, true, "Desktop standalone routing header must not overflow");
    assert.ok(standaloneNav.navHeight <= 64, "Desktop standalone routing header must remain compact");
    assert.equal(standaloneNav.modeLabel, "MODE", "Standalone route header must label the creation mode");
    assert.equal(standaloneNav.engineLabel, "ENGINE", "Standalone route header must label the engine");
    assert.equal(standaloneNav.activeMode, "MANGA", "Standalone route header must identify MANGA as the active mode");
    assert.equal(standaloneNav.activeEngine, "COMFYUI", "Standalone route header must identify COMFYUI as the active engine");
    assert.equal(standaloneNav.movieHref, "http://127.0.0.1:8190/?creation_mode=movie", "Movie mode routes to the H3 entrypoint");
    assert.equal(standaloneNav.illustHref, "http://127.0.0.1:8190/?creation_mode=illust", "Illust mode routes to H3 Still");
    assert.equal(standaloneNav.h3Href, "http://127.0.0.1:8190/?creation_mode=movie", "H3 engine routes to its canonical Movie mode");
    assert.equal(standaloneNav.mangaActive, true, "Standalone Manga mode active");
    assert.equal(standaloneNav.comfyuiActive, true, "Standalone ComfyUI engine active");
    assert.equal(standaloneNav.easyReforgeDisabled, true, "Standalone EasyReforge remains unavailable");
    assert.equal(standaloneNav.duplicateHeadingVisible, false, "Standalone route header must not have a visible duplicate Manga heading");
    await page8191.screenshot({ path: path.join(EVIDENCE_DIR, "standalone_8191_futaba_header.png") });

    // Test clicking H3 from standalone 8191 navigates to shell at 8190
    await page8191.click("#standalone-mode-illust");
    await page8191.waitForURL("http://127.0.0.1:8190/?creation_mode=illust", { timeout: 10000 });
    const standaloneIllustState = await page8191.evaluate(() => ({
        modeIllust: document.getElementById("mode-still")?.getAttribute("aria-pressed") === "true",
        engineH3: document.getElementById("product-h3")?.getAttribute("aria-pressed") === "true",
        bodyProduct: document.body.dataset.product
    }));
    assert.deepEqual(standaloneIllustState, { modeIllust: true, engineH3: true, bodyProduct: "h3" }, "Standalone Illust route loads the H3 workspace coherently");
    await page8191.reload();
    const standaloneIllustReload = await page8191.evaluate(() => ({
        modeIllust: document.getElementById("mode-still")?.getAttribute("aria-pressed") === "true",
        engineH3: document.getElementById("product-h3")?.getAttribute("aria-pressed") === "true"
    }));
    assert.deepEqual(standaloneIllustReload, { modeIllust: true, engineH3: true }, "The H3 URL reconstructs its valid route after reload");
    console.log("✓ Standalone 8191 -> H3 Illust route and reload PASSED!");
    await context8191.close();

    await browser.close();
    console.log("\n==================================================");
    console.log("ALL ACCEPTANCE CHECKS PASSED SUCCESSFULLY!");
    console.log("==================================================");
}

runAcceptanceSequence().catch(err => {
    console.error("Test failed:", err);
    process.exit(1);
});
