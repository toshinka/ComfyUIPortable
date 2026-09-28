// MANGA-LEGACY-EASYREFORGE-VERTICAL-MVP1: supervisor path safety + service/HTTP contract.
// Fakes only: no process is spawned, no network, no GPU.
import test from "node:test";
import assert from "node:assert/strict";
import { EventEmitter } from "node:events";
import {
    INTEGRATION_RUNTIME_ROOT, LegacyReforgeSupervisor, REFERENCE_RUNTIME_ROOT, buildStartCommand, resolveIntegrationRoot,
    resolveLegacyPort
} from "../service/legacy_reforge_supervisor.mjs";
import { LegacyReforgeService, handleLegacyReforgeRequest } from "../service/legacy_reforge_service.mjs";

const PNG = Buffer.concat([Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]), Buffer.alloc(24, 7)]);
const JPEG = Buffer.from("/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0aHBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/2wBDAQkJCQwLDBgNDRgyIRwhMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjL/wAARCAABAAEDASIAAhEBAxEB/8QAHwAAAQUBAQEBAQEAAAAAAAAAAAECAwQFBgcICQoL/8QAtRAAAgEDAwIEAwUFBAQAAAF9AQIDAAQRBRIhMUEGE1FhByJxFDKBkaEII0KxwRVS0fAkM2JyggkKFhcYGRolJicoKSo0NTY3ODk6Q0RFRkdISUpTVFVWV1hZWmNkZWZnaGlqc3R1dnd4eXqDhIWGh4iJipKTlJWWl5iZmqKjpKWmp6ipqrKztLW2t7i5usLDxMXGx8jJytLT1NXW19jZ2uHi4+Tl5ufo6erx8vP09fb3+Pn6/8QAHwEAAwEBAQEBAQEBAQAAAAAAAAECAwQFBgcICQoL/8QAtREAAgECBAQDBAcFBAQAAQJ3AAECAxEEBSExBhJBUQdhcRMiMoEIFEKRobHBCSMzUvAVYnLRChYkNOEl8RcYGRomJygpKjU2Nzg5OkNERUZHSElKU1RVVldYWVpjZGVmZ2hpanN0dXZ3eHl6goOEhYaHiImKkpOUlZaXmJmaoqOkpaanqKmqsrO0tba3uLm6wsPExcbHyMnK0tPU1dbX2Nna4uPk5ebn6Onq8vP09fb3+Pn6/9oADAMBAAIRAxEAPwD3+iiigD//2Q==", "base64");
const existsAll = { existsSync: () => true, realpathSync: p => p };
const noListeners = () => ({ ok: true, listeners: [] });

test("Integration path safety: default target is the Integration Runtime; Reference is rejected", () => {
    assert.equal(resolveIntegrationRoot({ env: {} }), INTEGRATION_RUNTIME_ROOT);
    for (const bad of [REFERENCE_RUNTIME_ROOT, "e:\\easyreforge\\", "E:\\EasyReforge\\stable-diffusion-webui-reForge"]) {
        assert.throws(() => resolveIntegrationRoot({ env: { TEGAKI_REFORGE_RUNTIME: bad } }), err => err.code === "REFERENCE_RUNTIME_FORBIDDEN", bad);
    }
    assert.throws(() => resolveIntegrationRoot({ env: { TEGAKI_REFORGE_RUNTIME: "D:\\Elsewhere\\EasyReforge" } }), err => err.code === "INTEGRATION_ROOT_REQUIRED");
    assert.throws(() => resolveIntegrationRoot({ env: { TEGAKI_REFORGE_RUNTIME: "E:\\TEGAKI_Runtime\\..\\EasyReforge" } }), err => err.code === "REFERENCE_RUNTIME_FORBIDDEN");
    assert.throws(() => resolveIntegrationRoot({ env: {}, realpath: () => "E:\\EasyReforge" }), err => err.code === "REFERENCE_RUNTIME_FORBIDDEN",
        "a junction redirecting the Integration root into the Reference is refused");
    assert.throws(() => resolveLegacyPort({ TEGAKI_REFORGE_PORT: "7860" }), err => err.code === "LEGACY_PORT_INVALID", "Reference default port is never shared");
    assert.equal(resolveLegacyPort({}), 7862);
});

