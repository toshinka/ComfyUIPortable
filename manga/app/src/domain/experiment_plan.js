/**
 * Manga experiment planning (Card MANGA-EXPERIMENT-OUTPUT-PRODUCTION1).
 *
 * Pure, DOM-free contracts shared by the Experiment / Output panel and its tests:
 *   - Owner sampler/scheduler presets classified ONLY against the live capability catalog
 *   - bounded X/Y/Z Cartesian plans (X fastest, then Y, then Z; hard cap 64 cells)
 *   - literal Prompt S/R (no regex), per-cell derived generation settings
 *   - deterministic Grid page/slot layout
 *
 * Experiment state is session/application state.  Nothing here reads or writes the
 * Authoring Document: every cell is a derived copy of the normal Global generation
 * settings, compiled and submitted through the existing compile/job contracts.
 */

export const EXPERIMENT_MAX_CELLS = 64;
export const AXIS_KEYS = Object.freeze(["x", "y", "z"]);
export const AXIS_TYPES = Object.freeze(["none", "checkpoint", "sampler", "scheduler", "steps", "cfg", "seed", "prompt_sr"]);
export const AXIS_LABELS = Object.freeze({
    none: "Off", checkpoint: "Checkpoint", sampler: "Sampler", scheduler: "Scheduler",
    steps: "Steps", cfg: "CFG", seed: "Seed", prompt_sr: "Prompt S/R"
});
const INTEGER = /^(0|[1-9][0-9]*)$/;
const SEED_MAX = 4294967295;

/*
 * Owner presets.  `ids` lists ONLY runtime IDs verified in the capability audit of this Card
 * (ComfyUI KSampler catalog on the Manga backend).  Parts whose algorithm has no verified runtime
 * ID carry an empty list and are therefore UNAVAILABLE — never mapped to a look-alike algorithm.
 * A part with `keep: true` intentionally leaves that control untouched.
 */
export const SAMPLER_PRESETS = Object.freeze([
    { id: "smea_dy_sgm_uniform", group: "Normal", label: "Euler SMEA dy + SGM Uniform",
        sampler: { label: "Euler SMEA dy", ids: [] }, scheduler: { label: "SGM Uniform", ids: ["sgm_uniform"] } },
    { id: "euler_negative_simple", group: "Normal", label: "Euler Negative + Simple",
        sampler: { label: "Euler Negative", ids: [] }, scheduler: { label: "Simple", ids: ["simple"] } },
    { id: "dpm2_phi", group: "Normal", label: "DPM2 + Phi",
        sampler: { label: "DPM2", ids: ["dpm_2"] }, scheduler: { label: "Phi", ids: [] } },
    { id: "euler_negative_ays11", group: "Normal", label: "Euler Negative family + AYS 11",
        sampler: { label: "Euler Negative family", ids: [] }, scheduler: { label: "AYS 11", ids: [] } },
    { id: "euler_cosine", group: "Research", label: "Euler + Cosine",
        sampler: { label: "Euler", ids: ["euler"] }, scheduler: { label: "Cosine", ids: [] } },
    { id: "euler_negative_invcos_sf", group: "Research", label: "Euler Negative + Invcosinusoidal SF",
        sampler: { label: "Euler Negative", ids: [] }, scheduler: { label: "Invcosinusoidal SF", ids: [] } },
    { id: "ays_gits", group: "Special", label: "AYS GITS",
        sampler: { label: "(keep current sampler)", ids: [], keep: true }, scheduler: { label: "AYS GITS", ids: [] } },
]);

export const PRESET_STATUS = Object.freeze({
    SUPPORTED: "SUPPORTED", PARTIAL: "PARTIALLY SUPPORTED", UNAVAILABLE: "UNAVAILABLE"
});

/** Classify one preset against the live catalog.  Exact ID membership only. */
export function classifyPreset(preset, catalog) {
    const samplers = new Set(Array.isArray(catalog?.samplers) ? catalog.samplers : []);
    const schedulers = new Set(Array.isArray(catalog?.schedulers) ? catalog.schedulers : []);
    const parts = [];
    for (const [field, pool] of [["sampler_id", samplers], ["scheduler_id", schedulers]]) {
        const spec = field === "sampler_id" ? preset.sampler : preset.scheduler;
        if (!spec || spec.keep) continue;
        const id = spec.ids.find(candidate => pool.has(candidate)) || null;
        parts.push({ field, label: spec.label, id, available: id !== null });
    }
    const available = parts.filter(part => part.available);
    const status = parts.length && available.length === parts.length ? PRESET_STATUS.SUPPORTED
        : available.length ? PRESET_STATUS.PARTIAL : PRESET_STATUS.UNAVAILABLE;
    const missing = parts.filter(part => !part.available).map(part => part.label);
    return {
        id: preset.id, label: preset.label, group: preset.group, status, parts,
        apply: Object.fromEntries(available.map(part => [part.field, part.id])),
        missing,
        reason: status === PRESET_STATUS.SUPPORTED ? "" :
            `Not in the runtime catalog: ${missing.join(", ")}`
    };
}

