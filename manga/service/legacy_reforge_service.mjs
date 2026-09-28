/**
 * Legacy EasyReforge generation service + HTTP routes (Card MANGA-LEGACY-EASYREFORGE-VERTICAL-MVP1).
 *
 * Unified Manga GUI -> backend-neutral recipe -> LegacyReforgeAdapter -> LegacyReforgeSupervisor
 * (Integration Runtime only) -> txt2img -> one PNG/JPEG + recipe metadata -> existing Stage result path.
 *
 * Jobs are in-memory (Output/History integration is banked).  One heavy job at a time: a
 * Legacy job never starts while the Comfy queue is busy, and the workspace refuses Comfy jobs
 * while a Legacy job runs.  Logical job states:
 *   submitting -> running -> completed | failed | interrupted
 * Supervisor states: stopped | starting | ready | failed | stopping.
 * There is never a fallback from EasyReforge to ComfyUI.
 */
import { randomUUID } from "node:crypto";
import { BACKEND_ID, LegacyReforgeError, buildTxt2ImgRequest, parseTxt2ImgResponse, samplingEquivalents } from "./legacy_reforge_adapter.mjs";
import { LegacyReforgeClient } from "./legacy_reforge_client.mjs";
import { LegacyReforgeSupervisor } from "./legacy_reforge_supervisor.mjs";

const JOB_ID = /^[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}$/;
const TERMINAL = new Set(["completed", "failed", "interrupted"]);
const MAX_JOBS = 12;

export class LegacyReforgeService {
    constructor({ supervisor = null, client = null, env = process.env, isComfyBusy = async () => false } = {}) {
        this.supervisor = supervisor || new LegacyReforgeSupervisor({ env });
        this.client = client || (this.supervisor.baseUrl ? new LegacyReforgeClient({ baseUrl: this.supervisor.baseUrl }) : null);
        if (!this.supervisor.client) this.supervisor.client = this.client;
        this.isComfyBusy = isComfyBusy;
        this.jobs = new Map();
        this.activeJobId = null;
    }

    isBusy() {
        const job = this.activeJobId ? this.jobs.get(this.activeJobId) : null;
        return Boolean(job && !TERMINAL.has(job.state)) || this.supervisor.state === "starting";
    }

    status() {
        const s = this.supervisor.status();
        const ready = s.state === "ready";
        return { ...s, available: Boolean(s.installed && ready), ready, busy: this.isBusy(), active_job_id: this.activeJobId };
    }

    async refreshStatus() {
        await this.supervisor.refreshExternal?.();
        return this.status();
    }

    async capabilities() {
        const status = await this.refreshStatus();
        if (!status.ready) return { ...status, samplers: [], schedulers: [], txt2img: false };
        const [samplers, schedulers] = await Promise.all([this.client.samplers(), this.client.schedulers()]);
        const names = list => (Array.isArray(list) ? list : []).map(item => typeof item === "string" ? item : item?.name).filter(n => typeof n === "string");
        const equivalents = samplingEquivalents(samplers, schedulers);
        return { ...status, samplers: names(samplers), schedulers: names(schedulers),
            sampler_equivalents: equivalents.samplers, scheduler_equivalents: equivalents.schedulers,
            txt2img: true, interrupt: true, progress: true };
    }

    /** Owner action: spawn the Integration Runtime; readiness continues in the background. */
    async start() {
        const current = await this.refreshStatus();
        if (current.state === "ready" || current.state === "starting") return current;
        await this.supervisor.begin();
        this.supervisor.waitReady().catch(() => {});
        return this.status();
    }
    stop() {
        if (this.isBusy() && this.supervisor.state === "ready") {
            throw new LegacyReforgeError("LEGACY_BUSY", "An EasyReforge job is running; interrupt it before stopping", 409);
        }
        return this.supervisor.stop();
    }

    _publicJob(job) {
        const { bytes, ...visible } = job;
        return { ...visible, has_result: Boolean(bytes) };
    }

    async generate(recipe) {
        if (this.supervisor.state !== "ready") {
            throw new LegacyReforgeError("LEGACY_NOT_READY", "EasyReforge is not running; start it first", 409);
        }
        if (this.isBusy()) throw new LegacyReforgeError("LEGACY_BUSY", "An EasyReforge job is already running", 409);
        if (await this.isComfyBusy()) throw new LegacyReforgeError("COMFY_BUSY", "The ComfyUI queue is busy; wait for it to finish", 409);
        const catalog = await this.client.catalog();
        const { payload, metadata } = buildTxt2ImgRequest(recipe, catalog);   // throws before any submission
        const job = { job_id: randomUUID(), backend: BACKEND_ID, state: "submitting", created_at: new Date().toISOString(),
            finished_at: null, recipe: metadata, result: null, error: null, bytes: null, mime: null };
        this.jobs.set(job.job_id, job);
        this.activeJobId = job.job_id;
        while (this.jobs.size > MAX_JOBS) {
            const oldest = [...this.jobs.values()].find(item => TERMINAL.has(item.state));
            if (!oldest) break;
            this.jobs.delete(oldest.job_id);
        }
        this._run(job, payload, metadata);
        return this._publicJob(job);
    }

