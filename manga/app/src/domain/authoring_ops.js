/**
 * authoring_ops.js — Standalone Pure Authoring Operations
 * ========================================================
 * TEGAKI Manga Authoring Workspace (M1B)
 * 
 * Strict semantic parity with M3B production reference logic:
 * - Pure functions: zero DOM, zero graph-engine, zero ComfyUI host glue.
 * - Enforces CAST selection and placement invariants.
 * - Enforces CAST delete protection when referenced by Character Instances.
 * - Scene move translates child Character Instances by exact effective delta.
 * - Scene resize proportionally scales child Character Instances.
 * - Character move and resize are clamped strictly within parent Scene bounds.
 * - Scene deletion cascade-deletes child instances without leaving orphans.
 * - Removing the last Character Instance resets scene.input_mode to 'simple'.
 */

/**
 * Choose target CAST to place into a scene based on current authoring state.
 * Invariants (Card Section 9):
 * - No CAST registered -> placement rejected with NO_CAST.
 * - Single CAST registered -> automatic target allowed.
 * - Multiple CAST registered -> explicit selected CAST required.
 * - Selected CAST must exist.
 */
export function chooseCastForPlacement({ castList = [], selectedCastId = null, sceneInstances = [] } = {}) {
    if (!castList || castList.length === 0) {
        return {
            ok: false,
            reason: "NO_CAST",
            error: "Please register at least one CAST character before placing them in a scene."
        };
    }

    // Single CAST -> auto-place allowed
    if (castList.length === 1) {
        return {
            ok: true,
            targetCast: castList[0]
        };
    }

    // Multiple CAST -> explicit selection required (no silent cycling)
    if (!selectedCastId) {
        return {
            ok: false,
            reason: "SELECTION_REQUIRED",
            error: "Please select a CAST character first to place into this scene."
        };
    }

    const found = castList.find(c => c.cast_id === selectedCastId);
    if (!found) {
        return {
            ok: false,
            reason: "SELECTION_REQUIRED",
            error: "Selected CAST character does not exist in registry."
        };
    }

    return {
        ok: true,
        targetCast: found
    };
}

/**
 * Generate next unique instance_id avoiding collisions.
 */
export function getNextInstanceId(allInstances = []) {
    let nextNum = 1;
    const existingNums = (allInstances || []).map(i => {
        const m = i.instance_id && String(i.instance_id).match(/inst_(\d+)/);
        return m ? parseInt(m[1], 10) : 0;
    });
    if (existingNums.length > 0) {
        nextNum = Math.max(...existingNums, 0) + 1;
    }
    let candidate = `inst_${nextNum}`;
    while ((allInstances || []).some(i => i.instance_id === candidate)) {
        nextNum++;
        candidate = `inst_${nextNum}`;
    }
    return candidate;
}

/**
 * Generate next unique scene_id avoiding collisions.
 */
export function getNextSceneId(allScenes = []) {
    let nextNum = (allScenes || []).length + 1;
    let candidate = `scene_${nextNum}`;
    while ((allScenes || []).some(s => s.scene_id === candidate)) {
        nextNum++;
        candidate = `scene_${nextNum}`;
    }
    return candidate;
}

/**
 * Generate next unique cast_id avoiding collisions.
 */
export function getNextCastId(allCast = []) {
    let nextNum = (allCast || []).length + 1;
    let candidate = `cast_${nextNum}`;
    while ((allCast || []).some(c => c.cast_id === candidate)) {
        nextNum++;
        candidate = `cast_${nextNum}`;
    }
    return candidate;
}

/**
 * Calculate initial normalized bounding box for placing a character within a scene.
 */
export function calculateNewInstanceGeometry(sceneArea, currentSceneInstanceCount = 0) {
    const sb = sceneArea || { x: 0.1, y: 0.1, w: 0.8, h: 0.4 };
    const charW = parseFloat((sb.w * 0.40).toFixed(4));
    const charH = parseFloat((sb.h * 0.80).toFixed(4));
    const charX = (currentSceneInstanceCount === 0)
        ? parseFloat((sb.x + sb.w * 0.08).toFixed(4))
        : parseFloat((sb.x + sb.w * 0.52).toFixed(4));
    const charY = parseFloat((sb.y + sb.h * 0.10).toFixed(4));

    return {
        shape_type: "rect",
        x: charX,
        y: charY,
        w: charW,
        h: charH
    };
}

