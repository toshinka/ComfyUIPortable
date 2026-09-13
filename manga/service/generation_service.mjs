/** PLAY1b Manga-owned submission, observation, and output boundary. No UI or runtime lifecycle. */
import { createHash, randomBytes, randomUUID } from "node:crypto";
import { isDeepStrictEqual } from "node:util";
import { GenerationJournal, JournalError, JOB_ID } from "./generation_journal.mjs";

const SETTINGS = new Set([
    "mode", "checkpoint_id", "positive_raw", "negative_raw", "sampler_id", "scheduler_id",
    "steps", "cfg", "width", "height", "seed_requested", "capability_revision"
]);
const GRAPH_CLASSES = new Set([
    "CheckpointLoaderSimple", "LoraLoader", "CLIPTextEncode", "EmptyLatentImage",
    "KSampler", "VAEDecode", "SaveImage"
]);
const SHA256 = /^[0-9a-f]{64}$/;
const PNG_SIGNATURE = Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]);
const ACTIVE = new Set(["VALIDATING", "SUBMITTING", "QUEUED", "RUNNING", "UNKNOWN"]);

export class GenerationServiceError extends Error {
    constructor(code, message, status = 409) {
        super(message);
        this.code = code;
        this.status = status;
    }
}

const fail = (code, message, status) => { throw new GenerationServiceError(code, message, status); };
const now = () => new Date().toISOString();
const hash = value => createHash("sha256").update(value).digest("hex");
const stable = value => {
    if (Array.isArray(value)) return `[${value.map(stable).join(",")}]`;
    if (value !== null && typeof value === "object") {
        return `{${Object.keys(value).sort().map(key => `${JSON.stringify(key)}:${stable(value[key])}`).join(",")}}`;
    }
    return JSON.stringify(value);
};
const isObject = value => value !== null && typeof value === "object" && !Array.isArray(value);

export function validateOutputLocator(locator, jobId) {
    if (!JOB_ID.test(jobId) || !isObject(locator) || locator.type !== "output" ||
        typeof locator.filename !== "string" || typeof locator.subfolder !== "string") {
        fail("OUTPUT_INVALID", "Missing or foreign Manga output locator", 502);
    }
    const subfolder = locator.subfolder.replaceAll("\\", "/");
    if (subfolder !== "Manga/Playable" ||
        !new RegExp(`^${jobId}_[0-9]{5}_\\.png$`).test(locator.filename)) {
        fail("OUTPUT_INVALID", "Output is outside the owned Manga job prefix", 502);
    }
    return { filename: locator.filename, subfolder, type: "output" };
}

export class GenerationService {
    constructor({ backendUrl = "http://127.0.0.1:8189", journal = new GenerationJournal(),
                  fetchFn = fetch, timeoutMs = 5000 } = {}) {
        const target = new URL(backendUrl);
        if (target.protocol !== "http:" || !["127.0.0.1", "localhost"].includes(target.hostname) ||
            target.pathname !== "/" || target.search || target.hash) {
            fail("BACKEND_TARGET_INVALID", "Manga backend must be a fixed loopback HTTP origin", 500);
        }
        this.origin = target.origin;
        this.journal = journal;
        this.fetchFn = fetchFn;
        this.timeoutMs = timeoutMs;
        this.tail = Promise.resolve();
    }

    _exclusive(work) {
        const result = this.tail.then(work);
        this.tail = result.catch(() => {});
        return result;
    }

    async _fetch(path, options = {}) {
        try {
            return await this.fetchFn(`${this.origin}${path}`, {
                ...options, signal: AbortSignal.timeout(this.timeoutMs)
            });
        } catch (error) {
            throw new GenerationServiceError(
                error.name === "TimeoutError" ? "BACKEND_TIMEOUT" : "BACKEND_UNAVAILABLE",
                error.name === "TimeoutError" ? "Manga backend request timed out" : "Manga backend request failed",
                502
            );
        }
    }

