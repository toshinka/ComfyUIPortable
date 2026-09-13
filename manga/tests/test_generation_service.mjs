/** PLAY1b service state and HTTP routes against a fake Comfy backend only. */
import test from "node:test";
import assert from "node:assert/strict";
import http from "node:http";
import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { randomUUID } from "node:crypto";
import { GenerationService } from "../service/generation_service.mjs";
import { GenerationJournal, JournalError } from "../service/generation_journal.mjs";

const DIGEST = "a".repeat(64);
const PNG = Buffer.from([137, 80, 78, 71, 13, 10, 26, 10, 0, 0, 0, 0]);
const settings = () => ({
    mode: "txt2img", checkpoint_id: "Illustrious.safetensors", positive_raw: "draw", negative_raw: "bad",
    sampler_id: "euler", scheduler_id: "normal", steps: 20, cfg: 7,
    width: 832, height: 1216, seed_requested: "0", capability_revision: "r1"
});
const input = (key = "intent-one", digest = DIGEST) => ({
    settings: settings(), idempotency_key: key, expected_graph_digest: digest
});
const graph = () => ({
    "1": { class_type: "CheckpointLoaderSimple", inputs: { ckpt_name: "Illustrious.safetensors" } },
    "2": { class_type: "CLIPTextEncode", inputs: { text: "draw", clip: ["1", 1] } },
    "3": { class_type: "CLIPTextEncode", inputs: { text: "bad", clip: ["1", 1] } },
    "4": { class_type: "EmptyLatentImage", inputs: { width: 832, height: 1216, batch_size: 1 } },
    "5": { class_type: "KSampler", inputs: { model: ["1", 0], positive: ["2", 0], negative: ["3", 0], latent_image: ["4", 0], seed: 0, steps: 20, cfg: 7, sampler_name: "euler", scheduler: "normal", denoise: 1 } },
    "6": { class_type: "VAEDecode", inputs: { samples: ["5", 0], vae: ["1", 2] } },
    "7": { class_type: "SaveImage", inputs: { images: ["6", 0], filename_prefix: "Manga/Playable/compiled" } }
});
const json = (res, status, value) => {
    res.writeHead(status, { "Content-Type": "application/json" });
    res.end(JSON.stringify(value));
};
const close = server => new Promise(resolve => server.close(resolve));

class FakeBackend {
    constructor() {
        this.mode = "normal";
        this.queueMode = "normal";
        this.queuePending = [];
        this.queueRunning = [];
        this.history = new Map();
        this.promptCalls = 0;
        this.requests = [];
        this.lastPayload = null;
        this.lastSubmittedPayload = null;
        this.releasePrompt = null;
        this.imageBytes = PNG;
        this.server = http.createServer((req, res) => this.handle(req, res));
    }
    async start() {
        await new Promise(resolve => this.server.listen(0, "127.0.0.1", resolve));
        this.origin = `http://127.0.0.1:${this.server.address().port}`;
        return this;
    }
    async handle(req, res) {
        const target = new URL(req.url, "http://127.0.0.1");
        this.requests.push([req.method, target.pathname]);
        if (target.pathname === "/object_info/TegakiMinimumHandSceneEditor") {
            json(res, 200, { TegakiMinimumHandSceneEditor: { input: {} } });
        } else if (target.pathname === "/queue") {
            if (this.queueMode === "unavailable") json(res, 503, { error: "offline" });
            else if (this.queueMode === "malformed") json(res, 200, { queue_running: "idle", queue_pending: [] });
            else json(res, 200, { queue_running: this.queueRunning, queue_pending: this.queuePending });
        } else if (target.pathname === "/tegaki/manga/generation/capabilities") {
            json(res, 200, { ok: true, revision: "r1" });
        } else if (target.pathname === "/tegaki/manga/generation/compile-basic") {
            let body = "";
            for await (const chunk of req) body += chunk;
            const request = JSON.parse(body);
            const compiled = graph();
            compiled["5"].inputs.seed = Number(request.seed_requested);
            json(res, 200, {
                ok: true, normalized_request: request, graph: compiled, graph_digest: DIGEST,
                capability_revision: "r1", effective_seed: Number(request.seed_requested),
                positive_clean: request.positive_raw, negative_clean: request.negative_raw,
                resolved_loras: []
            });
        } else if (target.pathname === "/prompt") {
            this.promptCalls++;
            let body = "";
            for await (const chunk of req) body += chunk;
            const payload = JSON.parse(body);
            this.lastSubmittedPayload = payload;
            this.lastPayload = { ...payload, prompt_id: randomUUID() };
            if (this.mode === "reject") {
                json(res, 400, { error: { message: "Invalid backend graph" }, node_errors: {} });
                return;
            }
            if (!["timeout_lost", "malformed_accept"].includes(this.mode)) this.queuePending = [this.queueItem()];
            if (this.mode === "http408_duplicate") {
                const duplicate = this.queueItem();
                duplicate[1] = randomUUID();
                this.queuePending.push(duplicate);
            }
            const accepted = () => json(res, 200, {
                prompt_id: this.mode === "malformed_accept" ? "invalid" : this.lastPayload.prompt_id,
                number: 1, node_errors: {}
            });
            if (this.mode === "hold_accept") {
                this.releasePrompt = accepted;
                return;
            }
            if (["http408_accept", "http408_duplicate"].includes(this.mode)) {
                json(res, 408, { error: "backend timed out after acceptance" });
                return;
            }
            if (this.mode.startsWith("timeout")) {
                setTimeout(() => {
                    if (!res.writableEnded) accepted();
                }, 300);
            } else {
                accepted();
            }
        } else if (target.pathname === "/history") {
            json(res, 200, Object.fromEntries(this.history));
        } else if (target.pathname.startsWith("/history/")) {
            const promptId = target.pathname.slice("/history/".length);
            json(res, 200, this.history.has(promptId) ? { [promptId]: this.history.get(promptId) } : {});
        } else if (target.pathname === "/view") {
            res.writeHead(200, { "Content-Type": "image/png" });
            res.end(this.imageBytes);
        } else {
            json(res, 404, { error: "unknown route" });
        }
    }
    queueItem(payload = this.lastPayload) {
        return [0, payload.prompt_id, payload.prompt, payload.extra_data, ["7"]];
    }
    complete(locator, status = "success", payload = this.lastPayload) {
        this.queuePending = [];
        this.queueRunning = [];
        this.history.set(payload.prompt_id, {
            prompt: this.queueItem(payload),
            status: { status_str: status, completed: status === "success", messages: [] },
            outputs: { "7": { images: [locator || {
                filename: `${payload.extra_data.tegaki_manga.job_id}_00001_.png`, subfolder: "Manga\\Playable", type: "output"
            }] } }
        });
    }
}

