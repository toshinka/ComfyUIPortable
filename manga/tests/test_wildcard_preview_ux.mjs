// WILDCARD-PREVIEW-OWNER-UX1: persistent Wildcard preview (no timer), full wrapped content,
// dismissal by outside click / scroll / x / target change / stale context, replacement.
// A minimal DOM stand-in drives the real mountWildcardPreview; CSS rules are checked from
// the shipped stylesheet (real layout is proven in the live Manga browser acceptance).
import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import { mountWildcardPreview, wildcardPreviewCountText } from "../app/src/view/prompt_assist.js";

class Node_ {
    constructor(tag) { this.tagName = tag; this.children = []; this.parent = null; this.className = ""; this.textContent = "";
        this.dataset = {}; this.hidden = false; this.attrs = {}; this.onclick = null; }
    appendChild(child) { child.parent = this; this.children.push(child); return child; }
    append(...kids) { kids.forEach(k => this.appendChild(k)); }
    replaceChildren() { this.children.forEach(c => { c.parent = null; }); this.children = []; }
    setAttribute(k, v) { this.attrs[k] = v; }
    contains(n) { for (let x = n; x; x = x.parent) if (x === this) return true; return false; }
    closest(sel) { const cls = sel.replace(/^\./, ""); for (let x = this; x; x = x.parent) if (x.className.split(" ").includes(cls)) return x; return null; }
    find(cls) { if (this.className.split(" ").includes(cls)) return this; for (const c of this.children) { const f = c.find(cls); if (f) return f; } return null; }
    all(tag) { const out = this.tagName === tag ? [this] : []; for (const c of this.children) out.push(...c.all(tag)); return out; }
}
function makeDom() {
    const listeners = new Map();
    const target = { addEventListener(t, f) { listeners.set(t, f); }, removeEventListener(t, f) { if (listeners.get(t) === f) listeners.delete(t); } };
    const win = { ...target };
    const doc = { ...target, defaultView: win, createElement: tag => new Node_(tag), documentElement: null, body: null };
    doc.body = new Node_("body");
    const scroller = doc.body.appendChild(new Node_("main"));
    const assist = scroller.appendChild(new Node_("section"));
    const prompt = scroller.appendChild(new Node_("textarea"));
    const container = scroller.appendChild(new Node_("div"));
    container.hidden = true;
    const other = scroller.appendChild(new Node_("button"));
    const popup = doc.body.appendChild(new Node_("div")); popup.className = "tag-autocomplete-popup";
    const option = popup.appendChild(new Node_("div"));
    const fire = (type, t) => listeners.get(type)?.({ target: t });
    return { doc, win, listeners, scroller, assist, prompt, container, other, option, fire };
}
const LONG = "x".repeat(4000);
const payloads = {
    long: { ok: true, entries: [LONG], total: 1 },
    many: { ok: true, entries: Array.from({ length: 500 }, (_, i) => `entry ${i}`), total: 500 },
    "character/hair": { ok: true, entries: ["long hair", "short hair"], total: 2 },
};
const fetchImpl = async url => ({ json: async () => payloads[decodeURIComponent(url.split("name=")[1])] });
const globalDoc = makeDom().doc;
globalThis.document = globalDoc; // el() uses document.createElement

function mount(dom) {
    return mountWildcardPreview({ container: dom.container, keepOpenWithin: [dom.assist, dom.prompt], fetchImpl, doc: dom.doc });
}

test("A/B: long single entry and all multiline entries are rendered whole", async () => {
    const dom = makeDom(); const p = mount(dom);
    await p.show("long");
    assert.deepEqual(dom.container.all("li").map(li => li.textContent), [LONG]);
    await p.show("many");
    assert.equal(dom.container.all("li").length, 500);
    assert.equal(dom.container.find("mg-wildcard-preview-count").textContent, "500 entries");
    assert.equal(dom.container.find("mg-wildcard-preview-token").textContent, "__many__");
    assert.equal(wildcardPreviewCountText({ entries: ["a"], total: 1 }), "1 entry");
    assert.match(wildcardPreviewCountText({ entries: ["a", "b"], total: null }), /^2 entries shown .*total unknown$/);
});

