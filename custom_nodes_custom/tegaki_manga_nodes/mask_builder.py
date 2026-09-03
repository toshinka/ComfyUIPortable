import json
import logging
import torch
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from typing import Dict, Any, List, Optional, Tuple

from .scene_spec import validate_page_compile_plan, MIN_RECT_SIZE

# キャラクター識別用の視覚的パレット (ふたば茶系・セマンティック対応)
CHAR_PALETTE = [
    {"name": "Alice / Blue", "hex": "#3b82f6", "rgb": (59, 130, 246), "fill": (59, 130, 246, 70)},
    {"name": "Bob / Orange", "hex": "#f97316", "rgb": (249, 115, 22), "fill": (249, 115, 22, 70)},
    {"name": "Carol / Green", "hex": "#10b981", "rgb": (16, 185, 129), "fill": (16, 185, 129, 70)},
    {"name": "Dave / Purple", "hex": "#8b5cf6", "rgb": (139, 92, 246), "fill": (139, 92, 246, 70)},
    {"name": "Eve / Rose", "hex": "#f43f5e", "rgb": (244, 63, 94), "fill": (244, 63, 94, 70)},
    {"name": "Frank / Teal", "hex": "#14b8a6", "rgb": (20, 184, 166), "fill": (20, 184, 166, 70)},
]


