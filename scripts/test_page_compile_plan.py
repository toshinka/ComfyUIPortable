import sys
import os
import json
import copy
import torch

# プロジェクトルートとカスタムノードへのパス解決
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CUSTOM_NODES_DIR = os.path.join(ROOT_DIR, "ComfyUI", "custom_nodes")
if CUSTOM_NODES_DIR not in sys.path:
    sys.path.insert(0, CUSTOM_NODES_DIR)
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from custom_nodes.tegaki_manga_nodes.scene_spec import (
    validate_page_compile_plan,
    SUPPORTED_PAGE_COMPILE_PLAN_VERSION,
    get_active_panel_ids
)
from custom_nodes.tegaki_manga_nodes.scene_compiler import (
    TegakiMangaPageCompiler,
    compile_panel_data
)
from custom_nodes.tegaki_manga_nodes.mask_builder import TegakiMangaMaskBuilder


def run_page_compile_plan_tests():
    print("================================================================================")
    print("PAGE_COMPILE_PLAN & Mask Projection Unit Tests (Phase 3B)")
    print("================================================================================")

    page_compiler = TegakiMangaPageCompiler()
    mask_builder = TegakiMangaMaskBuilder()

    # 3コマの基本 REGION_SPEC
    base_region_spec = {
        "version": 1,
        "canvas": {"width": 832, "height": 1216},
        "panel_count": 3,
        "global_prompt": "manga page, monochrome, expressive linework, high contrast <lora:clean_lineart:0.4>",
        "global_negative_prompt": "bad anatomy, color, photo",
        "regions": [
            {
                "id": 1,
                "name": "KOMA 1",
                "enabled": True,
                "x": 0.06, "y": 0.05, "w": 0.88, "h": 0.28,
                "prompt": "classroom, two people talking <lora:dramatic_angle:0.35>",
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
                        "area": None  # Unconstrained (area=None)
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
                "characters": []  # キャラなし背景コマ
            },
            {
                "id": 4,
                "name": "KOMA 4",
                "enabled": False,  # 無効コマ
                "x": 0.06, "y": 0.76, "w": 0.88, "h": 0.20,
                "prompt": "inactive slot",
                "characters": []
            }
        ]
    }

    test_cast_spec = {
        "version": 1,
        "characters": [
            {
                "id": "char_alice",
                "name": "Alice",
                "enabled": True,
                "prompt": "1girl, blonde twin tails, blue eyes",
                "negative_prompt": "blurry",
                "loras": [{"name": "alice_v1", "model_weight": 0.8, "clip_weight": 0.6, "enabled": True}]
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
    cast_json = json.dumps(test_cast_spec)

    # 1. Active panel IDs 検証
    print("\n--- 1. Testing get_active_panel_ids ---")
    active_ids = get_active_panel_ids(base_region_spec)
    assert active_ids == [1, 2, 3], f"Expected [1, 2, 3], got {active_ids}"
    print("get_active_panel_ids: PASSED")

    # 2. 3 KOMA 全体コンパイル (Page Compiler)
    print("\n--- 2. Testing TegakiMangaPageCompiler 3 KOMA compile ---")
    page_plan, page_json, global_loras_text, active_count = page_compiler.compile_page(
        region_spec=base_region_spec,
        cast_spec=cast_json,
        global_loras="<lora:manga_tone:0.5:0.3>"
    )
    assert active_count == 3
    assert len(page_plan["panels"]) == 3
    assert page_plan["active_panel_ids"] == [1, 2, 3]
    assert "<lora:manga_tone:0.5:0.3>" in global_loras_text
    assert "<lora:clean_lineart:0.4:0.4>" in global_loras_text
    print("PageCompiler 3 KOMA compile: PASSED")

    # 3. 各コマのCharacter構成検証 (2 in K1, 1 in K2, 0 in K3)
    print("\n--- 3. Testing Characters distribution across panels ---")
    p1 = page_plan["panels"][0]
    p2 = page_plan["panels"][1]
    p3 = page_plan["panels"][2]
    assert len(p1["characters"]) == 2, f"Expected 2 characters in K1, got {len(p1['characters'])}"
    assert len(p2["characters"]) == 1, f"Expected 1 character in K2, got {len(p2['characters'])}"
    assert len(p3["characters"]) == 0, f"Expected 0 characters in K3, got {len(p3['characters'])}"
    print("Characters distribution (2, 1, 0): PASSED")

    # 4. Mask Builder & Page 座標投影テスト
    print("\n--- 4. Testing Mask Builder and Page Coordinate Projection ---")
    p_masks, c_masks, preview, debug_json, lr_masks = mask_builder.build_masks(page_plan)
    assert p_masks.shape == (3, 1216, 832)
    assert c_masks.shape == (3, 1216, 832)  # Alice (K1), Bob (K1), Alice (K2) = 合計3体
    assert preview.shape == (1, 1216, 832, 3)

    debug_data = json.loads(debug_json)
    c_meta = debug_data["characters"]
    # Alice (KOMA 1): Left area
    alice_k1 = c_meta[0]
    assert alice_k1["character_id"] == "char_alice"
    assert alice_k1["panel_id"] == 1
    # page_x = 0.06 + 0.88 * 0.05 = 0.104
    assert round(alice_k1["page_projected_area"]["x"], 3) == 0.104

    # Bob (KOMA 1): Right area
    bob_k1 = c_meta[1]
    assert bob_k1["character_id"] == "char_bob"
    assert bob_k1["panel_id"] == 1
    # page_x = 0.06 + 0.88 * 0.53 = 0.5264
    assert round(bob_k1["page_projected_area"]["x"], 3) == 0.526
    assert bob_k1["page_projected_area"]["x"] > alice_k1["page_projected_area"]["x"]
    print("Page Coordinate Projection (Alice=Left, Bob=Right): PASSED")

    # 5. area=None の安全処理 (当該KOMA全体領域の採用)
    print("\n--- 5. Testing area=None handling (fallback to KOMA bounds) ---")
    alice_k2 = c_meta[2]
    assert alice_k2["character_id"] == "char_alice"
    assert alice_k2["panel_id"] == 2
    assert alice_k2["is_unconstrained"] is True
    # KOMA 2 の x=0.06, w=0.42 と完全に一致すること
    assert alice_k2["page_projected_area"]["x"] == 0.06
    assert alice_k2["page_projected_area"]["w"] == 0.42
    print("area=None fallback to KOMA bounds: PASSED")

    # 6. CASTなし背景のみページ互換動作 (全コマBindingなし)
    print("\n--- 6. Testing CAST Absent Compatibility (No character bindings) ---")
    no_char_spec = copy.deepcopy(base_region_spec)
    for r in no_char_spec["regions"]:
        r["characters"] = []
    page_plan_no_cast, _, _, count_no_cast = page_compiler.compile_page(no_char_spec, cast_spec="{}")
    assert count_no_cast == 3
    p_masks_nc, c_masks_nc, _, _, _ = mask_builder.build_masks(page_plan_no_cast)
    assert p_masks_nc.shape == (3, 1216, 832)
    assert c_masks_nc.shape == (1, 1216, 832)  # キャラ0人時は全ゼロのダミーマスク (1, H, W)
    assert torch.sum(c_masks_nc) == 0.0
    print("CAST Absent Compatibility: PASSED")

    # 7. Character Bindingあり + CASTなしの拒絶
    print("\n--- 7. Testing Character Binding present + CAST absent rejection ---")
    try:
        page_compiler.compile_page(base_region_spec, cast_spec="{}")
        assert False, "Should raise ValueError when binding exists without CAST_SPEC"
    except ValueError as e:
        assert "cast_spec is empty or missing" in str(e).lower()
        print(f"Binding without CAST rejected successfully: {e}")
    print("Character Binding without CAST rejection: PASSED")

    # 8. PAGE_COMPILE_PLAN Validator 検証 (異常データ拒絶)
    print("\n--- 8. Testing validate_page_compile_plan on corrupted plan ---")
    corrupted_page = copy.deepcopy(page_plan)
    corrupted_page["active_panel_ids"] = [1, 2, 999]  # 存在しないPanel ID
    try:
        validate_page_compile_plan(corrupted_page)
        assert False, "Should reject active_panel_ids with out of bounds ID"
    except ValueError as e:
        assert "elements must be strict int (1..6)" in str(e).lower()
        print(f"Corrupted active_panel_ids rejected successfully: {e}")
    print("PAGE_COMPILE_PLAN Validator: PASSED")

    print("\n================================================================================")
    print("[SUCCESS] ALL PAGE_COMPILE_PLAN & MASK BUILDER TESTS PASSED PERFECTLY!")
    print("================================================================================")
    return 0


if __name__ == "__main__":
    sys.exit(run_page_compile_plan_tests())
