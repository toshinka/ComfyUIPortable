import sys
import os
import json
import copy
import torch

comfy_dir = os.path.abspath("ComfyUI")
sys.path.insert(0, comfy_dir)

from custom_nodes.tegaki_manga_nodes.region_editor import (
    TegakiMangaRegionEditor,
    default_region_spec,
    validate_region_spec,
    normalize_region_spec,
    is_active_region,
    KOMA_COLORS,
    SUPPORTED_SCHEMA_VERSION
)

DEFAULT_LAYOUTS = [
    {"id": 1, "x": 0.06, "y": 0.05, "w": 0.88, "h": 0.28, "prompt": ""},
    {"id": 2, "x": 0.06, "y": 0.36, "w": 0.42, "h": 0.58, "prompt": ""},
    {"id": 3, "x": 0.52, "y": 0.36, "w": 0.42, "h": 0.58, "prompt": ""},
    {"id": 4, "x": 0.06, "y": 0.05, "w": 0.88, "h": 0.20, "prompt": ""},
    {"id": 5, "x": 0.06, "y": 0.28, "w": 0.88, "h": 0.20, "prompt": ""},
    {"id": 6, "x": 0.06, "y": 0.51, "w": 0.88, "h": 0.43, "prompt": ""},
]

def simulate_split_h(spec, target_id, undo_stack):
    """Frontendの splitSelectedRegion('H') のロジックを忠実に再現"""
    target = next((r for r in spec["regions"] if r["id"] == target_id), None)
    if not target or not target["enabled"]:
        return False

    # 1. 現在の panel_count 範囲内の無効コマを優先探索
    unused = next((r for r in spec["regions"] if r["id"] <= spec["panel_count"] and not r["enabled"] and r["id"] != target_id), None)
    need_increase = False

    # 2. 範囲内にない場合、panel_count < 6 であれば拡張
    if not unused and spec["panel_count"] < 6:
        unused = next((r for r in spec["regions"] if r["id"] == spec["panel_count"] + 1), None)
        need_increase = True

    if not unused:
        return False

    # 変更直前に snapshot
    undo_stack.append(copy.deepcopy(spec))

    if need_increase:
        spec["panel_count"] += 1
    unused["enabled"] = True

    half_w = target["w"] / 2
    unused["x"] = round(target["x"] + half_w, 4)
    unused["y"] = target["y"]
    unused["w"] = round(half_w, 4)
    unused["h"] = target["h"]
    target["w"] = round(half_w, 4)

    return True

def simulate_create_region(spec, mx, my, undo_stack):
    """Frontendの canvas.onmousedown (新規Region作成) のロジックを再現"""
    target_koma = next((r for r in spec["regions"] if r["id"] <= spec["panel_count"] and not r["enabled"]), None)
    need_increase = False
    if not target_koma and spec["panel_count"] < 6:
        target_koma = next((r for r in spec["regions"] if r["id"] == spec["panel_count"] + 1), None)
        need_increase = True

    if not target_koma:
        return False

    # 変更直前に snapshot
    undo_stack.append(copy.deepcopy(spec))

    if need_increase:
        spec["panel_count"] += 1
    target_koma["enabled"] = True
    target_koma["x"] = round(mx, 4)
    target_koma["y"] = round(my, 4)
    target_koma["w"] = 0.2
    target_koma["h"] = 0.2
    return True

def simulate_layout_reset(spec, undo_stack):
    """Frontendの resetLayout() のロジックを再現 (geometryのみリセット)"""
    undo_stack.append(copy.deepcopy(spec))
    for i in range(6):
        layout = DEFAULT_LAYOUTS[i]
        r = spec["regions"][i]
        r["x"] = layout["x"]
        r["y"] = layout["y"]
        r["w"] = layout["w"]
        r["h"] = layout["h"]
        # r["enabled"] や r["prompt"] は変更しない

def simulate_generic_swap(spec, id1, id2, undo_stack):
    """Frontendの swapSelectedRegions() の Generic Payload 交換ロジックを再現"""
    r1 = next((r for r in spec["regions"] if r["id"] == id1), None)
    r2 = next((r for r in spec["regions"] if r["id"] == id2), None)
    if not r1 or not r2:
        return False

    undo_stack.append(copy.deepcopy(spec))

    identity_keys = {"id", "name", "color"}
    all_keys = set(r1.keys()).union(r2.keys())

    for key in all_keys:
        if key in identity_keys:
            continue
        v1 = r1.get(key)
        v2 = r2.get(key)
        if v2 is not None:
            r1[key] = copy.deepcopy(v2)
        elif key in r1:
            del r1[key]

        if v1 is not None:
            r2[key] = copy.deepcopy(v1)
        elif key in r2:
            del r2[key]
    return True


