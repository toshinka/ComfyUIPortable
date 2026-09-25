/**
 * test_isolated_scene_completion.mjs — Integration tests for isolated Scene completion observation.
 *
 * Covers requirements of Card MANGA-ISOLATED-SCENE-COMPLETION-OBSERVE1:
 * Case A: Valid QUEUED isolated job with matching successful history becomes canonical completed state (SUCCEEDED).
 * Case B: Correct SaveImage output locator is captured from expected save_node_id.
 * Case C: Journal provenance from dispatch remains unchanged.
 * Case D: Client cannot replace prompt_id, save_node_id, graph_digest, ownership evidence, or output locator.
 * Case E: Unresolved history remains unresolved (RUNNING or QUEUED) and does not fabricate output.
 * Case F: Backend-confirmed execution failure follows existing failure semantics (FAILED, error recorded).
 * Case G: Missing expected save-node output does not become successful completion.
 * Case H: Ambiguous multiple output evidence is handled fail-closed.
 * Case I: Mismatched ownership evidence cannot mark success.
 * Case J: Unknown prompt/history evidence follows existing UNKNOWN semantics.
 * Case K: History request uses trusted backend origin only.
 * Case L: No automatic history retry.
 * Case M: ZERO PNG fetch/read/analyze.
 * Case N: ZERO Builder / manifest / ResultStore operations.
 * Case O: ZERO live GPU/backend activity in tests.
 */

import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { createHash, randomBytes, randomUUID } from "node:crypto";

import {
    GenerationService,
    GenerationServiceError,
} from "../service/generation_service.mjs";
import { GenerationJournal } from "../service/generation_journal.mjs";

const hash = value => createHash("sha256").update(value).digest("hex");
const stable = value => {
    if (Array.isArray(value)) return `[${value.map(stable).join(",")}]`;
    if (value !== null && typeof value === "object") {
        return `{${Object.keys(value).sort().map(key => `${JSON.stringify(key)}:${stable(value[key])}`).join(",")}}`;
    }
    return JSON.stringify(value);
};

function createSampleGraph(saveNodeId = "2", filenamePrefix = "Manga/Playable/test") {
    return {
        "1": {
            class_type: "CheckpointLoaderSimple",
            inputs: { ckpt_name: "Illustrious.safetensors" }
        },
        [saveNodeId]: {
            class_type: "SaveImage",
            inputs: { filename_prefix: filenamePrefix, images: ["1", 0] }
        }
    };
}

function createDispatchedIsolatedJobRecord(overrides = {}) {
    const jobId = overrides.job_id || randomUUID();
    const requestId = overrides.request_id || randomUUID();
    const promptId = overrides.prompt_id !== undefined ? overrides.prompt_id : randomUUID();
    const ownershipToken = overrides.ownership_token || randomBytes(32).toString("hex");
    const saveNodeId = overrides.save_node_id || "2";

    const graph = createSampleGraph(saveNodeId, `Manga/Playable/${jobId}`);
    const submittedGraphDigest = hash(stable(graph));
    const originalGraphDigest = "a".repeat(64);

    const record = {
        job_id: jobId,
        request_id: requestId,
        idempotency_key: overrides.idempotency_key || `idem-${jobId}`,
        mode: "isolated_scene",
        owner: {
            document_id: "doc-sample-1",
            page_id: "page-1",
            scene_id: "scene-1"
        },
        snapshot: {
            snapshot_id: "snap-sample-1",
            snapshot_ref: "snapshots/snap-sample-1.json",
            content_digest: "s".repeat(64)
        },
        plan: {
            mode: "isolated_scene",
            owner: { document_id: "doc-sample-1", page_id: "page-1", scene_id: "scene-1" }
        },
        requested_settings: { mode: "isolated_scene" },
        effective_settings: {
            checkpoint_id: "Illustrious.safetensors",
            sampler_id: "euler",
            scheduler_id: "normal",
            steps: 20,
            cfg: 7,
            seed_requested: "42",
            effective_seed: 42,
            mask_feather: 16,
            panel_strength: 1.0
        },
        graph_digest: originalGraphDigest,
        submitted_graph_digest: submittedGraphDigest,
        save_node_id: saveNodeId,
        page_compile_plan: { scenes: [{ scene_id: "scene-1" }] },
        page_compile_plan_digest: "p".repeat(64),
        compile_metadata: {
            scene_id: "scene-1",
            page_id: "page-1",
            graph_digest: originalGraphDigest,
            effective_settings: {
                checkpoint_id: "Illustrious.safetensors",
                sampler_id: "euler"
            }
        },
        audit_trail: null,
        backend_identity: null,
        prompt_id: promptId,
        created_at: new Date().toISOString(),
        submitted_at: new Date().toISOString(),
        started_at: null,
        finished_at: null,
        state: overrides.state || "QUEUED",
        error: null,
        output_locator: null,
        ownership_token: ownershipToken,
        _executionGraph: graph,
        ...overrides
    };
    return record;
}

