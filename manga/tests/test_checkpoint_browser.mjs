import assert from "node:assert/strict";
import test from "node:test";

import {
    CHECKPOINT_PREVIEW_SLOTS,
    checkpointPreviewUrl,
    filterCheckpointEntries,
    mountCheckpointBrowser
} from "../app/src/view/generation_view.js";
import { mountStageResourcePreview, resetStageResourcePreview } from "../app/src/view/stage_resource_preview.js";

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
        this.dataset = {};
        this.style = {};
        this.className = "";
        this.textContent = "";
        this.value = "";
        this.hidden = false;
        this.disabled = false;
    }

    get firstChild() { return this.children[0] || null; }
    get childElementCount() { return this.children.length; }
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
        { id: "models\\nested\\Example.safetensors", available: true },
        { id: "models/nested/Second.safetensors", available: true },
        { id: "models/Other.safetensors", available: true },
        { id: "models\\nested\\Missing.safetensors", available: false },
        { id: "Root.safetensors", available: true }
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

function openFolder(browser, folderId) {
    const button = browser.folders.children.find(item => item.dataset.folder === folderId);
    assert.ok(button, `folder ${folderId} is visible`);
    button.dispatchEvent(new FakeEvent("click"));
}

function openCrumb(browser, folderId) {
    const button = browser.breadcrumb.children.find(item => item.dataset.folder === folderId);
    assert.ok(button, `breadcrumb ${folderId || "root"} is visible`);
    button.dispatchEvent(new FakeEvent("click"));
}

