import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs/promises";
import path from "node:path";
import os from "node:os";

import {
    SceneResultStore,
    SceneResultStoreError,
    saveCompletedManifest,
    getManifest,
} from "../service/scene_result_store.mjs";

function createValidManifest(overrides = {}) {
    return {
        schema_id: "TEGAKI_SCENE_RESULT_MANIFEST",
        schema_version: "1.0.0",
        manifest_id: "c8e0cf3a-446f-42e5-8da8-654cb6c72e42",
        owner: {
            document_id: "97f0fb52-ebcc-47d2-9721-a3fcf442d8f9",
            page_id: "page-1",
            scene_id: "scene-1",
        },
        input_provenance: {
            authoring_snapshot_ref: "snapshots/doc-97f0fb52/v1.json",
            authoring_snapshot_digest: "a".repeat(64),
            effective_input_digest: "b".repeat(64),
            reference_content_digest: "c".repeat(64),
        },
        execution: {
            job_id: "d9e0cf3a-446f-42e5-8da8-654cb6c72e43",
            prompt_id: "e9e0cf3a-446f-42e5-8da8-654cb6c72e44",
            state: "SUCCEEDED",
            graph_digest: "d".repeat(64),
            page_compile_plan_digest: "e".repeat(64),
            effective_settings: {
                checkpoint_id: "animagine-xl-3.1",
                sampler_id: "euler_a",
                scheduler_id: "normal",
                steps: 28,
                cfg: 7.0,
                seed_requested: "42",
                effective_seed: 42,
            },
        },
        artifact: {
            locator: {
                filename: "d9e0cf3a-446f-42e5-8da8-654cb6c72e43_00001_.png",
                subfolder: "Manga/Playable",
                type: "output",
            },
            dimensions: {
                width: 1024,
                height: 768,
            },
            content_digest: "f".repeat(64),
        },
        placement: {
            page_target_rect: { x: 0.1, y: 0.2, w: 0.8, h: 0.6 },
            local_source_rect: { x: 0.0, y: 0.0, w: 1.0, h: 1.0 },
            transform: { scale_x: 0.8, scale_y: 0.6, offset_x: 0.1, offset_y: 0.2 },
            target_page_dimensions: { width: 1200, height: 1800 },
        },
        created_at: "2026-09-25T03:00:00.000Z",
        ...overrides,
    };
}

test("A. Save and reload one complete, structurally valid manifest", async () => {
    const tmpDir = await fs.mkdtemp(path.join(os.tmpdir(), "store-test-a-"));
    try {
        const store = new SceneResultStore(tmpDir);
        const manifest = createValidManifest();

        const saved = await store.saveCompletedManifest(manifest);
        assert.equal(saved.manifest_id, manifest.manifest_id);

        const loaded = await store.getManifest(manifest.manifest_id);
        assert.deepEqual(loaded, manifest);
    } finally {
        await fs.rm(tmpDir, { recursive: true, force: true });
    }
});

test("B. A second manifest can be saved without modifying the first", async () => {
    const tmpDir = await fs.mkdtemp(path.join(os.tmpdir(), "store-test-b-"));
    try {
        const store = new SceneResultStore(tmpDir);
        const manifest1 = createValidManifest({
            manifest_id: "11111111-1111-4111-8111-111111111111",
        });
        const manifest2 = createValidManifest({
            manifest_id: "22222222-2222-4222-8222-222222222222",
            owner: {
                document_id: "97f0fb52-ebcc-47d2-9721-a3fcf442d8f9",
                page_id: "page-1",
                scene_id: "scene-2",
            },
        });

        await store.saveCompletedManifest(manifest1);
        await store.saveCompletedManifest(manifest2);

        const loaded1 = await store.getManifest(manifest1.manifest_id);
        const loaded2 = await store.getManifest(manifest2.manifest_id);

        assert.equal(loaded1.owner.scene_id, "scene-1");
        assert.equal(loaded2.owner.scene_id, "scene-2");
    } finally {
        await fs.rm(tmpDir, { recursive: true, force: true });
    }
});

