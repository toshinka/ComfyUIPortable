"""
Tegaki Single Panel Multi-Scene Impact Adapter (Phase 3E Hostile Test)
======================================================================
Dedicated experimental oracle node for testing:
- 1 visible panel containing 2 internal semantic scenes (Scene A vs Scene B).
- Recurrent Cast within the same panel: Alice x2 instances, Bob x2 instances.
- Zero textual position bias: NO "left" or "right" words in prompts.
- Independent subscene geometries with controllable scene and character overlap.
"""

import json
import logging
import os
import sys
from typing import Dict, Any, Tuple, List, Optional

import torch
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from .scene_spec import validate_cast_spec
from .panel_layout_spec import validate_panel_layout_spec
from .layout_aware_mask_builder import render_polygon_mask, render_rect_mask


class TegakiSinglePanelMultiSceneImpactAdapter:
    """
    Experimental Single-Panel Multi-Scene Impact Adapter (Hostile Oracle)
    """
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "panel_layout_spec": ("PANEL_LAYOUT_SPEC",),
                "cast_spec": ("CAST_SPEC",),
                "base_sampler": ("KSAMPLER_ADVANCED",),
                "clip": ("CLIP",),
            },
            "optional": {
                "scene_A_scene_prompt": ("STRING", {
                    "default": "school gate, afternoon sunset, dramatic shadows",
                    "multiline": True
                }),
                "scene_A_acting": ("STRING", {
                    "default": "arguing intensely, both looking away from each other, frustrated expression",
                    "multiline": True
                }),
                "scene_B_scene_prompt": ("STRING", {
                    "default": "school garden, blooming flowers, soft sunlight",
                    "multiline": True
                }),
                "scene_B_acting": ("STRING", {
                    "default": "friendly handshake, facing each other, happy smiling expression",
                    "multiline": True
                }),
                "scene_split_ratio": ("FLOAT", {"default": 0.50, "min": 0.20, "max": 0.80, "step": 0.05}),
                "scene_boundary_overlap": ("FLOAT", {"default": 0.05, "min": 0.0, "max": 0.20, "step": 0.01}),
                "character_overlap": ("FLOAT", {"default": 0.25, "min": 0.0, "max": 0.50, "step": 0.01}),
                "mask_feather": ("INT", {"default": 0, "min": 0, "max": 64, "step": 1}),
                "variation_seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff}),
                "variation_strength": ("FLOAT", {"default": 0.0, "min": 0.0, "max": 1.0, "step": 0.01}),
                "variation_method": (["linear", "slerp"], {"default": "linear"}),
            }
        }

    RETURN_TYPES = ("REGIONAL_PROMPTS", "MASK", "IMAGE", "STRING")
    RETURN_NAMES = ("regional_prompts", "region_masks", "preview_image", "debug_json")
    FUNCTION = "build_multiscene_prompts"
    CATEGORY = "tegaki/manga/experimental"

    def _encode_text(self, clip: Any, text: str):
        if clip is None:
            raise RuntimeError("[TegakiSinglePanelMultiSceneImpactAdapter] CLIP input is None.")
        tokens = clip.tokenize(text if text is not None else "")
        return clip.encode_from_tokens_scheduled(tokens)

    def build_multiscene_prompts(
        self,
        panel_layout_spec: Any,
        cast_spec: Any,
        base_sampler: Any,
        clip: Any,
        scene_A_scene_prompt: str = "school gate, afternoon sunset",
        scene_A_acting: str = "arguing intensely, looking away",
        scene_B_scene_prompt: str = "school garden, flowers",
        scene_B_acting: str = "friendly handshake, facing each other",
        scene_split_ratio: float = 0.50,
        scene_boundary_overlap: float = 0.05,
        character_overlap: float = 0.25,
        mask_feather: int = 0,
        variation_seed: int = 0,
        variation_strength: float = 0.0,
        variation_method: str = "linear"
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
                "[TegakiSinglePanelMultiSceneImpactAdapter] ComfyUI-Impact-Pack is not installed or importable."
            )

        layout = validate_panel_layout_spec(panel_layout_spec, context_name="MultiSceneAdapter")
        cast = validate_cast_spec(cast_spec)

        width = int(layout["canvas"]["width"])
        height = int(layout["canvas"]["height"])

        # Find Alice and Bob in cast_spec
        chars_map = {c["id"]: c for c in cast.get("characters", [])}
        alice_master = chars_map.get("char_alice") or {"prompt": "1girl, blonde twin tails, blue eyes, school uniform", "negative_prompt": ""}
        bob_master = chars_map.get("char_bob") or {"prompt": "1boy, short black hair, school uniform", "negative_prompt": ""}

        # Geometry definition:
        # Scene A = Left side [0.0, 0.0, split + overlap/2, 1.0]
        # Scene B = Right side [split - overlap/2, 0.0, 1.0 - (split - overlap/2), 1.0]
        half_ov = scene_boundary_overlap / 2.0
        sA_x0 = 0.0
        sA_x1 = min(1.0, scene_split_ratio + half_ov)
        sB_x0 = max(0.0, scene_split_ratio - half_ov)
        sB_x1 = 1.0

        # Subscene character positioning:
        # Inside each scene, place Alice on left, Bob on right with character_overlap
        # For Scene A:
        sA_w = sA_x1 - sA_x0
        cA_alice_x0 = sA_x0 + 0.05 * sA_w
        cA_alice_x1 = sA_x0 + (0.50 + character_overlap / 2.0) * sA_w
        cA_bob_x0 = sA_x0 + (0.50 - character_overlap / 2.0) * sA_w
        cA_bob_x1 = sA_x0 + 0.95 * sA_w

        # For Scene B:
        sB_w = sB_x1 - sB_x0
        cB_alice_x0 = sB_x0 + 0.05 * sB_w
        cB_alice_x1 = sB_x0 + (0.50 + character_overlap / 2.0) * sB_w
        cB_bob_x0 = sB_x0 + (0.50 - character_overlap / 2.0) * sB_w
        cB_bob_x1 = sB_x0 + 0.95 * sB_w

        def _to_pixel_bounds(x0, y0, x1, y1):
            px0 = max(0, min(width, int(round(x0 * width))))
            py0 = max(0, min(height, int(round(y0 * height))))
            px1 = max(0, min(width, int(round(x1 * width))))
            py1 = max(0, min(height, int(round(y1 * height))))
            return [px0, py0, px1, py1]

        sceneA_bounds = _to_pixel_bounds(sA_x0, 0.0, sA_x1, 1.0)
        sceneB_bounds = _to_pixel_bounds(sB_x0, 0.0, sB_x1, 1.0)
        aliceA_bounds = _to_pixel_bounds(cA_alice_x0, 0.15, cA_alice_x1, 0.95)
        bobA_bounds = _to_pixel_bounds(cA_bob_x0, 0.15, cA_bob_x1, 0.95)
        aliceB_bounds = _to_pixel_bounds(cB_alice_x0, 0.15, cB_alice_x1, 0.95)
        bobB_bounds = _to_pixel_bounds(cB_bob_x0, 0.15, cB_bob_x1, 0.95)

        # Build region entries
        # Canonical order: Scene first -> Characters later
        entries = [
            # 1. Scene A Background
            {
                "scope_type": "experimental_subscene",
                "source_scene_id": "scene_A",
                "character_instance_id": None,
                "master_character_id": None,
                "prompt": scene_A_scene_prompt,
                "negative_prompt": "blurry, low quality",
                "bounds": sceneA_bounds,
                "priority": 100
            },
            # 2. Scene B Background
            {
                "scope_type": "experimental_subscene",
                "source_scene_id": "scene_B",
                "character_instance_id": None,
                "master_character_id": None,
                "prompt": scene_B_scene_prompt,
                "negative_prompt": "blurry, low quality",
                "bounds": sceneB_bounds,
                "priority": 100
            },
            # 3. Scene A - Alice instance 1
            {
                "scope_type": "character_instance",
                "source_scene_id": "scene_A",
                "character_instance_id": "scene_a_char_alice_00",
                "master_character_id": "char_alice",
                "character_name": "Alice",
                "prompt": f"{scene_A_scene_prompt}, {alice_master['prompt']}, {scene_A_acting}",
                "negative_prompt": alice_master.get("negative_prompt", "blurry, low quality"),
                "bounds": aliceA_bounds,
                "priority": 300
            },
            # 4. Scene A - Bob instance 1
            {
                "scope_type": "character_instance",
                "source_scene_id": "scene_A",
                "character_instance_id": "scene_a_char_bob_01",
                "master_character_id": "char_bob",
                "character_name": "Bob",
                "prompt": f"{scene_A_scene_prompt}, {bob_master['prompt']}, {scene_A_acting}",
                "negative_prompt": bob_master.get("negative_prompt", "bad anatomy"),
                "bounds": bobA_bounds,
                "priority": 300
            },
            # 5. Scene B - Alice instance 2
            {
                "scope_type": "character_instance",
                "source_scene_id": "scene_B",
                "character_instance_id": "scene_b_char_alice_02",
                "master_character_id": "char_alice",
                "character_name": "Alice",
                "prompt": f"{scene_B_scene_prompt}, {alice_master['prompt']}, {scene_B_acting}",
                "negative_prompt": alice_master.get("negative_prompt", "blurry, low quality"),
                "bounds": aliceB_bounds,
                "priority": 300
            },
            # 6. Scene B - Bob instance 2
            {
                "scope_type": "character_instance",
                "source_scene_id": "scene_B",
                "character_instance_id": "scene_b_char_bob_03",
                "master_character_id": "char_bob",
                "character_name": "Bob",
                "prompt": f"{scene_B_scene_prompt}, {bob_master['prompt']}, {scene_B_acting}",
                "negative_prompt": bob_master.get("negative_prompt", "bad anatomy"),
                "bounds": bobB_bounds,
                "priority": 300
            },
        ]

        regional_prompts = []
        mask_list = []
        for idx, e in enumerate(entries):
            e["region_index"] = idx
            pos_cond = self._encode_text(clip, e["prompt"])
            neg_cond = self._encode_text(clip, e["negative_prompt"])

            reg_sampler = base_sampler.clone_with_conditionings(pos_cond, neg_cond)
            mask = render_rect_mask(e["bounds"], width, height).unsqueeze(0)

            rp = impact_core.REGIONAL_PROMPT(
                mask=mask,
                sampler=reg_sampler,
                variation_seed=variation_seed,
                variation_strength=variation_strength,
                variation_method=variation_method
            )
            regional_prompts.append(rp)
            mask_list.append(mask[0])

        stacked_masks = torch.stack(mask_list, dim=0)

        # Visual preview
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

        # Draw scene split
        draw_base.rectangle(sceneA_bounds, outline=(180, 50, 50, 255), width=3)
        draw_base.text((sceneA_bounds[0] + 12, 12), "Scene A: Conflict / Arguing", fill=(180, 50, 50, 255), font=font)
        draw_base.rectangle(sceneB_bounds, outline=(50, 130, 70, 255), width=3)
        draw_base.text((sceneB_bounds[0] + 12, 12), "Scene B: Friendly / Handshake", fill=(50, 130, 70, 255), font=font)

        # Draw character instances
        c_colors = [
            (245, 130, 32, 170),  # Alice A
            (70, 130, 180, 170),  # Bob A
            (245, 130, 32, 170),  # Alice B
            (70, 130, 180, 170),  # Bob B
        ]
        char_entries = entries[2:]
        for idx, ce in enumerate(char_entries):
            b = ce["bounds"]
            color = c_colors[idx % len(c_colors)]
            draw_overlay.rectangle(b, fill=color, outline=(40, 30, 20, 240), width=2)
            label = f"{ce['character_name']} ({ce['character_instance_id']})"
            draw_overlay.text((b[0] + 6, b[1] + 8), label, fill=(255, 255, 255, 255), font=font)

        final_preview = Image.alpha_composite(preview_img, overlay).convert("RGB")
        preview_np = np.array(final_preview, dtype=np.float32) / 255.0
        preview_tensor = torch.from_numpy(preview_np).unsqueeze(0)

        debug_info = {
            "test_type": "Hostile Multi-Scene Single-Panel Test",
            "visible_panel_count": 1,
            "internal_scene_count": 2,
            "character_instance_count": len(char_entries),
            "master_characters_used": ["char_alice", "char_bob"],
            "recurrent_instances": [e["character_instance_id"] for e in char_entries],
            "ordering": "scene_first",
            "entries": entries
        }

        return (regional_prompts, stacked_masks, preview_tensor, json.dumps(debug_info, indent=2, ensure_ascii=False))
