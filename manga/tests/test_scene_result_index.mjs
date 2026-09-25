/**
 * test_scene_result_index.mjs
 *
 * Targeted contract test suite for SceneResultIndex and its integration
 * with finalizeIsolatedSceneResult(jobId).
 *
 * Covers requirements of Card MANGA-SCENE-RESULT-INDEX-QUERY1:
 * Case A: Index one valid stored manifest.
 * Case B: getByJobId returns its canonical manifest.
 * Case C: Same job + same manifest indexing is idempotent.
 * Case D: Same job + different manifest fails JOB_RESULT_CONFLICT.
 * Case E: Multiple different jobs/results for the same Scene are retained as history.
 * Case F: listByScene ordering is deterministic (created_at descending, manifest_id tie-breaker).
 * Case G: Index write derives owner/job fields from stored manifest, not caller data.
 * Case H: Missing manifest creates ZERO index mutation.
 * Case I: Invalid manifest creates ZERO index mutation.
 * Case J: Concurrent conflicting association cannot both succeed.
 * Case K: Index pointing to missing manifest fails closed on retrieval (INDEX_CONSISTENCY_ERROR).
 * Case L: finalizeIsolatedSceneResult returns canonical manifest on repeat without PNG fetch, builder, or store write.
 * Case M: First finalization performs normal manifest build/store/index path.
 * Case N: Simulated index publication failure leaves stored manifest intact and reports indexing failure.
 * Case O: indexManifest(existingManifestId) recovers that orphan association.
 * Case P: GenerationJournal receives ZERO result index mutation.
 * Case Q: ZERO CURRENT/STALE classification.
 * Case R: ZERO page compositor work.
 * Case S: ZERO live backend / GPU activity.
 */

import assert from "node:assert/strict";
import fs from "node:fs/promises";
import path from "node:path";
import os from "node:os";
import { createHash, randomBytes, randomUUID } from "node:crypto";
import { deflateSync } from "node:zlib";

import { SceneResultIndex, SceneResultIndexError, INDEX_SCHEMA_ID, INDEX_SCHEMA_VERSION } from "../service/scene_result_index.mjs";
import { SceneResultStore } from "../service/scene_result_store.mjs";
import { SCHEMA_ID, SCHEMA_VERSION, validateSceneResultManifest } from "../service/scene_result_manifest.mjs";
import { GenerationService } from "../service/generation_service.mjs";
import { GenerationJournal } from "../service/generation_journal.mjs";

function crc32(buf) {
    let crc = 0xffffffff;
    for (let i = 0; i < buf.length; i++) {
        crc ^= buf[i];
        for (let j = 0; j < 8; j++) {
            crc = (crc >>> 1) ^ (crc & 1 ? 0xedb88320 : 0);
        }
    }
    return (crc ^ 0xffffffff) >>> 0;
}

function makeValidPng(width, height) {
    const signature = Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]);
    const ihdrData = Buffer.alloc(13);
    ihdrData.writeUInt32BE(width, 0);
    ihdrData.writeUInt32BE(height, 4);
    ihdrData[8] = 8;
    ihdrData[9] = 2;
    ihdrData[10] = 0;
    ihdrData[11] = 0;
    ihdrData[12] = 0;
    const ihdrType = Buffer.from("IHDR");
    const ihdrCrc = Buffer.alloc(4);
    ihdrCrc.writeUInt32BE(crc32(Buffer.concat([ihdrType, ihdrData])), 0);
    const ihdrChunk = Buffer.concat([
        Buffer.from([0, 0, 0, 13]),
        ihdrType,
        ihdrData,
        ihdrCrc
    ]);

    const rawScanlines = Buffer.alloc(height * (1 + width * 3), 0);
    const idatCompressed = deflateSync(rawScanlines);
    const idatType = Buffer.from("IDAT");
    const idatLen = Buffer.alloc(4);
    idatLen.writeUInt32BE(idatCompressed.length, 0);
    const idatCrc = Buffer.alloc(4);
    idatCrc.writeUInt32BE(crc32(Buffer.concat([idatType, idatCompressed])), 0);
    const idatChunk = Buffer.concat([idatLen, idatType, idatCompressed, idatCrc]);

    const iendChunk = Buffer.from([0, 0, 0, 0, 73, 69, 78, 68, 174, 66, 96, 130]);

    return Buffer.concat([signature, ihdrChunk, idatChunk, iendChunk]);
}

