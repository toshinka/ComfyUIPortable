"""
test_m0_authoring_contract.py — M0 Authoring Contract Fixtures 0-4, 10-12
==========================================================================
Pure Python tests. No ComfyUI server required.
"""
import sys
import os
import json
import copy
import unittest
import math
import importlib.util

# Direct file import to avoid __init__.py pulling in ComfyUI runtime
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

# authoring_contract has no intra-package dependencies
_ac = _import_module(
    "authoring_contract",
    os.path.join(_NODES_DIR, "authoring_contract.py"),
)

SCHEMA_ID = _ac.SCHEMA_ID
SCHEMA_VERSION = _ac.SCHEMA_VERSION
KNOWN_VERSIONS = _ac.KNOWN_VERSIONS
create_document = _ac.create_document
create_page = _ac.create_page
create_scene = _ac.create_scene
create_visual_frame = _ac.create_visual_frame
create_cast_entry = _ac.create_cast_entry
create_character_instance = _ac.create_character_instance
create_guide = _ac.create_guide
make_area = _ac.make_area
validate_document = _ac.validate_document
validate_area = _ac.validate_area
generate_id = _ac.generate_id
to_dict = _ac.to_dict
to_json = _ac.to_json
from_dict = _ac.from_dict
from_json = _ac.from_json
ValidationResult = _ac.ValidationResult


class TestFixture0_EmptyDocument(unittest.TestCase):
    """Fixture 0: Empty editable state — 0 Scenes, 0 Frames, 0 CAST."""

    def test_empty_document_is_valid(self):
        page = create_page(832, 1216)
        doc = create_document(pages=[page])

        result = validate_document(doc)
        self.assertTrue(result.valid, f"Errors: {result.errors}")
        self.assertEqual(len(doc["pages"][0]["scenes"]), 0)
        self.assertEqual(len(doc["pages"][0]["visual_frames"]), 0)
        self.assertEqual(len(doc["pages"][0]["cast"]), 0)
        self.assertEqual(len(doc["pages"][0]["character_instances"]), 0)

    def test_empty_document_serializable(self):
        page = create_page(832, 1216)
        doc = create_document(pages=[page])

        json_str = to_json(doc)
        reloaded = from_json(json_str)
        self.assertEqual(reloaded["schema_id"], SCHEMA_ID)
        self.assertEqual(reloaded["schema_version"], SCHEMA_VERSION)
        self.assertEqual(len(reloaded["pages"][0]["scenes"]), 0)

    def test_validator_does_not_inject_default_scene(self):
        """Validator must NOT add a full-page scene when none exists."""
        page = create_page(832, 1216)
        doc = create_document(pages=[page])
        result = validate_document(doc)
        self.assertTrue(result.valid)
        self.assertEqual(len(result.normalized_document["pages"][0]["scenes"]), 0)


class TestFixture1_TwoScenesAndFrames(unittest.TestCase):
    """Fixture 1: Two independent Scenes + Two Frames with different geometry."""

    def setUp(self):
        page = create_page(832, 1216, page_id="page_1")
        page["scenes"].append(create_scene(
            name="Scene A", prompt="classroom",
            area=make_area(0.0, 0.0, 0.5, 0.5),
            order=1, scene_id="scene_a",
        ))
        page["scenes"].append(create_scene(
            name="Scene B", prompt="hallway",
            area=make_area(0.5, 0.0, 0.5, 0.5),
            order=2, scene_id="scene_b",
        ))
        page["visual_frames"].append(create_visual_frame(
            area=make_area(0.0, 0.0, 1.0, 0.5),
            order=1, frame_id="frame_1",
        ))
        page["visual_frames"].append(create_visual_frame(
            area=make_area(0.0, 0.5, 1.0, 0.5),
            order=2, frame_id="frame_2",
        ))
        self.doc = create_document(pages=[page])

    def test_valid(self):
        result = validate_document(self.doc)
        self.assertTrue(result.valid, f"Errors: {result.errors}")

    def test_scene_and_frame_ids_are_distinct(self):
        page = self.doc["pages"][0]
        scene_ids = {s["scene_id"] for s in page["scenes"]}
        frame_ids = {f["frame_id"] for f in page["visual_frames"]}
        self.assertEqual(len(scene_ids), 2)
        self.assertEqual(len(frame_ids), 2)
        self.assertTrue(scene_ids.isdisjoint(frame_ids))

    def test_scene_geometry_differs_from_frame_geometry(self):
        page = self.doc["pages"][0]
        scene_a_area = page["scenes"][0]["area"]
        frame_1_shape = page["visual_frames"][0]["shape"]
        # Scene A is left half, Frame 1 is full width top
        self.assertNotEqual(scene_a_area["w"], frame_1_shape["w"])

    def test_separate_arrays(self):
        page = self.doc["pages"][0]
        self.assertIsInstance(page["scenes"], list)
        self.assertIsInstance(page["visual_frames"], list)
        self.assertIsNot(page["scenes"], page["visual_frames"])


