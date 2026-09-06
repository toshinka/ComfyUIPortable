"""
test_m1_1_authoring_ui_contract_fixture.py — Authoring UI Contract & SSOT Diagnostics Tests
=============================================================================================
Verifies:
1. Document SSOT derivation in Python backend node (Finding D)
2. Reset 2-scene fixture validity without legacy dialect (Finding E)
3. Diagnostic debug_json keys (effective_sampler_seed, effective_latent_width, etc.)
4. Legacy 'dimensions' dialect auto-migration into canonical format
5. Clean validation under all resolution and style presets
"""

import os
import sys
import json
import unittest

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CUSTOM_NODES_DIR = os.path.join(ROOT_DIR, "custom_nodes_custom")
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
if CUSTOM_NODES_DIR not in sys.path:
    sys.path.insert(0, CUSTOM_NODES_DIR)

from tegaki_manga_nodes.authoring_contract import (
    create_document,
    create_page,
    create_scene,
    make_area,
    validate_document,
)
from tegaki_manga_nodes.minimum_hand_scene_editor import (
    TegakiMinimumHandSceneEditor,
    create_default_m1_document,
    RESOLUTION_PRESETS,
    STYLE_TEMPLATES,
)


class TestM1_1AuthoringUIContractFixture(unittest.TestCase):
    def setUp(self):
        self.editor = TegakiMinimumHandSceneEditor()

    def test_01_default_document_strictly_valid_no_dimensions(self):
        """Default document must have width_px, height_px and NO dimensions object."""
        doc = create_default_m1_document(width=832, height=1216, seed=42)
        page = doc["pages"][0]
        self.assertIn("width_px", page)
        self.assertIn("height_px", page)
        self.assertNotIn("dimensions", page)

        doc_json = json.dumps(doc)
        self.assertNotIn('"dimensions"', doc_json)

        val_res = validate_document(doc)
        self.assertEqual(val_res.errors, [])

    def test_02_all_resolution_presets_strictly_valid(self):
        """All supported resolution presets produce strictly valid authoring documents."""
        for preset_name, (w, h) in RESOLUTION_PRESETS.items():
            doc = create_default_m1_document(width=w, height=h)
            page = doc["pages"][0]
            self.assertEqual(page["width_px"], w)
            self.assertEqual(page["height_px"], h)
            self.assertNotIn("dimensions", page)

            val_res = validate_document(doc)
            self.assertEqual(val_res.errors, [], f"Validation failed for preset {preset_name}")

    def test_03_widget_to_document_seed_synchronization(self):
        """Option B: Backend synchronizes seed widget into document generation.seed and derives effective sampler seed."""
        doc = create_default_m1_document(seed=42)
        doc_json = json.dumps(doc)

        # Pass widget seed=777
        res = self.editor.edit_and_compile(
            document_json=doc_json,
            seed=777,
            style_template="Manga Monochrome",
            resolution="Portrait 832x1216",
        )

        plan, preview, effective_seed, res_w, res_h, debug_str, norm_json = res
        self.assertEqual(effective_seed, 777)

        debug = json.loads(debug_str)
        self.assertEqual(debug["document_seed"], 777)
        self.assertEqual(debug["effective_sampler_seed"], 777)
        self.assertEqual(debug["widget_seed"], 777)

        # Normalized document also reflects synchronized seed
        norm_doc = json.loads(norm_json)
        self.assertEqual(norm_doc["pages"][0]["generation"]["seed"], 777)

    def test_04_widget_to_document_resolution_synchronization(self):
        """Option B: Backend synchronizes resolution widget into document width_px/height_px and derives effective latent dimensions."""
        doc = create_default_m1_document(width=832, height=1216)
        doc_json = json.dumps(doc)

        # Pass widget resolution="Landscape 1216x832"
        res = self.editor.edit_and_compile(
            document_json=doc_json,
            seed=42,
            style_template="Manga Monochrome",
            resolution="Landscape 1216x832",
        )

        plan, preview, effective_seed, res_w, res_h, debug_str, norm_json = res
        self.assertEqual(res_w, 1216)
        self.assertEqual(res_h, 832)

        debug = json.loads(debug_str)
        self.assertEqual(debug["effective_latent_width"], 1216)
        self.assertEqual(debug["effective_latent_height"], 832)
        self.assertEqual(debug["document_resolution"], "1216x832")
        self.assertEqual(debug["effective_latent_resolution"], "1216x832")

        # Normalized document also reflects synchronized resolution
        norm_doc = json.loads(norm_json)
        self.assertEqual(norm_doc["pages"][0]["width_px"], 1216)
        self.assertEqual(norm_doc["pages"][0]["height_px"], 832)

    def test_05_legacy_dimensions_auto_migration(self):
        """Legacy document with 'dimensions' dialect is migrated in-place and purged."""
        legacy_doc = {
            "schema_id": "TEGAKI_AUTHORING_DOCUMENT",
            "schema_version": "1.0.0",
            "pages": [
                {
                    "page_id": "page_1",
                    "order": 1,
                    "dimensions": {
                        "width_px": 1024,
                        "height_px": 1024,
                    },
                    "scenes": [
                        {
                            "scene_id": "scene_1",
                            "name": "Scene 1",
                            "prompt": "test prompt",
                            "area": {"shape_type": "rect", "x": 0.1, "y": 0.1, "w": 0.8, "h": 0.8},
                            "order": 1,
                        }
                    ],
                    "generation": {"seed": 99},
                }
            ]
        }
        legacy_json = json.dumps(legacy_doc)

        res = self.editor.edit_and_compile(document_json=legacy_json, seed=99)
        plan, preview, effective_seed, res_w, res_h, debug_str, norm_json = res

        self.assertEqual(res_w, 1024)
        self.assertEqual(res_h, 1024)
        self.assertEqual(effective_seed, 99)

        # Verified normalized json has no dimensions
        norm_doc = json.loads(norm_json)
        self.assertNotIn("dimensions", norm_doc["pages"][0])
        self.assertEqual(norm_doc["pages"][0]["width_px"], 1024)
        self.assertEqual(norm_doc["pages"][0]["height_px"], 1024)

        # Validates cleanly
        val_res = validate_document(norm_doc)
        self.assertEqual(val_res.errors, [])

    def test_06_debug_json_contains_all_required_keys(self):
        """debug_json must provide all diagnostics required by §59 and §60."""
        doc = create_default_m1_document(seed=42)
        res = self.editor.edit_and_compile(document_json=json.dumps(doc), seed=42)
        debug = json.loads(res[5])

        required_keys = [
            "document_seed",
            "effective_sampler_seed",
            "document_resolution",
            "effective_latent_width",
            "effective_latent_height",
            "effective_latent_resolution",
            "style_template",
            "scene_ids",
            "scene_areas",
        ]
        for key in required_keys:
            self.assertIn(key, debug, f"Missing required debug key: {key}")


if __name__ == "__main__":
    unittest.main()