export function classifyPresets(catalog, presets = SAMPLER_PRESETS) {
    return presets.map(preset => classifyPreset(preset, catalog));
}

/**
 * The exact control changes a preset application may make.  SUPPORTED applies every part.
 * PARTIAL applies only when the Owner explicitly asks for the available part(s); the
 * unavailable part is never substituted and the control keeps its current value.
 */
export function presetChanges(classified, { allowPartial = false } = {}) {
    if (classified.status === PRESET_STATUS.SUPPORTED) return { ok: true, changes: { ...classified.apply }, partial: false };
    if (classified.status === PRESET_STATUS.PARTIAL && allowPartial) {
        return { ok: true, changes: { ...classified.apply }, partial: true, missing: [...classified.missing] };
    }
    return { ok: false, changes: {}, reason: classified.reason || "Preset is unavailable" };
}

// ---------------------------------------------------------------------------------------------
// Axis parsing

export function stemOf(id) {
    const base = String(id ?? "").split(/[\\/]/).pop();
    return base.replace(/\.(safetensors|ckpt|pt|pth|bin|sft|gguf)$/i, "");
}

function splitList(text) {
    return String(text ?? "").split(/[,\n]/).map(item => item.trim()).filter(Boolean);
}

function numericBound(catalog, field) {
    const product = catalog?.product_bounds?.[field] || {};
    const backend = catalog?.backend_bounds?.[field] || {};
    return {
        min: Math.max(Number(product.min ?? -Infinity), Number(backend.min ?? -Infinity)),
        max: Math.min(Number(product.max ?? Infinity), Number(backend.max ?? Infinity)),
    };
}

/**
 * Parse one axis definition into concrete values.
 * spec: { type, values?: string[] (select types), text?: string (numeric), search?, replacements? }
 * -> { type, enabled, values: [{ value, label, fragment }], error }
 */
export function parseAxis(spec, catalog) {
    const type = AXIS_TYPES.includes(spec?.type) ? spec.type : "none";
    if (type === "none") return { type, enabled: false, values: [null], error: "" };
    const fail = error => ({ type, enabled: true, values: [], error });
    let values = [];
    if (type === "checkpoint") {
        const available = new Set((catalog?.checkpoints || []).filter(entry => entry.available === true).map(entry => entry.id));
        for (const id of spec.values || []) {
            if (!available.has(id)) return fail(`Checkpoint unavailable: ${id}`);
            values.push({ value: id, label: stemOf(id), fragment: stemOf(id) });
        }
    } else if (type === "sampler" || type === "scheduler") {
        const pool = new Set(catalog?.[type === "sampler" ? "samplers" : "schedulers"] || []);
        for (const id of spec.values || []) {
            if (!pool.has(id)) return fail(`${AXIS_LABELS[type]} not in runtime catalog: ${id}`);
            values.push({ value: id, label: id, fragment: id });
        }
    } else if (type === "steps") {
        const bound = numericBound(catalog, "steps");
        for (const raw of splitList(spec.text)) {
            if (!INTEGER.test(raw) || Number(raw) < bound.min || Number(raw) > bound.max) {
                return fail(`Steps value '${raw}' must be a whole number ${bound.min}..${bound.max}`);
            }
            values.push({ value: Number(raw), label: raw, fragment: `s${raw}` });
        }
    } else if (type === "cfg") {
        const bound = numericBound(catalog, "cfg");
        for (const raw of splitList(spec.text)) {
            const n = Number(raw);
            if (!/^[+]?(\d+(\.\d*)?|\.\d+)$/.test(raw) || !Number.isFinite(n) || n < bound.min || n > bound.max) {
                return fail(`CFG value '${raw}' must be a number ${bound.min}..${bound.max}`);
            }
            values.push({ value: n, label: String(n), fragment: `cfg${n}` });
        }
    } else if (type === "seed") {
        for (const raw of splitList(spec.text)) {
            if (raw !== "-1" && (!INTEGER.test(raw) || Number(raw) > SEED_MAX)) {
                return fail(`Seed value '${raw}' must be -1 or 0..${SEED_MAX}`);
            }
            values.push({ value: raw, label: raw === "-1" ? "random" : raw, fragment: raw === "-1" ? "rand" : raw });
        }
    } else if (type === "prompt_sr") {
        const search = String(spec.search ?? "");
        if (!search.trim()) return fail("Prompt S/R needs a Search string");
        const replacements = String(spec.replacements ?? "").split("\n").map(line => line.replace(/\r$/, ""))
            .filter(line => line.trim() !== "");
        for (const replacement of replacements) {
            values.push({ value: replacement, search, label: replacement, fragment: replacement });
        }
    }
    if (!values.length) return fail(`${AXIS_LABELS[type]} axis has no values`);
    const seen = new Set();
    for (const entry of values) {
        const key = JSON.stringify(entry.value);
        if (seen.has(key)) return fail(`${AXIS_LABELS[type]} axis repeats '${entry.label}'`);
        seen.add(key);
    }
    return { type, enabled: true, values, error: "" };
}

