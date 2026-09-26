// MANGA Prompt Assist UI acceptance (offline): LoRA panel (MANGA-ILLUSTRIOUS-LORA-PRODUCTION1)
// plus autocomplete stability, Wildcard browser and LoRA previews (MANGA-PROMPT-ASSIST-PRODUCTION1).
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
// 1x1 PNG
const PNG = Buffer.from("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==", "base64");

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
    fs.writeFileSync(path.join(root, "characters/series_a/alice_v3.preview.png"), PNG);
    fs.writeFileSync(path.join(root, "styles/ink.preview.png"), PNG); // unopened folder: must not load
    return root;
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
repo, root, port = sys.argv[1], sys.argv[2], int(sys.argv[3])
sys.path.insert(0, repo)
pkg = types.ModuleType("custom_nodes_custom.tegaki_manga_nodes")
pkg.__path__ = [repo + "/custom_nodes_custom/tegaki_manga_nodes"]
sys.modules["custom_nodes_custom.tegaki_manga_nodes"] = pkg
from custom_nodes_custom.tegaki_manga_nodes.engine_resources import browse_lora_payload, lora_preview_path, ResourceContractError
ENV = {"TEGAKI_ILLUSTRIOUS_LORA_ROOT": root}
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
                return self.send(200, browse_lora_payload(parts[3], query.get("dir", [""])[0], [root], environ=ENV))
            if self.command == "GET" and parts[:3] == ["tegaki", "manga", "resources"] and parts[4:] == ["lora", "preview"]:
                path = lora_preview_path(parts[3], query.get("id", [""])[0], [root], environ=ENV)
                return self.send(200, open(path, "rb").read(), "image/png")
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
    const backendLog = [];
    const backend = spawn(PYTHON, ["-c", STUB, REPO, root, String(BACKEND_PORT)], { stdio: ["ignore", "pipe", "inherit"] });
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
        const loraCalls = () => backendLog.filter(e => e.path.startsWith("/tegaki/manga/resources/")).length;
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
            assert.equal(afterAdd, `masterpiece, clean lines, <lora:${A}:1.0>`));
        check("Strength still updates the token", () =>
            assert.equal(afterStrength, `masterpiece, clean lines, <lora:${A}:0.7>`));

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
            assert.equal(both, `masterpiece, clean lines, <lora:${A}:0.7>, <lora:${B}:1.0>`);
            assert.equal(count, "(2)");
        });
        await page.screenshot({ path: path.join(SCRATCH, "prompt_assist_lora_preview.png"), fullPage: false });

        const previewRequests = backendLog.filter(e => e.path.endsWith("/lora/preview")).map(e => decodeURIComponent(e.query));
        check("previews are requested only for the opened folder", () =>
            assert.deepEqual(previewRequests, [`id=${A}`]));
        const traversal = await page.evaluate(async () => Promise.all([
            "../x.safetensors", "characters/series_a/alice_v3.preview.png", "characters/readme.txt", "C:/Windows/x.safetensors",
        ].map(async id => {
            const r = await fetch(`/api/manga/resources/lora/preview?id=${encodeURIComponent(id)}`);
            return [r.status, (r.headers.get("content-type") || "").split(";")[0]];
        })));
        check("preview route fails closed for traversal and non-sidecar requests", () =>
            traversal.forEach(([status, type]) => assert.ok(status >= 400 && type === "application/json", JSON.stringify(traversal))));

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
    }
    const failed = results.filter(([, s]) => s !== "PASS").length;
    console.log(`\n${results.length - failed}/${results.length} UI acceptance checks passed`);
    process.exit(failed ? 1 : 0);
}

main().catch(err => { console.error(err); process.exit(1); });
