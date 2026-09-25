/**
 * test_isolated_scene_prep_service.mjs — Targeted unit tests for isolated Scene preparation service.
 *
 * Covers cases A through M of Card MANGA-ISOLATED-SCENE-PREP-SERVICE1:
 * A. Valid Reference-disabled backend response produces a prepared bundle.
 * B. Exact captured Authoring Document value is sent to backend and saved as snapshot.
 * C. Caller mutation after invocation cannot alter backend request evidence or stored snapshot.
 * D. Returned snapshot digest matches actual saved snapshot bytes.
 * E. Owner document/page/scene IDs come from real plan/document evidence.
 * F. Root and metadata graph digests must agree.
 * G. Root and metadata compile-plan digests must agree.
 * H. Guide-disabled state must be explicit and consistent.
 * I. Active Reference backend result fails with ISOLATED_REFERENCE_UNSUPPORTED and writes ZERO snapshot.
 * J. Missing/malformed Guide evidence fails and writes ZERO snapshot.
 * K. Backend structured failure propagates as preparation failure and writes ZERO snapshot.
 * L. Snapshot persistence failure prevents successful preparation.
 * M. Zero execution side effects (no /prompt, no journal, no PNG/manifest, only injected compile fetch).
 */

import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs/promises";
import path from "node:path";
import os from "node:os";
import { createHash } from "node:crypto";

import { AuthoringSnapshotStore } from "../service/authoring_snapshot_store.mjs";
import {
    IsolatedScenePrepService,
    IsolatedScenePrepError,
    prepareIsolatedScene,
} from "../service/isolated_scene_prep_service.mjs";

function createValidAuthoringDoc(overrides = {}) {
    return {
        schema_id: "TEGAKI_AUTHORING_DOCUMENT",
        schema_version: "1.0.0",
        document_id: "doc_test_uuid_456",
        pages: [
            {
                page_id: "page_1",
                width_px: 1024,
                height_px: 1536,
                scenes: [
                    {
                        scene_id: "scene_1",
                        name: "Panel 1",
                        area: { shape_type: "rect", x: 0.05, y: 0.05, w: 0.90, h: 0.40 },
                    },
                ],
                cast: [],
                character_instances: [],
                guides: [],
            },
        ],
        ...overrides,
    };
}

function createValidBackendCompileResult(overrides = {}) {
    const graphDigest = "a".repeat(64);
    const compilePlanDigest = "b".repeat(64);
    return {
        ok: true,
        plan: {
            owner: {
                document_id: "doc_test_uuid_456",
                page_id: "page_1",
                scene_id: "scene_1",
            },
            scene: {
                scene_id: "scene_1",
                area: { x: 0.05, y: 0.05, w: 0.90, h: 0.40 },
            },
            page_context: {
                page_id: "page_1",
                page_index: 0,
                width_px: 1024,
                height_px: 1536,
            },
            local_canvas: { width: 1024, height: 1024 },
            placement_mapping: {
                page_target_rect: { x: 0.05, y: 0.05, w: 0.90, h: 0.40 },
                local_source_rect: { x: 0, y: 0, w: 1, h: 1 },
                transform: {},
            },
            character_instances: [],
            cast: [],
            reference: {
                enabled: false,
                reference_asset: null,
            },
            guide_state: {
                enabled: false,
                active: false,
            },
        },
        graph: {
            "1": { class_type: "KSampler", inputs: {} },
            "2": { class_type: "SaveImage", inputs: { filename_prefix: "Manga/Playable" } },
        },
        graph_digest: graphDigest,
        save_node_id: "2",
        page_compile_plan: { scenes: ["scene_1"] },
        page_compile_plan_digest: compilePlanDigest,
        compile_metadata: {
            scene_id: "scene_1",
            graph_digest: graphDigest,
            page_id: "page_1",
            page_index: 0,
            reference: {
                enabled: false,
                reference_asset: null,
            },
            guide_state: {
                enabled: false,
                active: false,
            },
            page_compile_plan_digest: compilePlanDigest,
        },
        audit_trail: { compile_step: "done" },
        ...overrides,
    };
}

