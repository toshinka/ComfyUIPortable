import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs/promises";
import path from "node:path";
import os from "node:os";
import { createHash } from "node:crypto";

import {
    ReferenceAssetAnalyzerError,
    validateCanonicalReferenceAsset,
    analyzeReferenceAsset,
} from "../service/reference_asset_analyzer.mjs";

test("A. A valid canonical Reference identifier resolves beneath the designated permitted root", async () => {
    const tmpDir = await fs.mkdtemp(path.join(os.tmpdir(), "ref-test-a-"));
    try {
        const refDir = path.join(tmpDir, "tegaki_manga_references");
        await fs.mkdir(refDir, { recursive: true });

        const filename = "ref_heroine_01.png";
        const fileBytes = Buffer.from("fake-png-heroine-image-data-12345");
        await fs.writeFile(path.join(refDir, filename), fileBytes);

        const identifier = `tegaki_manga_references/${filename}`;
        const result = await analyzeReferenceAsset({
            referenceAsset: identifier,
            permittedRoot: tmpDir,
        });

        assert.equal(result.enabled, true);
        assert.equal(result.reference_asset, identifier);
        assert.equal(result.byte_length, fileBytes.length);
        assert.match(result.content_digest, /^[0-9a-f]{64}$/);
    } finally {
        await fs.rm(tmpDir, { recursive: true, force: true });
    }
});

test("B. The digest matches SHA-256 of the exact file bytes", async () => {
    const tmpDir = await fs.mkdtemp(path.join(os.tmpdir(), "ref-test-b-"));
    try {
        const refDir = path.join(tmpDir, "tegaki_manga_references");
        await fs.mkdir(refDir, { recursive: true });

        const filename = "ref_test_bytes.jpg";
        const fileBytes = Buffer.from("exact-image-binary-payload-bytes-999");
        await fs.writeFile(path.join(refDir, filename), fileBytes);

        const expectedDigest = createHash("sha256").update(fileBytes).digest("hex");

        const result = await analyzeReferenceAsset({
            referenceAsset: `tegaki_manga_references/${filename}`,
            permittedRoot: tmpDir,
        });

        assert.equal(result.content_digest, expectedDigest);
    } finally {
        await fs.rm(tmpDir, { recursive: true, force: true });
    }
});

test("C. Replacing the test file's bytes changes the returned digest", async () => {
    const tmpDir = await fs.mkdtemp(path.join(os.tmpdir(), "ref-test-c-"));
    try {
        const refDir = path.join(tmpDir, "tegaki_manga_references");
        await fs.mkdir(refDir, { recursive: true });

        const filename = "ref_mutable.webp";
        const filePath = path.join(refDir, filename);

        await fs.writeFile(filePath, Buffer.from("initial-content-version-1"));
        const result1 = await analyzeReferenceAsset({
            referenceAsset: `tegaki_manga_references/${filename}`,
            permittedRoot: tmpDir,
        });

        await fs.writeFile(filePath, Buffer.from("replaced-content-version-2"));
        const result2 = await analyzeReferenceAsset({
            referenceAsset: `tegaki_manga_references/${filename}`,
            permittedRoot: tmpDir,
        });

        assert.notEqual(result1.content_digest, result2.content_digest);
    } finally {
        await fs.rm(tmpDir, { recursive: true, force: true });
    }
});

test("D. An explicit disabled Reference produces content_digest: null without reading a file", async () => {
    // 1. With enabled: false
    const res1 = await analyzeReferenceAsset({ enabled: false });
    assert.deepEqual(res1, {
        enabled: false,
        reference_asset: null,
        content_digest: null,
        byte_length: null,
    });

    // 2. With referenceAsset: null
    const res2 = await analyzeReferenceAsset({ referenceAsset: null });
    assert.deepEqual(res2, {
        enabled: false,
        reference_asset: null,
        content_digest: null,
        byte_length: null,
    });

    // 3. With empty input object
    const res3 = await analyzeReferenceAsset({});
    assert.deepEqual(res3, {
        enabled: false,
        reference_asset: null,
        content_digest: null,
        byte_length: null,
    });
});

test("E. An active Reference with a missing filename fails", async () => {
    for (const badId of [
        "tegaki_manga_references/",
        "tegaki_manga_references",
        "",
    ]) {
        await assert.rejects(
            async () => await analyzeReferenceAsset({ referenceAsset: badId, permittedRoot: "ignored" }),
            (err) => err instanceof ReferenceAssetAnalyzerError && err.code === "INVALID_REFERENCE_IDENTIFIER"
        );
    }
});

