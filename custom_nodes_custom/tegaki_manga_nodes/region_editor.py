import json
import logging
import torch
import numpy as np
from PIL import Image, ImageDraw

# KOMA 1〜6 の統一カラーパレット (RGB & Hex)
# Presentation 情報としての固定パレット。KOMA identity に紐づく。
KOMA_COLORS = [
    {"name": "KOMA 1", "hex": "#E53935", "rgb": (229, 57, 53)},    # Red
    {"name": "KOMA 2", "hex": "#1E88E5", "rgb": (30, 136, 229)},   # Blue
    {"name": "KOMA 3", "hex": "#43A047", "rgb": (67, 160, 71)},    # Green
    {"name": "KOMA 4", "hex": "#FB8C00", "rgb": (251, 140, 0)},    # Amber/Orange
    {"name": "KOMA 5", "hex": "#8E24AA", "rgb": (142, 36, 170)},   # Purple
    {"name": "KOMA 6", "hex": "#00ACC1", "rgb": (0, 172, 193)},    # Cyan
]

SUPPORTED_SCHEMA_VERSION = 1


MIN_REGION_SIZE = 0.001


def is_active_region(region: dict, panel_count: int) -> bool:
    """
    KOMAが現在アクティブ（有効かつ現在のコマ数範囲内）であるかを判定する共通ルール。
    Frontend, Backend, 将来のCompilerで同一の定義を使用します。
    厳格な boolean (enabled is True) を要求します。
    """
    if not isinstance(region, dict):
        return False
    enabled = region.get("enabled", True)
    if enabled is not True:
        return False
    try:
        rid = int(region.get("id", 1))
    except (ValueError, TypeError):
        return False
    return 1 <= rid <= panel_count


