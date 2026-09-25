/** PLAY1c Manga Generate view. Owns no ComfyUI routes and no authoring document data. */
import { GenerationState, ACTIVE_JOB_STATES } from "../state/generation_state.js";
import { MangaGenerationClient } from "../adapters/manga_generation_client.js";
import { validateAuthoringDocument } from "../domain/authoring_document.js";
import { setupNumericWheelControl } from "./numeric_wheel.js";

const FIELDS = ["checkpoint_id", "sampler_id", "scheduler_id", "steps", "cfg", "width", "height", "seed_requested"];
const SELECTS = new Set(["checkpoint_id", "sampler_id", "scheduler_id"]);
const INTEGER = /^(0|[1-9][0-9]*)$/;
const JOB_ID = /^[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}$/;
const own = (obj, key) => Object.hasOwn(obj, key);
const LORA_TAG = /^<lora:([^:<>]+):([+-]?(?:\d+(?:\.\d*)?|\.\d+))>$/;
const ANGLE_TAG = /<[^<>]*>/g;
const SCENE_LORA_TAG = /<lora:/i;

const SCENE_PALETTE = [
    { hex: "#e53935", rgb: [229, 57, 53] },
    { hex: "#1e88e5", rgb: [30, 136, 229] },
    { hex: "#43a047", rgb: [67, 160, 71] },
    { hex: "#fb8c00", rgb: [251, 140, 0] },
    { hex: "#8e24aa", rgb: [142, 36, 170] },
    { hex: "#00acc1", rgb: [0, 172, 193] }
];

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

const INCOMPATIBLE_CHECKPOINT_SUBSTRINGS = [
    "sd15", "sd_1.5", "sd-1.5", "v1-5", "v1.5", "sd21", "sd_2.1", "sd-2.1", "flux", "cascade"
];
const COMPATIBLE_CHECKPOINT_SUBSTRINGS = ["illustrious", "sdxl"];

export function isIllustriousSdxlCheckpoint(checkpointId, catalog) {
    if (!checkpointId || typeof checkpointId !== "string") return false;
    const entry = (catalog?.checkpoints || []).find(c => c && (c.id === checkpointId || c.filename === checkpointId));
    if (entry && entry.family && entry.family !== "UNKNOWN") {
        const fam = String(entry.family).toLowerCase();
        if (fam === "illustrious" || fam === "sdxl") return true;
        if (["sd15", "v1-5", "sd21", "v2-1", "flux", "cascade", "auraflow", "sd3"].includes(fam)) return false;
    }
    const lower = checkpointId.toLowerCase();
    if (INCOMPATIBLE_CHECKPOINT_SUBSTRINGS.some(inc => lower.includes(inc))) return false;
    return COMPATIBLE_CHECKPOINT_SUBSTRINGS.some(comp => lower.includes(comp));
}

export function generationBlockReason(state, authoringStore = state.authoringStore, source = "mode") {
    if (state.historyLoading) return "Checking recorded Manga jobs…";
    if (state.submitUnconfirmed) return "Job outcome is UNKNOWN; automatic retry is disabled.";
    if (state.localBusy) return "Submission is in progress…";
    if (state.activeJob && ACTIVE_JOB_STATES.has(state.activeJob.state)) return "Job already active.";
    if (!state.catalog) return state.catalogError
        ? `Capability catalog unavailable — ${state.catalogError}`
        : "Manga workspace unavailable; capability catalog unavailable.";
    const sceneScope = source === "scenes" || (source === "mode" && state.mode === "scene");
    try {
        if (sceneScope) buildSceneGenerationSettings(state, authoringStore);
        else if (source === "global") buildGlobalGenerationSettings(state, authoringStore);
        else buildGenerationSettings(state);
    } catch (cause) {
        return cause.message;
    }
    if (sceneScope) {
        const document = authoringStore?.getDocument?.();
        const scenes = document?.pages?.[0]?.scenes || [];
        if (scenes.some(scene => SCENE_LORA_TAG.test(String(scene?.prompt || "")) ||
            SCENE_LORA_TAG.test(String(scene?.negative_prompt || "")))) {
            return "Scene LoRA prompt notation is unavailable in PLAY5; remove it from the Scene document.";
        }
        return "";
    }
    if (source === "global") {
        const page = authoringStore?.getPage?.(0);
        return loraBlockReason(state.catalog, page?.style_prompt || "", page?.style_negative_prompt || "");
    }
    return loraBlockReason(state.catalog, state.draft.positive_raw, state.draft.negative_raw);
}

export function buildGenerationSettings(state, promptValues = null) {
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
        mode: "txt2img", checkpoint_id: draft.checkpoint_id,
        positive_raw: promptValues?.positive_raw ?? draft.positive_raw,
        negative_raw: promptValues?.negative_raw ?? draft.negative_raw,
        sampler_id: draft.sampler_id, scheduler_id: draft.scheduler_id,
        steps: values.steps, cfg, width: values.width, height: values.height,
        seed_requested: seed, capability_revision: catalog.revision
    };
}

export function buildGlobalGenerationSettings(state, authoringStore = state.authoringStore) {
    const page = authoringStore?.getPage?.(0);
    if (!page) throw new Error("Global prompt page is unavailable");
    return buildGenerationSettings(state, {
        positive_raw: typeof page.style_prompt === "string" ? page.style_prompt : "",
        negative_raw: typeof page.style_negative_prompt === "string" ? page.style_negative_prompt : ""
    });
}

export async function compileGlobalGeneration(state, authoringStore, client) {
    const settings = buildGlobalGenerationSettings(state, authoringStore);
    const promptError = loraBlockReason(state.catalog, settings.positive_raw, settings.negative_raw);
    if (promptError) throw new Error(promptError);
    if (typeof client?.compile !== "function") throw new Error("Basic generation compiler is unavailable");
    const compiled = await client.compile(settings);
    return { settings, compiled };
}

