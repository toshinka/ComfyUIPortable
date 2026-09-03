import json
import os
import sys
import math

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CUSTOM_NODES_DIR = os.path.join(ROOT_DIR, "ComfyUI", "custom_nodes")
if CUSTOM_NODES_DIR not in sys.path:
    sys.path.insert(0, CUSTOM_NODES_DIR)
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from custom_nodes.tegaki_manga_nodes.conditioning_builder import TegakiMangaConditioningBuilder

WORKFLOWS_DIR = os.path.join(ROOT_DIR, "workflows")


def migrate_conditioning_builder_widgets_python(wv):
    """
    manga_workflow_migration.js と等価なマイグレーションロジック (Pythonテスト検証用)
    """
    if not isinstance(wv, list):
        return wv

    # 1. Generation 1 (Legacy Phase 3B): [1.0, 1.0, "default"] (長さ 3)
    if len(wv) == 3 and isinstance(wv[0], (int, float)) and isinstance(wv[1], (int, float)) and isinstance(wv[2], str):
        return [float(wv[0]), float(wv[1]), str(wv[2]), 1.0, 0]

    # 2. Generation 2 (Phase 3B.1 initial): [1.0, 1.0, 1.0, "default", 0]
    # (長さ 5 で index 2 が数値, index 3 が文字列)
    if len(wv) >= 5 and isinstance(wv[2], (int, float)) and isinstance(wv[3], str):
        p = float(wv[0])
        c = float(wv[1])
        lr = float(wv[2])
        area = str(wv[3])
        feather = int(wv[4]) if isinstance(wv[4], (int, float)) else 0
        return [p, c, area, lr, feather]

    # 3. Generation 3 (Canonical Phase 3B.1.1): [1.0, 1.0, "default", 1.0, 0]
    # NaN や不正な文字列が紛れ込んでいる場合の安全自動修復
    if len(wv) >= 3:
        try:
            p = float(wv[0])
            if not math.isfinite(p):
                p = 1.0
        except (ValueError, TypeError):
            p = 1.0

        try:
            c = float(wv[1])
            if not math.isfinite(c):
                c = 1.0
        except (ValueError, TypeError):
            c = 1.0

        area = str(wv[2]) if isinstance(wv[2], str) else "default"

        try:
            lr = float(wv[3]) if len(wv) > 3 else 1.0
            if not math.isfinite(lr):
                lr = 1.0
        except (ValueError, TypeError):
            lr = 1.0

        try:
            feather = int(wv[4]) if len(wv) > 4 else 0
            if not math.isfinite(feather):
                feather = 0
        except (ValueError, TypeError):
            feather = 0

        return [p, c, area, lr, feather]

    return wv


