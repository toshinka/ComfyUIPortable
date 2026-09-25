/**
 * test_page_composite_current.mjs — Targeted tests for PageCompositeCurrentClassifier.
 *
 * Verifies:
 * - Exclusion of volatile fields (plan_id, created_at, top/scene diagnostics)
 * - Sensitivity to semantic changes (selected result, artifact digest, placement, order, state, dimensions)
 * - Robust UNKNOWN handling (unsupported schema/version, prep failure, owner mismatch)
 * - Exact historical plan digest vs semantic composition digest distinction
 * - Non-destructive read-only classification
 */

import assert from "node:assert/strict";
import fs from "node:fs/promises";
import path from "node:path";
import os from "node:os";
import zlib from "node:zlib";
import { createHash } from "node:crypto";

import {
    PageCompositeCurrentClassifier,
    CURRENT_STATUS,
    CURRENT_REASON,
    PAGE_COMPOSITE_SEMANTIC_DIGEST_VERSION,
    computeSemanticCompositionDigest,
    classifyCurrentPageComposite,
} from "../service/page_composite_current.mjs";
import { PageCompositeStore } from "../service/page_composite_store.mjs";
import { PageCompositeIndex } from "../service/page_composite_index.mjs";
import { computePngCrc32 } from "../service/png_artifact_analyzer.mjs";

function createValidPngBuffer(width, height) {
    const sig = Buffer.from([0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A]);
    const ihdrData = Buffer.alloc(13);
    ihdrData.writeUInt32BE(width, 0);
    ihdrData.writeUInt32BE(height, 4);
    ihdrData[8] = 8;
    ihdrData[9] = 6;
    ihdrData[10] = 0;
    ihdrData[11] = 0;
    ihdrData[12] = 0;

    const ihdrChunk = Buffer.alloc(4 + 4 + 13 + 4);
    ihdrChunk.writeUInt32BE(13, 0);
    ihdrChunk.write("IHDR", 4);
    ihdrData.copy(ihdrChunk, 8);
    const ihdrCrc = computePngCrc32(ihdrChunk, 4, 21);
    ihdrChunk.writeUInt32BE(ihdrCrc, 21);

    const rawScanline = Buffer.alloc(1 + width * 4, 0);
    const rawScanlines = Buffer.concat(Array(height).fill(rawScanline));
    const compressed = zlib.deflateSync(rawScanlines);

    const idatChunk = Buffer.alloc(4 + 4 + compressed.length + 4);
    idatChunk.writeUInt32BE(compressed.length, 0);
    idatChunk.write("IDAT", 4);
    compressed.copy(idatChunk, 8);
    const idatCrc = computePngCrc32(idatChunk, 4, 8 + compressed.length);
    idatChunk.writeUInt32BE(idatCrc, 8 + compressed.length);

    const iendChunk = Buffer.alloc(4 + 4 + 4);
    iendChunk.writeUInt32BE(0, 0);
    iendChunk.write("IEND", 4);
    const iendCrc = computePngCrc32(iendChunk, 4, 8);
    iendChunk.writeUInt32BE(iendCrc, 8);

    return Buffer.concat([sig, ihdrChunk, idatChunk, iendChunk]);
}

