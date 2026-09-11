/**
 * authoring_document.js — Standalone Domain Document Representation
 * =================================================================
 * TEGAKI Manga Authoring Workspace (M1A)
 * 
 * Strict parity with TEGAKI_AUTHORING_DOCUMENT 1.0.0 specification:
 * - Pure JavaScript, zero external dependencies, zero ComfyUI host glue.
 * - Enforces schema invariants without inventing new fields.
 * - Protects durable document JSON from session/UI pollution.
 */

export const SCHEMA_ID = "TEGAKI_AUTHORING_DOCUMENT";
export const SCHEMA_VERSION = "1.0.0";

export const RESOLUTION_PRESETS = {
    "Portrait 832x1216": { width: 832, height: 1216 },
    "Landscape 1216x832": { width: 1216, height: 832 },
    "Square 1024x1024": { width: 1024, height: 1024 }
};

export const STYLE_PRESETS = {
    "Manga Monochrome": {
        prompt: "manga page, monochrome, expressive linework, high contrast, screentone shading",
        negative: "bad anatomy, blurry, photo, color, 3d render, watermark, text"
    },
    "Manga Color": {
        prompt: "color manga page, rich vibrant digital watercolor and clean ink, anime aesthetic",
        negative: "bad anatomy, blurry, lowres, photo, realistic 3d, watermark, text"
    }
};

/**
 * Creates a default canonical TEGAKI_AUTHORING_DOCUMENT 1.0.0
 * Pixel and semantic parity with reference M3B implementation.
 */
export function createDefaultAuthoringDocument({
    resolution = "Portrait 832x1216",
    styleTemplate = "Manga Monochrome",
    seed = 42,
    documentId = null
} = {}) {
    const res = RESOLUTION_PRESETS[resolution] || { width: 832, height: 1216 };
    const style = STYLE_PRESETS[styleTemplate] || STYLE_PRESETS["Manga Monochrome"];

    return {
        schema_id: SCHEMA_ID,
        schema_version: SCHEMA_VERSION,
        document_id: documentId || ("doc_" + Math.random().toString(36).substring(2, 10)),
        pages: [
            {
                page_id: "page_1",
                order: 1,
                width_px: res.width,
                height_px: res.height,
                style_prompt: style.prompt,
                style_negative_prompt: style.negative,
                generation: {
                    seed: parseInt(seed, 10) || 42
                },
                metadata: {
                    style_template: styleTemplate
                },
                scenes: [
                    {
                        scene_id: "scene_top",
                        order: 1,
                        name: "Scene 1",
                        prompt: "school classroom, desks and chairs, a student reading quietly by the window, warm sunlight",
                        negative_prompt: "",
                        input_mode: "simple",
                        area: {
                            shape_type: "rect",
                            x: 0.08,
                            y: 0.06,
                            w: 0.84,
                            h: 0.42
                        },
                        metadata: {}
                    },
                    {
                        scene_id: "scene_bottom",
                        order: 2,
                        name: "Scene 2",
                        prompt: "outdoor train station platform, railway tracks, a commuter waiting with bicycle, afternoon sky",
                        negative_prompt: "",
                        input_mode: "simple",
                        area: {
                            shape_type: "rect",
                            x: 0.08,
                            y: 0.52,
                            w: 0.84,
                            h: 0.42
                        },
                        metadata: {}
                    }
                ],
                visual_frames: [],
                cast: [],
                character_instances: [],
                guides: []
            }
        ],
        metadata: {}
    };
}

/**
 * Creates a rich authoring fixture with all layers populated:
 * Scenes, Cast, Character Instances, Visual Frames, and Guides with Figure Regions.
 */
