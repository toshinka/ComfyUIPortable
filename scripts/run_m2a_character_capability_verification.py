"""
run_m2a_character_capability_verification.py — M2A Character Spatial Capability Runner
======================================================================================
Executes the empirical verification suite for M2A Character Spatial Capability Ladder:
- Stage A: Single Character Positioning Sanity (A1 Left vs A2 Right, same seed 42)
- Stage B: Two Distinct Characters Presence & Separation (Alice left, Bob right; seeds 42, 101, 202)
- Stage B2: Two Characters Left/Right Swap Oracle (same seed 42, swapped areas)
- Stage C/D: Depth 3-way Comparison (C1 Prompt-only vs C2 Geometry-only vs C3 Combined, seed 42)
- Stage E: Pose Prompt Ceiling Diagnostic (E1 Standing vs E2 Sitting, seed 42)
- Stage F: Same CAST Across Multiple Scenes (Scene 1 reading, Scene 2 looking back, seed 42)
- Stage G: Same CAST Twice in One Scene (Alice_A smiling, Alice_B looking away; seeds 42, 101, 202)
- Stage H: Same CAST + Other CAST Mixed 3-person (Alice_A, Alice_B, Bob_A; seeds 42, 101, 202)
- Stage I: Crowd / Large Count Scalability (4 distinct character slots, seed 42)

Produces:
- output/Tegaki/M2A/ raw generations
- docs/manga/verification/m2a/ verified images, mask preview images, manifest, and contact sheets:
  - M2A_TWO_CHARACTER_ORACLE.png
  - M2A_DEPTH_ORACLE.png
  - M2A_REPEATED_CAST_ORACLE.png
  - M2A_CROWD_ORACLE.png
"""
import os
import sys
import json
import time
import shutil
from typing import Dict, Any, List, Tuple
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
_ir = _import_submodule("interaction_resolver", "interaction_resolver.py")
_sc = _import_submodule("subscene_contract", "subscene_contract.py")
_ss = _import_submodule("scene_spec", "scene_spec.py")
_mb = _import_submodule("mask_builder", "mask_builder.py")
_aeb = _import_submodule("authoring_execution_bridge", "authoring_execution_bridge.py")
_mse = _import_submodule("minimum_hand_scene_editor", "minimum_hand_scene_editor.py")

create_document = _ac.create_document
create_page = _ac.create_page
create_scene = _ac.create_scene
create_cast_entry = _ac.create_cast_entry
create_character_instance = _ac.create_character_instance
make_area = _ac.make_area
generate_scene_regions_preview_image = _aeb.generate_scene_regions_preview_image

OUTPUT_DIR = os.path.join(ROOT_DIR, "output", "Tegaki", "M2A")
DOCS_DIR = os.path.join(ROOT_DIR, "docs", "manga", "verification", "m2a")
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(DOCS_DIR, exist_ok=True)

CKPT_NAME = r"♃CN_Skeb\waiIllustriousSDXL_v170.safetensors"