test("F. Absolute paths and traversal attempts fail", async () => {
    for (const badId of [
        "/tegaki_manga_references/ref.png",
        "C:/tegaki_manga_references/ref.png",
        "tegaki_manga_references/../secret.png",
        "tegaki_manga_references/sub/../../secret.png",
        "file:///tegaki_manga_references/ref.png",
    ]) {
        await assert.rejects(
            async () => await analyzeReferenceAsset({ referenceAsset: badId, permittedRoot: "ignored" }),
            (err) => err instanceof ReferenceAssetAnalyzerError && err.code === "INVALID_REFERENCE_IDENTIFIER"
        );
    }
});

test("G. Backslashes and nested paths outside the approved single-level namespace fail", async () => {
    for (const badId of [
        "tegaki_manga_references\\ref.png",
        "tegaki_manga_references/subfolder/ref.png",
        "tegaki_manga_references/a/b/c.png",
        "tegaki_manga_references/ref.unsupported_ext",
    ]) {
        await assert.rejects(
            async () => await analyzeReferenceAsset({ referenceAsset: badId, permittedRoot: "ignored" }),
            (err) => err instanceof ReferenceAssetAnalyzerError && err.code === "INVALID_REFERENCE_IDENTIFIER"
        );
    }
});

test("H. A missing asset fails explicitly", async () => {
    const tmpDir = await fs.mkdtemp(path.join(os.tmpdir(), "ref-test-h-"));
    try {
        const refDir = path.join(tmpDir, "tegaki_manga_references");
        await fs.mkdir(refDir, { recursive: true });

        await assert.rejects(
            async () => await analyzeReferenceAsset({
                referenceAsset: "tegaki_manga_references/non_existent.png",
                permittedRoot: tmpDir,
            }),
            (err) => err instanceof ReferenceAssetAnalyzerError && err.code === "ASSET_NOT_FOUND"
        );
    } finally {
        await fs.rm(tmpDir, { recursive: true, force: true });
    }
});

test("I. An unreadable or empty asset does not produce successful provenance", async () => {
    const tmpDir = await fs.mkdtemp(path.join(os.tmpdir(), "ref-test-i-"));
    try {
        const refDir = path.join(tmpDir, "tegaki_manga_references");
        await fs.mkdir(refDir, { recursive: true });

        const emptyFile = path.join(refDir, "empty_ref.png");
        await fs.writeFile(emptyFile, Buffer.alloc(0));

        await assert.rejects(
            async () => await analyzeReferenceAsset({
                referenceAsset: "tegaki_manga_references/empty_ref.png",
                permittedRoot: tmpDir,
            }),
            (err) => err instanceof ReferenceAssetAnalyzerError && err.code === "EMPTY_ASSET"
        );
    } finally {
        await fs.rm(tmpDir, { recursive: true, force: true });
    }
});

test("J. A symlink escaping the permitted root is rejected, where the active test environment supports creating such a symlink", async () => {
    const tmpDir = await fs.mkdtemp(path.join(os.tmpdir(), "ref-test-j-"));
    const outsideDir = await fs.mkdtemp(path.join(os.tmpdir(), "ref-test-outside-"));
    try {
        const refDir = path.join(tmpDir, "tegaki_manga_references");
        await fs.mkdir(refDir, { recursive: true });

        const outsideFile = path.join(outsideDir, "outside_secret.png");
        await fs.writeFile(outsideFile, Buffer.from("sensitive-data-outside-root"));

        const symlinkPath = path.join(refDir, "symlink_ref.png");
        let symlinkCreated = false;
        try {
            await fs.symlink(outsideFile, symlinkPath);
            symlinkCreated = true;
        } catch {
            // Test environment does not permit creating symlinks; skip gracefully
        }

        if (symlinkCreated) {
            await assert.rejects(
                async () => await analyzeReferenceAsset({
                    referenceAsset: "tegaki_manga_references/symlink_ref.png",
                    permittedRoot: tmpDir,
                }),
                (err) => err instanceof ReferenceAssetAnalyzerError && err.code === "PATH_TRAVERSAL"
            );
        }
    } finally {
        await fs.rm(tmpDir, { recursive: true, force: true });
        await fs.rm(outsideDir, { recursive: true, force: true });
    }
});

test("K. No network request, ComfyUI job, checkpoint load or GPU operation is required", () => {
    // Pure canonical validator functions work standalone synchronously
    const basename = validateCanonicalReferenceAsset("tegaki_manga_references/heroine_01.jpg");
    assert.equal(basename, "heroine_01.jpg");

    // Invalid identifiers reject without I/O
    assert.throws(
        () => validateCanonicalReferenceAsset("invalid/prefix/test.png"),
        (err) => err instanceof ReferenceAssetAnalyzerError && err.code === "INVALID_REFERENCE_IDENTIFIER"
    );
});