test("C. Saving an existing manifest_id cannot overwrite its record", async () => {
    const tmpDir = await fs.mkdtemp(path.join(os.tmpdir(), "store-test-c-"));
    try {
        const store = new SceneResultStore(tmpDir);
        const manifestOriginal = createValidManifest({
            manifest_id: "33333333-3333-4333-8333-333333333333",
        });
        await store.saveCompletedManifest(manifestOriginal);

        const manifestDuplicate = createValidManifest({
            manifest_id: "33333333-3333-4333-8333-333333333333",
            owner: {
                document_id: "97f0fb52-ebcc-47d2-9721-a3fcf442d8f9",
                page_id: "page-1",
                scene_id: "scene-modified",
            },
        });

        await assert.rejects(
            async () => await store.saveCompletedManifest(manifestDuplicate),
            (err) => err instanceof SceneResultStoreError && err.code === "MANIFEST_EXISTS"
        );

        // Verify the original record remains unmodified
        const loaded = await store.getManifest("33333333-3333-4333-8333-333333333333");
        assert.equal(loaded.owner.scene_id, "scene-1");
    } finally {
        await fs.rm(tmpDir, { recursive: true, force: true });
    }
});

test("D. Concurrent writes with the same manifest_id cannot both publish different records", async () => {
    const tmpDir = await fs.mkdtemp(path.join(os.tmpdir(), "store-test-d-"));
    try {
        const store = new SceneResultStore(tmpDir);
        const sharedId = "44444444-4444-4444-8444-444444444444";
        const manifestA = createValidManifest({
            manifest_id: sharedId,
            owner: {
                document_id: "doc-A",
                page_id: "p1",
                scene_id: "scene-A",
            },
        });
        const manifestB = createValidManifest({
            manifest_id: sharedId,
            owner: {
                document_id: "doc-B",
                page_id: "p1",
                scene_id: "scene-B",
            },
        });

        const results = await Promise.allSettled([
            store.saveCompletedManifest(manifestA),
            store.saveCompletedManifest(manifestB),
        ]);

        const fulfilled = results.filter((r) => r.status === "fulfilled");
        const rejected = results.filter((r) => r.status === "rejected");

        assert.equal(fulfilled.length, 1, "Exactly one concurrent writer must succeed");
        assert.equal(rejected.length, 1, "The competing concurrent writer must fail");
        assert.equal(rejected[0].reason.code, "MANIFEST_EXISTS");

        // Stored content must strictly match the fulfilled writer
        const loaded = await store.getManifest(sharedId);
        assert.equal(loaded.owner.scene_id, fulfilled[0].value.owner.scene_id);
    } finally {
        await fs.rm(tmpDir, { recursive: true, force: true });
    }
});

test("E. Missing or invalid provenance is rejected before publication", async () => {
    const tmpDir = await fs.mkdtemp(path.join(os.tmpdir(), "store-test-e-"));
    try {
        const store = new SceneResultStore(tmpDir);
        const invalidManifest = createValidManifest({
            input_provenance: {
                authoring_snapshot_ref: "snap.json",
                authoring_snapshot_digest: "invalid-short-hash",
                effective_input_digest: "b".repeat(64),
                reference_content_digest: null,
            },
        });

        await assert.rejects(
            async () => await store.saveCompletedManifest(invalidManifest),
            (err) => err instanceof SceneResultStoreError && err.code === "INVALID_MANIFEST"
        );

        // Ensure no file was created in the store directory
        const files = await fs.readdir(tmpDir).catch(() => []);
        assert.equal(files.length, 0);
    } finally {
        await fs.rm(tmpDir, { recursive: true, force: true });
    }
});

