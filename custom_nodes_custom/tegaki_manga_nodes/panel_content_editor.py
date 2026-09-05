"""
Tegaki Manga Panel Content Editor (Phase 3F)
============================================
JSON-backed progressive panel content authoring node.
Provides single-panel focused editing:
- panel_count (1..6, default 4)
- selected_panel (P1..P6)
- scene_prompt / scene_negative
- character attendance & acting prompt overrides
- optional SubScene v1 progressive disclosure (+ Split Scene)
Outputs standard REGION_SPEC compatible with TegakiMangaPageCompiler.
"""

import json
import logging
from typing import Dict, Any, List, Optional, Tuple

from .region_editor import SUPPORTED_SCHEMA_VERSION, validate_region_spec
from .subscene_contract import validate_panel_subscenes, has_active_subscenes


DEFAULT_RECURRENT_PANELS_CONTENT: Dict[str, Any] = {
    "version": SUPPORTED_SCHEMA_VERSION,
    "canvas": {"width": 1024, "height": 1024},
    "panel_count": 4,
    "global_prompt": "manga page, 4-panel comic, sequence of events, high quality",
    "global_negative_prompt": "blurry, low quality, bad anatomy",
    "panels": [
        {
            "id": 1,
            "name": "Panel 1",
            "enabled": True,
            "prompt": "simple school garden, sunny afternoon, outdoor stone path",
            "negative_prompt": "blurry",
            "characters": [
                {
                    "character_id": "char_alice",
                    "enabled": True,
                    "prompt_override": "smiling happily, friendly handshake, reaching hand forward",
                    "negative_prompt_override": "",
                    "area": {"x": 0.08, "y": 0.15, "w": 0.45, "h": 0.8}
                },
                {
                    "character_id": "char_bob",
                    "enabled": True,
                    "prompt_override": "smiling warmly, friendly handshake, shaking hands",
                    "negative_prompt_override": "",
                    "area": {"x": 0.47, "y": 0.15, "w": 0.45, "h": 0.8}
                }
            ],
            "subscenes": []
        },
        {
            "id": 2,
            "name": "Panel 2",
            "enabled": True,
            "prompt": "school flower bed, colorful blooming flowers, soil, sunny morning",
            "negative_prompt": "blurry",
            "characters": [
                {
                    "character_id": "char_alice",
                    "enabled": True,
                    "prompt_override": "watering flowers with a watering can, cheerful expression",
                    "negative_prompt_override": "",
                    "area": {"x": 0.15, "y": 0.12, "w": 0.7, "h": 0.82}
                }
            ],
            "subscenes": []
        },
        {
            "id": 3,
            "name": "Panel 3",
            "enabled": True,
            "prompt": "school garden stone path, trees in background",
            "negative_prompt": "blurry",
            "characters": [
                {
                    "character_id": "char_bob",
                    "enabled": True,
                    "prompt_override": "carrying a large potted green plant with both hands, focused expression",
                    "negative_prompt_override": "",
                    "area": {"x": 0.15, "y": 0.12, "w": 0.7, "h": 0.82}
                }
            ],
            "subscenes": []
        },
        {
            "id": 4,
            "name": "Panel 4",
            "enabled": True,
            "prompt": "school iron gate in sunset, dramatic evening light, long shadows",
            "negative_prompt": "blurry",
            "characters": [
                {
                    "character_id": "char_alice",
                    "enabled": True,
                    "prompt_override": "arguing, angry pout, looking away to the left with arms crossed",
                    "negative_prompt_override": "",
                    "area": {"x": 0.08, "y": 0.15, "w": 0.45, "h": 0.8}
                },
                {
                    "character_id": "char_bob",
                    "enabled": True,
                    "prompt_override": "arguing, annoyed expression, looking away to the right",
                    "negative_prompt_override": "",
                    "area": {"x": 0.47, "y": 0.15, "w": 0.45, "h": 0.8}
                }
            ],
            "subscenes": []
        }
    ]
}


