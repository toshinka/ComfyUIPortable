"""
Tegaki Manga Character Staging Editor (Phase 3F)
================================================
Visual character staging and placement node.
Accepts REGION_SPEC and PANEL_LAYOUT_SPEC.
Provides:
- Current panel selection (P1..P6)
- Display of attending characters for selected panel
- Interactive coordinate move / resize support
- Real-time staging preview image generation
- Pass-through of updated REGION_SPEC
"""

import json
import logging
from typing import Dict, Any, List, Optional, Tuple

import torch
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from .region_editor import validate_region_spec
from .panel_layout_spec import validate_panel_layout_spec


CHAR_PALETTE = {
    "char_alice": {"fill": (234, 88, 12, 110), "stroke": (234, 88, 12, 255), "name": "Alice"},
    "char_bob": {"fill": (30, 136, 229, 110), "stroke": (30, 136, 229, 255), "name": "Bob"},
    "default": {"fill": (22, 163, 74, 110), "stroke": (22, 163, 74, 255), "name": "Character"}
}


def render_staging_preview_image(
    region_spec: Dict[str, Any],
    panel_layout_spec: Dict[str, Any]
) -> torch.Tensor:
    """
    Renders a crisp, readable visual preview of panels and character staging boxes.
    Returns [1, H, W, 3] float32 torch tensor.
    """
    canvas = region_spec.get("canvas", {"width": 1024, "height": 1024})
    width = int(canvas.get("width", 1024))
    height = int(canvas.get("height", 1024))

    img = Image.new("RGB", (width, height), (252, 250, 242)) # Soft futaba paper
    draw = ImageDraw.Draw(img, "RGBA")

    # 1. Draw Panel Layout Polygons
    vertices = {v["id"]: (float(v["x"]) * width, float(v["y"]) * height) for v in panel_layout_spec.get("vertices", [])}
    panels = panel_layout_spec.get("panels", [])

    for p_idx, p in enumerate(panels):
        v_ids = p.get("vertex_ids", [])
        pts = [vertices[vid] for vid in v_ids if vid in vertices]
        if len(pts) >= 3:
            # Subtle panel fill
            draw.polygon(pts, fill=(245, 240, 230, 180), outline=(60, 50, 40, 255), width=3)
            # Panel label
            cx = sum(pt[0] for pt in pts) / len(pts)
            cy = min(pt[1] for pt in pts) + 15
            draw.text((cx - 15, cy), f"P{p_idx + 1}", fill=(80, 70, 60, 200))

    # 2. Draw Character Staging Boxes
    regions = region_spec.get("regions", [])
    panel_count = int(region_spec.get("panel_count", len(panels)))

    for p_idx, r in enumerate(regions[:panel_count]):
        if not r.get("enabled", True):
            continue
        if p_idx >= len(panels):
            continue

        p = panels[p_idx]
        v_ids = p.get("vertex_ids", [])
        pts = [vertices[vid] for vid in v_ids if vid in vertices]
        if not pts:
            continue

        p_min_x = min(pt[0] for pt in pts)
        p_min_y = min(pt[1] for pt in pts)
        p_max_x = max(pt[0] for pt in pts)
        p_max_y = max(pt[1] for pt in pts)
        p_w = p_max_x - p_min_x
        p_h = p_max_y - p_min_y

        chars = r.get("characters", [])
        for c in chars:
            if not c.get("enabled", True):
                continue
            cid = c.get("character_id", "")
            cfg = CHAR_PALETTE.get(cid, CHAR_PALETTE["default"])
            area = c.get("area") or {"x": 0.1, "y": 0.15, "w": 0.4, "h": 0.8}

            cx0 = p_min_x + area["x"] * p_w
            cy0 = p_min_y + area["y"] * p_h
            cx1 = cx0 + area["w"] * p_w
            cy1 = cy0 + area["h"] * p_h

            draw.rectangle([cx0, cy0, cx1, cy1], fill=cfg["fill"], outline=cfg["stroke"], width=2)
            # Name badge
            label = cfg["name"]
            draw.rectangle([cx0, cy0, cx0 + len(label) * 8 + 12, cy0 + 16], fill=cfg["stroke"])
            draw.text((cx0 + 4, cy0 + 2), label, fill=(255, 255, 255, 255))

    arr = np.array(img, dtype=np.float32) / 255.0
    tensor = torch.from_numpy(arr).unsqueeze(0)
    return tensor