function cardFor(browser, checkpointId) {
    return browser.cards.children.find(card => card.dataset.checkpointId === checkpointId);
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

test("checkpoint folders navigate without changing canonical selection; search stays global", () => {
    const { select, state, browser, hint } = makeFixture();
    assert.match(hint.textContent, /live catalog/i);
    assert.equal(browser.cards.children.length, 1, "root renders its immediate resource only");
    assert.equal(cardFor(browser, "Root.safetensors")?.dataset.checkpointId, "Root.safetensors");
    assert.equal(cardFor(browser, "models\\nested\\Example.safetensors"), undefined,
        "nested descendants are not flattened into the root");
    assert.equal(browser.folders.hidden, false);
    assert.deepEqual(browser.folders.children.map(button => button.dataset.folder), ["models"]);

    openFolder(browser, "models");
    assert.deepEqual(browser.cards.children.map(card => card.dataset.checkpointId), ["models/Other.safetensors"]);
    assert.deepEqual(browser.folders.children.map(button => button.dataset.folder), ["models/nested"]);
    assert.equal(state.selected, "models\\nested\\Example.safetensors", "navigation preserves the exact selected ID");

    openFolder(browser, "models/nested");
    assert.deepEqual(browser.cards.children.map(card => card.dataset.checkpointId).sort(), [
        "models\\nested\\Example.safetensors",
        "models\\nested\\Missing.safetensors",
        "models/nested/Second.safetensors"
    ].sort(), "slash and backslash catalog paths share the same folder view");
    const selectedCard = cardFor(browser, "models\\nested\\Example.safetensors");
    assert.equal(selectedCard.getAttribute("aria-pressed"), "true");
    assert.equal(selectedCard.classList.contains("mg-lora-card"), true);
    assert.equal(selectedCard.children.length, 2, "each ordinary card contains one preview and one title");
    assert.equal(selectedCard.children[0].tagName, "img");
    assert.equal(selectedCard.children[0].classList.contains("mg-lora-card-thumb"), true);
    assert.match(selectedCard.children[0].src, /slot=1$/);
    assert.equal(selectedCard.children[1].classList.contains("mg-lora-card-name"), true);

    browser.search.value = "Other";
    browser.search.dispatchEvent(new FakeEvent("input"));
    assert.equal(browser.cards.children.length, 1);
    assert.equal(cardFor(browser, "models/Other.safetensors")?.dataset.checkpointId, "models/Other.safetensors",
        "search finds a resource outside the current folder");
    assert.equal(browser.cards.children[0].children.at(-1).className, "mg-lora-card-folder");
    assert.equal(browser.cards.children[0].children.at(-1).textContent, "models");
    assert.equal(browser.breadcrumb.hidden, true);
    assert.equal(browser.folders.hidden, true);
    assert.equal(state.selected, "models\\nested\\Example.safetensors", "search does not mutate selection");

    browser.search.value = "";
    browser.search.dispatchEvent(new FakeEvent("input"));
    assert.deepEqual(browser.cards.children.map(card => card.dataset.checkpointId).sort(), [
        "models\\nested\\Example.safetensors",
        "models\\nested\\Missing.safetensors",
        "models/nested/Second.safetensors"
    ].sort(), "clearing search restores the current folder");

    select.value = "models/Other.safetensors";
    select.dispatchEvent(new FakeEvent("change"));
    assert.equal(cardFor(browser, "models/Other.safetensors"), undefined,
        "external selector changes do not navigate folders");
    assert.equal(browser.breadcrumb.children.at(-1).dataset.folder, "models/nested");

    openCrumb(browser, "models");
    const otherCard = cardFor(browser, "models/Other.safetensors");
    assert.equal(otherCard.getAttribute("aria-pressed"), "true", "visible folder reflects external selection");
    otherCard.dispatchEvent(new FakeEvent("click"));
    assert.equal(select.value, "models/Other.safetensors");
    assert.equal(state.selected, "models/Other.safetensors");

    openCrumb(browser, "");
    cardFor(browser, "Root.safetensors").dispatchEvent(new FakeEvent("click"));
    assert.equal(select.value, "Root.safetensors");
    assert.equal(state.selected, "Root.safetensors");

    openFolder(browser, "models");
    openFolder(browser, "models/nested");
    cardFor(browser, "models/nested/Second.safetensors").dispatchEvent(new FakeEvent("click"));
    assert.equal(select.value, "models/nested/Second.safetensors", "selection writes the exact canonical slash ID");
    assert.equal(state.selected, "models/nested/Second.safetensors");

    select.value = "models\\nested\\Example.safetensors";
    select.dispatchEvent(new FakeEvent("change"));
    assert.equal(cardFor(browser, select.value).getAttribute("aria-pressed"), "true");

    browser.clearButton.dispatchEvent(new FakeEvent("click"));
    assert.equal(select.value, "");
    assert.equal(state.selected, "");
    assert.equal(browser.clearButton.disabled, true);
});

test("checkpoint browser starts collapsed and disclosure toggles preserve its state", () => {
    const { browser, state } = makeFixture();
    assert.equal(browser.details.open, false);

    browser.search.value = "Second";
    browser.search.dispatchEvent(new FakeEvent("input"));
    browser.previewButtons[2].dispatchEvent(new FakeEvent("click"));
    assert.equal(browser.cards.children.length, 1);
    assert.equal(state.selected, "models\\nested\\Example.safetensors");

    browser.details.open = true;
    assert.equal(browser.details.open, true);
    browser.details.open = false;
    assert.equal(browser.details.open, false);

    assert.equal(browser.search.value, "Second");
    assert.equal(browser.previewButtons[2].getAttribute("aria-pressed"), "true");
    assert.equal(state.selected, "models\\nested\\Example.safetensors");
    assert.equal(browser.cards.children.length, 1);
    assert.match(cardFor(browser, "models/nested/Second.safetensors").children[0].src, /slot=3$/);
});

test("four neutral preview slots switch the single card thumbnail without changing selection", () => {
    assert.deepEqual(CHECKPOINT_PREVIEW_SLOTS.map(item => item.label), ["Preview 1", "Preview 2", "Preview 3", "Preview 4"]);
    const { browser, state } = makeFixture();
    assert.equal(browser.previewButtons.length, 4);
    assert.deepEqual(browser.previewButtons.map(button => button.textContent), ["1", "2", "3", "4"]);
    assert.equal(browser.previewButtons[0].getAttribute("aria-pressed"), "true");
    assert.equal(browser.previewButtons[3].getAttribute("aria-pressed"), "false");
    assert.equal(state.selected, "models\\nested\\Example.safetensors");

    openFolder(browser, "models");
    openFolder(browser, "models/nested");

    const firstCard = cardFor(browser, "models\\nested\\Example.safetensors");
    browser.render();
    assert.equal(cardFor(browser, "models\\nested\\Example.safetensors"), firstCard,
        "unchanged catalog/selection/search/folder keeps the same cards");

    browser.previewButtons[3].dispatchEvent(new FakeEvent("click"));
    assert.equal(browser.previewButtons[3].getAttribute("aria-pressed"), "true");
    assert.equal(browser.previewButtons[0].getAttribute("aria-pressed"), "false");
    assert.notEqual(cardFor(browser, "models\\nested\\Example.safetensors"), firstCard,
        "changing the preview slot rebuilds thumbnails");
    assert.match(cardFor(browser, "models\\nested\\Example.safetensors").children[0].src, /slot=4$/);
    assert.equal(state.selected, "models\\nested\\Example.safetensors");

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

    const unavailableFixture = makeFixture();
    openFolder(unavailableFixture.browser, "models");
    openFolder(unavailableFixture.browser, "models/nested");
    const unavailable = cardFor(unavailableFixture.browser, "models\\nested\\Missing.safetensors");
    assert.equal(unavailable.disabled, true);
    assert.equal(unavailable.children[0].classList.contains("mg-lora-card-noimg"), true);
    assert.equal(unavailable.children[0].src ?? "", "", "unavailable checkpoints request nothing");
});

test("Stage hover preview mirrors the displayed checkpoint thumbnail and never changes state", () => {
    const { doc, browser, state, select } = makeFixture();
    const host = doc.createElement("div");
    const stage = mountStageResourcePreview(host, { doc });
    try {
        assert.equal(browser.details.open, false, "Browse checkpoints stays default-collapsed");
        browser.details.open = true;
        openFolder(browser, "models");
        openFolder(browser, "models/nested");
        browser.previewButtons[2].dispatchEvent(new FakeEvent("click"));
        const cardA = cardFor(browser, "models\\nested\\Example.safetensors");
        const cardB = cardFor(browser, "models/nested/Second.safetensors");
        const [imgA, imgB] = [cardA.children[0], cardB.children[0]];
        for (const img of [imgA, imgB]) Object.assign(img, { complete: true, naturalWidth: 832 });
        const before = { selected: state.selected, value: select.value, search: browser.search.value,
            slot: browser.previewButtons.map(button => button.getAttribute("aria-pressed")), open: browser.details.open };

        imgA.dispatchEvent(new FakeEvent("pointerenter"));
        assert.equal(stage.layer.hidden, false, "hover publishes the preview");
        assert.equal(stage.image.src, imgA.src, "same URL as the visible card thumbnail");
        assert.match(stage.image.src, /slot=3$/, "respects the current Preview slot; no fallback to 1");
        imgB.dispatchEvent(new FakeEvent("pointerenter"));
        imgA.dispatchEvent(new FakeEvent("pointerleave"));
        assert.equal(stage.image.src, imgB.src, "hover A -> B shows B; a late leave of A does not clear B");
        imgB.dispatchEvent(new FakeEvent("pointerleave"));
        assert.equal(stage.layer.hidden, true, "leave clears the temporary preview");

        imgA.dispatchEvent(new FakeEvent("pointerenter"));
        browser.details.open = false;
        browser.details.dispatchEvent(new FakeEvent("toggle"));
        assert.equal(stage.layer.hidden, true, "closing Browse checkpoints clears a lingering preview");
        browser.details.open = true;

        const loading = doc.createElement("img");
        Object.assign(loading, { src: imgA.src, complete: false, naturalWidth: 0 });
        assert.equal(stage.show(loading, "x"), false, "a not-yet-displayed image does nothing");
        Object.assign(imgA, { naturalWidth: 0 });           // a failed image has no pixels (as in a browser)
        imgA.dispatchEvent(new FakeEvent("error"));
        const placeholder = cardFor(browser, "models\\nested\\Example.safetensors").children[0];
        imgA.dispatchEvent(new FakeEvent("pointerenter"));
        placeholder.dispatchEvent(new FakeEvent("pointerenter"));
        assert.equal(stage.layer.hidden, true, "missing / failed preview does not blank or replace the Stage");

        assert.deepEqual({ selected: state.selected, value: select.value, search: browser.search.value,
            slot: browser.previewButtons.map(button => button.getAttribute("aria-pressed")), open: browser.details.open }, before,
            "hover changed no checkpoint selection, search, slot or disclosure");

        cardB.dispatchEvent(new FakeEvent("click"));
        assert.equal(select.value, "models/nested/Second.safetensors", "normal card click still selects");
    } finally {
        resetStageResourcePreview();
    }
});

test("checkpoint cards carry no native hover tooltip; identity stays in aria-label and dataset", () => {
    const { browser } = makeFixture();
    openFolder(browser, "models");
    openFolder(browser, "models/nested");
    for (const card of browser.cards.children) {
        assert.equal(card.title || "", "", "no Create-side tooltip on the hovered card");
        assert.equal(card.children[0].title || "", "", "no tooltip on the thumbnail");
        assert.match(card.getAttribute("aria-label"), /checkpoint models[\\/]/);
        assert.match(card.dataset.checkpointId, /^models[\\/]/);
    }
});
