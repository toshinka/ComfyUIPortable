"""
test_m0_legacy_import.py — M0 Legacy Import/Export Fixture 9 + Regression
==========================================================================
Pure Python tests. No ComfyUI server required.
"""
import sys
import os
import json
import glob
import copy
import unittest
import importlib.util

_NODES_DIR = os.path.abspath(os.path.join(
    os.path.dirname(__file__), "..",
    "custom_nodes_custom", "tegaki_manga_nodes",
))

def _import_module(name, filepath):
    spec = importlib.util.spec_from_file_location(name, filepath)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod

# Import authoring_contract first (no deps)
_ac = _import_module(
    "authoring_contract",
    os.path.join(_NODES_DIR, "authoring_contract.py"),
)

# Patch for relative imports in authoring_migration
pkg = type(sys)("tegaki_manga_nodes")
pkg.__path__ = [_NODES_DIR]
sys.modules["tegaki_manga_nodes"] = pkg
sys.modules["tegaki_manga_nodes.authoring_contract"] = _ac

# Import authoring_migration
_mig_spec = importlib.util.spec_from_file_location(
    "tegaki_manga_nodes.authoring_migration",
    os.path.join(_NODES_DIR, "authoring_migration.py"),
    submodule_search_locations=[],
)
_mig = importlib.util.module_from_spec(_mig_spec)
_mig.__package__ = "tegaki_manga_nodes"
sys.modules["tegaki_manga_nodes.authoring_migration"] = _mig
_mig_spec.loader.exec_module(_mig)

SCHEMA_ID = _ac.SCHEMA_ID
SCHEMA_VERSION = _ac.SCHEMA_VERSION
validate_document = _ac.validate_document
make_area = _ac.make_area
to_json = _ac.to_json
from_json = _ac.from_json
create_document = _ac.create_document
create_page = _ac.create_page
create_scene = _ac.create_scene

import_from_legacy = _mig.import_from_legacy
export_to_legacy = _mig.export_to_legacy
koma_local_to_page_normalized = _mig.koma_local_to_page_normalized
page_normalized_to_koma_local = _mig.page_normalized_to_koma_local
MigrationResult = _mig.MigrationResult
ExportResult = _mig.ExportResult


# ===================================================================
# Representative legacy data
# ===================================================================

def _make_legacy_region_spec():
    """Build a representative legacy REGION_SPEC with 2 active panels."""
    return {
        "version": 1,
        "canvas": {"width": 832, "height": 1216},
        "panel_count": 3,
        "global_prompt": "manga page, monochrome",
        "global_negative_prompt": "bad anatomy, color",
        "regions": [
            {
                "id": 1,
                "enabled": True,
                "x": 0.05, "y": 0.05, "w": 0.9, "h": 0.4,
                "prompt": "classroom, two people talking",
                "negative_prompt": "empty room",
                "characters": [
                    {
                        "character_id": "char_alice",
                        "enabled": True,
                        "prompt_override": "annoyed, looking at Bob",
                        "negative_prompt_override": "happy",
                        "area": {"x": 0.05, "y": 0.15, "w": 0.40, "h": 0.75},
                        "shot_type": "half_body",
                        "pose_preset": "facing_right",
                        "metadata": {},
                    },
                    {
                        "character_id": "char_bob",
                        "enabled": True,
                        "prompt_override": "smiling, waving",
                        "negative_prompt_override": "",
                        "area": {"x": 0.55, "y": 0.15, "w": 0.40, "h": 0.75},
                        "metadata": {},
                    },
                ],
            },
            {
                "id": 2,
                "enabled": True,
                "x": 0.05, "y": 0.5, "w": 0.9, "h": 0.45,
                "prompt": "outdoor park, sunny day",
                "negative_prompt": "",
                "characters": [],
            },
            {
                "id": 3,
                "enabled": False,
                "x": 0.05, "y": 0.05, "w": 0.9, "h": 0.9,
                "prompt": "",
                "negative_prompt": "",
                "characters": [],
            },
        ],
    }


