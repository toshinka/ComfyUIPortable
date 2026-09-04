/**
 * Tegaki Manga Cast Master Editor (Phase 3D.1)
 * ============================================
 * Frontend extension for TegakiMangaCastMaster.
 * Provides character selection, immutable ID protection, base prompt / negative editing,
 * enable/disable toggle, LoRA plan notification, and character addition/deletion.
 */

import { app } from "../../../scripts/app.js";

const PALETTE = {
    cardBg: "#fcfaf2",
    cardBorder: "#d4c8b8",
    activeCardBorder: "#ea580c",
    textDark: "#2c2621",
    textMuted: "#7a6e65",
    accent: "#ea580c",
    badgeEnabled: "#16a34a",
    badgeDisabled: "#dc2626",
    loraNoticeBg: "rgba(234, 88, 12, 0.10)",
    loraNoticeText: "#c2410c"
};

const DEFAULT_INITIAL_CAST = {
    version: 1,
    characters: [
        {
            id: "char_alice",
            name: "Alice",
            enabled: true,
            prompt: "1girl, blonde twin tails, blue eyes, school uniform",
            negative_prompt: "blurry, low quality",
            loras: []
        },
        {
            id: "char_bob",
            name: "Bob",
            enabled: true,
            prompt: "1boy, short brown hair, school uniform",
            negative_prompt: "bad anatomy",
            loras: []
        }
    ]
};

