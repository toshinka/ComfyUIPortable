// MANGA-LORA-GRID-UX2: global preview slot 1/2/3, image-click Add/Remove, Selected-first ON/OFF,
// compact card CSS.  Real mountLoraPanel on a minimal DOM stand-in; layout proven live.
import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import { findLoraTokens, loraSlotAvailability, mountLoraPanel, nextPreviewSlot } from "../app/src/view/lora_panel.js";
import { mountStageResourcePreview, resetStageResourcePreview } from "../app/src/view/stage_resource_preview.js";

const LISTING = { folders: [], loras: [
    { id: "chars/a.safetensors", name: "a", token: "a", folder: "chars", available: true, preview: true, previews: [true, false, false] },
    { id: "chars/b.safetensors", name: "b", token: "b", folder: "chars", available: true, preview: true, previews: [true, true, false] },
    { id: "chars/c.safetensors", name: "c", token: "c", folder: "chars", available: true, preview: true, previews: [true, true, true] },
    { id: "chars/d.safetensors", name: "d", token: "d", folder: "chars", available: true, preview: false, previews: [false, false, false] },
] };

async function mount(promptText = "") {
    const dom = fakeDom();
    const prompt = dom.make("textarea");
    prompt.value = promptText;
    const els = { panel: dom.make("section"), body: dom.make("div"), status: dom.make("div"), breadcrumb: dom.make("nav"),
        folders: dom.make("div"), cards: dom.make("div"), count: dom.make("span"), viewControls: dom.make("div") };
    const view = mountLoraPanel({ ...els, toggle: null, prompt, fetchFolder: async () => LISTING, loadIndex: async () => [] });
    view.setExpanded(true);
    await new Promise(r => setTimeout(r, 0));
    const cards = () => els.cards.children.filter(c => c.dataset.loraId);
    const card = id => cards().find(c => c.dataset.loraId === `chars/${id}.safetensors`);
    const thumb = c => c.children.find(ch => ch.className === "mg-lora-card-thumbbtn");
    const media = c => thumb(c).children[0];
    const action = c => c.children.find(ch => ch.className === "mg-lora-card-controls").children[1];
    const slotButtons = () => els.viewControls.children[1].children;
    const selFirst = () => els.viewControls.children[2];
    return { view, prompt, els, cards, card, thumb, media, action, slotButtons, selFirst };
}

test("slot model: fixed 1 -> 2 -> 3 -> 1, availability from listing data, unknown stays unknown", () => {
    assert.deepEqual([1, 2, 3].map(nextPreviewSlot), [2, 3, 1]);
    assert.equal(loraSlotAvailability(LISTING.loras[1], 2), true);
    assert.equal(loraSlotAvailability(LISTING.loras[1], 3), false);
    assert.equal(loraSlotAvailability({ preview: true }, 1), true, "legacy listing flag = slot 1");
    assert.equal(loraSlotAvailability({ preview: true }, 2), null);
    assert.equal(loraSlotAvailability({}, 1), null);
});

test("L/H/I/K: one global slot for every visible card; missing slot is blank, never slot 1", async () => {
    const t = await mount();
    const show = () => t.cards().map(c => {
        const m = t.media(c);
        return m.tagName === "img" ? new URL(m.src, "http://x").searchParams.get("slot") : "BLANK";
    });
    assert.deepEqual([...t.slotButtons()].map(b => [b.textContent, b.attrs["aria-pressed"]]),
        [["1", "true"], ["2", "false"], ["3", "false"]], "default slot 1; exactly three slots");
    assert.deepEqual(show(), ["1", "1", "1", "BLANK"]);
    t.slotButtons()[1].onclick();
    assert.deepEqual(show(), ["BLANK", "2", "2", "BLANK"], "all cards switch together; a lacks _ani -> blank");
    t.slotButtons()[2].onclick();
    assert.deepEqual(show(), ["BLANK", "BLANK", "3", "BLANK"]);
    t.slotButtons()[0].onclick();
    assert.deepEqual(show(), ["1", "1", "1", "BLANK"], "3 -> 1 returns to .preview");
    assert.match(t.media(t.card("d")).textContent, /NO PREVIEW 1/);
    assert.equal(t.view.previewSlot, 1);
});

