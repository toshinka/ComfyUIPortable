"""
Test Phase 3J.1: Impact Character Prompt Truth and Region Isolation
===================================================================
Verifies:
1. For character_instance regions in IMPACT_REGION_PLAN:
   - prompt is non-empty
   - in standalone mode, prompt is NOT identical to panel scene prompt
   - master_character_id is preserved
   - pixel_bounds is correctly computed
2. For panel_scene regions in IMPACT_REGION_PLAN:
   - in remainder_mask_mode=True, scene mask subtracts character masks
     (character staging area has zero scene mask coverage)
3. In scene_composed mode, prompt merges panel prompt and character prompt
"""

import os
import sys
import json
import unittest
import torch

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
COMFY_DIR = os.path.join(ROOT_DIR, "ComfyUI")
CUSTOM_NODES_DIR = os.path.join(ROOT_DIR, "custom_nodes_custom")
IMPACT_PACK_DIR = os.path.join(COMFY_DIR, "custom_nodes", "ComfyUI-Impact-Pack", "modules")

for p in [ROOT_DIR, COMFY_DIR, CUSTOM_NODES_DIR, IMPACT_PACK_DIR]:
    if p not in sys.path:
        sys.path.insert(0, p)

from custom_nodes_custom.tegaki_manga_nodes.scene_compiler import TegakiMangaPageCompiler
from custom_nodes_custom.tegaki_manga_nodes.impact_region_plan import build_impact_region_plan