def _normalize_box_area(val: Any, default_area: Optional[Dict[str, float]] = None) -> Dict[str, float]:
    if isinstance(val, (list, tuple)) and len(val) >= 4:
        return {
            "x": round(float(val[0]), 3),
            "y": round(float(val[1]), 3),
            "w": round(float(val[2]), 3),
            "h": round(float(val[3]), 3)
        }
    if isinstance(val, dict):
        return {
            "x": round(float(val.get("x", 0.1)), 3),
            "y": round(float(val.get("y", 0.15)), 3),
            "w": round(float(val.get("w", 0.4)), 3),
            "h": round(float(val.get("h", 0.75)), 3)
        }
    if default_area is not None:
        return _normalize_box_area(default_area)
    return {"x": 0.1, "y": 0.15, "w": 0.4, "h": 0.75}


class CharacterStagingStateManager:
    """
    State manager for character staging overrides and live manipulation.
    """
    def __init__(self, region_spec: Dict[str, Any], overrides: Optional[Dict[str, Any]] = None):
        self.region_spec = region_spec
        self.overrides = overrides or {}
        self.selected_panel_id: int = 1
        self.selected_char_id: Optional[str] = None

        attending = self.get_attending_characters(1)
        if attending:
            self.selected_char_id = attending[0]["character_id"]

    def select_panel(self, panel_id: int):
        self.selected_panel_id = int(panel_id)
        attending = self.get_attending_characters(self.selected_panel_id)
        if self.selected_char_id not in [c["character_id"] for c in attending]:
            self.selected_char_id = attending[0]["character_id"] if attending else None

    def get_attending_characters(self, panel_id: int) -> List[Dict[str, Any]]:
        for r in self.region_spec.get("regions", []):
            if int(r.get("id", 0)) == int(panel_id):
                chars = []
                for c in r.get("characters", []):
                    if c.get("enabled", True):
                        cid = c.get("character_id")
                        area = self.get_character_area(panel_id, cid, c.get("area"))
                        chars.append({
                            "character_id": cid,
                            "area": area,
                            "enabled": True
                        })
                return chars
        return []

    def get_character_area(self, panel_id: int, char_id: str, default_area: Optional[Dict[str, float]] = None) -> Dict[str, float]:
        pid_str = str(panel_id)
        if pid_str in self.overrides and char_id in self.overrides[pid_str]:
            raw = self.overrides[pid_str][char_id].get("area")
            return _normalize_box_area(raw, default_area)
        if default_area:
            return _normalize_box_area(default_area)
        return {"x": 0.1, "y": 0.15, "w": 0.4, "h": 0.75}

    def select_character(self, char_id: str):
        attending = [c["character_id"] for c in self.get_attending_characters(self.selected_panel_id)]
        if char_id not in attending:
            raise ValueError(f"Character {char_id!r} is not attending Panel {self.selected_panel_id}")
        self.selected_char_id = char_id

    def move_character(self, panel_id: int, char_id: str, dx: float, dy: float) -> Dict[str, float]:
        attending = [c["character_id"] for c in self.get_attending_characters(panel_id)]
        if char_id not in attending:
            raise ValueError(f"Cannot move non-attending character {char_id!r} in Panel {panel_id}")
        curr = self.get_character_area(panel_id, char_id)
        new_x = max(0.0, min(1.0 - curr["w"], curr["x"] + dx))
        new_y = max(0.0, min(1.0 - curr["h"], curr["y"] + dy))
        area = {
            "x": round(new_x, 3),
            "y": round(new_y, 3),
            "w": round(curr["w"], 3),
            "h": round(curr["h"], 3)
        }
        self._commit_override(panel_id, char_id, area)
        return area

    def resize_character(self, panel_id: int, char_id: str, dw: float, dh: float, min_size: float = 0.05) -> Dict[str, float]:
        attending = [c["character_id"] for c in self.get_attending_characters(panel_id)]
        if char_id not in attending:
            raise ValueError(f"Cannot resize non-attending character {char_id!r} in Panel {panel_id}")
        curr = self.get_character_area(panel_id, char_id)
        new_w = max(min_size, min(1.0 - curr["x"], curr["w"] + dw))
        new_h = max(min_size, min(1.0 - curr["y"], curr["h"] + dh))
        area = {
            "x": round(curr["x"], 3),
            "y": round(curr["y"], 3),
            "w": round(new_w, 3),
            "h": round(new_h, 3)
        }
        self._commit_override(panel_id, char_id, area)
        return area

    def _commit_override(self, panel_id: int, char_id: str, area: Dict[str, float]):
        pid_str = str(panel_id)
        if pid_str not in self.overrides:
            self.overrides[pid_str] = {}
        self.overrides[pid_str][char_id] = {"area": area}

    def reset_overrides(self):
        self.overrides = {}

    def serialize_overrides(self) -> str:
        return json.dumps(self.overrides, indent=2, ensure_ascii=False)

    def apply_to_region_spec(self) -> Dict[str, Any]:
        copied = json.loads(json.dumps(self.region_spec))
        for r in copied.get("regions", []):
            pid = str(r.get("id"))
            if pid in self.overrides:
                p_ov = self.overrides[pid]
                for c in r.get("characters", []):
                    cid = c.get("character_id")
                    if cid in p_ov and "area" in p_ov[cid]:
                        c["area"] = _normalize_box_area(p_ov[cid]["area"])
        return copied


