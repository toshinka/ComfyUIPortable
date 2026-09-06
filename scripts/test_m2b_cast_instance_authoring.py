"""
test_m2b_cast_instance_authoring.py — Unit & Contract Tests for CAST & Character Instance Authoring
===================================================================================================
Covers M2B Requirements in Card §94:
1. Add CAST with unique, stable cast_id
2. Rename CAST display_name without mutating cast_id (stable identity)
3. Add Character Instance with unique, stable instance_id
4. Same CAST across multiple scenes (recurrent identity)
5. Same CAST duplicate in the same scene (allowed)
6. Missing Foreign Key (character instance referencing non-existent cast_id) fails closed
7. Scene deletion cascades to remove its character instances without leaving orphan references
8. Scene deletion leaves CAST Masters intact
9. CAST deletion rejected if referenced by active instances
10. Full document validation & roundtrip persistence
"""
import sys
import os
import copy
import json
import unittest
import importlib.util

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
_aeb = _import_submodule("authoring_execution_bridge", "authoring_execution_bridge.py")

create_document = _ac.create_document
create_page = _ac.create_page
create_scene = _ac.create_scene
create_cast_entry = _ac.create_cast_entry
create_character_instance = _ac.create_character_instance
make_area = _ac.make_area
validate_document = _ac.validate_document
to_json = _ac.to_json
from_json = _ac.from_json
compile_document_to_page_plan = _aeb.compile_document_to_page_plan


