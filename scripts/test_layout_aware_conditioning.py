import os
import sys
import json
import unittest
import torch

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
COMFYUI_DIR = os.path.join(PROJECT_ROOT, "ComfyUI")
CUSTOM_NODES_PATH = os.path.join(PROJECT_ROOT, "custom_nodes_custom")
SCRIPTS_PATH = os.path.dirname(__file__)
if COMFYUI_DIR not in sys.path:
    sys.path.insert(0, COMFYUI_DIR)
if CUSTOM_NODES_PATH not in sys.path:
    sys.path.insert(0, CUSTOM_NODES_PATH)
if SCRIPTS_PATH not in sys.path:
    sys.path.insert(0, SCRIPTS_PATH)

from tegaki_manga_nodes.panel_layout_spec import get_default_panel_layout_spec
from tegaki_manga_nodes.layout_aware_conditioning import TegakiMangaLayoutAwareConditioningBuilder
from test_layout_region_mapping import create_dummy_compile_plan


class MockCLIP:
    def tokenize(self, text):
        return {"text": text}

    def encode_from_tokens_scheduled(self, tokens):
        text = tokens.get("text", "")
        cond_tensor = torch.zeros((1, 77, 768), dtype=torch.float32)
        pooled_tensor = torch.zeros((1, 768), dtype=torch.float32)
        return [[cond_tensor, {"pooled_output": pooled_tensor, "debug_text": text}]]


class TestLayoutAwareConditioning(unittest.TestCase):
    """
    Phase 3D: Layout-Aware Conditioning Builder Tests
    4階層 (Global / Panel / Local / Character) Conditioning結合と多角形マスク適用検証
    """

    def setUp(self):
        self.builder = TegakiMangaLayoutAwareConditioningBuilder()
        self.clip = MockCLIP()

    def test_01_3_panel_conditioning_branches(self):
        """3パネル構成での階層 Conditioning 結合検証"""
        plan = create_dummy_compile_plan(3)
        layout = get_default_panel_layout_spec(832, 1216, preset="3_basic")

        pos, neg, panel_masks, char_masks, preview, debug_json, lr_masks = self.builder.build_conditioning(
            clip=self.clip,
            page_compile_plan=plan,
            panel_layout_spec=layout,
            panel_strength=1.0,
            character_strength=0.9,
            local_region_strength=0.8,
            mask_feather=0
        )

        self.assertIsInstance(pos, list)
        self.assertIsInstance(neg, list)

        # 枝の内訳:
        # Global: 1
        # Panels: 3 (KOMA 1, 2, 3)
        # Local Regions: 3 (各コマ1)
        # Characters: 6 (各コマ2)
        # 合計: 1 + 3 + 3 + 6 = 13 branches
        self.assertEqual(len(pos), 13, f"Expected 13 positive branches, got {len(pos)}")

        # 最初のブランチは Global でマスク無し
        g_meta = pos[0][1]
        self.assertNotIn("mask", g_meta, "Global positive conditioning should not have mask")

        # 2番目のブランチは Panel 1 で多角形マスク付き
        p1_meta = pos[1][1]
        self.assertIn("mask", p1_meta)
        self.assertEqual(p1_meta["mask_strength"], 1.0)

        # Debug JSON の構造検証
        debug_data = json.loads(debug_json)
        self.assertEqual(debug_data["mode"], "layout_driven_polygon_conditioning")
        self.assertEqual(debug_data["panel_content_map"], {"1": "p1", "2": "p2", "3": "p3"})
        self.assertEqual(len(debug_data["panels"]), 3)
        self.assertEqual(len(debug_data["characters"]), 6)
        self.assertEqual(len(debug_data["local_regions"]), 3)

    def test_02_finite_float_validation(self):
        """NaN や Inf の強度が与えられた場合に ValueError で拒絶されること"""
        plan = create_dummy_compile_plan(3)
        layout = get_default_panel_layout_spec(832, 1216, preset="3_basic")

        with self.assertRaises(ValueError):
            self.builder.build_conditioning(
                clip=self.clip,
                page_compile_plan=plan,
                panel_layout_spec=layout,
                panel_strength=float("nan")
            )

        with self.assertRaises(ValueError):
            self.builder.build_conditioning(
                clip=self.clip,
                page_compile_plan=plan,
                panel_layout_spec=layout,
                character_strength=float("inf")
            )

    def test_03_panel_count_mismatch_fails_closed(self):
        """KOMA 数と Layout パネル数が一致しない場合に ValueError で拒絶されること"""
        plan_3 = create_dummy_compile_plan(3)
        layout_4 = get_default_panel_layout_spec(832, 1216, preset="4_grid")

        with self.assertRaises(ValueError) as ctx:
            self.builder.build_conditioning(
                clip=self.clip,
                page_compile_plan=plan_3,
                panel_layout_spec=layout_4
            )
        self.assertIn("Panel count mismatch", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
