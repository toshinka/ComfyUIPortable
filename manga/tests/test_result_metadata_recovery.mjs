/** Bounded PNG/ComfyUI metadata recovery tests; no runtime or generation. */
import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { deflateSync } from "node:zlib";

import {
    ERROR_CODES,
    inspectGeneratedPng,
    inspectPngBuffer
} from "../service/result_metadata_recovery.mjs";

const PNG_SIGNATURE = Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]);
const CRC_TABLE = (() => {
    const table = new Uint32Array(256);
    for (let i = 0; i < table.length; i++) {
        let value = i;
        for (let bit = 0; bit < 8; bit++) value = (value & 1) ? (0xedb88320 ^ (value >>> 1)) : (value >>> 1);
        table[i] = value >>> 0;
    }
    return table;
})();

function crc32(bytes) {
    let value = 0xffffffff;
    for (const byte of bytes) value = CRC_TABLE[(value ^ byte) & 0xff] ^ (value >>> 8);
    return (value ^ 0xffffffff) >>> 0;
}

function pngChunk(type, data) {
    const kind = Buffer.from(type, "ascii");
    const payload = Buffer.isBuffer(data) ? data : Buffer.from(data);
    const header = Buffer.alloc(8);
    header.writeUInt32BE(payload.length, 0);
    kind.copy(header, 4);
    const checksum = Buffer.alloc(4);
    checksum.writeUInt32BE(crc32(Buffer.concat([kind, payload])), 0);
    return Buffer.concat([header, payload, checksum]);
}

function textChunk(keyword, text) {
    return pngChunk("tEXt", Buffer.concat([
        Buffer.from(keyword, "latin1"),
        Buffer.from([0]),
        Buffer.from(text, "latin1")
    ]));
}

function compressedTextChunk(keyword, text) {
    return pngChunk("zTXt", Buffer.concat([
        Buffer.from(keyword, "latin1"),
        Buffer.from([0, 0]),
        deflateSync(Buffer.from(text, "latin1"))
    ]));
}

function iTextChunk(keyword, text) {
    return pngChunk("iTXt", Buffer.concat([
        Buffer.from(keyword, "latin1"),
        Buffer.from([0, 0]),
        Buffer.from("en\0", "utf8"),
        Buffer.from("\0", "utf8"),
        Buffer.from(text, "utf8")
    ]));
}

function tinyPng({ width = 1, height = 1, metadata = [] } = {}) {
    const ihdr = Buffer.alloc(13);
    ihdr.writeUInt32BE(width, 0);
    ihdr.writeUInt32BE(height, 4);
    ihdr[8] = 8; // bit depth
    ihdr[9] = 6; // RGBA
    const scanline = Buffer.alloc(width * 4 + 1);
    scanline[0] = 0; // filter type
    for (let row = 0; row < height; row++) {
        // A deterministic opaque white scanline is enough for PNG structure tests.
        scanline.fill(255, 1);
    }
    const idat = deflateSync(Buffer.concat(Array.from({ length: height }, () => scanline)));
    return Buffer.concat([
        PNG_SIGNATURE,
        pngChunk("IHDR", ihdr),
        ...metadata,
        pngChunk("IDAT", idat),
        pngChunk("IEND", Buffer.alloc(0))
    ]);
}

function graph({ ambiguousPositive = false, unknownNode = false } = {}) {
    const value = {
        "1": { class_type: "CheckpointLoaderSimple", inputs: { ckpt_name: "Illustrious.safetensors" } },
        "2": {
            class_type: "LoraLoader",
            inputs: {
                model: ["1", 0], clip: ["1", 1],
                lora_name: "style/ink.safetensors", strength_model: 0.7, strength_clip: 0.55
            }
        },
        "3": { class_type: "CLIPTextEncode", inputs: { text: "1girl, <lora:prompt_style:0.4>", clip: ["2", 1] } },
        "4": { class_type: "CLIPTextEncode", inputs: { text: "low quality, blurry", clip: ["2", 1] } },
        "5": { class_type: "EmptyLatentImage", inputs: { width: 832, height: 1216, batch_size: 1 } },
        "6": {
            class_type: "KSampler",
            inputs: {
                model: ["2", 0], seed: 0, steps: 24, cfg: 6.5,
                sampler_name: "euler", scheduler: "normal",
                positive: [ambiguousPositive ? "9" : "3", 0], negative: ["4", 0],
                latent_image: ["5", 0], denoise: 1
            }
        }
    };
    if (ambiguousPositive) {
        value["7"] = { class_type: "CLIPTextEncode", inputs: { text: "first prompt", clip: ["2", 1] } };
        value["8"] = { class_type: "CLIPTextEncode", inputs: { text: "second prompt", clip: ["2", 1] } };
        value["9"] = { class_type: "ConditioningCombine", inputs: { conditioning_1: ["7", 0], conditioning_2: ["8", 0] } };
    }
    if (unknownNode) value.unknown = { class_type: "FutureNodeThatIsNotKnown", inputs: { arbitrary: { nested: true } } };
    return value;
}

