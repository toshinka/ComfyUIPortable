/**
 * session_state.js — Ephemeral UI Session State Container
 * =======================================================
 * TEGAKI Manga Authoring Workspace (M1A)
 * 
 * Manages transient user interaction states:
 * - Active editing layer / tab (scenes, frames, guides, cast)
 * - Selected entity identifiers (scene, cast, instance, frame, guide, figure)
 * - Viewport transform (zoom, pan)
 * 
 * INVARIANT: No state from this container may ever leak into TEGAKI_AUTHORING_DOCUMENT!
 */

export class SessionState {
    constructor() {
        this.activeTab = "scenes"; // 'scenes' | 'frames' | 'guides' | 'cast'
        this.selectedSceneId = "scene_top";
        this.selectedCastId = null;
        this.selectedInstanceId = null;
        this.selectedFrameId = null;
        this.selectedGuideId = null;
        this.selectedFigureId = null;
        this.viewport = {
            zoom: 1.0,
            panX: 0,
            panY: 0
        };
        this.listeners = new Set();
    }

    setActiveTab(tab) {
        if (this.activeTab !== tab) {
            this.activeTab = tab;
            this.notify();
        }
    }

    selectScene(sceneId) {
        this.selectedSceneId = sceneId;
        this.notify();
    }

    selectCast(castId, toggle = false) {
        this.selectedCastId = (toggle && this.selectedCastId === castId) ? null : castId;
        this.notify();
    }

    selectInstance(instanceId, toggle = false) {
        this.selectedInstanceId = (toggle && this.selectedInstanceId === instanceId) ? null : instanceId;
        this.notify();
    }

    selectFrame(frameId) {
        this.selectedFrameId = (this.selectedFrameId === frameId) ? null : frameId;
        this.notify();
    }

    selectGuide(guideId) {
        this.selectedGuideId = (this.selectedGuideId === guideId) ? null : guideId;
        this.notify();
    }

    selectFigure(figureId) {
        this.selectedFigureId = (this.selectedFigureId === figureId) ? null : figureId;
        this.notify();
    }

    setViewport(zoom, panX, panY) {
        this.viewport.zoom = zoom;
        this.viewport.panX = panX;
        this.viewport.panY = panY;
        this.notify();
    }

    subscribe(listener) {
        this.listeners.add(listener);
        return () => this.listeners.delete(listener);
    }

    notify() {
        for (const listener of this.listeners) {
            try {
                listener(this);
            } catch (err) {
                console.error("[SessionState listener error]", err);
            }
        }
    }

    /**
     * Returns a snapshot of session-only state.
     */
    getSnapshot() {
        return {
            activeTab: this.activeTab,
            selectedSceneId: this.selectedSceneId,
            selectedCastId: this.selectedCastId,
            selectedInstanceId: this.selectedInstanceId,
            selectedFrameId: this.selectedFrameId,
            selectedGuideId: this.selectedGuideId,
            selectedFigureId: this.selectedFigureId,
            viewport: { ...this.viewport }
        };
    }
}
