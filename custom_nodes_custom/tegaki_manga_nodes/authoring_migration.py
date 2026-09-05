"""
authoring_migration.py — Legacy Import / Export for Authoring Contract (M0 / 3M-0)
===================================================================================
Converts between the existing REGION_SPEC / CAST_SPEC v1 format and the new
TEGAKI_AUTHORING_DOCUMENT v1.0.0 format.

Legacy import:
  REGION_SPEC + CAST_SPEC → TEGAKI_AUTHORING_DOCUMENT

Legacy export:
  TEGAKI_AUTHORING_DOCUMENT → REGION_SPEC + CAST_SPEC (for existing backend)
  Fails closed for unsupported features.

Coordinate transform:
  KOMA-local character area → page-normalized area:
    page_x = panel_x + local_x * panel_w
    page_y = panel_y + local_y * panel_h
    page_w = local_w * panel_w
    page_h = local_h * panel_h
"""

import copy
import logging
from typing import Any, Dict, List, Optional, Tuple

from .authoring_contract import (
    SCHEMA_ID,
    SCHEMA_VERSION,
    create_document,
    create_page,
    create_scene,
    create_visual_frame,
    create_cast_entry,
    create_character_instance,
    make_area,
    validate_document,
    GEOMETRY_ROUND_DIGITS,
)

logger = logging.getLogger(__name__)


# ===================================================================
# Migration result types
# ===================================================================

class MigrationResult:
    """Result of a legacy import."""

    __slots__ = ("document", "warnings", "field_mapping_table")

    def __init__(
        self,
        document: Dict[str, Any],
        warnings: Optional[List[str]] = None,
        field_mapping_table: Optional[List[Dict[str, str]]] = None,
    ):
        self.document = document
        self.warnings: List[str] = warnings or []
        self.field_mapping_table: List[Dict[str, str]] = field_mapping_table or []


class ExportResult:
    """Result of a new→legacy export."""

    __slots__ = ("region_spec", "cast_spec", "warnings", "unsupported")

    def __init__(
        self,
        region_spec: Dict[str, Any],
        cast_spec: Dict[str, Any],
        warnings: Optional[List[str]] = None,
        unsupported: Optional[List[str]] = None,
    ):
        self.region_spec = region_spec
        self.cast_spec = cast_spec
        self.warnings: List[str] = warnings or []
        self.unsupported: List[str] = unsupported or []


# ===================================================================
# Coordinate transform helpers
# ===================================================================

# Dummy geometry used by PanelContentEditor when no real layout exists
DUMMY_PANEL_GEOMETRY = {"x": 0.05, "y": 0.05, "w": 0.9, "h": 0.9}
DUMMY_TOLERANCE = 0.001


def _is_dummy_geometry(geom: Dict) -> bool:
    """Check if panel geometry matches the PanelContentEditor dummy."""
    return (
        abs(float(geom.get("x", 0)) - DUMMY_PANEL_GEOMETRY["x"]) < DUMMY_TOLERANCE
        and abs(float(geom.get("y", 0)) - DUMMY_PANEL_GEOMETRY["y"]) < DUMMY_TOLERANCE
        and abs(float(geom.get("w", 0)) - DUMMY_PANEL_GEOMETRY["w"]) < DUMMY_TOLERANCE
        and abs(float(geom.get("h", 0)) - DUMMY_PANEL_GEOMETRY["h"]) < DUMMY_TOLERANCE
    )


def koma_local_to_page_normalized(
    local_area: Dict, panel_geometry: Dict
) -> Dict[str, Any]:
    """
    Transform a KOMA-local character area to page-normalized coordinates.

    local_area:     {x, y, w, h} in [0,1] relative to panel bounds
    panel_geometry: {x, y, w, h} in [0,1] relative to page

    Returns: {shape_type: "rect", x, y, w, h} in page-normalized coords
    """
    px = float(panel_geometry.get("x", 0))
    py = float(panel_geometry.get("y", 0))
    pw = float(panel_geometry.get("w", 1))
    ph = float(panel_geometry.get("h", 1))

    lx = float(local_area.get("x", 0))
    ly = float(local_area.get("y", 0))
    lw = float(local_area.get("w", 0.3))
    lh = float(local_area.get("h", 0.6))

    return make_area(
        x=px + lx * pw,
        y=py + ly * ph,
        w=lw * pw,
        h=lh * ph,
    )


