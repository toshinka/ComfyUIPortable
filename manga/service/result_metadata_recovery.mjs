/**
 * Read-only recovery of textual generation metadata from a PNG produced by
 * ComfyUI's SaveImage node.
 *
 * This is deliberately a small TEGAKI-owned parser.  ComfyUI currently uses
 * Pillow's PngInfo.add_text(), which writes the `prompt` and extra_pnginfo
 * values (including the usual `workflow` key) as PNG tEXt chunks.  zTXt/iTXt
 * are accepted as bounded interoperability paths, but no image decoding or
 * workflow execution is attempted here.
 */
import fs from "node:fs/promises";
import path from "node:path";
import { createHash } from "node:crypto";
import { inflateSync } from "node:zlib";

export const PNG_SIGNATURE = Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]);

export const ERROR_CODES = Object.freeze({
    FILE_NOT_FOUND: "FILE_NOT_FOUND",
    FILE_READ_FAILED: "FILE_READ_FAILED",
    FILE_TOO_LARGE: "FILE_TOO_LARGE",
    NOT_PNG: "NOT_PNG",
    PNG_CORRUPT: "PNG_CORRUPT",
    METADATA_ABSENT: "METADATA_ABSENT",
    METADATA_MALFORMED: "METADATA_MALFORMED",
    UNSUPPORTED_METADATA: "UNSUPPORTED_METADATA"
});

export const LIMITS = Object.freeze({
    maxFileBytes: 64 * 1024 * 1024,
    maxTextChunkBytes: 8 * 1024 * 1024,
    maxTextBytes: 32 * 1024 * 1024,
    maxJsonDepth: 128,
    maxJsonNodes: 100_000
});

const TEXT_CHUNKS = new Set(["tEXt", "zTXt", "iTXt"]);
const SAMPLER_CLASSES = new Set(["KSampler", "KSamplerAdvanced"]);
const CHECKPOINT_CLASSES = new Set(["CheckpointLoaderSimple", "CheckpointLoader"]);
const LORA_CLASSES = new Set(["LoraLoader", "LoraLoaderModelOnly"]);
const LATENT_SIZE_CLASSES = new Set([
    "EmptyLatentImage",
    "EmptySD3LatentImage",
    "EmptyFlux2LatentImage",
    "EmptyHunyuanLatentVideo",
    "EmptyLatentAudio"
]);
const LATENT_PASSTHROUGH_CLASSES = new Set([
    "LatentFromBatch",
    "RepeatLatentBatch",
    "LatentUpscale",
    "LatentUpscaleBy",
    "VAEEncode",
    "VAEEncodeTiled"
]);
const CONDITIONING_PASSTHROUGH_CLASSES = new Set([
    "ConditioningSetArea",
    "ConditioningSetAreaPercentage",
    "ConditioningSetAreaStrength",
    "ConditioningSetAreaSD3",
    "ConditioningSetMask",
    "ConditioningAverage",
    "ConditioningConcat",
    "ConditioningMultiply",
    "ConditioningZeroOut"
]);
const MODEL_PASSTHROUGH_CLASSES = new Set([
    "ModelSamplingDiscrete",
    "ModelSamplingContinuousEDM",
    "ModelSamplingFlux",
    "ModelSamplingAuraFlow",
    "ModelSamplingStableCascade",
    "FreeU_V2",
    "PerturbedAttentionGuidance",
    "CFGNorm",
    "ModelMergeSimple"
]);

const CRC_TABLE = (() => {
    const table = new Uint32Array(256);
    for (let i = 0; i < table.length; i++) {
        let value = i;
        for (let bit = 0; bit < 8; bit++) {
            value = (value & 1) ? (0xedb88320 ^ (value >>> 1)) : (value >>> 1);
        }
        table[i] = value >>> 0;
    }
    return table;
})();

function crc32(...buffers) {
    let value = 0xffffffff;
    for (const buffer of buffers) {
        for (const byte of buffer) value = CRC_TABLE[(value ^ byte) & 0xff] ^ (value >>> 8);
    }
    return (value ^ 0xffffffff) >>> 0;
}

