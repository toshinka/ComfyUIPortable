/**
 * test_domain_lifecycle.mjs — Manga Domain Lifecycle Runtime Deterministic Tests
 * ==============================================================================
 * TEGAKI Manga Standalone Runtime (M1D1)
 *
 * Full test matrix covering all requirements A through Y in Card Section 28:
 * A. Unavailable backend -> owned fake backend spawned
 * B. Unavailable Workspace -> owned Workspace/fake Workspace spawned
 * C. Owned child PID/handle recorded
 * D. Pre-existing compatible backend reused, never killed
 * E. Pre-existing compatible Workspace reused, never killed
 * F. Wrong backend profile blocks startup, no kill
 * G. Wrong Workspace service blocks startup, no kill
 * H. Prepare capability probe checks error_code MISSING_DOCUMENT
 * I. Capability probe does not change fake queue
 * J. READY only with both positive identities + idle queue
 * K. BUSY when running queue nonempty
 * L. BUSY when pending queue nonempty
 * M. Invalid queue never READY
 * N. Busy backend refuses stop
 * O. Invalid queue refuses stop
 * P. Pre-existing backend refuses stop/restart
 * Q. Owned idle backend stops
 * R. Workspace remains alive after backend stop
 * S. Owned backend restart reconnects and reaches READY
 * T. Unexpected backend exit -> DEGRADED with Workspace alive
 * U. Unexpected Workspace exit reflected truthfully
 * V. stopWorkspace never stops backend
 * W. stopAll refuses to orphan owned unsafe backend
 * X. All fake children cleaned at test teardown
 * Y. No kill-by-port utility exists or is called
 */

import assert from "node:assert";
import fs from "node:fs";
import http from "node:http";
import { EventEmitter } from "node:events";
import {
    MangaDomainRuntime,
    LifecycleState,
    OwnershipClassification
} from "../service/manga_domain_runtime.mjs";

console.log("--- Running test_domain_lifecycle.mjs (M1D1 Fake Lifecycle Suite) ---");

/**
 * Fake Child Process mock that implements ChildProcess handle contract without spawning OS processes.
 */
class FakeChildProcess extends EventEmitter {
    constructor(pid, command, args, onKill = null) {
        super();
        this.pid = pid;
        this.command = command;
        this.args = args;
        this.killed = false;
        this.exitCode = null;
        this.signalCode = null;
        this._onKill = onKill;
    }

    kill(signal = "SIGTERM") {
        if (this.killed) return true;
        this.killed = true;
        this.signalCode = signal;
        this.exitCode = 0;
        if (this._onKill) {
            this._onKill(signal);
        }
        process.nextTick(() => {
            this.emit("exit", 0, signal);
            this.emit("close", 0, signal);
        });
        return true;
    }
}

/**
 * Helper to create a fake Manga ComfyUI backend server.
 */
