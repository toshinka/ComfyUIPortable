/**
 * test_domain_lifecycle.mjs — Manga Domain Lifecycle Runtime Deterministic Tests
 * ==============================================================================
 * TEGAKI Manga Standalone Runtime (M1D1 / M1D1A)
 *
 * Full test matrix covering all requirements A through Y (M1D1) plus
 * M1D1A hotfix assertions:
 * A. Second queue unavailable after valid first read -> not compatible
 * B. Second queue malformed after valid first read -> not compatible
 * C. stopBackend with stale first-idle / failed second queue -> refused, child kill count = 0
 * D. Generic { input: {} } object-info -> wrong profile
 * E. Public await runtime.restartBackend() -> old child stopped, new child started, workspace survives, reaches READY
 * F. Unexpected workspace exit -> backend untouched, status DEGRADED, lastWorkspaceExit recorded
 * G. Unexpected backend exit -> lastBackendExit recorded
 * H. Partial startup failure (owned backend spawned, then wrong workspace encountered) -> wrong external workspace not killed, owned backend safely stopped
 */

import assert from "node:assert";
import fs from "node:fs";
import http from "node:http";
import { EventEmitter } from "node:events";
import {
    MangaDomainRuntime,
    LifecycleState,
    OwnershipClassification,
    InternalSubstate
} from "../service/manga_domain_runtime.mjs";

console.log("--- Running test_domain_lifecycle.mjs (M1D1 / M1D1A Suite) ---");

/**
 * Fake Child Process mock that implements ChildProcess handle contract without spawning OS processes.
 */
class FakeChildProcess extends EventEmitter {
    constructor(pid, command, args, onKill = null, stubborn = false) {
        super();
        this.pid = pid;
        this.command = command;
        this.args = args;
        this.killed = false;
        this.exitCode = null;
        this.signalCode = null;
        this._onKill = onKill;
        this._stubborn = stubborn;
    }

    kill(signal = "SIGTERM") {
        if (this.killed) return true;
        this.killed = true;
        this.signalCode = signal;
        if (this._onKill) {
            this._onKill(signal);
        }
        if (!this._stubborn) {
            this.exitCode = 0;
            process.nextTick(() => {
                this.emit("exit", 0, signal);
                this.emit("close", 0, signal);
            });
        }
        return true;
    }

    triggerExit(code = 0, signal = "SIGTERM") {
        this.exitCode = code;
        this.signalCode = signal;
        process.nextTick(() => {
            this.emit("exit", code, signal);
            this.emit("close", code, signal);
        });
    }
}

/**
 * Helper to create a fake Manga ComfyUI backend server.
 */
