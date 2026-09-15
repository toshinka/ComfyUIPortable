"""
test_manga_reference_compile_bridge.py — Product Data Bridge Contract Tests
===========================================================================
Card: MANGA-REFERENCE-COMPILE-BRIDGE1

Validates:
A. CAST with reference_asset -> compiled character carries exact canonical reference
B. CAST without reference -> compile succeeds (reference_asset is None/null)
C. Two instances from same CAST -> same reference, different geometry
D. Two different CAST members -> references remain isolated by cast_id
E. Area remains unchanged
F. acting_prompt / negative override / LoRA behavior unchanged
G. Invalid persistent reference still fails at authoritative document validation boundary
H. Scene CAST gate is narrowed to the one-reference slice
I. Debug info serialization includes reference_asset
"""

import copy
import importlib.util
import os
import sys
import unittest

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
_mb = _import_submodule("mask_builder", "mask_builder.py")
_aeb = _import_submodule("authoring_execution_bridge", "authoring_execution_bridge.py")

create_document = _ac.create_document
create_page = _ac.create_page
create_scene = _ac.create_scene
create_cast_entry = _ac.create_cast_entry
create_character_instance = _ac.create_character_instance
make_area = _ac.make_area
validate_document = _ac.validate_document

compile_document_to_page_plan = _aeb.compile_document_to_page_plan
get_execution_debug_info = _aeb.get_execution_debug_info
validate_page_compile_plan = _ss.validate_page_compile_plan


