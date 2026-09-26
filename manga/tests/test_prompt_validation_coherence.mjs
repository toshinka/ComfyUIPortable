// MANGA-PROMPT-VALIDATION-COHERENCE1: one authoritative LoRA validation snapshot per exact
// prompt content, consumed by BOTH the LoRA status panel and the Generate gate.
//
// Root cause reproduced here: the validator's settle only called updateAll(), which never
// re-renders the Generate gate (generation_view renderStatus).  The gate therefore kept the
// "Checking LoRAs…" it computed while the request was pending, until an unrelated store edit
// (delete + Undo) happened to re-render it.
import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import {
    addLoraToken, applyBulkLoraStrength, createLoraValidator, isBlockingProblem, loraBlockReasonFromDiagnostics,
    loraStatusSummary, mountLoraDiagnostics, removeLoraToken, sourcesHaveLora, sourcesHaveWildcards,
    updateLoraTokenStrength,
} from "../app/src/view/lora_panel.js";
import { generationBlockReason, setLoraValidationProvider } from "../app/src/view/generation_view.js";

const RESOLVED = name => ({ source: "page_positive", name, status: "RESOLVED", resolved_id: `${name}.safetensors` });
const MISSING = name => ({ source: "page_positive", name, status: "LORA_UNAVAILABLE", message: "missing" });
const KNOWN = new Set(["foo", "bar", "baz"]);

/** Fake backend: resolves names in KNOWN; each call is held until released (controllable order). */
function fakeBackend() {
    const calls = [];
    const fetchImpl = (_url, init) => new Promise(resolve => {
        const { sources } = JSON.parse(init.body);
        const entries = [];
        for (const source of sources) {
            for (const match of String(source.text).matchAll(/<lora:([^:<>]+):([^>]+)>/g)) {
                entries.push(KNOWN.has(match[1]) ? RESOLVED(match[1]) : MISSING(match[1]));
            }
        }
        const body = { ok: true, entries, chain: entries.filter(e => e.status === "RESOLVED"),
            problems: entries.filter(e => e.status !== "RESOLVED").length };
        calls.push({ sources, release: () => resolve({ ok: true, status: 200, json: async () => body }) });
    });
    return { calls, fetchImpl };
}
const flush = () => new Promise(resolve => setTimeout(resolve, 0));

/** Mirror of the index.html wiring: provider for the gate + settle refreshes the gate. */
function workspace() {
    const backend = fakeBackend();
    const page = { style_prompt: "", style_negative_prompt: "" };
    const renders = { gate: [] };
    let gateReason = null;
    const state = {
        catalog: {
            checkpoints: [{ id: "ck.safetensors", available: true }], samplers: ["euler"], schedulers: ["normal"],
            product_bounds: { steps: { min: 1, max: 100 }, cfg: { min: 0, max: 30 }, width: { min: 256, max: 2048 },
                height: { min: 256, max: 2048 }, max_pixels: 4194304 },
            backend_bounds: { steps: { min: 1, max: 100 }, cfg: { min: 0, max: 30 }, width: { min: 256, max: 2048 },
                height: { min: 256, max: 2048 } }, revision: "r", loras: [],
        },
        draft: { checkpoint_id: "ck.safetensors", sampler_id: "euler", scheduler_id: "normal", steps: "20", cfg: "7",
            width: "1024", height: "1024", seed_requested: "1", positive_raw: "", negative_raw: "" },
    };
    const store = { getPage: () => page, getDocument: () => ({ pages: [page] }) };
    // generation_view.renderStatus equivalent
    const renderGate = () => { gateReason = generationBlockReason(state, store, "global"); renders.gate.push(gateReason); };
    const validator = createLoraValidator({ fetchImpl: backend.fetchImpl, onSettled: () => renderGate() });
    setLoraValidationProvider((positive, negative) => {
        const sources = [{ source: "page_positive", text: positive }, { source: "page_negative", text: negative }];
        if (!sourcesHaveLora(sources)) return "";
        const result = validator.peek(sources);
        if (!result) { validator.request(sources); return "Checking LoRAs…"; }
        return loraBlockReasonFromDiagnostics(result);
    });
    const edit = (text) => { page.style_prompt = text; renderGate(); }; // store edit -> gate render
    return { backend, validator, page, edit, get gate() { return gateReason; }, renderGate, renders };
}

test("A/C: valid prompt reaches ALL RESOLVED and the gate clears WITHOUT any further edit", async () => {
    const ws = workspace();
    ws.edit("1girl, <lora:foo:0.5>, <lora:bar:0.3>");
    assert.equal(ws.gate, "Checking LoRAs…");
    await flush();
    ws.backend.calls[0].release();
    await flush(); await flush();
    assert.equal(ws.gate, "", "settle re-rendered the gate: no stuck 'Checking LoRAs…', no delete+Undo needed");
    assert.equal(loraStatusSummary(ws.validator.peek([{ source: "page_positive", text: ws.page.style_prompt },
        { source: "page_negative", text: "" }])), "LoRA status · all resolved");
    setLoraValidationProvider(null);
});

