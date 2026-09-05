"""
test_m1_scene_editor_document.py — M1 Scene Editor Node & Document Tests
========================================================================
Tests for TegakiMinimumHandSceneEditor node, create_default_m1_document,
resolution presets, style templates, and JSON synchronization.
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

pkg = type(sys)("tegaki_manga_nodes")
pkg.__path__ = [_NODES_DIR]
sys.modules["tegaki_manga_nodes"] = pkg

_ac = _import_submodule("authoring_contract", "authoring_contract.py")
_ir = _import_submodule("interaction_resolver", "interaction_resolver.py")
_sc = _import_submodule("subscene_contract", "subscene_contract.py")
_ss = _import_submodule("scene_spec", "scene_spec.py")
_aeb = _import_submodule("authoring_execution_bridge", "authoring_execution_bridge.py")
_mse = _import_submodule("minimum_hand_scene_editor", "minimum_hand_scene_editor.py")

validate_document = _ac.validate_document
create_default_m1_document = _mse.create_default_m1_document
TegakiMinimumHandSceneEditor = _mse.TegakiMinimumHandSceneEditor
RESOLUTION_PRESETS = _mse.RESOLUTION_PRESETS
STYLE_TEMPLATES = _mse.STYLE_TEMPLATES


class TestM1DefaultDocument(unittest.TestCase):
    """Tests for create_default_m1_document."""

    def test_default_document_validity(self):
        doc = create_default_m1_document()
        v_res = validate_document(doc)
        self.assertTrue(v_res.valid, f"Validation errors: {v_res.errors}")

        self.assertEqual(doc["schema_id"], "TEGAKI_AUTHORING_DOCUMENT")
        self.assertEqual(doc["schema_version"], "1.0.0")
        self.assertEqual(len(doc["pages"]), 1)

        page = doc["pages"][0]
        self.assertEqual(page["width_px"], 832)
        self.assertEqual(page["height_px"], 1216)
        self.assertEqual(len(page["scenes"]), 2)

        s1 = page["scenes"][0]
        self.assertEqual(s1["input_mode"], "simple")
        self.assertEqual(s1["order"], 1)
        self.assertIn("classroom", s1["prompt"].lower())

        s2 = page["scenes"][1]
        self.assertEqual(s2["input_mode"], "simple")
        self.assertEqual(s2["order"], 2)
        self.assertIn("train", s2["prompt"].lower())

    def test_presets_customization(self):
        doc = create_default_m1_document(
            width=1216,
            height=832,
            style_template_name="Manga Color",
            seed=999,
        )
        page = doc["pages"][0]
        self.assertEqual(page["width_px"], 1216)
        self.assertEqual(page["height_px"], 832)
        self.assertEqual(page["metadata"]["style_template"], "Manga Color")
        self.assertEqual(page["generation"]["seed"], 999)
        self.assertIn("color manga page", page["style_prompt"].lower())


class TestTegakiMinimumHandSceneEditorNode(unittest.TestCase):
    """Tests for node execution and interface contract."""

    def setUp(self):
        self.node = TegakiMinimumHandSceneEditor()

    def test_input_types(self):
        inputs = self.node.INPUT_TYPES()
        self.assertIn("required", inputs)
        self.assertIn("document_json", inputs["required"])
        self.assertIn("seed", inputs["required"])
        self.assertIn("optional", inputs)
        self.assertIn("resolution", inputs["optional"])
        self.assertIn("style_template", inputs["optional"])

    def test_return_types(self):
        self.assertEqual(len(self.node.RETURN_TYPES), 7)
        self.assertEqual(self.node.RETURN_TYPES[0], "PAGE_COMPILE_PLAN")
        self.assertEqual(self.node.RETURN_TYPES[1], "IMAGE")
        self.assertEqual(self.node.RETURN_TYPES[2], "INT")
        self.assertEqual(self.node.RETURN_TYPES[3], "INT")
        self.assertEqual(self.node.RETURN_TYPES[4], "INT")
        self.assertEqual(self.node.RETURN_TYPES[5], "STRING")
        self.assertEqual(self.node.RETURN_TYPES[6], "STRING")

    def test_node_execution_default(self):
        default_doc = create_default_m1_document()
        doc_json = json.dumps(default_doc)

        outputs = self.node.edit_and_compile(
            document_json=doc_json,
            seed=42,
            resolution="Portrait 832x1216",
            style_template="Manga Monochrome",
        )

        self.assertEqual(len(outputs), 7)
        plan, preview, seed, width, height, debug_json, out_doc_json = outputs

        self.assertEqual(plan["canvas"]["width"], 832)
        self.assertEqual(plan["canvas"]["height"], 1216)
        self.assertEqual(len(plan["panels"]), 2)
        self.assertEqual(seed, 42)
        self.assertEqual(width, 832)
        self.assertEqual(height, 1216)

        debug = json.loads(debug_json)
        self.assertEqual(debug["scene_count"], 2)
        self.assertEqual(debug["seed"], 42)

        out_doc = json.loads(out_doc_json)
        self.assertEqual(out_doc["schema_id"], "TEGAKI_AUTHORING_DOCUMENT")

    def test_node_execution_resolution_override(self):
        default_doc = create_default_m1_document()
        doc_json = json.dumps(default_doc)

        outputs = self.node.edit_and_compile(
            document_json=doc_json,
            seed=777,
            resolution="Landscape 1216x832",
            style_template="Manga Color",
        )

        plan, preview, seed, width, height, debug_json, out_doc_json = outputs
        self.assertEqual(width, 1216)
        self.assertEqual(height, 832)
        self.assertEqual(seed, 777)
        self.assertEqual(plan["canvas"]["width"], 1216)
        self.assertEqual(plan["canvas"]["height"], 832)

    def test_node_execution_rejects_zero_scenes(self):
        empty_page = _ac.create_page(832, 1216)
        empty_doc = _ac.create_document(pages=[empty_page])
        doc_json = json.dumps(empty_doc)

        with self.assertRaises(ValueError):
            self.node.edit_and_compile(document_json=doc_json, seed=42)


if __name__ == "__main__":
    unittest.main()
