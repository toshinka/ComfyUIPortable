/** MANGA-PLAY3 offline Danbooru-style autocomplete browser fixture.
 * Uses a tiny test catalog over one intercepted static request. No generation,
 * GPU inference, or /prompt submission is performed.
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

const FIXTURE_CATALOG = [
    { tag: "1girl", category: "general", ranking: 900 },
    { tag: "1boy", category: "general", ranking: 800 },
    { tag: "long_hair", category: "general", ranking: 700 },
    { tag: "long_hair_style", category: "general", ranking: 600 },
    { tag: "short_hair", category: "general", ranking: 500 },
    { tag: "blue_eyes", category: "character", ranking: 400 },
    { tag: "school_uniform", category: "general", ranking: 300 },
    { tag: "solo", category: "general", ranking: 200 },
    { tag: "hair", category: "general", ranking: 100 }
];

const capabilityCatalog = {
    ok: true,
    revision: "play3-browser-fixture",
    checkpoints: [{ id: "Illustrious.safetensors", available: true }],
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
        return json(res, 500, { error: "Generation is forbidden in PLAY3 fixture" });
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
    return json(res, 404, { error: "PLAY3 fixture route not found" });
});

const previous = Object.fromEntries(["MANGA_BACKEND_URL", "MANGA_WORKSPACE_PORT", "MANGA_GENERATION_JOURNAL_DIR"]
    .map(key => [key, process.env[key]]));
const journalDir = await fs.mkdtemp(path.join(os.tmpdir(), "manga-play3-journal-"));
let workspace;
let browser;
let checks = 0;
function check(condition, message) { assert.ok(condition, message); checks += 1; }

async function selectFirst(page, textareaSelector) {
    const popup = page.locator(textareaSelector).locator("xpath=..").locator(".tag-autocomplete-popup");
    await popup.waitFor({ state: "visible" });
    await popup.locator("[role=option]").first().click();
    return popup;
}

async function setCaretAndRefresh(page, selector, value, marker) {
    await page.locator(selector).fill(value);
    await page.locator(selector).evaluate((element, needle) => {
        const caret = element.value.indexOf(needle) + needle.length;
        element.focus();
        element.setSelectionRange(caret, caret);
        element.dispatchEvent(new Event("input", { bubbles: true }));
    }, marker);
}

try {
    await listen(backend);
    process.env.MANGA_BACKEND_URL = `http://127.0.0.1:${backend.address().port}`;
    process.env.MANGA_WORKSPACE_PORT = "0";
    process.env.MANGA_GENERATION_JOURNAL_DIR = journalDir;
    ({ server: workspace } = await import(`../service/manga_workspace_server.mjs?play3=${Date.now()}`));
    if (!workspace.listening) await new Promise(resolve => workspace.once("listening", resolve));
    const origin = `http://127.0.0.1:${workspace.address().port}`;
    browser = await resolveChromium().launch({ headless: true, args: ["--no-sandbox", "--disable-setuid-sandbox"] });

    let catalogRequests = 0;
    const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
    const pageErrors = [];
    page.on("pageerror", error => pageErrors.push(error.message));
    await page.route("**/data/danbooru_tags.json", async route => {
        catalogRequests += 1;
        await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(FIXTURE_CATALOG) });
    });
    await page.goto(origin, { waitUntil: "networkidle" });
    await page.waitForFunction(() => Boolean(window.__tegakiManga?.store));
    await page.waitForFunction(() =>
        document.querySelector("#scene-composer-prompt")?.dataset.tagAutocompleteState === "ready" &&
        document.querySelector("#mg-positive_raw")?.dataset.tagAutocompleteState === "ready");
    check(catalogRequests === 1, "static catalog loads once for all prompt controllers");

    await page.evaluate(() => window.__tegakiManga.setMangaMode("generate"));
    await page.fill("#mg-positive_raw", "1gi");
    const generatePopup = page.locator("#mg-positive_raw").locator("xpath=..").locator(".tag-autocomplete-popup");
    await generatePopup.waitFor({ state: "visible" });
    check((await generatePopup.locator("[role=option]").first().textContent()).includes("1girl"),
        "Generate positive prompt offers prefix suggestions");

    await page.fill("#mg-positive_raw", "long_");
    await generatePopup.waitFor({ state: "visible" });
    const ranked = await generatePopup.locator(".tag-autocomplete-label").allTextContents();
    check(JSON.stringify(ranked.slice(0, 2)) === JSON.stringify(["long_hair", "long_hair_style"]),
        "prefix ranking orders common tags first");
    await page.locator("#mg-positive_raw").press("ArrowDown");
    check(await generatePopup.locator("[role=option][aria-selected=true] .tag-autocomplete-label").textContent() === "long_hair_style",
        "ArrowDown moves autocomplete selection");
    await page.locator("#mg-positive_raw").press("ArrowUp");
    check(await generatePopup.locator("[role=option][aria-selected=true] .tag-autocomplete-label").textContent() === "long_hair",
        "ArrowUp moves autocomplete selection");
    await page.locator("#mg-positive_raw").press("Enter");
    check(await page.inputValue("#mg-positive_raw") === "long_hair, ", "Enter inserts the selected tag with delimiter");

    await page.fill("#mg-positive_raw", "blue_");
    await generatePopup.waitFor({ state: "visible" });
    await page.locator("#mg-positive_raw").press("Tab");
    check(await page.inputValue("#mg-positive_raw") === "blue_eyes, ", "Tab accepts only while popup is open");
    await page.fill("#mg-positive_raw", "zz");
    await page.locator("#mg-positive_raw").press("Tab");
    check(await page.inputValue("#mg-positive_raw") === "zz" &&
        await page.evaluate(() => document.activeElement?.id !== "mg-positive_raw"),
        "Closed-popup Tab keeps normal textarea behavior");

    await page.fill("#mg-positive_raw", "school_");
    await generatePopup.waitFor({ state: "visible" });
    await page.locator("#mg-positive_raw").press("Escape");
    check(await generatePopup.isHidden(), "Escape closes autocomplete without editing");
    await page.fill("#mg-positive_raw", "solo");
    await generatePopup.waitFor({ state: "visible" });
    await page.mouse.click(4, 4);
    check(await generatePopup.isHidden(), "Pointer outside closes autocomplete");

    const preserved = "prefix, 1gi, suffix";
    await setCaretAndRefresh(page, "#mg-positive_raw", preserved, "1gi");
    await generatePopup.waitFor({ state: "visible" });
    await generatePopup.locator("[role=option]").first().click();
    check(await page.inputValue("#mg-positive_raw") === "prefix, 1girl, suffix" &&
        await page.evaluate(() => document.activeElement?.id === "mg-positive_raw"),
        "Pointer insertion preserves surrounding text and textarea focus");

    const specialCases = [
        "hero, <lora:ink:0.7>",
        "hero, __wildcard__",
        "hero, {blue|red}"
    ];
    for (const value of specialCases) {
        const marker = value.includes("<") ? "<lora:ink" : value.includes("__") ? "__wild" : "{blue|";
        await setCaretAndRefresh(page, "#mg-positive_raw", value, marker);
        check(await generatePopup.isHidden() && await page.inputValue("#mg-positive_raw") === value,
            `special syntax suppresses autocomplete: ${value}`);
    }
    await page.fill("#mg-negative_raw", "1gi");
    check(await page.locator("#mg-negative_raw").locator("xpath=..").locator(".tag-autocomplete-popup").isHidden(),
        "Negative Prompt remains unmodified by default");

    await page.evaluate(() => window.__tegakiManga.setMangaMode("authoring"));
    await page.click("#scene-prompt-tab-global");
    await page.fill("#scene-composer-prompt", "1gi");
    const composerPopup = page.locator("#scene-composer-prompt").locator("xpath=..").locator(".tag-autocomplete-popup");
    await composerPopup.waitFor({ state: "visible" });
    await composerPopup.locator("[role=option]").first().click();
    check(await page.inputValue("#scene-composer-prompt") === "1girl, " &&
        await page.evaluate(() => window.__tegakiManga.store.getPage().style_prompt === "1girl, "),
        "Global positive Prompt attaches to the shared controller and Store field");

    await page.click("#scene-prompt-tab-scene_top");
    await page.fill("#scene-composer-prompt", "long_h");
    await composerPopup.waitFor({ state: "visible" });
    await composerPopup.locator("[role=option]").first().click();
    check(await page.evaluate(() => {
        const page = window.__tegakiManga.store.getPage();
        return page.scenes[0].prompt === "long_hair, " && page.style_prompt === "1girl, ";
    }), "Scene 1 positive Prompt writes only its existing scene field");

    await page.click("#scene-prompt-tab-scene_bottom");
    await page.fill("#scene-composer-prompt", "blue_");
    await composerPopup.waitFor({ state: "visible" });
    await composerPopup.locator("[role=option]").first().click();
    check(await page.evaluate(() => {
        const scenes = window.__tegakiManga.store.getPage().scenes;
        return scenes[1].prompt === "blue_eyes, " && scenes[0].prompt === "long_hair, ";
    }), "Scene 2 autocomplete remains isolated from Scene 1");

    await page.click("#scene-prompt-tab-scene_top");
    check(await page.inputValue("#scene-composer-prompt") === "long_hair, ",
        "Scene switching preserves prompt text and one controller attachment");
    check(catalogRequests === 1, "typing and scene switching never fetch per keystroke");

    const failedPage = await browser.newPage({ viewport: { width: 1280, height: 800 } });
    const failedErrors = [];
    failedPage.on("pageerror", error => failedErrors.push(error.message));
    let failedCatalogRequests = 0;
    await failedPage.route("**/data/danbooru_tags.json", async route => {
        failedCatalogRequests += 1;
        await route.fulfill({ status: 404, contentType: "text/plain", body: "missing fixture" });
    });
    await failedPage.goto(origin, { waitUntil: "networkidle" });
    await failedPage.waitForFunction(() => document.querySelector("#mg-positive_raw")?.dataset.tagAutocompleteState === "unavailable");
    await failedPage.evaluate(() => window.__tegakiManga.setMangaMode("generate"));
    await failedPage.fill("#mg-positive_raw", "1gi");
    check(await failedPage.inputValue("#mg-positive_raw") === "1gi" &&
        await failedPage.locator("#mg-positive_raw").locator("xpath=..").locator(".tag-autocomplete-popup").isHidden() &&
        failedCatalogRequests === 1, "Catalog load failure leaves prompt editing usable");
    check(failedErrors.length === 0, `catalog failure browser errors: ${failedErrors.join("; ")}`);
    await failedPage.close();

    check(pageErrors.length === 0, `browser errors: ${pageErrors.join("; ")}`);
    check(promptCalls === 0, "PLAY3 fixture performed no /prompt submission");
    console.log(`MANGA-PLAY3 BROWSER FIXTURE PASS: ${checks} checks; catalog requests ${catalogRequests}; /prompt calls ${promptCalls}; real generation 0`);
} finally {
    if (browser) await browser.close();
    if (workspace) await close(workspace);
    await close(backend);
    for (const [key, value] of Object.entries(previous)) {
        if (value === undefined) delete process.env[key]; else process.env[key] = value;
    }
    await fs.rm(journalDir, { recursive: true, force: true });
}
