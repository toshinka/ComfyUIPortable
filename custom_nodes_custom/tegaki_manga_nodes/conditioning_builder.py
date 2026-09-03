import json
import logging
import torch
from typing import Dict, Any, List, Optional, Tuple

import node_helpers
from .scene_spec import validate_page_compile_plan
from .mask_builder import TegakiMangaMaskBuilder


class TegakiMangaConditioningBuilder:
    """
    Tegaki Manga Conditioning Builder (Phase 3B)
    PAGE_COMPILE_PLAN と CLIP を受け取り、
    - Global Positive / Negative (ページ全体・マスクなし)
    - Panel Positive / Negative (各コマ領域・Mask付き)
    - Character Positive / Negative (各Character Area・Mask付き)
    を ComfyUI Core API に準拠して構築・Combineした Conditioning を生成する。
    """
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "clip": ("CLIP",),
                "page_compile_plan": ("PAGE_COMPILE_PLAN",),
            },
            "optional": {
                "panel_strength": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 2.0, "step": 0.05}),
                "character_strength": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 2.0, "step": 0.05}),
                "set_cond_area": (["default", "mask bounds"], {"default": "default"}),
            }
        }

    RETURN_TYPES = ("CONDITIONING", "CONDITIONING", "MASK", "MASK", "STRING")
    RETURN_NAMES = ("positive", "negative", "panel_mask_batch", "character_mask_batch", "debug_json")
    FUNCTION = "build_conditioning"
    CATEGORY = "tegaki/manga"

    def _encode_text(self, clip: Any, text: str):
        if clip is None:
            raise RuntimeError("[TegakiConditioningBuilder] CLIP input is None.")
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
        panel_strength: float = 1.0,
        character_strength: float = 1.0,
        set_cond_area: str = "default"
    ):
        plan = validate_page_compile_plan(page_compile_plan)

        # 1. Mask Builder を利用してマスクを生成
        mask_builder = TegakiMangaMaskBuilder()
        panel_masks, char_masks, _, mask_debug_json = mask_builder.build_masks(plan)
        mask_debug_data = json.loads(mask_debug_json)

        global_prompt = plan.get("global_prompt", "")
        global_negative_prompt = plan.get("global_negative_prompt", "")
        panels = plan.get("panels", [])

        pos_conditioning = []
        neg_conditioning = []

        debug_entries = {
            "global": {
                "positive": global_prompt,
                "negative": global_negative_prompt
            },
            "panels": [],
            "characters": []
        }

        # 2. Global Conditioning のエンコード (マスクなし・全体適用)
        g_pos = self._encode_text(clip, global_prompt)
        pos_conditioning.extend(g_pos)

        g_neg = self._encode_text(clip, global_negative_prompt)
        neg_conditioning.extend(g_neg)

        # 3. Panel Conditioning の構築
        for p_idx, p in enumerate(panels):
            pid = p["target_panel_id"]
            p_pos_text = p.get("panel", {}).get("prompt", "")
            p_neg_text = p.get("panel", {}).get("negative_prompt", "")
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
                "panel_id": pid,
                "index": p_idx,
                "positive": p_pos_text,
                "negative": p_neg_text,
                "strength": panel_strength
            })

        # 4. Character Conditioning の構築
        char_meta_list = mask_debug_data.get("characters", [])
        char_idx = 0
        for p in panels:
            pid = p["target_panel_id"]
            for c in p.get("characters", []):
                cid = c.get("character_id")
                cname = c.get("name", cid)
                c_pos_text = c.get("combined_prompt", "")
                c_neg_text = c.get("combined_negative_prompt", "")

                if char_idx < len(char_masks):
                    c_mask = char_masks[char_idx:char_idx+1]

                    if c_pos_text and c_pos_text.strip():
                        c_pos_raw = self._encode_text(clip, c_pos_text)
                        c_pos_masked = self._apply_mask(c_pos_raw, c_mask, character_strength, set_cond_area)
                        pos_conditioning.extend(c_pos_masked)

                    if c_neg_text and c_neg_text.strip():
                        c_neg_raw = self._encode_text(clip, c_neg_text)
                        c_neg_masked = self._apply_mask(c_neg_raw, c_mask, character_strength, set_cond_area)
                        neg_conditioning.extend(c_neg_masked)

                    debug_entries["characters"].append({
                        "character_id": cid,
                        "character_name": cname,
                        "panel_id": pid,
                        "index": char_idx,
                        "positive": c_pos_text,
                        "negative": c_neg_text,
                        "strength": character_strength
                    })
                char_idx += 1

        debug_json = json.dumps({
            "status": "success",
            "entries": debug_entries,
            "total_positive_branches": len(pos_conditioning),
            "total_negative_branches": len(neg_conditioning)
        }, indent=2, ensure_ascii=False)

        return (pos_conditioning, neg_conditioning, panel_masks, char_masks, debug_json)