class TestFixture2_OverlappingScenes(unittest.TestCase):
    """Fixture 2: Two scenes with overlapping geometry."""

    def test_overlap_preserved_on_roundtrip(self):
        page = create_page(832, 1216, page_id="page_1")
        page["scenes"].append(create_scene(
            name="A", area=make_area(0.1, 0.1, 0.6, 0.6),
            order=1, scene_id="scene_a",
        ))
        page["scenes"].append(create_scene(
            name="B", area=make_area(0.3, 0.3, 0.6, 0.6),
            order=2, scene_id="scene_b",
        ))
        doc = create_document(pages=[page])

        # Validate
        result = validate_document(doc)
        self.assertTrue(result.valid, f"Errors: {result.errors}")

        # Roundtrip
        json_str = to_json(doc)
        reloaded = from_json(json_str)

        r_scenes = reloaded["pages"][0]["scenes"]
        self.assertEqual(len(r_scenes), 2)
        self.assertAlmostEqual(r_scenes[0]["area"]["x"], 0.1, places=3)
        self.assertAlmostEqual(r_scenes[1]["area"]["x"], 0.3, places=3)
        self.assertEqual(r_scenes[0]["order"], 1)
        self.assertEqual(r_scenes[1]["order"], 2)


class TestFixture3_SameCastRepeated(unittest.TestCase):
    """Fixture 3: Same CAST member appearing in 3 different scenes."""

    def test_same_cast_multiple_instances(self):
        page = create_page(832, 1216, page_id="page_1")

        # One CAST member
        page["cast"].append(create_cast_entry(
            display_name="Alice",
            identity_prompt="1girl, blonde hair",
            cast_id="cast_alice",
        ))

        # Three scenes
        for i, sid in enumerate(["scene_a", "scene_b", "scene_c"]):
            page["scenes"].append(create_scene(
                name=f"Scene {sid[-1].upper()}",
                input_mode="cast",
                area=make_area(0.0, i * 0.33, 1.0, 0.33),
                order=i + 1,
                scene_id=sid,
            ))

        # Alice appears in all three scenes with different instance IDs
        for i, sid in enumerate(["scene_a", "scene_b", "scene_c"]):
            page["character_instances"].append(create_character_instance(
                cast_id="cast_alice",
                scene_id=sid,
                area=make_area(0.1, i * 0.33 + 0.05, 0.3, 0.25),
                acting_prompt=f"acting in scene {i+1}",
                instance_id=f"inst_alice_{i+1}",
            ))

        doc = create_document(pages=[page])
        result = validate_document(doc)
        self.assertTrue(result.valid, f"Errors: {result.errors}")

        # All instance_ids are different
        inst_ids = [
            i["instance_id"]
            for i in page["character_instances"]
        ]
        self.assertEqual(len(inst_ids), 3)
        self.assertEqual(len(set(inst_ids)), 3)

        # All cast_ids are the same
        cast_ids = [
            i["cast_id"]
            for i in page["character_instances"]
        ]
        self.assertEqual(set(cast_ids), {"cast_alice"})


