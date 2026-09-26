// MANGA-PROMPT-PRODUCTION-UX1: presets, default prompt, Ctrl+Up/Down weights, coherence.
import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import {
    MAX_PRESETS, MAX_PROMPT_CHARS, PROMPT_PREFS_KEY, applyDefaultToNewDocument, applyTextEdit, attachWeightKeys,
    computeWeightEdit, createPromptPrefs, formatPromptWeight, mountPromptPresets,
} from "../app/src/view/prompt_production.js";
import { AuthoringStore, createNewAuthoringSessionDocument } from "../app/src/state/authoring_store.js";
import { STYLE_PRESETS } from "../app/src/domain/authoring_document.js";
import { createLoraValidator, loraBlockReasonFromDiagnostics } from "../app/src/view/lora_panel.js";

class MemStorage {
    constructor() { this.map = new Map(); this.fail = false; }
    getItem(k) { return this.map.has(k) ? this.map.get(k) : null; }
    setItem(k, v) { if (this.fail) throw new Error("QuotaExceededError"); this.map.set(k, String(v)); }
}
const MIKI = "<lora:Miki_Hoshii__The_iDOLM_STER_2011__epoch_8:0.3>";
const RICH = { positive: `1girl, __lora_!kawa2604__, ${MIKI},\n(smile:1.2), 日本語 {a|b}`, negative: "bad hands, <lora:neg__x__:-0.2>" };
const BUILT_IN = { positive: STYLE_PRESETS["Manga Monochrome"].prompt, negative: STYLE_PRESETS["Manga Monochrome"].negative };

test("presets A,D,E,F,G,I: verbatim pair, no silent overwrite, explicit Replace, survives reload", () => {
    const storage = new MemStorage();
    const prefs = createPromptPrefs({ storage });
    assert.equal(prefs.save("  daily  ", RICH).ok, true);
    assert.deepEqual(prefs.get("daily"), { name: "daily", ...RICH }, "name trimmed, LoRA/Wildcard/newlines/Unicode byte-for-byte");
    const dup = prefs.save("daily", { positive: "other", negative: "" });
    assert.equal(dup.code, "EXISTS");
    assert.equal(prefs.get("daily").positive, RICH.positive, "no silent overwrite");
    assert.equal(prefs.save("daily", { positive: "other", negative: "n" }, { replace: true }).ok, true);
    assert.equal(prefs.get("daily").positive, "other");
    assert.equal(prefs.save("   ", RICH).code, "EMPTY_NAME");
    const reloaded = createPromptPrefs({ storage }); // page reload = fresh store over the same storage
    assert.deepEqual(reloaded.list().map(p => p.name), ["daily"]);
    assert.ok(JSON.parse(storage.getItem(PROMPT_PREFS_KEY)).version === 1);
});

test("presets J,K: storage failure and limits are explicit and keep existing data", () => {
    const storage = new MemStorage();
    const prefs = createPromptPrefs({ storage });
    prefs.save("keep", RICH);
    storage.fail = true;
    const failed = prefs.save("new", RICH);
    assert.equal(failed.code, "STORAGE_FAILED");
    assert.match(failed.error, /Existing presets were kept/);
    assert.deepEqual(prefs.list().map(p => p.name), ["keep"], "in-memory state unchanged");
    assert.equal(prefs.remove("keep").ok, false);
    storage.fail = false;
    assert.deepEqual(createPromptPrefs({ storage }).list().map(p => p.name), ["keep"], "stored data unchanged");
    const big = prefs.save("big", { positive: "x".repeat(MAX_PROMPT_CHARS + 1), negative: "" });
    assert.equal(big.code, "TOO_LARGE");
    assert.equal(prefs.get("keep").positive, RICH.positive, "nothing truncated");
    for (let i = prefs.list().length; i < MAX_PRESETS; i += 1) assert.equal(prefs.save(`p${i}`, RICH).ok, true);
    assert.equal(prefs.save("one-too-many", RICH).code, "LIMIT");
    assert.equal(prefs.list().length, MAX_PRESETS);
});

