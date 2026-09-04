"""
Tegaki Manga Cast Master (Phase 3D.1)
=====================================
Centralized character management (CAST_SPEC v1) node and state machine.
Provides immutable ID preservation, base prompt/negative management,
character enable/disable toggles, referenced binding deletion protection,
and derived appearance queries.
"""

import json
import logging
import re
from typing import Dict, Any, List, Optional, Set, Tuple

from .scene_spec import (
    validate_cast_spec,
    validate_lora_entry,
    SUPPORTED_CAST_SPEC_VERSION
)
from .region_editor import validate_region_spec, is_active_region


DEFAULT_INITIAL_CAST: Dict[str, Any] = {
    "version": SUPPORTED_CAST_SPEC_VERSION,
    "characters": [
        {
            "id": "char_alice",
            "name": "Alice",
            "enabled": True,
            "prompt": "1girl, blonde twin tails, blue eyes, school uniform",
            "negative_prompt": "blurry, low quality",
            "loras": []
        },
        {
            "id": "char_bob",
            "name": "Bob",
            "enabled": True,
            "prompt": "1boy, short brown hair, school uniform",
            "negative_prompt": "bad anatomy",
            "loras": []
        }
    ]
}


def get_default_cast_spec() -> Dict[str, Any]:
    """Returns a deep copy of the default initial CAST_SPEC."""
    return json.loads(json.dumps(DEFAULT_INITIAL_CAST))


def generate_unique_character_id(existing_ids: Set[str], prefix: str = "char") -> str:
    """Generates a stable, unique character ID."""
    clean_prefix = re.sub(r"[^a-zA-Z0-9_]", "_", prefix).lower().strip("_")
    if not clean_prefix:
        clean_prefix = "char"

    counter = 1
    candidate = f"{clean_prefix}_{counter:03d}"
    while candidate in existing_ids:
        counter += 1
        candidate = f"{clean_prefix}_{counter:03d}"
    return candidate


def add_character(
    spec: Dict[str, Any],
    name: str = "New Character",
    char_id: Optional[str] = None,
    prompt: str = "",
    negative_prompt: str = "",
    loras: Optional[List[Dict[str, Any]]] = None,
    enabled: bool = True
) -> Tuple[Dict[str, Any], str]:
    """
    Adds a new character to CAST_SPEC with unique stable ID.
    Returns (updated_spec, created_char_id).
    """
    valid_spec = validate_cast_spec(spec)
    chars = list(valid_spec.get("characters", []))
    existing_ids = {c["id"] for c in chars}

    if char_id:
        if char_id in existing_ids:
            raise ValueError(f"[CastMaster] Duplicate character ID detected: '{char_id}'")
        final_id = char_id
    else:
        name_prefix = name.lower().replace(" ", "_")
        final_id = generate_unique_character_id(existing_ids, prefix=f"char_{name_prefix}")

    validated_loras = []
    if loras:
        validated_loras = [validate_lora_entry(l, f"Character '{final_id}'") for l in loras]

    new_char = {
        "id": final_id,
        "name": name if name else final_id,
        "enabled": bool(enabled),
        "prompt": prompt,
        "negative_prompt": negative_prompt,
        "loras": validated_loras,
        "metadata": {}
    }
    chars.append(new_char)

    updated = dict(valid_spec)
    updated["characters"] = chars
    return (validate_cast_spec(updated), final_id)


def update_character(
    spec: Dict[str, Any],
    char_id: str,
    name: Optional[str] = None,
    prompt: Optional[str] = None,
    negative_prompt: Optional[str] = None,
    loras: Optional[List[Dict[str, Any]]] = None,
    enabled: Optional[bool] = None
) -> Dict[str, Any]:
    """
    Updates character attributes while strictly preserving immutable char_id.
    """
    valid_spec = validate_cast_spec(spec)
    chars = list(valid_spec.get("characters", []))

    found = False
    new_chars = []
    for c in chars:
        if c["id"] == char_id:
            found = True
            c_copy = dict(c)
            if name is not None:
                c_copy["name"] = name
            if prompt is not None:
                c_copy["prompt"] = prompt
            if negative_prompt is not None:
                c_copy["negative_prompt"] = negative_prompt
            if enabled is not None:
                c_copy["enabled"] = bool(enabled)
            if loras is not None:
                c_copy["loras"] = [validate_lora_entry(l, f"Character '{char_id}'") for l in loras]
            new_chars.append(c_copy)
        else:
            new_chars.append(c)

    if not found:
        raise ValueError(f"[CastMaster] Character ID '{char_id}' not found in CAST_SPEC.")

    updated = dict(valid_spec)
    updated["characters"] = new_chars
    return validate_cast_spec(updated)


