import json
import logging
import torch
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
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

# Local Region 用の視覚的パレット (シアン / エメラルド系)
LOCAL_REGION_PALETTE = [
    {"name": "Local Cyan", "hex": "#06b6d4", "rgb": (6, 182, 212), "fill": (6, 182, 212, 60)},
    {"name": "Local Emerald", "hex": "#10b981", "rgb": (16, 185, 129), "fill": (16, 185, 129, 60)},
    {"name": "Local Amber", "hex": "#f59e0b", "rgb": (245, 158, 11), "fill": (245, 158, 11, 60)},
    {"name": "Local Indigo", "hex": "#6366f1", "rgb": (99, 102, 241), "fill": (99, 102, 241, 60)},
]


def _apply_feather(mask_tensor: torch.Tensor, radius: int) -> torch.Tensor:
    """
    マスクテンソル [B, H, W] の境界をガウシアンブラーでフェザー（ぼかし）処理する
    """
    if radius <= 0:
        return mask_tensor
    B, H, W = mask_tensor.shape
    feathered = torch.zeros_like(mask_tensor)
    for i in range(B):
        arr = (mask_tensor[i].cpu().numpy() * 255.0).astype(np.uint8)
        img = Image.fromarray(arr, mode="L")
        blurred = img.filter(ImageFilter.GaussianBlur(radius=radius))
        feathered[i] = torch.from_numpy(np.array(blurred).astype(np.float32) / 255.0)
    return feathered


