/**
 * LegacyReforgeAdapter (Card MANGA-LEGACY-EASYREFORGE-VERTICAL-MVP1).
 *
 * Pure translation between the backend-neutral Manga recipe and the Legacy EasyReforge
 * (stable-diffusion-webui-reForge) txt2img API.  No process ownership, no I/O.
 *
 * Contract highlights:
 *   - The Manga recipe is logical: canonical Manga resource IDs, the user's raw prompt text
 *     with Manga `<lora:name:weight>` tokens, Manga/Comfy or native Legacy sampling names.
 *   - LoRAs: every Manga token is resolved to exactly one Legacy LoRA and rewritten IN PLACE
 *     (position = order preserved) with the weight text copied verbatim.  The user's prompt is
 *     never mutated; the adapter returns a derived request prompt.
 *   - Checkpoint / VAE / LoRA mapping is deterministic by relative resource path; zero or
 *     several candidates fail closed.  No family filtering, no basename-only guessing.
 *   - Sampler / scheduler: a native Legacy value is used as-is; a Manga/Comfy id is accepted
 *     only through the explicit equivalence table below and only if the target exists in the
 *     live Legacy catalog.  Anything else fails closed (no silent substitution).
 *   - Persisted Manga state never contains ReForge script_args, Gradio IDs or positional
 *     parameters; those exist only in the payload built here.
 */

export const BACKEND_ID = "easyreforge";

export class LegacyReforgeError extends Error {
    constructor(code, message, status = 422) {
        super(message);
        this.code = code;
        this.status = status;
    }
}
const fail = (code, message, status) => { throw new LegacyReforgeError(code, message, status); };

/** Manga/Comfy sampler id -> Legacy (A1111/ReForge) sampler display name.  Explicit only. */
export const COMFY_TO_LEGACY_SAMPLER = Object.freeze({
    euler: "Euler",
    euler_ancestral: "Euler a",
    heun: "Heun",
    dpm_2: "DPM2",
    dpm_2_ancestral: "DPM2 a",
    lms: "LMS",
    dpm_fast: "DPM fast",
    dpm_adaptive: "DPM adaptive",
    dpmpp_2s_ancestral: "DPM++ 2S a",
    dpmpp_sde: "DPM++ SDE",
    dpmpp_2m: "DPM++ 2M",
    dpmpp_2m_sde: "DPM++ 2M SDE",
    dpmpp_3m_sde: "DPM++ 3M SDE",
    ddim: "DDIM",
    uni_pc: "UniPC",
    lcm: "LCM",
});

/** Comfy scheduler ids that have a same-named Legacy scheduler (identity only if present). */
export const COMFY_TO_LEGACY_SCHEDULER = Object.freeze({
    simple: "simple", sgm_uniform: "sgm_uniform", karras: "karras", exponential: "exponential",
    beta: "beta", normal: "normal", kl_optimal: "kl_optimal",
});

/**
 * Explicit, bidirectional Manga/Comfy <-> Legacy equivalences that exist in the LIVE Legacy catalog.
 * Used by the GUI to carry the user's logical sampler/scheduler intent across an engine switch;
 * anything not listed here stays as-is and is shown unavailable (never substituted).
 */
export function samplingEquivalents(samplers, schedulers) {
    const present = list => new Set(samplerNames(list));
    const liveSamplers = present(samplers);
    const liveSchedulers = present(schedulers);
    const pick = (table, live) => Object.fromEntries(Object.entries(table).filter(([, legacy]) => live.has(legacy)));
    return { samplers: pick(COMFY_TO_LEGACY_SAMPLER, liveSamplers), schedulers: pick(COMFY_TO_LEGACY_SCHEDULER, liveSchedulers) };
}

/** Manga VAE ids are relative to the Comfy VAE root; the Integration Runtime's Model\VAE is
 *  the `Illustrious` sub-folder of that root.  Only prefixes listed here are translated. */
export const DEFAULT_VAE_PREFIX_MAP = Object.freeze({ "Illustrious/": "" });

