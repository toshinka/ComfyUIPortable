import json
import logging
from typing import Dict, Any, List, Optional, Set

"""
scene_spec.py — Manga Scene Data Contract (Phase 3A)
===================================================
PAGE ├ KOMA └ CHARACTER の3層構造を支えるデータ契約とバリデーション。
- REGION_SPEC (v1): コマ領域・幾何・Prompt・KOMA内Character Bindingの正本
- CAST_SPEC (v1): キャラクター恒久定義（Base Prompt, Baseline LoRA, メタデータ）
- COMPILE_PLAN (v1): CompilerがKOMA単位で出力する実行計画
- MANGA_SCENE_SPEC (v1): ページ全体の上位集約コンテナ
"""

SUPPORTED_CAST_SPEC_VERSION = 1
SUPPORTED_SCENE_SPEC_VERSION = 1
MIN_RECT_SIZE = 0.001


def normalize_rect(x: float, y: float, w: float, h: float, min_size: float = MIN_RECT_SIZE) -> Dict[str, float]:
    """
    0.0〜1.0 の正規化矩形座標を検証・クランプする汎用関数。
    Page Region (REGION_SPEC) と Character Local Area の双方で共通利用します。
    """
    x = float(x)
    y = float(y)
    w = float(w)
    h = float(h)

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
        "x": round(x, 4),
        "y": round(y, 4),
        "w": round(w, 4),
        "h": round(h, 4)
    }


def validate_lora_entry(entry: Any, context_name: str = "LoRA") -> Dict[str, Any]:
    """
    LoRA定義エントリを検証する。未知フィールドは保持。
    """
    if not isinstance(entry, dict):
        raise ValueError(f"[{context_name}] LoRA entry must be a dictionary, got {type(entry).__name__}")

    name = str(entry.get("name", "")).strip()
    if not name:
        raise ValueError(f"[{context_name}] LoRA entry must have a non-empty 'name'")

    try:
        weight = float(entry.get("weight", 1.0))
    except (ValueError, TypeError):
        raise ValueError(f"[{context_name}] LoRA '{name}' weight must be numeric, got {entry.get('weight')!r}")

    enabled = entry.get("enabled", True)
    if not isinstance(enabled, bool):
        raise ValueError(
            f"[{context_name}] LoRA '{name}' 'enabled' must be a strict boolean (True/False), "
            f"got {type(enabled).__name__} ({enabled!r})"
        )

    validated = dict(entry)
    validated["name"] = name
    validated["weight"] = round(weight, 4)
    validated["enabled"] = enabled
    return validated


def default_cast_spec() -> Dict[str, Any]:
    """
    空の初期 CAST_SPEC (v1) を生成する
    """
    return {
        "version": SUPPORTED_CAST_SPEC_VERSION,
        "characters": []
    }


def validate_cast_spec(spec: Any) -> Dict[str, Any]:
    """
    CAST_SPEC (v1) の構造を厳格に検証する。
    - version === 1
    - characters は list
    - character id は非空文字列かつ一意
    - enabled は strict boolean
    - prompt / negative_prompt は文字列
    - loras は list
    - 未知フィールドは保持
    """
    if not isinstance(spec, dict):
        raise ValueError("[CastSpecValidator] Root CAST_SPEC must be a dictionary.")

    version = spec.get("version")
    if version != SUPPORTED_CAST_SPEC_VERSION:
        raise ValueError(
            f"[CastSpecValidator] Unsupported CAST_SPEC version: {version}. "
            f"Expected version {SUPPORTED_CAST_SPEC_VERSION}."
        )

    characters = spec.get("characters")
    if not isinstance(characters, list):
        raise ValueError("[CastSpecValidator] 'characters' must be a list.")

    seen_ids: Set[str] = set()
    validated_characters = []

    for idx, c in enumerate(characters):
        if not isinstance(c, dict):
            raise ValueError(
                f"[CastSpecValidator] Invalid character entry at index {idx}: "
                f"must be a dictionary, got {type(c).__name__}"
            )

        cid = str(c.get("id", "")).strip()
        if not cid:
            raise ValueError(f"[CastSpecValidator] Character at index {idx} has missing or empty 'id'.")
        if cid in seen_ids:
            raise ValueError(f"[CastSpecValidator] Duplicate character id detected: '{cid}'. IDs must be unique.")
        seen_ids.add(cid)

        name = str(c.get("name", "")).strip() or cid

        enabled = c.get("enabled", True)
        if not isinstance(enabled, bool):
            raise ValueError(
                f"[CastSpecValidator] Character '{cid}': 'enabled' must be a strict boolean (True/False), "
                f"got {type(enabled).__name__} ({enabled!r})"
            )

        prompt = str(c.get("prompt", "") or "")
        negative_prompt = str(c.get("negative_prompt", "") or "")

        loras_raw = c.get("loras", [])
        if not isinstance(loras_raw, list):
            raise ValueError(f"[CastSpecValidator] Character '{cid}': 'loras' must be a list.")

        validated_loras = [validate_lora_entry(lora, f"Character '{cid}'") for lora in loras_raw]

        validated_c = dict(c)
        validated_c["id"] = cid
        validated_c["name"] = name
        validated_c["enabled"] = enabled
        validated_c["prompt"] = prompt
        validated_c["negative_prompt"] = negative_prompt
        validated_c["loras"] = validated_loras
        if "metadata" not in validated_c:
            validated_c["metadata"] = {}

        validated_characters.append(validated_c)

    validated_spec = dict(spec)
    validated_spec["characters"] = validated_characters
    return validated_spec


