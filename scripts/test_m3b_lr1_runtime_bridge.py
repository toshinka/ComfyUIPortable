"""M3B-LR1 runtime bridge checks (Stage 4)."""

import copy
import importlib.util
import json
import os
import sys
import tempfile
import types
import unittest
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = "custom_nodes_custom.tegaki_manga_nodes"
PACKAGE_PATH = ROOT / "custom_nodes_custom" / "tegaki_manga_nodes"


def _load_package_module(module_name, path):
    if PACKAGE not in sys.modules:
        package_module = types.ModuleType(PACKAGE)
        package_module.__path__ = [str(PACKAGE_PATH)]
        sys.modules[PACKAGE] = package_module
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


contract = _load_package_module(
    f"{PACKAGE}.authoring_contract",
    PACKAGE_PATH / "authoring_contract.py",
)
bridge = _load_package_module(
    f"{PACKAGE}.rough_guide_bridge",
    PACKAGE_PATH / "rough_guide_bridge.py",
)


class TestM3BLR1RuntimeBridge(unittest.TestCase):
    def setUp(self):
        page = contract.create_page(64, 96, page_id="page_1")
        page["scenes"] = [contract.create_scene("Scene 1", scene_id="scene_1")]
        page["cast"] = [contract.create_cast_entry("Alice", cast_id="cast_1")]
        page["character_instances"] = [contract.create_character_instance(
            "cast_1", "scene_1", instance_id="inst_1"
        )]
        self.doc = contract.create_document(pages=[page])

    def _guide(self, asset_reference="guide.png", enabled=True):
        return {
            "guide_id": "guide_1",
            "guide_type": "rough_manga",
            "asset_reference": asset_reference,
            "placement": contract.make_area(0.0, 0.0, 1.0, 1.0),
            "enabled": enabled,
            "figure_regions": [{
                "figure_id": "figure_1",
                "area": contract.make_area(0.2, 0.2, 0.4, 0.4),
                "instance_id": "inst_1",
            }],
            "metadata": {"fit_mode": "contain"},
        }

    def test_no_guide_is_explicit(self):
        with tempfile.TemporaryDirectory() as root:
            result = bridge.build_rough_guide_plan(self.doc, input_root=root)
            self.assertEqual(result["status"], "NO_GUIDE")
            self.assertEqual(result["debug"]["generation_influence"], "NOT_IMPLEMENTED")

    def test_enabled_guide_outputs_page_image_and_union_mask(self):
        with tempfile.TemporaryDirectory() as root:
            root_path = Path(root)
            Image.new("RGB", (32, 16), (255, 0, 0)).save(root_path / "guide.png")
            self.doc["pages"][0]["guides"] = [self._guide()]
            result = bridge.build_rough_guide_plan(self.doc, input_root=root)
            self.assertEqual(result["status"], "PASS")
            self.assertEqual(tuple(result["image"].shape), (1, 96, 64, 3))
            self.assertEqual(tuple(result["mask"].shape), (1, 96, 64))
            self.assertGreater(float(result["mask"].sum()), 0.0)
            self.assertEqual(result["debug"]["guides"][0]["figure_regions"][0]["instance_id"], "inst_1")

    def test_disabled_guide_does_not_load_or_influence_runtime(self):
        with tempfile.TemporaryDirectory() as root:
            self.doc["pages"][0]["guides"] = [self._guide("missing.png", enabled=False)]
            result = bridge.build_rough_guide_plan(self.doc, input_root=root)
            self.assertEqual(result["status"], "NO_GUIDE")

    def test_missing_absolute_traversal_and_unsupported_paths_fail_closed(self):
        bad_paths = [
            "missing.png",
            "D:/absolute.png",
            "../escape.png",
            "guide.bmp",
        ]
        for bad_path in bad_paths:
            with self.subTest(bad_path=bad_path), tempfile.TemporaryDirectory() as root:
                self.doc["pages"][0]["guides"] = [self._guide(bad_path)]
                with self.assertRaises(ValueError):
                    bridge.build_rough_guide_plan(self.doc, input_root=root)

    def test_duplicate_association_and_unknown_instance_fail_closed(self):
        with tempfile.TemporaryDirectory() as root:
            Image.new("RGB", (32, 16), (0, 0, 0)).save(Path(root) / "guide.png")
            guide = self._guide()
            guide["figure_regions"].append({
                "figure_id": "figure_2",
                "area": contract.make_area(0.6, 0.2, 0.2, 0.4),
                "instance_id": "inst_1",
            })
            self.doc["pages"][0]["guides"] = [guide]
            with self.assertRaises(ValueError):
                bridge.build_rough_guide_plan(self.doc, input_root=root)

            unknown = self._guide()
            unknown["figure_regions"][0]["instance_id"] = "missing_instance"
            self.doc["pages"][0]["guides"] = [unknown]
            with self.assertRaises(ValueError):
                bridge.build_rough_guide_plan(self.doc, input_root=root)


if __name__ == "__main__":
    unittest.main(verbosity=2)
