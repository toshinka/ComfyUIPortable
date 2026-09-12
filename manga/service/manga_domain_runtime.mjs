/**
 * manga_domain_runtime.mjs — Manga Domain Lifecycle Runtime Controller
 * ====================================================================
 * TEGAKI Manga Standalone Runtime (M1D1)
 *
 * Deterministic lifecycle controller for the standalone Manga Workspace
 * and its dedicated ComfyUI backend:
 * - Pure Node.js built-ins (zero npm dependencies).
 * - Explicit process ownership tracking (spawns child processes directly).
 * - Anti-kill-by-port strictly enforced: never kills external PIDs.
 * - Positive deterministic identity fingerprinting for backend & workspace.
 * - Fail-closed safe-stop and restart rules: refuses shutdown on busy/invalid queue.
 * - Decoupled service lifetimes: workspace lives independently from backend.
 */

import http from "node:http";
import path from "node:path";
import { spawn } from "node:child_process";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Public lifecycle states (Card Section 12)
export const LifecycleState = Object.freeze({
    STOPPED: "STOPPED",
    STARTING: "STARTING",
    READY: "READY",
    BUSY: "BUSY",
    DEGRADED: "DEGRADED",
    STOPPING: "STOPPING",
    FAILED: "FAILED"
});

// Internal substates (Card Section 13)
export const InternalSubstate = Object.freeze({
    IDLE: "IDLE",
    STARTING_BACKEND: "STARTING_BACKEND",
    BACKEND_READY: "BACKEND_READY",
    STARTING_WORKSPACE: "STARTING_WORKSPACE",
    RUNNING: "RUNNING",
    STOPPING: "STOPPING",
    FAILED: "FAILED"
});

// Process ownership classifications (Card Section 7)
export const OwnershipClassification = Object.freeze({
    OWNED_BY_THIS_RUNTIME: "OWNED_BY_THIS_RUNTIME",
    PREEXISTING_COMPATIBLE: "PREEXISTING_COMPATIBLE",
    PORT_OCCUPIED_WRONG_PROFILE: "PORT_OCCUPIED_WRONG_PROFILE",
    UNAVAILABLE: "UNAVAILABLE"
});

/**
 * Helper to perform HTTP JSON requests with timeout.
 */
function httpRequest(urlStr, options = {}, body = null) {
    return new Promise((resolve, reject) => {
        try {
            const parsed = new URL(urlStr);
            const reqOptions = {
                protocol: parsed.protocol,
                hostname: parsed.hostname,
                port: parsed.port,
                path: parsed.pathname + parsed.search,
                method: options.method || "GET",
                headers: options.headers || {},
                timeout: options.timeout || 3000
            };

            const req = http.request(reqOptions, (res) => {
                const chunks = [];
                res.on("data", (chunk) => chunks.push(chunk));
                res.on("end", () => {
                    const rawText = Buffer.concat(chunks).toString("utf-8");
                    let parsedJson = null;
                    try {
                        parsedJson = JSON.parse(rawText);
                    } catch (_) {}
                    resolve({
                        status: res.statusCode || 0,
                        headers: res.headers,
                        text: rawText,
                        json: parsedJson
                    });
                });
            });

            req.on("timeout", () => {
                req.destroy(new Error(`Request to ${urlStr} timed out after ${reqOptions.timeout}ms`));
            });

            req.on("error", (err) => {
                resolve({ status: 0, error: err.message, text: "", json: null });
            });

            if (body != null) {
                const payload = typeof body === "string" ? body : JSON.stringify(body);
                req.write(payload);
            }
            req.end();
        } catch (err) {
            resolve({ status: 0, error: err.message, text: "", json: null });
        }
    });
}

function sleep(ms) {
    return new Promise((resolve) => setTimeout(resolve, ms));
}