class TestFixture4_MixedModes(unittest.TestCase):
    """Fixture 4: Mixed simple/cast modes on same page."""

    def test_mixed_modes(self):
        page = create_page(832, 1216, page_id="page_1")

        page["cast"].append(create_cast_entry(
            display_name="Alice", cast_id="cast_alice",
        ))

        page["scenes"].append(create_scene(
            name="Simple Scene", input_mode="simple",
            prompt="a girl walking, 1girl, blonde",
            scene_id="scene_simple",
            order=1,
        ))
        page["scenes"].append(create_scene(
            name="Cast Scene", input_mode="cast",
            prompt="classroom background",
            scene_id="scene_cast",
            order=2,
        ))
        page["scenes"].append(create_scene(
            name="Another Simple", input_mode="simple",
            prompt="a landscape",
            scene_id="scene_simple2",
            order=3,
        ))

        page["character_instances"].append(create_character_instance(
            cast_id="cast_alice",
            scene_id="scene_cast",
            instance_id="inst_alice_cast",
        ))

        doc = create_document(pages=[page])
        result = validate_document(doc)
        self.assertTrue(result.valid, f"Errors: {result.errors}")

        modes = [s["input_mode"] for s in page["scenes"]]
        self.assertEqual(modes, ["simple", "cast", "simple"])


class TestFixture10_InvalidReferences(unittest.TestCase):
    """Fixture 10: Invalid references must be rejected."""

    def _make_base_doc(self):
        page = create_page(832, 1216, page_id="page_1")
        page["cast"].append(create_cast_entry(cast_id="cast_alice"))
        page["scenes"].append(create_scene(scene_id="scene_a"))
        return create_document(pages=[page])

    def test_missing_cast_id(self):
        doc = self._make_base_doc()
        doc["pages"][0]["character_instances"].append({
            "instance_id": "inst_1",
            "cast_id": "nonexistent_cast",
            "scene_id": "scene_a",
            "area": make_area(0.1, 0.1, 0.3, 0.3),
            "acting_prompt": "",
            "negative_prompt_override": "",
            "order": 0,
            "metadata": {},
        })
        result = validate_document(doc)
        self.assertFalse(result.valid)
        self.assertTrue(any("nonexistent_cast" in e for e in result.errors))

    def test_missing_scene_id(self):
        doc = self._make_base_doc()
        doc["pages"][0]["character_instances"].append({
            "instance_id": "inst_1",
            "cast_id": "cast_alice",
            "scene_id": "nonexistent_scene",
            "area": make_area(0.1, 0.1, 0.3, 0.3),
            "acting_prompt": "",
            "negative_prompt_override": "",
            "order": 0,
            "metadata": {},
        })
        result = validate_document(doc)
        self.assertFalse(result.valid)
        self.assertTrue(any("nonexistent_scene" in e for e in result.errors))

    def test_duplicate_stable_id(self):
        doc = self._make_base_doc()
        page = doc["pages"][0]
        page["scenes"].append(create_scene(scene_id="scene_a"))  # duplicate!
        result = validate_document(doc)
        self.assertFalse(result.valid)
        self.assertTrue(any("duplicate" in e.lower() for e in result.errors))

    def test_nan_geometry(self):
        doc = self._make_base_doc()
        doc["pages"][0]["scenes"][0]["area"] = {
            "shape_type": "rect",
            "x": float("nan"), "y": 0.1, "w": 0.3, "h": 0.3,
        }
        result = validate_document(doc)
        self.assertFalse(result.valid)
        self.assertTrue(any("finite" in e.lower() or "nan" in e.lower()
                            for e in result.errors))

    def test_invalid_schema_version(self):
        doc = self._make_base_doc()
        doc["schema_version"] = "99.0.0"
        result = validate_document(doc)
        self.assertFalse(result.valid)
        self.assertTrue(any("unknown" in e.lower() or "fail closed" in e.lower()
                            for e in result.errors))


