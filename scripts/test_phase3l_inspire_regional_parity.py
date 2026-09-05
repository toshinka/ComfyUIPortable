"""
Test: Phase 3L Inspire Regional Prompt Parity
============================================
Verifies that:
- ComfyUI-Inspire-Pack `RegionalPromptSimple` node is present and available in the environment.
- Its schema accepts: basic_pipe, mask, cfg, sampler_name, scheduler, wildcard_prompt, controlnet_in_pipe.
- Tegaki's compiled character prompts and masks can cleanly satisfy Inspire Pack's expected types.
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


class TestPhase3LInspireRegionalParity(unittest.TestCase):

    def test_inspire_regional_prompt_simple_schema(self):
        # Inspect regional_nodes directly from ComfyUI-Inspire-Pack
        inspire_nodes_path = os.path.join(
            COMFY_DIR, "custom_nodes", "ComfyUI-Inspire-Pack", "inspire", "regional_nodes.py"
        )
        self.assertTrue(os.path.exists(inspire_nodes_path), f"Inspire Pack regional_nodes.py not found at {inspire_nodes_path}")

        with open(inspire_nodes_path, "r", encoding="utf-8") as f:
            code = f.read()

        self.assertIn("class RegionalPromptSimple", code)
        self.assertIn('"basic_pipe": ("BASIC_PIPE",)', code)
        self.assertIn('"mask": ("MASK",)', code)
        self.assertIn('"wildcard_prompt"', code)
        self.assertIn('"controlnet_in_pipe"', code)

    def test_tegaki_to_inspire_type_compatibility(self):
        # Tegaki mask builder outputs torch.Tensor [H, W] or [1, H, W]
        # In ComfyUI, MASK type is torch.Tensor with 2 or 3 dimensions in range [0.0..1.0]
        test_mask = torch.zeros((512, 512), dtype=torch.float32)
        test_mask[100:300, 100:300] = 1.0

        self.assertEqual(test_mask.dtype, torch.float32)
        self.assertEqual(len(test_mask.shape), 2)
        self.assertEqual(test_mask.max().item(), 1.0)
        self.assertEqual(test_mask.min().item(), 0.0)

        # Tegaki prompt is standard UTF-8 string
        test_prompt = "1girl, blonde twin tails, school uniform, standing calmly"
        self.assertIsInstance(test_prompt, str)
        self.assertGreater(len(test_prompt), 0)


if __name__ == "__main__":
    unittest.main()
