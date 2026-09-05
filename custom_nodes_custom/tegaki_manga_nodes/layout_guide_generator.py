"""
Tegaki Manga Layout Guide Generator (Phase 3I)
==============================================
Synthesizes visual layout auxiliary guide images (mannequin capsules, wireframe boxes,
or silhouettes) directly from character staging metadata and panel topology.

These guide images serve as ControlNet (AnyTest / LineArt / Scribble) inputs to strictly
lock character scale, silhouette bounds, and perspective placement, resolving Case B
(Perspective Scale Shrinkage) in the progressive manga authoring pipeline.
"""

import json
import logging
from typing import Dict, Any, List, Optional, Tuple, Union

import torch
import numpy as np
from PIL import Image, ImageDraw

logger = logging.getLogger("tegaki.manga.layout_guide")


def _normalize_box(area: Any) -> Optional[List[float]]:
    """Normalizes box representation [x, y, w, h] from dict or list."""
    if isinstance(area, (list, tuple)) and len(area) >= 4:
        return [float(area[0]), float(area[1]), float(area[2]), float(area[3])]
    if isinstance(area, dict):
        x = float(area.get("x", 0.0))
        y = float(area.get("y", 0.0))
        w = float(area.get("w", area.get("width", 0.0)))
        h = float(area.get("h", area.get("height", 0.0)))
        return [x, y, w, h]
    return None


def extract_staging_boxes(
    scene_plan: Any,
    target_panel_id: int = 1
) -> Tuple[List[float], List[Dict[str, Any]]]:
    """
    Extracts panel box [px, py, pw, ph] and character staging boxes from various schema inputs:
    - MANGA_PAGE_PLAN (TegakiMangaPageCompiler)
    - REGION_SPEC (TegakiMangaCharacterStagingEditor)
    - TWO_REGION_SPEC (TegakiTwoRegionCoupleEditor)
    - Raw JSON string or dictionary
    """
    data = scene_plan
    if isinstance(data, str):
        trimmed = data.strip()
        if trimmed:
            try:
                data = json.loads(trimmed)
            except Exception as e:
                logger.warning(f"Failed to parse scene_plan JSON: {e}")
                data = {}
        else:
            data = {}

    if not isinstance(data, dict):
        return [0.05, 0.05, 0.90, 0.90], []

    # Case 0: PAGE_COMPILE_PLAN (TegakiMangaPageCompiler output)
    if "characters" in data and isinstance(data.get("characters"), list) and ("target_panel_id" in data or "panel" in data):
        panel_box = [0.05, 0.05, 0.90, 0.90]
        p_obj = data.get("panel")
        if isinstance(p_obj, dict):
            p_geo = p_obj.get("geometry", {})
            if p_geo:
                p_norm = _normalize_box(p_geo)
                if p_norm:
                    panel_box = p_norm
        char_boxes = []
        for c in data.get("characters", []):
            if not c.get("enabled", True):
                continue
            area = c.get("area") or c.get("bounding_box") or c.get("box_area")
            box = _normalize_box(area)
            if box and box[2] > 0 and box[3] > 0:
                char_boxes.append({
                    "id": c.get("character_id", c.get("id", "char")),
                    "box": box,
                    "name": c.get("name", "Character")
                })
        return panel_box, char_boxes

    # Case 1: TWO_REGION_SPEC (Phase 3C Oracle)
    if "regions" in data and any(r.get("id") in ("A", "B") for r in data.get("regions", [])):
        panel_box = [0.05, 0.05, 0.90, 0.90]
        char_boxes = []
        for reg in data.get("regions", []):
            if not reg.get("enabled", True):
                continue
            box = _normalize_box(reg)
            if box and box[2] > 0 and box[3] > 0:
                char_boxes.append({
                    "id": reg.get("id", "char"),
                    "box": box,
                    "name": reg.get("label", reg.get("id", "Character"))
                })
        return panel_box, char_boxes

    # Case 2: MANGA_PAGE_PLAN / PAGE_COMPILE_PLAN
    if "panels" in data:
        panel_box = [0.05, 0.05, 0.90, 0.90]
        char_boxes = []
        panels = data.get("panels", [])
        for p in panels:
            pid = p.get("target_panel_id", p.get("panel_id", p.get("id")))
            if pid == target_panel_id or str(pid) == str(target_panel_id):
                p_geo = p.get("geometry", {}) or (p.get("panel", {}).get("geometry", {}) if isinstance(p.get("panel"), dict) else {})
                if p_geo:
                    p_norm = _normalize_box(p_geo)
                    if p_norm:
                        panel_box = p_norm
                chars = p.get("characters", [])
                for c in chars:
                    if not c.get("enabled", True):
                        continue
                    area = c.get("area") or c.get("bounding_box") or c.get("box_area")
                    box = _normalize_box(area)
                    if box and box[2] > 0 and box[3] > 0:
                        char_boxes.append({
                            "id": c.get("character_id", c.get("id", "char")),
                            "box": box,
                            "name": c.get("name", "Character")
                        })
                break
        return panel_box, char_boxes

    # Case 3: REGION_SPEC (CharacterStagingEditor output)
    if "regions" in data:
        panel_box = [0.05, 0.05, 0.90, 0.90]
        char_boxes = []
        regions = data.get("regions", [])
        for r in regions:
            rid = r.get("id")
            if rid == target_panel_id:
                chars = r.get("characters", [])
                for c in chars:
                    if not c.get("enabled", True):
                        continue
                    area = c.get("area") or c.get("box_area") or c.get("bounding_box")
                    box = _normalize_box(area)
                    if box and box[2] > 0 and box[3] > 0:
                        char_boxes.append({
                            "id": c.get("character_id", c.get("id", "char")),
                            "box": box,
                            "name": c.get("name", "Character")
                        })
                break
        return panel_box, char_boxes

    # Case 4: Simple staging_boxes format
    if "staging_boxes" in data:
        panel_box = _normalize_box(data.get("panel_box")) or [0.05, 0.05, 0.90, 0.90]
        char_boxes = []
        for sb in data.get("staging_boxes", []):
            raw_b = sb.get("staging_box") or sb.get("box") or sb.get("area") or sb.get("bounds")
            box = _normalize_box(raw_b)
            if box and box[2] > 0 and box[3] > 0:
                char_boxes.append({
                    "id": sb.get("id", sb.get("character", "char")),
                    "box": box,
                    "name": sb.get("name", sb.get("character", "Character"))
                })
        return panel_box, char_boxes

    return [0.05, 0.05, 0.90, 0.90], []


