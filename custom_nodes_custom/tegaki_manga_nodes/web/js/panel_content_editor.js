/**
 * Tegaki Manga Panel Content Editor (Phase 3F)
 * ============================================
 * Frontend extension for TegakiMangaPanelContentEditor.
 * Provides progressive authoring:
 * - Selectable panel tab (P1..P6)
 * - Single-panel focused editing of Scene Prompt and Negative Prompt
 * - Character attendance toggles (Alice ✓, Bob □, etc.) and acting prompt overrides
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

        const getWidget = (name) => node.widgets?.find(w => w.name === name);
        const dataWidget = getWidget("panel_content_data");
        if (dataWidget) {
            dataWidget.type = "hidden";
        }

        // Helper to get parsed data
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

        // Helper to commit updated content data
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

        // Attendance: Alice
        const aliceToggleWidget = node.addWidget("toggle", "Attend: Alice", true, (val) => {
            const data = node.getContentData();
            const panel = data.panels?.[node.selectedPanelIdx];
            if (panel) {
                let binding = (panel.characters || []).find(c => c.character_id === "char_alice");
                if (val && !binding) {
                    panel.characters = panel.characters || [];
                    panel.characters.push({
                        character_id: "char_alice",
                        enabled: true,
                        prompt_override: "",
                        negative_prompt_override: "",
                        area: { x: 0.1, y: 0.15, w: 0.4, h: 0.8 }
                    });
                } else if (!val && binding) {
                    panel.characters = panel.characters.filter(c => c.character_id !== "char_alice");
                }
                node.setContentData(data);
            }
        });

        const aliceActingWidget = node.addWidget("text", "Alice Acting", "", (val) => {
            const data = node.getContentData();
            const panel = data.panels?.[node.selectedPanelIdx];
            if (panel) {
                const binding = (panel.characters || []).find(c => c.character_id === "char_alice");
                if (binding) {
                    binding.prompt_override = val;
                    node.setContentData(data);
                }
            }
        });

        // Attendance: Bob
        const bobToggleWidget = node.addWidget("toggle", "Attend: Bob", true, (val) => {
            const data = node.getContentData();
            const panel = data.panels?.[node.selectedPanelIdx];
            if (panel) {
                let binding = (panel.characters || []).find(c => c.character_id === "char_bob");
                if (val && !binding) {
                    panel.characters = panel.characters || [];
                    panel.characters.push({
                        character_id: "char_bob",
                        enabled: true,
                        prompt_override: "",
                        negative_prompt_override: "",
                        area: { x: 0.5, y: 0.15, w: 0.4, h: 0.8 }
                    });
                } else if (!val && binding) {
                    panel.characters = panel.characters.filter(c => c.character_id !== "char_bob");
                }
                node.setContentData(data);
            }
        });

        const bobActingWidget = node.addWidget("text", "Bob Acting", "", (val) => {
            const data = node.getContentData();
            const panel = data.panels?.[node.selectedPanelIdx];
            if (panel) {
                const binding = (panel.characters || []).find(c => c.character_id === "char_bob");
                if (binding) {
                    binding.prompt_override = val;
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

        // Sync widget display values from current state
        node.updateWidgetsFromState = function () {
            const data = node.getContentData();
            const panels = data.panels || [];
            panelSelectorWidget.options.values = panels.map((p, idx) => `Panel ${idx + 1} (P${idx + 1})`);

            const current = node.getSelectedPanel();
            if (current) {
                panelSelectorWidget.value = `Panel ${node.selectedPanelIdx + 1} (P${node.selectedPanelIdx + 1})`;
                scenePromptWidget.value = current.prompt || "";
                sceneNegWidget.value = current.negative_prompt || "";

                const aliceBinding = (current.characters || []).find(c => c.character_id === "char_alice");
                aliceToggleWidget.value = Boolean(aliceBinding);
                aliceActingWidget.value = aliceBinding?.prompt_override || "";

                const bobBinding = (current.characters || []).find(c => c.character_id === "char_bob");
                bobToggleWidget.value = Boolean(bobBinding);
                bobActingWidget.value = bobBinding?.prompt_override || "";

                const hasSub = Array.isArray(current.subscenes) && current.subscenes.length > 0;
                advancedSubsceneToggle.value = hasSub;
            }
        };

        // Initial widget update
        node.updateWidgetsFromState();
        node.size = [420, 600];

        // Draw foreground summary
        const origOnDrawForeground = node.onDrawForeground;
        node.onDrawForeground = function (ctx) {
            if (origOnDrawForeground) {
                origOnDrawForeground.apply(this, arguments);
            }

            const current = node.getSelectedPanel();
            if (!current) return;

            ctx.save();
            const cardX = 10;
            const cardY = node.size[1] - 80;
            const cardW = node.size[0] - 20;
            const cardH = 70;

            ctx.fillStyle = PALETTE.cardBg;
            ctx.strokeStyle = PALETTE.cardBorder;
            ctx.lineWidth = 1;
            ctx.beginPath();
            ctx.roundRect(cardX, cardY, cardW, cardH, [6]);
            ctx.fill();
            ctx.stroke();

            // Panel Title
            ctx.font = "bold 12px sans-serif";
            ctx.fillStyle = PALETTE.textDark;
            ctx.fillText(`P${node.selectedPanelIdx + 1}: ${current.name || "Panel"}`, cardX + 10, cardY + 20);

            // Attendance list
            const attending = (current.characters || []).map(c => c.character_id.replace("char_", ""));
            ctx.font = "11px sans-serif";
            ctx.fillStyle = attending.length > 0 ? PALETTE.badgeActive : PALETTE.badgeInactive;
            const attText = attending.length > 0 ? `Attending: [${attending.join(", ")}]` : "Solo Scene (No Characters)";
            ctx.fillText(attText, cardX + 10, cardY + 40);

            // Subscene status
            const hasSub = Array.isArray(current.subscenes) && current.subscenes.length > 0;
            ctx.font = "10px sans-serif";
            if (hasSub) {
                ctx.fillStyle = PALETTE.subsceneNoticeText;
                ctx.fillText(`Mode: Advanced (${current.subscenes.length} SubScenes)`, cardX + 10, cardY + 58);
            } else {
                ctx.fillStyle = PALETTE.textMuted;
                ctx.fillText("Mode: Simple 1-Panel 1-Scene (Standard)", cardX + 10, cardY + 58);
            }

            ctx.restore();
        };
    }
});
