import os
import sys
import torch
import numpy as np

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CUSTOM_NODES_DIR = os.path.join(ROOT_DIR, "ComfyUI", "custom_nodes")
if CUSTOM_NODES_DIR not in sys.path:
    sys.path.insert(0, CUSTOM_NODES_DIR)
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from custom_nodes.tegaki_manga_nodes.panel_layout_spec import get_default_panel_layout_spec
from custom_nodes.tegaki_manga_nodes.panel_layout_editor import TegakiMangaPanelLayoutEditor, render_panel_layout_image


def test_renderer_output_properties():
    print("\n--- 1. Testing Renderer Image Tensor Shape & Types ---")
    editor = TegakiMangaPanelLayoutEditor()
    tensor_img, spec, debug_json = editor.execute_layout_editor(
        canvas_width=832,
        canvas_height=1216,
        line_thickness=4,
        panel_layout_spec_data=""
    )

    assert isinstance(tensor_img, torch.Tensor)
    assert tensor_img.shape == (1, 1216, 832, 3), f"Expected (1, 1216, 832, 3), got {tensor_img.shape}"
    assert tensor_img.dtype == torch.float32
    print("  Image tensor shape (1, 1216, 832, 3) & dtype float32: PASSED")


def test_pure_monochrome_and_no_text():
    print("\n--- 2. Testing Pure Monochrome (White BG + Black Lines Only, No Color/Text) ---")
    editor = TegakiMangaPanelLayoutEditor()
    tensor_img, spec, _ = editor.execute_layout_editor(
        canvas_width=832,
        canvas_height=1216,
        line_thickness=4,
        panel_layout_spec_data=""
    )

    np_img = tensor_img[0].numpy()  # [1216, 832, 3]

    # R, G, B がすべて同一（グレースケール・モノクロ）であることを確認
    diff_rg = np.abs(np_img[:, :, 0] - np_img[:, :, 1])
    diff_gb = np.abs(np_img[:, :, 1] - np_img[:, :, 2])
    assert diff_rg.max() < 1e-4, "Image must have no colored pixels"
    assert diff_gb.max() < 1e-4, "Image must have no colored pixels"

    # 背景が純白 (1.0) であるピクセルが大部分を占めること
    white_pixels = (np_img[:, :, 0] >= 0.99).sum()
    total_pixels = 832 * 1216
    white_ratio = white_pixels / total_pixels
    assert white_ratio > 0.90, f"Background must be predominantly white, got {white_ratio:.2%}"

    # コマ線（純黒 0.0）が存在すること
    black_pixels = (np_img[:, :, 0] <= 0.01).sum()
    assert black_pixels > 1000, f"Black panel lines must exist, got {black_pixels} pixels"
    print(f"  White BG ({white_ratio:.1%}) & Black lines ({black_pixels} px), zero color contamination: PASSED")


def run_all():
    print("================================================================================")
    print("Running Panel Layout Renderer Unit Tests (Phase 3C.1)")
    print("================================================================================")
    test_renderer_output_properties()
    test_pure_monochrome_and_no_text()
    print("\n================================================================================")
    print("[SUCCESS] ALL PANEL LAYOUT RENDERER TESTS PASSED!")
    print("================================================================================")
    return 0


if __name__ == "__main__":
    sys.exit(run_all())