const MANGA_LORA = /<lora:([^:<>]+):([+-]?(?:\d+(?:\.\d*)?|\.\d+))>/g;
const ANY_LORA = /<lora:[^<>]*>/gi;
const WILDCARD = /(?<![A-Za-z0-9_])__[^\s_][^\s]*?__/;
const DYNAMIC_CHOICE = /(?<!\\)\{[^{}]*\|[^{}]*\}/;
const MODEL_EXT = /\.(safetensors|ckpt|pt|pth|bin|sft|gguf)$/i;

const norm = value => String(value ?? "").replaceAll("\\", "/").replace(/\/+/g, "/");
const lower = value => norm(value).toLowerCase();
const stem = value => norm(value).split("/").pop().replace(MODEL_EXT, "");

function isInt(value, min, max) {
    return Number.isSafeInteger(value) && value >= min && value <= max;
}

/** Validate the logical recipe.  Returns a frozen normalized copy. */
export function validateRecipe(recipe) {
    if (!recipe || typeof recipe !== "object" || Array.isArray(recipe)) fail("INVALID_RECIPE", "Recipe must be an object", 400);
    const text = (name, max = 64 * 1024, required = false) => {
        const value = recipe[name] ?? "";
        if (typeof value !== "string" || value.length > max) fail("INVALID_RECIPE", `${name} must be text up to ${max} characters`, 400);
        if (required && !value.trim()) fail("INVALID_RECIPE", `${name} is required`, 400);
        return value;
    };
    const out = {
        engine: BACKEND_ID,
        checkpoint_id: text("checkpoint_id", 1024, true),
        vae_id: text("vae_id", 1024),
        positive_raw: text("positive_raw"),
        negative_raw: text("negative_raw"),
        sampler: text("sampler", 128, true),
        scheduler: text("scheduler", 128),
        steps: recipe.steps, cfg: recipe.cfg, width: recipe.width, height: recipe.height,
        seed_requested: String(recipe.seed_requested ?? ""),
    };
    if (recipe.engine !== undefined && recipe.engine !== BACKEND_ID) fail("INVALID_RECIPE", "Recipe engine must be easyreforge", 400);
    if (!isInt(out.steps, 1, 150)) fail("INVALID_RECIPE", "steps must be 1..150", 400);
    if (typeof out.cfg !== "number" || !Number.isFinite(out.cfg) || out.cfg < 0 || out.cfg > 30) fail("INVALID_RECIPE", "cfg must be 0..30", 400);
    for (const side of ["width", "height"]) {
        if (!isInt(out[side], 64, 2048) || out[side] % 8 !== 0) fail("INVALID_RECIPE", `${side} must be a multiple of 8 in 64..2048`, 400);
    }
    if (out.seed_requested !== "-1" && !(/^(0|[1-9][0-9]*)$/.test(out.seed_requested) && Number(out.seed_requested) <= 4294967295)) {
        fail("INVALID_RECIPE", "seed_requested must be -1 or 0..4294967295", 400);
    }
    return Object.freeze(out);
}

/** Ordered Manga LoRA tokens of one prompt side (the logical LoRA recipe). */
export function extractLoraRecipe(text, side = "positive") {
    const source = String(text ?? "");
    const tokens = [];
    for (const match of source.matchAll(MANGA_LORA)) {
        tokens.push({ resource_id: match[1], weight: Number(match[2]), weight_text: match[2],
            order: tokens.length, side, index: match.index, raw: match[0] });
    }
    const strict = new Set(tokens.map(token => token.index));
    for (const any of source.matchAll(ANY_LORA)) {
        if (!strict.has(any.index)) fail("LORA_MALFORMED", `Malformed LoRA token: ${any[0]}`, 422);
    }
    return tokens;
}

function rejectUnsupportedSyntax(text, side) {
    if (WILDCARD.test(text)) fail("WILDCARD_UNSUPPORTED",
        `The ${side} prompt contains a Wildcard; EasyReforge uses a different Wildcard library. Use Expand first.`, 422);
    if (DYNAMIC_CHOICE.test(text)) fail("DYNAMIC_PROMPT_UNSUPPORTED",
        `The ${side} prompt contains {a|b} choices; expand them before generating with EasyReforge.`, 422);
}

