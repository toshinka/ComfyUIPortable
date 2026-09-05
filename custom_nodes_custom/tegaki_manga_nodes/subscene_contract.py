"""
Tegaki Manga SubScene Contract v1.1 (Phase 3L)
==============================================
Formalizes the mainline non-hierarchical SubScene contract for multi-scene panels.

Design Principles (Aligned with Tegaki Intermediate Architecture):
- Simple First: Simple panels have 1 Root Scene (panel polygon). Subscenes are absent or empty.
- Progressive Disclosure: Complex panels specify `subscenes: list[dict]`.
- Non-hierarchical: Exactly 1 level of subscenes per panel (nested subscenes strictly rejected).
- SubScene Entry Specification:
  - id: str (e.g. "sub_a", unique within panel)
  - enabled: bool (strict boolean, default True)
  - prompt: str (scene background prompt)
  - negative_prompt: str (scene negative prompt)
  - area: dict with {x, y, w, h} (normalized [0..1] relative to panel bounds or canvas)
  - character_bindings: list[dict] (characters bound to this subscene)
    - instance_id: str (stable instance ID, e.g. "p1_sub_a_alice_01", unique within panel)
    - character_id: str (references CAST master)
    - enabled: bool (strict boolean, default True)
    - prompt_override: str
    - negative_prompt_override: str
    - area: dict with {x, y, w, h}
    - shot_type: str ("full_body", "half_body", "bust")
    - pose_preset: str ("standing_neutral", "facing_left", "facing_right", "sitting")
    - interaction: dict (canonical interaction dict)
    - metadata: dict
  - metadata: dict
"""

import math
from typing import Dict, Any, List, Optional, Tuple, Set
from .interaction_resolver import normalize_interaction, generate_stable_instance_id

SUPPORTED_SUBSCENE_VERSION = "1.1"

VALID_SHOT_TYPES: Set[str] = {"full_body", "half_body", "bust"}
VALID_POSE_PRESETS: Set[str] = {"standing_neutral", "facing_left", "facing_right", "sitting"}


def validate_subscene_area(area: Any, context: str = "SubScene") -> Dict[str, float]:
    """Validates and clamps a normalized bounding rectangle for a subscene or character."""
    if not isinstance(area, dict):
        raise ValueError(f"[{context}] 'area' must be a dictionary, got {type(area).__name__}")
    
    for key in ("x", "y", "w", "h"):
        if key not in area:
            raise ValueError(f"[{context}] 'area' missing required coordinate key '{key}'")
        val = area[key]
        if not isinstance(val, (int, float)) or isinstance(val, bool):
            raise ValueError(f"[{context}] 'area.{key}' must be numeric, got {val!r}")
        if math.isnan(val) or math.isinf(val):
            raise ValueError(f"[{context}] 'area.{key}' must be a finite number, got {val!r}")
            
    x = max(0.0, min(1.0, float(area["x"])))
    y = max(0.0, min(1.0, float(area["y"])))
    w = max(0.001, min(1.0 - x, float(area["w"])))
    h = max(0.001, min(1.0 - y, float(area["h"])))
    
    return {"x": round(x, 4), "y": round(y, 4), "w": round(w, 4), "h": round(h, 4)}