def get_referenced_character_ids(region_spec: Any) -> Set[str]:
    """
    Collects all character_ids referenced in any active KOMA bindings.
    """
    if not region_spec:
        return set()
    try:
        r_spec = validate_region_spec(region_spec)
    except Exception:
        return set()

    panel_count = r_spec.get("panel_count", len(r_spec.get("regions", [])))
    referenced = set()
    for r in r_spec.get("regions", []):
        if is_active_region(r, panel_count):
            for b in r.get("characters", []):
                cid = b.get("character_id")
                if cid:
                    referenced.add(cid)
    return referenced


def get_character_appearances(spec: Dict[str, Any], region_spec: Any) -> Dict[str, List[int]]:
    """
    Calculates the derived appearance list (KOMA IDs) for each character in CAST_SPEC.
    """
    valid_spec = validate_cast_spec(spec)
    appearances = {c["id"]: [] for c in valid_spec.get("characters", [])}

    if not region_spec:
        return appearances

    try:
        r_spec = validate_region_spec(region_spec)
    except Exception:
        return appearances

    panel_count = r_spec.get("panel_count", len(r_spec.get("regions", [])))
    for r in r_spec.get("regions", []):
        if is_active_region(r, panel_count):
            koma_id = r.get("id")
            for b in r.get("characters", []):
                cid = b.get("character_id")
                if cid in appearances and koma_id not in appearances[cid]:
                    appearances[cid].append(koma_id)

    return appearances


def delete_character(
    spec: Dict[str, Any],
    char_id: str,
    region_spec: Optional[Any] = None
) -> Dict[str, Any]:
    """
    Deletes a character from CAST_SPEC.
    Fails closed if the character is currently referenced in active KOMA bindings!
    """
    valid_spec = validate_cast_spec(spec)

    if region_spec:
        referenced_ids = get_referenced_character_ids(region_spec)
        if char_id in referenced_ids:
            raise ValueError(
                f"[CastMaster] Cannot delete character '{char_id}': "
                f"referenced in active KOMA bindings. Remove binding references first."
            )

    chars = valid_spec.get("characters", [])
    new_chars = [c for c in chars if c["id"] != char_id]

    if len(new_chars) == len(chars):
        raise ValueError(f"[CastMaster] Character ID '{char_id}' not found in CAST_SPEC.")

    updated = dict(valid_spec)
    updated["characters"] = new_chars
    return validate_cast_spec(updated)


class TegakiMangaCastMaster:
    """
    Tegaki Manga Cast Master (Phase 3D.1)
    ====================================
    Provides centralized character management for multi-panel manga pages.
    """
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "cast_spec_data": ("STRING", {
                    "multiline": True,
                    "default": json.dumps(DEFAULT_INITIAL_CAST, indent=2, ensure_ascii=False)
                }),
            },
            "optional": {
                "region_spec": ("REGION_SPEC",),
            }
        }

    RETURN_TYPES = ("CAST_SPEC", "STRING", "STRING", "INT")
    RETURN_NAMES = ("cast_spec", "cast_spec_json", "selected_character_id", "character_count")
    FUNCTION = "process"
    CATEGORY = "tegaki/manga"

    def process(self, cast_spec_data: str, region_spec: Optional[Any] = None):
        trimmed = cast_spec_data.strip() if cast_spec_data else ""
        if not trimmed or trimmed == "{}":
            spec = get_default_cast_spec()
        else:
            try:
                parsed = json.loads(trimmed)
                spec = validate_cast_spec(parsed)
            except json.JSONDecodeError as e:
                raise ValueError(f"[TegakiMangaCastMaster] Invalid JSON in cast_spec_data: {e}")
            except ValueError as e:
                raise ValueError(f"[TegakiMangaCastMaster] CAST_SPEC schema error: {e}")

        # Optional reference check if region_spec provided
        if region_spec:
            _ = get_character_appearances(spec, region_spec)

        characters = spec.get("characters", [])
        char_count = len(characters)
        first_id = characters[0]["id"] if characters else ""

        spec_json = json.dumps(spec, indent=2, ensure_ascii=False)
        return (spec, spec_json, first_id, char_count)
