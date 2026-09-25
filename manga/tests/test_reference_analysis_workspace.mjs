/**
 * test_reference_analysis_workspace.mjs
 * =====================================
 * Tests the /api/reference-assets/analyze endpoint on the Manga workspace server.
 * Verifies:
 * 1. HTTP method enforcement (POST required, GET -> 405).
 * 2. Origin validation (foreign Origin -> 403).
 * 3. Input validation:
 *    - Missing body or asset_reference -> 400.
 *    - Invalid prefix (outside tegaki_manga_references/) -> 400.
 *    - Path traversal attempt -> 400.
 *    - Unsupported extension -> 400.
 *    - Non-existent asset -> 404.
 * 4. Successful analysis request for existing reference asset -> 200 with structured candidate.
 */

import http from "node:http";
import assert from "node:assert/strict";

console.log("--- Running test_reference_analysis_workspace.mjs ---");

process.env.MANGA_WORKSPACE_PORT = "0";

const { server: workspaceServer } = await import(`../service/manga_workspace_server.mjs?test=${Date.now()}`);
await new Promise(r => {
    if (workspaceServer.listening) r();
    else workspaceServer.on("listening", r);
});
const workspacePort = workspaceServer.address().port;
const workspaceOrigin = `http://127.0.0.1:${workspacePort}`;

function makeRequest({ path, method = "GET", headers = {}, body = null }) {
    return new Promise((resolve, reject) => {
        const req = http.request({
            hostname: "127.0.0.1",
            port: workspacePort,
            path,
            method,
            headers
        }, (res) => {
            const chunks = [];
            res.on("data", c => chunks.push(c));
            res.on("end", () => {
                const raw = Buffer.concat(chunks);
                let json = null;
                try {
                    json = JSON.parse(raw.toString("utf8"));
                } catch (_) {}
                resolve({
                    status: res.statusCode,
                    headers: res.headers,
                    body: json,
                    rawBody: raw
                });
            });
        });
        req.on("error", reject);
        if (body) {
            req.write(body);
        }
        req.end();
    });
}

try {
    // 1. Method Not Allowed (GET)
    {
        const res = await makeRequest({
            path: "/api/reference-assets/analyze",
            method: "GET"
        });
        assert.equal(res.status, 405, "GET should return 405 Method Not Allowed");
        assert.equal(res.body?.ok, false);
        console.log("PASS: 1. GET returns 405");
    }

    // 2. Foreign Origin rejection (403)
    {
        const res = await makeRequest({
            path: "/api/reference-assets/analyze",
            method: "POST",
            headers: {
                "Origin": "http://evil-attacker.com",
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ asset_reference: "tegaki_manga_references/ref_c789751db904319d.png" })
        });
        assert.equal(res.status, 403, "Foreign origin should return 403");
        assert.equal(res.body?.ok, false);
        console.log("PASS: 2. Foreign Origin returns 403");
    }

    // 3. Missing asset_reference parameter (400)
    {
        const res = await makeRequest({
            path: "/api/reference-assets/analyze",
            method: "POST",
            headers: {
                "Origin": workspaceOrigin,
                "Content-Type": "application/json"
            },
            body: JSON.stringify({})
        });
        assert.equal(res.status, 400, "Missing asset_reference should return 400");
        assert.equal(res.body?.ok, false);
        console.log("PASS: 3. Missing asset_reference returns 400");
    }

    // 4. Invalid prefix outside tegaki_manga_references/ (400)
    {
        const res = await makeRequest({
            path: "/api/reference-assets/analyze",
            method: "POST",
            headers: {
                "Origin": workspaceOrigin,
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ asset_reference: "tegaki_manga_guides/guide.png" })
        });
        assert.equal(res.status, 400, "Invalid prefix should return 400");
        assert.equal(res.body?.ok, false);
        console.log("PASS: 4. Wrong prefix returns 400");
    }

    // 5. Path traversal attempt (400)
    {
        const res = await makeRequest({
            path: "/api/reference-assets/analyze",
            method: "POST",
            headers: {
                "Origin": workspaceOrigin,
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ asset_reference: "tegaki_manga_references/../../secret.png" })
        });
        assert.equal(res.status, 400, "Path traversal should return 400");
        assert.equal(res.body?.ok, false);
        console.log("PASS: 5. Path traversal returns 400");
    }

    // 6. Unsupported extension (400)
    {
        const res = await makeRequest({
            path: "/api/reference-assets/analyze",
            method: "POST",
            headers: {
                "Origin": workspaceOrigin,
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ asset_reference: "tegaki_manga_references/script.py" })
        });
        assert.equal(res.status, 400, "Unsupported extension should return 400");
        assert.equal(res.body?.ok, false);
        console.log("PASS: 6. Unsupported extension returns 400");
    }

    // 7. Non-existent reference file (404)
    {
        const res = await makeRequest({
            path: "/api/reference-assets/analyze",
            method: "POST",
            headers: {
                "Origin": workspaceOrigin,
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ asset_reference: "tegaki_manga_references/non_existent_12345.png" })
        });
        assert.equal(res.status, 404, "Non-existent file should return 404");
        assert.equal(res.body?.ok, false);
        console.log("PASS: 7. Non-existent asset returns 404");
    }

    // 8. Valid reference asset analysis
    {
        const res = await makeRequest({
            path: "/api/reference-assets/analyze",
            method: "POST",
            headers: {
                "Origin": workspaceOrigin,
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ asset_reference: "tegaki_manga_references/ref_c789751db904319d.png" })
        });
        assert.equal(res.status, 200, "Valid reference should return 200");
        assert.equal(res.body?.ok, true);
        assert.equal(res.body?.model, "SmilingWolf/wd-v1-4-convnext-tagger-v2");
        assert.equal(res.body?.execution_provider, "CPUExecutionProvider");
        assert.ok(typeof res.body?.candidate === "string" && res.body?.candidate.length > 0);
        assert.ok(Array.isArray(res.body?.tags));
        assert.ok(res.body?.tags.includes("1girl"));
        console.log("PASS: 8. Valid reference analysis returns 200 with candidate:", res.body.candidate);
    }

    console.log("=== ALL WORKSPACE SERVER ENDPOINT TESTS PASSED ===");
} finally {
    workspaceServer.close();
}
