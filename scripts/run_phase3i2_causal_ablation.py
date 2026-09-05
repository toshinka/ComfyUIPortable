"""
Phase 3I.2: Causal Ablation Suite Runner
========================================
Executes:
- Condition A: Reference Native 20s (CFG 7.0, base_only_steps=2, No LoRA, Base-Only CN 0.75/0.80) -> WF40
- Condition B: Native Short 12s (CFG 6.0, base_only_steps=2, No LoRA, Base-Only CN 0.75/0.80) -> WF45
- Condition C: Native CFG 6.0 20s (CFG 6.0, base_only_steps=2, No LoRA, Base-Only CN 0.75/0.80)
- Condition D: Hyper 12s (CFG 6.0, base_only_steps=2, Hyper-SDXL LoRA, Base-Only CN 0.75/0.80) -> WF46
- Condition E: Native 20s Base-Only 0 (CFG 7.0, base_only_steps=0, No LoRA, Base-Only CN 0.75/0.80) -> WF44
- Condition F: Regional Control - Shared Global 0.35 (CFG 7.0, base_only_steps=2, No LoRA, shared_global 0.35)
- Condition G: Regional Control - Per-Region Hint 0.35 (CFG 7.0, base_only_steps=2, No LoRA, per_region_hint 0.35) -> WF47

Guarantees:
- Zero validation errors
- Strict timeout breaker (300s per condition)
- Live VRAM and execution timing capture
- Saves results to output/Tegaki/Phase3I2/phase3i2_causal_ablation_results.json
"""

import os
import sys
import json
import time
import shutil
import subprocess
import urllib.request
from typing import Dict, Any, Union

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CUSTOM_NODES_DIR = os.path.join(ROOT_DIR, "custom_nodes_custom")
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
if CUSTOM_NODES_DIR not in sys.path:
    sys.path.insert(0, CUSTOM_NODES_DIR)

from scripts import comfy_runtime_helper
from scripts.generate_phase3i2_workflows import build_phase3i2_workflow

WORKFLOWS_DIR = os.path.join(ROOT_DIR, "workflows")
OUTPUT_DIR = os.path.join(ROOT_DIR, "output", "Tegaki", "Phase3I2", "canonical")


def get_gpu_vram_mb() -> int:
    try:
        res = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True
        )
        return int(res.stdout.strip().splitlines()[0])
    except Exception:
        return 0


