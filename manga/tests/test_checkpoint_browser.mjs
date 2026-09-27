import assert from "node:assert/strict";
import test from "node:test";

import {
    CHECKPOINT_PREVIEW_SLOTS,
    checkpointPreviewUrl,
    filterCheckpointEntries,
    mountCheckpointBrowser
} from "../app/src/view/generation_view.js";

class FakeEvent {
    constructor(type, init = {}) {
        this.type = type;
        Object.assign(this, init);
    }
}

class FakeElement {
    constructor(tagName, ownerDocument) {
        this.tagName = tagName.toLowerCase();
        this.ownerDocument = ownerDocument;
        this.children = [];
        this.parentNode = null;
        this.listeners = new Map();
        this.attributes = new Map();
        this.style = {};
        this.className = "";
        this.textContent = "";
        this.value = "";
        this.hidden = false;
        this.disabled = false;
    }

    get firstChild() { return this.children[0] || null; }
    get options() { return this.tagName === "select" ? this.children : undefined; }
    get nextElementSibling() {
        if (!this.parentNode) return null;
        const index = this.parentNode.children.indexOf(this);
        return this.parentNode.children[index + 1] || null;
    }
    get classList() {
        return { contains: name => this.className.split(/\s+/).includes(name) };
    }

    append(...items) {
        for (const item of items) {
            item.parentNode?.removeChild(item);
            item.parentNode = this;
            this.children.push(item);
        }
    }

    replaceChildren(...items) {
        for (const child of this.children) child.parentNode = null;
        this.children = [];
        this.append(...items);
    }

    replaceWith(replacement) {
        if (!this.parentNode) return;
        const parent = this.parentNode;
        const index = parent.children.indexOf(this);
        if (index < 0) return;
        this.parentNode = null;
        replacement.parentNode = parent;
        parent.children[index] = replacement;
    }

    removeChild(child) {
        const index = this.children.indexOf(child);
        if (index >= 0) this.children.splice(index, 1);
        child.parentNode = null;
        return child;
    }

    insertBefore(child, reference) {
        child.parentNode?.removeChild(child);
        const index = reference ? this.children.indexOf(reference) : -1;
        child.parentNode = this;
        if (index < 0) this.children.push(child);
        else this.children.splice(index, 0, child);
        return child;
    }

    insertAdjacentElement(position, element) {
        assert.equal(position, "afterend");
        const parent = this.parentNode;
        const index = parent.children.indexOf(this);
        element.parentNode = parent;
        parent.children.splice(index + 1, 0, element);
        return element;
    }

    setAttribute(name, value) { this.attributes.set(name, String(value)); }
    getAttribute(name) { return this.attributes.get(name) ?? null; }

    addEventListener(type, callback, options = {}) {
        const list = this.listeners.get(type) || [];
        list.push({ callback, once: Boolean(options.once) });
        this.listeners.set(type, list);
    }

    dispatchEvent(event) {
        event.target = this;
        const list = this.listeners.get(event.type) || [];
        for (const item of [...list]) {
            item.callback(event);
            if (item.once) list.splice(list.indexOf(item), 1);
        }
        return true;
    }
}

class FakeDocument {
    constructor() { this.defaultView = { Event: FakeEvent }; }
    createElement(tagName) { return new FakeElement(tagName, this); }
}

function makeFixture() {
    const doc = new FakeDocument();
    const parent = doc.createElement("div");
    const select = doc.createElement("select");
    const hint = doc.createElement("p");
    hint.className = "mg-hint";
    parent.append(select, hint);
    const entries = [
        { id: "models/nested/Example.safetensors", available: true },
        { id: "models/Other.safetensors", available: true },
        { id: "models/Missing.safetensors", available: false }
    ];
    for (const entry of entries) {
        const option = doc.createElement("option");
        option.value = entry.id;
        select.append(option);
    }
    const state = { selected: entries[0].id };
    select.value = state.selected;
    select.addEventListener("change", () => { state.selected = select.value; });
    const browser = mountCheckpointBrowser({
        select,
        getEntries: () => entries,
        getSelected: () => state.selected,
        doc
    });
    browser.render();
    return { doc, parent, select, hint, entries, state, browser };
}

test("checkpoint previews preserve canonical nested IDs across four slots", () => {
    assert.deepEqual(CHECKPOINT_PREVIEW_SLOTS.map(item => item.slot), [1, 2, 3, 4]);
    assert.equal(
        checkpointPreviewUrl("models/nested/Example one.safetensors", 4),
        "/api/manga/resources/checkpoint/preview?id=models%2Fnested%2FExample%20one.safetensors&slot=4"
    );
    assert.deepEqual(
        filterCheckpointEntries([{ id: "models/nested/Example.safetensors" }, { id: "Other.safetensors" }], "NESTED\\example"),
        [{ id: "models/nested/Example.safetensors" }]
    );
});

