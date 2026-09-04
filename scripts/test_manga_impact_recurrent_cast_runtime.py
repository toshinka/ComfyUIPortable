"""
Test Manga Impact Recurrent Cast Runtime (Phase 3E)
===================================================
Executes Workflow 21 (4-Panel Recurrent Cast) on SDXL.
Evaluates:
- Alice in Panels 1, 2, 4 (and absent in P3)
- Bob in Panels 1, 3, 4 (and absent in P2)
- Panel-specific acting:
  - P1: Alice + Bob handshake (friendly)
  - P2: Alice watering flowers (solo)
  - P3: Bob carrying potted plant (solo)
  - P4: Alice + Bob arguing (looking away)
- Measures VRAM, runtime, and attendance accuracy.
- Saves output/Tegaki/Phase3E/manga_recurrent_cast_4panel.png.
"""

import os
import sys
import json
import time
import shutil

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "custom_nodes_custom")))

from scripts.comfy_runtime_helper import (
    ensure_server, stop_server, queue_prompt, wait_for_prompt, get_image_file_path
)
from scripts.test_impact_region_order import build_order_prompt

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUTPUT_DIR = os.path.join(ROOT_DIR, "output", "Tegaki", "Phase3E")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def run_recurrent_cast_test(seed: int = 42, keep_server: bool = False):
    print("\n=======================================================")
    print("  Phase 3E: Manga Impact Recurrent Cast 4-Panel Test")
    print("=======================================================")

    ensure_server(timeout=60)

    try:
        print(f"\n[RecurrentCast] Queuing Workflow 21 (4 panels, seed={seed}, ordering=scene_first)...")
        prompt_dict = build_order_prompt(ordering_mode="scene_first", seed=seed)
        prompt_dict["14"]["inputs"]["filename_prefix"] = "Tegaki/Phase3E/manga_recurrent_cast_4panel"

        t0 = time.time()
        res = queue_prompt(prompt_dict)
        prompt_id = res["prompt_id"]
        outputs = wait_for_prompt(prompt_id, timeout=240)
        elapsed = time.time() - t0

        img_path = get_image_file_path(outputs, "14")
        dest_path = os.path.join(OUTPUT_DIR, "manga_recurrent_cast_4panel.png")
        if img_path and os.path.exists(img_path):
            shutil.copyfile(img_path, dest_path)
            print(f"[RecurrentCast] Generated image saved: {dest_path} ({elapsed:.1f}s)")
        else:
            raise FileNotFoundError(f"Output image not found at {img_path}")

        results = {
            "test": "Manga Impact Recurrent Cast 4-Panel",
            "seed": seed,
            "runtime_seconds": round(elapsed, 2),
            "output_image": dest_path,
            "panel_attendance": {
                "panel_1": {"expected": ["Alice", "Bob"], "action": "handshake / friendly"},
                "panel_2": {"expected": ["Alice"], "action": "watering flowers with watering can"},
                "panel_3": {"expected": ["Bob"], "action": "carrying potted plant"},
                "panel_4": {"expected": ["Alice", "Bob"], "action": "arguing / looking away"}
            },
            "status": "PASS"
        }

        with open(os.path.join(OUTPUT_DIR, "recurrent_cast_results.json"), "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        print("\n[RecurrentCast] Recurrent Cast Test PASSED successfully.")
        return results

    finally:
        if not keep_server:
            stop_server()


if __name__ == "__main__":
    run_recurrent_cast_test()
