import json
import logging
from typing import Dict, Any, List, Optional, Set, Tuple

from .region_editor import is_active_region, validate_region_spec
from .scene_spec import (
    validate_cast_spec,
    validate_character_binding,
    default_cast_spec,
    SUPPORTED_COMPILE_PLAN_VERSION,
    validate_lora_entry,
    parse_lora_tags,
    validate_compile_plan
)


class TegakiMangaSceneCompiler:
    """
    Tegaki Manga Scene Compiler (Phase 3A.1 Hardened)
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
        global_negative_prompt = spec.get("global_negative_prompt", "")

        # 2. 対象KOMAの探索
        target_koma = None
        for r in spec.get("regions", []):
            if r.get("id") == target_panel_id:
                target_koma = r
                break

        is_active = is_active_region(target_koma, panel_count) if target_koma else False
        bindings = target_koma.get("characters", []) if target_koma else []
        has_bindings = bool(bindings and len(bindings) > 0)

        # 3. CAST_SPEC のロードと厳格な契約検証 (指示書第3〜5項)
        cast = None
        has_cast = False
        cast_syntax_error = None

        if cast_spec:
            if isinstance(cast_spec, str):
                trimmed = cast_spec.strip()
                if trimmed not in ("{}", ""):
                    try:
                        parsed = json.loads(trimmed)
                        cast = validate_cast_spec(parsed)
                        has_cast = True
                    except json.JSONDecodeError as e:
                        cast_syntax_error = e
                    except ValueError as e:
                        # スキーマエラーは即時停止
                        raise ValueError(f"[TegakiSceneCompiler] CAST_SPEC schema error: {e}")
            elif isinstance(cast_spec, dict) and "characters" in cast_spec:
                cast = validate_cast_spec(cast_spec)
                has_cast = True

        # CASTなし + Bindingあり、または Broken CAST + Bindingあり の拒絶
        if has_bindings:
            if cast_syntax_error is not None:
                raise ValueError(
                    f"[TegakiSceneCompiler] Character binding detected in KOMA {target_panel_id}, "
                    f"but CAST_SPEC has syntax error: {cast_syntax_error}. "
                    f"A valid CAST_SPEC is required to resolve characters."
                )
            if not has_cast or not cast.get("characters"):
                raise ValueError(
                    f"[TegakiSceneCompiler] Character binding detected in KOMA {target_panel_id}, "
                    f"but CAST_SPEC is empty or missing. "
                    f"A valid CAST_SPEC is required to resolve characters."
                )
        else:
            # Bindingがない場合は、構文エラー時はwarningを出して空CASTへフォールバック
            if cast_syntax_error is not None:
                logging.warning(f"[TegakiSceneCompiler] Syntax error in cast_spec JSON: {cast_syntax_error}. Falling back to empty cast.")
            if not has_cast:
                cast = default_cast_spec()

        cast_map = {c["id"]: c for c in cast["characters"]}
        available_cids = set(cast_map.keys())

        # 4. Global Prompt の LoRA 解析と Clean Prompt 抽出
        clean_global_prompt, global_prompt_loras = parse_lora_tags(global_prompt, "global_prompt_tag")
        _, structured_global_loras = parse_lora_tags(global_loras, "structured_global")
        combined_global_loras = structured_global_loras + global_prompt_loras

        # 非Active KOMA の場合、安全な空Planを生成
        if not target_koma or not is_active:
            empty_plan = {
                "version": SUPPORTED_COMPILE_PLAN_VERSION,
                "status": "inactive",
                "target_panel_id": target_panel_id,
                "canvas": canvas,
                "panel": None,
                "global_prompt": clean_global_prompt,
                "global_negative_prompt": global_negative_prompt,
                "compiled_prompt": "",
                "compiled_negative_prompt": "",
                "characters": [],
                "lora_plan": {
                    "global_loras": combined_global_loras,
                    "koma_loras": [],
                    "character_loras": []
                }
            }
            validated_empty_plan = validate_compile_plan(empty_plan)
            empty_json = json.dumps(validated_empty_plan, indent=2, ensure_ascii=False)
            return (validated_empty_plan, empty_json, "", 0)

        # 5. KOMA Prompt の LoRA 解析
        koma_prompt = target_koma.get("prompt", "")
        panel_negative_prompt = target_koma.get("negative_prompt", "")
        clean_koma_prompt, koma_prompt_loras = parse_lora_tags(koma_prompt, "koma_prompt_tag")

        koma_loras_plan = []
        if "loras" in target_koma and isinstance(target_koma["loras"], list):
            for le in target_koma["loras"]:
                v_le = validate_lora_entry(le, f"KOMA {target_panel_id} LoRA")
                v_le["source"] = "structured_koma"
                if v_le.get("enabled", True):
                    koma_loras_plan.append(v_le)
        koma_loras_plan.extend(koma_prompt_loras)

        # 6. KOMA内 Character Binding のコンパイル
        compiled_characters = []
        character_prompts = []
        character_negative_prompts = []
        character_loras_plan = []

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

                raw_base_p = char_master.get("prompt", "")
                raw_override_p = validated_b.get("prompt_override", "")

                # 全階層LoRA Parser適用
                clean_base_p, base_c_loras = parse_lora_tags(raw_base_p, "character_prompt_tag")
                clean_override_p, override_c_loras = parse_lora_tags(raw_override_p, "character_override_tag")

                # Positive Prompt 結合
                pos_parts = [p.strip() for p in [clean_base_p, clean_override_p] if p and p.strip()]
                combined_c_prompt = ", ".join(pos_parts)
                if combined_c_prompt:
                    character_prompts.append(combined_c_prompt)

                # Negative Prompt 結合 (Phase 3A.1)
                base_neg = char_master.get("negative_prompt", "")
                override_neg = validated_b.get("negative_prompt_override", "")
                neg_parts = [p.strip() for p in [base_neg, override_neg] if p and p.strip()]
                combined_c_neg = ", ".join(neg_parts)
                if combined_c_neg:
                    character_negative_prompts.append(combined_c_neg)

                # Character LoRA (override があれば優先、なければ master から)
                c_loras = validated_b.get("lora_override")
                if c_loras is None:
                    c_loras = char_master.get("loras", [])

                # タグから抽出されたLoRAも追加
                tag_c_loras = base_c_loras + override_c_loras
                total_c_loras = list(c_loras) + tag_c_loras

                for lora_entry in total_c_loras:
                    if lora_entry.get("enabled", True):
                        character_loras_plan.append({
                            "character_id": cid,
                            "character_name": char_master.get("name", cid),
                            "name": lora_entry["name"],
                            "enabled": True,
                            "model_weight": lora_entry.get("model_weight", 1.0),
                            "clip_weight": lora_entry.get("clip_weight", 1.0),
                            "source": lora_entry.get("source", "structured_character"),
                            "metadata": lora_entry.get("metadata", {})
                        })

                compiled_c = {
                    "character_id": cid,
                    "name": char_master.get("name", cid),
                    "base_prompt": clean_base_p,
                    "override_prompt": clean_override_p,
                    "combined_prompt": combined_c_prompt,
                    "base_negative_prompt": base_neg,
                    "override_negative_prompt": override_neg,
                    "combined_negative_prompt": combined_c_neg,
                    "area": validated_b.get("area"),  # None または KOMA-local 座標
                    "loras": total_c_loras,
                    "metadata": validated_b.get("metadata", {})
                }
                compiled_characters.append(compiled_c)

        # 7. 自然結合プレビュー用 Positive / Negative Prompt の生成
        prompt_parts = []
        if clean_global_prompt:
            prompt_parts.append(clean_global_prompt)
        if clean_koma_prompt:
            prompt_parts.append(clean_koma_prompt)
        if character_prompts:
            prompt_parts.extend(character_prompts)
        compiled_prompt = ", ".join(prompt_parts)

        neg_parts = []
        if global_negative_prompt:
            neg_parts.append(global_negative_prompt.strip())
        if panel_negative_prompt:
            neg_parts.append(panel_negative_prompt.strip())
        if character_negative_prompts:
            neg_parts.extend(character_negative_prompts)
        compiled_negative_prompt = ", ".join(neg_parts)

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
                "prompt": clean_koma_prompt,
                "negative_prompt": panel_negative_prompt
            },
            "global_prompt": clean_global_prompt,
            "global_negative_prompt": global_negative_prompt,
            "compiled_prompt": compiled_prompt,
            "compiled_negative_prompt": compiled_negative_prompt,
            "characters": compiled_characters,
            "lora_plan": {
                "global_loras": combined_global_loras,
                "koma_loras": koma_loras_plan,
                "character_loras": character_loras_plan
            }
        }

        # 自己検証を実行 (指示書第31項)
        validated_plan = validate_compile_plan(compile_plan)

        plan_json = json.dumps(validated_plan, indent=2, ensure_ascii=False)
        char_count = len(compiled_characters)

        return (validated_plan, plan_json, compiled_prompt, char_count)
