"""
Unit Test: Two-Region Geometry Swap (Phase 3D.2)
================================================
Verifies that:
1. Two-Region spec maintains unchanged prompts for A (Dog) and B (Cat).
2. Swapping the geometry rectangles (A left -> right, B right -> left)
   flips the mask centroids of Mask A and Mask B.
3. Both Core conditioner and Impact adapter receive the swapped masks
   faithfully without text prompt mutation.
"""

import json
import os
import sys
import unittest
import torch

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CUSTOM_NODES_DIR = os.path.join(ROOT_DIR, "custom_nodes_custom")
if CUSTOM_NODES_DIR not in sys.path:
    sys.path.insert(0, CUSTOM_NODES_DIR)

from tegaki_manga_nodes.two_region_spec import validate_two_region_spec
from tegaki_manga_nodes.two_region_editor import TegakiTwoRegionCoupleEditor
from tegaki_manga_nodes.two_region_impact_adapter import TegakiTwoRegionImpactAdapter
from tegaki_manga_nodes.two_region_core_conditioner import TegakiTwoRegionCoreConditioner


class MockCLIP:
    def tokenize(self, text):
        return {"tokens": [text]}

    def encode_from_tokens_scheduled(self, tokens):
        return [[torch.zeros((1, 77, 768)), {"pooled_output": torch.zeros((1, 768))}]]


class MockSampler:
    def __init__(self, name):
        self.name = name


def compute_mask_centroid(mask: torch.Tensor):
    # mask: (1, H, W)
    coords = torch.nonzero(mask[0])
    if len(coords) == 0:
        return 0.0, 0.0
    cy = float(coords[:, 0].float().mean())
    cx = float(coords[:, 1].float().mean())
    return cx, cy