async function fixture(t, timeoutMs = 1000) {
    const directory = await fs.mkdtemp(path.join(os.tmpdir(), "manga-play1b-"));
    const backend = await new FakeBackend().start();
    const journal = new GenerationJournal(directory);
    const service = new GenerationService({ backendUrl: backend.origin, journal, timeoutMs });
    t.after(async () => {
        await close(backend.server);
        if (!directory.startsWith(path.resolve(os.tmpdir()) + path.sep)) throw new Error("Unexpected test cleanup path");
        await fs.rm(directory, { recursive: true, force: true });
    });
    return { backend, journal, service, directory };
}

async function rejectsCode(operation, code) {
    await assert.rejects(operation, error => error.code === code, code);
}

async function waitFor(predicate) {
    for (let attempt = 0; attempt < 100; attempt++) {
        if (predicate()) return;
        await new Promise(resolve => setTimeout(resolve, 10));
    }
    throw new Error("Timed out waiting for fake backend request");
}

test("job exists with null prompt ID before backend accepts", async t => {
    const { backend, journal, service } = await fixture(t, 5000);
    backend.mode = "hold_accept";
    const pending = service.createJob(input());
    await waitFor(() => backend.releasePrompt !== null);
    const [beforeAcceptance] = await journal.list();
    assert.match(beforeAcceptance.job_id, /^[0-9a-f-]{36}$/);
    assert.equal(beforeAcceptance.state, "SUBMITTING");
    assert.equal(beforeAcceptance.prompt_id, null);
    assert.equal(Object.hasOwn(backend.lastSubmittedPayload, "prompt_id"), false);
    backend.releasePrompt();
    const accepted = await pending;
    assert.equal(accepted.prompt_id, backend.lastPayload.prompt_id);
    assert.notEqual(accepted.job_id, accepted.prompt_id);
});

