/**
 * test_authoring_ops.mjs — Domain Operations & Invariants Unit Tests
 * ===================================================================
 * TEGAKI Manga Authoring Workspace (M1B)
 * 
 * Verifies all 14 domain checks specified in Card Section 23:
 * 1. add Scene
 * 2. delete Scene cascades children
 * 3. move Scene moves children by effective delta
 * 4. resize Scene proportionally scales children
 * 5. add CAST
 * 6. referenced CAST delete blocked
 * 7. single CAST auto-place
 * 8. multiple CAST requires selection
 * 9. Character placement uses selected CAST
 * 10. Character move stays within Scene
 * 11. Character resize stays within Scene
 * 12. final Character removal restores production input_mode behavior
 * 13. every operation leaves schema validation PASS
 * 14. session state excluded from export
 */

import assert from "node:assert";
import { AuthoringStore } from "../app/src/state/authoring_store.js";
import { SessionState } from "../app/src/state/session_state.js";
import { validateAuthoringDocument, FORBIDDEN_SESSION_KEYS } from "../app/src/domain/authoring_document.js";
import {
    chooseCastForPlacement,
    canDeleteCast,
    onInstanceRemoved,
    moveSceneWithChildren,
    resizeSceneWithChildren,
    clampCharacterDrag,
    clampCharacterResize
} from "../app/src/domain/authoring_ops.js";

console.log("--- Running test_authoring_ops.mjs (M1B Core Edit Parity) ---");

// Test 1: Add Scene
{
    const store = new AuthoringStore();
    const sc = store.addScene({ name: "Scene 3 New", prompt: "sunny park with trees" });
    const doc = store.getDocument();
    assert.strictEqual(doc.pages[0].scenes.length, 3);
    assert.strictEqual(sc.scene_id, "scene_3");
    assert.strictEqual(sc.order, 3);
    assert.strictEqual(validateAuthoringDocument(doc).valid, true);
    console.log("✓ Check 1 Passed: add Scene");
}

// Test 2: Delete Scene cascades children
{
    const store = new AuthoringStore();
    store.addCast({ display_name: "Hero" });
    const inst = store.placeCharacter("scene_top"); // auto-place single cast
    assert.strictEqual(store.getPage().character_instances.length, 1);

    // Deleting scene_top must cascade-delete the instance
    store.deleteScene("scene_top");
    const doc = store.getDocument();
    assert.strictEqual(doc.pages[0].scenes.length, 1);
    assert.strictEqual(doc.pages[0].character_instances.length, 0, "Child instance must be cascaded");
    assert.strictEqual(doc.pages[0].scenes[0].order, 1, "Remaining scene re-indexed");
    assert.strictEqual(validateAuthoringDocument(doc).valid, true);
    console.log("✓ Check 2 Passed: delete Scene cascades children");
}

// Test 3: Move Scene moves children by effective delta
{
    const startSceneArea = { shape_type: "rect", x: 0.10, y: 0.10, w: 0.70, h: 0.40 };
    const childRecords = [
        { id: "c1", area: { shape_type: "rect", x: 0.20, y: 0.15, w: 0.25, h: 0.25 } }
    ];
    const res = moveSceneWithChildren(startSceneArea, childRecords, 0.05, 0.08);
    assert.strictEqual(res.sceneArea.x, 0.15);
    assert.strictEqual(res.sceneArea.y, 0.18);
    assert.strictEqual(res.childAreas[0].area.x, 0.25, "Child moved by effective dx");
    assert.strictEqual(res.childAreas[0].area.y, 0.23, "Child moved by effective dy");

    // Test in store
    const store = new AuthoringStore();
    store.addCast({ display_name: "Alice" });
    store.placeCharacter("scene_top");
    const instBefore = store.getPage().character_instances[0].area.x;
    store.moveScene("scene_top", 0.02, 0.02);
    const instAfter = store.getPage().character_instances[0].area.x;
    assert.strictEqual(instAfter, parseFloat((instBefore + 0.02).toFixed(4)));
    assert.strictEqual(validateAuthoringDocument(store.getDocument()).valid, true);
    console.log("✓ Check 3 Passed: move Scene moves children by effective delta");
}

// Test 4: Resize Scene proportionally scales children
{
    const startScene = { shape_type: "rect", x: 0.10, y: 0.10, w: 0.80, h: 0.40 };
    const childRecords = [
        { id: "c1", area: { shape_type: "rect", x: 0.30, y: 0.20, w: 0.40, h: 0.20 } }
    ];
    const newScene = { shape_type: "rect", x: 0.10, y: 0.10, w: 0.40, h: 0.20 };
    const scaled = resizeSceneWithChildren(startScene, childRecords, newScene);
    assert.strictEqual(scaled[0].area.w, 0.20, "Child width scaled by 0.5");
    assert.strictEqual(scaled[0].area.h, 0.10, "Child height scaled by 0.5");

    // Test in store
    const store = new AuthoringStore();
    store.addCast({ display_name: "Bob" });
    store.placeCharacter("scene_top");
    store.resizeScene("scene_top", { shape_type: "rect", x: 0.08, y: 0.06, w: 0.60, h: 0.30 });
    assert.strictEqual(validateAuthoringDocument(store.getDocument()).valid, true);
    console.log("✓ Check 4 Passed: resize Scene proportionally scales children");
}

