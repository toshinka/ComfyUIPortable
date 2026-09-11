/**
 * test_frame_ops.mjs — Visual Frame Pure and Store Operations Tests (M1C1)
 * =========================================================================
 * Verifies all requirements from Card Section 18 and 19:
 *
 * Section 18: Pure Tests (A through K)
 * A. getNextFrameId avoids collisions
 * B. calculateNewFrameGeometry matches reference behavior
 * C. copyScenesToFrames creates independent clones
 * D. moving Scene after copy does not move Frame
 * E. moving Frame after copy does not move Scene
 * F. clampFrameDrag cannot leave page bounds
 * G. resizeFrame supports NW/NE/SE/SW
 * H. resize remains within page bounds
 * I. minimum frame size enforced
 * J. overlap detection identifies intersecting pair
 * K. touching borders are not incorrectly treated as overlap
 *
 * Section 19: Store Tests (A through H)
 * A. addFrame commits valid schema
 * B. deleteFrame reorders survivors
 * C. copyScenesToFrames replaces previous frames intentionally
 * D. moveFrame persists geometry
 * E. resizeFrame persists geometry
 * F. border thickness persists
 * G. export/import preserves all frame document data
 * H. session state never leaks into document
 */

import assert from "node:assert/strict";
import { AuthoringStore } from "../app/src/state/authoring_store.js";
import { validateAuthoringDocument, FORBIDDEN_SESSION_KEYS } from "../app/src/domain/authoring_document.js";
import {
    getNextFrameId,
    calculateNewFrameGeometry,
    copyFramesFromScenes,
    clampFrameDrag,
    resizeFrame,
    checkFrameOverlap
} from "../app/src/domain/authoring_ops.js";

console.log("--- Running test_frame_ops.mjs (MANGA-M1C1) ---");

// ===================================================================
// SECTION 18: PURE TESTS
// ===================================================================

// 18.A: getNextFrameId avoids collisions
{
    const frames = [
        { frame_id: "frame_1" },
        { frame_id: "frame_2" }
    ];
    assert.equal(getNextFrameId(frames), "frame_3");

    // Gaps in numbering
    const gapFrames = [
        { frame_id: "frame_1" },
        { frame_id: "frame_5" }
    ];
    assert.equal(getNextFrameId(gapFrames), "frame_6");

    // Empty list
    assert.equal(getNextFrameId([]), "frame_1");
    console.log("✓ Pure Check A PASS: getNextFrameId avoids collisions");
}

// 18.B: calculateNewFrameGeometry matches reference behavior
{
    const geom0 = calculateNewFrameGeometry([]);
    assert.deepEqual(geom0, { shape_type: "rect", x: 0.05, y: 0.05, w: 0.90, h: 0.42 });

    const geom1 = calculateNewFrameGeometry([{}]);
    assert.deepEqual(geom1, { shape_type: "rect", x: 0.05, y: 0.52, w: 0.90, h: 0.42 });

    const geom2 = calculateNewFrameGeometry([{}, {}]);
    assert.equal(geom2.shape_type, "rect");
    assert.equal(geom2.x, 0.05);
    assert.equal(geom2.w, 0.90);
    assert.equal(geom2.h, 0.22);
    console.log("✓ Pure Check B PASS: calculateNewFrameGeometry matches reference behavior");
}

// 18.C: copyScenesToFrames creates independent clones
{
    const scenes = [
        { area: { x: 0.1, y: 0.1, w: 0.8, h: 0.3 } },
        { area: { x: 0.1, y: 0.5, w: 0.8, h: 0.3 } }
    ];
    const frames = copyFramesFromScenes(scenes);
    assert.equal(frames.length, 2);
    assert.equal(frames[0].frame_id, "frame_1");
    assert.equal(frames[0].order, 1);
    assert.equal(frames[0].border_thickness, 4);
    assert.equal(frames[0].border_color, "#000000");
    assert.deepEqual(frames[0].area, { shape_type: "rect", x: 0.1, y: 0.1, w: 0.8, h: 0.3 });

    // Mutate source scene rectangle to prove independence
    scenes[0].area.x = 0.99;
    assert.equal(frames[0].area.x, 0.1, "Frame area must not change when source scene area is mutated");
    console.log("✓ Pure Check C PASS: copyScenesToFrames creates independent clones");
}

