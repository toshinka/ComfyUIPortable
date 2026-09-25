/**
 * Unit tests for Manga Authoring Document Identity Lifecycle (Card MANGA-DOCUMENT-IDENTITY-LIFECYCLE1).
 *
 * Covers requirements A through I:
 * A. New document receives an ID.
 * B. Two new documents receive distinct IDs.
 * C. Export/import preserves an existing document_id.
 * D. Legacy doc_-prefixed ID remains accepted and unchanged.
 * E. Missing ID is assigned at the defined ingestion boundary.
 * F. Explicit duplication produces a different document_id.
 * G. Duplication preserves the intended Scene/CAST/Page content and does not mutate its source.
 * H. Ordinary Scene/CAST edits do not change the document_id.
 * I. Existing export/import behavior does not become dependent on a backend file registry.
 */

import test from "node:test";
import assert from "node:assert/strict";

import {
    createDefaultAuthoringDocument,
    validateAuthoringDocument,
    generateDocumentId,
    isValidDocumentId,
    ensureDocumentIdentity,
    duplicateDocument
} from "../app/src/domain/authoring_document.js";
import {
    AuthoringStore,
    createNewAuthoringSessionDocument
} from "../app/src/state/authoring_store.js";

const UUID_REGEX = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

test("A. New document receives an ID", () => {
    const doc = createDefaultAuthoringDocument();
    assert.ok(doc.document_id, "New document must have document_id");
    assert.match(doc.document_id, UUID_REGEX, "Default new document ID should be a UUID");

    const sessionDoc = createNewAuthoringSessionDocument();
    assert.ok(sessionDoc.document_id, "New session document must have document_id");
    assert.match(sessionDoc.document_id, UUID_REGEX, "New session document ID should be a UUID");
});

test("B. Two new documents receive distinct IDs", () => {
    const doc1 = createDefaultAuthoringDocument();
    const doc2 = createDefaultAuthoringDocument();
    assert.notEqual(doc1.document_id, doc2.document_id, "Two new documents must have distinct IDs");

    const id1 = generateDocumentId();
    const id2 = generateDocumentId();
    assert.notEqual(id1, id2, "generateDocumentId must produce unique values");
});

test("C. Export/import preserves an existing document_id", () => {
    const store = new AuthoringStore();
    const originalId = store.getDocument().document_id;
    assert.ok(originalId);

    const exportedJson = store.exportJson(false);
    const store2 = new AuthoringStore();
    const importResult = store2.importJson(exportedJson);

    assert.ok(importResult.ok, "Import must succeed");
    assert.equal(store2.getDocument().document_id, originalId, "Import must preserve existing document_id");
});

test("D. Legacy doc_-prefixed ID remains accepted and unchanged", () => {
    const legacyDoc = createDefaultAuthoringDocument();
    legacyDoc.document_id = "doc_legacy12345";

    const validation = validateAuthoringDocument(legacyDoc);
    assert.ok(validation.valid, "Legacy document_id must be valid");

    const store = new AuthoringStore(legacyDoc);
    assert.equal(store.getDocument().document_id, "doc_legacy12345", "Store must preserve legacy document_id");

    const exportedJson = store.exportJson(false);
    const store2 = new AuthoringStore();
    const res = store2.importJson(exportedJson);
    assert.ok(res.ok);
    assert.equal(store2.getDocument().document_id, "doc_legacy12345", "Import must preserve legacy ID verbatim");
});

test("E. Missing ID is assigned at the defined ingestion boundary", () => {
    const unassignedDoc = createDefaultAuthoringDocument();
    delete unassignedDoc.document_id;

    // Caller's object is not mutated
    const originalClone = JSON.parse(JSON.stringify(unassignedDoc));
    const ingested = ensureDocumentIdentity(unassignedDoc);

    assert.equal(unassignedDoc.document_id, undefined, "Original caller object must not be mutated");
    assert.deepEqual(unassignedDoc, originalClone, "Original caller object must remain unchanged");
    assert.ok(ingested.document_id, "Ingested document must acquire document_id");
    assert.match(ingested.document_id, UUID_REGEX, "Assigned ID must be a UUID");

    // Also verify via store.importJson
    const store = new AuthoringStore();
    const jsonWithoutId = JSON.stringify(unassignedDoc);
    const res = store.importJson(jsonWithoutId);
    assert.ok(res.ok);
    assert.ok(store.getDocument().document_id, "Imported document without ID must acquire document_id");
    assert.match(store.getDocument().document_id, UUID_REGEX);
});

