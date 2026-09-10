"""
generation_guide_bridge.py — M3B-PI1 Deterministic CLEAN Generation Guide Bridge.

Promotes qualified M3B research CLEAN Guide architecture into production.
Transforms authoring document rough_manga Guide Figure geometry into a
deterministic, page-sized, pure black/white flat-silhouette ControlNet guide.
RAW raster pixels are never loaded or forwarded to ControlNet.
"""

from __future__ import annotations

import json
import math
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from PIL import Image, ImageDraw

try:
    import torch
    HAS_TORCH = True
except ImportError:  # pragma: no cover - ComfyUI supplies torch in production
    HAS_TORCH = False

from .authoring_contract import validate_document
from .layout_guide_generator import draw_single_character_mannequin


GUIDE_TYPE = "rough_manga"
DEFAULT_WIDTH = 832
DEFAULT_HEIGHT = 1216


def _require_positive_int(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"Generation guide bridge requires positive integer page.{field}, got {value!r}")
    return int(value)


def _white_tensor(width: int, height: int) -> Any:
    """Return deterministic pure white IMAGE tensor (1, H, W, 3) representing NO_GENERATION_GUIDE."""
    image = np.ones((1, int(height), int(width), 3), dtype=np.float32)
    if HAS_TORCH:
        return torch.from_numpy(image)
    return image


def _tensor_output(image: Image.Image) -> Any:
    """Convert RGB PIL Image to ComfyUI IMAGE tensor (1, H, W, 3)."""
    image_array = np.asarray(image.convert("RGB"), dtype=np.float32) / 255.0
    image_array = np.expand_dims(image_array, axis=0)
    if HAS_TORCH:
        return torch.from_numpy(image_array)
    return image_array


def _area_values(area: Dict[str, Any], context: str) -> Tuple[float, float, float, float]:
    if not isinstance(area, dict):
        raise ValueError(f"{context} must be an area object")
    try:
        values = tuple(float(area[key]) for key in ("x", "y", "w", "h"))
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"{context} is missing numeric x/y/w/h") from exc
    if not all(math.isfinite(value) for value in values):
        raise ValueError(f"{context} must contain finite x/y/w/h")
    x, y, w, h = values
    if w <= 0 or h <= 0 or x < 0 or y < 0 or x + w > 1.0001 or y + h > 1.0001:
        raise ValueError(f"{context} must be contained in normalized [0,1] bounds")
    return x, y, w, h


def _derive_page_area(placement: Dict[str, Any], local_area: Dict[str, Any], context: str) -> Tuple[float, float, float, float]:
    px, py, pw, ph = _area_values(placement, f"{context}.placement")
    lx, ly, lw, lh = _area_values(local_area, f"{context}.figure_area")
    x = px + lx * pw
    y = py + ly * ph
    w = lw * pw
    h = lh * ph
    if x < 0 or y < 0 or x + w > 1.0001 or y + h > 1.0001:
        raise ValueError(f"Derived Guide figure area exceeds page bounds ({context})")
    return x, y, w, h


def _pixel_bounds(page_area: Tuple[float, float, float, float], width: int, height: int) -> Tuple[int, int, int, int]:
    x, y, w, h = page_area
    x0 = max(0, min(width - 1, int(round(x * width))))
    y0 = max(0, min(height - 1, int(round(y * height))))
    x1 = max(x0 + 1, min(width, int(round((x + w) * width))))
    y1 = max(y0 + 1, min(height, int(round((y + h) * height))))
    return x0, y0, x1, y1


def _enabled_rough_guides(page: Dict[str, Any]) -> List[Dict[str, Any]]:
    guides = page.get("guides", [])
    if not isinstance(guides, list):
        raise ValueError("page.guides must be a list")
    return [
        guide for guide in guides
        if isinstance(guide, dict)
        and guide.get("guide_type") == GUIDE_TYPE
        and guide.get("enabled", True) is True
    ]


