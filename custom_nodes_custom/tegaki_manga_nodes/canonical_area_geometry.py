"""
canonical_area_geometry.py — Pure Canonical Area Geometry & Mask Core
======================================================================
TEGAKI Manga Authoring Capability Bank (MANGA-CANONICAL-AREA-GEOMETRY-CORE1)

This module provides pure, deterministic, domain-semantics-neutral utilities
for canonical area geometry in page-normalized coordinates [0.0, 1.0] and
their conversion to pixel bounds and hard binary masks.

Key principles:
- Deterministic and pure: zero side-effects, zero state, input immutable.
- CPU-safe and GPU-independent.
- Domain-neutral: shares geometry without merging MRP, CAST, or Guide semantics.
- Standalone foundation: separate from feather/blur, overlap precedence,
  or conditioning engines.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Sequence, Tuple

import torch

# Canonical geometry constants (consistent with authoring_contract and scene_spec)
MIN_RECT_SIZE: float = 0.001
GEOMETRY_ROUND_DIGITS: int = 4
VALID_SHAPE_TYPES: frozenset[str] = frozenset({"rect"})
COORDINATE_TOLERANCE: float = 1e-4


def _is_finite_numeric(val: Any) -> bool:
    """Return True if val is a finite int or float (excluding bool)."""
    if isinstance(val, bool) or not isinstance(val, (int, float)):
        return False
    return math.isfinite(float(val))


def validate_canonical_area(area: Any, context: str = "") -> Dict[str, float]:
    """Validate a canonical normalized area dictionary.

    Expects a mapping containing 'x', 'y', 'w', 'h' in page-normalized [0.0, 1.0]
    coordinates where w > 0, h > 0, x + w <= 1.0, and y + h <= 1.0.
    Optional 'shape_type' must be 'rect' if present.

    Returns a clean dictionary with float values {'x': ..., 'y': ..., 'w': ..., 'h': ...}.
    Raises ValueError on any invariant violation.
    """
    ctx = f" ({context})" if context else ""

    if not isinstance(area, dict):
        raise ValueError(f"[CanonicalAreaGeometry] area must be a dictionary{ctx}, got {type(area).__name__}")

    shape_type = area.get("shape_type", "rect")
    if shape_type not in VALID_SHAPE_TYPES:
        raise ValueError(
            f"[CanonicalAreaGeometry] unsupported shape_type '{shape_type}'{ctx}; "
            f"must be one of {sorted(VALID_SHAPE_TYPES)}"
        )

    for key in ("x", "y", "w", "h"):
        if key not in area:
            raise ValueError(f"[CanonicalAreaGeometry] area.{key} is missing{ctx}")
        val = area[key]
        if not _is_finite_numeric(val):
            raise ValueError(
                f"[CanonicalAreaGeometry] area.{key} must be a finite numeric (not bool, NaN, or Inf){ctx}, got {val!r}"
            )

    x = float(area["x"])
    y = float(area["y"])
    w = float(area["w"])
    h = float(area["h"])

    if w <= 0.0:
        raise ValueError(f"[CanonicalAreaGeometry] area.w must be > 0{ctx}, got {w}")
    if h <= 0.0:
        raise ValueError(f"[CanonicalAreaGeometry] area.h must be > 0{ctx}, got {h}")
    if x < 0.0 or x > 1.0:
        raise ValueError(f"[CanonicalAreaGeometry] area.x out of bounds [0, 1]{ctx}, got {x}")
    if y < 0.0 or y > 1.0:
        raise ValueError(f"[CanonicalAreaGeometry] area.y out of bounds [0, 1]{ctx}, got {y}")
    if x + w > 1.0 + COORDINATE_TOLERANCE:
        raise ValueError(f"[CanonicalAreaGeometry] area.x + area.w exceeds 1.0{ctx}, got {x + w}")
    if y + h > 1.0 + COORDINATE_TOLERANCE:
        raise ValueError(f"[CanonicalAreaGeometry] area.y + area.h exceeds 1.0{ctx}, got {y + h}")

    return {
        "x": x,
        "y": y,
        "w": w,
        "h": h,
    }


def normalize_canonical_area(
    area: Any,
    min_size: float = MIN_RECT_SIZE,
    context: str = "",
) -> Dict[str, Any]:
    """Validate and clamp a rectangle to strictly valid canonical normalized bounds.

    Clamps coordinates within [0.0, 1.0 - min_size] and dimensions within
    [min_size, 1.0 - origin], rounded to GEOMETRY_ROUND_DIGITS (4 decimal places).
    Does not mutate the input dictionary.
    """
    ctx = f" ({context})" if context else ""

    if not isinstance(area, dict):
        raise ValueError(f"[CanonicalAreaGeometry] area must be a dictionary{ctx}, got {type(area).__name__}")

    for key in ("x", "y", "w", "h"):
        if key not in area:
            raise ValueError(f"[CanonicalAreaGeometry] area.{key} is missing{ctx}")
        val = area[key]
        if not _is_finite_numeric(val):
            raise ValueError(
                f"[CanonicalAreaGeometry] area.{key} must be a finite numeric{ctx}, got {val!r}"
            )

    x = float(area["x"])
    y = float(area["y"])
    w = float(area["w"])
    h = float(area["h"])

    x = max(0.0, min(1.0 - min_size, x))
    y = max(0.0, min(1.0 - min_size, y))

    max_w = max(min_size, 1.0 - x)
    max_h = max(min_size, 1.0 - y)
    w = max(min_size, min(max_w, w))
    h = max(min_size, min(max_h, h))

    if x + w > 1.0:
        w = max(min_size, 1.0 - x)
    if y + h > 1.0:
        h = max(min_size, 1.0 - y)

    return {
        "shape_type": "rect",
        "x": round(x, GEOMETRY_ROUND_DIGITS),
        "y": round(y, GEOMETRY_ROUND_DIGITS),
        "w": round(w, GEOMETRY_ROUND_DIGITS),
        "h": round(h, GEOMETRY_ROUND_DIGITS),
    }


def canonical_area_to_pixel_bounds(
    area: Dict[str, Any],
    width: int,
    height: int,
    *,
    validate: bool = True,
    context: str = "",
) -> Tuple[int, int, int, int]:
    """Project a canonical normalized area to integer pixel bounds [px0, py0, px1, py1].

    Conversion rules:
      px0 = max(0, min(width, int(round(x * width))))
      py0 = max(0, min(height, int(round(y * height))))
      px1 = max(0, min(width, int(round((x + w) * width))))
      py1 = max(0, min(height, int(round((y + h) * height))))

    This matches the authoritative pixel projection convention proven in
    production mask_builder.py and authoring_execution_bridge.py.

    Returns a 4-tuple of ints (px0, py0, px1, py1) satisfying:
      0 <= px0 <= px1 <= width
      0 <= py0 <= py1 <= height
    """
    ctx = f" ({context})" if context else ""

    if isinstance(width, bool) or not isinstance(width, int) or width <= 0:
        raise ValueError(f"[CanonicalAreaGeometry] canvas width must be a positive integer{ctx}, got {width!r}")
    if isinstance(height, bool) or not isinstance(height, int) or height <= 0:
        raise ValueError(f"[CanonicalAreaGeometry] canvas height must be a positive integer{ctx}, got {height!r}")

    if validate:
        valid_area = validate_canonical_area(area, context=context)
        x, y, w, h = valid_area["x"], valid_area["y"], valid_area["w"], valid_area["h"]
    else:
        for key in ("x", "y", "w", "h"):
            if key not in area or not _is_finite_numeric(area[key]):
                raise ValueError(f"[CanonicalAreaGeometry] area.{key} must be a finite numeric{ctx}")
        x = float(area["x"])
        y = float(area["y"])
        w = float(area["w"])
        h = float(area["h"])

    px0 = max(0, min(width, int(round(x * width))))
    py0 = max(0, min(height, int(round(y * height))))
    px1 = max(0, min(width, int(round((x + w) * width))))
    py1 = max(0, min(height, int(round((y + h) * height))))

    return (px0, py0, px1, py1)


def pixel_bounds_to_mask(
    bounds: Sequence[int],
    width: int,
    height: int,
    *,
    as_batch: bool = False,
    device: Optional[Any] = None,
) -> torch.Tensor:
    """Rasterize pixel bounds [px0, py0, px1, py1] to a binary float32 mask tensor.

    Pixels inside [py0:py1, px0:px1] are set to 1.0; all other pixels are 0.0.
    Orientation is rows = height, columns = width (standard image/mask layout).

    Returns:
      torch.Tensor of shape (height, width) if as_batch=False,
      or shape (1, height, width) if as_batch=True.
      dtype is torch.float32.
    """
    if isinstance(width, bool) or not isinstance(width, int) or width <= 0:
        raise ValueError(f"[CanonicalAreaGeometry] canvas width must be a positive integer, got {width!r}")
    if isinstance(height, bool) or not isinstance(height, int) or height <= 0:
        raise ValueError(f"[CanonicalAreaGeometry] canvas height must be a positive integer, got {height!r}")

    if not isinstance(bounds, (list, tuple)) or len(bounds) != 4:
        raise ValueError(f"[CanonicalAreaGeometry] bounds must be a sequence of 4 integers, got {bounds!r}")

    for idx, coord in enumerate(bounds):
        if isinstance(coord, bool) or not isinstance(coord, int):
            raise ValueError(
                f"[CanonicalAreaGeometry] bounds[{idx}] must be an integer, got {coord!r}"
            )

    px0 = max(0, min(width, bounds[0]))
    py0 = max(0, min(height, bounds[1]))
    px1 = max(0, min(width, bounds[2]))
    py1 = max(0, min(height, bounds[3]))

    dev = device if device is not None else "cpu"
    mask = torch.zeros((height, width), dtype=torch.float32, device=dev)

    if px1 > px0 and py1 > py0:
        mask[py0:py1, px0:px1] = 1.0

    if as_batch:
        mask = mask.unsqueeze(0)

    return mask


def canonical_area_to_mask(
    area: Dict[str, Any],
    width: int,
    height: int,
    *,
    as_batch: bool = False,
    validate: bool = True,
    device: Optional[Any] = None,
    context: str = "",
) -> torch.Tensor:
    """Convenience pipeline: convert a canonical area directly to a binary mask tensor.

    Combines canonical_area_to_pixel_bounds and pixel_bounds_to_mask in a single
    pure, deterministic call without side-effects or intermediate storage.
    """
    bounds = canonical_area_to_pixel_bounds(
        area, width, height, validate=validate, context=context
    )
    return pixel_bounds_to_mask(
        bounds, width, height, as_batch=as_batch, device=device
    )
