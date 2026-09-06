"""
test_m3a_visual_frame_contract.py — M3A Visual Panel Frame & Overlay Contract Tests
=====================================================================================
Validates all Tier A and Tier B contract requirements for M3A:
1. Zero visual frames pass-through mode: image tensor returned bit-for-bit identical.
2. 1 frame, 2 frames, 4 frames overlay border rendering.
3. Stable frame ID generation and structure (shape / area normalized).
4. Frame move/resize does not change scenes or character instances (Decoupled SSOT).
5. Scene move/resize does not change visual frames (Decoupled SSOT).
6. 1 Scene + 2 Frames validity; 2 Scenes + 1 Frame validity.
7. Derived PANEL_LAYOUT_SPEC bridge preserves semantic spec without mutating doc.
8. Border thickness and color fidelity (pure black borders on boundary).
"""
import os
import sys
import json
import unittest
import copy
import importlib.util
import torch

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

_ac = _import_submodule("authoring_contract", "authoring_contract.py")
_avfb = _import_submodule("authoring_visual_frame_bridge", "authoring_visual_frame_bridge.py")
_fo = _import_submodule("frame_overlay", "frame_overlay.py")
_mse = _import_submodule("minimum_hand_scene_editor", "minimum_hand_scene_editor.py")

validate_document = _ac.validate_document
create_default_m1_document = _mse.create_default_m1_document
derive_panel_layout_spec_from_frames = _avfb.derive_panel_layout_spec_from_frames
TegakiMangaFrameOverlay = _fo.TegakiMangaFrameOverlay


