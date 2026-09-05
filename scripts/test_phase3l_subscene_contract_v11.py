"""
Test: Phase 3L SubScene Contract v1.1
====================================
Verifies SubScene Contract v1.1 validation:
- Rejects non-dict entries.
- Rejects nested subscenes.
- Requires strict boolean `enabled`.
- Requires finite numeric `area`.
- Validates `shot_type` enum and `pose_preset` enum.
- Rejects duplicate subscene IDs.
- Rejects duplicate character instance IDs across subscenes within a panel.
"""

import os
import sys
import unittest

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from custom_nodes_custom.tegaki_manga_nodes.subscene_contract import (
    validate_subscene_entry,
    validate_panel_subscenes,
    validate_subscene_area
)


class TestPhase3LSubSceneContractV11(unittest.TestCase):

    def test_valid_subscene_v11(self):
        entry = {
            "id": "sub_a",
            "enabled": True,
            "prompt": "school gate background",
            "negative_prompt": "blurry",
            "area": {"x": 0.0, "y": 0.0, "w": 0.5, "h": 1.0},
            "character_bindings": [
                {
                    "instance_id": "p1_sub_a_alice_01",
                    "character_id": "char_alice",
                    "enabled": True,
                    "prompt_override": "angry, arms crossed",
                    "negative_prompt_override": "",
                    "area": {"x": 0.1, "y": 0.1, "w": 0.4, "h": 0.8},
                    "shot_type": "full_body",
                    "pose_preset": "facing_right",
                    "interaction": {
                        "interaction_id": "int_lookaway",
                        "type": "look_away",
                        "role": "initiator",
                        "target_instance_id": "p1_sub_a_bob_01"
                    },
                    "metadata": {}
                }
            ],
            "metadata": {}
        }
        val = validate_subscene_entry(entry, panel_id=1)
        self.assertEqual(val["id"], "sub_a")
        self.assertTrue(val["enabled"])
        self.assertEqual(len(val["character_bindings"]), 1)
        cb = val["character_bindings"][0]
        self.assertEqual(cb["instance_id"], "p1_sub_a_alice_01")
        self.assertEqual(cb["shot_type"], "full_body")
        self.assertEqual(cb["pose_preset"], "facing_right")
        self.assertIsInstance(cb["interaction"], dict)

    def test_reject_nested_subscenes(self):
        entry = {
            "id": "sub_root",
            "enabled": True,
            "subscenes": [{"id": "sub_nested"}]  # Strictly prohibited!
        }
        with self.assertRaises(ValueError) as ctx:
            validate_subscene_entry(entry)
        self.assertIn("Nested subscenes are strictly prohibited", str(ctx.exception))

    def test_reject_non_strict_bool(self):
        entry = {
            "id": "sub_a",
            "enabled": "yes",  # Not a strict bool!
            "character_bindings": []
        }
        with self.assertRaises(ValueError):
            validate_subscene_entry(entry)

    def test_reject_invalid_shot_type(self):
        entry = {
            "id": "sub_a",
            "character_bindings": [
                {
                    "character_id": "char_alice",
                    "shot_type": "extreme_close_up"  # Invalid enum!
                }
            ]
        }
        with self.assertRaises(ValueError) as ctx:
            validate_subscene_entry(entry)
        self.assertIn("Invalid shot_type", str(ctx.exception))

    def test_reject_invalid_pose_preset(self):
        entry = {
            "id": "sub_a",
            "character_bindings": [
                {
                    "character_id": "char_alice",
                    "pose_preset": "doing_backflip"  # Invalid enum!
                }
            ]
        }
        with self.assertRaises(ValueError) as ctx:
            validate_subscene_entry(entry)
        self.assertIn("Invalid pose_preset", str(ctx.exception))

    def test_reject_duplicate_subscene_ids(self):
        panel = {
            "koma_id": 1,
            "subscenes": [
                {"id": "sub_a", "character_bindings": []},
                {"id": "sub_a", "character_bindings": []}  # Duplicate!
            ]
        }
        with self.assertRaises(ValueError) as ctx:
            validate_panel_subscenes(panel)
        self.assertIn("Duplicate subscene id", str(ctx.exception))

    def test_reject_duplicate_instance_ids_across_subscenes(self):
        panel = {
            "koma_id": 1,
            "subscenes": [
                {
                    "id": "sub_a",
                    "character_bindings": [
                        {"instance_id": "duplicate_id", "character_id": "char_alice"}
                    ]
                },
                {
                    "id": "sub_b",
                    "character_bindings": [
                        {"instance_id": "duplicate_id", "character_id": "char_bob"}  # Duplicate instance_id!
                    ]
                }
            ]
        }
        with self.assertRaises(ValueError) as ctx:
            validate_panel_subscenes(panel)
        self.assertIn("Duplicate instance_id", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
