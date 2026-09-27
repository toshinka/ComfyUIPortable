/**
 * LegacyReforgeSupervisor (Card MANGA-LEGACY-EASYREFORGE-VERTICAL-MVP1).
 *
 * Owns ONE EasyReforge process started from the Integration Runtime copy.  Minimal:
 * configuration, command construction, start, readiness, stop, ownership, failure reporting.
 * No cold-switch machinery, no GPU-memory orchestration, no crash-restart loops.
 *
 * SAFETY: the Legacy Reference appliance (E:\EasyReforge) is never a runtime or write target.
 * The runtime root must resolve (lexically AND through links) under the Integration Runtime.
 */
import fs from "node:fs";
import path from "node:path";
import { execFileSync, spawn } from "node:child_process";
import { LegacyReforgeError } from "./legacy_reforge_adapter.mjs";

export const REFERENCE_RUNTIME_ROOT = "E:\\EasyReforge";
export const INTEGRATION_RUNTIME_ROOT = "E:\\TEGAKI_Runtime\\EasyReforge";
export const DEFAULT_LEGACY_PORT = 7862;           // Reference default is 7860; never share it
export const LEGACY_LAUNCH_ARGS = Object.freeze(["--api"]);

const win = path.win32;
const key = value => win.resolve(String(value)).replace(/[\\/]+$/, "").toLowerCase();
export function isSameOrInside(candidate, root) {
    const c = key(candidate);
    const r = key(root);
    return c === r || c.startsWith(`${r}\\`);
}

/** Inspect only the configured ReForge port and resolve its one listener to an executable. */
function inspectWindowsListener(port) {
    if (process.platform !== "win32") return { ok: false, listeners: [] };
    let output;
    try {
        output = execFileSync("netstat.exe", ["-ano", "-p", "tcp"],
            { encoding: "utf8", windowsHide: true, timeout: 4000 });
    } catch {
        return { ok: false, listeners: [] };
    }
    const pids = new Set();
    for (const line of output.split(/\r?\n/)) {
        const fields = line.trim().split(/\s+/);
        if (fields.length < 5 || fields[0]?.toUpperCase() !== "TCP" || fields[3]?.toUpperCase() !== "LISTENING") continue;
        if (!fields[1]?.endsWith(`:${port}`)) continue;
        const pid = Number(fields[4]);
        if (Number.isSafeInteger(pid) && pid > 0) pids.add(pid);
    }
    if (!pids.size) return { ok: true, listeners: [] };
    if (pids.size !== 1) return { ok: true, listeners: [...pids].map(pid => ({ pid, executable: "" })) };
    const pid = [...pids][0];
    let executable = "";
    try {
        executable = execFileSync("powershell.exe", ["-NoProfile", "-NonInteractive", "-Command",
            `$ErrorActionPreference='Stop'; $p=Get-Process -Id ${pid} -ErrorAction Stop; [Console]::Write($p.Path)`],
        { encoding: "utf8", windowsHide: true, timeout: 4000 }).trim();
    } catch { /* An unreadable process identity must fail closed. */ }
    return { ok: true, listeners: [{ pid, executable }] };
}

/**
 * Resolve and guard the runtime root.  `realpath` lets the caller prove that links/junctions
 * do not redirect the Integration root into the Reference.
 */
export function resolveIntegrationRoot({ env = process.env, realpath = null } = {}) {
    const configured = String(env.TEGAKI_REFORGE_RUNTIME || "").trim() || INTEGRATION_RUNTIME_ROOT;
    const root = win.resolve(configured);
    const check = (candidate, label) => {
        if (isSameOrInside(candidate, REFERENCE_RUNTIME_ROOT)) {
            throw new LegacyReforgeError("REFERENCE_RUNTIME_FORBIDDEN",
                `${label} resolves to the read-only Legacy Reference (${REFERENCE_RUNTIME_ROOT})`, 500);
        }
        if (!isSameOrInside(candidate, INTEGRATION_RUNTIME_ROOT)) {
            throw new LegacyReforgeError("INTEGRATION_ROOT_REQUIRED",
                `${label} must be under the Integration Runtime (${INTEGRATION_RUNTIME_ROOT})`, 500);
        }
    };
    check(root, "EasyReforge runtime root");
    if (typeof realpath === "function") {
        let real = null;
        try { real = realpath(root); } catch { real = null; }
        if (real) check(real, "EasyReforge runtime root (resolved)");
    }
    return root;
}

