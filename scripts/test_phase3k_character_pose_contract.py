"""
Test Phase 3K: Character Pose Contract and End-to-End Metadata Truth
===================================================================
Verifies:
1. Canonical CHARACTER_BINDING validation of 'shot_type', 'pose_preset', and 'interaction'.
2. CharacterStagingStateManager deep merge semantics (move/resize retains shot/pose/interaction).
3. End-to-end metadata truth propagation:
   staging_overrides -> REGION_SPEC -> PAGE_COMPILE_PLAN -> LayoutRegionBridge -> IMPACT_REGION_PLAN.
4. Fail-closed rejection of invalid enum values for shot_type and pose_preset.
5. Scene camera distance contract:
   - Panel camera distance validation ('near', 'medium', 'far').
   - Explicit staging area precedence over camera default.
   - Default area adaptation when character area is unconstrained.
"""

import os
import sys
import json
import unittest

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
COMFY_DIR = os.path.join(ROOT_DIR, "ComfyUI")
CUSTOM_NODES_DIR = os.path.join(ROOT_DIR, "custom_nodes_custom")
IMPACT_PACK_DIR = os.path.join(COMFY_DIR, "custom_nodes", "ComfyUI-Impact-Pack", "modules")

for p in [ROOT_DIR, COMFY_DIR, CUSTOM_NODES_DIR, IMPACT_PACK_DIR]:
    if p not in sys.path:
        sys.path.insert(0, p)

from custom_nodes_custom.tegaki_manga_nodes.scene_spec import (
    validate_cast_spec,
    validate_character_binding,
    validate_compile_plan,
    validate_page_compile_plan
)
from custom_nodes_custom.tegaki_manga_nodes.region_editor import validate_region_spec
from custom_nodes_custom.tegaki_manga_nodes.character_staging_editor import (
    CharacterStagingStateManager,
    TegakiMangaCharacterStagingEditor
)
from custom_nodes_custom.tegaki_manga_nodes.scene_compiler import (
    TegakiMangaPageCompiler,
    compile_panel_data
)
from custom_nodes_custom.tegaki_manga_nodes.panel_layout_spec import get_default_panel_layout_spec
from custom_nodes_custom.tegaki_manga_nodes.layout_region_bridge import build_panel_content_bridge
from custom_nodes_custom.tegaki_manga_nodes.impact_region_plan import build_impact_region_plan