test("start command targets ONLY the Integration Runtime launcher chain with --api and a dedicated port", () => {
    const spec = buildStartCommand(INTEGRATION_RUNTIME_ROOT, 7862, { COMMANDLINE_ARGS: "--x", PYTHONPATH: "C:\\comfy", KEEP: "1" });
    assert.equal(spec.command, "cmd.exe");
    assert.equal(spec.options.cwd, INTEGRATION_RUNTIME_ROOT);
    assert.equal(spec.launcher, "E:\\TEGAKI_Runtime\\EasyReforge\\Reforge.bat");
    assert.equal(spec.args.at(-1), '""E:\\TEGAKI_Runtime\\EasyReforge\\Reforge.bat" --api --port 7862"');
    assert.ok(!spec.args.join(" ").toLowerCase().includes("e:\\easyreforge\\"), "Reference path never appears in the command");
    assert.equal(spec.options.env.COMMANDLINE_ARGS, "", "inherited COMMANDLINE_ARGS cannot leak into the launcher");
    assert.equal(spec.options.env.PYTHONPATH, undefined);
    assert.equal(spec.options.env.KEEP, "1");
    assert.equal(spec.options.env.SD_WEBUI_RESTARTING, "1",
        "TEGAKI-started ReForge keeps its WebUI server but never auto-opens a browser tab (webui.py inbrowser gate)");
    assert.ok(!spec.args.join(" ").includes("--nowebui"), "the WebUI/extension initialisation path is unchanged");
    assert.throws(() => buildStartCommand(REFERENCE_RUNTIME_ROOT, 7862, {}), err => err.code === "REFERENCE_RUNTIME_FORBIDDEN");
});

class FakeChild extends EventEmitter {
    constructor(pid) { super(); this.pid = pid; this.stdout = new EventEmitter(); this.stderr = new EventEmitter(); }
    kill() { this.emit("exit", 1); }
}

test("supervisor ownership: refuses a foreign API on the port, starts, becomes ready, stops only its own tree", async () => {
    const spawned = [];
    let apiUp = true;
    const client = { ping: async () => apiUp };
    const spawnFn = (command, args) => {
        const child = new FakeChild(spawned.length + 500);
        spawned.push({ command, args, child });
        if (command === "taskkill") queueMicrotask(() => { child.emit("exit", 0); spawned[0].child.emit("exit", 1); });
        return child;
    };
    const sup = new LegacyReforgeSupervisor({ env: {}, fsImpl: existsAll, spawnFn, client, platform: "win32",
        listenerInspector: noListeners, pollMs: 1, sleep: async () => {} });
    await assert.rejects(sup.start(), err => err.code === "FOREIGN_PROCESS_ON_PORT");
    assert.equal(spawned.length, 0, "nothing spawned while another process owns the port");
    apiUp = false;
    let pings = 0;
    client.ping = async () => (++pings > 2);
    const status = await sup.start();
    assert.equal(status.state, "ready");
    assert.equal(status.owned, true);
    assert.equal(spawned[0].command, "cmd.exe");
    spawned[0].child.stdout.emit("data", "Loading... civitai_api_key=SECRET-VALUE\nModel loaded\n");
    assert.ok(!JSON.stringify(sup.status()).includes("SECRET-VALUE"), "secret-looking log lines are withheld");
    const stopped = await sup.stop();
    assert.equal(stopped.state, "stopped");
    assert.deepEqual(spawned[1].args, ["/PID", "500", "/T", "/F"], "taskkill targets the owned PID tree only");
});

test("verified external Integration runtime is ready and reusable without becoming owned", async () => {
    const spawned = [];
    let listening = true;
    const listenerInspector = () => ({ ok: true, listeners: listening ? [{ pid: 37828,
        executable: "E:\\TEGAKI_Runtime\\EasyReforge\\stable-diffusion-webui-reForge\\venv\\Scripts\\python.exe" }] : [] });
    const client = { ping: async () => true };
    const sup = new LegacyReforgeSupervisor({ env: {}, fsImpl: existsAll, spawnFn: (...args) => spawned.push(args), client,
        platform: "win32", listenerInspector });
    const service = new LegacyReforgeService({ supervisor: sup, client });

    const status = await service.refreshStatus();
    assert.deepEqual([status.installed, status.state, status.ready, status.available, status.owned, status.pid],
        [true, "ready", true, true, false, 37828]);
    const begun = await sup.begin();
    assert.deepEqual([begun.state, begun.owned, begun.pid], ["ready", false, 37828]);
    assert.equal(spawned.length, 0, "begin reuses the verified process without spawning a second ReForge");

    const stopped = await service.stop();
    assert.deepEqual([stopped.state, stopped.owned, stopped.pid], ["ready", false, 37828], "stop is a truthful no-op for an external process");
    assert.equal(spawned.length, 0, "external process was not terminated");

    listening = false;
    const gone = await service.refreshStatus();
    assert.deepEqual([gone.state, gone.ready, gone.available, gone.owned, gone.pid], ["stopped", false, false, false, null]);
});

