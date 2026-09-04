/**
 * Tegaki Manga Panel Content Editor (Phase 3G)
 * ============================================
 * Frontend extension for TegakiMangaPanelContentEditor.
 * Provides progressive authoring:
 * - Selectable panel tab (P1..P6)
 * - Single-panel focused editing of Scene Prompt and Negative Prompt
 * - Dynamic Character selector (from cast_spec or panel data, not hardcoded Alice/Bob)
 * - Character attendance toggle (Attend in this Panel ✓ / □)
 * - Character acting prompt & negative overrides
 * - Optional SubScene progressive disclosure (+ Advanced Scene)
 */

import { app } from "../../../scripts/app.js";

const PALETTE = {
    cardBg: "#fcfaf2",
    cardBorder: "#d4c8b8",
    accent: "#ea580c",
    textDark: "#2c2621",
    textMuted: "#7a6e65",
    badgeActive: "#16a34a",
    badgeInactive: "#9ca3af",
    subsceneNoticeBg: "rgba(234, 88, 12, 0.08)",
    subsceneNoticeText: "#c2410c"
};

app.registerExtension({
    name: "Tegaki.PanelContentEditor",

    async nodeCreated(node) {
        if (node.comfyClass !== "TegakiMangaPanelContentEditor") return;

        node.selectedPanelIdx = 0; // 0-indexed (0 == P1)
        node.selectedCharId = "char_alice";

        const getWidget = (name) => node.widgets?.find(w => w.name === name);
        const dataWidget = getWidget("panel_content_data");
        if (dataWidget) {
            dataWidget.type = "hidden";
        }

        // Helper: Get parsed content data
        node.getContentData = function () {
            if (dataWidget && dataWidget.value) {
                try {
                    const parsed = JSON.parse(dataWidget.value);
                    if (parsed && Array.isArray(parsed.panels)) {
                        return parsed;
                    }
                } catch (e) { }
            }
            return {
                version: 1,
                panel_count: 4,
                panels: [
                    { id: 1, name: "Panel 1", prompt: "", negative_prompt: "", characters: [], subscenes: [] },
                    { id: 2, name: "Panel 2", prompt: "", negative_prompt: "", characters: [], subscenes: [] },
                    { id: 3, name: "Panel 3", prompt: "", negative_prompt: "", characters: [], subscenes: [] },
                    { id: 4, name: "Panel 4", prompt: "", negative_prompt: "", characters: [], subscenes: [] }
                ]
            };
        };

        // Helper: Commit updated content data
        node.setContentData = function (data) {
            if (dataWidget) {
                dataWidget.value = JSON.stringify(data, null, 2);
            }
            node.updateWidgetsFromState();
            node.setDirtyCanvas(true, true);
        };

        node.getSelectedPanel = function () {
            const data = node.getContentData();
            const panels = data.panels || [];
            if (node.selectedPanelIdx < 0) node.selectedPanelIdx = 0;
            if (node.selectedPanelIdx >= panels.length) node.selectedPanelIdx = Math.max(0, panels.length - 1);
            return panels[node.selectedPanelIdx] || null;
        };

        // Helper: Discover available characters dynamically from cast_spec or existing panels
        node.getAvailableCharacters = function () {
            const charsMap = new Map();
            // Default known characters
            charsMap.set("char_alice", "Alice");
            charsMap.set("char_bob", "Bob");

            // 1. Try to read upstream cast_spec from input slot 1
            const linkId = node.inputs?.[1]?.link;
            if (linkId != null && node.graph) {
                const link = node.graph.links[linkId];
                if (link) {
                    const srcNode = node.graph.getNodeById(link.origin_id);
                    if (srcNode) {
                        const castWidget = srcNode.widgets?.find(w => w.name === "cast_data" || w.name === "cast_spec");
                        if (castWidget && castWidget.value) {
                            try {
                                const parsed = JSON.parse(castWidget.value);
                                if (Array.isArray(parsed.characters)) {
                                    for (const c of parsed.characters) {
                                        if (c.id) charsMap.set(c.id, c.name || c.id);
                                    }
                                }
                            } catch (e) { }
                        }
                    }
                }
            }

            // 2. Read characters from panels in content data
            const data = node.getContentData();
            for (const p of data.panels || []) {
                for (const c of p.characters || []) {
                    if (c.character_id && !charsMap.has(c.character_id)) {
                        charsMap.set(c.character_id, c.character_id);
                    }
                }
            }

            return Array.from(charsMap.entries()).map(([id, name]) => ({ id, name }));
        };

        // --- Interactive Controls ---
        const panelSelectorWidget = node.addWidget("combo", "Selected Panel", "Panel 1 (P1)", (val) => {
            const match = val.match(/P(\d+)/);
            if (match) {
                node.selectedPanelIdx = parseInt(match[1], 10) - 1;
                node.updateWidgetsFromState();
                node.setDirtyCanvas(true, true);
            }
        }, { values: ["Panel 1 (P1)", "Panel 2 (P2)", "Panel 3 (P3)", "Panel 4 (P4)"] });

        const scenePromptWidget = node.addWidget("customtext", "Scene / Background Prompt", "", (val) => {
            const data = node.getContentData();
            const panel = data.panels?.[node.selectedPanelIdx];
            if (panel) {
                panel.prompt = val;
                node.setContentData(data);
            }
        }, { multiline: true });

        const sceneNegWidget = node.addWidget("customtext", "Scene Negative Prompt", "", (val) => {
            const data = node.getContentData();
            const panel = data.panels?.[node.selectedPanelIdx];
            if (panel) {
                panel.negative_prompt = val;
                node.setContentData(data);
            }
        }, { multiline: true });

        // Dynamic Character Selector (Dynamic Cast Selection)
        const charSelectorWidget = node.addWidget("combo", "Selected Character", "Alice (char_alice)", (val) => {
            const m = val.match(/\(([^)]+)\)/);
            node.selectedCharId = m ? m[1] : val;
            node.updateCharacterFields();
            node.setDirtyCanvas(true, true);
        }, { values: ["Alice (char_alice)", "Bob (char_bob)"] });

        // Character Attendance Toggle
        const attendToggleWidget = node.addWidget("toggle", "Attend in this Panel", true, (val) => {
            const data = node.getContentData();
            const panel = data.panels?.[node.selectedPanelIdx];
            if (panel && node.selectedCharId) {
                panel.characters = panel.characters || [];
                let binding = panel.characters.find(c => c.character_id === node.selectedCharId);
                if (val && !binding) {
                    panel.characters.push({
                        character_id: node.selectedCharId,
                        enabled: true,
                        prompt_override: "",
                        negative_prompt_override: "",
                        area: { x: 0.1, y: 0.15, w: 0.4, h: 0.8 }
                    });
                } else if (!val && binding) {
                    panel.characters = panel.characters.filter(c => c.character_id !== node.selectedCharId);
                }
                node.setContentData(data);
            }
        });

        // Character Acting Prompt Override
        const actingWidget = node.addWidget("text", "Character Acting Prompt", "", (val) => {
            const data = node.getContentData();
            const panel = data.panels?.[node.selectedPanelIdx];
            if (panel && node.selectedCharId) {
                const binding = (panel.characters || []).find(c => c.character_id === node.selectedCharId);
                if (binding) {
                    binding.prompt_override = val;
                    node.setContentData(data);
                }
            }
        });

        // Character Negative Override
        const actingNegWidget = node.addWidget("text", "Character Negative Override", "", (val) => {
            const data = node.getContentData();
            const panel = data.panels?.[node.selectedPanelIdx];
            if (panel && node.selectedCharId) {
                const binding = (panel.characters || []).find(c => c.character_id === node.selectedCharId);
                if (binding) {
                    binding.negative_prompt_override = val;
                    node.setContentData(data);
                }
            }
        });

        // Progressive SubScene Toggle
        const advancedSubsceneToggle = node.addWidget("toggle", "+ Advanced Scene (SubScenes)", false, (val) => {
            const data = node.getContentData();
            const panel = data.panels?.[node.selectedPanelIdx];
            if (panel) {
                if (val && (!panel.subscenes || panel.subscenes.length === 0)) {
                    panel.subscenes = [
                        { id: "sub_a", enabled: true, prompt: "left side scene", negative_prompt: "", area: { x: 0.0, y: 0.0, w: 0.5, h: 1.0 }, character_bindings: [] },
                        { id: "sub_b", enabled: true, prompt: "right side scene", negative_prompt: "", area: { x: 0.5, y: 0.0, w: 0.5, h: 1.0 }, character_bindings: [] }
                    ];
                } else if (!val) {
                    panel.subscenes = [];
                }
                node.setContentData(data);
            }
        });

        // Update Character-specific widgets from current panel and selected character
        node.updateCharacterFields = function () {
            const current = node.getSelectedPanel();
            if (current && node.selectedCharId) {
                const binding = (current.characters || []).find(c => c.character_id === node.selectedCharId);
                attendToggleWidget.value = Boolean(binding);
                actingWidget.value = binding?.prompt_override || "";
                actingNegWidget.value = binding?.negative_prompt_override || "";
            }
        };

        // Sync widget display values from current state
        node.updateWidgetsFromState = function () {
            const data = node.getContentData();
            const panels = data.panels || [];
            panelSelectorWidget.options.values = panels.map((p, idx) => `Panel ${idx + 1} (P${idx + 1})`);

            // Populate character options dynamically
            const availChars = node.getAvailableCharacters();
            const charOptions = availChars.map(c => `${c.name} (${c.id})`);
            charSelectorWidget.options.values = charOptions;

            if (!node.selectedCharId || !availChars.some(c => c.id === node.selectedCharId)) {
                node.selectedCharId = availChars[0]?.id || "char_alice";
            }
            const curChar = availChars.find(c => c.id === node.selectedCharId);
            charSelectorWidget.value = curChar ? `${curChar.name} (${curChar.id})` : charOptions[0];

            const current = node.getSelectedPanel();
            if (current) {
                panelSelectorWidget.value = `Panel ${node.selectedPanelIdx + 1} (P${node.selectedPanelIdx + 1})`;
                scenePromptWidget.value = current.prompt || "";
                sceneNegWidget.value = current.negative_prompt || "";

                node.updateCharacterFields();

                const hasSub = Array.isArray(current.subscenes) && current.subscenes.length > 0;
                advancedSubsceneToggle.value = hasSub;
            }
        };

        // Initial widget update
        node.updateWidgetsFromState();
        node.size = [420, 620];

        // Canvas Overview Summary
        const origOnDrawForeground = node.onDrawForeground;
        node.onDrawForeground = function (ctx) {
            if (origOnDrawForeground) {
                origOnDrawForeground.apply(this, arguments);
            }

            ctx.save();
            const pad = 10;
            const top = 340;
            const w = node.size[0] - pad * 2;
            const h = node.size[1] - top - pad;

            // Overview card background
            ctx.fillStyle = PALETTE.cardBg;
            ctx.strokeStyle = PALETTE.cardBorder;
            ctx.lineWidth = 1;
            ctx.beginPath();
            ctx.roundRect(pad, top, w, h, [4]);
            ctx.fill();
            ctx.stroke();

            // Header
            ctx.fillStyle = PALETTE.textDark;
            ctx.font = "bold 11px sans-serif";
            ctx.fillText(`P${node.selectedPanelIdx + 1} Staging Overview`, pad + 8, top + 18);

            const current = node.getSelectedPanel();
            if (current) {
                // Scene Prompt preview
                ctx.fillStyle = PALETTE.textMuted;
                ctx.font = "10px sans-serif";
                const pText = (current.prompt || "(no prompt)").trim();
                const truncP = pText.length > 48 ? pText.substring(0, 48) + "..." : pText;
                ctx.fillText(`Scene: ${truncP}`, pad + 8, top + 34);

                // Attending Characters Badges
                ctx.fillStyle = PALETTE.textDark;
                ctx.fillText("Attending Cast:", pad + 8, top + 52);

                let badgeX = pad + 90;
                const chars = current.characters || [];
                if (chars.length === 0) {
                    ctx.fillStyle = PALETTE.badgeInactive;
                    ctx.fillText("(None - Background Only)", badgeX, top + 52);
                } else {
                    for (const c of chars) {
                        const name = c.character_id.replace("char_", "");
                        const bw = name.length * 7 + 12;
                        ctx.fillStyle = PALETTE.badgeActive;
                        ctx.beginPath();
                        ctx.roundRect(badgeX, top + 41, bw, 15, [3]);
                        ctx.fill();
                        ctx.fillStyle = "#ffffff";
                        ctx.font = "bold 9px sans-serif";
                        ctx.fillText(name, badgeX + 5, top + 52);
                        badgeX += bw + 6;
                    }
                }

                // SubScene Indicator
                if (current.subscenes && current.subscenes.length > 0) {
                    ctx.fillStyle = PALETTE.subsceneNoticeBg;
                    ctx.beginPath();
                    ctx.roundRect(pad + 8, top + 64, w - 16, 20, [3]);
                    ctx.fill();
                    ctx.fillStyle = PALETTE.subsceneNoticeText;
                    ctx.font = "italic 9px sans-serif";
                    ctx.fillText(`★ SubScenes active: ${current.subscenes.length} sub-regions split`, pad + 14, top + 78);
                }
            }

            ctx.restore();
        };
    }
});
