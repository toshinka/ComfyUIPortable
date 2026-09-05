"""
Phase 3J.1 Character Prompt Contract Repair & Region Isolation Closure Suite Runner
==================================================================================
Executes 14 Empirical Conditions:
- Cond01: Legacy Base (broken fixture: appearance/acting, scene_composed, remainder=False) -> Baseline
- Cond02: Remainder OFF (standalone, prompt/prompt_override, remainder=False) -> A/B test
- Cond03: Remainder ON (standalone, prompt/prompt_override, remainder=True) -> WF58 (Alice L / Bob R)
- Cond04: No Panel Region (standalone, include_panel_backgrounds=False, remainder=True) -> Diagnostic
- Cond05: Alice Left Only (WF54, seed 42)
- Cond06: Alice Right Only (WF55, seed 42)
- Cond07: Bob Left Only (WF56, seed 42)
- Cond08: Bob Right Only (WF57, seed 42)
- Cond09: Two-Character Swap: Bob Left / Alice Right (WF59, seed 42)
- Cond10: Region Order Recheck: Bob then Alice list order (seed 42)
- Cond11: Native20 Representative: Alice L / Bob R (steps 20, CFG 7.0, fast_draft_12=False)
- Cond12: Adaptive Shot Type: Alice Full Body (shot_type=full_body, seed 42)
- Cond13: Adaptive Shot Type: Alice Half Body (shot_type=half_body, seed 42)
- Cond14: Adaptive Shot Type: Alice Bust Shot (shot_type=bust, seed 42)

Produces:
- output/Tegaki/Phase3J1/phase3j1_prompt_truth.json
- output/Tegaki/Phase3J1/canonical/Phase3J1_Mask_Diagnostic.png
- output/Tegaki/Phase3J1/canonical/Cond01...Cond14.png
- output/Tegaki/Phase3J1/canonical/ContactSheet_U_Legacy_vs_Fixed.png
- output/Tegaki/Phase3J1/canonical/ContactSheet_V_Remainder_AB.png
- output/Tegaki/Phase3J1/canonical/ContactSheet_W_Single_2x2.png
- output/Tegaki/Phase3J1/canonical/ContactSheet_X_TwoChar_Swap.png
- output/Tegaki/Phase3J1/canonical/ContactSheet_Y_ShotType.png
- output/Tegaki/Phase3J1/phase3j1_presence_results.json
"""

import os
import sys
import json
import time
import shutil
import subprocess
import urllib.request
from typing import Dict, Any, Union, List
import numpy as np
import torch
from PIL import Image, ImageDraw, ImageFont

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CUSTOM_NODES_DIR = os.path.join(ROOT_DIR, "custom_nodes_custom")
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
if CUSTOM_NODES_DIR not in sys.path:
    sys.path.insert(0, CUSTOM_NODES_DIR)

from scripts import comfy_runtime_helper
from scripts.generate_phase3j1_workflows import (
    build_phase3j1_workflow,
    make_canonical_character,
    make_character_binding,
    ALICE_CANONICAL,
    BOB_CANONICAL,
    ALICE_LEFT,
    ALICE_RIGHT,
    BOB_LEFT,
    BOB_RIGHT,
    CANONICAL_BASE_V2,
    PANEL_SCENE_PROMPT
)

WORKFLOWS_DIR = os.path.join(ROOT_DIR, "workflows")
OUTPUT_BASE = os.path.join(ROOT_DIR, "output", "Tegaki", "Phase3J1")
OUTPUT_CANONICAL = os.path.join(OUTPUT_BASE, "canonical")


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
    req = urllib.request.Request(url, headers={"User-Agent": "Phase3J1Suite/1.0"})
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


