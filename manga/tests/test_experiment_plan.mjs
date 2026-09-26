// MANGA-EXPERIMENT-OUTPUT-PRODUCTION1: presets vs live catalog, X/Y/Z expansion, 64-cell cap,
// literal Prompt S/R, first_lora generation order, deterministic Grid layout.  Pure; no DOM, no GPU.
import test from "node:test";
import assert from "node:assert/strict";
import {
    EXPERIMENT_MAX_CELLS, PRESET_STATUS, SAMPLER_PRESETS, cellFragment, classifyPreset, classifyPresets,
    deriveCellSettings, expandExperiment, firstLoraFromResolved, gridGeometry, literalReplaceAll,
    planGridPages, presetChanges
} from "../app/src/domain/experiment_plan.js";

// Exact runtime catalog captured live from 8189 during this Card's capability audit.
const LIVE = {
    samplers: ["euler", "euler_cfg_pp", "euler_ancestral", "euler_ancestral_cfg_pp", "heun", "heunpp2", "exp_heun_2_x0",
        "exp_heun_2_x0_sde", "dpm_2", "dpm_2_ancestral", "lms", "dpm_fast", "dpm_adaptive", "dpmpp_2s_ancestral",
        "dpmpp_2s_ancestral_cfg_pp", "dpmpp_sde", "dpmpp_sde_gpu", "dpmpp_2m", "dpmpp_2m_cfg_pp", "dpmpp_2m_sde",
        "dpmpp_2m_sde_gpu", "dpmpp_2m_sde_heun", "dpmpp_2m_sde_heun_gpu", "dpmpp_3m_sde", "dpmpp_3m_sde_gpu", "ddpm",
        "lcm", "ipndm", "ipndm_v", "deis", "res_multistep", "res_multistep_cfg_pp", "res_multistep_ancestral",
        "res_multistep_ancestral_cfg_pp", "gradient_estimation", "gradient_estimation_cfg_pp", "er_sde", "seeds_2",
        "seeds_3", "sa_solver", "sa_solver_pece", "ddim", "uni_pc", "uni_pc_bh2"],
    schedulers: ["simple", "sgm_uniform", "karras", "exponential", "ddim_uniform", "beta", "normal", "linear_quadratic", "kl_optimal"],
    checkpoints: ["a/ckA.safetensors", "b/ckB.safetensors", "ckC.safetensors", "d/ckD.safetensors"].map(id => ({ id, available: true }))
        .concat([{ id: "gone.safetensors", available: false }]),
    product_bounds: { steps: { min: 1, max: 100 }, cfg: { min: 0, max: 30 }, seed: { min: 0, max: 4294967295 } },
    backend_bounds: { steps: { min: 1, max: 10000 }, cfg: { min: 0, max: 100 } },
};
const BASE = Object.freeze({ mode: "txt2img", checkpoint_id: "a/ckA.safetensors", positive_raw: "1girl, <lora:foo:0.3>, smile",
    negative_raw: "lowres", sampler_id: "euler", scheduler_id: "simple", steps: 20, cfg: 7, width: 832, height: 1216,
    seed_requested: "5", capability_revision: "rev" });

test("preset audit against the LIVE runtime catalog: no Owner preset is fully supported, nothing substituted", () => {
    const byId = Object.fromEntries(classifyPresets(LIVE).map(item => [item.id, item]));
    assert.equal(byId.smea_dy_sgm_uniform.status, PRESET_STATUS.PARTIAL);
    assert.deepEqual(byId.smea_dy_sgm_uniform.apply, { scheduler_id: "sgm_uniform" });
    assert.equal(byId.euler_negative_simple.status, PRESET_STATUS.PARTIAL);
    assert.deepEqual(byId.dpm2_phi.apply, { sampler_id: "dpm_2" });
    assert.equal(byId.euler_negative_ays11.status, PRESET_STATUS.UNAVAILABLE);
    assert.equal(byId.euler_cosine.status, PRESET_STATUS.PARTIAL);
    assert.deepEqual(byId.euler_cosine.missing, ["Cosine"]);
    assert.equal(byId.euler_negative_invcos_sf.status, PRESET_STATUS.UNAVAILABLE);
    assert.equal(byId.ays_gits.status, PRESET_STATUS.UNAVAILABLE);
    for (const item of Object.values(byId)) {
        for (const id of Object.values(item.apply)) assert.ok(LIVE.samplers.includes(id) || LIVE.schedulers.includes(id), `${id} is a real runtime ID`);
    }
    // No preset maps an unverified label onto a different runtime algorithm.
    for (const preset of SAMPLER_PRESETS) {
        for (const part of [preset.sampler, preset.scheduler]) {
            for (const id of part.ids) assert.ok(LIVE.samplers.includes(id) || LIVE.schedulers.includes(id), `candidate ${id} was audited`);
        }
    }
});

