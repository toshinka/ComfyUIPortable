/** Bounded settings-import proposal tests; no UI, runtime, or generation. */
import test from "node:test";
import assert from "node:assert/strict";
import { deflateSync } from "node:zlib";

import {
    EVIDENCE_CLASSES,
    READINESS,
    buildSettingsImportProposal
} from "../service/result_settings_import.mjs";
import { inspectPngBuffer } from "../service/result_metadata_recovery.mjs";

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

function tinyPng({ width = 1, height = 1, metadata = [] } = {}) {
    const ihdr = Buffer.alloc(13);
    ihdr.writeUInt32BE(width, 0);
    ihdr.writeUInt32BE(height, 4);
    ihdr[8] = 8;
    ihdr[9] = 6;
    const scanline = Buffer.alloc(width * 4 + 1, 255);
    scanline[0] = 0;
    const idat = deflateSync(Buffer.concat(Array.from({ length: height }, () => scanline)));
    return Buffer.concat([
        PNG_SIGNATURE,
        pngChunk("IHDR", ihdr),
        ...metadata,
        pngChunk("IDAT", idat),
        pngChunk("IEND", Buffer.alloc(0))
    ]);
}

function simpleRecovered(hints, extra = {}) {
    return {
        ok: true,
        status: "OK",
        warnings: [],
        normalized_hints: hints,
        ...extra
    };
}

function fullGraph() {
    return {
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
                positive: ["3", 0], negative: ["4", 0], latent_image: ["5", 0], denoise: 1
            }
        }
    };
}

test("full simple ComfyUI metadata yields reviewable candidates with provenance", () => {
    const result = buildSettingsImportProposal(simpleRecovered({
        positive_prompt: "1girl, ink",
        negative_prompt: "blurry",
        checkpoint: "Illustrious.safetensors",
        lora_references: [{ name: "style/ink.safetensors", strength_model: 0.7, strength_clip: 0.55, source: "workflow" }],
        seed: 0,
        steps: 24,
        cfg: 6.5,
        sampler: "euler",
        scheduler: "normal",
        width: 832,
        height: 1216,
        dimension_source: "workflow"
    }));
    assert.equal(result.ok, true);
    assert.equal(result.status, "PROPOSAL_READY");
    assert.equal(result.proposal_only, true);
    assert.equal(result.fields.positive_prompt.value, "1girl, ink");
    assert.equal(result.fields.positive_prompt.source, "PNG prompt graph");
    assert.equal(result.fields.seed.value, 0);
    assert.equal(result.fields.checkpoint.requested_id, "Illustrious.safetensors");
    assert.equal(result.fields.loras.value[0].requested_id, "style/ink.safetensors");
    assert.equal(result.fields.loras.value[0].strength, 0.7);
    assert.equal(result.fields.dimensions.value.width, 832);
    assert.equal(result.fields.dimensions.partial, false);
});

test("prompt and negative prompt can stand alone without resource claims", () => {
    const result = buildSettingsImportProposal(simpleRecovered({
        positive_prompt: "a quiet panel",
        negative_prompt: "low quality"
    }));
    assert.equal(result.fields.positive_prompt.readiness, READINESS.READY_TO_REVIEW);
    assert.equal(result.fields.negative_prompt.readiness, READINESS.READY_TO_REVIEW);
    assert.equal(result.summary.candidate_count, 2);
    assert.equal(result.summary.resource_check_required, false);
});

test("checkpoint without caller evidence remains an unknown requested resource", () => {
    const result = buildSettingsImportProposal(simpleRecovered({ checkpoint: "models/illustrious.safetensors" }));
    assert.equal(result.fields.checkpoint.value, "models/illustrious.safetensors");
    assert.equal(result.fields.checkpoint.availability, "UNKNOWN");
    assert.equal(result.fields.checkpoint.readiness, READINESS.NEEDS_RESOURCE_RESOLUTION);
    assert.equal(result.summary.resource_check_required, true);
    assert.ok(result.warnings.some(item => item.code === "RESOURCE_AVAILABILITY_UNKNOWN"));
});

test("caller-reported missing checkpoint is preserved without substitution", () => {
    const result = buildSettingsImportProposal(
        simpleRecovered({ checkpoint: "missing.safetensors" }),
        { availability: { checkpoint: { "missing.safetensors": "MISSING" } } }
    );
    assert.equal(result.fields.checkpoint.value, "missing.safetensors");
    assert.equal(result.fields.checkpoint.availability, "MISSING");
    assert.equal(result.fields.checkpoint.resolution_state, "MISSING");
    assert.equal(result.fields.checkpoint.readiness, READINESS.NEEDS_RESOURCE_RESOLUTION);
});

test("LoRA identity and strength are retained with exact requested ID", () => {
    const result = buildSettingsImportProposal(simpleRecovered({
        lora_references: [{ name: "style/ink.safetensors", strength_model: 0.7, strength_clip: 0.55, source: "workflow" }]
    }));
    const lora = result.fields.loras.value[0];
    assert.equal(lora.requested_id, "style/ink.safetensors");
    assert.equal(lora.strength, 0.7);
    assert.equal(lora.strength_clip, 0.55);
    assert.equal(lora.availability, "UNKNOWN");
    assert.equal(result.fields.loras.readiness, READINESS.NEEDS_RESOURCE_RESOLUTION);
});