test("unknown 7862 responder fails closed and stopped Integration remains unavailable", async () => {
    const spawned = [];
    const unknown = new LegacyReforgeSupervisor({ env: {}, fsImpl: existsAll, client: { ping: async () => true }, platform: "win32",
        listenerInspector: () => ({ ok: true, listeners: [{ pid: 777, executable: "C:\\Other\\python.exe" }] }),
        spawnFn: (...args) => spawned.push(args) });
    const unknownService = new LegacyReforgeService({ supervisor: unknown, client: unknown.client });
    const status = await unknownService.refreshStatus();
    assert.deepEqual([status.state, status.ready, status.available, status.owned], ["failed", false, false, false]);
    await assert.rejects(unknown.begin(), err => err.code === "FOREIGN_PROCESS_ON_PORT");
    assert.equal(spawned.length, 0, "unknown listener is never replaced");

    const stopped = new LegacyReforgeSupervisor({ env: {}, fsImpl: existsAll, client: { ping: async () => false }, platform: "win32",
        listenerInspector: noListeners });
    const stoppedStatus = await new LegacyReforgeService({ supervisor: stopped, client: stopped.client }).refreshStatus();
    assert.deepEqual([stoppedStatus.state, stoppedStatus.ready, stoppedStatus.available, stoppedStatus.owned], ["stopped", false, false, false]);
});

test("supervisor reports unavailable when the Integration Runtime is incomplete or not Windows", () => {
    const missing = new LegacyReforgeSupervisor({ env: {}, fsImpl: { existsSync: p => !p.endsWith("python.exe"), realpathSync: p => p }, platform: "win32" });
    assert.equal(missing.status().installed, false);
    assert.match(missing.status().installed_reason, /missing python/);
    assert.equal(new LegacyReforgeSupervisor({ env: {}, fsImpl: existsAll, platform: "linux" }).status().installed, false);
    const reference = new LegacyReforgeSupervisor({ env: { TEGAKI_REFORGE_RUNTIME: REFERENCE_RUNTIME_ROOT }, fsImpl: existsAll, platform: "win32" });
    assert.equal(reference.status().installed, false);
    assert.equal(reference.status().runtime_root, null, "Reference is never even recorded as the runtime");
});

test("service availability requires both an installed runtime and API readiness", () => {
    const cases = [
        { installed: true, state: "stopped", ready: false, available: false, owned: false },
        { installed: true, state: "starting", ready: false, available: false, owned: false },
        { installed: true, state: "ready", ready: true, available: true, owned: true },
        { installed: true, state: "ready", ready: true, available: true, owned: false },
        { installed: false, state: "stopped", ready: false, available: false, owned: false },
        { installed: true, state: "failed", ready: false, available: false, owned: false },
    ];
    for (const expected of cases) {
        const supervisor = {
            state: expected.state,
            status: () => ({ installed: expected.installed, state: expected.state, port: 7862, owned: expected.owned }),
        };
        const status = new LegacyReforgeService({ supervisor, client: {} }).status();
        assert.equal(status.installed, expected.installed, `installed (${expected.state})`);
        assert.equal(status.state, expected.state, `state (${expected.state})`);
        assert.equal(status.ready, expected.ready, `ready (${expected.state})`);
        assert.equal(status.available, expected.available, `available (${expected.state})`);
        assert.equal(status.owned, expected.owned, `owned (${expected.state})`);
    }
});

function fakeService({ ready = true, comfyBusy = false, txt2img, image = PNG } = {}) {
    const supervisor = { state: ready ? "ready" : "stopped", baseUrl: "http://127.0.0.1:7862", client: {},
        status() { return { backend: "easyreforge", installed: true, installed_reason: "", state: this.state, owned: ready, port: 7862 }; },
        async begin() { this.state = "starting"; }, async waitReady() { this.state = "ready"; }, async stop() { this.state = "stopped"; return this.status(); } };
    const calls = [];
    const client = {
        samplers: async () => [{ name: "Euler a" }], schedulers: async () => [{ name: "karras" }],
        catalog: async () => ({ sdModels: [{ title: "m.safetensors [1]", filename: "E:\\TEGAKI_Runtime\\EasyReforge\\Model\\Stable-diffusion\\m.safetensors" }],
            sdVae: [], loras: [], samplers: [{ name: "Euler a" }], schedulers: [{ name: "karras" }] }),
        txt2img: async payload => { calls.push(payload); return txt2img ? txt2img(payload) : { images: [image.toString("base64")], info: JSON.stringify({ seed: 9 }) }; },
        interrupt: async () => ({}),
    };
    return { service: new LegacyReforgeService({ supervisor, client, isComfyBusy: async () => comfyBusy }), calls };
}
const RECIPE = { checkpoint_id: "m.safetensors", vae_id: "", positive_raw: "1girl", negative_raw: "", sampler: "Euler a",
    scheduler: "karras", steps: 20, cfg: 7, width: 832, height: 1216, seed_requested: "9" };
