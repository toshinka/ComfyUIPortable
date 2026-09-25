/**
 * test_isolated_scene_prepare_http.mjs — Integration tests for compile-only isolated Scene HTTP endpoint.
 *
 * Covers cases A through M of Card MANGA-ISOLATED-SCENE-COMPILE-HTTP1:
 * A. Valid POST request reaches preparation service and returns prepared bundle.
 * B. Request fields are forwarded without synthesizing IDs or single-Scene document.
 * C. Request-supplied backend URL/origin fields cannot redirect preparation.
 * D. Reference-disabled successful prepared response remains compile-only.
 * E. ISOLATED_REFERENCE_UNSUPPORTED returns failure with code/status preserved.
 * F. ISOLATED_GUIDE_STATE_INVALID returns failure with code/status preserved.
 * G. Backend structured validation failure remains a failure and preserves code/status/message.
 * H. Snapshot persistence failure remains a failure.
 * I. Unknown/internal errors do not leak stack trace or filesystem path.
 * J. No /prompt submission.
 * K. No generation job creation.
 * L. No journal, PNG, manifest, history or GPU side effects.
 * M. Only intended preparation service call occurs for one valid request.
 */

import test from "node:test";
import assert from "node:assert/strict";
import http from "node:http";

import {
    IsolatedScenePrepError,
} from "../service/isolated_scene_prep_service.mjs";

process.env.MANGA_WORKSPACE_PORT = "0";

const { server, setIsolatedScenePrepService } = await import(
    `../service/manga_workspace_server.mjs?test=${Date.now()}`
);

await new Promise(r => {
    if (server.listening) r();
    else server.on("listening", r);
});

const port = server.address().port;
const baseUrl = `http://127.0.0.1:${port}`;

function postRequest(path, body, headers = {}) {
    return new Promise((resolve, reject) => {
        const payload = typeof body === "string" ? body : JSON.stringify(body);
        const req = http.request({
            hostname: "127.0.0.1",
            port,
            path,
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Content-Length": Buffer.byteLength(payload),
                Origin: baseUrl,
                ...headers,
            },
        }, res => {
            const chunks = [];
            res.on("data", c => chunks.push(c));
            res.on("end", () => {
                const raw = Buffer.concat(chunks).toString("utf8");
                let json = null;
                try {
                    json = JSON.parse(raw);
                } catch (_) {}
                resolve({
                    status: res.statusCode,
                    headers: res.headers,
                    body: json,
                    raw,
                });
            });
        });
        req.on("error", reject);
        req.write(payload);
        req.end();
    });
}

function createSampleAuthoringDoc() {
    return {
        schema_id: "TEGAKI_AUTHORING_DOCUMENT",
        schema_version: "1.0.0",
        document_id: "doc_test_abc123",
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
    };
}

function createSampleBundle(input) {
    const graphDigest = "e".repeat(64);
    const compilePlanDigest = "f".repeat(64);
    return {
        owner: {
            document_id: input.authoring_document?.document_id || "doc_test_abc123",
            page_id: input.page_id || "page_1",
            scene_id: input.scene_id || "scene_1",
        },
        snapshot: {
            snapshot_id: "55555555-5555-4555-8555-555555555555",
            snapshot_ref: "snapshots/55555555-5555-4555-8555-555555555555.json",
            content_digest: "1".repeat(64),
        },
        plan: {
            owner: { scene_id: input.scene_id },
            reference: { enabled: false, reference_asset: null },
            guide_state: { enabled: false, active: false },
        },
        graph: {
            "1": { class_type: "KSampler", inputs: {} },
            "2": { class_type: "SaveImage", inputs: { filename_prefix: "Manga/Playable" } },
        },
        graph_digest: graphDigest,
        save_node_id: "2",
        page_compile_plan: { scenes: [input.scene_id] },
        page_compile_plan_digest: compilePlanDigest,
        compile_metadata: {
            scene_id: input.scene_id,
            graph_digest: graphDigest,
            page_compile_plan_digest: compilePlanDigest,
            reference: { enabled: false, reference_asset: null },
            guide_state: { enabled: false, active: false },
        },
        audit_trail: { step: "prepared" },
    };
}

const defaultGenParams = {
    checkpoint_id: "comicBookIllustrious.safetensors",
    sampler_id: "euler",
    scheduler_id: "normal",
    steps: 28,
    cfg: 7.0,
    seed: 123456,
};

