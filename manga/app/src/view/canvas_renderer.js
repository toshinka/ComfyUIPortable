/**
 * canvas_renderer.js — Standalone 2D Canvas Renderer for Manga Document
 * =====================================================================
 * TEGAKI Manga Authoring Workspace (M1A)
 * 
 * Decoupled from node graph host and ComfyUI DOM widgets.
 * Renders authoring document layers with exact spatial mapping:
 * - Page border & background
 * - Visual frames (with border thickness)
 * - Rough manga guides & figure regions
 * - Semantic scenes (color-coded boxes)
 * - Character instances (with cast colors)
 * - Highlights currently selected item in session state.
 */

const SCENE_PALETTE = [
    { hex: "#e53935", rgb: [229, 57, 53] },
    { hex: "#1e88e5", rgb: [30, 136, 229] },
    { hex: "#43a047", rgb: [67, 160, 71] },
    { hex: "#fb8c00", rgb: [251, 140, 0] },
    { hex: "#8e24aa", rgb: [142, 36, 170] },
    { hex: "#00acc1", rgb: [0, 172, 193] }
];

const CAST_PALETTE = [
    { hex: "#06b6d4", rgb: [6, 182, 212] },
    { hex: "#eab308", rgb: [234, 179, 8] },
    { hex: "#ec4899", rgb: [236, 72, 153] },
    { hex: "#a855f7", rgb: [168, 85, 247] },
    { hex: "#22c55e", rgb: [34, 197, 94] },
    { hex: "#f97316", rgb: [249, 115, 22] }
];

