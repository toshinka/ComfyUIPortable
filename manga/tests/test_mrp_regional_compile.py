"""Pure MRP regional compile-core contract tests; no graph, runtime, or GPU use."""

from __future__ import annotations

import copy
import importlib.util
import pathlib
import sys
import types
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


# Load only the pure contract modules.  Importing the production package
# initializer would also load optional ComfyUI/torch extensions unrelated to
# this headless test.
_PURE_PACKAGE = "_tegaki_mrp_compile_test"
_PURE_DIR = ROOT / "custom_nodes_custom" / "tegaki_manga_nodes"
_pure_package = types.ModuleType(_PURE_PACKAGE)
_pure_package.__path__ = [str(_PURE_DIR)]
sys.modules[_PURE_PACKAGE] = _pure_package
for _module_name in ("interaction_resolver", "subscene_contract", "authoring_contract", "scene_spec"):
    _module_full_name = f"{_PURE_PACKAGE}.{_module_name}"
    _module_spec = importlib.util.spec_from_file_location(_module_full_name, _PURE_DIR / f"{_module_name}.py")
    _module = importlib.util.module_from_spec(_module_spec)
    sys.modules[_module_full_name] = _module
    _module_spec.loader.exec_module(_module)

_scene_spec = sys.modules[f"{_PURE_PACKAGE}.scene_spec"]
RegionalCompileError = _scene_spec.RegionalCompileError
compile_regional_spec = _scene_spec.compile_regional_spec


def context():
    return {
        "page_id": "page-1",
        "scene_id": "scene-1",
        "style_prompt": "inked manga",
        "style_negative_prompt": "photorealistic",
        "prompt": "rainy street",
        "negative_prompt": "daylight",
        "canvas": {"width": 832, "height": 1216},
    }


def region(region_id="r1", **changes):
    value = {
        "id": region_id,
        "area": {"x": 0.123456, "y": 0.1, "w": 0.25, "h": 0.3},
        "prompt": "wet pavement",
    }
    value.update(changes)
    return value