class TestPhase3J1ImpactCharacterPromptTruth(unittest.TestCase):

    def setUp(self):
        self.cast = {
            "version": 1,
            "characters": [
                {
                    "id": "char_alice",
                    "name": "Alice",
                    "enabled": True,
                    "prompt": "1girl, blonde twin tails, blue eyes, school uniform, pleated skirt",
                    "negative_prompt": "1boy, male, duplicate person, blurry",
                    "loras": [],
                    "metadata": {}
                },
                {
                    "id": "char_bob",
                    "name": "Bob",
                    "enabled": True,
                    "prompt": "1boy, short black hair, dark school uniform, male student",
                    "negative_prompt": "1girl, female, duplicate person, blurry",
                    "loras": [],
                    "metadata": {}
                }
            ]
        }
        self.region_spec = {
            "version": 1,
            "canvas": {"width": 1024, "height": 1024},
            "panel_count": 1,
            "global_prompt": "manga illustration, monochrome linework",
            "global_negative_prompt": "low quality",
            "regions": [
                {
                    "id": 1,
                    "type": "panel",
                    "prompt": "empty school courtyard, clear open foreground, simple architectural background",
                    "negative_prompt": "low quality, text",
                    "panel": {
                        "prompt": "empty school courtyard, clear open foreground, simple architectural background",
                        "negative_prompt": "low quality, text"
                    },
                    "characters": [
                        {
                            "character_id": "char_alice",
                            "enabled": True,
                            "prompt_override": "standing calmly on left",
                            "negative_prompt_override": "",
                            "area": {"x": 0.10, "y": 0.15, "w": 0.35, "h": 0.75}
                        },
                        {
                            "character_id": "char_bob",
                            "enabled": True,
                            "prompt_override": "standing listening on right",
                            "negative_prompt_override": "",
                            "area": {"x": 0.55, "y": 0.15, "w": 0.35, "h": 0.75}
                        }
                    ]
                }
            ]
        }
        self.panel_layout_spec = {
            "version": 1,
            "canvas": {"width": 1024, "height": 1024},
            "vertices": [
                {"id": "v1", "x": 0.05, "y": 0.05},
                {"id": "v2", "x": 0.95, "y": 0.05},
                {"id": "v3", "x": 0.95, "y": 0.95},
                {"id": "v4", "x": 0.05, "y": 0.95}
            ],
            "panels": [
                {
                    "id": "p1",
                    "vertex_ids": ["v1", "v2", "v3", "v4"],
                    "z_index": 0
                }
            ]
        }
        compiler = TegakiMangaPageCompiler()
        self.page_compile_plan, _, _, _ = compiler.compile_page(
            region_spec=self.region_spec,
            cast_spec=json.dumps(self.cast)
        )

    def test_01_standalone_mode_prompt_truth(self):
        """In standalone mode, character prompt must contain character identity and NOT be equal to panel scene prompt."""
        plan = build_impact_region_plan(
            page_compile_plan=self.page_compile_plan,
            panel_layout_spec=self.panel_layout_spec,
            ordering_mode="scene_first",
            character_prompt_mode="standalone",
            include_panel_backgrounds=True,
            remainder_mask_mode=True
        )

        char_regions = [r for r in plan["regions"] if r["scope_type"] == "character_instance"]
        scene_regions = [r for r in plan["regions"] if r["scope_type"] == "panel_scene"]

        self.assertEqual(len(char_regions), 2)
        self.assertEqual(len(scene_regions), 1)

        panel_prompt = scene_regions[0]["prompt"]
        alice_reg = next(r for r in char_regions if r["master_character_id"] == "char_alice")
        bob_reg = next(r for r in char_regions if r["master_character_id"] == "char_bob")

        # 1. Non-empty
        self.assertTrue(bool(alice_reg["prompt"].strip()))
        self.assertTrue(bool(bob_reg["prompt"].strip()))

        # 2. Not identical to panel prompt
        self.assertNotEqual(alice_reg["prompt"], panel_prompt)
        self.assertNotEqual(bob_reg["prompt"], panel_prompt)

        # 3. Contains identity
        self.assertIn("1girl", alice_reg["prompt"])
        self.assertIn("blonde twin tails", alice_reg["prompt"])
        self.assertIn("standing calmly on left", alice_reg["prompt"])

        self.assertIn("1boy", bob_reg["prompt"])
        self.assertIn("short black hair", bob_reg["prompt"])
        self.assertIn("standing listening on right", bob_reg["prompt"])

        # 4. Correct bounds
        self.assertTrue(len(alice_reg["metadata"]["pixel_bounds"]) == 4)
        self.assertTrue(len(bob_reg["metadata"]["pixel_bounds"]) == 4)

    def test_02_remainder_mask_isolation(self):
        """In remainder_mask_mode=True, scene mask must have holes where characters are located."""
        plan_remainder = build_impact_region_plan(
            page_compile_plan=self.page_compile_plan,
            panel_layout_spec=self.panel_layout_spec,
            ordering_mode="scene_first",
            character_prompt_mode="standalone",
            include_panel_backgrounds=True,
            remainder_mask_mode=True
        )
        scene_mask_rem = next(r["mask"] for r in plan_remainder["regions"] if r["scope_type"] == "panel_scene")
        alice_mask_rem = next(r["mask"] for r in plan_remainder["regions"] if r["master_character_id"] == "char_alice")
        bob_mask_rem = next(r["mask"] for r in plan_remainder["regions"] if r["master_character_id"] == "char_bob")

        # In remainder mode, character mask and scene mask should NOT overlap
        overlap_alice = torch.sum(scene_mask_rem * alice_mask_rem).item()
        overlap_bob = torch.sum(scene_mask_rem * bob_mask_rem).item()

        self.assertAlmostEqual(overlap_alice, 0.0, places=2, msg="Scene mask overlapped Alice's mask in remainder mode!")
        self.assertAlmostEqual(overlap_bob, 0.0, places=2, msg="Scene mask overlapped Bob's mask in remainder mode!")

        # Contrast with remainder_mask_mode=False
        plan_full = build_impact_region_plan(
            page_compile_plan=self.page_compile_plan,
            panel_layout_spec=self.panel_layout_spec,
            ordering_mode="scene_first",
            character_prompt_mode="standalone",
            include_panel_backgrounds=True,
            remainder_mask_mode=False
        )
        scene_mask_full = next(r["mask"] for r in plan_full["regions"] if r["scope_type"] == "panel_scene")
        overlap_full_alice = torch.sum(scene_mask_full * alice_mask_rem).item()
        self.assertGreater(overlap_full_alice, 1000.0, "Expected full overlap in non-remainder mode")

    def test_03_scene_composed_mode(self):
        """In scene_composed mode, character prompt includes both scene and character tokens."""
        plan = build_impact_region_plan(
            page_compile_plan=self.page_compile_plan,
            panel_layout_spec=self.panel_layout_spec,
            ordering_mode="scene_first",
            character_prompt_mode="scene_composed",
            include_panel_backgrounds=True,
            remainder_mask_mode=False
        )
        char_regions = [r for r in plan["regions"] if r["scope_type"] == "character_instance"]
        alice_reg = next(r for r in char_regions if r["master_character_id"] == "char_alice")

        # Must have both scene tokens and character tokens
        self.assertIn("empty school courtyard", alice_reg["prompt"])
        self.assertIn("1girl", alice_reg["prompt"])


if __name__ == "__main__":
    unittest.main()
