"""
test_m1_authoring_execution_bridge.py — M1 Authoring Execution Bridge Tests
===========================================================================
Tests for validate_m1_execution_document, compile_document_to_page_plan,
generate_scene_regions_preview_image / tensor, and get_execution_debug_info.
"""
import sys
import os
import json
import unittest
import importlib.util

_NODES_DIR = os.path.abspath(os.path.join(
    os.path.dirname(__file__), "..",
    "custom_nodes_custom", "tegaki_manga_nodes",
))

def _import_submodule(subname, filename):
    fullname = f"tegaki_manga_nodes.{subname}"
    spec = importlib.util.spec_from_file_location(
        fullname,
        os.path.join(_NODES_DIR, filename),
        submodule_search_locations=[],
    )
    mod = importlib.util.module_from_spec(spec)
    mod.__package__ = "tegaki_manga_nodes"
    sys.modules[fullname] = mod
    spec.loader.exec_module(mod)
    return mod

# Create root package with valid path
pkg = type(sys)("tegaki_manga_nodes")
pkg.__path__ = [_NODES_DIR]
sys.modules["tegaki_manga_nodes"] = pkg

# 1. authoring_contract
_ac = _import_submodule("authoring_contract", "authoring_contract.py")

# 2. interaction_resolver & subscene_contract (needed by scene_spec)
_ir = _import_submodule("interaction_resolver", "interaction_resolver.py")
_sc = _import_submodule("subscene_contract", "subscene_contract.py")

# 3. scene_spec
_ss = _import_submodule("scene_spec", "scene_spec.py")

# 4. authoring_execution_bridge
_aeb = _import_submodule("authoring_execution_bridge", "authoring_execution_bridge.py")

create_document = _ac.create_document
create_page = _ac.create_page
create_scene = _ac.create_scene
make_area = _ac.make_area

validate_m1_execution_document = _aeb.validate_m1_execution_document
compile_document_to_page_plan = _aeb.compile_document_to_page_plan
generate_scene_regions_preview_image = _aeb.generate_scene_regions_preview_image
generate_scene_regions_preview_tensor = _aeb.generate_scene_regions_preview_tensor
get_execution_debug_info = _aeb.get_execution_debug_info
validate_page_compile_plan = _ss.validate_page_compile_plan


class TestM1ExecutionDocumentValidation(unittest.TestCase):
    """Tests for M1 execution validation boundaries."""

    def test_valid_canonical_two_scene_document(self):
        page = create_page(832, 1216, style_prompt="monochrome")
        page["scenes"].append(create_scene("Scene 1", "prompt 1", input_mode="simple", area=make_area(0.1, 0.1, 0.8, 0.35)))
        page["scenes"].append(create_scene("Scene 2", "prompt 2", input_mode="simple", area=make_area(0.1, 0.55, 0.8, 0.35)))
        doc = create_document(pages=[page])

        page_out, warnings = validate_m1_execution_document(doc)
        self.assertIsNotNone(page_out)
        self.assertTrue(isinstance(warnings, list))

    def test_fail_closed_on_zero_scenes(self):
        page = create_page(832, 1216)
        doc = create_document(pages=[page])
        with self.assertRaises(ValueError) as ctx:
            validate_m1_execution_document(doc)
        self.assertIn("at least one scene", str(ctx.exception).lower())

    def test_fail_closed_on_more_than_six_scenes(self):
        page = create_page(832, 1216)
        for i in range(7):
            page["scenes"].append(create_scene(f"Scene {i+1}", f"prompt {i+1}", input_mode="simple", area=make_area(0.1, 0.1 * i, 0.8, 0.1)))
        doc = create_document(pages=[page])

        with self.assertRaises(ValueError) as ctx:
            validate_m1_execution_document(doc)
        self.assertIn("limit of 6 panels", str(ctx.exception))

    def test_fail_closed_on_cast_mode_in_m1(self):
        page = create_page(832, 1216)
        page["scenes"].append(create_scene("Scene 1", "prompt 1", input_mode="cast", area=make_area(0.1, 0.1, 0.8, 0.4)))
        doc = create_document(pages=[page])

        with self.assertRaises(ValueError) as ctx:
            validate_m1_execution_document(doc)
        self.assertIn("cast mode is deferred to m2", str(ctx.exception).lower())

    def test_one_scene_document_is_valid(self):
        page = create_page(832, 1216)
        page["scenes"].append(create_scene("Full Scene", "full page scene", input_mode="simple", area=make_area(0.05, 0.05, 0.9, 0.9)))
        doc = create_document(pages=[page])

        page_out, warnings = validate_m1_execution_document(doc)
        self.assertIsNotNone(page_out)


