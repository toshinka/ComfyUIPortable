"""M3B-LR1 rough guide contract tests (Stage 1)."""

import copy
import importlib.util
import json
import os
import unittest


_NODES_DIR = os.path.abspath(os.path.join(
    os.path.dirname(__file__), "..", "custom_nodes_custom", "tegaki_manga_nodes"
))


def _import_module(name, filepath):
    spec = importlib.util.spec_from_file_location(name, filepath)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_ac = _import_module("m3b_lr1_authoring_contract", os.path.join(_NODES_DIR, "authoring_contract.py"))


class TestM3BLR1GuideContract(unittest.TestCase):
    def setUp(self):
        page = _ac.create_page(832, 1216, page_id="page_1")
        page["scenes"] = [_ac.create_scene(
            "Scene 1", "classroom", area=_ac.make_area(0.05, 0.05, 0.9, 0.9), scene_id="scene_1"
        )]
        page["cast"] = [_ac.create_cast_entry("Alice", cast_id="cast_alice")]
        page["character_instances"] = [
            _ac.create_character_instance("cast_alice", "scene_1", instance_id="inst_1")
        ]
        self.page = page

    def _validate(self, guide):
        doc = _ac.create_document(pages=[copy.deepcopy(self.page)])
        doc["pages"][0]["guides"] = [guide]
        return _ac.validate_document(doc)

    def _valid_guide(self, **overrides):
        guide = {
            "guide_id": "guide_1",
            "guide_type": "rough_manga",
            "asset_reference": "tegaki_manga_guides/example.png",
            "placement": _ac.make_area(0.1, 0.1, 0.8, 0.8),
            "enabled": True,
            "figure_regions": [{
                "figure_id": "figure_1",
                "area": _ac.make_area(0.1, 0.1, 0.3, 0.7),
                "instance_id": "inst_1",
            }],
            "metadata": {"fit_mode": "contain"},
        }
        guide.update(overrides)
        return guide

    def test_legacy_empty_guides_pass(self):
        doc = _ac.create_document(pages=[copy.deepcopy(self.page)])
        result = _ac.validate_document(doc)
        self.assertTrue(result.valid, result.errors)

    def test_valid_rough_manga_guide_passes(self):
        result = self._validate(self._valid_guide())
        self.assertTrue(result.valid, result.errors)

    def test_existing_unknown_guide_type_is_preserved(self):
        guide = {
            "guide_id": "legacy_guide",
            "guide_type": "legacy_future_type",
            "asset_reference": None,
            "placement": None,
            "enabled": True,
            "legacy_payload": {"keep": True},
        }
        result = self._validate(guide)
        self.assertTrue(result.valid, result.errors)
        self.assertTrue(result.warnings)
        doc = _ac.create_document(pages=[copy.deepcopy(self.page)])
        doc["pages"][0]["guides"] = [guide]
        roundtrip = _ac.from_json(_ac.to_json(doc))
        self.assertEqual(roundtrip["pages"][0]["guides"][0]["legacy_payload"], {"keep": True})

    def test_duplicate_figure_id_fails(self):
        guide = self._valid_guide()
        guide["figure_regions"].append({"figure_id": "figure_1", "area": _ac.make_area(0.5, 0.1, 0.2, 0.3)})
        result = self._validate(guide)
        self.assertFalse(result.valid)
        self.assertTrue(any("duplicate figure_id" in error for error in result.errors))

    def test_unknown_instance_id_fails(self):
        guide = self._valid_guide()
        guide["figure_regions"][0]["instance_id"] = "inst_missing"
        result = self._validate(guide)
        self.assertFalse(result.valid)
        self.assertTrue(any("not found" in error for error in result.errors))

    def test_duplicate_instance_association_fails(self):
        guide = self._valid_guide()
        guide["figure_regions"].append({"figure_id": "figure_2", "area": _ac.make_area(0.5, 0.1, 0.2, 0.3), "instance_id": "inst_1"})
        result = self._validate(guide)
        self.assertFalse(result.valid)
        self.assertTrue(any("duplicate instance association" in error for error in result.errors))

    def test_invalid_placement_fails(self):
        guide = self._valid_guide(placement=_ac.make_area(0.8, 0.8, 0.4, 0.4))
        result = self._validate(guide)
        self.assertFalse(result.valid)
        self.assertTrue(any("placement" in error for error in result.errors))

    def test_invalid_figure_area_fails(self):
        guide = self._valid_guide()
        guide["figure_regions"][0]["area"] = _ac.make_area(-0.1, 0.1, 0.4, 0.4)
        result = self._validate(guide)
        self.assertFalse(result.valid)
        self.assertTrue(any("figure_regions[0].area" in error for error in result.errors))

    def test_absolute_asset_path_fails(self):
        for path in ("D:/guide.png", "C:/guide.png", "/home/user/guide.png", "file://guide.png"):
            with self.subTest(path=path):
                result = self._validate(self._valid_guide(asset_reference=path))
                self.assertFalse(result.valid)

    def test_path_traversal_fails(self):
        result = self._validate(self._valid_guide(asset_reference="tegaki_manga_guides/../guide.png"))
        self.assertFalse(result.valid)

    def test_unsupported_extension_fails(self):
        result = self._validate(self._valid_guide(asset_reference="tegaki_manga_guides/guide.bmp"))
        self.assertFalse(result.valid)

    def test_unassigned_figure_is_legal(self):
        guide = self._valid_guide()
        guide["figure_regions"][0]["instance_id"] = None
        result = self._validate(guide)
        self.assertTrue(result.valid, result.errors)


if __name__ == "__main__":
    unittest.main(verbosity=2)
