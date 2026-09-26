// MANGA-ILLUSTRIOUS-LORA-PRODUCTION1: visible LoRA token editing preserves the Owner's prompt.
import test from "node:test";
import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";
import {
    addLoraToken, findLoraTokens, formatLoraStrength, formatLoraToken, removeLoraToken, updateLoraTokenStrength,
} from "../app/src/view/lora_panel.js";

const A = "characters/series_a/alice_v3.safetensors";
const B = "characters/series_b/alice_v3.safetensors";
const INK = "styles/ink.safetensors";

test("token syntax uses the canonical relative ID and default strength 1.0", () => {
    assert.equal(formatLoraToken(A), `<lora:${A}:1.0>`);
    assert.equal(formatLoraToken(A, 0.85), `<lora:${A}:0.85>`);
    assert.throws(() => formatLoraToken("C:/x.safetensors"));
    assert.throws(() => formatLoraToken(INK, 5));
});

test("strength text matches the backend formatter exactly", () => {
    const values = [1, 0.85, -1.25, 0, 0.1, 2.3333, -4, 4];
    const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..", "..");
    const script = [
        "import sys, json, types",
        `sys.path.insert(0, ${JSON.stringify(repoRoot)})`,
        "pkg = types.ModuleType('custom_nodes_custom.tegaki_manga_nodes')",
        `pkg.__path__ = [${JSON.stringify(path.join(repoRoot, "custom_nodes_custom", "tegaki_manga_nodes"))}]`,
        "sys.modules['custom_nodes_custom.tegaki_manga_nodes'] = pkg",
        "from custom_nodes_custom.tegaki_manga_nodes.basic_generation import format_lora_directive",
        `print(json.dumps([format_lora_directive(${JSON.stringify(INK)}, v) for v in ${JSON.stringify(values)}]))`,
    ].join("\n");
    const python = process.env.TEGAKI_PYTHON || "python";
    const backend = JSON.parse(execFileSync(python, ["-c", script], { encoding: "utf8" }));
    assert.deepEqual(values.map(v => formatLoraToken(INK, v)), backend);
    assert.equal(formatLoraStrength(1), "1.0");
});

test("add appends a visible token without touching manual text", () => {
    assert.equal(addLoraToken("", A), `<lora:${A}:1.0>`);
    assert.equal(addLoraToken("1girl, smile", A), `1girl, smile, <lora:${A}:1.0>`);
    assert.equal(addLoraToken("1girl, ", A), `1girl, <lora:${A}:1.0>`);
    const once = addLoraToken("1girl", A);
    assert.equal(addLoraToken(once, A), once, "adding the same LoRA twice is a no-op");
    const both = addLoraToken(once, B, 0.5);
    assert.deepEqual(findLoraTokens(both).map(t => [t.id, t.strength]), [[A, 1], [B, 0.5]]);
});

test("strength update rewrites only the matching token", () => {
    const text = `masterpiece, <lora:${A}:1.0>, {red|blue} hair, <lora:${B}:1.0>, __pose__`;
    assert.equal(updateLoraTokenStrength(text, B, 0.6),
        `masterpiece, <lora:${A}:1.0>, {red|blue} hair, <lora:${B}:0.6>, __pose__`);
});

test("remove deletes only the matching token and its inserted separator", () => {
    const manual = "1girl,  smile ,\n{a|b}, __hair__";
    const added = addLoraToken(addLoraToken(manual, A), B, 0.7);
    assert.equal(removeLoraToken(removeLoraToken(added, A), B), manual);
    assert.equal(removeLoraToken(`a, <lora:${A}:1.0>, b`, A), "a, b");
    assert.equal(removeLoraToken(`<lora:${A}:1.0>, a`, A), "a");
    assert.equal(removeLoraToken(`a, <lora:${B}:1.0>`, A), `a, <lora:${B}:1.0>`, "other duplicate-basename LoRA untouched");
});
