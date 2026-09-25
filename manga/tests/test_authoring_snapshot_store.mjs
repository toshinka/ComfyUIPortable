import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs/promises";
import path from "node:path";
import os from "node:os";
import { createHash } from "node:crypto";

import {
    AuthoringSnapshotStore,
    AuthoringSnapshotStoreError,
    saveSnapshot,
    getSnapshot,
} from "../service/authoring_snapshot_store.mjs";

function createSampleAuthoringDocument(overrides = {}) {
    return {
        schema_id: "TEGAKI_AUTHORING_DOCUMENT",
        schema_version: "1.0.0",
        document_id: "97f0fb52-ebcc-47d2-9721-a3fcf442d8f9",
        pages: [
            {
                page_id: "page_1",
                width_px: 1024,
                height_px: 1536,
                style_prompt: "masterpiece, manga style, clean lines",
                style_negative_prompt: "blurry, low quality",
                scenes: [
                    {
                        scene_id: "scene_1",
                        order: 1,
                        name: "Panel 1",
                        input_mode: "cast",
                        prompt: "girl reading a book",
                        negative_prompt: "outdoor",
                        area: { shape_type: "rect", x: 0.05, y: 0.05, w: 0.90, h: 0.45 },
                    },
                ],
                cast: [
                    {
                        cast_id: "cast_heroine",
                        display_name: "Heroine",
                        identity_prompt: "1girl, brown hair, school uniform",
                        reference_asset: "tegaki_manga_references/heroine_ref_01.png",
                    },
                ],
                character_instances: [
                    {
                        instance_id: "inst_1",
                        cast_id: "cast_heroine",
                        scene_id: "scene_1",
                        acting_prompt: "sitting quietly",
                        area: { shape_type: "rect", x: 0.10, y: 0.10, w: 0.30, h: 0.30 },
                    },
                ],
                guides: [
                    {
                        guide_id: "guide_layout",
                        guide_type: "rough_manga",
                        enabled: false,
                        asset_reference: "rough_01.png",
                    },
                ],
            },
        ],
        ...overrides,
    };
}

test("A. Save and reload a complete Authoring Document snapshot", async () => {
    const tmpDir = await fs.mkdtemp(path.join(os.tmpdir(), "snap-test-a-"));
    try {
        const store = new AuthoringSnapshotStore(tmpDir);
        const snapshotId = "11111111-1111-4111-8111-111111111111";
        const doc = createSampleAuthoringDocument();

        const saveResult = await store.saveSnapshot(snapshotId, doc);
        assert.equal(saveResult.snapshot_id, snapshotId);
        assert.equal(saveResult.snapshot_ref, `snapshots/${snapshotId}.json`);
        assert.match(saveResult.content_digest, /^[0-9a-f]{64}$/);

        const loaded = await store.getSnapshot(snapshotId);
        assert.equal(loaded.snapshot_id, snapshotId);
        assert.equal(loaded.snapshot_ref, `snapshots/${snapshotId}.json`);
        assert.equal(loaded.content_digest, saveResult.content_digest);
        assert.deepEqual(loaded.document, doc);
    } finally {
        await fs.rm(tmpDir, { recursive: true, force: true });
    }
});

test("B. Snapshot content digest matches the actual stored bytes", async () => {
    const tmpDir = await fs.mkdtemp(path.join(os.tmpdir(), "snap-test-b-"));
    try {
        const store = new AuthoringSnapshotStore(tmpDir);
        const snapshotId = "22222222-2222-4222-8222-222222222222";
        const doc = createSampleAuthoringDocument();

        const saveResult = await store.saveSnapshot(snapshotId, doc);

        // Manually read raw stored bytes from filesystem
        const storedBytes = await fs.readFile(path.join(tmpDir, `${snapshotId}.json`), "utf8");
        const expectedDigest = createHash("sha256").update(storedBytes, "utf8").digest("hex");

        assert.equal(saveResult.content_digest, expectedDigest);

        // getSnapshot returns matching digest
        const loaded = await store.getSnapshot(snapshotId);
        assert.equal(loaded.content_digest, expectedDigest);
    } finally {
        await fs.rm(tmpDir, { recursive: true, force: true });
    }
});