export class MangaDomainRuntime {
    /**
     * @param {object} [config]
     */
    constructor(config = {}) {
        // Derive root paths relative to module location / Portable root (Card Section 4, 6)
        // manga/service/ -> manga/ -> ComfyUIPortable/
        const portableRoot = config.portableRoot || path.resolve(__dirname, "..", "..");
        this.portableRoot = portableRoot;

        this.backendHost = config.backendHost || "127.0.0.1";
        this.backendPort = parseInt(config.backendPort || "8189", 10);
        this.workspaceHost = config.workspaceHost || "127.0.0.1";
        this.workspacePort = parseInt(config.workspacePort || "8191", 10);

        this.pythonExe = config.pythonExe || path.resolve(portableRoot, "python_embeded", "python.exe");
        this.comfyMain = config.comfyMain || path.resolve(portableRoot, "ComfyUI", "main.py");
        this.workspaceScript = config.workspaceScript || path.resolve(__dirname, "manga_workspace_server.mjs");

        // Custom override for spawning backend / workspace (used by fake tests)
        this.customSpawnBackend = config.customSpawnBackend || null;
        this.customSpawnWorkspace = config.customSpawnWorkspace || null;

        // Tracked service ownership
        this.backendOwnership = OwnershipClassification.UNAVAILABLE;
        this.workspaceOwnership = OwnershipClassification.UNAVAILABLE;

        // Child process records (Card Section 7)
        this.backendProcessRecord = null; // { pid, spawnTimestamp, argv, child }
        this.workspaceProcessRecord = null; // { pid, spawnTimestamp, argv, child }

        // Exit diagnostics (Card M1D1A Section 9, 10)
        this.lastBackendExit = null; // { code, signal, timestamp, intentional }
        this.lastWorkspaceExit = null; // { code, signal, timestamp, intentional }
        this._intentionalBackendStop = false;
        this._intentionalWorkspaceStop = false;

        // Internal substate
        this.internalSubstate = InternalSubstate.IDLE;
        this.lastError = null;

        // Poll timeouts (configurable, bounded)
        this.probeTimeoutMs = config.probeTimeoutMs || 800;
        this.startupWaitTimeoutMs = config.startupWaitTimeoutMs || 5000;
        this.shutdownTimeoutMs = config.shutdownTimeoutMs || 3000;
    }

    get backendUrl() {
        return `http://${this.backendHost}:${this.backendPort}`;
    }

    get workspaceUrl() {
        return `http://${this.workspaceHost}:${this.workspacePort}`;
    }

    // -------------------------------------------------------------
    // Deterministic Probes (Card Section 9, 10, 11)
    // -------------------------------------------------------------