/**
 * Expand an experiment definition.  Order: X changes fastest, then Y, then Z.
 * index = x + nx * (y + ny * z).  The same order drives execution, results, grid slots
 * and {index} naming.  Over-cap plans are BLOCKED (never truncated).
 */
export function expandExperiment(definition, catalog, { maxCells = EXPERIMENT_MAX_CELLS } = {}) {
    const axes = AXIS_KEYS.map(key => ({ key, ...parseAxis(definition?.[key], catalog) }));
    const counts = Object.fromEntries(axes.map(axis => [axis.key, axis.enabled ? axis.values.length : 1]));
    const total = counts.x * counts.y * counts.z;
    const result = { axes, counts, total, cells: [], blocked: "" };
    const typed = axes.filter(axis => axis.enabled && axis.type !== "prompt_sr").map(axis => axis.type);
    const axisError = axes.find(axis => axis.error);
    if (axisError) result.blocked = `${axisError.key.toUpperCase()}: ${axisError.error}`;
    else if (new Set(typed).size !== typed.length) result.blocked = "Two axes change the same setting; use each setting on one axis only.";
    else if (!axes.some(axis => axis.enabled)) result.blocked = "Enable at least one axis.";
    else if (total > maxCells) {
        result.blocked = `${counts.x} × ${counts.y} × ${counts.z} = ${total} cells exceeds the ${maxCells}-cell limit. Remove values; nothing is truncated.`;
    }
    if (result.blocked) return result;
    for (let z = 0; z < counts.z; z++) {
        for (let y = 0; y < counts.y; y++) {
            for (let x = 0; x < counts.x; x++) {
                const pick = { x, y, z };
                const index = x + counts.x * (y + counts.y * z);
                const assignments = axes.filter(axis => axis.enabled)
                    .map(axis => ({ axis: axis.key, type: axis.type, ...axis.values[pick[axis.key]] }));
                result.cells.push({ index, x, y, z, assignments });
            }
        }
    }
    return result;
}

/** Literal replace-all (no regex, no special replacement patterns). */
export function literalReplaceAll(text, search, replacement) {
    if (!search) return { text, count: 0 };
    const parts = String(text).split(search);
    return { text: parts.join(replacement), count: parts.length - 1 };
}

/**
 * Derive one cell's generation settings from the base Global settings.  The base object is
 * never mutated.  A Prompt S/R whose Search string is absent at application time makes the
 * cell invalid instead of silently producing an unchanged prompt.
 */
export function deriveCellSettings(base, cell) {
    const settings = { ...base };
    const notes = [];
    for (const assignment of cell.assignments) {
        switch (assignment.type) {
            case "checkpoint": settings.checkpoint_id = assignment.value; break;
            case "sampler": settings.sampler_id = assignment.value; break;
            case "scheduler": settings.scheduler_id = assignment.value; break;
            case "steps": settings.steps = assignment.value; break;
            case "cfg": settings.cfg = assignment.value; break;
            case "seed": settings.seed_requested = assignment.value; break;
            case "prompt_sr": {
                const positive = literalReplaceAll(settings.positive_raw, assignment.search, assignment.value);
                const negative = literalReplaceAll(settings.negative_raw, assignment.search, assignment.value);
                if (positive.count + negative.count === 0) {
                    return { ok: false, settings: null,
                        error: `Prompt S/R (${assignment.axis.toUpperCase()}): Search string not found: ${assignment.search}` };
                }
                settings.positive_raw = positive.text;
                settings.negative_raw = negative.text;
                notes.push({ axis: assignment.axis, replaced: positive.count + negative.count });
                break;
            }
            default: return { ok: false, settings: null, error: `Unsupported axis type ${assignment.type}` };
        }
    }
    return { ok: true, settings, notes, error: "" };
}