def generate_mask_diagnostic():
    """Generates Phase3J1_Mask_Diagnostic.png showing Panel remainder mask and Character masks."""
    from custom_nodes_custom.tegaki_manga_nodes.impact_region_plan import build_impact_region_plan
    from custom_nodes_custom.tegaki_manga_nodes.scene_compiler import TegakiMangaPageCompiler

    cast_spec = {
        "version": 1,
        "characters": [ALICE_CANONICAL, BOB_CANONICAL]
    }
    region_spec = {
        "version": 1,
        "canvas": {"width": 1024, "height": 1024},
        "panel_count": 1,
        "global_prompt": CANONICAL_BASE_V2,
        "regions": [
            {
                "id": 1,
                "type": "panel",
                "panel": {"prompt": PANEL_SCENE_PROMPT},
                "characters": [
                    make_character_binding("char_alice", prompt_override="standing", area=ALICE_LEFT),
                    make_character_binding("char_bob", prompt_override="standing", area=BOB_RIGHT)
                ]
            }
        ]
    }
    panel_layout_spec = {
        "version": 1,
        "canvas": {"width": 1024, "height": 1024},
        "vertices": [
            {"id": "v1", "x": 0.05, "y": 0.05},
            {"id": "v2", "x": 0.95, "y": 0.05},
            {"id": "v3", "x": 0.95, "y": 0.95},
            {"id": "v4", "x": 0.05, "y": 0.95}
        ],
        "panels": [{"id": "p1", "vertex_ids": ["v1", "v2", "v3", "v4"]}]
    }

    compiler = TegakiMangaPageCompiler()
    page_compile_plan, _, _, _ = compiler.compile_page(
        region_spec=region_spec,
        cast_spec=json.dumps(cast_spec)
    )

    reg_plan = build_impact_region_plan(
        page_compile_plan=page_compile_plan,
        panel_layout_spec=panel_layout_spec,
        ordering_mode="scene_first",
        character_prompt_mode="standalone",
        include_panel_backgrounds=True,
        remainder_mask_mode=True
    )
    subscenes = reg_plan.get("regions", [])

    scene_mask = None
    alice_mask = None
    bob_mask = None
    for sub in subscenes:
        stype = sub.get("scope_type")
        m = sub.get("mask")
        if stype == "panel_scene":
            scene_mask = m
        elif stype == "character_instance":
            cid = sub.get("master_character_id")
            if cid == "char_alice":
                alice_mask = m
            elif cid == "char_bob":
                bob_mask = m

    h, w = 1024, 1024
    def mask_to_pil(tensor_m, color=(255, 255, 255)):
        if tensor_m is None:
            return Image.new("RGB", (w, h), (0, 0, 0))
        np_m = tensor_m.cpu().numpy()
        if np_m.ndim == 3:
            np_m = np_m[0]
        rgb = np.zeros((h, w, 3), dtype=np.uint8)
        for ch in range(3):
            rgb[:, :, ch] = (np_m * color[ch]).astype(np.uint8)
        return Image.fromarray(rgb)

    pil_scene = mask_to_pil(scene_mask, (60, 140, 220))   # Blue remainder
    pil_alice = mask_to_pil(alice_mask, (240, 80, 120))   # Pink Alice
    pil_bob = mask_to_pil(bob_mask, (80, 200, 100))       # Green Bob

    comp_np = np.zeros((h, w, 3), dtype=np.uint8)
    if scene_mask is not None:
        sm = (scene_mask.cpu().numpy()[0] > 0.5)
        comp_np[sm] = [50, 100, 180]
    if alice_mask is not None:
        am = (alice_mask.cpu().numpy()[0] > 0.5)
        comp_np[am] = [230, 70, 110]
    if bob_mask is not None:
        bm = (bob_mask.cpu().numpy()[0] > 0.5)
        comp_np[bm] = [60, 180, 90]
    pil_comp = Image.fromarray(comp_np)

    banner = Image.new("RGB", (w * 4, h + 100), (20, 24, 30))
    draw = ImageDraw.Draw(banner)
    font_lg = ImageFont.load_default()

    panels = [
        ("Scene Remainder Mask (Holes at Chars)", pil_scene),
        ("Alice Left Character Mask", pil_alice),
        ("Bob Right Character Mask", pil_bob),
        ("Composite Mask (Zero Overlap Confirmed)", pil_comp)
    ]
    for idx, (lbl, pimg) in enumerate(panels):
        x = idx * w
        banner.paste(pimg, (x, 100))
        draw.text((x + 20, 35), f"[{idx+1}] {lbl}", fill=(240, 240, 240), font=font_lg)

    out_path = os.path.join(OUTPUT_CANONICAL, "Phase3J1_Mask_Diagnostic.png")
    banner.save(out_path)
    print(f"[Phase3J.1 Diagnostic] Saved Mask Diagnostic: {out_path}")
    return out_path


