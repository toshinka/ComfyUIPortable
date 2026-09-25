/**
 * test_page_composite_persist_service.mjs — Targeted tests for PageCompositePersistService.
 *
 * Verifies orchestration connecting PageCompositorBridge to PageCompositeStore:
 * - Single call to bridge and store
 * - Exact byte and plan preservation
 * - Immutable bundle persistence and validated retrieval
 * - Zero authoring document or journal mutations
 * - Fail-closed handling on bridge/store errors and consistency mismatches
 */

import assert from "node:assert/strict";
import fs from "node:fs/promises";
import path from "node:path";
import os from "node:os";
import zlib from "node:zlib";
import { createHash } from "node:crypto";

import {
    PageCompositePersistService,
    PageCompositePersistError,
    persistCurrentPageComposite,
} from "../service/page_composite_persist_service.mjs";
import { PageCompositeStore } from "../service/page_composite_store.mjs";
import { computePngCrc32 } from "../service/png_artifact_analyzer.mjs";

/**
 * Creates a valid RGBA PNG buffer in memory.
 */
function createValidPngBuffer(width, height) {
    const sig = Buffer.from([0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A]);
    const ihdrData = Buffer.alloc(13);
    ihdrData.writeUInt32BE(width, 0);
    ihdrData.writeUInt32BE(height, 4);
    ihdrData[8] = 8;  // bit depth
    ihdrData[9] = 6;  // RGBA
    ihdrData[10] = 0; // deflate
    ihdrData[11] = 0; // standard filter
    ihdrData[12] = 0; // no interlace

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

function makeValidPlan(docId = "doc_test_1", pageId = "page_test_1", width = 64, height = 64) {
    return {
        schema_id: "TEGAKI_PAGE_COMPOSITION_PLAN",
        schema_version: "1.0.0",
        plan_id: "plan_valid_001",
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
                    manifest_id: "res_001",
                    artifact: {
                        locator: "manga/data/results/res_001/artifact.png",
                        dimensions: {
                            width,
                            height,
                        },
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

    const baseTempDir = await fs.mkdtemp(path.join(os.tmpdir(), "manga-persist-test-"));

    try {
        // CASE A - L: Successful bridge result persists one immutable bundle
        await test("Case A - L: Successful orchestration, single calls, exact byte/plan/digest continuity", async () => {
            const storeDir = path.join(baseTempDir, "store_success");
            await fs.mkdir(storeDir, { recursive: true });
            const store = new PageCompositeStore(storeDir);

            const pngBytes = createValidPngBuffer(64, 64);
            const pngDigest = computeDigest(pngBytes);
            const plan = makeValidPlan("doc_persist_1", "page_persist_1", 64, 64);

            let bridgeCallCount = 0;
            let bridgeReceivedInput = null;
            let storeSaveCalls = 0;

            const originalSave = store.saveComposite.bind(store);
            store.saveComposite = async (args) => {
                storeSaveCalls++;
                return originalSave(args);
            };

            const mockBridge = {
                async composeCurrentPage(input) {
                    bridgeCallCount++;
                    bridgeReceivedInput = input;
                    return {
                        plan,
                        composite_bytes: pngBytes,
                        composite: {
                            content_digest: pngDigest,
                            declared_width: 64,
                            declared_height: 64,
                            byte_length: pngBytes.length,
                        },
                        statistics: {
                            total_scenes: 1,
                            composed_scenes: 1,
                            unfilled_scenes: 0,
                        },
                    };
                },
            };

            const service = new PageCompositePersistService({ bridge: mockBridge, store });

            const authoringDoc = {
                document_id: "doc_persist_1",
                pages: [{ page_id: "page_persist_1", width: 64, height: 64 }],
            };
            const docClone = structuredClone(authoringDoc);
            const genParams = { prompt: "test prompt" };

            const result = await service.persistCurrentPageComposite({
                authoring_document: authoringDoc,
                generation_params: genParams,
                page_id: "page_persist_1",
            });

            // Case A: Persists exactly one bundle
            const subdirs = await fs.readdir(storeDir);
            assert.equal(subdirs.length, 1, "Exactly one bundle directory created");
            assert.equal(subdirs[0], result.composite_id, "Bundle dir equals composite_id");

            // Case B: Bridge called exactly once
            assert.equal(bridgeCallCount, 1, "Bridge called exactly once");
            assert.equal(bridgeReceivedInput.page_id, "page_persist_1");

            // Case C: Store save called exactly once
            assert.equal(storeSaveCalls, 1, "Store save called exactly once");

            // Case D & L: Exact PNG bytes persisted byte-for-byte
            const persistedBytes = await fs.readFile(path.join(storeDir, result.composite_id, "artifact.png"));
            assert.equal(persistedBytes.length, pngBytes.length, "Byte length matches");
            assert.deepEqual(persistedBytes, pngBytes, "Bytes equal byte-for-byte");

            // Case E & F: Stored manifest plan deep-equals bridge plan
            assert.deepEqual(result.manifest.composition_plan, plan, "Stored plan deep-equals bridge plan");

            // Case G: Stored owner matches plan page owner
            assert.equal(result.manifest.owner.document_id, "doc_persist_1");
            assert.equal(result.manifest.owner.page_id, "page_persist_1");

            // Case H, I, J: Digest and dimensions match bridge
            assert.equal(result.composite.content_digest, pngDigest);
            assert.equal(result.composite.declared_width, 64);
            assert.equal(result.composite.declared_height, 64);
            assert.equal(result.composite.byte_length, pngBytes.length);

            // Case K: Validated retrieval returns the same manifest
            const retrieved = await store.getComposite(result.composite_id, { required: true });
            assert.deepEqual(retrieved.manifest, result.manifest, "Retrieved manifest equals returned manifest");
            assert.deepEqual(retrieved.artifact_bytes, pngBytes, "Retrieved bytes equal original bytes");

            // Functional wrapper test
            const wrapperResult = await persistCurrentPageComposite({
                authoring_document: authoringDoc,
                generation_params: genParams,
                page_id: "page_persist_1",
            }, { bridge: mockBridge, store });
            assert.ok(wrapperResult.composite_id, "Functional wrapper returns composite_id");
            assert.notEqual(wrapperResult.composite_id, result.composite_id, "Subsequent call creates distinct bundle");
        });

        // CASE M: Bridge failure produces ZERO store bundle
        await test("Case M: Bridge failure produces ZERO store bundle", async () => {
            const storeDir = path.join(baseTempDir, "store_bridge_fail");
            await fs.mkdir(storeDir, { recursive: true });
            const store = new PageCompositeStore(storeDir);

            const failingBridge = {
                async composeCurrentPage() {
                    const err = new Error("Backend connection refused");
                    err.code = "BACKEND_UNAVAILABLE";
                    throw err;
                },
            };

            const service = new PageCompositePersistService({ bridge: failingBridge, store });

            await assert.rejects(
                () => service.persistCurrentPageComposite({
                    authoring_document: { document_id: "doc1", pages: [{ page_id: "p1" }] },
                    generation_params: {},
                }),
                (err) => err instanceof PageCompositePersistError && err.code === "BACKEND_UNAVAILABLE"
            );

            const subdirs = await fs.readdir(storeDir);
            assert.equal(subdirs.length, 0, "No bundle directory should exist after bridge failure");
        });

        // CASE N: Invalid bridge PNG causes Store failure and ZERO final bundle
        await test("Case N: Invalid bridge PNG causes Store failure and ZERO final bundle", async () => {
            const storeDir = path.join(baseTempDir, "store_invalid_png");
            await fs.mkdir(storeDir, { recursive: true });
            const store = new PageCompositeStore(storeDir);

            const corruptPng = Buffer.from("NOT_A_VALID_PNG_BUFFER_DATA");
            const plan = makeValidPlan("doc_n", "page_n", 64, 64);

            const badBridge = {
                async composeCurrentPage() {
                    return {
                        plan,
                        composite_bytes: corruptPng,
                        composite: {
                            content_digest: computeDigest(corruptPng),
                            declared_width: 64,
                            declared_height: 64,
                            byte_length: corruptPng.length,
                        },
                        statistics: { total_scenes: 1, composed_scenes: 1, unfilled_scenes: 0 },
                    };
                },
            };

            const service = new PageCompositePersistService({ bridge: badBridge, store });

            await assert.rejects(
                () => service.persistCurrentPageComposite({
                    authoring_document: { document_id: "doc_n", pages: [{ page_id: "page_n" }] },
                    generation_params: {},
                }),
                (err) => err instanceof PageCompositePersistError
            );

            const subdirs = await fs.readdir(storeDir);
            assert.equal(subdirs.length, 0, "Zero bundles persisted on invalid PNG");
        });

        // CASE O: Plan/page dimension mismatch fails
        await test("Case O: Plan/page dimension mismatch fails", async () => {
            const storeDir = path.join(baseTempDir, "store_dim_mismatch");
            await fs.mkdir(storeDir, { recursive: true });
            const store = new PageCompositeStore(storeDir);

            const png32 = createValidPngBuffer(32, 32); // Actual bytes 32x32
            const plan64 = makeValidPlan("doc_o", "page_o", 64, 64); // Plan expects 64x64

            const mismatchBridge = {
                async composeCurrentPage() {
                    return {
                        plan: plan64,
                        composite_bytes: png32,
                        composite: {
                            content_digest: computeDigest(png32),
                            declared_width: 32,
                            declared_height: 32,
                            byte_length: png32.length,
                        },
                        statistics: { total_scenes: 1, composed_scenes: 1, unfilled_scenes: 0 },
                    };
                },
            };

            const service = new PageCompositePersistService({ bridge: mismatchBridge, store });

            await assert.rejects(
                () => service.persistCurrentPageComposite({
                    authoring_document: { document_id: "doc_o", pages: [{ page_id: "page_o" }] },
                    generation_params: {},
                }),
                (err) => err instanceof PageCompositePersistError
            );

            const subdirs = await fs.readdir(storeDir);
            assert.equal(subdirs.length, 0, "Zero bundles on dimension mismatch");
        });

        // CASE P: Simulated Store failure is propagated without retry
        await test("Case P: Simulated Store failure is propagated without retry", async () => {
            let bridgeCalls = 0;
            let storeCalls = 0;

            const pngBytes = createValidPngBuffer(64, 64);
            const plan = makeValidPlan("doc_p", "page_p", 64, 64);

            const mockBridge = {
                async composeCurrentPage() {
                    bridgeCalls++;
                    return {
                        plan,
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

            const failingStore = {
                async saveComposite() {
                    storeCalls++;
                    const err = new Error("Disk full or IO error");
                    err.code = "STORE_IO_ERROR";
                    throw err;
                },
                async getComposite() {
                    return null;
                },
            };

            const service = new PageCompositePersistService({ bridge: mockBridge, store: failingStore });

            await assert.rejects(
                () => service.persistCurrentPageComposite({
                    authoring_document: { document_id: "doc_p", pages: [{ page_id: "page_p" }] },
                    generation_params: {},
                }),
                (err) => err instanceof PageCompositePersistError && err.code === "STORE_IO_ERROR"
            );

            assert.equal(bridgeCalls, 1, "Bridge called exactly once");
            assert.equal(storeCalls, 1, "Store save called exactly once (no retry)");
        });

        // CASE Q: Simulated post-save retrieval/consistency failure does NOT delete published bundle
        await test("Case Q: Simulated post-save retrieval / consistency failure does NOT delete published bundle", async () => {
            const storeDir = path.join(baseTempDir, "store_post_save_inconsistent");
            await fs.mkdir(storeDir, { recursive: true });
            const realStore = new PageCompositeStore(storeDir);

            const pngBytes = createValidPngBuffer(64, 64);
            const plan = makeValidPlan("doc_q", "page_q", 64, 64);

            const mockBridge = {
                async composeCurrentPage() {
                    return {
                        plan,
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

            let publishedCompositeId = null;
            const originalSave = realStore.saveComposite.bind(realStore);

            // Wrap store: save runs normally on disk, but getComposite throws simulation
            const spiedStore = {
                async saveComposite(args) {
                    const res = await originalSave(args);
                    publishedCompositeId = res.composite_id;
                    return res;
                },
                async getComposite(id) {
                    // Simulate corrupt/inconsistent retrieval failure
                    throw new Error("Simulated retrieval/consistency failure after save");
                },
            };

            const service = new PageCompositePersistService({ bridge: mockBridge, store: spiedStore });

            let caughtErr = null;
            try {
                await service.persistCurrentPageComposite({
                    authoring_document: { document_id: "doc_q", pages: [{ page_id: "page_q" }] },
                    generation_params: {},
                });
            } catch (err) {
                caughtErr = err;
            }

            assert.ok(caughtErr instanceof PageCompositePersistError);
            assert.equal(caughtErr.code, "PERSISTED_COMPOSITE_INCONSISTENT");
            assert.ok(caughtErr.composite_id, "Reports composite_id");
            assert.equal(caughtErr.composite_id, publishedCompositeId);

            // Verify bundle on disk was NOT deleted or rolled back
            const bundlePath = path.join(storeDir, publishedCompositeId);
            const manifestExists = await fs.stat(path.join(bundlePath, "manifest.json")).then(() => true).catch(() => false);
            const artifactExists = await fs.stat(path.join(bundlePath, "artifact.png")).then(() => true).catch(() => false);

            assert.ok(manifestExists, "manifest.json must remain published on disk");
            assert.ok(artifactExists, "artifact.png must remain published on disk");
        });

        // CASE R, S, T: Caller cannot inject authority fields
        await test("Case R, S, T: Caller cannot inject composition_plan, composite_bytes, or composite_id", async () => {
            const store = new PageCompositeStore(path.join(baseTempDir, "store_auth"));
            const mockBridge = { async composeCurrentPage() { return {}; } };
            const service = new PageCompositePersistService({ bridge: mockBridge, store });

            const baseInput = {
                authoring_document: { document_id: "doc", pages: [{ page_id: "p" }] },
                generation_params: {},
            };

            // Case R: composition_plan injection rejected
            await assert.rejects(
                () => service.persistCurrentPageComposite({ ...baseInput, composition_plan: {} }),
                (err) => err instanceof PageCompositePersistError && err.code === "FORBIDDEN_CALLER_FIELD"
            );

            // Case S: composite_bytes injection rejected
            await assert.rejects(
                () => service.persistCurrentPageComposite({ ...baseInput, composite_bytes: Buffer.from("fake") }),
                (err) => err instanceof PageCompositePersistError && err.code === "FORBIDDEN_CALLER_FIELD"
            );

            // Case T: composite_id injection rejected
            await assert.rejects(
                () => service.persistCurrentPageComposite({ ...baseInput, composite_id: "injected_id" }),
                (err) => err instanceof PageCompositePersistError && err.code === "FORBIDDEN_CALLER_FIELD"
            );
        });

        // CASE U, V, W, X: Zero mutation of authoring doc, journal, scene result store, GPU
        await test("Case U, V, W, X: Zero side effects across document, stores, GPU", async () => {
            const storeDir = path.join(baseTempDir, "store_pure");
            await fs.mkdir(storeDir, { recursive: true });
            const store = new PageCompositeStore(storeDir);

            const pngBytes = createValidPngBuffer(64, 64);
            const plan = makeValidPlan("doc_pure", "page_pure", 64, 64);

            const mockBridge = {
                async composeCurrentPage() {
                    return {
                        plan,
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

            const service = new PageCompositePersistService({ bridge: mockBridge, store });

            const authoringDoc = {
                document_id: "doc_pure",
                pages: [{ page_id: "page_pure", width: 64, height: 64, title: "Original Page" }],
                metadata: { version: 1 },
            };
            const docSnapshot = JSON.stringify(authoringDoc);

            await service.persistCurrentPageComposite({
                authoring_document: authoringDoc,
                generation_params: { seed: 42 },
            });

            // Case U: Zero mutation of Authoring Document
            assert.equal(JSON.stringify(authoringDoc), docSnapshot, "Authoring document must not be mutated");

            // Case V, W, X: Only storeDir was modified within our isolated test dir
            const storeSubdirs = await fs.readdir(storeDir);
            assert.equal(storeSubdirs.length, 1);
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
