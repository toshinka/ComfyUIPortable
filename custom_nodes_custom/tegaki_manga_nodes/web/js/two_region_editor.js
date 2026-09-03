/**
 * Tegaki Two Region Couple Editor (Phase 3C.1 Hardened Oracle Frontend)
 * 
 * 2領域 (Region A / Region B) 専用の Interactive Rectangle Editor Canvas。
 * Semantic Overlap（重なり前提）を基本思想とし、
 * - 矩形クリック選択 (A / B)
 * - 矩形内部ドラッグ (Move)
 * - 右下ハンドルドラッグ (Resize)
 * - 余白ドラッグ (選択中Regionの再作成)
 * - Disable / Enable トグル
 * - プリセット (Semantic Overlap, Separate Left/Right, Separate Top/Bottom, A Only, B Only)
 * を完全サポートします。
 */

import { app } from "../../../scripts/app.js";

const PALETTE = {
    A: { stroke: "#2563eb", fill: "rgba(37, 99, 235, 0.35)", active: "#1d4ed8", name: "Region A (Blue)" },
    B: { stroke: "#ea580c", fill: "rgba(234, 88, 12, 0.35)", active: "#c2410c", name: "Region B (Orange)" },
    bg: "#fcfaf2",
    grid: "#e5e0d8",
    handle: "#ffffff"
};

// Phase 3C.1: Semantic Overlap を既定テンプレートとする
const PRESETS = {
    overlap: [
        { id: "A", enabled: true, x: 0.05, y: 0.10, w: 0.62, h: 0.80 },
        { id: "B", enabled: true, x: 0.33, y: 0.10, w: 0.62, h: 0.80 }
    ],
    horizontal: [
        { id: "A", enabled: true, x: 0.05, y: 0.10, w: 0.42, h: 0.80 },
        { id: "B", enabled: true, x: 0.53, y: 0.10, w: 0.42, h: 0.80 }
    ],
    vertical: [
        { id: "A", enabled: true, x: 0.10, y: 0.05, w: 0.80, h: 0.42 },
        { id: "B", enabled: true, x: 0.10, y: 0.53, w: 0.80, h: 0.42 }
    ],
    one_a: [
        { id: "A", enabled: true, x: 0.10, y: 0.10, w: 0.80, h: 0.80 },
        { id: "B", enabled: false, x: 0.33, y: 0.10, w: 0.62, h: 0.80 }
    ],
    one_b: [
        { id: "A", enabled: false, x: 0.05, y: 0.10, w: 0.62, h: 0.80 },
        { id: "B", enabled: true, x: 0.10, y: 0.10, w: 0.80, h: 0.80 }
    ]
};