class TegakiMangaCharacterStagingEditor:
    """
    Tegaki Manga Character Staging Editor (Phase 3F / 3G)
    ===================================================
    Visual layout & character staging editor with real-time canvas preview.
    """
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "region_spec": ("REGION_SPEC",),
                "panel_layout_spec": ("PANEL_LAYOUT_SPEC",),
            },
            "optional": {
                "staging_overrides": ("STRING", {
                    "multiline": True,
                    "default": "{}"
                }),
            }
        }

    RETURN_TYPES = ("REGION_SPEC", "IMAGE", "STRING")
    RETURN_NAMES = ("region_spec", "staging_preview", "staging_json")
    FUNCTION = "process"
    CATEGORY = "tegaki/manga"

    def process(
        self,
        region_spec: Dict[str, Any],
        panel_layout_spec: Dict[str, Any],
        staging_overrides: str = "{}"
    ):
        v_region_spec = validate_region_spec(region_spec)
        v_layout_spec = validate_panel_layout_spec(panel_layout_spec, context_name="StagingEditor")

        # Parse overrides and apply via CharacterStagingStateManager
        overrides_dict = {}
        trimmed = staging_overrides.strip() if staging_overrides else "{}"
        if trimmed and trimmed != "{}":
            try:
                parsed = json.loads(trimmed)
                if isinstance(parsed, dict):
                    overrides_dict = parsed
            except Exception as e:
                logging.warning(f"[CharacterStagingEditor] Could not parse staging_overrides: {e}")

        mgr = CharacterStagingStateManager(v_region_spec, overrides_dict)
        updated_region_spec = mgr.apply_to_region_spec()

        # Render preview image
        preview_tensor = render_staging_preview_image(updated_region_spec, v_layout_spec)
        staging_json = json.dumps(updated_region_spec, indent=2, ensure_ascii=False)

        return (updated_region_spec, preview_tensor, staging_json)

