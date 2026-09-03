import json
import re
import logging
from typing import Dict, Any, List, Optional, Set, Tuple

"""
scene_spec.py — Manga Scene Data Contract (Phase 3A.1 Hardened)
=============================================================
PAGE ├ KOMA └ CHARACTER の3層構造を支えるデータ契約・バリデーション・LoRA Canonicalization。
- REGION_SPEC (v1): コマ領域・幾何・Prompt・KOMA内Character Bindingの正本
- CAST_SPEC (v1): キャラクター恒久定義（Base Prompt, Baseline LoRA, メタデータ）
- COMPILE_PLAN (v1): CompilerがKOMA単位で出力する実行計画
- MANGA_SCENE_SPEC (v1): ページ全体の上位集約コンテナ
"""

SUPPORTED_CAST_SPEC_VERSION = 1
SUPPORTED_SCENE_SPEC_VERSION = 1
SUPPORTED_COMPILE_PLAN_VERSION = 1
MIN_RECT_SIZE = 0.001

# <lora:name:weight:clip_weight> タグ検出用正規表現
LORA_TAG_FULL_REGEX = re.compile(r"<lora:([^>]+)>", re.IGNORECASE)


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


def _check_strict_numeric(val: Any, name: str, context_name: str = "LoRA") -> float:
    """
    Pythonの bool (True == 1) を排除し、厳格な int/float のみを許可する
    """
    if isinstance(val, bool) or not isinstance(val, (int, float)):
        raise ValueError(
            f"[{context_name}] '{name}' must be a strict numeric (int or float, not bool), "
            f"got {type(val).__name__} ({val!r})"
        )
    return float(val)


def _validate_strict_string(val: Any, field_name: str, context_name: str, allow_empty: bool = True, default_if_missing: str = "") -> str:
    """
    厳格な文字列検証。missing/Noneは default_if_missing を返し、数値・bool・dict等は即時 ValueError
    """
    if val is None:
        return default_if_missing
    if not isinstance(val, str):
        raise ValueError(
            f"[{context_name}] '{field_name}' must be a string, got {type(val).__name__} ({val!r})"
        )
    s = val.strip()
    if not allow_empty and not s:
        raise ValueError(f"[{context_name}] '{field_name}' must be a non-empty string.")
    return val


def validate_lora_entry(entry: Any, context_name: str = "LoRA") -> Dict[str, Any]:
    """
    LoRA定義エントリを検証し、Canonical LoRA Entry に正規化する。
    Canonical形式:
      {
        "name": str,
        "enabled": bool,
        "model_weight": float,
        "clip_weight": float,
        "metadata": dict
      }
    - legacy 'weight' のみ指定時: model_weight = clip_weight = weight
    - 2値指定時: model_weight, clip_weight を個別保持
    - 'weight' と 'model_weight'/'clip_weight' の値が矛盾して同時指定された場合は ValueError
    - bool weight は厳格排除
    - 未知フィールドは保持
    """
    if not isinstance(entry, dict):
        raise ValueError(f"[{context_name}] LoRA entry must be a dictionary, got {type(entry).__name__}")

    raw_name = entry.get("name")
    name = _validate_strict_string(raw_name, "name", context_name, allow_empty=False).strip()

    enabled = entry.get("enabled", True)
    if not isinstance(enabled, bool):
        raise ValueError(
            f"[{context_name}] LoRA '{name}' 'enabled' must be a strict boolean (True/False), "
            f"got {type(enabled).__name__} ({enabled!r})"
        )

    # 重みフィールドの取得と型検証
    weight_val = entry.get("weight")
    model_w_val = entry.get("model_weight")
    clip_w_val = entry.get("clip_weight")

    weight = _check_strict_numeric(weight_val, "weight", context_name) if weight_val is not None else None
    model_weight = _check_strict_numeric(model_w_val, "model_weight", context_name) if model_w_val is not None else None
    clip_weight = _check_strict_numeric(clip_w_val, "clip_weight", context_name) if clip_w_val is not None else None

    # 矛盾する値の同時指定チェック (指示書第9項)
    if weight is not None and model_weight is not None and round(weight, 4) != round(model_weight, 4):
        raise ValueError(
            f"[{context_name}] LoRA '{name}' conflicting weight definitions: "
            f"legacy 'weight'={weight} vs 'model_weight'={model_weight}"
        )
    if weight is not None and clip_weight is not None and round(weight, 4) != round(clip_weight, 4):
        raise ValueError(
            f"[{context_name}] LoRA '{name}' conflicting weight definitions: "
            f"legacy 'weight'={weight} vs 'clip_weight'={clip_weight}"
        )

    # Canonical 値の決定
    final_model_w = model_weight if model_weight is not None else (weight if weight is not None else 1.0)
    final_clip_w = clip_weight if clip_weight is not None else (weight if weight is not None else 1.0)

    # metadata の検証
    raw_metadata = entry.get("metadata", {})
    if raw_metadata is not None and not isinstance(raw_metadata, dict):
        raise ValueError(f"[{context_name}] LoRA '{name}' 'metadata' must be a dictionary, got {type(raw_metadata).__name__}")
    metadata = dict(raw_metadata) if isinstance(raw_metadata, dict) else {}

    validated = dict(entry)
    validated["name"] = name
    validated["enabled"] = enabled
    validated["model_weight"] = round(final_model_w, 4)
    validated["clip_weight"] = round(final_clip_w, 4)
    validated["metadata"] = metadata
    return validated