    /**
     * Positive Backend Identity Probe:
     * Requires:
     * A. GET /queue: HTTP 200, array queue_running, array queue_pending.
     * B. GET /object_info/TegakiMinimumHandSceneEditor: HTTP 200 with object containing key.
     * C. POST /tegaki/manga/generation/prepare: HTTP 400 with { ok: false, error_code: "MISSING_DOCUMENT" }.
     * Re-read /queue to verify state unchanged.
     */
    async probeBackend() {
        const queueRes = await httpRequest(`${this.backendUrl}/queue`, { timeout: this.probeTimeoutMs });
        if (queueRes.status === 0) {
            return {
                classification: OwnershipClassification.UNAVAILABLE,
                queue: null,
                details: "Connection refused or unreachable"
            };
        }

        const isQueueValid =
            queueRes.status === 200 &&
            queueRes.json &&
            Array.isArray(queueRes.json.queue_running) &&
            Array.isArray(queueRes.json.queue_pending);

        if (!isQueueValid) {
            return {
                classification: OwnershipClassification.PORT_OCCUPIED_WRONG_PROFILE,
                queue: null,
                details: "Port occupied but /queue response invalid"
            };
        }

        // Check node object_info
        const nodeRes = await httpRequest(
            `${this.backendUrl}/object_info/TegakiMinimumHandSceneEditor`,
            { timeout: this.probeTimeoutMs }
        );
        const isNodeValid =
            nodeRes.status === 200 &&
            nodeRes.json &&
            typeof nodeRes.json === "object" &&
            Boolean(nodeRes.json.TegakiMinimumHandSceneEditor);

        if (!isNodeValid) {
            return {
                classification: OwnershipClassification.PORT_OCCUPIED_WRONG_PROFILE,
                queue: queueRes.json,
                details: "Node TegakiMinimumHandSceneEditor not found on server"
            };
        }

        // Non-mutating Capability Probe
        const prepareRes = await httpRequest(
            `${this.backendUrl}/tegaki/manga/generation/prepare`,
            {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                timeout: this.probeTimeoutMs
            },
            {}
        );

        const isPrepareValid =
            prepareRes.status === 400 &&
            prepareRes.json &&
            prepareRes.json.ok === false &&
            prepareRes.json.error_code === "MISSING_DOCUMENT";

        if (!isPrepareValid) {
            return {
                classification: OwnershipClassification.PORT_OCCUPIED_WRONG_PROFILE,
                queue: queueRes.json,
                details: "Capability probe /tegaki/manga/generation/prepare failed or returned unexpected response"
            };
        }

        // Re-read /queue: MUST fail closed if unavailable, non-200, invalid JSON, or missing arrays (no fallback to first read)
        const queueRecheck = await httpRequest(`${this.backendUrl}/queue`, { timeout: this.probeTimeoutMs });
        if (queueRecheck.status === 0) {
            return {
                classification: OwnershipClassification.PORT_OCCUPIED_WRONG_PROFILE,
                queue: null,
                details: "Second /queue read after capability probe was unavailable/unreachable"
            };
        }

        const isRecheckValid =
            queueRecheck.status === 200 &&
            queueRecheck.json &&
            Array.isArray(queueRecheck.json.queue_running) &&
            Array.isArray(queueRecheck.json.queue_pending);

        if (!isRecheckValid) {
            return {
                classification: OwnershipClassification.PORT_OCCUPIED_WRONG_PROFILE,
                queue: null,
                details: "Second /queue read after capability probe was invalid or malformed"
            };
        }

        return {
            classification: OwnershipClassification.PREEXISTING_COMPATIBLE,
            queue: queueRecheck.json,
            details: "Positive Manga backend identity verified"
        };
    }

    /**
     * Positive Workspace Identity Probe:
     * GET /api/runtime/identity
     * {
     *   service: "tegaki_manga_workspace",
     *   version: "1.0.0",
     *   domain: "manga",
     *   authoring_schema: "1.0.0",
     *   backend_target: "http://127.0.0.1:<port>"
     * }
     */
    async probeWorkspace() {
        const idRes = await httpRequest(`${this.workspaceUrl}/api/runtime/identity`, { timeout: this.probeTimeoutMs });
        if (idRes.status === 0) {
            return {
                classification: OwnershipClassification.UNAVAILABLE,
                identity: null,
                details: "Connection refused or unreachable"
            };
        }

        if (
            idRes.status === 200 &&
            idRes.json &&
            idRes.json.service === "tegaki_manga_workspace" &&
            idRes.json.domain === "manga" &&
            idRes.json.authoring_schema === "1.0.0" &&
            idRes.json.backend_target === this.backendUrl
        ) {
            return {
                classification: OwnershipClassification.PREEXISTING_COMPATIBLE,
                identity: idRes.json,
                details: "Positive Manga workspace identity verified"
            };
        }

        return {
            classification: OwnershipClassification.PORT_OCCUPIED_WRONG_PROFILE,
            identity: idRes.json,
            details: "Port occupied but /api/runtime/identity does not match expected Manga workspace signature"
        };
    }

    // -------------------------------------------------------------
    // Public Status & Mapping (Card Section 12, 13)
    // -------------------------------------------------------------

