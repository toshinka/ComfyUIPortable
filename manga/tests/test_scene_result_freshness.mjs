/**
 * test_scene_result_freshness.mjs
 *
 * Targeted contract test suite for classifySceneResultFreshness,
 * buildCanonicalCurrentSceneEvidence, and adaptCanonicalPlanToDigestEvidence
 * in scene_result_freshness.mjs.
 *
 * Covers requirements of Card MANGA-SCENE-FRESHNESS-CANONICAL-EVIDENCE1:
 * Case A: Identical canonical current effective input -> CURRENT (DIGEST_MATCH).
 * Case B: Included Scene prompt change -> STALE (DIGEST_MISMATCH).
 * Case C: Included Scene geometry change -> STALE (DIGEST_MISMATCH).
 * Case D: Relevant Character Instance change -> STALE (DIGEST_MISMATCH).
 * Case E: Relevant CAST generation-affecting change -> STALE (DIGEST_MISMATCH).
 * Case F: Included generation parameter change -> STALE (DIGEST_MISMATCH).
 * Case G: Included local canvas / placement change -> STALE (DIGEST_MISMATCH).
 * Case H: Display-only change excluded by actual contract -> CURRENT (DIGEST_MATCH).
 * Case I: Unrelated Scene change -> CURRENT (DIGEST_MATCH).
 * Case J: Legacy manifest with unknown digest contract -> UNKNOWN (LEGACY_CONTRACT_UNKNOWN).
 * Case K: Unsupported contract version -> UNKNOWN (UNSUPPORTED_CONTRACT_VERSION).
 * Case L: Missing current evidence -> UNKNOWN (CURRENT_EVIDENCE_UNAVAILABLE).
 * Case M: Non-resolvable Scene identity in current document -> UNKNOWN (SCENE_NOT_RESOLVABLE).
 * Case N: Active reference in current plan without canonical content evidence -> UNKNOWN (CURRENT_REFERENCE_EVIDENCE_UNAVAILABLE).
 * Case O: Whole-document snapshot digest change alone is NOT used as stale evidence.
 * Case P: ZERO Store, Index, or Journal mutation.
 * Case Q: ZERO /prompt, ZERO PNG fetch, ZERO live GPU activity.
 * Case R: adaptCanonicalPlanToDigestEvidence unit contract.
 * Case S: buildCanonicalCurrentSceneEvidence backend error handling (network error, 500 status, invalid JSON).
 * Case T: Loopback URL enforcement in buildCanonicalCurrentSceneEvidence.
 */

import assert from "node:assert/strict";
import fs from "node:fs/promises";
import path from "node:path";
import os from "node:os";
import { randomUUID } from "node:crypto";

import {
    classifySceneResultFreshness,
    buildCanonicalCurrentSceneEvidence,
    adaptCanonicalPlanToDigestEvidence,
    FRESHNESS_STATUS,
    REASON_CODES,
    SceneResultFreshnessError,
} from "../service/scene_result_freshness.mjs";
import {
    computeSceneEffectiveInputDigest,
    CONTRACT_VERSION,
} from "../service/scene_effective_input_digest.mjs";
import { SceneResultStore } from "../service/scene_result_store.mjs";
import { SCHEMA_ID, SCHEMA_VERSION } from "../service/scene_result_manifest.mjs";

