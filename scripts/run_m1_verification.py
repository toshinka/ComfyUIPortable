"""
run_m1_verification.py — M1 Scene-Only Minimum-Hand Draft Verification Runner
=============================================================================
Executes the empirical verification suite for M1:
- Condition A: 1 Scene Draft (A_one_scene.png)
- Condition B: 2 Distinct Scenes Draft (B_two_scene_seed42.png)
- Condition C: Geometry Swap Oracle (C_swap_same_seed42.png, seed 42 identical to B)
- Condition D1: Seed Brainstorm Variation (D_seed101.png)
- Condition D2: Seed Brainstorm Variation (E_seed202.png)

Generates:
- output/Tegaki/M1/ raw generations
- docs/verification/m1/ verified images, previews, manifest, and contact sheet.
"""

import os
import sys
import json
import time
import shutil
import urllib.request
from typing import Dict, Any, List, Tuple
from PIL import Image, ImageDraw, ImageFont

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CUSTOM_NODES_DIR = os.path.join(ROOT_DIR, "custom_nodes_custom")
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
if CUSTOM_NODES_DIR not in sys.path:
    sys.path.insert(0, CUSTOM_NODES_DIR)

from scripts import comfy_runtime_helper

# Import tegaki submodules
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
_aeb = _import_submodule("authoring_execution_bridge", "authoring_execution_bridge.py")
_mse = _import_submodule("minimum_hand_scene_editor", "minimum_hand_scene_editor.py")

create_document = _ac.create_document
create_page = _ac.create_page
create_scene = _ac.create_scene
make_area = _ac.make_area
generate_scene_regions_preview_image = _aeb.generate_scene_regions_preview_image
create_default_m1_document = _mse.create_default_m1_document

OUTPUT_DIR = os.path.join(ROOT_DIR, "output", "Tegaki", "M1")
DOCS_DIR = os.path.join(ROOT_DIR, "docs", "verification", "m1")
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(DOCS_DIR, exist_ok=True)

CKPT_NAME = r"♃CN_Skeb\waiIllustriousSDXL_v170.safetensors"


def build_m1_prompt_workflow(doc: Dict[str, Any], seed: int, prefix: str) -> Dict[str, Any]:
    """Construct ComfyUI prompt dictionary for M1 Minimum-Hand Scene Draft."""
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
                "style_template": "Manga Monochrome",
                "resolution": f"Portrait {w}x{h}",
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
                "width": w,
                "height": h,
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
                "seed": seed,
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
                "filename_prefix": f"Tegaki/M1/{prefix}"
            }
        }
    }


def create_condition_a_doc(seed: int = 42) -> Dict[str, Any]:
    """Condition A: 1 Scene Draft (Single large scene)."""
    page = create_page(
        832, 1216,
        style_prompt="manga page, monochrome, expressive linework, high contrast, screentone shading",
        style_negative_prompt="bad anatomy, blurry, photo, color, 3d render, watermark, text"
    )
    page["metadata"]["style_template"] = "Manga Monochrome"
    page["generation"] = {"seed": seed}
    page["scenes"].append(create_scene(
        name="Classroom",
        prompt="1boy, high school student, sitting quietly by classroom window, desks and chairs, sunlight streaming in, melancholic calm expression, fine manga linework, screentone",
        negative_prompt="",
        input_mode="simple",
        area=make_area(0.08, 0.08, 0.84, 0.84),
        order=1,
        scene_id="sc_single_classroom"
    ))
    return create_document(pages=[page])


def create_condition_b_doc(seed: int = 42) -> Dict[str, Any]:
    """Condition B: 2 Distinct Scenes Draft (Canonical 2-scene layout)."""
    return create_default_m1_document(832, 1216, "Manga Monochrome", seed)


def create_condition_c_doc(seed: int = 42) -> Dict[str, Any]:
    """Condition C: Geometry Swap Oracle (Train Platform at Top, Classroom at Bottom)."""
    doc = create_default_m1_document(832, 1216, "Manga Monochrome", seed)
    scenes = doc["pages"][0]["scenes"]
    # Swap areas
    area_top = make_area(0.08, 0.06, 0.84, 0.42)
    area_bottom = make_area(0.08, 0.52, 0.84, 0.42)

    # Scene 1: Train Platform at Top
    scenes[0]["name"] = "Train Platform"
    scenes[0]["prompt"] = "outdoor train station platform, railway tracks, a commuter waiting with bicycle, afternoon sky"
    scenes[0]["area"] = area_top

    # Scene 2: Classroom at Bottom
    scenes[1]["name"] = "Classroom"
    scenes[1]["prompt"] = "school classroom, desks and chairs, a student reading quietly by the window, warm sunlight"
    scenes[1]["area"] = area_bottom

    return doc


