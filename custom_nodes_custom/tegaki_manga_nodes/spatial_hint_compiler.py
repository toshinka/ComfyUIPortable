"""
spatial_hint_compiler.py — Spatial Prompt Hint Compiler (M2A.1)
================================================================
Pure logic module that compiles rough bounding box geometry into short,
structured prompt hints according to Manga Research Pipeline (MRP) principles:
- Horizontal classification (left / centered / right) with ambiguity detection
- Relative scale depth hierarchy ("large in the foreground" / "smaller in the background")
- Scene presence hints ("two distinct people, same scene, both fully visible")
- Transparent provenance metadata (raw_identity, raw_acting, derived_spatial_hint, effective_character_prompt)
- Strict SSOT isolation: Never mutates the persistent TEGAKI_AUTHORING_DOCUMENT.
"""

from typing import Dict, Any, List, Tuple, Optional
import copy


SUPPORTED_HINT_MODES = [
    "off",
    "horizontal",
    "horizontal_presence",
    "spatial_depth",
    "full",
]

# Presence hint definitions according to Card §13
PRESENCE_HINTS: Dict[int, str] = {
    2: "two distinct people, same scene, both fully visible",
    3: "three people, same scene, all visible",
    4: "four people, group composition, all visible",
}


def _get_area_val(box: Dict[str, Any]) -> Tuple[float, float, float, float, float]:
    """Returns (x, y, w, h, area) for a normalized box dictionary."""
    x = float(box.get("x", 0.0))
    y = float(box.get("y", 0.0))
    w = float(box.get("w", box.get("width", 0.0)))
    h = float(box.get("h", box.get("height", 0.0)))
    area = max(w * h, 0.0)
    return x, y, w, h, area


def classify_horizontal_slot(
    rel_center_x: float,
    is_ambiguous: bool = False,
) -> Tuple[str, str]:
    """
    Classifies relative center X in [0.0, 1.0] into a slot identifier and hint text.
    Returns: (slot_name, hint_text)
    """
    if is_ambiguous:
        return "ambiguous", ""

    if rel_center_x < 0.38:
        return "left", "on the left side"
    elif rel_center_x > 0.62:
        return "right", "on the right side"
    else:
        return "center", "centered"


def compute_horizontal_ambiguity(
    instances: List[Dict[str, Any]],
    scene_x: float,
    scene_w: float,
) -> Dict[str, bool]:
    """
    Detects whether instances are in an ambiguous band where forcing left/right is inappropriate.
    Ambiguity triggers if:
    - Center X distance between two instances is < 0.15 relative to scene width, OR
    - Horizontal bounding box overlap ratio > 0.40 of either box.
    """
    ambiguity_map: Dict[str, bool] = {inst.get("instance_id", str(i)): False for i, inst in enumerate(instances)}
    n = len(instances)
    if n <= 1 or scene_w <= 0:
        return ambiguity_map

    parsed = []
    for i, inst in enumerate(instances):
        iid = inst.get("instance_id", str(i))
        ix, iy, iw, ih, _ = _get_area_val(inst.get("area", {}))
        cx = (ix + iw / 2.0 - scene_x) / scene_w
        parsed.append({
            "iid": iid,
            "x0": (ix - scene_x) / scene_w,
            "x1": (ix + iw - scene_x) / scene_w,
            "cx": cx,
            "w": iw / scene_w,
        })

    for i in range(n):
        for j in range(i + 1, n):
            p1 = parsed[i]
            p2 = parsed[j]
            # Center difference check
            cdiff = abs(p1["cx"] - p2["cx"])
            # Overlap check
            overlap_x = max(0.0, min(p1["x1"], p2["x1"]) - max(p1["x0"], p2["x0"]))
            min_w = min(p1["w"], p2["w"])
            overlap_ratio = overlap_x / max(min_w, 1e-6)

            if cdiff < 0.15 or overlap_ratio > 0.40:
                ambiguity_map[p1["iid"]] = True
                ambiguity_map[p2["iid"]] = True

    return ambiguity_map


