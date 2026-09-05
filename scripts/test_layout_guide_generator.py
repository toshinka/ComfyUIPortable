"""
Unit Tests for TegakiMangaLayoutGuideGenerator (Phase 3I)
=========================================================
Tests layout guide generation from multiple input schemas (TWO_REGION_SPEC,
REGION_SPEC, MANGA_PAGE_PLAN), output tensor shapes, value ranges, and styles.
"""

import os
import sys
import json
import unittest
import torch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "custom_nodes_custom")))
from tegaki_manga_nodes.layout_guide_generator import (
    TegakiMangaLayoutGuideGenerator,
    extract_staging_boxes,
    _normalize_box
)


class TestLayoutGuideGenerator(unittest.TestCase):
    def setUp(self):
        self.node = TegakiMangaLayoutGuideGenerator()

    def test_01_normalize_box(self):
        # List format
        b1 = _normalize_box([0.1, 0.2, 0.3, 0.4])
        self.assertEqual(b1, [0.1, 0.2, 0.3, 0.4])

        # Dict format
        b2 = _normalize_box({"x": 0.15, "y": 0.25, "w": 0.35, "h": 0.45})
        self.assertEqual(b2, [0.15, 0.25, 0.35, 0.45])

        # Dict format with width/height
        b3 = _normalize_box({"x": 0.15, "y": 0.25, "width": 0.35, "height": 0.45})
        self.assertEqual(b3, [0.15, 0.25, 0.35, 0.45])

        # Invalid format
        self.assertIsNone(_normalize_box("invalid"))
        self.assertIsNone(_normalize_box([1, 2]))

    def test_02_extract_staging_boxes_two_region(self):
        two_region = {
            "canvas": {"width": 1024, "height": 1024},
            "regions": [
                {"id": "A", "x": 0.1, "y": 0.1, "w": 0.4, "h": 0.7, "label": "Dog", "enabled": True},
                {"id": "B", "x": 0.5, "y": 0.1, "w": 0.4, "h": 0.7, "label": "Cat", "enabled": True},
            ]
        }
        panel_box, chars = extract_staging_boxes(two_region)
        self.assertEqual(len(chars), 2)
        self.assertEqual(chars[0]["id"], "A")
        self.assertEqual(chars[0]["name"], "Dog")
        self.assertEqual(chars[1]["id"], "B")
        self.assertEqual(chars[1]["name"], "Cat")

    def test_03_extract_staging_boxes_region_spec(self):
        region_spec = {
            "canvas": {"width": 1024, "height": 1024},
            "regions": [
                {
                    "id": 1,
                    "characters": [
                        {
                            "character_id": "char_alice",
                            "name": "Alice",
                            "enabled": True,
                            "area": [0.15, 0.20, 0.35, 0.70]
                        },
                        {
                            "character_id": "char_bob",
                            "name": "Bob",
                            "enabled": True,
                            "area": {"x": 0.55, "y": 0.20, "w": 0.35, "h": 0.70}
                        }
                    ]
                }
            ]
        }
        panel_box, chars = extract_staging_boxes(region_spec, target_panel_id=1)
        self.assertEqual(len(chars), 2)
        self.assertEqual(chars[0]["id"], "char_alice")
        self.assertEqual(chars[0]["box"], [0.15, 0.20, 0.35, 0.70])
        self.assertEqual(chars[1]["id"], "char_bob")
        self.assertEqual(chars[1]["box"], [0.55, 0.20, 0.35, 0.70])

    def test_04_generate_guide_shapes_and_ranges(self):
        region_spec = {
            "canvas": {"width": 1024, "height": 1024},
            "regions": [
                {
                    "id": 1,
                    "characters": [
                        {"character_id": "alice", "enabled": True, "area": [0.15, 0.20, 0.35, 0.70]},
                        {"character_id": "bob", "enabled": True, "area": [0.55, 0.20, 0.35, 0.70]}
                    ]
                }
            ]
        }
        img, mask, debug = self.node.generate_guide(
            scene_plan=region_spec,
            target_panel_id=1,
            guide_style="mannequin_capsule",
            color_mode="Black on White",
            width=1024,
            height=1024
        )
        self.assertEqual(img.shape, (1, 1024, 1024, 3))
        self.assertEqual(mask.shape, (1, 1024, 1024))
        self.assertEqual(img.dtype, torch.float32)
        self.assertEqual(mask.dtype, torch.float32)
        self.assertTrue(0.0 <= img.min() <= img.max() <= 1.0)
        self.assertTrue(0.0 <= mask.min() <= mask.max() <= 1.0)
        # Mask must have non-zero elements where characters are
        self.assertGreater(mask.sum().item(), 1000)

        # Parse debug json
        info = json.loads(debug)
        self.assertEqual(info["extracted_characters"], 2)

    def test_05_guide_styles_and_colors(self):
        spec = {
            "regions": [
                {"id": "A", "x": 0.2, "y": 0.2, "w": 0.6, "h": 0.6, "enabled": True}
            ]
        }
        for style in ["mannequin_capsule", "box_wireframe", "flat_silhouette"]:
            for color in ["Black on White", "White on Black"]:
                img, mask, debug = self.node.generate_guide(
                    scene_plan=spec,
                    guide_style=style,
                    color_mode=color,
                    width=512,
                    height=512
                )
                self.assertEqual(img.shape, (1, 512, 512, 3))
                self.assertEqual(mask.shape, (1, 512, 512))


if __name__ == "__main__":
    unittest.main()