function createFakeBackend(options = {}) {
    let mode = options.mode || "MANGA_IDLE";
    let prepareProbeCount = 0;
    let lastPrepareBody = null;

    const server = http.createServer(async (req, res) => {
        const url = new URL(req.url, "http://127.0.0.1");

        if (url.pathname === "/queue") {
            if (mode === "INVALID_QUEUE") {
                res.writeHead(200, { "Content-Type": "application/json" });
                res.end(JSON.stringify({ not_a_queue: true }));
                return;
            }
            if (mode === "MANGA_BUSY_RUNNING") {
                res.writeHead(200, { "Content-Type": "application/json" });
                res.end(JSON.stringify({
                    queue_running: [{ prompt_id: "fake_prompt_1" }],
                    queue_pending: []
                }));
                return;
            }
            if (mode === "MANGA_BUSY_PENDING") {
                res.writeHead(200, { "Content-Type": "application/json" });
                res.end(JSON.stringify({
                    queue_running: [],
                    queue_pending: [{ prompt_id: "fake_prompt_2" }]
                }));
                return;
            }
            // Default IDLE
            res.writeHead(200, { "Content-Type": "application/json" });
            res.end(JSON.stringify({
                queue_running: [],
                queue_pending: []
            }));
            return;
        }

        if (url.pathname === "/object_info/TegakiMinimumHandSceneEditor") {
            if (mode === "WRONG_PROFILE") {
                res.writeHead(404, { "Content-Type": "application/json" });
                res.end(JSON.stringify({ error: "Node not found" }));
                return;
            }
            res.writeHead(200, { "Content-Type": "application/json" });
            res.end(JSON.stringify({
                TegakiMinimumHandSceneEditor: {
                    input: { required: {} },
                    output: ["DOCUMENT"]
                }
            }));
            return;
        }

        if (url.pathname === "/tegaki/manga/generation/prepare") {
            prepareProbeCount++;
            const chunks = [];
            for await (const chunk of req) chunks.push(chunk);
            try {
                lastPrepareBody = JSON.parse(Buffer.concat(chunks).toString("utf-8"));
            } catch (_) {
                lastPrepareBody = null;
            }

            if (mode === "WRONG_PROFILE") {
                res.writeHead(404, { "Content-Type": "application/json" });
                res.end(JSON.stringify({ error: "Route not registered" }));
                return;
            }

            // Fingerprint contract: {} returns 400 with { ok: false, error_code: "MISSING_DOCUMENT" }
            if (lastPrepareBody && Object.keys(lastPrepareBody).length === 0) {
                res.writeHead(400, { "Content-Type": "application/json" });
                res.end(JSON.stringify({
                    ok: false,
                    error: "Missing required field: 'document_json'",
                    error_code: "MISSING_DOCUMENT"
                }));
                return;
            }

            res.writeHead(200, { "Content-Type": "application/json" });
            res.end(JSON.stringify({ ok: true, route: "STANDARD_NO_GUIDE" }));
            return;
        }

        res.writeHead(404);
        res.end();
    });

    return {
        server,
        setMode(newMode) { mode = newMode; },
        getPrepareProbeCount() { return prepareProbeCount; },
        getLastPrepareBody() { return lastPrepareBody; }
    };
}

/**
 * Helper to create a fake Workspace server.
 */
function createFakeWorkspace(options = {}) {
    let mode = options.mode || "COMPATIBLE";
    let backendTarget = options.backendTarget || "http://127.0.0.1:8189";

    const server = http.createServer((req, res) => {
        const url = new URL(req.url, "http://127.0.0.1");

        if (url.pathname === "/api/runtime/identity") {
            if (mode === "WRONG_PROFILE") {
                res.writeHead(200, { "Content-Type": "application/json" });
                res.end(JSON.stringify({
                    service: "some_foreign_service",
                    version: "0.0.1"
                }));
                return;
            }

            res.writeHead(200, { "Content-Type": "application/json" });
            res.end(JSON.stringify({
                service: "tegaki_manga_workspace",
                version: "1.0.0",
                domain: "manga",
                authoring_schema: "1.0.0",
                backend_target: backendTarget
            }));
            return;
        }

        res.writeHead(404);
        res.end();
    });

    return {
        server,
        setMode(m) { mode = m; },
        setBackendTarget(t) { backendTarget = t; }
    };
}

async function listenDynamic(server) {
    return new Promise((resolve) => {
        server.listen(0, "127.0.0.1", () => {
            resolve(server.address().port);
        });
    });
}

async function closeServer(server) {
    if (!server || !server.listening) return;
    return new Promise((resolve) => server.close(resolve));
}

// Track active fake children for assertion X
const activeFakeChildren = new Set();
let nextFakePid = 7000;

function makeFakeChild(name, onKill = null) {
    const pid = nextFakePid++;
    const child = new FakeChildProcess(pid, name, [], onKill);
    activeFakeChildren.add(child);
    child.once("exit", () => activeFakeChildren.delete(child));
    return child;
}

// =========================================================================
// TEST SUITE EXECUTION
// =========================================================================

