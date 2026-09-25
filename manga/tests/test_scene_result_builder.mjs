import test from "node:test";
import assert from "node:assert/strict";

import {
    buildSceneResultManifest,
    SceneResultBuilderError,
} from "../service/scene_result_builder.mjs";
import { computeSceneEffectiveInputDigest } from "../service/scene_effective_input_digest.mjs";

const VALID_MANIFEST_ID = "11111111-2222-4333-8444-555555555555";
const VALID_JOB_ID = "22222222-3333-4444-8555-666666666666";
const VALID_PROMPT_ID = "33333333-4444-4555-8666-777777777777";
const GRAPH_DIGEST = "1".repeat(64);
const PLAN_DIGEST = "2".repeat(64);
const SNAPSHOT_DIGEST = "a".repeat(64);
const REF_DIGEST = "b".repeat(64);
const PNG_DIGEST = "c".repeat(64);

function makeValidBuilderEvidence(overrides = {}) {
    return {
        manifest_id: VALID_MANIFEST_ID,
        created_at: "2026-09-25T03:40:00.000Z",
        owner: {
            document_id: "doc_tegaki_001",
            page_id: "page_01",
            scene_id: "scene_01",
            ...overrides.owner,
        },
        snapshot_ref: "snapshots/doc_tegaki_001/snapshot_01.json",
        snapshot_digest: SNAPSHOT_DIGEST,
        plan: {
            scene: {
                scene_id: "scene_01",
                name: "Panel 1",
                prompt: "1girl smiling happily in a park",
                negative_prompt: "blurry, low quality",
                input_mode: "cast",
                order: 0,
                local_area: { x: 0, y: 0, w: 512, h: 768 },
            },
            page_context: {
                page_id: "page_01",
                style_prompt: "manga, screentone, monochrome",
                style_negative_prompt: "color, photographic",
                width_px: 1200,
                height_px: 1800,
            },
            character_instances: [
                {
                    instance_id: "inst_01",
                    cast_id: "cast_01",
                    acting_prompt: "waving hand enthusiastically",
                    negative_prompt_override: null,
                    order: 0,
                    area: { x: 50, y: 50, w: 200, h: 400 },
                },
            ],
            cast: [
                {
                    cast_id: "cast_01",
                    display_name: "Heroine",
                    identity_prompt: "long blue hair, school uniform",
                    negative_prompt: "short hair",
                    reference_asset: "cast_01.png",
                },
            ],
            reference: {
                enabled: true,
                reference_asset: "cast_01.png",
            },
            local_canvas: {
                width: 512,
                height: 768,
            },
            guide_state: {
                enabled: false,
                active: false,
            },
            ...overrides.plan,
        },
        compile_metadata: {
            scene_id: "scene_01",
            page_id: "page_01",
            graph_digest: GRAPH_DIGEST,
            page_compile_plan_digest: PLAN_DIGEST,
            local_dimensions: {
                width: 512,
                height: 768,
            },
            effective_settings: {
                checkpoint_id: "illustrious_v1.safetensors",
                sampler_id: "euler_ancestral",
                scheduler_id: "karras",
                steps: 28,
                cfg: 6.5,
                seed_requested: 42,
                effective_seed: 42,
                mask_feather: 16,
                panel_strength: 1.0,
                reference_weight: 0.7,
                reference_start: 0.0,
                reference_end: 0.8,
            },
            placement_mapping: {
                page_target_rect: { x: 0.05, y: 0.044, w: 0.426, h: 0.426 },
                local_source_rect: { x: 0, y: 0, w: 512, h: 768 },
                transform: { scale_x: 0.426, scale_y: 0.426, offset_x: 0.05, offset_y: 0.044 },
                target_page_dimensions: { width: 1200, height: 1800 },
            },
            ...overrides.compile_metadata,
        },
        reference_evidence: {
            enabled: true,
            reference_asset: "cast_01.png",
            content_digest: REF_DIGEST,
            ...overrides.reference_evidence,
        },
        job: {
            job_id: VALID_JOB_ID,
            prompt_id: VALID_PROMPT_ID,
            state: "SUCCEEDED",
            graph_digest: GRAPH_DIGEST,
            page_compile_plan_digest: PLAN_DIGEST,
            effective_settings: {
                checkpoint_id: "illustrious_v1.safetensors",
                sampler_id: "euler_ancestral",
                scheduler_id: "karras",
                steps: 28,
                cfg: 6.5,
                seed_requested: 42,
                effective_seed: 42,
            },
            ...overrides.job,
        },
        locator: {
            filename: "manga_scene_01_0001.png",
            subfolder: "manga/scenes",
            type: "output",
            ...overrides.locator,
        },
        png_analysis: {
            content_digest: PNG_DIGEST,
            declared_width: 512,
            declared_height: 768,
            byte_length: 98765,
            ...overrides.png_analysis,
        },
        ...overrides.root,
    };
}

