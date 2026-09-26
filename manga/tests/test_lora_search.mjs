// MANGA-PROMPT-VALIDATION-COHERENCE1: LoRA search over the TRUSTED index (no disk scan).
import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import { mountLoraPanel, searchLoraIndex } from "../app/src/view/lora_panel.js";
import { normalizeLoraList } from "../app/src/view/tag_autocomplete.js";

// Payload shape of /api/manga/resources/lora/index (trusted root; token chosen by the backend).
const INDEX = normalizeLoraList({ entries: [
    { id: "!!!Ani/Ani0H/2000s_anime_style.safetensors", token: "2000s_anime_style", folder: "!!!Ani/Ani0H" },
    { id: "!!!kawaii/0/Onono_Imoko .safetensors", token: "Onono_Imoko .safetensors", folder: "!!!kawaii/0" },
    { id: "characters/A/dup.safetensors", token: "characters/A/dup", folder: "characters/A" },
    { id: "styles/dup.safetensors", token: "styles/dup", folder: "styles" },
    { id: "styles/InkWash.safetensors", token: "InkWash", folder: "styles" },
] });

test("unique-name, folder/context and case-insensitive search over the trusted index", () => {
    assert.deepEqual(searchLoraIndex(INDEX, "inkwash").items.map(i => [i.id, i.token]), [["styles/InkWash.safetensors", "InkWash"]]);
    assert.deepEqual(searchLoraIndex(INDEX, "INK").items.map(i => i.name), ["InkWash"]);
    assert.deepEqual(searchLoraIndex(INDEX, "kawaii").items.map(i => i.id), ["!!!kawaii/0/Onono_Imoko .safetensors"]);
    assert.deepEqual(searchLoraIndex(INDEX, "ani0h").items.map(i => i.folder), ["!!!Ani/Ani0H"]);
    const dups = searchLoraIndex(INDEX, "dup").items;
    assert.deepEqual(dups.map(i => [i.name, i.folder, i.token]),
        [["dup", "characters/A", "characters/A/dup"], ["dup", "styles", "styles/dup"]], "duplicate basenames keep canonical tokens");
    assert.deepEqual(searchLoraIndex(INDEX, "  ").items, []);
    assert.equal(searchLoraIndex(INDEX, "a", { limit: 2 }).items.length, 2);
    assert.ok(searchLoraIndex(INDEX, "a", { limit: 2 }).total > 2, "total reported beyond the display cap");
});

test("preview availability only from already-loaded folder data; no paths", () => {
    const folderCache = new Map([["styles", { loras: [{ id: "styles/InkWash.safetensors", preview: true }] }]]);
    const [ink] = searchLoraIndex(INDEX, "inkwash", { folderCache }).items;
    assert.equal(ink.preview, true);
    assert.equal(searchLoraIndex(INDEX, "inkwash").items[0].preview, false);
    assert.ok(!/[A-Za-z]:[\\/]|Models/.test(JSON.stringify(searchLoraIndex(INDEX, "a").items)));
});

test("panel: results span folders, selected state, Add/Remove, clear returns to folder mode, no folder fetch per query", async () => {
    const dom = fakeDom();
    const prompt = dom.input("textarea");
    prompt.value = "1girl, <lora:styles/dup:0.4>";
    const search = dom.input("input");
    const fetched = [];
    const panelEls = { panel: dom.node(), body: dom.node(), status: dom.node(), breadcrumb: dom.node(), folders: dom.node(),
        cards: dom.node(), count: dom.node() };
    let indexLoads = 0;
    const view = mountLoraPanel({ ...panelEls, toggle: null, prompt, search,
        fetchFolder: async dir => { fetched.push(dir); return { folders: [{ id: "styles", name: "styles" }], loras: [] }; },
        loadIndex: async () => { indexLoads += 1; return INDEX; } });
    view.setExpanded(true);
    await tick();
    assert.deepEqual(fetched, [""], "only the opened folder is listed");

    await view.search("DUP");
    const cards = () => panelEls.cards.children.filter(c => c.dataset.loraId);
    assert.deepEqual(cards().map(c => [c.dataset.loraId, c.cls["is-selected"]]),
        [["characters/A/dup.safetensors", false], ["styles/dup.safetensors", true]], "selected state from the prompt");
    assert.equal(panelEls.breadcrumb.hidden, true);
    assert.match(panelEls.status.textContent, /2 matches across folders/);
    // folder context is shown for search results
    assert.ok(cards()[0].children.some(ch => ch.className === "mg-lora-card-folder" && ch.textContent === "characters/A"));

    const action = card => card.children.find(ch => ch.className === "mg-lora-card-controls").children[1];
    action(cards()[0]).onclick();
    assert.equal(prompt.value, "1girl, <lora:styles/dup:0.4>, <lora:characters/A/dup:1.0>", "Add inserts the canonical token for a duplicate basename");
    action(cards()[1]).onclick();
    assert.equal(prompt.value, "1girl, <lora:characters/A/dup:1.0>", "Remove from results; other text/order untouched");

    await view.search("inkwash");
    action(cards()[0]).onclick();
    assert.equal(prompt.value, "1girl, <lora:characters/A/dup:1.0>, <lora:InkWash:1.0>", "portable token for a unique basename");

    await view.search("");
    assert.equal(panelEls.breadcrumb.hidden, false, "clear returns to normal folder browsing");
    assert.equal(cards().length, 0);
    assert.ok(panelEls.cards.children.some(c => /No LoRA files in this folder/.test(c.textContent)));
    assert.deepEqual(fetched, [""], "searching never listed folders or scanned disk");
    assert.ok(indexLoads >= 1);
});

test("the search strategy never touches the filesystem browse route", () => {
    const src = fs.readFileSync(new URL("../app/src/view/lora_panel.js", import.meta.url), "utf8");
    const fn = src.slice(src.indexOf("export function searchLoraIndex"), src.indexOf("export function mountLoraPanel"));
    assert.ok(!/fetch|resources\/lora\?/.test(fn));
});

// --- minimal DOM stand-in -------------------------------------------------------------
const tick = () => new Promise(resolve => setTimeout(resolve, 0));
function fakeDom() {
    const make = tag => {
        const node = { tagName: tag, children: [], className: "", textContent: "", hidden: false, dataset: {}, attrs: {},
            cls: {}, listeners: {}, value: "", onclick: null, onchange: null, disabled: false };
        node.classList = { toggle(name, on) { node.cls[name] = on === undefined ? !node.cls[name] : Boolean(on); }, add(name) { node.cls[name] = true; },
            remove(name) { node.cls[name] = false; } };
        node.append = (...kids) => { node.children.push(...kids); };
        node.appendChild = kid => { node.children.push(kid); return kid; };
        node.replaceChildren = () => { node.children = []; };
        node.setAttribute = (k, v) => { node.attrs[k] = v; };
        node.getAttribute = k => node.attrs[k];
        node.addEventListener = (type, fn) => { (node.listeners[type] ||= []).push(fn); };
        node.dispatchEvent = event => { for (const fn of node.listeners[event.type] || []) fn(event); return true; };
        node.replaceWith = () => {};
        Object.defineProperty(node, "childElementCount", { get: () => node.children.length });
        return node;
    };
    globalThis.document = { createElement: make };
    globalThis.Event = class { constructor(type) { this.type = type; } };
    return { node: () => make("div"), input: tag => make(tag) };
}