test("F. Invalid or path-like manifest_id is rejected before path access", async () => {
    const tmpDir = await fs.mkdtemp(path.join(os.tmpdir(), "store-test-f-"));
    try {
        const store = new SceneResultStore(tmpDir);

        for (const badId of [
            "../../etc/passwd",
            "not-a-uuid",
            "c8e0cf3a-446f-12e5-8da8-654cb6c72e42", // UUIDv1 (not v4)
            "",
            12345,
            null,
        ]) {
            await assert.rejects(
                async () => await store.getManifest(badId),
                (err) => err instanceof SceneResultStoreError && err.code === "INVALID_MANIFEST_ID"
            );
        }
    } finally {
        await fs.rm(tmpDir, { recursive: true, force: true });
    }
});

test("G. Missing record returns an explicit not-found result/error", async () => {
    const tmpDir = await fs.mkdtemp(path.join(os.tmpdir(), "store-test-g-"));
    try {
        const store = new SceneResultStore(tmpDir);
        const nonExistentId = "55555555-5555-4555-8555-555555555555";

        // Default: returns null as explicit not-found result
        const result = await store.getManifest(nonExistentId);
        assert.equal(result, null);

        // Optional { required: true }: throws MANIFEST_NOT_FOUND error
        await assert.rejects(
            async () => await store.getManifest(nonExistentId, { required: true }),
            (err) => err instanceof SceneResultStoreError && err.code === "MANIFEST_NOT_FOUND"
        );
    } finally {
        await fs.rm(tmpDir, { recursive: true, force: true });
    }
});

test("H. Malformed stored JSON or an invalid stored record is rejected", async () => {
    const tmpDir = await fs.mkdtemp(path.join(os.tmpdir(), "store-test-h-"));
    try {
        await fs.mkdir(tmpDir, { recursive: true });
        const store = new SceneResultStore(tmpDir);

        // 1. Corrupt JSON
        const corruptId = "66666666-6666-4666-8666-666666666666";
        await fs.writeFile(path.join(tmpDir, `${corruptId}.json`), "{ unparseable json");
        await assert.rejects(
            async () => await store.getManifest(corruptId),
            (err) => err instanceof SceneResultStoreError && err.code === "STORE_CORRUPT"
        );

        // 2. Structurally invalid manifest record
        const invalidRecordId = "77777777-7777-4777-8777-777777777777";
        await fs.writeFile(
            path.join(tmpDir, `${invalidRecordId}.json`),
            JSON.stringify({ schema_id: "WRONG_SCHEMA" })
        );
        await assert.rejects(
            async () => await store.getManifest(invalidRecordId),
            (err) => err instanceof SceneResultStoreError && err.code === "STORE_CORRUPT"
        );
    } finally {
        await fs.rm(tmpDir, { recursive: true, force: true });
    }
});

test("I. Caller mutation after saving does not change the saved record", async () => {
    const tmpDir = await fs.mkdtemp(path.join(os.tmpdir(), "store-test-i-"));
    try {
        const store = new SceneResultStore(tmpDir);
        const manifest = createValidManifest({
            manifest_id: "88888888-8888-4888-8888-888888888888",
        });

        await store.saveCompletedManifest(manifest);

        // Caller mutates source object
        manifest.owner.scene_id = "mutated-scene";
        manifest.execution.effective_settings.steps = 999;
        manifest.placement.transform.scale_x = 0.001;

        const reloaded = await store.getManifest(manifest.manifest_id);
        assert.equal(reloaded.owner.scene_id, "scene-1");
        assert.equal(reloaded.execution.effective_settings.steps, 28);
        assert.equal(reloaded.placement.transform.scale_x, 0.8);
    } finally {
        await fs.rm(tmpDir, { recursive: true, force: true });
    }
});