async function fixture(t, bytes, name = "fixture.png") {
    const directory = await fs.mkdtemp(path.join(os.tmpdir(), "tegaki-png-recovery-"));
    const file = path.join(directory, name);
    await fs.writeFile(file, bytes);
    t.after(async () => {
        if (!directory.startsWith(path.resolve(os.tmpdir()) + path.sep)) throw new Error("Unexpected fixture cleanup path");
        await fs.rm(directory, { recursive: true, force: true });
    });
    return { directory, file };
}

test("valid PNG is identified and metadata absence is explicit", async t => {
    const { file } = await fixture(t, tinyPng());
    const result = await inspectGeneratedPng(file);
    assert.equal(result.ok, true);
    assert.equal(result.png.valid, true);
    assert.equal(result.error.code, ERROR_CODES.METADATA_ABSENT);
    assert.equal(result.file.name, "fixture.png");
    assert.equal(result.png.width, 1);
    assert.equal(result.normalized_hints.width, 1);
    assert.equal(result.normalized_hints.height, 1);
});

test("ComfyUI prompt metadata is recovered faithfully", async t => {
    const prompt = graph();
    const promptJson = JSON.stringify(prompt);
    const { file } = await fixture(t, tinyPng({ metadata: [textChunk("prompt", promptJson)] }));
    const result = await inspectGeneratedPng(file);
    assert.equal(result.ok, true);
    assert.equal(result.error, null);
    assert.equal(result.raw_metadata.prompt, promptJson);
    assert.deepEqual(result.parsed_prompt, prompt);
    assert.equal(result.metadata_entries[0].chunk_type, "tEXt");
});

test("workflow metadata is recovered without applying it", async t => {
    const workflow = { version: 1, nodes: [{ id: 6, type: "KSampler" }], links: [] };
    const workflowJson = JSON.stringify(workflow);
    const { file } = await fixture(t, tinyPng({ metadata: [textChunk("workflow", workflowJson)] }));
    const result = await inspectGeneratedPng(file);
    assert.equal(result.ok, true);
    assert.equal(result.raw_metadata.workflow, workflowJson);
    assert.deepEqual(result.parsed_workflow, workflow);
    assert.equal(result.parsed_prompt, null);
});

test("prompt plus workflow yield conservative normalized hints", async t => {
    const prompt = graph();
    const workflow = { nodes: [{ id: 6, type: "KSampler" }], last_node_id: 6 };
    const { file } = await fixture(t, tinyPng({
        width: 832,
        height: 1216,
        metadata: [textChunk("prompt", JSON.stringify(prompt)), textChunk("workflow", JSON.stringify(workflow))]
    }));
    const result = await inspectGeneratedPng(file);
    assert.equal(result.ok, true);
    assert.equal(result.error, null);
    assert.equal(result.normalized_hints.positive_prompt, "1girl, <lora:prompt_style:0.4>");
    assert.equal(result.normalized_hints.negative_prompt, "low quality, blurry");
    assert.equal(result.normalized_hints.checkpoint, "Illustrious.safetensors");
    assert.equal(result.normalized_hints.seed, 0, "seed zero is a real value");
    assert.equal(result.normalized_hints.steps, 24);
    assert.equal(result.normalized_hints.cfg, 6.5);
    assert.equal(result.normalized_hints.sampler, "euler");
    assert.equal(result.normalized_hints.scheduler, "normal");
    assert.equal(result.normalized_hints.width, 832);
    assert.equal(result.normalized_hints.height, 1216);
    assert.equal(result.normalized_hints.dimension_source, "workflow");
    assert.deepEqual(result.normalized_hints.lora_references, [{
        name: "style/ink.safetensors", strength_model: 0.7, strength_clip: 0.55, source: "workflow"
    }]);
    assert.deepEqual(result.normalized_hints.prompt_lora_references, [{ name: "prompt_style", weight: 0.4, source: "prompt" }]);
});

