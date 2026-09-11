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

export const QUEUE_STATUS = {
    OK: "QUEUE_OK",
    UNAVAILABLE: "QUEUE_UNAVAILABLE",
    INVALID_RESPONSE: "QUEUE_INVALID_RESPONSE"
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

        // Browser fallback to workspace proxy using ?path=<endpoint>
        if (typeof window !== "undefined" && window.location) {
            const proxyUrl = `/api/proxy?path=${encodeURIComponent(endpoint)}`;
            return await fetch(proxyUrl, options);
        }

        throw new Error(`Connection failed to ${fullUrl}`);
    }

    /**
     * Probes backend endpoints to establish runtime profile identity.
     * Invariant (Card Section 3): MANGA_BACKEND_READY strictly requires both:
     * - /queue succeeds with valid shape
     * - /object_info/TegakiMinimumHandSceneEditor succeeds and contains node
     * If queue read fails, backend CANNOT be classified as ready even if node endpoint responded!
     */
    async probeStatus() {
        // 1. Probe /queue with fail-closed validation
        const queueRes = await this.getQueue();
        if (!queueRes.ok) {
            return {
                status: BACKEND_STATUS.UNAVAILABLE,
                error: `Queue unreachable or invalid (${queueRes.status}): ${queueRes.error || "connection failed"}`,
                queue: null
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
                queue: queueRes
            };
        }

        return {
            status: BACKEND_STATUS.MANGA_READY,
            nodeOk: true,
            queue: queueRes
        };
    }

    /**
     * Fetches current execution queue from backend.
     * Invariant (Card Section 2): Must NOT synthesize IDLE on network or API failure!
     * Returns: { ok: boolean, status: string, queue_running: Array|null, queue_pending: Array|null, error?: string }
     */
    async getQueue() {
        try {
            const resp = await this._fetch("/queue", { method: "GET" });
            if (!resp.ok) {
                return {
                    ok: false,
                    status: QUEUE_STATUS.UNAVAILABLE,
                    error: `HTTP ${resp.status} fetching queue`,
                    queue_running: null,
                    queue_pending: null
                };
            }
            let data;
            try {
                data = await resp.json();
            } catch (e) {
                return {
                    ok: false,
                    status: QUEUE_STATUS.INVALID_RESPONSE,
                    error: "Queue response was not valid JSON",
                    queue_running: null,
                    queue_pending: null
                };
            }
            if (!data || !Array.isArray(data.queue_running) || !Array.isArray(data.queue_pending)) {
                return {
                    ok: false,
                    status: QUEUE_STATUS.INVALID_RESPONSE,
                    error: "Queue response missing queue_running or queue_pending array",
                    queue_running: null,
                    queue_pending: null
                };
            }
            return {
                ok: true,
                status: QUEUE_STATUS.OK,
                queue_running: data.queue_running,
                queue_pending: data.queue_pending
            };
        } catch (err) {
            return {
                ok: false,
                status: QUEUE_STATUS.UNAVAILABLE,
                error: err.message || "Queue connection failed",
                queue_running: null,
                queue_pending: null
            };
        }
    }

    /**
     * Executes generation prepare contract:
     * POST /tegaki/manga/generation/prepare
     * 
     * Invariants (Card Section 2 & 12):
     * - Successfully read queue before prepare; must be known IDLE (running == [] && pending == []).
     * - Otherwise STOP / fail closed.
     * - Perform prepare ONLY when queue state is known idle.
     * - Successfully read queue after prepare and report truthfully.
     * - If post-prepare queue cannot be read: do NOT claim Queue IDLE.
     * - Real generations: 0 (never submit to /prompt).
     */
    async prepareDraft(authoringDocument, pageIndex = 0, seed = 42) {
        // 1. Strict pre-execution check: Queue must be known IDLE
        const queueBefore = await this.getQueue();
        if (!queueBefore.ok) {
            return {
                ok: false,
                status: 503,
                error: `Cannot prepare: queue check failed (${queueBefore.status}: ${queueBefore.error || "unavailable"})`,
                error_code: "QUEUE_UNAVAILABLE",
                queueBefore,
                queueAfter: null,
                isQueueIdleAfter: false,
                generationTriggered: false
            };
        }

        const runningCount = queueBefore.queue_running.length;
        const pendingCount = queueBefore.queue_pending.length;
        if (runningCount > 0 || pendingCount > 0) {
            return {
                ok: false,
                status: 409,
                error: `Cannot prepare: queue is busy (${runningCount} running, ${pendingCount} pending)`,
                error_code: "QUEUE_BUSY",
                queueBefore,
                queueAfter: null,
                isQueueIdleAfter: false,
                generationTriggered: false
            };
        }

        // 2. Perform prepare ONLY when queue state is known idle
        let resp;
        try {
            resp = await this._fetch("/tegaki/manga/generation/prepare", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    document_json: authoringDocument,
                    page_index: pageIndex,
                    seed: parseInt(seed, 10) || 42
                })
            });
        } catch (err) {
            return {
                ok: false,
                status: 500,
                error: `Prepare request failed: ${err.message}`,
                error_code: "PREPARE_FETCH_FAILED",
                queueBefore,
                queueAfter: null,
                isQueueIdleAfter: false,
                generationTriggered: false
            };
        }

        let data = null;
        try {
            data = await resp.json();
        } catch (err) {
            data = { ok: false, error: "Prepare response was not valid JSON" };
        }

        // 3. Post-execution check: Read queue after prepare truthfully
        const queueAfter = await this.getQueue();
        const isQueueIdleAfter = queueAfter.ok &&
            queueAfter.queue_running.length === 0 &&
            queueAfter.queue_pending.length === 0;

        return {
            ok: resp.ok && data.ok,
            status: resp.status,
            route: data.route,
            prompt: data.prompt,
            error: data.error,
            error_code: data.error_code,
            queueBefore,
            queueAfter,
            isQueueIdleAfter,
            generationTriggered: false
        };
    }
}
