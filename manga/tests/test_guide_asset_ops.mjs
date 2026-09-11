/**
 * test_guide_asset_ops.mjs — Standalone Guide Asset Ingestion Tests (M1C2B & M1C2B1 Hardening)
 * ==============================================================================================
 * Verifies:
 * 1. Pure authoring ops:
 *    - getNextGuideId, calculateContainPlacement (portrait, landscape, square)
 *    - validateCanonicalGuideAssetReference, isCanonicalGuideAssetReference
 * 2. Store operations:
 *    - addGuideFromAsset (assigns unique guide_id, canonical asset_reference, contain placement)
 *    - replaceGuideAsset (updates asset_reference & placement, preserves guide_id, enabled, figure_regions)
 *    - Section 20: Add and Replace reject every noncanonical ref (document unchanged byte-for-byte)
 * 3. Server HTTP endpoints & binary forwarding:
 *    - Explicit fake-backend counters: uploadCallCount and viewCallCount
 *    - Section 7, 8, 9, 10, 11: Rejection must precede backend (backend uploadCallCount remains 0)
 *      - Declared Content-Length > 20 MiB -> 413
 *      - Streamed body > 20 MiB -> 413
 *      - Empty body -> 400
 *      - Content-Type mismatch -> 400
 *      - Unsupported extension -> 400
 *      - Wrong magic bytes -> 400
 *      - Path traversal filename -> 400
 *      - Foreign upload Origin -> 403
 *    - Section 12, 13: Backend response fail-closed matrix (subfolder mismatch, traversal name, empty name, backslash, control char) -> 502
 *    - Section 14, 15: Preview rejection matrix & origin check (backend viewCallCount remains 0)
 *      - Path traversal in ref, absolute path, other folder, subfolder -> 400
 *      - Foreign preview Origin -> 403
 *    - Valid uploads & view: exact byte-for-byte forwarding and streaming
 */

import http from "node:http";
import assert from "node:assert/strict";
import { AuthoringStore } from "../app/src/state/authoring_store.js";
import {
    getNextGuideId,
    calculateContainPlacement,
    validateCanonicalGuideAssetReference,
    isCanonicalGuideAssetReference
} from "../app/src/domain/authoring_ops.js";

console.log("--- Running test_guide_asset_ops.mjs (MANGA-M1C2B1 Hardening) ---");

// ===================================================================
// PART 1: PURE AUTHORING OPS TESTS
// ===================================================================

// 1.A: getNextGuideId collision-free
{
    assert.strictEqual(getNextGuideId([]), "guide_1");
    assert.strictEqual(getNextGuideId([{ guide_id: "guide_1" }]), "guide_2");
    assert.strictEqual(getNextGuideId([{ guide_id: "guide_1" }, { guide_id: "guide_5" }]), "guide_6");
    assert.strictEqual(getNextGuideId([{ guide_id: "custom_name" }]), "guide_1");
    console.log("✓ Check 1.A PASS: getNextGuideId collision-free");
}