    async _json(path, options = {}) {
        const response = await this._fetch(path, options);
        let data;
        try {
            const chunks = [];
            let size = 0;
            for await (const chunk of response.body) {
                size += chunk.length;
                if (size > 4 * 1024 * 1024) fail("BACKEND_INVALID_RESPONSE", "Backend JSON exceeds 4 MiB", 502);
                chunks.push(chunk);
            }
            const bytes = Buffer.concat(chunks);
            data = JSON.parse(bytes.toString("utf8"));
            if (!isObject(data)) throw new Error("Expected object");
        } catch (error) {
            if (error instanceof GenerationServiceError) throw error;
            fail("BACKEND_INVALID_RESPONSE", "Backend returned invalid JSON", 502);
        }
        return { status: response.status, ok: response.ok, data };
    }

    async _identity() {
        const response = await this._json("/object_info/TegakiMinimumHandSceneEditor");
        if (!response.ok || !isObject(response.data.TegakiMinimumHandSceneEditor)) {
            fail("BACKEND_IDENTITY_INVALID", "Backend lacks exact Manga node identity", 503);
        }
        return { origin: this.origin, node: "TegakiMinimumHandSceneEditor" };
    }

    async _queue() {
        const response = await this._json("/queue");
        const { queue_running: running, queue_pending: pending } = response.data;
        if (!response.ok || !Array.isArray(running) || !Array.isArray(pending) ||
            [...running, ...pending].some(item => !Array.isArray(item) || item.length < 4 ||
                typeof item[1] !== "string" || !isObject(item[3]))) {
            fail("QUEUE_UNKNOWN", "Backend queue is unavailable or malformed", 503);
        }
        return { running, pending };
    }

    async _capabilities(revision) {
        const response = await this._json("/tegaki/manga/generation/capabilities");
        if (!response.ok || response.data.ok !== true || typeof response.data.revision !== "string") {
            fail("CAPABILITY_UNKNOWN", "Manga capability catalog is unavailable", 503);
        }
        if (response.data.revision !== revision) {
            fail("CAPABILITY_CHANGED", "Manga capability catalog changed; review again", 409);
        }
    }

    async _compile(settings, requestId, expectedDigest, effectiveSeed) {
        let seed = settings.seed_requested;
        if (seed === "-1") {
            if (typeof effectiveSeed !== "string" || !/^(0|[1-9][0-9]*)$/.test(effectiveSeed) ||
                BigInt(effectiveSeed) > 4294967295n) {
                fail("EFFECTIVE_SEED_REQUIRED", "Reviewed random seed must be supplied as decimal text", 400);
            }
            seed = effectiveSeed;
        } else if (effectiveSeed !== undefined && effectiveSeed !== seed) {
            fail("EFFECTIVE_SEED_MISMATCH", "Effective seed differs from requested seed", 400);
        }
        const compileRequest = { ...settings, request_id: requestId, seed_requested: seed };
        const response = await this._json("/tegaki/manga/generation/compile-basic", {
            method: "POST", headers: { "Content-Type": "application/json" },
            body: JSON.stringify(compileRequest)
        });
        if (!response.ok || response.data.ok !== true) {
            fail(response.data.error_code || "COMPILE_REJECTED", response.data.error || "Backend compile rejected", response.status);
        }
        const result = response.data;
        if (result.graph_digest !== expectedDigest || result.capability_revision !== settings.capability_revision) {
            fail("DIGEST_MISMATCH", "Reviewed graph digest or capability revision differs", 409);
        }
        if (!isDeepStrictEqual(result.normalized_request, compileRequest) || !isObject(result.graph) ||
            typeof result.positive_clean !== "string" || typeof result.negative_clean !== "string" ||
            !Array.isArray(result.resolved_loras) || result.effective_seed !== Number(seed)) {
            fail("COMPILE_INVALID", "Backend compile result does not match request", 502);
        }
        const nodes = Object.entries(result.graph);
        if (!nodes.length || nodes.some(([, node]) => !isObject(node) || !GRAPH_CLASSES.has(node.class_type))) {
            fail("COMPILE_INVALID", "Backend compiled an unsupported graph", 502);
        }
        const saves = nodes.filter(([, node]) => node.class_type === "SaveImage");
        if (saves.length !== 1 || saves[0][1].inputs?.filename_prefix !== "Manga/Playable/compiled") {
            fail("COMPILE_INVALID", "Backend graph lacks the single PLAY1a SaveImage output", 502);
        }
        return { result, saveNodeId: saves[0][0] };
    }

