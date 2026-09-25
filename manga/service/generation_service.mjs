/** PLAY1b Manga-owned submission, observation, and output boundary. No UI or runtime lifecycle. */
import { createHash, randomBytes, randomUUID } from "node:crypto";
import { isDeepStrictEqual } from "node:util";
import { GenerationJournal, JournalError, JOB_ID } from "./generation_journal.mjs";
import { IsolatedScenePrepService, IsolatedScenePrepError } from "./isolated_scene_prep_service.mjs";
import { analyzePngArtifact, PngArtifactAnalyzerError } from "./png_artifact_analyzer.mjs";
import { buildSceneResultManifest, SceneResultBuilderError } from "./scene_result_builder.mjs";
import { SceneResultStore, SceneResultStoreError } from "./scene_result_store.mjs";
import { SceneResultIndex, SceneResultIndexError } from "./scene_result_index.mjs";

const SETTINGS = new Set([
    "mode", "checkpoint_id", "positive_raw", "negative_raw", "sampler_id", "scheduler_id",
    "steps", "cfg", "width", "height", "seed_requested", "capability_revision"
]);
const SCENE_SETTINGS = new Set([
    "mode", "checkpoint_id", "authoring_document", "page_index", "sampler_id", "scheduler_id",
    "steps", "cfg", "seed_requested", "capability_revision", "mask_feather", "panel_strength",
    "controlnet_strength", "controlnet_start_percent", "controlnet_end_percent",
    "reference_weight", "reference_start", "reference_end", "reference_start_at", "reference_end_at"
]);
const SCENE_REQUIRED_SETTINGS = new Set([
    "mode", "checkpoint_id", "authoring_document", "page_index", "sampler_id", "scheduler_id",
    "steps", "cfg", "seed_requested", "capability_revision"
]);
const GRAPH_CLASSES = new Set([
    "CheckpointLoaderSimple", "LoraLoader", "CLIPTextEncode", "EmptyLatentImage",
    "KSampler", "VAEDecode", "SaveImage"
]);
const SCENE_GRAPH_CLASSES = new Set([
    "CheckpointLoaderSimple", "LoraLoader", "TegakiMangaPagePlanFromJSON",
    "TegakiMangaConditioningBuilder", "LoadImage", "CLIPVisionLoader",
    "IPAdapterModelLoader", "IPAdapterAdvanced", "ControlNetLoader",
    "ControlNetApplyAdvanced", "EmptyLatentImage", "KSampler",
    "VAEDecode", "SaveImage"
]);
const SHA256 = /^[0-9a-f]{64}$/;
const PNG_SIGNATURE = Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]);
const FORBIDDEN_CLIENT_DISPATCH_FIELDS = [
    "backend_url", "backend_origin", "snapshot_id", "snapshot", "job_id",
    "prompt_id", "manifest_id", "artifact_locator", "graph", "graph_digest",
    "compile_metadata", "page_compile_plan", "save_node_id"
];

export function validatePreparedBundle(bundle) {
    if (!isObject(bundle)) {
        fail("INVALID_PREPARED_BUNDLE", "Prepared bundle must be a non-null object", 400);
    }
    if (!isObject(bundle.owner) ||
        typeof bundle.owner.document_id !== "string" || !bundle.owner.document_id ||
        typeof bundle.owner.page_id !== "string" || !bundle.owner.page_id ||
        typeof bundle.owner.scene_id !== "string" || !bundle.owner.scene_id) {
        fail("INVALID_PREPARED_BUNDLE", "Prepared bundle owner must contain document_id, page_id, and scene_id", 400);
    }
    if (!isObject(bundle.snapshot) ||
        typeof bundle.snapshot.snapshot_id !== "string" || !bundle.snapshot.snapshot_id ||
        typeof bundle.snapshot.snapshot_ref !== "string" || !bundle.snapshot.snapshot_ref ||
        typeof bundle.snapshot.content_digest !== "string" || !SHA256.test(bundle.snapshot.content_digest)) {
        fail("INVALID_PREPARED_BUNDLE", "Prepared bundle snapshot must contain valid snapshot_id, snapshot_ref, and content_digest", 400);
    }
    if (!isObject(bundle.graph) || Object.keys(bundle.graph).length === 0) {
        fail("INVALID_PREPARED_BUNDLE", "Prepared bundle graph must be a non-empty object", 400);
    }
    if (typeof bundle.graph_digest !== "string" || !SHA256.test(bundle.graph_digest)) {
        fail("INVALID_PREPARED_BUNDLE", "Prepared bundle graph_digest must be a 64-character SHA-256 hash", 400);
    }
    if (typeof bundle.save_node_id !== "string" && typeof bundle.save_node_id !== "number") {
        fail("INVALID_PREPARED_BUNDLE", "Prepared bundle save_node_id must be a string or number", 400);
    }
    const saveNode = bundle.graph[bundle.save_node_id];
    if (!isObject(saveNode) || saveNode.class_type !== "SaveImage" || !isObject(saveNode.inputs)) {
        fail("INVALID_PREPARED_BUNDLE", "Prepared bundle save_node_id must point to a valid SaveImage node", 400);
    }
    if (!isObject(bundle.page_compile_plan)) {
        fail("INVALID_PREPARED_BUNDLE", "Prepared bundle page_compile_plan must be an object", 400);
    }
    if (typeof bundle.page_compile_plan_digest !== "string" || !bundle.page_compile_plan_digest) {
        fail("INVALID_PREPARED_BUNDLE", "Prepared bundle page_compile_plan_digest must be a non-empty string", 400);
    }
    if (!isObject(bundle.compile_metadata)) {
        fail("INVALID_PREPARED_BUNDLE", "Prepared bundle compile_metadata must be an object", 400);
    }
    if (!isObject(bundle.compile_metadata.effective_settings)) {
        fail("INVALID_PREPARED_BUNDLE", "Prepared bundle compile_metadata.effective_settings must be an object", 400);
    }
    return bundle;
}
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
const isNonEmptyString = value => typeof value === "string" && value.trim().length > 0;