class RecoveryFailure extends Error {
    constructor(code, message, details = {}) {
        super(message);
        this.name = "RecoveryFailure";
        this.code = code;
        Object.assign(this, details);
    }
}

function diagnostic(code, message, details = {}) {
    return { code, message, ...details };
}

function isRecord(value) {
    return value !== null && typeof value === "object" && !Array.isArray(value);
}

function createResult(filePath = null, sizeBytes = 0, sha256 = null) {
    const resolved = filePath === null ? null : path.resolve(String(filePath));
    return {
        ok: false,
        status: "INVALID",
        file: {
            path: resolved,
            name: resolved ? path.basename(resolved) : null,
            size_bytes: sizeBytes,
            sha256
        },
        png: { valid: false },
        // Values are strings for unique keys; duplicate keys become arrays.
        // metadata_entries remains the lossless ordered representation.
        raw_metadata: Object.create(null),
        metadata_entries: [],
        parsed_prompt: null,
        parsed_workflow: null,
        normalized_hints: {},
        warnings: [],
        error: null
    };
}

function addWarning(result, code, message, details = {}) {
    if (result.warnings.some(item => item.code === code && item.message === message)) return;
    result.warnings.push(diagnostic(code, message, details));
}

function setError(result, item) {
    if (!result.error) result.error = item;
    result.ok = false;
    result.status = "ERROR";
}

function addRawMetadata(result, entry) {
    result.metadata_entries.push(entry);
    const key = entry.keyword;
    if (!Object.hasOwn(result.raw_metadata, key)) {
        result.raw_metadata[key] = entry.text;
    } else if (Array.isArray(result.raw_metadata[key])) {
        result.raw_metadata[key].push(entry.text);
    } else {
        result.raw_metadata[key] = [result.raw_metadata[key], entry.text];
    }
}

function decodeUtf8(bytes, context) {
    try {
        return new TextDecoder("utf-8", { fatal: true }).decode(bytes);
    } catch (error) {
        throw new RecoveryFailure(
            ERROR_CODES.METADATA_MALFORMED,
            `${context} contains invalid UTF-8`,
            { cause: error.message }
        );
    }
}

function inflateText(bytes, context) {
    try {
        const output = inflateSync(bytes);
        if (output.length > LIMITS.maxTextChunkBytes) {
            throw new RecoveryFailure(
                ERROR_CODES.UNSUPPORTED_METADATA,
                `${context} exceeds the bounded decoded metadata limit`
            );
        }
        return output;
    } catch (error) {
        if (error instanceof RecoveryFailure) throw error;
        throw new RecoveryFailure(
            ERROR_CODES.METADATA_MALFORMED,
            `${context} has invalid compressed text`,
            { cause: error.message }
        );
    }
}

