/** PLAY1a fixed-route workspace boundary against a fake backend; zero generation. */
import test from "node:test";
import assert from "node:assert/strict";
import http from "node:http";

const listen = server => new Promise(resolve => server.listen(0, "127.0.0.1", resolve));
const close = server => new Promise(resolve => server.close(resolve));
const json = (res, status, value) => {
    res.writeHead(status, { "Content-Type": "application/json" });
    res.end(JSON.stringify(value));
};

test("PLAY1a routes are fixed, bounded, and never submit", async () => {
    const seen = [];
    let behavior = "ok";
    const backend = http.createServer((req, res) => {
        seen.push([req.method, req.url]);
        if (behavior === "invalid") {
            res.writeHead(200, { "Content-Type": "application/json" });
            res.end("not json");
            return;
        }
        if (behavior === "timeout") {
            setTimeout(() => json(res, 200, { ok: true, revision: "r1", checkpoints: [], samplers: [] }), 6000);
            return;
        }
        if (behavior === "reject") {
            json(res, 422, { ok: false, error_code: "LORA_UNAVAILABLE", error: "missing LoRA" });
            return;
        }
        if (req.url === "/tegaki/manga/generation/capabilities") {
            json(res, 200, { ok: true, revision: "r1", checkpoints: [], samplers: ["euler"] });
        } else if (req.url === "/tegaki/manga/generation/compile-basic") {
            json(res, 200, { ok: true, graph: { "1": { class_type: "CheckpointLoaderSimple", inputs: {} } }, graph_digest: "hash" });
        } else {
            json(res, 404, { ok: false, error: "unknown backend path" });
        }
    });
    await listen(backend);
    const oldBackend = process.env.MANGA_BACKEND_URL;
    const oldPort = process.env.MANGA_WORKSPACE_PORT;
    process.env.MANGA_BACKEND_URL = `http://127.0.0.1:${backend.address().port}`;
    process.env.MANGA_WORKSPACE_PORT = "0";
    const { server: workspace } = await import(`../service/manga_workspace_server.mjs?play1a=${Date.now()}`);
    if (!workspace.listening) await new Promise(resolve => workspace.once("listening", resolve));
    const origin = `http://127.0.0.1:${workspace.address().port}`;
    try {
        const capabilities = await fetch(`${origin}/api/manga/generation/capabilities`);
        assert.equal(capabilities.status, 200);
        assert.equal((await capabilities.json()).revision, "r1");
        const compile = await fetch(`${origin}/api/manga/generation/compile`, {
            method: "POST", headers: { "Content-Type": "application/json", Origin: origin },
            body: JSON.stringify({ request_id: "r1" })
        });
        assert.equal(compile.status, 200);
        assert.equal((await compile.json()).graph_digest, "hash");
        assert.deepEqual(seen, [
            ["GET", "/tegaki/manga/generation/capabilities"],
            ["POST", "/tegaki/manga/generation/compile-basic"]
        ]);
        for (const [path, options, status] of [
            ["/api/manga/generation/capabilities", { method: "POST" }, 405],
            ["/api/manga/generation/compile", { method: "GET" }, 405],
            ["/api/manga/generation/capabilities", { headers: { Origin: "http://evil.example" } }, 403],
            ["/api/manga/generation/compile", { method: "POST", headers: { Origin: "http://evil.example", "Content-Type": "application/json" }, body: "{}" }, 403],
            ["/api/manga/generation/compile", { method: "POST", headers: { "Content-Type": "text/plain" }, body: "{}" }, 415],
            ["/api/manga/generation/compile", { method: "POST", headers: { "Content-Type": "application/json" }, body: "bad" }, 400],
            ["/api/manga/generation/compile", { method: "POST", headers: { "Content-Type": "application/json" }, body: Buffer.alloc(256 * 1024 + 1) }, 413],
        ]) {
            const response = await fetch(origin + path, options);
            assert.equal(response.status, status, path);
            assert.equal((await response.json()).ok, false);
        }
        assert.equal(seen.length, 2, "Rejected client requests never reach backend");
        behavior = "reject";
        const rejected = await fetch(`${origin}/api/manga/generation/compile`, {
            method: "POST", headers: { "Content-Type": "application/json" }, body: "{}"
        });
        assert.equal(rejected.status, 422);
        assert.equal((await rejected.json()).error_code, "LORA_UNAVAILABLE");
        behavior = "invalid";
        const invalid = await fetch(`${origin}/api/manga/generation/capabilities`);
        assert.equal(invalid.status, 502);
        assert.equal((await invalid.json()).error_code, "BACKEND_INVALID_RESPONSE");
        behavior = "timeout";
        const timeout = await fetch(`${origin}/api/manga/generation/capabilities`);
        assert.equal(timeout.status, 502);
        assert.equal((await timeout.json()).error_code, "BACKEND_TIMEOUT");
        assert.equal(seen.filter(([, path]) => path === "/prompt" || path === "/queue").length, 0);
    } finally {
        await close(workspace);
        await close(backend);
        if (oldBackend === undefined) delete process.env.MANGA_BACKEND_URL;
        else process.env.MANGA_BACKEND_URL = oldBackend;
        if (oldPort === undefined) delete process.env.MANGA_WORKSPACE_PORT;
        else process.env.MANGA_WORKSPACE_PORT = oldPort;
    }
});