test("B: an old slow validation cannot overwrite or block a newer prompt", async () => {
    const ws = workspace();
    ws.edit("<lora:missing:1>");            // request #0 (slow, invalid)
    ws.edit("<lora:foo:1>");                // request #1 (current, valid)
    await flush();
    ws.backend.calls[1].release();
    await flush(); await flush();
    assert.equal(ws.gate, "");
    ws.backend.calls[0].release();          // stale reply lands late
    await flush(); await flush();
    assert.equal(ws.gate, "", "late result for the older prompt does not replace the current state");
    ws.edit("<lora:missing:1>");            // going back re-uses that prompt's own snapshot
    assert.match(ws.gate, /unresolved LoRA: missing NOT FOUND/);
    setLoraValidationProvider(null);
});

async function settleAll(ws) {
    for (let i = 0; i < 4; i += 1) {
        for (const call of ws.backend.calls.splice(0)) call.release();
        await flush();
    }
}

test("D/E/F/G/H: Add, Remove, strength, bulk strength and Wildcard insertion all validate the current text", async () => {
    const ws = workspace();
    const steps = [
        ["Add", text => addLoraToken(text, "foo", 0.5)],
        ["Add invalid", text => addLoraToken(text, "nope", 1)],
        ["Remove", text => removeLoraToken(text, "nope")],
        ["strength", text => updateLoraTokenStrength(text, "foo", 0.8)],
        ["bulk", text => applyBulkLoraStrength(addLoraToken(text, "bar", 1), 0.2).value],
        ["wildcard", text => `${text}, __girl1__`],
    ];
    let text = "1girl";
    for (const [label, mutate] of steps) {
        text = mutate(text);
        const sources = [{ source: "page_positive", text }, { source: "page_negative", text: "" }];
        const known = ws.validator.peek(sources);
        ws.edit(text);
        if (!known) {
            assert.equal(ws.gate, "Checking LoRAs…", `${label}: validates the new text`);
            await flush();
            assert.equal(ws.backend.calls.at(-1).sources[0].text, text, `${label}: request is for the current text`);
        } else {
            assert.equal(ws.gate, loraBlockReasonFromDiagnostics(known), `${label}: same content re-uses its snapshot`);
        }
        await settleAll(ws);
        const expectBlocked = text.includes("<lora:nope:");
        assert.equal(Boolean(ws.gate), expectBlocked, `${label}: gate matches the CURRENT text (${text})`);
    }
    assert.equal(ws.page.style_prompt, "1girl, <lora:foo:0.2>, <lora:bar:0.2>, __girl1__");
    setLoraValidationProvider(null);
});

test("I: Global/Scene switch validates the prompt of the selected target", async () => {
    const backend = fakeBackend();
    const validator = createLoraValidator({ fetchImpl: backend.fetchImpl });
    const page = { style_prompt: "<lora:foo:1>", scenes: [{ scene_id: "s1", prompt: "<lora:nope:1>" }] };
    let target = "global";
    const getSources = () => target === "global"
        ? [{ source: "page_positive", text: page.style_prompt }]
        : [{ source: "page_positive", text: page.style_prompt }, { source: "scene_positive", text: page.scenes[0].prompt }];
    const container = fakeContainer();
    const diag = mountLoraDiagnostics({ container, validator, getSources });
    diag.refresh();
    await new Promise(r => setTimeout(r, 300));
    await settleAll({ backend });
    diag.refresh();
    assert.equal(container.headText(), "LoRA status · all resolved");
    target = "s1";
    diag.refresh();
    await new Promise(r => setTimeout(r, 300));
    assert.equal(backend.calls.at(-1).sources.length, 2, "Scene target sends Global + Scene sources");
    await settleAll({ backend });
    diag.refresh();
    assert.equal(container.headText(), "LoRA status · 1 problem");
    target = "global";
    diag.refresh();
    assert.equal(container.headText(), "LoRA status · all resolved", "Scene -> Global shows the Global snapshot again");
});

test("J: a current invalid LoRA blocks with the current reason; conditional/dynamic entries do not", () => {
    const result = { ok: true, entries: [RESOLVED("foo"), MISSING("gone")], chain: [], problems: 1 };
    assert.equal(loraBlockReasonFromDiagnostics(result),
        "Generate disabled — unresolved LoRA: gone NOT FOUND. See LoRA status under the prompt.");
    const conditional = { ok: true, chain: [], problems: 0, entries: [
        { ...MISSING("maybe"), conditional: true, blocking: false },
        { source: "page_positive", raw: "<lora:{a|b}:1>", status: "DYNAMIC_LORA", blocking: false },
    ] };
    assert.equal(loraBlockReasonFromDiagnostics(conditional), "");
    assert.equal(conditional.entries.filter(isBlockingProblem).length, 0);
    assert.equal(loraStatusSummary(conditional), "LoRA status · all resolved · 2 conditional");
});

