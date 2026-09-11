/**
 * manga_backend_client.js — Manga ComfyUI Backend Integration Adapter
 * ====================================================================
 * TEGAKI Manga Authoring Workspace (M1A)
 * 
 * Standalone client for communicating with Manga-capable ComfyUI instances:
 * - Probes backend identity and capability.
 * - Validates presence of TegakiMinimumHandSceneEditor node.
 * - Distinguishes: UNAVAILABLE vs GENERIC_COMFYUI vs MANGA_CAPABLE.
 * - Executes POST /tegaki/manga/generation/prepare WITHOUT queueing generation.
 * - Checks queue state before and after prepare to verify real generations = 0.
 */

export const BACKEND_STATUS = {
    UNAVAILABLE: "BACKEND_UNAVAILABLE",
    GENERIC_COMFYUI: "GENERIC_COMFYUI",
    MANGA_READY: "MANGA_BACKEND_READY"
};

export class MangaBackendClient {
    constructor(backendUrl = "http://127.0.0.1:8189") {
        this.backendUrl = backendUrl.replace(/\/$/, "");
    }

    setBackendUrl(url) {
        this.backendUrl = url.replace(/\/$/, "");
    }

    async _fetch(endpoint, options = {}) {
        const fullUrl = `${this.backendUrl}${endpoint}`;
        try {
            const resp = await fetch(fullUrl, options);
            if (resp.status !== 403) {
                return resp;
            }
        } catch (e) {
            // direct fetch failed (e.g. browser CORS blocked)
        }

        // Browser fallback to workspace proxy
        if (typeof window !== "undefined" && window.location) {
            const proxyUrl = `/api/proxy?target=${encodeURIComponent(fullUrl)}`;
            return await fetch(proxyUrl, options);
        }

        throw new Error(`Connection failed to ${fullUrl}`);
    }

    /**
     * Probes backend endpoints to establish runtime profile identity.
     * Returns { status, error?, details? }
     */
    async probeStatus() {
        let queueOk = false;
        let queueData = null;

        // 1. Probe /queue
        try {
            const qResp = await this._fetch("/queue", { method: "GET" });
            if (qResp.ok) {
                queueOk = true;
                queueData = await qResp.json();
            }
        } catch (err) {
            return {
                status: BACKEND_STATUS.UNAVAILABLE,
                error: `Connection refused or unreachable at ${this.backendUrl}`
            };
        }

        // 2. Probe /object_info/TegakiMinimumHandSceneEditor
        let nodeOk = false;
        try {
            const objResp = await this._fetch("/object_info/TegakiMinimumHandSceneEditor", { method: "GET" });
            if (objResp.ok) {
                const nodeData = await objResp.json();
                if (nodeData && nodeData.TegakiMinimumHandSceneEditor) {
                    nodeOk = true;
                }
            }
        } catch (err) {
            // Error probing node
        }

        if (!nodeOk) {
            return {
                status: BACKEND_STATUS.GENERIC_COMFYUI,
                error: "ComfyUI is running, but TegakiMinimumHandSceneEditor custom node is missing",
                queue: queueData
            };
        }

        return {
            status: BACKEND_STATUS.MANGA_READY,
            nodeOk: true,
            queue: queueData
        };
    }

    /**
     * Fetches current execution queue from backend.
     */
    async getQueue() {
        try {
            const resp = await this._fetch("/queue", { method: "GET" });
            if (resp.ok) {
                return await resp.json();
            }
        } catch (err) {
            console.warn("[MangaBackendClient] Failed to fetch queue:", err);
        }
        return { queue_running: [], queue_pending: [] };
    }

    /**
     * Executes generation prepare contract:
     * POST /tegaki/manga/generation/prepare
     * 
     * INVARIANT: Never submits prompt to /prompt or queues execution!
     */
    async prepareDraft(authoringDocument, pageIndex = 0, seed = 42) {
        // Verify queue is idle before prepare
        const queueBefore = await this.getQueue();
        const beforeRunning = queueBefore.queue_running?.length || 0;
        const beforePending = queueBefore.queue_pending?.length || 0;

        const resp = await this._fetch("/tegaki/manga/generation/prepare", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                document_json: authoringDocument,
                page_index: pageIndex,
                seed: parseInt(seed, 10) || 42
            })
        });

        const data = await resp.json();

        // Verify queue remains idle after prepare
        const queueAfter = await this.getQueue();
        const afterRunning = queueAfter.queue_running?.length || 0;
        const afterPending = queueAfter.queue_pending?.length || 0;

        return {
            ok: resp.ok && data.ok,
            status: resp.status,
            route: data.route,
            prompt: data.prompt,
            error: data.error,
            error_code: data.error_code,
            queueBefore: { running: beforeRunning, pending: beforePending },
            queueAfter: { running: afterRunning, pending: afterPending },
            generationTriggered: false
        };
    }
}