def validate_region_spec(spec: dict) -> dict:
    """
    REGION_SPEC の構造を厳格に検査・バリデーションする。
    軽微な座標逸脱はクランプし、壊れた構造や未サポートバージョンは明確な ValueError を送出する。
    将来の拡張フィールド（control, lora, metadata等）は保持します。
    """
    if not isinstance(spec, dict):
        raise ValueError("[TegakiRegionEditor] Invalid REGION_SPEC: Root must be a dictionary.")

    version = spec.get("version")
    if version != SUPPORTED_SCHEMA_VERSION:
        raise ValueError(
            f"[TegakiRegionEditor] Unsupported REGION_SPEC schema version: {version}. "
            f"Expected version {SUPPORTED_SCHEMA_VERSION}."
        )

    canvas = spec.get("canvas")
    if not isinstance(canvas, dict):
        raise ValueError("[TegakiRegionEditor] Invalid REGION_SPEC: 'canvas' must be a dictionary.")
    
    width = int(canvas.get("width", 832))
    height = int(canvas.get("height", 1216))
    if width <= 0 or height <= 0:
        raise ValueError(f"[TegakiRegionEditor] Invalid canvas dimensions: {width}x{height}")
    spec["canvas"]["width"] = width
    spec["canvas"]["height"] = height

    # Global Prompt / Negative Prompt の厳格な型検証
    raw_gp = spec.get("global_prompt", "")
    if raw_gp is not None and not isinstance(raw_gp, str):
        raise ValueError(f"[TegakiRegionEditor] 'global_prompt' must be a string, got {type(raw_gp).__name__}")
    spec["global_prompt"] = raw_gp if raw_gp is not None else ""

    raw_gnp = spec.get("global_negative_prompt", "")
    if raw_gnp is not None and not isinstance(raw_gnp, str):
        raise ValueError(f"[TegakiRegionEditor] 'global_negative_prompt' must be a string, got {type(raw_gnp).__name__}")
    spec["global_negative_prompt"] = raw_gnp if raw_gnp is not None else ""

    panel_count = int(spec.get("panel_count", 3))
    if not (1 <= panel_count <= 6):
        logging.warning(f"[TegakiRegionEditor] panel_count ({panel_count}) out of bounds (1..6). Clamping.")
        panel_count = max(1, min(6, panel_count))
    spec["panel_count"] = panel_count

    regions = spec.get("regions")
    if not isinstance(regions, list):
        raise ValueError("[TegakiRegionEditor] Invalid REGION_SPEC: 'regions' must be a list.")

    seen_ids = set()
    validated_regions = []

    for idx, r in enumerate(regions):
        if not isinstance(r, dict):
            raise ValueError(
                f"[TegakiRegionEditor] Invalid region entry at index {idx}: element in 'regions' "
                f"must be a dictionary, got {type(r).__name__} ({r!r})"
            )
        rid = int(r.get("id", 0))
        if rid < 1 or rid > 6:
            raise ValueError(f"[TegakiRegionEditor] Invalid region id: {rid}. Must be between 1 and 6.")
        if rid in seen_ids:
            raise ValueError(f"[TegakiRegionEditor] Duplicate region id detected: {rid}")
        seen_ids.add(rid)

        # enabled の厳格な型検査 (指示書第14〜15項)
        enabled_val = r.get("enabled", True)
        if not isinstance(enabled_val, bool):
            raise ValueError(
                f"[TegakiRegionEditor] Region id {rid}: 'enabled' must be a strict boolean (True/False), "
                f"got {type(enabled_val).__name__} ({enabled_val!r}). String values like 'false' or '1' are not allowed."
            )
        r["enabled"] = enabled_val

        # 座標の検証と厳密クランプ (Phase 3A 境界値修正)
        x = float(r.get("x", 0.0))
        y = float(r.get("y", 0.0))
        w = float(r.get("w", 0.1))
        h = float(r.get("h", 0.1))

        # x, y は最大 1.0 - MIN_REGION_SIZE まで
        x = max(0.0, min(1.0 - MIN_REGION_SIZE, x))
        y = max(0.0, min(1.0 - MIN_REGION_SIZE, y))

        # w, h は最低 MIN_REGION_SIZE、最大 1.0 - x / 1.0 - y まで
        max_w = max(MIN_REGION_SIZE, 1.0 - x)
        max_h = max(MIN_REGION_SIZE, 1.0 - y)
        w = max(MIN_REGION_SIZE, min(max_w, w))
        h = max(MIN_REGION_SIZE, min(max_h, h))

        if x + w > 1.0:
            w = max(MIN_REGION_SIZE, 1.0 - x)
        if y + h > 1.0:
            h = max(MIN_REGION_SIZE, 1.0 - y)

        r["x"] = round(x, 4)
        r["y"] = round(y, 4)
        r["w"] = round(w, 4)
        r["h"] = round(h, 4)

        raw_p = r.get("prompt", "")
        if raw_p is not None and not isinstance(raw_p, str):
            raise ValueError(f"[TegakiRegionEditor] Region id {rid}: 'prompt' must be a string, got {type(raw_p).__name__}")
        r["prompt"] = raw_p if raw_p is not None else ""

        raw_np = r.get("negative_prompt", "")
        if raw_np is not None and not isinstance(raw_np, str):
            raise ValueError(f"[TegakiRegionEditor] Region id {rid}: 'negative_prompt' must be a string, got {type(raw_np).__name__}")
        r["negative_prompt"] = raw_np if raw_np is not None else ""

        # characters フィールドが存在する場合は list 必須 (指示書第32〜33項)
        if "characters" in r:
            if not isinstance(r["characters"], list):
                raise ValueError(f"[TegakiRegionEditor] Region id {rid}: 'characters' must be a list, got {type(r['characters']).__name__}")

        # local_regions フィールドが存在する場合は list 必須 (Phase 3B.1)
        if "local_regions" in r:
            if not isinstance(r["local_regions"], list):
                raise ValueError(f"[TegakiRegionEditor] Region id {rid}: 'local_regions' must be a list, got {type(r['local_regions']).__name__}")

        # カラーは固定パレットと同期
        color_info = KOMA_COLORS[(rid - 1) % len(KOMA_COLORS)]
        r["color"] = color_info["hex"]
        if "name" not in r:
            r["name"] = color_info["name"]

        validated_regions.append(r)

    # ID順にソート
    validated_regions.sort(key=lambda item: item["id"])
    spec["regions"] = validated_regions

    return spec


def normalize_region_spec(spec: dict, default_w: int = 832, default_h: int = 1216, default_panel_count: int = 3, default_global_prompt: str = "") -> dict:
    """
    不完全なREGION_SPECを完全な6コマ構成に正規化する。
    スキーマ違反がある場合は ValueError を送出する。
    """
    if not isinstance(spec, dict) or "regions" not in spec:
        raise ValueError("[TegakiRegionEditor] Cannot normalize invalid spec: missing 'regions' list.")

    # バリデーション実行 (異常時は ValueError 送出)
    spec = validate_region_spec(spec)

    # 1〜6の全KOMAが存在するか確認し、不足分を補完
    existing_ids = {r["id"] for r in spec["regions"]}
    default_base = default_region_spec(
        spec["canvas"]["width"],
        spec["canvas"]["height"],
        spec["panel_count"],
        spec.get("global_prompt", default_global_prompt)
    )

    for def_r in default_base["regions"]:
        if def_r["id"] not in existing_ids:
            def_r["enabled"] = False
            spec["regions"].append(def_r)

    spec["regions"].sort(key=lambda item: item["id"])
    return spec