    _validateSubmission(body) {
        if (!isObject(body) || !isObject(body.settings) ||
            Object.keys(body).some(key => !["settings", "idempotency_key", "expected_graph_digest", "effective_seed"].includes(key)) ||
            Object.keys(body.settings).length !== SETTINGS.size ||
            Object.keys(body.settings).some(key => !SETTINGS.has(key))) {
            fail("INVALID_REQUEST", "Provide only PLAY1a settings and reviewed digest", 400);
        }
        if (typeof body.idempotency_key !== "string" || !/^[A-Za-z0-9_-]{1,64}$/.test(body.idempotency_key) ||
            typeof body.expected_graph_digest !== "string" || !SHA256.test(body.expected_graph_digest) ||
            (body.effective_seed !== undefined && typeof body.effective_seed !== "string")) {
            fail("INVALID_REQUEST", "Invalid idempotency key, digest, or seed", 400);
        }
        return body;
    }

    async createJob(input) {
        return this._exclusive(async () => {
            const body = this._validateSubmission(input);
            let records;
            try {
                records = await this.journal.list();
            } catch (error) {
                if (error instanceof JournalError) fail(error.code, error.message, 503);
                throw error;
            }
            if (records.some(record => record.idempotency_key === body.idempotency_key)) {
                fail("DUPLICATE_REQUEST", "Manga request was already recorded", 409);
            }
            if (records.some(record => ACTIVE.has(record.state) && record.graph_digest === body.expected_graph_digest)) {
                fail("DUPLICATE_GRAPH", "Identical reviewed graph already has an unresolved job", 409);
            }
            if (records.some(record => ACTIVE.has(record.state))) {
                fail("OWNED_JOB_BUSY", "A Manga-owned job is still unresolved", 409);
            }
            const identity = await this._identity();
            const queue = await this._queue();
            if (queue.running.length || queue.pending.length) {
                fail("FOREIGN_QUEUE_BUSY", "Backend queue contains an existing job", 409);
            }
            await this._capabilities(body.settings.capability_revision);
            const jobId = randomUUID();
            const requestId = randomUUID();
            const { result, saveNodeId } = await this._compile(
                body.settings, requestId, body.expected_graph_digest, body.effective_seed
            );
            const token = randomBytes(32).toString("hex");
            const record = {
                job_id: jobId, request_id: requestId, idempotency_key: body.idempotency_key,
                requested_settings: structuredClone(body.settings),
                effective_settings: { ...result.normalized_request, seed_requested: String(result.effective_seed) },
                raw_positive: body.settings.positive_raw, raw_negative: body.settings.negative_raw,
                clean_positive: result.positive_clean, clean_negative: result.negative_clean,
                resolved_loras: result.resolved_loras, capability_revision: body.settings.capability_revision,
                graph_digest: body.expected_graph_digest, submitted_graph_digest: null,
                backend_identity: identity, prompt_id: null, save_node_id: saveNodeId,
                created_at: now(), submitted_at: null, started_at: null, finished_at: null,
                state: "VALIDATING", error: null, output_locator: null, ownership_token: token
            };
            await this.journal.put(record);
            const graph = structuredClone(result.graph);
            graph[saveNodeId].inputs.filename_prefix = `Manga/Playable/${jobId}`;
            record.submitted_graph_digest = hash(stable(graph));
            record.state = "SUBMITTING";
            await this.journal.put(record);
            const payload = {
                prompt: graph,
                extra_data: { tegaki_manga: {
                    job_id: jobId, request_id: requestId, graph_digest: body.expected_graph_digest,
                    submitted_graph_digest: record.submitted_graph_digest, ownership_token: token
                }}
            };
            let reply;
            try {
                reply = await this._json("/prompt", {
                    method: "POST", headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(payload)
                });
            } catch (error) {
                return this._reconcileUnknown(record, error.code || "SUBMIT_UNCONFIRMED");
            }
            if (reply.ok && typeof reply.data.prompt_id === "string" && JOB_ID.test(reply.data.prompt_id) &&
                typeof reply.data.number === "number" && Number.isFinite(reply.data.number) &&
                isObject(reply.data.node_errors)) {
                record.prompt_id = reply.data.prompt_id;
                record.state = "QUEUED";
                record.submitted_at = now();
                await this.journal.put(record);
                return this.publicJob(record);
            }
            if ([400, 422].includes(reply.status) && !reply.data.prompt_id) {
                record.state = "FAILED";
                record.finished_at = now();
                record.error = { code: "BACKEND_REJECTED", message: reply.data.error?.message || "Backend rejected the graph" };
                await this.journal.put(record);
                return this.publicJob(record);
            }
            return this._reconcileUnknown(record, "SUBMIT_UNCONFIRMED");
        });
    }

