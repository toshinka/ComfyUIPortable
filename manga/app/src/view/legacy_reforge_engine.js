/**
 * MANGA + EASYREFORGE engine glue for the existing Generate view
 * (Card MANGA-LEGACY-EASYREFORGE-VERTICAL-MVP1).
 *
 * The Unified Manga GUI is reused as-is: checkpoint browser, LoRA cards (prompt tokens), prompt,
 * negative, VAE, seed, steps, CFG, size and Generate.  Only three things are engine-aware:
 *   1. the sampler / scheduler option lists (EasyReforge exposes its own values),
 *   2. the Generate dispatch (adapter route instead of the Comfy compile/job route),
 *   3. a small runtime status row (Start / Stop / Interrupt for the Integration Runtime).
 * The recipe built here is logical (Manga IDs + raw prompt text); backend translation happens
 * server-side in LegacyReforgeAdapter.  Nothing here is persisted into the Authoring Document.
 * There is no fallback to ComfyUI.
 */

export const MANGA_ENGINES = Object.freeze(["comfyui", "easyreforge"]);
const INTEGER = /^(0|[1-9][0-9]*)$/;
const TERMINAL = new Set(["completed", "failed", "interrupted"]);

export function ensureEngineState(state) {
    state.engine ??= "comfyui";
    state.legacy ??= { status: null, samplers: [], schedulers: [], job: null, lastResult: null };
    state.engineSampling ??= { comfyui: null, easyreforge: null };
    return state;
}

export function legacyAvailable(state) {
    return Boolean(state.legacy?.status?.available);
}

/** Sampler / scheduler option lists for the current engine (null = use the Comfy catalog). */
export function engineSamplingLists(state) {
    if (state.engine !== "easyreforge") return null;
    return { samplers: state.legacy?.samplers || [], schedulers: state.legacy?.schedulers || [] };
}

function bound(catalog, field) {
    const product = catalog?.product_bounds?.[field];
    const backend = catalog?.backend_bounds?.[field];
    return { min: Math.max(Number(product?.min), Number(backend?.min)), max: Math.min(Number(product?.max), Number(backend?.max)) };
}

/** Backend-neutral recipe from the SAME controls Generate uses (Global prompt of page 0). */
export function buildLegacyReforgeRecipe(state, authoringStore = state.authoringStore) {
    ensureEngineState(state);
    const catalog = state.catalog;
    if (!catalog) throw new Error("Manga capabilities are unavailable");
    const status = state.legacy.status;
    if (!status?.available) throw new Error(`EasyReforge is unavailable${status?.installed_reason ? ` — ${status.installed_reason}` : ""}`);
    if (status.state !== "ready") throw new Error(status.state === "starting" ? "EasyReforge is starting…" : "EasyReforge is not running — press Start EasyReforge");
    const draft = state.draft;
    if (!catalog.checkpoints.some(entry => entry.id === draft.checkpoint_id && entry.available === true)) {
        throw new Error(`Checkpoint unavailable: ${draft.checkpoint_id || "none selected"}`);
    }
    if (!state.legacy.samplers.includes(draft.sampler_id)) throw new Error("Choose an EasyReforge sampler");
    if (draft.scheduler_id && !state.legacy.schedulers.includes(draft.scheduler_id)) throw new Error("Choose an EasyReforge scheduler");
    const values = {};
    for (const field of ["steps", "width", "height"]) {
        const b = bound(catalog, field);
        const value = Number(draft[field]);
        if (!INTEGER.test(draft[field]) || value < b.min || value > b.max || (field !== "steps" && value % 8 !== 0)) {
            throw new Error(`${field} is outside the available bounds`);
        }
        values[field] = value;
    }
    const cfg = Number(draft.cfg);
    const cfgBound = bound(catalog, "cfg");
    if (String(draft.cfg).trim() === "" || !Number.isFinite(cfg) || cfg < cfgBound.min || cfg > cfgBound.max) {
        throw new Error("CFG is outside the available bounds");
    }
    const seed = draft.seed_requested;
    if (seed !== "-1" && (!INTEGER.test(seed) || Number(seed) > 4294967295)) throw new Error("Seed must be -1 or 0..4294967295");
    const vae = String(draft.vae_id || "");
    if (vae && !(catalog.vaes || []).some(entry => entry?.id === vae && entry.available !== false)) throw new Error(`VAE unavailable: ${vae}`);
    const page = authoringStore?.getPage?.(0);
    if (!page) throw new Error("Global prompt page is unavailable");
    return {
        engine: "easyreforge",
        checkpoint_id: draft.checkpoint_id,
        vae_id: vae,
        positive_raw: typeof page.style_prompt === "string" ? page.style_prompt : "",
        negative_raw: typeof page.style_negative_prompt === "string" ? page.style_negative_prompt : "",
        sampler: draft.sampler_id,
        scheduler: draft.scheduler_id || "",
        steps: values.steps, cfg, width: values.width, height: values.height,
        seed_requested: seed,
    };
}

export function legacyReforgeBlockReason(state, authoringStore, source) {
    if (source === "scenes") return "Scenes generation is ComfyUI-only; EasyReforge generates the Global prompt.";
    if (state.legacy?.job && !TERMINAL.has(state.legacy.job.state)) return "EasyReforge job is running…";
    try { buildLegacyReforgeRecipe(state, authoringStore); } catch (cause) { return cause.message; }
    return "";
}

/**
 * Wire the engine into a mounted Generate view.
 * hooks: { render(), showBlob(jobId, blob), onAvailability(status) }
 */
