"""
Tegaki Manga Impact Regional Adapter (Phase 3E)
================================================
Translates PAGE_COMPILE_PLAN and PANEL_LAYOUT_SPEC into Impact Pack
REGIONAL_PROMPTS using KSamplerAdvancedWrapper.clone_with_conditionings.

Features:
- Generic N-region generation for arbitrary active panels (1-6) and character instances.
- Zero extra provider nodes required: clones base_sampler per-region with encoded CLIP conditionings.
- Color-coded preview image visualizing panel bounds, scene backgrounds, and character placements.
- Fail-closed error handling and detailed debug JSON telemetry.
"""

import json
import logging
import os
import sys
from typing import Dict, Any, Tuple, List, Optional

import torch
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from .impact_region_plan import build_impact_region_plan


CHAR_PREVIEW_COLORS = [
    (245, 130, 32, 160),   # Futaba orange
    (46, 139, 87, 160),    # Sea green
    (70, 130, 180, 160),   # Steel blue
    (186, 85, 211, 160),   # Medium orchid
    (220, 20, 60, 160),    # Crimson
    (218, 165, 32, 160)    # Goldenrod
]


class TegakiMangaImpactRegionalAdapter:
    """
    Tegaki Manga Impact Regional Adapter (Phase 3E Engine)
    """
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "page_compile_plan": ("PAGE_COMPILE_PLAN",),
                "panel_layout_spec": ("PANEL_LAYOUT_SPEC",),
                "base_sampler": ("KSAMPLER_ADVANCED",),
                "clip": ("CLIP",),
            },
            "optional": {
                "ordering_mode": (["scene_first", "character_first"], {"default": "scene_first"}),
                "character_prompt_mode": (["scene_composed", "standalone"], {"default": "scene_composed"}),
                "include_panel_backgrounds": ("BOOLEAN", {"default": True}),
                "remainder_mask_mode": ("BOOLEAN", {"default": False}),
                "mask_feather": ("INT", {"default": 0, "min": 0, "max": 64, "step": 1}),
                "variation_seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff}),
                "variation_strength": ("FLOAT", {"default": 0.0, "min": 0.0, "max": 1.0, "step": 0.01}),
                "variation_method": (["linear", "slerp"], {"default": "linear"}),
                "propagate_controlnet_to_regions": ("BOOLEAN", {"default": False}),
            }
        }

    RETURN_TYPES = ("REGIONAL_PROMPTS", "MASK", "IMAGE", "STRING")
    RETURN_NAMES = ("regional_prompts", "region_masks", "preview_image", "debug_json")
    FUNCTION = "build_regional_prompts"
    CATEGORY = "tegaki/manga/engine"

    def _encode_text(self, clip: Any, text: str):
        if clip is None:
            raise RuntimeError("[TegakiMangaImpactRegionalAdapter] CLIP input is None.")
        tokens = clip.tokenize(text if text is not None else "")
        return clip.encode_from_tokens_scheduled(tokens)

    def build_regional_prompts(
        self,
        page_compile_plan: Any,
        panel_layout_spec: Any,
        base_sampler: Any,
        clip: Any,
        ordering_mode: str = "scene_first",
        character_prompt_mode: str = "scene_composed",
        include_panel_backgrounds: bool = True,
        remainder_mask_mode: bool = False,
        mask_feather: int = 0,
        variation_seed: int = 0,
        variation_strength: float = 0.0,
        variation_method: str = "linear",
        propagate_controlnet_to_regions: bool = False
    ) -> Tuple[List[Any], torch.Tensor, torch.Tensor, str]:
        # 1. Dynamic import of Impact Pack
        impact_core = None
        try:
            import impact.core as impact_core
        except ImportError:
            try:
                import importlib
                impact_pack_mod = importlib.import_module("ComfyUI-Impact-Pack.modules.impact.core")
                impact_core = impact_pack_mod
            except Exception:
                pass

        if impact_core is None:
            candidate_dirs = [
                os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "ComfyUI", "custom_nodes", "ComfyUI-Impact-Pack", "modules")),
                os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "ComfyUI-Impact-Pack", "modules")),
            ]
            for cdir in candidate_dirs:
                if os.path.exists(cdir) and cdir not in sys.path:
                    sys.path.insert(0, cdir)
            try:
                import impact.core as impact_core
            except Exception:
                pass

        if impact_core is None:
            raise RuntimeError(
                "[TegakiMangaImpactRegionalAdapter] ComfyUI-Impact-Pack is not installed or importable. "
                "Please install ComfyUI-Impact-Pack to use this adapter."
            )

        # 2. Compile execution plan
        plan = build_impact_region_plan(
            page_compile_plan=page_compile_plan,
            panel_layout_spec=panel_layout_spec,
            ordering_mode=ordering_mode,
            character_prompt_mode=character_prompt_mode,
            include_panel_backgrounds=include_panel_backgrounds,
            remainder_mask_mode=remainder_mask_mode,
            mask_feather=mask_feather
        )

        width = plan["canvas"]["width"]
        height = plan["canvas"]["height"]
        regions = plan["regions"]

        regional_prompts = []
        mask_list = []
        debug_regions = []

        # Inspect base_sampler for ControlNet conditioning propagation (Phase 3I.1 A/B)
        base_control_obj = None
        base_control_uncond = False
        if propagate_controlnet_to_regions and hasattr(base_sampler, "params") and len(base_sampler.params) >= 5:
            base_pos = base_sampler.params[4]
            if base_pos and isinstance(base_pos, list) and len(base_pos) > 0 and len(base_pos[0]) > 1:
                base_dict = base_pos[0][1]
                if isinstance(base_dict, dict) and "control" in base_dict:
                    base_control_obj = base_dict["control"]
                    base_control_uncond = base_dict.get("control_apply_to_uncond", False)

        # 3. Create regional samplers via base_sampler.clone_with_conditionings
        for reg in regions:
            pos_cond = self._encode_text(clip, reg["prompt"])
            neg_cond = self._encode_text(clip, reg["negative_prompt"])

            # Attach ControlNet metadata if propagation enabled and present
            if propagate_controlnet_to_regions and base_control_obj is not None:
                new_pos_cond = []
                for t, d in pos_cond:
                    d_copy = d.copy()
                    d_copy["control"] = base_control_obj
                    d_copy["control_apply_to_uncond"] = base_control_uncond
                    new_pos_cond.append([t, d_copy])
                pos_cond = new_pos_cond

            # Clone base sampler with regional conditionings
            regional_sampler = base_sampler.clone_with_conditionings(pos_cond, neg_cond)

            mask_tensor = reg["mask"]
            if len(mask_tensor.shape) == 2:
                mask_tensor = mask_tensor.unsqueeze(0)

            rp = impact_core.REGIONAL_PROMPT(
                mask=mask_tensor,
                sampler=regional_sampler,
                variation_seed=variation_seed,
                variation_strength=variation_strength,
                variation_method=variation_method
            )
            regional_prompts.append(rp)
            mask_list.append(mask_tensor[0])

            debug_regions.append({
                "region_index": reg["region_index"],
                "scope_type": reg["scope_type"],
                "source_panel_id": reg["source_panel_id"],
                "character_instance_id": reg["character_instance_id"],
                "master_character_id": reg["master_character_id"],
                "prompt": reg["prompt"],
                "negative_prompt": reg["negative_prompt"],
                "priority": reg["priority"]
            })

        if mask_list:
            stacked_masks = torch.stack(mask_list, dim=0)
        else:
            stacked_masks = torch.zeros((1, height, width), dtype=torch.float32)

        # 4. Generate visual preview image
        preview_img = Image.new("RGBA", (width, height), (248, 246, 240, 255))
        overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw_overlay = ImageDraw.Draw(overlay)
        draw_base = ImageDraw.Draw(preview_img)

        try:
            font = ImageFont.truetype("arial.ttf", 18)
            small_font = ImageFont.truetype("arial.ttf", 13)
        except Exception:
            font = ImageFont.load_default()
            small_font = ImageFont.load_default()

        # Draw panel regions and character regions
        char_color_idx = 0
        for reg in regions:
            stype = reg["scope_type"]
            meta = reg.get("metadata", {})

            if stype == "panel_scene":
                # Panel outline
                bbox = meta.get("bbox_pixels", [0, 0, width, height])
                draw_base.rectangle(bbox, outline=(70, 50, 30, 255), width=2)
                p_label = f"Panel {reg['source_panel_id']}"
                draw_base.text((bbox[0] + 8, bbox[1] + 8), p_label, fill=(70, 50, 30, 255), font=font)
                if reg["prompt"]:
                    short_prompt = reg["prompt"][:40] + ("..." if len(reg["prompt"]) > 40 else "")
                    draw_base.text((bbox[0] + 8, bbox[1] + 30), short_prompt, fill=(120, 100, 80, 255), font=small_font)

            elif stype == "character_instance":
                bounds = meta.get("pixel_bounds", [0, 0, 100, 100])
                c_color = CHAR_PREVIEW_COLORS[char_color_idx % len(CHAR_PREVIEW_COLORS)]
                char_color_idx += 1

                # Fill translucent rectangle
                draw_overlay.rectangle(bounds, fill=c_color, outline=(40, 30, 20, 220), width=2)
                c_label = f"{reg.get('character_name') or reg['master_character_id']} ({reg['character_instance_id']})"
                draw_overlay.text((bounds[0] + 6, bounds[1] + 6), c_label, fill=(255, 255, 255, 255), font=font)
                if reg["prompt"]:
                    short_acting = reg["prompt"][:35] + ("..." if len(reg["prompt"]) > 35 else "")
                    draw_overlay.text((bounds[0] + 6, bounds[1] + 28), short_acting, fill=(240, 240, 240, 255), font=small_font)

        final_preview = Image.alpha_composite(preview_img, overlay).convert("RGB")
        preview_np = np.array(final_preview, dtype=np.float32) / 255.0
        preview_tensor = torch.from_numpy(preview_np).unsqueeze(0)  # [1, H, W, 3]

        debug_info = {
            "summary": plan["summary"],
            "ordering_mode": ordering_mode,
            "character_prompt_mode": character_prompt_mode,
            "propagate_controlnet_to_regions": propagate_controlnet_to_regions,
            "controlnet_propagated": (base_control_obj is not None) if propagate_controlnet_to_regions else False,
            "total_regional_prompts": len(regional_prompts),
            "regions": debug_regions
        }

        return (regional_prompts, stacked_masks, preview_tensor, json.dumps(debug_info, indent=2, ensure_ascii=False))
