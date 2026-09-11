"""
scripts/test_m3b_pi2_product_generation_route.py — M3B-PI2 API Contract & Route Tests
====================================================================================
Tests the backend routing contract according to Section 41 of M3B-PI2:
- 1. valid STANDARD route (no guides)
- 2. valid GUIDED route (enabled rough_manga guide with figures)
- 3. disabled Guide -> STANDARD
- 4. zero Figures -> STANDARD
- 5. unassigned Figure -> GUIDED (instance_id is None)
- 6. multiple Guides -> deterministic route
- 7. malformed document -> fail closed
- 8. page_index out of range -> fail closed
- 9. STANDARD prompt has zero ControlNet nodes
- 10. GUIDED prompt has core ControlNet nodes
- 11. GUIDED has zero ACN / effect masks
- 12. seed propagated from document to Node 1 and Node 6
- 13. frame overlay retained in both routes
- 14. RAW asset path not consumed by routing (asset existence alone doesn't trigger guided)
"""

from __future__ import annotations

import copy
import json
import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "ComfyUI"))

from custom_nodes_custom.tegaki_manga_nodes.product_generation_router import (
    ROUTE_STANDARD,
    ROUTE_GUIDED,
    evaluate_generation_route,
    prepare_generation_prompt,
    build_standard_prompt,
    build_guided_prompt,
    is_controlnet_available,
    CONTROLNET_MODEL_SELECTOR,
)


def create_base_doc(
    has_guide: bool = False,
    guide_enabled: bool = True,
    figure_count: int = 1,
    instance_id: str | None = "inst_1",
    seed: int = 42,
) -> dict:
    guides = []
    if has_guide:
        figs = []
        for i in range(figure_count):
            figs.append({
                "figure_id": f"fig_{i+1}",
                "instance_id": instance_id,
                "area": {"shape_type": "rect", "x": 0.1 * (i + 1), "y": 0.2, "w": 0.3, "h": 0.5},
            })
        guides.append({
            "guide_id": "guide_1",
            "guide_type": "rough_manga",
            "asset_reference": "tegaki_manga_guides/rough_guide_live.png",
            "enabled": guide_enabled,
            "placement": {"x": 0.0, "y": 0.2, "w": 1.0, "h": 0.6},
            "figure_regions": figs,
        })

    return {
        "schema_id": "TEGAKI_AUTHORING_DOCUMENT",
        "schema_version": "1.0.0",
        "document_id": "test_doc",
        "pages": [
            {
                "page_id": "page_1",
                "order": 1,
                "width_px": 832,
                "height_px": 1216,
                "style_prompt": "manga page, monochrome",
                "style_negative_prompt": "blurry, photo",
                "scenes": [
                    {
                        "scene_id": "scene_1",
                        "name": "Scene 1",
                        "prompt": "classroom",
                        "negative_prompt": "",
                        "input_mode": "simple",
                        "area": {"shape_type": "rect", "x": 0.08, "y": 0.06, "w": 0.84, "h": 0.88},
                        "order": 1,
                        "metadata": {},
                    }
                ],
                "visual_frames": [],
                "cast": [],
                "character_instances": [],
                "guides": guides,
                "metadata": {"style_template": "Manga Monochrome"},
                "generation": {"seed": seed},
            }
        ],
        "metadata": {},
    }


