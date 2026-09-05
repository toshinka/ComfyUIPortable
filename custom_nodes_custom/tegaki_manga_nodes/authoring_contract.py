"""
authoring_contract.py — Tegaki Manga Authoring Document Contract (M0 / 3M-0)
==============================================================================
Backend-independent versioned authoring document schema.

This module defines the single persistent authoring truth for manga page
composition. It is independent of ComfyUI runtime objects, Impact regional
adapters, ControlNet tensors, and KSampler state.

Semantic Scene Regions and Visual Panel Frames are independent entities
with separate ID spaces and separate geometry. Scene != Frame.

Coordinates are page-normalized [0, 1]. Character instance areas are
page-normalized (not panel-local).

Unknown fields within a known schema version are preserved on round-trip.
Unknown newer schema versions fail closed — never silently overwritten.
"""

import copy
import json
import math
import uuid
from typing import Any, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Schema identity
# ---------------------------------------------------------------------------

SCHEMA_ID = "TEGAKI_AUTHORING_DOCUMENT"
SCHEMA_VERSION = "1.0.0"
KNOWN_VERSIONS = frozenset({"1.0.0"})

# ---------------------------------------------------------------------------
# Geometry constants
# ---------------------------------------------------------------------------

MIN_RECT_SIZE = 0.001
GEOMETRY_ROUND_DIGITS = 4

# ---------------------------------------------------------------------------
# Valid enums
# ---------------------------------------------------------------------------

VALID_INPUT_MODES = frozenset({"simple", "cast"})
VALID_SHAPE_TYPES = frozenset({"rect"})  # polygon, freeform: future


# ===================================================================
# Validation result
# ===================================================================

class ValidationResult:
    """Machine-readable validation diagnostic."""

    __slots__ = ("errors", "warnings", "normalized_document")

    def __init__(
        self,
        errors: Optional[List[str]] = None,
        warnings: Optional[List[str]] = None,
        normalized_document: Optional[Dict[str, Any]] = None,
    ):
        self.errors: List[str] = errors or []
        self.warnings: List[str] = warnings or []
        self.normalized_document: Optional[Dict[str, Any]] = normalized_document

    @property
    def valid(self) -> bool:
        return len(self.errors) == 0


# ===================================================================
# ID generation
# ===================================================================

def generate_id(prefix: str = "") -> str:
    """Generate a stable unique ID with optional human-readable prefix."""
    short = uuid.uuid4().hex[:12]
    if prefix:
        return f"{prefix}_{short}"
    return short


# ===================================================================
# Geometry helpers
# ===================================================================

def _is_finite_number(val: Any) -> bool:
    """Check that val is a finite float/int (not bool, not NaN, not inf)."""
    if isinstance(val, bool):
        return False
    if not isinstance(val, (int, float)):
        return False
    return math.isfinite(val)


def validate_area(area: Dict[str, Any], context: str = "") -> List[str]:
    """
    Validate a page-normalized area dict.

    Returns a list of error strings (empty == valid).
    For authoring input: fail clearly with descriptive messages.
    """
    errors: List[str] = []
    ctx = f" ({context})" if context else ""

    if not isinstance(area, dict):
        errors.append(f"area must be dict{ctx}, got {type(area).__name__}")
        return errors

    shape_type = area.get("shape_type", "rect")
    if shape_type not in VALID_SHAPE_TYPES:
        errors.append(f"unsupported shape_type '{shape_type}'{ctx}")

    for key in ("x", "y", "w", "h"):
        val = area.get(key)
        if val is None:
            errors.append(f"area.{key} is missing{ctx}")
        elif not _is_finite_number(val):
            errors.append(f"area.{key} must be a finite number{ctx}, got {val!r}")

    if errors:
        return errors

    x, y, w, h = float(area["x"]), float(area["y"]), float(area["w"]), float(area["h"])

    if w <= 0:
        errors.append(f"area.w must be > 0{ctx}, got {w}")
    if h <= 0:
        errors.append(f"area.h must be > 0{ctx}, got {h}")
    if x < 0 or x > 1:
        errors.append(f"area.x out of [0,1]{ctx}, got {x}")
    if y < 0 or y > 1:
        errors.append(f"area.y out of [0,1]{ctx}, got {y}")
    if x + w > 1.0 + 0.0001:
        errors.append(f"area.x+w exceeds 1.0{ctx}, got {x + w}")
    if y + h > 1.0 + 0.0001:
        errors.append(f"area.y+h exceeds 1.0{ctx}, got {y + h}")

    return errors


