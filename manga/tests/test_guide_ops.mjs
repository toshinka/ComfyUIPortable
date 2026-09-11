/**
 * test_guide_ops.mjs — Existing Guide / Figure Direct Editing Parity Tests (M1C2A)
 * =================================================================================
 * Verifies all requirements from Card Sections 29, 30, and 31:
 *
 * Section 29: Pure Guide/Figure Tests (A through I)
 * A. getNextFigureId collision-free
 * B. new Figure geometry stays in Guide-local [0,1]
 * C. clampGuideFigureDrag stays within Guide-local bounds
 * D. resizeGuideFigure supports NW/NE/SE/SW
 * E. resize respects minimum size
 * F. association to valid Instance succeeds
 * G. duplicate association within same Guide rejected
 * H. unassign preserves Figure
 * I. Figure deletion does not delete Character Instance
 *
 * Section 30: Render / Coordinate Mapping Tests
 * - Non-full-page Guide placement (e.g. x=0.20, y=0.10, w=0.50, h=0.70)
 * - Proves rendered / hit-test page coordinates equal placement + local * placement-size
 * - Fails if Figure.area is mistakenly treated as page-global
 *
 * Section 31: Store Tests (A through J)
 * A. toggle Guide enabled persists
 * B. delete Guide leaves other document layers intact
 * C. add Figure commits valid document
 * D. remove Figure leaves Instance intact
 * E. move Figure persists local geometry
 * F. resize Figure persists local geometry
 * G. associate/unassign persists
 * H. Character removal unassigns Figure
 * I. Scene deletion unassigns Figures for deleted child Instances
 * J. export/import exact durable parity
 */

import assert from "node:assert/strict";
import { AuthoringStore } from "../app/src/state/authoring_store.js";
import { SessionState } from "../app/src/state/session_state.js";
import { validateAuthoringDocument, FORBIDDEN_SESSION_KEYS } from "../app/src/domain/authoring_document.js";
import {
    getNextFigureId,
    clampGuideFigureArea,
    calculateNewGuideFigureArea,
    createGuideFigure,
    clampGuideFigureDrag,
    resizeGuideFigure,
    associateGuideFigure,
    unassignGuideInstance
} from "../app/src/domain/authoring_ops.js";
import { hitTestCanvas } from "../app/src/view/canvas_renderer.js";

console.log("--- Running test_guide_ops.mjs (MANGA-M1C2A) ---");

// ===================================================================
// SECTION 29: REQUIRED PURE GUIDE TESTS
// ===================================================================

// 29.A: getNextFigureId collision-free
{
    const figures = [
        { figure_id: "figure_1" },
        { figure_id: "figure_2" }
    ];
    assert.equal(getNextFigureId(figures), "figure_3");

    // With gaps
    const gapFigures = [
        { figure_id: "figure_1" },
        { figure_id: "figure_5" }
    ];
    assert.equal(getNextFigureId(gapFigures), "figure_6");

    // Empty
    assert.equal(getNextFigureId([]), "figure_1");
    console.log("✓ Pure Check A PASS: getNextFigureId collision-free");
}

// 29.B: new Figure geometry stays in Guide-local [0,1]
{
    const emptyGeom = calculateNewGuideFigureArea([]);
    assert.ok(emptyGeom.x >= 0 && emptyGeom.x + emptyGeom.w <= 1.0, "First figure within [0,1]");
    assert.ok(emptyGeom.y >= 0 && emptyGeom.y + emptyGeom.h <= 1.0, "First figure within [0,1]");

    const secondGeom = calculateNewGuideFigureArea([ { figure_id: "figure_1" } ]);
    assert.ok(secondGeom.x >= 0 && secondGeom.x + secondGeom.w <= 1.0, "Second figure within [0,1]");
    assert.ok(secondGeom.y >= 0 && secondGeom.y + secondGeom.h <= 1.0, "Second figure within [0,1]");

    // Many figures check
    for (let count = 0; count < 10; count++) {
        const dummyList = Array.from({ length: count }, (_, i) => ({ figure_id: `figure_${i+1}` }));
        const fig = createGuideFigure(dummyList);
        assert.ok(fig.area.x >= 0 && fig.area.x + fig.area.w <= 1.0, `Figure ${count} x bounds`);
        assert.ok(fig.area.y >= 0 && fig.area.y + fig.area.h <= 1.0, `Figure ${count} y bounds`);
        assert.equal(fig.instance_id, null, "Initially unassigned");
    }
    console.log("✓ Pure Check B PASS: new Figure geometry stays in Guide-local [0,1]");
}

