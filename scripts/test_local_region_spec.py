import sys
import os
import json
import copy

# プロジェクトルートとカスタムノードへのパス解決
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CUSTOM_NODES_DIR = os.path.join(ROOT_DIR, "ComfyUI", "custom_nodes")
if CUSTOM_NODES_DIR not in sys.path:
    sys.path.insert(0, CUSTOM_NODES_DIR)
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from custom_nodes.tegaki_manga_nodes.scene_spec import (
    validate_local_region,
    validate_compile_plan,
    SUPPORTED_COMPILE_PLAN_VERSION
)
from custom_nodes.tegaki_manga_nodes.region_editor import validate_region_spec


def run_local_region_spec_tests():
    print("================================================================================")
    print("Local Region Specification (v1) Data Contract Tests (Phase 3B.1)")
    print("================================================================================")

    # 1. 正常系: 有効な Local Region 単体バリデーション
    print("\n--- 1. Testing valid local region ---")
    valid_lr = {
        "id": "local_window_desks",
        "name": "Window Desks",
        "enabled": True,
        "prompt": "school desks near the window, sunlight streaming",
        "negative_prompt": "dark, shadow",
        "area": {
            "x": 0.55,
            "y": 0.10,
            "w": 0.35,
            "h": 0.50
        },
        "metadata": {"type": "prop_cluster"}
    }
    v_lr = validate_local_region(valid_lr)
    assert v_lr["id"] == "local_window_desks"
    assert v_lr["name"] == "Window Desks"
    assert v_lr["enabled"] is True
    assert v_lr["prompt"] == "school desks near the window, sunlight streaming"
    assert v_lr["negative_prompt"] == "dark, shadow"
    assert v_lr["area"]["x"] == 0.55
    assert v_lr["metadata"]["type"] == "prop_cluster"
    print("Valid local region: PASSED")

    # 2. absent compatibility: local_regions が存在しない REGION_SPEC
    print("\n--- 2. Testing local_regions absent compatibility in REGION_SPEC ---")
    base_spec = {
        "version": 1,
        "canvas": {"width": 832, "height": 1216},
        "panel_count": 1,
        "global_prompt": "test",
        "regions": [{
            "id": 1,
            "x": 0.05, "y": 0.05, "w": 0.9, "h": 0.9,
            "prompt": "test koma"
        }]
    }
    v_base = validate_region_spec(base_spec)
    assert "local_regions" not in v_base["regions"][0] or v_base["regions"][0].get("local_regions") is None or isinstance(v_base["regions"][0].get("local_regions"), list)
    print("local_regions absent compatibility: PASSED")

    # 3. 異常系: local_regions がリストでない場合
    print("\n--- 3. Testing non-list local_regions in REGION_SPEC ---")
    bad_lr_spec = copy.deepcopy(base_spec)
    bad_lr_spec["regions"][0]["local_regions"] = "not_a_list"
    try:
        validate_region_spec(bad_lr_spec)
        assert False, "Should reject non-list local_regions"
    except ValueError as e:
        assert "must be a list" in str(e).lower()
        print(f"Non-list local_regions rejected successfully: {e}")
    print("Non-list local_regions: PASSED")

    # 4. 異常系: enabled が strict bool でない場合
    print("\n--- 4. Testing non-bool enabled in local region ---")
    bad_bool_lr = copy.deepcopy(valid_lr)
    bad_bool_lr["enabled"] = "true"  # 文字列
    try:
        validate_local_region(bad_bool_lr)
        assert False, "Should reject string enabled"
    except ValueError as e:
        assert "strict boolean" in str(e).lower()
        print(f"String enabled rejected successfully: {e}")
    print("Strict bool enabled: PASSED")

    # 5. 異常系: prompt が文字列でない場合
    print("\n--- 5. Testing non-string prompt in local region ---")
    bad_p_lr = copy.deepcopy(valid_lr)
    bad_p_lr["prompt"] = 12345
    try:
        validate_local_region(bad_p_lr)
        assert False, "Should reject integer prompt"
    except ValueError as e:
        assert "must be a string" in str(e).lower()
        print(f"Non-string prompt rejected successfully: {e}")
    print("Strict string prompt: PASSED")

    # 6. 異常系: area が欠落または無効な場合
    print("\n--- 6. Testing missing or invalid area in local region ---")
    bad_area_lr = copy.deepcopy(valid_lr)
    bad_area_lr["area"] = None
    try:
        validate_local_region(bad_area_lr)
        assert False, "Should reject None area for local region"
    except ValueError as e:
        assert "must be a dictionary with x, y, w, h" in str(e).lower()
        print(f"None area rejected successfully: {e}")
    print("Missing area rejection: PASSED")

    # 7. 異常系: 重複した local region ID の拒絶
    print("\n--- 7. Testing duplicate local region ID in COMPILE_PLAN ---")
    test_plan = {
        "version": SUPPORTED_COMPILE_PLAN_VERSION,
        "status": "active",
        "target_panel_id": 1,
        "canvas": {"width": 832, "height": 1216},
        "panel": {
            "id": 1,
            "enabled": True,
            "geometry": {"x": 0.05, "y": 0.05, "w": 0.9, "h": 0.9},
            "prompt": "classroom",
            "negative_prompt": "",
            "local_regions": [
                {
                    "id": "dup_lr_1",
                    "name": "Desk",
                    "enabled": True,
                    "prompt": "desks",
                    "negative_prompt": "",
                    "area": {"x": 0.1, "y": 0.1, "w": 0.3, "h": 0.3}
                },
                {
                    "id": "dup_lr_1",  # 重複ID
                    "name": "Another Desk",
                    "enabled": True,
                    "prompt": "more desks",
                    "negative_prompt": "",
                    "area": {"x": 0.5, "y": 0.5, "w": 0.3, "h": 0.3}
                }
            ]
        },
        "global_prompt": "",
        "global_negative_prompt": "",
        "compiled_prompt": "",
        "compiled_negative_prompt": "",
        "characters": [],
        "lora_plan": {"global_loras": [], "koma_loras": [], "character_loras": []}
    }
    try:
        validate_compile_plan(test_plan)
        assert False, "Should reject duplicate local_region ID"
    except ValueError as e:
        assert "duplicate local_region id" in str(e).lower()
        print(f"Duplicate local_region ID rejected successfully: {e}")
    print("Duplicate local_region ID rejection: PASSED")

    print("\n================================================================================")
    print("[SUCCESS] ALL 7 LOCAL REGION SPEC TEST SUITES PASSED PERFECTLY!")
    print("================================================================================")
    return 0


if __name__ == "__main__":
    sys.exit(run_local_region_spec_tests())
