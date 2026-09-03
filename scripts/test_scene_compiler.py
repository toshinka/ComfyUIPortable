import sys
import os
import json
import copy

comfy_dir = os.path.abspath("ComfyUI")
sys.path.insert(0, comfy_dir)

from custom_nodes.tegaki_manga_nodes.region_editor import default_region_spec
from custom_nodes.tegaki_manga_nodes.scene_compiler import TegakiMangaSceneCompiler

def run_scene_compiler_tests():
    print("================================================================================")
    print("Tegaki Manga Scene Compiler (Phase 3A) Integration Tests")
    print("================================================================================")

    compiler = TegakiMangaSceneCompiler()

    # 共通フィクスチャ: 3コマ漫画 REGION_SPEC
    base_region_spec = default_region_spec(
        width=832,
        height=1216,
        panel_count=3,
        global_prompt="manga page, monochrome, ink lineart, high contrast"
    )

    # 共通フィクスチャ: CAST_SPEC (Alice, Bob, Carol)
    test_cast_spec = {
        "version": 1,
        "characters": [
            {
                "id": "char_alice",
                "name": "Alice",
                "enabled": True,
                "prompt": "1girl, blonde twin tails, blue eyes, school uniform",
                "negative_prompt": "",
                "loras": [
                    {"name": "alice_v1", "weight": 0.8, "enabled": True}
                ]
            },
            {
                "id": "char_bob",
                "name": "Bob",
                "enabled": True,
                "prompt": "1boy, short brown hair, school uniform",
                "negative_prompt": "",
                "loras": [
                    {"name": "bob_v1", "weight": 0.6, "enabled": True}
                ]
            },
            {
                "id": "char_carol",
                "name": "Carol",
                "enabled": True,
                "prompt": "1girl, glasses, black long hair",
                "negative_prompt": "",
                "loras": []
            }
        ]
    }
    cast_json = json.dumps(test_cast_spec)

    # --------------------------------------------------------------------------
    # 1. 1 Character / 1 Panel compile
    # --------------------------------------------------------------------------
    print("\n--- 1. Testing 1 Character / 1 Panel compile ---")
    spec1 = copy.deepcopy(base_region_spec)
    spec1["regions"][0]["prompt"] = "corridor, walking, sunny morning"
    spec1["regions"][0]["characters"] = [
        {
            "character_id": "char_alice",
            "enabled": True,
            "prompt_override": "walking, looking forward",
            "area": {"x": 0.2, "y": 0.1, "w": 0.5, "h": 0.8}
        }
    ]

    plan, plan_json, prompt, char_count = compiler.compile_panel(
        region_spec=spec1,
        target_panel_id=1,
        cast_spec=cast_json
    )

    assert plan["version"] == 1
    assert plan["status"] == "active"
    assert char_count == 1
    assert len(plan["characters"]) == 1
    c_alice = plan["characters"][0]
    assert c_alice["character_id"] == "char_alice"
    assert "blonde twin tails" in c_alice["combined_prompt"]
    assert "looking forward" in c_alice["combined_prompt"]
    assert c_alice["area"]["x"] == 0.2
    assert "corridor" in prompt and "blonde twin tails" in prompt
    print("1 Character / 1 Panel compile: PASSED")

    # --------------------------------------------------------------------------
    # 2. 2 Characters / 1 Panel compile (2人会話シーン)
    # --------------------------------------------------------------------------
    print("\n--- 2. Testing 2 Characters / 1 Panel compile (Dialogue Scene) ---")
    spec2 = copy.deepcopy(base_region_spec)
    spec2["regions"][0]["prompt"] = "classroom, two people talking, medium shot"
    spec2["regions"][0]["characters"] = [
        {
            "character_id": "char_alice",
            "enabled": True,
            "prompt_override": "annoyed, looking at Bob",
            "area": {"x": 0.05, "y": 0.15, "w": 0.40, "h": 0.75}
        },
        {
            "character_id": "char_bob",
            "enabled": True,
            "prompt_override": "laughing, looking at Alice",
            "area": {"x": 0.55, "y": 0.15, "w": 0.40, "h": 0.75}
        }
    ]

    plan2, _, prompt2, char_count2 = compiler.compile_panel(
        region_spec=spec2,
        target_panel_id=1,
        cast_spec=cast_json
    )

    assert char_count2 == 2
    assert len(plan2["characters"]) == 2
    assert plan2["characters"][0]["character_id"] == "char_alice"
    assert plan2["characters"][0]["override_prompt"] == "annoyed, looking at Bob"
    assert plan2["characters"][1]["character_id"] == "char_bob"
    assert plan2["characters"][1]["override_prompt"] == "laughing, looking at Alice"

    # 各キャラクターのareaが互いに独立していること
    assert plan2["characters"][0]["area"]["x"] == 0.05
    assert plan2["characters"][1]["area"]["x"] == 0.55

    # compiled_prompt に2人の情報が分離統合されていること
    assert "annoyed, looking at Bob" in prompt2
    assert "laughing, looking at Alice" in prompt2
    print("2 Characters / 1 Panel compile: PASSED")

    # --------------------------------------------------------------------------
    # 3. Panelごとの出演差分テスト (KOMA 1 vs KOMA 2 vs KOMA 3)
    # --------------------------------------------------------------------------
    print("\n--- 3. Testing Appearance differences across panels ---")
    spec3 = copy.deepcopy(base_region_spec)
    # KOMA 1: Alice + Bob
    spec3["regions"][0]["characters"] = [
        {"character_id": "char_alice", "enabled": True},
        {"character_id": "char_bob", "enabled": True}
    ]
    # KOMA 2: Alice only
    spec3["regions"][1]["characters"] = [
        {"character_id": "char_alice", "enabled": True, "prompt_override": "close-up face"}
    ]
    # KOMA 3: Bob + Carol
    spec3["regions"][2]["characters"] = [
        {"character_id": "char_bob", "enabled": True},
        {"character_id": "char_carol", "enabled": True}
    ]

    p1, _, _, c1 = compiler.compile_panel(spec3, target_panel_id=1, cast_spec=cast_json)
    p2, _, _, c2 = compiler.compile_panel(spec3, target_panel_id=2, cast_spec=cast_json)
    p3, _, _, c3 = compiler.compile_panel(spec3, target_panel_id=3, cast_spec=cast_json)

    assert c1 == 2 and {c["character_id"] for c in p1["characters"]} == {"char_alice", "char_bob"}
    assert c2 == 1 and {c["character_id"] for c in p2["characters"]} == {"char_alice"}
    assert c3 == 2 and {c["character_id"] for c in p3["characters"]} == {"char_bob", "char_carol"}
    print("Appearance differences across panels: PASSED")

    # --------------------------------------------------------------------------
    # 4. Character area: area=None (ブレスト性維持) の検証
    # --------------------------------------------------------------------------
    print("\n--- 4. Testing Character area=None (AI Creative Freedom) ---")
    spec4 = copy.deepcopy(base_region_spec)
    spec4["regions"][0]["characters"] = [
        {"character_id": "char_alice", "enabled": True, "area": None}
    ]
    plan4, _, _, _ = compiler.compile_panel(spec4, target_panel_id=1, cast_spec=cast_json)
    assert plan4["characters"][0]["area"] is None, "area must be None when unconstrained"
    print("area=None preservation: PASSED")

    # --------------------------------------------------------------------------
    # 5. Global LoRA / KOMA LoRA / Character LoRA 階層集約テスト
    # --------------------------------------------------------------------------
    print("\n--- 5. Testing LoRA Plan hierarchy aggregation ---")
    spec5 = copy.deepcopy(base_region_spec)
    # KOMA 1 に KOMA LoRA (タグおよび明示フィールド)
    spec5["regions"][0]["prompt"] = "rooftop sunset <lora:dramatic_angle:0.35>"
    spec5["regions"][0]["loras"] = [{"name": "lighting_lora", "weight": 0.25, "enabled": True}]
    spec5["regions"][0]["characters"] = [
        {"character_id": "char_alice", "enabled": True}  # Alice possesses alice_v1 0.8
    ]

    global_lora_input = "<lora:shinkai_style:0.5> <lora:clean_lineart:0.2>"

    plan5, _, clean_prompt5, _ = compiler.compile_panel(
        region_spec=spec5,
        target_panel_id=1,
        cast_spec=cast_json,
        global_loras=global_lora_input
    )

    lora_plan = plan5["lora_plan"]
    # Global LoRAs
    g_names = {l["name"]: l["weight"] for l in lora_plan["global_loras"]}
    assert g_names["shinkai_style"] == 0.5
    assert g_names["clean_lineart"] == 0.2

    # KOMA LoRAs
    k_names = {l["name"]: l["weight"] for l in lora_plan["koma_loras"]}
    assert k_names["dramatic_angle"] == 0.35
    assert k_names["lighting_lora"] == 0.25

    # Character LoRAs
    c_names = {l["name"]: l["weight"] for l in lora_plan["character_loras"]}
    assert c_names["alice_v1"] == 0.8
    assert lora_plan["character_loras"][0]["character_name"] == "Alice"

    # clean prompt からは <lora:...> が除去されていること
    assert "<lora:" not in clean_prompt5
    print("LoRA Plan hierarchy aggregation: PASSED")

    # --------------------------------------------------------------------------
    # 6. 未登録 Character ID 参照時の ValueError 検知
    # --------------------------------------------------------------------------
    print("\n--- 6. Testing Unknown character_id error detection ---")
    spec6 = copy.deepcopy(base_region_spec)
    spec6["regions"][0]["characters"] = [
        {"character_id": "char_unknown_ghost", "enabled": True}
    ]
    try:
        compiler.compile_panel(spec6, target_panel_id=1, cast_spec=cast_json)
        assert False, "Compiler must raise ValueError when referencing non-existent character_id!"
    except ValueError as e:
        assert "not found in cast_spec" in str(e).lower()
        print(f"Unknown character_id detected and rejected: {e}")
    print("Unknown character_id validation: PASSED")

    # --------------------------------------------------------------------------
    # 7. CAST_SPEC なし互換モード (CAST_SPEC absent compatibility)
    # --------------------------------------------------------------------------
    print("\n--- 7. Testing CAST_SPEC Absent Compatibility Mode ---")
    spec7 = copy.deepcopy(base_region_spec)
    spec7["regions"][0]["prompt"] = "landscape only, mountains and blue sky"

    plan7, plan_json7, prompt7, char_count7 = compiler.compile_panel(
        region_spec=spec7,
        target_panel_id=1,
        cast_spec="{}"  # 空または未指定
    )
    assert plan7["status"] == "active"
    assert char_count7 == 0
    assert plan7["characters"] == []
    assert "mountains and blue sky" in prompt7
    print("CAST_SPEC Absent Compatibility: PASSED")

    print("\n================================================================================")
    print("[SUCCESS] ALL 7 SCENE COMPILER TEST SUITES PASSED PERFECTLY!")
    print("================================================================================")
    return 0

if __name__ == "__main__":
    sys.exit(run_scene_compiler_tests())
