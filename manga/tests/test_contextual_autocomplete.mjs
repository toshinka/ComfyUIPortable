import test from "node:test";
import assert from "node:assert/strict";

import {
    detectPromptCompletionContext,
    insertPromptLora,
    insertPromptWildcard,
    insertPromptTag,
    queryLoraCatalog,
    queryWildcardCatalog,
    queryTagCatalog,
    normalizeLoraList,
    normalizeWildcardList,
    suppressedPromptContext
} from "../app/src/view/tag_autocomplete.js";

test("Context Detection: LoRA context", () => {
    // A. <lora:foo detects LORA context
    const textA = "<lora:foo";
    const ctxA = detectPromptCompletionContext(textA, textA.length);
    assert.equal(ctxA.type, "lora");
    assert.equal(ctxA.query, "foo");
    assert.equal(ctxA.weight, null);
    assert.equal(ctxA.hasClosingAngle, false);

    // B. <lora:foo:0.75> caret in name detects LORA context with preserved weight
    const textB = "<lora:foo:0.75>";
    const caretB = 8; // on 'foo'
    const ctxB = detectPromptCompletionContext(textB, caretB);
    assert.equal(ctxB.type, "lora");
    assert.equal(ctxB.query, "foo");
    assert.equal(ctxB.weight, "0.75");
    assert.equal(ctxB.hasClosingAngle, true);

    // Caret in weight portion suppresses autocomplete
    const caretBWeight = 12; // on '0.75'
    const ctxBWeight = detectPromptCompletionContext(textB, caretBWeight);
    assert.equal(ctxBWeight.type, "suppressed");
    assert.equal(ctxBWeight.reason, "lora-weight");

    // C. Ordinary "foo" does NOT return LoRA context
    const textC = "foo";
    const ctxC = detectPromptCompletionContext(textC, textC.length);
    assert.equal(ctxC.type, "tag");
    assert.equal(ctxC.query, "foo");

    // D. Malformed angle syntax remains safely handled
    const textD1 = "<embedding:foo>";
    const ctxD1 = detectPromptCompletionContext(textD1, 10);
    assert.equal(ctxD1.type, "suppressed");
    assert.equal(ctxD1.reason, "angle-token");

    const textD2 = "<unclosed";
    const ctxD2 = detectPromptCompletionContext(textD2, 5);
    assert.equal(ctxD2.type, "suppressed");
    assert.equal(ctxD2.reason, "angle-token");
});

test("Context Detection: Wildcard context", () => {
    // A. __foo detects WILDCARD context
    const textA = "__foo";
    const ctxA = detectPromptCompletionContext(textA, textA.length);
    assert.equal(ctxA.type, "wildcard");
    assert.equal(ctxA.query, "foo");
    assert.equal(ctxA.hasClosingDelimiter, false);

    // B. __foo__ detects WILDCARD context with hasClosingDelimiter true
    const textB = "__foo__";
    const ctxB = detectPromptCompletionContext(textB, 4); // on 'foo'
    assert.equal(ctxB.type, "wildcard");
    assert.equal(ctxB.query, "foo");
    assert.equal(ctxB.hasClosingDelimiter, true);

    // C. Nested wildcard path
    const textC = "__clothing/dress";
    const ctxC = detectPromptCompletionContext(textC, textC.length);
    assert.equal(ctxC.type, "wildcard");
    assert.equal(ctxC.query, "clothing/dress");

    // D. Ordinary text does not return wildcard context
    const textD = "1girl, smiling";
    const ctxD = detectPromptCompletionContext(textD, textD.length);
    assert.equal(ctxD.type, "tag");
    assert.equal(ctxD.query, "smiling");

    // Multiple wildcards: __pose__, __hair
    const textE = "__pose__, __hair";
    const ctxE = detectPromptCompletionContext(textE, textE.length);
    assert.equal(ctxE.type, "wildcard");
    assert.equal(ctxE.query, "hair");

    // After closed wildcard: __pose__, 1girl
    const textF = "__pose__, 1girl";
    const ctxF = detectPromptCompletionContext(textF, textF.length);
    assert.equal(ctxF.type, "tag");
    assert.equal(ctxF.query, "1girl");
});

test("Context Detection: Dynamic Choice suppression", () => {
    const textA = "{red|blue}";
    const ctxA = detectPromptCompletionContext(textA, 3);
    assert.equal(ctxA.type, "suppressed");
    assert.equal(ctxA.reason, "dynamic-choice");

    const textB = "1girl, {red|blue, smiling";
    const ctxB = detectPromptCompletionContext(textB, 15);
    assert.equal(ctxB.type, "suppressed");
    assert.equal(ctxB.reason, "dynamic-choice");
});

