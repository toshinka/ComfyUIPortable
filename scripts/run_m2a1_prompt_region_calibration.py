"""
run_m2a1_prompt_region_calibration.py — M2A.1 Prompt-Region Calibration Runner
================================================================================
Empirical verification runner for Milestone M2A.1:
- Fixed 8-seed benchmark (42, 77, 101, 133, 202, 303, 404, 505)
- Benchmark B: Two Distinct Characters (B0 Baseline vs B1 Horizontal Hints vs B2 Horizontal + Presence Hints)
- Benchmark B-Swap: Left/Right Area Inversion on top 3 seeds (42, 101, 202)
- Benchmark C: Depth 4-way Evaluation (C0 Long prompt vs C1 Short phrase vs C2 Geometry only vs C3 Geometry + Derived Depth)
- Benchmark H: 3 Distinct Characters (Alice, Bob, Carol; H0 Baseline vs H1 Horizontal vs H2 Horizontal + Presence)
- Benchmark F: Same CAST across separate scenes (4 seeds: 42, 77, 101, 133)
- Benchmark I: 4-Person Crowd (4 seeds: 42, 77, 101, 133)
- Conditional ControlNet Escalation Gate v2: Evaluates weak block guide ControlNet (0.20, 0.35)
  using TegakiMangaLayoutGuideGenerator and CN-anytest4_illustrious2_A.safetensors.

Generates:
- output/Tegaki/M2A1/ raw outputs
- docs/manga/verification/m2a1/ verified outputs, manifest, and contact sheets:
  - M2A1_TWO_CHARACTER_PROMPT_REGION.png
  - M2A1_DEPTH_PROMPT_REGION.png
  - M2A1_THREE_CHARACTER_PROMPT_REGION.png
  - M2A1_BLOCK_CONTROL_ESCALATION.png
  - M2A1_CALIBRATION_MANIFEST.json
"""

import os
import sys
import json
import time
import shutil
from typing import Dict, Any, List, Tuple, Optional
from PIL import Image, ImageDraw, ImageFont

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CUSTOM_NODES_DIR = os.path.join(ROOT_DIR, "custom_nodes_custom")
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
if CUSTOM_NODES_DIR not in sys.path:
    sys.path.insert(0, CUSTOM_NODES_DIR)

from scripts import comfy_runtime_helper
import importlib.util

def _import_submodule(subname, filename):
    fullname = f"tegaki_manga_nodes.{subname}"
    spec = importlib.util.spec_from_file_location(
        fullname,
        os.path.join(CUSTOM_NODES_DIR, "tegaki_manga_nodes", filename),
        submodule_search_locations=[],
    )
    mod = importlib.util.module_from_spec(spec)
    mod.__package__ = "tegaki_manga_nodes"
    sys.modules[fullname] = mod
    spec.loader.exec_module(mod)
    return mod

pkg = type(sys)("tegaki_manga_nodes")
pkg.__path__ = [os.path.join(CUSTOM_NODES_DIR, "tegaki_manga_nodes")]
sys.modules["tegaki_manga_nodes"] = pkg

_ac = _import_submodule("authoring_contract", "authoring_contract.py")
_aeb = _import_submodule("authoring_execution_bridge", "authoring_execution_bridge.py")
_shc = _import_submodule("spatial_hint_compiler", "spatial_hint_compiler.py")

create_document = _ac.create_document
create_page = _ac.create_page
create_scene = _ac.create_scene
create_cast_entry = _ac.create_cast_entry
create_character_instance = _ac.create_character_instance
make_area = _ac.make_area
generate_scene_regions_preview_image = _aeb.generate_scene_regions_preview_image
compile_document_to_page_plan = _aeb.compile_document_to_page_plan

OUTPUT_DIR = os.path.join(ROOT_DIR, "output", "Tegaki", "M2A1")
DOCS_DIR = os.path.join(ROOT_DIR, "docs", "manga", "verification", "m2a1")
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(DOCS_DIR, exist_ok=True)

CKPT_NAME = r"♃CN_Skeb\waiIllustriousSDXL_v170.safetensors"
CONTROLNET_NAME = "CN-anytest4_illustrious2_A.safetensors"
BENCHMARK_SEEDS = [42, 77, 101, 133, 202, 303, 404, 505]
SWAP_SEEDS = [42, 101, 202]


# --- Workflow Builders ---