const defaultGenerationParams = {
    checkpoint_id: "comicBookIllustrious.safetensors",
    sampler_id: "euler",
    scheduler_id: "normal",
    steps: 28,
    cfg: 7.0,
    seed: 123456,
};

test("Case A: Valid Reference-disabled backend response produces a prepared bundle", async () => {
    const tmpDir = await fs.mkdtemp(path.join(os.tmpdir(), "prep-test-a-"));
    try {
        const store = new AuthoringSnapshotStore(tmpDir);
        const fixedId = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa";
        const backendResult = createValidBackendCompileResult();

        const mockFetch = async (url, options) => {
            assert.equal(url, "http://127.0.0.1:8189/tegaki/manga/generation/compile-isolated-scene");
            assert.equal(options.method, "POST");
            return {
                ok: true,
                status: 200,
                json: async () => backendResult,
            };
        };

        const service = new IsolatedScenePrepService({
            snapshotStore: store,
            fetchFn: mockFetch,
            idFactory: () => fixedId,
        });

        const input = {
            authoring_document: createValidAuthoringDoc(),
            scene_id: "scene_1",
            generation_params: defaultGenerationParams,
        };

        const bundle = await service.prepareIsolatedScene(input);

        // Verify bundle structure
        assert.ok(bundle);
        assert.equal(bundle.owner.document_id, "doc_test_uuid_456");
        assert.equal(bundle.owner.page_id, "page_1");
        assert.equal(bundle.owner.scene_id, "scene_1");

        assert.equal(bundle.snapshot.snapshot_id, fixedId);
        assert.equal(bundle.snapshot.snapshot_ref, `snapshots/${fixedId}.json`);
        assert.match(bundle.snapshot.content_digest, /^[0-9a-f]{64}$/);

        assert.deepEqual(bundle.plan, backendResult.plan);
        assert.deepEqual(bundle.graph, backendResult.graph);
        assert.equal(bundle.graph_digest, backendResult.graph_digest);
        assert.equal(bundle.save_node_id, "2");
        assert.deepEqual(bundle.page_compile_plan, backendResult.page_compile_plan);
        assert.equal(bundle.page_compile_plan_digest, backendResult.page_compile_plan_digest);
        assert.deepEqual(bundle.compile_metadata, backendResult.compile_metadata);
        assert.deepEqual(bundle.audit_trail, backendResult.audit_trail);
    } finally {
        await fs.rm(tmpDir, { recursive: true, force: true });
    }
});

test("Case B: Exact captured Authoring Document value is sent to backend and saved as snapshot", async () => {
    const tmpDir = await fs.mkdtemp(path.join(os.tmpdir(), "prep-test-b-"));
    try {
        const store = new AuthoringSnapshotStore(tmpDir);
        const fixedId = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb";
        const doc = createValidAuthoringDoc({ custom_field: "preserve_me" });

        let capturedInFetch = null;
        const mockFetch = async (_url, options) => {
            const body = JSON.parse(options.body);
            capturedInFetch = body.authoring_document;
            return {
                ok: true,
                status: 200,
                json: async () => createValidBackendCompileResult(),
            };
        };

        const service = new IsolatedScenePrepService({
            snapshotStore: store,
            fetchFn: mockFetch,
            idFactory: () => fixedId,
        });

        const bundle = await service.prepareIsolatedScene({
            authoring_document: doc,
            scene_id: "scene_1",
            generation_params: defaultGenerationParams,
        });

        // 1. Sent to backend matches original
        assert.deepEqual(capturedInFetch, doc);

        // 2. Saved snapshot in store matches original
        const loaded = await store.getSnapshot(fixedId);
        assert.deepEqual(loaded.document, doc);
        assert.equal(bundle.snapshot.content_digest, loaded.content_digest);
    } finally {
        await fs.rm(tmpDir, { recursive: true, force: true });
    }
});