// Test 5: Add CAST
{
    const store = new AuthoringStore();
    const c1 = store.addCast({ display_name: "Shinji", identity_prompt: "boy in plugsuit" });
    const doc = store.getDocument();
    assert.strictEqual(doc.pages[0].cast.length, 1);
    assert.strictEqual(c1.cast_id, "cast_1");
    assert.strictEqual(c1.display_name, "Shinji");
    assert.strictEqual(validateAuthoringDocument(doc).valid, true);
    console.log("✓ Check 5 Passed: add CAST");
}

// Test 6: Referenced CAST delete blocked (Delete Guard)
{
    const store = new AuthoringStore();
    const c1 = store.addCast({ display_name: "Asuka" });
    store.placeCharacter("scene_top", c1.cast_id);

    // Attempt to delete cast_1 must throw / be rejected
    let threw = false;
    try {
        store.deleteCast(c1.cast_id);
    } catch (e) {
        threw = true;
        assert.ok(e.message.includes("referenced by active character instances"));
    }
    assert.strictEqual(threw, true, "Referenced CAST deletion must be blocked");
    assert.strictEqual(store.getPage().cast.length, 1, "CAST must still exist");

    // Once character instance removed, CAST deletion must succeed
    store.removeCharacter(store.getPage().character_instances[0].instance_id);
    store.deleteCast(c1.cast_id);
    assert.strictEqual(store.getPage().cast.length, 0);
    assert.strictEqual(validateAuthoringDocument(store.getDocument()).valid, true);
    console.log("✓ Check 6 Passed: referenced CAST delete blocked");
}

// Test 7: Single CAST auto-place
{
    const castList = [{ cast_id: "cast_solo", display_name: "Solo Hero" }];
    const res = chooseCastForPlacement({ castList, selectedCastId: null });
    assert.strictEqual(res.ok, true);
    assert.strictEqual(res.targetCast.cast_id, "cast_solo");
    console.log("✓ Check 7 Passed: single CAST auto-place");
}

// Test 8: Multiple CAST requires selection
{
    const castList = [
        { cast_id: "cast_1", display_name: "A" },
        { cast_id: "cast_2", display_name: "B" }
    ];
    const resNoSel = chooseCastForPlacement({ castList, selectedCastId: null });
    assert.strictEqual(resNoSel.ok, false);
    assert.strictEqual(resNoSel.reason, "SELECTION_REQUIRED");

    const resWithSel = chooseCastForPlacement({ castList, selectedCastId: "cast_2" });
    assert.strictEqual(resWithSel.ok, true);
    assert.strictEqual(resWithSel.targetCast.cast_id, "cast_2");
    console.log("✓ Check 8 Passed: multiple CAST requires selection");
}

// Test 9: Character placement uses selected CAST
{
    const store = new AuthoringStore();
    store.addCast({ display_name: "Hero" });
    store.addCast({ display_name: "Villain" });

    // Multi cast with null selection fails
    assert.throws(() => store.placeCharacter("scene_top", null), /select a CAST character|SELECTION_REQUIRED|selection required/i);

    // Multi cast with explicit selection succeeds
    const inst = store.placeCharacter("scene_top", "cast_2");
    assert.strictEqual(inst.cast_id, "cast_2");
    assert.strictEqual(inst.scene_id, "scene_top");
    assert.strictEqual(validateAuthoringDocument(store.getDocument()).valid, true);
    console.log("✓ Check 9 Passed: Character placement uses selected CAST");
}

// Test 10: Character move stays within Scene
{
    const parentScene = { x: 0.10, y: 0.10, w: 0.60, h: 0.40 };
    const charArea = { x: 0.15, y: 0.15, w: 0.20, h: 0.20 };

    // Move attempting to escape left/top
    const clampLeft = clampCharacterDrag(parentScene, charArea, -0.20, -0.20);
    assert.strictEqual(clampLeft.x, 0.10, "Clamped to scene left");
    assert.strictEqual(clampLeft.y, 0.10, "Clamped to scene top");

    // Move attempting to escape right/bottom
    const clampRight = clampCharacterDrag(parentScene, charArea, 0.80, 0.80);
    assert.strictEqual(clampRight.x, 0.50, "Clamped to scene right: 0.10 + 0.60 - 0.20 = 0.50");
    assert.strictEqual(clampRight.y, 0.30, "Clamped to scene bottom: 0.10 + 0.40 - 0.20 = 0.30");
    console.log("✓ Check 10 Passed: Character move stays within Scene");
}

