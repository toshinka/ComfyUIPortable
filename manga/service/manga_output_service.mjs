/**
 * Manga output naming, named copies, Grid artifacts and the fixed output-folder shortcut
 * (Card MANGA-EXPERIMENT-OUTPUT-PRODUCTION1).
 *
 * Boundaries:
 *   - One storage root: the existing Tegaki output directory (TEGAKI_MANGA_OUTPUT_DIR or
 *     <portable>/output/Tegaki, same formula as MangaDomainRuntime).  Named copies go to
 *     <root>/Manga/Named, Grids to <root>/Manga/Grids.  Owned job outputs
 *     (<root>/Manga/Playable/<job>_NNNNN_.png) and SceneResult manifests are never touched.
 *   - The browser never supplies a path.  Names are rendered from a template whose token
 *     values come from the job record (checkpoint, first resolved LoRA, effective seed).
 *   - Never overwrite: exclusive create ('wx') with deterministic _001.._999 suffixes.
 *   - Folder shortcut: fixed directory, explorer.exe only, Windows only, no shell.
 */
import fs from "node:fs";
import path from "node:path";
import { spawn } from "node:child_process";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

export const FILENAME_TOKENS = Object.freeze(["checkpoint", "first_lora", "suffix", "seed", "index", "axis", "date", "time"]);
export const DEFAULT_FILENAME_TEMPLATE = "{checkpoint}_{first_lora}_{suffix}_{seed}";
export const MAX_TEMPLATE_CHARS = 200;
export const MAX_BASENAME_CHARS = 150;
const TOKEN_LIMITS = { checkpoint: 80, first_lora: 80, suffix: 40, seed: 10, index: 3, axis: 60, date: 8, time: 6 };
const WINDOWS_INVALID = /[<>:"/\\|?*\u0000-\u001f]/g;
const WINDOWS_RESERVED = /^(con|prn|aux|nul|com[1-9]|lpt[1-9])(\..*)?$/i;
const PNG_SIGNATURE = Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]);
export const MAX_GRID_BYTES = 64 * 1024 * 1024;

export class MangaOutputError extends Error {
    constructor(code, message, status = 400) {
        super(message);
        this.code = code;
        this.status = status;
    }
}
const fail = (code, message, status) => { throw new MangaOutputError(code, message, status); };

export function resolveMangaOutputDir({ env = process.env, portableRoot = path.resolve(__dirname, "..", "..") } = {}) {
    const configured = env.TEGAKI_MANGA_OUTPUT_DIR?.trim();
    return path.resolve(configured || path.join(portableRoot, "output", "Tegaki"));
}

/** Replace only Windows-invalid characters; keep Unicode.  Bounded length. */
export function sanitizeFilenamePart(value, max = 80) {
    let text = String(value ?? "").normalize("NFC").replace(WINDOWS_INVALID, "_");
    text = Array.from(text).slice(0, max).join("");
    return text;
}

export function stemOf(id) {
    const base = String(id ?? "").split(/[\\/]/).pop();
    return base.replace(/\.(safetensors|ckpt|pt|pth|bin|sft|gguf)$/i, "");
}

/** Validate a template before any expensive work: known tokens only, bounded, no path parts. */
export function validateTemplate(template) {
    if (typeof template !== "string") return "Filename template must be text";
    if (!template.trim()) return "Filename template is empty";
    if (template.length > MAX_TEMPLATE_CHARS) return `Filename template exceeds ${MAX_TEMPLATE_CHARS} characters`;
    const unknown = [...template.matchAll(/\{([^{}]*)\}/g)].map(m => m[1]).filter(name => !FILENAME_TOKENS.includes(name));
    if (unknown.length) return `Unknown filename token: {${unknown[0]}}`;
    if (/[{}]/.test(template.replace(/\{[a-z_]+\}/g, ""))) return "Unbalanced { } in filename template";
    return "";
}

function pad(n, width) { return String(n).padStart(width, "0"); }

/**
 * Render a base filename (no extension).  Token values are sanitized and bounded; runs of
 * underscores left by empty tokens collapse to one; leading/trailing separators, dots and
 * spaces are trimmed; reserved device names are prefixed with '_'; empty result -> "manga".
 */
