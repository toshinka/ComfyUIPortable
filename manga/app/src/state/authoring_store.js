/**
 * authoring_store.js — Authoring Document Store & Mutation Boundary
 * =================================================================
 * TEGAKI Manga Authoring Workspace (M1B)
 * 
 * Invariants:
 * - Owns the current TEGAKI_AUTHORING_DOCUMENT 1.0.0.
 * - Enforces schema validation after every mutation (Card Section 13).
 * - Rejects invalid edits without corrupting document state.
 * - Preserves CAST delete guards and placement contracts (Card Section 9 & 10).
 * - Preserves Scene child translation, proportional scaling, and cascade delete (Card Section 7).
 * - Preserves Character containment within parent Scene bounds (Card Section 8).
 * - Protects document from session state pollution during export.
 */

import {
    createDefaultAuthoringDocument,
    createRichAuthoringFixture,
    validateAuthoringDocument,
    cloneDocument
} from "../domain/authoring_document.js";
import {
    chooseCastForPlacement,
    getNextInstanceId,
    getNextSceneId,
    getNextCastId,
    calculateNewInstanceGeometry,
    onInstanceRemoved,
    canDeleteCast,
    cascadeDeleteScene,
    moveSceneWithChildren,
    resizeSceneWithChildren,
    clampCharacterDrag,
    clampCharacterResize,
    getNextFrameId,
    calculateNewFrameGeometry,
    copyFramesFromScenes,
    clampFrameDrag,
    resizeFrame,
    checkFrameOverlap
} from "../domain/authoring_ops.js";

const DEFAULT_CAST_PALETTE = [
    "#06b6d4", "#eab308", "#ec4899", "#a855f7", "#22c55e", "#f97316"
];

export class AuthoringStore {
    constructor(initialDoc = null) {
        this.document = initialDoc ? cloneDocument(initialDoc) : createDefaultAuthoringDocument();
        this.listeners = new Set();
    }

    getDocument() {
        return cloneDocument(this.document);
    }

    getPage(pageIndex = 0) {
        return this.document.pages[pageIndex] || null;
    }

    setDocument(newDoc) {
        const validation = validateAuthoringDocument(newDoc);
        if (!validation.valid) {
            throw new Error("Invalid authoring document: " + validation.errors.join(", "));
        }
        this.document = cloneDocument(newDoc);
        this.notify();
    }

    resetDefault() {
        this.setDocument(createDefaultAuthoringDocument());
    }

    loadRichFixture() {
        this.setDocument(createRichAuthoringFixture());
    }

    exportJson(pretty = true) {
        const validation = validateAuthoringDocument(this.document);
        if (!validation.valid) {
            throw new Error("Cannot export invalid document: " + validation.errors.join(", "));
        }
        return pretty ? JSON.stringify(this.document, null, 2) : JSON.stringify(this.document);
    }

    importJson(jsonString) {
        let parsed;
        try {
            parsed = JSON.parse(jsonString);
        } catch (e) {
            return { ok: false, error: "JSON parse error: " + e.message };
        }
        const validation = validateAuthoringDocument(parsed);
        if (!validation.valid) {
            return { ok: false, error: validation.errors.join("; ") };
        }
        this.setDocument(parsed);
        return { ok: true, document: this.getDocument() };
    }

    // ==========================================
    // GLOBAL MUTATIONS (Card Section 6.A)
    // ==========================================

    setSeed(seed, pageIndex = 0) {
        const draft = cloneDocument(this.document);
        const page = draft.pages[pageIndex];
        if (!page) throw new Error("Page not found");
        if (!page.generation) page.generation = {};
        page.generation.seed = parseInt(seed, 10) || 0;
        this.setDocument(draft);
    }

    setStyleMetadata({ styleTemplate, stylePrompt, styleNegativePrompt } = {}, pageIndex = 0) {
        const draft = cloneDocument(this.document);
        const page = draft.pages[pageIndex];
        if (!page) throw new Error("Page not found");
        if (styleTemplate !== undefined) {
            if (!page.metadata) page.metadata = {};
            page.metadata.style_template = styleTemplate;
        }
        if (stylePrompt !== undefined) page.style_prompt = stylePrompt;
        if (styleNegativePrompt !== undefined) page.style_negative_prompt = styleNegativePrompt;
        this.setDocument(draft);
    }

