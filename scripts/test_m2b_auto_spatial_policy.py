"""
test_m2b_auto_spatial_policy.py — Unit & Contract Tests for M2B Production Auto Spatial Policy
=============================================================================================
Tests the M2B Production AUTO Spatial Policy:
1. 0 characters -> 'off'
2. 1 character -> 'off'
3. 2 characters (balanced size) -> 'horizontal'
4. 2 characters (ratio >= 1.8) -> 'spatial_depth'
5. 3+ characters -> 'off'
6. Ambiguous horizontal overlap -> no forced hint under auto
7. Multi-scene page: Independent per-scene auto resolution
8. Backward compatibility: Explicit research modes ('off', 'horizontal', 'spatial_depth', 'full') still function.
"""
import sys
import os
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

resolve_auto_spatial_mode = _shc.resolve_auto_spatial_mode
compile_scene_spatial_hints = _shc.compile_scene_spatial_hints
compile_document_to_page_plan = _aeb.compile_document_to_page_plan
get_execution_debug_info = _aeb.get_execution_debug_info
create_document = _ac.create_document
create_page = _ac.create_page
create_scene = _ac.create_scene
create_cast_entry = _ac.create_cast_entry
create_character_instance = _ac.create_character_instance
make_area = _ac.make_area


class TestM2BAutoSpatialPolicy(unittest.TestCase):
    def setUp(self):
        self.cast_alice = create_cast_entry("Alice", "blonde twin tails, school uniform", cast_id="c_alice")
        self.cast_bob = create_cast_entry("Bob", "short black hair, school blazer", cast_id="c_bob")
        self.cast_carol = create_cast_entry("Carol", "long brown hair, glasses", cast_id="c_carol")
        self.cast_map = {
            "c_alice": self.cast_alice,
            "c_bob": self.cast_bob,
            "c_carol": self.cast_carol,
        }

    def test_01_auto_policy_zero_characters(self):
        """0 characters in scene resolves to 'off'."""
        self.assertEqual(resolve_auto_spatial_mode([]), "off")

    def test_02_auto_policy_single_character(self):
        """1 character in scene resolves to 'off' (area tracking is already strong)."""
        inst = {"instance_id": "i1", "area": {"x": 0.1, "y": 0.1, "w": 0.3, "h": 0.6}}
        self.assertEqual(resolve_auto_spatial_mode([inst]), "off")

    def test_03_auto_policy_two_character_balanced(self):
        """2 characters with balanced scale (ratio < 1.8) resolves to 'horizontal'."""
        inst1 = {"instance_id": "i1", "area": {"x": 0.1, "y": 0.1, "w": 0.3, "h": 0.6}}
        inst2 = {"instance_id": "i2", "area": {"x": 0.55, "y": 0.1, "w": 0.3, "h": 0.6}}
        self.assertEqual(resolve_auto_spatial_mode([inst1, inst2]), "horizontal")

    def test_04_auto_policy_two_character_depth(self):
        """2 characters with scale ratio >= 1.8 resolves to 'spatial_depth'."""
        inst1 = {"instance_id": "i1", "area": {"x": 0.05, "y": 0.05, "w": 0.5, "h": 0.8}}  # area = 0.40
        inst2 = {"instance_id": "i2", "area": {"x": 0.65, "y": 0.10, "w": 0.2, "h": 0.3}}  # area = 0.06 (ratio ~6.67)
        self.assertEqual(resolve_auto_spatial_mode([inst1, inst2]), "spatial_depth")

    def test_05_auto_policy_three_characters(self):
        """3 characters in scene resolves to 'off' (advanced/seed-sensitive in M2A.1)."""
        inst1 = {"instance_id": "i1", "area": {"x": 0.1, "y": 0.1, "w": 0.2, "h": 0.6}}
        inst2 = {"instance_id": "i2", "area": {"x": 0.4, "y": 0.1, "w": 0.2, "h": 0.6}}
        inst3 = {"instance_id": "i3", "area": {"x": 0.7, "y": 0.1, "w": 0.2, "h": 0.6}}
        self.assertEqual(resolve_auto_spatial_mode([inst1, inst2, inst3]), "off")

    def test_06_auto_policy_four_characters(self):
        """4+ characters in scene resolves to 'off'."""
        insts = [{"instance_id": f"i{k}", "area": {"x": 0.1 * k, "y": 0.1, "w": 0.15, "h": 0.5}} for k in range(4)]
        self.assertEqual(resolve_auto_spatial_mode(insts), "off")

    def test_07_compile_scene_auto_horizontal(self):
        """compile_scene_spatial_hints with mode='auto' applies horizontal hints for 2 balanced chars."""
        scene = {"area": {"x": 0.0, "y": 0.0, "w": 1.0, "h": 1.0}}
        inst1 = {"instance_id": "i1", "cast_id": "c_alice", "acting_prompt": "reading", "area": {"x": 0.1, "y": 0.1, "w": 0.25, "h": 0.7}}
        inst2 = {"instance_id": "i2", "cast_id": "c_bob", "acting_prompt": "writing", "area": {"x": 0.65, "y": 0.1, "w": 0.25, "h": 0.7}}
        hints, pres = compile_scene_spatial_hints(scene, [inst1, inst2], self.cast_map, mode="auto")
        self.assertEqual(hints["i1"]["derived_spatial_hint"], "on the left side")
        self.assertEqual(hints["i2"]["derived_spatial_hint"], "on the right side")
        self.assertEqual(hints["i1"]["derived_hints_metadata"]["resolved_mode"], "horizontal")
        self.assertEqual(pres, "")  # No presence hint by default in auto

    def test_08_compile_scene_auto_depth(self):
        """compile_scene_spatial_hints with mode='auto' applies depth hints when ratio >= 1.8."""
        scene = {"area": {"x": 0.0, "y": 0.0, "w": 1.0, "h": 1.0}}
        inst1 = {"instance_id": "i1", "cast_id": "c_alice", "acting_prompt": "walking", "area": {"x": 0.05, "y": 0.05, "w": 0.55, "h": 0.85}}
        inst2 = {"instance_id": "i2", "cast_id": "c_bob", "acting_prompt": "waving", "area": {"x": 0.65, "y": 0.20, "w": 0.20, "h": 0.30}}
        hints, pres = compile_scene_spatial_hints(scene, [inst1, inst2], self.cast_map, mode="auto")
        self.assertEqual(hints["i1"]["derived_spatial_hint"], "large in the foreground")
        self.assertEqual(hints["i2"]["derived_spatial_hint"], "smaller in the background")
        self.assertEqual(hints["i1"]["derived_hints_metadata"]["resolved_mode"], "spatial_depth")

    def test_09_multi_scene_independent_auto_resolution(self):
        """Each scene independently resolves its auto spatial mode on a multi-scene page."""
        page = create_page(width_px=832, height_px=1216)
        page["cast"] = [self.cast_alice, self.cast_bob]
        # Scene 1: 1 character -> resolves to off
        s1 = create_scene("Scene 1", "classroom", area=make_area(0.1, 0.05, 0.8, 0.4), scene_id="s1", input_mode="cast")
        # Scene 2: 2 characters balanced -> resolves to horizontal
        s2 = create_scene("Scene 2", "hallway", area=make_area(0.1, 0.52, 0.8, 0.4), scene_id="s2", input_mode="cast")
        page["scenes"] = [s1, s2]

        inst_s1_alice = create_character_instance("c_alice", "s1", make_area(0.2, 0.1, 0.3, 0.3), acting_prompt="sitting", instance_id="i_s1_a")
        inst_s2_alice = create_character_instance("c_alice", "s2", make_area(0.15, 0.55, 0.25, 0.3), acting_prompt="standing", instance_id="i_s2_a")
        inst_s2_bob = create_character_instance("c_bob", "s2", make_area(0.55, 0.55, 0.25, 0.3), acting_prompt="standing", instance_id="i_s2_b")
        page["character_instances"] = [inst_s1_alice, inst_s2_alice, inst_s2_bob]

        doc = create_document(pages=[page])
        plan = compile_document_to_page_plan(doc, spatial_hint_mode="auto")

        p1_chars = plan["panels"][0]["characters"]
        p2_chars = plan["panels"][1]["characters"]

        # Scene 1 has 1 char: spatial hint should be empty
        self.assertEqual(p1_chars[0]["derived_spatial_hint"], "")
        self.assertEqual(p1_chars[0]["derived_hints_metadata"]["resolved_mode"], "off")

        # Scene 2 has 2 chars: spatial hints are left / right
        self.assertEqual(p2_chars[0]["derived_spatial_hint"], "on the left side")
        self.assertEqual(p2_chars[1]["derived_spatial_hint"], "on the right side")
        self.assertEqual(p2_chars[0]["derived_hints_metadata"]["resolved_mode"], "horizontal")

    def test_10_explicit_research_modes_still_compatible(self):
        """Explicit research modes ('off', 'horizontal', 'spatial_depth', 'full') still function when passed."""
        scene = {"area": {"x": 0.0, "y": 0.0, "w": 1.0, "h": 1.0}}
        inst1 = {"instance_id": "i1", "cast_id": "c_alice", "area": {"x": 0.1, "y": 0.1, "w": 0.25, "h": 0.7}}
        inst2 = {"instance_id": "i2", "cast_id": "c_bob", "area": {"x": 0.65, "y": 0.1, "w": 0.25, "h": 0.7}}

        hints_off, _ = compile_scene_spatial_hints(scene, [inst1, inst2], self.cast_map, mode="off")
        self.assertEqual(hints_off["i1"]["derived_spatial_hint"], "")

        hints_full, pres = compile_scene_spatial_hints(scene, [inst1, inst2], self.cast_map, mode="full")
        self.assertIn("on the left side", hints_full["i1"]["derived_spatial_hint"])
        self.assertIn("two distinct people", pres)


if __name__ == "__main__":
    unittest.main()