test("Case C: Caller mutation after invocation cannot alter backend request evidence or stored snapshot", async () => {
    const tmpDir = await fs.mkdtemp(path.join(os.tmpdir(), "prep-test-c-"));
    try {
        const store = new AuthoringSnapshotStore(tmpDir);
        const fixedId = "cccccccc-cccc-4ccc-8ccc-cccccccccccc";
        const doc = createValidAuthoringDoc();

        let capturedInFetch = null;
        const mockFetch = async (_url, options) => {
            // Simulate delay during which caller might mutate doc
            await new Promise(resolve => setTimeout(resolve, 5));
            const body = JSON.parse(options.body);
            capturedInFetch = body.authoring_document;
            return {
                ok: true,
                status: 200,
                json: async () => createValidBackendCompileResult(),
            };
        };

        const service = new IsolatedScenePrepService({
            snapshotStore: store,
            fetchFn: mockFetch,
            idFactory: () => fixedId,
        });

        const promise = service.prepareIsolatedScene({
            authoring_document: doc,
            scene_id: "scene_1",
            generation_params: defaultGenerationParams,
        });

        // Mutate caller object immediately after invocation
        doc.pages[0].scenes[0].name = "MUTATED_BY_CALLER";
        doc.mutated_field = true;

        const bundle = await promise;

        // Fetch request body must NOT have the mutations
        assert.equal(capturedInFetch.pages[0].scenes[0].name, "Panel 1");
        assert.equal(capturedInFetch.mutated_field, undefined);

        // Stored snapshot must NOT have the mutations
        const loaded = await store.getSnapshot(fixedId);
        assert.equal(loaded.document.pages[0].scenes[0].name, "Panel 1");
        assert.equal(loaded.document.mutated_field, undefined);
    } finally {
        await fs.rm(tmpDir, { recursive: true, force: true });
    }
});

test("Case D: Returned snapshot digest matches actual saved snapshot bytes", async () => {
    const tmpDir = await fs.mkdtemp(path.join(os.tmpdir(), "prep-test-d-"));
    try {
        const store = new AuthoringSnapshotStore(tmpDir);
        const fixedId = "dddddddd-dddd-4ddd-8ddd-dddddddddddd";
        const doc = createValidAuthoringDoc();

        const mockFetch = async () => ({
            ok: true,
            status: 200,
            json: async () => createValidBackendCompileResult(),
        });

        const service = new IsolatedScenePrepService({
            snapshotStore: store,
            fetchFn: mockFetch,
            idFactory: () => fixedId,
        });

        const bundle = await service.prepareIsolatedScene({
            authoring_document: doc,
            scene_id: "scene_1",
            generation_params: defaultGenerationParams,
        });

        const filePath = path.join(tmpDir, `${fixedId}.json`);
        const rawBytes = await fs.readFile(filePath);
        const actualHash = createHash("sha256").update(rawBytes).digest("hex");

        assert.equal(bundle.snapshot.content_digest, actualHash);
    } finally {
        await fs.rm(tmpDir, { recursive: true, force: true });
    }
});

test("Case E: Owner document/page/scene IDs come from real plan/document evidence", async () => {
    const tmpDir = await fs.mkdtemp(path.join(os.tmpdir(), "prep-test-e-"));
    try {
        const store = new AuthoringSnapshotStore(tmpDir);
        const doc = createValidAuthoringDoc({ document_id: "doc_alpha_999" });
        const backendResult = createValidBackendCompileResult();
        backendResult.plan.owner = {
            document_id: "doc_alpha_999",
            page_id: "page_special_77",
            scene_id: "scene_target_42",
        };
        backendResult.compile_metadata.scene_id = "scene_target_42";

        const mockFetch = async () => ({
            ok: true,
            status: 200,
            json: async () => backendResult,
        });

        const service = new IsolatedScenePrepService({
            snapshotStore: store,
            fetchFn: mockFetch,
        });

        const bundle = await service.prepareIsolatedScene({
            authoring_document: doc,
            scene_id: "scene_target_42",
            generation_params: defaultGenerationParams,
        });

        assert.equal(bundle.owner.document_id, "doc_alpha_999");
        assert.equal(bundle.owner.page_id, "page_special_77");
        assert.equal(bundle.owner.scene_id, "scene_target_42");
    } finally {
        await fs.rm(tmpDir, { recursive: true, force: true });
    }
});