export function resolveLegacyPort(env = process.env) {
    const raw = String(env.TEGAKI_REFORGE_PORT || "").trim();
    const port = raw ? Number(raw) : DEFAULT_LEGACY_PORT;
    if (!Number.isSafeInteger(port) || port < 1024 || port > 65535 || port === 7860) {
        throw new LegacyReforgeError("LEGACY_PORT_INVALID", "TEGAKI_REFORGE_PORT must be 1024..65535 and not 7860", 500);
    }
    return port;
}

/** Files that must exist for the Integration Runtime to be considered installed. */
export function runtimeLayout(root) {
    return {
        launcher: win.join(root, "Reforge.bat"),
        launcherNoOptions: win.join(root, "Reforge_NoOptions.bat"),
        webuiBat: win.join(root, "stable-diffusion-webui-reForge", "webui.bat"),
        python: win.join(root, "stable-diffusion-webui-reForge", "venv", "Scripts", "python.exe"),
    };
}

/**
 * The exact process to start: the copied appliance's own launcher chain
 * (Reforge.bat -> Reforge_NoOptions.bat -> webui.bat), with --api and a dedicated port.
 * COMMANDLINE_ARGS is cleared so the launcher uses exactly these arguments; Python-related
 * variables of the Manga/Comfy environment are removed so the copied venv is used.
 */
export function buildStartCommand(root, port, baseEnv = process.env) {
    const { launcher } = runtimeLayout(root);
    if (!isSameOrInside(launcher, INTEGRATION_RUNTIME_ROOT) || isSameOrInside(launcher, REFERENCE_RUNTIME_ROOT)) {
        throw new LegacyReforgeError("REFERENCE_RUNTIME_FORBIDDEN", "Launcher is outside the Integration Runtime", 500);
    }
    const args = [...LEGACY_LAUNCH_ARGS, "--port", String(port)];
    const env = { ...baseEnv, COMMANDLINE_ARGS: "" };
    for (const name of ["PYTHONPATH", "PYTHONHOME", "VIRTUAL_ENV", "PYTHON", "VENV_DIR", "GIT"]) delete env[name];
    return {
        command: "cmd.exe",
        args: ["/d", "/s", "/c", `""${launcher}" ${args.join(" ")}"`],
        options: { cwd: root, env, windowsHide: true, windowsVerbatimArguments: true, stdio: ["ignore", "pipe", "pipe"] },
        launcher, port, launchArgs: args,
    };
}

const SECRETISH = /(api[_-]?key|token|secret|password|civitai)/i;

export class LegacyReforgeSupervisor {
    constructor({ env = process.env, fsImpl = fs, spawnFn = spawn, client = null, platform = process.platform,
                  listenerInspector = inspectWindowsListener, readyTimeoutMs = 15 * 60 * 1000, pollMs = 2000,
                  sleep = ms => new Promise(r => setTimeout(r, ms)) } = {}) {
        this.fs = fsImpl;
        this.spawnFn = spawnFn;
        this.platform = platform;
        this.listenerInspector = listenerInspector;
        this.readyTimeoutMs = readyTimeoutMs;
        this.pollMs = pollMs;
        this.sleep = sleep;
        this.client = client;
        this.configError = null;
        try {
            this.root = resolveIntegrationRoot({ env, realpath: p => fsImpl.realpathSync?.native?.(p) ?? fsImpl.realpathSync?.(p) });
            this.port = resolveLegacyPort(env);
        } catch (error) {
            this.root = null;
            this.port = null;
            this.configError = error;
        }
        this.env = env;
        this.child = null;
        this.external = null;
        this.state = "stopped";           // stopped | starting | ready | failed | stopping
        this.error = null;
        this.logTail = [];
    }