def build_prompt_workflow(
    doc: Dict[str, Any],
    seed: int,
    prefix: str,
    spatial_hint_mode: str = "off",
    control_strength: float = 0.0,
) -> Dict[str, Any]:
    """Construct ComfyUI prompt dictionary for prompt-region conditioning with optional ControlNet."""
    doc_json = json.dumps(doc)
    page = doc["pages"][0]
    w = int(page.get("width_px", 832))
    h = int(page.get("height_px", 1216))

    wf = {
        "1": {
            "class_type": "TegakiMinimumHandSceneEditor",
            "inputs": {
                "document_json": doc_json,
                "seed": seed,
                "style_template": page.get("metadata", {}).get("style_template", "Manga Monochrome"),
                "resolution": "Portrait 832x1216",
                "spatial_hint_mode": spatial_hint_mode,
            }
        },
        "2": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {
                "ckpt_name": CKPT_NAME
            }
        },
        "3": {
            "class_type": "TegakiMangaConditioningBuilder",
            "inputs": {
                "clip": ["2", 1],
                "page_compile_plan": ["1", 0],
                "panel_strength": 1.0,
                "character_strength": 1.0,
                "set_cond_area": "default",
                "local_region_strength": 1.0,
                "mask_feather": 0
            }
        },
        "4": {
            "class_type": "EmptyLatentImage",
            "inputs": {
                "width": ["1", 3],
                "height": ["1", 4],
                "batch_size": 1
            }
        },
    }

    positive_link = ["3", 0]
    negative_link = ["3", 1]

    # If weak block ControlNet is requested
    if control_strength > 0.0:
        wf["10"] = {
            "class_type": "TegakiMangaLayoutGuideGenerator",
            "inputs": {
                "scene_plan": ["1", 0],
                "target_panel_id": 1,
                "guide_style": "mannequin_capsule",
                "color_mode": "Black on White",
                "line_thickness": 3,
                "include_panel_border": False,
                "include_character_bbox_outline": False,
                "width": w,
                "height": h,
            }
        }
        wf["11"] = {
            "class_type": "ControlNetLoader",
            "inputs": {
                "control_net_name": CONTROLNET_NAME
            }
        }
        wf["12"] = {
            "class_type": "ControlNetApplyAdvanced",
            "inputs": {
                "positive": ["3", 0],
                "negative": ["3", 1],
                "control_net": ["11", 0],
                "image": ["10", 0],
                "strength": float(control_strength),
                "start_percent": 0.0,
                "end_percent": 1.0,
            }
        }
        positive_link = ["12", 0]
        negative_link = ["12", 1]

    wf["5"] = {
        "class_type": "KSampler",
        "inputs": {
            "model": ["2", 0],
            "positive": positive_link,
            "negative": negative_link,
            "latent_image": ["4", 0],
            "seed": ["1", 2],
            "steps": 20,
            "cfg": 7.0,
            "sampler_name": "euler",
            "scheduler": "normal",
            "denoise": 1.0
        }
    }
    wf["6"] = {
        "class_type": "VAEDecode",
        "inputs": {
            "samples": ["5", 0],
            "vae": ["2", 2]
        }
    }
    wf["7"] = {
        "class_type": "SaveImage",
        "inputs": {
            "images": ["6", 0],
            "filename_prefix": f"Tegaki/M2A1/{prefix}"
        }
    }

    return wf


# --- CAST Fixtures ---

def get_cast():
    alice = create_cast_entry(
        display_name="Alice",
        identity_prompt="1girl, blonde twin tails, school uniform",
        negative_prompt="bad hands",
        cast_id="cast_alice"
    )
    bob = create_cast_entry(
        display_name="Bob",
        identity_prompt="1boy, short dark hair, glasses, school uniform",
        negative_prompt="bad hands",
        cast_id="cast_bob"
    )
    carol = create_cast_entry(
        display_name="Carol",
        identity_prompt="1girl, short brown bob hair, cardigan, school uniform",
        negative_prompt="bad hands",
        cast_id="cast_carol"
    )
    dave = create_cast_entry(
        display_name="Dave",
        identity_prompt="1boy, messy brown hair, athletic jacket",
        negative_prompt="bad hands",
        cast_id="cast_dave"
    )
    return alice, bob, carol, dave


# --- Condition Creators ---