def run_state_transition_tests():
    print("================================================================================")
    print("Phase 2.1.1 State Transitions & Regression Tests")
    print("================================================================================")

    # --------------------------------------------------------------------------
    # 1. Split 3 -> 4 panel
    # --------------------------------------------------------------------------
    print("\n--- 1. Testing Split 3 -> 4 Panel & Active Region State ---")
    spec = default_region_spec(panel_count=3)
    undo_stack = []
    redo_stack = []

    orig_koma1_w = spec["regions"][0]["w"]
    success = simulate_split_h(spec, target_id=1, undo_stack=undo_stack)
    assert success is True, "Split should succeed"
    assert spec["panel_count"] == 4, f"Expected panel_count=4, got {spec['panel_count']}"
    assert spec["regions"][3]["id"] == 4 and spec["regions"][3]["enabled"] is True, "KOMA 4 must be enabled"
    assert is_active_region(spec["regions"][3], spec["panel_count"]) is True, "KOMA 4 must be active region"
    assert spec["regions"][0]["w"] == round(orig_koma1_w / 2, 4), "KOMA 1 width must be halved"
    print("Split 3 -> 4: PASSED")

    # --------------------------------------------------------------------------
    # 2. Split Undo 4 -> 3 & Redo 3 -> 4
    # --------------------------------------------------------------------------
    print("\n--- 2. Testing Split Undo 4 -> 3 & Redo 3 -> 4 ---")
    assert len(undo_stack) == 1, "Undo stack should have 1 item"
    # Undo
    redo_stack.append(copy.deepcopy(spec))
    spec = undo_stack.pop()

    assert spec["panel_count"] == 3, f"Undo must restore panel_count=3, got {spec['panel_count']}"
    assert spec["regions"][3]["enabled"] is False, "KOMA 4 must be restored to disabled"
    assert spec["regions"][0]["w"] == orig_koma1_w, f"KOMA 1 geometry must be restored to {orig_koma1_w}"
    print("Split Undo: PASSED")

    # Redo
    undo_stack.append(copy.deepcopy(spec))
    spec = redo_stack.pop()
    assert spec["panel_count"] == 4 and spec["regions"][3]["enabled"] is True, "Redo must restore split state"
    print("Split Redo: PASSED")

    # --------------------------------------------------------------------------
    # 3. Create 3 -> 4 panel & Undo 4 -> 3
    # --------------------------------------------------------------------------
    print("\n--- 3. Testing Create 3 -> 4 Panel & Undo 4 -> 3 ---")
    spec = default_region_spec(panel_count=3)
    undo_stack = []
    success = simulate_create_region(spec, 0.2, 0.2, undo_stack)
    assert success is True, "Create region should succeed"
    assert spec["panel_count"] == 4, f"panel_count must become 4, got {spec['panel_count']}"
    assert spec["regions"][3]["enabled"] is True, "KOMA 4 must be enabled"
    assert spec["regions"][3]["x"] == 0.2 and spec["regions"][3]["y"] == 0.2

    # Undo
    spec = undo_stack.pop()
    assert spec["panel_count"] == 3, f"Undo must restore panel_count=3, got {spec['panel_count']}"
    assert spec["regions"][3]["enabled"] is False, "KOMA 4 must be restored to disabled"
    assert spec["regions"][3]["x"] == DEFAULT_LAYOUTS[3]["x"], "KOMA 4 coordinates must revert to initial"
    print("Create & Undo: PASSED")

    # --------------------------------------------------------------------------
    # 4. Delete -> Layout Reset preserves enabled & prompt
    # --------------------------------------------------------------------------
    print("\n--- 4. Testing Delete -> Layout Reset preserves enabled & prompt ---")
    spec = default_region_spec(panel_count=3)
    undo_stack = []

    # KOMA 2 を無効化、カスタム座標、カスタムプロンプト
    spec["regions"][1]["enabled"] = False
    spec["regions"][1]["prompt"] = "hero character in rain"
    spec["regions"][1]["x"] = 0.33
    spec["regions"][1]["w"] = 0.60

    # Layout Reset を実行
    simulate_layout_reset(spec, undo_stack)

    # ジオメトリは DEFAULT_LAYOUTS[1] にリセット
    assert spec["regions"][1]["x"] == DEFAULT_LAYOUTS[1]["x"], "x must reset to default"
    assert spec["regions"][1]["w"] == DEFAULT_LAYOUTS[1]["w"], "w must reset to default"
    # enabled と prompt は絶対に変更されないこと！
    assert spec["regions"][1]["enabled"] is False, "Layout Reset must NOT enable disabled regions!"
    assert spec["regions"][1]["prompt"] == "hero character in rain", "Layout Reset must NOT erase prompt!"
    print("Layout Reset preserves state: PASSED")

    # --------------------------------------------------------------------------
    # 5. Generic Swap with unknown metadata
    # --------------------------------------------------------------------------
    print("\n--- 5. Testing Generic Swap with unknown metadata ---")
    spec = default_region_spec(panel_count=3)
    undo_stack = []

    # KOMA 1 に未知メタデータ付与
    spec["regions"][0]["prompt"] = "Alice in Wonderland"
    spec["regions"][0]["control_strength"] = 0.85
    spec["regions"][0]["lora_tag"] = "<lora:alice:0.75>"
    spec["regions"][0]["char_id"] = "CHAR_ALICE"

    # KOMA 2 に別メタデータ付与
    spec["regions"][1]["prompt"] = "Bob the Builder"
    spec["regions"][1]["control_strength"] = 0.25
    spec["regions"][1]["lora_tag"] = "<lora:bob:0.5>"
    spec["regions"][1]["char_id"] = "CHAR_BOB"

    success = simulate_generic_swap(spec, id1=1, id2=2, undo_stack=undo_stack)
    assert success is True, "Swap should succeed"

    r1 = spec["regions"][0]
    r2 = spec["regions"][1]

    # KOMA Identity (id, name, color) は不変
    assert r1["id"] == 1 and r1["name"] == "KOMA 1" and r1["color"] == KOMA_COLORS[0]["hex"]
    assert r2["id"] == 2 and r2["name"] == "KOMA 2" and r2["color"] == KOMA_COLORS[1]["hex"]

    # Payload と 未知フィールドが完全に交換されていること
    assert r1["prompt"] == "Bob the Builder", f"KOMA 1 prompt got {r1['prompt']}"
    assert r1["control_strength"] == 0.25, f"KOMA 1 control_strength got {r1.get('control_strength')}"
    assert r1["lora_tag"] == "<lora:bob:0.5>", f"KOMA 1 lora_tag got {r1.get('lora_tag')}"
    assert r1["char_id"] == "CHAR_BOB", f"KOMA 1 char_id got {r1.get('char_id')}"

    assert r2["prompt"] == "Alice in Wonderland"
    assert r2["control_strength"] == 0.85
    assert r2["lora_tag"] == "<lora:alice:0.75>"
    assert r2["char_id"] == "CHAR_ALICE"
    print("Generic Swap unknown metadata: PASSED")

    # --------------------------------------------------------------------------
    # 6. execute_editor unsupported schema error propagation
    # --------------------------------------------------------------------------
    print("\n--- 6. Testing execute_editor Unsupported Schema Error propagation ---")
    editor = TegakiMangaRegionEditor()
    bad_version_spec = default_region_spec(panel_count=3)
    bad_version_spec["version"] = 999
    bad_version_json = json.dumps(bad_version_spec)

    try:
        editor.execute_editor(
            panel_count=3,
            canvas_width=832,
            canvas_height=1216,
            global_prompt="test",
            region_spec_data=bad_version_json
        )
        assert False, "execute_editor must raise ValueError for unsupported schema version 999!"
    except ValueError as e:
        assert "unsupported" in str(e).lower(), f"Expected unsupported version error, got: {e}"
        print(f"Unsupported schema error propagated successfully: {e}")
    print("Schema error propagation: PASSED")

    # 構文エラー (Syntax error) は default spec へ fallback することを再確認
    print("\n--- 6b. Testing Syntax Error fallback to default ---")
    _, out_json, _, _, _, _ = editor.execute_editor(
        panel_count=3,
        canvas_width=832,
        canvas_height=1216,
        global_prompt="test",
        region_spec_data="{broken json syntax..."
    )
    fallback_parsed = json.loads(out_json)
    assert fallback_parsed["version"] == SUPPORTED_SCHEMA_VERSION, "Syntax error must fallback to default"
    print("Syntax error fallback: PASSED")

    # --------------------------------------------------------------------------
    # 7. enabled strict boolean type validation
    # --------------------------------------------------------------------------
    print("\n--- 7. Testing Strict boolean validation on 'enabled' ---")
    spec_str_false = default_region_spec(panel_count=3)
    spec_str_false["regions"][0]["enabled"] = "false"  # 文字列 "false"

    try:
        validate_region_spec(spec_str_false)
        assert False, "validate_region_spec must reject 'enabled': 'false' string!"
    except ValueError as e:
        assert "strict boolean" in str(e).lower(), f"Expected strict boolean error, got: {e}"
        print(f"String 'false' rejected successfully: {e}")

    # 整数 1 / 0 も reject されるか検証
    spec_int = default_region_spec(panel_count=3)
    spec_int["regions"][0]["enabled"] = 1
    try:
        # Python では isinstance(True, int) は True だが isinstance(1, bool) は False
        validate_region_spec(spec_int)
        assert False, "validate_region_spec must reject 'enabled': 1 int!"
    except ValueError as e:
        assert "strict boolean" in str(e).lower()
        print(f"Integer 1 rejected successfully: {e}")

    # is_active_region で非booleanが渡された場合のガード
    assert is_active_region({"id": 1, "enabled": "false"}, 3) is False
    assert is_active_region({"id": 1, "enabled": 1}, 3) is False
    assert is_active_region({"id": 1, "enabled": True}, 3) is True
    print("Strict boolean validation: PASSED")

    print("\n================================================================================")
    print("[SUCCESS] ALL PHASE 2.1.1 REGRESSION TESTS PASSED PERFECTLY!")
    print("================================================================================")
    return 0

if __name__ == "__main__":
    sys.exit(run_state_transition_tests())
