/**
 * test_isolated_scene_manifest_finalize.mjs
 *
 * Targeted contract test suite for finalizeIsolatedSceneResult(jobId)
 * in GenerationService.
 *
 * Verifies:
 * - Successful assembly of schema v1.1.0 Scene Result Manifest
 * - Atomic persistence in SceneResultStore
 * - Provenance preservation (original snapshot, effective input digest v2.0.0, disabled reference)
 * - Fresh artifact analysis integration and digest/dimension equality
 * - Zero GenerationJournal mutation
 * - Zero persistence on failure modes (builder mismatch, PNG error, missing journal provenance, store failure)
 * - Safe return shape (no raw bytes, no paths, no ownership tokens)
 * - Zero live backend / GPU calls
 */

import assert from "node:assert/strict";
import fs from "node:fs/promises";
import path from "node:path";
import os from "node:os";
import { createHash, randomBytes, randomUUID } from "node:crypto";
import { deflateSync } from "node:zlib";

import { GenerationService, sceneResultManifestIdForJob } from "../service/generation_service.mjs";
import { GenerationJournal } from "../service/generation_journal.mjs";
import { SceneResultStore } from "../service/scene_result_store.mjs";
import { SceneResultIndex } from "../service/scene_result_index.mjs";
import {
    SCHEMA_ID,
    SCHEMA_VERSION,
    REQUIRED_DIGEST_CONTRACT_VERSION_V1_1,
} from "../service/scene_result_manifest.mjs";

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

    const tmpBase = await fs.mkdtemp(path.join(os.tmpdir(), "manga-finalize-test-"));
    const journalDir = path.join(tmpBase, "journal");
    const storeDir = path.join(tmpBase, "scene_results");

    try {
        // CASE A-L & Q & R: Valid completed isolated job finalization
        await test("Case A-L: Valid completed isolated job finalizes schema v1.1.0 manifest with full provenance", async () => {
            const setup = createValidJobSetup();
            const pngBytes = makeValidPng(setup.width, setup.height);
            const expectedPngDigest = createHash("sha256").update(pngBytes).digest("hex");

            const journal = new GenerationJournal(journalDir);
            await journal.put(setup.record);
            const preJournalContent = await fs.readFile(path.join(journalDir, `${setup.jobId}.json`), "utf8");

            const mockFetch = async (url) => {
                const u = new URL(url);
                if (u.pathname === "/view") {
                    return new Response(pngBytes, {
                        status: 200,
                        headers: { "Content-Type": "image/png" }
                    });
                }
                throw new Error(`Unexpected fetch URL: ${url}`);
            };

            const store = new SceneResultStore(storeDir);
            const service = new GenerationService({
                backendUrl: "http://127.0.0.1:8189",
                journal,
                fetchFn: mockFetch,
                sceneResultStore: store
            });

            const result = await service.finalizeIsolatedSceneResult(setup.jobId);

            // Shape of return
            assert.ok(result.manifest_id, "Must return manifest_id");
            assert.ok(result.manifest, "Must return manifest object");
            assert.equal(result.manifest_id, result.manifest.manifest_id);

            // Case A: schema_id and schema_version
            assert.equal(result.manifest.schema_id, SCHEMA_ID);
            assert.equal(result.manifest.schema_version, SCHEMA_VERSION);

            // Case B: round-trips through actual SceneResultStore
            const loaded = await store.getManifest(result.manifest_id, { required: true });
            assert.deepEqual(loaded, result.manifest);

            // Case C: Original snapshot provenance
            assert.equal(result.manifest.input_provenance.authoring_snapshot_ref, setup.record.snapshot.snapshot_ref);
            assert.equal(result.manifest.input_provenance.authoring_snapshot_digest, setup.record.snapshot.content_digest);

            // Case D & E: effective_input_digest and contract version
            assert.match(result.manifest.input_provenance.effective_input_digest, /^[0-9a-f]{64}$/);
            assert.equal(result.manifest.input_provenance.effective_input_contract_version, REQUIRED_DIGEST_CONTRACT_VERSION_V1_1);

            // Case F: Reference explicitly disabled, no fake reference digest
            assert.equal(result.manifest.input_provenance.reference_content_digest, null);

            // Case G & H: PNG analysis digest matches exact fetched bytes
            assert.equal(result.manifest.artifact.content_digest, expectedPngDigest);

            // Case I: Dimensions match local canvas dimensions
            assert.equal(result.manifest.artifact.dimensions.width, setup.width);
            assert.equal(result.manifest.artifact.dimensions.height, setup.height);

            // Case J: Owner identity matches trusted plan/job evidence
            assert.equal(result.manifest.owner.document_id, setup.docId);
            assert.equal(result.manifest.owner.page_id, setup.pageId);
            assert.equal(result.manifest.owner.scene_id, setup.sceneId);

            // Case K: graph_digest and page_compile_plan_digest match compiler metadata
            assert.equal(result.manifest.execution.graph_digest, setup.graphDigest);
            assert.equal(result.manifest.execution.page_compile_plan_digest, setup.planDigest);

            // Case L: effective_settings match compiler/runtime evidence
            assert.equal(result.manifest.execution.effective_settings.checkpoint_id, setup.effectiveSettings.checkpoint_id);
            assert.equal(result.manifest.execution.effective_settings.steps, setup.effectiveSettings.steps);
            assert.equal(result.manifest.execution.effective_settings.cfg, setup.effectiveSettings.cfg);
            assert.equal(result.manifest.execution.effective_settings.effective_seed, setup.effectiveSettings.effective_seed);

            // Case Q: No raw PNG bytes returned
            assert.equal(result.bytes, undefined);
            assert.equal(result.png_bytes, undefined);
            assert.equal(result.ownership_token, undefined);

            // Case R: Zero GenerationJournal mutation
            const postJournalContent = await fs.readFile(path.join(journalDir, `${setup.jobId}.json`), "utf8");
            assert.equal(postJournalContent, preJournalContent, "Journal file must not be modified by finalization");
        });

        // CASE M: Builder consistency failure -> ZERO Store persistence
        await test("Case M: Builder consistency failure causes ZERO SceneResultStore persistence", async () => {
            const setup = createValidJobSetup();
            // Introduce a mismatch: compile_metadata graph_digest differs from job graph_digest
            setup.record.compile_metadata.graph_digest = "f".repeat(64);

            const pngBytes = makeValidPng(setup.width, setup.height);
            const journal = new GenerationJournal(journalDir);
            await journal.put(setup.record);

            const mockFetch = async () => new Response(pngBytes, {
                status: 200,
                headers: { "Content-Type": "image/png" }
            });

            const store = new SceneResultStore(storeDir);
            let preFiles = [];
            try {
                preFiles = (await fs.readdir(storeDir)).filter(f => f.endsWith(".json"));
            } catch (err) {
                if (err.code !== "ENOENT") throw err;
            }

            const service = new GenerationService({
                backendUrl: "http://127.0.0.1:8189",
                journal,
                fetchFn: mockFetch,
                sceneResultStore: store
            });

            await assert.rejects(
                () => service.finalizeIsolatedSceneResult(setup.jobId),
                (err) => err.code === "DIGEST_MISMATCH"
            );

            let postFiles = [];
            try {
                postFiles = (await fs.readdir(storeDir)).filter(f => f.endsWith(".json"));
            } catch (err) {
                if (err.code !== "ENOENT") throw err;
            }
            assert.equal(postFiles.length, preFiles.length, "ZERO new files must be written to Store on builder failure");
        });

        // CASE N: PNG / artifact failure -> ZERO Store persistence
        await test("Case N: Artifact dimension mismatch causes ZERO SceneResultStore persistence", async () => {
            const setup = createValidJobSetup();
            // PNG bytes are 256x256 while expected is 512x512
            const badPngBytes = makeValidPng(256, 256);

            const journal = new GenerationJournal(journalDir);
            await journal.put(setup.record);

            const mockFetch = async () => new Response(badPngBytes, {
                status: 200,
                headers: { "Content-Type": "image/png" }
            });

            const store = new SceneResultStore(storeDir);
            let preFiles = [];
            try {
                preFiles = (await fs.readdir(storeDir)).filter(f => f.endsWith(".json"));
            } catch (err) {
                if (err.code !== "ENOENT") throw err;
            }

            const service = new GenerationService({
                backendUrl: "http://127.0.0.1:8189",
                journal,
                fetchFn: mockFetch,
                sceneResultStore: store
            });

            await assert.rejects(
                () => service.finalizeIsolatedSceneResult(setup.jobId),
                (err) => err.code === "DIMENSION_MISMATCH"
            );

            let postFiles = [];
            try {
                postFiles = (await fs.readdir(storeDir)).filter(f => f.endsWith(".json"));
            } catch (err) {
                if (err.code !== "ENOENT") throw err;
            }
            assert.equal(postFiles.length, preFiles.length, "ZERO files written on artifact error");
        });

        // CASE O: Missing required journal provenance -> ZERO Store persistence
        await test("Case O: Missing required journal provenance causes ZERO persistence", async () => {
            const setup = createValidJobSetup();
            // Put valid record first to pass journal validation, then mutate on disk to test missing provenance
            const journal = new GenerationJournal(journalDir);
            await journal.put(setup.record);

            // Read disk record, delete snapshot, and write back directly to disk
            const diskPath = path.join(journalDir, `${setup.jobId}.json`);
            const diskRecord = JSON.parse(await fs.readFile(diskPath, "utf8"));
            delete diskRecord.snapshot;
            await fs.writeFile(diskPath, JSON.stringify(diskRecord, null, 2), "utf8");

            const store = new SceneResultStore(storeDir);
            let preFiles = [];
            try {
                preFiles = (await fs.readdir(storeDir)).filter(f => f.endsWith(".json"));
            } catch (err) {
                if (err.code !== "ENOENT") throw err;
            }

            const service = new GenerationService({
                backendUrl: "http://127.0.0.1:8189",
                journal,
                sceneResultStore: store
            });

            await assert.rejects(
                () => service.finalizeIsolatedSceneResult(setup.jobId),
                (err) => err.code === "MISSING_EXECUTION_PROVENANCE"
            );

            let postFiles = [];
            try {
                postFiles = (await fs.readdir(storeDir)).filter(f => f.endsWith(".json"));
            } catch (err) {
                if (err.code !== "ENOENT") throw err;
            }
            assert.equal(postFiles.length, preFiles.length, "ZERO files written on missing provenance");
        });

        // CASE P: Store persistence failure causes finalization to fail
        await test("Case P: Store persistence failure prevents successful finalization", async () => {
            const setup = createValidJobSetup();
            const pngBytes = makeValidPng(setup.width, setup.height);

            const journal = new GenerationJournal(journalDir);
            await journal.put(setup.record);

            const mockFetch = async () => new Response(pngBytes, {
                status: 200,
                headers: { "Content-Type": "image/png" }
            });

            // Mock store whose saveCompletedManifest always fails
            const failingStore = {
                // No prior record exists for this job (canonical-id lookup).
                getManifest: async () => null,
                saveCompletedManifest: async () => {
                    const err = new Error("Disk full simulation");
                    err.code = "STORE_WRITE_FAILED";
                    throw err;
                }
            };

            const service = new GenerationService({
                backendUrl: "http://127.0.0.1:8189",
                journal,
                fetchFn: mockFetch,
                sceneResultStore: failingStore
            });

            await assert.rejects(
                () => service.finalizeIsolatedSceneResult(setup.jobId),
                (err) => err.code === "STORE_WRITE_FAILED" || err.message.includes("Disk full simulation")
            );
        });

        // CASE S: No result index or query sidecar created
        await test("Case S: No result index or query sidecar file is created in SceneResultStore", async () => {
            let entries = [];
            try {
                entries = await fs.readdir(storeDir);
            } catch (err) {
                if (err.code !== "ENOENT") throw err;
            }
            for (const entry of entries) {
                assert.match(entry, /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\.json$/,
                    `Store directory must only contain UUIDv4 manifest JSON files, found: ${entry}`);
            }
        });

        // CASE T: Zero live backend / GPU activity
        await test("Case T: Zero live backend / GPU endpoints called", async () => {
            const setup = createValidJobSetup();
            const pngBytes = makeValidPng(setup.width, setup.height);

            const journal = new GenerationJournal(journalDir);
            await journal.put(setup.record);

            const requestedUrls = [];
            const mockFetch = async (url) => {
                requestedUrls.push(url.toString());
                return new Response(pngBytes, {
                    status: 200,
                    headers: { "Content-Type": "image/png" }
                });
            };

            const store = new SceneResultStore(storeDir);
            const service = new GenerationService({
                backendUrl: "http://127.0.0.1:8189",
                journal,
                fetchFn: mockFetch,
                sceneResultStore: store
            });

            await service.finalizeIsolatedSceneResult(setup.jobId);

            // Verify only loopback /view was called
            assert.equal(requestedUrls.length, 1);
            const calledUrl = new URL(requestedUrls[0]);
            assert.equal(calledUrl.pathname, "/view");
            assert.ok(!requestedUrls.some(u => u.includes("/prompt") || u.includes("/history") || u.includes("8188")));
        });

        // ------------------------------------------------------------------
        // MANGA-ISOLATED-BASELINE-CORRECTION1 / B4: auto-finalization on getJob
        // ------------------------------------------------------------------
        const b4Env = async (label, setup, { fetchImpl = null } = {}) => {
            const base = path.join(tmpBase, `b4-${label}`);
            const journal = new GenerationJournal(path.join(base, "journal"));
            await journal.put(setup.record);
            const store = new SceneResultStore(path.join(base, "scene_results"));
            const index = new SceneResultIndex({ directory: path.join(base, "scene_result_index"), store });
            const pngBytes = makeValidPng(setup.width, setup.height);
            const calls = [];
            const fetchFn = fetchImpl || (async (url) => {
                calls.push(new URL(url).pathname);
                if (new URL(url).pathname === "/view") {
                    return new Response(pngBytes, { status: 200, headers: { "Content-Type": "image/png" } });
                }
                throw new Error(`Unexpected fetch URL: ${url}`);
            });
            const service = new GenerationService({
                backendUrl: "http://127.0.0.1:8189", journal, fetchFn,
                sceneResultStore: store, sceneResultIndex: index,
            });
            const manifestFiles = async () => {
                try {
                    return (await fs.readdir(path.join(base, "scene_results"))).filter(n => n.endsWith(".json"));
                } catch { return []; }
            };
            return { base, journal, store, index, service, calls, manifestFiles };
        };

        await test("B4-1: getJob on SUCCEEDED isolated job auto-finalizes exactly one durable SceneResult", async () => {
            const setup = createValidJobSetup();
            const env = await b4Env("one", setup);
            const journalPath = path.join(env.base, "journal", `${setup.jobId}.json`);
            const journalBefore = await fs.readFile(journalPath, "utf8");

            const job = await env.service.getJob(setup.jobId);
            assert.equal(job.state, "SUCCEEDED");
            assert.equal(job.scene_result.status, "FINALIZED");
            assert.equal(job.scene_result.manifest_id, sceneResultManifestIdForJob(setup.jobId));
            assert.equal(job.ownership_token, undefined);

            const entry = await env.index.getEntryByJobId(setup.jobId);
            assert.equal(entry.manifest_id, job.scene_result.manifest_id);
            const stored = await env.store.getManifest(job.scene_result.manifest_id, { required: true });
            assert.equal(stored.execution.job_id, setup.jobId);
            assert.deepEqual(await env.manifestFiles(), [`${job.scene_result.manifest_id}.json`]);
            // Association is response-only: the journal record is untouched.
            assert.equal(await fs.readFile(journalPath, "utf8"), journalBefore);
        });

        await test("B4-2: repeated and concurrent polling is idempotent (one manifest, one /view fetch)", async () => {
            const setup = createValidJobSetup();
            const env = await b4Env("idem", setup);
            const first = await env.service.getJob(setup.jobId);
            const again = await Promise.all([
                env.service.getJob(setup.jobId),
                env.service.getJob(setup.jobId),
                env.service.getJob(setup.jobId),
            ]);
            for (const j of again) {
                assert.equal(j.scene_result.status, "FINALIZED");
                assert.equal(j.scene_result.manifest_id, first.scene_result.manifest_id);
            }
            const direct = await env.service.finalizeIsolatedSceneResult(setup.jobId);
            assert.equal(direct.manifest_id, first.scene_result.manifest_id);
            assert.equal((await env.manifestFiles()).length, 1);
            assert.equal(env.calls.filter(p => p === "/view").length, 1);
        });

        await test("B4-3: already-finalized job reuses its existing canonical result (no new manifest)", async () => {
            const setup = createValidJobSetup();
            const env = await b4Env("reuse", setup);
            const legacyId = randomUUID();
            await env.service.finalizeIsolatedSceneResult(setup.jobId, { _manifestIdFactory: () => legacyId });
            const job = await env.service.getJob(setup.jobId);
            assert.equal(job.scene_result.manifest_id, legacyId);
            assert.deepEqual(await env.manifestFiles(), [`${legacyId}.json`]);
        });

        await test("B4-4: saved-but-unindexed partial finalization is adopted, not duplicated", async () => {
            const setup = createValidJobSetup();
            const env = await b4Env("partial", setup);
            const brokenIndex = {
                getByJobId: async () => null,
                indexManifest: async () => { const e = new Error("disk full"); e.code = "INDEX_WRITE_FAILED"; throw e; },
            };
            const broken = new GenerationService({
                backendUrl: "http://127.0.0.1:8189", journal: env.journal, fetchFn: env.service.fetchFn,
                sceneResultStore: env.store, sceneResultIndex: brokenIndex,
            });
            const failed = await broken.getJob(setup.jobId);
            assert.equal(failed.state, "SUCCEEDED");
            assert.equal(failed.scene_result.status, "FINALIZATION_FAILED");
            assert.equal(failed.scene_result.error.code, "INDEX_WRITE_FAILED");
            assert.equal((await env.manifestFiles()).length, 1);

            const job = await env.service.getJob(setup.jobId);
            assert.equal(job.scene_result.status, "FINALIZED");
            assert.equal(job.scene_result.manifest_id, sceneResultManifestIdForJob(setup.jobId));
            assert.equal((await env.manifestFiles()).length, 1);
            assert.equal((await env.index.getEntryByJobId(setup.jobId)).manifest_id, job.scene_result.manifest_id);
        });

        await test("B4-5: conflicting durable data fails closed without overwrite or repair", async () => {
            const victim = createValidJobSetup();
            const env = await b4Env("conflict", victim);
            // Another job's manifest occupies the victim's canonical id (tampered/foreign data).
            const other = createValidJobSetup();
            await env.journal.put(other.record);
            const sideIndex = new SceneResultIndex({ directory: path.join(env.base, "side_index"), store: env.store });
            const side = new GenerationService({
                backendUrl: "http://127.0.0.1:8189", journal: env.journal, fetchFn: env.service.fetchFn,
                sceneResultStore: env.store, sceneResultIndex: sideIndex,
            });
            const squatId = sceneResultManifestIdForJob(victim.jobId);
            await side.finalizeIsolatedSceneResult(other.jobId, { _manifestIdFactory: () => squatId });
            const squatPath = path.join(env.base, "scene_results", `${squatId}.json`);
            const squatBefore = await fs.readFile(squatPath, "utf8");

            const job = await env.service.getJob(victim.jobId);
            assert.equal(job.state, "SUCCEEDED");
            assert.equal(job.scene_result.status, "FINALIZATION_FAILED");
            assert.equal(job.scene_result.error.code, "SCENE_RESULT_CONSISTENCY_ERROR");
            assert.equal(await fs.readFile(squatPath, "utf8"), squatBefore);
            assert.equal((await env.manifestFiles()).length, 1);
            assert.equal(await env.index.getEntryByJobId(victim.jobId), null);
        });

        await test("B4-6: FAILED / RUNNING / UNKNOWN isolated jobs never finalize", async () => {
            for (const state of ["FAILED", "RUNNING", "UNKNOWN"]) {
                const setup = createValidJobSetup();
                if (state === "FAILED") {
                    setup.record.error = { code: "BACKEND_EXECUTION_FAILED", message: "x" };
                }
                setup.record.state = state;
                const env = await b4Env(`state-${state}`, setup, {
                    fetchImpl: async () => { throw new Error("backend offline"); },
                });
                const job = await env.service.getJob(setup.jobId);
                assert.notEqual(job.state, "SUCCEEDED");
                assert.equal(job.scene_result, undefined, `${state} must not carry a scene_result`);
                assert.equal((await env.manifestFiles()).length, 0);
                assert.equal(await env.index.getEntryByJobId(setup.jobId), null);
            }
        });

        await test("B4-7: whole-page (non-isolated) SUCCEEDED job is returned unchanged by getJob", async () => {
            const setup = createValidJobSetup();
            delete setup.record.mode;
            const env = await b4Env("whole-page", setup, {
                fetchImpl: async () => { throw new Error("no backend call expected"); },
            });
            const job = await env.service.getJob(setup.jobId);
            const { ownership_token, ...expected } = setup.record;
            assert.deepEqual(job, expected);
            assert.equal((await env.manifestFiles()).length, 0);
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
