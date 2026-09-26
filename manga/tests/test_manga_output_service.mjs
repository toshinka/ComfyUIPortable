// MANGA-EXPERIMENT-OUTPUT-PRODUCTION1: filename tokens, sanitization, collision safety, named copies
// derived from the job record, Grid artifact storage, and the parameterless output-folder shortcut.
import test from "node:test";
import assert from "node:assert/strict";
import { EventEmitter } from "node:events";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import {
    DEFAULT_FILENAME_TEMPLATE, MangaOutputError, MangaOutputService, namingValuesFromJob, renderFilenameBase,
    resolveMangaOutputDir, validateTemplate, writeExclusive
} from "../service/manga_output_service.mjs";

const PNG = Buffer.concat([Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]), Buffer.from("fake-png-body")]);
const NOW = new Date(2026, 8, 27, 9, 5, 7);
const tmp = () => fs.mkdtempSync(path.join(os.tmpdir(), "manga-output-"));
const JOB = {
    job_id: "11111111-2222-4333-8444-555555555555", state: "SUCCEEDED",
    requested_settings: { checkpoint_id: "!新規SDモデル\\comicBookIllustrious_illustriousV11.safetensors", seed_requested: "-1",
        positive_raw: "1girl, <lora:zeta:0.3>, <lora:alpha:0.5>" },
    effective_settings: { checkpoint_id: "!新規SDモデル\\comicBookIllustrious_illustriousV11.safetensors", seed_requested: "123456" },
    resolved_loras: [{ id: "chars\\zeta_v2.safetensors", weight_model: 0.3 }, { id: "alpha.safetensors", weight_model: 0.5 }],
};
const fakeGeneration = (job = JOB) => ({
    calls: [],
    async getJob(id) { this.calls.push(["getJob", id]); if (id !== job.job_id) throw new MangaOutputError("JOB_NOT_FOUND", "nope", 404); return job; },
    async getResult(id) { this.calls.push(["getResult", id]); return PNG; },
});

test("output root uses the MangaDomainRuntime formula (env override or <portable>/output/Tegaki)", () => {
    assert.equal(resolveMangaOutputDir({ env: {}, portableRoot: "/p" }), path.resolve("/p/output/Tegaki"));
    assert.equal(resolveMangaOutputDir({ env: { TEGAKI_MANGA_OUTPUT_DIR: " /x/out " }, portableRoot: "/p" }), path.resolve("/x/out"));
});

test("tokens: {checkpoint} stem without directories, {first_lora}, {suffix}, {seed}, {index}, {date}/{time}", () => {
    const values = { ...namingValuesFromJob(JOB), suffix: "MANGA", index: 3, axis: "ckB-karras" };
    assert.equal(renderFilenameBase(DEFAULT_FILENAME_TEMPLATE, values, { now: NOW }),
        "comicBookIllustrious_illustriousV11_zeta_v2_MANGA_123456");
    assert.equal(renderFilenameBase("{checkpoint}_{suffix}_{index}_{axis}_{date}-{time}", values, { now: NOW }),
        "comicBookIllustrious_illustriousV11_MANGA_003_ckB-karras_20260927-090507");
    assert.equal(renderFilenameBase("{checkpoint}_{first_lora}_{suffix}", { checkpoint_id: "a/b/c.safetensors" }, { now: NOW }), "c",
        "empty first_lora/suffix collapse; no directory");
    assert.equal(namingValuesFromJob({ ...JOB, resolved_loras: [] }).first_lora, "", "no LoRA -> empty");
    assert.equal(namingValuesFromJob(JOB).first_lora, "zeta_v2", "first in generation order, stem only");
    assert.equal(namingValuesFromJob(JOB).seed, "123456", "effective seed, not the -1 request");
});

test("sanitization: Windows-invalid characters only; Unicode kept; bounded; reserved names; never a path", () => {
    assert.equal(renderFilenameBase("{suffix}", { suffix: "漫画<>:\"/\\|?*テスト" }, { now: NOW }), "漫画_テスト");
    assert.equal(renderFilenameBase("{checkpoint}", { checkpoint_id: "日本語モデル★v2.safetensors" }, { now: NOW }), "日本語モデル★v2");
    assert.equal(renderFilenameBase("a/b\\c{suffix}", { suffix: "" }, { now: NOW }), "a_b_c", "literal separators are neutralised");
    assert.equal(renderFilenameBase("{suffix}", { suffix: "CON" }, { now: NOW }), "_CON");
    assert.equal(renderFilenameBase("{suffix}", { suffix: "..." }, { now: NOW }), "manga");
    assert.ok(renderFilenameBase("{suffix}{axis}{checkpoint}{first_lora}", { suffix: "s".repeat(500), axis: "a".repeat(500),
        checkpoint_id: "c".repeat(500), first_lora: "l".repeat(500) }, { now: NOW }).length <= 150);
    assert.match(validateTemplate("{checkpoint}_{bogus}"), /Unknown filename token: \{bogus\}/);
    assert.match(validateTemplate("{checkpoint"), /Unbalanced/);
    assert.match(validateTemplate("  "), /empty/);
    assert.throws(() => renderFilenameBase("{nope}", {}), err => err.code === "INVALID_TEMPLATE");
});

