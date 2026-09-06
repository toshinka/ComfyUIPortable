"""
authoring_visual_frame_bridge.py — M3A.1 Visual Frame Adapter and Deterministic Renderer
=========================================================================================
M3A.1 corrections applied:
- derive_panel_layout_spec_from_frames([]) returns None (no fake full-frame guide for 0 frames)
- render_deterministic_frame_overlay implements comic_panels semantics:
    * white page background (gutter/margins)
    * source image visible inside each frame rectangle (no crop/rescale)
    * per-frame border_thickness honored; global line_thickness is fallback only
    * black deterministic border lines on top
- Canonical geometry key is area; shape is legacy import boundary only
"""
import logging
from typing import Dict, Any, List, Optional, Tuple

import numpy as np
from PIL import Image, ImageDraw

try:
    import torch
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

logger = logging.getLogger(__name__)


def _get_frame_area(f: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Canonical geometry key resolution: area takes priority over legacy shape.
    Returns None if neither key is valid.
    """
    area = f.get("area")
    if area and isinstance(area, dict) and "x" in area and "w" in area:
        return area
    shape = f.get("shape")
    if shape and isinstance(shape, dict) and "x" in shape and "w" in shape:
        return shape
    return None


def derive_panel_layout_spec_from_frames(
    visual_frames: List[Dict[str, Any]],
    canvas_width: int = 832,
    canvas_height: int = 1216,
) -> Optional[Dict[str, Any]]:
    """
    Converts list of visual frame dicts into a validated PANEL_LAYOUT_SPEC (v1).
    Each rectangular visual frame creates 4 vertices and 1 CCW panel.

    Returns None when visual_frames is empty.
    M3A.1 policy: 0 frames => guide OFF. Do NOT fabricate a full-frame layout.
    Callers must check for None before using the result.
    """
    if not visual_frames:
        return None

    W = int(canvas_width)
    H = int(canvas_height)

    vertices = []
    panels = []
    min_x, min_y = 1.0, 1.0
    max_r, max_b = 0.0, 0.0

    for idx, f in enumerate(visual_frames):
        fid = f.get("frame_id", f"frame_{idx + 1}")
        b = _get_frame_area(f) or {"x": 0.05, "y": 0.05, "w": 0.90, "h": 0.90}
        x = float(b.get("x", 0.05))
        y = float(b.get("y", 0.05))
        w = float(b.get("w", 0.90))
        h = float(b.get("h", 0.90))
        r = x + w
        bot = y + h

        min_x = min(min_x, x)
        min_y = min(min_y, y)
        max_r = max(max_r, r)
        max_b = max(max_b, bot)

        v_tl = f"v_{fid}_tl"
        v_tr = f"v_{fid}_tr"
        v_br = f"v_{fid}_br"
        v_bl = f"v_{fid}_bl"

        vertices.extend([
            {"id": v_tl, "x": round(x, 4), "y": round(y, 4)},
            {"id": v_tr, "x": round(r, 4), "y": round(y, 4)},
            {"id": v_br, "x": round(r, 4), "y": round(bot, 4)},
            {"id": v_bl, "x": round(x, 4), "y": round(bot, 4)},
        ])

        panels.append({
            "id": f"panel_{fid}",
            "vertex_ids": [v_tl, v_bl, v_br, v_tr]
        })

    frame_rect = {
        "x": round(max(0.0, min_x), 4),
        "y": round(max(0.0, min_y), 4),
        "w": round(min(1.0 - min_x, max_r - min_x), 4),
        "h": round(min(1.0 - min_y, max_b - min_y), 4),
    }

    return {
        "version": 1,
        "canvas": {"width": W, "height": H},
        "frame": frame_rect,
        "vertices": vertices,
        "panels": panels,
        "metadata": {
            "derived_from": "visual_frames",
            "frame_count": len(visual_frames)
        }
    }


def _render_single_pil_overlay(
    img: Image.Image,
    visual_frames: List[Dict[str, Any]],
    global_line_thickness: int = 4,
    bg_color: Tuple[int, int, int] = (255, 255, 255),
    border_color: Tuple[int, int, int] = (0, 0, 0),
) -> Tuple[Image.Image, Image.Image]:
    """
    Comic-panels semantics renderer (M3A.1):
    1. Start with white canvas (gutter/margin).
    2. Paste source image inside each frame rectangle (no crop/rescale).
    3. Draw black border lines using per-frame border_thickness (fallback: global).
    4. Areas outside all frame interiors remain white.

    Returns (result_image, border_mask).
    """
    W, H = img.size
    # Step 1: white canvas
    result = Image.new("RGB", (W, H), bg_color)
    mask = Image.new("L", (W, H), 0)
    source_rgb = img.convert("RGB")

    # Step 2: paste source inside each frame
    for f in visual_frames:
        b = _get_frame_area(f) or {}
        x = float(b.get("x", 0.0))
        y = float(b.get("y", 0.0))
        w = float(b.get("w", 0.0))
        h = float(b.get("h", 0.0))
        if w <= 0 or h <= 0:
            continue

        rx0 = max(0, int(round(x * W)))
        ry0 = max(0, int(round(y * H)))
        rx1 = min(W, int(round((x + w) * W)))
        ry1 = min(H, int(round((y + h) * H)))

        if rx1 > rx0 and ry1 > ry0:
            source_crop = source_rgb.crop((rx0, ry0, rx1, ry1))
            result.paste(source_crop, (rx0, ry0))

    # Step 3: draw borders on top
    result_draw = ImageDraw.Draw(result)
    mask_draw = ImageDraw.Draw(mask)
    for f in visual_frames:
        b = _get_frame_area(f) or {}
        x = float(b.get("x", 0.0))
        y = float(b.get("y", 0.0))
        w = float(b.get("w", 0.0))
        h = float(b.get("h", 0.0))
        if w <= 0 or h <= 0:
            continue

        rx0 = max(0, int(round(x * W)))
        ry0 = max(0, int(round(y * H)))
        rx1 = min(W, int(round((x + w) * W)))
        ry1 = min(H, int(round((y + h) * H)))

        if rx1 > rx0 and ry1 > ry0:
            raw_t = f.get("border_thickness")
            if raw_t is not None:
                try:
                    lt = max(1, min(64, int(raw_t)))
                except (TypeError, ValueError):
                    lt = max(1, int(global_line_thickness))
            else:
                lt = max(1, int(global_line_thickness))

            result_draw.rectangle([rx0, ry0, rx1 - 1, ry1 - 1], outline=border_color, width=lt)
            mask_draw.rectangle([rx0, ry0, rx1 - 1, ry1 - 1], outline=255, width=lt)

    return result, mask


def render_deterministic_frame_overlay(
    image_tensor_or_pil,
    visual_frames: List[Dict[str, Any]],
    line_thickness: int = 4,
    gutter_mask_outside: bool = False,
    bg_margin_color: Tuple[int, int, int] = (255, 255, 255),
    border_color: Tuple[int, int, int] = (0, 0, 0),
):
    """
    Deterministically overlay crisp panel borders and white gutters on an image.
    When visual_frames is empty ([]), strictly passes through original image pixel-identical.

    Comic-panels render mode (M3A.1):
    - white page background
    - source image pasted inside each frame rect (no crop/rescale)
    - per-frame black borders (fallback to global line_thickness)
    - outside all frames = white gutter

    Returns: (framed_image, frame_mask)
    """
    if not visual_frames:
        if HAS_TORCH and isinstance(image_tensor_or_pil, torch.Tensor):
            t = image_tensor_or_pil
            B = t.shape[0] if t.ndim == 4 else 1
            H = t.shape[1] if t.ndim == 4 else t.shape[0]
            W = t.shape[2] if t.ndim == 4 else t.shape[1]
            empty_mask = torch.zeros((B, H, W), dtype=torch.float32, device=t.device)
            return t, empty_mask
        elif isinstance(image_tensor_or_pil, Image.Image):
            W2, H2 = image_tensor_or_pil.size
            return image_tensor_or_pil, Image.new("L", (W2, H2), 0)
        else:
            return image_tensor_or_pil, None

    is_tensor = HAS_TORCH and isinstance(image_tensor_or_pil, torch.Tensor)
    if is_tensor:
        tensor = image_tensor_or_pil
        if tensor.ndim == 4:
            B, H, W, C = tensor.shape
            framed_batches = []
            mask_batches = []
            for b in range(B):
                single_np = (tensor[b].cpu().numpy() * 255.0).clip(0, 255).astype(np.uint8)
                single_pil = Image.fromarray(single_np)
                f_pil, m_pil = _render_single_pil_overlay(
                    single_pil, visual_frames, line_thickness, bg_margin_color, border_color
                )
                framed_batches.append(np.array(f_pil).astype(np.float32) / 255.0)
                mask_batches.append(np.array(m_pil).astype(np.float32) / 255.0)
            framed_out = torch.from_numpy(np.stack(framed_batches, axis=0)).to(tensor.device)
            mask_out = torch.from_numpy(np.stack(mask_batches, axis=0)).to(tensor.device)
            return framed_out, mask_out
        elif tensor.ndim == 3:
            H, W, C = tensor.shape
            single_np = (tensor.cpu().numpy() * 255.0).clip(0, 255).astype(np.uint8)
            single_pil = Image.fromarray(single_np)
            f_pil, m_pil = _render_single_pil_overlay(
                single_pil, visual_frames, line_thickness, bg_margin_color, border_color
            )
            framed_out = torch.from_numpy(np.array(f_pil).astype(np.float32) / 255.0).unsqueeze(0).to(tensor.device)
            mask_out = torch.from_numpy(np.array(m_pil).astype(np.float32) / 255.0).unsqueeze(0).to(tensor.device)
            return framed_out, mask_out

    if isinstance(image_tensor_or_pil, Image.Image):
        return _render_single_pil_overlay(
            image_tensor_or_pil, visual_frames, line_thickness, bg_margin_color, border_color
        )

    return image_tensor_or_pil, None