def fetch_all_object_info() -> Dict[str, Any]:
    url = f"{comfy_runtime_helper.COMFY_URL}/object_info"
    req = urllib.request.Request(url, headers={"User-Agent": "Phase3I2Suite/1.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.load(resp)


def graph_to_api_prompt(wf_data: Union[str, Dict[str, Any]], object_info: Dict[str, Any]) -> Dict[str, Any]:
    if isinstance(wf_data, str):
        with open(wf_data, "r", encoding="utf-8") as f:
            wf = json.load(f)
    else:
        wf = wf_data

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
            is_socket = isinstance(t, str) and (
                t.upper() in {
                    "LATENT", "MODEL", "CLIP", "VAE", "CONDITIONING",
                    "BASIC_PIPE", "KSAMPLER_ADVANCED", "REGIONAL_PROMPTS",
                    "SAMPLER", "SCHEDULER_FUNC", "IMAGE", "MASK", "REGION_SPEC",
                    "PAGE_COMPILE_PLAN", "PANEL_LAYOUT_SPEC", "CAST_SPEC",
                    "TWO_REGION_SPEC", "CONTROL_NET"
                } or t == "*"
            )
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


def run_ablation_suite():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    results_file = os.path.join(ROOT_DIR, "output", "Tegaki", "Phase3I2", "phase3i2_causal_ablation_results.json")

    print("\n" + "=" * 80)
    print("Phase 3I.2: Causal Ablation Suite (Conditions A to G)")
    print("Target: RTX 4070 12GB | AnyTest v4 | Zero-Touch Execution")
    print("=" * 80)

    comfy_runtime_helper.ensure_server()
    object_info = fetch_all_object_info()

    char_alice = {
        "id": "char_alice",
        "name": "Alice",
        "enabled": True,
        "prompt": "1girl, blonde hair, twin tails, blue eyes, school uniform, white shirt, red necktie, pleated skirt",
        "negative_prompt": "worst quality, low quality, bad anatomy, duplicate girl",
        "loras": []
    }
    char_bob = {
        "id": "char_bob",
        "name": "Bob",
        "enabled": True,
        "prompt": "1boy, short black hair, dark eyes, school uniform, black gakuran jacket, male student",
        "negative_prompt": "worst quality, low quality, bad anatomy, duplicate boy",
        "loras": []
    }

    standard_attending = [
        {
            "character_id": "char_alice",
            "enabled": True,
            "prompt_override": "standing calmly",
            "negative_prompt_override": "",
            "area": {"x": 0.10, "y": 0.15, "w": 0.35, "h": 0.75}
        },
        {
            "character_id": "char_bob",
            "enabled": True,
            "prompt_override": "standing calmly",
            "negative_prompt_override": "",
            "area": {"x": 0.55, "y": 0.15, "w": 0.35, "h": 0.75}
        }
    ]

    standard_overrides = {
        "1": {
            "char_alice": {"area": {"x": 0.10, "y": 0.15, "w": 0.35, "h": 0.75}},
            "char_bob": {"area": {"x": 0.55, "y": 0.15, "w": 0.35, "h": 0.75}}
        }
    }

    # Define test conditions A through G
    conditions = [
        {
            "cond_id": "CondA",
            "name": "Native Reference 20s (CFG 7.0, base_only=2, no LoRA)",
            "wf_source": os.path.join(WORKFLOWS_DIR, "40_VERIFY_CN_AUTHORING_REFERENCE_PAIR.json"),
            "dest_filename": "CondA_Native20_CFG7_BaseOnly2.png",
            "steps": 20, "cfg": 7.0, "base_only_steps": 2, "fast_draft_12": False,
            "regional_mode": "off", "cn_strength": 0.75
        },
        {
            "cond_id": "CondB",
            "name": "Native Short 12s (CFG 6.0, base_only=2, no LoRA)",
            "wf_source": os.path.join(WORKFLOWS_DIR, "45_VERIFY_NATIVE12_CONTROL.json"),
            "dest_filename": "CondB_Native12_CFG6_BaseOnly2.png",
            "steps": 12, "cfg": 6.0, "base_only_steps": 2, "fast_draft_12": False,
            "regional_mode": "off", "cn_strength": 0.75
        },
        {
            "cond_id": "CondC",
            "name": "Native CFG 6.0 Control 20s (CFG 6.0, base_only=2, no LoRA)",
            "wf_source": build_phase3i2_workflow(
                wf_filename="CondC_NATIVE20_CFG6.json",
                title="Condition C: Native 20s CFG 6.0 Control",
                save_prefix="Phase3I2_CondC_Native20_CFG6",
                characters=[char_alice, char_bob],
                attending_chars=standard_attending,
                staging_overrides=standard_overrides,
                fast_draft_12=False,
                steps=20,
                cfg=6.0,
                base_only_steps=2,
                regional_control_mode="off"
            ),
            "dest_filename": "CondC_Native20_CFG6_BaseOnly2.png",
            "steps": 20, "cfg": 6.0, "base_only_steps": 2, "fast_draft_12": False,
            "regional_mode": "off", "cn_strength": 0.75
        },
        {
            "cond_id": "CondD",
            "name": "Hyper 12s (CFG 6.0, base_only=2, Hyper-SDXL LoRA)",
            "wf_source": os.path.join(WORKFLOWS_DIR, "46_VERIFY_HYPER12_CAUSAL_CONTROL.json"),
            "dest_filename": "CondD_Hyper12_CFG6_BaseOnly2.png",
            "steps": 12, "cfg": 6.0, "base_only_steps": 2, "fast_draft_12": True,
            "regional_mode": "off", "cn_strength": 0.75
        },
        {
            "cond_id": "CondE",
            "name": "Native 20s Base-Only 0 (CFG 7.0, base_only=0, no LoRA)",
            "wf_source": os.path.join(WORKFLOWS_DIR, "44_VERIFY_NATIVE20_BASEONLY_ZERO.json"),
            "dest_filename": "CondE_Native20_CFG7_BaseOnly0.png",
            "steps": 20, "cfg": 7.0, "base_only_steps": 0, "fast_draft_12": False,
            "regional_mode": "off", "cn_strength": 0.75
        },
        {
            "cond_id": "CondF",
            "name": "Regional Control - Shared Global 0.35 (Euler 20s, CFG 7.0, shared_global 0.35)",
            "wf_source": build_phase3i2_workflow(
                wf_filename="CondF_SHARED_GLOBAL_035.json",
                title="Condition F: Shared Global Regional CN 0.35",
                save_prefix="Phase3I2_CondF_SharedGlobal_035",
                characters=[char_alice, char_bob],
                attending_chars=standard_attending,
                staging_overrides=standard_overrides,
                fast_draft_12=False,
                steps=20,
                cfg=7.0,
                base_only_steps=2,
                regional_control_mode="shared_global",
                regional_control_strength=0.35
            ),
            "dest_filename": "CondF_SharedGlobal_035.png",
            "steps": 20, "cfg": 7.0, "base_only_steps": 2, "fast_draft_12": False,
            "regional_mode": "shared_global", "cn_strength": 0.35
        },
        {
            "cond_id": "CondG",
            "name": "Regional Control - Per-Region Hint 0.35 (Euler 20s, CFG 7.0, per_region_hint 0.35)",
            "wf_source": os.path.join(WORKFLOWS_DIR, "47_VERIFY_PER_REGION_HINT_ATTENUATED.json"),
            "dest_filename": "CondG_PerRegionHint_035.png",
            "steps": 20, "cfg": 7.0, "base_only_steps": 2, "fast_draft_12": False,
            "regional_mode": "per_region_hint", "cn_strength": 0.35
        }
    ]

    suite_results = []
    overall_start = time.time()

    try:
        for c in conditions:
            dest_path = os.path.join(OUTPUT_DIR, c["dest_filename"])
            # Check if previous valid run succeeded
            if os.path.exists(dest_path) and os.path.getsize(dest_path) > 1000:
                prev_res = None
                if os.path.exists(results_file):
                    try:
                        with open(results_file, "r", encoding="utf-8") as rf:
                            prev_data = json.load(rf)
                            for r in prev_data.get("results", []):
                                if r.get("cond_id") == c["cond_id"] and r.get("runtime_status") == "PASS":
                                    prev_res = r
                                    break
                    except Exception:
                        pass
                if prev_res:
                    print(f"\n[{c['cond_id']}] {c['name']} already completed ({prev_res['elapsed_sec']}s). Reusing cached output.")
                    suite_results.append(prev_res)
                    continue

            print(f"\n[{c['cond_id']}] Running: {c['name']}...")
            vram_start = get_gpu_vram_mb()
            prompt_graph = graph_to_api_prompt(c["wf_source"], object_info)

            t0 = time.time()
            try:
                queue_resp = comfy_runtime_helper.queue_prompt(prompt_graph)
                prompt_id = queue_resp.get("prompt_id")
                node_errors = queue_resp.get("node_errors", {})
                if node_errors:
                    raise RuntimeError(f"Zero-touch validation error in {c['name']}: {node_errors}")

                print(f"  [QUEUED] Prompt ID: {prompt_id} (0 validation errors)")
                outputs = comfy_runtime_helper.wait_for_prompt(prompt_id, timeout=300)
                elapsed = time.time() - t0
                vram_peak = max(vram_start, get_gpu_vram_mb())

                # Resolve generated image file path from SaveImage node 18
                img_path = comfy_runtime_helper.get_image_file_path(outputs, "18")
                if not img_path or not os.path.exists(img_path):
                    for nid, out_dict in outputs.items():
                        if "images" in out_dict and out_dict["images"]:
                            fallback_path = comfy_runtime_helper.get_image_file_path(outputs, nid)
                            if fallback_path and os.path.exists(fallback_path):
                                img_path = fallback_path
                                break

                if img_path and os.path.exists(img_path):
                    dest_path = os.path.join(OUTPUT_DIR, c["dest_filename"])
                    shutil.copyfile(img_path, dest_path)
                    print(f"  [PASS] Completed in {elapsed:.2f}s | VRAM: {vram_peak} MB. Image: {dest_path}")

                    suite_results.append({
                        "cond_id": c["cond_id"],
                        "name": c["name"],
                        "runtime_status": "PASS",
                        "elapsed_sec": round(elapsed, 2),
                        "vram_mb": vram_peak,
                        "steps": c["steps"],
                        "cfg": c["cfg"],
                        "base_only_steps": c["base_only_steps"],
                        "fast_draft_12": c["fast_draft_12"],
                        "regional_mode": c["regional_mode"],
                        "output_image": dest_path
                    })
                else:
                    raise RuntimeError(f"No output image produced for {c['name']}")

            except Exception as e:
                elapsed = time.time() - t0
                print(f"  [FAIL] Failed after {elapsed:.2f}s: {e}")
                suite_results.append({
                    "cond_id": c["cond_id"],
                    "name": c["name"],
                    "runtime_status": "FAIL",
                    "elapsed_sec": round(elapsed, 2),
                    "error": str(e)
                })
    finally:
        comfy_runtime_helper.stop_server()

    total_time = time.time() - overall_start
    print("\n" + "=" * 80)
    print(f"Phase 3I.2 Causal Ablation Suite Completed in {total_time:.2f}s")
    all_passed = all(r.get("runtime_status") == "PASS" for r in suite_results)
    print(f"Overall Runtime Result: {'ALL PASS' if all_passed else 'FAIL'}")
    print("=" * 80)

    summary_data = {
        "suite": "Phase 3I.2 Causal Ablation Suite",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_elapsed_sec": round(total_time, 2),
        "all_passed": all_passed,
        "results": suite_results
    }

    with open(results_file, "w", encoding="utf-8") as f:
        json.dump(summary_data, f, indent=2, ensure_ascii=False)
    print(f"Results recorded to: {results_file}")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(run_ablation_suite())
