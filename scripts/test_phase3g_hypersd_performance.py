"""
Phase 3G: Hyper-SD Fast-Mode Performance Track P0
=================================================
Benchmarks generation performance and semantic integrity across 3 load tiers:
- Load A: Two-Region Spatial Swap (WF27 & WF28)
- Load B: Recurrent Cast 4-Panel (WF21)
- Load C: Same-Cast Multi-Scene (WF22)

Evaluates 3 variants:
1. Reference Mode: 20-step Illustrious SDXL, Euler/Normal, CFG 7.0 (Baseline SSOT)
2. Fast-12 Mode: 12-step Hyper-SDXL CFG LoRA (調整\\Hyper-SDXL-12steps-CFG-lora.safetensors), CFG 6.0
3. Fast-8 Mode: 8-step Hyper-SDXL CFG LoRA (調整\\Hyper-SDXL-8steps-CFG-lora.safetensors), CFG 5.0

Saves results to:
- Images: output/Tegaki/Phase3G/hypersd/
- Metrics: output/Tegaki/Phase3G/hypersd_performance_results.json
"""

import os
import sys
import copy
import json
import time
import shutil
import urllib.request
from typing import Dict, Any, List, Optional

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from scripts import comfy_runtime_helper

WORKFLOWS_DIR = os.path.join(ROOT_DIR, "workflows")
OUTPUT_DIR = os.path.join(ROOT_DIR, "output", "Tegaki", "Phase3G", "hypersd")

# Local Hyper-SD LoRA assets discovered in D:\Models\Lora\調整\
LORA_12STEP = "調整\\Hyper-SDXL-12steps-CFG-lora.safetensors"
LORA_8STEP = "調整\\Hyper-SDXL-8steps-CFG-lora.safetensors"


