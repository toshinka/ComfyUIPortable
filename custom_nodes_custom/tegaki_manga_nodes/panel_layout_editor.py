import copy
import json
import logging
from typing import Dict, Any, Tuple, Optional, List

import torch
import numpy as np
from PIL import Image, ImageDraw

from .panel_layout_spec import (
    get_default_panel_layout_spec,
    validate_panel_layout_spec,
    MAX_PANELS
)


def render_panel_layout_image(
    spec: Dict[str, Any],
    line_thickness: int = 4
) -> Image.Image:
    """
    ControlNet Layout 用の純粋な漫画コマ割り画像を生成する。
    仕様:
    - 背景: 白 (255, 255, 255)
    - コマ線: 黒 (0, 0, 0)
    - 文字・コマ番号・色は一切描画しない
    """
    W = spec["canvas"]["width"]
    H = spec["canvas"]["height"]

    img = Image.new("RGB", (W, H), (255, 255, 255))
    draw = ImageDraw.Draw(img)

    v_map = {v["id"]: (int(round(v["x"] * W)), int(round(v["y"] * H))) for v in spec["vertices"]}

    for panel in spec["panels"]:
        v_ids = panel["vertex_ids"]
        pts = [v_map[vid] for vid in v_ids if vid in v_map]
        if len(pts) >= 3:
            # 多角形の外周線を黒線で描画
            pts_closed = pts + [pts[0]]
            draw.line(pts_closed, fill=(0, 0, 0), width=line_thickness, joint="miter")

    return img


class TegakiMangaPanelLayoutEditor:
    """
    Tegaki Manga Panel Layout Editor (Phase 3C.1)
    漫画コマ割り（Panel Layout）専用の幾何エディターノード。
    Shared-Vertex Mesh 方式を採用し、ControlNet 向けに純粋な白地・黒線の枠線画像を出力する。
    """
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "canvas_width": ("INT", {"default": 832, "min": 256, "max": 4096, "step": 64}),
                "canvas_height": ("INT", {"default": 1216, "min": 256, "max": 4096, "step": 64}),
                "line_thickness": ("INT", {"default": 4, "min": 1, "max": 32, "step": 1}),
                "panel_layout_spec_data": ("STRING", {"multiline": True, "default": ""}),
            }
        }

    RETURN_TYPES = ("IMAGE", "PANEL_LAYOUT_SPEC", "STRING")
    RETURN_NAMES = ("layout_image", "panel_layout_spec", "debug_json")
    FUNCTION = "execute_layout_editor"
    CATEGORY = "tegaki/manga/layout"

    def execute_layout_editor(
        self,
        canvas_width: int,
        canvas_height: int,
        line_thickness: int = 4,
        panel_layout_spec_data: str = ""
    ) -> Tuple[torch.Tensor, Dict[str, Any], str]:
        spec: Optional[Dict[str, Any]] = None

        if panel_layout_spec_data and panel_layout_spec_data.strip():
            try:
                raw_spec = json.loads(panel_layout_spec_data)
            except json.JSONDecodeError as e:
                logging.warning(f"[TegakiMangaPanelLayoutEditor] Fallback to default layout due to JSON syntax error: {e}")
                raw_spec = None

            if raw_spec is not None:
                # Valid JSON だがスキーマ不正の場合は fail-closed
                spec = validate_panel_layout_spec(raw_spec, context_name="TegakiMangaPanelLayoutEditor")

        if spec is None:
            spec = get_default_panel_layout_spec(canvas_width, canvas_height, preset="3_basic")

        # ウィジェットからの canvas 寸法同期
        spec["canvas"]["width"] = int(canvas_width)
        spec["canvas"]["height"] = int(canvas_height)
        spec = validate_panel_layout_spec(spec, context_name="TegakiMangaPanelLayoutEditor")

        # 1. 白地・黒線の純粋な ControlNet ガイド画像のレンダリング
        pil_img = render_panel_layout_image(spec, line_thickness=int(line_thickness))
        np_img = np.array(pil_img).astype(np.float32) / 255.0
        tensor_img = torch.from_numpy(np_img).unsqueeze(0)  # [1, H, W, 3]

        debug_json = json.dumps(spec, indent=2, ensure_ascii=False)
        return (tensor_img, spec, debug_json)