    /**
     * Returns the externally visible public status truthfully mapped to:
     * STOPPED | STARTING | READY | BUSY | DEGRADED | STOPPING | FAILED
     */
    async getStatus() {
        if (this.internalSubstate === InternalSubstate.STOPPING) {
            return LifecycleState.STOPPING;
        }
        if (this.internalSubstate === InternalSubstate.STARTING_BACKEND ||
            this.internalSubstate === InternalSubstate.STARTING_WORKSPACE) {
            return LifecycleState.STARTING;
        }

        const [backendProbe, workspaceProbe] = await Promise.all([
            this.probeBackend(),
            this.probeWorkspace()
        ]);

        const isBackendCompatible =
            backendProbe.classification === OwnershipClassification.PREEXISTING_COMPATIBLE;
        const isWorkspaceCompatible =
            workspaceProbe.classification === OwnershipClassification.PREEXISTING_COMPATIBLE;

        // If nothing is running and no owned processes exist
        if (!isBackendCompatible && !isWorkspaceCompatible &&
            !this.backendProcessRecord && !this.workspaceProcessRecord &&
            this.internalSubstate === InternalSubstate.IDLE) {
            return LifecycleState.STOPPED;
        }

        // Workspace compatible: evaluate backend health
        if (isWorkspaceCompatible) {
            if (isBackendCompatible) {
                const q = backendProbe.queue;
                if (q && Array.isArray(q.queue_running) && Array.isArray(q.queue_pending)) {
                    if (q.queue_running.length > 0 || q.queue_pending.length > 0) {
                        return LifecycleState.BUSY;
                    }
                    return LifecycleState.READY;
                }
                // Invalid queue cannot be READY
                return LifecycleState.DEGRADED;
            }

            // Workspace is alive/compatible but backend is unavailable or invalid profile
            return LifecycleState.DEGRADED;
        }

        // If wrong profile is detected on either port during running state without compatible workspace
        if (backendProbe.classification === OwnershipClassification.PORT_OCCUPIED_WRONG_PROFILE ||
            workspaceProbe.classification === OwnershipClassification.PORT_OCCUPIED_WRONG_PROFILE) {
            return LifecycleState.FAILED;
        }

        // Backend compatible but workspace down
        if (isBackendCompatible && !isWorkspaceCompatible) {
            return LifecycleState.DEGRADED;
        }

        // Both down but we have records or substate not idle
        if (this.lastError) {
            return LifecycleState.FAILED;
        }

        return LifecycleState.STOPPED;
    }

    _hasOwnedBackendChild() {
        return (
            this.backendOwnership === OwnershipClassification.OWNED_BY_THIS_RUNTIME &&
            this.backendProcessRecord != null &&
            this.backendProcessRecord.child != null
        );
    }

    _hasOwnedWorkspaceChild() {
        return (
            this.workspaceOwnership === OwnershipClassification.OWNED_BY_THIS_RUNTIME &&
            this.workspaceProcessRecord != null &&
            this.workspaceProcessRecord.child != null
        );
    }

    // -------------------------------------------------------------
    // Startup Sequence (Card Section 14, 15, 16)
    // -------------------------------------------------------------

