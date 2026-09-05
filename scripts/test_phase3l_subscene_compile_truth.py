"""
Test: Phase 3L SubScene Compile Truth
=====================================
Verifies that `SceneCompiler`:
- Mainline compiler combines CAST master prompt with SubScene binding override.
- Compiles both positive prompt and negative prompt.
- Retains stable instance IDs, shot_type, pose_preset, interaction.
- Produces valid COMPILE_PLAN and PAGE_COMPILE_PLAN containing SubScenes.
"""

import os
import sys
import unittest

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from custom_nodes_custom.tegaki_manga_nodes.scene_compiler import compile_panel_data, TegakiMangaPageCompiler


class TestPhase3LSubSceneCompileTruth(unittest.TestCase):

    def setUp(self):
        self.cast_spec = {
            "version": 1,
            "characters": [
                {
                    "id": "char_alice",
                    "name": "Alice",
                    "prompt": "1girl, blonde hair",
                    "negative_prompt": "1boy, ugly",
                    "enabled": True
                },
                {
                    "id": "char_bob",
                    "name": "Bob",
                    "prompt": "1boy, dark hair",
                    "negative_prompt": "1girl",
                    "enabled": True
                }
            ]
        }
        self.region_spec = {
            "version": 1,
            "canvas": {"width": 832, "height": 1216},
            "panel_count": 1,
            "global_prompt": "masterpiece, manga style",
            "global_negative_prompt": "bad anatomy",
            "regions": [
                {
                    "id": 1,
                    "x": 0.0,
                    "y": 0.0,
                    "w": 1.0,
                    "h": 1.0,
                    "prompt": "classroom",
                    "negative_prompt": "blurry",
                    "characters": [],
                    "subscenes": [
                        {
                            "id": "sub_a",
                            "enabled": True,
                            "prompt": "school gate",
                            "negative_prompt": "watermark",
                            "area": {"x": 0.0, "y": 0.0, "w": 0.5, "h": 1.0},
                            "character_bindings": [
                                {
                                    "instance_id": "p1_sub_a_alice_01",
                                    "character_id": "char_alice",
                                    "prompt_override": "angry expression, arms crossed",
                                    "negative_prompt_override": "smiling",
                                    "shot_type": "full_body",
                                    "pose_preset": "facing_right",
                                    "interaction": {
                                        "interaction_id": "int_p1_01",
                                        "type": "look_away",
                                        "role": "initiator",
                                        "target_instance_id": "p1_sub_a_bob_01"
                                    }
                                }
                            ]
                        }
                    ]
                }
            ]
        }

    def test_compile_panel_with_subscenes(self):
        plan, plan_json, compiled_prompt, char_count = compile_panel_data(
            region_spec=self.region_spec,
            target_panel_id=1,
            cast_spec=self.cast_spec
        )
        self.assertEqual(plan["status"], "active")
        self.assertIn("subscenes", plan["panel"])
        subscenes = plan["panel"]["subscenes"]
        self.assertEqual(len(subscenes), 1)

        sub_a = subscenes[0]
        self.assertEqual(sub_a["id"], "sub_a")
        self.assertEqual(sub_a["prompt"], "school gate")
        self.assertEqual(len(sub_a["characters"]), 1)

        char_inst = sub_a["characters"][0]
        self.assertEqual(char_inst["instance_id"], "p1_sub_a_alice_01")
        self.assertEqual(char_inst["character_id"], "char_alice")
        self.assertEqual(char_inst["shot_type"], "full_body")
        self.assertEqual(char_inst["pose_preset"], "facing_right")
        self.assertIn("1girl, blonde hair", char_inst["combined_prompt"])
        self.assertIn("angry expression, arms crossed", char_inst["combined_prompt"])
        self.assertIn("smiling", char_inst["combined_negative_prompt"])
        self.assertEqual(char_inst["interaction"]["type"], "look_away")

    def test_page_compiler_with_subscenes(self):
        page_compiler = TegakiMangaPageCompiler()
        page_plan, page_json, global_loras, active_panels = page_compiler.compile_page(
            region_spec=self.region_spec,
            cast_spec=self.cast_spec
        )
        self.assertEqual(active_panels, 1)
        self.assertEqual(len(page_plan["panels"]), 1)
        panel_0 = page_plan["panels"][0]["panel"]
        self.assertIn("subscenes", panel_0)
        self.assertEqual(len(panel_0["subscenes"]), 1)


if __name__ == "__main__":
    unittest.main()