export function createRichAuthoringFixture() {
    return {
        schema_id: SCHEMA_ID,
        schema_version: SCHEMA_VERSION,
        document_id: "doc_rich_fixture_m1a",
        pages: [
            {
                page_id: "page_1",
                order: 1,
                width_px: 832,
                height_px: 1216,
                style_prompt: "manga page, monochrome, expressive linework, high contrast, screentone shading",
                style_negative_prompt: "bad anatomy, blurry, photo, color, 3d render, watermark, text",
                generation: {
                    seed: 1337
                },
                metadata: {
                    style_template: "Manga Monochrome"
                },
                scenes: [
                    {
                        scene_id: "scene_action_top",
                        order: 1,
                        name: "Top Action Scene",
                        prompt: "shonen action battle, dramatic wind, high angle view, intense expression",
                        negative_prompt: "",
                        input_mode: "detailed",
                        area: {
                            shape_type: "rect",
                            x: 0.06,
                            y: 0.05,
                            w: 0.88,
                            h: 0.44
                        },
                        metadata: {}
                    },
                    {
                        scene_id: "scene_reaction_bottom",
                        order: 2,
                        name: "Bottom Dialogue Scene",
                        prompt: "close-up dialogue, emotional realization, speedlines background",
                        negative_prompt: "",
                        input_mode: "simple",
                        area: {
                            shape_type: "rect",
                            x: 0.06,
                            y: 0.53,
                            w: 0.88,
                            h: 0.42
                        },
                        metadata: {}
                    }
                ],
                visual_frames: [
                    {
                        frame_id: "frame_1",
                        order: 1,
                        area: {
                            shape_type: "rect",
                            x: 0.06,
                            y: 0.05,
                            w: 0.88,
                            h: 0.44
                        },
                        border_thickness: 4,
                        border_color: "#000000",
                        metadata: {}
                    },
                    {
                        frame_id: "frame_2",
                        order: 2,
                        area: {
                            shape_type: "rect",
                            x: 0.06,
                            y: 0.53,
                            w: 0.88,
                            h: 0.42
                        },
                        border_thickness: 4,
                        border_color: "#000000",
                        metadata: {}
                    }
                ],
                cast: [
                    {
                        cast_id: "cast_ren",
                        display_name: "Ren",
                        identity_prompt: "young boy, messy black hair, dark eyes, dark jacket",
                        negative_prompt: "",
                        color: "#06b6d4",
                        loras: [],
                        metadata: {}
                    },
                    {
                        cast_id: "cast_sora",
                        display_name: "Sora",
                        identity_prompt: "tall youth, silver hair, sharp eyes, high-collar uniform",
                        negative_prompt: "",
                        color: "#eab308",
                        loras: [],
                        metadata: {}
                    }
                ],
                character_instances: [
                    {
                        instance_id: "inst_ren_1",
                        cast_id: "cast_ren",
                        scene_id: "scene_action_top",
                        area: {
                            shape_type: "rect",
                            x: 0.12,
                            y: 0.10,
                            w: 0.32,
                            h: 0.35
                        },
                        acting_prompt: "leaping forward, ready to strike",
                        negative_prompt_override: "",
                        order: 1,
                        metadata: {}
                    },
                    {
                        instance_id: "inst_sora_1",
                        cast_id: "cast_sora",
                        scene_id: "scene_action_top",
                        area: {
                            shape_type: "rect",
                            x: 0.54,
                            y: 0.12,
                            w: 0.34,
                            h: 0.34
                        },
                        acting_prompt: "defending with raised arm, smirk",
                        negative_prompt_override: "",
                        order: 2,
                        metadata: {}
                    }
                ],
                guides: [
                    {
                        guide_id: "guide_rough_1",
                        guide_type: "rough_manga",
                        asset_reference: "tegaki_manga_guides/rough_guide_fixture.png",
                        enabled: true,
                        placement: {
                            shape_type: "rect",
                            x: 0.06,
                            y: 0.05,
                            w: 0.88,
                            h: 0.44
                        },
                        figure_regions: [
                            {
                                figure_id: "fig_ren",
                                instance_id: "inst_ren_1",
                                area: {
                                    shape_type: "rect",
                                    x: 0.12,
                                    y: 0.10,
                                    w: 0.32,
                                    h: 0.35
                                },
                                metadata: {}
                            },
                            {
                                figure_id: "fig_sora",
                                instance_id: "inst_sora_1",
                                area: {
                                    shape_type: "rect",
                                    x: 0.54,
                                    y: 0.12,
                                    w: 0.34,
                                    h: 0.34
                                },
                                metadata: {}
                            }
                        ],
                        metadata: {}
                    }
                ]
            }
        ],
        metadata: {}
    };
}