function parseTextChunk(type, data) {
    const keywordEnd = data.indexOf(0);
    if (keywordEnd <= 0 || keywordEnd > 79) {
        throw new RecoveryFailure(ERROR_CODES.PNG_CORRUPT, `${type} has an invalid keyword`);
    }
    const keyword = data.subarray(0, keywordEnd).toString("latin1");

    if (type === "tEXt") {
        return { keyword, text: data.subarray(keywordEnd + 1).toString("latin1"), chunk_type: type };
    }

    if (type === "zTXt") {
        if (data.length <= keywordEnd + 2) {
            throw new RecoveryFailure(ERROR_CODES.METADATA_MALFORMED, "zTXt has no compressed text");
        }
        const method = data[keywordEnd + 1];
        if (method !== 0) {
            throw new RecoveryFailure(
                ERROR_CODES.UNSUPPORTED_METADATA,
                `zTXt compression method ${method} is unsupported`,
                { keyword }
            );
        }
        const text = inflateText(data.subarray(keywordEnd + 2), `zTXt '${keyword}'`)
            .toString("latin1");
        return { keyword, text, chunk_type: type, compressed: true };
    }

    // iTXt: keyword NUL, compression flag, compression method, language NUL,
    // translated keyword NUL, text.
    let cursor = keywordEnd + 1;
    if (data.length < cursor + 2) {
        throw new RecoveryFailure(ERROR_CODES.METADATA_MALFORMED, "iTXt has no compression fields");
    }
    const compressionFlag = data[cursor++];
    const compressionMethod = data[cursor++];
    if (compressionFlag !== 0 && compressionFlag !== 1) {
        throw new RecoveryFailure(
            ERROR_CODES.UNSUPPORTED_METADATA,
            `iTXt compression flag ${compressionFlag} is unsupported`,
            { keyword }
        );
    }
    if (compressionFlag === 1 && compressionMethod !== 0) {
        throw new RecoveryFailure(
            ERROR_CODES.UNSUPPORTED_METADATA,
            `iTXt compression method ${compressionMethod} is unsupported`,
            { keyword }
        );
    }
    const languageEnd = data.indexOf(0, cursor);
    if (languageEnd < 0) {
        throw new RecoveryFailure(ERROR_CODES.METADATA_MALFORMED, "iTXt has no language terminator");
    }
    const language = decodeUtf8(data.subarray(cursor, languageEnd), "iTXt language");
    cursor = languageEnd + 1;
    const translatedEnd = data.indexOf(0, cursor);
    if (translatedEnd < 0) {
        throw new RecoveryFailure(ERROR_CODES.METADATA_MALFORMED, "iTXt has no translated-keyword terminator");
    }
    const translatedKeyword = decodeUtf8(data.subarray(cursor, translatedEnd), "iTXt translated keyword");
    cursor = translatedEnd + 1;
    const textBytes = compressionFlag === 1
        ? inflateText(data.subarray(cursor), `iTXt '${keyword}'`)
        : data.subarray(cursor);
    return {
        keyword,
        text: decodeUtf8(textBytes, `iTXt '${keyword}'`),
        chunk_type: type,
        compressed: compressionFlag === 1,
        language,
        translated_keyword: translatedKeyword
    };
}

