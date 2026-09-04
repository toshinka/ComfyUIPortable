import os
import sys
import json
import copy
import unittest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CUSTOM_NODES_PATH = os.path.join(PROJECT_ROOT, "custom_nodes_custom")
if CUSTOM_NODES_PATH not in sys.path:
    sys.path.insert(0, CUSTOM_NODES_PATH)

from tegaki_manga_nodes.panel_layout_spec import (
    get_default_panel_layout_spec,
    validate_panel_layout_spec
)
from tegaki_manga_nodes.panel_layout_topology import validate_layout_topology


class FrontendDragTransactionSimulator:
    """
    web/js/panel_layout_editor.js のドラッグトランザクション動作を
    忠実にシミュレートするコントローラー
    """
    def __init__(self, initial_spec):
        self.committed_spec = copy.deepcopy(initial_spec)
        self.preview_candidate = None
        self.drag_vertex_id = None
        self.undo_stack = []
        self.redo_stack = []

    def on_mouse_down(self, vertex_id):
        self.drag_vertex_id = vertex_id
        # トランザクション開始: 確定状態と candidate を分離
        self.preview_candidate = copy.deepcopy(self.committed_spec)

    def on_mouse_move(self, target_x, target_y):
        if not self.drag_vertex_id or not self.preview_candidate:
            return
        frame = self.preview_candidate.get("frame", {"x": 0.05, "y": 0.05, "w": 0.90, "h": 0.90})
        fx_min, fx_max = frame["x"], frame["x"] + frame["w"]
        fy_min, fy_max = frame["y"], frame["y"] + frame["h"]

        # 外周境界スライド拘束
        orig_v = next(v for v in self.committed_spec["vertices"] if v["id"] == self.drag_vertex_id)
        cand_x, cand_y = target_x, target_y

        if abs(orig_v["x"] - fx_min) < 1e-3:
            cand_x = fx_min
            cand_y = max(fy_min, min(fy_max, cand_y))
        elif abs(orig_v["x"] - fx_max) < 1e-3:
            cand_x = fx_max
            cand_y = max(fy_min, min(fy_max, cand_y))
        elif abs(orig_v["y"] - fy_min) < 1e-3:
            cand_y = fy_min
            cand_x = max(fx_min, min(fx_max, cand_x))
        elif abs(orig_v["y"] - fy_max) < 1e-3:
            cand_y = fy_max
            cand_x = max(fx_min, min(fx_max, cand_x))

        target_v = next(v for v in self.preview_candidate["vertices"] if v["id"] == self.drag_vertex_id)
        target_v["x"] = round(cand_x, 4)
        target_v["y"] = round(cand_y, 4)

    def on_mouse_up(self):
        if not self.drag_vertex_id:
            return False
        self.drag_vertex_id = None
        candidate = self.preview_candidate
        self.preview_candidate = None

        try:
            # Backend Validator API による厳格検証
            validated = validate_panel_layout_spec(candidate, context_name="Sim.MouseUp")
            # VALID: Commit!
            self.undo_stack.append(copy.deepcopy(self.committed_spec))
            self.redo_stack.clear()
            self.committed_spec = validated
            return True
        except Exception:
            # INVALID: Rollback! (committed_spec は変更されない)
            return False

    def undo(self):
        if not self.undo_stack:
            return False
        self.redo_stack.append(copy.deepcopy(self.committed_spec))
        self.committed_spec = self.undo_stack.pop()
        return True

    def redo(self):
        if not self.redo_stack:
            return False
        self.undo_stack.append(copy.deepcopy(self.committed_spec))
        self.committed_spec = self.redo_stack.pop()
        return True