test("C/D/E: CSS wraps instead of ellipsis, natural height, internal scroll cap only for large content", () => {
    const css = fs.readFileSync(new URL("../app/css/manga_workspace.css", import.meta.url), "utf8");
    const rule = sel => (css.match(new RegExp(sel.replace(/[.*+?^${}()|[\]\\]/g, "\\$&") + "\\s*\\{([^}]*)\\}")) || [])[1] || "";
    const li = rule(".mg-wildcard-preview-list li");
    const list = rule(".mg-wildcard-preview-list");
    const box = rule(".mg-wildcard-preview");
    assert.ok(!/text-overflow|nowrap/.test(li), "no ellipsis / single-line strip");
    assert.match(li, /white-space:\s*pre-wrap/);
    assert.match(li, /overflow-wrap:\s*anywhere/);
    assert.ok(!/(^|[^-])height\s*:/.test(box + list), "no fixed height: grows with content");
    assert.match(list, /max-height:\s*\d+px/);
    assert.match(list, /overflow-y:\s*auto/);
});

test("F/L: no timer dismissal; the opening gesture cannot dismiss its own preview", async () => {
    const realSetTimeout = globalThis.setTimeout;
    let timers = 0;
    globalThis.setTimeout = (...a) => { timers += 1; return realSetTimeout(...a); };
    try {
        const dom = makeDom(); const p = mount(dom);
        assert.equal(dom.listeners.has("pointerdown"), false, "not listening before a preview exists");
        const pending = p.show("long");
        dom.fire("pointerdown", dom.option); // selection gesture happened before render
        await pending;
        assert.equal(timers, 0, "no setTimeout used");
        assert.equal(p.visible, true);
        assert.equal(dom.listeners.has("pointerdown"), true);
        dom.fire("pointerdown", dom.option);
        dom.fire("pointerdown", dom.assist);
        dom.fire("pointerdown", dom.prompt);
        dom.fire("pointerdown", dom.container.find("mg-wildcard-preview-list"));
        assert.equal(p.visible, true, "clicks inside preview / Prompt Assist / prompt / popup keep it");
    } finally { globalThis.setTimeout = realSetTimeout; }
    assert.ok(!/setTimeout|durationMs/.test(mountWildcardPreview.toString()));
});

test("G: outside click dismisses and removes listeners", async () => {
    const dom = makeDom(); const p = mount(dom);
    await p.show("long");
    dom.fire("pointerdown", dom.other);
    assert.equal(p.visible, false);
    assert.equal(dom.container.children.length, 0);
    assert.equal(dom.listeners.size, 0, "all listeners removed on dismiss");
});

test("H: workspace scroll dismisses; scrolling the preview list or textarea does not", async () => {
    const dom = makeDom(); const p = mount(dom);
    await p.show("many");
    dom.fire("scroll", dom.container.find("mg-wildcard-preview-list"));
    dom.fire("scroll", dom.prompt);
    assert.equal(p.visible, true);
    dom.fire("scroll", dom.scroller);
    assert.equal(p.visible, false);
    await p.show("many");
    dom.fire("scroll", dom.doc);
    assert.equal(p.visible, false, "document scroll dismisses");
});

test("I: close button dismisses", async () => {
    const dom = makeDom(); const p = mount(dom);
    await p.show("long");
    dom.container.find("mg-wildcard-preview-close").onclick();
    assert.equal(p.visible, false);
});

test("J: target change (hide) and stale navigation dismiss", async () => {
    const dom = makeDom(); const p = mount(dom);
    await p.show("long");
    p.hide(); // index.html calls hide() when the prompt target changes
    assert.equal(p.visible, false);
    for (const type of ["hashchange", "popstate", "pagehide"]) {
        await p.show("long");
        dom.fire(type, dom.win);
        assert.equal(p.visible, false, type);
    }
    const html = fs.readFileSync(new URL("../app/index.html", import.meta.url), "utf8");
    assert.match(html, /wildcardPreviewTarget !== composerPromptTarget\) wildcardPreview\.hide\(\)/);
});