class TestTwoRegionGeometrySwap(unittest.TestCase):
    def setUp(self):
        self.canvas_w = 832
        self.canvas_h = 1216
        self.editor = TegakiTwoRegionCoupleEditor()
        self.impact_adapter = TegakiTwoRegionImpactAdapter()
        self.core_conditioner = TegakiTwoRegionCoreConditioner()
        self.mock_clip = MockCLIP()

    def test_geometry_swap_preserves_prompts_and_swaps_masks(self):
        prompt_A = "a white dog, full body"
        prompt_B = "a black cat, full body"

        # 1. Original Layout: A = Left, B = Right
        spec_orig = {
            "version": 1,
            "canvas": {"width": self.canvas_w, "height": self.canvas_h},
            "global_prompt": "simple park background, two subjects",
            "global_negative_prompt": "worst quality",
            "regions": [
                {
                    "id": "A",
                    "enabled": True,
                    "prompt": prompt_A,
                    "negative_prompt": "",
                    "x": 0.05,
                    "y": 0.10,
                    "w": 0.42,
                    "h": 0.80
                },
                {
                    "id": "B",
                    "enabled": True,
                    "prompt": prompt_B,
                    "negative_prompt": "",
                    "x": 0.53,
                    "y": 0.10,
                    "w": 0.42,
                    "h": 0.80
                }
            ]
        }

        # 2. Swapped Layout: A = Right, B = Left (Prompts UNCHANGED)
        spec_swapped = {
            "version": 1,
            "canvas": {"width": self.canvas_w, "height": self.canvas_h},
            "global_prompt": "simple park background, two subjects",
            "global_negative_prompt": "worst quality",
            "regions": [
                {
                    "id": "A",
                    "enabled": True,
                    "prompt": prompt_A,  # Identical prompt A!
                    "negative_prompt": "",
                    "x": 0.53,
                    "y": 0.10,
                    "w": 0.42,
                    "h": 0.80
                },
                {
                    "id": "B",
                    "enabled": True,
                    "prompt": prompt_B,  # Identical prompt B!
                    "negative_prompt": "",
                    "x": 0.05,
                    "y": 0.10,
                    "w": 0.42,
                    "h": 0.80
                }
            ]
        }

        # Execute Editor for Original
        _, mask_A_orig, mask_B_orig, _, _ = self.editor.execute_editor(
            canvas_width=self.canvas_w,
            canvas_height=self.canvas_h,
            global_prompt=spec_orig["global_prompt"],
            global_negative_prompt=spec_orig["global_negative_prompt"],
            prompt_A=prompt_A,
            negative_prompt_A="",
            prompt_B=prompt_B,
            negative_prompt_B="",
            two_region_spec_data=json.dumps(spec_orig)
        )

        # Execute Editor for Swapped
        _, mask_A_swap, mask_B_swap, _, _ = self.editor.execute_editor(
            canvas_width=self.canvas_w,
            canvas_height=self.canvas_h,
            global_prompt=spec_swapped["global_prompt"],
            global_negative_prompt=spec_swapped["global_negative_prompt"],
            prompt_A=prompt_A,
            negative_prompt_A="",
            prompt_B=prompt_B,
            negative_prompt_B="",
            two_region_spec_data=json.dumps(spec_swapped)
        )

        # Calculate mask centroids
        cx_A_orig, _ = compute_mask_centroid(mask_A_orig)
        cx_B_orig, _ = compute_mask_centroid(mask_B_orig)

        cx_A_swap, _ = compute_mask_centroid(mask_A_swap)
        cx_B_swap, _ = compute_mask_centroid(mask_B_swap)

        mid_x = self.canvas_w / 2.0

        # In Original: A must be on the left (< mid_x), B on the right (> mid_x)
        self.assertLess(cx_A_orig, mid_x, "Original Mask A must be on Left")
        self.assertGreater(cx_B_orig, mid_x, "Original Mask B must be on Right")

        # In Swapped: A must be on the right (> mid_x), B on the left (< mid_x)
        self.assertGreater(cx_A_swap, mid_x, "Swapped Mask A must be on Right")
        self.assertLess(cx_B_swap, mid_x, "Swapped Mask B must be on Left")

        # Check that centroids match inverse positions
        self.assertAlmostEqual(cx_A_orig, cx_B_swap, delta=2.0, msg="A orig and B swapped must share left x")
        self.assertAlmostEqual(cx_B_orig, cx_A_swap, delta=2.0, msg="B orig and A swapped must share right x")

        # Impact Adapter check
        sampler_A = MockSampler("sampler_A")
        sampler_B = MockSampler("sampler_B")
        rp_orig, m_A_imp_orig, m_B_imp_orig, _ = self.impact_adapter.build_impact_prompts(
            two_region_spec=spec_orig,
            sampler_A=sampler_A,
            sampler_B=sampler_B
        )
        rp_swap, m_A_imp_swap, m_B_imp_swap, _ = self.impact_adapter.build_impact_prompts(
            two_region_spec=spec_swapped,
            sampler_A=sampler_A,
            sampler_B=sampler_B
        )

        self.assertEqual(len(rp_orig), 2)
        self.assertEqual(len(rp_swap), 2)

        cx_imp_A_orig, _ = compute_mask_centroid(m_A_imp_orig)
        cx_imp_A_swap, _ = compute_mask_centroid(m_A_imp_swap)
        self.assertLess(cx_imp_A_orig, mid_x)
        self.assertGreater(cx_imp_A_swap, mid_x)

        # Core Conditioner check
        _, _, m_A_core_orig, m_B_core_orig, _ = self.core_conditioner.build_conditioning(
            clip=self.mock_clip,
            two_region_spec=spec_orig
        )
        _, _, m_A_core_swap, m_B_core_swap, _ = self.core_conditioner.build_conditioning(
            clip=self.mock_clip,
            two_region_spec=spec_swapped
        )
        cx_core_A_orig, _ = compute_mask_centroid(m_A_core_orig)
        cx_core_A_swap, _ = compute_mask_centroid(m_A_core_swap)
        self.assertLess(cx_core_A_orig, mid_x)
        self.assertGreater(cx_core_A_swap, mid_x)


if __name__ == "__main__":
    unittest.main()
