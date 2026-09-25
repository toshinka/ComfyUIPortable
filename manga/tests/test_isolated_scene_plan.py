"""Unit tests for isolated_scene_plan.py (Card MANGA-ISOLATED-SCENE-PLAN1).

Covers cases A through L specified in the Card contract:
A. Select a non-first Scene; no unrelated Scene enters the resulting plan.
B. A non-origin Scene rectangle correctly transforms a contained Character Instance to local coordinates.
C. Relevant CAST identity, acting text, and Reference assignment are preserved.
D. An unrelated Scene's Instance and CAST are excluded.
E. Input snapshot is unchanged (immutability).
F. Missing or duplicate Scene ID fails explicitly.
G. Out-of-Scene Instance fails without silent clipping.
H. More than two selected-Scene Instances fails.
I. More than one distinct active Reference fails.
J. An effective active full-page Guide fails with ISOLATED_SCENE_GUIDE_UNSUPPORTED.
K. No active Guide (or disabled/inactive) allows normal plan construction.
L. Invalid local canvas dimensions fail explicitly.
"""

from __future__ import annotations

import copy
import math
import os
import sys
import unittest
from pathlib import Path

# Ensure repo root and custom_nodes_custom are on sys.path
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
CUSTOM_NODES_DIR = REPO_ROOT / "custom_nodes_custom"
if str(CUSTOM_NODES_DIR) not in sys.path:
    sys.path.insert(0, str(CUSTOM_NODES_DIR))

import importlib.util

MODULE_PATH = REPO_ROOT / "custom_nodes_custom" / "tegaki_manga_nodes" / "isolated_scene_plan.py"
spec = importlib.util.spec_from_file_location("isolated_scene_plan", str(MODULE_PATH))
if spec is None or spec.loader is None:
    raise ImportError(f"Cannot load module from {MODULE_PATH}")
isolated_scene_plan = importlib.util.module_from_spec(spec)
sys.modules["isolated_scene_plan"] = isolated_scene_plan
spec.loader.exec_module(isolated_scene_plan)

create_isolated_scene_plan = isolated_scene_plan.create_isolated_scene_plan
IsolatedScenePlanError = isolated_scene_plan.IsolatedScenePlanError
DIMENSION_BOUNDS = isolated_scene_plan.DIMENSION_BOUNDS


def make_sample_document() -> dict:
    """Fixture producing a multi-scene, multi-cast document snapshot."""
    return {
        "schema_id": "TEGAKI_AUTHORING_DOCUMENT",
        "schema_version": "1.0.0",
        "document_id": "doc_test_123",
        "pages": [
            {
                "page_id": "page_1",
                "width_px": 1024,
                "height_px": 1536,
                "style_prompt": "masterpiece, manga style, clean lines",
                "style_negative_prompt": "blurry, low quality",
                "scenes": [
                    {
                        "scene_id": "scene_1",
                        "order": 1,
                        "name": "Panel 1",
                        "input_mode": "simple",
                        "prompt": "cat on the roof",
                        "negative_prompt": "human",
                        "area": {"shape_type": "rect", "x": 0.05, "y": 0.05, "w": 0.90, "h": 0.40},
                    },
                    {
                        "scene_id": "scene_2",
                        "order": 2,
                        "name": "Panel 2",
                        "input_mode": "cast",
                        "prompt": "girl standing in the room",
                        "negative_prompt": "outdoor",
                        "area": {"shape_type": "rect", "x": 0.05, "y": 0.50, "w": 0.40, "h": 0.45},
                    },
                    {
                        "scene_id": "scene_3",
                        "order": 3,
                        "name": "Panel 3",
                        "input_mode": "cast",
                        "prompt": "vintage car parked",
                        "negative_prompt": "",
                        "area": {"shape_type": "rect", "x": 0.55, "y": 0.50, "w": 0.40, "h": 0.45},
                    },
                ],
                "cast": [
                    {
                        "cast_id": "cast_heroine",
                        "display_name": "Heroine",
                        "identity_prompt": "1girl, brown hair, school uniform",
                        "negative_prompt": "boy, man",
                        "color": "#ff6699",
                        "reference_asset": "heroine_ref_01.png",
                    },
                    {
                        "cast_id": "cast_rival",
                        "display_name": "Rival",
                        "identity_prompt": "1girl, blonde twin-tails",
                        "negative_prompt": "",
                        "color": "#3399ff",
                        "reference_asset": "rival_ref_02.png",
                    },
                ],
                "character_instances": [
                    {
                        "instance_id": "inst_scene_2_heroine",
                        "cast_id": "cast_heroine",
                        "scene_id": "scene_2",
                        "acting_prompt": "looking shocked, hand over mouth",
                        "area": {"shape_type": "rect", "x": 0.10, "y": 0.55, "w": 0.20, "h": 0.30},
                    },
                    {
                        "instance_id": "inst_scene_3_rival",
                        "cast_id": "cast_rival",
                        "scene_id": "scene_3",
                        "acting_prompt": "leaning on the car hood",
                        "area": {"shape_type": "rect", "x": 0.60, "y": 0.60, "w": 0.25, "h": 0.25},
                    },
                ],
                "guides": [],
            }
        ],
    }


