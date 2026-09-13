/**
 * TEGAKI owner shell supervisor.
 *
 * This is deliberately a bounded coordinator, not a second domain runtime:
 * H3 child processes are owned here, while Manga backend/workspace ownership
 * remains in MangaDomainRuntime.
 */
import http from "node:http";
import net from "node:net";
import path from "node:path";
import { accessSync, constants as fsConstants } from "node:fs";
import { spawn as nodeSpawn } from "node:child_process";
import { createInterface } from "node:readline";
import { fileURLToPath } from "node:url";
import { MangaDomainRuntime, OwnershipClassification } from "../../manga/service/manga_domain_runtime.mjs";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const DEFAULTS = Object.freeze({
    h3BackendPort: 8188,
    mangaBackendPort: 8189,
    h3SkinPort: 8190,
    mangaWorkspacePort: 8191,
    host: "127.0.0.1",
    startupTimeoutMs: 120000,
    probeTimeoutMs: 1000,
    noBrowser: false,
});

function numberFromEnv(value, fallback) {
    const parsed = Number.parseInt(value || "", 10);
    return Number.isInteger(parsed) && parsed > 0 && parsed < 65536 ? parsed : fallback;
}

export function readShellConfig(env = process.env) {
    return {
        h3BackendPort: numberFromEnv(env.TEGAKI_H3_NATIVE_PORT, DEFAULTS.h3BackendPort),
        mangaBackendPort: numberFromEnv(env.TEGAKI_MANGA_BACKEND_PORT, DEFAULTS.mangaBackendPort),
        h3SkinPort: numberFromEnv(env.TEGAKI_H3_SKIN_PORT, DEFAULTS.h3SkinPort),
        mangaWorkspacePort: numberFromEnv(env.TEGAKI_MANGA_WORKSPACE_PORT, DEFAULTS.mangaWorkspacePort),
        host: DEFAULTS.host,
        startupTimeoutMs: numberFromEnv(env.TEGAKI_SHELL_STARTUP_TIMEOUT_MS, DEFAULTS.startupTimeoutMs),
        probeTimeoutMs: numberFromEnv(env.TEGAKI_SHELL_PROBE_TIMEOUT_MS, DEFAULTS.probeTimeoutMs),
        noBrowser: env.TEGAKI_H3_NO_BROWSER === "1",
    };
}

/** Return `free` only for a positively refused loopback connection. */
export function inspectPort(port, host = DEFAULTS.host, timeoutMs = 500) {
    return new Promise((resolve) => {
        const socket = net.createConnection({ host, port });
        let settled = false;
        const finish = (state, detail = "") => {
            if (settled) return;
            settled = true;
            socket.destroy();
            resolve({ port, host, state, detail });
        };
        socket.setTimeout(timeoutMs, () => finish("occupied", "connection timed out"));
        socket.once("connect", () => finish("occupied", "a listener accepted the connection"));
        socket.once("error", (error) => {
            if (["ECONNREFUSED", "EHOSTUNREACH", "ENETUNREACH"].includes(error.code)) {
                finish("free", error.code);
            } else {
                finish("occupied", error.code || error.message);
            }
        });
    });
}

function request(urlString, timeoutMs = 1000) {
    return new Promise((resolve) => {
        let parsed;
        try { parsed = new URL(urlString); } catch (error) {
            resolve({ status: 0, json: null, text: "", error });
            return;
        }
        const req = http.request({
            hostname: parsed.hostname,
            port: parsed.port,
            path: `${parsed.pathname}${parsed.search}`,
            method: "GET",
            timeout: timeoutMs,
            headers: { Accept: "application/json" },
        }, (res) => {
            const chunks = [];
            res.on("data", chunk => chunks.push(chunk));
            res.on("end", () => {
                const text = Buffer.concat(chunks).toString("utf8");
                let json = null;
                try { json = JSON.parse(text); } catch (_) { /* identity probes reject malformed JSON */ }
                resolve({ status: res.statusCode || 0, json, text, error: null });
            });
        });
        req.once("timeout", () => req.destroy(new Error("request timeout")));
        req.once("error", error => resolve({ status: 0, json: null, text: "", error }));
        req.end();
    });
}

export async function waitForHttp(urlString, predicate, {
    timeoutMs = DEFAULTS.startupTimeoutMs,
    intervalMs = 150,
    probeTimeoutMs = DEFAULTS.probeTimeoutMs,
} = {}) {
    const started = Date.now();
    let last = { status: 0, json: null, text: "", error: new Error("not probed") };
    while (Date.now() - started < timeoutMs) {
        last = await request(urlString, probeTimeoutMs);
        if (predicate(last)) return last;
        await new Promise(resolve => setTimeout(resolve, intervalMs));
    }
    const detail = last.error?.message || `HTTP ${last.status}`;
    throw new Error(`Timed out waiting for ${urlString} (${detail})`);
}

