"""
run_controlnet_escalation.py — Execute ControlNet Escalation conditions
======================================================================
Runs weak block guide ControlNet (0.20, 0.35) for seeds 101 and 202 on Benchmark H (3-person),
generates M2A1_BLOCK_CONTROL_ESCALATION.png, and updates M2A1_CALIBRATION_MANIFEST.json.
"""
import os
import sys
import json
import time
import shutil
from typing import Dict, Any, List
from PIL import Image

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DOCS_DIR = os.path.join(ROOT_DIR, "docs", "manga", "verification", "m2a1")
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from scripts import comfy_runtime_helper
from scripts.run_m2a1_prompt_region_calibration import (
    build_prompt_workflow,
    create_h_document,
    create_contact_sheet,
    generate_scene_regions_preview_image,
)

def main():
    print("[ControlNetEscalation] Ensuring server is running...")
    comfy_runtime_helper.ensure_server(timeout=90)
    print("[ControlNetEscalation] Running ControlNet escalation suite...")
    cn_tasks = [
        {"id": "H_CN020_s101", "base_id": "H2_presence_s101", "seed": 101, "ctrl": 0.20},
        {"id": "H_CN035_s101", "base_id": "H2_presence_s101", "seed": 101, "ctrl": 0.35},
        {"id": "H_CN020_s202", "base_id": "H2_presence_s202", "seed": 202, "ctrl": 0.20},
        {"id": "H_CN035_s202", "base_id": "H2_presence_s202", "seed": 202, "ctrl": 0.35},
    ]

    doc = create_h_document()
    manifest_path = os.path.join(DOCS_DIR, "M2A1_CALIBRATION_MANIFEST.json")
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    for item in cn_tasks:
        cid = item["id"]
        seed = item["seed"]
        ctrl = item["ctrl"]
        print(f" -> Running {cid} (ctrl={ctrl}, seed={seed})...")

        wf = build_prompt_workflow(doc, seed, prefix=cid, spatial_hint_mode="horizontal_presence", control_strength=ctrl)
        t0 = time.time()
        res = comfy_runtime_helper.queue_prompt(wf)
        prompt_id = res["prompt_id"]
        outputs = comfy_runtime_helper.wait_for_prompt(prompt_id, timeout=120)
        elapsed = time.time() - t0

        raw_path = comfy_runtime_helper.get_image_file_path(outputs, "7")
        final_path = os.path.join(DOCS_DIR, f"{cid}.png")
        shutil.copyfile(raw_path, final_path)
        print(f"    Completed in {elapsed:.1f}s -> {final_path}")

        manifest["entries"].append({
            "condition_id": cid,
            "suite": "ControlNet",
            "seed": seed,
            "hint_mode": "horizontal_presence",
            "control_strength": ctrl,
            "runtime_status": "PASS",
            "visual_status": "PENDING_INSPECTION",
            "review_method": "DIRECT_IMAGE_INSPECTION",
            "elapsed_seconds": round(elapsed, 2),
            "output_path": f"docs/manga/verification/m2a1/{cid}.png",
        })

    manifest["conditions_total"] = len(manifest["entries"])
    manifest["conditions_completed"] = len([e for e in manifest["entries"] if e.get("runtime_status") == "PASS"])
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    print(f"[Manifest] Updated {manifest_path}")

    # Build M2A1_BLOCK_CONTROL_ESCALATION.png
    cells_cn = []
    for seed in [101, 202]:
        base_id = f"H2_presence_s{seed}"
        cn020_id = f"H_CN020_s{seed}"
        cn035_id = f"H_CN035_s{seed}"

        prev_path = os.path.join(DOCS_DIR, f"{base_id}_preview.png")
        base_path = os.path.join(DOCS_DIR, f"{base_id}.png")
        cn020_path = os.path.join(DOCS_DIR, f"{cn020_id}.png")
        cn035_path = os.path.join(DOCS_DIR, f"{cn035_id}.png")

        if os.path.exists(prev_path) and os.path.exists(base_path) and os.path.exists(cn020_path) and os.path.exists(cn035_path):
            prev = Image.open(prev_path)
            img_base = Image.open(base_path)
            img_020 = Image.open(cn020_path)
            img_035 = Image.open(cn035_path)

            cells_cn.append((prev, f"Preview s{seed}", "Staging bounds"))
            cells_cn.append((img_base, f"Prompt-only s{seed}", "H2 Presence"))
            cells_cn.append((img_020, f"Block CN 0.20 s{seed}", "Weak guide"))
            cells_cn.append((img_035, f"Block CN 0.35 s{seed}", "Medium guide"))

    if cells_cn:
        sheet_cn_path = os.path.join(DOCS_DIR, "M2A1_BLOCK_CONTROL_ESCALATION.png")
        create_contact_sheet(cells_cn, "M2A.1 ControlNet Escalation Comparison (Prompt-Only vs Block CN 0.20 vs Block CN 0.35)", sheet_cn_path, cols=4, thumb_w=240, thumb_h=350)

    print("[ControlNetEscalation] Complete!")

if __name__ == "__main__":
    main()
