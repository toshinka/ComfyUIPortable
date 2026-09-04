"""
Tegaki Manga SubScene v1 Contract (Phase 3F)
===========================================
Formalizes the minimal non-hierarchical SubScene contract for multi-scene panels.

Design Principles:
- Simple by default: Simple panels have 1 Root Scene (panel polygon). Subscenes are absent or empty.
- Complex only when requested: Panels can optionally specify `subscenes: list[dict]`.
- Non-hierarchical: Exactly 1 level of subscenes per panel.
- SubScene Entry Specification:
  - id: str (e.g. "sub_scene_a", unique within panel)
  - enabled: bool (default True)
  - prompt: str (scene background prompt)
  - negative_prompt: str (scene negative prompt)
  - area: dict with {x, y, w, h} (normalized [0..1] relative to panel bounds or canvas)
  - character_bindings: list[dict] (characters bound to this subscene)
  - metadata: dict (arbitrary extension properties)
"""

import logging
from typing import Dict, Any, List, Optional, Tuple


SUPPORTED_SUBSCENE_VERSION = 1


def validate_subscene_area(area: Any, context: str = "SubScene") -> Dict[str, float]:
    """Validates and clamps a normalized bounding rectangle for a subscene."""
    if not isinstance(area, dict):
        raise ValueError(f"[{context}] 'area' must be a dictionary, got {type(area).__name__}")
    
    for key in ("x", "y", "w", "h"):
        if key not in area:
            raise ValueError(f"[{context}] 'area' missing required coordinate key '{key}'")
        try:
            area[key] = float(area[key])
        except (ValueError, TypeError):
            raise ValueError(f"[{context}] 'area.{key}' must be numeric, got {area[key]!r}")
            
    x = max(0.0, min(1.0, area["x"]))
    y = max(0.0, min(1.0, area["y"]))
    w = max(0.001, min(1.0 - x, area["w"]))
    h = max(0.001, min(1.0 - y, area["h"]))
    
    return {"x": round(x, 4), "y": round(y, 4), "w": round(w, 4), "h": round(h, 4)}


def validate_subscene_entry(entry: Any, context: str = "SubScene") -> Dict[str, Any]:
    """Validates a single SubScene entry against SubScene v1 specification."""
    if not isinstance(entry, dict):
        raise ValueError(f"[{context}] SubScene entry must be a dictionary, got {type(entry).__name__}")
        
    sub_id = str(entry.get("id", "")).strip()
    if not sub_id:
        raise ValueError(f"[{context}] SubScene missing required non-empty 'id'")
        
    enabled = bool(entry.get("enabled", True))
    prompt = str(entry.get("prompt", ""))
    neg_prompt = str(entry.get("negative_prompt", ""))
    
    raw_area = entry.get("area", {"x": 0.0, "y": 0.0, "w": 1.0, "h": 1.0})
    area = validate_subscene_area(raw_area, context=f"{context}.{sub_id}")
    
    char_bindings = entry.get("character_bindings", [])
    if not isinstance(char_bindings, list):
        raise ValueError(f"[{context}.{sub_id}] 'character_bindings' must be a list")
        
    validated_bindings = []
    for b_idx, b in enumerate(char_bindings):
        if not isinstance(b, dict):
            raise ValueError(f"[{context}.{sub_id}] Binding [{b_idx}] must be a dictionary")
        cid = str(b.get("character_id", "")).strip()
        if not cid:
            raise ValueError(f"[{context}.{sub_id}] Binding [{b_idx}] missing 'character_id'")
        
        b_area = None
        if "area" in b and b["area"] is not None:
            b_area = validate_subscene_area(b["area"], context=f"{context}.{sub_id}.char_{cid}")
            
        validated_bindings.append({
            "character_id": cid,
            "enabled": bool(b.get("enabled", True)),
            "prompt_override": str(b.get("prompt_override", "")),
            "negative_prompt_override": str(b.get("negative_prompt_override", "")),
            "area": b_area,
            "metadata": b.get("metadata", {}) if isinstance(b.get("metadata"), dict) else {}
        })
        
    metadata = entry.get("metadata", {})
    if not isinstance(metadata, dict):
        metadata = {}
        
    return {
        "id": sub_id,
        "enabled": enabled,
        "prompt": prompt,
        "negative_prompt": neg_prompt,
        "area": area,
        "character_bindings": validated_bindings,
        "metadata": metadata
    }


def validate_panel_subscenes(panel_dict: Dict[str, Any], context: str = "Panel") -> List[Dict[str, Any]]:
    """
    Validates the optional `subscenes` field in a panel dictionary.
    Returns empty list if no subscenes or subscenes are not active.
    Supports both root `panel_dict['subscenes']` and nested `panel_dict['panel']['subscenes']`.
    """
    if not isinstance(panel_dict, dict):
        return []
        
    subscenes = panel_dict.get("subscenes")
    if not subscenes and "panel" in panel_dict and isinstance(panel_dict["panel"], dict):
        subscenes = panel_dict["panel"].get("subscenes")

    if not subscenes:
        return []
        
    if not isinstance(subscenes, list):
        raise ValueError(f"[{context}] 'subscenes' must be a list if present")
        
    validated = []
    seen_ids = set()
    for s_idx, s in enumerate(subscenes):
        v = validate_subscene_entry(s, context=f"{context}.subscene[{s_idx}]")
        if v["id"] in seen_ids:
            raise ValueError(f"[{context}] Duplicate subscene id '{v['id']}' detected")
        seen_ids.add(v["id"])
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
