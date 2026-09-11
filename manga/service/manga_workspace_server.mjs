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

    // 2. Dedicated Guide Asset Ingestion Endpoint (Card M1C2B Section 3, 5, 7, 8, 9, 10, 11, 14)
    if (pathname === "/api/guide-assets/upload") {
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

        // Backend multipart forwarding (Card Section 10, 11)
        const backendUploadUrl = `${parsedBackend.origin}/upload/image`;
        try {
            const formData = new FormData();
            const blob = new Blob([body], { type: detectedType });
            formData.append("image", blob, filename);
            formData.append("subfolder", "tegaki_manga_guides");

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
                returnedSubfolder !== "tegaki_manga_guides"
            ) {
                res.writeHead(502, { "Content-Type": "application/json" });
                res.end(JSON.stringify({ ok: false, error: "Backend response validation failed: unexpected subfolder or unsafe filename" }));
                return;
            }

            const canonicalRef = `tegaki_manga_guides/${returnedName}`;
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

    // 3. Dedicated Guide Asset Preview Endpoint (Card M1C2B Section 12, 13 & M1C2B1 Section 14, 15)
    if (pathname === "/api/guide-assets/view") {
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
        // Must start with canonical tegaki_manga_guides/
        if (!ref.startsWith("tegaki_manga_guides/")) {
            res.writeHead(400, { "Content-Type": "application/json" });
            res.end(JSON.stringify({ ok: false, error: "Invalid ref: must start with 'tegaki_manga_guides/'" }));
            return;
        }

        const relativeName = ref.slice("tegaki_manga_guides/".length);
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
        backendViewUrl.searchParams.set("subfolder", "tegaki_manga_guides");
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