def build_default_panel_content(panel_count: int = 4) -> Dict[str, Any]:
    """Generates default panel content structure for panel_count (1..6)."""
    base = json.loads(json.dumps(DEFAULT_RECURRENT_PANELS_CONTENT))
    base["panel_count"] = max(1, min(6, int(panel_count)))
    # Ensure panels up to panel_count exist
    existing = {p["id"]: p for p in base["panels"]}
    panels = []
    for i in range(1, base["panel_count"] + 1):
        if i in existing:
            panels.append(existing[i])
        else:
            panels.append({
                "id": i,
                "name": f"Panel {i}",
                "enabled": True,
                "prompt": f"manga scene background for panel {i}",
                "negative_prompt": "blurry",
                "characters": [],
                "subscenes": []
            })
    base["panels"] = panels
    return base


class TegakiMangaPanelContentEditor:
    """
    Tegaki Manga Panel Content Editor (Phase 3F)
    ===========================================
    Interactive progressive authoring node for manga panel scenes, character
    attendance, acting prompts, and optional SubScene v1 splitting.
    """
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "panel_content_data": ("STRING", {
                    "multiline": True,
                    "default": json.dumps(DEFAULT_RECURRENT_PANELS_CONTENT, indent=2, ensure_ascii=False)
                }),
            },
            "optional": {
                "cast_spec": ("CAST_SPEC",),
            }
        }

    RETURN_TYPES = ("REGION_SPEC", "STRING", "INT")
    RETURN_NAMES = ("region_spec", "content_data_json", "panel_count")
    FUNCTION = "process"
    CATEGORY = "tegaki/manga"

    def process(self, panel_content_data: str, cast_spec: Optional[Dict[str, Any]] = None):
        trimmed = panel_content_data.strip() if panel_content_data else ""
        if not trimmed or trimmed == "{}":
            spec_dict = build_default_panel_content(4)
        else:
            try:
                parsed = json.loads(trimmed)
                if not isinstance(parsed, dict) or "panels" not in parsed:
                    spec_dict = build_default_panel_content(4)
                else:
                    spec_dict = parsed
            except Exception as e:
                logging.warning(f"[PanelContentEditor] Parse failed, falling back to default: {e}")
                spec_dict = build_default_panel_content(4)

        panel_count = int(spec_dict.get("panel_count", len(spec_dict.get("panels", []))))
        panel_count = max(1, min(6, panel_count))
        spec_dict["panel_count"] = panel_count

        # Convert panels into REGION_SPEC regions format for seamless bridge compatibility
        regions = []
        panels = spec_dict.get("panels", [])
        for p in panels[:panel_count]:
            pid = int(p.get("id", len(regions) + 1))
            cam_dist = p.get("camera_distance") or (p.get("metadata", {}).get("camera_distance") if isinstance(p.get("metadata"), dict) else None) or "medium"
            koma_meta = dict(p.get("metadata", {})) if isinstance(p.get("metadata"), dict) else {}
            koma_meta["camera_distance"] = cam_dist

            koma_entry = {
                "id": pid,
                "name": p.get("name", f"Panel {pid}"),
                "enabled": bool(p.get("enabled", True)),
                "x": 0.05,
                "y": 0.05,
                "w": 0.9,
                "h": 0.9,
                "prompt": p.get("prompt", ""),
                "negative_prompt": p.get("negative_prompt", ""),
                "characters": p.get("characters", []),
                "subscenes": p.get("subscenes", []),
                "camera_distance": cam_dist,
                "metadata": koma_meta
            }
            regions.append(koma_entry)

        region_spec = {
            "version": SUPPORTED_SCHEMA_VERSION,
            "canvas": spec_dict.get("canvas", {"width": 1024, "height": 1024}),
            "panel_count": panel_count,
            "global_prompt": spec_dict.get("global_prompt", ""),
            "global_negative_prompt": spec_dict.get("global_negative_prompt", ""),
            "regions": regions
        }

        # Validate through existing REGION_SPEC contract
        valid_region_spec = validate_region_spec(region_spec)
        content_json = json.dumps(spec_dict, indent=2, ensure_ascii=False)

        return (valid_region_spec, content_json, panel_count)
