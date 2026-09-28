/**
 * Minimal Legacy EasyReforge API client (Card MANGA-LEGACY-EASYREFORGE-VERTICAL-MVP1).
 * Only the endpoints the MVP needs; loopback only; bounded responses.  No endpoint mirroring.
 */
import { LegacyReforgeError } from "./legacy_reforge_adapter.mjs";

const MAX_JSON_BYTES = 64 * 1024 * 1024;   // txt2img carries one base64 PNG

export class LegacyReforgeClient {
    constructor({ baseUrl, fetchFn = fetch, timeoutMs = 10000, generateTimeoutMs = 30 * 60 * 1000 } = {}) {
        const url = new URL(baseUrl);
        if (url.protocol !== "http:" || !["127.0.0.1", "localhost"].includes(url.hostname)) {
            throw new LegacyReforgeError("LEGACY_URL_FORBIDDEN", "EasyReforge API must be a loopback http URL", 500);
        }
        this.origin = url.origin;
        this.fetchFn = fetchFn;
        this.timeoutMs = timeoutMs;
        this.generateTimeoutMs = generateTimeoutMs;
    }

    async _request(path, { method = "GET", body, timeoutMs = this.timeoutMs } = {}) {
        let response;
        try {
            response = await this.fetchFn(`${this.origin}${path}`, {
                method, headers: body === undefined ? undefined : { "Content-Type": "application/json" },
                body: body === undefined ? undefined : JSON.stringify(body),
                signal: AbortSignal.timeout(timeoutMs),
            });
        } catch (error) {
            throw new LegacyReforgeError(error?.name === "TimeoutError" ? "LEGACY_API_TIMEOUT" : "LEGACY_API_UNAVAILABLE",
                error?.name === "TimeoutError" ? `EasyReforge ${path} timed out` : "EasyReforge API is unavailable", 503);
        }
        const text = await response.text();
        if (text.length > MAX_JSON_BYTES) throw new LegacyReforgeError("LEGACY_RESPONSE_INVALID", "EasyReforge response is too large", 502);
        let data = null;
        try { data = text ? JSON.parse(text) : null; } catch {
            throw new LegacyReforgeError("LEGACY_RESPONSE_INVALID", `EasyReforge ${path} returned non-JSON (HTTP ${response.status})`, 502);
        }
        if (!response.ok) {
            const detail = typeof data?.detail === "string" ? data.detail : typeof data?.error === "string" ? data.error : "";
            throw new LegacyReforgeError(response.status === 404 ? "LEGACY_ENDPOINT_MISSING" : "LEGACY_REQUEST_FAILED",
                `EasyReforge ${path} failed (HTTP ${response.status})${detail ? `: ${detail.slice(0, 300)}` : ""}`,
                response.status === 404 ? 502 : 502);
        }
        return data;
    }

    /** Readiness probe: the API router answers once the webui finished initialising. */
    ping() { return this._request("/sdapi/v1/samplers", { timeoutMs: 3000 }).then(list => Array.isArray(list)); }
    samplers() { return this._request("/sdapi/v1/samplers"); }
    async schedulers() {
        try { return await this._request("/sdapi/v1/schedulers"); }
        catch (error) { if (error.code === "LEGACY_ENDPOINT_MISSING") return []; throw error; }
    }
    sdModels() { return this._request("/sdapi/v1/sd-models"); }
    /** Launch flags of the running webui (read-only); null when the endpoint does not exist. */
    async cmdFlags() {
        try { return await this._request("/sdapi/v1/cmd-flags"); }
        catch (error) { if (error.code === "LEGACY_ENDPOINT_MISSING") return null; throw error; }
    }
    sdVae() { return this._request("/sdapi/v1/sd-vae"); }
    loras() { return this._request("/sdapi/v1/loras"); }
    progress() { return this._request("/sdapi/v1/progress?skip_current_image=true"); }
    interrupt() { return this._request("/sdapi/v1/interrupt", { method: "POST", body: {} }); }
    txt2img(payload) { return this._request("/sdapi/v1/txt2img", { method: "POST", body: payload, timeoutMs: this.generateTimeoutMs }); }

    /** Everything the adapter needs to map one recipe. */
    async catalog() {
        const [sdModels, sdVae, loras, samplers, schedulers, cmdFlags] = await Promise.all([
            this.sdModels(), this.sdVae(), this.loras(), this.samplers(), this.schedulers(), this.cmdFlags()]);
        return { sdModels, sdVae, loras, samplers, schedulers, cmdFlags };
    }
}
