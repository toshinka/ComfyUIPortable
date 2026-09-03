import json
import logging
import torch
from typing import Dict, Any, List, Optional, Tuple

import node_helpers
from .scene_spec import validate_page_compile_plan
from .mask_builder import TegakiMangaMaskBuilder


class TegakiMangaConditioningBuilder:
    """
    Tegaki Manga Conditioning Builder (Phase 3B / 3B.1)
    PAGE_COMPILE_PLAN と CLIP を受け取り、
    - Global Positive / Negative (ページ全体・マスクなし)
    - Panel Positive / Negative (各コマ領域・Mask付き)
    - Local Region Positive / Negative (コマ内局所領域・Mask付き, Phase 3B.1新設)
    - Character Positive / Negative (各Character Area・Mask付き)
    を ComfyUI Core API に準拠して構築・Combineした Conditioning を生成する。
    優先順位: Global -> Panel -> Local Region -> Character
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
                "local_region_strength": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 2.0, "step": 0.05}),
                "set_cond_area": (["default", "mask bounds"], {"default": "default"}),
                "mask_feather": ("INT", {"default": 0, "min": 0, "max": 64, "step": 1}),
            }
        }

    RETURN_TYPES = ("CONDITIONING", "CONDITIONING", "MASK", "MASK", "STRING", "MASK")
    RETURN_NAMES = ("positive", "negative", "panel_masks", "character_masks", "debug_json", "local_region_masks")
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
        local_region_strength: float = 1.0,
        set_cond_area: str = "default",
        mask_feather: int = 0
    ):
        plan = validate_page_compile_plan(page_compile_plan)

        # 1. Mask Builder を利用して各階層のマスクを生成 (フェザー対応)
        mask_builder = TegakiMangaMaskBuilder()
        panel_masks, char_masks, mask_preview, mask_debug_json, lr_masks = mask_builder.build_masks(plan, mask_feather=mask_feather)
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
            "local_regions": [],
            "characters": []
        }

        # 2. Global Conditioning (マスクなし・全体適用)
        g_pos = self._encode_text(clip, global_prompt)
        pos_conditioning.extend(g_pos)

        g_neg = self._encode_text(clip, global_negative_prompt)
        neg_conditioning.extend(g_neg)

        # 3. Panel Conditioning (各コマ領域)
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

        # 4. Local Region Conditioning (コマ内局所領域 - Phase 3B.1新設)
        lr_idx = 0
        for p in panels:
            pid = p["target_panel_id"]
            for lr in p.get("panel", {}).get("local_regions", []):
                lid = lr.get("id")
                lname = lr.get("name", lid)
                lr_pos_text = lr.get("prompt", "")
                lr_neg_text = lr.get("negative_prompt", "")

                if lr_idx < len(lr_masks):
                    l_mask = lr_masks[lr_idx:lr_idx+1]

                    if lr_pos_text and lr_pos_text.strip():
                        lr_pos_raw = self._encode_text(clip, lr_pos_text)
                        lr_pos_masked = self._apply_mask(lr_pos_raw, l_mask, local_region_strength, set_cond_area)
                        pos_conditioning.extend(lr_pos_masked)

                    if lr_neg_text and lr_neg_text.strip():
                        lr_neg_raw = self._encode_text(clip, lr_neg_text)
                        lr_neg_masked = self._apply_mask(lr_neg_raw, l_mask, local_region_strength, set_cond_area)
                        neg_conditioning.extend(lr_neg_masked)

                    debug_entries["local_regions"].append({
                        "id": lid,
                        "name": lname,
                        "panel_id": pid,
                        "index": lr_idx,
                        "positive": lr_pos_text,
                        "negative": lr_neg_text,
                        "strength": local_region_strength
                    })
                lr_idx += 1

        # 5. Character Conditioning (各Character Area)
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
            "tuning": {
                "panel_strength": panel_strength,
                "local_region_strength": local_region_strength,
                "character_strength": character_strength,
                "set_cond_area": set_cond_area,
                "mask_feather": mask_feather
            },
            "entries": debug_entries,
            "total_positive_branches": len(pos_conditioning),
            "total_negative_branches": len(neg_conditioning)
        }, indent=2, ensure_ascii=False)

        return (pos_conditioning, neg_conditioning, panel_masks, char_masks, debug_json, lr_masks)
