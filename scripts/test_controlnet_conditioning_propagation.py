"""
Phase 3I.1: ControlNet Conditioning Propagation & Metadata Inspection
====================================================================
Programmatically inspects the mechanics of conditioning propagation between:
1. Base Sampler (with ControlNet applied via ControlNetApplyAdvanced)
2. Regional Prompts (encoded via CLIPTextEncode in TegakiMangaImpactRegionalAdapter)
3. Cloned Regional Samplers (via KSamplerAdvancedWrapper.clone_with_conditionings)

Audits Section 18 of Phase 3I.1 Request:
- Base positive conditioning: control metadata present?
- Regional encoded positive: control metadata present?
- clone_with_conditionings result: which conditioning stored?
- Regional sampler receives control: YES / NO / UNKNOWN
"""

import sys
import os
import unittest
import torch

# Ensure ComfyUI and custom nodes are on path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
COMFY_DIR = os.path.join(ROOT_DIR, "ComfyUI")
CUSTOM_NODES_DIR = os.path.join(ROOT_DIR, "custom_nodes_custom")
IMPACT_PACK_DIR = os.path.join(COMFY_DIR, "custom_nodes", "ComfyUI-Impact-Pack", "modules")

for p in [ROOT_DIR, COMFY_DIR, CUSTOM_NODES_DIR, IMPACT_PACK_DIR]:
    if p not in sys.path:
        sys.path.insert(0, p)

from impact.impact_sampling import KSamplerAdvancedWrapper
from custom_nodes_custom.tegaki_manga_nodes.manga_impact_regional_adapter import TegakiMangaImpactRegionalAdapter


class MockControlNet:
    """Mock ControlNet instance simulating AnyTest v4 object."""
    def __init__(self, name="AnyTest_v4"):
        self.name = name

    def copy(self):
        c = MockControlNet(self.name)
        c.cond_hint_original = getattr(self, "cond_hint_original", None)
        c.strength = getattr(self, "strength", 1.0)
        c.timestep_percent_range = getattr(self, "timestep_percent_range", (0.0, 1.0))
        return c

    def set_cond_hint(self, cond_hint, strength=1.0, timestep_percent_range=(0.0, 1.0), vae=None, extra_concat=[]):
        self.cond_hint_original = cond_hint
        self.strength = strength
        self.timestep_percent_range = timestep_percent_range
        return self

    def set_previous_controlnet(self, prev):
        self.prev = prev
        return self


class MockCLIP:
    """Mock CLIP instance simulating SDXL tokenization & scheduled encoding."""
    def tokenize(self, text):
        return {"g": [[1, 2, 3]], "l": [[4, 5, 6]]}

    def encode_from_tokens_scheduled(self, tokens):
        # Standard ComfyUI CLIP conditioning structure:
        # list of [cond_tensor, {"pooled_output": pooled_tensor}]
        cond_tensor = torch.zeros((1, 77, 2048), dtype=torch.float32)
        pooled_tensor = torch.zeros((1, 1280), dtype=torch.float32)
        return [[cond_tensor, {"pooled_output": pooled_tensor}]]


def simulate_controlnet_apply(positive, negative, control_net, image, strength=0.75, start_percent=0.0, end_percent=0.80):
    """Exact logic of ComfyUI's ControlNetApplyAdvanced.apply_controlnet."""
    control_hint = image
    cnets = {}
    out = []
    for conditioning in [positive, negative]:
        c = []
        for t in conditioning:
            d = t[1].copy()
            prev_cnet = d.get('control', None)
            c_net = control_net.copy().set_cond_hint(control_hint, strength, (start_percent, end_percent))
            c_net.set_previous_controlnet(prev_cnet)
            d['control'] = c_net
            d['control_apply_to_uncond'] = False
            c.append([t[0], d])
        out.append(c)
    return out[0], out[1]


