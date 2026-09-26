/**
 * manga_workspace_server.mjs — Standalone Manga Workspace HTTP Service
 * ====================================================================
 * TEGAKI Manga Authoring Workspace (M1A)
 * 
 * Lightweight local static server & backend proxy:
 * - Pure Node.js (zero npm dependencies).
 * - Serves frontend from ComfyUIPortable/manga/app/.
 * - Binds to local port (default 8191).
 * - Supports CORS-free proxying to ComfyUI backend if requested via /proxy/*.
 */

import http from "node:http";
import fs from "node:fs";
import path from "node:path";
import crypto from "node:crypto";
import { spawn } from "node:child_process";
import { fileURLToPath } from "node:url";
import { GenerationService, GenerationServiceError } from "./generation_service.mjs";
import { GenerationJournal, JournalError } from "./generation_journal.mjs";
import { IsolatedScenePrepService, IsolatedScenePrepError } from "./isolated_scene_prep_service.mjs";
import { PageCompositeStore, PageCompositeStoreError } from "./page_composite_store.mjs";
import { PageCompositeIndex, PageCompositeIndexError } from "./page_composite_index.mjs";
import { PageCompositorBridge, PageCompositorBridgeError } from "./page_compositor_bridge.mjs";
import { PageCompositePersistService, PageCompositePersistError } from "./page_composite_persist_service.mjs";
import { PageCompositeCurrentClassifier, PageCompositeCurrentError } from "./page_composite_current.mjs";
import { preparePageComposition } from "./page_compositor_prep.mjs";
import { SceneResultStore } from "./scene_result_store.mjs";
import { SceneResultIndex } from "./scene_result_index.mjs";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const APP_DIR = path.resolve(__dirname, "..", "app");
const REPO_ROOT = path.resolve(__dirname, "..", "..");
const EMBEDDED_PYTHON = path.join(REPO_ROOT, "python_embeded", "python.exe");
const ANALYZER_SCRIPT = path.join(__dirname, "reference_identity_analyzer.py");

const PORT = parseInt(process.env.MANGA_WORKSPACE_PORT || "8191", 10);
const HOST = "127.0.0.1";

// Runtime freshness (Card MANGA-PROMPT-VALIDATION-COHERENCE1): the server-side source this
// process LOADED.  Static app files are read from disk per request and always look current,
// so run_manga.mjs compares this digest (same formula) with disk before reusing a process.
function workspaceSourceDigest(dir = __dirname) {
    const hash = crypto.createHash("sha256");
    for (const name of fs.readdirSync(dir).filter(item => item.endsWith(".mjs")).sort()) {
        const file = path.join(dir, name);
        if (!fs.statSync(file).isFile()) continue;
        hash.update(Buffer.concat([Buffer.from(name, "utf8"), Buffer.from([0]), fs.readFileSync(file), Buffer.from([0])]));
    }
    return hash.digest("hex");
}
let LOADED_SOURCE_DIGEST = null;
try { LOADED_SOURCE_DIGEST = workspaceSourceDigest(); } catch { LOADED_SOURCE_DIGEST = null; }

const MIME_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".svg": "image/svg+xml"
};

const BACKEND_URL = (process.env.MANGA_BACKEND_URL || "http://127.0.0.1:8189").replace(/\/$/, "");
let parsedBackend;
try {
    parsedBackend = new URL(BACKEND_URL);
    if (parsedBackend.protocol !== "http:") {
        throw new Error(`Forbidden protocol '${parsedBackend.protocol}'. Only http: is permitted.`);
    }
    if (parsedBackend.hostname !== "127.0.0.1" && parsedBackend.hostname !== "localhost") {
        throw new Error(`Forbidden host '${parsedBackend.hostname}'. Only loopback (127.0.0.1 or localhost) is permitted.`);
    }
} catch (err) {
    console.error(`[MangaWorkspaceServer] Backend configuration error: ${err.message}`);
    process.exit(1);
}

// Strictly bounded whitelist of allowed Manga backend paths (Card Section 4)
export const ALLOWED_PROXY_PATHS = new Set([
    "/queue",
    "/object_info/TegakiMinimumHandSceneEditor",
    "/tegaki/manga/generation/prepare",
    "/tegaki/manga/generation/compile-scene",
    "/extensions/tegaki_manga_nodes/js/minimum_hand_scene_editor.js"
]);

let generationService = new GenerationService({
    backendUrl: parsedBackend.origin,
    journal: new GenerationJournal(process.env.MANGA_GENERATION_JOURNAL_DIR || undefined)
});

let isolatedScenePrepService = new IsolatedScenePrepService({
    backendUrl: parsedBackend.origin
});

generationService.isolatedScenePrepService = isolatedScenePrepService;

export function setIsolatedScenePrepService(service) {
    isolatedScenePrepService = service;
    if (generationService) {
        generationService.isolatedScenePrepService = service;
    }
}

export function setGenerationService(service) {
    generationService = service;
}

let sceneResultStore = new SceneResultStore();
let sceneResultIndex = new SceneResultIndex({ store: sceneResultStore });
let pageCompositeStore = new PageCompositeStore();
let pageCompositeIndex = new PageCompositeIndex({ store: pageCompositeStore });
let pageCompositorBridge = new PageCompositorBridge({
    backendUrl: parsedBackend.origin,
    store: sceneResultStore,
    index: sceneResultIndex,
    prepFn: preparePageComposition,
});
let pageCompositePersistService = new PageCompositePersistService({
    bridge: pageCompositorBridge,
    store: pageCompositeStore,
    index: pageCompositeIndex,
});
let pageCompositeCurrentClassifier = new PageCompositeCurrentClassifier({
    store: pageCompositeStore,
    index: pageCompositeIndex,
    prepFn: preparePageComposition,
    sceneStore: sceneResultStore,
    sceneIndex: sceneResultIndex,
});

export function setPageCompositeServices({
    store = null,
    index = null,
    bridge = null,
    persistService = null,
    currentClassifier = null,
    sceneStore = null,
    sceneIndex = null,
} = {}) {
    if (store !== null) pageCompositeStore = store;
    if (index !== null) pageCompositeIndex = index;
    if (bridge !== null) pageCompositorBridge = bridge;
    if (persistService !== null) pageCompositePersistService = persistService;
    if (currentClassifier !== null) pageCompositeCurrentClassifier = currentClassifier;
    if (sceneStore !== null) sceneResultStore = sceneStore;
    if (sceneIndex !== null) sceneResultIndex = sceneIndex;
}

