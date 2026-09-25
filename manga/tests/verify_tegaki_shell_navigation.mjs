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

const EVIDENCE_DIR = path.resolve("scratch/navigation_evidence");
if (!fs.existsSync(EVIDENCE_DIR)) {
    fs.mkdirSync(EVIDENCE_DIR, { recursive: true });
}

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
        const btnH3 = document.getElementById("product-h3");
        const btnManga = document.getElementById("product-manga");
        const brandMode = document.getElementById("brand-mode");
        const h3Workspace = document.querySelector(".workspace");
        const mangaPanel = document.getElementById("manga-shell-panel");
        const modeSwitch = document.querySelector(".mode-switch");
        const backendPill = document.getElementById("backend-pill");

        return {
            topbarBg: topbarStyle?.backgroundColor,
            topbarBorder: topbarStyle?.borderBottomColor,
            h3Selected: btnH3?.getAttribute("aria-selected") === "true",
            h3Active: btnH3?.classList.contains("active"),
            mangaSelected: btnManga?.getAttribute("aria-selected") === "false",
            mangaActive: btnManga?.classList.contains("active"),
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
    assert.equal(h3State.h3Selected, true, "H3 button aria-selected must be true");
    assert.equal(h3State.h3Active, true, "H3 button class must contain active");
    assert.equal(h3State.mangaSelected, true, "MANGA button aria-selected must be false");
    assert.equal(h3State.mangaActive, false, "MANGA button class must not contain active");
    assert.equal(h3State.brandMode, "Video", "Brand mode should show media mode (Video)");
    assert.equal(h3State.h3WorkspaceVisible, true, "H3 workspace controls must be visible");
    assert.equal(h3State.mangaPanelHidden, true, "Manga panel must be hidden");
    assert.equal(h3State.modeSwitchVisible, true, "Video / Still mode switch visible");
    await page.screenshot({ path: path.join(EVIDENCE_DIR, "step2_desktop_h3_active.png") });

    // Enter a test prompt into H3 to verify input preservation across domain switches
    const testH3Prompt = "cinematic drone flight through pine forest, 4k ultra detailed";
    const promptInput = await page.$("#prompt");
    if (promptInput) {
        await promptInput.fill(testH3Prompt);
    }

    // Step 3: Click MANGA
    console.log("Step 3: Click MANGA...");
    await page.click("#product-manga");
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
        const btnH3 = document.getElementById("product-h3");
        const btnManga = document.getElementById("product-manga");
        const brandMode = document.getElementById("brand-mode");
        const h3Workspace = document.querySelector(".workspace");
        const mangaPanel = document.getElementById("manga-shell-panel");
        const modeSwitch = document.querySelector(".mode-switch");

        return {
            topbarVisible: topbar ? window.getComputedStyle(topbar).display !== "none" : false,
            h3Selected: btnH3?.getAttribute("aria-selected") === "false",
            mangaSelected: btnManga?.getAttribute("aria-selected") === "true",
            mangaActive: btnManga?.classList.contains("active"),
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
    assert.equal(mangaShellState.mangaSelected, true, "MANGA button aria-selected must be true");
    assert.equal(mangaShellState.mangaActive, true, "MANGA button class must contain active");
    assert.equal(mangaShellState.h3Selected, true, "H3 button aria-selected must be false");
    assert.equal(mangaShellState.brandMode, "MANGA", "Brand mode should show MANGA");
    assert.equal(mangaShellState.h3WorkspaceHidden, true, "H3 workspace hidden");
    assert.equal(mangaShellState.mangaPanelVisible, true, "Manga panel visible");

    // Inspect inside iframe
    const frameElement = await page.$("#manga-workspace-frame");
    const frame = await frameElement.contentFrame();
    await frame.waitForSelector("#mg-generate", { state: "visible", timeout: 15000 });

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

    // Step 5: Click H3
    console.log("Step 5: Click H3...");
    await page.click("#product-h3");
    await page.screenshot({ path: path.join(EVIDENCE_DIR, "step5_desktop_h3_click.png") });

    // Step 6: Confirm actual H3 application loads with H3 active and preserved input
    console.log("Step 6: Confirm actual H3 application loads with H3 active...");
    await page.waitForTimeout(500);

    const h3RestoredState = await page.evaluate(() => {
        const topbar = document.querySelector(".topbar");
        const btnH3 = document.getElementById("product-h3");
        const btnManga = document.getElementById("product-manga");
        const brandMode = document.getElementById("brand-mode");
        const h3Workspace = document.querySelector(".workspace");
        const mangaPanel = document.getElementById("manga-shell-panel");
        const promptInput = document.getElementById("prompt");

        return {
            topbarVisible: topbar ? window.getComputedStyle(topbar).display !== "none" : false,
            bodyProduct: document.body.dataset.product,
            h3Selected: btnH3?.getAttribute("aria-selected") === "true",
            h3Active: btnH3?.classList.contains("active"),
            mangaSelected: btnManga?.getAttribute("aria-selected") === "false",
            brandMode: brandMode?.textContent.trim(),
            h3WorkspaceVisible: h3Workspace ? window.getComputedStyle(h3Workspace).display !== "none" : false,
            mangaPanelHidden: mangaPanel?.hidden === true,
            promptVal: promptInput?.value
        };
    });

    console.log("Step 6 Verification:", h3RestoredState);
    assert.equal(h3RestoredState.bodyProduct, "h3", "Body product must be h3");
    assert.equal(h3RestoredState.h3Selected, true, "H3 button aria-selected must be true");
    assert.equal(h3RestoredState.h3Active, true, "H3 button class must contain active");
    assert.equal(h3RestoredState.brandMode, "Video", "Brand mode should restore Video");
    assert.equal(h3RestoredState.h3WorkspaceVisible, true, "H3 workspace visible");
    assert.equal(h3RestoredState.mangaPanelHidden, true, "Manga panel hidden");
    if (promptInput) {
        assert.equal(h3RestoredState.promptVal, testH3Prompt, "H3 user prompt must be preserved");
    }
    await page.screenshot({ path: path.join(EVIDENCE_DIR, "step6_desktop_h3_restored.png") });

    // Step 7: Return to MANGA
    console.log("Step 7: Return to MANGA...");
    await page.click("#product-manga");
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
            generateVisible: btnGen ? window.getComputedStyle(btnGen).display !== "none" : false
        };
    });

    console.log("Step 8 Verification:", mangaRetainedState);
    assert.equal(mangaRetainedState.createVisible, true, "Create must remain accessible");
    assert.equal(mangaRetainedState.stageVisible, true, "Stage must remain accessible");
    assert.equal(mangaRetainedState.generateVisible, true, "Generate must remain accessible");
    await page.screenshot({ path: path.join(EVIDENCE_DIR, "step8_desktop_manga_accessible.png") });
    console.log("✓ Desktop (1440x900) 8-step sequence PASSED!");
    await desktopContext.close();

    // ------------------------------------------------------------------
    // 1024x768 Viewport
    // ------------------------------------------------------------------
    console.log("\n[Sequence 2] 1024x768 Viewport Verification");
    const context1024 = await browser.newContext({ viewport: { width: 1024, height: 768 } });
    const page1024 = await context1024.newPage();
    await page1024.goto("http://127.0.0.1:8190/", { waitUntil: "networkidle" });
    await page1024.click("#product-manga");
    await page1024.waitForTimeout(1500);
    const frame1024El = await page1024.$("#manga-workspace-frame");
    const frame1024 = await frame1024El.contentFrame();
    await frame1024.waitForSelector("#mg-generate", { state: "visible", timeout: 15000 });
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
    await pageNarrow.click("#product-manga");
    await pageNarrow.waitForTimeout(1500);
    const frameNarrowEl = await pageNarrow.$("#manga-workspace-frame");
    const frameNarrow = await frameNarrowEl.contentFrame();
    await frameNarrow.waitForSelector("#mg-generate", { state: "visible", timeout: 15000 });
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
        const h3Link = document.getElementById("standalone-product-h3");
        const mangaBtn = document.getElementById("standalone-product-manga");
        const heading = document.querySelector(".mg-page-heading");
        const headingStyle = heading ? window.getComputedStyle(heading) : null;

        return {
            navVisible: nav ? navStyle.display !== "none" : false,
            navBg: navStyle?.backgroundColor,
            navBorder: navStyle?.borderBottomColor,
            h3Href: h3Link?.getAttribute("href"),
            mangaActive: mangaBtn?.classList.contains("active"),
            headingHidden: headingStyle?.display === "none"
        };
    });

    console.log("Standalone 8191 Verification:", standaloneNav);
    assert.equal(standaloneNav.navVisible, true, "Standalone nav must be visible");
    assert.equal(standaloneNav.h3Href, "http://127.0.0.1:8190/", "Standalone nav has link back to H3 shell");
    assert.equal(standaloneNav.mangaActive, true, "Standalone Manga button active");
    assert.equal(standaloneNav.headingHidden, true, "Standalone disconnected heading banner is hidden");
    await page8191.screenshot({ path: path.join(EVIDENCE_DIR, "standalone_8191_futaba_header.png") });

    // Test clicking H3 from standalone 8191 navigates to shell at 8190
    await page8191.click("#standalone-product-h3");
    await page8191.waitForURL("http://127.0.0.1:8190/**", { timeout: 10000 });
    assert.ok(page8191.url().includes("8190"), "Clicking H3 from standalone Manga must navigate to H3 shell");
    console.log("✓ Standalone 8191 -> H3 8190 Navigation PASSED!");
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
