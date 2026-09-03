import re
import os
import logging
import folder_paths
import comfy.utils
import comfy.sd

# LoRAファイルのメモリキャッシュ（複数回呼び出し時の高速化）
_LORA_FILE_CACHE = {}

def get_available_loras():
    return folder_paths.get_filename_list("loras")

def resolve_lora_name(requested_name: str, available_loras: list[str]) -> str | None:
    """
    指定された名前から実際のLoRAファイルパスを柔軟に解決する:
    1. 完全一致
    2. 拡張子補完 (.safetensors, .pt など)
    3. ファイル名のみ一致 (サブディレクトリ考慮)
    4. 大小文字を無視した一致
    """
    cleaned = requested_name.strip()
    if not cleaned:
        return None

    norm_req = cleaned.replace("\\", "/").lower()
    base_req = os.path.splitext(os.path.basename(norm_req))[0]

    # 1. 完全一致 (パスそのまま)
    for l in available_loras:
        if l == cleaned:
            return l

    # 2. パスそのまま (大文字小文字無視)
    for l in available_loras:
        if l.replace("\\", "/").lower() == norm_req:
            return l

    # 3. 拡張子補完
    for ext in [".safetensors", ".pt", ".ckpt"]:
        cand = cleaned + ext
        for l in available_loras:
            if l.replace("\\", "/").lower() == cand.replace("\\", "/").lower():
                return l

    # 4. ベースファイル名一致 (サブディレクトリ内のLoRAも名前だけで呼べるように)
    matches = []
    for l in available_loras:
        l_norm = l.replace("\\", "/")
        l_base = os.path.splitext(os.path.basename(l_norm))[0].lower()
        if l_base == base_req:
            matches.append(l)

    if len(matches) == 1:
        return matches[0]
    elif len(matches) > 1:
        logging.warning(f"[TegakiLora] Multiple LoRA files match base name '{cleaned}': {matches}. Using first: {matches[0]}")
        return matches[0]

    # 5. 部分一致（プレフィックス等）
    for l in available_loras:
        l_norm = l.replace("\\", "/").lower()
        if base_req in l_norm:
            return l

    return None

class TegakiLoraPromptLoader:
    """
    Prompt文字列から `<lora:name:weight>` または `<lora:name:modelWeight:clipWeight>` を抽出し、
    自動的にMODELおよびCLIPに適用するノード。
    漫画制作向けに、複数のLoRAを直感的にブレンド・適用できます。
    """
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "model": ("MODEL",),
                "clip": ("CLIP",),
                "text": ("STRING", {"multiline": True, "dynamicPrompts": True, "default": ""}),
            },
            "optional": {
                "optional_lora_stack": ("LORA_STACK",),
            }
        }

    RETURN_TYPES = ("MODEL", "CLIP", "STRING", "LORA_STACK")
    RETURN_NAMES = ("MODEL", "CLIP", "clean_text", "lora_stack")
    FUNCTION = "apply_loras"
    CATEGORY = "tegaki/manga"

    def apply_loras(self, model, clip, text: str, optional_lora_stack=None):
        pattern = r'<lora:([^:>]+)(?::(-?\d+(?:\.\d+)?))?(?::(-?\d+(?:\.\d+)?))?>'
        
        available = get_available_loras()
        lora_stack = list(optional_lora_stack) if optional_lora_stack is not None else []
        
        applied_model = model
        applied_clip = clip

        # マッチを検索
        matches = list(re.finditer(pattern, text))
        
        for m in matches:
            lora_name_raw = m.group(1).strip()
            # weight解析
            m_weight_str = m.group(2)
            c_weight_str = m.group(3)

            model_weight = float(m_weight_str) if m_weight_str is not None else 1.0
            clip_weight = float(c_weight_str) if c_weight_str is not None else model_weight

            resolved_path = resolve_lora_name(lora_name_raw, available)
            if not resolved_path:
                logging.error(f"[TegakiLora] ERROR: LoRA not found: '{lora_name_raw}'. Check your spelling or model directory.")
                continue

            full_lora_path = folder_paths.get_full_path("loras", resolved_path)
            if not full_lora_path or not os.path.exists(full_lora_path):
                logging.error(f"[TegakiLora] ERROR: Full path resolution failed for LoRA: '{resolved_path}'")
                continue

            logging.info(f"[TegakiLora] Loading LoRA: '{resolved_path}' (model_weight={model_weight}, clip_weight={clip_weight})")

            # キャッシュから読み込み、またはディスクから読み込み
            if full_lora_path in _LORA_FILE_CACHE:
                lora_data = _LORA_FILE_CACHE[full_lora_path]
            else:
                lora_data = comfy.utils.load_torch_file(full_lora_path, safe_load=True)
                _LORA_FILE_CACHE[full_lora_path] = lora_data

            applied_model, applied_clip = comfy.sd.load_lora_for_models(
                applied_model, applied_clip, lora_data, model_weight, clip_weight
            )

            lora_stack.append((resolved_path, model_weight, clip_weight))

        # LoRAタグをプロンプトから除去して綺麗なプロンプトを生成
        clean_text = re.sub(pattern, "", text)
        clean_text = re.sub(r'[\s,]+,', ',', clean_text)
        clean_text = clean_text.strip()

        return (applied_model, applied_clip, clean_text, lora_stack)


class TegakiLoraStackToPrompt:
    """
    LoRA Stack (Inspire/Impact Pack等) を `<lora:name:weight>` 形式のプロンプトテキストに変換・可視化するノード。
    ワークフローの共有・レビュー用。
    """
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "lora_stack": ("LORA_STACK",),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("lora_prompt_text",)
    FUNCTION = "convert_to_text"
    CATEGORY = "tegaki/manga"

    def convert_to_text(self, lora_stack):
        lines = []
        for item in lora_stack:
            if len(item) >= 3:
                name, mw, cw = item[0], item[1], item[2]
                if mw == cw:
                    lines.append(f"<lora:{os.path.splitext(os.path.basename(name))[0]}:{mw:.2f}>")
                else:
                    lines.append(f"<lora:{os.path.splitext(os.path.basename(name))[0]}:{mw:.2f}:{cw:.2f}>")
        return ("\n".join(lines),)
