"""
Tegaki Manga Layout Region Bridge (Phase 3D)
=============================================
PANEL_LAYOUT_SPEC (コマ割り幾何・Planar Subdivision) と
PAGE_COMPILE_PLAN (意味シーン計画・Prompt / Character / Local Region) を
安全に結合する純粋関数ブリッジモジュール。

- コマ数整合性 (Active KOMA == Layout Panels, 1〜6) の Fail-Closed 検証
- 決定論的安定マッピング (Active KOMA ID昇順 <-> Layout Panel保存順)
- Panel多角形のBounding Box計算と、KOMAローカル矩形のBBox相対投影
- 人物A/Bの同一コマ内Semantic Overlap (重なり) 完全許容
"""

import json
import logging
from typing import Dict, Any, List, Optional, Tuple

from .panel_layout_spec import validate_panel_layout_spec
from .scene_spec import validate_page_compile_plan


def build_panel_content_bridge(
    page_compile_plan: Any,
    panel_layout_spec: Any,
    context_name: str = "LayoutRegionBridge"
) -> Dict[str, Any]:
    """
    PAGE_COMPILE_PLAN と PANEL_LAYOUT_SPEC を結合・投影し、
    多角形マスクおよび階層的 Conditioning 生成に必要なマッピング構造を生成する。
    """
    plan = validate_page_compile_plan(page_compile_plan)
    layout = validate_panel_layout_spec(panel_layout_spec, context_name=f"{context_name}.panel_layout")

    canvas = plan["canvas"]
    width = int(canvas["width"])
    height = int(canvas["height"])

    # 1. Active KOMA の収集とソート (ID昇順)
    raw_panels = plan.get("panels", [])
    active_komas = []
    for p in raw_panels:
        # 有効コマ判定 (enabled 未指定または True)
        if p.get("enabled", True) is not False:
            active_komas.append(p)

    def _koma_sort_key(p):
        pid = str(p.get("target_panel_id", "0"))
        return int(pid) if pid.isdigit() else pid

    active_komas.sort(key=_koma_sort_key)
    active_koma_count = len(active_komas)

    # 2. Layout Panels の収集 (保存順を厳格に維持)
    layout_panels = layout.get("panels", [])
    layout_panel_count = len(layout_panels)

    # 3. コマ数制約 & 一致検証 (Fail-Closed)
    if active_koma_count < 1 or active_koma_count > 6:
        raise ValueError(f"[{context_name}] Active KOMA count must be between 1 and 6, got {active_koma_count}")
    if layout_panel_count < 1 or layout_panel_count > 6:
        raise ValueError(f"[{context_name}] Layout panel count must be between 1 and 6, got {layout_panel_count}")

    if active_koma_count != layout_panel_count:
        raise ValueError(
            f"[{context_name}] Panel count mismatch: active KOMA count ({active_koma_count}) "
            f"does not match layout panel count ({layout_panel_count}). "
            f"Content and layout must have matching panel counts."
        )

    # 4. 頂点座標マップの構築
    vertex_map = {v["id"]: (float(v["x"]), float(v["y"])) for v in layout.get("vertices", [])}

    # 5. 安定マッピング & 各Panelの幾何・BBox計算
    panel_content_map = {}
    mapped_panels = []
    all_char_entries = []
    all_lr_entries = []

    for idx in range(active_koma_count):
        koma = active_komas[idx]
        lpanel = layout_panels[idx]

        koma_id = str(koma.get("target_panel_id", idx + 1))
        panel_id = lpanel.get("id", f"p{idx + 1}")
        panel_content_map[koma_id] = panel_id

        # 多角形頂点 (正規化 & ピクセル)
        v_ids = lpanel.get("vertex_ids", [])
        norm_pts = [vertex_map[vid] for vid in v_ids if vid in vertex_map]
        if len(norm_pts) < 3:
            raise ValueError(f"[{context_name}] Layout panel '{panel_id}' has fewer than 3 valid vertices: {v_ids}")

        pixel_pts = [(int(round(x * width)), int(round(y * height))) for x, y in norm_pts]

        # Bounding Box 計算
        min_x = min(x for x, y in norm_pts)
        max_x = max(x for x, y in norm_pts)
        min_y = min(y for x, y in norm_pts)
        max_y = max(y for x, y in norm_pts)
        bbox_w = max_x - min_x
        bbox_h = max_y - min_y

        px0 = max(0, min(width, int(round(min_x * width))))
        py0 = max(0, min(height, int(round(min_y * height))))
        px1 = max(0, min(width, int(round(max_x * width))))
        py1 = max(0, min(height, int(round(max_y * height))))

        panel_info = {
            "index": idx,
            "koma_id": koma_id,
            "layout_panel_id": panel_id,
            "polygon_norm": norm_pts,
            "polygon_pixels": pixel_pts,
            "bbox_norm": {
                "x": round(min_x, 4),
                "y": round(min_y, 4),
                "w": round(bbox_w, 4),
                "h": round(bbox_h, 4)
            },
            "bbox_pixels": [px0, py0, px1, py1],
            "koma": koma
        }
        mapped_panels.append(panel_info)

        # 6. Character の BBox 相対投影
        for c in koma.get("characters", []):
            cid = c.get("character_id")
            cname = c.get("name", cid)
            area = c.get("area")

            if area is None:
                cx, cy, cw, ch = 0.0, 0.0, 1.0, 1.0
                is_unconstrained = True
            else:
                cx, cy, cw, ch = float(area["x"]), float(area["y"]), float(area["w"]), float(area["h"])
                is_unconstrained = False

            # Panel polygon bbox に対する相対投影
            proj_x = min_x + bbox_w * cx
            proj_y = min_y + bbox_h * cy
            proj_w = bbox_w * cw
            proj_h = bbox_h * ch

            c_px0 = max(0, min(width, int(round(proj_x * width))))
            c_py0 = max(0, min(height, int(round(proj_y * height))))
            c_px1 = max(0, min(width, int(round((proj_x + proj_w) * width))))
            c_py1 = max(0, min(height, int(round((proj_y + proj_h) * height))))

            char_entry = {
                "character_index": len(all_char_entries),
                "panel_index": idx,
                "koma_id": koma_id,
                "layout_panel_id": panel_id,
                "character_id": cid,
                "character_name": cname,
                "clean_prompt": c.get("combined_prompt") or c.get("clean_prompt", ""),
                "clean_negative_prompt": c.get("combined_negative_prompt") or c.get("clean_negative_prompt", ""),
                "is_unconstrained": is_unconstrained,
                "koma_local_area": {"x": cx, "y": cy, "w": cw, "h": ch} if not is_unconstrained else None,
                "page_projected_area": {
                    "x": round(proj_x, 4),
                    "y": round(proj_y, 4),
                    "w": round(proj_w, 4),
                    "h": round(proj_h, 4)
                },
                "pixel_bounds": [c_px0, c_py0, c_px1, c_py1],
                "panel_polygon_pixels": pixel_pts
            }
            all_char_entries.append(char_entry)

        # 7. Local Region の BBox 相対投影
        for lr in koma.get("panel", {}).get("local_regions", []):
            lid = lr.get("id")
            lname = lr.get("name", lid)
            area = lr["area"]
            lx, ly, lw, lh = float(area["x"]), float(area["y"]), float(area["w"]), float(area["h"])

            lr_proj_x = min_x + bbox_w * lx
            lr_proj_y = min_y + bbox_h * ly
            lr_proj_w = bbox_w * lw
            lr_proj_h = bbox_h * lh

            lr_px0 = max(0, min(width, int(round(lr_proj_x * width))))
            lr_py0 = max(0, min(height, int(round(lr_proj_y * height))))
            lr_px1 = max(0, min(width, int(round((lr_proj_x + lr_proj_w) * width))))
            lr_py1 = max(0, min(height, int(round((lr_proj_y + lr_proj_h) * height))))

            lr_entry = {
                "local_region_index": len(all_lr_entries),
                "panel_index": idx,
                "koma_id": koma_id,
                "layout_panel_id": panel_id,
                "id": lid,
                "name": lname,
                "prompt": lr.get("prompt", ""),
                "negative_prompt": lr.get("negative_prompt", ""),
                "weight": float(lr.get("weight", 1.0)),
                "koma_local_area": {"x": lx, "y": ly, "w": lw, "h": lh},
                "page_projected_area": {
                    "x": round(lr_proj_x, 4),
                    "y": round(lr_proj_y, 4),
                    "w": round(lr_proj_w, 4),
                    "h": round(lr_proj_h, 4)
                },
                "pixel_bounds": [lr_px0, lr_py0, lr_px1, lr_py1],
                "panel_polygon_pixels": pixel_pts
            }
            all_lr_entries.append(lr_entry)

    return {
        "canvas": {"width": width, "height": height},
        "active_koma_count": active_koma_count,
        "layout_panel_count": layout_panel_count,
        "panel_content_map": panel_content_map,
        "mapped_panels": mapped_panels,
        "characters": all_char_entries,
        "local_regions": all_lr_entries,
        "debug_summary": {
            "mode": "layout_driven",
            "active_komas": [p["koma_id"] for p in mapped_panels],
            "layout_panels": [p["layout_panel_id"] for p in mapped_panels],
            "mapping": panel_content_map,
            "character_count": len(all_char_entries),
            "local_region_count": len(all_lr_entries),
        }
    }