app.registerExtension({
    name: "Tegaki.CastMasterEditor",

    async nodeCreated(node) {
        if (node.comfyClass !== "TegakiMangaCastMaster") return;

        node.selectedCharIdx = 0;

        const getWidget = (name) => node.widgets?.find(w => w.name === name);
        const specWidget = getWidget("cast_spec_data");
        if (specWidget) {
            specWidget.type = "hidden";
        }

        // Helper to get parsed CAST_SPEC
        node.getSpec = function () {
            if (specWidget && specWidget.value) {
                try {
                    const parsed = JSON.parse(specWidget.value);
                    if (parsed && Array.isArray(parsed.characters)) {
                        return parsed;
                    }
                } catch (e) { }
            }
            return JSON.parse(JSON.stringify(DEFAULT_INITIAL_CAST));
        };

        // Helper to commit updated CAST_SPEC
        node.setSpec = function (spec) {
            if (specWidget) {
                specWidget.value = JSON.stringify(spec, null, 2);
            }
            node.updateWidgetsFromState();
            node.setDirtyCanvas(true, true);
        };

        // Get currently selected character
        node.getSelectedChar = function () {
            const spec = node.getSpec();
            const chars = spec.characters || [];
            if (node.selectedCharIdx < 0) node.selectedCharIdx = 0;
            if (node.selectedCharIdx >= chars.length) node.selectedCharIdx = Math.max(0, chars.length - 1);
            return chars[node.selectedCharIdx] || null;
        };

        // --- Custom interactive widgets ---
        const charSelectorWidget = node.addWidget("combo", "Selected Character", "Alice (char_alice)", (val) => {
            const spec = node.getSpec();
            const idx = (spec.characters || []).findIndex(c => `${c.name} (${c.id})` === val);
            if (idx >= 0) {
                node.selectedCharIdx = idx;
                node.updateWidgetsFromState();
                node.setDirtyCanvas(true, true);
            }
        }, { values: [] });

        const nameWidget = node.addWidget("text", "Name", "", (val) => {
            const spec = node.getSpec();
            const char = spec.characters?.[node.selectedCharIdx];
            if (char && val.trim()) {
                char.name = val.trim();
                node.setSpec(spec);
            }
        });

        const idDisplayWidget = node.addWidget("text", "ID (Stable)", "", () => {
            // Read-only: restore original ID if modified
            const char = node.getSelectedChar();
            if (char && idDisplayWidget.value !== char.id) {
                idDisplayWidget.value = char.id;
            }
        });

        const enabledWidget = node.addWidget("toggle", "Enabled", true, (val) => {
            const spec = node.getSpec();
            const char = spec.characters?.[node.selectedCharIdx];
            if (char) {
                char.enabled = Boolean(val);
                node.setSpec(spec);
            }
        });

        const promptWidget = node.addWidget("customtext", "Base Prompt", "", (val) => {
            const spec = node.getSpec();
            const char = spec.characters?.[node.selectedCharIdx];
            if (char) {
                char.prompt = val;
                node.setSpec(spec);
            }
        }, { multiline: true });

        const negPromptWidget = node.addWidget("customtext", "Base Negative", "", (val) => {
            const spec = node.getSpec();
            const char = spec.characters?.[node.selectedCharIdx];
            if (char) {
                char.negative_prompt = val;
                node.setSpec(spec);
            }
        }, { multiline: true });

        // Add Character Button
        node.addWidget("button", "+ Add Character (Max 6)", null, () => {
            const spec = node.getSpec();
            if ((spec.characters || []).length >= 6) {
                alert("Maximum character capacity (6) reached.");
                return;
            }
            const existingIds = new Set(spec.characters.map(c => c.id));
            let counter = spec.characters.length + 1;
            let candidateId = `char_00${counter}`;
            while (existingIds.has(candidateId)) {
                counter++;
                candidateId = `char_00${counter}`;
            }
            const newChar = {
                id: candidateId,
                name: `Character ${counter}`,
                enabled: true,
                prompt: "",
                negative_prompt: "",
                loras: []
            };
            spec.characters.push(newChar);
            node.selectedCharIdx = spec.characters.length - 1;
            node.setSpec(spec);
        });

        // Delete Character Button
        node.addWidget("button", "Delete Selected Character", null, () => {
            const spec = node.getSpec();
            if ((spec.characters || []).length <= 1) {
                alert("Cannot delete the only remaining character in CAST_SPEC.");
                return;
            }
            const targetChar = node.getSelectedChar();
            if (!targetChar) return;

            // Confirm
            if (!confirm(`Are you sure you want to delete '${targetChar.name}' (${targetChar.id})?`)) {
                return;
            }

            spec.characters = spec.characters.filter(c => c.id !== targetChar.id);
            node.selectedCharIdx = Math.max(0, node.selectedCharIdx - 1);
            node.setSpec(spec);
        });

        // Sync widget display values from current state
        node.updateWidgetsFromState = function () {
            const spec = node.getSpec();
            const chars = spec.characters || [];
            charSelectorWidget.options.values = chars.map(c => `${c.name} (${c.id})`);

            const current = node.getSelectedChar();
            if (current) {
                charSelectorWidget.value = `${current.name} (${current.id})`;
                nameWidget.value = current.name || "";
                idDisplayWidget.value = current.id || "";
                enabledWidget.value = Boolean(current.enabled);
                promptWidget.value = current.prompt || "";
                negPromptWidget.value = current.negative_prompt || "";
            }
        };

        // Initial widget update
        node.updateWidgetsFromState();

        // Node resizing
        node.size = [360, 480];

        // Custom canvas foreground rendering: Display summary card and LoRA Plan notice
        const origOnDrawForeground = node.onDrawForeground;
        node.onDrawForeground = function (ctx) {
            if (origOnDrawForeground) {
                origOnDrawForeground.apply(this, arguments);
            }

            const spec = node.getSpec();
            const chars = spec.characters || [];
            const current = node.getSelectedChar();
            if (!current) return;

            ctx.save();
            const cardX = 10;
            const cardY = node.size[1] - 80;
            const cardW = node.size[0] - 20;
            const cardH = 70;

            // Card background
            ctx.fillStyle = PALETTE.cardBg;
            ctx.strokeStyle = PALETTE.cardBorder;
            ctx.lineWidth = 1;
            ctx.beginPath();
            ctx.roundRect(cardX, cardY, cardW, cardH, [6]);
            ctx.fill();
            ctx.stroke();

            // Character Header & Status Badge
            ctx.font = "bold 12px sans-serif";
            ctx.fillStyle = PALETTE.textDark;
            ctx.fillText(`${current.name} [${current.id}]`, cardX + 10, cardY + 20);

            const badgeText = current.enabled ? "ACTIVE" : "DISABLED";
            ctx.font = "bold 10px sans-serif";
            ctx.fillStyle = current.enabled ? PALETTE.badgeEnabled : PALETTE.badgeDisabled;
            ctx.fillText(badgeText, cardX + cardW - 70, cardY + 20);

            // LoRA Plan notice
            ctx.fillStyle = PALETTE.loraNoticeBg;
            ctx.fillRect(cardX + 8, cardY + 30, cardW - 16, 20);
            ctx.fillStyle = PALETTE.loraNoticeText;
            ctx.font = "10px sans-serif";
            ctx.fillText("Character LoRA Plan: [NOT YET SPATIALLY APPLIED - Plan Only]", cardX + 14, cardY + 44);

            // Cast Count
            ctx.fillStyle = PALETTE.textMuted;
            ctx.font = "10px sans-serif";
            ctx.fillText(`Cast Members: ${chars.length} / 6  |  Selected: ${node.selectedCharIdx + 1}`, cardX + 10, cardY + 62);

            ctx.restore();
        };
    }
});