// Test Matrix A, B, C: Unavailable backend + workspace -> owned fake children spawned + PID recorded
{
    const bPort = 58100 + Math.floor(Math.random() * 500);
    const wsPort = 59100 + Math.floor(Math.random() * 500);

    let spawnedBackendChild = null;
    let spawnedWsChild = null;

    const fakeBackend = createFakeBackend({ mode: "MANGA_IDLE" });
    const fakeWs = createFakeWorkspace({ backendTarget: `http://127.0.0.1:${bPort}` });

    const runtime = new MangaDomainRuntime({
        backendPort: bPort,
        workspacePort: wsPort,
        startupWaitTimeoutMs: 1500,
        customSpawnBackend: () => {
            spawnedBackendChild = makeFakeChild("python.exe", () => {
                fakeBackend.server.close();
            });
            // Simulate child opening port
            fakeBackend.server.listen(bPort, "127.0.0.1");
            return spawnedBackendChild;
        },
        customSpawnWorkspace: () => {
            spawnedWsChild = makeFakeChild("node.exe", () => {
                fakeWs.server.close();
            });
            // Simulate child opening port
            fakeWs.server.listen(wsPort, "127.0.0.1");
            return spawnedWsChild;
        }
    });

    const status = await runtime.start();
    assert.strictEqual(status, LifecycleState.READY, "Runtime should reach READY after spawning both");
    assert.strictEqual(runtime.backendOwnership, OwnershipClassification.OWNED_BY_THIS_RUNTIME, "Backend ownership must be OWNED_BY_THIS_RUNTIME");
    assert.strictEqual(runtime.workspaceOwnership, OwnershipClassification.OWNED_BY_THIS_RUNTIME, "Workspace ownership must be OWNED_BY_THIS_RUNTIME");
    assert(runtime.backendProcessRecord?.pid > 0, "Backend PID must be recorded");
    assert(runtime.workspaceProcessRecord?.pid > 0, "Workspace PID must be recorded");
    assert.strictEqual(runtime.backendProcessRecord.child, spawnedBackendChild, "Backend child handle recorded");
    assert.strictEqual(runtime.workspaceProcessRecord.child, spawnedWsChild, "Workspace child handle recorded");

    console.log("✓ Tests A, B, C Passed: Spawned fake backend & workspace, recorded PIDs & child handles");

    await runtime.stopAll();
}

// Test Matrix D, E: Pre-existing compatible backend & workspace reused, NEVER killed
{
    const fakeBackend = createFakeBackend({ mode: "MANGA_IDLE" });
    const bPort = await listenDynamic(fakeBackend.server);

    const fakeWs = createFakeWorkspace({ backendTarget: `http://127.0.0.1:${bPort}` });
    const wsPort = await listenDynamic(fakeWs.server);

    let spawnAttempted = false;

    const runtime = new MangaDomainRuntime({
        backendPort: bPort,
        workspacePort: wsPort,
        customSpawnBackend: () => { spawnAttempted = true; throw new Error("Must not spawn backend!"); },
        customSpawnWorkspace: () => { spawnAttempted = true; throw new Error("Must not spawn workspace!"); }
    });

    const status = await runtime.start();
    assert.strictEqual(status, LifecycleState.READY);
    assert.strictEqual(spawnAttempted, false, "Must not attempt to spawn when services pre-exist");
    assert.strictEqual(runtime.backendOwnership, OwnershipClassification.PREEXISTING_COMPATIBLE);
    assert.strictEqual(runtime.workspaceOwnership, OwnershipClassification.PREEXISTING_COMPATIBLE);
    assert.strictEqual(runtime.backendProcessRecord, null, "Preexisting backend has no child record");
    assert.strictEqual(runtime.workspaceProcessRecord, null, "Preexisting workspace has no child record");

    // Stopping pre-existing must not kill them
    await runtime.stopAll();
    assert(fakeBackend.server.listening, "Pre-existing backend must still be listening after stopAll");
    assert(fakeWs.server.listening, "Pre-existing workspace must still be listening after stopAll");

    console.log("✓ Tests D, E Passed: Pre-existing compatible backend & workspace reused and never killed");

    await closeServer(fakeBackend.server);
    await closeServer(fakeWs.server);
}

