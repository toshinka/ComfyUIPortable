/**
 * Experiment / Output panel (Card MANGA-EXPERIMENT-OUTPUT-PRODUCTION1).
 *
 * Session/application state only.  The Authoring Document is read (through the Generation
 * view's own Global settings builder) and never written.  Every experiment cell is a derived
 * copy compiled through the existing compile route and submitted through the existing job route;
 * there is no second generation engine.  Validate is compile-only (no /prompt, no GPU); Run
 * requires an explicit two-step confirmation.
 */
import {
    AXIS_KEYS, AXIS_LABELS, AXIS_TYPES, EXPERIMENT_MAX_CELLS, PRESET_STATUS,
    cellCaption, cellFragment, classifyPresets, deriveCellSettings, expandExperiment,
    firstLoraFromResolved, gridGeometry, planGridPages, presetChanges, stemOf
} from "../domain/experiment_plan.js";

export const OUTPUT_PREFS_KEY = "tegaki.manga.output_naming.v1";
const DEFAULT_TEMPLATE = "{checkpoint}_{first_lora}_{suffix}_{seed}";
const ACTIVE = new Set(["VALIDATING", "SUBMITTING", "QUEUED", "RUNNING", "UNKNOWN"]);

export function readOutputPrefs(storage) {
    const fallback = { template: DEFAULT_TEMPLATE, suffix: "", autoNamed: false, experimentNamed: true, labels: true };
    try {
        const raw = storage?.getItem(OUTPUT_PREFS_KEY);
        const parsed = raw ? JSON.parse(raw) : null;
        if (!parsed || typeof parsed !== "object") return fallback;
        return {
            template: typeof parsed.template === "string" && parsed.template.trim() ? parsed.template : fallback.template,
            suffix: typeof parsed.suffix === "string" ? parsed.suffix : "",
            autoNamed: parsed.autoNamed === true,
            experimentNamed: parsed.experimentNamed !== false,
            labels: parsed.labels !== false,
        };
    } catch { return fallback; }
}

function writeOutputPrefs(storage, prefs) {
    try { storage?.setItem(OUTPUT_PREFS_KEY, JSON.stringify(prefs)); return true; } catch { return false; }
}

