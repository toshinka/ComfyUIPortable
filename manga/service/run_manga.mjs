/** Owner entrypoint. Lifecycle/ownership authority remains MangaDomainRuntime. */
import { spawn } from "node:child_process";
import { accessSync } from "node:fs";
import { readFile } from "node:fs/promises";
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

// Identity alone does not distinguish an older checkout. Refuse a stale UI, without stopping its owner.
export async function verifyWorkspaceSource(runtime) {
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
    await verifySource(runtime);
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
