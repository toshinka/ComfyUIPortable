"""
frame_overlay.py — Tegaki Manga Frame Overlay Node (Phase 3M-3A.1)
================================================================
M3A.1 corrections applied:
- Fail-closed on invalid JSON (explicit error status, not silent pass-through)
- Fail-closed on page_index out-of-range
- Valid document with 0 frames => pass-through PASS (this is legal)
- Rich debug_json with validation_status, resolved_page_index, per-frame effective info
- Per-frame border_thickness honored via authoring_visual_frame_bridge
"""
import json
import logging
from typing import Dict, Any, Tuple, Optional

import torch
from .authoring_visual_frame_bridge import render_deterministic_frame_overlay

logger = logging.getLogger(__name__)


class TegakiMangaFrameOverlay:
    """
    Tegaki Manga Frame Overlay (Deterministic Panel Borders) — M3A.1

    Fail-closed contract:
    - Invalid JSON => validation_status=ERROR, output error debug_json, pass-through image
    - Page index out-of-range => validation_status=ERROR
    - Valid document + 0 frames => pass-through PASS (legal)
    - Valid document + N frames => comic_panels render (white gutter + source cutout + black borders)

    Inputs:
    - image: generated IMAGE tensor from VAEDecode
    - line_thickness: global fallback border thickness (per-frame thickness in document takes priority)
    - authoring_document_json: TEGAKI_AUTHORING_DOCUMENT string (linked from TegakiMinimumHandSceneEditor)
    - page_index: page to read visual_frames from (default 0; product workflow always 0)
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
        validation_status = "PASS"
        validation_error = None
        resolved_page_index = page_index
        render_mode = "pass_through"

        raw_str = (authoring_document_json or "").strip()

        if raw_str:
            # Step 1: Parse JSON (fail-closed on parse error)
            try:
                doc = json.loads(raw_str)
            except json.JSONDecodeError as e:
                validation_status = "ERROR"
                validation_error = f"JSON parse failed: {e}"
                doc = None

            if doc is not None:
                doc_id = doc.get("document_id", "unknown")
                pages = doc.get("pages", [])

                # Step 2: Resolve page_index (fail-closed on out-of-range)
                if not isinstance(pages, list) or len(pages) == 0:
                    validation_status = "ERROR"
                    validation_error = "Document has no pages"
                elif not (0 <= page_index < len(pages)):
                    validation_status = "ERROR"
                    validation_error = (
                        f"page_index {page_index} out of range "
                        f"(document has {len(pages)} page(s))"
                    )
                else:
                    p = pages[page_index]
                    visual_frames = p.get("visual_frames", [])
                    frame_count = len(visual_frames)
                    render_mode = "comic_panels" if frame_count > 0 else "pass_through"

        # Build per-frame debug info
        frame_debug = []
        for f in visual_frames:
            raw_t = f.get("border_thickness")
            try:
                effective_t = max(1, min(64, int(raw_t))) if raw_t is not None else int(line_thickness)
            except (TypeError, ValueError):
                effective_t = int(line_thickness)
            b = f.get("area") or f.get("shape") or {}
            frame_debug.append({
                "frame_id": f.get("frame_id", "unknown"),
                "effective_area": b,
                "effective_border_thickness": effective_t,
            })

        # Step 3: Render (or pass-through on error/0-frames)
        if validation_status == "ERROR":
            # Fail-closed: log error, pass image through, report error in debug_json
            logger.error(f"[TegakiMangaFrameOverlay] {validation_error}")
            if image.ndim == 4:
                B, H, W, C = image.shape
                empty_mask = torch.zeros((B, H, W), dtype=torch.float32, device=image.device)
            else:
                H, W, C = image.shape
                empty_mask = torch.zeros((1, H, W), dtype=torch.float32, device=image.device)
            framed_img = image
            frame_mask = empty_mask
            render_mode = "error_pass_through"
        else:
            framed_img, frame_mask = render_deterministic_frame_overlay(
                image,
                visual_frames=visual_frames,
                line_thickness=int(line_thickness),
                border_color=(0, 0, 0),
            )

        debug_info = {
            "node": "TegakiMangaFrameOverlay",
            "document_id": doc_id,
            "resolved_page_index": resolved_page_index,
            "frame_count": frame_count,
            "render_mode": render_mode,
            "validation_status": validation_status,
            "global_line_thickness_fallback": int(line_thickness),
            "frames": frame_debug,
            "status": "PASS" if validation_status == "PASS" else "ERROR",
        }
        if validation_error:
            debug_info["error"] = validation_error

        debug_json = json.dumps(debug_info, indent=2, ensure_ascii=False)
        return (framed_img, frame_mask, debug_json)
