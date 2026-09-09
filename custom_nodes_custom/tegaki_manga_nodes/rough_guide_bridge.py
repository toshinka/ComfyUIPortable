"""
rough_guide_bridge.py — M3B-LR1 Page-owned Rough Guide runtime bridge.

The bridge is deliberately observational. It loads an uploaded rough guide at
the ComfyUI input boundary, projects manually-authored Guide-local figure
rectangles into a page-sized preview/mask, and reports provenance. It does not
alter prompts, conditioning, KSampler inputs, ControlNet, or generation
semantics.
"""

from __future__ import annotations

import json
import math
import posixpath
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from PIL import Image, ImageDraw

try:
    import torch
    HAS_TORCH = True
except ImportError:  # pragma: no cover - ComfyUI supplies torch in production
    HAS_TORCH = False

try:
    import folder_paths
except ImportError:  # pragma: no cover - direct unit tests can inject input_root
    folder_paths = None

from .authoring_contract import SUPPORTED_GUIDE_EXTENSIONS, validate_document


GUIDE_TYPE = "rough_manga"
DRIVE_PREFIX_RE = re.compile(r"^[A-Za-z]:")


def _empty_outputs(width: int, height: int) -> Tuple[Any, Any]:
    """Return deterministic no-guide IMAGE/MASK outputs."""
    image = np.zeros((1, int(height), int(width), 3), dtype=np.float32)
    mask = np.zeros((1, int(height), int(width)), dtype=np.float32)
    if HAS_TORCH:
        return torch.from_numpy(image), torch.from_numpy(mask)
    return image, mask


def _tensor_outputs(image: Image.Image, mask: Image.Image) -> Tuple[Any, Any]:
    image_array = np.asarray(image.convert("RGB"), dtype=np.float32) / 255.0
    mask_array = np.asarray(mask.convert("L"), dtype=np.float32) / 255.0
    image_array = np.expand_dims(image_array, axis=0)
    mask_array = np.expand_dims(mask_array, axis=0)
    if HAS_TORCH:
        return torch.from_numpy(image_array), torch.from_numpy(mask_array)
    return image_array, mask_array


def _require_positive_int(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"Guide bridge requires positive integer page.{field}, got {value!r}")
    return int(value)


def validate_asset_reference(asset_reference: Any) -> List[str]:
    """Return errors for the canonical relative ComfyUI input-boundary path."""
    errors: List[str] = []
    if not isinstance(asset_reference, str) or not asset_reference.strip():
        return ["asset_reference must be a non-empty string"]

    value = asset_reference.strip()
    if value.startswith(("/", "\\")):
        errors.append("asset_reference must be relative")
    if value.lower().startswith("file://"):
        errors.append("asset_reference must not be a file URL")
    if DRIVE_PREFIX_RE.match(value):
        errors.append("asset_reference must not contain a drive prefix")
    if "\\" in value:
        errors.append("asset_reference must use canonical '/' separators")
    if any(part in ("", ".", "..") for part in value.split("/")):
        errors.append("asset_reference contains an invalid path segment")
    if posixpath.normpath(value) != value:
        errors.append("asset_reference is not normalized")
    extension = Path(value).suffix.lower()
    if extension not in SUPPORTED_GUIDE_EXTENSIONS:
        errors.append(
            f"unsupported Guide asset extension '{extension or '<none>'}'"
        )
    return errors


def resolve_input_asset(asset_reference: str, input_root: Optional[str] = None) -> Path:
    """Resolve a safe canonical reference strictly below the ComfyUI input root."""
    errors = validate_asset_reference(asset_reference)
    if errors:
        raise ValueError("Invalid Guide asset reference: " + "; ".join(errors))

    root_value = input_root
    if root_value is None:
        if folder_paths is None or not hasattr(folder_paths, "get_input_directory"):
            raise ValueError("ComfyUI input directory is unavailable")
        root_value = folder_paths.get_input_directory()
    root = Path(root_value).resolve()
    relative_parts = asset_reference.split("/")
    candidate = (root.joinpath(*relative_parts)).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise ValueError("Guide asset resolves outside the ComfyUI input directory") from exc
    return candidate


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


def _guide_page_area(placement: Dict[str, Any], local_area: Dict[str, Any]) -> Tuple[float, float, float, float]:
    px, py, pw, ph = _area_values(placement, "guide.placement")
    lx, ly, lw, lh = _area_values(local_area, "guide.figure_regions[].area")
    x = px + lx * pw
    y = py + ly * ph
    w = lw * pw
    h = lh * ph
    if x < 0 or y < 0 or x + w > 1.0001 or y + h > 1.0001:
        raise ValueError("Derived Guide figure area exceeds page bounds")
    return x, y, w, h


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