function parsePng(buffer) {
    if (!Buffer.isBuffer(buffer)) {
        throw new RecoveryFailure(ERROR_CODES.PNG_CORRUPT, "PNG input is not a byte buffer");
    }
    if (buffer.length > LIMITS.maxFileBytes) {
        throw new RecoveryFailure(ERROR_CODES.FILE_TOO_LARGE, "PNG exceeds the bounded file size limit");
    }
    if (buffer.length < PNG_SIGNATURE.length || !buffer.subarray(0, 8).equals(PNG_SIGNATURE)) {
        throw new RecoveryFailure(ERROR_CODES.NOT_PNG, "Input does not have a PNG signature");
    }

    let offset = 8;
    let seenIHDR = false;
    let seenIDAT = false;
    let seenIEND = false;
    let width = null;
    let height = null;
    let bitDepth = null;
    let colorType = null;
    let textBytes = 0;
    const entries = [];

    while (offset < buffer.length) {
        const chunkOffset = offset;
        if (offset + 12 > buffer.length) {
            throw new RecoveryFailure(ERROR_CODES.PNG_CORRUPT, "PNG chunk header is truncated", { offset });
        }
        const length = buffer.readUInt32BE(offset);
        offset += 4;
        const typeBytes = buffer.subarray(offset, offset + 4);
        const type = typeBytes.toString("ascii");
        offset += 4;
        if (!/^[A-Za-z]{4}$/.test(type)) {
            throw new RecoveryFailure(ERROR_CODES.PNG_CORRUPT, `PNG has invalid chunk type '${type}'`, { offset: chunkOffset });
        }
        const dataEnd = offset + length;
        if (dataEnd < offset || dataEnd + 4 > buffer.length) {
            throw new RecoveryFailure(ERROR_CODES.PNG_CORRUPT, `PNG ${type} chunk is truncated`, { offset: chunkOffset });
        }
        const data = buffer.subarray(offset, dataEnd);
        offset = dataEnd;
        const expectedCrc = buffer.readUInt32BE(offset);
        offset += 4;
        if (crc32(typeBytes, data) !== expectedCrc) {
            throw new RecoveryFailure(ERROR_CODES.PNG_CORRUPT, `PNG ${type} CRC is invalid`, { offset: chunkOffset });
        }

        if (!seenIHDR && type !== "IHDR") {
            throw new RecoveryFailure(ERROR_CODES.PNG_CORRUPT, "PNG must begin with IHDR", { offset: chunkOffset });
        }
        if (type === "IHDR") {
            if (seenIHDR || length !== 13) {
                throw new RecoveryFailure(ERROR_CODES.PNG_CORRUPT, "PNG IHDR is missing or duplicated", { offset: chunkOffset });
            }
            seenIHDR = true;
            width = data.readUInt32BE(0);
            height = data.readUInt32BE(4);
            bitDepth = data[8];
            colorType = data[9];
            const validBitDepth = new Set([1, 2, 4, 8, 16]).has(bitDepth);
            const validColorType = new Set([0, 2, 3, 4, 6]).has(colorType);
            if (!width || !height || !validBitDepth || !validColorType || data[10] !== 0 || data[11] !== 0 || data[12] > 1) {
                throw new RecoveryFailure(ERROR_CODES.PNG_CORRUPT, "PNG IHDR has invalid dimensions or encoding", { offset: chunkOffset });
            }
        } else if (type === "IDAT") {
            seenIDAT = true;
        } else if (type === "IEND") {
            if (length !== 0 || seenIEND) {
                throw new RecoveryFailure(ERROR_CODES.PNG_CORRUPT, "PNG IEND is invalid", { offset: chunkOffset });
            }
            seenIEND = true;
            if (offset !== buffer.length) {
                throw new RecoveryFailure(ERROR_CODES.PNG_CORRUPT, "PNG contains data after IEND", { offset });
            }
        } else if (TEXT_CHUNKS.has(type)) {
            if (length > LIMITS.maxTextChunkBytes) {
                throw new RecoveryFailure(ERROR_CODES.UNSUPPORTED_METADATA, `${type} metadata chunk exceeds the bounded size limit`, { offset: chunkOffset });
            }
            textBytes += length;
            if (textBytes > LIMITS.maxTextBytes) {
                throw new RecoveryFailure(ERROR_CODES.UNSUPPORTED_METADATA, "PNG textual metadata exceeds the bounded total size limit", { offset: chunkOffset });
            }
            entries.push({ ...parseTextChunk(type, data), offset: chunkOffset, byte_length: length });
        }
        if (seenIEND && offset < buffer.length) {
            throw new RecoveryFailure(ERROR_CODES.PNG_CORRUPT, "PNG contains a chunk after IEND", { offset });
        }
    }

    if (!seenIHDR || !seenIEND || !seenIDAT) {
        throw new RecoveryFailure(ERROR_CODES.PNG_CORRUPT, "PNG is missing IHDR, IDAT, or IEND");
    }
    return { width, height, bitDepth, colorType, entries };
}

function metadataValues(result, key) {
    if (!Object.hasOwn(result.raw_metadata, key)) return [];
    const value = result.raw_metadata[key];
    return Array.isArray(value) ? value : [value];
}

function assertJsonBounds(value) {
    const stack = [{ value, depth: 0 }];
    let nodes = 0;
    while (stack.length) {
        const current = stack.pop();
        nodes++;
        if (nodes > LIMITS.maxJsonNodes || current.depth > LIMITS.maxJsonDepth) {
            throw new RecoveryFailure(ERROR_CODES.METADATA_MALFORMED, "JSON metadata exceeds the bounded nesting limit");
        }
        if (Array.isArray(current.value)) {
            for (const child of current.value) stack.push({ value: child, depth: current.depth + 1 });
        } else if (isRecord(current.value)) {
            for (const child of Object.values(current.value)) stack.push({ value: child, depth: current.depth + 1 });
        }
    }
}