def default_region_spec(width=832, height=1216, panel_count=3, global_prompt=""):
    """
    初期状態の REGION_SPEC (v1) を生成する
    """
    default_layouts = [
        {"id": 1, "x": 0.06, "y": 0.05, "w": 0.88, "h": 0.28, "prompt": ""},
        {"id": 2, "x": 0.06, "y": 0.36, "w": 0.42, "h": 0.58, "prompt": ""},
        {"id": 3, "x": 0.52, "y": 0.36, "w": 0.42, "h": 0.58, "prompt": ""},
        {"id": 4, "x": 0.06, "y": 0.05, "w": 0.88, "h": 0.20, "prompt": ""},
        {"id": 5, "x": 0.06, "y": 0.28, "w": 0.88, "h": 0.20, "prompt": ""},
        {"id": 6, "x": 0.06, "y": 0.51, "w": 0.88, "h": 0.43, "prompt": ""},
    ]

    regions = []
    for i in range(6):
        c = KOMA_COLORS[i]
        layout = default_layouts[i]
        regions.append({
            "id": i + 1,
            "name": c["name"],
            "enabled": (i < panel_count),
            "x": layout["x"],
            "y": layout["y"],
            "w": layout["w"],
            "h": layout["h"],
            "prompt": layout["prompt"],
            "color": c["hex"],
        })

    return {
        "version": SUPPORTED_SCHEMA_VERSION,
        "canvas": {
            "width": width,
            "height": height
        },
        "panel_count": panel_count,
        "global_prompt": global_prompt,
        "regions": regions
    }


def render_preview_image(spec: dict, width: int, height: int) -> torch.Tensor:
    """
    REGION_SPEC からプレビュー画像テンソル [1, H, W, 3] を生成する
    """
    img = Image.new("RGBA", (width, height), (250, 248, 245, 255))
    draw = ImageDraw.Draw(img)

    # 外枠ガイド線 (原稿マージン)
    draw.rectangle([10, 10, width - 10, height - 10], outline=(200, 195, 185, 255), width=2)

    regions = spec.get("regions", [])
    panel_count = spec.get("panel_count", len(regions))

    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)

    for r in regions:
        if not is_active_region(r, panel_count):
            continue
        rid = r["id"]

        rx = int(r.get("x", 0.0) * width)
        ry = int(r.get("y", 0.0) * height)
        rw = int(r.get("w", 0.1) * width)
        rh = int(r.get("h", 0.1) * height)

        color_info = KOMA_COLORS[(rid - 1) % len(KOMA_COLORS)]
        rgb = color_info["rgb"]

        # 半透明の塗りつぶし (alpha=75)
        overlay_draw.rectangle([rx, ry, rx + rw, ry + rh], fill=(rgb[0], rgb[1], rgb[2], 75))
        # 太い枠線 (alpha=220)
        overlay_draw.rectangle([rx, ry, rx + rw, ry + rh], outline=(rgb[0], rgb[1], rgb[2], 220), width=4)

        # ラベル描画 (極小Regionではbadge描画を安全にスキップ)
        if rw >= 40 and rh >= 24:
            prompt_snippet = (r.get("prompt", "") or "").strip()
            if prompt_snippet:
                label = f"KOMA {rid}: {prompt_snippet[:24]}..."
            else:
                label = f"KOMA {rid}"

            badge_w = min(rw - 8, max(40, len(label) * 8))
            badge_h = min(rh - 8, 20)
            overlay_draw.rectangle([rx + 4, ry + 4, rx + 4 + badge_w, ry + 4 + badge_h], fill=(rgb[0], rgb[1], rgb[2], 230))
            overlay_draw.text((rx + 8, ry + 6), label, fill=(255, 255, 255, 255))

    img = Image.alpha_composite(img, overlay).convert("RGB")

    arr = np.array(img).astype(np.float32) / 255.0
    tensor = torch.from_numpy(arr).unsqueeze(0)
    return tensor


def render_mask_batch(spec: dict, width: int, height: int):
    """
    有効な各Regionのバイナリマスク [N, H, W] および対応する KOMA ID リストを生成する。
    有効Regionが0件の場合は安全のため [1, H, W] のゼロテンソル（黒マスク）を返します。
    """
    masks = []
    active_ids = []
    regions = spec.get("regions", [])
    panel_count = spec.get("panel_count", len(regions))

    for r in regions:
        if not is_active_region(r, panel_count):
            continue
        rid = r["id"]
        active_ids.append(rid)

        rx = int(r.get("x", 0.0) * width)
        ry = int(r.get("y", 0.0) * height)
        rw = int(r.get("w", 0.1) * width)
        rh = int(r.get("h", 0.1) * height)

        mask_img = Image.new("L", (width, height), 0)
        draw = ImageDraw.Draw(mask_img)
        draw.rectangle([rx, ry, rx + rw, ry + rh], fill=255)

        arr = np.array(mask_img).astype(np.float32) / 255.0
        masks.append(torch.from_numpy(arr))

    if not masks:
        # 有効Regionなし: 安全のため全画面黒マスク（ゼロ）を返す（全画面白ではない）
        empty_mask = torch.zeros((1, height, width), dtype=torch.float32)
        return empty_mask, []

    return torch.stack(masks, dim=0), active_ids