test("transport failures are shown but expire so the prompt is re-validated (never stuck)", async () => {
    let now = 0;
    let fail = true;
    const validator = createLoraValidator({ now: () => now, failureTtlMs: 5000,
        fetchImpl: async () => fail ? Promise.reject(new Error("backend down"))
            : { ok: true, status: 200, json: async () => ({ ok: true, entries: [], chain: [], problems: 0 }) } });
    const sources = [{ source: "page_positive", text: "<lora:foo:1>" }];
    await validator.request(sources);
    assert.equal(validator.peek(sources).ok, false);
    now = 6000; fail = false;
    assert.equal(validator.peek(sources), null, "expired failure is not an answer");
    assert.equal((await validator.request(sources)).ok, true);
});

test("Wildcard-only prompt: honest note, no validation request, gate not blocked", async () => {
    const backend = fakeBackend();
    const validator = createLoraValidator({ fetchImpl: backend.fetchImpl });
    const sources = [{ source: "page_positive", text: "1girl, __lora_style__" }];
    assert.equal(sourcesHaveLora(sources), false);
    assert.equal(sourcesHaveWildcards(sources), true);
    const container = fakeContainer();
    mountLoraDiagnostics({ container, validator, getSources: () => sources }).refresh();
    await new Promise(r => setTimeout(r, 300));
    assert.equal(backend.calls.length, 0);
    assert.equal(container.hidden, false);
    assert.equal(container.headText(), "LoRA status · Wildcards may add LoRAs (resolved at generation)");
});

test("LoRA status collapses/reopens, header keeps the state, validation continues while collapsed", async () => {
    const backend = fakeBackend();
    const validator = createLoraValidator({ fetchImpl: backend.fetchImpl });
    let text = "<lora:foo:1>";
    const container = fakeContainer();
    const diag = mountLoraDiagnostics({ container, validator, getSources: () => [{ source: "page_positive", text }] });
    diag.refresh();
    await new Promise(r => setTimeout(r, 300));
    await settleAll({ backend });
    diag.refresh();
    container.toggle().onclick();
    assert.equal(diag.expanded, false);
    assert.equal(container.body().hidden, true);
    text = "<lora:foo:1>, <lora:gone:1>";
    diag.refresh();
    await new Promise(r => setTimeout(r, 300));
    assert.equal(backend.calls.length, 1, "collapsed panel still validates");
    await settleAll({ backend });
    diag.refresh();
    assert.equal(container.headText(), "LoRA status · 1 problem", "collapsed header does not hide the problem count");
    assert.equal(container.body().hidden, true, "stays collapsed across re-render");
    container.toggle().onclick();
    assert.equal(container.body().hidden, false);
});

test("root-cause regression: the workspace settle refreshes the Generate gate, not only updateAll()", () => {
    const html = fs.readFileSync(new URL("../app/index.html", import.meta.url), "utf8");
    const settle = html.slice(html.indexOf("const onLoraValidationSettled"), html.indexOf("const loraValidator ="));
    assert.match(settle, /updateAll\(\);/);
    assert.match(settle, /generation\?\.refresh\?\.\(\)/);
    assert.match(html, /createLoraValidator\(\{ onSettled: onLoraValidationSettled \}\)/);
    assert.ok(!/loraValidator\.request\(sources\)\.then\(\(\) => updateAll\(\)\)/.test(html), "old updateAll-only path removed");
    const view = fs.readFileSync(new URL("../app/src/view/generation_view.js", import.meta.url), "utf8");
    assert.match(view, /refresh: renderStatus/, "generation view exposes its gate renderer");
});

// --- minimal DOM stand-in for mountLoraDiagnostics -------------------------------------
function fakeNode(tag) {
    const node = {
        tagName: tag, children: [], className: "", textContent: "", hidden: false, dataset: {}, attrs: {}, onclick: null,
        classList: { toggle(name, on) { node.cls = { ...(node.cls || {}), [name]: on }; } },
        append(...kids) { node.children.push(...kids); }, appendChild(kid) { node.children.push(kid); return kid; },
        replaceChildren() { node.children = []; }, setAttribute(k, v) { node.attrs[k] = v; },
    };
    return node;
}
globalThis.document = { createElement: tag => fakeNode(tag) };
function fakeContainer() {
    const container = fakeNode("div");
    container.toggle = () => container.children.find(c => String(c.className).includes("mg-lora-diag-toggle"));
    container.body = () => container.children.find(c => String(c.className).includes("mg-lora-diag-body"));
    container.headText = () => container.toggle()?.textContent;
    return container;
}

test("'__' inside a LoRA name is not a Wildcard reference (UI note)", () => {
    const miki = "<lora:Miki_Hoshii__The_iDOLM_STER_2011__epoch_8:1.0>";
    assert.equal(sourcesHaveWildcards([{ source: "page_positive", text: miki }]), false);
    assert.equal(sourcesHaveWildcards([{ source: "page_positive", text: `__quality__, ${miki}` }]), true);
});