def _make_legacy_cast_spec():
    """Build a representative legacy CAST_SPEC."""
    return {
        "version": 1,
        "characters": [
            {
                "id": "char_alice",
                "name": "Alice",
                "enabled": True,
                "prompt": "1girl, blonde twin tails, blue eyes, school uniform",
                "negative_prompt": "bad anatomy",
                "loras": [
                    {"name": "alice_costume", "model_weight": 0.8,
                     "clip_weight": 0.6, "enabled": True, "metadata": {}}
                ],
                "metadata": {"role": "protagonist"},
            },
            {
                "id": "char_bob",
                "name": "Bob",
                "enabled": True,
                "prompt": "1boy, short brown hair, green eyes",
                "negative_prompt": "",
                "loras": [],
                "metadata": {},
            },
        ],
    }


class TestFixture9_LegacyImport(unittest.TestCase):
    """Fixture 9: Legacy REGION_SPEC + CAST_SPEC → new document."""

    def setUp(self):
        self.region_spec = _make_legacy_region_spec()
        self.cast_spec = _make_legacy_cast_spec()
        self.result = import_from_legacy(self.region_spec, self.cast_spec)
        self.doc = self.result.document

    def test_import_produces_valid_document(self):
        validation = validate_document(self.doc)
        self.assertTrue(validation.valid, f"Errors: {validation.errors}")

    def test_schema_identity(self):
        self.assertEqual(self.doc["schema_id"], SCHEMA_ID)
        self.assertEqual(self.doc["schema_version"], SCHEMA_VERSION)

    def test_page_resolution(self):
        page = self.doc["pages"][0]
        self.assertEqual(page["width_px"], 832)
        self.assertEqual(page["height_px"], 1216)

    def test_global_prompts(self):
        page = self.doc["pages"][0]
        self.assertEqual(page["style_prompt"], "manga page, monochrome")
        self.assertEqual(page["style_negative_prompt"], "bad anatomy, color")

    def test_cast_imported(self):
        page = self.doc["pages"][0]
        self.assertEqual(len(page["cast"]), 2)
        alice = next(c for c in page["cast"] if c["cast_id"] == "char_alice")
        self.assertEqual(alice["display_name"], "Alice")
        self.assertIn("blonde twin tails", alice["identity_prompt"])

    def test_active_panels_become_scenes_and_frames(self):
        page = self.doc["pages"][0]
        # 2 active panels → 2 scenes + 2 frames
        self.assertEqual(len(page["scenes"]), 2)
        self.assertEqual(len(page["visual_frames"]), 2)
        # Disabled panel 3 is NOT imported
        scene_ids = [s["scene_id"] for s in page["scenes"]]
        self.assertNotIn("legacy_scene_3", scene_ids)

    def test_scene_and_frame_ids_are_distinct(self):
        page = self.doc["pages"][0]
        scene_ids = {s["scene_id"] for s in page["scenes"]}
        frame_ids = {f["frame_id"] for f in page["visual_frames"]}
        self.assertTrue(scene_ids.isdisjoint(frame_ids))

    def test_input_mode_detection(self):
        page = self.doc["pages"][0]
        scene_1 = next(s for s in page["scenes"]
                       if s["scene_id"] == "legacy_scene_1")
        scene_2 = next(s for s in page["scenes"]
                       if s["scene_id"] == "legacy_scene_2")
        self.assertEqual(scene_1["input_mode"], "cast")   # has characters
        self.assertEqual(scene_2["input_mode"], "simple")  # no characters

    def test_character_instances_created(self):
        page = self.doc["pages"][0]
        self.assertEqual(len(page["character_instances"]), 2)
        alice_inst = next(
            i for i in page["character_instances"]
            if i["cast_id"] == "char_alice"
        )
        self.assertEqual(alice_inst["scene_id"], "legacy_scene_1")
        self.assertEqual(alice_inst["acting_prompt"], "annoyed, looking at Bob")

    def test_shot_type_preserved_in_metadata(self):
        page = self.doc["pages"][0]
        alice_inst = next(
            i for i in page["character_instances"]
            if i["cast_id"] == "char_alice"
        )
        self.assertEqual(alice_inst["metadata"].get("shot_type"), "half_body")
        self.assertEqual(alice_inst["metadata"].get("pose_preset"), "facing_right")

    def test_field_mapping_table_populated(self):
        self.assertGreater(len(self.result.field_mapping_table), 0)
        # Check a representative mapping
        has_scene_mapping = any(
            "legacy_scene_1" in m.get("new_field", "")
            for m in self.result.field_mapping_table
        )
        self.assertTrue(has_scene_mapping)


