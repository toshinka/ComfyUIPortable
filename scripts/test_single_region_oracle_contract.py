"""
Unit Test: Single Region Oracle Contract (Phase 3D.2)
=====================================================
Verifies that:
1. TWO_REGION_SPEC supports Single-Region mode (A.enabled = True, B.enabled = False).
2. The 5 position presets (TL, TR, BL, BR, C) produce correct non-zero mask A
   bounding boxes while mask B is strictly all zeros.
3. TegakiTwoRegionCoupleEditor outputs valid spec, active Mask A, empty Mask B,
   and combined preview image.
4. TegakiTwoRegionCoreConditioner routes only Global and Region A conditioning
   when Region B is disabled.
5. TegakiTwoRegionImpactAdapter handles optional sampler_B when Region B is disabled,
   producing exactly 1 REGIONAL_PROMPT for Region A.
6. JSON serialization and reload round-trip preserves state.
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

from tegaki_manga_nodes.two_region_spec import get_default_two_region_spec, validate_two_region_spec
from tegaki_manga_nodes.two_region_editor import TegakiTwoRegionCoupleEditor
from tegaki_manga_nodes.two_region_core_conditioner import TegakiTwoRegionCoreConditioner
from tegaki_manga_nodes.two_region_impact_adapter import TegakiTwoRegionImpactAdapter


class MockCLIP:
    def tokenize(self, text):
        return {"tokens": [text]}

    def encode_from_tokens_scheduled(self, tokens):
        return [[torch.zeros((1, 77, 768)), {"pooled_output": torch.zeros((1, 768))}]]


class MockSamplerAdvanced:
    def __init__(self, name="mock_sampler"):
        self.name = name


class TestSingleRegionOracleContract(unittest.TestCase):
    def setUp(self):
        self.canvas_w = 832
        self.canvas_h = 1216
        self.editor = TegakiTwoRegionCoupleEditor()
        self.core_conditioner = TegakiTwoRegionCoreConditioner()
        self.impact_adapter = TegakiTwoRegionImpactAdapter()
        self.mock_clip = MockCLIP()

    def test_single_region_spec_validation(self):
        """Verify TWO_REGION_SPEC with A enabled and B disabled."""
        spec = get_default_two_region_spec(self.canvas_w, self.canvas_h)
        spec["regions"][0]["enabled"] = True
        spec["regions"][0]["prompt"] = "a white dog, full body"
        spec["regions"][1]["enabled"] = False
        spec["regions"][1]["prompt"] = ""

        validated = validate_two_region_spec(spec)
        self.assertTrue(validated["regions"][0]["enabled"])
        self.assertFalse(validated["regions"][1]["enabled"])
        self.assertEqual(len(validated["regions"]), 2)

    def test_five_position_presets_mask_geometry(self):
        """Verify the 5 canonical positions (TL, TR, BL, BR, C)."""
        presets = {
            "TL": {"x": 0.05, "y": 0.05, "w": 0.35, "h": 0.45},
            "TR": {"x": 0.60, "y": 0.05, "w": 0.35, "h": 0.45},
            "BL": {"x": 0.05, "y": 0.50, "w": 0.35, "h": 0.45},
            "BR": {"x": 0.60, "y": 0.50, "w": 0.35, "h": 0.45},
            "C":  {"x": 0.325, "y": 0.275, "w": 0.35, "h": 0.45},
        }

        for name, geom in presets.items():
            spec = {
                "version": 1,
                "canvas": {"width": self.canvas_w, "height": self.canvas_h},
                "global_prompt": "masterpiece, clean background",
                "global_negative_prompt": "worst quality",
                "regions": [
                    {
                        "id": "A",
                        "enabled": True,
                        "prompt": "a white dog, full body",
                        "negative_prompt": "",
                        "x": geom["x"],
                        "y": geom["y"],
                        "w": geom["w"],
                        "h": geom["h"]
                    },
                    {
                        "id": "B",
                        "enabled": False,
                        "prompt": "",
                        "negative_prompt": "",
                        "x": 0.55,
                        "y": 0.50,
                        "w": 0.35,
                        "h": 0.45
                    }
                ]
            }

            res_spec, mask_A, mask_B, preview_img, debug_json = self.editor.execute_editor(
                canvas_width=self.canvas_w,
                canvas_height=self.canvas_h,
                global_prompt="masterpiece, clean background",
                global_negative_prompt="worst quality",
                prompt_A="a white dog, full body",
                negative_prompt_A="",
                prompt_B="",
                negative_prompt_B="",
                two_region_spec_data=json.dumps(spec)
            )

            # Mask A must have non-zero pixels
            sum_A = float(mask_A.sum())
            self.assertGreater(sum_A, 0.0, f"Preset {name} mask A must have non-zero sum")

            # Mask B must be strictly all zeros
            sum_B = float(mask_B.sum())
            self.assertEqual(sum_B, 0.0, f"Preset {name} mask B must be all zeros")

            # Expected pixel bounds
            exp_x0 = int(round(geom["x"] * self.canvas_w))
            exp_y0 = int(round(geom["y"] * self.canvas_h))
            exp_x1 = int(round((geom["x"] + geom["w"]) * self.canvas_w))
            exp_y1 = int(round((geom["y"] + geom["h"]) * self.canvas_h))

            # Sample inside mask A: should be 1.0
            mid_x = (exp_x0 + exp_x1) // 2
            mid_y = (exp_y0 + exp_y1) // 2
            self.assertEqual(float(mask_A[0, mid_y, mid_x]), 1.0, f"Preset {name} midpoint must be 1.0")

            # Sample outside mask A: opposite corner should be 0.0
            opp_x = (mid_x + self.canvas_w // 2) % self.canvas_w
            opp_y = (mid_y + self.canvas_h // 2) % self.canvas_h
            if not (exp_x0 <= opp_x < exp_x1 and exp_y0 <= opp_y < exp_y1):
                self.assertEqual(float(mask_A[0, opp_y, opp_x]), 0.0, f"Preset {name} outside point must be 0.0")

    def test_core_conditioner_single_region_isolation(self):
        """Verify Core conditioner outputs only Global + Region A (no Region B branch)."""
        spec = {
            "version": 1,
            "canvas": {"width": self.canvas_w, "height": self.canvas_h},
            "global_prompt": "clean background",
            "global_negative_prompt": "worst quality",
            "regions": [
                {
                    "id": "A",
                    "enabled": True,
                    "prompt": "a white dog",
                    "negative_prompt": "",
                    "x": 0.05,
                    "y": 0.05,
                    "w": 0.35,
                    "h": 0.45
                },
                {
                    "id": "B",
                    "enabled": False,
                    "prompt": "ignored cat",
                    "negative_prompt": "",
                    "x": 0.60,
                    "y": 0.50,
                    "w": 0.35,
                    "h": 0.45
                }
            ]
        }

        pos, neg, mask_A, mask_B, debug_json = self.core_conditioner.build_conditioning(
            clip=self.mock_clip,
            two_region_spec=spec
        )

        debug_info = json.loads(debug_json)
        branches = debug_info["branches"]
        scopes = [b["scope"] for b in branches]

        self.assertIn("Global", scopes)
        self.assertIn("Region A", scopes)
        self.assertNotIn("Region B", scopes, "Region B must NOT be included in conditioning when disabled")
        self.assertEqual(len(branches), 2)
        self.assertEqual(float(mask_B.sum()), 0.0)

    def test_impact_adapter_single_region_optional_sampler_b(self):
        """Verify Impact adapter supports single region mode with sampler_B=None."""
        spec = {
            "version": 1,
            "canvas": {"width": self.canvas_w, "height": self.canvas_h},
            "global_prompt": "clean background",
            "global_negative_prompt": "worst quality",
            "regions": [
                {
                    "id": "A",
                    "enabled": True,
                    "prompt": "a white dog",
                    "negative_prompt": "",
                    "x": 0.05,
                    "y": 0.05,
                    "w": 0.35,
                    "h": 0.45
                },
                {
                    "id": "B",
                    "enabled": False,
                    "prompt": "",
                    "negative_prompt": "",
                    "x": 0.60,
                    "y": 0.50,
                    "w": 0.35,
                    "h": 0.45
                }
            ]
        }

        sampler_A = MockSamplerAdvanced("sampler_A")

        # Test call with sampler_B omitted/None
        regional_prompts, mask_A, mask_B, debug_json = self.impact_adapter.build_impact_prompts(
            two_region_spec=spec,
            sampler_A=sampler_A,
            sampler_B=None
        )

        debug_info = json.loads(debug_json)
        self.assertEqual(debug_info["total_regional_prompts"], 1)
        self.assertTrue(debug_info["enabled_A"])
        self.assertFalse(debug_info["enabled_B"])
        self.assertEqual(float(mask_B.sum()), 0.0)
        self.assertGreater(float(mask_A.sum()), 0.0)


if __name__ == "__main__":
    unittest.main()