def create_b_document(swap: bool = False):
    """Benchmark B: Two distinct characters in classroom."""
    alice, bob, _, _ = get_cast()
    scene = create_scene(
        name="Classroom",
        prompt="classroom, daytime, desks, windows, simple background",
        input_mode="cast",
        area=make_area(0.05, 0.05, 0.90, 0.90),
        scene_id="s_class"
    )

    area_left = make_area(0.08, 0.15, 0.38, 0.75)
    area_right = make_area(0.54, 0.15, 0.38, 0.75)

    if not swap:
        inst_alice = create_character_instance(cast_id="cast_alice", scene_id="s_class", area=area_left, acting_prompt="standing casually", order=1, instance_id="inst_a")
        inst_bob = create_character_instance(cast_id="cast_bob", scene_id="s_class", area=area_right, acting_prompt="reading a book", order=2, instance_id="inst_b")
    else:
        inst_bob = create_character_instance(cast_id="cast_bob", scene_id="s_class", area=area_left, acting_prompt="reading a book", order=1, instance_id="inst_b")
        inst_alice = create_character_instance(cast_id="cast_alice", scene_id="s_class", area=area_right, acting_prompt="standing casually", order=2, instance_id="inst_a")

    page = create_page(832, 1216)
    page["scenes"] = [scene]
    page["cast"] = [alice, bob]
    page["character_instances"] = [inst_alice, inst_bob]
    return create_document(pages=[page])


def create_c_document(mode: str):
    """
    Benchmark C: Depth.
    C0: equal boxes + manual long acting depth prompt
    C1: equal boxes + shorter depth phrase
    C2: geometry size difference + neutral acting prompt
    C3: geometry size difference + neutral acting prompt (depth derived)
    """
    alice, bob, _, _ = get_cast()
    scene = create_scene(
        name="Hallway",
        prompt="school hallway, lockers, windows, perspective hallway, simple background",
        input_mode="cast",
        area=make_area(0.05, 0.05, 0.90, 0.90),
        scene_id="s_hall"
    )

    if mode in ("C0", "C1"):
        # Equal boxes
        area_a = make_area(0.08, 0.15, 0.40, 0.78)
        area_b = make_area(0.52, 0.15, 0.40, 0.78)
        if mode == "C0":
            act_a = "close foreground, upper body prominently in foreground"
            act_b = "far in the background, small distant full body"
        else: # C1
            act_a = "large in foreground"
            act_b = "smaller in background"
    else: # C2, C3
        # Geometry size difference: large Alice, small Bob (ratio > 2.0)
        area_a = make_area(0.06, 0.08, 0.54, 0.84)  # area = 0.4536
        area_b = make_area(0.66, 0.20, 0.24, 0.45)  # area = 0.1080 (ratio ~ 4.2)
        act_a = "standing casually"
        act_b = "standing casually"

    inst_a = create_character_instance(cast_id="cast_alice", scene_id="s_hall", area=area_a, acting_prompt=act_a, order=1, instance_id="inst_a")
    inst_b = create_character_instance(cast_id="cast_bob", scene_id="s_hall", area=area_b, acting_prompt=act_b, order=2, instance_id="inst_b")

    page = create_page(832, 1216)
    page["scenes"] = [scene]
    page["cast"] = [alice, bob]
    page["character_instances"] = [inst_a, inst_b]
    return create_document(pages=[page])


def create_h_document():
    """Benchmark H: 3 Distinct Characters (Alice left, Bob center, Carol right)."""
    alice, bob, carol, _ = get_cast()
    scene = create_scene(
        name="Courtyard",
        prompt="school courtyard, benches, trees, daytime, simple background",
        input_mode="cast",
        area=make_area(0.05, 0.05, 0.90, 0.90),
        scene_id="s_court"
    )

    area_a = make_area(0.06, 0.15, 0.28, 0.72)
    area_b = make_area(0.36, 0.15, 0.28, 0.72)
    area_c = make_area(0.66, 0.15, 0.28, 0.72)

    inst_a = create_character_instance(cast_id="cast_alice", scene_id="s_court", area=area_a, acting_prompt="standing casually", order=1, instance_id="inst_a")
    inst_b = create_character_instance(cast_id="cast_bob", scene_id="s_court", area=area_b, acting_prompt="reading a book", order=2, instance_id="inst_b")
    inst_c = create_character_instance(cast_id="cast_carol", scene_id="s_court", area=area_c, acting_prompt="looking forward with smile", order=3, instance_id="inst_c")

    page = create_page(832, 1216)
    page["scenes"] = [scene]
    page["cast"] = [alice, bob, carol]
    page["character_instances"] = [inst_a, inst_b, inst_c]
    return create_document(pages=[page])


