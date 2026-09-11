/**
 * minimum_hand_scene_editor.js — Minimum-Hand Manga Authoring (Draft) Product UI (M2B)
 * ======================================================================================
 * Product-facing unified authoring canvas and inspector for:
 * - GLOBAL: Resolution, Style, Seed + [Randomize Seed]
 * - CAST: CAST Master Registration (Name, Identity Prompt, Negative Prompt), Delete Protection
 * - CANVAS: Scene Regions + Character Rough Regions with Visual Hierarchy & Direct Manipulation
 * - SCENE: Scene Label, Scene Prompt (Common Context), Character Presence, Warning Badges (3+, 4+)
 * - CHARACTER: Free-Text Acting Prompt, Direct Drag/Resize within Scene, Remove Character
 * - CONTRACT PARITY: Scene Move carries child instances; Scene Resize scales child instances.
 * 
 * Strict SSOT: TEGAKI_AUTHORING_DOCUMENT in document_json widget.
 */
import { app } from "../../../scripts/app.js";
import { api } from "../../../scripts/api.js";
import {
    chooseCastForPlacement,
    getNextInstanceId,
    calculateNewInstanceGeometry,
    onInstanceRemoved,
    canDeleteCast,
    cascadeDeleteScene,
    moveSceneWithChildren,
    clampCharacterDrag,
    getNextFrameId,
    calculateNewFrameGeometry,
    copyFramesFromScenes,
    clampFrameDrag,
    resizeFrame,
    checkFrameOverlap,
    getNextGuideId,
    calculateContainPlacement,
    clampGuideFigureDrag,
    resizeGuideFigure,
    createGuideFigure,
    associateGuideFigure,
    unassignGuideInstance
} from "./minimum_hand_authoring_ops.js";
import {
    previewGenerationRoute,
    ROUTE_STANDARD,
    ROUTE_GUIDED,
    ROUTE_LABELS
} from "./minimum_hand_generation_route.js";

const SCENE_PALETTE = [
    { name: "Scene 1", hex: "#e53935", rgb: [229, 57, 53] },
    { name: "Scene 2", hex: "#1e88e5", rgb: [30, 136, 229] },
    { name: "Scene 3", hex: "#43a047", rgb: [67, 160, 71] },
    { name: "Scene 4", hex: "#fb8c00", rgb: [251, 140, 0] },
    { name: "Scene 5", hex: "#8e24aa", rgb: [142, 36, 170] },
    { name: "Scene 6", hex: "#00acc1", rgb: [0, 172, 193] },
];

const CAST_PALETTE = [
    { name: "Cast 1", hex: "#06b6d4", rgb: [6, 182, 212] },
    { name: "Cast 2", hex: "#eab308", rgb: [234, 179, 8] },
    { name: "Cast 3", hex: "#ec4899", rgb: [236, 72, 153] },
    { name: "Cast 4", hex: "#a855f7", rgb: [168, 85, 247] },
    { name: "Cast 5", hex: "#22c55e", rgb: [34, 197, 94] },
    { name: "Cast 6", hex: "#f97316", rgb: [249, 115, 22] },
];

const RESOLUTION_MAP = {
    "Portrait 832x1216": { width: 832, height: 1216 },
    "Landscape 1216x832": { width: 1216, height: 832 },
    "Square 1024x1024": { width: 1024, height: 1024 },
};

const STYLE_PRESETS = {
    "Manga Monochrome": {
        prompt: "manga page, monochrome, expressive linework, high contrast, screentone shading",
        negative: "bad anatomy, blurry, photo, color, 3d render, watermark, text"
    },
    "Manga Color": {
        prompt: "color manga page, rich vibrant digital watercolor and clean ink, anime aesthetic",
        negative: "bad anatomy, blurry, lowres, photo, realistic 3d, watermark, text"
    }
};

function parseResolution(resStr) {
    if (RESOLUTION_MAP[resStr]) return RESOLUTION_MAP[resStr];
    if (resStr && resStr.includes("x")) {
        const parts = resStr.split(" ")[0].split("x");
        const w = parseInt(parts[0], 10);
        const h = parseInt(parts[1], 10);
        if (w > 0 && h > 0) return { width: w, height: h };
    }
    return { width: 832, height: 1216 };
}

