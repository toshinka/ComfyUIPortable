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
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const APP_DIR = path.resolve(__dirname, "..", "app");

const PORT = parseInt(process.env.MANGA_WORKSPACE_PORT || "8191", 10);
const HOST = "127.0.0.1";

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
    "/extensions/tegaki_manga_nodes/js/minimum_hand_scene_editor.js"
]);

const server = http.createServer(async (req, res) => {
    // Restricted same-origin CORS: do not expose wildcard '*' (Card Section 5)
    const requestOrigin = req.headers.origin;
    const allowedLocalOrigins = new Set([
        `http://${HOST}:${PORT}`,
        `http://localhost:${PORT}`
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

    // 2. Static File Serving
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

export { server, PORT, HOST };