    // ==========================================
    // SCENE MUTATIONS (Card Section 6.B, 7)
    // ==========================================

    addScene({ name = "", prompt = "", negative_prompt = "", area = null } = {}, pageIndex = 0) {
        const draft = cloneDocument(this.document);
        const page = draft.pages[pageIndex];
        if (!page) throw new Error("Page not found");
        if (!Array.isArray(page.scenes)) page.scenes = [];

        if (page.scenes.length >= 6) {
            throw new Error("Maximum 6 scenes allowed per page");
        }

        const sceneId = getNextSceneId(page.scenes);
        const order = page.scenes.length + 1;
        const defaultY = Math.min(0.80, 0.05 + (order - 1) * 0.22);
        const sceneArea = area || {
            shape_type: "rect",
            x: 0.08,
            y: parseFloat(defaultY.toFixed(4)),
            w: 0.84,
            h: 0.20
        };

        const newScene = {
            scene_id: sceneId,
            order,
            name: name || `Scene ${order}`,
            prompt: prompt || "",
            negative_prompt: negative_prompt || "",
            input_mode: "simple",
            area: sceneArea,
            metadata: {}
        };

        page.scenes.push(newScene);
        this.setDocument(draft);
        return newScene;
    }

    updateScene(sceneId, updates = {}, pageIndex = 0) {
        const draft = cloneDocument(this.document);
        const page = draft.pages[pageIndex];
        if (!page) throw new Error("Page not found");
        const scene = (page.scenes || []).find(s => s.scene_id === sceneId);
        if (!scene) throw new Error(`Scene '${sceneId}' not found`);

        if (updates.name !== undefined) scene.name = updates.name;
        if (updates.prompt !== undefined) scene.prompt = updates.prompt;
        if (updates.negative_prompt !== undefined) scene.negative_prompt = updates.negative_prompt;
        if (updates.input_mode !== undefined) scene.input_mode = updates.input_mode;

        this.setDocument(draft);
        return scene;
    }

    moveScene(sceneId, dx, dy, pageIndex = 0) {
        const draft = cloneDocument(this.document);
        const page = draft.pages[pageIndex];
        if (!page) throw new Error("Page not found");
        const scene = (page.scenes || []).find(s => s.scene_id === sceneId);
        if (!scene) throw new Error(`Scene '${sceneId}' not found`);

        // Find child instances belonging to this scene
        const childInstances = (page.character_instances || []).filter(i => i.scene_id === sceneId);
        const childRecords = childInstances.map(i => ({ id: i.instance_id, area: i.area }));

        const result = moveSceneWithChildren(scene.area, childRecords, dx, dy);
        scene.area = result.sceneArea;

        // Apply translated areas to children
        result.childAreas.forEach(rec => {
            const inst = childInstances.find(i => i.instance_id === rec.id);
            if (inst) inst.area = rec.area;
        });

        this.setDocument(draft);
    }

    resizeScene(sceneId, newArea, pageIndex = 0) {
        const draft = cloneDocument(this.document);
        const page = draft.pages[pageIndex];
        if (!page) throw new Error("Page not found");
        const scene = (page.scenes || []).find(s => s.scene_id === sceneId);
        if (!scene) throw new Error(`Scene '${sceneId}' not found`);

        const childInstances = (page.character_instances || []).filter(i => i.scene_id === sceneId);
        const childRecords = childInstances.map(i => ({ id: i.instance_id, area: i.area }));

        const scaledChildAreas = resizeSceneWithChildren(scene.area, childRecords, newArea);
        scene.area = {
            shape_type: "rect",
            x: parseFloat(newArea.x.toFixed(4)),
            y: parseFloat(newArea.y.toFixed(4)),
            w: parseFloat(newArea.w.toFixed(4)),
            h: parseFloat(newArea.h.toFixed(4))
        };

        scaledChildAreas.forEach(rec => {
            const inst = childInstances.find(i => i.instance_id === rec.id);
            if (inst) inst.area = rec.area;
        });

        this.setDocument(draft);
    }

