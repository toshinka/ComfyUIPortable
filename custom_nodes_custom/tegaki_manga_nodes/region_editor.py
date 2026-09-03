import json
import logging
import torch
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# KOMA 1〜6 の統一カラーパレット (RGB & Hex)
KOMA_COLORS = [
    {"name": "KOMA 1", "hex": "#E53935", "rgb": (229, 57, 53)},    # Red
    {"name": "KOMA 2", "hex": "#1E88E5", "rgb": (30, 136, 229)},   # Blue
    {"name": "KOMA 3", "hex": "#43A047", "rgb": (67, 160, 71)},    # Green
    {"name": "KOMA 4", "hex": "#FB8C00", "rgb": (251, 140, 0)},    # Amber/Orange
    {"name": "KOMA 5", "hex": "#8E24AA", "rgb": (142, 36, 170)},   # Purple
    {"name": "KOMA 6", "hex": "#00ACC1", "rgb": (0, 172, 193)},    # Cyan
]

def default_region_spec(width=832, height=1216, panel_count=3, global_prompt=""):
    """
    初期状態の REGION_SPEC (v1) を生成する
    """
    # 典型的な3コマ漫画レイアウトの初期配置
    default_layouts = [
        {"id": 1, "x": 0.06, "y": 0.05, "w": 0.88, "h": 0.28, "prompt": ""},
        {"id": 2, "x": 0.06, "y": 0.36, "w": 0.42, "h": 0.58, "prompt": ""},
        {"id": 3, "x": 0.52, "y": 0.36, "w": 0.42, "h": 0.58, "prompt": ""},
        {"id": 4, "x": 0.06, "y": 0.05, "w": 0.88, "h": 0.20, "prompt": ""},
        {"id": 5, "x": 0.06, "y": 0.28, "w": 0.88, "h": 0.20, "prompt": ""},
        {"id": 6, "x": 0.06, "y": 0.51, "w": 0.88, "h": 0.43, "prompt": ""},
    ]

    regions = []
    for i in range(6):
        c = KOMA_COLORS[i]
        layout = default_layouts[i]
        regions.append({
            "id": i + 1,
            "name": c["name"],
            "enabled": (i < panel_count),
            "x": layout["x"],
            "y": layout["y"],
            "w": layout["w"],
            "h": layout["h"],
            "prompt": layout["prompt"],
            "color": c["hex"],
        })

    return {
        "version": 1,
        "canvas": {
            "width": width,
            "height": height
        },
        "panel_count": panel_count,
        "global_prompt": global_prompt,
        "regions": regions
    }


def render_preview_image(spec: dict, width: int, height: int) -> torch.Tensor:
    """
    REGION_SPEC からプレビュー画像テンソル [1, H, W, 3] を生成する
    """
    # 白背景（漫画原稿用紙）
    img = Image.new("RGBA", (width, height), (250, 248, 245, 255))
    draw = ImageDraw.Draw(img)

    # 外枠ガイド線 (原稿マージン)
    draw.rectangle([10, 10, width - 10, height - 10], outline=(200, 195, 185, 255), width=2)

    regions = spec.get("regions", [])
    panel_count = spec.get("panel_count", len(regions))

    # 各Regionを描画
    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)

    for r in regions:
        if not r.get("enabled", True):
            continue
        rid = r.get("id", 1)
        if rid > panel_count:
            continue

        rx = int(r.get("x", 0.0) * width)
        ry = int(r.get("y", 0.0) * height)
        rw = int(r.get("w", 0.1) * width)
        rh = int(r.get("h", 0.1) * height)

        color_info = KOMA_COLORS[(rid - 1) % len(KOMA_COLORS)]
        rgb = color_info["rgb"]

        # 半透明の塗りつぶし (alpha=70)
        overlay_draw.rectangle([rx, ry, rx + rw, ry + rh], fill=(rgb[0], rgb[1], rgb[2], 75))
        # 太い枠線 (alpha=220)
        overlay_draw.rectangle([rx, ry, rx + rw, ry + rh], outline=(rgb[0], rgb[1], rgb[2], 220), width=4)

        # ラベル描画（KOMA番号 + プロンプト抜粋）
        prompt_snippet = (r.get("prompt", "") or "").strip()
        if prompt_snippet:
            label = f"KOMA {rid}: {prompt_snippet[:24]}..."
        else:
            label = f"KOMA {rid}"

        # ラベル背景バッジ
        badge_w = min(rw - 8, max(80, len(label) * 9))
        badge_h = 24
        overlay_draw.rectangle([rx + 4, ry + 4, rx + 4 + badge_w, ry + 4 + badge_h], fill=(rgb[0], rgb[1], rgb[2], 230))
        overlay_draw.text((rx + 8, ry + 8), label, fill=(255, 255, 255, 255))

    # 合成
    img = Image.alpha_composite(img, overlay).convert("RGB")

    # PyTorch Tensor [1, H, W, 3] (float32, 0.0〜1.0) に変換
    arr = np.array(img).astype(np.float32) / 255.0
    tensor = torch.from_numpy(arr).unsqueeze(0)
    return tensor


