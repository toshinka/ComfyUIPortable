// Card TEGAKI-MULTI-ENGINE-LAUNCHER-AND-AVAILABILITY-SYNC-1: run_tegaki.bat top-level orchestration.
// Fakes only: no process is spawned, no port is opened, no GPU, no generation.
import test from "node:test";
import assert from "node:assert/strict";
import { EventEmitter } from "node:events";
import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { TegakiShellSupervisor, WITH_EASYREFORGE_FLAG, readShellConfig } from "../tools/tegaki_shell_supervisor.mjs";
import { INTEGRATION_RUNTIME_ROOT, LegacyReforgeSupervisor, runtimeLayout } from "../../manga/service/legacy_reforge_supervisor.mjs";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..", "..");
const INTEGRATION_PYTHON = runtimeLayout(INTEGRATION_RUNTIME_ROOT).python;
const existsAll = { existsSync: () => true, realpathSync: p => p };

class FakeChild extends EventEmitter {
    static nextPid = 52000;
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
        setImmediate(() => { this.exitCode = 0; this.emit("exit", 0, signal); });
        return true;
    }
}

/** A real LegacyReforgeSupervisor with fake OS identity, fake spawn and a fake API client. */
function legacyHarness({ listener = null, apiUp = true, jobCount = 0, events = [] } = {}) {
    const spawned = [];
    let up = apiUp;
    const client = {
        ping: async () => up,
        progress: async () => ({ state: { job_count: jobCount } }),
    };
    const spawnFn = (command, args, options) => {
        const child = new FakeChild(command);
        spawned.push({ command, args, options, child });
        events.push(`legacy:${command}`);
        if (command === "cmd.exe") queueMicrotask(() => { up = true; });   // becomes API-ready after launch
        if (command === "taskkill") queueMicrotask(() => { child.emit("exit", 0); spawned[0].child.emit("exit", 1); });
        return child;
    };
    const legacy = new LegacyReforgeSupervisor({
        env: {}, fsImpl: existsAll, platform: "win32", client, spawnFn, pollMs: 1, sleep: async () => {},
        listenerInspector: () => ({ ok: true, listeners: listener ? [listener] : [] }),
    });
    return { legacy, spawned, events, client };
}

function mangaRuntime({ ownership = "OWNED_BY_THIS_RUNTIME", events } = {}) {
    let stops = 0;
    return {
        runtime: {
            backendOwnership: ownership, workspaceOwnership: ownership,
            workspaceUrl: "http://127.0.0.1:8191", backendUrl: "http://127.0.0.1:8189",
            async start() { events?.push("manga:start"); return "READY"; },
            async probeWorkspace() { return { classification: "PREEXISTING_COMPATIBLE", details: "test" }; },
            async stopAll() { stops += 1; },
        },
        stops: () => stops,
    };
}

function supervisorWith({ legacy, events, runtime, verifySource = async () => ({ workspacePid: 1, backendPid: 2 }), logs }) {
    const h3Children = [];
    const supervisor = new TegakiShellSupervisor({
        portableRoot: ROOT,
        config: { withEasyReforge: true },
        portInspector: async port => ({ port, host: "127.0.0.1", state: "free", detail: "ECONNREFUSED" }),
        spawn: (command, args) => {
            const child = new FakeChild(args[0] || command);
            h3Children.push(child);
            events.push(`h3:${path.basename(args[0] || command)}`);
            return child;
        },
        waitFor: async () => ({ status: 200, json: { queue_running: [], queue_pending: [], playable: {}, still: {}, prep: {}, state: "READY" } }),
        runtimeFactory: () => runtime,
        verifySource,
        legacyFactory: () => legacy,
        browserLauncher: async () => { events.push("browser"); },
        log: message => logs.push(message), error: message => logs.push(message),
    });
    supervisor.h3SafeToStop = async () => true;
    return { supervisor, h3Children };
}

