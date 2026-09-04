import os
import sys
import json
import unittest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CUSTOM_NODES_PATH = os.path.join(PROJECT_ROOT, "custom_nodes_custom")
if CUSTOM_NODES_PATH not in sys.path:
    sys.path.insert(0, CUSTOM_NODES_PATH)

from tegaki_manga_nodes.panel_layout_spec import get_default_panel_layout_spec
from tegaki_manga_nodes.panel_layout_split import generic_split_panel
from tegaki_manga_nodes.layout_region_bridge import build_panel_content_bridge


from tegaki_manga_nodes.scene_compiler import TegakiMangaPageCompiler


def create_dummy_compile_plan(num_komas: int, disabled_indices=None):
    if disabled_indices is None:
        disabled_indices = set()

    regions = []
    for i in range(1, num_komas + 1):
        is_enabled = (i not in disabled_indices)
        reg = {
            "id": i,
            "name": f"KOMA {i}",
            "enabled": is_enabled,
            "x": 0.05, "y": 0.05 + 0.15 * (i - 1), "w": 0.90, "h": 0.12,
            "prompt": f"koma {i} prompt",
            "negative_prompt": "",
            "local_regions": [
                {
                    "id": f"lr_{i}",
                    "name": f"Item {i}",
                    "area": {"x": 0.1, "y": 0.1, "w": 0.3, "h": 0.3},
                    "prompt": f"local item {i}",
                    "negative_prompt": "",
                    "weight": 1.0,
                    "enabled": True
                }
            ],
            "characters": [
                {
                    "character_id": "char_alice",
                    "enabled": True,
                    "prompt_override": f"character {i}A prompt",
                    "area": {"x": 0.05, "y": 0.05, "w": 0.50, "h": 0.80}
                },
                {
                    "character_id": "char_bob",
                    "enabled": True,
                    "prompt_override": f"character {i}B prompt",
                    "area": {"x": 0.35, "y": 0.05, "w": 0.55, "h": 0.80}
                }
            ]
        }
        regions.append(reg)

    spec = {
        "version": 1,
        "canvas": {"width": 832, "height": 1216},
        "panel_count": num_komas,
        "global_prompt": "master page global prompt",
        "global_negative_prompt": "blurry, low quality",
        "regions": regions
    }
    cast_spec = {
        "version": 1,
        "characters": [
            {"id": "char_alice", "name": "Alice", "base_prompt": "1girl, blonde hair", "default_negative_prompt": ""},
            {"id": "char_bob", "name": "Bob", "base_prompt": "1boy, black hair", "default_negative_prompt": ""}
        ]
    }
    page_compiler = TegakiMangaPageCompiler()
    plan, _, _, _ = page_compiler.compile_page(region_spec=spec, cast_spec=cast_spec)
    return plan


