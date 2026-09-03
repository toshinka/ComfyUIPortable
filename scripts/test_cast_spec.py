import sys
import os
import json
import copy

comfy_dir = os.path.abspath("ComfyUI")
sys.path.insert(0, comfy_dir)

from custom_nodes.tegaki_manga_nodes.scene_spec import (
    validate_cast_spec,
    validate_character_binding,
    default_cast_spec,
    normalize_rect,
    SUPPORTED_CAST_SPEC_VERSION
)

def run_cast_spec_tests():
    print("================================================================================")
    print("CAST_SPEC (v1) and Character Binding Validation Tests")
    print("================================================================================")

    # 1. 正常系: default_cast_spec
    print("\n--- 1. Testing default_cast_spec ---")
    d_spec = default_cast_spec()
    assert d_spec["version"] == SUPPORTED_CAST_SPEC_VERSION
    assert d_spec["characters"] == []
    v_default = validate_cast_spec(d_spec)
    assert v_default["version"] == 1
    print("default_cast_spec: PASSED")

    # 2. 正常系: 複数キャラクターとLoRA設定
    print("\n--- 2. Testing valid multi-character CAST_SPEC ---")
    valid_cast = {
        "version": 1,
        "characters": [
            {
                "id": "char_001",
                "name": "Alice",
                "enabled": True,
                "prompt": "1girl, blonde hair, blue eyes, school uniform",
                "negative_prompt": "bad anatomy",
                "loras": [
                    {"name": "alice_costume", "weight": 0.85, "enabled": True}
                ],
                "metadata": {"role": "protagonist"}
            },
            {
                "id": "char_002",
                "name": "Bob",
                "enabled": False,
                "prompt": "1boy, short brown hair, tall",
                "negative_prompt": "",
                "loras": []
            }
        ]
    }
    v_cast = validate_cast_spec(valid_cast)
    assert len(v_cast["characters"]) == 2
    assert v_cast["characters"][0]["id"] == "char_001"
    assert v_cast["characters"][0]["loras"][0]["weight"] == 0.85
    assert v_cast["characters"][0]["metadata"]["role"] == "protagonist"
    print("Valid multi-character CAST_SPEC: PASSED")

    # 3. 異常系: version != 1
    print("\n--- 3. Testing Unsupported CAST_SPEC version ---")
    bad_ver = copy.deepcopy(valid_cast)
    bad_ver["version"] = 999
    try:
        validate_cast_spec(bad_ver)
        assert False, "Should raise ValueError on version 999"
    except ValueError as e:
        assert "unsupported" in str(e).lower()
        print(f"Unsupported version rejected: {e}")
    print("Unsupported version: PASSED")

    # 4. 異常系: Duplicate character ID
    print("\n--- 4. Testing Duplicate character ID ---")
    dup_id_spec = {
        "version": 1,
        "characters": [
            {"id": "alice", "name": "Alice", "enabled": True, "prompt": "p1"},
            {"id": "alice", "name": "Alice 2", "enabled": True, "prompt": "p2"},
        ]
    }
    try:
        validate_cast_spec(dup_id_spec)
        assert False, "Should raise ValueError on duplicate character id 'alice'"
    except ValueError as e:
        assert "duplicate" in str(e).lower()
        print(f"Duplicate character ID rejected: {e}")
    print("Duplicate character ID: PASSED")

    # 5. 異常系: enabled strict boolean
    print("\n--- 5. Testing strict boolean validation on character 'enabled' ---")
    str_enabled_spec = {
        "version": 1,
        "characters": [
            {"id": "char_001", "name": "Alice", "enabled": "false", "prompt": "p"}
        ]
    }
    try:
        validate_cast_spec(str_enabled_spec)
        assert False, "Should reject 'enabled': 'false' string"
    except ValueError as e:
        assert "strict boolean" in str(e).lower()
        print(f"String 'false' rejected: {e}")
    print("Strict boolean validation: PASSED")

    # 6. 未知フィールド保持 (Forward compatibility)
    print("\n--- 6. Testing unknown fields preservation in character master ---")
    custom_field_spec = copy.deepcopy(valid_cast)
    custom_field_spec["characters"][0]["actor_voice"] = "voice_sample_01.wav"
    custom_field_spec["characters"][0]["loras"][0]["trigger_word"] = "alice_v2"
    v_custom = validate_cast_spec(custom_field_spec)
    assert v_custom["characters"][0]["actor_voice"] == "voice_sample_01.wav"
    assert v_custom["characters"][0]["loras"][0]["trigger_word"] == "alice_v2"
    print("Unknown fields preservation: PASSED")

    # 7. Character Binding: 正常系 (areaあり、area=None)
    print("\n--- 7. Testing Character Binding (with area & area=None) ---")
    available_ids = {"char_001", "char_002"}
    b_with_area = {
        "character_id": "char_001",
        "enabled": True,
        "prompt_override": "smiling",
        "area": {"x": 0.1, "y": 0.2, "w": 0.4, "h": 0.6}
    }
    vb1 = validate_character_binding(b_with_area, available_ids)
    assert vb1["area"]["x"] == 0.1 and vb1["area"]["w"] == 0.4

    b_no_area = {
        "character_id": "char_002",
        "enabled": True,
        "prompt_override": "surprised",
        "area": None
    }
    vb2 = validate_character_binding(b_no_area, available_ids)
    assert vb2["area"] is None, "area=None must be preserved for AI creative freedom"
    print("Character Binding with area & area=None: PASSED")

    # 8. Character Binding: 未登録 Character ID
    print("\n--- 8. Testing Character Binding with non-existent character_id ---")
    b_unknown = {
        "character_id": "char_ghost",
        "enabled": True
    }
    try:
        validate_character_binding(b_unknown, available_ids)
        assert False, "Should raise ValueError for char_ghost not in CAST_SPEC"
    except ValueError as e:
        assert "not found in cast_spec" in str(e).lower()
        print(f"Unknown character_id rejected: {e}")
    print("Non-existent character_id in binding: PASSED")

    print("\n================================================================================")
    print("[SUCCESS] ALL CAST_SPEC & BINDING TEST SUITES PASSED PERFECTLY!")
    print("================================================================================")
    return 0

if __name__ == "__main__":
    sys.exit(run_cast_spec_tests())
