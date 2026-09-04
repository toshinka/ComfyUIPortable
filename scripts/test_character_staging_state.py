"""
Unit Test: Character Staging State Management (Phase 3G)
========================================================
Verifies:
- Panel selection and dynamic attending character inspection
- Character selection within panel
- Move with clamping [0.0, 1.0 - w]
- Resize with clamping [min_size, 1.0 - x]
- Semantic overlap allowed
- Save / reload state serialization parity
- Unknown / non-attending character rejection
- Non-attending characters hidden from active list
"""

import os
import sys
import json
import unittest

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from custom_nodes_custom.tegaki_manga_nodes.character_staging_editor import CharacterStagingStateManager


class TestCharacterStagingState(unittest.TestCase):
    def setUp(self):
        self.mock_region_spec = {
            "version": 1,
            "canvas": {"width": 1024, "height": 1024},
            "panel_count": 4,
            "regions": [
                {
                    "id": 1,
                    "name": "Panel 1",
                    "enabled": True,
                    "characters": [
                        {
                            "character_id": "char_alice",
                            "enabled": True,
                            "area": {"x": 0.1, "y": 0.15, "w": 0.4, "h": 0.75}
                        },
                        {
                            "character_id": "char_bob",
                            "enabled": True,
                            "area": {"x": 0.5, "y": 0.15, "w": 0.4, "h": 0.75}
                        }
                    ]
                },
                {
                    "id": 2,
                    "name": "Panel 2",
                    "enabled": True,
                    "characters": [
                        {
                            "character_id": "char_alice",
                            "enabled": True,
                            "area": {"x": 0.2, "y": 0.2, "w": 0.6, "h": 0.7}
                        },
                        {
                            "character_id": "char_bob",
                            "enabled": False,  # Non-attending in Panel 2
                            "area": {"x": 0.5, "y": 0.15, "w": 0.4, "h": 0.75}
                        }
                    ]
                }
            ]
        }

    def test_panel_and_attending_characters(self):
        mgr = CharacterStagingStateManager(self.mock_region_spec)
        # Panel 1 has both Alice and Bob
        mgr.select_panel(1)
        attending_p1 = mgr.get_attending_characters(1)
        char_ids_p1 = [c["character_id"] for c in attending_p1]
        self.assertIn("char_alice", char_ids_p1)
        self.assertIn("char_bob", char_ids_p1)

        # Panel 2 only has Alice attending (Bob is disabled)
        mgr.select_panel(2)
        attending_p2 = mgr.get_attending_characters(2)
        char_ids_p2 = [c["character_id"] for c in attending_p2]
        self.assertIn("char_alice", char_ids_p2)
        self.assertNotIn("char_bob", char_ids_p2)

    def test_character_selection_and_unknown_reject(self):
        mgr = CharacterStagingStateManager(self.mock_region_spec)
        mgr.select_panel(1)
        mgr.select_character("char_bob")
        self.assertEqual(mgr.selected_char_id, "char_bob")

        # In Panel 2, Bob is non-attending -> select_character must raise ValueError
        mgr.select_panel(2)
        with self.assertRaises(ValueError):
            mgr.select_character("char_bob")

        # Unknown character ID
        with self.assertRaises(ValueError):
            mgr.select_character("char_unknown_charlie")

    def test_move_and_clamping(self):
        mgr = CharacterStagingStateManager(self.mock_region_spec)
        # Alice initial: x=0.1, y=0.15, w=0.4, h=0.75
        # Move within bounds: dx=+0.1, dy=+0.05 -> x=0.2, y=0.20
        area = mgr.move_character(1, "char_alice", 0.1, 0.05)
        self.assertAlmostEqual(area["x"], 0.2, places=3)
        self.assertAlmostEqual(area["y"], 0.2, places=3)

        # Move beyond right edge: dx=+1.0 -> should clamp to 1.0 - w = 0.6
        area = mgr.move_character(1, "char_alice", 1.0, 0.0)
        self.assertAlmostEqual(area["x"], 0.6, places=3)

        # Move beyond top edge: dy=-1.0 -> should clamp to 0.0
        area = mgr.move_character(1, "char_alice", 0.0, -1.0)
        self.assertAlmostEqual(area["y"], 0.0, places=3)

    def test_resize_and_clamping(self):
        mgr = CharacterStagingStateManager(self.mock_region_spec)
        # Alice initial: x=0.1, y=0.15, w=0.4, h=0.75
        # Resize: dw=+0.2, dh=-0.1 -> w=0.6, h=0.65
        area = mgr.resize_character(1, "char_alice", 0.2, -0.1)
        self.assertAlmostEqual(area["w"], 0.6, places=3)
        self.assertAlmostEqual(area["h"], 0.65, places=3)

        # Resize beyond canvas width: dw=+2.0 -> should clamp to 1.0 - x = 0.9
        area = mgr.resize_character(1, "char_alice", 2.0, 0.0)
        self.assertAlmostEqual(area["w"], 0.9, places=3)

        # Resize below minimum size (min_size=0.05)
        area = mgr.resize_character(1, "char_alice", -2.0, -2.0)
        self.assertAlmostEqual(area["w"], 0.05, places=3)
        self.assertAlmostEqual(area["h"], 0.05, places=3)

    def test_overlap_allowed(self):
        mgr = CharacterStagingStateManager(self.mock_region_spec)
        # In Panel 1, move Alice and Bob to heavily overlapping positions
        area_a = mgr.move_character(1, "char_alice", 0.2, 0.0) # x=0.3, w=0.4 (extends to 0.7)
        area_b = mgr.move_character(1, "char_bob", -0.1, 0.0)  # x=0.4, w=0.4 (extends from 0.4 to 0.8)
        # Check overlap is permitted without raising error
        self.assertTrue(area_a["x"] < area_b["x"] + area_b["w"])
        self.assertTrue(area_b["x"] < area_a["x"] + area_a["w"])

    def test_save_and_reload_state(self):
        mgr1 = CharacterStagingStateManager(self.mock_region_spec)
        mgr1.move_character(1, "char_alice", 0.15, 0.1)
        mgr1.resize_character(1, "char_bob", 0.05, -0.05)
        serialized = mgr1.serialize_overrides()

        # Parse serialized JSON into new manager instance
        loaded_overrides = json.loads(serialized)
        mgr2 = CharacterStagingStateManager(self.mock_region_spec, loaded_overrides)
        area_a2 = mgr2.get_character_area(1, "char_alice")
        area_b2 = mgr2.get_character_area(1, "char_bob")

        self.assertAlmostEqual(area_a2["x"], 0.25, places=3)
        self.assertAlmostEqual(area_a2["y"], 0.25, places=3)
        self.assertAlmostEqual(area_b2["w"], 0.45, places=3)
        self.assertAlmostEqual(area_b2["h"], 0.70, places=3)

        # Verify application to region_spec
        applied_spec = mgr2.apply_to_region_spec()
        applied_alice = applied_spec["regions"][0]["characters"][0]
        self.assertAlmostEqual(applied_alice["area"]["x"], 0.25, places=3)


if __name__ == "__main__":
    unittest.main()
