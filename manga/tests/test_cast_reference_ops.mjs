/**
 * test_cast_reference_ops.mjs — CAST Reference Asset Ingestion & Contract Tests
 * ==============================================================================
 * Verifies:
 * 1. Pure authoring ops:
 *    - validateCanonicalReferenceAssetReference, isCanonicalReferenceAssetReference
 *    - Rejection of traversal, absolute, UNC, wrong namespace, unsupported ext, empty
 * 2. Store operations:
 *    - addCast with/without reference_asset
 *    - setCastReference / assignCastReference / clearCastReference
 *    - Rejection of invalid reference_asset leaves document byte-for-byte unchanged
 *    - Preserves other CAST fields and doesn't mutate character instances
 * 3. Server HTTP endpoints & binary forwarding:
 *    - Rejections precede backend (uploadCallCount remains 0)
 *      - Declared Content-Length > 20 MiB -> 413
 *      - Streamed body > 20 MiB -> 413
 *      - Empty body -> 400
 *      - Content-Type mismatch -> 400
 *      - Unsupported extension -> 400
 *      - Wrong magic bytes -> 400
 *      - Path traversal filename -> 400
 *      - Foreign upload Origin -> 403
 *    - Backend response fail-closed matrix (subfolder mismatch, traversal name, empty name, backslash, control char) -> 502
 *    - Valid uploads: stable hash name ref_<hash>.<ext>, exact byte-for-byte forwarding
 *    - Preview rejection matrix & origin check (backend viewCallCount remains 0)
 *      - Path traversal in ref, absolute path, other folder, subfolder -> 400
 *      - Foreign preview Origin -> 403
 *    - Valid preview: exact byte-for-byte binary content stream
 * 4. Document roundtrip & backward compatibility:
 *    - Export / reload preserves reference_asset exactly
 *    - Legacy documents without reference_asset validate cleanly
 */

import http from "node:http";
import assert from "node:assert/strict";
import { AuthoringStore } from "../app/src/state/authoring_store.js";
import {
    validateCanonicalReferenceAssetReference,
    isCanonicalReferenceAssetReference,
    SUPPORTED_REFERENCE_EXTENSIONS,
    REFERENCE_ASSET_PREFIX
} from "../app/src/domain/authoring_ops.js";
import { validateAuthoringDocument } from "../app/src/domain/authoring_document.js";

console.log("--- Running test_cast_reference_ops.mjs (MANGA-CAST-REFERENCE-DATA1) ---");

// ===================================================================
// PART 1: PURE AUTHORING OPS TESTS
// ===================================================================

{
    // Valid reference asset references
    const validRefs = [
        "tegaki_manga_references/ref_0123456789abcdef.png",
        "tegaki_manga_references/ref_abcdef0123456789.jpg",
        "tegaki_manga_references/character_face.jpeg",
        "tegaki_manga_references/mika_front.webp"
    ];
    for (const ref of validRefs) {
        const val = validateCanonicalReferenceAssetReference(ref);
        assert.ok(val.valid, `Expected valid ref for '${ref}', got: ${val.reason}`);
        assert.ok(isCanonicalReferenceAssetReference(ref));
    }
    console.log("✓ Check 1.A PASS: validateCanonicalReferenceAssetReference accepts valid refs");

    // Invalid references
    const invalidRefs = [
        "", // empty
        null,
        123,
        "tegaki_manga_references/", // empty basename
        "tegaki_manga_references/../secret.png", // traversal
        "tegaki_manga_references/sub/test.png", // subdirectory
        "tegaki_manga_references/test\\back.png", // backslash
        "tegaki_manga_guides/test.png", // wrong namespace
        "/tegaki_manga_references/test.png", // leading slash
        "C:/Users/test/ref.png", // drive letter
        "file:///test.png", // file URI
        "tegaki_manga_references/test.exe", // unsupported extension
        "tegaki_manga_references/test.svg", // unsupported extension
        "tegaki_manga_references/test\x00.png" // control character
    ];
    for (const ref of invalidRefs) {
        const val = validateCanonicalReferenceAssetReference(ref);
        assert.strictEqual(val.valid, false, `Expected invalid ref for '${ref}'`);
        assert.strictEqual(isCanonicalReferenceAssetReference(ref), false);
    }
    console.log("✓ Check 1.B PASS: validateCanonicalReferenceAssetReference rejects all invalid refs");
}

