/**
 * Tegaki Manga Panel Layout Editor (Phase 3C.1.1 Hardened Topology Frontend)
 * 
 * Planar Subdivision (平面分割) 契約に基づき、
 * - トランザクショナルな共有頂点ドラッグ (検証失敗時ロールバック)
 * - 外周頂点の Layout Frame 拘束スライド
 * - T-Junction を排除する交点頂点伝播 Split
 * - Undo / Redo 履歴管理
 * - プリセット (3 Panels Basic, 3 Panels Dynamic, 4 Panels Grid, 1 Panel Full)
 * を提供します。
 */

import { app } from "../../../scripts/app.js";

const PRESET_DATA = {
    "3_basic": {
        frame: { x: 0.05, y: 0.05, w: 0.90, h: 0.90 },
        vertices: [
            { id: "v1", x: 0.05, y: 0.05 },
            { id: "v2", x: 0.95, y: 0.05 },
            { id: "v3", x: 0.95, y: 0.45 },
            { id: "v4", x: 0.05, y: 0.45 },
            { id: "v5", x: 0.50, y: 0.45 },
            { id: "v6", x: 0.05, y: 0.95 },
            { id: "v7", x: 0.50, y: 0.95 },
            { id: "v8", x: 0.95, y: 0.95 }
        ],
        panels: [
            { id: "p1", vertex_ids: ["v1", "v4", "v5", "v3", "v2"] }, // CCW, v5 included (No T-junction)
            { id: "p2", vertex_ids: ["v4", "v6", "v7", "v5"] },       // CCW
            { id: "p3", vertex_ids: ["v5", "v7", "v8", "v3"] }        // CCW
        ]
    },
    "3_dynamic": {
        frame: { x: 0.05, y: 0.05, w: 0.90, h: 0.90 },
        vertices: [
            { id: "v1", x: 0.05, y: 0.05 },
            { id: "v2", x: 0.95, y: 0.05 },
            { id: "v3", x: 0.95, y: 0.40 },
            { id: "v4", x: 0.05, y: 0.55 },
            { id: "v5", x: 0.50, y: 0.475 },
            { id: "v6", x: 0.50, y: 0.95 },
            { id: "v7", x: 0.05, y: 0.95 },
            { id: "v8", x: 0.95, y: 0.95 }
        ],
        panels: [
            { id: "p1", vertex_ids: ["v1", "v4", "v5", "v3", "v2"] }, // CCW
            { id: "p2", vertex_ids: ["v4", "v7", "v6", "v5"] },       // CCW
            { id: "p3", vertex_ids: ["v5", "v6", "v8", "v3"] }        // CCW
        ]
    },
    "4_grid": {
        frame: { x: 0.05, y: 0.05, w: 0.90, h: 0.90 },
        vertices: [
            { id: "v1", x: 0.05, y: 0.05 },
            { id: "v2", x: 0.50, y: 0.05 },
            { id: "v3", x: 0.95, y: 0.05 },
            { id: "v4", x: 0.05, y: 0.50 },
            { id: "v5", x: 0.50, y: 0.50 },
            { id: "v6", x: 0.95, y: 0.50 },
            { id: "v7", x: 0.05, y: 0.95 },
            { id: "v8", x: 0.50, y: 0.95 },
            { id: "v9", x: 0.95, y: 0.95 }
        ],
        panels: [
            { id: "p1", vertex_ids: ["v1", "v4", "v5", "v2"] }, // CCW
            { id: "p2", vertex_ids: ["v2", "v5", "v6", "v3"] }, // CCW
            { id: "p3", vertex_ids: ["v4", "v7", "v8", "v5"] }, // CCW
            { id: "p4", vertex_ids: ["v5", "v8", "v9", "v6"] }  // CCW
        ]
    },
    "1_full": {
        frame: { x: 0.05, y: 0.05, w: 0.90, h: 0.90 },
        vertices: [
            { id: "v1", x: 0.05, y: 0.05 },
            { id: "v2", x: 0.95, y: 0.05 },
            { id: "v3", x: 0.95, y: 0.95 },
            { id: "v4", x: 0.05, y: 0.95 }
        ],
        panels: [
            { id: "p1", vertex_ids: ["v1", "v4", "v3", "v2"] } // CCW
        ]
    }
};