test("seed zero is retained and sampler/scheduler are never substituted", () => {
    const result = buildSettingsImportProposal(simpleRecovered({
        seed: 0,
        sampler: "euler_smea_dy",
        scheduler: "sgm_uniform"
    }));
    assert.equal(result.fields.seed.value, 0);
    assert.equal(result.fields.sampler.value, "euler_smea_dy");
    assert.equal(result.fields.scheduler.value, "sgm_uniform");
    assert.equal(result.fields.sampler.availability, "UNKNOWN");
    assert.equal(result.fields.scheduler.availability, "UNKNOWN");
});

test("dimensions preserve both values and explicitly mark a partial result", () => {
    const full = buildSettingsImportProposal(simpleRecovered({ width: 768, height: 1024 }));
    assert.deepEqual(full.fields.dimensions.value, { width: 768, height: 1024 });
    assert.equal(full.fields.dimensions.partial, false);

    const partial = buildSettingsImportProposal(simpleRecovered({ width: 768 }));
    assert.deepEqual(partial.fields.dimensions.value, { width: 768, height: null });
    assert.equal(partial.fields.dimensions.partial, true);
    assert.ok(partial.fields.dimensions.warnings.some(item => item.code === "PARTIAL_DIMENSIONS"));
});

test("ambiguous conditioning is reported without a fake flat prompt", () => {
    const result = buildSettingsImportProposal(simpleRecovered(
        { negative_prompt: "blurry" },
        { warnings: [{ code: "AMBIGUOUS_PROMPT_GRAPH", message: "Positive conditioning has multiple paths" }] }
    ));
    assert.equal(result.fields.positive_prompt.value, null);
    assert.equal(result.fields.positive_prompt.evidence, EVIDENCE_CLASSES.AMBIGUOUS);
    assert.equal(result.fields.positive_prompt.readiness, READINESS.AMBIGUOUS);
    assert.equal(result.candidates.some(item => item.field === "positive_prompt"), false);
    assert.deepEqual(result.summary.ambiguous_fields, ["positive_prompt"]);
    assert.equal(result.fields.negative_prompt.value, "blurry");
});

test("missing metadata remains a valid empty proposal while PNG dimensions stay explicit", () => {
    const recovered = inspectPngBuffer(tinyPng({ width: 320, height: 480 }));
    const result = buildSettingsImportProposal(recovered);
    assert.equal(recovered.status, "METADATA_ABSENT");
    assert.equal(result.ok, true);
    assert.equal(result.fields.positive_prompt.evidence, EVIDENCE_CLASSES.UNAVAILABLE);
    assert.equal(result.fields.width.value, 320);
    assert.equal(result.fields.height.value, 480);
    assert.equal(result.summary.candidate_count, 2);
    assert.ok(result.warnings.some(item => item.code === "METADATA_ABSENT"));
});

test("malformed or non-finite numeric hints are omitted", () => {
    const result = buildSettingsImportProposal(simpleRecovered({
        seed: Number.NaN,
        cfg: Number.POSITIVE_INFINITY,
        width: 832,
        height: 1216
    }));
    assert.equal(result.fields.seed.value, null);
    assert.equal(result.fields.cfg.value, null);
    assert.equal(result.fields.width.value, 832);
    assert.equal(result.fields.height.value, 1216);
    assert.ok(result.fields.seed.warnings.some(item => item.code === "INVALID_NUMERIC_HINT"));
});

test("malformed LoRA list fails closed rather than returning a partial list", () => {
    const result = buildSettingsImportProposal(simpleRecovered({
        lora_references: [{ name: "good.safetensors", strength_model: 0.5 }, { strength_model: 0.2 }]
    }));
    assert.equal(result.fields.loras.value, null);
    assert.equal(result.fields.loras.evidence, EVIDENCE_CLASSES.AMBIGUOUS);
    assert.equal(result.fields.loras.readiness, READINESS.AMBIGUOUS);
    assert.equal(result.candidates.some(item => item.field === "loras"), false);
});

test("proposal construction does not mutate metadata or availability facts", () => {
    const recovered = simpleRecovered({
        checkpoint: "Illustrious.safetensors",
        lora_references: [{ name: "style.safetensors", strength_model: 0.4 }]
    });
    const availability = { checkpoint: { "Illustrious.safetensors": { state: "AVAILABLE" } } };
    const beforeRecovered = structuredClone(recovered);
    const beforeAvailability = structuredClone(availability);
    buildSettingsImportProposal(recovered, { availability });
    assert.deepEqual(recovered, beforeRecovered);
    assert.deepEqual(availability, beforeAvailability);
});

test("identical input produces an identical deterministic proposal", () => {
    const recovered = simpleRecovered({
        positive_prompt: "1girl",
        negative_prompt: "blurry",
        seed: -1,
        width: 512,
        height: 512
    });
    const first = buildSettingsImportProposal(recovered);
    const second = buildSettingsImportProposal(recovered);
    assert.deepEqual(second, first);
    assert.equal(first.fields.seed.value, -1, "proposal preserves sentinel; server resolution is separate");
});

test("inspectPngBuffer output feeds the proposal builder without a bridge", () => {
    const recovered = inspectPngBuffer(tinyPng({
        width: 832,
        height: 1216,
        metadata: [textChunk("prompt", JSON.stringify(fullGraph()))]
    }));
    const result = buildSettingsImportProposal(recovered);
    assert.equal(result.ok, true);
    assert.equal(result.fields.positive_prompt.value, "1girl, <lora:prompt_style:0.4>");
    assert.equal(result.fields.negative_prompt.value, "low quality, blurry");
    assert.equal(result.fields.checkpoint.requested_id, "Illustrious.safetensors");
    assert.equal(result.fields.loras.value[0].requested_id, "style/ink.safetensors");
    assert.equal(result.fields.seed.value, 0);
    assert.equal(result.fields.dimensions.value.width, 832);
});