    deleteScene(sceneId, pageIndex = 0) {
        const draft = cloneDocument(this.document);
        const page = draft.pages[pageIndex];
        if (!page) throw new Error("Page not found");
        if ((page.scenes || []).length <= 1) {
            throw new Error("Cannot delete the only scene; at least 1 scene required");
        }

        const res = cascadeDeleteScene(sceneId, page.scenes, page.character_instances, page.guides);
        page.scenes = res.scenes;
        page.character_instances = res.instances;
        page.guides = res.guides;

        this.setDocument(draft);
    }

    // ==========================================
    // CAST MUTATIONS (Card Section 6.C, 10)
    // ==========================================

    addCast({ display_name = "", identity_prompt = "", negative_prompt = "", color = null, loras = [] } = {}, pageIndex = 0) {
        const draft = cloneDocument(this.document);
        const page = draft.pages[pageIndex];
        if (!page) throw new Error("Page not found");
        if (!Array.isArray(page.cast)) page.cast = [];

        const castId = getNextCastId(page.cast);
        const paletteIdx = page.cast.length % DEFAULT_CAST_PALETTE.length;
        const castColor = color || DEFAULT_CAST_PALETTE[paletteIdx];

        const newCast = {
            cast_id: castId,
            display_name: display_name || `Character ${page.cast.length + 1}`,
            identity_prompt: identity_prompt || "",
            negative_prompt: negative_prompt || "",
            color: castColor,
            loras: Array.isArray(loras) ? loras : [],
            metadata: {}
        };

        page.cast.push(newCast);
        this.setDocument(draft);
        return newCast;
    }

    updateCast(castId, updates = {}, pageIndex = 0) {
        const draft = cloneDocument(this.document);
        const page = draft.pages[pageIndex];
        if (!page) throw new Error("Page not found");
        const castEntry = (page.cast || []).find(c => c.cast_id === castId);
        if (!castEntry) throw new Error(`CAST '${castId}' not found`);

        if (updates.display_name !== undefined) castEntry.display_name = updates.display_name;
        if (updates.identity_prompt !== undefined) castEntry.identity_prompt = updates.identity_prompt;
        if (updates.negative_prompt !== undefined) castEntry.negative_prompt = updates.negative_prompt;
        if (updates.color !== undefined) castEntry.color = updates.color;

        this.setDocument(draft);
        return castEntry;
    }

    deleteCast(castId, pageIndex = 0) {
        const draft = cloneDocument(this.document);
        const page = draft.pages[pageIndex];
        if (!page) throw new Error("Page not found");

        // Strict delete guard (Card Section 10)
        const check = canDeleteCast(castId, page.character_instances);
        if (!check.canDelete) {
            throw new Error(
                `Cannot delete CAST '${castId}': referenced by active character instances (${check.referencingInstances.join(", ")})`
            );
        }

        page.cast = (page.cast || []).filter(c => c.cast_id !== castId);
        this.setDocument(draft);
    }

    // ==========================================
    // CHARACTER INSTANCE MUTATIONS (Card Section 6.D, 8, 9)
    // ==========================================