def parse_lora_tags(prompt_text: str, source_context: str = "prompt_tag") -> Tuple[str, List[Dict[str, Any]]]:
    """
    Prompt文字列から <lora:...> タグを抽出し、Clean Prompt と Canonical LoRA Entry のリストを返す。
    - 1値タグ: <lora:Alice:0.8> -> model_weight=0.8, clip_weight=0.8
    - 2値タグ: <lora:Alice:0.8:0.5> -> model_weight=0.8, clip_weight=0.5
    - 不正タグ: <lora::0.8>, <lora:Alice:abc>, <lora:Alice:0.8:abc> は ValueError を送出！
    """
    if not prompt_text or not isinstance(prompt_text, str):
        return ("", [])

    lora_entries = []

    def _replace_tag(match):
        inner = match.group(1).strip()
        parts = [p.strip() for p in inner.split(":")]
        if not parts or not parts[0]:
            raise ValueError(f"[{source_context}] Invalid LoRA tag '{match.group(0)}': missing LoRA name.")

        lora_name = parts[0]
        model_w = 1.0
        clip_w = 1.0

        if len(parts) >= 2:
            try:
                model_w = float(parts[1])
            except ValueError:
                raise ValueError(f"[{source_context}] Invalid LoRA tag '{match.group(0)}': model weight '{parts[1]}' must be numeric.")
            clip_w = model_w  # 1値指定時は clip_weight も同値

        if len(parts) >= 3:
            try:
                clip_w = float(parts[2])
            except ValueError:
                raise ValueError(f"[{source_context}] Invalid LoRA tag '{match.group(0)}': clip weight '{parts[2]}' must be numeric.")

        if len(parts) > 3:
            raise ValueError(f"[{source_context}] Invalid LoRA tag '{match.group(0)}': too many arguments (expected name[:model_weight[:clip_weight]]).")

        canonical_entry = {
            "name": lora_name,
            "enabled": True,
            "model_weight": round(model_w, 4),
            "clip_weight": round(clip_w, 4),
            "source": source_context,
            "metadata": {}
        }
        lora_entries.append(canonical_entry)
        return ""  # プロンプトからタグを除去

    clean = LORA_TAG_FULL_REGEX.sub(_replace_tag, prompt_text)
    # 連続カンマや余分な空白を整理
    clean = re.sub(r",\s*,+", ",", clean)
    clean = re.sub(r"\s+", " ", clean).strip(", ").strip()

    return (clean, lora_entries)


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
    - characters は list (非listは即 ValueError)
    - character id は strict string かつ一意
    - prompt / negative_prompt は strict string
    - loras は list of Canonical LoRA Entry
    - metadata は dict
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
        raise ValueError(f"[CastSpecValidator] 'characters' must be a list, got {type(characters).__name__}")

    seen_ids: Set[str] = set()
    validated_characters = []

    for idx, c in enumerate(characters):
        if not isinstance(c, dict):
            raise ValueError(
                f"[CastSpecValidator] Invalid character entry at index {idx}: "
                f"must be a dictionary, got {type(c).__name__}"
            )

        cid = _validate_strict_string(c.get("id"), "id", f"Character[{idx}]", allow_empty=False)
        if cid in seen_ids:
            raise ValueError(f"[CastSpecValidator] Duplicate character id detected: '{cid}'. IDs must be unique.")
        seen_ids.add(cid)

        raw_name = c.get("name")
        name = _validate_strict_string(raw_name, "name", f"Character '{cid}'", allow_empty=True, default_if_missing=cid)
        if not name:
            name = cid

        enabled = c.get("enabled", True)
        if not isinstance(enabled, bool):
            raise ValueError(
                f"[CastSpecValidator] Character '{cid}': 'enabled' must be a strict boolean (True/False), "
                f"got {type(enabled).__name__} ({enabled!r})"
            )

        prompt = _validate_strict_string(c.get("prompt"), "prompt", f"Character '{cid}'")
        negative_prompt = _validate_strict_string(c.get("negative_prompt"), "negative_prompt", f"Character '{cid}'")

        loras_raw = c.get("loras", [])
        if not isinstance(loras_raw, list):
            raise ValueError(f"[CastSpecValidator] Character '{cid}': 'loras' must be a list, got {type(loras_raw).__name__}")

        validated_loras = [validate_lora_entry(lora, f"Character '{cid}'") for lora in loras_raw]

        raw_meta = c.get("metadata", {})
        if raw_meta is not None and not isinstance(raw_meta, dict):
            raise ValueError(f"[CastSpecValidator] Character '{cid}': 'metadata' must be a dictionary, got {type(raw_meta).__name__}")
        metadata = dict(raw_meta) if isinstance(raw_meta, dict) else {}

        validated_c = dict(c)
        validated_c["id"] = cid
        validated_c["name"] = name
        validated_c["enabled"] = enabled
        validated_c["prompt"] = prompt
        validated_c["negative_prompt"] = negative_prompt
        validated_c["loras"] = validated_loras
        validated_c["metadata"] = metadata

        validated_characters.append(validated_c)

    validated_spec = dict(spec)
    validated_spec["characters"] = validated_characters
    return validated_spec


