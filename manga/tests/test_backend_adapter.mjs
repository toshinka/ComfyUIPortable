/**
 * test_backend_adapter.mjs — Manga Backend Adapter Contract Tests
 * ===============================================================
 * TEGAKI Manga Authoring Workspace (M1A)
 * 
 * Verifies:
 * 1. Backend unavailable classification when server not responding.
 * 2. Generic ComfyUI classification when Tegaki custom node is missing.
 * 3. Manga-ready classification when Tegaki node is present.
 * 4. Zero generation invariant: prepareDraft does NOT queue execution.
 */

import assert from "node:assert";
import http from "node:http";
import { MangaBackendClient, BACKEND_STATUS } from "../app/src/adapters/manga_backend_client.js";
import { createDefaultAuthoringDocument } from "../app/src/domain/authoring_document.js";

console.log("--- Running test_backend_adapter.mjs ---");

// Test 1: Unavailable backend probe
{
    const client = new MangaBackendClient("http://127.0.0.1:59999"); // Unused port
    const res = await client.probeStatus();
    assert.strictEqual(res.status, BACKEND_STATUS.UNAVAILABLE);
    console.log("✓ Test 1 Passed: Correctly classifies unreachable backend");
}

// Test 2: Generic ComfyUI mock (serves /queue, but 404s on TegakiMinimumHandSceneEditor)
{
    const mockGenericServer = http.createServer((req, res) => {
        if (req.url === "/queue") {
            res.writeHead(200, { "Content-Type": "application/json" });
            res.end(JSON.stringify({ queue_running: [], queue_pending: [] }));
        } else {
            res.writeHead(404, { "Content-Type": "application/json" });
            res.end(JSON.stringify({ error: "Not found" }));
        }
    });

    await new Promise(r => mockGenericServer.listen(0, "127.0.0.1", r));
    const port = mockGenericServer.address().port;

    const client = new MangaBackendClient(`http://127.0.0.1:${port}`);
    const res = await client.probeStatus();
    assert.strictEqual(res.status, BACKEND_STATUS.GENERIC_COMFYUI);
    console.log("✓ Test 2 Passed: Correctly classifies generic / non-Manga ComfyUI");

    mockGenericServer.close();
}

// Test 3: Manga-Ready Mock Server
{
    let prepareCalled = false;
    let queueChecked = 0;

    const mockMangaServer = http.createServer((req, res) => {
        if (req.url === "/queue") {
            queueChecked++;
            res.writeHead(200, { "Content-Type": "application/json" });
            res.end(JSON.stringify({ queue_running: [], queue_pending: [] }));
        } else if (req.url === "/object_info/TegakiMinimumHandSceneEditor") {
            res.writeHead(200, { "Content-Type": "application/json" });
            res.end(JSON.stringify({
                TegakiMinimumHandSceneEditor: { name: "TegakiMinimumHandSceneEditor" }
            }));
        } else if (req.url === "/tegaki/manga/generation/prepare" && req.method === "POST") {
            prepareCalled = true;
            res.writeHead(200, { "Content-Type": "application/json" });
            res.end(JSON.stringify({
                ok: true,
                route: "STANDARD_NO_GUIDE",
                prompt: { "1": { class_type: "KSampler" } }
            }));
        } else {
            res.writeHead(404);
            res.end();
        }
    });

    await new Promise(r => mockMangaServer.listen(0, "127.0.0.1", r));
    const port = mockMangaServer.address().port;

    const client = new MangaBackendClient(`http://127.0.0.1:${port}`);
    const res = await client.probeStatus();
    assert.strictEqual(res.status, BACKEND_STATUS.MANGA_READY);
    console.log("✓ Test 3 Passed: Correctly identifies Manga-capable backend");

    // Test 4: prepareDraft execution without queue submission
    const defaultDoc = createDefaultAuthoringDocument();
    const prepRes = await client.prepareDraft(defaultDoc, 0, 42);
    assert.strictEqual(prepRes.ok, true);
    assert.strictEqual(prepRes.route, "STANDARD_NO_GUIDE");
    assert.strictEqual(prepRes.generationTriggered, false);
    assert.strictEqual(prepRes.queueBefore.running, 0);
    assert.strictEqual(prepRes.queueAfter.running, 0);
    assert.strictEqual(prepareCalled, true);
    assert.ok(queueChecked >= 2, "Queue must be checked before and after prepare");
    console.log("✓ Test 4 Passed: prepareDraft executes without queue submission");

    mockMangaServer.close();
}

console.log("All backend adapter tests PASSED successfully.");