class MangaRegionalCompileTests(unittest.TestCase):
    def test_single_region_is_deterministic_and_normalized(self):
        first = compile_regional_spec(context(), [region()])
        second = compile_regional_spec(context(), [region()])

        self.assertEqual(first, second)
        self.assertEqual(first["version"], 1)
        self.assertEqual(first["source"], {"page_id": "page-1", "scene_id": "scene-1"})
        self.assertEqual(first["canvas"], {"width": 832, "height": 1216})
        self.assertEqual(first["regions"][0]["area"], {"x": 0.1235, "y": 0.1, "w": 0.25, "h": 0.3})
        self.assertEqual(set(first["regions"][0]["area"]), {"x", "y", "w", "h"})

    def test_order_and_explicit_ids_are_preserved(self):
        result = compile_regional_spec(context(), [
            region("stable-first", prompt="first"),
            region("stable-second", prompt="second", area={"x": 0.7, "y": 0.1, "w": 0.2, "h": 0.2}),
        ])

        self.assertEqual([entry["id"] for entry in result["regions"]], ["stable-first", "stable-second"])
        self.assertEqual([entry["source_order"] for entry in result["regions"]], [0, 1])

    def test_duplicate_ids_fail_closed(self):
        with self.assertRaises(RegionalCompileError) as raised:
            compile_regional_spec(context(), [region("same"), region("same", prompt="second")])
        self.assertEqual(raised.exception.code, "DUPLICATE_REGION_ID")

    def test_invalid_and_out_of_bounds_geometry_fail_closed(self):
        cases = [
            (region(area={"x": 0, "y": 0, "w": 0, "h": 0.2}), "INVALID_GEOMETRY"),
            (region(area={"x": 0, "y": 0, "w": "wide", "h": 0.2}), "INVALID_GEOMETRY"),
            (region(area={"x": -0.1, "y": 0, "w": 0.2, "h": 0.2}), "OUT_OF_BOUNDS"),
            (region(area={"x": 0.9, "y": 0, "w": 0.2, "h": 0.2}), "OUT_OF_BOUNDS"),
        ]
        for candidate, code in cases:
            with self.subTest(code=code):
                with self.assertRaises(RegionalCompileError) as raised:
                    compile_regional_spec(context(), [candidate])
                self.assertEqual(raised.exception.code, code)

    def test_prompt_scopes_remain_structured(self):
        result = compile_regional_spec(context(), [region("r1", negative_prompt="mud", strength=1.25)])

        self.assertEqual(result["prompt_scopes"]["global"]["positive"], "inked manga")
        self.assertEqual(result["prompt_scopes"]["global"]["negative"], "photorealistic")
        self.assertEqual(result["prompt_scopes"]["scene"]["positive"], "rainy street")
        self.assertEqual(result["prompt_scopes"]["scene"]["negative"], "daylight")
        self.assertEqual(result["regions"][0]["prompt"], "wet pavement")
        self.assertEqual(result["regions"][0]["negative_prompt"], "mud")
        self.assertTrue(result["regions"][0]["negative_prompt_present"])
        self.assertNotIn("compiled_prompt", result["regions"][0])

    def test_negative_absence_is_distinct_from_explicit_empty(self):
        absent = compile_regional_spec(context(), [region()])["regions"][0]
        explicit_empty = compile_regional_spec(context(), [region(negative_prompt="")])["regions"][0]

        self.assertIsNone(absent["negative_prompt"])
        self.assertFalse(absent["negative_prompt_present"])
        self.assertEqual(explicit_empty["negative_prompt"], "")
        self.assertTrue(explicit_empty["negative_prompt_present"])

    def test_strength_uses_existing_range_without_inventing_a_default(self):
        explicit = compile_regional_spec(context(), [region(strength=1.5)])["regions"][0]
        legacy_weight = compile_regional_spec(context(), [region(weight=0.75)])["regions"][0]
        absent = compile_regional_spec(context(), [region()])["regions"][0]

        self.assertEqual(explicit["strength"], 1.5)
        self.assertEqual(explicit["strength_source"], "strength")
        self.assertEqual(legacy_weight["strength"], 0.75)
        self.assertEqual(legacy_weight["strength_source"], "weight")
        self.assertIsNone(absent["strength"])
        self.assertFalse(absent["strength_present"])
        with self.assertRaises(RegionalCompileError) as raised:
            compile_regional_spec(context(), [region(strength=2.01)])
        self.assertEqual(raised.exception.code, "INVALID_STRENGTH")

    def test_overlap_warns_without_precedence_or_discarding(self):
        result = compile_regional_spec(context(), [
            region("left", prompt="left"),
            region("overlap", prompt="right", area={"x": 0.2, "y": 0.2, "w": 0.3, "h": 0.3}),
        ])

        self.assertEqual([entry["id"] for entry in result["regions"]], ["left", "overlap"])
        self.assertEqual(len(result["diagnostics"]), 1)
        warning = result["diagnostics"][0]
        self.assertEqual(warning["severity"], "WARNING")
        self.assertEqual(warning["code"], "OVERLAP_PRESENT")
        self.assertEqual(warning["region_ids"], ["left", "overlap"])
        self.assertNotIn("winner", warning)
        self.assertNotIn("priority", warning)

    def test_source_objects_are_not_mutated(self):
        page = context()
        regions = [region("r1", metadata={"origin": {"kind": "fixture"}})]
        original_page = copy.deepcopy(page)
        original_regions = copy.deepcopy(regions)

        result = compile_regional_spec(page, regions)
        result["regions"][0]["area"]["x"] = 0.9
        result["regions"][0]["metadata"]["origin"]["kind"] = "changed"

        self.assertEqual(page, original_page)
        self.assertEqual(regions, original_regions)

    def test_unknown_fields_are_rejected_and_disabled_empty_prompt_is_allowed(self):
        with self.assertRaises(RegionalCompileError) as raised:
            compile_regional_spec(context(), [region(color="#fff")])
        self.assertEqual(raised.exception.code, "UNSUPPORTED_REGION_FIELD")

        disabled = compile_regional_spec(context(), [region("disabled", enabled=False, prompt="")])
        self.assertEqual(disabled["regions"][0]["prompt"], "")
        self.assertFalse(disabled["regions"][0]["enabled"])
        self.assertEqual(disabled["diagnostics"], [])

    def test_missing_id_and_area_shape_are_rejected(self):
        missing_id = region()
        del missing_id["id"]
        with self.assertRaises(RegionalCompileError) as raised:
            compile_regional_spec(context(), [missing_id])
        self.assertEqual(raised.exception.code, "INVALID_REGION_ID")

        with self.assertRaises(RegionalCompileError) as raised:
            compile_regional_spec(context(), [region(area={"shape_type": "polygon", "x": 0, "y": 0, "w": 0.2, "h": 0.2})])
        self.assertEqual(raised.exception.code, "INVALID_GEOMETRY")


if __name__ == "__main__":
    unittest.main()