test("compressed textual PNG metadata is supported without changing raw text", async t => {
    const value = JSON.stringify({ hello: "world" });
    const { file } = await fixture(t, tinyPng({ metadata: [compressedTextChunk("custom", value), iTextChunk("note", "こんにちは")] }));
    const result = await inspectGeneratedPng(file);
    assert.equal(result.ok, true);
    assert.equal(result.raw_metadata.custom, value);
    assert.equal(result.raw_metadata.note, "こんにちは");
    assert.equal(result.metadata_entries[0].compressed, true);
});

test("malformed JSON is distinct while raw metadata remains available", async t => {
    const raw = "{not valid json";
    const { file } = await fixture(t, tinyPng({ metadata: [textChunk("prompt", raw)] }));
    const result = await inspectGeneratedPng(file);
    assert.equal(result.ok, false);
    assert.equal(result.error.code, ERROR_CODES.METADATA_MALFORMED);
    assert.equal(result.raw_metadata.prompt, raw);
    assert.equal(result.png.valid, true);
});

test("non-PNG input is rejected distinctly", async t => {
    const { file } = await fixture(t, Buffer.from("not a png", "utf8"), "not-png.bin");
    const result = await inspectGeneratedPng(file);
    assert.equal(result.ok, false);
    assert.equal(result.error.code, ERROR_CODES.NOT_PNG);
    assert.equal(result.png.valid, false);
});

test("truncated PNG is rejected as corrupt", async t => {
    const valid = tinyPng({ metadata: [textChunk("prompt", JSON.stringify(graph()))] });
    const { file } = await fixture(t, valid.subarray(0, valid.length - 7));
    const result = await inspectGeneratedPng(file);
    assert.equal(result.ok, false);
    assert.equal(result.error.code, ERROR_CODES.PNG_CORRUPT);
    assert.equal(result.png.valid, true);
});

test("known graph extracts high-value hints and unknown nodes do not crash", () => {
    const result = inspectPngBuffer(tinyPng({ width: 832, height: 1216, metadata: [textChunk("prompt", JSON.stringify(graph({ unknownNode: true })))] }));
    assert.equal(result.ok, true);
    assert.equal(result.normalized_hints.checkpoint, "Illustrious.safetensors");
    assert.equal(result.normalized_hints.seed, 0);
    assert.equal(result.normalized_hints.width, 832);
    assert.equal(result.normalized_hints.height, 1216);
});

test("ambiguous conditioning is never flattened into invented prompt text", () => {
    const result = inspectPngBuffer(tinyPng({
        metadata: [textChunk("prompt", JSON.stringify(graph({ ambiguousPositive: true })))]
    }));
    assert.equal(result.ok, true);
    assert.equal(Object.hasOwn(result.normalized_hints, "positive_prompt"), false);
    assert.equal(result.normalized_hints.negative_prompt, "low quality, blurry");
    assert.ok(result.warnings.some(item => item.code === "AMBIGUOUS_PROMPT_GRAPH"));
});

test("inspection performs no filesystem writes", async t => {
    const { directory, file } = await fixture(t, tinyPng({ metadata: [textChunk("prompt", JSON.stringify(graph()))] }));
    const beforeStat = await fs.stat(file);
    const beforeEntries = await fs.readdir(directory);
    await inspectGeneratedPng(file);
    const afterStat = await fs.stat(file);
    const afterEntries = await fs.readdir(directory);
    assert.equal(afterStat.size, beforeStat.size);
    assert.equal(afterStat.mtimeMs, beforeStat.mtimeMs);
    assert.deepEqual(afterEntries, beforeEntries);
});

test("missing file has a bounded FILE_NOT_FOUND result", async () => {
    const result = await inspectGeneratedPng(path.join(os.tmpdir(), "tegaki-png-recovery-does-not-exist.png"));
    assert.equal(result.ok, false);
    assert.equal(result.error.code, ERROR_CODES.FILE_NOT_FOUND);
});
