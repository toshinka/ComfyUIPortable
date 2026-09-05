"""
Test: Phase 3L Interaction Contract
===================================
Verifies that:
- normalize_interaction accepts legacy string ('handshake') and produces canonical dict.
- normalize_interaction accepts structured dict.
- Canonical dict contains: interaction_id, type, role, target_instance_id.
- Rejects non-string/non-dict inputs and invalid type fields.
"""

import os
import sys
import unittest

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from custom_nodes_custom.tegaki_manga_nodes.interaction_resolver import normalize_interaction


class TestPhase3LInteractionContract(unittest.TestCase):

    def test_legacy_string_normalization(self):
        canon = normalize_interaction("handshake", source_instance_id="p1_alice_01")
        self.assertIsNotNone(canon)
        self.assertEqual(canon["type"], "handshake")
        self.assertEqual(canon["interaction_id"], "int_p1_alice_01")
        self.assertEqual(canon["role"], "mutual")
        self.assertIsNone(canon["target_instance_id"])

    def test_canonical_dict_pass_through(self):
        raw = {
            "interaction_id": "int_p1_01",
            "type": "handshake",
            "role": "left_participant",
            "target_instance_id": "p1_bob_01"
        }
        canon = normalize_interaction(raw)
        self.assertEqual(canon["interaction_id"], "int_p1_01")
        self.assertEqual(canon["type"], "handshake")
        self.assertEqual(canon["role"], "left_participant")
        self.assertEqual(canon["target_instance_id"], "p1_bob_01")

    def test_none_or_empty_returns_none(self):
        self.assertIsNone(normalize_interaction(None))
        self.assertIsNone(normalize_interaction(""))
        self.assertIsNone(normalize_interaction("   "))

    def test_reject_invalid_data_types(self):
        with self.assertRaises(ValueError):
            normalize_interaction(123)

        with self.assertRaises(ValueError):
            normalize_interaction(["handshake"])

    def test_reject_empty_dict_type(self):
        with self.assertRaises(ValueError):
            normalize_interaction({"type": ""})


if __name__ == "__main__":
    unittest.main()
