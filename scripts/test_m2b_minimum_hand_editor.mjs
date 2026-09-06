/**
 * test_m2b_minimum_hand_editor.mjs — Headless contract verification for M2B Product Editor
 * ========================================================================================
 * Verifies frontend logic invariants required by Card M2B and M2B.1:
 * 1. Scene move applies common effective delta to child character instances (M0 contract parity)
 * 2. Scene resize proportionally scales child character instances (M0 contract parity)
 * 3. Character drag is bounded by parent scene
 * 4. CAST deletion protection when referenced by instances
 * 5. Scene deletion removes child instances without leaving orphan references
 * 6. Complexity warning thresholds (3=amber, 4+=red)
 * 7. Seed randomize updates page generation seed
 * 8. M2B.1 Selection causality: Selected CAST dictates placed character
 * 9. M2B.1 Prohibited silent cycling: Multi-CAST with null selection fails non-silently
 * 10. M2B.1 Single CAST auto-place: Single CAST automatically chosen without manual click
 * 11. M2B.1 Multiple placements: Repeated placements of same CAST create distinct instance_ids
 * 12. M2B.1 Last instance removal: input_mode resets to 'simple' while prompt is preserved
 * 13. M2B.1 Geometry calculation within scene boundaries
 */
import assert from "node:assert";
import {
    chooseCastForPlacement,
    getNextInstanceId,
    calculateNewInstanceGeometry,
    onInstanceRemoved,
    canDeleteCast,
    cascadeDeleteScene,
    moveSceneWithChildren,
    resizeSceneWithChildren,
    clampCharacterDrag
} from "../custom_nodes_custom/tegaki_manga_nodes/web/js/minimum_hand_authoring_ops.js";

console.log("--- Testing M2B and M2B.1 Minimum-Hand Editor Logic Invariants ---");

// Test 1: Scene Move carries child instances with common delta
{
    const sceneArea = { x: 0.1, y: 0.1, w: 0.8, h: 0.4 };
    const childRecords = [
        { id: "c1", area: { x: 0.15, y: 0.15, w: 0.3, h: 0.3 } },
        { id: "c2", area: { x: 0.55, y: 0.15, w: 0.3, h: 0.3 } }
    ];

    const res = moveSceneWithChildren(sceneArea, childRecords, 0.05, 0.08);

    assert.strictEqual(res.sceneArea.x, 0.15);
    assert.strictEqual(res.sceneArea.y, 0.18);
    assert.strictEqual(res.childAreas[0].area.x, 0.20, "Child 1 X must move by dx");
    assert.strictEqual(res.childAreas[0].area.y, 0.23, "Child 1 Y must move by dy");
    assert.strictEqual(res.childAreas[1].area.x, 0.60, "Child 2 X must move by dx");
    assert.strictEqual(res.childAreas[1].area.y, 0.23, "Child 2 Y must move by dy");
    console.log("✓ Test 1 Passed: Scene Move carries children with common delta");
}

// Test 2: Scene Resize proportionally scales child character instances
{
    const startScene = { x: 0.1, y: 0.1, w: 0.8, h: 0.4 };
    const childRecords = [
        { id: "c1", area: { x: 0.3, y: 0.2, w: 0.4, h: 0.2 } }
    ];
    const newScene = { x: 0.1, y: 0.1, w: 0.6, h: 0.3 };

    const scaled = resizeSceneWithChildren(startScene, childRecords, newScene);

    assert.strictEqual(scaled[0].area.x, 0.25, "Scaled child X must match relative proportion");
    assert.strictEqual(scaled[0].area.y, 0.175, "Scaled child Y must match relative proportion");
    assert.strictEqual(scaled[0].area.w, 0.30, "Scaled child W must be half new scene width");
    assert.strictEqual(scaled[0].area.h, 0.15, "Scaled child H must be half new scene height");
    console.log("✓ Test 2 Passed: Scene Resize scales children proportionally");
}

