import unittest
import copy
import sys
import os
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

_ac = _import_module(
    "authoring_contract",
    os.path.join(_NODES_DIR, "authoring_contract.py"),
)

create_document = _ac.create_document
create_page = _ac.create_page
create_cast_entry = _ac.create_cast_entry
validate_document = _ac.validate_document
validate_reference_asset_reference = _ac.validate_reference_asset_reference
to_json = _ac.to_json
from_json = _ac.from_json



class TestCastReferenceContract(unittest.TestCase):
    def test_cast_without_reference_asset_is_valid(self):
        doc = create_document()
        page = create_page(832, 1216)
        cast = create_cast_entry(display_name="Alice", identity_prompt="1girl, blonde hair")
        page["cast"].append(cast)
        doc["pages"].append(page)

        result = validate_document(doc)
        self.assertTrue(result.valid, f"Expected valid doc, got errors: {result.errors}")

    def test_cast_with_valid_reference_asset_validates(self):
        doc = create_document()
        page = create_page(832, 1216)
        cast = create_cast_entry(
            display_name="Alice",
            identity_prompt="1girl, blonde hair",
            reference_asset="tegaki_manga_references/ref_a1b2c3d4e5f60718.png"
        )
        page["cast"].append(cast)
        doc["pages"].append(page)

        result = validate_document(doc)
        self.assertTrue(result.valid, f"Expected valid doc, got errors: {result.errors}")

    def test_cast_reference_asset_traversal_rejected(self):
        doc = create_document()
        page = create_page(832, 1216)
        cast = create_cast_entry(
            display_name="Alice",
            reference_asset="tegaki_manga_references/../secret.png"
        )
        page["cast"].append(cast)
        doc["pages"].append(page)

        result = validate_document(doc)
        self.assertFalse(result.valid)
        self.assertTrue(any("invalid path segment" in err or "traversal" in err for err in result.errors))

    def test_cast_reference_asset_absolute_rejected(self):
        doc = create_document()
        page = create_page(832, 1216)
        cast = create_cast_entry(
            display_name="Alice",
            reference_asset="C:/Users/MAX/Desktop/ref.png"
        )
        page["cast"].append(cast)
        doc["pages"].append(page)

        result = validate_document(doc)
        self.assertFalse(result.valid)
        self.assertTrue(any("must be relative" in err or "drive prefix" in err for err in result.errors))

    def test_cast_reference_asset_wrong_namespace_rejected(self):
        doc = create_document()
        page = create_page(832, 1216)
        cast = create_cast_entry(
            display_name="Alice",
            reference_asset="tegaki_manga_guides/guide.png"
        )
        page["cast"].append(cast)
        doc["pages"].append(page)

        result = validate_document(doc)
        self.assertFalse(result.valid)
        self.assertTrue(any("tegaki_manga_references/" in err for err in result.errors))

    def test_cast_reference_asset_unsupported_extension_rejected(self):
        doc = create_document()
        page = create_page(832, 1216)
        cast = create_cast_entry(
            display_name="Alice",
            reference_asset="tegaki_manga_references/malicious.exe"
        )
        page["cast"].append(cast)
        doc["pages"].append(page)

        result = validate_document(doc)
        self.assertFalse(result.valid)
        self.assertTrue(any("extension must be one of" in err for err in result.errors))

    def test_cast_reference_roundtrip_preserves_reference_asset(self):
        doc = create_document()
        page = create_page(832, 1216)
        cast = create_cast_entry(
            display_name="Alice",
            identity_prompt="1girl",
            reference_asset="tegaki_manga_references/ref_1234567890abcdef.webp"
        )
        page["cast"].append(cast)
        doc["pages"].append(page)

        json_str = to_json(doc)
        loaded = from_json(json_str)

        self.assertEqual(
            loaded["pages"][0]["cast"][0]["reference_asset"],
            "tegaki_manga_references/ref_1234567890abcdef.webp"
        )
        result = validate_document(loaded)
        self.assertTrue(result.valid)

    def test_older_document_without_reference_asset_compatible(self):
        doc = {
            "schema_id": "TEGAKI_AUTHORING_DOCUMENT",
            "schema_version": "1.0.0",
            "pages": [
                {
                    "page_id": "page_old",
                    "width_px": 832,
                    "height_px": 1216,
                    "scenes": [],
                    "visual_frames": [],
                    "cast": [
                        {
                            "cast_id": "cast_legacy",
                            "display_name": "Old Hero",
                            "identity_prompt": "hero with cape",
                            "negative_prompt": "",
                            "loras": []
                        }
                    ],
                    "character_instances": [],
                    "guides": []
                }
            ],
            "metadata": {}
        }
        result = validate_document(doc)
        self.assertTrue(result.valid, f"Legacy doc should validate, got: {result.errors}")


if __name__ == "__main__":
    unittest.main()