function parseJsonField(result, key) {
    const values = metadataValues(result, key);
    if (!values.length) return null;
    if (values.length !== 1) {
        return diagnostic(ERROR_CODES.METADATA_MALFORMED, `PNG contains duplicate '${key}' metadata`, { keyword: key });
    }
    try {
        const parsed = JSON.parse(values[0]);
        assertJsonBounds(parsed);
        return { value: parsed };
    } catch (error) {
        if (error instanceof RecoveryFailure) return diagnostic(error.code, error.message, { keyword: key });
        return diagnostic(ERROR_CODES.METADATA_MALFORMED, `PNG '${key}' metadata is not valid JSON`, {
            keyword: key,
            cause: error.message
        });
    }
}

function graphNodes(prompt) {
    if (!isRecord(prompt)) return new Map();
    const nodes = new Map();
    for (const [id, value] of Object.entries(prompt)) {
        if (!isRecord(value) || typeof value.class_type !== "string" || !isRecord(value.inputs)) continue;
        nodes.set(String(id), value);
    }
    return nodes;
}

function referenceId(value) {
    return Array.isArray(value) && value.length >= 1 && (typeof value[0] === "string" || typeof value[0] === "number")
        ? String(value[0])
        : null;
}

function finiteNumber(value, { integer = false, min = -Infinity, max = Infinity } = {}) {
    const number = typeof value === "number" ? value : null;
    if (number === null || !Number.isFinite(number) || (integer && !Number.isInteger(number)) || number < min || number > max) return null;
    return number;
}

function scalarValue(value) {
    if (typeof value === "string" && value.length) return value;
    if (typeof value === "number" && Number.isFinite(value)) return value;
    if (typeof value === "boolean") return value;
    return null;
}

function stableValue(value) {
    return JSON.stringify(value);
}

function consistent(values, result, code, label) {
    const usable = values.filter(value => value !== null && value !== undefined);
    if (!usable.length) return null;
    if (usable.length !== values.length) {
        addWarning(result, `${code}_INCOMPLETE`, `${label} is missing or invalid on one or more graph paths; it was omitted`);
        return null;
    }
    const first = stableValue(usable[0]);
    if (usable.every(value => stableValue(value) === first)) return usable[0];
    addWarning(result, code, `${label} differs across graph paths; it was omitted`);
    return null;
}

function collectModelChain(startId, nodes) {
    const visited = new Set();
    const loras = [];
    const checkpoints = [];
    let nodeId = startId;
    while (nodeId && !visited.has(nodeId)) {
        visited.add(nodeId);
        const node = nodes.get(nodeId);
        if (!node) break;
        const kind = node.class_type;
        if (LORA_CLASSES.has(kind)) {
            const name = typeof node.inputs.lora_name === "string" && node.inputs.lora_name ? node.inputs.lora_name : null;
            const strengthModel = finiteNumber(node.inputs.strength_model);
            const strengthClip = finiteNumber(node.inputs.strength_clip);
            if (name !== null) {
                loras.push({
                    name,
                    strength_model: strengthModel,
                    ...(strengthClip === null ? {} : { strength_clip: strengthClip }),
                    source: "workflow"
                });
            }
            nodeId = referenceId(node.inputs.model);
            continue;
        }
        if (CHECKPOINT_CLASSES.has(kind)) {
            const name = typeof node.inputs.ckpt_name === "string" && node.inputs.ckpt_name ? node.inputs.ckpt_name : null;
            if (name !== null) checkpoints.push(name);
            break;
        }
        if (MODEL_PASSTHROUGH_CLASSES.has(kind)) {
            nodeId = referenceId(node.inputs.model);
            continue;
        }
        break;
    }
    return { loras: loras.reverse(), checkpoints };
}