def build_rough_guide_plan(
    doc: Dict[str, Any],
    page_index: int = 0,
    input_root: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Load enabled rough guides and build a page-sized preview/mask plan.

    No enabled rough_manga Guide is a valid NO_GUIDE result. Any enabled Guide
    with a missing, unsafe, unsupported, undecodable, or structurally invalid
    asset fails closed with ValueError.
    """
    if not isinstance(doc, dict):
        raise ValueError("Guide bridge document must be a dict")
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
    if not guides:
        image, mask = _empty_outputs(width, height)
        return {
            "status": "NO_GUIDE",
            "image": image,
            "mask": mask,
            "debug": {
                "node": "TegakiMangaRoughGuideBridge",
                "document_id": doc.get("document_id", "unknown"),
                "resolved_page_index": page_index,
                "guide_count": 0,
                "figure_count": 0,
                "generation_influence": "NOT_IMPLEMENTED",
                "controlnet": "NOT_ADDED",
                "association_policy": "manual_instance_id_only",
                "status": "NO_GUIDE",
            },
        }

    canvas = Image.new("RGB", (width, height), (255, 255, 255))
    union_mask = Image.new("L", (width, height), 0)
    mask_draw = ImageDraw.Draw(union_mask)
    guide_debug: List[Dict[str, Any]] = []
    figure_count = 0

    for guide in guides:
        asset_reference = guide.get("asset_reference")
        asset_path = resolve_input_asset(asset_reference, input_root=input_root)
        if not asset_path.is_file():
            raise ValueError(f"Guide asset does not exist: {asset_reference}")
        try:
            with Image.open(asset_path) as source:
                source.load()
                source_rgb = source.convert("RGB")
        except Exception as exc:
            raise ValueError(f"Guide asset could not be decoded: {asset_reference}") from exc

        placement = guide.get("placement")
        px, py, pw, ph = _area_values(placement, f"guide '{guide.get('guide_id')}'.placement")
        dest_x = max(0, min(width, int(round(px * width))))
        dest_y = max(0, min(height, int(round(py * height))))
        dest_w = max(1, min(width - dest_x, int(round(pw * width))))
        dest_h = max(1, min(height - dest_y, int(round(ph * height))))
        resized = source_rgb.resize((dest_w, dest_h), Image.Resampling.LANCZOS)
        canvas.paste(resized, (dest_x, dest_y))

        figure_debug: List[Dict[str, Any]] = []
        figure_regions = guide.get("figure_regions", [])
        if not isinstance(figure_regions, list):
            raise ValueError(f"Guide '{guide.get('guide_id')}' figure_regions must be a list")
        seen_figure_ids = set()
        seen_instance_ids = set()
        for figure in figure_regions:
            if not isinstance(figure, dict):
                raise ValueError(f"Guide '{guide.get('guide_id')}' contains a non-object figure")
            figure_id = figure.get("figure_id")
            if not isinstance(figure_id, str) or not figure_id:
                raise ValueError("Guide figure_id must be a non-empty string")
            if figure_id in seen_figure_ids:
                raise ValueError(f"Duplicate figure_id '{figure_id}' in Guide '{guide.get('guide_id')}'")
            seen_figure_ids.add(figure_id)
            instance_id = figure.get("instance_id")
            if instance_id is not None:
                if instance_id in seen_instance_ids:
                    raise ValueError(
                        f"Duplicate instance association '{instance_id}' in Guide '{guide.get('guide_id')}'"
                    )
                seen_instance_ids.add(instance_id)
            fx, fy, fw, fh = _guide_page_area(placement, figure.get("area"))
            mask_draw.rectangle(
                [
                    max(0, int(round(fx * width))),
                    max(0, int(round(fy * height))),
                    min(width - 1, int(round((fx + fw) * width)) - 1),
                    min(height - 1, int(round((fy + fh) * height)) - 1),
                ],
                fill=255,
            )
            figure_debug.append({
                "figure_id": figure_id,
                "instance_id": instance_id,
                "local_area": figure.get("area"),
                "derived_page_area": {
                    "x": round(fx, 4), "y": round(fy, 4),
                    "w": round(fw, 4), "h": round(fh, 4),
                },
            })
            figure_count += 1

        guide_debug.append({
            "guide_id": guide.get("guide_id"),
            "guide_type": guide.get("guide_type"),
            "asset_reference": asset_reference,
            "source_dimensions": {"width_px": source_rgb.width, "height_px": source_rgb.height},
            "placement": placement,
            "figure_regions": figure_debug,
        })

    image_output, mask_output = _tensor_outputs(canvas, union_mask)
    return {
        "status": "PASS",
        "image": image_output,
        "mask": mask_output,
        "debug": {
            "node": "TegakiMangaRoughGuideBridge",
            "document_id": doc.get("document_id", "unknown"),
            "resolved_page_index": page_index,
            "guide_count": len(guides),
            "figure_count": figure_count,
            "guides": guide_debug,
            "generation_influence": "NOT_IMPLEMENTED",
            "controlnet": "NOT_ADDED",
            "association_policy": "manual_instance_id_only",
            "automatic_interpretation": "NOT_PERFORMED",
            "status": "PASS",
        },
    }


class TegakiMangaRoughGuideBridge:
    """Standalone preview/mask bridge; intentionally outside generation influence."""

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

    RETURN_TYPES = ("IMAGE", "MASK", "STRING")
    RETURN_NAMES = ("rough_guide_image", "figure_union_mask", "debug_json")
    FUNCTION = "bridge"
    CATEGORY = "tegaki/manga/guide"

    def bridge(self, document_json: str = "", page_index: int = 0):
        raw_text = (document_json or "").strip()
        if not raw_text:
            image, mask = _empty_outputs(832, 1216)
            debug = {
                "node": "TegakiMangaRoughGuideBridge",
                "guide_count": 0,
                "figure_count": 0,
                "generation_influence": "NOT_IMPLEMENTED",
                "controlnet": "NOT_ADDED",
                "status": "NO_GUIDE",
            }
            return image, mask, json.dumps(debug, indent=2, ensure_ascii=False)
        try:
            doc = json.loads(raw_text)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Rough Guide document JSON parse failed: {exc}") from exc
        result = build_rough_guide_plan(doc, page_index=page_index)
        return result["image"], result["mask"], json.dumps(result["debug"], indent=2, ensure_ascii=False)