def render_mask_batch(spec: dict, width: int, height: int) -> torch.Tensor:
    """
    有効な各Regionのバイナリマスク [N, H, W] を生成する
    """
    masks = []
    regions = spec.get("regions", [])
    panel_count = spec.get("panel_count", len(regions))

    for r in regions:
        if not r.get("enabled", True):
            continue
        rid = r.get("id", 1)
        if rid > panel_count:
            continue

        rx = int(r.get("x", 0.0) * width)
        ry = int(r.get("y", 0.0) * height)
        rw = int(r.get("w", 0.1) * width)
        rh = int(r.get("h", 0.1) * height)

        mask_img = Image.new("L", (width, height), 0)
        draw = ImageDraw.Draw(mask_img)
        draw.rectangle([rx, ry, rx + rw, ry + rh], fill=255)

        arr = np.array(mask_img).astype(np.float32) / 255.0
        masks.append(torch.from_numpy(arr))

    if not masks:
        # 空の場合は全画面白マスクを1枚返す
        return torch.ones((1, height, width), dtype=torch.float32)

    return torch.stack(masks, dim=0)


class TegakiMangaRegionEditor:
    """
    Tegaki Manga Region Editor (Phase 2)
    最大6コマの漫画レイアウトを視覚的に編集し、REGION_SPEC およびプレビュー画像を出力するノード。
    UIと生成Backendを完全分離したアーキテクチャを持ち、将来の外部GUIやMCWWにも対応します。
    """
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "panel_count": ("INT", {"default": 3, "min": 1, "max": 6, "step": 1}),
                "canvas_width": ("INT", {"default": 832, "min": 256, "max": 4096, "step": 64}),
                "canvas_height": ("INT", {"default": 1216, "min": 256, "max": 4096, "step": 64}),
                "global_prompt": ("STRING", {
                    "multiline": True,
                    "dynamicPrompts": True,
                    "default": "manga page, monochrome, highly detailed, ink lineart, cinematic lighting"
                }),
                "region_spec_data": ("STRING", {
                    "multiline": True,
                    "default": "{}"
                }),
            }
        }

    RETURN_TYPES = ("REGION_SPEC", "STRING", "STRING", "IMAGE", "MASK")
    RETURN_NAMES = ("region_spec", "region_spec_json", "global_prompt", "preview_image", "mask_batch")
    FUNCTION = "execute_editor"
    CATEGORY = "tegaki/manga"

    def execute_editor(self, panel_count, canvas_width, canvas_height, global_prompt, region_spec_data="{}"):
        spec = None
        # 保存されたJSONデータのパースを試行
        if region_spec_data and region_spec_data.strip() not in ("{}", ""):
            try:
                parsed = json.loads(region_spec_data)
                if isinstance(parsed, dict) and "regions" in parsed:
                    spec = parsed
            except Exception as e:
                logging.warning(f"[TegakiRegionEditor] Failed to parse region_spec_data: {e}. Generating default spec.")

        # デフォルトSpecの生成
        if spec is None:
            spec = default_region_spec(canvas_width, canvas_height, panel_count, global_prompt)
        else:
            # 入力引数との同期
            spec["panel_count"] = panel_count
            spec["canvas"]["width"] = canvas_width
            spec["canvas"]["height"] = canvas_height
            spec["global_prompt"] = global_prompt

        # Region Prompt内の <lora:...> をチェック（Phase 2注意喚起: 指示書第24項）
        for r in spec.get("regions", []):
            p = r.get("prompt", "")
            if "<lora:" in p.lower():
                logging.warning(
                    f"[TegakiRegionEditor] Notice: KOMA {r.get('id')} prompt contains '<lora:...>'. "
                    "Region-local LoRA is planned for Phase 5 (RLL). Currently LoRA affects the entire model."
                )

        spec_json = json.dumps(spec, indent=2, ensure_ascii=False)
        preview_img = render_preview_image(spec, canvas_width, canvas_height)
        mask_batch = render_mask_batch(spec, canvas_width, canvas_height)

        return (spec, spec_json, global_prompt, preview_img, mask_batch)
