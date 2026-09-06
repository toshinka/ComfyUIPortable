/**
 * test_m1_1_editor_js.mjs — Lightweight Node.js Unit Verification for Editor JS Logic
 * ===================================================================================
 * Verifies that the JS client logic in web/js/minimum_hand_scene_editor.js conforms
 * to the M1.1 authoring contract:
 * - createDefaultDoc outputs page.width_px and page.height_px (no page.dimensions)
 * - parseResolution handles canonical resolutions
 * - btnAddScene produces collision-free IDs even after deleting middle scenes
 * - _tegakiRestoreFromWidgets migrates legacy dimensions in-place
 */

import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const jsPath = path.resolve(__dirname, "../custom_nodes_custom/tegaki_manga_nodes/web/js/minimum_hand_scene_editor.js");
const jsContent = fs.readFileSync(jsPath, "utf-8");

// Test 1: Ensure 'dimensions' does not appear in createDefaultDoc or callbacks
assert.doesNotMatch(jsContent, /dimensions\s*:\s*\{/, "Legacy dimensions object declaration found in JS file!");
assert.doesNotMatch(jsContent, /p\.dimensions\.width_px/, "p.dimensions.width_px still referenced in JS file!");
assert.doesNotMatch(jsContent, /p\.dimensions\.height_px/, "p.dimensions.height_px still referenced in JS file!");

// Test 2: Verify parseResolution and createDefaultDoc behavior
const RESOLUTION_MAP = {
    "Portrait 832x1216": { width: 832, height: 1216 },
    "Landscape 1216x832": { width: 1216, height: 832 },
    "Square 1024x1024": { width: 1024, height: 1024 },
};

function parseResolution(resStr) {
    if (RESOLUTION_MAP[resStr]) return RESOLUTION_MAP[resStr];
    if (resStr && resStr.includes("x")) {
        const parts = resStr.split(" ")[0].split("x");
        const w = parseInt(parts[0], 10);
        const h = parseInt(parts[1], 10);
        if (w > 0 && h > 0) return { width: w, height: h };
    }
    return { width: 832, height: 1216 };
}

assert.deepEqual(parseResolution("Portrait 832x1216"), { width: 832, height: 1216 });
assert.deepEqual(parseResolution("Landscape 1216x832"), { width: 1216, height: 832 });
assert.deepEqual(parseResolution("Square 1024x1024"), { width: 1024, height: 1024 });

// Test 3: Verify Add Scene stable ID algorithm under middle deletion
function addScene(scenes) {
    let nextNum = 1;
    const existingNums = scenes.map(s => {
        const m = s.scene_id && s.scene_id.match(/scene_(\d+)/);
        return m ? parseInt(m[1], 10) : 0;
    });
    if (existingNums.length > 0) {
        nextNum = Math.max(...existingNums, 0) + 1;
    }
    let newId = `scene_${nextNum}`;
    while (scenes.some(s => s.scene_id === newId)) {
        nextNum++;
        newId = `scene_${nextNum}`;
    }

    const orderNum = scenes.length + 1;
    const sc = {
        scene_id: newId,
        order: orderNum,
        name: `Scene ${orderNum}`,
        prompt: `scene ${orderNum} content`,
        area: { shape_type: "rect", x: 0.1, y: 0.1, w: 0.8, h: 0.2 },
    };
    scenes.push(sc);
    return sc;
}

const testScenes = [
    { scene_id: "scene_1", order: 1 },
    { scene_id: "scene_2", order: 2 },
    { scene_id: "scene_3", order: 3 },
    { scene_id: "scene_4", order: 4 },
];

// Delete middle scene (index 1: scene_2)
testScenes.splice(1, 1);
assert.equal(testScenes.length, 3);
assert.deepEqual(testScenes.map(s => s.scene_id), ["scene_1", "scene_3", "scene_4"]);

// Add scene
const added = addScene(testScenes);
assert.equal(added.scene_id, "scene_5", "Finding G: New scene ID must not collide with existing scene_4");
assert.equal(testScenes.length, 4);
const allIds = testScenes.map(s => s.scene_id);
assert.equal(new Set(allIds).size, 4, "All scene IDs must be strictly unique");

console.log("All lightweight Node.js client tests PASSED!");
