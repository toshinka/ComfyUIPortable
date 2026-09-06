"""
test_m2b1_authoring_regression.py — Backend & Contract Regression Tests for M2B.1
================================================================================
Verifies that authoring document invariants and execution bridge compile
correctly under M2B.1 rules:
1. Bob-first single character scene (Bob instance without Alice) compiles cleanly.
2. Two-CAST explicit placement compiles with correct distinct identities.
3. Repeated CAST across multiple scenes retains distinct instance_ids and shares master prompt.
4. Safe string handling preserves special characters in display names & prompts without corruption.
5. Invariant safety: No orphans, valid FKs, schema version intact.
"""
import sys
import os
import json
import unittest
import importlib.util

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


class TestM2B1AuthoringRegression(unittest.TestCase):
    def setUp(self):
        self.cast_alice = create_cast_entry(
            display_name="Alice",
            identity_prompt="1girl, blonde twin tails, blue eyes, school uniform",
            cast_id="cast_alice"
        )
        self.cast_bob = create_cast_entry(
            display_name="Bob",
            identity_prompt="1boy, short black hair, casual jacket",
            cast_id="cast_bob"
        )

    def test_01_bob_first_scene_compiles_cleanly(self):
        """Bob placed as the only character in a scene compiles without needing Alice."""
        page = create_page(width_px=832, height_px=1216)
        page["cast"] = [self.cast_alice, self.cast_bob]
        s1 = create_scene("Scene 1", "classroom interior", area=make_area(0.1, 0.1, 0.8, 0.4), scene_id="s1", input_mode="cast")
        page["scenes"] = [s1]
        
        # Instance refers to cast_bob directly (Finding A fix)
        inst_bob = create_character_instance("cast_bob", "s1", make_area(0.15, 0.15, 0.3, 0.3), acting_prompt="sitting reading a book", instance_id="inst_1")
        page["character_instances"] = [inst_bob]
        
        doc = create_document(pages=[page])
        v = validate_document(doc)
        self.assertTrue(v.valid, f"Document should validate cleanly: {v.errors}")

        plan = compile_document_to_page_plan(doc)
        self.assertEqual(len(plan["panels"]), 1)
        chars = plan["panels"][0]["characters"]
        self.assertEqual(len(chars), 1)
        self.assertEqual(chars[0]["instance_id"], "inst_1")
        self.assertIn("short black hair", chars[0]["effective_character_prompt"])
        self.assertNotIn("blonde twin tails", chars[0]["effective_character_prompt"])

    def test_02_two_cast_explicit_placement(self):
        """Both Alice and Bob placed into same scene compile with respective identities."""
        page = create_page(width_px=832, height_px=1216)
        page["cast"] = [self.cast_alice, self.cast_bob]
        s1 = create_scene("Scene 1", "cafe", area=make_area(0.1, 0.1, 0.8, 0.5), scene_id="s1", input_mode="cast")
        page["scenes"] = [s1]
        
        inst_alice = create_character_instance("cast_alice", "s1", make_area(0.15, 0.15, 0.3, 0.35), acting_prompt="drinking tea", instance_id="inst_1")
        inst_bob = create_character_instance("cast_bob", "s1", make_area(0.55, 0.15, 0.3, 0.35), acting_prompt="talking enthusiastically", instance_id="inst_2")
        page["character_instances"] = [inst_alice, inst_bob]

        doc = create_document(pages=[page])
        v = validate_document(doc)
        self.assertTrue(v.valid, f"Validation errors: {v.errors}")

        plan = compile_document_to_page_plan(doc)
        chars = plan["panels"][0]["characters"]
        self.assertEqual(len(chars), 2)
        self.assertEqual(chars[0]["instance_id"], "inst_1")
        self.assertIn("blonde twin tails", chars[0]["effective_character_prompt"])
        self.assertEqual(chars[1]["instance_id"], "inst_2")
        self.assertIn("short black hair", chars[1]["effective_character_prompt"])

    def test_03_repeated_cast_across_multiple_scenes(self):
        """Alice in Scene 1 and Alice in Scene 2 retain distinct instance_ids and share cast prompt."""
        page = create_page(width_px=832, height_px=1216)
        page["cast"] = [self.cast_alice]
        s1 = create_scene("Scene 1", "outdoor park morning", area=make_area(0.1, 0.05, 0.8, 0.4), scene_id="s1", input_mode="cast")
        s2 = create_scene("Scene 2", "outdoor park sunset", area=make_area(0.1, 0.52, 0.8, 0.4), scene_id="s2", input_mode="cast")
        page["scenes"] = [s1, s2]

        inst1 = create_character_instance("cast_alice", "s1", make_area(0.2, 0.1, 0.3, 0.3), acting_prompt="walking", instance_id="inst_1")
        inst2 = create_character_instance("cast_alice", "s2", make_area(0.2, 0.6, 0.3, 0.3), acting_prompt="looking back", instance_id="inst_2")
        page["character_instances"] = [inst1, inst2]

        doc = create_document(pages=[page])
        v = validate_document(doc)
        self.assertTrue(v.valid, f"Validation errors: {v.errors}")

        plan = compile_document_to_page_plan(doc)
        self.assertEqual(len(plan["panels"]), 2)
        self.assertIn("blonde twin tails", plan["panels"][0]["characters"][0]["effective_character_prompt"])
        self.assertIn("blonde twin tails", plan["panels"][1]["characters"][0]["effective_character_prompt"])
        self.assertNotEqual(plan["panels"][0]["characters"][0]["instance_id"], plan["panels"][1]["characters"][0]["instance_id"])

    def test_04_special_characters_handling(self):
        """Display names and prompts containing < > & " ' serialize, validate, and roundtrip cleanly."""
        page = create_page(width_px=832, height_px=1216)
        cast_special = create_cast_entry(
            display_name="""Character <"A & B'>""",
            identity_prompt='1girl, wearing "fancy & elegant" dress <ribbon>',
            cast_id="cast_special"
        )
        page["cast"] = [cast_special]
        s1 = create_scene('Scene <"Main & Sub">', "cafe with 'warm' lights", area=make_area(0.1, 0.1, 0.8, 0.5), scene_id="s1", input_mode="cast")
        page["scenes"] = [s1]
        inst = create_character_instance("cast_special", "s1", make_area(0.2, 0.2, 0.4, 0.4), acting_prompt='saying "hello & goodbye" <smile>', instance_id="inst_1")
        page["character_instances"] = [inst]

        doc = create_document(pages=[page])
        v = validate_document(doc)
        self.assertTrue(v.valid, f"Validation errors: {v.errors}")

        json_str = to_json(doc)
        doc_recovered = from_json(json_str)
        v_rec = validate_document(doc_recovered)
        self.assertTrue(v_rec.valid, f"Recovered doc validation errors: {v_rec.errors}")
        self.assertEqual(doc_recovered["pages"][0]["cast"][0]["display_name"], """Character <"A & B'>""")
        self.assertEqual(doc_recovered["pages"][0]["character_instances"][0]["acting_prompt"], 'saying "hello & goodbye" <smile>')


if __name__ == "__main__":
    unittest.main()