/** Short human label of a cell's axis values (for results, grid captions, filename fragment). */
export function cellCaption(cell, { max = 48 } = {}) {
    return cell.assignments.map(item => {
        const label = String(item.label ?? "");
        return `${item.axis.toUpperCase()}=${label.length > max ? `${label.slice(0, max - 1)}…` : label}`;
    }).join(" · ");
}

export function cellFragment(cell) {
    return cell.assignments.map(item => String(item.fragment ?? "").slice(0, 24)).join("-");
}

/** First effective LoRA from a compile/job result: backend generation order, never card order. */
export function firstLoraFromResolved(resolvedLoras) {
    const first = Array.isArray(resolvedLoras) ? resolvedLoras[0] : null;
    return first && typeof first.id === "string" ? stemOf(first.id) : "";
}

// ---------------------------------------------------------------------------------------------
// Grid layout

/**
 * Grid page rule (documented, bounded):
 *   - exactly one enabled axis -> ONE compact grid; cols = n <= 4 ? n : ceil(sqrt(n)), cells row-major
 *   - two or more enabled axes -> ONE grid PER Z value; columns = X values, rows = Y values
 * Slots are addressed by cell index, so a failed cell keeps its own position.
 */
export function planGridPages(plan) {
    const enabled = plan.axes.filter(axis => axis.enabled);
    if (enabled.length <= 1) {
        const n = plan.cells.length;
        const cols = n <= 4 ? Math.max(1, n) : Math.ceil(Math.sqrt(n));
        return [{ page: 0, title: "", cols, rows: Math.ceil(n / cols),
            slots: plan.cells.map((cell, i) => ({ index: cell.index, col: i % cols, row: Math.floor(i / cols) })) }];
    }
    const zAxis = plan.axes.find(axis => axis.key === "z");
    const pages = [];
    for (let z = 0; z < plan.counts.z; z++) {
        pages.push({
            page: z,
            title: zAxis.enabled ? `Z=${zAxis.values[z].label}` : "",
            cols: plan.counts.x, rows: plan.counts.y,
            slots: plan.cells.filter(cell => cell.z === z).map(cell => ({ index: cell.index, col: cell.x, row: cell.y }))
        });
    }
    return pages;
}

/**
 * Pixel geometry for one page.  Every slot is max(width) × max(height) of the page's successful
 * images; each image is drawn at its natural size, centred (never stretched).  If the canvas would
 * exceed the bounds, ONE uniform scale factor is applied to the whole page (aspect preserved).
 * sizes: Map/obj index -> { width, height } for successful cells only.
 */
export function gridGeometry(page, sizes, { labels = true, gap = 8, labelHeight = 36, titleHeight = 40,
    maxSide = 16384, maxPixels = 120_000_000, fallback = { width: 512, height: 512 } } = {}) {
    const get = index => (sizes instanceof Map ? sizes.get(index) : sizes?.[index]) || null;
    const known = page.slots.map(slot => get(slot.index)).filter(Boolean);
    const cellW = known.length ? Math.max(...known.map(size => size.width)) : fallback.width;
    const cellH = known.length ? Math.max(...known.map(size => size.height)) : fallback.height;
    const capH = labels ? labelHeight : 0;
    const topH = labels && page.title ? titleHeight : 0;
    const width = page.cols * cellW + (page.cols + 1) * gap;
    const height = topH + page.rows * (cellH + capH) + (page.rows + 1) * gap;
    const scale = Math.min(1, maxSide / width, maxSide / height, Math.sqrt(maxPixels / (width * height)));
    const slots = page.slots.map(slot => {
        const x = gap + slot.col * (cellW + gap);
        const y = topH + gap + slot.row * (cellH + capH + gap);
        const size = get(slot.index);
        return {
            index: slot.index, col: slot.col, row: slot.row, x, y, w: cellW, h: cellH + capH,
            caption: labels ? { x, y, w: cellW, h: capH } : null,
            image: size ? { x: x + Math.floor((cellW - size.width) / 2), y: y + capH + Math.floor((cellH - size.height) / 2),
                w: size.width, h: size.height } : null
        };
    });
    return { width, height, scale, outWidth: Math.max(1, Math.round(width * scale)),
        outHeight: Math.max(1, Math.round(height * scale)), cellW, cellH, captionH: capH, titleH: topH, slots };
}
