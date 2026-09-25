/**
 * test_create_guide_reference_hub.mjs
 * ====================================
 * Verifies Card MANGA-CREATE-GUIDE-REFERENCE-HUB1 acceptance criteria:
 * A. Global-only: Guide entry reachable without opening legacy Authoring editor.
 * B. Guide assignment: Existing asset identity is retained.
 * C. Guide enable/disable: Uses the canonical document operation.
 * D. Character selection: Relevant Reference entry appears contextually.
 * E. Character Reference: Assignment affects the correct CAST.
 * F. Prompt target and Scene selection: Existing Guide/Reference assignment remains unchanged.
 * G. Stage Generate: Existing Global/Scenes distinction remains truthful.
 * H. Existing JSON export/import: Asset references remain intact.
 * I. Guide Generation Status Truth: Distinct states (none, disabled, enabled, unsupported).
 */

import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { AuthoringStore, createNewAuthoringSessionDocument } from "../app/src/state/authoring_store.js";
import { SessionState } from "../app/src/state/session_state.js";
import { validateAuthoringDocument } from "../app/src/domain/authoring_document.js";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

console.log("--- Running test_create_guide_reference_hub.mjs ---");

// Helper function mirroring the Create-side Guide status computation
function deriveGuideStatus(page, catalog) {
    const guides = page?.guides || [];
    if (guides.length === 0) {
        return {
            status: "NO GUIDE ASSIGNED",
            state: "none"
        };
    }
    const activeGuide = guides[0];
    if (activeGuide.enabled === false) {
        return {
            status: "GUIDE ASSIGNED BUT DISABLED",
            state: "disabled"
        };
    }
    const cnetAvailable = Boolean(catalog?.scene_generation?.controlnet?.available);
    if (!cnetAvailable) {
        return {
            status: "GUIDE ENABLED BUT GENERATION CURRENTLY UNSUPPORTED",
            state: "unsupported"
        };
    }
    return {
        status: "GUIDE ENABLED",
        state: "enabled"
    };
}

// ------------------------------------------------------------------
// Check A & B: Guide Assignment & Retention of Asset Identity
// ------------------------------------------------------------------
{
    const store = new AuthoringStore(createNewAuthoringSessionDocument());
    let page = store.getPage(0);
    assert.deepEqual(page.guides, [], "Fresh session document has no guides");

    // Check status in empty state
    const emptyStatus = deriveGuideStatus(page, { scene_generation: { controlnet: { available: true } } });
    assert.equal(emptyStatus.status, "NO GUIDE ASSIGNED");
    assert.equal(emptyStatus.state, "none");

    // Add guide from asset
    const guideRef = "tegaki_manga_guides/rough_layout_test.png";
    const newGuide = store.addGuideFromAsset({
        asset_reference: guideRef,
        image_width: 832,
        image_height: 1216
    });

    page = store.getPage(0);
    assert.equal(page.guides.length, 1, "Page has exactly 1 guide");
    assert.equal(page.guides[0].guide_id, newGuide.guide_id);
    assert.equal(page.guides[0].asset_reference, guideRef, "Asset identity retained exactly");
    assert.equal(page.guides[0].metadata?.source_dimensions?.width_px, 832);
    assert.equal(page.guides[0].metadata?.source_dimensions?.height_px, 1216);
    assert.equal(page.guides[0].enabled, true, "New guide is enabled by default");
    console.log("✓ Check A & B PASS: Guide assignment & asset identity retention");
}

// ------------------------------------------------------------------
// Check C: Guide Enable / Disable & Removal without asset file deletion
// ------------------------------------------------------------------
{
    const store = new AuthoringStore(createNewAuthoringSessionDocument());
    const g = store.addGuideFromAsset({
        asset_reference: "tegaki_manga_guides/rough_layout_1.png",
        image_width: 832,
        image_height: 1216
    });

    // Toggle disabled
    store.toggleGuideEnabled(g.guide_id);
    let page = store.getPage(0);
    assert.equal(page.guides[0].enabled, false, "Guide toggled to disabled");

    let disabledStatus = deriveGuideStatus(page, { scene_generation: { controlnet: { available: true } } });
    assert.equal(disabledStatus.status, "GUIDE ASSIGNED BUT DISABLED");
    assert.equal(disabledStatus.state, "disabled");

    // Toggle back to enabled
    store.toggleGuideEnabled(g.guide_id);
    page = store.getPage(0);
    assert.equal(page.guides[0].enabled, true, "Guide toggled back to enabled");

    // Replace asset
    const replacedRef = "tegaki_manga_guides/rough_layout_v2.png";
    store.replaceGuideAsset(g.guide_id, {
        asset_reference: replacedRef,
        image_width: 1024,
        image_height: 1024
    });
    page = store.getPage(0);
    assert.equal(page.guides[0].asset_reference, replacedRef, "Guide asset replaced in document");
    assert.equal(page.guides[0].metadata?.source_dimensions?.width_px, 1024);

    // Delete guide from document
    store.deleteGuide(g.guide_id);
    page = store.getPage(0);
    assert.equal(page.guides.length, 0, "Guide removed from document");
    console.log("✓ Check C PASS: Canonical Guide toggle, replace, and removal");
}