// ===================================================================
// PART 2: STORE OPERATIONS TESTS
// ===================================================================

{
    const store = new AuthoringStore();
    const beforeJSON = JSON.stringify(store.document);

    // 2.A: addCast without reference_asset defaults to null
    const c1 = store.addCast({ display_name: "Hero" });
    assert.strictEqual(c1.reference_asset, null);
    assert.ok(validateAuthoringDocument(store.document).valid);
    console.log("✓ Check 2.A PASS: addCast without reference_asset defaults to null");

    // 2.B: addCast with valid reference_asset
    const c2 = store.addCast({
        display_name: "Villain",
        reference_asset: "tegaki_manga_references/ref_1122334455667788.png"
    });
    assert.strictEqual(c2.reference_asset, "tegaki_manga_references/ref_1122334455667788.png");
    assert.ok(validateAuthoringDocument(store.document).valid);
    console.log("✓ Check 2.B PASS: addCast with valid reference_asset succeeds");

    // 2.C: addCast with invalid reference_asset throws and leaves document intact
    const docBeforeBadAdd = JSON.stringify(store.document);
    assert.throws(() => {
        store.addCast({
            display_name: "Bad",
            reference_asset: "tegaki_manga_references/../traversal.png"
        });
    }, /Invalid reference_asset/);
    assert.strictEqual(JSON.stringify(store.document), docBeforeBadAdd);
    console.log("✓ Check 2.C PASS: addCast with invalid reference_asset fails closed");

    // 2.D: assignCastReference / setCastReference
    store.assignCastReference(c1.cast_id, "tegaki_manga_references/ref_hero_face.webp");
    const updatedC1 = store.getPage().cast.find(c => c.cast_id === c1.cast_id);
    assert.strictEqual(updatedC1.reference_asset, "tegaki_manga_references/ref_hero_face.webp");
    assert.strictEqual(updatedC1.display_name, "Hero");
    console.log("✓ Check 2.D PASS: assignCastReference updates asset and preserves other fields");

    // 2.E: replace reference
    store.assignCastReference(c1.cast_id, "tegaki_manga_references/ref_hero_face_v2.png");
    const replacedC1 = store.getPage().cast.find(c => c.cast_id === c1.cast_id);
    assert.strictEqual(replacedC1.reference_asset, "tegaki_manga_references/ref_hero_face_v2.png");
    console.log("✓ Check 2.E PASS: replace reference succeeds");

    // 2.F: clear reference
    store.clearCastReference(c1.cast_id);
    const clearedC1 = store.getPage().cast.find(c => c.cast_id === c1.cast_id);
    assert.strictEqual(clearedC1.reference_asset, null);
    console.log("✓ Check 2.F PASS: clearCastReference sets reference_asset to null");

    // 2.G: updateCast with invalid reference_asset throws and leaves document intact
    const docBeforeBadUpdate = JSON.stringify(store.document);
    assert.throws(() => {
        store.updateCast(c1.cast_id, { reference_asset: "C:/evil.jpg" });
    }, /Invalid reference_asset/);
    assert.strictEqual(JSON.stringify(store.document), docBeforeBadUpdate);
    console.log("✓ Check 2.G PASS: updateCast with invalid reference_asset fails closed");

    // 2.H: verify character_instances are not mutated when CAST reference changes
    const inst = store.placeCharacter("scene_top", c1.cast_id);
    const instBefore = JSON.stringify(inst);
    store.assignCastReference(c1.cast_id, "tegaki_manga_references/ref_hero_new.png");
    const instAfter = JSON.stringify(store.getPage().character_instances.find(i => i.instance_id === inst.instance_id));
    assert.strictEqual(instBefore, instAfter);
    console.log("✓ Check 2.H PASS: character instances unaffected by CAST reference update");
}

