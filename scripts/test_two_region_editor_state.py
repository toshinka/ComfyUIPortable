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
from custom_nodes.tegaki_manga_nodes.two_region_spec import validate_two_region_spec, get_default_two_region_spec


def test_editor_default_overlap():
    print("\n--- 1. Testing Default Semantic Overlap State ---")
    editor = TegakiTwoRegionCoupleEditor()
    spec, mask_A, mask_B, preview, debug_json = editor.execute_editor(
        canvas_width=832,
        canvas_height=1216,
        global_prompt="masterpiece",
        global_negative_prompt="low quality",
        prompt_A="1girl, blonde hair",
        negative_prompt_A="",
        prompt_B="1boy, black hair",
        negative_prompt_B="",
        two_region_spec_data=""
    )

    assert spec["version"] == 1
    assert len(spec["regions"]) == 2
    assert spec["regions"][0]["id"] == "A"
    assert spec["regions"][1]["id"] == "B"

    # Default は Semantic Overlap (~35% 重なり)
    intersection = (mask_A * mask_B).sum().item()
    assert intersection > 0, "Default state must have overlapping pixels for Semantic Overlap"
    total_area = mask_A.sum().item() + mask_B.sum().item() - intersection
    overlap_ratio = intersection / total_area
    print(f"  Overlap pixels: {intersection:.0f} (Ratio: {overlap_ratio:.2%}) [PASSED]")


def test_editor_move_and_resize_simulation():
    print("\n--- 2. Testing A/B Move & Resize State Transitions ---")
    editor = TegakiTwoRegionCoupleEditor()

    # 初期状態から A を移動、B をリサイズ
    state_spec = get_default_two_region_spec(832, 1216)
    reg_A = state_spec["regions"][0]
    reg_B = state_spec["regions"][1]

    # Move A: x=0.05 -> 0.15, y=0.10 -> 0.20
    reg_A["x"] = 0.15
    reg_A["y"] = 0.20
    # Resize A: w=0.62 -> 0.50, h=0.80 -> 0.60
    reg_A["w"] = 0.50
    reg_A["h"] = 0.60

    # Move B: x=0.33 -> 0.40
    reg_B["x"] = 0.40
    # Resize B: w=0.62 -> 0.55
    reg_B["w"] = 0.55

    spec, mask_A, mask_B, preview, debug_json = editor.execute_editor(
        canvas_width=832, canvas_height=1216,
        global_prompt="", global_negative_prompt="",
        prompt_A="girl", negative_prompt_A="",
        prompt_B="boy", negative_prompt_B="",
        two_region_spec_data=json.dumps(state_spec)
    )

    assert spec["regions"][0]["x"] == 0.15
    assert spec["regions"][0]["w"] == 0.50
    assert spec["regions"][1]["x"] == 0.40
    assert spec["regions"][1]["w"] == 0.55
    # 境界安全性 x+w <= 1.0
    assert spec["regions"][0]["x"] + spec["regions"][0]["w"] <= 1.0001
    assert spec["regions"][1]["x"] + spec["regions"][1]["w"] <= 1.0001
    print("  Move & Resize state transitions & boundary safety: PASSED")


def test_disable_and_restore():
    print("\n--- 3. Testing Disable and Restore of Region A/B ---")
    editor = TegakiTwoRegionCoupleEditor()

    # Step 1: Disable A
    state_spec = get_default_two_region_spec(832, 1216)
    state_spec["regions"][0]["enabled"] = False
    spec1, mask_A1, mask_B1, preview1, _ = editor.execute_editor(
        canvas_width=832, canvas_height=1216,
        global_prompt="", global_negative_prompt="",
        prompt_A="", negative_prompt_A="", prompt_B="", negative_prompt_B="",
        two_region_spec_data=json.dumps(state_spec)
    )
    assert mask_A1.sum() == 0, "Disabled Region A must output all-zero mask"
    assert mask_B1.sum() > 0, "Enabled Region B must output non-zero mask"

    # Step 2: Restore A
    state_spec["regions"][0]["enabled"] = True
    spec2, mask_A2, mask_B2, preview2, _ = editor.execute_editor(
        canvas_width=832, canvas_height=1216,
        global_prompt="", global_negative_prompt="",
        prompt_A="", negative_prompt_A="", prompt_B="", negative_prompt_B="",
        two_region_spec_data=json.dumps(state_spec)
    )
    assert mask_A2.sum() > 0, "Restored Region A must output non-zero mask"
    print("  Disable and Restore functionality: PASSED")