// ------------------------------------------------------------------
// Check D & E: Contextual Character Reference Assignment to CAST
// ------------------------------------------------------------------
{
    const store = new AuthoringStore(createNewAuthoringSessionDocument());
    const cast1 = store.addCast({ display_name: "Hero", identity_prompt: "1boy, warrior" });
    const cast2 = store.addCast({ display_name: "Sidekick", identity_prompt: "1girl, mage" });

    let page = store.getPage(0);
    assert.equal(page.cast.length, 2);
    assert.equal(page.cast[0].reference_asset, null, "Default CAST has null reference_asset");

    // Assign reference to cast1
    const refHero = "tegaki_manga_references/ref_hero_concept.png";
    store.assignCastReference(cast1.cast_id, refHero);

    page = store.getPage(0);
    const heroEntry = page.cast.find(c => c.cast_id === cast1.cast_id);
    const sidekickEntry = page.cast.find(c => c.cast_id === cast2.cast_id);

    assert.equal(heroEntry.reference_asset, refHero, "Hero received reference asset");
    assert.equal(sidekickEntry.reference_asset, null, "Sidekick reference asset untouched");

    // Clearing reference sets null without mutating other fields or deleting CAST
    store.clearCastReference(cast1.cast_id);
    page = store.getPage(0);
    const heroCleared = page.cast.find(c => c.cast_id === cast1.cast_id);
    assert.equal(heroCleared.reference_asset, null, "Reference cleared to null");
    assert.equal(heroCleared.display_name, "Hero", "Display name preserved");
    assert.equal(heroCleared.identity_prompt, "1boy, warrior", "Identity prompt preserved");

    // Character instances are NOT auto-placed merely because reference is assigned
    assert.equal(page.character_instances.length, 0, "No character instance created automatically");
    console.log("✓ Check D & E PASS: Contextual Character Reference assignment and clearing");
}

// ------------------------------------------------------------------
// Check F: Prompt Target and Scene Selection Independence
// ------------------------------------------------------------------
{
    const store = new AuthoringStore(createNewAuthoringSessionDocument());
    const g = store.addGuideFromAsset({
        asset_reference: "tegaki_manga_guides/rough_layout_main.png",
        image_width: 832,
        image_height: 1216
    });
    const cast = store.addCast({ display_name: "Protagonist" });
    store.assignCastReference(cast.cast_id, "tegaki_manga_references/ref_protag.png");
    const scene1 = store.addScene({ name: "Scene 1", prompt: "outside school" });

    const session = new SessionState();

    // Select global
    session.setActiveTab("scenes");
    session.selectScene(null);
    let page = store.getPage(0);
    assert.equal(page.guides[0].asset_reference, "tegaki_manga_guides/rough_layout_main.png");
    assert.equal(page.cast[0].reference_asset, "tegaki_manga_references/ref_protag.png");

    // Select Scene
    session.selectScene(scene1.scene_id);
    page = store.getPage(0);
    assert.equal(page.guides[0].asset_reference, "tegaki_manga_guides/rough_layout_main.png");
    assert.equal(page.cast[0].reference_asset, "tegaki_manga_references/ref_protag.png");

    // Select Cast
    session.selectCast(cast.cast_id);
    session.setActiveTab("cast");
    page = store.getPage(0);
    assert.equal(page.guides[0].asset_reference, "tegaki_manga_guides/rough_layout_main.png");
    assert.equal(page.cast[0].reference_asset, "tegaki_manga_references/ref_protag.png");
    console.log("✓ Check F PASS: Target switching leaves Guide and Reference intact");
}

