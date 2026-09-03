import json
import logging
from typing import Dict, Any, Tuple, List, Optional

import torch

from .two_region_spec import validate_two_region_spec


class TegakiTwoRegionImpactAdapter:
    """
    Tegaki Two Region Impact Adapter (Phase 3C Oracle)
    TWO_REGION_SPEC から Region A / Region B のマスクを抽出し、
    Impact Pack の RegionalPrompt / RegionalSampler と連携するための
    REGIONAL_PROMPTS を構築・出力するアダプターノード。
    """
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "two_region_spec": ("TWO_REGION_SPEC",),
                "sampler_A": ("KSAMPLER_ADVANCED",),
                "sampler_B": ("KSAMPLER_ADVANCED",),
            },
            "optional": {
                "variation_seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff}),
                "variation_strength": ("FLOAT", {"default": 0.0, "min": 0.0, "max": 1.0, "step": 0.01}),
                "variation_method": (["linear", "slerp"], {"default": "linear"}),
            }
        }

    RETURN_TYPES = ("REGIONAL_PROMPTS", "MASK", "MASK", "STRING")
    RETURN_NAMES = ("regional_prompts", "mask_A", "mask_B", "debug_json")
    FUNCTION = "build_impact_prompts"
    CATEGORY = "tegaki/manga/oracle"

    def build_impact_prompts(
        self,
        two_region_spec: Any,
        sampler_A: Any,
        sampler_B: Any,
        variation_seed: int = 0,
        variation_strength: float = 0.0,
        variation_method: str = "linear"
    ) -> Tuple[List[Any], torch.Tensor, torch.Tensor, str]:
        # 1. Impact Pack の動的インポート
        impact_core = None
        try:
            import impact.core as impact_core
        except ImportError:
            try:
                import importlib
                impact_pack_mod = importlib.import_module("ComfyUI-Impact-Pack.modules.impact.core")
                impact_core = impact_pack_mod
            except Exception:
                try:
                    import importlib.util
                    import os
                    pack_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "ComfyUI-Impact-Pack", "modules", "impact", "core.py"))
                    if os.path.exists(pack_path):
                        spec_imp = importlib.util.spec_from_file_location("impact_core", pack_path)
                        mod = importlib.util.module_from_spec(spec_imp)
                        spec_imp.loader.exec_module(mod)
                        impact_core = mod
                except Exception:
                    pass

        if impact_core is None:
            raise RuntimeError(
                "[TegakiTwoRegionImpactAdapter] ComfyUI-Impact-Pack is not installed or importable. "
                "Please install ComfyUI-Impact-Pack to use this adapter."
            )

        spec = validate_two_region_spec(two_region_spec)
        W = spec["canvas"]["width"]
        H = spec["canvas"]["height"]

        mask_A = torch.zeros((1, H, W), dtype=torch.float32)
        mask_B = torch.zeros((1, H, W), dtype=torch.float32)

        enabled_A = False
        enabled_B = False

        for reg in spec["regions"]:
            rid = reg["id"]
            enabled = reg.get("enabled", True)
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
                    enabled_A = True
                elif rid == "B":
                    mask_B[0, y0:y1, x0:x1] = 1.0
                    enabled_B = True

        regional_prompts = []
        # Region A
        if enabled_A and sampler_A is not None:
            rp_A = impact_core.REGIONAL_PROMPT(
                mask=mask_A,
                sampler=sampler_A,
                variation_seed=variation_seed,
                variation_strength=variation_strength,
                variation_method=variation_method
            )
            regional_prompts.append(rp_A)

        # Region B
        if enabled_B and sampler_B is not None:
            rp_B = impact_core.REGIONAL_PROMPT(
                mask=mask_B,
                sampler=sampler_B,
                variation_seed=variation_seed,
                variation_strength=variation_strength,
                variation_method=variation_method
            )
            regional_prompts.append(rp_B)

        debug_info = {
            "total_regional_prompts": len(regional_prompts),
            "enabled_A": enabled_A,
            "enabled_B": enabled_B,
            "variation_seed": variation_seed,
            "variation_strength": variation_strength,
            "variation_method": variation_method
        }

        return (regional_prompts, mask_A, mask_B, json.dumps(debug_info, indent=2, ensure_ascii=False))
