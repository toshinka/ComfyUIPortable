"""
Tegaki Manga Layout-Aware Mask Builder (Phase 3D)
==================================================
PAGE_COMPILE_PLAN と PANEL_LAYOUT_SPEC から派生した Bridge データを基に:
1. Panel Polygon Masks (N枚, Planar Subdivision多角形ラスタライズ)
2. Character Semantic Masks (M枚, BBox投影 + 多角形クリッピング, Overlap許容)
3. Local Region Masks (L枚, BBox投影 + 多角形クリッピング)
4. Mask Preview 画像 (半透明カラーオーバーレイ可視化)
5. Debug JSON
を生成する。
"""

import json
import logging
import torch
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from typing import Dict, Any, List, Optional, Tuple

from .mask_builder import CHAR_PALETTE, LOCAL_REGION_PALETTE, _apply_feather
from .layout_region_bridge import build_panel_content_bridge


def render_polygon_mask(points: List[Tuple[int, int]], width: int, height: int) -> torch.Tensor:
    """
    指定された多角形頂点から 2値マスク [H, W] (0.0 or 1.0) をラスタライズする。
    """
    img = Image.new("L", (width, height), color=0)
    draw = ImageDraw.Draw(img)
    if len(points) >= 3:
        draw.polygon(points, fill=255)
    arr = np.array(img, dtype=np.float32) / 255.0
    return torch.from_numpy(arr)


def render_rect_mask(bounds: List[int], width: int, height: int) -> torch.Tensor:
    """
    [x0, y0, x1, y1] から 2値矩形マスク [H, W] を生成する。
    """
    mask = torch.zeros((height, width), dtype=torch.float32)
    x0, y0, x1, y1 = bounds
    if x1 > x0 and y1 > y0:
        mask[y0:y1, x0:x1] = 1.0
    return mask