function unique(candidates, notFound, ambiguous) {
    if (candidates.length === 1) return candidates[0];
    if (!candidates.length) fail(notFound[0], notFound[1], 422);
    fail(ambiguous[0], ambiguous[1], 422);
}

/** Checkpoint: exact relative-path suffix match against the Legacy catalog filenames. */
export function mapCheckpoint(checkpointId, sdModels) {
    if (!Array.isArray(sdModels)) fail("LEGACY_CATALOG_UNAVAILABLE", "Legacy checkpoint catalog is unavailable", 503);
    const id = lower(checkpointId);
    const candidates = sdModels.filter(model => typeof model?.filename === "string" &&
        (lower(model.filename) === id || lower(model.filename).endsWith(`/${id}`)));
    const model = unique(candidates,
        ["CHECKPOINT_NOT_FOUND", `Checkpoint '${checkpointId}' is not in the EasyReforge catalog`],
        ["CHECKPOINT_AMBIGUOUS", `Checkpoint '${checkpointId}' matches ${candidates.length} EasyReforge models`]);
    const title = typeof model.title === "string" && model.title ? model.title : model.model_name;
    if (typeof title !== "string" || !title) fail("LEGACY_RESPONSE_INVALID", "EasyReforge model entry has no title", 502);
    return { title, filename: model.filename };
}

/**
 * VAE (contract proven from ReForge 19395bf modules/sd_vae.py + processing.py):
 *   resolve_vae(): with opts.sd_vae_overrides_per_model_preferences=True and sd_vae != "Automatic",
 *   the value comes ONLY from resolve_vae_from_setting(); sd_vae="None" -> VaeResolution(vae=None)
 *   -> load_vae(None) restores the checkpoint's own (base) VAE.  "Automatic" instead searches per-model
 *   user metadata and prefix-matching "near checkpoint" files, so it is NOT checkpoint-default.
 *   The request therefore always carries sd_vae_overrides_per_model_preferences=true BEFORE sd_vae
 *   (process_images applies override_settings in insertion order and reloads the VAE on sd_vae).
 *   A --vae-path launch flag overrides everything and makes both semantics unrepresentable.
 * VAE: empty -> "None" (the checkpoint's own VAE; no external VAE is forced).  Explicit ->
 * exactly one Legacy VAE whose relative path equals the Manga id after the configured prefix
 * translation.  Extensionless/virtual Comfy entries cannot be represented and fail closed.
 */
export function mapVae(vaeId, sdVae, prefixMap = DEFAULT_VAE_PREFIX_MAP) {
    const id = norm(vaeId);
    if (!id) return { setting: "None", explicit: false };
    if (!MODEL_EXT.test(id)) fail("VAE_UNSUPPORTED", `VAE '${vaeId}' is not a file resource EasyReforge can load`, 422);
    if (!Array.isArray(sdVae)) fail("LEGACY_CATALOG_UNAVAILABLE", "Legacy VAE catalog is unavailable", 503);
    let relative = null;
    for (const [from, to] of Object.entries(prefixMap)) {
        if (id.toLowerCase().startsWith(from.toLowerCase())) { relative = `${to}${id.slice(from.length)}`; break; }
    }
    if (relative === null) fail("VAE_UNSUPPORTED", `VAE '${vaeId}' is outside the EasyReforge VAE folder`, 422);
    const want = relative.toLowerCase();
    const candidates = sdVae.filter(vae => typeof vae?.filename === "string" && lower(vae.filename).endsWith(`/${want}`));
    const vae = unique(candidates,
        ["VAE_NOT_FOUND", `VAE '${vaeId}' is not in the EasyReforge catalog`],
        ["VAE_AMBIGUOUS", `VAE '${vaeId}' matches ${candidates.length} EasyReforge VAEs`]);
    if (typeof vae.model_name !== "string" || !vae.model_name) fail("LEGACY_RESPONSE_INVALID", "EasyReforge VAE entry has no name", 502);
    return { setting: vae.model_name, explicit: true };
}

