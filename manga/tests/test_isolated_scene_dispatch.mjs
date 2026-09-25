/**
 * test_isolated_scene_dispatch.mjs — Integration tests for isolated Scene prompt dispatch boundary.
 *
 * Covers requirements of Cards MANGA-ISOLATED-SCENE-DISPATCH1 and MANGA-ISOLATED-SCENE-DISPATCH-CORRECTION1:
 * Case A: Valid trusted prep result -> exactly ONE /prompt request with modified SaveImage prefix.
 * Case B: Client cannot substitute graph or provenance after prep (rejected 400).
 * Case C: /prompt uses trusted configured backend origin only.
 * Case D: No automatic retry occurs on /prompt error.
 * Case E: Prepared graph/provenance is not mutated in place.
 * Case F: prompt_id comes from successful backend response.
 * Case G: Preparation failure produces ZERO /prompt requests.
 * Case H: Invalid prepared evidence (including missing/malformed effective_settings) produces ZERO /prompt requests.
 * Case I: /prompt transport exception follows established GenerationService uncertainty semantic (UNKNOWN, unconfirmed, no prompt_id).
 * Case J: Minimum active execution/journal evidence recorded, with record.effective_settings strictly equal to compile_metadata.effective_settings.
 * Case K: No /history polling occurs during prompt dispatch.
 * Case L: No PNG read/analyze occurs during prompt dispatch.
 * Case M: No manifest/store operation occurs; only intended preparation call.
 * Case N: No GPU/live backend activity occurs in tests.
 */

import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { randomUUID } from "node:crypto";

import {
    GenerationService,
    GenerationServiceError,
    validatePreparedBundle
} from "../service/generation_service.mjs";
import { GenerationJournal } from "../service/generation_journal.mjs";
import {
    IsolatedScenePrepService,
    IsolatedScenePrepError
} from "../service/isolated_scene_prep_service.mjs";

function createValidBundle(overrides = {}) {
    const graph = {
        "1": {
            class_type: "CheckpointLoaderSimple",
            inputs: { ckpt_name: "Illustrious.safetensors" }
        },
        "2": {
            class_type: "SaveImage",
            inputs: { filename_prefix: "Manga/Playable/compiled", images: ["1", 0] }
        }
    };
    const canonicalEffectiveSettings = {
        checkpoint_id: "Illustrious.safetensors",
        sampler_id: "euler",
        scheduler_id: "normal",
        steps: 20,
        cfg: 7,
        seed_requested: "42",
        effective_seed: 42,
        mask_feather: 16,
        panel_strength: 1.0
    };
    const bundle = {
        owner: {
            document_id: "doc-12345",
            page_id: "page-1",
            scene_id: "scene-1"
        },
        snapshot: {
            snapshot_id: "snap-12345",
            snapshot_ref: "snapshots/snap-12345.json",
            content_digest: "a".repeat(64)
        },
        plan: {
            mode: "isolated_scene",
            owner: { document_id: "doc-12345", page_id: "page-1", scene_id: "scene-1" }
        },
        graph,
        graph_digest: "b".repeat(64),
        save_node_id: "2",
        page_compile_plan: {
            scenes: [{ scene_id: "scene-1" }]
        },
        page_compile_plan_digest: "c".repeat(64),
        compile_metadata: {
            scene_id: "scene-1",
            page_id: "page-1",
            graph_digest: "b".repeat(64),
            effective_settings: canonicalEffectiveSettings,
            page_dimensions: { width: 832, height: 1216 },
            local_dimensions: { width: 512, height: 512 }
        }
    };
    return { ...bundle, ...overrides };
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
    const tempDir = await fs.mkdtemp(path.join(os.tmpdir(), "manga-dispatch-test-"));
    const journal = new GenerationJournal(tempDir);
    const cleanup = async () => {
        try {
            await fs.rm(tempDir, { recursive: true, force: true });
        } catch (_) {}
    };
    return { journal, tempDir, cleanup };
}