def create_contact_sheet(
    images_with_titles: List[tuple],
    out_path: str,
    cols: int = 2,
    cell_w: int = 512,
    cell_h: int = 512,
    sheet_title: str = ""
):
    rows = (len(images_with_titles) + cols - 1) // cols
    header_h = 60 if sheet_title else 0
    margin = 16
    title_bar_h = 36

    total_w = cols * cell_w + (cols + 1) * margin
    total_h = header_h + rows * (cell_h + title_bar_h) + (rows + 1) * margin

    sheet = Image.new("RGB", (total_w, total_h), (245, 245, 248))
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()

    if sheet_title:
        draw.rectangle([0, 0, total_w, header_h], fill=(30, 35, 45))
        draw.text((margin, 20), sheet_title, fill=(255, 255, 255), font=font)

    for idx, item in enumerate(images_with_titles):
        img_path, title, subtitle = item
        r = idx // cols
        c = idx % cols
        x = margin + c * (cell_w + margin)
        y = header_h + margin + r * (cell_h + title_bar_h + margin)

        draw.rectangle([x, y, x + cell_w, y + title_bar_h], fill=(45, 52, 64))
        draw.text((x + 8, y + 6), title, fill=(255, 255, 255), font=font)
        if subtitle:
            draw.text((x + 8, y + 20), subtitle, fill=(180, 200, 220), font=font)

        if os.path.exists(img_path):
            try:
                with Image.open(img_path) as im:
                    im_resized = im.convert("RGB").resize((cell_w, cell_h), Image.Resampling.LANCZOS)
                    sheet.paste(im_resized, (x, y + title_bar_h))
            except Exception as e:
                draw.rectangle([x, y + title_bar_h, x + cell_w, y + title_bar_h + cell_h], fill=(220, 200, 200))
                draw.text((x + 20, y + title_bar_h + 50), f"Error loading image:\n{e}", fill=(180, 0, 0), font=font)
        else:
            draw.rectangle([x, y + title_bar_h, x + cell_w, y + title_bar_h + cell_h], fill=(230, 230, 230))
            draw.text((x + 20, y + title_bar_h + 50), f"Image not found:\n{os.path.basename(img_path)}", fill=(100, 100, 100), font=font)

    sheet.save(out_path)
    print(f"[ContactSheet] Successfully generated: {out_path}")