def test_prompt_clearing():
    print("\n--- 4. Testing Clearing Prompt to Empty String ---")
    editor = TegakiTwoRegionCoupleEditor()
    state_spec = get_default_two_region_spec(832, 1216)
    state_spec["regions"][0]["prompt"] = "previously blonde hair"

    # 空文字 "" を送信してクリアできるか
    spec, _, _, _, _ = editor.execute_editor(
        canvas_width=832, canvas_height=1216,
        global_prompt="", global_negative_prompt="",
        prompt_A="", negative_prompt_A="",
        prompt_B="boy", negative_prompt_B="",
        two_region_spec_data=json.dumps(state_spec)
    )
    assert spec["regions"][0]["prompt"] == "", f"Prompt A must be cleared to empty string, got '{spec['regions'][0]['prompt']}'"
    print("  Prompt clearing to empty string: PASSED")


def test_fail_closed_schema_validation():
    print("\n--- 5. Testing Fail-Closed Schema Validation ---")
    editor = TegakiTwoRegionCoupleEditor()

    # 不正な JSON 構文 (SyntaxError) -> フォールバック許容
    corrupted_json = "{ invalid json string }"
    spec, _, _, _, _ = editor.execute_editor(
        canvas_width=832, canvas_height=1216,
        global_prompt="", global_negative_prompt="",
        prompt_A="", negative_prompt_A="", prompt_B="", negative_prompt_B="",
        two_region_spec_data=corrupted_json
    )
    assert spec["version"] == 1
    print("  JSON syntax error gracefully falls back to default: PASSED")

    # Valid JSON だがスキーマ不正 (regions が 3 個、ID が不正など) -> fail-closed (ValueError)
    invalid_schema = {
        "version": 1,
        "canvas": {"width": 832, "height": 1216},
        "regions": [
            {"id": "A", "enabled": True, "prompt": "a", "x": 0, "y": 0, "w": 0.5, "h": 1.0},
            {"id": "B", "enabled": True, "prompt": "b", "x": 0.5, "y": 0, "w": 0.5, "h": 1.0},
            {"id": "C", "enabled": True, "prompt": "c", "x": 0.2, "y": 0, "w": 0.5, "h": 1.0}
        ]
    }
    try:
        editor.execute_editor(
            canvas_width=832, canvas_height=1216,
            global_prompt="", global_negative_prompt="",
            prompt_A="", negative_prompt_A="", prompt_B="", negative_prompt_B="",
            two_region_spec_data=json.dumps(invalid_schema)
        )
        assert False, "Should raise ValueError on invalid schema (fail-closed)"
    except ValueError as e:
        assert "exactly 2 entries" in str(e)
    print("  Invalid schema raises ValueError (Fail-Closed): PASSED")


def run_all():
    print("================================================================================")
    print("Running TegakiTwoRegionCoupleEditor State Tests (Phase 3C.1 Hardened)")
    print("================================================================================")
    test_editor_default_overlap()
    test_editor_move_and_resize_simulation()
    test_disable_and_restore()
    test_prompt_clearing()
    test_fail_closed_schema_validation()
    print("\n================================================================================")
    print("[SUCCESS] ALL HARDENED EDITOR STATE TESTS PASSED!")
    print("================================================================================")
    return 0


if __name__ == "__main__":
    sys.exit(run_all())
