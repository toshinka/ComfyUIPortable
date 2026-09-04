"""
Generation Profile Unit Tests (Phase 3H)
========================================
Verifies:
1. Profiles "reference" and "fast_draft_12" are defined with valid fields.
2. Fast-8 is strictly excluded.
3. Unknown profiles raise KeyError.
4. apply_profile_to_prompt correctly updates steps, CFG, and injects LoraLoader.
"""

import unittest
import os
import sys

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CUSTOM_NODES_DIR = os.path.join(ROOT_DIR, "custom_nodes_custom")
if CUSTOM_NODES_DIR not in sys.path:
    sys.path.insert(0, CUSTOM_NODES_DIR)

from tegaki_manga_nodes.generation_profile import (
    get_profile,
    list_profiles,
    validate_generation_profile_name,
    apply_profile_to_prompt,
    PROFILES
)


class TestGenerationProfile(unittest.TestCase):

    def test_registered_profiles(self):
        profiles = list_profiles()
        names = [p["name"] for p in profiles]
        self.assertIn("reference", names)
        self.assertIn("fast_draft_12", names)
        self.assertNotIn("fast_8", names, "Fast-8 must not be in registered profiles")
        self.assertEqual(len(profiles), 2)

    def test_reference_profile_values(self):
        ref = get_profile("reference")
        self.assertEqual(ref["steps"], 20)
        self.assertEqual(ref["cfg"], 7.0)
        self.assertEqual(ref["sampler"], "euler")
        self.assertEqual(ref["scheduler"], "normal")
        self.assertIsNone(ref["lora_name"])

    def test_fast_draft_12_values(self):
        fast12 = get_profile("fast_draft_12")
        self.assertEqual(fast12["steps"], 12)
        self.assertEqual(fast12["cfg"], 6.0)
        self.assertEqual(fast12["sampler"], "euler")
        self.assertEqual(fast12["scheduler"], "normal")
        self.assertIsNotNone(fast12["lora_name"])
        self.assertIn("Hyper-SDXL-12steps", fast12["lora_name"])

    def test_invalid_profile_rejection(self):
        self.assertFalse(validate_generation_profile_name("fast_8"))
        self.assertFalse(validate_generation_profile_name("nonexistent"))
        with self.assertRaises(KeyError):
            get_profile("fast_8")

    def test_apply_reference_profile(self):
        mock_prompt = {
            "1": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": "test.safetensors"}},
            "2": {"class_type": "KSamplerAdvancedProvider", "inputs": {"cfg": 5.0, "sampler_name": "euler"}},
            "3": {"class_type": "RegionalSampler", "inputs": {"steps": 10, "base_only_steps": 1}}
        }
        res = apply_profile_to_prompt(mock_prompt, "reference")
        self.assertEqual(res["2"]["inputs"]["cfg"], 7.0)
        self.assertEqual(res["3"]["inputs"]["steps"], 20)
        self.assertEqual(res["3"]["inputs"]["base_only_steps"], 2)
        self.assertNotIn("profile_hypersd_lora", res)

    def test_apply_fast_draft_12_profile(self):
        mock_prompt = {
            "1": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": "test.safetensors"}},
            "2": {"class_type": "ToBasicPipe", "inputs": {"model": ["1", 0], "clip": ["1", 1]}},
            "3": {"class_type": "KSamplerAdvancedProvider", "inputs": {"cfg": 7.0}},
            "4": {"class_type": "RegionalSampler", "inputs": {"steps": 20, "base_only_steps": 2}}
        }
        res = apply_profile_to_prompt(mock_prompt, "fast_draft_12")
        self.assertIn("profile_hypersd_lora", res)
        lora_node = res["profile_hypersd_lora"]
        self.assertEqual(lora_node["class_type"], "LoraLoader")
        self.assertEqual(lora_node["inputs"]["model"], ["1", 0])
        self.assertEqual(lora_node["inputs"]["clip"], ["1", 1])
        # Check rewiring
        self.assertEqual(res["2"]["inputs"]["model"], ["profile_hypersd_lora", 0])
        self.assertEqual(res["2"]["inputs"]["clip"], ["profile_hypersd_lora", 1])
        # Check step & cfg updates
        self.assertEqual(res["3"]["inputs"]["cfg"], 6.0)
        self.assertEqual(res["4"]["inputs"]["steps"], 12)
        self.assertEqual(res["4"]["inputs"]["base_only_steps"], 2)


if __name__ == "__main__":
    unittest.main()
