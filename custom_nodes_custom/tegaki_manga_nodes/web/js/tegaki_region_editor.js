import { app } from "../../scripts/app.js";

// KOMA 1〜6 統一カラーパレット
const KOMA_COLORS = [
    { name: "KOMA 1", hex: "#E53935", rgb: [229, 57, 53] },
    { name: "KOMA 2", hex: "#1E88E5", rgb: [30, 136, 229] },
    { name: "KOMA 3", hex: "#43A047", rgb: [67, 160, 71] },
    { name: "KOMA 4", hex: "#FB8C00", rgb: [251, 140, 0] },
    { name: "KOMA 5", hex: "#8E24AA", rgb: [142, 36, 170] },
    { name: "KOMA 6", hex: "#00ACC1", rgb: [0, 172, 193] },
];

function createDefaultSpec(panelCount = 3) {
    const defaultLayouts = [
        { id: 1, x: 0.06, y: 0.05, w: 0.88, h: 0.28, prompt: "" },
        { id: 2, x: 0.06, y: 0.36, w: 0.42, h: 0.58, prompt: "" },
        { id: 3, x: 0.52, y: 0.36, w: 0.42, h: 0.58, prompt: "" },
        { id: 4, x: 0.06, y: 0.05, w: 0.88, h: 0.20, prompt: "" },
        { id: 5, x: 0.06, y: 0.28, w: 0.88, h: 0.20, prompt: "" },
        { id: 6, x: 0.06, y: 0.51, w: 0.88, h: 0.43, prompt: "" },
    ];

    const regions = [];
    for (let i = 0; i < 6; i++) {
        const c = KOMA_COLORS[i];
        const layout = defaultLayouts[i];
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
        canvas: { width: 832, height: 1216 },
        panel_count: panelCount,
        global_prompt: "",
        regions: regions
    };
}

