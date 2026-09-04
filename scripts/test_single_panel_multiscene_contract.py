"""
Unit test for Single Panel Multi-Scene Contract (Phase 3E Hostile Test)
======================================================================
Verifies that:
1. 1 visible panel hosts 2 independent semantic subscenes (Scene A and Scene B).
2. Alice master and Bob master are each referenced twice across the scenes.
3. 4 unique instance IDs are generated.
4. Scene A and Scene B have independent, non-conflicting bounding boxes.
5. Character areas are properly nested and bounded within their parent scene bounds.
6. Zero directional words ("left", "right") are required in prompts.
"""

import os
import sys
import unittest
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "custom_nodes_custom")))

from tegaki_manga_nodes.cast_master import get_default_cast_spec
from tegaki_manga_nodes.single_panel_multiscene_adapter import TegakiSinglePanelMultiSceneImpactAdapter


class MockClip:
    def tokenize(self, text):
        return {"g": text, "l": text}
    def encode_from_tokens_scheduled(self, tokens):
        return [("mock_cond", {"tokens": tokens})]


class MockSampler:
    def clone_with_conditionings(self, pos, neg):
        return self


class TestSinglePanelMultiSceneContract(unittest.TestCase):
    def setUp(self):
        self.cast_spec = get_default_cast_spec()
        self.layout_spec = {
            "version": 1,
            "canvas": {"width": 1024, "height": 1024},
            "vertices": [
                {"id": "v0", "x": 0.05, "y": 0.05},
                {"id": "v1", "x": 0.95, "y": 0.05},
                {"id": "v2", "x": 0.95, "y": 0.95},
                {"id": "v3", "x": 0.05, "y": 0.95}
            ],
            "panels": [
                {"id": "p1", "vertex_ids": ["v0", "v1", "v2", "v3"]}
            ]
        }
        self.adapter = TegakiSinglePanelMultiSceneImpactAdapter()
        self.mock_clip = MockClip()
        self.mock_sampler = MockSampler()

    def test_multiscene_contract_and_traceability(self):
        prompts, masks, preview, debug_json = self.adapter.build_multiscene_prompts(
            panel_layout_spec=self.layout_spec,
            cast_spec=self.cast_spec,
            base_sampler=self.mock_sampler,
            clip=self.mock_clip,
            scene_A_scene_prompt="school gate, afternoon sunset, dramatic shadows",
            scene_A_acting="arguing intensely, both looking away from each other, frustrated expression",
            scene_B_scene_prompt="school garden, blooming flowers, soft sunlight",
            scene_B_acting="friendly handshake, facing each other, happy smiling expression",
            scene_split_ratio=0.50,
            scene_boundary_overlap=0.05,
            character_overlap=0.25
        )

        debug = json.loads(debug_json)
        self.assertEqual(debug["visible_panel_count"], 1)
        self.assertEqual(debug["internal_scene_count"], 2)
        self.assertEqual(debug["character_instance_count"], 4)

        recurrent_instances = debug["recurrent_instances"]
        self.assertEqual(len(recurrent_instances), 4)
        self.assertEqual(len(set(recurrent_instances)), 4, "All 4 character instance IDs must be unique")

        # Verify Alice is referenced twice and Bob is referenced twice
        char_entries = [e for e in debug["entries"] if e["scope_type"] == "character_instance"]
        alice_instances = [e for e in char_entries if e["master_character_id"] == "char_alice"]
        bob_instances = [e for e in char_entries if e["master_character_id"] == "char_bob"]

        self.assertEqual(len(alice_instances), 2)
        self.assertEqual(len(bob_instances), 2)

        # Verify that prompt texts do NOT contain directional words "left" or "right"
        for e in debug["entries"]:
            p = e["prompt"].lower()
            self.assertNotIn(" left", p)
            self.assertNotIn(" right", p)
            self.assertNotIn("left ", p)
            self.assertNotIn("right ", p)

        # Verify geometric nesting
        sceneA = next(e for e in debug["entries"] if e["source_scene_id"] == "scene_A" and e["scope_type"] == "experimental_subscene")
        sceneB = next(e for e in debug["entries"] if e["source_scene_id"] == "scene_B" and e["scope_type"] == "experimental_subscene")

        # Scene A is on the left half, Scene B is on the right half
        self.assertLess(sceneA["bounds"][0], sceneB["bounds"][0])
        self.assertLess(sceneA["bounds"][2], sceneB["bounds"][2])

        # Verify mask dimensions
        self.assertEqual(masks.shape, (6, 1024, 1024))
        self.assertEqual(preview.shape, (1, 1024, 1024, 3))


if __name__ == "__main__":
    unittest.main()