test("K: selecting another Wildcard replaces the preview (nested included); late replies are ignored", async () => {
    const dom = makeDom(); const p = mount(dom);
    await p.show("long");
    const a = p.show("many"); const b = p.show("character/hair");
    await Promise.all([a, b]);
    assert.equal(dom.container.dataset.wildcard, "character/hair");
    assert.deepEqual(dom.container.all("li").map(li => li.textContent), ["long hair", "short hair"]);
    assert.equal(dom.container.find("mg-wildcard-preview-token").textContent, "__character/hair__");
    assert.equal(dom.container.all("ul").length, 1, "one preview, no stacking");
});

// MANGA-PROMPT-VALIDATION-COHERENCE1: explicit Expand on the accepted preview.
test("Expand: replaces exactly the tracked occurrence with one backend expansion; refuses ambiguity", async () => {
    const { applyWildcardExpansion, expandWildcardInPrompt, locateWildcardOccurrence } = await import("../app/src/view/prompt_assist.js");
    const text = "1girl, __style__, smile, __style__";
    assert.deepEqual(locateWildcardOccurrence(text, "style", 7), { start: 7, end: 16, token: "__style__" });
    assert.deepEqual(locateWildcardOccurrence(text, "style", 3), { error: "ambiguous", token: "__style__" }, "stale offset + 2 copies -> refuse");
    assert.deepEqual(locateWildcardOccurrence("x", "style", 0), { error: "missing", token: "__style__" });
    assert.equal(locateWildcardOccurrence("a, __style__", "style", 99).start, 3, "single occurrence is unambiguous");
    assert.equal(applyWildcardExpansion(text, "style", 25, "<lora:ink:0.4>, mono").value,
        "1girl, __style__, smile, <lora:ink:0.4>, mono", "only the tracked occurrence; other text untouched");

    const events = [];
    const prompt = { value: "1girl, __character/hair__, smile", focus() {}, setSelectionRange(a, b) { this.sel = [a, b]; },
        dispatchEvent(e) { events.push(e.type); } };
    const calls = [];
    const fetchImpl = async (url, init) => { calls.push([url, JSON.parse(init.body)]);
        return { ok: true, status: 200, json: async () => ({ ok: true, name: "character/hair", expanded_text: "long hair" }) }; };
    const outcome = await expandWildcardInPrompt({ prompt, name: "character/hair", start: 7, fetchImpl, doc: {} });
    assert.equal(outcome.ok, true);
    assert.equal(prompt.value, "1girl, long hair, smile");
    assert.deepEqual(calls, [["/api/manga/wildcards/expand", { name: "character/hair" }]]);
    assert.deepEqual(events, ["input"], "normal input event -> store + LoRA diagnostics validate the expansion");

    const twice = { ...prompt, value: "__a__, __a__", dispatchEvent() {} };
    const refused = await expandWildcardInPrompt({ prompt: twice, name: "a", start: 3, fetchImpl, doc: {} });
    assert.equal(refused.ok, false);
    assert.match(refused.message, /more than once/);
    assert.equal(twice.value, "__a__, __a__", "nothing replaced when the occurrence is not identifiable");
});

test("Expand button: passes the insertion occurrence, hides on success, reports failure in place", async () => {
    const dom = makeDom();
    const seen = [];
    let answer = { ok: false, message: "Backend does not provide Wildcard expansion" };
    const p = mountWildcardPreview({ container: dom.container, keepOpenWithin: [dom.assist, dom.prompt], fetchImpl, doc: dom.doc,
        expand: async (name, start) => { seen.push([name, start]); return answer; } });
    await p.show("character/hair", { start: 12 });
    const button = dom.container.find("mg-wildcard-preview-expand");
    assert.equal(button.textContent, "Expand");
    await button.onclick();
    assert.deepEqual(seen, [["character/hair", 12]]);
    assert.equal(p.visible, true, "failure keeps the preview");
    assert.match(dom.container.find("mg-wildcard-preview-expand-note").textContent, /does not provide/);
    answer = { ok: true };
    await button.onclick();
    assert.equal(p.visible, false, "expanded token is gone -> preview dismissed");
});