/**
 * LoRA: a Manga token name without "/" is a file stem; with "/" it is a relative path under
 * the shared LoRA root.  The Legacy prompt token uses the Legacy `name`, which Legacy resolves
 * by stem, so a stem shared by several Legacy files fails closed even if the path is unique.
 */
export function mapLora(tokenName, loras) {
    if (!Array.isArray(loras)) fail("LEGACY_CATALOG_UNAVAILABLE", "Legacy LoRA catalog is unavailable", 503);
    const name = norm(tokenName);
    const byPath = name.includes("/");
    const candidates = loras.filter(lora => {
        const file = lower(lora?.path);
        if (!file || !MODEL_EXT.test(file)) return false;
        return byPath ? file.replace(MODEL_EXT, "").endsWith(`/${name.toLowerCase()}`)
            : stem(file).toLowerCase() === name.toLowerCase();
    });
    const lora = unique(candidates,
        ["LORA_NOT_FOUND", `LoRA '${tokenName}' is not in the EasyReforge catalog`],
        ["LORA_AMBIGUOUS", `LoRA '${tokenName}' matches ${candidates.length} EasyReforge LoRAs`]);
    const legacyName = typeof lora.name === "string" && lora.name ? lora.name : stem(lora.path);
    const sameStem = loras.filter(other => stem(other?.path).toLowerCase() === stem(lora.path).toLowerCase());
    if (sameStem.length > 1) fail("LORA_AMBIGUOUS",
        `LoRA '${tokenName}' shares its name with ${sameStem.length - 1} other EasyReforge LoRA(s); EasyReforge cannot address it uniquely`, 422);
    return { name: legacyName, path: lora.path };
}

const samplerNames = list => (Array.isArray(list) ? list : []).map(item => typeof item === "string" ? item : item?.name).filter(Boolean);

export function mapSampler(value, samplers) {
    const names = samplerNames(samplers);
    if (!names.length) fail("LEGACY_CATALOG_UNAVAILABLE", "Legacy sampler catalog is unavailable", 503);
    if (names.includes(value)) return value;
    const mapped = COMFY_TO_LEGACY_SAMPLER[value];
    if (mapped && names.includes(mapped)) return mapped;
    fail("SAMPLER_UNSUPPORTED", `Sampler '${value}' has no EasyReforge equivalent; choose an EasyReforge sampler`, 422);
}

export function mapScheduler(value, schedulers) {
    if (!value) return "";
    const names = samplerNames(schedulers);
    if (!names.length) fail("SCHEDULER_UNSUPPORTED", `Scheduler '${value}' cannot be sent: EasyReforge exposes no scheduler list`, 422);
    if (names.includes(value)) return value;
    const mapped = COMFY_TO_LEGACY_SCHEDULER[value];
    if (mapped && names.includes(mapped)) return mapped;
    fail("SCHEDULER_UNSUPPORTED", `Scheduler '${value}' has no EasyReforge equivalent; choose an EasyReforge scheduler`, 422);
}

/** Replace each Manga LoRA token in place with its Legacy token; weight text is copied verbatim. */
export function composeLegacyPrompt(text, tokens, resolved) {
    let out = "";
    let cursor = 0;
    tokens.forEach((token, i) => {
        out += text.slice(cursor, token.index) + `<lora:${resolved[i].name}:${token.weight_text}>`;
        cursor = token.index + token.raw.length;
    });
    return out + text.slice(cursor);
}

/**
 * Build the txt2img request.  catalog: { sdModels, sdVae, loras, samplers, schedulers }.
 * Returns { payload, metadata } — metadata is the logical recipe echo for the result.
 */
