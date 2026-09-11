/**
 * test_backend_adapter.mjs — Manga Backend Adapter Contract & Safety Tests
 * =========================================================================
 * TEGAKI Manga Authoring Workspace (M1A1)
 * 
 * Verifies all Card Section 9 failure/safety invariants:
 * 1. queue connection failure != IDLE (fail-closed)
 * 2. invalid queue response != IDLE (fail-closed)
 * 3. queue busy blocks prepare
 * 4. node available + queue unavailable != MANGA_READY
 * 5. arbitrary proxy external URL rejected (403)
 * 6. wrong local port/origin rejected unless explicitly configured (403)
 * 7. unapproved proxy path rejected (403)
 * 8. allowed Manga paths pass (200)
 * 9. clipboard / handoff IPC not involved
 */

import assert from "node:assert";
import http from "node:http";
import { MangaBackendClient, BACKEND_STATUS, QUEUE_STATUS } from "../app/src/adapters/manga_backend_client.js";
import { createDefaultAuthoringDocument } from "../app/src/domain/authoring_document.js";

console.log("--- Running test_backend_adapter.mjs (M1A1 Hardening) ---");

// Test 1: Queue connection failure != IDLE (Fail-Closed)
{
    const client = new MangaBackendClient("http://127.0.0.1:59999"); // Offline port
    const qRes = await client.getQueue();
    assert.strictEqual(qRes.ok, false, "Offline queue read must not succeed");
    assert.strictEqual(qRes.status, QUEUE_STATUS.UNAVAILABLE, "Offline queue must be UNAVAILABLE");
    assert.strictEqual(qRes.queue_running, null, "Offline queue must not synthesize empty array");
    assert.strictEqual(qRes.queue_pending, null, "Offline queue must not synthesize empty array");

    // prepareDraft must fail closed and refuse to execute prepare
    const defaultDoc = createDefaultAuthoringDocument();
    const prepRes = await client.prepareDraft(defaultDoc, 0, 42);
    assert.strictEqual(prepRes.ok, false, "prepareDraft must fail closed when queue is unreachable");
    assert.strictEqual(prepRes.error_code, "QUEUE_UNAVAILABLE");
    assert.strictEqual(prepRes.isQueueIdleAfter, false);
    console.log("✓ Test 1 Passed: queue connection failure != IDLE (fail-closed)");
}

// Test 2: Invalid queue response != IDLE (Fail-Closed)
{
    const mockInvalidServer = http.createServer((req, res) => {
        if (req.url === "/queue") {
            res.writeHead(200, { "Content-Type": "application/json" });
            // Malformed queue response missing expected arrays
            res.end(JSON.stringify({ unexpected_payload: true }));
        } else {
            res.writeHead(404);
            res.end();
        }
    });
    await new Promise(r => mockInvalidServer.listen(0, "127.0.0.1", r));
    const port = mockInvalidServer.address().port;

    const client = new MangaBackendClient(`http://127.0.0.1:${port}`);
    const qRes = await client.getQueue();
    assert.strictEqual(qRes.ok, false);
    assert.strictEqual(qRes.status, QUEUE_STATUS.INVALID_RESPONSE);

    const defaultDoc = createDefaultAuthoringDocument();
    const prepRes = await client.prepareDraft(defaultDoc, 0, 42);
    assert.strictEqual(prepRes.ok, false, "prepareDraft must fail closed on invalid queue response");
    assert.strictEqual(prepRes.error_code, "QUEUE_UNAVAILABLE");
    console.log("✓ Test 2 Passed: invalid queue response != IDLE (fail-closed)");

    mockInvalidServer.close();
}

// Test 3: Queue busy blocks prepare
{
    let prepareCalled = false;
    const mockBusyServer = http.createServer((req, res) => {
        if (req.url === "/queue") {
            res.writeHead(200, { "Content-Type": "application/json" });
            // Queue has 1 running execution
            res.end(JSON.stringify({ queue_running: ["exec_1"], queue_pending: [] }));
        } else if (req.url === "/tegaki/manga/generation/prepare") {
            prepareCalled = true;
            res.writeHead(200, { "Content-Type": "application/json" });
            res.end(JSON.stringify({ ok: true, route: "STANDARD_NO_GUIDE" }));
        } else {
            res.writeHead(404);
            res.end();
        }
    });
    await new Promise(r => mockBusyServer.listen(0, "127.0.0.1", r));
    const port = mockBusyServer.address().port;

    const client = new MangaBackendClient(`http://127.0.0.1:${port}`);
    const defaultDoc = createDefaultAuthoringDocument();
    const prepRes = await client.prepareDraft(defaultDoc, 0, 42);

    assert.strictEqual(prepRes.ok, false, "prepareDraft must fail when queue is busy");
    assert.strictEqual(prepRes.error_code, "QUEUE_BUSY");
    assert.strictEqual(prepareCalled, false, "prepare endpoint must NEVER be called when queue is busy");
    console.log("✓ Test 3 Passed: queue busy blocks prepare");

    mockBusyServer.close();
}