test("run_tegaki.bat is the top-level entrypoint; lower-level launchers remain", async () => {
    const bat = await fs.readFile(path.join(ROOT, "run_tegaki.bat"), "utf8");
    assert.match(bat, /node "%PORTABLE_ROOT%h3\\tools\\tegaki_shell_supervisor\.mjs" --with-easyreforge %\*/);
    assert.ok(bat.includes("\r\n"), "batch file uses CRLF line endings");
    assert.doesNotMatch(bat, /E:\\EasyReforge/i, "the Reference appliance is never referenced");
    for (const lower of [["h3", "run_h3.bat"], ["manga", "run_manga.bat"]]) {
        await fs.access(path.join(ROOT, ...lower));
    }
    assert.equal(WITH_EASYREFORGE_FLAG, "--with-easyreforge");
    assert.equal(readShellConfig({}).withEasyReforge, false, "run_h3.bat keeps its previous service set");
    assert.equal(readShellConfig({ TEGAKI_WITH_EASYREFORGE: "1" }).withEasyReforge, true);
});

test("compatible pre-existing Integration ReForge is recognised, reused (never spawned) and left running at shutdown", async () => {
    const events = [];
    const logs = [];
    const { legacy, spawned } = legacyHarness({ listener: { pid: 7001, executable: INTEGRATION_PYTHON } });
    const manga = mangaRuntime({ events });
    const { supervisor } = supervisorWith({ legacy, events, runtime: manga.runtime, logs });
    await supervisor.start();
    assert.equal(spawned.length, 0, "no second ReForge is started");
    assert.equal(supervisor.legacyOwnership, "PREEXISTING_COMPATIBLE");
    assert.ok(logs.some(line => /EasyReforge: PREEXISTING_COMPATIBLE \(PID 7001\)/.test(line)));
    assert.equal(legacy.status().owned, false);
    assert.equal(legacy.status().state, "ready");
    assert.equal(await supervisor.shutdown(), true);
    assert.equal(spawned.length, 0, "shutdown never taskkills an external ReForge");
    assert.ok(logs.some(line => /pre-existing Integration runtime left running/.test(line)));
    assert.equal(manga.stops(), 1);
});

test("empty 7862 launches ONLY the Integration runtime, before H3/Manga, without a browser tab; owned stop at shutdown", async () => {
    const events = [];
    const logs = [];
    const { legacy, spawned } = legacyHarness({ apiUp: false, events });
    const manga = mangaRuntime({ events });
    const { supervisor } = supervisorWith({ legacy, events, runtime: manga.runtime, logs });
    await supervisor.start();
    assert.equal(spawned[0].command, "cmd.exe");
    assert.equal(spawned[0].options.cwd, INTEGRATION_RUNTIME_ROOT);
    assert.ok(spawned[0].args.at(-1).includes("E:\\TEGAKI_Runtime\\EasyReforge\\Reforge.bat\" --api --port 7862"));
    assert.equal(spawned[0].options.env.SD_WEBUI_RESTARTING, "1", "ReForge's inbrowser gate is closed");
    assert.equal(supervisor.legacyOwnership, "OWNED_BY_THIS_RUNTIME");
    assert.deepEqual(events.slice(0, 4), ["legacy:cmd.exe", "h3:run_native_isolated.py", "h3:server.py", "manga:start"],
        "EasyReforge is ready before H3 and Manga start");
    assert.equal(events.at(-1), "browser", "the TEGAKI shell is presented last");
    spawned[0].child.stdout.emit("data", "Model loaded\ncivitai_api_key=SECRET-VALUE\n");
    assert.ok(logs.includes("[EasyReforge] Model loaded"));
    assert.ok(!logs.some(line => line.includes("SECRET-VALUE")), "secret-looking ReForge lines never reach the console");
    assert.equal(await supervisor.shutdown(), true);
    assert.deepEqual(spawned[1].args, ["/PID", String(spawned[0].child.pid), "/T", "/F"], "only the owned tree is stopped");
});

test("owned ReForge with a job in progress is not stopped (no force kill of active work)", async () => {
    const events = [];
    const logs = [];
    const { legacy, spawned } = legacyHarness({ apiUp: false, jobCount: 1 });
    const { supervisor } = supervisorWith({ legacy, events, runtime: mangaRuntime({ events }).runtime, logs });
    await supervisor.start();
    assert.equal(await supervisor.shutdown(), false);
    assert.equal(spawned.length, 1, "no taskkill while ReForge reports job_count > 0");
    assert.ok(logs.some(line => /EasyReforge safe stop refused/.test(line)));
});