test("preset application: SUPPORTED sets both; PARTIAL only on explicit request; UNAVAILABLE never", () => {
    const supported = classifyPreset(SAMPLER_PRESETS.find(p => p.id === "dpm2_phi"), { ...LIVE, schedulers: [...LIVE.schedulers] });
    assert.equal(supported.status, PRESET_STATUS.PARTIAL);
    assert.equal(presetChanges(supported).ok, false, "partial is not applied implicitly");
    const partial = presetChanges(supported, { allowPartial: true });
    assert.deepEqual(partial.changes, { sampler_id: "dpm_2" });
    assert.deepEqual(partial.missing, ["Phi"]);
    const full = classifyPreset({ id: "t", sampler: { label: "Euler", ids: ["euler"] }, scheduler: { label: "Simple", ids: ["simple"] } }, LIVE);
    assert.equal(full.status, PRESET_STATUS.SUPPORTED);
    assert.deepEqual(presetChanges(full).changes, { sampler_id: "euler", scheduler_id: "simple" });
    const none = classifyPreset(SAMPLER_PRESETS.find(p => p.id === "ays_gits"), LIVE);
    assert.equal(presetChanges(none, { allowPartial: true }).ok, false);
    assert.equal(classifyPreset(SAMPLER_PRESETS[0], null).status, PRESET_STATUS.UNAVAILABLE, "no catalog -> unavailable");
});

test("X/Y/Z Cartesian expansion: disabled axis = one value; X fastest, then Y, then Z", () => {
    const four = expandExperiment({ x: { type: "checkpoint", values: LIVE.checkpoints.slice(0, 4).map(c => c.id) } }, LIVE);
    assert.equal(four.blocked, "");
    assert.deepEqual(four.counts, { x: 4, y: 1, z: 1 });
    assert.equal(four.total, 4);
    const xyz = expandExperiment({ x: { type: "steps", text: "10, 20" }, y: { type: "cfg", text: "4,5,6" },
        z: { type: "seed", text: "1, -1" } }, LIVE);
    assert.equal(xyz.total, 12);
    assert.deepEqual(xyz.cells.map(c => [c.x, c.y, c.z]).slice(0, 7),
        [[0, 0, 0], [1, 0, 0], [0, 1, 0], [1, 1, 0], [0, 2, 0], [1, 2, 0], [0, 0, 1]]);
    assert.deepEqual(xyz.cells.map(c => c.index), [...Array(12).keys()], "index = x + nx*(y + ny*z)");
    const again = expandExperiment({ x: { type: "steps", text: "10, 20" }, y: { type: "cfg", text: "4,5,6" }, z: { type: "seed", text: "1, -1" } }, LIVE);
    assert.deepEqual(again.cells, xyz.cells, "deterministic");
});

