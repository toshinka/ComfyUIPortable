"""
run_m2b_product_verification.py — M2B Product Path Verification Runner
======================================================================
Executes runtime conditions on ComfyUI standalone runtime to produce:
1. M2B_single_char.png (Single character in classroom, auto hint: off)
2. M2B_two_char_seed202.png (Alice left, Bob right, auto hint: horizontal)
3. M2B_depth_seed404.png (Alice foreground, Bob background, auto hint: spatial_depth)
4. M2B_same_cast_multi_scene.png (Alice across 2 scenes, auto hint: off)

Also generates UI preview artifacts and docs/manga/verification/m2b/M2B_PRODUCT_PATH_MANIFEST.json.
"""
import os
import sys
import json
import time
import shutil
from typing import Dict, Any, List
from PIL import Image

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
_shc = _import_submodule("spatial_hint_compiler", "spatial_hint_compiler.py")
_aeb = _import_submodule("authoring_execution_bridge", "authoring_execution_bridge.py")

create_document = _ac.create_document
create_page = _ac.create_page
create_scene = _ac.create_scene
create_cast_entry = _ac.create_cast_entry
create_character_instance = _ac.create_character_instance
make_area = _ac.make_area
compile_document_to_page_plan = _aeb.compile_document_to_page_plan
generate_scene_regions_preview_image = _aeb.generate_scene_regions_preview_image
get_execution_debug_info = _aeb.get_execution_debug_info

CKPT_NAME = r"♃CN_Skeb\waiIllustriousSDXL_v170.safetensors"
OUT_DIR = os.path.join(ROOT_DIR, "docs", "manga", "verification", "m2b")
os.makedirs(OUT_DIR, exist_ok=True)


def build_workflow(doc: Dict[str, Any], seed: int, prefix: str) -> Dict[str, Any]:
    page = doc["pages"][0]
    w = int(page.get("width_px", 832))
    h = int(page.get("height_px", 1216))

    return {
        "1": {
            "class_type": "TegakiMinimumHandSceneEditor",
            "inputs": {
                "document_json": json.dumps(doc),
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
                "filename_prefix": f"Tegaki/M2B/{prefix}"
            }
        }
    }


def make_single_char_doc() -> Dict[str, Any]:
    page = create_page(width_px=832, height_px=1216)
    alice = create_cast_entry("Alice", "1girl, blonde hair, twin tails, blue eyes, sailor uniform, school skirt", cast_id="c_alice")
    page["cast"] = [alice]
    s1 = create_scene("Scene 1", "school classroom, desks and chairs, window, daylight", area=make_area(0.08, 0.08, 0.84, 0.84), scene_id="s1", input_mode="cast")
    page["scenes"] = [s1]
    inst = create_character_instance("c_alice", "s1", make_area(0.15, 0.15, 0.35, 0.70), acting_prompt="standing casually, looking at viewer", instance_id="inst_1")
    page["character_instances"] = [inst]
    return create_document(pages=[page])


def make_two_char_doc() -> Dict[str, Any]:
    page = create_page(width_px=832, height_px=1216)
    alice = create_cast_entry("Alice", "1girl, blonde hair, twin tails, blue eyes, sailor uniform, school skirt", cast_id="c_alice")
    bob = create_cast_entry("Bob", "1boy, short black hair, school uniform, necktie, blazer", cast_id="c_bob")
    page["cast"] = [alice, bob]
    s1 = create_scene("Scene 1", "school classroom, desks and chairs, window, daylight", area=make_area(0.08, 0.08, 0.84, 0.84), scene_id="s1", input_mode="cast")
    page["scenes"] = [s1]
    inst1 = create_character_instance("c_alice", "s1", make_area(0.12, 0.15, 0.32, 0.70), acting_prompt="standing casually, looking at viewer", instance_id="inst_1")
    inst2 = create_character_instance("c_bob", "s1", make_area(0.56, 0.15, 0.32, 0.70), acting_prompt="reading a book at desk", instance_id="inst_2")
    page["character_instances"] = [inst1, inst2]
    return create_document(pages=[page])


def make_depth_doc() -> Dict[str, Any]:
    page = create_page(width_px=832, height_px=1216)
    alice = create_cast_entry("Alice", "1girl, blonde hair, twin tails, blue eyes, sailor uniform, school skirt", cast_id="c_alice")
    bob = create_cast_entry("Bob", "1boy, short black hair, school uniform, necktie, blazer", cast_id="c_bob")
    page["cast"] = [alice, bob]
    s1 = create_scene("Scene 1", "school hallway, lockers, perspective view", area=make_area(0.08, 0.08, 0.84, 0.84), scene_id="s1", input_mode="cast")
    page["scenes"] = [s1]
    # Area ratio: 0.44 * 0.75 = 0.33 vs 0.18 * 0.30 = 0.054 -> ratio = 6.1 >= 1.8
    inst1 = create_character_instance("c_alice", "s1", make_area(0.10, 0.18, 0.44, 0.75), acting_prompt="standing in corridor", instance_id="inst_1")
    inst2 = create_character_instance("c_bob", "s1", make_area(0.68, 0.22, 0.18, 0.30), acting_prompt="walking away down the corridor", instance_id="inst_2")
    page["character_instances"] = [inst1, inst2]
    return create_document(pages=[page])


