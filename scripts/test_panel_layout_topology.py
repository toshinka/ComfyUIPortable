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
from custom_nodes.tegaki_manga_nodes.panel_layout_topology import (
    validate_layout_topology,
    polygon_self_intersects,
    detect_t_junctions,
    build_edge_incidence,
    check_area_conservation,
    diagnose_gaps_and_overlaps
)


import re


def assert_raises(exc_type, fn, *args, match=None, **kwargs):
    try:
        fn(*args, **kwargs)
        raise AssertionError(f"Expected {exc_type.__name__} was not raised.")
    except exc_type as e:
        if match and not re.search(match, str(e)):
            raise AssertionError(f"Expected exception message matching '{match}', got: {e}")
        return e


def test_valid_presets_topology():
    print("\n--- 1. Testing Planar Subdivision Topology on All Presets ---")
    for preset in ("1_full", "3_basic", "3_dynamic", "4_grid"):
        spec = get_default_panel_layout_spec(832, 1216, preset=preset)
        summary = validate_layout_topology(spec)
        assert summary["status"] == "VALID"
        assert summary["gap_ratio"] <= 0.01
        assert summary["overlap_ratio"] <= 0.01
        print(f"  Preset '{preset}': Panels={summary['panel_count']}, Edges={summary['unique_edges_count']}, Gap={summary['gap_ratio']:.1%}, Overlap={summary['overlap_ratio']:.1%} [PASSED]")


def test_self_intersection_bow_tie_rejection():
    print("\n--- 2. Testing Self-Intersecting Polygon (Bow-Tie) Rejection ---")
    spec = get_default_panel_layout_spec(832, 1216, preset="1_full")
    # p1 の頂点順序を自己交差 (bow-tie) に改変: v1 -> v3 -> v2 -> v4
    spec["panels"][0]["vertex_ids"] = ["v1", "v3", "v2", "v4"]
    assert_raises(ValueError, validate_layout_topology, spec, match="Self-intersecting")
    print("  Bow-tie self-intersection rejected: PASSED")


def test_duplicate_vertex_in_cycle_rejection():
    print("\n--- 3. Testing Duplicate Vertex in Panel Cycle Rejection ---")
    spec = get_default_panel_layout_spec(832, 1216, preset="1_full")
    spec["panels"][0]["vertex_ids"] = ["v1", "v4", "v3", "v2", "v1"]
    assert_raises(ValueError, validate_layout_topology, spec, match="Duplicate vertex ID")
    print("  Duplicate vertex in cycle rejected: PASSED")


def test_zero_length_edge_rejection():
    print("\n--- 4. Testing Zero-Length Edge / Duplicate Coordinate Rejection ---")
    spec = get_default_panel_layout_spec(832, 1216, preset="1_full")
    # 同一座標の頂点を追加
    spec["vertices"].append({"id": "v_dup_pos", "x": 0.05, "y": 0.05})
    spec["panels"][0]["vertex_ids"] = ["v1", "v_dup_pos", "v3", "v4"]
    assert_raises(ValueError, validate_layout_topology, spec, match="Zero-length edge|Duplicate vertex coordinates detected")
    print("  Zero-length edge / duplicate coordinates rejected: PASSED")


def test_edge_incidence_overflow_rejection():
    print("\n--- 5. Testing Edge Incidence Overflow (> 2 panels per edge) Rejection ---")
    spec = get_default_panel_layout_spec(832, 1216, preset="3_basic")
    # 3つ目のパネルにも全く同じエッジ (v4, v5) を不当に挿入
    spec["panels"].append({"id": "p_invalid_overlap", "vertex_ids": ["v4", "v5", "v6"]})
    assert_raises(ValueError, validate_layout_topology, spec, match="Max allowed incidence is 2")
    print("  Edge incidence > 2 rejected: PASSED")


def test_t_junction_detection_and_rejection():
    print("\n--- 6. Testing T-Junction Detection & Rejection ---")
    spec = get_default_panel_layout_spec(832, 1216, preset="1_full")
    # p1 の下辺 v4(0.05, 0.95) - v3(0.95, 0.95) の中間に新頂点 vt(0.50, 0.95) を置く
    # しかし p1 の頂点リストには含めず、別のパネル p2 だけが vt を持つ
    spec["vertices"].append({"id": "vt", "x": 0.50, "y": 0.95})
    spec["panels"] = [
        {"id": "p1", "vertex_ids": ["v1", "v4", "v3", "v2"]},
        {"id": "p2", "vertex_ids": ["vt", "v3", "v2"]}
    ]
    assert_raises(ValueError, validate_layout_topology, spec, match="T-Junction detected")
    print("  T-Junction rejected: PASSED")


def test_area_conservation_and_gap_overlap_diagnostics():
    print("\n--- 7. Testing Area Conservation & Gap/Overlap Diagnostics ---")
    spec = get_default_panel_layout_spec(832, 1216, preset="1_full")
    # パネルの座標を縮めて隙間を作る
    spec["vertices"][2]["x"] = 0.80  # 0.95 -> 0.80
    assert_raises(ValueError, validate_layout_topology, spec, match="Area conservation violated|Structural gap detected")
    print("  Area conservation violation / gap rejected: PASSED")