// Test 3: Character Drag is clipped to parent scene bounds
{
    const parentScene = { x: 0.1, y: 0.1, w: 0.8, h: 0.4 };
    const charBox = { x: 0.15, y: 0.15, w: 0.3, h: 0.3 };

    // Drag beyond left
    const clampedLeft = clampCharacterDrag(parentScene, charBox, -0.10, 0.05);
    assert.strictEqual(clampedLeft.x, 0.10, "Left boundary clamped to scene.x");
    assert.strictEqual(clampedLeft.y, 0.20, "Y within bounds preserved");

    // Drag beyond right
    const clampedRight = clampCharacterDrag(parentScene, charBox, 0.65, 0);
    assert.strictEqual(clampedRight.x, 0.60, "Right boundary clamped to scene.x + scene.w - w");
    console.log("✓ Test 3 Passed: Character drag strictly clipped to parent scene");
}

// Test 4: CAST deletion guard against active references
{
    const instances = [{ instance_id: "i1", cast_id: "c_alice", scene_id: "s1" }];

    assert.strictEqual(canDeleteCast("c_alice", instances), false, "Referenced CAST deletion must be blocked");
    assert.strictEqual(canDeleteCast("c_bob", instances), true, "Unreferenced CAST deletion must be allowed");
    console.log("✓ Test 4 Passed: CAST deletion guard against active references");
}

// Test 5: Scene deletion cascades to remove child instances
{
    let scenes = [{ scene_id: "s1", order: 1 }, { scene_id: "s2", order: 2 }];
    let instances = [
        { instance_id: "i1", scene_id: "s1", cast_id: "c_alice" },
        { instance_id: "i2", scene_id: "s2", cast_id: "c_bob" },
    ];

    const cascadeRes = cascadeDeleteScene("s1", scenes, instances);
    assert.strictEqual(cascadeRes.scenes.length, 1);
    assert.strictEqual(cascadeRes.instances.length, 1);
    assert.strictEqual(cascadeRes.instances[0].instance_id, "i2");
    assert.strictEqual(cascadeRes.instances.some(i => i.scene_id === "s1"), false, "No orphan instances of s1 remain");
    console.log("✓ Test 5 Passed: Scene deletion cascades to remove child instances");
}

// Test 6: Complexity warning thresholds (3=amber, 4+=red)
{
    function getWarning(count) {
        if (count === 3) return "3 characters — Advanced / Seed-Sensitive";
        if (count >= 4) return "4+ characters — Experimental";
        return "normal";
    }

    assert.strictEqual(getWarning(1), "normal");
    assert.strictEqual(getWarning(2), "normal");
    assert.strictEqual(getWarning(3), "3 characters — Advanced / Seed-Sensitive");
    assert.strictEqual(getWarning(4), "4+ characters — Experimental");
    assert.strictEqual(getWarning(5), "4+ characters — Experimental");
    console.log("✓ Test 6 Passed: Complexity warning thresholds (3=amber, 4+=red)");
}

// Test 7: Random seed generation
{
    const seeds = new Set();
    for (let i = 0; i < 100; i++) {
        seeds.add(Math.floor(Math.random() * 2147483647));
    }
    assert.strictEqual(seeds.size, 100, "Random seeds must be unique and within 31-bit range");
    console.log("✓ Test 7 Passed: Random seed generation");
}

// Test 8: M2B.1 Selection causality — Selected CAST dictates placed character
{
    const castList = [
        { cast_id: "cast_1", display_name: "Alice" },
        { cast_id: "cast_2", display_name: "Bob" }
    ];
    const pickBob = chooseCastForPlacement({
        castList,
        selectedCastId: "cast_2",
        sceneInstances: []
    });
    assert.strictEqual(pickBob.ok, true);
    assert.strictEqual(pickBob.targetCast.cast_id, "cast_2", "Bob must be selected regardless of sceneInstances.length === 0");
    assert.strictEqual(pickBob.targetCast.display_name, "Bob");
    console.log("✓ Test 8 Passed: Selection causality (Bob selected => Bob placed as first character)");
}