test("collision policy: exclusive create, deterministic _001/_002, never overwrites", () => {
    const dir = tmp();
    const a = writeExclusive(dir, "same", Buffer.from("A"));
    const b = writeExclusive(dir, "same", Buffer.from("B"));
    const c = writeExclusive(dir, "same", Buffer.from("C"));
    assert.deepEqual([a.filename, b.filename, c.filename], ["same.png", "same_001.png", "same_002.png"]);
    assert.equal(fs.readFileSync(path.join(dir, "same.png"), "utf8"), "A", "original untouched");
});

test("named copy: values come from the SUCCEEDED job record; suffix never touches the prompt; owned output untouched", async () => {
    const dir = tmp();
    const generation = fakeGeneration();
    const service = new MangaOutputService({ outputDir: dir, generationService: generation, clock: () => NOW });
    const before = structuredClone(JOB);
    const first = await service.namedCopy({ job_id: JOB.job_id, template: "{checkpoint}_{first_lora}_{suffix}_{seed}", suffix: "ANIME" });
    assert.deepEqual(first, { filename: "comicBookIllustrious_illustriousV11_zeta_v2_ANIME_123456.png", folder: "Manga/Named" });
    const second = await service.namedCopy({ job_id: JOB.job_id, template: "{checkpoint}_{first_lora}_{suffix}_{seed}", suffix: "ANIME" });
    assert.equal(second.filename, "comicBookIllustrious_illustriousV11_zeta_v2_ANIME_123456_001.png");
    assert.deepEqual(fs.readFileSync(path.join(dir, "Manga", "Named", first.filename)), PNG);
    assert.deepEqual(JOB, before, "job record (and its prompt) unchanged by suffix/naming");
    assert.equal(fs.existsSync(path.join(dir, "Manga", "Playable")), false, "owned job namespace never written");
    await assert.rejects(service.namedCopy({ job_id: JOB.job_id, template: "{x}" }), err => err.code === "INVALID_TEMPLATE");
    await assert.rejects(service.namedCopy({ job_id: JOB.job_id, index: 0 }), err => err.code === "INVALID_INDEX");
    const pending = new MangaOutputService({ outputDir: dir, generationService: fakeGeneration({ ...JOB, state: "RUNNING" }) });
    await assert.rejects(pending.namedCopy({ job_id: JOB.job_id }), err => err.code === "RESULT_NOT_READY");
    // Browser-supplied checkpoint/seed/path fields are ignored for real copies.
    const spoof = await service.namedCopy({ job_id: JOB.job_id, template: "{checkpoint}_{seed}", checkpoint_id: "../../evil", seed: "666", path: "C:/Windows" });
    assert.equal(spoof.filename, "comicBookIllustrious_illustriousV11_123456.png");
});

test("preview is pure (no filesystem writes) and reports the rendered name", () => {
    const dir = tmp();
    const service = new MangaOutputService({ outputDir: dir, clock: () => NOW });
    const data = service.preview({ template: "{checkpoint}_{first_lora}_{suffix}_{seed}_{index}", suffix: "MANGA",
        checkpoint_id: "x\\model.safetensors", first_lora: "dir/lo.safetensors", seed: "42", index: 4 });
    assert.deepEqual(data, { base: "model_lo_MANGA_42_004", filename: "model_lo_MANGA_42_004.png", folder: "Manga/Named" });
    assert.deepEqual(fs.readdirSync(dir), []);
});

test("grid artifact: PNG only, bounded, label is a fragment (never a path), collision-safe", () => {
    const dir = tmp();
    const service = new MangaOutputService({ outputDir: dir, clock: () => NOW });
    assert.equal(service.saveGrid(PNG, "ANIME").filename, "ANIME_grid.png");
    assert.equal(service.saveGrid(PNG, "ANIME").filename, "ANIME_grid_001.png");
    assert.equal(service.saveGrid(PNG, "../../x").filename, "x_grid.png", "separators neutralised, stays in Manga/Grids");
    const files = fs.readdirSync(path.join(dir, "Manga", "Grids"));
    assert.ok(files.every(name => !name.includes("/") && !name.includes("\\")));
    assert.throws(() => service.saveGrid(Buffer.from("not png"), "a"), err => err.code === "INVALID_PNG");
});

class FakeChild extends EventEmitter { unref() { this.unrefed = true; } }