def validate_character_binding(binding: Any, available_character_ids: Optional[Set[str]] = None, context_name: str = "Binding") -> Dict[str, Any]:
    """
    KOMA内に保持される Character Binding を検証する。
    - character_id: strict string。available_character_ids が与えられた場合は存在確認。
    - enabled: strict boolean
    - prompt_override: strict string
    - negative_prompt_override: strict string (Phase 3A.1 追加)
    - area: None または KOMA-local 正規化矩形 (x, y, w, h)
    - lora_override: None または list of Canonical LoRA Entry
    - metadata: dict
    """
    if not isinstance(binding, dict):
        raise ValueError(f"[{context_name}] Character binding must be a dictionary, got {type(binding).__name__}")

    cid = _validate_strict_string(binding.get("character_id"), "character_id", context_name, allow_empty=False)

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

    prompt_override = _validate_strict_string(binding.get("prompt_override"), "prompt_override", f"Character '{cid}' binding")
    neg_override = _validate_strict_string(binding.get("negative_prompt_override"), "negative_prompt_override", f"Character '{cid}' binding")

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
            raise ValueError(f"[{context_name}] Character '{cid}': 'lora_override' must be a list or null, got {type(lora_override_raw).__name__}")
        lora_override = [validate_lora_entry(le, f"Character '{cid}' override") for le in lora_override_raw]
    else:
        lora_override = None

    raw_meta = binding.get("metadata", {})
    if raw_meta is not None and not isinstance(raw_meta, dict):
        raise ValueError(f"[{context_name}] Character '{cid}': 'metadata' must be a dictionary, got {type(raw_meta).__name__}")
    metadata = dict(raw_meta) if isinstance(raw_meta, dict) else {}

    validated = dict(binding)
    validated["character_id"] = cid
    validated["enabled"] = enabled
    validated["prompt_override"] = prompt_override
    validated["negative_prompt_override"] = neg_override
    validated["area"] = norm_area
    validated["lora_override"] = lora_override
    validated["metadata"] = metadata
    return validated


def get_active_panel_ids(region_spec: dict) -> List[int]:
    """
    REGION_SPEC から現在アクティブなコマ番号のリストを返す。
    - panel_count: 表示/参照可能なコマ番号の上限（スロット範囲 1..6）
    - active_panel_ids: id <= panel_count かつ enabled == True のコマID
    """
    from .region_editor import is_active_region
    panel_count = int(region_spec.get("panel_count", 3))
    active_ids = []
    for r in region_spec.get("regions", []):
        if is_active_region(r, panel_count):
            active_ids.append(r["id"])
    return sorted(active_ids)