test("missing-slot failures are remembered: no repeated request storm", async () => {
    const t = await mount();
    const search = { id: "x/y.safetensors", name: "y", token: "y", folder: "x", available: true, fromSearch: true };
    LISTING.loras.push(search);
    await t.view.openFolder("", { refresh: true });
    t.slotButtons()[1].onclick();
    const img = t.media(t.card("y") || t.cards().find(c => c.dataset.loraId === search.id));
    assert.equal(img.tagName, "img", "unknown availability is attempted once");
    img.onerror();
    t.slotButtons()[0].onclick();
    t.slotButtons()[1].onclick();
    assert.equal(t.media(t.cards().find(c => c.dataset.loraId === search.id)).tagName, "div", "not requested again");
    LISTING.loras.pop();
});

test("A-F: image click toggles through the SAME Add/Remove path; blank area too; no duplicates", async () => {
    const t = await mount("1girl");
    t.thumb(t.card("b")).onclick();
    assert.equal(t.prompt.value, "1girl, <lora:b:1.0>", "image click on unselected -> Add");
    t.thumb(t.card("d")).onclick();
    assert.equal(t.prompt.value, "1girl, <lora:b:1.0>, <lora:d:1.0>", "blank preview area also toggles");
    t.thumb(t.card("b")).onclick();
    assert.equal(t.prompt.value, "1girl, <lora:d:1.0>", "image click on selected -> Remove");
    t.action(t.card("b")).onclick();
    const viaButton = t.prompt.value;
    t.action(t.card("b")).onclick();
    t.thumb(t.card("b")).onclick();
    assert.equal(t.prompt.value, viaButton, "button and image produce the same observable result");
    assert.equal(findLoraTokens(t.prompt.value).filter(x => x.id === "b").length, 1, "no duplicate insertion");
    assert.equal(t.action(t.card("b")).textContent, "Remove", "explicit button still present and in sync");
});