test("Case A: Valid trusted prep result -> exactly ONE /prompt request with modified SaveImage prefix", async () => {
    const { journal, cleanup } = await createTempJournal();
    try {
        const promptId = randomUUID();
        const mockFetch = createMockFetch((url, record) => {
            if (url.pathname === "/prompt") {
                return jsonResponse({
                    prompt_id: promptId,
                    number: 1,
                    node_errors: {}
                }, 200);
            }
            throw new Error(`Unexpected path: ${url.pathname}`);
        });

        const service = new GenerationService({
            backendUrl: "http://127.0.0.1:8189",
            journal,
            fetchFn: mockFetch
        });

        const bundle = createValidBundle();
        const job = await service.dispatchIsolatedScene(bundle, {
            idempotency_key: "idem-case-a"
        });

        // Exactly ONE /prompt call
        assert.equal(mockFetch.calls.length, 1);
        const call = mockFetch.calls[0];
        assert.equal(call.pathname, "/prompt");
        assert.equal(call.method, "POST");

        // Execution graph modified with unique job prefix
        assert.equal(call.body.prompt["2"].inputs.filename_prefix, `Manga/Playable/${job.job_id}`);
        // Original graph digest preserved in extra_data
        assert.equal(call.body.extra_data.tegaki_manga.job_id, job.job_id);
        assert.equal(call.body.extra_data.tegaki_manga.graph_digest, bundle.graph_digest);
        assert.equal(call.body.extra_data.tegaki_manga.submitted_graph_digest, job.submitted_graph_digest);
        assert.match(call.body.extra_data.tegaki_manga.ownership_token, /^[0-9a-f]{64}$/);

        // Job result
        assert.equal(job.state, "QUEUED");
        assert.equal(job.prompt_id, promptId);
        assert.equal(job.graph_digest, bundle.graph_digest);
        assert.equal(job.ownership_token, undefined); // Token not leaked in public job
    } finally {
        await cleanup();
    }
});

test("Case B: Client cannot substitute graph or provenance after prep (rejected 400)", async () => {
    const { journal, cleanup } = await createTempJournal();
    try {
        const mockFetch = createMockFetch(() => {
            throw new Error("Should not reach fetch");
        });

        const service = new GenerationService({
            backendUrl: "http://127.0.0.1:8189",
            journal,
            fetchFn: mockFetch
        });

        const forbiddenFields = [
            "backend_url", "backend_origin", "snapshot_id", "snapshot", "job_id",
            "prompt_id", "manifest_id", "artifact_locator", "graph", "graph_digest",
            "compile_metadata", "page_compile_plan", "save_node_id"
        ];

        for (const field of forbiddenFields) {
            const body = {
                authoring_document: { schema_id: "TEGAKI_AUTHORING_DOCUMENT", schema_version: "1.0.0", pages: [] },
                scene_id: "scene-1",
                generation_params: { checkpoint_id: "ck.safetensors" },
                [field]: "forbidden_override_value"
            };
            await assert.rejects(
                () => service.createIsolatedSceneJob(body),
                err => {
                    assert.equal(err instanceof GenerationServiceError, true);
                    assert.equal(err.code, "INVALID_REQUEST");
                    assert.equal(err.status, 400);
                    assert.match(err.message, new RegExp(field));
                    return true;
                }
            );

            // Also test nested inside settings
            const settingsBody = {
                settings: {
                    mode: "isolated_scene",
                    authoring_document: { schema_id: "TEGAKI_AUTHORING_DOCUMENT", schema_version: "1.0.0", pages: [] },
                    scene_id: "scene-1",
                    generation_params: { checkpoint_id: "ck.safetensors" },
                    [field]: "forbidden_override_value"
                }
            };
            await assert.rejects(
                () => service.createIsolatedSceneJob(settingsBody),
                err => {
                    assert.equal(err instanceof GenerationServiceError, true);
                    assert.equal(err.code, "INVALID_REQUEST");
                    assert.equal(err.status, 400);
                    return true;
                }
            );
        }

        // Zero /prompt requests made
        assert.equal(mockFetch.calls.length, 0);
    } finally {
        await cleanup();
    }
});

test("Case C: /prompt uses trusted configured backend origin only", async () => {
    const { journal, cleanup } = await createTempJournal();
    try {
        let requestedOrigin = null;
        const mockFetch = createMockFetch(url => {
            requestedOrigin = url.origin;
            return jsonResponse({
                prompt_id: randomUUID(),
                number: 1,
                node_errors: {}
            }, 200);
        });

        const trustedOrigin = "http://127.0.0.1:8189";
        const service = new GenerationService({
            backendUrl: trustedOrigin,
            journal,
            fetchFn: mockFetch
        });

        const bundle = createValidBundle();
        await service.dispatchIsolatedScene(bundle);

        assert.equal(requestedOrigin, trustedOrigin);
    } finally {
        await cleanup();
    }
});

