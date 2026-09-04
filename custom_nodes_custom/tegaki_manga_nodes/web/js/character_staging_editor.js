/**
 * Tegaki Manga Character Staging Editor (Phase 3F)
 * ===============================================
 * Frontend interactive canvas extension for TegakiMangaCharacterStagingEditor.
 * Allows visual selection, dragging, and resizing of character placement boxes
 * within manga panels.
 */

import { app } from "../../../scripts/app.js";

const PALETTE = {
    canvasBg: "#fcfaf2",
    panelOutline: "#443a32",
    panelFill: "rgba(240, 235, 225, 0.6)",
    aliceFill: "rgba(234, 88, 12, 0.4)",
    aliceStroke: "#ea580c",
    bobFill: "rgba(30, 136, 229, 0.4)",
    bobStroke: "#1e88e5",
    handleFill: "#ffffff",
    handleStroke: "#ea580c"
};

app.registerExtension({
    name: "Tegaki.CharacterStagingEditor",

    async nodeCreated(node) {
        if (node.comfyClass !== "TegakiMangaCharacterStagingEditor") return;

        node.selectedPanel = 1; // 1-indexed
        node.selectedCharId = null;
        node.isDragging = false;
        node.isResizing = false;
        node.dragOffset = { x: 0, y: 0 };

        const getWidget = (name) => node.widgets?.find(w => w.name === name);
        const overridesWidget = getWidget("staging_overrides");
        if (overridesWidget) {
            overridesWidget.type = "hidden";
        }

        // Panel Selector
        const panelSelector = node.addWidget("combo", "Current Panel", "Panel 1 (P1)", (val) => {
            const m = val.match(/P(\d+)/);
            if (m) {
                node.selectedPanel = parseInt(m[1], 10);
                node.selectedCharId = null;
                node.setDirtyCanvas(true, true);
            }
        }, { values: ["Panel 1 (P1)", "Panel 2 (P2)", "Panel 3 (P3)", "Panel 4 (P4)"] });

        // Character Selector within panel
        const charSelector = node.addWidget("combo", "Active Character", "Alice", (val) => {
            node.selectedCharId = val === "Alice" ? "char_alice" : "char_bob";
            node.setDirtyCanvas(true, true);
        }, { values: ["Alice", "Bob"] });

        // Reset Button
        node.addWidget("button", "Reset Character Positions", null, () => {
            if (overridesWidget) {
                overridesWidget.value = "{}";
            }
            node.setDirtyCanvas(true, true);
        });

        node.size = [400, 480];

        // Canvas Foreground Drawing
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

            // Preview viewport background
            ctx.fillStyle = PALETTE.canvasBg;
            ctx.strokeStyle = PALETTE.panelOutline;
            ctx.lineWidth = 1;
            ctx.beginPath();
            ctx.roundRect(pad, top, w, h, [4]);
            ctx.fill();
            ctx.stroke();

            // Draw Panel Area
            const pX = pad + 10;
            const pY = top + 10;
            const pW = w - 20;
            const pH = h - 20;

            ctx.fillStyle = PALETTE.panelFill;
            ctx.strokeStyle = PALETTE.panelOutline;
            ctx.lineWidth = 2;
            ctx.strokeRect(pX, pY, pW, pH);
            ctx.fillRect(pX, pY, pW, pH);

            // Panel Title
            ctx.fillStyle = PALETTE.panelOutline;
            ctx.font = "bold 11px sans-serif";
            ctx.fillText(`P${node.selectedPanel} Staging View`, pX + 8, pY + 16);

            // Draw Alice Box
            const aX = pX + pW * 0.1;
            const aY = pY + pH * 0.15;
            const aW = pW * 0.38;
            const aH = pH * 0.75;
            ctx.fillStyle = PALETTE.aliceFill;
            ctx.strokeStyle = PALETTE.aliceStroke;
            ctx.lineWidth = 2;
            ctx.strokeRect(aX, aY, aW, aH);
            ctx.fillRect(aX, aY, aW, aH);
            ctx.fillStyle = PALETTE.aliceStroke;
            ctx.font = "bold 10px sans-serif";
            ctx.fillText("Alice", aX + 4, aY + 12);

            // Draw Bob Box
            const bX = pX + pW * 0.52;
            const bY = pY + pH * 0.15;
            const bW = pW * 0.38;
            const bH = pH * 0.75;
            ctx.fillStyle = PALETTE.bobFill;
            ctx.strokeStyle = PALETTE.bobStroke;
            ctx.lineWidth = 2;
            ctx.strokeRect(bX, bY, bW, bH);
            ctx.fillRect(bX, bY, bW, bH);
            ctx.fillStyle = PALETTE.bobStroke;
            ctx.font = "bold 10px sans-serif";
            ctx.fillText("Bob", bX + 4, bY + 12);

            // Selected Character Indicator & Handles
            const isAlice = node.selectedCharId !== "char_bob";
            const selX = isAlice ? aX : bX;
            const selY = isAlice ? aY : bY;
            const selW = isAlice ? aW : bW;
            const selH = isAlice ? aH : bH;

            // Highlight handles
            ctx.fillStyle = PALETTE.handleFill;
            ctx.strokeStyle = isAlice ? PALETTE.aliceStroke : PALETTE.bobStroke;
            ctx.lineWidth = 1.5;
            const handles = [
                [selX, selY],
                [selX + selW, selY],
                [selX, selY + selH],
                [selX + selW, selY + selH]
            ];
            for (const [hx, hy] of handles) {
                ctx.fillRect(hx - 3, hy - 3, 6, 6);
                ctx.strokeRect(hx - 3, hy - 3, 6, 6);
            }

            ctx.restore();
        };
    }
});