test("Case A: Complete consistent evidence produces a schema-valid manifest", () => {
    const evidence = makeValidBuilderEvidence();
    const manifest = buildSceneResultManifest(evidence);

    assert.strictEqual(manifest.schema_id, "TEGAKI_SCENE_RESULT_MANIFEST");
    assert.strictEqual(manifest.schema_version, "1.1.0");
    assert.strictEqual(manifest.manifest_id, VALID_MANIFEST_ID);

    assert.deepStrictEqual(manifest.owner, {
        document_id: "doc_tegaki_001",
        page_id: "page_01",
        scene_id: "scene_01",
    });

    assert.strictEqual(manifest.input_provenance.authoring_snapshot_ref, "snapshots/doc_tegaki_001/snapshot_01.json");
    assert.strictEqual(manifest.input_provenance.authoring_snapshot_digest, SNAPSHOT_DIGEST);
    assert.strictEqual(manifest.input_provenance.reference_content_digest, REF_DIGEST);
    assert.strictEqual(manifest.input_provenance.effective_input_contract_version, "2.0.0");
    assert.match(manifest.input_provenance.effective_input_digest, /^[0-9a-f]{64}$/);

    assert.strictEqual(manifest.execution.job_id, VALID_JOB_ID);
    assert.strictEqual(manifest.execution.prompt_id, VALID_PROMPT_ID);
    assert.strictEqual(manifest.execution.state, "SUCCEEDED");
    assert.strictEqual(manifest.execution.graph_digest, GRAPH_DIGEST);
    assert.strictEqual(manifest.execution.page_compile_plan_digest, PLAN_DIGEST);
    assert.strictEqual(manifest.execution.effective_settings.effective_seed, 42);

    assert.strictEqual(manifest.artifact.locator.filename, "manga_scene_01_0001.png");
    assert.strictEqual(manifest.artifact.dimensions.width, 512);
    assert.strictEqual(manifest.artifact.dimensions.height, 768);
    assert.strictEqual(manifest.artifact.content_digest, PNG_DIGEST);

    assert.deepStrictEqual(manifest.placement.page_target_rect, { x: 0.05, y: 0.044, w: 0.426, h: 0.426 });
    assert.strictEqual(manifest.created_at, "2026-09-25T03:40:00.000Z");
});

test("Case B: Missing original snapshot provenance fails", () => {
    // Missing snapshot_ref
    const ev1 = makeValidBuilderEvidence();
    delete ev1.snapshot_ref;
    assert.throws(() => buildSceneResultManifest(ev1), {
        name: "SceneResultBuilderError",
        code: "MISSING_SNAPSHOT_PROVENANCE",
    });

    // Missing snapshot_digest
    const ev2 = makeValidBuilderEvidence();
    delete ev2.snapshot_digest;
    assert.throws(() => buildSceneResultManifest(ev2), {
        name: "SceneResultBuilderError",
        code: "MISSING_SNAPSHOT_PROVENANCE",
    });
});

test("Case C: Scene/Page identity mismatch fails", () => {
    // Plan scene_id mismatch
    assert.throws(() => {
        buildSceneResultManifest(makeValidBuilderEvidence({
            plan: {
                scene: { scene_id: "different_scene" },
            },
        }));
    }, {
        name: "SceneResultBuilderError",
        code: "IDENTITY_MISMATCH",
    });

    // Compiler metadata scene_id mismatch
    assert.throws(() => {
        buildSceneResultManifest(makeValidBuilderEvidence({
            compile_metadata: {
                scene_id: "different_scene",
            },
        }));
    }, {
        name: "SceneResultBuilderError",
        code: "IDENTITY_MISMATCH",
    });

    // Plan page_id mismatch
    assert.throws(() => {
        buildSceneResultManifest(makeValidBuilderEvidence({
            plan: {
                page_context: { page_id: "different_page" },
            },
        }));
    }, {
        name: "SceneResultBuilderError",
        code: "IDENTITY_MISMATCH",
    });
});