class TestCoordinateTransform(unittest.TestCase):
    """Numeric verification of KOMA-local → page-normalized transform."""

    def test_basic_transform(self):
        """Panel at (0.1, 0.2, 0.6, 0.5), character at local (0.25, 0.1, 0.5, 0.8)."""
        panel_geom = {"x": 0.1, "y": 0.2, "w": 0.6, "h": 0.5}
        local_area = {"x": 0.25, "y": 0.1, "w": 0.5, "h": 0.8}

        page_area = koma_local_to_page_normalized(local_area, panel_geom)

        # page_x = 0.1 + 0.25 * 0.6 = 0.1 + 0.15 = 0.25
        # page_y = 0.2 + 0.1 * 0.5 = 0.2 + 0.05 = 0.25
        # page_w = 0.5 * 0.6 = 0.3
        # page_h = 0.8 * 0.5 = 0.4
        self.assertAlmostEqual(page_area["x"], 0.25, places=3)
        self.assertAlmostEqual(page_area["y"], 0.25, places=3)
        self.assertAlmostEqual(page_area["w"], 0.3, places=3)
        self.assertAlmostEqual(page_area["h"], 0.4, places=3)

    def test_roundtrip_transform(self):
        """Forward + inverse should return original values."""
        panel_geom = {"x": 0.1, "y": 0.2, "w": 0.6, "h": 0.5}
        local_area = {"x": 0.25, "y": 0.1, "w": 0.5, "h": 0.8}

        page_area = koma_local_to_page_normalized(local_area, panel_geom)
        restored = page_normalized_to_koma_local(page_area, panel_geom)

        self.assertAlmostEqual(restored["x"], 0.25, places=3)
        self.assertAlmostEqual(restored["y"], 0.1, places=3)
        self.assertAlmostEqual(restored["w"], 0.5, places=3)
        self.assertAlmostEqual(restored["h"], 0.8, places=3)

    def test_full_panel_identity(self):
        """Character covering full panel → page coordinates == panel coordinates."""
        panel_geom = {"x": 0.1, "y": 0.2, "w": 0.6, "h": 0.5}
        local_area = {"x": 0.0, "y": 0.0, "w": 1.0, "h": 1.0}

        page_area = koma_local_to_page_normalized(local_area, panel_geom)

        self.assertAlmostEqual(page_area["x"], 0.1, places=3)
        self.assertAlmostEqual(page_area["y"], 0.2, places=3)
        self.assertAlmostEqual(page_area["w"], 0.6, places=3)
        self.assertAlmostEqual(page_area["h"], 0.5, places=3)