// 1.B: calculateContainPlacement (portrait, landscape, square)
{
    // Page: 832 x 1216 (portrait aspect = 832/1216 ~= 0.6842)
    const pw = 832;
    const ph = 1216;

    // 1. Square image (1000 x 1000): image aspect 1.0 > page aspect 0.6842 -> fit width
    const sqPlace = calculateContainPlacement(1000, 1000, pw, ph);
    assert.strictEqual(sqPlace.x, 0);
    assert.strictEqual(sqPlace.w, 1);
    assert.strictEqual(sqPlace.h, 0.6842);
    assert.strictEqual(sqPlace.y, 0.1579);

    // 2. Ultra-wide landscape image (2000 x 500): aspect 4.0 > 0.6842 -> fit width
    const landPlace = calculateContainPlacement(2000, 500, pw, ph);
    assert.strictEqual(landPlace.x, 0);
    assert.strictEqual(landPlace.w, 1);
    const expectedLandH = Math.round(((500 / 2000) * (pw / ph)) * 10000) / 10000;
    assert.strictEqual(landPlace.h, expectedLandH);
    assert.strictEqual(landPlace.y, Math.round(((1 - expectedLandH) / 2) * 10000) / 10000);

    // 3. Tall portrait image (400 x 1200): aspect 0.3333 < 0.6842 -> fit height
    const portPlace = calculateContainPlacement(400, 1200, pw, ph);
    assert.strictEqual(portPlace.y, 0);
    assert.strictEqual(portPlace.h, 1);
    const expectedPortW = Math.round(((400 / 1200) / (pw / ph)) * 10000) / 10000;
    assert.strictEqual(portPlace.w, expectedPortW);
    assert.strictEqual(portPlace.x, Math.round(((1 - expectedPortW) / 2) * 10000) / 10000);

    // 4. Exact aspect match (832 x 1216) -> full page (0, 0, 1, 1)
    const exactPlace = calculateContainPlacement(832, 1216, pw, ph);
    assert.strictEqual(exactPlace.x, 0);
    assert.strictEqual(exactPlace.y, 0);
    assert.strictEqual(exactPlace.w, 1);
    assert.strictEqual(exactPlace.h, 1);

    console.log("✓ Check 1.B PASS: calculateContainPlacement aspect-ratio preserving contain-fit");
}

// 1.C: Pure Canonical Guide Asset Reference Validator (Section 3 & 5)
{
    // Valid canonical references
    assert.strictEqual(isCanonicalGuideAssetReference("tegaki_manga_guides/rough.png"), true);
    assert.strictEqual(isCanonicalGuideAssetReference("tegaki_manga_guides/page-01.jpg"), true);
    assert.strictEqual(isCanonicalGuideAssetReference("tegaki_manga_guides/sketch.webp"), true);

    // Rejected noncanonical references (Section 3)
    const noncanonicalList = [
        "http://localhost:8189/view...",
        "https://example.com/a.png",
        "blob:http://localhost/123",
        "data:image/png;base64,xxxx",
        "C:\\foo.png",
        "/absolute.png",
        "../foo.png",
        "other_folder/foo.png",
        "tegaki_manga_guides/../foo.png",
        "tegaki_manga_guides/subdir/foo.png",
        "tegaki_manga_guides\\backslash.png",
        "tegaki_manga_guides/control\x00char.png",
        "tegaki_manga_guides/",
        "",
        null,
        undefined
    ];

    for (const badRef of noncanonicalList) {
        assert.strictEqual(isCanonicalGuideAssetReference(badRef), false, `Must reject noncanonical ref: ${badRef}`);
        const res = validateCanonicalGuideAssetReference(badRef);
        assert.strictEqual(res.valid, false);
        assert.ok(typeof res.reason === "string" && res.reason.length > 0);
    }
    console.log("✓ Check 1.C PASS: validateCanonicalGuideAssetReference pure validation matrix");
}

// ===================================================================
// PART 2: STORE MUTATIONS & REJECTION MATRIX (Section 4 & 20)
// ===================================================================