export function renderFilenameBase(template, values = {}, { now = new Date() } = {}) {
    const problem = validateTemplate(template);
    if (problem) fail("INVALID_TEMPLATE", problem, 400);
    const tokens = {
        checkpoint: stemOf(values.checkpoint_id ?? ""),
        first_lora: values.first_lora ?? "",
        suffix: values.suffix ?? "",
        seed: values.seed == null ? "" : String(values.seed),
        index: values.index == null ? "" : pad(values.index, 3),
        axis: values.axis ?? "",
        date: `${now.getFullYear()}${pad(now.getMonth() + 1, 2)}${pad(now.getDate(), 2)}`,
        time: `${pad(now.getHours(), 2)}${pad(now.getMinutes(), 2)}${pad(now.getSeconds(), 2)}`,
    };
    let text = template.replace(/\{([a-z_]+)\}/g, (_, name) => sanitizeFilenamePart(tokens[name], TOKEN_LIMITS[name]));
    text = sanitizeFilenamePart(text, MAX_TEMPLATE_CHARS * 2)
        .replace(/_{2,}/g, "_")
        .replace(/^[\s._-]+|[\s._-]+$/g, "");
    text = Array.from(text).slice(0, MAX_BASENAME_CHARS).join("").replace(/[\s.]+$/g, "");
    if (!text) text = "manga";
    if (WINDOWS_RESERVED.test(text)) text = `_${text}`;
    return text;
}

/** Exclusive create: <base>.png, then <base>_001.png .. _999.png.  Never overwrites. */
export function writeExclusive(dir, base, bytes, { fsImpl = fs } = {}) {
    fsImpl.mkdirSync(dir, { recursive: true });
    for (let n = 0; n < 1000; n++) {
        const name = n === 0 ? `${base}.png` : `${base}_${pad(n, 3)}.png`;
        const target = path.join(dir, name);
        if (path.dirname(target) !== path.resolve(dir)) fail("INVALID_NAME", "Filename escapes the output folder", 400);
        let fd;
        try {
            fd = fsImpl.openSync(target, "wx");
        } catch (error) {
            if (error.code === "EEXIST") continue;
            fail("OUTPUT_WRITE_FAILED", `Output could not be written (${error.code || "error"})`, 500);
        }
        try { fsImpl.writeSync(fd, bytes); } finally { fsImpl.closeSync(fd); }
        return { filename: name, path: target };
    }
    fail("OUTPUT_COLLISION_EXHAUSTED", "999 files with this name already exist", 409);
}

function isPng(bytes) {
    return Buffer.isBuffer(bytes) && bytes.length > PNG_SIGNATURE.length && bytes.subarray(0, 8).equals(PNG_SIGNATURE);
}

/** Values for naming from a verified job record (never from the browser). */
export function namingValuesFromJob(job) {
    const effective = job?.effective_settings || {};
    const requested = job?.requested_settings || {};
    const first = Array.isArray(job?.resolved_loras) ? job.resolved_loras[0] : null;
    return {
        checkpoint_id: typeof effective.checkpoint_id === "string" ? effective.checkpoint_id : (requested.checkpoint_id || ""),
        first_lora: first && typeof first.id === "string" ? stemOf(first.id) : "",
        seed: effective.seed_requested ?? requested.seed_requested ?? "",
    };
}

function checkClientNaming(input) {
    if (!input || typeof input !== "object" || Array.isArray(input)) fail("INVALID_REQUEST", "Naming request must be an object", 400);
    const template = input.template ?? DEFAULT_FILENAME_TEMPLATE;
    const problem = validateTemplate(template);
    if (problem) fail("INVALID_TEMPLATE", problem, 400);
    const suffix = input.suffix ?? "";
    if (typeof suffix !== "string" || suffix.length > 200) fail("INVALID_SUFFIX", "Suffix must be text up to 200 characters", 400);
    const index = input.index ?? null;
    if (index !== null && (!Number.isSafeInteger(index) || index < 1 || index > 999)) fail("INVALID_INDEX", "Index must be 1..999", 400);
    const axis = input.axis ?? "";
    if (typeof axis !== "string" || axis.length > 400) fail("INVALID_AXIS", "Axis fragment must be text up to 400 characters", 400);
    return { template, suffix, index, axis };
}

