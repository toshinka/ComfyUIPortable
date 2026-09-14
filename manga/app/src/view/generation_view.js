/** PLAY1c Manga Generate view. Owns no ComfyUI routes and no authoring document data. */
import { GenerationState, ACTIVE_JOB_STATES } from "../state/generation_state.js";
import { MangaGenerationClient } from "../adapters/manga_generation_client.js";
import { createTagAutocomplete } from "./tag_autocomplete.js";
import { validateAuthoringDocument } from "../domain/authoring_document.js";

const FIELDS = ["checkpoint_id", "positive_raw", "negative_raw", "sampler_id", "scheduler_id",
    "steps", "cfg", "width", "height", "seed_requested"];
const SELECTS = new Set(["checkpoint_id", "sampler_id", "scheduler_id"]);
const INTEGER = /^(0|[1-9][0-9]*)$/;
const JOB_ID = /^[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}$/;
const own = (obj, key) => Object.hasOwn(obj, key);
const LORA_TAG = /^<lora:([^:<>]+):([+-]?(?:\d+(?:\.\d*)?|\.\d+))>$/;
const ANGLE_TAG = /<[^<>]*>/g;
const SCENE_LORA_TAG = /<lora:/i;

function numericBound(catalog, field) {
    const product = catalog.product_bounds?.[field];
    const backend = catalog.backend_bounds?.[field];
    return { min: Math.max(Number(product?.min), Number(backend?.min)),
        max: Math.min(Number(product?.max), Number(backend?.max)) };
}

function loraBlockReason(catalog, positive, negative) {
    if (!Array.isArray(catalog?.loras)) return "";
    const seen = new Set();
    for (const raw of [positive, negative]) {
        for (const match of String(raw || "").matchAll(ANGLE_TAG)) {
            const token = match[0];
            const tag = LORA_TAG.exec(token);
            if (!tag) return "Prompt contains malformed or unsupported LoRA syntax.";
            const name = tag[1];
            if (name.trim() !== name) return "LoRA name must not contain surrounding whitespace.";
            const available = catalog.loras.filter(entry => entry?.available === true && typeof entry.id === "string");
            const normalized = name.replaceAll("\\", "/");
            const exact = available.filter(entry => entry.id === name);
            const pathMatches = exact.length ? exact : available.filter(entry => entry.id.replaceAll("\\", "/") === normalized);
            const filename = normalized.split("/").pop();
            const stem = filename?.replace(/\.[^.]+$/, "");
            const matches = pathMatches.length ? pathMatches : available.filter(entry => {
                const item = entry.id.replaceAll("\\", "/");
                const itemName = item.split("/").pop();
                return itemName === filename || (!normalized.includes("/") && itemName?.replace(/\.[^.]+$/, "") === stem);
            });
            if (matches.length === 0) return `LoRA unavailable: ${name}`;
            if (matches.length > 1) return `LoRA name is ambiguous: ${name}`;
            if (seen.has(matches[0].id)) return `LoRA appears more than once: ${matches[0].id}`;
            seen.add(matches[0].id);
        }
    }
    return "";
}

export function generationBlockReason(state, authoringStore = state.authoringStore) {
    if (state.historyLoading) return "Checking recorded Manga jobs…";
    if (state.submitUnconfirmed) return "Job outcome is UNKNOWN; automatic retry is disabled.";
    if (state.localBusy) return "Submission is in progress…";
    if (state.activeJob && ACTIVE_JOB_STATES.has(state.activeJob.state)) return "Job already active.";
    if (!state.catalog) return state.catalogError
        ? `Capability catalog unavailable — ${state.catalogError}`
        : "Manga workspace unavailable; capability catalog unavailable.";
    try {
        if (state.mode === "scene") buildSceneGenerationSettings(state, authoringStore);
        else buildGenerationSettings(state);
    } catch (cause) {
        return cause.message;
    }
    if (state.mode === "scene") {
        const document = authoringStore?.getDocument?.();
        const scenes = document?.pages?.[0]?.scenes || [];
        if (scenes.some(scene => SCENE_LORA_TAG.test(String(scene?.prompt || "")) ||
            SCENE_LORA_TAG.test(String(scene?.negative_prompt || "")))) {
            return "Scene LoRA prompt notation is unavailable in PLAY5; remove it from the Scene document.";
        }
        return "";
    }
    return loraBlockReason(state.catalog, state.draft.positive_raw, state.draft.negative_raw);
}