test("accepted submit follows QUEUED, RUNNING, completed history, verified PNG", async t => {
    const { backend, journal, service } = await fixture(t);
    const queued = await service.createJob(input());
    assert.equal(queued.state, "QUEUED", JSON.stringify(queued.error));
    assert.notEqual(queued.prompt_id, queued.job_id);
    assert.equal(queued.prompt_id, backend.lastPayload.prompt_id);
    assert.equal(Object.hasOwn(backend.lastSubmittedPayload, "prompt_id"), false);
    assert.equal((await journal.get(queued.job_id)).prompt_id, backend.lastPayload.prompt_id);
    assert.equal(backend.promptCalls, 1);
    assert.equal(backend.lastPayload.prompt["7"].inputs.filename_prefix, `Manga/Playable/${queued.job_id}`);
    assert.equal(backend.lastPayload.extra_data.tegaki_manga.request_id, queued.request_id);
    assert.equal(Object.hasOwn(queued, "ownership_token"), false);
    backend.queueRunning = backend.queuePending;
    backend.queuePending = [];
    const running = await service.getJob(queued.job_id);
    assert.equal(running.state, "RUNNING");
    assert.ok(backend.requests.some(([method, route]) => method === "GET" && route === `/history/${queued.prompt_id}`));
    assert.ok(!backend.requests.some(([method, route]) => method === "GET" && route === `/history/${queued.job_id}`));
    backend.complete();
    const completed = await service.getJob(queued.job_id);
    assert.equal(completed.state, "SUCCEEDED");
    assert.deepEqual(completed.output_locator, {
        filename: `${queued.job_id}_00001_.png`, subfolder: "Manga/Playable", type: "output"
    });
    assert.deepEqual(await service.getResult(queued.job_id), PNG);
    assert.equal((await journal.get(queued.job_id)).state, "SUCCEEDED");
    assert.equal(backend.promptCalls, 1);
});

test("backend validation rejection is FAILED, without output", async t => {
    const { backend, service } = await fixture(t);
    backend.mode = "reject";
    const failed = await service.createJob(input());
    assert.equal(failed.state, "FAILED");
    assert.equal(failed.error.code, "BACKEND_REJECTED");
    assert.equal(failed.prompt_id, null);
    await rejectsCode(() => service.getResult(failed.job_id), "RESULT_NOT_READY");
    assert.equal(backend.promptCalls, 1);
});

test("completed backend execution error is FAILED without a fake image", async t => {
    const { backend, service } = await fixture(t);
    const queued = await service.createJob(input());
    backend.complete(undefined, "error");
    const failed = await service.getJob(queued.job_id);
    assert.equal(failed.state, "FAILED");
    assert.equal(failed.error.code, "BACKEND_EXECUTION_FAILED");
    await rejectsCode(() => service.getResult(queued.job_id), "RESULT_NOT_READY");
});
test("timeout after acceptance reconciles owned queue without a second POST", async t => {
    const { backend, service } = await fixture(t, 100);
    backend.mode = "timeout_accept";
    const queued = await service.createJob(input());
    assert.equal(queued.state, "QUEUED", JSON.stringify(queued.error));
    assert.equal(queued.prompt_id, backend.lastPayload.prompt_id);
    assert.notEqual(queued.prompt_id, queued.job_id);
    assert.equal(backend.promptCalls, 1);
    assert.equal((await service.getJob(queued.job_id)).state, "QUEUED");
    assert.equal(backend.promptCalls, 1);
});

test("HTTP 408 after possible acceptance reconciles instead of failing", async t => {
    const { backend, service } = await fixture(t);
    backend.mode = "http408_accept";
    const queued = await service.createJob(input());
    assert.equal(queued.state, "QUEUED", JSON.stringify(queued.error));
    assert.equal(backend.promptCalls, 1);
});
test("ambiguous submit with two matching backend IDs stays UNKNOWN and does not retry", async t => {
    const { backend, service } = await fixture(t);
    backend.mode = "http408_duplicate";
    const unknown = await service.createJob(input());
    assert.equal(unknown.state, "UNKNOWN");
    assert.equal(unknown.prompt_id, null);
    assert.equal(backend.promptCalls, 1);
});

test("malformed accepted response without backend evidence cannot invent a prompt ID", async t => {
    const { backend, service } = await fixture(t);
    backend.mode = "malformed_accept";
    const unknown = await service.createJob(input());
    assert.equal(unknown.state, "UNKNOWN");
    assert.equal(unknown.prompt_id, null);
    assert.equal(backend.promptCalls, 1);
});

test("unresolved timeout becomes UNKNOWN; late owned result can recover", async t => {
    const { backend, service } = await fixture(t, 100);
    backend.mode = "timeout_lost";
    const unknown = await service.createJob(input());
    assert.equal(unknown.state, "UNKNOWN");
    assert.equal(unknown.prompt_id, null);
    assert.equal(backend.promptCalls, 1);
    await rejectsCode(() => service.createJob(input()), "DUPLICATE_REQUEST");
    assert.equal(backend.promptCalls, 1);
    backend.complete();
    const recovered = await service.getJob(unknown.job_id);
    assert.equal(recovered.state, "SUCCEEDED");
    assert.equal(recovered.prompt_id, backend.lastPayload.prompt_id);
    assert.notEqual(recovered.prompt_id, recovered.job_id);
    assert.equal(backend.promptCalls, 1);
});