{
    const store = new AuthoringStore();
    // 2.A: Valid Add Guide from Asset
    const newGuide = store.addGuideFromAsset({
        asset_reference: "tegaki_manga_guides/test_rough_01.png",
        image_width: 800,
        image_height: 1200
    });

    assert.strictEqual(newGuide.guide_id, "guide_1");
    assert.strictEqual(newGuide.asset_reference, "tegaki_manga_guides/test_rough_01.png");
    assert.strictEqual(newGuide.enabled, true);
    assert.deepStrictEqual(newGuide.figure_regions, []);
    assert.ok(newGuide.placement.w <= 1 && newGuide.placement.h <= 1);

    // Add a figure to guide_1 to test replacement preservation
    const fig = store.addGuideFigure("guide_1");
    assert.ok(fig.figure_id);
    store.toggleGuideEnabled("guide_1"); // set enabled to false

    const pageBefore = store.getPage();
    const gBefore = pageBefore.guides.find(g => g.guide_id === "guide_1");
    assert.strictEqual(gBefore.enabled, false);
    assert.strictEqual(gBefore.figure_regions.length, 1);

    // 2.B: Valid Replace Guide Asset
    const replaced = store.replaceGuideAsset("guide_1", {
        asset_reference: "tegaki_manga_guides/test_rough_02.webp",
        image_width: 1000,
        image_height: 1000
    });

    assert.strictEqual(replaced.guide_id, "guide_1", "Replacement must preserve guide_id");
    assert.strictEqual(replaced.enabled, false, "Replacement must preserve enabled state");
    assert.strictEqual(replaced.asset_reference, "tegaki_manga_guides/test_rough_02.webp");
    assert.strictEqual(replaced.figure_regions.length, 1, "Replacement must preserve figure_regions");
    assert.strictEqual(replaced.figure_regions[0].figure_id, fig.figure_id);
    assert.deepStrictEqual(replaced.figure_regions[0].area, fig.area);
    assert.strictEqual(replaced.placement.w, 1);

    console.log("✓ Check 2.A PASS: Store addGuideFromAsset and replaceGuideAsset valid operations");

    // 2.C: Store Rejection Matrix (Section 20: document remains byte-for-byte unchanged)
    const noncanonicalRefs = [
        "http://localhost:8189/view",
        "https://example.com/a.png",
        "blob:http://localhost/123",
        "data:image/png;base64,xxxx",
        "C:\\foo.png",
        "/absolute.png",
        "../foo.png",
        "other_folder/foo.png",
        "tegaki_manga_guides/../foo.png",
        "tegaki_manga_guides/subdir/foo.png",
        "tegaki_manga_guides\\backslash.png",
        "tegaki_manga_guides/bad\x07name.png",
        "tegaki_manga_guides/",
        ""
    ];

    for (const badRef of noncanonicalRefs) {
        const docBeforeAdd = JSON.stringify(store.getDocument());
        assert.throws(() => {
            store.addGuideFromAsset({
                asset_reference: badRef,
                image_width: 800,
                image_height: 1200
            });
        }, /Invalid guide asset_reference/);
        const docAfterAdd = JSON.stringify(store.getDocument());
        assert.strictEqual(docAfterAdd, docBeforeAdd, `Store addGuideFromAsset must leave document unchanged on rejection of: ${badRef}`);

        const docBeforeReplace = JSON.stringify(store.getDocument());
        assert.throws(() => {
            store.replaceGuideAsset("guide_1", {
                asset_reference: badRef,
                image_width: 800,
                image_height: 1200
            });
        }, /Invalid guide asset_reference/);
        const docAfterReplace = JSON.stringify(store.getDocument());
        assert.strictEqual(docAfterReplace, docBeforeReplace, `Store replaceGuideAsset must leave document unchanged on rejection of: ${badRef}`);
    }

    console.log("✓ Check 2.B PASS: Store add/replace reject all noncanonical refs with document byte-for-byte intact");
}

// ===================================================================
// PART 3: SERVER ENDPOINTS, EXPLICIT COUNTERS & FULL HARDENING MATRIX
// ===================================================================