function sanitizeErrorMessage(msg) {
    if (typeof msg !== "string") return "An error occurred";
    return msg
        .replace(/[A-Za-z]:\\[^ \t\n\r"'\)]+/g, "[redacted-path]")
        .replace(/(?:\/[a-zA-Z0-9_\.\-]+){3,}/g, "[redacted-path]");
}

const server = http.createServer(async (req, res) => {
    // Restricted same-origin CORS: do not expose wildcard '*' (Card Section 5)
    const requestOrigin = req.headers.origin;
    const boundPort = server.address()?.port || PORT;
    const allowedLocalOrigins = new Set([
        `http://${HOST}:${PORT}`,
        `http://localhost:${PORT}`,
        `http://${HOST}:${boundPort}`,
        `http://localhost:${boundPort}`
    ]);
    if (requestOrigin && allowedLocalOrigins.has(requestOrigin)) {
        res.setHeader("Access-Control-Allow-Origin", requestOrigin);
        res.setHeader("Access-Control-Allow-Methods", "GET, POST, OPTIONS");
        res.setHeader("Access-Control-Allow-Headers", "Content-Type");
    }

    if (req.method === "OPTIONS") {
        res.writeHead(204);
        res.end();
        return;
    }

    const url = new URL(req.url, `http://${HOST}:${PORT}`);
    let pathname = url.pathname;
    if (pathname === "/") pathname = "/index.html";

    // PLAY1a/PLAY5: fixed read/compile routes. No browser graph submission or general proxy expansion.
    if (pathname === "/api/manga/generation/capabilities" ||
        pathname === "/api/manga/generation/compile" ||
        pathname === "/api/manga/generation/compile-scene") {
        const isCompile = pathname === "/api/manga/generation/compile";
        const isSceneCompile = pathname === "/api/manga/generation/compile-scene";
        const expectedMethod = isCompile || isSceneCompile ? "POST" : "GET";
        const reply = (status, error_code, error) => {
            res.writeHead(status, { "Content-Type": "application/json; charset=utf-8" });
            res.end(JSON.stringify({ ok: false, error_code, error }));
        };
        if (req.method !== expectedMethod) {
            reply(405, "METHOD_NOT_ALLOWED", `Use ${expectedMethod}`);
            return;
        }
        if ((requestOrigin && !allowedLocalOrigins.has(requestOrigin)) ||
            (req.headers["sec-fetch-site"] && !["same-origin", "none"].includes(req.headers["sec-fetch-site"]))) {
            reply(403, "ORIGIN_FORBIDDEN", "Request origin is not the Manga workspace");
            return;
        }
        let body;
        if (isCompile || isSceneCompile) {
            if ((req.headers["content-type"] || "").split(";")[0].trim().toLowerCase() !== "application/json") {
                reply(415, "INVALID_CONTENT_TYPE", "Content-Type must be application/json");
                return;
            }
            const declaredLength = Number(req.headers["content-length"]);
            if (req.headers["content-length"] && (!Number.isSafeInteger(declaredLength) || declaredLength > 256 * 1024)) {
                reply(413, "REQUEST_TOO_LARGE", "Request exceeds 256 KiB");
                return;
            }
            const chunks = [];
            let received = 0;
            for await (const chunk of req) {
                received += chunk.length;
                if (received > 256 * 1024) {
                    req.resume();
                    reply(413, "REQUEST_TOO_LARGE", "Request exceeds 256 KiB");
                    return;
                }
                chunks.push(chunk);
            }
            body = Buffer.concat(chunks);
            try {
                const parsed = JSON.parse(body.toString("utf8"));
                if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) throw new Error("Expected JSON object");
            } catch (err) {
                reply(400, "INVALID_JSON", `Invalid JSON request: ${err.message}`);
                return;
            }
        }
        const backendPath = isCompile
            ? "/tegaki/manga/generation/compile-basic"
            : isSceneCompile
                ? "/tegaki/manga/generation/compile-scene"
                : "/tegaki/manga/generation/capabilities";
        try {
            const backendRes = await fetch(`${parsedBackend.origin}${backendPath}`, {
                method: expectedMethod,
                headers: (isCompile || isSceneCompile) ? { "Content-Type": "application/json" } : undefined,
                body,
                signal: AbortSignal.timeout(5000)
            });
            const chunks = [];
            let size = 0;
            for await (const chunk of backendRes.body) {
                size += chunk.length;
                if (size > 4 * 1024 * 1024) {
                    reply(502, "BACKEND_INVALID_RESPONSE", "Backend response exceeds 4 MiB");
                    return;
                }
                chunks.push(chunk);
            }
            let data;
            try {
                data = JSON.parse(Buffer.concat(chunks).toString("utf8"));
            } catch (err) {
                reply(502, "BACKEND_INVALID_RESPONSE", "Backend returned invalid JSON");
                return;
            }
            if (!data || typeof data !== "object" || Array.isArray(data) ||
                (backendRes.ok && (data.ok !== true ||
                    ((isCompile || isSceneCompile) ? !data.graph || typeof data.graph_digest !== "string"
                               : !Array.isArray(data.checkpoints) || !Array.isArray(data.samplers) || typeof data.revision !== "string"))) ||
                (!backendRes.ok && (data.ok !== false || typeof data.error !== "string"))) {
                reply(502, "BACKEND_INVALID_RESPONSE", "Backend response is missing required fields");
                return;
            }
            if (!backendRes.ok) {
                res.writeHead(backendRes.status, { "Content-Type": "application/json; charset=utf-8" });
                res.end(JSON.stringify({ ok: false, error_code: data.error_code || "BACKEND_REJECTED", error: data.error,
                    request: data.request }));
                return;
            }
            res.writeHead(200, { "Content-Type": "application/json; charset=utf-8" });
            res.end(JSON.stringify(data));
        } catch (err) {
            reply(502, err.name === "TimeoutError" ? "BACKEND_TIMEOUT" : "BACKEND_UNAVAILABLE",
                err.name === "TimeoutError" ? "Backend capability request timed out" : "Backend capability request failed");
        }
        return;
    }

    // Trusted-root LoRA index (autocomplete) and batch prompt LoRA diagnostics
    // (Card MANGA-LORA-PORTABLE-COMPAT-DIAGNOSTICS1). The backend resolver is authoritative.
    if (pathname === "/api/manga/resources/lora/index" || pathname === "/api/manga/resources/lora/validate") {
        const isValidate = pathname.endsWith("/validate");
        const expectedMethod = isValidate ? "POST" : "GET";
        const reply = (status, error_code, error) => {
            res.writeHead(status, { "Content-Type": "application/json; charset=utf-8" });
            res.end(JSON.stringify({ ok: false, error_code, error }));
        };
        if (req.method !== expectedMethod) {
            reply(405, "METHOD_NOT_ALLOWED", `Use ${expectedMethod}`);
            return;
        }
        if ((requestOrigin && !allowedLocalOrigins.has(requestOrigin)) ||
            (req.headers["sec-fetch-site"] && !["same-origin", "none"].includes(req.headers["sec-fetch-site"]))) {
            reply(403, "ORIGIN_FORBIDDEN", "Request origin is not the Manga workspace");
            return;
        }
        const engine = url.searchParams.get("engine") || "illustrious";
        if (!["illustrious"].includes(engine)) {
            reply(404, "RESOURCE_UNSUPPORTED", `No LoRA resource is registered for engine '${engine}'`);
            return;
        }
        let body;
        if (isValidate) {
            if ((req.headers["content-type"] || "").split(";")[0].trim().toLowerCase() !== "application/json") {
                reply(415, "INVALID_CONTENT_TYPE", "Content-Type must be application/json");
                return;
            }
            const chunks = [];
            let received = 0;
            for await (const chunk of req) {
                received += chunk.length;
                if (received > 256 * 1024) {
                    req.resume();
                    reply(413, "REQUEST_TOO_LARGE", "Request exceeds 256 KiB");
                    return;
                }
                chunks.push(chunk);
            }
            body = Buffer.concat(chunks);
        }
        try {
            const backendRes = await fetch(
                `${parsedBackend.origin}/tegaki/manga/resources/${engine}/lora/${isValidate ? "validate" : "index"}`,
                { method: expectedMethod, body, headers: isValidate ? { "Content-Type": "application/json" } : undefined,
                  signal: AbortSignal.timeout(20000) }
            );
            const chunks = [];
            let size = 0;
            for await (const chunk of backendRes.body) {
                size += chunk.length;
                if (size > 16 * 1024 * 1024) {
                    reply(502, "BACKEND_INVALID_RESPONSE", "Backend response exceeds 16 MiB");
                    return;
                }
                chunks.push(chunk);
            }
            let data;
            try {
                data = JSON.parse(Buffer.concat(chunks).toString("utf8"));
            } catch {
                reply(502, "BACKEND_INVALID_RESPONSE", "Backend returned invalid JSON");
                return;
            }
            const valid = data && typeof data === "object" && !Array.isArray(data) && (backendRes.ok
                ? data.ok === true && Array.isArray(data.entries) && (!isValidate || Array.isArray(data.chain))
                : data.ok === false && typeof data.error === "string");
            if (!valid) {
                reply(502, "BACKEND_INVALID_RESPONSE", "Backend response is missing required fields");
                return;
            }
            res.writeHead(backendRes.status, { "Content-Type": "application/json; charset=utf-8" });
            res.end(JSON.stringify(data));
        } catch (err) {
            reply(502, err.name === "TimeoutError" ? "BACKEND_TIMEOUT" : "BACKEND_UNAVAILABLE",
                err.name === "TimeoutError" ? "Backend LoRA request timed out" : "Backend LoRA request failed");
        }
        return;
    }

    // LoRA preview sidecar bytes (Card MANGA-PROMPT-ASSIST-PRODUCTION1).
    // Addressed by canonical LoRA ID only; the backend derives <stem>.preview.png inside the engine root.
    if (pathname === "/api/manga/resources/lora/preview") {
        const reply = (status, error_code, error) => {
            res.writeHead(status, { "Content-Type": "application/json; charset=utf-8" });
            res.end(JSON.stringify({ ok: false, error_code, error }));
        };
        if (req.method !== "GET") {
            reply(405, "METHOD_NOT_ALLOWED", "Use GET");
            return;
        }
        if ((requestOrigin && !allowedLocalOrigins.has(requestOrigin)) ||
            (req.headers["sec-fetch-site"] && !["same-origin", "none"].includes(req.headers["sec-fetch-site"]))) {
            reply(403, "ORIGIN_FORBIDDEN", "Request origin is not the Manga workspace");
            return;
        }
        const engine = url.searchParams.get("engine") || "illustrious";
        const id = url.searchParams.get("id") || "";
        if (!["illustrious"].includes(engine)) {
            reply(404, "RESOURCE_UNSUPPORTED", `No LoRA resource is registered for engine '${engine}'`);
            return;
        }
        if (!id || id.length > 1024) {
            reply(400, "INVALID_RESOURCE_ID", "LoRA ID is missing or too long");
            return;
        }
        try {
            const backendRes = await fetch(
                `${parsedBackend.origin}/tegaki/manga/resources/${engine}/lora/preview?id=${encodeURIComponent(id)}`,
                { method: "GET", signal: AbortSignal.timeout(10000) }
            );
            const chunks = [];
            let size = 0;
            for await (const chunk of backendRes.body) {
                size += chunk.length;
                if (size > 16 * 1024 * 1024) {
                    reply(502, "BACKEND_INVALID_RESPONSE", "Preview exceeds 16 MiB");
                    return;
                }
                chunks.push(chunk);
            }
            const body = Buffer.concat(chunks);
            const type = (backendRes.headers.get("content-type") || "").split(";")[0].trim().toLowerCase();
            if (backendRes.ok) {
                // The sidecar is named *.preview.png but legacy assets may hold JPEG bytes:
                // the type must match the actual bytes, and must agree with the backend's.
                const sniffed = body.length >= 8 && body.subarray(0, 8).equals(Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a])) ? "image/png"
                    : body.length >= 3 && body[0] === 0xff && body[1] === 0xd8 && body[2] === 0xff ? "image/jpeg"
                    : body.length >= 12 && body.subarray(0, 4).toString("latin1") === "RIFF" && body.subarray(8, 12).toString("latin1") === "WEBP" ? "image/webp"
                    : null;
                if (!sniffed || type !== sniffed) {
                    reply(502, "BACKEND_INVALID_RESPONSE", "Backend preview is not a PNG, JPEG or WebP image");
                    return;
                }
                res.writeHead(200, { "Content-Type": sniffed, "Cache-Control": "private, max-age=300",
                    "X-Content-Type-Options": "nosniff" });
                res.end(body);
                return;
            }
            let data = null;
            try { data = JSON.parse(body.toString("utf8")); } catch { /* handled below */ }
            if (!data || data.ok !== false || typeof data.error !== "string") {
                reply(502, "BACKEND_INVALID_RESPONSE", "Backend response is missing required fields");
                return;
            }
            res.writeHead(backendRes.status, { "Content-Type": "application/json; charset=utf-8" });
            res.end(JSON.stringify({ ok: false, error_code: data.error_code || "BACKEND_REJECTED", error: data.error }));
        } catch (err) {
            reply(502, err.name === "TimeoutError" ? "BACKEND_TIMEOUT" : "BACKEND_UNAVAILABLE",
                err.name === "TimeoutError" ? "Backend LoRA preview timed out" : "Backend LoRA preview failed");
        }
        return;
    }

    // Engine-scoped LoRA browse (Card MANGA-ILLUSTRIOUS-LORA-PRODUCTION1).
    // One folder per request; the backend owns the root and canonical IDs.
    if (pathname === "/api/manga/resources/lora") {
        const reply = (status, error_code, error) => {
            res.writeHead(status, { "Content-Type": "application/json; charset=utf-8" });
            res.end(JSON.stringify({ ok: false, error_code, error }));
        };
        if (req.method !== "GET") {
            reply(405, "METHOD_NOT_ALLOWED", "Use GET");
            return;
        }
        if ((requestOrigin && !allowedLocalOrigins.has(requestOrigin)) ||
            (req.headers["sec-fetch-site"] && !["same-origin", "none"].includes(req.headers["sec-fetch-site"]))) {
            reply(403, "ORIGIN_FORBIDDEN", "Request origin is not the Manga workspace");
            return;
        }
        const engine = url.searchParams.get("engine") || "illustrious";
        const dir = url.searchParams.get("dir") || "";
        if (!["illustrious"].includes(engine)) {
            reply(404, "RESOURCE_UNSUPPORTED", `No LoRA resource is registered for engine '${engine}'`);
            return;
        }
        if (dir.length > 1024) {
            reply(400, "INVALID_RESOURCE_ID", "Folder ID is too long");
            return;
        }
        try {
            const backendRes = await fetch(
                `${parsedBackend.origin}/tegaki/manga/resources/${engine}/lora?dir=${encodeURIComponent(dir)}`,
                { method: "GET", signal: AbortSignal.timeout(10000) }
            );
            const chunks = [];
            let size = 0;
            for await (const chunk of backendRes.body) {
                size += chunk.length;
                if (size > 4 * 1024 * 1024) {
                    reply(502, "BACKEND_INVALID_RESPONSE", "Backend response exceeds 4 MiB");
                    return;
                }
                chunks.push(chunk);
            }
            let data;
            try {
                data = JSON.parse(Buffer.concat(chunks).toString("utf8"));
            } catch {
                reply(502, "BACKEND_INVALID_RESPONSE", "Backend returned invalid JSON");
                return;
            }
            const valid = data && typeof data === "object" && !Array.isArray(data) && (backendRes.ok
                ? data.ok === true && Array.isArray(data.folders) && Array.isArray(data.loras) && typeof data.folder === "string"
                : data.ok === false && typeof data.error === "string");
            if (!valid) {
                reply(502, "BACKEND_INVALID_RESPONSE", "Backend response is missing required fields");
                return;
            }
            res.writeHead(backendRes.status, { "Content-Type": "application/json; charset=utf-8" });
            res.end(JSON.stringify(data));
        } catch (err) {
            reply(502, err.name === "TimeoutError" ? "BACKEND_TIMEOUT" : "BACKEND_UNAVAILABLE",
                err.name === "TimeoutError" ? "Backend LoRA browse timed out" : "Backend LoRA browse failed");
        }
        return;
    }

    // Compile-only isolated Scene preparation endpoint (Card MANGA-ISOLATED-SCENE-COMPILE-HTTP1)
    if (pathname === "/api/manga/generation/prepare-isolated-scene") {
        const reply = (status, error_code, error) => {
            res.writeHead(status, { "Content-Type": "application/json; charset=utf-8" });
            res.end(JSON.stringify({ ok: false, error_code, error }));
        };
        if (req.method !== "POST") {
            reply(405, "METHOD_NOT_ALLOWED", "Use POST");
            return;
        }
        if ((requestOrigin && !allowedLocalOrigins.has(requestOrigin)) ||
            (req.headers["sec-fetch-site"] && !["same-origin", "none"].includes(req.headers["sec-fetch-site"]))) {
            reply(403, "ORIGIN_FORBIDDEN", "Request origin is not the Manga workspace");
            return;
        }
        if ((req.headers["content-type"] || "").split(";")[0].trim().toLowerCase() !== "application/json") {
            reply(415, "INVALID_CONTENT_TYPE", "Content-Type must be application/json");
            return;
        }
        const declaredLength = Number(req.headers["content-length"]);
        if (req.headers["content-length"] && (!Number.isSafeInteger(declaredLength) || declaredLength > 256 * 1024)) {
            reply(413, "REQUEST_TOO_LARGE", "Request exceeds 256 KiB");
            return;
        }
        const chunks = [];
        let received = 0;
        for await (const chunk of req) {
            received += chunk.length;
            if (received > 256 * 1024) {
                req.resume();
                reply(413, "REQUEST_TOO_LARGE", "Request exceeds 256 KiB");
                return;
            }
            chunks.push(chunk);
        }
        let parsed;
        try {
            parsed = JSON.parse(Buffer.concat(chunks).toString("utf8"));
            if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
                throw new Error("Expected JSON object");
            }
        } catch (err) {
            reply(400, "INVALID_JSON", `Invalid JSON request: ${err.message}`);
            return;
        }

        // Strict rejection of forbidden client-supplied fields (Card Section 4)
        const FORBIDDEN_CLIENT_FIELDS = [
            "backend_url", "backend_origin", "snapshot_id", "job_id",
            "prompt_id", "manifest_id", "artifact_locator"
        ];
        const presentForbidden = FORBIDDEN_CLIENT_FIELDS.filter(f => f in parsed);
        if (presentForbidden.length > 0) {
            reply(400, "INVALID_REQUEST", `Forbidden client request fields: ${presentForbidden.join(", ")}`);
            return;
        }

        const prepInput = {
            authoring_document: parsed.authoring_document,
            scene_id: parsed.scene_id,
            generation_params: parsed.generation_params,
        };
        if (parsed.page_id !== undefined) prepInput.page_id = parsed.page_id;
        if (parsed.page_index !== undefined) prepInput.page_index = parsed.page_index;
        if (parsed.local_dimensions !== undefined) prepInput.local_dimensions = parsed.local_dimensions;
        if (parsed.random_seed !== undefined) prepInput.random_seed = parsed.random_seed;

        try {
            const bundle = await isolatedScenePrepService.prepareIsolatedScene(prepInput);
            res.writeHead(200, { "Content-Type": "application/json; charset=utf-8" });
            res.end(JSON.stringify({ ok: true, ...bundle }));
        } catch (error) {
            if (error instanceof IsolatedScenePrepError) {
                const status = Number.isInteger(error.status) && error.status >= 400 && error.status < 600
                    ? error.status
                    : 500;
                reply(status, error.code || "PREPARATION_FAILED", sanitizeErrorMessage(error.message));
            } else {
                console.error(`[MangaWorkspaceServer] Isolated scene prep internal error: ${error?.stack || error}`);
                reply(500, "PREPARATION_INTERNAL_ERROR", "Isolated scene preparation failed unexpectedly");
            }
        }
        return;
    }

    // Isolated Scene Prompt Dispatch endpoint (Card MANGA-ISOLATED-SCENE-DISPATCH1)
    if (pathname === "/api/manga/generation/dispatch-isolated-scene") {
        const reply = (status, error_code, error) => {
            res.writeHead(status, { "Content-Type": "application/json; charset=utf-8" });
            res.end(JSON.stringify({ ok: false, error_code, error }));
        };
        if (req.method !== "POST") {
            reply(405, "METHOD_NOT_ALLOWED", "Use POST");
            return;
        }
        if ((requestOrigin && !allowedLocalOrigins.has(requestOrigin)) ||
            (req.headers["sec-fetch-site"] && !["same-origin", "none"].includes(req.headers["sec-fetch-site"]))) {
            reply(403, "ORIGIN_FORBIDDEN", "Request origin is not the Manga workspace");
            return;
        }
        if ((req.headers["content-type"] || "").split(";")[0].trim().toLowerCase() !== "application/json") {
            reply(415, "INVALID_CONTENT_TYPE", "Content-Type must be application/json");
            return;
        }
        const declaredLength = Number(req.headers["content-length"]);
        if (req.headers["content-length"] && (!Number.isSafeInteger(declaredLength) || declaredLength > 256 * 1024)) {
            reply(413, "REQUEST_TOO_LARGE", "Request exceeds 256 KiB");
            return;
        }
        const chunks = [];
        let received = 0;
        for await (const chunk of req) {
            received += chunk.length;
            if (received > 256 * 1024) {
                req.resume();
                reply(413, "REQUEST_TOO_LARGE", "Request exceeds 256 KiB");
                return;
            }
            chunks.push(chunk);
        }
        let parsed;
        try {
            parsed = JSON.parse(Buffer.concat(chunks).toString("utf8"));
            if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
                throw new Error("Expected JSON object");
            }
        } catch (err) {
            reply(400, "INVALID_JSON", `Invalid JSON request: ${err.message}`);
            return;
        }
        try {
            const job = await generationService.createIsolatedSceneJob(parsed);
            res.writeHead(202, { "Content-Type": "application/json; charset=utf-8" });
            res.end(JSON.stringify({ ok: true, job }));
        } catch (error) {
            if (error instanceof GenerationServiceError || error instanceof JournalError) {
                reply(error.status || 503, error.code, sanitizeErrorMessage(error.message));
            } else {
                console.error(`[MangaWorkspaceServer] Isolated scene dispatch internal error: ${error?.stack || error}`);
                reply(500, "DISPATCH_INTERNAL_ERROR", "Isolated scene dispatch failed unexpectedly");
            }
        }
        return;
    }

        // =========================================================================
    // PAGE COMPOSITE HTTP ROUTES (Card MANGA-WORKSPACE-PAGE-COMPOSITE-HTTP1)
    // =========================================================================

    const PAGE_COMPOSITE_PREFIX = "/api/manga/page-composites";
    if (pathname === PAGE_COMPOSITE_PREFIX || pathname.startsWith(PAGE_COMPOSITE_PREFIX + "/")) {
        const reply = (status, error_code, error) => {
            res.writeHead(status, { "Content-Type": "application/json; charset=utf-8" });
            res.end(JSON.stringify({ ok: false, error_code, error: sanitizeErrorMessage(error) }));
        };

        // Origin & sec-fetch-site policy (reuse existing server policy)
        if ((requestOrigin && !allowedLocalOrigins.has(requestOrigin)) ||
            (req.headers["sec-fetch-site"] && !["same-origin", "none"].includes(req.headers["sec-fetch-site"]))) {
            reply(403, "ORIGIN_FORBIDDEN", "Request origin is not the Manga workspace");
            return;
        }

        // Helper to parse JSON body with standard 256 KiB limit
        const parseJsonBody = async () => {
            if ((req.headers["content-type"] || "").split(";")[0].trim().toLowerCase() !== "application/json") {
                reply(415, "INVALID_CONTENT_TYPE", "Content-Type must be application/json");
                return null;
            }
            const declaredLength = Number(req.headers["content-length"]);
            if (req.headers["content-length"] && (!Number.isSafeInteger(declaredLength) || declaredLength > 256 * 1024)) {
                reply(413, "REQUEST_TOO_LARGE", "Request exceeds 256 KiB");
                return null;
            }
            const chunks = [];
            let received = 0;
            for await (const chunk of req) {
                received += chunk.length;
                if (received > 256 * 1024) {
                    req.resume();
                    reply(413, "REQUEST_TOO_LARGE", "Request exceeds 256 KiB");
                    return null;
                }
                chunks.push(chunk);
            }
            try {
                const parsed = JSON.parse(Buffer.concat(chunks).toString("utf8"));
                if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
                    throw new Error("Expected JSON object");
                }
                return parsed;
            } catch (err) {
                reply(400, "INVALID_JSON", `Invalid JSON request: ${err.message}`);
                return null;
            }
        };

        const UUID_V4_REGEX = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

        // A. COMPOSE + PERSIST: POST /api/manga/page-composites/compose
        if (pathname === `${PAGE_COMPOSITE_PREFIX}/compose`) {
            if (req.method !== "POST") {
                reply(405, "METHOD_NOT_ALLOWED", "Use POST");
                return;
            }
            const parsed = await parseJsonBody();
            if (parsed === null) return;

            // Strict Trust Boundary: Reject forbidden client fields (Card Section 8)
            const FORBIDDEN_COMPOSE_FIELDS = [
                "composition_plan", "composite_bytes", "composite_id",
                "manifest", "artifact_ref", "content_digest",
                "backend_url", "backend_origin", "output_path",
                "store_root", "index_root"
            ];
            const presentForbidden = FORBIDDEN_COMPOSE_FIELDS.filter(f => f in parsed);
            if (presentForbidden.length > 0) {
                reply(400, "INVALID_REQUEST", `Forbidden client request fields: ${presentForbidden.join(", ")}`);
                return;
            }

            try {
                const result = await pageCompositePersistService.persistCurrentPageComposite(parsed);
                res.writeHead(200, { "Content-Type": "application/json; charset=utf-8" });
                res.end(JSON.stringify({ ok: true, ...result }));
            } catch (error) {
                let status = 500;
                let code = error.code || "PERSIST_FAILED";
                if (error instanceof PageCompositePersistError) {
                    if (error.code === "INVALID_REQUEST" || error.code === "FORBIDDEN_CALLER_FIELD") {
                        status = 400;
                    } else if (error.code === "BRIDGE_COMPOSE_FAILED") {
                        status = 502;
                    } else if (error.code === "STORE_SAVE_FAILED" || error.code === "PERSISTED_COMPOSITE_INCONSISTENT" || error.code === "COMPOSITE_INDEX_PUBLICATION_FAILED") {
                        status = 500;
                    }
                }
                reply(status, code, error.message);
            }
            return;
        }

        // B. PAGE HISTORY: GET /api/manga/page-composites
        if (pathname === PAGE_COMPOSITE_PREFIX) {
            if (req.method !== "GET") {
                reply(405, "METHOD_NOT_ALLOWED", "Use GET");
                return;
            }
            const document_id = url.searchParams.get("document_id");
            const page_id = url.searchParams.get("page_id");
            const composition_plan_digest = url.searchParams.get("composition_plan_digest") || null;

            if (!document_id || !page_id) {
                reply(400, "INVALID_QUERY", "document_id and page_id query parameters are required");
                return;
            }

            try {
                const entries = await pageCompositeIndex.listByPage({
                    document_id,
                    page_id,
                    composition_plan_digest: composition_plan_digest || undefined,
                });
                res.writeHead(200, { "Content-Type": "application/json; charset=utf-8" });
                res.end(JSON.stringify({ ok: true, entries }));
            } catch (error) {
                reply(500, error.code || "HISTORY_LOOKUP_FAILED", error.message);
            }
            return;
        }

        // D. ARTIFACT: GET /api/manga/page-composites/:composite_id/artifact
        const artifactMatch = pathname.match(/^\/api\/manga\/page-composites\/([^\/]+)\/artifact$/);
        if (artifactMatch) {
            if (req.method !== "GET") {
                reply(405, "METHOD_NOT_ALLOWED", "Use GET");
                return;
            }
            const compositeId = artifactMatch[1];
            if (!UUID_V4_REGEX.test(compositeId)) {
                reply(400, "INVALID_COMPOSITE_ID", `composite_id must be a valid UUIDv4 string, got '${compositeId}'`);
                return;
            }

            try {
                const bytes = await pageCompositeStore.getArtifactBytes(compositeId, { required: true });
                res.writeHead(200, {
                    "Content-Type": "image/png",
                    "Content-Length": bytes.length,
                });
                res.end(bytes);
            } catch (error) {
                if (error instanceof PageCompositeStoreError) {
                    if (error.code === "COMPOSITE_NOT_FOUND" || error.code === "ARTIFACT_NOT_FOUND") {
                        reply(404, "ARTIFACT_NOT_FOUND", `Artifact for composite '${compositeId}' not found`);
                        return;
                    }
                    if (error.code === "ARTIFACT_CORRUPT" || error.code === "COMPOSITE_CORRUPT") {
                        reply(500, "ARTIFACT_CORRUPT", error.message);
                        return;
                    }
                }
                reply(500, error.code || "ARTIFACT_RETRIEVAL_FAILED", error.message);
            }
            return;
        }

        // E. CURRENTNESS: POST /api/manga/page-composites/:composite_id/currentness
        const currentnessMatch = pathname.match(/^\/api\/manga\/page-composites\/([^\/]+)\/currentness$/);
        if (currentnessMatch) {
            if (req.method !== "POST") {
                reply(405, "METHOD_NOT_ALLOWED", "Use POST");
                return;
            }
            const compositeId = currentnessMatch[1];
            if (!UUID_V4_REGEX.test(compositeId)) {
                reply(400, "INVALID_COMPOSITE_ID", `composite_id must be a valid UUIDv4 string, got '${compositeId}'`);
                return;
            }
            const parsed = await parseJsonBody();
            if (parsed === null) return;

            try {
                const result = await pageCompositeCurrentClassifier.classifyCurrentPageComposite({
                    composite_id: compositeId,
                    authoring_document: parsed.authoring_document,
                    generation_params: parsed.generation_params,
                    page_id: parsed.page_id,
                    page_index: parsed.page_index,
                });
                res.writeHead(200, { "Content-Type": "application/json; charset=utf-8" });
                res.end(JSON.stringify({ ok: true, ...result }));
            } catch (error) {
                const status = (error instanceof PageCompositeCurrentError && (error.code === "INVALID_REQUEST" || error.code === "FORBIDDEN_CALLER_FIELD"))
                    ? 400
                    : 500;
                reply(status, error.code || "CURRENTNESS_FAILED", error.message);
            }
            return;
        }

        // C. COMPOSITE METADATA: GET /api/manga/page-composites/:composite_id
        const metadataMatch = pathname.match(/^\/api\/manga\/page-composites\/([^\/]+)$/);
        if (metadataMatch) {
            if (req.method !== "GET") {
                reply(405, "METHOD_NOT_ALLOWED", "Use GET");
                return;
            }
            const compositeId = metadataMatch[1];
            if (!UUID_V4_REGEX.test(compositeId)) {
                reply(400, "INVALID_COMPOSITE_ID", `composite_id must be a valid UUIDv4 string, got '${compositeId}'`);
                return;
            }

            try {
                const manifest = await pageCompositeStore.getManifest(compositeId, { required: true });
                const entry = await pageCompositeIndex.getEntry(compositeId);
                res.writeHead(200, { "Content-Type": "application/json; charset=utf-8" });
                res.end(JSON.stringify({ ok: true, composite_id: compositeId, manifest, entry }));
            } catch (error) {
                if (error instanceof PageCompositeStoreError && error.code === "COMPOSITE_NOT_FOUND") {
                    reply(404, "COMPOSITE_NOT_FOUND", `Composite '${compositeId}' not found`);
                    return;
                }
                reply(500, error.code || "COMPOSITE_LOOKUP_FAILED", error.message);
            }
            return;
        }
    }

    // Wildcard source preview (Card MANGA-WILDCARD-AUTOCOMPLETE-PRODUCTION1).
    // Read-only, bounded, addressed by the same canonical name the listing emits
    // ("nested/leaf" -> <root>/nested/leaf.txt). Never expands, never writes.
    // Explicit Wildcard Expand (Card MANGA-PROMPT-VALIDATION-COHERENCE1): ONE concrete expansion
    // produced by the backend's existing dynamicprompts owner; the workspace never parses wildcards.
    if (pathname === "/api/manga/wildcards/expand") {
        const reply = (status, error_code, error) => {
            res.writeHead(status, { "Content-Type": "application/json; charset=utf-8" });
            res.end(JSON.stringify({ ok: false, error_code, error }));
        };
        if (req.method !== "POST") {
            reply(405, "METHOD_NOT_ALLOWED", "Use POST");
            return;
        }
        if ((requestOrigin && !allowedLocalOrigins.has(requestOrigin)) ||
            (req.headers["sec-fetch-site"] && !["same-origin", "none"].includes(req.headers["sec-fetch-site"]))) {
            reply(403, "ORIGIN_FORBIDDEN", "Request origin is not the Manga workspace");
            return;
        }
        if ((req.headers["content-type"] || "").split(";")[0].trim().toLowerCase() !== "application/json") {
            reply(415, "INVALID_CONTENT_TYPE", "Content-Type must be application/json");
            return;
        }
        const chunks = [];
        let received = 0;
        for await (const chunk of req) {
            received += chunk.length;
            if (received > 16 * 1024) {
                req.resume();
                reply(413, "REQUEST_TOO_LARGE", "Request exceeds 16 KiB");
                return;
            }
            chunks.push(chunk);
        }
        let name;
        try { name = JSON.parse(Buffer.concat(chunks).toString("utf8"))?.name; } catch { name = undefined; }
        if (typeof name !== "string" || !name || name.length > 512) {
            reply(400, "INVALID_WILDCARD_NAME", "Wildcard name is required");
            return;
        }
        try {
            const backendRes = await fetch(`${parsedBackend.origin}/tegaki/manga/wildcards/expand`, {
                method: "POST", headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ name }), signal: AbortSignal.timeout(20000),
            });
            const text = await backendRes.text();
            if (text.length > 1024 * 1024) {
                reply(502, "BACKEND_INVALID_RESPONSE", "Backend response exceeds 1 MiB");
                return;
            }
            let data;
            try { data = JSON.parse(text); } catch {
                reply(backendRes.status === 404 ? 503 : 502, "BACKEND_INVALID_RESPONSE",
                    backendRes.status === 404 ? "Backend does not provide Wildcard expansion (restart the Manga backend)" : "Backend returned invalid JSON");
                return;
            }
            const valid = data && typeof data === "object" && (backendRes.ok
                ? data.ok === true && typeof data.expanded_text === "string" && typeof data.name === "string"
                : data.ok === false && typeof data.error === "string");
            if (!valid) {
                reply(502, "BACKEND_INVALID_RESPONSE", "Backend response is missing required fields");
                return;
            }
            res.writeHead(backendRes.status, { "Content-Type": "application/json; charset=utf-8", "Cache-Control": "no-store" });
            res.end(JSON.stringify(backendRes.ok
                ? { ok: true, name: data.name, token: `__${data.name}__`, expanded_text: data.expanded_text,
                    used_wildcards: Array.isArray(data.used_wildcards) ? data.used_wildcards : [] }
                : { ok: false, error_code: data.error_code, error: data.error }));
        } catch (err) {
            reply(502, err.name === "TimeoutError" ? "BACKEND_TIMEOUT" : "BACKEND_UNAVAILABLE",
                err.name === "TimeoutError" ? "Backend Wildcard expansion timed out" : "Backend Wildcard expansion failed");
        }
        return;
    }

    if (pathname === "/api/manga/wildcards/preview") {
        const reply = (status, error_code, error) => {
            res.writeHead(status, { "Content-Type": "application/json; charset=utf-8" });
            res.end(JSON.stringify({ ok: false, error_code, error }));
        };
        if (req.method !== "GET") {
            reply(405, "METHOD_NOT_ALLOWED", "Use GET");
            return;
        }
        if ((requestOrigin && !allowedLocalOrigins.has(requestOrigin)) ||
            (req.headers["sec-fetch-site"] && !["same-origin", "none"].includes(req.headers["sec-fetch-site"]))) {
            reply(403, "ORIGIN_FORBIDDEN", "Request origin is not the Manga workspace");
            return;
        }
        const name = (url.searchParams.get("name") || "").replaceAll("\\", "/");
        // Same name rule as the listing below; anything else fails closed.
        if (!name || name.length > 512 || name.startsWith("/") ||
            name.split("/").some(part => !part || part === "." || part === "..") ||
            /[\x00-\x1f\x7f<>#$:*?\[\]]/.test(name)) {
            reply(400, "INVALID_WILDCARD_NAME", "Wildcard name must be a canonical relative name");
            return;
        }
        try {
            const configured = (process.env.TEGAKI_MANGA_WILDCARDS_DIR || "").trim();
            const root = fs.realpathSync(configured ? path.resolve(configured) : path.resolve(__dirname, "..", "wildcards"));
            const candidate = path.resolve(root, ...name.split("/")) + ".txt";
            if (!fs.existsSync(candidate)) {
                reply(404, "WILDCARD_NOT_FOUND", `Wildcard '${name}' does not exist`);
                return;
            }
            const real = fs.realpathSync(candidate);
            const rel = path.relative(root, real);
            if (!rel || rel.startsWith("..") || path.isAbsolute(rel) || !fs.statSync(real).isFile()) {
                reply(400, "INVALID_WILDCARD_NAME", "Wildcard is outside the wildcard root");
                return;
            }
            const MAX_BYTES = 1024 * 1024;
            const size = fs.statSync(real).size;
            const handle = fs.openSync(real, "r");
            let text;
            try {
                const buffer = Buffer.alloc(Math.min(size, MAX_BYTES));
                fs.readSync(handle, buffer, 0, buffer.length, 0);
                text = buffer.toString("utf8");
            } finally {
                fs.closeSync(handle);
            }
            const truncated = size > MAX_BYTES;
            // Usable entries follow dynamicprompts' text-wildcard rule: one entry per
            // line, stripped, skipping blank lines and '#' comment lines.
            const entries = text.replace(/^﻿/, "").split(/\r?\n/).map(line => line.trim())
                .filter(line => line && !line.startsWith("#"));
            if (truncated && entries.length) entries.pop(); // a cut-off last line is not an entry
            // Every usable entry within the read cap is returned (no sample limit); the
            // UI shows them all.  Past the cap the true total is unknown -> null.
            res.writeHead(200, { "Content-Type": "application/json; charset=utf-8", "Cache-Control": "no-store" });
            res.end(JSON.stringify({ ok: true, name, token: `__${name}__`, entries,
                shown: entries.length, total: truncated ? null : entries.length, truncated,
                max_bytes: MAX_BYTES }));
        } catch (err) {
            reply(500, "WILDCARD_PREVIEW_FAILED", "Failed to read wildcard preview");
        }
        return;
    }

    // Manga Wildcard Discovery
    if (pathname === "/api/manga/wildcards") {
        if (req.method !== "GET") {
            res.writeHead(405, { "Content-Type": "application/json; charset=utf-8" });
            res.end(JSON.stringify({ ok: false, error_code: "METHOD_NOT_ALLOWED", error: "Use GET" }));
            return;
        }
        if ((requestOrigin && !allowedLocalOrigins.has(requestOrigin)) ||
            (req.headers["sec-fetch-site"] && !["same-origin", "none"].includes(req.headers["sec-fetch-site"]))) {
            res.writeHead(403, { "Content-Type": "application/json; charset=utf-8" });
            res.end(JSON.stringify({ ok: false, error_code: "ORIGIN_FORBIDDEN", error: "Request origin is not the Manga workspace" }));
            return;
        }
        try {
            const configured = (process.env.TEGAKI_MANGA_WILDCARDS_DIR || "").trim();
            const root = configured ? path.resolve(configured) : path.resolve(__dirname, "..", "wildcards");
            if (!fs.existsSync(root) || !fs.statSync(root).isDirectory()) {
                res.writeHead(200, { "Content-Type": "application/json; charset=utf-8" });
                res.end(JSON.stringify({ ok: true, wildcards: [], root_available: false }));
                return;
            }
            const wildcards = [];
            const walk = dir => {
                const entries = fs.readdirSync(dir, { withFileTypes: true });
                for (const entry of entries) {
                    const fullPath = path.join(dir, entry.name);
                    if (entry.isDirectory()) {
                        walk(fullPath);
                    } else if (entry.isFile() && entry.name.toLowerCase().endsWith(".txt")) {
                        const rel = path.relative(root, fullPath).replaceAll("\\", "/");
                        const name = rel.slice(0, -4);
                        if (!name || name.includes("..") || /[\x00-\x1f\x7f<>#$:*?\[\]]/.test(name)) {
                            continue;
                        }
                        wildcards.push(name);
                    }
                }
            };
            walk(root);
            wildcards.sort();
            res.writeHead(200, { "Content-Type": "application/json; charset=utf-8" });
            res.end(JSON.stringify({ ok: true, wildcards, root_available: true }));
        } catch (err) {
            res.writeHead(500, { "Content-Type": "application/json; charset=utf-8" });
            res.end(JSON.stringify({ ok: false, error_code: "WILDCARD_ENUMERATION_FAILED", error: "Failed to list wildcards: " + err.message }));
        }
        return;
    }
    // PLAY1b: Manga-owned job API; graph, backend URL, and output paths are never client inputs.
    if (/^\/api\/manga\/generation\/jobs(?:\/|$)/.test(pathname)) {
        const pieces = pathname.split("/").filter(Boolean);
        const collection = pieces.length === 4;
        const result = pieces.length === 6 && pieces[5] === "result";
        const item = pieces.length === 5 || result;
        const reply = (status, code, message) => {
            res.writeHead(status, { "Content-Type": "application/json; charset=utf-8" });
            res.end(JSON.stringify({ ok: false, error_code: code, error: message }));
        };
        if (!collection && !item) {
            reply(404, "ROUTE_NOT_FOUND", "Unknown Manga job route");
            return;
        }
        if (req.method !== (collection ? "POST" : "GET")) {
            reply(405, "METHOD_NOT_ALLOWED", `Use ${collection ? "POST" : "GET"}`);
            return;
        }
        if ((requestOrigin && !allowedLocalOrigins.has(requestOrigin)) ||
            (req.headers["sec-fetch-site"] && !["same-origin", "none"].includes(req.headers["sec-fetch-site"]))) {
            reply(403, "ORIGIN_FORBIDDEN", "Request origin is not the Manga workspace");
            return;
        }
        try {
            if (collection) {
                if ((req.headers["content-type"] || "").split(";")[0].trim().toLowerCase() !== "application/json") {
                    reply(415, "INVALID_CONTENT_TYPE", "Content-Type must be application/json");
                    return;
                }
                const declared = Number(req.headers["content-length"]);
                if (req.headers["content-length"] && (!Number.isSafeInteger(declared) || declared > 256 * 1024)) {
                    reply(413, "REQUEST_TOO_LARGE", "Manga job request exceeds 256 KiB");
                    return;
                }
                const chunks = [];
                let size = 0;
                for await (const chunk of req) {
                    size += chunk.length;
                    if (size > 256 * 1024) {
                        req.resume();
                        reply(413, "REQUEST_TOO_LARGE", "Manga job request exceeds 256 KiB");
                        return;
                    }
                    chunks.push(chunk);
                }
                let body;
                try {
                    body = JSON.parse(Buffer.concat(chunks).toString("utf8"));
                } catch {
                    reply(400, "INVALID_JSON", "Manga job request is not valid JSON");
                    return;
                }
                const isIsolatedScene = body?.mode === "isolated_scene" || body?.settings?.mode === "isolated_scene";
                const job = isIsolatedScene
                    ? await generationService.createIsolatedSceneJob(body)
                    : (body?.settings?.mode === "scene"
                        ? await generationService.createSceneJob(body)
                        : await generationService.createJob(body));
                res.writeHead(202, { "Content-Type": "application/json; charset=utf-8" });
                res.end(JSON.stringify({ ok: true, job }));
            } else if (result) {
                const bytes = await generationService.getResult(pieces[4]);
                res.writeHead(200, { "Content-Type": "image/png", "Cache-Control": "no-store" });
                res.end(bytes);
            } else {
                const job = await generationService.getJob(pieces[4]);
                res.writeHead(200, { "Content-Type": "application/json; charset=utf-8" });
                res.end(JSON.stringify({ ok: true, job }));
            }
        } catch (error) {
            if (error instanceof GenerationServiceError || error instanceof JournalError) {
                reply(error.status || 503, error.code, error.message);
            } else {
                console.error(`[MangaWorkspaceServer] Manga job internal error: ${error?.stack || error}`);
                reply(500, "MANGA_JOB_INTERNAL_ERROR", "Manga job service failed");
            }
        }
        return;
    }
    // 1. Restricted Bounded Proxy to Manga Backend (Card Section 4, 6)
    if (pathname === "/api/proxy") {
        let requestedPath = url.searchParams.get("path");
        const requestedTarget = url.searchParams.get("target");

        // Resolve requested path from ?path or ?target
        if (!requestedPath && requestedTarget) {
            try {
                const parsedTarget = new URL(requestedTarget);
                // Reject different origins, non-loopback, unexpected schemes (Card Section 4)
                if (parsedTarget.origin !== parsedBackend.origin) {
                    res.writeHead(403, { "Content-Type": "application/json" });
                    res.end(JSON.stringify({
                        ok: false,
                        error: `Forbidden: target origin '${parsedTarget.origin}' does not match configured backend origin '${parsedBackend.origin}'`
                    }));
                    return;
                }
                requestedPath = parsedTarget.pathname;
            } catch (err) {
                res.writeHead(400, { "Content-Type": "application/json" });
                res.end(JSON.stringify({ ok: false, error: "Invalid target URL: " + err.message }));
                return;
            }
        }

        if (!requestedPath) {
            res.writeHead(400, { "Content-Type": "application/json" });
            res.end(JSON.stringify({ ok: false, error: "Missing required 'path' or 'target' query parameter" }));
            return;
        }

        // Validate requested path against whitelist
        if (!ALLOWED_PROXY_PATHS.has(requestedPath)) {
            res.writeHead(403, { "Content-Type": "application/json" });
            res.end(JSON.stringify({
                ok: false,
                error: `Forbidden: path '${requestedPath}' is not an authorized Manga backend endpoint`
            }));
            return;
        }

        const resolvedTarget = `${parsedBackend.origin}${requestedPath}`;
        try {
            const fetchOptions = {
                method: req.method,
                headers: { "Content-Type": req.headers["content-type"] || "application/json" }
            };
            if (req.method === "POST") {
                const chunks = [];
                for await (const chunk of req) chunks.push(chunk);
                fetchOptions.body = Buffer.concat(chunks).toString();
            }
            const proxyRes = await fetch(resolvedTarget, fetchOptions);
            res.writeHead(proxyRes.status, {
                "Content-Type": proxyRes.headers.get("content-type") || "application/json"
            });
            const data = await proxyRes.arrayBuffer();
            res.end(Buffer.from(data));
        } catch (err) {
            res.writeHead(502, { "Content-Type": "application/json" });
            res.end(JSON.stringify({ ok: false, error: "Proxy backend failure: " + err.message }));
        }
        return;
    }

    // 2. Dedicated Asset Ingestion Endpoints (Guides & References)
    if (pathname === "/api/guide-assets/upload" || pathname === "/api/reference-assets/upload") {
        const isReference = (pathname === "/api/reference-assets/upload");
        const targetSubfolder = isReference ? "tegaki_manga_references" : "tegaki_manga_guides";

        // Enforce POST method
        if (req.method !== "POST") {
            res.writeHead(405, { "Content-Type": "application/json" });
            res.end(JSON.stringify({ ok: false, error: "Method Not Allowed" }));
            return;
        }

        // Strict Origin Policy (Card Section 14)
        if (requestOrigin && !allowedLocalOrigins.has(requestOrigin)) {
            res.writeHead(403, { "Content-Type": "application/json" });
            res.end(JSON.stringify({ ok: false, error: `Forbidden origin '${requestOrigin}'` }));
            return;
        }

        // Filename Validation (Card Section 9)
        const rawFilename = url.searchParams.get("filename") || "";
        const filename = path.basename(rawFilename);
        if (
            !filename ||
            filename !== rawFilename ||
            filename.includes("/") ||
            filename.includes("\\") ||
            filename.includes("..") ||
            /[\x00-\x1f\x7f]/.test(filename) ||
            filename.length > 255
        ) {
            res.writeHead(400, { "Content-Type": "application/json" });
            res.end(JSON.stringify({ ok: false, error: "Invalid filename: must be a safe basename" }));
            return;
        }

        // Content-Length check (Card Section 8): max 20 MiB
        const MAX_BYTES = 20 * 1024 * 1024;
        const contentLengthHeader = req.headers["content-length"];
        if (contentLengthHeader) {
            const cl = parseInt(contentLengthHeader, 10);
            if (Number.isFinite(cl) && cl > MAX_BYTES) {
                res.writeHead(413, { "Connection": "close", "Content-Type": "application/json" });
                res.end(JSON.stringify({ ok: false, error: "Payload Too Large: exceeds 20 MiB limit" }));
                req.destroy();
                return;
            }
        }

        // Buffer body with byte limit
        const chunks = [];
        let receivedBytes = 0;
        let tooLarge = false;

        const readSuccess = await new Promise((resolve) => {
            req.on("data", (chunk) => {
                if (tooLarge) return;
                receivedBytes += chunk.length;
                if (receivedBytes > MAX_BYTES) {
                    tooLarge = true;
                    res.writeHead(413, { "Connection": "close", "Content-Type": "application/json" });
                    res.end(JSON.stringify({ ok: false, error: "Payload Too Large: exceeds 20 MiB limit" }));
                    req.resume();
                    resolve(false);
                    return;
                }
                chunks.push(chunk);
            });

            req.on("end", () => {
                if (!tooLarge) resolve(true);
            });

            req.on("error", (err) => {
                if (!tooLarge) {
                    res.writeHead(500, { "Content-Type": "application/json" });
                    res.end(JSON.stringify({ ok: false, error: "Upload read error: " + err.message }));
                    resolve(false);
                }
            });
        });

        if (!readSuccess) {
            return;
        }

        const body = Buffer.concat(chunks);
        if (body.length === 0) {
            res.writeHead(400, { "Content-Type": "application/json" });
            res.end(JSON.stringify({ ok: false, error: "Empty upload body" }));
            return;
        }

        // Magic byte validation (Card Section 7)
        let detectedType = null;
        if (body.length >= 8 &&
            body[0] === 0x89 && body[1] === 0x50 && body[2] === 0x4E && body[3] === 0x47 &&
            body[4] === 0x0D && body[5] === 0x0A && body[6] === 0x1A && body[7] === 0x0A) {
            detectedType = "image/png";
        } else if (body.length >= 3 &&
            body[0] === 0xFF && body[1] === 0xD8 && body[2] === 0xFF) {
            detectedType = "image/jpeg";
        } else if (body.length >= 12 &&
            body.toString("ascii", 0, 4) === "RIFF" &&
            body.toString("ascii", 8, 12) === "WEBP") {
            detectedType = "image/webp";
        }

        if (!detectedType) {
            res.writeHead(400, { "Content-Type": "application/json" });
            res.end(JSON.stringify({ ok: false, error: "Invalid image format: signature does not match PNG, JPEG, or WEBP" }));
            return;
        }

        // Content-Type agreement validation (Card M1C2B1 Section 6)
        const reqContentType = (req.headers["content-type"] || "").split(";")[0].trim().toLowerCase();
        if (reqContentType !== detectedType) {
            res.writeHead(400, { "Content-Type": "application/json" });
            res.end(JSON.stringify({ ok: false, error: `Request Content-Type '${reqContentType}' does not agree with detected format '${detectedType}'` }));
            return;
        }

        // Extension match validation
        const ext = path.extname(filename).toLowerCase();
        const validExtensions = {
            "image/png": [".png"],
            "image/jpeg": [".jpg", ".jpeg"],
            "image/webp": [".webp"]
        };
        if (!validExtensions[detectedType]?.includes(ext)) {
            res.writeHead(400, { "Content-Type": "application/json" });
            res.end(JSON.stringify({ ok: false, error: `Filename extension '${ext}' does not match detected format '${detectedType}'` }));
            return;
        }

        // Stable asset naming for references (Card MANGA-CAST-REFERENCE-DATA1 Section 7)
        let uploadFilename = filename;
        if (isReference) {
            const hash = crypto.createHash("sha256").update(body).digest("hex").slice(0, 16);
            uploadFilename = `ref_${hash}${ext}`;
        }

        // Backend multipart forwarding (Card Section 10, 11)
        const backendUploadUrl = `${parsedBackend.origin}/upload/image`;
        try {
            const formData = new FormData();
            const blob = new Blob([body], { type: detectedType });
            formData.append("image", blob, uploadFilename);
            formData.append("subfolder", targetSubfolder);

            const backendRes = await fetch(backendUploadUrl, {
                method: "POST",
                body: formData
            });

            if (!backendRes.ok) {
                const errText = await backendRes.text();
                res.writeHead(backendRes.status, { "Content-Type": "application/json" });
                res.end(JSON.stringify({ ok: false, error: "Backend upload failed: " + errText }));
                return;
            }

            const backendJson = await backendRes.json();
            const returnedName = backendJson.name;
            const returnedSubfolder = backendJson.subfolder;

            // Validate backend response fields (Card M1C2B1 Section 12, 13)
            if (
                !returnedName ||
                typeof returnedName !== "string" ||
                returnedName.includes("/") ||
                returnedName.includes("\\") ||
                returnedName.includes("..") ||
                /[\x00-\x1f\x7f]/.test(returnedName) ||
                returnedName.length > 255 ||
                returnedSubfolder !== targetSubfolder
            ) {
                res.writeHead(502, { "Content-Type": "application/json" });
                res.end(JSON.stringify({ ok: false, error: "Backend response validation failed: unexpected subfolder or unsafe filename" }));
                return;
            }

            const canonicalRef = `${targetSubfolder}/${returnedName}`;
            res.writeHead(200, { "Content-Type": "application/json" });
            res.end(JSON.stringify({
                ok: true,
                asset_reference: canonicalRef
            }));
        } catch (err) {
            res.writeHead(502, { "Content-Type": "application/json" });
            res.end(JSON.stringify({ ok: false, error: "Failed to forward upload to backend: " + err.message }));
        }
        return;
    }

    // 3. Dedicated Asset Preview Endpoints (Guides & References)
    if (pathname === "/api/guide-assets/view" || pathname === "/api/reference-assets/view") {
        const isReference = (pathname === "/api/reference-assets/view");
        const targetSubfolder = isReference ? "tegaki_manga_references" : "tegaki_manga_guides";

        if (req.method !== "GET") {
            res.writeHead(405, { "Content-Type": "application/json" });
            res.end(JSON.stringify({ ok: false, error: "Method Not Allowed" }));
            return;
        }

        // Preview Origin Policy (Card M1C2B1 Section 15): If foreign Origin is present, reject with 403
        if (requestOrigin && !allowedLocalOrigins.has(requestOrigin)) {
            res.writeHead(403, { "Content-Type": "application/json" });
            res.end(JSON.stringify({ ok: false, error: `Forbidden origin '${requestOrigin}'` }));
            return;
        }

        const ref = url.searchParams.get("ref") || "";
        const expectedPrefix = `${targetSubfolder}/`;
        if (!ref.startsWith(expectedPrefix)) {
            res.writeHead(400, { "Content-Type": "application/json" });
            res.end(JSON.stringify({ ok: false, error: `Invalid ref: must start with '${expectedPrefix}'` }));
            return;
        }

        const relativeName = ref.slice(expectedPrefix.length);
        const basename = path.basename(relativeName);
        if (
            !basename ||
            basename !== relativeName ||
            basename.includes("/") ||
            basename.includes("\\") ||
            basename.includes("..") ||
            /[\x00-\x1f\x7f]/.test(basename)
        ) {
            res.writeHead(400, { "Content-Type": "application/json" });
            res.end(JSON.stringify({ ok: false, error: "Invalid ref: path traversal detected" }));
            return;
        }

        const backendViewUrl = new URL(`${parsedBackend.origin}/view`);
        backendViewUrl.searchParams.set("filename", basename);
        backendViewUrl.searchParams.set("subfolder", targetSubfolder);
        backendViewUrl.searchParams.set("type", "input");

        try {
            const backendRes = await fetch(backendViewUrl.toString(), { method: "GET" });
            if (!backendRes.ok) {
                res.writeHead(backendRes.status, { "Content-Type": "application/json" });
                res.end(JSON.stringify({ ok: false, error: `Backend view returned status ${backendRes.status}` }));
                return;
            }

            const ct = backendRes.headers.get("content-type") || "";
            const allowedViewTypes = ["image/png", "image/jpeg", "image/webp"];
            const isAllowedType = allowedViewTypes.some(t => ct.toLowerCase().startsWith(t));

            if (!isAllowedType) {
                res.writeHead(502, { "Content-Type": "application/json" });
                res.end(JSON.stringify({ ok: false, error: `Backend returned unexpected content type: ${ct}` }));
                return;
            }

            res.writeHead(200, { "Content-Type": ct });
            const imgData = await backendRes.arrayBuffer();
            res.end(Buffer.from(imgData));
        } catch (err) {
            res.writeHead(502, { "Content-Type": "application/json" });
            res.end(JSON.stringify({ ok: false, error: "Backend view request failed: " + err.message }));
        }
        return;
    }

    // 4. Positive Service Identity Endpoint (Card M1D1 Section 10)
    if (pathname === "/api/runtime/identity") {
        if (req.method !== "GET") {
            res.writeHead(405, { "Content-Type": "application/json" });
            res.end(JSON.stringify({ ok: false, error: "Method Not Allowed" }));
            return;
        }

        res.writeHead(200, { "Content-Type": "application/json; charset=utf-8" });
        res.end(JSON.stringify({
            service: "tegaki_manga_workspace",
            version: "1.0.0",
            domain: "manga",
            authoring_schema: "1.0.0",
            backend_target: parsedBackend.origin,
            pid: process.pid,
            source_digest: LOADED_SOURCE_DIGEST
        }));
        return;
    }

    // 5. Dedicated Reference-to-Identity Analysis Endpoint (Card MANGA-REFERENCE-TO-IDENTITY-INTEGRATION1)
    if (pathname === "/api/reference-assets/analyze") {
        if (req.method !== "POST") {
            res.writeHead(405, { "Content-Type": "application/json" });
            res.end(JSON.stringify({ ok: false, error: "Method Not Allowed" }));
            return;
        }

        if (requestOrigin && !allowedLocalOrigins.has(requestOrigin)) {
            res.writeHead(403, { "Content-Type": "application/json" });
            res.end(JSON.stringify({ ok: false, error: `Forbidden origin '${requestOrigin}'` }));
            return;
        }

        // Read JSON body (max 64 KiB)
        const MAX_BODY_BYTES = 64 * 1024;
        let bodyBuffer = "";
        let bodyTooLarge = false;

        const bodyReadSuccess = await new Promise((resolve) => {
            req.on("data", (chunk) => {
                if (bodyTooLarge) return;
                bodyBuffer += chunk.toString("utf8");
                if (bodyBuffer.length > MAX_BODY_BYTES) {
                    bodyTooLarge = true;
                    res.writeHead(413, { "Connection": "close", "Content-Type": "application/json" });
                    res.end(JSON.stringify({ ok: false, error: "Payload Too Large" }));
                    req.resume();
                    resolve(false);
                }
            });
            req.on("end", () => {
                if (!bodyTooLarge) resolve(true);
            });
            req.on("error", (err) => {
                if (!bodyTooLarge) {
                    res.writeHead(500, { "Content-Type": "application/json" });
                    res.end(JSON.stringify({ ok: false, error: "Read error: " + err.message }));
                    resolve(false);
                }
            });
        });

        if (!bodyReadSuccess) return;

        let parsedBody = {};
        if (bodyBuffer.trim()) {
            try {
                parsedBody = JSON.parse(bodyBuffer);
            } catch (err) {
                res.writeHead(400, { "Content-Type": "application/json" });
                res.end(JSON.stringify({ ok: false, error: "Invalid JSON body" }));
                return;
            }
        }

        const rawRef = parsedBody.asset_reference || parsedBody.ref || url.searchParams.get("ref") || "";
        if (!rawRef) {
            res.writeHead(400, { "Content-Type": "application/json" });
            res.end(JSON.stringify({ ok: false, error: "Missing required 'asset_reference' parameter" }));
            return;
        }

        const expectedPrefix = "tegaki_manga_references/";
        if (!rawRef.startsWith(expectedPrefix)) {
            res.writeHead(400, { "Content-Type": "application/json" });
            res.end(JSON.stringify({ ok: false, error: `Invalid ref: must start with '${expectedPrefix}'` }));
            return;
        }

        const relativeName = rawRef.slice(expectedPrefix.length);
        const basename = path.basename(relativeName);
        if (
            !basename ||
            basename !== relativeName ||
            basename.includes("/") ||
            basename.includes("\\") ||
            basename.includes("..") ||
            /[\x00-\x1f\x7f]/.test(basename)
        ) {
            res.writeHead(400, { "Content-Type": "application/json" });
            res.end(JSON.stringify({ ok: false, error: "Invalid ref: path traversal detected" }));
            return;
        }

        const ext = path.extname(basename).toLowerCase();
        if (![".png", ".jpg", ".jpeg", ".webp"].includes(ext)) {
            res.writeHead(400, { "Content-Type": "application/json" });
            res.end(JSON.stringify({ ok: false, error: "Unsupported image format: must be PNG, JPEG, or WEBP" }));
            return;
        }

        const targetDir = path.join(REPO_ROOT, "ComfyUI", "input", "tegaki_manga_references");
        const fullAssetPath = path.join(targetDir, basename);
        if (!fs.existsSync(fullAssetPath)) {
            res.writeHead(404, { "Content-Type": "application/json" });
            res.end(JSON.stringify({ ok: false, error: "Character Reference asset not found" }));
            return;
        }

        const pythonPath = fs.existsSync(EMBEDDED_PYTHON) ? EMBEDDED_PYTHON : (process.env.PYTHON_PATH || "python");

        try {
            const child = spawn(pythonPath, [ANALYZER_SCRIPT, "--asset", basename], {
                cwd: REPO_ROOT,
                windowsHide: true
            });

            let stdout = "";
            let stderr = "";

            child.stdout.on("data", (data) => {
                stdout += data.toString("utf8");
            });

            child.stderr.on("data", (data) => {
                stderr += data.toString("utf8");
            });

            const exitCode = await new Promise((resolve) => {
                child.on("close", resolve);
                child.on("error", (err) => {
                    stderr += "\nSpawn error: " + err.message;
                    resolve(-1);
                });
            });

            if (exitCode !== 0) {
                let errMsg = "Analysis subprocess failed";
                try {
                    const parsedErr = JSON.parse(stdout);
                    if (parsedErr.error) errMsg = parsedErr.error;
                } catch {
                    if (stderr.trim()) errMsg = stderr.trim().split("\n")[0];
                }
                const sanitizedErr = errMsg.replace(/[A-Za-z]:\\[^ \t\n\r"'\)]+/g, "[redacted-path]");
                res.writeHead(500, { "Content-Type": "application/json" });
                res.end(JSON.stringify({ ok: false, error: sanitizedErr }));
                return;
            }

            let resultJson;
            try {
                resultJson = JSON.parse(stdout);
            } catch (err) {
                res.writeHead(500, { "Content-Type": "application/json" });
                res.end(JSON.stringify({ ok: false, error: "Failed to parse analyzer response" }));
                return;
            }

            if (!resultJson.ok) {
                const sanitizedErr = (resultJson.error || "Analysis error").replace(/[A-Za-z]:\\[^ \t\n\r"'\)]+/g, "[redacted-path]");
                res.writeHead(500, { "Content-Type": "application/json" });
                res.end(JSON.stringify({ ok: false, error: sanitizedErr }));
                return;
            }

            res.writeHead(200, { "Content-Type": "application/json" });
            res.end(JSON.stringify({
                ok: true,
                candidate: resultJson.candidate,
                tags: resultJson.tags,
                ratings: resultJson.ratings,
                model: resultJson.model,
                execution_provider: resultJson.execution_provider
            }));
        } catch (spawnErr) {
            res.writeHead(500, { "Content-Type": "application/json" });
            res.end(JSON.stringify({ ok: false, error: "Failed to run analyzer: " + spawnErr.message.replace(/[A-Za-z]:\\[^ \t\n\r"'\)]+/g, "[redacted-path]") }));
        }
        return;
    }

    // 6. Static File Serving
    const safePath = path.normalize(path.join(APP_DIR, pathname));
    if (!safePath.startsWith(APP_DIR)) {
        res.writeHead(403);
        res.end("Forbidden");
        return;
    }

    if (!fs.existsSync(safePath) || fs.statSync(safePath).isDirectory()) {
        res.writeHead(404, { "Content-Type": "text/plain" });
        res.end("Not Found");
        return;
    }

    const ext = path.extname(safePath).toLowerCase();
    const contentType = MIME_TYPES[ext] || "application/octet-stream";

    res.writeHead(200, { "Content-Type": contentType });
    fs.createReadStream(safePath).pipe(res);
});

server.listen(PORT, HOST, () => {
    console.log(`[MangaWorkspaceServer] Serving on http://${HOST}:${PORT}`);
});

export { server, PORT, HOST, generationService };