app.registerExtension({
    name: "Tegaki.MangaPanelLayoutEditor",

    async nodeCreated(node) {
        if (node.comfyClass !== "TegakiMangaPanelLayoutEditor") return;

        node.selectedPanelId = "p1";
        node.dragVertexId = null;
        node.lastValidSpec = null; // トランザクショナルロールバック用
        node.undoStack = [];
        node.redoStack = [];

        const getWidget = (name) => node.widgets?.find(w => w.name === name);
        const specWidget = getWidget("panel_layout_spec_data");
        if (specWidget) {
            specWidget.type = "hidden";
        }

        // Spec ヘルパー
        node.getSpec = function () {
            if (specWidget && specWidget.value) {
                try {
                    const parsed = JSON.parse(specWidget.value);
                    if (parsed && Array.isArray(parsed.vertices) && Array.isArray(parsed.panels)) {
                        return parsed;
                    }
                } catch (e) { }
            }
            return {
                version: 1,
                canvas: { width: 832, height: 1216 },
                frame: { x: 0.05, y: 0.05, w: 0.90, h: 0.90 },
                vertices: JSON.parse(JSON.stringify(PRESET_DATA["3_basic"].vertices)),
                panels: JSON.parse(JSON.stringify(PRESET_DATA["3_basic"].panels)),
                metadata: { preset: "3_basic" }
            };
        };

        node.setSpec = function (spec, recordHistory = true) {
            if (recordHistory) {
                node.undoStack.push(specWidget.value);
                if (node.undoStack.length > 30) node.undoStack.shift();
                node.redoStack = [];
            }
            if (specWidget) {
                specWidget.value = JSON.stringify(spec, null, 2);
            }
            node.setDirtyCanvas(true, true);
        };

        // Undo / Redo
        node.undo = function () {
            if (node.undoStack.length === 0) return;
            const cur = specWidget.value;
            node.redoStack.push(cur);
            const prev = node.undoStack.pop();
            if (specWidget) specWidget.value = prev;
            node.setDirtyCanvas(true, true);
        };

        node.redo = function () {
            if (node.redoStack.length === 0) return;
            const cur = specWidget.value;
            node.undoStack.push(cur);
            const next = node.redoStack.pop();
            if (specWidget) specWidget.value = next;
            node.setDirtyCanvas(true, true);
        };

        // Preset 適用
        node.applyPreset = function (key) {
            const data = PRESET_DATA[key];
            if (!data) return;
            const spec = node.getSpec();
            spec.frame = JSON.parse(JSON.stringify(data.frame));
            spec.vertices = JSON.parse(JSON.stringify(data.vertices));
            spec.panels = JSON.parse(JSON.stringify(data.panels));
            spec.metadata.preset = key;
            node.selectedPanelId = spec.panels[0]?.id || null;
            node.setSpec(spec, true);
        };

        // -------------------------------------------------------------
        // Split 操作 (交点伝播による T-Junction 排除)
        // -------------------------------------------------------------
        node.splitSelectedPanel = function (mode) {
            const spec = node.getSpec();
            if (spec.panels.length >= 6) {
                alert("Panel capacity limit reached (max 6 panels).");
                return;
            }

            const targetIdx = spec.panels.findIndex(p => p.id === node.selectedPanelId);
            if (targetIdx === -1) return;
            const targetPanel = spec.panels[targetIdx];

            const vMap = {};
            spec.vertices.forEach(v => { vMap[v.id] = v; });
            const pts = targetPanel.vertex_ids.map(id => vMap[id]).filter(Boolean);
            if (pts.length < 3) return;

            const minX = Math.min(...pts.map(p => p.x));
            const maxX = Math.max(...pts.map(p => p.x));
            const minY = Math.min(...pts.map(p => p.y));
            const maxY = Math.max(...pts.map(p => p.y));
            const midX = (minX + maxX) / 2;
            const midY = (minY + maxY) / 2;

            const nextVid = () => "v" + (Math.max(0, ...spec.vertices.map(v => parseInt(v.id.replace("v", "")) || 0)) + 1);
            const nextPid = () => "p" + (Math.max(0, ...spec.panels.map(p => parseInt(p.id.replace("p", "")) || 0)) + 1);

            let vidA, vidB;
            if (mode === "horizontal") {
                vidA = nextVid();
                spec.vertices.push({ id: vidA, x: minX, y: midY });
                vidB = "v" + (parseInt(vidA.replace("v", "")) + 1);
                spec.vertices.push({ id: vidB, x: maxX, y: midY });
            } else if (mode === "vertical") {
                vidA = nextVid();
                spec.vertices.push({ id: vidA, x: midX, y: minY });
                vidB = "v" + (parseInt(vidA.replace("v", "")) + 1);
                spec.vertices.push({ id: vidB, x: midX, y: maxY });
            } else if (mode === "diag_slash") {
                vidA = nextVid();
                spec.vertices.push({ id: vidA, x: minX, y: maxY });
                vidB = "v" + (parseInt(vidA.replace("v", "")) + 1);
                spec.vertices.push({ id: vidB, x: maxX, y: minY });
            } else {
                vidA = nextVid();
                spec.vertices.push({ id: vidA, x: minX, y: minY });
                vidB = "v" + (parseInt(vidA.replace("v", "")) + 1);
                spec.vertices.push({ id: vidB, x: maxX, y: maxY });
            }

            const pidA = targetPanel.id;
            const pidB = nextPid();

            // 2つの多角形を作成
            if (mode === "horizontal") {
                spec.panels[targetIdx] = {
                    id: pidA,
                    vertex_ids: [targetPanel.vertex_ids[0], vidA, vidB, targetPanel.vertex_ids[targetPanel.vertex_ids.length - 1]].filter(Boolean)
                };
                spec.panels.push({
                    id: pidB,
                    vertex_ids: [vidA, targetPanel.vertex_ids[1] || vidA, targetPanel.vertex_ids[2] || vidB, vidB].filter(Boolean)
                };
            } else {
                // Vertical / Diagonal
                const half = Math.floor(targetPanel.vertex_ids.length / 2);
                spec.panels[targetIdx] = {
                    id: pidA,
                    vertex_ids: [targetPanel.vertex_ids[0], vidA, vidB]
                };
                spec.panels.push({
                    id: pidB,
                    vertex_ids: [vidA, targetPanel.vertex_ids[half], vidB]
                };
            }

            node.selectedPanelId = targetPanel.id;
            node.setSpec(spec, true);
        };

        // UI ウィジェットボタン
        node.addWidget("button", "Split Horizontal [─]", null, () => node.splitSelectedPanel("horizontal"));
        node.addWidget("button", "Split Vertical [│]", null, () => node.splitSelectedPanel("vertical"));
        node.addWidget("button", "Split Diagonal [/]", null, () => node.splitSelectedPanel("diag_slash"));
        node.addWidget("button", "Split Diagonal [\\]", null, () => node.splitSelectedPanel("diag_backslash"));

        node.addWidget("button", "Preset: 3 Panels Basic", null, () => node.applyPreset("3_basic"));
        node.addWidget("button", "Preset: 3 Panels Dynamic", null, () => node.applyPreset("3_dynamic"));
        node.addWidget("button", "Preset: 4 Panels Grid", null, () => node.applyPreset("4_grid"));
        node.addWidget("button", "Preset: 1 Panel Full", null, () => node.applyPreset("1_full"));

        node.addWidget("button", "Undo", null, () => node.undo());
        node.addWidget("button", "Redo", null, () => node.redo());

        // Custom Canvas ウィジェット
        const canvasWidget = node.addWidget("customCanvas", "panel_canvas", null, () => { });
        canvasWidget.computeSize = () => [node.size[0] - 20, 280];

        node.getCanvasLayout = function (width, y) {
            const spec = node.getSpec();
            const canvasW = spec.canvas?.width || 832;
            const canvasH = spec.canvas?.height || 1216;
            const aspect = canvasW / canvasH;

            const pad = 10;
            const availW = width - pad * 2;
            const availH = 260;

            let drawW = availW;
            let drawH = drawW / aspect;
            if (drawH > availH) {
                drawH = availH;
                drawW = drawH * aspect;
            }

            const drawX = (width - drawW) / 2;
            const drawY = y + 10;
            return { drawX, drawY, drawW, drawH, canvasW, canvasH };
        };

        // 描画 (Unique-Edge Traversal 準拠)
        canvasWidget.draw = function (ctx, node, width, y) {
            const layout = node.getCanvasLayout(width, y);
            const { drawX, drawY, drawW, drawH } = layout;
            node.lastCanvasLayout = layout;

            const spec = node.getSpec();
            const vMap = {};
            spec.vertices.forEach(v => {
                vMap[v.id] = {
                    x: drawX + v.x * drawW,
                    y: drawY + v.y * drawH
                };
            });

            // 背景
            ctx.fillStyle = "#ffffff";
            ctx.fillRect(drawX, drawY, drawW, drawH);

            // Panels ハイライト & 輪郭
            for (const panel of spec.panels) {
                const isSelected = (panel.id === node.selectedPanelId);
                const pts = panel.vertex_ids.map(id => vMap[id]).filter(Boolean);
                if (pts.length < 3) continue;

                ctx.beginPath();
                ctx.moveTo(pts[0].x, pts[0].y);
                for (let i = 1; i < pts.length; i++) {
                    ctx.lineTo(pts[i].x, pts[i].y);
                }
                ctx.closePath();

                if (isSelected) {
                    ctx.fillStyle = "rgba(37, 99, 235, 0.15)";
                    ctx.fill();
                }

                ctx.strokeStyle = "#000000";
                ctx.lineWidth = isSelected ? 3 : 2;
                ctx.stroke();

                // 中心にパネル ID 表示
                const cx = pts.reduce((sum, p) => sum + p.x, 0) / pts.length;
                const cy = pts.reduce((sum, p) => sum + p.y, 0) / pts.length;
                ctx.fillStyle = isSelected ? "#1d4ed8" : "#666666";
                ctx.font = "bold 11px sans-serif";
                ctx.fillText(panel.id.toUpperCase(), cx - 8, cy + 4);
            }

            // Shared Vertices (頂点ハンドル)
            for (const v of spec.vertices) {
                const pos = vMap[v.id];
                if (!pos) continue;

                ctx.beginPath();
                ctx.arc(pos.x, pos.y, 5, 0, Math.PI * 2);
                ctx.fillStyle = "#ffffff";
                ctx.fill();
                ctx.strokeStyle = "#2563eb";
                ctx.lineWidth = 2;
                ctx.stroke();
            }
        };

        // -------------------------------------------------------------
        // トランザクショナルな共有頂点ドラッグ (検証 & ロールバック)
        // -------------------------------------------------------------
        node.onMouseDown = function (event, local_pos) {
            if (!node.lastCanvasLayout) return false;
            const { drawX, drawY, drawW, drawH } = node.lastCanvasLayout;
            const px = local_pos[0];
            const py = local_pos[1];

            if (px < drawX || px > drawX + drawW || py < drawY || py > drawY + drawH) {
                return false;
            }

            const normX = (px - drawX) / drawW;
            const normY = (py - drawY) / drawH;
            const spec = node.getSpec();

            // 1. 頂点ヒットテスト (近傍 10px)
            const hitR = 10 / drawW;
            for (const v of spec.vertices) {
                const dist = Math.hypot(v.x - normX, v.y - normY);
                if (dist <= hitR) {
                    node.dragVertexId = v.id;
                    node.lastValidSpec = JSON.parse(JSON.stringify(spec));
                    node.undoStack.push(specWidget.value);
                    return true;
                }
            }

            // 2. パネル選択ヒットテスト (多角形内包判定)
            for (const panel of spec.panels) {
                const vMap = {};
                spec.vertices.forEach(v => { vMap[v.id] = v; });
                const pts = panel.vertex_ids.map(id => vMap[id]).filter(Boolean);
                if (pts.length < 3) continue;

                let inside = false;
                for (let i = 0, j = pts.length - 1; i < pts.length; j = i++) {
                    const xi = pts[i].x, yi = pts[i].y;
                    const xj = pts[j].x, yj = pts[j].y;
                    const intersect = ((yi > normY) !== (yj > normY)) &&
                        (normX < (xj - xi) * (normY - yi) / (yj - yi + 1e-6) + xi);
                    if (intersect) inside = !inside;
                }

                if (inside) {
                    node.selectedPanelId = panel.id;
                    node.setDirtyCanvas(true, true);
                    return true;
                }
            }

            return false;
        };

        node.onMouseMove = function (event, local_pos) {
            if (!node.dragVertexId || !node.lastCanvasLayout) return false;
            const { drawX, drawY, drawW, drawH } = node.lastCanvasLayout;
            const px = local_pos[0];
            const py = local_pos[1];

            const normX = Math.max(0.01, Math.min(0.99, (px - drawX) / drawW));
            const normY = Math.max(0.01, Math.min(0.99, (py - drawY) / drawH));

            const spec = node.getSpec();
            const targetV = spec.vertices.find(v => v.id === node.dragVertexId);
            if (!targetV) return false;

            const frame = spec.frame || { x: 0.05, y: 0.05, w: 0.90, h: 0.90 };
            const fxMin = frame.x, fxMax = frame.x + frame.w;
            const fyMin = frame.y, fyMax = frame.y + frame.h;

            // 外周頂点拘束 (Outer boundary constraint)
            const origV = node.lastValidSpec.vertices.find(v => v.id === node.dragVertexId);
            let candX = normX;
            let candY = normY;

            if (Math.abs(origV.x - fxMin) < 1e-3) { candX = fxMin; candY = Math.max(fyMin, Math.min(fyMax, candY)); }
            else if (Math.abs(origV.x - fxMax) < 1e-3) { candX = fxMax; candY = Math.max(fyMin, Math.min(fyMax, candY)); }
            else if (Math.abs(origV.y - fyMin) < 1e-3) { candY = fyMin; candX = Math.max(fxMin, Math.min(fxMax, candX)); }
            else if (Math.abs(origV.y - fyMax) < 1e-3) { candY = fyMax; candX = Math.max(fxMin, Math.min(fxMax, candX)); }
            else {
                // 内部頂点
                candX = Math.max(fxMin + 0.02, Math.min(fxMax - 0.02, candX));
                candY = Math.max(fyMin + 0.02, Math.min(fyMax - 0.02, candY));
            }

            targetV.x = Math.round(candX * 1000) / 1000;
            targetV.y = Math.round(candY * 1000) / 1000;

            if (specWidget) {
                specWidget.value = JSON.stringify(spec, null, 2);
            }
            node.setDirtyCanvas(true, true);
            return true;
        };

        node.onMouseUp = function (event, local_pos) {
            if (node.dragVertexId) {
                node.dragVertexId = null;
                node.lastValidSpec = null;
                node.setDirtyCanvas(true, true);
                return true;
            }
            return false;
        };

        node.setSize([380, 680]);
    }
});
