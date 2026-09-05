"""
authoring_operations.py — Pure Authoring Document Operations (M0 / 3M-0)
=========================================================================
Side-effect-free operations on the versioned authoring document.
No ComfyUI dependency. No I/O. Testable with plain Python.
"""

import copy
import math
from typing import Any, Dict, List, Optional, Tuple

from .authoring_contract import (
    validate_area,
    make_area,
    generate_id,
    GEOMETRY_ROUND_DIGITS,
)


# ===================================================================
# Internal helpers
# ===================================================================

def _find_page(doc: Dict, page_id: str) -> Dict:
    """Find a page by ID. Raises ValueError if not found."""
    for page in doc.get("pages", []):
        if page.get("page_id") == page_id:
            return page
    raise ValueError(f"Page '{page_id}' not found in document")


def _find_scene(page: Dict, scene_id: str) -> Dict:
    """Find a scene by ID within a page."""
    for scene in page.get("scenes", []):
        if scene.get("scene_id") == scene_id:
            return scene
    raise ValueError(f"Scene '{scene_id}' not found in page '{page.get('page_id')}'")


def _find_frame(page: Dict, frame_id: str) -> Dict:
    """Find a visual frame by ID within a page."""
    for frame in page.get("visual_frames", []):
        if frame.get("frame_id") == frame_id:
            return frame
    raise ValueError(f"Frame '{frame_id}' not found in page '{page.get('page_id')}'")


def _get_instances_for_scene(page: Dict, scene_id: str) -> List[Dict]:
    """Get all character instances belonging to a scene."""
    return [
        inst for inst in page.get("character_instances", [])
        if inst.get("scene_id") == scene_id
    ]


def _clamp_area(area: Dict) -> Dict:
    """Clamp area coordinates to [0, 1] bounds, preserving unknown fields."""
    result = dict(area)  # shallow copy preserving extra keys
    x = max(0.0, min(1.0, float(area["x"])))
    y = max(0.0, min(1.0, float(area["y"])))
    w = float(area["w"])
    h = float(area["h"])

    # Ensure x+w and y+h don't exceed 1.0
    if x + w > 1.0:
        w = max(0.001, 1.0 - x)
    if y + h > 1.0:
        h = max(0.001, 1.0 - y)

    result["x"] = round(x, GEOMETRY_ROUND_DIGITS)
    result["y"] = round(y, GEOMETRY_ROUND_DIGITS)
    result["w"] = round(w, GEOMETRY_ROUND_DIGITS)
    result["h"] = round(h, GEOMETRY_ROUND_DIGITS)
    return result


def _translate_area(area: Dict, dx: float, dy: float) -> Dict:
    """Translate an area by (dx, dy) and clamp to bounds."""
    result = dict(area)
    result["x"] = float(area["x"]) + dx
    result["y"] = float(area["y"]) + dy
    return _clamp_area(result)


# ===================================================================
# Scene operations
# ===================================================================

def move_scene(doc: Dict, page_id: str, scene_id: str,
               dx: float, dy: float) -> Dict:
    """
    Move a scene and all its belonging character instances by (dx, dy).

    Visual frames are NOT moved (scene-frame independence).
    Other scenes are NOT moved.

    Returns a new document (deep copy).
    """
    doc = copy.deepcopy(doc)
    page = _find_page(doc, page_id)
    scene = _find_scene(page, scene_id)

    # Move scene area
    scene["area"] = _translate_area(scene["area"], dx, dy)

    # Move belonging instances by the same delta
    for inst in _get_instances_for_scene(page, scene_id):
        inst["area"] = _translate_area(inst["area"], dx, dy)

    return doc


def resize_scene(doc: Dict, page_id: str, scene_id: str,
                 new_area: Dict) -> Dict:
    """
    Resize a scene to new_area. Belonging character instances are
    proportionally transformed relative to the scene origin.

    Visual frames are NOT affected.

    Returns a new document (deep copy).
    """
    doc = copy.deepcopy(doc)
    page = _find_page(doc, page_id)
    scene = _find_scene(page, scene_id)

    old_area = scene["area"]
    old_x, old_y = float(old_area["x"]), float(old_area["y"])
    old_w, old_h = float(old_area["w"]), float(old_area["h"])
    new_x, new_y = float(new_area["x"]), float(new_area["y"])
    new_w, new_h = float(new_area["w"]), float(new_area["h"])

    # Proportional transform for instances
    if old_w > 0 and old_h > 0:
        scale_x = new_w / old_w
        scale_y = new_h / old_h

        for inst in _get_instances_for_scene(page, scene_id):
            ia = inst["area"]
            # Instance position relative to old scene origin
            rel_x = (float(ia["x"]) - old_x) / old_w
            rel_y = (float(ia["y"]) - old_y) / old_h
            rel_w = float(ia["w"]) / old_w
            rel_h = float(ia["h"]) / old_h

            # Map to new scene space
            inst["area"] = _clamp_area({
                **ia,  # preserve extra keys
                "x": new_x + rel_x * new_w,
                "y": new_y + rel_y * new_h,
                "w": rel_w * new_w,
                "h": rel_h * new_h,
            })

    # Update scene area
    area_errors = validate_area(new_area, f"resize_scene({scene_id})")
    if area_errors:
        raise ValueError(f"Invalid new_area: {'; '.join(area_errors)}")
    scene["area"] = _clamp_area({**old_area, **new_area})

    return doc


# ===================================================================
# Frame operations
# ===================================================================

def move_frame(doc: Dict, page_id: str, frame_id: str,
               dx: float, dy: float) -> Dict:
    """
    Move a visual frame by (dx, dy).

    Scenes and character instances are NOT moved (independence).

    Returns a new document (deep copy).
    """
    doc = copy.deepcopy(doc)
    page = _find_page(doc, page_id)
    frame = _find_frame(page, frame_id)

    frame["shape"] = _translate_area(frame["shape"], dx, dy)

    return doc


# ===================================================================
# Resolution operations
# ===================================================================

def change_resolution(doc: Dict, page_id: str,
                      new_width: int, new_height: int) -> Dict:
    """
    Change page resolution. Normalized areas remain unchanged
    (they are resolution-independent by definition).

    Returns a new document (deep copy).
    """
    if new_width <= 0 or new_height <= 0:
        raise ValueError(f"Resolution must be positive: {new_width}x{new_height}")

    doc = copy.deepcopy(doc)
    page = _find_page(doc, page_id)
    page["width_px"] = int(new_width)
    page["height_px"] = int(new_height)
    return doc


# ===================================================================
# Duplication
# ===================================================================

def duplicate_scene(doc: Dict, page_id: str, scene_id: str) -> Dict:
    """
    Deep copy a scene and all its character instances with new IDs.

    Returns a new document (deep copy).
    """
    doc = copy.deepcopy(doc)
    page = _find_page(doc, page_id)
    scene = _find_scene(page, scene_id)

    # Create new scene with new ID
    new_scene = copy.deepcopy(scene)
    new_scene_id = generate_id("scene")
    new_scene["scene_id"] = new_scene_id
    new_scene["name"] = f"{scene.get('name', '')} (copy)"
    page["scenes"].append(new_scene)

    # Duplicate belonging instances with new IDs
    for inst in _get_instances_for_scene(page, scene_id):
        new_inst = copy.deepcopy(inst)
        new_inst["instance_id"] = generate_id("inst")
        new_inst["scene_id"] = new_scene_id
        page["character_instances"].append(new_inst)

    return doc
