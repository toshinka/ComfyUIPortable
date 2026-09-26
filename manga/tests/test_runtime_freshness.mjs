// MANGA-PROMPT-VALIDATION-COHERENCE1: a reused (PREEXISTING_COMPATIBLE) process must not make
// old server source look current.  Static app files are read from disk per request, so the old
// file-equality check passed even when the running workspace/backend held stale route code.
import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs/promises";
import http from "node:http";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { sourceFolderDigest, verifyWorkspaceSource, WORKSPACE_SOURCE_DIR } from "../service/run_manga.mjs";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const APP = path.resolve(HERE, "..", "app");

async function fakeServices({ workspaceIdentity, backendIdentity }) {
    const workspace = http.createServer(async (req, res) => {
        if (req.url === "/api/runtime/identity") {
            res.writeHead(200, { "Content-Type": "application/json" });
            res.end(JSON.stringify(workspaceIdentity));
            return;
        }
        try {
            const body = await fs.readFile(path.join(APP, decodeURIComponent(req.url.split("?")[0])));
            res.writeHead(200);
            res.end(body);
        } catch { res.writeHead(404); res.end(); }
    });
    const backend = http.createServer((req, res) => {
        if (req.url === "/tegaki/manga/runtime/source-identity" && backendIdentity) {
            res.writeHead(200, { "Content-Type": "application/json" });
            res.end(JSON.stringify(backendIdentity));
            return;
        }
        res.writeHead(404, { "Content-Type": "text/plain" });
        res.end("404: Not Found");
    });
    await Promise.all([workspace, backend].map(s => new Promise(r => s.listen(0, "127.0.0.1", r))));
    return {
        runtime: { workspaceUrl: `http://127.0.0.1:${workspace.address().port}`, backendUrl: `http://127.0.0.1:${backend.address().port}` },
        close: () => Promise.all([workspace, backend].map(s => new Promise(r => s.close(r)))),
    };
}

async function backendDir() {
    const dir = await fs.mkdtemp(path.join(os.tmpdir(), "tegaki-nodes-"));
    await fs.writeFile(path.join(dir, "engine_resources.py"), "LOADED = 1\n");
    await fs.writeFile(path.join(dir, "notes.txt"), "ignored\n");
    return dir;
}

test("current workspace + backend source is accepted (and PIDs are reported)", async () => {
    const dir = await backendDir();
    const ws = await sourceFolderDigest(WORKSPACE_SOURCE_DIR, ".mjs");
    const be = await sourceFolderDigest(dir, ".py");
    const svc = await fakeServices({ workspaceIdentity: { source_digest: ws, pid: 111 }, backendIdentity: { source_digest: be, pid: 222 } });
    try {
        const fresh = await verifyWorkspaceSource(svc.runtime, { backendDir: dir });
        assert.deepEqual([fresh.workspacePid, fresh.backendPid], [111, 222]);
    } finally { await svc.close(); }
});

test("a reused workspace process with older server source is refused with its PID", async () => {
    const dir = await backendDir();
    const be = await sourceFolderDigest(dir, ".py");
    for (const identity of [{ source_digest: "0".repeat(64), pid: 4242 }, { pid: 4242 }]) {
        const svc = await fakeServices({ workspaceIdentity: identity, backendIdentity: { source_digest: be, pid: 1 } });
        try {
            await assert.rejects(verifyWorkspaceSource(svc.runtime, { backendDir: dir }),
                /STALE WORKSPACE SERVER: .*taskkill \/PID 4242 \/F/);
        } finally { await svc.close(); }
    }
});

test("a reused backend with older (or pre-reporting) tegaki_manga_nodes source is refused", async () => {
    const dir = await backendDir();
    const ws = await sourceFolderDigest(WORKSPACE_SOURCE_DIR, ".mjs");
    const stale = await fakeServices({ workspaceIdentity: { source_digest: ws, pid: 1 }, backendIdentity: { source_digest: "f".repeat(64), pid: 777 } });
    try {
        await assert.rejects(verifyWorkspaceSource(stale.runtime, { backendDir: dir }), /STALE BACKEND: .*taskkill \/PID 777 \/F/);
    } finally { await stale.close(); }
    const old = await fakeServices({ workspaceIdentity: { source_digest: ws, pid: 1 }, backendIdentity: null });
    try {
        await assert.rejects(verifyWorkspaceSource(old.runtime, { backendDir: dir }), /STALE BACKEND: .*predates source reporting/);
    } finally { await old.close(); }
    // editing a backend file on disk makes the running (loaded) digest stale
    const before = await sourceFolderDigest(dir, ".py");
    await fs.writeFile(path.join(dir, "engine_resources.py"), "LOADED = 2\n");
    assert.notEqual(await sourceFolderDigest(dir, ".py"), before);
});

test("the real workspace server reports the digest of the source it loaded (same formula)", async () => {
    const oldPort = process.env.MANGA_WORKSPACE_PORT;
    process.env.MANGA_WORKSPACE_PORT = "0";
    const { server } = await import(`../service/manga_workspace_server.mjs?fresh=${Date.now()}`);
    if (!server.listening) await new Promise(resolve => server.once("listening", resolve));
    try {
        const identity = await (await fetch(`http://127.0.0.1:${server.address().port}/api/runtime/identity`)).json();
        assert.equal(identity.source_digest, await sourceFolderDigest(WORKSPACE_SOURCE_DIR, ".mjs"));
        assert.equal(identity.pid, process.pid);
        assert.equal(identity.service, "tegaki_manga_workspace");
    } finally {
        await new Promise(resolve => server.close(resolve));
        if (oldPort === undefined) delete process.env.MANGA_WORKSPACE_PORT;
        else process.env.MANGA_WORKSPACE_PORT = oldPort;
    }
});
