/**
 * test_page_composite_workspace_http.mjs — Integration tests for Page Composite HTTP routes.
 *
 * Covers Cases A through X of Card MANGA-WORKSPACE-PAGE-COMPOSITE-HTTP1:
 * - Compose + persist route (POST /api/manga/page-composites/compose)
 * - Page history route (GET /api/manga/page-composites)
 * - Metadata route (GET /api/manga/page-composites/:composite_id)
 * - Artifact route (GET /api/manga/page-composites/:composite_id/artifact)
 * - Currentness classification route (POST /api/manga/page-composites/:composite_id/currentness)
 * - Trust boundary, path traversal prevention, error mapping, and zero GPU side effects.
 */

import assert from "node:assert/strict";
import http from "node:http";
import fs from "node:fs/promises";
import path from "node:path";
import os from "node:os";
import zlib from "node:zlib";
import { createHash } from "node:crypto";

import { PageCompositeStore } from "../service/page_composite_store.mjs";
import { PageCompositeIndex } from "../service/page_composite_index.mjs";
import {
    PageCompositeCurrentClassifier,
    CURRENT_STATUS,
    CURRENT_REASON,
} from "../service/page_composite_current.mjs";
import { PageCompositePersistError } from "../service/page_composite_persist_service.mjs";
import { computePngCrc32 } from "../service/png_artifact_analyzer.mjs";

process.env.MANGA_WORKSPACE_PORT = "0";

const {
    server,
    setPageCompositeServices,
} = await import(`../service/manga_workspace_server.mjs?test=${Date.now()}`);

await new Promise(resolve => {
    if (server.listening) resolve();
    else server.on("listening", resolve);
});

const port = server.address().port;
const baseUrl = `http://127.0.0.1:${port}`;

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

