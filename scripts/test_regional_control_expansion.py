import sys
import os
import json
import copy
import torch

# プロジェクトルートとカスタムノードへのパス解決
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
COMFYUI_DIR = os.path.join(ROOT_DIR, "ComfyUI")
CUSTOM_NODES_DIR = os.path.join(COMFYUI_DIR, "custom_nodes")
if COMFYUI_DIR not in sys.path:
    sys.path.insert(0, COMFYUI_DIR)
if CUSTOM_NODES_DIR not in sys.path:
    sys.path.insert(0, CUSTOM_NODES_DIR)
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from custom_nodes.tegaki_manga_nodes.scene_compiler import TegakiMangaPageCompiler
from custom_nodes.tegaki_manga_nodes.mask_builder import TegakiMangaMaskBuilder
from custom_nodes.tegaki_manga_nodes.conditioning_builder import TegakiMangaConditioningBuilder


class MockCLIP:
    """
    ComfyUI CLIP の最小モックオブジェクト (テスト用)
    """
    def tokenize(self, text):
        return {"text": text}

    def encode_from_tokens_scheduled(self, tokens):
        text = tokens.get("text", "")
        cond_tensor = torch.zeros((1, 77, 768), dtype=torch.float32)
        pooled_tensor = torch.zeros((1, 768), dtype=torch.float32)
        return [[cond_tensor, {"pooled_output": pooled_tensor, "debug_text": text}]]