function resolveLatentSize(startId, nodes, visited = new Set()) {
    if (!startId || visited.has(startId)) return null;
    visited.add(startId);
    const node = nodes.get(startId);
    if (!node) return null;
    if (LATENT_SIZE_CLASSES.has(node.class_type)) {
        const width = finiteNumber(node.inputs.width, { integer: true, min: 1 });
        const height = finiteNumber(node.inputs.height, { integer: true, min: 1 });
        return width !== null && height !== null ? { width, height } : null;
    }
    if (LATENT_PASSTHROUGH_CLASSES.has(node.class_type)) {
        return resolveLatentSize(
            referenceId(node.inputs.samples) || referenceId(node.inputs.latent),
            nodes,
            visited
        );
    }
    return null;
}

function collectTextSources(startId, nodes, visited = new Set()) {
    if (!startId || visited.has(startId)) return { texts: [], ambiguous: false };
    visited.add(startId);
    const node = nodes.get(startId);
    if (!node) return { texts: [], ambiguous: false };
    if (node.class_type === "CLIPTextEncode") {
        return typeof node.inputs.text === "string"
            ? { texts: [node.inputs.text], ambiguous: false }
            : { texts: [], ambiguous: false };
    }
    if (node.class_type === "CLIPTextEncodeSDXL") {
        const global = typeof node.inputs.text_g === "string" ? node.inputs.text_g : null;
        const local = typeof node.inputs.text_l === "string" ? node.inputs.text_l : null;
        return global !== null && local !== null && global === local
            ? { texts: [global], ambiguous: false }
            : { texts: [], ambiguous: global !== null || local !== null };
    }
    if (!CONDITIONING_PASSTHROUGH_CLASSES.has(node.class_type) && node.class_type !== "ConditioningCombine") {
        return { texts: [], ambiguous: false };
    }
    const refs = [];
    for (const [key, value] of Object.entries(node.inputs)) {
        if ((key === "conditioning" || key.startsWith("conditioning") || key === "positive" || key === "negative") && referenceId(value)) {
            refs.push(referenceId(value));
        }
    }
    const merged = { texts: [], ambiguous: false };
    for (const ref of refs) {
        const found = collectTextSources(ref, nodes, visited);
        merged.ambiguous ||= found.ambiguous;
        for (const text of found.texts) if (!merged.texts.includes(text)) merged.texts.push(text);
    }
    if (merged.texts.length > 1) merged.ambiguous = true;
    return merged;
}

function promptLoraReferences(texts) {
    const pattern = /<lora:([^:<>]+):([+-]?(?:\d+(?:\.\d*)?|\.\d+))>/g;
    const references = [];
    for (const text of texts) {
        if (typeof text !== "string") continue;
        for (const match of text.matchAll(pattern)) {
            const weight = Number(match[2]);
            if (Number.isFinite(weight)) references.push({ name: match[1], weight, source: "prompt" });
        }
    }
    const unique = new Map(references.map(item => [`${item.name}\u0000${item.weight}`, item]));
    return [...unique.values()];
}

