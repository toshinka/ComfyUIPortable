import copy
import json
import math
from typing import Dict, Any, List, Optional, Tuple


def get_default_two_region_spec(width: int = 832, height: int = 1216) -> Dict[str, Any]:
    """
    既定の TWO_REGION_SPEC (v1) を生成する。
    左右 2 分割 (Horizontal Split) を初期状態とする。
    """
    return {
        "version": 1,
        "canvas": {
            "width": int(width),
            "height": int(height)
        },
        "global_prompt": "",
        "global_negative_prompt": "",
        "regions": [
            {
                "id": "A",
                "enabled": True,
                "prompt": "1girl, blonde hair",
                "negative_prompt": "",
                "x": 0.05,
                "y": 0.10,
                "w": 0.42,
                "h": 0.80
            },
            {
                "id": "B",
                "enabled": True,
                "prompt": "1boy, black hair",
                "negative_prompt": "",
                "x": 0.53,
                "y": 0.10,
                "w": 0.42,
                "h": 0.80
            }
        ],
        "metadata": {}
    }


def validate_two_region_spec(spec_data: Any, context_name: str = "TWO_REGION_SPEC") -> Dict[str, Any]:
    """
    TWO_REGION_SPEC (v1) のデータ構造を厳格に検証・正規化する。
    """
    if spec_data is None:
        raise ValueError(f"[{context_name}] Spec cannot be None.")

    if isinstance(spec_data, str):
        try:
            spec_data = json.loads(spec_data)
        except json.JSONDecodeError as e:
            raise ValueError(f"[{context_name}] Invalid JSON string: {e}")

    if not isinstance(spec_data, dict):
        raise ValueError(f"[{context_name}] Root element must be a dictionary, got {type(spec_data).__name__}")

    # 1. Version validation
    version = spec_data.get("version")
    if version != 1:
        raise ValueError(f"[{context_name}] Unsupported schema version: {version}. Expected version 1.")

    # 2. Canvas validation
    canvas = spec_data.get("canvas")
    if not isinstance(canvas, dict):
        raise ValueError(f"[{context_name}] 'canvas' must be a dictionary.")

    width = canvas.get("width")
    height = canvas.get("height")
    if not isinstance(width, int) or isinstance(width, bool) or width <= 0 or width > 8192:
        raise ValueError(f"[{context_name}] 'canvas.width' must be an integer between 1 and 8192, got {width!r}")
    if not isinstance(height, int) or isinstance(height, bool) or height <= 0 or height > 8192:
        raise ValueError(f"[{context_name}] 'canvas.height' must be an integer between 1 and 8192, got {height!r}")

    # 3. Global prompts validation
    global_prompt = spec_data.get("global_prompt", "")
    global_neg_prompt = spec_data.get("global_negative_prompt", "")
    if not isinstance(global_prompt, str):
        raise ValueError(f"[{context_name}] 'global_prompt' must be a string, got {type(global_prompt).__name__}")
    if not isinstance(global_neg_prompt, str):
        raise ValueError(f"[{context_name}] 'global_negative_prompt' must be a string, got {type(global_neg_prompt).__name__}")

    # 4. Regions validation
    regions = spec_data.get("regions")
    if not isinstance(regions, list):
        raise ValueError(f"[{context_name}] 'regions' must be a list.")

    if len(regions) < 1:
        raise ValueError(f"[{context_name}] 'regions' must contain at least 1 region entry.")

    seen_ids = set()
    validated_regions = []

    for idx, reg in enumerate(regions):
        reg_ctx = f"{context_name}.regions[{idx}]"
        if not isinstance(reg, dict):
            raise ValueError(f"[{reg_ctx}] Region entry must be a dictionary, got {type(reg).__name__}")

        # ID validation
        reg_id = reg.get("id")
        if not isinstance(reg_id, str) or not reg_id.strip():
            raise ValueError(f"[{reg_ctx}] 'id' must be a non-empty string, got {reg_id!r}")
        if reg_id in seen_ids:
            raise ValueError(f"[{reg_ctx}] Duplicate region id: '{reg_id}'")
        seen_ids.add(reg_id)

        # Enabled validation (strict bool)
        enabled = reg.get("enabled", True)
        if not isinstance(enabled, bool):
            raise ValueError(f"[{reg_ctx}] 'enabled' must be a strict boolean (True/False), got {type(enabled).__name__} ({enabled!r})")

        # Prompt validation
        prompt = reg.get("prompt", "")
        neg_prompt = reg.get("negative_prompt", "")
        if not isinstance(prompt, str):
            raise ValueError(f"[{reg_ctx}] 'prompt' must be a string, got {type(prompt).__name__}")
        if not isinstance(neg_prompt, str):
            raise ValueError(f"[{reg_ctx}] 'negative_prompt' must be a string, got {type(neg_prompt).__name__}")

        # Geometry validation (x, y, w, h in normalized [0, 1])
        for coord_name in ("x", "y", "w", "h"):
            val = reg.get(coord_name)
            if val is None or isinstance(val, bool) or not isinstance(val, (int, float)):
                raise ValueError(f"[{reg_ctx}] '{coord_name}' must be numeric, got {val!r}")
            if not math.isfinite(float(val)):
                raise ValueError(f"[{reg_ctx}] '{coord_name}' must be a finite number, got {val!r}")

        x = float(reg["x"])
        y = float(reg["y"])
        w = float(reg["w"])
        h = float(reg["h"])

        if w <= 0.0 or h <= 0.0:
            raise ValueError(f"[{reg_ctx}] Width ('w') and height ('h') must be > 0, got w={w}, h={h}")

        # Normalization clamp [0, 1]
        x = max(0.0, min(1.0, x))
        y = max(0.0, min(1.0, y))
        w = max(0.001, min(1.0 - x, w))
        h = max(0.001, min(1.0 - y, h))

        norm_reg = copy.deepcopy(reg)
        norm_reg["id"] = reg_id
        norm_reg["enabled"] = enabled
        norm_reg["prompt"] = prompt
        norm_reg["negative_prompt"] = neg_prompt
        norm_reg["x"] = round(x, 4)
        norm_reg["y"] = round(y, 4)
        norm_reg["w"] = round(w, 4)
        norm_reg["h"] = round(h, 4)
        validated_regions.append(norm_reg)

    validated_spec = copy.deepcopy(spec_data)
    validated_spec["version"] = 1
    validated_spec["canvas"] = {"width": width, "height": height}
    validated_spec["global_prompt"] = global_prompt
    validated_spec["global_negative_prompt"] = global_neg_prompt
    validated_spec["regions"] = validated_regions
    if "metadata" not in validated_spec or not isinstance(validated_spec["metadata"], dict):
        validated_spec["metadata"] = {}

    return validated_spec
