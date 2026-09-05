"""
test_m1_scene_mask_plan.py — M1 Scene Mask & Plan Integration Tests
===================================================================
Tests contract compatibility between TegakiMinimumHandSceneEditor output,
validate_page_compile_plan, and TegakiMangaMaskBuilder mask generation.
"""
import sys
import os
import json
import unittest
import importlib.util
import torch

_NODES_DIR = os.path.abspath(os.path.join(
    os.path.dirname(__file__), "..",
    "custom_nodes_custom", "tegaki_manga_nodes",
))

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
_ir = _import_submodule("interaction_resolver", "interaction_resolver.py")
_sc = _import_submodule("subscene_contract", "subscene_contract.py")
_ss = _import_submodule("scene_spec", "scene_spec.py")
_aeb = _import_submodule("authoring_execution_bridge", "authoring_execution_bridge.py")
_mse = _import_submodule("minimum_hand_scene_editor", "minimum_hand_scene_editor.py")
_mb = _import_submodule("mask_builder", "mask_builder.py")

validate_page_compile_plan = _ss.validate_page_compile_plan
create_default_m1_document = _mse.create_default_m1_document
TegakiMinimumHandSceneEditor = _mse.TegakiMinimumHandSceneEditor
TegakiMangaMaskBuilder = _mb.TegakiMangaMaskBuilder


class TestM1SceneMaskPlanIntegration(unittest.TestCase):
    """Integration tests between M1 Scene Editor and Mask Generation."""

    def setUp(self):
        self.editor = TegakiMinimumHandSceneEditor()
        self.mask_builder = TegakiMangaMaskBuilder()

    def test_default_two_scene_masks(self):
        default_doc = create_default_m1_document(832, 1216, "Manga Monochrome", 42)
        outputs = self.editor.edit_and_compile(
            document_json=json.dumps(default_doc),
            seed=42,
            resolution="Portrait 832x1216",
        )
        plan = outputs[0]

        # 1. Validate compile plan
        v_plan = validate_page_compile_plan(plan)
        self.assertIsNotNone(v_plan)

        # 2. Build masks with TegakiMangaMaskBuilder
        mask_out = self.mask_builder.build_masks(page_compile_plan=plan, mask_feather=0)
        panel_masks, char_masks, mask_preview, debug_json, local_masks = mask_out

        # Check panel mask tensor properties
        self.assertIsInstance(panel_masks, torch.Tensor)
        self.assertEqual(panel_masks.shape, (2, 1216, 832))

        # Panel 1: Top scene (y ~ 0.06 to 0.48)
        mask1 = panel_masks[0]
        self.assertTrue(mask1[int(1216 * 0.2), int(832 * 0.5)] > 0.9)
        self.assertTrue(mask1[int(1216 * 0.7), int(832 * 0.5)] < 0.1)

        # Panel 2: Bottom scene (y ~ 0.52 to 0.94)
        mask2 = panel_masks[1]
        self.assertTrue(mask2[int(1216 * 0.7), int(832 * 0.5)] > 0.9)
        self.assertTrue(mask2[int(1216 * 0.2), int(832 * 0.5)] < 0.1)

        # Non-overlapping masks
        overlap = (mask1 > 0.5) & (mask2 > 0.5)
        self.assertEqual(overlap.sum().item(), 0)

    def test_geometry_swap_oracle(self):
        """Verify that swapping scene geometries swaps mask positions deterministically."""
        doc = create_default_m1_document(832, 1216, "Manga Monochrome", 42)
        scenes = doc["pages"][0]["scenes"]

        # Swap areas between scene 1 and scene 2
        area1 = dict(scenes[0]["area"])
        area2 = dict(scenes[1]["area"])
        scenes[0]["area"] = area2  # Scene 1 now at bottom
        scenes[1]["area"] = area1  # Scene 2 now at top

        outputs = self.editor.edit_and_compile(
            document_json=json.dumps(doc),
            seed=42,
            resolution="Portrait 832x1216",
        )
        plan = outputs[0]

        mask_out = self.mask_builder.build_masks(page_compile_plan=plan, mask_feather=0)
        panel_masks = mask_out[0]

        # Panel 1 should now be at the bottom
        mask1 = panel_masks[0]
        self.assertTrue(mask1[int(1216 * 0.7), int(832 * 0.5)] > 0.9)
        self.assertTrue(mask1[int(1216 * 0.2), int(832 * 0.5)] < 0.1)

        # Panel 2 should now be at the top
        mask2 = panel_masks[1]
        self.assertTrue(mask2[int(1216 * 0.2), int(832 * 0.5)] > 0.9)
        self.assertTrue(mask2[int(1216 * 0.7), int(832 * 0.5)] < 0.1)

    def test_maximum_six_panels_masks(self):
        """Verify that a 6-scene layout compiles and generates 6 valid masks."""
        page = _ac.create_page(832, 1216)
        for i in range(6):
            y = 0.05 + i * 0.15
            page["scenes"].append(_ac.create_scene(
                name=f"Scene {i+1}",
                prompt=f"scene prompt {i+1}",
                input_mode="simple",
                area=_ac.make_area(0.1, y, 0.8, 0.12),
                order=i+1,
                scene_id=f"sc_{i+1}",
            ))
        doc = _ac.create_document(pages=[page])

        outputs = self.editor.edit_and_compile(
            document_json=json.dumps(doc),
            seed=42,
            resolution="Portrait 832x1216",
        )
        plan = outputs[0]

        mask_out = self.mask_builder.build_masks(page_compile_plan=plan, mask_feather=0)
        panel_masks = mask_out[0]
        self.assertEqual(panel_masks.shape, (6, 1216, 832))

        for i in range(6):
            y_center = int(1216 * (0.05 + i * 0.15 + 0.06))
            x_center = int(832 * 0.5)
            self.assertTrue(panel_masks[i, y_center, x_center] > 0.9)


if __name__ == "__main__":
    unittest.main()