    _owned(item, record, promptId = record.prompt_id) {
        const meta = item?.[3]?.tegaki_manga;
        return JOB_ID.test(promptId) && Array.isArray(item) && isObject(item[2]) &&
            item[1] === promptId && isObject(meta) &&
            meta.job_id === record.job_id && meta.request_id === record.request_id &&
            meta.ownership_token === record.ownership_token && meta.graph_digest === record.graph_digest &&
            meta.submitted_graph_digest === record.submitted_graph_digest &&
            hash(stable(item[2])) === record.submitted_graph_digest;
    }

    async _recoverPromptId(record) {
        // Installed ComfyUI preserves extra_data in both queue tuples and history prompt tuples.
        // Read both complete views; an unavailable or oversized view leaves the job UNKNOWN.
        const queue = await this._queue();
        const response = await this._json("/history");
        if (!response.ok) fail("HISTORY_UNKNOWN", "Backend history is unavailable", 503);
        const candidates = new Set();
        for (const item of [...queue.running, ...queue.pending]) {
            if (this._owned(item, record, item[1])) candidates.add(item[1]);
        }
        for (const [promptId, entry] of Object.entries(response.data)) {
            if (isObject(entry) && this._owned(entry.prompt, record, promptId)) candidates.add(promptId);
        }
        if (candidates.size !== 1) {
            fail("JOB_UNRESOLVED", "A unique backend prompt ID could not be established", 503);
        }
        record.prompt_id = [...candidates][0];
        record.state = "UNKNOWN";
        record.submitted_at ??= now();
        await this.journal.put(record);
    }

    async _history(record) {
        const response = await this._json(`/history/${record.prompt_id}`);
        if (!response.ok) fail("HISTORY_UNKNOWN", "Backend history is unavailable", 503);
        const entry = response.data[record.prompt_id];
        if (entry === undefined) return null;
        if (!isObject(entry) || !this._owned(entry.prompt, record)) {
            fail("OWNERSHIP_MISMATCH", "History prompt does not match Manga ownership", 503);
        }
        return entry;
    }