def test_frame_outside_vertex_rejection():
    print("\n--- 8. Testing Frame Outside Vertex Rejection ---")
    spec = get_default_panel_layout_spec(832, 1216, preset="1_full")
    spec["vertices"][0]["x"] = 0.01  # frame.x (0.05) より外側
    assert_raises(ValueError, validate_layout_topology, spec, match="outside the Layout Frame")
    print("  Frame outside vertex rejected: PASSED")


def test_duplicate_coordinate_rejection():
    print("\n--- 9. Testing Duplicate Coordinate Rejection ---")
    spec = get_default_panel_layout_spec(832, 1216, preset="1_full")
    # 別 ID なのに v1(0.05, 0.05) と同じ座標を持つ頂点 v_dup を追加
    spec["vertices"].append({"id": "v_dup", "x": 0.05, "y": 0.05})
    spec["panels"][0]["vertex_ids"].append("v_dup")
    assert_raises(ValueError, validate_layout_topology, spec, match="Duplicate vertex coordinates detected")
    print("  Duplicate vertex coordinates rejected: PASSED")


def test_orphan_vertex_rejection():
    print("\n--- 10. Testing Orphan Vertex Rejection ---")
    spec = get_default_panel_layout_spec(832, 1216, preset="1_full")
    # どのパネルからも参照されていない孤立頂点
    spec["vertices"].append({"id": "v_orphan", "x": 0.50, "y": 0.50})
    assert_raises(ValueError, validate_layout_topology, spec, match="Orphan vertices detected")
    print("  Orphan vertex rejected: PASSED")


def test_internal_edge_gap_incidence_1_rejection():
    print("\n--- 11. Testing Internal Edge Gap (Incidence 1) Rejection ---")
    spec = get_default_panel_layout_spec(832, 1216, preset="3_basic")
    # p2(下左) を削除して内部エッジ (v4-v5, v5-v7) が incidence 1 (穴あき) になるようにする
    spec["panels"] = [spec["panels"][0], spec["panels"][2]]
    # 未参照になった v6 を削除
    spec["vertices"] = [v for v in spec["vertices"] if v["id"] != "v6"]
    assert_raises(ValueError, validate_layout_topology, spec, match="Structural gap detected")
    print("  Internal edge structural gap rejected: PASSED")


def test_exact_pairwise_overlap_rejection():
    print("\n--- 12. Testing Exact Pairwise Polygon Overlap Rejection ---")
    spec = get_default_panel_layout_spec(832, 1216, preset="1_full")
    # p1 の真の内部に入り込む重複パネル p_overlap を追加
    spec["vertices"].extend([
        {"id": "ov1", "x": 0.20, "y": 0.20},
        {"id": "ov2", "x": 0.80, "y": 0.20},
        {"id": "ov3", "x": 0.80, "y": 0.80},
        {"id": "ov4", "x": 0.20, "y": 0.80},
    ])
    spec["panels"].append({"id": "p_overlap", "vertex_ids": ["ov1", "ov4", "ov3", "ov2"]})
    assert_raises(ValueError, validate_layout_topology, spec, match="Exact polygon overlap detected")
    print("  Exact pairwise polygon overlap rejected: PASSED")


def test_raw_vertex_outside_unit_square_rejection():
    print("\n--- 13. Testing Raw Vertex Coordinate Outside [0, 1] Rejection (Phase 3D-0) ---")
    spec = get_default_panel_layout_spec(832, 1216, preset="1_full")
    # frame を [0, 1] 全域に変更した場合でも raw x > 1.0 が clamp されず reject されること
    spec["frame"] = {"x": 0.0, "y": 0.0, "w": 1.0, "h": 1.0}
    spec["vertices"][0]["x"] = 1.25
    assert_raises(ValueError, validate_panel_layout_spec, spec, match="must be in \\[0.0, 1.0\\]")
    print("  Raw vertex outside [0, 1] rejected: PASSED")


def run_all():
    print("================================================================================")
    print("Running Rigorous Panel Layout Topology Tests (Phase 3D-0 / 3C.1.2)")
    print("================================================================================")
    test_valid_presets_topology()
    test_self_intersection_bow_tie_rejection()
    test_duplicate_vertex_in_cycle_rejection()
    test_zero_length_edge_rejection()
    test_edge_incidence_overflow_rejection()
    test_t_junction_detection_and_rejection()
    test_area_conservation_and_gap_overlap_diagnostics()
    test_frame_outside_vertex_rejection()
    test_duplicate_coordinate_rejection()
    test_orphan_vertex_rejection()
    test_internal_edge_gap_incidence_1_rejection()
    test_exact_pairwise_overlap_rejection()
    test_raw_vertex_outside_unit_square_rejection()
    print("\n================================================================================")
    print("[SUCCESS] ALL 13 PANEL LAYOUT TOPOLOGY TESTS PASSED!")
    print("================================================================================")
    return 0


if __name__ == "__main__":
    sys.exit(run_all())


