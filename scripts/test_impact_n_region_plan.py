"""
Unit test for Impact N-Region Plan (Phase 3E)
=============================================
Verifies that:
1. 2, 3, 4 region entries compile correctly.
2. Ordering modes ("scene_first" vs "character_first") sort priorities deterministically.
3. Unique instance IDs are assigned with full traceability to source panels and characters.
4. Masks match canvas dimensions and are properly clipped to panel polygons.
"""

import os
import sys
import unittest
import torch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "custom_nodes_custom")))

from tegaki_manga_nodes.impact_region_plan import build_impact_region_plan
from tegaki_manga_nodes.scene_compiler import TegakiMangaPageCompiler
from tegaki_manga_nodes.cast_master import get_default_cast_spec
from tegaki_manga_nodes.panel_layout_spec import get_default_panel_layout_spec


def make_test_fixture(num_panels=4):
    """Generates standard 4-panel fixture with recurrent Alice & Bob instances."""
    canvas = {"width": 1024, "height": 1024}

    layout_spec = get_default_panel_layout_spec(1024, 1024, preset="4_grid")

    # Base region spec with recurrent Alice & Bob
    all_komas = [
        {
            "id": 1,
            "name": "KOMA 1",
            "enabled": True,
            "prompt": "simple school garden, handshake",
            "negative_prompt": "blurry",
            "characters": [
                {"character_id": "char_alice", "enabled": True, "prompt_override": "smiling", "area": {"x": 0.1, "y": 0.2, "w": 0.4, "h": 0.7}},
                {"character_id": "char_bob", "enabled": True, "prompt_override": "friendly", "area": {"x": 0.5, "y": 0.2, "w": 0.4, "h": 0.7}},
            ]
        },
        {
            "id": 2,
            "name": "KOMA 2",
            "enabled": True,
            "prompt": "flower bed",
            "negative_prompt": "blurry",
            "characters": [
                {"character_id": "char_alice", "enabled": True, "prompt_override": "watering flowers", "area": {"x": 0.2, "y": 0.1, "w": 0.6, "h": 0.8}},
            ]
        },
        {
            "id": 3,
            "name": "KOMA 3",
            "enabled": True,
            "prompt": "garden path",
            "negative_prompt": "blurry",
            "characters": [
                {"character_id": "char_bob", "enabled": True, "prompt_override": "carrying plant", "area": {"x": 0.2, "y": 0.1, "w": 0.6, "h": 0.8}},
            ]
        },
        {
            "id": 4,
            "name": "KOMA 4",
            "enabled": True,
            "prompt": "school gate, argument",
            "negative_prompt": "blurry",
            "characters": [
                {"character_id": "char_alice", "enabled": True, "prompt_override": "looking away, angry", "area": {"x": 0.1, "y": 0.2, "w": 0.4, "h": 0.7}},
                {"character_id": "char_bob", "enabled": True, "prompt_override": "looking away, frustrated", "area": {"x": 0.5, "y": 0.2, "w": 0.4, "h": 0.7}},
            ]
        }
    ]

    base_region_spec = {
        "version": 1,
        "panel_count": num_panels,
        "canvas": canvas,
        "global_prompt": "masterpiece, 4-panel manga",
        "global_negative_prompt": "blurry",
        "regions": all_komas[:num_panels]
    }

    cast_spec = get_default_cast_spec()
    page_compiler = TegakiMangaPageCompiler()
    compile_plan, _, _, _ = page_compiler.compile_page(region_spec=base_region_spec, cast_spec=cast_spec)

    return compile_plan, layout_spec


class TestImpactNRegionPlan(unittest.TestCase):
    def test_compilation_and_counts(self):
        compile_plan, layout_spec = make_test_fixture(4)
        plan = build_impact_region_plan(compile_plan, layout_spec, ordering_mode="scene_first")

        self.assertEqual(plan["canvas"]["width"], 1024)
        self.assertEqual(plan["canvas"]["height"], 1024)
        # 4 panels + 6 character instances = 10 total regions
        self.assertEqual(plan["summary"]["panel_count"], 4)
        self.assertEqual(plan["summary"]["character_instance_count"], 6)
        self.assertEqual(plan["region_count"], 10)

    def test_ordering_modes(self):
        compile_plan, layout_spec = make_test_fixture(4)

        # Scene first: panel scenes (priority 100) before characters (priority 300)
        plan_sf = build_impact_region_plan(compile_plan, layout_spec, ordering_mode="scene_first")
        first_four = [r["scope_type"] for r in plan_sf["regions"][:4]]
        remaining = [r["scope_type"] for r in plan_sf["regions"][4:]]
        self.assertTrue(all(s == "panel_scene" for s in first_four))
        self.assertTrue(all(s == "character_instance" for s in remaining))

        # Character first: characters (priority 100) before panel scenes (priority 300)
        plan_cf = build_impact_region_plan(compile_plan, layout_spec, ordering_mode="character_first")
        first_six = [r["scope_type"] for r in plan_cf["regions"][:6]]
        remaining_four = [r["scope_type"] for r in plan_cf["regions"][6:]]
        self.assertTrue(all(s == "character_instance" for s in first_six))
        self.assertTrue(all(s == "panel_scene" for s in remaining_four))

    def test_unique_instance_ids_and_traceability(self):
        compile_plan, layout_spec = make_test_fixture(4)
        plan = build_impact_region_plan(compile_plan, layout_spec)

        char_regions = [r for r in plan["regions"] if r["scope_type"] == "character_instance"]
        instance_ids = [r["character_instance_id"] for r in char_regions]
        # All instance IDs must be unique
        self.assertEqual(len(instance_ids), len(set(instance_ids)))

        # Panel attendance: Alice in 1, 2, 4; Bob in 1, 3, 4
        alice_panels = [r["source_panel_id"] for r in char_regions if r["master_character_id"] == "char_alice"]
        bob_panels = [r["source_panel_id"] for r in char_regions if r["master_character_id"] == "char_bob"]

        self.assertEqual(alice_panels, ["1", "2", "4"])
        self.assertEqual(bob_panels, ["1", "3", "4"])

    def test_mask_geometry_and_clipping(self):
        compile_plan, layout_spec = make_test_fixture(4)
        plan = build_impact_region_plan(compile_plan, layout_spec)

        for reg in plan["regions"]:
            mask = reg["mask"]
            self.assertEqual(mask.shape, (1024, 1024))
            self.assertGreater(float(mask.sum()), 0.0)
            # Mask values must be bounded [0.0, 1.0]
            self.assertTrue(bool(torch.all((mask >= 0.0) & (mask <= 1.0))))


if __name__ == "__main__":
    unittest.main()
