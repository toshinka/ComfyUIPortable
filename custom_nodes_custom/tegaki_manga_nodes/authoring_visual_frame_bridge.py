"""
authoring_visual_frame_bridge.py — M3A Visual Frame Adapter and Deterministic Renderer
======================================================================================
Provides pure adapters and deterministic rendering operations for visual panel frames:
1. derive_panel_layout_spec_from_frames: Adapts page.visual_frames to PANEL_LAYOUT_SPEC
   for layout guide generators and ControlNet wireframes without mutating authoring SSOT.
2. render_deterministic_frame_overlay: Pure deterministic compositing of crisp black frame
   borders and white page gutters directly onto generated RGB image tensors.
"""
import copy
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


def derive_panel_layout_spec_from_frames(
    visual_frames: List[Dict[str, Any]],
    canvas_width: int = 832,
    canvas_height: int = 1216,
) -> Dict[str, Any]:
    """
    Converts list of visual frame dicts into a validated PANEL_LAYOUT_SPEC (v1).
    Each rectangular visual frame creates 4 vertices and 1 CCW panel.
    If visual_frames is empty, creates a single full-bleed layout frame.
    """
    W = int(canvas_width)
    H = int(canvas_height)

    if not visual_frames:
        frame = {"x": 0.05, "y": 0.05, "w": 0.90, "h": 0.90}
        vertices = [
            {"id": "v_tl", "x": 0.05, "y": 0.05},
            {"id": "v_tr", "x": 0.95, "y": 0.05},
            {"id": "v_br", "x": 0.95, "y": 0.95},
            {"id": "v_bl", "x": 0.05, "y": 0.95},
        ]
        panels = [{"id": "p_full", "vertex_ids": ["v_tl", "v_bl", "v_br", "v_tr"]}]
        return {
            "version": 1,
            "canvas": {"width": W, "height": H},
            "frame": frame,
            "vertices": vertices,
            "panels": panels,
            "metadata": {"derived_from": "visual_frames_empty"}
        }

    vertices = []
    panels = []
    min_x, min_y = 1.0, 1.0
    max_r, max_b = 0.0, 0.0

    for idx, f in enumerate(visual_frames):
        fid = f.get("frame_id", f"frame_{idx + 1}")
        b = f.get("shape") or f.get("area") or {"x": 0.05, "y": 0.05, "w": 0.90, "h": 0.90}
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
    line_thickness: int = 4,
    gutter_mask_outside: bool = False,
    bg_margin_color: Tuple[int, int, int] = (255, 255, 255),
    border_color: Tuple[int, int, int] = (0, 0, 0),
) -> Tuple[Image.Image, Image.Image]:
    """Render border lines and gutters onto a single PIL Image."""
    W, H = img.size
    result = img.copy().convert("RGB")
    draw = ImageDraw.Draw(result)
    mask = Image.new("L", (W, H), 0)
    mask_draw = ImageDraw.Draw(mask)

    lt = max(1, int(line_thickness))

    for f in visual_frames:
        b = f.get("shape") or f.get("area") or {}
        x = float(b.get("x", 0.05))
        y = float(b.get("y", 0.05))
        w = float(b.get("w", 0.90))
        h = float(b.get("h", 0.90))

        rx0 = int(round(x * W))
        ry0 = int(round(y * H))
        rx1 = int(round((x + w) * W))
        ry1 = int(round((y + h) * H))

        rx0 = max(0, min(W - 1, rx0))
        ry0 = max(0, min(H - 1, ry0))
        rx1 = max(0, min(W - 1, rx1))
        ry1 = max(0, min(H - 1, ry1))

        if rx1 > rx0 and ry1 > ry0:
            draw.rectangle([rx0, ry0, rx1, ry1], outline=border_color, width=lt)
            mask_draw.rectangle([rx0, ry0, rx1, ry1], outline=255, width=lt)

    return result, mask


def render_deterministic_frame_overlay(
    image_tensor_or_pil: Any,
    visual_frames: List[Dict[str, Any]],
    line_thickness: int = 4,
    gutter_mask_outside: bool = False,
    bg_margin_color: Tuple[int, int, int] = (255, 255, 255),
    border_color: Tuple[int, int, int] = (0, 0, 0),
) -> Tuple[Any, Any]:
    """
    Deterministically overlay crisp panel borders and optional gutters on an image.
    When visual_frames is empty ([]), strictly passes through original image.

    Returns: (framed_image, frame_mask)
    """
    if not visual_frames:
        if HAS_TORCH and isinstance(image_tensor_or_pil, torch.Tensor):
            B = image_tensor_or_pil.shape[0] if image_tensor_or_pil.ndim == 4 else 1
            H = image_tensor_or_pil.shape[1] if image_tensor_or_pil.ndim == 4 else image_tensor_or_pil.shape[0]
            W = image_tensor_or_pil.shape[2] if image_tensor_or_pil.ndim == 4 else image_tensor_or_pil.shape[1]
            empty_mask = torch.zeros((B, H, W), dtype=torch.float32, device=image_tensor_or_pil.device)
            return image_tensor_or_pil, empty_mask
        elif isinstance(image_tensor_or_pil, Image.Image):
            W, H = image_tensor_or_pil.size
            empty_mask = Image.new("L", (W, H), 0)
            return image_tensor_or_pil, empty_mask
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
                    single_pil, visual_frames, line_thickness, gutter_mask_outside, bg_margin_color, border_color
                )
                f_np = np.array(f_pil).astype(np.float32) / 255.0
                m_np = np.array(m_pil).astype(np.float32) / 255.0
                framed_batches.append(f_np)
                mask_batches.append(m_np)
            framed_out = torch.from_numpy(np.stack(framed_batches, axis=0)).to(tensor.device)
            mask_out = torch.from_numpy(np.stack(mask_batches, axis=0)).to(tensor.device)
            return framed_out, mask_out
        elif tensor.ndim == 3:
            H, W, C = tensor.shape
            single_np = (tensor.cpu().numpy() * 255.0).clip(0, 255).astype(np.uint8)
            single_pil = Image.fromarray(single_np)
            f_pil, m_pil = _render_single_pil_overlay(
                single_pil, visual_frames, line_thickness, gutter_mask_outside, bg_margin_color, border_color
            )
            f_np = np.array(f_pil).astype(np.float32) / 255.0
            m_np = np.array(m_pil).astype(np.float32) / 255.0
            framed_out = torch.from_numpy(f_np).unsqueeze(0).to(tensor.device)
            mask_out = torch.from_numpy(m_np).unsqueeze(0).to(tensor.device)
            return framed_out, mask_out

    if isinstance(image_tensor_or_pil, Image.Image):
        return _render_single_pil_overlay(
            image_tensor_or_pil, visual_frames, line_thickness, gutter_mask_outside, bg_margin_color, border_color
        )

    return image_tensor_or_pil, None