class TestProductGenerationRoute(unittest.TestCase):

    def test_01_valid_standard_route_no_guides(self):
        """1. No guides on page -> routes to STANDARD_NO_GUIDE."""
        doc = create_base_doc(has_guide=False)
        route, reason, meta = evaluate_generation_route(doc, 0)
        self.assertEqual(route, ROUTE_STANDARD)
        self.assertEqual(meta["eligible_guide_count"], 0)
        self.assertEqual(meta["figure_count"], 0)

    def test_02_valid_guided_route(self):
        """2. Enabled rough_manga guide with figures -> routes to GUIDED_CLEAN_GLOBAL."""
        doc = create_base_doc(has_guide=True, guide_enabled=True, figure_count=2)
        route, reason, meta = evaluate_generation_route(doc, 0)
        self.assertEqual(route, ROUTE_GUIDED)
        self.assertEqual(meta["eligible_guide_count"], 1)
        self.assertEqual(meta["figure_count"], 2)

    def test_03_disabled_guide_routes_standard(self):
        """3. Disabled rough_manga Guide -> routes to STANDARD_NO_GUIDE."""
        doc = create_base_doc(has_guide=True, guide_enabled=False, figure_count=2)
        route, reason, meta = evaluate_generation_route(doc, 0)
        self.assertEqual(route, ROUTE_STANDARD)
        self.assertEqual(meta["eligible_guide_count"], 0)
        self.assertEqual(meta["figure_count"], 0)
        self.assertIn("disabled", reason.lower())

    def test_04_zero_figures_routes_standard(self):
        """4. Enabled rough_manga Guide with 0 figures -> routes to STANDARD_NO_GUIDE."""
        doc = create_base_doc(has_guide=True, guide_enabled=True, figure_count=0)
        route, reason, meta = evaluate_generation_route(doc, 0)
        self.assertEqual(route, ROUTE_STANDARD)
        self.assertEqual(meta["eligible_guide_count"], 0)
        self.assertEqual(meta["figure_count"], 0)
        self.assertIn("zero figure", reason.lower())

    def test_05_unassigned_figure_routes_guided(self):
        """5. Figure region with instance_id=None -> routes to GUIDED_CLEAN_GLOBAL."""
        doc = create_base_doc(has_guide=True, guide_enabled=True, figure_count=1, instance_id=None)
        route, reason, meta = evaluate_generation_route(doc, 0)
        self.assertEqual(route, ROUTE_GUIDED)
        self.assertEqual(meta["eligible_guide_count"], 1)
        self.assertEqual(meta["figure_count"], 1)

    def test_06_multiple_guides_deterministic_route(self):
        """6. Multiple guides on page: deterministic evaluation."""
        doc = create_base_doc(has_guide=True, guide_enabled=False, figure_count=2)
        # Add a second guide that is enabled and has figures
        doc["pages"][0]["guides"].append({
            "guide_id": "guide_2",
            "guide_type": "rough_manga",
            "enabled": True,
            "figure_regions": [
                {"figure_id": "fig_g2", "area": {"shape_type": "rect", "x": 0.1, "y": 0.1, "w": 0.5, "h": 0.5}}
            ],
        })
        route, reason, meta = evaluate_generation_route(doc, 0)
        self.assertEqual(route, ROUTE_GUIDED)
        self.assertEqual(meta["eligible_guide_count"], 1)
        self.assertEqual(meta["figure_count"], 1)

    def test_07_malformed_document_fails_closed(self):
        """7. Malformed document fails closed with exception."""
        with self.assertRaises(ValueError):
            evaluate_generation_route({}, 0)
        with self.assertRaises(ValueError):
            evaluate_generation_route({"pages": []}, 0)
        with self.assertRaises(ValueError):
            evaluate_generation_route("not a dict", 0)

    def test_08_page_index_out_of_range_fails_closed(self):
        """8. page_index out of range fails closed with IndexError."""
        doc = create_base_doc(has_guide=False)
        with self.assertRaises(IndexError):
            evaluate_generation_route(doc, 1)
        with self.assertRaises(IndexError):
            evaluate_generation_route(doc, -1)

    def test_09_standard_prompt_zero_controlnet_nodes(self):
        """9. STANDARD prompt must contain ZERO ControlNet or bridge nodes."""
        doc = create_base_doc(has_guide=False)
        res = prepare_generation_prompt(doc, 0)
        self.assertTrue(res["ok"])
        self.assertEqual(res["route"], ROUTE_STANDARD)
        prompt = res["prompt"]

        node_classes = [n["class_type"] for n in prompt.values()]
        for prohibited in [
            "ControlNetLoader",
            "ControlNetApplyAdvanced",
            "TegakiMangaGenerationGuideBridge",
            "ACN_AdvancedControlNetApply_v2",
        ]:
            self.assertNotIn(prohibited, node_classes, f"Prohibited node {prohibited} found in STANDARD prompt")

        for cls in node_classes:
            self.assertNotIn("controlnet", cls.lower())

        self.assertFalse(res["route_meta"]["has_controlnet_nodes"])

    def test_10_guided_prompt_has_core_controlnet_nodes(self):
        """10. GUIDED prompt must contain core ControlNetApplyAdvanced & Guide Bridge."""
        doc = create_base_doc(has_guide=True, guide_enabled=True, figure_count=1)
        res = prepare_generation_prompt(doc, 0)
        self.assertTrue(res["ok"])
        self.assertEqual(res["route"], ROUTE_GUIDED)
        prompt = res["prompt"]

        node_classes = [n["class_type"] for n in prompt.values()]
        for required in [
            "TegakiMinimumHandSceneEditor",
            "TegakiMangaConditioningBuilder",
            "TegakiMangaGenerationGuideBridge",
            "ControlNetLoader",
            "ControlNetApplyAdvanced",
            "KSampler",
            "VAEDecode",
            "TegakiMangaFrameOverlay",
            "SaveImage",
        ]:
            self.assertIn(required, node_classes, f"Required node {required} missing from GUIDED prompt")

        # Verify fixed parameters on ControlNetApplyAdvanced
        cn_node = next(n for n in prompt.values() if n["class_type"] == "ControlNetApplyAdvanced")
        self.assertEqual(cn_node["inputs"]["strength"], 0.75)
        self.assertEqual(cn_node["inputs"]["start_percent"], 0.0)
        self.assertEqual(cn_node["inputs"]["end_percent"], 1.0)

    def test_11_guided_has_zero_acn_and_zero_effect_masks(self):
        """11. GUIDED prompt must contain 0 Advanced-ControlNet and 0 effect masks."""
        doc = create_base_doc(has_guide=True, guide_enabled=True, figure_count=1)
        res = prepare_generation_prompt(doc, 0)
        prompt = res["prompt"]

        node_classes = [n["class_type"] for n in prompt.values()]
        self.assertNotIn("ACN_AdvancedControlNetApply_v2", node_classes)
        for cls in node_classes:
            self.assertFalse(cls.startswith("ACN_"), f"ACN node found: {cls}")

        # Check inputs for effect mask connections
        for nid, node in prompt.items():
            inputs = node.get("inputs", {})
            self.assertNotIn("mask_optional", inputs)
            self.assertNotIn("effect_mask", inputs)

    def test_12_seed_propagation(self):
        """12. Seed from document is propagated to Node 1 and KSampler."""
        test_seed = 987654321
        doc = create_base_doc(has_guide=False, seed=test_seed)
        res = prepare_generation_prompt(doc, 0)
        prompt = res["prompt"]

        self.assertEqual(prompt["1"]["inputs"]["seed"], test_seed)
        self.assertEqual(prompt["6"]["inputs"]["seed"], test_seed)
        self.assertEqual(res["route_meta"]["seed"], test_seed)

    def test_13_frame_overlay_retained(self):
        """13. Frame overlay is retained in both STANDARD and GUIDED prompts."""
        for has_guide in (False, True):
            doc = create_base_doc(has_guide=has_guide, guide_enabled=True, figure_count=1)
            res = prepare_generation_prompt(doc, 0)
            prompt = res["prompt"]
            self.assertIn("9", prompt)
            self.assertEqual(prompt["9"]["class_type"], "TegakiMangaFrameOverlay")
            self.assertEqual(prompt["8"]["class_type"], "SaveImage")
            self.assertEqual(prompt["8"]["inputs"]["images"], ["9", 0])

    def test_14_raw_asset_path_not_consumed_by_routing(self):
        """14. Asset reference existence alone does NOT trigger Guided route."""
        # Guide with asset reference but 0 figures
        doc = create_base_doc(has_guide=True, guide_enabled=True, figure_count=0)
        doc["pages"][0]["guides"][0]["asset_reference"] = "path/to/some/valid/asset.png"
        route, reason, meta = evaluate_generation_route(doc, 0)
        self.assertEqual(route, ROUTE_STANDARD)
        self.assertEqual(meta["eligible_guide_count"], 0)


if __name__ == "__main__":
    unittest.main()