export function buildGenerationSettings(state) {
    const catalog = state.catalog;
    if (!catalog) throw new Error("Manga capabilities are unavailable");
    const draft = state.draft;
    if (!catalog.checkpoints.some(entry => entry.id === draft.checkpoint_id && entry.available === true)) {
        throw new Error(`Checkpoint unavailable: ${draft.checkpoint_id || "none selected"}`);
    }
    if (!catalog.samplers.includes(draft.sampler_id) || !catalog.schedulers.includes(draft.scheduler_id)) {
        throw new Error("Selected sampler or scheduler is unavailable");
    }
    const values = {};
    for (const field of ["steps", "width", "height"]) {
        if (!INTEGER.test(draft[field])) throw new Error(`${field} must be a whole number`);
        const value = Number(draft[field]);
        const bound = numericBound(catalog, field);
        if (!Number.isSafeInteger(value) || value < bound.min || value > bound.max ||
            (["width", "height"].includes(field) && value % 8 !== 0)) {
            throw new Error(`${field} is outside the available bounds`);
        }
        values[field] = value;
    }
    const cfg = Number(draft.cfg);
    const cfgBound = numericBound(catalog, "cfg");
    if (draft.cfg.trim() === "" || !Number.isFinite(cfg) || cfg < cfgBound.min || cfg > cfgBound.max) {
        throw new Error("CFG is outside the available bounds");
    }
    if (values.width * values.height > Number(catalog.product_bounds.max_pixels)) {
        throw new Error("Resolution exceeds the Manga pixel limit");
    }
    const seed = draft.seed_requested;
    if (seed !== "-1" && (!INTEGER.test(seed) || Number(seed) > 4294967295)) {
        throw new Error("Seed must be -1 or 0..4294967295");
    }
    return {
        mode: "txt2img", checkpoint_id: draft.checkpoint_id, positive_raw: draft.positive_raw,
        negative_raw: draft.negative_raw, sampler_id: draft.sampler_id, scheduler_id: draft.scheduler_id,
        steps: values.steps, cfg, width: values.width, height: values.height,
        seed_requested: seed, capability_revision: catalog.revision
    };
}

