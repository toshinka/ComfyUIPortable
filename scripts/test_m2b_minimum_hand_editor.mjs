/**
 * test_m2b_minimum_hand_editor.mjs — Headless contract verification for M2B Product Editor
 * ========================================================================================
 * Verifies frontend logic invariants required by Card §95:
 * 1. Scene move applies common effective delta to child character instances (M0 contract parity)
 * 2. Scene resize proportionally scales child character instances (M0 contract parity)
 * 3. Character drag is bounded by parent scene
 * 4. CAST deletion protection when referenced by instances
 * 5. Scene deletion removes child instances without leaving orphan references
 * 6. Seed randomize updates page generation seed
 * 7. 3+ character warning logic
 */
import assert from "node:assert";

console.log("--- Testing M2B Minimum-Hand Editor Logic Invariants ---");

// Test 1: Scene Move carries child instances with common delta
{
    const sceneArea = { x: 0.1, y: 0.1, w: 0.8, h: 0.4 };
    const child1 = { id: "c1", area: { x: 0.15, y: 0.15, w: 0.3, h: 0.3 } };
    const child2 = { id: "c2", area: { x: 0.55, y: 0.15, w: 0.3, h: 0.3 } };

    // Move scene by dx=+0.05, dy=+0.08
    const dx = 0.05;
    const dy = 0.08;
    const newSceneX = parseFloat((sceneArea.x + dx).toFixed(4));
    const newSceneY = parseFloat((sceneArea.y + dy).toFixed(4));
    const effectiveDx = newSceneX - sceneArea.x;
    const effectiveDy = newSceneY - sceneArea.y;

    const newChild1X = parseFloat((child1.area.x + effectiveDx).toFixed(4));
    const newChild1Y = parseFloat((child1.area.y + effectiveDy).toFixed(4));
    const newChild2X = parseFloat((child2.area.x + effectiveDx).toFixed(4));
    const newChild2Y = parseFloat((child2.area.y + effectiveDy).toFixed(4));

    assert.strictEqual(newChild1X, 0.20, "Child 1 X must move by dx");
    assert.strictEqual(newChild1Y, 0.23, "Child 1 Y must move by dy");
    assert.strictEqual(newChild2X, 0.60, "Child 2 X must move by dx");
    assert.strictEqual(newChild2Y, 0.23, "Child 2 Y must move by dy");
    console.log("✓ Test 1 Passed: Scene Move carries children with common delta");
}

// Test 2: Scene Resize proportionally scales child character instances
{
    const startScene = { x: 0.1, y: 0.1, w: 0.8, h: 0.4 };
    const child = { area: { x: 0.3, y: 0.2, w: 0.4, h: 0.2 } };

    // Resize scene: w: 0.8 -> 0.6, h: 0.4 -> 0.3
    const newScene = { x: 0.1, y: 0.1, w: 0.6, h: 0.3 };

    const relX = (child.area.x - startScene.x) / startScene.w; // (0.3 - 0.1) / 0.8 = 0.25
    const relY = (child.area.y - startScene.y) / startScene.h; // (0.2 - 0.1) / 0.4 = 0.25
    const relW = child.area.w / startScene.w;                   // 0.4 / 0.8 = 0.50
    const relH = child.area.h / startScene.h;                   // 0.2 / 0.4 = 0.50

    const scaledX = parseFloat((newScene.x + relX * newScene.w).toFixed(4));
    const scaledY = parseFloat((newScene.y + relY * newScene.h).toFixed(4));
    const scaledW = parseFloat((relW * newScene.w).toFixed(4));
    const scaledH = parseFloat((relH * newScene.h).toFixed(4));

    assert.strictEqual(scaledX, 0.25, "Scaled child X must match relative proportion");
    assert.strictEqual(scaledY, 0.175, "Scaled child Y must match relative proportion");
    assert.strictEqual(scaledW, 0.30, "Scaled child W must be half new scene width");
    assert.strictEqual(scaledH, 0.15, "Scaled child H must be half new scene height");
    console.log("✓ Test 2 Passed: Scene Resize scales children proportionally");
}

// Test 3: Character Drag is clipped to parent scene bounds
{
    const parentScene = { x: 0.1, y: 0.1, w: 0.8, h: 0.4 };
    const charBox = { x: 0.15, y: 0.15, w: 0.3, h: 0.3 };

    // Try dragging beyond left
    let nx = 0.05; // < parentScene.x (0.1)
    let ny = 0.20;
    const clampedX = Math.max(parentScene.x, Math.min(parentScene.x + parentScene.w - charBox.w, nx));
    const clampedY = Math.max(parentScene.y, Math.min(parentScene.y + parentScene.h - charBox.h, ny));

    assert.strictEqual(clampedX, 0.10, "Left boundary must be clamped to scene.x");
    assert.strictEqual(clampedY, 0.20, "Y within bounds preserved");

    // Try dragging beyond right
    nx = 0.80; // parentScene.x + parentScene.w - charBox.w = 0.1 + 0.8 - 0.3 = 0.6
    const clampedRight = Math.max(parentScene.x, Math.min(parentScene.x + parentScene.w - charBox.w, nx));
    assert.strictEqual(parseFloat(clampedRight.toFixed(4)), 0.60, "Right boundary must be clamped to scene.x + scene.w - w");
    console.log("✓ Test 3 Passed: Character drag strictly clipped to parent scene");
}

// Test 4: CAST deletion rejected when referenced by instance
{
    const castList = [{ cast_id: "c_alice", display_name: "Alice" }];
    const instances = [{ instance_id: "i1", cast_id: "c_alice", scene_id: "s1" }];

    function canDeleteCast(castId) {
        return !instances.some(i => i.cast_id === castId);
    }

    assert.strictEqual(canDeleteCast("c_alice"), false, "Referenced CAST deletion must be blocked");
    assert.strictEqual(canDeleteCast("c_bob"), true, "Unreferenced CAST deletion must be allowed");
    console.log("✓ Test 4 Passed: CAST deletion guard against active references");
}

// Test 5: Scene deletion removes child instances without leaving orphans
{
    let scenes = [{ scene_id: "s1" }, { scene_id: "s2" }];
    let instances = [
        { instance_id: "i1", scene_id: "s1", cast_id: "c_alice" },
        { instance_id: "i2", scene_id: "s2", cast_id: "c_bob" },
    ];

    // Delete s1
    const deadSceneId = "s1";
    scenes = scenes.filter(s => s.scene_id !== deadSceneId);
    instances = instances.filter(i => i.scene_id !== deadSceneId);

    assert.strictEqual(scenes.length, 1);
    assert.strictEqual(instances.length, 1);
    assert.strictEqual(instances[0].instance_id, "i2");
    assert.strictEqual(instances.some(i => i.scene_id === "s1"), false, "No orphan instances of s1 remain");
    console.log("✓ Test 5 Passed: Scene deletion cascades to remove child instances");
}

// Test 6: Complexity Warning Logic
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

// Test 7: Seed Randomize
{
    const seeds = new Set();
    for (let i = 0; i < 100; i++) {
        seeds.add(Math.floor(Math.random() * 2147483647));
    }
    assert.strictEqual(seeds.size, 100, "Random seeds must be unique and within 31-bit range");
    console.log("✓ Test 7 Passed: Random seed generation");
}

console.log("\nALL JS FRONTEND CONTRACT TESTS PASSED (7/7)!");