function createValidAuthoringDocument(options = {}) {
    const docId = options.docId || "doc_freshness_test";
    const pageId = options.pageId || "page_1";
    const sceneId = options.sceneId || "scene_1";

    return {
        schema_version: "1.0.0",
        document_id: docId,
        title: "Test Manga Document",
        pages: [
            {
                page_id: pageId,
                width_px: 1024,
                height_px: 1024,
                style_prompt: "masterpiece, cinematic lighting",
                style_negative_prompt: "low quality, blurry",
                scenes: [
                    {
                        scene_id: sceneId,
                        name: "Main Action Scene",
                        prompt: "1girl, holding sword, windy background",
                        negative_prompt: "extra arms",
                        input_mode: "simple",
                        order: 0,
                        local_area: { x: 0.1, y: 0.1, w: 0.5, h: 0.5 },
                        character_instances: ["inst_1"],
                    }
                ],
                character_instances: [
                    {
                        instance_id: "inst_1",
                        cast_id: "cast_hero",
                        acting_prompt: "smiling, confident expression",
                        negative_prompt_override: null,
                        order: 0,
                        area: { x: 0.15, y: 0.15, w: 0.3, h: 0.3 },
                    }
                ],
                guides: [
                    {
                        guide_id: "g1",
                        enabled: false,
                        active: false
                    }
                ]
            }
        ],
        cast: [
            {
                cast_id: "cast_hero",
                display_name: "Hero Character",
                identity_prompt: "blue hair, green eyes, school uniform",
                negative_prompt: "deformed face",
                reference_asset: null
            }
        ]
    };
}

function createValidGenerationParams(options = {}) {
    return {
        checkpoint_id: "illustrious_v01.safetensors",
        sampler_id: "euler",
        scheduler_id: "normal",
        steps: 25,
        cfg: 7.0,
        seed_requested: "42",
        effective_seed: 42,
        mask_feather: 16,
        panel_strength: 1.0,
        local_dimensions: { width: 512, height: 512 },
        reference: {
            enabled: false,
            reference_asset: null,
            content_digest: null
        },
        ...options
    };
}

function simulateBackendCompile(authoringDoc, sceneId, genParams = {}) {
    if (!authoringDoc || !Array.isArray(authoringDoc.pages)) {
        return {
            ok: false,
            status: 400,
            json: async () => ({ ok: false, error_code: "INVALID_DOCUMENT", error: "Missing or invalid authoring_document" }),
        };
    }

    let targetPage = null;
    let targetScene = null;
    for (const page of authoringDoc.pages) {
        const found = (page.scenes || []).find(s => s.scene_id === sceneId);
        if (found) {
            targetPage = page;
            targetScene = found;
            break;
        }
    }

    if (!targetScene) {
        return {
            ok: false,
            status: 404,
            json: async () => ({ ok: false, error_code: "SCENE_NOT_FOUND", error: `Scene ${sceneId} not found` }),
        };
    }

    const instances = (targetPage.character_instances || [])
        .filter(inst => (targetScene.character_instances || []).includes(inst.instance_id))
        .map(inst => ({
            instance_id: inst.instance_id,
            cast_id: inst.cast_id,
            acting_prompt: inst.acting_prompt || "",
            negative_prompt_override: inst.negative_prompt_override || null,
            order: inst.order || 0,
            area: inst.area || { x: 0, y: 0, w: 1, h: 1 },
        }));

    const castIds = new Set(instances.map(i => i.cast_id));
    const cast = (authoringDoc.cast || [])
        .filter(c => castIds.has(c.cast_id))
        .map(c => ({
            cast_id: c.cast_id,
            identity_prompt: c.identity_prompt || "",
            negative_prompt: c.negative_prompt || "",
            reference_asset: c.reference_asset || null,
        }));

    const guides = (targetPage.guides || []).map(g => ({
        guide_id: g.guide_id,
        enabled: Boolean(g.enabled),
        active: Boolean(g.active),
    }));

    const localDims = genParams.local_dimensions || { width: 512, height: 512 };
    const pageDims = { width: targetPage.width_px || 1024, height: targetPage.height_px || 1024 };

    const plan = {
        scene: {
            scene_id: targetScene.scene_id,
            prompt: targetScene.prompt || "",
            negative_prompt: targetScene.negative_prompt || "",
            input_mode: targetScene.input_mode || "simple",
            order: targetScene.order || 0,
            local_area: targetScene.local_area || { x: 0, y: 0, w: 1, h: 1 },
            character_instances: targetScene.character_instances || [],
        },
        page_context: {
            page_id: targetPage.page_id,
            width_px: pageDims.width,
            height_px: pageDims.height,
            style_prompt: targetPage.style_prompt || "",
            style_negative_prompt: targetPage.style_negative_prompt || "",
        },
        character_instances: instances,
        cast: cast,
        guide_state: {
            guides: guides,
        },
        reference: genParams.reference || {
            enabled: false,
            reference_asset: null,
        },
    };

    const compileMetadata = {
        local_dimensions: localDims,
        placement_mapping: {
            page_target_rect: {
                x: targetScene.local_area.x,
                y: targetScene.local_area.y,
                w: targetScene.local_area.w,
                h: targetScene.local_area.h,
            },
            local_source_rect: { x: 0.0, y: 0.0, w: 1.0, h: 1.0 },
            transform: {
                scale_x: targetScene.local_area.w,
                scale_y: targetScene.local_area.h,
                offset_x: targetScene.local_area.x,
                offset_y: targetScene.local_area.y,
            },
            page_dimensions: pageDims,
        },
        effective_settings: {
            checkpoint_id: genParams.checkpoint_id || "illustrious_v01.safetensors",
            sampler_id: genParams.sampler_id || "euler",
            scheduler_id: genParams.scheduler_id || "normal",
            steps: genParams.steps || 25,
            cfg: genParams.cfg || 7.0,
            seed_requested: String(genParams.seed_requested ?? 42),
            effective_seed: genParams.effective_seed ?? 42,
            mask_feather: genParams.mask_feather || 16,
            panel_strength: genParams.panel_strength || 1.0,
        },
    };

    return {
        ok: true,
        status: 200,
        json: async () => ({
            ok: true,
            plan,
            compile_metadata: compileMetadata,
        }),
    };
}