    async start() {
        this.lastError = null;
        this.internalSubstate = InternalSubstate.STARTING_BACKEND;
        let spawnedBackendThisStart = false;

        try {
            // 1. Establish backend classification / start
            const backendInitial = await this.probeBackend();
            const hasOwnedBackend = this._hasOwnedBackendChild();

            if (backendInitial.classification === OwnershipClassification.PORT_OCCUPIED_WRONG_PROFILE) {
                this.internalSubstate = InternalSubstate.FAILED;
                this.lastError = new Error(`Backend port ${this.backendPort} occupied by incompatible profile: ${backendInitial.details}`);
                throw this.lastError;
            } else if (backendInitial.classification === OwnershipClassification.PREEXISTING_COMPATIBLE) {
                if (!hasOwnedBackend) {
                    this.backendOwnership = OwnershipClassification.PREEXISTING_COMPATIBLE;
                    this.backendProcessRecord = null;
                }
                // If hasOwnedBackend, preserve OWNED_BY_THIS_RUNTIME and backendProcessRecord
            } else {
                // Backend is UNAVAILABLE
                if (hasOwnedBackend) {
                    // Retain owned child record and ownership; do NOT spawn a duplicate backend child
                    this.internalSubstate = InternalSubstate.FAILED;
                    this.lastError = new Error(`Owned backend child is running (PID ${this.backendProcessRecord.pid}) but probe returned UNAVAILABLE`);
                    throw this.lastError;
                }
                // UNAVAILABLE and not owned -> spawn candidate backend child
                await this._spawnBackendChild();
                spawnedBackendThisStart = true;
            }

            this.internalSubstate = InternalSubstate.STARTING_WORKSPACE;

            // 2. Establish workspace classification / start
            const wsInitial = await this.probeWorkspace();
            const hasOwnedWs = this._hasOwnedWorkspaceChild();

            if (wsInitial.classification === OwnershipClassification.PORT_OCCUPIED_WRONG_PROFILE) {
                this.internalSubstate = InternalSubstate.FAILED;
                this.lastError = new Error(`Workspace port ${this.workspacePort} occupied by incompatible profile: ${wsInitial.details}`);

                // M1D1D: Only attempt safe stop if backend was newly spawned by THIS start() invocation.
                // Pre-existing owned backend MUST be preserved.
                if (spawnedBackendThisStart && this.backendOwnership === OwnershipClassification.OWNED_BY_THIS_RUNTIME) {
                    try {
                        await this.stopBackend();
                    } catch (_) {
                        // Retain explicit owned-process record and FAILED state; do not force kill
                    }
                }
                throw this.lastError;
            } else if (wsInitial.classification === OwnershipClassification.PREEXISTING_COMPATIBLE) {
                if (!hasOwnedWs) {
                    this.workspaceOwnership = OwnershipClassification.PREEXISTING_COMPATIBLE;
                    this.workspaceProcessRecord = null;
                }
                // If hasOwnedWs, preserve OWNED_BY_THIS_RUNTIME and workspaceProcessRecord
            } else {
                // Workspace is UNAVAILABLE
                if (hasOwnedWs) {
                    // Retain owned child record and ownership; do NOT spawn a duplicate workspace child
                    this.internalSubstate = InternalSubstate.FAILED;
                    this.lastError = new Error(`Owned workspace child is running (PID ${this.workspaceProcessRecord.pid}) but probe returned UNAVAILABLE`);
                    throw this.lastError;
                }
                // UNAVAILABLE and not owned -> spawn candidate workspace child
                try {
                    await this._spawnWorkspaceChild();
                } catch (err) {
                    this.internalSubstate = InternalSubstate.FAILED;
                    this.lastError = err;
                    if (spawnedBackendThisStart && this.backendOwnership === OwnershipClassification.OWNED_BY_THIS_RUNTIME) {
                        try {
                            await this.stopBackend();
                        } catch (_) {}
                    }
                    throw err;
                }
            }

            this.internalSubstate = InternalSubstate.RUNNING;
            return this.getStatus();
        } catch (err) {
            this.internalSubstate = InternalSubstate.FAILED;
            this.lastError = err;
            throw err;
        }
    }