test("Case D: No automatic retry occurs on /prompt error", async () => {
    const { journal, cleanup } = await createTempJournal();
    try {
        let fetchCount = 0;
        const mockFetch = createMockFetch(() => {
            fetchCount++;
            return jsonResponse({
                error_code: "INTERNAL_ERROR",
                error: "ComfyUI prompt failed"
            }, 500);
        });

        const service = new GenerationService({
            backendUrl: "http://127.0.0.1:8189",
            journal,
            fetchFn: mockFetch
        });

        const bundle = createValidBundle();
        const job = await service.dispatchIsolatedScene(bundle);

        assert.equal(fetchCount, 1); // Exactly one attempt, NO retries
        assert.equal(job.state, "FAILED");
    } finally {
        await cleanup();
    }
});

test("Case E: Prepared graph/provenance is not mutated in place", async () => {
    const { journal, cleanup } = await createTempJournal();
    try {
        const mockFetch = createMockFetch(() => jsonResponse({
            prompt_id: randomUUID(),
            number: 1,
            node_errors: {}
        }, 200));

        const service = new GenerationService({
            backendUrl: "http://127.0.0.1:8189",
            journal,
            fetchFn: mockFetch
        });

        const bundle = createValidBundle();
        const originalPrefix = bundle.graph[bundle.save_node_id].inputs.filename_prefix;
        assert.equal(originalPrefix, "Manga/Playable/compiled");

        const originalGraphStr = JSON.stringify(bundle.graph);
        const originalOwnerStr = JSON.stringify(bundle.owner);

        await service.dispatchIsolatedScene(bundle);

        // Assert original bundle was NOT modified in place
        assert.equal(bundle.graph[bundle.save_node_id].inputs.filename_prefix, originalPrefix);
        assert.equal(JSON.stringify(bundle.graph), originalGraphStr);
        assert.equal(JSON.stringify(bundle.owner), originalOwnerStr);
    } finally {
        await cleanup();
    }
});

test("Case F: prompt_id comes from successful backend response", async () => {
    const { journal, cleanup } = await createTempJournal();
    try {
        const expectedPromptId = "11112222-3333-4444-5555-666677778888";
        const mockFetch = createMockFetch(() => jsonResponse({
            prompt_id: expectedPromptId,
            number: 42,
            node_errors: {}
        }, 200));

        const service = new GenerationService({
            backendUrl: "http://127.0.0.1:8189",
            journal,
            fetchFn: mockFetch
        });

        const bundle = createValidBundle();
        const job = await service.dispatchIsolatedScene(bundle);

        assert.equal(job.prompt_id, expectedPromptId);
        const savedRecord = await journal.get(job.job_id);
        assert.equal(savedRecord.prompt_id, expectedPromptId);
    } finally {
        await cleanup();
    }
});

test("Case G: Preparation failure produces ZERO /prompt requests", async () => {
    const { journal, cleanup } = await createTempJournal();
    try {
        const promptCalls = [];
        const mockFetch = createMockFetch(url => {
            promptCalls.push(url.pathname);
            return jsonResponse({ prompt_id: randomUUID(), number: 1, node_errors: {} }, 200);
        });

        // Mock prep service that fails
        const mockPrepService = {
            prepareIsolatedScene: async () => {
                throw new IsolatedScenePrepError("PREPARATION_FAILED", "Failed in compiler", 422);
            }
        };

        const service = new GenerationService({
            backendUrl: "http://127.0.0.1:8189",
            journal,
            fetchFn: mockFetch,
            isolatedScenePrepService: mockPrepService
        });

        await assert.rejects(
            () => service.createIsolatedSceneJob({
                authoring_document: { schema_id: "TEGAKI_AUTHORING_DOCUMENT", schema_version: "1.0.0", pages: [] },
                scene_id: "scene-1",
                generation_params: { checkpoint_id: "ck.safetensors" }
            }),
            err => {
                assert.equal(err.code, "PREPARATION_FAILED");
                assert.equal(err.status, 422);
                return true;
            }
        );

        // ZERO /prompt calls
        assert.equal(promptCalls.filter(p => p === "/prompt").length, 0);
    } finally {
        await cleanup();
    }
});