class TestLegacyImportRoundTrip(unittest.TestCase):
    """Import → Export → verify equivalence."""

    def test_import_export_roundtrip(self):
        region_spec = _make_legacy_region_spec()
        cast_spec = _make_legacy_cast_spec()

        # Import
        import_result = import_from_legacy(region_spec, cast_spec)
        doc = import_result.document

        # Export
        export_result = export_to_legacy(doc, page_index=0)
        self.assertEqual(len(export_result.unsupported), 0)

        # Verify CAST preserved
        orig_ids = {c["id"] for c in cast_spec["characters"]}
        exported_ids = {c["id"] for c in export_result.cast_spec["characters"]}
        self.assertEqual(orig_ids, exported_ids)

        # Verify active panels preserved
        exported_active = [
            r for r in export_result.region_spec["regions"]
            if r["enabled"]
        ]
        self.assertEqual(len(exported_active), 2)

        # Verify prompts
        exported_r1 = export_result.region_spec["regions"][0]
        self.assertEqual(exported_r1["prompt"], "classroom, two people talking")

    def test_export_preserves_global_prompts(self):
        region_spec = _make_legacy_region_spec()
        cast_spec = _make_legacy_cast_spec()

        import_result = import_from_legacy(region_spec, cast_spec)
        export_result = export_to_legacy(import_result.document)

        self.assertEqual(
            export_result.region_spec["global_prompt"],
            "manga page, monochrome",
        )


class TestLossyConversionDiagnostics(unittest.TestCase):
    """Lossy conversions emit warnings."""

    def test_dummy_geometry_warning(self):
        """Import with PanelContentEditor dummy geometry emits warning."""
        region_spec = {
            "version": 1,
            "canvas": {"width": 832, "height": 1216},
            "panel_count": 1,
            "global_prompt": "",
            "global_negative_prompt": "",
            "regions": [
                {
                    "id": 1, "enabled": True,
                    "x": 0.05, "y": 0.05, "w": 0.9, "h": 0.9,
                    "prompt": "test",
                    "negative_prompt": "",
                    "characters": [
                        {
                            "character_id": "char_alice",
                            "enabled": True,
                            "area": {"x": 0.1, "y": 0.1, "w": 0.3, "h": 0.6},
                            "prompt_override": "",
                            "metadata": {},
                        }
                    ],
                },
            ],
        }
        cast_spec = {
            "version": 1,
            "characters": [{"id": "char_alice", "name": "Alice",
                            "enabled": True, "prompt": "1girl"}],
        }
        result = import_from_legacy(region_spec, cast_spec)
        self.assertTrue(
            any("dummy" in w.lower() for w in result.warnings),
            f"Expected dummy geometry warning, got: {result.warnings}"
        )


class TestExportFailClosed(unittest.TestCase):
    """Export fails closed for unsupported features."""

    def test_too_many_scenes_rejected(self):
        """More than 6 scenes → fail closed."""
        page = create_page(832, 1216, page_id="page_1")
        for i in range(7):
            page["scenes"].append(create_scene(scene_id=f"s{i}", order=i))
        doc = create_document(pages=[page])

        result = export_to_legacy(doc)
        self.assertGreater(len(result.unsupported), 0)
        self.assertTrue(any("6" in u for u in result.unsupported))


class TestWorkflowStructuralRegression(unittest.TestCase):
    """Existing workflow JSON files are not modified by M0."""

    def test_workflow_files_not_modified(self):
        """
        Structural regression: verify that workflow JSON files exist and
        are valid JSON (we haven't broken them). We do NOT modify them.
        """
        workflows_dir = os.path.join(
            os.path.dirname(__file__), "..", "ComfyUIPortable", "workflows"
        )
        # Resolve relative to scripts/
        workflows_dir = os.path.abspath(os.path.join(
            os.path.dirname(__file__), "..", "workflows"
        ))

        if not os.path.isdir(workflows_dir):
            self.skipTest(f"Workflows directory not found: {workflows_dir}")

        json_files = glob.glob(os.path.join(workflows_dir, "**", "*.json"), recursive=True)
        if not json_files:
            self.skipTest("No workflow JSON files found")

        for filepath in json_files:
            with open(filepath, "r", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                    self.assertIsInstance(data, dict,
                                         f"{filepath} is not a dict")
                except json.JSONDecodeError as e:
                    self.fail(f"Invalid JSON in {filepath}: {e}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
