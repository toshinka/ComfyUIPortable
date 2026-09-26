// MANGA Prompt Assist UI acceptance (offline): LoRA panel (MANGA-ILLUSTRIOUS-LORA-PRODUCTION1)
// plus autocomplete stability, Wildcard browser and LoRA previews (MANGA-PROMPT-ASSIST-PRODUCTION1),
// plus portable aliases, diagnostics and trusted-root autocomplete (MANGA-LORA-PORTABLE-COMPAT-DIAGNOSTICS1),
// plus the compact card grid and bulk strength (MANGA-LORA-UX-PRODUCTION1),
// plus content-typed previews, portrait slots and selected-first order (MANGA-LORA-UX-OWNER-CORRECTION1).
//
// Real manga_workspace_server.mjs + real app + real Danbooru catalog, backed by a loopback stub
// that serves ONLY the LoRA browse/preview routes through the production engine_resources
// functions over a temp LoRA tree.  No ComfyUI, no /prompt, no GPU.
// Usage: node manga/tests/verify_lora_panel_browser.mjs
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
const A_TOKEN = "characters/series_a/alice_v3"; // duplicate basename -> canonical token
const B_TOKEN = "characters/series_b/alice_v3";
const LONG = "an_extremely_long_lora_filename_for_layout_testing_with_many_many_words_v1234567890abcdef";
// 1x1 PNG
// 60x80 portrait fixtures. JPEG_AS_PNG mirrors the Owner's legacy HELLSING sidecar: JPEG bytes named *.preview.png.
const PNG = Buffer.from("iVBORw0KGgoAAAANSUhEUgAAADwAAABQCAIAAADKqIEEAAAAkklEQVR4nO3bIQ6DUBRFwdKgqlkWmkWiWURXVF3RBE0qDvnJjLry5Pk3Le/lMZrn3QH/GDJ6PtexvW7suGLdP78x5KVFV0RXRFdEV0RXRFdEV0RXRFdEV0RXRFdEV0RXRFdEV0RXRFdEV0RXRFdEV0RXRFdEV0RXRFdEV0RXRFdEV0RXRFdEV0RXRFcmD2eRIaO/WRAFgUBingwAAAAASUVORK5CYII=", "base64");
const JPEG_AS_PNG = Buffer.from("/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAYEBQYFBAYGBQYHBwYIChAKCgkJChQODwwQFxQYGBcUFhYaHSUfGhsjHBYWICwgIyYnKSopGR8tMC0oMCUoKSj/2wBDAQcHBwoIChMKChMoGhYaKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCj/wAARCABQADwDASIAAhEBAxEB/8QAHwAAAQUBAQEBAQEAAAAAAAAAAAECAwQFBgcICQoL/8QAtRAAAgEDAwIEAwUFBAQAAAF9AQIDAAQRBRIhMUEGE1FhByJxFDKBkaEII0KxwRVS0fAkM2JyggkKFhcYGRolJicoKSo0NTY3ODk6Q0RFRkdISUpTVFVWV1hZWmNkZWZnaGlqc3R1dnd4eXqDhIWGh4iJipKTlJWWl5iZmqKjpKWmp6ipqrKztLW2t7i5usLDxMXGx8jJytLT1NXW19jZ2uHi4+Tl5ufo6erx8vP09fb3+Pn6/8QAHwEAAwEBAQEBAQEBAQAAAAAAAAECAwQFBgcICQoL/8QAtREAAgECBAQDBAcFBAQAAQJ3AAECAxEEBSExBhJBUQdhcRMiMoEIFEKRobHBCSMzUvAVYnLRChYkNOEl8RcYGRomJygpKjU2Nzg5OkNERUZHSElKU1RVVldYWVpjZGVmZ2hpanN0dXZ3eHl6goOEhYaHiImKkpOUlZaXmJmaoqOkpaanqKmqsrO0tba3uLm6wsPExcbHyMnK0tPU1dbX2Nna4uPk5ebn6Onq8vP09fb3+Pn6/9oADAMBAAIRAxEAPwDF1jU5rK5WOJYypQN8wPqff2qj/b11/wA84fyP+NHib/j/AI/+uQ/mayK+SoUKcqabR9Hw1w1lWKyqhWrUIylKOr7mv/b11/zzh/I/40f29df884fyP+NZFFa/VqX8p7n+qWTf9A0TX/t66/55w/kf8aP7euv+ecP5H/Gsiij6tS/lD/VLJv8AoGia/wDb11/zzh/I/wCNdDayGW2hkbAZ0DHHuK4eu10//jwtv+uS/wAhXHjaUIRXKrH594g5Ngcuw9GeEpKDcne3oYPib/j/AI/+uQ/mayK1/E3/AB/x/wDXIfzNZFdmG/hRP0HhL/kTYb/CFFFFbn0QUUUUAFdrp/8Ax4W3/XJf5CuKrtdP/wCPC2/65L/IV5+P+FH5f4of7rQ/xP8AIwfE3/H/AB/9ch/M1kVr+Jv+P+P/AK5D+ZrIrpw38KJ9dwl/yJsN/hCiiitz6IKKKKACu10//jwtv+uS/wAhXFV2un/8eFt/1yX+Qrz8f8KPy/xQ/wB1of4n+Rg+Jv8Aj/j/AOuQ/mayK1/E3/H/AB/9ch/M1kV04b+FE+u4S/5E2G/whRRRW59EFFFFABXa6f8A8eFt/wBcl/kK4qu10/8A48Lb/rkv8hXn4/4Ufl/ih/utD/E/yMHxN/x/x/8AXIfzNZFdLrGmTXtyskTRhQgX5ifU+3vVH+wbr/npD+Z/wrShXpxppNnpcNcS5VhcqoUa1eMZRjquxkUVr/2Ddf8APSH8z/hR/YN1/wA9IfzP+Fa/WaX8x7n+tuTf9BMTIorX/sG6/wCekP5n/Cj+wbr/AJ6Q/mf8KPrNL+YP9bcm/wCgmJkV2un/APHhbf8AXJf5CsH+wbr/AJ6Q/mf8K6G1jMVtDG2CyIFOPYVx42rCcVyu5+feIOc4HMcPRhhKqm1J3t6H/9k=", "base64");