test("Case F: Root and metadata graph digests must agree", async () => {
    const tmpDir = await fs.mkdtemp(path.join(os.tmpdir(), "prep-test-f-"));
    try {
        const store = new AuthoringSnapshotStore(tmpDir);
        const backendResult = createValidBackendCompileResult({
            graph_digest: "1111111111111111111111111111111111111111111111111111111111111111",
        });
        backendResult.compile_metadata.graph_digest = "2222222222222222222222222222222222222222222222222222222222222222";

        const mockFetch = async () => ({
            ok: true,
            status: 200,
            json: async () => backendResult,
        });

        const service = new IsolatedScenePrepService({
            snapshotStore: store,
            fetchFn: mockFetch,
        });

        await assert.rejects(
            async () => {
                await service.prepareIsolatedScene({
                    authoring_document: createValidAuthoringDoc(),
                    scene_id: "scene_1",
                    generation_params: defaultGenerationParams,
                });
            },
            err => {
                assert.ok(err instanceof IsolatedScenePrepError);
                assert.equal(err.code, "DIGEST_MISMATCH");
                return true;
            }
        );

        // ZERO snapshots written
        const files = await fs.readdir(tmpDir).catch(() => []);
        assert.equal(files.length, 0);
    } finally {
        await fs.rm(tmpDir, { recursive: true, force: true });
    }
});

test("Case G: Root and metadata compile-plan digests must agree", async () => {
    const tmpDir = await fs.mkdtemp(path.join(os.tmpdir(), "prep-test-g-"));
    try {
        const store = new AuthoringSnapshotStore(tmpDir);
        const backendResult = createValidBackendCompileResult({
            page_compile_plan_digest: "3333333333333333333333333333333333333333333333333333333333333333",
        });
        backendResult.compile_metadata.page_compile_plan_digest = "4444444444444444444444444444444444444444444444444444444444444444";

        const mockFetch = async () => ({
            ok: true,
            status: 200,
            json: async () => backendResult,
        });

        const service = new IsolatedScenePrepService({
            snapshotStore: store,
            fetchFn: mockFetch,
        });

        await assert.rejects(
            async () => {
                await service.prepareIsolatedScene({
                    authoring_document: createValidAuthoringDoc(),
                    scene_id: "scene_1",
                    generation_params: defaultGenerationParams,
                });
            },
            err => {
                assert.ok(err instanceof IsolatedScenePrepError);
                assert.equal(err.code, "DIGEST_MISMATCH");
                return true;
            }
        );

        // ZERO snapshots written
        const files = await fs.readdir(tmpDir).catch(() => []);
        assert.equal(files.length, 0);
    } finally {
        await fs.rm(tmpDir, { recursive: true, force: true });
    }
});

test("Case H: Guide-disabled state must be explicit and consistent", async () => {
    const tmpDir = await fs.mkdtemp(path.join(os.tmpdir(), "prep-test-h-"));
    try {
        const store = new AuthoringSnapshotStore(tmpDir);
        const backendResult = createValidBackendCompileResult();
        // Mismatch between plan guide_state and metadata guide_state
        backendResult.compile_metadata.guide_state = { enabled: true, active: false };

        const mockFetch = async () => ({
            ok: true,
            status: 200,
            json: async () => backendResult,
        });

        const service = new IsolatedScenePrepService({
            snapshotStore: store,
            fetchFn: mockFetch,
        });

        await assert.rejects(
            async () => {
                await service.prepareIsolatedScene({
                    authoring_document: createValidAuthoringDoc(),
                    scene_id: "scene_1",
                    generation_params: defaultGenerationParams,
                });
            },
            err => {
                assert.ok(err instanceof IsolatedScenePrepError);
                assert.equal(err.code, "COMPILE_CONSISTENCY_MISMATCH");
                return true;
            }
        );

        // ZERO snapshots written
        const files = await fs.readdir(tmpDir).catch(() => []);
        assert.equal(files.length, 0);
    } finally {
        await fs.rm(tmpDir, { recursive: true, force: true });
    }
});