    placeCharacter(sceneId, selectedCastId = null, pageIndex = 0) {
        const draft = cloneDocument(this.document);
        const page = draft.pages[pageIndex];
        if (!page) throw new Error("Page not found");
        const scene = (page.scenes || []).find(s => s.scene_id === sceneId);
        if (!scene) throw new Error(`Scene '${sceneId}' not found`);

        const sceneInstances = (page.character_instances || []).filter(i => i.scene_id === sceneId);

        // Enforce CAST selection contract (Card Section 9)
        const pick = chooseCastForPlacement({
            castList: page.cast || [],
            selectedCastId,
            sceneInstances
        });
        if (!pick.ok) {
            throw new Error(pick.error || "Cannot place character: selection required");
        }

        const targetCast = pick.targetCast;
        if (!Array.isArray(page.character_instances)) page.character_instances = [];

        const instanceId = getNextInstanceId(page.character_instances);
        const geom = calculateNewInstanceGeometry(scene.area, sceneInstances.length);

        const newInstance = {
            instance_id: instanceId,
            cast_id: targetCast.cast_id,
            scene_id: sceneId,
            area: geom,
            acting_prompt: "",
            negative_prompt_override: "",
            order: sceneInstances.length + 1,
            metadata: {}
        };

        scene.input_mode = "cast";
        page.character_instances.push(newInstance);
        this.setDocument(draft);
        return newInstance;
    }

    updateCharacter(instanceId, updates = {}, pageIndex = 0) {
        const draft = cloneDocument(this.document);
        const page = draft.pages[pageIndex];
        if (!page) throw new Error("Page not found");
        const inst = (page.character_instances || []).find(i => i.instance_id === instanceId);
        if (!inst) throw new Error(`Character instance '${instanceId}' not found`);

        if (updates.acting_prompt !== undefined) inst.acting_prompt = updates.acting_prompt;
        if (updates.negative_prompt_override !== undefined) inst.negative_prompt_override = updates.negative_prompt_override;

        this.setDocument(draft);
        return inst;
    }

    moveCharacter(instanceId, dx, dy, pageIndex = 0) {
        const draft = cloneDocument(this.document);
        const page = draft.pages[pageIndex];
        if (!page) throw new Error("Page not found");
        const inst = (page.character_instances || []).find(i => i.instance_id === instanceId);
        if (!inst) throw new Error(`Character instance '${instanceId}' not found`);
        const scene = (page.scenes || []).find(s => s.scene_id === inst.scene_id);
        if (!scene) throw new Error(`Parent scene '${inst.scene_id}' not found`);

        const clamped = clampCharacterDrag(scene.area, inst.area, dx, dy);
        inst.area = {
            ...inst.area,
            x: clamped.x,
            y: clamped.y
        };

        this.setDocument(draft);
    }

    resizeCharacter(instanceId, newW, newH, pageIndex = 0) {
        const draft = cloneDocument(this.document);
        const page = draft.pages[pageIndex];
        if (!page) throw new Error("Page not found");
        const inst = (page.character_instances || []).find(i => i.instance_id === instanceId);
        if (!inst) throw new Error(`Character instance '${instanceId}' not found`);
        const scene = (page.scenes || []).find(s => s.scene_id === inst.scene_id);
        if (!scene) throw new Error(`Parent scene '${inst.scene_id}' not found`);

        const clamped = clampCharacterResize(scene.area, inst.area, newW, newH);
        inst.area = {
            ...inst.area,
            w: clamped.w,
            h: clamped.h
        };

        this.setDocument(draft);
    }

    removeCharacter(instanceId, pageIndex = 0) {
        const draft = cloneDocument(this.document);
        const page = draft.pages[pageIndex];
        if (!page) throw new Error("Page not found");
        const inst = (page.character_instances || []).find(i => i.instance_id === instanceId);
        if (!inst) throw new Error(`Character instance '${instanceId}' not found`);
        const sceneId = inst.scene_id;

        page.character_instances = (page.character_instances || []).filter(i => i.instance_id !== instanceId);

        // Reset scene input_mode to 'simple' if last instance removed (Card Section 8)
        const scene = (page.scenes || []).find(s => s.scene_id === sceneId);
        const remaining = (page.character_instances || []).filter(i => i.scene_id === sceneId);
        onInstanceRemoved(scene, remaining);

        // Unassign from guide figures if any
        page.guides = (page.guides || []).map(guide => {
            if (!guide.figure_regions) return guide;
            const updated = guide.figure_regions.map(f => {
                if (f.instance_id === instanceId) return { ...f, instance_id: null };
                return f;
            });
            return { ...guide, figure_regions: updated };
        });

        this.setDocument(draft);
    }