export function renderMangaCanvas(canvas, document, sessionState, pageIndex = 0, imageCache = {}) {
    if (!canvas || !document || !document.pages || !document.pages[pageIndex]) return;
    const page = document.pages[pageIndex];
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const cw = canvas.width;
    const ch = canvas.height;

    // 1. Clear & draw page background
    ctx.clearRect(0, 0, cw, ch);
    ctx.fillStyle = "#ffffff";
    ctx.fillRect(0, 0, cw, ch);

    // Page border
    ctx.strokeStyle = "#cbd5e1";
    ctx.lineWidth = 1;
    ctx.strokeRect(0, 0, cw, ch);

    const activeTab = sessionState ? sessionState.activeTab : "scenes";

    // 2. Draw Visual Frames (Border Layer)
    const frames = page.visual_frames || [];
    frames.forEach((fr, idx) => {
        const area = fr.area || fr.shape || { x: 0, y: 0, w: 1, h: 1 };
        const isSelected = (sessionState && sessionState.selectedFrameId === fr.frame_id);
        const rx = area.x * cw;
        const ry = area.y * ch;
        const rw = area.w * cw;
        const rh = area.h * ch;

        // Fill translucent if frames layer is active
        if (activeTab === "frames") {
            ctx.fillStyle = isSelected ? "rgba(59, 130, 246, 0.12)" : "rgba(0, 0, 0, 0.03)";
            ctx.fillRect(rx, ry, rw, rh);
        }

        const thickness = Math.max(1, Math.min(10, Math.round((fr.border_thickness || 4) * (cw / (page.width_px || 832)))));
        ctx.strokeStyle = isSelected ? "#2563eb" : (fr.border_color || "#18181b");
        ctx.lineWidth = isSelected ? Math.max(thickness, 3) : thickness;
        ctx.strokeRect(rx, ry, rw, rh);

        // Frame badge
        const label = fr.frame_id || `Frame ${idx + 1}`;
        ctx.font = "bold 10px system-ui, sans-serif";
        const tw = ctx.measureText(label).width;
        ctx.fillStyle = isSelected ? "#2563eb" : "#475569";
        ctx.fillRect(rx, ry, tw + 8, 16);
        ctx.fillStyle = "#ffffff";
        ctx.fillText(label, rx + 4, ry + 12);

        // 4-corner handles for selected frame
        if (isSelected) {
            const handleSize = 8;
            const half = handleSize / 2;
            const corners = [
                { x: rx, y: ry, handle: "nw" },
                { x: rx + rw, y: ry, handle: "ne" },
                { x: rx + rw, y: ry + rh, handle: "se" },
                { x: rx, y: ry + rh, handle: "sw" }
            ];
            ctx.fillStyle = "#2563eb";
            ctx.strokeStyle = "#ffffff";
            ctx.lineWidth = 1.5;
            corners.forEach(c => {
                ctx.fillRect(c.x - half, c.y - half, handleSize, handleSize);
                ctx.strokeRect(c.x - half, c.y - half, handleSize, handleSize);
            });
        }
    });

    // 3. Draw Guides & Figure Regions
    const guides = page.guides || [];
    guides.forEach((guide, gIdx) => {
        const placement = guide.placement || { x: 0, y: 0, w: 1, h: 1 };
        const enabled = guide.enabled !== false;
        const isSelectedGuide = (sessionState && sessionState.selectedGuideId === guide.guide_id);

        const gx = placement.x * cw;
        const gy = placement.y * ch;
        const gw = placement.w * cw;
        const gh = placement.h * ch;

        ctx.save();
        ctx.fillStyle = enabled ? "rgba(186, 230, 253, 0.2)" : "rgba(250, 204, 21, 0.15)";
        ctx.fillRect(gx, gy, gw, gh);

        // Preview loaded guide image asset if cached
        const cachedImg = imageCache && guide.asset_reference ? imageCache[guide.asset_reference] : null;
        if (cachedImg && (cachedImg.complete || cachedImg.naturalWidth > 0)) {
            ctx.save();
            ctx.globalAlpha = enabled ? 0.9 : 0.35;
            try {
                ctx.drawImage(cachedImg, gx, gy, gw, gh);
            } catch (e) {
                // Ignore rendering error
            }
            ctx.restore();
        }

        ctx.strokeStyle = enabled ? "#0284c7" : "#ca8a04";
        ctx.lineWidth = isSelectedGuide ? 2 : 1;
        if (!enabled) ctx.setLineDash([5, 4]);
        ctx.strokeRect(gx, gy, gw, gh);
        ctx.setLineDash([]);

        const gLabel = `${guide.guide_id || `Guide ${gIdx + 1}`} [${enabled ? "enabled" : "disabled"}]`;
        ctx.font = "bold 9px system-ui, sans-serif";
        const gtw = ctx.measureText(gLabel).width;
        ctx.fillStyle = enabled ? "#0284c7" : "#ca8a04";
        ctx.fillRect(gx, gy, gtw + 6, 14);
        ctx.fillStyle = "#ffffff";
        ctx.fillText(gLabel, gx + 3, gy + 10);
        ctx.restore();

        // Figure regions
        (guide.figure_regions || []).forEach((fig, fIdx) => {
            const fa = fig.area || { x: 0.1, y: 0.1, w: 0.3, h: 0.4 };
            // Section 4 & 21: Transform Guide-local coordinates to page/canvas coordinates
            const pageFigX = placement.x + fa.x * placement.w;
            const pageFigY = placement.y + fa.y * placement.h;
            const pageFigW = fa.w * placement.w;
            const pageFigH = fa.h * placement.h;

            const fx = pageFigX * cw;
            const fy = pageFigY * ch;
            const fw = pageFigW * cw;
            const fh = pageFigH * ch;
            const isSelectedFig = (sessionState && sessionState.selectedFigureId === fig.figure_id && activeTab === "guides");

            ctx.save();
            ctx.fillStyle = isSelectedFig ? "rgba(14, 116, 144, 0.35)" : "rgba(14, 116, 144, 0.15)";
            ctx.fillRect(fx, fy, fw, fh);
            ctx.strokeStyle = isSelectedFig ? "#0891b2" : "#0e7490";
            ctx.lineWidth = isSelectedFig ? 2.5 : 1.5;
            ctx.strokeRect(fx, fy, fw, fh);

            ctx.font = "bold 9px system-ui, sans-serif";
            const figLabel = fig.figure_id || `Figure ${fIdx + 1}`;
            ctx.fillStyle = "#0e7490";
            ctx.fillText(figLabel, fx + 3, fy + 11);

            // Four corner handles for selected Figure (Card Section 13 & 21)
            if (isSelectedFig) {
                const handleSize = 8;
                const half = handleSize / 2;
                const corners = [
                    { x: fx, y: fy, handle: "nw" },
                    { x: fx + fw, y: fy, handle: "ne" },
                    { x: fx + fw, y: fy + fh, handle: "se" },
                    { x: fx, y: fy + fh, handle: "sw" }
                ];
                ctx.fillStyle = "#0891b2";
                ctx.strokeStyle = "#ffffff";
                ctx.lineWidth = 1.5;
                corners.forEach(c => {
                    ctx.fillRect(c.x - half, c.y - half, handleSize, handleSize);
                    ctx.strokeRect(c.x - half, c.y - half, handleSize, handleSize);
                });
            }
            ctx.restore();
        });
    });

    // 4. Draw Scenes
    const scenes = page.scenes || [];
    scenes.forEach((sc, idx) => {
        const area = sc.area || { x: 0, y: 0, w: 1, h: 1 };
        const col = SCENE_PALETTE[idx % SCENE_PALETTE.length];
        const isSelected = (sessionState && sessionState.selectedSceneId === sc.scene_id && activeTab === "scenes");

        const rx = area.x * cw;
        const ry = area.y * ch;
        const rw = area.w * cw;
        const rh = area.h * ch;

        const fillAlpha = isSelected ? 0.25 : (activeTab === "frames" ? 0.05 : 0.12);
        const strokeWidth = isSelected ? 3 : 1.5;

        ctx.fillStyle = `rgba(${col.rgb.join(",")}, ${fillAlpha})`;
        ctx.fillRect(rx, ry, rw, rh);

        ctx.strokeStyle = col.hex;
        ctx.lineWidth = strokeWidth;
        ctx.strokeRect(rx, ry, rw, rh);

        // Badge
        const label = `Scene ${idx + 1}: ${sc.name || sc.scene_id}`;
        ctx.font = "bold 11px system-ui, sans-serif";
        const tw = ctx.measureText(label).width;
        ctx.fillStyle = col.hex;
        ctx.fillRect(rx, ry, tw + 8, 18);
        ctx.fillStyle = "#ffffff";
        ctx.fillText(label, rx + 4, ry + 13);

        // Handle for selected scene
        if (isSelected) {
            ctx.fillStyle = col.hex;
            ctx.fillRect(rx + rw - 10, ry + rh - 10, 10, 10);
            ctx.strokeStyle = "#ffffff";
            ctx.lineWidth = 1.5;
            ctx.strokeRect(rx + rw - 10, ry + rh - 10, 10, 10);
        }
    });

    // 5. Draw Character Instances
    const instances = page.character_instances || [];
    const castList = page.cast || [];
    instances.forEach((inst, idx) => {
        const area = inst.area || { x: 0, y: 0, w: 0.2, h: 0.2 };
        const castEntry = castList.find(c => c.cast_id === inst.cast_id);
        const colHex = castEntry?.color || CAST_PALETTE[idx % CAST_PALETTE.length].hex;
        const isSelected = (sessionState && sessionState.selectedInstanceId === inst.instance_id);

        const rx = area.x * cw;
        const ry = area.y * ch;
        const rw = area.w * cw;
        const rh = area.h * ch;

        ctx.save();
        ctx.fillStyle = isSelected ? "rgba(6, 182, 212, 0.35)" : "rgba(6, 182, 212, 0.18)";
        ctx.fillRect(rx, ry, rw, rh);

        ctx.strokeStyle = colHex;
        ctx.lineWidth = isSelected ? 3 : 2;
        ctx.strokeRect(rx, ry, rw, rh);

        const name = castEntry?.display_name || inst.cast_id;
        const instLabel = `${name} (${inst.instance_id})`;
        ctx.font = "bold 10px system-ui, sans-serif";
        const itw = ctx.measureText(instLabel).width;
        ctx.fillStyle = colHex;
        ctx.fillRect(rx, ry + rh - 16, itw + 8, 16);
        ctx.fillStyle = "#ffffff";
        ctx.fillText(instLabel, rx + 4, ry + rh - 4);

        // Handle for selected character instance
        if (isSelected) {
            ctx.fillStyle = colHex;
            ctx.fillRect(rx + rw - 8, ry + rh - 8, 8, 8);
            ctx.strokeStyle = "#ffffff";
            ctx.lineWidth = 1;
            ctx.strokeRect(rx + rw - 8, ry + rh - 8, 8, 8);
        }
        ctx.restore();
    });
}