function getPlaywrightChromium() {
    if (process.env.TEGAKI_PLAYWRIGHT_MODULE) return require(process.env.TEGAKI_PLAYWRIGHT_MODULE).chromium;
    try { return require("playwright").chromium; } catch {}
    const root = execSync("npm root -g", { encoding: "utf8" }).trim();
    try { return require(path.join(root, "playwright")).chromium; } catch {}
    return require(path.join(root, "@executeautomation", "playwright-mcp-server", "node_modules", "playwright")).chromium;
}

function makeTree() {
    const root = fs.mkdtempSync(path.join(os.tmpdir(), "tegaki-lora-"));
    const files = [A, B, "styles/ink.safetensors", `styles/${LONG}.safetensors`, "root_level.safetensors", "characters/readme.txt"];
    for (let i = 0; i < 40; i++) files.push(`bulk/style_${String(i).padStart(2, "0")}.safetensors`);
    for (const rel of files) {
        fs.mkdirSync(path.dirname(path.join(root, rel)), { recursive: true });
        fs.writeFileSync(path.join(root, rel), "NOT-A-REAL-MODEL");
    }
    fs.writeFileSync(path.join(root, "characters/series_a/alice_v3.preview.png"), PNG);
    fs.writeFileSync(path.join(root, "styles/ink.preview.png"), JPEG_AS_PNG); // unopened folder: must not load
    return root;
}

function makeOutsideRoot() {
    // Another ComfyUI-registered LoRA root (EasyReforge-like): never a candidate.
    const dir = fs.mkdtempSync(path.join(os.tmpdir(), "tegaki-lora-outside-"));
    fs.writeFileSync(path.join(dir, "outside_only.safetensors"), "NOT-A-REAL-MODEL");
    return dir;
}

function makeWildcards() {
    const dir = fs.mkdtempSync(path.join(os.tmpdir(), "tegaki-wildcards-"));
    fs.writeFileSync(path.join(dir, "simple.txt"), "red\nblue\n");
    fs.mkdirSync(path.join(dir, "nested"));
    fs.writeFileSync(path.join(dir, "nested", "leaf.txt"), "cat\ndog\n");
    return dir;
}