def make_multi_scene_doc() -> Dict[str, Any]:
    page = create_page(width_px=832, height_px=1216)
    alice = create_cast_entry("Alice", "1girl, blonde hair, twin tails, blue eyes, sailor uniform, school skirt", cast_id="c_alice")
    page["cast"] = [alice]
    s1 = create_scene("Scene 1", "school library, bookshelves, quiet study desk", area=make_area(0.08, 0.06, 0.84, 0.42), scene_id="s1", input_mode="cast")
    s2 = create_scene("Scene 2", "outdoor park, cherry blossoms, bench", area=make_area(0.08, 0.52, 0.84, 0.42), scene_id="s2", input_mode="cast")
    page["scenes"] = [s1, s2]
    inst1 = create_character_instance("c_alice", "s1", make_area(0.25, 0.12, 0.50, 0.32), acting_prompt="reading a book quietly", instance_id="inst_s1")
    inst2 = create_character_instance("c_alice", "s2", make_area(0.25, 0.58, 0.50, 0.32), acting_prompt="walking under trees, smiling", instance_id="inst_s2")
    page["character_instances"] = [inst1, inst2]
    return create_document(pages=[page])


def main():
    print("=== M2B Product Path Verification Runner ===")
    comfy_runtime_helper.ensure_server(timeout=90)

    # 1. Generate UI Preview images
    doc_simple = make_single_char_doc()
    img_simple = generate_scene_regions_preview_image(doc_simple)
    img_simple.save(os.path.join(OUT_DIR, "M2B_UI_SIMPLE.png"))

    doc_two = make_two_char_doc()
    img_two = generate_scene_regions_preview_image(doc_two)
    img_two.save(os.path.join(OUT_DIR, "M2B_UI_TWO_CAST.png"))

    doc_multi = make_multi_scene_doc()
    img_multi = generate_scene_regions_preview_image(doc_multi)
    img_multi.save(os.path.join(OUT_DIR, "M2B_UI_REPEATED_CAST.png"))
    print("✓ Saved UI layout previews.")

    tasks = [
        ("M2B_single_char", make_single_char_doc(), 42, "M2B_single_char.png"),
        ("M2B_two_char_seed202", make_two_char_doc(), 202, "M2B_two_char_seed202.png"),
        ("M2B_depth_seed404", make_depth_doc(), 404, "M2B_depth_seed404.png"),
        ("M2B_same_cast_multi_scene", make_multi_scene_doc(), 42, "M2B_same_cast_multi_scene.png"),
    ]

    manifest_entries = []

    for prefix, doc, seed, target_fname in tasks:
        print(f"\n--- Running Task: {prefix} (Seed {seed}) ---")
        debug_info = get_execution_debug_info(doc, seed=seed, spatial_hint_mode="auto")
        plan = compile_document_to_page_plan(doc, spatial_hint_mode="auto")

        resolved_hints = {}
        for p in plan.get("panels", []):
            for c in p.get("characters", []):
                resolved_hints[c["instance_id"]] = {
                    "derived_spatial_hint": c["derived_spatial_hint"],
                    "effective_character_prompt": c["effective_character_prompt"],
                    "resolved_mode": c["derived_hints_metadata"].get("resolved_mode", "auto"),
                }

        wf = build_workflow(doc, seed, prefix)
        queue_res = comfy_runtime_helper.queue_prompt(wf)
        pid = queue_res["prompt_id"]
        print(f"Queued prompt: {pid}")
        outputs = comfy_runtime_helper.wait_for_prompt(pid, timeout=180)

        # Locate output image
        img_path = comfy_runtime_helper.get_image_file_path(outputs, "7")
        if not img_path or not os.path.exists(img_path):
            raise RuntimeError(f"Output image for {prefix} not found: {img_path}")

        dest_file = os.path.join(OUT_DIR, target_fname)
        shutil.copy2(img_path, dest_file)
        print(f"✓ Saved {dest_file}")

        manifest_entries.append({
            "task_id": prefix,
            "filename": target_fname,
            "seed": seed,
            "runtime_status": "PASS",
            "visual_status": "DIRECT_IMAGE_INSPECTION",
            "scene_count": len(doc["pages"][0]["scenes"]),
            "cast_count": len(doc["pages"][0]["cast"]),
            "instance_count": len(doc["pages"][0]["character_instances"]),
            "resolved_hints": resolved_hints,
            "auto_spatial_policy": debug_info.get("spatial_policy", "auto"),
        })

    manifest = {
        "milestone": "M2B",
        "description": "Minimum-Hand CAST and Character Staging Product UI Verification",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "checkpoint": CKPT_NAME,
        "controlnet_core": "OFF",
        "tasks": manifest_entries,
    }

    manifest_path = os.path.join(OUT_DIR, "M2B_PRODUCT_PATH_MANIFEST.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    print(f"\n✓ Saved manifest to {manifest_path}")
    print("=== M2B Verification Run Complete! ===")


if __name__ == "__main__":
    main()
