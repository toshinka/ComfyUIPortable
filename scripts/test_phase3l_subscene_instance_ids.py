"""
Test: Phase 3L SubScene Same-Cast Multi-Instance IDs
===================================================
Verifies that:
- Same CAST master character can appear in multiple SubScenes within the same panel.
- Master IDs are identical (e.g. 'char_alice').
- Instance IDs are distinct (e.g. 'p1_sub_a_alice_01' vs 'p1_sub_b_alice_01').
- Acting prompts, poses, and interaction relations remain completely isolated per instance.
"""

import os
import sys
import unittest

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from custom_nodes_custom.tegaki_manga_nodes.scene_compiler import compile_panel_data


class TestPhase3LSubSceneInstanceIDs(unittest.TestCase):

    def test_same_cast_multiple_subscene_instances(self):
        cast_spec = {
            "version": 1,
            "characters": [
                {
                    "id": "char_alice",
                    "name": "Alice",
                    "prompt": "1girl, blonde twin tails, blue eyes",
                    "negative_prompt": "blurry",
                    "enabled": True
                },
                {
                    "id": "char_bob",
                    "name": "Bob",
                    "prompt": "1boy, short dark hair",
                    "negative_prompt": "blurry",
                    "enabled": True
                }
            ]
        }

        # 1 visible panel, 2 internal subscenes
        region_spec = {
            "version": 1,
            "canvas": {"width": 832, "height": 1216},
            "panel_count": 1,
            "global_prompt": "manga page",
            "global_negative_prompt": "bad hands",
            "regions": [
                {
                    "id": 1,
                    "x": 0.0,
                    "y": 0.0,
                    "w": 1.0,
                    "h": 1.0,
                    "prompt": "school grounds",
                    "negative_prompt": "",
                    "characters": [],
                    "subscenes": [
                        {
                            "id": "sub_a",
                            "enabled": True,
                            "prompt": "school gate, conflict",
                            "area": {"x": 0.0, "y": 0.0, "w": 0.5, "h": 1.0},
                            "character_bindings": [
                                {
                                    "instance_id": "p1_sub_a_alice_01",
                                    "character_id": "char_alice",
                                    "prompt_override": "angry expression",
                                    "pose_preset": "facing_left",
                                    "interaction": {
                                        "interaction_id": "int_lookaway",
                                        "type": "look_away",
                                        "role": "left_participant",
                                        "target_instance_id": "p1_sub_a_bob_01"
                                    }
                                },
                                {
                                    "instance_id": "p1_sub_a_bob_01",
                                    "character_id": "char_bob",
                                    "prompt_override": "annoyed expression",
                                    "pose_preset": "facing_right",
                                    "interaction": {
                                        "interaction_id": "int_lookaway",
                                        "type": "look_away",
                                        "role": "right_participant",
                                        "target_instance_id": "p1_sub_a_alice_01"
                                    }
                                }
                            ]
                        },
                        {
                            "id": "sub_b",
                            "enabled": True,
                            "prompt": "school garden, friendship",
                            "area": {"x": 0.5, "y": 0.0, "w": 0.5, "h": 1.0},
                            "character_bindings": [
                                {
                                    "instance_id": "p1_sub_b_alice_01",
                                    "character_id": "char_alice",
                                    "prompt_override": "smiling expression",
                                    "pose_preset": "facing_right",
                                    "interaction": {
                                        "interaction_id": "int_handshake",
                                        "type": "handshake",
                                        "role": "left_participant",
                                        "target_instance_id": "p1_sub_b_bob_01"
                                    }
                                },
                                {
                                    "instance_id": "p1_sub_b_bob_01",
                                    "character_id": "char_bob",
                                    "prompt_override": "cheerful expression",
                                    "pose_preset": "facing_left",
                                    "interaction": {
                                        "interaction_id": "int_handshake",
                                        "type": "handshake",
                                        "role": "right_participant",
                                        "target_instance_id": "p1_sub_b_alice_01"
                                    }
                                }
                            ]
                        }
                    ]
                }
            ]
        }

        plan, _, _, total_chars = compile_panel_data(
            region_spec=region_spec,
            target_panel_id=1,
            cast_spec=cast_spec
        )

        self.assertEqual(total_chars, 4)
        subscenes = plan["panel"]["subscenes"]
        self.assertEqual(len(subscenes), 2)

        sub_a_chars = {c["instance_id"]: c for c in subscenes[0]["characters"]}
        sub_b_chars = {c["instance_id"]: c for c in subscenes[1]["characters"]}

        # Check Alice instances
        alice_a = sub_a_chars["p1_sub_a_alice_01"]
        alice_b = sub_b_chars["p1_sub_b_alice_01"]
        self.assertEqual(alice_a["character_id"], alice_b["character_id"])
        self.assertNotEqual(alice_a["instance_id"], alice_b["instance_id"])
        self.assertIn("angry expression", alice_a["combined_prompt"])
        self.assertIn("smiling expression", alice_b["combined_prompt"])
        self.assertEqual(alice_a["pose_preset"], "facing_left")
        self.assertEqual(alice_b["pose_preset"], "facing_right")
        self.assertEqual(alice_a["interaction"]["type"], "look_away")
        self.assertEqual(alice_b["interaction"]["type"], "handshake")

        # Check Bob instances
        bob_a = sub_a_chars["p1_sub_a_bob_01"]
        bob_b = sub_b_chars["p1_sub_b_bob_01"]
        self.assertEqual(bob_a["character_id"], bob_b["character_id"])
        self.assertNotEqual(bob_a["instance_id"], bob_b["instance_id"])
        self.assertIn("annoyed expression", bob_a["combined_prompt"])
        self.assertIn("cheerful expression", bob_b["combined_prompt"])


if __name__ == "__main__":
    unittest.main()
