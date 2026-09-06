"""
frame_overlay.py — Tegaki Manga Frame Overlay Node (Phase 3M-3A)
================================================================
Pure deterministic post-process node that renders crisp comic panel frames
and gutters onto generated images based on `page.visual_frames`.
Zero diffusion artifacts, zero seed dependency.
When `visual_frames` is empty, acts as a pure pass-through.
"""
import json
import logging
from typing import Dict, Any, Tuple, Optional

import torch
from .authoring_visual_frame_bridge import render_deterministic_frame_overlay

logger = logging.getLogger(__name__)


class TegakiMangaFrameOverlay:
    """
    Tegaki Manga Frame Overlay (Deterministic Panel Borders)
    Inputs:
    - image: generated IMAGE tensor from VAEDecode
    - authoring_document_json: TEGAKI_AUTHORING_DOCUMENT string from TegakiMinimumHandSceneEditor
    - line_thickness: integer pixel thickness of panel borders (default 4)
    - page_index: page to read visual_frames from (default 0)
    Outputs:
    - image: framed IMAGE tensor
    - frame_mask: MASK tensor (1.0 at border pixels)
    - debug_json: execution provenance JSON
    """
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "line_thickness": ("INT", {"default": 4, "min": 1, "max": 32, "step": 1}),
            },
            "optional": {
                "authoring_document_json": ("STRING", {"multiline": True, "default": ""}),
                "page_index": ("INT", {"default": 0, "min": 0, "max": 64, "step": 1}),
            }
        }

    RETURN_TYPES = ("IMAGE", "MASK", "STRING")
    RETURN_NAMES = ("image", "frame_mask", "debug_json")
    FUNCTION = "apply_overlay"
    CATEGORY = "tegaki/manga/frame"

    def apply_overlay(
        self,
        image: torch.Tensor,
        line_thickness: int = 4,
        authoring_document_json: str = "",
        page_index: int = 0,
    ) -> Tuple[torch.Tensor, torch.Tensor, str]:
        visual_frames = []
        doc_id = "unknown"
        frame_count = 0

        raw_str = (authoring_document_json or "").strip()
        if raw_str:
            try:
                doc = json.loads(raw_str)
                doc_id = doc.get("document_id", "unknown")
                pages = doc.get("pages", [])
                if 0 <= page_index < len(pages):
                    p = pages[page_index]
                    visual_frames = p.get("visual_frames", [])
                    frame_count = len(visual_frames)
            except Exception as e:
                logger.warning(f"[TegakiMangaFrameOverlay] Failed to parse authoring_document_json: {e}")

        # Deterministically composite frame lines
        framed_img, frame_mask = render_deterministic_frame_overlay(
            image,
            visual_frames=visual_frames,
            line_thickness=int(line_thickness),
            border_color=(0, 0, 0),
        )

        debug_info = {
            "node": "TegakiMangaFrameOverlay",
            "document_id": doc_id,
            "page_index": page_index,
            "frame_count": frame_count,
            "visual_frames": visual_frames,
            "line_thickness": int(line_thickness),
            "status": "PASS",
            "mode": "deterministic_overlay" if frame_count > 0 else "pass_through",
        }
        debug_json = json.dumps(debug_info, indent=2, ensure_ascii=False)

        return (framed_img, frame_mask, debug_json)