test("64-cell cap blocks with counts; never truncates; axis errors are explicit", () => {
    const steps = Array.from({ length: 8 }, (_, i) => i + 1).join(",");
    const ok = expandExperiment({ x: { type: "steps", text: steps }, y: { type: "seed", text: steps } }, LIVE);
    assert.equal(ok.total, EXPERIMENT_MAX_CELLS);
    assert.equal(ok.blocked, "");
    const over = expandExperiment({ x: { type: "steps", text: steps }, y: { type: "seed", text: steps }, z: { type: "cfg", text: "1,2" } }, LIVE);
    assert.equal(over.total, 128);
    assert.match(over.blocked, /8 × 8 × 2 = 128 cells exceeds the 64-cell limit/);
    assert.equal(over.cells.length, 0, "blocked, not truncated");
    assert.match(expandExperiment({ x: { type: "checkpoint", values: ["gone.safetensors"] } }, LIVE).blocked, /Checkpoint unavailable/);
    assert.match(expandExperiment({ x: { type: "sampler", values: ["euler_smea_dy"] } }, LIVE).blocked, /not in runtime catalog/);
    assert.match(expandExperiment({ x: { type: "steps", text: "0" } }, LIVE).blocked, /Steps value '0'/);
    assert.match(expandExperiment({ x: { type: "seed", text: "-2" } }, LIVE).blocked, /Seed value '-2'/);
    assert.equal(expandExperiment({ x: { type: "seed", text: "-1, 7" } }, LIVE).blocked, "", "seed -1 stays valid");
    assert.match(expandExperiment({ x: { type: "steps", text: "20" }, y: { type: "steps", text: "30" } }, LIVE).blocked, /same setting/);
    assert.match(expandExperiment({}, LIVE).blocked, /Enable at least one axis/);
    assert.match(expandExperiment({ x: { type: "steps", text: "20, 20" } }, LIVE).blocked, /repeats/);
});

test("Prompt S/R: literal (no regex), all occurrences, source prompt unchanged, not-found is an error", () => {
    assert.deepEqual(literalReplaceAll("a.b a.b", "a.b", "$&"), { text: "$& $&", count: 2 }, "no regex / replacement patterns");
    assert.equal(literalReplaceAll("axb", "a.b", "Z").count, 0, "'.' is literal");
    const plan = expandExperiment({ x: { type: "prompt_sr", search: "<lora:foo:0.3>", replacements: "<lora:bar:0.3>\n<lora:baz:0.3>\n" } }, LIVE);
    assert.equal(plan.total, 2);
    const base = structuredClone(BASE);
    const cells = plan.cells.map(cell => deriveCellSettings(base, cell));
    assert.equal(cells[0].settings.positive_raw, "1girl, <lora:bar:0.3>, smile");
    assert.equal(cells[1].settings.positive_raw, "1girl, <lora:baz:0.3>, smile");
    assert.deepEqual(base, BASE, "source prompt/settings are never mutated");
    const missing = expandExperiment({ x: { type: "prompt_sr", search: "<lora:nope:1>", replacements: "<lora:bar:1>" } }, LIVE);
    const result = deriveCellSettings(base, missing.cells[0]);
    assert.equal(result.ok, false);
    assert.match(result.error, /Search string not found: <lora:nope:1>/);
    assert.match(expandExperiment({ x: { type: "prompt_sr", search: " ", replacements: "x" } }, LIVE).blocked, /needs a Search string/);
    // Explicit baseline: the search string itself may be one of the replacement values.
    const baseline = expandExperiment({ x: { type: "prompt_sr", search: "smile", replacements: "smile\ngrin" } }, LIVE);
    assert.deepEqual(baseline.cells.map(c => deriveCellSettings(base, c).settings.positive_raw),
        ["1girl, <lora:foo:0.3>, smile", "1girl, <lora:foo:0.3>, grin"]);
});

test("cell settings: overrides only the axis field; S/R output still goes through normal LoRA compile", () => {
    const plan = expandExperiment({ x: { type: "checkpoint", values: ["b/ckB.safetensors"] }, y: { type: "scheduler", values: ["karras"] },
        z: { type: "prompt_sr", search: "<lora:foo:0.3>", replacements: "<lora:foo:0.3>, <lora:bar:0.5>" } }, LIVE);
    const { settings } = deriveCellSettings(BASE, plan.cells[0]);
    assert.equal(settings.checkpoint_id, "b/ckB.safetensors");
    assert.equal(settings.scheduler_id, "karras");
    assert.equal(settings.sampler_id, BASE.sampler_id);
    assert.equal(settings.positive_raw, "1girl, <lora:foo:0.3>, <lora:bar:0.5>, smile", "plain prompt text; LoRA parsing stays backend-owned");
    assert.equal(cellFragment(plan.cells[0]), `ckB-karras-${"<lora:foo:0.3>, <lora:bar:0.5>".slice(0, 24)}`, "bounded per-axis fragment");
});

