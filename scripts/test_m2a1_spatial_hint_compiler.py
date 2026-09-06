"""
test_m2a1_spatial_hint_compiler.py — Unit & Contract Tests for M2A.1 Spatial Hint Compiler
==========================================================================================
Tests pure logic and bridge integration for:
1. Left box -> "on the left side"
2. Right box -> "on the right side"
3. Center box -> "centered"
4. Ambiguous overlapping boxes -> no hint
5. 2 side-by-side arrangement detection
6. Depth hierarchy with scale ratio >= 1.8 -> foreground / background
7. Small scale ratio < 1.8 -> no depth hint
8. Authoring document SSOT non-mutation invariant
9. Hint mode 'off' is 100% M2A-equivalent
10. Transparent provenance fields present in compiled characters and debug JSON
11. Scene presence hints for 2, 3, 4 characters
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
_shc = _import_submodule("spatial_hint_compiler", "spatial_hint_compiler.py")
_aeb = _import_submodule("authoring_execution_bridge", "authoring_execution_bridge.py")

create_document = _ac.create_document
create_page = _ac.create_page
create_scene = _ac.create_scene
create_cast_entry = _ac.create_cast_entry
create_character_instance = _ac.create_character_instance
make_area = _ac.make_area

classify_horizontal_slot = _shc.classify_horizontal_slot
compute_horizontal_ambiguity = _shc.compute_horizontal_ambiguity
classify_depth_hints = _shc.classify_depth_hints
detect_arrangement_hint = _shc.detect_arrangement_hint
compile_scene_spatial_hints = _shc.compile_scene_spatial_hints
compile_document_to_page_plan = _aeb.compile_document_to_page_plan
get_execution_debug_info = _aeb.get_execution_debug_info


class TestM2A1SpatialHintCompiler(unittest.TestCase):
    def setUp(self):
        self.cast_alice = create_cast_entry(
            display_name="Alice",
            identity_prompt="1girl, blonde twin tails, school uniform",
            cast_id="alice_01",
        )
        self.cast_bob = create_cast_entry(
            display_name="Bob",
            identity_prompt="1boy, short dark hair, glasses, school uniform",
            cast_id="bob_01",
        )
        self.cast_carol = create_cast_entry(
            display_name="Carol",
            identity_prompt="1girl, short brown bob hair, cardigan",
            cast_id="carol_01",
        )
        self.cast_map = {
            "alice_01": self.cast_alice,
            "bob_01": self.cast_bob,
            "carol_01": self.cast_carol,
        }

    def test_01_left_box_yields_left_hint(self):
        """Instance positioned in left third (<0.38 relative center) receives 'on the left side'."""
        slot, hint = classify_horizontal_slot(0.25, is_ambiguous=False)
        self.assertEqual(slot, "left")
        self.assertEqual(hint, "on the left side")

    def test_02_right_box_yields_right_hint(self):
        """Instance positioned in right third (>0.62 relative center) receives 'on the right side'."""
        slot, hint = classify_horizontal_slot(0.75, is_ambiguous=False)
        self.assertEqual(slot, "right")
        self.assertEqual(hint, "on the right side")

    def test_03_center_box_yields_centered(self):
        """Instance positioned in middle third receives 'centered'."""
        slot, hint = classify_horizontal_slot(0.50, is_ambiguous=False)
        self.assertEqual(slot, "center")
        self.assertEqual(hint, "centered")

    def test_04_ambiguous_overlapping_boxes_yield_no_hint(self):
        """Instances that heavily overlap (>40%) are flagged ambiguous and receive no left/right hint."""
        scene_x, scene_w = 0.05, 0.90
        inst1 = {
            "instance_id": "inst_1",
            "area": make_area(0.30, 0.20, 0.35, 0.70),
        }
        inst2 = {
            "instance_id": "inst_2",
            "area": make_area(0.35, 0.20, 0.35, 0.70),
        }
        ambiguity = compute_horizontal_ambiguity([inst1, inst2], scene_x, scene_w)
        self.assertTrue(ambiguity["inst_1"])
        self.assertTrue(ambiguity["inst_2"])

        slot, hint = classify_horizontal_slot(0.35, is_ambiguous=True)
        self.assertEqual(slot, "ambiguous")
        self.assertEqual(hint, "")

    def test_05_side_by_side_arrangement_detection(self):
        """Two balanced characters horizontally separated are detected as 'side-by-side'."""
        inst_left = {
            "instance_id": "inst_l",
            "area": make_area(0.10, 0.15, 0.35, 0.70),
        }
        inst_right = {
            "instance_id": "inst_r",
            "area": make_area(0.55, 0.15, 0.35, 0.70),
        }
        arr = detect_arrangement_hint([inst_left, inst_right], 0.05, 0.05, 0.90, 0.90)
        self.assertEqual(arr, "side-by-side")

    def test_06_depth_scale_ratio_ge_1_8(self):
        """When max_area / min_area >= 1.8, foreground and background hints are derived."""
        inst_large = {
            "instance_id": "inst_fg",
            "area": make_area(0.08, 0.10, 0.50, 0.80),  # area = 0.40
        }
        inst_small = {
            "instance_id": "inst_bg",
            "area": make_area(0.60, 0.20, 0.25, 0.40),  # area = 0.10, ratio = 4.0
        }
        hints = classify_depth_hints([inst_large, inst_small], min_ratio=1.8)
        self.assertEqual(hints["inst_fg"][0], "foreground")
        self.assertEqual(hints["inst_fg"][1], "large in the foreground")
        self.assertEqual(hints["inst_bg"][0], "background")
        self.assertEqual(hints["inst_bg"][1], "smaller in the background")

    def test_07_depth_scale_ratio_lt_1_8_no_hint(self):
        """When max_area / min_area < 1.8, neutral depth is assigned without text hint."""
        inst1 = {
            "instance_id": "inst_1",
            "area": make_area(0.10, 0.15, 0.35, 0.70),  # area = 0.245
        }
        inst2 = {
            "instance_id": "inst_2",
            "area": make_area(0.55, 0.15, 0.30, 0.65),  # area = 0.195, ratio ~1.25
        }
        hints = classify_depth_hints([inst1, inst2], min_ratio=1.8)
        self.assertEqual(hints["inst_1"], ("neutral", ""))
        self.assertEqual(hints["inst_2"], ("neutral", ""))

    def test_08_presence_hints_by_count(self):
        """Scene presence hints conform exactly to Card §13."""
        scene = {"scene_id": "s1", "area": make_area(0.05, 0.05, 0.90, 0.90)}
        inst1 = {"instance_id": "i1", "cast_id": "alice_01", "acting_prompt": "standing", "area": make_area(0.1, 0.1, 0.3, 0.7)}
        inst2 = {"instance_id": "i2", "cast_id": "bob_01", "acting_prompt": "smiling", "area": make_area(0.5, 0.1, 0.3, 0.7)}
        inst3 = {"instance_id": "i3", "cast_id": "carol_01", "acting_prompt": "reading", "area": make_area(0.3, 0.1, 0.3, 0.7)}

        # 2 characters
        _, p2 = compile_scene_spatial_hints(scene, [inst1, inst2], self.cast_map, mode="horizontal_presence")
        self.assertEqual(p2, "two distinct people, same scene, both fully visible")

        # 3 characters
        _, p3 = compile_scene_spatial_hints(scene, [inst1, inst2, inst3], self.cast_map, mode="horizontal_presence")
        self.assertEqual(p3, "three people, same scene, all visible")

        # off mode -> presence is empty
        _, p_off = compile_scene_spatial_hints(scene, [inst1, inst2], self.cast_map, mode="off")
        self.assertEqual(p_off, "")

    def test_09_document_ssot_never_mutated(self):
        """Compile must never mutate the input TEGAKI_AUTHORING_DOCUMENT."""
        scene = create_scene(scene_id="s1", name="Main", input_mode="cast", area=make_area(0.05, 0.05, 0.90, 0.90))
        inst_a = create_character_instance(instance_id="inst_a", cast_id="alice_01", scene_id="s1", area=make_area(0.08, 0.15, 0.38, 0.75), acting_prompt="standing casually")
        inst_b = create_character_instance(instance_id="inst_b", cast_id="bob_01", scene_id="s1", area=make_area(0.54, 0.15, 0.38, 0.75), acting_prompt="reading a book")
        page = create_page(832, 1216)
        page["scenes"] = [scene]
        page["cast"] = [self.cast_alice, self.cast_bob]
        page["character_instances"] = [inst_a, inst_b]
        doc = create_document(pages=[page])

        doc_snapshot = copy.deepcopy(doc)
        _ = compile_document_to_page_plan(doc, spatial_hint_mode="full")

        self.assertEqual(doc, doc_snapshot, "Authoring document was mutated during compilation!")

    def test_10_mode_off_strictly_matches_m2a(self):
        """When spatial_hint_mode='off', character prompt is strictly 'identity, acting' with zero spatial cues."""
        scene = create_scene(scene_id="s1", input_mode="cast", area=make_area(0.05, 0.05, 0.90, 0.90))
        inst_a = create_character_instance(instance_id="inst_a", cast_id="alice_01", scene_id="s1", area=make_area(0.08, 0.15, 0.38, 0.75), acting_prompt="standing casually")
        page = create_page(832, 1216)
        page["scenes"] = [scene]
        page["cast"] = [self.cast_alice]
        page["character_instances"] = [inst_a]
        doc = create_document(pages=[page])

        plan = compile_document_to_page_plan(doc, spatial_hint_mode="off")
        c = plan["panels"][0]["characters"][0]
        expected_prompt = f"{self.cast_alice['identity_prompt']}, standing casually"
        self.assertEqual(c["combined_prompt"], expected_prompt)
        self.assertEqual(c["derived_spatial_hint"], "")
        self.assertEqual(c["scene_presence_hint"], "")

    def test_11_transparent_provenance_keys_in_plan_and_debug_json(self):
        """Compiled character dictionary and debug JSON expose transparent hint provenance."""
        scene = create_scene(scene_id="s1", input_mode="cast", area=make_area(0.05, 0.05, 0.90, 0.90))
        inst_a = create_character_instance(instance_id="inst_a", cast_id="alice_01", scene_id="s1", area=make_area(0.08, 0.15, 0.38, 0.75), acting_prompt="standing casually")
        inst_b = create_character_instance(instance_id="inst_b", cast_id="bob_01", scene_id="s1", area=make_area(0.54, 0.15, 0.38, 0.75), acting_prompt="reading a book")
        page = create_page(832, 1216)
        page["scenes"] = [scene]
        page["cast"] = [self.cast_alice, self.cast_bob]
        page["character_instances"] = [inst_a, inst_b]
        doc = create_document(pages=[page])

        plan = compile_document_to_page_plan(doc, spatial_hint_mode="horizontal_presence")
        c_a = plan["panels"][0]["characters"][0]
        c_b = plan["panels"][0]["characters"][1]

        self.assertIn("raw_identity_prompt", c_a)
        self.assertIn("raw_acting_prompt", c_a)
        self.assertIn("derived_spatial_hint", c_a)
        self.assertIn("scene_presence_hint", c_a)
        self.assertIn("effective_character_prompt", c_a)
        self.assertIn("derived_hints_metadata", c_a)

        self.assertEqual(c_a["derived_spatial_hint"], "on the left side")
        self.assertEqual(c_b["derived_spatial_hint"], "on the right side")
        self.assertEqual(c_a["scene_presence_hint"], "two distinct people, same scene, both fully visible")

        debug_info = get_execution_debug_info(doc, spatial_hint_mode="horizontal_presence")
        self.assertEqual(debug_info["spatial_hint_mode"], "horizontal_presence")
        self.assertEqual(len(debug_info["compiled_characters"]), 2)
        self.assertEqual(debug_info["compiled_characters"][0]["derived_spatial_hint"], "on the left side")


if __name__ == "__main__":
    unittest.main()