class TegakiMangaLayoutGuideGenerator:
    """
    Tegaki Manga Layout Guide Generator (Phase 3I)
    Synthesizes clean visual layout guides for ControlNet auxiliary conditioning.
    """
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "scene_plan": ("*",),
                "target_panel_id": ("INT", {"default": 1, "min": 1, "max": 8, "step": 1}),
                "guide_style": (["mannequin_capsule", "box_wireframe", "flat_silhouette"], {"default": "mannequin_capsule"}),
                "color_mode": (["Black on White", "White on Black"], {"default": "Black on White"}),
                "line_thickness": ("INT", {"default": 4, "min": 1, "max": 32, "step": 1}),
                "include_panel_border": ("BOOLEAN", {"default": True}),
                "width": ("INT", {"default": 1024, "min": 512, "max": 2048, "step": 64}),
                "height": ("INT", {"default": 1024, "min": 512, "max": 2048, "step": 64}),
            }
        }

    RETURN_TYPES = ("IMAGE", "MASK", "STRING")
    RETURN_NAMES = ("guide_image", "layout_mask", "debug_json")
    FUNCTION = "generate_guide"
    CATEGORY = "tegaki/manga/authoring"

    def generate_guide(
        self,
        scene_plan: Any,
        target_panel_id: int = 1,
        guide_style: str = "mannequin_capsule",
        color_mode: str = "Black on White",
        line_thickness: int = 4,
        include_panel_border: bool = True,
        width: int = 1024,
        height: int = 1024
    ) -> Tuple[torch.Tensor, torch.Tensor, str]:
        W, H = int(width), int(height)
        panel_box, char_boxes = extract_staging_boxes(scene_plan, target_panel_id)

        # Set up color scheme
        if color_mode == "White on Black":
            bg_color = (0, 0, 0)
            fg_color = (255, 255, 255)
            box_outline_color = (100, 100, 100)
            fill_color = (255, 255, 255)
        else:  # Black on White (default for manga linework)
            bg_color = (255, 255, 255)
            fg_color = (0, 0, 0)
            box_outline_color = (190, 190, 190)
            fill_color = (0, 0, 0)

        img = Image.new("RGB", (W, H), bg_color)
        draw = ImageDraw.Draw(img)
        mask_tensor = torch.zeros((1, H, W), dtype=torch.float32)

        # 1. Draw Panel Frame Outline
        px0 = int(round(panel_box[0] * W))
        py0 = int(round(panel_box[1] * H))
        pw = int(round(panel_box[2] * W))
        ph = int(round(panel_box[3] * H))
        px1 = min(W - 1, px0 + pw)
        py1 = min(H - 1, py0 + ph)

        if include_panel_border:
            border_width = max(line_thickness + 2, 6)
            draw.rectangle([px0, py0, px1, py1], outline=fg_color, width=border_width)

        # 2. Draw Character Guides
        for char_info in char_boxes:
            cbox = char_info["box"]
            # Coordinates are relative to panel box or canvas
            # If coordinates are normalized to [0, 1], map relative to panel interior
            rx0 = px0 + int(round(cbox[0] * pw))
            ry0 = py0 + int(round(cbox[1] * ph))
            rw = int(round(cbox[2] * pw))
            rh = int(round(cbox[3] * ph))
            rx1 = min(W - 1, rx0 + rw)
            ry1 = min(H - 1, ry0 + rh)

            cw = rx1 - rx0
            ch = ry1 - ry0
            if cw <= 4 or ch <= 4:
                continue

            cx = rx0 + cw // 2

            # Update layout mask
            mask_tensor[0, ry0:ry1, rx0:rx1] = 1.0

            if guide_style == "mannequin_capsule":
                # Subtly mark the bounding box bounds
                draw.rectangle([rx0, ry0, rx1, ry1], outline=box_outline_color, width=max(1, line_thickness // 2))

                # Head oval
                r_head_x = max(4, int(cw * 0.22))
                r_head_y = max(4, int(ch * 0.11))
                head_cy = ry0 + int(ch * 0.12)
                draw.ellipse(
                    [cx - r_head_x, head_cy - r_head_y, cx + r_head_x, head_cy + r_head_y],
                    outline=fg_color,
                    width=line_thickness
                )

                # Neck
                neck_top = head_cy + r_head_y
                neck_bot = ry0 + int(ch * 0.27)
                if neck_bot > neck_top:
                    draw.line([(cx, neck_top), (cx, neck_bot)], fill=fg_color, width=line_thickness)

                # Shoulders
                sh_w = max(4, int(cw * 0.35))
                draw.line([(cx - sh_w, neck_bot), (cx + sh_w, neck_bot)], fill=fg_color, width=line_thickness)

                # Torso
                torso_bot = ry0 + int(ch * 0.58)
                draw.rectangle(
                    [cx - int(cw * 0.22), neck_bot, cx + int(cw * 0.22), torso_bot],
                    outline=fg_color,
                    width=line_thickness
                )

                # Pelvis
                draw.line([(cx - int(cw * 0.25), torso_bot), (cx + int(cw * 0.25), torso_bot)], fill=fg_color, width=line_thickness)

                # Legs
                knee_y = ry0 + int(ch * 0.78)
                leg_l = cx - int(cw * 0.12)
                leg_r = cx + int(cw * 0.12)
                draw.line([(leg_l, torso_bot), (leg_l, knee_y), (leg_l, ry1 - 2)], fill=fg_color, width=line_thickness)
                draw.line([(leg_r, torso_bot), (leg_r, knee_y), (leg_r, ry1 - 2)], fill=fg_color, width=line_thickness)

                # Arms
                elbow_y = ry0 + int(ch * 0.45)
                hand_y = ry0 + int(ch * 0.62)
                arm_l_elbow = cx - int(cw * 0.40)
                arm_r_elbow = cx + int(cw * 0.40)
                arm_l_hand = cx - int(cw * 0.35)
                arm_r_hand = cx + int(cw * 0.35)
                draw.line([(cx - sh_w, neck_bot), (arm_l_elbow, elbow_y), (arm_l_hand, hand_y)], fill=fg_color, width=line_thickness)
                draw.line([(cx + sh_w, neck_bot), (arm_r_elbow, elbow_y), (arm_r_hand, hand_y)], fill=fg_color, width=line_thickness)

            elif guide_style == "box_wireframe":
                # Outer rectangle
                draw.rectangle([rx0, ry0, rx1, ry1], outline=fg_color, width=line_thickness)
                # Diagonal cross
                draw.line([(rx0, ry0), (rx1, ry1)], fill=box_outline_color, width=max(1, line_thickness // 2))
                draw.line([(rx0, ry1), (rx1, ry0)], fill=box_outline_color, width=max(1, line_thickness // 2))
                # Head indicator circle
                r_head = min(cw, ch) // 5
                draw.ellipse([cx - r_head, ry0 + 4, cx + r_head, ry0 + 4 + 2 * r_head], outline=fg_color, width=line_thickness)

            elif guide_style == "flat_silhouette":
                # Head circle fill
                r_head_x = max(4, int(cw * 0.22))
                r_head_y = max(4, int(ch * 0.11))
                head_cy = ry0 + int(ch * 0.12)
                draw.ellipse([cx - r_head_x, head_cy - r_head_y, cx + r_head_x, head_cy + r_head_y], fill=fill_color)

                # Body rounded rectangle fill
                body_y0 = ry0 + int(ch * 0.24)
                draw.rounded_rectangle([cx - int(cw * 0.30), body_y0, cx + int(cw * 0.30), ry1 - 2], radius=int(cw * 0.10), fill=fill_color)

        # Convert PIL Image to PyTorch Tensor [1, H, W, 3] in range [0.0, 1.0]
        np_img = np.array(img).astype(np.float32) / 255.0
        tensor_img = torch.from_numpy(np_img).unsqueeze(0)

        debug_info = {
            "target_panel_id": target_panel_id,
            "guide_style": guide_style,
            "color_mode": color_mode,
            "canvas_size": [W, H],
            "panel_box": panel_box,
            "extracted_characters": len(char_boxes),
            "characters": char_boxes
        }

        return (tensor_img, mask_tensor, json.dumps(debug_info, indent=2, ensure_ascii=False))
