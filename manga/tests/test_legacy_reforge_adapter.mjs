// MANGA-LEGACY-EASYREFORGE-VERTICAL-MVP1: LegacyReforgeAdapter recipe -> txt2img translation.
// Pure; no process, no network, no GPU.
import test from "node:test";
import assert from "node:assert/strict";
import {
    COMFY_TO_LEGACY_SAMPLER, buildTxt2ImgRequest, extractLoraRecipe, mapCheckpoint, mapLora, mapSampler,
    mapScheduler, mapVae, parseTxt2ImgResponse, validateRecipe
} from "../service/legacy_reforge_adapter.mjs";

const RT = "E:\\TEGAKI_Runtime\\EasyReforge\\Model";
const CATALOG = Object.freeze({
    sdModels: [
        { title: "!新規SDモデル\\comicBookIllustrious_illustriousV11.safetensors [abc123]", model_name: "comicBook",
            filename: `${RT}\\Stable-diffusion\\!新規SDモデル\\comicBookIllustrious_illustriousV11.safetensors` },
        { title: "other\\dup.safetensors [1]", filename: `${RT}\\Stable-diffusion\\other\\dup.safetensors` },
        { title: "x\\other\\dup.safetensors [2]", filename: `${RT}\\Stable-diffusion\\x\\other\\dup.safetensors` },
    ],
    sdVae: [{ model_name: "XlVaeC_f2.safetensors", filename: `${RT}\\VAE\\XlVaeC_f2.safetensors` }],
    loras: [
        { name: "2000s_anime_style", path: `${RT}\\Lora\\!!!Ani\\Ani0H\\2000s_anime_style.safetensors` },
        { name: "2020s_anime_style", path: `${RT}\\Lora\\!!!Ani\\Ani0H\\2020s_anime_style.safetensors` },
        { name: "twin", path: `${RT}\\Lora\\a\\twin.safetensors` },
        { name: "twin", path: `${RT}\\Lora\\b\\twin.safetensors` },
    ],
    samplers: [{ name: "Euler a" }, { name: "Euler" }, { name: "DPM++ 2M" }, { name: "Euler SMEA Dy" }],
    schedulers: [{ name: "automatic" }, { name: "karras" }, { name: "sgm_uniform" }, { name: "phi" }],
});
const RECIPE = Object.freeze({
    engine: "easyreforge",
    checkpoint_id: "!新規SDモデル\\comicBookIllustrious_illustriousV11.safetensors",
    vae_id: "",
    positive_raw: "1girl, <lora:2020s_anime_style:0.72>, smile, <lora:2000s_anime_style:0.45>",
    negative_raw: "lowres, bad hands",
    sampler: "Euler a", scheduler: "karras",
    steps: 28, cfg: 5.5, width: 832, height: 1216, seed_requested: "12345",
});
const RESULT_PNG = Buffer.from("89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4890000000a49444154789c63000100000500010d0a2db40000000049454e44ae426082", "hex");
const RESULT_JPEG = Buffer.from("/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0aHBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/2wBDAQkJCQwLDBgNDRgyIRwhMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjL/wAARCAABAAEDASIAAhEBAxEB/8QAHwAAAQUBAQEBAQEAAAAAAAAAAAECAwQFBgcICQoL/8QAtRAAAgEDAwIEAwUFBAQAAAF9AQIDAAQRBRIhMUEGE1FhByJxFDKBkaEII0KxwRVS0fAkM2JyggkKFhcYGRolJicoKSo0NTY3ODk6Q0RFRkdISUpTVFVWV1hZWmNkZWZnaGlqc3R1dnd4eXqDhIWGh4iJipKTlJWWl5iZmqKjpKWmp6ipqrKztLW2t7i5usLDxMXGx8jJytLT1NXW19jZ2uHi4+Tl5ufo6erx8vP09fb3+Pn6/8QAHwEAAwEBAQEBAQEBAQAAAAAAAAECAwQFBgcICQoL/8QAtREAAgECBAQDBAcFBAQAAQJ3AAECAxEEBSExBhJBUQdhcRMiMoEIFEKRobHBCSMzUvAVYnLRChYkNOEl8RcYGRomJygpKjU2Nzg5OkNERUZHSElKU1RVVldYWVpjZGVmZ2hpanN0dXZ3eHl6goOEhYaHiImKkpOUlZaXmJmaoqOkpaanqKmqsrO0tba3uLm6wsPExcbHyMnK0tPU1dbX2Nna4uPk5ebn6Onq8vP09fb3+Pn6/9oADAMBAAIRAxEAPwD3+iiigD//2Q==", "base64");

