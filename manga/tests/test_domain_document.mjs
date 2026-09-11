/**
 * test_domain_document.mjs — Domain Document Parity & Isolation Tests
 * ===================================================================
 * TEGAKI Manga Authoring Workspace (M1A)
 * 
 * Verifies:
 * 1. Schema ID and Version parity (TEGAKI_AUTHORING_DOCUMENT 1.0.0).
 * 2. Default document structure matches canonical reference.
 * 3. Rich fixture structure contains all authoring layers.
 * 4. Document import/export round-trip preserves valid semantics.
 * 5. Session state leakage detection works and rejects polluted documents.
 * 6. Exported JSON has zero session/UI keys.
 */

import assert from "node:assert";
import {
    SCHEMA_ID,
    SCHEMA_VERSION,
    createDefaultAuthoringDocument,
    createRichAuthoringFixture,
    validateAuthoringDocument,
    cloneDocument,
    FORBIDDEN_SESSION_KEYS
} from "../app/src/domain/authoring_document.js";
import { AuthoringStore } from "../app/src/state/authoring_store.js";
import { SessionState } from "../app/src/state/session_state.js";

console.log("--- Running test_domain_document.mjs ---");

// Test 1: Schema Invariants
assert.strictEqual(SCHEMA_ID, "TEGAKI_AUTHORING_DOCUMENT");
assert.strictEqual(SCHEMA_VERSION, "1.0.0");
console.log("✓ Test 1 Passed: Schema ID and Version match canonical 1.0.0");

// Test 2: Default Document Parity
const defaultDoc = createDefaultAuthoringDocument();
const valDefault = validateAuthoringDocument(defaultDoc);
assert.strictEqual(valDefault.valid, true, "Default doc must be strictly valid");
assert.strictEqual(defaultDoc.pages.length, 1);
assert.strictEqual(defaultDoc.pages[0].width_px, 832);
assert.strictEqual(defaultDoc.pages[0].height_px, 1216);
assert.strictEqual(defaultDoc.pages[0].scenes.length, 2);
assert.deepStrictEqual(defaultDoc.pages[0].visual_frames, []);
assert.deepStrictEqual(defaultDoc.pages[0].cast, []);
assert.deepStrictEqual(defaultDoc.pages[0].character_instances, []);
assert.deepStrictEqual(defaultDoc.pages[0].guides, []);
console.log("✓ Test 2 Passed: Default document has exact semantic parity");

// Test 3: Rich Fixture Populates All Layers
const richDoc = createRichAuthoringFixture();
const valRich = validateAuthoringDocument(richDoc);
assert.strictEqual(valRich.valid, true, "Rich fixture must be strictly valid");
assert.strictEqual(richDoc.pages[0].scenes.length, 2);
assert.strictEqual(richDoc.pages[0].visual_frames.length, 2);
assert.strictEqual(richDoc.pages[0].cast.length, 2);
assert.strictEqual(richDoc.pages[0].character_instances.length, 2);
assert.strictEqual(richDoc.pages[0].guides.length, 1);
assert.strictEqual(richDoc.pages[0].guides[0].figure_regions.length, 2);
console.log("✓ Test 3 Passed: Rich fixture correctly populates all layers");

// Test 4: Import / Export Round-Trip
const store = new AuthoringStore();
store.setDocument(richDoc);
const exportedJson = store.exportJson(true);
const roundTripDoc = JSON.parse(exportedJson);
const valRoundTrip = validateAuthoringDocument(roundTripDoc);
assert.strictEqual(valRoundTrip.valid, true);
assert.deepStrictEqual(roundTripDoc, richDoc);
console.log("✓ Test 4 Passed: JSON import/export round-trip preserves exact semantics");

// Test 5: Session State Isolation & Forbidden Keys Detection
const session = new SessionState();
session.setActiveTab("frames");
session.selectScene("scene_test");
session.selectFrame("frame_test");
session.selectInstance("inst_test");

// Verify session state snapshot has forbidden keys
const snapshot = session.getSnapshot();
assert.ok("activeTab" in snapshot);
assert.ok("selectedSceneId" in snapshot);

// Pollute a document with session state
const pollutedDoc = cloneDocument(defaultDoc);
pollutedDoc.activeTab = "frames";
pollutedDoc.pages[0].selectedSceneId = "scene_top";
const valPolluted = validateAuthoringDocument(pollutedDoc);
assert.strictEqual(valPolluted.valid, false, "Polluted document must fail validation");
assert.ok(valPolluted.errors.some(e => e.includes("Session state leakage detected")));
console.log("✓ Test 5 Passed: Session state leakage properly detected and rejected");

// Test 6: Verify Store Export Never Contains Session Keys
const store2 = new AuthoringStore();
const exported = store2.exportJson(false);
FORBIDDEN_SESSION_KEYS.forEach(key => {
    assert.strictEqual(exported.includes(`"${key}":`), false, `Exported JSON must not contain session key '${key}'`);
});
console.log("✓ Test 6 Passed: Store export contains zero session keys");

console.log("All domain document tests PASSED successfully.");