/**
 * Handle input_mode policy when an instance is removed from a scene.
 * If 0 instances remain in the scene, reset scene.input_mode to 'simple'
 * while strictly leaving scene.prompt untouched.
 */
export function onInstanceRemoved(scene, remainingInstancesInScene = []) {
    if (!scene) return;
    if (remainingInstancesInScene.length === 0) {
        scene.input_mode = "simple";
    }
}

/**
 * Guard check (Card Section 10): Can a CAST master be safely deleted?
 * Blocked if any character instance references this cast_id.
 */
export function canDeleteCast(castId, allInstances = []) {
    if (!castId) return { canDelete: false, reason: "NO_CAST_ID" };
    const referencing = (allInstances || []).filter(inst => inst.cast_id === castId);
    if (referencing.length > 0) {
        return {
            canDelete: false,
            reason: "REFERENCED_BY_INSTANCES",
            referencingInstances: referencing.map(i => i.instance_id)
        };
    }
    return { canDelete: true };
}

/**
 * Cascade scene deletion (Card Section 7):
 * Removes scene and all child instances belonging to this scene.
 * Re-indexes remaining scenes' order.
 */
export function cascadeDeleteScene(sceneId, scenes = [], instances = [], guides = []) {
    const remainingScenes = (scenes || []).filter(s => s.scene_id !== sceneId);
    remainingScenes.forEach((s, idx) => {
        s.order = idx + 1;
    });

    const deletedInstanceIds = new Set(
        (instances || []).filter(i => i.scene_id === sceneId).map(i => i.instance_id)
    );

    const remainingInstances = (instances || []).filter(i => i.scene_id !== sceneId);

    // Unassign deleted instances from any guide figures
    const updatedGuides = (guides || []).map(guide => {
        if (!guide.figure_regions) return guide;
        const updatedFigures = guide.figure_regions.map(fig => {
            if (fig.instance_id && deletedInstanceIds.has(fig.instance_id)) {
                return { ...fig, instance_id: null };
            }
            return fig;
        });
        return { ...guide, figure_regions: updatedFigures };
    });

    return {
        scenes: remainingScenes,
        instances: remainingInstances,
        guides: updatedGuides,
        deletedInstanceCount: deletedInstanceIds.size
    };
}

/**
 * Move scene within page unit square [0, 1] and translate child instances
 * by the exact effective delta (Card Section 7).
 */
export function moveSceneWithChildren(startSceneArea, startChildRecords = [], dx = 0, dy = 0) {
    let newX = startSceneArea.x + dx;
    let newY = startSceneArea.y + dy;
    newX = Math.max(0, Math.min(1.0 - startSceneArea.w, newX));
    newY = Math.max(0, Math.min(1.0 - startSceneArea.h, newY));

    const effectiveDx = newX - startSceneArea.x;
    const effectiveDy = newY - startSceneArea.y;

    const newSceneArea = {
        ...startSceneArea,
        x: parseFloat(newX.toFixed(4)),
        y: parseFloat(newY.toFixed(4))
    };

    const newChildAreas = (startChildRecords || []).map(record => ({
        id: record.id,
        area: {
            ...record.area,
            x: parseFloat((record.area.x + effectiveDx).toFixed(4)),
            y: parseFloat((record.area.y + effectiveDy).toFixed(4))
        }
    }));

    return {
        sceneArea: newSceneArea,
        childAreas: newChildAreas
    };
}

/**
 * Proportionally scale child instances when parent scene is resized (Card Section 7).
 */
export function resizeSceneWithChildren(startSceneArea, startChildRecords = [], newSceneArea) {
    const sw = Math.max(startSceneArea.w, 1e-6);
    const sh = Math.max(startSceneArea.h, 1e-6);

    return (startChildRecords || []).map(record => {
        const relX = (record.area.x - startSceneArea.x) / sw;
        const relY = (record.area.y - startSceneArea.y) / sh;
        const relW = record.area.w / sw;
        const relH = record.area.h / sh;

        return {
            id: record.id,
            area: {
                ...record.area,
                x: parseFloat((newSceneArea.x + relX * newSceneArea.w).toFixed(4)),
                y: parseFloat((newSceneArea.y + relY * newSceneArea.h).toFixed(4)),
                w: parseFloat((relW * newSceneArea.w).toFixed(4)),
                h: parseFloat((relH * newSceneArea.h).toFixed(4))
            }
        };
    });
}

