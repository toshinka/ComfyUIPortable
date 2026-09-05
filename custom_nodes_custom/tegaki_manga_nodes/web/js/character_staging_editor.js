/**
 * Tegaki Manga Character Staging Editor (Phase 3G)
 * ===============================================
 * Data-driven, interactive canvas extension for TegakiMangaCharacterStagingEditor.
 * Features:
 * - Dynamic data-driven character binding (inspects attending characters per panel)
 * - True mouse pointer interaction: selection, drag move, and corner resize
 * - Strict coordinate clamping within normalized [0.0, 1.0] bounds
 * - Transactional override synchronization: frontend == backend == saved workflow
 * - Reset button to restore layout defaults
 */

import { app } from "../../../scripts/app.js";

const PALETTE = {
    canvasBg: "#fcfaf2",        // futaba cream paper
    panelOutline: "#443a32",     // dark warm border
    panelFill: "rgba(245, 240, 230, 0.7)",
    handleFill: "#ffffff",
    handleStroke: "#ea580c",
    defaultFill: "rgba(22, 163, 74, 0.4)",
    defaultStroke: "#16a34a",
    chars: {
        char_alice: { fill: "rgba(234, 88, 12, 0.4)", stroke: "#ea580c", name: "Alice" },
        char_bob: { fill: "rgba(30, 136, 229, 0.4)", stroke: "#1e88e5", name: "Bob" }
    }
};

