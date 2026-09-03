import { app } from "../../scripts/app.js";

// KOMA 1〜6 統一カラーパレット (Presentation 情報・KOMA identity に紐づく)
const KOMA_COLORS = [
    { name: "KOMA 1", hex: "#E53935", rgb: [229, 57, 53] },
    { name: "KOMA 2", hex: "#1E88E5", rgb: [30, 136, 229] },
    { name: "KOMA 3", hex: "#43A047", rgb: [67, 160, 71] },
    { name: "KOMA 4", hex: "#FB8C00", rgb: [251, 140, 0] },
    { name: "KOMA 5", hex: "#8E24AA", rgb: [142, 36, 170] },
    { name: "KOMA 6", hex: "#00ACC1", rgb: [0, 172, 193] },
];

const DEFAULT_LAYOUTS = [
    { id: 1, x: 0.06, y: 0.05, w: 0.88, h: 0.28, prompt: "" },
    { id: 2, x: 0.06, y: 0.36, w: 0.42, h: 0.58, prompt: "" },
    { id: 3, x: 0.52, y: 0.36, w: 0.42, h: 0.58, prompt: "" },
    { id: 4, x: 0.06, y: 0.05, w: 0.88, h: 0.20, prompt: "" },
    { id: 5, x: 0.06, y: 0.28, w: 0.88, h: 0.20, prompt: "" },
    { id: 6, x: 0.06, y: 0.51, w: 0.88, h: 0.43, prompt: "" },
];

function createDefaultSpec(panelCount = 3, width = 832, height = 1216, globalPrompt = "") {
    const regions = [];
    for (let i = 0; i < 6; i++) {
        const c = KOMA_COLORS[i];
        const layout = DEFAULT_LAYOUTS[i];
        regions.push({
            id: i + 1,
            name: c.name,
            enabled: i < panelCount,
            x: layout.x,
            y: layout.y,
            w: layout.w,
            h: layout.h,
            prompt: layout.prompt,
            color: c.hex,
        });
    }

    return {
        version: 1,
        canvas: { width: width, height: height },
        panel_count: panelCount,
        global_prompt: globalPrompt,
        regions: regions
    };
}

// 共通アクティブ判定 (enabled かつ id <= panel_count)
function isActiveRegion(r, panelCount) {
    return r && r.enabled && (r.id <= panelCount);
}