    get baseUrl() { return this.port ? `http://127.0.0.1:${this.port}` : null; }

    installed() {
        if (this.configError) return { ok: false, reason: this.configError.message, code: this.configError.code };
        if (this.platform !== "win32") return { ok: false, reason: "EasyReforge runs on Windows only", code: "UNSUPPORTED_PLATFORM" };
        const missing = Object.entries(runtimeLayout(this.root)).filter(([, file]) => !this.fs.existsSync(file)).map(([name]) => name);
        return missing.length ? { ok: false, reason: `Integration Runtime is incomplete (missing ${missing.join(", ")})`, code: "RUNTIME_INCOMPLETE" }
            : { ok: true, reason: "", code: "" };
    }

    status() {
        const installed = this.installed();
        return {
            backend: "easyreforge", installed: installed.ok, installed_reason: installed.reason,
            runtime_root: this.root, port: this.port, state: this.state,
            owned: Boolean(this.child), pid: this.child?.pid ?? this.external?.pid ?? null,
            error: this.error ? { code: this.error.code, message: this.error.message } : null,
            log_tail: this.logTail.slice(-12),
        };
    }

    _externalListener() {
        let snapshot;
        try { snapshot = this.listenerInspector(this.port); }
        catch { snapshot = null; }
        if (!snapshot || snapshot.ok !== true || !Array.isArray(snapshot.listeners)) {
            throw new LegacyReforgeError("PROCESS_IDENTITY_UNAVAILABLE", "Could not verify the process listening on the EasyReforge port", 503);
        }
        if (!snapshot.listeners.length) return null;
        if (snapshot.listeners.length !== 1) {
            throw new LegacyReforgeError("FOREIGN_PROCESS_ON_PORT", `Port ${this.port} has an ambiguous listener identity`, 409);
        }
        const listener = snapshot.listeners[0];
        const expectedPython = runtimeLayout(this.root).python;
        if (!Number.isSafeInteger(listener?.pid) || listener.pid < 1 || !listener.executable || key(listener.executable) !== key(expectedPython)) {
            throw new LegacyReforgeError("FOREIGN_PROCESS_ON_PORT", `Port ${this.port} is occupied by an unverified process`, 409);
        }
        return { pid: listener.pid, executable: win.resolve(listener.executable) };
    }

    /** Recheck an external listener before exposing readiness through Manga status routes. */
    async refreshExternal() {
        if (this.child || !this.installed().ok || !this.client) return this.status();
        let listener;
        try { listener = this._externalListener(); }
        catch (error) {
            this.external = null;
            this._fail(error.code || "PROCESS_IDENTITY_UNAVAILABLE", error.message || "Could not verify the EasyReforge process");
            return this.status();
        }
        if (!listener) {
            const wasExternal = Boolean(this.external);
            this.external = null;
            if (wasExternal || ["FOREIGN_PROCESS_ON_PORT", "PROCESS_IDENTITY_UNAVAILABLE", "LEGACY_API_UNAVAILABLE"].includes(this.error?.code)) {
                this.state = "stopped";
                this.error = null;
            }
            return this.status();
        }
        this.external = listener;
        if (await this.client.ping().catch(() => false)) {
            this.state = "ready";
            this.error = null;
        } else {
            this._fail("LEGACY_API_UNAVAILABLE", "The verified Integration process is not API-ready");
        }
        return this.status();
    }

    _log(chunk) {
        for (const line of String(chunk).split(/\r?\n/)) {
            if (!line.trim()) continue;
            this.logTail.push(SECRETISH.test(line) ? "[line withheld]" : line.slice(0, 300));
            if (this.logTail.length > 40) this.logTail.shift();
        }
    }

    /** Start and wait for readiness (tests / callers that want to block). */
    async start() {
        await this.begin();
        return this.waitReady();
    }

