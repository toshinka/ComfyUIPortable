"""
test_m3a1_frame_overlay_runtime_truth.py — M3A.1 Frame Runtime Truth Tests
=============================================================================
Tests the M3A.1 corrections:
1. Invalid JSON -> fail-closed (ERROR status, not silent pass-through)
2. Page index out-of-range -> fail-closed
3. Valid document + 0 frames -> pass-through pixel-identical
4. 2 frames -> white gutter verified (non-frame pixels are white)
5. 2 frames -> black borders verified (border pixels are black)
6. Per-frame thickness 2px/8px -> different pixel widths reflected in output
7. area-only canonical frame -> geometry respected
8. Legacy shape-only frame -> area priority migration (shape used as fallback)
9. Empty frames -> derive_panel_layout_spec_from_frames returns None (no fake full-frame)
10. area+shape both present -> area takes priority
"""
import os
import sys
import json
import unittest
import copy
import importlib.util
import torch
import numpy as np
from PIL import Image

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_NODES_DIR = os.path.join(_ROOT, "custom_nodes_custom", "tegaki_manga_nodes")


def _import_submodule(subname, filename):
    fullname = f"tegaki_manga_nodes.{subname}"
    spec = importlib.util.spec_from_file_location(
        fullname,
        os.path.join(_NODES_DIR, filename),
        submodule_search_locations=[],
    )
    mod = importlib.util.module_from_spec(spec)
    mod.__package__ = "tegaki_manga_nodes"
    sys.modules[fullname] = mod
    spec.loader.exec_module(mod)
    return mod


pkg = type(sys)("tegaki_manga_nodes")
pkg.__path__ = [_NODES_DIR]
sys.modules["tegaki_manga_nodes"] = pkg

_avfb = _import_submodule("authoring_visual_frame_bridge", "authoring_visual_frame_bridge.py")
_fo = _import_submodule("frame_overlay", "frame_overlay.py")

derive_panel_layout_spec_from_frames = _avfb.derive_panel_layout_spec_from_frames
render_deterministic_frame_overlay = _avfb.render_deterministic_frame_overlay
_render_single_pil_overlay = _avfb._render_single_pil_overlay
TegakiMangaFrameOverlay = _fo.TegakiMangaFrameOverlay


def _make_solid_tensor(H=64, W=48, color=(128, 200, 100)):
    """Create a solid-color image tensor (B,H,W,C) float32 in [0,1]."""
    arr = np.zeros((H, W, 3), dtype=np.float32)
    arr[:, :, 0] = color[0] / 255.0
    arr[:, :, 1] = color[1] / 255.0
    arr[:, :, 2] = color[2] / 255.0
    return torch.from_numpy(arr).unsqueeze(0)  # (1,H,W,3)


def _make_doc_with_frames(frames):
    return {
        "document_id": "test_doc",
        "schema_version": "1.0",
        "pages": [{
            "page_id": "p1",
            "width_px": 832,
            "height_px": 1216,
            "scenes": [],
            "character_instances": [],
            "visual_frames": frames,
            "metadata": {}
        }]
    }


class TestFailClosed(unittest.TestCase):

    def setUp(self):
        self.node = TegakiMangaFrameOverlay()
        self.img = _make_solid_tensor()

    def test_invalid_json_returns_error_status(self):
        """Finding A: invalid JSON must produce ERROR status, not silent pass-through PASS."""
        result_img, mask, debug_str = self.node.apply_overlay(
            self.img, line_thickness=4,
            authoring_document_json="NOT VALID JSON {{{",
            page_index=0
        )
        debug = json.loads(debug_str)
        self.assertEqual(debug["validation_status"], "ERROR", "Invalid JSON should produce ERROR status")
        self.assertIn("error", debug, "Error detail must be present in debug_json")
        self.assertEqual(debug["status"], "ERROR")
        # Image should be passed through unchanged on error
        self.assertEqual(result_img.shape, self.img.shape)

    def test_page_index_out_of_range_error(self):
        """Finding A: page_index out-of-range must produce ERROR, not silent 0-frame pass-through."""
        doc = _make_doc_with_frames([])
        result_img, mask, debug_str = self.node.apply_overlay(
            self.img, line_thickness=4,
            authoring_document_json=json.dumps(doc),
            page_index=99
        )
        debug = json.loads(debug_str)
        self.assertEqual(debug["validation_status"], "ERROR", "Out-of-range page_index must be ERROR")
        self.assertIn("out of range", debug.get("error", "").lower(),
                      "Error message must mention out of range")

    def test_valid_zero_frames_is_pass_through(self):
        """Valid document with 0 frames => pass-through PASS (legal case)."""
        doc = _make_doc_with_frames([])
        result_img, mask, debug_str = self.node.apply_overlay(
            self.img, line_thickness=4,
            authoring_document_json=json.dumps(doc),
            page_index=0
        )
        debug = json.loads(debug_str)
        self.assertEqual(debug["validation_status"], "PASS")
        self.assertEqual(debug["render_mode"], "pass_through")
        self.assertEqual(debug["frame_count"], 0)
        # Pixel-identical pass-through
        self.assertTrue(torch.allclose(result_img, self.img),
                        "0-frame must be pixel-identical pass-through")

    def test_empty_string_authoring_json_is_passthrough(self):
        """Empty authoring_document_json string => pass-through (no document provided)."""
        result_img, mask, debug_str = self.node.apply_overlay(
            self.img, line_thickness=4,
            authoring_document_json="",
            page_index=0
        )
        debug = json.loads(debug_str)
        self.assertEqual(debug["render_mode"], "pass_through")
        self.assertTrue(torch.allclose(result_img, self.img))