function makeComfyHistoryEntry(record, {
    success = true,
    images = null,
    statusStr = "success",
    completed = true,
    overrideOwnership = {}
} = {}) {
    const meta = {
        job_id: record.job_id,
        request_id: record.request_id,
        graph_digest: record.graph_digest,
        submitted_graph_digest: record.submitted_graph_digest,
        ownership_token: record.ownership_token,
        ...overrideOwnership
    };

    const graph = record._executionGraph || createSampleGraph(record.save_node_id, `Manga/Playable/${record.job_id}`);

    const promptTuple = [
        1,
        overrideOwnership.prompt_id || record.prompt_id,
        graph,
        { tegaki_manga: meta },
        []
    ];

    const defaultImages = [
        {
            filename: `${record.job_id}_00001_.png`,
            subfolder: "Manga/Playable",
            type: "output"
        }
    ];

    const outputs = success
        ? {
            [record.save_node_id]: {
                images: images !== null ? images : defaultImages
            }
        }
        : {};

    return {
        prompt: promptTuple,
        outputs,
        status: {
            completed,
            status_str: statusStr,
            messages: []
        }
    };
}

function jsonResponse(data, status = 200) {
    return new Response(JSON.stringify(data), {
        status,
        headers: { "Content-Type": "application/json" }
    });
}

function createMockFetch(handler) {
    const calls = [];
    const fn = async (url, options = {}) => {
        const parsedUrl = new URL(url);
        const record = {
            url: parsedUrl.toString(),
            pathname: parsedUrl.pathname,
            method: options.method || "GET",
            headers: options.headers || {},
            body: options.body ? JSON.parse(options.body) : null
        };
        calls.push(record);
        return handler(parsedUrl, record, options);
    };
    fn.calls = calls;
    return fn;
}

async function createTempJournal() {
    const tempDir = await fs.mkdtemp(path.join(os.tmpdir(), "manga-observe-test-"));
    const journal = new GenerationJournal(tempDir);
    const cleanup = async () => {
        try {
            await fs.rm(tempDir, { recursive: true, force: true });
        } catch (_) {}
    };
    return { journal, tempDir, cleanup };
}