test("J. Reading does not mutate the stored JSON or prior results", async () => {
    const tmpDir = await fs.mkdtemp(path.join(os.tmpdir(), "store-test-j-"));
    try {
        const store = new SceneResultStore(tmpDir);
        const manifest = createValidManifest({
            manifest_id: "99999999-9999-4999-8999-999999999999",
        });
        await store.saveCompletedManifest(manifest);

        const read1 = await store.getManifest(manifest.manifest_id);
        read1.owner.scene_id = "mutated-read1";

        const read2 = await store.getManifest(manifest.manifest_id);
        assert.equal(read2.owner.scene_id, "scene-1");
    } finally {
        await fs.rm(tmpDir, { recursive: true, force: true });
    }
});

test("K. Legacy nonempty document_id remains valid as structured payload data, without becoming part of the physical path", async () => {
    const tmpDir = await fs.mkdtemp(path.join(os.tmpdir(), "store-test-k-"));
    try {
        const store = new SceneResultStore(tmpDir);
        const manifest = createValidManifest({
            manifest_id: "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
            owner: {
                document_id: "doc_legacy_custom_identity_12345",
                page_id: "page-1",
                scene_id: "scene-1",
            },
        });

        await store.saveCompletedManifest(manifest);

        // Check physical directory contains only <manifest_id>.json
        const files = await fs.readdir(tmpDir);
        assert.deepEqual(files, ["aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa.json"]);

        const loaded = await store.getManifest("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa");
        assert.equal(loaded.owner.document_id, "doc_legacy_custom_identity_12345");
    } finally {
        await fs.rm(tmpDir, { recursive: true, force: true });
    }
});

test("L. No generation job, service, network request or GPU process is required by the store", async () => {
    const tmpDir = await fs.mkdtemp(path.join(os.tmpdir(), "store-test-l-"));
    try {
        // Standalone convenience functions work with just an options directory
        const manifest = createValidManifest({
            manifest_id: "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb",
        });

        const saved = await saveCompletedManifest(manifest, { directory: tmpDir });
        assert.equal(saved.manifest_id, manifest.manifest_id);

        const loaded = await getManifest(manifest.manifest_id, { directory: tmpDir });
        assert.equal(loaded.manifest_id, manifest.manifest_id);
    } finally {
        await fs.rm(tmpDir, { recursive: true, force: true });
    }
});

function createValidManifestV11(overrides = {}) {
    return {
        schema_id: "TEGAKI_SCENE_RESULT_MANIFEST",
        schema_version: "1.1.0",
        manifest_id: "d8e0cf3a-446f-42e5-8da8-654cb6c72e43",
        owner: {
            document_id: "97f0fb52-ebcc-47d2-9721-a3fcf442d8f9",
            page_id: "page-1",
            scene_id: "scene-1",
            ...overrides.owner,
        },
        input_provenance: {
            authoring_snapshot_ref: "snapshots/doc-97f0fb52/v1.json",
            authoring_snapshot_digest: "a".repeat(64),
            effective_input_digest: "b".repeat(64),
            effective_input_contract_version: "2.0.0",
            reference_content_digest: "c".repeat(64),
            ...overrides.input_provenance,
        },
        execution: {
            job_id: "d9e0cf3a-446f-42e5-8da8-654cb6c72e43",
            prompt_id: "e9e0cf3a-446f-42e5-8da8-654cb6c72e44",
            state: "SUCCEEDED",
            graph_digest: "d".repeat(64),
            page_compile_plan_digest: "e".repeat(64),
            effective_settings: {
                checkpoint_id: "animagine-xl-3.1",
                sampler_id: "euler_a",
                scheduler_id: "normal",
                steps: 28,
                cfg: 7.0,
                seed_requested: "42",
                effective_seed: 42,
            },
            ...overrides.execution,
        },
        artifact: {
            locator: {
                filename: "d9e0cf3a-446f-42e5-8da8-654cb6c72e43_00001_.png",
                subfolder: "Manga/Playable",
                type: "output",
            },
            dimensions: {
                width: 1024,
                height: 768,
            },
            content_digest: "f".repeat(64),
            ...overrides.artifact,
        },
        placement: {
            page_target_rect: { x: 0.1, y: 0.2, w: 0.8, h: 0.6 },
            local_source_rect: { x: 0.0, y: 0.0, w: 1.0, h: 1.0 },
            transform: { scale_x: 0.8, scale_y: 0.6, offset_x: 0.1, offset_y: 0.2 },
            target_page_dimensions: { width: 1200, height: 1800 },
            ...overrides.placement,
        },
        created_at: "2026-09-25T03:00:00.000Z",
        ...overrides,
    };
}