def validate_compile_plan(plan: Any) -> Dict[str, Any]:
    """
    COMPILE_PLAN (v1) のデータ構造を厳格に検証する (Phase 3A.1 新設)。
    Conditioningノードへの境界として、不正な計画データの伝播を水際で遮断します。
    """
    if not isinstance(plan, dict):
        raise ValueError("[CompilePlanValidator] Root COMPILE_PLAN must be a dictionary.")

    version = plan.get("version")
    if version != SUPPORTED_COMPILE_PLAN_VERSION:
        raise ValueError(f"[CompilePlanValidator] Unsupported COMPILE_PLAN version: {version}. Expected {SUPPORTED_COMPILE_PLAN_VERSION}.")

    status = plan.get("status")
    if status not in ("active", "inactive"):
        raise ValueError(f"[CompilePlanValidator] 'status' must be 'active' or 'inactive', got {status!r}")

    pid = plan.get("target_panel_id")
    if not isinstance(pid, int) or not (1 <= pid <= 6):
        raise ValueError(f"[CompilePlanValidator] 'target_panel_id' must be an integer between 1 and 6, got {pid!r}")

    canvas = plan.get("canvas")
    if not isinstance(canvas, dict) or "width" not in canvas or "height" not in canvas:
        raise ValueError(f"[CompilePlanValidator] 'canvas' must be a dictionary with 'width' and 'height'.")

    panel = plan.get("panel")
    if status == "active":
        if not isinstance(panel, dict):
            raise ValueError("[CompilePlanValidator] 'panel' must be a dictionary when status is 'active'.")
        if "id" not in panel or "geometry" not in panel:
            raise ValueError("[CompilePlanValidator] Active 'panel' must contain 'id' and 'geometry'.")
    else:
        if panel is not None:
            raise ValueError("[CompilePlanValidator] 'panel' must be null when status is 'inactive'.")

    _validate_strict_string(plan.get("global_prompt"), "global_prompt", "CompilePlan")
    _validate_strict_string(plan.get("global_negative_prompt"), "global_negative_prompt", "CompilePlan")
    _validate_strict_string(plan.get("compiled_prompt"), "compiled_prompt", "CompilePlan")
    _validate_strict_string(plan.get("compiled_negative_prompt"), "compiled_negative_prompt", "CompilePlan")

    characters = plan.get("characters")
    if not isinstance(characters, list):
        raise ValueError(f"[CompilePlanValidator] 'characters' must be a list, got {type(characters).__name__}")

    for idx, c in enumerate(characters):
        if not isinstance(c, dict):
            raise ValueError(f"[CompilePlanValidator] Character entry at index {idx} must be a dictionary.")
        _validate_strict_string(c.get("character_id"), "character_id", f"PlanCharacter[{idx}]", allow_empty=False)
        _validate_strict_string(c.get("name"), "name", f"PlanCharacter[{idx}]")
        _validate_strict_string(c.get("base_prompt"), "base_prompt", f"PlanCharacter[{idx}]")
        _validate_strict_string(c.get("override_prompt"), "override_prompt", f"PlanCharacter[{idx}]")
        _validate_strict_string(c.get("combined_prompt"), "combined_prompt", f"PlanCharacter[{idx}]")
        _validate_strict_string(c.get("base_negative_prompt"), "base_negative_prompt", f"PlanCharacter[{idx}]")
        _validate_strict_string(c.get("override_negative_prompt"), "override_negative_prompt", f"PlanCharacter[{idx}]")
        _validate_strict_string(c.get("combined_negative_prompt"), "combined_negative_prompt", f"PlanCharacter[{idx}]")

        area = c.get("area")
        if area is not None and not isinstance(area, dict):
            raise ValueError(f"[CompilePlanValidator] Character '{c.get('character_id')}' 'area' must be dict or null.")

        loras = c.get("loras", [])
        if not isinstance(loras, list):
            raise ValueError(f"[CompilePlanValidator] Character '{c.get('character_id')}' 'loras' must be a list.")
        for le in loras:
            validate_lora_entry(le, f"PlanCharacter '{c.get('character_id')}' LoRA")

    lora_plan = plan.get("lora_plan")
    if not isinstance(lora_plan, dict):
        raise ValueError("[CompilePlanValidator] 'lora_plan' must be a dictionary.")

    for scope in ("global_loras", "koma_loras", "character_loras"):
        scope_list = lora_plan.get(scope, [])
        if not isinstance(scope_list, list):
            raise ValueError(f"[CompilePlanValidator] 'lora_plan.{scope}' must be a list, got {type(scope_list).__name__}")
        for le in scope_list:
            validate_lora_entry(le, f"LoRA Plan ({scope})")

    return plan


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

    # generation.global_loras の Canonical 検証
    raw_global_loras = generation.get("global_loras", [])
    if not isinstance(raw_global_loras, list):
        raise ValueError(f"[MangaSceneSpecValidator] 'generation.global_loras' must be a list, got {type(raw_global_loras).__name__}")
    validated_global_loras = [validate_lora_entry(le, "Generation Global LoRA") for le in raw_global_loras]
    generation["global_loras"] = validated_global_loras

    validated = dict(spec)
    validated["region_spec"] = region_spec
    validated["cast_spec"] = cast_spec
    validated["generation"] = generation
    return validated