def create_f_document():
    """Benchmark F: Same CAST across separate scenes (Alice reading vs Alice walking)."""
    alice, _, _, _ = get_cast()
    s1 = create_scene(name="Library", prompt="library, bookshelves, reading desk", input_mode="cast", area=make_area(0.05, 0.05, 0.90, 0.42), order=1, scene_id="s1")
    s2 = create_scene(name="Park", prompt="outdoor park, pathway, daylight", input_mode="cast", area=make_area(0.05, 0.52, 0.90, 0.42), order=2, scene_id="s2")

    inst_1 = create_character_instance(cast_id="cast_alice", scene_id="s1", area=make_area(0.15, 0.10, 0.45, 0.32), acting_prompt="reading a book intently", order=1, instance_id="inst_1")
    inst_2 = create_character_instance(cast_id="cast_alice", scene_id="s2", area=make_area(0.40, 0.56, 0.45, 0.34), acting_prompt="walking forward, looking back", order=2, instance_id="inst_2")

    page = create_page(832, 1216)
    page["scenes"] = [s1, s2]
    page["cast"] = [alice]
    page["character_instances"] = [inst_1, inst_2]
    return create_document(pages=[page])


def create_i_document():
    """Benchmark I: 4-Person crowd."""
    alice, bob, carol, dave = get_cast()
    scene = create_scene(name="Clubroom", prompt="school clubroom, table, daylight, simple background", input_mode="cast", area=make_area(0.05, 0.05, 0.90, 0.90), scene_id="s_club")

    inst_a = create_character_instance(cast_id="cast_alice", scene_id="s_club", area=make_area(0.06, 0.15, 0.21, 0.70), acting_prompt="standing casually", order=1, instance_id="inst_a")
    inst_b = create_character_instance(cast_id="cast_bob", scene_id="s_club", area=make_area(0.28, 0.15, 0.21, 0.70), acting_prompt="sitting reading", order=2, instance_id="inst_b")
    inst_c = create_character_instance(cast_id="cast_carol", scene_id="s_club", area=make_area(0.50, 0.15, 0.21, 0.70), acting_prompt="smiling talking", order=3, instance_id="inst_c")
    inst_d = create_character_instance(cast_id="cast_dave", scene_id="s_club", area=make_area(0.72, 0.15, 0.21, 0.70), acting_prompt="standing hands in pockets", order=4, instance_id="inst_d")

    page = create_page(832, 1216)
    page["scenes"] = [scene]
    page["cast"] = [alice, bob, carol, dave]
    page["character_instances"] = [inst_a, inst_b, inst_c, inst_d]
    return create_document(pages=[page])


# --- Contact Sheet Generator ---

def create_contact_sheet(
    cells: List[Tuple[Image.Image, str, str]],
    title: str,
    output_path: str,
    cols: int = 8,
    thumb_w: int = 240,
    thumb_h: int = 350,
):
    """Renders a labeled grid contact sheet."""
    n = len(cells)
    if n == 0:
        return
    rows = (n + cols - 1) // cols
    cell_w = thumb_w + 16
    cell_h = thumb_h + 46
    top_header = 70
    side_margin = 16

    sheet_w = side_margin * 2 + cols * cell_w
    sheet_h = top_header + rows * cell_h + side_margin

    sheet = Image.new("RGB", (sheet_w, sheet_h), color=(22, 24, 28))
    draw = ImageDraw.Draw(sheet)

    try:
        font_title = ImageFont.truetype("arialbd.ttf", 22)
        font_cell = ImageFont.truetype("arialbd.ttf", 11)
        font_sub = ImageFont.truetype("arial.ttf", 10)
    except Exception:
        font_title = font_cell = font_sub = ImageFont.load_default()

    draw.text((side_margin, 20), title, fill=(255, 255, 255), font=font_title)

    for idx, (img, header, sub) in enumerate(cells):
        r = idx // cols
        c = idx % cols
        x = side_margin + c * cell_w + 8
        y = top_header + r * cell_h + 8

        thumb = img.copy()
        thumb.thumbnail((thumb_w, thumb_h), Image.Resampling.LANCZOS)
        tw, th = thumb.size
        ox = x + (thumb_w - tw) // 2
        oy = y + (thumb_h - th) // 2

        draw.rectangle([x - 2, y - 2, x + thumb_w + 2, y + thumb_h + 38], fill=(30, 33, 38), outline=(60, 65, 75), width=1)
        sheet.paste(thumb, (ox, oy))

        draw.text((x + 2, y + thumb_h + 4), header, fill=(240, 240, 240), font=font_cell)
        draw.text((x + 2, y + thumb_h + 18), sub, fill=(170, 180, 195), font=font_sub)

    sheet.save(output_path, "PNG", quality=95)
    print(f"[ContactSheet] Saved: {output_path} ({sheet_w}x{sheet_h})")