test("M. Save and reload one complete, structurally valid v1.1.0 manifest with contract version 2.0.0", async () => {
    const tmpDir = await fs.mkdtemp(path.join(os.tmpdir(), "store-test-m-"));
    try {
        const store = new SceneResultStore(tmpDir);
        const manifest = createValidManifestV11();

        const saved = await store.saveCompletedManifest(manifest);
        assert.equal(saved.manifest_id, manifest.manifest_id);

        const loaded = await store.getManifest(manifest.manifest_id);
        assert.deepEqual(loaded, manifest);

        // Explicitly verify preservation of all critical fields
        assert.equal(loaded.schema_id, "TEGAKI_SCENE_RESULT_MANIFEST");
        assert.equal(loaded.schema_version, "1.1.0");
        assert.equal(loaded.manifest_id, manifest.manifest_id);
        assert.deepEqual(loaded.owner, manifest.owner);
        assert.equal(loaded.input_provenance.authoring_snapshot_ref, manifest.input_provenance.authoring_snapshot_ref);
        assert.equal(loaded.input_provenance.authoring_snapshot_digest, manifest.input_provenance.authoring_snapshot_digest);
        assert.equal(loaded.input_provenance.effective_input_digest, manifest.input_provenance.effective_input_digest);
        assert.equal(loaded.input_provenance.effective_input_contract_version, "2.0.0");
        assert.equal(loaded.input_provenance.reference_content_digest, manifest.input_provenance.reference_content_digest);
        assert.deepEqual(loaded.execution, manifest.execution);
        assert.deepEqual(loaded.artifact, manifest.artifact);
        assert.deepEqual(loaded.placement, manifest.placement);
        assert.equal(loaded.created_at, manifest.created_at);
    } finally {
        await fs.rm(tmpDir, { recursive: true, force: true });
    }
});

test("N. Saving a v1.1.0 manifest with missing or unsupported digest contract version is rejected", async () => {
    const tmpDir = await fs.mkdtemp(path.join(os.tmpdir(), "store-test-n-"));
    try {
        const store = new SceneResultStore(tmpDir);

        // Missing contract version
        const manifestNoVer = createValidManifestV11();
        delete manifestNoVer.input_provenance.effective_input_contract_version;
        await assert.rejects(
            async () => await store.saveCompletedManifest(manifestNoVer),
            (err) => err instanceof SceneResultStoreError && err.code === "INVALID_MANIFEST"
        );

        // Null contract version
        const manifestNullVer = createValidManifestV11();
        manifestNullVer.input_provenance.effective_input_contract_version = null;
        await assert.rejects(
            async () => await store.saveCompletedManifest(manifestNullVer),
            (err) => err instanceof SceneResultStoreError && err.code === "INVALID_MANIFEST"
        );

        // Empty contract version
        const manifestEmptyVer = createValidManifestV11();
        manifestEmptyVer.input_provenance.effective_input_contract_version = "   ";
        await assert.rejects(
            async () => await store.saveCompletedManifest(manifestEmptyVer),
            (err) => err instanceof SceneResultStoreError && err.code === "INVALID_MANIFEST"
        );

        // Unsupported contract versions
        for (const badVer of ["1.0.0", "3.0.0", "invalid", 123]) {
            const manifestBadVer = createValidManifestV11();
            manifestBadVer.input_provenance.effective_input_contract_version = badVer;
            await assert.rejects(
                async () => await store.saveCompletedManifest(manifestBadVer),
                (err) => err instanceof SceneResultStoreError && err.code === "INVALID_MANIFEST"
            );
        }

        // Store directory remains untouched
        const files = await fs.readdir(tmpDir).catch(() => []);
        assert.equal(files.length, 0);
    } finally {
        await fs.rm(tmpDir, { recursive: true, force: true });
    }
});

