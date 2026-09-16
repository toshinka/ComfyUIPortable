"""Unit tests for banked canonical area geometry and mask core.

Verifies pure geometry contracts, coordinate validation, rounding,
boundary handling, mask rasterization, determinism, input immutability,
and production parity against authoritative Manga fixtures.
"""

from __future__ import annotations

import copy
import importlib.util
import math
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

MODULE_PATH = ROOT / "custom_nodes_custom" / "tegaki_manga_nodes" / "canonical_area_geometry.py"
SPEC = importlib.util.spec_from_file_location("canonical_area_geometry", MODULE_PATH.resolve())
assert SPEC is not None and SPEC.loader is not None
geo = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(geo)

validate_canonical_area = geo.validate_canonical_area
normalize_canonical_area = geo.normalize_canonical_area
canonical_area_to_pixel_bounds = geo.canonical_area_to_pixel_bounds
pixel_bounds_to_mask = geo.pixel_bounds_to_mask
canonical_area_to_mask = geo.canonical_area_to_mask
MIN_RECT_SIZE = geo.MIN_RECT_SIZE


class CanonicalAreaGeometryTests(unittest.TestCase):
    """Test suite for canonical area geometry and hard mask creation."""

    def test_full_canvas_area(self):
        area = {"x": 0.0, "y": 0.0, "w": 1.0, "h": 1.0}
        bounds = canonical_area_to_pixel_bounds(area, 832, 1216)
        self.assertEqual(bounds, (0, 0, 832, 1216))

        mask = canonical_area_to_mask(area, 832, 1216)
        self.assertEqual(mask.shape, (1216, 832))
        self.assertEqual(float(mask.sum().item()), float(832 * 1216))
        self.assertEqual(float(mask.min().item()), 1.0)
        self.assertEqual(float(mask.max().item()), 1.0)

    def test_top_left_area(self):
        area = {"x": 0.0, "y": 0.0, "w": 0.25, "h": 0.25}
        bounds = canonical_area_to_pixel_bounds(area, 800, 600)
        self.assertEqual(bounds, (0, 0, 200, 150))

        mask = canonical_area_to_mask(area, 800, 600)
        self.assertEqual(mask.shape, (600, 800))
        # Inside bounds: 1.0
        self.assertEqual(float(mask[0:150, 0:200].min().item()), 1.0)
        self.assertEqual(float(mask[0:150, 0:200].max().item()), 1.0)
        # Outside bounds: 0.0
        self.assertEqual(float(mask[150:, :].max().item()), 0.0)
        self.assertEqual(float(mask[:, 200:].max().item()), 0.0)
        self.assertEqual(float(mask.sum().item()), float(200 * 150))

    def test_bottom_right_area(self):
        area = {"x": 0.75, "y": 0.75, "w": 0.25, "h": 0.25}
        bounds = canonical_area_to_pixel_bounds(area, 800, 600)
        self.assertEqual(bounds, (600, 450, 800, 600))

        mask = canonical_area_to_mask(area, 800, 600)
        self.assertEqual(mask.shape, (600, 800))
        # Inside bounds: 1.0
        self.assertEqual(float(mask[450:600, 600:800].min().item()), 1.0)
        self.assertEqual(float(mask[450:600, 600:800].max().item()), 1.0)
        # Outside bounds: 0.0
        self.assertEqual(float(mask[:450, :].max().item()), 0.0)
        self.assertEqual(float(mask[:, :600].max().item()), 0.0)
        self.assertEqual(float(mask.sum().item()), float(200 * 150))

    def test_non_square_canvas_orientation(self):
        # Tall portrait canvas: width=832, height=1216
        area = {"x": 0.1, "y": 0.2, "w": 0.5, "h": 0.4}
        bounds = canonical_area_to_pixel_bounds(area, 832, 1216)
        # px0 = round(0.1 * 832) = 83
        # py0 = round(0.2 * 1216) = 243
        # px1 = round(0.6 * 832) = 499
        # py1 = round(0.6 * 1216) = 730
        self.assertEqual(bounds, (83, 243, 499, 730))

        mask = canonical_area_to_mask(area, 832, 1216)
        # Height is dimension 0, width is dimension 1
        self.assertEqual(mask.shape, (1216, 832))
        self.assertEqual(float(mask[243:730, 83:499].min().item()), 1.0)
        self.assertEqual(float(mask.sum().item()), float((499 - 83) * (730 - 243)))

    def test_fractional_canonical_coordinates_and_rounding(self):
        # Precise coordinates with floating fraction
        area = {"x": 0.123456, "y": 0.234567, "w": 0.345678, "h": 0.456789}
        w, h = 1000, 1000
        # px0 = round(123.456) = 123
        # py0 = round(234.567) = 235
        # px1 = round((0.123456 + 0.345678) * 1000) = round(469.134) = 469
        # py1 = round((0.234567 + 0.456789) * 1000) = round(691.356) = 691
        bounds = canonical_area_to_pixel_bounds(area, w, h)
        self.assertEqual(bounds, (123, 235, 469, 691))

    def test_small_valid_rectangle(self):
        area = {"x": 0.5, "y": 0.5, "w": MIN_RECT_SIZE, "h": MIN_RECT_SIZE}
        bounds = canonical_area_to_pixel_bounds(area, 1000, 1000)
        # px0 = 500, py0 = 500, px1 = 501, py1 = 501
        self.assertEqual(bounds, (500, 500, 501, 501))
        mask = canonical_area_to_mask(area, 1000, 1000)
        self.assertEqual(float(mask.sum().item()), 1.0)
        self.assertEqual(float(mask[500, 500].item()), 1.0)

    def test_edge_touching_rectangles(self):
        # Touching left and top
        left_top = {"x": 0.0, "y": 0.0, "w": 0.5, "h": 0.5}
        bounds_lt = canonical_area_to_pixel_bounds(left_top, 800, 600)
        self.assertEqual(bounds_lt, (0, 0, 400, 300))

        # Touching right and bottom
        right_bottom = {"x": 0.5, "y": 0.5, "w": 0.5, "h": 0.5}
        bounds_rb = canonical_area_to_pixel_bounds(right_bottom, 800, 600)
        self.assertEqual(bounds_rb, (400, 300, 800, 600))

        # Adjacent boundary shares pixel coordinate without gap or overlap
        self.assertEqual(bounds_lt[2], bounds_rb[0])
        self.assertEqual(bounds_lt[3], bounds_rb[1])

    def test_determinism(self):
        area = {"x": 0.08, "y": 0.06, "w": 0.84, "h": 0.42}
        bounds_1 = canonical_area_to_pixel_bounds(area, 832, 1216)
        bounds_2 = canonical_area_to_pixel_bounds(area, 832, 1216)
        self.assertEqual(bounds_1, bounds_2)

        mask_1 = canonical_area_to_mask(area, 832, 1216)
        mask_2 = canonical_area_to_mask(area, 832, 1216)
        self.assertTrue((mask_1 == mask_2).all().item())

    def test_input_immutability(self):
        area = {"shape_type": "rect", "x": 0.1, "y": 0.2, "w": 0.3, "h": 0.4}
        original = copy.deepcopy(area)

        validate_canonical_area(area)
        self.assertEqual(area, original)

        normalize_canonical_area(area)
        self.assertEqual(area, original)

        canonical_area_to_pixel_bounds(area, 832, 1216)
        self.assertEqual(area, original)

        canonical_area_to_mask(area, 832, 1216)
        self.assertEqual(area, original)

    def test_invalid_canvas_dimensions(self):
        valid_area = {"x": 0.1, "y": 0.1, "w": 0.5, "h": 0.5}
        invalid_dimensions = [
            (0, 100),
            (100, 0),
            (-100, 100),
            (100, -100),
            (True, 100),
            (100, False),
            ("800", 600),
            (800.5, 600),
            (None, 600),
        ]
        for w, h in invalid_dimensions:
            with self.subTest(w=w, h=h):
                with self.assertRaises(ValueError):
                    canonical_area_to_pixel_bounds(valid_area, w, h)
                with self.assertRaises(ValueError):
                    canonical_area_to_mask(valid_area, w, h)
                with self.assertRaises(ValueError):
                    pixel_bounds_to_mask((0, 0, 10, 10), w, h)

    def test_invalid_area_values(self):
        invalid_areas = [
            # Missing key
            {"x": 0.1, "y": 0.1, "w": 0.5},
            # Non-dict
            "x=0.1,y=0.1",
            # Unsupported shape_type
            {"shape_type": "polygon", "x": 0.1, "y": 0.1, "w": 0.5, "h": 0.5},
            # Non-numeric / boolean
            {"x": True, "y": 0.1, "w": 0.5, "h": 0.5},
            {"x": 0.1, "y": "0.1", "w": 0.5, "h": 0.5},
            # Non-finite
            {"x": float("nan"), "y": 0.1, "w": 0.5, "h": 0.5},
            {"x": 0.1, "y": float("inf"), "w": 0.5, "h": 0.5},
            # Zero or negative dimension
            {"x": 0.1, "y": 0.1, "w": 0.0, "h": 0.5},
            {"x": 0.1, "y": 0.1, "w": 0.5, "h": -0.1},
        ]
        for candidate in invalid_areas:
            with self.subTest(candidate=candidate):
                with self.assertRaises(ValueError):
                    validate_canonical_area(candidate)
                with self.assertRaises(ValueError):
                    canonical_area_to_pixel_bounds(candidate, 800, 600)

    def test_out_of_range_behavior(self):
        out_of_range_areas = [
            # Negative origin
            {"x": -0.01, "y": 0.1, "w": 0.5, "h": 0.5},
            {"x": 0.1, "y": -0.05, "w": 0.5, "h": 0.5},
            # Origin > 1.0
            {"x": 1.05, "y": 0.1, "w": 0.5, "h": 0.5},
            {"x": 0.1, "y": 1.1, "w": 0.5, "h": 0.5},
            # Exceeding 1.0 sum
            {"x": 0.8, "y": 0.1, "w": 0.3, "h": 0.5},
            {"x": 0.1, "y": 0.7, "w": 0.5, "h": 0.4},
        ]
        for candidate in out_of_range_areas:
            with self.subTest(candidate=candidate):
                with self.assertRaises(ValueError):
                    validate_canonical_area(candidate)

    def test_normalize_canonical_area_clamping(self):
        # Out of bounds area clamped cleanly
        clamped = normalize_canonical_area({"x": -0.1, "y": 0.9, "w": 0.5, "h": 0.5})
        self.assertEqual(clamped["shape_type"], "rect")
        self.assertGreaterEqual(clamped["x"], 0.0)
        self.assertGreaterEqual(clamped["y"], 0.0)
        self.assertLessEqual(clamped["x"] + clamped["w"], 1.0)
        self.assertLessEqual(clamped["y"] + clamped["h"], 1.0)
        self.assertEqual(clamped["x"], 0.0)
        self.assertEqual(clamped["w"], 0.5)
        self.assertEqual(clamped["y"], 0.9)
        self.assertEqual(clamped["h"], 0.1)  # clamped to 1.0 - 0.9

    def test_as_batch_tensor_shape(self):
        area = {"x": 0.2, "y": 0.2, "w": 0.4, "h": 0.4}
        mask_2d = canonical_area_to_mask(area, 400, 400, as_batch=False)
        self.assertEqual(mask_2d.shape, (400, 400))

        mask_3d = canonical_area_to_mask(area, 400, 400, as_batch=True)
        self.assertEqual(mask_3d.shape, (1, 400, 400))
        self.assertTrue((mask_2d == mask_3d[0]).all().item())

    def test_production_parity_with_authoring_document_fixtures(self):
        """Verify exact parity with production pixel bounds calculation."""
        # Standard Manga authoring page resolution
        W, H = 832, 1216

        # Fixture Scene 1: Top panel
        scene_1_area = {"shape_type": "rect", "x": 0.08, "y": 0.06, "w": 0.84, "h": 0.42}
        # Production math from mask_builder.py lines 96-99:
        expected_px0 = max(0, min(W, int(round(0.08 * W))))
        expected_py0 = max(0, min(H, int(round(0.06 * H))))
        expected_px1 = max(0, min(W, int(round((0.08 + 0.84) * W))))
        expected_py1 = max(0, min(H, int(round((0.06 + 0.42) * H))))

        bounds = canonical_area_to_pixel_bounds(scene_1_area, W, H)
        self.assertEqual(bounds, (expected_px0, expected_py0, expected_px1, expected_py1))
        self.assertEqual(bounds, (67, 73, 765, 584))

        # Fixture Scene 2: Bottom panel
        scene_2_area = {"shape_type": "rect", "x": 0.08, "y": 0.52, "w": 0.84, "h": 0.42}
        expected_s2_px0 = max(0, min(W, int(round(0.08 * W))))
        expected_s2_py0 = max(0, min(H, int(round(0.52 * H))))
        expected_s2_px1 = max(0, min(W, int(round((0.08 + 0.84) * W))))
        expected_s2_py1 = max(0, min(H, int(round((0.52 + 0.42) * H))))

        bounds_2 = canonical_area_to_pixel_bounds(scene_2_area, W, H)
        self.assertEqual(bounds_2, (expected_s2_px0, expected_s2_py0, expected_s2_px1, expected_s2_py1))
        self.assertEqual(bounds_2, (67, 632, 765, 1143))

        # Fixture Character Instance: Page-projected area
        char_area = {"shape_type": "rect", "x": 0.12, "y": 0.10, "w": 0.32, "h": 0.35}
        expected_c_px0 = max(0, min(W, int(round(0.12 * W))))
        expected_c_py0 = max(0, min(H, int(round(0.10 * H))))
        expected_c_px1 = max(0, min(W, int(round((0.12 + 0.32) * W))))
        expected_c_py1 = max(0, min(H, int(round((0.10 + 0.35) * H))))

        char_bounds = canonical_area_to_pixel_bounds(char_area, W, H)
        self.assertEqual(char_bounds, (expected_c_px0, expected_c_py0, expected_c_px1, expected_c_py1))
        self.assertEqual(char_bounds, (100, 122, 366, 547))

        # Verify raster mask matches slice assignment in production mask_builder.py
        char_mask = canonical_area_to_mask(char_area, W, H, as_batch=False)
        self.assertEqual(char_mask.shape, (H, W))
        # Active slice
        self.assertEqual(float(char_mask[122:547, 100:366].min().item()), 1.0)
        # Exact active area count
        self.assertEqual(float(char_mask.sum().item()), float((366 - 100) * (547 - 122)))


if __name__ == "__main__":
    unittest.main()
