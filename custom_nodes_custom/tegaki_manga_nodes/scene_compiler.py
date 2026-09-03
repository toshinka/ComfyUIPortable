import json
import re
import logging
from typing import Dict, Any, List, Optional, Set, Tuple

from .region_editor import is_active_region, validate_region_spec
from .scene_spec import (
    validate_cast_spec,
    validate_character_binding,
    default_cast_spec,
    SUPPORTED_CAST_SPEC_VERSION,
    validate_lora_entry
)

SUPPORTED_COMPILE_PLAN_VERSION = 1
LORA_TAG_REGEX = re.compile(r"<lora:([^:>]+)(?::([0-9.-]+))?(?::([0-9.-]+))?>", re.IGNORECASE)


def parse_lora_tags_to_plan(prompt_text: str) -> List[Dict[str, Any]]:
    """
    Prompt文字列から <lora:name:weight> を抽出して LoRA Plan エントリ一覧を生成する
    """
    if not prompt_text:
        return []
    plan = []
    for match in LORA_TAG_REGEX.finditer(prompt_text):
        name = match.group(1).strip()
        weight_str = match.group(2)
        weight = float(weight_str) if weight_str is not None else 1.0
        plan.append({
            "name": name,
            "weight": round(weight, 4),
            "enabled": True,
            "source": "tag"
        })
    return plan