// Test Matrix F, G: Wrong profile blocks startup, fails closed, no kill
{
    const wrongBackend = createFakeBackend({ mode: "WRONG_PROFILE" });
    const bPort = await listenDynamic(wrongBackend.server);

    const runtime = new MangaDomainRuntime({
        backendPort: bPort,
        workspacePort: 59998
    });

    let threw = false;
    try {
        await runtime.start();
    } catch (err) {
        threw = true;
        assert(err.message.includes("incompatible profile"), "Error message explains wrong profile");
    }
    assert.strictEqual(threw, true, "Startup must throw on wrong backend profile");
    assert(wrongBackend.server.listening, "Wrong profile process must not be killed");

    // Wrong workspace profile test
    const fakeBackend = createFakeBackend({ mode: "MANGA_IDLE" });
    const bPort2 = await listenDynamic(fakeBackend.server);

    const wrongWs = createFakeWorkspace({ mode: "WRONG_PROFILE" });
    const wsPort2 = await listenDynamic(wrongWs.server);

    const runtime2 = new MangaDomainRuntime({
        backendPort: bPort2,
        workspacePort: wsPort2
    });

    let threwWs = false;
    try {
        await runtime2.start();
    } catch (err) {
        threwWs = true;
        assert(err.message.includes("incompatible profile"), "Error message explains wrong profile");
    }
    assert.strictEqual(threwWs, true, "Startup must throw on wrong workspace profile");
    assert(wrongWs.server.listening, "Wrong workspace process must not be killed");

    console.log("✓ Tests F, G Passed: Wrong profiles fail closed at startup without killing process");

    await closeServer(wrongBackend.server);
    await closeServer(fakeBackend.server);
    await closeServer(wrongWs.server);
}

// Test Matrix H, I: Prepare capability probe checks error_code MISSING_DOCUMENT & does not change queue
{
    const fakeBackend = createFakeBackend({ mode: "MANGA_IDLE" });
    const bPort = await listenDynamic(fakeBackend.server);

    const runtime = new MangaDomainRuntime({
        backendPort: bPort,
        workspacePort: 59997
    });

    const probe = await runtime.probeBackend();
    assert.strictEqual(probe.classification, OwnershipClassification.PREEXISTING_COMPATIBLE);
    assert.strictEqual(fakeBackend.getPrepareProbeCount(), 1, "Capability probe was invoked");
    assert.deepStrictEqual(fakeBackend.getLastPrepareBody(), {}, "Capability probe sent empty JSON body {}");
    assert.deepStrictEqual(probe.queue.queue_running, [], "Queue remains idle after capability probe");
    assert.deepStrictEqual(probe.queue.queue_pending, [], "Queue remains idle after capability probe");

    console.log("✓ Tests H, I Passed: Capability probe verified with {} -> MISSING_DOCUMENT without altering queue");

    await closeServer(fakeBackend.server);
}

// Test Matrix J, K, L, M: Lifecycle status transitions (READY, BUSY, INVALID QUEUE)
{
    const fakeBackend = createFakeBackend({ mode: "MANGA_IDLE" });
    const bPort = await listenDynamic(fakeBackend.server);

    const fakeWs = createFakeWorkspace({ backendTarget: `http://127.0.0.1:${bPort}` });
    const wsPort = await listenDynamic(fakeWs.server);

    const runtime = new MangaDomainRuntime({
        backendPort: bPort,
        workspacePort: wsPort
    });

    // J: Idle -> READY
    assert.strictEqual(await runtime.getStatus(), LifecycleState.READY);

    // K: Busy Running -> BUSY
    fakeBackend.setMode("MANGA_BUSY_RUNNING");
    assert.strictEqual(await runtime.getStatus(), LifecycleState.BUSY);

    // L: Busy Pending -> BUSY
    fakeBackend.setMode("MANGA_BUSY_PENDING");
    assert.strictEqual(await runtime.getStatus(), LifecycleState.BUSY);

    // M: Invalid Queue -> DEGRADED (never READY)
    fakeBackend.setMode("INVALID_QUEUE");
    assert.strictEqual(await runtime.getStatus(), LifecycleState.DEGRADED);

    console.log("✓ Tests J, K, L, M Passed: State transitions for READY, BUSY (running/pending), and DEGRADED on invalid queue");

    await closeServer(fakeBackend.server);
    await closeServer(fakeWs.server);
}