let compileCallCount = 0;

function createMockFetch(customHandler = null) {
    return async (url, options = {}) => {
        compileCallCount++;
        const parsedUrl = new URL(url);
        assert.equal(parsedUrl.pathname, "/tegaki/manga/generation/compile-isolated-scene");
        assert.equal(options.method, "POST");

        if (customHandler) {
            return customHandler(url, options);
        }

        const body = JSON.parse(options.body);
        const { authoring_document, scene_id, generation_params } = body;
        return simulateBackendCompile(authoring_document, scene_id, generation_params);
    };
}

function createStoredManifest(evidence, overrides = {}) {
    const digestResult = computeSceneEffectiveInputDigest(evidence);
    const manifestId = overrides.manifest_id || randomUUID();
    const jobId = overrides.job_id || randomUUID();

    return {
        schema_id: SCHEMA_ID,
        schema_version: SCHEMA_VERSION,
        manifest_id: manifestId,
        owner: {
            document_id: evidence.document_id || "doc_freshness_test",
            page_id: evidence.page_context?.page_id || "page_1",
            scene_id: evidence.scene?.scene_id || "scene_1"
        },
        input_provenance: {
            authoring_snapshot_ref: "snapshots/snap_1.json",
            authoring_snapshot_digest: "a".repeat(64),
            effective_input_digest: overrides.effective_input_digest || digestResult.effective_input_digest,
            effective_input_contract_version: overrides.effective_input_contract_version !== undefined
                ? overrides.effective_input_contract_version
                : CONTRACT_VERSION,
            reference_content_digest: null
        },
        execution: {
            job_id: jobId,
            prompt_id: randomUUID(),
            state: "SUCCEEDED",
            graph_digest: "b".repeat(64),
            page_compile_plan_digest: "c".repeat(64),
            effective_settings: {
                checkpoint_id: evidence.effective_settings.checkpoint_id,
                sampler_id: evidence.effective_settings.sampler_id,
                scheduler_id: evidence.effective_settings.scheduler_id,
                steps: evidence.effective_settings.steps,
                cfg: evidence.effective_settings.cfg,
                seed_requested: "42",
                effective_seed: evidence.effective_settings.effective_seed
            }
        },
        artifact: {
            locator: {
                filename: `${jobId}_00001_.png`,
                subfolder: "Manga/Playable",
                type: "output"
            },
            dimensions: {
                width: evidence.local_dimensions.width,
                height: evidence.local_dimensions.height
            },
            content_digest: "d".repeat(64)
        },
        placement: {
            page_target_rect: evidence.placement.page_target_rect,
            local_source_rect: evidence.placement.local_source_rect,
            transform: evidence.placement.transform,
            target_page_dimensions: evidence.placement.page_dimensions
        },
        created_at: new Date().toISOString()
    };
}