test("unknown 7862 listener fails closed before H3 or Manga start and is never killed", async () => {
    for (const listener of [{ pid: 9001, executable: "C:\\Other\\python.exe" }, { pid: 9002, executable: "" }]) {
        const events = [];
        const logs = [];
        const { legacy, spawned } = legacyHarness({ listener });
        let runtimeCalls = 0;
        const { supervisor, h3Children } = supervisorWith({ legacy, events, logs,
            runtime: new Proxy({}, { get() { runtimeCalls += 1; throw new Error("Manga must not start"); } }) });
        await assert.rejects(supervisor.start(), /EasyReforge: Port 7862 is occupied by an unverified process/);
        assert.equal(spawned.length, 0, "no ReForge spawn and no taskkill");
        assert.equal(h3Children.length, 0);
        assert.equal(runtimeCalls, 0);
    }
    const events = [];
    const { legacy, spawned } = legacyHarness({ apiUp: true });   // something answers the API with no verified listener
    const { supervisor } = supervisorWith({ legacy, events, logs: [], runtime: mangaRuntime({ events }).runtime });
    await assert.rejects(supervisor.start(), /no verified Integration listener/);
    assert.equal(spawned.length, 0);
});

test("stale reused Manga workspace is refused (fail closed); owned services skip the source check", async () => {
    const events = [];
    const logs = [];
    const { legacy } = legacyHarness({ listener: { pid: 7001, executable: INTEGRATION_PYTHON } });
    const reused = mangaRuntime({ ownership: "PREEXISTING_COMPATIBLE", events });
    let verified = 0;
    const { supervisor, h3Children } = supervisorWith({ legacy, events, logs, runtime: reused.runtime,
        verifySource: async runtime => {
            verified += 1;
            assert.equal(runtime.workspaceUrl, "http://127.0.0.1:8191");
            throw new Error("STALE WORKSPACE SERVER: the process on the workspace port loaded older manga/service source than is on disk");
        } });
    await assert.rejects(supervisor.start(), /STALE WORKSPACE SERVER/);
    assert.equal(verified, 1);
    assert.ok(!events.includes("browser"), "a stale implementation is never presented");
    assert.ok(h3Children.every(child => child.killed), "owned H3 children are cleaned up after the refusal");
    assert.equal(reused.stops(), 1, "Manga stop decision stays with MangaDomainRuntime (pre-existing left untouched)");

    const ownedEvents = [];
    let ownedVerified = 0;
    const { legacy: legacy2 } = legacyHarness({ listener: { pid: 7001, executable: INTEGRATION_PYTHON } });
    const { supervisor: fresh } = supervisorWith({ legacy: legacy2, events: ownedEvents, logs: [],
        runtime: mangaRuntime({ events: ownedEvents }).runtime, verifySource: async () => { ownedVerified += 1; return {}; } });
    await fresh.start();
    assert.equal(ownedVerified, 0, "services started by this runtime are fresh by construction");
    await fresh.shutdown();
});

test("without --with-easyreforge the shell supervisor does not touch 7862", async () => {
    const events = [];
    let legacyCalls = 0;
    const supervisor = new TegakiShellSupervisor({
        portableRoot: ROOT,
        portInspector: async port => ({ port, host: "127.0.0.1", state: "free", detail: "ECONNREFUSED" }),
        spawn: (command, args) => new FakeChild(args[0] || command),
        waitFor: async () => ({ status: 200, json: { queue_running: [], queue_pending: [], playable: {}, still: {}, prep: {}, state: "READY" } }),
        runtimeFactory: () => mangaRuntime({ events }).runtime,
        legacyFactory: () => { legacyCalls += 1; throw new Error("must not be used"); },
        browserLauncher: async () => {}, log: () => {}, error: () => {},
    });
    supervisor.h3SafeToStop = async () => true;
    await supervisor.start();
    assert.equal(legacyCalls, 0);
    assert.equal(await supervisor.shutdown(), true);
});