class TestWhiteGutterAndBlackBorders(unittest.TestCase):

    def test_gutter_is_white_between_two_frames(self):
        """Finding B: pixels outside frame rectangles must be pure white (gutter)."""
        H, W = 100, 80
        source = Image.new("RGB", (W, H), (50, 100, 150))  # solid blue-ish

        # Two frames: top half and bottom half with a gap
        frames = [
            {"frame_id": "f1", "area": {"x": 0.1, "y": 0.1, "w": 0.8, "h": 0.35}, "border_thickness": 2},
            {"frame_id": "f2", "area": {"x": 0.1, "y": 0.55, "w": 0.8, "h": 0.35}, "border_thickness": 2},
        ]

        result, mask = _render_single_pil_overlay(source, frames, global_line_thickness=2)
        arr = np.array(result)

        # Top-left corner (0,0) is outside both frames -> should be white
        self.assertEqual(tuple(arr[0, 0]), (255, 255, 255),
                         "Top-left corner outside frames must be white gutter")
        # Gap between frames (around y=0.45*H) should be white
        gap_y = int(0.47 * H)
        gap_x = int(0.5 * W)
        self.assertEqual(tuple(arr[gap_y, gap_x]), (255, 255, 255),
                         "Gap between frames must be white gutter")

    def test_border_pixels_are_black(self):
        """Finding B: border pixels must be pure black."""
        H, W = 100, 80
        source = Image.new("RGB", (W, H), (128, 128, 128))  # gray

        frames = [
            {"frame_id": "f1", "area": {"x": 0.1, "y": 0.1, "w": 0.8, "h": 0.8}, "border_thickness": 4},
        ]

        result, mask = _render_single_pil_overlay(source, frames, global_line_thickness=4)
        arr = np.array(result)

        # Top-left border corner
        bx0 = int(round(0.1 * W))
        by0 = int(round(0.1 * H))
        # The border starts at (bx0, by0); check a pixel at the border
        border_pixel = tuple(arr[by0, bx0])
        self.assertEqual(border_pixel, (0, 0, 0),
                         f"Border pixel at ({bx0},{by0}) must be black, got {border_pixel}")

    def test_interior_preserves_source(self):
        """Finding B: inside frame interior (non-border) must preserve source image pixels."""
        H, W = 100, 80
        src_color = (200, 150, 100)
        source = Image.new("RGB", (W, H), src_color)

        frames = [
            {"frame_id": "f1", "area": {"x": 0.1, "y": 0.1, "w": 0.8, "h": 0.8}, "border_thickness": 4},
        ]

        result, mask = _render_single_pil_overlay(source, frames, global_line_thickness=4)
        arr = np.array(result)

        # Center of frame (well inside borders)
        cy = int(0.5 * H)
        cx = int(0.5 * W)
        center_pixel = tuple(arr[cy, cx])
        self.assertEqual(center_pixel, src_color,
                         f"Interior pixel must preserve source color {src_color}, got {center_pixel}")


class TestPerFrameThickness(unittest.TestCase):

    def test_per_frame_thickness_honored(self):
        """Finding C: per-frame border_thickness must be used, not global line_thickness."""
        H, W = 200, 160
        source = Image.new("RGB", (W, H), (128, 128, 128))

        frames = [
            {"frame_id": "f_thin", "area": {"x": 0.05, "y": 0.05, "w": 0.4, "h": 0.4}, "border_thickness": 2},
            {"frame_id": "f_thick", "area": {"x": 0.55, "y": 0.05, "w": 0.4, "h": 0.4}, "border_thickness": 12},
        ]

        result, mask = _render_single_pil_overlay(source, frames, global_line_thickness=4)
        arr = np.array(result)

        # Check thin frame border: only 1-2 pixels from edge should be black
        # f_thin left edge at x = 0.05*W
        thin_x = int(round(0.05 * W))
        thin_y = int(round(0.25 * H))  # midpoint vertically

        # pixel at thin_x+3 (inside thin border 2px) should be source color
        if thin_x + 3 < W:
            pixel_inside_thin = tuple(arr[thin_y, thin_x + 3])
            self.assertNotEqual(pixel_inside_thin, (0, 0, 0),
                                "Pixel 3px inside thin frame (2px border) should NOT be black")

        # Check thick frame border: pixel at thick_x+5 should still be black (12px border)
        thick_x = int(round(0.55 * W))
        thick_y = int(round(0.25 * H))

        if thick_x + 5 < W:
            pixel_inside_thick = tuple(arr[thick_y, thick_x + 5])
            self.assertEqual(pixel_inside_thick, (0, 0, 0),
                             f"Pixel 5px inside thick frame (12px border) should be black, got {pixel_inside_thick}")

    def test_global_fallback_used_when_no_per_frame(self):
        """If frame has no border_thickness, global line_thickness fallback is used."""
        H, W = 100, 80
        source = Image.new("RGB", (W, H), (128, 128, 128))
        frames = [
            {"frame_id": "f1", "area": {"x": 0.1, "y": 0.1, "w": 0.8, "h": 0.8}},
        ]
        # Should not raise; use global fallback 4
        result, mask = _render_single_pil_overlay(source, frames, global_line_thickness=4)
        arr = np.array(result)
        bx0 = int(round(0.1 * W))
        by0 = int(round(0.1 * H))
        self.assertEqual(tuple(arr[by0, bx0]), (0, 0, 0), "Border should be black with fallback thickness")