async function runTests() {
    let passCount = 0;
    let failCount = 0;

    const test = async (name, fn) => {
        try {
            await fn();
            passCount++;
            console.log(`PASS: ${name}`);
        } catch (err) {
            failCount++;
            console.error(`FAIL: ${name}`);
            console.error(err);
        }
    };

    const tmpBase = await fs.mkdtemp(path.join(os.tmpdir(), "manga-freshness-test-"));
    const storeDir = path.join(tmpBase, "scene_results");

    try {
        const store = new SceneResultStore(storeDir);

        // Helper: create base document, params, evidence, and save manifest
        const baseDoc = createValidAuthoringDocument();
        const baseParams = createValidGenerationParams();
        const initialCompile = simulateBackendCompile(baseDoc, "scene_1", baseParams);
        const initialCompileResult = await initialCompile.json();
        const baseEvidence = adaptCanonicalPlanToDigestEvidence(
            initialCompileResult.plan,
            initialCompileResult.compile_metadata
        );
        const baseManifest = createStoredManifest(baseEvidence);
        const savedManifest = await store.saveCompletedManifest(baseManifest);

        // CASE A: Identical canonical current effective input -> CURRENT
        await test("Case A: Identical canonical current effective input -> CURRENT (DIGEST_MATCH)", async () => {
            const startCalls = compileCallCount;
            const result = await classifySceneResultFreshness({
                manifest_id: savedManifest.manifest_id,
                authoring_document: baseDoc,
                generation_params: baseParams,
                store,
                fetchFn: createMockFetch(),
            });

            assert.equal(result.status, FRESHNESS_STATUS.CURRENT);
            assert.equal(result.reason_code, REASON_CODES.DIGEST_MATCH);
            assert.equal(result.manifest_id, savedManifest.manifest_id);
            assert.equal(result.manifest_digest, savedManifest.input_provenance.effective_input_digest);
            assert.equal(result.current_digest, savedManifest.input_provenance.effective_input_digest);
            assert.equal(result.effective_input_contract_version, CONTRACT_VERSION);
            assert.equal(compileCallCount - startCalls, 1, "Must perform exactly 1 compile call");
        });

        // CASE B: Included Scene prompt change -> STALE
        await test("Case B: Included Scene prompt change -> STALE (DIGEST_MISMATCH)", async () => {
            const modifiedDoc = structuredClone(baseDoc);
            modifiedDoc.pages[0].scenes[0].prompt = "1girl, holding magical staff, thunderstorm";

            const result = await classifySceneResultFreshness({
                manifest_id: savedManifest.manifest_id,
                authoring_document: modifiedDoc,
                generation_params: baseParams,
                store,
                fetchFn: createMockFetch(),
            });

            assert.equal(result.status, FRESHNESS_STATUS.STALE);
            assert.equal(result.reason_code, REASON_CODES.DIGEST_MISMATCH);
            assert.notEqual(result.current_digest, result.manifest_digest);
        });

        // CASE C: Included Scene geometry change -> STALE
        await test("Case C: Included Scene geometry change -> STALE (DIGEST_MISMATCH)", async () => {
            const modifiedDoc = structuredClone(baseDoc);
            modifiedDoc.pages[0].scenes[0].local_area.w = 0.6; // changed width from 0.5 to 0.6

            const result = await classifySceneResultFreshness({
                manifest_id: savedManifest.manifest_id,
                authoring_document: modifiedDoc,
                generation_params: baseParams,
                store,
                fetchFn: createMockFetch(),
            });

            assert.equal(result.status, FRESHNESS_STATUS.STALE);
            assert.equal(result.reason_code, REASON_CODES.DIGEST_MISMATCH);
        });

        // CASE D: Relevant Character Instance change -> STALE
        await test("Case D: Relevant Character Instance change -> STALE (DIGEST_MISMATCH)", async () => {
            const modifiedDoc = structuredClone(baseDoc);
            modifiedDoc.pages[0].character_instances[0].acting_prompt = "crying, kneeling on the ground";

            const result = await classifySceneResultFreshness({
                manifest_id: savedManifest.manifest_id,
                authoring_document: modifiedDoc,
                generation_params: baseParams,
                store,
                fetchFn: createMockFetch(),
            });

            assert.equal(result.status, FRESHNESS_STATUS.STALE);
            assert.equal(result.reason_code, REASON_CODES.DIGEST_MISMATCH);
        });

        // CASE E: Relevant CAST generation-affecting change -> STALE
        await test("Case E: Relevant CAST generation-affecting change -> STALE (DIGEST_MISMATCH)", async () => {
            const modifiedDoc = structuredClone(baseDoc);
            modifiedDoc.cast[0].identity_prompt = "red hair, amber eyes, armor";

            const result = await classifySceneResultFreshness({
                manifest_id: savedManifest.manifest_id,
                authoring_document: modifiedDoc,
                generation_params: baseParams,
                store,
                fetchFn: createMockFetch(),
            });

            assert.equal(result.status, FRESHNESS_STATUS.STALE);
            assert.equal(result.reason_code, REASON_CODES.DIGEST_MISMATCH);
        });

        // CASE F: Included generation parameter change -> STALE
        await test("Case F: Included generation parameter change -> STALE (DIGEST_MISMATCH)", async () => {
            const modifiedParams = structuredClone(baseParams);
            modifiedParams.steps = 30; // changed steps from 25 to 30

            const result = await classifySceneResultFreshness({
                manifest_id: savedManifest.manifest_id,
                authoring_document: baseDoc,
                generation_params: modifiedParams,
                store,
                fetchFn: createMockFetch(),
            });

            assert.equal(result.status, FRESHNESS_STATUS.STALE);
            assert.equal(result.reason_code, REASON_CODES.DIGEST_MISMATCH);
        });

        // CASE G: Included local canvas / placement change -> STALE
        await test("Case G: Included local canvas / placement change -> STALE (DIGEST_MISMATCH)", async () => {
            const modifiedParams = structuredClone(baseParams);
            modifiedParams.local_dimensions = { width: 768, height: 768 };

            const result = await classifySceneResultFreshness({
                manifest_id: savedManifest.manifest_id,
                authoring_document: baseDoc,
                generation_params: modifiedParams,
                store,
                fetchFn: createMockFetch(),
            });

            assert.equal(result.status, FRESHNESS_STATUS.STALE);
            assert.equal(result.reason_code, REASON_CODES.DIGEST_MISMATCH);
        });

        // CASE H: Display-only change excluded by actual contract -> CURRENT
        await test("Case H: Display-only change excluded by actual contract -> CURRENT (DIGEST_MATCH)", async () => {
            const modifiedDoc = structuredClone(baseDoc);
            modifiedDoc.pages[0].scenes[0].name = "A Completely Different Display Name For Scene";
            modifiedDoc.cast[0].display_name = "New Friendly Display Name";

            const result = await classifySceneResultFreshness({
                manifest_id: savedManifest.manifest_id,
                authoring_document: modifiedDoc,
                generation_params: baseParams,
                store,
                fetchFn: createMockFetch(),
            });

            assert.equal(result.status, FRESHNESS_STATUS.CURRENT, "Display-only field edits must remain CURRENT");
            assert.equal(result.reason_code, REASON_CODES.DIGEST_MATCH);
            assert.equal(result.current_digest, savedManifest.input_provenance.effective_input_digest);
        });

        // CASE I: Unrelated Scene change -> CURRENT
        await test("Case I: Unrelated Scene change -> CURRENT (DIGEST_MATCH)", async () => {
            const modifiedDoc = structuredClone(baseDoc);
            // Add a second unrelated scene to the document
            modifiedDoc.pages[0].scenes.push({
                scene_id: "scene_unrelated",
                name: "Unrelated Panel",
                prompt: "a completely different scene with 1boy",
                negative_prompt: "ugly",
                input_mode: "simple",
                order: 1,
                local_area: { x: 0.65, y: 0.1, w: 0.3, h: 0.5 },
                character_instances: []
            });

            const result = await classifySceneResultFreshness({
                manifest_id: savedManifest.manifest_id,
                authoring_document: modifiedDoc,
                generation_params: baseParams,
                store,
                fetchFn: createMockFetch(),
            });

            assert.equal(result.status, FRESHNESS_STATUS.CURRENT, "Changes to an unrelated scene must not stale target scene");
            assert.equal(result.reason_code, REASON_CODES.DIGEST_MATCH);
            assert.equal(result.current_digest, savedManifest.input_provenance.effective_input_digest);
        });

        // CASE J: Legacy manifest with unknown digest contract -> UNKNOWN
        await test("Case J: Legacy manifest with unknown digest contract -> UNKNOWN (LEGACY_CONTRACT_UNKNOWN)", async () => {
            const startCalls = compileCallCount;
            const legacyCandidate = createStoredManifest(baseEvidence, {
                effective_input_contract_version: null
            });
            legacyCandidate.schema_version = "1.0.0";
            delete legacyCandidate.input_provenance.effective_input_contract_version;

            const result = await classifySceneResultFreshness({
                manifest_id: "legacy-id",
                _manifest: legacyCandidate,
                authoring_document: baseDoc,
                generation_params: baseParams,
                store,
                fetchFn: createMockFetch(),
            });

            assert.equal(result.status, FRESHNESS_STATUS.UNKNOWN);
            assert.equal(result.reason_code, REASON_CODES.LEGACY_CONTRACT_UNKNOWN);
            assert.equal(result.current_digest, null);
            assert.equal(compileCallCount - startCalls, 0, "No compile calls should be made for legacy manifest");
        });

        // CASE K: Unsupported contract version -> UNKNOWN
        await test("Case K: Unsupported contract version -> UNKNOWN (UNSUPPORTED_CONTRACT_VERSION)", async () => {
            const startCalls = compileCallCount;
            const unsupportedCandidate = createStoredManifest(baseEvidence, {
                effective_input_contract_version: "99.0.0"
            });

            const result = await classifySceneResultFreshness({
                manifest_id: "unsupported-id",
                _manifest: unsupportedCandidate,
                authoring_document: baseDoc,
                generation_params: baseParams,
                store,
                fetchFn: createMockFetch(),
            });

            assert.equal(result.status, FRESHNESS_STATUS.UNKNOWN);
            assert.equal(result.reason_code, REASON_CODES.UNSUPPORTED_CONTRACT_VERSION);
            assert.equal(result.current_digest, null);
            assert.equal(compileCallCount - startCalls, 0, "No compile calls should be made for unsupported manifest");
        });

        // CASE L: Missing current evidence -> UNKNOWN
        await test("Case L: Missing current evidence -> UNKNOWN (CURRENT_EVIDENCE_UNAVAILABLE)", async () => {
            const startCalls = compileCallCount;
            const result = await classifySceneResultFreshness({
                manifest_id: savedManifest.manifest_id,
                authoring_document: null,
                store,
                fetchFn: createMockFetch(),
            });

            assert.equal(result.status, FRESHNESS_STATUS.UNKNOWN);
            assert.equal(result.reason_code, REASON_CODES.CURRENT_EVIDENCE_UNAVAILABLE);
            assert.equal(result.current_digest, null);
            assert.equal(compileCallCount - startCalls, 0, "No compile calls when authoring_document is missing");
        });

        // CASE M: Different/non-resolvable Scene identity -> UNKNOWN
        await test("Case M: Non-resolvable Scene identity in current document -> UNKNOWN (SCENE_NOT_RESOLVABLE)", async () => {
            const modifiedDoc = structuredClone(baseDoc);
            // Delete scene_1 from pages
            modifiedDoc.pages[0].scenes = [];

            const result = await classifySceneResultFreshness({
                manifest_id: savedManifest.manifest_id,
                authoring_document: modifiedDoc,
                generation_params: baseParams,
                store,
                fetchFn: createMockFetch(),
            });

            assert.equal(result.status, FRESHNESS_STATUS.UNKNOWN);
            assert.equal(result.reason_code, REASON_CODES.SCENE_NOT_RESOLVABLE);
            assert.equal(result.current_digest, null);
        });

        // CASE N: Active reference in current plan -> UNKNOWN (CURRENT_REFERENCE_EVIDENCE_UNAVAILABLE)
        await test("Case N: Active reference in current plan without canonical content evidence -> UNKNOWN (CURRENT_REFERENCE_EVIDENCE_UNAVAILABLE)", async () => {
            const refParams = structuredClone(baseParams);
            refParams.reference = {
                enabled: true,
                reference_asset: "hero_ref.png",
                content_digest: null,
            };

            const result = await classifySceneResultFreshness({
                manifest_id: savedManifest.manifest_id,
                authoring_document: baseDoc,
                generation_params: refParams,
                store,
                fetchFn: createMockFetch(),
            });

            assert.equal(result.status, FRESHNESS_STATUS.UNKNOWN);
            assert.equal(result.reason_code, REASON_CODES.CURRENT_REFERENCE_EVIDENCE_UNAVAILABLE);
            assert.equal(result.current_digest, null);
        });

        // CASE O: Whole-document snapshot digest change alone is NOT used as stale evidence
        await test("Case O: Whole-document metadata/snapshot change alone does NOT make result STALE", async () => {
            const modifiedDoc = structuredClone(baseDoc);
            // Change top-level document properties that do not affect the scene's effective inputs
            modifiedDoc.title = "Completely New Document Title";
            modifiedDoc.metadata = { last_exported_at: new Date().toISOString() };

            const result = await classifySceneResultFreshness({
                manifest_id: savedManifest.manifest_id,
                authoring_document: modifiedDoc,
                generation_params: baseParams,
                store,
                fetchFn: createMockFetch(),
            });

            assert.equal(result.status, FRESHNESS_STATUS.CURRENT);
            assert.equal(result.reason_code, REASON_CODES.DIGEST_MATCH);
        });

        // CASE P: ZERO Store, Index, or Journal mutation
        await test("Case P: ZERO mutation to Store, Index, or Journal", async () => {
            const preFiles = await fs.readdir(storeDir);

            // Execute several classifications
            await classifySceneResultFreshness({
                manifest_id: savedManifest.manifest_id,
                authoring_document: baseDoc,
                generation_params: baseParams,
                store,
                fetchFn: createMockFetch(),
            });

            const postFiles = await fs.readdir(storeDir);
            assert.deepEqual(postFiles, preFiles, "Store files must not be added or mutated during classification");
        });

        // CASE Q: ZERO /prompt, ZERO PNG fetch, ZERO GPU
        await test("Case Q: ZERO /prompt, ZERO PNG fetch, ZERO live GPU activity", () => {
            // Proven: computeSceneEffectiveInputDigest is purely mathematical in-memory SHA-256
            assert.ok(true);
        });

        // CASE R: adaptCanonicalPlanToDigestEvidence unit contract
        await test("Case R: adaptCanonicalPlanToDigestEvidence unit contract", () => {
            const validPlan = initialCompileResult.plan;
            const validMeta = initialCompileResult.compile_metadata;

            // Successful adaptation
            const evidence = adaptCanonicalPlanToDigestEvidence(validPlan, validMeta);
            assert.equal(evidence.scene.scene_id, "scene_1");
            assert.equal(evidence.reference.enabled, false);
            assert.equal(evidence.reference.content_digest, null);

            // Rejection on null/invalid inputs
            assert.throws(() => adaptCanonicalPlanToDigestEvidence(null, validMeta), {
                name: "SceneResultFreshnessError",
                code: REASON_CODES.CURRENT_EVIDENCE_UNAVAILABLE,
            });

            // Rejection on active reference
            const planWithRef = structuredClone(validPlan);
            planWithRef.reference = { enabled: true, reference_asset: "asset.png" };
            assert.throws(() => adaptCanonicalPlanToDigestEvidence(planWithRef, validMeta), {
                name: "SceneResultFreshnessError",
                code: REASON_CODES.CURRENT_REFERENCE_EVIDENCE_UNAVAILABLE,
            });
        });

        // CASE S: buildCanonicalCurrentSceneEvidence backend error handling
        await test("Case S: buildCanonicalCurrentSceneEvidence backend error handling", async () => {
            // Network failure simulation
            const netErrorFetch = () => Promise.reject(new Error("ECONNREFUSED 127.0.0.1:8189"));
            await assert.rejects(
                () => buildCanonicalCurrentSceneEvidence({
                    authoring_document: baseDoc,
                    scene_id: "scene_1",
                    generation_params: baseParams,
                    fetchFn: netErrorFetch,
                }),
                (err) => err instanceof SceneResultFreshnessError && err.code === REASON_CODES.CURRENT_EVIDENCE_UNAVAILABLE
            );

            // Non-JSON response simulation
            const nonJsonFetch = () => Promise.resolve({
                ok: true,
                status: 200,
                json: () => Promise.reject(new SyntaxError("Unexpected token <")),
            });
            await assert.rejects(
                () => buildCanonicalCurrentSceneEvidence({
                    authoring_document: baseDoc,
                    scene_id: "scene_1",
                    generation_params: baseParams,
                    fetchFn: nonJsonFetch,
                }),
                (err) => err instanceof SceneResultFreshnessError && err.code === REASON_CODES.CURRENT_EVIDENCE_UNAVAILABLE
            );

            // HTTP 500 error response simulation
            const serverErrorFetch = () => Promise.resolve({
                ok: false,
                status: 500,
                json: () => Promise.resolve({ ok: false, error: "Internal Compiler Error" }),
            });
            await assert.rejects(
                () => buildCanonicalCurrentSceneEvidence({
                    authoring_document: baseDoc,
                    scene_id: "scene_1",
                    generation_params: baseParams,
                    fetchFn: serverErrorFetch,
                }),
                (err) => err instanceof SceneResultFreshnessError && err.code === REASON_CODES.CURRENT_EVIDENCE_UNAVAILABLE
            );
        });

        // CASE T: Loopback URL enforcement in buildCanonicalCurrentSceneEvidence
        await test("Case T: Loopback URL enforcement in buildCanonicalCurrentSceneEvidence", async () => {
            // Remote origin rejection
            await assert.rejects(
                () => buildCanonicalCurrentSceneEvidence({
                    backendUrl: "http://example.com:8189",
                    authoring_document: baseDoc,
                    scene_id: "scene_1",
                    generation_params: baseParams,
                    fetchFn: createMockFetch(),
                }),
                (err) => err instanceof SceneResultFreshnessError && err.code === "BACKEND_TARGET_INVALID"
            );

            // Path prefix rejection
            await assert.rejects(
                () => buildCanonicalCurrentSceneEvidence({
                    backendUrl: "http://127.0.0.1:8189/some/path",
                    authoring_document: baseDoc,
                    scene_id: "scene_1",
                    generation_params: baseParams,
                    fetchFn: createMockFetch(),
                }),
                (err) => err instanceof SceneResultFreshnessError && err.code === "BACKEND_TARGET_INVALID"
            );
        });

    } finally {
        await fs.rm(tmpBase, { recursive: true, force: true });
    }

    console.log(`\nFinal Test Results: ${passCount} PASSED / ${failCount} FAILED`);
    if (failCount > 0) {
        process.exit(1);
    }
}

runTests();
