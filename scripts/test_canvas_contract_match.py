"""
Test Canvas Contract Match (Phase 3D.1-A)
=========================================
Tests Fail-Closed enforcement of canvas dimension parity between
PAGE_COMPILE_PLAN and PANEL_LAYOUT_SPEC in layout_region_bridge.py.
"""

import os
import sys
import unittest

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CUSTOM_NODES_DIR = os.path.join(ROOT_DIR, "custom_nodes_custom")
if CUSTOM_NODES_DIR not in sys.path:
    sys.path.insert(0, CUSTOM_NODES_DIR)

from tegaki_manga_nodes.panel_layout_spec import get_default_panel_layout_spec
from tegaki_manga_nodes.scene_compiler import TegakiMangaPageCompiler
from tegaki_manga_nodes.layout_region_bridge import build_panel_content_bridge


class TestCanvasContractMatch(unittest.TestCase):

    def setUp(self):
        self.compiler = TegakiMangaPageCompiler()

    def _create_region_spec(self, w: int, h: int, panel_count: int = 3):
        return {
            "version": 1,
            "canvas": {"width": w, "height": h},
            "panel_count": panel_count,
            "global_prompt": "manga, monochrome",
            "global_negative_prompt": "bad anatomy",
            "regions": [
                {
                    "id": 1, "name": "KOMA 1", "enabled": True,
                    "x": 0.05, "y": 0.05, "w": 0.90, "h": 0.40,
                    "prompt": "panel 1 scene", "negative_prompt": "",
                    "characters": []
                },
                {
                    "id": 2, "name": "KOMA 2", "enabled": True,
                    "x": 0.05, "y": 0.45, "w": 0.45, "h": 0.50,
                    "prompt": "panel 2 scene", "negative_prompt": "",
                    "characters": []
                },
                {
                    "id": 3, "name": "KOMA 3", "enabled": True,
                    "x": 0.50, "y": 0.45, "w": 0.45, "h": 0.50,
                    "prompt": "panel 3 scene", "negative_prompt": "",
                    "characters": []
                }
            ]
        }

    def test_01_matching_canvas_passes(self):
        """Plan (832x1216) and Layout (832x1216) should validate cleanly."""
        reg_spec = self._create_region_spec(832, 1216, 3)
        plan, _, _, _ = self.compiler.compile_page(region_spec=reg_spec)
        layout = get_default_panel_layout_spec(832, 1216, preset="3_basic")

        bridge = build_panel_content_bridge(plan, layout)
        self.assertIn("mapped_panels", bridge)
        self.assertEqual(len(bridge["mapped_panels"]), 3)
        self.assertEqual(bridge["panel_content_map"], {"1": "p1", "2": "p2", "3": "p3"})

    def test_02_dimension_mismatch_raises_value_error(self):
        """Plan (832x1216) vs Layout (1024x1024) must raise ValueError."""
        reg_spec = self._create_region_spec(832, 1216, 3)
        plan, _, _, _ = self.compiler.compile_page(region_spec=reg_spec)
        layout = get_default_panel_layout_spec(1024, 1024, preset="3_basic")

        with self.assertRaises(ValueError) as ctx:
            build_panel_content_bridge(plan, layout)
        self.assertIn("Canvas dimension mismatch", str(ctx.exception))
        self.assertIn("832x1216", str(ctx.exception))
        self.assertIn("1024x1024", str(ctx.exception))

    def test_03_width_mismatch_raises_value_error(self):
        """Plan (832x1216) vs Layout (768x1216) must raise ValueError."""
        reg_spec = self._create_region_spec(832, 1216, 3)
        plan, _, _, _ = self.compiler.compile_page(region_spec=reg_spec)
        layout = get_default_panel_layout_spec(768, 1216, preset="3_basic")

        with self.assertRaises(ValueError) as ctx:
            build_panel_content_bridge(plan, layout)
        self.assertIn("Canvas dimension mismatch", str(ctx.exception))
        self.assertIn("768x1216", str(ctx.exception))

    def test_04_height_mismatch_raises_value_error(self):
        """Plan (832x1216) vs Layout (832x1152) must raise ValueError."""
        reg_spec = self._create_region_spec(832, 1216, 3)
        plan, _, _, _ = self.compiler.compile_page(region_spec=reg_spec)
        layout = get_default_panel_layout_spec(832, 1152, preset="3_basic")

        with self.assertRaises(ValueError) as ctx:
            build_panel_content_bridge(plan, layout)
        self.assertIn("Canvas dimension mismatch", str(ctx.exception))
        self.assertIn("832x1152", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
