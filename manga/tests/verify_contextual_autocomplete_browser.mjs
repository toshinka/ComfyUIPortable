/**
 * Contextual Prompt Autocomplete Browser Acceptance Fixture.
 * Covers Generate, Global, and Scene prompt surfaces for:
 * - Normal Danbooru tag completion
 * - Contextual <lora:...> completion & weight preservation
 * - Contextual __...__ wildcard completion & delimiter safety
 * - Dynamic choice {...} suppression
 * - Keyboard + pointer acceptance
 */
import assert from "node:assert/strict";
import http from "node:http";
import os from "node:os";
import path from "node:path";
import fs from "node:fs/promises";
import { createRequire } from "node:module";
import { execSync } from "node:child_process";

const require = createRequire(import.meta.url);
function resolveChromium() {
    if (process.env.TEGAKI_PLAYWRIGHT_MODULE) {
        try { return require(process.env.TEGAKI_PLAYWRIGHT_MODULE).chromium; } catch {}
    }
    try { return require("playwright").chromium; } catch {}
    const root = execSync("npm root -g", { encoding: "utf8" }).trim();
    return require(path.join(root, "@executeautomation", "playwright-mcp-server", "node_modules", "playwright")).chromium;
}

const FIXTURE_TAGS = [
    { tag: "1girl", category: "general", ranking: 900 },
    { tag: "1boy", category: "general", ranking: 800 },
    { tag: "solo", category: "general", ranking: 700 },
    { tag: "blue_eyes", category: "character", ranking: 600 },
    { tag: "long_hair", category: "general", ranking: 500 }
];

const FIXTURE_LORAS = [
    { id: "test_lora", available: true },
    { id: "styles/line", available: true },
    { id: "styles/ink", available: true },
    { id: "unavailable_lora", available: false }
];

const capabilityCatalog = {
    ok: true,
    revision: "contextual-autocomplete-fixture",
    checkpoints: [{ id: "Illustrious.safetensors", available: true }],
    loras: FIXTURE_LORAS,
    samplers: ["euler"],
    schedulers: ["normal"],
    product_bounds: {
        steps: { min: 1, max: 100 }, cfg: { min: 0, max: 30 },
        width: { min: 256, max: 2048 }, height: { min: 256, max: 2048 }, max_pixels: 2097152
    },
    backend_bounds: {
        steps: { min: 1, max: 100 }, cfg: { min: 0, max: 30 },
        width: { min: 256, max: 2048 }, height: { min: 256, max: 2048 }, seed: { min: 0, max: 4294967295 }
    }
};

const json = (res, status, body) => {
    res.writeHead(status, { "Content-Type": "application/json; charset=utf-8" });
    res.end(JSON.stringify(body));
};
const listen = server => new Promise(resolve => server.listen(0, "127.0.0.1", resolve));
const close = server => new Promise(resolve => server.close(resolve));

let promptCalls = 0;
const backend = http.createServer((req, res) => {
    const url = new URL(req.url, "http://127.0.0.1");
    if (req.method === "POST" && url.pathname === "/prompt") {
        promptCalls += 1;
        return json(res, 500, { error: "Generation is forbidden in test" });
    }
    if (req.method === "GET" && url.pathname === "/queue") {
        return json(res, 200, { queue_running: [], queue_pending: [] });
    }
    if (req.method === "GET" && url.pathname === "/object_info/TegakiMinimumHandSceneEditor") {
        return json(res, 200, { TegakiMinimumHandSceneEditor: { input: {} } });
    }
    if (req.method === "GET" && url.pathname === "/tegaki/manga/generation/capabilities") {
        return json(res, 200, capabilityCatalog);
    }
    return json(res, 404, { error: "Route not found" });
});

const wildcardsDir = await fs.mkdtemp(path.join(os.tmpdir(), "manga-wildcards-browser-"));
await fs.writeFile(path.join(wildcardsDir, "smoke_wildcard.txt"), "sample\n", "utf-8");
await fs.mkdir(path.join(wildcardsDir, "nested"), { recursive: true });
await fs.writeFile(path.join(wildcardsDir, "nested", "clothing.txt"), "dress\nshirt\n", "utf-8");

const journalDir = await fs.mkdtemp(path.join(os.tmpdir(), "manga-journal-browser-"));
let workspace;
let browser;
let checks = 0;
function check(condition, message) { assert.ok(condition, message); checks += 1; }