export function mountGenerationView(root, { state = new GenerationState(), client = new MangaGenerationClient(),
    authoringStore = null, onEditScenes = null, pollMs = 1500 } = {}) {
    state.authoringStore = authoringStore;
    const byId = id => root.querySelector(`#${id}`);
    const controls = Object.fromEntries(FIELDS.map(field => [field, byId(`mg-${field}`)]));
    const positiveTagAutocomplete = createTagAutocomplete(controls.positive_raw);
    const generate = byId("mg-generate");
    const generateLabel = byId("mg-generate-label");
    const generateReason = byId("mg-generate-reason");
    const status = byId("mg-status");
    const error = byId("mg-error");
    const preview = byId("mg-preview-image");
    const previewEmpty = byId("mg-preview-empty");
    const previewLabel = byId("mg-preview-label");
    const history = byId("mg-history");
    const catalogNote = byId("mg-catalog-note");
    const basicModeButton = byId("mg-mode-basic");
    const sceneModeButton = byId("mg-mode-scene");
    const basicOnly = [...root.querySelectorAll("[data-mg-basic-only]")];
    const sceneOnly = [...root.querySelectorAll("[data-mg-scene-only]")];
    const sceneSummary = byId("mg-scene-summary");
    const sceneResolution = byId("mg-scene-resolution");
    const editScenes = byId("mg-edit-scenes");
    let pollTimer = null;
    let polling = false;

    function setOptions(select, entries, current) {
        select.replaceChildren();
        const known = entries.some(entry => entry.id === current);
        if (!known && current) entries = [...entries, { id: current, available: false }];
        if (!current) {
            const empty = document.createElement("option");
            empty.value = "";
            empty.textContent = "Select…";
            select.append(empty);
        }
        for (const entry of entries) {
            const option = document.createElement("option");
            option.value = entry.id;
            option.textContent = entry.available ? entry.id : `Unavailable · ${entry.id}`;
            select.append(option);
        }
        select.value = current;
    }

    function renderMode() {
        const scene = state.mode === "scene";
        basicModeButton?.setAttribute("aria-selected", String(!scene));
        sceneModeButton?.setAttribute("aria-selected", String(scene));
        for (const element of basicOnly) element.hidden = scene;
        for (const element of sceneOnly) element.hidden = !scene;
        // Scene resolution is read-only and comes from the canonical page.
        controls.width.readOnly = scene;
        controls.height.readOnly = scene;
        controls.width.disabled = false;
        controls.height.disabled = false;
        if (scene && authoringStore) {
            const page = authoringStore.getPage?.(0);
            if (page) {
                controls.width.value = String(page.width_px);
                controls.height.value = String(page.height_px);
            }
        }
        if (sceneSummary) {
            const page = authoringStore?.getPage?.(0);
            const scenes = [...(page?.scenes || [])].sort((a, b) => (Number(a.order) || 0) - (Number(b.order) || 0));
            if (!page) sceneSummary.textContent = "Authoring document unavailable.";
            else if (!scenes.length) sceneSummary.textContent = "No scenes in the Authoring document.";
            else sceneSummary.textContent = `${scenes.length} simple Scene${scenes.length === 1 ? "" : "s"} · ${page.width_px} × ${page.height_px} · ` +
                scenes.map((item, index) => `${item.name || `Scene ${index + 1}`}: ${String(item.prompt || "").trim() || "(empty prompt)"}`).join(" · ");
        }
        if (sceneResolution) {
            const page = authoringStore?.getPage?.(0);
            sceneResolution.textContent = page ? `Resolution · ${page.width_px} × ${page.height_px} (Authoring page)` : "Resolution · unavailable";
        }
    }

    function renderForm() {
        for (const field of FIELDS) {
            if (SELECTS.has(field)) continue;
            if (controls[field].value !== state.draft[field]) controls[field].value = state.draft[field];
        }
        if (state.catalog) {
            setOptions(controls.checkpoint_id, state.catalog.checkpoints, state.draft.checkpoint_id);
            setOptions(controls.sampler_id, state.catalog.samplers.map(id => ({ id, available: true })), state.draft.sampler_id);
            setOptions(controls.scheduler_id, state.catalog.schedulers.map(id => ({ id, available: true })), state.draft.scheduler_id);
            for (const field of ["steps", "cfg", "width", "height"]) {
                const bound = numericBound(state.catalog, field);
                controls[field].min = String(bound.min);
                controls[field].max = String(bound.max);
            }
            catalogNote.textContent = `Backend catalog · ${state.catalog.checkpoints.filter(entry => entry.available).length} checkpoints · ${state.catalog.samplers.length} samplers · ${state.catalog.schedulers.length} schedulers`;
        } else {
            catalogNote.textContent = state.catalogError || "Loading Manga capabilities…";
        }
        renderMode();
    }

    function renderStatus() {
        const job = state.activeJob;
        const stateName = job?.state === "RUNNING" ? "GENERATING" :
            ["VALIDATING", "SUBMITTING"].includes(job?.state) ? "SUBMITTING" : job?.state;
        status.textContent = state.historyLoading ? "Checking recorded Manga jobs…" :
            state.submitUnconfirmed ? "UNKNOWN · Job creation response unavailable" :
            state.localBusy ? "SUBMITTING · Validating settings and creating Manga job…" :
            job ? `${stateName} · Manga job ${job.job_id}` :
                state.error ? "FAILED · Manga generation could not start" :
                    state.catalog ? `READY · Ready to generate one ${state.mode === "scene" ? "Scene Layout" : "image"}` : "FAILED · Capabilities unavailable";
        status.dataset.state = state.submitUnconfirmed ? "UNKNOWN" :
            state.localBusy ? "SUBMITTING" : (stateName || (state.error ? "FAILED" : "READY"));
        const reason = generationBlockReason(state, authoringStore);
        generate.disabled = Boolean(reason);
        generateReason.textContent = reason;
        generateReason.hidden = !reason;
        generateLabel.textContent = state.mode === "scene" && !state.localBusy && !["VALIDATING", "SUBMITTING", "QUEUED", "RUNNING"].includes(job?.state)
            ? "Generate with Scenes" : state.localBusy || ["VALIDATING", "SUBMITTING"].includes(job?.state)
            ? "Submitting…" : ["QUEUED", "RUNNING"].includes(job?.state) ? "Generating…" : "Generate";
        const message = state.error || (job?.state === "FAILED" || job?.state === "UNKNOWN" ?
            `${job.state}: ${job.error?.message || "Backend outcome is not confirmed"}` : "");
        error.textContent = message;
        error.hidden = !message;
        const isPrevious = state.preview.jobId && job && state.preview.jobId !== job.job_id;
        previewLabel.textContent = state.preview.jobId ?
            (state.submitUnconfirmed ? "Previous verified result · current submission UNKNOWN" :
                isPrevious ? `Previous verified result · current job ${job.state}` : "Verified current result") :
            "No verified result yet";
        preview.hidden = !state.preview.url;
        previewEmpty.hidden = Boolean(state.preview.url);
    }

    function renderHistory() {
        history.replaceChildren();
        if (!state.jobs.length) {
            const empty = document.createElement("p");
            empty.textContent = "No Manga generation jobs in this session.";
            history.append(empty);
            return;
        }
        for (const job of state.jobs) {
            const row = document.createElement("div");
            row.className = "mg-history-row";
            row.dataset.jobId = job.job_id;
            const facts = document.createElement("div");
            const heading = document.createElement("strong");
            heading.textContent = job.state;
            const summary = document.createElement("span");
            const s = job.requested_settings || {};
            const page = s.authoring_document?.pages?.[s.page_index || 0];
            const dimensions = s.mode === "scene" ? `${page?.width_px || "?"} × ${page?.height_px || "?"}` : `${s.width || "?"} × ${s.height || "?"}`;
            summary.textContent = ` ${s.mode === "scene" ? "Scene Layout · " : ""}${s.checkpoint_id || "Unknown checkpoint"} · ${dimensions} · seed ${s.seed_requested ?? "?"}`;
            facts.append(heading, summary);
            const restore = document.createElement("button");
            restore.type = "button";
            restore.className = "mg-restore";
            restore.textContent = "Restore settings";
            restore.disabled = !job.requested_settings;
            restore.addEventListener("click", () => {
                try { state.restore(job); renderForm(); renderStatus(); }
                catch (cause) { state.error = cause.message; renderStatus(); }
            });
            row.append(facts, restore);
            history.append(row);
        }
    }

    async function showResult(job) {
        if (state.preview.jobId === job.job_id) return;
        try {
            const blob = await client.getResult(job.job_id);
            const url = URL.createObjectURL(blob);
            await new Promise((resolve, reject) => {
                const probe = new Image();
                probe.onload = resolve;
                probe.onerror = () => reject(new Error("Validated result PNG could not be displayed"));
                probe.src = url;
            }).catch(cause => { URL.revokeObjectURL(url); throw cause; });
            const old = state.preview.url;
            state.setPreview(job.job_id, url);
            preview.src = url;
            if (old) URL.revokeObjectURL(old);
            renderStatus();
        } catch (cause) {
            state.error = cause.message;
            renderStatus();
        }
    }

    function schedulePoll(jobId, delay = pollMs) {
        if (pollTimer) clearTimeout(pollTimer);
        pollTimer = setTimeout(() => poll(jobId), delay);
    }
    async function poll(jobId) {
        if (polling || state.activeJob?.job_id !== jobId) return;
        polling = true;
        try {
            const job = await client.getJob(jobId);
            if (state.activeJob?.job_id !== jobId) return;
            state.setJob(job);
            renderStatus();
            renderHistory();
            if (job.state === "SUCCEEDED") await showResult(job);
            if (ACTIVE_JOB_STATES.has(job.state)) schedulePoll(jobId);
        } catch (cause) {
            state.error = `Job observation unavailable: ${cause.message}`;
            renderStatus();
            schedulePoll(jobId);
        } finally { polling = false; }
    }

    async function generateOne() {
        if (!state.beginAttempt()) return;
        let submitStarted = false;
        renderStatus();
        try {
            const settings = state.mode === "scene"
                ? buildSceneGenerationSettings(state, authoringStore)
                : buildGenerationSettings(state);
            const compiled = state.mode === "scene"
                ? await client.compileScene(settings)
                : await client.compile(settings);
            if (compiled.capability_revision !== settings.capability_revision ||
                !own(compiled, "effective_seed")) throw new Error("Compiled capability or seed is unavailable");
            submitStarted = true;
            const job = await client.createJob(settings, compiled);
            if (!job || !JOB_ID.test(job.job_id)) throw new Error("Manga job response is invalid");
            state.setJob(job);
            renderStatus();
            renderHistory();
            if (job.state === "SUCCEEDED") await showResult(job);
            if (ACTIVE_JOB_STATES.has(job.state)) schedulePoll(job.job_id, 0);
        } catch (cause) {
            state.endAttempt();
            if (submitStarted && (!cause.status || cause.status >= 500)) {
                state.submitUnconfirmed = true;
                state.error = `Submission outcome is unknown: ${cause.message}. No automatic retry.`;
            } else {
                state.error = cause.message;
            }
            renderStatus();
        }
    }

    for (const field of FIELDS) {
        controls[field].addEventListener(SELECTS.has(field) ? "change" : "input", event => {
            state.setDraft(field, event.target.value);
            renderStatus();
        });
    }
    generate.addEventListener("click", generateOne);
    basicModeButton?.addEventListener("click", () => {
        state.setMode("basic");
        renderForm();
        renderStatus();
    });
    sceneModeButton?.addEventListener("click", () => {
        state.setMode("scene");
        renderForm();
        renderStatus();
    });
    editScenes?.addEventListener("click", () => {
        if (typeof onEditScenes === "function") onEditScenes();
    });
    authoringStore?.subscribe?.(() => {
        if (state.mode === "scene") {
            renderForm();
            renderStatus();
        }
    });
    byId("mg-refresh-catalog").addEventListener("click", async () => {
        try { state.setCatalog(await client.capabilities()); renderForm(); renderStatus(); }
        catch (cause) { state.catalog = null; state.catalogError = cause.message; renderForm(); renderStatus(); }
    });

    async function start() {
        try { state.setCatalog(await client.capabilities()); }
        catch (cause) { state.catalogError = cause.message; }
        renderForm();
        renderStatus();
        for (const jobId of [...state.jobIds].reverse()) {
            try { state.setJob(await client.getJob(jobId), false); } catch {}
        }
        if (state.jobs.length) {
            state.activeJob = state.jobs[0];
            const previousSuccess = state.jobs.find(job => job.state === "SUCCEEDED");
            if (previousSuccess) await showResult(previousSuccess);
            if (ACTIVE_JOB_STATES.has(state.activeJob.state)) schedulePoll(state.activeJob.job_id, 0);
        }
        state.historyLoading = false;
        renderStatus();
        renderHistory();
    }

    renderForm();
    renderStatus();
    renderHistory();
    const ready = start();
    return { state, client, ready, generateOne, refresh: renderStatus, tagAutocomplete: positiveTagAutocomplete, dispose() {
        if (pollTimer) clearTimeout(pollTimer);
        if (state.preview.url) URL.revokeObjectURL(state.preview.url);
        positiveTagAutocomplete.dispose();
    } };
}

