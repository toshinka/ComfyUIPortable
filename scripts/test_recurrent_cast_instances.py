"""
Unit test for Recurrent Cast Instances (Phase 3E)
=================================================
Verifies that:
1. Alice master is a single immutable definition in CAST_SPEC.
2. Bob master is a single immutable definition in CAST_SPEC.
3. Multiple character instances across panels correctly reference the single master ID.
4. Alice attends Panels 1, 2, 4 and is ABSENT from Panel 3.
5. Bob attends Panels 1, 3, 4 and is ABSENT from Panel 2.
6. Panel-specific acting overrides are preserved per instance without mutating master character.
"""

import os
import sys
import unittest
import copy

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "custom_nodes_custom")))

from tegaki_manga_nodes.cast_master import get_default_cast_spec, validate_cast_spec
from tegaki_manga_nodes.impact_region_plan import build_impact_region_plan
from scripts.test_impact_n_region_plan import make_test_fixture


class TestRecurrentCastInstances(unittest.TestCase):
    def setUp(self):
        self.cast_spec = get_default_cast_spec()
        self.compile_plan, self.layout_spec = make_test_fixture(4)

    def test_single_master_definitions(self):
        chars = self.cast_spec["characters"]
        alice_masters = [c for c in chars if c["id"] == "char_alice"]
        bob_masters = [c for c in chars if c["id"] == "char_bob"]

        self.assertEqual(len(alice_masters), 1, "There must be exactly ONE Alice master in CAST_SPEC")
        self.assertEqual(len(bob_masters), 1, "There must be exactly ONE Bob master in CAST_SPEC")

    def test_recurrent_panel_attendance(self):
        original_cast = copy.deepcopy(self.cast_spec)
        plan = build_impact_region_plan(self.compile_plan, self.layout_spec)

        char_regions = [r for r in plan["regions"] if r["scope_type"] == "character_instance"]

        # Panel 1: Alice + Bob
        p1_chars = [r["master_character_id"] for r in char_regions if r["source_panel_id"] == "1"]
        self.assertIn("char_alice", p1_chars)
        self.assertIn("char_bob", p1_chars)

        # Panel 2: Alice ONLY
        p2_chars = [r["master_character_id"] for r in char_regions if r["source_panel_id"] == "2"]
        self.assertIn("char_alice", p2_chars)
        self.assertNotIn("char_bob", p2_chars, "Bob must NOT appear in Panel 2")

        # Panel 3: Bob ONLY
        p3_chars = [r["master_character_id"] for r in char_regions if r["source_panel_id"] == "3"]
        self.assertIn("char_bob", p3_chars)
        self.assertNotIn("char_alice", p3_chars, "Alice must NOT appear in Panel 3")

        # Panel 4: Alice + Bob
        p4_chars = [r["master_character_id"] for r in char_regions if r["source_panel_id"] == "4"]
        self.assertIn("char_alice", p4_chars)
        self.assertIn("char_bob", p4_chars)

        # Master CAST_SPEC must not have been mutated
        self.assertEqual(self.cast_spec, original_cast)

    def test_panel_specific_acting_isolation(self):
        plan = build_impact_region_plan(self.compile_plan, self.layout_spec, character_prompt_mode="scene_composed")

        char_regions = [r for r in plan["regions"] if r["scope_type"] == "character_instance"]

        alice_p1 = next(r for r in char_regions if r["master_character_id"] == "char_alice" and r["source_panel_id"] == "1")
        alice_p2 = next(r for r in char_regions if r["master_character_id"] == "char_alice" and r["source_panel_id"] == "2")
        alice_p4 = next(r for r in char_regions if r["master_character_id"] == "char_alice" and r["source_panel_id"] == "4")

        # Panel 1 Alice has handshake / smiling acting
        self.assertIn("smiling", alice_p1["prompt"])
        self.assertIn("handshake", alice_p1["prompt"])

        # Panel 2 Alice has watering flowers acting
        self.assertIn("watering flowers", alice_p2["prompt"])

        # Panel 4 Alice has arguing / looking away acting
        self.assertIn("looking away", alice_p4["prompt"])
        self.assertIn("angry", alice_p4["prompt"])

        # Overrides do not leak across panels
        self.assertNotIn("watering flowers", alice_p1["prompt"])
        self.assertNotIn("watering flowers", alice_p4["prompt"])


if __name__ == "__main__":
    unittest.main()