def validate_character_binding(binding: Any, available_character_ids: Optional[Set[str]] = None, context_name: str = "Binding") -> Dict[str, Any]:
    """
    KOMA内に保持される Character Binding を検証する。
    - character_id: 空でない文字列。available_character_ids が与えられた場合は存在確認。
    - enabled: 厳格な boolean
    - prompt_override: 文字列
    - area: None または KOMA-local 正規化矩形 (x, y, w, h)
    - 未知フィールドは保持
    """
    if not isinstance(binding, dict):
        raise ValueError(f"[{context_name}] Character binding must be a dictionary, got {type(binding).__name__}")

    cid = str(binding.get("character_id", "")).strip()
    if not cid:
        raise ValueError(f"[{context_name}] Missing or empty 'character_id' in binding.")

    if available_character_ids is not None and cid not in available_character_ids:
        raise ValueError(
            f"[{context_name}] Referenced character_id '{cid}' was not found in CAST_SPEC. "
            f"Available characters: {sorted(list(available_character_ids))}"
        )

    enabled = binding.get("enabled", True)
    if not isinstance(enabled, bool):
        raise ValueError(
            f"[{context_name}] Character '{cid}': 'enabled' must be a strict boolean (True/False), "
            f"got {type(enabled).__name__} ({enabled!r})"
        )

    prompt_override = str(binding.get("prompt_override", "") or "")

    area = binding.get("area")
    if area is not None:
        if not isinstance(area, dict):
            raise ValueError(f"[{context_name}] Character '{cid}': 'area' must be a dictionary or null, got {type(area).__name__}")
        try:
            norm_area = normalize_rect(area.get("x", 0.0), area.get("y", 0.0), area.get("w", 0.3), area.get("h", 0.6))
        except (ValueError, TypeError) as e:
            raise ValueError(f"[{context_name}] Character '{cid}': Invalid 'area' coordinates: {e}")
    else:
        norm_area = None

    lora_override_raw = binding.get("lora_override")
    if lora_override_raw is not None:
        if not isinstance(lora_override_raw, list):
            raise ValueError(f"[{context_name}] Character '{cid}': 'lora_override' must be a list or null.")
        lora_override = [validate_lora_entry(le, f"Character '{cid}' override") for le in lora_override_raw]
    else:
        lora_override = None

    validated = dict(binding)
    validated["character_id"] = cid
    validated["enabled"] = enabled
    validated["prompt_override"] = prompt_override
    validated["area"] = norm_area
    validated["lora_override"] = lora_override
    return validated


def default_manga_scene_spec(region_spec: Optional[Dict[str, Any]] = None, cast_spec: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    包括的な MANGA_SCENE_SPEC (v1) の初期構造を生成する
    """
    from .region_editor import default_region_spec
    return {
        "version": SUPPORTED_SCENE_SPEC_VERSION,
        "region_spec": region_spec if region_spec is not None else default_region_spec(),
        "cast_spec": cast_spec if cast_spec is not None else default_cast_spec(),
        "generation": {
            "global_loras": [],
            "sampler": "euler_ancestral",
            "steps": 28,
            "cfg": 6.0,
            "seed": None
        },
        "metadata": {}
    }


def validate_manga_scene_spec(spec: Any) -> Dict[str, Any]:
    """
    MANGA_SCENE_SPEC (v1) の総合バリデーション
    """
    from .region_editor import validate_region_spec

    if not isinstance(spec, dict):
        raise ValueError("[MangaSceneSpecValidator] Root must be a dictionary.")

    version = spec.get("version")
    if version != SUPPORTED_SCENE_SPEC_VERSION:
        raise ValueError(
            f"[MangaSceneSpecValidator] Unsupported MANGA_SCENE_SPEC version: {version}. "
            f"Expected {SUPPORTED_SCENE_SPEC_VERSION}."
        )

    region_spec = validate_region_spec(spec.get("region_spec", {}))
    cast_spec = validate_cast_spec(spec.get("cast_spec", default_cast_spec()))

    # KOMA内の Character Binding を CAST_SPEC と照合
    available_cids = {c["id"] for c in cast_spec["characters"]}
    for r in region_spec.get("regions", []):
        bindings = r.get("characters", [])
        if bindings:
            if not isinstance(bindings, list):
                raise ValueError(f"[MangaSceneSpecValidator] KOMA {r.get('id')} 'characters' must be a list.")
            validated_bindings = []
            for b_idx, b in enumerate(bindings):
                v_b = validate_character_binding(b, available_cids, f"KOMA {r.get('id')} binding[{b_idx}]")
                validated_bindings.append(v_b)
            r["characters"] = validated_bindings

    generation = spec.get("generation", {})
    if not isinstance(generation, dict):
        raise ValueError("[MangaSceneSpecValidator] 'generation' must be a dictionary.")

    validated = dict(spec)
    validated["region_spec"] = region_spec
    validated["cast_spec"] = cast_spec
    validated["generation"] = generation
    return validated