def build_generation_guide_plan(
    doc: Dict[str, Any],
    page_index: int = 0,
) -> Dict[str, Any]:
    """
    Build a deterministic CLEAN generation guide from authoring document geometry.

    Follows M3B-PI1 production contracts:
    - Only enabled rough_manga guides contribute.
    - If no eligible guides or zero figure regions: returns NO_GENERATION_GUIDE (pure white canvas).
    - Figure geometry is projected to page space and rendered using flat_silhouette mannequin.
    - RAW image pixels are never accessed.
    """
    if not isinstance(doc, dict):
        raise ValueError("Generation guide bridge document must be a dict")
    validation = validate_document(doc)
    if not validation.valid:
        raise ValueError("Invalid authoring document: " + "; ".join(validation.errors))

    pages = doc.get("pages", [])
    if not isinstance(page_index, int) or isinstance(page_index, bool) or not (0 <= page_index < len(pages)):
        raise ValueError(f"page_index {page_index} out of range (document has {len(pages)} page(s))")

    page = pages[page_index]
    width = _require_positive_int(page.get("width_px"), "width_px")
    height = _require_positive_int(page.get("height_px"), "height_px")

    guides = _enabled_rough_guides(page)
    # Collect all figures across enabled rough_manga guides
    eligible_guides_with_figures: List[Tuple[Dict[str, Any], List[Dict[str, Any]]]] = []
    total_figures = 0

    for guide in guides:
        figure_regions = guide.get("figure_regions", [])
        if not isinstance(figure_regions, list):
            raise ValueError(f"Guide '{guide.get('guide_id')}' figure_regions must be a list")
        if len(figure_regions) > 0:
            eligible_guides_with_figures.append((guide, figure_regions))
            total_figures += len(figure_regions)

    if not eligible_guides_with_figures or total_figures == 0:
        white_tensor = _white_tensor(width, height)
        return {
            "status": "NO_GENERATION_GUIDE",
            "image": white_tensor,
            "canvas_image": Image.new("RGB", (width, height), (255, 255, 255)),
            "debug": {
                "node": "TegakiMangaGenerationGuideBridge",
                "document_id": doc.get("document_id", "unknown"),
                "resolved_page_index": page_index,
                "status": "NO_GENERATION_GUIDE",
                "eligible_guide_count": len(guides),
                "figure_count": 0,
                "canvas_dimensions": {"width_px": width, "height_px": height},
                "generation_influence": "NO_GUIDE",
                "controlnet_target": "GLOBAL",
            },
        }

    canvas = Image.new("RGB", (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(canvas)
    figure_debug_records: List[Dict[str, Any]] = []

    for guide, figure_regions in eligible_guides_with_figures:
        guide_id = guide.get("guide_id", "unknown")
        placement = guide.get("placement")
        seen_figure_ids = set()

        for figure in figure_regions:
            if not isinstance(figure, dict):
                raise ValueError(f"Guide '{guide_id}' contains a non-object figure")
            figure_id = figure.get("figure_id")
            if not isinstance(figure_id, str) or not figure_id:
                raise ValueError("Guide figure_id must be a non-empty string")
            if figure_id in seen_figure_ids:
                raise ValueError(f"Duplicate figure_id '{figure_id}' in Guide '{guide_id}'")
            seen_figure_ids.add(figure_id)

            ctx = f"guide '{guide_id}', figure '{figure_id}'"
            derived_page_area = _derive_page_area(placement, figure.get("area"), ctx)
            pixel_box = _pixel_bounds(derived_page_area, width, height)

            draw_single_character_mannequin(
                draw,
                *pixel_box,
                guide_style="flat_silhouette",
                fg_color=(0, 0, 0),
                box_outline_color=(0, 0, 0),
                fill_color=(0, 0, 0),
                line_thickness=1,
                include_bbox_outline=False,
                shot_type="full_body",
                pose_preset="standing_neutral",
            )

            figure_debug_records.append({
                "guide_id": guide_id,
                "figure_id": figure_id,
                "instance_id": figure.get("instance_id"),
                "local_area": figure.get("area"),
                "guide_placement": placement,
                "derived_page_area": {
                    "x": round(derived_page_area[0], 6),
                    "y": round(derived_page_area[1], 6),
                    "w": round(derived_page_area[2], 6),
                    "h": round(derived_page_area[3], 6),
                },
                "pixel_bounds": {
                    "x0": pixel_box[0],
                    "y0": pixel_box[1],
                    "x1": pixel_box[2],
                    "y1": pixel_box[3],
                },
                "renderer": "custom_nodes_custom.tegaki_manga_nodes.layout_guide_generator.draw_single_character_mannequin",
                "renderer_style": "flat_silhouette",
                "shot_type": "full_body",
                "pose_preset": "standing_neutral",
                "include_bbox_outline": False,
            })

    image_tensor = _tensor_output(canvas)
    return {
        "status": "PASS",
        "image": image_tensor,
        "canvas_image": canvas,
        "debug": {
            "node": "TegakiMangaGenerationGuideBridge",
            "document_id": doc.get("document_id", "unknown"),
            "resolved_page_index": page_index,
            "status": "PASS",
            "eligible_guide_count": len(guides),
            "figure_count": len(figure_debug_records),
            "canvas_dimensions": {"width_px": width, "height_px": height},
            "figures": figure_debug_records,
            "renderer": "custom_nodes_custom.tegaki_manga_nodes.layout_guide_generator.draw_single_character_mannequin",
            "renderer_style": "flat_silhouette",
            "shot_type": "full_body",
            "pose_preset": "standing_neutral",
            "include_bbox_outline": False,
            "generation_influence": "CLEAN_GLOBAL",
            "controlnet_target": "GLOBAL",
        },
    }


class TegakiMangaGenerationGuideBridge:
    """Production CLEAN generation guide bridge for Core Global ControlNet."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "document_json": ("STRING", {"multiline": True, "default": ""}),
            },
            "optional": {
                "page_index": ("INT", {"default": 0, "min": 0, "max": 64, "step": 1}),
            },
        }

    RETURN_TYPES = ("IMAGE", "STRING")
    RETURN_NAMES = ("clean_generation_guide", "debug_json")
    FUNCTION = "bridge"
    CATEGORY = "tegaki/manga/guide"

    def bridge(self, document_json: str = "", page_index: int = 0):
        raw_text = (document_json or "").strip()
        if not raw_text:
            white = _white_tensor(DEFAULT_WIDTH, DEFAULT_HEIGHT)
            debug = {
                "node": "TegakiMangaGenerationGuideBridge",
                "document_id": "none",
                "resolved_page_index": page_index,
                "status": "NO_GENERATION_GUIDE",
                "eligible_guide_count": 0,
                "figure_count": 0,
                "canvas_dimensions": {"width_px": DEFAULT_WIDTH, "height_px": DEFAULT_HEIGHT},
                "generation_influence": "NO_GUIDE",
                "controlnet_target": "GLOBAL",
            }
            return white, json.dumps(debug, indent=2, ensure_ascii=False)

        try:
            doc = json.loads(raw_text)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Generation Guide document JSON parse failed: {exc}") from exc

        result = build_generation_guide_plan(doc, page_index=page_index)
        return result["image"], json.dumps(result["debug"], indent=2, ensure_ascii=False)
