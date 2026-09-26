// MANGA-ILLUSTRIOUS-LORA-PRODUCTION1 UI acceptance (offline).
//
// Real manga_workspace_server.mjs + real app, backed by a loopback stub that serves ONLY the
// LoRA browse route through the production engine_resources.browse_lora_payload over a temp
// LoRA tree.  No ComfyUI, no /prompt, no GPU.  Usage: node manga/tests/verify_lora_panel_browser.mjs
import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { spawn, execSync } from "node:child_process";
import { createRequire } from "node:module";
import { fileURLToPath } from "node:url";

const require = createRequire(import.meta.url);
const HERE = path.dirname(fileURLToPath(import.meta.url));
const REPO = path.resolve(HERE, "..", "..");
const PYTHON = process.env.TEGAKI_PYTHON || "python";
const BACKEND_PORT = 18000 + Math.floor(Math.random() * 500);
const WORKSPACE_PORT = BACKEND_PORT + 600;
const SCRATCH = process.env.TEGAKI_VERIFY_SCRATCH || path.resolve("scratch");
const A = "characters/series_a/alice_v3.safetensors";
const B = "characters/series_b/alice_v3.safetensors";

function getPlaywrightChromium() {
    if (process.env.TEGAKI_PLAYWRIGHT_MODULE) return require(process.env.TEGAKI_PLAYWRIGHT_MODULE).chromium;
    try { return require("playwright").chromium; } catch {}
    const root = execSync("npm root -g", { encoding: "utf8" }).trim();
    try { return require(path.join(root, "playwright")).chromium; } catch {}
    return require(path.join(root, "@executeautomation", "playwright-mcp-server", "node_modules", "playwright")).chromium;
}

function makeTree() {
    const root = fs.mkdtempSync(path.join(os.tmpdir(), "tegaki-lora-"));
    const files = [A, B, "styles/ink.safetensors", "root_level.safetensors", "characters/readme.txt"];
    for (let i = 0; i < 40; i++) files.push(`bulk/style_${String(i).padStart(2, "0")}.safetensors`);
    for (const rel of files) {
        fs.mkdirSync(path.dirname(path.join(root, rel)), { recursive: true });
        fs.writeFileSync(path.join(root, rel), "NOT-A-REAL-MODEL");
    }
    return root;
}

const STUB = `
import json, sys, types
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit, parse_qs
repo, root, port = sys.argv[1], sys.argv[2], int(sys.argv[3])
sys.path.insert(0, repo)
pkg = types.ModuleType("custom_nodes_custom.tegaki_manga_nodes")
pkg.__path__ = [repo + "/custom_nodes_custom/tegaki_manga_nodes"]
sys.modules["custom_nodes_custom.tegaki_manga_nodes"] = pkg
from custom_nodes_custom.tegaki_manga_nodes.engine_resources import browse_lora_payload, ResourceContractError
class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def send(self, status, payload):
        body = json.dumps(payload).encode()
        self.send_response(status); self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body)
    def handle_any(self):
        url = urlsplit(self.path)
        print(json.dumps({"method": self.command, "path": url.path}), flush=True)
        parts = url.path.strip("/").split("/")
        if self.command == "GET" and len(parts) == 5 and parts[:3] == ["tegaki", "manga", "resources"] and parts[4] == "lora":
            try:
                rel = parse_qs(url.query).get("dir", [""])[0]
                return self.send(200, browse_lora_payload(parts[3], rel, [root],
                    environ={"TEGAKI_ILLUSTRIOUS_LORA_ROOT": root}))
            except ResourceContractError as exc:
                return self.send(404, {"ok": False, "error_code": exc.code, "error": str(exc)})
        return self.send(404, {"ok": False, "error_code": "NOT_IN_STUB", "error": "not served by stub"})
    do_GET = do_POST = handle_any
ThreadingHTTPServer(("127.0.0.1", port), H).serve_forever()
`;

async function waitFor(url, attempts = 80) {
    for (let i = 0; i < attempts; i++) {
        try { const r = await fetch(url); if (r.status < 500) return; } catch {}
        await new Promise(r => setTimeout(r, 150));
    }
    throw new Error(`Server did not start: ${url}`);
}

const results = [];
function check(name, fn) {
    try { fn(); results.push([name, "PASS"]); } catch (err) { results.push([name, `FAIL: ${err.message}`]); }
}

