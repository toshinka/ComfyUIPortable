/**
 * Tegaki Two Region Couple Editor (Phase 3C Oracle Frontend)
 * 
 * 2領域 (Region A / Region B) 専用の Rectangle Editor Canvas。
 * プリセットボタン (Horizontal, Vertical, Overlap, One Region A/B, Reset) を配備し、
 * TWO_REGION_SPEC (v1) とリアルタイムに同期します。
 */

import { app } from "../../../scripts/app.js";

const PALETTE = {
    A: { stroke: "#2563eb", fill: "rgba(37, 99, 235, 0.35)", active: "#1d4ed8", name: "Region A (Blue)" },
    B: { stroke: "#ea580c", fill: "rgba(234, 88, 12, 0.35)", active: "#c2410c", name: "Region B (Orange)" },
    bg: "#fcfaf2",
    grid: "#e5e0d8",
    handle: "#ffffff"
};

const PRESETS = {
    horizontal: [
        { id: "A", enabled: true, x: 0.05, y: 0.10, w: 0.42, h: 0.80 },
        { id: "B", enabled: true, x: 0.53, y: 0.10, w: 0.42, h: 0.80 }
    ],
    vertical: [
        { id: "A", enabled: true, x: 0.10, y: 0.05, w: 0.80, h: 0.42 },
        { id: "B", enabled: true, x: 0.10, y: 0.53, w: 0.80, h: 0.42 }
    ],
    overlap: [
        { id: "A", enabled: true, x: 0.10, y: 0.10, w: 0.55, h: 0.80 },
        { id: "B", enabled: true, x: 0.35, y: 0.10, w: 0.55, h: 0.80 }
    ],
    one_a: [
        { id: "A", enabled: true, x: 0.10, y: 0.10, w: 0.80, h: 0.80 },
        { id: "B", enabled: false, x: 0.53, y: 0.10, w: 0.42, h: 0.80 }
    ],
    one_b: [
        { id: "A", enabled: false, x: 0.05, y: 0.10, w: 0.42, h: 0.80 },
        { id: "B", enabled: true, x: 0.10, y: 0.10, w: 0.80, h: 0.80 }
    ]
};

app.registerExtension({
    name: "Tegaki.TwoRegionCoupleEditor",

    async nodeCreated(node) {
        if (node.comfyClass !== "TegakiTwoRegionCoupleEditor") return;

        node.selectedRegionId = "A";
        node.dragState = null;

        // ウィジェット検索
        const getWidget = (name) => node.widgets?.find(w => w.name === name);
        const specWidget = getWidget("two_region_spec_data");
        if (specWidget) {
            specWidget.type = "hidden";
        }

        // 初期化ヘルパー
        node.getSpec = function () {
            if (specWidget && specWidget.value) {
                try {
                    return JSON.parse(specWidget.value);
                } catch (e) { }
            }
            return {
                version: 1,
                canvas: { width: 832, height: 1216 },
                regions: JSON.parse(JSON.stringify(PRESETS.horizontal))
            };
        };

        node.setSpec = function (spec) {
            if (specWidget) {
                specWidget.value = JSON.stringify(spec, null, 2);
            }
            node.setDirtyCanvas(true, true);
        };

        // Preset 適用
        node.applyPreset = function (presetKey) {
            const spec = node.getSpec();
            const template = PRESETS[presetKey] || PRESETS.horizontal;
            spec.regions = JSON.parse(JSON.stringify(template));
            node.setSpec(spec);
        };

        // プリセットボタンウィジェットの追加
        node.addWidget("button", "Horizontal [A][B]", null, () => node.applyPreset("horizontal"));
        node.addWidget("button", "Vertical [A]/[B]", null, () => node.applyPreset("vertical"));
        node.addWidget("button", "Overlap (30%)", null, () => node.applyPreset("overlap"));
        node.addWidget("button", "One Region A", null, () => node.applyPreset("one_a"));
        node.addWidget("button", "One Region B", null, () => node.applyPreset("one_b"));
        node.addWidget("button", "Reset", null, () => node.applyPreset("horizontal"));

        // Canvas描画ウィジェットの追加
        const canvasWidget = node.addWidget("customCanvas", "two_region_canvas", null, () => { });
        canvasWidget.computeSize = () => [node.size[0] - 20, 260];

        canvasWidget.draw = function (ctx, node, width, y) {
            const spec = node.getSpec();
            const canvasW = spec.canvas?.width || 832;
            const canvasH = spec.canvas?.height || 1216;
            const aspect = canvasW / canvasH;

            const pad = 10;
            const availW = width - pad * 2;
            const availH = 240;

            let drawW = availW;
            let drawH = drawW / aspect;
            if (drawH > availH) {
                drawH = availH;
                drawW = drawH * aspect;
            }

            const drawX = (width - drawW) / 2;
            const drawY = y + 10;

            // 背景 & 枠
            ctx.fillStyle = PALETTE.bg;
            ctx.fillRect(drawX, drawY, drawW, drawH);
            ctx.strokeStyle = PALETTE.grid;
            ctx.lineWidth = 1;
            ctx.strokeRect(drawX, drawY, drawW, drawH);

            // Region A & B 描画
            for (const reg of spec.regions || []) {
                const isA = (reg.id === "A");
                const pal = isA ? PALETTE.A : PALETTE.B;
                const isSelected = (node.selectedRegionId === reg.id);

                if (!reg.enabled) {
                    ctx.save();
                    ctx.globalAlpha = 0.3;
                }

                const rx = drawX + reg.x * drawW;
                const ry = drawY + reg.y * drawH;
                const rw = reg.w * drawW;
                const rh = reg.h * drawH;

                ctx.fillStyle = pal.fill;
                ctx.fillRect(rx, ry, rw, rh);

                ctx.strokeStyle = isSelected ? pal.active : pal.stroke;
                ctx.lineWidth = isSelected ? 3 : 1.5;
                ctx.strokeRect(rx, ry, rw, rh);

                // ラベル
                const promptWidget = getWidget(isA ? "prompt_A" : "prompt_B");
                const pText = promptWidget?.value?.substring(0, 18) || "";
                ctx.fillStyle = pal.stroke;
                ctx.fillRect(rx, ry, Math.min(rw, 120), 18);
                ctx.fillStyle = "#ffffff";
                ctx.font = "bold 10px sans-serif";
                ctx.fillText(`${reg.id}: ${pText}`, rx + 4, ry + 13);

                // ハンドル (選択中のみ)
                if (isSelected && reg.enabled) {
                    ctx.fillStyle = PALETTE.handle;
                    ctx.strokeStyle = pal.stroke;
                    ctx.lineWidth = 1.5;
                    const hs = 6;
                    ctx.fillRect(rx + rw - hs, ry + rh - hs, hs * 2, hs * 2);
                    ctx.strokeRect(rx + rw - hs, ry + rh - hs, hs * 2, hs * 2);
                }

                if (!reg.enabled) {
                    ctx.restore();
                }
            }
        };

        // ノードサイズ調整
        node.setSize([380, 580]);
    }
});