test("Case I: Active Reference backend result fails with ISOLATED_REFERENCE_UNSUPPORTED and writes ZERO snapshot", async () => {
    const tmpDir = await fs.mkdtemp(path.join(os.tmpdir(), "prep-test-i-"));
    try {
        const store = new AuthoringSnapshotStore(tmpDir);
        const backendResult = createValidBackendCompileResult();
        backendResult.plan.reference = {
            enabled: true,
            reference_asset: "tegaki_manga_references/heroine_ref_01.png",
        };
        backendResult.compile_metadata.reference = backendResult.plan.reference;

        const mockFetch = async () => ({
            ok: true,
            status: 200,
            json: async () => backendResult,
        });

        const service = new IsolatedScenePrepService({
            snapshotStore: store,
            fetchFn: mockFetch,
        });

        await assert.rejects(
            async () => {
                await service.prepareIsolatedScene({
                    authoring_document: createValidAuthoringDoc(),
                    scene_id: "scene_1",
                    generation_params: defaultGenerationParams,
                });
            },
            err => {
                assert.ok(err instanceof IsolatedScenePrepError);
                assert.equal(err.code, "ISOLATED_REFERENCE_UNSUPPORTED");
                assert.equal(err.status, 422);
                return true;
            }
        );

        // ZERO snapshots written
        const files = await fs.readdir(tmpDir).catch(() => []);
        assert.equal(files.length, 0);
    } finally {
        await fs.rm(tmpDir, { recursive: true, force: true });
    }
});

test("Case J: Missing/malformed Guide evidence fails and writes ZERO snapshot", async () => {
    const tmpDir = await fs.mkdtemp(path.join(os.tmpdir(), "prep-test-j-"));
    try {
        const store = new AuthoringSnapshotStore(tmpDir);

        // 1. Missing guide_state
        const resultMissing = createValidBackendCompileResult();
        delete resultMissing.plan.guide_state;
        resultMissing.compile_metadata.guide_state = null;

        let mockFetch = async () => ({
            ok: true,
            status: 200,
            json: async () => resultMissing,
        });

        let service = new IsolatedScenePrepService({
            snapshotStore: store,
            fetchFn: mockFetch,
        });

        await assert.rejects(
            async () => {
                await service.prepareIsolatedScene({
                    authoring_document: createValidAuthoringDoc(),
                    scene_id: "scene_1",
                    generation_params: defaultGenerationParams,
                });
            },
            err => {
                assert.ok(err instanceof IsolatedScenePrepError);
                assert.equal(err.code, "ISOLATED_GUIDE_STATE_INVALID");
                return true;
            }
        );

        // 2. Active guide_state
        const resultActive = createValidBackendCompileResult();
        resultActive.plan.guide_state = { enabled: true, active: true };
        resultActive.compile_metadata.guide_state = { enabled: true, active: true };

        mockFetch = async () => ({
            ok: true,
            status: 200,
            json: async () => resultActive,
        });

        service = new IsolatedScenePrepService({
            snapshotStore: store,
            fetchFn: mockFetch,
        });

        await assert.rejects(
            async () => {
                await service.prepareIsolatedScene({
                    authoring_document: createValidAuthoringDoc(),
                    scene_id: "scene_1",
                    generation_params: defaultGenerationParams,
                });
            },
            err => {
                assert.ok(err instanceof IsolatedScenePrepError);
                assert.equal(err.code, "ISOLATED_GUIDE_STATE_INVALID");
                return true;
            }
        );

        // ZERO snapshots written
        const files = await fs.readdir(tmpDir).catch(() => []);
        assert.equal(files.length, 0);
    } finally {
        await fs.rm(tmpDir, { recursive: true, force: true });
    }
});

test("Case K: Backend structured failure propagates as preparation failure and writes ZERO snapshot", async () => {
    const tmpDir = await fs.mkdtemp(path.join(os.tmpdir(), "prep-test-k-"));
    try {
        const store = new AuthoringSnapshotStore(tmpDir);

        const mockFetch = async () => ({
            ok: false,
            status: 422,
            json: async () => ({
                ok: false,
                error_code: "SCENE_NOT_FOUND",
                error: "Scene 'scene_nonexistent' not found in any page of the document",
            }),
        });

        const service = new IsolatedScenePrepService({
            snapshotStore: store,
            fetchFn: mockFetch,
        });

        await assert.rejects(
            async () => {
                await service.prepareIsolatedScene({
                    authoring_document: createValidAuthoringDoc(),
                    scene_id: "scene_nonexistent",
                    generation_params: defaultGenerationParams,
                });
            },
            err => {
                assert.ok(err instanceof IsolatedScenePrepError);
                assert.equal(err.code, "SCENE_NOT_FOUND");
                assert.equal(err.status, 422);
                assert.match(err.message, /Scene 'scene_nonexistent' not found/);
                return true;
            }
        );

        // ZERO snapshots written
        const files = await fs.readdir(tmpDir).catch(() => []);
        assert.equal(files.length, 0);
    } finally {
        await fs.rm(tmpDir, { recursive: true, force: true });
    }
});

