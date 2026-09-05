"""
test_phase3j_layout_guide_shot_types.py
========================================
Phase 3J automated test suite validating:
1. Clean Per-Region Hint v2: include_bbox_outline toggle (True vs False).
2. Adaptive Shot Type Foundation: vertical spatial distribution of full_body, half_body, and bust.
3. Manga Impact Regional Adapter: regional_control_end_percent and per-region hint injection with shot_type.
"""

import os
import sys
import unittest
import torch
import numpy as np

# Ensure ComfyUI and custom nodes are on path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
COMFY_DIR = os.path.join(ROOT_DIR, "ComfyUI")
CUSTOM_NODES_DIR = os.path.join(ROOT_DIR, "custom_nodes_custom")
IMPACT_PACK_DIR = os.path.join(COMFY_DIR, "custom_nodes", "ComfyUI-Impact-Pack", "modules")

for p in [ROOT_DIR, COMFY_DIR, CUSTOM_NODES_DIR, IMPACT_PACK_DIR]:
    if p not in sys.path:
        sys.path.insert(0, p)

from custom_nodes_custom.tegaki_manga_nodes.layout_guide_generator import (
    draw_single_character_mannequin,
    generate_single_character_guide_image,
    extract_staging_boxes,
    TegakiMangaLayoutGuideGenerator
)
from custom_nodes_custom.tegaki_manga_nodes.manga_impact_regional_adapter import TegakiMangaImpactRegionalAdapter