function expectedH3Config(config) {
    return {
        ...config,
        h3BackendUrl: `http://${config.host}:${config.h3BackendPort}`,
        h3ShellUrl: `http://${config.host}:${config.h3SkinPort}/`,
        mangaBackendUrl: `http://${config.host}:${config.mangaBackendPort}`,
        mangaWorkspaceUrl: `http://${config.host}:${config.mangaWorkspacePort}/`,
    };
}

export function formatOccupiedPort(result) {
    return `Port ${result.port} on ${result.host} is occupied (${result.detail}). `
        + `No process was adopted or killed; inspect the owning PID for this port, then retry.`;
}

function verifyExecutable(file, label) {
    try { accessSync(file, fsConstants.F_OK); }
    catch { throw new Error(`${label} is missing: ${file}`); }
}

export class TegakiShellSupervisor {
    constructor(options = {}) {
        this.portableRoot = path.resolve(options.portableRoot || path.resolve(__dirname, "..", ".."));
        this.config = expectedH3Config({ ...readShellConfig(process.env), ...(options.config || {}) });
        this.spawn = options.spawn || nodeSpawn;
        this.portInspector = options.portInspector || inspectPort;
        this.runtimeFactory = options.runtimeFactory || ((runtimeConfig) => new MangaDomainRuntime(runtimeConfig));
        this.browserLauncher = options.browserLauncher || openDefaultBrowser;
        this.waitFor = options.waitFor || waitForHttp;
        this.log = options.log || ((message) => console.log(message));
        this.error = options.error || ((message) => console.error(message));
        this.h3Processes = [];
        this.mangaRuntime = null;
        this.started = false;
        this.shutdownInFlight = null;
    }

    get pythonExe() { return path.resolve(this.portableRoot, "python_embeded", "python.exe"); }
    get modelPathsConfig() {
        const local = path.resolve(this.portableRoot, "h3", "config", "extra_model_paths.local.yaml");
        return requireFile(local) ? local : path.resolve(this.portableRoot, "h3", "config", "extra_model_paths.yaml");
    }

    async checkRequiredPorts() {
        const ports = [
            ["H3 Native backend", this.config.h3BackendPort],
            ["H3 shell", this.config.h3SkinPort],
        ];
        for (const [label, port] of ports) {
            const result = await this.portInspector(port, this.config.host, this.config.probeTimeoutMs);
            if (result.state !== "free") throw new Error(`${label}: ${formatOccupiedPort(result)}`);
        }
    }

    spawnOwned(label, command, args, { cwd = this.portableRoot, env = process.env } = {}) {
        const child = this.spawn(command, args, {
            cwd,
            env,
            stdio: ["ignore", "pipe", "pipe"],
            windowsHide: true,
        });
        const record = { label, command, args: [...args], child, pid: child.pid ?? null };
        this.h3Processes.push(record);
        this.log(`${label}: OWNED_BY_THIS_RUNTIME (PID ${record.pid ?? "unknown"})`);
        const forward = (stream, kind) => stream?.on?.("data", chunk => process.stdout.write(`[${label} ${kind}] ${chunk}`));
        forward(child.stdout, "stdout");
        child.stderr?.on?.("data", chunk => process.stderr.write(`[${label} stderr] ${chunk}`));
        child.once?.("error", error => this.error(`${label} startup error: ${error.message}`));
        child.once?.("exit", (code, signal) => {
            record.exit = { code: code ?? null, signal: signal ?? null, timestamp: Date.now() };
            this.log(`${label} exited (code=${record.exit.code}, signal=${record.exit.signal}).`);
        });
        return child;
    }