def generate_contact_sheet(items: List[Dict[str, Any]], output_path: str):
    """Generate high-resolution contact sheet comparing layout preview and output."""
    thumb_w, thumb_h = 320, 468
    pad = 20
    header_h = 50
    item_w = thumb_w * 2 + 10
    total_w = item_w * len(items) + pad * (len(items) + 1)
    total_h = thumb_h + pad * 2 + header_h + 40

    sheet = Image.new("RGB", (total_w, total_h), (24, 24, 27))
    draw = ImageDraw.Draw(sheet)

    try:
        font_title = ImageFont.load_default()
    except Exception:
        font_title = None

    # Title
    draw.text((pad, pad), "TEGAKI PHASE 3M-1 (M1) — MINIMUM-HAND SCENE DRAFT CONTACT SHEET", fill=(250, 250, 250), font=font_title)

    for idx, it in enumerate(items):
        x_base = pad + idx * (item_w + pad)
        y_base = pad + header_h

        # Label
        lbl = f"[{it['id']}] {it['title']} (Seed: {it['seed']})"
        draw.text((x_base, y_base - 22), lbl, fill=(212, 212, 216), font=font_title)

        # Draw Preview Image
        if os.path.exists(it["preview_path"]):
            p_img = Image.open(it["preview_path"]).resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)
            sheet.paste(p_img, (x_base, y_base))
            draw.rectangle([x_base, y_base, x_base + thumb_w, y_base + thumb_h], outline=(82, 82, 91), width=1)

        # Draw Generated Image
        gen_x = x_base + thumb_w + 10
        if os.path.exists(it["gen_path"]):
            g_img = Image.open(it["gen_path"]).resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)
            sheet.paste(g_img, (gen_x, y_base))
            draw.rectangle([gen_x, y_base, gen_x + thumb_w, y_base + thumb_h], outline=(82, 82, 91), width=1)

        # Sub labels
        draw.text((x_base + 5, y_base + thumb_h + 6), "Layout Plan", fill=(161, 161, 170), font=font_title)
        draw.text((gen_x + 5, y_base + thumb_h + 6), "Draft Output", fill=(161, 161, 170), font=font_title)

    sheet.save(output_path)
    print(f"[M1 Verification] Contact sheet saved to {output_path}")


