import test from "node:test";
import assert from "node:assert/strict";
import { EventEmitter } from "node:events";
import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import {
    TegakiShellSupervisor,
    formatOccupiedPort,
    readShellConfig,
} from "../tools/tegaki_shell_supervisor.mjs";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..", "..");

class FakeChild extends EventEmitter {
    static nextPid = 41000;
    constructor(label) {
        super();
        this.label = label;
        this.pid = FakeChild.nextPid++;
        this.killed = false;
        this.exitCode = null;
        this.signalCode = null;
        this.stdout = new EventEmitter();
        this.stderr = new EventEmitter();
    }
    kill(signal) {
        this.killed = true;
        this.signalCode = signal;
        setImmediate(() => {
            this.exitCode = 0;
            this.emit("exit", 0, signal);
        });
        return true;
    }
}

test("shell config keeps Manga endpoint and documented port overrides explicit", () => {
    const config = readShellConfig({
        TEGAKI_H3_NATIVE_PORT: "8288",
        TEGAKI_H3_SKIN_PORT: "8290",
        TEGAKI_MANGA_BACKEND_PORT: "8289",
        TEGAKI_MANGA_WORKSPACE_PORT: "8291",
    });
    assert.equal(config.h3BackendPort, 8288);
    assert.equal(config.h3SkinPort, 8290);
    assert.equal(config.mangaBackendPort, 8289);
    assert.equal(config.mangaWorkspacePort, 8291);
    assert.match(formatOccupiedPort({ port: 8190, host: "127.0.0.1", detail: "listener" }), /8190/);
    assert.match(formatOccupiedPort({ port: 8190, host: "127.0.0.1", detail: "listener" }), /PID/);
});

test("occupied H3 port fails closed before any process or Manga runtime starts", async () => {
    let spawnCalls = 0;
    let runtimeCalls = 0;
    const supervisor = new TegakiShellSupervisor({
        portableRoot: ROOT,
        portInspector: async port => port === 8188
            ? { port, host: "127.0.0.1", state: "occupied", detail: "test listener" }
            : { port, host: "127.0.0.1", state: "free", detail: "ECONNREFUSED" },
        spawn: () => { spawnCalls += 1; return new FakeChild("unexpected"); },
        runtimeFactory: () => { runtimeCalls += 1; throw new Error("runtime must not start"); },
        log: () => {}, error: () => {},
    });
    await assert.rejects(() => supervisor.start(), /8188.*occupied.*PID/);
    assert.equal(spawnCalls, 0);
    assert.equal(runtimeCalls, 0);
});

test("Owner shutdown stops owned H3 children and delegates Manga stopAll", async () => {
    const children = [];
    const logs = [];
    let runtimeConfig;
    let stopAllCalls = 0;
    const fakeRuntime = {
        backendOwnership: "OWNED_BY_THIS_RUNTIME",
        workspaceOwnership: "OWNED_BY_THIS_RUNTIME",
        async start() {
            runtimeConfig.customSpawnBackend({ command: "manga-backend", args: [], cwd: ROOT });
            runtimeConfig.customSpawnWorkspace({ command: process.execPath, args: [], cwd: ROOT, env: {} });
            return "READY";
        },
        async probeWorkspace() { return { classification: "PREEXISTING_COMPATIBLE", details: "test" }; },
        async stopAll() { stopAllCalls += 1; },
    };
    const supervisor = new TegakiShellSupervisor({
        portableRoot: ROOT,
        portInspector: async port => ({ port, host: "127.0.0.1", state: "free", detail: "ECONNREFUSED" }),
        spawn: (_command, args) => {
            const child = new FakeChild(args[0] || "h3");
            children.push(child);
            return child;
        },
        waitFor: async () => ({ status: 200, json: { queue_running: [], queue_pending: [], playable: {}, still: {}, prep: {} } }),
        runtimeFactory: config => { runtimeConfig = config; return fakeRuntime; },
        browserLauncher: async () => {},
        log: message => logs.push(message), error: () => {},
    });
    supervisor.h3SafeToStop = async () => true;
    await supervisor.start();
    assert.equal(supervisor.started, true);
    assert.equal(children.length, 4, "H3 backend, H3 skin, and two Manga children are tracked");
    const stopped = await supervisor.shutdown();
    assert.equal(stopped, true);
    assert.equal(stopAllCalls, 1, "Manga lifecycle owns its own stop decision");
    assert.ok(children.every(child => child.killed), "every child launched by this session received SIGTERM");
    assert.ok(logs.some(line => /OWNED_BY_THIS_RUNTIME \(PID 410\d+\)/.test(line)),
        "startup diagnostics identify owner-session PIDs");
});

test("H3 shell statically exposes top-level MANGA navigation and config-driven iframe", async () => {
    const [html, app, server, styles] = await Promise.all([
        fs.readFile(path.join(ROOT, "h3", "app", "static", "index.html"), "utf8"),
        fs.readFile(path.join(ROOT, "h3", "app", "static", "app.js"), "utf8"),
        fs.readFile(path.join(ROOT, "h3", "app", "server.py"), "utf8"),
        fs.readFile(path.join(ROOT, "h3", "app", "static", "styles.css"), "utf8"),
    ]);
    assert.match(html, /id="product-h3"/);
    assert.match(html, /id="product-manga"/);
    assert.match(html, /id="manga-workspace-frame"/);
    assert.match(app, /manga_workspace_url/);
    assert.match(app, /setProduct\("manga"\)/);
    assert.match(app, /searchParams\.set\("embedded", "1"\)/);
    assert.match(server, /--manga-workspace-url/);
    assert.match(server, /"manga_workspace_url"/);
    assert.match(styles, /body\[data-product="manga"\] \.mode-switch/);
    assert.match(styles, /body\[data-product="manga"\] \.backend-pill/);
});
