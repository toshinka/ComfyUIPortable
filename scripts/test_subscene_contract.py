"""
Unit Tests for SubScene v1 Contract & Progressive Authoring (Phase 3F)
======================================================================
Tests:
1. Simple Panel baseline (has_active_subscenes == False).
2. Advanced SubScene parsing & coordinate validation.
3. Multi-SubScene impact_region_plan synthesis:
   - Same master character (Alice) instantiated in both SubScene A and SubScene B.
   - Unique instance IDs generated per subscene.
   - Correct scene_first priority ordering.
4. Fail-closed behavior on duplicate subscene IDs or malformed schemas.
"""

import os
import sys
import unittest
import torch

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CUSTOM_NODES_DIR = os.path.join(ROOT_DIR, "ComfyUI", "custom_nodes")
if CUSTOM_NODES_DIR not in sys.path:
    sys.path.insert(0, CUSTOM_NODES_DIR)
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from tegaki_manga_nodes.subscene_contract import (
    validate_subscene_entry,
    validate_panel_subscenes,
    has_active_subscenes
)
from tegaki_manga_nodes.impact_region_plan import build_impact_region_plan
from tegaki_manga_nodes.panel_content_editor import (
    TegakiMangaPanelContentEditor,
    build_default_panel_content
)


class TestSubSceneContract(unittest.TestCase):
    def setUp(self):
        # 1-panel layout spec fixture
        self.single_panel_layout = {
            "version": 1,
            "canvas": {"width": 1024, "height": 1024},
            "frame": {"x": 0.05, "y": 0.05, "w": 0.9, "h": 0.9},
            "vertices": [
                {"id": "v1", "x": 0.05, "y": 0.05},
                {"id": "v2", "x": 0.95, "y": 0.05},
                {"id": "v3", "x": 0.95, "y": 0.95},
                {"id": "v4", "x": 0.05, "y": 0.95}
            ],
            "panels": [
                {"id": "p1", "vertex_ids": ["v1", "v4", "v3", "v2"]}
            ],
            "metadata": {"preset": "1_panel"}
        }

    def test_simple_panel_default_contract(self):
        """Simple panels without subscenes default cleanly to 1 Root Scene."""
        simple_panel = {
            "id": 1,
            "name": "Panel 1",
            "enabled": True,
            "prompt": "sunny meadow, bright sky",
            "negative_prompt": "blurry",
            "characters": [
                {
                    "character_id": "char_alice",
                    "enabled": True,
                    "prompt_override": "smiling, running",
                    "area": {"x": 0.1, "y": 0.1, "w": 0.4, "h": 0.8}
                }
            ]
        }
        self.assertFalse(has_active_subscenes(simple_panel))
        self.assertEqual(validate_panel_subscenes(simple_panel), [])

    def test_subscene_v1_validation(self):
        """SubScene v1 entry validation and coordinate normalization."""
        raw_sub = {
            "id": "sub_conflict",
            "enabled": True,
            "prompt": "sunset drama, dark shadows",
            "negative_prompt": "bad anatomy",
            "area": {"x": 0.0, "y": 0.0, "w": 0.5, "h": 1.0},
            "character_bindings": [
                {
                    "character_id": "char_alice",
                    "enabled": True,
                    "prompt_override": "angry pout",
                    "area": {"x": 0.1, "y": 0.1, "w": 0.8, "h": 0.8}
                }
            ]
        }
        validated = validate_subscene_entry(raw_sub)
        self.assertEqual(validated["id"], "sub_conflict")
        self.assertTrue(validated["enabled"])
        self.assertEqual(validated["area"]["w"], 0.5)
        self.assertEqual(len(validated["character_bindings"]), 1)
        self.assertEqual(validated["character_bindings"][0]["character_id"], "char_alice")

    def test_subscene_duplicate_id_fail_closed(self):
        """Panels with duplicate subscene IDs fail closed."""
        panel_with_dupes = {
            "id": 1,
            "subscenes": [
                {"id": "sub_a", "prompt": "scene A"},
                {"id": "sub_a", "prompt": "scene A duplicate"}
            ]
        }
        with self.assertRaises(ValueError):
            validate_panel_subscenes(panel_with_dupes)

    def test_progressive_impact_region_plan_with_subscenes(self):
        """
        Synthesizes an IMPACT_REGION_PLAN for a 1-panel comic with 2 SubScenes.
        Verifies Alice is instantiated in both SubScenes with distinct instance IDs.
        """
        multi_sub_compile_plan = {
            "version": 1,
            "canvas": {"width": 1024, "height": 1024},
            "active_panel_ids": [1],
            "global_prompt": "manga masterpiece",
            "global_negative_prompt": "blurry",
            "global_loras": [],
            "panels": [
                {
                    "version": 1,
                    "status": "active",
                    "target_panel_id": 1,
                    "canvas": {"width": 1024, "height": 1024},
                    "panel": {
                        "id": 1,
                        "enabled": True,
                        "geometry": {"x": 0.05, "y": 0.05, "w": 0.9, "h": 0.9},
                        "prompt": "school scene",
                        "negative_prompt": "blurry",
                        "subscenes": [
                            {
                                "id": "sub_left",
                                "enabled": True,
                                "prompt": "sunset school hallway, tense mood",
                                "negative_prompt": "blurry",
                                "area": {"x": 0.0, "y": 0.0, "w": 0.5, "h": 1.0},
                                "character_bindings": [
                                    {
                                        "character_id": "char_alice",
                                        "enabled": True,
                                        "prompt_override": "arguing, crossed arms",
                                        "area": {"x": 0.1, "y": 0.15, "w": 0.8, "h": 0.75}
                                    }
                                ]
                            },
                            {
                                "id": "sub_right",
                                "enabled": True,
                                "prompt": "morning courtyard, peaceful sunbeams",
                                "negative_prompt": "blurry",
                                "area": {"x": 0.5, "y": 0.0, "w": 0.5, "h": 1.0},
                                "character_bindings": [
                                    {
                                        "character_id": "char_alice",
                                        "enabled": True,
                                        "prompt_override": "cheerful smile, holding flowers",
                                        "area": {"x": 0.1, "y": 0.15, "w": 0.8, "h": 0.75}
                                    }
                                ]
                            }
                        ]
                    },
                    "global_prompt": "manga masterpiece",
                    "global_negative_prompt": "blurry",
                    "compiled_prompt": "manga masterpiece, school scene",
                    "compiled_negative_prompt": "blurry",
                    "characters": [],
                    "lora_plan": {"global_loras": [], "koma_loras": [], "character_loras": []}
                }
            ]
        }

        plan = build_impact_region_plan(
            page_compile_plan=multi_sub_compile_plan,
            panel_layout_spec=self.single_panel_layout,
            ordering_mode="scene_first"
        )

        regions = plan["regions"]
        # Expected: 2 subscene background regions + 2 character instance regions = 4 total regions
        self.assertEqual(len(regions), 4)

        subscene_regions = [r for r in regions if r["scope_type"] == "subscene"]
        char_regions = [r for r in regions if r["scope_type"] == "character_instance"]

        self.assertEqual(len(subscene_regions), 2)
        self.assertEqual(len(char_regions), 2)

        # In scene_first mode, subscene backgrounds come first
        self.assertLess(subscene_regions[0]["priority"], char_regions[0]["priority"])

        # Character instance IDs must be distinct and reference subscenes
        instance_ids = [c["character_instance_id"] for c in char_regions]
        self.assertEqual(len(set(instance_ids)), 2)
        self.assertTrue(any("sub_left" in iid for iid in instance_ids))
        self.assertTrue(any("sub_right" in iid for iid in instance_ids))

        # Check masks are valid tensors
        for r in regions:
            self.assertIsInstance(r["mask"], torch.Tensor)
            self.assertEqual(r["mask"].shape, (1024, 1024))


if __name__ == "__main__":
    unittest.main()