function extractGraphHints(prompt, png, result) {
    const nodes = graphNodes(prompt);
    if (!nodes.size) return {};
    const samplers = [...nodes.entries()].filter(([, node]) => SAMPLER_CLASSES.has(node.class_type));
    if (!samplers.length) {
        addWarning(result, ERROR_CODES.UNSUPPORTED_METADATA, "ComfyUI prompt graph has no supported KSampler node");
        return {};
    }

    const hints = {};
    const samplerValues = field => samplers.map(([, node]) => {
        const value = node.inputs[field];
        if (field === "seed") return finiteNumber(value, { integer: true, min: 0 });
        if (field === "noise_seed") return finiteNumber(value, { integer: true, min: 0 });
        if (field === "steps") return finiteNumber(value, { integer: true, min: 1 });
        if (field === "cfg") return finiteNumber(value, { min: 0 });
        return scalarValue(value);
    });
    const seed = consistent(
        samplers.map(([, node]) => finiteNumber(
            node.inputs[node.class_type === "KSamplerAdvanced" ? "noise_seed" : "seed"],
            { integer: true, min: 0 }
        )),
        result,
        "CONFLICTING_SEED",
        "Seed"
    );
    if (seed !== null) hints.seed = seed;
    for (const [field, label] of [["steps", "Steps"], ["cfg", "CFG"], ["sampler_name", "Sampler"], ["scheduler", "Scheduler"]]) {
        const value = consistent(samplerValues(field), result, `CONFLICTING_${field.toUpperCase()}`, label);
        if (value !== null) hints[field === "sampler_name" ? "sampler" : field] = value;
    }

    const positiveTexts = [];
    const negativeTexts = [];
    const latentSizes = [];
    const modelChains = [];
    for (const [, node] of samplers) {
        const positive = collectTextSources(referenceId(node.inputs.positive), nodes);
        const negative = collectTextSources(referenceId(node.inputs.negative), nodes);
        if (positive.ambiguous) addWarning(result, "AMBIGUOUS_PROMPT_GRAPH", "Positive conditioning has multiple or ambiguous text sources");
        if (negative.ambiguous) addWarning(result, "AMBIGUOUS_PROMPT_GRAPH", "Negative conditioning has multiple or ambiguous text sources");
        if (!positive.ambiguous && positive.texts.length === 1) positiveTexts.push(positive.texts[0]);
        if (!negative.ambiguous && negative.texts.length === 1) negativeTexts.push(negative.texts[0]);
        const size = resolveLatentSize(referenceId(node.inputs.latent_image), nodes);
        if (size) latentSizes.push(size);
        modelChains.push(collectModelChain(referenceId(node.inputs.model), nodes));
    }
    const positive = consistent(positiveTexts, result, "CONFLICTING_POSITIVE_PROMPT", "Positive prompt");
    const negative = consistent(negativeTexts, result, "CONFLICTING_NEGATIVE_PROMPT", "Negative prompt");
    if (positive !== null) hints.positive_prompt = positive;
    if (negative !== null) hints.negative_prompt = negative;

    const graphSize = latentSizes.length === samplers.length
        ? consistent(latentSizes, result, "CONFLICTING_DIMENSIONS", "Latent dimensions")
        : null;
    if (graphSize && graphSize.width === png.width && graphSize.height === png.height) {
        hints.width = graphSize.width;
        hints.height = graphSize.height;
        hints.dimension_source = "workflow";
    } else if (graphSize) {
        addWarning(result, "DIMENSION_CONFLICT", "Workflow dimensions differ from PNG dimensions; PNG dimensions were retained as file facts");
    }

    const checkpointNames = modelChains.flatMap(chain => chain.checkpoints);
    const checkpoint = checkpointNames.length === samplers.length
        ? consistent(checkpointNames, result, "CONFLICTING_CHECKPOINT", "Checkpoint")
        : null;
    if (checkpoint !== null) hints.checkpoint = checkpoint;

    const loraLists = modelChains.map(chain => chain.loras);
    if (loraLists.length && loraLists.every(list => stableValue(list) === stableValue(loraLists[0]))) {
        if (loraLists[0].length) hints.lora_references = loraLists[0];
    } else if (loraLists.some(list => list.length)) {
        addWarning(result, "CONFLICTING_LORA_GRAPH", "LoRA loader paths differ across graph samplers; workflow LoRAs were omitted");
    }
    const promptLoras = promptLoraReferences([...positiveTexts, ...negativeTexts]);
    if (promptLoras.length) hints.prompt_lora_references = promptLoras;

    return hints;
}