app.registerExtension({
    name: "Tegaki.TwoRegionCoupleEditor",

    async nodeCreated(node) {
        if (node.comfyClass !== "TegakiTwoRegionCoupleEditor") return;

        node.selectedRegionId = "A";
        node.dragState = null; // { mode: 'move'|'resize'|'create', regionId: 'A'|'B', startNormX, startNormY, origRect: {x,y,w,h} }

        const getWidget = (name) => node.widgets?.find(w => w.name === name);
        const specWidget = getWidget("two_region_spec_data");
        if (specWidget) {
            specWidget.type = "hidden";
        }

        // 初期化ヘルパー
        node.getSpec = function () {
            if (specWidget && specWidget.value) {
                try {
                    const parsed = JSON.parse(specWidget.value);
                    if (parsed && Array.isArray(parsed.regions) && parsed.regions.length === 2) {
                        return parsed;
                    }
                } catch (e) { }
            }
            return {
                version: 1,
                canvas: { width: 832, height: 1216 },
                regions: JSON.parse(JSON.stringify(PRESETS.overlap))
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
            const template = PRESETS[presetKey] || PRESETS.overlap;
            spec.regions = JSON.parse(JSON.stringify(template));
            node.setSpec(spec);
        };

        // Toggle Enable / Disable
        node.toggleActiveRegion = function () {
            const spec = node.getSpec();
            const reg = spec.regions.find(r => r.id === node.selectedRegionId);
            if (reg) {
                reg.enabled = !reg.enabled;
                node.setSpec(spec);
            }
        };

        // プリセットボタンウィジェットの追加 (Phase 3C.1 改称)
        node.addWidget("button", "Semantic Overlap (~35%)", null, () => node.applyPreset("overlap"));
        node.addWidget("button", "Separate Left / Right", null, () => node.applyPreset("horizontal"));
        node.addWidget("button", "Separate Top / Bottom", null, () => node.applyPreset("vertical"));
        node.addWidget("button", "A Only (Disable B)", null, () => node.applyPreset("one_a"));
        node.addWidget("button", "B Only (Disable A)", null, () => node.applyPreset("one_b"));
        node.addWidget("button", "Toggle Selected A/B Enable", null, () => node.toggleActiveRegion());

        // Canvas描画ウィジェットの追加
        const canvasWidget = node.addWidget("customCanvas", "two_region_canvas", null, () => { });
        canvasWidget.computeSize = () => [node.size[0] - 20, 260];

        // 描画座標計算ヘルパー
        node.getCanvasLayout = function (width, y) {
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
            return { drawX, drawY, drawW, drawH, canvasW, canvasH };
        };

        canvasWidget.draw = function (ctx, node, width, y) {
            const layout = node.getCanvasLayout(width, y);
            const { drawX, drawY, drawW, drawH } = layout;
            node.lastCanvasLayout = layout; // マウスイベント用キャッシュ

            const spec = node.getSpec();

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
                    ctx.globalAlpha = 0.25;
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
                ctx.fillRect(rx, ry, Math.min(rw, 130), 18);
                ctx.fillStyle = "#ffffff";
                ctx.font = "bold 10px sans-serif";
                ctx.fillText(`${reg.id}${reg.enabled ? "" : " (OFF)"}: ${pText}`, rx + 4, ry + 13);

                // ハンドル (選択中のみ右下に描画)
                if (isSelected && reg.enabled) {
                    ctx.fillStyle = PALETTE.handle;
                    ctx.strokeStyle = pal.stroke;
                    ctx.lineWidth = 2;
                    const hs = 6;
                    ctx.fillRect(rx + rw - hs, ry + rh - hs, hs * 2, hs * 2);
                    ctx.strokeRect(rx + rw - hs, ry + rh - hs, hs * 2, hs * 2);
                }

                if (!reg.enabled) {
                    ctx.restore();
                }
            }
        };

        // -------------------------------------------------------------
        // 実インタラクション: Pointer / Mouse イベントハンドラ
        // -------------------------------------------------------------
        node.onMouseDown = function (event, local_pos) {
            if (!node.lastCanvasLayout) return false;
            const { drawX, drawY, drawW, drawH } = node.lastCanvasLayout;
            const px = local_pos[0];
            const py = local_pos[1];

            // Canvas 領域内判定
            if (px < drawX || px > drawX + drawW || py < drawY || py > drawY + drawH) {
                return false;
            }

            const normX = Math.max(0.0, Math.min(1.0, (px - drawX) / drawW));
            const normY = Math.max(0.0, Math.min(1.0, (py - drawY) / drawH));

            const spec = node.getSpec();
            const hsNorm = 8 / drawW; // ハンドル判定サイズ (normalized)

            // 1. 選択中 Region の右下ハンドル判定 (Resize)
            const selReg = spec.regions.find(r => r.id === node.selectedRegionId);
            if (selReg && selReg.enabled) {
                const hx = selReg.x + selReg.w;
                const hy = selReg.y + selReg.h;
                if (Math.abs(normX - hx) <= hsNorm * 1.5 && Math.abs(normY - hy) <= hsNorm * 1.5) {
                    node.dragState = {
                        mode: "resize",
                        regionId: selReg.id,
                        startNormX: normX,
                        startNormY: normY,
                        origRect: { x: selReg.x, y: selReg.y, w: selReg.w, h: selReg.h }
                    };
                    node.setDirtyCanvas(true, true);
                    return true;
                }
            }

            // 2. 矩形内部クリック判定 (選択 & Move)
            // 選択優先度: 現在の選択中ではないほうもクリックで切り替え可能
            // 逆順（手前のもの）からヒットテスト
            let hitRegion = null;
            for (let i = spec.regions.length - 1; i >= 0; i--) {
                const reg = spec.regions[i];
                if (normX >= reg.x && normX <= reg.x + reg.w && normY >= reg.y && normY <= reg.y + reg.h) {
                    hitRegion = reg;
                    break;
                }
            }

            if (hitRegion) {
                node.selectedRegionId = hitRegion.id;
                node.dragState = {
                    mode: "move",
                    regionId: hitRegion.id,
                    startNormX: normX,
                    startNormY: normY,
                    origRect: { x: hitRegion.x, y: hitRegion.y, w: hitRegion.w, h: hitRegion.h }
                };
                node.setDirtyCanvas(true, true);
                return true;
            }

            // 3. 余白ドラッグ (選択中 Region の新位置作成)
            if (selReg) {
                node.dragState = {
                    mode: "create",
                    regionId: selReg.id,
                    startNormX: normX,
                    startNormY: normY,
                    origRect: { x: normX, y: normY, w: 0.05, h: 0.05 }
                };
                selReg.enabled = true;
                selReg.x = normX;
                selReg.y = normY;
                selReg.w = 0.05;
                selReg.h = 0.05;
                node.setDirtyCanvas(true, true);
                return true;
            }

            return false;
        };

        node.onMouseMove = function (event, local_pos) {
            if (!node.dragState || !node.lastCanvasLayout) return false;
            const { drawX, drawY, drawW, drawH } = node.lastCanvasLayout;
            const px = local_pos[0];
            const py = local_pos[1];

            const normX = Math.max(0.0, Math.min(1.0, (px - drawX) / drawW));
            const normY = Math.max(0.0, Math.min(1.0, (py - drawY) / drawH));
            const dx = normX - node.dragState.startNormX;
            const dy = normY - node.dragState.startNormY;

            const spec = node.getSpec();
            const reg = spec.regions.find(r => r.id === node.dragState.regionId);
            if (!reg) return false;

            const minSize = 0.02;

            if (node.dragState.mode === "move") {
                let newX = node.dragState.origRect.x + dx;
                let newY = node.dragState.origRect.y + dy;
                newX = Math.max(0.0, Math.min(1.0 - reg.w, newX));
                newY = Math.max(0.0, Math.min(1.0 - reg.h, newY));
                reg.x = Math.round(newX * 1000) / 1000;
                reg.y = Math.round(newY * 1000) / 1000;
            } else if (node.dragState.mode === "resize") {
                let newW = node.dragState.origRect.w + dx;
                let newH = node.dragState.origRect.h + dy;
                newW = Math.max(minSize, Math.min(1.0 - reg.x, newW));
                newH = Math.max(minSize, Math.min(1.0 - reg.y, newH));
                reg.w = Math.round(newW * 1000) / 1000;
                reg.h = Math.round(newH * 1000) / 1000;
            } else if (node.dragState.mode === "create") {
                const curX = Math.min(node.dragState.startNormX, normX);
                const curY = Math.min(node.dragState.startNormY, normY);
                const curW = Math.max(minSize, Math.abs(normX - node.dragState.startNormX));
                const curH = Math.max(minSize, Math.abs(normY - node.dragState.startNormY));
                reg.x = Math.round(Math.max(0.0, curX) * 1000) / 1000;
                reg.y = Math.round(Math.max(0.0, curY) * 1000) / 1000;
                reg.w = Math.round(Math.min(1.0 - reg.x, curW) * 1000) / 1000;
                reg.h = Math.round(Math.min(1.0 - reg.y, curH) * 1000) / 1000;
            }

            node.setSpec(spec);
            return true;
        };

        node.onMouseUp = function (event, local_pos) {
            if (node.dragState) {
                node.dragState = null;
                node.setDirtyCanvas(true, true);
                return true;
            }
            return false;
        };

        // ノード初期サイズ
        node.setSize([380, 600]);
    }
});