export class MangaOutputService {
    constructor({ outputDir = resolveMangaOutputDir(), generationService = null, platform = process.platform,
                  spawnFn = spawn, fsImpl = fs, clock = () => new Date() } = {}) {
        this.outputDir = path.resolve(outputDir);
        this.generationService = generationService;
        this.platform = platform;
        this.spawnFn = spawnFn;
        this.fs = fsImpl;
        this.clock = clock;
    }

    get namedDir() { return path.join(this.outputDir, "Manga", "Named"); }
    get gridDir() { return path.join(this.outputDir, "Manga", "Grids"); }

    /** Pure preview: token values are supplied (e.g. from a compile-only result). No filesystem. */
    preview(input) {
        const naming = checkClientNaming(input);
        const checkpoint_id = typeof input.checkpoint_id === "string" ? input.checkpoint_id : "";
        const first_lora = typeof input.first_lora === "string" ? stemOf(input.first_lora) : "";
        const seed = typeof input.seed === "string" || Number.isSafeInteger(input.seed) ? String(input.seed) : "";
        const base = renderFilenameBase(naming.template, { checkpoint_id, first_lora, seed, ...naming }, { now: this.clock() });
        return { base, filename: `${base}.png`, folder: "Manga/Named" };
    }

    /** Copy a verified SUCCEEDED job result to Manga/Named under the rendered name. */
    async namedCopy(input) {
        const naming = checkClientNaming(input);
        const jobId = input?.job_id;
        if (typeof jobId !== "string") fail("INVALID_JOB_ID", "job_id is required", 400);
        if (!this.generationService) fail("SERVICE_UNAVAILABLE", "Generation service is unavailable", 503);
        const job = await this.generationService.getJob(jobId);
        if (job?.state !== "SUCCEEDED") fail("RESULT_NOT_READY", "Only a verified SUCCEEDED job can be named", 409);
        const bytes = await this.generationService.getResult(jobId);
        if (!isPng(bytes)) fail("OUTPUT_INVALID", "Job result is not a PNG", 502);
        const base = renderFilenameBase(naming.template, { ...namingValuesFromJob(job), ...naming }, { now: this.clock() });
        const written = writeExclusive(this.namedDir, base, bytes, { fsImpl: this.fs });
        return { filename: written.filename, folder: "Manga/Named" };
    }

    /** Save a browser-composed Grid PNG.  The label is a filename fragment, never a path. */
    saveGrid(bytes, label) {
        if (!isPng(bytes)) fail("INVALID_PNG", "Grid body must be a PNG", 400);
        if (bytes.length > MAX_GRID_BYTES) fail("GRID_TOO_LARGE", "Grid exceeds 64 MiB", 413);
        if (typeof label !== "string" || label.length > 300) fail("INVALID_LABEL", "Grid label must be text up to 300 characters", 400);
        const base = renderFilenameBase("{axis}_grid", { axis: label || "experiment" }, { now: this.clock() });
        const written = writeExclusive(this.gridDir, base, bytes, { fsImpl: this.fs });
        return { filename: written.filename, folder: "Manga/Grids" };
    }

    /** The only directory the shortcut can open: <root>/Manga if present, else <root>. */
    folderTarget() {
        const manga = path.join(this.outputDir, "Manga");
        if (this.fs.existsSync(manga) && this.fs.statSync(manga).isDirectory()) return manga;
        if (this.fs.existsSync(this.outputDir) && this.fs.statSync(this.outputDir).isDirectory()) return this.outputDir;
        return null;
    }

    async openFolder() {
        if (this.platform !== "win32") fail("UNSUPPORTED_PLATFORM", "Opening the output folder is available on Windows only", 501);
        const target = this.folderTarget();
        if (!target) fail("OUTPUT_DIR_MISSING", "The Tegaki output folder does not exist yet", 404);
        await new Promise((resolve, reject) => {
            let child;
            try {
                child = this.spawnFn("explorer.exe", [target], { detached: true, stdio: "ignore", shell: false, windowsHide: false });
            } catch (error) {
                reject(new MangaOutputError("EXPLORER_FAILED", `Explorer could not be started (${error.code || "error"})`, 500));
                return;
            }
            child.once("error", error => reject(new MangaOutputError("EXPLORER_FAILED", `Explorer could not be started (${error.code || "error"})`, 500)));
            child.once("spawn", () => { try { child.unref?.(); } catch {} resolve(); });
        });
        return { opened: true, folder: path.relative(this.outputDir, target).replaceAll("\\", "/") || "." };
    }
}
