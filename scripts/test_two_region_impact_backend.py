import os
import sys
import json
import torch

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CUSTOM_NODES_DIR = os.path.join(ROOT_DIR, "ComfyUI", "custom_nodes")
if CUSTOM_NODES_DIR not in sys.path:
    sys.path.insert(0, CUSTOM_NODES_DIR)
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from custom_nodes.tegaki_manga_nodes.two_region_impact_adapter import TegakiTwoRegionImpactAdapter
from custom_nodes.tegaki_manga_nodes.two_region_spec import get_default_two_region_spec


class MockAdvancedSampler:
    def __init__(self, name="mock_sampler"):
        self.name = name


def test_impact_adapter():
    print("\n--- 1. Testing Impact Adapter REGIONAL_PROMPTS generation ---")
    adapter = TegakiTwoRegionImpactAdapter()
    spec = get_default_two_region_spec(512, 768)

    sampler_A = MockAdvancedSampler("sampler_A")
    sampler_B = MockAdvancedSampler("sampler_B")

    regional_prompts, mask_A, mask_B, debug_json = adapter.build_impact_prompts(
        two_region_spec=spec,
        sampler_A=sampler_A,
        sampler_B=sampler_B,
        variation_seed=42,
        variation_strength=0.2,
        variation_method="linear"
    )

    assert len(regional_prompts) == 2, f"Expected 2 regional prompts, got {len(regional_prompts)}"
    assert mask_A.shape == (1, 768, 512)
    assert mask_B.shape == (1, 768, 512)

    # 各プロンプトのサンプラーとマスク
    assert regional_prompts[0].sampler.name == "sampler_A"
    assert regional_prompts[1].sampler.name == "sampler_B"
    assert regional_prompts[0].variation_seed == 42
    assert regional_prompts[0].variation_strength == 0.2

    print("  Impact Adapter REGIONAL_PROMPTS construction: PASSED")


def run_all():
    print("================================================================================")
    print("Running TegakiTwoRegionImpactAdapter Tests (Phase 3C-4)")
    print("================================================================================")
    test_impact_adapter()
    print("\n================================================================================")
    print("[SUCCESS] ALL IMPACT ADAPTER TESTS PASSED!")
    print("================================================================================")
    return 0


if __name__ == "__main__":
    sys.exit(run_all())