test("Case L: Snapshot persistence failure prevents successful preparation", async () => {
    const failingStore = {
        saveSnapshot: async () => {
            throw new Error("Simulated disk I/O error during snapshot save");
        },
    };

    const mockFetch = async () => ({
        ok: true,
        status: 200,
        json: async () => createValidBackendCompileResult(),
    });

    const service = new IsolatedScenePrepService({
        snapshotStore: failingStore,
        fetchFn: mockFetch,
    });

    await assert.rejects(
        async () => {
            await service.prepareIsolatedScene({
                authoring_document: createValidAuthoringDoc(),
                scene_id: "scene_1",
                generation_params: defaultGenerationParams,
            });
        },
        err => {
            assert.ok(err instanceof IsolatedScenePrepError);
            assert.equal(err.code, "SNAPSHOT_SAVE_FAILED");
            assert.equal(err.status, 500);
            assert.match(err.message, /Simulated disk I\/O error/);
            return true;
        }
    );
});

test("Case M: Zero execution side effects", async () => {
    const tmpDir = await fs.mkdtemp(path.join(os.tmpdir(), "prep-test-m-"));
    try {
        const store = new AuthoringSnapshotStore(tmpDir);
        const fetchCalls = [];

        const mockFetch = async (url, options) => {
            fetchCalls.push({ url, method: options.method });
            return {
                ok: true,
                status: 200,
                json: async () => createValidBackendCompileResult(),
            };
        };

        const service = new IsolatedScenePrepService({
            snapshotStore: store,
            fetchFn: mockFetch,
        });

        const bundle = await service.prepareIsolatedScene({
            authoring_document: createValidAuthoringDoc(),
            scene_id: "scene_1",
            generation_params: defaultGenerationParams,
        });

        // 1. Only ONE fetch call made, and only to /compile-isolated-scene
        assert.equal(fetchCalls.length, 1);
        assert.equal(fetchCalls[0].url, "http://127.0.0.1:8189/tegaki/manga/generation/compile-isolated-scene");
        assert.equal(fetchCalls[0].method, "POST");

        // 2. Output bundle has no job_id, prompt_id, manifest_id, or artifact locator
        assert.equal(bundle.job_id, undefined);
        assert.equal(bundle.prompt_id, undefined);
        assert.equal(bundle.manifest_id, undefined);
        assert.equal(bundle.output_locator, undefined);

        // 3. Only snapshot store file exists, no generation journal or PNG outputs
        const files = await fs.readdir(tmpDir);
        assert.equal(files.length, 1);
        assert.match(files[0], /^[0-9a-f-]{36}\.json$/);
    } finally {
        await fs.rm(tmpDir, { recursive: true, force: true });
    }
});

test("Convenience export prepareIsolatedScene works as expected", async () => {
    const tmpDir = await fs.mkdtemp(path.join(os.tmpdir(), "prep-test-conv-"));
    try {
        const store = new AuthoringSnapshotStore(tmpDir);
        const mockFetch = async () => ({
            ok: true,
            status: 200,
            json: async () => createValidBackendCompileResult(),
        });

        const bundle = await prepareIsolatedScene(
            {
                authoring_document: createValidAuthoringDoc(),
                scene_id: "scene_1",
                generation_params: defaultGenerationParams,
            },
            {
                snapshotStore: store,
                fetchFn: mockFetch,
            }
        );

        assert.ok(bundle);
        assert.equal(bundle.owner.scene_id, "scene_1");
    } finally {
        await fs.rm(tmpDir, { recursive: true, force: true });
    }
});