# --- Main Verification Suite ---

def main():
    print("\n========================================================")
    print("  Milestone M2A.1 Empirical Prompt-Region Calibration  ")
    print("========================================================\n")

    # Ensure server is running with latest code
    print("[Runner] Ensuring ComfyUI server is running and ready...")
    comfy_runtime_helper.restart_server(timeout=90)

    # 1. Build all conditions
    # We organize conditions into groups:
    # Suite B: B0, B1, B2 across 8 seeds (24)
    # Suite B-Swap: B0_swap, B1_swap, B2_swap across 3 seeds (9)
    # Suite C: C0, C1, C2, C3 across 8 seeds (32)
    # Suite H: H0, H1, H2 across 8 seeds (24)
    # Suite F: F across 4 seeds (4)
    # Suite I: I across 4 seeds (4)

    tasks = []

    # Benchmark B
    for seed in BENCHMARK_SEEDS:
        tasks.append({
            "id": f"B0_baseline_s{seed}",
            "suite": "B",
            "seed": seed,
            "doc": create_b_document(swap=False),
            "mode": "off",
            "control": 0.0,
            "title": f"B0 off s{seed}",
            "desc": "Baseline unhinted",
        })
        tasks.append({
            "id": f"B1_horiz_s{seed}",
            "suite": "B",
            "seed": seed,
            "doc": create_b_document(swap=False),
            "mode": "horizontal",
            "control": 0.0,
            "title": f"B1 horiz s{seed}",
            "desc": "Left/Right hints",
        })
        tasks.append({
            "id": f"B2_presence_s{seed}",
            "suite": "B",
            "seed": seed,
            "doc": create_b_document(swap=False),
            "mode": "horizontal_presence",
            "control": 0.0,
            "title": f"B2 pres s{seed}",
            "desc": "Horiz + 2-presence",
        })

    # Benchmark B-Swap (top 3 seeds)
    for seed in SWAP_SEEDS:
        tasks.append({
            "id": f"B0_swap_s{seed}",
            "suite": "B-Swap",
            "seed": seed,
            "doc": create_b_document(swap=True),
            "mode": "off",
            "control": 0.0,
            "title": f"B0 swap s{seed}",
            "desc": "Swap unhinted",
        })
        tasks.append({
            "id": f"B1_swap_s{seed}",
            "suite": "B-Swap",
            "seed": seed,
            "doc": create_b_document(swap=True),
            "mode": "horizontal",
            "control": 0.0,
            "title": f"B1 swap s{seed}",
            "desc": "Swap + Horiz",
        })
        tasks.append({
            "id": f"B2_swap_s{seed}",
            "suite": "B-Swap",
            "seed": seed,
            "doc": create_b_document(swap=True),
            "mode": "horizontal_presence",
            "control": 0.0,
            "title": f"B2 swap s{seed}",
            "desc": "Swap + Horiz+Pres",
        })

    # Benchmark C (Depth)
    for seed in BENCHMARK_SEEDS:
        tasks.append({
            "id": f"C0_long_s{seed}",
            "suite": "C",
            "seed": seed,
            "doc": create_c_document("C0"),
            "mode": "off",
            "control": 0.0,
            "title": f"C0 long s{seed}",
            "desc": "Equal boxes + long text",
        })
        tasks.append({
            "id": f"C1_short_s{seed}",
            "suite": "C",
            "seed": seed,
            "doc": create_c_document("C1"),
            "mode": "off",
            "control": 0.0,
            "title": f"C1 short s{seed}",
            "desc": "Equal boxes + short phrase",
        })
        tasks.append({
            "id": f"C2_geom_s{seed}",
            "suite": "C",
            "seed": seed,
            "doc": create_c_document("C2"),
            "mode": "off",
            "control": 0.0,
            "title": f"C2 geom s{seed}",
            "desc": "Geom ratio > 4x neutral",
        })
        tasks.append({
            "id": f"C3_depth_hint_s{seed}",
            "suite": "C",
            "seed": seed,
            "doc": create_c_document("C3"),
            "mode": "spatial_depth",
            "control": 0.0,
            "title": f"C3 derived s{seed}",
            "desc": "Geom + derived depth",
        })

    # Benchmark H (3 Distinct)
    for seed in BENCHMARK_SEEDS:
        tasks.append({
            "id": f"H0_baseline_s{seed}",
            "suite": "H",
            "seed": seed,
            "doc": create_h_document(),
            "mode": "off",
            "control": 0.0,
            "title": f"H0 off s{seed}",
            "desc": "3-distinct unhinted",
        })
        tasks.append({
            "id": f"H1_horiz_s{seed}",
            "suite": "H",
            "seed": seed,
            "doc": create_h_document(),
            "mode": "horizontal",
            "control": 0.0,
            "title": f"H1 horiz s{seed}",
            "desc": "3-distinct left/ctr/right",
        })
        tasks.append({
            "id": f"H2_presence_s{seed}",
            "suite": "H",
            "seed": seed,
            "doc": create_h_document(),
            "mode": "horizontal_presence",
            "control": 0.0,
            "title": f"H2 pres s{seed}",
            "desc": "3-distinct + 3-presence",
        })

    # Benchmark F (Cross-scene, 4 seeds)
    for seed in BENCHMARK_SEEDS[:4]:
        tasks.append({
            "id": f"F_cross_scene_s{seed}",
            "suite": "F",
            "seed": seed,
            "doc": create_f_document(),
            "mode": "off",
            "control": 0.0,
            "title": f"F s{seed}",
            "desc": "Same CAST across scenes",
        })

    # Benchmark I (4-person crowd, 4 seeds)
    for seed in BENCHMARK_SEEDS[:4]:
        tasks.append({
            "id": f"I_crowd_s{seed}",
            "suite": "I",
            "seed": seed,
            "doc": create_i_document(),
            "mode": "horizontal_presence",
            "control": 0.0,
            "title": f"I s{seed}",
            "desc": "4-person group scene",
        })

    print(f"[Runner] Total empirical calibration conditions queued: {len(tasks)}")

    # Execute all conditions
    completed_map: Dict[str, Dict[str, Any]] = {}
    manifest_entries: List[Dict[str, Any]] = []

    t_start_all = time.time()

    for idx, item in enumerate(tasks):
        cid = item["id"]
        seed = item["seed"]
        doc = item["doc"]
        mode = item["mode"]
        ctrl = item["control"]
        suite = item["suite"]

        print(f"\n[{idx+1}/{len(tasks)}] Running {cid} (Suite {suite}, seed {seed}, mode {mode})...")

        # Compile plan to capture transparent provenance
        plan = compile_document_to_page_plan(doc, spatial_hint_mode=mode)
        p0 = plan["panels"][0]

        char_debug = []
        for c in p0.get("characters", []):
            char_debug.append({
                "instance_id": c.get("instance_id"),
                "cast_id": c.get("character_id"),
                "raw_identity_prompt": c.get("raw_identity_prompt"),
                "raw_acting_prompt": c.get("raw_acting_prompt"),
                "derived_spatial_hint": c.get("derived_spatial_hint"),
                "scene_presence_hint": c.get("scene_presence_hint"),
                "effective_character_prompt": c.get("effective_character_prompt"),
            })

        # Save preview
        prev_img = generate_scene_regions_preview_image(doc)
        prev_path = os.path.join(DOCS_DIR, f"{cid}_preview.png")
        prev_img.save(prev_path)

        wf = build_prompt_workflow(doc, seed, prefix=cid, spatial_hint_mode=mode, control_strength=ctrl)

        t0 = time.time()
        try:
            res = comfy_runtime_helper.queue_prompt(wf)
            prompt_id = res["prompt_id"]
            outputs = comfy_runtime_helper.wait_for_prompt(prompt_id, timeout=120)
            elapsed = time.time() - t0

            raw_path = comfy_runtime_helper.get_image_file_path(outputs, "7")
            if not raw_path or not os.path.exists(raw_path):
                raise RuntimeError(f"Generated file not found for {cid}")

            final_path = os.path.join(DOCS_DIR, f"{cid}.png")
            shutil.copyfile(raw_path, final_path)
            print(f" -> Finished in {elapsed:.1f}s. Saved: {final_path}")

            completed_map[cid] = {
                "image_path": final_path,
                "preview_path": prev_path,
                "elapsed": elapsed,
                "item": item,
            }

            manifest_entries.append({
                "condition_id": cid,
                "suite": suite,
                "seed": seed,
                "hint_mode": mode,
                "control_strength": ctrl,
                "runtime_status": "PASS",
                "visual_status": "PENDING_INSPECTION",
                "review_method": "DIRECT_IMAGE_INSPECTION",
                "effective_scene_prompt": p0.get("compiled_prompt"),
                "characters": char_debug,
                "elapsed_seconds": round(elapsed, 2),
                "output_path": f"docs/manga/verification/m2a1/{cid}.png",
            })
        except Exception as e:
            elapsed = time.time() - t0
            print(f" -> ERROR in {cid}: {e}")
            manifest_entries.append({
                "condition_id": cid,
                "suite": suite,
                "seed": seed,
                "hint_mode": mode,
                "control_strength": ctrl,
                "runtime_status": "FAIL",
                "visual_status": "FAIL",
                "review_method": "RUNTIME_ERROR",
                "error": str(e),
                "elapsed_seconds": round(elapsed, 2),
            })

    total_time = time.time() - t_start_all
    print(f"\n[Runner] All prompt-region conditions completed in {total_time:.1f}s ({total_time/60:.1f} min).")

    # 2. Check ControlNet Escalation conditions
    # We will run ControlNet comparison on select hard seeds (e.g. 42, 101, 202) for 3-character and depth
    print("\n[ControlNetGate] Evaluating ControlNet Escalation Suite (Block CN 0.20 and 0.35)...")
    cn_tasks = [
        {"id": "H_CN020_s101", "base_id": "H2_presence_s101", "doc": create_h_document(), "seed": 101, "mode": "horizontal_presence", "ctrl": 0.20},
        {"id": "H_CN035_s101", "base_id": "H2_presence_s101", "doc": create_h_document(), "seed": 101, "mode": "horizontal_presence", "ctrl": 0.35},
        {"id": "H_CN020_s202", "base_id": "H2_presence_s202", "doc": create_h_document(), "seed": 202, "mode": "horizontal_presence", "ctrl": 0.20},
        {"id": "H_CN035_s202", "base_id": "H2_presence_s202", "doc": create_h_document(), "seed": 202, "mode": "horizontal_presence", "ctrl": 0.35},
    ]

    for cn_item in cn_tasks:
        cid = cn_item["id"]
        seed = cn_item["seed"]
        doc = cn_item["doc"]
        mode = cn_item["mode"]
        ctrl = cn_item["ctrl"]

        print(f" -> Running ControlNet condition {cid} (ctrl={ctrl}, seed={seed})...")
        prev_img = generate_scene_regions_preview_image(doc)
        prev_path = os.path.join(DOCS_DIR, f"{cid}_preview.png")
        prev_img.save(prev_path)

        wf = build_prompt_workflow(doc, seed, prefix=cid, spatial_hint_mode=mode, control_strength=ctrl)
        t0 = time.time()
        try:
            res = comfy_runtime_helper.queue_prompt(wf)
            prompt_id = res["prompt_id"]
            outputs = comfy_runtime_helper.wait_for_prompt(prompt_id, timeout=120)
            elapsed = time.time() - t0
            raw_path = comfy_runtime_helper.get_image_file_path(outputs, "7")
            final_path = os.path.join(DOCS_DIR, f"{cid}.png")
            shutil.copyfile(raw_path, final_path)
            print(f"    Completed in {elapsed:.1f}s.")

            completed_map[cid] = {
                "image_path": final_path,
                "preview_path": prev_path,
                "elapsed": elapsed,
                "item": cn_item,
            }
            manifest_entries.append({
                "condition_id": cid,
                "suite": "ControlNet",
                "seed": seed,
                "hint_mode": mode,
                "control_strength": ctrl,
                "runtime_status": "PASS",
                "visual_status": "PENDING_INSPECTION",
                "review_method": "DIRECT_IMAGE_INSPECTION",
                "elapsed_seconds": round(elapsed, 2),
                "output_path": f"docs/manga/verification/m2a1/{cid}.png",
            })
        except Exception as e:
            print(f"    ERROR: {e}")

    # 3. Build Contact Sheets
    print("\n[ContactSheets] Generating Contact Sheets...")

    # Sheet 1: M2A1_TWO_CHARACTER_PROMPT_REGION.png (8 seeds x 3 modes = 24 cells)
    cells_b = []
    for mode_prefix in ["B0_baseline", "B1_horiz", "B2_presence"]:
        for seed in BENCHMARK_SEEDS:
            cid = f"{mode_prefix}_s{seed}"
            if cid in completed_map:
                img = Image.open(completed_map[cid]["image_path"])
                label = f"[{cid}]"
                sub = f"{mode_prefix.split('_')[0]} | seed {seed}"
                cells_b.append((img, label, sub))

    sheet_b_path = os.path.join(DOCS_DIR, "M2A1_TWO_CHARACTER_PROMPT_REGION.png")
    create_contact_sheet(cells_b, "M2A.1 Two-Character 8-Seed Calibration (B0 Baseline vs B1 Horiz vs B2 Presence)", sheet_b_path, cols=8, thumb_w=200, thumb_h=290)

    # Sheet 2: M2A1_DEPTH_PROMPT_REGION.png (8 seeds x 4 modes = 32 cells)
    cells_c = []
    for mode_prefix in ["C0_long", "C1_short", "C2_geom", "C3_depth_hint"]:
        for seed in BENCHMARK_SEEDS:
            cid = f"{mode_prefix}_s{seed}"
            if cid in completed_map:
                img = Image.open(completed_map[cid]["image_path"])
                label = f"[{cid}]"
                sub = f"{mode_prefix.split('_')[0]} | seed {seed}"
                cells_c.append((img, label, sub))

    sheet_c_path = os.path.join(DOCS_DIR, "M2A1_DEPTH_PROMPT_REGION.png")
    create_contact_sheet(cells_c, "M2A.1 Depth 8-Seed Calibration (C0 Long vs C1 Short vs C2 Geom vs C3 Derived)", sheet_c_path, cols=8, thumb_w=200, thumb_h=290)

    # Sheet 3: M2A1_THREE_CHARACTER_PROMPT_REGION.png (8 seeds x 3 modes = 24 cells)
    cells_h = []
    for mode_prefix in ["H0_baseline", "H1_horiz", "H2_presence"]:
        for seed in BENCHMARK_SEEDS:
            cid = f"{mode_prefix}_s{seed}"
            if cid in completed_map:
                img = Image.open(completed_map[cid]["image_path"])
                label = f"[{cid}]"
                sub = f"{mode_prefix.split('_')[0]} | seed {seed}"
                cells_h.append((img, label, sub))

    sheet_h_path = os.path.join(DOCS_DIR, "M2A1_THREE_CHARACTER_PROMPT_REGION.png")
    create_contact_sheet(cells_h, "M2A.1 Three-Character 8-Seed Calibration (H0 Baseline vs H1 Horiz vs H2 Presence)", sheet_h_path, cols=8, thumb_w=200, thumb_h=290)

    # Sheet 4: M2A1_BLOCK_CONTROL_ESCALATION.png
    cells_cn = []
    for seed in [101, 202]:
        base_id = f"H2_presence_s{seed}"
        cn020_id = f"H_CN020_s{seed}"
        cn035_id = f"H_CN035_s{seed}"
        if base_id in completed_map and cn020_id in completed_map and cn035_id in completed_map:
            prev = Image.open(completed_map[base_id]["preview_path"])
            img_base = Image.open(completed_map[base_id]["image_path"])
            img_020 = Image.open(completed_map[cn020_id]["image_path"])
            img_035 = Image.open(completed_map[cn035_id]["image_path"])

            cells_cn.append((prev, f"Preview s{seed}", "Staging bounds"))
            cells_cn.append((img_base, f"Prompt-only s{seed}", "H2 Presence"))
            cells_cn.append((img_020, f"Block CN 0.20 s{seed}", "Weak guide"))
            cells_cn.append((img_035, f"Block CN 0.35 s{seed}", "Medium guide"))

    if cells_cn:
        sheet_cn_path = os.path.join(DOCS_DIR, "M2A1_BLOCK_CONTROL_ESCALATION.png")
        create_contact_sheet(cells_cn, "M2A.1 ControlNet Escalation Comparison (Prompt-Only vs Block CN 0.20 vs Block CN 0.35)", sheet_cn_path, cols=4, thumb_w=240, thumb_h=350)

    # 4. Save Manifest
    manifest_file = os.path.join(DOCS_DIR, "M2A1_CALIBRATION_MANIFEST.json")
    with open(manifest_file, "w", encoding="utf-8") as f:
        json.dump({
            "milestone": "M2A.1",
            "title": "M2A.1 Prompt Region Calibration & ControlNet Gate Manifest",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "checkpoint": CKPT_NAME,
            "seeds": BENCHMARK_SEEDS,
            "conditions_total": len(manifest_entries),
            "conditions_completed": len(completed_map),
            "entries": manifest_entries,
        }, f, indent=2, ensure_ascii=False)
    print(f"[Manifest] Saved: {manifest_file}")
    print("\n[Runner] Milestone M2A.1 Verification Execution COMPLETE.\n")


if __name__ == "__main__":
    main()