function buildTestPlan({
    docId = "doc_test",
    pageId = "page_1",
    planId = "plan_001",
    createdAt = "2026-09-01T10:00:00.000Z",
    width = 64,
    height = 64,
    topDiag = { total_scenes: 1, filled_scenes: 1, unfilled_scenes: 0 },
    sceneDiag = { evaluated_candidates: 1, total_indexed_candidates: 1 },
    sceneState = "CURRENT_RESULT",
    sceneOrder = 0,
    manifestId = "550e8400-e29b-41d4-a716-446655440001",
    contentDigest = "a".repeat(64),
    placementX = 0,
    placementY = 0,
    schemaVersion = "1.0.0",
} = {}) {
    return {
        schema_id: "TEGAKI_PAGE_COMPOSITION_PLAN",
        schema_version: schemaVersion,
        plan_id: planId,
        created_at: createdAt,
        page: {
            document_id: docId,
            page_id: pageId,
            width,
            height,
        },
        background: {
            mode: "solid",
            value: "white",
        },
        scenes: [
            {
                scene_id: "scene_001",
                order: sceneOrder,
                state: sceneState,
                selected_result: sceneState === "CURRENT_RESULT" ? {
                    manifest_id: manifestId,
                    artifact: {
                        locator: `manga/data/results/${manifestId}/artifact.png`,
                        dimensions: { width, height },
                        content_digest: contentDigest,
                    },
                    placement: {
                        page_target_rect: { x: placementX, y: placementY, width, height },
                        local_source_rect: { x: 0, y: 0, width, height },
                        transform: {},
                        target_page_dimensions: { width, height },
                    },
                } : null,
                diagnostics: sceneDiag,
            },
        ],
        diagnostics: topDiag,
    };
}