// 18.D & 18.E: Moving Scene after copy does not move Frame; Moving Frame does not move Scene
{
    const store = new AuthoringStore();
    store.copyScenesToFrames();
    const docBefore = store.getDocument();
    const frame0Before = docBefore.pages[0].visual_frames[0].area;
    const scene0Before = docBefore.pages[0].scenes[0].area;

    // Move Scene
    store.moveScene("scene_top", 0.05, 0.05);
    const docAfterSceneMove = store.getDocument();
    assert.deepEqual(
        docAfterSceneMove.pages[0].visual_frames[0].area,
        frame0Before,
        "18.D: Moving Scene must NOT move Frame"
    );

    // Move Frame
    store.moveFrame("frame_1", 0.02, 0.03);
    const docAfterFrameMove = store.getDocument();
    assert.deepEqual(
        docAfterFrameMove.pages[0].scenes[0].area,
        docAfterSceneMove.pages[0].scenes[0].area,
        "18.E: Moving Frame must NOT move Scene"
    );
    console.log("✓ Pure Check D & E PASS: Scene and Frame are completely decoupled and independent");
}

// 18.F: clampFrameDrag cannot leave page bounds
{
    const startArea = { x: 0.80, y: 0.80, w: 0.20, h: 0.20 };
    // Drag way past right and bottom
    const clampedMax = clampFrameDrag(startArea, 0.50, 0.50);
    assert.equal(clampedMax.x, 0.80, "Must clamp to 1.0 - w");
    assert.equal(clampedMax.y, 0.80, "Must clamp to 1.0 - h");

    // Drag past left and top
    const clampedMin = clampFrameDrag(startArea, -0.90, -0.90);
    assert.equal(clampedMin.x, 0.0, "Must clamp to 0.0");
    assert.equal(clampedMin.y, 0.0, "Must clamp to 0.0");
    console.log("✓ Pure Check F PASS: clampFrameDrag cannot leave page bounds");
}

// 18.G, 18.H, 18.I: resizeFrame supports NW/NE/SE/SW, stays in bounds, enforces minimum size
{
    const startArea = { x: 0.20, y: 0.20, w: 0.40, h: 0.40 };

    // SE handle: grows right & down
    const se = resizeFrame(startArea, "se", 0.10, 0.15);
    assert.equal(se.x, 0.20);
    assert.equal(se.y, 0.20);
    assert.equal(se.w, 0.50);
    assert.equal(se.h, 0.55);

    // NW handle: moves top-left, changes w & h
    const nw = resizeFrame(startArea, "nw", 0.05, 0.05);
    assert.equal(nw.x, 0.25);
    assert.equal(nw.y, 0.25);
    assert.equal(nw.w, 0.35);
    assert.equal(nw.h, 0.35);

    // NE handle: changes top & right
    const ne = resizeFrame(startArea, "ne", 0.10, -0.05);
    assert.equal(ne.x, 0.20);
    assert.equal(ne.y, 0.15);
    assert.equal(ne.w, 0.50);
    assert.equal(ne.h, 0.45);

    // SW handle: changes left & bottom
    const sw = resizeFrame(startArea, "sw", -0.05, 0.10);
    assert.equal(sw.x, 0.15);
    assert.equal(sw.y, 0.20);
    assert.equal(sw.w, 0.45);
    assert.equal(sw.h, 0.50);

    // 18.H: Resize cannot exceed page boundaries [0, 1]
    const seOvershoot = resizeFrame(startArea, "se", 0.90, 0.90);
    assert.equal(seOvershoot.x + seOvershoot.w, 1.0);
    assert.equal(seOvershoot.y + seOvershoot.h, 1.0);

    const nwOvershoot = resizeFrame(startArea, "nw", -0.50, -0.50);
    assert.equal(nwOvershoot.x, 0.0);
    assert.equal(nwOvershoot.y, 0.0);

    // 18.I: Minimum size enforced (default 0.05)
    const shrinkSE = resizeFrame(startArea, "se", -0.80, -0.80, 0.05);
    assert.equal(shrinkSE.w, 0.05, "SE must enforce minSize 0.05");
    assert.equal(shrinkSE.h, 0.05, "SE must enforce minSize 0.05");

    const shrinkNW = resizeFrame(startArea, "nw", 0.80, 0.80, 0.05);
    assert.equal(shrinkNW.w, 0.05, "NW must enforce minSize 0.05");
    assert.equal(shrinkNW.h, 0.05, "NW must enforce minSize 0.05");
    console.log("✓ Pure Check G, H, I PASS: Four-corner resize, boundary clipping, and minimum size");
}