class TestIsolatedScenePlan(unittest.TestCase):
    """Test suite covering cases A through L of MANGA-ISOLATED-SCENE-PLAN1."""

    def test_case_a_select_non_first_scene_excludes_unrelated_scenes(self):
        """A. Select a non-first Scene; no unrelated Scene enters the resulting plan."""
        doc = make_sample_document()
        plan = create_isolated_scene_plan(doc, scene_id="scene_2", local_dimensions=(512, 768))

        self.assertEqual(plan["owner"]["scene_id"], "scene_2")
        self.assertEqual(plan["owner"]["document_id"], "doc_test_123")
        self.assertEqual(plan["owner"]["page_id"], "page_1")
        self.assertEqual(plan["scene"]["scene_id"], "scene_2")
        self.assertEqual(plan["scene"]["prompt"], "girl standing in the room")

        # Must not contain any traces of scene_1 or scene_3
        self.assertNotIn("scene_1", repr(plan["scene"]))
        self.assertNotIn("scene_3", repr(plan["scene"]))
        self.assertEqual(len(plan["character_instances"]), 1)
        self.assertEqual(plan["character_instances"][0]["scene_id"], "scene_2")

    def test_case_b_coordinate_transformation(self):
        """B. A non-origin Scene rectangle correctly transforms a contained Character Instance to local coordinates."""
        doc = make_sample_document()
        # Scene 2 is at x=0.05, y=0.50, w=0.40, h=0.45
        # Instance is at x=0.10, y=0.55, w=0.20, h=0.30
        plan = create_isolated_scene_plan(doc, scene_id="scene_2", local_dimensions=(512, 768))

        inst = plan["character_instances"][0]
        local_area = inst["area"]
        self.assertEqual(local_area["shape_type"], "rect")

        # u = (0.10 - 0.05) / 0.40 = 0.05 / 0.40 = 0.125
        # v = (0.55 - 0.50) / 0.45 = 0.05 / 0.45 = 1/9 = 0.111111...
        # local_w = 0.20 / 0.40 = 0.5
        # local_h = 0.30 / 0.45 = 2/3 = 0.666666...
        self.assertAlmostEqual(local_area["x"], 0.125, places=5)
        self.assertAlmostEqual(local_area["y"], 1.0 / 9.0, places=5)
        self.assertAlmostEqual(local_area["w"], 0.5, places=5)
        self.assertAlmostEqual(local_area["h"], 2.0 / 3.0, places=5)

        # Scene-local rectangle covers complete local canvas: 0, 0, 1, 1
        self.assertEqual(plan["scene"]["local_area"], {"shape_type": "rect", "x": 0.0, "y": 0.0, "w": 1.0, "h": 1.0})
        # Original area preserved
        self.assertEqual(plan["scene"]["original_page_area"], {"shape_type": "rect", "x": 0.05, "y": 0.50, "w": 0.40, "h": 0.45})
        # Placement mapping
        self.assertEqual(plan["placement_mapping"]["transform"]["scale_x"], 0.40)
        self.assertEqual(plan["placement_mapping"]["transform"]["scale_y"], 0.45)
        self.assertEqual(plan["placement_mapping"]["transform"]["offset_x"], 0.05)
        self.assertEqual(plan["placement_mapping"]["transform"]["offset_y"], 0.50)

    def test_case_c_preserves_cast_identity_acting_reference(self):
        """C. Relevant CAST identity, acting text, and Reference assignment are preserved."""
        doc = make_sample_document()
        plan = create_isolated_scene_plan(doc, scene_id="scene_2", local_dimensions=(512, 768))

        self.assertEqual(len(plan["cast"]), 1)
        heroine_cast = plan["cast"][0]
        self.assertEqual(heroine_cast["cast_id"], "cast_heroine")
        self.assertEqual(heroine_cast["identity_prompt"], "1girl, brown hair, school uniform")
        self.assertEqual(heroine_cast["reference_asset"], "heroine_ref_01.png")

        inst = plan["character_instances"][0]
        self.assertEqual(inst["instance_id"], "inst_scene_2_heroine")
        self.assertEqual(inst["cast_id"], "cast_heroine")
        self.assertEqual(inst["acting_prompt"], "looking shocked, hand over mouth")

        self.assertTrue(plan["reference"]["enabled"])
        self.assertEqual(plan["reference"]["reference_asset"], "heroine_ref_01.png")

    def test_case_d_excludes_unrelated_instances_and_cast(self):
        """D. An unrelated Scene's Instance and CAST are excluded."""
        doc = make_sample_document()
        plan = create_isolated_scene_plan(doc, scene_id="scene_2", local_dimensions=(512, 768))

        instance_ids = [inst["instance_id"] for inst in plan["character_instances"]]
        self.assertNotIn("inst_scene_3_rival", instance_ids)

        cast_ids = [c["cast_id"] for c in plan["cast"]]
        self.assertNotIn("cast_rival", cast_ids)

    def test_case_e_snapshot_immutability(self):
        """E. Input snapshot is unchanged."""
        doc = make_sample_document()
        snapshot_copy = copy.deepcopy(doc)

        plan = create_isolated_scene_plan(doc, scene_id="scene_2", local_dimensions=(512, 768))
        self.assertIsNotNone(plan)
        self.assertEqual(doc, snapshot_copy, "Input snapshot must not be mutated in any way")

    def test_case_f_missing_or_duplicate_scene_id(self):
        """F. Missing or duplicate Scene ID fails explicitly."""
        doc = make_sample_document()

        # Missing scene ID
        with self.assertRaises(IsolatedScenePlanError) as ctx:
            create_isolated_scene_plan(doc, scene_id="scene_nonexistent", local_dimensions=(512, 768))
        self.assertEqual(ctx.exception.code, "SCENE_NOT_FOUND")

        # Duplicate scene ID on the same page
        dup_doc = copy.deepcopy(doc)
        dup_scene = copy.deepcopy(dup_doc["pages"][0]["scenes"][1])
        dup_doc["pages"][0]["scenes"].append(dup_scene)

        with self.assertRaises(IsolatedScenePlanError) as ctx:
            create_isolated_scene_plan(dup_doc, scene_id="scene_2", local_dimensions=(512, 768))
        self.assertEqual(ctx.exception.code, "AMBIGUOUS_SCENE_ID")

    def test_case_g_out_of_scene_instance_fails_closed(self):
        """G. Out-of-Scene Instance fails without silent clipping."""
        doc = make_sample_document()
        # Scene 2 is [0.05, 0.50, 0.40, 0.45] -> max_x is 0.45
        # Set instance area x to 0.40, w to 0.10 -> extends to 0.50 (> 0.45)
        bad_doc = copy.deepcopy(doc)
        bad_doc["pages"][0]["character_instances"][0]["area"] = {
            "shape_type": "rect",
            "x": 0.40,
            "y": 0.55,
            "w": 0.10,
            "h": 0.30,
        }

        with self.assertRaises(IsolatedScenePlanError) as ctx:
            create_isolated_scene_plan(bad_doc, scene_id="scene_2", local_dimensions=(512, 768))
        self.assertEqual(ctx.exception.code, "CHARACTER_INSTANCE_OUT_OF_BOUNDS")

    def test_case_h_max_instances_exceeded(self):
        """H. More than two selected-Scene Instances fails."""
        doc = make_sample_document()
        inst1 = copy.deepcopy(doc["pages"][0]["character_instances"][0])
        inst2 = copy.deepcopy(inst1)
        inst2["instance_id"] = "inst_2"
        inst3 = copy.deepcopy(inst1)
        inst3["instance_id"] = "inst_3"

        doc["pages"][0]["character_instances"] = [inst1, inst2, inst3]

        with self.assertRaises(IsolatedScenePlanError) as ctx:
            create_isolated_scene_plan(doc, scene_id="scene_2", local_dimensions=(512, 768))
        self.assertEqual(ctx.exception.code, "MAX_INSTANCES_EXCEEDED")

    def test_case_i_max_distinct_references_exceeded(self):
        """I. More than one distinct active Reference fails."""
        doc = make_sample_document()
        # Add a second instance in scene_2 that references cast_rival with a different reference asset
        second_inst = {
            "instance_id": "inst_scene_2_rival",
            "cast_id": "cast_rival",
            "scene_id": "scene_2",
            "acting_prompt": "watching",
            "area": {"shape_type": "rect", "x": 0.25, "y": 0.55, "w": 0.15, "h": 0.25},
        }
        doc["pages"][0]["character_instances"] = [
            doc["pages"][0]["character_instances"][0],
            second_inst,
        ]

        with self.assertRaises(IsolatedScenePlanError) as ctx:
            create_isolated_scene_plan(doc, scene_id="scene_2", local_dimensions=(512, 768))
        self.assertEqual(ctx.exception.code, "MAX_REFERENCES_EXCEEDED")

    def test_case_j_active_structural_guide_rejected(self):
        """J. An effective active full-page Guide fails with ISOLATED_SCENE_GUIDE_UNSUPPORTED."""
        doc = make_sample_document()
        doc["pages"][0]["guides"] = [
            {
                "guide_id": "guide_rough_1",
                "guide_type": "rough_manga",
                "enabled": True,
                "asset_reference": "rough_layout_page1.png",
            }
        ]

        with self.assertRaises(IsolatedScenePlanError) as ctx:
            create_isolated_scene_plan(doc, scene_id="scene_2", local_dimensions=(512, 768))
        self.assertEqual(ctx.exception.code, "ISOLATED_SCENE_GUIDE_UNSUPPORTED")

    def test_case_k_disabled_or_absent_guide_succeeds(self):
        """K. No active Guide allows normal plan construction."""
        doc = make_sample_document()

        # Case K1: guides list is empty
        doc["pages"][0]["guides"] = []
        plan1 = create_isolated_scene_plan(doc, scene_id="scene_2", local_dimensions=(512, 768))
        self.assertIsNotNone(plan1)

        # Case K2: guide exists but enabled is False
        doc["pages"][0]["guides"] = [
            {
                "guide_id": "guide_disabled",
                "guide_type": "rough_manga",
                "enabled": False,
                "asset_reference": "rough_layout_page1.png",
            }
        ]
        plan2 = create_isolated_scene_plan(doc, scene_id="scene_2", local_dimensions=(512, 768))
        self.assertIsNotNone(plan2)

        # Case K3: guide exists and enabled is True, but no asset_reference
        doc["pages"][0]["guides"] = [
            {
                "guide_id": "guide_no_asset",
                "guide_type": "rough_manga",
                "enabled": True,
                "asset_reference": "",
            }
        ]
        plan3 = create_isolated_scene_plan(doc, scene_id="scene_2", local_dimensions=(512, 768))
        self.assertIsNotNone(plan3)

    def test_case_l_invalid_local_dimensions_fail(self):
        """L. Invalid local canvas dimensions fail explicitly."""
        doc = make_sample_document()

        # Not divisible by 8
        with self.assertRaises(IsolatedScenePlanError) as ctx:
            create_isolated_scene_plan(doc, scene_id="scene_2", local_dimensions=(515, 768))
        self.assertEqual(ctx.exception.code, "INVALID_LOCAL_DIMENSIONS")

        # Float dimensions
        with self.assertRaises(IsolatedScenePlanError) as ctx:
            create_isolated_scene_plan(doc, scene_id="scene_2", local_dimensions=(512.0, 768))  # type: ignore
        self.assertEqual(ctx.exception.code, "INVALID_LOCAL_DIMENSIONS")

        # Below min (256)
        with self.assertRaises(IsolatedScenePlanError) as ctx:
            create_isolated_scene_plan(doc, scene_id="scene_2", local_dimensions=(128, 512))
        self.assertEqual(ctx.exception.code, "INVALID_LOCAL_DIMENSIONS")

        # Above max (2048)
        with self.assertRaises(IsolatedScenePlanError) as ctx:
            create_isolated_scene_plan(doc, scene_id="scene_2", local_dimensions=(4096, 512))
        self.assertEqual(ctx.exception.code, "INVALID_LOCAL_DIMENSIONS")

        # Missing dimensions entirely: canonical derivation applies (B6), but it
        # still fails closed when the Page has no pixel dimensions to derive from.
        no_page_px = copy.deepcopy(doc)
        del no_page_px["pages"][0]["width_px"]
        with self.assertRaises(IsolatedScenePlanError) as ctx:
            create_isolated_scene_plan(no_page_px, scene_id="scene_2")
        self.assertEqual(ctx.exception.code, "INVALID_LOCAL_DIMENSIONS")

    def test_broken_cast_reference_fails(self):
        """Verify broken cast reference raises CAST_NOT_FOUND."""
        doc = make_sample_document()
        doc["pages"][0]["character_instances"][0]["cast_id"] = "unknown_cast_id"
        with self.assertRaises(IsolatedScenePlanError) as ctx:
            create_isolated_scene_plan(doc, scene_id="scene_2", local_dimensions=(512, 768))
        self.assertEqual(ctx.exception.code, "CAST_NOT_FOUND")

    def test_invalid_scene_geometry_fails(self):
        """Verify negative or zero width scene geometry raises INVALID_SCENE_GEOMETRY."""
        doc = make_sample_document()
        doc["pages"][0]["scenes"][1]["area"]["w"] = 0.0
        with self.assertRaises(IsolatedScenePlanError) as ctx:
            create_isolated_scene_plan(doc, scene_id="scene_2", local_dimensions=(512, 768))
        self.assertEqual(ctx.exception.code, "INVALID_SCENE_GEOMETRY")

    def test_guide_state_emitted_when_no_active_guide(self):
        """A. No active structural Guide produces explicit guide_state with enabled=False and active=False."""
        doc = make_sample_document()
        plan = create_isolated_scene_plan(doc, scene_id="scene_2", local_dimensions=(512, 768))
        self.assertIn("guide_state", plan)
        self.assertEqual(plan["guide_state"], {"enabled": False, "active": False})

    def test_active_guide_still_raises_unsupported(self):
        """B. An active structural Guide continues to fail with ISOLATED_SCENE_GUIDE_UNSUPPORTED."""
        doc = make_sample_document()
        doc["pages"][0]["guides"] = [
            {
                "guide_id": "guide_active",
                "guide_type": "rough_manga",
                "enabled": True,
                "asset_reference": "rough_page1.png",
            }
        ]
        with self.assertRaises(IsolatedScenePlanError) as ctx:
            create_isolated_scene_plan(doc, scene_id="scene_2", local_dimensions=(512, 768))
        self.assertEqual(ctx.exception.code, "ISOLATED_SCENE_GUIDE_UNSUPPORTED")

    def test_guide_state_immutability(self):
        """C. Source Authoring snapshot remains unchanged."""
        doc = make_sample_document()
        snapshot = copy.deepcopy(doc)
        plan = create_isolated_scene_plan(doc, scene_id="scene_2", local_dimensions=(512, 768))
        self.assertIsNotNone(plan)
        self.assertEqual(doc, snapshot)
        self.assertNotIn("guide_state", doc["pages"][0])


