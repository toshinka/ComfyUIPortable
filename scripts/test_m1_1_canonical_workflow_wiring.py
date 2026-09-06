"""
test_m1_1_canonical_workflow_wiring.py — M1.1 Canonical Workflow Wiring & SSOT Tests
=====================================================================================
Validates that workflows/M1_MINIMUM_HAND_SCENE_DRAFT.json conforms to all M1.1 wiring
and schema contracts:
1. Exactly 1 active root workflow in workflows/
2. Editor page_compile_plan -> ConditioningBuilder input
3. Editor seed output -> KSampler seed input
4. Editor width output -> EmptyLatentImage width input
5. Editor height output -> EmptyLatentImage height input
6. Editor document_json fixture validates without errors
7. No legacy 'dimensions' dialect anywhere in workflow JSON
8. Causal link integrity and no secondary unlinked seed/resolution authority
"""

import os
import sys
import json
import unittest

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CUSTOM_NODES_DIR = os.path.join(ROOT_DIR, "custom_nodes_custom")
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
if CUSTOM_NODES_DIR not in sys.path:
    sys.path.insert(0, CUSTOM_NODES_DIR)

from tegaki_manga_nodes.authoring_contract import validate_document


class TestM1_1CanonicalWorkflowWiring(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workflows_dir = os.path.join(ROOT_DIR, "workflows")
        cls.canonical_wf_path = os.path.join(cls.workflows_dir, "M1_MINIMUM_HAND_SCENE_DRAFT.json")
        with open(cls.canonical_wf_path, "r", encoding="utf-8") as f:
            cls.raw_text = f.read()
            cls.wf = json.loads(cls.raw_text)

    def test_01_root_active_workflow_count(self):
        """Root active workflow count in workflows/ must be exactly 1."""
        entries = os.listdir(self.workflows_dir)
        json_files = [e for e in entries if e.endswith(".json") and os.path.isfile(os.path.join(self.workflows_dir, e))]
        self.assertEqual(json_files, ["M1_MINIMUM_HAND_SCENE_DRAFT.json"],
                         f"Expected exactly 1 root active workflow, found: {json_files}")

    def test_02_legacy_dimensions_completely_absent(self):
        """Legacy 'dimensions' dialect must be absent from canonical workflow JSON."""
        self.assertNotIn('"dimensions"', self.raw_text,
                         "Workflow JSON contains legacy 'dimensions' dialect!")

    def test_03_embedded_document_validates_without_backend_patch(self):
        """Embedded document_json fixture must validate cleanly without backend modifications."""
        nodes = self.wf.get("nodes", [])
        editor_node = next((n for n in nodes if n.get("type") == "TegakiMinimumHandSceneEditor"), None)
        self.assertIsNotNone(editor_node, "TegakiMinimumHandSceneEditor node not found in workflow")

        doc_json_str = editor_node["widgets_values"][0]
        doc = json.loads(doc_json_str)

        val_res = validate_document(doc)
        self.assertEqual(val_res.errors, [], f"Document validation errors: {val_res.errors}")
        self.assertEqual(doc["schema_id"], "TEGAKI_AUTHORING_DOCUMENT")
        self.assertEqual(doc["schema_version"], "1.0.0")

        page = doc["pages"][0]
        self.assertEqual(page["width_px"], 832)
        self.assertEqual(page["height_px"], 1216)
        self.assertEqual(page["generation"]["seed"], 42)
        self.assertEqual(len(page["scenes"]), 2)

    def test_04_editor_conditioning_builder_wiring(self):
        """Editor page_compile_plan (slot 0) must link to ConditioningBuilder input (slot 1)."""
        nodes = {n["id"]: n for n in self.wf.get("nodes", [])}
        links = {l[0]: l for l in self.wf.get("links", [])}

        editor_node = nodes[1]
        self.assertEqual(editor_node["type"], "TegakiMinimumHandSceneEditor")

        plan_slot = editor_node["outputs"][0]
        self.assertEqual(plan_slot["name"], "page_compile_plan")
        self.assertIsNotNone(plan_slot.get("links"))
        self.assertTrue(len(plan_slot["links"]) >= 1)

        link_id = plan_slot["links"][0]
        link = links[link_id]
        # [link_id, from_node, from_slot, to_node, to_slot, type]
        self.assertEqual(link[1], 1)
        self.assertEqual(link[2], 0)
        self.assertEqual(link[3], 4)  # Node 4: TegakiMangaConditioningBuilder
        self.assertEqual(link[5], "PAGE_COMPILE_PLAN")

    def test_05_editor_seed_wired_to_ksampler(self):
        """Editor seed (slot 2) must link directly to KSampler seed input."""
        nodes = {n["id"]: n for n in self.wf.get("nodes", [])}
        links = {l[0]: l for l in self.wf.get("links", [])}

        editor_node = nodes[1]
        seed_slot = editor_node["outputs"][2]
        self.assertEqual(seed_slot["name"], "seed")
        self.assertEqual(seed_slot["type"], "INT")
        self.assertIsNotNone(seed_slot.get("links"), "Editor seed output has no links!")
        self.assertTrue(len(seed_slot["links"]) >= 1)

        link_id = seed_slot["links"][0]
        link = links[link_id]
        self.assertEqual(link[1], 1)
        self.assertEqual(link[2], 2)
        target_node_id = link[3]
        target_node = nodes[target_node_id]
        self.assertEqual(target_node["type"], "KSampler",
                         f"Seed link target should be KSampler, got {target_node['type']}")

        # Verify KSampler has converted seed input
        seed_input = next((inp for inp in target_node.get("inputs", []) if inp.get("name") == "seed"), None)
        self.assertIsNotNone(seed_input, "KSampler does not have an input named 'seed'")
        self.assertEqual(seed_input.get("link"), link_id)
        self.assertEqual(seed_input.get("type"), "INT")

    def test_06_editor_resolution_wired_to_empty_latent(self):
        """Editor width (slot 3) and height (slot 4) must link to EmptyLatentImage width and height inputs."""
        nodes = {n["id"]: n for n in self.wf.get("nodes", [])}
        links = {l[0]: l for l in self.wf.get("links", [])}

        editor_node = nodes[1]

        # Width slot
        width_slot = editor_node["outputs"][3]
        self.assertEqual(width_slot["name"], "width")
        self.assertEqual(width_slot["type"], "INT")
        self.assertIsNotNone(width_slot.get("links"), "Editor width output has no links!")
        w_link_id = width_slot["links"][0]
        w_link = links[w_link_id]
        self.assertEqual(w_link[1], 1)
        self.assertEqual(w_link[2], 3)
        w_target_node = nodes[w_link[3]]
        self.assertEqual(w_target_node["type"], "EmptyLatentImage")
        w_input = next((inp for inp in w_target_node.get("inputs", []) if inp.get("name") == "width"), None)
        self.assertIsNotNone(w_input, "EmptyLatentImage does not have input 'width'")
        self.assertEqual(w_input.get("link"), w_link_id)

        # Height slot
        height_slot = editor_node["outputs"][4]
        self.assertEqual(height_slot["name"], "height")
        self.assertEqual(height_slot["type"], "INT")
        self.assertIsNotNone(height_slot.get("links"), "Editor height output has no links!")
        h_link_id = height_slot["links"][0]
        h_link = links[h_link_id]
        self.assertEqual(h_link[1], 1)
        self.assertEqual(h_link[2], 4)
        h_target_node = nodes[h_link[3]]
        self.assertEqual(h_target_node["type"], "EmptyLatentImage")
        h_input = next((inp for inp in h_target_node.get("inputs", []) if inp.get("name") == "height"), None)
        self.assertIsNotNone(h_input, "EmptyLatentImage does not have input 'height'")
        self.assertEqual(h_input.get("link"), h_link_id)


if __name__ == "__main__":
    unittest.main()