def classify_depth_hints(
    instances: List[Dict[str, Any]],
    min_ratio: float = 1.8,
) -> Dict[str, Tuple[str, str]]:
    """
    Classifies depth hints based on relative area ratio among instances in a scene.
    Only active if at least 2 instances exist and max_area / min_area >= min_ratio.
    Returns mapping: instance_id -> (depth_slot, hint_text)
    """
    result: Dict[str, Tuple[str, str]] = {}
    if len(instances) < 2:
        for i, inst in enumerate(instances):
            result[inst.get("instance_id", str(i))] = ("none", "")
        return result

    areas = []
    for i, inst in enumerate(instances):
        iid = inst.get("instance_id", str(i))
        _, _, _, _, a = _get_area_val(inst.get("area", {}))
        areas.append((iid, a))

    max_entry = max(areas, key=lambda item: item[1])
    min_entry = min(areas, key=lambda item: item[1])
    max_area = max_entry[1]
    min_area = max(min_entry[1], 1e-6)
    ratio = max_area / min_area

    for iid, a in areas:
        if ratio >= min_ratio:
            if iid == max_entry[0]:
                result[iid] = ("foreground", "large in the foreground")
            elif iid == min_entry[0]:
                result[iid] = ("background", "smaller in the background")
            else:
                result[iid] = ("midground", "")
        else:
            result[iid] = ("neutral", "")

    return result


def detect_arrangement_hint(
    instances: List[Dict[str, Any]],
    scene_x: float,
    scene_y: float,
    scene_w: float,
    scene_h: float,
) -> str:
    """
    Detects whether 2 characters form a clear side-by-side arrangement:
    - High vertical overlap / alignment (|cy1 - cy2| < 0.20)
    - Clear horizontal separation (|cx1 - cx2| >= 0.30)
    - Balanced scale ratio (0.65 <= a1 / a2 <= 1.55)
    """
    if len(instances) != 2 or scene_w <= 0 or scene_h <= 0:
        return ""

    _, y1, _, _, a1 = _get_area_val(instances[0].get("area", {}))
    _, y2, _, _, a2 = _get_area_val(instances[1].get("area", {}))
    x1, _, w1, h1, _ = _get_area_val(instances[0].get("area", {}))
    x2, _, w2, h2, _ = _get_area_val(instances[1].get("area", {}))

    cx1 = (x1 + w1 / 2.0 - scene_x) / scene_w
    cx2 = (x2 + w2 / 2.0 - scene_x) / scene_w
    cy1 = (y1 + h1 / 2.0 - scene_y) / scene_h
    cy2 = (y2 + h2 / 2.0 - scene_y) / scene_h

    vert_diff = abs(cy1 - cy2)
    horiz_diff = abs(cx1 - cx2)
    area_ratio = a1 / max(a2, 1e-6)

    if vert_diff < 0.20 and horiz_diff >= 0.30 and (0.65 <= area_ratio <= 1.55):
        return "side-by-side"
    return ""