def make_area(x: float, y: float, w: float, h: float,
              shape_type: str = "rect") -> Dict[str, Any]:
    """Create an area dict with rounded coordinates (does not validate bounds; use validate_area for validation)."""
    return {
        "shape_type": shape_type,
        "x": round(float(x), GEOMETRY_ROUND_DIGITS),
        "y": round(float(y), GEOMETRY_ROUND_DIGITS),
        "w": round(float(w), GEOMETRY_ROUND_DIGITS),
        "h": round(float(h), GEOMETRY_ROUND_DIGITS),
    }


# ===================================================================
# Factory functions
# ===================================================================

def create_document(pages: Optional[List[Dict]] = None,
                    metadata: Optional[Dict] = None) -> Dict[str, Any]:
    """Create a new empty authoring document."""
    return {
        "schema_id": SCHEMA_ID,
        "schema_version": SCHEMA_VERSION,
        "pages": pages or [],
        "metadata": metadata or {},
    }


def create_page(width_px: int, height_px: int,
                style_prompt: str = "",
                style_negative_prompt: str = "",
                page_id: Optional[str] = None,
                metadata: Optional[Dict] = None) -> Dict[str, Any]:
    """Create a new page with the given resolution."""
    return {
        "page_id": page_id or generate_id("page"),
        "width_px": int(width_px),
        "height_px": int(height_px),
        "style_prompt": style_prompt,
        "style_negative_prompt": style_negative_prompt,
        "scenes": [],
        "visual_frames": [],
        "cast": [],
        "character_instances": [],
        "guides": [],
        "generation": {},
        "metadata": metadata or {},
    }


def create_scene(name: str = "",
                 prompt: str = "",
                 negative_prompt: str = "",
                 input_mode: str = "simple",
                 area: Optional[Dict] = None,
                 order: int = 0,
                 scene_id: Optional[str] = None,
                 metadata: Optional[Dict] = None) -> Dict[str, Any]:
    """Create a new semantic scene region."""
    if input_mode not in VALID_INPUT_MODES:
        raise ValueError(f"input_mode must be one of {VALID_INPUT_MODES}, got '{input_mode}'")
    return {
        "scene_id": scene_id or generate_id("scene"),
        "name": name,
        "prompt": prompt,
        "negative_prompt": negative_prompt,
        "input_mode": input_mode,
        "area": area or make_area(0.0, 0.0, 1.0, 1.0),
        "order": int(order),
        "metadata": metadata or {},
    }


def create_visual_frame(area: Optional[Dict] = None,
                        order: int = 0,
                        frame_id: Optional[str] = None,
                        metadata: Optional[Dict] = None) -> Dict[str, Any]:
    """Create a new visual panel frame."""
    return {
        "frame_id": frame_id or generate_id("frame"),
        "shape": area or make_area(0.0, 0.0, 1.0, 1.0),
        "order": int(order),
        "metadata": metadata or {},
    }


def create_cast_entry(display_name: str = "",
                      identity_prompt: str = "",
                      negative_prompt: str = "",
                      loras: Optional[List[Dict]] = None,
                      cast_id: Optional[str] = None,
                      metadata: Optional[Dict] = None) -> Dict[str, Any]:
    """Create a new CAST master entry."""
    return {
        "cast_id": cast_id or generate_id("cast"),
        "display_name": display_name,
        "identity_prompt": identity_prompt,
        "negative_prompt": negative_prompt,
        "loras": loras or [],
        "metadata": metadata or {},
    }


def create_character_instance(cast_id: str,
                              scene_id: str,
                              area: Optional[Dict] = None,
                              acting_prompt: str = "",
                              negative_prompt_override: str = "",
                              order: int = 0,
                              instance_id: Optional[str] = None,
                              metadata: Optional[Dict] = None) -> Dict[str, Any]:
    """Create a character appearance instance in a scene."""
    return {
        "instance_id": instance_id or generate_id("inst"),
        "cast_id": cast_id,
        "scene_id": scene_id,
        "area": area or make_area(0.1, 0.1, 0.3, 0.6),
        "acting_prompt": acting_prompt,
        "negative_prompt_override": negative_prompt_override,
        "order": int(order),
        "metadata": metadata or {},
    }


def create_guide(guide_type: str = "frame_guide",
                 asset_reference: Optional[str] = None,
                 placement: Optional[Dict] = None,
                 enabled: bool = True,
                 guide_id: Optional[str] = None,
                 metadata: Optional[Dict] = None) -> Dict[str, Any]:
    """Create a guide entry."""
    return {
        "guide_id": guide_id or generate_id("guide"),
        "guide_type": guide_type,
        "asset_reference": asset_reference,
        "placement": placement,
        "enabled": enabled,
        "metadata": metadata or {},
    }


