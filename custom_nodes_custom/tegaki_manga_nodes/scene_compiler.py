import json
import logging
from typing import Dict, Any, List, Optional, Set, Tuple

from .region_editor import is_active_region, validate_region_spec
from .scene_spec import (
    validate_cast_spec,
    validate_character_binding,
    validate_local_region,
    default_cast_spec,
    SUPPORTED_COMPILE_PLAN_VERSION,
    SUPPORTED_PAGE_COMPILE_PLAN_VERSION,
    validate_lora_entry,
    parse_lora_tags,
    validate_compile_plan,
    validate_page_compile_plan,
    get_active_panel_ids
)
from .interaction_resolver import generate_stable_instance_id, normalize_interaction
from .subscene_contract import has_active_subscenes, validate_panel_subscenes


def compile_panel_data(
    region_spec: Any,
    target_panel_id: int,
    cast_spec: Any = "{}",
    global_loras: str = ""
) -> Tuple[Dict[str, Any], str, str, int]:
    """
    1コマ (KOMA) の実行計画 (COMPILE_PLAN v1) をコンパイルする純粋関数 (Phase 3B / 3B.1)。
    PAGE ├ KOMA ├ LOCAL_REGION └ CHARACTER の4階層を統合・正規化します。
    """
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
    koma_prompt = target_koma.get("prompt") or (target_koma.get("panel", {}).get("prompt") if isinstance(target_koma.get("panel"), dict) else "") or ""
    panel_negative_prompt = target_koma.get("negative_prompt") or (target_koma.get("panel", {}).get("negative_prompt") if isinstance(target_koma.get("panel"), dict) else "") or ""
    clean_koma_prompt, koma_prompt_loras = parse_lora_tags(koma_prompt, "koma_prompt_tag")

    koma_loras_plan = []
    if "loras" in target_koma and isinstance(target_koma["loras"], list):
        for le in target_koma["loras"]:
            v_le = validate_lora_entry(le, f"KOMA {target_panel_id} LoRA")
            v_le["source"] = "structured_koma"
            if v_le.get("enabled", True):
                koma_loras_plan.append(v_le)
    koma_loras_plan.extend(koma_prompt_loras)

    # 5.5. KOMA内 Local Region のコンパイル (Phase 3B.1 新設)
    raw_local_regions = target_koma.get("local_regions", [])
    compiled_local_regions = []
    local_region_prompts = []
    local_region_negative_prompts = []

    if raw_local_regions:
        if not isinstance(raw_local_regions, list):
            raise ValueError(f"[TegakiSceneCompiler] KOMA {target_panel_id} 'local_regions' must be a list.")
        seen_lr_ids = set()
        for lr_idx, lr in enumerate(raw_local_regions):
            v_lr = validate_local_region(lr, f"KOMA {target_panel_id} local_region[{lr_idx}]")
            if v_lr["id"] in seen_lr_ids:
                raise ValueError(f"[TegakiSceneCompiler] KOMA {target_panel_id} duplicate local_region id: '{v_lr['id']}'")
            seen_lr_ids.add(v_lr["id"])

            if not v_lr.get("enabled", True):
                continue

            clean_lr_p, lr_p_loras = parse_lora_tags(v_lr["prompt"], f"koma_{target_panel_id}_local_{v_lr['id']}")
            clean_lr_neg, _ = parse_lora_tags(v_lr["negative_prompt"], f"koma_{target_panel_id}_local_neg_{v_lr['id']}")

            if clean_lr_p:
                local_region_prompts.append(clean_lr_p)
            if clean_lr_neg:
                local_region_negative_prompts.append(clean_lr_neg)

            # タグから抽出されたLoRAはコマLoRAプランに合流
            koma_loras_plan.extend(lr_p_loras)

            compiled_lr = dict(v_lr)
            compiled_lr["prompt"] = clean_lr_p
            compiled_lr["negative_prompt"] = clean_lr_neg
            compiled_local_regions.append(compiled_lr)

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

            c_meta = dict(validated_b.get("metadata", {}))
            shot_type = validated_b.get("shot_type") or c_meta.get("shot_type") or validated_b.get("shot")
            pose_preset = validated_b.get("pose_preset") or c_meta.get("pose_preset")
            raw_inter = validated_b.get("interaction") or c_meta.get("interaction")
            raw_iid = validated_b.get("instance_id") or c_meta.get("instance_id")
            if not raw_iid:
                raw_iid = generate_stable_instance_id(target_panel_id, cid, index=b_idx + 1)
            instance_id = str(raw_iid).strip()
            c_meta["instance_id"] = instance_id

            interaction = normalize_interaction(raw_inter, source_instance_id=instance_id, context=f"KOMA {target_panel_id}.{instance_id}")

            if shot_type:
                c_meta["shot_type"] = shot_type
            if pose_preset:
                c_meta["pose_preset"] = pose_preset
            if interaction:
                c_meta["interaction"] = interaction

            compiled_c = {
                "instance_id": instance_id,
                "character_id": cid,
                "name": char_master.get("name", cid),
                "base_prompt": clean_base_p,
                "override_prompt": clean_override_p,
                "combined_prompt": combined_c_prompt,
                "base_negative_prompt": base_neg,
                "override_negative_prompt": override_neg,
                "combined_negative_prompt": combined_c_neg,
                "area": validated_b.get("area"),  # None または KOMA-local 座標
                "shot_type": shot_type,
                "pose_preset": pose_preset,
                "interaction": interaction,
                "loras": total_c_loras,
                "metadata": c_meta
            }
            compiled_characters.append(compiled_c)

    # Phase 3L: SubScene Compilation (Mainline Compiler Integration)
    compiled_subscenes = []
    if has_active_subscenes(target_koma):
        validated_subscenes = validate_panel_subscenes(target_koma, panel_id=target_panel_id, context=f"KOMA {target_panel_id}")
        for s_idx, sub in enumerate(validated_subscenes):
            if not sub.get("enabled", True):
                continue
            s_id = sub["id"]
            raw_s_prompt = sub.get("prompt", "")
            raw_s_neg = sub.get("negative_prompt", "")
            clean_s_prompt, _ = parse_lora_tags(raw_s_prompt, f"subscene_{s_id}_prompt")
            
            sub_chars = []
            for sb_idx, sb in enumerate(sub.get("character_bindings", [])):
                if not sb.get("enabled", True):
                    continue
                s_cid = sb["character_id"]
                s_char_master = cast_map.get(s_cid, {})
                if not s_char_master.get("enabled", True):
                    continue
                
                s_base_p = s_char_master.get("prompt", "")
                s_override_p = sb.get("prompt_override", "")
                clean_sb_base, sb_base_loras = parse_lora_tags(s_base_p, f"sub_{s_id}_char_base")
                clean_sb_over, sb_over_loras = parse_lora_tags(s_override_p, f"sub_{s_id}_char_over")
                
                sb_pos_parts = [p.strip() for p in [clean_sb_base, clean_sb_over] if p and p.strip()]
                combined_sb_prompt = ", ".join(sb_pos_parts)
                
                sb_base_neg = s_char_master.get("negative_prompt", "")
                sb_over_neg = sb.get("negative_prompt_override", "")
                sb_neg_parts = [p.strip() for p in [sb_base_neg, sb_over_neg] if p and p.strip()]
                combined_sb_neg = ", ".join(sb_neg_parts)
                
                sb_loras = s_char_master.get("loras", [])
                total_sb_loras = list(sb_loras) + sb_base_loras + sb_over_loras
                for le in total_sb_loras:
                    if le.get("enabled", True):
                        character_loras_plan.append({
                            "character_id": s_cid,
                            "character_name": s_char_master.get("name", s_cid),
                            "name": le["name"],
                            "enabled": True,
                            "model_weight": le.get("model_weight", 1.0),
                            "clip_weight": le.get("clip_weight", 1.0),
                            "source": f"subscene_{s_id}",
                            "metadata": le.get("metadata", {})
                        })
                
                sb_meta = dict(sb.get("metadata", {}))
                sb_shot = sb.get("shot_type") or sb_meta.get("shot_type")
                sb_pose = sb.get("pose_preset") or sb_meta.get("pose_preset")
                sb_iid = sb.get("instance_id") or sb_meta.get("instance_id")
                if not sb_iid:
                    sb_iid = generate_stable_instance_id(target_panel_id, s_cid, subscene_id=s_id, index=sb_idx + 1)
                sb_iid = str(sb_iid).strip()
                sb_meta["instance_id"] = sb_iid

                raw_sb_inter = sb.get("interaction") or sb_meta.get("interaction")
                sb_inter = normalize_interaction(raw_sb_inter, source_instance_id=sb_iid, context=f"KOMA {target_panel_id}.{s_id}.{sb_iid}")

                if sb_shot:
                    sb_meta["shot_type"] = sb_shot
                if sb_pose:
                    sb_meta["pose_preset"] = sb_pose
                if sb_inter:
                    sb_meta["interaction"] = sb_inter
                
                sub_chars.append({
                    "instance_id": sb_iid,
                    "character_id": s_cid,
                    "name": s_char_master.get("name", s_cid),
                    "base_prompt": clean_sb_base,
                    "override_prompt": clean_sb_over,
                    "combined_prompt": combined_sb_prompt,
                    "base_negative_prompt": sb_base_neg,
                    "override_negative_prompt": sb_over_neg,
                    "combined_negative_prompt": combined_sb_neg,
                    "area": sb.get("area"),
                    "shot_type": sb_shot,
                    "pose_preset": sb_pose,
                    "interaction": sb_inter,
                    "loras": total_sb_loras,
                    "metadata": sb_meta
                })
            
            compiled_subscenes.append({
                "id": s_id,
                "enabled": True,
                "prompt": clean_s_prompt,
                "negative_prompt": raw_s_neg,
                "area": sub.get("area", {"x": 0.0, "y": 0.0, "w": 1.0, "h": 1.0}),
                "characters": sub_chars,
                "metadata": dict(sub.get("metadata", {}))
            })

    # 7. 自然結合プレビュー用 Positive / Negative Prompt の生成
    # 優先順位 (指示書第20項): Global -> Panel -> Local Region -> Character
    prompt_parts = []
    if clean_global_prompt:
        prompt_parts.append(clean_global_prompt)
    if clean_koma_prompt:
        prompt_parts.append(clean_koma_prompt)
    if local_region_prompts:
        prompt_parts.extend(local_region_prompts)
    if character_prompts:
        prompt_parts.extend(character_prompts)
    compiled_prompt = ", ".join(prompt_parts)

    neg_parts = []
    if global_negative_prompt:
        neg_parts.append(global_negative_prompt.strip())
    if panel_negative_prompt:
        neg_parts.append(panel_negative_prompt.strip())
    if local_region_negative_prompts:
        neg_parts.extend(local_region_negative_prompts)
    if character_negative_prompts:
        neg_parts.extend(character_negative_prompts)
    compiled_negative_prompt = ", ".join(neg_parts)

    # 8. COMPILE_PLAN (v1) データ構造の構築
    panel_camera_dist = target_koma.get("camera_distance") or (target_koma.get("metadata", {}).get("camera_distance") if isinstance(target_koma.get("metadata"), dict) else None) or "medium"
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
            "negative_prompt": panel_negative_prompt,
            "local_regions": compiled_local_regions,
            "subscenes": compiled_subscenes,
            "camera_distance": panel_camera_dist
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
    char_count = len(compiled_characters) + sum(len(s["characters"]) for s in compiled_subscenes)

    return (validated_plan, plan_json, compiled_prompt, char_count)