def compile_scene_spatial_hints(
    scene: Dict[str, Any],
    instances: List[Dict[str, Any]],
    cast_by_id: Dict[str, Any],
    mode: str = "off",
) -> Tuple[Dict[str, Dict[str, Any]], str]:
    """
    Main entry point for Spatial Prompt Hint compilation for a single scene.
    
    Args:
        scene: Scene dictionary with 'area' {x, y, w, h}.
        instances: List of character instance dictionaries belonging to this scene.
        cast_by_id: Mapping of cast_id to CAST master dictionary.
        mode: Compilation mode in ('off', 'horizontal', 'horizontal_presence', 'spatial_depth', 'full').
        
    Returns:
        (instance_hints_map, scene_presence_hint)
        where instance_hints_map is {instance_id: {
            "instance_id": ...,
            "raw_identity_prompt": ...,
            "raw_acting_prompt": ...,
            "derived_spatial_hint": ...,
            "scene_presence_hint": ...,
            "effective_character_prompt": ...,
            "derived_hints_metadata": {...},
        }}
    """
    if mode not in SUPPORTED_HINT_MODES:
        raise ValueError(f"Unsupported spatial_hint_mode '{mode}'. Supported: {SUPPORTED_HINT_MODES}")

    scene_area = scene.get("area", {})
    sx, sy, sw, sh, s_area = _get_area_val(scene_area)
    sw = max(sw, 1e-6)
    sh = max(sh, 1e-6)

    # 1. Scene presence hint
    char_count = len(instances)
    raw_presence_hint = PRESENCE_HINTS.get(char_count, "")
    include_presence = mode in ("horizontal_presence", "full")
    scene_presence_hint = raw_presence_hint if include_presence else ""

    # 2. Horizontal ambiguity and depth
    ambiguity_map = compute_horizontal_ambiguity(instances, sx, sw)
    depth_hints = classify_depth_hints(instances, min_ratio=1.8)
    arrangement_hint = detect_arrangement_hint(instances, sx, sy, sw, sh)

    result_map: Dict[str, Dict[str, Any]] = {}

    for i, inst in enumerate(instances):
        iid = inst.get("instance_id", f"inst_{i+1}")
        cid = inst.get("cast_id", "")
        cast_master = cast_by_id.get(cid, {})

        raw_id_prompt = cast_master.get("identity_prompt", "").strip()
        raw_act_prompt = inst.get("acting_prompt", "").strip()

        ix, iy, iw, ih, ia = _get_area_val(inst.get("area", {}))
        cx = (ix + iw / 2.0 - sx) / sw
        cy = (iy + ih / 2.0 - sy) / sh

        is_ambig = ambiguity_map.get(iid, False)
        h_slot, h_hint = classify_horizontal_slot(cx, is_ambiguous=is_ambig)
        d_slot, d_hint = depth_hints.get(iid, ("none", ""))

        # Assemble derived spatial hint based on mode
        hint_parts = []
        if mode == "off":
            pass
        elif mode == "horizontal":
            if h_hint:
                hint_parts.append(h_hint)
        elif mode == "horizontal_presence":
            if h_hint:
                hint_parts.append(h_hint)
        elif mode == "spatial_depth":
            if d_hint:
                hint_parts.append(d_hint)
            elif h_hint:
                hint_parts.append(h_hint)
        elif mode == "full":
            if d_hint:
                hint_parts.append(d_hint)
            if h_hint:
                hint_parts.append(h_hint)
            if arrangement_hint and char_count == 2 and not d_hint:
                # Add side-by-side arrangement hint if not conflicting with depth
                hint_parts.append(arrangement_hint)

        derived_spatial_hint = ", ".join(hint_parts)

        # Assemble effective prompt
        eff_parts = [p for p in [raw_id_prompt, raw_act_prompt, derived_spatial_hint] if p]
        effective_character_prompt = ", ".join(eff_parts)

        result_map[iid] = {
            "instance_id": iid,
            "cast_id": cid,
            "raw_identity_prompt": raw_id_prompt,
            "raw_acting_prompt": raw_act_prompt,
            "derived_spatial_hint": derived_spatial_hint,
            "scene_presence_hint": scene_presence_hint,
            "effective_character_prompt": effective_character_prompt,
            "derived_hints_metadata": {
                "rel_center_x": round(cx, 4),
                "rel_center_y": round(cy, 4),
                "horizontal_slot": h_slot,
                "depth_slot": d_slot,
                "is_ambiguous": is_ambig,
                "arrangement_hint": arrangement_hint if mode == "full" else "",
                "mode": mode,
            }
        }

    return result_map, scene_presence_hint