class TegakiMangaRegionEditor:
    """
    Tegaki Manga Region Editor (Phase 2.1.1 安定化・回帰防止版)
    最大6コマの漫画レイアウトを視覚的に編集し、REGION_SPEC およびプレビュー画像を出力するノード。
    REGION_SPEC (v1) を完全な Single Source of Truth とし、UIと生成Backendを疎結合に保ちます。
    """
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "panel_count": ("INT", {"default": 3, "min": 1, "max": 6, "step": 1}),
                "canvas_width": ("INT", {"default": 832, "min": 256, "max": 4096, "step": 64}),
                "canvas_height": ("INT", {"default": 1216, "min": 256, "max": 4096, "step": 64}),
                "global_prompt": ("STRING", {
                    "multiline": True,
                    "dynamicPrompts": True,
                    "default": "manga page, monochrome, highly detailed, ink lineart, cinematic lighting"
                }),
                "region_spec_data": ("STRING", {
                    "multiline": True,
                    "default": "{}"
                }),
            }
        }

    RETURN_TYPES = ("REGION_SPEC", "STRING", "STRING", "IMAGE", "MASK", "STRING")
    RETURN_NAMES = ("region_spec", "region_spec_json", "global_prompt", "preview_image", "mask_batch", "active_region_ids_json")
    FUNCTION = "execute_editor"
    CATEGORY = "tegaki/manga"

    def execute_editor(self, panel_count, canvas_width, canvas_height, global_prompt, region_spec_data="{}"):
        spec = None
        has_valid_json = False

        # 1. 保存されたJSONデータのパースと検証 (Single Source of Truth)
        if region_spec_data and region_spec_data.strip() not in ("{}", ""):
            # A. 構文エラー (Syntax Error) のハンドリング
            try:
                parsed = json.loads(region_spec_data)
            except (json.JSONDecodeError, Exception) as e:
                logging.warning(
                    f"[TegakiRegionEditor] Syntax error in region_spec_data JSON: {e}. "
                    "Falling back to default spec."
                )
                parsed = None

            # B. スキーマエラー (Schema Error) のハンドリング
            # JSONとしてパースできた場合、normalize/validate での例外(ValueError等)は
            # 握りつぶさずにそのまま送出し、Node execution error として停止させる (制作データ保護)
            if parsed is not None:
                if not isinstance(parsed, dict) or "regions" not in parsed:
                    raise ValueError(
                        "[TegakiRegionEditor] Invalid REGION_SPEC: Root must be a dict containing 'regions' list."
                    )
                spec = normalize_region_spec(
                    parsed,
                    default_w=canvas_width,
                    default_h=canvas_height,
                    default_panel_count=panel_count,
                    default_global_prompt=global_prompt
                )
                has_valid_json = True

        # 2. JSONデータが存在しない場合のみ、外側引数から初期REGION_SPECを生成
        if not has_valid_json:
            spec = default_region_spec(canvas_width, canvas_height, panel_count, global_prompt)

        # 3. 実際のキャンバスサイズとGlobal Promptの確定
        actual_width = spec["canvas"]["width"]
        actual_height = spec["canvas"]["height"]
        actual_global_prompt = spec.get("global_prompt", global_prompt)

        # Region Prompt内の <lora:...> をチェック（Phase 2注意喚起: 指示書第24項）
        for r in spec.get("regions", []):
            if is_active_region(r, spec["panel_count"]):
                p = r.get("prompt", "")
                if "<lora:" in p.lower():
                    logging.warning(
                        f"[TegakiRegionEditor] Notice: KOMA {r.get('id')} prompt contains '<lora:...>'. "
                        "Region-local LoRA is planned for Phase 5 (RLL). Currently LoRA affects the entire model."
                    )

        spec_json = json.dumps(spec, indent=2, ensure_ascii=False)
        preview_img = render_preview_image(spec, actual_width, actual_height)
        mask_batch, active_ids = render_mask_batch(spec, actual_width, actual_height)
        active_ids_json = json.dumps(active_ids)

        return (spec, spec_json, actual_global_prompt, preview_img, mask_batch, active_ids_json)