test("presets B,C,H + UI: Apply replaces only the Global pair, Delete never touches the prompt", () => {
    const dom = fakeDom();
    const storage = new MemStorage();
    const prefs = createPromptPrefs({ storage });
    const store = new AuthoringStore(createNewAuthoringSessionDocument());
    store.addScene?.({ name: "S", prompt: "scene prompt, <lora:s:1>" });
    const sceneBefore = JSON.stringify(store.getPage().scenes);
    assert.equal(store.getPage().scenes.length, 1, "fixture has a Scene prompt");
    const container = dom.make("details");
    let applied = 0;
    mountPromptPresets({ container, prefs,
        getGlobalPair: () => ({ positive: store.getPage().style_prompt, negative: store.getPage().style_negative_prompt }),
        applyGlobalPair: (pair) => { applied += 1; store.setStyleMetadata({ stylePrompt: pair.positive, styleNegativePrompt: pair.negative }); } });
    const [summary, row, row2, status] = container.children;
    const [select, applyBtn, deleteBtn, nameInput, saveBtn] = row.children;
    const [setDefaultBtn, applyDefaultBtn, clearDefaultBtn] = row2.children;
    store.setStyleMetadata({ stylePrompt: RICH.positive, styleNegativePrompt: RICH.negative });
    nameInput.value = "rich"; saveBtn.onclick();
    assert.match(status.textContent, /Saved preset "rich"/);
    store.setStyleMetadata({ stylePrompt: "changed", styleNegativePrompt: "changed neg" });
    nameInput.value = "rich"; saveBtn.onclick();
    assert.equal(saveBtn.textContent, "Replace", "same name -> explicit Replace state, no overwrite yet");
    assert.equal(prefs.get("rich").positive, RICH.positive);
    select.value = "rich"; select.onchange();
    assert.equal(saveBtn.textContent, "Save current", "leaving the name resets the confirmation");
    applyBtn.onclick();
    assert.equal(applied, 1);
    assert.deepEqual([store.getPage().style_prompt, store.getPage().style_negative_prompt], [RICH.positive, RICH.negative]);
    assert.equal(JSON.stringify(store.getPage().scenes), sceneBefore, "Scene prompts untouched");
    deleteBtn.onclick();
    assert.equal(deleteBtn.textContent, "Confirm delete");
    assert.ok(prefs.get("rich"), "first click only asks");
    deleteBtn.onclick();
    assert.equal(prefs.get("rich"), null);
    assert.equal(store.getPage().style_prompt, RICH.positive, "Delete does not alter the current prompt");
    assert.ok(!JSON.stringify(store.getDocument()).includes("rich\""), "presets never enter the Authoring Document");
    assert.equal(applyDefaultBtn.disabled, true);
    setDefaultBtn.onclick();
    assert.equal(applyDefaultBtn.disabled, false);
    clearDefaultBtn.onclick();
    assert.equal(prefs.getDefault(), null);
    assert.equal(summary.textContent, "Prompt presets");
});