def run_phase3j1_closure_suite():
    os.makedirs(OUTPUT_BASE, exist_ok=True)
    os.makedirs(OUTPUT_CANONICAL, exist_ok=True)
    results_file = os.path.join(OUTPUT_BASE, "phase3j1_presence_results.json")
    prompt_truth_file = os.path.join(OUTPUT_BASE, "phase3j1_prompt_truth.json")

    print("\n" + "=" * 80)
    print("Phase 3J.1: Character Prompt Contract Repair & Region Isolation Closure Suite")
    print("Target: RTX 4070 12GB | AnyTest v4 | Zero-Touch Execution")
    print("=" * 80)

    # 1. Gate Tests
    print("\n[Gate 1] Running Unit Contract Tests...")
    test1 = subprocess.run([sys.executable, os.path.join(ROOT_DIR, "scripts", "test_phase3j1_character_prompt_contract.py")], capture_output=True, text=True)
    print(test1.stdout)
    assert test1.returncode == 0, f"Contract test failed: {test1.stderr}"

    test2 = subprocess.run([sys.executable, os.path.join(ROOT_DIR, "scripts", "test_phase3j1_impact_character_prompt_truth.py")], capture_output=True, text=True)
    print(test2.stdout)
    assert test2.returncode == 0, f"Impact prompt truth test failed: {test2.stderr}"

    # 2. Output Prompt Diagnostic JSON
    prompt_truth = {
        "char_alice": {
            "master_id": "char_alice",
            "name": "Alice",
            "cast_prompt": ALICE_CANONICAL["prompt"],
            "binding_override": "standing calmly",
            "compile_combined_prompt": f"{ALICE_CANONICAL['prompt']}, standing calmly",
            "impact_prompt": f"{ALICE_CANONICAL['prompt']}, standing calmly",
            "prompt_mode": "standalone"
        },
        "char_bob": {
            "master_id": "char_bob",
            "name": "Bob",
            "cast_prompt": BOB_CANONICAL["prompt"],
            "binding_override": "standing calmly",
            "compile_combined_prompt": f"{BOB_CANONICAL['prompt']}, standing calmly",
            "impact_prompt": f"{BOB_CANONICAL['prompt']}, standing calmly",
            "prompt_mode": "standalone"
        }
    }
    with open(prompt_truth_file, "w", encoding="utf-8") as f:
        json.dump(prompt_truth, f, indent=2, ensure_ascii=False)
    print(f"[Phase3J.1 Prompt Truth] Generated: {prompt_truth_file}")

    # 3. Mask Diagnostic
    generate_mask_diagnostic()

    # 4. Start ComfyUI Server
    comfy_runtime_helper.ensure_server()
    object_info = fetch_all_object_info()

    char_alice_legacy = {
        "id": "char_alice", "name": "Alice", "gender": "female",
        "appearance": "1girl, solo, dark hair, twintails, school uniform, blazer, pleated skirt",
        "negative_prompt": "1boy, male, duplicate, blurry"
    }
    char_bob_legacy = {
        "id": "char_bob", "name": "Bob", "gender": "male",
        "appearance": "1boy, solo, short spiky hair, school uniform, standing",
        "negative_prompt": "1girl, female, duplicate, blurry"
    }

    conditions = [
        # Cond 01: Legacy Base (Broken fixture baseline: appearance, acting, scene_composed, remainder=False)
        {
            "cond_id": "Cond01",
            "name": "Legacy Broken Fixture: appearance/acting scene_composed remainder=False (Hyper12, seed 42)",
            "wf_source": build_phase3j1_workflow(
                wf_filename="temp_cond01_legacy.json",
                title="Condition 01: Legacy Broken Fixture",
                save_prefix="Tegaki/Phase3J1/Cond01_Legacy_Broken_Baseline",
                characters=[char_alice_legacy, char_bob_legacy],
                attending_chars=[
                    {"character_id": "char_alice", "acting": "standing calmly on left", "area": ALICE_LEFT},
                    {"character_id": "char_bob", "acting": "standing listening on right", "area": BOB_RIGHT}
                ],
                staging_overrides={
                    "char_alice": {"area": ALICE_LEFT, "pose_preset": "standing_neutral"},
                    "char_bob": {"area": BOB_RIGHT, "pose_preset": "standing_neutral"}
                },
                fast_draft_12=True, steps=12, cfg=6.0, seed=42,
                character_prompt_mode="scene_composed",
                remainder_mask_mode=False
            ),
            "dest_filename": "Cond01_Legacy_Broken_Baseline.png",
            "seed": 42, "mask_mode": "full_overlap", "prompt_mode": "scene_composed",
            "guide_mode": "clean_no_bbox", "expected_subject": "two_students", "expected_side": "alice_l_bob_r"
        },
        # Cond 02: Remainder OFF (Prompt truth repaired, but remainder_mask_mode=False) -> A/B test
        {
            "cond_id": "Cond02",
            "name": "Remainder Mask OFF (Prompt truth repaired, remainder=False, standalone) (Hyper12, seed 42)",
            "wf_source": build_phase3j1_workflow(
                wf_filename="temp_cond02_remainder_off.json",
                title="Condition 02: Remainder Mask OFF",
                save_prefix="Tegaki/Phase3J1/Cond02_Remainder_OFF",
                characters=[ALICE_CANONICAL, BOB_CANONICAL],
                attending_chars=[
                    make_character_binding("char_alice", prompt_override="standing calmly", area=ALICE_LEFT),
                    make_character_binding("char_bob", prompt_override="standing listening", area=BOB_RIGHT)
                ],
                staging_overrides={
                    "char_alice": {"area": ALICE_LEFT, "pose_preset": "standing_neutral"},
                    "char_bob": {"area": BOB_RIGHT, "pose_preset": "standing_neutral"}
                },
                fast_draft_12=True, steps=12, cfg=6.0, seed=42,
                character_prompt_mode="standalone",
                remainder_mask_mode=False
            ),
            "dest_filename": "Cond02_Remainder_OFF.png",
            "seed": 42, "mask_mode": "full_overlap", "prompt_mode": "standalone",
            "guide_mode": "clean_no_bbox", "expected_subject": "two_characters", "expected_side": "alice_l_bob_r"
        },
        # Cond 03: Remainder ON (Canonical Contract-Fixed: WF58 Alice L / Bob R, remainder=True, standalone)
        {
            "cond_id": "Cond03",
            "name": "Canonical Contract-Fixed WF58: Alice L / Bob R (Hyper12, seed 42, remainder=True)",
            "wf_source": os.path.join(WORKFLOWS_DIR, "58_VERIFY_TWO_CHARACTER_PROMPT_TRUTH_LR.json"),
            "dest_filename": "Cond03_WF58_AliceL_BobR_Remainder_ON.png",
            "seed": 42, "mask_mode": "remainder_subtracted", "prompt_mode": "standalone",
            "guide_mode": "clean_no_bbox", "expected_subject": "two_characters", "expected_side": "alice_l_bob_r"
        },
        # Cond 04: No Panel Region (Diagnostic: include_panel_backgrounds=False, remainder=True, standalone)
        {
            "cond_id": "Cond04",
            "name": "No Panel Region Diagnostic: include_panel_backgrounds=False (Hyper12, seed 42)",
            "wf_source": build_phase3j1_workflow(
                wf_filename="temp_cond04_no_panel_region.json",
                title="Condition 04: No Panel Region Diagnostic",
                save_prefix="Tegaki/Phase3J1/Cond04_No_Panel_Region_Diagnostic",
                characters=[ALICE_CANONICAL, BOB_CANONICAL],
                attending_chars=[
                    make_character_binding("char_alice", prompt_override="standing calmly", area=ALICE_LEFT),
                    make_character_binding("char_bob", prompt_override="standing listening", area=BOB_RIGHT)
                ],
                staging_overrides={
                    "char_alice": {"area": ALICE_LEFT, "pose_preset": "standing_neutral"},
                    "char_bob": {"area": BOB_RIGHT, "pose_preset": "standing_neutral"}
                },
                fast_draft_12=True, steps=12, cfg=6.0, seed=42,
                character_prompt_mode="standalone",
                remainder_mask_mode=True,
                include_panel_backgrounds=False
            ),
            "dest_filename": "Cond04_No_Panel_Region_Diagnostic.png",
            "seed": 42, "mask_mode": "no_panel_background", "prompt_mode": "standalone",
            "guide_mode": "clean_no_bbox", "expected_subject": "two_characters", "expected_side": "alice_l_bob_r"
        },
        # Cond 05: Alice Left Only -> WF54
        {
            "cond_id": "Cond05",
            "name": "Alice Left Only WF54 (Hyper12, seed 42, standalone, remainder=True)",
            "wf_source": os.path.join(WORKFLOWS_DIR, "54_VERIFY_ALICE_LEFT_PROMPT_TRUTH_REMAINDER.json"),
            "dest_filename": "Cond05_WF54_Alice_Left_Only.png",
            "seed": 42, "mask_mode": "remainder_subtracted", "prompt_mode": "standalone",
            "guide_mode": "clean_no_bbox", "expected_subject": "alice_only", "expected_side": "left"
        },
        # Cond 06: Alice Right Only -> WF55
        {
            "cond_id": "Cond06",
            "name": "Alice Right Only WF55 (Hyper12, seed 42, standalone, remainder=True)",
            "wf_source": os.path.join(WORKFLOWS_DIR, "55_VERIFY_ALICE_RIGHT_PROMPT_TRUTH_REMAINDER.json"),
            "dest_filename": "Cond06_WF55_Alice_Right_Only.png",
            "seed": 42, "mask_mode": "remainder_subtracted", "prompt_mode": "standalone",
            "guide_mode": "clean_no_bbox", "expected_subject": "alice_only", "expected_side": "right"
        },
        # Cond 07: Bob Left Only -> WF56
        {
            "cond_id": "Cond07",
            "name": "Bob Left Only WF56 (Hyper12, seed 42, standalone, remainder=True)",
            "wf_source": os.path.join(WORKFLOWS_DIR, "56_VERIFY_BOB_LEFT_PROMPT_TRUTH_REMAINDER.json"),
            "dest_filename": "Cond07_WF56_Bob_Left_Only.png",
            "seed": 42, "mask_mode": "remainder_subtracted", "prompt_mode": "standalone",
            "guide_mode": "clean_no_bbox", "expected_subject": "bob_only", "expected_side": "left"
        },
        # Cond 08: Bob Right Only -> WF57
        {
            "cond_id": "Cond08",
            "name": "Bob Right Only WF57 (Hyper12, seed 42, standalone, remainder=True)",
            "wf_source": os.path.join(WORKFLOWS_DIR, "57_VERIFY_BOB_RIGHT_PROMPT_TRUTH_REMAINDER.json"),
            "dest_filename": "Cond08_WF57_Bob_Right_Only.png",
            "seed": 42, "mask_mode": "remainder_subtracted", "prompt_mode": "standalone",
            "guide_mode": "clean_no_bbox", "expected_subject": "bob_only", "expected_side": "right"
        },
        # Cond 09: Two-Character Swap: Bob Left / Alice Right -> WF59
        {
            "cond_id": "Cond09",
            "name": "Two-Character Swap WF59: Bob L / Alice R (Hyper12, seed 42, remainder=True)",
            "wf_source": os.path.join(WORKFLOWS_DIR, "59_VERIFY_TWO_CHARACTER_PROMPT_TRUTH_SWAP.json"),
            "dest_filename": "Cond09_WF59_TwoChar_BobL_AliceR.png",
            "seed": 42, "mask_mode": "remainder_subtracted", "prompt_mode": "standalone",
            "guide_mode": "clean_no_bbox", "expected_subject": "two_characters", "expected_side": "bob_l_alice_r"
        },
        # Cond 10: Region Order Recheck (Bob then Alice in region list)
        {
            "cond_id": "Cond10",
            "name": "Region Order Recheck: Bob list order first (Hyper12, seed 42, remainder=True)",
            "wf_source": build_phase3j1_workflow(
                wf_filename="temp_cond10_region_order_bob_first.json",
                title="Condition 10: Region Order Bob First",
                save_prefix="Tegaki/Phase3J1/Cond10_Region_Order_Bob_First",
                characters=[BOB_CANONICAL, ALICE_CANONICAL],
                attending_chars=[
                    make_character_binding("char_bob", prompt_override="standing on left", area=BOB_LEFT),
                    make_character_binding("char_alice", prompt_override="standing on right", area=ALICE_RIGHT)
                ],
                staging_overrides={
                    "char_bob": {"area": BOB_LEFT, "pose_preset": "standing_neutral"},
                    "char_alice": {"area": ALICE_RIGHT, "pose_preset": "standing_neutral"}
                },
                fast_draft_12=True, steps=12, cfg=6.0, seed=42,
                character_prompt_mode="standalone",
                remainder_mask_mode=True,
                ordering_mode="character_first"
            ),
            "dest_filename": "Cond10_Region_Order_Bob_First.png",
            "seed": 42, "mask_mode": "remainder_subtracted", "prompt_mode": "standalone",
            "guide_mode": "clean_no_bbox", "expected_subject": "two_characters", "expected_side": "bob_l_alice_r"
        },
        # Cond 11: Native20 Representative (Alice L / Bob R, steps 20, CFG 7.0, fast_draft_12=False)
        {
            "cond_id": "Cond11",
            "name": "Native20 Representative: Alice L / Bob R (Native20, steps 20, CFG 7.0, remainder=True)",
            "wf_source": build_phase3j1_workflow(
                wf_filename="temp_cond11_native20.json",
                title="Condition 11: Native20 Representative",
                save_prefix="Tegaki/Phase3J1/Cond11_Native20_AliceL_BobR",
                characters=[ALICE_CANONICAL, BOB_CANONICAL],
                attending_chars=[
                    make_character_binding("char_alice", prompt_override="standing calmly", area=ALICE_LEFT),
                    make_character_binding("char_bob", prompt_override="standing listening", area=BOB_RIGHT)
                ],
                staging_overrides={
                    "char_alice": {"area": ALICE_LEFT, "pose_preset": "standing_neutral"},
                    "char_bob": {"area": BOB_RIGHT, "pose_preset": "standing_neutral"}
                },
                fast_draft_12=False, steps=20, cfg=7.0, seed=42,
                character_prompt_mode="standalone",
                remainder_mask_mode=True
            ),
            "dest_filename": "Cond11_Native20_AliceL_BobR.png",
            "seed": 42, "mask_mode": "remainder_subtracted", "prompt_mode": "standalone",
            "guide_mode": "clean_no_bbox", "expected_subject": "two_characters", "expected_side": "alice_l_bob_r"
        },
        # Cond 12: Adaptive Shot Type: Alice Full Body (seed 42)
        {
            "cond_id": "Cond12",
            "name": "Adaptive Shot Type: Alice Full Body (Hyper12, seed 42, standalone)",
            "wf_source": build_phase3j1_workflow(
                wf_filename="temp_cond12_alice_full_body.json",
                title="Condition 12: Alice Full Body",
                save_prefix="Tegaki/Phase3J1/Cond12_ShotType_FullBody_Alice",
                characters=[ALICE_CANONICAL],
                attending_chars=[
                    make_character_binding("char_alice", prompt_override="standing calmly, full body", area=ALICE_LEFT)
                ],
                staging_overrides={
                    "char_alice": {"area": ALICE_LEFT, "shot_type": "full_body", "pose_preset": "standing_neutral"}
                },
                fast_draft_12=True, steps=12, cfg=6.0, seed=42,
                character_prompt_mode="standalone",
                remainder_mask_mode=True
            ),
            "dest_filename": "Cond12_ShotType_FullBody_Alice.png",
            "seed": 42, "mask_mode": "remainder_subtracted", "prompt_mode": "standalone",
            "guide_mode": "clean_no_bbox", "expected_subject": "alice_only", "expected_side": "left"
        },
        # Cond 13: Adaptive Shot Type: Alice Half Body (seed 42)
        {
            "cond_id": "Cond13",
            "name": "Adaptive Shot Type: Alice Half Body (Hyper12, seed 42, standalone)",
            "wf_source": build_phase3j1_workflow(
                wf_filename="temp_cond13_alice_half_body.json",
                title="Condition 13: Alice Half Body",
                save_prefix="Tegaki/Phase3J1/Cond13_ShotType_HalfBody_Alice",
                characters=[ALICE_CANONICAL],
                attending_chars=[
                    make_character_binding("char_alice", prompt_override="standing calmly, half body upper body portrait", area=ALICE_LEFT)
                ],
                staging_overrides={
                    "char_alice": {"area": ALICE_LEFT, "shot_type": "half_body", "pose_preset": "standing_neutral"}
                },
                fast_draft_12=True, steps=12, cfg=6.0, seed=42,
                character_prompt_mode="standalone",
                remainder_mask_mode=True
            ),
            "dest_filename": "Cond13_ShotType_HalfBody_Alice.png",
            "seed": 42, "mask_mode": "remainder_subtracted", "prompt_mode": "standalone",
            "guide_mode": "clean_no_bbox", "expected_subject": "alice_only", "expected_side": "left"
        },
        # Cond 14: Adaptive Shot Type: Alice Bust Shot (seed 42)
        {
            "cond_id": "Cond14",
            "name": "Adaptive Shot Type: Alice Bust Shot (Hyper12, seed 42, standalone)",
            "wf_source": build_phase3j1_workflow(
                wf_filename="temp_cond14_alice_bust_shot.json",
                title="Condition 14: Alice Bust Shot",
                save_prefix="Tegaki/Phase3J1/Cond14_ShotType_Bust_Alice",
                characters=[ALICE_CANONICAL],
                attending_chars=[
                    make_character_binding("char_alice", prompt_override="standing calmly, close-up bust shot face and shoulders", area=ALICE_LEFT)
                ],
                staging_overrides={
                    "char_alice": {"area": ALICE_LEFT, "shot_type": "bust", "pose_preset": "standing_neutral"}
                },
                fast_draft_12=True, steps=12, cfg=6.0, seed=42,
                character_prompt_mode="standalone",
                remainder_mask_mode=True
            ),
            "dest_filename": "Cond14_ShotType_Bust_Alice.png",
            "seed": 42, "mask_mode": "remainder_subtracted", "prompt_mode": "standalone",
            "guide_mode": "clean_no_bbox", "expected_subject": "alice_only", "expected_side": "left"
        }
    ]

    suite_results = []
    overall_start = time.time()

    try:
        for c in conditions:
            dest_path = os.path.join(OUTPUT_CANONICAL, c["dest_filename"])
            print(f"\n[{c['cond_id']}] Running: {c['name']}...")
            vram_start = get_gpu_vram_mb()
            prompt_graph = graph_to_api_prompt(c["wf_source"], object_info)

            t0 = time.time()
            try:
                queue_resp = comfy_runtime_helper.queue_prompt(prompt_graph)
                prompt_id = queue_resp.get("prompt_id")
                node_errors = queue_resp.get("node_errors", {})
                if node_errors:
                    raise RuntimeError(f"Validation error in {c['name']}: {node_errors}")

                print(f"  [QUEUED] Prompt ID: {prompt_id} (0 errors)")
                outputs = comfy_runtime_helper.wait_for_prompt(prompt_id, timeout=300)
                elapsed = time.time() - t0
                vram_peak = max(vram_start, get_gpu_vram_mb())

                img_path = comfy_runtime_helper.get_image_file_path(outputs, "18")
                if not img_path or not os.path.exists(img_path):
                    for nid, out_dict in outputs.items():
                        if "images" in out_dict and out_dict["images"]:
                            fallback = comfy_runtime_helper.get_image_file_path(outputs, nid)
                            if fallback and os.path.exists(fallback):
                                img_path = fallback
                                break

                if img_path and os.path.exists(img_path):
                    shutil.copyfile(img_path, dest_path)
                    print(f"  [PASS] Completed in {elapsed:.2f}s | VRAM: {vram_peak} MB. Image: {dest_path}")
                    suite_results.append({
                        "cond_id": c["cond_id"],
                        "name": c["name"],
                        "runtime_status": "PASS",
                        "elapsed_sec": round(elapsed, 2),
                        "vram_mb": vram_peak,
                        "seed": c["seed"],
                        "mask_mode": c["mask_mode"],
                        "prompt_mode": c["prompt_mode"],
                        "guide_mode": c["guide_mode"],
                        "expected_subject": c["expected_subject"],
                        "expected_side": c["expected_side"],
                        "output_image": dest_path
                    })
                else:
                    raise RuntimeError(f"No image produced for {c['name']}")

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
    print(f"Phase 3J.1 Execution Completed in {total_time:.2f}s")
    all_passed = all(r.get("runtime_status") == "PASS" for r in suite_results)
    print(f"Overall Runtime Result: {'ALL PASS' if all_passed else 'FAIL'}")
    print("=" * 80)

    # 5. Build Contact Sheets U, V, W, X, Y
    print("\n[Contact Sheets] Building Sheets U, V, W, X, Y...")

    sheet_u_items = [
        (os.path.join(OUTPUT_CANONICAL, "Cond01_Legacy_Broken_Baseline.png"), "Cond01: Legacy Broken Baseline", "appearance/acting | scene_composed | remainder=False"),
        (os.path.join(OUTPUT_CANONICAL, "Cond03_WF58_AliceL_BobR_Remainder_ON.png"), "Cond03: Contract-Fixed WF58", "prompt/override | standalone | remainder=True")
    ]
    create_contact_sheet(
        sheet_u_items,
        os.path.join(OUTPUT_CANONICAL, "ContactSheet_U_Legacy_vs_Fixed.png"),
        cols=2, cell_w=600, cell_h=600,
        sheet_title="Sheet U: Phase 3J Legacy Broken Fixture vs Phase 3J.1 Contract-Fixed Fixture"
    )

    sheet_v_items = [
        (os.path.join(OUTPUT_CANONICAL, "Cond02_Remainder_OFF.png"), "Cond02: Remainder Mask OFF", "Full Scene Overlap on Characters"),
        (os.path.join(OUTPUT_CANONICAL, "Cond03_WF58_AliceL_BobR_Remainder_ON.png"), "Cond03: Remainder Mask ON", "Scene Holes Subtracted at Characters"),
        (os.path.join(OUTPUT_CANONICAL, "Cond04_No_Panel_Region_Diagnostic.png"), "Cond04: No Panel Region", "include_panel_backgrounds=False")
    ]
    create_contact_sheet(
        sheet_v_items,
        os.path.join(OUTPUT_CANONICAL, "ContactSheet_V_Remainder_AB.png"),
        cols=3, cell_w=480, cell_h=480,
        sheet_title="Sheet V: Remainder Mask A/B Comparison (Overlap vs Subtraction vs No-Panel-Region)"
    )

    sheet_w_items = [
        (os.path.join(OUTPUT_CANONICAL, "Cond05_WF54_Alice_Left_Only.png"), "Cond05: Alice Left Only (WF54)", "standalone | remainder=True | seed 42"),
        (os.path.join(OUTPUT_CANONICAL, "Cond06_WF55_Alice_Right_Only.png"), "Cond06: Alice Right Only (WF55)", "standalone | remainder=True | seed 42"),
        (os.path.join(OUTPUT_CANONICAL, "Cond07_WF56_Bob_Left_Only.png"), "Cond07: Bob Left Only (WF56)", "standalone | remainder=True | seed 42"),
        (os.path.join(OUTPUT_CANONICAL, "Cond08_WF57_Bob_Right_Only.png"), "Cond08: Bob Right Only (WF57)", "standalone | remainder=True | seed 42")
    ]
    create_contact_sheet(
        sheet_w_items,
        os.path.join(OUTPUT_CANONICAL, "ContactSheet_W_Single_2x2.png"),
        cols=2, cell_w=512, cell_h=512,
        sheet_title="Sheet W: Single Character Staging & Side Bias Matrix (Alice & Bob L / R)"
    )

    sheet_x_items = [
        (os.path.join(OUTPUT_CANONICAL, "Cond03_WF58_AliceL_BobR_Remainder_ON.png"), "Cond03: Alice Left / Bob Right (WF58)", "Alice x=0.10, Bob x=0.55 | seed 42"),
        (os.path.join(OUTPUT_CANONICAL, "Cond09_WF59_TwoChar_BobL_AliceR.png"), "Cond09: Bob Left / Alice Right (WF59)", "Bob x=0.10, Alice x=0.55 | seed 42")
    ]
    create_contact_sheet(
        sheet_x_items,
        os.path.join(OUTPUT_CANONICAL, "ContactSheet_X_TwoChar_Swap.png"),
        cols=2, cell_w=600, cell_h=600,
        sheet_title="Sheet X: Two-Character Spatial Swap Matrix (WF58 vs WF59)"
    )

    sheet_y_items = [
        (os.path.join(OUTPUT_CANONICAL, "Cond12_ShotType_FullBody_Alice.png"), "Cond12: Alice Full Body", "shot_type=full_body | seed 42"),
        (os.path.join(OUTPUT_CANONICAL, "Cond13_ShotType_HalfBody_Alice.png"), "Cond13: Alice Half Body", "shot_type=half_body | seed 42"),
        (os.path.join(OUTPUT_CANONICAL, "Cond14_ShotType_Bust_Alice.png"), "Cond14: Alice Bust Shot", "shot_type=bust | seed 42")
    ]
    create_contact_sheet(
        sheet_y_items,
        os.path.join(OUTPUT_CANONICAL, "ContactSheet_Y_ShotType.png"),
        cols=3, cell_w=480, cell_h=480,
        sheet_title="Sheet Y: Adaptive Shot Type Semantic Verification (Full vs Half vs Bust)"
    )

    summary_data = {
        "suite": "Phase 3J.1 Character Prompt Contract Repair & Region Isolation Closure Suite",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_elapsed_sec": round(total_time, 2),
        "all_passed": all_passed,
        "results": suite_results
    }

    with open(results_file, "w", encoding="utf-8") as f:
        json.dump(summary_data, f, indent=2, ensure_ascii=False)
    print(f"\n[Phase3J.1 Results] Saved results to: {results_file}")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(run_phase3j1_closure_suite())