    async _observe(record) {
        if (record.prompt_id === null) await this._recoverPromptId(record);
        const history = await this._history(record);
        if (history) {
            const status = history.status;
            if (status?.completed === true && status.status_str === "success") {
                const images = history.outputs?.[record.save_node_id]?.images;
                if (!Array.isArray(images) || images.length !== 1) {
                    fail("OUTPUT_INVALID", "Completed history lacks the expected SaveImage output", 502);
                }
                const locator = validateOutputLocator(images[0], record.job_id);
                await this._image(locator);
                record.state = "SUCCEEDED";
                record.output_locator = locator;
                record.error = null;
                record.submitted_at ??= now();
                record.started_at ??= record.submitted_at;
                record.finished_at = now();
                await this.journal.put(record);
                return record;
            }
            if (status?.completed === false && status.status_str === "error") {
                record.state = "FAILED";
                record.error = { code: "BACKEND_EXECUTION_FAILED", message: "Backend history reports an execution error" };
                record.finished_at = now();
                await this.journal.put(record);
                return record;
            }
            fail("HISTORY_UNKNOWN", "History has no completed execution status", 503);
        }
        const queue = await this._queue();
        const foundRunning = queue.running.find(item => item[1] === record.prompt_id);
        const foundPending = queue.pending.find(item => item[1] === record.prompt_id);
        const found = foundRunning || foundPending;
        if (found) {
            if (!this._owned(found, record)) fail("OWNERSHIP_MISMATCH", "Queue prompt does not match Manga ownership", 503);
            record.state = foundRunning ? "RUNNING" : "QUEUED";
            record.submitted_at ??= now();
            if (foundRunning) record.started_at ??= now();
            record.error = null;
            await this.journal.put(record);
            return record;
        }
        fail("JOB_UNRESOLVED", "Owned prompt is absent from queue and history", 503);
    }

    async _reconcileUnknown(record, reason) {
        try {
            return this.publicJob(await this._observe(record));
        } catch (error) {
            record.state = "UNKNOWN";
            record.error = { code: error.code || reason, message: error.message || "Submit outcome cannot be confirmed" };
            await this.journal.put(record);
            return this.publicJob(record);
        }
    }

    async getJob(jobId) {
        return this._exclusive(async () => {
            if (!JOB_ID.test(jobId)) fail("INVALID_JOB_ID", "Invalid Manga job ID", 400);
            const record = await this.journal.get(jobId);
            if (!record) fail("JOB_NOT_FOUND", "Manga job not found", 404);
            if (ACTIVE.has(record.state)) return this._reconcileUnknown(record, "RECONCILE_UNAVAILABLE");
            return this.publicJob(record);
        });
    }

    async _image(locator) {
        const query = new URLSearchParams(locator);
        const response = await this._fetch(`/view?${query}`);
        if (!response.ok || !/^(image\/png)(;|$)/i.test(response.headers.get("content-type") || "")) {
            fail("OUTPUT_UNAVAILABLE", "Owned Manga image is unavailable", 502);
        }
        const chunks = [];
        let size = 0;
        for await (const chunk of response.body) {
            size += chunk.length;
            if (size > 32 * 1024 * 1024) fail("OUTPUT_INVALID", "Owned Manga PNG exceeds 32 MiB", 502);
            chunks.push(chunk);
        }
        const bytes = Buffer.concat(chunks);
        if (bytes.length < PNG_SIGNATURE.length ||
            !bytes.subarray(0, PNG_SIGNATURE.length).equals(PNG_SIGNATURE)) {
            fail("OUTPUT_INVALID", "Owned Manga output is not a bounded PNG", 502);
        }
        return bytes;
    }

    async getResult(jobId) {
        return this._exclusive(async () => {
            if (!JOB_ID.test(jobId)) fail("INVALID_JOB_ID", "Invalid Manga job ID", 400);
            const record = await this.journal.get(jobId);
            if (!record) fail("JOB_NOT_FOUND", "Manga job not found", 404);
            if (record.state !== "SUCCEEDED") fail("RESULT_NOT_READY", "Manga result is not verified", 409);
            const locator = validateOutputLocator(record.output_locator, jobId);
            return this._image(locator);
        });
    }

    publicJob(record) {
        const { ownership_token, ...visible } = record;
        return visible;
    }
}