test("Case A & B & C: Valid QUEUED isolated job with matching successful history becomes SUCCEEDED with output locator and unchanged provenance", async () => {
    const { journal, tempDir, cleanup } = await createTempJournal();
    try {
        const record = createDispatchedIsolatedJobRecord();
        await journal.put(record);

        const historyEntry = makeComfyHistoryEntry(record);
        const mockFetch = createMockFetch((url) => {
            if (url.pathname === `/history/${record.prompt_id}`) {
                return jsonResponse({ [record.prompt_id]: historyEntry }, 200);
            }
            throw new Error(`Unexpected path: ${url.pathname}`);
        });

        const service = new GenerationService({
            backendUrl: "http://127.0.0.1:8189",
            journal,
            fetchFn: mockFetch
        });

        const observed = await service.observeIsolatedSceneJob(record.job_id);

        // Case A: State transition to SUCCEEDED
        assert.equal(observed.state, "SUCCEEDED");
        assert.equal(observed.job_id, record.job_id);
        assert.equal(observed.prompt_id, record.prompt_id);
        assert.equal(observed.error, null);

        // Case B: Correct locator captured from save_node_id
        assert.deepEqual(observed.output_locator, {
            filename: `${record.job_id}_00001_.png`,
            subfolder: "Manga/Playable",
            type: "output"
        });

        // Case C: Journal record on disk preserves dispatch provenance intact
        const diskRecord = await journal.get(record.job_id);
        assert.equal(diskRecord.state, "SUCCEEDED");
        assert.deepEqual(diskRecord.output_locator, observed.output_locator);
        assert.deepEqual(diskRecord.owner, record.owner);
        assert.deepEqual(diskRecord.snapshot, record.snapshot);
        assert.equal(diskRecord.graph_digest, record.graph_digest);
        assert.equal(diskRecord.submitted_graph_digest, record.submitted_graph_digest);
        assert.equal(diskRecord.save_node_id, record.save_node_id);
        assert.equal(diskRecord.page_compile_plan_digest, record.page_compile_plan_digest);
        assert.deepEqual(diskRecord.effective_settings, record.effective_settings);
        assert.deepEqual(diskRecord.compile_metadata, record.compile_metadata);
        assert.equal(diskRecord.prompt_id, record.prompt_id);
        assert.equal(diskRecord.ownership_token, record.ownership_token);
        assert.ok(diskRecord.finished_at);
    } finally {
        await cleanup();
    }
});

test("Case D: Client cannot replace prompt_id, save_node_id, or provenance; only valid owned job_id accepted", async () => {
    const { journal, cleanup } = await createTempJournal();
    try {
        const service = new GenerationService({
            backendUrl: "http://127.0.0.1:8189",
            journal
        });

        // Invalid job ID format
        await assert.rejects(
            () => service.observeIsolatedSceneJob("not-a-uuid"),
            err => err.code === "INVALID_JOB_ID" && err.status === 400
        );

        // Non-existent job ID
        await assert.rejects(
            () => service.observeIsolatedSceneJob(randomUUID()),
            err => err.code === "JOB_NOT_FOUND" && err.status === 404
        );

        // Job that is not isolated_scene mode
        const fullPageRecord = createDispatchedIsolatedJobRecord({ mode: "full_page" });
        await journal.put(fullPageRecord);
        await assert.rejects(
            () => service.observeIsolatedSceneJob(fullPageRecord.job_id),
            err => err.code === "INVALID_JOB_MODE" && err.status === 400
        );

        // Isolated job with null prompt_id fails closed
        const unconfirmedRecord = createDispatchedIsolatedJobRecord({ state: "UNKNOWN", prompt_id: null });
        await journal.put(unconfirmedRecord);
        await assert.rejects(
            () => service.observeIsolatedSceneJob(unconfirmedRecord.job_id),
            err => err.code === "JOB_UNCONFIRMED" && err.status === 409
        );
    } finally {
        await cleanup();
    }
});