class TestM1CompileDocumentToPagePlan(unittest.TestCase):
    """Tests for compiling authoring document into PAGE_COMPILE_PLAN."""

    def setUp(self):
        page = create_page(832, 1216, style_prompt="monochrome, screentone", style_negative_prompt="color, 3d")
        page["metadata"]["style_template"] = "Manga Monochrome"
        page["generation"] = {"seed": 12345}
        page["scenes"].append(create_scene(
            "Top Classroom",
            "classroom desks and window",
            negative_prompt="crowd",
            input_mode="simple",
            area=make_area(0.08, 0.06, 0.84, 0.42),
            order=1,
            scene_id="sc_classroom",
        ))
        page["scenes"].append(create_scene(
            "Bottom Train",
            "train station platform dusk",
            negative_prompt="",
            input_mode="simple",
            area=make_area(0.08, 0.52, 0.84, 0.42),
            order=2,
            scene_id="sc_train",
        ))
        self.doc = create_document(pages=[page])

    def test_compile_produces_valid_plan(self):
        plan = compile_document_to_page_plan(self.doc)
        v_res = validate_page_compile_plan(plan)
        self.assertIsNotNone(v_res)

        self.assertEqual(plan["canvas"]["width"], 832)
        self.assertEqual(plan["canvas"]["height"], 1216)
        self.assertEqual(plan["global_prompt"], "monochrome, screentone")
        self.assertEqual(plan["global_negative_prompt"], "color, 3d")
        self.assertEqual(len(plan["panels"]), 2)

        p1 = plan["panels"][0]
        self.assertEqual(p1["target_panel_id"], 1)
        self.assertEqual(p1["panel"]["prompt"], "classroom desks and window")
        self.assertEqual(p1["panel"]["negative_prompt"], "crowd")
        self.assertAlmostEqual(p1["panel"]["geometry"]["x"], 0.08)
        self.assertAlmostEqual(p1["panel"]["geometry"]["y"], 0.06)
        self.assertAlmostEqual(p1["panel"]["geometry"]["w"], 0.84)
        self.assertAlmostEqual(p1["panel"]["geometry"]["h"], 0.42)
        self.assertEqual(p1["characters"], [])

        p2 = plan["panels"][1]
        self.assertEqual(p2["target_panel_id"], 2)
        self.assertEqual(p2["panel"]["prompt"], "train station platform dusk")
        self.assertEqual(p2["characters"], [])

    def test_compile_fails_on_zero_scenes(self):
        empty_page = create_page(832, 1216)
        empty_doc = create_document(pages=[empty_page])
        with self.assertRaises(ValueError):
            compile_document_to_page_plan(empty_doc)


class TestM1SceneRegionsPreviewAndDebug(unittest.TestCase):
    """Tests for mask preview generation and debug info."""

    def setUp(self):
        page = create_page(832, 1216)
        page["scenes"].append(create_scene("Scene 1", "prompt 1", input_mode="simple", area=make_area(0.1, 0.1, 0.8, 0.35)))
        page["scenes"].append(create_scene("Scene 2", "prompt 2", input_mode="simple", area=make_area(0.1, 0.55, 0.8, 0.35)))
        self.doc = create_document(pages=[page])

    def test_preview_image_generation(self):
        img = generate_scene_regions_preview_image(self.doc, width=416, height=608)
        self.assertEqual(img.size, (416, 608))
        self.assertEqual(img.mode, "RGB")

    def test_preview_tensor_generation(self):
        try:
            import torch
            tensor = generate_scene_regions_preview_tensor(self.doc, width=416, height=608)
            self.assertEqual(tensor.shape, (1, 608, 416, 3))
            self.assertEqual(tensor.dtype, torch.float32)
            self.assertTrue(tensor.min() >= 0.0)
            self.assertTrue(tensor.max() <= 1.0)
        except ImportError:
            self.skipTest("torch not installed in test environment")

    def test_execution_debug_info_format(self):
        debug = get_execution_debug_info(self.doc, seed=42)
        self.assertEqual(debug["schema_id"], "TEGAKI_AUTHORING_DOCUMENT")
        self.assertEqual(debug["scene_count"], 2)
        self.assertEqual(debug["seed"], 42)
        self.assertEqual(len(debug["scenes"]), 2)
        self.assertEqual(debug["scenes"][0]["name"], "Scene 1")
        self.assertEqual(debug["scenes"][1]["name"], "Scene 2")


if __name__ == "__main__":
    unittest.main()
