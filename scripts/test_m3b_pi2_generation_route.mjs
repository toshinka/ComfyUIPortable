/**
 * scripts/test_m3b_pi2_generation_route.mjs — M3B-PI2 Frontend Route Preview & Parity Tests
 * =========================================================================================
 * Tests:
 * 1. Parity between frontend route preview and backend routing rules (Section 31)
 * 2. One-action disable / re-enable transitions (Section 9, 42)
 * 3. Zero-figure behavior (Section 6, 42)
 * 4. Unassigned figure behavior (Section 7, 42)
 * 5. Display label and badge state (Section 12, 42)
 */

import assert from "node:assert";
import {
    previewGenerationRoute,
    ROUTE_STANDARD,
    ROUTE_GUIDED,
    ROUTE_LABELS
} from "../custom_nodes_custom/tegaki_manga_nodes/web/js/minimum_hand_generation_route.js";

function createDoc({ hasGuide = false, guideEnabled = true, figureCount = 1, instanceId = "inst_1" } = {}) {
    const guides = [];
    if (hasGuide) {
        const figs = [];
        for (let i = 0; i < figureCount; i++) {
            figs.push({
                figure_id: `fig_${i + 1}`,
                instance_id: instanceId,
                area: { shape_type: "rect", x: 0.1 * (i + 1), y: 0.2, w: 0.3, h: 0.5 }
            });
        }
        guides.push({
            guide_id: "guide_1",
            guide_type: "rough_manga",
            asset_reference: "tegaki_manga_guides/rough_guide_live.png",
            enabled: guideEnabled,
            placement: { x: 0.0, y: 0.2, w: 1.0, h: 0.6 },
            figure_regions: figs
        });
    }

    return {
        schema_id: "TEGAKI_AUTHORING_DOCUMENT",
        schema_version: "1.0.0",
        document_id: "test_doc_js",
        pages: [
            {
                page_id: "page_1",
                order: 1,
                width_px: 832,
                height_px: 1216,
                scenes: [
                    {
                        scene_id: "scene_1",
                        area: { shape_type: "rect", x: 0.08, y: 0.06, w: 0.84, h: 0.88 }
                    }
                ],
                visual_frames: [],
                cast: [],
                character_instances: [],
                guides,
                generation: { seed: 42 }
            }
        ]
    };
}

let testCount = 0;
let passCount = 0;

function it(name, fn) {
    testCount++;
    try {
        fn();
        passCount++;
        console.log(`  PASS: ${name}`);
    } catch (err) {
        console.error(`  FAIL: ${name}`);
        console.error(err);
        process.exitCode = 1;
    }
}

console.log("=================================================================");
console.log("M3B-PI2 FRONTEND GENERATION ROUTE TEST SUITE");
console.log("=================================================================");

it("Case 1: No guides -> STANDARD_NO_GUIDE", () => {
    const doc = createDoc({ hasGuide: false });
    const r = previewGenerationRoute(doc, 0);
    assert.strictEqual(r.route, ROUTE_STANDARD);
    assert.strictEqual(r.displayLabel, "Generation: Standard");
    assert.strictEqual(r.eligibleGuideCount, 0);
    assert.strictEqual(r.figureCount, 0);
});

it("Case 2: Disabled guide -> STANDARD_NO_GUIDE", () => {
    const doc = createDoc({ hasGuide: true, guideEnabled: false, figureCount: 2 });
    const r = previewGenerationRoute(doc, 0);
    assert.strictEqual(r.route, ROUTE_STANDARD);
    assert.strictEqual(r.displayLabel, "Generation: Standard");
    assert.strictEqual(r.eligibleGuideCount, 0);
    assert.strictEqual(r.figureCount, 0);
    assert.match(r.reason, /disabled/i);
});

it("Case 3: Enabled guide with zero figures -> STANDARD_NO_GUIDE", () => {
    const doc = createDoc({ hasGuide: true, guideEnabled: true, figureCount: 0 });
    const r = previewGenerationRoute(doc, 0);
    assert.strictEqual(r.route, ROUTE_STANDARD);
    assert.strictEqual(r.displayLabel, "Generation: Standard");
    assert.strictEqual(r.eligibleGuideCount, 0);
    assert.strictEqual(r.figureCount, 0);
    assert.match(r.reason, /zero figure/i);
});

