import os
import sys
import json

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CUSTOM_NODES_DIR = os.path.join(ROOT_DIR, "ComfyUI", "custom_nodes")
if CUSTOM_NODES_DIR not in sys.path:
    sys.path.insert(0, CUSTOM_NODES_DIR)
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from custom_nodes.tegaki_manga_nodes.two_region_spec import (
    get_default_two_region_spec,
    validate_two_region_spec,
)


def assert_raises(exc_type, func, *args, match=None, **kwargs):
    try:
        func(*args, **kwargs)
    except exc_type as e:
        if match and match not in str(e):
            raise AssertionError(f"Expected error message containing '{match}', got '{str(e)}'")
        return e
    except Exception as e:
        raise AssertionError(f"Expected {exc_type.__name__}, got {type(e).__name__}: {e}")
    raise AssertionError(f"Expected {exc_type.__name__} was not raised")


def test_default_spec():
    print("\n--- 1. Testing Default TWO_REGION_SPEC ---")
    spec = get_default_two_region_spec(832, 1216)
    validated = validate_two_region_spec(spec)
    assert validated["version"] == 1
    assert validated["canvas"]["width"] == 832
    assert validated["canvas"]["height"] == 1216
    assert len(validated["regions"]) == 2
    assert validated["regions"][0]["id"] == "A"
    assert validated["regions"][1]["id"] == "B"
    print("  Default spec validation: PASSED")


def test_json_string_input():
    print("\n--- 2. Testing JSON String Input ---")
    spec = get_default_two_region_spec()
    spec_str = json.dumps(spec)
    validated = validate_two_region_spec(spec_str)
    assert validated["version"] == 1
    print("  JSON string parsing: PASSED")


def test_version_validation():
    print("\n--- 3. Testing Version Validation ---")
    spec = get_default_two_region_spec()
    spec["version"] = 2
    assert_raises(ValueError, validate_two_region_spec, spec, match="Unsupported schema version")
    print("  Invalid version rejection: PASSED")


def test_canvas_bounds():
    print("\n--- 4. Testing Canvas Bounds ---")
    spec = get_default_two_region_spec()
    spec["canvas"]["width"] = -10
    assert_raises(ValueError, validate_two_region_spec, spec, match="canvas.width")

    spec["canvas"]["width"] = 832
    spec["canvas"]["height"] = 99999
    assert_raises(ValueError, validate_two_region_spec, spec, match="canvas.height")

    spec["canvas"]["width"] = True  # bool is subclass of int
    assert_raises(ValueError, validate_two_region_spec, spec, match="canvas.width")
    print("  Canvas bounds validation: PASSED")


def test_strict_bool_enabled():
    print("\n--- 5. Testing Strict Boolean on 'enabled' ---")
    spec = get_default_two_region_spec()
    spec["regions"][0]["enabled"] = "true"
    assert_raises(ValueError, validate_two_region_spec, spec, match="strict boolean")

    spec["regions"][0]["enabled"] = 1
    assert_raises(ValueError, validate_two_region_spec, spec, match="strict boolean")
    print("  Strict bool validation: PASSED")


def test_duplicate_and_empty_id():
    print("\n--- 6. Testing Duplicate, Non-A/B, and Count != 2 IDs ---")
    spec = get_default_two_region_spec()
    spec["regions"][1]["id"] = "A"
    assert_raises(ValueError, validate_two_region_spec, spec, match="Duplicate region id")

    spec = get_default_two_region_spec()
    spec["regions"][1]["id"] = ""
    assert_raises(ValueError, validate_two_region_spec, spec, match="Region id must be 'A' or 'B'")

    spec = get_default_two_region_spec()
    spec["regions"][1]["id"] = "C"
    assert_raises(ValueError, validate_two_region_spec, spec, match="Region id must be 'A' or 'B'")

    spec = get_default_two_region_spec()
    spec["regions"].append({"id": "C", "enabled": True, "prompt": "", "negative_prompt": "", "x": 0, "y": 0, "w": 0.5, "h": 0.5})
    assert_raises(ValueError, validate_two_region_spec, spec, match="exactly 2 entries")
    print("  Duplicate, Non-A/B, and Count != 2 rejection: PASSED")


def test_nan_and_infinite_coords():
    print("\n--- 7. Testing NaN and Infinite Coordinates ---")
    spec = get_default_two_region_spec()
    spec["regions"][0]["x"] = float("nan")
    assert_raises(ValueError, validate_two_region_spec, spec, match="finite number")

    spec["regions"][0]["x"] = float("inf")
    assert_raises(ValueError, validate_two_region_spec, spec, match="finite number")
    print("  NaN and Infinite coords rejection: PASSED")


def test_boundary_clamping():
    print("\n--- 8. Testing Boundary Clamping ---")
    spec = get_default_two_region_spec()
    spec["regions"][0]["x"] = 0.8
    spec["regions"][0]["w"] = 0.5  # 0.8 + 0.5 = 1.3 > 1.0 -> should clamp w to 0.2
    validated = validate_two_region_spec(spec)
    assert validated["regions"][0]["x"] == 0.8
    assert validated["regions"][0]["w"] == 0.2
    print("  Boundary clamping: PASSED")


def test_unknown_fields_preservation():
    print("\n--- 9. Testing Unknown Fields Preservation ---")
    spec = get_default_two_region_spec()
    spec["custom_oracle_field"] = "oracle_123"
    spec["metadata"]["extra_info"] = 42
    validated = validate_two_region_spec(spec)
    assert validated.get("custom_oracle_field") == "oracle_123"
    assert validated["metadata"].get("extra_info") == 42
    print("  Unknown fields preservation: PASSED")


def run_all():
    print("================================================================================")
    print("Running TWO_REGION_SPEC Unit Tests (Phase 3C-1)")
    print("================================================================================")
    test_default_spec()
    test_json_string_input()
    test_version_validation()
    test_canvas_bounds()
    test_strict_bool_enabled()
    test_duplicate_and_empty_id()
    test_nan_and_infinite_coords()
    test_boundary_clamping()
    test_unknown_fields_preservation()
    print("\n================================================================================")
    print("[SUCCESS] ALL 9 TWO_REGION_SPEC UNIT TESTS PASSED!")
    print("================================================================================")
    return 0


if __name__ == "__main__":
    sys.exit(run_all())