export function mountGenerationView(root, { state = new GenerationState(), client = new MangaGenerationClient(),
    authoringStore = null, session = null, getPromptTarget = null, setPromptTarget = null, pollMs = 1500, onCatalogChange = null } = {}) {
    state.authoringStore = authoringStore;
    state.session = session;
    state.sceneDraft = state.sceneDraft || {};
    state.sceneDraft.mask_feather ??= "16";
    state.sceneDraft.panel_strength ??= "1";
    state.sceneDraft.controlnet_strength ??= "0.35";
    state.sceneDraft.controlnet_start_percent ??= "0.0";
    state.sceneDraft.controlnet_end_percent ??= "1.0";
    state.sceneDraft.reference_weight ??= "0.70";
    state.sceneDraft.reference_start ??= "0.0";
    state.sceneDraft.reference_end ??= "1.0";
    const byId = id => root.querySelector(`#${id}`);
    const controls = Object.fromEntries(FIELDS.map(field => [field, byId(`mg-${field}`)]));
    setupNumericWheelControl(controls.width, { step: 8 });
    setupNumericWheelControl(controls.height, { step: 8 });
    const generate = byId("mg-generate");
    const generateLabel = byId("mg-generate-label");
    const generateReason = byId("mg-generate-reason");
    const status = byId("mg-status");
    const error = byId("mg-error");
    const preview = byId("mg-preview-image");
    const previewEmpty = byId("mg-preview-empty");
    const previewLabel = byId("mg-preview-label");
    const focusToggle = byId("mg-focus-toggle");
    const history = byId("mg-history");
    const catalogNote = byId("mg-catalog-note");
    const artworkToggle = byId("mg-toggle-artwork");
    const regionsToggle = byId("mg-toggle-regions");
    const stageModeSwitch = byId("mg-stage-mode-switch");
    const stageModeLayout = byId("mg-stage-mode-layout");
    const stageModeResult = byId("mg-stage-mode-result");
    const generationScopeControl = byId("mg-generation-scope");
    const generationScopeGlobal = byId("mg-generation-scope-global");
    const generationScopeScenes = byId("mg-generation-scope-scenes");
    const stageOverlay = byId("mg-stage-overlay");
    const stageNeutral = byId("mg-stage-neutral");
    let stageMode = (authoringStore?.getPage?.(0)?.scenes || []).length ? "layout" : "result"; // "layout" | "result"
    let stageLayer = session?.activeTab || "scenes"; // "scenes" | "frames" | "guides" | "cast"
    let generationScope = "global"; // transient Generation UI state; independent of the Prompt target
    let artworkVisible = true;
    let regionsVisible = true;
    let pollTimer = null;
    let polling = false;
    let presentationMode = "glance";
    let resultAspectRatio = null;
    let lastDraftAspectRatio = null;

    function hasSpatialStageContent(page = authoringStore?.getPage?.(0)) {
        return ["scenes", "character_instances", "visual_frames", "guides"]
            .some(field => Array.isArray(page?.[field]) && page[field].length > 0);
    }

    function renderGenerationScope() {
        const hasScenes = (authoringStore?.getPage?.(0)?.scenes || []).length > 0;
        if (!hasScenes) generationScope = "global";
        if (generationScopeControl) generationScopeControl.hidden = !hasScenes;
        generationScopeGlobal?.setAttribute("aria-pressed", String(generationScope === "global"));
        generationScopeScenes?.setAttribute("aria-pressed", String(generationScope === "scenes"));
        if (generationScopeScenes) generationScopeScenes.disabled = !hasScenes;
    }

    function setGenerationScope(next) {
        if (next !== "global" && next !== "scenes") return false;
        if (next === "scenes" && !(authoringStore?.getPage?.(0)?.scenes || []).length) return false;
        generationScope = next;
        renderGenerationScope();
        renderForm();
        renderStatus();
        return true;
    }

    function renderStageMode() {
        const hasSpatialContent = hasSpatialStageContent();
        if (!hasSpatialContent) stageMode = "result";
        if (stageModeSwitch) stageModeSwitch.hidden = !hasSpatialContent;
        const isLayout = hasSpatialContent && stageMode === "layout";
        stageModeLayout?.setAttribute("aria-selected", String(isLayout));
        stageModeResult?.setAttribute("aria-selected", String(!isLayout));
        if (stageModeLayout) {
            stageModeLayout.disabled = !hasSpatialContent;
            stageModeLayout.title = !hasSpatialContent
                ? "Layout is available when the document has spatial content"
                : "領域編集 · Current authoring layout";
        }
        root.dataset.stageMode = isLayout ? "layout" : "result";
    }

    function setStageMode(next) {
        if (next !== "layout" && next !== "result") return;
        if (next === "layout" && !hasSpatialStageContent()) return;
        stageMode = next;
        renderStageMode();
        syncPreviewGeometry();
        renderStatus();
        renderStageOverlay();
    }

    function syncPreviewGeometry() {
        if (stageMode !== "layout" && state.preview.url && artworkVisible && resultAspectRatio) {
            root.style.setProperty("--mg-preview-ratio", `${resultAspectRatio.width} / ${resultAspectRatio.height}`);
            root.style.setProperty("--mg-preview-ratio-value", String(resultAspectRatio.value));
            return;
        }
        const page = authoringStore?.getPage?.(0);
        const usePageSize = stageMode === "layout" || generationScope === "scenes";
        const source = usePageSize && page
            ? { width: page.width_px, height: page.height_px }
            : state.draft;
        const width = Number(source?.width);
        const height = Number(source?.height);
        const value = width / height;
        if (Number.isFinite(value) && value > 0 && width > 0 && height > 0) {
            lastDraftAspectRatio = { width, height, value };
        }
        if (lastDraftAspectRatio) {
            root.style.setProperty("--mg-preview-ratio", `${lastDraftAspectRatio.width} / ${lastDraftAspectRatio.height}`);
            root.style.setProperty("--mg-preview-ratio-value", String(lastDraftAspectRatio.value));
        }
    }

    function renderPresentation() {
        const focused = presentationMode === "focus";
        root.dataset.presentation = presentationMode;
        root.dataset.result = state.preview.url ? "validated" : "empty";
        if (!focusToggle) return;
        focusToggle.textContent = focused ? "Back to Create" : "Focus Preview";
        focusToggle.setAttribute("aria-label", focused ? "Return to Create view" : "Focus Preview");
        focusToggle.setAttribute("aria-pressed", String(focused));
        focusToggle.title = focused ? "Return to Create" : "Give the verified result more space";
    }

    function setPresentation(next, restoreFocus = false) {
        if (next !== "glance" && next !== "focus") return;
        presentationMode = next;
        renderPresentation();
        if (restoreFocus) focusToggle?.focus({ preventScroll: true });
    }

    function onPresentationKeyDown(event) {
        if (root.hidden || event.key !== "Escape" || presentationMode !== "focus" || event.defaultPrevented || event.isComposing) return;
        const target = event.target;
        if (target?.matches?.("input, textarea, select, [contenteditable=\"true\"]") || target?.isContentEditable) return;
        event.preventDefault();
        event.stopPropagation();
        setPresentation("glance", true);
    }

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
        renderGenerationScope();
        controls.width.readOnly = false;
        controls.height.readOnly = false;
        controls.width.disabled = false;
        controls.height.disabled = false;
        if (authoringStore) {
            const page = authoringStore.getPage?.(0);
            if (page) {
                if (document.activeElement !== controls.width) {
                    controls.width.value = String(page.width_px);
                }
                if (document.activeElement !== controls.height) {
                    controls.height.value = String(page.height_px);
                }
                if (state.draft.width !== String(page.width_px)) {
                    state.draft.width = String(page.width_px);
                }
                if (state.draft.height !== String(page.height_px)) {
                    state.draft.height = String(page.height_px);
                }
            }
        }
        if (!hasSpatialStageContent()) stageMode = "result";
        renderStageMode();
        renderStageOverlay();
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
        renderGenerationScope();
        const job = state.activeJob;
        const stateName = job?.state === "RUNNING" ? "GENERATING" :
            ["VALIDATING", "SUBMITTING"].includes(job?.state) ? "SUBMITTING" : job?.state;
        status.textContent = state.historyLoading ? "Checking recorded Manga jobs…" :
            state.submitUnconfirmed ? "UNKNOWN · Job creation response unavailable" :
            state.localBusy ? "SUBMITTING · Validating settings and creating Manga job…" :
            job ? `${stateName} · Manga job ${job.job_id}` :
                state.error ? "FAILED · Manga generation could not start" :
                state.catalog ? `READY · Ready to generate one ${generationScope === "scenes" ? "Scene Layout" : "image"}` : "FAILED · Capabilities unavailable";
        status.dataset.state = state.submitUnconfirmed ? "UNKNOWN" :
            state.localBusy ? "SUBMITTING" : (stateName || (state.error ? "FAILED" : "READY"));
        const reason = generationBlockReason(state, authoringStore, generationScope);
        generate.disabled = Boolean(reason);
        generateReason.textContent = reason;
        generateReason.hidden = !reason;
        generateLabel.textContent = generationScope === "scenes" && !state.localBusy && !["VALIDATING", "SUBMITTING", "QUEUED", "RUNNING"].includes(job?.state)
            ? "Generate with Scenes" : state.localBusy || ["VALIDATING", "SUBMITTING"].includes(job?.state)
            ? "Submitting…" : ["QUEUED", "RUNNING"].includes(job?.state) ? "Generating…" : "Generate";
        const message = state.error || (job?.state === "FAILED" || job?.state === "UNKNOWN" ?
            `${job.state}: ${job.error?.message || "Backend outcome is not confirmed"}` : "");
        error.textContent = message;
        error.hidden = !message;
        syncPreviewGeometry();
        const isPrevious = state.preview.jobId && job && state.preview.jobId !== job.job_id;
        previewLabel.textContent = state.preview.jobId ?
            (state.submitUnconfirmed ? "Previous verified result · current submission UNKNOWN" :
                isPrevious ? `Previous verified result · current job ${job.state}` : "Verified current result") :
            "No verified result yet";

        const hasResult = Boolean(state.preview.url);

        renderStageMode();

        const isLayout = stageMode === "layout" && hasSpatialStageContent();

        if (isLayout) {
            preview.hidden = true;
            previewEmpty.hidden = true;
            if (stageNeutral) stageNeutral.hidden = true;
            if (stageOverlay) stageOverlay.style.display = "block";
            const page = authoringStore?.getPage?.(0);
            previewLabel.textContent = page
                ? `Authoring layout · ${page.width_px} × ${page.height_px}`
                : "Authoring layout";
        } else {
            if (stageOverlay) stageOverlay.style.display = "none";
            if (stageNeutral) stageNeutral.hidden = true;
            const showArtwork = hasResult && artworkVisible;
            preview.hidden = !showArtwork;
            previewEmpty.hidden = showArtwork;
            const isPrevious = state.preview.jobId && job && state.preview.jobId !== job.job_id;
            previewLabel.textContent = state.preview.jobId ?
                (state.submitUnconfirmed ? "Previous verified result · current submission UNKNOWN" :
                    isPrevious ? `Previous verified result · current job ${job.state}` : "Verified current result") :
                "No verified result yet";
        }

        if (artworkToggle) {
            artworkToggle.disabled = !hasResult;
            artworkToggle.setAttribute("aria-pressed", String(hasResult && artworkVisible));
            artworkToggle.title = !hasResult
                ? "No verified result yet"
                : (artworkVisible ? "Hide verified result artwork" : "Show verified result artwork");
        }

        if (regionsToggle) {
            regionsToggle.disabled = !hasSpatialStageContent();
            regionsToggle.setAttribute("aria-pressed", String(isLayout));
            regionsToggle.title = !hasSpatialStageContent()
                ? "Layout is available when the document has spatial content"
                : (isLayout ? "Viewing scene layout" : "Switch to Layout mode to view scene layout");
        }

        renderPresentation();
    }

    stageModeLayout?.addEventListener("click", () => {
        setStageMode("layout");
    });
    stageModeResult?.addEventListener("click", () => {
        setStageMode("result");
    });

    focusToggle?.addEventListener("click", () => {
        setPresentation(presentationMode === "focus" ? "glance" : "focus");
    });
    document.addEventListener("keydown", onPresentationKeyDown);

    artworkToggle?.addEventListener("click", () => {
        if (!state.preview.url) return;
        artworkVisible = !artworkVisible;
        syncPreviewGeometry();
        renderStatus();
        renderStageOverlay();
    });

    regionsToggle?.addEventListener("click", () => {
        setStageMode(stageMode === "layout" ? "result" : "layout");
    });

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
                probe.onload = () => {
                    resultAspectRatio = {
                        width: probe.naturalWidth || 1,
                        height: probe.naturalHeight || 1,
                        value: (probe.naturalWidth || 1) / (probe.naturalHeight || 1)
                    };
                    resolve();
                };
                probe.onerror = () => reject(new Error("Validated result PNG could not be displayed"));
                probe.src = url;
            }).catch(cause => { URL.revokeObjectURL(url); throw cause; });
            const old = state.preview.url;
            state.setPreview(job.job_id, url);
            preview.src = url;
            if (old) URL.revokeObjectURL(old);
            stageMode = "result";
            syncPreviewGeometry();
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

    async function refreshCatalog() {
        try {
            const catalog = await client.capabilities();
            state.setCatalog(catalog);
            renderForm();
            renderStatus();
            onCatalogChange?.(catalog);
            return catalog;
        } catch (cause) {
            state.catalog = null;
            state.catalogError = cause.message;
            renderForm();
            renderStatus();
            throw cause;
        }
    }

    // =========================================================================
    // PAGE COMPOSITE FLOW (Card MANGA-WORKSPACE-PAGE-COMPOSITE-GUI1)
    // =========================================================================
    function setupPageCompositeControls() {
        const compositeSection = document.createElement("div");
        compositeSection.className = "mg-page-composite-section";
        compositeSection.dataset.testid = "page-composite-section";

        const headerRow = document.createElement("div");
        headerRow.className = "mg-page-composite-header";

        const compositeBtn = document.createElement("button");
        compositeBtn.type = "button";
        compositeBtn.className = "mg-page-composite-btn";
        compositeBtn.dataset.testid = "page-composite-btn";
        compositeBtn.textContent = "ページ合成";

        const historyBtn = document.createElement("button");
        historyBtn.type = "button";
        historyBtn.className = "mg-page-composite-history-btn";
        historyBtn.dataset.testid = "page-composite-history-btn";
        historyBtn.textContent = "合成履歴";

        const compositeStatus = document.createElement("span");
        compositeStatus.className = "mg-page-composite-status";
        compositeStatus.dataset.testid = "page-composite-status";

        headerRow.append(compositeBtn, historyBtn, compositeStatus);

        const compositeError = document.createElement("div");
        compositeError.className = "mg-page-composite-error";
        compositeError.dataset.testid = "page-composite-error";
        compositeError.style.display = "none";

        const compositePreviewContainer = document.createElement("div");
        compositePreviewContainer.className = "mg-page-composite-preview";
        compositePreviewContainer.dataset.testid = "page-composite-preview";
        compositePreviewContainer.style.display = "none";

        const compositeImg = document.createElement("img");
        compositeImg.className = "mg-page-composite-img";
        compositeImg.dataset.testid = "page-composite-img";
        compositeImg.alt = "Page Composite Preview";
        compositePreviewContainer.append(compositeImg);

        const historyContainer = document.createElement("div");
        historyContainer.className = "mg-page-composite-history-container";
        historyContainer.dataset.testid = "page-composite-history-container";

        const historyError = document.createElement("div");
        historyError.className = "mg-page-composite-history-error";
        historyError.dataset.testid = "page-composite-history-error";
        historyError.style.display = "none";

        const historyList = document.createElement("div");
        historyList.className = "mg-page-composite-history-list";
        historyList.dataset.testid = "page-composite-history-list";

        historyContainer.append(historyError, historyList);

        compositeSection.append(headerRow, compositeError, compositePreviewContainer, historyContainer);

        const actionsContainer = root.querySelector(".mg-actions") || root.querySelector(".mg-form-actions") || root;
        actionsContainer.append(compositeSection);

        let isComposing = false;
        let isLoadingHistory = false;
        let currentCompositeId = null;
        let currentCompositePageId = null;
        let currentCompositePageIndex = null;
        let lastLoadedPageId = null;
        let lastLoadedPageIndex = null;
        let selectedHistoryId = null;

        function resolveCurrentPageIdentity(doc) {
            const activeState = (typeof options === "object" && options?.state) || state;
            const store = (typeof options === "object" && options?.store) || authoringStore || activeState?.authoringStore;
            const authoringDoc = doc || store?.getDocument?.() || null;

            // 1. Resolve pageIndex via value-based fallback
            let pageIndex = null;
            if (typeof store?.getCurrentPageIndex === "function") {
                const idx = store.getCurrentPageIndex();
                if (typeof idx === "number" && Number.isInteger(idx) && idx >= 0) {
                    pageIndex = idx;
                }
            }
            if (pageIndex === null && typeof activeState?.currentPageIndex === "number" && Number.isInteger(activeState.currentPageIndex) && activeState.currentPageIndex >= 0) {
                pageIndex = activeState.currentPageIndex;
            }

            // 2. Resolve pageId via value-based fallback
            let pageId = null;
            if (typeof store?.getCurrentPageId === "function") {
                const pid = store.getCurrentPageId();
                if (typeof pid === "string" && pid.trim().length > 0) {
                    pageId = pid;
                }
            }
            if (!pageId && typeof store?.getCurrentPage === "function") {
                const cp = store.getCurrentPage();
                const pid = cp?.id || cp?.page_id;
                if (typeof pid === "string" && pid.trim().length > 0) {
                    pageId = pid;
                }
            }
            if (!pageId && typeof activeState?.currentPageId === "string" && activeState.currentPageId.trim().length > 0) {
                pageId = activeState.currentPageId;
            }

            // 3. If pageIndex is still unresolved but pageId is known, derive index from authoringDoc.pages
            if (pageIndex === null && pageId && Array.isArray(authoringDoc?.pages)) {
                const foundIdx = authoringDoc.pages.findIndex(p => p.id === pageId || p.page_id === pageId);
                if (foundIdx >= 0) {
                    pageIndex = foundIdx;
                }
            }

            // 4. Default pageIndex to 0 if still unresolved
            if (pageIndex === null) {
                pageIndex = 0;
            }

            // 5. If pageId is still unresolved, resolve from authoringDoc.pages[pageIndex]
            if (!pageId && Array.isArray(authoringDoc?.pages) && authoringDoc.pages[pageIndex]) {
                const targetPage = authoringDoc.pages[pageIndex];
                const pid = targetPage.id || targetPage.page_id;
                if (typeof pid === "string" && pid.trim().length > 0) {
                    pageId = pid;
                }
            }

            return { pageIndex, pageId, authoringDoc };
        }

        compositeBtn.addEventListener("click", async () => {
            if (isComposing) return;
            isComposing = true;
            compositeBtn.disabled = true;
            compositeError.style.display = "none";
            compositeError.textContent = "";

            const { pageIndex, pageId, authoringDoc } = resolveCurrentPageIdentity();
            if (!authoringDoc) {
                compositeError.textContent = "Authoring Document not available";
                compositeError.style.display = "block";
                isComposing = false;
                compositeBtn.disabled = false;
                return;
            }

            const genParams = {
                checkpoint_id: state.checkpoint_id || "",
                sampler_id: state.sampler_id || "",
                scheduler_id: state.scheduler_id || "",
                steps: Number(state.steps) || 20,
                cfg: Number(state.cfg) || 7,
                seed: state.seed_requested === "-1" || state.seed_requested == null ? -1 : Number(state.seed_requested),
                positive_prompt: state.positive_raw || "",
                negative_prompt: state.negative_raw || "",
            };

            const composePayload = {
                authoring_document: authoringDoc,
                generation_params: genParams,
            };
            if (pageId) composePayload.page_id = pageId;
            if (pageIndex !== null && pageIndex !== undefined) composePayload.page_index = pageIndex;

            try {
                const composeRes = await fetch('/api/manga/page-composites/compose', {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(composePayload),
                });

                if (!composeRes.ok) {
                    let errMsg = `Compose failed: HTTP ${composeRes.status}`;
                    try {
                        const errData = await composeRes.json();
                        if (errData.error) errMsg = errData.error;
                    } catch (_) {}
                    errMsg = errMsg.replace(/[A-Za-z]:\\[^ \t\n\r"'\)]+/g, "[redacted-path]");
                    compositeError.textContent = errMsg;
                    compositeError.style.display = "block";
                    return;
                }

                const composeData = await composeRes.json();
                const compositeId = composeData.composite_id;
                if (!compositeId) {
                    throw new Error("Missing composite_id in response");
                }

                currentCompositeId = compositeId;
                currentCompositePageId = pageId;
                currentCompositePageIndex = pageIndex;

                const artifactUrl = `/api/manga/page-composites/${compositeId}/artifact`;
                compositeImg.src = artifactUrl;
                compositePreviewContainer.style.display = "block";

                try {
                    const currentnessRes = await fetch(`/api/manga/page-composites/${compositeId}/currentness`, {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify(composePayload),
                    });

                    if (currentnessRes.ok) {
                        const currentnessData = await currentnessRes.json();
                        const status = currentnessData.status || "UNKNOWN";
                        compositeStatus.textContent = status;
                        compositeStatus.dataset.status = status;
                    } else {
                        compositeStatus.textContent = "UNKNOWN";
                        compositeStatus.dataset.status = "UNKNOWN";
                        compositeError.textContent = "Currentness classification unavailable";
                        compositeError.style.display = "block";
                    }
                } catch (curErr) {
                    compositeStatus.textContent = "UNKNOWN";
                    compositeStatus.dataset.status = "UNKNOWN";
                    compositeError.textContent = "Currentness request failed";
                    compositeError.style.display = "block";
                }
            } catch (err) {
                let msg = err.message || "Failed to composite page";
                msg = msg.replace(/[A-Za-z]:\\[^ \t\n\r"'\)]+/g, "[redacted-path]");
                compositeError.textContent = msg;
                compositeError.style.display = "block";
            } finally {
                isComposing = false;
                compositeBtn.disabled = false;
            }
        });

        async function loadHistory() {
            if (isLoadingHistory) return;
            isLoadingHistory = true;
            historyBtn.disabled = true;
            historyError.style.display = "none";
            historyError.textContent = "";

            const { pageIndex, pageId, authoringDoc } = resolveCurrentPageIdentity();
            if (!authoringDoc) {
                historyError.textContent = "Authoring Document not available";
                historyError.style.display = "block";
                isLoadingHistory = false;
                historyBtn.disabled = false;
                return;
            }

            const docId = authoringDoc.id || authoringDoc.document_id || "default";
            const targetPageId = pageId || (authoringDoc.pages?.[pageIndex]?.id) || (authoringDoc.pages?.[pageIndex]?.page_id) || "";

            lastLoadedPageId = targetPageId;
            lastLoadedPageIndex = pageIndex;

            const params = new URLSearchParams();
            if (docId) params.set("document_id", docId);
            if (targetPageId) params.set("page_id", targetPageId);

            try {
                const res = await fetch(`/api/manga/page-composites?${params.toString()}`, {
                    method: "GET",
                    headers: { "Accept": "application/json" }
                });

                if (!res.ok) {
                    let errMsg = `Failed to load history: HTTP ${res.status}`;
                    try {
                        const errData = await res.json();
                        if (errData.error) errMsg = errData.error;
                    } catch (_) {}
                    errMsg = errMsg.replace(/[A-Za-z]:\\[^ \t\n\r"'\)]+/g, "[redacted-path]");
                    historyError.textContent = errMsg;
                    historyError.style.display = "block";
                    return;
                }

                const data = await res.json();
                const entries = Array.isArray(data.entries) ? data.entries : (Array.isArray(data) ? data : []);
                renderHistoryList(entries);
            } catch (err) {
                let msg = err.message || "Failed to load composite history";
                msg = msg.replace(/[A-Za-z]:\\[^ \t\n\r"'\)]+/g, "[redacted-path]");
                historyError.textContent = msg;
                historyError.style.display = "block";
            } finally {
                isLoadingHistory = false;
                historyBtn.disabled = false;
            }
        }

        function renderHistoryList(entries) {
            if (typeof historyList.replaceChildren === "function") {
                historyList.replaceChildren();
            } else {
                while (historyList.firstChild) historyList.removeChild(historyList.firstChild);
            }

            if (!entries || entries.length === 0) {
                const emptyEl = document.createElement("div");
                emptyEl.className = "mg-page-composite-history-empty";
                emptyEl.dataset.testid = "page-composite-history-empty";
                emptyEl.textContent = "履歴なし";
                historyList.append(emptyEl);
                return;
            }

            for (const entry of entries) {
                const itemEl = document.createElement("div");
                itemEl.className = "mg-page-composite-history-item";
                itemEl.dataset.testid = "page-composite-history-item";
                itemEl.dataset.compositeId = entry.composite_id || "";
                if (entry.composite_id === selectedHistoryId) {
                    if (itemEl.classList?.add) itemEl.classList.add("selected");
                }

                const labelEl = document.createElement("span");
                labelEl.className = "mg-page-composite-history-label";
                const shortId = (entry.composite_id || "").slice(0, 16);
                const timeStr = entry.created_at ? new Date(entry.created_at).toLocaleTimeString() : "";
                labelEl.textContent = timeStr ? `${shortId} (${timeStr})` : shortId;

                const itemStatusEl = document.createElement("span");
                itemStatusEl.className = "mg-page-composite-history-item-status";
                itemStatusEl.dataset.testid = "page-composite-history-item-status";

                itemEl.append(labelEl, itemStatusEl);

                itemEl.addEventListener("click", () => {
                    selectHistoryEntry(entry, itemEl, itemStatusEl);
                });

                historyList.append(itemEl);
            }
        }

        async function selectHistoryEntry(entry, itemEl, itemStatusEl) {
            selectedHistoryId = entry.composite_id;
            for (const child of historyList.children) {
                if (child.classList?.remove) {
                    child.classList.remove("selected");
                }
            }
            if (itemEl.classList?.add) {
                itemEl.classList.add("selected");
            }

            compositeError.style.display = "none";
            compositeError.textContent = "";

            const compositeId = entry.composite_id;
            currentCompositeId = compositeId;

            // Display artifact preview
            const artifactUrl = `/api/manga/page-composites/${compositeId}/artifact`;
            compositeImg.src = artifactUrl;
            compositePreviewContainer.style.display = "block";

            // Run currentness classification for selected entry using CURRENT authoring doc & gen params
            const { pageIndex, pageId, authoringDoc } = resolveCurrentPageIdentity();
            const genParams = {
                checkpoint_id: state.checkpoint_id || "",
                sampler_id: state.sampler_id || "",
                scheduler_id: state.scheduler_id || "",
                steps: Number(state.steps) || 20,
                cfg: Number(state.cfg) || 7,
                seed: state.seed_requested === "-1" || state.seed_requested == null ? -1 : Number(state.seed_requested),
                positive_prompt: state.positive_raw || "",
                negative_prompt: state.negative_raw || "",
            };

            const payload = {
                authoring_document: authoringDoc,
                generation_params: genParams,
            };
            if (pageId) payload.page_id = pageId;
            if (pageIndex !== null && pageIndex !== undefined) payload.page_index = pageIndex;

            try {
                const currentnessRes = await fetch(`/api/manga/page-composites/${compositeId}/currentness`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(payload),
                });

                if (currentnessRes.ok) {
                    const currentnessData = await currentnessRes.json();
                    const status = currentnessData.status || "UNKNOWN";
                    compositeStatus.textContent = status;
                    compositeStatus.dataset.status = status;
                    if (itemStatusEl) {
                        itemStatusEl.textContent = status;
                        itemStatusEl.dataset.status = status;
                    }
                } else {
                    compositeStatus.textContent = "UNKNOWN";
                    compositeStatus.dataset.status = "UNKNOWN";
                    if (itemStatusEl) {
                        itemStatusEl.textContent = "UNKNOWN";
                        itemStatusEl.dataset.status = "UNKNOWN";
                    }
                    compositeError.textContent = "Currentness classification unavailable";
                    compositeError.style.display = "block";
                }
            } catch (curErr) {
                compositeStatus.textContent = "UNKNOWN";
                compositeStatus.dataset.status = "UNKNOWN";
                if (itemStatusEl) {
                    itemStatusEl.textContent = "UNKNOWN";
                    itemStatusEl.dataset.status = "UNKNOWN";
                }
                compositeError.textContent = "Currentness request failed";
                compositeError.style.display = "block";
            }
        }

        historyBtn.addEventListener("click", loadHistory);

        compositeImg.addEventListener("error", () => {
            compositeError.textContent = "Composite image could not be loaded";
            compositeError.style.display = "block";
        });

        const store = authoringStore || state.authoringStore;
        if (store && typeof store.subscribe === "function") {
            store.subscribe(() => {
                const { pageId: activePageId, pageIndex: activePageIndex } = resolveCurrentPageIdentity();
                const pageChanged = (currentCompositePageId && activePageId && currentCompositePageId !== activePageId) ||
                    (currentCompositePageIndex !== null && activePageIndex !== null && currentCompositePageIndex !== activePageIndex) ||
                    (lastLoadedPageId && activePageId && lastLoadedPageId !== activePageId) ||
                    (lastLoadedPageIndex !== null && activePageIndex !== null && lastLoadedPageIndex !== activePageIndex);

                if (pageChanged) {
                    compositeImg.src = "";
                    compositePreviewContainer.style.display = "none";
                    compositeStatus.textContent = "";
                    compositeStatus.removeAttribute("data-status");
                    compositeError.textContent = "";
                    compositeError.style.display = "none";
                    currentCompositeId = null;
                    currentCompositePageId = null;
                    currentCompositePageIndex = null;
                    lastLoadedPageId = null;
                    lastLoadedPageIndex = null;
                    selectedHistoryId = null;
                    if (typeof historyList.replaceChildren === "function") {
                        historyList.replaceChildren();
                    } else {
                        while (historyList.firstChild) historyList.removeChild(historyList.firstChild);
                    }
                    historyError.textContent = "";
                    historyError.style.display = "none";
                }
            });
        }
    }

    setupPageCompositeControls();

    async function generateOne({ source = "mode", isRetry = false } = {}) {
        if (!state.beginAttempt()) return;
        let submitStarted = false;
        renderStatus();
        try {
            let settings;
            let compiled;
            if (source === "global") {
                ({ settings, compiled } = await compileGlobalGeneration(state, authoringStore, client));
            } else if (source === "scenes") {
                settings = buildSceneGenerationSettings(state, authoringStore);
                compiled = await client.compileScene(settings);
            } else {
                settings = state.mode === "scene"
                    ? buildSceneGenerationSettings(state, authoringStore)
                    : buildGenerationSettings(state);
                compiled = state.mode === "scene"
                    ? await client.compileScene(settings)
                    : await client.compile(settings);
            }
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
            if (!isRetry && !submitStarted && (cause.code === "CAPABILITY_CHANGED" || /revision changed/i.test(cause.message))) {
                try {
                    await refreshCatalog();
                    return await generateOne({ source, isRetry: true });
                } catch {
                    // if refresh itself fails, proceed to normal error reporting
                }
            }
            if (submitStarted && (!cause.status || cause.status >= 500)) {
                state.submitUnconfirmed = true;
                state.error = `Submission outcome is unknown: ${cause.message}. No automatic retry.`;
            } else {
                state.error = cause.message;
            }
            renderStatus();
        }
    }
    function generateGlobal() { return generateOne({ source: "global" }); }

    for (const field of FIELDS) {
        controls[field].addEventListener(SELECTS.has(field) ? "change" : "input", event => {
            state.setDraft(field, event.target.value);
            if (authoringStore && (field === "width" || field === "height")) {
                const val = parseInt(event.target.value, 10);
                if (Number.isFinite(val) && val > 0) {
                    const page = authoringStore.getPage?.(0);
                    if (page && page[`${field}_px`] !== val) {
                        try {
                            authoringStore.setPageDimensions?.({ [field]: val });
                        } catch {
                            // keep draft even if store rejects transient invalid dimension
                        }
                    }
                }
            }
            renderStatus();
        });
        if (field === "width" || field === "height") {
            controls[field].addEventListener("change", event => {
                const val = parseInt(event.target.value, 10);
                if (Number.isFinite(val) && val > 0) {
                    const page = authoringStore?.getPage?.(0);
                    if (page && page[`${field}_px`] !== val) {
                        try {
                            authoringStore.setPageDimensions?.({ [field]: val });
                        } catch {}
                    }
                }
            });
        }
    }
    generate.addEventListener("click", () => generateOne({ source: generationScope }));
    generationScopeGlobal?.addEventListener("click", () => setGenerationScope("global"));
    generationScopeScenes?.addEventListener("click", () => setGenerationScope("scenes"));
    authoringStore?.subscribe?.(() => {
        renderForm();
        renderStatus();
        renderStageOverlay();
    });
    byId("mg-refresh-catalog").addEventListener("click", refreshCatalog);

    function getSvgPoint(svg, clientX, clientY) {
        if (typeof svg.createSVGPoint === "function" && typeof svg.getScreenCTM === "function") {
            const pt = svg.createSVGPoint();
            pt.x = clientX;
            pt.y = clientY;
            const ctm = svg.getScreenCTM();
            if (ctm) {
                try {
                    const inverted = ctm.inverse();
                    if (inverted) return pt.matrixTransform(inverted);
                } catch {}
            }
        }
        const rect = svg.getBoundingClientRect();
        const width = svg.viewBox.baseVal?.width || rect.width || 1024;
        const height = svg.viewBox.baseVal?.height || rect.height || 1024;
        const scaleX = rect.width ? width / rect.width : 1;
        const scaleY = rect.height ? height / rect.height : 1;
        return {
            x: (clientX - rect.left) * scaleX,
            y: (clientY - rect.top) * scaleY
        };
    }

    function setStageLayer(next) {
        if (!["scenes", "frames", "guides", "cast"].includes(next)) return;
        stageLayer = next;
        if (session && session.activeTab !== next) {
            session.setActiveTab(next);
        }
        renderStageOverlay();
    }

    if (session) {
        session.subscribe((s) => {
            if (s.activeTab) stageLayer = s.activeTab;
            renderStageOverlay();
        });
    }

    function calculateResizedRect(startArea, handle, dx, dy, minW = 0.05, minH = 0.05, maxRight = 1.0, maxBottom = 1.0, clampMinX = 0, clampMinY = 0) {
        const rBound = Math.min(maxRight, startArea.x + startArea.w);
        const bBound = Math.min(maxBottom, startArea.y + startArea.h);

        let x = startArea.x;
        let y = startArea.y;
        let w = startArea.w;
        let h = startArea.h;

        if (handle === "se") {
            w = Math.max(minW, Math.min(maxRight - x, startArea.w + dx));
            h = Math.max(minH, Math.min(maxBottom - y, startArea.h + dy));
        } else if (handle === "nw") {
            const nx = Math.max(clampMinX, Math.min(rBound - minW, startArea.x + dx));
            const ny = Math.max(clampMinY, Math.min(bBound - minH, startArea.y + dy));
            x = nx;
            y = ny;
            w = rBound - nx;
            h = bBound - ny;
        } else if (handle === "ne") {
            const ny = Math.max(clampMinY, Math.min(bBound - minH, startArea.y + dy));
            w = Math.max(minW, Math.min(maxRight - x, startArea.w + dx));
            y = ny;
            h = bBound - ny;
        } else if (handle === "sw") {
            const nx = Math.max(clampMinX, Math.min(rBound - minW, startArea.x + dx));
            x = nx;
            w = rBound - nx;
            h = Math.max(minH, Math.min(maxBottom - y, startArea.h + dy));
        }

        return {
            shape_type: "rect",
            x: parseFloat(x.toFixed(4)),
            y: parseFloat(y.toFixed(4)),
            w: parseFloat(w.toFixed(4)),
            h: parseFloat(h.toFixed(4))
        };
    }

    let isStageDragging = false;

    function renderStageOverlay() {
        if (!stageOverlay || isStageDragging) return;
        stageOverlay.replaceChildren();
        if (stageMode !== "layout" || !hasSpatialStageContent() || !authoringStore) {
            stageOverlay.style.display = "none";
            return;
        }
        stageOverlay.style.display = "block";

        const page = authoringStore.getPage?.(0);
        if (!page) return;
        const width = page.width_px || 1024;
        const height = page.height_px || 1024;
        stageOverlay.setAttribute("viewBox", `0 0 ${width} ${height}`);
        stageOverlay.setAttribute("preserveAspectRatio", "xMidYMid meet");
        stageOverlay.setAttribute("aria-label", "Current authoring layout");

        // Static Stage background; entity creation stays in Create.
        const pageBg = document.createElementNS("http://www.w3.org/2000/svg", "rect");
        pageBg.setAttribute("width", String(width));
        pageBg.setAttribute("height", String(height));
        pageBg.setAttribute("fill", "#1c1423");
        stageOverlay.append(pageBg);

        const badge = document.createElementNS("http://www.w3.org/2000/svg", "text");
        badge.setAttribute("x", String(width - 12));
        badge.setAttribute("y", "22");
        badge.setAttribute("text-anchor", "end");
        badge.setAttribute("fill", "rgba(212, 161, 225, 0.85)");
        badge.setAttribute("font-size", "11px");
        badge.setAttribute("font-family", "monospace");
        badge.setAttribute("font-weight", "700");
        badge.setAttribute("letter-spacing", "0.08em");
        badge.textContent = `CURRENT AUTHORING LAYOUT [${stageLayer.toUpperCase()}]`;
        stageOverlay.append(badge);

        const handleSize = Math.max(14, Math.min(24, Math.round(Math.min(width, height) * 0.022)));

        // Helper to attach 4 corner handles
        const attachHandles = ({
            area,
            color,
            minW = 0.05,
            minH = 0.05,
            maxRight = 1.0,
            maxBottom = 1.0,
            clampMinX = 0,
            clampMinY = 0,
            onUpdateVisuals,
            onCommit
        }) => {
            const handleDefs = [
                { id: "nw", getPos: (a) => ({ x: a.x * width - handleSize / 2, y: a.y * height - handleSize / 2 }) },
                { id: "ne", getPos: (a) => ({ x: (a.x + a.w) * width - handleSize / 2, y: a.y * height - handleSize / 2 }) },
                { id: "se", getPos: (a) => ({ x: (a.x + a.w) * width - handleSize / 2, y: (a.y + a.h) * height - handleSize / 2 }) },
                { id: "sw", getPos: (a) => ({ x: a.x * width - handleSize / 2, y: (a.y + a.h) * height - handleSize / 2 }) },
            ];
            const handleElements = {};
            for (const def of handleDefs) {
                const hEl = document.createElementNS("http://www.w3.org/2000/svg", "rect");
                hEl.classList.add("mg-stage-resize-handle");
                hEl.dataset.handle = def.id;
                const pos = def.getPos(area);
                hEl.setAttribute("x", String(pos.x));
                hEl.setAttribute("y", String(pos.y));
                hEl.setAttribute("width", String(handleSize));
                hEl.setAttribute("height", String(handleSize));
                hEl.setAttribute("rx", "2");
                hEl.setAttribute("ry", "2");
                hEl.setAttribute("stroke", color);
                handleElements[def.id] = hEl;
                stageOverlay.append(hEl);

                hEl.addEventListener("pointerdown", (e) => {
                    if (e.button !== 0) return;
                    e.stopPropagation();
                    e.preventDefault();
                    isStageDragging = true;
                    try { hEl.setPointerCapture(e.pointerId); } catch {}

                    const startSvgPt = getSvgPoint(stageOverlay, e.clientX, e.clientY);
                    const startArea = { ...area };
                    let currentArea = { ...startArea };

                    const onPointerMove = (me) => {
                        const curSvgPt = getSvgPoint(stageOverlay, me.clientX, me.clientY);
                        const dx = (curSvgPt.x - startSvgPt.x) / width;
                        const dy = (curSvgPt.y - startSvgPt.y) / height;
                        currentArea = calculateResizedRect(startArea, def.id, dx, dy, minW, minH, maxRight, maxBottom, clampMinX, clampMinY);
                        onUpdateVisuals(currentArea);
                        for (const d of handleDefs) {
                            const el = handleElements[d.id];
                            if (el) {
                                const p = d.getPos(currentArea);
                                el.setAttribute("x", String(p.x));
                                el.setAttribute("y", String(p.y));
                            }
                        }
                    };

                    const onPointerUp = () => {
                        window.removeEventListener("pointermove", onPointerMove);
                        window.removeEventListener("pointerup", onPointerUp);
                        window.removeEventListener("pointercancel", onPointerCancel);
                        try { hEl.releasePointerCapture(e.pointerId); } catch {}
                        isStageDragging = false;

                        if (
                            Math.abs(currentArea.x - startArea.x) > 1e-4 ||
                            Math.abs(currentArea.y - startArea.y) > 1e-4 ||
                            Math.abs(currentArea.w - startArea.w) > 1e-4 ||
                            Math.abs(currentArea.h - startArea.h) > 1e-4
                        ) {
                            onCommit(currentArea, startArea);
                        }
                    };

                    const onPointerCancel = () => {
                        window.removeEventListener("pointermove", onPointerMove);
                        window.removeEventListener("pointerup", onPointerUp);
                        window.removeEventListener("pointercancel", onPointerCancel);
                        try { hEl.releasePointerCapture(e.pointerId); } catch {}
                        isStageDragging = false;
                        onUpdateVisuals(startArea);
                    };

                    window.addEventListener("pointermove", onPointerMove);
                    window.addEventListener("pointerup", onPointerUp);
                    window.addEventListener("pointercancel", onPointerCancel);
                });
            }
            return handleElements;
        };

        // 0. Active Structural Guide Raster Underlay (Card Section 4 & 5)
        const guides = page.guides || [];
        const activeGuides = guides.filter(g => g && g.enabled !== false);
        if (activeGuides.length === 1) {
            const activeGuide = activeGuides[0];
            if (activeGuide.asset_reference) {
                const guideImg = document.createElementNS("http://www.w3.org/2000/svg", "image");
                guideImg.setAttribute("x", "0");
                guideImg.setAttribute("y", "0");
                guideImg.setAttribute("width", String(width));
                guideImg.setAttribute("height", String(height));
                guideImg.setAttribute("preserveAspectRatio", "xMidYMid meet");
                guideImg.setAttribute("href", `/api/guide-assets/view?ref=${encodeURIComponent(activeGuide.asset_reference)}`);
                guideImg.classList.add("mg-stage-guide-raster");
                guideImg.style.pointerEvents = "none";
                guideImg.style.opacity = "0.70";

                guideImg.addEventListener("error", () => {
                    guideImg.style.display = "none";
                    const errText = document.createElementNS("http://www.w3.org/2000/svg", "text");
                    errText.setAttribute("x", "12");
                    errText.setAttribute("y", String(height - 14));
                    errText.setAttribute("fill", "#fcd34d");
                    errText.setAttribute("font-size", "11px");
                    errText.setAttribute("font-family", "monospace");
                    errText.textContent = "Guide preview unavailable";
                    stageOverlay.append(errText);
                });
                stageOverlay.append(guideImg);
            }
        } else if (activeGuides.length > 1) {
            const warnText = document.createElementNS("http://www.w3.org/2000/svg", "text");
            warnText.setAttribute("x", "12");
            warnText.setAttribute("y", "22");
            warnText.setAttribute("fill", "#fcd34d");
            warnText.setAttribute("font-size", "11px");
            warnText.setAttribute("font-family", "monospace");
            warnText.textContent = "Multiple active guides: single guide supported for generation";
            stageOverlay.append(warnText);
        }

        // 1. Render Guides & Guide Figures
        guides.forEach((guide) => {
            const placement = guide.placement || { x: 0, y: 0, w: 1, h: 1 };
            const enabled = guide.enabled !== false;
            const gx = placement.x * width;
            const gy = placement.y * height;
            const gw = placement.w * width;
            const gh = placement.h * height;

            const gRect = document.createElementNS("http://www.w3.org/2000/svg", "rect");
            gRect.setAttribute("x", String(gx));
            gRect.setAttribute("y", String(gy));
            gRect.setAttribute("width", String(gw));
            gRect.setAttribute("height", String(gh));
            gRect.setAttribute("fill", enabled ? "rgba(186, 230, 253, 0.08)" : "rgba(250, 204, 21, 0.05)");
            gRect.setAttribute("stroke", enabled ? "#0284c7" : "#ca8a04");
            gRect.setAttribute("stroke-width", "1");
            if (!enabled) gRect.setAttribute("stroke-dasharray", "5 4");
            stageOverlay.append(gRect);

            // Figures inside guide
            (guide.figure_regions || []).forEach((fig, fIdx) => {
                const fa = fig.area || { x: 0.1, y: 0.1, w: 0.3, h: 0.4 };
                // Section 4 & 21: Transform Guide-local to page coordinates
                const pageFig = {
                    x: placement.x + fa.x * placement.w,
                    y: placement.y + fa.y * placement.h,
                    w: fa.w * placement.w,
                    h: fa.h * placement.h
                };
                const isSelected = (stageLayer === "guides" && session?.selectedFigureId === fig.figure_id && session?.selectedGuideId === guide.guide_id);

                const fRect = document.createElementNS("http://www.w3.org/2000/svg", "rect");
                fRect.setAttribute("x", String(pageFig.x * width));
                fRect.setAttribute("y", String(pageFig.y * height));
                fRect.setAttribute("width", String(pageFig.w * width));
                fRect.setAttribute("height", String(pageFig.h * height));
                fRect.classList.add("mg-stage-guide-figure");
                if (isSelected) fRect.classList.add("is-active");
                fRect.setAttribute("fill", isSelected ? "rgba(14, 116, 144, 0.35)" : "rgba(14, 116, 144, 0.15)");
                fRect.setAttribute("stroke", isSelected ? "#0891b2" : "#0e7490");
                fRect.setAttribute("stroke-width", isSelected ? "2.5" : "1.5");

                const fText = document.createElementNS("http://www.w3.org/2000/svg", "text");
                fText.setAttribute("x", String(pageFig.x * width + 4));
                fText.setAttribute("y", String(pageFig.y * height + 14));
                fText.setAttribute("fill", "#0891b2");
                fText.setAttribute("font-size", "10px");
                fText.setAttribute("font-weight", "bold");
                fText.setAttribute("paint-order", "stroke fill");
                fText.setAttribute("stroke", "#18121d");
                fText.setAttribute("stroke-width", "2px");
                fText.textContent = fig.figure_id || `Fig ${fIdx + 1}`;

                stageOverlay.append(fRect, fText);

                if (stageLayer === "guides") {
                    fRect.style.pointerEvents = "all";
                    fRect.style.cursor = "pointer";
                    fRect.addEventListener("pointerdown", (e) => {
                        if (e.button !== 0) return;
                        e.stopPropagation();
                        e.preventDefault();
                        if (session) {
                            session.selectGuide(guide.guide_id);
                            session.selectFigure(fig.figure_id);
                        }
                        renderStageOverlay();

                        // Drag move for figure in guide-local coords
                        try { fRect.setPointerCapture(e.pointerId); } catch {}
                        const startSvgPt = getSvgPoint(stageOverlay, e.clientX, e.clientY);
                        const startLocalArea = { ...fa };
                        let currentLocalArea = { ...startLocalArea };

                        const onPointerMove = (me) => {
                            const curSvgPt = getSvgPoint(stageOverlay, me.clientX, me.clientY);
                            const pageDx = (curSvgPt.x - startSvgPt.x) / width;
                            const pageDy = (curSvgPt.y - startSvgPt.y) / height;
                            const localDx = pageDx / placement.w;
                            const localDy = pageDy / placement.h;
                            const newX = Math.max(0, Math.min(1.0 - startLocalArea.w, startLocalArea.x + localDx));
                            const newY = Math.max(0, Math.min(1.0 - startLocalArea.h, startLocalArea.y + localDy));
                            currentLocalArea = {
                                x: parseFloat(newX.toFixed(4)),
                                y: parseFloat(newY.toFixed(4)),
                                w: startLocalArea.w,
                                h: startLocalArea.h
                            };
                            const curPageX = placement.x + currentLocalArea.x * placement.w;
                            const curPageY = placement.y + currentLocalArea.y * placement.h;
                            fRect.setAttribute("x", String(curPageX * width));
                            fRect.setAttribute("y", String(curPageY * height));
                            fText.setAttribute("x", String(curPageX * width + 4));
                            fText.setAttribute("y", String(curPageY * height + 14));
                        };

                        const onPointerUp = () => {
                            window.removeEventListener("pointermove", onPointerMove);
                            window.removeEventListener("pointerup", onPointerUp);
                            window.removeEventListener("pointercancel", onPointerCancel);
                            try { fRect.releasePointerCapture(e.pointerId); } catch {}
                            const ldx = currentLocalArea.x - startLocalArea.x;
                            const ldy = currentLocalArea.y - startLocalArea.y;
                            if (Math.abs(ldx) > 1e-4 || Math.abs(ldy) > 1e-4) {
                                try {
                                    authoringStore.moveGuideFigure(guide.guide_id, fig.figure_id, ldx, ldy);
                                } catch (err) { console.error("Move guide figure failed:", err); }
                            }
                        };

                        const onPointerCancel = () => {
                            window.removeEventListener("pointermove", onPointerMove);
                            window.removeEventListener("pointerup", onPointerUp);
                            window.removeEventListener("pointercancel", onPointerCancel);
                            try { fRect.releasePointerCapture(e.pointerId); } catch {}
                            renderStageOverlay();
                        };

                        window.addEventListener("pointermove", onPointerMove);
                        window.addEventListener("pointerup", onPointerUp);
                        window.addEventListener("pointercancel", onPointerCancel);
                    });

                    // 4 corner handles for active figure
                    if (isSelected) {
                        attachHandles({
                            area: pageFig,
                            color: "#0891b2",
                            minW: 0.04 * placement.w,
                            minH: 0.04 * placement.h,
                            maxRight: placement.x + placement.w,
                            maxBottom: placement.y + placement.h,
                            clampMinX: placement.x,
                            clampMinY: placement.y,
                            onUpdateVisuals: (curPageArea) => {
                                fRect.setAttribute("x", String(curPageArea.x * width));
                                fRect.setAttribute("y", String(curPageArea.y * height));
                                fRect.setAttribute("width", String(curPageArea.w * width));
                                fRect.setAttribute("height", String(curPageArea.h * height));
                                fText.setAttribute("x", String(curPageArea.x * width + 4));
                                fText.setAttribute("y", String(curPageArea.y * height + 14));
                            },
                            onCommit: (curPageArea) => {
                                const newLocalArea = {
                                    x: (curPageArea.x - placement.x) / placement.w,
                                    y: (curPageArea.y - placement.y) / placement.h,
                                    w: curPageArea.w / placement.w,
                                    h: curPageArea.h / placement.h
                                };
                                const ldx = newLocalArea.w - fa.w;
                                const ldy = newLocalArea.h - fa.h;
                                try {
                                    authoringStore.resizeGuideFigure(guide.guide_id, fig.figure_id, "se", ldx, ldy);
                                } catch (err) {
                                    console.error("Resize guide figure failed:", err);
                                    renderStageOverlay();
                                }
                            }
                        });
                    }
                }
            });
        });

        // 2. Render Visual Frames
        const frames = page.visual_frames || [];
        frames.forEach((fr, fIdx) => {
            const area = fr.area || fr.shape || { x: 0, y: 0, w: 1, h: 1 };
            const isSelected = (stageLayer === "frames" && session?.selectedFrameId === fr.frame_id);
            const rx = area.x * width;
            const ry = area.y * height;
            const rw = area.w * width;
            const rh = area.h * height;

            const rect = document.createElementNS("http://www.w3.org/2000/svg", "rect");
            rect.setAttribute("x", String(rx));
            rect.setAttribute("y", String(ry));
            rect.setAttribute("width", String(rw));
            rect.setAttribute("height", String(rh));
            rect.classList.add("mg-stage-frame-region");
            if (isSelected) rect.classList.add("is-active");

            const thickness = Math.max(1, Math.min(10, Math.round((fr.border_thickness || 4) * (width / (page.width_px || 832)))));
            rect.setAttribute("stroke", isSelected ? "#2563eb" : (fr.border_color || "#3b82f6"));
            rect.setAttribute("stroke-width", String(isSelected ? Math.max(thickness, 3) : thickness));
            rect.setAttribute("fill", isSelected ? "rgba(59, 130, 246, 0.15)" : "rgba(59, 130, 246, 0.04)");

            const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
            text.setAttribute("x", String(rx + 6));
            text.setAttribute("y", String(ry + 16));
            text.setAttribute("fill", isSelected ? "#60a5fa" : "#3b82f6");
            text.setAttribute("font-size", "11px");
            text.setAttribute("font-weight", "600");
            text.setAttribute("paint-order", "stroke fill");
            text.setAttribute("stroke", "#18121d");
            text.setAttribute("stroke-width", "2px");
            text.textContent = fr.frame_id || `Frame ${fIdx + 1}`;

            stageOverlay.append(rect, text);

            if (stageLayer === "frames") {
                rect.style.pointerEvents = "all";
                rect.style.cursor = "pointer";
                rect.addEventListener("pointerdown", (e) => {
                    if (e.button !== 0) return;
                    e.stopPropagation();
                    e.preventDefault();
                    if (session) session.selectFrame(fr.frame_id);
                    renderStageOverlay();

                    // Drag move
                    try { rect.setPointerCapture(e.pointerId); } catch {}
                    const startSvgPt = getSvgPoint(stageOverlay, e.clientX, e.clientY);
                    const startArea = { ...area };
                    let currentArea = { ...startArea };

                    const onPointerMove = (me) => {
                        const curSvgPt = getSvgPoint(stageOverlay, me.clientX, me.clientY);
                        const dx = (curSvgPt.x - startSvgPt.x) / width;
                        const dy = (curSvgPt.y - startSvgPt.y) / height;
                        const newX = Math.max(0, Math.min(1.0 - startArea.w, startArea.x + dx));
                        const newY = Math.max(0, Math.min(1.0 - startArea.h, startArea.y + dy));
                        currentArea = {
                            x: parseFloat(newX.toFixed(4)),
                            y: parseFloat(newY.toFixed(4)),
                            w: startArea.w,
                            h: startArea.h
                        };
                        rect.setAttribute("x", String(currentArea.x * width));
                        rect.setAttribute("y", String(currentArea.y * height));
                        text.setAttribute("x", String(currentArea.x * width + 6));
                        text.setAttribute("y", String(currentArea.y * height + 16));
                    };

                    const onPointerUp = () => {
                        window.removeEventListener("pointermove", onPointerMove);
                        window.removeEventListener("pointerup", onPointerUp);
                        window.removeEventListener("pointercancel", onPointerCancel);
                        try { rect.releasePointerCapture(e.pointerId); } catch {}
                        const fdx = currentArea.x - startArea.x;
                        const fdy = currentArea.y - startArea.y;
                        if (Math.abs(fdx) > 1e-4 || Math.abs(fdy) > 1e-4) {
                            try {
                                authoringStore.moveFrame(fr.frame_id, fdx, fdy);
                            } catch (err) { console.error("Move frame failed:", err); }
                        }
                    };

                    const onPointerCancel = () => {
                        window.removeEventListener("pointermove", onPointerMove);
                        window.removeEventListener("pointerup", onPointerUp);
                        window.removeEventListener("pointercancel", onPointerCancel);
                        try { rect.releasePointerCapture(e.pointerId); } catch {}
                        renderStageOverlay();
                    };

                    window.addEventListener("pointermove", onPointerMove);
                    window.addEventListener("pointerup", onPointerUp);
                    window.addEventListener("pointercancel", onPointerCancel);
                });

                if (isSelected) {
                    attachHandles({
                        area,
                        color: "#2563eb",
                        minW: 0.05,
                        minH: 0.05,
                        onUpdateVisuals: (cur) => {
                            rect.setAttribute("x", String(cur.x * width));
                            rect.setAttribute("y", String(cur.y * height));
                            rect.setAttribute("width", String(cur.w * width));
                            rect.setAttribute("height", String(cur.h * height));
                            text.setAttribute("x", String(cur.x * width + 6));
                            text.setAttribute("y", String(cur.y * height + 16));
                        },
                        onCommit: (cur, start) => {
                            const dx = cur.w - start.w;
                            const dy = cur.h - start.h;
                            try {
                                authoringStore.resizeFrame(fr.frame_id, "se", dx, dy);
                            } catch (err) {
                                console.error("Resize frame failed:", err);
                                renderStageOverlay();
                            }
                        }
                    });
                }
            }
        });

        // 3. Render Scenes
        const scenes = [...(page.scenes || [])].sort((a, b) => (Number(a.order) || 0) - (Number(b.order) || 0));
        const activeScene = scenes.find(scene => scene.scene_id === session?.selectedSceneId);
        const promptTarget = typeof getPromptTarget === "function" ? getPromptTarget() : null;

        scenes.forEach((scene, index) => {
            const isSelected = scene === activeScene && stageLayer === "scenes" &&
                (typeof getPromptTarget !== "function" || promptTarget === scene.scene_id);
            const area = scene.area || { x: 0, y: 0, w: 1, h: 1 };
            const rx = area.x * width;
            const ry = area.y * height;
            const rw = area.w * width;
            const rh = area.h * height;

            const rect = document.createElementNS("http://www.w3.org/2000/svg", "rect");
            rect.setAttribute("x", String(rx));
            rect.setAttribute("y", String(ry));
            rect.setAttribute("width", String(rw));
            rect.setAttribute("height", String(rh));
            rect.setAttribute("rx", "6");
            rect.setAttribute("ry", "6");
            rect.classList.add("mg-stage-scene-region");
            rect.dataset.sceneId = scene.scene_id;
            if (isSelected) rect.classList.add("is-active");

            const palette = SCENE_PALETTE[index % SCENE_PALETTE.length];
            rect.setAttribute("stroke", palette.hex);
            rect.setAttribute("stroke-width", isSelected ? "3.5" : "1.5");
            rect.setAttribute("stroke-dasharray", isSelected ? "none" : "4 3");
            rect.setAttribute("fill", palette.hex);
            rect.setAttribute("fill-opacity", isSelected ? "0.22" : "0.07");

            const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
            text.setAttribute("x", String(rx + 8));
            text.setAttribute("y", String(ry + 20));
            text.setAttribute("fill", palette.hex);
            text.setAttribute("font-size", isSelected ? "13px" : "11px");
            text.setAttribute("font-weight", isSelected ? "bold" : "600");
            text.setAttribute("font-family", "system-ui, sans-serif");
            text.setAttribute("paint-order", "stroke fill");
            text.setAttribute("stroke", "#18121d");
            text.setAttribute("stroke-width", "3px");
            text.textContent = scene.name || `Scene ${index + 1}`;

            stageOverlay.append(rect, text);

            rect.style.pointerEvents = "all";
            rect.style.cursor = isSelected ? "move" : "pointer";

            rect.addEventListener("pointerdown", (e) => {
                if (e.button !== 0) return;
                e.stopPropagation();
                e.preventDefault();

                isStageDragging = true;

                if (!isSelected) {
                    if (typeof setPromptTarget === "function") {
                        setPromptTarget(scene.scene_id);
                    } else if (session) {
                        session.setActiveTab("scenes");
                        session.selectScene(scene.scene_id);
                    }
                    if (session) {
                        session.selectInstance(null);
                        session.selectCast(null);
                    }
                }

                // Drag move on active scene
                try { rect.setPointerCapture(e.pointerId); } catch {}
                const startSvgPt = getSvgPoint(stageOverlay, e.clientX, e.clientY);
                const startArea = {
                    x: Number(scene.area?.x) || 0,
                    y: Number(scene.area?.y) || 0,
                    w: Number(scene.area?.w) || 0.84,
                    h: Number(scene.area?.h) || 0.22
                };
                let currentArea = { ...startArea };

                const onPointerMove = (me) => {
                    const curSvgPt = getSvgPoint(stageOverlay, me.clientX, me.clientY);
                    const dx = (curSvgPt.x - startSvgPt.x) / width;
                    const dy = (curSvgPt.y - startSvgPt.y) / height;
                    const newX = Math.max(0, Math.min(1.0 - startArea.w, startArea.x + dx));
                    const newY = Math.max(0, Math.min(1.0 - startArea.h, startArea.y + dy));
                    currentArea = {
                        x: parseFloat(newX.toFixed(4)),
                        y: parseFloat(newY.toFixed(4)),
                        w: startArea.w,
                        h: startArea.h
                    };
                    rect.setAttribute("x", String(currentArea.x * width));
                    rect.setAttribute("y", String(currentArea.y * height));
                    text.setAttribute("x", String(currentArea.x * width + 8));
                    text.setAttribute("y", String(currentArea.y * height + 20));
                };

                const onPointerUp = () => {
                    window.removeEventListener("pointermove", onPointerMove);
                    window.removeEventListener("pointerup", onPointerUp);
                    window.removeEventListener("pointercancel", onPointerCancel);
                    try { rect.releasePointerCapture(e.pointerId); } catch {}
                    isStageDragging = false;

                    const finalDx = currentArea.x - startArea.x;
                    const finalDy = currentArea.y - startArea.y;
                    if (Math.abs(finalDx) > 1e-4 || Math.abs(finalDy) > 1e-4) {
                        try {
                            authoringStore.moveScene(scene.scene_id, finalDx, finalDy);
                        } catch (err) {
                            console.error("Failed to move scene:", err);
                            renderStageOverlay();
                        }
                    } else {
                        renderStageOverlay();
                    }
                };

                const onPointerCancel = () => {
                    window.removeEventListener("pointermove", onPointerMove);
                    window.removeEventListener("pointerup", onPointerUp);
                    window.removeEventListener("pointercancel", onPointerCancel);
                    try { rect.releasePointerCapture(e.pointerId); } catch {}
                    isStageDragging = false;
                    renderStageOverlay();
                };

                window.addEventListener("pointermove", onPointerMove);
                window.addEventListener("pointerup", onPointerUp);
                window.addEventListener("pointercancel", onPointerCancel);
            });

            if (isSelected) {
                attachHandles({
                    area,
                    color: palette.hex,
                    minW: 0.10,
                    minH: 0.08,
                    onUpdateVisuals: (cur) => {
                        rect.setAttribute("x", String(cur.x * width));
                        rect.setAttribute("y", String(cur.y * height));
                        rect.setAttribute("width", String(cur.w * width));
                        rect.setAttribute("height", String(cur.h * height));
                        text.setAttribute("x", String(cur.x * width + 8));
                        text.setAttribute("y", String(cur.y * height + 20));
                    },
                    onCommit: (cur) => {
                        try {
                            authoringStore.resizeScene(scene.scene_id, cur);
                        } catch (err) {
                            console.error("Failed to resize scene:", err);
                            renderStageOverlay();
                        }
                    }
                });
            }
        });

        // 4. Render Character Instances
        const instances = page.character_instances || [];
        const castList = page.cast || [];
        instances.forEach((inst, idx) => {
            const area = inst.area || { x: 0, y: 0, w: 0.2, h: 0.2 };
            const castEntry = castList.find(c => c.cast_id === inst.cast_id);
            const colHex = castEntry?.color || "#06b6d4";
            const isSelected = (stageLayer === "cast" && session?.selectedInstanceId === inst.instance_id);

            const rx = area.x * width;
            const ry = area.y * height;
            const rw = area.w * width;
            const rh = area.h * height;

            const rect = document.createElementNS("http://www.w3.org/2000/svg", "rect");
            rect.setAttribute("x", String(rx));
            rect.setAttribute("y", String(ry));
            rect.setAttribute("width", String(rw));
            rect.setAttribute("height", String(rh));
            rect.classList.add("mg-stage-char-instance");
            rect.dataset.instanceId = inst.instance_id;
            rect.dataset.sceneId = inst.scene_id;
            if (isSelected) rect.classList.add("is-active");

            rect.setAttribute("stroke", colHex);
            rect.setAttribute("stroke-width", isSelected ? "3" : "2");
            rect.setAttribute("fill", colHex);
            rect.setAttribute("fill-opacity", isSelected ? "0.35" : "0.18");

            const parentScene = scenes.find(s => s.scene_id === inst.scene_id);
            const name = castEntry?.display_name || inst.cast_id;
            const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
            text.setAttribute("x", String(rx + 4));
            text.setAttribute("y", String(ry + rh - 6));
            text.setAttribute("fill", colHex);
            text.setAttribute("font-size", "10px");
            text.setAttribute("font-weight", "bold");
            text.setAttribute("paint-order", "stroke fill");
            text.setAttribute("stroke", "#18121d");
            text.setAttribute("stroke-width", "2px");
            text.textContent = `${name} (${inst.instance_id})`;

            stageOverlay.append(rect, text);

            rect.style.pointerEvents = "all";
            rect.style.cursor = isSelected ? "move" : "pointer";
            rect.addEventListener("pointerdown", (e) => {
                if (e.button !== 0) return;
                e.stopPropagation();
                e.preventDefault();

                isStageDragging = true;

                if (!isSelected) {
                    if (typeof setPromptTarget === "function") {
                        setPromptTarget("cast_" + inst.cast_id);
                    } else if (session) {
                        session.setActiveTab("cast");
                        session.selectCast(inst.cast_id);
                    }
                    if (session) {
                        session.selectScene(inst.scene_id);
                        session.selectInstance(inst.instance_id);
                    }
                }

                // Drag move clamped within parent scene
                try { rect.setPointerCapture(e.pointerId); } catch {}
                const startSvgPt = getSvgPoint(stageOverlay, e.clientX, e.clientY);
                const startArea = { ...area };
                let currentArea = { ...startArea };
                const scArea = parentScene?.area || { x: 0, y: 0, w: 1, h: 1 };

                const onPointerMove = (me) => {
                    const curSvgPt = getSvgPoint(stageOverlay, me.clientX, me.clientY);
                    const dx = (curSvgPt.x - startSvgPt.x) / width;
                    const dy = (curSvgPt.y - startSvgPt.y) / height;
                    const minX = scArea.x;
                    const minY = scArea.y;
                    const maxX = scArea.x + scArea.w - startArea.w;
                    const maxY = scArea.y + scArea.h - startArea.h;
                    const newX = Math.max(minX, Math.min(maxX, startArea.x + dx));
                    const newY = Math.max(minY, Math.min(maxY, startArea.y + dy));
                    currentArea = {
                        x: parseFloat(newX.toFixed(4)),
                        y: parseFloat(newY.toFixed(4)),
                        w: startArea.w,
                        h: startArea.h
                    };
                    rect.setAttribute("x", String(currentArea.x * width));
                    rect.setAttribute("y", String(currentArea.y * height));
                    text.setAttribute("x", String(currentArea.x * width + 4));
                    text.setAttribute("y", String(currentArea.y * height + currentArea.h * height - 6));
                };

                const onPointerUp = () => {
                    window.removeEventListener("pointermove", onPointerMove);
                    window.removeEventListener("pointerup", onPointerUp);
                    window.removeEventListener("pointercancel", onPointerCancel);
                    try { rect.releasePointerCapture(e.pointerId); } catch {}
                    isStageDragging = false;

                    const cdx = currentArea.x - startArea.x;
                    const cdy = currentArea.y - startArea.y;
                    if (Math.abs(cdx) > 1e-4 || Math.abs(cdy) > 1e-4) {
                        try {
                            authoringStore.moveCharacter(inst.instance_id, cdx, cdy);
                        } catch (err) { console.error("Move character failed:", err); }
                    } else {
                        renderStageOverlay();
                    }
                };

                const onPointerCancel = () => {
                    window.removeEventListener("pointermove", onPointerMove);
                    window.removeEventListener("pointerup", onPointerUp);
                    window.removeEventListener("pointercancel", onPointerCancel);
                    try { rect.releasePointerCapture(e.pointerId); } catch {}
                    isStageDragging = false;
                    renderStageOverlay();
                };

                window.addEventListener("pointermove", onPointerMove);
                window.addEventListener("pointerup", onPointerUp);
                window.addEventListener("pointercancel", onPointerCancel);
            });

            if (isSelected) {
                const scArea = parentScene?.area || { x: 0, y: 0, w: 1, h: 1 };
                attachHandles({
                    area,
                    color: colHex,
                    minW: 0.05,
                    minH: 0.05,
                    maxRight: scArea.x + scArea.w,
                    maxBottom: scArea.y + scArea.h,
                    clampMinX: scArea.x,
                    clampMinY: scArea.y,
                    onUpdateVisuals: (cur) => {
                        rect.setAttribute("x", String(cur.x * width));
                        rect.setAttribute("y", String(cur.y * height));
                        rect.setAttribute("width", String(cur.w * width));
                        rect.setAttribute("height", String(cur.h * height));
                        text.setAttribute("x", String(cur.x * width + 4));
                        text.setAttribute("y", String(cur.y * height + cur.h * height - 6));
                    },
                    onCommit: (cur) => {
                        try {
                            authoringStore.resizeCharacter(inst.instance_id, cur.w, cur.h);
                        } catch (err) {
                            console.error("Resize character failed:", err);
                            renderStageOverlay();
                        }
                    }
                });
            }
        });

    }

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
    return {
        state,
        client,
        ready,
        generateOne,
        generateGlobal,
        getGenerationScope: () => generationScope,
        setGenerationScope,
        refresh: renderStatus,
        refreshCatalog,
        renderForm,
        renderStageOverlay,
        getStageMode: () => stageMode,
        setStageMode,
        getStageLayer: () => stageLayer,
        setStageLayer,
        getArtworkVisible: () => artworkVisible,
        setArtworkVisible: (val) => { artworkVisible = Boolean(val); syncPreviewGeometry(); renderStatus(); renderStageOverlay(); },
        getRegionsVisible: () => regionsVisible,
        setRegionsVisible: (val) => { regionsVisible = Boolean(val); syncPreviewGeometry(); renderStatus(); renderStageOverlay(); },
        dispose() {
            if (pollTimer) clearTimeout(pollTimer);
            if (state.preview.url) URL.revokeObjectURL(state.preview.url);
        }
    };
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
    const instances = page.character_instances || [];
    if (instances.length === 0) {
        if (page.scenes.some(scene => scene.input_mode === "cast")) {
            throw new Error("A CAST Scene requires one placed Character Instance");
        }
        if (page.scenes.some(scene => scene.input_mode !== undefined && scene.input_mode !== "simple")) {
            throw new Error("Scene Layout currently supports simple Scenes only");
        }
    } else {
        if (instances.length > 2) {
            throw new Error("Scenes generation currently supports at most two placed Character Instances.");
        }
        const scenesWithInstances = new Set();
        const activeReferences = new Set();
        const castList = page.cast || [];
        for (const instance of instances) {
            const parentScene = page.scenes.find(s => s.scene_id === instance.scene_id);
            if (!parentScene) {
                throw new Error(`Character Instance references unknown Scene: ${instance.scene_id || "none"}`);
            }
            if (parentScene.input_mode !== "cast") {
                throw new Error("Character Instance requires its parent Scene to use CAST mode");
            }
            scenesWithInstances.add(instance.scene_id);
            const cast = castList.find(entry => entry.cast_id === instance.cast_id);
            if (!cast) {
                throw new Error(`Character Instance references unavailable CAST: ${instance.cast_id || "none"}`);
            }
            if (!isRectWithinScene(parentScene.area, instance.area)) {
                throw new Error("Character Instance area must be a normalized rectangle inside its parent Scene");
            }
            if (cast.reference_asset) {
                activeReferences.add(cast.reference_asset);
            }
        }
        if (activeReferences.size > 1) {
            throw new Error("Scenes generation currently supports at most one active Character Reference across instances.");
        }
        for (const s of page.scenes) {
            if (!scenesWithInstances.has(s.scene_id)) {
                if (s.input_mode !== undefined && s.input_mode !== "simple") {
                    throw new Error(`All scenes without a placed CAST appearance must use simple text conditioning (switch '${s.name || s.scene_id}' to Simple)`);
                }
            }
        }
    }
    const activeGuide = (page.guides || []).find(g => g && g.enabled !== false);
    if (activeGuide) {
        const cnet = catalog.scene_generation?.controlnet;
        if (!cnet?.available) {
            throw new Error("Active structural guide requires ControlNet capability, which is unavailable from the backend. Disable the guide to proceed without it.");
        }
    }
    let hasReference = false;
    if (instances.length > 0) {
        const castList = page.cast || [];
        hasReference = instances.some(inst => {
            const cast = castList.find(c => c.cast_id === inst.cast_id);
            return !!cast?.reference_asset;
        });
        if (hasReference) {
            const ref = catalog.scene_generation?.reference;
            if (!ref?.available) {
                throw new Error("Character Reference requires IP-Adapter runtime, which is unavailable from the backend");
            }
        }
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
        panel_strength: Number(state.sceneDraft?.panel_strength ?? 1),
        ...(activeGuide ? {
            controlnet_strength: Number(state.sceneDraft?.controlnet_strength ?? 0.35),
            controlnet_start_percent: Number(state.sceneDraft?.controlnet_start_percent ?? 0.0),
            controlnet_end_percent: Number(state.sceneDraft?.controlnet_end_percent ?? 1.0)
        } : {}),
        ...(hasReference ? {
            reference_weight: Number(state.sceneDraft?.reference_weight ?? 0.70),
            reference_start: Number(state.sceneDraft?.reference_start ?? 0.0),
            reference_end: Number(state.sceneDraft?.reference_end ?? 1.0)
        } : {})
    };
}

function isRectWithinScene(sceneArea, instanceArea) {
    const read = area => {
        if (!area || typeof area !== "object" || (area.shape_type ?? "rect") !== "rect") return null;
        const { x, y, w, h } = area;
        if (![x, y, w, h].every(value => typeof value === "number" && Number.isFinite(value))) return null;
        if (x < 0 || y < 0 || w <= 0 || h <= 0 || x + w > 1.0001 || y + h > 1.0001) return null;
        return { x, y, w, h };
    };
    const parent = read(sceneArea);
    const child = read(instanceArea);
    if (!parent || !child) return false;
    const tolerance = 0.0001;
    return child.x >= parent.x - tolerance && child.y >= parent.y - tolerance &&
        child.x + child.w <= parent.x + parent.w + tolerance &&
        child.y + child.h <= parent.y + parent.h + tolerance;
}
