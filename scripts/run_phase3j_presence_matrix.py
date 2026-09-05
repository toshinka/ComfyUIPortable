"""
Phase 3J: Semantic Presence Stabilization & Adaptive Character Guide Suite Runner
=================================================================================
Executes 14 Empirical Conditions:
- Cond01: Legacy Base (courtyard, two students) + Alice L / Bob R (Hyper12, seed 42)
- Cond02: Background-Only Base (empty courtyard, no students) + Alice L / Bob R (Hyper12, seed 42) -> WF48
- Cond03: Alice Left only (Hyper12, seed 42) -> WF49
- Cond04: Alice Right only (Hyper12, seed 42) -> WF50
- Cond05: Bob Left only (Hyper12, seed 42) -> WF51
- Cond06: Bob Right only (Hyper12, seed 42) -> WF52
- Cond07: Bob Left / Alice Right (Hyper12, seed 42, base-only CN)
- Cond08: Region Order: Bob then Alice list order (Hyper12, seed 42)
- Cond09: PRH-v1: Per-Region Hint with bbox outline ON (Bob L / Alice R, seed 42)
- Cond10: PRH-v2: Per-Region Hint with bbox outline OFF (Bob L / Alice R, seed 42) -> WF53
- Cond11: PRH-v2: Per-Region Hint with bbox outline OFF (Alice L / Bob R, seed 42)
- Cond12: Seed Robustness: Seed 43 on WF53 (Bob L / Alice R + PRH v2)
- Cond13: Adaptive Shot Type: Alice Half Body (shot_type=half_body, seed 42)
- Cond14: Adaptive Shot Type: Alice Bust Shot (shot_type=bust, seed 42)

Guarantees:
- Live VRAM and execution timing capture
- Zero validation errors
- Strict timeout breaker (300s per condition)
- Output to output/Tegaki/Phase3J/canonical/
- Results recorded to output/Tegaki/Phase3J/phase3j_presence_matrix.json
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
from scripts.generate_phase3j_workflows import (
    build_phase3j_workflow,
    CANONICAL_BASE_V2,
    LEGACY_BASE_PROMPT,
    PANEL_SCENE_PROMPT
)

WORKFLOWS_DIR = os.path.join(ROOT_DIR, "workflows")
OUTPUT_DIR = os.path.join(ROOT_DIR, "output", "Tegaki", "Phase3J", "canonical")


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
    req = urllib.request.Request(url, headers={"User-Agent": "Phase3JSuite/1.0"})
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


def run_presence_matrix_suite():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    results_dir = os.path.join(ROOT_DIR, "output", "Tegaki", "Phase3J")
    os.makedirs(results_dir, exist_ok=True)
    results_file = os.path.join(results_dir, "phase3j_presence_matrix.json")

    print("\n" + "=" * 80)
    print("Phase 3J: Semantic Presence & Adaptive Character Guide Suite (14 Conditions)")
    print("Target: RTX 4070 12GB | AnyTest v4 | Zero-Touch Execution")
    print("=" * 80)

    comfy_runtime_helper.ensure_server()
    object_info = fetch_all_object_info()

    char_alice = {
        "id": "char_alice",
        "name": "Alice",
        "gender": "female",
        "appearance": "1girl, solo, dark hair, twintails, school uniform, blazer, pleated skirt",
        "negative_prompt": "1boy, male, duplicate, blurry"
    }
    char_bob = {
        "id": "char_bob",
        "name": "Bob",
        "gender": "male",
        "appearance": "1boy, solo, short spiky hair, school uniform, standing",
        "negative_prompt": "1girl, female, duplicate, blurry"
    }

    alice_left = {"x": 0.10, "y": 0.15, "w": 0.35, "h": 0.75, "width": 0.35, "height": 0.75}
    alice_right = {"x": 0.55, "y": 0.15, "w": 0.35, "h": 0.75, "width": 0.35, "height": 0.75}
    bob_left = {"x": 0.10, "y": 0.15, "w": 0.35, "h": 0.75, "width": 0.35, "height": 0.75}
    bob_right = {"x": 0.55, "y": 0.15, "w": 0.35, "h": 0.75, "width": 0.35, "height": 0.75}

    conditions = [
        # Cond 01: Legacy Base (Alice L / Bob R)
        {
            "cond_id": "Cond01",
            "name": "Legacy Base (two students) Alice L / Bob R (Hyper12, seed 42)",
            "wf_source": build_phase3j_workflow(
                wf_filename="temp_cond01_legacy_base.json",
                title="Condition 01: Legacy Base Alice L / Bob R",
                save_prefix="Tegaki/Phase3J/Cond01_LegacyBase_AliceL_BobR",
                characters=[char_alice, char_bob],
                attending_chars=[
                    {"character_id": "char_alice", "acting": "standing calmly on left", "importance": "primary", "area": alice_left},
                    {"character_id": "char_bob", "acting": "standing listening on right", "importance": "secondary", "area": bob_right}
                ],
                staging_overrides={
                    "char_alice": {"area": alice_left, "pose_preset": "standing_neutral"},
                    "char_bob": {"area": bob_right, "pose_preset": "standing_neutral"}
                },
                fast_draft_12=True, steps=12, cfg=6.0, base_only_steps=2,
                base_prompt=LEGACY_BASE_PROMPT, regional_control_mode="off", seed=42
            ),
            "dest_filename": "Cond01_LegacyBase_AliceL_BobR.png",
            "seed": 42, "regional_mode": "off", "base_prompt_type": "legacy",
            "shot_type": "full_body", "include_bbox": True
        },
        # Cond 02: Background-Only Base (Alice L / Bob R) -> WF48
        {
            "cond_id": "Cond02",
            "name": "Background-Only Base Alice L / Bob R (WF48, Hyper12, seed 42)",
            "wf_source": os.path.join(WORKFLOWS_DIR, "48_VERIFY_BASE_BACKGROUND_ONLY_CHARACTER_PRESENCE.json"),
            "dest_filename": "Cond02_BgOnlyBase_AliceL_BobR.png",
            "seed": 42, "regional_mode": "off", "base_prompt_type": "background_only",
            "shot_type": "full_body", "include_bbox": True
        },
        # Cond 03: Alice Left Only -> WF49
        {
            "cond_id": "Cond03",
            "name": "Alice Left Only Hyper12 (WF49, seed 42)",
            "wf_source": os.path.join(WORKFLOWS_DIR, "49_VERIFY_ALICE_LEFT_ONLY_HYPER12.json"),
            "dest_filename": "Cond03_AliceLeft_Hyper12.png",
            "seed": 42, "regional_mode": "off", "base_prompt_type": "background_only",
            "shot_type": "full_body", "include_bbox": True
        },
        # Cond 04: Alice Right Only -> WF50
        {
            "cond_id": "Cond04",
            "name": "Alice Right Only Hyper12 (WF50, seed 42)",
            "wf_source": os.path.join(WORKFLOWS_DIR, "50_VERIFY_ALICE_RIGHT_ONLY_HYPER12.json"),
            "dest_filename": "Cond04_AliceRight_Hyper12.png",
            "seed": 42, "regional_mode": "off", "base_prompt_type": "background_only",
            "shot_type": "full_body", "include_bbox": True
        },
        # Cond 05: Bob Left Only -> WF51
        {
            "cond_id": "Cond05",
            "name": "Bob Left Only Hyper12 (WF51, seed 42)",
            "wf_source": os.path.join(WORKFLOWS_DIR, "51_VERIFY_BOB_LEFT_ONLY_HYPER12.json"),
            "dest_filename": "Cond05_BobLeft_Hyper12.png",
            "seed": 42, "regional_mode": "off", "base_prompt_type": "background_only",
            "shot_type": "full_body", "include_bbox": True
        },
        # Cond 06: Bob Right Only -> WF52
        {
            "cond_id": "Cond06",
            "name": "Bob Right Only Hyper12 (WF52, seed 42)",
            "wf_source": os.path.join(WORKFLOWS_DIR, "52_VERIFY_BOB_RIGHT_ONLY_HYPER12.json"),
            "dest_filename": "Cond06_BobRight_Hyper12.png",
            "seed": 42, "regional_mode": "off", "base_prompt_type": "background_only",
            "shot_type": "full_body", "include_bbox": True
        },
        # Cond 07: Two Character Swap C2: Bob Left / Alice Right (Hyper12, base-only CN)
        {
            "cond_id": "Cond07",
            "name": "Two-Character Swap C2: Bob L / Alice R (Hyper12, seed 42, CN off)",
            "wf_source": build_phase3j_workflow(
                wf_filename="temp_cond07_bob_l_alice_r_cnoff.json",
                title="Condition 07: Bob L / Alice R Hyper12 Base-Only CN",
                save_prefix="Tegaki/Phase3J/Cond07_TwoChar_BobL_AliceR_Hyper12",
                characters=[char_alice, char_bob],
                attending_chars=[
                    {"character_id": "char_bob", "acting": "standing on left", "importance": "secondary", "area": bob_left},
                    {"character_id": "char_alice", "acting": "standing calmly on right", "importance": "primary", "area": alice_right}
                ],
                staging_overrides={
                    "char_bob": {"area": bob_left, "pose_preset": "standing_neutral"},
                    "char_alice": {"area": alice_right, "pose_preset": "standing_neutral"}
                },
                fast_draft_12=True, steps=12, cfg=6.0, base_only_steps=2,
                base_prompt=CANONICAL_BASE_V2, regional_control_mode="off", seed=42
            ),
            "dest_filename": "Cond07_TwoChar_BobL_AliceR_Hyper12.png",
            "seed": 42, "regional_mode": "off", "base_prompt_type": "background_only",
            "shot_type": "full_body", "include_bbox": True
        },
        # Cond 08: Region Order Effect: Bob then Alice in compiler attending list
        {
            "cond_id": "Cond08",
            "name": "Region Order Sanity: Bob then Alice attending order (Hyper12, seed 42)",
            "wf_source": build_phase3j_workflow(
                wf_filename="temp_cond08_bob_then_alice_order.json",
                title="Condition 08: Region Order Bob Then Alice",
                save_prefix="Tegaki/Phase3J/Cond08_RegionOrder_BobFirst_AliceL_BobR",
                characters=[char_bob, char_alice],
                attending_chars=[
                    {"character_id": "char_bob", "acting": "standing listening on right", "importance": "secondary", "area": bob_right},
                    {"character_id": "char_alice", "acting": "standing calmly on left", "importance": "primary", "area": alice_left}
                ],
                staging_overrides={
                    "char_alice": {"area": alice_left, "pose_preset": "standing_neutral"},
                    "char_bob": {"area": bob_right, "pose_preset": "standing_neutral"}
                },
                fast_draft_12=True, steps=12, cfg=6.0, base_only_steps=2,
                base_prompt=CANONICAL_BASE_V2, regional_control_mode="off", seed=42
            ),
            "dest_filename": "Cond08_RegionOrder_BobFirst_AliceL_BobR.png",
            "seed": 42, "regional_mode": "off", "base_prompt_type": "background_only",
            "shot_type": "full_body", "include_bbox": True
        },
        # Cond 09: PRH-v1: Per-Region Hint with bbox outline ON (Bob L / Alice R, seed 42)
        {
            "cond_id": "Cond09",
            "name": "PRH-v1: BBox Outline ON (Bob L / Alice R, Hyper12, seed 42)",
            "wf_source": build_phase3j_workflow(
                wf_filename="temp_cond09_prh_v1_bbox_on.json",
                title="Condition 09: PRH v1 BBox ON",
                save_prefix="Tegaki/Phase3J/Cond09_PRH_v1_BBoxON_BobL_AliceR",
                characters=[char_alice, char_bob],
                attending_chars=[
                    {"character_id": "char_bob", "acting": "standing on left", "importance": "secondary", "area": bob_left},
                    {"character_id": "char_alice", "acting": "standing calmly on right", "importance": "primary", "area": alice_right}
                ],
                staging_overrides={
                    "char_bob": {"area": bob_left, "pose_preset": "standing_neutral"},
                    "char_alice": {"area": alice_right, "pose_preset": "standing_neutral"}
                },
                fast_draft_12=True, steps=12, cfg=6.0, base_only_steps=2,
                base_prompt=CANONICAL_BASE_V2,
                include_character_bbox_outline=True,
                regional_control_mode="per_region_hint",
                regional_control_strength=0.35,
                regional_control_end_percent=0.60,
                seed=42
            ),
            "dest_filename": "Cond09_PRH_v1_BBoxON_BobL_AliceR.png",
            "seed": 42, "regional_mode": "per_region_hint", "base_prompt_type": "background_only",
            "shot_type": "full_body", "include_bbox": True
        },
        # Cond 10: PRH-v2: Per-Region Hint with bbox outline OFF (Bob L / Alice R, seed 42) -> WF53
        {
            "cond_id": "Cond10",
            "name": "PRH-v2: Clean Hint No-Box Bob L / Alice R (WF53, Hyper12, seed 42)",
            "wf_source": os.path.join(WORKFLOWS_DIR, "53_VERIFY_HYPER12_PER_REGION_HINT_SWAP.json"),
            "dest_filename": "Cond10_PRH_v2_BBoxOFF_BobL_AliceR.png",
            "seed": 42, "regional_mode": "per_region_hint", "base_prompt_type": "background_only",
            "shot_type": "full_body", "include_bbox": False
        },
        # Cond 11: PRH-v2: Per-Region Hint with bbox outline OFF (Alice L / Bob R, seed 42)
        {
            "cond_id": "Cond11",
            "name": "PRH-v2: Clean Hint No-Box Alice L / Bob R (Hyper12, seed 42)",
            "wf_source": build_phase3j_workflow(
                wf_filename="temp_cond11_prh_v2_alice_l_bob_r.json",
                title="Condition 11: PRH v2 Alice L / Bob R",
                save_prefix="Tegaki/Phase3J/Cond11_PRH_v2_BBoxOFF_AliceL_BobR",
                characters=[char_alice, char_bob],
                attending_chars=[
                    {"character_id": "char_alice", "acting": "standing calmly on left", "importance": "primary", "area": alice_left},
                    {"character_id": "char_bob", "acting": "standing listening on right", "importance": "secondary", "area": bob_right}
                ],
                staging_overrides={
                    "char_alice": {"area": alice_left, "pose_preset": "standing_neutral"},
                    "char_bob": {"area": bob_right, "pose_preset": "standing_neutral"}
                },
                fast_draft_12=True, steps=12, cfg=6.0, base_only_steps=2,
                base_prompt=CANONICAL_BASE_V2,
                include_character_bbox_outline=False,
                regional_control_mode="per_region_hint",
                regional_control_strength=0.35,
                regional_control_end_percent=0.60,
                seed=42
            ),
            "dest_filename": "Cond11_PRH_v2_BBoxOFF_AliceL_BobR.png",
            "seed": 42, "regional_mode": "per_region_hint", "base_prompt_type": "background_only",
            "shot_type": "full_body", "include_bbox": False
        },
        # Cond 12: Seed Robustness (Seed 43) on WF53 (Bob L / Alice R + PRH v2)
        {
            "cond_id": "Cond12",
            "name": "Seed Robustness: Seed 43 Bob L / Alice R PRH v2 (Hyper12, seed 43)",
            "wf_source": build_phase3j_workflow(
                wf_filename="temp_cond12_seed43_wf53.json",
                title="Condition 12: Seed 43 WF53",
                save_prefix="Tegaki/Phase3J/Cond12_SeedRobustness_Seed43_WF53",
                characters=[char_alice, char_bob],
                attending_chars=[
                    {"character_id": "char_bob", "acting": "standing on left", "importance": "secondary", "area": bob_left},
                    {"character_id": "char_alice", "acting": "standing calmly on right", "importance": "primary", "area": alice_right}
                ],
                staging_overrides={
                    "char_bob": {"area": bob_left, "pose_preset": "standing_neutral"},
                    "char_alice": {"area": alice_right, "pose_preset": "standing_neutral"}
                },
                fast_draft_12=True, steps=12, cfg=6.0, base_only_steps=2,
                base_prompt=CANONICAL_BASE_V2,
                include_character_bbox_outline=False,
                regional_control_mode="per_region_hint",
                regional_control_strength=0.35,
                regional_control_end_percent=0.60,
                seed=43
            ),
            "dest_filename": "Cond12_SeedRobustness_Seed43_WF53.png",
            "seed": 43, "regional_mode": "per_region_hint", "base_prompt_type": "background_only",
            "shot_type": "full_body", "include_bbox": False
        },
        # Cond 13: Adaptive Shot Type: Alice Half Body (shot_type=half_body, seed 42)
        {
            "cond_id": "Cond13",
            "name": "Adaptive Shot Type: Alice Half Body (Hyper12, seed 42, PRH v2)",
            "wf_source": build_phase3j_workflow(
                wf_filename="temp_cond13_alice_half_body.json",
                title="Condition 13: Alice Half Body",
                save_prefix="Tegaki/Phase3J/Cond13_ShotType_HalfBody_Alice",
                characters=[char_alice],
                attending_chars=[
                    {"character_id": "char_alice", "acting": "standing calmly on left, upper body", "importance": "primary", "area": alice_left, "shot_type": "half_body"}
                ],
                staging_overrides={
                    "char_alice": {"area": alice_left, "shot_type": "half_body", "pose_preset": "standing_neutral"}
                },
                fast_draft_12=True, steps=12, cfg=6.0, base_only_steps=2,
                base_prompt=CANONICAL_BASE_V2,
                include_character_bbox_outline=False,
                regional_control_mode="per_region_hint",
                regional_control_strength=0.35,
                regional_control_end_percent=0.60,
                seed=42
            ),
            "dest_filename": "Cond13_ShotType_HalfBody_Alice.png",
            "seed": 42, "regional_mode": "per_region_hint", "base_prompt_type": "background_only",
            "shot_type": "half_body", "include_bbox": False
        },
        # Cond 14: Adaptive Shot Type: Alice Bust Shot (shot_type=bust, seed 42)
        {
            "cond_id": "Cond14",
            "name": "Adaptive Shot Type: Alice Bust Shot (Hyper12, seed 42, PRH v2)",
            "wf_source": build_phase3j_workflow(
                wf_filename="temp_cond14_alice_bust_shot.json",
                title="Condition 14: Alice Bust Shot",
                save_prefix="Tegaki/Phase3J/Cond14_ShotType_Bust_Alice",
                characters=[char_alice],
                attending_chars=[
                    {"character_id": "char_alice", "acting": "standing calmly on left, close portrait", "importance": "primary", "area": alice_left, "shot_type": "bust"}
                ],
                staging_overrides={
                    "char_alice": {"area": alice_left, "shot_type": "bust", "pose_preset": "standing_neutral"}
                },
                fast_draft_12=True, steps=12, cfg=6.0, base_only_steps=2,
                base_prompt=CANONICAL_BASE_V2,
                include_character_bbox_outline=False,
                regional_control_mode="per_region_hint",
                regional_control_strength=0.35,
                regional_control_end_percent=0.60,
                seed=42
            ),
            "dest_filename": "Cond14_ShotType_Bust_Alice.png",
            "seed": 42, "regional_mode": "per_region_hint", "base_prompt_type": "background_only",
            "shot_type": "bust", "include_bbox": False
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
                    print(f"\n[{c['cond_id']}] {c['name']} already completed ({prev_res.get('elapsed_sec', 0)}s). Reusing cached output.")
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
                        "seed": c["seed"],
                        "regional_mode": c["regional_mode"],
                        "base_prompt_type": c["base_prompt_type"],
                        "shot_type": c["shot_type"],
                        "include_bbox": c["include_bbox"],
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
                    "seed": c["seed"],
                    "error": str(e)
                })
    finally:
        comfy_runtime_helper.stop_server()

    total_time = time.time() - overall_start
    print("\n" + "=" * 80)
    print(f"Phase 3J Presence Matrix Suite Completed in {total_time:.2f}s")
    all_passed = all(r.get("runtime_status") == "PASS" for r in suite_results)
    print(f"Overall Runtime Result: {'ALL PASS' if all_passed else 'FAIL'}")
    print("=" * 80)

    summary_data = {
        "suite": "Phase 3J Semantic Presence & Adaptive Character Guide Suite",
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
    sys.exit(run_presence_matrix_suite())