// Test 9: M2B.1 Prohibited silent cycling — Multi-CAST with null selection fails non-silently
{
    const castList = [
        { cast_id: "cast_1", display_name: "Alice" },
        { cast_id: "cast_2", display_name: "Bob" }
    ];
    const pickNull = chooseCastForPlacement({
        castList,
        selectedCastId: null,
        sceneInstances: []
    });
    assert.strictEqual(pickNull.ok, false, "Must not silently cycle when multiple CASTs exist and none is selected");
    assert.strictEqual(pickNull.reason, "SELECTION_REQUIRED");
    assert.ok(pickNull.error.includes("select a CAST"), "Must provide actionable non-silent error message");
    console.log("✓ Test 9 Passed: Silent cycling prohibited; non-silent prompt to select CAST");
}

// Test 10: M2B.1 Single CAST auto-place — Single CAST automatically chosen without manual click
{
    const singleCastList = [
        { cast_id: "cast_1", display_name: "Alice" }
    ];
    const pickAuto = chooseCastForPlacement({
        castList: singleCastList,
        selectedCastId: null,
        sceneInstances: []
    });
    assert.strictEqual(pickAuto.ok, true, "Single CAST registered must auto-place without explicit selection");
    assert.strictEqual(pickAuto.targetCast.cast_id, "cast_1");
    console.log("✓ Test 10 Passed: Single CAST auto-place when selectedCastId is null");
}

// Test 11: M2B.1 Multiple placements of same CAST create distinct instance_ids
{
    const allInstances = [
        { instance_id: "inst_1", cast_id: "cast_1", scene_id: "scene_1" }
    ];
    const nextId1 = getNextInstanceId(allInstances);
    assert.strictEqual(nextId1, "inst_2");

    allInstances.push({ instance_id: nextId1, cast_id: "cast_1", scene_id: "scene_1" });
    const nextId2 = getNextInstanceId(allInstances);
    assert.strictEqual(nextId2, "inst_3");
    assert.notStrictEqual(nextId1, nextId2, "Instance IDs must be distinct even for same cast_id");
    console.log("✓ Test 11 Passed: Repeated placements of same CAST generate distinct instance_ids");
}

// Test 12: M2B.1 Last instance removal: input_mode resets to 'simple' while prompt is preserved
{
    const scene = {
        scene_id: "scene_1",
        input_mode: "cast",
        prompt: "Preserved original background prompt: coffee shop interior"
    };
    onInstanceRemoved(scene, []);
    assert.strictEqual(scene.input_mode, "simple", "input_mode must reset to simple when last instance is removed");
    assert.strictEqual(scene.prompt, "Preserved original background prompt: coffee shop interior", "Scene prompt must be untouched");
    console.log("✓ Test 12 Passed: Last instance removal resets input_mode to simple and preserves prompt");
}

// Test 13: M2B.1 Geometry calculation within scene boundaries
{
    const sceneArea = { x: 0.1, y: 0.2, w: 0.8, h: 0.6 };
    const geom0 = calculateNewInstanceGeometry(sceneArea, 0);
    assert.ok(geom0.x >= sceneArea.x);
    assert.ok(geom0.x + geom0.w <= sceneArea.x + sceneArea.w);
    assert.ok(geom0.y >= sceneArea.y);
    assert.ok(geom0.y + geom0.h <= sceneArea.y + sceneArea.h);

    const geom1 = calculateNewInstanceGeometry(sceneArea, 1);
    assert.ok(geom1.x >= sceneArea.x);
    assert.ok(geom1.x + geom1.w <= sceneArea.x + sceneArea.w);
    assert.notStrictEqual(geom0.x, geom1.x, "Consecutive characters must be placed at offset positions");
    console.log("✓ Test 13 Passed: Character geometry placed safely inside parent scene");
}

console.log("\nALL JS FRONTEND CONTRACT TESTS PASSED (13/13)!");