test("O. Stored v1.1.0 record with missing or invalid digest contract version is rejected on retrieval", async () => {
    const tmpDir = await fs.mkdtemp(path.join(os.tmpdir(), "store-test-o-"));
    try {
        await fs.mkdir(tmpDir, { recursive: true });
        const store = new SceneResultStore(tmpDir);

        // Record with missing version
        const corruptId1 = "e8e0cf3a-446f-42e5-8da8-654cb6c72e44";
        const rawNoVer = createValidManifestV11({ manifest_id: corruptId1 });
        delete rawNoVer.input_provenance.effective_input_contract_version;
        await fs.writeFile(path.join(tmpDir, `${corruptId1}.json`), JSON.stringify(rawNoVer, null, 2));

        await assert.rejects(
            async () => await store.getManifest(corruptId1),
            (err) => err instanceof SceneResultStoreError && err.code === "STORE_CORRUPT"
        );

        // Record with unsupported version
        const corruptId2 = "f8e0cf3a-446f-42e5-8da8-654cb6c72e45";
        const rawBadVer = createValidManifestV11({ manifest_id: corruptId2 });
        rawBadVer.input_provenance.effective_input_contract_version = "1.0.0";
        await fs.writeFile(path.join(tmpDir, `${corruptId2}.json`), JSON.stringify(rawBadVer, null, 2));

        await assert.rejects(
            async () => await store.getManifest(corruptId2),
            (err) => err instanceof SceneResultStoreError && err.code === "STORE_CORRUPT"
        );
    } finally {
        await fs.rm(tmpDir, { recursive: true, force: true });
    }
});

test("P. Existing v1.0.0 manifest remains readable without fabricating effective_input_contract_version", async () => {
    const tmpDir = await fs.mkdtemp(path.join(os.tmpdir(), "store-test-p-"));
    try {
        const store = new SceneResultStore(tmpDir);
        const legacyManifest = createValidManifest({
            manifest_id: "a1a1a1a1-b2b2-4c3c-8d4d-e5e5e5e5e5e5",
        });

        await store.saveCompletedManifest(legacyManifest);
        const loaded = await store.getManifest(legacyManifest.manifest_id);

        assert.equal(loaded.schema_version, "1.0.0");
        assert.equal(loaded.input_provenance.effective_input_contract_version, undefined);
        assert.equal("effective_input_contract_version" in loaded.input_provenance, false);
        assert.deepEqual(loaded, legacyManifest);
    } finally {
        await fs.rm(tmpDir, { recursive: true, force: true });
    }
});

test("Q. Duplicate manifest_id publication remains prohibited for v1.1.0 manifests", async () => {
    const tmpDir = await fs.mkdtemp(path.join(os.tmpdir(), "store-test-q-"));
    try {
        const store = new SceneResultStore(tmpDir);
        const manifest1 = createValidManifestV11({
            manifest_id: "b2b2b2b2-c3c3-4d4d-8e5e-f6f6f6f6f6f6",
        });
        await store.saveCompletedManifest(manifest1);

        const manifestDuplicate = createValidManifestV11({
            manifest_id: "b2b2b2b2-c3c3-4d4d-8e5e-f6f6f6f6f6f6",
            owner: {
                document_id: "97f0fb52-ebcc-47d2-9721-a3fcf442d8f9",
                page_id: "page-1",
                scene_id: "scene-modified",
            },
        });

        await assert.rejects(
            async () => await store.saveCompletedManifest(manifestDuplicate),
            (err) => err instanceof SceneResultStoreError && err.code === "MANIFEST_EXISTS"
        );
    } finally {
        await fs.rm(tmpDir, { recursive: true, force: true });
    }
});
