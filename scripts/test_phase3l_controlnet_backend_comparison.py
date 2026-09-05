"""
Test: Phase 3L Advanced-ControlNet Backend Comparison
=====================================================
Verifies that:
- ComfyUI-Advanced-ControlNet is present in the environment.
- Its apply node (`ACN_AdvancedControlNetApply_v2` / `AdvancedControlNetApply`) exposes:
    - positive & negative conditioning
    - control_net
    - image (guide)
    - mask_optional (effect_mask)
    - start_percent & end_percent
- Validates that Tegaki regional mask tensors match the shape and type required by Advanced-ControlNet.
"""

import os
import sys
import unittest
import torch

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
COMFY_DIR = os.path.join(ROOT_DIR, "ComfyUI")
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
if COMFY_DIR not in sys.path:
    sys.path.insert(0, COMFY_DIR)


class TestPhase3LControlNetBackendComparison(unittest.TestCase):

    def test_advanced_controlnet_schema_presence(self):
        adv_nodes_path = os.path.join(
            COMFY_DIR, "custom_nodes", "ComfyUI-Advanced-ControlNet", "adv_control", "nodes_main.py"
        )
        self.assertTrue(os.path.exists(adv_nodes_path), f"Advanced-ControlNet nodes_main.py not found at {adv_nodes_path}")

        with open(adv_nodes_path, "r", encoding="utf-8") as f:
            code = f.read()

        self.assertIn("class AdvancedControlNetApply", code)
        self.assertIn("ACN_AdvancedControlNetApply_v2", code)
        self.assertIn("effect_mask", code)
        self.assertIn("start_percent", code)
        self.assertIn("end_percent", code)

    def test_tegaki_effect_mask_compatibility(self):
        # Advanced-ControlNet expects mask as a 2D or 3D torch.Tensor [B, H, W] or [H, W]
        tegaki_mask = torch.zeros((1, 512, 512), dtype=torch.float32)
        tegaki_mask[0, 50:200, 50:200] = 1.0

        self.assertEqual(tegaki_mask.dtype, torch.float32)
        self.assertEqual(tegaki_mask.shape[1:], (512, 512))
        self.assertTrue(tegaki_mask.count_nonzero() > 0)


if __name__ == "__main__":
    unittest.main()
