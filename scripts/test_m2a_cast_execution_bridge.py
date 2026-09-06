"""
test_m2a_cast_execution_bridge.py — M2A Character Execution Bridge Contract Tests
==================================================================================
Tests the CAST Master and Character Instance execution bridge:
- 1 CAST 1 Instance compilation
- 2 CAST 2 Instances compilation
- Same CAST multiple instances (recurrent appearance)
- Same CAST + Other CAST mixed
- Instance ID uniqueness fail-closed
- Missing CAST FK fail-closed
- Missing Scene FK fail-closed
- Prompt and negative composition
- Page-normalized coordinate retention & mask projection
- Simple scene regression
- Mixed simple + cast page support
- Preview and debug info
"""
import sys
import os
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

validate_authoring_execution_document = _aeb.validate_authoring_execution_document
validate_m1_execution_document = _aeb.validate_m1_execution_document
compile_document_to_page_plan = _aeb.compile_document_to_page_plan
generate_scene_regions_preview_image = _aeb.generate_scene_regions_preview_image
get_execution_debug_info = _aeb.get_execution_debug_info
validate_page_compile_plan = _ss.validate_page_compile_plan
TegakiMangaMaskBuilder = _mb.TegakiMangaMaskBuilder


class TestM2ACastExecutionBridge(unittest.TestCase):
    """M2A Pure contract tests for CAST and Character Instances."""

    def test_single_cast_single_instance(self):
        """1 CAST, 1 Instance compiles with correct prompt concatenation and coordinates."""
        page = create_page(832, 1216, style_prompt="monochrome manga")
        page["scenes"].append(create_scene(
            name="Courtyard",
            prompt="school courtyard, daytime",
            input_mode="cast",
            area=make_area(0.05, 0.05, 0.9, 0.9),
            scene_id="scene_courtyard"
        ))
        page["cast"].append(create_cast_entry(
            display_name="Alice",
            identity_prompt="blonde twin tails, blue eyes, school uniform",
            negative_prompt="bad hands",
            cast_id="cast_alice"
        ))
        page["character_instances"].append(create_character_instance(
            cast_id="cast_alice",
            scene_id="scene_courtyard",
            area=make_area(0.1, 0.15, 0.35, 0.7),
            acting_prompt="standing casually",
            negative_prompt_override="closed eyes",
            order=1,
            instance_id="inst_alice_1"
        ))
        doc = create_document(pages=[page])

        plan = compile_document_to_page_plan(doc)
        validate_page_compile_plan(plan)

        self.assertEqual(len(plan["panels"]), 1)
        p1 = plan["panels"][0]
        self.assertEqual(len(p1["characters"]), 1)
        c = p1["characters"][0]

        self.assertEqual(c["character_id"], "cast_alice")
        self.assertEqual(c["instance_id"], "inst_alice_1")
        self.assertEqual(c["name"], "Alice")
        self.assertEqual(c["base_prompt"], "blonde twin tails, blue eyes, school uniform")
        self.assertEqual(c["override_prompt"], "standing casually")
        self.assertEqual(c["combined_prompt"], "blonde twin tails, blue eyes, school uniform, standing casually")
        self.assertEqual(c["base_negative_prompt"], "bad hands")
        self.assertEqual(c["override_negative_prompt"], "closed eyes")
        self.assertEqual(c["combined_negative_prompt"], "bad hands, closed eyes")
        self.assertEqual(c["coordinate_space"], "page")
        self.assertAlmostEqual(c["area"]["x"], 0.1)
        self.assertAlmostEqual(c["area"]["y"], 0.15)
        self.assertAlmostEqual(c["area"]["w"], 0.35)
        self.assertAlmostEqual(c["area"]["h"], 0.7)

    def test_two_cast_two_instances(self):
        """2 distinct CAST, 2 instances in same scene maintain separate identities and areas."""
        page = create_page(832, 1216)
        page["scenes"].append(create_scene(
            name="Classroom",
            prompt="classroom desks and chalkboard",
            input_mode="cast",
            area=make_area(0.05, 0.05, 0.9, 0.9),
            scene_id="scene_class"
        ))
        page["cast"].append(create_cast_entry(
            display_name="Alice",
            identity_prompt="blonde twin tails, blue eyes",
            cast_id="cast_alice"
        ))
        page["cast"].append(create_cast_entry(
            display_name="Bob",
            identity_prompt="short black hair, glasses",
            cast_id="cast_bob"
        ))
        page["character_instances"].append(create_character_instance(
            cast_id="cast_alice",
            scene_id="scene_class",
            area=make_area(0.08, 0.1, 0.38, 0.8),
            acting_prompt="smiling",
            order=1,
            instance_id="inst_alice"
        ))
        page["character_instances"].append(create_character_instance(
            cast_id="cast_bob",
            scene_id="scene_class",
            area=make_area(0.54, 0.1, 0.38, 0.8),
            acting_prompt="holding a book",
            order=2,
            instance_id="inst_bob"
        ))
        doc = create_document(pages=[page])

        plan = compile_document_to_page_plan(doc)
        p1 = plan["panels"][0]
        self.assertEqual(len(p1["characters"]), 2)

        char1 = p1["characters"][0]
        char2 = p1["characters"][1]
        self.assertEqual(char1["name"], "Alice")
        self.assertEqual(char1["instance_id"], "inst_alice")
        self.assertAlmostEqual(char1["area"]["x"], 0.08)

        self.assertEqual(char2["name"], "Bob")
        self.assertEqual(char2["instance_id"], "inst_bob")
        self.assertAlmostEqual(char2["area"]["x"], 0.54)

    def test_same_cast_multiple_instances(self):
        """Same CAST with 2 instances in same scene: unique instance_ids, independent acting prompts."""
        page = create_page(832, 1216)
        page["scenes"].append(create_scene(
            name="Hallway",
            prompt="school hallway",
            input_mode="cast",
            area=make_area(0.05, 0.05, 0.9, 0.9),
            scene_id="scene_hallway"
        ))
        page["cast"].append(create_cast_entry(
            display_name="Alice",
            identity_prompt="blonde twin tails, blue eyes",
            cast_id="cast_alice"
        ))
        page["character_instances"].append(create_character_instance(
            cast_id="cast_alice",
            scene_id="scene_hallway",
            area=make_area(0.08, 0.1, 0.38, 0.8),
            acting_prompt="smiling at camera",
            order=1,
            instance_id="inst_alice_left"
        ))
        page["character_instances"].append(create_character_instance(
            cast_id="cast_alice",
            scene_id="scene_hallway",
            area=make_area(0.54, 0.1, 0.38, 0.8),
            acting_prompt="looking away into window",
            order=2,
            instance_id="inst_alice_right"
        ))
        doc = create_document(pages=[page])

        plan = compile_document_to_page_plan(doc)
        p = plan["panels"][0]
        self.assertEqual(len(p["characters"]), 2)

        # Same CAST
        self.assertEqual(p["characters"][0]["character_id"], "cast_alice")
        self.assertEqual(p["characters"][1]["character_id"], "cast_alice")

        # Distinct instances
        self.assertEqual(p["characters"][0]["instance_id"], "inst_alice_left")
        self.assertEqual(p["characters"][1]["instance_id"], "inst_alice_right")
        self.assertNotEqual(p["characters"][0]["combined_prompt"], p["characters"][1]["combined_prompt"])
        self.assertNotEqual(p["characters"][0]["area"]["x"], p["characters"][1]["area"]["x"])

    def test_same_cast_plus_other_cast(self):
        """Mixed 3-person scene: 2 Alice instances + 1 Bob instance."""
        page = create_page(832, 1216)
        page["scenes"].append(create_scene(
            name="Clubroom",
            prompt="afterschool clubroom",
            input_mode="cast",
            area=make_area(0.05, 0.05, 0.9, 0.9),
            scene_id="scene_club"
        ))
        page["cast"].append(create_cast_entry(display_name="Alice", identity_prompt="blonde girl", cast_id="cast_a"))
        page["cast"].append(create_cast_entry(display_name="Bob", identity_prompt="glasses boy", cast_id="cast_b"))

        page["character_instances"].append(create_character_instance("cast_a", "scene_club", area=make_area(0.05, 0.2, 0.25, 0.7), order=1, instance_id="i1"))
        page["character_instances"].append(create_character_instance("cast_a", "scene_club", area=make_area(0.35, 0.2, 0.25, 0.7), order=2, instance_id="i2"))
        page["character_instances"].append(create_character_instance("cast_b", "scene_club", area=make_area(0.68, 0.2, 0.25, 0.7), order=3, instance_id="i3"))
        doc = create_document(pages=[page])

        plan = compile_document_to_page_plan(doc)
        chars = plan["panels"][0]["characters"]
        self.assertEqual(len(chars), 3)
        self.assertEqual([c["character_id"] for c in chars], ["cast_a", "cast_a", "cast_b"])
        self.assertEqual([c["instance_id"] for c in chars], ["i1", "i2", "i3"])

    def test_instance_id_uniqueness_fail_closed(self):
        """Duplicate instance_id triggers hard fail-closed ValueError."""
        page = create_page(832, 1216)
        page["scenes"].append(create_scene("Scene", input_mode="cast", scene_id="s1"))
        page["cast"].append(create_cast_entry("Alice", "blonde girl", cast_id="c1"))
        page["character_instances"].append(create_character_instance("c1", "s1", instance_id="dup_id"))
        page["character_instances"].append(create_character_instance("c1", "s1", instance_id="dup_id"))
        doc = create_document(pages=[page])

        with self.assertRaises(ValueError) as ctx:
            compile_document_to_page_plan(doc)
        self.assertIn("duplicate instance_id", str(ctx.exception).lower())

    def test_missing_cast_fk_fail_closed(self):
        """Character instance referencing unknown cast_id triggers hard fail-closed ValueError."""
        page = create_page(832, 1216)
        page["scenes"].append(create_scene("Scene", input_mode="cast", scene_id="s1"))
        page["cast"].append(create_cast_entry("Alice", "blonde girl", cast_id="c1"))
        page["character_instances"].append(create_character_instance("c_unknown", "s1", instance_id="i1"))
        doc = create_document(pages=[page])

        with self.assertRaises(ValueError) as ctx:
            compile_document_to_page_plan(doc)
        self.assertIn("not found in page cast", str(ctx.exception).lower())

    def test_missing_scene_fk_fail_closed(self):
        """Character instance referencing unknown scene_id triggers hard fail-closed ValueError."""
        page = create_page(832, 1216)
        page["scenes"].append(create_scene("Scene", input_mode="cast", scene_id="s1"))
        page["cast"].append(create_cast_entry("Alice", "blonde girl", cast_id="c1"))
        page["character_instances"].append(create_character_instance("c1", "s_unknown", instance_id="i1"))
        doc = create_document(pages=[page])

        with self.assertRaises(ValueError) as ctx:
            compile_document_to_page_plan(doc)
        self.assertIn("not found in page scenes", str(ctx.exception).lower())

    def test_prompt_composition(self):
        """Combined prompt correctly joins identity and acting prompts with clean commas."""
        page = create_page(832, 1216)
        page["scenes"].append(create_scene("Scene", input_mode="cast", scene_id="s1"))
        page["cast"].append(create_cast_entry("Alice", "1girl, blonde hair", cast_id="c1"))
        page["character_instances"].append(create_character_instance(
            "c1", "s1",
            acting_prompt="looking surprised, hand on chest",
            instance_id="i1"
        ))
        doc = create_document(pages=[page])

        plan = compile_document_to_page_plan(doc)
        c = plan["panels"][0]["characters"][0]
        self.assertEqual(c["combined_prompt"], "1girl, blonde hair, looking surprised, hand on chest")

    def test_negative_prompt_composition(self):
        """Combined negative prompt correctly joins base and override negative prompts."""
        page = create_page(832, 1216)
        page["scenes"].append(create_scene("Scene", input_mode="cast", scene_id="s1"))
        page["cast"].append(create_cast_entry("Alice", "1girl", negative_prompt="bad hands, lowres", cast_id="c1"))
        page["character_instances"].append(create_character_instance(
            "c1", "s1",
            negative_prompt_override="sad, crying",
            instance_id="i1"
        ))
        doc = create_document(pages=[page])

        plan = compile_document_to_page_plan(doc)
        c = plan["panels"][0]["characters"][0]
        self.assertEqual(c["combined_negative_prompt"], "bad hands, lowres, sad, crying")

    def test_page_normalized_area_retained_and_mask_projection(self):
        """Page-normalized coordinates are retained on character and accurately projected by mask builder."""
        page = create_page(832, 1216)
        page["scenes"].append(create_scene(
            name="Scene",
            input_mode="cast",
            area=make_area(0.06, 0.05, 0.88, 0.9),
            scene_id="s1"
        ))
        page["cast"].append(create_cast_entry("Alice", "1girl", cast_id="c1"))
        # Character placed at page coordinates x=0.10, y=0.15, w=0.35, h=0.70
        page["character_instances"].append(create_character_instance(
            "c1", "s1",
            area=make_area(0.10, 0.15, 0.35, 0.70),
            instance_id="i1"
        ))
        doc = create_document(pages=[page])

        plan = compile_document_to_page_plan(doc)
        c = plan["panels"][0]["characters"][0]
        self.assertEqual(c["coordinate_space"], "page")
        self.assertAlmostEqual(c["area"]["x"], 0.10)
        self.assertAlmostEqual(c["area"]["y"], 0.15)
        self.assertAlmostEqual(c["area"]["w"], 0.35)
        self.assertAlmostEqual(c["area"]["h"], 0.70)

        # Test mask builder projection
        mb = TegakiMangaMaskBuilder()
        panel_masks, char_masks, preview, debug_json, lr_masks = mb.build_masks(plan)
        debug = json.loads(debug_json)
        cm = debug["characters"][0]

        # Page projected area must exactly equal the page coordinates
        self.assertAlmostEqual(cm["page_projected_area"]["x"], 0.10)
        self.assertAlmostEqual(cm["page_projected_area"]["y"], 0.15)
        self.assertAlmostEqual(cm["page_projected_area"]["w"], 0.35)
        self.assertAlmostEqual(cm["page_projected_area"]["h"], 0.70)

        # Pixel bounds: x0 = round(0.10 * 832) = 83, y0 = round(0.15 * 1216) = 182
        # x1 = round(0.45 * 832) = 374, y1 = round(0.85 * 1216) = 1034
        x0, y0, x1, y1 = cm["pixel_bounds"]
        self.assertEqual(x0, 83)
        self.assertEqual(y0, 182)
        self.assertEqual(x1, 374)
        self.assertEqual(y1, 1034)

        # Char mask tensor check
        self.assertEqual(char_masks.shape, (1, 1216, 832))
        self.assertEqual(char_masks[0, y0:y1, x0:x1].mean().item(), 1.0)
        self.assertEqual(char_masks[0, 0:10, 0:10].mean().item(), 0.0)

    def test_simple_scene_regression(self):
        """M1 simple scene documents compile identically with empty characters list."""
        page = create_page(832, 1216)
        page["scenes"].append(create_scene("Scene 1", "prompt 1", input_mode="simple", scene_id="s1"))
        page["scenes"].append(create_scene("Scene 2", "prompt 2", input_mode="simple", scene_id="s2"))
        doc = create_document(pages=[page])

        plan = compile_document_to_page_plan(doc)
        self.assertEqual(len(plan["panels"]), 2)
        self.assertEqual(plan["panels"][0]["characters"], [])
        self.assertEqual(plan["panels"][1]["characters"], [])

    def test_mixed_simple_and_cast_page(self):
        """Mixed mode: Scene 1 is simple, Scene 2 is cast."""
        page = create_page(832, 1216)
        page["scenes"].append(create_scene("Scene 1 (Simple)", "landscape without cast", input_mode="simple", scene_id="s1", order=1))
        page["scenes"].append(create_scene("Scene 2 (Cast)", "classroom with character", input_mode="cast", scene_id="s2", order=2))
        page["cast"].append(create_cast_entry("Alice", "blonde girl", cast_id="c1"))
        page["character_instances"].append(create_character_instance("c1", "s2", area=make_area(0.1, 0.55, 0.35, 0.38), instance_id="i1"))
        doc = create_document(pages=[page])

        plan = compile_document_to_page_plan(doc)
        self.assertEqual(len(plan["panels"]), 2)
        self.assertEqual(len(plan["panels"][0]["characters"]), 0)
        self.assertEqual(len(plan["panels"][1]["characters"]), 1)
        self.assertEqual(plan["panels"][1]["characters"][0]["name"], "Alice")

    def test_preview_image_with_characters(self):
        """generate_scene_regions_preview_image renders both scene and character overlays."""
        page = create_page(832, 1216)
        page["scenes"].append(create_scene("Scene 1", "prompt 1", input_mode="cast", area=make_area(0.05, 0.05, 0.9, 0.9), scene_id="s1"))
        page["cast"].append(create_cast_entry("Alice", "blonde girl", cast_id="c1"))
        page["character_instances"].append(create_character_instance("c1", "s1", area=make_area(0.1, 0.2, 0.35, 0.6), acting_prompt="smiling", instance_id="i1"))
        doc = create_document(pages=[page])

        img = generate_scene_regions_preview_image(doc, width=416, height=608)
        self.assertEqual(img.size, (416, 608))
        self.assertEqual(img.mode, "RGB")

    def test_debug_info_includes_cast_and_instances(self):
        """get_execution_debug_info includes CAST and instance counts and metadata."""
        page = create_page(832, 1216)
        page["scenes"].append(create_scene("Scene 1", "prompt 1", input_mode="cast", scene_id="s1"))
        page["cast"].append(create_cast_entry("Alice", "blonde girl", cast_id="c1"))
        page["character_instances"].append(create_character_instance("c1", "s1", area=make_area(0.1, 0.2, 0.35, 0.6), acting_prompt="smiling", instance_id="i1"))
        doc = create_document(pages=[page])

        debug = get_execution_debug_info(doc, seed=123)
        self.assertEqual(debug["cast_count"], 1)
        self.assertEqual(debug["character_instances_count"], 1)
        self.assertEqual(debug["cast"][0]["display_name"], "Alice")
        self.assertEqual(debug["character_instances"][0]["instance_id"], "i1")


if __name__ == "__main__":
    unittest.main()
