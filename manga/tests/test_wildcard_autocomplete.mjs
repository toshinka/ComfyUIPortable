// MANGA-WILDCARD-AUTOCOMPLETE-PRODUCTION1: live-runtime root cause (line-delimited tokens) and
// single "_" Wildcard discovery on the one shared autocomplete surface.
import test from "node:test";
import assert from "node:assert/strict";
import {
    detectPromptCompletionContext, findActivePromptToken, insertPromptTag, insertPromptWildcard, queryWildcardCatalog,
} from "../app/src/view/tag_autocomplete.js";

const ctx = (text, caret = text.length) => detectPromptCompletionContext(text, caret);
const WILDCARDS = ["body1", "character/hair", "hair_style", "girl1"];

test("root cause: a new prompt line is its own token (live repro 'blue ey\\nsmi')", () => {
    assert.equal(findActivePromptToken("a, long_hair, blue ey\nsmi", 25).query, "smi");
    assert.equal(ctx("masterpiece\nsmi").query, "smi");
    assert.equal(ctx("x,\r\nsmi").query, "smi");
    const r = insertPromptTag("x, blue_eyes\nsmi", 16, "smile");
    assert.equal(r.value, "x, blue_eyes\nsmile, ");
    assert.equal(ctx("a, blue_ey").query, "blue_ey", "comma tokens unchanged");
});

test("A/B: single '_' at a token boundary offers Wildcards", () => {
    for (const text of ["_", "_ha", "1girl, _ha", "1girl _ha", "1girl,\n_ha", "1girl,_ha"]) {
        const c = ctx(text);
        assert.equal(c.type, "wildcard", text);
        assert.equal(c.discovery, true, text);
    }
    assert.deepEqual(queryWildcardCatalog(WILDCARDS, ctx("_").query).map(e => e.tag).length, 4);
    assert.deepEqual(queryWildcardCatalog(WILDCARDS, ctx("a, _hai").query).map(e => e.tag), ["hair_style", "character/hair"]);
});

test("C: '__' still selects Wildcard mode (not discovery)", () => {
    const c = ctx("1girl, __ha");
    assert.equal(c.type, "wildcard");
    assert.equal(c.discovery, undefined);
    assert.equal(c.query, "ha");
});

test("D: 'long_' and inner underscores remain tag completion", () => {
    for (const text of ["long_", "a, long_", "a, long_h", "x_y", "a, ^_^"]) assert.equal(ctx(text).type, "tag", text);
});

test("E/F: selecting from '_' inserts full canonical __name__ (nested kept), unrelated text preserved", () => {
    const text = "1girl, _hai, smile";
    const c = ctx(text, 11);
    assert.equal(insertPromptWildcard(text, c, "hair_style").value, "1girl, __hair_style__, smile");
    const nested = "_cha\nsmile";
    assert.equal(insertPromptWildcard(nested, ctx(nested, 4), "character/hair").value, "__character/hair__\nsmile");
    assert.equal(insertPromptWildcard("_", ctx("_"), "body1").value, "__body1__");
});

// MANGA-PROMPT-VALIDATION-COHERENCE1: ordinary tag completion next to prompt syntax.
// The whole comma segment used to be the query, so "(smi", "<lora:x:1> smi" or "__w__ smi"
// matched nothing — ordinary autocomplete looked dead while Wildcard mode worked.
test("tag token starts after prompt syntax in the same comma segment; insertion keeps that syntax", async () => {
    const { detectPromptCompletionContext: detect, insertPromptTag, queryTagCatalog } = await import("../app/src/view/tag_autocomplete.js");
    const CATALOG = [{ tag: "smile", category: "general", ranking: 80 }, { tag: "long_hair", category: "general", ranking: 90 },
        { tag: "blue_eyes", category: "general", ranking: 70 }];
    const cases = [
        ["smi", "smi", "smile, "],
        ["long h", "long h", "long_hair, "],
        ["1girl, blue e", "blue e", "1girl, blue_eyes, "],
        ["blue eyes\nsmi", "smi", "blue eyes\nsmile, "],
        ["(smi", "smi", "(smile"],
        ["1girl, [smi", "smi", "1girl, [smile"],
        ["<lora:foo:0.5> smi", "smi", "<lora:foo:0.5> smile, "],
        ["__girl1__ smi", "smi", "__girl1__ smile, "],
        ["(masterpiece:1.2) smi", "smi", "(masterpiece:1.2) smile, "],
    ];
    for (const [text, query, inserted] of cases) {
        const ctx = detect(text, text.length);
        assert.equal(ctx.type, "tag", text);
        assert.equal(ctx.query, query, text);
        assert.ok(queryTagCatalog(CATALOG, ctx.query).length > 0, `${text} has suggestions`);
        assert.equal(insertPromptTag(text, text.length, queryTagCatalog(CATALOG, ctx.query)[0].tag).value, inserted);
    }
    // caret inside a weighted group: the weight after ":" is never replaced
    assert.equal(insertPromptTag("(smi:1.2), x", 4, "smile").value, "(smile:1.2), x");
    // mode rules unchanged
    assert.equal(detect("1girl, <lora:fo", 15).type, "lora");
    assert.equal(detect("1girl, _gi", 10).type, "wildcard");
    assert.equal(detect("1girl, __gi", 11).type, "wildcard");
    assert.equal(detect("long_", 5).type, "tag");
    assert.equal(detect("{red|blu", 8).type, "suppressed");
});

// Live-runtime regression (browser pass 1): accept() read this.activeContext after emitting
// "input", but the controller's own input handler clears it -> TypeError on every accept and
// the Wildcard preview event was never sent.
test("accept() survives its own input handler clearing activeContext and still reports the Wildcard occurrence", async () => {
    const { TagAutocompleteController, detectPromptCompletionContext: detect } = await import("../app/src/view/tag_autocomplete.js");
    globalThis.CustomEvent ??= class extends Event { constructor(type, init) { super(type, init); this.detail = init?.detail; } };
    for (const [text, entry, expectValue, expectEvent] of [
        ["1girl, _gir", { tag: "girl1" }, "1girl, __girl1__", { name: "girl1", start: 7 }],
        ["smi", { tag: "smile" }, "smile, ", null],
    ]) {
        const events = [];
        const self = {
            suggestions: [entry], selectedIndex: 0, contextValue: text, activeContext: detect(text, text.length),
            closed: false, close() { this.closed = true; }, refresh() {},
            textarea: {
                value: text, selectionStart: text.length, focus() {}, setSelectionRange() {},
                dispatchEvent(event) { events.push(event); if (event.type === "input") self.activeContext = null; },
            },
        };
        assert.equal(TagAutocompleteController.prototype.accept.call(self, 0), true, text);
        assert.equal(self.textarea.value, expectValue);
        assert.equal(self.closed, true, "close() reached (no TypeError)");
        const inserted = events.find(e => e.type === "tegaki:wildcard-inserted");
        assert.deepEqual(inserted ? inserted.detail : null, expectEvent);
    }
});