def run_widget_compatibility_tests():
    print("================================================================================")
    print("Workflow Widget Compatibility & Migration Tests (Phase 3B.1.1)")
    print("================================================================================")

    # 1. Conditioning Builder Canonical Widget 定義の確認
    print("\n--- 1. Testing TegakiMangaConditioningBuilder INPUT_TYPES ---")
    input_types = TegakiMangaConditioningBuilder.INPUT_TYPES()
    opt_keys = list(input_types.get("optional", {}).keys())
    expected_order = [
        "panel_strength",
        "character_strength",
        "set_cond_area",
        "local_region_strength",
        "mask_feather"
    ]
    assert opt_keys == expected_order, f"Expected widget order {expected_order}, got {opt_keys}"
    print(f"  Canonical Optional Order: {opt_keys} [PASSED]")

    # 2. Fixture 1: Legacy Phase 3B widgets_values ([1.0, 1.0, "default"])
    print("\n--- 2. Testing Fixture: Legacy Phase 3B [1.0, 1.0, 'default'] ---")
    legacy_wv = [1.0, 1.0, "default"]
    migrated_1 = migrate_conditioning_builder_widgets_python(legacy_wv)
    assert migrated_1 == [1.0, 1.0, "default", 1.0, 0]
    print(f"  Legacy Phase 3B {legacy_wv} -> {migrated_1} [PASSED]")

    # 3. Fixture 2: Phase 3B.1 initial widgets_values ([1.0, 1.0, 1.0, "default", 0])
    print("\n--- 3. Testing Fixture: Phase 3B.1 initial [1.0, 1.0, 1.0, 'default', 0] ---")
    init_wv = [1.0, 1.0, 1.0, "default", 0]
    migrated_2 = migrate_conditioning_builder_widgets_python(init_wv)
    assert migrated_2 == [1.0, 1.0, "default", 1.0, 0]
    print(f"  Phase 3B.1 initial {init_wv} -> {migrated_2} [PASSED]")

    # 4. Fixture 3: Corrupted NaN / Invalid string repair
    print("\n--- 4. Testing Fixture: Corrupted NaN / string recovery ---")
    corrupted_wv = [float("nan"), 1.2, "default", "invalid_str", 0]
    migrated_3 = migrate_conditioning_builder_widgets_python(corrupted_wv)
    assert migrated_3[0] == 1.0, "NaN panel_strength should be healed to 1.0"
    assert migrated_3[1] == 1.2, "Valid character_strength should be preserved"
    assert migrated_3[2] == "default"
    assert migrated_3[3] == 1.0, "Invalid string local_region_strength should be healed to 1.0"
    assert migrated_3[4] == 0
    print(f"  Corrupted {corrupted_wv} -> {migrated_3} [PASSED]")

    # 5. 実際の Workflow 08, 09, 10, 11, 12, 13 の保存値の整合性検証
    print("\n--- 5. Testing saved workflows widgets_values matching schema ---")
    workflows_to_check = [
        ("08_MANGA_SCENE_CONTRACT_TEST.json", "TegakiMangaRegionEditor", 5),
        ("09_MANGA_REGIONAL_GENERATION_POC.json", "TegakiMangaConditioningBuilder", 5),
        ("10_MANGA_REGIONAL_CONTROL_EXPANSION_TEST.json", "TegakiMangaConditioningBuilder", 5),
        ("11_TWO_REGION_CORE_COUPLE_ORACLE.json", "TegakiTwoRegionCoreConditioner", 4),
        ("12_TWO_REGION_IMPACT_COUPLE_ORACLE.json", "TegakiTwoRegionImpactAdapter", 3),
        ("13_TWO_REGION_CONTROLNET_LAYOUT_AUX.json", "TegakiTwoRegionLayoutGuide", 2),
        ("14_MANGA_PANEL_LAYOUT_GUIDE_EDITOR_TEST.json", "TegakiMangaPanelLayoutEditor", 4),
        ("15_MANGA_PANEL_LAYOUT_CONTROLNET_FUSION_ORACLE.json", "TegakiMangaPanelLayoutEditor", 4),
    ]

    for wf_name, target_node_type, expected_wv_len in workflows_to_check:
        wf_path = os.path.join(WORKFLOWS_DIR, wf_name)
        with open(wf_path, "r", encoding="utf-8") as f:
            wf = json.load(f)

        found = False
        for n in wf.get("nodes", []):
            if n.get("type") == target_node_type:
                found = True
                wv = n.get("widgets_values", [])
                print(f"  Workflow {wf_name} node '{target_node_type}': widgets_values = {wv}")
                assert len(wv) == expected_wv_len, f"Expected length {expected_wv_len}, got {len(wv)}"
                if target_node_type == "TegakiMangaConditioningBuilder":
                    # [panel, char, area, local, feather]
                    assert isinstance(wv[0], (int, float)) and math.isfinite(wv[0])
                    assert isinstance(wv[1], (int, float)) and math.isfinite(wv[1])
                    assert isinstance(wv[2], str)
                    assert isinstance(wv[3], (int, float)) and math.isfinite(wv[3])
                    assert isinstance(wv[4], int) and math.isfinite(wv[4])
                elif target_node_type == "TegakiTwoRegionCoreConditioner":
                    # [strength_A, strength_B, set_cond_area, mask_feather]
                    assert isinstance(wv[0], (int, float)) and math.isfinite(wv[0])
                    assert isinstance(wv[1], (int, float)) and math.isfinite(wv[1])
                    assert isinstance(wv[2], str)
                    assert isinstance(wv[3], int) and math.isfinite(wv[3])
        assert found, f"Node type {target_node_type} not found in {wf_name}"

    print("\n================================================================================")
    print("[SUCCESS] ALL WIDGET COMPATIBILITY & FIXTURE TESTS PASSED PERFECTLY!")
    print("================================================================================")
    return 0


if __name__ == "__main__":
    sys.exit(run_widget_compatibility_tests())