// 18.J & 18.K: Overlap detection identifies intersecting pair, touching borders are not overlap
{
    // Intersecting pair
    const overlappingFrames = [
        { frame_id: "f1", area: { x: 0.10, y: 0.10, w: 0.40, h: 0.40 } },
        { frame_id: "f2", area: { x: 0.30, y: 0.30, w: 0.40, h: 0.40 } }
    ];
    const checkOverlap1 = checkFrameOverlap(overlappingFrames);
    assert.equal(checkOverlap1.hasOverlap, true);
    assert.equal(checkOverlap1.pairs.length, 1);
    assert.deepEqual(checkOverlap1.pairs[0], ["f1", "f2"]);

    // Touching borders: f1 right = 0.50, f2 left = 0.50
    const touchingFrames = [
        { frame_id: "f1", area: { x: 0.10, y: 0.10, w: 0.40, h: 0.40 } },
        { frame_id: "f2", area: { x: 0.50, y: 0.10, w: 0.40, h: 0.40 } }
    ];
    const checkTouching = checkFrameOverlap(touchingFrames);
    assert.equal(checkTouching.hasOverlap, false, "Touching borders must NOT be treated as overlap");
    assert.equal(checkTouching.pairs.length, 0);

    // Completely disjoint
    const disjointFrames = [
        { frame_id: "f1", area: { x: 0.05, y: 0.05, w: 0.90, h: 0.40 } },
        { frame_id: "f2", area: { x: 0.05, y: 0.50, w: 0.90, h: 0.40 } }
    ];
    assert.equal(checkFrameOverlap(disjointFrames).hasOverlap, false);
    console.log("✓ Pure Check J & K PASS: Overlap detection correctly flags intersections and ignores touching edges");
}

// ===================================================================
// SECTION 19: STORE TESTS
// ===================================================================

// 19.A: addFrame commits valid schema
{
    const store = new AuthoringStore();
    const frame = store.addFrame({ border_thickness: 6, border_color: "#1e293b" });
    assert.equal(frame.frame_id, "frame_1");
    assert.equal(frame.order, 1);
    assert.equal(frame.border_thickness, 6);
    assert.equal(frame.border_color, "#1e293b");

    const doc = store.getDocument();
    assert.equal(doc.pages[0].visual_frames.length, 1);
    const val = validateAuthoringDocument(doc);
    assert.equal(val.valid, true, `Schema must be valid: ${val.errors}`);
    console.log("✓ Store Check A PASS: addFrame commits valid schema");
}

// 19.B: deleteFrame reorders survivors and leaves other objects intact
{
    const store = new AuthoringStore();
    const f1 = store.addFrame();
    const f2 = store.addFrame();
    const f3 = store.addFrame();
    assert.equal(store.getPage().visual_frames.length, 3);

    // Scenes, CAST, instances must remain untouched
    const initialScenesCount = store.getPage().scenes.length;

    store.deleteFrame(f2.frame_id);
    const remaining = store.getPage().visual_frames;
    assert.equal(remaining.length, 2);
    assert.equal(remaining[0].frame_id, f1.frame_id);
    assert.equal(remaining[0].order, 1);
    assert.equal(remaining[1].frame_id, f3.frame_id);
    assert.equal(remaining[1].order, 2, "Survivor order normalized to 1..N");

    assert.equal(store.getPage().scenes.length, initialScenesCount, "Scenes untouched by frame deletion");
    assert.equal(validateAuthoringDocument(store.getDocument()).valid, true);
    console.log("✓ Store Check B PASS: deleteFrame reorders survivors");
}

