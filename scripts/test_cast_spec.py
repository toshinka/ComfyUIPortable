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
    assert v_cast["characters"][0]["loras"][0]["model_weight"] == 0.85
    assert v_cast["characters"][0]["loras"][0]["clip_weight"] == 0.85
    assert "weight" not in v_cast["characters"][0]["loras"][0], "legacy 'weight' must be removed from canonical output"
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

    # 9. Phase 3A.1: Character ID strict string (No numeric or bool)
    print("\n--- 9. Testing Character ID strict string validation ---")
    num_id_spec = {
        "version": 1,
        "characters": [{"id": 12345, "name": "Numeric Alice", "enabled": True, "prompt": "1girl"}]
    }
    try:
        validate_cast_spec(num_id_spec)
        assert False, "Should reject numeric character_id"
    except ValueError as e:
        assert "must be a string" in str(e).lower()
        print(f"Numeric character_id rejected successfully: {e}")
    print("Character ID strict string validation: PASSED")

    # 10. Phase 3A.1: Prompt strict string (No numeric or bool)
    print("\n--- 10. Testing Prompt strict string validation ---")
    num_prompt_spec = {
        "version": 1,
        "characters": [{"id": "char_001", "name": "Alice", "enabled": True, "prompt": 9999}]
    }
    try:
        validate_cast_spec(num_prompt_spec)
        assert False, "Should reject numeric prompt"
    except ValueError as e:
        assert "must be a string" in str(e).lower()
        print(f"Numeric prompt rejected successfully: {e}")
    print("Prompt strict string validation: PASSED")

    # 11. Phase 3A.1: LoRA weight bool reject
    print("\n--- 11. Testing LoRA weight bool rejection ---")
    bool_weight_spec = {
        "version": 1,
        "characters": [{
            "id": "char_001",
            "name": "Alice",
            "enabled": True,
            "prompt": "1girl",
            "loras": [{"name": "alice_lora", "weight": True, "enabled": True}]
        }]
    }
    try:
        validate_cast_spec(bool_weight_spec)
        assert False, "Should reject boolean weight in LoRA"
    except ValueError as e:
        assert "strict numeric" in str(e).lower()
        print(f"Boolean LoRA weight rejected successfully: {e}")
    print("LoRA weight bool rejection: PASSED")

    # 12. Phase 3A.1: Legacy weight to canonical model_weight/clip_weight
    print("\n--- 12. Testing legacy weight to Canonical LoRA Entry normalization ---")
    legacy_lora_spec = {
        "version": 1,
        "characters": [{
            "id": "char_001",
            "name": "Alice",
            "enabled": True,
            "prompt": "1girl",
            "loras": [{"name": "legacy_lora", "weight": 0.75, "enabled": True}]
        }]
    }
    v_legacy = validate_cast_spec(legacy_lora_spec)
    c_lora = v_legacy["characters"][0]["loras"][0]
    assert c_lora["model_weight"] == 0.75, f"Expected 0.75, got {c_lora['model_weight']}"
    assert c_lora["clip_weight"] == 0.75, f"Expected 0.75, got {c_lora['clip_weight']}"
    print("Legacy weight normalization: PASSED")

    # 13. Phase 3A.1: Conflicting LoRA weights rejection
    print("\n--- 13. Testing conflicting LoRA weights rejection ---")
    conflict_spec = {
        "version": 1,
        "characters": [{
            "id": "char_001",
            "name": "Alice",
            "enabled": True,
            "prompt": "1girl",
            "loras": [{"name": "conflict_lora", "weight": 0.8, "model_weight": 0.5, "enabled": True}]
        }]
    }
    try:
        validate_cast_spec(conflict_spec)
        assert False, "Should reject conflicting weight vs model_weight"
    except ValueError as e:
        assert "conflicting weight" in str(e).lower()
        print(f"Conflicting weights rejected successfully: {e}")
    print("Conflicting LoRA weights rejection: PASSED")

    # 14. Phase 3A.1: Invalid characters type (dict or str instead of list)
    print("\n--- 14. Testing invalid characters type rejection ---")
    bad_chars_spec = {
        "version": 1,
        "characters": {"char_001": {"name": "Alice"}}  # dict instead of list
    }
    try:
        validate_cast_spec(bad_chars_spec)
        assert False, "Should reject dict for 'characters'"
    except ValueError as e:
        assert "must be a list" in str(e).lower()
        print(f"Dict 'characters' rejected successfully: {e}")
    print("Invalid characters type rejection: PASSED")

    # 15. Phase 3A.1: Binding Negative Prompt Override
    print("\n--- 15. Testing Binding negative_prompt_override ---")
    b_neg = {
        "character_id": "char_001",
        "enabled": True,
        "prompt_override": "smiling",
        "negative_prompt_override": "crying, frown"
    }
    vb_neg = validate_character_binding(b_neg, available_ids)
    assert vb_neg["negative_prompt_override"] == "crying, frown"
    print("Binding negative_prompt_override: PASSED")

    # 16. Phase 3B-0: NaN / +Inf / -Inf LoRA weight rejection (指示書第3.3項)
    print("\n--- 16. Testing NaN / Infinity LoRA weight rejection ---")
    import math
    for bad_val, desc in [(float("nan"), "NaN"), (float("inf"), "+Infinity"), (float("-inf"), "-Infinity")]:
        nan_spec = {
            "version": 1,
            "characters": [{
                "id": "char_001",
                "name": "Alice",
                "enabled": True,
                "prompt": "1girl",
                "loras": [{"name": "nan_lora", "model_weight": bad_val, "enabled": True}]
            }]
        }
        try:
            validate_cast_spec(nan_spec)
            assert False, f"Should reject {desc} in LoRA weight"
        except ValueError as e:
            assert "finite" in str(e).lower()
            print(f"{desc} weight rejected successfully: {e}")
    print("NaN / Infinity LoRA weight rejection: PASSED")

    # 17. Phase 3B-0: Legacy 'weight' key completely removed from Canonical output (指示書第3.2項)
    print("\n--- 17. Testing legacy 'weight' removal from Canonical LoRA Entry ---")
    legacy_input = {
        "name": "test_legacy",
        "weight": 0.9,
        "enabled": True
    }
    from custom_nodes.tegaki_manga_nodes.scene_spec import validate_lora_entry
    canonical_entry = validate_lora_entry(legacy_input)
    assert "weight" not in canonical_entry, "Legacy 'weight' key must be purged from Canonical output"
    assert canonical_entry["model_weight"] == 0.9
    assert canonical_entry["clip_weight"] == 0.9
    print("Legacy weight key removal: PASSED")

    print("\n================================================================================")
    print("[SUCCESS] ALL 17 CAST_SPEC & BINDING TEST SUITES PASSED PERFECTLY!")
    print("================================================================================")
    return 0

if __name__ == "__main__":
    sys.exit(run_cast_spec_tests())