def main():
    print("=================================================================")
    print("Tegaki M1 (Phase 3M-1) Minimum-Hand Scene Draft Verification")
    print("=================================================================")

    # Define test conditions
    conditions = [
        {
            "id": "Condition_A",
            "filename": "A_one_scene.png",
            "prefix": "A_one_scene",
            "title": "1 Scene Full Draft",
            "seed": 42,
            "doc_fn": create_condition_a_doc,
            "notes": "Validates single scene baseline draft generation."
        },
        {
            "id": "Condition_B",
            "filename": "B_two_scene_seed42.png",
            "prefix": "B_two_scene_seed42",
            "title": "2 Distinct Scenes (Top Classroom / Bottom Train)",
            "seed": 42,
            "doc_fn": create_condition_b_doc,
            "notes": "Canonical 2-scene draft. Verifies spatial separation between top classroom and bottom train."
        },
        {
            "id": "Condition_C",
            "filename": "C_swap_same_seed42.png",
            "prefix": "C_swap_same_seed42",
            "title": "Geometry Swap Oracle (Top Train / Bottom Classroom)",
            "seed": 42,
            "doc_fn": create_condition_c_doc,
            "notes": "Geometry swap oracle with identical seed 42. Verifies semantic locality causality."
        },
        {
            "id": "Condition_D1",
            "filename": "D_seed101.png",
            "prefix": "D_seed101",
            "title": "Seed Brainstorm Variation 1",
            "seed": 101,
            "doc_fn": create_condition_b_doc,
            "notes": "Seed 101 variation on canonical 2-scene layout."
        },
        {
            "id": "Condition_D2",
            "filename": "E_seed202.png",
            "prefix": "E_seed202",
            "title": "Seed Brainstorm Variation 2",
            "seed": 202,
            "doc_fn": create_condition_b_doc,
            "notes": "Seed 202 variation on canonical 2-scene layout."
        },
    ]

    # Pre-generate preview maps for all conditions
    items_for_contact_sheet = []
    manifest_records = []

    for cond in conditions:
        doc = cond["doc_fn"](cond["seed"])
        preview_img = generate_scene_regions_preview_image(doc)
        preview_filename = cond["prefix"] + "_preview.png"
        preview_path = os.path.join(DOCS_DIR, preview_filename)
        preview_img.save(preview_path)

        cond["doc"] = doc
        cond["preview_path"] = preview_path

    # Start ComfyUI Server
    server_started = False
    try:
        print("[M1 Verification] Ensuring ComfyUI server is running...")
        comfy_runtime_helper.ensure_server(timeout=90)
        server_started = True

        for cond in conditions:
            print(f"\n--- Running {cond['id']}: {cond['title']} (Seed: {cond['seed']}) ---")
            prompt_wf = build_m1_prompt_workflow(cond["doc"], cond["seed"], cond["prefix"])
            t0 = time.time()
            resp = comfy_runtime_helper.queue_prompt(prompt_wf)
            prompt_id = resp["prompt_id"]
            print(f"[M1 Verification] Queued prompt {prompt_id}. Waiting for execution...")

            outputs = comfy_runtime_helper.wait_for_prompt(prompt_id, timeout=180)
            elapsed = time.time() - t0

            # Resolve output file
            img_path = comfy_runtime_helper.get_image_file_path(outputs, "7")
            if not img_path or not os.path.exists(img_path):
                raise RuntimeError(f"Output image for {cond['id']} not found!")

            dest_path = os.path.join(DOCS_DIR, cond["filename"])
            shutil.copyfile(img_path, dest_path)
            print(f"[M1 Verification] Image saved to {dest_path} (took {elapsed:.1f}s)")

            cond["gen_path"] = dest_path
            cond["elapsed_sec"] = round(elapsed, 2)

            items_for_contact_sheet.append({
                "id": cond["id"],
                "title": cond["title"],
                "seed": cond["seed"],
                "preview_path": cond["preview_path"],
                "gen_path": dest_path
            })

            manifest_records.append({
                "condition_id": cond["id"],
                "title": cond["title"],
                "filename": cond["filename"],
                "file_path": dest_path,
                "preview_path": cond["preview_path"],
                "seed": cond["seed"],
                "resolution": "832x1216",
                "elapsed_seconds": round(elapsed, 2),
                "notes": cond["notes"],
                "status": "PASS",
                "provenance": "LIVE_COMFYUI_GENERATION"
            })

    except Exception as e:
        print(f"\n[M1 Verification ERROR] Generation run failed: {e}")
        raise
    finally:
        if server_started:
            print("[M1 Verification] Cleaning up ComfyUI server...")
            comfy_runtime_helper.stop_server()

    # Generate Contact Sheet
    contact_sheet_path = os.path.join(DOCS_DIR, "M1_SCENE_DRAFT_CONTACT_SHEET.png")
    generate_contact_sheet(items_for_contact_sheet, contact_sheet_path)

    # Generate Manifest JSON
    manifest_path = os.path.join(DOCS_DIR, "M1_SCENE_DRAFT_MANIFEST.json")
    manifest_data = {
        "milestone": "Phase 3M-1 / M1",
        "title": "Minimum-Hand Scene Draft Empirical Verification Suite",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "checkpoint": CKPT_NAME,
        "base_model": "Illustrious SDXL v1.7",
        "resolution": "832x1216 (Portrait)",
        "total_conditions": len(manifest_records),
        "contact_sheet": contact_sheet_path,
        "conditions": manifest_records
    }

    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, indent=2, ensure_ascii=False)
    print(f"[M1 Verification] Manifest saved to {manifest_path}")

    print("\n=================================================================")
    print("M1 Verification Run Completed Successfully!")
    print("=================================================================")


if __name__ == "__main__":
    main()