# ===================================================================
# Serialization
# ===================================================================

def to_dict(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Return a deep copy suitable for JSON serialization."""
    return copy.deepcopy(doc)


def to_json(doc: Dict[str, Any], indent: int = 2) -> str:
    """Serialize document to JSON string."""
    return json.dumps(to_dict(doc), indent=indent, ensure_ascii=False)


def from_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Load a document from a plain dict (e.g. parsed JSON).

    Performs version check. Unknown newer versions fail closed.
    Unknown fields within a known version are preserved.
    """
    if not isinstance(data, dict):
        raise ValueError(f"Expected dict, got {type(data).__name__}")

    sid = data.get("schema_id")
    if sid != SCHEMA_ID:
        raise ValueError(
            f"Unknown schema_id '{sid}', expected '{SCHEMA_ID}'"
        )

    version = data.get("schema_version")
    if version not in KNOWN_VERSIONS:
        raise ValueError(
            f"Unknown schema_version '{version}'. "
            f"Known versions: {sorted(KNOWN_VERSIONS)}. "
            f"Cannot read a newer or unknown format — refusing to "
            f"silently overwrite. Fail closed."
        )

    # Deep copy to avoid mutation of caller's data.
    # Unknown fields are preserved by copying the entire dict.
    return copy.deepcopy(data)


def from_json(json_str: str) -> Dict[str, Any]:
    """Deserialize document from JSON string."""
    data = json.loads(json_str)
    return from_dict(data)


# ===================================================================
# Validation
# ===================================================================

def validate_document(doc: Dict[str, Any]) -> ValidationResult:
    """
    Validate an authoring document.

    Returns ValidationResult with errors, warnings, and the
    (potentially normalized) document. Unknown fields are preserved.
    """
    errors: List[str] = []
    warnings: List[str] = []

    if not isinstance(doc, dict):
        return ValidationResult(
            errors=[f"Document must be dict, got {type(doc).__name__}"]
        )

    # --- Schema identity ---
    sid = doc.get("schema_id")
    if sid != SCHEMA_ID:
        errors.append(f"Invalid schema_id: '{sid}', expected '{SCHEMA_ID}'")

    version = doc.get("schema_version")
    if version not in KNOWN_VERSIONS:
        errors.append(
            f"Unknown schema_version '{version}'. "
            f"Known: {sorted(KNOWN_VERSIONS)}. Fail closed."
        )
        # Cannot validate further if version is unknown
        return ValidationResult(errors=errors, warnings=warnings)

    pages = doc.get("pages")
    if not isinstance(pages, list):
        errors.append("'pages' must be a list")
        return ValidationResult(errors=errors, warnings=warnings)

    seen_page_ids: set = set()
    for pi, page in enumerate(pages):
        if isinstance(page, dict):
            pid = page.get("page_id")
            if isinstance(pid, str) and pid:
                if pid in seen_page_ids:
                    errors.append(f"duplicate page_id '{pid}' in document")
                else:
                    seen_page_ids.add(pid)
        page_errors, page_warnings = _validate_page(page, pi)
        errors.extend(page_errors)
        warnings.extend(page_warnings)

    result_doc = copy.deepcopy(doc) if not errors else None
    return ValidationResult(
        errors=errors,
        warnings=warnings,
        normalized_document=result_doc,
    )


def _validate_page(page: Dict[str, Any], page_index: int) -> Tuple[List[str], List[str]]:
    """Validate a single page. Returns (errors, warnings)."""
    errors: List[str] = []
    warnings: List[str] = []
    ctx = f"page[{page_index}]"

    if not isinstance(page, dict):
        errors.append(f"{ctx}: must be dict")
        return errors, warnings

    # --- page_id ---
    page_id = page.get("page_id")
    if not isinstance(page_id, str) or not page_id:
        errors.append(f"{ctx}: page_id must be non-empty string")

    # --- Resolution ---
    for dim in ("width_px", "height_px"):
        val = page.get(dim)
        if not isinstance(val, int) or isinstance(val, bool) or val <= 0:
            errors.append(f"{ctx}: {dim} must be positive int, got {val!r}")

    # --- Collect IDs for FK checks ---
    scene_ids: set = set()
    cast_ids: set = set()
    frame_ids: set = set()
    instance_ids: set = set()
    guide_ids: set = set()

    # --- Scenes ---
    scenes = page.get("scenes", [])
    if not isinstance(scenes, list):
        errors.append(f"{ctx}: scenes must be list")
        scenes = []
    for si, scene in enumerate(scenes):
        s_ctx = f"{ctx}.scenes[{si}]"
        if not isinstance(scene, dict):
            errors.append(f"{s_ctx}: must be dict")
            continue
        sid = scene.get("scene_id")
        if not isinstance(sid, str) or not sid:
            errors.append(f"{s_ctx}: scene_id must be non-empty string")
        elif sid in scene_ids:
            errors.append(f"{s_ctx}: duplicate scene_id '{sid}'")
        else:
            scene_ids.add(sid)

        mode = scene.get("input_mode", "simple")
        if mode not in VALID_INPUT_MODES:
            errors.append(f"{s_ctx}: invalid input_mode '{mode}'")

        area = scene.get("area")
        if area is not None:
            area_errs = validate_area(area, s_ctx)
            errors.extend(area_errs)

    # --- Visual frames ---
    frames = page.get("visual_frames", [])
    if not isinstance(frames, list):
        errors.append(f"{ctx}: visual_frames must be list")
        frames = []
    for fi, frame in enumerate(frames):
        f_ctx = f"{ctx}.visual_frames[{fi}]"
        if not isinstance(frame, dict):
            errors.append(f"{f_ctx}: must be dict")
            continue
        fid = frame.get("frame_id")
        if not isinstance(fid, str) or not fid:
            errors.append(f"{f_ctx}: frame_id must be non-empty string")
        elif fid in frame_ids:
            errors.append(f"{f_ctx}: duplicate frame_id '{fid}'")
        else:
            frame_ids.add(fid)

        shape = frame.get("shape")
        if shape is not None:
            shape_errs = validate_area(shape, f_ctx)
            errors.extend(shape_errs)

    # --- CAST ---
    cast_list = page.get("cast", [])
    if not isinstance(cast_list, list):
        errors.append(f"{ctx}: cast must be list")
        cast_list = []
    for ci, cast_entry in enumerate(cast_list):
        c_ctx = f"{ctx}.cast[{ci}]"
        if not isinstance(cast_entry, dict):
            errors.append(f"{c_ctx}: must be dict")
            continue
        cid = cast_entry.get("cast_id")
        if not isinstance(cid, str) or not cid:
            errors.append(f"{c_ctx}: cast_id must be non-empty string")
        elif cid in cast_ids:
            errors.append(f"{c_ctx}: duplicate cast_id '{cid}'")
        else:
            cast_ids.add(cid)

    # --- Character instances ---
    instances = page.get("character_instances", [])
    if not isinstance(instances, list):
        errors.append(f"{ctx}: character_instances must be list")
        instances = []
    for ii, inst in enumerate(instances):
        i_ctx = f"{ctx}.character_instances[{ii}]"
        if not isinstance(inst, dict):
            errors.append(f"{i_ctx}: must be dict")
            continue

        iid = inst.get("instance_id")
        if not isinstance(iid, str) or not iid:
            errors.append(f"{i_ctx}: instance_id must be non-empty string")
        elif iid in instance_ids:
            errors.append(f"{i_ctx}: duplicate instance_id '{iid}'")
        else:
            instance_ids.add(iid)

        # FK: cast_id
        ref_cast = inst.get("cast_id")
        if not isinstance(ref_cast, str) or not ref_cast:
            errors.append(f"{i_ctx}: cast_id must be non-empty string")
        elif ref_cast not in cast_ids:
            errors.append(
                f"{i_ctx}: cast_id '{ref_cast}' not found in page cast"
            )

        # FK: scene_id
        ref_scene = inst.get("scene_id")
        if not isinstance(ref_scene, str) or not ref_scene:
            errors.append(f"{i_ctx}: scene_id must be non-empty string")
        elif ref_scene not in scene_ids:
            errors.append(
                f"{i_ctx}: scene_id '{ref_scene}' not found in page scenes"
            )

        area = inst.get("area")
        if area is not None:
            area_errs = validate_area(area, i_ctx)
            errors.extend(area_errs)

    # --- Guides ---
    guides = page.get("guides", [])
    if not isinstance(guides, list):
        errors.append(f"{ctx}: guides must be list")
        guides = []
    for gi, guide in enumerate(guides):
        g_ctx = f"{ctx}.guides[{gi}]"
        if not isinstance(guide, dict):
            errors.append(f"{g_ctx}: must be dict")
            continue
        gid = guide.get("guide_id")
        if not isinstance(gid, str) or not gid:
            errors.append(f"{g_ctx}: guide_id must be non-empty string")
        elif gid in guide_ids:
            errors.append(f"{g_ctx}: duplicate guide_id '{gid}'")
        else:
            guide_ids.add(gid)

    return errors, warnings