class TestFixture11_UnknownFieldRoundTrip(unittest.TestCase):
    """Fixture 11: Unknown fields within known version are preserved."""

    def test_unknown_fields_preserved(self):
        page = create_page(832, 1216, page_id="page_1")
        page["future_vendor_extension"] = {"key": "value", "nested": [1, 2, 3]}
        page["scenes"].append(create_scene(scene_id="scene_a"))
        page["scenes"][0]["future_ai_annotation"] = "some annotation"

        doc = create_document(pages=[page])
        doc["custom_global_field"] = 42

        # Validate — should pass
        result = validate_document(doc)
        self.assertTrue(result.valid, f"Errors: {result.errors}")

        # Roundtrip via JSON
        json_str = to_json(doc)
        reloaded = from_json(json_str)

        # Unknown fields preserved
        self.assertEqual(reloaded["custom_global_field"], 42)
        self.assertEqual(
            reloaded["pages"][0]["future_vendor_extension"],
            {"key": "value", "nested": [1, 2, 3]},
        )
        self.assertEqual(
            reloaded["pages"][0]["scenes"][0]["future_ai_annotation"],
            "some annotation",
        )

    def test_edit_known_field_preserves_unknown(self):
        """Edit an unrelated known field; unknown fields survive."""
        page = create_page(832, 1216, page_id="page_1")
        page["scenes"].append(create_scene(scene_id="scene_a", prompt="original"))
        page["scenes"][0]["vendor_x"] = "keep_me"

        doc = create_document(pages=[page])

        # Serialize
        json_str = to_json(doc)
        reloaded = from_json(json_str)

        # Edit known field
        reloaded["pages"][0]["scenes"][0]["prompt"] = "modified"

        # Re-serialize
        json_str2 = to_json(reloaded)
        final = from_json(json_str2)

        self.assertEqual(final["pages"][0]["scenes"][0]["prompt"], "modified")
        self.assertEqual(final["pages"][0]["scenes"][0]["vendor_x"], "keep_me")


class TestFixture12_UnknownNewerSchema(unittest.TestCase):
    """Fixture 12: Unknown newer schema version fails closed."""

    def test_from_dict_rejects_newer_version(self):
        data = {
            "schema_id": SCHEMA_ID,
            "schema_version": "99.0.0",
            "pages": [],
        }
        with self.assertRaises(ValueError) as cm:
            from_dict(data)
        self.assertIn("Unknown schema_version", str(cm.exception))
        self.assertIn("fail closed", str(cm.exception).lower())

    def test_from_json_rejects_newer_version(self):
        data = {
            "schema_id": SCHEMA_ID,
            "schema_version": "99.0.0",
            "pages": [],
        }
        with self.assertRaises(ValueError):
            from_json(json.dumps(data))

    def test_validate_rejects_newer_version(self):
        doc = {
            "schema_id": SCHEMA_ID,
            "schema_version": "99.0.0",
            "pages": [],
        }
        result = validate_document(doc)
        self.assertFalse(result.valid)

    def test_wrong_schema_id_rejected(self):
        data = {
            "schema_id": "SOME_OTHER_APP",
            "schema_version": SCHEMA_VERSION,
            "pages": [],
        }
        with self.assertRaises(ValueError):
            from_dict(data)


