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
from custom_nodes.tegaki_manga_nodes.panel_layout_topology import validate_layout_topology


def test_valid_shared_vertex_drag():
    print("\n--- 1. Testing Valid Shared Vertex Drag ---")
    spec = get_default_panel_layout_spec(832, 1216, preset="3_basic")
    # v5 は p1, p2, p3 に共有された頂点 (x=0.50, y=0.45)
    v5 = next(v for v in spec["vertices"] if v["id"] == "v5")
    # 安全な範囲で (0.55, 0.50) へ移動
    v5["x"] = 0.55
    v5["y"] = 0.50

    validated = validate_panel_layout_spec(spec)
    assert validated["metadata"]["topology_summary"]["status"] == "VALID"
    print("  Valid shared vertex move: PASSED")


def test_invalid_crossing_move_and_rollback():
    print("\n--- 2. Testing Invalid Crossing Move Rejection & Rollback ---")
    spec = get_default_panel_layout_spec(832, 1216, preset="3_basic")
    last_valid_spec = copy.deepcopy(spec)

    # v5 を大きく左上に動かして p1 や p2 を自己交差させる
    v5 = next(v for v in spec["vertices"] if v["id"] == "v5")
    v5["x"] = 0.01  # frame.x (0.05) を越えて不正領域へ
    v5["y"] = 0.01

    candidate_rejected = False
    try:
        validate_panel_layout_spec(spec)
    except ValueError as e:
        candidate_rejected = True
        # 不正検知によりロールバック
        spec = copy.deepcopy(last_valid_spec)

    assert candidate_rejected, "Invalid crossing move must be rejected"
    # ロールバック後の状態が valid であることを確認
    validated_reverted = validate_panel_layout_spec(spec)
    assert validated_reverted["metadata"]["topology_summary"]["status"] == "VALID"
    print("  Invalid crossing move rejected and rolled back to valid state: PASSED")


def test_degenerate_move_rejection():
    print("\n--- 3. Testing Degenerate Move Rejection (Zero Area) ---")
    spec = get_default_panel_layout_spec(832, 1216, preset="3_basic")
    # v5 を v4(0.05, 0.45) と完全に同じ座標に重ねて p2 を縮退させる
    v5 = next(v for v in spec["vertices"] if v["id"] == "v5")
    v5["x"] = 0.05
    v5["y"] = 0.45

    try:
        validate_panel_layout_spec(spec)
        assert False, "Should raise ValueError on zero-length edge/degenerate area"
    except ValueError as e:
        assert ("Zero-length edge" in str(e) or "smaller than minimum" in str(e) or "T-Junction" in str(e))
    print("  Degenerate move (overlapping vertices) rejected: PASSED")


def test_outer_boundary_constraint():
    print("\n--- 4. Testing Outer Boundary Constraint ---")
    spec = get_default_panel_layout_spec(832, 1216, preset="3_basic")
    # 外周下端の中間頂点 v7(0.50, 0.95) は frame の y=0.95 上に留まりつつスライド可能
    v7 = next(v for v in spec["vertices"] if v["id"] == "v7")
    v7["x"] = 0.55  # 下辺に沿った安全なスライド移動
    v7["y"] = 0.95

    validated = validate_panel_layout_spec(spec)
    assert validated["metadata"]["topology_summary"]["status"] == "VALID"
    print("  Outer boundary middle vertex sliding constraint: PASSED")


def run_all():
    print("================================================================================")
    print("Running Panel Layout Drag Validation & Transaction Tests (Phase 3C.1.1)")
    print("================================================================================")
    test_valid_shared_vertex_drag()
    test_invalid_crossing_move_and_rollback()
    test_degenerate_move_rejection()
    test_outer_boundary_constraint()
    print("\n================================================================================")
    print("[SUCCESS] ALL DRAG VALIDATION & TRANSACTION TESTS PASSED!")
    print("================================================================================")
    return 0


if __name__ == "__main__":
    sys.exit(run_all())