/**
 * List of forbidden keys that belong exclusively to session/UI state
 * and must NEVER appear inside durable TEGAKI_AUTHORING_DOCUMENT.
 */
export const FORBIDDEN_SESSION_KEYS = [
    "activeTab",
    "activeLayer",
    "activeEditLayer",
    "selectedSceneId",
    "selectedSceneIndex",
    "selectedCastId",
    "selectedInstanceId",
    "selectedFrameId",
    "selectedFrameIndex",
    "selectedGuideId",
    "selectedGuideIndex",
    "selectedFigureId",
    "selectedFigureIndex",
    "viewport",
    "zoom",
    "panX",
    "panY",
    "isGenerating",
    "dragState",
    "ui"
];

/**
 * Validates a document against TEGAKI_AUTHORING_DOCUMENT 1.0.0 invariants.
 * Returns { valid: boolean, errors: string[] }
 */
export function validateAuthoringDocument(doc) {
    const errors = [];
    if (!doc || typeof doc !== "object") {
        return { valid: false, errors: ["Document must be an object"] };
    }

    if (doc.schema_id !== SCHEMA_ID) {
        errors.push(`Invalid schema_id: expected '${SCHEMA_ID}', got '${doc.schema_id}'`);
    }

    if (doc.schema_version !== SCHEMA_VERSION) {
        errors.push(`Invalid schema_version: expected '${SCHEMA_VERSION}', got '${doc.schema_version}'`);
    }

    if (!Array.isArray(doc.pages) || doc.pages.length === 0) {
        errors.push("Document must contain at least one page");
    } else {
        doc.pages.forEach((page, pIdx) => {
            const ctx = `pages[${pIdx}]`;
            if (typeof page.width_px !== "number" || page.width_px <= 0) {
                errors.push(`${ctx}.width_px must be a positive number`);
            }
            if (typeof page.height_px !== "number" || page.height_px <= 0) {
                errors.push(`${ctx}.height_px must be a positive number`);
            }
            if (!Array.isArray(page.scenes)) {
                errors.push(`${ctx}.scenes must be an array`);
            }
            if (!Array.isArray(page.visual_frames)) {
                errors.push(`${ctx}.visual_frames must be an array`);
            }
            if (!Array.isArray(page.cast)) {
                errors.push(`${ctx}.cast must be an array`);
            }
            if (!Array.isArray(page.character_instances)) {
                errors.push(`${ctx}.character_instances must be an array`);
            }
            if (!Array.isArray(page.guides)) {
                errors.push(`${ctx}.guides must be an array`);
            }
        });
    }

    // Check for forbidden session keys
    function scanForSessionKeys(obj, path = "") {
        if (!obj || typeof obj !== "object") return;
        for (const key of Object.keys(obj)) {
            const curPath = path ? `${path}.${key}` : key;
            if (FORBIDDEN_SESSION_KEYS.includes(key)) {
                errors.push(`Session state leakage detected in document: '${curPath}'`);
            }
            if (typeof obj[key] === "object" && obj[key] !== null) {
                scanForSessionKeys(obj[key], curPath);
            }
        }
    }
    scanForSessionKeys(doc);

    return {
        valid: errors.length === 0,
        errors
    };
}

/**
 * Deep clones an authoring document without modifying anything.
 */
export function cloneDocument(doc) {
    return JSON.parse(JSON.stringify(doc));
}
