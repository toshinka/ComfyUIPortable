import copy
import json
import logging
from typing import Dict, Any, Tuple, Optional, List, Set

import torch
import numpy as np
from PIL import Image, ImageDraw

from .panel_layout_spec import (
    get_default_panel_layout_spec,
    validate_panel_layout_spec,
    MAX_PANELS
)
from .panel_layout_topology import build_edge_incidence


def render_panel_layout_image(
    spec: Dict[str, Any],
    line_thickness: int = 4
) -> Image.Image:
    """
    ControlNet Layout 用の純粋な漫画コマ割り画像を生成する。
    トポロジー正本仕様 (Unique Edge Traversal):
    - Canonical Unique Edge Table から各辺を厳密に 1 回だけ描画
    - 背景: 純白 (255, 255, 255)
    - コマ線: 純黒 (0, 0, 0)
    - 文字・コマ番号・色は一切描画しない
    """
    W = spec["canvas"]["width"]
    H = spec["canvas"]["height"]

    img = Image.new("RGB", (W, H), (255, 255, 255))
    draw = ImageDraw.Draw(img)

    v_map = {v["id"]: (int(round(v["x"] * W)), int(round(v["y"] * H))) for v in spec["vertices"]}

    # Canonical Unique Edge Table の構築
    incidence = build_edge_incidence(spec["panels"])

    for (v1_id, v2_id) in incidence.keys():
        if v1_id in v_map and v2_id in v_map:
            p1 = v_map[v1_id]
            p2 = v_map[v2_id]
            draw.line([p1, p2], fill=(0, 0, 0), width=int(line_thickness), joint="miter")

    return img


class TegakiMangaPanelLayoutEditor:
    """
    Tegaki Manga Panel Layout Editor (Phase 3C.1.1 Hardened)
    漫画コマ割り（Panel Layout）専用の幾何エディターノード。
    Planar Subdivision (平面分割) 契約に基づき、
    Canonical Unique-Edge レンダリングで ControlNet 向け白黒枠線画像を出力する。
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
                # Valid JSON だがスキーマ/トポロジー不正の場合は fail-closed
                spec = validate_panel_layout_spec(raw_spec, context_name="TegakiMangaPanelLayoutEditor")

        if spec is None:
            spec = get_default_panel_layout_spec(canvas_width, canvas_height, preset="3_basic")

        # ウィジェットからの canvas 寸法同期
        spec["canvas"]["width"] = int(canvas_width)
        spec["canvas"]["height"] = int(canvas_height)
        spec = validate_panel_layout_spec(spec, context_name="TegakiMangaPanelLayoutEditor")

        # 1. Unique-Edge 走査による白地・黒線の純粋な ControlNet ガイド画像
        pil_img = render_panel_layout_image(spec, line_thickness=int(line_thickness))
        np_img = np.array(pil_img).astype(np.float32) / 255.0
        tensor_img = torch.from_numpy(np_img).unsqueeze(0)  # [1, H, W, 3]

        debug_json = json.dumps(spec, indent=2, ensure_ascii=False)
        return (tensor_img, spec, debug_json)