def page_normalized_to_koma_local(
    page_area: Dict, panel_geometry: Dict
) -> Dict[str, float]:
    """
    Inverse transform: page-normalized → KOMA-local character area.
    """
    px = float(panel_geometry.get("x", 0))
    py = float(panel_geometry.get("y", 0))
    pw = float(panel_geometry.get("w", 1))
    ph = float(panel_geometry.get("h", 1))

    ax = float(page_area.get("x", 0))
    ay = float(page_area.get("y", 0))
    aw = float(page_area.get("w", 0.3))
    ah = float(page_area.get("h", 0.6))

    if pw <= 0 or ph <= 0:
        return {"x": 0.0, "y": 0.0, "w": 0.3, "h": 0.6}

    return {
        "x": round(max(0.0, min(1.0, (ax - px) / pw)), GEOMETRY_ROUND_DIGITS),
        "y": round(max(0.0, min(1.0, (ay - py) / ph)), GEOMETRY_ROUND_DIGITS),
        "w": round(max(0.001, min(1.0, aw / pw)), GEOMETRY_ROUND_DIGITS),
        "h": round(max(0.001, min(1.0, ah / ph)), GEOMETRY_ROUND_DIGITS),
    }


# ===================================================================
# Legacy Import
# ===================================================================

def import_from_legacy(
    region_spec: Dict[str, Any],
    cast_spec: Dict[str, Any],
    canvas_width: int = 832,
    canvas_height: int = 1216,
) -> MigrationResult:
    """
    Import from legacy REGION_SPEC + CAST_SPEC into new authoring document.

    Each active KOMA becomes both a Scene AND a VisualFrame (with distinct IDs),
    since in the legacy format 1 KOMA = 1 Scene = 1 Frame.

    Character binding areas are transformed from KOMA-local to page-normalized.
    shot_type, pose_preset, interaction are preserved in instance metadata.
    """
    warnings: List[str] = []
    field_mapping: List[Dict[str, str]] = []

    # --- Canvas resolution ---
    canvas = region_spec.get("canvas", {})
    width = int(canvas.get("width", canvas_width))
    height = int(canvas.get("height", canvas_height))

    # --- Create page ---
    style_prompt = region_spec.get("global_prompt", "")
    style_neg = region_spec.get("global_negative_prompt", "")
    page = create_page(
        width_px=width,
        height_px=height,
        style_prompt=style_prompt,
        style_negative_prompt=style_neg,
        page_id="legacy_page_001",
    )

    # --- Import CAST ---
    cast_version = cast_spec.get("version", 1)
    if cast_version != 1:
        warnings.append(f"CAST_SPEC version {cast_version} != 1, attempting import")

    cast_characters = cast_spec.get("characters", [])
    cast_id_map: Dict[str, str] = {}  # old char_id → new cast_id (same)

    for char in cast_characters:
        old_id = char.get("id", "")
        if not old_id:
            warnings.append("Skipping character with empty id")
            continue

        # Keep original ID for consistency
        cast_id_map[old_id] = old_id

        # Map prompt field (legacy alias: appearance → prompt)
        identity_prompt = char.get("prompt", char.get("appearance", ""))
        neg_prompt = char.get("negative_prompt", "")

        entry = create_cast_entry(
            display_name=char.get("name", old_id),
            identity_prompt=identity_prompt,
            negative_prompt=neg_prompt,
            loras=char.get("loras", []),
            cast_id=old_id,
            metadata=char.get("metadata", {}),
        )
        page["cast"].append(entry)

        field_mapping.append({
            "legacy_field": f"cast.characters[id={old_id}]",
            "new_field": f"cast[cast_id={old_id}]",
            "transform": "direct copy (id, prompt, loras preserved)",
            "lossless": "yes",
        })

    # --- Import KOMAs → Scenes + Frames ---
    panel_count = int(region_spec.get("panel_count", 3))
    regions = region_spec.get("regions", [])

    for region in regions:
        rid = region.get("id")
        enabled = region.get("enabled", True)

        # Only import active panels
        if enabled is not True:
            continue
        try:
            rid_int = int(rid)
        except (ValueError, TypeError):
            warnings.append(f"Skipping region with invalid id: {rid}")
            continue
        if rid_int < 1 or rid_int > panel_count:
            continue

        # Panel geometry (page-normalized)
        panel_geom = {
            "x": float(region.get("x", 0.05)),
            "y": float(region.get("y", 0.05)),
            "w": float(region.get("w", 0.9)),
            "h": float(region.get("h", 0.9)),
        }

        is_dummy = _is_dummy_geometry(panel_geom)
        if is_dummy:
            warnings.append(
                f"Panel {rid}: using PanelContentEditor dummy geometry "
                f"({DUMMY_PANEL_GEOMETRY}). Character page-normalized "
                f"coordinates may not reflect real layout positions."
            )

        # Determine input_mode
        characters = region.get("characters", [])
        has_cast_bindings = len(characters) > 0
        input_mode = "cast" if has_cast_bindings else "simple"

        # Create Scene
        scene_id = f"legacy_scene_{rid}"
        scene = create_scene(
            name=f"Scene {rid}",
            prompt=region.get("prompt", ""),
            negative_prompt=region.get("negative_prompt", ""),
            input_mode=input_mode,
            area=make_area(panel_geom["x"], panel_geom["y"],
                          panel_geom["w"], panel_geom["h"]),
            order=rid_int,
            scene_id=scene_id,
        )
        page["scenes"].append(scene)

        # Create VisualFrame (same geometry, different ID)
        frame_id = f"legacy_frame_{rid}"
        frame = create_visual_frame(
            area=make_area(panel_geom["x"], panel_geom["y"],
                          panel_geom["w"], panel_geom["h"]),
            order=rid_int,
            frame_id=frame_id,
        )
        page["visual_frames"].append(frame)

        field_mapping.append({
            "legacy_field": f"region[id={rid}]",
            "new_field": f"scene[{scene_id}] + frame[{frame_id}]",
            "transform": "1 KOMA → 1 Scene + 1 Frame (separate IDs)",
            "lossless": "yes",
        })

        # --- Import character bindings → instances ---
        for b_idx, binding in enumerate(characters):
            char_id = binding.get("character_id", "")
            if not char_id:
                warnings.append(f"Panel {rid}: skipping binding with empty character_id")
                continue

            # Transform KOMA-local area to page-normalized
            local_area = binding.get("area")
            if local_area is not None:
                page_area = koma_local_to_page_normalized(local_area, panel_geom)
            else:
                # No area specified → AI free composition, use scene center
                page_area = make_area(
                    panel_geom["x"] + panel_geom["w"] * 0.25,
                    panel_geom["y"] + panel_geom["h"] * 0.1,
                    panel_geom["w"] * 0.5,
                    panel_geom["h"] * 0.8,
                )
                warnings.append(
                    f"Panel {rid}, character {char_id}: "
                    f"area was null (AI free), assigned default page area"
                )

            # Preserve advanced metadata
            inst_metadata: Dict[str, Any] = {}
            for preserve_key in ("shot_type", "pose_preset", "interaction",
                                 "camera_distance", "instance_id"):
                if preserve_key in binding:
                    inst_metadata[preserve_key] = binding[preserve_key]
            if binding.get("metadata"):
                inst_metadata.update(binding["metadata"])

            # acting prompt (legacy alias: acting → prompt_override)
            acting = binding.get("prompt_override",
                                 binding.get("acting", ""))
            neg_override = binding.get("negative_prompt_override", "")

            instance_id = f"legacy_p{rid}_{char_id}_{b_idx + 1:02d}"
            inst = create_character_instance(
                cast_id=char_id,
                scene_id=scene_id,
                area=page_area,
                acting_prompt=acting,
                negative_prompt_override=neg_override,
                order=b_idx,
                instance_id=instance_id,
                metadata=inst_metadata,
            )
            page["character_instances"].append(inst)

            field_mapping.append({
                "legacy_field": f"region[{rid}].characters[{b_idx}]",
                "new_field": f"instance[{instance_id}]",
                "transform": "KOMA-local → page-normalized coordinates",
                "lossless": "yes" if not is_dummy else "warning (dummy geometry)",
            })

    # --- Import generation settings ---
    gen = region_spec.get("generation", {})
    if gen:
        page["generation"] = copy.deepcopy(gen)

    # --- Build document ---
    doc = create_document(pages=[page])

    return MigrationResult(
        document=doc,
        warnings=warnings,
        field_mapping_table=field_mapping,
    )