test("Case D: Compile/job digest mismatch fails", () => {
    // Graph digest mismatch
    assert.throws(() => {
        buildSceneResultManifest(makeValidBuilderEvidence({
            job: { graph_digest: "9".repeat(64) },
        }));
    }, {
        name: "SceneResultBuilderError",
        code: "DIGEST_MISMATCH",
    });

    // Page compile plan digest mismatch
    assert.throws(() => {
        buildSceneResultManifest(makeValidBuilderEvidence({
            job: { page_compile_plan_digest: "8".repeat(64) },
        }));
    }, {
        name: "SceneResultBuilderError",
        code: "DIGEST_MISMATCH",
    });
});

test("Case E: Effective seed/settings mismatch fails", () => {
    // Seed mismatch
    assert.throws(() => {
        buildSceneResultManifest(makeValidBuilderEvidence({
            job: {
                effective_settings: {
                    checkpoint_id: "illustrious_v1.safetensors",
                    sampler_id: "euler_ancestral",
                    scheduler_id: "karras",
                    steps: 28,
                    cfg: 6.5,
                    seed_requested: 42,
                    effective_seed: 99999, // Mismatch!
                },
            },
        }));
    }, {
        name: "SceneResultBuilderError",
        code: "SETTINGS_MISMATCH",
    });

    // Checkpoint mismatch
    assert.throws(() => {
        buildSceneResultManifest(makeValidBuilderEvidence({
            job: {
                effective_settings: {
                    checkpoint_id: "different_model.safetensors",
                    sampler_id: "euler_ancestral",
                    scheduler_id: "karras",
                    steps: 28,
                    cfg: 6.5,
                    seed_requested: 42,
                    effective_seed: 42,
                },
            },
        }));
    }, {
        name: "SceneResultBuilderError",
        code: "SETTINGS_MISMATCH",
    });
});

test("Case F: Missing active Reference content digest fails", () => {
    assert.throws(() => {
        buildSceneResultManifest(makeValidBuilderEvidence({
            reference_evidence: {
                enabled: true,
                reference_asset: "cast_01.png",
                content_digest: null, // Active with missing digest!
            },
        }));
    }, {
        name: "SceneResultBuilderError",
        code: "REFERENCE_PROVENANCE_ERROR",
    });
});

test("Case G: Explicit disabled Reference succeeds", () => {
    const ev = makeValidBuilderEvidence({
        plan: {
            reference: { enabled: false, reference_asset: null },
        },
        reference_evidence: {
            enabled: false,
            reference_asset: null,
            content_digest: null,
        },
    });

    const manifest = buildSceneResultManifest(ev);
    assert.strictEqual(manifest.input_provenance.reference_content_digest, null);
});

test("Case H: Inconsistent Reference asset identity fails", () => {
    assert.throws(() => {
        buildSceneResultManifest(makeValidBuilderEvidence({
            reference_evidence: {
                enabled: true,
                reference_asset: "other_character.png", // Disagrees with plan's cast_01.png
                content_digest: REF_DIGEST,
            },
        }));
    }, {
        name: "SceneResultBuilderError",
        code: "REFERENCE_PROVENANCE_ERROR",
    });
});

test("Case I: Failed or pending job fails", () => {
    assert.throws(() => {
        buildSceneResultManifest(makeValidBuilderEvidence({
            job: { state: "PENDING" },
        }));
    }, {
        name: "SceneResultBuilderError",
        code: "JOB_NOT_SUCCEEDED",
    });

    assert.throws(() => {
        buildSceneResultManifest(makeValidBuilderEvidence({
            job: { state: "FAILED" },
        }));
    }, {
        name: "SceneResultBuilderError",
        code: "JOB_NOT_SUCCEEDED",
    });
});

test("Case J: PNG dimension mismatch fails", () => {
    assert.throws(() => {
        buildSceneResultManifest(makeValidBuilderEvidence({
            png_analysis: {
                content_digest: PNG_DIGEST,
                declared_width: 768, // Mismatch with compiler 512
                declared_height: 768,
            },
        }));
    }, {
        name: "SceneResultBuilderError",
        code: "ARTIFACT_PROVENANCE_ERROR",
    });
});