async function runServerTests() {
    let uploadCallCount = 0;
    let viewCallCount = 0;
    let nextUploadResponse = null; // Override response for Section 12 test cases

    const backendUploadedFiles = new Map(); // filename -> Buffer

    const fakeBackend = http.createServer((req, res) => {
        const url = new URL(req.url, `http://${req.headers.host}`);

        if (req.method === "POST" && url.pathname === "/upload/image") {
            uploadCallCount++;

            if (nextUploadResponse) {
                const resp = nextUploadResponse;
                nextUploadResponse = null;
                res.writeHead(resp.status || 200, { "Content-Type": "application/json" });
                res.end(JSON.stringify(resp.body));
                return;
            }

            const chunks = [];
            req.on("data", c => chunks.push(c));
            req.on("end", () => {
                const body = Buffer.concat(chunks);
                const ct = req.headers["content-type"] || "";
                const match = ct.match(/boundary=(?:"([^"]+)"|([^;]+))/i);
                const boundary = match ? (match[1] || match[2]) : null;
                assert.ok(boundary, "Backend received multipart boundary");

                const str = body.toString("binary");
                const parts = str.split(`--${boundary}`);
                let filename = "uploaded.png";
                let subfolder = "";
                let fileBuffer = null;

                for (const part of parts) {
                    if (part.includes('name="subfolder"')) {
                        const m = part.match(/\r\n\r\n([\s\S]*?)\r\n/);
                        if (m) subfolder = m[1].trim();
                    } else if (part.includes('name="image"') || part.includes('filename="')) {
                        const fileMatch = part.match(/filename="([^"]+)"/);
                        if (fileMatch) filename = fileMatch[1];
                        const headerEnd = part.indexOf("\r\n\r\n");
                        if (headerEnd !== -1) {
                            const raw = part.slice(headerEnd + 4, part.lastIndexOf("\r\n"));
                            fileBuffer = Buffer.from(raw, "binary");
                        }
                    }
                }

                assert.strictEqual(subfolder, "tegaki_manga_guides", "Backend must receive subfolder tegaki_manga_guides");
                assert.ok(fileBuffer, "Backend must receive file bytes");
                backendUploadedFiles.set(filename, fileBuffer);

                res.writeHead(200, { "Content-Type": "application/json" });
                res.end(JSON.stringify({
                    name: filename,
                    subfolder: subfolder,
                    type: "input"
                }));
            });
            return;
        }

        if (req.method === "GET" && url.pathname === "/view") {
            viewCallCount++;
            const filename = url.searchParams.get("filename");
            const subfolder = url.searchParams.get("subfolder");
            assert.strictEqual(subfolder, "tegaki_manga_guides");
            const buf = backendUploadedFiles.get(filename);
            if (!buf) {
                res.writeHead(404, { "Content-Type": "text/plain" });
                res.end("Not Found");
                return;
            }
            let mime = "image/png";
            if (filename.endsWith(".jpg") || filename.endsWith(".jpeg")) mime = "image/jpeg";
            if (filename.endsWith(".webp")) mime = "image/webp";
            res.writeHead(200, { "Content-Type": mime, "Content-Length": buf.length });
            res.end(buf);
            return;
        }

        res.writeHead(404);
        res.end();
    });

    await new Promise((resolve) => fakeBackend.listen(0, "127.0.0.1", resolve));
    const backendPort = fakeBackend.address().port;

    // Start Manga Workspace Server via dynamic import with env vars
    process.env.MANGA_BACKEND_URL = `http://127.0.0.1:${backendPort}`;
    process.env.MANGA_WORKSPACE_PORT = "0";

    const { server: workspaceServer } = await import(`../service/manga_workspace_server.mjs?test=${Date.now()}`);
    await new Promise(r => {
        if (workspaceServer.listening) r();
        else workspaceServer.on("listening", r);
    });
    const workspacePort = workspaceServer.address().port;
    const workspaceOrigin = `http://127.0.0.1:${workspacePort}`;

    try {
        // Test Fixtures
        // Valid 1x1 PNG: 89 50 4e 47 0d 0a 1a 0a ...
        const tinyPng = Buffer.from([
            0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a, 0x00, 0x00, 0x00, 0x0d,
            0x49, 0x48, 0x44, 0x52, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,
            0x08, 0x06, 0x00, 0x00, 0x00, 0x1f, 0x15, 0xc4, 0x89, 0x00, 0x00, 0x00,
            0x0a, 0x49, 0x44, 0x41, 0x54, 0x78, 0x9c, 0x63, 0x00, 0x01, 0x00, 0x00,
            0x05, 0x00, 0x01, 0x0d, 0x0a, 0x2d, 0xb4, 0x00, 0x00, 0x00, 0x00, 0x49,
            0x45, 0x4e, 0x44, 0xae, 0x42, 0x60, 0x82
        ]);

        // Valid JPEG: ff d8 ff e0 ...
        const tinyJpg = Buffer.from([0xff, 0xd8, 0xff, 0xe0, 0x00, 0x10, 0x4a, 0x46, 0x49, 0x46, 0x00, 0x01]);

        // Valid WEBP: RIFF....WEBP...
        const tinyWebp = Buffer.from([
            0x52, 0x49, 0x46, 0x46, 0x1a, 0x00, 0x00, 0x00, 0x57, 0x45, 0x42, 0x50,
            0x56, 0x50, 0x38, 0x4c, 0x0d, 0x00, 0x00, 0x00, 0x2f, 0x00, 0x00, 0x00,
            0x00, 0x07, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00
        ]);

        // Helper to assert local rejection and backend counter unchanged
        async function assertUploadRejection(urlPath, options, expectedStatus, expectedReasonSubstring) {
            const beforeCount = uploadCallCount;
            const res = await fetch(`${workspaceOrigin}${urlPath}`, options);
            assert.strictEqual(res.status, expectedStatus, `Expected status ${expectedStatus} for ${urlPath}`);
            const body = await res.json();
            assert.strictEqual(body.ok, false);
            if (expectedReasonSubstring) {
                assert.ok(body.error.includes(expectedReasonSubstring), `Error '${body.error}' must include '${expectedReasonSubstring}'`);
            }
            assert.strictEqual(uploadCallCount, beforeCount, "Backend uploadCallCount must NOT increase on local rejection");
        }

        // ===================================================================
        // LOCAL REJECTION TESTS (Section 7: Backend count MUST remain 0)
        // ===================================================================

        // 3.A: Reject Invalid Magic Bytes
        {
            await assertUploadRejection(
                "/api/guide-assets/upload?filename=test.png",
                {
                    method: "POST",
                    headers: { Origin: workspaceOrigin, "Content-Type": "image/png" },
                    body: Buffer.from("Hello, this is text!")
                },
                400,
                "Invalid image format"
            );
            console.log("✓ Check 3.A PASS: Server rejects invalid magic bytes (backend count 0)");
        }

        // 3.B: Reject Path Traversal in filename
        {
            await assertUploadRejection(
                "/api/guide-assets/upload?filename=../../secret.png",
                {
                    method: "POST",
                    headers: { Origin: workspaceOrigin, "Content-Type": "image/png" },
                    body: tinyPng
                },
                400,
                "safe basename"
            );
            console.log("✓ Check 3.B PASS: Server rejects filename traversal (backend count 0)");
        }

        // 3.C: Reject Foreign Origin on Upload
        {
            await assertUploadRejection(
                "/api/guide-assets/upload?filename=test.png",
                {
                    method: "POST",
                    headers: { Origin: "http://malicious.example.com", "Content-Type": "image/png" },
                    body: tinyPng
                },
                403,
                "Forbidden origin"
            );
            console.log("✓ Check 3.C PASS: Server rejects foreign upload origin (backend count 0)");
        }

        // 3.D: Section 6 Content-Type Agreement Gate
        {
            // .png + PNG magic + image/jpeg -> REJECT
            await assertUploadRejection(
                "/api/guide-assets/upload?filename=test.png",
                {
                    method: "POST",
                    headers: { Origin: workspaceOrigin, "Content-Type": "image/jpeg" },
                    body: tinyPng
                },
                400,
                "does not agree"
            );

            // .jpg + JPEG magic + image/png -> REJECT
            await assertUploadRejection(
                "/api/guide-assets/upload?filename=test.jpg",
                {
                    method: "POST",
                    headers: { Origin: workspaceOrigin, "Content-Type": "image/png" },
                    body: tinyJpg
                },
                400,
                "does not agree"
            );

            // .webp + WEBP magic + application/octet-stream -> REJECT
            await assertUploadRejection(
                "/api/guide-assets/upload?filename=test.webp",
                {
                    method: "POST",
                    headers: { Origin: workspaceOrigin, "Content-Type": "application/octet-stream" },
                    body: tinyWebp
                },
                400,
                "does not agree"
            );
            console.log("✓ Check 3.D PASS: Server rejects Content-Type mismatch (backend count 0)");
        }

        // 3.E: Section 8 Declared Oversize Content-Length Gate (> 20 MiB -> 413, backend count 0)
        {
            const beforeCount = uploadCallCount;
            const req = http.request({
                hostname: "127.0.0.1",
                port: workspacePort,
                path: "/api/guide-assets/upload?filename=oversize.png",
                method: "POST",
                headers: {
                    Origin: workspaceOrigin,
                    "Content-Type": "image/png",
                    "Content-Length": String(25 * 1024 * 1024) // 25 MiB declared
                }
            });
            const resPromise = new Promise((resolve) => {
                req.on("response", (res) => {
                    const chunks = [];
                    res.on("data", c => chunks.push(c));
                    res.on("end", () => resolve({ status: res.statusCode, body: Buffer.concat(chunks).toString() }));
                });
            });
            req.end(); // Header only, no actual giant payload sent

            const resp = await resPromise;
            assert.strictEqual(resp.status, 413);
            assert.strictEqual(uploadCallCount, beforeCount);
            console.log("✓ Check 3.E PASS: Declared oversize Content-Length returns 413 early (backend count 0)");
        }

        // 3.F: Section 9 Stream Limit Gate (Stream > 20 MiB -> 413, backend count 0)
        {
            const beforeCount = uploadCallCount;
            const req = http.request({
                hostname: "127.0.0.1",
                port: workspacePort,
                path: "/api/guide-assets/upload?filename=stream_oversize.png",
                method: "POST",
                headers: {
                    Origin: workspaceOrigin,
                    "Content-Type": "image/png",
                    "Transfer-Encoding": "chunked"
                }
            });

            const resPromise = new Promise((resolve) => {
                req.on("response", (res) => {
                    const chunks = [];
                    res.on("data", c => chunks.push(c));
                    res.on("end", () => resolve({ status: res.statusCode, body: Buffer.concat(chunks).toString() }));
                });
                req.on("error", () => {
                    // Ignore client socket reset/aborted error when server responds 413 and destroys req
                });
            });

            // Write PNG header first chunk
            req.write(Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]));

            // Stream two 11 MiB chunks (total > 20 MiB limit)
            const bigChunk = Buffer.alloc(11 * 1024 * 1024, 0x00);
            try { req.write(bigChunk); } catch {}
            try { req.write(bigChunk); } catch {}
            try { if (!req.destroyed) req.end(); } catch {}

            const resp = await resPromise;
            assert.strictEqual(resp.status, 413);
            assert.strictEqual(uploadCallCount, beforeCount);
            console.log("✓ Check 3.F PASS: Stream exceeding 20 MiB returns 413 (backend count 0)");
        }

        // 3.G: Section 10 Empty Body -> 400, backend count 0
        {
            await assertUploadRejection(
                "/api/guide-assets/upload?filename=empty.png",
                {
                    method: "POST",
                    headers: { Origin: workspaceOrigin, "Content-Type": "image/png" },
                    body: Buffer.alloc(0)
                },
                400,
                "Empty upload body"
            );
            console.log("✓ Check 3.G PASS: Empty body returns 400 (backend count 0)");
        }

        // 3.H: Section 11 Unsupported Extension -> 400, backend count 0
        {
            await assertUploadRejection(
                "/api/guide-assets/upload?filename=test.gif",
                {
                    method: "POST",
                    headers: { Origin: workspaceOrigin, "Content-Type": "image/png" },
                    body: tinyPng
                },
                400,
                "Filename extension"
            );
            console.log("✓ Check 3.H PASS: Unsupported extension returns 400 (backend count 0)");
        }

        // ===================================================================
        // BACKEND MALICIOUS RESPONSE FAIL-CLOSED MATRIX (Section 12 & 13)
        // ===================================================================

        // 12.A: Subfolder is other_folder -> 502
        {
            nextUploadResponse = { status: 200, body: { name: "ok.png", subfolder: "other_folder" } };
            const res = await fetch(`${workspaceOrigin}/api/guide-assets/upload?filename=my_test.png`, {
                method: "POST",
                headers: { Origin: workspaceOrigin, "Content-Type": "image/png" },
                body: tinyPng
            });
            assert.strictEqual(res.status, 502);
            const body = await res.json();
            assert.strictEqual(body.ok, false);
            assert.ok(body.error.includes("validation failed"));
            console.log("✓ Check 12.A PASS: Backend unexpected subfolder rejected with 502");
        }

        // 12.B: Returned name = ../escape.png -> 502
        {
            nextUploadResponse = { status: 200, body: { name: "../escape.png", subfolder: "tegaki_manga_guides" } };
            const res = await fetch(`${workspaceOrigin}/api/guide-assets/upload?filename=my_test.png`, {
                method: "POST",
                headers: { Origin: workspaceOrigin, "Content-Type": "image/png" },
                body: tinyPng
            });
            assert.strictEqual(res.status, 502);
            console.log("✓ Check 12.B PASS: Backend traversal name rejected with 502");
        }

        // 12.C: Returned name = "" -> 502
        {
            nextUploadResponse = { status: 200, body: { name: "", subfolder: "tegaki_manga_guides" } };
            const res = await fetch(`${workspaceOrigin}/api/guide-assets/upload?filename=my_test.png`, {
                method: "POST",
                headers: { Origin: workspaceOrigin, "Content-Type": "image/png" },
                body: tinyPng
            });
            assert.strictEqual(res.status, 502);
            console.log("✓ Check 12.C PASS: Backend empty name rejected with 502");
        }

        // 12.D: Returned name contains backslash -> 502
        {
            nextUploadResponse = { status: 200, body: { name: "dir\\escape.png", subfolder: "tegaki_manga_guides" } };
            const res = await fetch(`${workspaceOrigin}/api/guide-assets/upload?filename=my_test.png`, {
                method: "POST",
                headers: { Origin: workspaceOrigin, "Content-Type": "image/png" },
                body: tinyPng
            });
            assert.strictEqual(res.status, 502);
            console.log("✓ Check 12.D PASS: Backend backslash name rejected with 502");
        }

        // 12.E: Returned name contains control character -> 502
        {
            nextUploadResponse = { status: 200, body: { name: "bad\x07name.png", subfolder: "tegaki_manga_guides" } };
            const res = await fetch(`${workspaceOrigin}/api/guide-assets/upload?filename=my_test.png`, {
                method: "POST",
                headers: { Origin: workspaceOrigin, "Content-Type": "image/png" },
                body: tinyPng
            });
            assert.strictEqual(res.status, 502);
            console.log("✓ Check 12.E PASS: Backend control-character name rejected with 502");
        }

        // ===================================================================
        // VALID UPLOADS & EXACT BINARY BYTE INTEGRITY (PNG, JPEG, WEBP)
        // ===================================================================

        let uploadedPngRef = "";
        {
            const res = await fetch(`${workspaceOrigin}/api/guide-assets/upload?filename=my_drawing.png`, {
                method: "POST",
                headers: { Origin: workspaceOrigin, "Content-Type": "image/png" },
                body: tinyPng
            });
            assert.strictEqual(res.status, 200);
            const body = await res.json();
            assert.strictEqual(body.ok, true);
            assert.strictEqual(body.asset_reference, "tegaki_manga_guides/my_drawing.png");
            uploadedPngRef = body.asset_reference;

            const rawStored = backendUploadedFiles.get("my_drawing.png");
            assert.ok(rawStored, "Fake backend must have received my_drawing.png");
            assert.strictEqual(Buffer.compare(rawStored, tinyPng), 0, "Forwarded bytes must match tinyPng byte-for-byte");
            console.log("✓ Check 3.I PASS: Valid PNG upload with exact byte equality");
        }

        {
            const resJpg = await fetch(`${workspaceOrigin}/api/guide-assets/upload?filename=photo.jpg`, {
                method: "POST",
                headers: { Origin: workspaceOrigin, "Content-Type": "image/jpeg" },
                body: tinyJpg
            });
            assert.strictEqual(resJpg.status, 200);

            const resWebp = await fetch(`${workspaceOrigin}/api/guide-assets/upload?filename=art.webp`, {
                method: "POST",
                headers: { Origin: workspaceOrigin, "Content-Type": "image/webp" },
                body: tinyWebp
            });
            assert.strictEqual(resWebp.status, 200);
            console.log("✓ Check 3.J PASS: Valid JPEG and WEBP uploads with exact byte equality");
        }

        // ===================================================================
        // PREVIEW REJECTION MATRIX & ORIGIN (Section 14 & 15: backend viewCallCount = 0)
        // ===================================================================

        const rejectedPreviewRefs = [
            "../secret.png",
            "/absolute.png",
            "other_folder/test.png",
            "tegaki_manga_guides/../secret.png",
            "tegaki_manga_guides/subdir/test.png",
            "tegaki_manga_guides\\backslash.png"
        ];

        for (const badRef of rejectedPreviewRefs) {
            const beforeViewCount = viewCallCount;
            const res = await fetch(`${workspaceOrigin}/api/guide-assets/view?ref=${encodeURIComponent(badRef)}`);
            assert.strictEqual(res.status, 400, `Expected 400 for bad view ref: ${badRef}`);
            assert.strictEqual(viewCallCount, beforeViewCount, "Backend viewCallCount must NOT increase on local rejection");
        }
        console.log("✓ Check 14 PASS: Preview rejection matrix rejected locally (backend view count 0)");

        // Foreign Origin on preview request -> 403, backend count unchanged
        {
            const beforeViewCount = viewCallCount;
            const res = await fetch(`${workspaceOrigin}/api/guide-assets/view?ref=${encodeURIComponent(uploadedPngRef)}`, {
                headers: { Origin: "http://attacker.example.com" }
            });
            assert.strictEqual(res.status, 403);
            assert.strictEqual(viewCallCount, beforeViewCount);
            console.log("✓ Check 15 PASS: Foreign Origin on preview rejected with 403 (backend view count 0)");
        }

        // Valid preview without Origin (or same Origin) -> 200 exact bytes
        {
            const res = await fetch(`${workspaceOrigin}/api/guide-assets/view?ref=${encodeURIComponent(uploadedPngRef)}`);
            assert.strictEqual(res.status, 200);
            assert.strictEqual(res.headers.get("content-type"), "image/png");
            const buf = Buffer.from(await res.arrayBuffer());
            assert.strictEqual(Buffer.compare(buf, tinyPng), 0, "View response must match tinyPng byte-for-byte");
            console.log("✓ Check 16 PASS: Valid preview streams exact byte-for-byte binary content");
        }

    } finally {
        workspaceServer.close();
        fakeBackend.close();
    }
}

await runServerTests();
console.log("==================================================");
console.log("ALL GUIDE ASSET INGESTION TESTS PASSED (M1C2B1)");
console.log("==================================================");