class TestMangaReferenceCompileBridge(unittest.TestCase):
    """Test suite for MANGA-REFERENCE-COMPILE-BRIDGE1 data bridge."""

    def _make_base_doc(self):
        page = create_page(832, 1216, style_prompt="monochrome manga", style_negative_prompt="blurry")
        page["scenes"].append(create_scene(
            name="Room",
            prompt="quiet interior room",
            negative_prompt="crowd",
            input_mode="cast",
            area=make_area(0.05, 0.05, 0.9, 0.9),
            scene_id="scene_main",
        ))
        return create_document(pages=[page])

    # A. CAST with reference_asset -> compiled character carries exact canonical reference
    def test_a_cast_with_reference_asset_carried_to_compile_plan(self):
        doc = self._make_base_doc()
        page = doc["pages"][0]
        canonical_ref = "tegaki_manga_references/ref_alice_heroine.png"

        page["cast"].append(create_cast_entry(
            display_name="Alice",
            identity_prompt="1girl, twin braids, school blazer",
            negative_prompt="messy hair",
            cast_id="cast_alice",
            reference_asset=canonical_ref,
        ))
        page["character_instances"].append(create_character_instance(
            cast_id="cast_alice",
            scene_id="scene_main",
            area=make_area(0.1, 0.2, 0.35, 0.6),
            acting_prompt="holding notebook",
            instance_id="inst_alice_1",
        ))

        plan = compile_document_to_page_plan(doc)
        validate_page_compile_plan(plan)

        chars = plan["panels"][0]["characters"]
        self.assertEqual(len(chars), 1)
        c = chars[0]

        # Explicit compile-plan fields
        self.assertEqual(c["cast_id"], "cast_alice")
        self.assertEqual(c["character_id"], "cast_alice")
        self.assertEqual(c["instance_id"], "inst_alice_1")
        self.assertEqual(c["reference_asset"], canonical_ref)
        self.assertEqual(c["metadata"]["reference_asset"], canonical_ref)
        self.assertEqual(c["metadata"]["cast_id"], "cast_alice")

    # B. CAST without reference -> compile succeeds (reference_asset is None)
    def test_b_cast_without_reference_asset_compiles_successfully(self):
        doc = self._make_base_doc()
        page = doc["pages"][0]

        page["cast"].append(create_cast_entry(
            display_name="Bob",
            identity_prompt="1boy, short dark hair",
            cast_id="cast_bob",
            reference_asset=None,
        ))
        page["character_instances"].append(create_character_instance(
            cast_id="cast_bob",
            scene_id="scene_main",
            area=make_area(0.5, 0.2, 0.35, 0.6),
            acting_prompt="waving hand",
            instance_id="inst_bob_1",
        ))

        plan = compile_document_to_page_plan(doc)
        validate_page_compile_plan(plan)

        c = plan["panels"][0]["characters"][0]
        self.assertEqual(c["cast_id"], "cast_bob")
        self.assertIsNone(c["reference_asset"])
        self.assertIsNone(c["metadata"]["reference_asset"])

    # C. Two instances from same CAST -> same reference, different geometry
    def test_c_multiple_instances_same_cast_share_reference_with_distinct_geometry(self):
        doc = self._make_base_doc()
        page = doc["pages"][0]
        canonical_ref = "tegaki_manga_references/ref_alice_heroine.png"

        page["cast"].append(create_cast_entry(
            display_name="Alice",
            identity_prompt="1girl, twin braids",
            cast_id="cast_alice",
            reference_asset=canonical_ref,
        ))
        # Instance 1: left side, sitting
        page["character_instances"].append(create_character_instance(
            cast_id="cast_alice",
            scene_id="scene_main",
            area=make_area(0.08, 0.15, 0.35, 0.7),
            acting_prompt="sitting by desk",
            order=1,
            instance_id="inst_alice_left",
        ))
        # Instance 2: right side, standing
        page["character_instances"].append(create_character_instance(
            cast_id="cast_alice",
            scene_id="scene_main",
            area=make_area(0.55, 0.10, 0.38, 0.8),
            acting_prompt="standing near doorway",
            order=2,
            instance_id="inst_alice_right",
        ))

        plan = compile_document_to_page_plan(doc)
        chars = plan["panels"][0]["characters"]
        self.assertEqual(len(chars), 2)

        c1, c2 = chars[0], chars[1]

        # Both carry the exact same CAST-owned reference
        self.assertEqual(c1["reference_asset"], canonical_ref)
        self.assertEqual(c2["reference_asset"], canonical_ref)
        self.assertEqual(c1["cast_id"], "cast_alice")
        self.assertEqual(c2["cast_id"], "cast_alice")

        # Distinct instance IDs and distinct acting prompts
        self.assertEqual(c1["instance_id"], "inst_alice_left")
        self.assertEqual(c2["instance_id"], "inst_alice_right")
        self.assertIn("sitting by desk", c1["combined_prompt"])
        self.assertIn("standing near doorway", c2["combined_prompt"])

        # Distinct areas retained
        self.assertAlmostEqual(c1["area"]["x"], 0.08)
        self.assertAlmostEqual(c2["area"]["x"], 0.55)
        self.assertNotEqual(c1["area"], c2["area"])

    # D. Two different CAST members -> references remain isolated by cast_id
    def test_d_distinct_cast_members_have_isolated_references(self):
        doc = self._make_base_doc()
        page = doc["pages"][0]
        ref_alice = "tegaki_manga_references/ref_alice.png"
        ref_bob = "tegaki_manga_references/ref_bob.webp"

        page["cast"].append(create_cast_entry(
            display_name="Alice",
            identity_prompt="1girl, twin braids",
            cast_id="cast_alice",
            reference_asset=ref_alice,
        ))
        page["cast"].append(create_cast_entry(
            display_name="Bob",
            identity_prompt="1boy, glasses",
            cast_id="cast_bob",
            reference_asset=ref_bob,
        ))
        page["character_instances"].append(create_character_instance(
            cast_id="cast_alice",
            scene_id="scene_main",
            area=make_area(0.1, 0.2, 0.35, 0.6),
            instance_id="inst_alice",
            order=1,
        ))
        page["character_instances"].append(create_character_instance(
            cast_id="cast_bob",
            scene_id="scene_main",
            area=make_area(0.5, 0.2, 0.35, 0.6),
            instance_id="inst_bob",
            order=2,
        ))

        plan = compile_document_to_page_plan(doc)
        chars = plan["panels"][0]["characters"]
        self.assertEqual(len(chars), 2)

        self.assertEqual(chars[0]["cast_id"], "cast_alice")
        self.assertEqual(chars[0]["reference_asset"], ref_alice)
        self.assertEqual(chars[1]["cast_id"], "cast_bob")
        self.assertEqual(chars[1]["reference_asset"], ref_bob)

    # E. Area remains unchanged
    def test_e_character_instance_area_preserved_without_duplicate_geometry(self):
        doc = self._make_base_doc()
        page = doc["pages"][0]
        original_area = make_area(0.1234, 0.2345, 0.3456, 0.4567)

        page["cast"].append(create_cast_entry(
            display_name="Alice",
            cast_id="cast_alice",
            reference_asset="tegaki_manga_references/ref_alice.png",
        ))
        page["character_instances"].append(create_character_instance(
            cast_id="cast_alice",
            scene_id="scene_main",
            area=original_area,
            instance_id="inst_alice_geo",
        ))

        plan = compile_document_to_page_plan(doc)
        c = plan["panels"][0]["characters"][0]

        self.assertEqual(c["area"], original_area)
        self.assertNotIn("reference_area", c)
        self.assertNotIn("reference_mask_rect", c)
        self.assertNotIn("identity_region", c)

    # F. acting_prompt / negative override / LoRA behavior unchanged
    def test_f_prompt_negative_lora_behavior_preserved(self):
        doc = self._make_base_doc()
        page = doc["pages"][0]
        lora_def = [{"name": "alice_costume", "model_weight": 0.8, "clip_weight": 0.8, "enabled": True}]

        page["cast"].append(create_cast_entry(
            display_name="Alice",
            identity_prompt="1girl, twin braids",
            negative_prompt="bad anatomy",
            loras=lora_def,
            cast_id="cast_alice",
            reference_asset="tegaki_manga_references/ref_alice.png",
        ))
        page["character_instances"].append(create_character_instance(
            cast_id="cast_alice",
            scene_id="scene_main",
            area=make_area(0.1, 0.2, 0.3, 0.5),
            acting_prompt="smiling warmly",
            negative_prompt_override="closed eyes",
            instance_id="inst_alice_prompt",
        ))

        plan = compile_document_to_page_plan(doc)
        c = plan["panels"][0]["characters"][0]

        self.assertEqual(c["base_prompt"], "1girl, twin braids")
        self.assertEqual(c["override_prompt"], "smiling warmly")
        self.assertEqual(c["combined_prompt"], "1girl, twin braids, smiling warmly")
        self.assertEqual(c["base_negative_prompt"], "bad anatomy")
        self.assertEqual(c["override_negative_prompt"], "closed eyes")
        self.assertEqual(c["combined_negative_prompt"], "bad anatomy, closed eyes")
        self.assertEqual(len(c["loras"]), 1)
        self.assertEqual(c["loras"][0]["name"], "alice_costume")

    # G. Invalid persistent reference still fails at authoritative document validation boundary
    def test_g_invalid_reference_fails_at_validation_boundary(self):
        invalid_references = [
            "tegaki_manga_references/../escaped.png",
            "C:/Users/MAX/Desktop/ref.png",
            "tegaki_manga_references/invalid_ext.exe",
            "wrong_prefix/ref.png",
            "",
            "   ",
        ]
        for bad_ref in invalid_references:
            doc = self._make_base_doc()
            page = doc["pages"][0]
            page["cast"].append(create_cast_entry(
                display_name="Alice",
                cast_id="cast_alice",
                reference_asset=bad_ref,
            ))
            page["character_instances"].append(create_character_instance(
                cast_id="cast_alice",
                scene_id="scene_main",
                instance_id="inst_alice",
            ))

            # Authoritative document validation boundary must fail
            v_res = validate_document(doc)
            self.assertFalse(v_res.valid, f"Expected validation failure for bad ref: {bad_ref!r}")

            # Compile bridge must also fail closed
            with self.assertRaises(ValueError, msg=f"Bridge did not fail for bad ref: {bad_ref!r}"):
                compile_document_to_page_plan(doc)

    # H. The product gate accepts exactly the bounded one-reference slice.
    def test_h_scene_cast_gate_accepts_bounded_reference_slice(self):
        _sg = _import_submodule("scene_generation", "scene_generation.py")
        _validate_scene_document = _sg._validate_scene_document

        doc = self._make_base_doc()
        page = doc["pages"][0]
        page["cast"].append(create_cast_entry(
            display_name="Alice",
            cast_id="cast_alice",
            reference_asset="tegaki_manga_references/ref_alice.png",
        ))
        page["character_instances"].append(create_character_instance(
            cast_id="cast_alice",
            scene_id="scene_main",
            instance_id="inst_alice",
        ))

        page, cast_slice = _validate_scene_document(doc, page_index=0)
        self.assertEqual(page["scenes"][0]["input_mode"], "cast")
        self.assertEqual(cast_slice["cast_id"], "cast_alice")
        self.assertEqual(cast_slice["instance_id"], "inst_alice")
        self.assertEqual(cast_slice["reference_asset"], "tegaki_manga_references/ref_alice.png")

    # I. Debug serialization visibility
    def test_i_debug_serialization_includes_reference_asset(self):
        doc = self._make_base_doc()
        page = doc["pages"][0]
        canonical_ref = "tegaki_manga_references/ref_alice.png"

        page["cast"].append(create_cast_entry(
            display_name="Alice",
            identity_prompt="1girl",
            cast_id="cast_alice",
            reference_asset=canonical_ref,
        ))
        page["character_instances"].append(create_character_instance(
            cast_id="cast_alice",
            scene_id="scene_main",
            instance_id="inst_alice",
        ))

        debug_info = get_execution_debug_info(doc, page_index=0)

        # Check compiled_characters in debug info
        compiled_chars = debug_info["compiled_characters"]
        self.assertEqual(len(compiled_chars), 1)
        self.assertEqual(compiled_chars[0]["cast_id"], "cast_alice")
        self.assertEqual(compiled_chars[0]["reference_asset"], canonical_ref)

        # Check cast in debug info
        cast_entries = debug_info["cast"]
        self.assertEqual(len(cast_entries), 1)
        self.assertEqual(cast_entries[0]["reference_asset"], canonical_ref)


if __name__ == "__main__":
    unittest.main()