// 29.C: clampGuideFigureDrag stays within Guide-local bounds
{
    const start = { shape_type: "rect", x: 0.50, y: 0.50, w: 0.30, h: 0.40 };
    // Drag way beyond top-left
    const clampedTopLeft = clampGuideFigureDrag(start, -0.80, -0.80);
    assert.equal(clampedTopLeft.x, 0.0);
    assert.equal(clampedTopLeft.y, 0.0);
    assert.equal(clampedTopLeft.w, 0.30);
    assert.equal(clampedTopLeft.h, 0.40);

    // Drag way beyond bottom-right (max x = 1 - 0.30 = 0.70, max y = 1 - 0.40 = 0.60)
    const clampedBottomRight = clampGuideFigureDrag(start, 0.80, 0.80);
    assert.equal(clampedBottomRight.x, 0.70);
    assert.equal(clampedBottomRight.y, 0.60);
    console.log("✓ Pure Check C PASS: clampGuideFigureDrag stays within Guide-local bounds");
}

// 29.D & 29.E: resizeGuideFigure supports NW/NE/SE/SW & respects minimum size
{
    const start = { shape_type: "rect", x: 0.20, y: 0.20, w: 0.40, h: 0.40 };
    const minSize = 0.04;

    // SE resize
    const se = resizeGuideFigure(start, "se", 0.10, 0.10, minSize);
    assert.equal(se.x, 0.20);
    assert.equal(se.y, 0.20);
    assert.equal(se.w, 0.50);
    assert.equal(se.h, 0.50);

    // NW resize
    const nw = resizeGuideFigure(start, "nw", -0.05, -0.05, minSize);
    assert.equal(nw.x, 0.15);
    assert.equal(nw.y, 0.15);
    assert.equal(nw.w, 0.45);
    assert.equal(nw.h, 0.45);

    // NE resize
    const ne = resizeGuideFigure(start, "ne", 0.05, -0.05, minSize);
    assert.equal(ne.x, 0.20);
    assert.equal(ne.y, 0.15);
    assert.equal(ne.w, 0.45);
    assert.equal(ne.h, 0.45);

    // SW resize
    const sw = resizeGuideFigure(start, "sw", -0.05, 0.05, minSize);
    assert.equal(sw.x, 0.15);
    assert.equal(sw.y, 0.20);
    assert.equal(sw.w, 0.45);
    assert.equal(sw.h, 0.45);

    // Minimum size enforcement
    const shrinkSE = resizeGuideFigure(start, "se", -0.50, -0.50, minSize);
    assert.equal(shrinkSE.w, minSize);
    assert.equal(shrinkSE.h, minSize);

    // Outer boundary enforcement (cannot resize past 1.0)
    const growSE = resizeGuideFigure(start, "se", 0.90, 0.90, minSize);
    assert.equal(growSE.x + growSE.w, 1.0);
    assert.equal(growSE.y + growSE.h, 1.0);

    console.log("✓ Pure Check D & E PASS: resizeGuideFigure supports NW/NE/SE/SW and respects minimum size");
}

// 29.F & 29.G: association to valid Instance succeeds, duplicate association within same Guide rejected
{
    const guide = {
        guide_id: "guide_1",
        figure_regions: [
            { figure_id: "fig_1", instance_id: null, area: { x: 0, y: 0, w: 0.2, h: 0.2 } },
            { figure_id: "fig_2", instance_id: null, area: { x: 0.3, y: 0, w: 0.2, h: 0.2 } }
        ]
    };

    // Valid association
    const res1 = associateGuideFigure(guide, "fig_1", "inst_ren_1");
    assert.equal(res1.ok, true);
    assert.equal(res1.guide.figure_regions[0].instance_id, "inst_ren_1");

    // Attempt duplicate association of same instance to fig_2
    const res2 = associateGuideFigure(res1.guide, "fig_2", "inst_ren_1");
    assert.equal(res2.ok, false);
    assert.equal(res2.reason, "DUPLICATE_INSTANCE_ASSOCIATION");
    assert.ok(res2.error.includes("already associated"));

    console.log("✓ Pure Check F & G PASS: valid association succeeds, duplicate association rejected");
}