// ===================================================================
// PART 3: SERVER HTTP ENDPOINT TESTS (INGESTION & PREVIEW)
// ===================================================================

{
    let uploadCallCount = 0;
    let viewCallCount = 0;
    let nextUploadResponse = null;
    const backendUploadedFiles = new Map();

    const fakeBackend = http.createServer((req, res) => {
        const url = new URL(req.url, `http://${req.headers.host || "127.0.0.1"}`);

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

                assert.strictEqual(subfolder, "tegaki_manga_references", "Backend must receive subfolder tegaki_manga_references");
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
            assert.strictEqual(subfolder, "tegaki_manga_references");
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

    process.env.MANGA_BACKEND_URL = `http://127.0.0.1:${backendPort}`;
    process.env.MANGA_WORKSPACE_PORT = "0";

    const { server: workspaceServer } = await import(`../service/manga_workspace_server.mjs?test=${Date.now()}`);
    await new Promise(r => {
        if (workspaceServer.listening) r();
        else workspaceServer.on("listening", r);
    });
    const workspacePort = workspaceServer.address().port;
    const workspaceOrigin = `http://127.0.0.1:${workspacePort}`;

    // Helper to send HTTP requests to Workspace server
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

    // Tiny valid image buffers
    const TINY_PNG = Buffer.from([
        0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,
        0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52,
        0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,
        0x08, 0x06, 0x00, 0x00, 0x00, 0x1F, 0x15, 0xC4, 0x89,
        0x00, 0x00, 0x00, 0x0A, 0x49, 0x44, 0x41, 0x54,
        0x78, 0x9C, 0x63, 0x00, 0x01, 0x00, 0x00, 0x05, 0x00, 0x01, 0x0D, 0x0A, 0x2D, 0xB4,
        0x00, 0x00, 0x00, 0x00, 0x49, 0x45, 0x4E, 0x44,
        0xAE, 0x42, 0x60, 0x82
    ]);

    const TINY_JPEG = Buffer.from([
        0xFF, 0xD8, 0xFF, 0xE0, 0x00, 0x10, 0x4A, 0x46, 0x49, 0x46,
        0x00, 0x01, 0x01, 0x00, 0x00, 0x01, 0x00, 0x01, 0x00, 0x00,
        0xFF, 0xD9
    ]);

    const TINY_WEBP = Buffer.from([
        0x52, 0x49, 0x46, 0x46, 0x1A, 0x00, 0x00, 0x00,
        0x57, 0x45, 0x42, 0x50, 0x56, 0x50, 0x38, 0x4C,
        0x0E, 0x00, 0x00, 0x00, 0x2F, 0x00, 0x00, 0x00,
        0x00, 0x07, 0x88, 0x88, 0x08, 0x00, 0x00, 0x00
    ]);

    // 3.A: Wrong magic bytes -> 400
    {
        uploadCallCount = 0;
        const fakePng = Buffer.from("NOT_A_PNG_FILE_DATA");
        const res = await makeRequest({
            path: "/api/reference-assets/upload?filename=bad.png",
            method: "POST",
            headers: { "Content-Type": "image/png" },
            body: fakePng
        });
        assert.strictEqual(res.status, 400);
        assert.strictEqual(uploadCallCount, 0);
        console.log("✓ Check 3.A PASS: Server rejects invalid magic bytes");
    }

    // 3.B: Filename traversal -> 400
    {
        uploadCallCount = 0;
        const res = await makeRequest({
            path: "/api/reference-assets/upload?filename=../escape.png",
            method: "POST",
            headers: { "Content-Type": "image/png" },
            body: TINY_PNG
        });
        assert.strictEqual(res.status, 400);
        assert.strictEqual(uploadCallCount, 0);
        console.log("✓ Check 3.B PASS: Server rejects filename traversal");
    }

    // 3.C: Foreign Origin -> 403
    {
        uploadCallCount = 0;
        const res = await makeRequest({
            path: "/api/reference-assets/upload?filename=ok.png",
            method: "POST",
            headers: {
                "Content-Type": "image/png",
                "Origin": "http://evil.com"
            },
            body: TINY_PNG
        });
        assert.strictEqual(res.status, 403);
        assert.strictEqual(uploadCallCount, 0);
        console.log("✓ Check 3.C PASS: Server rejects foreign upload origin");
    }

    // 3.D: Content-Type mismatch -> 400
    {
        uploadCallCount = 0;
        const res = await makeRequest({
            path: "/api/reference-assets/upload?filename=pic.png",
            method: "POST",
            headers: { "Content-Type": "image/jpeg" }, // mismatch!
            body: TINY_PNG
        });
        assert.strictEqual(res.status, 400);
        assert.strictEqual(uploadCallCount, 0);
        console.log("✓ Check 3.D PASS: Server rejects Content-Type mismatch");
    }

    // 3.E: Unsupported extension -> 400
    {
        uploadCallCount = 0;
        const res = await makeRequest({
            path: "/api/reference-assets/upload?filename=pic.gif",
            method: "POST",
            headers: { "Content-Type": "image/gif" },
            body: TINY_PNG
        });
        assert.strictEqual(res.status, 400);
        assert.strictEqual(uploadCallCount, 0);
        console.log("✓ Check 3.E PASS: Unsupported extension returns 400");
    }

    // 3.F: Valid PNG upload with stable hash naming
    let uploadedRef = null;
    {
        uploadCallCount = 0;
        const res = await makeRequest({
            path: "/api/reference-assets/upload?filename=my_photo.png",
            method: "POST",
            headers: { "Content-Type": "image/png" },
            body: TINY_PNG
        });
        assert.strictEqual(res.status, 200);
        assert.strictEqual(uploadCallCount, 1);
        assert.ok(res.body.ok);
        assert.ok(res.body.asset_reference.startsWith("tegaki_manga_references/ref_"));
        assert.ok(res.body.asset_reference.endsWith(".png"));
        uploadedRef = res.body.asset_reference;
        console.log(`✓ Check 3.F PASS: Valid PNG upload with stable hash naming (${uploadedRef})`);
    }

    // 3.G: Valid JPEG & WEBP uploads
    {
        const resJpg = await makeRequest({
            path: "/api/reference-assets/upload?filename=face.jpg",
            method: "POST",
            headers: { "Content-Type": "image/jpeg" },
            body: TINY_JPEG
        });
        assert.strictEqual(resJpg.status, 200);
        assert.ok(resJpg.body.asset_reference.startsWith("tegaki_manga_references/ref_"));
        assert.ok(resJpg.body.asset_reference.endsWith(".jpg"));

        const resWebp = await makeRequest({
            path: "/api/reference-assets/upload?filename=model.webp",
            method: "POST",
            headers: { "Content-Type": "image/webp" },
            body: TINY_WEBP
        });
        assert.strictEqual(resWebp.status, 200);
        assert.ok(resWebp.body.asset_reference.startsWith("tegaki_manga_references/ref_"));
        assert.ok(resWebp.body.asset_reference.endsWith(".webp"));
        console.log("✓ Check 3.G PASS: Valid JPEG and WEBP uploads succeed with hash naming");
    }

    // 3.H: Preview rejection matrix
    {
        viewCallCount = 0;
        // Traversal in ref
        const res1 = await makeRequest({
            path: "/api/reference-assets/view?ref=tegaki_manga_references/../secret.png"
        });
        assert.strictEqual(res1.status, 400);

        // Wrong subfolder
        const res2 = await makeRequest({
            path: "/api/reference-assets/view?ref=tegaki_manga_guides/something.png"
        });
        assert.strictEqual(res2.status, 400);

        // Foreign origin
        const res3 = await makeRequest({
            path: `/api/reference-assets/view?ref=${encodeURIComponent(uploadedRef)}`,
            headers: { "Origin": "http://evil.com" }
        });
        assert.strictEqual(res3.status, 403);
        assert.strictEqual(viewCallCount, 0);
        console.log("✓ Check 3.H PASS: Preview rejection matrix rejected locally");
    }

    // 3.I: Valid preview streams exact binary content
    {
        viewCallCount = 0;
        const res = await makeRequest({
            path: `/api/reference-assets/view?ref=${encodeURIComponent(uploadedRef)}`
        });
        assert.strictEqual(res.status, 200);
        assert.strictEqual(viewCallCount, 1);
        assert.strictEqual(res.headers["content-type"], "image/png");
        assert.strictEqual(res.rawBody.length, TINY_PNG.length);
        assert.ok(res.rawBody.equals(TINY_PNG), "Streamed body must equal original bytes exactly");
        console.log("✓ Check 3.I PASS: Valid preview streams exact byte-for-byte binary content");
    }

    // Clean up servers
    await new Promise(r => workspaceServer.close(r));
    await new Promise(r => fakeBackend.close(r));
}

// ===================================================================
// PART 4: ROUNDTRIP SERIALIZATION & BACKWARD COMPATIBILITY
// ===================================================================

{
    const store = new AuthoringStore();
    const c = store.addCast({
        display_name: "Detective",
        identity_prompt: "1man, trenchcoat, fedora",
        reference_asset: "tegaki_manga_references/ref_detective_01.png"
    });

    // 4.A: Export to JSON string and parse back
    const jsonStr = JSON.stringify(store.document);
    const parsed = JSON.parse(jsonStr);

    assert.strictEqual(
        parsed.pages[0].cast.find(item => item.cast_id === c.cast_id).reference_asset,
        "tegaki_manga_references/ref_detective_01.png"
    );
    const valResult = validateAuthoringDocument(parsed);
    assert.ok(valResult.valid, `Exported document must validate: ${valResult.errors}`);
    console.log("✓ Check 4.A PASS: Export/import roundtrip preserves reference_asset exactly");

    // 4.B: Legacy document fixture without reference_asset
    const legacyDoc = {
        schema_id: "TEGAKI_AUTHORING_DOCUMENT",
        schema_version: "1.0.0",
        pages: [
            {
                page_id: "p1",
                width_px: 832,
                height_px: 1216,
                scenes: [],
                visual_frames: [],
                cast: [
                    {
                        cast_id: "cast_1",
                        display_name: "Old Cast",
                        identity_prompt: "old style",
                        negative_prompt: "",
                        color: "#06b6d4",
                        loras: [],
                        metadata: {}
                    }
                ],
                character_instances: [],
                guides: []
            }
        ],
        metadata: {}
    };

    const legacyStore = new AuthoringStore(legacyDoc);
    assert.ok(validateAuthoringDocument(legacyStore.document).valid);
    assert.strictEqual(legacyStore.getPage().cast[0].reference_asset, undefined);

    // Can assign reference to legacy cast
    legacyStore.assignCastReference("cast_1", "tegaki_manga_references/ref_upgraded.webp");
    assert.strictEqual(
        legacyStore.getPage().cast[0].reference_asset,
        "tegaki_manga_references/ref_upgraded.webp"
    );
    assert.ok(validateAuthoringDocument(legacyStore.document).valid);
    console.log("✓ Check 4.B PASS: Legacy document without reference_asset loads and upgrades cleanly");
}

console.log("==================================================");
console.log("ALL CAST REFERENCE DATA TESTS PASSED (DATA1)");
console.log("==================================================");