    async _spawnBackendChild() {
        const argv = [
            "-s",
            this.comfyMain,
            "--listen", this.backendHost,
            "--port", String(this.backendPort),
            "--disable-auto-launch",
            "--output-directory", "output/Tegaki"
        ];

        let child;
        if (this.customSpawnBackend) {
            child = this.customSpawnBackend({
                command: this.pythonExe,
                args: argv,
                cwd: this.portableRoot
            });
        } else {
            child = spawn(this.pythonExe, argv, {
                cwd: this.portableRoot,
                stdio: ["ignore", "pipe", "pipe"],
                windowsHide: true
            });
        }

        const record = {
            pid: child.pid,
            spawnTimestamp: Date.now(),
            argv: [this.pythonExe, ...argv],
            child
        };
        this.backendProcessRecord = record;
        this.backendOwnership = OwnershipClassification.OWNED_BY_THIS_RUNTIME;

        child.on("exit", (code, signal) => {
            this.lastBackendExit = {
                code: code ?? null,
                signal: signal ?? null,
                timestamp: Date.now(),
                intentional: this._intentionalBackendStop
            };

            if (this.backendProcessRecord?.child === child) {
                this.backendProcessRecord = null;
                this.backendOwnership = OwnershipClassification.UNAVAILABLE;
            }
        });

        // Bound poll for positive identity
        const start = Date.now();
        while (Date.now() - start < this.startupWaitTimeoutMs) {
            const probe = await this.probeBackend();
            if (probe.classification === OwnershipClassification.PREEXISTING_COMPATIBLE) {
                return;
            }
            if (probe.classification === OwnershipClassification.PORT_OCCUPIED_WRONG_PROFILE) {
                throw new Error(`Spawned backend reported wrong profile: ${probe.details}`);
            }
            await sleep(100);
        }

        throw new Error(`Timed out waiting for backend on ${this.backendUrl} to report positive identity`);
    }

    async _spawnWorkspaceChild() {
        const argv = [this.workspaceScript];
        const env = {
            ...process.env,
            MANGA_WORKSPACE_PORT: String(this.workspacePort),
            MANGA_BACKEND_URL: this.backendUrl
        };

        let child;
        if (this.customSpawnWorkspace) {
            child = this.customSpawnWorkspace({
                command: process.execPath,
                args: argv,
                env,
                cwd: this.portableRoot
            });
        } else {
            child = spawn(process.execPath, argv, {
                cwd: this.portableRoot,
                env,
                stdio: ["ignore", "pipe", "pipe"],
                windowsHide: true
            });
        }

        const record = {
            pid: child.pid,
            spawnTimestamp: Date.now(),
            argv: [process.execPath, ...argv],
            child
        };
        this.workspaceProcessRecord = record;
        this.workspaceOwnership = OwnershipClassification.OWNED_BY_THIS_RUNTIME;

        child.on("exit", (code, signal) => {
            this.lastWorkspaceExit = {
                code: code ?? null,
                signal: signal ?? null,
                timestamp: Date.now(),
                intentional: this._intentionalWorkspaceStop
            };

            if (this.workspaceProcessRecord?.child === child) {
                this.workspaceProcessRecord = null;
                this.workspaceOwnership = OwnershipClassification.UNAVAILABLE;
            }
        });

        // Bound poll for positive identity
        const start = Date.now();
        while (Date.now() - start < this.startupWaitTimeoutMs) {
            const probe = await this.probeWorkspace();
            if (probe.classification === OwnershipClassification.PREEXISTING_COMPATIBLE) {
                return;
            }
            if (probe.classification === OwnershipClassification.PORT_OCCUPIED_WRONG_PROFILE) {
                throw new Error(`Spawned workspace reported wrong profile: ${probe.details}`);
            }
            await sleep(100);
        }

        throw new Error(`Timed out waiting for workspace on ${this.workspaceUrl} to report positive identity`);
    }

    // -------------------------------------------------------------
    // Safe Backend Stop & Restart (Card Section 17, 21, 22)
    // -------------------------------------------------------------