def validate_subscene_entry(
    entry: Any,
    panel_id: Optional[Any] = None,
    context: str = "SubScene"
) -> Dict[str, Any]:
    """Validates a single SubScene entry against SubScene v1.1 specification."""
    if not isinstance(entry, dict):
        raise ValueError(f"[{context}] SubScene entry must be a dictionary, got {type(entry).__name__}")
        
    # Strictly reject nested subscenes
    if "subscenes" in entry and entry["subscenes"]:
        raise ValueError(f"[{context}] Nested subscenes are strictly prohibited in SubScene v1.1.")
        
    raw_id = entry.get("id")
    if not isinstance(raw_id, str) or not raw_id.strip():
        raise ValueError(f"[{context}] SubScene missing required non-empty string 'id'")
    sub_id = raw_id.strip()

    raw_enabled = entry.get("enabled", True)
    if not isinstance(raw_enabled, bool):
        raise ValueError(f"[{context}.{sub_id}] 'enabled' must be a strict boolean, got {type(raw_enabled).__name__}")
    enabled = raw_enabled

    prompt = str(entry.get("prompt", "") or "")
    neg_prompt = str(entry.get("negative_prompt", "") or "")
    
    raw_area = entry.get("area", {"x": 0.0, "y": 0.0, "w": 1.0, "h": 1.0})
    area = validate_subscene_area(raw_area, context=f"{context}.{sub_id}")
    
    char_bindings = entry.get("character_bindings")
    if char_bindings is None:
        char_bindings = entry.get("characters", [])
    if not isinstance(char_bindings, list):
        raise ValueError(f"[{context}.{sub_id}] 'character_bindings' must be a list")
        
    validated_bindings = []
    seen_binding_instances: Set[str] = set()

    for b_idx, b in enumerate(char_bindings):
        if not isinstance(b, dict):
            raise ValueError(f"[{context}.{sub_id}] Binding [{b_idx}] must be a dictionary")
        raw_cid = b.get("character_id")
        if not isinstance(raw_cid, str) or not raw_cid.strip():
            raise ValueError(f"[{context}.{sub_id}] Binding [{b_idx}] missing required 'character_id'")
        cid = raw_cid.strip()

        # Instance ID (stable & unique)
        raw_iid = b.get("instance_id") or b.get("character_instance_id")
        if raw_iid and isinstance(raw_iid, str) and raw_iid.strip():
            instance_id = raw_iid.strip()
        else:
            instance_id = generate_stable_instance_id(
                panel_id=panel_id if panel_id is not None else "1",
                char_id=cid,
                subscene_id=sub_id,
                index=b_idx + 1
            )

        if instance_id in seen_binding_instances:
            raise ValueError(f"[{context}.{sub_id}] Duplicate instance_id '{instance_id}' within subscene")
        seen_binding_instances.add(instance_id)

        # Enabled check
        b_enabled = b.get("enabled", True)
        if not isinstance(b_enabled, bool):
            raise ValueError(f"[{context}.{sub_id}.{instance_id}] 'enabled' must be a strict boolean")

        # Area validation
        b_area = None
        if "area" in b and b["area"] is not None:
            b_area = validate_subscene_area(b["area"], context=f"{context}.{sub_id}.{instance_id}")

        # Shot Type validation
        raw_shot = b.get("shot_type") or b.get("shot")
        if raw_shot is not None:
            if not isinstance(raw_shot, str) or raw_shot not in VALID_SHOT_TYPES:
                raise ValueError(
                    f"[{context}.{sub_id}.{instance_id}] Invalid shot_type '{raw_shot}'. Must be one of {sorted(list(VALID_SHOT_TYPES))}"
                )
            shot_type = raw_shot
        else:
            shot_type = None

        # Pose Preset validation
        raw_pose = b.get("pose_preset")
        if raw_pose is not None:
            if not isinstance(raw_pose, str) or raw_pose not in VALID_POSE_PRESETS:
                raise ValueError(
                    f"[{context}.{sub_id}.{instance_id}] Invalid pose_preset '{raw_pose}'. Must be one of {sorted(list(VALID_POSE_PRESETS))}"
                )
            pose_preset = raw_pose
        else:
            pose_preset = None

        # Canonical Interaction validation
        raw_inter = b.get("interaction")
        interaction = normalize_interaction(
            raw_inter,
            source_instance_id=instance_id,
            context=f"{context}.{sub_id}.{instance_id}"
        )

        b_meta = b.get("metadata", {})
        if not isinstance(b_meta, dict):
            raise ValueError(f"[{context}.{sub_id}.{instance_id}] 'metadata' must be a dictionary")
        metadata = dict(b_meta)
        if shot_type:
            metadata["shot_type"] = shot_type
        if pose_preset:
            metadata["pose_preset"] = pose_preset
        if interaction:
            metadata["interaction"] = interaction
        metadata["instance_id"] = instance_id

        binding_out = {
            "instance_id": instance_id,
            "character_id": cid,
            "enabled": b_enabled,
            "prompt_override": str(b.get("prompt_override", "") or ""),
            "negative_prompt_override": str(b.get("negative_prompt_override", "") or ""),
            "area": b_area,
            "shot_type": shot_type,
            "pose_preset": pose_preset,
            "interaction": interaction,
            "metadata": metadata
        }
        for extra_key in ("name", "base_prompt", "override_prompt", "combined_prompt", "base_negative_prompt", "override_negative_prompt", "combined_negative_prompt", "loras"):
            if extra_key in b:
                binding_out[extra_key] = b[extra_key]
        validated_bindings.append(binding_out)
        
    metadata = entry.get("metadata", {})
    if not isinstance(metadata, dict):
        raise ValueError(f"[{context}.{sub_id}] 'metadata' must be a dictionary")
        
    return {
        "id": sub_id,
        "enabled": enabled,
        "prompt": prompt,
        "negative_prompt": neg_prompt,
        "area": area,
        "character_bindings": validated_bindings,
        "characters": validated_bindings,
        "metadata": dict(metadata)
    }