    // ==========================================
    // VISUAL FRAME MUTATIONS (Card Section 13)
    // ==========================================

    addFrame(customProps = {}, pageIndex = 0) {
        const draft = cloneDocument(this.document);
        const page = draft.pages[pageIndex];
        if (!page) throw new Error("Page not found");
        if (!Array.isArray(page.visual_frames)) page.visual_frames = [];

        const frameId = customProps.frame_id || getNextFrameId(page.visual_frames);
        const area = customProps.area || calculateNewFrameGeometry(page.visual_frames);
        const newFrame = {
            frame_id: frameId,
            order: page.visual_frames.length + 1,
            area,
            border_thickness: customProps.border_thickness ?? 4,
            border_color: customProps.border_color || "#000000",
            metadata: customProps.metadata || {}
        };

        page.visual_frames.push(newFrame);
        this.setDocument(draft);
        return newFrame;
    }

    deleteFrame(frameId, pageIndex = 0) {
        const draft = cloneDocument(this.document);
        const page = draft.pages[pageIndex];
        if (!page) throw new Error("Page not found");

        page.visual_frames = (page.visual_frames || [])
            .filter(f => f.frame_id !== frameId)
            .map((f, idx) => ({ ...f, order: idx + 1 }));

        this.setDocument(draft);
    }

    copyScenesToFrames(pageIndex = 0) {
        const draft = cloneDocument(this.document);
        const page = draft.pages[pageIndex];
        if (!page) throw new Error("Page not found");

        page.visual_frames = copyFramesFromScenes(page.scenes || []);
        this.setDocument(draft);
        return page.visual_frames;
    }

    moveFrame(frameId, dx, dy, pageIndex = 0) {
        const draft = cloneDocument(this.document);
        const page = draft.pages[pageIndex];
        if (!page) throw new Error("Page not found");
        const frame = (page.visual_frames || []).find(f => f.frame_id === frameId);
        if (!frame) throw new Error(`Frame '${frameId}' not found`);

        const clamped = clampFrameDrag(frame.area, dx, dy);
        frame.area = { ...frame.area, x: clamped.x, y: clamped.y };

        this.setDocument(draft);
        return frame;
    }

    resizeFrame(frameId, handle, dx, dy, minSize = 0.05, pageIndex = 0) {
        const draft = cloneDocument(this.document);
        const page = draft.pages[pageIndex];
        if (!page) throw new Error("Page not found");
        const frame = (page.visual_frames || []).find(f => f.frame_id === frameId);
        if (!frame) throw new Error(`Frame '${frameId}' not found`);

        frame.area = resizeFrame(frame.area, handle, dx, dy, minSize);

        this.setDocument(draft);
        return frame;
    }

    updateFrame(frameId, updates = {}, pageIndex = 0) {
        const draft = cloneDocument(this.document);
        const page = draft.pages[pageIndex];
        if (!page) throw new Error("Page not found");
        const frame = (page.visual_frames || []).find(f => f.frame_id === frameId);
        if (!frame) throw new Error(`Frame '${frameId}' not found`);

        if (updates.border_thickness !== undefined) {
            frame.border_thickness = Math.max(1, Math.min(20, parseInt(updates.border_thickness, 10) || 4));
        }
        if (updates.border_color !== undefined) {
            frame.border_color = updates.border_color;
        }
        if (updates.area !== undefined) {
            frame.area = updates.area;
        }
        if (updates.metadata !== undefined) {
            frame.metadata = updates.metadata;
        }

        this.setDocument(draft);
        return frame;
    }

    getFrameOverlap(pageIndex = 0) {
        const page = this.getPage(pageIndex);
        return checkFrameOverlap(page?.visual_frames || []);
    }

    subscribe(listener) {
        this.listeners.add(listener);
        return () => this.listeners.delete(listener);
    }

    notify() {
        for (const listener of this.listeners) {
            try {
                listener(this.getDocument());
            } catch (err) {
                console.error("[AuthoringStore listener error]", err);
            }
        }
    }
}
