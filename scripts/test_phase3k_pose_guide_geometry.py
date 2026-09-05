"""
Test Phase 3K: Pose Guide Geometry and Pixel Mannequin Patterns
===============================================================
Validates:
1. Mannequin pixel differentiation: standing_neutral != facing_left.
2. Mirror symmetry: facing_left is identical to the horizontal mirror of facing_right.
3. Sitting bent-leg spatial density distribution:
   sitting concentrates drawn pixels in the lower-middle region (thighs/lap) compared to vertical leg pillars.
4. Orthogonal combinations:
   shot_type (full_body, half_body, bust) x pose_preset (standing_neutral, facing_left, facing_right, sitting).
5. Handshake pair guide anchor connectivity:
   Midpoint anchor connects left and right mannequin arms.
"""

import os
import sys
import unittest
import torch
import numpy as np

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
COMFY_DIR = os.path.join(ROOT_DIR, "ComfyUI")
CUSTOM_NODES_DIR = os.path.join(ROOT_DIR, "custom_nodes_custom")
IMPACT_PACK_DIR = os.path.join(COMFY_DIR, "custom_nodes", "ComfyUI-Impact-Pack", "modules")

for p in [ROOT_DIR, COMFY_DIR, CUSTOM_NODES_DIR, IMPACT_PACK_DIR]:
    if p not in sys.path:
        sys.path.insert(0, p)

from custom_nodes_custom.tegaki_manga_nodes.layout_guide_generator import (
    generate_single_character_guide_image,
    draw_single_character_mannequin,
    TegakiMangaLayoutGuideGenerator
)