test("LoRA Replacement and Syntax Preservation", () => {
    // Unsupplied weight -> default :1
    const text1 = "<lora:foo";
    const ctx1 = detectPromptCompletionContext(text1, text1.length);
    const res1 = insertPromptLora(text1, ctx1, "foo_bar");
    assert.equal(res1.value, "<lora:foo_bar:1>");
    assert.equal(res1.caret, "<lora:foo_bar:1>".length);

    // Existing weight preserved
    const text2 = "<lora:foo:0.75>";
    const ctx2 = detectPromptCompletionContext(text2, 8);
    const res2 = insertPromptLora(text2, ctx2, "foo_bar");
    assert.equal(res2.value, "<lora:foo_bar:0.75>");

    // Embedded in surrounding prompt text without weight
    const text3 = "1girl, <lora:foo, master";
    const ctx3 = detectPromptCompletionContext(text3, 16);
    const res3 = insertPromptLora(text3, ctx3, "styles/A");
    assert.equal(res3.value, "1girl, <lora:styles/A:1>, master");

    // Embedded in surrounding prompt text with weight
    const text4 = "1girl, <lora:foo:0.5>, master";
    const ctx4 = detectPromptCompletionContext(text4, 15);
    const res4 = insertPromptLora(text4, ctx4, "styles/A");
    assert.equal(res4.value, "1girl, <lora:styles/A:0.5>, master");
});

test("Wildcard Replacement and Syntax Preservation", () => {
    // Unclosed __foo -> __pose_sitting__
    const text1 = "__foo";
    const ctx1 = detectPromptCompletionContext(text1, text1.length);
    const res1 = insertPromptWildcard(text1, ctx1, "pose_sitting");
    assert.equal(res1.value, "__pose_sitting__");
    assert.equal(res1.caret, "__pose_sitting__".length);

    // Already closed __foo__ -> __pose_sitting__ (no delimiter duplication)
    const text2 = "__foo__";
    const ctx2 = detectPromptCompletionContext(text2, 4);
    const res2 = insertPromptWildcard(text2, ctx2, "pose_sitting");
    assert.equal(res2.value, "__pose_sitting__");

    // Embedded in surrounding prompt text without closing delimiter
    const text3 = "1girl, __foo, smile";
    const ctx3 = detectPromptCompletionContext(text3, 12);
    const res3 = insertPromptWildcard(text3, ctx3, "pose_sitting");
    assert.equal(res3.value, "1girl, __pose_sitting__, smile");

    // Embedded in surrounding prompt text with closing delimiter
    const text4 = "1girl, __foo__, smile";
    const ctx4 = detectPromptCompletionContext(text4, 11);
    const res4 = insertPromptWildcard(text4, ctx4, "pose_sitting");
    assert.equal(res4.value, "1girl, __pose_sitting__, smile");

    // Nested wildcard path
    const text5 = "__clothing/";
    const ctx5 = detectPromptCompletionContext(text5, text5.length);
    const res5 = insertPromptWildcard(text5, ctx5, "clothing/dress");
    assert.equal(res5.value, "__clothing/dress__");
});

test("Provider Query Separation", () => {
    const loras = ["foo_bar", "foo_character", "styles/A"];
    const wildcards = ["play4_smoke", "clothing/dress", "pose_sitting"];
    const tags = [
        { tag: "1girl", category: "general", ranking: 900 },
        { tag: "food", category: "general", ranking: 800 }
    ];

    // LoRA query returns only LoRAs
    const loraResults = queryLoraCatalog(loras, "foo");
    assert.equal(loraResults.length, 2);
    assert.equal(loraResults[0].tag, "foo_bar");
    assert.equal(loraResults[0].category, "lora");
    assert.equal(loraResults[0].type, "lora");

    // Wildcard query returns only Wildcards
    const wildcardResults = queryWildcardCatalog(wildcards, "pose");
    assert.equal(wildcardResults.length, 1);
    assert.equal(wildcardResults[0].tag, "pose_sitting");
    assert.equal(wildcardResults[0].category, "wildcard");
    assert.equal(wildcardResults[0].type, "wildcard");

    // Tag query returns only Tags
    const tagResults = queryTagCatalog(tags, "foo");
    assert.equal(tagResults.length, 1);
    assert.equal(tagResults[0].tag, "food");
    assert.equal(tagResults[0].category, "general");
});

test("Normalization helpers", () => {
    // LoRA normalization
    const rawLoras = [
        { id: "A", available: true },
        { id: "B", available: false },
        "C",
        "  A  ", // duplicate
        "",
        null
    ];
    const normalizedLoras = normalizeLoraList(rawLoras);
    assert.deepEqual(normalizedLoras, ["A", "C"]);

    // Wildcard normalization
    const rawWildcards = [
        "clothing\\dress",
        "play4_smoke",
        "  clothing/dress  ", // duplicate
        "",
        null
    ];
    const normalizedWildcards = normalizeWildcardList(rawWildcards);
    assert.deepEqual(normalizedWildcards, ["clothing/dress", "play4_smoke"]);
});
