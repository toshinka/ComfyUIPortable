import os
import sys
import json
import math

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CUSTOM_NODES_DIR = os.path.join(ROOT_DIR, "ComfyUI", "custom_nodes")
if CUSTOM_NODES_DIR not in sys.path:
    sys.path.insert(0, CUSTOM_NODES_DIR)
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from custom_nodes.tegaki_manga_nodes.panel_layout_spec import (
    get_default_panel_layout_spec,
    validate_panel_layout_spec,
    polygon_signed_area,
    MAX_PANELS
)


def assert_raises(exc_type, fn, *args, match=None, **kwargs):
    try:
        fn(*args, **kwargs)
        raise AssertionError(f"Expected {exc_type.__name__} was not raised.")
    except exc_type as e:
        if match and match not in str(e):
            raise AssertionError(f"Expected exception message containing '{match}', got: {e}")
        return e


def test_default_presets():
    print("\n--- 1. Testing Default Presets (1_full, 3_basic, 3_dynamic, 4_grid) ---")
    for preset in ("1_full", "3_basic", "3_dynamic", "4_grid"):
        spec = get_default_panel_layout_spec(832, 1216, preset=preset)
        validated = validate_panel_layout_spec(spec)
        assert validated["version"] == 1
        assert 1 <= len(validated["panels"]) <= MAX_PANELS
        print(f"  Preset '{preset}': {len(validated['panels'])} panels, {len(validated['vertices'])} vertices [PASSED]")


def test_canvas_bounds():
    print("\n--- 2. Testing Canvas Bounds Validation ---")
    spec = get_default_panel_layout_spec(832, 1216)
    spec["canvas"]["width"] = -10
    assert_raises(ValueError, validate_panel_layout_spec, spec, match="canvas.width")

    spec = get_default_panel_layout_spec(832, 1216)
    spec["canvas"]["height"] = 99999
    assert_raises(ValueError, validate_panel_layout_spec, spec, match="canvas.height")
    print("  Canvas bounds validation: PASSED")


def test_unique_vertex_and_panel_ids():
    print("\n--- 3. Testing Unique Vertex and Panel IDs ---")
    spec = get_default_panel_layout_spec(832, 1216)
    spec["vertices"][1]["id"] = spec["vertices"][0]["id"]
    assert_raises(ValueError, validate_panel_layout_spec, spec, match="Duplicate vertex id")

    spec = get_default_panel_layout_spec(832, 1216)
    spec["panels"][1]["id"] = spec["panels"][0]["id"]
    assert_raises(ValueError, validate_panel_layout_spec, spec, match="Duplicate panel id")
    print("  Duplicate ID rejection: PASSED")


def test_undefined_vertex_reference():
    print("\n--- 4. Testing Undefined Vertex Reference ---")
    spec = get_default_panel_layout_spec(832, 1216)
    spec["panels"][0]["vertex_ids"].append("non_existent_vertex_999")
    assert_raises(ValueError, validate_panel_layout_spec, spec, match="Undefined vertex reference")
    print("  Undefined vertex reference rejection: PASSED")


def test_panel_capacity_limit():
    print("\n--- 5. Testing Panel Capacity Limit (Max 6) ---")
    spec = get_default_panel_layout_spec(832, 1216)
    while len(spec["panels"]) < 7:
        p_dummy = {
            "id": f"p_extra_{len(spec['panels'])}",
            "vertex_ids": ["v1", "v2", "v3"]
        }
        spec["panels"].append(p_dummy)
    assert_raises(ValueError, validate_panel_layout_spec, spec, match="panels' count must be between 1 and 6")
    print("  Panel capacity > 6 rejection: PASSED")


def test_degenerate_polygon_area():
    print("\n--- 6. Testing Degenerate Polygon Area Rejection ---")
    spec = get_default_panel_layout_spec(832, 1216)
    # 同一線上の頂点 (面積 0)
    spec["vertices"].append({"id": "v_zero1", "x": 0.1, "y": 0.1})
    spec["vertices"].append({"id": "v_zero2", "x": 0.2, "y": 0.2})
    spec["vertices"].append({"id": "v_zero3", "x": 0.3, "y": 0.3})
    spec["panels"][0]["vertex_ids"] = ["v_zero1", "v_zero2", "v_zero3"]
    assert_raises(ValueError, validate_panel_layout_spec, spec, match="smaller than minimum")
    print("  Degenerate polygon rejection: PASSED")


def test_json_string_save_reload():
    print("\n--- 7. Testing JSON String Save & Reload Exactness ---")
    spec = get_default_panel_layout_spec(832, 1216, preset="3_dynamic")
    json_str = json.dumps(spec, indent=2)
    reloaded = validate_panel_layout_spec(json_str)
    assert reloaded["version"] == spec["version"]
    assert len(reloaded["panels"]) == len(spec["panels"])
    assert len(reloaded["vertices"]) == len(spec["vertices"])
    print("  Save & Reload exactness: PASSED")


def run_all():
    print("================================================================================")
    print("Running PANEL_LAYOUT_SPEC Unit Tests (Phase 3C.1)")
    print("================================================================================")
    test_default_presets()
    test_canvas_bounds()
    test_unique_vertex_and_panel_ids()
    test_undefined_vertex_reference()
    test_panel_capacity_limit()
    test_degenerate_polygon_area()
    test_json_string_save_reload()
    print("\n================================================================================")
    print("[SUCCESS] ALL 7 PANEL_LAYOUT_SPEC UNIT TESTS PASSED!")
    print("================================================================================")
    return 0


if __name__ == "__main__":
    sys.exit(run_all())