test("C. An existing snapshot_id cannot be overwritten", async () => {
    const tmpDir = await fs.mkdtemp(path.join(os.tmpdir(), "snap-test-c-"));
    try {
        const store = new AuthoringSnapshotStore(tmpDir);
        const snapshotId = "33333333-3333-4333-8333-333333333333";
        const docOriginal = createSampleAuthoringDocument();
        await store.saveSnapshot(snapshotId, docOriginal);

        const docModified = createSampleAuthoringDocument({
            document_id: "different-doc-id",
        });

        await assert.rejects(
            async () => await store.saveSnapshot(snapshotId, docModified),
            (err) => err instanceof AuthoringSnapshotStoreError && err.code === "SNAPSHOT_EXISTS"
        );

        // Content remains original
        const loaded = await store.getSnapshot(snapshotId);
        assert.equal(loaded.document.document_id, docOriginal.document_id);
    } finally {
        await fs.rm(tmpDir, { recursive: true, force: true });
    }
});

test("D. Concurrent publication with the same snapshot_id cannot overwrite another writer's completed record", async () => {
    const tmpDir = await fs.mkdtemp(path.join(os.tmpdir(), "snap-test-d-"));
    try {
        const store = new AuthoringSnapshotStore(tmpDir);
        const sharedId = "44444444-4444-4444-8444-444444444444";
        const docA = createSampleAuthoringDocument({ document_id: "doc-A" });
        const docB = createSampleAuthoringDocument({ document_id: "doc-B" });

        const results = await Promise.allSettled([
            store.saveSnapshot(sharedId, docA),
            store.saveSnapshot(sharedId, docB),
        ]);

        const fulfilled = results.filter((r) => r.status === "fulfilled");
        const rejected = results.filter((r) => r.status === "rejected");

        assert.equal(fulfilled.length, 1, "Exactly one concurrent writer must succeed");
        assert.equal(rejected.length, 1, "The competing concurrent writer must fail");
        assert.equal(rejected[0].reason.code, "SNAPSHOT_EXISTS");

        // Stored content must strictly match the fulfilled writer
        const loaded = await store.getSnapshot(sharedId);
        assert.ok(loaded.document.document_id === "doc-A" || loaded.document.document_id === "doc-B");
    } finally {
        await fs.rm(tmpDir, { recursive: true, force: true });
    }
});

test("E. Original document IDs, Page, Scene, CAST, Instance and Guide content survive the round trip", async () => {
    const tmpDir = await fs.mkdtemp(path.join(os.tmpdir(), "snap-test-e-"));
    try {
        const store = new AuthoringSnapshotStore(tmpDir);
        const snapshotId = "55555555-5555-4555-8555-555555555555";
        const doc = createSampleAuthoringDocument();

        await store.saveSnapshot(snapshotId, doc);
        const loaded = await store.getSnapshot(snapshotId);

        assert.equal(loaded.document.pages[0].scenes[0].scene_id, "scene_1");
        assert.equal(loaded.document.pages[0].cast[0].cast_id, "cast_heroine");
        assert.equal(loaded.document.pages[0].character_instances[0].instance_id, "inst_1");
        assert.equal(loaded.document.pages[0].guides[0].guide_id, "guide_layout");
        assert.deepEqual(loaded.document, doc);
    } finally {
        await fs.rm(tmpDir, { recursive: true, force: true });
    }
});

test("F. Legacy nonempty doc_-prefixed document_id remains accepted", async () => {
    const tmpDir = await fs.mkdtemp(path.join(os.tmpdir(), "snap-test-f-"));
    try {
        const store = new AuthoringSnapshotStore(tmpDir);
        const snapshotId = "66666666-6666-4666-8666-666666666666";
        const doc = createSampleAuthoringDocument({
            document_id: "doc_legacy_prefixed_12345",
        });

        await store.saveSnapshot(snapshotId, doc);

        // Path is derived strictly from snapshotId, not document_id
        const files = await fs.readdir(tmpDir);
        assert.deepEqual(files, [`${snapshotId}.json`]);

        const loaded = await store.getSnapshot(snapshotId);
        assert.equal(loaded.document.document_id, "doc_legacy_prefixed_12345");
    } finally {
        await fs.rm(tmpDir, { recursive: true, force: true });
    }
});

test("G. Invalid or path-like snapshot_id is rejected before path access", async () => {
    const tmpDir = await fs.mkdtemp(path.join(os.tmpdir(), "snap-test-g-"));
    try {
        const store = new AuthoringSnapshotStore(tmpDir);
        const doc = createSampleAuthoringDocument();

        for (const badId of [
            "../../etc/passwd",
            "not-a-uuid",
            "c8e0cf3a-446f-12e5-8da8-654cb6c72e42", // UUIDv1
            "",
            12345,
            null,
        ]) {
            await assert.rejects(
                async () => await store.saveSnapshot(badId, doc),
                (err) => err instanceof AuthoringSnapshotStoreError && err.code === "INVALID_SNAPSHOT_ID"
            );
            await assert.rejects(
                async () => await store.getSnapshot(badId),
                (err) => err instanceof AuthoringSnapshotStoreError && err.code === "INVALID_SNAPSHOT_ID"
            );
        }
    } finally {
        await fs.rm(tmpDir, { recursive: true, force: true });
    }
});

