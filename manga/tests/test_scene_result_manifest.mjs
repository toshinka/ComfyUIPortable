import test from "node:test";
import assert from "node:assert/strict";

import {
    SCHEMA_ID,
    SCHEMA_VERSION,
    SceneResultManifestError,
    validateSceneResultManifest,
} from "../service/scene_result_manifest.mjs";

function createValidManifest() {
    return {
        schema_id: SCHEMA_ID,
        schema_version: SCHEMA_VERSION,
        manifest_id: "c8e0cf3a-446f-42e5-8da8-654cb6c72e42", // valid UUIDv4
        owner: {
            document_id: "97f0fb52-ebcc-47d2-9721-a3fcf442d8f9",
            page_id: "page-1",
            scene_id: "scene-1",
        },
        input_provenance: {
            authoring_snapshot_ref: "snapshots/doc-97f0fb52/v1.json",
            authoring_snapshot_digest: "a".repeat(64),
            effective_input_digest: "b".repeat(64),
            effective_input_contract_version: "2.0.0",
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
    };
}

test("A: Complete valid finalized manifest is accepted", () => {
    const raw = createValidManifest();
    const result = validateSceneResultManifest(raw);
    assert.equal(result.schema_id, SCHEMA_ID);
    assert.equal(result.schema_version, "1.1.0");
    assert.equal(result.manifest_id, "c8e0cf3a-446f-42e5-8da8-654cb6c72e42");
    assert.equal(result.owner.document_id, "97f0fb52-ebcc-47d2-9721-a3fcf442d8f9");
    assert.equal(result.execution.state, "SUCCEEDED");
    assert.equal(result.input_provenance.effective_input_contract_version, "2.0.0");
});

test("B: Missing owner ID (document_id, page_id, scene_id) is rejected", () => {
    const rawNoDoc = createValidManifest();
    delete rawNoDoc.owner.document_id;
    assert.throws(
        () => validateSceneResultManifest(rawNoDoc),
        (err) => err instanceof SceneResultManifestError && err.code === "INVALID_OWNER"
    );

    const rawEmptyDoc = createValidManifest();
    rawEmptyDoc.owner.document_id = "   ";
    assert.throws(
        () => validateSceneResultManifest(rawEmptyDoc),
        (err) => err instanceof SceneResultManifestError && err.code === "INVALID_OWNER"
    );

    const rawNoPage = createValidManifest();
    delete rawNoPage.owner.page_id;
    assert.throws(
        () => validateSceneResultManifest(rawNoPage),
        (err) => err instanceof SceneResultManifestError && err.code === "INVALID_OWNER"
    );

    const rawNoScene = createValidManifest();
    delete rawNoScene.owner.scene_id;
    assert.throws(
        () => validateSceneResultManifest(rawNoScene),
        (err) => err instanceof SceneResultManifestError && err.code === "INVALID_OWNER"
    );
});

test("C: Legacy nonempty doc_-prefixed document_id is accepted", () => {
    const raw = createValidManifest();
    raw.owner.document_id = "doc_legacy_12345";
    const result = validateSceneResultManifest(raw);
    assert.equal(result.owner.document_id, "doc_legacy_12345");
});

test("D: Invalid UUIDv4 manifest_id (wrong version, wrong variant, bad format) is rejected", () => {
    const rawBadFormat = createValidManifest();
    rawBadFormat.manifest_id = "not-a-uuid";
    assert.throws(
        () => validateSceneResultManifest(rawBadFormat),
        (err) => err instanceof SceneResultManifestError && err.code === "INVALID_MANIFEST_ID"
    );

    // Version 1 instead of 4 (13th char is '1')
    const rawWrongVersion = createValidManifest();
    rawWrongVersion.manifest_id = "c8e0cf3a-446f-12e5-8da8-654cb6c72e42";
    assert.throws(
        () => validateSceneResultManifest(rawWrongVersion),
        (err) => err instanceof SceneResultManifestError && err.code === "INVALID_MANIFEST_ID"
    );

    // Variant not [89ab] (17th char is 'c')
    const rawWrongVariant = createValidManifest();
    rawWrongVariant.manifest_id = "c8e0cf3a-446f-42e5-cda8-654cb6c72e42";
    assert.throws(
        () => validateSceneResultManifest(rawWrongVariant),
        (err) => err instanceof SceneResultManifestError && err.code === "INVALID_MANIFEST_ID"
    );
});

test("E: Missing durable snapshot reference or digest is rejected", () => {
    const rawNoRef = createValidManifest();
    delete rawNoRef.input_provenance.authoring_snapshot_ref;
    assert.throws(
        () => validateSceneResultManifest(rawNoRef),
        (err) => err instanceof SceneResultManifestError && err.code === "INVALID_INPUT_PROVENANCE"
    );

    const rawNoDigest = createValidManifest();
    delete rawNoDigest.input_provenance.authoring_snapshot_digest;
    assert.throws(
        () => validateSceneResultManifest(rawNoDigest),
        (err) => err instanceof SceneResultManifestError && err.code === "INVALID_INPUT_PROVENANCE"
    );

    const rawBadDigest = createValidManifest();
    rawBadDigest.input_provenance.authoring_snapshot_digest = "short_digest";
    assert.throws(
        () => validateSceneResultManifest(rawBadDigest),
        (err) => err instanceof SceneResultManifestError && err.code === "INVALID_INPUT_PROVENANCE"
    );
});

test("F: Missing effective-input provenance is rejected", () => {
    const rawNoEffDigest = createValidManifest();
    delete rawNoEffDigest.input_provenance.effective_input_digest;
    assert.throws(
        () => validateSceneResultManifest(rawNoEffDigest),
        (err) => err instanceof SceneResultManifestError && err.code === "INVALID_INPUT_PROVENANCE"
    );

    const rawBadEffDigest = createValidManifest();
    rawBadEffDigest.input_provenance.effective_input_digest = "not-64-hex";
    assert.throws(
        () => validateSceneResultManifest(rawBadEffDigest),
        (err) => err instanceof SceneResultManifestError && err.code === "INVALID_INPUT_PROVENANCE"
    );
});

test("G: Active reference with missing reference CONTENT digest is rejected", () => {
    const raw = createValidManifest();
    raw.input_provenance.reference_content_digest = "not-hex";
    assert.throws(
        () => validateSceneResultManifest(raw),
        (err) => err instanceof SceneResultManifestError && err.code === "INVALID_INPUT_PROVENANCE"
    );
});

test("H: No-active-Reference state (reference_content_digest: null) is accepted", () => {
    const raw = createValidManifest();
    raw.input_provenance.reference_content_digest = null;
    const result = validateSceneResultManifest(raw);
    assert.equal(result.input_provenance.reference_content_digest, null);
});

test("I: Missing output PNG content digest is rejected", () => {
    const rawNoContentDigest = createValidManifest();
    delete rawNoContentDigest.artifact.content_digest;
    assert.throws(
        () => validateSceneResultManifest(rawNoContentDigest),
        (err) => err instanceof SceneResultManifestError && err.code === "INVALID_ARTIFACT"
    );

    const rawBadContentDigest = createValidManifest();
    rawBadContentDigest.artifact.content_digest = "bad-hash";
    assert.throws(
        () => validateSceneResultManifest(rawBadContentDigest),
        (err) => err instanceof SceneResultManifestError && err.code === "INVALID_ARTIFACT"
    );
});

test("J: Pending or failed execution state is rejected", () => {
    for (const invalidState of ["PENDING", "RUNNING", "FAILED", "QUEUED", "SUBMITTING"]) {
        const raw = createValidManifest();
        raw.execution.state = invalidState;
        assert.throws(
            () => validateSceneResultManifest(raw),
            (err) => err instanceof SceneResultManifestError && err.code === "INVALID_EXECUTION_STATE"
        );
    }
});

test("K: Missing or inconsistent placement mapping is rejected", () => {
    const rawMissingPlacement = createValidManifest();
    delete rawMissingPlacement.placement;
    assert.throws(
        () => validateSceneResultManifest(rawMissingPlacement),
        (err) => err instanceof SceneResultManifestError && err.code === "INVALID_PLACEMENT"
    );

    // Inconsistent scale_x vs page_target_rect.w
    const rawInconsistent = createValidManifest();
    rawInconsistent.placement.transform.scale_x = 0.5; // page_target_rect.w is 0.8
    assert.throws(
        () => validateSceneResultManifest(rawInconsistent),
        (err) => err instanceof SceneResultManifestError && err.code === "INCONSISTENT_PLACEMENT"
    );

    // Exceeds [0, 1] bounds
    const rawOutOfBounds = createValidManifest();
    rawOutOfBounds.placement.page_target_rect = { x: 0.9, y: 0.9, w: 0.5, h: 0.5 };
    rawOutOfBounds.placement.transform = { scale_x: 0.5, scale_y: 0.5, offset_x: 0.9, offset_y: 0.9 };
    assert.throws(
        () => validateSceneResultManifest(rawOutOfBounds),
        (err) => err instanceof SceneResultManifestError && err.code === "INVALID_PLACEMENT"
    );
});

test("L: Non-finite or invalid dimensions are rejected", () => {
    // Artifact width not multiple of 8
    const rawNonDiv8 = createValidManifest();
    rawNonDiv8.artifact.dimensions.width = 1023;
    assert.throws(
        () => validateSceneResultManifest(rawNonDiv8),
        (err) => err instanceof SceneResultManifestError && err.code === "INVALID_ARTIFACT_DIMENSIONS"
    );

    // Negative dimensions
    const rawNegDim = createValidManifest();
    rawNegDim.artifact.dimensions.height = -768;
    assert.throws(
        () => validateSceneResultManifest(rawNegDim),
        (err) => err instanceof SceneResultManifestError && err.code === "INVALID_ARTIFACT_DIMENSIONS"
    );

    // Non-finite page dimensions
    const rawBadPageDim = createValidManifest();
    rawBadPageDim.placement.target_page_dimensions.width = NaN;
    assert.throws(
        () => validateSceneResultManifest(rawBadPageDim),
        (err) => err instanceof SceneResultManifestError && err.code === "INVALID_PLACEMENT"
    );
});

test("M: Invalid source object does not mutate caller object", () => {
    const raw = createValidManifest();
    raw.execution.state = "FAILED";
    const snapshot = JSON.stringify(raw);
    assert.throws(() => validateSceneResultManifest(raw));
    assert.equal(JSON.stringify(raw), snapshot);
});

test("N: Validated result does not change when caller later mutates source object", () => {
    const raw = createValidManifest();
    const validated = validateSceneResultManifest(raw);
    raw.owner.scene_id = "mutated-scene";
    raw.execution.effective_settings.steps = 999;
    raw.placement.transform.scale_x = 0.001;

    assert.equal(validated.owner.scene_id, "scene-1");
    assert.equal(validated.execution.effective_settings.steps, 28);
    assert.equal(validated.placement.transform.scale_x, 0.8);
});

test("O: Missing digest contract version in v1.1.0 is rejected", () => {
    // Completely missing
    const rawNoVer = createValidManifest();
    delete rawNoVer.input_provenance.effective_input_contract_version;
    assert.throws(
        () => validateSceneResultManifest(rawNoVer),
        (err) => err instanceof SceneResultManifestError && err.code === "INVALID_INPUT_PROVENANCE"
    );

    // Null version
    const rawNullVer = createValidManifest();
    rawNullVer.input_provenance.effective_input_contract_version = null;
    assert.throws(
        () => validateSceneResultManifest(rawNullVer),
        (err) => err instanceof SceneResultManifestError && err.code === "INVALID_INPUT_PROVENANCE"
    );

    // Empty version
    const rawEmptyVer = createValidManifest();
    rawEmptyVer.input_provenance.effective_input_contract_version = "   ";
    assert.throws(
        () => validateSceneResultManifest(rawEmptyVer),
        (err) => err instanceof SceneResultManifestError && err.code === "INVALID_INPUT_PROVENANCE"
    );
});

test("P: Invalid or unsupported digest contract version in v1.1.0 is rejected", () => {
    for (const badVer of ["1.0.0", "3.0.0", "2.0.1", 123, true, {}]) {
        const raw = createValidManifest();
        raw.input_provenance.effective_input_contract_version = badVer;
        assert.throws(
            () => validateSceneResultManifest(raw),
            (err) => err instanceof SceneResultManifestError && err.code === "INVALID_INPUT_PROVENANCE"
        );
    }
});

test("Q: Existing v1.0.0 manifest validation behavior is preserved", () => {
    const raw100 = createValidManifest();
    raw100.schema_version = "1.0.0";
    delete raw100.input_provenance.effective_input_contract_version;

    const result = validateSceneResultManifest(raw100);
    assert.equal(result.schema_version, "1.0.0");
    assert.equal(result.manifest_id, "c8e0cf3a-446f-42e5-8da8-654cb6c72e42");
    assert.equal(result.execution.state, "SUCCEEDED");
});

test("R: No missing legacy provenance is silently fabricated for v1.0.0", () => {
    const raw100 = createValidManifest();
    raw100.schema_version = "1.0.0";
    delete raw100.input_provenance.effective_input_contract_version;

    const result = validateSceneResultManifest(raw100);
    assert.strictEqual(result.input_provenance.effective_input_contract_version, undefined);
    assert.strictEqual("effective_input_contract_version" in result.input_provenance, false);
});

test("S: Unsupported schema_version is rejected (SCHEMA_VERSION_MISMATCH)", () => {
    for (const badSchemaVer of ["0.9.0", "1.2.0", "2.0.0", "invalid"]) {
        const raw = createValidManifest();
        raw.schema_version = badSchemaVer;
        assert.throws(
            () => validateSceneResultManifest(raw),
            (err) => err instanceof SceneResultManifestError && err.code === "SCHEMA_VERSION_MISMATCH"
        );
    }
});