/**
 * Hit test helper for canvas interaction
 */
export function hitTestCanvas(cw, ch, page, normX, normY, sessionState) {
    if (!page) return null;
    const pxX = normX * cw;
    const pxY = normY * ch;

    // ACTIVE LAYER HIT TEST (Card Section 14)
    // When activeTab === "guides", Guides, Figure handles, and Figure rectangles take exclusive priority
    if (sessionState?.activeTab === "guides") {
        const guides = page.guides || [];
        const selGuide = guides.find(g => g.guide_id === sessionState?.selectedGuideId);

        // 1. Check selected figure handles
        if (selGuide && sessionState?.selectedFigureId) {
            const fig = (selGuide.figure_regions || []).find(f => f.figure_id === sessionState.selectedFigureId);
            if (fig) {
                const gp = selGuide.placement || { x: 0, y: 0, w: 1, h: 1 };
                const fa = fig.area || { x: 0.1, y: 0.1, w: 0.3, h: 0.4 };
                const pfx = (gp.x + fa.x * gp.w) * cw;
                const pfy = (gp.y + fa.y * gp.h) * ch;
                const pfw = (fa.w * gp.w) * cw;
                const pfh = (fa.h * gp.h) * ch;
                const hitDist = 12;

                if (Math.abs(pxX - pfx) <= hitDist && Math.abs(pxY - pfy) <= hitDist) {
                    return { type: "handle_figure", handle: "nw", item: fig, guide: selGuide };
                }
                if (Math.abs(pxX - (pfx + pfw)) <= hitDist && Math.abs(pxY - pfy) <= hitDist) {
                    return { type: "handle_figure", handle: "ne", item: fig, guide: selGuide };
                }
                if (Math.abs(pxX - (pfx + pfw)) <= hitDist && Math.abs(pxY - (pfy + pfh)) <= hitDist) {
                    return { type: "handle_figure", handle: "se", item: fig, guide: selGuide };
                }
                if (Math.abs(pxX - pfx) <= hitDist && Math.abs(pxY - (pfy + pfh)) <= hitDist) {
                    return { type: "handle_figure", handle: "sw", item: fig, guide: selGuide };
                }
            }
        }

        // 2. Check figures across guides (top-most first)
        for (let gi = guides.length - 1; gi >= 0; gi--) {
            const g = guides[gi];
            const gp = g.placement || { x: 0, y: 0, w: 1, h: 1 };
            const figs = g.figure_regions || [];
            for (let fi = figs.length - 1; fi >= 0; fi--) {
                const fig = figs[fi];
                const fa = fig.area || { x: 0, y: 0, w: 0, h: 0 };
                const pfx = gp.x + fa.x * gp.w;
                const pfy = gp.y + fa.y * gp.h;
                const pfw = fa.w * gp.w;
                const pfh = fa.h * gp.h;
                if (normX >= pfx && normX <= pfx + pfw && normY >= pfy && normY <= pfy + pfh) {
                    return { type: "figure", item: fig, guide: g };
                }
            }
        }

        // 3. Check guide placement rectangle
        for (let gi = guides.length - 1; gi >= 0; gi--) {
            const g = guides[gi];
            const gp = g.placement || { x: 0, y: 0, w: 1, h: 1 };
            if (normX >= gp.x && normX <= gp.x + gp.w && normY >= gp.y && normY <= gp.y + gp.h) {
                return { type: "guide", item: g };
            }
        }

        return null;
    }

    // ACTIVE LAYER HIT TEST (Card Section 9)
    // When activeTab === "frames", Frames and Frame handles take exclusive priority
    if (sessionState?.activeTab === "frames") {
        if (sessionState?.selectedFrameId) {
            const fr = (page.visual_frames || []).find(f => f.frame_id === sessionState.selectedFrameId);
            if (fr) {
                const a = fr.area || fr.shape || { x: 0, y: 0, w: 1, h: 1 };
                const rx = a.x * cw;
                const ry = a.y * ch;
                const rw = a.w * cw;
                const rh = a.h * ch;
                const hitDist = 12;

                if (Math.abs(pxX - rx) <= hitDist && Math.abs(pxY - ry) <= hitDist) {
                    return { type: "handle_frame", handle: "nw", item: fr };
                }
                if (Math.abs(pxX - (rx + rw)) <= hitDist && Math.abs(pxY - ry) <= hitDist) {
                    return { type: "handle_frame", handle: "ne", item: fr };
                }
                if (Math.abs(pxX - (rx + rw)) <= hitDist && Math.abs(pxY - (ry + rh)) <= hitDist) {
                    return { type: "handle_frame", handle: "se", item: fr };
                }
                if (Math.abs(pxX - rx) <= hitDist && Math.abs(pxY - (ry + rh)) <= hitDist) {
                    return { type: "handle_frame", handle: "sw", item: fr };
                }
            }
        }

        const frames = page.visual_frames || [];
        for (let i = frames.length - 1; i >= 0; i--) {
            const fr = frames[i];
            const a = fr.area || fr.shape;
            if (a && normX >= a.x && normX <= a.x + a.w && normY >= a.y && normY <= a.y + a.h) {
                return { type: "frame", item: fr };
            }
        }

        return null;
    }

    // 1. Check selected instance handle
    if (sessionState?.selectedInstanceId) {
        const inst = (page.character_instances || []).find(i => i.instance_id === sessionState.selectedInstanceId);
        if (inst) {
            const hx = (inst.area.x + inst.area.w) * cw;
            const hy = (inst.area.y + inst.area.h) * cw;
            if (Math.abs(pxX - hx) <= 12 && Math.abs(pxY - hy) <= 12) {
                return { type: "handle_instance", item: inst };
            }
        }
    }

    // 2. Check character instances
    const instances = page.character_instances || [];
    for (let i = instances.length - 1; i >= 0; i--) {
        const inst = instances[i];
        const a = inst.area;
        if (normX >= a.x && normX <= a.x + a.w && normY >= a.y && normY <= a.y + a.h) {
            return { type: "instance", item: inst };
        }
    }

    // 3. Check selected scene handle
    if (sessionState?.selectedSceneId) {
        const sc = (page.scenes || []).find(s => s.scene_id === sessionState.selectedSceneId);
        if (sc) {
            const hx = (sc.area.x + sc.area.w) * cw;
            const hy = (sc.area.y + sc.area.h) * ch;
            if (Math.abs(pxX - hx) <= 14 && Math.abs(pxY - hy) <= 14) {
                return { type: "handle_scene", item: sc };
            }
        }
    }

    // 4. Check scenes
    const scenes = page.scenes || [];
    for (let i = scenes.length - 1; i >= 0; i--) {
        const sc = scenes[i];
        const a = sc.area;
        if (normX >= a.x && normX <= a.x + a.w && normY >= a.y && normY <= a.y + a.h) {
            return { type: "scene", item: sc };
        }
    }

    // 5. Check visual frames (selection only in non-frames layer)
    const frames = page.visual_frames || [];
    for (let i = frames.length - 1; i >= 0; i--) {
        const fr = frames[i];
        const a = fr.area || fr.shape;
        if (a && normX >= a.x && normX <= a.x + a.w && normY >= a.y && normY <= a.y + a.h) {
            return { type: "frame", item: fr };
        }
    }

    return null;
}