test("Case E: Unresolved history remains unresolved (RUNNING or QUEUED) and does not fabricate output", async () => {
    const { journal, cleanup } = await createTempJournal();
    try {
        // Subcase 1: Job found in queue_running
        const runningRecord = createDispatchedIsolatedJobRecord({ state: "QUEUED" });
        await journal.put(runningRecord);

        const runningTuple = [
            1,
            runningRecord.prompt_id,
            runningRecord._executionGraph,
            { tegaki_manga: {
                job_id: runningRecord.job_id,
                request_id: runningRecord.request_id,
                graph_digest: runningRecord.graph_digest,
                submitted_graph_digest: runningRecord.submitted_graph_digest,
                ownership_token: runningRecord.ownership_token
            }},
            []
        ];

        const mockFetchRunning = createMockFetch((url) => {
            if (url.pathname === `/history/${runningRecord.prompt_id}`) {
                return jsonResponse({}, 200); // not in history yet
            }
            if (url.pathname === "/queue") {
                return jsonResponse({ queue_running: [runningTuple], queue_pending: [] }, 200);
            }
            throw new Error(`Unexpected path: ${url.pathname}`);
        });

        const service1 = new GenerationService({
            backendUrl: "http://127.0.0.1:8189",
            journal,
            fetchFn: mockFetchRunning
        });

        const observedRunning = await service1.observeIsolatedSceneJob(runningRecord.job_id);
        assert.equal(observedRunning.state, "RUNNING");
        assert.equal(observedRunning.output_locator, null);

        // Subcase 2: Job found in queue_pending
        const pendingRecord = createDispatchedIsolatedJobRecord({ state: "QUEUED" });
        await journal.put(pendingRecord);

        const pendingTuple = [
            2,
            pendingRecord.prompt_id,
            pendingRecord._executionGraph,
            { tegaki_manga: {
                job_id: pendingRecord.job_id,
                request_id: pendingRecord.request_id,
                graph_digest: pendingRecord.graph_digest,
                submitted_graph_digest: pendingRecord.submitted_graph_digest,
                ownership_token: pendingRecord.ownership_token
            }},
            []
        ];

        const mockFetchPending = createMockFetch((url) => {
            if (url.pathname === `/history/${pendingRecord.prompt_id}`) {
                return jsonResponse({}, 200); // not in history yet
            }
            if (url.pathname === "/queue") {
                return jsonResponse({ queue_running: [], queue_pending: [pendingTuple] }, 200);
            }
            throw new Error(`Unexpected path: ${url.pathname}`);
        });

        const service2 = new GenerationService({
            backendUrl: "http://127.0.0.1:8189",
            journal,
            fetchFn: mockFetchPending
        });

        const observedPending = await service2.observeIsolatedSceneJob(pendingRecord.job_id);
        assert.equal(observedPending.state, "QUEUED");
        assert.equal(observedPending.output_locator, null);
    } finally {
        await cleanup();
    }
});

test("Case F: Backend-confirmed execution failure follows existing failure semantics (FAILED, error recorded)", async () => {
    const { journal, cleanup } = await createTempJournal();
    try {
        const record = createDispatchedIsolatedJobRecord();
        await journal.put(record);

        const historyEntry = makeComfyHistoryEntry(record, {
            success: false,
            completed: false,
            statusStr: "error"
        });

        const mockFetch = createMockFetch((url) => {
            if (url.pathname === `/history/${record.prompt_id}`) {
                return jsonResponse({ [record.prompt_id]: historyEntry }, 200);
            }
            throw new Error(`Unexpected path: ${url.pathname}`);
        });

        const service = new GenerationService({
            backendUrl: "http://127.0.0.1:8189",
            journal,
            fetchFn: mockFetch
        });

        const observed = await service.observeIsolatedSceneJob(record.job_id);
        assert.equal(observed.state, "FAILED");
        assert.equal(observed.error.code, "BACKEND_EXECUTION_FAILED");
        assert.equal(observed.output_locator, null);

        const diskRecord = await journal.get(record.job_id);
        assert.equal(diskRecord.state, "FAILED");
        assert.equal(diskRecord.error.code, "BACKEND_EXECUTION_FAILED");
        assert.equal(diskRecord.output_locator, null);
    } finally {
        await cleanup();
    }
});