async function postJson(fetchFn, url, body) {
    let response;
    try {
        response = await fetchFn(url, { method: "POST", cache: "no-store", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
    } catch { throw new Error("Manga workspace is unavailable"); }
    let data = null;
    try { data = await response.json(); } catch {}
    if (!response.ok || data?.ok !== true) throw new Error(data?.error || `Request failed (HTTP ${response.status})`);
    return data;
}

/** Fixed, parameterless output-folder action.  Never sends a path. */
export function mountOutputFolderButton(button, statusEl, { fetchFn = (...a) => fetch(...a) } = {}) {
    if (!button) return null;
    let timer = null;
    const show = (text, state) => {
        if (!statusEl) return;
        statusEl.textContent = text;
        statusEl.dataset.state = state;
        statusEl.hidden = !text;
        clearTimeout(timer);
        timer = setTimeout(() => { statusEl.hidden = true; statusEl.textContent = ""; }, state === "error" ? 6000 : 2500);
    };
    const open = async () => {
        button.disabled = true;
        try {
            const data = await postJson(fetchFn, "/api/manga/output/open-folder", {});
            show(`Opened output folder (${data.folder})`, "ok");
            return data;
        } catch (cause) {
            show(`Output folder unavailable: ${cause.message}`, "error");
            return null;
        } finally { button.disabled = false; }
    };
    button.addEventListener("click", open);
    return { open };
}

const el = (tag, props = {}, ...children) => {
    const node = document.createElement(tag);
    for (const [key, value] of Object.entries(props)) {
        if (key === "class") node.className = value;
        else if (key === "text") node.textContent = value;
        else if (key.includes("-")) node.setAttribute(key, value);
        else node[key] = value;
    }
    for (const child of children) if (child != null) node.append(child);
    return node;
};

export function mountExperimentPanel(root, { generation, client, authoringStore = null,
    fetchFn = (...a) => fetch(...a), storage = (() => { try { return globalThis.localStorage; } catch { return null; } })(),
    pollMs = 1500, sleep = ms => new Promise(r => setTimeout(r, ms)) } = {}) {
    const prefs = readOutputPrefs(storage);
    const definition = { x: { type: "none" }, y: { type: "none" }, z: { type: "none" } };
    let plan = null;
    let validated = null;       // { signature, cells: [...] }
    let run = null;             // { plan, cells: [{ index, status, job_id, url, size, error, named, checkpoint }] }
    let stopRequested = false;
    let confirmTimer = null;
    let previewSeq = 0;
    let previewTimer = null;
    let grids = [];

    root.replaceChildren();
    // ---- A. Sampler preset --------------------------------------------------------------
    const presetSelect = el("select", { id: "mg-xo-preset", "aria-label": "Sampler preset" });
    const presetApply = el("button", { type: "button", id: "mg-xo-preset-apply", text: "Apply" });
    const presetStatus = el("p", { id: "mg-xo-preset-status", class: "mg-hint mg-xo-status" });
    // ---- B. Output naming ---------------------------------------------------------------
    const template = el("input", { id: "mg-xo-template", type: "text", value: prefs.template, spellcheck: false,
        "aria-label": "Filename template" });
    const suffix = el("input", { id: "mg-xo-suffix", type: "text", value: prefs.suffix, placeholder: "ANIME / MANGA",
        "aria-label": "Filename suffix" });
    const autoNamed = el("input", { id: "mg-xo-auto-named", type: "checkbox", checked: prefs.autoNamed });
    const namePreview = el("p", { id: "mg-xo-name-preview", class: "mg-xo-name-preview", text: "…" });
    const nameNote = el("p", { id: "mg-xo-name-note", class: "mg-hint mg-xo-status" });
    // ---- C. Experiment -------------------------------------------------------------------
    const axisRows = {};
    const counts = el("p", { id: "mg-xo-counts", class: "mg-xo-counts" });
    const blocked = el("p", { id: "mg-xo-blocked", class: "mg-disabled-reason", role: "note" });
    const srPreview = el("ol", { id: "mg-xo-sr-preview", class: "mg-xo-sr-preview" });
    const validateBtn = el("button", { type: "button", id: "mg-xo-validate", text: "Validate (compile only)" });
    const runBtn = el("button", { type: "button", id: "mg-xo-run", text: "Run", disabled: true });
    const stopBtn = el("button", { type: "button", id: "mg-xo-stop", text: "Stop remaining", disabled: true });
    const experimentNamed = el("input", { id: "mg-xo-exp-named", type: "checkbox", checked: prefs.experimentNamed });
    const runStatus = el("p", { id: "mg-xo-run-status", class: "mg-hint mg-xo-status", role: "status" });
    const cellsList = el("ol", { id: "mg-xo-cells", class: "mg-xo-cells" });
    const labels = el("input", { id: "mg-xo-grid-labels", type: "checkbox", checked: prefs.labels });
    const gridBtn = el("button", { type: "button", id: "mg-xo-grid-build", text: "Build grid", disabled: true });
    const gridSave = el("button", { type: "button", id: "mg-xo-grid-save", text: "Save grid", disabled: true });
    const gridStatus = el("p", { id: "mg-xo-grid-status", class: "mg-hint mg-xo-status" });
    const gridView = el("div", { id: "mg-xo-grid-view", class: "mg-xo-grid-view" });

    root.append(
        el("div", { class: "mg-xo-block" }, el("div", { class: "mg-xo-heading", text: "Sampler preset" }),
            el("div", { class: "mg-xo-row" }, presetSelect, presetApply), presetStatus),
        el("div", { class: "mg-xo-block" }, el("div", { class: "mg-xo-heading", text: "Output filename" }),
            el("label", { class: "mg-xo-field" }, el("span", { text: "Template" }), template),
            el("p", { class: "mg-hint", text: "Tokens: {checkpoint} {first_lora} {suffix} {seed} {index} {axis} {date} {time}" }),
            el("label", { class: "mg-xo-field" }, el("span", { text: "Suffix" }), suffix),
            el("label", { class: "mg-xo-check" }, autoNamed, el("span", { text: "Save a named copy after Generate (Manga/Named)" })),
            namePreview, nameNote),
        el("div", { class: "mg-xo-block" }, el("div", { class: "mg-xo-heading", text: `X/Y/Z experiment · max ${EXPERIMENT_MAX_CELLS} cells` }),
            ...AXIS_KEYS.map(key => buildAxisRow(key)),
            counts, blocked, srPreview,
            el("label", { class: "mg-xo-check" }, experimentNamed, el("span", { text: "Save named copies of experiment cells" })),
            el("div", { class: "mg-xo-row" }, validateBtn, runBtn, stopBtn), runStatus, cellsList,
            el("div", { class: "mg-xo-row" }, el("label", { class: "mg-xo-check" }, labels, el("span", { text: "Labels" })), gridBtn, gridSave),
            gridStatus, gridView)
    );

    function buildAxisRow(key) {
        const type = el("select", { id: `mg-xo-${key}-type`, "aria-label": `${key.toUpperCase()} axis type` });
        for (const t of AXIS_TYPES) type.append(el("option", { value: t, text: AXIS_LABELS[t] }));
        const multi = el("select", { id: `mg-xo-${key}-values`, multiple: true, size: 5, hidden: true, "aria-label": `${key.toUpperCase()} axis values` });
        const text = el("input", { id: `mg-xo-${key}-text`, type: "text", hidden: true, placeholder: "e.g. 20, 28, 36", "aria-label": `${key.toUpperCase()} axis values` });
        const search = el("input", { id: `mg-xo-${key}-search`, type: "text", hidden: true, placeholder: "Search (literal)", "aria-label": `${key.toUpperCase()} S/R search` });
        const replacements = el("textarea", { id: `mg-xo-${key}-replace`, rows: 3, hidden: true,
            placeholder: "One replacement per line", "aria-label": `${key.toUpperCase()} S/R replacements` });
        const row = el("div", { class: "mg-xo-axis", "data-axis": key },
            el("span", { class: "mg-xo-axis-key", text: key.toUpperCase() }), type,
            el("div", { class: "mg-xo-axis-values" }, multi, text, search, replacements));
        axisRows[key] = { type, multi, text, search, replacements };
        type.addEventListener("change", () => { fillAxisOptions(key); syncAxis(key); });
        for (const input of [multi, text, search, replacements]) {
            input.addEventListener(input === multi ? "change" : "input", () => syncAxis(key));
        }
        return row;
    }

    function fillAxisOptions(key) {
        const row = axisRows[key];
        const t = row.type.value;
        const catalog = generation.state.catalog;
        row.multi.hidden = !["checkpoint", "sampler", "scheduler"].includes(t);
        row.text.hidden = !["steps", "cfg", "seed"].includes(t);
        row.search.hidden = row.replacements.hidden = t !== "prompt_sr";
        row.text.placeholder = t === "seed" ? "e.g. 1, 2, -1" : t === "cfg" ? "e.g. 4, 5.5, 7" : "e.g. 20, 28, 36";
        if (!row.multi.hidden) {
            const entries = t === "checkpoint"
                ? (catalog?.checkpoints || []).filter(entry => entry.available).map(entry => ({ id: entry.id, label: stemOf(entry.id) }))
                : (catalog?.[t === "sampler" ? "samplers" : "schedulers"] || []).map(id => ({ id, label: id }));
            const selected = new Set(definition[key].values || []);
            row.multi.replaceChildren(...entries.map(entry => el("option", { value: entry.id, text: entry.label, title: entry.id, selected: selected.has(entry.id) })));
        }
    }

    function syncAxis(key) {
        const row = axisRows[key];
        definition[key] = {
            type: row.type.value,
            values: [...row.multi.selectedOptions].map(option => option.value),
            text: row.text.value, search: row.search.value, replacements: row.replacements.value,
        };
        invalidate();
    }

    function baseSettings() {
        try { return { ok: true, settings: generation.getGlobalBaseSettings() }; }
        catch (cause) { return { ok: false, error: cause.message }; }
    }

    function signature() {
        const base = baseSettings();
        return JSON.stringify({ definition, base: base.ok ? base.settings : base.error });
    }

    function invalidate() {
        plan = expandExperiment(definition, generation.state.catalog);
        validated = null;
        renderPlan();
    }

    function renderPlan() {
        const p = plan || expandExperiment(definition, generation.state.catalog);
        counts.textContent = `X ${p.counts.x} × Y ${p.counts.y} × Z ${p.counts.z} = TOTAL ${p.total}`;
        counts.dataset.over = String(p.total > EXPERIMENT_MAX_CELLS);
        blocked.textContent = p.blocked;
        blocked.hidden = !p.blocked;
        srPreview.replaceChildren();
        const hasSr = p.axes.some(axis => axis.enabled && axis.type === "prompt_sr");
        if (!p.blocked && hasSr) {
            const base = baseSettings();
            for (const cell of p.cells.slice(0, 8)) {
                const derived = base.ok ? deriveCellSettings(base.settings, cell) : { ok: false, error: base.error };
                srPreview.append(el("li", { class: derived.ok ? "" : "is-error",
                    text: derived.ok ? `#${cell.index + 1} ${derived.settings.positive_raw}` : `#${cell.index + 1} ${derived.error}` }));
            }
            if (p.cells.length > 8) srPreview.append(el("li", { text: `… ${p.cells.length - 8} more` }));
        }
        srPreview.hidden = !srPreview.childElementCount;
        validateBtn.disabled = Boolean(p.blocked) || Boolean(run?.running);
        renderRunButton();
    }

    function renderRunButton() {
        const ready = validated && validated.signature === signature() && validated.cells.every(cell => cell.ok) && !run?.running;
        runBtn.disabled = !ready;
        if (!confirmTimer) runBtn.textContent = ready ? `Run ${validated.cells.length} cells (GPU)` : "Run";
        stopBtn.disabled = !run?.running;
    }

    // ---- Presets -------------------------------------------------------------------------
    function renderPresets() {
        const classified = classifyPresets(generation.state.catalog);
        const current = presetSelect.value;
        presetSelect.replaceChildren(el("option", { value: "", text: "Choose preset…" }));
        for (const group of ["Normal", "Research", "Special"]) {
            const optgroup = el("optgroup", { label: group });
            for (const item of classified.filter(entry => entry.group === group)) {
                optgroup.append(el("option", { value: item.id, disabled: item.status === PRESET_STATUS.UNAVAILABLE,
                    text: `${item.label} · ${item.status === PRESET_STATUS.SUPPORTED ? "supported" : item.status === PRESET_STATUS.PARTIAL ? "partial" : "unavailable"}`,
                    "data-status": item.status }));
            }
            presetSelect.append(optgroup);
        }
        presetSelect.value = classified.some(item => item.id === current && item.status !== PRESET_STATUS.UNAVAILABLE) ? current : "";
        renderPresetStatus();
        return classified;
    }

    function selectedPreset() {
        return classifyPresets(generation.state.catalog).find(item => item.id === presetSelect.value) || null;
    }

    function renderPresetStatus(message = "") {
        const item = selectedPreset();
        presetApply.disabled = !item || item.status === PRESET_STATUS.UNAVAILABLE;
        presetApply.textContent = item?.status === PRESET_STATUS.PARTIAL ? "Apply available part only" : "Apply";
        presetStatus.dataset.status = item?.status || "";
        presetStatus.textContent = message || (!item ? "Presets are checked against the live runtime catalog." :
            item.status === PRESET_STATUS.SUPPORTED ? `Sets ${item.parts.map(part => part.id).join(" + ")}` :
            `${item.status}: ${item.reason}. The missing part is never substituted.`);
    }

    presetSelect.addEventListener("change", () => renderPresetStatus());
    presetApply.addEventListener("click", () => {
        const item = selectedPreset();
        if (!item) return;
        const result = presetChanges(item, { allowPartial: true });
        if (!result.ok) { renderPresetStatus(result.reason); return; }
        try {
            const applied = generation.applySampling(result.changes);
            const text = Object.entries(applied).map(([field, id]) => `${field === "sampler_id" ? "Sampler" : "Scheduler"} → ${id}`).join(", ");
            renderPresetStatus(result.partial
                ? `Applied only: ${text}. Unavailable and unchanged: ${result.missing.join(", ")}.`
                : `Applied: ${text}.`);
            invalidate();
            schedulePreview();
        } catch (cause) { renderPresetStatus(`Preset not applied: ${cause.message}`); }
    });

    // ---- Output naming ------------------------------------------------------------------
    function savePrefs() {
        Object.assign(prefs, { template: template.value, suffix: suffix.value, autoNamed: autoNamed.checked,
            experimentNamed: experimentNamed.checked, labels: labels.checked });
        if (!writeOutputPrefs(storage, prefs)) nameNote.textContent = "Naming preferences could not be saved in this browser.";
    }

    function namingBody(extra = {}) {
        return { template: template.value, suffix: suffix.value, ...extra };
    }

    async function refreshNamePreview() {
        const token = ++previewSeq;
        const draft = generation.state.draft || {};
        const values = { checkpoint_id: draft.checkpoint_id || "", first_lora: "", seed: draft.seed_requested ?? "" };
        let note = "";
        const base = baseSettings();
        if (base.ok) {
            try {
                const compiled = await client.compile(base.settings);
                values.checkpoint_id = base.settings.checkpoint_id;
                values.first_lora = firstLoraFromResolved(compiled.resolved_loras);
                values.seed = String(compiled.effective_seed);
                if (base.settings.seed_requested === "-1") note = "Seed -1: sample random seed shown; the file uses the job's effective seed.";
            } catch (cause) { note = `first_lora unresolved (compile: ${cause.message})`; }
        } else note = `first_lora unresolved: ${base.error}`;
        if (token !== previewSeq) return null;
        try {
            const data = await postJson(fetchFn, "/api/manga/output/filename-preview", namingBody(values));
            if (token !== previewSeq) return null;
            namePreview.textContent = `${data.folder}/${data.filename}`;
            namePreview.dataset.state = "ok";
            nameNote.textContent = note;
            return data;
        } catch (cause) {
            if (token !== previewSeq) return null;
            namePreview.textContent = `Invalid: ${cause.message}`;
            namePreview.dataset.state = "error";
            nameNote.textContent = note;
            return null;
        }
    }

    function schedulePreview() {
        clearTimeout(previewTimer);
        previewTimer = setTimeout(refreshNamePreview, 300);
    }

    for (const input of [template, suffix]) input.addEventListener("input", () => { savePrefs(); schedulePreview(); invalidate(); });
    for (const input of [autoNamed, experimentNamed, labels]) input.addEventListener("change", savePrefs);

    /** Named copy for a job the normal Generate button just completed (opt-in). */
    async function namedCopyForGenerate(job) {
        if (!autoNamed.checked) return null;
        try {
            const data = await postJson(fetchFn, "/api/manga/output/named-copy", namingBody({ job_id: job.job_id }));
            nameNote.textContent = `Saved ${data.folder}/${data.filename}`;
            return data;
        } catch (cause) {
            nameNote.textContent = `Named copy failed: ${cause.message}`;
            return null;
        }
    }

    // ---- Validate (compile-only) --------------------------------------------------------
    async function validate() {
        invalidate();
        if (plan.blocked) return null;
        const base = baseSettings();
        if (!base.ok) { blocked.textContent = `Base settings: ${base.error}`; blocked.hidden = false; return null; }
        const sig = signature();
        validateBtn.disabled = true;
        runStatus.textContent = `Validating ${plan.cells.length} cells (compile only, no GPU)…`;
        const cells = [];
        for (const cell of plan.cells) {
            const entry = { index: cell.index, caption: cellCaption(cell), ok: false, error: "", filename: "" };
            const derived = deriveCellSettings(base.settings, cell);
            if (!derived.ok) entry.error = derived.error;
            else {
                try {
                    const compiled = await client.compile(derived.settings);
                    const name = await postJson(fetchFn, "/api/manga/output/filename-preview", namingBody({
                        checkpoint_id: derived.settings.checkpoint_id, first_lora: firstLoraFromResolved(compiled.resolved_loras),
                        seed: String(compiled.effective_seed), index: cell.index + 1, axis: cellFragment(cell) }));
                    Object.assign(entry, { ok: true, filename: name.filename, checkpoint: stemOf(derived.settings.checkpoint_id) });
                } catch (cause) { entry.error = cause.message; }
            }
            cells.push(entry);
        }
        validated = { signature: sig, cells, plan };
        const bad = cells.filter(cell => !cell.ok).length;
        runStatus.textContent = bad ? `${bad} of ${cells.length} cells failed validation; Run is blocked.` : `${cells.length} cells validated (compile only).`;
        renderCells(cells.map(cell => ({ ...cell, status: cell.ok ? "VALID" : "INVALID" })));
        validateBtn.disabled = false;
        renderRunButton();
        return validated;
    }

    function renderCells(entries) {
        cellsList.replaceChildren(...entries.map(entry => el("li", { "data-status": entry.status,
            text: `#${entry.index + 1} ${entry.status} · ${entry.caption}${entry.filename ? ` · ${entry.filename}` : ""}${entry.error ? ` · ${entry.error}` : ""}` })));
    }

    // ---- Run (explicit two-step confirmation; real GPU jobs) -----------------------------
    runBtn.addEventListener("click", () => {
        if (runBtn.disabled) return;
        if (!confirmTimer) {
            runBtn.textContent = `Confirm: queue ${validated.cells.length} GPU jobs`;
            runBtn.dataset.confirm = "true";
            confirmTimer = setTimeout(() => { confirmTimer = null; delete runBtn.dataset.confirm; renderRunButton(); }, 6000);
            return;
        }
        clearTimeout(confirmTimer); confirmTimer = null; delete runBtn.dataset.confirm;
        execute();
    });
    stopBtn.addEventListener("click", () => { stopRequested = true; runStatus.textContent = "Stopping after the current cell (running jobs are not cancelled)…"; });

    async function waitForTerminal(job) {
        let current = job;
        while (ACTIVE.has(current.state)) {
            await sleep(pollMs);
            current = await client.getJob(current.job_id);
        }
        return current;
    }

    async function execute() {
        const base = baseSettings();
        if (!base.ok || !validated || validated.signature !== signature()) { renderRunButton(); return null; }
        const busy = generation.state.localBusy || (generation.state.activeJob && ACTIVE.has(generation.state.activeJob.state));
        if (busy) { runStatus.textContent = "A Manga job is already active; wait for it to finish."; return null; }
        const runPlan = validated.plan;
        run = { running: true, plan: runPlan, cells: runPlan.cells.map(cell => ({ index: cell.index, caption: cellCaption(cell), status: "PENDING" })) };
        stopRequested = false;
        renderRunButton();
        for (const cell of runPlan.cells) {
            const entry = run.cells[cell.index];
            if (stopRequested) { entry.status = "NOT RUN"; continue; }
            entry.status = "RUNNING";
            renderCells(run.cells);
            runStatus.textContent = `Cell ${cell.index + 1} of ${runPlan.cells.length}…`;
            try {
                const derived = deriveCellSettings(base.settings, cell);
                if (!derived.ok) throw new Error(derived.error);
                entry.checkpoint = stemOf(derived.settings.checkpoint_id);
                const compiled = await client.compile(derived.settings);
                let job = await client.createJob(derived.settings, compiled);
                entry.job_id = job.job_id;
                job = await waitForTerminal(job);
                if (job.state !== "SUCCEEDED") throw new Error(`${job.state}: ${job.error?.message || "job did not succeed"}`);
                const blob = await client.getResult(job.job_id);
                entry.blob = blob;
                entry.status = "SUCCEEDED";
                if (experimentNamed.checked) {
                    try {
                        const named = await postJson(fetchFn, "/api/manga/output/named-copy",
                            namingBody({ job_id: job.job_id, index: cell.index + 1, axis: cellFragment(cell) }));
                        entry.filename = named.filename;
                    } catch (cause) { entry.error = `named copy failed: ${cause.message}`; }
                }
            } catch (cause) {
                entry.status = "FAILED";
                entry.error = cause.message;
                if (["OWNED_JOB_BUSY", "FOREIGN_QUEUE_BUSY"].includes(cause.code)) stopRequested = true;
            }
            renderCells(run.cells);
        }
        run.running = false;
        const ok = run.cells.filter(cell => cell.status === "SUCCEEDED").length;
        runStatus.textContent = `Experiment finished: ${ok} succeeded, ${run.cells.length - ok} failed/not run.`;
        gridBtn.disabled = ok === 0;
        renderRunButton();
        return run;
    }

    // ---- Grid ---------------------------------------------------------------------------
    async function decode(blob) {
        const url = URL.createObjectURL(blob);
        try {
            const image = new Image();
            await new Promise((resolve, reject) => { image.onload = resolve; image.onerror = () => reject(new Error("image decode failed")); image.src = url; });
            return { image, width: image.naturalWidth, height: image.naturalHeight };
        } finally { setTimeout(() => URL.revokeObjectURL(url), 0); }
    }

    /** Compose Grid canvases from a plan and per-index results ({status, blob, checkpoint}). */
    async function composeGrids(gridPlan, results, { labels: withLabels = labels.checked } = {}) {
        const decoded = new Map();
        for (const result of results) {
            if (result?.status === "SUCCEEDED" && result.blob) {
                try { decoded.set(result.index, await decode(result.blob)); } catch { /* shown as failed slot */ }
            }
        }
        const sizes = new Map([...decoded].map(([index, d]) => [index, { width: d.width, height: d.height }]));
        const cellsByIndex = new Map(gridPlan.cells.map(cell => [cell.index, cell]));
        const resultByIndex = new Map(results.map(result => [result.index, result]));
        const pages = [];
        for (const page of planGridPages(gridPlan)) {
            const geo = gridGeometry(page, sizes, { labels: withLabels });
            const canvas = document.createElement("canvas");
            canvas.width = geo.outWidth;
            canvas.height = geo.outHeight;
            const ctx = canvas.getContext("2d");
            ctx.setTransform(geo.scale, 0, 0, geo.scale, 0, 0);
            ctx.fillStyle = "#ffffee";
            ctx.fillRect(0, 0, geo.width, geo.height);
            ctx.textBaseline = "middle";
            if (geo.titleH) {
                ctx.fillStyle = "#800000";
                ctx.font = "bold 22px sans-serif";
                ctx.fillText(page.title.slice(0, 80), 8, geo.titleH / 2, geo.width - 16);
            }
            for (const slot of geo.slots) {
                const d = decoded.get(slot.index);
                const result = resultByIndex.get(slot.index);
                if (slot.caption) {
                    ctx.fillStyle = "#f0e0d6";
                    ctx.fillRect(slot.caption.x, slot.caption.y, slot.caption.w, slot.caption.h);
                    ctx.fillStyle = "#800000";
                    ctx.font = "16px sans-serif";
                    const cell = cellsByIndex.get(slot.index);
                    const text = `#${slot.index + 1} ${result?.checkpoint || ""} · ${cell ? cellCaption(cell, { max: 32 }) : ""}`;
                    ctx.fillText(text.slice(0, 120), slot.caption.x + 6, slot.caption.y + slot.caption.h / 2, slot.caption.w - 12);
                }
                if (d && slot.image) ctx.drawImage(d.image, slot.image.x, slot.image.y, slot.image.w, slot.image.h);
                else {
                    const top = slot.y + (slot.caption?.h || 0);
                    ctx.fillStyle = "#dddddd";
                    ctx.fillRect(slot.x, top, geo.cellW, geo.cellH);
                    ctx.fillStyle = "#666666";
                    ctx.font = "bold 20px sans-serif";
                    ctx.fillText(`#${slot.index + 1} ${result?.status === "NOT RUN" ? "NOT RUN" : "FAILED"}`, slot.x + 12, top + geo.cellH / 2, geo.cellW - 24);
                }
            }
            pages.push({ canvas, geometry: geo, page });
        }
        return pages;
    }

    gridBtn.addEventListener("click", async () => {
        if (!run) return;
        gridBtn.disabled = true;
        try {
            grids = await composeGrids(run.plan, run.cells);
            gridView.replaceChildren(...grids.map(g => { g.canvas.className = "mg-xo-grid-canvas"; return g.canvas; }));
            gridStatus.textContent = `${grids.length} grid${grids.length === 1 ? "" : "s"} · ${grids.map(g => `${g.canvas.width}×${g.canvas.height}`).join(", ")}`;
            gridSave.disabled = !grids.length;
        } catch (cause) { gridStatus.textContent = `Grid failed: ${cause.message}`; }
        finally { gridBtn.disabled = false; }
    });

    async function saveGrids() {
        const saved = [];
        for (const [i, grid] of grids.entries()) {
            const blob = await new Promise(resolve => grid.canvas.toBlob(resolve, "image/png"));
            const label = `${suffix.value || "experiment"}${grids.length > 1 ? `_z${i + 1}` : ""}`;
            const response = await fetchFn(`/api/manga/output/grid?label=${encodeURIComponent(label)}`,
                { method: "POST", headers: { "Content-Type": "image/png" }, body: blob });
            const data = await response.json().catch(() => null);
            if (!response.ok || data?.ok !== true) throw new Error(data?.error || `HTTP ${response.status}`);
            saved.push(`${data.folder}/${data.filename}`);
        }
        return saved;
    }
    gridSave.addEventListener("click", async () => {
        gridSave.disabled = true;
        try { gridStatus.textContent = `Saved ${(await saveGrids()).join(", ")}`; }
        catch (cause) { gridStatus.textContent = `Grid save failed: ${cause.message}`; }
        finally { gridSave.disabled = !grids.length; }
    });

    validateBtn.addEventListener("click", validate);

    function refreshCatalog() {
        renderPresets();
        for (const key of AXIS_KEYS) fillAxisOptions(key);
        invalidate();
        schedulePreview();
    }
    // Prompt / control edits invalidate validation and refresh the filename preview.
    authoringStore?.subscribe?.(() => { invalidate(); if (root.closest?.("details")?.open !== false) schedulePreview(); });
    document.addEventListener("change", event => {
        if (event.target?.matches?.("#mg-checkpoint_id, #mg-sampler_id, #mg-scheduler_id")) { invalidate(); schedulePreview(); }
    });
    document.addEventListener("input", event => {
        if (event.target?.matches?.("#mg-seed_requested, #mg-steps, #mg-cfg")) { invalidate(); schedulePreview(); }
    });

    refreshCatalog();
    return {
        refreshCatalog, refreshNamePreview, validate, execute, composeGrids, namedCopyForGenerate,
        getPlan: () => plan, getDefinition: () => structuredClone(definition),
        getValidated: () => validated, getRun: () => run,
        setAxis(key, spec) {
            const row = axisRows[key];
            row.type.value = spec.type || "none";
            fillAxisOptions(key);
            if (spec.values) for (const option of row.multi.options) option.selected = spec.values.includes(option.value);
            row.text.value = spec.text || "";
            row.search.value = spec.search || "";
            row.replacements.value = spec.replacements || "";
            syncAxis(key);
            return plan;
        },
    };
}