def build_m2a_prompt_workflow(doc: Dict[str, Any], seed: int, prefix: str) -> Dict[str, Any]:
    """Construct ComfyUI prompt dictionary for M2A Minimum-Hand Authoring with CAST & Character instances."""
    doc_json = json.dumps(doc)
    page = doc["pages"][0]
    w = int(page.get("width_px", 832))
    h = int(page.get("height_px", 1216))

    return {
        "1": {
            "class_type": "TegakiMinimumHandSceneEditor",
            "inputs": {
                "document_json": doc_json,
                "seed": seed,
                "style_template": page.get("metadata", {}).get("style_template", "Manga Monochrome"),
                "resolution": "Portrait 832x1216",
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
        "5": {
            "class_type": "KSampler",
            "inputs": {
                "model": ["2", 0],
                "positive": ["3", 0],
                "negative": ["3", 1],
                "latent_image": ["4", 0],
                "seed": ["1", 2],
                "steps": 20,
                "cfg": 7.0,
                "sampler_name": "euler",
                "scheduler": "normal",
                "denoise": 1.0
            }
        },
        "6": {
            "class_type": "VAEDecode",
            "inputs": {
                "samples": ["5", 0],
                "vae": ["2", 2]
            }
        },
        "7": {
            "class_type": "SaveImage",
            "inputs": {
                "images": ["6", 0],
                "filename_prefix": f"Tegaki/M2A/{prefix}"
            }
        }
    }


# Standard Characters
def get_cast_alice():
    return create_cast_entry(
        display_name="Alice",
        identity_prompt="1girl, blonde twin tails, blue eyes, female school uniform",
        negative_prompt="bad anatomy, lowres",
        cast_id="cast_alice"
    )

def get_cast_bob():
    return create_cast_entry(
        display_name="Bob",
        identity_prompt="1boy, short black hair, glasses, male school uniform",
        negative_prompt="bad anatomy, lowres",
        cast_id="cast_bob"
    )

def get_cast_carol():
    return create_cast_entry(
        display_name="Carol",
        identity_prompt="1girl, red short hair, green eyes, female school uniform",
        negative_prompt="bad anatomy, lowres",
        cast_id="cast_carol"
    )

def get_cast_dave():
    return create_cast_entry(
        display_name="Dave",
        identity_prompt="1boy, messy brown hair, amber eyes, casual jacket",
        negative_prompt="bad anatomy, lowres",
        cast_id="cast_dave"
    )


# Fixture Builders
def create_fixture_a1(seed: int = 42) -> Dict[str, Any]:
    """A1: Single character Alice on LEFT."""
    page = create_page(832, 1216, "manga page, monochrome, expressive linework, screentone shading", "color, photo, 3d render")
    page["scenes"].append(create_scene("Courtyard", "school courtyard, daytime, cherry blossom trees", input_mode="cast", area=make_area(0.05, 0.05, 0.90, 0.90), scene_id="sc1"))
    page["cast"].append(get_cast_alice())
    page["character_instances"].append(create_character_instance("cast_alice", "sc1", area=make_area(0.08, 0.10, 0.38, 0.80), acting_prompt="standing casually", order=1, instance_id="inst_alice_left"))
    return create_document(pages=[page])


def create_fixture_a2(seed: int = 42) -> Dict[str, Any]:
    """A2: Single character Alice on RIGHT (same seed as A1)."""
    page = create_page(832, 1216, "manga page, monochrome, expressive linework, screentone shading", "color, photo, 3d render")
    page["scenes"].append(create_scene("Courtyard", "school courtyard, daytime, cherry blossom trees", input_mode="cast", area=make_area(0.05, 0.05, 0.90, 0.90), scene_id="sc1"))
    page["cast"].append(get_cast_alice())
    page["character_instances"].append(create_character_instance("cast_alice", "sc1", area=make_area(0.54, 0.10, 0.38, 0.80), acting_prompt="standing casually", order=1, instance_id="inst_alice_right"))
    return create_document(pages=[page])


def create_fixture_b(seed: int = 42) -> Dict[str, Any]:
    """B: Two distinct characters: Alice LEFT, Bob RIGHT."""
    page = create_page(832, 1216, "manga page, monochrome, expressive linework, screentone shading", "color, photo, 3d render")
    page["scenes"].append(create_scene("Classroom", "classroom desks and chalkboard, daylight streaming", input_mode="cast", area=make_area(0.05, 0.05, 0.90, 0.90), scene_id="sc1"))
    page["cast"].extend([get_cast_alice(), get_cast_bob()])
    page["character_instances"].append(create_character_instance("cast_alice", "sc1", area=make_area(0.08, 0.10, 0.38, 0.80), acting_prompt="standing, looking forward", order=1, instance_id="inst_alice"))
    page["character_instances"].append(create_character_instance("cast_bob", "sc1", area=make_area(0.54, 0.10, 0.38, 0.80), acting_prompt="standing, holding a notebook", order=2, instance_id="inst_bob"))
    return create_document(pages=[page])


def create_fixture_b2_swap(seed: int = 42) -> Dict[str, Any]:
    """B2 Swap: Swapped positions: Alice RIGHT, Bob LEFT (identical prompts & seed to B)."""
    page = create_page(832, 1216, "manga page, monochrome, expressive linework, screentone shading", "color, photo, 3d render")
    page["scenes"].append(create_scene("Classroom", "classroom desks and chalkboard, daylight streaming", input_mode="cast", area=make_area(0.05, 0.05, 0.90, 0.90), scene_id="sc1"))
    page["cast"].extend([get_cast_alice(), get_cast_bob()])
    # Swapped areas
    page["character_instances"].append(create_character_instance("cast_bob", "sc1", area=make_area(0.08, 0.10, 0.38, 0.80), acting_prompt="standing, holding a notebook", order=1, instance_id="inst_bob"))
    page["character_instances"].append(create_character_instance("cast_alice", "sc1", area=make_area(0.54, 0.10, 0.38, 0.80), acting_prompt="standing, looking forward", order=2, instance_id="inst_alice"))
    return create_document(pages=[page])


def create_fixture_c1_depth_prompt(seed: int = 42) -> Dict[str, Any]:
    """C1: Prompt-only depth (equal region sizes, distinct depth prompts)."""
    page = create_page(832, 1216, "manga page, monochrome, expressive linework, screentone shading", "color, photo, 3d render")
    page["scenes"].append(create_scene("School Hallway", "school hallway with perspective lockers and floor tiles", input_mode="cast", area=make_area(0.05, 0.05, 0.90, 0.90), scene_id="sc1"))
    page["cast"].extend([get_cast_alice(), get_cast_bob()])
    # Equal sizes
    page["character_instances"].append(create_character_instance("cast_alice", "sc1", area=make_area(0.08, 0.12, 0.40, 0.78), acting_prompt="close foreground, upper body prominently in foreground", order=1, instance_id="inst_alice_fg"))
    page["character_instances"].append(create_character_instance("cast_bob", "sc1", area=make_area(0.52, 0.12, 0.40, 0.78), acting_prompt="far in the background, small distant full body", order=2, instance_id="inst_bob_bg"))
    return create_document(pages=[page])


def create_fixture_c2_depth_geometry(seed: int = 42) -> Dict[str, Any]:
    """C2: Geometry-only depth (large Alice region vs small Bob region, neutral prompts)."""
    page = create_page(832, 1216, "manga page, monochrome, expressive linework, screentone shading", "color, photo, 3d render")
    page["scenes"].append(create_scene("School Hallway", "school hallway with perspective lockers and floor tiles", input_mode="cast", area=make_area(0.05, 0.05, 0.90, 0.90), scene_id="sc1"))
    page["cast"].extend([get_cast_alice(), get_cast_bob()])
    # Geometry differentiated
    page["character_instances"].append(create_character_instance("cast_alice", "sc1", area=make_area(0.06, 0.08, 0.54, 0.84), acting_prompt="standing casually", order=1, instance_id="inst_alice_large"))
    page["character_instances"].append(create_character_instance("cast_bob", "sc1", area=make_area(0.68, 0.26, 0.24, 0.45), acting_prompt="standing casually", order=2, instance_id="inst_bob_small"))
    return create_document(pages=[page])


def create_fixture_c3_depth_combined(seed: int = 42) -> Dict[str, Any]:
    """C3: Combined depth (Geometry size + Prompt depth wording)."""
    page = create_page(832, 1216, "manga page, monochrome, expressive linework, screentone shading", "color, photo, 3d render")
    page["scenes"].append(create_scene("School Hallway", "school hallway with perspective lockers and floor tiles", input_mode="cast", area=make_area(0.05, 0.05, 0.90, 0.90), scene_id="sc1"))
    page["cast"].extend([get_cast_alice(), get_cast_bob()])
    # Geometry + Prompt combined
    page["character_instances"].append(create_character_instance("cast_alice", "sc1", area=make_area(0.06, 0.08, 0.54, 0.84), acting_prompt="close foreground, upper body prominently in foreground", order=1, instance_id="inst_alice_comb"))
    page["character_instances"].append(create_character_instance("cast_bob", "sc1", area=make_area(0.68, 0.26, 0.24, 0.45), acting_prompt="far in the background, small distant full body", order=2, instance_id="inst_bob_comb"))
    return create_document(pages=[page])


def create_fixture_e1_standing(seed: int = 42) -> Dict[str, Any]:
    """E1: Pose diagnostic - standing casually."""
    page = create_page(832, 1216, "manga page, monochrome, expressive linework, screentone shading", "color, photo, 3d render")
    page["scenes"].append(create_scene("Room", "japanese study room, tatami mats", input_mode="cast", area=make_area(0.05, 0.05, 0.90, 0.90), scene_id="sc1"))
    page["cast"].append(get_cast_alice())
    page["character_instances"].append(create_character_instance("cast_alice", "sc1", area=make_area(0.20, 0.10, 0.60, 0.80), acting_prompt="standing casually", order=1, instance_id="inst_alice_stand"))
    return create_document(pages=[page])


def create_fixture_e2_sitting(seed: int = 42) -> Dict[str, Any]:
    """E2: Pose diagnostic - sitting on a chair (same seed and area as E1)."""
    page = create_page(832, 1216, "manga page, monochrome, expressive linework, screentone shading", "color, photo, 3d render")
    page["scenes"].append(create_scene("Room", "japanese study room, tatami mats", input_mode="cast", area=make_area(0.05, 0.05, 0.90, 0.90), scene_id="sc1"))
    page["cast"].append(get_cast_alice())
    page["character_instances"].append(create_character_instance("cast_alice", "sc1", area=make_area(0.20, 0.10, 0.60, 0.80), acting_prompt="sitting on a wooden chair, relaxed posture", order=1, instance_id="inst_alice_sit"))
    return create_document(pages=[page])


def create_fixture_f_across_scenes(seed: int = 42) -> Dict[str, Any]:
    """F: Same CAST across 2 semantic scenes on same page."""
    page = create_page(832, 1216, "manga page, monochrome, expressive linework, screentone shading", "color, photo, 3d render")
    page["scenes"].append(create_scene("Scene 1 (Top)", "classroom, daytime window light", input_mode="cast", area=make_area(0.08, 0.06, 0.84, 0.42), scene_id="sc_top", order=1))
    page["scenes"].append(create_scene("Scene 2 (Bottom)", "outdoor train station platform at dusk", input_mode="cast", area=make_area(0.08, 0.52, 0.84, 0.42), scene_id="sc_bottom", order=2))
    page["cast"].append(get_cast_alice())
    page["character_instances"].append(create_character_instance("cast_alice", "sc_top", area=make_area(0.12, 0.10, 0.40, 0.35), acting_prompt="reading a book quietly", order=1, instance_id="inst_alice_scene1"))
    page["character_instances"].append(create_character_instance("cast_alice", "sc_bottom", area=make_area(0.50, 0.56, 0.38, 0.35), acting_prompt="walking and looking back, surprised smile", order=1, instance_id="inst_alice_scene2"))
    return create_document(pages=[page])


def create_fixture_g_same_cast_double(seed: int = 42) -> Dict[str, Any]:
    """G: Same CAST twice in one scene (Alice left and Alice right)."""
    page = create_page(832, 1216, "manga page, monochrome, expressive linework, screentone shading", "color, photo, 3d render")
    page["scenes"].append(create_scene("Music Room", "school music room, piano and sheet music", input_mode="cast", area=make_area(0.05, 0.05, 0.90, 0.90), scene_id="sc1"))
    page["cast"].append(get_cast_alice())
    page["character_instances"].append(create_character_instance("cast_alice", "sc1", area=make_area(0.08, 0.10, 0.38, 0.80), acting_prompt="smiling happily, waving hand", order=1, instance_id="inst_alice_a"))
    page["character_instances"].append(create_character_instance("cast_alice", "sc1", area=make_area(0.54, 0.10, 0.38, 0.80), acting_prompt="looking away thoughtfully with hand on chin", order=2, instance_id="inst_alice_b"))
    return create_document(pages=[page])


def create_fixture_h_mixed_three_person(seed: int = 42) -> Dict[str, Any]:
    """H: Same CAST + Other CAST mixed (Alice_A left, Alice_B center, Bob_A right)."""
    page = create_page(832, 1216, "manga page, monochrome, expressive linework, screentone shading", "color, photo, 3d render")
    page["scenes"].append(create_scene("Clubroom", "school clubroom, table and chairs", input_mode="cast", area=make_area(0.05, 0.05, 0.90, 0.90), scene_id="sc1"))
    page["cast"].extend([get_cast_alice(), get_cast_bob()])
    page["character_instances"].append(create_character_instance("cast_alice", "sc1", area=make_area(0.05, 0.15, 0.27, 0.75), acting_prompt="cheerful smile, talking", order=1, instance_id="inst_alice_1"))
    page["character_instances"].append(create_character_instance("cast_alice", "sc1", area=make_area(0.36, 0.15, 0.27, 0.75), acting_prompt="curious expression, pointing", order=2, instance_id="inst_alice_2"))
    page["character_instances"].append(create_character_instance("cast_bob", "sc1", area=make_area(0.68, 0.15, 0.27, 0.75), acting_prompt="listening calmly with glasses", order=3, instance_id="inst_bob_1"))
    return create_document(pages=[page])


def create_fixture_i_four_person_crowd(seed: int = 42) -> Dict[str, Any]:
    """I: 4-person crowd scalability across 4 distinct slots."""
    page = create_page(832, 1216, "manga page, monochrome, expressive linework, screentone shading", "color, photo, 3d render")
    page["scenes"].append(create_scene("Auditorium", "school stage presentation, curtains in background", input_mode="cast", area=make_area(0.05, 0.05, 0.90, 0.90), scene_id="sc1"))
    page["cast"].extend([get_cast_alice(), get_cast_bob(), get_cast_carol(), get_cast_dave()])
    page["character_instances"].append(create_character_instance("cast_alice", "sc1", area=make_area(0.05, 0.15, 0.20, 0.75), acting_prompt="standing cheerful", order=1, instance_id="inst_c1"))
    page["character_instances"].append(create_character_instance("cast_bob", "sc1", area=make_area(0.28, 0.15, 0.20, 0.75), acting_prompt="standing with notebook", order=2, instance_id="inst_c2"))
    page["character_instances"].append(create_character_instance("cast_carol", "sc1", area=make_area(0.51, 0.15, 0.20, 0.75), acting_prompt="standing energetic", order=3, instance_id="inst_c3"))
    page["character_instances"].append(create_character_instance("cast_dave", "sc1", area=make_area(0.74, 0.15, 0.20, 0.75), acting_prompt="standing with arms crossed", order=4, instance_id="inst_c4"))
    return create_document(pages=[page])


# Complete Capability Ladder Specification Table
CONDITIONS = [
    # Tier A: Single Character
    {"id": "A1_single_alice_left", "tier": "A_SINGLE_CHAR", "seed": 42, "fn": create_fixture_a1, "name": "A1 Alice Left (Seed 42)"},
    {"id": "A2_single_alice_right", "tier": "A_SINGLE_CHAR", "seed": 42, "fn": create_fixture_a2, "name": "A2 Alice Right (Seed 42)"},

    # Tier B: Two Distinct Characters (3 Seeds)
    {"id": "B_two_char_seed42", "tier": "B_TWO_CHAR", "seed": 42, "fn": create_fixture_b, "name": "B Two Characters (Seed 42)"},
    {"id": "B_two_char_seed101", "tier": "B_TWO_CHAR", "seed": 101, "fn": create_fixture_b, "name": "B Two Characters (Seed 101)"},
    {"id": "B_two_char_seed202", "tier": "B_TWO_CHAR", "seed": 202, "fn": create_fixture_b, "name": "B Two Characters (Seed 202)"},

    # Tier B2: Swap Oracle (Same seed 42)
    {"id": "B2_swap_oracle_seed42", "tier": "B2_SWAP_ORACLE", "seed": 42, "fn": create_fixture_b2_swap, "name": "B2 Swap Oracle (Seed 42)"},

    # Tier C / D: Depth 3-way
    {"id": "C1_depth_prompt_only", "tier": "C_DEPTH", "seed": 42, "fn": create_fixture_c1_depth_prompt, "name": "C1 Depth Prompt-Only (Seed 42)"},
    {"id": "C2_depth_geom_only", "tier": "C_DEPTH", "seed": 42, "fn": create_fixture_c2_depth_geometry, "name": "C2 Depth Geometry-Only (Seed 42)"},
    {"id": "C3_depth_combined", "tier": "C_DEPTH", "seed": 42, "fn": create_fixture_c3_depth_combined, "name": "C3 Depth Combined (Seed 42)"},

    # Tier E: Pose Diagnostic
    {"id": "E1_pose_standing", "tier": "E_POSE_DIAGNOSTIC", "seed": 42, "fn": create_fixture_e1_standing, "name": "E1 Pose Standing (Seed 42)"},
    {"id": "E2_pose_sitting", "tier": "E_POSE_DIAGNOSTIC", "seed": 42, "fn": create_fixture_e2_sitting, "name": "E2 Pose Sitting (Seed 42)"},

    # Tier F: Same CAST Across Scenes
    {"id": "F_same_cast_across_scenes", "tier": "F_ACROSS_SCENES", "seed": 42, "fn": create_fixture_f_across_scenes, "name": "F Same CAST Across 2 Scenes (Seed 42)"},

    # Tier G: Same CAST Twice (3 Seeds)
    {"id": "G_same_cast_twice_seed42", "tier": "G_SAME_CAST_TWICE", "seed": 42, "fn": create_fixture_g_same_cast_double, "name": "G Same CAST Twice (Seed 42)"},
    {"id": "G_same_cast_twice_seed101", "tier": "G_SAME_CAST_TWICE", "seed": 101, "fn": create_fixture_g_same_cast_double, "name": "G Same CAST Twice (Seed 101)"},
    {"id": "G_same_cast_twice_seed202", "tier": "G_SAME_CAST_TWICE", "seed": 202, "fn": create_fixture_g_same_cast_double, "name": "G Same CAST Twice (Seed 202)"},

    # Tier H: Same CAST + Other CAST 3-person (3 Seeds)
    {"id": "H_mixed_3person_seed42", "tier": "H_MIXED_3PERSON", "seed": 42, "fn": create_fixture_h_mixed_three_person, "name": "H Mixed 3-Person (Seed 42)"},
    {"id": "H_mixed_3person_seed101", "tier": "H_MIXED_3PERSON", "seed": 101, "fn": create_fixture_h_mixed_three_person, "name": "H Mixed 3-Person (Seed 101)"},
    {"id": "H_mixed_3person_seed202", "tier": "H_MIXED_3PERSON", "seed": 202, "fn": create_fixture_h_mixed_three_person, "name": "H Mixed 3-Person (Seed 202)"},

    # Tier I: Crowd Scalability
    {"id": "I_crowd_4person_seed42", "tier": "I_CROWD_4PERSON", "seed": 42, "fn": create_fixture_i_four_person_crowd, "name": "I Crowd 4-Person (Seed 42)"},
]


def create_labeled_cell(img: Image.Image, label_top: str, label_bottom: str, target_size=(380, 555)) -> Image.Image:
    """Resize image and add top title banner and bottom detail caption."""
    cell = Image.new("RGB", (target_size[0], target_size[1] + 60), (24, 26, 32))
    resized = img.resize(target_size, Image.Resampling.LANCZOS)
    cell.paste(resized, (0, 30))

    draw = ImageDraw.Draw(cell)
    try:
        font = ImageFont.load_default()
    except Exception:
        font = None

    # Top header bar
    draw.rectangle([0, 0, target_size[0], 28], fill=(38, 42, 54))
    draw.text((10, 7), label_top, fill=(240, 240, 240), font=font)

    # Bottom caption bar
    draw.rectangle([0, target_size[1] + 32, target_size[0], target_size[1] + 58], fill=(30, 34, 44))
    draw.text((10, target_size[1] + 38), label_bottom, fill=(180, 190, 210), font=font)

    return cell


def create_contact_sheet(
    cells: List[Tuple[Image.Image, str, str]],
    title: str,
    output_path: str,
    cols: int = 2
):
    """Build high-resolution multi-column contact sheet."""
    num_items = len(cells)
    rows = (num_items + cols - 1) // cols

    cell_w = 380
    cell_h = 555 + 60
    pad = 16
    title_h = 50

    sheet_w = cols * cell_w + (cols + 1) * pad
    sheet_h = rows * cell_h + (rows + 1) * pad + title_h

    sheet = Image.new("RGB", (sheet_w, sheet_h), (18, 20, 24))
    draw = ImageDraw.Draw(sheet)

    try:
        font = ImageFont.load_default()
    except Exception:
        font = None

    # Title header
    draw.rectangle([0, 0, sheet_w, title_h], fill=(28, 32, 42))
    draw.text((pad, 16), title, fill=(255, 255, 255), font=font)

    for idx, (img, top_lbl, bot_lbl) in enumerate(cells):
        r = idx // cols
        c = idx % cols
        cell_img = create_labeled_cell(img, top_lbl, bot_lbl, (cell_w, 555))
        x = pad + c * (cell_w + pad)
        y = title_h + pad + r * (cell_h + pad)
        sheet.paste(cell_img, (x, y))

    sheet.save(output_path)
    print(f"[ContactSheet] Saved: {output_path}")


def main():
    print("=================================================================")
    print("  M2A Character Spatial Capability Ladder Verification Runner    ")
    print("=================================================================")

    # 1. Ensure ComfyUI server is freshly started with updated custom nodes
    print("[Runner] Starting fresh ComfyUI server with updated custom nodes...")
    comfy_runtime_helper.restart_server(timeout=90)

    print(f"[Runner] Server is ready. Total test conditions: {len(CONDITIONS)}")

    manifest_entries = []
    generated_map = {}

    for idx, cond in enumerate(CONDITIONS):
        cid = cond["id"]
        tier = cond["tier"]
        seed = cond["seed"]
        name = cond["name"]
        print(f"\n--- [{idx+1}/{len(CONDITIONS)}] Running Condition: {cid} ({name}) ---")

        doc = cond["fn"](seed=seed)
        page = doc["pages"][0]

        # Generate & save mask preview
        preview_img = generate_scene_regions_preview_image(doc, width=832, height=1216)
        preview_path = os.path.join(DOCS_DIR, f"{cid}_preview.png")
        preview_img.save(preview_path)

        # Build prompt workflow
        prompt = build_m2a_prompt_workflow(doc, seed=seed, prefix=cid)

        # Queue prompt
        t0 = time.time()
        resp = comfy_runtime_helper.queue_prompt(prompt)
        prompt_id = resp["prompt_id"]
        print(f"[Runner] Queued prompt {prompt_id}. Waiting for execution...")

        try:
            outputs = comfy_runtime_helper.wait_for_prompt(prompt_id, timeout=240)
            elapsed = time.time() - t0

            # Resolve output file
            raw_path = comfy_runtime_helper.get_image_file_path(outputs, "7")
            if not raw_path or not os.path.exists(raw_path):
                raise RuntimeError(f"Output image for {cid} not found in outputs!")

            # Copy to docs/manga/verification/m2a/
            doc_img_path = os.path.join(DOCS_DIR, f"{cid}.png")
            shutil.copyfile(raw_path, doc_img_path)
            print(f"[Runner] Condition {cid} completed in {elapsed:.1f}s -> Saved: {doc_img_path}")
        except Exception as ex:
            elapsed = time.time() - t0
            print(f"[ERROR] Condition {cid} failed: {ex}")
            manifest_entries.append({
                "condition_id": cid,
                "tier": tier,
                "name": name,
                "seed": seed,
                "runtime_status": "FAIL",
                "visual_status": "FAIL",
                "review_method": "RUNTIME_FAILURE",
                "elapsed_seconds": round(elapsed, 2),
                "error": str(ex),
            })
            continue

        generated_map[cid] = {
            "image_path": doc_img_path,
            "preview_path": preview_path,
            "raw_path": raw_path,
            "elapsed": elapsed,
        }

        manifest_entries.append({
            "condition_id": cid,
            "tier": tier,
            "name": name,
            "seed": seed,
            "scenes": [s.get("name") for s in page.get("scenes", [])],
            "cast": [c.get("display_name") for c in page.get("cast", [])],
            "instances": [
                {
                    "instance_id": i.get("instance_id"),
                    "cast_id": i.get("cast_id"),
                    "area": i.get("area"),
                    "acting_prompt": i.get("acting_prompt"),
                }
                for i in page.get("character_instances", [])
            ],
            "runtime_status": "PASS",
            "visual_status": "PENDING_INSPECTION",
            "review_method": "DIRECT_IMAGE_INSPECTION",
            "output_path": f"docs/manga/verification/m2a/{cid}.png",
            "preview_path": f"docs/manga/verification/m2a/{cid}_preview.png",
            "elapsed_seconds": round(elapsed, 2),
        })

    # Save initial Manifest
    manifest_file = os.path.join(DOCS_DIR, "M2A_CAPABILITY_MANIFEST.json")
    with open(manifest_file, "w", encoding="utf-8") as f:
        json.dump({
            "milestone": "M2A",
            "title": "M2A Character Spatial Capability Ladder Manifest",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "checkpoint": CKPT_NAME,
            "conditions_total": len(CONDITIONS),
            "conditions_completed": len(generated_map),
            "entries": manifest_entries
        }, f, indent=2, ensure_ascii=False)
    print(f"\n[Manifest] Saved initial manifest to: {manifest_file}")

    # 2. Generate Contact Sheets
    print("\n[ContactSheets] Generating Oracle Contact Sheets...")

    # Sheet 1: M2A_TWO_CHARACTER_ORACLE.png (A1, A2, B, B2 Swap)
    cells_oracle = []
    for cid in ["A1_single_alice_left", "A2_single_alice_right", "B_two_char_seed42", "B2_swap_oracle_seed42"]:
        if cid in generated_map:
            img = Image.open(generated_map[cid]["image_path"])
            prev = Image.open(generated_map[cid]["preview_path"])
            cells_oracle.append((prev, f"[{cid}] REGION PREVIEW", "Translucent blueprint"))
            cells_oracle.append((img, f"[{cid}] GENERATION", "Euler 20st / Seed 42"))
    if cells_oracle:
        sheet1_path = os.path.join(DOCS_DIR, "M2A_TWO_CHARACTER_ORACLE.png")
        create_contact_sheet(cells_oracle, "M2A Two-Character & Spatial Swap Oracle Sheet", sheet1_path, cols=4)

    # Sheet 2: M2A_DEPTH_ORACLE.png (C1 Prompt vs C2 Geometry vs C3 Combined)
    cells_depth = []
    for cid in ["C1_depth_prompt_only", "C2_depth_geom_only", "C3_depth_combined"]:
        if cid in generated_map:
            img = Image.open(generated_map[cid]["image_path"])
            prev = Image.open(generated_map[cid]["preview_path"])
            cells_depth.append((prev, f"[{cid}] PREVIEW", "Region bounds"))
            cells_depth.append((img, f"[{cid}] GENERATION", "Seed 42"))
    if cells_depth:
        sheet2_path = os.path.join(DOCS_DIR, "M2A_DEPTH_ORACLE.png")
        create_contact_sheet(cells_depth, "M2A Depth 3-Way Comparison Oracle Sheet (Prompt vs Geom vs Comb)", sheet2_path, cols=2)

    # Sheet 3: M2A_REPEATED_CAST_ORACLE.png (F across scenes, G same cast twice, H mixed 3-person)
    cells_repeated = []
    for cid in ["F_same_cast_across_scenes", "G_same_cast_twice_seed42", "H_mixed_3person_seed42", "E2_pose_sitting"]:
        if cid in generated_map:
            img = Image.open(generated_map[cid]["image_path"])
            cells_repeated.append((img, f"[{cid}]", "Seed 42"))
    if cells_repeated:
        sheet3_path = os.path.join(DOCS_DIR, "M2A_REPEATED_CAST_ORACLE.png")
        create_contact_sheet(cells_repeated, "M2A Repeated CAST & Mixed Composition Sheet", sheet3_path, cols=2)

    # Sheet 4: M2A_CROWD_ORACLE.png (B seed variation, G seed variation, H seed variation, I 4-person)
    cells_crowd = []
    for cid in ["B_two_char_seed101", "B_two_char_seed202", "G_same_cast_twice_seed101", "G_same_cast_twice_seed202", "H_mixed_3person_seed101", "H_mixed_3person_seed202", "I_crowd_4person_seed42"]:
        if cid in generated_map:
            img = Image.open(generated_map[cid]["image_path"])
            cells_crowd.append((img, f"[{cid}]", "Seed variation / Crowd"))
    if cells_crowd:
        sheet4_path = os.path.join(DOCS_DIR, "M2A_CROWD_ORACLE.png")
        create_contact_sheet(cells_crowd, "M2A Multi-Seed Robustness & 4-Person Crowd Sheet", sheet4_path, cols=2)

    print("\n=================================================================")
    print("  M2A Character Spatial Capability Runner FINISHED SUCCESSFUL   ")
    print(f"  Generated images: {len(generated_map)}/{len(CONDITIONS)}")
    print(f"  Output directory: {DOCS_DIR}")
    print("=================================================================")


if __name__ == "__main__":
    main()