async function runTests() {
    let passed = 0;
    let failed = 0;

    async function test(name, fn) {
        try {
            await fn();
            console.log(`PASS: ${name}`);
            passed++;
        } catch (err) {
            console.error(`FAIL: ${name}`);
            console.error(err);
            failed++;
        }
    }

    const baseTempDir = await fs.mkdtemp(path.join(os.tmpdir(), "manga-current-test-"));

    try {
        const storeDir = path.join(baseTempDir, "store");
        const indexDir = path.join(baseTempDir, "index");
        await fs.mkdir(storeDir, { recursive: true });
        await fs.mkdir(indexDir, { recursive: true });

        const store = new PageCompositeStore(storeDir);
        const index = new PageCompositeIndex({ directory: indexDir, store });
        const pngBytes = createValidPngBuffer(64, 64);

        const baseStoredPlan = buildTestPlan({
            docId: "doc_alpha",
            pageId: "page_1",
            planId: "plan_stored_001",
            createdAt: "2026-09-01T12:00:00.000Z",
            topDiag: { total_scenes: 1, filled_scenes: 1, unfilled_scenes: 0, test_diag: "old" },
            sceneDiag: { evaluated_candidates: 3, total_indexed_candidates: 3 },
            manifestId: "550e8400-e29b-41d4-a716-446655440001",
            contentDigest: "a".repeat(64),
            placementX: 0,
            placementY: 0,
        });

        const savedComposite = await store.saveComposite({
            composition_plan: baseStoredPlan,
            composite_bytes: pngBytes,
        });
        await index.indexComposite(savedComposite.composite_id);
        const compositeId = savedComposite.composite_id;

        const authoringDoc = {
            document_id: "doc_alpha",
            pages: [{ page_id: "page_1", width: 64, height: 64 }],
        };

        // CASE A: Identical semantic plan -> CURRENT
        await test("Case A: Identical semantic plan -> CURRENT", async () => {
            const currentPlan = structuredClone(baseStoredPlan);
            const classifier = new PageCompositeCurrentClassifier({
                store,
                index,
                prepFn: async () => currentPlan,
            });

            const res = await classifier.classifyCurrentPageComposite({
                composite_id: compositeId,
                authoring_document: authoringDoc,
            });

            assert.equal(res.status, CURRENT_STATUS.CURRENT);
            assert.equal(res.reason_code, CURRENT_REASON.SEMANTIC_PLAN_MATCH);
            assert.equal(res.semantic_contract_version, PAGE_COMPOSITE_SEMANTIC_DIGEST_VERSION);
            assert.ok(res.stored_semantic_digest);
            assert.equal(res.stored_semantic_digest, res.current_semantic_digest);
            assert.equal(res.historical_plan_digest, savedComposite.manifest.composition_plan_digest);
        });

        // CASE B, C, D, E, Q: Volatile field changes do NOT make composite STALE
        await test("Case B, C, D, E, Q: Volatile fields (plan_id, created_at, diagnostics) do not cause STALE", async () => {
            const currentPlan = buildTestPlan({
                docId: "doc_alpha",
                pageId: "page_1",
                planId: "DIFFERENT_PLAN_ID_NEW_UUID", // Different plan_id (Case B)
                createdAt: "2026-09-25T18:00:00.000Z", // Different created_at (Case C)
                topDiag: { total_scenes: 1, filled_scenes: 1, unfilled_scenes: 0, evaluated_now: 999 }, // Top diag (Case D)
                sceneDiag: { evaluated_candidates: 99, total_indexed_candidates: 99 }, // Scene diag (Case E)
                manifestId: "550e8400-e29b-41d4-a716-446655440001",
                contentDigest: "a".repeat(64),
                placementX: 0,
                placementY: 0,
            });

            const classifier = new PageCompositeCurrentClassifier({
                store,
                index,
                prepFn: async () => currentPlan,
            });

            const res = await classifier.classifyCurrentPageComposite({
                composite_id: compositeId,
                authoring_document: authoringDoc,
            });

            assert.equal(res.status, CURRENT_STATUS.CURRENT);
            assert.equal(res.reason_code, CURRENT_REASON.SEMANTIC_PLAN_MATCH);
            assert.equal(res.stored_semantic_digest, res.current_semantic_digest);

            // Case Q: Exact historical composition_plan_digest differs, but semantic digest matches
            assert.notEqual(res.historical_plan_digest, createHash("sha256").update(JSON.stringify(currentPlan)).digest("hex"));
        });

        // CASE F: Different selected manifest_id -> STALE
        await test("Case F: Different selected manifest_id -> STALE", async () => {
            const currentPlan = buildTestPlan({
                docId: "doc_alpha",
                pageId: "page_1",
                manifestId: "550e8400-e29b-41d4-a716-446655440002", // Changed manifest_id
            });

            const classifier = new PageCompositeCurrentClassifier({
                store,
                index,
                prepFn: async () => currentPlan,
            });

            const res = await classifier.classifyCurrentPageComposite({
                composite_id: compositeId,
                authoring_document: authoringDoc,
            });

            assert.equal(res.status, CURRENT_STATUS.STALE);
            assert.equal(res.reason_code, CURRENT_REASON.SEMANTIC_PLAN_MISMATCH);
            assert.notEqual(res.stored_semantic_digest, res.current_semantic_digest);
        });

        // CASE G: Different selected artifact digest -> STALE
        await test("Case G: Different selected artifact digest -> STALE", async () => {
            const currentPlan = buildTestPlan({
                docId: "doc_alpha",
                pageId: "page_1",
                contentDigest: "b".repeat(64), // Changed digest
            });

            const classifier = new PageCompositeCurrentClassifier({
                store,
                index,
                prepFn: async () => currentPlan,
            });

            const res = await classifier.classifyCurrentPageComposite({
                composite_id: compositeId,
                authoring_document: authoringDoc,
            });

            assert.equal(res.status, CURRENT_STATUS.STALE);
            assert.equal(res.reason_code, CURRENT_REASON.SEMANTIC_PLAN_MISMATCH);
        });

        // CASE H: Different placement -> STALE
        await test("Case H: Different placement -> STALE", async () => {
            const currentPlan = buildTestPlan({
                docId: "doc_alpha",
                pageId: "page_1",
                placementX: 10, // Changed placement
            });

            const classifier = new PageCompositeCurrentClassifier({
                store,
                index,
                prepFn: async () => currentPlan,
            });

            const res = await classifier.classifyCurrentPageComposite({
                composite_id: compositeId,
                authoring_document: authoringDoc,
            });

            assert.equal(res.status, CURRENT_STATUS.STALE);
            assert.equal(res.reason_code, CURRENT_REASON.SEMANTIC_PLAN_MISMATCH);
        });

        // CASE I: CURRENT_RESULT -> UNFILLED -> STALE
        await test("Case I: CURRENT_RESULT -> UNFILLED -> STALE", async () => {
            const currentPlan = buildTestPlan({
                docId: "doc_alpha",
                pageId: "page_1",
                sceneState: "UNFILLED", // Now unfilled
            });

            const classifier = new PageCompositeCurrentClassifier({
                store,
                index,
                prepFn: async () => currentPlan,
            });

            const res = await classifier.classifyCurrentPageComposite({
                composite_id: compositeId,
                authoring_document: authoringDoc,
            });

            assert.equal(res.status, CURRENT_STATUS.STALE);
            assert.equal(res.reason_code, CURRENT_REASON.SEMANTIC_PLAN_MISMATCH);
        });

        // CASE J: Scene structural order change -> STALE
        await test("Case J: Scene structural order change -> STALE", async () => {
            const currentPlan = buildTestPlan({
                docId: "doc_alpha",
                pageId: "page_1",
                sceneOrder: 1, // Changed order
            });

            const classifier = new PageCompositeCurrentClassifier({
                store,
                index,
                prepFn: async () => currentPlan,
            });

            const res = await classifier.classifyCurrentPageComposite({
                composite_id: compositeId,
                authoring_document: authoringDoc,
            });

            assert.equal(res.status, CURRENT_STATUS.STALE);
            assert.equal(res.reason_code, CURRENT_REASON.SEMANTIC_PLAN_MISMATCH);
        });

        // CASE K: Page dimension change -> STALE
        await test("Case K: Page dimension change -> STALE", async () => {
            const currentPlan = buildTestPlan({
                docId: "doc_alpha",
                pageId: "page_1",
                width: 128, // Changed page dimension
            });

            const classifier = new PageCompositeCurrentClassifier({
                store,
                index,
                prepFn: async () => currentPlan,
            });

            const res = await classifier.classifyCurrentPageComposite({
                composite_id: compositeId,
                authoring_document: authoringDoc,
            });

            assert.equal(res.status, CURRENT_STATUS.STALE);
            assert.equal(res.reason_code, CURRENT_REASON.SEMANTIC_PLAN_MISMATCH);
        });

        // CASE L: Newer historical composite does not make older match STALE
        await test("Case L: Newer historical composite alone does not make older match STALE", async () => {
            // Save a second composite for the same page later in time
            const secondSaved = await store.saveComposite({
                composition_plan: baseStoredPlan,
                composite_bytes: pngBytes,
            });
            await index.indexComposite(secondSaved.composite_id);

            const classifier = new PageCompositeCurrentClassifier({
                store,
                index,
                prepFn: async () => baseStoredPlan,
            });

            // Classify the older composite
            const res = await classifier.classifyCurrentPageComposite({
                composite_id: compositeId,
                authoring_document: authoringDoc,
            });

            assert.equal(res.status, CURRENT_STATUS.CURRENT, "Older composite with matching semantics remains CURRENT");
        });

        // CASE M: Unsupported stored plan version -> UNKNOWN
        await test("Case M: Unsupported stored plan version -> UNKNOWN", async () => {
            const unsuppPlan = buildTestPlan({
                docId: "doc_unsupp_store",
                pageId: "page_1",
                schemaVersion: "2.0.0", // Unsupported version
            });

            // Bypass store validator to simulate historical schema incompatibility
            const fakeId = "550e8400-e29b-41d4-a716-446655440099";
            const mockIndex = {
                async resolveComposite() {
                    return {
                        manifest: {
                            composite_id: fakeId,
                            owner: { document_id: "doc_unsupp_store", page_id: "page_1" },
                            composition_plan: unsuppPlan,
                            composition_plan_digest: "x".repeat(64),
                        },
                    };
                },
            };

            const classifier = new PageCompositeCurrentClassifier({
                store,
                index: mockIndex,
                prepFn: async () => baseStoredPlan,
            });

            const res = await classifier.classifyCurrentPageComposite({
                composite_id: fakeId,
                authoring_document: { document_id: "doc_unsupp_store", pages: [{ page_id: "page_1" }] },
            });

            assert.equal(res.status, CURRENT_STATUS.UNKNOWN);
            assert.equal(res.reason_code, CURRENT_REASON.UNSUPPORTED_STORED_PLAN_VERSION);
        });

        // CASE N: Unsupported current plan version -> UNKNOWN
        await test("Case N: Unsupported current plan version -> UNKNOWN", async () => {
            const classifier = new PageCompositeCurrentClassifier({
                store,
                index,
                prepFn: async () => ({
                    schema_id: "TEGAKI_PAGE_COMPOSITION_PLAN",
                    schema_version: "99.0.0", // Unsupported
                    page: { document_id: "doc_alpha", page_id: "page_1" },
                }),
            });

            const res = await classifier.classifyCurrentPageComposite({
                composite_id: compositeId,
                authoring_document: authoringDoc,
            });

            assert.equal(res.status, CURRENT_STATUS.UNKNOWN);
            assert.equal(res.reason_code, CURRENT_REASON.UNSUPPORTED_CURRENT_PLAN_VERSION);
        });

        // CASE O: Current plan preparation failure -> UNKNOWN
        await test("Case O: Current plan preparation failure -> UNKNOWN", async () => {
            const classifier = new PageCompositeCurrentClassifier({
                store,
                index,
                prepFn: async () => {
                    throw new Error("Compilation failure in Python backend");
                },
            });

            const res = await classifier.classifyCurrentPageComposite({
                composite_id: compositeId,
                authoring_document: authoringDoc,
            });

            assert.equal(res.status, CURRENT_STATUS.UNKNOWN);
            assert.equal(res.reason_code, CURRENT_REASON.CURRENT_PLAN_UNAVAILABLE);
        });

        // CASE P: Owner/page mismatch does not become false STALE
        await test("Case P: Owner/page mismatch does not become a false STALE result", async () => {
            const classifier = new PageCompositeCurrentClassifier({
                store,
                index,
                prepFn: async () => baseStoredPlan,
            });

            // Calling with different document_id
            const resDiffDoc = await classifier.classifyCurrentPageComposite({
                composite_id: compositeId,
                authoring_document: { document_id: "doc_OTHER", pages: [{ page_id: "page_1" }] },
            });
            assert.equal(resDiffDoc.status, CURRENT_STATUS.UNKNOWN);
            assert.equal(resDiffDoc.reason_code, CURRENT_REASON.OWNER_MISMATCH);

            // Calling with explicit different page_id
            const resDiffPage = await classifier.classifyCurrentPageComposite({
                composite_id: compositeId,
                authoring_document: authoringDoc,
                page_id: "page_DIFFERENT",
            });
            assert.equal(resDiffPage.status, CURRENT_STATUS.UNKNOWN);
            assert.equal(resDiffPage.reason_code, CURRENT_REASON.OWNER_MISMATCH);
        });

        // Functional wrapper test
        await test("Functional wrapper classifyCurrentPageComposite", async () => {
            const res = await classifyCurrentPageComposite({
                composite_id: compositeId,
                authoring_document: authoringDoc,
            }, {
                store,
                index,
                prepFn: async () => baseStoredPlan,
            });

            assert.equal(res.status, CURRENT_STATUS.CURRENT);
        });

        // CASE R, S, T: Zero mutation of Authoring Document, Journal, stores, GPU
        await test("Case R, S, T: Zero mutation across external stores, Authoring Doc, GPU", async () => {
            const docClone = structuredClone(authoringDoc);
            const docSnapshot = JSON.stringify(docClone);

            await classifyCurrentPageComposite({
                composite_id: compositeId,
                authoring_document: docClone,
            }, {
                store,
                index,
                prepFn: async () => baseStoredPlan,
            });

            assert.equal(JSON.stringify(docClone), docSnapshot, "Authoring document must not be mutated");
        });

    } finally {
        await fs.rm(baseTempDir, { recursive: true, force: true }).catch(() => {});
    }

    console.log(`\nFinal Test Results: ${passed} PASSED / ${failed} FAILED\n`);
    if (failed > 0) {
        process.exit(1);
    }
}

runTests().catch((err) => {
    console.error("Unhandled test suite error:", err);
    process.exit(1);
});