export function buildSceneGenerationSettings(state, authoringStore = state.authoringStore) {
    const catalog = state.catalog;
    if (!catalog) throw new Error("Manga capabilities are unavailable");
    const document = authoringStore?.getDocument?.();
    const validation = validateAuthoringDocument(document);
    if (!validation.valid) throw new Error(`Authoring document unavailable: ${validation.errors.join("; ")}`);
    const page = document.pages[0];
    if (!Array.isArray(page.scenes) || page.scenes.length < 1 || page.scenes.length > 6) {
        throw new Error("Scene Layout requires 1–6 authoring scenes");
    }
    if ((page.cast || []).length || (page.character_instances || []).length ||
        page.scenes.some(scene => scene.input_mode && scene.input_mode !== "simple")) {
        throw new Error("Scene Layout currently supports simple Scenes only; CAST is unavailable");
    }
    if (!catalog.scene_generation?.available) throw new Error("Scene generation capability is unavailable");
    if (!catalog.checkpoints.some(entry => entry.id === state.draft.checkpoint_id && entry.available === true)) {
        throw new Error(`Checkpoint unavailable: ${state.draft.checkpoint_id || "none selected"}`);
    }
    if (!catalog.samplers.includes(state.draft.sampler_id) || !catalog.schedulers.includes(state.draft.scheduler_id)) {
        throw new Error("Selected sampler or scheduler is unavailable");
    }
    if (!INTEGER.test(state.draft.steps)) throw new Error("steps must be a whole number");
    const steps = Number(state.draft.steps);
    const stepBound = numericBound(catalog, "steps");
    if (!Number.isSafeInteger(steps) || steps < stepBound.min || steps > stepBound.max) {
        throw new Error("steps is outside the available bounds");
    }
    const cfg = Number(state.draft.cfg);
    const cfgBound = numericBound(catalog, "cfg");
    if (state.draft.cfg.trim() === "" || !Number.isFinite(cfg) || cfg < cfgBound.min || cfg > cfgBound.max) {
        throw new Error("CFG is outside the available bounds");
    }
    const width = page.width_px;
    const height = page.height_px;
    const widthBound = numericBound(catalog, "width");
    const heightBound = numericBound(catalog, "height");
    if (!Number.isInteger(width) || !Number.isInteger(height) || width < widthBound.min || width > widthBound.max ||
        height < heightBound.min || height > heightBound.max || width % 8 || height % 8) {
        throw new Error("Authoring page resolution is outside the available bounds");
    }
    if (width * height > Number(catalog.product_bounds.max_pixels)) {
        throw new Error("Authoring page resolution exceeds the Manga pixel limit");
    }
    const seed = state.draft.seed_requested;
    if (seed !== "-1" && (!INTEGER.test(seed) || Number(seed) > 4294967295)) {
        throw new Error("Seed must be -1 or 0..4294967295");
    }
    return {
        mode: "scene", checkpoint_id: state.draft.checkpoint_id,
        authoring_document: document, page_index: 0,
        sampler_id: state.draft.sampler_id, scheduler_id: state.draft.scheduler_id,
        steps, cfg, seed_requested: seed, capability_revision: catalog.revision,
        mask_feather: Number(state.sceneDraft?.mask_feather ?? 16),
        panel_strength: Number(state.sceneDraft?.panel_strength ?? 1)
    };
}