const settle = () => new Promise(r => setImmediate(r));

test("service: generate -> completed PNG with backend identity; mapping errors fail before submission; busy guards", async () => {
    const { service, calls } = fakeService();
    const job = await service.generate(RECIPE);
    await settle();
    const done = service.getJob(job.job_id);
    assert.equal(done.state, "completed");
    assert.equal(done.result.backend, "easyreforge");
    assert.equal(done.result.seed, 9);
    assert.deepEqual(service.getResult(job.job_id), { bytes: PNG, mime: "image/png" });
    assert.equal(done.result.mime, "image/png");
    assert.equal(calls.length, 1);
    await assert.rejects(service.generate({ ...RECIPE, sampler: "euler_cfg_pp" }), err => err.code === "SAMPLER_UNSUPPORTED");
    assert.equal(calls.length, 1, "unsupported mapping never reaches txt2img");
    await assert.rejects(fakeService({ ready: false }).service.generate(RECIPE), err => err.code === "LEGACY_NOT_READY");
    await assert.rejects(fakeService({ comfyBusy: true }).service.generate(RECIPE), err => err.code === "COMFY_BUSY");
    const broken = fakeService({ txt2img: () => ({ images: [] }) }).service;
    const failed = await broken.generate(RECIPE);
    await settle();
    assert.equal(broken.getJob(failed.job_id).state, "failed");
    assert.equal(broken.getJob(failed.job_id).error.code, "LEGACY_RESPONSE_INVALID");
});

test("HTTP: origin-guarded routes; status never exposes config secrets; unknown route 404", async () => {
    const { service } = fakeService();
    const call = async (method, path, body, allowed = true, targetService = service) => {
        const req = Object.assign((async function* () { if (body !== undefined) yield Buffer.from(JSON.stringify(body)); })(),
            { method, headers: body !== undefined ? { "content-type": "application/json" } : {} });
        const out = { status: 0, body: null, headers: {} };
        const res = { writeHead(status, headers = {}) { out.status = status; out.headers = headers; }, end(data) { out.body = data; } };
        const handled = await handleLegacyReforgeRequest(targetService, req, res, new URL(`http://127.0.0.1:8191${path}`), { allowed });
        return { handled, status: out.status, headers: out.headers, body: out.body,
            json: typeof out.body === "string" ? JSON.parse(out.body) : out.body };
    };
    assert.equal((await call("GET", "/api/manga/legacy-reforge/status", undefined, false)).status, 403);
    const status = await call("GET", "/api/manga/legacy-reforge/status");
    assert.equal(status.json.available, true);
    assert.ok(!/civitai|api_key/i.test(JSON.stringify(status.json)));
    const caps = await call("GET", "/api/manga/legacy-reforge/capabilities");
    assert.deepEqual([caps.json.samplers, caps.json.schedulers], [["Euler a"], ["karras"]]);
    // Stabilization Issue A: only explicit equivalences whose Legacy target exists live are exposed.
    assert.deepEqual(caps.json.sampler_equivalents, { euler_ancestral: "Euler a" });
    assert.deepEqual(caps.json.scheduler_equivalents, { karras: "karras" });
    const gen = await call("POST", "/api/manga/legacy-reforge/generate", { recipe: RECIPE });
    assert.equal(gen.status, 202);
    await settle();
    const result = await call("GET", `/api/manga/legacy-reforge/jobs/${gen.json.job.job_id}/result`);
    assert.equal(result.headers["Content-Type"], "image/png");
    assert.deepEqual(result.body, PNG);

    const jpegPair = fakeService({ image: JPEG });
    const jpegGenerated = await jpegPair.service.generate(RECIPE);
    await settle();
    const jpegJob = await call("GET", `/api/manga/legacy-reforge/jobs/${jpegGenerated.job_id}`, undefined, true, jpegPair.service);
    assert.equal(jpegJob.json.job.state, "completed");
    assert.equal(jpegJob.json.job.result.mime, "image/jpeg", "result metadata belongs to the same EasyReforge job");
    assert.equal(jpegJob.json.job.result.seed, 9);
    const jpegResult = await call("GET", `/api/manga/legacy-reforge/jobs/${jpegGenerated.job_id}/result`, undefined, true, jpegPair.service);
    assert.equal(jpegResult.headers["Content-Type"], "image/jpeg");
    assert.deepEqual(jpegResult.body, JPEG);
    assert.equal((await call("GET", "/api/manga/legacy-reforge/nope")).status, 404);
    assert.equal((await call("GET", "/api/manga/other")).handled, false);
});