function createFakeBackend(options = {}) {
    let mode = options.mode || "MANGA_IDLE";
    let prepareProbeCount = 0;
    let lastPrepareBody = null;
    let queueReadCount = 0;
    let secondQueueMode = options.secondQueueMode || null; // e.g. "UNAVAILABLE", "MALFORMED"

    const server = http.createServer(async (req, res) => {
        const url = new URL(req.url, "http://127.0.0.1");

        if (url.pathname === "/queue") {
            queueReadCount++;
            if (queueReadCount >= 2 && secondQueueMode) {
                if (secondQueueMode === "UNAVAILABLE") {
                    res.writeHead(500, { "Content-Type": "text/plain" });
                    res.end("Internal Server Error");
                    return;
                }
                if (secondQueueMode === "MALFORMED") {
                    res.writeHead(200, { "Content-Type": "application/json" });
                    res.end(JSON.stringify({ not_a_queue: true }));
                    return;
                }
            }

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
            if (mode === "GENERIC_INPUT_NODE") {
                // Returns top-level { "input": {...} } without TegakiMinimumHandSceneEditor key
                res.writeHead(200, { "Content-Type": "application/json" });
                res.end(JSON.stringify({
                    input: { required: {} },
                    output: ["IMAGE"]
                }));
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
        setSecondQueueMode(sqm) { secondQueueMode = sqm; },
        getQueueReadCount() { return queueReadCount; },
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

function makeFakeChild(name, onKill = null, stubborn = false) {
    const pid = nextFakePid++;
    const child = new FakeChildProcess(pid, name, [], onKill, stubborn);
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
            fakeBackend.server.listen(bPort, "127.0.0.1");
            return spawnedBackendChild;
        },
        customSpawnWorkspace: () => {
            spawnedWsChild = makeFakeChild("node.exe", () => {
                fakeWs.server.close();
            });
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
    assert.strictEqual(runtime.backendProcessRecord, null);
    assert.strictEqual(runtime.backendOwnership, OwnershipClassification.UNAVAILABLE);
    assert.strictEqual(runtime.lastBackendExit?.intentional, true, "Intentional backend exit flag recorded");

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
    assert.strictEqual(runtime.lastBackendExit?.intentional, false, "lastBackendExit recorded as unintentional");

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
    assert.strictEqual(runtime.lastWorkspaceExit?.intentional, true, "lastWorkspaceExit recorded as intentional");

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

// =========================================================================
// M1D1A HOTFIX DETERMINISTIC MATRIX (Checks A through H)
// =========================================================================

// M1D1A Check A: Second queue unavailable after valid first read -> not compatible
{
    const fakeBackend = createFakeBackend({ mode: "MANGA_IDLE", secondQueueMode: "UNAVAILABLE" });
    const bPort = await listenDynamic(fakeBackend.server);

    const runtime = new MangaDomainRuntime({ backendPort: bPort, workspacePort: 59990 });
    const probe = await runtime.probeBackend();

    assert.strictEqual(
        probe.classification,
        OwnershipClassification.PORT_OCCUPIED_WRONG_PROFILE,
        "Second queue unavailable must fail closed to PORT_OCCUPIED_WRONG_PROFILE"
    );
    assert.strictEqual(probe.queue, null, "Queue must be null when second queue check fails");
    assert(fakeBackend.getQueueReadCount() >= 2, "Must have performed two queue reads");

    await closeServer(fakeBackend.server);
    console.log("✓ M1D1A Check A Passed: Second queue unavailable fails closed to PORT_OCCUPIED_WRONG_PROFILE");
}

// M1D1A Check B: Second queue malformed after valid first read -> not compatible
{
    const fakeBackend = createFakeBackend({ mode: "MANGA_IDLE", secondQueueMode: "MALFORMED" });
    const bPort = await listenDynamic(fakeBackend.server);

    const runtime = new MangaDomainRuntime({ backendPort: bPort, workspacePort: 59991 });
    const probe = await runtime.probeBackend();

    assert.strictEqual(
        probe.classification,
        OwnershipClassification.PORT_OCCUPIED_WRONG_PROFILE,
        "Second queue malformed must fail closed to PORT_OCCUPIED_WRONG_PROFILE"
    );
    assert.strictEqual(probe.queue, null, "Queue must be null when second queue is malformed");

    await closeServer(fakeBackend.server);
    console.log("✓ M1D1A Check B Passed: Second queue malformed fails closed to PORT_OCCUPIED_WRONG_PROFILE");
}

// M1D1A Check C: stopBackend with stale first-idle / failed second queue -> refused, child kill count = 0
{
    const bPort = 58400 + Math.floor(Math.random() * 500);
    const wsPort = 59400 + Math.floor(Math.random() * 500);

    const fakeBackend = createFakeBackend({ mode: "MANGA_IDLE" });
    const fakeWs = createFakeWorkspace({ backendTarget: `http://127.0.0.1:${bPort}` });

    let bChild = null;
    let wsChild = null;
    let killCount = 0;

    const runtime = new MangaDomainRuntime({
        backendPort: bPort,
        workspacePort: wsPort,
        startupWaitTimeoutMs: 1500,
        customSpawnBackend: () => {
            bChild = makeFakeChild("python.exe", () => {
                killCount++;
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

    // Configure second queue mode to fail when stopBackend calls safe-stop probe
    fakeBackend.setSecondQueueMode("UNAVAILABLE");

    let stopThrew = false;
    try {
        await runtime.stopBackend();
    } catch (err) {
        stopThrew = true;
        assert(err.message.includes("positive profile identity failed") || err.message.includes("invalid") || err.message.includes("unreadable"), "Error cites failed identity probe or unreadable queue");
    }

    assert.strictEqual(stopThrew, true, "stopBackend must throw when queue recheck is unavailable");
    assert.strictEqual(killCount, 0, "Child kill count must be strictly 0");
    assert.strictEqual(bChild.killed, false, "Backend child must not be killed");

    // Clean up
    fakeBackend.setSecondQueueMode(null);
    fakeBackend.setMode("MANGA_IDLE");
    await runtime.stopBackend();
    assert.strictEqual(killCount, 1);
    await runtime.stopWorkspace();
    await closeServer(fakeBackend.server);
    await closeServer(fakeWs.server);
    console.log("✓ M1D1A Check C Passed: stopBackend refused on failed second queue, kill count = 0");
}

// M1D1A Check D: Generic { input: {} } object-info -> wrong profile
{
    const fakeBackend = createFakeBackend({ mode: "GENERIC_INPUT_NODE" });
    const bPort = await listenDynamic(fakeBackend.server);

    const runtime = new MangaDomainRuntime({ backendPort: bPort, workspacePort: 59992 });
    const probe = await runtime.probeBackend();

    assert.strictEqual(
        probe.classification,
        OwnershipClassification.PORT_OCCUPIED_WRONG_PROFILE,
        "Generic top-level input node must be rejected as PORT_OCCUPIED_WRONG_PROFILE"
    );

    await closeServer(fakeBackend.server);
    console.log("✓ M1D1A Check D Passed: Generic object-info rejected, exact node fingerprint required");
}

// M1D1A Check E: Public await runtime.restartBackend() test
{
    const bPort = 58500 + Math.floor(Math.random() * 500);
    const wsPort = 59500 + Math.floor(Math.random() * 500);

    let backendServer = createFakeBackend({ mode: "MANGA_IDLE" });
    const fakeWs = createFakeWorkspace({ backendTarget: `http://127.0.0.1:${bPort}` });

    let firstBChild = null;
    let secondBChild = null;
    let wsChild = null;
    let backendSpawnCount = 0;

    const runtime = new MangaDomainRuntime({
        backendPort: bPort,
        workspacePort: wsPort,
        startupWaitTimeoutMs: 1500,
        customSpawnBackend: () => {
            backendSpawnCount++;
            if (backendSpawnCount === 1) {
                firstBChild = makeFakeChild("python.exe", () => {
                    backendServer.server.close();
                });
                backendServer.server.listen(bPort, "127.0.0.1");
                return firstBChild;
            } else {
                backendServer = createFakeBackend({ mode: "MANGA_IDLE" });
                secondBChild = makeFakeChild("python.exe", () => {
                    backendServer.server.close();
                });
                backendServer.server.listen(bPort, "127.0.0.1");
                return secondBChild;
            }
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
    assert.strictEqual(runtime.backendProcessRecord.child, firstBChild);

    // Call the real public restartBackend() method
    await runtime.restartBackend();
    assert.strictEqual(await runtime.getStatus(), LifecycleState.READY, "Restart reaches READY");
    assert.strictEqual(firstBChild.killed, true, "First backend child terminated");
    assert.strictEqual(secondBChild.killed, false, "Second backend child active");
    assert.strictEqual(runtime.backendProcessRecord.child, secondBChild);
    assert.strictEqual(wsChild.killed, false, "Workspace child remained untouched across restart");
    assert.strictEqual(fakeWs.server.listening, true, "Workspace server still listening");

    await runtime.stopAll();
    await closeServer(backendServer.server);
    await closeServer(fakeWs.server);
    console.log("✓ M1D1A Check E Passed: Public restartBackend() stopped old child, spawned new child, preserved workspace, reached READY");
}

// M1D1A Check F: Unexpected workspace exit
{
    const bPort = 58600 + Math.floor(Math.random() * 500);
    const wsPort = 59600 + Math.floor(Math.random() * 500);

    const fakeBackend = createFakeBackend({ mode: "MANGA_IDLE" });
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

    // Simulate unexpected crash of workspace child
    await closeServer(fakeWs.server);
    wsChild.kill("SIGSEGV");
    await new Promise(r => setTimeout(r, 50));

    // Backend must remain completely untouched
    assert.strictEqual(bChild.killed, false, "Backend child must not be touched by workspace crash");
    assert.strictEqual(fakeBackend.server.listening, true, "Backend server still listening");

    // Workspace process record updated
    assert.strictEqual(runtime.workspaceProcessRecord, null, "Workspace process record cleared on exit");
    assert.strictEqual(runtime.workspaceOwnership, OwnershipClassification.UNAVAILABLE);

    // Overall status is DEGRADED
    assert.strictEqual(await runtime.getStatus(), LifecycleState.DEGRADED, "Status is DEGRADED when workspace crashes");

    // Exit diagnostics recorded truthfully
    assert.strictEqual(runtime.lastWorkspaceExit?.intentional, false, "lastWorkspaceExit recorded as unintentional");
    assert.strictEqual(runtime.lastWorkspaceExit?.signal, "SIGSEGV", "Exit signal recorded");
    assert(runtime.lastWorkspaceExit?.timestamp > 0, "Exit timestamp recorded");

    await runtime.stopBackend();
    await closeServer(fakeBackend.server);
    console.log("✓ M1D1A Check F Passed: Unexpected workspace exit leaves backend untouched, updates records, records diagnostics");
}

// M1D1A Check G: Unexpected backend exit records lastBackendExit
{
    const bPort = 58700 + Math.floor(Math.random() * 500);
    const wsPort = 59700 + Math.floor(Math.random() * 500);

    const fakeBackend = createFakeBackend({ mode: "MANGA_IDLE" });
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

    // Unexpected backend crash
    await closeServer(fakeBackend.server);
    bChild.kill("SIGTERM");
    await new Promise(r => setTimeout(r, 50));

    assert.strictEqual(runtime.lastBackendExit?.intentional, false, "Unintentional backend exit recorded");
    assert.strictEqual(runtime.lastBackendExit?.signal, "SIGTERM");
    assert(runtime.lastBackendExit?.timestamp > 0);

    await runtime.stopWorkspace();
    await closeServer(fakeWs.server);
    console.log("✓ M1D1A Check G Passed: Unexpected backend exit recorded with code/signal/timestamp/intentional");
}

// M1D1A Check H: Partial startup failure handling
// (backend spawned, then workspace encounters pre-existing wrong profile: wrong workspace is NEVER killed, owned backend is safely stopped)
{
    const bPort = 58800 + Math.floor(Math.random() * 500);

    // Pre-listen an incompatible external workspace on wsPort
    const wrongExternalWs = createFakeWorkspace({ mode: "WRONG_PROFILE" });
    const wsPort = await listenDynamic(wrongExternalWs.server);

    const fakeBackend = createFakeBackend({ mode: "MANGA_IDLE" });
    let bChild = null;

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
        }
    });

    let startThrew = false;
    try {
        await runtime.start();
    } catch (err) {
        startThrew = true;
        assert(err.message.includes("incompatible profile"));
    }

    assert.strictEqual(startThrew, true, "start() must throw when workspace has wrong profile");
    assert.strictEqual(wrongExternalWs.server.listening, true, "Wrong external workspace must NEVER be killed");
    assert.strictEqual(bChild.killed, true, "Owned backend must be safely stopped on partial startup failure");
    assert.strictEqual(runtime.backendProcessRecord, null, "Owned backend record cleared");

    await closeServer(wrongExternalWs.server);
    await closeServer(fakeBackend.server);
    console.log("✓ M1D1A Check H Passed: Partial startup failure safely stops owned backend and never touches external workspace");
}

// M1D1B Checks: Spawn Ownership Truth on Startup Failure
// Invariant: Immediately upon child handle creation, ownership is OWNED_BY_THIS_RUNTIME.
// Failure during startup polling (timeout or wrong profile) retains OWNED_BY_THIS_RUNTIME while child is alive.
// When child exits, ownership becomes UNAVAILABLE and record is null.
// Status reports FAILED while owned child remains alive without compatible service.
// No live child may ever have UNAVAILABLE ownership.

// M1D1B Check I: Backend startup timeout retains OWNED truth while child is alive
{
    const bPort = 58900 + Math.floor(Math.random() * 500);
    const wsPort = 59900 + Math.floor(Math.random() * 500);

    let bChild = null;
    const runtime = new MangaDomainRuntime({
        backendPort: bPort,
        workspacePort: wsPort,
        startupWaitTimeoutMs: 250,
        customSpawnBackend: () => {
            // Child never starts server -> timeout
            bChild = makeFakeChild("python.exe");
            return bChild;
        }
    });

    let startThrew = false;
    try {
        await runtime.start();
    } catch (err) {
        startThrew = true;
        assert(err.message.includes("Timed out waiting for backend"));
    }

    assert.strictEqual(startThrew, true, "start() must fail on backend startup timeout");
    assert.notStrictEqual(bChild, null, "Child handle must have been acquired");
    assert.strictEqual(bChild.killed, false, "Child must NOT be killed automatically by product code");
    assert.strictEqual(runtime.backendProcessRecord?.child, bChild, "backendProcessRecord must point to live child");
    assert.strictEqual(
        runtime.backendOwnership,
        OwnershipClassification.OWNED_BY_THIS_RUNTIME,
        "Ownership must remain OWNED_BY_THIS_RUNTIME even on startup timeout"
    );
    assert.notStrictEqual(
        runtime.backendOwnership,
        OwnershipClassification.UNAVAILABLE,
        "Live child must never have UNAVAILABLE ownership"
    );
    assert.strictEqual(await runtime.getStatus(), LifecycleState.FAILED, "Status must report FAILED");

    // Clean up child and verify exit transition
    bChild.kill();
    await new Promise(r => setTimeout(r, 50));
    assert.strictEqual(runtime.backendProcessRecord, null, "backendProcessRecord cleared on exit");
    assert.strictEqual(
        runtime.backendOwnership,
        OwnershipClassification.UNAVAILABLE,
        "backendOwnership becomes UNAVAILABLE after child exit"
    );

    console.log("✓ M1D1B Check I Passed: Backend startup timeout retains OWNED truth while child is alive");
}

// M1D1B Check J: Spawned backend wrong profile retains OWNED truth while child is alive
{
    const bPort = 58900 + Math.floor(Math.random() * 500);
    const wsPort = 59900 + Math.floor(Math.random() * 500);

    const wrongBackend = createFakeBackend({ mode: "WRONG_PROFILE" });
    let bChild = null;
    const runtime = new MangaDomainRuntime({
        backendPort: bPort,
        workspacePort: wsPort,
        startupWaitTimeoutMs: 1000,
        customSpawnBackend: () => {
            bChild = makeFakeChild("python.exe", () => {
                wrongBackend.server.close();
            });
            wrongBackend.server.listen(bPort, "127.0.0.1");
            return bChild;
        }
    });

    let startThrew = false;
    try {
        await runtime.start();
    } catch (err) {
        startThrew = true;
        assert(err.message.includes("Spawned backend reported wrong profile"));
    }

    assert.strictEqual(startThrew, true, "start() must fail on wrong profile backend");
    assert.notStrictEqual(bChild, null, "Child handle must have been acquired");
    assert.strictEqual(bChild.killed, false, "Child must NOT be killed automatically by product code");
    assert.strictEqual(runtime.backendProcessRecord?.child, bChild, "backendProcessRecord must point to live child");
    assert.strictEqual(
        runtime.backendOwnership,
        OwnershipClassification.OWNED_BY_THIS_RUNTIME,
        "Ownership must remain OWNED_BY_THIS_RUNTIME when spawned backend reports wrong profile"
    );
    assert.notStrictEqual(
        runtime.backendOwnership,
        OwnershipClassification.UNAVAILABLE,
        "Live child must never have UNAVAILABLE ownership"
    );
    assert.strictEqual(await runtime.getStatus(), LifecycleState.FAILED, "Status must report FAILED");

    // Clean up
    await closeServer(wrongBackend.server);
    bChild.kill();
    await new Promise(r => setTimeout(r, 50));
    assert.strictEqual(runtime.backendProcessRecord, null);
    assert.strictEqual(runtime.backendOwnership, OwnershipClassification.UNAVAILABLE);

    console.log("✓ M1D1B Check J Passed: Spawned backend wrong profile retains OWNED truth while child is alive");
}

// M1D1B Check K: Workspace startup timeout retains OWNED truth while child is alive
{
    const fakeBackend = createFakeBackend({ mode: "MANGA_IDLE" });
    const bPort = await listenDynamic(fakeBackend.server);
    const wsPort = 59900 + Math.floor(Math.random() * 500);

    let wsChild = null;
    const runtime = new MangaDomainRuntime({
        backendPort: bPort,
        workspacePort: wsPort,
        startupWaitTimeoutMs: 250,
        customSpawnWorkspace: () => {
            // Child never starts server -> timeout
            wsChild = makeFakeChild("node.exe");
            return wsChild;
        }
    });

    let startThrew = false;
    try {
        await runtime.start();
    } catch (err) {
        startThrew = true;
        assert(err.message.includes("Timed out waiting for workspace"));
    }

    assert.strictEqual(startThrew, true, "start() must fail on workspace startup timeout");
    assert.notStrictEqual(wsChild, null, "Workspace child handle must have been acquired");
    assert.strictEqual(wsChild.killed, false, "Workspace child must NOT be killed automatically");
    assert.strictEqual(runtime.workspaceProcessRecord?.child, wsChild, "workspaceProcessRecord must point to live child");
    assert.strictEqual(
        runtime.workspaceOwnership,
        OwnershipClassification.OWNED_BY_THIS_RUNTIME,
        "Ownership must remain OWNED_BY_THIS_RUNTIME even on workspace startup timeout"
    );
    assert.notStrictEqual(
        runtime.workspaceOwnership,
        OwnershipClassification.UNAVAILABLE,
        "Live child must never have UNAVAILABLE ownership"
    );
    assert.strictEqual(
        await runtime.getStatus(),
        LifecycleState.DEGRADED,
        "Status must report DEGRADED when pre-existing backend is compatible but workspace startup timed out"
    );
    assert.strictEqual(runtime.internalSubstate, InternalSubstate.FAILED);
    assert(runtime.lastError !== null);

    // Clean up
    wsChild.kill();
    await new Promise(r => setTimeout(r, 50));
    assert.strictEqual(runtime.workspaceProcessRecord, null);
    assert.strictEqual(runtime.workspaceOwnership, OwnershipClassification.UNAVAILABLE);
    await closeServer(fakeBackend.server);

    console.log("✓ M1D1B Check K Passed: Workspace startup timeout retains OWNED truth while child is alive");
}

// M1D1B Check L: Spawned Workspace wrong profile retains OWNED truth while child is alive
{
    const fakeBackend = createFakeBackend({ mode: "MANGA_IDLE" });
    const bPort = await listenDynamic(fakeBackend.server);
    const wsPort = 59900 + Math.floor(Math.random() * 500);

    const wrongWs = createFakeWorkspace({ mode: "WRONG_PROFILE" });
    let wsChild = null;
    const runtime = new MangaDomainRuntime({
        backendPort: bPort,
        workspacePort: wsPort,
        startupWaitTimeoutMs: 1000,
        customSpawnWorkspace: () => {
            wsChild = makeFakeChild("node.exe", () => {
                wrongWs.server.close();
            });
            wrongWs.server.listen(wsPort, "127.0.0.1");
            return wsChild;
        }
    });

    let startThrew = false;
    try {
        await runtime.start();
    } catch (err) {
        startThrew = true;
        assert(err.message.includes("Spawned workspace reported wrong profile"));
    }

    assert.strictEqual(startThrew, true, "start() must fail on wrong profile workspace");
    assert.notStrictEqual(wsChild, null, "Child handle must have been acquired");
    assert.strictEqual(wsChild.killed, false, "Child must NOT be killed automatically by product code");
    assert.strictEqual(runtime.workspaceProcessRecord?.child, wsChild, "workspaceProcessRecord must point to live child");
    assert.strictEqual(
        runtime.workspaceOwnership,
        OwnershipClassification.OWNED_BY_THIS_RUNTIME,
        "Ownership must remain OWNED_BY_THIS_RUNTIME when spawned workspace reports wrong profile"
    );
    assert.notStrictEqual(
        runtime.workspaceOwnership,
        OwnershipClassification.UNAVAILABLE,
        "Live child must never have UNAVAILABLE ownership"
    );
    assert.strictEqual(await runtime.getStatus(), LifecycleState.FAILED, "Status must report FAILED");

    // Clean up
    await closeServer(wrongWs.server);
    wsChild.kill();
    await new Promise(r => setTimeout(r, 50));
    assert.strictEqual(runtime.workspaceProcessRecord, null);
    assert.strictEqual(runtime.workspaceOwnership, OwnershipClassification.UNAVAILABLE);
    await closeServer(fakeBackend.server);

    console.log("✓ M1D1B Check L Passed: Spawned Workspace wrong profile retains OWNED truth while child is alive");
}

// =========================================================================
// M1D1C Checks: Preserve Owned Process Identity Across start() Re-entry
// =========================================================================

// M1D1C Check A: start() on already-owned READY runtime is idempotent
{
    const bPort = 58950 + Math.floor(Math.random() * 300);
    const wsPort = 59950 + Math.floor(Math.random() * 300);

    const fakeBackend = createFakeBackend({ mode: "MANGA_IDLE" });
    const fakeWs = createFakeWorkspace({ mode: "COMPATIBLE", backendTarget: `http://127.0.0.1:${bPort}` });

    let bSpawnCount = 0;
    let wsSpawnCount = 0;
    let bChild = null;
    let wsChild = null;

    const runtime = new MangaDomainRuntime({
        backendPort: bPort,
        workspacePort: wsPort,
        startupWaitTimeoutMs: 1500,
        customSpawnBackend: () => {
            bSpawnCount++;
            bChild = makeFakeChild("python.exe", () => {
                fakeBackend.server.close();
            });
            fakeBackend.server.listen(bPort, "127.0.0.1");
            return bChild;
        },
        customSpawnWorkspace: () => {
            wsSpawnCount++;
            wsChild = makeFakeChild("node.exe", () => {
                fakeWs.server.close();
            });
            fakeWs.server.listen(wsPort, "127.0.0.1");
            return wsChild;
        }
    });

    const status1 = await runtime.start();
    assert.strictEqual(status1, LifecycleState.READY, "First start must reach READY");
    assert.strictEqual(bSpawnCount, 1, "Backend spawned once");
    assert.strictEqual(wsSpawnCount, 1, "Workspace spawned once");
    assert.strictEqual(runtime.backendOwnership, OwnershipClassification.OWNED_BY_THIS_RUNTIME);
    assert.strictEqual(runtime.workspaceOwnership, OwnershipClassification.OWNED_BY_THIS_RUNTIME);

    const savedBChild = runtime.backendProcessRecord.child;
    const savedWsChild = runtime.workspaceProcessRecord.child;
    const savedBPid = runtime.backendProcessRecord.pid;
    const savedWsPid = runtime.workspaceProcessRecord.pid;

    // Second start() call — must be idempotent
    const status2 = await runtime.start();
    assert.strictEqual(status2, LifecycleState.READY, "Second start must return READY");
    assert.strictEqual(bSpawnCount, 1, "Zero additional backend children spawned");
    assert.strictEqual(wsSpawnCount, 1, "Zero additional workspace children spawned");
    assert.strictEqual(runtime.backendOwnership, OwnershipClassification.OWNED_BY_THIS_RUNTIME, "Backend ownership must remain OWNED");
    assert.strictEqual(runtime.workspaceOwnership, OwnershipClassification.OWNED_BY_THIS_RUNTIME, "Workspace ownership must remain OWNED");
    assert.strictEqual(runtime.backendProcessRecord.child, savedBChild, "Backend child handle unchanged");
    assert.strictEqual(runtime.workspaceProcessRecord.child, savedWsChild, "Workspace child handle unchanged");
    assert.strictEqual(runtime.backendProcessRecord.pid, savedBPid, "Backend PID unchanged");
    assert.strictEqual(runtime.workspaceProcessRecord.pid, savedWsPid, "Workspace PID unchanged");

    await runtime.stopAll();
    assert.strictEqual(bChild.killed, true);
    assert.strictEqual(wsChild.killed, true);
    await closeServer(fakeBackend.server);
    await closeServer(fakeWs.server);

    console.log("✓ M1D1C Check A Passed: start() on already-owned READY runtime is idempotent");
}

// M1D1C Check B: stopBackend() -> start() preserves Workspace handle, spawns new backend, cleans both on stopAll
{
    const bPort = 58950 + Math.floor(Math.random() * 300);
    const wsPort = 59950 + Math.floor(Math.random() * 300);

    let fakeBackend = createFakeBackend({ mode: "MANGA_IDLE" });
    const fakeWs = createFakeWorkspace({ mode: "COMPATIBLE", backendTarget: `http://127.0.0.1:${bPort}` });

    let bSpawnCount = 0;
    let wsSpawnCount = 0;
    let bChild = null;
    let wsChild = null;

    const runtime = new MangaDomainRuntime({
        backendPort: bPort,
        workspacePort: wsPort,
        startupWaitTimeoutMs: 1500,
        customSpawnBackend: () => {
            bSpawnCount++;
            bChild = makeFakeChild(`python.exe_${bSpawnCount}`, () => {
                fakeBackend.server.close();
            });
            fakeBackend.server.listen(bPort, "127.0.0.1");
            return bChild;
        },
        customSpawnWorkspace: () => {
            wsSpawnCount++;
            wsChild = makeFakeChild("node.exe", () => {
                fakeWs.server.close();
            });
            fakeWs.server.listen(wsPort, "127.0.0.1");
            return wsChild;
        }
    });

    await runtime.start();
    assert.strictEqual(bSpawnCount, 1);
    assert.strictEqual(wsSpawnCount, 1);
    const initialWsChild = runtime.workspaceProcessRecord.child;
    const initialWsPid = runtime.workspaceProcessRecord.pid;

    // Stop backend safely
    await runtime.stopBackend();
    assert.strictEqual(runtime.backendOwnership, OwnershipClassification.UNAVAILABLE);
    assert.strictEqual(runtime.backendProcessRecord, null);
    assert.strictEqual(runtime.workspaceOwnership, OwnershipClassification.OWNED_BY_THIS_RUNTIME);
    assert.strictEqual(await runtime.getStatus(), LifecycleState.DEGRADED);

    // Prepare new fake backend server for 2nd spawn
    fakeBackend = createFakeBackend({ mode: "MANGA_IDLE" });

    // Call start() again to recover backend
    const statusAfter = await runtime.start();
    assert.strictEqual(statusAfter, LifecycleState.READY);
    assert.strictEqual(bSpawnCount, 2, "Exactly one replacement backend spawned");
    assert.strictEqual(wsSpawnCount, 1, "Existing workspace child NOT respawned");
    assert.strictEqual(runtime.workspaceProcessRecord.child, initialWsChild, "Workspace child handle preserved");
    assert.strictEqual(runtime.workspaceProcessRecord.pid, initialWsPid, "Workspace PID preserved");
    assert.strictEqual(runtime.workspaceOwnership, OwnershipClassification.OWNED_BY_THIS_RUNTIME);
    assert.strictEqual(runtime.backendOwnership, OwnershipClassification.OWNED_BY_THIS_RUNTIME);

    // stopAll cleans both owned processes
    const currentBChild = runtime.backendProcessRecord.child;
    await runtime.stopAll();
    assert.strictEqual(currentBChild.killed, true);
    assert.strictEqual(initialWsChild.killed, true);
    await closeServer(fakeBackend.server);
    await closeServer(fakeWs.server);

    console.log("✓ M1D1C Check B Passed: stopBackend() -> start() preserves workspace, spawns exactly one backend, cleans both on stopAll");
}

// M1D1C Check C: stopWorkspace() -> start() preserves Backend handle, spawns new workspace, cleans both on stopAll
{
    const bPort = 58950 + Math.floor(Math.random() * 300);
    const wsPort = 59950 + Math.floor(Math.random() * 300);

    const fakeBackend = createFakeBackend({ mode: "MANGA_IDLE" });
    let fakeWs = createFakeWorkspace({ mode: "COMPATIBLE", backendTarget: `http://127.0.0.1:${bPort}` });

    let bSpawnCount = 0;
    let wsSpawnCount = 0;
    let bChild = null;
    let wsChild = null;

    const runtime = new MangaDomainRuntime({
        backendPort: bPort,
        workspacePort: wsPort,
        startupWaitTimeoutMs: 1500,
        customSpawnBackend: () => {
            bSpawnCount++;
            bChild = makeFakeChild("python.exe", () => {
                fakeBackend.server.close();
            });
            fakeBackend.server.listen(bPort, "127.0.0.1");
            return bChild;
        },
        customSpawnWorkspace: () => {
            wsSpawnCount++;
            wsChild = makeFakeChild(`node.exe_${wsSpawnCount}`, () => {
                fakeWs.server.close();
            });
            fakeWs.server.listen(wsPort, "127.0.0.1");
            return wsChild;
        }
    });

    await runtime.start();
    assert.strictEqual(bSpawnCount, 1);
    assert.strictEqual(wsSpawnCount, 1);
    const initialBChild = runtime.backendProcessRecord.child;
    const initialBPid = runtime.backendProcessRecord.pid;

    // Stop workspace
    await runtime.stopWorkspace();
    assert.strictEqual(runtime.workspaceOwnership, OwnershipClassification.UNAVAILABLE);
    assert.strictEqual(runtime.workspaceProcessRecord, null);
    assert.strictEqual(runtime.backendOwnership, OwnershipClassification.OWNED_BY_THIS_RUNTIME);
    assert.strictEqual(await runtime.getStatus(), LifecycleState.DEGRADED);

    // Prepare new fake workspace for 2nd spawn
    fakeWs = createFakeWorkspace({ mode: "COMPATIBLE", backendTarget: `http://127.0.0.1:${bPort}` });

    // Call start() again to recover workspace
    const statusAfter = await runtime.start();
    assert.strictEqual(statusAfter, LifecycleState.READY);
    assert.strictEqual(bSpawnCount, 1, "Existing backend NOT respawned");
    assert.strictEqual(wsSpawnCount, 2, "Exactly one replacement workspace spawned");
    assert.strictEqual(runtime.backendProcessRecord.child, initialBChild, "Backend child handle preserved");
    assert.strictEqual(runtime.backendProcessRecord.pid, initialBPid, "Backend PID preserved");
    assert.strictEqual(runtime.backendOwnership, OwnershipClassification.OWNED_BY_THIS_RUNTIME);
    assert.strictEqual(runtime.workspaceOwnership, OwnershipClassification.OWNED_BY_THIS_RUNTIME);

    // stopAll cleans both owned processes
    const currentWsChild = runtime.workspaceProcessRecord.child;
    await runtime.stopAll();
    assert.strictEqual(initialBChild.killed, true);
    assert.strictEqual(currentWsChild.killed, true);
    await closeServer(fakeBackend.server);
    await closeServer(fakeWs.server);

    console.log("✓ M1D1C Check C Passed: stopWorkspace() -> start() preserves backend, spawns exactly one workspace, cleans both on stopAll");
}

// M1D1C Check D: owned backend child alive + backend probe unavailable -> no second backend spawned
{
    const bPort = 58950 + Math.floor(Math.random() * 300);
    const wsPort = 59950 + Math.floor(Math.random() * 300);

    const fakeBackend = createFakeBackend({ mode: "MANGA_IDLE" });
    const fakeWs = createFakeWorkspace({ mode: "COMPATIBLE", backendTarget: `http://127.0.0.1:${bPort}` });

    let bSpawnCount = 0;
    let wsSpawnCount = 0;
    let bChild = null;
    let wsChild = null;

    const runtime = new MangaDomainRuntime({
        backendPort: bPort,
        workspacePort: wsPort,
        startupWaitTimeoutMs: 1500,
        customSpawnBackend: () => {
            bSpawnCount++;
            bChild = makeFakeChild("python.exe");
            return bChild;
        },
        customSpawnWorkspace: () => {
            wsSpawnCount++;
            wsChild = makeFakeChild("node.exe", () => {
                fakeWs.server.close();
            });
            fakeWs.server.listen(wsPort, "127.0.0.1");
            return wsChild;
        }
    });

    // Start with backend server closed (so backend probe will be UNAVAILABLE)
    let startThrew = false;
    try {
        await runtime.start();
    } catch (_) {
        startThrew = true;
    }
    assert.strictEqual(startThrew, true);
    assert.strictEqual(bSpawnCount, 1);
    assert.strictEqual(runtime.backendOwnership, OwnershipClassification.OWNED_BY_THIS_RUNTIME);
    assert.notStrictEqual(runtime.backendProcessRecord, null);

    // Second start while owned child is still alive and probe is unavailable
    let secondStartThrew = false;
    try {
        await runtime.start();
    } catch (err) {
        secondStartThrew = true;
        assert(err.message.includes("is running") && err.message.includes("UNAVAILABLE"));
    }
    assert.strictEqual(secondStartThrew, true);
    assert.strictEqual(bSpawnCount, 1, "Must NOT spawn a second backend child while owned child is alive");
    assert.strictEqual(runtime.backendOwnership, OwnershipClassification.OWNED_BY_THIS_RUNTIME);
    assert.notStrictEqual(runtime.backendProcessRecord, null);
    assert.notStrictEqual(await runtime.getStatus(), LifecycleState.READY);

    // Clean up
    bChild.kill();
    await new Promise(r => setTimeout(r, 50));
    await closeServer(fakeWs.server);
    console.log("✓ M1D1C Check D Passed: Owned backend child alive + unavailable probe -> zero duplicate spawn, ownership retained");
}

// M1D1C Check E: owned workspace child alive + workspace probe unavailable -> no second workspace spawned
{
    const bPort = 58950 + Math.floor(Math.random() * 300);
    const wsPort = 59950 + Math.floor(Math.random() * 300);

    const fakeBackend = createFakeBackend({ mode: "MANGA_IDLE" });

    let bSpawnCount = 0;
    let wsSpawnCount = 0;
    let bChild = null;
    let wsChild = null;

    const runtime = new MangaDomainRuntime({
        backendPort: bPort,
        workspacePort: wsPort,
        startupWaitTimeoutMs: 1500,
        customSpawnBackend: () => {
            bSpawnCount++;
            bChild = makeFakeChild("python.exe", () => {
                fakeBackend.server.close();
            });
            fakeBackend.server.listen(bPort, "127.0.0.1");
            return bChild;
        },
        customSpawnWorkspace: () => {
            wsSpawnCount++;
            wsChild = makeFakeChild("node.exe");
            return wsChild;
        }
    });

    let startThrew = false;
    try {
        await runtime.start();
    } catch (_) {
        startThrew = true;
    }
    assert.strictEqual(startThrew, true);
    assert.strictEqual(wsSpawnCount, 1);
    assert.strictEqual(runtime.workspaceOwnership, OwnershipClassification.OWNED_BY_THIS_RUNTIME);
    assert.notStrictEqual(runtime.workspaceProcessRecord, null);

    // Second start while owned workspace child is still alive and probe is unavailable
    let secondStartThrew = false;
    try {
        await runtime.start();
    } catch (err) {
        secondStartThrew = true;
        assert(err.message.includes("is running") && err.message.includes("UNAVAILABLE"));
    }
    assert.strictEqual(secondStartThrew, true);
    assert.strictEqual(wsSpawnCount, 1, "Must NOT spawn a second workspace child while owned child is alive");
    assert.strictEqual(runtime.workspaceOwnership, OwnershipClassification.OWNED_BY_THIS_RUNTIME);
    assert.notStrictEqual(runtime.workspaceProcessRecord, null);
    assert.notStrictEqual(await runtime.getStatus(), LifecycleState.READY);

    // Clean up
    if (bChild) bChild.kill();
    wsChild.kill();
    await new Promise(r => setTimeout(r, 50));
    await closeServer(fakeBackend.server);
    console.log("✓ M1D1C Check E Passed: Owned workspace child alive + unavailable probe -> zero duplicate spawn, ownership retained");
}

// M1D1C Check F: owned live service returning wrong profile fails closed without duplicate spawn
{
    const bPort = 58950 + Math.floor(Math.random() * 300);
    const wsPort = 59950 + Math.floor(Math.random() * 300);

    const fakeBackend = createFakeBackend({ mode: "WRONG_PROFILE" });
    let bSpawnCount = 0;
    let bChild = null;

    const runtime = new MangaDomainRuntime({
        backendPort: bPort,
        workspacePort: wsPort,
        startupWaitTimeoutMs: 1500,
        customSpawnBackend: () => {
            bSpawnCount++;
            bChild = makeFakeChild("python.exe", () => {
                fakeBackend.server.close();
            });
            fakeBackend.server.listen(bPort, "127.0.0.1");
            return bChild;
        }
    });

    let startThrew = false;
    try {
        await runtime.start();
    } catch (err) {
        startThrew = true;
        assert(err.message.includes("wrong profile"));
    }
    assert.strictEqual(startThrew, true);
    assert.strictEqual(bSpawnCount, 1);
    assert.strictEqual(runtime.backendOwnership, OwnershipClassification.OWNED_BY_THIS_RUNTIME);
    assert.notStrictEqual(runtime.backendProcessRecord, null);

    // Re-attempt start() with live owned child
    let secondStartThrew = false;
    try {
        await runtime.start();
    } catch (err) {
        secondStartThrew = true;
    }
    assert.strictEqual(secondStartThrew, true);
    assert.strictEqual(bSpawnCount, 1, "Must NOT spawn another child on wrong profile re-entry");
    assert.strictEqual(runtime.backendOwnership, OwnershipClassification.OWNED_BY_THIS_RUNTIME);

    // Clean up
    await closeServer(fakeBackend.server);
    bChild.kill();
    await new Promise(r => setTimeout(r, 50));
    console.log("✓ M1D1C Check F Passed: Owned live service returning wrong profile fails closed, zero duplicate spawn");
}

// M1D1C Check G & H: Genuine pre-existing compatible backend/Workspace remain PREEXISTING and are never killed
{
    const fakeBackend = createFakeBackend({ mode: "MANGA_IDLE" });
    const bPort = await listenDynamic(fakeBackend.server);
    const fakeWs = createFakeWorkspace({ mode: "COMPATIBLE", backendTarget: `http://127.0.0.1:${bPort}` });
    const wsPort = await listenDynamic(fakeWs.server);

    let bSpawnCount = 0;
    let wsSpawnCount = 0;

    const runtime = new MangaDomainRuntime({
        backendPort: bPort,
        workspacePort: wsPort,
        customSpawnBackend: () => { bSpawnCount++; return makeFakeChild("python.exe"); },
        customSpawnWorkspace: () => { wsSpawnCount++; return makeFakeChild("node.exe"); }
    });

    const st = await runtime.start();
    assert.strictEqual(st, LifecycleState.READY);
    assert.strictEqual(bSpawnCount, 0, "No backend spawned for pre-existing");
    assert.strictEqual(wsSpawnCount, 0, "No workspace spawned for pre-existing");
    assert.strictEqual(runtime.backendOwnership, OwnershipClassification.PREEXISTING_COMPATIBLE);
    assert.strictEqual(runtime.workspaceOwnership, OwnershipClassification.PREEXISTING_COMPATIBLE);
    assert.strictEqual(runtime.backendProcessRecord, null);
    assert.strictEqual(runtime.workspaceProcessRecord, null);

    // Calling stopAll() on runtime with pre-existing services must NOT kill them
    await runtime.stopAll();
    assert.strictEqual(fakeBackend.server.listening, true, "Pre-existing backend must NEVER be killed");
    assert.strictEqual(fakeWs.server.listening, true, "Pre-existing workspace must NEVER be killed");

    await closeServer(fakeBackend.server);
    await closeServer(fakeWs.server);
    console.log("✓ M1D1C Checks G, H Passed: Genuine pre-existing services remain PREEXISTING and are never killed");
}

// =========================================================================
// M1D1D Checks: Existing-Owned Cleanup Guard + Exit-Truth Ownership
// =========================================================================

// M1D1D Check A: child.killed == true without exit event retains owned record & ownership
{
    const bPort = 58980 + Math.floor(Math.random() * 200);
    const wsPort = 59980 + Math.floor(Math.random() * 200);

    const fakeBackend = createFakeBackend({ mode: "MANGA_IDLE" });
    const fakeWs = createFakeWorkspace({ mode: "COMPATIBLE", backendTarget: `http://127.0.0.1:${bPort}` });

    let bChild = null;
    let wsChild = null;

    const runtime = new MangaDomainRuntime({
        backendPort: bPort,
        workspacePort: wsPort,
        startupWaitTimeoutMs: 1500,
        shutdownTimeoutMs: 200,
        customSpawnBackend: () => {
            bChild = makeFakeChild("python.exe", () => {
                fakeBackend.server.close();
            }, /* stubborn */ true);
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
    assert.strictEqual(runtime.backendOwnership, OwnershipClassification.OWNED_BY_THIS_RUNTIME);
    assert.strictEqual(runtime.workspaceOwnership, OwnershipClassification.OWNED_BY_THIS_RUNTIME);

    // Explicitly send kill signal to bChild (sets bChild.killed = true, but DOES NOT emit exit because stubborn = true)
    bChild.kill("SIGTERM");
    assert.strictEqual(bChild.killed, true, "kill signal sent, killed property set");

    // The runtime bookkeeping must NOT consider this process exited!
    assert.strictEqual(
        runtime._hasOwnedBackendChild(),
        true,
        "_hasOwnedBackendChild must remain true while child has not emitted exit"
    );
    assert.strictEqual(
        runtime.backendOwnership,
        OwnershipClassification.OWNED_BY_THIS_RUNTIME,
        "Ownership must remain OWNED while child has not emitted exit"
    );
    assert.strictEqual(
        runtime.backendProcessRecord?.child,
        bChild,
        "Process record must remain intact while child has not emitted exit"
    );

    // Now emit exit and verify exit listener cleans it up
    bChild.triggerExit(0, "SIGTERM");
    await new Promise(r => setTimeout(r, 50));

    assert.strictEqual(runtime.backendProcessRecord, null, "Exit event clears processRecord");
    assert.strictEqual(runtime.backendOwnership, OwnershipClassification.UNAVAILABLE, "Exit event resets ownership to UNAVAILABLE");
    assert.strictEqual(runtime._hasOwnedBackendChild(), false, "_hasOwnedBackendChild is now false");

    await runtime.stopWorkspace();
    await closeServer(fakeBackend.server);
    await closeServer(fakeWs.server);

    console.log("✓ M1D1D Check A Passed: child.killed == true without exit event retains owned record & ownership");
}

// M1D1D Checks B & C: Backend termination timeout retains ownership & record; subsequent start() spawns 0 duplicate backend
{
    const bPort = 58980 + Math.floor(Math.random() * 200);
    const wsPort = 59980 + Math.floor(Math.random() * 200);

    const fakeBackend = createFakeBackend({ mode: "MANGA_IDLE" });
    const fakeWs = createFakeWorkspace({ mode: "COMPATIBLE", backendTarget: `http://127.0.0.1:${bPort}` });

    let bSpawnCount = 0;
    let bChild = null;
    let wsChild = null;

    const runtime = new MangaDomainRuntime({
        backendPort: bPort,
        workspacePort: wsPort,
        startupWaitTimeoutMs: 1500,
        shutdownTimeoutMs: 150, // Short shutdown timeout for deterministic test
        customSpawnBackend: () => {
            bSpawnCount++;
            bChild = makeFakeChild(`python.exe_${bSpawnCount}`, () => {
                fakeBackend.server.close();
            }, /* stubborn */ true);
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
    assert.strictEqual(bSpawnCount, 1);
    assert.strictEqual(runtime.backendOwnership, OwnershipClassification.OWNED_BY_THIS_RUNTIME);

    // Attempt stopBackend() -> SIGTERM sent, stubborn child does not exit -> throws timeout error
    let stopThrew = false;
    try {
        await runtime.stopBackend();
    } catch (err) {
        stopThrew = true;
        assert(err.message.includes("Timed out waiting for Backend child process"));
    }
    assert.strictEqual(stopThrew, true, "stopBackend() must throw when child does not exit in time");

    // Invariant: Ownership and record must be RETAINED
    assert.strictEqual(
        runtime.backendOwnership,
        OwnershipClassification.OWNED_BY_THIS_RUNTIME,
        "backendOwnership must remain OWNED_BY_THIS_RUNTIME after termination timeout"
    );
    assert.strictEqual(
        runtime.backendProcessRecord?.child,
        bChild,
        "backendProcessRecord must point to original child after termination timeout"
    );

    // Call start() after backend termination timeout
    // Invariant: Must NOT spawn a replacement/duplicate backend, must NOT downgrade to PREEXISTING
    let startThrew = false;
    try {
        await runtime.start();
    } catch (err) {
        startThrew = true;
    }
    assert.strictEqual(bSpawnCount, 1, "Must spawn ZERO duplicate backend children after termination timeout");
    assert.strictEqual(
        runtime.backendOwnership,
        OwnershipClassification.OWNED_BY_THIS_RUNTIME,
        "Ownership must not be downgraded or lost"
    );
    assert.strictEqual(
        runtime.backendProcessRecord?.child,
        bChild,
        "Process record must not be discarded"
    );

    // Trigger stubborn child exit and verify clean state
    bChild.triggerExit(0, "SIGTERM");
    await new Promise(r => setTimeout(r, 50));
    assert.strictEqual(runtime.backendProcessRecord, null);
    assert.strictEqual(runtime.backendOwnership, OwnershipClassification.UNAVAILABLE);

    await runtime.stopWorkspace();
    await closeServer(fakeBackend.server);
    await closeServer(fakeWs.server);

    console.log("✓ M1D1D Checks B, C Passed: Backend termination timeout retains ownership & record; 0 duplicate spawned on start()");
}

// M1D1D Checks D & E: Workspace termination timeout retains ownership & record; subsequent start() spawns 0 duplicate workspace
{
    const bPort = 58980 + Math.floor(Math.random() * 200);
    const wsPort = 59980 + Math.floor(Math.random() * 200);

    const fakeBackend = createFakeBackend({ mode: "MANGA_IDLE" });
    const fakeWs = createFakeWorkspace({ mode: "COMPATIBLE", backendTarget: `http://127.0.0.1:${bPort}` });

    let wsSpawnCount = 0;
    let bChild = null;
    let wsChild = null;

    const runtime = new MangaDomainRuntime({
        backendPort: bPort,
        workspacePort: wsPort,
        startupWaitTimeoutMs: 1500,
        shutdownTimeoutMs: 150,
        customSpawnBackend: () => {
            bChild = makeFakeChild("python.exe", () => {
                fakeBackend.server.close();
            });
            fakeBackend.server.listen(bPort, "127.0.0.1");
            return bChild;
        },
        customSpawnWorkspace: () => {
            wsSpawnCount++;
            wsChild = makeFakeChild(`node.exe_${wsSpawnCount}`, () => {
                fakeWs.server.close();
            }, /* stubborn */ true);
            fakeWs.server.listen(wsPort, "127.0.0.1");
            return wsChild;
        }
    });

    await runtime.start();
    assert.strictEqual(wsSpawnCount, 1);
    assert.strictEqual(runtime.workspaceOwnership, OwnershipClassification.OWNED_BY_THIS_RUNTIME);

    // Attempt stopWorkspace() -> timeout
    let stopThrew = false;
    try {
        await runtime.stopWorkspace();
    } catch (err) {
        stopThrew = true;
        assert(err.message.includes("Timed out waiting for Workspace child process"));
    }
    assert.strictEqual(stopThrew, true, "stopWorkspace() must throw on timeout");

    // Invariant: Workspace ownership and record retained
    assert.strictEqual(
        runtime.workspaceOwnership,
        OwnershipClassification.OWNED_BY_THIS_RUNTIME,
        "workspaceOwnership must remain OWNED_BY_THIS_RUNTIME after termination timeout"
    );
    assert.strictEqual(
        runtime.workspaceProcessRecord?.child,
        wsChild,
        "workspaceProcessRecord must point to original child after termination timeout"
    );

    // Call start() after workspace termination timeout
    let startThrew = false;
    try {
        await runtime.start();
    } catch (_) {
        startThrew = true;
    }
    assert.strictEqual(wsSpawnCount, 1, "Must spawn ZERO duplicate workspace children after termination timeout");
    assert.strictEqual(
        runtime.workspaceOwnership,
        OwnershipClassification.OWNED_BY_THIS_RUNTIME,
        "Workspace ownership must not be downgraded or lost"
    );
    assert.strictEqual(
        runtime.workspaceProcessRecord?.child,
        wsChild,
        "Workspace process record must not be discarded"
    );

    // Clean up
    wsChild.triggerExit(0, "SIGTERM");
    await new Promise(r => setTimeout(r, 50));
    assert.strictEqual(runtime.workspaceProcessRecord, null);
    assert.strictEqual(runtime.workspaceOwnership, OwnershipClassification.UNAVAILABLE);

    await runtime.stopBackend();
    await closeServer(fakeBackend.server);
    await closeServer(fakeWs.server);

    console.log("✓ M1D1D Checks D, E Passed: Workspace termination timeout retains ownership & record; 0 duplicate spawned on start()");
}

// M1D1D Check F: Pre-owned backend + wrong external Workspace -> existing backend NOT killed
{
    const bPort = 58980 + Math.floor(Math.random() * 200);
    const wsPort = 59980 + Math.floor(Math.random() * 200);

    const fakeBackend = createFakeBackend({ mode: "MANGA_IDLE" });
    let fakeWs = createFakeWorkspace({ mode: "COMPATIBLE", backendTarget: `http://127.0.0.1:${bPort}` });

    let bChild = null;
    let wsChild = null;
    let bSpawnCount = 0;

    const runtime = new MangaDomainRuntime({
        backendPort: bPort,
        workspacePort: wsPort,
        startupWaitTimeoutMs: 1500,
        customSpawnBackend: () => {
            bSpawnCount++;
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

    // 1. Initial start reaches READY
    await runtime.start();
    assert.strictEqual(bSpawnCount, 1);
    const initialBChild = runtime.backendProcessRecord.child;
    const initialBPid = runtime.backendProcessRecord.pid;

    // 2. Stop workspace cleanly -> backend remains OWNED and alive
    await runtime.stopWorkspace();
    assert.strictEqual(runtime.backendOwnership, OwnershipClassification.OWNED_BY_THIS_RUNTIME);
    assert.strictEqual(runtime.workspaceOwnership, OwnershipClassification.UNAVAILABLE);

    // 3. Start a wrong external service on workspace port
    const wrongExternalWs = createFakeWorkspace({ mode: "WRONG_PROFILE" });
    await new Promise(r => wrongExternalWs.server.listen(wsPort, "127.0.0.1", r));

    // 4. Call start()
    let startThrew = false;
    try {
        await runtime.start();
    } catch (err) {
        startThrew = true;
        assert(err.message.includes("incompatible profile"));
    }
    assert.strictEqual(startThrew, true, "start() must throw on wrong profile workspace");

    // Invariant: Wrong external workspace must NOT be touched/killed
    assert.strictEqual(wrongExternalWs.server.listening, true, "Wrong external workspace must NOT be killed");

    // Invariant (Defect A fix): Existing pre-owned backend must NOT be killed!
    assert.strictEqual(initialBChild.killed, false, "Pre-owned backend MUST NOT be killed when workspace fails startup");
    assert.strictEqual(runtime.backendProcessRecord?.child, initialBChild, "Backend child handle preserved");
    assert.strictEqual(runtime.backendProcessRecord?.pid, initialBPid, "Backend PID preserved");
    assert.strictEqual(runtime.backendOwnership, OwnershipClassification.OWNED_BY_THIS_RUNTIME);

    // 5. Clean up: close wrong external workspace, stop backend safely
    await closeServer(wrongExternalWs.server);
    await runtime.stopBackend();
    assert.strictEqual(initialBChild.killed, true);
    await closeServer(fakeBackend.server);

    console.log("✓ M1D1D Check F Passed: Pre-owned backend + wrong external Workspace -> existing backend NOT killed");
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

console.log("--- ALL MANGA DOMAIN LIFECYCLE TESTS (A through Y + M1D1A A-H + M1D1B I-L + M1D1C A-H + M1D1D A-F) PASSED ---");