    async _run(job, payload, metadata) {
        job.state = "running";
        try {
            const data = await this.client.txt2img(payload);
            if (job.state === "interrupted") return;
            const { bytes, mime, result } = parseTxt2ImgResponse(data, metadata);
            job.bytes = bytes;
            job.mime = mime;
            job.result = result;
            job.state = "completed";
        } catch (error) {
            if (job.state !== "interrupted") {
                job.state = "failed";
                job.error = { code: error?.code || "GENERATION_FAILED", message: error?.message || "EasyReforge generation failed" };
            }
        } finally {
            job.finished_at = new Date().toISOString();
        }
    }

    async interrupt(jobId) {
        const job = this.jobs.get(jobId);
        if (!job) throw new LegacyReforgeError("JOB_NOT_FOUND", "EasyReforge job not found", 404);
        if (TERMINAL.has(job.state)) return this._publicJob(job);
        await this.client.interrupt();
        job.state = "interrupted";
        job.error = { code: "INTERRUPTED", message: "Interrupted by the user" };
        return this._publicJob(job);
    }

    getJob(jobId) {
        const job = JOB_ID.test(jobId) ? this.jobs.get(jobId) : null;
        if (!job) throw new LegacyReforgeError("JOB_NOT_FOUND", "EasyReforge job not found", 404);
        return this._publicJob(job);
    }

    getResult(jobId) {
        const job = JOB_ID.test(jobId) ? this.jobs.get(jobId) : null;
        if (!job) throw new LegacyReforgeError("JOB_NOT_FOUND", "EasyReforge job not found", 404);
        if (job.state !== "completed" || !job.bytes || !["image/png", "image/jpeg"].includes(job.mime)) {
            throw new LegacyReforgeError("RESULT_NOT_READY", "EasyReforge result is not ready", 409);
        }
        return { bytes: job.bytes, mime: job.mime };
    }
}

/**
 * Route handler for /api/manga/legacy-reforge/*.  `allowed` = same-origin check result from the
 * workspace server.  Returns true when the request was handled.
 */
export async function handleLegacyReforgeRequest(service, req, res, url, { allowed }) {
    const base = "/api/manga/legacy-reforge";
    if (!url.pathname.startsWith(`${base}/`)) return false;
    const send = (status, data, type = "application/json; charset=utf-8") => {
        res.writeHead(status, { "Content-Type": type, "Cache-Control": "no-store" });
        res.end(type.startsWith("application/json") ? JSON.stringify(data) : data);
    };
    const reply = (status, code, message) => send(status, { ok: false, error_code: code, error: message });
    if (!allowed) { reply(403, "ORIGIN_FORBIDDEN", "Request origin is not the Manga workspace"); return true; }
    const route = url.pathname.slice(base.length + 1);
    const readBody = async () => {
        if ((req.headers["content-type"] || "").split(";")[0].trim().toLowerCase() !== "application/json") {
            throw new LegacyReforgeError("INVALID_CONTENT_TYPE", "Content-Type must be application/json", 415);
        }
        const chunks = [];
        let size = 0;
        for await (const chunk of req) {
            size += chunk.length;
            if (size > 256 * 1024) throw new LegacyReforgeError("REQUEST_TOO_LARGE", "Request exceeds 256 KiB", 413);
            chunks.push(chunk);
        }
        try { return JSON.parse(Buffer.concat(chunks).toString("utf8") || "{}"); }
        catch { throw new LegacyReforgeError("INVALID_JSON", "Invalid JSON request", 400); }
    };
    const expect = method => {
        if (req.method !== method) throw new LegacyReforgeError("METHOD_NOT_ALLOWED", `Use ${method}`, 405);
    };
    try {
        const jobMatch = /^jobs\/([0-9a-f-]{36})(\/result|\/interrupt)?$/.exec(route);
        if (route === "status") { expect("GET"); send(200, { ok: true, ...(await service.refreshStatus()) }); }
        else if (route === "capabilities") { expect("GET"); send(200, { ok: true, ...(await service.capabilities()) }); }
        else if (route === "start") { expect("POST"); await readBody(); send(200, { ok: true, ...(await service.start()) }); }
        else if (route === "stop") { expect("POST"); await readBody(); send(200, { ok: true, ...(await service.stop()) }); }
        else if (route === "generate") {
            expect("POST");
            const body = await readBody();
            send(202, { ok: true, job: await service.generate(body?.recipe) });
        } else if (jobMatch && !jobMatch[2]) { expect("GET"); send(200, { ok: true, job: service.getJob(jobMatch[1]) }); }
        else if (jobMatch && jobMatch[2] === "/result") {
            expect("GET");
            const { bytes, mime } = service.getResult(jobMatch[1]);
            send(200, bytes, mime);
        }
        else if (jobMatch && jobMatch[2] === "/interrupt") { expect("POST"); await readBody(); send(200, { ok: true, job: await service.interrupt(jobMatch[1]) }); }
        else reply(404, "ROUTE_NOT_FOUND", "Unknown EasyReforge route");
    } catch (error) {
        if (error instanceof LegacyReforgeError) reply(error.status || 422, error.code, error.message);
        else reply(500, "LEGACY_REFORGE_FAILED", "EasyReforge request failed");
    }
    return true;
}