class TestLayoutRegionMapping(unittest.TestCase):
    """
    Phase 3D: Layout Region Bridge & Mapping Unit Tests
    """

    def test_01_mapping_n1_full(self):
        """N=1: 1_full layout + 1 active KOMA -> 正常マッピング"""
        plan = create_dummy_compile_plan(1)
        layout = get_default_panel_layout_spec(832, 1216, preset="1_full")
        bridge = build_panel_content_bridge(plan, layout)

        self.assertEqual(bridge["active_koma_count"], 1)
        self.assertEqual(bridge["layout_panel_count"], 1)
        self.assertEqual(bridge["panel_content_map"], {"1": "p1"})
        self.assertEqual(len(bridge["mapped_panels"]), 1)
        self.assertEqual(len(bridge["characters"]), 2)
        self.assertEqual(len(bridge["local_regions"]), 1)

    def test_02_mapping_n3_basic(self):
        """N=3: 3_basic layout + 3 active KOMAs -> 決定論的マッピング (1->p1, 2->p2, 3->p3)"""
        plan = create_dummy_compile_plan(3)
        layout = get_default_panel_layout_spec(832, 1216, preset="3_basic")
        bridge = build_panel_content_bridge(plan, layout)

        self.assertEqual(bridge["active_koma_count"], 3)
        self.assertEqual(bridge["layout_panel_count"], 3)
        self.assertEqual(bridge["panel_content_map"], {"1": "p1", "2": "p2", "3": "p3"})
        self.assertEqual(len(bridge["mapped_panels"]), 3)
        self.assertEqual(len(bridge["characters"]), 6)
        self.assertEqual(len(bridge["local_regions"]), 3)

    def test_03_mapping_n4_grid(self):
        """N=4: 4_grid layout + 4 active KOMAs -> 4パネル正常マッピング"""
        plan = create_dummy_compile_plan(4)
        layout = get_default_panel_layout_spec(832, 1216, preset="4_grid")
        bridge = build_panel_content_bridge(plan, layout)

        self.assertEqual(bridge["active_koma_count"], 4)
        self.assertEqual(bridge["layout_panel_count"], 4)
        self.assertEqual(bridge["panel_content_map"], {"1": "p1", "2": "p2", "3": "p3", "4": "p4"})

    def test_04_mapping_n5_split(self):
        """N=5: 一般分割で生成した5パネルレイアウト + 5 active KOMAs -> 正常マッピング"""
        # 4_grid の p1 を分割して 5 パネル化
        base_layout = get_default_panel_layout_spec(832, 1216, preset="4_grid")
        layout_5 = generic_split_panel(base_layout, "p1", split_mode="horizontal", split_ratio=0.5)
        self.assertEqual(len(layout_5["panels"]), 5)

        plan = create_dummy_compile_plan(5)
        bridge = build_panel_content_bridge(plan, layout_5)

        self.assertEqual(bridge["active_koma_count"], 5)
        self.assertEqual(bridge["layout_panel_count"], 5)
        self.assertEqual(len(bridge["mapped_panels"]), 5)

    def test_05_mapping_n6_capacity(self):
        """N=6: 最大容量 6 パネルレイアウト + 6 active KOMAs -> 正常マッピング"""
        base_layout = get_default_panel_layout_spec(832, 1216, preset="4_grid")
        l5 = generic_split_panel(base_layout, "p1", split_mode="horizontal", split_ratio=0.5)
        l6 = generic_split_panel(l5, "p2", split_mode="vertical", split_ratio=0.5)
        self.assertEqual(len(l6["panels"]), 6)

        plan = create_dummy_compile_plan(6)
        bridge = build_panel_content_bridge(plan, l6)
        self.assertEqual(bridge["active_koma_count"], 6)
        self.assertEqual(bridge["layout_panel_count"], 6)

    def test_06_count_mismatch_rejection_fail_closed(self):
        """コマ数不一致 (3 vs 4) で勝手に切り捨てず ValueError を発生 (Fail-Closed)"""
        plan_3 = create_dummy_compile_plan(3)
        layout_4 = get_default_panel_layout_spec(832, 1216, preset="4_grid")

        with self.assertRaises(ValueError) as ctx:
            build_panel_content_bridge(plan_3, layout_4)
        self.assertIn("Panel count mismatch", str(ctx.exception))

    def test_07_stable_order_with_shuffled_komas(self):
        """KOMA の配列順序がシャッフルされていても target_panel_id 昇順にソートされて安定対応すること"""
        plan = create_dummy_compile_plan(3)
        # 順序を [3, 1, 2] に入れ替え
        plan["panels"] = [plan["panels"][2], plan["panels"][0], plan["panels"][1]]

        layout = get_default_panel_layout_spec(832, 1216, preset="3_basic")
        bridge = build_panel_content_bridge(plan, layout)

        self.assertEqual(bridge["panel_content_map"], {"1": "p1", "2": "p2", "3": "p3"})
        self.assertEqual(bridge["mapped_panels"][0]["koma_id"], "1")
        self.assertEqual(bridge["mapped_panels"][1]["koma_id"], "2")
        self.assertEqual(bridge["mapped_panels"][2]["koma_id"], "3")

    def test_08_disabled_koma_ignored(self):
        """enabled=False の KOMA は除外され、残りの有効 KOMA 数でレイアウトと一致すること"""
        # 4コマ中、KOMA 2 を無効化 -> 有効コマ 1, 3, 4 (計3コマ)
        plan = create_dummy_compile_plan(4, disabled_indices={2})
        layout = get_default_panel_layout_spec(832, 1216, preset="3_basic")
        bridge = build_panel_content_bridge(plan, layout)

        self.assertEqual(bridge["active_koma_count"], 3)
        self.assertEqual(bridge["panel_content_map"], {"1": "p1", "3": "p2", "4": "p3"})

    def test_09_character_bbox_projection(self):
        """Character の KOMA ローカル座標が Panel BBox 内に正しくスケール・投影されること"""
        plan = create_dummy_compile_plan(1)
        layout = get_default_panel_layout_spec(832, 1216, preset="1_full")
        bridge = build_panel_content_bridge(plan, layout)

        chars = bridge["characters"]
        c1 = chars[0]
        # KOMA 1 local: x=0.05, y=0.05, w=0.50, h=0.80
        # 1_full bbox: x=0.05, y=0.05, w=0.90, h=0.90
        # proj_x = 0.05 + 0.90 * 0.05 = 0.095
        # proj_y = 0.05 + 0.90 * 0.05 = 0.095
        # proj_w = 0.90 * 0.50 = 0.45
        # proj_h = 0.90 * 0.80 = 0.72
        self.assertAlmostEqual(c1["page_projected_area"]["x"], 0.095, places=3)
        self.assertAlmostEqual(c1["page_projected_area"]["y"], 0.095, places=3)
        self.assertAlmostEqual(c1["page_projected_area"]["w"], 0.450, places=3)
        self.assertAlmostEqual(c1["page_projected_area"]["h"], 0.720, places=3)


if __name__ == "__main__":
    unittest.main()