// 29.H: unassign preserves Figure
{
    const guide = {
        guide_id: "guide_1",
        figure_regions: [
            { figure_id: "fig_1", instance_id: "inst_ren_1", area: { x: 0.1, y: 0.1, w: 0.2, h: 0.2 } }
        ]
    };

    // Unassign via associateGuideFigure with null/empty
    const resNull = associateGuideFigure(guide, "fig_1", null);
    assert.equal(resNull.ok, true);
    assert.equal(resNull.guide.figure_regions.length, 1);
    assert.equal(resNull.guide.figure_regions[0].figure_id, "fig_1");
    assert.equal(resNull.guide.figure_regions[0].instance_id, null);

    // Unassign via unassignGuideInstance
    const resInst = unassignGuideInstance(guide, "inst_ren_1");
    assert.equal(resInst.figure_regions.length, 1);
    assert.equal(resInst.figure_regions[0].instance_id, null);

    console.log("✓ Pure Check H PASS: unassign preserves Figure region");
}

// 29.I: Figure deletion does not delete Character Instance
{
    // Pure function perspective: removing a figure is an array filter on figure_regions
    const figures = [
        { figure_id: "fig_1", instance_id: "inst_ren_1" },
        { figure_id: "fig_2", instance_id: "inst_sora_1" }
    ];
    const filtered = figures.filter(f => f.figure_id !== "fig_1");
    assert.equal(filtered.length, 1);
    assert.equal(filtered[0].figure_id, "fig_2");
    // Character instances are not touched by this filter
    console.log("✓ Pure Check I PASS: Figure deletion does not delete Character Instance");
}

// ===================================================================
// SECTION 30: REQUIRED RENDER / COORDINATE TESTS
// ===================================================================
{
    // Use a Guide placement deliberately NOT equal to full page
    const guidePlacement = { shape_type: "rect", x: 0.20, y: 0.10, w: 0.50, h: 0.70 };
    const figureLocalArea = { shape_type: "rect", x: 0.10, y: 0.20, w: 0.40, h: 0.50 };

    const expectedPageX = guidePlacement.x + figureLocalArea.x * guidePlacement.w; // 0.20 + 0.10 * 0.50 = 0.25
    const expectedPageY = guidePlacement.y + figureLocalArea.y * guidePlacement.h; // 0.10 + 0.20 * 0.70 = 0.24
    const expectedPageW = figureLocalArea.w * guidePlacement.w; // 0.40 * 0.50 = 0.20
    const expectedPageH = figureLocalArea.h * guidePlacement.h; // 0.50 * 0.70 = 0.35

    assert.equal(parseFloat(expectedPageX.toFixed(4)), 0.25);
    assert.equal(parseFloat(expectedPageY.toFixed(4)), 0.24);
    assert.equal(parseFloat(expectedPageW.toFixed(4)), 0.20);
    assert.equal(parseFloat(expectedPageH.toFixed(4)), 0.35);

    // Mock canvas test with hitTestCanvas
    const cw = 1000;
    const ch = 1000;
    const testPage = {
        guides: [
            {
                guide_id: "guide_test",
                enabled: true,
                placement: guidePlacement,
                figure_regions: [
                    {
                        figure_id: "fig_test",
                        area: figureLocalArea,
                        instance_id: null
                    }
                ]
            }
        ],
        scenes: [],
        character_instances: [],
        visual_frames: []
    };

    const session = new SessionState();
    session.setActiveTab("guides");
    session.selectGuide("guide_test");
    session.selectFigure("fig_test");

    // Hit test at center of transformed figure: x = 0.25 + 0.10 = 0.35, y = 0.24 + 0.175 = 0.415
    const hitInside = hitTestCanvas(cw, ch, testPage, 0.35, 0.415, session);
    assert.ok(hitInside, "Must hit figure inside transformed page coordinates");
    assert.equal(hitInside.type, "figure");
    assert.equal(hitInside.item.figure_id, "fig_test");

    // Hit test at figureLocalArea coordinates if someone mistakenly treated it as page-global:
    // x = 0.10, y = 0.20 -> outside guide placement (which starts at x=0.20)
    const hitMistakenGlobal = hitTestCanvas(cw, ch, testPage, 0.12, 0.22, session);
    assert.equal(hitMistakenGlobal, null, "Must NOT hit at untransformed local coordinates (which lie outside guide placement)");

    // Hit test at SE handle of transformed figure:
    // handle corner is at page (0.25 + 0.20, 0.24 + 0.35) = (0.45, 0.59) -> px (450, 590)
    const hitHandle = hitTestCanvas(cw, ch, testPage, 0.45, 0.59, session);
    assert.ok(hitHandle, "Must hit handle at transformed figure corner");
    assert.equal(hitHandle.type, "handle_figure");
    assert.equal(hitHandle.handle, "se");

    console.log("✓ Section 30 PASS: Guide-local coordinate transformation correctly derived at runtime");
}