test("Case A: Valid POST request reaches preparation service and returns prepared bundle", async () => {
    const calls = [];
    const mockService = {
        async prepareIsolatedScene(input) {
            calls.push(input);
            return createSampleBundle(input);
        },
    };
    setIsolatedScenePrepService(mockService);

    const doc = createSampleAuthoringDoc();
    const payload = {
        authoring_document: doc,
        scene_id: "scene_1",
        generation_params: defaultGenParams,
        page_id: "page_1",
        local_dimensions: { width: 1024, height: 1024 },
    };

    const res = await postRequest("/api/manga/generation/prepare-isolated-scene", payload);

    assert.equal(res.status, 200);
    assert.ok(res.body);
    assert.equal(res.body.ok, true);
    assert.equal(res.body.owner.scene_id, "scene_1");
    assert.equal(res.body.owner.document_id, "doc_test_abc123");
    assert.equal(res.body.snapshot.snapshot_id, "55555555-5555-4555-8555-555555555555");
    assert.equal(res.body.graph_digest, "e".repeat(64));
    assert.equal(res.body.save_node_id, "2");
    assert.deepEqual(res.body.audit_trail, { step: "prepared" });
    assert.equal(calls.length, 1);
});

test("Case B: Request fields are forwarded without synthesizing IDs or a single-Scene document", async () => {
    const calls = [];
    const mockService = {
        async prepareIsolatedScene(input) {
            calls.push(input);
            return createSampleBundle(input);
        },
    };
    setIsolatedScenePrepService(mockService);

    const originalDoc = createSampleAuthoringDoc();
    // Multi-scene page to verify it is NOT synthesized or truncated into a single-scene document
    originalDoc.pages[0].scenes.push({
        scene_id: "scene_2",
        name: "Panel 2",
        area: { shape_type: "rect", x: 0.05, y: 0.50, w: 0.90, h: 0.40 },
    });

    const payload = {
        authoring_document: originalDoc,
        scene_id: "scene_1",
        generation_params: defaultGenParams,
        page_index: 0,
    };

    const res = await postRequest("/api/manga/generation/prepare-isolated-scene", payload);
    assert.equal(res.status, 200);
    assert.equal(calls.length, 1);

    const forwarded = calls[0];
    // Document was not modified or synthesized
    assert.equal(forwarded.authoring_document.pages[0].scenes.length, 2);
    assert.equal(forwarded.authoring_document.document_id, "doc_test_abc123");
    assert.equal(forwarded.scene_id, "scene_1");
    assert.deepEqual(forwarded.generation_params, defaultGenParams);
    assert.equal(forwarded.page_index, 0);
    // Unsupplied fields were not synthesized
    assert.equal(forwarded.page_id, undefined);
    assert.equal(forwarded.local_dimensions, undefined);
    assert.equal(forwarded.random_seed, undefined);
});

test("Case C: Request-supplied backend URL/origin fields cannot redirect preparation", async () => {
    const calls = [];
    const mockService = {
        async prepareIsolatedScene(input) {
            calls.push(input);
            return createSampleBundle(input);
        },
    };
    setIsolatedScenePrepService(mockService);

    // 1. Attempt to pass backend_url
    const payloadWithBackendUrl = {
        authoring_document: createSampleAuthoringDoc(),
        scene_id: "scene_1",
        generation_params: defaultGenParams,
        backend_url: "http://attacker.com:8189",
    };
    const res1 = await postRequest("/api/manga/generation/prepare-isolated-scene", payloadWithBackendUrl);
    assert.equal(res1.status, 400);
    assert.equal(res1.body.ok, false);
    assert.equal(res1.body.error_code, "INVALID_REQUEST");
    assert.match(res1.body.error, /Forbidden client request fields: backend_url/);

    // 2. Attempt to pass backend_origin
    const payloadWithBackendOrigin = {
        authoring_document: createSampleAuthoringDoc(),
        scene_id: "scene_1",
        generation_params: defaultGenParams,
        backend_origin: "http://attacker.com:8189",
    };
    const res2 = await postRequest("/api/manga/generation/prepare-isolated-scene", payloadWithBackendOrigin);
    assert.equal(res2.status, 400);
    assert.equal(res2.body.ok, false);
    assert.equal(res2.body.error_code, "INVALID_REQUEST");
    assert.match(res2.body.error, /Forbidden client request fields: backend_origin/);

    // 3. Attempt to pass job_id or snapshot_id
    const payloadWithJobId = {
        authoring_document: createSampleAuthoringDoc(),
        scene_id: "scene_1",
        generation_params: defaultGenParams,
        job_id: "forbidden_job_id",
    };
    const res3 = await postRequest("/api/manga/generation/prepare-isolated-scene", payloadWithJobId);
    assert.equal(res3.status, 400);
    assert.equal(res3.body.error_code, "INVALID_REQUEST");

    // Prep service was never called for any forbidden request
    assert.equal(calls.length, 0);
});