export function buildTxt2ImgRequest(recipeInput, catalog, { vaePrefixMap = DEFAULT_VAE_PREFIX_MAP } = {}) {
    const recipe = validateRecipe(recipeInput);
    rejectUnsupportedSyntax(recipe.positive_raw, "positive");
    rejectUnsupportedSyntax(recipe.negative_raw, "negative");
    const loras = extractLoraRecipe(recipe.positive_raw, "positive");
    if (extractLoraRecipe(recipe.negative_raw, "negative").length) {
        fail("LORA_NEGATIVE_UNSUPPORTED", "LoRA tokens in the negative prompt are not supported by the EasyReforge path", 422);
    }
    const seen = new Set();
    for (const token of loras) {
        const key = norm(token.resource_id).toLowerCase();
        if (seen.has(key)) fail("LORA_DUPLICATE", `LoRA '${token.resource_id}' appears more than once`, 422);
        seen.add(key);
    }
    if (catalog?.cmdFlags && typeof catalog.cmdFlags === "object" && catalog.cmdFlags.vae_path) {
        fail("VAE_FORCED_BY_RUNTIME", "EasyReforge was launched with --vae-path; the Manga VAE choice cannot be honoured", 422);
    }
    const checkpoint = mapCheckpoint(recipe.checkpoint_id, catalog?.sdModels);
    const vae = mapVae(recipe.vae_id, catalog?.sdVae, vaePrefixMap);
    const resolved = loras.map(token => mapLora(token.resource_id, catalog?.loras));
    const sampler = mapSampler(recipe.sampler, catalog?.samplers);
    const scheduler = mapScheduler(recipe.scheduler, catalog?.schedulers);
    const payload = {
        prompt: composeLegacyPrompt(recipe.positive_raw, loras, resolved),
        negative_prompt: recipe.negative_raw,
        seed: Number(recipe.seed_requested),
        sampler_name: sampler,
        steps: recipe.steps, cfg_scale: recipe.cfg,
        width: recipe.width, height: recipe.height,
        batch_size: 1, n_iter: 1,
        // Insertion order matters: the VAE-resolution rule must be in force before sd_vae reloads.
        override_settings: { sd_vae_overrides_per_model_preferences: true, sd_model_checkpoint: checkpoint.title, sd_vae: vae.setting },
        override_settings_restore_afterwards: false,
        send_images: true, save_images: true,
    };
    if (scheduler) payload.scheduler = scheduler;
    const metadata = {
        backend: BACKEND_ID,
        checkpoint_id: recipe.checkpoint_id, legacy_checkpoint: checkpoint.title,
        vae_id: recipe.vae_id || null, legacy_vae: vae.setting,
        loras: loras.map((token, i) => ({ resource_id: token.resource_id, legacy_name: resolved[i].name,
            weight: token.weight, weight_text: token.weight_text, order: token.order })),
        sampler: recipe.sampler, legacy_sampler: sampler,
        scheduler: recipe.scheduler || null, legacy_scheduler: scheduler || null,
        cfg: recipe.cfg, steps: recipe.steps, width: recipe.width, height: recipe.height,
        seed_requested: recipe.seed_requested,
    };
    return { payload, metadata };
}

const PNG_SIGNATURE = Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]);
const MAX_RESULT_BYTES = 32 * 1024 * 1024;
const MAX_RESULT_BASE64_CHARS = Math.ceil(MAX_RESULT_BYTES / 3) * 4;

function invalidImage(message = "EasyReforge image is not a supported bounded PNG or JPEG") {
    fail("LEGACY_RESPONSE_INVALID", message, 502);
}