test("Case K: Missing PNG content digest fails", () => {
    assert.throws(() => {
        buildSceneResultManifest(makeValidBuilderEvidence({
            png_analysis: {
                content_digest: "",
                declared_width: 512,
                declared_height: 768,
            },
        }));
    }, {
        name: "SceneResultBuilderError",
        code: "ARTIFACT_PROVENANCE_ERROR",
    });
});

test("Case L: Original Page placement survives", () => {
    const ev = makeValidBuilderEvidence({
        compile_metadata: {
            placement_mapping: {
                page_target_rect: { x: 0.1, y: 0.2, w: 0.5, h: 0.6 },
                local_source_rect: { x: 0, y: 0, w: 512, h: 768 },
                transform: { scale_x: 0.5, scale_y: 0.6, offset_x: 0.1, offset_y: 0.2 },
                target_page_dimensions: { width: 1200, height: 1800 },
            },
        },
    });

    const manifest = buildSceneResultManifest(ev);

    assert.deepStrictEqual(manifest.placement.page_target_rect, { x: 0.1, y: 0.2, w: 0.5, h: 0.6 });
    assert.deepStrictEqual(manifest.placement.local_source_rect, { x: 0, y: 0, w: 512, h: 768 });
    assert.deepStrictEqual(manifest.placement.transform, { scale_x: 0.5, scale_y: 0.6, offset_x: 0.1, offset_y: 0.2 });
    assert.deepStrictEqual(manifest.placement.target_page_dimensions, { width: 1200, height: 1800 });
});

test("Case M: The effective-input digest is computed using the existing digest function", () => {
    const ev = makeValidBuilderEvidence();
    const manifest = buildSceneResultManifest(ev);

    const expectedDigestResult = computeSceneEffectiveInputDigest({
        scene: ev.plan.scene,
        page_context: ev.plan.page_context,
        character_instances: ev.plan.character_instances,
        cast: ev.plan.cast,
        reference: {
            enabled: true,
            reference_asset: "cast_01.png",
            content_digest: REF_DIGEST,
        },
        effective_settings: {
            checkpoint_id: "illustrious_v1.safetensors",
            sampler_id: "euler_ancestral",
            scheduler_id: "karras",
            steps: 28,
            cfg: 6.5,
            effective_seed: 42,
            mask_feather: 16,
            panel_strength: 1.0,
            reference_weight: 0.7,
            reference_start: 0.0,
            reference_end: 0.8,
        },
        local_dimensions: { width: 512, height: 768 },
        placement: {
            page_dimensions: { width: 1200, height: 1800 },
            page_target_rect: { x: 0.05, y: 0.044, w: 0.426, h: 0.426 },
            local_source_rect: { x: 0, y: 0, w: 512, h: 768 },
            transform: { scale_x: 0.426, scale_y: 0.426, offset_x: 0.05, offset_y: 0.044 },
        },
        guide_state: { enabled: false, active: false },
    });

    assert.strictEqual(manifest.input_provenance.effective_input_digest, expectedDigestResult.effective_input_digest);
    assert.strictEqual(manifest.input_provenance.effective_input_contract_version, expectedDigestResult.contract_version);
    assert.strictEqual(manifest.input_provenance.effective_input_contract_version, "2.0.0");
});

test("Case N: Unrelated Scene edits do not enter effective-input evidence", () => {
    const ev1 = makeValidBuilderEvidence();
    const manifest1 = buildSceneResultManifest(ev1);

    // Modifying an unrelated scene outside scene_01's boundary produces the same effective input digest
    const ev2 = makeValidBuilderEvidence({
        root: {
            unrelated_document_scenes: [
                { scene_id: "scene_99", prompt: "completely unrelated scene" },
            ],
        },
    });
    const manifest2 = buildSceneResultManifest(ev2);

    assert.strictEqual(manifest1.input_provenance.effective_input_digest, manifest2.input_provenance.effective_input_digest);
});

