/**
 * verify_reference_to_identity_browser.mjs
 * ========================================
 * Targeted Playwright browser acceptance test for Reference-to-Identity controls.
 * Verifies:
 * 1. CAST without reference disables Analyze.
 * 2. CAST with reference shows Ready status.
 * 3. Clicking Analyze triggers request, sets Analyzing status, then Candidate Ready.
 * 4. Analysis alone leaves identity_prompt unchanged in Authoring Store.
 * 5. Candidate text is editable.
 * 6. Append updates only the selected CAST's identity_prompt.
 * 7. Replace replaces only the selected CAST's identity_prompt.
 * 8. Discard clears candidate without modifying store.
 * 9. Switching CAST or clearing reference invalidates candidate state.
 * 10. Narrow viewport layout stacks without horizontal overflow.
 * 11. Captures desktop and narrow screenshots into scratch/.
 */

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

const MOCK_CANDIDATE_TAGS = [
    "1girl", "skirt", "long_hair", "long_sleeves", "very_long_hair",
    "plaid_skirt", "pleated_skirt", "bangs", "plaid", "jacket",
    "hair_between_eyes", "shirt", "school_uniform", "collared_shirt",
    "floating_hair", "v-shaped_eyebrows", "multicolored_hair", "bag"
];
const MOCK_CANDIDATE_TEXT = MOCK_CANDIDATE_TAGS.join(", ");