def validate_panel_subscenes(
    panel_dict: Dict[str, Any],
    panel_id: Optional[Any] = None,
    context: str = "Panel"
) -> List[Dict[str, Any]]:
    """
    Validates the optional `subscenes` field in a panel dictionary.
    Returns empty list if no subscenes or subscenes are not active.
    Supports both root `panel_dict['subscenes']` and nested `panel_dict['panel']['subscenes']`.
    Enforces cross-subscene unique instance_id constraints.
    """
    if not isinstance(panel_dict, dict):
        return []
        
    pid = panel_id if panel_id is not None else panel_dict.get("koma_id", panel_dict.get("panel_id", 1))

    subscenes = panel_dict.get("subscenes")
    if not subscenes and "panel" in panel_dict and isinstance(panel_dict["panel"], dict):
        subscenes = panel_dict["panel"].get("subscenes")

    if not subscenes:
        return []
        
    if not isinstance(subscenes, list):
        raise ValueError(f"[{context}] 'subscenes' must be a list if present, got {type(subscenes).__name__}")
        
    validated: List[Dict[str, Any]] = []
    seen_subscene_ids: Set[str] = set()
    seen_panel_instance_ids: Set[str] = set()

    for s_idx, s in enumerate(subscenes):
        v = validate_subscene_entry(s, panel_id=pid, context=f"{context}.subscene[{s_idx}]")
        if v["id"] in seen_subscene_ids:
            raise ValueError(f"[{context}] Duplicate subscene id '{v['id']}' detected")
        seen_subscene_ids.add(v["id"])

        for cb in v["character_bindings"]:
            inst_id = cb["instance_id"]
            if inst_id in seen_panel_instance_ids:
                raise ValueError(
                    f"[{context}] Duplicate instance_id '{inst_id}' detected across subscenes in panel {pid}"
                )
            seen_panel_instance_ids.add(inst_id)

        validated.append(v)
        
    return validated


def has_active_subscenes(panel_dict: Dict[str, Any]) -> bool:
    """Checks if a panel contains one or more enabled subscenes."""
    if not isinstance(panel_dict, dict):
        return False
    subscenes = panel_dict.get("subscenes")
    if not subscenes and "panel" in panel_dict and isinstance(panel_dict["panel"], dict):
        subscenes = panel_dict["panel"].get("subscenes")
    if not isinstance(subscenes, list) or not subscenes:
        return False
    return any(isinstance(s, dict) and s.get("enabled", True) for s in subscenes)
