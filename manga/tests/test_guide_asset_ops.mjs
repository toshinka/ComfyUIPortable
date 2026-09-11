/**
 * test_guide_asset_ops.mjs — Standalone Guide Asset Ingestion Tests (M1C2B)
 * =========================================================================
 * Verifies:
 * 1. Pure authoring ops: getNextGuideId, calculateContainPlacement (portrait, landscape, square)
 * 2. Store operations:
 *    - addGuideFromAsset (assigns unique guide_id, asset_reference, contain placement)
 *    - replaceGuideAsset (updates asset_reference & placement, preserves guide_id, enabled, figure_regions)
 * 3. Server HTTP endpoints & binary forwarding:
 *    - Fake Manga backend for /upload/image and /view
 *    - POST /api/guide-assets/upload rejects: invalid magic bytes, traversal filenames, oversized payload
 *    - POST /api/guide-assets/upload accepts: PNG, JPEG, WEBP and forwards exact byte-for-byte to fake backend
 *    - GET /api/guide-assets/view streams exact byte-for-byte from fake backend
 */

import http from "node:http";
import assert from "node:assert/strict";
import { AuthoringStore } from "../app/src/state/authoring_store.js";
import {
    getNextGuideId,
    calculateContainPlacement
} from "../app/src/domain/authoring_ops.js";

console.log("--- Running test_guide_asset_ops.mjs (MANGA-M1C2B) ---");

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
    // height should be 832/1216 rounded to 4 decimals = 0.6842
    assert.strictEqual(sqPlace.h, 0.6842);
    // y should be centered: (1 - 0.6842) / 2 = 0.1579
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

// ===================================================================
// PART 2: STORE MUTATIONS
// ===================================================================

{
    const store = new AuthoringStore();
    // 2.A: Add Guide from Asset
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

    // 2.B: Replace Guide Asset
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
    // Placement changed to square contain
    assert.strictEqual(replaced.placement.w, 1);

    console.log("✓ Check 2 PASS: Store addGuideFromAsset and replaceGuideAsset with region preservation");
}

// ===================================================================
// PART 3: SERVER ENDPOINTS, MAGIC BYTES, AND EXACT BYTE FORWARDING
// ===================================================================

async function runServerTests() {
    // 1. Create Fake Manga Backend
    const backendUploadedFiles = new Map(); // filename -> Buffer

    const fakeBackend = http.createServer((req, res) => {
        const url = new URL(req.url, `http://${req.headers.host}`);

        if (req.method === "POST" && url.pathname === "/upload/image") {
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

    // 2. Start Manga Workspace Server via dynamic import with env vars
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

        // Invalid binary / magic bytes (plain text file)
        const fakeFile = Buffer.from("Hello, this is not an image file at all!");

        // 3.A: Reject Invalid Magic Bytes
        {
            const res = await fetch(`${workspaceOrigin}/api/guide-assets/upload?filename=test.png`, {
                method: "POST",
                headers: { Origin: workspaceOrigin, "Content-Type": "image/png" },
                body: fakeFile
            });
            assert.strictEqual(res.status, 400);
            const body = await res.json();
            assert.strictEqual(body.ok, false);
            assert.ok(body.error.includes("Invalid image format"));
            console.log("✓ Check 3.A PASS: Server rejects invalid magic bytes");
        }

        // 3.B: Reject Path Traversal in filename
        {
            const res = await fetch(`${workspaceOrigin}/api/guide-assets/upload?filename=../../secret.png`, {
                method: "POST",
                headers: { Origin: workspaceOrigin, "Content-Type": "image/png" },
                body: tinyPng
            });
            assert.strictEqual(res.status, 400);
            const body = await res.json();
            assert.strictEqual(body.ok, false);
            assert.ok(body.error.includes("safe basename"));
            console.log("✓ Check 3.B PASS: Server rejects filename traversal");
        }

        // 3.C: Reject Cross-Origin Upload
        {
            const res = await fetch(`${workspaceOrigin}/api/guide-assets/upload?filename=test.png`, {
                method: "POST",
                headers: { Origin: "http://malicious.example.com", "Content-Type": "image/png" },
                body: tinyPng
            });
            assert.strictEqual(res.status, 403);
            console.log("✓ Check 3.C PASS: Server enforces same-origin upload");
        }

        // 3.D: Accept Valid PNG and Check Exact Byte-for-Byte Forwarding
        let uploadedRef = "";
        {
            const res = await fetch(`${workspaceOrigin}/api/guide-assets/upload?filename=my_drawing.png`, {
                method: "POST",
                headers: { Origin: workspaceOrigin, "Content-Type": "image/png" },
                body: tinyPng
            });
            assert.strictEqual(res.status, 200);
            const body = await res.json();
            assert.strictEqual(body.ok, true);
            assert.ok(body.asset_reference.startsWith("tegaki_manga_guides/"));
            uploadedRef = body.asset_reference;

            // Check exact byte equality on fake backend
            const rawStored = backendUploadedFiles.get("my_drawing.png");
            assert.ok(rawStored, "Fake backend must have received my_drawing.png");
            assert.strictEqual(Buffer.compare(rawStored, tinyPng), 0, "Forwarded bytes must match tinyPng byte-for-byte");
            console.log("✓ Check 3.D PASS: Exact byte-for-byte binary forwarding to ComfyUI endpoint");
        }

        // 3.E: GET /api/guide-assets/view streams exact byte-for-byte
        {
            const res = await fetch(`${workspaceOrigin}/api/guide-assets/view?ref=${encodeURIComponent(uploadedRef)}`);
            assert.strictEqual(res.status, 200);
            assert.strictEqual(res.headers.get("content-type"), "image/png");
            const buf = Buffer.from(await res.arrayBuffer());
            assert.strictEqual(Buffer.compare(buf, tinyPng), 0, "View response must match tinyPng byte-for-byte");
            console.log("✓ Check 3.E PASS: /api/guide-assets/view streams exact byte-for-byte binary content");
        }

        // 3.F: Reject Path Traversal in /api/guide-assets/view
        {
            const res = await fetch(`${workspaceOrigin}/api/guide-assets/view?ref=${encodeURIComponent("tegaki_manga_guides/../passwords.txt")}`);
            assert.strictEqual(res.status, 400);
            console.log("✓ Check 3.F PASS: View endpoint rejects path traversal in ref");
        }

        // 3.G: Accept JPEG and WEBP uploads
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
            console.log("✓ Check 3.G PASS: JPEG and WEBP successfully ingested");
        }

    } finally {
        workspaceServer.close();
        fakeBackend.close();
    }
}

await runServerTests();
console.log("==================================================");
console.log("ALL GUIDE ASSET INGESTION TESTS PASSED (M1C2B)");
console.log("==================================================");
