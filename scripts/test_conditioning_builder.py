import sys
import os
import json
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
from custom_nodes.tegaki_manga_nodes.conditioning_builder import TegakiMangaConditioningBuilder


class MockCLIP:
    """
    ComfyUI CLIP の最小モックオブジェクト (テスト用)
    """
    def tokenize(self, text):
        return {"text": text}

    def encode_from_tokens_scheduled(self, tokens):
        text = tokens.get("text", "")
        # ComfyUI標準 conditioning 形式: [[tensor, {"pooled_output": tensor}]]
        cond_tensor = torch.zeros((1, 77, 768), dtype=torch.float32)
        pooled_tensor = torch.zeros((1, 768), dtype=torch.float32)
        return [[cond_tensor, {"pooled_output": pooled_tensor, "debug_text": text}]]


def run_conditioning_builder_tests():
    print("================================================================================")
    print("Tegaki Manga Conditioning Builder Unit Tests (Phase 3B)")
    print("================================================================================")

    page_compiler = TegakiMangaPageCompiler()
    cond_builder = TegakiMangaConditioningBuilder()
    mock_clip = MockCLIP()

    region_spec = {
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
                "prompt": "corridor view",
                "negative_prompt": "",
                "characters": [
                    {
                        "character_id": "char_alice",
                        "enabled": True,
                        "prompt_override": "walking away",
                        "area": None
                    }
                ]
            },
            {
                "id": 3,
                "name": "KOMA 3",
                "enabled": True,
                "x": 0.52, "y": 0.36, "w": 0.42, "h": 0.38,
                "prompt": "sunset rooftop",
                "negative_prompt": "",
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
                "prompt": "1girl, blonde twin tails, blue eyes",
                "negative_prompt": "blurry",
                "loras": []
            },
            {
                "id": "char_bob",
                "name": "Bob",
                "enabled": True,
                "prompt": "1boy, short brown hair, uniform",
                "negative_prompt": "bad hands",
                "loras": []
            }
        ]
    }

    # 1. PAGE_COMPILE_PLAN の生成
    page_plan, _, _, _ = page_compiler.compile_page(
        region_spec=region_spec,
        cast_spec=json.dumps(cast_spec)
    )

    # 2. Conditioning Builder の実行
    print("\n--- 1. Testing build_conditioning execution ---")
    pos_cond, neg_cond, p_masks, c_masks, debug_json, lr_masks = cond_builder.build_conditioning(
        clip=mock_clip,
        page_compile_plan=page_plan,
        panel_strength=0.9,
        character_strength=0.85,
        set_cond_area="default",
        local_region_strength=1.0,
        mask_feather=0
    )

    debug_data = json.loads(debug_json)
    print(f"Total Positive Branches: {len(pos_cond)}")
    print(f"Total Negative Branches: {len(neg_cond)}")

    # 3. Positive Conditioning の構成検証
    # 期待されるブランチ:
    # 1 (Global) + 3 (K1, K2, K3) + 3 (Alice K1, Bob K1, Alice K2) = 7
    print("\n--- 2. Testing Positive Conditioning branches ---")
    assert len(pos_cond) == 7, f"Expected 7 positive branches, got {len(pos_cond)}"

    # Branch 0: Global Positive (マスクなし)
    assert "mask" not in pos_cond[0][1], "Global positive must NOT have a mask"
    assert "manga page" in pos_cond[0][1]["debug_text"]

    # Branch 1..3: Panel Positives (マスクあり、panel_strength=0.9)
    for p_i in range(1, 4):
        branch = pos_cond[p_i]
        assert "mask" in branch[1], f"Panel {p_i} must have a mask"
        assert branch[1]["mask_strength"] == 0.9, f"Expected mask_strength=0.9, got {branch[1]['mask_strength']}"

    # Branch 4..6: Character Positives (マスクあり、character_strength=0.85)
    for c_i in range(4, 7):
        branch = pos_cond[c_i]
        assert "mask" in branch[1], f"Character {c_i} must have a mask"
        assert branch[1]["mask_strength"] == 0.85, f"Expected mask_strength=0.85, got {branch[1]['mask_strength']}"

    print("Positive Conditioning branches: PASSED")

    # 4. Negative Conditioning の構成検証
    # 期待されるブランチ:
    # 1 (Global) + 1 (K1: empty room) + 3 (Alice K1: blurry, happy / Bob K1: bad hands, crying / Alice K2: blurry) = 5
    print("\n--- 3. Testing Negative Conditioning branches ---")
    assert len(neg_cond) == 5, f"Expected 5 negative branches, got {len(neg_cond)}"
    assert "mask" not in neg_cond[0][1], "Global negative must NOT have a mask"
    assert "bad anatomy" in neg_cond[0][1]["debug_text"]

    for n_i in range(1, 5):
        assert "mask" in neg_cond[n_i][1], f"Masked negative branch {n_i} must have a mask"
    print("Negative Conditioning branches: PASSED")

    # 5. Mask Shapes 検証
    print("\n--- 4. Testing Mask shapes ---")
    assert p_masks.shape == (3, 1216, 832)
    assert c_masks.shape == (3, 1216, 832)
    print("Mask shapes (3, 1216, 832): PASSED")

    print("\n================================================================================")
    print("[SUCCESS] ALL CONDITIONING BUILDER TESTS PASSED PERFECTLY!")
    print("================================================================================")
    return 0


if __name__ == "__main__":
    sys.exit(run_conditioning_builder_tests())