it("Case 4: Enabled guide with unassigned figure -> GUIDED_CLEAN_GLOBAL", () => {
    const doc = createDoc({ hasGuide: true, guideEnabled: true, figureCount: 1, instanceId: null });
    const r = previewGenerationRoute(doc, 0);
    assert.strictEqual(r.route, ROUTE_GUIDED);
    assert.strictEqual(r.displayLabel, "Generation: Guide-assisted");
    assert.strictEqual(r.eligibleGuideCount, 1);
    assert.strictEqual(r.figureCount, 1);
});

it("Case 5: Enabled guide with multiple figures -> GUIDED_CLEAN_GLOBAL", () => {
    const doc = createDoc({ hasGuide: true, guideEnabled: true, figureCount: 3 });
    const r = previewGenerationRoute(doc, 0);
    assert.strictEqual(r.route, ROUTE_GUIDED);
    assert.strictEqual(r.displayLabel, "Generation: Guide-assisted");
    assert.strictEqual(r.eligibleGuideCount, 1);
    assert.strictEqual(r.figureCount, 3);
});

it("Case 6: Multiple guides, one eligible -> GUIDED_CLEAN_GLOBAL", () => {
    const doc = createDoc({ hasGuide: true, guideEnabled: false, figureCount: 2 });
    doc.pages[0].guides.push({
        guide_id: "guide_2",
        guide_type: "rough_manga",
        enabled: true,
        figure_regions: [
            { figure_id: "fig_g2", area: { shape_type: "rect", x: 0.1, y: 0.1, w: 0.5, h: 0.5 } }
        ]
    });
    const r = previewGenerationRoute(doc, 0);
    assert.strictEqual(r.route, ROUTE_GUIDED);
    assert.strictEqual(r.eligibleGuideCount, 1);
    assert.strictEqual(r.figureCount, 1);
});

it("Case 7: One-action disable transition (GUIDED -> STANDARD)", () => {
    const doc = createDoc({ hasGuide: true, guideEnabled: true, figureCount: 1 });
    let r = previewGenerationRoute(doc, 0);
    assert.strictEqual(r.route, ROUTE_GUIDED);

    // Simulate Disable Guide button toggle
    doc.pages[0].guides[0].enabled = false;
    r = previewGenerationRoute(doc, 0);
    assert.strictEqual(r.route, ROUTE_STANDARD);
    assert.strictEqual(r.displayLabel, "Generation: Standard");
});

it("Case 8: Re-enable transition (STANDARD -> GUIDED)", () => {
    const doc = createDoc({ hasGuide: true, guideEnabled: false, figureCount: 1 });
    let r = previewGenerationRoute(doc, 0);
    assert.strictEqual(r.route, ROUTE_STANDARD);

    // Simulate Enable Guide button toggle
    doc.pages[0].guides[0].enabled = true;
    r = previewGenerationRoute(doc, 0);
    assert.strictEqual(r.route, ROUTE_GUIDED);
    assert.strictEqual(r.displayLabel, "Generation: Guide-assisted");
});

it("Case 9: Guide removed transition (GUIDED -> STANDARD)", () => {
    const doc = createDoc({ hasGuide: true, guideEnabled: true, figureCount: 1 });
    let r = previewGenerationRoute(doc, 0);
    assert.strictEqual(r.route, ROUTE_GUIDED);

    // Remove guide
    doc.pages[0].guides.splice(0, 1);
    r = previewGenerationRoute(doc, 0);
    assert.strictEqual(r.route, ROUTE_STANDARD);
    assert.strictEqual(r.displayLabel, "Generation: Standard");
});

it("Case 10: Invalid document / out of bounds handling", () => {
    assert.strictEqual(previewGenerationRoute(null).route, ROUTE_STANDARD);
    assert.strictEqual(previewGenerationRoute({ pages: [] }).route, ROUTE_STANDARD);
    const doc = createDoc({ hasGuide: true });
    assert.strictEqual(previewGenerationRoute(doc, 5).route, ROUTE_STANDARD);
    assert.strictEqual(previewGenerationRoute(doc, -1).route, ROUTE_STANDARD);
});

console.log(`\nResults: ${passCount} / ${testCount} tests passed.`);
if (passCount !== testCount) {
    process.exit(1);
}