class TegakiMangaSceneCompiler:
    """
    Tegaki Manga Scene Compiler (Phase 3A プロトタイプ)
    REGION_SPEC と CAST_SPEC から、指定したKOMAに関する統合実行計画 (COMPILE_PLAN v1) をコンパイル・生成する。
    PAGE ├ KOMA └ CHARACTER の意味階層を維持し、次PhaseのConditioning生成への明確なデータ契約を提供します。
    """
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "region_spec": ("REGION_SPEC",),
                "target_panel_id": ("INT", {"default": 1, "min": 1, "max": 6, "step": 1}),
            },
            "optional": {
                "cast_spec": ("STRING", {
                    "multiline": True,
                    "default": "{}"
                }),
                "global_loras": ("STRING", {
                    "multiline": True,
                    "dynamicPrompts": True,
                    "default": ""
                }),
            }
        }

    RETURN_TYPES = ("COMPILE_PLAN", "STRING", "STRING", "INT")
    RETURN_NAMES = ("compile_plan", "compile_plan_json", "compiled_prompt", "character_count")
    FUNCTION = "compile_panel"
    CATEGORY = "tegaki/manga"

    def compile_panel(self, region_spec: Any, target_panel_id: int, cast_spec: Any = "{}", global_loras: str = ""):
        # 1. REGION_SPEC の検証
        spec = validate_region_spec(region_spec)
        canvas = spec.get("canvas", {"width": 832, "height": 1216})
        panel_count = spec.get("panel_count", 3)
        global_prompt = spec.get("global_prompt", "")

        # 2. CAST_SPEC のロードと検証 (CAST_SPEC なし互換モード対応)
        cast = None
        has_cast = False
        if cast_spec:
            if isinstance(cast_spec, str) and cast_spec.strip() not in ("{}", ""):
                try:
                    parsed = json.loads(cast_spec)
                    cast = validate_cast_spec(parsed)
                    has_cast = True
                except json.JSONDecodeError as e:
                    logging.warning(f"[TegakiSceneCompiler] Syntax error in cast_spec JSON: {e}. Falling back to empty cast.")
                    cast = default_cast_spec()
            elif isinstance(cast_spec, dict) and "characters" in cast_spec:
                cast = validate_cast_spec(cast_spec)
                has_cast = True

        if not has_cast:
            cast = default_cast_spec()

        cast_map = {c["id"]: c for c in cast["characters"]}
        available_cids = set(cast_map.keys())

        # 3. 対象KOMAの探索
        target_koma = None
        for r in spec.get("regions", []):
            if r.get("id") == target_panel_id:
                target_koma = r
                break

        is_active = is_active_region(target_koma, panel_count) if target_koma else False

        # 非Active KOMA の場合、安全な空Planを生成
        if not target_koma or not is_active:
            empty_plan = {
                "version": SUPPORTED_COMPILE_PLAN_VERSION,
                "status": "inactive",
                "target_panel_id": target_panel_id,
                "canvas": canvas,
                "panel": None,
                "global_prompt": global_prompt,
                "characters": [],
                "lora_plan": {
                    "global_loras": parse_lora_tags_to_plan(global_loras),
                    "koma_loras": [],
                    "character_loras": []
                }
            }
            empty_json = json.dumps(empty_plan, indent=2, ensure_ascii=False)
            return (empty_plan, empty_json, "", 0)

        # 4. KOMA内 Character Binding のコンパイル
        compiled_characters = []
        character_prompts = []
        character_loras_plan = []

        bindings = target_koma.get("characters", [])
        if bindings:
            if not isinstance(bindings, list):
                raise ValueError(f"[TegakiSceneCompiler] KOMA {target_panel_id} 'characters' must be a list.")

            for b_idx, b in enumerate(bindings):
                # Bindingの検証 (未知IDは ValueError 送出)
                validated_b = validate_character_binding(
                    b,
                    available_character_ids=available_cids if has_cast else None,
                    context_name=f"KOMA {target_panel_id} binding[{b_idx}]"
                )

                if not validated_b.get("enabled", True):
                    continue

                cid = validated_b["character_id"]
                char_master = cast_map.get(cid, {})

                if not char_master.get("enabled", True):
                    continue

                base_prompt = char_master.get("prompt", "")
                override_prompt = validated_b.get("prompt_override", "")

                # Combined Character Prompt
                parts = [p.strip() for p in [base_prompt, override_prompt] if p and p.strip()]
                combined_c_prompt = ", ".join(parts)
                if combined_c_prompt:
                    character_prompts.append(combined_c_prompt)

                # Character LoRA (override があれば優先、なければ master から)
                c_loras = validated_b.get("lora_override")
                if c_loras is None:
                    c_loras = char_master.get("loras", [])

                for lora_entry in c_loras:
                    if lora_entry.get("enabled", True):
                        character_loras_plan.append({
                            "character_id": cid,
                            "character_name": char_master.get("name", cid),
                            "name": lora_entry["name"],
                            "weight": lora_entry["weight"],
                            "enabled": True
                        })

                compiled_c = {
                    "character_id": cid,
                    "name": char_master.get("name", cid),
                    "base_prompt": base_prompt,
                    "override_prompt": override_prompt,
                    "combined_prompt": combined_c_prompt,
                    "area": validated_b.get("area"),  # None または KOMA-local 座標
                    "loras": c_loras,
                    "metadata": validated_b.get("metadata", {})
                }
                compiled_characters.append(compiled_c)

        # 5. KOMA LoRA の集約
        koma_prompt = target_koma.get("prompt", "")
        koma_loras_plan = []
        if "loras" in target_koma and isinstance(target_koma["loras"], list):
            for le in target_koma["loras"]:
                v_le = validate_lora_entry(le, f"KOMA {target_panel_id} LoRA")
                if v_le.get("enabled", True):
                    koma_loras_plan.append(v_le)
        # KOMA Prompt内の <lora:...> も抽出
        koma_loras_plan.extend(parse_lora_tags_to_plan(koma_prompt))

        # 6. Global LoRA の集約
        global_loras_plan = parse_lora_tags_to_plan(global_loras)

        # 7. 自然結合プレビュー用 Prompt の生成
        prompt_parts = []
        if global_prompt and global_prompt.strip():
            prompt_parts.append(global_prompt.strip())
        if koma_prompt and koma_prompt.strip():
            # <lora:...> タグを除去したクリーンプロンプト
            clean_koma_prompt = LORA_TAG_REGEX.sub("", koma_prompt).strip()
            if clean_koma_prompt:
                prompt_parts.append(clean_koma_prompt)
        if character_prompts:
            prompt_parts.extend(character_prompts)

        compiled_prompt = ", ".join(prompt_parts)

        # 8. COMPILE_PLAN (v1) データ構造の構築
        compile_plan = {
            "version": SUPPORTED_COMPILE_PLAN_VERSION,
            "status": "active",
            "target_panel_id": target_panel_id,
            "canvas": canvas,
            "panel": {
                "id": target_panel_id,
                "enabled": True,
                "geometry": {
                    "x": target_koma["x"],
                    "y": target_koma["y"],
                    "w": target_koma["w"],
                    "h": target_koma["h"]
                },
                "prompt": koma_prompt
            },
            "global_prompt": global_prompt,
            "characters": compiled_characters,
            "lora_plan": {
                "global_loras": global_loras_plan,
                "koma_loras": koma_loras_plan,
                "character_loras": character_loras_plan
            }
        }

        plan_json = json.dumps(compile_plan, indent=2, ensure_ascii=False)
        char_count = len(compiled_characters)

        return (compile_plan, plan_json, compiled_prompt, char_count)