    /**
     * Strictly fail-closed safe stop for backend:
     * Allowed only when:
     * - ownership == OWNED_BY_THIS_RUNTIME
     * - backend positive identity passes
     * - GET /queue valid, queue_running == [], queue_pending == []
     *
     * Refuses stop for PREEXISTING_COMPATIBLE, busy queue, or invalid queue.
     * NO FORCE FLAG.
     */
    async stopBackend() {
        if (this.backendOwnership !== OwnershipClassification.OWNED_BY_THIS_RUNTIME || !this.backendProcessRecord) {
            throw new Error("Cannot stop backend: process is not OWNED_BY_THIS_RUNTIME (pre-existing or not managed).");
        }

        const probe = await this.probeBackend();
        if (probe.classification !== OwnershipClassification.PREEXISTING_COMPATIBLE) {
            throw new Error(`Cannot stop backend: positive profile identity failed (${probe.details}).`);
        }

        const q = probe.queue;
        if (!q || !Array.isArray(q.queue_running) || !Array.isArray(q.queue_pending)) {
            throw new Error("Cannot stop backend: /queue data is invalid or unreadable.");
        }

        if (q.queue_running.length > 0 || q.queue_pending.length > 0) {
            throw new Error(`Cannot stop backend: queue is busy (running: ${q.queue_running.length}, pending: ${q.queue_pending.length}).`);
        }

        // Preconditions satisfied: terminate owned ChildProcess handle
        this._intentionalBackendStop = true;
        try {
            await this._terminateChild(this.backendProcessRecord.child, "Backend");
        } finally {
            this._intentionalBackendStop = false;
        }
        this.backendProcessRecord = null;
        this.backendOwnership = OwnershipClassification.UNAVAILABLE;
    }

    /**
     * Restarts owned backend:
     * Allowed only for OWNED backend. Must pass safe-stop rule, terminate child, and start again.
     */
    async restartBackend() {
        if (this.backendOwnership !== OwnershipClassification.OWNED_BY_THIS_RUNTIME) {
            throw new Error("Cannot restart backend: only OWNED_BY_THIS_RUNTIME backend can be restarted.");
        }

        await this.stopBackend();
        await this._spawnBackendChild();
    }

    // -------------------------------------------------------------
    // Safe Workspace Stop & Stop All (Card Section 19, 20)
    // -------------------------------------------------------------

    async stopWorkspace() {
        if (this.workspaceOwnership !== OwnershipClassification.OWNED_BY_THIS_RUNTIME || !this.workspaceProcessRecord) {
            throw new Error("Cannot stop workspace: process is not OWNED_BY_THIS_RUNTIME (pre-existing or not managed).");
        }

        this._intentionalWorkspaceStop = true;
        try {
            await this._terminateChild(this.workspaceProcessRecord.child, "Workspace");
        } finally {
            this._intentionalWorkspaceStop = false;
        }
        this.workspaceProcessRecord = null;
        this.workspaceOwnership = OwnershipClassification.UNAVAILABLE;
    }

    /**
     * Stop all managed processes safely.
     * If an owned backend cannot pass safe-stop (e.g. busy), REFUSES full shutdown to avoid orphaning.
     */
    async stopAll() {
        this.internalSubstate = InternalSubstate.STOPPING;

        try {
            if (this.backendOwnership === OwnershipClassification.OWNED_BY_THIS_RUNTIME) {
                // Must pass safe stop first!
                await this.stopBackend();
            }

            if (this.workspaceOwnership === OwnershipClassification.OWNED_BY_THIS_RUNTIME) {
                await this.stopWorkspace();
            }

            this.internalSubstate = InternalSubstate.IDLE;
        } catch (err) {
            this.internalSubstate = InternalSubstate.FAILED;
            this.lastError = err;
            throw err;
        }
    }

    /**
     * Terminates a ChildProcess handle without killing discovered external PIDs.
     */
    async _terminateChild(child, serviceName) {
        if (!child || child.killed) return;

        return new Promise((resolve, reject) => {
            let exited = false;
            const timeoutTimer = setTimeout(() => {
                if (!exited) {
                    reject(new Error(`Timed out waiting for ${serviceName} child process (PID ${child.pid}) to exit.`));
                }
            }, this.shutdownTimeoutMs);

            child.once("exit", () => {
                exited = true;
                clearTimeout(timeoutTimer);
                resolve();
            });

            try {
                child.kill("SIGTERM");
            } catch (err) {
                clearTimeout(timeoutTimer);
                reject(err);
            }
        });
    }
}
