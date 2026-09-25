"""isolated_scene_plan.py — Pure transformation for isolated-Scene execution plans.

Extracts and validates a single selected Scene from an Authoring Document snapshot,
yielding an isolated execution plan for a local canvas without modifying the
original Authoring Document or compiling ComfyUI nodes.
"""

from __future__ import annotations

import copy
import math
from typing import Any, Dict, List, Optional, Tuple, Union


class IsolatedScenePlanError(ValueError):
    """Validation or contract error for isolated-Scene planning."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message

    def __repr__(self) -> str:
        return f"IsolatedScenePlanError(code={self.code!r}, message={self.message!r})"


# Backend bounds aligned with PRODUCT_BOUNDS
DIMENSION_BOUNDS = {
    "width": {"min": 256, "max": 2048, "step": 8},
    "height": {"min": 256, "max": 2048, "step": 8},
    "max_pixels": 2097152,
}

MAX_INSTANCES_PER_SCENE = 2
MAX_REFERENCES_PER_SCENE = 1
GEOMETRY_TOLERANCE = 0.0001


def _validate_dimensions(
    local_dimensions: Optional[Union[Tuple[int, int], List[int], Dict[str, Any]]],
    width_override: Optional[int] = None,
    height_override: Optional[int] = None,
) -> Tuple[int, int]:
    w: Any = None
    h: Any = None

    if width_override is not None or height_override is not None:
        w = width_override
        h = height_override
    elif isinstance(local_dimensions, (tuple, list)):
        if len(local_dimensions) == 2:
            w, h = local_dimensions
    elif isinstance(local_dimensions, dict):
        w = local_dimensions.get("width")
        h = local_dimensions.get("height")

    if w is None or h is None:
        raise IsolatedScenePlanError(
            "INVALID_LOCAL_DIMENSIONS",
            "Explicit local canvas dimensions (width, height) must be provided",
        )

    # Must be exact ints, not floats or bools
    if type(w) is not int or type(h) is not int:
        raise IsolatedScenePlanError(
            "INVALID_LOCAL_DIMENSIONS",
            f"Canvas dimensions must be integers, got width={type(w).__name__}, height={type(h).__name__}",
        )

    w_bounds = DIMENSION_BOUNDS["width"]
    h_bounds = DIMENSION_BOUNDS["height"]

    if not (w_bounds["min"] <= w <= w_bounds["max"]) or (w % w_bounds["step"] != 0):
        raise IsolatedScenePlanError(
            "INVALID_LOCAL_DIMENSIONS",
            f"Width {w} must be in {w_bounds['min']}..{w_bounds['max']} and divisible by {w_bounds['step']}",
        )

    if not (h_bounds["min"] <= h <= h_bounds["max"]) or (h % h_bounds["step"] != 0):
        raise IsolatedScenePlanError(
            "INVALID_LOCAL_DIMENSIONS",
            f"Height {h} must be in {h_bounds['min']}..{h_bounds['max']} and divisible by {h_bounds['step']}",
        )

    if w * h > DIMENSION_BOUNDS["max_pixels"]:
        raise IsolatedScenePlanError(
            "INVALID_LOCAL_DIMENSIONS",
            f"Total pixels {w * h} exceeds maximum {DIMENSION_BOUNDS['max_pixels']}",
        )

    return w, h


def _parse_rect(area: Any, label: str) -> Dict[str, float]:
    if not isinstance(area, dict):
        raise IsolatedScenePlanError(
            "INVALID_SCENE_GEOMETRY" if "scene" in label.lower() else "CHARACTER_INSTANCE_OUT_OF_BOUNDS",
            f"{label} area must be a dictionary",
        )

    shape_type = area.get("shape_type", "rect")
    if shape_type != "rect":
        raise IsolatedScenePlanError(
            "INVALID_SCENE_GEOMETRY" if "scene" in label.lower() else "CHARACTER_INSTANCE_OUT_OF_BOUNDS",
            f"{label} has unsupported shape_type '{shape_type}'; only 'rect' is supported",
        )

    values = {}
    for k in ("x", "y", "w", "h"):
        val = area.get(k)
        if type(val) not in (int, float) or not math.isfinite(val):
            raise IsolatedScenePlanError(
                "INVALID_SCENE_GEOMETRY" if "scene" in label.lower() else "CHARACTER_INSTANCE_OUT_OF_BOUNDS",
                f"{label} area field '{k}' must be a finite number, got {val!r}",
            )
        values[k] = float(val)

    x, y, w, h = values["x"], values["y"], values["w"], values["h"]
    if w <= 0 or h <= 0:
        raise IsolatedScenePlanError(
            "INVALID_SCENE_GEOMETRY" if "scene" in label.lower() else "CHARACTER_INSTANCE_OUT_OF_BOUNDS",
            f"{label} area width and height must be positive, got w={w}, h={h}",
        )

    if x < -GEOMETRY_TOLERANCE or y < -GEOMETRY_TOLERANCE or (x + w) > (1.0 + GEOMETRY_TOLERANCE) or (y + h) > (1.0 + GEOMETRY_TOLERANCE):
        raise IsolatedScenePlanError(
            "INVALID_SCENE_GEOMETRY" if "scene" in label.lower() else "CHARACTER_INSTANCE_OUT_OF_BOUNDS",
            f"{label} area [{x}, {y}, {w}, {h}] extends outside page bounds [0, 0, 1, 1]",
        )

    return {"x": x, "y": y, "w": w, "h": h}


def _resolve_page(
    doc: Dict[str, Any],
    scene_id: str,
    page_selection: Optional[Union[str, int]] = None,
    page_index: Optional[int] = None,
    page_id: Optional[str] = None,
) -> Tuple[Dict[str, Any], int]:
    pages = doc.get("pages")
    if not isinstance(pages, list) or not pages:
        raise IsolatedScenePlanError("INVALID_DOCUMENT_SNAPSHOT", "Snapshot must contain a non-empty 'pages' list")

    # Reconcile page selection
    target_idx: Optional[int] = None
    target_id: Optional[str] = None

    if page_index is not None:
        target_idx = page_index
    if page_id is not None:
        target_id = page_id

    if page_selection is not None:
        if isinstance(page_selection, int):
            if target_idx is not None and target_idx != page_selection:
                raise IsolatedScenePlanError(
                    "PAGE_SELECTION_CONFLICT",
                    f"Conflicting page_selection index {page_selection} vs page_index {target_idx}",
                )
            target_idx = page_selection
        elif isinstance(page_selection, str):
            if target_id is not None and target_id != page_selection:
                raise IsolatedScenePlanError(
                    "PAGE_SELECTION_CONFLICT",
                    f"Conflicting page_selection id '{page_selection}' vs page_id '{target_id}'",
                )
            target_id = page_selection

    if target_idx is not None:
        if target_idx < 0 or target_idx >= len(pages):
            raise IsolatedScenePlanError(
                "PAGE_NOT_FOUND",
                f"Page index {target_idx} is out of range (document has {len(pages)} pages)",
            )
        page = pages[target_idx]
        if not isinstance(page, dict):
            raise IsolatedScenePlanError("INVALID_DOCUMENT_SNAPSHOT", f"Page at index {target_idx} is not an object")
        if target_id is not None and page.get("page_id") != target_id:
            raise IsolatedScenePlanError(
                "PAGE_SELECTION_CONFLICT",
                f"Page at index {target_idx} has page_id '{page.get('page_id')}', expected '{target_id}'",
            )
        return page, target_idx

    if target_id is not None:
        matched = [(idx, p) for idx, p in enumerate(pages) if isinstance(p, dict) and p.get("page_id") == target_id]
        if not matched:
            raise IsolatedScenePlanError("PAGE_NOT_FOUND", f"Page with page_id '{target_id}' not found")
        if len(matched) > 1:
            raise IsolatedScenePlanError("AMBIGUOUS_PAGE_ID", f"Multiple pages have page_id '{target_id}'")
        return matched[0][1], matched[0][0]

    # Automatic page resolution by scene_id
    candidate_pages: List[Tuple[int, Dict[str, Any]]] = []
    for idx, p in enumerate(pages):
        if not isinstance(p, dict):
            continue
        scenes = p.get("scenes", [])
        if any(isinstance(s, dict) and s.get("scene_id") == scene_id for s in scenes):
            candidate_pages.append((idx, p))

    if not candidate_pages:
        raise IsolatedScenePlanError("SCENE_NOT_FOUND", f"Scene '{scene_id}' not found in any page of the document")
    if len(candidate_pages) > 1:
        raise IsolatedScenePlanError(
            "AMBIGUOUS_SCENE_ID",
            f"Scene '{scene_id}' found in multiple pages ({[idx for idx, _ in candidate_pages]}); explicit page selection required",
        )

    return candidate_pages[0][1], candidate_pages[0][0]


def _check_active_guides(page: Dict[str, Any]) -> None:
    guides = page.get("guides")
    if not guides or not isinstance(guides, list):
        return

    for g in guides:
        if not isinstance(g, dict):
            continue
        # In authoring contract: active if enabled is not False, type is structural, and asset_reference is present
        if g.get("enabled", True) is not False:
            guide_type = g.get("guide_type")
            asset = g.get("asset_reference")
            if guide_type in ("rough_manga", "frame_guide") and isinstance(asset, str) and asset.strip():
                raise IsolatedScenePlanError(
                    "ISOLATED_SCENE_GUIDE_UNSUPPORTED",
                    f"Active structural guide '{g.get('guide_id')}' of type '{guide_type}' is unsupported in isolated-Scene planning",
                )


def create_isolated_scene_plan(
    document_snapshot: Dict[str, Any],
    scene_id: str,
    page_selection: Optional[Union[str, int]] = None,
    local_dimensions: Optional[Union[Tuple[int, int], List[int], Dict[str, Any]]] = None,
    *,
    page_index: Optional[int] = None,
    page_id: Optional[str] = None,
    width: Optional[int] = None,
    height: Optional[int] = None,
) -> Dict[str, Any]:
    """Pure transformation creating an isolated execution plan for a single Scene.

    Args:
        document_snapshot: Complete authoring document snapshot (unmutated).
        scene_id: Target scene ID to isolate.
        page_selection: Optional page index (int) or page_id (str).
        local_dimensions: Explicit canvas dimensions (w, h) or {"width": w, "height": h}.
        page_index: Kwarg alias for page index.
        page_id: Kwarg alias for page id.
        width: Kwarg override for width.
        height: Kwarg override for height.

    Returns:
        Isolated execution plan dictionary.

    Raises:
        IsolatedScenePlanError: On any validation or contract failure.
    """
    if not isinstance(document_snapshot, dict):
        raise IsolatedScenePlanError("INVALID_DOCUMENT_SNAPSHOT", "document_snapshot must be a dictionary")

    if not isinstance(scene_id, str) or not scene_id.strip():
        raise IsolatedScenePlanError("SCENE_NOT_FOUND", "A valid non-empty scene_id must be provided")

    scene_id = scene_id.strip()

    # 1. Validate local dimensions
    local_w, local_h = _validate_dimensions(local_dimensions, width_override=width, height_override=height)

    # 2. Resolve target page
    page, resolved_page_index = _resolve_page(
        document_snapshot,
        scene_id,
        page_selection=page_selection,
        page_index=page_index,
        page_id=page_id,
    )

    # 3. Check for unsupported active structural guides
    _check_active_guides(page)

    # 4. Resolve selected scene within the page
    scenes = page.get("scenes")
    if not isinstance(scenes, list):
        raise IsolatedScenePlanError("INVALID_DOCUMENT_SNAPSHOT", "page.scenes must be a list")

    matching_scenes = [s for s in scenes if isinstance(s, dict) and s.get("scene_id") == scene_id]
    if not matching_scenes:
        raise IsolatedScenePlanError("SCENE_NOT_FOUND", f"Scene '{scene_id}' not found in target page")
    if len(matching_scenes) > 1:
        raise IsolatedScenePlanError("AMBIGUOUS_SCENE_ID", f"Duplicate scene_id '{scene_id}' found in target page")

    scene = matching_scenes[0]

    # Validate scene area
    scene_rect = _parse_rect(scene.get("area"), f"Scene '{scene_id}'")
    sx, sy, sw, sh = scene_rect["x"], scene_rect["y"], scene_rect["w"], scene_rect["h"]

    # 5. Filter and transform Character Instances
    all_instances = page.get("character_instances", [])
    if not isinstance(all_instances, list):
        raise IsolatedScenePlanError("INVALID_DOCUMENT_SNAPSHOT", "page.character_instances must be a list")

    scene_instances = [inst for inst in all_instances if isinstance(inst, dict) and inst.get("scene_id") == scene_id]

    if len(scene_instances) > MAX_INSTANCES_PER_SCENE:
        raise IsolatedScenePlanError(
            "MAX_INSTANCES_EXCEEDED",
            f"Scene '{scene_id}' has {len(scene_instances)} character instances, exceeding maximum of {MAX_INSTANCES_PER_SCENE}",
        )

    # Resolve CAST definitions
    all_cast = page.get("cast", [])
    if not isinstance(all_cast, list):
        raise IsolatedScenePlanError("INVALID_DOCUMENT_SNAPSHOT", "page.cast must be a list")

    cast_by_id = {c.get("cast_id"): c for c in all_cast if isinstance(c, dict) and c.get("cast_id")}

    transformed_instances: List[Dict[str, Any]] = []
    referenced_cast_ids: set[str] = set()
    active_references: set[str] = set()
    primary_reference_asset: Optional[str] = None

    for inst in scene_instances:
        inst_id = inst.get("instance_id")
        cast_id = inst.get("cast_id")

        if not cast_id or cast_id not in cast_by_id:
            raise IsolatedScenePlanError(
                "CAST_NOT_FOUND",
                f"Character instance '{inst_id}' references unknown or missing cast_id '{cast_id}'",
            )

        referenced_cast_ids.add(cast_id)
        cast_entry = cast_by_id[cast_id]
        ref_asset = cast_entry.get("reference_asset")
        if isinstance(ref_asset, str) and ref_asset.strip():
            ref_clean = ref_asset.strip()
            active_references.add(ref_clean)
            if primary_reference_asset is None:
                primary_reference_asset = ref_clean

        # Check instance area containment
        inst_rect = _parse_rect(inst.get("area"), f"Character instance '{inst_id}'")
        ix, iy, iw, ih = inst_rect["x"], inst_rect["y"], inst_rect["w"], inst_rect["h"]

        # Strict containment check against scene rectangle
        if (
            ix < sx - GEOMETRY_TOLERANCE
            or iy < sy - GEOMETRY_TOLERANCE
            or (ix + iw) > (sx + sw + GEOMETRY_TOLERANCE)
            or (iy + ih) > (sy + sh + GEOMETRY_TOLERANCE)
        ):
            raise IsolatedScenePlanError(
                "CHARACTER_INSTANCE_OUT_OF_BOUNDS",
                f"Character instance '{inst_id}' area [{ix}, {iy}, {iw}, {ih}] extends outside parent Scene [{sx}, {sy}, {sw}, {sh}]",
            )

        # Coordinate transformation to local canvas [0..1]
        local_u = (ix - sx) / sw
        local_v = (iy - sy) / sh
        local_iw = iw / sw
        local_ih = ih / sh

        transformed_inst = {
            "instance_id": inst_id,
            "cast_id": cast_id,
            "scene_id": scene_id,
            "acting_prompt": inst.get("acting_prompt", ""),
            "area": {
                "shape_type": "rect",
                "x": local_u,
                "y": local_v,
                "w": local_iw,
                "h": local_ih,
            },
            "original_page_area": copy.deepcopy(inst.get("area")),
        }
        if "negative_prompt_override" in inst:
            transformed_inst["negative_prompt_override"] = inst["negative_prompt_override"]
        if "order" in inst:
            transformed_inst["order"] = inst["order"]

        transformed_instances.append(transformed_inst)

    if len(active_references) > MAX_REFERENCES_PER_SCENE:
        raise IsolatedScenePlanError(
            "MAX_REFERENCES_EXCEEDED",
            f"Scene '{scene_id}' instances reference {len(active_references)} distinct reference assets, exceeding maximum of {MAX_REFERENCES_PER_SCENE}",
        )

    # Filter CAST definitions to only referenced ones
    filtered_cast = [
        copy.deepcopy(cast_by_id[cid])
        for cid in sorted(referenced_cast_ids)
    ]

    # Construct validated isolated plan
    plan: Dict[str, Any] = {
        "plan_version": "1.0.0",
        "owner": {
            "document_id": document_snapshot.get("document_id"),
            "page_id": page.get("page_id"),
            "scene_id": scene_id,
        },
        "page_context": {
            "page_id": page.get("page_id"),
            "page_index": resolved_page_index,
            "width_px": page.get("width_px"),
            "height_px": page.get("height_px"),
            "style_prompt": page.get("style_prompt", ""),
            "style_negative_prompt": page.get("style_negative_prompt", ""),
        },
        "scene": {
            "scene_id": scene_id,
            "order": scene.get("order", 0),
            "name": scene.get("name", ""),
            "input_mode": scene.get("input_mode", "simple"),
            "prompt": scene.get("prompt", ""),
            "negative_prompt": scene.get("negative_prompt", ""),
            "original_page_area": copy.deepcopy(scene.get("area")),
            "local_area": {
                "shape_type": "rect",
                "x": 0.0,
                "y": 0.0,
                "w": 1.0,
                "h": 1.0,
            },
        },
        "character_instances": transformed_instances,
        "cast": filtered_cast,
        "reference": {
            "enabled": bool(primary_reference_asset),
            "reference_asset": primary_reference_asset,
        },
        "local_canvas": {
            "width": local_w,
            "height": local_h,
        },
        "placement_mapping": {
            "page_target_rect": copy.deepcopy(scene.get("area")),
            "local_source_rect": {
                "shape_type": "rect",
                "x": 0.0,
                "y": 0.0,
                "w": 1.0,
                "h": 1.0,
            },
            "transform": {
                "scale_x": sw,
                "scale_y": sh,
                "offset_x": sx,
                "offset_y": sy,
            },
        },
        "guide_state": {
            "enabled": False,
            "active": False,
        },
    }

    return plan
