"""
Tegaki Manga Impact Region Plan (Phase 3E & 3F)
==============================================
Pure logic module that transforms high-level manga data (PAGE_COMPILE_PLAN,
PANEL_LAYOUT_SPEC) into an execution-time IMPACT_REGION_PLAN derivative.

Key Guarantees:
- Pure compile-time derivative: does NOT mutate or persist into permanent schemas.
- Stable deterministic mapping via LayoutRegionBridge.
- Progressive Authoring: Simple 1-Panel 1-Scene by default, with seamless SubScene v1 support.
- Unique character instance IDs (e.g. p1_char_alice_00, p1_subA_char_alice_00) preserving master character reference.
- Configurable region ordering: "scene_first" vs "character_first".
- Configurable prompt composition: "scene_composed" vs "standalone".
- Polygon-clipped masks preventing character/scene bleed across panel borders.
"""

import json
import logging
from typing import Dict, Any, List, Optional, Tuple

import torch
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from .layout_region_bridge import build_panel_content_bridge
from .layout_aware_mask_builder import render_polygon_mask, render_rect_mask
from .subscene_contract import has_active_subscenes, validate_panel_subscenes


def _apply_feather_single(mask: torch.Tensor, feather_radius: int) -> torch.Tensor:
    """Applies Gaussian feathering to a single [H, W] mask tensor."""
    if feather_radius <= 0:
        return mask
    H, W = mask.shape
    arr = (mask.cpu().numpy() * 255.0).astype(np.uint8)
    pil_img = Image.fromarray(arr, mode="L")
    blurred = pil_img.filter(ImageFilter.GaussianBlur(radius=feather_radius))
    out_arr = np.array(blurred, dtype=np.float32) / 255.0
    return torch.from_numpy(out_arr)