/**
 * Clamp character direct drag within parent scene bounding box (Card Section 8).
 */
export function clampCharacterDrag(parentSceneArea, startCharArea, dx, dy) {
    const sb = parentSceneArea || { x: 0, y: 0, w: 1, h: 1 };
    let nx = startCharArea.x + dx;
    let ny = startCharArea.y + dy;
    nx = Math.max(sb.x, Math.min(sb.x + sb.w - startCharArea.w, nx));
    ny = Math.max(sb.y, Math.min(sb.y + sb.h - startCharArea.h, ny));

    return {
        x: parseFloat(nx.toFixed(4)),
        y: parseFloat(ny.toFixed(4))
    };
}

/**
 * Clamp character direct resize within parent scene bounding box (Card Section 8).
 */
export function clampCharacterResize(parentSceneArea, startCharArea, newW, newH) {
    const sb = parentSceneArea || { x: 0, y: 0, w: 1, h: 1 };
    const minW = 0.04;
    const minH = 0.04;
    const maxW = (sb.x + sb.w) - startCharArea.x;
    const maxH = (sb.y + sb.h) - startCharArea.y;

    const clampedW = Math.max(minW, Math.min(maxW, newW));
    const clampedH = Math.max(minH, Math.min(maxH, newH));

    return {
        w: parseFloat(clampedW.toFixed(4)),
        h: parseFloat(clampedH.toFixed(4))
    };
}

/**
 * Clamp scene drag within unit square [0, 1].
 */
export function clampSceneDrag(startSceneArea, dx, dy) {
    let nx = startSceneArea.x + dx;
    let ny = startSceneArea.y + dy;
    nx = Math.max(0, Math.min(1.0 - startSceneArea.w, nx));
    ny = Math.max(0, Math.min(1.0 - startSceneArea.h, ny));
    return {
        x: parseFloat(nx.toFixed(4)),
        y: parseFloat(ny.toFixed(4))
    };
}

/**
 * Clamp scene resize within unit square [0, 1].
 */
export function clampSceneResize(startSceneArea, newW, newH) {
    const minW = 0.10;
    const minH = 0.08;
    const maxW = 1.0 - startSceneArea.x;
    const maxH = 1.0 - startSceneArea.y;

    const clampedW = Math.max(minW, Math.min(maxW, newW));
    const clampedH = Math.max(minH, Math.min(maxH, newH));

    return {
        w: parseFloat(clampedW.toFixed(4)),
        h: parseFloat(clampedH.toFixed(4))
    };
}

// ===================================================================
// VISUAL FRAME OPERATIONS (M1C1)
// ===================================================================

/**
 * Generate next unique frame_id avoiding collision with existing frames.
 *
 * @param {Array<Object>} allFrames
 * @returns {string} e.g. "frame_1", "frame_2"
 */
export function getNextFrameId(allFrames = []) {
    let nextNum = 1;
    const existingNums = allFrames.map(f => {
        const m = f.frame_id && String(f.frame_id).match(/frame_(\d+)/);
        return m ? parseInt(m[1], 10) : 0;
    });
    if (existingNums.length > 0) {
        nextNum = Math.max(...existingNums, 0) + 1;
    }
    let candidate = `frame_${nextNum}`;
    while (allFrames.some(f => f.frame_id === candidate)) {
        nextNum++;
        candidate = `frame_${nextNum}`;
    }
    return candidate;
}

/**
 * Calculate initial normalized bounding box for adding a new visual frame.
 *
 * @param {Array<Object>} existingFrames
 * @returns {{ shape_type: string, x: number, y: number, w: number, h: number }}
 */
export function calculateNewFrameGeometry(existingFrames = []) {
    const count = existingFrames.length;
    if (count === 0) {
        return { shape_type: "rect", x: 0.05, y: 0.05, w: 0.90, h: 0.42 };
    }
    if (count === 1) {
        return { shape_type: "rect", x: 0.05, y: 0.52, w: 0.90, h: 0.42 };
    }
    // Default stacked layout for subsequent frames
    const stepY = 0.05 + ((count % 4) * 0.22);
    return {
        shape_type: "rect",
        x: 0.05,
        y: Math.min(0.70, parseFloat(stepY.toFixed(4))),
        w: 0.90,
        h: 0.22
    };
}

/**
 * One-shot copy current scene rectangles into independent visual frame rectangles.
 * Strictly non-linking: scene and frame will have no binding after this call.
 *
 * @param {Array<Object>} scenes
 * @returns {Array<Object>}
 */