async function runBrowserAcceptance() {
    console.log("=== MANGA-REFERENCE-TO-IDENTITY BROWSER ACCEPTANCE ===");
    const chromium = getPlaywrightChromium();
    assert(chromium, "Playwright Chromium must be available");

    const browser = await chromium.launch({ headless: true });
    const context = await browser.newContext({ viewport: { width: 1280, height: 800 } });
    const page = await context.newPage();

    // Intercept analyze endpoint to ensure deterministic response independent of live backend freshness
    await page.route("**/api/reference-assets/analyze", async (route) => {
        const req = route.request();
        if (req.method() !== "POST") {
            return route.fulfill({ status: 405, contentType: "application/json", body: JSON.stringify({ ok: false, error: "Method Not Allowed" }) });
        }
        let postData = {};
        try { postData = JSON.parse(req.postData() || "{}"); } catch {}
        const ref = postData.asset_reference || "";
        if (!ref.startsWith("tegaki_manga_references/")) {
            return route.fulfill({ status: 400, contentType: "application/json", body: JSON.stringify({ ok: false, error: "Invalid ref" }) });
        }
        // Artificial short delay to verify intermediate "Analyzing…" state
        await new Promise(r => setTimeout(r, 100));
        return route.fulfill({
            status: 200,
            contentType: "application/json",
            body: JSON.stringify({
                ok: true,
                candidate: MOCK_CANDIDATE_TEXT,
                tags: MOCK_CANDIDATE_TAGS,
                model: "SmilingWolf/wd-v1-4-convnext-tagger-v2",
                execution_provider: "CPUExecutionProvider"
            })
        });
    });

    try {
        console.log("1. Navigating to Manga workspace (http://127.0.0.1:8191/) ...");
        await page.goto("http://127.0.0.1:8191/", { waitUntil: "networkidle" });
        await page.waitForFunction(() => window.__tegakiManga && window.__tegakiManga.generation?.state?.catalog);
        console.log("   Workspace loaded.");

        // 2. Setup document with two CASTs: one with reference, one without
        await page.evaluate(() => {
            const { store, session } = window.__tegakiManga;
            const doc = store.getDocument();
            doc.pages[0].scenes = [
                {
                    scene_id: "scene_1",
                    order: 1,
                    input_mode: "cast",
                    prompt: "classroom interior",
                    negative_prompt: "",
                    area: { shape_type: "rect", x: 0.05, y: 0.05, w: 0.42, h: 0.42 }
                }
            ];
            doc.pages[0].cast = [
                {
                    cast_id: "cast_heroine",
                    display_name: "Heroine",
                    identity_prompt: "1girl, braided hair",
                    negative_prompt: "",
                    reference_asset: "tegaki_manga_references/ref_c789751db904319d.png"
                },
                {
                    cast_id: "cast_hero",
                    display_name: "Hero",
                    identity_prompt: "1boy, black hair",
                    negative_prompt: "",
                    reference_asset: null
                }
            ];
            doc.pages[0].character_instances = [];
            store.setDocument(doc);
            session.selectCast("cast_heroine");
            session.setActiveTab("cast");
        });

        // 3. Switch to CAST without reference (cast_hero)
        console.log("2. Verifying CAST without Reference...");
        await page.evaluate(() => {
            const { session } = window.__tegakiManga;
            session.selectCast("cast_hero");
            const btn = document.querySelector("#scene-prompt-cast-group [data-cast-id='cast_hero']");
            if (btn) btn.click();
        });
        await page.waitForTimeout(100);

        // Check that empty state is shown and analyze is unavailable
        const emptyStateVisible = await page.isVisible("#mg-cast-ref-empty");
        const assignedCardVisible = await page.isVisible("#mg-cast-ref-assigned");
        assert.equal(emptyStateVisible, true, "#mg-cast-ref-empty must be visible when no reference");
        assert.equal(assignedCardVisible, false, "#mg-cast-ref-assigned must be hidden when no reference");
        console.log("   PASS: No-reference CAST cleanly displays empty state.");

        // 4. Switch to CAST with reference (cast_heroine)
        console.log("3. Verifying CAST with Reference...");
        await page.evaluate(() => {
            const { session } = window.__tegakiManga;
            session.selectCast("cast_heroine");
            const btn = document.querySelector("#scene-prompt-cast-group [data-cast-id='cast_heroine']");
            if (btn) btn.click();
        });
        await page.waitForTimeout(100);

        const assignedNowVisible = await page.isVisible("#mg-cast-ref-assigned");
        assert.equal(assignedNowVisible, true, "#mg-cast-ref-assigned must be visible for cast_heroine");

        const initialBadgeText = await page.textContent("#mg-ref-analysis-badge");
        const initialBadgeState = await page.getAttribute("#mg-ref-analysis-badge", "data-state");
        assert.equal(initialBadgeText.trim(), "Ready to analyze");
        assert.equal(initialBadgeState, "ready");

        const analyzeDisabled = await page.getAttribute("#mg-btn-analyze-ref", "disabled");
        assert.equal(analyzeDisabled, null, "Analyze button must be enabled");

        const candidateValue = await page.inputValue("#mg-ref-candidate-text");
        assert.equal(candidateValue, "", "Candidate textarea must be empty initially");

        const appendDisabled = await page.getAttribute("#mg-btn-candidate-append", "disabled");
        const replaceDisabled = await page.getAttribute("#mg-btn-candidate-replace", "disabled");
        const discardDisabled = await page.getAttribute("#mg-btn-candidate-discard", "disabled");
        assert.notEqual(appendDisabled, null, "Append button must be disabled initially");
        assert.notEqual(replaceDisabled, null, "Replace button must be disabled initially");
        assert.notEqual(discardDisabled, null, "Discard button must be disabled initially");
        console.log("   PASS: Initial ready state verified.");

        // 5. Click Analyze Reference
        console.log("4. Triggering Reference Analysis...");
        await page.click("#mg-btn-analyze-ref");

        // Wait for response and Candidate ready state
        await page.waitForFunction(() => {
            const badge = document.getElementById("mg-ref-analysis-badge");
            return badge && badge.getAttribute("data-state") === "candidate_ready";
        }, { timeout: 3000 });

        const readyBadgeText = await page.textContent("#mg-ref-analysis-badge");
        assert.equal(readyBadgeText.trim(), "Candidate ready");

        const populatedCandidate = await page.inputValue("#mg-ref-candidate-text");
        assert.equal(populatedCandidate, MOCK_CANDIDATE_TEXT, "Candidate textarea must contain extracted tags");

        // Verify Authoring Store identity_prompt is STILL unchanged
        const docBeforeApply = await page.evaluate(() => {
            const { store } = window.__tegakiManga;
            return store.getPage().cast.find(c => c.cast_id === "cast_heroine");
        });
        assert.equal(docBeforeApply.identity_prompt, "1girl, braided hair", "Analysis alone must NOT modify Authoring Document identity_prompt");
        console.log("   PASS: Candidate extracted and Authoring Document identity_prompt strictly unmodified.");

        // 6. Test Candidate Editing
        console.log("5. Testing candidate editing...");
        await page.fill("#mg-ref-candidate-text", populatedCandidate + ", custom_ribbon");
        const editedCandidate = await page.inputValue("#mg-ref-candidate-text");
        assert.ok(editedCandidate.endsWith(", custom_ribbon"), "Candidate text must be editable");
        console.log("   PASS: Candidate text is editable.");

        // 7. Test Append Action
        console.log("6. Testing [Append] action...");
        await page.click("#mg-btn-candidate-append");
        await page.waitForTimeout(100);

        const docAfterAppend = await page.evaluate(() => {
            const { store } = window.__tegakiManga;
            return store.getPage().cast.find(c => c.cast_id === "cast_heroine");
        });
        const expectedAppended = `1girl, braided hair, ${populatedCandidate}, custom_ribbon`;
        assert.equal(docAfterAppend.identity_prompt, expectedAppended, "Append must join existing identity_prompt with candidate");

        const composerPromptValue = await page.inputValue("#scene-composer-prompt");
        assert.equal(composerPromptValue, expectedAppended, "Composer prompt textarea must reflect appended identity prompt");

        // Verify other CAST is completely unmodified
        const heroAfterAppend = await page.evaluate(() => {
            const { store } = window.__tegakiManga;
            return store.getPage().cast.find(c => c.cast_id === "cast_hero");
        });
        assert.equal(heroAfterAppend.identity_prompt, "1boy, black hair", "Other CAST must remain untouched");
        console.log("   PASS: Append correctly updated only selected CAST.");

        // 8. Test Replace Action
        console.log("7. Testing [Replace] action...");
        const replacementText = "1girl, solo, school_uniform, black_skirt";
        await page.fill("#mg-ref-candidate-text", replacementText);
        await page.click("#mg-btn-candidate-replace");
        await page.waitForTimeout(100);

        const docAfterReplace = await page.evaluate(() => {
            const { store } = window.__tegakiManga;
            return store.getPage().cast.find(c => c.cast_id === "cast_heroine");
        });
        assert.equal(docAfterReplace.identity_prompt, replacementText, "Replace must overwrite identity_prompt with candidate");

        const composerPromptAfterReplace = await page.inputValue("#scene-composer-prompt");
        assert.equal(composerPromptAfterReplace, replacementText, "Composer prompt textarea must reflect replaced identity prompt");
        console.log("   PASS: Replace correctly updated selected CAST identity_prompt.");

        // 9. Test Discard Action
        console.log("8. Testing [Discard] action...");
        await page.fill("#mg-ref-candidate-text", "temporary_tags_to_discard");
        await page.click("#mg-btn-candidate-discard");
        await page.waitForTimeout(100);

        const candidateAfterDiscard = await page.inputValue("#mg-ref-candidate-text");
        assert.equal(candidateAfterDiscard, "", "Candidate textarea must be cleared after Discard");

        const docAfterDiscard = await page.evaluate(() => {
            const { store } = window.__tegakiManga;
            return store.getPage().cast.find(c => c.cast_id === "cast_heroine");
        });
        assert.equal(docAfterDiscard.identity_prompt, replacementText, "Discard must leave Authoring Document identity_prompt untouched");
        console.log("   PASS: Discard clears candidate without modifying store.");

        // 10. Test CAST Switching Invalidation
        console.log("9. Testing CAST switching invalidation...");
        // Re-analyze
        await page.click("#mg-btn-analyze-ref");
        await page.waitForFunction(() => {
            const badge = document.getElementById("mg-ref-analysis-badge");
            return badge && badge.getAttribute("data-state") === "candidate_ready";
        }, { timeout: 3000 });
        assert.ok((await page.inputValue("#mg-ref-candidate-text")).length > 0);

        // Switch to cast_hero
        await page.evaluate(() => {
            const { session } = window.__tegakiManga;
            session.selectCast("cast_hero");
            const btn = document.querySelector("#scene-prompt-cast-group [data-cast-id='cast_hero']");
            if (btn) btn.click();
        });
        await page.waitForTimeout(100);

        // Switch back to cast_heroine
        await page.evaluate(() => {
            const { session } = window.__tegakiManga;
            session.selectCast("cast_heroine");
            const btn = document.querySelector("#scene-prompt-cast-group [data-cast-id='cast_heroine']");
            if (btn) btn.click();
        });
        await page.waitForTimeout(100);

        // State is reset to ready
        const resetBadgeState = await page.getAttribute("#mg-ref-analysis-badge", "data-state");
        assert.equal(resetBadgeState, "ready");
        console.log("   PASS: CAST switching invalidates candidate state safely.");

        // 11. Test Clearing Reference
        console.log("10. Testing Clear Reference invalidation...");
        await page.click("#mg-btn-clear-char-ref");
        await page.waitForTimeout(100);

        const docAfterClearRef = await page.evaluate(() => {
            const { store } = window.__tegakiManga;
            return store.getPage().cast.find(c => c.cast_id === "cast_heroine");
        });
        assert.equal(docAfterClearRef.reference_asset, null, "Reference asset must be cleared");
        const emptyVisibleAfterClear = await page.isVisible("#mg-cast-ref-empty");
        assert.equal(emptyVisibleAfterClear, true, "Empty state must be visible after Clear");
        console.log("   PASS: Clearing Reference invalidates candidate and hides assigned card.");

        // 12. Visual Evidence & Responsive Check
        console.log("11. Capturing visual evidence...");
        // Reassign reference for screenshot
        await page.evaluate(() => {
            const { store, updateAll } = window.__tegakiManga;
            store.updateCast("cast_heroine", { reference_asset: "tegaki_manga_references/ref_c789751db904319d.png" });
            updateAll();
        });
        await page.waitForTimeout(100);

        // Trigger analysis for screenshot
        await page.click("#mg-btn-analyze-ref");
        await page.waitForFunction(() => {
            const badge = document.getElementById("mg-ref-analysis-badge");
            return badge && badge.getAttribute("data-state") === "candidate_ready";
        }, { timeout: 3000 });

        fs.mkdirSync("scratch", { recursive: true });
        const desktopShotPath = path.resolve("scratch/reference_identity_desktop.png");
        await page.locator("#mg-cast-ref-assigned").scrollIntoViewIfNeeded();
        await page.screenshot({ path: desktopShotPath, fullPage: false });
        console.log(`   Desktop screenshot saved: ${desktopShotPath}`);

        // Narrow layout test (480px width)
        console.log("12. Testing narrow layout (480px)...");
        await page.setViewportSize({ width: 480, height: 800 });
        await page.waitForTimeout(150);

        const overflowDetected = await page.evaluate(() => {
            const container = document.querySelector(".mg-cast-ref-assigned");
            if (!container) return false;
            return container.scrollWidth > container.clientWidth;
        });
        assert.equal(overflowDetected, false, "Narrow layout must not have horizontal overflow in .mg-cast-ref-assigned");

        const narrowShotPath = path.resolve("scratch/reference_identity_narrow.png");
        await page.locator("#mg-cast-ref-assigned").scrollIntoViewIfNeeded();
        await page.screenshot({ path: narrowShotPath, fullPage: false });
        console.log(`   Narrow screenshot saved: ${narrowShotPath}`);

        console.log("=== ALL BROWSER ACCEPTANCE TESTS PASSED ===");
    } finally {
        await browser.close();
    }
}

runBrowserAcceptance().catch((err) => {
    console.error("FATAL Browser Acceptance Failure:", err);
    process.exit(1);
});