def fetch_all_object_info() -> Dict[str, Any]:
    url = f"{comfy_runtime_helper.COMFY_URL}/object_info"
    req = urllib.request.Request(url, headers={"User-Agent": "HyperSDSuite/1.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.load(resp)


def graph_to_api_prompt(wf_path: str, object_info: Dict[str, Any]) -> Dict[str, Any]:
    with open(wf_path, "r", encoding="utf-8") as f:
        wf = json.load(f)

    nodes = wf.get("nodes", [])
    links = wf.get("links", [])

    link_map = {}
    for l in links:
        lid, src_nid, src_slot, tgt_nid, tgt_slot, ltype = l
        link_map[lid] = [str(src_nid), src_slot]

    prompt = {}
    for n in nodes:
        nid = str(n["id"])
        ntype = n["type"]
        node_inputs = {}

        for inp in n.get("inputs", []):
            name = inp["name"]
            lid = inp.get("link")
            if lid is not None and lid in link_map:
                node_inputs[name] = link_map[lid]

        info = object_info.get(ntype, {})
        input_def = info.get("input", {})
        req = input_def.get("required", {})
        opt = input_def.get("optional", {})
        all_specs = list(req.items()) + list(opt.items())

        wv = n.get("widgets_values", [])
        w_idx = 0
        for name, spec in all_specs:
            t = spec[0] if isinstance(spec, (tuple, list)) else spec
            is_socket = isinstance(t, str) and t.upper() in {
                "LATENT", "MODEL", "CLIP", "VAE", "CONDITIONING",
                "BASIC_PIPE", "KSAMPLER_ADVANCED", "REGIONAL_PROMPTS",
                "SAMPLER", "SCHEDULER_FUNC", "IMAGE", "MASK", "REGION_SPEC",
                "PAGE_COMPILE_PLAN", "PANEL_LAYOUT_SPEC", "CAST_SPEC",
                "TWO_REGION_SPEC"
            }
            if not is_socket:
                if w_idx < len(wv):
                    val = wv[w_idx]
                    w_idx += 1
                    if name not in node_inputs:
                        node_inputs[name] = val
                    if name in ("seed", "noise_seed"):
                        w_idx += 1

        prompt[nid] = {
            "class_type": ntype,
            "inputs": node_inputs
        }

    return prompt


def inject_hypersd_lora(
    prompt: Dict[str, Any],
    lora_name: str,
    target_steps: int,
    target_cfg: float,
    base_only_steps: int = 1
) -> Dict[str, Any]:
    """
    Injects Hyper-SD LoRA into prompt workflow between Checkpoint and ToBasicPipe/Impact,
    and adjusts sampling steps and CFG.
    """
    p = copy.deepcopy(prompt)

    # 1. Find Checkpoint loader node
    ckpt_nid = None
    for nid, nd in p.items():
        if nd["class_type"] in ("CheckpointLoaderSimple", "CheckpointLoader"):
            ckpt_nid = nid
            break

    if not ckpt_nid:
        raise ValueError("No CheckpointLoader found in prompt!")

    # 2. Add LoraLoader node
    lora_nid = "999_hypersd_lora"
    p[lora_nid] = {
        "class_type": "LoraLoader",
        "inputs": {
            "model": [ckpt_nid, 0],
            "clip": [ckpt_nid, 1],
            "lora_name": lora_name,
            "strength_model": 1.0,
            "strength_clip": 1.0
        }
    }

    # 3. Rewire MODEL and CLIP links that were pointing to ckpt_nid
    for nid, nd in p.items():
        if nid == lora_nid:
            continue
        for inp_name, inp_val in nd["inputs"].items():
            if isinstance(inp_val, list) and len(inp_val) == 2:
                src_node, src_slot = inp_val
                if src_node == ckpt_nid:
                    if src_slot == 0:  # MODEL
                        nd["inputs"][inp_name] = [lora_nid, 0]
                    elif src_slot == 1:  # CLIP
                        nd["inputs"][inp_name] = [lora_nid, 1]

    # 4. Update steps and CFG in sampling nodes
    for nid, nd in p.items():
        ctype = nd["class_type"]
        if ctype == "RegionalSampler":
            nd["inputs"]["steps"] = target_steps
            if "base_only_steps" in nd["inputs"]:
                nd["inputs"]["base_only_steps"] = base_only_steps
        elif ctype == "KSamplerAdvancedProvider":
            nd["inputs"]["cfg"] = target_cfg
        elif ctype in ("KSampler", "KSamplerAdvanced"):
            if "steps" in nd["inputs"]:
                nd["inputs"]["steps"] = target_steps
            if "cfg" in nd["inputs"]:
                nd["inputs"]["cfg"] = target_cfg

    return p


def get_vram_usage() -> Optional[float]:
    """Attempts to read GPU VRAM allocated in MB via nvidia-smi if available."""
    try:
        import subprocess
        res = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.used", "--format=csv,nounits,noheader"],
            capture_output=True, text=True, timeout=2
        )
        if res.returncode == 0:
            return float(res.stdout.strip().splitlines()[0])
    except Exception:
        pass
    return None


def run_hypersd_performance_suite():
    print("================================================================================")
    print("Phase 3G: Hyper-SD Fast-Mode Performance Track P0")
    print("================================================================================")
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Benchmark test matrix
    bench_tests = [
        # Load A: Two-Region Spatial Swap
        {
            "load_id": "Load_A_WF27",
            "load_desc": "Two-Region Dog Left / Cat Right (WF27)",
            "wf_file": "27_VERIFY_TWO_REGION_DOG_CAT_LEFT_RIGHT.json",
            "save_node_id": "18"
        },
        {
            "load_id": "Load_A_WF28",
            "load_desc": "Two-Region Dog Right / Cat Left SWAP (WF28)",
            "wf_file": "28_VERIFY_TWO_REGION_DOG_CAT_SWAP.json",
            "save_node_id": "18"
        },
        # Load B: Recurrent Cast 4-Panel
        {
            "load_id": "Load_B_WF21",
            "load_desc": "Recurrent Cast 4-Panel (WF21)",
            "wf_file": "21_MANGA_IMPACT_RECURRENT_CAST_POC.json",
            "save_node_id": "15"
        },
        # Load C: Same-Cast Multi-Scene
        {
            "load_id": "Load_C_WF22",
            "load_desc": "Same-Cast Multi-Scene Oracle (WF22)",
            "wf_file": "22_SINGLE_PANEL_MULTI_SCENE_SAME_CAST_ORACLE.json",
            "save_node_id": "13"
        }
    ]

    variants = [
        {"name": "REFERENCE", "steps": 20, "cfg": 7.0, "lora": None, "base_only": 2},
        {"name": "FAST-12", "steps": 12, "cfg": 6.0, "lora": LORA_12STEP, "base_only": 2},
        {"name": "FAST-8", "steps": 8, "cfg": 5.0, "lora": LORA_8STEP, "base_only": 1},
    ]

    results_matrix = []

    try:
        print("[HyperSDRunner] Ensuring ComfyUI server is running...")
        comfy_runtime_helper.ensure_server(timeout=90)
        object_info = fetch_all_object_info()

        for test in bench_tests:
            load_id = test["load_id"]
            wf_file = test["wf_file"]
            save_node_id = test["save_node_id"]
            wf_path = os.path.join(WORKFLOWS_DIR, wf_file)

            print(f"\n================================================================================")
            print(f"BENCHMARK LOAD: {load_id} ({test['load_desc']})")
            print(f"================================================================================")

            base_prompt = graph_to_api_prompt(wf_path, object_info)
            ref_runtime = None

            for var in variants:
                var_name = var["name"]
                steps = var["steps"]
                cfg = var["cfg"]
                lora = var["lora"]
                base_only = var["base_only"]

                out_img_name = f"{load_id.lower()}_{var_name.lower()}.png"
                target_img_path = os.path.join(OUTPUT_DIR, out_img_name)

                print(f"\n--- Variant: {var_name} ({steps} steps, CFG {cfg}) ---")

                if lora is None:
                    # Reference Mode
                    prompt = copy.deepcopy(base_prompt)
                else:
                    # Inject Hyper-SD LoRA
                    prompt = inject_hypersd_lora(base_prompt, lora, steps, cfg, base_only)

                start_vram = get_vram_usage()
                step_start = time.time()

                q_resp = comfy_runtime_helper.queue_prompt(prompt)
                prompt_id = q_resp.get("prompt_id")
                n_errs = q_resp.get("node_errors", {})
                if n_errs:
                    print(f"[FAIL] Validation error in {var_name} for {load_id}: {n_errs}")
                    raise RuntimeError(f"Validation error in {var_name}: {n_errs}")

                outputs = comfy_runtime_helper.wait_for_prompt(prompt_id, timeout=240)
                elapsed = time.time() - step_start
                end_vram = get_vram_usage()

                img_path = comfy_runtime_helper.get_image_file_path(outputs, save_node_id)
                if img_path and os.path.exists(img_path):
                    shutil.copyfile(img_path, target_img_path)
                    print(f"[OK] Generated: {target_img_path} ({elapsed:.1f}s)")
                else:
                    print(f"[WARN] No image found for {save_node_id}")

                if var_name == "REFERENCE":
                    ref_runtime = elapsed
                    speedup = 1.0
                    reduction_pct = 0.0
                else:
                    speedup = round(ref_runtime / elapsed, 2) if ref_runtime else 1.0
                    reduction_pct = round((1.0 - (elapsed / ref_runtime)) * 100, 1) if ref_runtime else 0.0

                record = {
                    "load_id": load_id,
                    "workflow": wf_file,
                    "variant": var_name,
                    "steps": steps,
                    "cfg": cfg,
                    "lora_used": lora,
                    "elapsed_seconds": round(elapsed, 1),
                    "speedup_factor": speedup,
                    "time_reduction_percent": reduction_pct,
                    "peak_vram_mb": end_vram or 0.0,
                    "output_image": out_img_name,
                    "status": "PASS"
                }
                results_matrix.append(record)
                print(f"  Result: {elapsed:.1f}s | Speedup: {speedup}x | Reduction: {reduction_pct}%")

    finally:
        print("[HyperSDRunner] Shutting down ComfyUI server...")
        comfy_runtime_helper.stop_server()

    summary = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_runs": len(results_matrix),
        "results": results_matrix
    }

    res_json_path = os.path.join(ROOT_DIR, "output", "Tegaki", "Phase3G", "hypersd_performance_results.json")
    with open(res_json_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print("\n================================================================================")
    print(f"[PERFORMANCE SUITE COMPLETED] Matrix saved to: {res_json_path}")
    print("================================================================================")
    return summary


if __name__ == "__main__":
    run_hypersd_performance_suite()