test("A-H selected-first: default ON, OFF keeps DOM/catalog order, prompt order never changes", async () => {
    const t = await mount("<lora:c:1.0>, <lora:a:0.5>");
    const dom = () => t.cards().map(c => c.dataset.loraId.split("/")[1][0]);
    assert.equal(t.els.cards.cls["is-selected-first"], true, "default ON");
    assert.equal(t.selFirst().textContent, "Selected first ON");
    assert.deepEqual(dom(), ["a", "b", "c", "d"], "DOM keeps catalog order; ON lifts selected via CSS order");
    t.selFirst().onclick();
    assert.equal(t.els.cards.cls["is-selected-first"], false);
    assert.equal(t.selFirst().textContent, "Selected first OFF");
    assert.deepEqual(t.cards().filter(c => c.cls["is-selected"]).map(c => c.dataset.loraId), ["chars/a.safetensors", "chars/c.safetensors"],
        "selection remains while OFF");
    t.action(t.card("b")).onclick();           // Add while OFF
    assert.deepEqual(dom(), ["a", "b", "c", "d"], "Add while OFF does not move the card");
    t.thumb(t.card("a")).onclick();            // Remove while OFF
    assert.deepEqual(dom(), ["a", "b", "c", "d"], "Remove while OFF does not move the card");
    t.selFirst().onclick();
    assert.equal(t.els.cards.cls["is-selected-first"], true, "ON re-applies");
    t.slotButtons()[2].onclick();
    t.slotButtons()[0].onclick();
    assert.deepEqual(findLoraTokens(t.prompt.value).map(x => x.id), ["c", "b"], "prompt LoRA order untouched by any view change");
    const css = fs.readFileSync(new URL("../app/css/manga_workspace.css", import.meta.url), "utf8");
    assert.match(css, /#mg-lora-cards\.is-selected-first \.mg-lora-card\.is-selected \{ order: -1; \}/);
    assert.ok(!/#mg-lora-cards \.mg-lora-card\.is-selected \{ order: -1; \}/.test(css), "ordering only while ON");
});

test("compact card CSS: 2-line name with ellipsis, slim readable strength row, portrait contain preview", () => {
    const css = fs.readFileSync(new URL("../app/css/manga_workspace.css", import.meta.url), "utf8");
    const last = sel => { const m = [...css.matchAll(new RegExp(sel.replace(/[.*+?^${}()|[\]\\]/g, "\\$&") + "\\s*\\{([^}]*)\\}", "g"))]; return m.length ? m.at(-1)[1] : ""; };
    const name = last("#mg-lora-cards .mg-lora-card-name");
    assert.match(name, /-webkit-line-clamp: 2/);
    assert.match(name, /text-overflow: ellipsis/);
    const strength = last("#mg-lora-cards .mg-lora-card-controls .mg-lora-strength");
    assert.match(strength, /width: 52px/);
    assert.match(strength, /height: 20px/);
    const media = last("#mg-lora-cards .mg-lora-card-thumbbtn .mg-lora-card-thumb");
    assert.match(media, /aspect-ratio: 3 \/ 4/);
    assert.match(media, /object-fit: contain/);
    const src = fs.readFileSync(new URL("../app/src/view/lora_panel.js", import.meta.url), "utf8");
    assert.match(src, /name\.title = lora\.id;/, "full name/ID stays available as a tooltip");
});

test("Stage hover preview: LoRA thumbnail mirrors the displayed slot, leaves cleanly, mutates nothing", async () => {
    const t = await mount("1girl, <lora:a:1.0>");
    const stage = mountStageResourcePreview(document.createElement("div"), { doc: document });
    try {
        t.slotButtons()[1].onclick();                       // global slot 2 (_ani)
        const [a, b, c, d] = ["a", "b", "c", "d"].map(t.card);
        for (const card of [b, c]) Object.assign(t.media(card), { complete: true, naturalWidth: 512 });
        const before = { prompt: t.prompt.value, slot: t.view.previewSlot };
        const enter = el => t.thumb(el).dispatchEvent(new Event("pointerenter"));
        const leave = el => t.thumb(el).dispatchEvent(new Event("pointerleave"));

        enter(b);
        assert.equal(stage.layer.hidden, false, "hover publishes the visible preview");
        assert.equal(stage.image.src, t.media(b).src, "same URL the card displays");
        assert.equal(new URL(stage.image.src, "http://x").searchParams.get("slot"), "2", "respects the global slot; no fallback to 1");
        assert.equal(stage.label.textContent, "b");
        enter(c);
        leave(b);
        assert.equal(stage.image.src, t.media(c).src, "hover A -> B shows B; stale A never lingers");
        leave(c);
        assert.equal(stage.layer.hidden, true, "leave clears the temporary preview");

        enter(a);                                            // slot 2 missing for a -> NO PREVIEW placeholder
        assert.equal(t.media(a).tagName, "div");
        assert.equal(stage.layer.hidden, true, "missing preview does nothing");
        enter(c);
        enter(d);
        assert.equal(stage.layer.hidden, true, "moving onto a missing preview clears, never blanks the Stage");

        assert.deepEqual({ prompt: t.prompt.value, slot: t.view.previewSlot }, before, "hover adds/removes no LoRA and keeps the slot");
        enter(c);
        t.thumb(c).onclick();
        assert.equal(t.prompt.value, "1girl, <lora:a:1.0>, <lora:c:1.0>", "normal thumbnail click still adds");
        assert.equal(stage.layer.hidden, true, "re-render after click drops the preview of the removed thumbnail");
    } finally {
        resetStageResourcePreview();
    }
});

// --- minimal DOM stand-in -------------------------------------------------------------
function fakeDom() {
    const make = tag => {
        const node = { tagName: tag, children: [], className: "", textContent: "", hidden: false, dataset: {}, attrs: {},
            cls: {}, listeners: {}, value: "", onclick: null, onchange: null, disabled: false, src: "" };
        node.classList = { toggle(n, on) { node.cls[n] = on === undefined ? !node.cls[n] : Boolean(on); }, add(n) { node.cls[n] = true; }, remove(n) { node.cls[n] = false; } };
        node.append = (...kids) => { node.children.push(...kids); };
        node.appendChild = kid => { node.children.push(kid); return kid; };
        node.replaceChildren = () => { node.children = []; };
        node.replaceWith = other => { const p = node.parent; if (p) p.children[p.children.indexOf(node)] = other; };
        node.setAttribute = (k, v) => { node.attrs[k] = v; };
        node.getAttribute = k => node.attrs[k];
        node.addEventListener = (type, fn) => { (node.listeners[type] ||= []).push(fn); };
        node.dispatchEvent = event => { for (const fn of node.listeners[event.type] || []) fn(event); return true; };
        Object.defineProperty(node, "childElementCount", { get: () => node.children.length });
        const append = node.appendChild;
        node.appendChild = kid => { kid.parent = node; return append(kid); };
        return node;
    };
    globalThis.document = { createElement: make };
    globalThis.Event = class { constructor(type) { this.type = type; } };
    return { make };
}
