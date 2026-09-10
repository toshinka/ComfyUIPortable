#!/usr/bin/env python3
"""
test_m3b_pi1_generation_guide_bridge.py — M3B-PI1 Generation Guide Bridge Unit & Contract Tests.

Verifies the 12 required test cases from Section 29 of M3B-PI1:
1. no Guide -> NO_GENERATION_GUIDE
2. disabled Guide -> NO_GENERATION_GUIDE
3. enabled Guide / zero Figures -> NO_GENERATION_GUIDE
4. one Figure -> deterministic CLEAN image
5. two Figures -> deterministic CLEAN image
6. unassigned Figure -> legal
7. same CAST multiple appearances -> legal
8. Guide-local -> Page geometry projection correct
9. invalid document -> fail closed
10. invalid Figure geometry -> fail closed
11. RAW asset pixel changes do not change CLEAN output
12. LR3 qualified fixture pixel/hash parity
"""

import copy
import hashlib
import io
import json
import os
import sys
import unittest
from pathlib import Path
from typing import Any, Dict

import numpy as np
from PIL import Image

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "ComfyUI"))

from custom_nodes_custom.tegaki_manga_nodes import authoring_contract as contract
from custom_nodes_custom.tegaki_manga_nodes.generation_guide_bridge import (
    TegakiMangaGenerationGuideBridge,
    build_generation_guide_plan,
    _derive_page_area,
    _pixel_bounds,
)

LR3_CLEAN_SHA256 = "96f99a6c1327925b4b7737c9658ffb3e2b69e76ea2b0fe40210a095b9d99ae3a"
LR3_WORKFLOW_PATH = REPO_ROOT / "workflows" / "manga" / "research" / "M3B_LR2R1_ANYTEST_AB.json"
LR3_FIXTURE_PATH = REPO_ROOT / "docs" / "manga" / "verification" / "m3b_lr3" / "M3B_LR3_CLEAN_GUIDE.png"


def _make_base_doc(width=832, height=1216):
    page = contract.create_page(width, height, page_id="page_1")
    page["scenes"] = [contract.create_scene("Scene 1", scene_id="scene_1")]
    page["cast"] = [contract.create_cast_entry("Hero", cast_id="cast_1")]
    page["character_instances"] = [
        contract.create_character_instance("cast_1", "scene_1", instance_id="inst_1")
    ]
    return contract.create_document(pages=[page])


def _make_guide(
    guide_id="guide_1",
    enabled=True,
    asset_reference="guide.png",
    placement=None,
    figure_regions=None,
):
    if placement is None:
        placement = contract.make_area(0.0, 0.0, 1.0, 1.0)
    if figure_regions is None:
        figure_regions = []
    return {
        "guide_id": guide_id,
        "guide_type": "rough_manga",
        "asset_reference": asset_reference,
        "placement": placement,
        "enabled": enabled,
        "figure_regions": figure_regions,
    }


