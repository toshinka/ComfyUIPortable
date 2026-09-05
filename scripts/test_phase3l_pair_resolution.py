"""
Test: Phase 3L Pair Resolution
==============================
Verifies pure logic in `resolve_interaction_pairs(...)`:
- Valid target successfully resolves mutual/directional pairs.
- Missing target rejected with ValueError.
- Self target rejected with ValueError.
- Cross-panel target rejected with ValueError.
- Duplicate role (e.g. both claiming 'left_participant') rejected with ValueError.
- More than 2 participants in a single pair rejected with ValueError.
"""

import os
import sys
import unittest

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from custom_nodes_custom.tegaki_manga_nodes.interaction_resolver import resolve_interaction_pairs


class TestPhase3LPairResolution(unittest.TestCase):

    def test_valid_pair_resolution(self):
        instances = [
            {
                "instance_id": "p1_alice_01",
                "panel_id": 1,
                "interaction": {
                    "interaction_id": "int_p1_01",
                    "type": "handshake",
                    "role": "left_participant",
                    "target_instance_id": "p1_bob_01"
                }
            },
            {
                "instance_id": "p1_bob_01",
                "panel_id": 1,
                "interaction": {
                    "interaction_id": "int_p1_01",
                    "type": "handshake",
                    "role": "right_participant",
                    "target_instance_id": "p1_alice_01"
                }
            }
        ]
        pairs = resolve_interaction_pairs(instances, panel_id=1)
        self.assertEqual(len(pairs), 1)
        p = pairs[0]
        self.assertEqual(p["interaction_id"], "int_p1_01")
        self.assertEqual(p["type"], "handshake")
        self.assertEqual(set(p["participants"]), {"p1_alice_01", "p1_bob_01"})
        self.assertEqual(p["participant_roles"]["p1_alice_01"], "left_participant")
        self.assertEqual(p["participant_roles"]["p1_bob_01"], "right_participant")

    def test_reject_missing_target(self):
        instances = [
            {
                "instance_id": "p1_alice_01",
                "panel_id": 1,
                "interaction": {
                    "interaction_id": "int_p1_01",
                    "type": "handshake",
                    "role": "left_participant",
                    "target_instance_id": "p1_ghost_target"  # Missing!
                }
            }
        ]
        with self.assertRaises(ValueError) as ctx:
            resolve_interaction_pairs(instances, panel_id=1)
        self.assertIn("Missing interaction target", str(ctx.exception))

    def test_reject_self_target(self):
        instances = [
            {
                "instance_id": "p1_alice_01",
                "panel_id": 1,
                "interaction": {
                    "interaction_id": "int_p1_01",
                    "type": "handshake",
                    "role": "left_participant",
                    "target_instance_id": "p1_alice_01"  # Self!
                }
            }
        ]
        with self.assertRaises(ValueError) as ctx:
            resolve_interaction_pairs(instances, panel_id=1)
        self.assertIn("Self-targeting", str(ctx.exception))

    def test_reject_cross_panel_target(self):
        instances = [
            {
                "instance_id": "p1_alice_01",
                "panel_id": 1,
                "interaction": {
                    "interaction_id": "int_p1_01",
                    "type": "handshake",
                    "role": "left_participant",
                    "target_instance_id": "p2_bob_01"
                }
            },
            {
                "instance_id": "p2_bob_01",
                "panel_id": 2,  # Cross panel!
                "interaction": {
                    "interaction_id": "int_p1_01",
                    "type": "handshake",
                    "role": "right_participant",
                    "target_instance_id": "p1_alice_01"
                }
            }
        ]
        with self.assertRaises(ValueError) as ctx:
            resolve_interaction_pairs(instances)
        self.assertIn("Cross-panel", str(ctx.exception))

    def test_reject_duplicate_roles(self):
        instances = [
            {
                "instance_id": "p1_alice_01",
                "panel_id": 1,
                "interaction": {
                    "interaction_id": "int_p1_01",
                    "type": "handshake",
                    "role": "left_participant",
                    "target_instance_id": "p1_bob_01"
                }
            },
            {
                "instance_id": "p1_bob_01",
                "panel_id": 1,
                "interaction": {
                    "interaction_id": "int_p1_01",
                    "type": "handshake",
                    "role": "left_participant",  # Duplicate role!
                    "target_instance_id": "p1_alice_01"
                }
            }
        ]
        with self.assertRaises(ValueError) as ctx:
            resolve_interaction_pairs(instances, panel_id=1)
        self.assertIn("Duplicate role", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