class TestPanelLayoutDragValidation(unittest.TestCase):
    """
    Phase 3C.1.2: Frontend Drag Transaction Model Tests
    Committed Spec vs Preview Candidate Spec の分離、検証失敗時ロールバック、
    Undo / Redo の確定性、および外周拘束を厳密に検証する。
    """

    def setUp(self):
        self.initial_spec = get_default_panel_layout_spec(832, 1216, preset="3_basic")
        self.sim = FrontendDragTransactionSimulator(self.initial_spec)

    def test_01_valid_drag_commits_and_records_undo(self):
        """有効な内部頂点移動がコミットされ、Undo 履歴に記録されること"""
        self.sim.on_mouse_down("v5")
        self.sim.on_mouse_move(0.55, 0.50)
        success = self.sim.on_mouse_up()

        self.assertTrue(success, "Valid drag must commit successfully")
        committed_v5 = next(v for v in self.sim.committed_spec["vertices"] if v["id"] == "v5")
        self.assertEqual(committed_v5["x"], 0.55)
        self.assertEqual(committed_v5["y"], 0.50)
        self.assertEqual(len(self.sim.undo_stack), 1)

    def test_02_invalid_drag_rolls_back_and_never_corrupts_committed(self):
        """不正な移動 (Frame逸脱・自己交差・縮退) が確実にロールバックされ、確定状態を壊さないこと"""
        orig_v5 = next(v for v in self.sim.committed_spec["vertices"] if v["id"] == "v5")
        orig_x, orig_y = orig_v5["x"], orig_v5["y"]

        # 不正移動: v5 を Frame 外 (0.01, 0.01) へ移動
        self.sim.on_mouse_down("v5")
        self.sim.on_mouse_move(0.01, 0.01)
        success = self.sim.on_mouse_up()

        self.assertFalse(success, "Invalid drag must fail validation")
        committed_v5 = next(v for v in self.sim.committed_spec["vertices"] if v["id"] == "v5")
        self.assertEqual(committed_v5["x"], orig_x, "Committed spec must retain original X")
        self.assertEqual(committed_v5["y"], orig_y, "Committed spec must retain original Y")
        self.assertEqual(len(self.sim.undo_stack), 0, "No undo entry should be recorded for failed drag")

    def test_03_duplicate_coordinate_move_rolls_back(self):
        """頂点を既存の別頂点と同一座標に重ねる移動 (縮退) がロールバックされること"""
        self.sim.on_mouse_down("v5")
        # v5(0.50, 0.45) を v4(0.05, 0.45) と完全に同じ座標へ移動
        self.sim.on_mouse_move(0.05, 0.45)
        success = self.sim.on_mouse_up()

        self.assertFalse(success, "Overlapping coordinate move must be rejected")
        committed_v5 = next(v for v in self.sim.committed_spec["vertices"] if v["id"] == "v5")
        self.assertEqual(committed_v5["x"], 0.50)

    def test_04_outer_boundary_sliding_constraint(self):
        """外周中間頂点 (v7) が外周枠線上のみに拘束されてスライド移動すること"""
        self.sim.on_mouse_down("v7")  # 下辺 y=0.95
        # 斜め内側 (0.60, 0.80) に引っ張っても、y=0.95 に拘束される
        self.sim.on_mouse_move(0.60, 0.80)
        success = self.sim.on_mouse_up()

        self.assertTrue(success, "Constrained outer boundary slide must be valid")
        committed_v7 = next(v for v in self.sim.committed_spec["vertices"] if v["id"] == "v7")
        self.assertEqual(committed_v7["x"], 0.60)
        self.assertEqual(committed_v7["y"], 0.95, "Y must remain constrained to frame boundary (0.95)")

    def test_05_undo_and_redo_integrity(self):
        """ドラッグ後の Undo / Redo が完全かつ無損失に動作すること"""
        self.sim.on_mouse_down("v5")
        self.sim.on_mouse_move(0.55, 0.50)
        self.sim.on_mouse_up()

        # Undo
        self.assertTrue(self.sim.undo())
        v5_undo = next(v for v in self.sim.committed_spec["vertices"] if v["id"] == "v5")
        self.assertEqual(v5_undo["x"], 0.50)

        # Redo
        self.assertTrue(self.sim.redo())
        v5_redo = next(v for v in self.sim.committed_spec["vertices"] if v["id"] == "v5")
        self.assertEqual(v5_redo["x"], 0.55)


if __name__ == "__main__":
    print("================================================================================")
    print("Running Panel Layout Drag Validation & Transaction Tests (Phase 3C.1.2)")
    print("================================================================================")
    unittest.main(verbosity=2)