class TegakiMangaSceneCompiler:
    """
    Tegaki Manga Scene Compiler (Phase 3A / 3B)
    REGION_SPEC と CAST_SPEC から、指定したKOMAに関する統合実行計画 (COMPILE_PLAN v1) をコンパイル・生成する。
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
        return compile_panel_data(
            region_spec=region_spec,
            target_panel_id=target_panel_id,
            cast_spec=cast_spec,
            global_loras=global_loras
        )


class TegakiMangaPageCompiler:
    """
    Tegaki Manga Page Compiler (Phase 3B / 3B.1)
    REGION_SPEC と CAST_SPEC から、ページ全体の全Active KOMAに関する統合実行計画 (PAGE_COMPILE_PLAN v1) をコンパイルする。
    """
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "region_spec": ("REGION_SPEC",),
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

    RETURN_TYPES = ("PAGE_COMPILE_PLAN", "STRING", "STRING", "INT")
    RETURN_NAMES = ("page_compile_plan", "page_compile_plan_json", "global_loras_text", "active_panels_count")
    FUNCTION = "compile_page"
    CATEGORY = "tegaki/manga"

    def compile_page(self, region_spec: Any, cast_spec: Any = "{}", global_loras: str = ""):
        spec = validate_region_spec(region_spec)
        active_pids = get_active_panel_ids(spec)
        canvas = spec.get("canvas", {"width": 832, "height": 1216})
        global_prompt = spec.get("global_prompt", "")
        global_negative_prompt = spec.get("global_negative_prompt", "")

        # Global Prompt の LoRA 解析と Clean Prompt 抽出
        clean_global_prompt, global_prompt_loras = parse_lora_tags(global_prompt, "global_prompt_tag")
        _, structured_global_loras = parse_lora_tags(global_loras, "structured_global")
        combined_global_loras = structured_global_loras + global_prompt_loras

        # 各Active KOMAをコンパイル
        panels = []
        for pid in active_pids:
            p_plan, _, _, _ = compile_panel_data(
                region_spec=spec,
                target_panel_id=pid,
                cast_spec=cast_spec,
                global_loras=global_loras
            )
            panels.append(p_plan)

        page_compile_plan = {
            "version": SUPPORTED_PAGE_COMPILE_PLAN_VERSION,
            "canvas": canvas,
            "active_panel_ids": active_pids,
            "global_prompt": clean_global_prompt,
            "global_negative_prompt": global_negative_prompt,
            "global_loras": combined_global_loras,
            "panels": panels
        }

        # 自己検証
        validated_page_plan = validate_page_compile_plan(page_compile_plan)
        plan_json = json.dumps(validated_page_plan, indent=2, ensure_ascii=False)

        # Global LoRA Adapter用テキスト (SSOT: <lora:name:model_weight:clip_weight>)
        lora_tag_tokens = []
        for gle in combined_global_loras:
            if gle.get("enabled", True):
                name = gle["name"]
                mw = gle.get("model_weight", 1.0)
                cw = gle.get("clip_weight", 1.0)
                lora_tag_tokens.append(f"<lora:{name}:{mw}:{cw}>")
        global_loras_text = " ".join(lora_tag_tokens)

        return (validated_page_plan, plan_json, global_loras_text, len(active_pids))


class TegakiCompilePlanInspector:
    """
    Tegaki Compile Plan Inspector (Phase 3B / 3B.1 監査ノード)
    COMPILE_PLAN または PAGE_COMPILE_PLAN を視覚的に監査・検査し、
    Active Panel IDs, Characters, Local Regions, LoRA Plan, Prompt 階層を綺麗に可視化する。
    """
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "compile_plan": ("COMPILE_PLAN",),
            }
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("inspection_summary", "plan_json_pretty")
    FUNCTION = "inspect_plan"
    CATEGORY = "tegaki/manga"
    OUTPUT_NODE = True

    def inspect_plan(self, compile_plan: Any):
        plan = validate_compile_plan(compile_plan)
        status = plan.get("status", "unknown")
        pid = plan.get("target_panel_id", 0)
        canvas = plan.get("canvas", {})
        characters = plan.get("characters", [])
        lora_plan = plan.get("lora_plan", {})
        local_regions = plan.get("panel", {}).get("local_regions", []) if plan.get("panel") else []

        g_loras = [f"{l['name']}(m={l.get('model_weight')},c={l.get('clip_weight')})" for l in lora_plan.get("global_loras", [])]
        k_loras = [f"{l['name']}(m={l.get('model_weight')},c={l.get('clip_weight')})" for l in lora_plan.get("koma_loras", [])]
        c_loras = [f"{l.get('character_name')}:{l['name']}(m={l.get('model_weight')},c={l.get('clip_weight')})" for l in lora_plan.get("character_loras", [])]

        char_areas = []
        for c in characters:
            cid = c.get("character_id")
            cname = c.get("name", cid)
            area = c.get("area")
            if area:
                char_areas.append(f"{cname}: [x={area['x']}, y={area['y']}, w={area['w']}, h={area['h']}]")
            else:
                char_areas.append(f"{cname}: Unconstrained (None)")

        lr_summaries = []
        for lr in local_regions:
            l_area = lr.get("area", {})
            lr_summaries.append(
                f"  • [{lr.get('id')}] {lr.get('name')}: "
                f"Pos='{lr.get('prompt')}' | Neg='{lr.get('negative_prompt')}' | "
                f"Area=[x={l_area.get('x')}, y={l_area.get('y')}, w={l_area.get('w')}, h={l_area.get('h')}]"
            )

        lines = [
            f"=== Tegaki Compile Plan Inspection (KOMA {pid}) ===",
            f"Status: {status.upper()}",
            f"Canvas: {canvas.get('width', 0)}x{canvas.get('height', 0)}",
            f"Target Panel ID: {pid}",
            "",
            "--- Prompt Summaries ---",
            f"Compiled Positive: {plan.get('compiled_prompt', '')}",
            f"Compiled Negative: {plan.get('compiled_negative_prompt', '')}",
            "",
            f"--- Characters ({len(characters)}) ---",
        ]
        for c in characters:
            lines.append(f"  • [{c.get('character_id')}] {c.get('name')}: Pos='{c.get('combined_prompt')}' | Neg='{c.get('combined_negative_prompt')}'")

        lines.extend([
            "",
            "--- Character Areas (KOMA-local) ---",
            "  " + ("\n  ".join(char_areas) if char_areas else "None"),
            "",
            f"--- Local Regions ({len(local_regions)}) ---",
            ("  " + "\n  ".join(lr_summaries)) if lr_summaries else "  None",
            "",
            "--- LoRA Plan ---",
            f"  Global LoRAs ({len(g_loras)}): {', '.join(g_loras) if g_loras else 'None'}",
            f"  KOMA LoRAs ({len(k_loras)}): {', '.join(k_loras) if k_loras else 'None'}",
            f"  Character LoRAs ({len(c_loras)}): {', '.join(c_loras) if c_loras else 'None'}",
            "=================================================="
        ])

        summary_text = "\n".join(lines)
        pretty_json = json.dumps(plan, indent=2, ensure_ascii=False)
        return {"ui": {"text": [summary_text]}, "result": (summary_text, pretty_json)}
