import json
from typing import Dict, Any, Tuple

import torch
import numpy as np
from PIL import Image, ImageDraw

from .two_region_spec import validate_two_region_spec


class TegakiTwoRegionLayoutGuide:
    """
    Tegaki Two Region Layout Guide (Phase 3C Oracle)
    TWO_REGION_SPEC から ControlNet (Scribble/Lineart/Canny/Inpaint) 向けに
    パネル外枠線 (Panel Outline) や矩形ブロックガイド画像を自動生成する補助ノード。
    """
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "two_region_spec": ("TWO_REGION_SPEC",),
                "mode": (["Panel Outline (White on Black)", "Panel Outline (Black on White)", "Binary Mask Block", "Color Block (RGB)"], {"default": "Panel Outline (White on Black)"}),
                "line_thickness": ("INT", {"default": 4, "min": 1, "max": 32, "step": 1}),
            }
        }

    RETURN_TYPES = ("IMAGE", "MASK", "STRING")
    RETURN_NAMES = ("guide_image", "combined_mask", "debug_json")
    FUNCTION = "generate_guide"
    CATEGORY = "tegaki/manga/oracle"

    def generate_guide(
        self,
        two_region_spec: Any,
        mode: str = "Panel Outline (White on Black)",
        line_thickness: int = 4
    ) -> Tuple[torch.Tensor, torch.Tensor, str]:
        spec = validate_two_region_spec(two_region_spec)
        W = spec["canvas"]["width"]
        H = spec["canvas"]["height"]

        combined_mask = torch.zeros((1, H, W), dtype=torch.float32)

        if mode == "Panel Outline (White on Black)":
            bg_color = (0, 0, 0)
            img = Image.new("RGB", (W, H), bg_color)
            draw = ImageDraw.Draw(img)
            stroke_A = (255, 255, 255)
            stroke_B = (255, 255, 255)
            fill_A = None
            fill_B = None
        elif mode == "Panel Outline (Black on White)":
            bg_color = (255, 255, 255)
            img = Image.new("RGB", (W, H), bg_color)
            draw = ImageDraw.Draw(img)
            stroke_A = (0, 0, 0)
            stroke_B = (0, 0, 0)
            fill_A = None
            fill_B = None
        elif mode == "Binary Mask Block":
            bg_color = (0, 0, 0)
            img = Image.new("RGB", (W, H), bg_color)
            draw = ImageDraw.Draw(img)
            stroke_A = (255, 255, 255)
            stroke_B = (255, 255, 255)
            fill_A = (255, 255, 255)
            fill_B = (255, 255, 255)
        else:  # Color Block (RGB)
            bg_color = (30, 30, 30)
            img = Image.new("RGB", (W, H), bg_color)
            draw = ImageDraw.Draw(img)
            stroke_A = (0, 150, 255)
            stroke_B = (255, 120, 0)
            fill_A = (0, 100, 220)
            fill_B = (220, 90, 0)

        for reg in spec["regions"]:
            if not reg.get("enabled", True):
                continue
            rid = reg["id"]
            rx = int(round(reg["x"] * W))
            ry = int(round(reg["y"] * H))
            rw = int(round(reg["w"] * W))
            rh = int(round(reg["h"] * H))

            x0 = max(0, min(W, rx))
            y0 = max(0, min(H, ry))
            x1 = max(0, min(W, rx + rw))
            y1 = max(0, min(H, ry + rh))

            if x1 > x0 and y1 > y0:
                combined_mask[0, y0:y1, x0:x1] = 1.0
                fill = fill_A if rid == "A" else fill_B
                stroke = stroke_A if rid == "A" else stroke_B
                draw.rectangle([x0, y0, x1, y1], fill=fill, outline=stroke, width=line_thickness)

        np_img = np.array(img).astype(np.float32) / 255.0
        tensor_img = torch.from_numpy(np_img).unsqueeze(0)

        debug_info = {
            "mode": mode,
            "line_thickness": line_thickness,
            "canvas": {"width": W, "height": H},
            "active_regions": [r["id"] for r in spec["regions"] if r.get("enabled", True)]
        }

        return (tensor_img, combined_mask, json.dumps(debug_info, indent=2, ensure_ascii=False))