export function copyFramesFromScenes(scenes = []) {
    return scenes.map((s, idx) => {
        const area = s.area || { x: 0.08, y: 0.06, w: 0.84, h: 0.42 };
        const geom = {
            shape_type: "rect",
            x: parseFloat(Number(area.x).toFixed(4)),
            y: parseFloat(Number(area.y).toFixed(4)),
            w: parseFloat(Number(area.w).toFixed(4)),
            h: parseFloat(Number(area.h).toFixed(4)),
        };
        return {
            frame_id: `frame_${idx + 1}`,
            order: idx + 1,
            area: geom,
            border_thickness: 4,
            border_color: "#000000",
            metadata: {}
        };
    });
}

/**
 * Clamp visual frame direct drag within unit square [0, 1].
 *
 * @param {Object} startFrameArea { x, y, w, h }
 * @param {number} dx
 * @param {number} dy
 * @returns {{ x: number, y: number }}
 */
export function clampFrameDrag(startFrameArea, dx, dy) {
    let nx = startFrameArea.x + dx;
    let ny = startFrameArea.y + dy;
    nx = Math.max(0, Math.min(1.0 - startFrameArea.w, nx));
    ny = Math.max(0, Math.min(1.0 - startFrameArea.h, ny));
    return {
        x: parseFloat(nx.toFixed(4)),
        y: parseFloat(ny.toFixed(4))
    };
}

/**
 * Resize visual frame with 4-corner handles within unit square [0, 1].
 *
 * @param {Object} startArea { x, y, w, h }
 * @param {string} handle "nw" | "ne" | "se" | "sw"
 * @param {number} dx
 * @param {number} dy
 * @param {number} minSize
 * @returns {{ shape_type: string, x: number, y: number, w: number, h: number }}
 */
export function resizeFrame(startArea, handle, dx, dy, minSize = 0.05) {
    const maxRight = startArea.x + startArea.w;
    const maxBottom = startArea.y + startArea.h;

    let x = startArea.x;
    let y = startArea.y;
    let w = startArea.w;
    let h = startArea.h;

    if (handle === "se") {
        w = Math.max(minSize, Math.min(1.0 - startArea.x, startArea.w + dx));
        h = Math.max(minSize, Math.min(1.0 - startArea.y, startArea.h + dy));
    } else if (handle === "nw") {
        const nx = Math.max(0, Math.min(maxRight - minSize, startArea.x + dx));
        const ny = Math.max(0, Math.min(maxBottom - minSize, startArea.y + dy));
        x = nx;
        y = ny;
        w = maxRight - nx;
        h = maxBottom - ny;
    } else if (handle === "ne") {
        const ny = Math.max(0, Math.min(maxBottom - minSize, startArea.y + dy));
        w = Math.max(minSize, Math.min(1.0 - startArea.x, startArea.w + dx));
        y = ny;
        h = maxBottom - ny;
    } else if (handle === "sw") {
        const nx = Math.max(0, Math.min(maxRight - minSize, startArea.x + dx));
        x = nx;
        w = maxRight - nx;
        h = Math.max(minSize, Math.min(1.0 - startArea.y, startArea.h + dy));
    }

    return {
        shape_type: "rect",
        x: parseFloat(x.toFixed(4)),
        y: parseFloat(y.toFixed(4)),
        w: parseFloat(w.toFixed(4)),
        h: parseFloat(h.toFixed(4)),
    };
}

/**
 * Check if visual frames have any overlap, returning diagnostic information.
 *
 * @param {Array<Object>} frames
 * @returns {{ hasOverlap: boolean, pairs: Array<[string, string]> }}
 */
export function checkFrameOverlap(frames = []) {
    const pairs = [];
    for (let i = 0; i < frames.length; i++) {
        const a = frames[i].area || frames[i].shape || {};
        for (let j = i + 1; j < frames.length; j++) {
            const b = frames[j].area || frames[j].shape || {};
            // Check bounding box intersection
            const noOverlap = (
                (a.x + a.w) <= b.x ||
                (b.x + b.w) <= a.x ||
                (a.y + a.h) <= b.y ||
                (b.y + b.h) <= a.y
            );
            if (!noOverlap) {
                pairs.push([frames[i].frame_id, frames[j].frame_id]);
            }
        }
    }
    return {
        hasOverlap: pairs.length > 0,
        pairs
    };
}