class TestPhase3KPoseGuideGeometry(unittest.TestCase):

    def test_01_neutral_vs_facing_left_differentiation(self):
        """standing_neutral and facing_left must produce significantly different pixel patterns."""
        W, H = 512, 512
        bounds = [100, 50, 300, 450]

        img_neutral = generate_single_character_guide_image(
            width=W, height=H, pixel_bounds=bounds,
            guide_style="mannequin_capsule",
            include_bbox_outline=False,
            shot_type="full_body",
            pose_preset="standing_neutral"
        )
        img_left = generate_single_character_guide_image(
            width=W, height=H, pixel_bounds=bounds,
            guide_style="mannequin_capsule",
            include_bbox_outline=False,
            shot_type="full_body",
            pose_preset="facing_left"
        )

        diff = torch.abs(img_neutral - img_left).sum().item()
        self.assertGreater(diff, 50.0, f"neutral and facing_left must differ in guide linework, got diff {diff}")

    def test_02_facing_left_right_mirror_symmetry(self):
        """facing_left must strictly match the horizontal mirror of facing_right."""
        W, H = 512, 512
        bounds = [100, 50, 300, 450]
        rx0, ry0, rx1, ry1 = bounds

        img_left = generate_single_character_guide_image(
            width=W, height=H, pixel_bounds=bounds,
            guide_style="mannequin_capsule",
            include_bbox_outline=False,
            shot_type="full_body",
            pose_preset="facing_left"
        )
        img_right = generate_single_character_guide_image(
            width=W, height=H, pixel_bounds=bounds,
            guide_style="mannequin_capsule",
            include_bbox_outline=False,
            shot_type="full_body",
            pose_preset="facing_right"
        )

        # Crop to the character box
        box_left = img_left[0, ry0:ry1, rx0:rx1, 0]
        box_right = img_right[0, ry0:ry1, rx0:rx1, 0]

        # Horizontally flip box_right
        box_right_flipped = torch.flip(box_right, dims=[1])

        # Tolerance: Allow minor integer rasterization rounding of <= 2 pixels
        diff = torch.abs(box_left - box_right_flipped).sum().item()
        total_pixels = box_left.numel()
        norm_diff = diff / total_pixels

        self.assertLess(norm_diff, 0.015, f"facing_left and facing_right must be mirror symmetric, norm_diff={norm_diff:.5f}")

    def test_03_sitting_bent_leg_spatial_density(self):
        """sitting pose must show distinct horizontal lap crossbar in lower-middle section."""
        W, H = 512, 512
        bounds = [100, 50, 300, 450]
        rx0, ry0, rx1, ry1 = bounds
        ch = ry1 - ry0

        img_standing = generate_single_character_guide_image(
            width=W, height=H, pixel_bounds=bounds,
            guide_style="mannequin_capsule",
            include_bbox_outline=False,
            shot_type="full_body",
            pose_preset="standing_neutral"
        )
        img_sitting = generate_single_character_guide_image(
            width=W, height=H, pixel_bounds=bounds,
            guide_style="mannequin_capsule",
            include_bbox_outline=False,
            shot_type="full_body",
            pose_preset="sitting"
        )

        # In sitting, knee/lap horizontal line is around y in [0.60..0.70] of the character box
        lap_y0 = ry0 + int(ch * 0.60)
        lap_y1 = ry0 + int(ch * 0.70)

        drawn_standing_lap = (img_standing[0, lap_y0:lap_y1, rx0:rx1, :] < 0.9).float().sum().item()
        drawn_sitting_lap = (img_sitting[0, lap_y0:lap_y1, rx0:rx1, :] < 0.9).float().sum().item()

        # The sitting lap horizontal crossbar must create substantially more drawn pixels across this horizontal band
        self.assertGreater(drawn_sitting_lap, drawn_standing_lap * 1.5,
                           f"Sitting pose should have higher drawn density at lap level: sitting={drawn_sitting_lap}, standing={drawn_standing_lap}")

    def test_04_shot_type_x_pose_preset_orthogonal_validity(self):
        """All 3 shot types x 4 pose presets must generate valid non-empty guide tensors."""
        W, H = 512, 512
        bounds = [100, 50, 300, 450]
        rx0, ry0, rx1, ry1 = bounds

        shot_types = ["full_body", "half_body", "bust"]
        pose_presets = ["standing_neutral", "facing_left", "facing_right", "sitting"]

        for st in shot_types:
            for pp in pose_presets:
                with self.subTest(shot_type=st, pose_preset=pp):
                    img = generate_single_character_guide_image(
                        width=W, height=H, pixel_bounds=bounds,
                        guide_style="mannequin_capsule",
                        include_bbox_outline=False,
                        shot_type=st,
                        pose_preset=pp
                    )
                    self.assertEqual(img.shape, (1, H, W, 3))
                    drawn_count = (img[0, ry0:ry1, rx0:rx1, :] < 0.9).float().sum().item()
                    self.assertGreater(drawn_count, 100, f"Empty guide generated for {st} x {pp}")

    def test_05_handshake_pair_interaction_guide(self):
        """Handshake pair interaction draws connecting arms between characters."""
        generator = TegakiMangaLayoutGuideGenerator()
        scene_plan = {
            "version": 1,
            "panel": {
                "id": 1,
                "geometry": {"x": 0.05, "y": 0.05, "w": 0.90, "h": 0.90}
            },
            "characters": [
                {
                    "character_id": "char_alice",
                    "name": "Alice",
                    "enabled": True,
                    "area": {"x": 0.10, "y": 0.15, "w": 0.35, "h": 0.75},
                    "shot_type": "full_body",
                    "pose_preset": "facing_right",
                    "interaction": {"type": "handshake", "role": "left_participant"}
                },
                {
                    "character_id": "char_bob",
                    "name": "Bob",
                    "enabled": True,
                    "area": {"x": 0.55, "y": 0.15, "w": 0.35, "h": 0.75},
                    "shot_type": "full_body",
                    "pose_preset": "facing_left",
                    "interaction": {"type": "handshake", "role": "right_participant"}
                }
            ]
        }

        # Generate guide with pair handshake
        guide_img_pair, mask_pair, debug_json = generator.generate_guide(
            scene_plan=scene_plan,
            target_panel_id=1,
            guide_style="mannequin_capsule",
            include_panel_border=False,
            include_character_bbox_outline=False,
            width=1024,
            height=1024
        )

        # In between Alice (right edge ~ x=0.45 * 0.9 + 0.05 = 0.455 * 1024 = 466)
        # and Bob (left edge ~ x=0.55 * 0.9 + 0.05 = 0.545 * 1024 = 558),
        # the midpoint anchor around x ~ 512, y ~ 500 must have drawn pixels!
        mid_x0, mid_x1 = 480, 544
        mid_y0, mid_y1 = 440, 560
        drawn_midpoint = (guide_img_pair[0, mid_y0:mid_y1, mid_x0:mid_x1, :] < 0.9).float().sum().item()
        self.assertGreater(drawn_midpoint, 50, "Shared handshake clasp anchor and arms should be drawn in the gap between characters")


if __name__ == "__main__":
    unittest.main()
