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
    validate_panel_layout_spec,
    polygon_signed_area
)
from custom_nodes.tegaki_manga_nodes.panel_layout_editor import TegakiMangaPanelLayoutEditor


def test_shared_vertex_drag():
    print("\n--- 1. Testing Shared Vertex Drag (Simultaneous Dual-Panel Deformation) ---")
    spec = get_default_panel_layout_spec(832, 1216, preset="3_basic")
    # v5 は p1, p2, p3 に共有されているキー頂点 (x=0.50, y=0.45)
    v5 = next(v for v in spec["vertices"] if v["id"] == "v5")
    assert v5["x"] == 0.50
    assert v5["y"] == 0.45

    # 共有頂点 v5 を右下 (0.65, 0.55) へドラッグ移動
    v5["x"] = 0.65
    v5["y"] = 0.55

    validated = validate_panel_layout_spec(spec)
    # 隣接する全パネルが隙間なく頂点 v5 の新座標を共有
    for p in validated["panels"]:
        if "v5" in p["vertex_ids"]:
            pts = [(v["x"], v["y"]) for v in validated["vertices"] if v["id"] in p["vertex_ids"]]
            assert abs(polygon_signed_area(pts)) > 0.01, f"Panel {p['id']} must remain non-degenerate"
    print("  Shared vertex v5 moved to (0.65, 0.55) with all adjacent panels intact: PASSED")


def test_panel_split_simulation():
    print("\n--- 2. Testing Panel Split Simulation via Production Generic Split ---")
    from custom_nodes.tegaki_manga_nodes.panel_layout_split import generic_split_panel

    spec = get_default_panel_layout_spec(832, 1216, preset="1_full")
    assert len(spec["panels"]) == 1

    # Split 1 -> 2 panels (Horizontal)
    spec = generic_split_panel(spec, "p1", split_mode="horizontal", split_ratio=0.5)
    validated = validate_panel_layout_spec(spec)
    assert len(validated["panels"]) == 2
    print("  Split 1 -> 2 panels (Horizontal): PASSED")

    # Split 2 -> 3 panels (Vertical on p2)
    spec = generic_split_panel(spec, "p2", split_mode="vertical", split_ratio=0.5)
    validated2 = validate_panel_layout_spec(spec)
    assert len(validated2["panels"]) == 3
    print("  Split 2 -> 3 panels (Vertical): PASSED")


def test_undo_redo_simulation():
    print("\n--- 3. Testing Undo / Redo History Stack Simulation ---")
    undo_stack = []
    redo_stack = []

    state0 = get_default_panel_layout_spec(832, 1216, preset="1_full")
    state1 = get_default_panel_layout_spec(832, 1216, preset="3_basic")
    state2 = get_default_panel_layout_spec(832, 1216, preset="4_grid")

    # Transition: 0 -> 1 -> 2
    cur_state = copy.deepcopy(state0)
    undo_stack.append(json.dumps(cur_state))
    cur_state = copy.deepcopy(state1)
    undo_stack.append(json.dumps(cur_state))
    cur_state = copy.deepcopy(state2)

    assert len(cur_state["panels"]) == 4

    # Undo: 2 -> 1
    redo_stack.append(json.dumps(cur_state))
    cur_state = json.loads(undo_stack.pop())
    assert len(cur_state["panels"]) == 3
    print("  Undo successfully reverted 4-panel to 3-panel state: PASSED")

    # Undo: 1 -> 0
    redo_stack.append(json.dumps(cur_state))
    cur_state = json.loads(undo_stack.pop())
    assert len(cur_state["panels"]) == 1
    print("  Undo successfully reverted 3-panel to 1-panel state: PASSED")

    # Redo: 0 -> 1
    undo_stack.append(json.dumps(cur_state))
    cur_state = json.loads(redo_stack.pop())
    assert len(cur_state["panels"]) == 3
    print("  Redo successfully advanced 1-panel to 3-panel state: PASSED")


def run_all():
    print("================================================================================")
    print("Running PANEL_LAYOUT State & Interaction Tests (Phase 3C.1)")
    print("================================================================================")
    test_shared_vertex_drag()
    test_panel_split_simulation()
    test_undo_redo_simulation()
    print("\n================================================================================")
    print("[SUCCESS] ALL PANEL_LAYOUT STATE & INTERACTION TESTS PASSED!")
    print("================================================================================")
    return 0


if __name__ == "__main__":
    sys.exit(run_all())
