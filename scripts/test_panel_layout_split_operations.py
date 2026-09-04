import os
import sys
import json
import copy

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CUSTOM_NODES_DIR = os.path.join(ROOT_DIR, "ComfyUI", "custom_nodes")
if CUSTOM_NODES_DIR not in sys.path:
    sys.path.insert(0, CUSTOM_NODES_DIR)
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from custom_nodes.tegaki_manga_nodes.panel_layout_spec import (
    get_default_panel_layout_spec,
    validate_panel_layout_spec
)
from custom_nodes.tegaki_manga_nodes.panel_layout_split import generic_split_panel


def test_split_matrix():
    print("\n--- 1. Testing Split Matrix: 1_full -> H, V, Diag /, Diag \\ ---")
    spec_base = get_default_panel_layout_spec(832, 1216, preset="1_full")

    # 1_full -> H
    spec_h = generic_split_panel(spec_base, "p1", split_mode="horizontal", split_ratio=0.5)
    assert len(spec_h["panels"]) == 2
    print("  1_full -> Horizontal: PASSED (2 panels)")

    # 1_full -> V
    spec_v = generic_split_panel(spec_base, "p1", split_mode="vertical", split_ratio=0.5)
    assert len(spec_v["panels"]) == 2
    print("  1_full -> Vertical: PASSED (2 panels)")

    # 1_full -> Diag /
    spec_d1 = generic_split_panel(spec_base, "p1", split_mode="diag_slash")
    assert len(spec_d1["panels"]) == 2
    print("  1_full -> Diagonal /: PASSED (2 panels)")

    # 1_full -> Diag \
    spec_d2 = generic_split_panel(spec_base, "p1", split_mode="diag_backslash")
    assert len(spec_d2["panels"]) == 2
    print("  1_full -> Diagonal \\: PASSED (2 panels)")


def test_3_basic_and_dynamic_splits():
    print("\n--- 2. Testing 3_basic & 3_dynamic Slanted Panel Splits (All 4 Modes) ---")
    # 3_basic p1 (5-vertex panel) -> H, V, Diag
    spec_3b = get_default_panel_layout_spec(832, 1216, preset="3_basic")
    self_p1_vlen = len(spec_3b["panels"][0]["vertex_ids"])
    assert self_p1_vlen == 5, f"p1 must be a 5-vertex panel, got {self_p1_vlen}"

    spec_3b_h = generic_split_panel(copy.deepcopy(spec_3b), "p1", split_mode="horizontal", split_ratio=0.5)
    assert len(spec_3b_h["panels"]) == 4
    print("  3_basic 5-vertex p1 -> Horizontal: PASSED (4 panels)")

    spec_3b_v = generic_split_panel(copy.deepcopy(spec_3b), "p1", split_mode="vertical", split_ratio=0.5)
    assert len(spec_3b_v["panels"]) == 4
    print("  3_basic 5-vertex p1 -> Vertical: PASSED (4 panels)")

    # 3_dynamic slanted panel p1 -> All 4 modes (H, V, Diag /, Diag \)
    for mode in ("horizontal", "vertical", "diag_slash", "diag_backslash"):
        spec_3d = get_default_panel_layout_spec(832, 1216, preset="3_dynamic")
        spec_3d_split = generic_split_panel(spec_3d, "p1", split_mode=mode)
        assert len(spec_3d_split["panels"]) == 4
        print(f"  3_dynamic slanted p1 -> {mode}: PASSED (4 panels)")

    # 共有頂点変形後の分割 (Deformation -> Split)
    spec_def = get_default_panel_layout_spec(832, 1216, preset="3_basic")
    v5 = next(v for v in spec_def["vertices"] if v["id"] == "v5")
    v5["x"] = 0.40
    v5["y"] = 0.50
    spec_def_h = generic_split_panel(spec_def, "p1", split_mode="horizontal")
    assert len(spec_def_h["panels"]) == 4
    print("  Deformed shared vertex panel -> Horizontal: PASSED (4 panels)")


def test_repeat_splits_up_to_limit():
    print("\n--- 3. Testing Sequential Splits up to Max Capacity (6 panels) & Refuse 7th ---")
    spec = get_default_panel_layout_spec(832, 1216, preset="3_basic")
    assert len(spec["panels"]) == 3

    # Split 3 -> 4
    spec = generic_split_panel(spec, "p1", split_mode="horizontal", split_ratio=0.5)
    assert len(spec["panels"]) == 4
    print("  Split 3 -> 4 panels: PASSED")

    # Split 4 -> 5
    spec = generic_split_panel(spec, "p2", split_mode="vertical", split_ratio=0.5)
    assert len(spec["panels"]) == 5
    print("  Split 4 -> 5 panels: PASSED")

    # Split 5 -> 6
    spec = generic_split_panel(spec, "p3", split_mode="vertical", split_ratio=0.5)
    assert len(spec["panels"]) == 6
    print("  Split 5 -> 6 panels: PASSED")

    # Split 6 -> 7 (Must refuse)
    try:
        generic_split_panel(spec, "p1", split_mode="horizontal", split_ratio=0.5)
        assert False, "Should raise ValueError when exceeding max 6 panels"
    except ValueError as e:
        assert "capacity limit reached" in str(e)
    print("  7th split refused gracefully (Max 6 limit enforced): PASSED")


def run_all():
    print("================================================================================")
    print("Running Panel Layout Generic Split Regression Matrix (Phase 3C.1.1)")
    print("================================================================================")
    test_split_matrix()
    test_3_basic_and_dynamic_splits()
    test_repeat_splits_up_to_limit()
    print("\n================================================================================")
    print("[SUCCESS] ALL GENERIC SPLIT REGRESSION TESTS PASSED!")
    print("================================================================================")
    return 0


if __name__ == "__main__":
    sys.exit(run_all())
