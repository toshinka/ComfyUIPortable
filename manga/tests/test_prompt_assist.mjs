// MANGA-PROMPT-ASSIST-PRODUCTION1: autocomplete root-cause fixes + Wildcard insertion contract.
import test from "node:test";
import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";
import {
    LOAD_FAILED, detectPromptCompletionContext, formatWildcardToken, insertPromptWildcard, insertWildcardAtCursor,
    loadLoraCatalog, loadWildcardCatalog, queryTagCatalog,
} from "../app/src/view/tag_autocomplete.js";
import { listWildcardFolder } from "../app/src/view/prompt_assist.js";

const REPO = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..", "..");
const PYTHON = process.env.TEGAKI_PYTHON || "python";
const CATALOG = [
    { tag: "long_hair", category: "general", ranking: 100 },
    { tag: "blue_eyes", category: "general", ranking: 90 },
    { tag: "smile", category: "general", ranking: 80 },
];

test("cause 1: space-typed queries match the underscore Danbooru catalog", () => {
    assert.deepEqual(queryTagCatalog(CATALOG, "long h").map(e => e.tag), ["long_hair"]);
    assert.deepEqual(queryTagCatalog(CATALOG, "blue  ey").map(e => e.tag), ["blue_eyes"]);
    assert.deepEqual(queryTagCatalog(CATALOG, "long_h").map(e => e.tag), ["long_hair"]);
});

test("cause 2: a failed LoRA/Wildcard load is not cached as a permanent empty list", async () => {
    for (const [load, payload] of [[loadLoraCatalog, { loras: [{ id: "styles/ink.safetensors", available: true }] }],
                                   [loadWildcardCatalog, { wildcards: ["simple"] }]]) {
        const url = `/fixture/${load.name}/${Date.now()}`;
        let calls = 0;
        const failing = async () => { calls++; return { ok: false, status: 502, json: async () => ({}) }; };
        const first = await load(url, failing);
        assert.deepEqual([...first], []);
        assert.equal(first[LOAD_FAILED], true);
        const ok = async () => { calls++; return { ok: true, json: async () => payload }; };
        const second = await load(url, ok);
        assert.equal(calls, 2, "backend not ready at page load must be retried later");
        assert.equal(second[LOAD_FAILED], undefined);
        assert.equal(second.length, 1);
        await load(url, ok);
        assert.equal(calls, 2, "successful loads stay cached");
    }
});

test("wildcard token is the existing __name__ syntax, nested identity preserved", () => {
    assert.equal(formatWildcardToken("simple"), "__simple__");
    assert.equal(formatWildcardToken("nested\\leaf"), "__nested/leaf__");
    for (const bad of ["", "a__b", "a,b", "a\nb", "{a|b}"]) assert.throws(() => formatWildcardToken(bad));
    // autocomplete insertion and panel insertion produce the same token (one formatter)
    const ctx = detectPromptCompletionContext("1girl, __nes", 12);
    assert.equal(insertPromptWildcard("1girl, __nes", ctx, "nested/leaf").value, `1girl, ${formatWildcardToken("nested/leaf")}`);
});

test("wildcard click insertion at the caret preserves unrelated text", () => {
    assert.equal(insertWildcardAtCursor("", 0, 0, "simple").value, "__simple__");
    assert.equal(insertWildcardAtCursor("masterpiece, smile", 18, 18, "simple").value, "masterpiece, smile, __simple__");
    assert.equal(insertWildcardAtCursor("masterpiece, smile", 12, 12, "nested/leaf").value, "masterpiece, __nested/leaf__, smile");
    assert.equal(insertWildcardAtCursor("a, ", 3, 3, "simple").value, "a, __simple__");
    const r = insertWildcardAtCursor("{red|blue}, 1girl", 17, 17, "simple");
    assert.equal(r.value, "{red|blue}, 1girl, __simple__");
    assert.equal(r.caret, r.value.length);
});

test("wildcard folders are browsed one level at a time", () => {
    const names = ["simple", "nested/leaf", "nested/deeper/x", "other/y"];
    assert.deepEqual(listWildcardFolder(names, ""), {
        folders: [{ id: "nested", name: "nested" }, { id: "other", name: "other" }],
        entries: [{ id: "simple", name: "simple" }],
    });
    assert.deepEqual(listWildcardFolder(names, "nested"), {
        folders: [{ id: "nested/deeper", name: "deeper" }],
        entries: [{ id: "nested/leaf", name: "leaf" }],
    });
});

test("generation contract unchanged: inserted token expands via the existing compiler", () => {
    const dir = fs.mkdtempSync(path.join(os.tmpdir(), "tegaki-wc-"));
    fs.mkdirSync(path.join(dir, "nested"));
    fs.writeFileSync(path.join(dir, "nested", "leaf.txt"), "cat\n");
    try {
        const prompt = insertWildcardAtCursor("1girl", 5, 5, "nested/leaf").value;
        const script = [
            "import sys, json, types",
            `sys.path.insert(0, ${JSON.stringify(REPO)})`,
            "pkg = types.ModuleType('custom_nodes_custom.tegaki_manga_nodes')",
            `pkg.__path__ = [${JSON.stringify(path.join(REPO, "custom_nodes_custom", "tegaki_manga_nodes"))}]`,
            "sys.modules['custom_nodes_custom.tegaki_manga_nodes'] = pkg",
            "from custom_nodes_custom.tegaki_manga_nodes.basic_generation import _expand_dynamic_prompt",
            `print(json.dumps(_expand_dynamic_prompt(${JSON.stringify(prompt)}, 42, 'positive')[0]))`,
        ].join("\n");
        const expanded = JSON.parse(execFileSync(PYTHON, ["-c", script], {
            encoding: "utf8", env: { ...process.env, TEGAKI_MANGA_WILDCARDS_DIR: dir },
        }));
        assert.equal(prompt, "1girl, __nested/leaf__");
        assert.equal(expanded, "1girl, cat");
    } finally {
        fs.rmSync(dir, { recursive: true, force: true });
    }
});