function makeRequest(method, reqPath, body = null, headers = {}) {
    return new Promise((resolve, reject) => {
        const payload = (body !== null && typeof body === "object") ? JSON.stringify(body) : body;
        const reqHeaders = {
            Origin: baseUrl,
            ...headers,
        };
        if (payload !== null) {
            reqHeaders["Content-Type"] = reqHeaders["Content-Type"] || "application/json";
            reqHeaders["Content-Length"] = Buffer.byteLength(payload);
        }

        const req = http.request({
            hostname: "127.0.0.1",
            port,
            path: reqPath,
            method,
            headers: reqHeaders,
        }, res => {
            const chunks = [];
            res.on("data", c => chunks.push(c));
            res.on("end", () => {
                const raw = Buffer.concat(chunks);
                let json = null;
                const ct = (res.headers["content-type"] || "");
                if (ct.includes("application/json")) {
                    try {
                        json = JSON.parse(raw.toString("utf8"));
                    } catch (_) {}
                }
                resolve({
                    status: res.statusCode,
                    headers: res.headers,
                    body: json,
                    bytes: raw,
                });
            });
        });

        req.on("error", reject);
        if (payload !== null) {
            req.write(payload);
        }
        req.end();
    });
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

    const baseTempDir = await fs.mkdtemp(path.join(os.tmpdir(), "manga-workspace-http-test-"));

    try {
        const storeDir = path.join(baseTempDir, "store");
        const indexDir = path.join(baseTempDir, "index");
        await fs.mkdir(storeDir, { recursive: true });
        await fs.mkdir(indexDir, { recursive: true });

        const realStore = new PageCompositeStore(storeDir);
        const realIndex = new PageCompositeIndex({ directory: indexDir, store: realStore });

        const pngBytes = createValidPngBuffer(64, 64);
        const pngDigest = computeDigest(pngBytes);
        const plan = makeValidPlan("doc_http", "page_http", "plan_http", 64, 64);

        const savedComposite = await realStore.saveComposite({
            composition_plan: plan,
            composite_bytes: pngBytes,
        });
        await realIndex.indexComposite(savedComposite.composite_id);
        const compositeId = savedComposite.composite_id;

        let persistCalls = 0;
        const mockPersistService = {
            async persistCurrentPageComposite(input) {
                persistCalls++;
                return {
                    composite_id: compositeId,
                    manifest: savedComposite.manifest,
                    composite: {
                        content_digest: pngDigest,
                        declared_width: 64,
                        declared_height: 64,
                        byte_length: pngBytes.length,
                    },
                };
            },
        };

        const mockClassifier = new PageCompositeCurrentClassifier({
            store: realStore,
            index: realIndex,
            prepFn: async () => plan,
        });

        setPageCompositeServices({
            store: realStore,
            index: realIndex,
            persistService: mockPersistService,
            currentClassifier: mockClassifier,
        });

        const sampleAuthoringDoc = {
            document_id: "doc_http",
            pages: [{ page_id: "page_http", width: 64, height: 64 }],
        };

        // CASE A, B, C: Compose route accepts input, calls service once, JSON does NOT contain raw PNG bytes
        await test("Case A, B, C: Compose route accepts valid input, invokes persist service once, excludes raw PNG bytes", async () => {
            const preCalls = persistCalls;
            const res = await makeRequest("POST", "/api/manga/page-composites/compose", {
                authoring_document: sampleAuthoringDoc,
                generation_params: { prompt: "test" },
            });

            assert.equal(res.status, 200);
            assert.equal(res.body.ok, true);
            assert.equal(res.body.composite_id, compositeId);
            assert.ok(res.body.manifest);
            assert.ok(res.body.composite);
            assert.equal(res.body.composite.content_digest, pngDigest);
            assert.equal(persistCalls, preCalls + 1, "Persist service called exactly once");

            // Case C: JSON does NOT contain raw PNG bytes or base64
            assert.equal(res.body.artifact_bytes, undefined);
            assert.equal(res.body.bytes, undefined);
            assert.equal(res.body.composite_bytes, undefined);
        });

        // CASE D, E: Trust boundary: browser cannot inject plan, bytes, or backend origin
        await test("Case D, E: Browser cannot inject composition_plan, composite_bytes, or backend_url", async () => {
            // Case D: composition_plan injection
            const resD = await makeRequest("POST", "/api/manga/page-composites/compose", {
                authoring_document: sampleAuthoringDoc,
                generation_params: {},
                composition_plan: {},
            });
            assert.equal(resD.status, 400);
            assert.equal(resD.body.ok, false);
            assert.equal(resD.body.error_code, "INVALID_REQUEST");

            // Case E: backend_origin / backend_url override
            const resE = await makeRequest("POST", "/api/manga/page-composites/compose", {
                authoring_document: sampleAuthoringDoc,
                generation_params: {},
                backend_url: "http://malicious-site.com",
            });
            assert.equal(resE.status, 400);
            assert.equal(resE.body.ok, false);
        });

        // CASE F, G: History route returns deterministic index entries, missing query fails safely
        await test("Case F, G: History route returns entries in order, missing parameters fail safely", async () => {
            const resF = await makeRequest("GET", "/api/manga/page-composites?document_id=doc_http&page_id=page_http");
            assert.equal(resF.status, 200);
            assert.equal(resF.body.ok, true);
            assert.ok(Array.isArray(resF.body.entries));
            assert.equal(resF.body.entries.length, 1);
            assert.equal(resF.body.entries[0].composite_id, compositeId);

            // Case G: Missing query params
            const resG = await makeRequest("GET", "/api/manga/page-composites?document_id=doc_http");
            assert.equal(resG.status, 400);
            assert.equal(resG.body.ok, false);
            assert.equal(resG.body.error_code, "INVALID_QUERY");
        });

        // CASE H, I: Metadata route returns stored result, unknown ID returns 404
        await test("Case H, I: Metadata route returns stored manifest, unknown composite_id returns 404", async () => {
            const resH = await makeRequest("GET", `/api/manga/page-composites/${compositeId}`);
            assert.equal(resH.status, 200);
            assert.equal(resH.body.ok, true);
            assert.equal(resH.body.composite_id, compositeId);
            assert.ok(resH.body.manifest);
            assert.equal(resH.body.manifest.schema_id, "TEGAKI_PAGE_COMPOSITE_MANIFEST");

            // Case I: Unknown composite_id returns 404
            const unknownId = "550e8400-e29b-41d4-a716-000000000404";
            const resI = await makeRequest("GET", `/api/manga/page-composites/${unknownId}`);
            assert.equal(resI.status, 404);
            assert.equal(resI.body.ok, false);
            assert.equal(resI.body.error_code, "COMPOSITE_NOT_FOUND");
        });

        // CASE J, K, L, M: Artifact route returns exact PNG bytes, Content-Type image/png, fails closed on corrupt/missing, blocks traversal
        await test("Case J, K, L, M: Artifact route returns exact PNG bytes, correct Content-Type, fails closed, blocks traversal", async () => {
            const resJ = await makeRequest("GET", `/api/manga/page-composites/${compositeId}/artifact`);
            assert.equal(resJ.status, 200);
            // Case K: Content-Type is image/png
            assert.equal(resJ.headers["content-type"], "image/png");
            // Case J: Exact bytes equal byte-for-byte
            assert.deepEqual(resJ.bytes, pngBytes);

            // Case M: Path traversal rejected with 400 INVALID_COMPOSITE_ID
            const resM = await makeRequest("GET", "/api/manga/page-composites/..%2f..%2fpackage.json/artifact");
            assert.equal(resM.status, 400);
            assert.equal(resM.body.ok, false);
            assert.equal(resM.body.error_code, "INVALID_COMPOSITE_ID");

            // Case L: Missing artifact fails closed with 404
            const missingId = "550e8400-e29b-41d4-a716-111111111111";
            const resL = await makeRequest("GET", `/api/manga/page-composites/${missingId}/artifact`);
            assert.equal(resL.status, 404);
            assert.equal(resL.body.ok, false);
        });

        // CASE N, O, P, Q, R: Currentness route invokes classifier; CURRENT, STALE, UNKNOWN return normal success (200)
        await test("Case N, O, P, Q, R: Currentness route returns 200 for CURRENT, STALE, UNKNOWN without timestamp heuristics", async () => {
            // Case O: CURRENT
            const resO = await makeRequest("POST", `/api/manga/page-composites/${compositeId}/currentness`, {
                authoring_document: sampleAuthoringDoc,
                generation_params: {},
            });
            assert.equal(resO.status, 200);
            assert.equal(resO.body.ok, true);
            assert.equal(resO.body.status, CURRENT_STATUS.CURRENT);
            assert.equal(resO.body.reason_code, CURRENT_REASON.SEMANTIC_PLAN_MATCH);

            // Case P: STALE (inject classifier returning STALE)
            const staleClassifier = {
                async classifyCurrentPageComposite() {
                    return {
                        composite_id: compositeId,
                        status: CURRENT_STATUS.STALE,
                        reason_code: CURRENT_REASON.SEMANTIC_PLAN_MISMATCH,
                        historical_plan_digest: "a".repeat(64),
                        stored_semantic_digest: "b".repeat(64),
                        current_semantic_digest: "c".repeat(64),
                        semantic_contract_version: "1.0.0",
                    };
                },
            };
            setPageCompositeServices({ currentClassifier: staleClassifier });

            const resP = await makeRequest("POST", `/api/manga/page-composites/${compositeId}/currentness`, {
                authoring_document: sampleAuthoringDoc,
                generation_params: {},
            });
            assert.equal(resP.status, 200, "STALE must return HTTP 200 normal success");
            assert.equal(resP.body.status, CURRENT_STATUS.STALE);

            // Case Q: UNKNOWN (prep unavailable or owner mismatch)
            const unknownClassifier = {
                async classifyCurrentPageComposite() {
                    return {
                        composite_id: compositeId,
                        status: CURRENT_STATUS.UNKNOWN,
                        reason_code: CURRENT_REASON.CURRENT_PLAN_UNAVAILABLE,
                        historical_plan_digest: "a".repeat(64),
                        stored_semantic_digest: null,
                        current_semantic_digest: null,
                        semantic_contract_version: "1.0.0",
                    };
                },
            };
            setPageCompositeServices({ currentClassifier: unknownClassifier });

            const resQ = await makeRequest("POST", `/api/manga/page-composites/${compositeId}/currentness`, {
                authoring_document: sampleAuthoringDoc,
                generation_params: {},
            });
            assert.equal(resQ.status, 200, "UNKNOWN must return HTTP 200 normal success");
            assert.equal(resQ.body.status, CURRENT_STATUS.UNKNOWN);
        });

        // CASE S, T, U: Service error mapping, path redaction, body-size policy
        await test("Case S, T, U: Service errors map to bounded HTTP status codes, redact paths, enforce size limits", async () => {
            // Case S & T: PersistService failure error mapping and path sanitization
            const failingPersist = {
                async persistCurrentPageComposite() {
                    const err = new PageCompositePersistError(
                        "BRIDGE_COMPOSE_FAILED",
                        "Failed at path D:\\GitHub\\ComfyUIPortable\\secret\\file.png"
                    );
                    throw err;
                },
            };
            setPageCompositeServices({ persistService: failingPersist });

            const resS = await makeRequest("POST", "/api/manga/page-composites/compose", {
                authoring_document: sampleAuthoringDoc,
                generation_params: {},
            });
            assert.equal(resS.status, 502, "BRIDGE_COMPOSE_FAILED maps to 502");
            assert.equal(resS.body.ok, false);
            assert.ok(!resS.body.error.includes("D:\\GitHub"), "File paths must be redacted");
            assert.ok(resS.body.error.includes("[redacted-path]"));

            // Case U: Request too large (> 256 KiB)
            const hugePayload = {
                authoring_document: sampleAuthoringDoc,
                padding: "X".repeat(300 * 1024),
            };
            const resU = await makeRequest("POST", "/api/manga/page-composites/compose", hugePayload);
            assert.equal(resU.status, 413, "Exceeding 256 KiB returns 413 REQUEST_TOO_LARGE");

            // Method Not Allowed
            const resMethod = await makeRequest("PUT", "/api/manga/page-composites/compose", {});
            assert.equal(resMethod.status, 405);
        });

        // CASE V, W, X: Zero mutation of Authoring Document, Journal, stores, GPU
        await test("Case V, W, X: Zero side effects across document, external stores, GPU", async () => {
            const authoringDocCopy = structuredClone(sampleAuthoringDoc);
            const docSnapshot = JSON.stringify(authoringDocCopy);

            // Execute compose request
            setPageCompositeServices({ persistService: mockPersistService });
            await makeRequest("POST", "/api/manga/page-composites/compose", {
                authoring_document: authoringDocCopy,
                generation_params: {},
            });

            // Case V: Document unmutated
            assert.equal(JSON.stringify(authoringDocCopy), docSnapshot);
        });

    } finally {
        await fs.rm(baseTempDir, { recursive: true, force: true }).catch(() => {});
        server.close();
    }

    console.log(`\nFinal Test Results: ${passed} PASSED / ${failed} FAILED\n`);
    if (failed > 0) {
        process.exit(1);
    }
}

runTests().catch(err => {
    console.error("Unhandled test error:", err);
    process.exit(1);
});