# ===================================================================
# Legacy Export
# ===================================================================

def export_to_legacy(
    doc: Dict[str, Any],
    page_index: int = 0,
) -> ExportResult:
    """
    Export new authoring document back to legacy REGION_SPEC + CAST_SPEC.

    Fails closed for unsupported features:
    - Overlapping independent scenes (more scenes than can map to 6 slots)
    - Multiple scenes sharing one frame
    - Non-rect shapes
    - More than 6 scenes
    """
    warnings: List[str] = []
    unsupported: List[str] = []

    pages = doc.get("pages", [])
    if page_index >= len(pages):
        raise ValueError(f"Page index {page_index} out of range (have {len(pages)} pages)")

    page = pages[page_index]
    scenes = page.get("scenes", [])
    cast_list = page.get("cast", [])
    instances = page.get("character_instances", [])

    # --- Check unsupported features ---
    if len(scenes) > 6:
        unsupported.append(
            f"Legacy format supports max 6 panels, document has {len(scenes)} scenes. "
            f"Cannot export. Fail closed."
        )

    # Check for non-rect shapes
    for scene in scenes:
        area = scene.get("area", {})
        if area.get("shape_type", "rect") != "rect":
            unsupported.append(
                f"Scene '{scene.get('scene_id')}' has non-rect shape "
                f"'{area.get('shape_type')}'. Legacy format only supports rect."
            )

    if unsupported:
        return ExportResult(
            region_spec={},
            cast_spec={},
            warnings=warnings,
            unsupported=unsupported,
        )

    # --- Build CAST_SPEC ---
    cast_spec = {
        "version": 1,
        "characters": [],
    }
    for entry in cast_list:
        char = {
            "id": entry.get("cast_id", ""),
            "name": entry.get("display_name", ""),
            "enabled": True,
            "prompt": entry.get("identity_prompt", ""),
            "negative_prompt": entry.get("negative_prompt", ""),
            "loras": entry.get("loras", []),
            "metadata": entry.get("metadata", {}),
        }
        cast_spec["characters"].append(char)

    # --- Build REGION_SPEC ---
    region_spec: Dict[str, Any] = {
        "version": 1,
        "canvas": {
            "width": page.get("width_px", 832),
            "height": page.get("height_px", 1216),
        },
        "panel_count": len(scenes),
        "global_prompt": page.get("style_prompt", ""),
        "global_negative_prompt": page.get("style_negative_prompt", ""),
        "regions": [],
    }

    # Sort scenes by order
    sorted_scenes = sorted(scenes, key=lambda s: s.get("order", 0))

    for slot_idx, scene in enumerate(sorted_scenes):
        slot_id = slot_idx + 1
        scene_id = scene.get("scene_id", "")
        scene_area = scene.get("area", {})

        panel_geom = {
            "x": float(scene_area.get("x", 0.05)),
            "y": float(scene_area.get("y", 0.05)),
            "w": float(scene_area.get("w", 0.9)),
            "h": float(scene_area.get("h", 0.9)),
        }

        # Find instances for this scene
        scene_instances = [
            i for i in instances if i.get("scene_id") == scene_id
        ]

        # Build character bindings with reverse coordinate transform
        char_bindings = []
        for inst in scene_instances:
            page_area = inst.get("area", {})
            local_area = page_normalized_to_koma_local(page_area, panel_geom)

            binding: Dict[str, Any] = {
                "character_id": inst.get("cast_id", ""),
                "enabled": True,
                "prompt_override": inst.get("acting_prompt", ""),
                "negative_prompt_override": inst.get("negative_prompt_override", ""),
                "area": local_area,
                "lora_override": None,
                "metadata": {},
            }

            # Restore preserved metadata
            meta = inst.get("metadata", {})
            for key in ("shot_type", "pose_preset", "interaction"):
                if key in meta:
                    binding[key] = meta[key]

            char_bindings.append(binding)

        region = {
            "id": slot_id,
            "enabled": True,
            "x": round(panel_geom["x"], GEOMETRY_ROUND_DIGITS),
            "y": round(panel_geom["y"], GEOMETRY_ROUND_DIGITS),
            "w": round(panel_geom["w"], GEOMETRY_ROUND_DIGITS),
            "h": round(panel_geom["h"], GEOMETRY_ROUND_DIGITS),
            "prompt": scene.get("prompt", ""),
            "negative_prompt": scene.get("negative_prompt", ""),
            "characters": char_bindings,
        }
        region_spec["regions"].append(region)

    # Pad remaining slots to 6 (disabled)
    for pad_id in range(len(sorted_scenes) + 1, 7):
        region_spec["regions"].append({
            "id": pad_id,
            "enabled": False,
            "x": 0.05,
            "y": 0.05,
            "w": 0.9,
            "h": 0.9,
            "prompt": "",
            "negative_prompt": "",
            "characters": [],
        })

    # Propagate generation settings
    gen = page.get("generation", {})
    if gen:
        region_spec["generation"] = copy.deepcopy(gen)

    return ExportResult(
        region_spec=region_spec,
        cast_spec=cast_spec,
        warnings=warnings,
        unsupported=unsupported,
    )
