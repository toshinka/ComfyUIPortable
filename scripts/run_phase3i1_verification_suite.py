"""
Phase 3I.1: Canonical Verification Suite Runner
===============================================
Executes:
1. WF40: ControlNet Authoring Reference Pair (Alice Left, Bob Right, Euler 20s, CN 0.75/0.80, Base-only CN)
2. WF41: ControlNet Strength Sanity (CN 0.50 / End 0.60 vs 0.75 / 0.80)
3. WF42: Regional ControlNet Propagation A/B (propagate_controlnet_to_regions: True)
4. WF43: Browser Staging Interaction Causality (Alice Center-Right Dragged, Fast Draft 12)

Guarantees:
- Zero validation errors
- Strict timeout breaker (240s)
- Runtime status separation
- Results recorded to output/Tegaki/Phase3I1/phase3i1_verification_results.json
"""

import os
import sys
import json
import time
import shutil
import urllib.request
from typing import Dict, Any, List

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CUSTOM_NODES_DIR = os.path.join(ROOT_DIR, "custom_nodes_custom")
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
if CUSTOM_NODES_DIR not in sys.path:
    sys.path.insert(0, CUSTOM_NODES_DIR)

from scripts import comfy_runtime_helper

WORKFLOWS_DIR = os.path.join(ROOT_DIR, "workflows")
OUTPUT_DIR = os.path.join(ROOT_DIR, "output", "Tegaki", "Phase3I1", "canonical")


def fetch_all_object_info() -> Dict[str, Any]:
    url = f"{comfy_runtime_helper.COMFY_URL}/object_info"
    req = urllib.request.Request(url, headers={"User-Agent": "Phase3I1Suite/1.0"})
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


def run_test_suite():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    results_file = os.path.join(ROOT_DIR, "output", "Tegaki", "Phase3I1", "phase3i1_verification_results.json")

    print("\n" + "=" * 80)
    print("Phase 3I.1: ControlNet Verification Suite (WF40-43)")
    print("Target: RTX 4070 12GB | AnyTest v4 | Zero-Touch Execution")
    print("=" * 80)

    comfy_runtime_helper.ensure_server()
    object_info = fetch_all_object_info()

    test_cases = [
        {
            "id": "WF40",
            "name": "40_VERIFY_CN_AUTHORING_REFERENCE_PAIR",
            "file": "40_VERIFY_CN_AUTHORING_REFERENCE_PAIR.json",
            "expected_prefix": "WF40_Phase3I1_Authoring_40_ReferencePair_AliceLeft_BobRight"
        },
        {
            "id": "WF41",
            "name": "41_VERIFY_CN_STRENGTH_SANITY",
            "file": "41_VERIFY_CN_STRENGTH_SANITY.json",
            "expected_prefix": "WF41_Phase3I1_CN_Strength_Sanity_50_60"
        },
        {
            "id": "WF42",
            "name": "42_VERIFY_REGIONAL_CN_PROPAGATION_AB",
            "file": "42_VERIFY_REGIONAL_CN_PROPAGATION_AB.json",
            "expected_prefix": "WF42_Phase3I1_Regional_CN_Propagation_AB"
        },
        {
            "id": "WF43",
            "name": "43_VERIFY_BROWSER_STAGING_CAUSALITY",
            "file": "43_VERIFY_BROWSER_STAGING_CAUSALITY.json",
            "expected_prefix": "WF43_Phase3I1_Browser_Staging_Causality_AliceRight"
        }
    ]

    suite_results = []
    overall_start = time.time()

    try:
        for tc in test_cases:
            print(f"\n[{tc['id']}] Running: {tc['name']}...")
            wf_path = os.path.join(WORKFLOWS_DIR, tc["file"])
            prompt_graph = graph_to_api_prompt(wf_path, object_info)

            t0 = time.time()
            try:
                queue_resp = comfy_runtime_helper.queue_prompt(prompt_graph)
                prompt_id = queue_resp.get("prompt_id")
                node_errors = queue_resp.get("node_errors", {})
                if node_errors:
                    raise RuntimeError(f"Zero-touch validation error in {tc['name']}: {node_errors}")

                print(f"  [QUEUED] Prompt ID: {prompt_id} (0 validation errors)")
                outputs = comfy_runtime_helper.wait_for_prompt(prompt_id, timeout=240)
                elapsed = time.time() - t0

                # Resolve generated image file path from SaveImage node 18
                img_path = comfy_runtime_helper.get_image_file_path(outputs, "18")
                if not img_path or not os.path.exists(img_path):
                    # Fallback: scan any node in outputs with images
                    for nid, out_dict in outputs.items():
                        if "images" in out_dict and out_dict["images"]:
                            fallback_path = comfy_runtime_helper.get_image_file_path(outputs, nid)
                            if fallback_path and os.path.exists(fallback_path):
                                img_path = fallback_path
                                break

                if img_path and os.path.exists(img_path):
                    dest_fn = f"{tc['id']}_{os.path.basename(img_path)}"
                    dest_path = os.path.join(OUTPUT_DIR, dest_fn)
                    shutil.copyfile(img_path, dest_path)
                    print(f"  [PASS] Completed in {elapsed:.2f}s. Image saved: {dest_path}")

                    suite_results.append({
                        "id": tc["id"],
                        "name": tc["name"],
                        "runtime_status": "PASS",
                        "elapsed_sec": round(elapsed, 2),
                        "output_image": dest_path
                    })
                else:
                    raise RuntimeError(f"No output image produced for {tc['name']}")

            except Exception as e:
                elapsed = time.time() - t0
                print(f"  [FAIL] Failed after {elapsed:.2f}s: {e}")
                suite_results.append({
                    "id": tc["id"],
                    "name": tc["name"],
                    "runtime_status": "FAIL",
                    "elapsed_sec": round(elapsed, 2),
                    "error": str(e)
                })
    finally:
        comfy_runtime_helper.stop_server()

    total_time = time.time() - overall_start
    print("\n" + "=" * 80)
    print(f"Phase 3I.1 Verification Suite Completed in {total_time:.2f}s")
    all_passed = all(r.get("runtime_status") == "PASS" for r in suite_results)
    print(f"Overall Runtime Result: {'ALL PASS' if all_passed else 'FAIL'}")
    print("=" * 80)

    summary_data = {
        "suite": "Phase 3I.1 Canonical ControlNet Suite",
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
    sys.exit(run_test_suite())