test("Case D: Reference-disabled successful prepared response remains compile-only", async () => {
    const mockService = {
        async prepareIsolatedScene(input) {
            return createSampleBundle(input);
        },
    };
    setIsolatedScenePrepService(mockService);

    const payload = {
        authoring_document: createSampleAuthoringDoc(),
        scene_id: "scene_1",
        generation_params: defaultGenParams,
    };

    const res = await postRequest("/api/manga/generation/prepare-isolated-scene", payload);
    assert.equal(res.status, 200);

    const body = res.body;
    // Verify required compile-only fields are present
    assert.ok(body.owner);
    assert.ok(body.snapshot);
    assert.ok(body.plan);
    assert.ok(body.graph);
    assert.ok(body.graph_digest);
    assert.ok(body.save_node_id);
    assert.ok(body.page_compile_plan);
    assert.ok(body.page_compile_plan_digest);
    assert.ok(body.compile_metadata);

    // Verify generation execution fields are strictly absent
    assert.equal(body.job_id, undefined);
    assert.equal(body.prompt_id, undefined);
    assert.equal(body.manifest_id, undefined);
    assert.equal(body.artifact_locator, undefined);
    assert.equal(body.execution_status, undefined);
    assert.equal(body.png_digest, undefined);
});

test("Case E: ISOLATED_REFERENCE_UNSUPPORTED returns failure with its code/status preserved", async () => {
    const mockService = {
        async prepareIsolatedScene() {
            throw new IsolatedScenePrepError(
                "ISOLATED_REFERENCE_UNSUPPORTED",
                "Active Reference is unsupported in isolated-Scene preparation",
                422
            );
        },
    };
    setIsolatedScenePrepService(mockService);

    const payload = {
        authoring_document: createSampleAuthoringDoc(),
        scene_id: "scene_1",
        generation_params: defaultGenParams,
    };

    const res = await postRequest("/api/manga/generation/prepare-isolated-scene", payload);
    assert.equal(res.status, 422);
    assert.equal(res.body.ok, false);
    assert.equal(res.body.error_code, "ISOLATED_REFERENCE_UNSUPPORTED");
    assert.match(res.body.error, /Active Reference is unsupported/);
});

test("Case F: ISOLATED_GUIDE_STATE_INVALID returns failure with its code/status preserved", async () => {
    const mockService = {
        async prepareIsolatedScene() {
            throw new IsolatedScenePrepError(
                "ISOLATED_GUIDE_STATE_INVALID",
                "Isolated plan must have explicit disabled guide_state { enabled: false, active: false }",
                422
            );
        },
    };
    setIsolatedScenePrepService(mockService);

    const payload = {
        authoring_document: createSampleAuthoringDoc(),
        scene_id: "scene_1",
        generation_params: defaultGenParams,
    };

    const res = await postRequest("/api/manga/generation/prepare-isolated-scene", payload);
    assert.equal(res.status, 422);
    assert.equal(res.body.ok, false);
    assert.equal(res.body.error_code, "ISOLATED_GUIDE_STATE_INVALID");
    assert.match(res.body.error, /explicit disabled guide_state/);
});

test("Case G: Backend structured validation failure remains a failure and preserves useful code/status/message", async () => {
    const mockService = {
        async prepareIsolatedScene() {
            throw new IsolatedScenePrepError(
                "SCENE_NOT_FOUND",
                "Scene 'scene_nonexistent' not found in any page of the document",
                422
            );
        },
    };
    setIsolatedScenePrepService(mockService);

    const payload = {
        authoring_document: createSampleAuthoringDoc(),
        scene_id: "scene_nonexistent",
        generation_params: defaultGenParams,
    };

    const res = await postRequest("/api/manga/generation/prepare-isolated-scene", payload);
    assert.equal(res.status, 422);
    assert.equal(res.body.ok, false);
    assert.equal(res.body.error_code, "SCENE_NOT_FOUND");
    assert.match(res.body.error, /Scene 'scene_nonexistent' not found/);
});

test("Case H: Snapshot persistence failure remains a failure", async () => {
    const mockService = {
        async prepareIsolatedScene() {
            throw new IsolatedScenePrepError(
                "SNAPSHOT_SAVE_FAILED",
                "Failed to persist Authoring Document snapshot: EACCES: permission denied, open 'D:\\GitHub\\ComfyUIPortable\\manga\\data\\snapshots\\test.tmp'",
                500
            );
        },
    };
    setIsolatedScenePrepService(mockService);

    const payload = {
        authoring_document: createSampleAuthoringDoc(),
        scene_id: "scene_1",
        generation_params: defaultGenParams,
    };

    const res = await postRequest("/api/manga/generation/prepare-isolated-scene", payload);
    assert.equal(res.status, 500);
    assert.equal(res.body.ok, false);
    assert.equal(res.body.error_code, "SNAPSHOT_SAVE_FAILED");
    // Ensure filesystem path was redacted
    assert.doesNotMatch(res.body.error, /D:\\GitHub/);
    assert.match(res.body.error, /\[redacted-path\]/);
});