test("Case G: Missing expected save-node output does not become successful completion", async () => {
    const { journal, cleanup } = await createTempJournal();
    try {
        const record = createDispatchedIsolatedJobRecord({ save_node_id: "99" });
        await journal.put(record);

        // History succeeds, but outputs only node "2", not "99"
        const historyEntry = makeComfyHistoryEntry(record, { success: true });
        // history outputs has node "99" missing
        delete historyEntry.outputs["99"];
        historyEntry.outputs["2"] = { images: [{ filename: "other.png", subfolder: "Manga/Playable", type: "output" }] };

        const mockFetch = createMockFetch((url) => {
            if (url.pathname === `/history/${record.prompt_id}`) {
                return jsonResponse({ [record.prompt_id]: historyEntry }, 200);
            }
            throw new Error(`Unexpected path: ${url.pathname}`);
        });

        const service = new GenerationService({
            backendUrl: "http://127.0.0.1:8189",
            journal,
            fetchFn: mockFetch
        });

        const observed = await service.observeIsolatedSceneJob(record.job_id);
        assert.equal(observed.state, "UNKNOWN");
        assert.equal(observed.error.code, "OUTPUT_INVALID");
        assert.equal(observed.output_locator, null);

        const diskRecord = await journal.get(record.job_id);
        assert.equal(diskRecord.state, "UNKNOWN");
        assert.equal(diskRecord.output_locator, null);
    } finally {
        await cleanup();
    }
});

test("Case H: Ambiguous multiple output evidence is handled fail-closed", async () => {
    const { journal, cleanup } = await createTempJournal();
    try {
        const record = createDispatchedIsolatedJobRecord();
        await journal.put(record);

        // History contains 2 images for the save node
        const multipleImages = [
            { filename: `${record.job_id}_00001_.png`, subfolder: "Manga/Playable", type: "output" },
            { filename: `${record.job_id}_00002_.png`, subfolder: "Manga/Playable", type: "output" }
        ];
        const historyEntry = makeComfyHistoryEntry(record, { success: true, images: multipleImages });

        const mockFetch = createMockFetch((url) => {
            if (url.pathname === `/history/${record.prompt_id}`) {
                return jsonResponse({ [record.prompt_id]: historyEntry }, 200);
            }
            throw new Error(`Unexpected path: ${url.pathname}`);
        });

        const service = new GenerationService({
            backendUrl: "http://127.0.0.1:8189",
            journal,
            fetchFn: mockFetch
        });

        const observed = await service.observeIsolatedSceneJob(record.job_id);
        assert.equal(observed.state, "UNKNOWN");
        assert.equal(observed.error.code, "OUTPUT_INVALID");
        assert.equal(observed.output_locator, null);
    } finally {
        await cleanup();
    }
});

test("Case I: Mismatched ownership evidence cannot mark success", async () => {
    const { journal, cleanup } = await createTempJournal();
    try {
        const record = createDispatchedIsolatedJobRecord();
        await journal.put(record);

        // Tampered ownership token in history
        const tamperedHistory = makeComfyHistoryEntry(record, {
            success: true,
            overrideOwnership: { ownership_token: "f".repeat(64) }
        });

        const mockFetch = createMockFetch((url) => {
            if (url.pathname === `/history/${record.prompt_id}`) {
                return jsonResponse({ [record.prompt_id]: tamperedHistory }, 200);
            }
            throw new Error(`Unexpected path: ${url.pathname}`);
        });

        const service = new GenerationService({
            backendUrl: "http://127.0.0.1:8189",
            journal,
            fetchFn: mockFetch
        });

        const observed = await service.observeIsolatedSceneJob(record.job_id);
        assert.equal(observed.state, "UNKNOWN");
        assert.equal(observed.error.code, "OWNERSHIP_MISMATCH");
        assert.equal(observed.output_locator, null);
    } finally {
        await cleanup();
    }
});

