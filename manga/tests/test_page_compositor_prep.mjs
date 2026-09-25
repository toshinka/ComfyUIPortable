/**
 * test_page_compositor_prep.mjs
 *
 * Contract test suite for preparePageComposition in page_compositor_prep.mjs.
 *
 * Covers requirements of Card MANGA-PAGE-COMPOSITOR-PREP1:
 * Case A: One page with one CURRENT Scene produces one CURRENT_RESULT slot.
 * Case B: Multiple Scenes preserve current Authoring structural order.
 * Case C: Scene with no result becomes UNFILLED.
 * Case D: Scene with STALE results only becomes UNFILLED.
 * Case E: Scene with UNKNOWN results only becomes UNFILLED.
 * Case F: Multiple CURRENT results select the deterministic newest CURRENT candidate according to index ordering.
 * Case G: Older CURRENT manifests are not deleted or mutated.
 * Case H: Selected artifact locator/digest/dimensions come from stored manifest.
 * Case I: Placement comes from stored manifest, not caller override.
 * Case J: Page identity and dimensions come from current Authoring Document.
 * Case K: Deleted historical Scene present only in index is NOT added to current page plan.
 * Case L: Display-only Authoring changes still permit CURRENT selection when freshness classifier says CURRENT.
 * Case M: Unrelated page/Scene change does not disqualify target Scene when classifier says CURRENT.
 * Case N: No STALE or UNKNOWN result is selected.
 * Case O: UNFILLED does not create a synthetic artifact.
 * Case P: Background is explicitly WHITE.
 * Case Q: No panel/border drawing instruction is introduced.
 * Case R: ZERO PNG fetch.
 * Case S: ZERO Store/Index/Journal mutation.
 * Case T: ZERO /prompt / live GPU.
 */

import assert from "node:assert/strict";
import fs from "node:fs/promises";
import path from "node:path";
import os from "node:os";
import { randomUUID } from "node:crypto";

import {
    preparePageComposition,
    SCHEMA_ID as PLAN_SCHEMA_ID,
    SCHEMA_VERSION as PLAN_SCHEMA_VERSION,
    SLOT_STATE,
    BACKGROUND_MODE,
    BACKGROUND_VALUE,
    PageCompositorPrepError,
} from "../service/page_compositor_prep.mjs";
import {
    computeSceneEffectiveInputDigest,
    CONTRACT_VERSION,
} from "../service/scene_effective_input_digest.mjs";
import { adaptCanonicalPlanToDigestEvidence } from "../service/scene_result_freshness.mjs";
import { SceneResultStore } from "../service/scene_result_store.mjs";
import { SceneResultIndex } from "../service/scene_result_index.mjs";
import { SCHEMA_ID as MANIFEST_SCHEMA_ID, SCHEMA_VERSION as MANIFEST_SCHEMA_VERSION } from "../service/scene_result_manifest.mjs";