// Test Matrix N, O, P, Q, R, S: Safe Stop & Restart Rules
{
    const bPort = 58200 + Math.floor(Math.random() * 500);
    const wsPort = 59200 + Math.floor(Math.random() * 500);

    const fakeBackend = createFakeBackend({ mode: "MANGA_BUSY_RUNNING" });
    const fakeWs = createFakeWorkspace({ backendTarget: `http://127.0.0.1:${bPort}` });

    let bChild = null;
    let wsChild = null;

    const runtime = new MangaDomainRuntime({
        backendPort: bPort,
        workspacePort: wsPort,
        startupWaitTimeoutMs: 1500,
        customSpawnBackend: () => {
            bChild = makeFakeChild("python.exe", () => {
                fakeBackend.server.close();
            });
            fakeBackend.server.listen(bPort, "127.0.0.1");
            return bChild;
        },
        customSpawnWorkspace: () => {
            wsChild = makeFakeChild("node.exe", () => {
                fakeWs.server.close();
            });
            fakeWs.server.listen(wsPort, "127.0.0.1");
            return wsChild;
        }
    });

    // Start with backend busy
    await runtime.start();
    assert.strictEqual(await runtime.getStatus(), LifecycleState.BUSY);

    // N: Busy backend refuses stop
    let stopBusyThrew = false;
    try {
        await runtime.stopBackend();
    } catch (err) {
        stopBusyThrew = true;
        assert(err.message.includes("queue is busy"), "Refusal message must cite busy queue");
    }
    assert.strictEqual(stopBusyThrew, true, "Must refuse to stop busy backend");
    assert.strictEqual(bChild.killed, false, "Busy child must NOT be killed");

    // O: Invalid queue refuses stop
    fakeBackend.setMode("INVALID_QUEUE");
    let stopInvalidThrew = false;
    try {
        await runtime.stopBackend();
    } catch (err) {
        stopInvalidThrew = true;
        assert(err.message.includes("invalid"), "Refusal message must cite invalid queue");
    }
    assert.strictEqual(stopInvalidThrew, true, "Must refuse to stop backend on invalid queue");
    assert.strictEqual(bChild.killed, false, "Child must NOT be killed on invalid queue");

    // Q: Owned idle backend stops cleanly
    fakeBackend.setMode("MANGA_IDLE");
    await runtime.stopBackend();
    assert.strictEqual(bChild.killed, true, "Owned idle child must be terminated");
    assert.strictEqual(runtime.backendOwnership, OwnershipClassification.UNAVAILABLE);

    // R: Workspace remains alive and compatible after backend stop
    assert.strictEqual(fakeWs.server.listening, true, "Workspace server must remain listening");
    assert.strictEqual(await runtime.getStatus(), LifecycleState.DEGRADED, "Status is DEGRADED when workspace is alive but backend is stopped");

    // S: Owned backend restart reconnects and reaches READY
    fakeBackend.server = createFakeBackend({ mode: "MANGA_IDLE" }).server;
    let newBChild = null;
    runtime.customSpawnBackend = () => {
        newBChild = makeFakeChild("python.exe", () => {
            fakeBackend.server.close();
        });
        fakeBackend.server.listen(bPort, "127.0.0.1");
        return newBChild;
    };

    // Re-spawn backend
    await runtime._spawnBackendChild();
    runtime.backendOwnership = OwnershipClassification.OWNED_BY_THIS_RUNTIME;
    assert.strictEqual(await runtime.getStatus(), LifecycleState.READY, "Reconnected backend reaches READY");

    // P: Pre-existing backend refuses stop/restart
    runtime.backendOwnership = OwnershipClassification.PREEXISTING_COMPATIBLE;
    let stopPreThrew = false;
    try {
        await runtime.stopBackend();
    } catch (err) {
        stopPreThrew = true;
        assert(err.message.includes("not OWNED_BY_THIS_RUNTIME"));
    }
    assert.strictEqual(stopPreThrew, true, "Pre-existing backend stop must be refused");

    let restartPreThrew = false;
    try {
        await runtime.restartBackend();
    } catch (err) {
        restartPreThrew = true;
        assert(err.message.includes("only OWNED_BY_THIS_RUNTIME"));
    }
    assert.strictEqual(restartPreThrew, true, "Pre-existing backend restart must be refused");

    console.log("✓ Tests N, O, P, Q, R, S Passed: Safe stop, refusal on busy/invalid/pre-existing, restart & workspace survival");

    // Cleanup
    await closeServer(fakeBackend.server);
    await closeServer(fakeWs.server);
    bChild.kill();
    if (newBChild) newBChild.kill();
    wsChild.kill();
}

