/**
 * page_compositor_prep.mjs — Ephemeral Page Composition Plan Preparation Service.
 *
 * Prepares a deterministic, server-derived composition plan for ONE Authoring Page
 * by querying indexed Scene Result history, classifying candidates against CURRENT
 * canonical effective inputs, selecting at most ONE CURRENT result per Scene,
 * and assembling validated placement operations without pixel compositing.
 */

import { randomUUID } from "node:crypto";
import { SceneResultStore } from "./scene_result_store.mjs";
import { SceneResultIndex } from "./scene_result_index.mjs";
import {
    classifySceneResultFreshness,
    FRESHNESS_STATUS,
} from "./scene_result_freshness.mjs";

export const SCHEMA_ID = "TEGAKI_PAGE_COMPOSITION_PLAN";
export const SCHEMA_VERSION = "1.0.0";

export const SLOT_STATE = Object.freeze({
    CURRENT_RESULT: "CURRENT_RESULT",
    UNFILLED: "UNFILLED",
});

export const BACKGROUND_MODE = Object.freeze({
    SOLID: "solid",
});

export const BACKGROUND_VALUE = Object.freeze({
    WHITE: "white",
});

export class PageCompositorPrepError extends Error {
    constructor(code, message, options = {}) {
        super(message, options);
        this.name = "PageCompositorPrepError";
        this.code = code;
    }
}

function isObject(val) {
    return val !== null && typeof val === "object" && !Array.isArray(val);
}

function isNonEmptyString(val) {
    return typeof val === "string" && val.trim().length > 0;
}

function isPositiveInteger(val) {
    return typeof val === "number" && Number.isInteger(val) && val > 0;
}

/**
 * Resolves exactly one page from the Authoring Document based on page_id or page_index.
 *
 * @param {object} authoringDocument
 * @param {string|null} pageId
 * @param {number|null} pageIndex
 * @returns {{ page: object, index: number }}
 */
function resolveAuthoringPage(authoringDocument, pageId, pageIndex) {
    if (!isObject(authoringDocument)) {
        throw new PageCompositorPrepError("INVALID_DOCUMENT", "authoring_document must be a non-null object");
    }
    if (!isNonEmptyString(authoringDocument.document_id)) {
        throw new PageCompositorPrepError("INVALID_DOCUMENT", "authoring_document must declare a non-empty document_id");
    }
    if (!Array.isArray(authoringDocument.pages) || authoringDocument.pages.length === 0) {
        throw new PageCompositorPrepError("EMPTY_PAGES", "authoring_document must contain at least one page");
    }

    const pages = authoringDocument.pages;

    let resolvedByIndex = null;
    if (pageIndex !== null && pageIndex !== undefined) {
        if (!Number.isInteger(pageIndex) || pageIndex < 0 || pageIndex >= pages.length) {
            throw new PageCompositorPrepError("PAGE_INDEX_OUT_OF_BOUNDS", `page_index ${pageIndex} is out of bounds (0..${pages.length - 1})`);
        }
        resolvedByIndex = { page: pages[pageIndex], index: pageIndex };
    }

    let resolvedById = null;
    if (pageId !== null && pageId !== undefined) {
        if (!isNonEmptyString(pageId)) {
            throw new PageCompositorPrepError("INVALID_PAGE_ID", "page_id must be a non-empty string");
        }
        const trimmedId = pageId.trim();
        const foundIdx = pages.findIndex(p => p.page_id === trimmedId);
        if (foundIdx === -1) {
            throw new PageCompositorPrepError("PAGE_NOT_FOUND", `Page "${trimmedId}" was not found in Authoring Document`);
        }
        resolvedById = { page: pages[foundIdx], index: foundIdx };
    }

    if (resolvedByIndex && resolvedById) {
        if (resolvedByIndex.index !== resolvedById.index || resolvedByIndex.page.page_id !== resolvedById.page.page_id) {
            throw new PageCompositorPrepError(
                "PAGE_RESOLUTION_MISMATCH",
                `page_id "${pageId}" (index ${resolvedById.index}) does not match page_index ${pageIndex} (page_id "${resolvedByIndex.page.page_id}")`
            );
        }
        return resolvedById;
    }

    if (resolvedById) return resolvedById;
    if (resolvedByIndex) return resolvedByIndex;

    // Default to the first page (index 0)
    return { page: pages[0], index: 0 };
}