class TegakiMangaMaskBuilder:
    """
    Tegaki Manga Mask Builder (Phase 3B)
    PAGE_COMPILE_PLAN を受け取り、KOMA Mask および Character Local Area を Page 座標へ投影した
    Pixel Mask Batch と視覚的 Mask Preview 画像を生成する。
    """
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "page_compile_plan": ("PAGE_COMPILE_PLAN",),
            }
        }

    RETURN_TYPES = ("MASK", "MASK", "IMAGE", "STRING")
    RETURN_NAMES = ("panel_masks", "character_masks", "mask_preview", "debug_json")
    FUNCTION = "build_masks"
    CATEGORY = "tegaki/manga"

    def build_masks(self, page_compile_plan: Any) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor, str]:
        plan = validate_page_compile_plan(page_compile_plan)
        canvas = plan["canvas"]
        width = int(canvas["width"])
        height = int(canvas["height"])
        panels = plan.get("panels", [])

        # 1. Panel Masks の構築
        num_panels = len(panels)
        if num_panels == 0:
            panel_masks_tensor = torch.zeros((1, height, width), dtype=torch.float32)
        else:
            panel_masks_tensor = torch.zeros((num_panels, height, width), dtype=torch.float32)

        panel_meta = []
        character_meta = []
        all_char_entries = []

        for p_idx, p in enumerate(panels):
            p_id = p["target_panel_id"]
            p_geom = p["panel"]["geometry"]
            kx, ky, kw, kh = float(p_geom["x"]), float(p_geom["y"]), float(p_geom["w"]), float(p_geom["h"])

            px0 = max(0, min(width, int(round(kx * width))))
            py0 = max(0, min(height, int(round(ky * height))))
            px1 = max(0, min(width, int(round((kx + kw) * width))))
            py1 = max(0, min(height, int(round((ky + kh) * height))))

            if num_panels > 0 and px1 > px0 and py1 > py0:
                panel_masks_tensor[p_idx, py0:py1, px0:px1] = 1.0

            panel_meta.append({
                "panel_id": p_id,
                "index": p_idx,
                "geometry": {"x": kx, "y": ky, "w": kw, "h": kh},
                "pixel_bounds": [px0, py0, px1, py1]
            })

            # KOMA内のキャラクターを収集
            for c in p.get("characters", []):
                all_char_entries.append({
                    "panel_id": p_id,
                    "panel_geom": (kx, ky, kw, kh),
                    "character": c
                })

        # 2. Character Masks の構築 (Page座標への投影)
        num_chars = len(all_char_entries)
        if num_chars == 0:
            # キャラクターが存在しない場合はダミーの全ゼロマスク
            char_masks_tensor = torch.zeros((1, height, width), dtype=torch.float32)
        else:
            char_masks_tensor = torch.zeros((num_chars, height, width), dtype=torch.float32)

        for c_idx, item in enumerate(all_char_entries):
            p_id = item["panel_id"]
            kx, ky, kw, kh = item["panel_geom"]
            c = item["character"]
            cid = c.get("character_id")
            cname = c.get("name", cid)
            area = c.get("area")

            # area = None の場合、指示書第12項に従い当該KOMA全体領域を採用
            if area is None:
                cx, cy, cw, ch = 0.0, 0.0, 1.0, 1.0
                is_unconstrained = True
            else:
                cx, cy, cw, ch = float(area["x"]), float(area["y"]), float(area["w"]), float(area["h"])
                is_unconstrained = False

            # Page 座標への投影 (指示書第11項)
            page_x = kx + kw * cx
            page_y = ky + kh * cy
            page_w = kw * cw
            page_h = kh * ch

            c_px0 = max(0, min(width, int(round(page_x * width))))
            c_py0 = max(0, min(height, int(round(page_y * height))))
            c_px1 = max(0, min(width, int(round((page_x + page_w) * width))))
            c_py1 = max(0, min(height, int(round((page_y + page_h) * height))))

            if num_chars > 0 and c_px1 > c_px0 and c_py1 > c_py0:
                char_masks_tensor[c_idx, c_py0:c_py1, c_px0:c_px1] = 1.0

            character_meta.append({
                "character_id": cid,
                "character_name": cname,
                "panel_id": p_id,
                "index": c_idx,
                "is_unconstrained": is_unconstrained,
                "koma_local_area": {"x": cx, "y": cy, "w": cw, "h": ch} if not is_unconstrained else None,
                "page_projected_area": {
                    "x": round(page_x, 4),
                    "y": round(page_y, 4),
                    "w": round(page_w, 4),
                    "h": round(page_h, 4)
                },
                "pixel_bounds": [c_px0, c_py0, c_px1, c_py1]
            })

        # 3. 視覚的 Mask Preview 画像の生成 (指示書第14項)
        # 背景: ふたば茶系ダークグレー
        base_img = Image.new("RGBA", (width, height), (35, 30, 28, 255))
        overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw_base = ImageDraw.Draw(base_img)
        draw_overlay = ImageDraw.Draw(overlay)

        # KOMA 枠の描画
        for pm in panel_meta:
            px0, py0, px1, py1 = pm["pixel_bounds"]
            pid = pm["panel_id"]
            # コマ枠線 (薄いベージュ)
            draw_base.rectangle([px0, py0, px1, py1], outline=(180, 165, 150, 255), width=3)
            # コマラベル
            draw_base.text((px0 + 8, py0 + 8), f"KOMA {pid}", fill=(220, 210, 195, 255))

        # Character 領域の描画 (カラーオーバーレイ)
        for cm in character_meta:
            c_px0, c_py0, c_px1, c_py1 = cm["pixel_bounds"]
            c_idx = cm["index"]
            cname = cm["character_name"]
            pid = cm["panel_id"]
            color_info = CHAR_PALETTE[c_idx % len(CHAR_PALETTE)]

            # 塗りつぶし (半透明)
            draw_overlay.rectangle([c_px0, c_py0, c_px1, c_py1], fill=color_info["fill"], outline=color_info["rgb"], width=2)
            # キャラクターラベル
            label = f"K{pid}:{cname}"
            if cm["is_unconstrained"]:
                label += " (Full)"
            draw_overlay.text((c_px0 + 6, c_py0 + 6), label, fill=(255, 255, 255, 230))

        # 合成
        combined_img = Image.alpha_composite(base_img, overlay).convert("RGB")
        img_np = np.array(combined_img).astype(np.float32) / 255.0
        mask_preview_tensor = torch.from_numpy(img_np).unsqueeze(0)  # (1, H, W, 3)

        debug_data = {
            "canvas": {"width": width, "height": height},
            "panels_count": num_panels,
            "characters_count": num_chars,
            "panels": panel_meta,
            "characters": character_meta
        }
        debug_json = json.dumps(debug_data, indent=2, ensure_ascii=False)

        return (panel_masks_tensor, char_masks_tensor, mask_preview_tensor, debug_json)
