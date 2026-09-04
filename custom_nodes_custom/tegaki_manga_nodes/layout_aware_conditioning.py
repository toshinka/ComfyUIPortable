"""
Tegaki Manga Layout-Aware Conditioning Builder (Phase 3D)
==========================================================
PAGE_COMPILE_PLAN と PANEL_LAYOUT_SPEC、および CLIP を受け取り、
1. Global Conditioning (ページ全体トーン・マスクなし)
2. Panel Polygon Conditioning (各コマ多角形領域・Polygon Mask付き)
3. Local Region Conditioning (コマ内局所領域・Polygon クリップ済みMask付き)
4. Character Semantic Conditioning (各人物領域・BBox投影 + Polygon クリップ済みMask付き, Overlap許容)
を ComfyUI Core API に準拠して構築・Combineした Conditioning を生成する。
"""

import json
import logging
import math
import torch
from typing import Dict, Any, List, Optional, Tuple

import node_helpers
from .scene_spec import validate_page_compile_plan
from .panel_layout_spec import validate_panel_layout_spec
from .layout_region_bridge import build_panel_content_bridge
from .layout_aware_mask_builder import build_layout_aware_masks


class TegakiMangaLayoutAwareConditioningBuilder:
    """
    Tegaki Manga Layout-Aware Conditioning Builder (Phase 3D)
    漫画コマ割り幾何 (PANEL_LAYOUT_SPEC) と意味シーン計画 (PAGE_COMPILE_PLAN) を統合し、
    多角形コママスクとキャラクター Semantic Overlap を単一 KSampler で矛盾なく
    駆動する階層的 Conditioning を生成する。
    """
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "clip": ("CLIP",),
                "page_compile_plan": ("PAGE_COMPILE_PLAN",),
                "panel_layout_spec": ("PANEL_LAYOUT_SPEC",),
            },
            "optional": {
                "panel_strength": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 2.0, "step": 0.05}),
                "character_strength": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 2.0, "step": 0.05}),
                "set_cond_area": (["default", "mask bounds"], {"default": "default"}),
                "local_region_strength": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 2.0, "step": 0.05}),
                "mask_feather": ("INT", {"default": 0, "min": 0, "max": 64, "step": 1}),
            }
        }

    RETURN_TYPES = ("CONDITIONING", "CONDITIONING", "MASK", "MASK", "IMAGE", "STRING", "MASK")
    RETURN_NAMES = ("positive", "negative", "panel_masks", "character_masks", "mask_preview", "debug_json", "local_region_masks")
    FUNCTION = "build_conditioning"
    CATEGORY = "tegaki/manga"

    def _encode_text(self, clip: Any, text: str):
        if clip is None:
            raise RuntimeError("[TegakiLayoutAwareConditioningBuilder] CLIP input is None.")
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
        page_compile_plan: Any,
        panel_layout_spec: Any,
        panel_strength: float = 1.0,
        character_strength: float = 1.0,
        set_cond_area: str = "default",
        local_region_strength: float = 1.0,
        mask_feather: int = 0
    ):
        # Backend Finite Validation
        for name, val in [
            ("panel_strength", panel_strength),
            ("character_strength", character_strength),
            ("local_region_strength", local_region_strength)
        ]:
            if val is None or not math.isfinite(float(val)):
                raise ValueError(f"[TegakiLayoutAwareConditioningBuilder] '{name}' must be a finite float, got {val!r}")

        # 1. Bridge によるコマ数検証・安定マッピング・幾何BBox投影
        bridge_data = build_panel_content_bridge(
            page_compile_plan,
            panel_layout_spec,
            context_name="TegakiLayoutAwareConditioningBuilder"
        )

        # 2. 多角形パネルマスク & クリップ済みキャラクター・局所マスクの構築
        panel_masks, char_masks, mask_preview, mask_debug_json, lr_masks = build_layout_aware_masks(
            bridge_data,
            mask_feather=mask_feather
        )

        plan = validate_page_compile_plan(page_compile_plan)
        global_prompt = plan.get("global_prompt", "")
        global_negative_prompt = plan.get("global_negative_prompt", "")

        pos_conditioning = []
        neg_conditioning = []

        debug_entries = {
            "mode": "layout_driven_polygon_conditioning",
            "global": {
                "positive": global_prompt,
                "negative": global_negative_prompt
            },
            "panel_content_map": bridge_data["panel_content_map"],
            "panels": [],
            "local_regions": [],
            "characters": []
        }

        # 3. Global Conditioning (マスクなし・全体スコープ)
        if global_prompt and global_prompt.strip():
            g_pos = self._encode_text(clip, global_prompt)
            pos_conditioning.extend(g_pos)
        else:
            g_pos = self._encode_text(clip, "")
            pos_conditioning.extend(g_pos)

        if global_negative_prompt and global_negative_prompt.strip():
            g_neg = self._encode_text(clip, global_negative_prompt)
            neg_conditioning.extend(g_neg)
        else:
            g_neg = self._encode_text(clip, "")
            neg_conditioning.extend(g_neg)

        # 4. Panel Polygon Conditioning (各コマ多角形領域)
        mapped_panels = bridge_data["mapped_panels"]
        for p_idx, p in enumerate(mapped_panels):
            koma_id = p["koma_id"]
            layout_id = p["layout_panel_id"]
            koma = p["koma"]

            p_pos_text = koma.get("clean_prompt") or koma.get("panel", {}).get("prompt") or koma.get("panel", {}).get("clean_prompt", "")
            p_neg_text = koma.get("clean_negative_prompt") or koma.get("panel", {}).get("negative_prompt") or koma.get("panel", {}).get("clean_negative_prompt", "")

            if p_idx < len(panel_masks):
                p_mask = panel_masks[p_idx:p_idx+1]

                if p_pos_text and p_pos_text.strip():
                    p_pos_raw = self._encode_text(clip, p_pos_text)
                    p_pos_masked = self._apply_mask(p_pos_raw, p_mask, panel_strength, set_cond_area)
                    pos_conditioning.extend(p_pos_masked)

                if p_neg_text and p_neg_text.strip():
                    p_neg_raw = self._encode_text(clip, p_neg_text)
                    p_neg_masked = self._apply_mask(p_neg_raw, p_mask, panel_strength, set_cond_area)
                    neg_conditioning.extend(p_neg_masked)

            debug_entries["panels"].append({
                "koma_id": koma_id,
                "layout_panel_id": layout_id,
                "index": p_idx,
                "positive": p_pos_text,
                "negative": p_neg_text,
                "strength": panel_strength
            })

        # 5. Local Region Conditioning (コマ内局所領域)
        for lr in bridge_data["local_regions"]:
            lr_idx = lr["local_region_index"]
            lr_pos_text = lr.get("prompt", "")
            lr_neg_text = lr.get("negative_prompt", "")
            eff_strength = lr.get("weight", 1.0) * local_region_strength

            if lr_idx < len(lr_masks):
                l_mask = lr_masks[lr_idx:lr_idx+1]

                if lr_pos_text and lr_pos_text.strip():
                    lr_pos_raw = self._encode_text(clip, lr_pos_text)
                    lr_pos_masked = self._apply_mask(lr_pos_raw, l_mask, eff_strength, set_cond_area)
                    pos_conditioning.extend(lr_pos_masked)

                if lr_neg_text and lr_neg_text.strip():
                    lr_neg_raw = self._encode_text(clip, lr_neg_text)
                    lr_neg_masked = self._apply_mask(lr_neg_raw, l_mask, eff_strength, set_cond_area)
                    neg_conditioning.extend(lr_neg_masked)

            debug_entries["local_regions"].append({
                "id": lr["id"],
                "name": lr["name"],
                "koma_id": lr["koma_id"],
                "layout_panel_id": lr["layout_panel_id"],
                "index": lr_idx,
                "positive": lr_pos_text,
                "negative": lr_neg_text,
                "strength": eff_strength
            })

        # 6. Character Semantic Conditioning (各人物領域 - Semantic Overlap 許容)
        for c in bridge_data["characters"]:
            c_idx = c["character_index"]
            c_pos_text = c.get("clean_prompt", "")
            c_neg_text = c.get("clean_negative_prompt", "")

            if c_idx < len(char_masks):
                c_mask = char_masks[c_idx:c_idx+1]

                if c_pos_text and c_pos_text.strip():
                    c_pos_raw = self._encode_text(clip, c_pos_text)
                    c_pos_masked = self._apply_mask(c_pos_raw, c_mask, character_strength, set_cond_area)
                    pos_conditioning.extend(c_pos_masked)

                if c_neg_text and c_neg_text.strip():
                    c_neg_raw = self._encode_text(clip, c_neg_text)
                    c_neg_masked = self._apply_mask(c_neg_raw, c_mask, character_strength, set_cond_area)
                    neg_conditioning.extend(c_neg_masked)

            debug_entries["characters"].append({
                "character_id": c["character_id"],
                "character_name": c["character_name"],
                "koma_id": c["koma_id"],
                "layout_panel_id": c["layout_panel_id"],
                "index": c_idx,
                "positive": c_pos_text,
                "negative": c_neg_text,
                "strength": character_strength,
                "projected_area": c["page_projected_area"]
            })

        return (
            pos_conditioning,
            neg_conditioning,
            panel_masks,
            char_masks,
            mask_preview,
            json.dumps(debug_entries, indent=2),
            lr_masks
        )