/**
 * Checks if two normalized rectangles [0, 1] overlap with positive area.
 */
function rectsOverlap(r1, r2) {
    const EPS = 0.0001;
    return (
        r1.x < r2.x + r2.w - EPS &&
        r1.x + r1.w > r2.x + EPS &&
        r1.y < r2.y + r2.h - EPS &&
        r1.y + r1.h > r2.y + EPS
    );
}

/**
 * Prepares an ephemeral Page Composition Plan for a single Authoring Page.
 *
 * @param {object} params
 * @param {object} params.authoring_document - Current Authoring Document JSON.
 * @param {string} [params.page_id] - Optional target page ID.
 * @param {number} [params.page_index] - Optional target page index.
 * @param {object} params.generation_params - Current generation parameters for freshness evaluation.
 * @param {SceneResultStore} [params.store] - Store instance (injectable).
 * @param {SceneResultIndex} [params.index] - Index instance (injectable).
 * @param {string} [params.backendUrl] - Manga backend URL.
 * @param {typeof fetch} [params.fetchFn] - Injectable fetch for canonical compile.
 * @param {Function} [params.classifyFn] - Injectable freshness classifier function.
 * @returns {Promise<object>} Ephemeral TEGAKI_PAGE_COMPOSITION_PLAN
 */