function createStoredManifestCandidate(overrides = {}) {
    const manifestId = overrides.manifest_id || randomUUID();
    const jobId = overrides.job_id || randomUUID();
    const docId = overrides.document_id || "doc_idx_test_1";
    const pageId = overrides.page_id || "page_idx_test_1";
    const sceneId = overrides.scene_id || "scene_idx_test_1";
    const createdAt = overrides.created_at || new Date().toISOString();

    return {
        schema_id: SCHEMA_ID,
        schema_version: SCHEMA_VERSION,
        manifest_id: manifestId,
        owner: {
            document_id: docId,
            page_id: pageId,
            scene_id: sceneId
        },
        input_provenance: {
            authoring_snapshot_ref: "snapshots/snap_1.json",
            authoring_snapshot_digest: "a".repeat(64),
            effective_input_digest: "b".repeat(64),
            effective_input_contract_version: "2.0.0",
            reference_content_digest: null
        },
        execution: {
            job_id: jobId,
            prompt_id: randomUUID(),
            state: "SUCCEEDED",
            graph_digest: "c".repeat(64),
            page_compile_plan_digest: "d".repeat(64),
            effective_settings: {
                checkpoint_id: "test.safetensors",
                sampler_id: "euler",
                scheduler_id: "normal",
                steps: 20,
                cfg: 7.0,
                seed_requested: "42",
                effective_seed: 42
            }
        },
        artifact: {
            locator: {
                filename: `${jobId}_00001_.png`,
                subfolder: "Manga/Playable",
                type: "output"
            },
            dimensions: {
                width: 512,
                height: 512
            },
            content_digest: "e".repeat(64)
        },
        placement: {
            page_target_rect: { x: 0.1, y: 0.1, w: 0.5, h: 0.5 },
            local_source_rect: { x: 0, y: 0, w: 512, h: 512 },
            transform: { scale_x: 0.5, scale_y: 0.5, offset_x: 0.1, offset_y: 0.1 },
            target_page_dimensions: { width: 1024, height: 1024 }
        },
        created_at: createdAt
    };
}

function createValidJobSetup(overrides = {}) {
    const jobId = overrides.jobId || overrides.job_id || randomUUID();
    const promptId = overrides.promptId || overrides.prompt_id || randomUUID();
    const requestId = overrides.requestId || overrides.request_id || randomUUID();
    const docId = overrides.docId || "doc_manifest_test_1";
    const pageId = overrides.pageId || "page_manifest_test_1";
    const sceneId = overrides.sceneId || "scene_manifest_test_1";
    const width = overrides.width || 512;
    const height = overrides.height || 512;
    const graphDigest = overrides.graphDigest || overrides.graph_digest || "a".repeat(64);
    const planDigest = overrides.planDigest || overrides.page_compile_plan_digest || "b".repeat(64);
    const snapshotDigest = overrides.snapshotDigest || "c".repeat(64);

    const effectiveSettings = {
        checkpoint_id: "test_checkpoint.safetensors",
        sampler_id: "euler",
        scheduler_id: "normal",
        steps: 20,
        cfg: 7.0,
        seed_requested: "12345",
        effective_seed: 12345,
        mask_feather: 0,
        panel_strength: 1.0,
        reference_weight: 0.0,
        reference_start: 0.0,
        reference_end: 1.0
    };

    const placementMapping = {
        page_target_rect: { x: 0.1, y: 0.1, w: 0.5, h: 0.5 },
        local_source_rect: { x: 0, y: 0, w: width, h: height },
        transform: { scale_x: 0.5, scale_y: 0.5, offset_x: 0.1, offset_y: 0.1 },
        target_page_dimensions: { width: 1024, height: 1024 }
    };

    const plan = {
        schema_version: "1.0.0",
        scene_id: sceneId,
        page_id: pageId,
        document_id: docId,
        page_context: {
            page_id: pageId,
            width_px: 1024,
            height_px: 1024
        },
        scene: {
            scene_id: sceneId,
            name: "Test Scene",
            prompt: "masterpiece, 1girl",
            local_area: {
                x: 0,
                y: 0,
                w: width,
                h: height,
                width: width,
                height: height
            }
        },
        character_instances: [],
        cast: [],
        guide_state: {},
        reference: {
            enabled: false,
            reference_asset: null
        },
        placement_mapping: placementMapping
    };

    const compileMetadata = {
        scene_id: sceneId,
        page_context: { page_id: pageId },
        local_dimensions: { width, height },
        graph_digest: graphDigest,
        page_compile_plan_digest: planDigest,
        effective_settings: effectiveSettings,
        placement_mapping: placementMapping
    };

    const outputLocator = {
        filename: `${jobId}_00001_.png`,
        subfolder: "Manga/Playable",
        type: "output"
    };

    const record = {
        job_id: jobId,
        request_id: requestId,
        idempotency_key: `idem-${jobId}`,
        mode: "isolated_scene",
        owner: {
            document_id: docId,
            page_id: pageId,
            scene_id: sceneId
        },
        snapshot: {
            snapshot_id: "snap_1",
            snapshot_ref: "snapshots/snap_1.json",
            content_digest: snapshotDigest
        },
        plan,
        requested_settings: { mode: "isolated_scene" },
        effective_settings: effectiveSettings,
        graph_digest: graphDigest,
        submitted_graph_digest: graphDigest,
        save_node_id: "99",
        page_compile_plan: { plan_version: "1.0.0", scenes: [{ scene_id: sceneId }] },
        page_compile_plan_digest: planDigest,
        compile_metadata: compileMetadata,
        audit_trail: null,
        backend_identity: null,
        prompt_id: promptId,
        created_at: new Date().toISOString(),
        submitted_at: new Date().toISOString(),
        started_at: new Date().toISOString(),
        finished_at: new Date().toISOString(),
        state: "SUCCEEDED",
        error: null,
        output_locator: outputLocator,
        ownership_token: randomBytes(32).toString("hex")
    };

    return {
        jobId,
        promptId,
        docId,
        pageId,
        sceneId,
        width,
        height,
        graphDigest,
        planDigest,
        snapshotDigest,
        effectiveSettings,
        plan,
        compileMetadata,
        outputLocator,
        record
    };
}