class TestAreaCanonicalKey(unittest.TestCase):

    def test_area_key_takes_priority_over_shape(self):
        """Finding D: when both area and shape present, area must take priority."""
        H, W = 100, 80
        source = Image.new("RGB", (W, H), (128, 128, 128))

        frames = [
            {
                "frame_id": "f1",
                "area": {"x": 0.1, "y": 0.1, "w": 0.8, "h": 0.3},  # top third
                "shape": {"x": 0.1, "y": 0.6, "w": 0.8, "h": 0.3},  # bottom third (WRONG one)
                "border_thickness": 3
            }
        ]

        result, mask = _render_single_pil_overlay(source, frames, global_line_thickness=3)
        arr = np.array(result)

        # area says top third: border at y=0.1*H
        by0 = int(round(0.1 * H))
        bx0 = int(round(0.1 * W))
        self.assertEqual(tuple(arr[by0, bx0]), (0, 0, 0),
                         "Border should be at area position (top), not shape position (bottom)")

        # shape says bottom third: y=0.6*H — should be white gutter if area took priority
        shape_y = int(round(0.6 * H))
        shape_x = int(round(0.1 * W))
        # Should not be border black (shape was ignored)
        # (Could be white gutter or interior white — not border of frame there)
        self.assertNotEqual(tuple(arr[shape_y, shape_x]), (0, 0, 0),
                            "Shape position should NOT have a border (area takes priority)")

    def test_shape_only_is_fallback(self):
        """Legacy shape-only frames still work (shape as fallback when area absent)."""
        H, W = 100, 80
        source = Image.new("RGB", (W, H), (128, 128, 128))
        frames = [
            {
                "frame_id": "f_legacy",
                "shape": {"x": 0.1, "y": 0.1, "w": 0.8, "h": 0.8},
                "border_thickness": 3
            }
        ]
        # Should not raise; shape used as fallback
        result, mask = _render_single_pil_overlay(source, frames, global_line_thickness=3)
        arr = np.array(result)
        bx0 = int(round(0.1 * W))
        by0 = int(round(0.1 * H))
        self.assertEqual(tuple(arr[by0, bx0]), (0, 0, 0),
                         "Legacy shape-only frame should produce black border")


class TestDeriveEmptyFrames(unittest.TestCase):

    def test_empty_frames_returns_none(self):
        """Finding E: derive_panel_layout_spec_from_frames([]) must return None (no fake full-frame)."""
        result = derive_panel_layout_spec_from_frames([], canvas_width=832, canvas_height=1216)
        self.assertIsNone(result,
                          "derive_panel_layout_spec_from_frames([]) must return None, not a fake full-frame spec")

    def test_nonempty_frames_returns_spec(self):
        """With frames present, derive should return valid PANEL_LAYOUT_SPEC."""
        frames = [{"frame_id": "f1", "area": {"x": 0.1, "y": 0.1, "w": 0.8, "h": 0.8}}]
        result = derive_panel_layout_spec_from_frames(frames)
        self.assertIsNotNone(result)
        self.assertIn("panels", result)
        self.assertEqual(len(result["panels"]), 1)

    def test_does_not_mutate_input_frames(self):
        """derive must not mutate the input document."""
        import copy as _copy
        frames = [{"frame_id": "f1", "area": {"x": 0.1, "y": 0.1, "w": 0.8, "h": 0.8}}]
        original = _copy.deepcopy(frames)
        derive_panel_layout_spec_from_frames(frames)
        self.assertEqual(frames, original, "derive must not mutate input")


if __name__ == "__main__":
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    for tc in [TestFailClosed, TestWhiteGutterAndBlackBorders, TestPerFrameThickness,
               TestAreaCanonicalKey, TestDeriveEmptyFrames]:
        suite.addTests(loader.loadTestsFromTestCase(tc))
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