class TestSerializationRoundTrip(unittest.TestCase):
    """Full serialization round-trip preserves all semantic content."""

    def test_full_roundtrip(self):
        page = create_page(832, 1216, page_id="page_1",
                           style_prompt="manga style",
                           style_negative_prompt="color photo")
        page["cast"].append(create_cast_entry(
            display_name="Alice", identity_prompt="1girl blonde",
            cast_id="alice",
        ))
        page["scenes"].append(create_scene(
            name="S1", prompt="classroom", input_mode="cast",
            area=make_area(0.0, 0.0, 0.5, 1.0),
            scene_id="s1", order=1,
        ))
        page["visual_frames"].append(create_visual_frame(
            area=make_area(0.0, 0.0, 1.0, 0.5),
            frame_id="f1", order=1,
        ))
        page["character_instances"].append(create_character_instance(
            cast_id="alice", scene_id="s1",
            area=make_area(0.05, 0.1, 0.2, 0.7),
            acting_prompt="surprised",
            instance_id="i1",
        ))
        page["guides"].append(create_guide(
            guide_type="frame_guide",
            asset_reference="/path/to/guide.png",
            guide_id="g1",
        ))
        page["generation"] = {"seed": 42, "model_ref": "illustrious_xl"}

        doc = create_document(pages=[page])
        json_str = to_json(doc)
        reloaded = from_json(json_str)

        # Compare key fields
        rp = reloaded["pages"][0]
        self.assertEqual(rp["page_id"], "page_1")
        self.assertEqual(rp["width_px"], 832)
        self.assertEqual(rp["style_prompt"], "manga style")
        self.assertEqual(rp["cast"][0]["cast_id"], "alice")
        self.assertEqual(rp["scenes"][0]["scene_id"], "s1")
        self.assertEqual(rp["scenes"][0]["input_mode"], "cast")
        self.assertEqual(rp["visual_frames"][0]["frame_id"], "f1")
        self.assertEqual(rp["character_instances"][0]["instance_id"], "i1")
        self.assertEqual(rp["character_instances"][0]["cast_id"], "alice")
        self.assertEqual(rp["character_instances"][0]["scene_id"], "s1")
        self.assertEqual(rp["guides"][0]["guide_id"], "g1")
        self.assertEqual(rp["generation"]["seed"], 42)


class TestGeometryValidation(unittest.TestCase):
    """Validate area geometry edge cases."""

    def test_valid_area(self):
        errors = validate_area(make_area(0.1, 0.2, 0.3, 0.4))
        self.assertEqual(errors, [])

    def test_zero_width_rejected(self):
        errors = validate_area({"shape_type": "rect", "x": 0, "y": 0, "w": 0, "h": 0.5})
        self.assertTrue(any("w must be > 0" in e for e in errors))

    def test_nan_rejected(self):
        errors = validate_area({"shape_type": "rect", "x": float("nan"),
                                "y": 0, "w": 0.5, "h": 0.5})
        self.assertTrue(any("finite" in e for e in errors))

    def test_inf_rejected(self):
        errors = validate_area({"shape_type": "rect", "x": float("inf"),
                                "y": 0, "w": 0.5, "h": 0.5})
        self.assertTrue(any("finite" in e for e in errors))

    def test_bool_rejected(self):
        errors = validate_area({"shape_type": "rect", "x": True,
                                "y": 0, "w": 0.5, "h": 0.5})
        self.assertTrue(any("finite" in e for e in errors))

    def test_out_of_bounds_rejected(self):
        errors = validate_area({"shape_type": "rect", "x": -0.1,
                                "y": 0, "w": 0.5, "h": 0.5})
        self.assertTrue(any("out of" in e for e in errors))


class TestStableIDs(unittest.TestCase):
    """Verify ID generation and uniqueness."""

    def test_generate_id_has_prefix(self):
        sid = generate_id("scene")
        self.assertTrue(sid.startswith("scene_"))
        self.assertTrue(len(sid) > len("scene_"))

    def test_ids_are_unique(self):
        ids = {generate_id("test") for _ in range(100)}
        self.assertEqual(len(ids), 100)

    def test_ids_survive_serialization(self):
        page = create_page(832, 1216, page_id="stable_page")
        page["scenes"].append(create_scene(scene_id="stable_scene"))
        doc = create_document(pages=[page])

        json_str = to_json(doc)
        reloaded = from_json(json_str)
        self.assertEqual(reloaded["pages"][0]["page_id"], "stable_page")
        self.assertEqual(reloaded["pages"][0]["scenes"][0]["scene_id"], "stable_scene")


if __name__ == "__main__":
    unittest.main(verbosity=2)