test("recipe translation: checkpoint, prompts, seed, steps, CFG, size preserved; no ReForge fields persisted", () => {
    const recipe = structuredClone(RECIPE);
    const { payload, metadata } = buildTxt2ImgRequest(recipe, CATALOG);
    assert.equal(payload.override_settings.sd_model_checkpoint, "!新規SDモデル\\comicBookIllustrious_illustriousV11.safetensors [abc123]");
    assert.equal(payload.negative_prompt, "lowres, bad hands");
    assert.deepEqual([payload.seed, payload.steps, payload.cfg_scale, payload.width, payload.height], [12345, 28, 5.5, 832, 1216]);
    assert.deepEqual([payload.batch_size, payload.n_iter], [1, 1], "exactly one image");
    assert.equal(metadata.checkpoint_id, RECIPE.checkpoint_id, "logical checkpoint identity kept verbatim");
    assert.deepEqual(recipe, RECIPE, "the logical recipe (user prompt) is never mutated");
    assert.ok(!("script_args" in payload) && !("alwayson_scripts" in payload), "no extension/script positional args");
});

test("multiple LoRA: prompt order and exact weight text preserved, tokens rewritten in place", () => {
    const { payload, metadata } = buildTxt2ImgRequest({ ...RECIPE, positive_raw: "a, <lora:2020s_anime_style:0.720>, b, <lora:2000s_anime_style:.45>" }, CATALOG);
    assert.equal(payload.prompt, "a, <lora:2020s_anime_style:0.720>, b, <lora:2000s_anime_style:.45>");
    assert.deepEqual(metadata.loras.map(l => [l.order, l.resource_id, l.weight_text, l.weight]),
        [[0, "2020s_anime_style", "0.720", 0.72], [1, "2000s_anime_style", ".45", 0.45]]);
    const pathToken = buildTxt2ImgRequest({ ...RECIPE, positive_raw: "<lora:!!!Ani/Ani0H/2000s_anime_style:1>" }, CATALOG);
    assert.equal(pathToken.payload.prompt, "<lora:2000s_anime_style:1>", "Manga canonical folder token maps to the Legacy name");
    assert.deepEqual(extractLoraRecipe("x <lora:a:1> y <lora:b:-0.25>").map(t => [t.resource_id, t.weight_text]), [["a", "1"], ["b", "-0.25"]]);
});

test("LoRA mapping fails closed: missing, ambiguous stem, duplicate, malformed, negative, wildcard", () => {
    const code = (fn, expected) => assert.throws(fn, err => err.code === expected, expected);
    code(() => mapLora("nope", CATALOG.loras), "LORA_NOT_FOUND");
    code(() => mapLora("twin", CATALOG.loras), "LORA_AMBIGUOUS");
    code(() => mapLora("a/twin", CATALOG.loras), "LORA_AMBIGUOUS");   // unique path but Legacy resolves by stem
    code(() => buildTxt2ImgRequest({ ...RECIPE, positive_raw: "<lora:2000s_anime_style:1>, <lora:2000s_anime_style:0.5>" }, CATALOG), "LORA_DUPLICATE");
    code(() => buildTxt2ImgRequest({ ...RECIPE, positive_raw: "<lora:2000s_anime_style>" }, CATALOG), "LORA_MALFORMED");
    code(() => buildTxt2ImgRequest({ ...RECIPE, negative_raw: "<lora:2000s_anime_style:1>" }, CATALOG), "LORA_NEGATIVE_UNSUPPORTED");
    code(() => buildTxt2ImgRequest({ ...RECIPE, positive_raw: "__!Quality/manga__" }, CATALOG), "WILDCARD_UNSUPPORTED");
    code(() => buildTxt2ImgRequest({ ...RECIPE, positive_raw: "{red|blue} hair" }, CATALOG), "DYNAMIC_PROMPT_UNSUPPORTED");
});

test("checkpoint identity: exact relative path, never basename guessing; unknown/ambiguous fail closed", () => {
    assert.throws(() => mapCheckpoint("comicBookIllustrious_illustriousV11.safetensors", CATALOG.sdModels.slice(1)), err => err.code === "CHECKPOINT_NOT_FOUND");
    assert.throws(() => mapCheckpoint("other\\dup.safetensors", CATALOG.sdModels), err => err.code === "CHECKPOINT_AMBIGUOUS");
    assert.equal(mapCheckpoint("x/other/dup.safetensors", CATALOG.sdModels).title, "x\\other\\dup.safetensors [2]");
    assert.throws(() => mapCheckpoint("missing.safetensors", CATALOG.sdModels), err => err.code === "CHECKPOINT_NOT_FOUND");
});

test("VAE: empty -> checkpoint VAE ('None', nothing forced); explicit -> exact entry; virtual/unknown fail closed", () => {
    assert.deepEqual(mapVae("", CATALOG.sdVae), { setting: "None", explicit: false });
    assert.equal(buildTxt2ImgRequest(RECIPE, CATALOG).payload.override_settings.sd_vae, "None");
    assert.deepEqual(mapVae("Illustrious\\XlVaeC_f2.safetensors", CATALOG.sdVae), { setting: "XlVaeC_f2.safetensors", explicit: true });
    assert.throws(() => mapVae("taesdxl", CATALOG.sdVae), err => err.code === "VAE_UNSUPPORTED");
    assert.throws(() => mapVae("minimaxH3\\minimax_h3_video_vae_fp16.safetensors", CATALOG.sdVae), err => err.code === "VAE_UNSUPPORTED");
    assert.throws(() => mapVae("Illustrious\\missing.safetensors", CATALOG.sdVae), err => err.code === "VAE_NOT_FOUND");
    const { metadata } = buildTxt2ImgRequest({ ...RECIPE, vae_id: "Illustrious\\XlVaeC_f2.safetensors" }, CATALOG);
    assert.equal(metadata.vae_id, "Illustrious\\XlVaeC_f2.safetensors");
});