export async function preparePageComposition({
    authoring_document,
    page_id = null,
    page_index = null,
    generation_params,
    store = null,
    index = null,
    backendUrl = "http://127.0.0.1:8189",
    fetchFn = fetch,
    classifyFn = null,
} = {}) {
    // 1. Resolve target page
    const { page: targetPage } = resolveAuthoringPage(authoring_document, page_id, page_index);

    if (!isNonEmptyString(targetPage.page_id)) {
        throw new PageCompositorPrepError("INVALID_PAGE", "Resolved page lacks a valid page_id");
    }

    const pageWidth = targetPage.width_px || targetPage.width;
    const pageHeight = targetPage.height_px || targetPage.height;

    if (!isPositiveInteger(pageWidth) || !isPositiveInteger(pageHeight)) {
        throw new PageCompositorPrepError(
            "INVALID_PAGE_DIMENSIONS",
            `Resolved page dimensions must be positive integers, got width=${pageWidth}, height=${pageHeight}`
        );
    }

    if (!isObject(generation_params)) {
        throw new PageCompositorPrepError("INVALID_GENERATION_PARAMS", "generation_params must be a non-null object");
    }

    // 2. Setup stores and index
    const resultStore = store || new SceneResultStore();
    const resultIndex = index || new SceneResultIndex({ store: resultStore });
    const classifier = classifyFn || classifySceneResultFreshness;

    // 3. Enumerate current page Scenes in structural order
    const pageScenes = Array.isArray(targetPage.scenes) ? targetPage.scenes : [];
    const compositionSlots = [];
    const selectedRects = [];

    for (let slotIndex = 0; slotIndex < pageScenes.length; slotIndex++) {
        const scene = pageScenes[slotIndex];
        if (!isObject(scene) || !isNonEmptyString(scene.scene_id)) {
            throw new PageCompositorPrepError("INVALID_SCENE", `Page scene at index ${slotIndex} lacks a valid scene_id`);
        }

        const sceneId = scene.scene_id.trim();
        const structuralOrder = Number.isInteger(scene.order) ? scene.order : slotIndex;

        // Query indexed history for this scene
        const historyCandidates = await resultIndex.listByScene({
            document_id: authoring_document.document_id,
            page_id: targetPage.page_id,
            scene_id: sceneId,
            loadManifests: true,
        });

        let selectedManifest = null;
        let evaluatedCount = 0;

        // Deterministic candidate evaluation: index ordering is created_at desc, manifest_id desc
        for (const candidate of historyCandidates) {
            evaluatedCount++;
            const candidateManifest = candidate.manifest;
            if (!candidateManifest) continue;

            const freshness = await classifier({
                manifest_id: candidate.manifest_id,
                _manifest: candidateManifest,
                authoring_document,
                generation_params,
                store: resultStore,
                backendUrl,
                fetchFn,
                page_id: targetPage.page_id,
            });

            if (freshness.status === FRESHNESS_STATUS.CURRENT) {
                selectedManifest = candidateManifest;
                break; // Deterministic policy: select the first (newest) CURRENT result
            }
        }

        if (selectedManifest) {
            // Validate manifest placement facts
            const placement = selectedManifest.placement;
            if (!isObject(placement) || !isObject(placement.page_target_rect) || !isObject(placement.local_source_rect) || !isObject(placement.transform)) {
                throw new PageCompositorPrepError(
                    "CORRUPT_MANIFEST_PLACEMENT",
                    `Selected manifest ${selectedManifest.manifest_id} has invalid placement structure`
                );
            }

            const slotResult = {
                manifest_id: selectedManifest.manifest_id,
                artifact: {
                    locator: structuredClone(selectedManifest.artifact.locator),
                    dimensions: structuredClone(selectedManifest.artifact.dimensions),
                    content_digest: selectedManifest.artifact.content_digest,
                },
                placement: {
                    page_target_rect: structuredClone(placement.page_target_rect),
                    local_source_rect: structuredClone(placement.local_source_rect),
                    transform: structuredClone(placement.transform),
                    target_page_dimensions: structuredClone(placement.target_page_dimensions || {
                        width: pageWidth,
                        height: pageHeight,
                    }),
                },
            };

            compositionSlots.push({
                scene_id: sceneId,
                order: structuralOrder,
                state: SLOT_STATE.CURRENT_RESULT,
                selected_result: slotResult,
                diagnostics: {
                    evaluated_candidates: evaluatedCount,
                    total_indexed_candidates: historyCandidates.length,
                },
            });

            selectedRects.push({
                scene_id: sceneId,
                rect: placement.page_target_rect,
            });
        } else {
            // UNFILLED slot
            compositionSlots.push({
                scene_id: sceneId,
                order: structuralOrder,
                state: SLOT_STATE.UNFILLED,
                selected_result: null,
                diagnostics: {
                    evaluated_candidates: evaluatedCount,
                    total_indexed_candidates: historyCandidates.length,
                },
            });
        }
    }

    // Pairwise overlap check for diagnostics
    const overlappingPairs = [];
    for (let i = 0; i < selectedRects.length; i++) {
        for (let j = i + 1; j < selectedRects.length; j++) {
            if (rectsOverlap(selectedRects[i].rect, selectedRects[j].rect)) {
                overlappingPairs.push([selectedRects[i].scene_id, selectedRects[j].scene_id]);
            }
        }
    }

    return {
        schema_id: SCHEMA_ID,
        schema_version: SCHEMA_VERSION,
        plan_id: randomUUID(),
        created_at: new Date().toISOString(),
        page: {
            document_id: authoring_document.document_id,
            page_id: targetPage.page_id,
            width: pageWidth,
            height: pageHeight,
        },
        background: {
            mode: BACKGROUND_MODE.SOLID,
            value: BACKGROUND_VALUE.WHITE,
        },
        scenes: compositionSlots,
        diagnostics: {
            total_scenes: compositionSlots.length,
            filled_scenes: compositionSlots.filter(s => s.state === SLOT_STATE.CURRENT_RESULT).length,
            unfilled_scenes: compositionSlots.filter(s => s.state === SLOT_STATE.UNFILLED).length,
            has_overlapping_scenes: overlappingPairs.length > 0,
            overlapping_scene_pairs: overlappingPairs,
        },
    };
}
