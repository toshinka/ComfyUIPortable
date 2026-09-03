import os
import sys
import json
import torch

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CUSTOM_NODES_DIR = os.path.join(ROOT_DIR, "ComfyUI", "custom_nodes")
if CUSTOM_NODES_DIR not in sys.path:
    sys.path.insert(0, CUSTOM_NODES_DIR)
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from custom_nodes.tegaki_manga_nodes.two_region_editor import TegakiTwoRegionCoupleEditor


def test_editor_execution():
    print("\n--- 1. Testing Default Editor Execution ---")
    editor = TegakiTwoRegionCoupleEditor()
    spec, mask_A, mask_B, preview, debug_json = editor.execute_editor(
        canvas_width=512,
        canvas_height=768,
        global_prompt="masterpiece",
        global_negative_prompt="low quality",
        prompt_A="1girl, blonde hair",
        negative_prompt_A="",
        prompt_B="1boy, black hair",
        negative_prompt_B="",
        two_region_spec_data=""
    )

    assert spec["version"] == 1
    assert spec["canvas"]["width"] == 512
    assert spec["canvas"]["height"] == 768
    assert mask_A.shape == (1, 768, 512)
    assert mask_B.shape == (1, 768, 512)
    assert preview.shape == (1, 768, 512, 3)

    # 左右分離 (Horizontal) の確認: Aは左半分、Bは右半分
    assert mask_A[0, :, :200].sum() > 0
    assert mask_A[0, :, 300:].sum() == 0
    assert mask_B[0, :, :200].sum() == 0
    assert mask_B[0, :, 300:].sum() > 0
    print("  Default execution & mask separation: PASSED")


def test_overlap_preset():
    print("\n--- 2. Testing Overlap Preset Mask Intersection ---")
    editor = TegakiTwoRegionCoupleEditor()
    overlap_spec = {
        "version": 1,
        "canvas": {"width": 512, "height": 768},
        "regions": [
            {"id": "A", "enabled": True, "prompt": "girl", "negative_prompt": "", "x": 0.10, "y": 0.10, "w": 0.55, "h": 0.80},
            {"id": "B", "enabled": True, "prompt": "boy", "negative_prompt": "", "x": 0.35, "y": 0.10, "w": 0.55, "h": 0.80}
        ]
    }
    spec, mask_A, mask_B, preview, debug_json = editor.execute_editor(
        canvas_width=512, canvas_height=768,
        global_prompt="", global_negative_prompt="",
        prompt_A="", negative_prompt_A="",
        prompt_B="", negative_prompt_B="",
        two_region_spec_data=json.dumps(overlap_spec)
    )

    intersection = (mask_A * mask_B).sum().item()
    assert intersection > 0, "Overlap preset should have intersecting mask pixels"
    print(f"  Overlap intersection pixels: {intersection:.0f} [PASSED]")


def test_one_region_disabled():
    print("\n--- 3. Testing One Region Disabled Behavior ---")
    editor = TegakiTwoRegionCoupleEditor()
    one_a_spec = {
        "version": 1,
        "canvas": {"width": 512, "height": 768},
        "regions": [
            {"id": "A", "enabled": True, "prompt": "girl", "negative_prompt": "", "x": 0.10, "y": 0.10, "w": 0.80, "h": 0.80},
            {"id": "B", "enabled": False, "prompt": "boy", "negative_prompt": "", "x": 0.50, "y": 0.10, "w": 0.40, "h": 0.80}
        ]
    }
    spec, mask_A, mask_B, preview, debug_json = editor.execute_editor(
        canvas_width=512, canvas_height=768,
        global_prompt="", global_negative_prompt="",
        prompt_A="", negative_prompt_A="",
        prompt_B="", negative_prompt_B="",
        two_region_spec_data=json.dumps(one_a_spec)
    )

    assert mask_A.sum() > 0
    assert mask_B.sum() == 0, "Disabled Region B mask must be completely zero"
    print("  One Region disabled mask: PASSED")


def run_all():
    print("================================================================================")
    print("Running TegakiTwoRegionCoupleEditor Tests (Phase 3C-2)")
    print("================================================================================")
    test_editor_execution()
    test_overlap_preset()
    test_one_region_disabled()
    print("\n================================================================================")
    print("[SUCCESS] ALL EDITOR STATE & PRESET TESTS PASSED!")
    print("================================================================================")
    return 0


if __name__ == "__main__":
    sys.exit(run_all())