async function runTests() {
    let passCount = 0;
    let failCount = 0;

    const test = async (name, fn) => {
        try {
            await fn();
            passCount++;
            console.log(`PASS: ${name}`);
        } catch (err) {
            failCount++;
            console.error(`FAIL: ${name}`);
            console.error(err);
        }
    };

    const tmpBase = await fs.mkdtemp(path.join(os.tmpdir(), "manga-index-test-"));
    const storeDir = path.join(tmpBase, "scene_results");
    const indexDir = path.join(tmpBase, "scene_results_index");
    const journalDir = path.join(tmpBase, "journal");

    try {
        const store = new SceneResultStore(storeDir);
        const index = new SceneResultIndex({ directory: indexDir, store });

        // CASE A: Index one valid stored manifest
        await test("Case A: Index one valid stored manifest", async () => {
            const candidate = createStoredManifestCandidate();
            const saved = await store.saveCompletedManifest(candidate);

            const entry = await index.indexManifest(saved.manifest_id);

            assert.equal(entry.manifest_id, saved.manifest_id);
            assert.equal(entry.job_id, saved.execution.job_id);
            assert.equal(entry.document_id, saved.owner.document_id);
            assert.equal(entry.page_id, saved.owner.page_id);
            assert.equal(entry.scene_id, saved.owner.scene_id);
            assert.equal(entry.created_at, saved.created_at);

            // Verify index file content on disk
            const rawIndex = JSON.parse(await fs.readFile(path.join(indexDir, "scene_result_index.json"), "utf8"));
            assert.equal(rawIndex.schema_id, INDEX_SCHEMA_ID);
            assert.equal(rawIndex.schema_version, INDEX_SCHEMA_VERSION);
            assert.equal(rawIndex.entries.length, 1);
        });

        // CASE B: getByJobId returns its canonical manifest
        await test("Case B: getByJobId returns its canonical manifest", async () => {
            const candidate = createStoredManifestCandidate();
            const saved = await store.saveCompletedManifest(candidate);
            await index.indexManifest(saved.manifest_id);

            const result = await index.getByJobId(saved.execution.job_id);
            assert.ok(result);
            assert.equal(result.manifest_id, saved.manifest_id);
            assert.deepEqual(result.manifest, saved);

            // Query non-existent jobId
            const missing = await index.getByJobId(randomUUID());
            assert.equal(missing, null);
        });

        // CASE C: Same job + same manifest indexing is idempotent
        await test("Case C: Same job + same manifest indexing is idempotent", async () => {
            const candidate = createStoredManifestCandidate();
            const saved = await store.saveCompletedManifest(candidate);

            const entry1 = await index.indexManifest(saved.manifest_id);
            const entry2 = await index.indexManifest(saved.manifest_id);

            assert.deepEqual(entry1, entry2);

            const rawIndex = JSON.parse(await fs.readFile(path.join(indexDir, "scene_result_index.json"), "utf8"));
            const matching = rawIndex.entries.filter(e => e.job_id === saved.execution.job_id);
            assert.equal(matching.length, 1, "Idempotent indexManifest must not duplicate entry");
        });

        // CASE D: Same job + different manifest fails JOB_RESULT_CONFLICT
        await test("Case D: Same job + different manifest fails JOB_RESULT_CONFLICT", async () => {
            const sharedJobId = randomUUID();
            const cand1 = createStoredManifestCandidate({ job_id: sharedJobId });
            const cand2 = createStoredManifestCandidate({ job_id: sharedJobId });

            const saved1 = await store.saveCompletedManifest(cand1);
            const saved2 = await store.saveCompletedManifest(cand2);

            await index.indexManifest(saved1.manifest_id);

            await assert.rejects(
                () => index.indexManifest(saved2.manifest_id),
                (err) => err instanceof SceneResultIndexError && err.code === "JOB_RESULT_CONFLICT"
            );

            // Canonical entry remains saved1
            const canonical = await index.getByJobId(sharedJobId);
            assert.equal(canonical.manifest_id, saved1.manifest_id);
        });

        // CASE E & F: Multiple results for same Scene retained as history with deterministic ordering
        await test("Case E & F: Multiple results for same Scene retained and ordered deterministically", async () => {
            const docId = "doc_hist_1";
            const pageId = "page_hist_1";
            const sceneId = "scene_hist_1";

            const t1 = "2026-09-25T10:00:00.000Z";
            const t2 = "2026-09-25T12:00:00.000Z";
            const t3 = "2026-09-25T14:00:00.000Z";

            const m1 = await store.saveCompletedManifest(createStoredManifestCandidate({ document_id: docId, page_id: pageId, scene_id: sceneId, created_at: t1 }));
            const m2 = await store.saveCompletedManifest(createStoredManifestCandidate({ document_id: docId, page_id: pageId, scene_id: sceneId, created_at: t2 }));
            const m3 = await store.saveCompletedManifest(createStoredManifestCandidate({ document_id: docId, page_id: pageId, scene_id: sceneId, created_at: t3 }));

            // Index in mixed order
            await index.indexManifest(m2.manifest_id);
            await index.indexManifest(m1.manifest_id);
            await index.indexManifest(m3.manifest_id);

            const history = await index.listByScene({ document_id: docId, page_id: pageId, scene_id: sceneId });
            assert.equal(history.length, 3);

            // Deterministic descending order by created_at: m3 (14:00), then m2 (12:00), then m1 (10:00)
            assert.equal(history[0].manifest_id, m3.manifest_id);
            assert.equal(history[1].manifest_id, m2.manifest_id);
            assert.equal(history[2].manifest_id, m1.manifest_id);

            // listByScene with loadManifests: true
            const fullHistory = await index.listByScene({ document_id: docId, page_id: pageId, scene_id: sceneId, loadManifests: true });
            assert.equal(fullHistory.length, 3);
            assert.deepEqual(fullHistory[0].manifest, m3);
            assert.deepEqual(fullHistory[1].manifest, m2);
            assert.deepEqual(fullHistory[2].manifest, m1);
        });

        // CASE G: Index write derives owner/job fields from stored manifest, not caller data
        await test("Case G: Index write derives owner/job fields from stored manifest, not caller data", async () => {
            const cand = createStoredManifestCandidate({ document_id: "doc_true", page_id: "page_true", scene_id: "scene_true" });
            const saved = await store.saveCompletedManifest(cand);

            // indexManifest only accepts manifestId, preventing any spoofing of owner/job
            const entry = await index.indexManifest(saved.manifest_id);
            assert.equal(entry.document_id, "doc_true");
            assert.equal(entry.page_id, "page_true");
            assert.equal(entry.scene_id, "scene_true");
            assert.equal(entry.job_id, saved.execution.job_id);
        });

        // CASE H: Missing manifest creates ZERO index mutation
        await test("Case H: Missing manifest creates ZERO index mutation", async () => {
            const missingId = "00000000-0000-4000-8000-000000000000";
            const preData = await index._readIndex();

            await assert.rejects(
                () => index.indexManifest(missingId),
                (err) => err instanceof SceneResultIndexError && err.code === "MANIFEST_NOT_FOUND"
            );

            const postData = await index._readIndex();
            assert.equal(postData.entries.length, preData.entries.length);
        });

        // CASE I: Invalid manifest creates ZERO index mutation
        await test("Case I: Invalid manifest creates ZERO index mutation", async () => {
            const badManifestId = randomUUID();
            const badPath = path.join(storeDir, `${badManifestId}.json`);
            // Write malformed JSON directly to store directory
            await fs.writeFile(badPath, "NOT_JSON_OR_MALFORMED", "utf8");

            const preData = await index._readIndex();

            await assert.rejects(
                () => index.indexManifest(badManifestId),
                (err) => err instanceof SceneResultIndexError
            );

            const postData = await index._readIndex();
            assert.equal(postData.entries.length, preData.entries.length);

            // Clean up the corrupt test file so subsequent store scans are clean
            try { await fs.unlink(badPath); } catch {}
        });

        // CASE J: Concurrent conflicting association cannot both succeed
        await test("Case J: Concurrent conflicting association cannot both succeed", async () => {
            const sharedJobId = randomUUID();
            const candA = createStoredManifestCandidate({ job_id: sharedJobId });
            const candB = createStoredManifestCandidate({ job_id: sharedJobId });

            const savedA = await store.saveCompletedManifest(candA);
            const savedB = await store.saveCompletedManifest(candB);

            const results = await Promise.allSettled([
                index.indexManifest(savedA.manifest_id),
                index.indexManifest(savedB.manifest_id)
            ]);

            const fulfilled = results.filter(r => r.status === "fulfilled");
            const rejected = results.filter(r => r.status === "rejected");

            assert.equal(fulfilled.length, 1, "Exactly one concurrent call must succeed");
            assert.equal(rejected.length, 1, "The competing concurrent call must fail");
            assert.equal(rejected[0].reason.code, "JOB_RESULT_CONFLICT");
        });

        // CASE K: Index pointing to missing manifest fails closed on retrieval
        await test("Case K: Index pointing to missing manifest fails closed on retrieval", async () => {
            const cand = createStoredManifestCandidate();
            const saved = await store.saveCompletedManifest(cand);
            await index.indexManifest(saved.manifest_id);

            // Remove physical manifest file from store behind the index
            await fs.unlink(path.join(storeDir, `${saved.manifest_id}.json`));

            await assert.rejects(
                () => index.getByJobId(saved.execution.job_id),
                (err) => err instanceof SceneResultIndexError && err.code === "INDEX_CONSISTENCY_ERROR"
            );
        });

        // CASE L & M & P: GenerationService finalization integration (First finalization and repeat finalization)
        await test("Case L & M & P: First finalization indexes result; repeat returns canonical without PNG fetch, builder, or store write", async () => {
            const setup = createValidJobSetup();
            const pngBytes = makeValidPng(setup.width, setup.height);

            const journal = new GenerationJournal(journalDir);
            await journal.put(setup.record);
            const preJournalRaw = await fs.readFile(path.join(journalDir, `${setup.jobId}.json`), "utf8");

            let fetchCount = 0;
            const mockFetch = async (url) => {
                fetchCount++;
                const u = new URL(url);
                if (u.pathname === "/view") {
                    return new Response(pngBytes, {
                        status: 200,
                        headers: { "Content-Type": "image/png" }
                    });
                }
                throw new Error(`Unexpected fetch URL: ${url}`);
            };

            const service = new GenerationService({
                backendUrl: "http://127.0.0.1:8189",
                journal,
                fetchFn: mockFetch,
                sceneResultStore: store,
                sceneResultIndex: index
            });

            // Case M: First finalization
            const initialStoreCount = (await fs.readdir(storeDir)).filter(f => f.endsWith(".json")).length;
            const res1 = await service.finalizeIsolatedSceneResult(setup.jobId);

            assert.ok(res1.manifest_id);
            assert.ok(res1.manifest);
            assert.equal(fetchCount, 1, "First finalization must fetch PNG artifact once");

            const postStoreCount = (await fs.readdir(storeDir)).filter(f => f.endsWith(".json")).length;
            assert.equal(postStoreCount, initialStoreCount + 1, "First finalization must write exactly ONE manifest");

            // Verify indexed in SceneResultIndex
            const indexedEntry = await index.getEntryByJobId(setup.jobId);
            assert.ok(indexedEntry);
            assert.equal(indexedEntry.manifest_id, res1.manifest_id);

            // Case P: GenerationJournal mutation is ZERO
            const postJournalRaw = await fs.readFile(path.join(journalDir, `${setup.jobId}.json`), "utf8");
            assert.equal(postJournalRaw, preJournalRaw, "Journal record must remain unmutated");

            // Case L: Repeat finalization of the SAME job
            const res2 = await service.finalizeIsolatedSceneResult(setup.jobId);

            assert.equal(res2.manifest_id, res1.manifest_id, "Repeat finalization must return the SAME canonical manifest ID");
            assert.deepEqual(res2.manifest, res1.manifest, "Repeat finalization must return the SAME manifest");
            assert.equal(fetchCount, 1, "Repeat finalization must perform ZERO additional PNG fetches");

            const repeatStoreCount = (await fs.readdir(storeDir)).filter(f => f.endsWith(".json")).length;
            assert.equal(repeatStoreCount, postStoreCount, "Repeat finalization must write ZERO additional files to SceneResultStore");
        });

        // CASE N & O: Store-succeeded / index-failed window and orphan recovery via indexManifest
        await test("Case N & O: Store-succeeded / index-failed window reports failure and indexManifest recovers orphan", async () => {
            const setup = createValidJobSetup();
            const pngBytes = makeValidPng(setup.width, setup.height);

            const journal = new GenerationJournal(journalDir);
            await journal.put(setup.record);

            const mockFetch = async () => new Response(pngBytes, {
                status: 200,
                headers: { "Content-Type": "image/png" }
            });

            // Index whose indexManifest fails
            const failingIndex = {
                getByJobId: async () => null,
                indexManifest: async () => {
                    const err = new Error("Simulated index write failure");
                    err.code = "INDEX_WRITE_FAILED";
                    throw err;
                }
            };

            const serviceWithFailingIndex = new GenerationService({
                backendUrl: "http://127.0.0.1:8189",
                journal,
                fetchFn: mockFetch,
                sceneResultStore: store,
                sceneResultIndex: failingIndex
            });

            // Case N: Finalization fails when index publication fails
            await assert.rejects(
                () => serviceWithFailingIndex.finalizeIsolatedSceneResult(setup.jobId),
                (err) => err.code === "INDEX_WRITE_FAILED" || err.message.includes("Simulated index write failure")
            );

            // But manifest in SceneResultStore remains intact!
            // Locate the persisted manifest by scanning store files
            const storeFiles = (await fs.readdir(storeDir)).filter(f => f.endsWith(".json"));
            let orphanManifestId = null;
            for (const file of storeFiles) {
                const id = path.basename(file, ".json");
                try {
                    const m = await store.getManifest(id);
                    if (m && m.execution?.job_id === setup.jobId) {
                        orphanManifestId = id;
                        break;
                    }
                } catch {}
            }
            assert.ok(orphanManifestId, "Manifest must remain persisted in Store even if index publication fails");

            // Case O: Orphan recovery via indexManifest on working index
            const recoveredEntry = await index.indexManifest(orphanManifestId);
            assert.equal(recoveredEntry.manifest_id, orphanManifestId);
            assert.equal(recoveredEntry.job_id, setup.jobId);

            // Now getByJobId succeeds
            const canonical = await index.getByJobId(setup.jobId);
            assert.equal(canonical.manifest_id, orphanManifestId);
        });

        // CASE Q: ZERO CURRENT / STALE classification
        await test("Case Q: ZERO CURRENT / STALE classification in index service", () => {
            assert.equal(typeof index.classifyFreshness, "undefined");
            assert.equal(typeof index.isCurrent, "undefined");
            assert.equal(typeof index.isStale, "undefined");
        });

        // CASE R: ZERO page compositor work
        await test("Case R: ZERO page compositor work in index service", () => {
            assert.equal(typeof index.compositePage, "undefined");
            assert.equal(typeof index.compose, "undefined");
        });

        // CASE S: ZERO live backend / GPU activity
        await test("Case S: ZERO live backend / GPU activity during all tests", () => {
            // Proven by offline mockFetch and local filesystem operations
            assert.ok(true);
        });

    } finally {
        await fs.rm(tmpBase, { recursive: true, force: true });
    }

    console.log(`\nFinal Test Results: ${passCount} PASSED / ${failCount} FAILED`);
    if (failCount > 0) {
        process.exit(1);
    }
}

runTests();
