/** Owner entrypoint. Lifecycle/ownership authority remains MangaDomainRuntime. */
import { spawn } from "node:child_process";
import { createHash } from "node:crypto";
import { accessSync } from "node:fs";
import { readFile, readdir, stat } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { createInterface } from "node:readline";
import { MangaDomainRuntime, OwnershipClassification } from "./manga_domain_runtime.mjs";

const here = path.dirname(fileURLToPath(import.meta.url));
export const WORKSPACE_URL = "http://127.0.0.1:8191/";

// Hooks only attach console diagnostics; runtime chooses commands, arguments and ownership.
function diagnosticSpawn({ command, args, cwd, env }) {
    accessSync(command);
    accessSync(args[0] === "-s" ? args[1] : args[0]);
    const child = spawn(command, args, {
        cwd, env, stdio: ["ignore", "pipe", "pipe"], windowsHide: true,
    });
    child.stdout.pipe(process.stdout);
    child.stderr.pipe(process.stderr);
    child.on("error", error => console.error(`Child startup error: ${error.message}`));
    return child;
}

export function openDefaultBrowser(url) {
    return new Promise((resolve, reject) => {
        const child = spawn("rundll32.exe", ["url.dll,FileProtocolHandler", url], {
            stdio: "ignore", windowsHide: true,
        });
        child.once("error", reject);
        child.once("exit", code => code === 0 ? resolve() : reject(new Error(`Browser launcher exit ${code}`)));
    });
}

/**
 * Digest of one source folder: sha256 over name + NUL + bytes + NUL for each file with
 * `extension`, sorted by name.  Same formula as the running processes report
 * (manga_workspace_server.mjs `source_digest`, basic_generation_api.py `source_digest`).
 */
export async function sourceFolderDigest(dir, extension) {
    const hash = createHash("sha256");
    for (const name of (await readdir(dir)).filter(item => item.endsWith(extension)).sort()) {
        const file = path.join(dir, name);
        if (!(await stat(file)).isFile()) continue;
        hash.update(Buffer.concat([Buffer.from(name, "utf8"), Buffer.from([0]), await readFile(file), Buffer.from([0])]));
    }
    return hash.digest("hex");
}

export const WORKSPACE_SOURCE_DIR = path.resolve(here);
export const BACKEND_SOURCE_DIR = path.resolve(here, "../../ComfyUI/custom_nodes/tegaki_manga_nodes");

async function fetchJson(url) {
    const response = await fetch(url, { signal: AbortSignal.timeout(5000), cache: "no-store", redirect: "error" });
    let data = null;
    try { data = await response.json(); } catch { data = null; }
    return { status: response.status, data };
}

function staleError(service, detail, pid, url) {
    const port = (() => { try { return new URL(url).port; } catch { return ""; } })();
    const stop = Number.isSafeInteger(pid) && pid > 0
        ? ` Stop that process (Windows: taskkill /PID ${pid} /F), then run run_manga.bat again.`
        : ` Stop the process listening on port ${port} (PowerShell: Get-NetTCPConnection -LocalPort ${port} -State Listen | Select OwningProcess; then taskkill /PID <OwningProcess> /F), then run run_manga.bat again.`;
    return new Error(`STALE ${service}: ${detail}.${stop}`);
}