test("checkpoint cards, search, native selection and clear share the existing selector", () => {
    const { select, state, browser, hint } = makeFixture();
    assert.match(hint.textContent, /live catalog/i);
    assert.equal(browser.cards.children.length, 3);
    const selectedCard = browser.cards.children[0];
    assert.equal(selectedCard.title, "models/nested/Example.safetensors");
    assert.equal(selectedCard.getAttribute("aria-pressed"), "true");
    assert.equal(selectedCard.classList.contains("mg-lora-card"), true);
    assert.equal(selectedCard.children.length, 2, "each card contains one preview and one title");
    assert.equal(selectedCard.children[0].tagName, "img");
    assert.equal(selectedCard.children[0].classList.contains("mg-lora-card-thumb"), true);
    assert.match(selectedCard.children[0].src, /slot=1$/);
    assert.equal(selectedCard.children[1].classList.contains("mg-lora-card-name"), true);

    browser.search.value = "other";
    browser.search.dispatchEvent(new FakeEvent("input"));
    assert.equal(browser.cards.children.length, 1);
    assert.equal(state.selected, "models/nested/Example.safetensors");

    browser.search.value = "";
    browser.search.dispatchEvent(new FakeEvent("input"));
    const otherCard = browser.cards.children.find(card => card.title === "models/Other.safetensors");
    otherCard.dispatchEvent(new FakeEvent("click"));
    assert.equal(select.value, "models/Other.safetensors");
    assert.equal(state.selected, "models/Other.safetensors");

    select.value = "models/nested/Example.safetensors";
    select.dispatchEvent(new FakeEvent("change"));
    assert.equal(browser.cards.children.find(card => card.title === select.value).getAttribute("aria-pressed"), "true");

    browser.clearButton.dispatchEvent(new FakeEvent("click"));
    assert.equal(select.value, "");
    assert.equal(state.selected, "");
    assert.equal(browser.clearButton.disabled, true);
});

test("four neutral preview slots switch the single card thumbnail without changing selection", () => {
    assert.deepEqual(CHECKPOINT_PREVIEW_SLOTS.map(item => item.label), ["Preview 1", "Preview 2", "Preview 3", "Preview 4"]);
    const { browser, state } = makeFixture();
    assert.equal(browser.previewButtons.length, 4);
    assert.deepEqual(browser.previewButtons.map(button => button.textContent), ["1", "2", "3", "4"]);
    assert.equal(browser.previewButtons[0].getAttribute("aria-pressed"), "true");
    assert.equal(browser.previewButtons[3].getAttribute("aria-pressed"), "false");
    assert.equal(state.selected, "models/nested/Example.safetensors");

    const firstCard = browser.cards.children[0];
    browser.render();
    assert.equal(browser.cards.children[0], firstCard, "unchanged catalog/selection/search keeps the same cards");

    browser.previewButtons[3].dispatchEvent(new FakeEvent("click"));
    assert.equal(browser.previewButtons[3].getAttribute("aria-pressed"), "true");
    assert.equal(browser.previewButtons[0].getAttribute("aria-pressed"), "false");
    assert.notEqual(browser.cards.children[0], firstCard, "changing the preview slot rebuilds thumbnails");
    assert.match(browser.cards.children[0].children[0].src, /slot=4$/);
    assert.equal(state.selected, "models/nested/Example.safetensors");

    browser.previewButtons[1].dispatchEvent(new FakeEvent("click"));
    const missing = browser.cards.children[0].children[0];
    const url = missing.src;
    missing.dispatchEvent(new FakeEvent("error"));
    assert.equal(browser.cards.children[0].children[0].classList.contains("mg-lora-card-noimg"), true,
        "a missing sidecar uses the same blank thumbnail treatment as LoRA");
    browser.search.value = "example";
    browser.search.dispatchEvent(new FakeEvent("input"));
    const again = browser.cards.children[0].children[0];
    assert.equal(again.tagName, "div");
    assert.equal(again.src ?? "", "", `failed preview ${url} is not requested again`);
    assert.equal(again.textContent, "NO PREVIEW 2");

    const unavailable = makeFixture().browser.cards.children.find(card => card.title === "models/Missing.safetensors");
    assert.equal(unavailable.disabled, true);
    assert.equal(unavailable.children[0].classList.contains("mg-lora-card-noimg"), true);
    assert.equal(unavailable.children[0].src ?? "", "", "unavailable checkpoints request nothing");
});