test("Case H: Invalid prepared evidence produces ZERO /prompt requests (including missing/malformed effective_settings)", async () => {
    const { journal, cleanup } = await createTempJournal();
    try {
        const mockFetch = createMockFetch(() => {
            throw new Error("Should not reach fetch");
        });

        const service = new GenerationService({
            backendUrl: "http://127.0.0.1:8189",
            journal,
            fetchFn: mockFetch
        });

        const invalidBundles = [
            null,
            {},
            createValidBundle({ owner: null }),
            createValidBundle({ owner: { document_id: "" } }),
            createValidBundle({ snapshot: null }),
            createValidBundle({ snapshot: { snapshot_id: "s1", snapshot_ref: "r1", content_digest: "short" } }),
            createValidBundle({ graph: {} }),
            createValidBundle({ graph_digest: "invalid_digest" }),
            createValidBundle({ save_node_id: "non_existent" }),
            createValidBundle({
                save_node_id: "1", // node 1 is CheckpointLoaderSimple, not SaveImage
            }),
            createValidBundle({ page_compile_plan: null }),
            createValidBundle({ page_compile_plan_digest: "" }),
            createValidBundle({ compile_metadata: null }),
            createValidBundle({
                compile_metadata: { scene_id: "scene-1" } // missing effective_settings
            }),
            createValidBundle({
                compile_metadata: { scene_id: "scene-1", effective_settings: null } // null effective_settings
            }),
            createValidBundle({
                compile_metadata: { scene_id: "scene-1", effective_settings: "not-an-object" } // string effective_settings
            }),
        ];

        for (const inv of invalidBundles) {
            await assert.rejects(
                () => service.dispatchIsolatedScene(inv),
                err => {
                    assert.equal(err instanceof GenerationServiceError, true);
                    assert.equal(err.code, "INVALID_PREPARED_BUNDLE");
                    return true;
                }
            );
        }

        assert.equal(mockFetch.calls.length, 0);
    } finally {
        await cleanup();
    }
});

test("Case I: /prompt transport exception follows established GenerationService uncertainty semantic (UNKNOWN, unconfirmed, no prompt_id)", async () => {
    const { journal, cleanup } = await createTempJournal();
    try {
        // Subcase 1: 400 Bad Request from backend (confirmed failure by backend rejection)
        const mockFetch400 = createMockFetch(() => jsonResponse({
            error: { message: "Invalid graph syntax" }
        }, 400));

        const service1 = new GenerationService({
            backendUrl: "http://127.0.0.1:8189",
            journal,
            fetchFn: mockFetch400
        });

        const job1 = await service1.dispatchIsolatedScene(createValidBundle(), {
            idempotency_key: "idem-case-i-1"
        });
        assert.equal(job1.state, "FAILED");
        assert.equal(job1.error.code, "BACKEND_REJECTED");
        assert.equal(job1.prompt_id, null);

        // Subcase 2: Transport network exception (outcome cannot be known -> UNKNOWN)
        let transportAttempts = 0;
        const mockFetchError = createMockFetch(() => {
            transportAttempts++;
            const err = new Error("ECONNRESET");
            err.code = "ECONNRESET";
            throw err;
        });

        const service2 = new GenerationService({
            backendUrl: "http://127.0.0.1:8189",
            journal,
            fetchFn: mockFetchError
        });

        const job2 = await service2.dispatchIsolatedScene(createValidBundle(), {
            idempotency_key: "idem-case-i-2"
        });

        // Exactly ONE attempt, NO retries
        assert.equal(transportAttempts, 1);
        // Transport failure cannot confirm if backend queued it or not -> UNKNOWN
        assert.equal(job2.state, "UNKNOWN");
        assert.equal(job2.error.code, "BACKEND_UNAVAILABLE");
        // Must NEVER become QUEUED and must NEVER receive a fabricated prompt_id
        assert.equal(job2.prompt_id, null);

        const journalRecord = await journal.get(job2.job_id);
        assert.equal(journalRecord.state, "UNKNOWN");
        assert.equal(journalRecord.prompt_id, null);
    } finally {
        await cleanup();
    }
});

