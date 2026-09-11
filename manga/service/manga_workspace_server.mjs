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

const server = http.createServer(async (req, res) => {
    // Add CORS headers for local developer convenience
    res.setHeader("Access-Control-Allow-Origin", "*");
    res.setHeader("Access-Control-Allow-Methods", "GET, POST, OPTIONS");
    res.setHeader("Access-Control-Allow-Headers", "Content-Type");

    if (req.method === "OPTIONS") {
        res.writeHead(204);
        res.end();
        return;
    }

    const url = new URL(req.url, `http://${HOST}:${PORT}`);
    let pathname = url.pathname;
    if (pathname === "/") pathname = "/index.html";

    // 1. Optional Proxy to Backend (/proxy?url=...)
    if (pathname === "/api/proxy") {
        const target = url.searchParams.get("target");
        if (!target) {
            res.writeHead(400, { "Content-Type": "application/json" });
            res.end(JSON.stringify({ error: "Missing target parameter" }));
            return;
        }
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
            const proxyRes = await fetch(target, fetchOptions);
            res.writeHead(proxyRes.status, { "Content-Type": proxyRes.headers.get("content-type") || "application/json" });
            const data = await proxyRes.arrayBuffer();
            res.end(Buffer.from(data));
        } catch (err) {
            res.writeHead(502, { "Content-Type": "application/json" });
            res.end(JSON.stringify({ error: "Proxy failure: " + err.message }));
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