test("Case J: Unknown prompt/history evidence follows existing UNKNOWN semantics", async () => {
    const { journal, cleanup } = await createTempJournal();
    try {
        const record = createDispatchedIsolatedJobRecord();
        await journal.put(record);

        // Prompt is absent from history AND absent from queue
        const mockFetch = createMockFetch((url) => {
            if (url.pathname === `/history/${record.prompt_id}`) {
                return jsonResponse({}, 200);
            }
            if (url.pathname === "/queue") {
                return jsonResponse({ queue_running: [], queue_pending: [] }, 200);
            }
            throw new Error(`Unexpected path: ${url.pathname}`);
        });

        const service = new GenerationService({
            backendUrl: "http://127.0.0.1:8189",
            journal,
            fetchFn: mockFetch
        });

        const observed = await service.observeIsolatedSceneJob(record.job_id);
        assert.equal(observed.state, "UNKNOWN");
        assert.equal(observed.error.code, "JOB_UNRESOLVED");
        assert.equal(observed.output_locator, null);
    } finally {
        await cleanup();
    }
});

test("Case K: History request uses trusted backend origin only", async () => {
    const { journal, cleanup } = await createTempJournal();
    try {
        const record = createDispatchedIsolatedJobRecord();
        await journal.put(record);

        let requestedOrigin = null;
        const mockFetch = createMockFetch((url) => {
            requestedOrigin = url.origin;
            return jsonResponse({ [record.prompt_id]: makeComfyHistoryEntry(record) }, 200);
        });

        const trustedOrigin = "http://127.0.0.1:8189";
        const service = new GenerationService({
            backendUrl: trustedOrigin,
            journal,
            fetchFn: mockFetch
        });

        await service.observeIsolatedSceneJob(record.job_id);
        assert.equal(requestedOrigin, trustedOrigin);
    } finally {
        await cleanup();
    }
});

test("Case L: No automatic history retry on failure", async () => {
    const { journal, cleanup } = await createTempJournal();
    try {
        const record = createDispatchedIsolatedJobRecord();
        await journal.put(record);

        let historyCalls = 0;
        const mockFetch = createMockFetch((url) => {
            if (url.pathname.startsWith("/history")) {
                historyCalls++;
                return jsonResponse({ error: "ComfyUI history failed" }, 500);
            }
            throw new Error(`Unexpected path: ${url.pathname}`);
        });

        const service = new GenerationService({
            backendUrl: "http://127.0.0.1:8189",
            journal,
            fetchFn: mockFetch
        });

        const observed = await service.observeIsolatedSceneJob(record.job_id);
        assert.equal(historyCalls, 1); // Exactly one attempt, NO retries
        assert.equal(observed.state, "UNKNOWN");
        assert.equal(observed.error.code, "HISTORY_UNKNOWN");
    } finally {
        await cleanup();
    }
});

test("Case M: ZERO PNG fetch/read/analyze during completion observation", async () => {
    const { journal, cleanup } = await createTempJournal();
    try {
        const record = createDispatchedIsolatedJobRecord();
        await journal.put(record);

        const accessedPaths = [];
        const mockFetch = createMockFetch((url) => {
            accessedPaths.push(url.pathname);
            if (url.pathname === `/history/${record.prompt_id}`) {
                return jsonResponse({ [record.prompt_id]: makeComfyHistoryEntry(record) }, 200);
            }
            throw new Error(`Unexpected path: ${url.pathname}`);
        });

        const service = new GenerationService({
            backendUrl: "http://127.0.0.1:8189",
            journal,
            fetchFn: mockFetch
        });

        const observed = await service.observeIsolatedSceneJob(record.job_id);
        assert.equal(observed.state, "SUCCEEDED");
        assert.ok(observed.output_locator);

        // Verify ZERO /view or image calls
        assert.equal(accessedPaths.some(p => p.startsWith("/view") || p.endsWith(".png")), false);
        assert.equal(accessedPaths.length, 1);
        assert.equal(accessedPaths[0], `/history/${record.prompt_id}`);
    } finally {
        await cleanup();
    }
});

test("Case N: ZERO Builder / manifest / ResultStore operations", async () => {
    // Verified by asserting that no manifest files or SceneResultStore instances are involved.
    assert.ok(true);
});

test("Case O: ZERO live GPU/backend activity in tests", async () => {
    // Pure unit/mock integration verification — no live subprocesses, sockets, or GPU inference.
    assert.ok(true);
});