class TestControlNetConditioningPropagation(unittest.TestCase):
    def setUp(self):
        self.clip = MockCLIP()
        self.adapter = TegakiMangaImpactRegionalAdapter()
        self.control_net = MockControlNet("AnyTest_v4")
        self.image = torch.zeros((1, 3, 1024, 1024), dtype=torch.float32)

        # 1. Simulate base prompt encoding
        base_pos_raw = self.adapter._encode_text(self.clip, "manga illustration, simple clean background")
        base_neg_raw = self.adapter._encode_text(self.clip, "worst quality, low quality, blurry")

        # 2. Apply ControlNet to base conditioning (as in WF35-39 Node 32)
        self.base_pos_cn, self.base_neg_cn = simulate_controlnet_apply(
            base_pos_raw, base_neg_raw, self.control_net, self.image, strength=0.75, start_percent=0.0, end_percent=0.80
        )

        # 3. Create base sampler (Node 6 KSamplerAdvancedProvider)
        mock_model = "MOCK_SDXL_MODEL"
        self.base_sampler = KSamplerAdvancedWrapper(
            model=mock_model,
            cfg=7.0,
            sampler_name="euler",
            scheduler="normal",
            positive=self.base_pos_cn,
            negative=self.base_neg_cn,
            sigma_factor=1.0
        )

    def test_01_base_conditioning_has_control(self):
        """Verify that base positive and negative conditioning carry 'control' metadata."""
        base_pos_dict = self.base_pos_cn[0][1]
        self.assertIn("control", base_pos_dict, "Base positive conditioning must have 'control' key.")
        self.assertIsInstance(base_pos_dict["control"], MockControlNet)
        print("\n[Audit Item 1] Base positive conditioning: control metadata present? YES")

    def test_02_regional_encoded_positive_lacks_control(self):
        """Verify that freshly encoded regional prompts do NOT carry 'control' metadata."""
        regional_prompt = "1girl, alice, standing calmly"
        regional_pos = self.adapter._encode_text(self.clip, regional_prompt)
        regional_pos_dict = regional_pos[0][1]

        self.assertNotIn("control", regional_pos_dict, "Freshly encoded regional conditioning must NOT have 'control'.")
        print("[Audit Item 2] Regional encoded positive: control metadata present? NO")

    def test_03_cloned_regional_sampler_discards_control(self):
        """Verify that base_sampler.clone_with_conditionings replaces conditionings with regional ones lacking control."""
        regional_prompt = "1girl, alice, standing calmly"
        regional_neg = "worst quality, blurry"
        regional_pos = self.adapter._encode_text(self.clip, regional_prompt)
        regional_neg_cond = self.adapter._encode_text(self.clip, regional_neg)

        # Clone sampler with regional conditionings
        regional_sampler = self.base_sampler.clone_with_conditionings(regional_pos, regional_neg_cond)

        # Extract stored conditionings: self.params = model, cfg, sampler_name, scheduler, positive, negative, sigma_factor
        stored_pos = regional_sampler.params[4]
        stored_neg = regional_sampler.params[5]

        # Stored conditioning is exactly the regional conditioning
        self.assertEqual(stored_pos, regional_pos)
        self.assertEqual(stored_neg, regional_neg_cond)
        print("[Audit Item 3] clone_with_conditionings result: which conditioning stored? Newly passed regional conditionings")

        # Check if stored positive in regional sampler has control
        stored_pos_dict = stored_pos[0][1]
        has_control = "control" in stored_pos_dict
        self.assertFalse(has_control, "Regional sampler positive conditioning must NOT have control metadata.")
        print("[Audit Item 4] Regional sampler receives control: NO (Base-Only)")

    def test_04_propagate_controlnet_to_regions_prototype(self):
        """Verify that when propagate_controlnet_to_regions=True, regional samplers receive cloned control metadata."""
        from tegaki_manga_nodes.scene_compiler import TegakiMangaPageCompiler
        from tegaki_manga_nodes.cast_master import get_default_cast_spec
        from tegaki_manga_nodes.panel_layout_spec import get_default_panel_layout_spec
        from tegaki_manga_nodes.region_editor import default_region_spec

        cast_data = get_default_cast_spec()
        layout_data = get_default_panel_layout_spec(512, 512, preset="1_full")
        reg_spec = default_region_spec(512, 512, panel_count=1)
        # compile
        page_compiler = TegakiMangaPageCompiler()
        compile_plan, _, _, _ = page_compiler.compile_page(
            region_spec=reg_spec,
            cast_spec=cast_data
        )

        # Run with propagate_controlnet_to_regions=False (Base-only default)
        res_default = self.adapter.build_regional_prompts(
            page_compile_plan=compile_plan,
            panel_layout_spec=layout_data,
            base_sampler=self.base_sampler,
            clip=self.clip,
            propagate_controlnet_to_regions=False
        )
        rps_default = res_default[0]
        default_char_rp = rps_default[-1]
        stored_default_pos = default_char_rp.sampler.params[4]
        self.assertNotIn("control", stored_default_pos[0][1])

        # Run with propagate_controlnet_to_regions=True (Prototype A/B toggle)
        res_propagated = self.adapter.build_regional_prompts(
            page_compile_plan=compile_plan,
            panel_layout_spec=layout_data,
            base_sampler=self.base_sampler,
            clip=self.clip,
            propagate_controlnet_to_regions=True
        )
        rps_propagated = res_propagated[0]
        propagated_char_rp = rps_propagated[-1]
        stored_prop_pos = propagated_char_rp.sampler.params[4]
        self.assertIn("control", stored_prop_pos[0][1])
        self.assertIsInstance(stored_prop_pos[0][1]["control"], MockControlNet)
        print("[Audit Item 5] Prototype propagate_controlnet_to_regions: Successfully attached to regional conditionings! YES")

    def test_05_per_region_hint_prototype(self):
        """Verify that regional_control_mode='per_region_hint' applies isolated hints only to character instances."""
        from tegaki_manga_nodes.scene_compiler import TegakiMangaPageCompiler
        from tegaki_manga_nodes.cast_master import get_default_cast_spec
        from tegaki_manga_nodes.panel_layout_spec import get_default_panel_layout_spec
        from tegaki_manga_nodes.region_editor import default_region_spec

        cast_data = get_default_cast_spec()
        layout_data = get_default_panel_layout_spec(512, 512, preset="1_full")
        reg_spec = default_region_spec(512, 512, panel_count=1)
        reg_spec["regions"][0]["characters"] = [
            {"character_id": "char_alice", "name": "Alice", "enabled": True, "area": {"x": 0.1, "y": 0.15, "w": 0.4, "h": 0.75}},
            {"character_id": "char_bob", "name": "Bob", "enabled": True, "area": {"x": 0.55, "y": 0.15, "w": 0.35, "h": 0.75}}
        ]
        page_compiler = TegakiMangaPageCompiler()
        compile_plan, _, _, _ = page_compiler.compile_page(
            region_spec=reg_spec,
            cast_spec=cast_data
        )

        res_per_region = self.adapter.build_regional_prompts(
            page_compile_plan=compile_plan,
            panel_layout_spec=layout_data,
            base_sampler=self.base_sampler,
            clip=self.clip,
            regional_control_mode="per_region_hint",
            regional_control_strength=0.35
        )
        rps = res_per_region[0]
        # First region is panel_scene
        panel_rp = rps[0]
        panel_pos = panel_rp.sampler.params[4]
        self.assertNotIn("control", panel_pos[0][1], "Panel scene must NOT receive character ControlNet in per_region_hint mode.")

        # Next regions are character instances
        char_rps = rps[1:]
        self.assertEqual(len(char_rps), 2)
        for c_rp in char_rps:
            c_pos = c_rp.sampler.params[4]
            self.assertIn("control", c_pos[0][1], "Character instance must receive ControlNet in per_region_hint mode.")
            c_ctrl = c_pos[0][1]["control"]
            self.assertEqual(c_ctrl.strength, 0.35, "Per-region control strength must be attenuated to 0.35.")
            self.assertIsNotNone(getattr(c_ctrl, "cond_hint_original", None), "Character hint must be attached.")
        print("[Audit Item 6] Prototype per_region_hint: Isolated character hints with attenuated strength 0.35 verified! YES")


def run_audit():
    print("=" * 80)
    print("Phase 3I.1: ControlNet Conditioning Propagation & Metadata Inspection")
    print("=" * 80)
    suite = unittest.TestLoader().loadTestsFromTestCase(TestControlNetConditioningPropagation)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    print("=" * 80)
    print(f"Summary Conclusion: ControlNet conditioning operates BASE_ONLY in current architecture.")
    print("=" * 80)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(run_audit())
