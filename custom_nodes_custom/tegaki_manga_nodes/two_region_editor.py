import copy
import json
import logging
import math
from typing import Dict, Any, Tuple, Optional

import torch
import numpy as np
from PIL import Image, ImageDraw

from .two_region_spec import get_default_two_region_spec, validate_two_region_spec


class TegakiTwoRegionCoupleEditor:
    """
    Tegaki Two Region Couple Editor (Phase 3C.1 Hardened Oracle)
    2領域 (Region A / Region B) に特化した視覚的 Rectangle Editor ノード。
    Semantic Overlap（約35%重なり）を基本思想とし、
    TWO_REGION_SPEC、Mask A/B、およびカラープレビュー画像を同時出力する。
    """
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "canvas_width": ("INT", {"default": 832, "min": 256, "max": 4096, "step": 64}),
                "canvas_height": ("INT", {"default": 1216, "min": 256, "max": 4096, "step": 64}),
                "global_prompt": ("STRING", {"multiline": True, "default": "masterpiece, best quality, expressive anime illustration"}),
                "global_negative_prompt": ("STRING", {"multiline": True, "default": "worst quality, low quality, bad anatomy"}),
                "prompt_A": ("STRING", {"multiline": True, "default": "1girl, blonde hair, blue eyes, smiling, light dress"}),
                "negative_prompt_A": ("STRING", {"multiline": True, "default": ""}),
                "prompt_B": ("STRING", {"multiline": True, "default": "1boy, black hair, dark jacket, standing"}),
                "negative_prompt_B": ("STRING", {"multiline": True, "default": ""}),
                "two_region_spec_data": ("STRING", {"multiline": True, "default": ""}),
            }
        }

    RETURN_TYPES = ("TWO_REGION_SPEC", "MASK", "MASK", "IMAGE", "STRING")
    RETURN_NAMES = ("two_region_spec", "mask_A", "mask_B", "combined_preview", "debug_json")
    FUNCTION = "execute_editor"
    CATEGORY = "tegaki/manga/oracle"

    def execute_editor(
        self,
        canvas_width: int,
        canvas_height: int,
        global_prompt: str,
        global_negative_prompt: str,
        prompt_A: str,
        negative_prompt_A: str,
        prompt_B: str,
        negative_prompt_B: str,
        two_region_spec_data: str = ""
    ) -> Tuple[Dict[str, Any], torch.Tensor, torch.Tensor, torch.Tensor, str]:
        # 1. Spec の復元または初期化 (fail-closed スキーマ検証)
        spec: Optional[Dict[str, Any]] = None
        if two_region_spec_data and two_region_spec_data.strip():
            try:
                raw_spec = json.loads(two_region_spec_data)
            except json.JSONDecodeError as e:
                logging.warning(f"[TegakiTwoRegionCoupleEditor] Fallback to default spec due to JSON syntax error: {e}")
                raw_spec = None

            if raw_spec is not None:
                # Valid JSON だがスキーマ不正の場合は fail-closed で例外を投げる
                spec = validate_two_region_spec(raw_spec, context_name="TegakiTwoRegionCoupleEditor")

        if spec is None:
            spec = get_default_two_region_spec(canvas_width, canvas_height)

        # ウィジェットからのプロンプト・キャンバス同期 (空文字へのクリアも完全許可)
        spec["canvas"]["width"] = int(canvas_width)
        spec["canvas"]["height"] = int(canvas_height)
        spec["global_prompt"] = str(global_prompt if global_prompt is not None else "")
        spec["global_negative_prompt"] = str(global_negative_prompt if global_negative_prompt is not None else "")

        reg_map = {r["id"]: r for r in spec["regions"]}
        if "A" in reg_map:
            if prompt_A is not None:
                reg_map["A"]["prompt"] = str(prompt_A)
            if negative_prompt_A is not None:
                reg_map["A"]["negative_prompt"] = str(negative_prompt_A)
        if "B" in reg_map:
            if prompt_B is not None:
                reg_map["B"]["prompt"] = str(prompt_B)
            if negative_prompt_B is not None:
                reg_map["B"]["negative_prompt"] = str(negative_prompt_B)

        # 再検証
        spec = validate_two_region_spec(spec, context_name="TegakiTwoRegionCoupleEditor")

        W = spec["canvas"]["width"]
        H = spec["canvas"]["height"]

        # 2. Mask A, Mask B の生成 (B=1, H, W)
        mask_A = torch.zeros((1, H, W), dtype=torch.float32)
        mask_B = torch.zeros((1, H, W), dtype=torch.float32)

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
                if rid == "A":
                    mask_A[0, y0:y1, x0:x1] = 1.0
                elif rid == "B":
                    mask_B[0, y0:y1, x0:x1] = 1.0

        # 3. カラープレビュー画像 (PIL -> torch.Tensor B=1, H, W, C=3)
        # 背景: ふたば茶系 #fcfaf2 (252, 250, 242)
        preview_img = Image.new("RGB", (W, H), (252, 250, 242))
        overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)

        # Region A: 青系 #2563eb (37, 99, 235), alpha 90
        # Region B: 橙系 #ea580c (234, 88, 12), alpha 90
        color_palette = {
            "A": {"fill": (37, 99, 235, 90), "stroke": (29, 78, 216, 230)},
            "B": {"fill": (234, 88, 12, 90), "stroke": (194, 65, 12, 230)},
        }

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
                pal = color_palette.get(rid, {"fill": (100, 100, 100, 80), "stroke": (50, 50, 50, 200)})
                overlay_draw.rectangle([x0, y0, x1, y1], fill=pal["fill"], outline=pal["stroke"], width=3)
                p_snippet = reg.get("prompt", "")[:25]
                label_text = f"Region {rid}: {p_snippet}"
                overlay_draw.rectangle([x0, y0, min(x1, x0 + 260), min(y1, y0 + 26)], fill=pal["stroke"])
                overlay_draw.text((x0 + 6, y0 + 5), label_text, fill=(255, 255, 255, 255))

        preview_img.paste(Image.alpha_composite(Image.new("RGBA", (W, H), (252, 250, 242, 255)), overlay).convert("RGB"), (0, 0))

        np_img = np.array(preview_img).astype(np.float32) / 255.0
        tensor_preview = torch.from_numpy(np_img).unsqueeze(0)

        debug_json = json.dumps(spec, indent=2, ensure_ascii=False)
        return (spec, mask_A, mask_B, tensor_preview, debug_json)