def run_regional_control_expansion_tests():
    print("================================================================================")
    print("Regional Control Expansion Integration Tests (Phase 3B.1)")
    print("================================================================================")

    page_compiler = TegakiMangaPageCompiler()
    mask_builder = TegakiMangaMaskBuilder()
    cond_builder = TegakiMangaConditioningBuilder()
    mock_clip = MockCLIP()

    # 4階層（Global, Panel, Local Region, Character）を含む REGION_SPEC
    # KOMA 1: Alice (左) + Bob (右) + Local Region 1 (窓際机群・Aliceと一部重複/Overlap)
    # KOMA 2: Alice (Full) + Local Region 1 (掲示板ポスター)
    # KOMA 3: 背景のみ (夕暮れ屋上)
    expansion_spec = {
        "version": 1,
        "canvas": {"width": 832, "height": 1216},
        "panel_count": 3,
        "global_prompt": "manga page, monochrome, expressive linework",
        "global_negative_prompt": "bad anatomy, color, photo",
        "regions": [
            {
                "id": 1,
                "name": "KOMA 1",
                "enabled": True,
                "x": 0.06, "y": 0.05, "w": 0.88, "h": 0.28,
                "prompt": "classroom, two people talking",
                "negative_prompt": "empty room",
                "local_regions": [
                    {
                        "id": "lr_desks",
                        "name": "Window Desks",
                        "enabled": True,
                        "prompt": "school desks near the window, sunlight streaming",
                        "negative_prompt": "dark",
                        "area": {"x": 0.10, "y": 0.20, "w": 0.40, "h": 0.60}  # Aliceの領域と重複(Overlap)
                    }
                ],
                "characters": [
                    {
                        "character_id": "char_alice",
                        "enabled": True,
                        "prompt_override": "annoyed, looking right",
                        "negative_prompt_override": "happy",
                        "area": {"x": 0.05, "y": 0.10, "w": 0.42, "h": 0.80}
                    },
                    {
                        "character_id": "char_bob",
                        "enabled": True,
                        "prompt_override": "laughing, looking left",
                        "negative_prompt_override": "crying",
                        "area": {"x": 0.53, "y": 0.10, "w": 0.42, "h": 0.80}
                    }
                ]
            },
            {
                "id": 2,
                "name": "KOMA 2",
                "enabled": True,
                "x": 0.06, "y": 0.36, "w": 0.42, "h": 0.38,
                "prompt": "school corridor, walking scene",
                "negative_prompt": "",
                "local_regions": [
                    {
                        "id": "lr_posters",
                        "name": "Wall Posters",
                        "enabled": True,
                        "prompt": "posters on school wall, bulletin board",
                        "negative_prompt": "",
                        "area": {"x": 0.60, "y": 0.15, "w": 0.35, "h": 0.40}
                    }
                ],
                "characters": [
                    {
                        "character_id": "char_alice",
                        "enabled": True,
                        "prompt_override": "walking away, back view",
                        "area": None
                    }
                ]
            },
            {
                "id": 3,
                "name": "KOMA 3",
                "enabled": True,
                "x": 0.52, "y": 0.36, "w": 0.42, "h": 0.38,
                "prompt": "sunset rooftop, empty scenic",
                "negative_prompt": "people",
                "local_regions": [],
                "characters": []
            }
        ]
    }

    cast_spec = {
        "version": 1,
        "characters": [
            {
                "id": "char_alice",
                "name": "Alice",
                "enabled": True,
                "prompt": "1girl, blonde twin tails",
                "negative_prompt": "blurry",
                "loras": []
            },
            {
                "id": "char_bob",
                "name": "Bob",
                "enabled": True,
                "prompt": "1boy, short brown hair",
                "negative_prompt": "bad hands",
                "loras": []
            }
        ]
    }

    # 1. Page Compile with Local Regions
    print("\n--- 1. Testing Page compile with local_regions ---")
    page_plan, page_json, _, active_count = page_compiler.compile_page(
        region_spec=expansion_spec,
        cast_spec=json.dumps(cast_spec)
    )
    assert active_count == 3
    p1 = page_plan["panels"][0]
    p2 = page_plan["panels"][1]
    p3 = page_plan["panels"][2]

    assert len(p1["panel"]["local_regions"]) == 1
    assert p1["panel"]["local_regions"][0]["id"] == "lr_desks"
    assert "school desks" in p1["panel"]["local_regions"][0]["prompt"]
    assert len(p2["panel"]["local_regions"]) == 1
    assert p2["panel"]["local_regions"][0]["id"] == "lr_posters"
    assert len(p3["panel"]["local_regions"]) == 0
    print("Page compile with local_regions: PASSED")

    # 2. Mask Projection for Local Regions
    print("\n--- 2. Testing Mask projection for local_regions ---")
    p_masks, c_masks, preview, debug_json, lr_masks = mask_builder.build_masks(page_plan, mask_feather=4)
    assert p_masks.shape == (3, 1216, 832)
    assert c_masks.shape == (3, 1216, 832)
    assert lr_masks.shape == (2, 1216, 832)  # lr_desks (K1), lr_posters (K2) = 2個
    assert preview.shape == (1, 1216, 832, 3)

    debug_data = json.loads(debug_json)
    lr_meta = debug_data["local_regions"]
    assert len(lr_meta) == 2
    # K1 lr_desks: page_x = 0.06 + 0.88 * 0.10 = 0.148
    assert round(lr_meta[0]["page_projected_area"]["x"], 3) == 0.148
    # K2 lr_posters: page_x = 0.06 + 0.42 * 0.60 = 0.312
    assert round(lr_meta[1]["page_projected_area"]["x"], 3) == 0.312
    print("Mask projection for local_regions: PASSED")

    # 3. Conditioning Count includes Local Regions (4-Tier Hierarchy)
    print("\n--- 3. Testing 4-tier Conditioning generation and branch count ---")
    pos_cond, neg_cond, p_m, c_m, lr_m, cond_debug_json = cond_builder.build_conditioning(
        clip=mock_clip,
        page_compile_plan=page_plan,
        panel_strength=0.9,
        character_strength=0.85,
        set_cond_area="default",
        local_region_strength=0.8,
        mask_feather=2
    )
    # Expected Positive branches:
    # 1 (Global) + 3 (KOMA 1,2,3) + 2 (Local Region 1,2) + 3 (Characters: Alice K1, Bob K1, Alice K2) = 9
    assert len(pos_cond) == 9, f"Expected 9 positive branches, got {len(pos_cond)}"

    # Branch order:
    # 0: Global
    assert "mask" not in pos_cond[0][1], "Global positive must NOT have mask"
    # 1..3: Panels (strength=0.9)
    for i in range(1, 4):
        assert pos_cond[i][1]["mask_strength"] == 0.9
    # 4..5: Local Regions (strength=0.8)
    for i in range(4, 6):
        assert pos_cond[i][1]["mask_strength"] == 0.8
    # 6..8: Characters (strength=0.85)
    for i in range(6, 9):
        assert pos_cond[i][1]["mask_strength"] == 0.85

    print("4-tier Conditioning branch count and priority order: PASSED")

    # 4. Overlapping Character / Local Region Support
    print("\n--- 4. Testing Overlap between Character and Local Region ---")
    # Alice KOMA 1 (c_masks[0]) と lr_desks (lr_masks[0]) の領域重なりを確認
    overlap_area = (c_masks[0] > 0.0) & (lr_masks[0] > 0.0)
    overlap_pixel_count = torch.sum(overlap_area).item()
    assert overlap_pixel_count > 0, "Character area and Local Region should have overlapping pixels"
    print(f"Overlap detected and safely handled ({overlap_pixel_count} overlapping pixels): PASSED")

    # 5. Existing Character-Only Compile Remains Valid (100% Backward Compatibility)
    print("\n--- 5. Testing Backward Compatibility (Character-only spec) ---")
    legacy_spec = copy.deepcopy(expansion_spec)
    for r in legacy_spec["regions"]:
        r.pop("local_regions", None)
    legacy_plan, _, _, legacy_count = page_compiler.compile_page(legacy_spec, json.dumps(cast_spec))
    assert legacy_count == 3
    leg_p_m, leg_c_m, _, _, leg_lr_m = mask_builder.build_masks(legacy_plan)
    assert leg_lr_m.shape == (1, 1216, 832)
    assert torch.sum(leg_lr_m) == 0.0  # Local Region 0個の場合は全ゼロダミーマスク
    leg_pos, leg_neg, _, _, _, _ = cond_builder.build_conditioning(mock_clip, legacy_plan)
    # Global(1) + Panels(3) + Local(0) + Chars(3) = 7
    assert len(leg_pos) == 7
    print("Backward Compatibility (Character-only compile): PASSED")

    print("\n================================================================================")
    print("[SUCCESS] ALL REGIONAL CONTROL EXPANSION TESTS PASSED PERFECTLY!")
    print("================================================================================")
    return 0


if __name__ == "__main__":
    sys.exit(run_regional_control_expansion_tests())
