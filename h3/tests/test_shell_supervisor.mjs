import test from "node:test";
import assert from "node:assert/strict";
import { EventEmitter } from "node:events";
import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";
import {
    TegakiShellSupervisor,
    formatOccupiedPort,
    readShellConfig,
    resolveH3OutputRoot,
    runSupervisorCli,
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

class FakeInput extends EventEmitter {
    constructor() {
        super();
        this.closed = false;
    }

    close() {
        this.closed = true;
        this.emit("close");
    }
}

function deferred() {
    let resolve;
    const promise = new Promise(value => { resolve = value; });
    return { promise, resolve };
}

async function flush() {
    await new Promise(resolve => setImmediate(resolve));
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

test("H3 output root defaults to the canonical namespace and rejects invalid overrides", () => {
    const defaultRoot = resolveH3OutputRoot(ROOT, {});
    assert.equal(defaultRoot.outputRoot, path.resolve(ROOT, "output", "h3"));
    assert.equal(defaultRoot.overridden, false);
    assert.throws(
        () => resolveH3OutputRoot(ROOT, { TEGAKI_H3_OUTPUT_DIR: "   " }),
        /non-empty absolute path/,
    );
    assert.throws(
        () => resolveH3OutputRoot(ROOT, { TEGAKI_H3_OUTPUT_DIR: "relative/output" }),
        /absolute path/,
    );
});

test("H3 output override is writable and reaches Native and skin argv", async () => {
    const outputRoot = await fs.mkdtemp(path.join(os.tmpdir(), "tegaki-h3-output-"));
    const calls = [];
    const children = [];
    const supervisor = new TegakiShellSupervisor({
        portableRoot: ROOT,
        env: { TEGAKI_H3_OUTPUT_DIR: outputRoot },
        spawn: (command, args, options) => {
            const child = new FakeChild(args[0] || "h3");
            calls.push({ command, args: [...args], options });
            children.push(child);
            return child;
        },
        waitFor: async () => ({
            status: 200,
            json: { queue_running: [], queue_pending: [], playable: {}, still: {}, prep: {}, state: "READY" },
        }),
        log: () => {},
        error: () => {},
    });
    supervisor.h3SafeToStop = async () => true;
    try {
        await supervisor.startH3Processes();
        assert.equal(supervisor.h3OutputRoot, path.resolve(outputRoot));
        assert.equal(calls.length, 2);
        const nativeArgs = calls[0].args;
        const nativeOutput = nativeArgs.indexOf("--output-directory");
        const nativeInput = nativeArgs.indexOf("--input-directory");
        assert.equal(nativeArgs[nativeOutput + 1], path.resolve(outputRoot));
        assert.equal(nativeArgs[nativeInput + 1], path.resolve(outputRoot));
        const skinArgs = calls[1].args;
        const skinOutput = skinArgs.indexOf("--output-dir");
        assert.equal(skinArgs[skinOutput + 1], path.resolve(outputRoot));
        assert.deepEqual(await fs.readdir(outputRoot), [], "writability probe is removed");
        assert.equal(await supervisor.shutdown(), true);
        assert.ok(children.every(child => child.killed));
    } finally {
        await fs.rm(outputRoot, { recursive: true, force: true });
    }
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

test("CLI clears STARTING after successful start and Enter reaches shutdown", async () => {
    const input = new FakeInput();
    const signals = new EventEmitter();
    let startCalls = 0;
    let shutdownCalls = 0;
    const supervisor = {
        async start() { startCalls += 1; },
        async shutdown() { shutdownCalls += 1; return true; },
    };
    const run = runSupervisorCli({ supervisor, input, signalSource: signals, log: () => {}, error: () => {} });
    await flush();
    assert.equal(startCalls, 1);
    assert.equal(shutdownCalls, 0);
    input.emit("line");
    assert.equal(await run, 0);
    assert.equal(shutdownCalls, 1);
    assert.equal(input.closed, true);
});

test("CLI invokes shutdown for Ctrl+C after READY", async () => {
    const input = new FakeInput();
    const signals = new EventEmitter();
    let shutdownCalls = 0;
    const supervisor = { async start() {}, async shutdown() { shutdownCalls += 1; return true; } };
    const run = runSupervisorCli({ supervisor, input, signalSource: signals, log: () => {}, error: () => {} });
    await flush();
    signals.emit("SIGINT");
    assert.equal(await run, 0);
    assert.equal(shutdownCalls, 1);
});

test("CLI remembers a shutdown request received during STARTING", async () => {
    const input = new FakeInput();
    const signals = new EventEmitter();
    const started = deferred();
    let shutdownCalls = 0;
    const supervisor = {
        start: () => started.promise,
        async shutdown() { shutdownCalls += 1; return true; },
    };
    const run = runSupervisorCli({ supervisor, input, signalSource: signals, log: () => {}, error: () => {} });
    await flush();
    input.emit("line");
    await flush();
    assert.equal(shutdownCalls, 0, "startup request must not race partial startup");
    started.resolve();
    assert.equal(await run, 0);
    assert.equal(shutdownCalls, 1);
});

test("CLI runs a remembered request immediately when startup becomes READY", async () => {
    const input = new FakeInput();
    const signals = new EventEmitter();
    const started = deferred();
    let shutdownStarted = false;
    let shutdownCalls = 0;
    const supervisor = {
        start: () => started.promise,
        async shutdown() { shutdownCalls += 1; shutdownStarted = true; return true; },
    };
    const run = runSupervisorCli({ supervisor, input, signalSource: signals, log: () => {}, error: () => {} });
    signals.emit("SIGINT");
    started.resolve();
    assert.equal(await run, 0);
    assert.equal(shutdownCalls, 1);
    assert.equal(shutdownStarted, true);
});

test("CLI successful shutdown closes its wait path", async () => {
    const input = new FakeInput();
    const signals = new EventEmitter();
    let release;
    const supervisor = {
        async start() {},
        shutdown: () => new Promise(resolve => { release = resolve; }),
    };
    const run = runSupervisorCli({ supervisor, input, signalSource: signals, log: () => {}, error: () => {} });
    await flush();
    input.emit("line");
    await flush();
    assert.equal(input.closed, false);
    release(true);
    assert.equal(await run, 0);
    assert.equal(input.closed, true);
});

test("CLI does not report STOPPED when shutdown is refused", async () => {
    const input = new FakeInput();
    const signals = new EventEmitter();
    let shutdownCalls = 0;
    const supervisor = {
        async start() {},
        async shutdown() { shutdownCalls += 1; return shutdownCalls > 1; },
    };
    const run = runSupervisorCli({ supervisor, input, signalSource: signals, log: () => {}, error: () => {} });
    await flush();
    input.emit("line");
    await flush();
    assert.equal(shutdownCalls, 1);
    assert.equal(input.closed, false);
    input.emit("line");
    assert.equal(await run, 0);
    assert.equal(shutdownCalls, 2);
});

test("CLI coalesces repeated shutdown requests while one stop is in flight", async () => {
    const input = new FakeInput();
    const signals = new EventEmitter();
    const stopping = deferred();
    let shutdownCalls = 0;
    const supervisor = {
        async start() {},
        shutdown: () => { shutdownCalls += 1; return stopping.promise; },
    };
    const run = runSupervisorCli({ supervisor, input, signalSource: signals, log: () => {}, error: () => {} });
    await flush();
    input.emit("line");
    signals.emit("SIGINT");
    signals.emit("SIGTERM");
    await flush();
    assert.equal(shutdownCalls, 1);
    stopping.resolve(true);
    assert.equal(await run, 0);
    assert.equal(input.closed, true);
});

test("startup failure keeps existing owned-child cleanup semantics", async () => {
    const children = [];
    const supervisor = new TegakiShellSupervisor({
        portableRoot: ROOT,
        portInspector: async port => ({ port, host: "127.0.0.1", state: "free", detail: "ECONNREFUSED" }),
        spawn: (_command, args) => {
            const child = new FakeChild(args[0] || "h3");
            children.push(child);
            return child;
        },
        waitFor: async () => { throw new Error("controlled startup failure"); },
        runtimeFactory: () => { throw new Error("Manga runtime must not start"); },
        browserLauncher: async () => {},
        log: () => {}, error: () => {},
    });
    await assert.rejects(() => supervisor.start(), /controlled startup failure/);
    assert.equal(children.length, 1);
    assert.ok(children.every(child => child.killed), "known partial children are cleaned");
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