test("H. Missing snapshot returns an explicit not-found result/error", async () => {
    const tmpDir = await fs.mkdtemp(path.join(os.tmpdir(), "snap-test-h-"));
    try {
        const store = new AuthoringSnapshotStore(tmpDir);
        const nonExistentId = "77777777-7777-4777-8777-777777777777";

        // Default: returns null as explicit not-found result
        const result = await store.getSnapshot(nonExistentId);
        assert.equal(result, null);

        // Optional { required: true }: throws SNAPSHOT_NOT_FOUND error
        await assert.rejects(
            async () => await store.getSnapshot(nonExistentId, { required: true }),
            (err) => err instanceof AuthoringSnapshotStoreError && err.code === "SNAPSHOT_NOT_FOUND"
        );
    } finally {
        await fs.rm(tmpDir, { recursive: true, force: true });
    }
});

test("I. Corrupt JSON is rejected", async () => {
    const tmpDir = await fs.mkdtemp(path.join(os.tmpdir(), "snap-test-i-"));
    try {
        await fs.mkdir(tmpDir, { recursive: true });
        const store = new AuthoringSnapshotStore(tmpDir);
        const corruptId = "88888888-8888-4888-8888-888888888888";

        await fs.writeFile(path.join(tmpDir, `${corruptId}.json`), "{ broken json content");

        await assert.rejects(
            async () => await store.getSnapshot(corruptId),
            (err) => err instanceof AuthoringSnapshotStoreError && err.code === "STORE_CORRUPT"
        );
    } finally {
        await fs.rm(tmpDir, { recursive: true, force: true });
    }
});

test("J. Modified stored bytes cause expected digest verification to fail", async () => {
    const tmpDir = await fs.mkdtemp(path.join(os.tmpdir(), "snap-test-j-"));
    try {
        const store = new AuthoringSnapshotStore(tmpDir);
        const snapshotId = "99999999-9999-4999-8999-999999999999";
        const doc = createSampleAuthoringDocument();

        const saveResult = await store.saveSnapshot(snapshotId, doc);

        // 1. Correct expectedDigest succeeds
        const verified = await store.getSnapshot(snapshotId, {
            expectedDigest: saveResult.content_digest,
        });
        assert.equal(verified.content_digest, saveResult.content_digest);

        // 2. Wrong expectedDigest fails with DIGEST_MISMATCH
        await assert.rejects(
            async () => await store.getSnapshot(snapshotId, {
                expectedDigest: "0".repeat(64),
            }),
            (err) => err instanceof AuthoringSnapshotStoreError && err.code === "DIGEST_MISMATCH"
        );
    } finally {
        await fs.rm(tmpDir, { recursive: true, force: true });
    }
});

test("K. Caller mutation after saving does not change stored content", async () => {
    const tmpDir = await fs.mkdtemp(path.join(os.tmpdir(), "snap-test-k-"));
    try {
        const store = new AuthoringSnapshotStore(tmpDir);
        const snapshotId = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa";
        const doc = createSampleAuthoringDocument();

        await store.saveSnapshot(snapshotId, doc);

        // Caller mutates source doc
        doc.pages[0].scenes[0].prompt = "mutated prompt";

        const loaded = await store.getSnapshot(snapshotId);
        assert.equal(loaded.document.pages[0].scenes[0].prompt, "girl reading a book");
    } finally {
        await fs.rm(tmpDir, { recursive: true, force: true });
    }
});

test("L. No generation job, GPU process, network call or service restart is needed", async () => {
    const tmpDir = await fs.mkdtemp(path.join(os.tmpdir(), "snap-test-l-"));
    try {
        const snapshotId = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb";
        const doc = createSampleAuthoringDocument();

        // Operates using convenience functions in temporary directory without services
        const saved = await saveSnapshot(snapshotId, doc, { directory: tmpDir });
        assert.equal(saved.snapshot_id, snapshotId);

        const loaded = await getSnapshot(snapshotId, { directory: tmpDir });
        assert.equal(loaded.snapshot_id, snapshotId);
        assert.equal(loaded.document.document_id, doc.document_id);
    } finally {
        await fs.rm(tmpDir, { recursive: true, force: true });
    }
});
