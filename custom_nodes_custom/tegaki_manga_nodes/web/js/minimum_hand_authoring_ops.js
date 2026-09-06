/**
 * minimum_hand_authoring_ops.js — Pure Authoring Operations for Minimum-Hand Manga UI
 * ====================================================================================
 * Source-coupled pure logic functions shared between:
 * 1. ComfyUI frontend web extension (`minimum_hand_scene_editor.js`)
 * 2. Headless contract verification suites (`test_m2b_minimum_hand_editor.mjs`)
 * 
 * Invariants enforced:
 * - Selected CAST strictly dictates newly placed character instance.
 * - Silent cycling across CAST list is prohibited.
 * - Single CAST can auto-place if unselected; multiple CAST requires explicit selection.
 * - Same CAST can appear across multiple scenes or repeatedly within the same scene.
 * - Removing the last character instance from a scene resets scene.input_mode to 'simple'.
 * - Scene move carries children with common effective delta.
 * - Scene resize proportionally scales children relative to scene bounds.
 * - Character drag is clipped within parent scene bounds.
 */

/**
 * Choose the target CAST to place into a scene based on current authoring state.
 * 
 * @param {Object} params
 * @param {Array<Object>} params.castList - Available CAST master list
 * @param {string|null} params.selectedCastId - Currently highlighted/selected cast_id
 * @param {Array<Object>} [params.sceneInstances] - Current character instances in target scene (for info/checks)
 * @returns {{ ok: boolean, targetCast?: Object, reason?: string, error?: string }}
 */
export function chooseCastForPlacement({ castList = [], selectedCastId = null, sceneInstances = [] } = {}) {
    if (!castList || castList.length === 0) {
        return {
            ok: false,
            reason: "NO_CAST",
            error: "Please register at least one CAST character above before placing them in a scene."
        };
    }

    // Rule 1: Single CAST registered -> automatically place the only CAST
    if (castList.length === 1) {
        return {
            ok: true,
            targetCast: castList[0]
        };
    }

    // Rule 2: Multiple CAST registered -> requires selected CAST (no silent cycling)
    if (!selectedCastId) {
        return {
            ok: false,
            reason: "SELECTION_REQUIRED",
            error: "Please select a CAST character above first to place into this scene."
        };
    }

    const found = castList.find(c => c.cast_id === selectedCastId);
    if (!found) {
        return {
            ok: false,
            reason: "SELECTION_REQUIRED",
            error: "Please select an existing CAST character above first."
        };
    }

    return {
        ok: true,
        targetCast: found
    };
}

/**
 * Generate next unique instance_id avoiding any collision with existing instances.
 * 
 * @param {Array<Object>} allInstances 
 * @returns {string} e.g. "inst_1", "inst_2"
 */
export function getNextInstanceId(allInstances = []) {
    let nextInstNum = 1;
    const existingNums = allInstances.map(i => {
        const m = i.instance_id && String(i.instance_id).match(/inst_(\d+)/);
        return m ? parseInt(m[1], 10) : 0;
    });
    if (existingNums.length > 0) {
        nextInstNum = Math.max(...existingNums, 0) + 1;
    }
    let candidate = `inst_${nextInstNum}`;
    while (allInstances.some(i => i.instance_id === candidate)) {
        nextInstNum++;
        candidate = `inst_${nextInstNum}`;
    }
    return candidate;
}

/**
 * Calculate initial normalized bounding box for placing a character within a scene.
 * 
 * @param {Object} sceneArea { x, y, w, h }
 * @param {number} currentSceneInstanceCount
 * @returns {{ shape_type: string, x: number, y: number, w: number, h: number }}
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
 * Handle mode policy when an instance is removed from a scene.
 * If 0 instances remain in the scene, reset scene.input_mode to "simple"
 * while strictly leaving scene.prompt untouched.
 * 
 * @param {Object} scene 
 * @param {Array<Object>} remainingInstancesInScene 
 */
export function onInstanceRemoved(scene, remainingInstancesInScene = []) {
    if (!scene) return;
    if (remainingInstancesInScene.length === 0) {
        scene.input_mode = "simple";
    }
}

/**
 * Guard check: Can a CAST master be safely deleted without leaving broken references?
 * 
 * @param {string} castId 
 * @param {Array<Object>} allInstances 
 * @returns {boolean}
 */
export function canDeleteCast(castId, allInstances = []) {
    if (!castId) return false;
    return !allInstances.some(inst => inst.cast_id === castId);
}

/**
 * Cascade scene deletion: removes scene from scenes array and removes all
 * child instances associated with this scene without leaving orphans.
 * 
 * @param {string} sceneId 
 * @param {Array<Object>} scenes 
 * @param {Array<Object>} instances 
 * @returns {{ scenes: Array<Object>, instances: Array<Object> }}
 */
export function cascadeDeleteScene(sceneId, scenes = [], instances = []) {
    const remainingScenes = scenes.filter(s => s.scene_id !== sceneId);
    remainingScenes.forEach((s, idx) => {
        s.order = idx + 1;
    });
    const remainingInstances = instances.filter(i => i.scene_id !== sceneId);
    return {
        scenes: remainingScenes,
        instances: remainingInstances
    };
}

/**
 * Move scene and translate child instances by the exact effective delta.
 * 
 * @param {Object} startSceneArea { x, y, w, h }
 * @param {Array<{ id: string, area: { x: number, y: number, w: number, h: number } }>} startChildRecords
 * @param {number} dx
 * @param {number} dy
 * @returns {{ sceneArea: Object, childAreas: Array<{ id: string, area: Object }> }}
 */
export function moveSceneWithChildren(startSceneArea, startChildRecords = [], dx = 0, dy = 0) {
    let newX = startSceneArea.x + dx;
    let newY = startSceneArea.y + dy;
    newX = Math.max(0, Math.min(1 - startSceneArea.w, newX));
    newY = Math.max(0, Math.min(1 - startSceneArea.h, newY));

    const effectiveDx = newX - startSceneArea.x;
    const effectiveDy = newY - startSceneArea.y;

    const newSceneArea = {
        ...startSceneArea,
        x: parseFloat(newX.toFixed(4)),
        y: parseFloat(newY.toFixed(4))
    };

    const newChildAreas = startChildRecords.map(record => ({
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
 * Proportionally scale child instances when parent scene is resized.
 * 
 * @param {Object} startSceneArea { x, y, w, h }
 * @param {Array<{ id: string, area: { x: number, y: number, w: number, h: number } }>} startChildRecords
 * @param {Object} newSceneArea { x, y, w, h }
 * @returns {Array<{ id: string, area: Object }>}
 */
export function resizeSceneWithChildren(startSceneArea, startChildRecords = [], newSceneArea) {
    const sw = Math.max(startSceneArea.w, 1e-6);
    const sh = Math.max(startSceneArea.h, 1e-6);

    return startChildRecords.map(record => {
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
 * Clamp character direct drag within parent scene bounding box.
 * 
 * @param {Object} parentSceneArea { x, y, w, h }
 * @param {Object} startCharArea { x, y, w, h }
 * @param {number} dx
 * @param {number} dy
 * @returns {{ x: number, y: number }}
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