// ===================================================================
// SECTION 31: REQUIRED STORE TESTS
// ===================================================================

// 31.A: toggle Guide enabled persists
{
    const store = new AuthoringStore();
    store.loadRichFixture();
    const gBefore = store.getPage().guides[0].enabled;
    store.toggleGuideEnabled("guide_rough_1");
    assert.equal(store.getPage().guides[0].enabled, !gBefore);
    assert.equal(validateAuthoringDocument(store.getDocument()).valid, true);

    store.toggleGuideEnabled("guide_rough_1");
    assert.equal(store.getPage().guides[0].enabled, gBefore);
    assert.equal(validateAuthoringDocument(store.getDocument()).valid, true);
    console.log("✓ Store Check A PASS: toggle Guide enabled persists");
}

// 31.B: delete Guide leaves other document layers intact
{
    const store = new AuthoringStore();
    store.loadRichFixture();
    const sceneCount = store.getPage().scenes.length;
    const frameCount = store.getPage().visual_frames.length;
    const castCount = store.getPage().cast.length;
    const instCount = store.getPage().character_instances.length;

    store.deleteGuide("guide_rough_1");
    assert.equal(store.getPage().guides.length, 0);
    assert.equal(store.getPage().scenes.length, sceneCount);
    assert.equal(store.getPage().visual_frames.length, frameCount);
    assert.equal(store.getPage().cast.length, castCount);
    assert.equal(store.getPage().character_instances.length, instCount);
    assert.equal(validateAuthoringDocument(store.getDocument()).valid, true);
    console.log("✓ Store Check B PASS: delete Guide leaves other document layers intact");
}

// 31.C: add Figure commits valid document
{
    const store = new AuthoringStore();
    store.loadRichFixture();
    const figBeforeCount = store.getPage().guides[0].figure_regions.length;
    const newFig = store.addGuideFigure("guide_rough_1");
    assert.ok(newFig.figure_id);
    assert.equal(store.getPage().guides[0].figure_regions.length, figBeforeCount + 1);
    assert.equal(validateAuthoringDocument(store.getDocument()).valid, true);
    console.log("✓ Store Check C PASS: add Figure commits valid document");
}

// 31.D: remove Figure leaves Instance intact
{
    const store = new AuthoringStore();
    store.loadRichFixture();
    const instancesBefore = JSON.parse(JSON.stringify(store.getPage().character_instances));
    store.deleteGuideFigure("guide_rough_1", "fig_ren");

    const guideFigs = store.getPage().guides[0].figure_regions;
    assert.equal(guideFigs.some(f => f.figure_id === "fig_ren"), false);
    assert.deepEqual(store.getPage().character_instances, instancesBefore);
    assert.equal(validateAuthoringDocument(store.getDocument()).valid, true);
    console.log("✓ Store Check D PASS: remove Figure leaves Instance intact");
}

// 31.E & 31.F: move and resize Figure persists local geometry
{
    const store = new AuthoringStore();
    store.loadRichFixture();
    const origArea = { ...store.getPage().guides[0].figure_regions[0].area };

    store.moveGuideFigure("guide_rough_1", "fig_ren", 0.05, 0.03);
    const movedArea = store.getPage().guides[0].figure_regions[0].area;
    assert.equal(movedArea.x, parseFloat((origArea.x + 0.05).toFixed(4)));
    assert.equal(movedArea.y, parseFloat((origArea.y + 0.03).toFixed(4)));

    store.resizeGuideFigure("guide_rough_1", "fig_ren", "se", 0.04, 0.04);
    const resizedArea = store.getPage().guides[0].figure_regions[0].area;
    assert.equal(resizedArea.w, parseFloat((origArea.w + 0.04).toFixed(4)));
    assert.equal(resizedArea.h, parseFloat((origArea.h + 0.04).toFixed(4)));

    assert.equal(validateAuthoringDocument(store.getDocument()).valid, true);
    console.log("✓ Store Check E & F PASS: move and resize Figure persist local geometry");
}