/** Require JPEG frame dimensions, scan data, and an EOI marker; reject truncated marker streams. */
function isStructurallyValidJpeg(bytes) {
    if (bytes.length < 4 || bytes[0] !== 0xff || bytes[1] !== 0xd8) return false;
    let position = 2;
    let hasFrame = false;
    let hasScan = false;
    while (position < bytes.length) {
        if (bytes[position] !== 0xff) return false;
        while (position < bytes.length && bytes[position] === 0xff) position++;
        if (position >= bytes.length) return false;
        const marker = bytes[position++];
        if (marker === 0x00 || marker === 0xd8) return false;
        if (marker === 0xd9) return hasFrame && hasScan;
        if (marker >= 0xd0 && marker <= 0xd7) return false;
        if (marker === 0x01) continue;
        if (position + 2 > bytes.length) return false;
        const segmentLength = bytes.readUInt16BE(position);
        if (segmentLength < 2 || position + segmentLength > bytes.length) return false;
        if (marker === 0xda) {
            if (!hasFrame || segmentLength < 6) return false;
            const scanComponents = bytes[position + 2];
            if (!scanComponents || segmentLength < 6 + 2 * scanComponents) return false;
        }
        if ((marker >= 0xc0 && marker <= 0xcf) && marker !== 0xc4 && marker !== 0xc8 && marker !== 0xcc) {
            if (segmentLength < 8) return false;
            const height = bytes.readUInt16BE(position + 3);
            const width = bytes.readUInt16BE(position + 5);
            const components = bytes[position + 7];
            if (!width || !height || !components || segmentLength < 8 + 3 * components) return false;
            hasFrame = true;
        }
        position += segmentLength;
        if (marker !== 0xda) continue;
        hasScan = true;
        let foundNextMarker = false;
        while (position < bytes.length) {
            if (bytes[position++] !== 0xff) continue;
            const markerStart = position - 1;
            while (position < bytes.length && bytes[position] === 0xff) position++;
            if (position >= bytes.length) return false;
            const scanMarker = bytes[position];
            if (scanMarker === 0x00 || (scanMarker >= 0xd0 && scanMarker <= 0xd7)) {
                position++;
                continue;
            }
            position = markerStart;
            foundNextMarker = true;
            break;
        }
        if (!foundNextMarker) return false;
    }
    return false;
}

function decodeResultImage(value) {
    let encoded = value;
    let declaredMime = null;
    if (value.startsWith("data:")) {
        const header = /^data:(image\/(?:png|jpeg));base64,/i.exec(value);
        if (!header) invalidImage("EasyReforge image uses an unsupported data URI format");
        declaredMime = header[1].toLowerCase();
        encoded = value.slice(header[0].length);
    }
    const compact = encoded.replace(/\s/g, "");
    if (!compact || compact.length > MAX_RESULT_BASE64_CHARS || /[^A-Za-z0-9+/=]/.test(compact) || compact.length % 4 === 1) {
        invalidImage("EasyReforge image is not valid base64");
    }
    const paddingAt = compact.indexOf("=");
    if (paddingAt !== -1) {
        const padding = compact.length - paddingAt;
        if ((padding !== 1 && padding !== 2) || compact.length % 4 !== 0 || paddingAt % 4 !== (padding === 2 ? 2 : 3)) {
            invalidImage("EasyReforge image is not valid base64");
        }
    }
    const bytes = Buffer.from(compact, "base64");
    if (bytes.length < 16 || bytes.length > MAX_RESULT_BYTES) invalidImage("EasyReforge image exceeds the bounded result size");
    if (bytes.toString("base64").replace(/=+$/, "") !== compact.replace(/=+$/, "")) invalidImage("EasyReforge image is not valid base64");
    const mime = bytes.subarray(0, PNG_SIGNATURE.length).equals(PNG_SIGNATURE) ? "image/png"
        : isStructurallyValidJpeg(bytes) ? "image/jpeg" : null;
    if (!mime) invalidImage();
    if (declaredMime && declaredMime !== mime) invalidImage("EasyReforge image MIME declaration does not match its bytes");
    return { bytes, mime };
}

/** Parse a txt2img response into one original PNG/JPEG byte stream + result metadata. */
export function parseTxt2ImgResponse(data, metadata) {
    if (!data || typeof data !== "object" || !Array.isArray(data.images) || data.images.length < 1 ||
        typeof data.images[0] !== "string") {
        fail("LEGACY_RESPONSE_INVALID", "EasyReforge txt2img response has no image", 502);
    }
    const { bytes, mime } = decodeResultImage(data.images[0]);
    let info = {};
    if (typeof data.info === "string" && data.info) {
        try { info = JSON.parse(data.info); } catch { fail("LEGACY_RESPONSE_INVALID", "EasyReforge info is not JSON", 502); }
    } else if (data.info && typeof data.info === "object") info = data.info;
    const seed = Number.isSafeInteger(info.seed) ? info.seed : null;
    return { bytes, mime, result: { ...metadata, backend: BACKEND_ID, mime, seed,
        legacy_model_name: typeof info.sd_model_name === "string" ? info.sd_model_name : null } };
}
