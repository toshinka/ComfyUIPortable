import assert from "node:assert/strict";
import { EventEmitter } from "node:events";
import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";
import {
    MangaDomainRuntime,
    OwnershipClassification,
} from "../service/manga_domain_runtime.mjs";
import { TegakiShellSupervisor } from "../../h3/tools/tegaki_shell_supervisor.mjs";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..", "..");

class FakeChild extends EventEmitter {
    static nextPid = 92000;

    constructor() {
        super();
        this.pid = FakeChild.nextPid++;
        this.killed = false;
        this.exitCode = null;
        this.signalCode = null;
        this.stdout = new EventEmitter();
        this.stderr = new EventEmitter();
    }

    kill(signal = "SIGTERM") {
        if (this.killed) return true;
        this.killed = true;
        this.signalCode = signal;
        this.exitCode = 0;
        queueMicrotask(() => this.emit("exit", 0, signal));
        return true;
    }
}

async function captureBackendArgs(configuredOutputDir) {
    const previous = process.env.TEGAKI_MANGA_OUTPUT_DIR;
    if (configuredOutputDir == null) delete process.env.TEGAKI_MANGA_OUTPUT_DIR;
    else process.env.TEGAKI_MANGA_OUTPUT_DIR = configuredOutputDir;

    let spawnSpec = null;
    try {
        const runtime = new MangaDomainRuntime({
            portableRoot: ROOT,
            startupWaitTimeoutMs: 100,
            log: () => {},
            customSpawnBackend: spec => {
                spawnSpec = spec;
                return new FakeChild();
            },
        });
        runtime.probeBackend = async () => ({
            classification: OwnershipClassification.PREEXISTING_COMPATIBLE,
            queue: { queue_running: [], queue_pending: [] },
        });
        await runtime._spawnBackendChild();
        const args = [...spawnSpec.args];
        await runtime.stopBackend();
        return { runtime, args };
    } finally {
        if (previous == null) delete process.env.TEGAKI_MANGA_OUTPUT_DIR;
        else process.env.TEGAKI_MANGA_OUTPUT_DIR = previous;
    }
}

test("Manga backend receives exactly one DynamicVRAM headroom flag", async () => {
    const { args } = await captureBackendArgs(null);
    const indexes = args.reduce((found, value, index) => value === "--vram-headroom" ? [...found, index] : found, []);
    assert.equal(indexes.length, 1);
    assert.equal(args[indexes[0] + 1], "2.0");
});

test("Manga backend receives the default absolute output/Tegaki root", async () => {
    const { runtime, args } = await captureBackendArgs(null);
    const outputIndex = args.indexOf("--output-directory");
    const expected = path.resolve(ROOT, "output", "Tegaki");
    assert.notEqual(outputIndex, -1);
    assert.equal(args[outputIndex + 1], expected);
    assert.equal(runtime.mangaOutputDir, expected);
});

test("TEGAKI_MANGA_OUTPUT_DIR is resolved and passed as a normal argv value", async () => {
    const configured = path.join(os.tmpdir(), "tegaki-play5-output");
    const { runtime, args } = await captureBackendArgs(configured);
    const outputIndex = args.indexOf("--output-directory");
    assert.equal(args[outputIndex + 1], path.resolve(configured));
    assert.equal(runtime.mangaOutputDir, path.resolve(configured));
    assert.equal(args.includes("&&"), false, "filesystem roots must not become shell fragments");
});

test("the logical Manga/Playable SaveImage namespace remains unchanged", async () => {
    const sceneSource = await fs.readFile(
        path.join(ROOT, "custom_nodes_custom", "tegaki_manga_nodes", "scene_generation.py"),
        "utf8",
    );
    assert.match(sceneSource, /Manga[\\/]Playable/);
});

test("Manga output override does not alter H3 launch arguments", async () => {
    const calls = [];
    const children = [];
    const supervisor = new TegakiShellSupervisor({
        portableRoot: ROOT,
        spawn: (command, args, options) => {
            const child = new FakeChild();
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
    await supervisor.startH3Processes();

    assert.equal(calls.length, 2);
    const nativeArgs = calls[0].args;
    assert.equal(nativeArgs.includes("--vram-headroom"), false);
    const nativeOutput = nativeArgs.indexOf("--output-directory");
    assert.equal(nativeArgs[nativeOutput + 1], path.resolve(ROOT, "output", "h3"));
    const skinArgs = calls[1].args;
    const skinOutput = skinArgs.indexOf("--output-dir");
    assert.equal(skinArgs[skinOutput + 1], "output/h3");

    assert.equal(await supervisor.shutdown(), true);
    assert.ok(children.every(child => child.killed));
});

console.log("MANGA OUTPUT OVERRIDE TESTS PASS");