/**
 * Canonical SceneResult manifest identity for one isolated job.
 * Deterministic (job_id -> manifest_id) so a retried finalization after a
 * partial failure (saved but not indexed) converges on the same immutable
 * record instead of creating a second manifest.  RFC 4122 v4 layout (version
 * and variant bits set) as required by the SceneResult manifest contract.
 */
export function sceneResultManifestIdForJob(jobId) {
    const h = createHash("sha256").update(`tegaki.manga.scene_result.v1:${jobId}`).digest("hex");
    const variant = ((parseInt(h[16], 16) & 0x3) | 0x8).toString(16);
    return `${h.slice(0, 8)}-${h.slice(8, 12)}-4${h.slice(13, 16)}-${variant}${h.slice(17, 20)}-${h.slice(20, 32)}`;
}

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
                  fetchFn = fetch, timeoutMs = 5000, isolatedScenePrepService = null,
                  sceneResultStore = null, sceneResultIndex = null } = {}) {
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
        this.isolatedScenePrepService = isolatedScenePrepService || new IsolatedScenePrepService({
            backendUrl: this.origin,
            fetchFn: this.fetchFn,
            timeoutMs: this.timeoutMs
        });
        this.sceneResultStore = sceneResultStore || new SceneResultStore();
        this.sceneResultIndex = sceneResultIndex || new SceneResultIndex({ store: this.sceneResultStore });
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
            typeof result.positive_raw !== "string" || result.positive_raw !== settings.positive_raw ||
            typeof result.negative_raw !== "string" || result.negative_raw !== settings.negative_raw ||
            typeof result.positive_expanded !== "string" || typeof result.negative_expanded !== "string" ||
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

    async _compileScene(settings, requestId, expectedDigest, effectiveSeed) {
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
        const compileRequest = {
            mask_feather: 16,
            panel_strength: 1.0,
            ...settings,
            request_id: requestId,
            seed_requested: seed
        };
        const response = await this._json("/tegaki/manga/generation/compile-scene", {
            method: "POST", headers: { "Content-Type": "application/json" },
            body: JSON.stringify(compileRequest)
        });
        if (!response.ok || response.data.ok !== true) {
            fail(response.data.error_code || "COMPILE_REJECTED", response.data.error || "Backend Scene compile rejected", response.status);
        }
        const result = response.data;
        if (result.graph_digest !== expectedDigest || result.capability_revision !== settings.capability_revision) {
            fail("DIGEST_MISMATCH", "Reviewed Scene graph digest or capability revision differs", 409);
        }
        if (!isDeepStrictEqual(result.normalized_request, compileRequest) || !isObject(result.graph) ||
            typeof result.page_compile_plan_digest !== "string" || !isObject(result.audit_trail) ||
            !Array.isArray(result.resolved_loras) || !isObject(result.effective_authoring_document) ||
            !isObject(result.page_compile_plan) || !Array.isArray(result.scene_ids) || result.effective_seed !== Number(seed) ||
            !isObject(result.resolution) || !Number.isInteger(result.resolution.width) ||
            !Number.isInteger(result.resolution.height)) {
            fail("COMPILE_INVALID", "Backend Scene compile result does not match request", 502);
        }
        const page = result.effective_authoring_document.pages?.[settings.page_index];
        if (!isObject(page) || page.width_px !== result.resolution.width || page.height_px !== result.resolution.height) {
            fail("COMPILE_INVALID", "Scene resolution does not match the effective Authoring page", 502);
        }
        const nodes = Object.entries(result.graph);
        if (!nodes.length || nodes.some(([, node]) => !isObject(node) || !SCENE_GRAPH_CLASSES.has(node.class_type))) {
            fail("COMPILE_INVALID", "Backend compiled an unsupported Scene graph", 502);
        }
        const saves = nodes.filter(([, node]) => node.class_type === "SaveImage");
        const adapters = nodes.filter(([, node]) => node.class_type === "TegakiMangaPagePlanFromJSON");
        const builders = nodes.filter(([, node]) => node.class_type === "TegakiMangaConditioningBuilder");
        if (saves.length !== 1 || adapters.length !== 1 || builders.length !== 1 ||
            saves[0][1].inputs?.filename_prefix !== "Manga/Playable/compiled") {
            fail("COMPILE_INVALID", "Backend Scene graph lacks the single page-plan conditioning path", 502);
        }
        const latent = nodes.filter(([, node]) => node.class_type === "EmptyLatentImage");
        if (latent.length !== 1 || latent[0][1].inputs?.width !== result.resolution.width ||
            latent[0][1].inputs?.height !== result.resolution.height || latent[0][1].inputs?.batch_size !== 1) {
            fail("COMPILE_INVALID", "Scene graph resolution is not the authoring page resolution", 502);
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

    _validateSceneSubmission(body) {
        if (!isObject(body) || !isObject(body.settings) ||
            Object.keys(body).some(key => !["settings", "idempotency_key", "expected_graph_digest", "effective_seed"].includes(key)) ||
            Object.keys(body.settings).length < SCENE_REQUIRED_SETTINGS.size ||
            Object.keys(body.settings).some(key => !SCENE_SETTINGS.has(key))) {
            fail("INVALID_REQUEST", "Provide only PLAY5 Scene settings and reviewed digest", 400);
        }
        const settings = body.settings;
        if (settings.mode !== "scene" || !isObject(settings.authoring_document) ||
            !Number.isInteger(settings.page_index) || settings.page_index < 0 ||
            typeof settings.checkpoint_id !== "string" || typeof settings.sampler_id !== "string" ||
            typeof settings.scheduler_id !== "string" || typeof settings.seed_requested !== "string" ||
            !Number.isInteger(settings.steps) || typeof settings.cfg !== "number" ||
            (Object.hasOwn(settings, "mask_feather") && !Number.isInteger(settings.mask_feather)) ||
            (Object.hasOwn(settings, "panel_strength") && typeof settings.panel_strength !== "number") ||
            (Object.hasOwn(settings, "controlnet_strength") && typeof settings.controlnet_strength !== "number") ||
            (Object.hasOwn(settings, "controlnet_start_percent") && typeof settings.controlnet_start_percent !== "number") ||
            (Object.hasOwn(settings, "controlnet_end_percent") && typeof settings.controlnet_end_percent !== "number") ||
            (Object.hasOwn(settings, "reference_weight") && typeof settings.reference_weight !== "number") ||
            (Object.hasOwn(settings, "reference_start") && typeof settings.reference_start !== "number") ||
            (Object.hasOwn(settings, "reference_end") && typeof settings.reference_end !== "number") ||
            (Object.hasOwn(settings, "reference_start_at") && typeof settings.reference_start_at !== "number") ||
            (Object.hasOwn(settings, "reference_end_at") && typeof settings.reference_end_at !== "number")) {
            fail("INVALID_REQUEST", "Invalid PLAY5 Scene settings", 400);
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
                raw_positive: result.positive_raw, raw_negative: result.negative_raw,
                positive_raw: result.positive_raw, negative_raw: result.negative_raw,
                expanded_positive: result.positive_expanded, expanded_negative: result.negative_expanded,
                positive_expanded: result.positive_expanded, negative_expanded: result.negative_expanded,
                clean_positive: result.positive_clean, clean_negative: result.negative_clean,
                positive_clean: result.positive_clean, negative_clean: result.negative_clean,
                wildcard_root: typeof result.wildcard_root === "string" ? result.wildcard_root : null,
                dynamicprompts_version: typeof result.dynamicprompts_version === "string" ? result.dynamicprompts_version : null,
                dynamic_seed_domains: isObject(result.dynamic_seed_domains)
                    ? structuredClone(result.dynamic_seed_domains) : null,
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

    async createSceneJob(input) {
        return this._exclusive(async () => {
            const body = this._validateSceneSubmission(input);
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
            const { result, saveNodeId } = await this._compileScene(
                body.settings, requestId, body.expected_graph_digest, body.effective_seed
            );
            const token = randomBytes(32).toString("hex");
            const audit = isObject(result.audit_trail) ? structuredClone(result.audit_trail) : {};
            const globalPositive = audit.global?.positive || {};
            const globalNegative = audit.global?.negative || {};
            const record = {
                job_id: jobId, request_id: requestId, idempotency_key: body.idempotency_key,
                requested_settings: structuredClone(body.settings),
                effective_settings: { ...result.normalized_request, seed_requested: String(result.effective_seed) },
                raw_positive: typeof globalPositive.raw === "string" ? globalPositive.raw : "",
                raw_negative: typeof globalNegative.raw === "string" ? globalNegative.raw : "",
                positive_raw: typeof globalPositive.raw === "string" ? globalPositive.raw : "",
                negative_raw: typeof globalNegative.raw === "string" ? globalNegative.raw : "",
                expanded_positive: typeof globalPositive.expanded === "string" ? globalPositive.expanded : "",
                expanded_negative: typeof globalNegative.expanded === "string" ? globalNegative.expanded : "",
                positive_expanded: typeof globalPositive.expanded === "string" ? globalPositive.expanded : "",
                negative_expanded: typeof globalNegative.expanded === "string" ? globalNegative.expanded : "",
                clean_positive: typeof globalPositive.clean === "string" ? globalPositive.clean : "",
                clean_negative: typeof globalNegative.clean === "string" ? globalNegative.clean : "",
                positive_clean: typeof globalPositive.clean === "string" ? globalPositive.clean : "",
                negative_clean: typeof globalNegative.clean === "string" ? globalNegative.clean : "",
                wildcard_root: typeof result.wildcard_root === "string" ? result.wildcard_root : null,
                dynamicprompts_version: typeof result.dynamicprompts_version === "string" ? result.dynamicprompts_version : null,
                dynamic_seed_domains: isObject(result.dynamic_seed_domains) ? structuredClone(result.dynamic_seed_domains) : null,
                resolved_loras: structuredClone(result.resolved_loras || []),
                effective_authoring_document: structuredClone(result.effective_authoring_document),
                page_compile_plan: structuredClone(result.page_compile_plan),
                page_compile_plan_digest: result.page_compile_plan_digest,
                audit_trail: audit,
                scene_ids: Array.isArray(result.scene_ids) ? [...result.scene_ids] : [],
                resolution: structuredClone(result.resolution),
                capability_revision: body.settings.capability_revision,
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
                record.error = { code: "BACKEND_REJECTED", message: reply.data.error?.message || "Backend rejected the Scene graph" };
                await this.journal.put(record);
                return this.publicJob(record);
            }
            return this._reconcileUnknown(record, "SUBMIT_UNCONFIRMED");
        });
    }


    _validateIsolatedSceneSubmission(body) {
        if (!isObject(body)) {
            fail("INVALID_REQUEST", "Request body must be an object", 400);
        }
        const forbiddenFound = new Set();
        for (const f of FORBIDDEN_CLIENT_DISPATCH_FIELDS) {
            if (Object.hasOwn(body, f)) forbiddenFound.add(f);
            if (isObject(body.settings) && Object.hasOwn(body.settings, f)) forbiddenFound.add(f);
        }
        if (forbiddenFound.size > 0) {
            fail("INVALID_REQUEST", `Forbidden client request fields: ${[...forbiddenFound].join(", ")}`, 400);
        }
        if (body.idempotency_key !== undefined) {
            if (typeof body.idempotency_key !== "string" || !/^[A-Za-z0-9_-]{1,64}$/.test(body.idempotency_key)) {
                fail("INVALID_REQUEST", "Invalid idempotency key", 400);
            }
        }
        const doc = body.authoring_document || body.settings?.authoring_document;
        const sceneId = body.scene_id || body.settings?.scene_id;
        const genParams = body.generation_params || body.settings?.generation_params || (
            isObject(body.settings) && body.settings.mode === "isolated_scene" ? body.settings : null
        );
        if (!isObject(doc)) {
            fail("INVALID_REQUEST", "authoring_document is required", 400);
        }
        if (typeof sceneId !== "string" || !sceneId.trim()) {
            fail("INVALID_REQUEST", "scene_id is required", 400);
        }
        if (!isObject(genParams)) {
            fail("INVALID_REQUEST", "generation_params is required", 400);
        }
        return body;
    }

    async dispatchIsolatedScene(bundle, { idempotency_key, requested_settings } = {}) {
        return this._exclusive(async () => {
            validatePreparedBundle(bundle);
            const idempotencyKey = idempotency_key || randomUUID();
            if (typeof idempotencyKey !== "string" || !/^[A-Za-z0-9_-]{1,64}$/.test(idempotencyKey)) {
                fail("INVALID_REQUEST", "Invalid idempotency key", 400);
            }

            let records;
            try {
                records = await this.journal.list();
            } catch (error) {
                if (error instanceof JournalError) fail(error.code, error.message, 503);
                throw error;
            }
            if (records.some(record => record.idempotency_key === idempotencyKey)) {
                fail("DUPLICATE_REQUEST", "Manga request was already recorded", 409);
            }
            if (records.some(record => ACTIVE.has(record.state) && record.graph_digest === bundle.graph_digest)) {
                fail("DUPLICATE_GRAPH", "Identical reviewed graph already has an unresolved job", 409);
            }
            if (records.some(record => ACTIVE.has(record.state))) {
                fail("OWNED_JOB_BUSY", "A Manga-owned job is still unresolved", 409);
            }

            const jobId = randomUUID();
            const requestId = randomUUID();
            const token = randomBytes(32).toString("hex");

            const executionGraph = structuredClone(bundle.graph);
            const saveNode = executionGraph[bundle.save_node_id];
            saveNode.inputs.filename_prefix = `Manga/Playable/${jobId}`;
            const submittedGraphDigest = hash(stable(executionGraph));

            const record = {
                job_id: jobId,
                request_id: requestId,
                idempotency_key: idempotencyKey,
                mode: "isolated_scene",
                owner: structuredClone(bundle.owner),
                snapshot: structuredClone(bundle.snapshot),
                plan: bundle.plan ? structuredClone(bundle.plan) : null,
                requested_settings: isObject(requested_settings) ? structuredClone(requested_settings) : { mode: "isolated_scene" },
                effective_settings: structuredClone(bundle.compile_metadata.effective_settings),
                graph_digest: bundle.graph_digest,
                submitted_graph_digest: submittedGraphDigest,
                save_node_id: String(bundle.save_node_id),
                page_compile_plan: structuredClone(bundle.page_compile_plan),
                page_compile_plan_digest: bundle.page_compile_plan_digest,
                compile_metadata: structuredClone(bundle.compile_metadata),
                audit_trail: bundle.audit_trail ? structuredClone(bundle.audit_trail) : null,
                backend_identity: null,
                prompt_id: null,
                created_at: now(),
                submitted_at: null,
                started_at: null,
                finished_at: null,
                state: "VALIDATING",
                error: null,
                output_locator: null,
                ownership_token: token,
            };

            await this.journal.put(record);

            record.state = "SUBMITTING";
            await this.journal.put(record);

            const payload = {
                prompt: executionGraph,
                extra_data: {
                    tegaki_manga: {
                        job_id: jobId,
                        request_id: requestId,
                        graph_digest: bundle.graph_digest,
                        submitted_graph_digest: submittedGraphDigest,
                        ownership_token: token,
                    }
                }
            };

            let reply;
            try {
                reply = await this._json("/prompt", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(payload)
                });
            } catch (error) {
                record.state = "UNKNOWN";
                record.finished_at = now();
                record.error = {
                    code: error.code || "SUBMIT_UNCONFIRMED",
                    message: error.message || "Submit outcome cannot be confirmed"
                };
                await this.journal.put(record);
                return this.publicJob(record);
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

            record.state = "FAILED";
            record.finished_at = now();
            record.error = {
                code: reply.data?.error_code || "BACKEND_REJECTED",
                message: reply.data?.error?.message || reply.data?.error || "Backend rejected the isolated Scene graph"
            };
            await this.journal.put(record);
            return this.publicJob(record);
        });
    }

    async createIsolatedSceneJob(input) {
        this._validateIsolatedSceneSubmission(input);

        const prepInput = {
            authoring_document: input.authoring_document || input.settings?.authoring_document,
            scene_id: input.scene_id || input.settings?.scene_id,
            generation_params: input.generation_params || input.settings?.generation_params || (
                isObject(input.settings) && input.settings.mode === "isolated_scene" ? input.settings : null
            ),
        };
        if (input.page_id !== undefined || input.settings?.page_id !== undefined) {
            prepInput.page_id = input.page_id ?? input.settings?.page_id;
        }
        if (input.page_index !== undefined || input.settings?.page_index !== undefined) {
            prepInput.page_index = input.page_index ?? input.settings?.page_index;
        }
        if (input.local_dimensions !== undefined || input.settings?.local_dimensions !== undefined) {
            prepInput.local_dimensions = input.local_dimensions ?? input.settings?.local_dimensions;
        }
        if (input.random_seed !== undefined || input.settings?.random_seed !== undefined) {
            prepInput.random_seed = input.random_seed ?? input.settings?.random_seed;
        }

        let bundle;
        try {
            bundle = await this.isolatedScenePrepService.prepareIsolatedScene(prepInput);
        } catch (error) {
            if (error instanceof IsolatedScenePrepError) {
                fail(error.code || "PREPARATION_FAILED", error.message, error.status || 400);
            }
            throw error;
        }

        const idempotencyKey = input.idempotency_key || input.settings?.idempotency_key;
        return this.dispatchIsolatedScene(bundle, {
            idempotency_key: idempotencyKey,
            requested_settings: input.generation_params || input.settings || input
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
        if (record.prompt_id === null) {
            if (record.mode === "isolated_scene") {
                fail("JOB_UNCONFIRMED", "Isolated scene job has no confirmed prompt ID", 409);
            }
            await this._recoverPromptId(record);
        }
        const history = await this._history(record);
        if (history) {
            const status = history.status;
            if (status?.completed === true && status.status_str === "success") {
                const images = history.outputs?.[record.save_node_id]?.images;
                if (!Array.isArray(images) || images.length !== 1) {
                    fail("OUTPUT_INVALID", "Completed history lacks the expected SaveImage output", 502);
                }
                const locator = validateOutputLocator(images[0], record.job_id);
                if (record.mode !== "isolated_scene") {
                    await this._image(locator);
                }
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

    async observeIsolatedSceneJob(jobId) {
        return this._exclusive(async () => {
            if (!JOB_ID.test(jobId)) fail("INVALID_JOB_ID", "Invalid Manga job ID", 400);
            const record = await this.journal.get(jobId);
            if (!record) fail("JOB_NOT_FOUND", "Manga job not found", 404);
            if (record.mode !== "isolated_scene") {
                fail("INVALID_JOB_MODE", "Job is not an isolated-Scene job", 400);
            }
            if (record.state === "SUCCEEDED" || record.state === "FAILED") {
                return this.publicJob(record);
            }
            if (!record.prompt_id || !JOB_ID.test(record.prompt_id)) {
                fail("JOB_UNCONFIRMED", "Isolated scene job has no confirmed prompt ID", 409);
            }
            return this._reconcileUnknown(record, "RECONCILE_UNAVAILABLE");
        });
    }

    async analyzeIsolatedSceneArtifact(jobId) {
        return this._exclusive(() => this._analyzeIsolatedSceneArtifactLocked(jobId));
    }

    async _analyzeIsolatedSceneArtifactLocked(jobId) {
        {
            if (!JOB_ID.test(jobId)) fail("INVALID_JOB_ID", "Invalid Manga job ID", 400);
            let record;
            try {
                record = await this.journal.get(jobId);
            } catch (error) {
                if (error instanceof JournalError) fail(error.code, error.message, 503);
                throw error;
            }
            if (!record) fail("JOB_NOT_FOUND", "Manga job not found", 404);
            if (record.mode !== "isolated_scene") {
                fail("INVALID_JOB_MODE", "Job is not an isolated-Scene job", 400);
            }
            if (record.state !== "SUCCEEDED") {
                fail("JOB_NOT_READY", `Isolated scene job is in state '${record.state}', expected 'SUCCEEDED'`, 409);
            }
            if (!record.prompt_id || !JOB_ID.test(record.prompt_id)) {
                fail("JOB_UNCONFIRMED", "Isolated scene job has no confirmed prompt ID", 409);
            }
            if (!isObject(record.compile_metadata) || !isObject(record.compile_metadata.local_dimensions)) {
                fail("LOCAL_DIMENSIONS_REQUIRED", "Isolated scene compile_metadata lacks local_dimensions", 502);
            }
            const localDims = record.compile_metadata.local_dimensions;
            const expW = localDims.width;
            const expH = localDims.height;
            if (typeof expW !== "number" || !Number.isInteger(expW) || expW <= 0 ||
                typeof expH !== "number" || !Number.isInteger(expH) || expH <= 0) {
                fail("LOCAL_DIMENSIONS_INVALID", "compile_metadata.local_dimensions must contain positive integers", 502);
            }

            const locator = validateOutputLocator(record.output_locator, record.job_id);
            const bytes = await this._image(locator);

            let analysis;
            try {
                analysis = analyzePngArtifact(bytes, { width: expW, height: expH });
            } catch (err) {
                if (err instanceof PngArtifactAnalyzerError) {
                    fail(err.code || "ARTIFACT_ANALYSIS_FAILED", err.message, 502);
                }
                throw err;
            }

            return {
                job_id: record.job_id,
                prompt_id: record.prompt_id,
                output_locator: {
                    filename: locator.filename,
                    subfolder: locator.subfolder,
                    type: locator.type
                },
                png_analysis: {
                    content_digest: analysis.content_digest,
                    declared_width: analysis.declared_width,
                    declared_height: analysis.declared_height,
                    byte_length: analysis.byte_length
                }
            };
        }
    }

    /**
     * Idempotent: one isolated job -> one canonical SceneResult.  Serialized with
     * all other job operations (getJob polling included) through _exclusive.
     */
    async finalizeIsolatedSceneResult(jobId, options = {}) {
        return this._exclusive(() => this._finalizeIsolatedSceneResultLocked(jobId, options));
    }

    _verifyExistingSceneResult(existing, record) {
        if (!isObject(existing) || existing.execution?.job_id !== record.job_id ||
            existing.owner?.document_id !== record.owner?.document_id ||
            existing.owner?.page_id !== record.owner?.page_id ||
            existing.owner?.scene_id !== record.owner?.scene_id) {
            fail("SCENE_RESULT_CONSISTENCY_ERROR",
                `Stored SceneResult ${existing?.manifest_id} does not belong to job ${record.job_id}`, 409);
        }
    }

    async _indexSceneResult(manifestId) {
        try {
            await this.sceneResultIndex.indexManifest(manifestId);
        } catch (indexError) {
            const status = indexError.code === "JOB_RESULT_CONFLICT" ? 409 : 500;
            fail(indexError.code || "INDEX_PUBLICATION_FAILED", `Manifest saved but indexing failed: ${indexError.message}`, status);
        }
    }

    async _finalizeIsolatedSceneResultLocked(jobId, options = {}) {
        if (!isNonEmptyString(jobId) || !JOB_ID.test(jobId)) {
            fail("INVALID_JOB_ID", "Invalid Manga job ID", 400);
        }

        let record;
        try {
            record = await this.journal.get(jobId);
        } catch (error) {
            if (error instanceof JournalError) fail(error.code, error.message, 503);
            throw error;
        }

        if (!record) {
            fail("JOB_NOT_FOUND", "Manga job not found", 404);
        }

        if (record.mode !== "isolated_scene") {
            fail("INVALID_JOB_MODE", "Job is not an isolated-Scene job", 400);
        }

        if (record.state !== "SUCCEEDED") {
            fail("JOB_NOT_READY", `Isolated scene job is in state '${record.state}', expected 'SUCCEEDED'`, 409);
        }

        let canonicalResult;
        try {
            canonicalResult = await this.sceneResultIndex.getByJobId(jobId);
        } catch (indexError) {
            if (indexError instanceof SceneResultIndexError) fail(indexError.code, indexError.message, 500);
            throw indexError;
        }
        if (canonicalResult) {
            this._verifyExistingSceneResult(canonicalResult.manifest, record);
            return {
                manifest_id: canonicalResult.manifest_id,
                manifest: canonicalResult.manifest,
            };
        }

        if (!isNonEmptyString(record.prompt_id) || !JOB_ID.test(record.prompt_id)) {
            fail("MISSING_EXECUTION_PROVENANCE", "Job record missing valid prompt_id", 500);
        }

        if (!isObject(record.owner) ||
            !isNonEmptyString(record.owner.document_id) ||
            !isNonEmptyString(record.owner.page_id) ||
            !isNonEmptyString(record.owner.scene_id)) {
            fail("MISSING_EXECUTION_PROVENANCE", "Job record missing complete owner identity", 500);
        }

        if (!isObject(record.snapshot) ||
            !isNonEmptyString(record.snapshot.snapshot_ref) ||
            !isNonEmptyString(record.snapshot.content_digest) ||
            !SHA256.test(record.snapshot.content_digest)) {
            fail("MISSING_EXECUTION_PROVENANCE", "Job record missing valid snapshot provenance", 500);
        }

        if (!isObject(record.plan)) {
            fail("MISSING_EXECUTION_PROVENANCE", "Job record missing plan", 500);
        }

        if (!isObject(record.compile_metadata)) {
            fail("MISSING_EXECUTION_PROVENANCE", "Job record missing compile_metadata", 500);
        }

        if (!isNonEmptyString(record.graph_digest) || !SHA256.test(record.graph_digest)) {
            fail("MISSING_EXECUTION_PROVENANCE", "Job record missing valid graph_digest", 500);
        }

        if (!isNonEmptyString(record.submitted_graph_digest) || !SHA256.test(record.submitted_graph_digest)) {
            fail("MISSING_EXECUTION_PROVENANCE", "Job record missing valid submitted_graph_digest", 500);
        }

        if (!isObject(record.page_compile_plan)) {
            fail("MISSING_EXECUTION_PROVENANCE", "Job record missing page_compile_plan", 500);
        }

        if (!isNonEmptyString(record.page_compile_plan_digest) || !SHA256.test(record.page_compile_plan_digest)) {
            fail("MISSING_EXECUTION_PROVENANCE", "Job record missing valid page_compile_plan_digest", 500);
        }

        if (!isObject(record.effective_settings)) {
            fail("MISSING_EXECUTION_PROVENANCE", "Job record missing effective_settings", 500);
        }

        if (typeof record.save_node_id !== "string" && typeof record.save_node_id !== "number") {
            fail("MISSING_EXECUTION_PROVENANCE", "Job record missing valid save_node_id", 500);
        }

        if (!isObject(record.output_locator)) {
            fail("MISSING_EXECUTION_PROVENANCE", "Job record missing output_locator", 500);
        }

        const planRef = record.plan.reference;
        if (!isObject(planRef) || planRef.enabled !== false) {
            fail("REFERENCE_NOT_DISABLED", "Isolated scene job must be Reference-disabled", 400);
        }

        const manifestId = (typeof options._manifestIdFactory === "function")
            ? options._manifestIdFactory()
            : sceneResultManifestIdForJob(jobId);

        // Recovery of a previous partial finalization (persisted, not indexed):
        // reuse the immutable record only if it provably belongs to this job.
        const adoptExisting = async () => {
            let existing;
            try {
                existing = await this.sceneResultStore.getManifest(manifestId, { required: false });
            } catch (storeError) {
                fail("SCENE_RESULT_CONSISTENCY_ERROR", `Stored SceneResult ${manifestId} is unreadable: ${storeError.message}`, 409);
            }
            if (!existing) return null;
            this._verifyExistingSceneResult(existing, record);
            await this._indexSceneResult(existing.manifest_id);
            return { manifest_id: existing.manifest_id, manifest: existing };
        };
        const adopted = await adoptExisting();
        if (adopted) return adopted;

        const artifactResult = await this._analyzeIsolatedSceneArtifactLocked(jobId);

        const evidence = {
            manifest_id: manifestId,
            created_at: now(),
            owner: {
                document_id: record.owner.document_id,
                page_id: record.owner.page_id,
                scene_id: record.owner.scene_id,
            },
            input_provenance: {
                authoring_snapshot_ref: record.snapshot.snapshot_ref,
                authoring_snapshot_digest: record.snapshot.content_digest,
            },
            plan: record.plan,
            compile_metadata: record.compile_metadata,
            job: {
                job_id: record.job_id,
                prompt_id: record.prompt_id,
                state: record.state,
                graph_digest: record.graph_digest,
                page_compile_plan_digest: record.page_compile_plan_digest,
                effective_settings: record.effective_settings,
                scene_id: record.owner.scene_id,
                page_id: record.owner.page_id,
            },
            reference: {
                enabled: false,
                reference_asset: null,
                content_digest: null,
            },
            locator: artifactResult.output_locator,
            png_analysis: artifactResult.png_analysis,
        };

        let manifest;
        try {
            manifest = buildSceneResultManifest(evidence, {
                _computeDigest: options._computeDigest,
            });
        } catch (builderError) {
            if (builderError instanceof SceneResultBuilderError) {
                fail(builderError.code, `Manifest assembly failed: ${builderError.message}`, 500);
            }
            throw builderError;
        }

        let saved;
        try {
            saved = await this.sceneResultStore.saveCompletedManifest(manifest);
        } catch (storeError) {
            if (storeError instanceof SceneResultStoreError && storeError.code === "MANIFEST_EXISTS") {
                const raced = await adoptExisting();
                if (raced) return raced;
            }
            if (storeError instanceof SceneResultStoreError) {
                fail(storeError.code, `Manifest persistence failed: ${storeError.message}`, 500);
            }
            throw storeError;
        }

        await this._indexSceneResult(saved.manifest_id);

        return {
            manifest_id: saved.manifest_id,
            manifest: saved,
        };
    }

    async getJob(jobId) {
        return this._exclusive(async () => {
            if (!JOB_ID.test(jobId)) fail("INVALID_JOB_ID", "Invalid Manga job ID", 400);
            const record = await this.journal.get(jobId);
            if (!record) fail("JOB_NOT_FOUND", "Manga job not found", 404);
            const job = ACTIVE.has(record.state)
                ? await this._reconcileUnknown(record, "RECONCILE_UNAVAILABLE")
                : this.publicJob(record);
            if (job.mode === "isolated_scene" && job.state === "SUCCEEDED") {
                return this._withSceneResult(job);
            }
            return job;
        });
    }

    /**
     * Auto-finalization on the normal observation path (B4).  Only a verified
     * SUCCEEDED isolated job reaches here.  Idempotent: an already-indexed job
     * returns its canonical association without new persistence.  The
     * association is response-only derived data (never written to the journal
     * or the Authoring Document).  A failure never masks the job state; it is
     * reported as a structured scene_result error and retried on the next poll.
     */
    async _withSceneResult(job) {
        try {
            const finalized = await this._finalizeIsolatedSceneResultLocked(job.job_id);
            return { ...job, scene_result: { status: "FINALIZED", manifest_id: finalized.manifest_id, error: null } };
        } catch (error) {
            return {
                ...job,
                scene_result: {
                    status: "FINALIZATION_FAILED",
                    manifest_id: null,
                    error: {
                        code: error?.code || "SCENE_RESULT_FINALIZATION_FAILED",
                        message: error?.message || "SceneResult finalization failed",
                    },
                },
            };
        }
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