test("random seed is locked to the reviewed effective value", async t => {
    const { backend, service } = await fixture(t);
    const request = input();
    request.settings.seed_requested = "-1";
    await rejectsCode(() => service.createJob(request), "EFFECTIVE_SEED_REQUIRED");
    assert.equal(backend.promptCalls, 0);
    const queued = await service.createJob({ ...request, effective_seed: "42" });
    assert.equal(queued.requested_settings.seed_requested, "-1");
    assert.equal(queued.effective_settings.seed_requested, "42");
    assert.equal(backend.lastPayload.prompt["5"].inputs.seed, 42);
    assert.equal(backend.promptCalls, 1);
});

test("stale capability and reviewed digest mismatch stop before submit", async t => {
    const { backend, service, journal } = await fixture(t);
    const stale = input();
    stale.settings.capability_revision = "old";
    await rejectsCode(() => service.createJob(stale), "CAPABILITY_CHANGED");
    await rejectsCode(() => service.createJob(input("other", "b".repeat(64))), "DIGEST_MISMATCH");
    assert.equal(backend.promptCalls, 0);
    assert.equal((await journal.list()).length, 0);
});
test("duplicate key/digest and a second outstanding owned job are refused", async t => {
    const { backend, service } = await fixture(t);
    await service.createJob(input());
    await rejectsCode(() => service.createJob(input()), "DUPLICATE_REQUEST");
    await rejectsCode(() => service.createJob(input("intent-two")), "DUPLICATE_GRAPH");
    await rejectsCode(() => service.createJob(input("intent-three", "b".repeat(64))), "OWNED_JOB_BUSY");
    assert.equal(backend.promptCalls, 1);
});

test("foreign queue and unreadable queue refuse submit without journal mutation", async t => {
    const { backend, service, journal } = await fixture(t);
    backend.queuePending = [[0, "foreign-job", {}, {}, []]];
    await rejectsCode(() => service.createJob(input()), "FOREIGN_QUEUE_BUSY");
    backend.queuePending = [];
    backend.queueRunning = [[0, "foreign-running", {}, {}, []]];
    await rejectsCode(() => service.createJob(input()), "FOREIGN_QUEUE_BUSY");
    backend.queueRunning = [];
    backend.queueMode = "unavailable";
    await rejectsCode(() => service.createJob(input()), "QUEUE_UNKNOWN");
    backend.queueMode = "malformed";
    await rejectsCode(() => service.createJob(input()), "QUEUE_UNKNOWN");
    assert.equal(backend.promptCalls, 0);
    assert.equal((await journal.list()).length, 0);
});

test("lost backend state remains UNKNOWN after service restart; late correct history wins", async t => {
    const { backend, journal, service } = await fixture(t);
    const queued = await service.createJob(input());
    backend.queuePending = [];
    assert.equal((await service.getJob(queued.job_id)).state, "UNKNOWN");
    const restarted = new GenerationService({ backendUrl: backend.origin, journal });
    assert.equal((await restarted.getJob(queued.job_id)).state, "UNKNOWN");
    const wrong = structuredClone(backend.lastPayload);
    wrong.extra_data.tegaki_manga.ownership_token = "0".repeat(64);
    backend.complete(undefined, "success", wrong);
    assert.equal((await restarted.getJob(queued.job_id)).state, "UNKNOWN");
    backend.complete();
    assert.equal((await restarted.getJob(queued.job_id)).state, "SUCCEEDED");
    assert.equal(backend.promptCalls, 1);
});

test("malicious locators never become successful history", async t => {
    const { backend, service } = await fixture(t);
    const queued = await service.createJob(input());
    const jobId = queued.job_id;
    const safe = { filename: `${jobId}_00001_.png`, subfolder: "Manga/Playable", type: "output" };
    for (const locator of [
        { ...safe, filename: "../evil.png" },
        { ...safe, filename: "C:\\evil.png" },
        { ...safe, subfolder: "Other/Playable" },
        { ...safe, type: "temp" },
    ]) {
        backend.complete(locator);
        const observed = await service.getJob(jobId);
        assert.equal(observed.state, "UNKNOWN");
        assert.equal(observed.output_locator, null);
    }
    backend.complete(safe);
    assert.equal((await service.getJob(jobId)).state, "SUCCEEDED");
});