function applyMetadata(result, parsed) {
    for (const entry of parsed.entries) addRawMetadata(result, entry);
    result.png = {
        valid: true,
        width: parsed.width,
        height: parsed.height,
        bit_depth: parsed.bitDepth,
        color_type: parsed.colorType
    };

    const prompt = parseJsonField(result, "prompt");
    const workflow = parseJsonField(result, "workflow");
    if (prompt?.value !== undefined) result.parsed_prompt = prompt.value;
    if (workflow?.value !== undefined) result.parsed_workflow = workflow.value;
    for (const issue of [prompt, workflow]) {
        if (issue?.code) setError(result, issue);
    }

    // PNG dimensions are explicit file facts even when no workflow is present.
    result.normalized_hints.width = parsed.width;
    result.normalized_hints.height = parsed.height;
    result.normalized_hints.dimension_source = "png";
    if (isRecord(result.parsed_prompt)) {
        const graphHints = extractGraphHints(result.parsed_prompt, parsed, result);
        Object.assign(result.normalized_hints, graphHints);
    }
    if (!parsed.entries.length && !result.error) {
        result.ok = true;
        result.status = "METADATA_ABSENT";
        result.error = diagnostic(ERROR_CODES.METADATA_ABSENT, "PNG contains no textual generation metadata", { fatal: false });
    } else if (!result.error) {
        result.ok = true;
        result.status = "OK";
    }
}

/**
 * Inspect an already-read PNG buffer without any filesystem side effects.
 * `filePath` is identity metadata only; the buffer is never written.
 */
export function inspectPngBuffer(buffer, { filePath = null } = {}) {
    const bytes = Buffer.isBuffer(buffer) ? buffer : Buffer.from(buffer || []);
    const digest = createHash("sha256").update(bytes).digest("hex");
    const result = createResult(filePath, bytes.length, digest);
    try {
        const parsed = parsePng(bytes);
        applyMetadata(result, parsed);
    } catch (error) {
        const issue = error instanceof RecoveryFailure
            ? diagnostic(error.code, error.message, Object.fromEntries(Object.entries(error).filter(([key]) => key !== "name" && key !== "message" && key !== "code")))
            : diagnostic(ERROR_CODES.PNG_CORRUPT, "PNG inspection failed", { cause: error.message });
        setError(result, issue);
        result.png.valid = issue.code !== ERROR_CODES.NOT_PNG;
    }
    return result;
}

/**
 * Inspect one local PNG path.  The operation is read-only and never contacts
 * a backend, changes a catalog, or restores authoring/generation state.
 */
export async function inspectGeneratedPng(filePath) {
    let resolved;
    try {
        resolved = path.resolve(String(filePath));
    } catch (error) {
        const result = createResult(null);
        setError(result, diagnostic(ERROR_CODES.FILE_NOT_FOUND, "PNG path is invalid", { cause: error.message }));
        return result;
    }
    let stat;
    try {
        stat = await fs.stat(resolved);
    } catch (error) {
        const result = createResult(resolved);
        setError(result, diagnostic(
            error.code === "ENOENT" ? ERROR_CODES.FILE_NOT_FOUND : ERROR_CODES.FILE_READ_FAILED,
            error.code === "ENOENT" ? "PNG file was not found" : "PNG file could not be inspected",
            { cause: error.code }
        ));
        return result;
    }
    if (!stat.isFile()) {
        const result = createResult(resolved, Number(stat.size) || 0);
        setError(result, diagnostic(ERROR_CODES.FILE_READ_FAILED, "PNG path is not a regular file"));
        return result;
    }
    if (stat.size > LIMITS.maxFileBytes) {
        const result = createResult(resolved, Number(stat.size));
        setError(result, diagnostic(ERROR_CODES.FILE_TOO_LARGE, "PNG exceeds the bounded file size limit"));
        return result;
    }
    let bytes;
    try {
        bytes = await fs.readFile(resolved);
    } catch (error) {
        const result = createResult(resolved, Number(stat.size) || 0);
        setError(result, diagnostic(ERROR_CODES.FILE_READ_FAILED, "PNG file could not be read", { cause: error.code }));
        return result;
    }
    return inspectPngBuffer(bytes, { filePath: resolved });
}