async function main() {
    fs.mkdirSync(SCRATCH, { recursive: true });
    const root = makeTree();
    const backendLog = [];
    const backend = spawn(PYTHON, ["-c", STUB, REPO, root, String(BACKEND_PORT)], { stdio: ["ignore", "pipe", "inherit"] });
    backend.stdout.on("data", chunk => String(chunk).split("\n").filter(Boolean).forEach(l => backendLog.push(JSON.parse(l))));
    const workspace = spawn(process.execPath, [path.join(REPO, "manga", "service", "manga_workspace_server.mjs")], {
        env: { ...process.env, MANGA_WORKSPACE_PORT: String(WORKSPACE_PORT), MANGA_BACKEND_URL: `http://127.0.0.1:${BACKEND_PORT}` },
        stdio: ["ignore", "ignore", "inherit"],
    });
    const chromium = getPlaywrightChromium();
    let browser;
    try {
        await waitFor(`http://127.0.0.1:${BACKEND_PORT}/health`);
        await waitFor(`http://127.0.0.1:${WORKSPACE_PORT}/`);
        browser = await chromium.launch({ headless: true });
        const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
        await page.goto(`http://127.0.0.1:${WORKSPACE_PORT}/`, { waitUntil: "domcontentloaded" });
        await page.waitForSelector("#scene-composer-prompt", { state: "visible", timeout: 15000 });
        const prompt = page.locator("#scene-composer-prompt");
        const loraCalls = () => backendLog.filter(e => e.path.startsWith("/tegaki/manga/resources/")).length;

        const tops = await page.evaluate(() => ["scene-composer-prompt-wrap", "mg-lora-panel", "scene-composer-negative-wrap"]
            .map(id => document.getElementById(id).getBoundingClientRect().top));
        check("Positive Prompt appears above LoRA", () => assert.ok(tops[0] < tops[1], JSON.stringify(tops)));
        check("LoRA appears above Negative Prompt", () => assert.ok(tops[1] < tops[2], JSON.stringify(tops)));
        check("LoRA starts collapsed and UI open does not browse", () => {
            assert.equal(loraCalls(), 0);
        });
        assert.equal(await page.locator("#mg-lora-body").isHidden(), true);

        await prompt.fill("masterpiece, clean lines");
        await page.click("#mg-lora-toggle");
        await page.waitForSelector('.mg-lora-card[data-lora-id="root_level.safetensors"]');
        const root0 = await page.evaluate(() => ({
            folders: [...document.querySelectorAll("#mg-lora-folders .mg-lora-folder")].map(b => b.dataset.folder),
            cards: [...document.querySelectorAll("#mg-lora-cards .mg-lora-card")].map(c => c.dataset.loraId),
        }));
        check("folder navigation does not flatten all files", () => {
            assert.deepEqual(root0.folders, ["bulk", "characters", "styles"]);
            assert.deepEqual(root0.cards, ["root_level.safetensors"]);
        });

        await page.click('#mg-lora-folders [data-folder="bulk"]');
        await page.waitForSelector('.mg-lora-card[data-lora-id="bulk/style_39.safetensors"]');
        const scroll = await page.evaluate(() => {
            const cards = document.getElementById("mg-lora-cards");
            const before = { win: window.scrollY, body: document.scrollingElement.scrollTop };
            cards.scrollTop = 200;
            return {
                count: cards.children.length, overflowY: getComputedStyle(cards).overflowY,
                scrollHeight: cards.scrollHeight, clientHeight: cards.clientHeight,
                scrollTop: cards.scrollTop, before, after: { win: window.scrollY, body: document.scrollingElement.scrollTop },
            };
        });
        check("LoRA card region scrolls internally", () => {
            assert.equal(scroll.count, 40);
            assert.equal(scroll.overflowY, "auto");
            assert.ok(scroll.scrollHeight > scroll.clientHeight, JSON.stringify(scroll));
            assert.ok(scroll.scrollTop > 0);
            assert.deepEqual(scroll.after, scroll.before);
        });

        await page.click('#mg-lora-breadcrumb [data-folder=""]');
        await page.click('#mg-lora-folders [data-folder="characters"]');
        await page.waitForSelector('#mg-lora-folders [data-folder="characters/series_a"]');
        const chars = await page.evaluate(() => ({
            folders: [...document.querySelectorAll("#mg-lora-folders .mg-lora-folder")].map(b => b.dataset.folder),
            cards: document.querySelectorAll("#mg-lora-cards .mg-lora-card").length,
        }));
        check("nested folder lists only its own children", () =>
            assert.deepEqual(chars, { folders: ["characters/series_a", "characters/series_b"], cards: 0 }));
        await page.click('#mg-lora-folders [data-folder="characters/series_a"]');
        const cardA = page.locator(`.mg-lora-card[data-lora-id="${A}"]`);
        await cardA.locator(".mg-lora-card-action").click();
        const afterAdd = await prompt.inputValue();
        const selectedA = await cardA.evaluate(n => n.classList.contains("is-selected"));
        check("selecting a card visibly updates Positive Prompt", () => {
            assert.equal(afterAdd, `masterpiece, clean lines, <lora:${A}:1.0>`);
            assert.equal(selectedA, true);
        });

        await cardA.locator(".mg-lora-strength").fill("0.7");
        await cardA.locator(".mg-lora-strength").dispatchEvent("change");
        const afterStrength = await prompt.inputValue();
        check("strength edit visibly updates the token", () =>
            assert.equal(afterStrength, `masterpiece, clean lines, <lora:${A}:0.7>`));

        await page.click('#mg-lora-breadcrumb [data-folder="characters"]');
        await page.click('#mg-lora-folders [data-folder="characters/series_b"]');
        await page.locator(`.mg-lora-card[data-lora-id="${B}"] .mg-lora-card-action`).click();
        const both = await prompt.inputValue();
        await page.click('#mg-lora-breadcrumb [data-folder="characters"]');
        await page.click('#mg-lora-folders [data-folder="characters/series_a"]');
        await page.locator(`.mg-lora-card[data-lora-id="${A}"] .mg-lora-card-action`).click();
        const afterRemove = await prompt.inputValue();
        check("removal removes the corresponding token", () => {
            assert.equal(both, `masterpiece, clean lines, <lora:${A}:0.7>, <lora:${B}:1.0>`);
            assert.equal(afterRemove, `masterpiece, clean lines, <lora:${B}:1.0>`);
        });
        await page.screenshot({ path: path.join(SCRATCH, "lora_panel_expanded.png"), fullPage: false });

        await page.click("#mg-lora-toggle");
        const collapsed = { hidden: await page.locator("#mg-lora-body").isHidden(),
            expanded: await page.getAttribute("#mg-lora-toggle", "aria-expanded"), prompt: await prompt.inputValue() };
        check("LoRA section can collapse", () =>
            assert.deepEqual(collapsed, { hidden: true, expanded: "false", prompt: `masterpiece, clean lines, <lora:${B}:1.0>` }));

        const negative = page.locator("#scene-composer-negative");
        await negative.fill("blurry, lowres");
        await page.click("#mg-negative-toggle");
        const negCollapsed = { hidden: await negative.isHidden(), value: await negative.inputValue(),
            expanded: await page.getAttribute("#mg-negative-toggle", "aria-expanded") };
        await page.click("#mg-negative-toggle");
        const negExpanded = { hidden: await negative.isHidden(), value: await negative.inputValue() };
        check("Negative Prompt collapse preserves content", () => {
            assert.deepEqual(negCollapsed, { hidden: true, value: "blurry, lowres", expanded: "false" });
            assert.deepEqual(negExpanded, { hidden: false, value: "blurry, lowres" });
        });
        await page.screenshot({ path: path.join(SCRATCH, "lora_panel_final.png"), fullPage: false });

        const prompts = backendLog.filter(e => e.path === "/prompt").length;
        check("no /prompt submitted", () => assert.equal(prompts, 0));
        console.log(`LoRA browse requests: ${loraCalls()} (lazy, one folder per request)`);
    } finally {
        if (browser) await browser.close();
        workspace.kill();
        backend.kill();
        fs.rmSync(root, { recursive: true, force: true });
    }
    for (const [name, status] of results) console.log(`${status.startsWith("PASS") ? "PASS" : "FAIL"}  ${name}${status === "PASS" ? "" : ` — ${status}`}`);
    const failed = results.filter(([, s]) => s !== "PASS").length;
    console.log(`\n${results.length - failed}/${results.length} UI acceptance checks passed`);
    process.exit(failed ? 1 : 0);
}

main().catch(err => { console.error(err); process.exit(1); });
