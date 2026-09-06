import { app } from "../../scripts/app.js";

const SCENE_PALETTE = [
    { name: "Scene 1", hex: "#e53935", rgb: [229, 57, 53] },
    { name: "Scene 2", hex: "#1e88e5", rgb: [30, 136, 229] },
    { name: "Scene 3", hex: "#43a047", rgb: [67, 160, 71] },
    { name: "Scene 4", hex: "#fb8c00", rgb: [251, 140, 0] },
    { name: "Scene 5", hex: "#8e24aa", rgb: [142, 36, 170] },
    { name: "Scene 6", hex: "#00acc1", rgb: [0, 172, 193] },
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
            if (this._tegakiRestoreFromWidgets) {
                this._tegakiRestoreFromWidgets();
            }
            return r;
        };

        const onNodeCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function () {
            const r = onNodeCreated ? onNodeCreated.apply(this, arguments) : undefined;

            const node = this;
            node.setSize([540, 840]);

            let doc = createDefaultDoc();
            let selectedSceneIndex = 0;
            let isDragging = false;
            let dragMode = "none"; // 'move' | 'nw' | 'ne' | 'se' | 'sw'
            let dragStartX = 0;
            let dragStartY = 0;
            let dragStartArea = null;

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
                    <span style="background: #3b82f6; color: #fff; padding: 2px 6px; border-radius: 4px; font-size: 10px;">M1</span>
                    <span>Scene-Only Minimum-Hand Editor</span>
                </div>
                <div id="scene-counter" style="color: #a1a1aa; font-size: 11px;">Scenes: 2 / 6</div>
            `;
            container.appendChild(header);

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

                // Stable unique ID generation (Finding G)
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
                    prompt: `scene ${orderNum} content prompt`,
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
                syncToWidgets();
                renderAll();
            });

            const btnDeleteScene = createButton("- Remove Scene", "Remove selected scene rectangle (min 1)", () => {
                const scenes = getScenes();
                if (scenes.length <= 1) return;
                scenes.splice(selectedSceneIndex, 1);
                scenes.forEach((s, i) => {
                    s.order = i + 1;
                });
                if (selectedSceneIndex >= scenes.length) {
                    selectedSceneIndex = scenes.length - 1;
                }
                syncToWidgets();
                renderAll();
            });

            const btnResetLayout = createButton("Reset 2-Scene", "Reset to canonical 2-scene vertical layout", () => {
                const resWidget = node.widgets.find(w => w.name === "resolution");
                const styleWidget = node.widgets.find(w => w.name === "style_template");
                const seedWidget = node.widgets.find(w => w.name === "seed");
                doc = createDefaultDoc(
                    resWidget ? resWidget.value : "Portrait 832x1216",
                    styleWidget ? styleWidget.value : "Manga Monochrome",
                    seedWidget ? seedWidget.value : 42
                );
                selectedSceneIndex = 0;
                syncToWidgets();
                renderAll();
            });

            toolbar.appendChild(btnAddScene);
            toolbar.appendChild(btnDeleteScene);
            toolbar.appendChild(btnResetLayout);
            container.appendChild(toolbar);

            // Scene Prompt Inspector
            const inspector = document.createElement("div");
            inspector.style.cssText = `
                display: flex;
                flex-direction: column;
                gap: 6px;
                background: #27272a;
                padding: 8px;
                border-radius: 6px;
                border: 1px solid #3f3f46;
            `;

            const inspectorHeader = document.createElement("div");
            inspectorHeader.style.cssText = "display: flex; justify-content: space-between; align-items: center;";

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

            inspectorHeader.appendChild(sceneBadge);
            inspectorHeader.appendChild(sceneNameInput);
            inspector.appendChild(inspectorHeader);

            const promptTextarea = document.createElement("textarea");
            promptTextarea.rows = 4;
            promptTextarea.placeholder = "Enter scene visual prompt (e.g. 1boy in classroom, looking outside)...";
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
            inspector.appendChild(promptTextarea);
            container.appendChild(inspector);

            function getSceneColor(idx) {
                return SCENE_PALETTE[idx % SCENE_PALETTE.length];
            }

            function renderInspector() {
                const scenes = getScenes();
                const countSpan = container.querySelector("#scene-counter");
                if (countSpan) countSpan.textContent = `Scenes: ${scenes.length} / 6`;

                btnAddScene.disabled = scenes.length >= 6;
                btnDeleteScene.disabled = scenes.length <= 1;

                const curScene = scenes[selectedSceneIndex];
                if (!curScene) {
                    sceneBadge.innerHTML = `<span style="color: #71717a;">No scene selected</span>`;
                    sceneNameInput.value = "";
                    promptTextarea.value = "";
                    return;
                }

                const col = getSceneColor(selectedSceneIndex);
                sceneBadge.innerHTML = `
                    <span style="display:inline-block; width:10px; height:10px; border-radius:50%; background:${col.hex};"></span>
                    <span>Scene ${selectedSceneIndex + 1} (${curScene.scene_id})</span>
                `;
                sceneNameInput.value = curScene.name || "";
                promptTextarea.value = curScene.prompt || "";
            }

            function renderCanvas() {
                const cw = canvas.width;
                const ch = canvas.height;

                ctx.clearRect(0, 0, cw, ch);

                // Background
                ctx.fillStyle = "#ffffff";
                ctx.fillRect(0, 0, cw, ch);

                // Grid lines
                ctx.strokeStyle = "#e5e7eb";
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
                scenes.forEach((sc, idx) => {
                    const b = sc.area || { x: 0, y: 0, w: 1, h: 1 };
                    const col = getSceneColor(idx);
                    const isSelected = (idx === selectedSceneIndex);

                    const rx = b.x * cw;
                    const ry = b.y * ch;
                    const rw = b.w * cw;
                    const rh = b.h * ch;

                    // Fill
                    ctx.fillStyle = isSelected ? `rgba(${col.rgb.join(",")}, 0.35)` : `rgba(${col.rgb.join(",")}, 0.20)`;
                    ctx.fillRect(rx, ry, rw, rh);

                    // Stroke
                    ctx.strokeStyle = col.hex;
                    ctx.lineWidth = isSelected ? 3 : 1.5;
                    ctx.strokeRect(rx, ry, rw, rh);

                    // Label badge
                    const label = `Scene ${idx + 1}: ${sc.name || sc.scene_id}`;
                    ctx.font = "bold 11px system-ui, sans-serif";
                    const tw = ctx.measureText(label).width;

                    ctx.fillStyle = col.hex;
                    ctx.fillRect(rx, ry, tw + 10, 18);

                    ctx.fillStyle = "#ffffff";
                    ctx.fillText(label, rx + 5, ry + 13);

                    // Handles
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
                renderInspector();
                renderCanvas();
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
            }

            node._tegakiRestoreFromWidgets = function () {
                const docWidget = node.widgets.find(w => w.name === "document_json");
                if (docWidget && docWidget.value && docWidget.value.trim() !== "") {
                    try {
                        const parsed = JSON.parse(docWidget.value);
                        if (parsed && parsed.schema_id === "TEGAKI_AUTHORING_DOCUMENT" && Array.isArray(parsed.pages)) {
                            // Migrate any legacy dimensions if present
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

            function hitTestHandle(scene, px, py) {
                const b = scene.area || { x: 0, y: 0, w: 1, h: 1 };
                const cw = canvas.width;
                const ch = canvas.height;
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

            canvas.onmousedown = (e) => {
                const pos = getCanvasNormPos(e);
                const scenes = getScenes();
                const curScene = scenes[selectedSceneIndex];

                if (curScene) {
                    const handle = hitTestHandle(curScene, pos.px, pos.py);
                    if (handle) {
                        isDragging = true;
                        dragMode = handle;
                        dragStartX = pos.x;
                        dragStartY = pos.y;
                        dragStartArea = { ...curScene.area };
                        return;
                    }
                }

                const hitIdx = hitTestScene(pos.x, pos.y);
                if (hitIdx !== -1) {
                    selectedSceneIndex = hitIdx;
                    isDragging = true;
                    dragMode = "move";
                    dragStartX = pos.x;
                    dragStartY = pos.y;
                    dragStartArea = { ...scenes[hitIdx].area };
                    renderAll();
                } else {
                    renderCanvas();
                }
            };

            const onWindowMouseMove = (e) => {
                const scenes = getScenes();
                if (!isDragging || !dragStartArea || selectedSceneIndex < 0 || selectedSceneIndex >= scenes.length) return;
                const pos = getCanvasNormPos(e);
                const dx = pos.x - dragStartX;
                const dy = pos.y - dragStartY;
                const b = scenes[selectedSceneIndex].area;

                if (dragMode === "move") {
                    let newX = dragStartArea.x + dx;
                    let newY = dragStartArea.y + dy;
                    newX = Math.max(0, Math.min(1 - dragStartArea.w, newX));
                    newY = Math.max(0, Math.min(1 - dragStartArea.h, newY));
                    b.x = parseFloat(newX.toFixed(4));
                    b.y = parseFloat(newY.toFixed(4));
                } else if (dragMode === "se") {
                    const newW = Math.max(0.1, Math.min(1 - dragStartArea.x, dragStartArea.w + dx));
                    const newH = Math.max(0.08, Math.min(1 - dragStartArea.y, dragStartArea.h + dy));
                    b.w = parseFloat(newW.toFixed(4));
                    b.h = parseFloat(newH.toFixed(4));
                } else if (dragMode === "nw") {
                    const maxRight = dragStartArea.x + dragStartArea.w;
                    const maxBottom = dragStartArea.y + dragStartArea.h;
                    const newX = Math.max(0, Math.min(maxRight - 0.1, dragStartArea.x + dx));
                    const newY = Math.max(0, Math.min(maxBottom - 0.08, dragStartArea.y + dy));
                    b.x = parseFloat(newX.toFixed(4));
                    b.y = parseFloat(newY.toFixed(4));
                    b.w = parseFloat((maxRight - newX).toFixed(4));
                    b.h = parseFloat((maxBottom - newY).toFixed(4));
                } else if (dragMode === "ne") {
                    const maxBottom = dragStartArea.y + dragStartArea.h;
                    const newW = Math.max(0.1, Math.min(1 - dragStartArea.x, dragStartArea.w + dx));
                    const newY = Math.max(0, Math.min(maxBottom - 0.08, dragStartArea.y + dy));
                    b.y = parseFloat(newY.toFixed(4));
                    b.w = parseFloat(newW.toFixed(4));
                    b.h = parseFloat((maxBottom - newY).toFixed(4));
                } else if (dragMode === "sw") {
                    const maxRight = dragStartArea.x + dragStartArea.w;
                    const newX = Math.max(0, Math.min(maxRight - 0.1, dragStartArea.x + dx));
                    const newH = Math.max(0.08, Math.min(1 - dragStartArea.y, dragStartArea.h + dy));
                    b.x = parseFloat(newX.toFixed(4));
                    b.w = parseFloat((maxRight - newX).toFixed(4));
                    b.h = parseFloat(newH.toFixed(4));
                }

                renderCanvas();
            };

            const onWindowMouseUp = () => {
                if (isDragging) {
                    isDragging = false;
                    dragMode = "none";
                    dragStartArea = null;
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