test("first_lora comes from backend generation order (resolved_loras), not card order; none -> empty", () => {
    assert.equal(firstLoraFromResolved([{ id: "chars/zeta_v2.safetensors" }, { id: "alpha.safetensors" }]), "zeta_v2");
    assert.equal(firstLoraFromResolved([]), "");
    assert.equal(firstLoraFromResolved(undefined), "");
});

test("Grid pages: single axis compact; X/Y columns×rows; one page per Z; failed slot keeps its position", () => {
    const single = expandExperiment({ y: { type: "steps", text: "1,2,3,4,5" } }, LIVE);
    const [page] = planGridPages(single);
    assert.deepEqual([page.cols, page.rows], [3, 2]);
    assert.deepEqual(page.slots.map(s => [s.index, s.col, s.row]), [[0, 0, 0], [1, 1, 0], [2, 2, 0], [3, 0, 1], [4, 1, 1]]);
    assert.deepEqual(planGridPages(expandExperiment({ x: { type: "steps", text: "1,2,3,4" } }, LIVE))[0].cols, 4);
    const xyz = expandExperiment({ x: { type: "steps", text: "1,2,3" }, y: { type: "cfg", text: "4,5" }, z: { type: "seed", text: "7,8" } }, LIVE);
    const pages = planGridPages(xyz);
    assert.equal(pages.length, 2);
    assert.deepEqual([pages[1].cols, pages[1].rows, pages[1].title], [3, 2, "Z=8"]);
    assert.deepEqual(pages[1].slots.map(s => [s.index, s.col, s.row]), [[6, 0, 0], [7, 1, 0], [8, 2, 0], [9, 0, 1], [10, 1, 1], [11, 2, 1]]);
    // Geometry: natural size, centred, no stretching; failed cell (index 7) has no image but keeps (1,0).
    const sizes = new Map([[6, { width: 832, height: 1216 }], [8, { width: 800, height: 1200 }], [9, { width: 832, height: 1216 }],
        [10, { width: 832, height: 1216 }], [11, { width: 832, height: 1216 }]]);
    const geo = gridGeometry(pages[1], sizes, { labels: true });
    assert.deepEqual([geo.cellW, geo.cellH], [832, 1216]);
    const failed = geo.slots.find(s => s.index === 7);
    assert.equal(failed.image, null);
    assert.deepEqual([failed.col, failed.row], [1, 0]);
    const small = geo.slots.find(s => s.index === 8).image;
    assert.deepEqual([small.w, small.h], [800, 1200], "drawn at natural size");
    assert.equal(small.x - geo.slots.find(s => s.index === 8).x, 16, "centred horizontally");
    assert.equal(geo.scale, 1);
    assert.equal(geo.width, 3 * 832 + 4 * 8);
    assert.equal(geo.height, 40 + 2 * (1216 + 36) + 3 * 8);
    const noLabels = gridGeometry(pages[1], sizes, { labels: false });
    assert.equal(noLabels.height, 2 * 1216 + 3 * 8);
    // Oversized pages scale uniformly (aspect preserved).
    const big = gridGeometry({ cols: 8, rows: 8, title: "", slots: [{ index: 0, col: 0, row: 0 }] }, new Map([[0, { width: 2048, height: 2048 }]]), { labels: false });
    assert.ok(big.scale < 1);
    assert.ok(Math.abs(big.outWidth / big.outHeight - big.width / big.height) < 0.01);
    assert.ok(big.outWidth <= 16384 && big.outWidth * big.outHeight <= 120_000_000 * 1.001);
});