app.registerExtension({
    name: "Tegaki.MangaRegionEditor",
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name !== "TegakiMangaRegionEditor") return;

        const onNodeCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function () {
            const r = onNodeCreated ? onNodeCreated.apply(this, arguments) : undefined;

            const node = this;
            node.setSize([540, 780]);

            // 内部State管理
            let spec = createDefaultSpec(3);
            let selectedRegionIds = new Set([1]); // 選択中のKOMA ID
            let undoStack = [];
            let redoStack = [];

            function pushHistory() {
                undoStack.push(JSON.parse(JSON.stringify(spec)));
                if (undoStack.length > 50) undoStack.shift();
                redoStack = [];
            }

            function syncToWidget() {
                const w = node.widgets.find(x => x.name === "region_spec_data");
                if (w) {
                    w.value = JSON.stringify(spec);
                }
                const panelWidget = node.widgets.find(x => x.name === "panel_count");
                if (panelWidget && panelWidget.value !== spec.panel_count) {
                    panelWidget.value = spec.panel_count;
                }
                node.setDirtyCanvas(true, true);
            }

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

            const undoBtn = document.createElement("button");
            undoBtn.textContent = "↩ Undo";
            undoBtn.style.cssText = "background: #3e352f; color: #fff; border: 1px solid #5a4f47; border-radius: 3px; padding: 3px 8px; cursor: pointer;";
            undoBtn.onclick = () => {
                if (undoStack.length > 0) {
                    redoStack.push(JSON.parse(JSON.stringify(spec)));
                    spec = undoStack.pop();
                    syncToWidget();
                    renderAll();
                }
            };

            const redoBtn = document.createElement("button");
            redoBtn.textContent = "↪ Redo";
            redoBtn.style.cssText = "background: #3e352f; color: #fff; border: 1px solid #5a4f47; border-radius: 3px; padding: 3px 8px; cursor: pointer;";
            redoBtn.onclick = () => {
                if (redoStack.length > 0) {
                    undoStack.push(JSON.parse(JSON.stringify(spec)));
                    spec = redoStack.pop();
                    syncToWidget();
                    renderAll();
                }
            };

            const splitHBtn = document.createElement("button");
            splitHBtn.textContent = "⬌ Split H";
            splitHBtn.title = "選択中のコマを水平に50:50分割";
            splitHBtn.style.cssText = "background: #3e352f; color: #fff; border: 1px solid #5a4f47; border-radius: 3px; padding: 3px 8px; cursor: pointer;";
            splitHBtn.onclick = () => splitSelectedRegion("H");

            const splitVBtn = document.createElement("button");
            splitVBtn.textContent = "⬍ Split V";
            splitVBtn.title = "選択中のコマを垂直に50:50分割";
            splitVBtn.style.cssText = "background: #3e352f; color: #fff; border: 1px solid #5a4f47; border-radius: 3px; padding: 3px 8px; cursor: pointer;";
            splitVBtn.onclick = () => splitSelectedRegion("V");

            const swapBtn = document.createElement("button");
            swapBtn.textContent = "⇄ Swap";
            swapBtn.title = "2つの選択コマを入れ替え";
            swapBtn.style.cssText = "background: #3e352f; color: #fff; border: 1px solid #5a4f47; border-radius: 3px; padding: 3px 8px; cursor: pointer;";
            swapBtn.onclick = () => swapSelectedRegions();

            const resetBtn = document.createElement("button");
            resetBtn.textContent = "Reset";
            resetBtn.style.cssText = "background: #5a2e2e; color: #fff; border: 1px solid #7a3e3e; border-radius: 3px; padding: 3px 8px; cursor: pointer; margin-left: auto;";
            resetBtn.onclick = () => {
                if (confirm("コマレイアウトを初期状態にリセットしますか？")) {
                    pushHistory();
                    spec = createDefaultSpec(spec.panel_count);
                    syncToWidget();
                    renderAll();
                }
            };

            toolbar.appendChild(undoBtn);
            toolbar.appendChild(redoBtn);
            toolbar.appendChild(splitHBtn);
            toolbar.appendChild(splitVBtn);
            toolbar.appendChild(swapBtn);
            toolbar.appendChild(resetBtn);

            // メイン作業領域 (Canvas + コマリスト)
            const mainRow = document.createElement("div");
            mainRow.style.cssText = "display: flex; gap: 10px; width: 100%; height: 380px;";

            // 左側: Region Canvas (漫画比率 832:1216 -> 250:365)
            const canvasContainer = document.createElement("div");
            canvasContainer.style.cssText = "position: relative; width: 250px; height: 365px; background: #fff; border: 2px solid #5a4f47; border-radius: 4px; box-shadow: 0 2px 6px rgba(0,0,0,0.5); flex-shrink: 0;";

            const canvas = document.createElement("canvas");
            canvas.width = 250;
            canvas.height = 365;
            canvas.style.cssText = "width: 100%; height: 100%; display: block; cursor: crosshair;";
            canvasContainer.appendChild(canvas);

            const ctx = canvas.getContext("2d");

            // 右側: KOMA 1〜6 リスト & Prompt
            const komaList = document.createElement("div");
            komaList.style.cssText = "display: flex; flex-direction: column; gap: 6px; flex-grow: 1; overflow-y: auto; max-height: 365px; padding-right: 4px;";

            mainRow.appendChild(canvasContainer);
            mainRow.appendChild(komaList);

            container.appendChild(toolbar);
            container.appendChild(mainRow);

            // キャンバス描画
            function renderCanvas() {
                ctx.clearRect(0, 0, canvas.width, canvas.height);

                // 漫画マージン線
                ctx.strokeStyle = "#ddd";
                ctx.lineWidth = 1;
                ctx.strokeRect(5, 5, canvas.width - 10, canvas.height - 10);

                // 有効コマの描画
                spec.regions.forEach(r => {
                    if (!r.enabled || r.id > spec.panel_count) return;

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
                    ctx.fillStyle = colorInfo.hex;
                    ctx.fillRect(rx + 2, ry + 2, Math.min(rw - 4, 60), 18);
                    ctx.fillStyle = "#fff";
                    ctx.font = "bold 10px sans-serif";
                    ctx.fillText(`KOMA ${r.id}`, rx + 5, ry + 15);

                    // リサイズハンドル (選択中のみ)
                    if (isSelected) {
                        drawHandle(rx + rw, ry + rh); // 右下ハンドル
                        drawHandle(rx + rw, ry);      // 右上ハンドル
                        drawHandle(rx, ry + rh);      // 左下ハンドル
                        drawHandle(rx, ry);           // 左上ハンドル
                    }
                });
            }

            function drawHandle(x, y) {
                ctx.fillStyle = "#fff";
                ctx.strokeStyle = "#111";
                ctx.lineWidth = 1.5;
                ctx.fillRect(x - 4, y - 4, 8, 8);
                ctx.strokeRect(x - 4, y - 4, 8, 8);
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
                        transition: all 0.1s;
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
                    chk.onclick = (e) => {
                        e.stopPropagation();
                        pushHistory();
                        r.enabled = chk.checked;
                        syncToWidget();
                        renderAll();
                    };

                    const title = document.createElement("span");
                    title.textContent = `KOMA ${r.id}`;
                    title.style.cssText = `font-weight: bold; color: ${colorInfo.hex};`;

                    header.appendChild(chk);
                    header.appendChild(title);

                    // Prompt入力欄
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
                        min-height: 38px;
                        max-height: 80px;
                        font-family: inherit;
                    `;
                    promptInput.oninput = () => {
                        r.prompt = promptInput.value;
                        syncToWidget();
                    };
                    promptInput.onchange = () => {
                        pushHistory();
                        r.prompt = promptInput.value;
                        syncToWidget();
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
            function splitSelectedRegion(dir) {
                if (selectedRegionIds.size === 0) return;
                const targetId = Array.from(selectedRegionIds)[0];
                const target = spec.regions.find(r => r.id === targetId);
                if (!target) return;

                // 未使用コマを探す
                const unused = spec.regions.find(r => r.id > spec.panel_count || (!r.enabled && r.id !== targetId));
                if (!unused && spec.panel_count >= 6) {
                    alert("これ以上コマを分割できません（最大6コマまで）。");
                    return;
                }

                pushHistory();
                const nextId = unused ? unused.id : spec.panel_count + 1;
                if (spec.panel_count < nextId) {
                    spec.panel_count = nextId;
                }

                const newRegion = spec.regions.find(r => r.id === nextId) || {
                    id: nextId,
                    name: `KOMA ${nextId}`,
                    enabled: true,
                    prompt: "",
                    color: KOMA_COLORS[(nextId - 1) % KOMA_COLORS.length].hex
                };
                newRegion.enabled = true;

                if (dir === "H") {
                    // 水平分割 (左右)
                    const halfW = target.w / 2;
                    newRegion.x = target.x + halfW;
                    newRegion.y = target.y;
                    newRegion.w = halfW;
                    newRegion.h = target.h;
                    target.w = halfW;
                } else {
                    // 垂直分割 (上下)
                    const halfH = target.h / 2;
                    newRegion.x = target.x;
                    newRegion.y = target.y + halfH;
                    newRegion.w = target.w;
                    newRegion.h = halfH;
                    target.h = halfH;
                }

                selectedRegionIds = new Set([targetId, nextId]);
                syncToWidget();
                renderAll();
            }

            // コマ入れ替え処理 (Swap)
            function swapSelectedRegions() {
                const ids = Array.from(selectedRegionIds);
                if (ids.length !== 2) {
                    alert("入れ替える2つのコマをShift+クリックで選択してください。");
                    return;
                }
                const r1 = spec.regions.find(r => r.id === ids[0]);
                const r2 = spec.regions.find(r => r.id === ids[1]);
                if (!r1 || !r2) return;

                pushHistory();
                // 座標とPromptを交換
                const tempX = r1.x, tempY = r1.y, tempW = r1.w, tempH = r1.h, tempPrompt = r1.prompt;
                r1.x = r2.x; r1.y = r2.y; r1.w = r2.w; r1.h = r2.h; r1.prompt = r2.prompt;
                r2.x = tempX; r2.y = tempY; r2.w = tempW; r2.h = tempH; r2.prompt = tempPrompt;

                syncToWidget();
                renderAll();
            }

            // Canvasインタラクション (ドラッグ移動・リサイズ・新規作成)
            let isDragging = false;
            let dragMode = "none"; // "move", "resize", "create"
            let dragHandle = "";   // "se", "ne", "sw", "nw"
            let startX = 0, startY = 0;
            let activeRegion = null;
            let initialRects = new Map();

            canvas.onmousedown = (e) => {
                const rect = canvas.getBoundingClientRect();
                const mx = (e.clientX - rect.left) / canvas.width;
                const my = (e.clientY - rect.top) / canvas.height;
                startX = mx;
                startY = my;

                // ハンドルクリック判定 (選択中コマの右下など)
                dragMode = "none";
                for (const rid of selectedRegionIds) {
                    const r = spec.regions.find(x => x.id === rid);
                    if (!r || !r.enabled) continue;
                    const hx = r.x + r.w;
                    const hy = r.y + r.h;
                    const distSE = Math.hypot(mx - hx, my - hy) * canvas.width;
                    if (distSE < 10) {
                        dragMode = "resize";
                        dragHandle = "se";
                        activeRegion = r;
                        break;
                    }
                }

                // 矩形内部クリック判定 (移動)
                if (dragMode === "none") {
                    let clickedRegion = null;
                    for (let i = spec.regions.length - 1; i >= 0; i--) {
                        const r = spec.regions[i];
                        if (!r.enabled || r.id > spec.panel_count) continue;
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
                        // 空白部分クリック -> 新規作成
                        if (!e.shiftKey) selectedRegionIds = new Set();
                        dragMode = "create";
                        // 空いているコマを探す
                        const unused = spec.regions.find(r => r.id <= spec.panel_count && (!r.enabled || r.w === 0));
                        if (unused) {
                            activeRegion = unused;
                            activeRegion.enabled = true;
                            activeRegion.x = mx;
                            activeRegion.y = my;
                            activeRegion.w = 0.01;
                            activeRegion.h = 0.01;
                            selectedRegionIds = new Set([activeRegion.id]);
                        } else {
                            dragMode = "none";
                        }
                    }
                }

                pushHistory();
                isDragging = true;
                initialRects.clear();
                selectedRegionIds.forEach(rid => {
                    const r = spec.regions.find(x => x.id === rid);
                    if (r) initialRects.set(rid, { x: r.x, y: r.y, w: r.w, h: r.h });
                });

                renderAll();
            };

            window.addEventListener("mousemove", (e) => {
                if (!isDragging || !activeRegion) return;

                const rect = canvas.getBoundingClientRect();
                const mx = Math.max(0, Math.min(1, (e.clientX - rect.left) / canvas.width));
                const my = Math.max(0, Math.min(1, (e.clientY - rect.top) / canvas.height));
                const dx = mx - startX;
                const dy = my - startY;

                if (dragMode === "move") {
                    // 選択中コマを一括移動
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
                        activeRegion.w = Math.max(0.05, Math.min(1 - activeRegion.x, init.w + dx));
                        activeRegion.h = Math.max(0.05, Math.min(1 - activeRegion.y, init.h + dy));
                    }
                } else if (dragMode === "create") {
                    activeRegion.w = Math.max(0.02, mx - startX);
                    activeRegion.h = Math.max(0.02, my - startY);
                }

                renderCanvas();
            });

            window.addEventListener("mouseup", () => {
                if (isDragging) {
                    isDragging = false;
                    dragMode = "none";
                    syncToWidget();
                    renderAll();
                }
            });

            // 初期化・Widget同期
            setTimeout(() => {
                const w = node.widgets.find(x => x.name === "region_spec_data");
                if (w && w.value && w.value !== "{}") {
                    try {
                        const loaded = JSON.parse(w.value);
                        if (loaded && loaded.regions) {
                            spec = loaded;
                        }
                    } catch (err) {}
                }
                syncToWidget();
                renderAll();
            }, 50);

            // ノードへのDOM追加
            node.addDOMWidget("manga_region_editor", "ui", container);

            return r;
        };
    }
});
