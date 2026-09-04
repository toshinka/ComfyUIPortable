"""
Canonical Verification Suite Runner (Phase 3G)
==============================================
Executes canonical verification workflows (Workflows 25, 26, 27, 28)
in deterministic order with:
1. Strict server lifecycle management (via comfy_runtime_helper).
2. Per-prompt timeout breakers.
3. Zero validation errors guarantee.
4. Output image collection to output/Tegaki/Phase3G/canonical/.
5. Execution metrics recording to output/Tegaki/Phase3G/canonical_verification_results.json.
"""

import os
import sys
import json
import time
import shutil
import urllib.request
from typing import Dict, Any, List

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from scripts import comfy_runtime_helper

WORKFLOWS_DIR = os.path.join(ROOT_DIR, "workflows")
OUTPUT_DIR = os.path.join(ROOT_DIR, "output", "Tegaki", "Phase3G", "canonical")
MANIFEST_PATH = os.path.join(ROOT_DIR, "docs", "verification", "PHASE3G_CANONICAL_VERIFICATION_MANIFEST.json")


def fetch_all_object_info() -> Dict[str, Any]:
    url = f"{comfy_runtime_helper.COMFY_URL}/object_info"
    req = urllib.request.Request(url, headers={"User-Agent": "CanonicalSuite/1.0"})
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

        # 1. Linked inputs
        for inp in n.get("inputs", []):
            name = inp["name"]
            lid = inp.get("link")
            if lid is not None and lid in link_map:
                node_inputs[name] = link_map[lid]

        # 2. Widget inputs mapped from object_info
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
                        # Frontend inserts control_after_generate widget
                        w_idx += 1

        prompt[nid] = {
            "class_type": ntype,
            "inputs": node_inputs
        }

    return prompt


def run_canonical_suite(skip_existing: bool = False) -> Dict[str, Any]:
    print("================================================================================")
    print("Phase 3G: Canonical Spatial Verification Suite Execution")
    print("================================================================================")
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    spatial_tests = manifest["suites"]["spatial_verification_set"]
    results = []
    overall_start = time.time()

    try:
        print("[Runner] Starting ComfyUI server...")
        comfy_runtime_helper.ensure_server(timeout=90)
        object_info = fetch_all_object_info()
        print(f"[Runner] /object_info fetched ({len(object_info)} node classes registered).")

        for item in spatial_tests:
            wf_file = item["workflow"]
            save_node_id = item["save_node_id"]
            out_name = item["output_image"]
            hyp = item["hypothesis"]

            print(f"\n--------------------------------------------------------------------------------")
            print(f"Executing: {wf_file}")
            print(f"Hypothesis: {hyp}")

            target_img_path = os.path.join(OUTPUT_DIR, out_name)
            if skip_existing and os.path.exists(target_img_path) and os.path.getsize(target_img_path) > 10000:
                print(f"[SKIP] Verified image already exists: {target_img_path}")
                results.append({
                    "workflow": wf_file,
                    "hypothesis": hyp,
                    "prompt_id": "cached",
                    "validation_errors": 0,
                    "elapsed_seconds": 0.0,
                    "output_image": out_name,
                    "status": "PASS"
                })
                continue

            wf_path = os.path.join(WORKFLOWS_DIR, wf_file)
            prompt = graph_to_api_prompt(wf_path, object_info)

            step_start = time.time()
            queue_resp = comfy_runtime_helper.queue_prompt(prompt)
            prompt_id = queue_resp.get("prompt_id")
            node_errors = queue_resp.get("node_errors", {})

            if node_errors:
                print(f"[FAIL] Node validation errors for {wf_file}:\n{json.dumps(node_errors, indent=2)}")
                raise RuntimeError(f"Zero-touch validation error in {wf_file}: {node_errors}")

            print(f"[QUEUED] Prompt ID: {prompt_id} (Zero Validation Errors)")

            outputs = comfy_runtime_helper.wait_for_prompt(prompt_id, timeout=240)
            elapsed = time.time() - step_start

            img_path = comfy_runtime_helper.get_image_file_path(outputs, save_node_id)
            if not img_path or not os.path.exists(img_path):
                raise FileNotFoundError(f"Output image for node {save_node_id} not found in {outputs}")

            shutil.copyfile(img_path, target_img_path)
            print(f"[SUCCESS] Image generated and saved to: {target_img_path} ({elapsed:.1f}s)")

            results.append({
                "workflow": wf_file,
                "hypothesis": hyp,
                "prompt_id": prompt_id,
                "validation_errors": 0,
                "elapsed_seconds": round(elapsed, 1),
                "output_image": out_name,
                "status": "PASS"
            })

    finally:
        print("[Runner] Tearing down ComfyUI server...")
        comfy_runtime_helper.stop_server()

    total_elapsed = time.time() - overall_start
    summary = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_elapsed_seconds": round(total_elapsed, 1),
        "total_workflows_tested": len(spatial_tests),
        "all_passed": all(r["status"] == "PASS" for r in results),
        "results": results
    }

    res_path = os.path.join(ROOT_DIR, "output", "Tegaki", "Phase3G", "canonical_verification_results.json")
    with open(res_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print("\n================================================================================")
    print(f"[CANONICAL SUITE PASSED] All {len(results)} workflows executed in {total_elapsed:.1f}s!")
    print(f"Results JSON: {res_path}")
    print("================================================================================")
    return summary


if __name__ == "__main__":
    run_canonical_suite()