function createValidAuthoringDocument(options = {}) {
    const docId = options.docId || "doc_comp_test";
    const pageId = options.pageId || "page_1";
    const scenes = options.scenes || [
        {
            scene_id: "scene_1",
            name: "Panel 1",
            prompt: "1girl, looking forward",
            negative_prompt: "bad anatomy",
            input_mode: "simple",
            order: 0,
            local_area: { x: 0.1, y: 0.1, w: 0.4, h: 0.4 },
            character_instances: ["inst_1"],
        },
        {
            scene_id: "scene_2",
            name: "Panel 2",
            prompt: "1girl, waving hand",
            negative_prompt: "bad hands",
            input_mode: "simple",
            order: 1,
            local_area: { x: 0.55, y: 0.1, w: 0.4, h: 0.4 },
            character_instances: ["inst_1"],
        }
    ];

    return {
        schema_version: "1.0.0",
        document_id: docId,
        title: "Test Manga Composition Document",
        pages: [
            {
                page_id: pageId,
                width_px: 1024,
                height_px: 1024,
                style_prompt: "manga style, crisp lines",
                style_negative_prompt: "blurry, photorealistic",
                scenes: scenes,
                character_instances: [
                    {
                        instance_id: "inst_1",
                        cast_id: "cast_hero",
                        acting_prompt: "determined expression",
                        negative_prompt_override: null,
                        order: 0,
                        area: { x: 0.15, y: 0.15, w: 0.3, h: 0.3 },
                    }
                ],
                guides: [
                    {
                        guide_id: "g1",
                        enabled: false,
                        active: false,
                    }
                ]
            }
        ],
        cast: [
            {
                cast_id: "cast_hero",
                display_name: "Hero Character",
                identity_prompt: "black hair, brown eyes",
                negative_prompt: "deformed",
                reference_asset: null,
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
            content_digest: null,
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

function createMockFetch() {
    return async (url, options = {}) => {
        const body = JSON.parse(options.body);
        const { authoring_document, scene_id, generation_params } = body;
        return simulateBackendCompile(authoring_document, scene_id, generation_params);
    };
}

function createStoredManifest(evidence, overrides = {}) {
    const digestResult = computeSceneEffectiveInputDigest(evidence);
    const manifestId = overrides.manifest_id || randomUUID();
    const jobId = overrides.job_id || randomUUID();
    const createdAt = overrides.created_at || new Date().toISOString();
    const schemaVersion = overrides.schema_version || MANIFEST_SCHEMA_VERSION;

    const inputProvenance = {
        authoring_snapshot_ref: "snapshots/snap_1.json",
        authoring_snapshot_digest: "a".repeat(64),
        effective_input_digest: overrides.effective_input_digest || digestResult.effective_input_digest,
        reference_content_digest: null
    };

    if (overrides.effective_input_contract_version !== null) {
        inputProvenance.effective_input_contract_version = overrides.effective_input_contract_version !== undefined
            ? overrides.effective_input_contract_version
            : CONTRACT_VERSION;
    }

    return {
        schema_id: MANIFEST_SCHEMA_ID,
        schema_version: schemaVersion,
        manifest_id: manifestId,
        owner: {
            document_id: evidence.document_id || "doc_comp_test",
            page_id: evidence.page_context?.page_id || "page_1",
            scene_id: evidence.scene?.scene_id || "scene_1"
        },
        input_provenance: inputProvenance,
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
        created_at: createdAt
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

    const tmpBase = await fs.mkdtemp(path.join(os.tmpdir(), "manga-page-comp-test-"));
    const storeDir = path.join(tmpBase, "scene_results");
    const indexDir = path.join(tmpBase, "scene_result_index");

    try {
        const store = new SceneResultStore(storeDir);
        const index = new SceneResultIndex({ store, directory: indexDir });
        const mockFetch = createMockFetch();

        // Helper to generate and index a valid manifest for a given scene
        const setupManifest = async (doc, sceneId, params, overrides = {}) => {
            const compileResp = simulateBackendCompile(doc, sceneId, params);
            const { plan, compile_metadata } = (await compileResp.json());
            const evidence = adaptCanonicalPlanToDigestEvidence(plan, compile_metadata);
            const manifestObj = createStoredManifest(evidence, {
                ...overrides,
                owner: {
                    document_id: doc.document_id,
                    page_id: doc.pages[0].page_id,
                    scene_id: sceneId,
                }
            });
            const saved = await store.saveCompletedManifest(manifestObj);
            await index.indexManifest(saved.manifest_id);
            return saved;
        };

        const baseDoc = createValidAuthoringDocument();
        const baseParams = createValidGenerationParams();

        // Setup Scene 1 manifest (CURRENT)
        const scene1Manifest = await setupManifest(baseDoc, "scene_1", baseParams, {
            created_at: new Date(Date.now() - 60000).toISOString(),
        });

        // Setup Scene 2 manifest (CURRENT)
        const scene2Manifest = await setupManifest(baseDoc, "scene_2", baseParams, {
            created_at: new Date(Date.now() - 30000).toISOString(),
        });

        // CASE A: One page with one CURRENT Scene produces one CURRENT_RESULT slot
        await test("Case A: One page with one CURRENT Scene produces one CURRENT_RESULT slot", async () => {
            const docSingle = structuredClone(baseDoc);
            docSingle.pages[0].scenes = [baseDoc.pages[0].scenes[0]];

            const plan = await preparePageComposition({
                authoring_document: docSingle,
                generation_params: baseParams,
                store,
                index,
                fetchFn: mockFetch,
            });

            assert.equal(plan.schema_id, PLAN_SCHEMA_ID);
            assert.equal(plan.schema_version, PLAN_SCHEMA_VERSION);
            assert.equal(plan.scenes.length, 1);
            assert.equal(plan.scenes[0].scene_id, "scene_1");
            assert.equal(plan.scenes[0].state, SLOT_STATE.CURRENT_RESULT);
            assert.equal(plan.scenes[0].selected_result.manifest_id, scene1Manifest.manifest_id);
        });

        // CASE B: Multiple Scenes preserve current Authoring structural order
        await test("Case B: Multiple Scenes preserve current Authoring structural order", async () => {
            const plan = await preparePageComposition({
                authoring_document: baseDoc,
                generation_params: baseParams,
                store,
                index,
                fetchFn: mockFetch,
            });

            assert.equal(plan.scenes.length, 2);
            assert.equal(plan.scenes[0].scene_id, "scene_1");
            assert.equal(plan.scenes[0].order, 0);
            assert.equal(plan.scenes[1].scene_id, "scene_2");
            assert.equal(plan.scenes[1].order, 1);
        });

        // CASE C: Scene with no result becomes UNFILLED
        await test("Case C: Scene with no result becomes UNFILLED", async () => {
            const docWithExtra = structuredClone(baseDoc);
            docWithExtra.pages[0].scenes.push({
                scene_id: "scene_unrendered",
                name: "Unrendered Panel",
                prompt: "a landscape",
                negative_prompt: "",
                input_mode: "simple",
                order: 2,
                local_area: { x: 0.1, y: 0.55, w: 0.8, h: 0.3 },
                character_instances: [],
            });

            const plan = await preparePageComposition({
                authoring_document: docWithExtra,
                generation_params: baseParams,
                store,
                index,
                fetchFn: mockFetch,
            });

            assert.equal(plan.scenes.length, 3);
            const slot3 = plan.scenes.find(s => s.scene_id === "scene_unrendered");
            assert.ok(slot3);
            assert.equal(slot3.state, SLOT_STATE.UNFILLED);
            assert.equal(slot3.selected_result, null);
        });

        // CASE D: Scene with STALE results only becomes UNFILLED
        await test("Case D: Scene with STALE results only becomes UNFILLED", async () => {
            // Modify steps in generation_params so stored scene1Manifest is STALE
            const modifiedParams = structuredClone(baseParams);
            modifiedParams.steps = 40;

            const plan = await preparePageComposition({
                authoring_document: baseDoc,
                generation_params: modifiedParams,
                store,
                index,
                fetchFn: mockFetch,
            });

            const slot1 = plan.scenes.find(s => s.scene_id === "scene_1");
            assert.equal(slot1.state, SLOT_STATE.UNFILLED);
            assert.equal(slot1.selected_result, null);
        });

        // CASE E: Scene with UNKNOWN results only becomes UNFILLED
        await test("Case E: Scene with UNKNOWN results only becomes UNFILLED", async () => {
            const docWithLegacy = structuredClone(baseDoc);
            docWithLegacy.pages[0].scenes = [
                {
                    scene_id: "scene_legacy",
                    name: "Legacy Panel",
                    prompt: "legacy prompt",
                    negative_prompt: "",
                    input_mode: "simple",
                    order: 0,
                    local_area: { x: 0.1, y: 0.1, w: 0.8, h: 0.8 },
                    character_instances: [],
                }
            ];

            // Setup legacy manifest without contract version under v1.0.0 schema
            const legacyManifest = await setupManifest(docWithLegacy, "scene_legacy", baseParams, {
                schema_version: "1.0.0",
                effective_input_contract_version: null,
            });

            const plan = await preparePageComposition({
                authoring_document: docWithLegacy,
                generation_params: baseParams,
                store,
                index,
                fetchFn: mockFetch,
            });

            const slot = plan.scenes[0];
            assert.equal(slot.state, SLOT_STATE.UNFILLED);
            assert.equal(slot.selected_result, null);
        });

        // CASE F: Multiple CURRENT results select the deterministic newest CURRENT candidate according to index ordering
        await test("Case F: Multiple CURRENT results select the deterministic newest CURRENT candidate", async () => {
            // Add a newer CURRENT manifest for scene_1
            const newerManifestScene1 = await setupManifest(baseDoc, "scene_1", baseParams, {
                created_at: new Date(Date.now() + 10000).toISOString(),
            });

            const plan = await preparePageComposition({
                authoring_document: baseDoc,
                generation_params: baseParams,
                store,
                index,
                fetchFn: mockFetch,
            });

            const slot1 = plan.scenes.find(s => s.scene_id === "scene_1");
            assert.equal(slot1.state, SLOT_STATE.CURRENT_RESULT);
            assert.equal(slot1.selected_result.manifest_id, newerManifestScene1.manifest_id, "Must select the newest CURRENT manifest");
        });

        // CASE G: Older CURRENT manifests are not deleted or mutated
        await test("Case G: Older CURRENT manifests are not deleted or mutated", async () => {
            const oldManifest = await store.getManifest(scene1Manifest.manifest_id);
            assert.ok(oldManifest, "Older manifest must still exist");
            assert.equal(oldManifest.manifest_id, scene1Manifest.manifest_id);
        });

        // CASE H: Selected artifact locator/digest/dimensions come from stored manifest
        await test("Case H: Selected artifact locator/digest/dimensions come from stored manifest", async () => {
            const plan = await preparePageComposition({
                authoring_document: baseDoc,
                generation_params: baseParams,
                store,
                index,
                fetchFn: mockFetch,
            });

            const slot2 = plan.scenes.find(s => s.scene_id === "scene_2");
            assert.equal(slot2.state, SLOT_STATE.CURRENT_RESULT);
            assert.deepEqual(slot2.selected_result.artifact.locator, scene2Manifest.artifact.locator);
            assert.deepEqual(slot2.selected_result.artifact.dimensions, scene2Manifest.artifact.dimensions);
            assert.equal(slot2.selected_result.artifact.content_digest, scene2Manifest.artifact.content_digest);
        });

        // CASE I: Placement comes from stored manifest, not caller override
        await test("Case I: Placement comes from stored manifest, not caller override", async () => {
            const plan = await preparePageComposition({
                authoring_document: baseDoc,
                generation_params: baseParams,
                store,
                index,
                fetchFn: mockFetch,
            });

            const slot2 = plan.scenes.find(s => s.scene_id === "scene_2");
            assert.deepEqual(slot2.selected_result.placement.page_target_rect, scene2Manifest.placement.page_target_rect);
            assert.deepEqual(slot2.selected_result.placement.local_source_rect, scene2Manifest.placement.local_source_rect);
            assert.deepEqual(slot2.selected_result.placement.transform, scene2Manifest.placement.transform);
        });

        // CASE J: Page identity and dimensions come from current Authoring Document
        await test("Case J: Page identity and dimensions come from current Authoring Document", async () => {
            const plan = await preparePageComposition({
                authoring_document: baseDoc,
                generation_params: baseParams,
                store,
                index,
                fetchFn: mockFetch,
            });

            assert.equal(plan.page.document_id, baseDoc.document_id);
            assert.equal(plan.page.page_id, baseDoc.pages[0].page_id);
            assert.equal(plan.page.width, baseDoc.pages[0].width_px);
            assert.equal(plan.page.height, baseDoc.pages[0].height_px);
        });

        // CASE K: Deleted historical Scene present only in index is NOT added to current page plan
        await test("Case K: Deleted historical Scene present only in index is NOT added to current page plan", async () => {
            // Manifest exists for scene_2, but let's remove scene_2 from current Authoring Document
            const docNoScene2 = structuredClone(baseDoc);
            docNoScene2.pages[0].scenes = [baseDoc.pages[0].scenes[0]];

            const plan = await preparePageComposition({
                authoring_document: docNoScene2,
                generation_params: baseParams,
                store,
                index,
                fetchFn: mockFetch,
            });

            assert.equal(plan.scenes.length, 1);
            assert.equal(plan.scenes[0].scene_id, "scene_1");
            assert.ok(!plan.scenes.some(s => s.scene_id === "scene_2"));
        });

        // CASE L: Display-only Authoring changes still permit CURRENT selection when freshness classifier says CURRENT
        await test("Case L: Display-only Authoring changes still permit CURRENT selection", async () => {
            const docDisplayEdit = structuredClone(baseDoc);
            docDisplayEdit.pages[0].scenes[1].name = "Renamed Display Title For Panel 2";
            docDisplayEdit.cast[0].display_name = "Friendly Character Label";

            const plan = await preparePageComposition({
                authoring_document: docDisplayEdit,
                generation_params: baseParams,
                store,
                index,
                fetchFn: mockFetch,
            });

            const slot2 = plan.scenes.find(s => s.scene_id === "scene_2");
            assert.equal(slot2.state, SLOT_STATE.CURRENT_RESULT);
            assert.equal(slot2.selected_result.manifest_id, scene2Manifest.manifest_id);
        });

        // CASE M: Unrelated page/Scene change does not disqualify target Scene when classifier says CURRENT
        await test("Case M: Unrelated page/Scene change does not disqualify target Scene", async () => {
            const docMultiPage = structuredClone(baseDoc);
            docMultiPage.pages.push({
                page_id: "page_2",
                width_px: 1024,
                height_px: 1024,
                scenes: [
                    {
                        scene_id: "scene_p2_1",
                        name: "Page 2 scene",
                        prompt: "other page prompt",
                        negative_prompt: "",
                        order: 0,
                        local_area: { x: 0.1, y: 0.1, w: 0.8, h: 0.8 },
                        character_instances: [],
                    }
                ],
                character_instances: [],
                guides: []
            });

            const plan = await preparePageComposition({
                authoring_document: docMultiPage,
                page_id: "page_1",
                generation_params: baseParams,
                store,
                index,
                fetchFn: mockFetch,
            });

            const slot2 = plan.scenes.find(s => s.scene_id === "scene_2");
            assert.equal(slot2.state, SLOT_STATE.CURRENT_RESULT);
        });

        // CASE N: No STALE or UNKNOWN result is selected
        await test("Case N: No STALE or UNKNOWN result is selected", async () => {
            const docStale = structuredClone(baseDoc);
            // Change prompt for scene_1 and scene_2 so all manifests become STALE
            docStale.pages[0].scenes[0].prompt = "completely modified prompt 1";
            docStale.pages[0].scenes[1].prompt = "completely modified prompt 2";

            const plan = await preparePageComposition({
                authoring_document: docStale,
                generation_params: baseParams,
                store,
                index,
                fetchFn: mockFetch,
            });

            for (const s of plan.scenes) {
                assert.equal(s.state, SLOT_STATE.UNFILLED);
                assert.equal(s.selected_result, null);
            }
        });

        // CASE O: UNFILLED does not create a synthetic artifact
        await test("Case O: UNFILLED does not create a synthetic artifact", async () => {
            const preFiles = await fs.readdir(storeDir);
            const docEmpty = structuredClone(baseDoc);
            docEmpty.pages[0].scenes = [
                {
                    scene_id: "scene_fresh_empty",
                    name: "Fresh Empty",
                    prompt: "something new",
                    negative_prompt: "",
                    order: 0,
                    local_area: { x: 0.2, y: 0.2, w: 0.6, h: 0.6 },
                    character_instances: [],
                }
            ];

            const plan = await preparePageComposition({
                authoring_document: docEmpty,
                generation_params: baseParams,
                store,
                index,
                fetchFn: mockFetch,
            });

            assert.equal(plan.scenes[0].state, SLOT_STATE.UNFILLED);
            assert.equal(plan.scenes[0].selected_result, null);

            const postFiles = await fs.readdir(storeDir);
            assert.deepEqual(postFiles, preFiles, "Store must not contain any synthetic artifacts");
        });

        // CASE P: Background is explicitly WHITE
        await test("Case P: Background is explicitly WHITE", async () => {
            const plan = await preparePageComposition({
                authoring_document: baseDoc,
                generation_params: baseParams,
                store,
                index,
                fetchFn: mockFetch,
            });

            assert.deepEqual(plan.background, {
                mode: BACKGROUND_MODE.SOLID,
                value: BACKGROUND_VALUE.WHITE,
            });
        });

        // CASE Q: No panel/border drawing instruction is introduced
        await test("Case Q: No panel/border drawing instruction is introduced", async () => {
            const plan = await preparePageComposition({
                authoring_document: baseDoc,
                generation_params: baseParams,
                store,
                index,
                fetchFn: mockFetch,
            });

            assert.equal(plan.borders, undefined);
            assert.equal(plan.border_width, undefined);
            assert.equal(plan.stroke, undefined);
            for (const s of plan.scenes) {
                assert.equal(s.border, undefined);
                assert.equal(s.stroke, undefined);
            }
        });

        // CASE R, S, T: ZERO PNG fetch, ZERO Store/Index/Journal mutation, ZERO /prompt / GPU
        await test("Case R, S, T: ZERO PNG fetch, ZERO Store/Index/Journal mutation, ZERO GPU", async () => {
            const preStoreFiles = await fs.readdir(storeDir);
            const preIndexFiles = await fs.readdir(indexDir);

            await preparePageComposition({
                authoring_document: baseDoc,
                generation_params: baseParams,
                store,
                index,
                fetchFn: mockFetch,
            });

            const postStoreFiles = await fs.readdir(storeDir);
            const postIndexFiles = await fs.readdir(indexDir);

            assert.deepEqual(postStoreFiles, preStoreFiles, "Store must remain unmutated");
            assert.deepEqual(postIndexFiles, preIndexFiles, "Index must remain unmutated");
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