test("folder shortcut: fixed directory, explorer.exe only, no shell, Windows only, clear failures", async () => {
    const dir = tmp();
    fs.mkdirSync(path.join(dir, "Manga"));
    const calls = [];
    const spawnFn = (command, args, options) => {
        calls.push({ command, args, options });
        const child = new FakeChild();
        queueMicrotask(() => child.emit("spawn"));
        return child;
    };
    const service = new MangaOutputService({ outputDir: dir, platform: "win32", spawnFn });
    assert.deepEqual(await service.openFolder(), { opened: true, folder: "Manga" });
    assert.deepEqual(calls, [{ command: "explorer.exe", args: [path.join(dir, "Manga")],
        options: { detached: true, stdio: "ignore", shell: false, windowsHide: false } }]);
    assert.equal(service.openFolder.length, 0, "openFolder accepts no arguments at all");
    await assert.rejects(new MangaOutputService({ outputDir: dir, platform: "linux", spawnFn }).openFolder(), err => err.code === "UNSUPPORTED_PLATFORM" && err.status === 501);
    await assert.rejects(new MangaOutputService({ outputDir: path.join(dir, "missing"), platform: "win32", spawnFn }).openFolder(), err => err.code === "OUTPUT_DIR_MISSING");
    const failing = new MangaOutputService({ outputDir: dir, platform: "win32", spawnFn: () => {
        const child = new FakeChild(); queueMicrotask(() => child.emit("error", Object.assign(new Error("x"), { code: "ENOENT" }))); return child; } });
    await assert.rejects(failing.openFolder(), err => err.code === "EXPLORER_FAILED");
});

test("HTTP: output routes are POST-only, same-origin, and the folder route rejects any path/parameters", async () => {
    const out = tmp();
    fs.mkdirSync(path.join(out, "Manga"));
    const oldPort = process.env.MANGA_WORKSPACE_PORT;
    const oldOut = process.env.TEGAKI_MANGA_OUTPUT_DIR;
    process.env.MANGA_WORKSPACE_PORT = "0";
    process.env.TEGAKI_MANGA_OUTPUT_DIR = out;
    const mod = await import(`../service/manga_workspace_server.mjs?output=${Date.now()}`);
    const { server } = mod;
    if (!server.listening) await new Promise(resolve => server.once("listening", resolve));
    const origin = `http://127.0.0.1:${server.address().port}`;
    const calls = [];
    const spawnFn = (command, args) => { calls.push([command, args]); const c = new FakeChild(); queueMicrotask(() => c.emit("spawn")); return c; };
    mod.setMangaOutputService(new MangaOutputService({ outputDir: out, platform: "win32", spawnFn, generationService: fakeGeneration(), clock: () => NOW }));
    const post = (route, body, headers = { "Content-Type": "application/json" }) => fetch(`${origin}${route}`, { method: "POST", headers, body });
    try {
        assert.equal((await fetch(`${origin}/api/manga/output/open-folder`)).status, 405);
        const opened = await post("/api/manga/output/open-folder", "{}");
        assert.equal(opened.status, 200);
        assert.deepEqual(await opened.json(), { ok: true, opened: true, folder: "Manga" });
        const withPath = await post("/api/manga/output/open-folder", JSON.stringify({ path: "C:\\Windows" }));
        assert.equal(withPath.status, 400);
        assert.equal((await withPath.json()).error_code, "UNEXPECTED_PARAMETERS");
        assert.equal((await post("/api/manga/output/open-folder?path=C:%5CWindows", "{}")).status, 400);
        assert.equal((await post("/api/manga/output/open-folder", "{}", { "Content-Type": "application/json", Origin: "http://evil.example" })).status, 403);
        assert.deepEqual(calls, [["explorer.exe", [path.join(out, "Manga")]]], "exactly one launch, fixed directory");
        const preview = await post("/api/manga/output/filename-preview", JSON.stringify({ template: "{checkpoint}_{suffix}", suffix: "MANGA", checkpoint_id: "m/x.safetensors" }));
        assert.deepEqual(await preview.json(), { ok: true, base: "x_MANGA", filename: "x_MANGA.png", folder: "Manga/Named" });
        const badTemplate = await post("/api/manga/output/filename-preview", JSON.stringify({ template: "{evil}" }));
        assert.equal(badTemplate.status, 400);
        const named = await post("/api/manga/output/named-copy", JSON.stringify({ job_id: JOB.job_id, template: "{checkpoint}", suffix: "" }));
        assert.equal((await named.json()).filename, "comicBookIllustrious_illustriousV11.png");
        const grid = await post("/api/manga/output/grid?label=MANGA", PNG, { "Content-Type": "image/png" });
        assert.deepEqual(await grid.json(), { ok: true, filename: "MANGA_grid.png", folder: "Manga/Grids" });
        assert.equal((await post("/api/manga/output/grid?label=a&dir=C:%5C", PNG, { "Content-Type": "image/png" })).status, 400);
        assert.equal((await post("/api/manga/output/unknown", "{}")).status, 404);
    } finally {
        await new Promise(resolve => server.close(resolve));
        if (oldPort == null) delete process.env.MANGA_WORKSPACE_PORT; else process.env.MANGA_WORKSPACE_PORT = oldPort;
        if (oldOut == null) delete process.env.TEGAKI_MANGA_OUTPUT_DIR; else process.env.TEGAKI_MANGA_OUTPUT_DIR = oldOut;
    }
});
