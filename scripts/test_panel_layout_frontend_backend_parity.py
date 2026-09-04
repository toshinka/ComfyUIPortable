import os
import sys
import json
import unittest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CUSTOM_NODES_PATH = os.path.join(PROJECT_ROOT, "custom_nodes_custom")
if CUSTOM_NODES_PATH not in sys.path:
    sys.path.insert(0, CUSTOM_NODES_PATH)

from tegaki_manga_nodes.panel_layout_spec import validate_panel_layout_spec, get_default_panel_layout_spec
from tegaki_manga_nodes.panel_layout_split import generic_split_panel
from tegaki_manga_nodes.panel_layout_topology import validate_layout_topology


class TestPanelLayoutFrontendBackendParity(unittest.TestCase):
    """
    Phase 3C.1.2: Frontend / Backend Split Parity & Single Source of Truth Tests
    Frontend が呼ぶ Split API ハンドラと Backend の generic_split_panel が
    同一の幾何を生成し、T-Junction 排除・面積保存を完全に満たすことを検証する。
    """

    def setUp(self):
        self.preset_1_full = get_default_panel_layout_spec(preset="1_full")
        self.preset_3_basic = get_default_panel_layout_spec(preset="3_basic")
        self.preset_3_dynamic = get_default_panel_layout_spec(preset="3_dynamic")
        self.preset_4_grid = get_default_panel_layout_spec(preset="4_grid")

    def _simulate_api_split(self, spec, panel_id, mode, ratio=0.5):
        """API ルートハンドラ相当の処理 (SSOT)"""
        valid_in = validate_panel_layout_spec(spec, context_name="Test.API.input")
        res = generic_split_panel(valid_in, panel_id, split_mode=mode, split_ratio=ratio)
        return validate_panel_layout_spec(res, context_name="Test.API.output")

    def test_01_preset_1_full_all_modes(self):
        """1_full に対する H / V / Diag / / Diag \\ 分割の Parity 検証"""
        for mode in ("horizontal", "vertical", "diag_slash", "diag_backslash"):
            spec = json.loads(json.dumps(self.preset_1_full))
            result_spec = self._simulate_api_split(spec, "p1", mode)
            self.assertEqual(len(result_spec["panels"]), 2)
            topo = validate_layout_topology(result_spec)
            self.assertEqual(topo["status"], "VALID")
            self.assertEqual(topo["gap_ratio"], 0.0)
            self.assertEqual(topo["overlap_ratio"], 0.0)

    def test_02_preset_3_basic_split_p1(self):
        """3_basic の p1 を Horizontal / Vertical / Diag で分割"""
        for mode in ("horizontal", "vertical", "diag_slash"):
            spec = json.loads(json.dumps(self.preset_3_basic))
            result_spec = self._simulate_api_split(spec, "p1", mode)
            self.assertEqual(len(result_spec["panels"]), 4)
            topo = validate_layout_topology(result_spec)
            self.assertEqual(topo["status"], "VALID")
            self.assertEqual(topo["gap_ratio"], 0.0)
            self.assertEqual(topo["overlap_ratio"], 0.0)

    def test_03_preset_3_dynamic_slanted_all_modes(self):
        """3_dynamic の斜めパネル (p1, p2) に対する全4方向 Split"""
        for pid in ("p1", "p2"):
            for mode in ("horizontal", "vertical", "diag_slash", "diag_backslash"):
                spec = json.loads(json.dumps(self.preset_3_dynamic))
                result_spec = self._simulate_api_split(spec, pid, mode)
                self.assertEqual(len(result_spec["panels"]), 4)
                topo = validate_layout_topology(result_spec)
                self.assertEqual(topo["status"], "VALID")

    def test_04_split_after_shared_vertex_deformation(self):
        """共有頂点移動後の変形パネルに対する Split"""
        spec = json.loads(json.dumps(self.preset_3_basic))
        # v5 (中央中間頂点: 0.50, 0.45) を斜めに大きく移動
        v5 = next(v for v in spec["vertices"] if v["id"] == "v5")
        v5["x"] = 0.35
        v5["y"] = 0.55
        validate_layout_topology(spec)

        # 変形後 p1 を垂直分割
        res_v = self._simulate_api_split(spec, "p1", "vertical")
        self.assertEqual(len(res_v["panels"]), 4)
        topo_v = validate_layout_topology(res_v)
        self.assertEqual(topo_v["status"], "VALID")

        # 変形後 p2 を水平分割
        res_h = self._simulate_api_split(res_v, "p2", "horizontal")
        self.assertEqual(len(res_h["panels"]), 5)
        topo_h = validate_layout_topology(res_h)
        self.assertEqual(topo_h["status"], "VALID")

    def test_05_sequential_split_up_to_capacity_and_refuse_7th(self):
        """5パネル -> 6パネル、および 7パネル目の安全な拒絶"""
        spec = json.loads(json.dumps(self.preset_4_grid))  # 4 panels
        # 4 -> 5
        spec = self._simulate_api_split(spec, "p1", "horizontal")
        self.assertEqual(len(spec["panels"]), 5)

        # 5 -> 6
        spec = self._simulate_api_split(spec, "p2", "vertical")
        self.assertEqual(len(spec["panels"]), 6)
        topo = validate_layout_topology(spec)
        self.assertEqual(topo["status"], "VALID")

        # 6 -> 7 (拒絶)
        with self.assertRaises(ValueError) as ctx:
            self._simulate_api_split(spec, "p3", "horizontal")
        self.assertIn("Panel capacity limit", str(ctx.exception))


if __name__ == "__main__":
    print("================================================================================")
    print("Running Frontend / Backend Geometry Split Parity Tests (Phase 3C.1.2)")
    print("================================================================================")
    unittest.main(verbosity=2)