try {
    await listen(backend);
    process.env.MANGA_BACKEND_URL = `http://127.0.0.1:${backend.address().port}`;
    process.env.MANGA_WORKSPACE_PORT = "0";
    process.env.MANGA_GENERATION_JOURNAL_DIR = journalDir;
    process.env.TEGAKI_MANGA_WILDCARDS_DIR = wildcardsDir;

    ({ server: workspace } = await import(`../service/manga_workspace_server.mjs?contextual=${Date.now()}`));
    if (!workspace.listening) await new Promise(resolve => workspace.once("listening", resolve));
    const origin = `http://127.0.0.1:${workspace.address().port}`;

    browser = await resolveChromium().launch({ headless: true, args: ["--no-sandbox", "--disable-setuid-sandbox"] });
    const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
    const pageErrors = [];
    page.on("pageerror", error => pageErrors.push(error.message));

    // Route static Danbooru catalog to fixture tags
    await page.route("**/data/danbooru_tags.json", async route => {
        await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(FIXTURE_TAGS) });
    });

    await page.goto(origin, { waitUntil: "networkidle" });
    await page.waitForFunction(() => Boolean(window.__tegakiManga?.store));
    await page.waitForFunction(() =>
        document.querySelector("#scene-composer-prompt")?.dataset.tagAutocompleteState === "ready" &&
        document.querySelector("#mg-positive_raw")?.dataset.tagAutocompleteState === "ready");

    // ==========================================================
    // 1. GENERATE PROMPT SURFACE (#mg-positive_raw)
    // ==========================================================
    await page.evaluate(() => window.__tegakiManga.setMangaMode("generate"));
    const genInput = page.locator("#mg-positive_raw");
    const genPopup = genInput.locator("xpath=..").locator(".tag-autocomplete-popup");

    // 1A. Normal Danbooru tag completion
    await genInput.fill("1gi");
    await genPopup.waitFor({ state: "visible" });
    const genTagOption = genPopup.locator("[role=option]").first();
    check((await genTagOption.locator(".tag-autocomplete-label").textContent()) === "1girl",
        "Generate: normal tag suggests '1girl'");
    check((await genTagOption.locator(".tag-autocomplete-category").textContent()) === "general",
        "Generate: normal tag category badge is 'general'");
    await genInput.press("Tab");
    check((await genInput.inputValue()) === "1girl, ", "Generate: Tab accepts tag with delimiter");

    // 1B. LoRA completion: typing <lora:test
    await genInput.fill("1girl, <lora:test");
    await genPopup.waitFor({ state: "visible" });
    const loraOption = genPopup.locator("[role=option]").first();
    check((await loraOption.locator(".tag-autocomplete-label").textContent()) === "test_lora",
        "Generate: <lora:test suggests 'test_lora'");
    check((await loraOption.locator(".tag-autocomplete-category").textContent()) === "lora",
        "Generate: LoRA category badge is 'lora'");
    await genInput.press("Enter");
    check((await genInput.inputValue()) === "1girl, <lora:test_lora:1>",
        "Generate: Enter inserts canonical LoRA with default weight :1");

    // 1C. LoRA weight preservation: editing <lora:style:0.75>
    await genInput.fill("1girl, <lora:style:0.75>");
    await genInput.evaluate(el => {
        const caret = el.value.indexOf("style") + "style".length;
        el.setSelectionRange(caret, caret);
        el.dispatchEvent(new Event("input", { bubbles: true }));
    });
    await genPopup.waitFor({ state: "visible" });
    const styleOption = genPopup.locator("[role=option]").first();
    check((await styleOption.locator(".tag-autocomplete-label").textContent()).startsWith("styles/"),
        "Generate: <lora:style suggests 'styles/...'");
    // Pointer click acceptance
    await styleOption.click();
    check((await genInput.inputValue()) === "1girl, <lora:styles/ink:0.75>",
        "Generate: Pointer click preserves existing weight :0.75");

    // 1D. Wildcard completion: typing __smoke
    await genInput.fill("1girl, __smoke");
    await genPopup.waitFor({ state: "visible" });
    const wcOption = genPopup.locator("[role=option]").first();
    check((await wcOption.locator(".tag-autocomplete-label").textContent()) === "smoke_wildcard",
        "Generate: __smoke suggests 'smoke_wildcard'");
    check((await wcOption.locator(".tag-autocomplete-category").textContent()) === "wildcard",
        "Generate: Wildcard category badge is 'wildcard'");
    await genInput.press("Enter");
    check((await genInput.inputValue()) === "1girl, __smoke_wildcard__",
        "Generate: Enter inserts closed wildcard __smoke_wildcard__");

    // 1E. Wildcard closed delimiter safety: editing inside __nested/cloth__
    await genInput.fill("1girl, __nested/cloth__, smile");
    await genInput.evaluate(el => {
        const caret = el.value.indexOf("cloth") + "cloth".length;
        el.setSelectionRange(caret, caret);
        el.dispatchEvent(new Event("input", { bubbles: true }));
    });
    await genPopup.waitFor({ state: "visible" });
    check((await genPopup.locator("[role=option]").first().locator(".tag-autocomplete-label").textContent()) === "nested/clothing",
        "Generate: nested wildcard suggests 'nested/clothing'");
    await genInput.press("Enter");
    check((await genInput.inputValue()) === "1girl, __nested/clothing__, smile",
        "Generate: does not duplicate closing delimiter __");

    // 1F. Dynamic Choice suppression: {red|blue}
    await genInput.fill("1girl, {red|blue");
    await page.waitForTimeout(150);
    check(await genPopup.isHidden(), "Generate: dynamic choice {red|blue suppresses autocomplete");

    // ==========================================================
    // 2. GLOBAL PROMPT SURFACE (#scene-composer-prompt under global)
    // ==========================================================
    await page.evaluate(() => window.__tegakiManga.setMangaMode("authoring"));
    await page.click("#scene-prompt-tab-global");
    const composerInput = page.locator("#scene-composer-prompt");
    const composerPopup = composerInput.locator("xpath=..").locator(".tag-autocomplete-popup");

    // 2A. Normal tag
    await composerInput.fill("blue_");
    await composerPopup.waitFor({ state: "visible" });
    check((await composerPopup.locator("[role=option]").first().locator(".tag-autocomplete-label").textContent()) === "blue_eyes",
        "Global: suggests 'blue_eyes'");
    await composerInput.press("Enter");
    check((await composerInput.inputValue()) === "blue_eyes, ", "Global: Enter inserts tag");

    // 2B. LoRA
    await composerInput.fill("blue_eyes, <lora:test");
    await composerPopup.waitFor({ state: "visible" });
    check((await composerPopup.locator("[role=option]").first().locator(".tag-autocomplete-label").textContent()) === "test_lora",
        "Global: <lora:test suggests 'test_lora'");
    await composerPopup.locator("[role=option]").first().click();
    check((await composerInput.inputValue()) === "blue_eyes, <lora:test_lora:1>",
        "Global: pointer click inserts <lora:test_lora:1>");

    // 2C. Wildcard
    await composerInput.fill("blue_eyes, __smoke");
    await composerPopup.waitFor({ state: "visible" });
    check((await composerPopup.locator("[role=option]").first().locator(".tag-autocomplete-label").textContent()) === "smoke_wildcard",
        "Global: __smoke suggests 'smoke_wildcard'");
    await composerInput.press("Enter");
    check((await composerInput.inputValue()) === "blue_eyes, __smoke_wildcard__",
        "Global: inserts __smoke_wildcard__");

    // ==========================================================
    // 3. SCENE PROMPT SURFACE (#scene-composer-prompt under scene)
    // ==========================================================
    await page.click("#scene-prompt-tab-scene_top");

    // 3A. Normal tag
    await composerInput.fill("solo");
    await composerPopup.waitFor({ state: "visible" });
    check((await composerPopup.locator("[role=option]").first().locator(".tag-autocomplete-label").textContent()) === "solo",
        "Scene: suggests 'solo'");
    await composerInput.press("Tab");
    check((await composerInput.inputValue()) === "solo, ", "Scene: Tab inserts 'solo, '");

    // 3B. LoRA
    await composerInput.fill("solo, <lora:styles/line");
    await composerPopup.waitFor({ state: "visible" });
    check((await composerPopup.locator("[role=option]").first().locator(".tag-autocomplete-label").textContent()) === "styles/line",
        "Scene: suggests 'styles/line'");
    await composerInput.press("Enter");
    check((await composerInput.inputValue()) === "solo, <lora:styles/line:1>",
        "Scene: Enter inserts <lora:styles/line:1>");

    // 3C. Wildcard
    await composerInput.fill("solo, __nested/cloth");
    await composerPopup.waitFor({ state: "visible" });
    check((await composerPopup.locator("[role=option]").first().locator(".tag-autocomplete-label").textContent()) === "nested/clothing",
        "Scene: suggests 'nested/clothing'");
    await composerPopup.locator("[role=option]").first().click();
    check((await composerInput.inputValue()) === "solo, __nested/clothing__",
        "Scene: pointer click inserts __nested/clothing__");

    check(pageErrors.length === 0, `Zero browser page errors (errors: ${pageErrors.join("; ")})`);
    check(promptCalls === 0, "Zero prompt submissions made during autocomplete verification");

    console.log(`\nCONTEXTUAL AUTOCOMPLETE BROWSER FIXTURE PASS: ${checks} checks passed; prompt calls 0; real generation 0`);
} finally {
    if (browser) await browser.close();
    if (workspace) await close(workspace);
    if (backend) await close(backend);
    await fs.rm(wildcardsDir, { recursive: true, force: true }).catch(() => {});
    await fs.rm(journalDir, { recursive: true, force: true }).catch(() => {});
}