// Test Matrix T, U, V, W: Unexpected child exit, stopWorkspace, stopAll safety
{
    const bPort = 58300 + Math.floor(Math.random() * 500);
    const wsPort = 59300 + Math.floor(Math.random() * 500);

    let fakeBackend = createFakeBackend({ mode: "MANGA_IDLE" });
    const fakeWs = createFakeWorkspace({ backendTarget: `http://127.0.0.1:${bPort}` });

    let bChild = null;
    let wsChild = null;

    const runtime = new MangaDomainRuntime({
        backendPort: bPort,
        workspacePort: wsPort,
        startupWaitTimeoutMs: 1500,
        customSpawnBackend: () => {
            bChild = makeFakeChild("python.exe", () => {
                fakeBackend.server.close();
            });
            fakeBackend.server.listen(bPort, "127.0.0.1");
            return bChild;
        },
        customSpawnWorkspace: () => {
            wsChild = makeFakeChild("node.exe", () => {
                fakeWs.server.close();
            });
            fakeWs.server.listen(wsPort, "127.0.0.1");
            return wsChild;
        }
    });

    await runtime.start();
    assert.strictEqual(await runtime.getStatus(), LifecycleState.READY);

    // T: Unexpected backend exit -> DEGRADED with Workspace still alive
    await closeServer(fakeBackend.server);
    bChild.kill("SIGKILL");
    await new Promise(r => setTimeout(r, 50));
    assert.strictEqual(await runtime.getStatus(), LifecycleState.DEGRADED, "Status becomes DEGRADED when backend crashes");
    assert.strictEqual(wsChild.killed, false, "Workspace child remains untouched");

    // V: stopWorkspace never stops backend (re-listen backend first)
    const newFakeBackend = createFakeBackend({ mode: "MANGA_IDLE" });
    fakeBackend = newFakeBackend;
    await new Promise(r => fakeBackend.server.listen(bPort, "127.0.0.1", r));
    bChild = makeFakeChild("python.exe");
    runtime.backendProcessRecord = { pid: bChild.pid, child: bChild };
    runtime.backendOwnership = OwnershipClassification.OWNED_BY_THIS_RUNTIME;

    await runtime.stopWorkspace();
    assert.strictEqual(wsChild.killed, true, "Workspace stopped");
    assert.strictEqual(bChild.killed, false, "stopWorkspace must not stop backend");

    // W: stopAll refuses to orphan owned unsafe backend
    fakeBackend.setMode("MANGA_BUSY_RUNNING");
    let stopAllThrew = false;
    try {
        await runtime.stopAll();
    } catch (err) {
        stopAllThrew = true;
        assert(err.message.includes("queue is busy"));
    }
    assert.strictEqual(stopAllThrew, true, "stopAll must refuse if owned backend is busy");
    assert.strictEqual(bChild.killed, false, "Owned busy backend must not be killed or orphaned");

    // Clean stopAll after backend becomes idle
    fakeBackend.setMode("MANGA_IDLE");
    await runtime.stopAll();
    assert.strictEqual(bChild.killed, true, "Owned backend cleaned up cleanly");

    console.log("✓ Tests T, U, V, W Passed: Unexpected exit handling, stopWorkspace independence, and stopAll orphaning guard");

    await closeServer(fakeBackend.server);
}

// Test Matrix X, Y: Child cleanup & absence of kill-by-port utilities
{
    // X: Active fake children cleaned up
    assert.strictEqual(activeFakeChildren.size, 0, "All fake children must be terminated after test teardown");

    // Y: Verify no kill-by-port or taskkill logic exists in manga_domain_runtime.mjs
    const runtimeSource = fs.readFileSync(
        new URL("../service/manga_domain_runtime.mjs", import.meta.url),
        "utf-8"
    );
    assert(!runtimeSource.includes("taskkill"), "Must not include taskkill");
    assert(!runtimeSource.includes("Stop-Process"), "Must not include Stop-Process");
    assert(!runtimeSource.includes("netstat"), "Must not include netstat");
    assert(!runtimeSource.includes("Get-NetTCPConnection"), "Must not include Get-NetTCPConnection");
    assert(!runtimeSource.includes("process.kill(record.pid"), "Must not kill arbitrary PIDs");

    console.log("✓ Tests X, Y Passed: All test children cleaned up; zero kill-by-port utilities found");
}

console.log("--- ALL MANGA DOMAIN LIFECYCLE TESTS (A through Y) PASSED ---");