// Identity alone does not distinguish an older checkout. Refuse a stale UI, without stopping its owner.
// Static app files are served from disk per request, so they always match; the SERVER code a reused
// process loaded is checked separately by source digest (RUNTIME-FRESHNESS).
export async function verifyWorkspaceSource(runtime, {
    workspaceDir = WORKSPACE_SOURCE_DIR, backendDir = BACKEND_SOURCE_DIR,
} = {}) {
    for (const relative of ["index.html", "css/manga_workspace.css", "src/view/generation_view.js",
        "src/state/generation_state.js", "src/adapters/manga_generation_client.js"]) {
        const local = await readFile(path.resolve(here, "../app", relative));
        const response = await fetch(new URL(relative, runtime.workspaceUrl + "/"), {
            signal: AbortSignal.timeout(5000), cache: "no-store", redirect: "error",
        });
        if (!response.ok || !local.equals(Buffer.from(await response.arrayBuffer()))) {
            throw new Error(`Workspace source mismatch: ${relative}. Close the other workspace through its own launcher, then retry.`);
        }
    }
    const workspace = await fetchJson(`${runtime.workspaceUrl}/api/runtime/identity`);
    const workspaceDisk = await sourceFolderDigest(workspaceDir, ".mjs");
    if (workspace.data?.source_digest !== workspaceDisk) {
        throw staleError("WORKSPACE SERVER", workspace.data?.source_digest
            ? "the process on the workspace port loaded older manga/service source than is on disk"
            : "the process on the workspace port predates source reporting (older code)", workspace.data?.pid, runtime.workspaceUrl);
    }
    const backend = await fetchJson(`${runtime.backendUrl}/tegaki/manga/runtime/source-identity`);
    const backendDisk = await sourceFolderDigest(backendDir, ".py");
    if (backend.data?.source_digest !== backendDisk) {
        throw staleError("BACKEND", backend.data?.source_digest
            ? "the ComfyUI process on the backend port loaded older tegaki_manga_nodes source than is on disk"
            : "the ComfyUI process on the backend port predates source reporting (older code)", backend.data?.pid, runtime.backendUrl);
    }
    return { workspacePid: workspace.data.pid, backendPid: backend.data.pid, workspaceDigest: workspaceDisk, backendDigest: backendDisk };
}

export async function startLauncher(runtime, {
    openBrowser = openDefaultBrowser, verifySource = verifyWorkspaceSource, log = console.log,
} = {}) {
    log("TEGAKI MANGA");
    log(`Portable root: ${runtime.portableRoot}`);
    log(`Backend: ${runtime.backendUrl}/`);
    log(`Workspace: ${WORKSPACE_URL}`);
    log("State: STARTING");
    const state = await runtime.start();
    const workspace = await runtime.probeWorkspace();
    if (workspace.classification !== OwnershipClassification.PREEXISTING_COMPATIBLE) {
        throw new Error(`Workspace identity invalid: ${workspace.details}`);
    }
    if (!["READY", "BUSY"].includes(state)) throw new Error(`Runtime state: ${state}`);
    const fresh = await verifySource(runtime);
    if (fresh?.workspacePid) log(`Source: current (workspace PID ${fresh.workspacePid}, backend PID ${fresh.backendPid})`);
    log(`State: ${state}`);
    log(`Backend ownership: ${runtime.backendOwnership}`);
    log(`Workspace ownership: ${runtime.workspaceOwnership}`);
    log(`Browser: ${WORKSPACE_URL}`);
    try { await openBrowser(WORKSPACE_URL); }
    catch (error) { log(`Browser launch failed: ${error.message}. Open ${WORKSPACE_URL} manually.`); }
}

export async function stopLauncher(runtime, log = console.log) {
    try {
        await runtime.stopAll();
        log("Owned-process shutdown confirmed by runtime. Preexisting services remain untouched.");
        return true;
    } catch (error) {
        log(`Safe stop refused/failed: ${error.message}. No force kill. Console remains active; retry Enter or Ctrl+C.`);
        return false;
    }
}

async function main() {
    const runtime = new MangaDomainRuntime({
        portableRoot: path.resolve(here, "../.."),
        customSpawnBackend: diagnosticSpawn, customSpawnWorkspace: diagnosticSpawn,
    });
    const keepAlive = setInterval(() => {}, 1000);
    const input = createInterface({ input: process.stdin, output: process.stdout });
    let starting = true, requested = false, stopping = false, finished = false;
    async function shutdown() {
        requested = true;
        if (starting || stopping || finished) return;
        stopping = true;
        if (await stopLauncher(runtime)) {
            finished = true;
            clearInterval(keepAlive);
            input.close();
            process.removeListener("SIGINT", shutdown);
            process.removeListener("SIGTERM", shutdown);
        }
        stopping = false;
    }
    process.on("SIGINT", shutdown);
    process.on("SIGTERM", shutdown);
    input.on("SIGINT", shutdown);
    input.on("line", shutdown);
    input.on("close", () => { if (!finished) void shutdown(); });
    console.log("Press Enter or Ctrl+C for safe shutdown (during startup, waits for startup to settle).");
    try { await startLauncher(runtime); }
    catch (error) {
        console.error(`State: FAILED — ${error.message}`);
        process.exitCode = 1;
        requested = true;
    } finally {
        starting = false;
        if (requested) await shutdown();
    }
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
    await main();
}