const STUB = `
import json, sys, types
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit, parse_qs
repo, root, port, outside = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4]
sys.path.insert(0, repo)
pkg = types.ModuleType("custom_nodes_custom.tegaki_manga_nodes")
pkg.__path__ = [repo + "/custom_nodes_custom/tegaki_manga_nodes"]
sys.modules["custom_nodes_custom.tegaki_manga_nodes"] = pkg
import os
from custom_nodes_custom.tegaki_manga_nodes.engine_resources import (browse_lora_payload, lora_preview_path, preview_mime,
    ResourceContractError, build_trusted_lora_index, lora_index_payload, validate_lora_request)
ENV = {"TEGAKI_ILLUSTRIOUS_LORA_ROOT": root}
def walk(base):
    return [os.path.relpath(os.path.join(d, f), base).replace(os.sep, "/") for d, _, fs in os.walk(base)
            for f in fs if f.endswith(".safetensors")]
# Stand-in for ComfyUI's merged get_filename_list("loras"): trusted root + another registered root.
INDEX = build_trusted_lora_index(sorted(walk(root) + walk(outside)), root)
class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def send(self, status, payload, ctype="application/json"):
        body = payload if isinstance(payload, bytes) else json.dumps(payload).encode()
        self.send_response(status); self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body)
    def handle_any(self):
        url = urlsplit(self.path)
        query = parse_qs(url.query)
        print(json.dumps({"method": self.command, "path": url.path, "query": url.query}), flush=True)
        parts = url.path.strip("/").split("/")
        try:
            if self.command == "GET" and parts[:3] == ["tegaki", "manga", "resources"] and parts[4:] == ["lora"]:
                return self.send(200, browse_lora_payload(parts[3], query.get("dir", [""])[0], [root], environ=ENV,
                                                          token_for=INDEX.token_for))
            if self.command == "GET" and parts[:3] == ["tegaki", "manga", "resources"] and parts[4:] == ["lora", "index"]:
                return self.send(200, lora_index_payload(parts[3], INDEX))
            if self.command == "POST" and parts[:3] == ["tegaki", "manga", "resources"] and parts[4:] == ["lora", "validate"]:
                body = json.loads(self.rfile.read(int(self.headers.get("Content-Length") or 0)) or b"{}")
                return self.send(200, validate_lora_request(parts[3], body, INDEX))
            if self.command == "GET" and parts[:3] == ["tegaki", "manga", "resources"] and parts[4:] == ["lora", "preview"]:
                path = lora_preview_path(parts[3], query.get("id", [""])[0], [root], environ=ENV)
                return self.send(200, open(path, "rb").read(), preview_mime(path))
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
    const [n, status] = results[results.length - 1];
    console.log(`${status === "PASS" ? "PASS" : "FAIL"}  ${n}${status === "PASS" ? "" : ` — ${status}`}`); // incremental
}

async function main() {
    fs.mkdirSync(SCRATCH, { recursive: true });
    const root = makeTree();
    const wildcards = makeWildcards();
    const outside = makeOutsideRoot();
    const backendLog = [];
    const backend = spawn(PYTHON, ["-c", STUB, REPO, root, String(BACKEND_PORT), outside], { stdio: ["ignore", "pipe", "inherit"] });
    backend.stdout.on("data", chunk => String(chunk).split("\n").filter(Boolean).forEach(l => backendLog.push(JSON.parse(l))));
    const workspace = spawn(process.execPath, [path.join(REPO, "manga", "service", "manga_workspace_server.mjs")], {
        env: { ...process.env, MANGA_WORKSPACE_PORT: String(WORKSPACE_PORT), MANGA_BACKEND_URL: `http://127.0.0.1:${BACKEND_PORT}`,
            TEGAKI_MANGA_WILDCARDS_DIR: wildcards },
        stdio: ["ignore", "ignore", "inherit"],
    });
    const chromium = getPlaywrightChromium();
    let browser;
    try {
        await waitFor(`http://127.0.0.1:${BACKEND_PORT}/health`);
        await waitFor(`http://127.0.0.1:${WORKSPACE_PORT}/`);
        browser = await chromium.launch({ headless: true });
        const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
        const pageErrors = [];
        page.on("pageerror", err => pageErrors.push(err.message));
        await page.goto(`http://127.0.0.1:${WORKSPACE_PORT}/`, { waitUntil: "domcontentloaded" });
        await page.waitForSelector("#scene-composer-prompt", { state: "visible", timeout: 15000 });
        await page.waitForFunction(() => document.querySelector("#scene-composer-prompt")?.dataset.tagAutocompleteState === "ready",
            null, { timeout: 30000 });
        const prompt = page.locator("#scene-composer-prompt");
        const popup = page.locator("#scene-composer-prompt-wrap .tag-autocomplete-popup");
        // Folder browse requests only (the autocomplete's trusted-index load is not a browse).
        const loraCalls = () => backendLog.filter(e => /^\/tegaki\/manga\/resources\/[^/]+\/lora$/.test(e.path)).length;
        const labels = () => popup.locator(".tag-autocomplete-label").allTextContents();
        const doc = () => page.evaluate(() => {
            const pageDoc = window.__tegakiManga.store.getPage();
            return { style: pageDoc.style_prompt, scenes: pageDoc.scenes.map(s => s.prompt) };
        });

        const tops = await page.evaluate(() => ["scene-composer-prompt-wrap", "mg-lora-panel", "scene-composer-negative-wrap"]
            .map(id => document.getElementById(id).getBoundingClientRect().top));
        check("Positive Prompt appears above Prompt Assist", () => assert.ok(tops[0] < tops[1], JSON.stringify(tops)));
        check("Prompt Assist appears above Negative Prompt", () => assert.ok(tops[1] < tops[2], JSON.stringify(tops)));
        check("Prompt Assist starts collapsed and UI open does not browse", () => assert.equal(loraCalls(), 0));

        // ---------------- Autocomplete: Global -> Scene -> Global ----------------
        await prompt.fill("");
        await prompt.click();
        await prompt.pressSequentially("long h");
        await popup.waitFor({ state: "visible", timeout: 5000 });
        const globalLabels = await labels();
        const popupLayer = await page.evaluate(() => {
            const pop = document.querySelector("#scene-composer-prompt-wrap .tag-autocomplete-popup");
            const r = pop.getBoundingClientRect();
            const hit = document.elementFromPoint(r.left + r.width / 2, r.top + Math.min(12, r.height / 2));
            return { inViewport: r.top >= 0 && r.bottom <= innerHeight && r.width > 0, onTop: pop.contains(hit), id: pop.id };
        });
        check("A. Global prompt completion appears (space-typed 'long h' -> long_hair)", () =>
            assert.ok(globalLabels.includes("long_hair"), JSON.stringify(globalLabels)));
        check("I. dropdown is visible and not covered within the prompt layer", () =>
            assert.deepEqual({ inViewport: popupLayer.inViewport, onTop: popupLayer.onTop }, { inViewport: true, onTop: true }));
        await prompt.press("Enter");
        const afterGlobalAccept = await prompt.inputValue();

        await page.click("#mg-scene-add");
        await page.waitForFunction(() => window.__tegakiManga.getComposerPromptTarget() !== "global");
        await prompt.click();
        await prompt.pressSequentially("blue_e");
        await popup.waitFor({ state: "visible", timeout: 5000 });
        const sceneLabels = await labels();
        await prompt.press("Enter");
        const afterScene = await doc();
        check("B. Scene target switch preserves completion", () => {
            assert.ok(sceneLabels.includes("blue_eyes"), JSON.stringify(sceneLabels));
            assert.equal(afterScene.scenes[0], "blue_eyes, ");
        });
        check("E. completion edits the active target only (Global untouched while on Scene)", () => {
            assert.equal(afterGlobalAccept, "long_hair, ");
            assert.equal(afterScene.style, "long_hair, ");
        });

        await page.click("#scene-prompt-tab-global");
        await page.waitForFunction(() => window.__tegakiManga.getComposerPromptTarget() === "global");
        const globalValueBack = await prompt.inputValue();
        await prompt.click();
        await page.keyboard.press("End");
        await prompt.pressSequentially("smi");
        await popup.waitFor({ state: "visible", timeout: 5000 });
        const backLabels = await labels();
        const popupCount = await page.locator(".tag-autocomplete-popup").count();
        await prompt.press("Escape");
        check("C. switching back to Global still completes", () => {
            assert.equal(globalValueBack, "long_hair, ");
            assert.ok(backLabels.includes("smile"), JSON.stringify(backLabels));
        });
        check("D. rerenders do not duplicate the popup/controller", () => assert.equal(popupCount, 1));

        // Stale target guard: value replaced without an input event (target re-render).
        const stale = await page.evaluate(() => {
            const ta = document.getElementById("scene-composer-prompt");
            const ac = window.__tegakiManga.composerTagAutocomplete;
            ta.focus();
            ta.value = "long_hair, blue_"; ta.setSelectionRange(ta.value.length, ta.value.length);
            ac.refresh();
            const opened = ac.suggestions.length > 0;
            ta.value = "other target text";
            const accepted = ac.accept(0);
            return { opened, accepted, value: ta.value };
        });
        check("E. stale suggestions are never applied to replaced prompt text", () =>
            assert.deepEqual(stale, { opened: true, accepted: false, value: "other target text" }));

        // Wildcard prefix completion through the same popup.
        await prompt.fill("");
        await prompt.pressSequentially("1girl, __sim");
        await popup.waitFor({ state: "visible", timeout: 5000 });
        const wcLabels = await labels();
        const wcPopupId = await popup.getAttribute("id");
        await prompt.press("Enter");
        const afterWc = await prompt.inputValue();
        check("F. wildcard prefix completion appears and inserts __simple__", () => {
            assert.ok(wcLabels.includes("simple"), JSON.stringify(wcLabels));
            assert.equal(afterWc, "1girl, __simple__");
        });
        check("G. tag and wildcard completion share one popup", () => assert.equal(wcPopupId, popupLayer.id));

        // IME composition: no popup while composing, Enter during composition is not an accept.
        const ime = await page.evaluate(() => {
            const ta = document.getElementById("scene-composer-prompt");
            const pop = document.querySelector("#scene-composer-prompt-wrap .tag-autocomplete-popup");
            ta.focus();
            ta.value = "1girl, blue_"; ta.setSelectionRange(ta.value.length, ta.value.length);
            ta.dispatchEvent(new CompositionEvent("compositionstart", { data: "" }));
            ta.dispatchEvent(new InputEvent("input", { isComposing: true, data: "e", inputType: "insertCompositionText" }));
            const hiddenWhileComposing = pop.hidden;
            ta.dispatchEvent(new KeyboardEvent("keydown", { key: "Enter", isComposing: true, bubbles: true, cancelable: true }));
            const valueAfterEnter = ta.value;
            ta.dispatchEvent(new CompositionEvent("compositionend", { data: "e" }));
            return { hiddenWhileComposing, valueAfterEnter, shownAfterEnd: !pop.hidden };
        });
        check("H. IME composition never triggers destructive replacement", () =>
            assert.deepEqual(ime, { hiddenWhileComposing: true, valueAfterEnter: "1girl, blue_", shownAfterEnd: true }));
        await prompt.press("Escape");

        // ---------------- Wildcard Prompt Assist ----------------
        await prompt.fill("masterpiece, smile");
        await prompt.press("Escape"); // the open suggestion popup overlays the tabs directly below the prompt
        await page.click("#mg-assist-tab-wildcard");
        await page.waitForSelector('#mg-wildcard-entries [data-wildcard-id="simple"]');
        const wcMode = { wildcardVisible: await page.locator("#mg-wildcard-body").isVisible(),
            loraHidden: await page.locator("#mg-lora-body").isHidden() };
        await prompt.evaluate(ta => ta.setSelectionRange(ta.value.length, ta.value.length));
        await page.click('#mg-wildcard-entries [data-wildcard-id="simple"]');
        const wcInsert = await prompt.inputValue();
        await page.click('#mg-wildcard-folders [data-folder="nested"]');
        await prompt.evaluate(ta => ta.setSelectionRange("masterpiece".length + 1, "masterpiece".length + 1));
        await page.click('#mg-wildcard-entries [data-wildcard-id="nested/leaf"]');
        const wcNested = await prompt.inputValue();
        check("Wildcard: Prompt Assist mode visible (LoRA body hidden)", () =>
            assert.deepEqual(wcMode, { wildcardVisible: true, loraHidden: true }));
        check("Wildcard: click inserts canonical token, unrelated text preserved", () =>
            assert.equal(wcInsert, "masterpiece, smile, __simple__"));
        check("Wildcard: nested identity inserted at the caret", () =>
            assert.equal(wcNested, "masterpiece, __nested/leaf__, smile, __simple__"));

        // ---------------- LoRA previews + existing LoRA behaviour ----------------
        await prompt.fill("masterpiece, clean lines");
        await prompt.press("Escape");
        await page.click("#mg-assist-tab-lora");
        await page.waitForSelector('.mg-lora-card[data-lora-id="root_level.safetensors"]');
        const root0 = await page.evaluate(() => ({
            folders: [...document.querySelectorAll("#mg-lora-folders .mg-lora-folder")].map(b => b.dataset.folder),
            cards: [...document.querySelectorAll("#mg-lora-cards .mg-lora-card")].map(c => c.dataset.loraId),
        }));
        check("folder navigation does not flatten all files", () => {
            assert.deepEqual(root0.folders, ["bulk", "characters", "styles"]);
            assert.deepEqual(root0.cards, ["root_level.safetensors"]);
        });
        await page.locator('.mg-lora-card[data-lora-id="root_level.safetensors"] .mg-lora-card-action').click();
        const uniqueInsert = await prompt.inputValue();
        await page.locator('.mg-lora-card[data-lora-id="root_level.safetensors"] .mg-lora-card-action').click();
        const uniqueRemoved = await prompt.inputValue();
        check("unique LoRA card inserts the portable basename token", () =>
            assert.equal(uniqueInsert, "masterpiece, clean lines, <lora:root_level:1.0>"));
        const browseBody = await page.evaluate(async () => (await fetch("/api/manga/resources/lora?dir=characters/series_a")).text());
        check("physical LoRA root is not exposed to the browser", () => assert.ok(!browseBody.includes(root), browseBody));

        await page.click('#mg-lora-folders [data-folder="bulk"]');
        await page.waitForSelector('.mg-lora-card[data-lora-id="bulk/style_39.safetensors"]');
        const scroll = await page.evaluate(() => {
            const cards = document.getElementById("mg-lora-cards");
            const before = window.scrollY;
            cards.scrollTop = 200;
            return { count: cards.children.length, overflowY: getComputedStyle(cards).overflowY,
                scrolls: cards.scrollHeight > cards.clientHeight && cards.scrollTop > 0, pageMoved: window.scrollY !== before };
        });
        check("LoRA card region scrolls internally", () =>
            assert.deepEqual(scroll, { count: 40, overflowY: "auto", scrolls: true, pageMoved: false }));

        await page.click('#mg-lora-breadcrumb [data-folder=""]');
        await page.click('#mg-lora-folders [data-folder="characters"]');
        await page.click('#mg-lora-folders [data-folder="characters/series_a"]');
        const cardA = page.locator(`.mg-lora-card[data-lora-id="${A}"]`);
        await cardA.locator("img.mg-lora-card-thumb").waitFor({ state: "visible" });
        await page.waitForFunction(id => document.querySelector(`.mg-lora-card[data-lora-id="${id}"] img`)?.naturalWidth > 0, A);
        const thumb = await cardA.locator("img.mg-lora-card-thumb").evaluate(img => ({ loading: img.loading, src: img.getAttribute("src") }));
        check("LoRA preview image appears for a card with .preview.png", () => {
            assert.equal(thumb.loading, "lazy");
            assert.ok(thumb.src.startsWith("/api/manga/resources/lora/preview?") && !thumb.src.includes(root), thumb.src);
        });
        await cardA.locator(".mg-lora-card-action").click();
        const afterAdd = await prompt.inputValue();
        await cardA.locator(".mg-lora-strength").fill("0.7");
        await cardA.locator(".mg-lora-strength").dispatchEvent("change");
        const afterStrength = await prompt.inputValue();
        check("LoRA selection still updates Positive Prompt", () =>
            assert.equal(afterAdd, `masterpiece, clean lines, <lora:${A_TOKEN}:1.0>`));
        check("ambiguous-basename LoRA card inserts the canonical token", () =>
            assert.equal(afterAdd, `masterpiece, clean lines, <lora:${A_TOKEN}:1.0>`));
        check("Strength still updates the token", () =>
            assert.equal(afterStrength, `masterpiece, clean lines, <lora:${A_TOKEN}:0.7>`));

        await page.click('#mg-lora-breadcrumb [data-folder="characters"]');
        await page.click('#mg-lora-folders [data-folder="characters/series_b"]');
        const cardB = page.locator(`.mg-lora-card[data-lora-id="${B}"]`);
        await cardB.waitFor();
        const bThumbs = await cardB.locator("img").count();
        await cardB.locator(".mg-lora-card-action").click();
        const both = await prompt.inputValue();
        const count = await page.locator("#mg-lora-count").textContent();
        check("No-preview LoRA falls back to the text card and stays usable", () => {
            assert.equal(bThumbs, 0);
            assert.equal(both, `masterpiece, clean lines, <lora:${A_TOKEN}:0.7>, <lora:${B_TOKEN}:1.0>`);
            assert.equal(count, "(2)");
        });
        await page.click('#mg-lora-breadcrumb [data-folder="characters"]');
        await page.click('#mg-lora-folders [data-folder="characters/series_a"]');
        await page.locator(`.mg-lora-card[data-lora-id="${A}"] .mg-lora-card-action`).click();
        const afterRemove = await prompt.inputValue();
        check("Remove deletes only that LoRA token; unrelated text preserved", () => {
            assert.equal(uniqueRemoved, "masterpiece, clean lines");
            assert.equal(afterRemove, `masterpiece, clean lines, <lora:${B_TOKEN}:1.0>`);
        });
        await page.waitForSelector('#mg-lora-diagnostics .mg-lora-diag-row[data-status="RESOLVED"]');
        const chainOk = await page.locator("#mg-lora-diagnostics .mg-lora-chain-list li").evaluateAll(els => els.map(e => e.dataset.resolvedId));
        check("valid LoRA appears resolved with its canonical ID in the chain", () => assert.deepEqual(chainOk, [B]));

        // ---------------- Diagnostics: mixed legacy prompt ----------------
        await prompt.fill("masterpiece, <lora:root_level:0.2>, <lora:missing_style:0.3>, <lora:alice_v3:0.5>, <lora:outside_only:1>, <lora:bulk/style_01:9>");
        await prompt.press("Escape");
        await page.waitForSelector('#mg-lora-diagnostics .mg-lora-diag-row[data-status="LORA_AMBIGUOUS"]');
        const diag = await page.evaluate(() => ({
            rows: [...document.querySelectorAll("#mg-lora-diagnostics .mg-lora-diag-row")].map(r => [r.dataset.loraName, r.dataset.status, r.textContent]),
            chain: [...document.querySelectorAll("#mg-lora-diagnostics .mg-lora-chain-list li")].map(li => li.dataset.resolvedId),
            text: document.getElementById("mg-lora-diagnostics").textContent,
        }));
        check("diagnostics report each LoRA individually (valid/missing/ambiguous/outside/strength)", () =>
            assert.deepEqual(diag.rows.map(([n, st]) => [n, st]), [["root_level", "RESOLVED"], ["missing_style", "LORA_UNAVAILABLE"],
                ["alice_v3", "LORA_AMBIGUOUS"], ["outside_only", "OUTSIDE_RESOURCE_ROOT"], ["bulk/style_01", "INVALID_STRENGTH"]]));
        check("missing LoRA shows a clear problem", () => assert.match(diag.rows[1][2], /missing_style.*NOT FOUND/));
        check("ambiguous LoRA shows candidate relative IDs", () => {
            assert.match(diag.rows[2][2], /AMBIGUOUS/);
            assert.ok(diag.rows[2][2].includes(A) && diag.rows[2][2].includes(B), diag.rows[2][2]);
        });
        check("valid LoRA resolves to its canonical relative ID; no physical path shown", () => {
            assert.ok(diag.rows[0][2].includes("→ root_level.safetensors"), diag.rows[0][2]);
            assert.deepEqual(diag.chain, ["root_level.safetensors"]);
            assert.ok(!diag.text.includes(root) && !diag.text.includes(outside));
        });
        const gate = await page.evaluate(async () => {
            const mod = await import("/src/view/generation_view.js");
            const state = { catalog: { checkpoints: [{ id: "ck", available: true }], samplers: ["euler"], schedulers: ["normal"],
                product_bounds: { steps: { min: 1, max: 100 }, cfg: { min: 0, max: 30 }, width: { min: 256, max: 2048 },
                    height: { min: 256, max: 2048 }, max_pixels: 2097152 },
                backend_bounds: { steps: { min: 1, max: 100 }, cfg: { min: 0, max: 30 }, width: { min: 256, max: 2048 },
                    height: { min: 256, max: 2048 } }, revision: "r" },
                draft: { checkpoint_id: "ck", sampler_id: "euler", scheduler_id: "normal", steps: "20", cfg: "7",
                    width: "1024", height: "1024", seed_requested: "1" } };
            try {
                await mod.compileGlobalGeneration(state, window.__tegakiManga.store, { compile: async () => ({}) });
                return "compiled";
            } catch (err) { return err.message; }
        });
        check("Generate-disabled LoRA reason is discoverable (backend diagnostics)", () =>
            assert.equal(gate, "Generate disabled — unresolved LoRA: missing_style NOT FOUND (+3 more). See LoRA status under the prompt."));

        // ---------------- Autocomplete: trusted root only ----------------
        await prompt.fill("1girl, <lora:outside_on");
        await page.waitForTimeout(400);
        const outsideLabels = await popup.isVisible() ? await labels() : [];
        await prompt.fill("1girl, <lora:alice");
        await popup.waitFor({ state: "visible", timeout: 5000 });
        const aliceOptions = await popup.locator("[role=option]").evaluateAll(els => els.map(e => e.textContent));
        await prompt.press("Enter");
        const aliceInsert = await prompt.inputValue();
        check("autocomplete does not suggest out-of-root-only LoRAs", () => assert.deepEqual(outsideLabels, []));
        check("autocomplete shows folder context for duplicate basenames and inserts canonical token", () => {
            assert.deepEqual(aliceOptions, ["alice_v3characters/series_a", "alice_v3characters/series_b"]);
            assert.equal(aliceInsert, `1girl, <lora:${A_TOKEN}:1>`);
        });
        await prompt.fill("masterpiece");
        await prompt.press("Escape"); // tag suggestion popup would cover the Prompt Assist toggle
        await page.screenshot({ path: path.join(SCRATCH, "prompt_assist_lora_preview.png"), fullPage: false });

        const previewRequests = backendLog.filter(e => e.path.endsWith("/lora/preview")).map(e => decodeURIComponent(e.query));
        check("previews are requested only for the opened folder", () =>
            assert.deepEqual([...new Set(previewRequests)], [`id=${A}`]));
        const traversal = await page.evaluate(async () => Promise.all([
            "../x.safetensors", "characters/series_a/alice_v3.preview.png", "characters/readme.txt", "C:/Windows/x.safetensors",
        ].map(async id => {
            const r = await fetch(`/api/manga/resources/lora/preview?id=${encodeURIComponent(id)}`);
            return [r.status, (r.headers.get("content-type") || "").split(";")[0]];
        })));
        check("preview route fails closed for traversal and non-sidecar requests", () =>
            traversal.forEach(([status, type]) => assert.ok(status >= 400 && type === "application/json", JSON.stringify(traversal))));

        // ---------------- Compact card grid (MANGA-LORA-UX-PRODUCTION1) ----------------
        await page.click('#mg-lora-breadcrumb [data-folder=""]');
        await page.click('#mg-lora-folders [data-folder="styles"]');
        await page.waitForSelector(`.mg-lora-card[data-lora-id="styles/${LONG}.safetensors"]`);
        await page.waitForFunction(() => document.querySelector('.mg-lora-card[data-lora-id="styles/ink.safetensors"] img')?.naturalWidth > 0);
        const grid = await page.evaluate(long => {
            const cards = document.getElementById("mg-lora-cards");
            const ink = cards.querySelector('.mg-lora-card[data-lora-id="styles/ink.safetensors"]');
            const lng = cards.querySelector(`.mg-lora-card[data-lora-id="styles/${long}.safetensors"]`);
            const box = el => el.getBoundingClientRect();
            const name = lng.querySelector(".mg-lora-card-name");
            const lineHeight = parseFloat(getComputedStyle(name).lineHeight);
            return {
                display: getComputedStyle(cards).display,
                columns: getComputedStyle(cards).gridTemplateColumns.split(" ").length,
                sameRow: Math.abs(box(ink).top - box(lng).top) < 1,
                equalCards: Math.abs(box(ink).height - box(lng).height) < 1.5,
                inkSlot: box(ink.querySelector(".mg-lora-card-thumb")).height,
                noPreviewSlot: box(lng.querySelector(".mg-lora-card-noimg")).height,
                noPreviewText: lng.querySelector(".mg-lora-card-noimg")?.textContent,
                nameLines: (() => {
                    const range = document.createRange();
                    range.selectNodeContents(name);
                    return new Set([...range.getClientRects()].map(r => Math.round(r.top))).size;
                })(),
                nameVisibleLines: Math.round(box(name).height / lineHeight),
                nameTitle: name.title,
                controlsVisible: [ink, lng].every(card => {
                    const r = box(card.querySelector(".mg-lora-card-controls"));
                    return r.height >= 18 && r.bottom <= box(card).bottom + 0.5;
                }),
                strengthWidth: box(lng.querySelector(".mg-lora-strength")).width,
                cardWidth: box(ink).width,
                inkSlotWidth: box(ink.querySelector(".mg-lora-card-thumb")).width,
                noPreviewSlotWidth: box(lng.querySelector(".mg-lora-card-noimg")).width,
                inkFit: getComputedStyle(ink.querySelector("img.mg-lora-card-thumb")).objectFit,
                inkNatural: [ink.querySelector("img").naturalWidth, ink.querySelector("img").naturalHeight],
            };
        }, LONG);
        check("UX A/B/I. responsive grid, >=2 compact cards per row, cards do not stretch past 200px", () => {
            assert.equal(grid.display, "grid");
            assert.ok(grid.columns >= 2, JSON.stringify(grid));
            assert.equal(grid.sameRow, true);
            assert.ok(grid.cardWidth >= 150 && grid.cardWidth <= 200.5, JSON.stringify(grid));
        });
        check("OC F/G. portrait 3:4 preview slot with non-distorting full-image fit", () => {
            assert.ok(Math.abs(grid.inkSlot / grid.inkSlotWidth - 4 / 3) < 0.02, JSON.stringify(grid));
            assert.equal(grid.inkFit, "contain");
            assert.deepEqual(grid.inkNatural, [60, 80]);
        });
        check("OC H / UX C/D. NO PREVIEW placeholder uses the same portrait slot", () => {
            assert.equal(grid.noPreviewSlot, grid.inkSlot);
            assert.equal(grid.noPreviewSlotWidth, grid.inkSlotWidth);
            assert.equal(grid.noPreviewText, "NO PREVIEW");
            assert.equal(grid.equalCards, true);
        });
        const mimes = await page.evaluate(async ids => Promise.all(ids.map(async id => {
            const r = await fetch(`/api/manga/resources/lora/preview?id=${encodeURIComponent(id)}`);
            return [r.status, r.headers.get("content-type")];
        })), ["characters/series_a/alice_v3.safetensors", "styles/ink.safetensors"]);
        check("OC A/B/C. PNG preview served as image/png; JPEG bytes in *.preview.png served as image/jpeg and render", () =>
            assert.deepEqual(mimes, [[200, "image/png"], [200, "image/jpeg"]]));
        const displayOrder = () => page.evaluate(() => [...document.querySelectorAll("#mg-lora-cards .mg-lora-card")]
            .map(card => ({ id: card.dataset.loraId.split("/").pop(), r: card.getBoundingClientRect() }))
            .sort((a, b) => (a.r.top - b.r.top) || (a.r.left - b.r.left)).map(item => item.id));
        const orderUnselected = await displayOrder();
        check("UX E. long name wraps to multiple lines, clamps at 3, keeps card geometry, full ID in title", () => {
            assert.ok(grid.nameLines >= 2 && grid.nameVisibleLines === 3, JSON.stringify(grid));
            assert.equal(grid.nameTitle, `styles/${LONG}.safetensors`);
        });
        check("UX F. strength + Add/Remove remain reachable in every card", () => {
            assert.equal(grid.controlsVisible, true);
            assert.ok(grid.strengthWidth >= 56, JSON.stringify(grid));
        });

        // ---------------- Bulk strength ----------------
        const sceneId = await page.evaluate(() => window.__tegakiManga.store.getPage().scenes[0].scene_id);
        const storeState = () => page.evaluate(id => {
            const pg = window.__tegakiManga.store.getPage();
            return { global: pg.style_prompt, negative: pg.style_negative_prompt,
                scene: pg.scenes.find(s => s.scene_id === id).prompt };
        }, sceneId);
        await prompt.fill("masterpiece");
        await prompt.press("Escape");
        const zeroDisabled = await page.locator("#mg-lora-bulk-apply").isDisabled();
        check("UX bulk K. no added LoRAs: Apply is disabled (no mutation)", () => assert.equal(zeroDisabled, true));
        const mixed = `masterpiece, <lora:root_level:1.0>, clean lines, <lora:ink:0.7>, <lora:${B_TOKEN}:0.4>, <lora:broken>`;
        await prompt.fill(mixed);
        await prompt.press("Escape");
        await page.locator("#scene-composer-negative").fill("blurry, <lora:ink:0.9>");
        const beforeBulk = await storeState();
        await page.locator("#mg-lora-bulk-strength").fill("0.2");
        await page.click("#mg-lora-bulk-apply");
        const afterBulk = { prompt: await prompt.inputValue(), status: await page.locator("#mg-lora-bulk-status").textContent(),
            store: await storeState() };
        check("UX H/I. bulk 0.2 changes all 3 added LoRAs; names, order, text kept; malformed untouched", () => {
            assert.equal(afterBulk.prompt, `masterpiece, <lora:root_level:0.2>, clean lines, <lora:ink:0.2>, <lora:${B_TOKEN}:0.2>, <lora:broken>`);
            assert.equal(afterBulk.status, "Applied 0.2 to 3 LoRAs");
            assert.equal(afterBulk.store.global, afterBulk.prompt);
        });
        check("UX bulk: Negative Prompt and the Scene prompt are untouched by a Global bulk apply", () => {
            assert.equal(afterBulk.store.negative, "blurry, <lora:ink:0.9>");
            assert.equal(afterBulk.store.scene, beforeBulk.scene);
        });
        const orderAfterBulk = await displayOrder();
        check("OC J/M. selected card displays first; prompt LoRA order unchanged by display order", () => {
            assert.deepEqual(orderUnselected, [`${LONG}.safetensors`, "ink.safetensors"]);
            assert.deepEqual(orderAfterBulk, ["ink.safetensors", `${LONG}.safetensors`]);
            assert.deepEqual([...afterBulk.prompt.matchAll(/<lora:([^:<>]+):/g)].map(m => m[1]), ["root_level", "ink", B_TOKEN]);
        });
        await page.waitForFunction(() => {
            const items = [...document.querySelectorAll("#mg-lora-diagnostics .mg-lora-chain-list li")];
            return items.length === 3 && items.every(li => li.textContent.endsWith("· 0.20"));
        }, null, { timeout: 5000 }).then(() => true, () => false).then(ok => check("UX L. diagnostics refresh after bulk update (chain shows 0.20; malformed still reported)", () => assert.equal(ok, true)));
        const malformedReported = await page.locator('#mg-lora-diagnostics .mg-lora-diag-row[data-status="INVALID_LORA_SYNTAX"]').count();
        check("UX bulk: malformed directive still reported by diagnostics", () => assert.equal(malformedReported, 1));

        const inkCard = page.locator('.mg-lora-card[data-lora-id="styles/ink.safetensors"]');
        await inkCard.locator(".mg-lora-strength").fill("0.5");
        await inkCard.locator(".mg-lora-strength").dispatchEvent("change");
        const afterIndividual = await prompt.inputValue();
        const selection = await page.evaluate(long => {
            const cs = sel => getComputedStyle(document.querySelector(sel));
            const on = cs('.mg-lora-card[data-lora-id="styles/ink.safetensors"]');
            const off = cs(`.mg-lora-card[data-lora-id="styles/${long}.safetensors"]`);
            return { selected: document.querySelector('.mg-lora-card[data-lora-id="styles/ink.safetensors"]').classList.contains("is-selected"),
                differs: on.borderColor !== off.borderColor && on.backgroundColor !== off.backgroundColor };
        }, LONG);
        check("UX J. individual strength still editable after bulk apply", () =>
            assert.equal(afterIndividual, `masterpiece, <lora:root_level:0.2>, clean lines, <lora:ink:0.5>, <lora:${B_TOKEN}:0.2>, <lora:broken>`));
        check("UX I(grid). selected card is visibly distinct (border and background)", () =>
            assert.deepEqual(selection, { selected: true, differs: true }));
        await inkCard.locator(".mg-lora-card-action").click();
        const afterInkRemove = await prompt.inputValue();
        const orderAfterRemove = await displayOrder();
        const longCard = page.locator(`.mg-lora-card[data-lora-id="styles/${LONG}.safetensors"]`);
        await longCard.locator(".mg-lora-card-action").click();
        const afterLongAdd = await prompt.inputValue();
        check("UX G/H/K. grid card Add and Remove work; Remove preserves unrelated text", () => {
            assert.equal(afterInkRemove, `masterpiece, <lora:root_level:0.2>, clean lines, <lora:${B_TOKEN}:0.2>, <lora:broken>`);
            assert.equal(afterLongAdd, `${afterInkRemove}, <lora:${LONG}:1.0>`);
        });
        await longCard.locator(".mg-lora-card-action").click();
        await inkCard.locator(".mg-lora-card-action").click();
        const afterInkReAdd = await prompt.inputValue();
        const orderAfterReAdd = await displayOrder();
        check("OC L. Remove returns the card to its stable catalog position", () =>
            assert.deepEqual(orderAfterRemove, [`${LONG}.safetensors`, "ink.safetensors"]));
        check("OC K/M. Add moves the card first visually; the prompt appends it without reordering", () => {
            assert.deepEqual(orderAfterReAdd, ["ink.safetensors", `${LONG}.safetensors`]);
            assert.equal(afterInkReAdd, `${afterInkRemove}, <lora:ink:0.5>`);
        });

        // Scene target: bulk touches only the active Scene prompt.
        await page.locator("#scene-prompt-scene-group button").first().click();
        await page.waitForFunction(() => window.__tegakiManga.getComposerPromptTarget() !== "global");
        await prompt.fill("blue_eyes, <lora:root_level:1.0>, <lora:ink:0.8>");
        await prompt.press("Escape");
        const globalBeforeScene = (await storeState()).global;
        await page.locator("#mg-lora-bulk-strength").fill("0.3");
        await page.click("#mg-lora-bulk-apply");
        const sceneAfter = await storeState();
        check("UX bulk G. active Scene bulk apply does not mutate Global or Negative", () => {
            assert.equal(sceneAfter.scene, "blue_eyes, <lora:root_level:0.3>, <lora:ink:0.3>");
            assert.equal(sceneAfter.global, globalBeforeScene);
            assert.equal(sceneAfter.negative, "blurry, <lora:ink:0.9>");
        });
        await page.click("#scene-prompt-tab-global");
        await page.waitForFunction(() => window.__tegakiManga.getComposerPromptTarget() === "global");
        const cardsScroll = await page.evaluate(() => {
            const cards = document.getElementById("mg-lora-cards");
            return getComputedStyle(cards).overflowY;
        });
        const folderNavWorks = await page.locator('#mg-lora-breadcrumb [data-folder=""]').isVisible();
        check("UX M/K(folders). internal card scrolling and folder navigation still available", () => {
            assert.equal(cardsScroll, "auto");
            assert.equal(folderNavWorks, true);
        });
        await page.screenshot({ path: path.join(SCRATCH, "lora_ux_grid.png"), fullPage: false });

        await page.click("#mg-lora-toggle");
        const collapsed = { lora: await page.locator("#mg-lora-body").isHidden(), wildcard: await page.locator("#mg-wildcard-body").isHidden() };
        check("Prompt Assist can collapse", () => assert.deepEqual(collapsed, { lora: true, wildcard: true }));

        const negative = page.locator("#scene-composer-negative");
        await negative.fill("blurry, lowres");
        await page.click("#mg-negative-toggle");
        const negCollapsed = { hidden: await negative.isHidden(), value: await negative.inputValue() };
        await page.click("#mg-negative-toggle");
        check("Negative Prompt collapse preserves value", () => {
            assert.deepEqual(negCollapsed, { hidden: true, value: "blurry, lowres" });
        });
        await page.screenshot({ path: path.join(SCRATCH, "prompt_assist_final.png"), fullPage: false });

        check("no page errors", () => assert.deepEqual(pageErrors, []));
        check("no /prompt submitted", () => assert.equal(backendLog.filter(e => e.path === "/prompt").length, 0));
    } finally {
        if (browser) await browser.close();
        workspace.kill();
        backend.kill();
        fs.rmSync(root, { recursive: true, force: true });
        fs.rmSync(wildcards, { recursive: true, force: true });
        fs.rmSync(outside, { recursive: true, force: true });
    }
    const failed = results.filter(([, s]) => s !== "PASS").length;
    console.log(`\n${results.length - failed}/${results.length} UI acceptance checks passed`);
    process.exit(failed ? 1 : 0);
}

main().catch(err => { console.error(err); process.exit(1); });