export function createLegacyReforgeEngine({ state, client, authoringStore = null, anchor = null, doc = globalThis.document,
    hooks = {}, pollMs = 1500, statusPollMs = 3000, sleep = ms => new Promise(r => setTimeout(r, ms)) } = {}) {
    ensureEngineState(state);
    const render = () => hooks.render?.();
    let statusTimer = null;
    let disposed = false;

    // --- small status row (Integration Runtime ownership), shown only for EASYREFORGE -------
    const row = doc?.createElement ? doc.createElement("div") : null;
    const text = row ? doc.createElement("span") : null;
    const startBtn = row ? doc.createElement("button") : null;
    const stopBtn = row ? doc.createElement("button") : null;
    const interruptBtn = row ? doc.createElement("button") : null;
    if (row) {
        row.className = "mg-legacy-reforge";
        row.hidden = true;
        row.setAttribute("role", "status");
        text.className = "mg-legacy-reforge-text";
        for (const [button, label] of [[startBtn, "Start EasyReforge"], [stopBtn, "Stop"], [interruptBtn, "Interrupt"]]) {
            button.type = "button";
            button.textContent = label;
        }
        row.append(text, startBtn, stopBtn, interruptBtn);
        anchor?.insertAdjacentElement?.("afterend", row);
        startBtn.addEventListener("click", () => act(() => client.legacyStart()));
        stopBtn.addEventListener("click", () => act(() => client.legacyStop()));
        interruptBtn.addEventListener("click", () => {
            const job = state.legacy.job;
            if (job && !TERMINAL.has(job.state)) act(() => client.legacyInterrupt(job.job_id).then(updated => { state.legacy.job = updated; }));
        });
    }

    function renderRow() {
        if (!row) return;
        row.hidden = state.engine !== "easyreforge";
        const s = state.legacy.status;
        const job = state.legacy.job;
        const running = job && !TERMINAL.has(job.state);
        text.textContent = !s ? "EasyReforge · checking…" :
            !s.available ? `EasyReforge · unavailable — ${s.installed_reason || "Integration Runtime not found"}` :
            `EasyReforge · ${s.state.toUpperCase()}${s.state === "ready" ? ` · port ${s.port}` : ""}` +
            (s.error ? ` · ${s.error.message}` : "") + (running ? ` · job ${job.state}` : "");
        row.dataset.state = s?.state || "unknown";
        startBtn.disabled = !s?.available || ["starting", "ready", "stopping"].includes(s?.state);
        stopBtn.disabled = !s?.owned || Boolean(running);
        interruptBtn.disabled = !running;
    }

    async function refreshStatus() {
        try {
            const status = await client.legacyStatus();
            const wasReady = state.legacy.status?.state === "ready";
            state.legacy.status = status;
            if (status.state === "ready" && (!wasReady || !state.legacy.samplers.length)) {
                const caps = await client.legacyCapabilities();
                state.legacy.samplers = Array.isArray(caps.samplers) ? caps.samplers : [];
                state.legacy.schedulers = Array.isArray(caps.schedulers) ? caps.schedulers : [];
            }
            if (status.state !== "ready") { state.legacy.samplers = []; state.legacy.schedulers = []; }
        } catch (cause) {
            state.legacy.status = { available: false, installed_reason: cause.message, state: "unknown" };
        }
        hooks.onAvailability?.(state.legacy.status);
        renderRow();
        render();
        return state.legacy.status;
    }

    function schedule() {
        clearTimeout(statusTimer);
        if (disposed) return;
        const s = state.legacy.status;
        if (state.engine === "easyreforge" || s?.state === "starting") statusTimer = setTimeout(async () => { await refreshStatus(); schedule(); }, statusPollMs);
    }

    async function act(fn) {
        try { await fn(); state.error = ""; }
        catch (cause) { state.error = cause.message; }
        await refreshStatus();
        schedule();
    }

    /** Switch engine.  EASYREFORGE only when the backend reports the Integration Runtime available. */
    function setEngine(engine) {
        if (!MANGA_ENGINES.includes(engine)) return false;
        if (engine === "easyreforge" && !legacyAvailable(state)) return false;
        if (engine === state.engine) { renderRow(); return true; }
        // Each engine keeps its own sampler/scheduler choice; values never cross-map silently.
        state.engineSampling[state.engine] = { sampler_id: state.draft.sampler_id, scheduler_id: state.draft.scheduler_id };
        const restored = state.engineSampling[engine] || { sampler_id: "", scheduler_id: "" };
        state.engine = engine;
        state.draft.sampler_id = restored.sampler_id;
        state.draft.scheduler_id = restored.scheduler_id;
        state.error = "";
        renderRow();
        render();
        refreshStatus().then(schedule);
        return true;
    }

    async function generate() {
        if (!state.beginAttempt()) return null;
        render();
        let job = null;
        try {
            const recipe = buildLegacyReforgeRecipe(state, authoringStore);
            job = await client.legacyGenerate(recipe);
            state.legacy.job = job;
            renderRow();
            while (!TERMINAL.has(job.state)) {
                await sleep(pollMs);
                job = await client.legacyJob(job.job_id);
                state.legacy.job = job;
                renderRow();
            }
            if (job.state !== "completed") throw new Error(`${job.state.toUpperCase()}: ${job.error?.message || "EasyReforge generation did not complete"}`);
            const blob = await client.legacyResult(job.job_id);
            state.legacy.lastResult = job.result;
            await hooks.showBlob?.(job.job_id, blob);
            return job;
        } catch (cause) {
            state.error = `EasyReforge: ${cause.message}`;
            return null;
        } finally {
            state.endAttempt();
            renderRow();
            render();
        }
    }

    return { setEngine, generate, refreshStatus, renderRow, get engine() { return state.engine; },
        dispose() { disposed = true; clearTimeout(statusTimer); } };
}