// 19.C: copyScenesToFrames replaces previous frames intentionally
{
    const store = new AuthoringStore();
    store.addFrame(); // frame_1
    assert.equal(store.getPage().visual_frames.length, 1);

    // Copy scenes to frames (default doc has 2 scenes)
    store.copyScenesToFrames();
    const frames = store.getPage().visual_frames;
    assert.equal(frames.length, 2, "Replaces existing frames with scene count");
    assert.equal(frames[0].frame_id, "frame_1");
    assert.equal(frames[1].frame_id, "frame_2");
    assert.equal(validateAuthoringDocument(store.getDocument()).valid, true);
    console.log("✓ Store Check C PASS: copyScenesToFrames replaces previous frames intentionally");
}

// 19.D & 19.E: moveFrame and resizeFrame persist geometry
{
    const store = new AuthoringStore();
    const f1 = store.addFrame({ area: { shape_type: "rect", x: 0.1, y: 0.1, w: 0.5, h: 0.3 } });
    const origArea = { ...f1.area };

    store.moveFrame(f1.frame_id, 0.03, 0.02);
    const movedArea = store.getPage().visual_frames[0].area;
    assert.equal(movedArea.x, parseFloat((origArea.x + 0.03).toFixed(4)));
    assert.equal(movedArea.y, parseFloat((origArea.y + 0.02).toFixed(4)));

    store.resizeFrame(f1.frame_id, "se", 0.05, 0.05);
    const resizedArea = store.getPage().visual_frames[0].area;
    assert.equal(resizedArea.w, parseFloat((origArea.w + 0.05).toFixed(4)));
    assert.equal(resizedArea.h, parseFloat((origArea.h + 0.05).toFixed(4)));

    assert.equal(validateAuthoringDocument(store.getDocument()).valid, true);
    console.log("✓ Store Check D & E PASS: moveFrame and resizeFrame persist geometry");
}

// 19.F: border thickness persists
{
    const store = new AuthoringStore();
    const f1 = store.addFrame();
    store.updateFrame(f1.frame_id, { border_thickness: 8 });
    assert.equal(store.getPage().visual_frames[0].border_thickness, 8);
    assert.equal(validateAuthoringDocument(store.getDocument()).valid, true);
    console.log("✓ Store Check F PASS: border thickness persists");
}

// 19.G & 19.H: export/import preserves all frame document data & session state excluded
{
    const store1 = new AuthoringStore();
    store1.copyScenesToFrames();
    store1.moveFrame("frame_1", 0.01, 0.02);
    store1.resizeFrame("frame_1", "se", 0.04, -0.02);
    store1.updateFrame("frame_1", { border_thickness: 7, border_color: "#2563eb" });

    const json1 = store1.exportJson();
    const parsed1 = JSON.parse(json1);

    // Check no session state
    for (const key of FORBIDDEN_SESSION_KEYS) {
        assert.equal(key in parsed1, false, `Forbidden key ${key} in root`);
        assert.equal(key in parsed1.pages[0], false, `Forbidden key ${key} in page`);
    }

    const store2 = new AuthoringStore();
    const importRes = store2.importJson(json1);
    assert.equal(importRes.ok, true, `Import must succeed: ${importRes.error}`);

    const json2 = store2.exportJson();
    assert.equal(json2, json1, "Re-imported document exported JSON must match exactly");

    const importedFrame = store2.getPage().visual_frames[0];
    assert.equal(importedFrame.border_thickness, 7);
    assert.equal(importedFrame.border_color, "#2563eb");
    assert.equal(importedFrame.order, 1);
    assert.equal(validateAuthoringDocument(store2.getDocument()).valid, true);
    console.log("✓ Store Check G & H PASS: export/import round-trip preserves frame data without session leakage");
}

console.log("==================================================");
console.log("ALL PURE & STORE VISUAL FRAME TESTS PASSED (M1C1)");
console.log("==================================================");