app.registerExtension({
    name: "Tegaki.MangaRegionEditor",
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name !== "TegakiMangaRegionEditor") return;

        // ノード設定復元ライフサイクル (onConfigure) のフック
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
            node.setSize([560, 800]);

            // 内部State管理 (REGION_SPEC が Single Source of Truth)
            let spec = createDefaultSpec(3, 832, 1216, "");
            let selectedRegionIds = new Set([1]);
            let undoStack = [];
            let redoStack = [];
            let beforeTextEditSnapshot = null;
            let statusMessage = "";
            let statusMessageTimeout = null;

            function showStatus(msg, durationMs = 2500) {
                statusMessage = msg;
                if (statusMessageTimeout) clearTimeout(statusMessageTimeout);
                statusMessageTimeout = setTimeout(() => {
                    statusMessage = "";
                    renderCanvas();
                }, durationMs);
                renderCanvas();
            }

            function pushHistory() {
                undoStack.push(JSON.parse(JSON.stringify(spec)));
                if (undoStack.length > 50) undoStack.shift();
                redoStack = [];
            }

            function doUndo() {
                if (undoStack.length > 0) {
                    redoStack.push(JSON.parse(JSON.stringify(spec)));
                    spec = undoStack.pop();
                    syncToWidgets();
                    renderAll();
                    showStatus("Undo");
                }
            }

            function doRedo() {
                if (redoStack.length > 0) {
                    undoStack.push(JSON.parse(JSON.stringify(spec)));
                    spec = redoStack.pop();
                    syncToWidgets();
                    renderAll();
                    showStatus("Redo");
                }
            }

            // REGION_SPEC -> ComfyUI Widgets 同期
            function syncToWidgets() {
                const wData = node.widgets.find(x => x.name === "region_spec_data");
                if (wData) {
                    wData.value = JSON.stringify(spec);
                }
                const wPanel = node.widgets.find(x => x.name === "panel_count");
                if (wPanel && wPanel.value !== spec.panel_count) {
                    wPanel.value = spec.panel_count;
                }
                const wWidth = node.widgets.find(x => x.name === "canvas_width");
                if (wWidth && wWidth.value !== spec.canvas.width) {
                    wWidth.value = spec.canvas.width;
                }
                const wHeight = node.widgets.find(x => x.name === "canvas_height");
                if (wHeight && wHeight.value !== spec.canvas.height) {
                    wHeight.value = spec.canvas.height;
                }
                const wPrompt = node.widgets.find(x => x.name === "global_prompt");
                if (wPrompt && wPrompt.value !== spec.global_prompt) {
                    wPrompt.value = spec.global_prompt;
                }
                node.setDirtyCanvas(true, true);
            }

            // 外側Widgets変更検知のバインド (Facade -> REGION_SPEC)
            function hookWidgetCallbacks() {
                const wPanel = node.widgets.find(x => x.name === "panel_count");
                if (wPanel && !wPanel._tegakiHooked) {
                    wPanel._tegakiHooked = true;
                    const origCb = wPanel.callback;
                    wPanel.callback = function (v) {
                        if (origCb) origCb.apply(this, arguments);
                        const p = Math.max(1, Math.min(6, parseInt(v) || 3));
                        if (spec.panel_count !== p) {
                            pushHistory();
                            spec.panel_count = p;
                            syncToWidgets();
                            renderAll();
                        }
                    };
                }

                const wWidth = node.widgets.find(x => x.name === "canvas_width");
                if (wWidth && !wWidth._tegakiHooked) {
                    wWidth._tegakiHooked = true;
                    const origCb = wWidth.callback;
                    wWidth.callback = function (v) {
                        if (origCb) origCb.apply(this, arguments);
                        const val = parseInt(v) || 832;
                        if (spec.canvas.width !== val) {
                            spec.canvas.width = val;
                            syncToWidgets();
                            renderCanvas();
                        }
                    };
                }

                const wHeight = node.widgets.find(x => x.name === "canvas_height");
                if (wHeight && !wHeight._tegakiHooked) {
                    wHeight._tegakiHooked = true;
                    const origCb = wHeight.callback;
                    wHeight.callback = function (v) {
                        if (origCb) origCb.apply(this, arguments);
                        const val = parseInt(v) || 1216;
                        if (spec.canvas.height !== val) {
                            spec.canvas.height = val;
                            syncToWidgets();
                            renderCanvas();
                        }
                    };
                }

                const wPrompt = node.widgets.find(x => x.name === "global_prompt");
                if (wPrompt && !wPrompt._tegakiHooked) {
                    wPrompt._tegakiHooked = true;
                    const origCb = wPrompt.callback;
                    wPrompt.callback = function (v) {
                        if (origCb) origCb.apply(this, arguments);
                        if (spec.global_prompt !== v) {
                            spec.global_prompt = v || "";
                            syncToWidgets();
                        }
                    };
                }
            }

            // ノード復元関数
            node._tegakiRestoreFromWidgets = function () {
                const w = node.widgets.find(x => x.name === "region_spec_data");
                if (w && w.value && w.value !== "{}") {
                    try {
                        const loaded = JSON.parse(w.value);
                        if (loaded && loaded.regions && Array.isArray(loaded.regions)) {
                            spec = loaded;
                            // 互換性チェック & 6コマ確保
                            if (!spec.canvas) spec.canvas = { width: 832, height: 1216 };
                            if (!spec.panel_count) spec.panel_count = 3;
                            if (spec.global_prompt === undefined) spec.global_prompt = "";
                        }
                    } catch (err) {
                        console.warn("[TegakiRegionEditor] Failed to parse saved region_spec_data JSON:", err);
                    }
                }
                syncToWidgets();
                renderAll();
            };

            // HTMLコンテナWidgetの作成
            const container = document.createElement("div");
            container.style.cssText = `
                display: flex;
                flex-direction: column;
                gap: 8px;
                background: #1c1815;
                color: #e6dfd5;
                padding: 10px;
                border-radius: 6px;
                font-family: sans-serif;
                font-size: 12px;
                box-sizing: border-box;
                width: 100%;
                user-select: none;
            `;

            // ツールバー
            const toolbar = document.createElement("div");
            toolbar.style.cssText = "display: flex; gap: 6px; align-items: center; flex-wrap: wrap;";

            function createBtn(text, title, onClick, extraStyle = "") {
                const btn = document.createElement("button");
                btn.textContent = text;
                btn.title = title;
                btn.style.cssText = `background: #3e352f; color: #fff; border: 1px solid #5a4f47; border-radius: 3px; padding: 4px 8px; cursor: pointer; font-size: 11px; ${extraStyle}`;
                btn.onclick = onClick;
                return btn;
            }

            const undoBtn = createBtn("↩ Undo", "元に戻す (Ctrl+Z)", doUndo);
            const redoBtn = createBtn("↪ Redo", "やり直す (Ctrl+Y / Ctrl+Shift+Z)", doRedo);
            const splitHBtn = createBtn("⬌ Split H", "選択コマを水平50:50分割", () => splitSelectedRegion("H"));
            const splitVBtn = createBtn("⬍ Split V", "選択コマを垂直50:50分割", () => splitSelectedRegion("V"));
            const swapBtn = createBtn("⇄ Swap", "選択した2つのコマを入れ替え", swapSelectedRegions);
            const deleteBtn = createBtn("🗑 Delete", "選択コマを無効化・削除 (Deleteキー)", deleteSelectedRegions, "color: #ff9999; border-color: #884444;");
            const resetBtn = createBtn("Layout Reset", "矩形レイアウトのみ初期状態へリセット", resetLayout, "background: #5a2e2e; margin-left: auto;");

            toolbar.appendChild(undoBtn);
            toolbar.appendChild(redoBtn);
            toolbar.appendChild(splitHBtn);
            toolbar.appendChild(splitVBtn);
            toolbar.appendChild(swapBtn);
            toolbar.appendChild(deleteBtn);
            toolbar.appendChild(resetBtn);

            // メイン作業領域 (Canvas + コマリスト)
            const mainRow = document.createElement("div");
            mainRow.style.cssText = "display: flex; gap: 10px; width: 100%; height: 400px;";

            // 左側: Region Canvas (漫画比率 832:1216 -> 250:365)
            const canvasContainer = document.createElement("div");
            canvasContainer.style.cssText = "position: relative; width: 250px; height: 365px; background: #fff; border: 2px solid #5a4f47; border-radius: 4px; box-shadow: 0 2px 6px rgba(0,0,0,0.5); flex-shrink: 0;";

            const canvas = document.createElement("canvas");
            canvas.width = 250;
            canvas.height = 365;
            canvas.style.cssText = "width: 100%; height: 100%; display: block;";
            canvasContainer.appendChild(canvas);

            const ctx = canvas.getContext("2d");

            // 右側: KOMA 1〜6 リスト & Prompt
            const komaList = document.createElement("div");
            komaList.style.cssText = "display: flex; flex-direction: column; gap: 6px; flex-grow: 1; overflow-y: auto; max-height: 380px; padding-right: 4px;";

            mainRow.appendChild(canvasContainer);
            mainRow.appendChild(komaList);

            container.appendChild(toolbar);
            container.appendChild(mainRow);

            // リサイズハンドルの描画
            function drawHandle(x, y) {
                ctx.fillStyle = "#ffffff";
                ctx.strokeStyle = "#111111";
                ctx.lineWidth = 1.5;
                ctx.fillRect(x - 4, y - 4, 8, 8);
                ctx.strokeRect(x - 4, y - 4, 8, 8);
            }

            // キャンバス描画
            function renderCanvas() {
                ctx.clearRect(0, 0, canvas.width, canvas.height);

                // 漫画マージン線
                ctx.strokeStyle = "#e0dedb";
                ctx.lineWidth = 1;
                ctx.strokeRect(6, 6, canvas.width - 12, canvas.height - 12);

                // 有効コマの描画
                spec.regions.forEach(r => {
                    if (!isActiveRegion(r, spec.panel_count)) return;

                    const rx = r.x * canvas.width;
                    const ry = r.y * canvas.height;
                    const rw = r.w * canvas.width;
                    const rh = r.h * canvas.height;

                    const colorInfo = KOMA_COLORS[(r.id - 1) % KOMA_COLORS.length];
                    const isSelected = selectedRegionIds.has(r.id);

                    // 塗りつぶし
                    ctx.fillStyle = isSelected ? `rgba(${colorInfo.rgb.join(",")}, 0.35)` : `rgba(${colorInfo.rgb.join(",")}, 0.20)`;
                    ctx.fillRect(rx, ry, rw, rh);

                    // 枠線
                    ctx.strokeStyle = colorInfo.hex;
                    ctx.lineWidth = isSelected ? 3 : 2;
                    ctx.setLineDash(isSelected ? [4, 2] : []);
                    ctx.strokeRect(rx, ry, rw, rh);
                    ctx.setLineDash([]);

                    // ラベルバッジ
                    const badgeW = Math.min(rw - 4, 56);
                    ctx.fillStyle = colorInfo.hex;
                    ctx.fillRect(rx + 2, ry + 2, badgeW, 16);
                    ctx.fillStyle = "#ffffff";
                    ctx.font = "bold 9px sans-serif";
                    ctx.fillText(`KOMA ${r.id}`, rx + 5, ry + 13);

                    // 4隅リサイズハンドル (選択中のみ全4隅描画)
                    if (isSelected) {
                        drawHandle(rx, ry);           // NW (左上)
                        drawHandle(rx + rw, ry);      // NE (右上)
                        drawHandle(rx, ry + rh);      // SW (左下)
                        drawHandle(rx + rw, ry + rh); // SE (右下)
                    }
                });

                // 通知・ステータスメッセージ表示
                if (statusMessage) {
                    ctx.fillStyle = "rgba(20, 17, 15, 0.85)";
                    ctx.fillRect(10, canvas.height - 30, canvas.width - 20, 22);
                    ctx.strokeStyle = "#fb8c00";
                    ctx.lineWidth = 1;
                    ctx.strokeRect(10, canvas.height - 30, canvas.width - 20, 22);
                    ctx.fillStyle = "#ffffff";
                    ctx.font = "10px sans-serif";
                    ctx.textAlign = "center";
                    ctx.fillText(statusMessage, canvas.width / 2, canvas.height - 15);
                    ctx.textAlign = "start";
                }
            }

            // KOMA リスト描画
            function renderKomaList() {
                komaList.innerHTML = "";

                spec.regions.forEach(r => {
                    if (r.id > spec.panel_count) return;

                    const colorInfo = KOMA_COLORS[(r.id - 1) % KOMA_COLORS.length];
                    const isSelected = selectedRegionIds.has(r.id);

                    const card = document.createElement("div");
                    card.style.cssText = `
                        background: ${isSelected ? "#2d2621" : "#231e1a"};
                        border: 1px solid ${isSelected ? colorInfo.hex : "#3d342d"};
                        border-left: 5px solid ${colorInfo.hex};
                        border-radius: 4px;
                        padding: 6px;
                        display: flex;
                        flex-direction: column;
                        gap: 4px;
                        opacity: ${r.enabled ? "1.0" : "0.55"};
                    `;

                    // ヘッダー行
                    const header = document.createElement("div");
                    header.style.cssText = "display: flex; align-items: center; gap: 6px; cursor: pointer;";
                    header.onclick = (e) => {
                        if (e.shiftKey) {
                            if (selectedRegionIds.has(r.id)) selectedRegionIds.delete(r.id);
                            else selectedRegionIds.add(r.id);
                        } else {
                            selectedRegionIds = new Set([r.id]);
                        }
                        renderAll();
                    };

                    const chk = document.createElement("input");
                    chk.type = "checkbox";
                    chk.checked = r.enabled;
                    chk.title = "コマの有効/無効トグル";
                    chk.onclick = (e) => {
                        e.stopPropagation();
                        pushHistory();
                        r.enabled = chk.checked;
                        syncToWidgets();
                        renderAll();
                    };

                    const title = document.createElement("span");
                    title.textContent = `KOMA ${r.id}`;
                    title.style.cssText = `font-weight: bold; color: ${colorInfo.hex};`;

                    const coordLabel = document.createElement("span");
                    coordLabel.style.cssText = "font-size: 10px; color: #a89f91; margin-left: auto;";
                    coordLabel.textContent = `${Math.round(r.w * 100)}%×${Math.round(r.h * 100)}%`;

                    header.appendChild(chk);
                    header.appendChild(title);
                    header.appendChild(coordLabel);

                    // Prompt入力欄 (focus時スナップショット、blur時コミット)
                    const promptInput = document.createElement("textarea");
                    promptInput.placeholder = `koma${r.id}: character, action, background...`;
                    promptInput.value = r.prompt || "";
                    promptInput.style.cssText = `
                        background: #14110f;
                        color: #f0eae1;
                        border: 1px solid #3d342d;
                        border-radius: 3px;
                        padding: 4px;
                        font-size: 11px;
                        resize: vertical;
                        min-height: 36px;
                        max-height: 75px;
                        font-family: inherit;
                    `;

                    promptInput.onfocus = () => {
                        beforeTextEditSnapshot = JSON.parse(JSON.stringify(spec));
                    };

                    promptInput.oninput = () => {
                        r.prompt = promptInput.value;
                        // Widget値だけ即時更新 (履歴はまだ積まない)
                        const wData = node.widgets.find(x => x.name === "region_spec_data");
                        if (wData) wData.value = JSON.stringify(spec);
                    };

                    promptInput.onblur = () => {
                        if (beforeTextEditSnapshot && JSON.stringify(beforeTextEditSnapshot) !== JSON.stringify(spec)) {
                            undoStack.push(beforeTextEditSnapshot);
                            if (undoStack.length > 50) undoStack.shift();
                            redoStack = [];
                            beforeTextEditSnapshot = null;
                            syncToWidgets();
                        }
                    };

                    card.appendChild(header);
                    card.appendChild(promptInput);
                    komaList.appendChild(card);
                });
            }

            function renderAll() {
                renderCanvas();
                renderKomaList();
            }

            // スライス処理 (Split H / V)
            // 仕様: panel_count枠内の無効コマを優先再利用。なければpanel_count<6のとき1増加して新規枠を確保。
            function splitSelectedRegion(dir) {
                if (selectedRegionIds.size === 0) {
                    showStatus("分割するコマを選択してください");
                    return;
                }
                const targetId = Array.from(selectedRegionIds)[0];
                const target = spec.regions.find(r => r.id === targetId);
                if (!target || !target.enabled) return;

                // 1. 現在の panel_count 範囲内の無効コマを優先探索
                let unused = spec.regions.find(r => r.id <= spec.panel_count && !r.enabled && r.id !== targetId);
                let needIncrease = false;

                // 2. 範囲内にない場合、panel_count < 6 であれば panel_count を拡張して次コマを利用
                if (!unused && spec.panel_count < 6) {
                    unused = spec.regions.find(r => r.id === spec.panel_count + 1);
                    needIncrease = true;
                }

                // 3. 6コマすべて使用済みの場合は分割不可
                if (!unused) {
                    showStatus("最大6コマに達しているため分割できません");
                    return;
                }

                // 変更直前に元状態のsnapshotを保存 (Undo時にpanel_count/geometry/enabledを完全復元)
                pushHistory();

                if (needIncrease) {
                    spec.panel_count += 1;
                }
                unused.enabled = true;

                if (dir === "H") {
                    const halfW = target.w / 2;
                    unused.x = target.x + halfW;
                    unused.y = target.y;
                    unused.w = halfW;
                    unused.h = target.h;
                    target.w = halfW;
                } else {
                    const halfH = target.h / 2;
                    unused.x = target.x;
                    unused.y = target.y + halfH;
                    unused.w = target.w;
                    unused.h = halfH;
                    target.h = halfH;
                }

                selectedRegionIds = new Set([targetId, unused.id]);
                syncToWidgets();
                renderAll();
                showStatus(`KOMA ${targetId} を分割しました (KOMA ${unused.id} 割り当て, コマ数: ${spec.panel_count})`);
            }

            // コマ入れ替え処理 (Swap)
            // 仕様: KOMA identity (id, name, color) は固定。それ以外の全フィールド(geometry, prompt, enabled, 未知フィールド等)をGeneric Payloadとして交換
            function swapSelectedRegions() {
                const ids = Array.from(selectedRegionIds);
                if (ids.length !== 2) {
                    showStatus("入れ替える2つのコマをShift+クリックで選択してください");
                    return;
                }
                const r1 = spec.regions.find(r => r.id === ids[0]);
                const r2 = spec.regions.find(r => r.id === ids[1]);
                if (!r1 || !r2) return;

                pushHistory();

                const identityKeys = new Set(["id", "name", "color"]);
                const allKeys = new Set([...Object.keys(r1), ...Object.keys(r2)]);

                allKeys.forEach(key => {
                    if (identityKeys.has(key)) return;
                    const val1 = r1[key];
                    const val2 = r2[key];
                    if (val2 !== undefined) {
                        r1[key] = val2;
                    } else {
                        delete r1[key];
                    }
                    if (val1 !== undefined) {
                        r2[key] = val1;
                    } else {
                        delete r2[key];
                    }
                });

                syncToWidgets();
                renderAll();
                showStatus(`KOMA ${r1.id} と KOMA ${r2.id} の内容を入れ替えました`);
            }

            // コマ削除処理 (Delete)
            // 仕様: オブジェクトそのものを破棄せず enabled = false にする
            function deleteSelectedRegions() {
                if (selectedRegionIds.size === 0) return;
                pushHistory();
                selectedRegionIds.forEach(rid => {
                    const r = spec.regions.find(x => x.id === rid);
                    if (r) r.enabled = false;
                });
                selectedRegionIds.clear();
                syncToWidgets();
                renderAll();
                showStatus("選択コマを無効化しました");
            }

            // レイアウトリセット
            // 仕様: x, y, w, h のみを初期値に戻す。enabled, prompt, panel_count, Canvas Size, Global Prompt, 未知フィールドは100%保持
            function resetLayout() {
                if (confirm("コマの矩形レイアウト (座標・サイズ) のみを初期状態にリセットしますか？\n(※コマの有効状態、Prompt、Canvasサイズは維持されます)")) {
                    pushHistory();
                    for (let i = 0; i < 6; i++) {
                        const layout = DEFAULT_LAYOUTS[i];
                        const r = spec.regions[i];
                        r.x = layout.x;
                        r.y = layout.y;
                        r.w = layout.w;
                        r.h = layout.h;
                        // enabled, prompt 等は変更しない
                    }
                    syncToWidgets();
                    renderAll();
                    showStatus("レイアウト座標をリセットしました");
                }
            }

            // Canvasインタラクション (ドラッグ移動・4隅リサイズ・新規作成)
            let isDragging = false;
            let dragMode = "none";   // "move", "resize", "create"
            let dragHandle = "";     // "nw", "ne", "sw", "se"
            let startX = 0, startY = 0;
            let activeRegion = null;
            let initialRects = new Map();

            // ハンドル当たり判定ヘルパー
            function getHandleAt(mx, my, r) {
                const hSize = 10 / canvas.width;
                const rx = r.x, ry = r.y, rw = r.w, rh = r.h;

                if (Math.hypot(mx - rx, my - ry) < hSize) return "nw";
                if (Math.hypot(mx - (rx + rw), my - ry) < hSize) return "ne";
                if (Math.hypot(mx - rx, my - (ry + rh)) < hSize) return "sw";
                if (Math.hypot(mx - (rx + rw), my - (ry + rh)) < hSize) return "se";
                return "";
            }

            canvas.onmousemove = (e) => {
                if (isDragging) return;
                const rect = canvas.getBoundingClientRect();
                const mx = (e.clientX - rect.left) / canvas.width;
                const my = (e.clientY - rect.top) / canvas.height;

                let cursor = "crosshair";
                for (const rid of selectedRegionIds) {
                    const r = spec.regions.find(x => x.id === rid);
                    if (!r || !isActiveRegion(r, spec.panel_count)) continue;
                    const h = getHandleAt(mx, my, r);
                    if (h === "nw" || h === "se") { cursor = "nwse-resize"; break; }
                    if (h === "ne" || h === "sw") { cursor = "nesw-resize"; break; }
                }

                if (cursor === "crosshair") {
                    for (let i = spec.regions.length - 1; i >= 0; i--) {
                        const r = spec.regions[i];
                        if (!isActiveRegion(r, spec.panel_count)) continue;
                        if (mx >= r.x && mx <= r.x + r.w && my >= r.y && my <= r.y + r.h) {
                            cursor = "move";
                            break;
                        }
                    }
                }
                canvas.style.cursor = cursor;
            };

            canvas.onmousedown = (e) => {
                // Drag state の明示的初期化 (過去参照の残存防止)
                isDragging = false;
                dragMode = "none";
                dragHandle = "";
                activeRegion = null;
                initialRects.clear();

                const rect = canvas.getBoundingClientRect();
                const mx = (e.clientX - rect.left) / canvas.width;
                const my = (e.clientY - rect.top) / canvas.height;
                startX = mx;
                startY = my;

                // 1. 4隅ハンドルクリック判定 (選択中コマ優先)
                for (const rid of selectedRegionIds) {
                    const r = spec.regions.find(x => x.id === rid);
                    if (!r || !isActiveRegion(r, spec.panel_count)) continue;
                    const h = getHandleAt(mx, my, r);
                    if (h) {
                        dragMode = "resize";
                        dragHandle = h;
                        activeRegion = r;
                        break;
                    }
                }

                // 2. 矩形内部クリック判定 (移動または選択)
                if (dragMode === "none") {
                    let clickedRegion = null;
                    for (let i = spec.regions.length - 1; i >= 0; i--) {
                        const r = spec.regions[i];
                        if (!isActiveRegion(r, spec.panel_count)) continue;
                        if (mx >= r.x && mx <= r.x + r.w && my >= r.y && my <= r.y + r.h) {
                            clickedRegion = r;
                            break;
                        }
                    }

                    if (clickedRegion) {
                        if (e.shiftKey) {
                            if (selectedRegionIds.has(clickedRegion.id)) selectedRegionIds.delete(clickedRegion.id);
                            else selectedRegionIds.add(clickedRegion.id);
                        } else if (!selectedRegionIds.has(clickedRegion.id)) {
                            selectedRegionIds = new Set([clickedRegion.id]);
                        }
                        dragMode = "move";
                        activeRegion = clickedRegion;
                    } else {
                        // 3. 空白領域ドラッグ -> 新規矩形作成
                        if (!e.shiftKey) selectedRegionIds = new Set();

                        // 空きコマを探す (無効コマ、またはpanel_count枠内の未有効化コマ)
                        let targetKoma = spec.regions.find(r => r.id <= spec.panel_count && !r.enabled);
                        let needIncrease = false;
                        if (!targetKoma && spec.panel_count < 6) {
                            targetKoma = spec.regions.find(r => r.id === spec.panel_count + 1);
                            needIncrease = true;
                        }

                        if (targetKoma) {
                            // 新規Region作成が成立すると判断した時点で、変更前に元状態のsnapshotを保存
                            pushHistory();

                            if (needIncrease) {
                                spec.panel_count += 1;
                            }
                            dragMode = "create";
                            activeRegion = targetKoma;
                            activeRegion.enabled = true;
                            activeRegion.x = mx;
                            activeRegion.y = my;
                            activeRegion.w = 0.01;
                            activeRegion.h = 0.01;
                            selectedRegionIds = new Set([activeRegion.id]);
                        } else {
                            dragMode = "none";
                            showStatus("最大6コマに達しているため新規作成できません");
                            return; // 履歴を追加せず終了
                        }
                    }
                }

                // 移動またはリサイズの場合も変更前にsnapshotを保存
                if (dragMode === "move" || dragMode === "resize") {
                    pushHistory();
                }

                isDragging = true;
                selectedRegionIds.forEach(rid => {
                    const r = spec.regions.find(x => x.id === rid);
                    if (r) initialRects.set(rid, { x: r.x, y: r.y, w: r.w, h: r.h });
                });

                renderAll();
            };

            const onWindowMouseMove = (e) => {
                if (!isDragging || !activeRegion) return;

                const rect = canvas.getBoundingClientRect();
                const mx = Math.max(0, Math.min(1, (e.clientX - rect.left) / canvas.width));
                const my = Math.max(0, Math.min(1, (e.clientY - rect.top) / canvas.height));
                const dx = mx - startX;
                const dy = my - startY;

                if (dragMode === "move") {
                    selectedRegionIds.forEach(rid => {
                        const init = initialRects.get(rid);
                        const r = spec.regions.find(x => x.id === rid);
                        if (init && r) {
                            r.x = Math.max(0, Math.min(1 - r.w, init.x + dx));
                            r.y = Math.max(0, Math.min(1 - r.h, init.y + dy));
                        }
                    });
                } else if (dragMode === "resize") {
                    const init = initialRects.get(activeRegion.id);
                    if (init) {
                        if (dragHandle === "se") {
                            activeRegion.w = Math.max(0.04, Math.min(1 - init.x, init.w + dx));
                            activeRegion.h = Math.max(0.04, Math.min(1 - init.y, init.h + dy));
                        } else if (dragHandle === "sw") {
                            const newX = Math.max(0, Math.min(init.x + init.w - 0.04, init.x + dx));
                            activeRegion.w = (init.x + init.w) - newX;
                            activeRegion.x = newX;
                            activeRegion.h = Math.max(0.04, Math.min(1 - init.y, init.h + dy));
                        } else if (dragHandle === "ne") {
                            activeRegion.w = Math.max(0.04, Math.min(1 - init.x, init.w + dx));
                            const newY = Math.max(0, Math.min(init.y + init.h - 0.04, init.y + dy));
                            activeRegion.h = (init.y + init.h) - newY;
                            activeRegion.y = newY;
                        } else if (dragHandle === "nw") {
                            const newX = Math.max(0, Math.min(init.x + init.w - 0.04, init.x + dx));
                            const newY = Math.max(0, Math.min(init.y + init.h - 0.04, init.y + dy));
                            activeRegion.w = (init.x + init.w) - newX;
                            activeRegion.h = (init.y + init.h) - newY;
                            activeRegion.x = newX;
                            activeRegion.y = newY;
                        }
                    }
                } else if (dragMode === "create") {
                    activeRegion.w = Math.max(0.04, Math.min(1 - activeRegion.x, mx - startX));
                    activeRegion.h = Math.max(0.04, Math.min(1 - activeRegion.y, my - startY));
                }

                renderCanvas();
            };

            const onWindowMouseUp = () => {
                if (isDragging) {
                    isDragging = false;
                    dragMode = "none";
                    dragHandle = "";
                    syncToWidgets();
                    renderAll();
                }
            };

            // キーボードショートカット (Ctrl+Z, Ctrl+Y, Delete)
            const onWindowKeyDown = (e) => {
                // テキスト入力中はブラウザ標準操作を優先
                const activeTag = document.activeElement ? document.activeElement.tagName.toLowerCase() : "";
                if (activeTag === "input" || activeTag === "textarea" || (document.activeElement && document.activeElement.isContentEditable)) {
                    return;
                }

                if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "z") {
                    e.preventDefault();
                    if (e.shiftKey) doRedo();
                    else doUndo();
                } else if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "y") {
                    e.preventDefault();
                    doRedo();
                } else if (e.key === "Delete" || e.key === "Backspace") {
                    if (selectedRegionIds.size > 0) {
                        e.preventDefault();
                        deleteSelectedRegions();
                    }
                }
            };

            // イベントリスナー登録
            window.addEventListener("mousemove", onWindowMouseMove);
            window.addEventListener("mouseup", onWindowMouseUp);
            window.addEventListener("keydown", onWindowKeyDown);

            // ノード削除時のリスナー cleanup (指示書第25項)
            const origOnRemoved = node.onRemoved;
            node.onRemoved = function () {
                window.removeEventListener("mousemove", onWindowMouseMove);
                window.removeEventListener("mouseup", onWindowMouseUp);
                window.removeEventListener("keydown", onWindowKeyDown);
                if (origOnRemoved) origOnRemoved.apply(this, arguments);
            };

            // Widget callback と初期同期
            hookWidgetCallbacks();
            node._tegakiRestoreFromWidgets();

            // DOM Widget の登録
            node.addDOMWidget("manga_region_editor", "ui", container);

            return r;
        };
    }
});