    async startH3Processes() {
        verifyExecutable(this.pythonExe, "Portable Python");
        const h3NativeMain = path.resolve(this.portableRoot, "h3", "tools", "run_native_isolated.py");
        const h3Skin = path.resolve(this.portableRoot, "h3", "app", "server.py");
        verifyExecutable(h3NativeMain, "H3 Native launcher");
        verifyExecutable(h3Skin, "H3 shell server");
        const outputRoot = path.resolve(this.portableRoot, "output", "h3");
        const nativeArgs = [
            h3NativeMain,
            "--listen", this.config.host,
            "--port", String(this.config.h3BackendPort),
            "--disable-auto-launch", "--disable-manager", "--disable-all-custom-nodes",
            "--extra-model-paths-config", this.modelPathsConfig,
            "--output-directory", outputRoot,
            "--input-directory", outputRoot,
            "--user-directory", path.resolve(outputRoot, "h3_native_user"),
            "--temp-directory", path.resolve(outputRoot, "h3_native_temp"),
            "--database-url", "sqlite:///:memory:", "--log-stdout",
        ];
        this.log(`Starting H3 Native backend: ${this.config.h3BackendUrl}/`);
        this.spawnOwned("H3 Native backend", this.pythonExe, nativeArgs);
        await this.waitFor(`${this.config.h3BackendUrl}/queue`, response => (
            response.status === 200 && response.json
            && Array.isArray(response.json.queue_running)
            && Array.isArray(response.json.queue_pending)
        ), { timeoutMs: this.config.startupTimeoutMs, probeTimeoutMs: this.config.probeTimeoutMs });

        const skinArgs = [
            h3Skin,
            "--host", this.config.host,
            "--port", String(this.config.h3SkinPort),
            "--comfy-url", this.config.h3BackendUrl,
            "--output-dir", "output/h3",
            "--manga-workspace-url", this.config.mangaWorkspaceUrl,
        ];
        this.log(`Starting H3 shell: ${this.config.h3ShellUrl}`);
        this.spawnOwned("H3 shell", this.pythonExe, skinArgs);
        await this.waitFor(`${this.config.h3ShellUrl}api/config`, response => (
            response.status === 200 && response.json && typeof response.json === "object"
            && response.json.playable && response.json.still && response.json.prep
        ), { timeoutMs: this.config.startupTimeoutMs, probeTimeoutMs: this.config.probeTimeoutMs });
        await this.waitFor(`${this.config.h3ShellUrl}api/status`, response => (
            response.status === 200 && response.json?.state === "READY"
        ), { timeoutMs: this.config.startupTimeoutMs, probeTimeoutMs: this.config.probeTimeoutMs });
    }

    async startMangaRuntime() {
        const diagnosticSpawn = (spec) => this.spawnOwned(
            spec.command === process.execPath ? "Manga workspace" : "Manga backend",
            spec.command,
            spec.args,
            { cwd: spec.cwd || this.portableRoot, env: { ...process.env, ...(spec.env || {}) } },
        );
        this.mangaRuntime = this.runtimeFactory({
            portableRoot: this.portableRoot,
            backendHost: this.config.host,
            backendPort: this.config.mangaBackendPort,
            workspaceHost: this.config.host,
            workspacePort: this.config.mangaWorkspacePort,
            customSpawnBackend: diagnosticSpawn,
            customSpawnWorkspace: diagnosticSpawn,
        });
        this.log(`Starting/reusing Manga services: ${this.config.mangaBackendUrl}/ and ${this.config.mangaWorkspaceUrl}`);
        const state = await this.mangaRuntime.start();
        const workspace = await this.mangaRuntime.probeWorkspace();
        if (workspace.classification !== OwnershipClassification.PREEXISTING_COMPATIBLE) {
            throw new Error(`Manga workspace identity invalid: ${workspace.details}`);
        }
        if (!["READY", "BUSY"].includes(state)) throw new Error(`Manga runtime state: ${state}`);
        this.log(`Manga state: ${state}`);
        this.log(`Manga backend ownership: ${this.mangaRuntime.backendOwnership}`);
        this.log(`Manga workspace ownership: ${this.mangaRuntime.workspaceOwnership}`);
    }

    async start() {
        if (this.started) return this;
        this.log("TEGAKI MANGA");
        this.log(`Portable root: ${this.portableRoot}`);
        this.log(`H3 backend: ${this.config.h3BackendUrl}/`);
        this.log(`H3 shell: ${this.config.h3ShellUrl}`);
        this.log(`Manga backend: ${this.config.mangaBackendUrl}/`);
        this.log(`Manga workspace: ${this.config.mangaWorkspaceUrl}`);
        this.log("State: STARTING");
        try {
            await this.checkRequiredPorts();
            await this.startH3Processes();
            await this.startMangaRuntime();
            this.started = true;
            this.log("State: READY");
            this.log(`Browser: ${this.config.h3ShellUrl}`);
            if (this.config.noBrowser) {
                this.log("Browser: launch suppressed by TEGAKI_H3_NO_BROWSER=1.");
            } else {
                try { await this.browserLauncher(this.config.h3ShellUrl); }
                catch (error) { this.log(`Browser launch failed: ${error.message}. Open ${this.config.h3ShellUrl} manually.`); }
            }
            return this;
        } catch (error) {
            this.error(`State: FAILED — ${error.message}`);
            // Startup owns no user jobs yet. Known child handles may be
            // terminated with the same SIGTERM-and-exit wait, even when the
            // H3 status endpoint never became available.
            await this.shutdown({ reportErrors: false, startupFailure: true });
            throw error;
        }
    }