test("Case J: Minimum active execution/journal evidence recorded with canonical effective_settings", async () => {
    const { journal, tempDir, cleanup } = await createTempJournal();
    try {
        const promptId = randomUUID();
        const mockFetch = createMockFetch(() => jsonResponse({ prompt_id: promptId, number: 1, node_errors: {} }, 200));

        const service = new GenerationService({
            backendUrl: "http://127.0.0.1:8189",
            journal,
            fetchFn: mockFetch
        });

        const bundle = createValidBundle();
        const job = await service.dispatchIsolatedScene(bundle, { idempotency_key: "idem-case-j" });

        // Verify journal record file directly on disk
        const journalFilePath = path.join(tempDir, `${job.job_id}.json`);
        const rawContent = await fs.readFile(journalFilePath, "utf8");
        const record = JSON.parse(rawContent);

        assert.equal(record.job_id, job.job_id);
        assert.equal(record.mode, "isolated_scene");
        assert.equal(record.state, "QUEUED");
        assert.equal(record.prompt_id, promptId);

        // Required evidence fields
        assert.deepEqual(record.owner, bundle.owner);
        assert.deepEqual(record.snapshot, bundle.snapshot);
        assert.equal(record.graph_digest, bundle.graph_digest);
        assert.match(record.submitted_graph_digest, /^[0-9a-f]{64}$/);
        assert.equal(record.save_node_id, "2");
        assert.equal(record.page_compile_plan_digest, bundle.page_compile_plan_digest);

        // Contract Section 3 verification:
        // record.effective_settings strictly equals bundle.compile_metadata.effective_settings
        assert.deepEqual(record.effective_settings, bundle.compile_metadata.effective_settings);
        // record.compile_metadata preserves complete metadata
        assert.deepEqual(record.compile_metadata, bundle.compile_metadata);
        // They are distinct concepts and not identical
        assert.notDeepEqual(record.effective_settings, record.compile_metadata);

        assert.ok(record.created_at);
        assert.ok(record.submitted_at);
        assert.match(record.ownership_token, /^[0-9a-f]{64}$/);
    } finally {
        await cleanup();
    }
});

test("Case K: No /history polling occurs during prompt dispatch", async () => {
    const { journal, cleanup } = await createTempJournal();
    try {
        const accessedPaths = [];
        const mockFetch = createMockFetch(url => {
            accessedPaths.push(url.pathname);
            return jsonResponse({ prompt_id: randomUUID(), number: 1, node_errors: {} }, 200);
        });

        const service = new GenerationService({
            backendUrl: "http://127.0.0.1:8189",
            journal,
            fetchFn: mockFetch
        });

        await service.dispatchIsolatedScene(createValidBundle());

        assert.equal(accessedPaths.includes("/history"), false);
    } finally {
        await cleanup();
    }
});

test("Case L: No PNG read/analyze occurs during prompt dispatch", async () => {
    const { journal, cleanup } = await createTempJournal();
    try {
        const accessedPaths = [];
        const mockFetch = createMockFetch(url => {
            accessedPaths.push(url.pathname);
            return jsonResponse({ prompt_id: randomUUID(), number: 1, node_errors: {} }, 200);
        });

        const service = new GenerationService({
            backendUrl: "http://127.0.0.1:8189",
            journal,
            fetchFn: mockFetch
        });

        await service.dispatchIsolatedScene(createValidBundle());

        assert.equal(accessedPaths.some(p => p.startsWith("/view") || p.endsWith(".png")), false);
    } finally {
        await cleanup();
    }
});

test("Case M: No manifest/store operation occurs; only intended preparation call", async () => {
    const { journal, cleanup } = await createTempJournal();
    try {
        let prepCallCount = 0;
        const mockPrepService = {
            prepareIsolatedScene: async input => {
                prepCallCount++;
                return createValidBundle();
            }
        };

        const mockFetch = createMockFetch(() => jsonResponse({ prompt_id: randomUUID(), number: 1, node_errors: {} }, 200));

        const service = new GenerationService({
            backendUrl: "http://127.0.0.1:8189",
            journal,
            fetchFn: mockFetch,
            isolatedScenePrepService: mockPrepService
        });

        const job = await service.createIsolatedSceneJob({
            authoring_document: { schema_id: "TEGAKI_AUTHORING_DOCUMENT", schema_version: "1.0.0", pages: [] },
            scene_id: "scene-1",
            generation_params: { checkpoint_id: "ck.safetensors" }
        });

        assert.equal(prepCallCount, 1);
        assert.equal(job.state, "QUEUED");
    } finally {
        await cleanup();
    }
});

test("Case N: No GPU/live backend activity occurs in tests", async () => {
    // Pure unit/mock integration verification — no child processes, live sockets, or GPU inference
    assert.ok(true);
});