class TestPhase3KCharacterPoseContract(unittest.TestCase):

    def setUp(self):
        self.cast_spec = {
            "version": 1,
            "characters": [
                {
                    "id": "char_alice",
                    "name": "Alice",
                    "enabled": True,
                    "prompt": "1girl, blonde twin tails, blue eyes, school uniform",
                    "negative_prompt": "1boy, blurry",
                    "loras": [],
                    "metadata": {}
                },
                {
                    "id": "char_bob",
                    "name": "Bob",
                    "enabled": True,
                    "prompt": "1boy, short dark hair, school uniform",
                    "negative_prompt": "1girl, blurry",
                    "loras": [],
                    "metadata": {}
                }
            ]
        }

    def test_01_canonical_binding_pose_contract(self):
        """Binding accepts shot_type, pose_preset, and interaction dictionary."""
        binding = {
            "character_id": "char_alice",
            "enabled": True,
            "prompt_override": "standing calmly",
            "area": {"x": 0.10, "y": 0.15, "w": 0.35, "h": 0.75},
            "shot_type": "half_body",
            "pose_preset": "facing_right",
            "interaction": {
                "type": "handshake",
                "role": "left_participant"
            },
            "metadata": {}
        }
        v = validate_character_binding(binding, available_character_ids={"char_alice"})
        self.assertEqual(v["shot_type"], "half_body")
        self.assertEqual(v["pose_preset"], "facing_right")
        self.assertEqual(v["interaction"]["type"], "handshake")
        self.assertEqual(v["metadata"]["shot_type"], "half_body")
        self.assertEqual(v["metadata"]["pose_preset"], "facing_right")

    def test_02_staging_override_deep_merge(self):
        """_commit_override and move/resize operations MUST NOT erase shot_type or pose_preset."""
        region_spec = {
            "version": 1,
            "panel_count": 1,
            "canvas": {"width": 1024, "height": 1024},
            "regions": [
                {
                    "id": 1,
                    "name": "Panel 1",
                    "enabled": True,
                    "x": 0.05, "y": 0.05, "w": 0.90, "h": 0.90,
                    "characters": [
                        {
                            "character_id": "char_alice",
                            "enabled": True,
                            "area": {"x": 0.10, "y": 0.15, "w": 0.35, "h": 0.75}
                        }
                    ]
                }
            ]
        }
        initial_overrides = {
            "1": {
                "char_alice": {
                    "area": {"x": 0.10, "y": 0.15, "w": 0.35, "h": 0.75},
                    "shot_type": "bust",
                    "pose_preset": "facing_left",
                    "interaction": {"type": "handshake"}
                }
            }
        }
        mgr = CharacterStagingStateManager(region_spec, initial_overrides)

        # Perform move operation
        new_area = mgr.move_character(panel_id=1, char_id="char_alice", dx=0.05, dy=0.02)
        self.assertAlmostEqual(new_area["x"], 0.15)
        self.assertAlmostEqual(new_area["y"], 0.17)

        # Verify that shot_type, pose_preset, and interaction are preserved
        stored_ov = mgr.overrides["1"]["char_alice"]
        self.assertEqual(stored_ov["shot_type"], "bust", "shot_type was erased during move!")
        self.assertEqual(stored_ov["pose_preset"], "facing_left", "pose_preset was erased during move!")
        self.assertEqual(stored_ov["interaction"]["type"], "handshake", "interaction was erased during move!")

        # Perform resize operation
        new_area_resize = mgr.resize_character(panel_id=1, char_id="char_alice", dw=0.05, dh=-0.05)
        self.assertAlmostEqual(new_area_resize["w"], 0.40)
        self.assertAlmostEqual(new_area_resize["h"], 0.70)
        stored_ov2 = mgr.overrides["1"]["char_alice"]
        self.assertEqual(stored_ov2["shot_type"], "bust", "shot_type was erased during resize!")
        self.assertEqual(stored_ov2["pose_preset"], "facing_left", "pose_preset was erased during resize!")

        # Verify apply_to_region_spec propagates all attributes
        updated_spec = mgr.apply_to_region_spec()
        c_applied = updated_spec["regions"][0]["characters"][0]
        self.assertEqual(c_applied["shot_type"], "bust")
        self.assertEqual(c_applied["pose_preset"], "facing_left")
        self.assertEqual(c_applied["interaction"]["type"], "handshake")

    def test_03_end_to_end_metadata_truth_flow(self):
        """End-to-end audit: Staging -> REGION_SPEC -> PAGE_COMPILE_PLAN -> Bridge -> IMPACT_REGION_PLAN."""
        base_region_spec = {
            "version": 1,
            "panel_count": 1,
            "canvas": {"width": 1024, "height": 1024},
            "regions": [
                {
                    "id": 1,
                    "name": "Panel 1",
                    "enabled": True,
                    "x": 0.05, "y": 0.05, "w": 0.90, "h": 0.90,
                    "characters": [
                        {
                            "character_id": "char_alice",
                            "enabled": True,
                            "prompt_override": "standing calmly",
                            "area": {"x": 0.10, "y": 0.15, "w": 0.35, "h": 0.75}
                        }
                    ]
                }
            ]
        }
        staging_overrides = {
            "1": {
                "char_alice": {
                    "area": {"x": 0.12, "y": 0.18, "w": 0.36, "h": 0.72},
                    "shot_type": "half_body",
                    "pose_preset": "facing_right",
                    "interaction": {"type": "handshake", "role": "left_participant"}
                }
            }
        }
        # 1. Staging Editor apply
        mgr = CharacterStagingStateManager(base_region_spec, staging_overrides)
        staged_region_spec = mgr.apply_to_region_spec()

        c_spec = staged_region_spec["regions"][0]["characters"][0]
        self.assertEqual(c_spec["shot_type"], "half_body")
        self.assertEqual(c_spec["pose_preset"], "facing_right")

        # 2. Page Compiler
        compiler = TegakiMangaPageCompiler()
        page_compile_plan, _, _, active_count = compiler.compile_page(
            region_spec=staged_region_spec,
            cast_spec=json.dumps(self.cast_spec)
        )
        self.assertEqual(active_count, 1)
        compiled_c = page_compile_plan["panels"][0]["characters"][0]
        self.assertEqual(compiled_c["shot_type"], "half_body", "shot_type lost in PAGE_COMPILE_PLAN!")
        self.assertEqual(compiled_c["pose_preset"], "facing_right", "pose_preset lost in PAGE_COMPILE_PLAN!")
        self.assertEqual(compiled_c["interaction"]["type"], "handshake")

        # 3. Layout Region Bridge
        layout_spec = get_default_panel_layout_spec(width=1024, height=1024, preset="1_full")
        bridge_data = build_panel_content_bridge(page_compile_plan, layout_spec)
        bridge_c = bridge_data["characters"][0]
        self.assertEqual(bridge_c["shot_type"], "half_body", "shot_type lost in LayoutRegionBridge!")
        self.assertEqual(bridge_c["pose_preset"], "facing_right", "pose_preset lost in LayoutRegionBridge!")
        self.assertEqual(bridge_c["interaction"]["type"], "handshake")

        # 4. Impact Region Plan
        impact_plan = build_impact_region_plan(
            page_compile_plan=page_compile_plan,
            panel_layout_spec=layout_spec,
            ordering_mode="scene_first",
            character_prompt_mode="standalone",
            include_panel_backgrounds=True,
            remainder_mask_mode=True
        )
        char_entries = [reg for reg in impact_plan["regions"] if reg["scope_type"] == "character_instance"]
        self.assertEqual(len(char_entries), 1)
        impact_c = char_entries[0]
        self.assertEqual(impact_c["shot_type"], "half_body", "shot_type lost in IMPACT_REGION_PLAN!")
        self.assertEqual(impact_c["pose_preset"], "facing_right", "pose_preset lost in IMPACT_REGION_PLAN!")
        self.assertEqual(impact_c["metadata"]["shot_type"], "half_body")
        self.assertEqual(impact_c["metadata"]["pose_preset"], "facing_right")
        self.assertEqual(impact_c["metadata"]["interaction"]["type"], "handshake")

    def test_04_fail_closed_invalid_enums(self):
        """Unknown shot_type and pose_preset must raise ValueError."""
        invalid_shot = {
            "character_id": "char_alice",
            "enabled": True,
            "shot_type": "extreme_macro_microscopic"
        }
        with self.assertRaises(ValueError):
            validate_character_binding(invalid_shot, available_character_ids={"char_alice"})

        invalid_pose = {
            "character_id": "char_alice",
            "enabled": True,
            "pose_preset": "somersault_backflip"
        }
        with self.assertRaises(ValueError):
            validate_character_binding(invalid_pose, available_character_ids={"char_alice"})

    def test_05_camera_distance_contract(self):
        """Scene camera_distance contract and explicit staging area precedence."""
        # Case A: Explicit staging area takes precedence over camera default
        c_explicit = {
            "character_id": "char_alice",
            "name": "Alice",
            "enabled": True,
            "area": {"x": 0.10, "y": 0.20, "w": 0.35, "h": 0.65}
        }
        panel_near = {
            "target_panel_id": 1,
            "enabled": True,
            "panel": {
                "id": 1,
                "enabled": True,
                "geometry": {"x": 0.05, "y": 0.05, "w": 0.90, "h": 0.90},
                "prompt": "courtyard",
                "negative_prompt": "blurry",
                "camera_distance": "near"
            },
            "canvas": {"width": 1024, "height": 1024},
            "global_prompt": "",
            "global_negative_prompt": "",
            "compiled_prompt": "",
            "compiled_negative_prompt": "",
            "characters": [c_explicit],
            "lora_plan": {"global_loras": [], "koma_loras": [], "character_loras": []},
            "status": "active",
            "version": 1
        }
        page_plan_explicit = {
            "version": 1,
            "canvas": {"width": 1024, "height": 1024},
            "active_panel_ids": [1],
            "global_prompt": "",
            "global_negative_prompt": "",
            "global_loras": [],
            "panels": [panel_near]
        }
        layout_spec = get_default_panel_layout_spec(width=1024, height=1024, preset="1_full")
        bridge_exp = build_panel_content_bridge(page_plan_explicit, layout_spec)
        c_b_exp = bridge_exp["characters"][0]
        # Must retain explicit coordinates exactly
        self.assertAlmostEqual(c_b_exp["koma_local_area"]["w"], 0.35)
        self.assertAlmostEqual(c_b_exp["koma_local_area"]["h"], 0.65)
        self.assertFalse(c_b_exp["is_unconstrained"])

        # Case B: Unconstrained character area adapts based on camera distance (near > medium > far)
        def get_unconstrained_scale(cam_dist: str):
            c_uncon = {
                "character_id": "char_alice",
                "name": "Alice",
                "enabled": True,
                "area": None
            }
            p = dict(panel_near)
            p["panel"] = dict(panel_near["panel"])
            p["panel"]["camera_distance"] = cam_dist
            p["characters"] = [c_uncon]
            pp = dict(page_plan_explicit)
            pp["panels"] = [p]
            b = build_panel_content_bridge(pp, layout_spec)
            entry = b["characters"][0]
            self.assertTrue(entry["is_unconstrained"])
            return entry["page_projected_area"]["w"] * entry["page_projected_area"]["h"]

        area_near = get_unconstrained_scale("near")
        area_medium = get_unconstrained_scale("medium")
        area_far = get_unconstrained_scale("far")

        self.assertGreater(area_near, area_medium, "near camera must be larger than medium")
        self.assertGreater(area_medium, area_far, "medium camera must be larger than far")


if __name__ == "__main__":
    unittest.main()