class TegakiMangaMaskBuilder:
    """
    Tegaki Manga Mask Builder (Phase 3B / 3B.1)
    PAGE_COMPILE_PLAN を受け取り、
    1. Panel Masks (N枚)
    2. Character Masks (M枚, Page座標投影)
    3. Local Region Masks (L枚, Page座標投影, Phase 3B.1新設)
    4. Mask Preview 画像 (オーバーレイ可視化)
    5. Debug JSON
    を生成する。
    """
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "page_compile_plan": ("PAGE_COMPILE_PLAN",),
            },
            "optional": {
                "mask_feather": ("INT", {"default": 0, "min": 0, "max": 64, "step": 1}),
            }
        }

    RETURN_TYPES = ("MASK", "MASK", "IMAGE", "STRING", "MASK")
    RETURN_NAMES = ("panel_masks", "character_masks", "mask_preview", "debug_json", "local_region_masks")
    FUNCTION = "build_masks"
    CATEGORY = "tegaki/manga"

    def build_masks(self, page_compile_plan: Any, mask_feather: int = 0) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, str]:
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
        all_lr_entries = []

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

            # KOMA内の Local Region を収集 (Phase 3B.1)
            for lr in p.get("panel", {}).get("local_regions", []):
                all_lr_entries.append({
                    "panel_id": p_id,
                    "panel_geom": (kx, ky, kw, kh),
                    "local_region": lr
                })

        # 2. Character Masks の構築 (Page座標への投影)
        num_chars = len(all_char_entries)
        if num_chars == 0:
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

            if area is None:
                cx, cy, cw, ch = 0.0, 0.0, 1.0, 1.0
                is_unconstrained = True
            else:
                cx, cy, cw, ch = float(area["x"]), float(area["y"]), float(area["w"]), float(area["h"])
                is_unconstrained = False

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

        # 3. Local Region Masks の構築 (Page座標への投影 - Phase 3B.1)
        num_lrs = len(all_lr_entries)
        if num_lrs == 0:
            lr_masks_tensor = torch.zeros((1, height, width), dtype=torch.float32)
        else:
            lr_masks_tensor = torch.zeros((num_lrs, height, width), dtype=torch.float32)

        local_region_meta = []
        for l_idx, item in enumerate(all_lr_entries):
            p_id = item["panel_id"]
            kx, ky, kw, kh = item["panel_geom"]
            lr = item["local_region"]
            lid = lr.get("id")
            lname = lr.get("name", lid)
            area = lr["area"]

            lx, ly, lw, lh = float(area["x"]), float(area["y"]), float(area["w"]), float(area["h"])

            lr_page_x = kx + kw * lx
            lr_page_y = ky + kh * ly
            lr_page_w = kw * lw
            lr_page_h = kh * lh

            lr_px0 = max(0, min(width, int(round(lr_page_x * width))))
            lr_py0 = max(0, min(height, int(round(lr_page_y * height))))
            lr_px1 = max(0, min(width, int(round((lr_page_x + lr_page_w) * width))))
            lr_py1 = max(0, min(height, int(round((lr_page_y + lr_page_h) * height))))

            if num_lrs > 0 and lr_px1 > lr_px0 and lr_py1 > lr_py0:
                lr_masks_tensor[l_idx, lr_py0:lr_py1, lr_px0:lr_px1] = 1.0

            local_region_meta.append({
                "id": lid,
                "name": lname,
                "panel_id": p_id,
                "index": l_idx,
                "koma_local_area": {"x": lx, "y": ly, "w": lw, "h": lh},
                "page_projected_area": {
                    "x": round(lr_page_x, 4),
                    "y": round(lr_page_y, 4),
                    "w": round(lr_page_w, 4),
                    "h": round(lr_page_h, 4)
                },
                "pixel_bounds": [lr_px0, lr_py0, lr_px1, lr_py1]
            })

        # 4. フェザー処理 (mask_feather > 0 の場合)
        if mask_feather > 0:
            if num_panels > 0:
                panel_masks_tensor = _apply_feather(panel_masks_tensor, mask_feather)
            if num_chars > 0:
                char_masks_tensor = _apply_feather(char_masks_tensor, mask_feather)
            if num_lrs > 0:
                lr_masks_tensor = _apply_feather(lr_masks_tensor, mask_feather)

        # 5. 視覚的 Mask Preview 画像の生成 (KOMA + Local Region + Character オーバーレイ)
        base_img = Image.new("RGBA", (width, height), (35, 30, 28, 255))
        overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw_base = ImageDraw.Draw(base_img)
        draw_overlay = ImageDraw.Draw(overlay)

        # KOMA 枠の描画
        for pm in panel_meta:
            px0, py0, px1, py1 = pm["pixel_bounds"]
            pid = pm["panel_id"]
            draw_base.rectangle([px0, py0, px1, py1], outline=(180, 165, 150, 255), width=3)
            draw_base.text((px0 + 8, py0 + 8), f"KOMA {pid}", fill=(220, 210, 195, 255))

        # Local Region 領域の描画 (シアン系オーバーレイ)
        for lm in local_region_meta:
            l_px0, l_py0, l_px1, l_py1 = lm["pixel_bounds"]
            l_idx = lm["index"]
            lname = lm["name"]
            pid = lm["panel_id"]
            color_info = LOCAL_REGION_PALETTE[l_idx % len(LOCAL_REGION_PALETTE)]

            draw_overlay.rectangle([l_px0, l_py0, l_px1, l_py1], fill=color_info["fill"], outline=color_info["rgb"], width=2)
            label = f"K{pid}:L:{lname}"
            draw_overlay.text((l_px0 + 4, l_py0 + 4), label, fill=(180, 240, 255, 230))

        # Character 領域の描画 (カラーオーバーレイ)
        for cm in character_meta:
            c_px0, c_py0, c_px1, c_py1 = cm["pixel_bounds"]
            c_idx = cm["index"]
            cname = cm["character_name"]
            pid = cm["panel_id"]
            color_info = CHAR_PALETTE[c_idx % len(CHAR_PALETTE)]

            draw_overlay.rectangle([c_px0, c_py0, c_px1, c_py1], fill=color_info["fill"], outline=color_info["rgb"], width=2)
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
            "local_regions_count": num_lrs,
            "mask_feather": mask_feather,
            "panels": panel_meta,
            "characters": character_meta,
            "local_regions": local_region_meta
        }
        debug_json = json.dumps(debug_data, indent=2, ensure_ascii=False)

        return (panel_masks_tensor, char_masks_tensor, mask_preview_tensor, debug_json, lr_masks_tensor)
