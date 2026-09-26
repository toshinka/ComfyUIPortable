// MANGA-LORA-PORTABLE-COMPAT-DIAGNOSTICS1: alias-aware token editing, trusted-index autocomplete,
// and the backend-authoritative Generate gate reason.
import test from "node:test";
import assert from "node:assert/strict";
import {
    addLoraToken, findLoraTokens, loraBlockReasonFromDiagnostics, loraNamesFor, removeLoraToken, updateLoraTokenStrength,
} from "../app/src/view/lora_panel.js";
import { normalizeLoraList, queryLoraCatalog, detectPromptCompletionContext, insertPromptLora } from "../app/src/view/tag_autocomplete.js";
import { compileGlobalGeneration, setLoraValidationProvider } from "../app/src/view/generation_view.js";

const FOO = { id: "!!!BASIC/0/foo.safetensors", token: "foo" };
const DUP_A = { id: "characters/A/dup.safetensors", token: "characters/A/dup" };

test("card editing recognises the LoRA under its alias or canonical names", () => {
    const names = loraNamesFor(FOO);
    assert.deepEqual(names, ["foo", "!!!BASIC/0/foo.safetensors", "!!!BASIC/0/foo"]);
    const added = addLoraToken("1girl", FOO.token, 1, names);
    assert.equal(added, "1girl, <lora:foo:1.0>");
    assert.equal(addLoraToken("1girl, <lora:!!!BASIC/0/foo:0.2>", FOO.token, 1, names), "1girl, <lora:!!!BASIC/0/foo:0.2>");
    // a legacy asset token keeps its own spelling; only the strength changes
    assert.equal(updateLoraTokenStrength("a, <lora:foo:0.2>, b", names, 0.35), "a, <lora:foo:0.35>, b");
    assert.equal(removeLoraToken("a, <lora:foo:0.2>, b, <lora:bar:0.1>", names), "a, b, <lora:bar:0.1>");
    assert.equal(addLoraToken("x", DUP_A.token, 1, loraNamesFor(DUP_A)), "x, <lora:characters/A/dup:1.0>");
    assert.deepEqual(findLoraTokens("<lora:characters/A/dup:1.0>").map(t => t.id), ["characters/A/dup"]);
});

test("autocomplete uses trusted-index entries: portable alias vs folder-qualified duplicates", () => {
    const loras = normalizeLoraList({ entries: [
        { id: "characters/A/dup.safetensors", token: "characters/A/dup", folder: "characters/A" },
        { id: "styles/dup.safetensors", token: "styles/dup", folder: "styles" },
        { id: "!!!BASIC/0/foo.safetensors", token: "foo", folder: "!!!BASIC/0" },
    ] });
    assert.deepEqual(normalizeLoraList(loras), loras, "re-normalization is idempotent");
    const dups = queryLoraCatalog(loras, "dup");
    assert.deepEqual(dups.map(e => [e.label, e.category, e.tag]),
        [["dup", "characters/A", "characters/A/dup"], ["dup", "styles", "styles/dup"]]);
    const ctx = detectPromptCompletionContext("1girl, <lora:fo", 15);
    const [foo] = queryLoraCatalog(loras, ctx.query);
    assert.equal(insertPromptLora("1girl, <lora:fo", ctx, foo.tag).value, "1girl, <lora:foo:1>");
});

test("Generate gate explains the unresolved LoRA from backend diagnostics", async () => {
    const diagnostics = { ok: true, problems: 2, chain: [], entries: [
        { name: "foo", status: "RESOLVED", resolved_id: FOO.id },
        { name: "dup", status: "LORA_AMBIGUOUS", candidates: [DUP_A.id, "styles/dup.safetensors"] },
        { name: "missing_style", status: "LORA_UNAVAILABLE" },
    ] };
    const reason = loraBlockReasonFromDiagnostics(diagnostics);
    assert.equal(reason, "Generate disabled — unresolved LoRA: dup AMBIGUOUS (+1 more). See LoRA status under the prompt.");
    assert.equal(loraBlockReasonFromDiagnostics({ ok: true, entries: [{ status: "RESOLVED" }], chain: [] }), "");

    const seen = [];
    setLoraValidationProvider((positive, negative) => { seen.push([positive, negative]); return reason; });
    const state = {
        catalog: {
            checkpoints: [{ id: "ck.safetensors", available: true }], samplers: ["euler"], schedulers: ["normal"],
            product_bounds: { steps: { min: 1, max: 100 }, cfg: { min: 0, max: 30 }, width: { min: 256, max: 2048 },
                height: { min: 256, max: 2048 }, max_pixels: 2097152 },
            backend_bounds: { steps: { min: 1, max: 100 }, cfg: { min: 0, max: 30 }, width: { min: 256, max: 2048 },
                height: { min: 256, max: 2048 } },
            revision: "r",
        },
        draft: { checkpoint_id: "ck.safetensors", sampler_id: "euler", scheduler_id: "normal", steps: "20", cfg: "7",
            width: "1024", height: "1024", seed_requested: "1" },
    };
    const store = { getPage: () => ({ style_prompt: "1girl, <lora:dup:0.5>", style_negative_prompt: "blurry" }) };
    await assert.rejects(compileGlobalGeneration(state, store, { compile: async () => assert.fail("must not compile") }),
        { message: reason });
    assert.deepEqual(seen, [["1girl, <lora:dup:0.5>", "blurry"]]);
    setLoraValidationProvider(null);
});
