/** PLAY1c Manga Generate view. Owns no ComfyUI routes and no authoring document data. */
import { GenerationState, ACTIVE_JOB_STATES } from "../state/generation_state.js";
import { MangaGenerationClient } from "../adapters/manga_generation_client.js";

const FIELDS = ["checkpoint_id", "positive_raw", "negative_raw", "sampler_id", "scheduler_id",
    "steps", "cfg", "width", "height", "seed_requested"];
const SELECTS = new Set(["checkpoint_id", "sampler_id", "scheduler_id"]);
const INTEGER = /^(0|[1-9][0-9]*)$/;
const JOB_ID = /^[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}$/;
const own = (obj, key) => Object.hasOwn(obj, key);

function numericBound(catalog, field) {
    const product = catalog.product_bounds?.[field];
    const backend = catalog.backend_bounds?.[field];
    return { min: Math.max(Number(product?.min), Number(backend?.min)),
        max: Math.min(Number(product?.max), Number(backend?.max)) };
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
    pollMs = 1500 } = {}) {
    const byId = id => root.querySelector(`#${id}`);
    const controls = Object.fromEntries(FIELDS.map(field => [field, byId(`mg-${field}`)]));
    const generate = byId("mg-generate");
    const status = byId("mg-status");
    const error = byId("mg-error");
    const preview = byId("mg-preview-image");
    const previewEmpty = byId("mg-preview-empty");
    const previewLabel = byId("mg-preview-label");
    const history = byId("mg-history");
    const catalogNote = byId("mg-catalog-note");
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
    }

    function renderStatus() {
        const job = state.activeJob;
        status.textContent = state.historyLoading ? "Checking recorded Manga jobs…" :
            state.submitUnconfirmed ? "UNKNOWN · Job creation response unavailable" :
            state.localBusy ? "Checking settings and creating Manga job…" :
            job ? `${job.state} · Manga job ${job.job_id}` :
                state.catalog ? "Ready to generate one image" : "Capabilities unavailable";
        status.dataset.state = state.submitUnconfirmed ? "UNKNOWN" :
            state.localBusy ? "VALIDATING" : (job?.state || "READY");
        generate.disabled = state.isBusy() || !state.catalog;
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
            summary.textContent = ` ${s.checkpoint_id || "Unknown checkpoint"} · ${s.width || "?"} × ${s.height || "?"} · seed ${s.seed_requested ?? "?"}`;
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
            const settings = buildGenerationSettings(state);
            const compiled = await client.compile(settings);
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
    return { state, client, ready, generateOne, refresh: renderStatus, dispose() {
        if (pollTimer) clearTimeout(pollTimer);
        if (state.preview.url) URL.revokeObjectURL(state.preview.url);
    } };
}