test("default A-F: stored pair, only a pristine new document gets it, clear restores built-in", () => {
    const storage = new MemStorage();
    const prefs = createPromptPrefs({ storage });
    assert.equal(prefs.setDefault(RICH).ok, true);
    assert.deepEqual(createPromptPrefs({ storage }).getDefault(), RICH, "A: both fields stored, survives reload");
    const fresh = new AuthoringStore(createNewAuthoringSessionDocument());
    assert.equal(applyDefaultToNewDocument(fresh, prefs, BUILT_IN), true, "F: new session document gets it");
    assert.deepEqual([fresh.getPage().style_prompt, fresh.getPage().style_negative_prompt], [RICH.positive, RICH.negative]);
    const loaded = new AuthoringStore(); // default doc with Scenes = loaded/fixture-like content
    const loadedBefore = loaded.getPage().style_prompt;
    assert.equal(applyDefaultToNewDocument(loaded, prefs, BUILT_IN), false, "B: document with Scenes untouched");
    assert.equal(loaded.getPage().style_prompt, loadedBefore);
    const edited = new AuthoringStore(createNewAuthoringSessionDocument());
    edited.setStyleMetadata({ stylePrompt: "my own work" });
    assert.equal(applyDefaultToNewDocument(edited, prefs, BUILT_IN), false, "C: non-pristine prompt untouched");
    assert.equal(edited.getPage().style_prompt, "my own work");
    prefs.clearDefault();
    const baseline = new AuthoringStore(createNewAuthoringSessionDocument());
    assert.equal(applyDefaultToNewDocument(baseline, prefs, BUILT_IN), false, "D: cleared -> built-in behaviour");
    assert.equal(baseline.getPage().style_prompt, BUILT_IN.positive);
    const html = fs.readFileSync(new URL("../app/index.html", import.meta.url), "utf8");
    const boot = html.indexOf("new AuthoringStore(createNewAuthoringSessionDocument())");
    assert.ok(boot > 0 && html.indexOf("applyDefaultToNewDocument(store, promptPrefs", boot) > boot,
        "auto-apply only at the page's own new-document bootstrap");
    assert.equal((html.match(/applyDefaultToNewDocument\(/g) || []).length, 1, "never on import/fixture/reset paths");
});

const edit = (text, s, e, dir) => {
    const r = computeWeightEdit(text, s, e, dir);
    return r && { value: text.slice(0, r.start) + r.replacement + text.slice(r.end), sel: [r.selStart, r.selEnd] };
};

test("weights: plain selection, existing groups, repeated stable target, clean formatting", () => {
    assert.deepEqual(edit("a, smile, b", 3, 8, 1), { value: "a, (smile:1.1), b", sel: [4, 9] });
    assert.equal(edit("a, smile, b", 3, 8, -1).value, "a, (smile:0.9), b");
    let v = "a, smile, b"; let sel = [3, 8];
    for (let i = 0; i < 3; i += 1) { const r = edit(v, sel[0], sel[1], 1); v = r.value; sel = r.sel; }
    assert.equal(v, "a, (smile:1.3), b", "Up x3 keeps operating on the same group");
    assert.equal(edit("(smile:1.1)", 0, 11, 1).value, "(smile:1.2)");
    assert.equal(edit("(smile:1.1)", 0, 11, -1).value, "(smile:1)");
    let down = "(x:0.1)";
    for (let i = 0; i < 3; i += 1) { const r = edit(down, 3, 3, -1); down = r.value; }
    assert.equal(down, "(x:-0.2)", "negative weights allowed, no LoRA clamp for prompt weights");
    assert.deepEqual([1, 1.1, 0.9, -0.2, 0.1 + 0.2, 1.2000000000000002].map(formatPromptWeight), ["1", "1.1", "0.9", "-0.2", "0.3", "1.2"]);
    assert.equal(edit("x, (smile:1.2), y", 7, 7, 1).value, "x, (smile:1.3), y", "caret inside explicit weight");
});

test("weights: LoRA strength via caret, Miki '__' name intact, bounds respected, malformed/no-context no-op", () => {
    assert.equal(edit("a, <lora:foo:0.3>", 8, 8, 1).value, "a, <lora:foo:0.4>");
    assert.equal(edit("a, <lora:foo:0.3>", 8, 8, -1).value, "a, <lora:foo:0.2>");
    const miki = edit(`x, ${MIKI}`, 10, 10, 1).value;
    assert.equal(miki, "x, <lora:Miki_Hoshii__The_iDOLM_STER_2011__epoch_8:0.4>");
    assert.equal(edit("<lora:日本 名/a b:1>", 3, 3, 1).value, "<lora:日本 名/a b:1.1>", "Unicode/space/folder names kept");
    assert.equal(computeWeightEdit("<lora:foo:4>", 3, 3, 1), null, "next step outside the LoRA domain -> no edit");
    assert.equal(computeWeightEdit("<lora:foo:-4>", 3, 3, -1), null);
    for (const [t, s, e] of [["(broken:1.1", 3, 3], ["<lora:foo:abc>", 3, 3], ["plain words", 3, 3], ["", 0, 0],
        ["(a:1.1), (b:1.2)", 0, 16], ["x <lora:y:1> z", 0, 14]]) {
        assert.equal(computeWeightEdit(t, s, e, 1), null, `no-op: ${t}`);
    }
});

test("keys: Ctrl only, never during IME or while autocomplete owns the key; one undoable input edit", () => {
    const events = [];
    const ta = { value: "a, smile", selectionStart: 3, selectionEnd: 8, listeners: {},
        addEventListener(t, f) { this.listeners[t] = f; }, removeEventListener() {},
        setSelectionRange(a, b) { this.selectionStart = a; this.selectionEnd = b; }, focus() {},
        dispatchEvent(e) { events.push(e.type); } };
    let popupOpen = false;
    attachWeightKeys(ta, { isAutocompleteOpen: () => popupOpen, doc: {} });
    const key = (props) => { const e = { key: "ArrowUp", ctrlKey: true, preventDefault() { this.prevented = true; }, ...props }; ta.listeners.keydown(e); return e; };
    assert.equal(key({ ctrlKey: false }).prevented, undefined, "plain ArrowUp untouched");
    assert.equal(ta.value, "a, smile");
    key({ isComposing: true });
    key({ keyCode: 229 });
    popupOpen = true; key({}); popupOpen = false;
    key({ defaultPrevented: true });
    assert.equal(ta.value, "a, smile", "IME / autocomplete / already-handled: no transform");
    assert.equal(key({}).prevented, true);
    assert.equal(ta.value, "a, (smile:1.1)");
    assert.deepEqual([ta.selectionStart, ta.selectionEnd], [4, 9]);
    key({ key: "ArrowDown" });
    assert.equal(ta.value, "a, (smile:1)");
    assert.deepEqual(events, ["input", "input"], "each edit is one normal input event (store + validation)");
});

test("coherence: after preset Apply / weight / LoRA strength edits the gate reflects the CURRENT text", async () => {
    const calls = [];
    const validator = createLoraValidator({ fetchImpl: async (_u, init) => {
        const { sources } = JSON.parse(init.body);
        const names = [...sources[0].text.matchAll(/<lora:([^:<>]+):([^>]+)>/g)].map(m => [m[1], Number(m[2])]);
        calls.push(sources[0].text);
        const entries = names.map(([n, w]) => (w <= 1 ? { name: n, status: "RESOLVED" } : { name: n, status: "INVALID_STRENGTH" }));
        return { ok: true, status: 200, json: async () => ({ ok: true, entries, chain: [], problems: 0 }) };
    } });
    const gate = async (text) => {
        const sources = [{ source: "page_positive", text }];
        const r = validator.peek(sources) || await validator.request(sources);
        return loraBlockReasonFromDiagnostics(r);
    };
    let text = "a, <lora:foo:1.0>";
    assert.equal(await gate(text), "");
    const up = edit(text, 5, 5, 1); text = up.value;
    assert.equal(text, "a, <lora:foo:1.1>");
    assert.match(await gate(text), /INVALID STRENGTH/, "new text validated, not the stale snapshot");
    text = edit(text, 5, 5, -1).value;
    assert.equal(await gate(text), "");
    assert.deepEqual(calls, ["a, <lora:foo:1.0>", "a, <lora:foo:1.1>"], "one request per distinct text; revisits reuse");
});

// --- minimal DOM ---------------------------------------------------------------------
function fakeDom() {
    const make = tag => {
        const node = { tagName: tag, children: [], className: "", textContent: "", value: "", disabled: false, dataset: {},
            attrs: {}, cls: {}, onclick: null, onchange: null, oninput: null, type: "", placeholder: "", maxLength: 0 };
        node.classList = { toggle(n, on) { node.cls[n] = Boolean(on); } };
        node.append = (...k) => { node.children.push(...k); };
        node.appendChild = k => { node.children.push(k); return k; };
        node.replaceChildren = () => { node.children = []; };
        node.setAttribute = (k, v) => { node.attrs[k] = v; };
        return node;
    };
    globalThis.document = { createElement: make };
    globalThis.Event = globalThis.Event || class { constructor(t) { this.type = t; } };
    return { make };
}