class TestM3BPI1GenerationGuideBridge(unittest.TestCase):
    """12 contract test cases for TegakiMangaGenerationGuideBridge."""

    def test_case_01_no_guide(self):
        """1. no Guide -> NO_GENERATION_GUIDE."""
        doc = _make_base_doc()
        doc["pages"][0]["guides"] = []
        plan = build_generation_guide_plan(doc)
        self.assertEqual(plan["status"], "NO_GENERATION_GUIDE")
        self.assertEqual(plan["debug"]["status"], "NO_GENERATION_GUIDE")
        self.assertEqual(plan["debug"]["figure_count"], 0)
        self.assertEqual(plan["debug"]["generation_influence"], "NO_GUIDE")

        # Verify image is pure white
        arr = np.asarray(plan["canvas_image"].convert("RGB"))
        self.assertTrue(np.all(arr == 255), "NO_GENERATION_GUIDE canvas must be pure white")

        # Also test ComfyUI node entry point with empty text
        bridge_node = TegakiMangaGenerationGuideBridge()
        img_tensor, dbg_str = bridge_node.bridge("", 0)
        dbg = json.loads(dbg_str)
        self.assertEqual(dbg["status"], "NO_GENERATION_GUIDE")

    def test_case_02_disabled_guide(self):
        """2. disabled Guide -> NO_GENERATION_GUIDE."""
        doc = _make_base_doc()
        fig = {
            "figure_id": "fig_1",
            "area": contract.make_area(0.1, 0.1, 0.3, 0.5),
            "instance_id": "inst_1",
        }
        doc["pages"][0]["guides"] = [_make_guide(enabled=False, figure_regions=[fig])]
        plan = build_generation_guide_plan(doc)
        self.assertEqual(plan["status"], "NO_GENERATION_GUIDE")
        arr = np.asarray(plan["canvas_image"].convert("RGB"))
        self.assertTrue(np.all(arr == 255))

    def test_case_03_enabled_guide_zero_figures(self):
        """3. enabled Guide / zero Figures -> NO_GENERATION_GUIDE."""
        doc = _make_base_doc()
        doc["pages"][0]["guides"] = [_make_guide(enabled=True, figure_regions=[])]
        plan = build_generation_guide_plan(doc)
        self.assertEqual(plan["status"], "NO_GENERATION_GUIDE")
        arr = np.asarray(plan["canvas_image"].convert("RGB"))
        self.assertTrue(np.all(arr == 255))

    def test_case_04_one_figure(self):
        """4. one Figure -> deterministic CLEAN image."""
        doc = _make_base_doc()
        fig = {
            "figure_id": "fig_1",
            "area": contract.make_area(0.2, 0.2, 0.3, 0.6),
            "instance_id": "inst_1",
        }
        doc["pages"][0]["guides"] = [_make_guide(enabled=True, figure_regions=[fig])]
        plan1 = build_generation_guide_plan(doc)
        plan2 = build_generation_guide_plan(doc)

        self.assertEqual(plan1["status"], "PASS")
        self.assertEqual(plan1["debug"]["figure_count"], 1)

        arr1 = np.asarray(plan1["canvas_image"].convert("RGB"))
        arr2 = np.asarray(plan2["canvas_image"].convert("RGB"))
        self.assertTrue(np.array_equal(arr1, arr2), "Rendering must be deterministic")

        # Must contain both black silhouette pixels and white background pixels
        colors = set(tuple(c) for c in arr1.reshape(-1, 3))
        self.assertTrue((0, 0, 0) in colors, "Clean guide must contain black silhouette pixels")
        self.assertTrue((255, 255, 255) in colors, "Clean guide must contain white background pixels")

    def test_case_05_two_figures(self):
        """5. two Figures -> deterministic CLEAN image."""
        doc = _make_base_doc()
        fig1 = {
            "figure_id": "fig_1",
            "area": contract.make_area(0.1, 0.2, 0.3, 0.5),
            "instance_id": "inst_1",
        }
        fig2 = {
            "figure_id": "fig_2",
            "area": contract.make_area(0.6, 0.2, 0.3, 0.5),
            "instance_id": None,
        }
        doc["pages"][0]["guides"] = [_make_guide(enabled=True, figure_regions=[fig1, fig2])]
        plan = build_generation_guide_plan(doc)
        self.assertEqual(plan["status"], "PASS")
        self.assertEqual(plan["debug"]["figure_count"], 2)

        # Both figures rendered into canvas
        arr = np.asarray(plan["canvas_image"].convert("RGB"))
        self.assertTrue((0, 0, 0) in set(tuple(c) for c in arr.reshape(-1, 3)))

    def test_case_06_unassigned_figure_legal(self):
        """6. unassigned Figure -> legal."""
        doc = _make_base_doc()
        fig = {
            "figure_id": "fig_unassigned",
            "area": contract.make_area(0.2, 0.2, 0.3, 0.5),
            "instance_id": None,  # No CAST association
        }
        doc["pages"][0]["guides"] = [_make_guide(enabled=True, figure_regions=[fig])]
        plan = build_generation_guide_plan(doc)
        self.assertEqual(plan["status"], "PASS")
        self.assertEqual(plan["debug"]["figures"][0]["instance_id"], None)

    def test_case_07_same_cast_multiple_appearances(self):
        """7. same CAST multiple appearances -> legal."""
        doc = _make_base_doc()
        # Add a second instance for cast_1
        doc["pages"][0]["character_instances"].append(
            contract.create_character_instance("cast_1", "scene_1", instance_id="inst_2")
        )
        fig1 = {
            "figure_id": "fig_1",
            "area": contract.make_area(0.1, 0.2, 0.3, 0.5),
            "instance_id": "inst_1",
        }
        fig2 = {
            "figure_id": "fig_2",
            "area": contract.make_area(0.55, 0.2, 0.3, 0.5),
            "instance_id": "inst_2",
        }
        doc["pages"][0]["guides"] = [_make_guide(enabled=True, figure_regions=[fig1, fig2])]
        plan = build_generation_guide_plan(doc)
        self.assertEqual(plan["status"], "PASS")
        self.assertEqual(plan["debug"]["figure_count"], 2)

    def test_case_08_guide_local_to_page_projection(self):
        """8. Guide-local -> Page geometry projection correct."""
        placement = contract.make_area(0.1, 0.2, 0.5, 0.6)
        local_area = contract.make_area(0.2, 0.3, 0.4, 0.5)
        derived = _derive_page_area(placement, local_area, "test_ctx")

        expected_x = round(0.1 + 0.2 * 0.5, 6)  # 0.20
        expected_y = round(0.2 + 0.3 * 0.6, 6)  # 0.38
        expected_w = round(0.4 * 0.5, 6)        # 0.20
        expected_h = round(0.5 * 0.6, 6)        # 0.30

        self.assertAlmostEqual(derived[0], expected_x, places=5)
        self.assertAlmostEqual(derived[1], expected_y, places=5)
        self.assertAlmostEqual(derived[2], expected_w, places=5)
        self.assertAlmostEqual(derived[3], expected_h, places=5)

        width, height = 1000, 2000
        pb = _pixel_bounds(derived, width, height)
        self.assertEqual(pb, (200, 760, 400, 1360))

    def test_case_09_invalid_document_fail_closed(self):
        """9. invalid document -> fail closed."""
        # Non-dict
        with self.assertRaises(ValueError):
            build_generation_guide_plan("not a dict")  # type: ignore

        # Invalid schema
        with self.assertRaises(ValueError):
            build_generation_guide_plan({"schema_id": "UNKNOWN_SCHEMA"})

        # Out-of-bounds page_index
        doc = _make_base_doc()
        with self.assertRaises(ValueError):
            build_generation_guide_plan(doc, page_index=99)

    def test_case_10_invalid_figure_geometry_fail_closed(self):
        """10. invalid Figure geometry -> fail closed."""
        doc = _make_base_doc()
        # Invalid figure area: negative width
        bad_fig = {
            "figure_id": "bad_fig",
            "area": {"x": 0.1, "y": 0.1, "w": -0.5, "h": 0.5},
            "instance_id": None,
        }
        doc["pages"][0]["guides"] = [_make_guide(figure_regions=[bad_fig])]
        with self.assertRaises(ValueError):
            build_generation_guide_plan(doc)

        # Derived figure area exceeding page bounds
        doc2 = _make_base_doc()
        overflow_fig = {
            "figure_id": "overflow_fig",
            "area": {"x": 0.8, "y": 0.8, "w": 0.5, "h": 0.5},  # x+w = 1.3
            "instance_id": None,
        }
        doc2["pages"][0]["guides"] = [_make_guide(figure_regions=[overflow_fig])]
        with self.assertRaises(ValueError):
            build_generation_guide_plan(doc2)

    def test_case_11_raw_asset_pixel_changes_do_not_change_clean_output(self):
        """11. RAW asset pixel changes do not change CLEAN output (RAW separation proof)."""
        doc_a = _make_base_doc()
        fig = {
            "figure_id": "fig_1",
            "area": contract.make_area(0.15, 0.25, 0.35, 0.55),
            "instance_id": "inst_1",
        }
        doc_a["pages"][0]["guides"] = [
            _make_guide(asset_reference="raw_cat_sketch.png", figure_regions=[fig])
        ]

        doc_b = copy.deepcopy(doc_a)
        # Point to a completely different RAW asset reference
        doc_b["pages"][0]["guides"][0]["asset_reference"] = "raw_robot_render.webp"

        plan_a = build_generation_guide_plan(doc_a)
        plan_b = build_generation_guide_plan(doc_b)

        arr_a = np.asarray(plan_a["canvas_image"].convert("RGB"))
        arr_b = np.asarray(plan_b["canvas_image"].convert("RGB"))

        self.assertTrue(
            np.array_equal(arr_a, arr_b),
            "CLEAN generation guide must be 100% independent of RAW asset pixels/reference",
        )

    def test_case_12_lr3_qualified_fixture_parity(self):
        """12. LR3 qualified fixture pixel/hash parity."""
        self.assertTrue(LR3_WORKFLOW_PATH.exists(), f"Missing LR3 workflow: {LR3_WORKFLOW_PATH}")
        workflow = json.loads(LR3_WORKFLOW_PATH.read_text(encoding="utf-8"))
        doc_json = workflow["prompt"]["1"]["inputs"]["document_json"]
        doc = json.loads(doc_json)

        plan = build_generation_guide_plan(doc, page_index=0)
        self.assertEqual(plan["status"], "PASS")
        self.assertEqual(plan["debug"]["figure_count"], 2)

        # Save to buffer using exact same parameters
        buf = io.BytesIO()
        plan["canvas_image"].save(buf, format="PNG", optimize=False)
        output_bytes = buf.getvalue()
        output_sha256 = hashlib.sha256(output_bytes).hexdigest()

        if LR3_FIXTURE_PATH.exists():
            fixture_bytes = LR3_FIXTURE_PATH.read_bytes()
            fixture_sha256 = hashlib.sha256(fixture_bytes).hexdigest()
            self.assertEqual(fixture_sha256, LR3_CLEAN_SHA256, "Existing LR3 fixture hash mismatch")

            if output_sha256 == LR3_CLEAN_SHA256:
                # Direct SHA256 parity PASS
                self.assertEqual(output_sha256, LR3_CLEAN_SHA256)
            else:
                # Decoded pixel parity check
                with Image.open(LR3_FIXTURE_PATH) as ref_img:
                    ref_arr = np.asarray(ref_img.convert("RGB"))
                out_arr = np.asarray(plan["canvas_image"].convert("RGB"))
                diff = np.abs(out_arr.astype(int) - ref_arr.astype(int))
                self.assertEqual(
                    int(diff.max()), 0,
                    f"Decoded pixel difference must be 0, got max diff {diff.max()}"
                )
        else:
            self.assertEqual(output_sha256, LR3_CLEAN_SHA256)


if __name__ == "__main__":
    unittest.main()