class TestPhase3JLayoutGuideShotTypes(unittest.TestCase):
    def test_01_include_bbox_outline_toggle(self):
        """Verify that include_bbox_outline=False eliminates outer bounding box outline."""
        W, H = 512, 512
        bounds = [100, 100, 200, 400] # rx0, ry0, rx1, ry1

        img_with_box = generate_single_character_guide_image(
            width=W, height=H, pixel_bounds=bounds,
            guide_style="mannequin_capsule",
            include_bbox_outline=True
        ) # [1, H, W, 3], black on white (white=1.0, black=0.0)

        img_no_box = generate_single_character_guide_image(
            width=W, height=H, pixel_bounds=bounds,
            guide_style="mannequin_capsule",
            include_bbox_outline=False
        )

        # In img_with_box, the top-left corner (100, 100) has the outline drawn (non-1.0)
        # In img_no_box, corner (100, 100) and outer corners must be pure white (1.0)
        corner_val_with_box = img_with_box[0, 100, 100, 0].item()
        corner_val_no_box = img_no_box[0, 100, 100, 0].item()

        self.assertLess(corner_val_with_box, 0.99, "Bounding box outline should be drawn when include_bbox_outline=True")
        self.assertAlmostEqual(corner_val_no_box, 1.0, places=4, msg="Bounding box corner should be pure white when include_bbox_outline=False")

        # Check entire top border [rx0:rx0+20, ry0]
        # In no_box, the top border near corners has zero drawn pixels
        top_left_segment_no_box = img_no_box[0, 100, 100:120, :].mean().item()
        self.assertAlmostEqual(top_left_segment_no_box, 1.0, places=4, msg="Box boundary edge should be pure white when outline is omitted")

    def test_02_shot_types_density_profile(self):
        """Verify that full_body, half_body, and bust produce distinct vertical distribution profiles."""
        W, H = 512, 512
        bounds = [100, 50, 300, 450] # rx0, ry0, rx1, ry1 (h = 400)
        rx0, ry0, rx1, ry1 = bounds
        ch = ry1 - ry0

        img_full = generate_single_character_guide_image(
            width=W, height=H, pixel_bounds=bounds,
            guide_style="mannequin_capsule",
            include_bbox_outline=False,
            shot_type="full_body"
        )
        img_half = generate_single_character_guide_image(
            width=W, height=H, pixel_bounds=bounds,
            guide_style="mannequin_capsule",
            include_bbox_outline=False,
            shot_type="half_body"
        )
        img_bust = generate_single_character_guide_image(
            width=W, height=H, pixel_bounds=bounds,
            guide_style="mannequin_capsule",
            include_bbox_outline=False,
            shot_type="bust"
        )

        # Convert to drawn pixel masks (1 = drawn/black, 0 = white bg)
        drawn_full = (img_full[0, :, :, :].mean(dim=-1) < 0.9).float()
        drawn_half = (img_half[0, :, :, :].mean(dim=-1) < 0.9).float()
        drawn_bust = (img_bust[0, :, :, :].mean(dim=-1) < 0.9).float()

        # Lower 20% of the character box (feet/ankles in full body)
        lower_y0 = ry0 + int(ch * 0.80)
        lower_y1 = ry1

        full_lower_pixels = drawn_full[lower_y0:lower_y1, rx0:rx1].sum().item()
        half_lower_pixels = drawn_half[lower_y0:lower_y1, rx0:rx1].sum().item()
        bust_lower_pixels = drawn_bust[lower_y0:lower_y1, rx0:rx1].sum().item()

        self.assertGreater(full_lower_pixels, 10, "Full body must have drawn pixels in the lower 20% (legs/feet)")
        self.assertEqual(half_lower_pixels, 0, "Half body should omit legs in the lower 20%")
        self.assertEqual(bust_lower_pixels, 0, "Bust shot must have exactly 0 drawn pixels in the lower 20%")

        # Lower 40% of character box (hips down)
        mid_lower_y0 = ry0 + int(ch * 0.60)
        bust_mid_lower = drawn_bust[mid_lower_y0:lower_y1, rx0:rx1].sum().item()
        self.assertEqual(bust_mid_lower, 0, "Bust shot must have 0 drawn pixels in lower 40%")

    def test_03_regional_adapter_shot_type_and_end_percent(self):
        """Verify that regional adapter correctly applies regional_control_end_percent and handles shot_type."""
        from custom_nodes_custom.tegaki_manga_nodes.scene_compiler import TegakiMangaPageCompiler
        from custom_nodes_custom.tegaki_manga_nodes.cast_master import get_default_cast_spec
        from custom_nodes_custom.tegaki_manga_nodes.panel_layout_spec import get_default_panel_layout_spec
        from custom_nodes_custom.tegaki_manga_nodes.region_editor import default_region_spec

        adapter = TegakiMangaImpactRegionalAdapter()

        class MockCLIP:
            def tokenize(self, text):
                return {"g": [[1, 2, 3]], "l": [[4, 5, 6]]}
            def encode_from_tokens_scheduled(self, tokens):
                cond_tensor = torch.zeros((1, 77, 2048), dtype=torch.float32)
                pooled_tensor = torch.zeros((1, 1280), dtype=torch.float32)
                return [[cond_tensor, {"pooled_output": pooled_tensor}]]

        class MockControl:
            def __init__(self):
                self.strength = 1.0
                self.timestep_percent_range = (0.0, 1.0)
                self.cond_hint = None
            def copy(self):
                c = MockControl()
                c.strength = self.strength
                c.timestep_percent_range = self.timestep_percent_range
                return c
            def set_cond_hint(self, cond_hint, strength, timestep_percent_range, vae=None):
                self.cond_hint = cond_hint
                self.strength = strength
                self.timestep_percent_range = timestep_percent_range
                return self

        class MockSampler:
            def __init__(self, control_obj):
                self.params = [None, None, None, None, [[torch.zeros(1, 4), {"control": control_obj, "control_apply_to_uncond": False}]]]
            def clone_with_conditionings(self, pos, neg):
                s = MockSampler(None)
                s.params = [None, None, None, None, pos, neg]
                return s

        ctrl = MockControl()
        base_sampler = MockSampler(ctrl)
        clip = MockCLIP()

        cast_data = get_default_cast_spec()
        layout_data = get_default_panel_layout_spec(512, 512, preset="1_full")
        reg_spec = default_region_spec(512, 512, panel_count=1)
        reg_spec["regions"][0]["characters"] = [
            {"character_id": "char_alice", "name": "Alice", "enabled": True, "shot_type": "bust", "area": {"x": 0.1, "y": 0.15, "w": 0.4, "h": 0.75}},
        ]
        page_compiler = TegakiMangaPageCompiler()
        compile_plan, _, _, _ = page_compiler.compile_page(
            region_spec=reg_spec,
            cast_spec=cast_data
        )

        # Build with per_region_hint and regional_control_end_percent=0.55
        regional_prompts, masks, preview, debug_json = adapter.build_regional_prompts(
            page_compile_plan=compile_plan,
            panel_layout_spec=layout_data,
            base_sampler=base_sampler,
            clip=clip,
            regional_control_mode="per_region_hint",
            regional_control_strength=0.35,
            regional_control_end_percent=0.55
        )

        # Inspect the character instance regional prompt
        char_rp = regional_prompts[1] # index 0 is panel_scene, index 1 is character
        char_pos_cond = char_rp.sampler.params[4]
        self.assertIn("control", char_pos_cond[0][1], "Regional conditioning must have control object attached")
        char_ctrl = char_pos_cond[0][1]["control"]
        self.assertAlmostEqual(char_ctrl.strength, 0.35, places=2)
        self.assertEqual(char_ctrl.timestep_percent_range, (0.0, 0.55), "ControlNet should disengage at 0.55")


if __name__ == "__main__":
    unittest.main()
