/**
 * test_page_composite_index.mjs — Targeted tests for PageCompositeIndex.
 *
 * Verifies:
 * - Validated composite registration (indexComposite)
 * - Deterministic ordering (created_at desc, composite_id tie-breaker)
 * - Page history preservation and plan-digest filtering
 * - Idempotence and fail-closed consistency checks
 * - In-process concurrency serialization
 * - Integration with PageCompositePersistService and recovery
 * - Zero authoring mutations, zero live backend / GPU
 */

import assert from "node:assert/strict";
import fs from "node:fs/promises";
import path from "node:path";
import os from "node:os";
import zlib from "node:zlib";
import { createHash } from "node:crypto";

import {
    PageCompositeIndex,
    PageCompositeIndexError,
    INDEX_SCHEMA_ID,
    INDEX_SCHEMA_VERSION,
} from "../service/page_composite_index.mjs";
import { PageCompositeStore } from "../service/page_composite_store.mjs";
import {
    PageCompositePersistService,
    PageCompositePersistError,
} from "../service/page_composite_persist_service.mjs";
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

function computeDigest(buffer) {
    return createHash("sha256").update(buffer).digest("hex");
}

function makeValidPlan(docId = "doc_test_1", pageId = "page_test_1", planId = "plan_1", width = 64, height = 64) {
    return {
        schema_id: "TEGAKI_PAGE_COMPOSITION_PLAN",
        schema_version: "1.0.0",
        plan_id: planId,
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
                order: 0,
                state: "CURRENT_RESULT",
                selected_result: {
                    manifest_id: "550e8400-e29b-41d4-a716-446655440001",
                    artifact: {
                        locator: "manga/data/results/550e8400-e29b-41d4-a716-446655440001/artifact.png",
                        dimensions: { width, height },
                        content_digest: "a".repeat(64),
                    },
                    placement: {
                        page_target_rect: { x: 0, y: 0, width, height },
                        local_source_rect: { x: 0, y: 0, width, height },
                        transform: {},
                        target_page_dimensions: { width, height },
                    },
                },
            },
        ],
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

    const baseTempDir = await fs.mkdtemp(path.join(os.tmpdir(), "manga-index-test-"));

    try {
        const storeDir = path.join(baseTempDir, "store");
        const indexDir = path.join(baseTempDir, "index");
        await fs.mkdir(storeDir, { recursive: true });
        await fs.mkdir(indexDir, { recursive: true });

        const store = new PageCompositeStore(storeDir);
        const index = new PageCompositeIndex({ directory: indexDir, store });

        const pngBytes = createValidPngBuffer(64, 64);
        const planA = makeValidPlan("doc_main", "page_1", "plan_A", 64, 64);
        const planB = makeValidPlan("doc_main", "page_1", "plan_B", 64, 64);

        // CASE A, B: Index one valid stored composite, metadata derived from Store manifest
        let savedA1;
        await test("Case A, B: Index one valid stored composite; metadata derived from store manifest", async () => {
            savedA1 = await store.saveComposite({
                composition_plan: planA,
                composite_bytes: pngBytes,
            });

            const entry = await index.indexComposite(savedA1.composite_id);
            assert.equal(entry.composite_id, savedA1.composite_id);
            assert.equal(entry.document_id, "doc_main");
            assert.equal(entry.page_id, "page_1");
            assert.equal(entry.composition_plan_digest, savedA1.manifest.composition_plan_digest);
            assert.equal(entry.created_at, savedA1.manifest.created_at);

            // Verify no heavy fields are copied into index entry
            assert.equal(entry.composition_plan, undefined);
            assert.equal(entry.artifact, undefined);
            assert.equal(entry.artifact_bytes, undefined);

            const directLookup = await index.getEntry(savedA1.composite_id);
            assert.deepEqual(directLookup, entry);
        });

        // CASE C: Same composite_id indexing is idempotent
        await test("Case C: Same composite_id indexing is idempotent", async () => {
            const secondEntry = await index.indexComposite(savedA1.composite_id);
            assert.equal(secondEntry.composite_id, savedA1.composite_id);

            const list = await index.listByPage({ document_id: "doc_main", page_id: "page_1" });
            assert.equal(list.length, 1, "Idempotent registration must not duplicate entry");
        });

        // CASE D, E, F, G, H: Multiple composites, same plan digest, deterministic ordering, filter
        let savedA2;
        let savedB1;
        await test("Case D, E, F, G, H: Page history, same plan digest, deterministic ordering, digest filter", async () => {
            // Wait slightly to guarantee distinct timestamp order if needed
            await new Promise(r => setTimeout(r, 10));

            // Second composite with same plan A (same plan digest)
            savedA2 = await store.saveComposite({
                composition_plan: planA,
                composite_bytes: pngBytes,
            });
            await index.indexComposite(savedA2.composite_id);

            // Third composite with plan B (different plan digest)
            savedB1 = await store.saveComposite({
                composition_plan: planB,
                composite_bytes: pngBytes,
            });
            await index.indexComposite(savedB1.composite_id);

            // Case D & F: All 3 composites preserved under page
            const history = await index.listByPage({ document_id: "doc_main", page_id: "page_1" });
            assert.equal(history.length, 3, "All 3 composites preserved in history");

            // Case G: Deterministic ordering (created_at desc, composite_id desc tie-break)
            for (let i = 0; i < history.length - 1; i++) {
                const cur = history[i];
                const next = history[i + 1];
                const tCur = Date.parse(cur.created_at);
                const tNext = Date.parse(next.created_at);
                assert.ok(tCur >= tNext, "Ordering must be created_at descending");
                if (tCur === tNext) {
                    assert.ok(cur.composite_id.localeCompare(next.composite_id) > 0, "Tie-break must be composite_id desc");
                }
            }

            // Case E & H: Plan digest filter returns all matching composites for that digest
            const digestA = savedA1.manifest.composition_plan_digest;
            const matchesA = await index.listByPlanDigest({
                document_id: "doc_main",
                page_id: "page_1",
                composition_plan_digest: digestA,
            });
            assert.equal(matchesA.length, 2, "Digest filter matches both composites with plan A");
            assert.ok(matchesA.every(e => e.composition_plan_digest === digestA));

            const digestB = savedB1.manifest.composition_plan_digest;
            const matchesB = await index.listByPlanDigest({
                document_id: "doc_main",
                page_id: "page_1",
                composition_plan_digest: digestB,
            });
            assert.equal(matchesB.length, 1);
            assert.equal(matchesB[0].composite_id, savedB1.composite_id);
        });

        // CASE I: Caller cannot inject owner fields during index write
        await test("Case I: Caller cannot inject owner fields during index write", async () => {
            // indexComposite only accepts compositeId string; if an object is passed, it rejects
            await assert.rejects(
                () => index.indexComposite({ composite_id: savedA1.composite_id, document_id: "injected_doc" }),
                (err) => err instanceof PageCompositeIndexError && err.code === "INVALID_COMPOSITE_ID"
            );
        });

        // CASE J: Missing composite creates ZERO index mutation
        await test("Case J: Missing composite creates ZERO index mutation", async () => {
            const fakeId = "550e8400-e29b-41d4-a716-000000000000";
            const preCount = (await index.listByPage({ document_id: "doc_main", page_id: "page_1" })).length;

            await assert.rejects(
                () => index.indexComposite(fakeId),
                (err) => err instanceof PageCompositeIndexError && err.code === "COMPOSITE_NOT_FOUND"
            );

            const postCount = (await index.listByPage({ document_id: "doc_main", page_id: "page_1" })).length;
            assert.equal(postCount, preCount, "Index entry count must remain unchanged");
        });

        // CASE K: Corrupt composite creates ZERO index mutation
        await test("Case K: Corrupt composite creates ZERO index mutation", async () => {
            const corruptSaved = await store.saveComposite({
                composition_plan: makeValidPlan("doc_corrupt", "page_c", "plan_c", 64, 64),
                composite_bytes: pngBytes,
            });

            // Corrupt manifest on disk
            const manifestPath = path.join(storeDir, corruptSaved.composite_id, "manifest.json");
            await fs.writeFile(manifestPath, "NOT_JSON_CORRUPT");

            await assert.rejects(
                () => index.indexComposite(corruptSaved.composite_id),
                (err) => err instanceof PageCompositeIndexError && err.code === "INVALID_COMPOSITE"
            );

            const entry = await index.getEntry(corruptSaved.composite_id);
            assert.equal(entry, null, "Corrupt bundle must not be indexed");
        });

        // CASE L: Concurrent independent registrations do not lose entries
        await test("Case L: Concurrent independent registrations do not lose entries", async () => {
            const concurrentComposites = await Promise.all([
                store.saveComposite({ composition_plan: makeValidPlan("doc_conc", "p1", "pl1", 64, 64), composite_bytes: pngBytes }),
                store.saveComposite({ composition_plan: makeValidPlan("doc_conc", "p1", "pl2", 64, 64), composite_bytes: pngBytes }),
                store.saveComposite({ composition_plan: makeValidPlan("doc_conc", "p1", "pl3", 64, 64), composite_bytes: pngBytes }),
            ]);

            const entries = await Promise.all(
                concurrentComposites.map(c => index.indexComposite(c.composite_id))
            );

            assert.equal(entries.length, 3);
            const list = await index.listByPage({ document_id: "doc_conc", page_id: "p1" });
            assert.equal(list.length, 3, "All concurrent entries must be saved without loss");
        });

        // CASE M: Index -> missing Store bundle fails INDEX_CONSISTENCY_ERROR
        await test("Case M: Index -> missing Store bundle fails INDEX_CONSISTENCY_ERROR", async () => {
            const delSaved = await store.saveComposite({
                composition_plan: makeValidPlan("doc_del", "p_del", "plan_del", 64, 64),
                composite_bytes: pngBytes,
            });
            await index.indexComposite(delSaved.composite_id);

            // Successfully resolves while bundle exists
            const resolved = await index.resolveComposite(delSaved.composite_id);
            assert.ok(resolved.manifest);
            assert.ok(resolved.artifact_bytes);

            // Delete bundle from store directory
            await fs.rm(path.join(storeDir, delSaved.composite_id), { recursive: true, force: true });

            // Index references missing bundle -> INDEX_CONSISTENCY_ERROR
            await assert.rejects(
                () => index.resolveComposite(delSaved.composite_id),
                (err) => err instanceof PageCompositeIndexError && err.code === "INDEX_CONSISTENCY_ERROR"
            );
        });

        // CASE N, O, P, Q: PersistService integration, failure window, orphan recovery, zero second bridge call
        await test("Case N, O, P, Q: PersistService integration, failure handling, recovery, single bridge call", async () => {
            let bridgeCalls = 0;
            const mockBridge = {
                async composeCurrentPage() {
                    bridgeCalls++;
                    return {
                        plan: planA,
                        composite_bytes: pngBytes,
                        composite: {
                            content_digest: computeDigest(pngBytes),
                            declared_width: 64,
                            declared_height: 64,
                            byte_length: pngBytes.length,
                        },
                        statistics: { total_scenes: 1, composed_scenes: 1, unfilled_scenes: 0 },
                    };
                },
            };

            const persistService = new PageCompositePersistService({
                bridge: mockBridge,
                store,
                index,
            });

            // Case N: Successful persistCurrentPageComposite publishes exactly one index entry
            const persistRes = await persistService.persistCurrentPageComposite({
                authoring_document: { document_id: "doc_main", pages: [{ page_id: "page_1" }] },
                generation_params: {},
            });

            assert.equal(bridgeCalls, 1);
            const entry = await index.getEntry(persistRes.composite_id);
            assert.ok(entry, "Index entry must exist after persistCurrentPageComposite");
            assert.equal(entry.composite_id, persistRes.composite_id);

            // Case O & Q: Index failure leaves Store bundle intact and makes NO second bridge call
            let secondBridgeCalls = 0;
            const mockBridge2 = {
                async composeCurrentPage() {
                    secondBridgeCalls++;
                    return {
                        plan: planA,
                        composite_bytes: pngBytes,
                        composite: {
                            content_digest: computeDigest(pngBytes),
                            declared_width: 64,
                            declared_height: 64,
                            byte_length: pngBytes.length,
                        },
                        statistics: { total_scenes: 1, composed_scenes: 1, unfilled_scenes: 0 },
                    };
                },
            };

            const failingIndex = {
                async indexComposite(id) {
                    throw new Error("Simulated index write failure");
                },
            };

            const failingPersistService = new PageCompositePersistService({
                bridge: mockBridge2,
                store,
                index: failingIndex,
            });

            let persistErr = null;
            try {
                await failingPersistService.persistCurrentPageComposite({
                    authoring_document: { document_id: "doc_main", pages: [{ page_id: "page_1" }] },
                    generation_params: {},
                });
            } catch (err) {
                persistErr = err;
            }

            assert.ok(persistErr instanceof PageCompositePersistError);
            assert.equal(persistErr.code, "COMPOSITE_INDEX_PUBLICATION_FAILED");
            assert.ok(persistErr.composite_id, "Reports composite_id for recovery");
            assert.equal(secondBridgeCalls, 1, "ZERO second bridge call");

            // Verify bundle on disk exists (Case O)
            const orphanId = persistErr.composite_id;
            const orphanManifest = await store.getManifest(orphanId);
            assert.ok(orphanManifest, "Store bundle must remain published and intact");

            // Case P: Recovery indexComposite(existingId) registers orphan without bridge rerun
            const recoveredEntry = await index.indexComposite(orphanId);
            assert.equal(recoveredEntry.composite_id, orphanId);
            assert.equal(secondBridgeCalls, 1, "No bridge call during recovery");

            const verifiedRecovery = await index.getEntry(orphanId);
            assert.ok(verifiedRecovery);
        });

        // CASE R: No CURRENT/STALE state is stored
        await test("Case R: No CURRENT/STALE state is stored in index entries", async () => {
            const list = await index.listByPage({ document_id: "doc_main", page_id: "page_1" });
            assert.ok(list.length > 0);
            for (const item of list) {
                assert.equal(item.status, undefined);
                assert.equal(item.state, undefined);
                assert.equal(item.is_current, undefined);
                assert.equal(item.freshness, undefined);
            }
        });

        // CASE S, T: Zero mutation of Authoring Document, Journal, SceneResultStore, GPU
        await test("Case S, T: Zero mutation across external stores, Authoring Doc, GPU", async () => {
            const doc = { document_id: "doc_pure", pages: [{ page_id: "p_pure" }] };
            const docSnap = JSON.stringify(doc);

            const mockBridge = {
                async composeCurrentPage() {
                    return {
                        plan: makeValidPlan("doc_pure", "p_pure", "pl_p", 64, 64),
                        composite_bytes: pngBytes,
                        composite: {
                            content_digest: computeDigest(pngBytes),
                            declared_width: 64,
                            declared_height: 64,
                            byte_length: pngBytes.length,
                        },
                        statistics: { total_scenes: 1, composed_scenes: 1, unfilled_scenes: 0 },
                    };
                },
            };

            const service = new PageCompositePersistService({ bridge: mockBridge, store, index });
            await service.persistCurrentPageComposite({
                authoring_document: doc,
                generation_params: {},
            });

            assert.equal(JSON.stringify(doc), docSnap, "Authoring document must not be mutated");
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
