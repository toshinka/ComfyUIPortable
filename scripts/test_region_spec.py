import sys
import os
import json
import torch
import copy

comfy_dir = os.path.abspath("ComfyUI")
sys.path.insert(0, comfy_dir)

from custom_nodes.tegaki_manga_nodes.region_editor import (
    TegakiMangaRegionEditor,
    default_region_spec,
    validate_region_spec,
    normalize_region_spec,
    render_preview_image,
    render_mask_batch,
    is_active_region,
    SUPPORTED_SCHEMA_VERSION
)

def run_tests():
    print("================================================================================")
    print("Running Comprehensive Tegaki Region Editor Backend Tests")
    print("================================================================================")

    # 1. default_region_spec
    print("\n--- 1. Testing default_region_spec ---")
    spec = default_region_spec(width=832, height=1216, panel_count=3, global_prompt="test global")
    assert spec["version"] == SUPPORTED_SCHEMA_VERSION, f"Expected version {SUPPORTED_SCHEMA_VERSION}"
    assert spec["canvas"]["width"] == 832 and spec["canvas"]["height"] == 1216
    assert spec["panel_count"] == 3
    assert len(spec["regions"]) == 6
    assert spec["global_prompt"] == "test global"
    print("default_region_spec: PASSED")

    # 2. panel_count = 1 & panel_count = 6
    print("\n--- 2. Testing panel_count bounds (1 and 6) ---")
    spec1 = default_region_spec(panel_count=1)
    v_spec1 = validate_region_spec(spec1)
    active1 = [r["id"] for r in v_spec1["regions"] if is_active_region(r, 1)]
    assert active1 == [1], f"Expected [1], got {active1}"

    spec6 = default_region_spec(panel_count=6)
    v_spec6 = validate_region_spec(spec6)
    active6 = [r["id"] for r in v_spec6["regions"] if is_active_region(r, 6)]
    assert len(active6) == 6, f"Expected 6 active regions, got {len(active6)}"
    print("panel_count bounds: PASSED")

    # 3. 0 active regions & Empty Mask behavior
    print("\n--- 3. Testing 0 active regions & Empty Mask behavior ---")
    spec_zero = copy.deepcopy(spec)
    for r in spec_zero["regions"]:
        r["enabled"] = False
    masks, active_ids = render_mask_batch(spec_zero, 832, 1216)
    assert active_ids == [], f"Expected empty active_ids, got {active_ids}"
    assert masks.shape == (1, 1216, 832), f"Expected shape [1, 1216, 832], got {masks.shape}"
    # 重要: 空Region時は全画面黒（zeros）であることを確認
    assert torch.all(masks == 0.0), "Empty mask must be all zeros (torch.zeros), NOT ones!"
    print("0 active regions & zeros mask: PASSED")

    # 4. Overlapping regions & disabled region
    print("\n--- 4. Testing Overlapping & Disabled regions ---")
    spec_overlap = copy.deepcopy(spec)
    # KOMA 1 と KOMA 2 を同一座標に重ねる
    spec_overlap["regions"][0]["x"] = 0.1
    spec_overlap["regions"][0]["y"] = 0.1
    spec_overlap["regions"][0]["w"] = 0.5
    spec_overlap["regions"][0]["h"] = 0.5
    spec_overlap["regions"][1]["x"] = 0.1
    spec_overlap["regions"][1]["y"] = 0.1
    spec_overlap["regions"][1]["w"] = 0.5
    spec_overlap["regions"][1]["h"] = 0.5
    spec_overlap["regions"][2]["enabled"] = False # KOMA 3 を disabled にする

    v_overlap = validate_region_spec(spec_overlap)
    preview = render_preview_image(v_overlap, 832, 1216)
    masks_o, ids_o = render_mask_batch(v_overlap, 832, 1216)
    assert ids_o == [1, 2], f"Expected active ids [1, 2], got {ids_o}"
    assert masks_o.shape == (2, 1216, 832), f"Expected [2, 1216, 832], got {masks_o.shape}"
    print("Overlapping & Disabled regions: PASSED")

    # 5. Invalid JSON handling
    print("\n--- 5. Testing Invalid JSON handling in node execute ---")
    editor = TegakiMangaRegionEditor()
    _, out_json, _, _, _, active_ids_str = editor.execute_editor(
        panel_count=3,
        canvas_width=832,
        canvas_height=1216,
        global_prompt="test",
        region_spec_data="{broken json..."
    )
    parsed = json.loads(out_json)
    assert parsed["version"] == SUPPORTED_SCHEMA_VERSION
    assert json.loads(active_ids_str) == [1, 2, 3]
    print("Invalid JSON fallback: PASSED")

    # 6. Missing canvas & Missing regions
    print("\n--- 6. Testing Validator on Missing canvas / regions ---")
    try:
        validate_region_spec({"version": 1, "panel_count": 3})
        assert False, "Should raise ValueError on missing canvas"
    except ValueError as e:
        assert "canvas" in str(e).lower()

    try:
        validate_region_spec({"version": 1, "canvas": {"width": 832, "height": 1216}})
        assert False, "Should raise ValueError on missing regions"
    except ValueError as e:
        assert "regions" in str(e).lower()
    print("Missing canvas / regions validation: PASSED")

    # 7. Duplicate region ID
    print("\n--- 7. Testing Duplicate region ID ---")
    bad_dup = {
        "version": 1,
        "canvas": {"width": 832, "height": 1216},
        "panel_count": 2,
        "regions": [
            {"id": 1, "enabled": True, "x": 0.1, "y": 0.1, "w": 0.4, "h": 0.4},
            {"id": 1, "enabled": True, "x": 0.5, "y": 0.1, "w": 0.4, "h": 0.4},
        ]
    }
    try:
        validate_region_spec(bad_dup)
        assert False, "Should raise ValueError on duplicate region ID"
    except ValueError as e:
        assert "duplicate" in str(e).lower()
    print("Duplicate region ID validation: PASSED")

    # 8. Negative coordinates & x+w > 1 clamping
    print("\n--- 8. Testing Negative coordinates & x+w > 1 clamping ---")
    out_of_bounds = {
        "version": 1,
        "canvas": {"width": 832, "height": 1216},
        "panel_count": 2,
        "regions": [
            {"id": 1, "enabled": True, "x": -0.2, "y": -0.1, "w": 0.5, "h": 0.5},
            {"id": 2, "enabled": True, "x": 0.8, "y": 0.8, "w": 0.5, "h": 0.5}, # 0.8 + 0.5 = 1.3 > 1.0
        ]
    }
    clamped = validate_region_spec(out_of_bounds)
    r1 = clamped["regions"][0]
    r2 = clamped["regions"][1]
    assert r1["x"] == 0.0 and r1["y"] == 0.0, f"Expected 0.0, got ({r1['x']}, {r1['y']})"
    assert r2["x"] + r2["w"] <= 1.0, f"x+w must be <= 1.0, got {r2['x'] + r2['w']}"
    assert r2["y"] + r2["h"] <= 1.0, f"y+h must be <= 1.0, got {r2['y'] + r2['h']}"
    print("Negative coords & x+w > 1 clamping: PASSED")

    # 9. Unsupported schema version
    print("\n--- 9. Testing Unsupported schema version ---")
    unsupported_ver = copy.deepcopy(spec)
    unsupported_ver["version"] = 999
    try:
        validate_region_spec(unsupported_ver)
        assert False, "Should raise ValueError on unsupported schema version"
    except ValueError as e:
        assert "unsupported" in str(e).lower()
    print("Unsupported schema version: PASSED")

    # 10. State serialization & reload consistency
    print("\n--- 10. Testing State Serialization and Reload consistency ---")
    editor = TegakiMangaRegionEditor()
    spec_o, spec_j, gp_o, prev_o, masks_o, ids_j = editor.execute_editor(
        panel_count=4,
        canvas_width=832,
        canvas_height=1216,
        global_prompt="custom global",
        region_spec_data="{}"
    )

    # 次回の実行で直前の spec_j を渡す
    spec_o2, spec_j2, gp_o2, prev_o2, masks_o2, ids_j2 = editor.execute_editor(
        panel_count=4,
        canvas_width=832,
        canvas_height=1216,
        global_prompt="custom global",
        region_spec_data=spec_j
    )

    assert spec_o["regions"][0]["x"] == spec_o2["regions"][0]["x"]
    assert spec_o["panel_count"] == spec_o2["panel_count"]
    assert ids_j == ids_j2 == "[1, 2, 3, 4]"
    assert torch.allclose(prev_o, prev_o2)
    assert torch.allclose(masks_o, masks_o2)
    print("State Serialization & Reload consistency: PASSED")

    # 11. Forward-compatibility: unknown fields preservation
    print("\n--- 11. Testing Forward-compatibility (Unknown fields preservation) ---")
    future_spec = copy.deepcopy(spec)
    future_spec["regions"][0]["control_strength"] = 0.85
    future_spec["regions"][0]["lora_tag"] = "<lora:style:0.6>"
    v_future = validate_region_spec(future_spec)
    assert v_future["regions"][0]["control_strength"] == 0.85
    assert v_future["regions"][0]["lora_tag"] == "<lora:style:0.6>"
    # 12. Phase 3A Boundary Clamping: x=1.0, y=1.0 with positive w, h
    print("\n--- 12. Testing Phase 3A Boundary Clamping (x=1.0, y=1.0) ---")
    boundary_spec = {
        "version": 1,
        "canvas": {"width": 832, "height": 1216},
        "panel_count": 2,
        "regions": [
            {"id": 1, "enabled": True, "x": 1.0, "y": 1.0, "w": 0.05, "h": 0.05},
            {"id": 2, "enabled": True, "x": 0.9999, "y": 0.5, "w": 0.1, "h": 0.1},
        ]
    }
    clamped_b = validate_region_spec(boundary_spec)
    for r in clamped_b["regions"]:
        assert r["x"] + r["w"] <= 1.0, f"x+w must be <= 1.0, got {r['x'] + r['w']} for id {r['id']}"
        assert r["y"] + r["h"] <= 1.0, f"y+h must be <= 1.0, got {r['y'] + r['h']} for id {r['id']}"
        assert r["w"] >= 0.001 and r["h"] >= 0.001, "w and h must be at least MIN_REGION_SIZE"
    print("Phase 3A Boundary Clamping: PASSED")

    # 13. Phase 3A Tiny Region Preview Rendering safety
    print("\n--- 13. Testing Phase 3A Tiny Region Preview Rendering ---")
    tiny_spec = {
        "version": 1,
        "canvas": {"width": 832, "height": 1216},
        "panel_count": 1,
        "regions": [
            {"id": 1, "enabled": True, "x": 0.5, "y": 0.5, "w": 0.001, "h": 0.001, "prompt": "tiny"}
        ]
    }
    v_tiny = validate_region_spec(tiny_spec)
    try:
        preview_tiny = render_preview_image(v_tiny, 832, 1216)
        assert preview_tiny.shape == (1, 1216, 832, 3)
    except Exception as e:
        assert False, f"render_preview_image raised an exception on tiny region: {e}"
    print("Tiny Region Preview Rendering: PASSED")

    # 14. Phase 3A Strict Non-dict Region Reject
    print("\n--- 14. Testing Phase 3A Non-dict Region Reject ---")
    bad_entries_spec = {
        "version": 1,
        "canvas": {"width": 832, "height": 1216},
        "panel_count": 1,
        "regions": [
            {"id": 1, "enabled": True, "x": 0.1, "y": 0.1, "w": 0.4, "h": 0.4},
            "broken string element in regions"
        ]
    }
    try:
        validate_region_spec(bad_entries_spec)
        assert False, "validate_region_spec must reject non-dict entries in regions!"
    except ValueError as e:
        assert "must be a dictionary" in str(e).lower()
        print(f"Non-dict element rejected successfully: {e}")
    print("Non-dict Region Reject: PASSED")

    print("\n================================================================================")
    print("[SUCCESS] ALL 14 TEST SUITES PASSED PERFECTLY!")
    print("================================================================================")
    return 0

if __name__ == "__main__":
    sys.exit(run_tests())