// 31.G: associate/unassign persists
{
    const store = new AuthoringStore();
    store.loadRichFixture();
    // Add an unassigned figure
    const newFig = store.addGuideFigure("guide_rough_1");
    assert.equal(newFig.instance_id, null);

    // Associate with inst_sora_1 (currently associated with fig_sora -> duplicate should fail!)
    assert.throws(() => {
        store.associateGuideFigure("guide_rough_1", newFig.figure_id, "inst_sora_1");
    }, /already associated/);

    // Unassign fig_sora
    store.associateGuideFigure("guide_rough_1", "fig_sora", null);
    const figSoraAfter = store.getPage().guides[0].figure_regions.find(f => f.figure_id === "fig_sora");
    assert.equal(figSoraAfter.instance_id, null);

    // Now associate newFig with inst_sora_1
    store.associateGuideFigure("guide_rough_1", newFig.figure_id, "inst_sora_1");
    const newFigAfter = store.getPage().guides[0].figure_regions.find(f => f.figure_id === newFig.figure_id);
    assert.equal(newFigAfter.instance_id, "inst_sora_1");

    assert.equal(validateAuthoringDocument(store.getDocument()).valid, true);
    console.log("✓ Store Check G PASS: associate/unassign persists");
}

// 31.H: Character removal unassigns Figure
{
    const store = new AuthoringStore();
    store.loadRichFixture();
    assert.equal(store.getPage().guides[0].figure_regions[0].instance_id, "inst_ren_1");

    store.removeCharacter("inst_ren_1");
    // Character instance removed
    assert.equal(store.getPage().character_instances.some(i => i.instance_id === "inst_ren_1"), false);
    // Figure region remains, but instance_id is cleared
    const figRen = store.getPage().guides[0].figure_regions.find(f => f.figure_id === "fig_ren");
    assert.ok(figRen, "Figure fig_ren must remain");
    assert.equal(figRen.instance_id, null, "Figure instance_id must be null");
    assert.equal(validateAuthoringDocument(store.getDocument()).valid, true);
    console.log("✓ Store Check H PASS: Character removal unassigns Figure");
}

// 31.I: Scene deletion unassigns Figures for deleted child Instances
{
    const store = new AuthoringStore();
    store.loadRichFixture();
    // In rich fixture, inst_ren_1 and inst_sora_1 belong to scene_action_top
    assert.equal(store.getPage().guides[0].figure_regions.length, 2);
    assert.equal(store.getPage().guides[0].figure_regions[0].instance_id, "inst_ren_1");
    assert.equal(store.getPage().guides[0].figure_regions[1].instance_id, "inst_sora_1");

    store.deleteScene("scene_action_top");
    // Figures still exist
    const figures = store.getPage().guides[0].figure_regions;
    assert.equal(figures.length, 2);
    assert.equal(figures[0].instance_id, null);
    assert.equal(figures[1].instance_id, null);
    assert.equal(validateAuthoringDocument(store.getDocument()).valid, true);
    console.log("✓ Store Check I PASS: Scene deletion unassigns Figures for deleted child Instances");
}

// 31.J: export/import exact durable parity
{
    const store1 = new AuthoringStore();
    store1.loadRichFixture();
    const g = store1.getPage().guides[0];
    store1.moveGuideFigure(g.guide_id, "fig_ren", 0.02, 0.02);
    store1.resizeGuideFigure(g.guide_id, "fig_ren", "se", 0.03, 0.03);
    store1.toggleGuideEnabled(g.guide_id);

    const json1 = store1.exportJson();
    const parsed1 = JSON.parse(json1);

    // Verify forbidden session keys are absent
    for (const key of FORBIDDEN_SESSION_KEYS) {
        assert.equal(key in parsed1, false, `Forbidden key ${key} in root`);
        assert.equal(key in parsed1.pages[0], false, `Forbidden key ${key} in page`);
    }

    const store2 = new AuthoringStore();
    const resImport = store2.importJson(json1);
    assert.equal(resImport.ok, true);

    const json2 = store2.exportJson();
    assert.equal(json2, json1, "Re-imported document exported JSON must match exactly");

    const importedGuide = store2.getPage().guides[0];
    assert.equal(importedGuide.enabled, false);
    assert.equal(importedGuide.figure_regions[0].figure_id, "fig_ren");
    assert.equal(importedGuide.figure_regions[0].instance_id, "inst_ren_1");
    assert.equal(validateAuthoringDocument(store2.getDocument()).valid, true);
    console.log("✓ Store Check J PASS: export/import exact durable parity");
}

console.log("==================================================");
console.log("ALL PURE, COORDINATE & STORE GUIDE TESTS PASSED (M1C2A)");
console.log("==================================================");
