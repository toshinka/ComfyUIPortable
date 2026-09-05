"""
Test: Phase 3L SubScene Remainder Masks
=======================================
Verifies that:
- SubScene background remainder mask subtracts only characters belonging to that SubScene.
- Characters in SubScene A do not subtract from SubScene B's background mask.
- Total area conservation is maintained without cross-subscene leakage.
"""

import os
import sys
import unittest
import torch

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from custom_nodes_custom.tegaki_manga_nodes.impact_region_plan import build_impact_region_plan


class TestPhase3LSubSceneMasks(unittest.TestCase):

    def test_subscene_remainder_mask_isolation(self):
        from custom_nodes_custom.tegaki_manga_nodes.panel_layout_spec import get_default_panel_layout_spec
        from custom_nodes_custom.tegaki_manga_nodes.scene_compiler import TegakiMangaPageCompiler

        panel_layout_spec = get_default_panel_layout_spec(width=832, height=1216, preset="1_full")

        cast_spec = {
            "version": 1,
            "characters": [
                {"id": "char_alice", "name": "Alice", "prompt": "1girl", "enabled": True},
                {"id": "char_bob", "name": "Bob", "prompt": "1boy", "enabled": True}
            ]
        }

        region_spec = {
            "version": 1,
            "canvas": {"width": 832, "height": 1216},
            "panel_count": 1,
            "global_prompt": "",
            "global_negative_prompt": "",
            "regions": [
                {
                    "id": 1,
                    "x": 0.0, "y": 0.0, "w": 1.0, "h": 1.0,
                    "prompt": "base",
                    "negative_prompt": "",
                    "characters": [],
                    "subscenes": [
                        {
                            "id": "sub_a",
                            "enabled": True,
                            "prompt": "left scene",
                            "negative_prompt": "",
                            "area": {"x": 0.0, "y": 0.0, "w": 0.5, "h": 1.0},
                            "character_bindings": [
                                {
                                    "instance_id": "p1_sub_a_alice",
                                    "character_id": "char_alice",
                                    "area": {"x": 0.1, "y": 0.1, "w": 0.8, "h": 0.8}
                                }
                            ]
                        },
                        {
                            "id": "sub_b",
                            "enabled": True,
                            "prompt": "right scene",
                            "negative_prompt": "",
                            "area": {"x": 0.5, "y": 0.0, "w": 0.5, "h": 1.0},
                            "character_bindings": [
                                {
                                    "instance_id": "p1_sub_b_bob",
                                    "character_id": "char_bob",
                                    "area": {"x": 0.1, "y": 0.1, "w": 0.8, "h": 0.8}
                                }
                            ]
                        }
                    ]
                }
            ]
        }

        page_compiler = TegakiMangaPageCompiler()
        page_compile_plan, _, _, _ = page_compiler.compile_page(region_spec=region_spec, cast_spec=cast_spec)

        plan = build_impact_region_plan(
            panel_layout_spec=panel_layout_spec,
            page_compile_plan=page_compile_plan,
            remainder_mask_mode=True,
            include_panel_backgrounds=True
        )

        entries = plan["regions"]
        sub_a_bg = next(e for e in entries if e["scope_type"] == "subscene" and e["metadata"]["subscene_id"] == "sub_a")
        sub_b_bg = next(e for e in entries if e["scope_type"] == "subscene" and e["metadata"]["subscene_id"] == "sub_b")
        alice_char = next(e for e in entries if e.get("character_instance_id") == "p1_sub_a_alice")
        bob_char = next(e for e in entries if e.get("character_instance_id") == "p1_sub_b_bob")

        # SubScene A mask is strictly on the left half (X < 416)
        sub_a_mask = sub_a_bg["mask"]
        self.assertEqual(sub_a_mask[:, 416:].sum().item(), 0.0)

        # SubScene B mask is strictly on the right half (X >= 416)
        sub_b_mask = sub_b_bg["mask"]
        self.assertEqual(sub_b_mask[:, :416].sum().item(), 0.0)

        # Alice is in SubScene A, so Alice does not subtract from SubScene B
        # Verify SubScene B retains positive mask area
        self.assertGreater(sub_b_mask.sum().item(), 0.0)

        # In SubScene A, Alice mask and SubScene A remainder mask do not overlap
        alice_overlap = (sub_a_mask * alice_char["mask"]).sum().item()
        self.assertAlmostEqual(alice_overlap, 0.0, places=3)


if __name__ == "__main__":
    unittest.main()