test("Case O: Caller input mutation cannot change the returned manifest", () => {
    const ev = makeValidBuilderEvidence();
    const manifest = buildSceneResultManifest(ev);

    // Mutate caller input properties post-assembly
    ev.manifest_id = "00000000-0000-4000-8000-000000000000";
    ev.owner.scene_id = "scene_mutated";
    ev.compile_metadata.placement_mapping.page_target_rect.x = 0.999;
    ev.job.effective_settings.effective_seed = 999999;

    assert.strictEqual(manifest.manifest_id, VALID_MANIFEST_ID);
    assert.strictEqual(manifest.owner.scene_id, "scene_01");
    assert.strictEqual(manifest.placement.page_target_rect.x, 0.05);
    assert.strictEqual(manifest.execution.effective_settings.effective_seed, 42);
});

test("Case P: Invalid evidence does not mutate the caller's input", () => {
    const ev = makeValidBuilderEvidence({
        job: { state: "FAILED" },
    });
    const clonedBefore = JSON.parse(JSON.stringify(ev));

    assert.throws(() => buildSceneResultManifest(ev));

    assert.deepStrictEqual(ev, clonedBefore);
});

test("Case Q: Builder emits schema_version 1.1.0 and both digest and contract_version from existing digest function", () => {
    const ev = makeValidBuilderEvidence();
    const manifest = buildSceneResultManifest(ev);

    assert.strictEqual(manifest.schema_version, "1.1.0");
    assert.strictEqual(manifest.input_provenance.effective_input_contract_version, "2.0.0");
    assert.match(manifest.input_provenance.effective_input_digest, /^[0-9a-f]{64}$/);
});

test("Case R: Relevant effective-input changes remain represented by the digest", () => {
    const base = buildSceneResultManifest(makeValidBuilderEvidence());

    // Prompt change changes digest, preserves contract_version "2.0.0"
    const evPrompt = makeValidBuilderEvidence();
    evPrompt.plan.scene.prompt = "completely different prompt";
    const modifiedPrompt = buildSceneResultManifest(evPrompt);
    assert.notStrictEqual(modifiedPrompt.input_provenance.effective_input_digest, base.input_provenance.effective_input_digest);
    assert.strictEqual(modifiedPrompt.input_provenance.effective_input_contract_version, "2.0.0");

    // Seed change changes digest, preserves contract_version "2.0.0"
    const evSeed = makeValidBuilderEvidence();
    evSeed.compile_metadata.effective_settings.seed_requested = 9999;
    evSeed.compile_metadata.effective_settings.effective_seed = 9999;
    evSeed.job.effective_settings.seed_requested = 9999;
    evSeed.job.effective_settings.effective_seed = 9999;
    const modifiedSeed = buildSceneResultManifest(evSeed);
    assert.notStrictEqual(modifiedSeed.input_provenance.effective_input_digest, base.input_provenance.effective_input_digest);
    assert.strictEqual(modifiedSeed.input_provenance.effective_input_contract_version, "2.0.0");
});

test("Case S: Missing or inconsistent digest-version evidence fails closed", () => {
    // 1. Caller provides inconsistent contract version in evidence
    assert.throws(() => {
        buildSceneResultManifest(makeValidBuilderEvidence({
            root: {
                effective_input_contract_version: "1.0.0",
            },
        }));
    }, {
        name: "SceneResultBuilderError",
        code: "INCONSISTENT_DIGEST_VERSION",
    });

    assert.throws(() => {
        buildSceneResultManifest(makeValidBuilderEvidence({
            root: {
                input_provenance: {
                    authoring_snapshot_ref: "snapshots/doc-97f0fb52/v1.json",
                    authoring_snapshot_digest: SNAPSHOT_DIGEST,
                    effective_input_contract_version: "9.9.9",
                },
            },
        }));
    }, {
        name: "SceneResultBuilderError",
        code: "INCONSISTENT_DIGEST_VERSION",
    });

    // 2. Digest computation returns missing contract_version
    assert.throws(() => {
        buildSceneResultManifest(makeValidBuilderEvidence(), {
            _computeDigest: () => ({ effective_input_digest: "a".repeat(64) }),
        });
    }, {
        name: "SceneResultBuilderError",
        code: "MISSING_DIGEST_VERSION",
    });

    // 3. Digest computation returns unsupported contract_version
    assert.throws(() => {
        buildSceneResultManifest(makeValidBuilderEvidence(), {
            _computeDigest: () => ({ effective_input_digest: "a".repeat(64), contract_version: "1.0.0" }),
        });
    }, {
        name: "SceneResultBuilderError",
        code: "UNSUPPORTED_DIGEST_CONTRACT_VERSION",
    });
});