    /** Reuse only a verified external Integration process; otherwise refuse occupied ports or spawn. */
    async begin() {
        const installed = this.installed();
        if (!installed.ok) throw new LegacyReforgeError(installed.code || "RUNTIME_UNAVAILABLE", installed.reason, 503);
        if (this.child && (this.state === "ready" || this.state === "starting")) return this.status();
        if (!this.client) throw new LegacyReforgeError("LEGACY_CLIENT_MISSING", "EasyReforge API client is not configured", 500);
        let listener;
        try { listener = this._externalListener(); }
        catch (error) {
            this._fail(error.code || "PROCESS_IDENTITY_UNAVAILABLE", error.message || "Could not verify the EasyReforge process");
            throw this.error;
        }
        if (listener) {
            this.external = listener;
            this.error = null;
            this.state = await this.client.ping().catch(() => false) ? "ready" : "starting";
            return this.status();
        }
        this.external = null;
        if (await this.client.ping().catch(() => false)) {
            this._fail("FOREIGN_PROCESS_ON_PORT", `Port ${this.port} responds to the API probe but has no verified Integration listener`);
            throw this.error;
        }
        const spec = buildStartCommand(this.root, this.port, this.env);
        this.state = "starting";
        this.error = null;
        this.logTail = [];
        let child;
        try { child = this.spawnFn(spec.command, spec.args, spec.options); }
        catch (error) { this._fail("STARTUP_FAILED", `EasyReforge could not be started (${error.code || error.message})`); throw this.error; }
        this.child = child;
        child.stdout?.on?.("data", chunk => this._log(chunk));
        child.stderr?.on?.("data", chunk => this._log(chunk));
        child.once?.("error", error => { if (this.child === child) this._fail("STARTUP_FAILED", `EasyReforge process error (${error.code || error.message})`); });
        child.once?.("exit", code => {
            if (this.child !== child) return;
            this.child = null;
            if (this.state === "stopping") this.state = "stopped";
            else this._fail("PROCESS_EXITED", `EasyReforge exited (code ${code ?? "?"})`);
        });
        return this.status();
    }

    /** Poll the API until ready, the process dies, or the timeout passes. */
    async waitReady() {
        const child = this.child;
        if (this.state === "ready") return this.status();
        const deadline = Date.now() + this.readyTimeoutMs;
        while (this.child === child && this.state === "starting") {
            if (!child) {
                let listener;
                try { listener = this._externalListener(); }
                catch (error) {
                    this.external = null;
                    this._fail(error.code || "FOREIGN_PROCESS_ON_PORT", error.message || "External process identity changed");
                    break;
                }
                if (!listener || listener.pid !== this.external?.pid) {
                    this.external = null;
                    this.state = "stopped";
                    this.error = null;
                    break;
                }
                this.external = listener;
            }
            if (await this.client.ping().catch(() => false)) { this.state = "ready"; break; }
            if (Date.now() > deadline) {
                this._fail("STARTUP_TIMEOUT", "EasyReforge API did not become ready in time");
                if (child) await this.stop();
                break;
            }
            await this.sleep(this.pollMs);
        }
        if (this.state !== "ready") throw this.error || new LegacyReforgeError("STARTUP_FAILED", "EasyReforge did not start", 503);
        return this.status();
    }

    _fail(code, message) {
        this.state = "failed";
        this.error = new LegacyReforgeError(code, message, 503);
    }

    /** Stop only the process tree this supervisor started. */
    async stop() {
        const child = this.child;
        if (!child) {
            if (this.external) return this.refreshExternal();
            if (this.state !== "failed") this.state = "stopped";
            return this.status();
        }
        this.state = "stopping";
        await new Promise(resolve => {
            let killer;
            try { killer = this.spawnFn("taskkill", ["/PID", String(child.pid), "/T", "/F"], { windowsHide: true, stdio: "ignore" }); }
            catch { try { child.kill(); } catch {} resolve(); return; }
            killer.once?.("exit", () => resolve());
            killer.once?.("error", () => { try { child.kill(); } catch {} resolve(); });
        });
        this.child = null;
        this.state = "stopped";
        return this.status();
    }
}
