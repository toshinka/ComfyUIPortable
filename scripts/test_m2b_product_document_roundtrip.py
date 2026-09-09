"""
test_m2b_product_document_roundtrip.py — Product UI Node Roundtrip and Workflow Invariants
==========================================================================================
Covers M2B Requirements in Card §92–§98:
1. TegakiMinimumHandSceneEditor node execution roundtrip with CAST and character instances
2. Resolution synchronization (Portrait, Landscape, Square)
3. Style template synchronization
4. Seed synchronization and random seed handling
5. Canonical workflow JSON structure:
   - Root active workflow count == 1
   - Canonical name: workflows/manga/MINIMUM_HAND_MANGA_DRAFT.json
   - No user-facing 'spatial_hint_mode' widget exposed in canonical workflow
   - Node display name in __init__.py is 'Tegaki Minimum-Hand Manga Authoring (Draft)'
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
_ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

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
_shc = _import_submodule("spatial_hint_compiler", "spatial_hint_compiler.py")
_aeb = _import_submodule("authoring_execution_bridge", "authoring_execution_bridge.py")
_editor = _import_submodule("minimum_hand_scene_editor", "minimum_hand_scene_editor.py")
_init = _import_submodule("__init__", "__init__.py")

TegakiMinimumHandSceneEditor = _editor.TegakiMinimumHandSceneEditor
create_document = _ac.create_document
create_page = _ac.create_page
create_scene = _ac.create_scene
create_cast_entry = _ac.create_cast_entry
create_character_instance = _ac.create_character_instance
make_area = _ac.make_area
to_json = _ac.to_json


class TestM2BProductDocumentRoundtrip(unittest.TestCase):
    def setUp(self):
        self.editor = TegakiMinimumHandSceneEditor()

    def test_01_node_execution_roundtrip_with_cast(self):
        """Node executes document containing CAST and Character Instances without data loss."""
        page = create_page(width_px=832, height_px=1216)
        cast_alice = create_cast_entry("Alice", "blonde twin tails, uniform", cast_id="c_alice")
        page["cast"] = [cast_alice]
        s1 = create_scene("Scene 1", "classroom", area=make_area(0.1, 0.1, 0.8, 0.8), scene_id="s1", input_mode="cast")
        page["scenes"] = [s1]
        inst = create_character_instance("c_alice", "s1", make_area(0.2, 0.2, 0.3, 0.5), acting_prompt="reading a book", instance_id="i1")
        page["character_instances"] = [inst]

        doc = create_document(pages=[page])
        doc_json = to_json(doc)

        plan, preview, seed_out, w_out, h_out, debug_json, norm_json = self.editor.edit_and_compile(
            document_json=doc_json,
            seed=777,
        )

        self.assertEqual(seed_out, 777)
        self.assertEqual(w_out, 832)
        self.assertEqual(h_out, 1216)
        self.assertIsNotNone(plan)
        self.assertIsNotNone(preview)

        # Parse normalized doc JSON
        norm_doc = json.loads(norm_json)
        self.assertEqual(len(norm_doc["pages"][0]["cast"]), 1)
        self.assertEqual(norm_doc["pages"][0]["cast"][0]["cast_id"], "c_alice")
        self.assertEqual(len(norm_doc["pages"][0]["character_instances"]), 1)
        self.assertEqual(norm_doc["pages"][0]["character_instances"][0]["acting_prompt"], "reading a book")

        # Check debug info transparent provenance
        debug_data = json.loads(debug_json)
        self.assertEqual(debug_data["spatial_policy"], "auto")
        self.assertEqual(debug_data["widget_seed"], 777)

    def test_02_resolution_and_style_sync(self):
        """Resolution and style template inputs synchronize into document."""
        page = create_page(width_px=832, height_px=1216)
        s1 = create_scene("Scene 1", "classroom", area=make_area(0.1, 0.1, 0.8, 0.8), scene_id="s1", input_mode="simple")
        page["scenes"] = [s1]
        doc = create_document(pages=[page])

        plan, preview, seed_out, w_out, h_out, debug_json, norm_json = self.editor.edit_and_compile(
            document_json=to_json(doc),
            seed=101,
            resolution="Landscape 1216x832",
            style_template="Manga Color",
        )

        self.assertEqual(w_out, 1216)
        self.assertEqual(h_out, 832)
        norm_doc = json.loads(norm_json)
        self.assertEqual(norm_doc["pages"][0]["width_px"], 1216)
        self.assertEqual(norm_doc["pages"][0]["height_px"], 832)
        self.assertEqual(norm_doc["pages"][0]["metadata"]["style_template"], "Manga Color")

    def test_03_display_name_mapping(self):
        """Display name for TegakiMinimumHandSceneEditor is updated to M2B Product title."""
        self.assertIn("TegakiMinimumHandSceneEditor", _init.NODE_DISPLAY_NAME_MAPPINGS)
        d_name = _init.NODE_DISPLAY_NAME_MAPPINGS["TegakiMinimumHandSceneEditor"]
        self.assertEqual(d_name, "Tegaki Minimum-Hand Manga Authoring (Draft)")

    def test_04_spatial_hint_mode_not_in_input_types(self):
        """spatial_hint_mode must NOT be exposed as an optional or required input widget."""
        input_types = TegakiMinimumHandSceneEditor.INPUT_TYPES()
        required = input_types.get("required", {})
        optional = input_types.get("optional", {})
        self.assertNotIn("spatial_hint_mode", required)
        self.assertNotIn("spatial_hint_mode", optional)

    def test_05_canonical_workflow_invariants(self):
        """Canonical workflow at workflows/manga/MINIMUM_HAND_MANGA_DRAFT.json satisfies all invariants."""
        wf_path = os.path.join(_ROOT_DIR, "workflows", "manga", "MINIMUM_HAND_MANGA_DRAFT.json")
        self.assertTrue(os.path.exists(wf_path), f"Canonical workflow missing: {wf_path}")

        # Check only 1 json file at workflows root
        wf_dir = os.path.join(_ROOT_DIR, "workflows", "manga")
        root_jsons = [f for f in os.listdir(wf_dir) if f.endswith(".json") and os.path.isfile(os.path.join(wf_dir, f))]
        self.assertEqual(root_jsons, ["MINIMUM_HAND_MANGA_DRAFT.json"], f"Found unexpected root workflows: {root_jsons}")

        with open(wf_path, "r", encoding="utf-8") as f:
            raw_text = f.read()
            wf = json.loads(raw_text)

        # Invariant: no spatial_hint_mode widget in workflow
        self.assertNotIn('"spatial_hint_mode"', raw_text)

        # Invariant: TegakiMinimumHandSceneEditor node present
        nodes = wf.get("nodes", [])
        editor_node = next((n for n in nodes if n.get("type") == "TegakiMinimumHandSceneEditor"), None)
        self.assertIsNotNone(editor_node, "TegakiMinimumHandSceneEditor missing from canonical workflow")


if __name__ == "__main__":
    unittest.main()