test("missing or invalid PNG cannot certify successful history", async t => {
    const { backend, service } = await fixture(t);
    const queued = await service.createJob(input());
    backend.complete();
    backend.imageBytes = Buffer.from("not a PNG");
    const unknown = await service.getJob(queued.job_id);
    assert.equal(unknown.state, "UNKNOWN");
    assert.equal(unknown.output_locator, null);
    backend.imageBytes = PNG;
    assert.equal((await service.getJob(queued.job_id)).state, "SUCCEEDED");
});
test("journal allows distinct backend ID and rejects malformed present prompt ID", async t => {
    const { journal, service } = await fixture(t);
    const queued = await service.createJob(input());
    const record = await journal.get(queued.job_id);
    assert.notEqual(record.job_id, record.prompt_id);
    await rejectsCode(() => journal.put({ ...record, prompt_id: "not-a-uuid" }), "JOURNAL_CORRUPT");
    await rejectsCode(() => journal.put({ ...record, prompt_id: null }), "JOURNAL_CORRUPT");
    assert.equal((await journal.get(queued.job_id)).prompt_id, queued.prompt_id);
});

test("corrupt and partial journal block recovery and new submits", async t => {
    const { backend, service, journal, directory } = await fixture(t);
    const queued = await service.createJob(input());
    const file = path.join(directory, `${queued.job_id}.json`);
    await fs.writeFile(file, '{"state":"SUCCEEDED"}', "utf8");
    await assert.rejects(() => journal.get(queued.job_id), error => error instanceof JournalError && error.code === "JOURNAL_CORRUPT");
    await rejectsCode(() => service.createJob(input("another")), "JOURNAL_CORRUPT");
    assert.equal(backend.promptCalls, 1);
    await fs.writeFile(path.join(directory, `${queued.job_id}.partial.tmp`), "partial", "utf8");
    await rejectsCode(() => service.createJob(input("third")), "JOURNAL_CORRUPT");
});

test("workspace job routes bind to same-origin service; generic /prompt stays forbidden", async t => {
    const { backend, directory } = await fixture(t);
    const previousBackend = process.env.MANGA_BACKEND_URL;
    const previousPort = process.env.MANGA_WORKSPACE_PORT;
    const previousJournal = process.env.MANGA_GENERATION_JOURNAL_DIR;
    process.env.MANGA_BACKEND_URL = backend.origin;
    process.env.MANGA_WORKSPACE_PORT = "0";
    process.env.MANGA_GENERATION_JOURNAL_DIR = directory;
    const { server: workspace } = await import(`../service/manga_workspace_server.mjs?play1b=${Date.now()}`);
    if (!workspace.listening) await new Promise(resolve => workspace.once("listening", resolve));
    t.after(async () => {
        await close(workspace);
        if (previousBackend === undefined) delete process.env.MANGA_BACKEND_URL;
        else process.env.MANGA_BACKEND_URL = previousBackend;
        if (previousPort === undefined) delete process.env.MANGA_WORKSPACE_PORT;
        else process.env.MANGA_WORKSPACE_PORT = previousPort;
        if (previousJournal === undefined) delete process.env.MANGA_GENERATION_JOURNAL_DIR;
        else process.env.MANGA_GENERATION_JOURNAL_DIR = previousJournal;
    });
    const origin = `http://127.0.0.1:${workspace.address().port}`;
    const blocked = await fetch(`${origin}/api/proxy?path=/prompt`);
    assert.equal(blocked.status, 403);
    const foreign = await fetch(`${origin}/api/manga/generation/jobs`, {
        method: "POST", headers: { Origin: "http://foreign.invalid", "Content-Type": "application/json" },
        body: JSON.stringify(input())
    });
    assert.equal(foreign.status, 403);
    const arbitraryGraph = await fetch(`${origin}/api/manga/generation/jobs`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...input(), graph: graph() })
    });
    assert.equal(arbitraryGraph.status, 400);
    const submit = await fetch(`${origin}/api/manga/generation/jobs`, {
        method: "POST", headers: { "Content-Type": "application/json", Origin: origin },
        body: JSON.stringify(input())
    });
    assert.equal(submit.status, 202);
    const created = (await submit.json()).job;
    assert.equal(created.state, "QUEUED");
    backend.complete();
    const poll = await fetch(`${origin}/api/manga/generation/jobs/${created.job_id}`);
    assert.equal((await poll.json()).job.state, "SUCCEEDED");
    const image = await fetch(`${origin}/api/manga/generation/jobs/${created.job_id}/result`);
    assert.equal(image.status, 200);
    assert.deepEqual(Buffer.from(await image.arrayBuffer()), PNG);
    assert.equal(backend.promptCalls, 1);
});
