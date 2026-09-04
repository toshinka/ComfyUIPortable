import os
import sys
import json
import unittest
import torch

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CUSTOM_NODES_PATH = os.path.join(PROJECT_ROOT, "custom_nodes_custom")
SCRIPTS_PATH = os.path.dirname(__file__)
if CUSTOM_NODES_PATH not in sys.path:
    sys.path.insert(0, CUSTOM_NODES_PATH)
if SCRIPTS_PATH not in sys.path:
    sys.path.insert(0, SCRIPTS_PATH)

from tegaki_manga_nodes.panel_layout_spec import get_default_panel_layout_spec
from tegaki_manga_nodes.panel_layout_split import generic_split_panel
from tegaki_manga_nodes.layout_region_bridge import build_panel_content_bridge
from tegaki_manga_nodes.layout_aware_mask_builder import build_layout_aware_masks
from test_layout_region_mapping import create_dummy_compile_plan


class TestLayoutAwareMasks(unittest.TestCase):
    """
    Phase 3D: Layout-Aware Mask Builder Tests
    多角形パネルマスク、クリッピング、Semantic Overlap、フェザー検証
    """

    def test_01_3_basic_polygon_masks(self):
        """3_basic: 3枚の多角形パネルマスクの形状・非重複性・フレーム内包検証"""
        plan = create_dummy_compile_plan(3)
        layout = get_default_panel_layout_spec(832, 1216, preset="3_basic")
        bridge = build_panel_content_bridge(plan, layout)

        panel_masks, char_masks, preview, debug_json, lr_masks = build_layout_aware_masks(bridge, mask_feather=0)

        self.assertEqual(panel_masks.shape, (3, 1216, 832))
        self.assertEqual(char_masks.shape, (6, 1216, 832))  # 各コマ2人 x 3コマ
        self.assertEqual(lr_masks.shape, (3, 1216, 832))    # 各コマ1個 x 3コマ
        self.assertEqual(preview.shape, (1, 1216, 832, 3))

        # パネルマスク間の非重複性 (Pairwise non-overlap)
        # 注意: PILの多角形描画では共有エッジ上の1px境界ピクセルが両多角形に含まれ得るため、
        # 共有境界線の長さ (約750px) 以下の微小境界ピクセル数を許容する
        p0_p1_intersect = (panel_masks[0] * panel_masks[1]).sum().item()
        p1_p2_intersect = (panel_masks[1] * panel_masks[2]).sum().item()
        p0_p2_intersect = (panel_masks[0] * panel_masks[2]).sum().item()

        self.assertLess(p0_p1_intersect, 800.0)
        self.assertLess(p1_p2_intersect, 800.0)
        self.assertLess(p0_p2_intersect, 800.0)

    def test_02_3_dynamic_slanted_polygon_masks(self):
        """3_dynamic: 斜め多角形パネルマスクの正常ラスタライズと非重複性"""
        plan = create_dummy_compile_plan(3)
        layout = get_default_panel_layout_spec(832, 1216, preset="3_dynamic")
        bridge = build_panel_content_bridge(plan, layout)

        panel_masks, char_masks, preview, debug_json, lr_masks = build_layout_aware_masks(bridge, mask_feather=0)
        self.assertEqual(panel_masks.shape, (3, 1216, 832))

        # 斜めパネル同士の重なりが共有境界ピクセル以下であること
        overlap = (panel_masks[0] * panel_masks[1]).sum().item()
        self.assertLess(overlap, 800.0)

    def test_03_character_semantic_overlap_allowed(self):
        """同一コマ内での複数人物 (Alice & Bob) の Semantic Overlap が維持されていること"""
        plan = create_dummy_compile_plan(3)
        layout = get_default_panel_layout_spec(832, 1216, preset="3_basic")
        bridge = build_panel_content_bridge(plan, layout)

        panel_masks, char_masks, preview, debug_json, lr_masks = build_layout_aware_masks(bridge, mask_feather=0)

        # KOMA 1 内の Char A (idx 0) と Char B (idx 1)
        c0 = char_masks[0]
        c1 = char_masks[1]

        overlap_area = (c0 * c1).sum().item()
        # Alice (0.05..0.55) と Bob (0.35..0.90) は x方向で 0.35..0.55 で重なるため、積が正であること
        self.assertGreater(overlap_area, 1000.0, "Char A and Char B must have positive overlap area in KOMA 1")

    def test_04_character_strictly_clipped_by_panel_polygon(self):
        """Character Mask が Panel Polygon の外部に一切漏れ出さない (厳格クリッピング) こと"""
        plan = create_dummy_compile_plan(3)
        layout = get_default_panel_layout_spec(832, 1216, preset="3_dynamic")
        bridge = build_panel_content_bridge(plan, layout)

        panel_masks, char_masks, preview, debug_json, lr_masks = build_layout_aware_masks(bridge, mask_feather=0)

        # 全てのキャラクターについて、所属パネルマスク外の領域が 0 であること
        for c_idx, c in enumerate(bridge["characters"]):
            p_idx = c["panel_index"]
            c_mask = char_masks[c_idx]
            p_mask = panel_masks[p_idx]

            # (1 - p_mask) 領域における c_mask の合計値が 0 であること
            outside_leak = (c_mask * (1.0 - p_mask)).sum().item()
            self.assertEqual(outside_leak, 0.0, f"Character {c_idx} leaked outside panel polygon {p_idx}")

    def test_05_local_region_strictly_clipped_by_panel_polygon(self):
        """Local Region Mask が Panel Polygon の外部に漏れ出さないこと"""
        plan = create_dummy_compile_plan(3)
        layout = get_default_panel_layout_spec(832, 1216, preset="3_dynamic")
        bridge = build_panel_content_bridge(plan, layout)

        panel_masks, char_masks, preview, debug_json, lr_masks = build_layout_aware_masks(bridge, mask_feather=0)

        for l_idx, lr in enumerate(bridge["local_regions"]):
            p_idx = lr["panel_index"]
            l_mask = lr_masks[l_idx]
            p_mask = panel_masks[p_idx]

            outside_leak = (l_mask * (1.0 - p_mask)).sum().item()
            self.assertEqual(outside_leak, 0.0, f"Local Region {l_idx} leaked outside panel polygon {p_idx}")

    def test_06_mask_feathering(self):
        """mask_feather > 0 で境界に中間値 (ぼかし) が生成されること"""
        plan = create_dummy_compile_plan(1)
        layout = get_default_panel_layout_spec(832, 1216, preset="1_full")
        bridge = build_panel_content_bridge(plan, layout)

        panel_masks, char_masks, preview, debug_json, lr_masks = build_layout_aware_masks(bridge, mask_feather=8)

        # フェザー適用により 0 < val < 1 のピクセルが存在すること
        intermediate = ((panel_masks[0] > 0.05) & (panel_masks[0] < 0.95)).sum().item()
        self.assertGreater(intermediate, 500, "Feathering must produce intermediate values along boundaries")


if __name__ == "__main__":
    unittest.main()