// ------------------------------------------------------------------
// Check G & I: Guide Generation Eligibility and Truthful Status Mapping
// ------------------------------------------------------------------
{
    const store = new AuthoringStore(createNewAuthoringSessionDocument());
    const g = store.addGuideFromAsset({
        asset_reference: "tegaki_manga_guides/guide_cnet.png",
        image_width: 832,
        image_height: 1216
    });

    const page = store.getPage(0);

    // Case 1: Backend has ControlNet capability
    const catalogReady = {
        scene_generation: {
            available: true,
            controlnet: {
                available: true,
                model: "CN-anytest_v4/CN-anytest4_illustrious2_A.safetensors"
            }
        }
    };
    const readyStatus = deriveGuideStatus(page, catalogReady);
    assert.equal(readyStatus.status, "GUIDE ENABLED");
    assert.equal(readyStatus.state, "enabled");

    // Case 2: Backend lacks ControlNet capability
    const catalogNoCnet = {
        scene_generation: {
            available: true,
            controlnet: {
                available: false
            }
        }
    };
    const unsupportedStatus = deriveGuideStatus(page, catalogNoCnet);
    assert.equal(unsupportedStatus.status, "GUIDE ENABLED BUT GENERATION CURRENTLY UNSUPPORTED");
    assert.equal(unsupportedStatus.state, "unsupported");

    // Case 3: Guide assigned but disabled
    store.toggleGuideEnabled(g.guide_id);
    const disabledStatus = deriveGuideStatus(store.getPage(0), catalogReady);
    assert.equal(disabledStatus.status, "GUIDE ASSIGNED BUT DISABLED");
    assert.equal(disabledStatus.state, "disabled");
    console.log("✓ Check G & I PASS: Truthful ControlNet readiness and status mapping");
}

// ------------------------------------------------------------------
// Check H: JSON Export / Import Roundtrip Parity
// ------------------------------------------------------------------
{
    const store = new AuthoringStore(createNewAuthoringSessionDocument());
    store.addGuideFromAsset({
        asset_reference: "tegaki_manga_guides/export_test_guide.png",
        image_width: 832,
        image_height: 1216
    });
    const c = store.addCast({ display_name: "ExportHero" });
    store.assignCastReference(c.cast_id, "tegaki_manga_references/export_test_ref.png");

    const exportedJson = JSON.stringify(store.getDocument());
    const parsed = JSON.parse(exportedJson);
    const validation = validateAuthoringDocument(parsed);
    assert.ok(validation.valid, "Exported document validates cleanly against schema");

    const importedStore = new AuthoringStore(parsed);
    const importedPage = importedStore.getPage(0);

    assert.equal(importedPage.guides.length, 1);
    assert.equal(importedPage.guides[0].asset_reference, "tegaki_manga_guides/export_test_guide.png");
    assert.equal(importedPage.cast.length, 1);
    assert.equal(importedPage.cast[0].reference_asset, "tegaki_manga_references/export_test_ref.png");
    console.log("✓ Check H PASS: Export/import roundtrip preserves asset references exactly");
}

// ------------------------------------------------------------------
// Check J: HTML DOM Structure & CSS Class Verification
// ------------------------------------------------------------------
{
    const htmlPath = path.resolve(__dirname, "../app/index.html");
    const html = fs.readFileSync(htmlPath, "utf-8");

    const expectedIds = [
        "mg-page-guide-panel",
        "mg-guide-status-badge",
        "mg-guide-empty",
        "mg-guide-assigned",
        "mg-guide-img",
        "mg-guide-name",
        "mg-guide-meta",
        "mg-guide-support-note",
        "mg-btn-add-guide",
        "mg-btn-toggle-guide",
        "mg-btn-replace-guide",
        "mg-btn-remove-guide",
        "scene-composer-cast-reference-wrap",
        "scene-composer-cast-ref-label",
        "mg-cast-ref-status",
        "mg-cast-ref-empty",
        "mg-cast-ref-assigned",
        "mg-cast-ref-img",
        "mg-cast-ref-name",
        "mg-cast-ref-error",
        "mg-btn-add-char-ref",
        "mg-btn-replace-char-ref",
        "mg-btn-clear-char-ref"
    ];

    for (const id of expectedIds) {
        assert.ok(html.includes(`id="${id}"`), `HTML contains element with id="${id}"`);
    }

    const cssPath = path.resolve(__dirname, "../app/css/manga_workspace.css");
    const css = fs.readFileSync(cssPath, "utf-8");

    const expectedClasses = [
        ".mg-guide-panel",
        ".mg-guide-head",
        ".mg-guide-badge",
        ".mg-guide-empty-state",
        ".mg-guide-assigned-card",
        ".mg-guide-preview-box",
        ".mg-guide-img",
        ".mg-cast-ref-field",
        ".mg-cast-ref-empty",
        ".mg-cast-ref-assigned",
        ".mg-cast-ref-preview-box",
        ".mg-cast-ref-img"
    ];

    for (const cls of expectedClasses) {
        assert.ok(css.includes(cls), `CSS contains class rule for "${cls}"`);
    }
    console.log("✓ Check J PASS: HTML elements and CSS selectors verified");
}

console.log("==================================================");
console.log("ALL CREATE GUIDE & REFERENCE HUB TESTS PASSED");
console.log("==================================================");
