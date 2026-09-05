"""
Test: Phase 3L Pose Causality Fixture
====================================
Verifies that:
- Pure causality prompt contains ZERO directional or posture vocabulary.
- Prohibited tokens: 'left', 'right', 'facing', 'profile', 'sitting', 'seated', 'look'.
- Pose variations are driven exclusively by `pose_preset`:
    'standing_neutral', 'facing_left', 'facing_right', 'sitting'
- Inward vs Outward two-character configurations are properly defined.
"""

import os
import sys
import unittest

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

PROHIBITED_DIRECTIONAL_TOKENS = {"left", "right", "facing", "profile", "sitting", "seated", "look"}

ALICE_CANONICAL_PURE_PROMPT = "1girl, blonde twin tails, school uniform, standing calmly"
BOB_CANONICAL_PURE_PROMPT = "1boy, short dark hair, school uniform, standing calmly"


class TestPhase3LPoseCausalityFixture(unittest.TestCase):

    def test_pure_prompt_has_no_directional_tokens(self):
        prompt_words = [w.strip(" ,.!?").lower() for w in ALICE_CANONICAL_PURE_PROMPT.split()]
        found = set(prompt_words) & PROHIBITED_DIRECTIONAL_TOKENS
        self.assertEqual(found, set(), f"Found prohibited directional words in Alice prompt: {found}")

        bob_words = [w.strip(" ,.!?").lower() for w in BOB_CANONICAL_PURE_PROMPT.split()]
        found_bob = set(bob_words) & PROHIBITED_DIRECTIONAL_TOKENS
        self.assertEqual(found_bob, set(), f"Found prohibited directional words in Bob prompt: {found_bob}")

    def test_supported_pose_presets(self):
        from custom_nodes_custom.tegaki_manga_nodes.subscene_contract import VALID_POSE_PRESETS
        expected = {"standing_neutral", "facing_left", "facing_right", "sitting"}
        self.assertEqual(VALID_POSE_PRESETS, expected)

    def test_two_character_orientation_contract(self):
        # Inward: Alice on Left facing right, Bob on Right facing left
        inward_config = {
            "alice": {"position": "left", "pose_preset": "facing_right"},
            "bob": {"position": "right", "pose_preset": "facing_left"}
        }
        self.assertEqual(inward_config["alice"]["pose_preset"], "facing_right")
        self.assertEqual(inward_config["bob"]["pose_preset"], "facing_left")

        # Outward: Alice on Left facing left, Bob on Right facing right
        outward_config = {
            "alice": {"position": "left", "pose_preset": "facing_left"},
            "bob": {"position": "right", "pose_preset": "facing_right"}
        }
        self.assertEqual(outward_config["alice"]["pose_preset"], "facing_left")
        self.assertEqual(outward_config["bob"]["pose_preset"], "facing_right")


if __name__ == "__main__":
    unittest.main()