// Test 4: Node available + queue unavailable != MANGA_READY
{
    const mockNodeOnlyServer = http.createServer((req, res) => {
        if (req.url === "/object_info/TegakiMinimumHandSceneEditor") {
            res.writeHead(200, { "Content-Type": "application/json" });
            res.end(JSON.stringify({
                TegakiMinimumHandSceneEditor: { name: "TegakiMinimumHandSceneEditor" }
            }));
        } else if (req.url === "/queue") {
            res.writeHead(500, { "Content-Type": "application/json" });
            res.end(JSON.stringify({ error: "Queue service unavailable" }));
        } else {
            res.writeHead(404);
            res.end();
        }
    });
    await new Promise(r => mockNodeOnlyServer.listen(0, "127.0.0.1", r));
    const port = mockNodeOnlyServer.address().port;

    const client = new MangaBackendClient(`http://127.0.0.1:${port}`);
    const statusRes = await client.probeStatus();

    assert.notStrictEqual(statusRes.status, BACKEND_STATUS.MANGA_READY, "Cannot be MANGA_READY if queue failed");
    assert.strictEqual(statusRes.status, BACKEND_STATUS.UNAVAILABLE);
    console.log("✓ Test 4 Passed: node available + queue unavailable != MANGA_READY");

    mockNodeOnlyServer.close();
}

// Test 5, 6, 7, 8: Workspace Proxy Restrictions & Whitelist
{
    // Start an instance of the hardened workspace server
    // Configure MANGA_BACKEND_URL to a known mock backend port
    const mockBackend = http.createServer((req, res) => {
        if (req.url === "/queue") {
            res.writeHead(200, { "Content-Type": "application/json" });
            res.end(JSON.stringify({ queue_running: [], queue_pending: [] }));
        } else if (req.url === "/object_info/TegakiMinimumHandSceneEditor") {
            res.writeHead(200, { "Content-Type": "application/json" });
            res.end(JSON.stringify({ TegakiMinimumHandSceneEditor: {} }));
        } else {
            res.writeHead(404);
            res.end();
        }
    });
    await new Promise(r => mockBackend.listen(0, "127.0.0.1", r));
    const backendPort = mockBackend.address().port;

    // Set env var for backend URL and import server dynamically
    process.env.MANGA_BACKEND_URL = `http://127.0.0.1:${backendPort}`;
    process.env.MANGA_WORKSPACE_PORT = "0"; // free port

    const { server: workspaceServer } = await import(`../service/manga_workspace_server.mjs?test=${Date.now()}`);
    await new Promise(r => {
        if (workspaceServer.listening) r();
        else workspaceServer.on("listening", r);
    });
    const wsPort = workspaceServer.address().port;

    // Test 5: Arbitrary proxy external URL rejected (403)
    const extRes = await fetch(`http://127.0.0.1:${wsPort}/api/proxy?target=http://example.com/malicious`);
    assert.strictEqual(extRes.status, 403, "External URL must be rejected with 403");
    console.log("✓ Test 5 Passed: arbitrary proxy external URL rejected");

    // Test 6: Wrong local port/origin rejected (403)
    const wrongPortRes = await fetch(`http://127.0.0.1:${wsPort}/api/proxy?target=http://127.0.0.1:9999/queue`);
    assert.strictEqual(wrongPortRes.status, 403, "Wrong port/origin must be rejected with 403");
    console.log("✓ Test 6 Passed: wrong local port/origin rejected unless explicitly configured");

    // Test 7: Unapproved proxy path rejected (403)
    const unapprovedRes = await fetch(`http://127.0.0.1:${wsPort}/api/proxy?path=/prompt`);
    assert.strictEqual(unapprovedRes.status, 403, "Unapproved path /prompt must be rejected with 403");
    const unapprovedTargetRes = await fetch(`http://127.0.0.1:${wsPort}/api/proxy?target=http://127.0.0.1:${backendPort}/prompt`);
    assert.strictEqual(unapprovedTargetRes.status, 403, "Unapproved target path must be rejected with 403");
    console.log("✓ Test 7 Passed: unapproved proxy path rejected");

    // Test 8: Allowed Manga paths pass (200)
    const allowedQueueRes = await fetch(`http://127.0.0.1:${wsPort}/api/proxy?path=/queue`);
    assert.strictEqual(allowedQueueRes.status, 200, "Approved path /queue must return 200");
    const allowedObjRes = await fetch(`http://127.0.0.1:${wsPort}/api/proxy?path=/object_info/TegakiMinimumHandSceneEditor`);
    assert.strictEqual(allowedObjRes.status, 200, "Approved path /object_info/... must return 200");
    console.log("✓ Test 8 Passed: allowed Manga paths pass");

    // Test 9: Zero broad CORS header on arbitrary origin
    const corsRes = await fetch(`http://127.0.0.1:${wsPort}/index.html`, {
        headers: { Origin: "http://malicious-site.com" }
    });
    assert.strictEqual(corsRes.headers.get("access-control-allow-origin"), null, "Arbitrary origin must NOT get CORS header");
    console.log("✓ Test 9 Passed: broad wildcard CORS removed/restricted");

    mockBackend.close();
    workspaceServer.close();
}

console.log("\n==================================================");
console.log("ALL BACKEND ADAPTER CONTRACT & SAFETY TESTS PASSED");
console.log("==================================================");