function createDefaultDoc(resolutionStr = "Portrait 832x1216", styleTemplate = "Manga Monochrome", seed = 42) {
    const res = parseResolution(resolutionStr);
    const tmpl = STYLE_PRESETS[styleTemplate] || STYLE_PRESETS["Manga Monochrome"];
    return {
        schema_id: "TEGAKI_AUTHORING_DOCUMENT",
        schema_version: "1.0.0",
        document_id: "doc_" + Math.random().toString(36).substring(2, 10),
        pages: [
            {
                page_id: "page_1",
                order: 1,
                width_px: res.width,
                height_px: res.height,
                style_prompt: tmpl.prompt,
                style_negative_prompt: tmpl.negative,
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

app.registerExtension({
    name: "Tegaki.MinimumHandSceneEditor",
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name !== "TegakiMinimumHandSceneEditor") return;

        const onConfigure = nodeType.prototype.onConfigure;
        nodeType.prototype.onConfigure = function (info) {
            const r = onConfigure ? onConfigure.apply(this, arguments) : undefined;
            const docWidget = this.widgets?.find(w => w.name === "document_json");
            if (docWidget) {
                docWidget.type = "hidden";
                docWidget.computeSize = () => [0, -4];
            }
            if (this._tegakiRestoreFromWidgets) {
                this._tegakiRestoreFromWidgets();
            }
            return r;
        };

        const onNodeCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function () {
            const r = onNodeCreated ? onNodeCreated.apply(this, arguments) : undefined;

            const node = this;
            node.setSize([560, 960]);

            // Hide raw document_json widget from primary surface (Root Cause C fix)
            const docWidget = node.widgets?.find(w => w.name === "document_json");
            if (docWidget) {
                docWidget.type = "hidden";
                docWidget.computeSize = () => [0, -4];
            }

            let doc = createDefaultDoc();
            let activeEditLayer = "scene"; // 'scene' | 'frame' | 'character' | 'guide'
            let selectedSceneIndex = 0;
            let selectedFrameIndex = -1;
            let selectedInstanceId = null;
            let selectedGuideIndex = -1;
            let selectedFigureIndex = -1;
            let selectedCastId = null;

            // Drag state
            let isDragging = false;
            let dragTarget = "none"; // 'scene' | 'character' | 'frame' | 'guide'
            let dragMode = "none";   // 'move' | 'nw' | 'ne' | 'se' | 'sw'
            let dragStartX = 0;
            let dragStartY = 0;
            let dragStartSceneArea = null;
            let dragStartInstArea = null;
            let dragStartFrameArea = null;
            let dragStartGuideFigureArea = null;
            let dragStartChildAreas = []; // [{ id, area }]

            function getPage() {
                if (!doc.pages || doc.pages.length === 0) {
                    doc = createDefaultDoc();
                }
                return doc.pages[0];
            }

            function getScenes() {
                const p = getPage();
                if (!p.scenes) p.scenes = [];
                return p.scenes;
            }

            function getVisualFrames() {
                const p = getPage();
                if (!p.visual_frames) p.visual_frames = [];
                return p.visual_frames;
            }

            function getCast() {
                const p = getPage();
                if (!p.cast) p.cast = [];
                return p.cast;
            }

            function getCharacterInstances() {
                const p = getPage();
                if (!p.character_instances) p.character_instances = [];
                return p.character_instances;
            }

            function getGuides() {
                const p = getPage();
                if (!p.guides) p.guides = [];
                return p.guides;
            }

            function getCastColor(castId) {
                const castList = getCast();
                const idx = castList.findIndex(c => c.cast_id === castId);
                if (idx === -1) return CAST_PALETTE[0];
                return CAST_PALETTE[idx % CAST_PALETTE.length];
            }

            function getSceneColor(idx) {
                return SCENE_PALETTE[idx % SCENE_PALETTE.length];
            }

            // DOM Container
            const container = document.createElement("div");
            container.style.cssText = `
                display: flex;
                flex-direction: column;
                gap: 8px;
                background: #18181b;
                color: #f4f4f5;
                padding: 10px;
                border-radius: 8px;
                font-family: system-ui, -apple-system, sans-serif;
                font-size: 12px;
                box-sizing: border-box;
                width: 100%;
                user-select: none;
            `;

            // Top Header
            const header = document.createElement("div");
            header.style.cssText = "display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #3f3f46; padding-bottom: 6px;";
            header.innerHTML = `
                <div style="font-weight: 600; font-size: 13px; display: flex; align-items: center; gap: 6px;">
                    <span style="background: #3b82f6; color: #fff; padding: 2px 6px; border-radius: 4px; font-size: 10px; font-weight: 700;">DRAFT</span>
                    <span>Tegaki Minimum-Hand Manga Authoring</span>
                </div>
                <div style="display: flex; align-items: center; gap: 8px;">
                    <button id="btn-random-seed" title="Randomize seed for rapid brainstorming" style="
                        background: #27272a;
                        color: #fafafa;
                        border: 1px solid #3f3f46;
                        border-radius: 4px;
                        padding: 3px 8px;
                        font-size: 11px;
                        font-weight: 600;
                        cursor: pointer;
                    ">🎲 Randomize Seed</button>
                    <div id="scene-counter" style="color: #a1a1aa; font-size: 11px;">Scenes: 2 / 6</div>
                </div>
            `;
            container.appendChild(header);

            // Wire Randomize Seed
            const btnRandomSeed = header.querySelector("#btn-random-seed");
            btnRandomSeed.onclick = (e) => {
                e.preventDefault();
                const newSeed = Math.floor(Math.random() * 2147483647);
                const page = getPage();
                if (!page.generation) page.generation = {};
                page.generation.seed = newSeed;
                const seedWidget = node.widgets.find(w => w.name === "seed");
                if (seedWidget) {
                    seedWidget.value = newSeed;
                }
                syncToWidgets();
            };

            // Product Generation Control Bar (M3B-PI2)
            const productGenBar = document.createElement("div");
            productGenBar.style.cssText = `
                display: flex;
                justify-content: space-between;
                align-items: center;
                background: #202024;
                padding: 6px 10px;
                border-radius: 6px;
                border: 1px solid #2f2f35;
                gap: 8px;
            `;
            productGenBar.innerHTML = `
                <div style="display: flex; align-items: center; gap: 8px; flex-shrink: 0;">
                    <button id="btn-generate-draft" title="Execute Minimum-Hand Draft generation with automatic route selection" style="
                        background: #2563eb;
                        color: #ffffff;
                        border: 1px solid #3b82f6;
                        border-radius: 4px;
                        padding: 4px 12px;
                        font-size: 11px;
                        font-weight: 700;
                        cursor: pointer;
                        display: flex;
                        align-items: center;
                        gap: 4px;
                    ">✨ Generate Draft</button>
                    <span id="route-badge" style="
                        background: #3f3f46;
                        color: #d4d4d8;
                        padding: 2px 8px;
                        border-radius: 4px;
                        font-size: 11px;
                        font-weight: 600;
                        border: 1px solid #52525b;
                        white-space: nowrap;
                    ">Generation: Standard</span>
                </div>
                <div id="generate-feedback" style="
                    font-size: 11px;
                    color: #a1a1aa;
                    overflow: hidden;
                    text-overflow: ellipsis;
                    white-space: nowrap;
                    text-align: right;
                "></div>
            `;
            container.appendChild(productGenBar);

            const btnGenerateDraft = productGenBar.querySelector("#btn-generate-draft");
            const routeBadge = productGenBar.querySelector("#route-badge");
            const generateFeedback = productGenBar.querySelector("#generate-feedback");

            function updateRouteBadge() {
                if (!routeBadge) return;
                const routeInfo = previewGenerationRoute(doc, 0);
                routeBadge.textContent = routeInfo.displayLabel;
                if (routeInfo.route === ROUTE_GUIDED) {
                    routeBadge.style.background = "#15803d";
                    routeBadge.style.color = "#dcfce7";
                    routeBadge.style.border = "1px solid #16a34a";
                } else {
                    routeBadge.style.background = "#3f3f46";
                    routeBadge.style.color = "#d4d4d8";
                    routeBadge.style.border = "1px solid #52525b";
                }
                routeBadge.title = routeInfo.reason;
            }

            let isGenerating = false;
            btnGenerateDraft.onclick = async (e) => {
                e.preventDefault();
                if (isGenerating) return;
                isGenerating = true;

                btnGenerateDraft.disabled = true;
                btnGenerateDraft.style.opacity = "0.5";
                btnGenerateDraft.style.cursor = "not-allowed";
                btnGenerateDraft.textContent = "⏳ Preparing...";
                generateFeedback.textContent = "";
                generateFeedback.style.color = "#a1a1aa";

                try {
                    syncToWidgets();
                    const page = getPage();
                    const seedWidget = node.widgets?.find(w => w.name === "seed");
                    const seedVal = seedWidget ? seedWidget.value : (page.generation?.seed ?? 42);

                    const resp = await api.fetchApi("/tegaki/manga/generation/prepare", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({
                            document_json: doc,
                            page_index: 0,
                            seed: seedVal
                        })
                    });

                    const data = await resp.json();
                    if (!resp.ok || !data.ok) {
                        const errMsg = data.error || `Preparation failed (${resp.status})`;
                        generateFeedback.textContent = `❌ ${errMsg}`;
                        generateFeedback.style.color = "#ef4444";
                        generateFeedback.title = errMsg;
                        return;
                    }

                    btnGenerateDraft.textContent = "⏳ Queueing...";
                    const promptGraph = data.prompt;
                    await api.queuePrompt(0, {
                        output: promptGraph,
                        workflow: app?.graph?.serialize ? app.graph.serialize() : undefined
                    });

                    const routeLabel = data.route === ROUTE_GUIDED ? "Guide-assisted" : "Standard";
                    generateFeedback.textContent = `✅ Queued · ${routeLabel}`;
                    generateFeedback.style.color = "#22c55e";
                    generateFeedback.title = `Prompt queued with route: ${data.route}`;
                } catch (err) {
                    console.error("[Tegaki Generate Draft]", err);
                    generateFeedback.textContent = `❌ ${err.message || String(err)}`;
                    generateFeedback.style.color = "#ef4444";
                    generateFeedback.title = err.message || String(err);
                } finally {
                    isGenerating = false;
                    btnGenerateDraft.disabled = false;
                    btnGenerateDraft.style.opacity = "1.0";
                    btnGenerateDraft.style.cursor = "pointer";
                    btnGenerateDraft.textContent = "✨ Generate Draft";
                }
            };
            updateRouteBadge();

            // CAST Section Bar
            const castSection = document.createElement("div");
            castSection.style.cssText = `
                display: flex;
                flex-direction: column;
                gap: 6px;
                background: #202024;
                padding: 8px;
                border-radius: 6px;
                border: 1px solid #2f2f35;
            `;

            const castHeader = document.createElement("div");
            castHeader.style.cssText = "display: flex; justify-content: space-between; align-items: center;";
            castHeader.innerHTML = `
                <div style="font-weight: 600; font-size: 11px; color: #a1a1aa; display: flex; align-items: center; gap: 4px;">
                    <span>CAST MASTER (RECURRENT CHARACTERS)</span>
                </div>
            `;
            castSection.appendChild(castHeader);

            const castChipsRow = document.createElement("div");
            castChipsRow.style.cssText = "display: flex; gap: 6px; align-items: center; flex-wrap: wrap;";
            castSection.appendChild(castChipsRow);

            const castInspector = document.createElement("div");
            castInspector.style.cssText = `
                display: none;
                flex-direction: column;
                gap: 6px;
                background: #18181b;
                padding: 8px;
                border-radius: 4px;
                border: 1px solid #3f3f46;
                margin-top: 4px;
            `;
            castSection.appendChild(castInspector);

            container.appendChild(castSection);

            // Canvas wrapper
            const canvasWrapper = document.createElement("div");
            canvasWrapper.style.cssText = "display: flex; justify-content: center; background: #09090b; padding: 8px; border-radius: 6px; border: 1px solid #27272a;";

            const canvas = document.createElement("canvas");
            canvas.width = 300;
            canvas.height = 438;
            canvas.style.cssText = "background: #ffffff; border: 1px solid #3f3f46; border-radius: 4px; cursor: crosshair;";
            canvasWrapper.appendChild(canvas);
            container.appendChild(canvasWrapper);

            const ctx = canvas.getContext("2d");

            // Layer Selector Bar: [Scene] | [Frame] | [Character]
            const layerSelectorBar = document.createElement("div");
            layerSelectorBar.style.cssText = `
                display: flex;
                align-items: center;
                gap: 6px;
                background: #202024;
                padding: 6px 8px;
                border-radius: 6px;
                border: 1px solid #333338;
            `;
            layerSelectorBar.innerHTML = `<span style="font-weight: 700; font-size: 11px; color: #a1a1aa; margin-right: 4px;">EDIT LAYER:</span>`;

            const layerButtons = {};
            const layers = [
                { id: "scene", label: "Scene Regions", desc: "Edit semantic story regions & regional prompts" },
                { id: "frame", label: "Visual Panel Frames", desc: "Edit visible manga comic panel borders (overlay / layout)" },
                { id: "character", label: "Character Staging", desc: "Edit character instance placement & acting within scenes" },
                { id: "guide", label: "Rough Guide", desc: "Upload and manually mark a page-owned rough manga guide" }
            ];

            layers.forEach(l => {
                const btn = document.createElement("button");
                btn.textContent = l.label;
                btn.title = l.desc;
                btn.style.cssText = `
                    background: ${activeEditLayer === l.id ? "#3b82f6" : "#27272a"};
                    color: ${activeEditLayer === l.id ? "#ffffff" : "#d4d4d8"};
                    border: 1px solid ${activeEditLayer === l.id ? "#60a5fa" : "#3f3f46"};
                    border-radius: 4px;
                    padding: 3px 10px;
                    font-size: 11px;
                    font-weight: 600;
                    cursor: pointer;
                    transition: all 0.15s;
                `;
                btn.onclick = (e) => {
                    e.preventDefault();
                    activeEditLayer = l.id;
                    updateLayerButtons();
                    renderInspector();
                    renderCanvas();
                };
                layerButtons[l.id] = btn;
                layerSelectorBar.appendChild(btn);
            });

            function updateLayerButtons() {
                layers.forEach(l => {
                    const btn = layerButtons[l.id];
                    if (!btn) return;
                    const isActive = activeEditLayer === l.id;
                    btn.style.background = isActive ? "#3b82f6" : "#27272a";
                    btn.style.color = isActive ? "#ffffff" : "#d4d4d8";
                    btn.style.borderColor = isActive ? "#60a5fa" : "#3f3f46";
                });
            }
            container.appendChild(layerSelectorBar);

            // Toolbar for Scene Management
            const toolbar = document.createElement("div");
            toolbar.style.cssText = "display: flex; gap: 6px; align-items: center; flex-wrap: wrap;";

            function createButton(text, title, onClick, bgColor = "#27272a") {
                const btn = document.createElement("button");
                btn.textContent = text;
                btn.title = title;
                btn.style.cssText = `
                    background: ${bgColor};
                    color: #fafafa;
                    border: 1px solid #3f3f46;
                    border-radius: 4px;
                    padding: 4px 10px;
                    font-size: 11px;
                    font-weight: 500;
                    cursor: pointer;
                    transition: background 0.15s;
                `;
                btn.onmouseenter = () => btn.style.background = "#3f3f46";
                btn.onmouseleave = () => btn.style.background = bgColor;
                btn.onclick = (e) => {
                    e.preventDefault();
                    onClick();
                };
                return btn;
            }

            const btnAddScene = createButton("+ Add Scene", "Add a new scene rectangle (max 6)", () => {
                const scenes = getScenes();
                if (scenes.length >= 6) return;

                let nextNum = 1;
                const existingNums = scenes.map(s => {
                    const m = s.scene_id && s.scene_id.match(/scene_(\d+)/);
                    return m ? parseInt(m[1], 10) : 0;
                });
                if (existingNums.length > 0) {
                    nextNum = Math.max(...existingNums, 0) + 1;
                }
                let newId = `scene_${nextNum}`;
                while (scenes.some(s => s.scene_id === newId)) {
                    nextNum++;
                    newId = `scene_${nextNum}`;
                }

                const yOffset = 0.06 + ((scenes.length % 3) * 0.30);
                const orderNum = scenes.length + 1;
                scenes.push({
                    scene_id: newId,
                    order: orderNum,
                    name: `Scene ${orderNum}`,
                    prompt: `scene ${orderNum} context prompt`,
                    negative_prompt: "",
                    input_mode: "simple",
                    area: {
                        shape_type: "rect",
                        x: 0.08,
                        y: Math.min(0.70, yOffset),
                        w: 0.84,
                        h: 0.25
                    },
                    metadata: {}
                });
                selectedSceneIndex = scenes.length - 1;
                selectedInstanceId = null;
                syncToWidgets();
                renderAll();
            });

            const btnDeleteScene = createButton("- Remove Scene", "Remove selected scene and its characters", () => {
                const scenes = getScenes();
                if (scenes.length <= 1) return;
                const deadScene = scenes[selectedSceneIndex];
                if (deadScene) {
                    const p = getPage();
                    const res = cascadeDeleteScene(deadScene.scene_id, p.scenes, p.character_instances || []);
                    p.scenes = res.scenes;
                    p.character_instances = res.instances;
                }
                if (selectedSceneIndex >= getScenes().length) {
                    selectedSceneIndex = getScenes().length - 1;
                }
                selectedInstanceId = null;
                syncToWidgets();
                renderAll();
            });

            const btnResetLayout = createButton("Reset Draft", "Reset document to default 2-scene layout", () => {
                const ok = confirm("Reset Draft will reset the entire document to default 2 scenes and clear all CAST and character instances. Proceed?");
                if (!ok) return;

                const resWidget = node.widgets.find(w => w.name === "resolution");
                const styleWidget = node.widgets.find(w => w.name === "style_template");
                const seedWidget = node.widgets.find(w => w.name === "seed");
                doc = createDefaultDoc(
                    resWidget ? resWidget.value : "Portrait 832x1216",
                    styleWidget ? styleWidget.value : "Manga Monochrome",
                    seedWidget ? seedWidget.value : 42
                );
                selectedSceneIndex = 0;
                selectedInstanceId = null;
                selectedGuideIndex = -1;
                selectedFigureIndex = -1;
                selectedCastId = null;
                syncToWidgets();
                renderAll();
            });

            toolbar.appendChild(btnAddScene);
            toolbar.appendChild(btnDeleteScene);
            toolbar.appendChild(btnResetLayout);
            container.appendChild(toolbar);

            // Scene Inspector
            const sceneInspector = document.createElement("div");
            sceneInspector.style.cssText = `
                display: flex;
                flex-direction: column;
                gap: 6px;
                background: #27272a;
                padding: 8px;
                border-radius: 6px;
                border: 1px solid #3f3f46;
            `;

            const sceneInspectorHeader = document.createElement("div");
            sceneInspectorHeader.style.cssText = "display: flex; justify-content: space-between; align-items: center;";

            const sceneBadge = document.createElement("div");
            sceneBadge.style.cssText = "display: flex; align-items: center; gap: 6px; font-weight: 600; font-size: 11px;";

            const sceneNameInput = document.createElement("input");
            sceneNameInput.type = "text";
            sceneNameInput.placeholder = "Scene Label";
            sceneNameInput.style.cssText = `
                background: #18181b;
                color: #fafafa;
                border: 1px solid #3f3f46;
                border-radius: 4px;
                padding: 3px 6px;
                font-size: 11px;
                width: 140px;
            `;
            sceneNameInput.oninput = () => {
                const scenes = getScenes();
                if (scenes[selectedSceneIndex]) {
                    scenes[selectedSceneIndex].name = sceneNameInput.value;
                    syncToWidgets();
                    renderCanvas();
                }
            };

            sceneInspectorHeader.appendChild(sceneBadge);
            sceneInspectorHeader.appendChild(sceneNameInput);
            sceneInspector.appendChild(sceneInspectorHeader);

            const promptTextarea = document.createElement("textarea");
            promptTextarea.rows = 3;
            promptTextarea.placeholder = "Scene context prompt (e.g. school classroom, desks, sunlight through window)...";
            promptTextarea.style.cssText = `
                background: #18181b;
                color: #fafafa;
                border: 1px solid #3f3f46;
                border-radius: 4px;
                padding: 6px;
                font-family: inherit;
                font-size: 11px;
                resize: vertical;
                box-sizing: border-box;
                width: 100%;
            `;
            promptTextarea.oninput = () => {
                const scenes = getScenes();
                if (scenes[selectedSceneIndex]) {
                    scenes[selectedSceneIndex].prompt = promptTextarea.value;
                    syncToWidgets();
                }
            };
            sceneInspector.appendChild(promptTextarea);

            // Characters in Scene Row
            const sceneCharactersRow = document.createElement("div");
            sceneCharactersRow.style.cssText = "display: flex; flex-direction: column; gap: 4px;";
            sceneInspector.appendChild(sceneCharactersRow);

            // Warning badge container
            const warningBadge = document.createElement("div");
            warningBadge.style.cssText = "display: none; padding: 4px 8px; border-radius: 4px; font-size: 11px; font-weight: 500;";
            sceneInspector.appendChild(warningBadge);

            container.appendChild(sceneInspector);

            // Frame Toolbar & Inspector
            const frameToolbar = document.createElement("div");
            frameToolbar.style.cssText = "display: none; gap: 6px; align-items: center; flex-wrap: wrap;";

            const btnAddFrame = createButton("+ Add Frame", "Add a new visual frame border", () => {
                const frames = getVisualFrames();
                const newFid = getNextFrameId(frames);
                const geom = calculateNewFrameGeometry(frames);
                frames.push({
                    frame_id: newFid,
                    order: frames.length + 1,
                    area: {
                        shape_type: "rect",
                        x: geom.x,
                        y: geom.y,
                        w: geom.w,
                        h: geom.h
                    },
                    border_thickness: 4,
                    border_color: "#000000",
                    is_full_bleed: false
                });
                selectedFrameIndex = frames.length - 1;
                syncToWidgets();
                renderAll();
            });

            const btnDeleteFrame = createButton("- Remove Frame", "Remove selected visual frame border", () => {
                const frames = getVisualFrames();
                if (frames.length === 0 || selectedFrameIndex < 0 || selectedFrameIndex >= frames.length) return;
                frames.splice(selectedFrameIndex, 1);
                if (selectedFrameIndex >= frames.length) {
                    selectedFrameIndex = frames.length - 1;
                }
                syncToWidgets();
                renderAll();
            }, "#7f1d1d");

            const btnCopyFramesFromScenes = createButton("📋 Copy Frames from Scenes", "One-shot non-linking copy of current scene regions to visual panel frames", () => {
                const scenes = getScenes();
                if (scenes.length === 0) return;
                const ok = confirm("One-shot copy scenes to visual frames? This will replace existing visual frames with clones of current scenes.");
                if (!ok) return;
                const p = getPage();
                p.visual_frames = copyFramesFromScenes(scenes);
                selectedFrameIndex = p.visual_frames.length > 0 ? 0 : -1;
                syncToWidgets();
                renderAll();
            }, "#1e3a5f");

            frameToolbar.appendChild(btnAddFrame);
            frameToolbar.appendChild(btnDeleteFrame);
            frameToolbar.appendChild(btnCopyFramesFromScenes);
            container.appendChild(frameToolbar);

            // Frame Inspector
            const frameInspector = document.createElement("div");
            frameInspector.style.cssText = `
                display: none;
                flex-direction: column;
                gap: 6px;
                background: #27272a;
                padding: 8px;
                border-radius: 6px;
                border: 1px solid #52525b;
            `;

            const frameInspectorHeader = document.createElement("div");
            frameInspectorHeader.style.cssText = "display: flex; justify-content: space-between; align-items: center;";

            const frameBadge = document.createElement("div");
            frameBadge.style.cssText = "display: flex; align-items: center; gap: 6px; font-weight: 600; font-size: 11px;";

            const frameChipsRow = document.createElement("div");
            frameChipsRow.style.cssText = "display: flex; gap: 4px; align-items: center; flex-wrap: wrap;";

            const frameThicknessRow = document.createElement("div");
            frameThicknessRow.style.cssText = "display: flex; align-items: center; gap: 8px;";
            frameThicknessRow.innerHTML = `
                <label style="color: #a1a1aa; font-size: 11px;">Line Thickness (px):</label>
                <input id="frame-thickness-input" type="number" min="1" max="24" value="4" style="
                    background: #18181b; color: #fafafa; border: 1px solid #3f3f46; border-radius: 4px;
                    padding: 2px 6px; width: 50px; font-size: 11px;
                " />
            `;
            const frameThicknessInput = frameThicknessRow.querySelector("#frame-thickness-input");
            frameThicknessInput.oninput = () => {
                const frames = getVisualFrames();
                const curFrame = frames[selectedFrameIndex];
                if (curFrame) {
                    curFrame.border_thickness = parseInt(frameThicknessInput.value, 10) || 4;
                    syncToWidgets();
                    renderCanvas();
                }
            };

            frameInspector.appendChild(frameInspectorHeader);
            frameInspectorHeader.appendChild(frameBadge);
            frameInspector.appendChild(frameChipsRow);
            frameInspector.appendChild(frameThicknessRow);
            container.appendChild(frameInspector);

            // Page-owned Rough Guide layer. This is intentionally separate from
            // Scene, Visual Panel Frame, CAST, and Character Instance semantics.
            const guideToolbar = document.createElement("div");
            guideToolbar.style.cssText = "display: none; gap: 6px; align-items: center; flex-wrap: wrap;";

            const guideFileInput = document.createElement("input");
            guideFileInput.type = "file";
            guideFileInput.accept = ".png,.jpg,.jpeg,.webp,image/png,image/jpeg,image/webp";
            guideFileInput.style.display = "none";
            document.body.appendChild(guideFileInput);
            let pendingGuideUploadMode = "add";

            function openGuideFilePicker(mode) {
                pendingGuideUploadMode = mode;
                guideFileInput.value = "";
                guideFileInput.click();
            }

            function readGuideImageDimensions(file) {
                return new Promise((resolve) => {
                    const objectUrl = URL.createObjectURL(file);
                    const image = new Image();
                    image.onload = () => {
                        const dimensions = { width: image.naturalWidth || image.width, height: image.naturalHeight || image.height };
                        URL.revokeObjectURL(objectUrl);
                        resolve(dimensions.width > 0 && dimensions.height > 0 ? dimensions : null);
                    };
                    image.onerror = () => {
                        URL.revokeObjectURL(objectUrl);
                        resolve(null);
                    };
                    image.src = objectUrl;
                });
            }

            async function uploadGuideAsset(file) {
                const fileName = String(file?.name || "");
                const extension = fileName.includes(".") ? fileName.slice(fileName.lastIndexOf(".")).toLowerCase() : "";
                if (![".png", ".jpg", ".jpeg", ".webp"].includes(extension)) {
                    throw new Error("Rough Guide accepts PNG, JPG, JPEG, or WEBP files only.");
                }

                const body = new FormData();
                body.append("image", file, file.name);
                body.append("subfolder", "tegaki_manga_guides");
                const response = await api.fetchApi("/upload/image", { method: "POST", body });
                if (!response.ok) {
                    throw new Error(`Guide upload failed (${response.status}).`);
                }
                const payload = await response.json();
                const name = String(payload?.name || "").replaceAll("\\", "/");
                const subfolder = String(payload?.subfolder || "").replaceAll("\\", "/").replace(/^\/+|\/+$/g, "");
                const reference = [subfolder, name].filter(Boolean).join("/");
                if (!reference || reference.startsWith("/") || reference.includes("..") || reference.includes("//")) {
                    throw new Error("Upload returned a non-canonical asset reference; refusing to save it.");
                }
                return {
                    reference,
                    dimensions: await readGuideImageDimensions(file)
                };
            }

            guideFileInput.onchange = async () => {
                const file = guideFileInput.files?.[0];
                if (!file) return;
                try {
                    const uploaded = await uploadGuideAsset(file);
                    const page = getPage();
                    const guides = getGuides();
                    const dimensions = uploaded.dimensions || { width: page.width_px, height: page.height_px };
                    const placement = calculateContainPlacement(
                        dimensions.width,
                        dimensions.height,
                        page.width_px,
                        page.height_px
                    );
                    if (pendingGuideUploadMode === "replace" && guides[selectedGuideIndex]) {
                        const guide = guides[selectedGuideIndex];
                        guide.guide_type = "rough_manga";
                        guide.asset_reference = uploaded.reference;
                        guide.placement = placement;
                        guide.enabled = guide.enabled !== false;
                        guide.figure_regions = Array.isArray(guide.figure_regions) ? guide.figure_regions : [];
                        guide.metadata = {
                            ...(guide.metadata || {}),
                            fit_mode: "contain",
                            source_dimensions: ({ width_px: dimensions.width, height_px: dimensions.height })
                        };
                    } else {
                        const guide = {
                            guide_id: getNextGuideId(guides),
                            guide_type: "rough_manga",
                            asset_reference: uploaded.reference,
                            placement,
                            enabled: true,
                            figure_regions: [],
                            metadata: {
                                fit_mode: "contain",
                                source_dimensions: ({ width_px: dimensions.width, height_px: dimensions.height })
                            }
                        };
                        guides.push(guide);
                        selectedGuideIndex = guides.length - 1;
                    }
                    selectedFigureIndex = -1;
                    syncToWidgets();
                    renderAll();
                } catch (error) {
                    console.error("[TegakiMinimumHandSceneEditor] Rough Guide upload failed", error);
                    alert(error?.message || "Rough Guide upload failed.");
                }
            };

            const btnAddGuide = createButton("+ Add Guide", "Upload a rough manga guide through ComfyUI's standard image upload boundary", () => {
                openGuideFilePicker("add");
            }, "#1e3a5f");
            const btnReplaceGuide = createButton("Replace Asset", "Replace the selected Guide asset and recompute contain placement", () => {
                if (selectedGuideIndex < 0 || !getGuides()[selectedGuideIndex]) return;
                openGuideFilePicker("replace");
            });
            const btnToggleGuide = createButton("Disable Guide", "Toggle whether the selected Guide is enabled", () => {
                const guide = getGuides()[selectedGuideIndex];
                if (!guide) return;
                guide.enabled = guide.enabled === false;
                syncToWidgets();
                renderAll();
            });
            const btnRemoveGuide = createButton("Remove Guide", "Remove only the selected Guide entry; preserve Character Instances and uploaded asset", () => {
                const guides = getGuides();
                if (selectedGuideIndex < 0 || selectedGuideIndex >= guides.length) return;
                guides.splice(selectedGuideIndex, 1);
                selectedGuideIndex = Math.min(selectedGuideIndex, guides.length - 1);
                selectedFigureIndex = -1;
                syncToWidgets();
                renderAll();
            }, "#7f1d1d");
            guideToolbar.appendChild(btnAddGuide);
            guideToolbar.appendChild(btnReplaceGuide);
            guideToolbar.appendChild(btnToggleGuide);
            guideToolbar.appendChild(btnRemoveGuide);
            container.appendChild(guideToolbar);

            const guideInspector = document.createElement("div");
            guideInspector.style.cssText = `
                display: none;
                flex-direction: column;
                gap: 6px;
                background: #1d2835;
                padding: 8px;
                border-radius: 6px;
                border: 1px solid #38bdf8;
            `;
            const guideInspectorHeader = document.createElement("div");
            guideInspectorHeader.style.cssText = "display: flex; justify-content: space-between; align-items: center; gap: 8px;";
            const guideStatusBadge = document.createElement("div");
            guideStatusBadge.style.cssText = "font-weight: 700; font-size: 11px; color: #7dd3fc;";
            const guideChipsRow = document.createElement("div");
            guideChipsRow.style.cssText = "display: flex; gap: 4px; align-items: center; flex-wrap: wrap;";
            const guideAssetLabel = document.createElement("div");
            guideAssetLabel.style.cssText = "font-size: 10px; color: #a5f3fc; word-break: break-all;";
            const guideFigureToolbar = document.createElement("div");
            guideFigureToolbar.style.cssText = "display: flex; gap: 5px; align-items: center; flex-wrap: wrap;";
            const btnAddFigure = createButton("+ Add Figure", "Add a manual Guide-local figure rectangle; no automatic interpretation", () => {
                const guide = getGuides()[selectedGuideIndex];
                if (!guide) return;
                if (!Array.isArray(guide.figure_regions)) guide.figure_regions = [];
                guide.figure_regions.push(createGuideFigure(guide.figure_regions));
                selectedFigureIndex = guide.figure_regions.length - 1;
                syncToWidgets();
                renderAll();
            });
            const btnRemoveFigure = createButton("Remove Figure", "Remove the selected Guide figure only", () => {
                const guide = getGuides()[selectedGuideIndex];
                if (!guide?.figure_regions || selectedFigureIndex < 0 || selectedFigureIndex >= guide.figure_regions.length) return;
                guide.figure_regions.splice(selectedFigureIndex, 1);
                selectedFigureIndex = Math.min(selectedFigureIndex, guide.figure_regions.length - 1);
                syncToWidgets();
                renderAll();
            }, "#7f1d1d");
            guideFigureToolbar.appendChild(btnAddFigure);
            guideFigureToolbar.appendChild(btnRemoveFigure);
            const guideFigureList = document.createElement("div");
            guideFigureList.style.cssText = "display: flex; flex-direction: column; gap: 5px;";

            guideInspectorHeader.appendChild(guideStatusBadge);
            guideInspector.appendChild(guideInspectorHeader);
            guideInspector.appendChild(guideChipsRow);
            guideInspector.appendChild(guideAssetLabel);
            guideInspector.appendChild(guideFigureToolbar);
            guideInspector.appendChild(guideFigureList);
            container.appendChild(guideInspector);

            // Character Instance Inspector (visible when an instance is selected)
            const charInspector = document.createElement("div");
            charInspector.style.cssText = `
                display: none;
                flex-direction: column;
                gap: 6px;
                background: #232733;
                padding: 8px;
                border-radius: 6px;
                border: 1px solid #3b82f6;
            `;

            const charInspectorHeader = document.createElement("div");
            charInspectorHeader.style.cssText = "display: flex; justify-content: space-between; align-items: center;";

            const charBadge = document.createElement("div");
            charBadge.style.cssText = "display: flex; align-items: center; gap: 6px; font-weight: 600; font-size: 11px; color: #60a5fa;";

            const btnRemoveChar = createButton("Remove Character", "Remove this character from the scene", () => {
                if (!selectedInstanceId) return;
                const p = getPage();
                const curInst = (p.character_instances || []).find(inst => inst.instance_id === selectedInstanceId);
                const sceneId = curInst ? curInst.scene_id : null;

                p.character_instances = (p.character_instances || []).filter(inst => inst.instance_id !== selectedInstanceId);
                p.guides = (p.guides || []).map(guide => unassignGuideInstance(guide, selectedInstanceId));
                selectedInstanceId = null;

                if (sceneId) {
                    const scene = (p.scenes || []).find(s => s.scene_id === sceneId);
                    const remaining = (p.character_instances || []).filter(inst => inst.scene_id === sceneId);
                    onInstanceRemoved(scene, remaining);
                }

                syncToWidgets();
                renderAll();
            }, "#b91c1c");
            btnRemoveChar.style.padding = "2px 8px";

            charInspectorHeader.appendChild(charBadge);
            charInspectorHeader.appendChild(btnRemoveChar);
            charInspector.appendChild(charInspectorHeader);

            const charActingInput = document.createElement("textarea");
            charActingInput.rows = 2;
            charActingInput.placeholder = "Free-text acting prompt (e.g. standing casually, reading a book, looking away, sitting)...";
            charActingInput.style.cssText = `
                background: #18181b;
                color: #fafafa;
                border: 1px solid #3f3f46;
                border-radius: 4px;
                padding: 6px;
                font-family: inherit;
                font-size: 11px;
                resize: vertical;
                box-sizing: border-box;
                width: 100%;
            `;
            charActingInput.oninput = () => {
                const instances = getCharacterInstances();
                const curInst = instances.find(i => i.instance_id === selectedInstanceId);
                if (curInst) {
                    curInst.acting_prompt = charActingInput.value;
                    syncToWidgets();
                    renderCanvas();
                }
            };
            charInspector.appendChild(charActingInput);

            container.appendChild(charInspector);

            // Render CAST section
            function renderCastSection() {
                castChipsRow.innerHTML = "";
                const castList = getCast();

                castList.forEach((c, idx) => {
                    const col = CAST_PALETTE[idx % CAST_PALETTE.length];
                    const isSelected = (selectedCastId === c.cast_id);

                    const chip = document.createElement("button");
                    chip.style.cssText = `
                        background: ${isSelected ? col.hex : "#27272a"};
                        color: ${isSelected ? "#ffffff" : "#d4d4d8"};
                        border: 1px solid ${col.hex};
                        border-radius: 4px;
                        padding: 3px 8px;
                        font-size: 11px;
                        font-weight: 600;
                        cursor: pointer;
                        display: flex;
                        align-items: center;
                        gap: 4px;
                    `;
                    chip.innerHTML = `
                        <span style="width: 8px; height: 8px; border-radius: 50%; background: ${isSelected ? '#fff' : col.hex};"></span>
                        <span>${c.display_name || c.cast_id}</span>
                    `;
                    chip.onclick = (e) => {
                        e.preventDefault();
                        selectedCastId = (selectedCastId === c.cast_id) ? null : c.cast_id;
                        renderCastSection();
                        renderInspector();
                    };
                    castChipsRow.appendChild(chip);
                });

                // Add CAST button
                const btnAddCast = document.createElement("button");
                btnAddCast.textContent = "+ Add CAST";
                btnAddCast.style.cssText = `
                    background: #27272a;
                    color: #fafafa;
                    border: 1px dashed #52525b;
                    border-radius: 4px;
                    padding: 3px 8px;
                    font-size: 11px;
                    font-weight: 500;
                    cursor: pointer;
                `;
                btnAddCast.onclick = (e) => {
                    e.preventDefault();
                    let nextNum = 1;
                    const existing = castList.map(c => {
                        const m = c.cast_id && c.cast_id.match(/cast_(\d+)/);
                        return m ? parseInt(m[1], 10) : 0;
                    });
                    if (existing.length > 0) {
                        nextNum = Math.max(...existing, 0) + 1;
                    }
                    let newId = `cast_${nextNum}`;
                    while (castList.some(c => c.cast_id === newId)) {
                        nextNum++;
                        newId = `cast_${nextNum}`;
                    }

                    const newCast = {
                        cast_id: newId,
                        display_name: `Character ${nextNum}`,
                        identity_prompt: "distinct character features, detailed clothing",
                        negative_prompt: "",
                        metadata: {}
                    };
                    castList.push(newCast);
                    selectedCastId = newId;
                    syncToWidgets();
                    renderCastSection();
                    renderInspector();
                    renderCanvas();
                };
                castChipsRow.appendChild(btnAddCast);

                // Render CAST Inspector for selected CAST
                const curCast = castList.find(c => c.cast_id === selectedCastId);
                if (!curCast) {
                    castInspector.style.display = "none";
                    return;
                }

                castInspector.style.display = "flex";
                castInspector.innerHTML = "";

                const headerRow = document.createElement("div");
                headerRow.style.cssText = "display: flex; justify-content: space-between; align-items: center;";
                const headerTitle = document.createElement("div");
                headerTitle.style.cssText = "font-weight: 600; font-size: 11px; color: #38bdf8;";
                headerTitle.textContent = `CAST Details (${curCast.cast_id})`;
                const btnDeleteCast = document.createElement("button");
                btnDeleteCast.style.cssText = `
                    background: #b91c1c; color: #fff; border: 1px solid #dc2626; border-radius: 4px;
                    padding: 2px 6px; font-size: 10px; cursor: pointer;
                `;
                btnDeleteCast.textContent = "Delete CAST";
                btnDeleteCast.onclick = (e) => {
                    e.preventDefault();
                    const allInstances = getCharacterInstances();
                    if (!canDeleteCast(curCast.cast_id, allInstances)) {
                        alert(`Cannot delete CAST '${curCast.display_name || curCast.cast_id}' because it is placed in scenes. Please remove appearances from scenes first.`);
                        return;
                    }
                    const p = getPage();
                    p.cast = p.cast.filter(c => c.cast_id !== curCast.cast_id);
                    selectedCastId = null;
                    syncToWidgets();
                    renderCastSection();
                    renderInspector();
                    renderCanvas();
                };
                headerRow.appendChild(headerTitle);
                headerRow.appendChild(btnDeleteCast);
                castInspector.appendChild(headerRow);

                const nameRow = document.createElement("div");
                nameRow.style.cssText = "display: flex; gap: 6px; align-items: center;";
                const nameLabel = document.createElement("label");
                nameLabel.style.cssText = "color: #a1a1aa; font-size: 11px; width: 80px;";
                nameLabel.textContent = "Name:";
                const nameInput = document.createElement("input");
                nameInput.type = "text";
                nameInput.value = curCast.display_name || "";
                nameInput.style.cssText = `
                    background: #27272a; color: #fff; border: 1px solid #3f3f46; border-radius: 4px;
                    padding: 2px 6px; font-size: 11px; flex: 1;
                `;
                nameInput.oninput = () => {
                    curCast.display_name = nameInput.value;
                    syncToWidgets();
                    renderCanvas();
                    renderInspector();
                };
                nameRow.appendChild(nameLabel);
                nameRow.appendChild(nameInput);
                castInspector.appendChild(nameRow);

                const promptRow = document.createElement("div");
                promptRow.style.cssText = "display: flex; flex-direction: column; gap: 2px;";
                const promptLabel = document.createElement("label");
                promptLabel.style.cssText = "color: #a1a1aa; font-size: 11px;";
                promptLabel.textContent = "Identity Prompt (features, hair, costume):";
                const idPromptArea = document.createElement("textarea");
                idPromptArea.rows = 2;
                idPromptArea.value = curCast.identity_prompt || "";
                idPromptArea.style.cssText = `
                    background: #27272a; color: #fff; border: 1px solid #3f3f46; border-radius: 4px;
                    padding: 4px; font-size: 11px; resize: vertical;
                `;
                idPromptArea.oninput = () => {
                    curCast.identity_prompt = idPromptArea.value;
                    syncToWidgets();
                };
                promptRow.appendChild(promptLabel);
                promptRow.appendChild(idPromptArea);
                castInspector.appendChild(promptRow);
            }

            const guidePreviewImages = new Map();

            function getGuidePreviewUrl(assetReference) {
                const normalized = String(assetReference || "").replaceAll("\\", "/");
                const slash = normalized.lastIndexOf("/");
                const name = slash >= 0 ? normalized.slice(slash + 1) : normalized;
                const subfolder = slash >= 0 ? normalized.slice(0, slash) : "";
                const query = new URLSearchParams({ filename: name, type: "input" });
                if (subfolder) query.set("subfolder", subfolder);
                return api.apiURL(`/view?${query.toString()}`);
            }

            function getGuidePreviewImage(guide) {
                const reference = String(guide?.asset_reference || "");
                if (!reference) return null;
                if (guidePreviewImages.has(reference)) return guidePreviewImages.get(reference);
                const image = new Image();
                guidePreviewImages.set(reference, image);
                image.onload = () => renderCanvas();
                image.onerror = () => {
                    guidePreviewImages.set(reference, null);
                    renderCanvas();
                };
                image.src = getGuidePreviewUrl(reference);
                return null;
            }

            function guideFigurePageArea(guide, figure) {
                const placement = guide?.placement || { x: 0, y: 0, w: 1, h: 1 };
                const local = figure?.area || { x: 0, y: 0, w: 0.2, h: 0.2 };
                return {
                    shape_type: "rect",
                    x: placement.x + local.x * placement.w,
                    y: placement.y + local.y * placement.h,
                    w: local.w * placement.w,
                    h: local.h * placement.h
                };
            }

            function renderGuideInspector() {
                const guides = getGuides();
                guideChipsRow.innerHTML = "";
                guides.forEach((guide, idx) => {
                    const selected = idx === selectedGuideIndex;
                    const chip = document.createElement("button");
                    chip.textContent = guide.guide_id || `Guide ${idx + 1}`;
                    chip.style.cssText = `
                        background: ${selected ? "#0284c7" : "#17202b"};
                        color: ${selected ? "#ffffff" : "#bae6fd"};
                        border: 1px solid ${selected ? "#7dd3fc" : "#0369a1"};
                        border-radius: 4px; padding: 2px 8px; font-size: 10px;
                        font-weight: 700; cursor: pointer;
                    `;
                    chip.onclick = (event) => {
                        event.preventDefault();
                        selectedGuideIndex = idx;
                        selectedFigureIndex = -1;
                        renderAll();
                    };
                    guideChipsRow.appendChild(chip);
                });

                if (guides.length === 0) {
                    selectedGuideIndex = -1;
                    selectedFigureIndex = -1;
                    guideStatusBadge.textContent = "No Rough Guide (optional)";
                    guideAssetLabel.textContent = "Add Guide uploads through the standard ComfyUI input boundary. Scene authoring remains available without a Guide.";
                    btnReplaceGuide.disabled = true;
                    btnToggleGuide.disabled = true;
                    btnRemoveGuide.disabled = true;
                    btnAddFigure.disabled = true;
                    btnRemoveFigure.disabled = true;
                    guideFigureList.innerHTML = "";
                    return;
                }

                if (selectedGuideIndex < 0 || selectedGuideIndex >= guides.length) selectedGuideIndex = 0;
                const guide = guides[selectedGuideIndex];
                if (!Array.isArray(guide.figure_regions)) guide.figure_regions = [];
                if (selectedFigureIndex >= guide.figure_regions.length) selectedFigureIndex = guide.figure_regions.length - 1;

                const enabled = guide.enabled !== false;
                guideStatusBadge.textContent = `${guide.guide_id || "Guide"} · ${enabled ? "ENABLED" : "DISABLED"} · ${guide.figure_regions.length} figure(s)`;
                guideStatusBadge.style.color = enabled ? "#7dd3fc" : "#fbbf24";
                guideAssetLabel.textContent = `Asset: ${guide.asset_reference || "missing"} · Placement: contain / page-normalized · Associations are manual only`;
                btnReplaceGuide.disabled = false;
                btnToggleGuide.disabled = false;
                btnToggleGuide.textContent = enabled ? "Disable Guide" : "Enable Guide";
                btnRemoveGuide.disabled = false;
                btnAddFigure.disabled = false;
                btnRemoveFigure.disabled = selectedFigureIndex < 0;

                guideFigureList.innerHTML = "";
                const instances = getCharacterInstances();
                const usedInstanceIds = new Set(guide.figure_regions.map(figure => figure.instance_id).filter(Boolean));
                guide.figure_regions.forEach((figure, idx) => {
                    const row = document.createElement("div");
                    row.style.cssText = `
                        display: flex; flex-direction: column; gap: 4px; padding: 5px;
                        background: ${idx === selectedFigureIndex ? "#164e63" : "#17202b"};
                        border: 1px solid ${idx === selectedFigureIndex ? "#67e8f9" : "#334155"};
                        border-radius: 4px;
                    `;
                    const rowHeader = document.createElement("div");
                    rowHeader.style.cssText = "display: flex; justify-content: space-between; align-items: center; gap: 6px;";
                    const selectFigureButton = document.createElement("button");
                    selectFigureButton.textContent = `${figure.figure_id || `figure_${idx + 1}`} · local ${Number(figure.area?.x || 0).toFixed(2)},${Number(figure.area?.y || 0).toFixed(2)}`;
                    selectFigureButton.style.cssText = "flex: 1; text-align: left; background: transparent; color: #e0f2fe; border: 0; padding: 0; font-size: 10px; font-weight: 700; cursor: pointer;";
                    selectFigureButton.onclick = (event) => {
                        event.preventDefault();
                        selectedFigureIndex = idx;
                        renderAll();
                    };
                    const removeButton = document.createElement("button");
                    removeButton.textContent = "×";
                    removeButton.title = "Remove this Guide figure";
                    removeButton.style.cssText = "background: #7f1d1d; color: #fff; border: 1px solid #ef4444; border-radius: 3px; padding: 0 5px; cursor: pointer;";
                    removeButton.onclick = (event) => {
                        event.preventDefault();
                        guide.figure_regions.splice(idx, 1);
                        selectedFigureIndex = Math.min(selectedFigureIndex, guide.figure_regions.length - 1);
                        syncToWidgets();
                        renderAll();
                    };
                    rowHeader.appendChild(selectFigureButton);
                    rowHeader.appendChild(removeButton);
                    row.appendChild(rowHeader);

                    const associationRow = document.createElement("div");
                    associationRow.style.cssText = "display: flex; align-items: center; gap: 5px;";
                    const associationLabel = document.createElement("span");
                    associationLabel.textContent = "Character Instance:";
                    associationLabel.style.cssText = "color: #a5f3fc; font-size: 10px; min-width: 105px;";
                    const associationSelect = document.createElement("select");
                    associationSelect.style.cssText = "flex: 1; background: #0f172a; color: #e0f2fe; border: 1px solid #475569; border-radius: 3px; padding: 2px; font-size: 10px;";
                    const unassignedOption = document.createElement("option");
                    unassignedOption.value = "";
                    unassignedOption.textContent = "Unassigned";
                    associationSelect.appendChild(unassignedOption);
                    instances.forEach((instance) => {
                        const option = document.createElement("option");
                        option.value = instance.instance_id;
                        const cast = getCast().find(entry => entry.cast_id === instance.cast_id);
                        option.textContent = `${instance.instance_id} · ${cast?.display_name || instance.cast_id}`;
                        option.disabled = usedInstanceIds.has(instance.instance_id) && instance.instance_id !== figure.instance_id;
                        associationSelect.appendChild(option);
                    });
                    associationSelect.value = figure.instance_id || "";
                    associationSelect.onchange = () => {
                        const result = associateGuideFigure(guide, figure.figure_id, associationSelect.value || null);
                        if (!result.ok) {
                            alert(result.error);
                            renderGuideInspector();
                            return;
                        }
                        guides[selectedGuideIndex] = result.guide;
                        syncToWidgets();
                        renderAll();
                    };
                    associationRow.appendChild(associationLabel);
                    associationRow.appendChild(associationSelect);
                    row.appendChild(associationRow);
                    guideFigureList.appendChild(row);
                });
            }

            function renderInspector() {
                updateLayerButtons();
                const scenes = getScenes();
                const frames = getVisualFrames();
                const guides = getGuides();
                const countSpan = container.querySelector("#scene-counter");
                if (countSpan) countSpan.textContent = `Scenes: ${scenes.length} / 6 | Frames: ${frames.length} | Guides: ${guides.length}`;

                btnAddScene.disabled = scenes.length >= 6;
                btnDeleteScene.disabled = scenes.length <= 1;

                if (activeEditLayer === "frame") {
                    toolbar.style.display = "none";
                    sceneInspector.style.display = "none";
                    charInspector.style.display = "none";
                    guideToolbar.style.display = "none";
                    guideInspector.style.display = "none";
                    frameToolbar.style.display = "flex";
                    frameInspector.style.display = "flex";

                    // Render Frame Chips
                    frameChipsRow.innerHTML = "";
                    frames.forEach((fr, idx) => {
                        const isSelected = (idx === selectedFrameIndex);
                        const chip = document.createElement("button");
                        chip.style.cssText = `
                            background: ${isSelected ? "#3b82f6" : "#18181b"};
                            color: ${isSelected ? "#ffffff" : "#d4d4d8"};
                            border: 1px solid ${isSelected ? "#60a5fa" : "#3f3f46"};
                            border-radius: 4px;
                            padding: 2px 8px;
                            font-size: 11px;
                            font-weight: 600;
                            cursor: pointer;
                        `;
                        chip.textContent = fr.frame_id || `Frame ${idx + 1}`;
                        chip.onclick = (e) => {
                            e.preventDefault();
                            selectedFrameIndex = idx;
                            renderInspector();
                            renderCanvas();
                        };
                        frameChipsRow.appendChild(chip);
                    });

                    const curFrame = frames[selectedFrameIndex];
                    if (curFrame) {
                        frameBadge.innerHTML = `<span style="color: #60a5fa;">Selected: <b>${curFrame.frame_id || 'Frame ' + (selectedFrameIndex + 1)}</b></span>`;
                        frameThicknessInput.value = curFrame.border_thickness || 4;
                    } else {
                        frameBadge.innerHTML = `<span style="color: #71717a;">No frame selected</span>`;
                    }
                    return;
                } else if (activeEditLayer === "guide") {
                    toolbar.style.display = "none";
                    sceneInspector.style.display = "none";
                    charInspector.style.display = "none";
                    frameToolbar.style.display = "none";
                    frameInspector.style.display = "none";
                    guideToolbar.style.display = "flex";
                    guideInspector.style.display = "flex";
                    renderGuideInspector();
                    return;
                } else {
                    toolbar.style.display = "flex";
                    sceneInspector.style.display = "flex";
                    frameToolbar.style.display = "none";
                    frameInspector.style.display = "none";
                    guideToolbar.style.display = "none";
                    guideInspector.style.display = "none";
                }

                const curScene = scenes[selectedSceneIndex];
                if (!curScene) {
                    sceneBadge.innerHTML = `<span style="color: #71717a;">No scene selected</span>`;
                    sceneNameInput.value = "";
                    promptTextarea.value = "";
                    sceneCharactersRow.innerHTML = "";
                    warningBadge.style.display = "none";
                    charInspector.style.display = "none";
                    return;
                }

                const col = getSceneColor(selectedSceneIndex);
                sceneBadge.innerHTML = `
                    <span style="display:inline-block; width:10px; height:10px; border-radius:50%; background:${col.hex};"></span>
                    <span>Scene ${selectedSceneIndex + 1} (${curScene.scene_id})</span>
                `;
                sceneNameInput.value = curScene.name || "";
                promptTextarea.value = curScene.prompt || "";

                // Characters in this scene
                const allInstances = getCharacterInstances();
                const sceneInstances = allInstances.filter(inst => inst.scene_id === curScene.scene_id);
                const castList = getCast();

                // Determine placement candidate label / tooltip
                const candidateCheck = chooseCastForPlacement({ castList, selectedCastId, sceneInstances });
                let addCharLabel = "+ Add Character";
                let addCharTitle = "Place character into this scene";
                if (candidateCheck.ok && candidateCheck.targetCast) {
                    const cName = candidateCheck.targetCast.display_name || candidateCheck.targetCast.cast_id;
                    addCharLabel = `+ Place ${cName}`;
                    addCharTitle = `Place ${cName} into Scene ${selectedSceneIndex + 1}`;
                } else if (candidateCheck.reason === "SELECTION_REQUIRED") {
                    addCharTitle = "Select a CAST above first to place into this scene";
                }

                sceneCharactersRow.innerHTML = `
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 4px;">
                        <span style="font-size: 11px; font-weight: 600; color: #a1a1aa;">CHARACTERS IN SCENE (${sceneInstances.length})</span>
                        <button id="btn-add-char-to-scene" title="${addCharTitle}" style="
                            background: #27272a; color: #fafafa; border: 1px dashed #52525b; border-radius: 4px;
                            padding: 2px 6px; font-size: 10px; cursor: pointer;
                        ">${addCharLabel}</button>
                    </div>
                    <div id="scene-chars-chips" style="display: flex; gap: 4px; align-items: center; flex-wrap: wrap;"></div>
                `;

                const chipsContainer = sceneCharactersRow.querySelector("#scene-chars-chips");
                sceneInstances.forEach((inst, idx) => {
                    const cInfo = castList.find(c => c.cast_id === inst.cast_id);
                    const cName = cInfo ? cInfo.display_name : inst.cast_id;
                    const cCol = getCastColor(inst.cast_id);
                    const isSelected = (selectedInstanceId === inst.instance_id);

                    const chip = document.createElement("button");
                    chip.style.cssText = `
                        background: ${isSelected ? cCol.hex : "#18181b"};
                        color: ${isSelected ? "#fff" : "#e4e4e7"};
                        border: 1px solid ${cCol.hex};
                        border-radius: 4px;
                        padding: 2px 6px;
                        font-size: 10px;
                        font-weight: 600;
                        cursor: pointer;
                    `;
                    chip.textContent = `${cName} #${idx + 1}`;
                    chip.onclick = (e) => {
                        e.preventDefault();
                        selectedInstanceId = (selectedInstanceId === inst.instance_id) ? null : inst.instance_id;
                        renderInspector();
                        renderCanvas();
                    };
                    chipsContainer.appendChild(chip);
                });

                // Wire Add Character to Scene
                const btnAddChar = sceneCharactersRow.querySelector("#btn-add-char-to-scene");
                btnAddChar.onclick = (e) => {
                    e.preventDefault();
                    const pickResult = chooseCastForPlacement({ castList, selectedCastId, sceneInstances });
                    if (!pickResult.ok) {
                        alert(pickResult.error);
                        return;
                    }

                    const targetCast = pickResult.targetCast;
                    const newInstId = getNextInstanceId(allInstances);
                    const geom = calculateNewInstanceGeometry(curScene.area, sceneInstances.length);

                    const newInst = {
                        instance_id: newInstId,
                        cast_id: targetCast.cast_id,
                        scene_id: curScene.scene_id,
                        order: sceneInstances.length + 1,
                        area: geom,
                        acting_prompt: "standing casually",
                        negative_prompt_override: "",
                        metadata: {}
                    };

                    allInstances.push(newInst);
                    curScene.input_mode = "cast";
                    selectedInstanceId = newInstId;

                    syncToWidgets();
                    renderInspector();
                    renderCanvas();
                };

                // Warnings for Scene Complexity
                const instCount = sceneInstances.length;
                if (instCount === 3) {
                    warningBadge.style.display = "block";
                    warningBadge.style.background = "rgba(245, 158, 11, 0.2)";
                    warningBadge.style.color = "#fbbf24";
                    warningBadge.style.border = "1px solid #f59e0b";
                    warningBadge.textContent = "3 characters — Advanced / Seed-Sensitive. Try new seeds or split scene if needed.";
                } else if (instCount >= 4) {
                    warningBadge.style.display = "block";
                    warningBadge.style.background = "rgba(239, 68, 68, 0.2)";
                    warningBadge.style.color = "#f87171";
                    warningBadge.style.border = "1px solid #ef4444";
                    warningBadge.textContent = "4+ characters — Experimental. Multi-cut / additional scenes are usually more reliable.";
                } else {
                    warningBadge.style.display = "none";
                }

                // Render Selected Character Inspector
                const curInst = allInstances.find(i => i.instance_id === selectedInstanceId);
                if (curInst && curInst.scene_id === curScene.scene_id) {
                    charInspector.style.display = "flex";
                    const cInfo = castList.find(c => c.cast_id === curInst.cast_id);
                    const cName = cInfo ? cInfo.display_name : curInst.cast_id;
                    const cCol = getCastColor(curInst.cast_id);
                    charBadge.innerHTML = "";
                    const dot = document.createElement("span");
                    dot.style.cssText = `display:inline-block; width:8px; height:8px; border-radius:50%; background:${cCol.hex};`;
                    const badgeText = document.createElement("span");
                    badgeText.textContent = `Editing [${cName}] in Scene ${selectedSceneIndex + 1}`;
                    charBadge.appendChild(dot);
                    charBadge.appendChild(badgeText);
                    charActingInput.value = curInst.acting_prompt || "";
                } else {
                    charInspector.style.display = "none";
                }
            }

            function renderCanvas() {
                const cw = canvas.width;
                const ch = canvas.height;

                ctx.clearRect(0, 0, cw, ch);

                // Background
                ctx.fillStyle = "#ffffff";
                ctx.fillRect(0, 0, cw, ch);

                // Grid lines
                ctx.strokeStyle = "#f3f4f6";
                ctx.lineWidth = 1;
                for (let x = 0.25; x < 1.0; x += 0.25) {
                    ctx.beginPath();
                    ctx.moveTo(x * cw, 0);
                    ctx.lineTo(x * cw, ch);
                    ctx.stroke();
                }
                for (let y = 0.25; y < 1.0; y += 0.25) {
                    ctx.beginPath();
                    ctx.moveTo(0, y * ch);
                    ctx.lineTo(cw, y * ch);
                    ctx.stroke();
                }

                const scenes = getScenes();
                const frames = getVisualFrames();
                const allInstances = getCharacterInstances();
                const castList = getCast();

                const isFrameActive = (activeEditLayer === "frame");
                const isSceneActive = (activeEditLayer === "scene");
                const isCharActive = (activeEditLayer === "character");

                // 1. Draw Visual Frames (Border Layer)
                frames.forEach((fr, idx) => {
                    const b = fr.area || fr.shape || { x: 0, y: 0, w: 1, h: 1 };
                    const isSelected = (isFrameActive && idx === selectedFrameIndex);
                    const rx = b.x * cw;
                    const ry = b.y * ch;
                    const rw = b.w * cw;
                    const rh = b.h * ch;

                    // Fill interior very light translucent when editing frames
                    if (isFrameActive) {
                        ctx.fillStyle = isSelected ? "rgba(59, 130, 246, 0.08)" : "rgba(0, 0, 0, 0.02)";
                        ctx.fillRect(rx, ry, rw, rh);
                    }

                    // Border line (comic panel style)
                    const thickness = Math.max(1, Math.min(10, Math.round((fr.border_thickness || 4) * (cw / 832))));
                    ctx.strokeStyle = isSelected ? "#2563eb" : (fr.border_color || "#18181b");
                    ctx.lineWidth = isSelected ? Math.max(thickness, 3) : thickness;
                    ctx.strokeRect(rx, ry, rw, rh);

                    // Badge
                    const label = fr.frame_id || `Frame ${idx + 1}`;
                    ctx.font = "bold 9px system-ui, sans-serif";
                    const tw = ctx.measureText(label).width;
                    ctx.fillStyle = isSelected ? "#2563eb" : "#3f3f46";
                    ctx.fillRect(rx, ry, tw + 6, 14);
                    ctx.fillStyle = "#ffffff";
                    ctx.fillText(label, rx + 3, ry + 10);

                    // Handles if selected in Frame layer
                    if (isSelected) {
                        const hs = 8;
                        ctx.fillStyle = "#ffffff";
                        ctx.strokeStyle = "#2563eb";
                        ctx.lineWidth = 2;
                        const corners = [
                            [rx, ry],
                            [rx + rw, ry],
                            [rx + rw, ry + rh],
                            [rx, ry + rh]
                        ];
                        corners.forEach(([cx, cy]) => {
                            ctx.fillRect(cx - hs / 2, cy - hs / 2, hs, hs);
                            ctx.strokeRect(cx - hs / 2, cy - hs / 2, hs, hs);
                        });
                    }
                });

                const guides = getGuides();
                const isGuideActive = (activeEditLayer === "guide");

                // 2. Draw Page-owned Rough Guides. Figure geometry is Guide-local;
                // this conversion is runtime/view derived and is never persisted.
                guides.forEach((guide, guideIndex) => {
                    const placement = guide.placement || { x: 0, y: 0, w: 1, h: 1 };
                    const isSelectedGuide = isGuideActive && guideIndex === selectedGuideIndex;
                    const enabled = guide.enabled !== false;
                    const rx = placement.x * cw;
                    const ry = placement.y * ch;
                    const rw = placement.w * cw;
                    const rh = placement.h * ch;
                    const preview = getGuidePreviewImage(guide);

                    ctx.save();
                    ctx.globalAlpha = isGuideActive ? (enabled ? 0.34 : 0.08) : 0.07;
                    if (preview) {
                        ctx.drawImage(preview, rx, ry, rw, rh);
                    } else {
                        ctx.fillStyle = enabled ? "#bae6fd" : "#facc15";
                        ctx.fillRect(rx, ry, rw, rh);
                    }
                    ctx.globalAlpha = isSelectedGuide ? 0.9 : 0.45;
                    ctx.strokeStyle = enabled ? "#0284c7" : "#ca8a04";
                    ctx.lineWidth = isSelectedGuide ? 2 : 1;
                    ctx.setLineDash(enabled ? [] : [5, 4]);
                    ctx.strokeRect(rx, ry, rw, rh);
                    ctx.setLineDash([]);

                    const guideLabel = `${guide.guide_id || `Guide ${guideIndex + 1}`} · ${enabled ? "enabled" : "disabled"}`;
                    ctx.font = "bold 9px system-ui, sans-serif";
                    const guideLabelWidth = ctx.measureText(guideLabel).width;
                    ctx.globalAlpha = isGuideActive ? 0.85 : 0.32;
                    ctx.fillStyle = enabled ? "#0369a1" : "#a16207";
                    ctx.fillRect(rx, ry, guideLabelWidth + 6, 14);
                    ctx.fillStyle = "#ffffff";
                    ctx.fillText(guideLabel, rx + 3, ry + 10);
                    ctx.restore();

                    (guide.figure_regions || []).forEach((figure, figureIndex) => {
                        const b = guideFigurePageArea(guide, figure);
                        const fx = b.x * cw;
                        const fy = b.y * ch;
                        const fw = b.w * cw;
                        const fh = b.h * ch;
                        const isSelectedFigure = isSelectedGuide && figureIndex === selectedFigureIndex;
                        ctx.save();
                        ctx.fillStyle = isSelectedFigure ? "rgba(14, 116, 144, 0.28)" : "rgba(14, 116, 144, 0.10)";
                        ctx.strokeStyle = isSelectedFigure ? "#0e7490" : "rgba(14, 116, 144, 0.65)";
                        ctx.lineWidth = isSelectedFigure ? 2.5 : 1;
                        ctx.setLineDash(isGuideActive ? [] : [3, 3]);
                        ctx.fillRect(fx, fy, fw, fh);
                        ctx.strokeRect(fx, fy, fw, fh);
                        ctx.setLineDash([]);
                        ctx.font = "bold 8px system-ui, sans-serif";
                        ctx.fillStyle = isSelectedFigure ? "#0e7490" : "rgba(14, 116, 144, 0.75)";
                        ctx.fillText(figure.figure_id || `figure_${figureIndex + 1}`, fx + 3, fy + 10);
                        if (isSelectedFigure) {
                            const hs = 8;
                            ctx.fillStyle = "#ffffff";
                            ctx.strokeStyle = "#0e7490";
                            ctx.lineWidth = 2;
                            [[fx, fy], [fx + fw, fy], [fx + fw, fy + fh], [fx, fy + fh]].forEach(([cx, cy]) => {
                                ctx.fillRect(cx - hs / 2, cy - hs / 2, hs, hs);
                                ctx.strokeRect(cx - hs / 2, cy - hs / 2, hs, hs);
                            });
                        }
                        ctx.restore();
                    });
                });

                // 3. Draw Scenes (Translucent boxes)
                scenes.forEach((sc, idx) => {
                    const b = sc.area || { x: 0, y: 0, w: 1, h: 1 };
                    const col = getSceneColor(idx);
                    const isSelected = (isSceneActive && idx === selectedSceneIndex && !selectedInstanceId);

                    const rx = b.x * cw;
                    const ry = b.y * ch;
                    const rw = b.w * cw;
                    const rh = b.h * ch;

                    // Fill & stroke alpha based on layer
                    let fillAlpha = isSelected ? 0.22 : 0.10;
                    let strokeAlpha = 1.0;
                    let strokeWidth = isSelected ? 3 : 1.5;
                    if (isFrameActive) {
                        fillAlpha = 0.04;
                        strokeAlpha = 0.4;
                        strokeWidth = 1;
                    }

                    // Fill
                    ctx.fillStyle = `rgba(${col.rgb.join(",")}, ${fillAlpha})`;
                    ctx.fillRect(rx, ry, rw, rh);

                    // Stroke
                    ctx.strokeStyle = isFrameActive ? `rgba(${col.rgb.join(",")}, ${strokeAlpha})` : col.hex;
                    ctx.lineWidth = strokeWidth;
                    ctx.strokeRect(rx, ry, rw, rh);

                    // Label badge
                    const label = `Scene ${idx + 1}: ${sc.name || sc.scene_id}`;
                    ctx.font = "bold 10px system-ui, sans-serif";
                    const tw = ctx.measureText(label).width;

                    ctx.fillStyle = isFrameActive ? `rgba(${col.rgb.join(",")}, 0.6)` : col.hex;
                    ctx.fillRect(rx, ry, tw + 8, 16);

                    ctx.fillStyle = "#ffffff";
                    ctx.fillText(label, rx + 4, ry + 12);

                    // Scene Handles
                    if (isSelected) {
                        const hs = 8;
                        ctx.fillStyle = "#ffffff";
                        ctx.strokeStyle = col.hex;
                        ctx.lineWidth = 2;

                        const corners = [
                            [rx, ry],
                            [rx + rw, ry],
                            [rx + rw, ry + rh],
                            [rx, ry + rh]
                        ];
                        corners.forEach(([cx, cy]) => {
                            ctx.fillRect(cx - hs / 2, cy - hs / 2, hs, hs);
                            ctx.strokeRect(cx - hs / 2, cy - hs / 2, hs, hs);
                        });
                    }
                });

                // 3. Draw Character Instances (Strong saturated boxes)
                allInstances.forEach(inst => {
                    const b = inst.area || { x: 0, y: 0, w: 0.2, h: 0.2 };
                    const col = getCastColor(inst.cast_id);
                    const isSelected = (isCharActive && inst.instance_id === selectedInstanceId);
                    const cInfo = castList.find(c => c.cast_id === inst.cast_id);
                    const cName = cInfo ? cInfo.display_name : inst.cast_id;

                    const rx = b.x * cw;
                    const ry = b.y * ch;
                    const rw = b.w * cw;
                    const rh = b.h * ch;

                    let fillAlpha = isSelected ? 0.35 : 0.20;
                    let strokeAlpha = 1.0;
                    let strokeWidth = isSelected ? 3 : 2;
                    if (isFrameActive) {
                        fillAlpha = 0.05;
                        strokeAlpha = 0.3;
                        strokeWidth = 1;
                    }

                    // Fill
                    ctx.fillStyle = `rgba(${col.rgb.join(",")}, ${fillAlpha})`;
                    ctx.fillRect(rx, ry, rw, rh);

                    // Stroke
                    ctx.strokeStyle = isFrameActive ? `rgba(${col.rgb.join(",")}, ${strokeAlpha})` : col.hex;
                    ctx.lineWidth = strokeWidth;
                    ctx.strokeRect(rx, ry, rw, rh);

                    // Badge
                    const badgeText = `${cName} (${inst.instance_id})`;
                    ctx.font = "bold 10px system-ui, sans-serif";
                    const tw = ctx.measureText(badgeText).width;

                    ctx.fillStyle = isFrameActive ? `rgba(${col.rgb.join(",")}, 0.5)` : col.hex;
                    ctx.fillRect(rx, ry, tw + 8, 16);

                    ctx.fillStyle = "#ffffff";
                    ctx.fillText(badgeText, rx + 4, ry + 12);

                    // Character Handles
                    if (isSelected) {
                        const hs = 8;
                        ctx.fillStyle = "#ffffff";
                        ctx.strokeStyle = col.hex;
                        ctx.lineWidth = 2;

                        const corners = [
                            [rx, ry],
                            [rx + rw, ry],
                            [rx + rw, ry + rh],
                            [rx, ry + rh]
                        ];
                        corners.forEach(([cx, cy]) => {
                            ctx.fillRect(cx - hs / 2, cy - hs / 2, hs, hs);
                            ctx.strokeRect(cx - hs / 2, cy - hs / 2, hs, hs);
                        });
                    }
                });
            }

            function renderAll() {
                renderCastSection();
                renderInspector();
                renderCanvas();
                updateRouteBadge();
            }

            function syncToWidgets() {
                const docWidget = node.widgets.find(w => w.name === "document_json");
                if (docWidget) {
                    docWidget.value = JSON.stringify(doc, null, 2);
                }

                const page = getPage();
                const resWidget = node.widgets.find(w => w.name === "resolution");
                if (resWidget && (page.width_px || page.height_px)) {
                    const resStr = `${page.width_px}x${page.height_px}`;
                    if (resStr.includes("832x1216")) resWidget.value = "Portrait 832x1216";
                    else if (resStr.includes("1216x832")) resWidget.value = "Landscape 1216x832";
                    else if (resStr.includes("1024x1024")) resWidget.value = "Square 1024x1024";
                }

                const styleWidget = node.widgets.find(w => w.name === "style_template");
                if (styleWidget && page.metadata && page.metadata.style_template) {
                    styleWidget.value = page.metadata.style_template;
                }

                const seedWidget = node.widgets.find(w => w.name === "seed");
                if (seedWidget && page.generation && page.generation.seed !== undefined) {
                    seedWidget.value = page.generation.seed;
                }

                node.setDirtyCanvas(true, true);
                updateRouteBadge();
            }

            node._tegakiRestoreFromWidgets = function () {
                const docWidget = node.widgets.find(w => w.name === "document_json");
                if (docWidget && docWidget.value && docWidget.value.trim() !== "") {
                    try {
                        const parsed = JSON.parse(docWidget.value);
                        if (parsed && parsed.schema_id === "TEGAKI_AUTHORING_DOCUMENT" && Array.isArray(parsed.pages)) {
                            parsed.pages.forEach(p => {
                                const legacy = p["dimensions"];
                                if (legacy && (!p.width_px || !p.height_px)) {
                                    p.width_px = legacy.width_px;
                                    p.height_px = legacy.height_px;
                                    delete p["dimensions"];
                                }
                            });
                            doc = parsed;
                        }
                    } catch (e) {
                        console.warn("[TegakiMinimumHandSceneEditor] Failed to parse document_json widget:", e);
                    }
                }
                const scenes = getScenes();
                if (selectedSceneIndex >= scenes.length) {
                    selectedSceneIndex = 0;
                }
                renderAll();
            };

            function getCanvasNormPos(e) {
                const rect = canvas.getBoundingClientRect();
                const x = (e.clientX - rect.left) / rect.width;
                const y = (e.clientY - rect.top) / rect.height;
                return {
                    x: Math.max(0, Math.min(1, x)),
                    y: Math.max(0, Math.min(1, y)),
                    px: e.clientX - rect.left,
                    py: e.clientY - rect.top
                };
            }

            function hitTestHandle(box, px, py) {
                const b = box || { x: 0, y: 0, w: 1, h: 1 };
                // Pointer coordinates are CSS pixels from getBoundingClientRect;
                // use the rendered canvas size rather than the backing bitmap
                // size so corner handles remain hittable under node zoom.
                const rect = canvas.getBoundingClientRect();
                const cw = rect.width;
                const ch = rect.height;
                const rx = b.x * cw;
                const ry = b.y * ch;
                const rw = b.w * cw;
                const rh = b.h * ch;
                const hs = 10;

                if (Math.abs(px - rx) <= hs && Math.abs(py - ry) <= hs) return "nw";
                if (Math.abs(px - (rx + rw)) <= hs && Math.abs(py - ry) <= hs) return "ne";
                if (Math.abs(px - (rx + rw)) <= hs && Math.abs(py - (ry + rh)) <= hs) return "se";
                if (Math.abs(px - rx) <= hs && Math.abs(py - (ry + rh)) <= hs) return "sw";
                return null;
            }

            function hitTestCharacter(x, y) {
                const instances = getCharacterInstances();
                for (let i = instances.length - 1; i >= 0; i--) {
                    const b = instances[i].area || { x: 0, y: 0, w: 0, h: 0 };
                    if (x >= b.x && x <= b.x + b.w && y >= b.y && y <= b.y + b.h) {
                        return instances[i];
                    }
                }
                return null;
            }

            function hitTestScene(x, y) {
                const scenes = getScenes();
                for (let i = scenes.length - 1; i >= 0; i--) {
                    const b = scenes[i].area || { x: 0, y: 0, w: 1, h: 1 };
                    if (x >= b.x && x <= b.x + b.w && y >= b.y && y <= b.y + b.h) {
                        return i;
                    }
                }
                return -1;
            }

            function hitTestFrame(x, y) {
                const frames = getVisualFrames();
                for (let i = frames.length - 1; i >= 0; i--) {
                    const b = frames[i].area || frames[i].shape || { x: 0, y: 0, w: 1, h: 1 };
                    if (x >= b.x && x <= b.x + b.w && y >= b.y && y <= b.y + b.h) {
                        return i;
                    }
                }
                return -1;
            }

            function hitTestGuide(x, y) {
                const guides = getGuides();
                for (let i = guides.length - 1; i >= 0; i--) {
                    const b = guides[i].placement || { x: 0, y: 0, w: 1, h: 1 };
                    if (x >= b.x && x <= b.x + b.w && y >= b.y && y <= b.y + b.h) return i;
                }
                return -1;
            }

            function hitTestGuideFigure(guide, x, y) {
                if (!guide) return -1;
                const figures = guide.figure_regions || [];
                for (let i = figures.length - 1; i >= 0; i--) {
                    const b = guideFigurePageArea(guide, figures[i]);
                    if (x >= b.x && x <= b.x + b.w && y >= b.y && y <= b.y + b.h) return i;
                }
                return -1;
            }

            canvas.onmousedown = (e) => {
                const pos = getCanvasNormPos(e);
                const scenes = getScenes();
                const frames = getVisualFrames();
                const allInstances = getCharacterInstances();

                // Layer: ROUGH GUIDE. Manipulation is limited to Guide-local
                // figure rectangles and cannot move Scene/Frame/Character boxes.
                if (activeEditLayer === "guide") {
                    const guides = getGuides();
                    const curGuide = guides[selectedGuideIndex];
                    if (curGuide) {
                        const figures = curGuide.figure_regions || [];
                        if (selectedFigureIndex >= 0 && selectedFigureIndex < figures.length) {
                            const figureArea = guideFigurePageArea(curGuide, figures[selectedFigureIndex]);
                            const handle = hitTestHandle(figureArea, pos.px, pos.py);
                            if (handle) {
                                isDragging = true;
                                dragTarget = "guide";
                                dragMode = handle;
                                dragStartX = pos.x;
                                dragStartY = pos.y;
                                dragStartGuideFigureArea = { ...(figures[selectedFigureIndex].area || {}) };
                                return;
                            }
                        }

                        const hitFigure = hitTestGuideFigure(curGuide, pos.x, pos.y);
                        if (hitFigure !== -1) {
                            selectedFigureIndex = hitFigure;
                            isDragging = true;
                            dragTarget = "guide";
                            dragMode = "move";
                            dragStartX = pos.x;
                            dragStartY = pos.y;
                            dragStartGuideFigureArea = { ...(figures[hitFigure].area || {}) };
                            renderAll();
                            return;
                        }
                    }

                    const hitGuide = hitTestGuide(pos.x, pos.y);
                    if (hitGuide !== -1) {
                        selectedGuideIndex = hitGuide;
                        selectedFigureIndex = -1;
                        renderAll();
                    } else {
                        selectedGuideIndex = -1;
                        selectedFigureIndex = -1;
                        renderAll();
                    }
                    return;
                }

                // Layer: FRAME
                if (activeEditLayer === "frame") {
                    if (selectedFrameIndex >= 0 && selectedFrameIndex < frames.length) {
                        const curFrame = frames[selectedFrameIndex];
                        const fa = curFrame.area || curFrame.shape;
                        const h = hitTestHandle(fa, pos.px, pos.py);
                        if (h) {
                            isDragging = true;
                            dragTarget = "frame";
                            dragMode = h;
                            dragStartX = pos.x;
                            dragStartY = pos.y;
                            dragStartFrameArea = { ...fa };
                            return;
                        }
                    }

                    const hitF = hitTestFrame(pos.x, pos.y);
                    if (hitF !== -1) {
                        selectedFrameIndex = hitF;
                        const fa = frames[hitF].area || frames[hitF].shape;
                        isDragging = true;
                        dragTarget = "frame";
                        dragMode = "move";
                        dragStartX = pos.x;
                        dragStartY = pos.y;
                        dragStartFrameArea = { ...fa };
                        renderAll();
                    } else {
                        selectedFrameIndex = -1;
                        renderAll();
                    }
                    return;
                }

                // Layer: CHARACTER
                if (activeEditLayer === "character") {
                    if (selectedInstanceId) {
                        const curInst = allInstances.find(i => i.instance_id === selectedInstanceId);
                        if (curInst) {
                            const h = hitTestHandle(curInst.area, pos.px, pos.py);
                            if (h) {
                                isDragging = true;
                                dragTarget = "character";
                                dragMode = h;
                                dragStartX = pos.x;
                                dragStartY = pos.y;
                                dragStartInstArea = { ...curInst.area };
                                return;
                            }
                        }
                    }

                    const hitChar = hitTestCharacter(pos.x, pos.y);
                    if (hitChar) {
                        selectedInstanceId = hitChar.instance_id;
                        const pSceneIdx = scenes.findIndex(s => s.scene_id === hitChar.scene_id);
                        if (pSceneIdx !== -1) selectedSceneIndex = pSceneIdx;
                        isDragging = true;
                        dragTarget = "character";
                        dragMode = "move";
                        dragStartX = pos.x;
                        dragStartY = pos.y;
                        dragStartInstArea = { ...hitChar.area };
                        renderAll();
                    } else {
                        selectedInstanceId = null;
                        renderAll();
                    }
                    return;
                }

                // Layer: SCENE (default)
                const curScene = scenes[selectedSceneIndex];
                if (curScene) {
                    const handle = hitTestHandle(curScene.area, pos.px, pos.py);
                    if (handle) {
                        isDragging = true;
                        dragTarget = "scene";
                        dragMode = handle;
                        dragStartX = pos.x;
                        dragStartY = pos.y;
                        dragStartSceneArea = { ...curScene.area };
                        dragStartChildAreas = allInstances
                            .filter(i => i.scene_id === curScene.scene_id)
                            .map(i => ({ id: i.instance_id, area: { ...i.area } }));
                        return;
                    }
                }

                const hitIdx = hitTestScene(pos.x, pos.y);
                if (hitIdx !== -1) {
                    selectedSceneIndex = hitIdx;
                    isDragging = true;
                    dragTarget = "scene";
                    dragMode = "move";
                    dragStartX = pos.x;
                    dragStartY = pos.y;
                    dragStartSceneArea = { ...scenes[hitIdx].area };
                    dragStartChildAreas = allInstances
                        .filter(i => i.scene_id === scenes[hitIdx].scene_id)
                        .map(i => ({ id: i.instance_id, area: { ...i.area } }));
                    renderAll();
                } else {
                    renderAll();
                }
            };

            const onWindowMouseMove = (e) => {
                if (!isDragging) return;
                const pos = getCanvasNormPos(e);
                const dx = pos.x - dragStartX;
                const dy = pos.y - dragStartY;
                const scenes = getScenes();
                const allInstances = getCharacterInstances();

                if (dragTarget === "guide") {
                    const guides = getGuides();
                    const guide = guides[selectedGuideIndex];
                    const figure = guide?.figure_regions?.[selectedFigureIndex];
                    const placement = guide?.placement;
                    if (!figure || !placement || !dragStartGuideFigureArea || placement.w <= 0 || placement.h <= 0) return;
                    const localDx = dx / placement.w;
                    const localDy = dy / placement.h;
                    if (dragMode === "move") {
                        const next = clampGuideFigureDrag(dragStartGuideFigureArea, localDx, localDy);
                        figure.area.x = next.x;
                        figure.area.y = next.y;
                    } else {
                        figure.area = resizeGuideFigure(dragStartGuideFigureArea, dragMode, localDx, localDy);
                    }
                    renderCanvas();
                    return;
                }

                if (dragTarget === "frame") {
                    const frames = getVisualFrames();
                    const curFrame = frames[selectedFrameIndex];
                    if (!curFrame || !dragStartFrameArea) return;
                    const b = curFrame.area || curFrame.shape;

                    if (dragMode === "move") {
                        const newPos = clampFrameDrag(dragStartFrameArea, dx, dy);
                        b.x = newPos.x;
                        b.y = newPos.y;
                    } else {
                        const newGeom = resizeFrame(dragStartFrameArea, dragMode, dx, dy);
                        b.x = newGeom.x;
                        b.y = newGeom.y;
                        b.w = newGeom.w;
                        b.h = newGeom.h;
                    }
                    renderCanvas();
                    return;
                }

                if (dragTarget === "character") {
                    const curInst = allInstances.find(i => i.instance_id === selectedInstanceId);
                    if (!curInst || !dragStartInstArea) return;
                    const b = curInst.area;
                    const parentScene = scenes.find(s => s.scene_id === curInst.scene_id);
                    const sb = parentScene ? parentScene.area : { x: 0, y: 0, w: 1, h: 1 };

                    if (dragMode === "move") {
                        let nx = dragStartInstArea.x + dx;
                        let ny = dragStartInstArea.y + dy;
                        nx = Math.max(sb.x, Math.min(sb.x + sb.w - dragStartInstArea.w, nx));
                        ny = Math.max(sb.y, Math.min(sb.y + sb.h - dragStartInstArea.h, ny));
                        b.x = parseFloat(nx.toFixed(4));
                        b.y = parseFloat(ny.toFixed(4));
                    } else if (dragMode === "se") {
                        const nw = Math.max(0.04, Math.min(sb.x + sb.w - dragStartInstArea.x, dragStartInstArea.w + dx));
                        const nh = Math.max(0.04, Math.min(sb.y + sb.h - dragStartInstArea.y, dragStartInstArea.h + dy));
                        b.w = parseFloat(nw.toFixed(4));
                        b.h = parseFloat(nh.toFixed(4));
                    } else if (dragMode === "nw") {
                        const maxRight = dragStartInstArea.x + dragStartInstArea.w;
                        const maxBottom = dragStartInstArea.y + dragStartInstArea.h;
                        const nx = Math.max(sb.x, Math.min(maxRight - 0.04, dragStartInstArea.x + dx));
                        const ny = Math.max(sb.y, Math.min(maxBottom - 0.04, dragStartInstArea.y + dy));
                        b.x = parseFloat(nx.toFixed(4));
                        b.y = parseFloat(ny.toFixed(4));
                        b.w = parseFloat((maxRight - nx).toFixed(4));
                        b.h = parseFloat((maxBottom - ny).toFixed(4));
                    } else if (dragMode === "ne") {
                        const maxBottom = dragStartInstArea.y + dragStartInstArea.h;
                        const nw = Math.max(0.04, Math.min(sb.x + sb.w - dragStartInstArea.x, dragStartInstArea.w + dx));
                        const ny = Math.max(sb.y, Math.min(maxBottom - 0.04, dragStartInstArea.y + dy));
                        b.y = parseFloat(ny.toFixed(4));
                        b.w = parseFloat(nw.toFixed(4));
                        b.h = parseFloat((maxBottom - ny).toFixed(4));
                    } else if (dragMode === "sw") {
                        const maxRight = dragStartInstArea.x + dragStartInstArea.w;
                        const nx = Math.max(sb.x, Math.min(maxRight - 0.04, dragStartInstArea.x + dx));
                        const nh = Math.max(0.04, Math.min(sb.y + sb.h - dragStartInstArea.y, dragStartInstArea.h + dy));
                        b.x = parseFloat(nx.toFixed(4));
                        b.w = parseFloat((maxRight - nx).toFixed(4));
                        b.h = parseFloat(nh.toFixed(4));
                    }
                    renderCanvas();
                    return;
                }

                if (dragTarget === "scene") {
                    if (!dragStartSceneArea || selectedSceneIndex < 0 || selectedSceneIndex >= scenes.length) return;
                    const curScene = scenes[selectedSceneIndex];
                    const sb = curScene.area;

                    if (dragMode === "move") {
                        let newX = dragStartSceneArea.x + dx;
                        let newY = dragStartSceneArea.y + dy;
                        newX = Math.max(0, Math.min(1 - dragStartSceneArea.w, newX));
                        newY = Math.max(0, Math.min(1 - dragStartSceneArea.h, newY));
                        const effectiveDx = newX - dragStartSceneArea.x;
                        const effectiveDy = newY - dragStartSceneArea.y;

                        sb.x = parseFloat(newX.toFixed(4));
                        sb.y = parseFloat(newY.toFixed(4));

                        dragStartChildAreas.forEach(cRecord => {
                            const inst = allInstances.find(i => i.instance_id === cRecord.id);
                            if (inst && inst.area) {
                                inst.area.x = parseFloat((cRecord.area.x + effectiveDx).toFixed(4));
                                inst.area.y = parseFloat((cRecord.area.y + effectiveDy).toFixed(4));
                            }
                        });
                    } else {
                        if (dragMode === "se") {
                            const nw = Math.max(0.1, Math.min(1 - dragStartSceneArea.x, dragStartSceneArea.w + dx));
                            const nh = Math.max(0.08, Math.min(1 - dragStartSceneArea.y, dragStartSceneArea.h + dy));
                            sb.w = parseFloat(nw.toFixed(4));
                            sb.h = parseFloat(nh.toFixed(4));
                        } else if (dragMode === "nw") {
                            const maxRight = dragStartSceneArea.x + dragStartSceneArea.w;
                            const maxBottom = dragStartSceneArea.y + dragStartSceneArea.h;
                            const nx = Math.max(0, Math.min(maxRight - 0.1, dragStartSceneArea.x + dx));
                            const ny = Math.max(0, Math.min(maxBottom - 0.08, dragStartSceneArea.y + dy));
                            sb.x = parseFloat(nx.toFixed(4));
                            sb.y = parseFloat(ny.toFixed(4));
                            sb.w = parseFloat((maxRight - nx).toFixed(4));
                            sb.h = parseFloat((maxBottom - ny).toFixed(4));
                        } else if (dragMode === "ne") {
                            const maxBottom = dragStartSceneArea.y + dragStartSceneArea.h;
                            const nw = Math.max(0.1, Math.min(1 - dragStartSceneArea.x, dragStartSceneArea.w + dx));
                            const ny = Math.max(0.08, Math.min(maxBottom - 0.08, dragStartSceneArea.y + dy));
                            sb.y = parseFloat(ny.toFixed(4));
                            sb.w = parseFloat(nw.toFixed(4));
                            sb.h = parseFloat((maxBottom - ny).toFixed(4));
                        } else if (dragMode === "sw") {
                            const maxRight = dragStartSceneArea.x + dragStartSceneArea.w;
                            const nx = Math.max(0, Math.min(maxRight - 0.1, dragStartSceneArea.x + dx));
                            const nh = Math.max(0.08, Math.min(1 - dragStartSceneArea.y, dragStartSceneArea.h + dy));
                            sb.x = parseFloat(nx.toFixed(4));
                            sb.w = parseFloat((maxRight - nx).toFixed(4));
                            sb.h = parseFloat(nh.toFixed(4));
                        }

                        dragStartChildAreas.forEach(cRecord => {
                            const inst = allInstances.find(i => i.instance_id === cRecord.id);
                            if (inst && inst.area) {
                                const relX = (cRecord.area.x - dragStartSceneArea.x) / Math.max(dragStartSceneArea.w, 1e-6);
                                const relY = (cRecord.area.y - dragStartSceneArea.y) / Math.max(dragStartSceneArea.h, 1e-6);
                                const relW = cRecord.area.w / Math.max(dragStartSceneArea.w, 1e-6);
                                const relH = cRecord.area.h / Math.max(dragStartSceneArea.h, 1e-6);

                                inst.area.x = parseFloat((sb.x + relX * sb.w).toFixed(4));
                                inst.area.y = parseFloat((sb.y + relY * sb.h).toFixed(4));
                                inst.area.w = parseFloat((relW * sb.w).toFixed(4));
                                inst.area.h = parseFloat((relH * sb.h).toFixed(4));
                            }
                        });
                    }
                    renderCanvas();
                }
            };

            const onWindowMouseUp = () => {
                if (isDragging) {
                    isDragging = false;
                    dragTarget = "none";
                    dragMode = "none";
                    dragStartSceneArea = null;
                    dragStartInstArea = null;
                    dragStartFrameArea = null;
                    dragStartGuideFigureArea = null;
                    dragStartChildAreas = [];
                    syncToWidgets();
                    renderAll();
                }
            };

            window.addEventListener("mousemove", onWindowMouseMove);
            window.addEventListener("mouseup", onWindowMouseUp);

            const origOnRemoved = node.onRemoved;
            node.onRemoved = function () {
                window.removeEventListener("mousemove", onWindowMouseMove);
                window.removeEventListener("mouseup", onWindowMouseUp);
                guideFileInput.remove();
                if (origOnRemoved) origOnRemoved.apply(this, arguments);
            };

            const resWidget = node.widgets.find(w => w.name === "resolution");
            if (resWidget) {
                const origCb = resWidget.callback;
                resWidget.callback = function (v) {
                    if (origCb) origCb.apply(this, arguments);
                    const res = parseResolution(v);
                    const p = getPage();
                    p.width_px = res.width;
                    p.height_px = res.height;
                    syncToWidgets();
                    renderCanvas();
                };
            }

            const styleWidget = node.widgets.find(w => w.name === "style_template");
            if (styleWidget) {
                const origCb = styleWidget.callback;
                styleWidget.callback = function (v) {
                    if (origCb) origCb.apply(this, arguments);
                    const p = getPage();
                    if (!p.metadata) p.metadata = {};
                    p.metadata.style_template = v;
                    const tmpl = STYLE_PRESETS[v];
                    if (tmpl) {
                        p.style_prompt = tmpl.prompt;
                        p.style_negative_prompt = tmpl.negative;
                    }
                    syncToWidgets();
                };
            }

            const seedWidget = node.widgets.find(w => w.name === "seed");
            if (seedWidget) {
                const origCb = seedWidget.callback;
                seedWidget.callback = function (v) {
                    if (origCb) origCb.apply(this, arguments);
                    const p = getPage();
                    if (!p.generation) p.generation = {};
                    p.generation.seed = parseInt(v, 10) || 0;
                    syncToWidgets();
                };
            }

            node.addDOMWidget("minimum_hand_scene_editor_ui", "ui", container);

            node._tegakiRestoreFromWidgets();
            syncToWidgets();
            renderAll();

            return r;
        };
    }
});