def build_layout_aware_masks(
    bridge_data: Dict[str, Any],
    mask_feather: int = 0
) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor, str, torch.Tensor]:
    """
    Bridge データから多角形パネルマスク、クリップされたキャラクターマスク、
    ローカルリージョンマスク、およびプレビュー画像を生成する。
    """
    canvas = bridge_data["canvas"]
    width = int(canvas["width"])
    height = int(canvas["height"])

    mapped_panels = bridge_data["mapped_panels"]
    characters = bridge_data["characters"]
    local_regions = bridge_data["local_regions"]

    num_panels = len(mapped_panels)
    num_chars = len(characters)
    num_lrs = len(local_regions)

    # 1. Panel Polygon Masks の生成 [N, H, W]
    if num_panels == 0:
        panel_masks = torch.zeros((1, height, width), dtype=torch.float32)
    else:
        panel_masks = torch.zeros((num_panels, height, width), dtype=torch.float32)
        for idx, p in enumerate(mapped_panels):
            poly_pts = p["polygon_pixels"]
            panel_masks[idx] = render_polygon_mask(poly_pts, width, height)

    # 2. Character Masks の生成 [M, H, W] (BBox投影 + Polygonクリッピング)
    if num_chars == 0:
        char_masks = torch.zeros((1, height, width), dtype=torch.float32)
    else:
        char_masks = torch.zeros((num_chars, height, width), dtype=torch.float32)
        for c_idx, c in enumerate(characters):
            p_idx = c["panel_index"]
            raw_rect_mask = render_rect_mask(c["pixel_bounds"], width, height)
            # 多角形パネルマスクによる厳格な幾何クリッピング (枠外漏出の完全防止)
            if p_idx < num_panels:
                char_masks[c_idx] = raw_rect_mask * panel_masks[p_idx]
            else:
                char_masks[c_idx] = raw_rect_mask

    # 3. Local Region Masks の生成 [L, H, W] (BBox投影 + Polygonクリッピング)
    if num_lrs == 0:
        lr_masks = torch.zeros((1, height, width), dtype=torch.float32)
    else:
        lr_masks = torch.zeros((num_lrs, height, width), dtype=torch.float32)
        for l_idx, lr in enumerate(local_regions):
            p_idx = lr["panel_index"]
            raw_rect_mask = render_rect_mask(lr["pixel_bounds"], width, height)
            if p_idx < num_panels:
                lr_masks[l_idx] = raw_rect_mask * panel_masks[p_idx]
            else:
                lr_masks[l_idx] = raw_rect_mask

    # 4. フェザー処理 (オプション)
    if mask_feather > 0:
        panel_masks = _apply_feather(panel_masks, mask_feather)
        if num_chars > 0:
            char_masks = _apply_feather(char_masks, mask_feather)
        if num_lrs > 0:
            lr_masks = _apply_feather(lr_masks, mask_feather)

    # 5. 視覚的 Mask Preview 画像の構築 (オーバーレイ描画)
    preview_img = Image.new("RGBA", (width, height), (248, 246, 240, 255))
    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw_overlay = ImageDraw.Draw(overlay)

    try:
        font = ImageFont.truetype("arial.ttf", 20)
        small_font = ImageFont.truetype("arial.ttf", 14)
    except Exception:
        font = ImageFont.load_default()
        small_font = ImageFont.load_default()

    # パネル多角形枠線の描画
    draw_base = ImageDraw.Draw(preview_img)
    for p in mapped_panels:
        pts = p["polygon_pixels"]
        if len(pts) >= 3:
            # 内側を白で抜く
            draw_base.polygon(pts, fill=(255, 255, 255, 255), outline=(40, 30, 20, 255), width=3)
            # ラベル (KOMA ID + Layout ID)
            bx, by = pts[0]
            label = f"KOMA {p['koma_id']} ({p['layout_panel_id']})"
            draw_base.text((bx + 8, by + 8), label, fill=(100, 90, 80, 255), font=small_font)

    # Local Region の半透明着色
    for l_idx, lr in enumerate(local_regions):
        pal = LOCAL_REGION_PALETTE[l_idx % len(LOCAL_REGION_PALETTE)]
        bx0, by0, bx1, by1 = lr["pixel_bounds"]
        draw_overlay.rectangle([bx0, by0, bx1, by1], fill=pal["fill"], outline=pal["rgb"], width=2)
        draw_overlay.text((bx0 + 6, by0 + 4), f"Local: {lr['name']}", fill=pal["rgb"], font=small_font)

    # Character の半透明着色 (Semantic Overlap 視覚化)
    for c_idx, c in enumerate(characters):
        pal = CHAR_PALETTE[c_idx % len(CHAR_PALETTE)]
        bx0, by0, bx1, by1 = c["pixel_bounds"]
        draw_overlay.rectangle([bx0, by0, bx1, by1], fill=pal["fill"], outline=pal["rgb"], width=2)
        draw_overlay.text((bx0 + 6, by1 - 22), f"Char: {c['character_name']}", fill=pal["rgb"], font=font)

    preview_img = Image.alpha_composite(preview_img, overlay).convert("RGB")
    preview_arr = np.array(preview_img, dtype=np.float32) / 255.0
    preview_tensor = torch.from_numpy(preview_arr).unsqueeze(0)  # [1, H, W, 3]

    # 6. Debug JSON の構築
    debug_data = {
        "canvas": {"width": width, "height": height},
        "mode": "layout_driven_polygon",
        "panel_count": num_panels,
        "character_count": num_chars,
        "local_region_count": num_lrs,
        "mask_feather": mask_feather,
        "panels": [
            {
                "koma_id": p["koma_id"],
                "layout_panel_id": p["layout_panel_id"],
                "index": p["index"],
                "polygon_norm": p["polygon_norm"],
                "bbox_norm": p["bbox_norm"],
            }
            for p in mapped_panels
        ],
        "characters": [
            {
                "character_id": c["character_id"],
                "character_name": c["character_name"],
                "koma_id": c["koma_id"],
                "layout_panel_id": c["layout_panel_id"],
                "index": c["character_index"],
                "projected_area": c["page_projected_area"],
            }
            for c in characters
        ],
        "local_regions": [
            {
                "id": lr["id"],
                "name": lr["name"],
                "koma_id": lr["koma_id"],
                "layout_panel_id": lr["layout_panel_id"],
                "index": lr["local_region_index"],
                "projected_area": lr["page_projected_area"],
            }
            for lr in local_regions
        ],
    }

    return panel_masks, char_masks, preview_tensor, json.dumps(debug_data, indent=2), lr_masks