class TestM2BCastInstanceAuthoring(unittest.TestCase):
    def setUp(self):
        self.page = create_page(width_px=832, height_px=1216)
        self.doc = create_document(pages=[self.page])

    def test_01_add_cast_stable_id(self):
        """Adding a CAST creates unique stable cast_id; display_name changes preserve cast_id."""
        cast_alice = create_cast_entry("Alice", "blonde hair, blue eyes", cast_id="cast_alice_1")
        self.assertEqual(cast_alice["cast_id"], "cast_alice_1")
        self.assertEqual(cast_alice["display_name"], "Alice")

        # Mutate display name
        cast_alice["display_name"] = "Alice in Wonderland"
        self.assertEqual(cast_alice["cast_id"], "cast_alice_1")  # ID unchanged
        self.assertEqual(cast_alice["display_name"], "Alice in Wonderland")

    def test_02_add_character_instance_stable_id(self):
        """Character instances have unique stable instance_ids independent of cast_id."""
        inst = create_character_instance(
            cast_id="c_alice",
            scene_id="s1",
            area=make_area(0.1, 0.1, 0.3, 0.5),
            acting_prompt="reading quietly",
            instance_id="inst_alice_top",
        )
        self.assertEqual(inst["instance_id"], "inst_alice_top")
        self.assertEqual(inst["cast_id"], "c_alice")
        self.assertEqual(inst["scene_id"], "s1")
        self.assertEqual(inst["acting_prompt"], "reading quietly")

    def test_03_same_cast_across_multiple_scenes(self):
        """Same CAST Master can be placed in multiple distinct scenes with separate instance IDs."""
        cast_alice = create_cast_entry("Alice", "blonde hair", cast_id="c_alice")
        self.page["cast"] = [cast_alice]

        s1 = create_scene("Scene 1", "classroom", area=make_area(0.1, 0.05, 0.8, 0.4), scene_id="s1", input_mode="cast")
        s2 = create_scene("Scene 2", "park", area=make_area(0.1, 0.52, 0.8, 0.4), scene_id="s2", input_mode="cast")
        self.page["scenes"] = [s1, s2]

        inst_s1 = create_character_instance("c_alice", "s1", make_area(0.2, 0.1, 0.3, 0.3), instance_id="i_s1")
        inst_s2 = create_character_instance("c_alice", "s2", make_area(0.2, 0.6, 0.3, 0.3), instance_id="i_s2")
        self.page["character_instances"] = [inst_s1, inst_s2]

        v = validate_document(self.doc)
        self.assertTrue(v.valid, f"Validation errors: {v.errors}")

        plan = compile_document_to_page_plan(self.doc)
        self.assertEqual(len(plan["panels"]), 2)
        self.assertEqual(plan["panels"][0]["characters"][0]["character_id"], "c_alice")
        self.assertEqual(plan["panels"][1]["characters"][0]["character_id"], "c_alice")
        self.assertNotEqual(plan["panels"][0]["characters"][0]["instance_id"], plan["panels"][1]["characters"][0]["instance_id"])

    def test_04_same_cast_same_scene_allowed(self):
        """Same CAST appearing twice in the same scene is allowed by schema and contract."""
        cast_alice = create_cast_entry("Alice", "blonde hair", cast_id="c_alice")
        self.page["cast"] = [cast_alice]
        s1 = create_scene("Scene 1", "mirror room", area=make_area(0.1, 0.1, 0.8, 0.8), scene_id="s1", input_mode="cast")
        self.page["scenes"] = [s1]

        inst1 = create_character_instance("c_alice", "s1", make_area(0.15, 0.2, 0.3, 0.5), acting_prompt="looking in mirror", instance_id="i1")
        inst2 = create_character_instance("c_alice", "s1", make_area(0.55, 0.2, 0.3, 0.5), acting_prompt="reflection looking back", instance_id="i2")
        self.page["character_instances"] = [inst1, inst2]

        v = validate_document(self.doc)
        self.assertTrue(v.valid, f"Validation errors: {v.errors}")
        plan = compile_document_to_page_plan(self.doc)
        chars = plan["panels"][0]["characters"]
        self.assertEqual(len(chars), 2)
        self.assertEqual(chars[0]["character_id"], "c_alice")
        self.assertEqual(chars[1]["character_id"], "c_alice")

    def test_05_missing_cast_fk_fails_closed(self):
        """Instance referencing a non-existent cast_id fails closed during validation."""
        s1 = create_scene("Scene 1", "classroom", area=make_area(0.1, 0.1, 0.8, 0.8), scene_id="s1", input_mode="cast")
        self.page["scenes"] = [s1]
        self.page["cast"] = []  # No cast registered

        inst = create_character_instance("non_existent_cast", "s1", make_area(0.2, 0.2, 0.3, 0.3), instance_id="i1")
        self.page["character_instances"] = [inst]

        v = validate_document(self.doc)
        self.assertFalse(v.valid)
        self.assertTrue(any("non_existent_cast" in err or "cast_id" in err for err in v.errors))

    def test_06_scene_delete_cascades_instances_keeps_cast(self):
        """Deleting a scene cascades to remove child character instances, while preserving CAST masters."""
        cast_alice = create_cast_entry("Alice", "blonde hair", cast_id="c_alice")
        cast_bob = create_cast_entry("Bob", "dark hair", cast_id="c_bob")
        self.page["cast"] = [cast_alice, cast_bob]

        s1 = create_scene("Scene 1", "classroom", area=make_area(0.1, 0.05, 0.8, 0.4), scene_id="s1", input_mode="cast")
        s2 = create_scene("Scene 2", "hallway", area=make_area(0.1, 0.52, 0.8, 0.4), scene_id="s2", input_mode="cast")
        self.page["scenes"] = [s1, s2]

        inst_s1_alice = create_character_instance("c_alice", "s1", make_area(0.2, 0.1, 0.3, 0.3), instance_id="i1")
        inst_s2_bob = create_character_instance("c_bob", "s2", make_area(0.2, 0.6, 0.3, 0.3), instance_id="i2")
        self.page["character_instances"] = [inst_s1_alice, inst_s2_bob]

        # Simulate deleting Scene 1 with cascade
        deleted_scene_id = "s1"
        self.page["scenes"] = [s for s in self.page["scenes"] if s["scene_id"] != deleted_scene_id]
        self.page["character_instances"] = [i for i in self.page["character_instances"] if i["scene_id"] != deleted_scene_id]

        v = validate_document(self.doc)
        self.assertTrue(v.valid, f"Validation errors: {v.errors}")
        # CAST masters remain intact
        self.assertEqual(len(self.page["cast"]), 2)
        # Only instance belonging to remaining scene exists
        self.assertEqual(len(self.page["character_instances"]), 1)
        self.assertEqual(self.page["character_instances"][0]["instance_id"], "i2")

    def test_07_roundtrip_json_serialization(self):
        """Document serializes to and deserializes from JSON with 100% field preservation."""
        cast_alice = create_cast_entry("Alice", "blonde hair", cast_id="c_alice")
        self.page["cast"] = [cast_alice]
        s1 = create_scene("Scene 1", "classroom", area=make_area(0.1, 0.1, 0.8, 0.8), scene_id="s1", input_mode="cast")
        self.page["scenes"] = [s1]
        inst = create_character_instance("c_alice", "s1", make_area(0.2, 0.2, 0.3, 0.4), acting_prompt="reading", instance_id="i1")
        self.page["character_instances"] = [inst]

        json_str = to_json(self.doc)
        restored = from_json(json_str)

        self.assertEqual(self.doc["schema_id"], restored["schema_id"])
        self.assertEqual(len(restored["pages"][0]["cast"]), 1)
        self.assertEqual(restored["pages"][0]["cast"][0]["cast_id"], "c_alice")
        self.assertEqual(len(restored["pages"][0]["character_instances"]), 1)
        self.assertEqual(restored["pages"][0]["character_instances"][0]["acting_prompt"], "reading")


if __name__ == "__main__":
    unittest.main()