    async h3SafeToStop() {
        const response = await request(`${this.config.h3ShellUrl}api/status`, this.config.probeTimeoutMs);
        return response.status === 200 && response.json?.lifecycle?.safe_to_stop_native === true;
    }

    async terminateChild(record) {
        const child = record?.child;
        if (!child || record.exit) return;
        await new Promise((resolve, reject) => {
            let done = false;
            const finish = (error) => { if (done) return; done = true; clearTimeout(timer); child.removeListener?.("exit", onExit); error ? reject(error) : resolve(); };
            const onExit = (code, signal) => { record.exit = { code: code ?? null, signal: signal ?? null, timestamp: Date.now() }; finish(); };
            const timer = setTimeout(() => finish(new Error(`${record.label} did not confirm exit before timeout`)), 5000);
            child.once?.("exit", onExit);
            try { if (!child.killed) child.kill("SIGTERM"); else if (child.exitCode != null) onExit(child.exitCode, child.signalCode); }
            catch (error) { finish(error); }
        });
    }

    async shutdown({ reportErrors = true, startupFailure = false } = {}) {
        if (this.shutdownInFlight) return this.shutdownInFlight;
        this.shutdownInFlight = (async () => {
            let failed = false;
            if (this.mangaRuntime) {
                try {
                    await this.mangaRuntime.stopAll();
                    this.log("Manga owned-process shutdown confirmed by MangaDomainRuntime.");
                } catch (error) {
                    failed = true;
                    this.log(`Manga safe stop refused/failed: ${error.message}. No force kill; pre-existing services remain untouched.`);
                }
            }
            if (this.h3Processes.length) {
                let safe = startupFailure;
                try { if (!safe) safe = await this.h3SafeToStop(); } catch (_) { safe = false; }
                if (!safe) {
                    failed = true;
                    this.log("H3 safe stop refused: canonical idle status was not positively verified. No force kill.");
                } else {
                    for (const record of [...this.h3Processes].reverse()) {
                        try { await this.terminateChild(record); }
                        catch (error) { failed = true; this.log(`${record.label} shutdown failed: ${error.message}`); }
                    }
                }
            }
            if (reportErrors && failed) this.log("State: DEGRADED — retry Enter or Ctrl+C after active work is idle.");
            if (!failed) this.log("State: STOPPED — all owned processes confirmed exited; pre-existing services untouched.");
            return !failed;
        })().finally(() => { this.shutdownInFlight = null; });
        return this.shutdownInFlight;
    }
}

function requireFile(file) {
    try { accessSync(file, fsConstants.F_OK); return true; } catch { return false; }
}

export function openDefaultBrowser(url) {
    return new Promise((resolve, reject) => {
        const child = nodeSpawn("rundll32.exe", ["url.dll,FileProtocolHandler", url], { stdio: "ignore", windowsHide: true });
        child.once("error", reject);
        child.once("exit", code => code === 0 ? resolve() : reject(new Error(`Browser launcher exit ${code}`)));
    });
}

async function main() {
    const supervisor = new TegakiShellSupervisor({ portableRoot: path.resolve(__dirname, "..", "..") });
    const input = createInterface({ input: process.stdin, output: process.stdout });
    let starting = true;
    let requested = false;
    let finished = false;
    const shutdown = async () => {
        requested = true;
        if (starting || finished) return;
        const stopped = await supervisor.shutdown();
        if (stopped) { finished = true; input.close(); process.exitCode = 0; }
    };
    process.on("SIGINT", shutdown);
    process.on("SIGTERM", shutdown);
    input.on("SIGINT", shutdown);
    input.on("line", shutdown);
    input.on("close", () => { if (!finished) void shutdown(); });
    console.log("Press Enter or Ctrl+C for safe shutdown.");
    try {
        await supervisor.start();
        await new Promise(() => {});
    } catch (_) {
        finished = true;
        input.close();
        process.exitCode = 1;
    } finally {
        starting = false;
        if (requested && !finished) await shutdown();
    }
}

if (process.argv[1] && path.resolve(process.argv[1]) === __filename) await main();