def build_impact_region_plan(
    page_compile_plan: Any,
    panel_layout_spec: Any,
    ordering_mode: str = "scene_first",
    character_prompt_mode: str = "scene_composed",
    include_panel_backgrounds: bool = True,
    remainder_mask_mode: bool = False,
    mask_feather: int = 0
) -> Dict[str, Any]:
    """
    Compiles PAGE_COMPILE_PLAN and PANEL_LAYOUT_SPEC into an IMPACT_REGION_PLAN.

    Args:
        page_compile_plan: Validated or raw PAGE_COMPILE_PLAN dictionary.
        panel_layout_spec: Validated or raw PANEL_LAYOUT_SPEC dictionary.
        ordering_mode: "scene_first" (scene background then characters) or
                       "character_first" (characters then scene background).
        character_prompt_mode: "scene_composed" (panel prompt + character prompt) or
                              "standalone" (character prompt only).
        include_panel_backgrounds: Whether to include broad panel scene regions.
        remainder_mask_mode: If True, subtracts character masks from panel background masks.
        mask_feather: Pixel radius for mask boundary feathering.

    Returns:
        Dictionary representing the IMPACT_REGION_PLAN.
    """
    bridge_data = build_panel_content_bridge(
        page_compile_plan=page_compile_plan,
        panel_layout_spec=panel_layout_spec,
        context_name="ImpactRegionPlan"
    )

    canvas = bridge_data["canvas"]
    width = int(canvas["width"])
    height = int(canvas["height"])
    mapped_panels = bridge_data["mapped_panels"]
    characters = bridge_data["characters"]
    local_regions = bridge_data["local_regions"]

    panel_masks: Dict[str, torch.Tensor] = {}
    for p in mapped_panels:
        pid = p["koma_id"]
        poly_pts = p["polygon_pixels"]
        panel_masks[pid] = render_polygon_mask(poly_pts, width, height)

    char_entries_built = []
    
    # Check if any mapped panels have SubScenes
    panels_with_subscenes = {}
    for p in mapped_panels:
        koma_obj = p["koma"]
        if has_active_subscenes(koma_obj):
            panels_with_subscenes[p["koma_id"]] = validate_panel_subscenes(koma_obj)

    # 1. Process Standard Character Instances (for panels WITHOUT subscenes)
    for c_idx, c in enumerate(characters):
        pid = c["koma_id"]
        if pid in panels_with_subscenes:
            # Characters for panels with subscenes are handled via subscene bindings below
            continue
            
        p_mask = panel_masks.get(pid, torch.ones((height, width), dtype=torch.float32))
        raw_rect = render_rect_mask(c["pixel_bounds"], width, height)
        # Clip character rectangle to panel polygon
        clipped_mask = raw_rect * p_mask
        if mask_feather > 0:
            clipped_mask = _apply_feather_single(clipped_mask, mask_feather)

        cid = c["character_id"]
        instance_id = f"p{pid}_{cid}_{c_idx:02d}"

        panel_info = next((p for p in mapped_panels if p["koma_id"] == pid), None)
        panel_prompt = ""
        panel_negative = ""
        if panel_info:
            koma_obj = panel_info["koma"]
            panel_prompt = koma_obj.get("panel", {}).get("prompt") or koma_obj.get("prompt", "")
            panel_negative = koma_obj.get("panel", {}).get("negative_prompt") or koma_obj.get("negative_prompt", "")

        char_prompt = c["clean_prompt"]
        char_neg = c["clean_negative_prompt"] or panel_negative

        if character_prompt_mode == "scene_composed" and panel_prompt:
            composed_prompt = f"{panel_prompt}, {char_prompt}" if char_prompt else panel_prompt
        else:
            composed_prompt = char_prompt

        entry = {
            "scope_type": "character_instance",
            "source_panel_id": pid,
            "source_scene_id": f"scene_p{pid}",
            "master_character_id": cid,
            "character_instance_id": instance_id,
            "character_name": c["character_name"],
            "prompt": composed_prompt,
            "negative_prompt": char_neg,
            "mask": clipped_mask,
            "priority": 300 if ordering_mode == "scene_first" else 100,
            "metadata": {
                "character_index": c["character_index"],
                "panel_index": c["panel_index"],
                "koma_local_area": c["koma_local_area"],
                "page_projected_area": c["page_projected_area"],
                "pixel_bounds": c["pixel_bounds"],
                "shot_type": c.get("shot_type") or c.get("metadata", {}).get("shot_type", "full_body")
            }
        }
        char_entries_built.append(entry)

    # 2. Process SubScene Character Instances (for panels WITH subscenes)
    subscene_entries_built = []
    for pid, subscenes in panels_with_subscenes.items():
        p_info = next(p for p in mapped_panels if p["koma_id"] == pid)
        p_mask = panel_masks[pid]
        p_bbox = p_info["bbox_pixels"]
        p_x0, p_y0, p_x1, p_y1 = p_bbox
        p_w = p_x1 - p_x0
        p_h = p_y1 - p_y0

        for s_idx, sub in enumerate(subscenes):
            sub_id = sub["id"]
            s_area = sub["area"]
            sub_px0 = int(p_x0 + s_area["x"] * p_w)
            sub_py0 = int(p_y0 + s_area["y"] * p_h)
            sub_px1 = int(sub_px0 + s_area["w"] * p_w)
            sub_py1 = int(sub_py0 + s_area["h"] * p_h)
            sub_bbox = (sub_px0, sub_py0, sub_px1, sub_py1)

            sub_raw_mask = render_rect_mask(sub_bbox, width, height)
            sub_clipped_mask = sub_raw_mask * p_mask
            if mask_feather > 0:
                sub_clipped_mask = _apply_feather_single(sub_clipped_mask, mask_feather)

            # Subscene scene entry
            if include_panel_backgrounds:
                s_entry = {
                    "scope_type": "subscene",
                    "source_panel_id": pid,
                    "source_scene_id": f"scene_p{pid}_{sub_id}",
                    "master_character_id": None,
                    "character_instance_id": None,
                    "prompt": sub["prompt"],
                    "negative_prompt": sub["negative_prompt"],
                    "mask": sub_clipped_mask,
                    "priority": 100 if ordering_mode == "scene_first" else 300,
                    "metadata": {
                        "subscene_id": sub_id,
                        "subscene_index": s_idx,
                        "panel_id": pid,
                        "area": s_area,
                        "bbox_pixels": sub_bbox
                    }
                }
                subscene_entries_built.append(s_entry)

            # Characters bound to this subscene
            for b_idx, b in enumerate(sub.get("character_bindings", [])):
                cid = b["character_id"]
                b_area = b.get("area") or {"x": 0.1, "y": 0.1, "w": 0.8, "h": 0.8}
                c_px0 = int(sub_px0 + b_area["x"] * (sub_px1 - sub_px0))
                c_py0 = int(sub_py0 + b_area["y"] * (sub_py1 - sub_py0))
                c_px1 = int(c_px0 + b_area["w"] * (sub_px1 - sub_px0))
                c_py1 = int(c_py0 + b_area["h"] * (sub_py1 - sub_py0))
                c_bbox = (c_px0, c_py0, c_px1, c_py1)

                c_raw_rect = render_rect_mask(c_bbox, width, height)
                c_clipped_mask = c_raw_rect * sub_clipped_mask
                if mask_feather > 0:
                    c_clipped_mask = _apply_feather_single(c_clipped_mask, mask_feather)

                instance_id = f"p{pid}_{sub_id}_{cid}_{b_idx:02d}"
                c_prompt = b.get("prompt_override", "")
                if character_prompt_mode == "scene_composed" and sub["prompt"]:
                    composed_c_prompt = f"{sub['prompt']}, {c_prompt}" if c_prompt else sub["prompt"]
                else:
                    composed_c_prompt = c_prompt

                c_entry = {
                    "scope_type": "character_instance",
                    "source_panel_id": pid,
                    "source_scene_id": f"scene_p{pid}_{sub_id}",
                    "master_character_id": cid,
                    "character_instance_id": instance_id,
                    "character_name": cid,
                    "prompt": composed_c_prompt,
                    "negative_prompt": b.get("negative_prompt_override") or sub["negative_prompt"],
                    "mask": c_clipped_mask,
                    "priority": 300 if ordering_mode == "scene_first" else 100,
                    "metadata": {
                        "subscene_id": sub_id,
                        "character_id": cid,
                        "binding_index": b_idx,
                        "area": b_area,
                        "pixel_bounds": c_bbox,
                        "shot_type": b.get("shot_type") or b.get("metadata", {}).get("shot_type", "full_body")
                    }
                }
                char_entries_built.append(c_entry)

    # 3. Process Local Regions
    lr_entries_built = []
    for l_idx, lr in enumerate(local_regions):
        pid = lr["koma_id"]
        p_mask = panel_masks.get(pid, torch.ones((height, width), dtype=torch.float32))
        raw_rect = render_rect_mask(lr["pixel_bounds"], width, height)
        clipped_mask = raw_rect * p_mask
        if mask_feather > 0:
            clipped_mask = _apply_feather_single(clipped_mask, mask_feather)

        entry = {
            "scope_type": "local_region",
            "source_panel_id": pid,
            "source_scene_id": f"scene_p{pid}",
            "master_character_id": None,
            "character_instance_id": None,
            "prompt": lr["prompt"],
            "negative_prompt": lr["negative_prompt"],
            "mask": clipped_mask,
            "priority": 200,
            "metadata": {
                "id": lr["id"],
                "name": lr["name"],
                "weight": lr["weight"],
                "page_projected_area": lr["page_projected_area"],
                "pixel_bounds": lr["pixel_bounds"]
            }
        }
        lr_entries_built.append(entry)

    # 4. Process Simple Panel Scenes (for panels WITHOUT subscenes)
    scene_entries_built = []
    if include_panel_backgrounds:
        for p in mapped_panels:
            pid = p["koma_id"]
            if pid in panels_with_subscenes:
                # Panel background already split into subscenes above
                continue

            p_mask = panel_masks[pid].clone()

            if remainder_mask_mode:
                # Subtract character and local region masks in this panel
                for c in char_entries_built:
                    if c["source_panel_id"] == pid:
                        p_mask = torch.clamp(p_mask - c["mask"], 0.0, 1.0)
                for lr in lr_entries_built:
                    if lr["source_panel_id"] == pid:
                        p_mask = torch.clamp(p_mask - lr["mask"], 0.0, 1.0)

            if mask_feather > 0:
                p_mask = _apply_feather_single(p_mask, mask_feather)

            koma_obj = p["koma"]
            panel_prompt = koma_obj.get("panel", {}).get("prompt") or koma_obj.get("prompt", "")
            panel_negative = koma_obj.get("panel", {}).get("negative_prompt") or koma_obj.get("negative_prompt", "")

            entry = {
                "scope_type": "panel_scene",
                "source_panel_id": pid,
                "source_scene_id": f"scene_p{pid}",
                "master_character_id": None,
                "character_instance_id": None,
                "prompt": panel_prompt,
                "negative_prompt": panel_negative,
                "mask": p_mask,
                "priority": 100 if ordering_mode == "scene_first" else 300,
                "metadata": {
                    "panel_index": p["index"],
                    "layout_panel_id": p["layout_panel_id"],
                    "bbox_pixels": p["bbox_pixels"],
                    "remainder_mask": remainder_mask_mode
                }
            }
            scene_entries_built.append(entry)

    # Total background scenes = simple panel scenes + subscenes
    all_scenes = scene_entries_built + subscene_entries_built

    if ordering_mode == "scene_first":
        all_entries = all_scenes + lr_entries_built + char_entries_built
    else:
        all_entries = char_entries_built + lr_entries_built + all_scenes

    all_entries.sort(key=lambda x: (x["priority"], str(x["source_panel_id"]), x.get("character_instance_id") or ""))

    for idx, e in enumerate(all_entries):
        e["region_index"] = idx

    return {
        "version": 1,
        "canvas": {"width": width, "height": height},
        "ordering_mode": ordering_mode,
        "character_prompt_mode": character_prompt_mode,
        "include_panel_backgrounds": include_panel_backgrounds,
        "remainder_mask_mode": remainder_mask_mode,
        "region_count": len(all_entries),
        "regions": all_entries,
        "summary": {
            "panel_count": len(mapped_panels),
            "character_instance_count": len(char_entries_built),
            "local_region_count": len(lr_entries_built),
            "subscene_count": len(subscene_entries_built),
            "total_regions": len(all_entries),
            "active_komas": [p["koma_id"] for p in mapped_panels],
            "character_instances": [c["character_instance_id"] for c in char_entries_built]
        }
    }