class TestCanonicalLocalCanvasDerivation(unittest.TestCase):
    """B6: one authoritative aspect-preserving local canvas rule."""

    def _doc_with_scene(self, page_w, page_h, rect):
        doc = make_sample_document()
        page = doc["pages"][0]
        page["width_px"], page["height_px"] = page_w, page_h
        page["character_instances"] = []
        page["scenes"] = [{
            "scene_id": "s_geo", "order": 1, "name": "geo", "input_mode": "simple",
            "prompt": "x", "negative_prompt": "",
            "area": {"shape_type": "rect", **rect},
        }]
        return doc

    def _assert_allowed(self, w, h):
        self.assertEqual(w % isolated_scene_plan.LOCAL_CANVAS_GRID, 0)
        self.assertEqual(h % isolated_scene_plan.LOCAL_CANVAS_GRID, 0)
        self.assertTrue(DIMENSION_BOUNDS["width"]["min"] <= w <= DIMENSION_BOUNDS["width"]["max"])
        self.assertTrue(DIMENSION_BOUNDS["height"]["min"] <= h <= DIMENSION_BOUNDS["height"]["max"])
        self.assertLessEqual(w * h, isolated_scene_plan.LOCAL_CANVAS_TARGET_PIXELS)
        self.assertLessEqual(w * h, DIMENSION_BOUNDS["max_pixels"])

    def _derive(self, page_w, page_h, rect):
        plan = create_isolated_scene_plan(self._doc_with_scene(page_w, page_h, rect), scene_id="s_geo")
        w, h = plan["local_canvas"]["width"], plan["local_canvas"]["height"]
        self._assert_allowed(w, h)
        scene_aspect = (rect["w"] * page_w) / (rect["h"] * page_h)
        return w, h, scene_aspect

    def test_portrait_scene_gets_portrait_canvas(self):
        w, h, a = self._derive(1024, 1536, {"x": 0.05, "y": 0.05, "w": 0.45, "h": 0.9})  # ~0.33
        self.assertLess(w, h)
        self.assertLess(abs(math.log((w / h) / a)), math.log(1.05))
        self.assertGreaterEqual(w * h, 0.8 * isolated_scene_plan.LOCAL_CANVAS_TARGET_PIXELS)

    def test_landscape_scene_gets_landscape_canvas(self):
        w, h, a = self._derive(1024, 1536, {"x": 0.05, "y": 0.05, "w": 0.9, "h": 0.3})  # 2.0
        self.assertGreater(w, h)
        self.assertLess(abs(math.log((w / h) / a)), math.log(1.05))
        self.assertEqual((w, h), (1408, 704))

    def test_square_scene_stays_square(self):
        w, h, a = self._derive(1024, 1536, {"x": 0.1, "y": 0.1, "w": 0.6, "h": 0.4})  # 1.0 in pixels
        self.assertAlmostEqual(a, 1.0, places=6)
        self.assertEqual((w, h), (1024, 1024))

    def test_normalized_rect_uses_page_pixel_aspect(self):
        # Normalized 0.5 x 0.5 on a 1024x1536 page is 512x768 px (2:3 portrait), not square.
        w, h, a = self._derive(1024, 1536, {"x": 0.0, "y": 0.0, "w": 0.5, "h": 0.5})
        self.assertEqual((w, h), (768, 1152))

    def test_extreme_strip_respects_bounds(self):
        w, h, _ = self._derive(1024, 1536, {"x": 0.0, "y": 0.0, "w": 1.0, "h": 0.05})
        self.assertEqual((w, h), (2048, 256))

    def test_deterministic_and_explicit_override_still_honored(self):
        rect = {"x": 0.05, "y": 0.05, "w": 0.45, "h": 0.9}
        doc = self._doc_with_scene(1024, 1536, rect)
        self.assertEqual(
            create_isolated_scene_plan(doc, scene_id="s_geo")["local_canvas"],
            create_isolated_scene_plan(copy.deepcopy(doc), scene_id="s_geo")["local_canvas"],
        )
        plan = create_isolated_scene_plan(doc, scene_id="s_geo", local_dimensions=(512, 768))
        self.assertEqual(plan["local_canvas"], {"width": 512, "height": 768})


if __name__ == "__main__":
    unittest.main()

