/** Same-origin PLAY1a/PLAY1b product API only. Never addresses backend 8189. */
export class MangaGenerationClientError extends Error {
    constructor(code, message, status = 0) {
        super(message);
        this.code = code;
        this.status = status;
    }
}

export class MangaGenerationClient {
    async _json(path, options = {}) {
        let response;
        try { response = await fetch(path, { cache: "no-store", ...options }); }
        catch { throw new MangaGenerationClientError("WORKSPACE_UNAVAILABLE", "Manga workspace is unavailable"); }
        let data;
        try { data = await response.json(); }
        catch { throw new MangaGenerationClientError("INVALID_RESPONSE", "Manga workspace returned invalid JSON", response.status); }
        if (!data || typeof data !== "object" || data.ok !== true || !response.ok) {
            throw new MangaGenerationClientError(data?.error_code || "REQUEST_FAILED",
                data?.error || `Manga request failed (HTTP ${response.status})`, response.status);
        }
        return data;
    }

    capabilities() { return this._json("/api/manga/generation/capabilities"); }
    compile(settings) {
        return this._json("/api/manga/generation/compile", {
            method: "POST", headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ ...settings, request_id: crypto.randomUUID() })
        });
    }
    compileScene(settings) {
        return this._json("/api/manga/generation/compile-scene", {
            method: "POST", headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ ...settings, request_id: crypto.randomUUID() })
        });
    }
    createJob(settings, compiled) {
        if (typeof compiled?.graph_digest !== "string" || !/^[0-9a-f]{64}$/.test(compiled.graph_digest)) {
            throw new MangaGenerationClientError("COMPILE_INVALID", "Compiler did not return a graph digest");
        }
        const payload = {
            settings, idempotency_key: crypto.randomUUID(), expected_graph_digest: compiled.graph_digest
        };
        if (settings.seed_requested === "-1") {
            if (!Number.isSafeInteger(compiled.effective_seed) || compiled.effective_seed < 0 ||
                compiled.effective_seed > 4294967295) {
                throw new MangaGenerationClientError("COMPILE_INVALID", "Compiler did not resolve the random seed");
            }
            payload.effective_seed = String(compiled.effective_seed);
        }
        return this._json("/api/manga/generation/jobs", {
            method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload)
        }).then(data => data.job);
    }
    getJob(jobId) {
        return this._json(`/api/manga/generation/jobs/${encodeURIComponent(jobId)}`).then(data => data.job);
    }
    // Card MANGA-LEGACY-EASYREFORGE-VERTICAL-MVP1: same-origin Legacy EasyReforge routes.
    legacyStatus() { return this._json("/api/manga/legacy-reforge/status"); }
    legacyCapabilities() { return this._json("/api/manga/legacy-reforge/capabilities"); }
    legacyStart() { return this._legacyPost("/api/manga/legacy-reforge/start", {}); }
    legacyStop() { return this._legacyPost("/api/manga/legacy-reforge/stop", {}); }
    legacyGenerate(recipe) { return this._legacyPost("/api/manga/legacy-reforge/generate", { recipe }).then(data => data.job); }
    legacyJob(jobId) { return this._json(`/api/manga/legacy-reforge/jobs/${encodeURIComponent(jobId)}`).then(data => data.job); }
    legacyInterrupt(jobId) {
        return this._legacyPost(`/api/manga/legacy-reforge/jobs/${encodeURIComponent(jobId)}/interrupt`, {}).then(data => data.job);
    }
    async legacyResult(jobId) {
        let response;
        try { response = await fetch(`/api/manga/legacy-reforge/jobs/${encodeURIComponent(jobId)}/result`, { cache: "no-store" }); }
        catch { throw new MangaGenerationClientError("RESULT_UNAVAILABLE", "EasyReforge result could not be loaded"); }
        if (!response.ok || !/^image\/(?:png|jpeg)(?:;|$)/i.test(response.headers.get("content-type") || "")) {
            throw new MangaGenerationClientError("RESULT_UNAVAILABLE", "EasyReforge result is unavailable", response.status);
        }
        return response.blob();
    }
    _legacyPost(path, body) {
        return this._json(path, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
    }
    async getResult(jobId) {
        let response;
        try { response = await fetch(`/api/manga/generation/jobs/${encodeURIComponent(jobId)}/result`, { cache: "no-store" }); }
        catch { throw new MangaGenerationClientError("RESULT_UNAVAILABLE", "Manga result could not be loaded"); }
        if (!response.ok || !/^image\/png(?:;|$)/i.test(response.headers.get("content-type") || "")) {
            throw new MangaGenerationClientError("RESULT_UNAVAILABLE", "Validated Manga result is unavailable", response.status);
        }
        return response.blob();
    }
}
