"""
Test Cast Master State Transitions (Phase 3D.1-B)
=================================================
Unit tests for TegakiMangaCastMaster state operations:
- Default spec generation
- Character addition & unique stable ID generation
- Attribute update with ID immutability
- Enable/disable toggling
- Unused character deletion
- Duplicate ID rejection
- Spec JSON serialization and roundtrip reload
"""

import os
import sys
import json
import unittest

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CUSTOM_NODES_DIR = os.path.join(ROOT_DIR, "custom_nodes_custom")
if CUSTOM_NODES_DIR not in sys.path:
    sys.path.insert(0, CUSTOM_NODES_DIR)

from tegaki_manga_nodes.cast_master import (
    get_default_cast_spec,
    add_character,
    update_character,
    delete_character,
    TegakiMangaCastMaster
)


class TestCastMasterState(unittest.TestCase):

    def setUp(self):
        self.spec = get_default_cast_spec()

    def test_01_default_spec_has_alice_and_bob(self):
        """Default spec should have exactly Alice and Bob with valid version 1."""
        self.assertEqual(self.spec.get("version"), 1)
        chars = self.spec.get("characters", [])
        self.assertEqual(len(chars), 2)
        ids = [c["id"] for c in chars]
        self.assertIn("char_alice", ids)
        self.assertIn("char_bob", ids)

    def test_02_add_character_generates_stable_unique_id(self):
        """Adding a character should generate a unique stable ID."""
        spec1, cid1 = add_character(self.spec, name="Charlie", prompt="1boy, black hair")
        self.assertEqual(len(spec1["characters"]), 3)
        self.assertTrue(cid1.startswith("char_charlie"))

        spec2, cid2 = add_character(spec1, name="Charlie", prompt="another charlie")
        self.assertEqual(len(spec2["characters"]), 4)
        self.assertNotEqual(cid1, cid2)
        self.assertTrue(cid2.startswith("char_charlie"))

    def test_03_rename_preserves_immutable_id(self):
        """Renaming a character must not change its unique ID."""
        orig_id = "char_alice"
        updated = update_character(self.spec, orig_id, name="Alicia Liddell")
        char = [c for c in updated["characters"] if c["id"] == orig_id][0]
        self.assertEqual(char["name"], "Alicia Liddell")
        self.assertEqual(char["id"], orig_id)

    def test_04_edit_prompt_and_negative(self):
        """Prompt and negative prompt updates should persist correctly."""
        updated = update_character(
            self.spec,
            "char_alice",
            prompt="1girl, vibrant cyan hair",
            negative_prompt="monochrome, deformed"
        )
        char = [c for c in updated["characters"] if c["id"] == "char_alice"][0]
        self.assertEqual(char["prompt"], "1girl, vibrant cyan hair")
        self.assertEqual(char["negative_prompt"], "monochrome, deformed")

    def test_05_enable_disable_toggle(self):
        """Enabling/disabling character works with strict boolean."""
        updated = update_character(self.spec, "char_bob", enabled=False)
        bob = [c for c in updated["characters"] if c["id"] == "char_bob"][0]
        self.assertFalse(bob["enabled"])

        restored = update_character(updated, "char_bob", enabled=True)
        bob_restored = [c for c in restored["characters"] if c["id"] == "char_bob"][0]
        self.assertTrue(bob_restored["enabled"])

    def test_06_delete_unused_character(self):
        """Unused character can be deleted cleanly."""
        updated = delete_character(self.spec, "char_bob")
        chars = updated["characters"]
        self.assertEqual(len(chars), 1)
        self.assertEqual(chars[0]["id"], "char_alice")

    def test_07_duplicate_id_rejected(self):
        """Specifying an explicit ID that already exists must raise ValueError."""
        with self.assertRaises(ValueError) as ctx:
            add_character(self.spec, name="Fake Alice", char_id="char_alice")
        self.assertIn("Duplicate character ID", str(ctx.exception))

    def test_08_node_process_serialization_roundtrip(self):
        """TegakiMangaCastMaster node execution serializes and parses properly."""
        node = TegakiMangaCastMaster()
        spec_out, json_out, first_id, count = node.process(json.dumps(self.spec))
        self.assertEqual(count, 2)
        self.assertEqual(first_id, "char_alice")
        reloaded = json.loads(json_out)
        self.assertEqual(reloaded["version"], 1)
        self.assertEqual(len(reloaded["characters"]), 2)


if __name__ == "__main__":
    unittest.main()
