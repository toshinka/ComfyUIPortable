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

from custom_nodes.tegaki_manga_nodes.two_region_core_conditioner import TegakiTwoRegionCoreConditioner
from custom_nodes.tegaki_manga_nodes.two_region_spec import get_default_two_region_spec


class MockCLIP:
    def tokenize(self, text):
        return {"mock_tokens": [1, 2, 3]}

    def encode_from_tokens_scheduled(self, tokens):
        # ComfyUI conditioning format: [[tensor, dict]]
        cond_tensor = torch.zeros((1, 77, 768), dtype=torch.float32)
        return [[cond_tensor, {}]]


def test_core_conditioner_branches():
    print("\n--- 1. Testing Core Conditioner Branch Generation ---")
    cond_builder = TegakiTwoRegionCoreConditioner()
    mock_clip = MockCLIP()

    spec = get_default_two_region_spec(512, 768)
    spec["global_prompt"] = "masterpiece, anime"
    spec["regions"][0]["prompt"] = "1girl, blonde hair"
    spec["regions"][1]["prompt"] = "1boy, black hair"

    pos_cond, neg_cond, mask_A, mask_B, debug_json = cond_builder.build_conditioning(
        clip=mock_clip,
        two_region_spec=spec,
        strength_A=1.0,
        strength_B=0.9,
        set_cond_area="default",
        mask_feather=0
    )

    # 期待される Positive ブランチ:
    # 1 (Global) + 1 (Region A) + 1 (Region B) = 3
    assert len(pos_cond) == 3, f"Expected 3 positive branches, got {len(pos_cond)}"
    assert mask_A.shape == (1, 768, 512)
    assert mask_B.shape == (1, 768, 512)

    # Branch 0 (Global) は mask なし
    assert "mask" not in pos_cond[0][1]
    # Branch 1 (Region A) は mask_A
    assert "mask" in pos_cond[1][1]
    assert pos_cond[1][1]["mask_strength"] == 1.0
    # Branch 2 (Region B) は mask_B
    assert "mask" in pos_cond[2][1]
    assert pos_cond[2][1]["mask_strength"] == 0.9

    print("  3-branch Positive Conditioning structure: PASSED")


def test_feather_and_finite_validation():
    print("\n--- 2. Testing Feathering and Finite Float Validation ---")
    cond_builder = TegakiTwoRegionCoreConditioner()
    mock_clip = MockCLIP()
    spec = get_default_two_region_spec(512, 768)

    pos_cond, neg_cond, mask_A, mask_B, debug_json = cond_builder.build_conditioning(
        clip=mock_clip,
        two_region_spec=spec,
        strength_A=1.0,
        strength_B=1.0,
        mask_feather=4
    )
    # フェザー適用後のマスクには 0 と 1 の間の中間値が存在するはず
    intermediate_vals = ((mask_A > 0.0) & (mask_A < 1.0)).sum().item()
    assert intermediate_vals > 0, "Gaussian feather should create intermediate float values"
    print(f"  Gaussian feather intermediate pixels: {intermediate_vals} [PASSED]")

    # NaN 検証
    try:
        cond_builder.build_conditioning(
            clip=mock_clip,
            two_region_spec=spec,
            strength_A=float("nan")
        )
        assert False, "Should reject NaN strength"
    except ValueError as e:
        assert "finite float" in str(e)
    print("  NaN strength rejection: PASSED")


def test_one_region_disabled_branch():
    print("\n--- 3. Testing One Region Disabled Branches ---")
    cond_builder = TegakiTwoRegionCoreConditioner()
    mock_clip = MockCLIP()
    spec = get_default_two_region_spec(512, 768)
    spec["regions"][1]["enabled"] = False  # B を無効化

    pos_cond, neg_cond, mask_A, mask_B, debug_json = cond_builder.build_conditioning(
        clip=mock_clip,
        two_region_spec=spec
    )
    # 期待されるブランチ: 1 (Global) + 1 (Region A) = 2
    assert len(pos_cond) == 2, f"Expected 2 positive branches, got {len(pos_cond)}"
    print("  One region disabled branch count (2): PASSED")


def run_all():
    print("================================================================================")
    print("Running TegakiTwoRegionCoreConditioner Tests (Phase 3C-3)")
    print("================================================================================")
    test_core_conditioner_branches()
    test_feather_and_finite_validation()
    test_one_region_disabled_branch()
    print("\n================================================================================")
    print("[SUCCESS] ALL CORE CONDITIONER TESTS PASSED!")
    print("================================================================================")
    return 0


if __name__ == "__main__":
    sys.exit(run_all())