test("F. Explicit duplication produces a different document_id", () => {
    const doc = createDefaultAuthoringDocument();
    const originalId = doc.document_id;

    const copy = duplicateDocument(doc);
    assert.ok(copy.document_id);
    assert.notEqual(copy.document_id, originalId, "Duplicate must have a different document_id");

    // Also verify store.duplicateDocument
    const store = new AuthoringStore(doc);
    const storeOriginalId = store.getDocument().document_id;
    const duplicatedDoc = store.duplicateDocument();

    assert.notEqual(duplicatedDoc.document_id, storeOriginalId, "Store duplicate must have a distinct ID");
    assert.equal(store.getDocument().document_id, duplicatedDoc.document_id, "Store should now hold the duplicated doc");
});

test("G. Duplication preserves the intended Scene/CAST/Page content and does not mutate its source", () => {
    const store = new AuthoringStore();
    store.addScene({ name: "Scene Test", prompt: "cat in the yard", area: { shape_type: "rect", x: 0.1, y: 0.1, w: 0.8, h: 0.3 } });
    store.addCast({ name: "Hero", identityPrompt: "1boy, warrior" });

    const sourceSnapshot = store.getDocument();
    const sourceClone = JSON.parse(JSON.stringify(sourceSnapshot));

    const copy = duplicateDocument(sourceSnapshot);

    // Source is not mutated
    assert.deepEqual(sourceSnapshot, sourceClone, "Source snapshot must not be mutated by duplication");

    // Content is preserved
    assert.equal(copy.pages.length, sourceSnapshot.pages.length);
    assert.equal(copy.pages[0].scenes.length, sourceSnapshot.pages[0].scenes.length);
    assert.equal(copy.pages[0].scenes[0].scene_id, sourceSnapshot.pages[0].scenes[0].scene_id);
    assert.equal(copy.pages[0].scenes[0].prompt, sourceSnapshot.pages[0].scenes[0].prompt);
    assert.equal(copy.pages[0].cast.length, sourceSnapshot.pages[0].cast.length);
    assert.equal(copy.pages[0].cast[0].cast_id, sourceSnapshot.pages[0].cast[0].cast_id);

    // Only document_id is changed
    assert.notEqual(copy.document_id, sourceSnapshot.document_id);
});

test("H. Ordinary Scene/CAST edits do not change the document_id", () => {
    const store = new AuthoringStore();
    const originalId = store.getDocument().document_id;

    store.addScene({ name: "Scene A", prompt: "dog running" });
    assert.equal(store.getDocument().document_id, originalId, "Adding scene must not change document_id");

    store.updateScene(store.getPage().scenes[0].scene_id, { prompt: "dog resting" });
    assert.equal(store.getDocument().document_id, originalId, "Updating scene must not change document_id");

    store.addCast({ name: "Rival", identityPrompt: "1girl" });
    assert.equal(store.getDocument().document_id, originalId, "Adding cast must not change document_id");

    store.setStyleMetadata({ stylePrompt: "watercolor manga" });
    assert.equal(store.getDocument().document_id, originalId, "Updating style must not change document_id");
});

test("I. Existing export/import behavior does not become dependent on a backend file registry", () => {
    const store = new AuthoringStore();
    const exportedJson = store.exportJson(true);

    assert.equal(typeof exportedJson, "string");
    assert.ok(exportedJson.includes('"schema_id": "TEGAKI_AUTHORING_DOCUMENT"'));
    assert.ok(exportedJson.includes('"document_id":'));

    const parsed = JSON.parse(exportedJson);
    assert.ok(isValidDocumentId(parsed.document_id));

    const newStore = new AuthoringStore();
    const res = newStore.importJson(exportedJson);
    assert.ok(res.ok, "Import must work completely in-memory without any backend registry");
    assert.equal(newStore.getDocument().document_id, parsed.document_id);
});