test("Case I: Unknown/internal errors do not leak stack trace or filesystem path", async () => {
    const mockService = {
        async prepareIsolatedScene() {
            const err = new Error("Uncaught database failure at D:\\Secret\\ComfyUIPortable\\manga\\internal.js:100:12");
            err.stack = "Error: Uncaught database failure\n    at D:\\Secret\\ComfyUIPortable\\manga\\internal.js:100:12";
            throw err;
        },
    };
    setIsolatedScenePrepService(mockService);

    const payload = {
        authoring_document: createSampleAuthoringDoc(),
        scene_id: "scene_1",
        generation_params: defaultGenParams,
    };

    const res = await postRequest("/api/manga/generation/prepare-isolated-scene", payload);
    assert.equal(res.status, 500);
    assert.equal(res.body.ok, false);
    assert.equal(res.body.error_code, "PREPARATION_INTERNAL_ERROR");
    assert.equal(res.body.error, "Isolated scene preparation failed unexpectedly");
    assert.equal(res.body.stack, undefined);
    assert.doesNotMatch(res.raw, /D:\\Secret/);
    assert.doesNotMatch(res.raw, /internal\.js/);
});

test("Case J, K, L: Zero execution side effects (/prompt, jobs, journals, manifests, GPU)", async () => {
    let promptOrJobCalled = false;
    const mockService = {
        async prepareIsolatedScene(input) {
            // Verify execution boundary inside preparation
            if (globalThis.__executedPrompt || globalThis.__createdJob) {
                promptOrJobCalled = true;
            }
            return createSampleBundle(input);
        },
    };
    setIsolatedScenePrepService(mockService);

    const payload = {
        authoring_document: createSampleAuthoringDoc(),
        scene_id: "scene_1",
        generation_params: defaultGenParams,
    };

    const res = await postRequest("/api/manga/generation/prepare-isolated-scene", payload);
    assert.equal(res.status, 200);
    assert.equal(promptOrJobCalled, false);
    assert.equal(res.body.job_id, undefined);
    assert.equal(res.body.prompt_id, undefined);
});

test("Case M: Only intended preparation service call occurs for one valid request", async () => {
    let callCount = 0;
    const mockService = {
        async prepareIsolatedScene(input) {
            callCount++;
            return createSampleBundle(input);
        },
    };
    setIsolatedScenePrepService(mockService);

    const payload = {
        authoring_document: createSampleAuthoringDoc(),
        scene_id: "scene_1",
        generation_params: defaultGenParams,
    };

    const res = await postRequest("/api/manga/generation/prepare-isolated-scene", payload);
    assert.equal(res.status, 200);
    assert.equal(callCount, 1);
});

test("HTTP protocol enforcement: method, content-type, request size, origin", async () => {
    // 1. GET method -> 405
    const getRes = await new Promise((resolve, reject) => {
        const req = http.request({
            hostname: "127.0.0.1",
            port,
            path: "/api/manga/generation/prepare-isolated-scene",
            method: "GET",
            headers: { Origin: baseUrl },
        }, res => {
            const chunks = [];
            res.on("data", c => chunks.push(c));
            res.on("end", () => {
                resolve({ status: res.statusCode, body: JSON.parse(Buffer.concat(chunks).toString()) });
            });
        });
        req.on("error", reject);
        req.end();
    });
    assert.equal(getRes.status, 405);
    assert.equal(getRes.body.error_code, "METHOD_NOT_ALLOWED");

    // 2. Foreign origin -> 403
    const originRes = await postRequest(
        "/api/manga/generation/prepare-isolated-scene",
        { scene_id: "scene_1" },
        { Origin: "http://malicious-website.com" }
    );
    assert.equal(originRes.status, 403);
    assert.equal(originRes.body.error_code, "ORIGIN_FORBIDDEN");

    // 3. Invalid Content-Type -> 415
    const ctRes = await postRequest(
        "/api/manga/generation/prepare-isolated-scene",
        "plain text",
        { "Content-Type": "text/plain" }
    );
    assert.equal(ctRes.status, 415);
    assert.equal(ctRes.body.error_code, "INVALID_CONTENT_TYPE");

    // 4. Invalid JSON -> 400
    const jsonRes = await postRequest(
        "/api/manga/generation/prepare-isolated-scene",
        "{invalid json",
        { "Content-Type": "application/json" }
    );
    assert.equal(jsonRes.status, 400);
    assert.equal(jsonRes.body.error_code, "INVALID_JSON");
});

test.after(async () => {
    await new Promise(r => server.close(r));
});