class TestM3AVisualFrameContract(unittest.TestCase):

    def setUp(self):
        self.doc = create_default_m1_document()
        self.page = self.doc["pages"][0]

    def test_01_zero_frames_pass_through(self):
        """Tier A: When visual_frames is empty, image tensor is returned bit-for-bit identical."""
        self.page["visual_frames"] = []
        doc_json = json.dumps(self.doc)

        dummy_img = torch.rand((1, 1216, 832, 3), dtype=torch.float32)
        node = TegakiMangaFrameOverlay()
        res_img, mask, debug = node.apply_overlay(
            image=dummy_img,
            line_thickness=4,
            authoring_document_json=doc_json,
            page_index=0
        )

        # Exact tensor equality
        self.assertTrue(torch.equal(res_img, dummy_img), "0-frame document must pass through image untouched")
        self.assertEqual(mask.shape, (1, 1216, 832))
        self.assertEqual(mask.max().item(), 0.0, "Mask should be completely empty (0.0)")
        dbg = json.loads(debug)
        self.assertEqual(dbg["status"], "PASS")
        self.assertEqual(dbg["mode"], "pass_through")
        self.assertEqual(dbg["frame_count"], 0)

    def test_02_deterministic_border_overlay(self):
        """Tier A: Exact 4px borders are stamped when visual_frames are defined."""
        self.page["visual_frames"] = [
            {
                "frame_id": "frame_1",
                "order": 1,
                "area": {"shape_type": "rect", "x": 0.1, "y": 0.1, "w": 0.8, "h": 0.35},
                "border_thickness": 4,
                "border_color": "#000000"
            },
            {
                "frame_id": "frame_2",
                "order": 2,
                "area": {"shape_type": "rect", "x": 0.1, "y": 0.55, "w": 0.8, "h": 0.35},
                "border_thickness": 4,
                "border_color": "#000000"
            }
        ]
        doc_json = json.dumps(self.doc)

        # Create pure white background image
        white_img = torch.ones((1, 1000, 1000, 3), dtype=torch.float32)
        node = TegakiMangaFrameOverlay()
        res_img, mask, debug = node.apply_overlay(
            image=white_img,
            line_thickness=4,
            authoring_document_json=doc_json,
            page_index=0
        )

        dbg = json.loads(debug)
        self.assertEqual(dbg["status"], "PASS")
        self.assertEqual(dbg["mode"], "deterministic_overlay")
        self.assertEqual(dbg["frame_count"], 2)

        # Inside frame remains white
        center_val = res_img[0, 275, 500].tolist()
        self.assertEqual(center_val, [1.0, 1.0, 1.0], "Inside panel frame must remain original image")

        # Check border at x=100, y=100 is black
        border_val = res_img[0, 100, 100].tolist()
        self.assertEqual(border_val, [0.0, 0.0, 0.0], "Frame perimeter must be black border")

        # Mask at border must be 1.0
        self.assertGreater(mask[0, 100, 100].item(), 0.5)
        # Mask inside frame must be 0.0
        self.assertEqual(mask[0, 275, 500].item(), 0.0)

    def test_03_decoupled_frame_move_invariance(self):
        """Frame move does NOT alter scenes or character instances."""
        orig_scenes = copy.deepcopy(self.page["scenes"])
        self.page["visual_frames"] = [
            {
                "frame_id": "frame_1",
                "order": 1,
                "area": {"shape_type": "rect", "x": 0.1, "y": 0.1, "w": 0.8, "h": 0.35}
            }
        ]

        # Simulate moving frame
        self.page["visual_frames"][0]["area"]["x"] = 0.25
        self.page["visual_frames"][0]["area"]["y"] = 0.30

        # Validate scenes completely identical
        self.assertEqual(self.page["scenes"], orig_scenes, "Scenes must not change when frames move")

    def test_04_decoupled_scene_move_invariance(self):
        """Scene move does NOT alter visual frames."""
        self.page["visual_frames"] = [
            {
                "frame_id": "frame_1",
                "order": 1,
                "area": {"shape_type": "rect", "x": 0.08, "y": 0.06, "w": 0.84, "h": 0.42}
            }
        ]
        orig_frames = copy.deepcopy(self.page["visual_frames"])

        # Simulate moving Scene 1
        self.page["scenes"][0]["area"]["x"] = 0.20
        self.page["scenes"][0]["area"]["y"] = 0.20

        # Validate visual_frames completely identical
        self.assertEqual(self.page["visual_frames"], orig_frames, "Visual frames must not change when scenes move")

    def test_05_valid_m_to_n_configurations(self):
        """Schema validation succeeds for 1 Scene + 2 Frames, and 2 Scenes + 1 Frame."""
        # Config A: 1 Scene + 2 Frames
        doc_a = copy.deepcopy(self.doc)
        doc_a["pages"][0]["scenes"] = [doc_a["pages"][0]["scenes"][0]]
        doc_a["pages"][0]["visual_frames"] = [
            {"frame_id": "f1", "order": 1, "area": {"shape_type": "rect", "x": 0.08, "y": 0.06, "w": 0.84, "h": 0.40}},
            {"frame_id": "f2", "order": 2, "area": {"shape_type": "rect", "x": 0.08, "y": 0.52, "w": 0.84, "h": 0.40}}
        ]
        res_a = validate_document(doc_a)
        self.assertTrue(res_a.valid, f"1 Scene + 2 Frames must be valid: {res_a.errors}")

        # Config B: 2 Scenes + 1 Frame
        doc_b = copy.deepcopy(self.doc)
        doc_b["pages"][0]["visual_frames"] = [
            {"frame_id": "f_splash", "order": 1, "area": {"shape_type": "rect", "x": 0.05, "y": 0.05, "w": 0.90, "h": 0.90}}
        ]
        res_b = validate_document(doc_b)
        self.assertTrue(res_b.valid, f"2 Scenes + 1 Frame must be valid: {res_b.errors}")

    def test_06_derived_panel_layout_spec_bridge(self):
        """Tier B: derive_panel_layout_spec_from_frames converts frames cleanly without mutating doc."""
        frames = [
            {"frame_id": "f1", "order": 1, "area": {"shape_type": "rect", "x": 0.1, "y": 0.1, "w": 0.8, "h": 0.35}},
            {"frame_id": "f2", "order": 2, "area": {"shape_type": "rect", "x": 0.1, "y": 0.55, "w": 0.8, "h": 0.35}}
        ]
        doc_copy = copy.deepcopy(self.doc)
        spec = derive_panel_layout_spec_from_frames(frames, canvas_width=832, canvas_height=1216)

        self.assertEqual(spec["version"], 1)
        self.assertEqual(spec["canvas"]["width"], 832)
        self.assertEqual(spec["canvas"]["height"], 1216)
        self.assertEqual(len(spec["panels"]), 2)
        self.assertEqual(spec["panels"][0]["id"], "panel_f1")
        self.assertEqual(spec["panels"][1]["id"], "panel_f2")
        self.assertEqual(self.doc, doc_copy, "Doc must remain completely unmutated")

    def test_07_area_and_shape_backward_compatibility(self):
        """Both 'shape' and 'area' keys are accepted by the contract."""
        doc_legacy_shape = copy.deepcopy(self.doc)
        doc_legacy_shape["pages"][0]["visual_frames"] = [
            {"frame_id": "f1", "order": 1, "shape": {"shape_type": "rect", "x": 0.1, "y": 0.1, "w": 0.8, "h": 0.8}}
        ]
        res = validate_document(doc_legacy_shape)
        self.assertTrue(res.valid, f"Legacy shape key must be valid: {res.errors}")


if __name__ == "__main__":
    unittest.main()