// Test 11: Character resize stays within Scene
{
    const parentScene = { x: 0.10, y: 0.10, w: 0.50, h: 0.40 };
    const charArea = { x: 0.30, y: 0.20, w: 0.15, h: 0.15 };

    // Attempting to resize larger than remaining space (max W = 0.60 - 0.30 = 0.30)
    const clamped = clampCharacterResize(parentScene, charArea, 0.50, 0.50);
    assert.strictEqual(clamped.w, 0.30, "Width clamped to scene boundary");
    assert.strictEqual(clamped.h, 0.30, "Height clamped to scene boundary: 0.50 - 0.20 = 0.30");
    console.log("✓ Check 11 Passed: Character resize stays within Scene");
}

// Test 12: Final Character removal restores production input_mode behavior
{
    const scene = { scene_id: "sc_1", input_mode: "detailed", prompt: "test prompt" };
    onInstanceRemoved(scene, []);
    assert.strictEqual(scene.input_mode, "simple", "input_mode must reset to simple");
    assert.strictEqual(scene.prompt, "test prompt", "prompt must remain untouched");

    const scene2 = { scene_id: "sc_2", input_mode: "detailed", prompt: "prompt 2" };
    onInstanceRemoved(scene2, [{ instance_id: "inst_remaining" }]);
    assert.strictEqual(scene2.input_mode, "detailed", "input_mode remains detailed when instances remain");
    console.log("✓ Check 12 Passed: final Character removal restores production input_mode behavior");
}

// Test 13: Every operation leaves schema validation PASS
{
    const store = new AuthoringStore();
    assert.strictEqual(validateAuthoringDocument(store.getDocument()).valid, true);

    store.setSeed(99999);
    assert.strictEqual(validateAuthoringDocument(store.getDocument()).valid, true);

    store.setStyleMetadata({ stylePrompt: "cyberpunk, dark neon" });
    assert.strictEqual(validateAuthoringDocument(store.getDocument()).valid, true);

    store.addScene({ name: "Scene 3", prompt: "alleyway" });
    assert.strictEqual(validateAuthoringDocument(store.getDocument()).valid, true);

    store.updateScene("scene_top", { prompt: "updated prompt" });
    assert.strictEqual(validateAuthoringDocument(store.getDocument()).valid, true);

    store.addCast({ display_name: "Rei", color: "#a855f7" });
    assert.strictEqual(validateAuthoringDocument(store.getDocument()).valid, true);

    store.placeCharacter("scene_top", "cast_1");
    assert.strictEqual(validateAuthoringDocument(store.getDocument()).valid, true);

    store.updateCharacter("inst_1", { acting_prompt: "looking solemn" });
    assert.strictEqual(validateAuthoringDocument(store.getDocument()).valid, true);

    store.moveCharacter("inst_1", 0.01, 0.01);
    assert.strictEqual(validateAuthoringDocument(store.getDocument()).valid, true);

    store.resizeCharacter("inst_1", 0.15, 0.15);
    assert.strictEqual(validateAuthoringDocument(store.getDocument()).valid, true);

    store.moveScene("scene_top", 0.01, 0.01);
    assert.strictEqual(validateAuthoringDocument(store.getDocument()).valid, true);

    store.resizeScene("scene_top", { shape_type: "rect", x: 0.10, y: 0.10, w: 0.70, h: 0.35 });
    assert.strictEqual(validateAuthoringDocument(store.getDocument()).valid, true);

    store.removeCharacter("inst_1");
    assert.strictEqual(validateAuthoringDocument(store.getDocument()).valid, true);

    store.deleteCast("cast_1");
    assert.strictEqual(validateAuthoringDocument(store.getDocument()).valid, true);

    store.deleteScene("scene_bottom");
    assert.strictEqual(validateAuthoringDocument(store.getDocument()).valid, true);
    console.log("✓ Check 13 Passed: every operation leaves schema validation PASS");
}

// Test 14: Session state excluded from export
{
    const store = new AuthoringStore();
    store.addCast({ display_name: "Test" });
    store.placeCharacter("scene_top");

    const session = new SessionState();
    session.setActiveTab("cast");
    session.selectCast("cast_1");
    session.selectInstance("inst_1");
    session.selectScene("scene_top");

    const exported = store.exportJson(false);
    FORBIDDEN_SESSION_KEYS.forEach(key => {
        assert.strictEqual(
            exported.includes(`"${key}":`),
            false,
            `Forbidden session key '${key}' found in exported JSON`
        );
    });
    console.log("✓ Check 14 Passed: session state excluded from export");
}

console.log("\n==================================================");
console.log("ALL 14 DOMAIN OPERATION CHECKS PASSED (M1B)");
console.log("==================================================");
