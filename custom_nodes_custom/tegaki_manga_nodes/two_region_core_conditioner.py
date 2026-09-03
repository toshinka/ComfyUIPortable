import json
import logging
import math
from typing import Dict, Any, Tuple, Optional

import numpy as np
import torch
import node_helpers
from PIL import Image, ImageFilter

from .two_region_spec import validate_two_region_spec


def apply_gaussian_feather(mask: torch.Tensor, feather_px: int) -> torch.Tensor:
    """
    マスク境界にガウシアンブラーを適用してフェザー処理を行う。
    mask: (1, H, W) float32 (0.0 or 1.0)
    """
    if feather_px <= 0:
        return mask
    H, W = mask.shape[1], mask.shape[2]
    np_mask = (mask[0].cpu().numpy() * 255.0).astype("uint8")
    pil_img = Image.fromarray(np_mask, mode="L")
    radius = float(feather_px) / 2.0
    blurred_img = pil_img.filter(ImageFilter.GaussianBlur(radius=radius))
    blurred_arr = np.array(blurred_img, dtype=np.float32) / 255.0
    return torch.from_numpy(blurred_arr).unsqueeze(0)


class TegakiTwoRegionCoreConditioner:
    """
    Tegaki Two Region Core Conditioner (Phase 3C Oracle)
    TWO_REGION_SPEC と CLIP を受け取り、ComfyUI Core API に準拠して
    - Global Positive / Negative (全体・マスクなし)
    - Region A Positive / Negative (Mask A 付き)
    - Region B Positive / Negative (Mask B 付き)
    を最短経路で構築・結合した Conditioning を生成する。
    """
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "clip": ("CLIP",),
                "two_region_spec": ("TWO_REGION_SPEC",),
            },
            "optional": {
                "strength_A": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 2.0, "step": 0.05}),
                "strength_B": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 2.0, "step": 0.05}),
                "set_cond_area": (["default", "mask bounds"], {"default": "default"}),
                "mask_feather": ("INT", {"default": 0, "min": 0, "max": 64, "step": 1}),
            }
        }

    RETURN_TYPES = ("CONDITIONING", "CONDITIONING", "MASK", "MASK", "STRING")
    RETURN_NAMES = ("positive", "negative", "mask_A", "mask_B", "debug_json")
    FUNCTION = "build_conditioning"
    CATEGORY = "tegaki/manga/oracle"

    def _encode_text(self, clip: Any, text: str):
        if clip is None:
            raise RuntimeError("[TegakiTwoRegionCoreConditioner] CLIP input is None.")
        tokens = clip.tokenize(text if text is not None else "")
        return clip.encode_from_tokens_scheduled(tokens)

    def _apply_mask(self, cond: Any, mask: torch.Tensor, strength: float, set_cond_area: str):
        set_area_to_bounds = (set_cond_area != "default")
        if len(mask.shape) < 3:
            mask = mask.unsqueeze(0)
        return node_helpers.conditioning_set_values(
            cond,
            {
                "mask": mask,
                "set_area_to_bounds": set_area_to_bounds,
                "mask_strength": float(strength)
            }
        )

    def build_conditioning(
        self,
        clip: Any,
        two_region_spec: Any,
        strength_A: float = 1.0,
        strength_B: float = 1.0,
        set_cond_area: str = "default",
        mask_feather: int = 0
    ) -> Tuple[Any, Any, torch.Tensor, torch.Tensor, str]:
        # 1. 有限値検証
        for name, val in [("strength_A", strength_A), ("strength_B", strength_B)]:
            if val is None or not math.isfinite(float(val)):
                raise ValueError(f"[TegakiTwoRegionCoreConditioner] '{name}' must be a finite float, got {val!r}")

        spec = validate_two_region_spec(two_region_spec)
        W = spec["canvas"]["width"]
        H = spec["canvas"]["height"]

        # 2. マスクの生成
        mask_A = torch.zeros((1, H, W), dtype=torch.float32)
        mask_B = torch.zeros((1, H, W), dtype=torch.float32)

        prompt_map = {"A": "", "B": ""}
        neg_prompt_map = {"A": "", "B": ""}
        enabled_map = {"A": False, "B": False}

        for reg in spec["regions"]:
            rid = reg["id"]
            enabled = reg.get("enabled", True)
            enabled_map[rid] = enabled
            prompt_map[rid] = reg.get("prompt", "")
            neg_prompt_map[rid] = reg.get("negative_prompt", "")

            if not enabled:
                continue

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

        # フェザー処理
        if mask_feather > 0:
            if enabled_map["A"]: mask_A = apply_gaussian_feather(mask_A, mask_feather)
            if enabled_map["B"]: mask_B = apply_gaussian_feather(mask_B, mask_feather)

        # 3. Conditioning 構築
        global_p = spec.get("global_prompt", "")
        global_n = spec.get("global_negative_prompt", "")

        pos_conditioning = []
        neg_conditioning = []

        # (a) Global Conditioning (unmasked)
        global_pos_cond = self._encode_text(clip, global_p)
        global_neg_cond = self._encode_text(clip, global_n)
        pos_conditioning.extend(global_pos_cond)
        neg_conditioning.extend(global_neg_cond)

        debug_branches = [
            {"scope": "Global", "prompt": global_p, "masked": False}
        ]

        # (b) Region A Conditioning (masked)
        if enabled_map["A"] and prompt_map["A"].strip():
            p_A = prompt_map["A"].strip()
            cond_A = self._encode_text(clip, p_A)
            masked_cond_A = self._apply_mask(cond_A, mask_A, strength_A, set_cond_area)
            pos_conditioning.extend(masked_cond_A)
            debug_branches.append({"scope": "Region A", "prompt": p_A, "masked": True, "strength": strength_A})

            if neg_prompt_map["A"].strip():
                n_A = neg_prompt_map["A"].strip()
                cond_neg_A = self._encode_text(clip, n_A)
                masked_neg_A = self._apply_mask(cond_neg_A, mask_A, strength_A, set_cond_area)
                neg_conditioning.extend(masked_neg_A)

        # (c) Region B Conditioning (masked)
        if enabled_map["B"] and prompt_map["B"].strip():
            p_B = prompt_map["B"].strip()
            cond_B = self._encode_text(clip, p_B)
            masked_cond_B = self._apply_mask(cond_B, mask_B, strength_B, set_cond_area)
            pos_conditioning.extend(masked_cond_B)
            debug_branches.append({"scope": "Region B", "prompt": p_B, "masked": True, "strength": strength_B})

            if neg_prompt_map["B"].strip():
                n_B = neg_prompt_map["B"].strip()
                cond_neg_B = self._encode_text(clip, n_B)
                masked_neg_B = self._apply_mask(cond_neg_B, mask_B, strength_B, set_cond_area)
                neg_conditioning.extend(masked_neg_B)

        debug_info = {
            "total_positive_branches": len(pos_conditioning),
            "total_negative_branches": len(neg_conditioning),
            "branches": debug_branches,
            "mask_feather": mask_feather,
            "set_cond_area": set_cond_area,
            "spec": spec
        }

        return (pos_conditioning, neg_conditioning, mask_A, mask_B, json.dumps(debug_info, indent=2, ensure_ascii=False))