test("sampler/scheduler: native Legacy values pass; Comfy ids only via the explicit table; unknown fail closed", () => {
    assert.equal(mapSampler("Euler SMEA Dy", CATALOG.samplers), "Euler SMEA Dy", "Legacy-only algorithm is representable");
    assert.equal(mapSampler("euler_ancestral", CATALOG.samplers), "Euler a");
    assert.equal(COMFY_TO_LEGACY_SAMPLER.dpmpp_2m, "DPM++ 2M");
    assert.throws(() => mapSampler("dpmpp_2m_sde_gpu", CATALOG.samplers), err => err.code === "SAMPLER_UNSUPPORTED");
    assert.throws(() => mapSampler("heun", CATALOG.samplers), err => err.code === "SAMPLER_UNSUPPORTED", "table target missing in catalog -> no substitute");
    assert.equal(mapScheduler("phi", CATALOG.schedulers), "phi");
    assert.equal(mapScheduler("", CATALOG.schedulers), "", "empty scheduler omits the field");
    assert.throws(() => mapScheduler("linear_quadratic", CATALOG.schedulers), err => err.code === "SCHEDULER_UNSUPPORTED");
    assert.throws(() => mapScheduler("karras", []), err => err.code === "SCHEDULER_UNSUPPORTED");
    assert.equal(buildTxt2ImgRequest({ ...RECIPE, scheduler: "" }, CATALOG).payload.scheduler, undefined);
});

test("recipe validation rejects out-of-contract values before anything is sent", () => {
    for (const bad of [{ steps: 0 }, { cfg: 31 }, { width: 830 }, { seed_requested: "-2" }, { checkpoint_id: "" }, { engine: "comfyui" }]) {
        assert.throws(() => validateRecipe({ ...RECIPE, ...bad }), err => err.code === "INVALID_RECIPE", JSON.stringify(bad));
    }
    assert.equal(validateRecipe({ ...RECIPE, seed_requested: "-1" }).seed_requested, "-1");
    assert.equal(buildTxt2ImgRequest({ ...RECIPE, seed_requested: "-1" }, CATALOG).payload.seed, -1);
});

test("result parser: preserves PNG/JPEG bytes, validates declared MIME and rejects malformed or oversized images", () => {
    const { metadata } = buildTxt2ImgRequest(RECIPE, CATALOG);
    const png = parseTxt2ImgResponse({ images: [`data:image/png;base64,${RESULT_PNG.toString("base64")}`],
        info: JSON.stringify({ seed: 12345, sd_model_name: "comicBook" }) }, metadata);
    assert.deepEqual(png.bytes, RESULT_PNG);
    assert.equal(png.mime, "image/png");
    assert.equal(png.result.mime, "image/png");
    assert.equal(png.result.backend, "easyreforge");
    assert.equal(png.result.seed, 12345);
    assert.deepEqual(png.result.loras.map(l => l.resource_id), ["2020s_anime_style", "2000s_anime_style"]);

    const jpeg = parseTxt2ImgResponse({ images: [`data:image/jpeg;base64,${RESULT_JPEG.toString("base64")}`] }, metadata);
    assert.deepEqual(jpeg.bytes, RESULT_JPEG);
    assert.equal(jpeg.mime, "image/jpeg");
    assert.equal(jpeg.result.mime, "image/jpeg");

    for (const [label, response] of [
        ["no images", {}], ["empty", { images: [] }],
        ["PNG declared for JPEG", { images: [`data:image/png;base64,${RESULT_JPEG.toString("base64")}`] }],
        ["JPEG declared for PNG", { images: [`data:image/jpeg;base64,${RESULT_PNG.toString("base64")}`] }],
        ["unsupported WebP", { images: [`data:image/webp;base64,${Buffer.from("RIFF0000WEBP").toString("base64")}`] }],
        ["malformed JPEG", { images: [Buffer.from([0xff, 0xd8, 0xff, 0xd9]).toString("base64")] }],
        ["truncated JPEG", { images: [RESULT_JPEG.subarray(0, -2).toString("base64")] }],
        ["invalid base64", { images: ["%%%="] }],
        ["bad info", { images: [RESULT_PNG.toString("base64")], info: "{not json" }],
    ]) {
        assert.throws(() => parseTxt2ImgResponse(response, metadata), err => err.code === "LEGACY_RESPONSE_INVALID", label);
    }
    const oversized = Buffer.alloc(32 * 1024 * 1024 + 1).toString("base64");
    assert.throws(() => parseTxt2ImgResponse({ images: [oversized] }, metadata), err => err.code === "LEGACY_RESPONSE_INVALID", "decoded payload bound");
});
