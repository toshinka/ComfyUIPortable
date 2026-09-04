"""
Test Cast Binding References & Appearance Derivation (Phase 3D.1-B)
===================================================================
Tests referencing validation:
- Deleting an unreferenced character succeeds
- Deleting a character referenced in active KOMA bindings is blocked (Fail-Closed)
- Derived appearances accurately list KOMA IDs for each character
- Disabled characters in CAST_SPEC are safely skipped by TegakiMangaPageCompiler
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
    delete_character,
    get_character_appearances
)
from tegaki_manga_nodes.scene_compiler import TegakiMangaPageCompiler


class TestCastBindingReferences(unittest.TestCase):

    def setUp(self):
        self.cast_spec = get_default_cast_spec()
        self.compiler = TegakiMangaPageCompiler()
        # Region Spec with Alice in KOMA 1, KOMA 2 and Bob in KOMA 1, KOMA 3
        self.region_spec = {
            "version": 1,
            "canvas": {"width": 832, "height": 1216},
            "panel_count": 3,
            "global_prompt": "manga page, monochrome",
            "global_negative_prompt": "bad anatomy",
            "regions": [
                {
                    "id": 1, "name": "KOMA 1", "enabled": True,
                    "x": 0.05, "y": 0.05, "w": 0.90, "h": 0.40,
                    "prompt": "classroom conversation",
                    "negative_prompt": "",
                    "characters": [
                        {"character_id": "char_alice", "enabled": True, "prompt_override": "smiling"},
                        {"character_id": "char_bob", "enabled": True, "prompt_override": "laughing"}
                    ]
                },
                {
                    "id": 2, "name": "KOMA 2", "enabled": True,
                    "x": 0.05, "y": 0.45, "w": 0.45, "h": 0.50,
                    "prompt": "corridor walk",
                    "negative_prompt": "",
                    "characters": [
                        {"character_id": "char_alice", "enabled": True, "prompt_override": "walking"}
                    ]
                },
                {
                    "id": 3, "name": "KOMA 3", "enabled": True,
                    "x": 0.50, "y": 0.45, "w": 0.45, "h": 0.50,
                    "prompt": "sunset yard",
                    "negative_prompt": "",
                    "characters": [
                        {"character_id": "char_bob", "enabled": True, "prompt_override": "standing"}
                    ]
                }
            ]
        }

    def test_01_derived_appearances_mapping(self):
        """Appearances should map char_alice -> [1, 2], char_bob -> [1, 3]."""
        apps = get_character_appearances(self.cast_spec, self.region_spec)
        self.assertEqual(apps.get("char_alice"), [1, 2])
        self.assertEqual(apps.get("char_bob"), [1, 3])

    def test_02_delete_referenced_character_blocked(self):
        """Attempting to delete char_alice when bound in KOMA 1/2 must raise ValueError."""
        with self.assertRaises(ValueError) as ctx:
            delete_character(self.cast_spec, "char_alice", region_spec=self.region_spec)
        self.assertIn("referenced in active KOMA bindings", str(ctx.exception))
        self.assertIn("char_alice", str(ctx.exception))

    def test_03_delete_unreferenced_character_allowed(self):
        """Adding Charlie (unreferenced) and then deleting Charlie should succeed."""
        updated, cid = add_character(self.cast_spec, name="Charlie")
        self.assertEqual(len(updated["characters"]), 3)

        apps = get_character_appearances(updated, self.region_spec)
        self.assertEqual(apps.get(cid), [])

        after_del = delete_character(updated, cid, region_spec=self.region_spec)
        self.assertEqual(len(after_del["characters"]), 2)
        remaining_ids = [c["id"] for c in after_del["characters"]]
        self.assertNotIn(cid, remaining_ids)

    def test_04_disabled_character_in_compiler(self):
        """Disabling Alice in CAST_SPEC causes compiler to safely skip her without error."""
        cast_copy = json.loads(json.dumps(self.cast_spec))
        cast_copy["characters"][0]["enabled"] = False  # disable Alice

        plan, plan_json, _, _ = self.compiler.compile_page(
            region_spec=self.region_spec,
            cast_spec=cast_copy
        )

        koma1 = plan["panels"][0]
        # In KOMA 1, Alice was disabled, so only Bob should be compiled into characters
        compiled_cids = [c["character_id"] for c in koma1["characters"]]
        self.assertNotIn("char_alice", compiled_cids)
        self.assertIn("char_bob", compiled_cids)


if __name__ == "__main__":
    unittest.main()
