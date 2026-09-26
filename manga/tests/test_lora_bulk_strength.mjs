// MANGA-LORA-UX-PRODUCTION1: bulk strength edits only valid LoRA directives in the given prompt.
import test from "node:test";
import assert from "node:assert/strict";
import {
    applyBulkLoraStrength, countBulkEditableLoras, findLoraTokens, formatLoraStrength, updateLoraTokenStrength,
} from "../app/src/view/lora_panel.js";

const PROMPT = "masterpiece, <lora:foo:1.0>, 1girl, {red|blue} hair,\n<lora:bar:0.7>, __pose__, <lora:characters/A/baz:0.4>";

test("A-F: three valid LoRAs get 0.2; names, order and other text are byte-identical", () => {
    const { value, count } = applyBulkLoraStrength(PROMPT, 0.2);
    assert.equal(count, 3);
    assert.equal(value, "masterpiece, <lora:foo:0.2>, 1girl, {red|blue} hair,\n<lora:bar:0.2>, __pose__, <lora:characters/A/baz:0.2>");
    const before = findLoraTokens(PROMPT);
    const after = findLoraTokens(value);
    assert.deepEqual(after.map(t => t.id), before.map(t => t.id), "portable aliases stay portable, canonical IDs stay canonical");
    assert.deepEqual(after.map(t => t.strengthText), ["0.2", "0.2", "0.2"]);
    const strip = s => s.replace(/<lora:([^:<>]+):[^>]+>/g, "<lora:$1:*>");
    assert.equal(strip(value), strip(PROMPT), "only strength text changed");
});

test("formatter is the existing canonical strength formatter", () => {
    for (const v of [0.2, 1, 0.15, -1.25, 0]) {
        assert.equal(findLoraTokens(applyBulkLoraStrength("<lora:foo:0.5>", v).value)[0].strengthText, formatLoraStrength(v));
    }
    assert.equal(applyBulkLoraStrength("<lora:foo:0.5>", 0.35).value, updateLoraTokenStrength("<lora:foo:0.5>", "foo", 0.35));
    assert.throws(() => applyBulkLoraStrength(PROMPT, 5));
});

test("J: malformed or contract-invalid directives are not repaired", () => {
    const text = "a, <lora:broken>, <lora:foo:1.0>, <lora: spaced:1.0>, <lora:toostrong:9>, <lora:unclosed:0.5";
    const { value, count } = applyBulkLoraStrength(text, 0.2);
    assert.equal(count, 1);
    assert.equal(value, "a, <lora:broken>, <lora:foo:0.2>, <lora: spaced:1.0>, <lora:toostrong:9>, <lora:unclosed:0.5");
    assert.equal(countBulkEditableLoras(text), 1);
});

test("K: no added LoRAs means no mutation", () => {
    const text = "1girl, smile, __pose__, <embedding:x>";
    assert.deepEqual(applyBulkLoraStrength(text, 0.2), { value: text, count: 0 });
    assert.equal(countBulkEditableLoras(text), 0);
    assert.equal(countBulkEditableLoras(""), 0);
});