app.registerExtension({
    name: "Tegaki.CharacterStagingEditor",

    async nodeCreated(node) {
        if (node.comfyClass !== "TegakiMangaCharacterStagingEditor") return;

        node.selectedPanel = 1;      // 1-indexed (P1..P6)
        node.selectedCharId = null;  // currently selected character
        node.dragState = null;       // { mode: 'move'|'resize', charId, startNormX, startNormY, origArea }
        node.lastCanvasLayout = null;

        const getWidget = (name) => node.widgets?.find(w => w.name === name);
        const overridesWidget = getWidget("staging_overrides");
        if (overridesWidget) {
            overridesWidget.type = "hidden";
        }

        // Helper: Get parsed overrides dictionary
        node.getOverrides = function () {
            if (overridesWidget && overridesWidget.value) {
                try {
                    const parsed = JSON.parse(overridesWidget.value);
                    if (parsed && typeof parsed === "object") return parsed;
                } catch (e) { }
            }
            return {};
        };

        // Helper: Commit updated override for a panel and character
        node.commitOverride = function (panelId, charId, area) {
            const ov = node.getOverrides();
            const pidStr = String(panelId);
            if (!ov[pidStr]) ov[pidStr] = {};
            if (!ov[pidStr][charId] || typeof ov[pidStr][charId] !== "object") {
                ov[pidStr][charId] = {};
            }
            ov[pidStr][charId].area = { ...area };
            if (overridesWidget) {
                overridesWidget.value = JSON.stringify(ov, null, 2);
            }
            node.setDirtyCanvas(true, true);
        };

        // Helper: Get attending characters for the given panel dynamically
        node.getAttendingCharactersForPanel = function (panelId) {
            // 1. Try to read upstream connected node (slot 0: region_spec)
            let panelData = null;
            const linkId = node.inputs?.[0]?.link;
            if (linkId != null && node.graph) {
                const link = node.graph.links[linkId];
                if (link) {
                    const srcNode = node.graph.getNodeById(link.origin_id);
                    if (srcNode) {
                        if (typeof srcNode.getContentData === "function") {
                            const content = srcNode.getContentData();
                            panelData = content.panels?.find(p => p.id === panelId);
                        } else {
                            const w = srcNode.widgets?.find(w => w.name === "panel_content_data" || w.name === "region_spec_data");
                            if (w && w.value) {
                                try {
                                    const parsed = JSON.parse(w.value);
                                    panelData = (parsed.panels || parsed.regions)?.find(p => p.id === panelId);
                                } catch (e) { }
                            }
                        }
                    }
                }
            }

            let chars = [];
            if (panelData && Array.isArray(panelData.characters)) {
                chars = panelData.characters
                    .filter(c => c.enabled !== false)
                    .map(c => ({
                        character_id: c.character_id,
                        name: PALETTE.chars[c.character_id]?.name || c.character_id,
                        area: c.area ? { ...c.area } : { x: 0.1, y: 0.15, w: 0.4, h: 0.75 }
                    }));
            }

            // 2. If no upstream data found, use defaults based on panelId
            if (chars.length === 0) {
                if (panelId === 1 || panelId === 4) {
                    chars = [
                        { character_id: "char_alice", name: "Alice", area: { x: 0.08, y: 0.15, w: 0.45, h: 0.75 } },
                        { character_id: "char_bob", name: "Bob", area: { x: 0.47, y: 0.15, w: 0.45, h: 0.75 } }
                    ];
                } else if (panelId === 2) {
                    chars = [
                        { character_id: "char_alice", name: "Alice", area: { x: 0.15, y: 0.12, w: 0.7, h: 0.8 } }
                    ];
                } else if (panelId === 3) {
                    chars = [
                        { character_id: "char_bob", name: "Bob", area: { x: 0.15, y: 0.12, w: 0.7, h: 0.8 } }
                    ];
                }
            }

            // 3. Apply overrides
            const ov = node.getOverrides();
            const pidStr = String(panelId);
            const pOv = ov[pidStr] || {};
            for (const c of chars) {
                if (pOv[c.character_id]?.area) {
                    c.area = { ...pOv[c.character_id].area };
                }
            }
            return chars;
        };

        // --- Widgets ---
        // Panel Selector
        const panelSelector = node.addWidget("combo", "Current Panel", "Panel 1 (P1)", (val) => {
            const m = val.match(/P(\d+)/);
            if (m) {
                node.selectedPanel = parseInt(m[1], 10);
                node.updateActiveCharSelector();
                node.setDirtyCanvas(true, true);
            }
        }, { values: ["Panel 1 (P1)", "Panel 2 (P2)", "Panel 3 (P3)", "Panel 4 (P4)"] });

        // Character Selector
        const charSelector = node.addWidget("combo", "Active Character", "", (val) => {
            const chars = node.getAttendingCharactersForPanel(node.selectedPanel);
            const match = chars.find(c => c.name === val || c.character_id === val);
            if (match) {
                node.selectedCharId = match.character_id;
                node.updateCharPoseWidgets();
                node.setDirtyCanvas(true, true);
            }
        }, { values: [] });

        // Shot Type Selector (Phase 3K)
        const shotTypeSelector = node.addWidget("combo", "Shot Type", "full_body", (val) => {
            if (!node.selectedCharId) return;
            const ov = node.getOverrides();
            const pidStr = String(node.selectedPanel);
            if (!ov[pidStr]) ov[pidStr] = {};
            if (!ov[pidStr][node.selectedCharId] || typeof ov[pidStr][node.selectedCharId] !== "object") {
                ov[pidStr][node.selectedCharId] = {};
            }
            ov[pidStr][node.selectedCharId].shot_type = val;
            if (overridesWidget) {
                overridesWidget.value = JSON.stringify(ov, null, 2);
            }
            node.setDirtyCanvas(true, true);
        }, { values: ["full_body", "half_body", "bust"] });

        // Pose Preset Selector (Phase 3K)
        const posePresetSelector = node.addWidget("combo", "Pose Preset", "standing_neutral", (val) => {
            if (!node.selectedCharId) return;
            const ov = node.getOverrides();
            const pidStr = String(node.selectedPanel);
            if (!ov[pidStr]) ov[pidStr] = {};
            if (!ov[pidStr][node.selectedCharId] || typeof ov[pidStr][node.selectedCharId] !== "object") {
                ov[pidStr][node.selectedCharId] = {};
            }
            ov[pidStr][node.selectedCharId].pose_preset = val;
            if (overridesWidget) {
                overridesWidget.value = JSON.stringify(ov, null, 2);
            }
            node.setDirtyCanvas(true, true);
        }, { values: ["standing_neutral", "facing_left", "facing_right", "sitting"] });

        node.updateCharPoseWidgets = function () {
            if (!node.selectedCharId) return;
            const ov = node.getOverrides();
            const pidStr = String(node.selectedPanel);
            const charOv = ov[pidStr]?.[node.selectedCharId] || {};
            shotTypeSelector.value = charOv.shot_type || "full_body";
            posePresetSelector.value = charOv.pose_preset || "standing_neutral";
        };

        node.updateActiveCharSelector = function () {
            const chars = node.getAttendingCharactersForPanel(node.selectedPanel);
            const names = chars.map(c => c.name);
            charSelector.options.values = names.length > 0 ? names : ["(None)"];
            if (names.length > 0) {
                if (!node.selectedCharId || !chars.some(c => c.character_id === node.selectedCharId)) {
                    node.selectedCharId = chars[0].character_id;
                }
                const cur = chars.find(c => c.character_id === node.selectedCharId);
                charSelector.value = cur ? cur.name : names[0];
            } else {
                node.selectedCharId = null;
                charSelector.value = "(None)";
            }
            node.updateCharPoseWidgets();
        };

        // Reset Button
        node.addWidget("button", "Reset Character Positions", null, () => {
            if (overridesWidget) {
                overridesWidget.value = "{}";
            }
            node.updateCharPoseWidgets();
            node.setDirtyCanvas(true, true);
        });

        node.size = [400, 540];
        node.updateActiveCharSelector();

        // --- Canvas Rendering ---
        const origOnDrawForeground = node.onDrawForeground;
        node.onDrawForeground = function (ctx) {
            if (origOnDrawForeground) {
                origOnDrawForeground.apply(this, arguments);
            }

            ctx.save();
            const pad = 12;
            const top = 130;
            const w = node.size[0] - pad * 2;
            const h = node.size[1] - top - pad;

            // Viewport background
            ctx.fillStyle = PALETTE.canvasBg;
            ctx.strokeStyle = PALETTE.panelOutline;
            ctx.lineWidth = 1;
            ctx.beginPath();
            ctx.roundRect(pad, top, w, h, [4]);
            ctx.fill();
            ctx.stroke();

            // Panel Interior Box
            const pX = pad + 10;
            const pY = top + 10;
            const pW = w - 20;
            const pH = h - 20;
            node.lastCanvasLayout = { pX, pY, pW, pH };

            ctx.fillStyle = PALETTE.panelFill;
            ctx.strokeStyle = PALETTE.panelOutline;
            ctx.lineWidth = 2;
            ctx.strokeRect(pX, pY, pW, pH);
            ctx.fillRect(pX, pY, pW, pH);

            // Title
            ctx.fillStyle = PALETTE.panelOutline;
            ctx.font = "bold 11px sans-serif";
            ctx.fillText(`P${node.selectedPanel} Staging Layout (Interactive)`, pX + 8, pY + 16);

            // Draw Attending Characters
            const chars = node.getAttendingCharactersForPanel(node.selectedPanel);
            for (const c of chars) {
                const cid = c.character_id;
                const isSelected = (cid === node.selectedCharId);
                const col = PALETTE.chars[cid] || { fill: PALETTE.defaultFill, stroke: PALETTE.defaultStroke, name: c.name };

                const cx = pX + c.area.x * pW;
                const cy = pY + c.area.y * pH;
                const cw = c.area.w * pW;
                const ch = c.area.h * pH;

                // Box
                ctx.fillStyle = col.fill;
                ctx.fillRect(cx, cy, cw, ch);
                ctx.strokeStyle = isSelected ? col.stroke : "rgba(80, 60, 40, 0.4)";
                ctx.lineWidth = isSelected ? 2.5 : 1.5;
                ctx.strokeRect(cx, cy, cw, ch);

                // Label badge
                ctx.fillStyle = col.stroke;
                const label = col.name;
                const badgeW = Math.min(cw, label.length * 8 + 14);
                ctx.fillRect(cx, cy, badgeW, 16);
                ctx.fillStyle = "#ffffff";
                ctx.font = "bold 10px sans-serif";
                ctx.fillText(label, cx + 4, cy + 12);

                // Corner Resize Handle (bottom-right) if selected
                if (isSelected) {
                    const hs = 6;
                    const hx = cx + cw;
                    const hy = cy + ch;
                    ctx.fillStyle = PALETTE.handleFill;
                    ctx.strokeStyle = col.stroke;
                    ctx.lineWidth = 2;
                    ctx.fillRect(hx - hs, hy - hs, hs * 2, hs * 2);
                    ctx.strokeRect(hx - hs, hy - hs, hs * 2, hs * 2);
                }
            }

            ctx.restore();
        };

        // --- Mouse Pointer Event Handlers ---
        node.onMouseDown = function (event, local_pos) {
            if (!node.lastCanvasLayout) return false;
            const { pX, pY, pW, pH } = node.lastCanvasLayout;
            const px = local_pos[0];
            const py = local_pos[1];

            // Inside panel check
            if (px < pX || px > pX + pW || py < pY || py > pY + pH) {
                return false;
            }

            const normX = Math.max(0.0, Math.min(1.0, (px - pX) / pW));
            const normY = Math.max(0.0, Math.min(1.0, (py - pY) / pH));

            const chars = node.getAttendingCharactersForPanel(node.selectedPanel);
            const hsNormX = 10 / pW;
            const hsNormY = 10 / pH;

            // 1. Check resize handle on selected character
            const selChar = chars.find(c => c.character_id === node.selectedCharId);
            if (selChar) {
                const hx = selChar.area.x + selChar.area.w;
                const hy = selChar.area.y + selChar.area.h;
                if (Math.abs(normX - hx) <= hsNormX && Math.abs(normY - hy) <= hsNormY) {
                    node.dragState = {
                        mode: "resize",
                        charId: selChar.character_id,
                        startNormX: normX,
                        startNormY: normY,
                        origArea: { ...selChar.area }
                    };
                    node.setDirtyCanvas(true, true);
                    return true;
                }
            }

            // 2. Check hit inside character box (reverse order for top-most box)
            let hitChar = null;
            for (let i = chars.length - 1; i >= 0; i--) {
                const c = chars[i];
                if (normX >= c.area.x && normX <= c.area.x + c.area.w &&
                    normY >= c.area.y && normY <= c.area.y + c.area.h) {
                    hitChar = c;
                    break;
                }
            }

            if (hitChar) {
                node.selectedCharId = hitChar.character_id;
                const cur = chars.find(c => c.character_id === hitChar.character_id);
                if (cur) charSelector.value = cur.name;
                node.updateCharPoseWidgets();

                node.dragState = {
                    mode: "move",
                    charId: hitChar.character_id,
                    startNormX: normX,
                    startNormY: normY,
                    origArea: { ...hitChar.area }
                };
                node.setDirtyCanvas(true, true);
                return true;
            }

            return false;
        };

        node.onMouseMove = function (event, local_pos) {
            if (!node.dragState || !node.lastCanvasLayout) return false;
            const { pX, pY, pW, pH } = node.lastCanvasLayout;
            const px = local_pos[0];
            const py = local_pos[1];

            const normX = Math.max(0.0, Math.min(1.0, (px - pX) / pW));
            const normY = Math.max(0.0, Math.min(1.0, (py - pY) / pH));
            const dx = normX - node.dragState.startNormX;
            const dy = normY - node.dragState.startNormY;

            const chars = node.getAttendingCharactersForPanel(node.selectedPanel);
            const targetChar = chars.find(c => c.character_id === node.dragState.charId);
            if (!targetChar) return false;

            const minSize = 0.05;

            if (node.dragState.mode === "move") {
                let newX = node.dragState.origArea.x + dx;
                let newY = node.dragState.origArea.y + dy;
                newX = Math.max(0.0, Math.min(1.0 - targetChar.area.w, newX));
                newY = Math.max(0.0, Math.min(1.0 - targetChar.area.h, newY));
                targetChar.area.x = Math.round(newX * 1000) / 1000;
                targetChar.area.y = Math.round(newY * 1000) / 1000;
                node.commitOverride(node.selectedPanel, targetChar.character_id, targetChar.area);
                return true;
            }

            if (node.dragState.mode === "resize") {
                let newW = node.dragState.origArea.w + dx;
                let newH = node.dragState.origArea.h + dy;
                newW = Math.max(minSize, Math.min(1.0 - targetChar.area.x, newW));
                newH = Math.max(minSize, Math.min(1.0 - targetChar.area.y, newH));
                targetChar.area.w = Math.round(newW * 1000) / 1000;
                targetChar.area.h = Math.round(newH * 1000) / 1000;
                node.commitOverride(node.selectedPanel, targetChar.character_id, targetChar.area);
                return true;
            }

            return false;
        };

        node.onMouseUp = function () {
            if (node.dragState) {
                node.dragState = null;
                node.setDirtyCanvas(true, true);
                return true;
            }
            return false;
        };
    }
});
