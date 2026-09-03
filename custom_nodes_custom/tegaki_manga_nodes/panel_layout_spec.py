import copy
import json
import math
from typing import Dict, Any, List, Optional, Tuple

from .panel_layout_topology import (
    signed_area,
    normalize_winding_ccw,
    validate_layout_topology,
    MIN_PANEL_AREA,
    MAX_PANELS
)

# Backward-compatibility alias
polygon_signed_area = signed_area


def get_default_panel_layout_spec(width: int = 832, height: int = 1216, preset: str = "3_basic") -> Dict[str, Any]:
    """
    既定の PANEL_LAYOUT_SPEC (v1) を生成する。
    Planar Subdivision (平面分割) 契約に基づき、明示的 Layout Frame と
    T-Junction のない完全な共有頂点メッシュを提供する。
    """
    W = int(width)
    H = int(height)
    frame = {"x": 0.05, "y": 0.05, "w": 0.90, "h": 0.90}

    if preset == "1_full":
        # 1 コマ全画面
        vertices = [
            {"id": "v1", "x": 0.05, "y": 0.05},
            {"id": "v2", "x": 0.95, "y": 0.05},
            {"id": "v3", "x": 0.95, "y": 0.95},
            {"id": "v4", "x": 0.05, "y": 0.95},
        ]
        panels = [
            {"id": "p1", "vertex_ids": ["v1", "v4", "v3", "v2"]}  # CCW
        ]
    elif preset == "4_grid":
        # 4 コマ田の字 (2x2 グリッド)
        vertices = [
            {"id": "v1", "x": 0.05, "y": 0.05},
            {"id": "v2", "x": 0.50, "y": 0.05},
            {"id": "v3", "x": 0.95, "y": 0.05},
            {"id": "v4", "x": 0.05, "y": 0.50},
            {"id": "v5", "x": 0.50, "y": 0.50},
            {"id": "v6", "x": 0.95, "y": 0.50},
            {"id": "v7", "x": 0.05, "y": 0.95},
            {"id": "v8", "x": 0.50, "y": 0.95},
            {"id": "v9", "x": 0.95, "y": 0.95},
        ]
        panels = [
            {"id": "p1", "vertex_ids": ["v1", "v4", "v5", "v2"]},  # CCW
            {"id": "p2", "vertex_ids": ["v2", "v5", "v6", "v3"]},  # CCW
            {"id": "p3", "vertex_ids": ["v4", "v7", "v8", "v5"]},  # CCW
            {"id": "p4", "vertex_ids": ["v5", "v8", "v9", "v6"]},  # CCW
        ]
    elif preset == "3_dynamic":
        # 3 コマ斜めカット (上段が斜め分割、中央分割点 v5 を全隣接パネルで共有)
        vertices = [
            {"id": "v1", "x": 0.05, "y": 0.05},
            {"id": "v2", "x": 0.95, "y": 0.05},
            {"id": "v3", "x": 0.95, "y": 0.40},
            {"id": "v4", "x": 0.05, "y": 0.55},
            {"id": "v5", "x": 0.50, "y": 0.475},  # 斜めライン上の共有点
            {"id": "v6", "x": 0.50, "y": 0.95},
            {"id": "v7", "x": 0.05, "y": 0.95},
            {"id": "v8", "x": 0.95, "y": 0.95},
        ]
        panels = [
            {"id": "p1", "vertex_ids": ["v1", "v4", "v5", "v3", "v2"]},  # CCW (v5 挿入で T-junction 排除)
            {"id": "p2", "vertex_ids": ["v4", "v7", "v6", "v5"]},        # CCW
            {"id": "p3", "vertex_ids": ["v5", "v6", "v8", "v3"]},        # CCW
        ]
    else:
        # 3 Panels Basic (上 1 コマ、下 2 コマ分割) - 既定
        vertices = [
            {"id": "v1", "x": 0.05, "y": 0.05},
            {"id": "v2", "x": 0.95, "y": 0.05},
            {"id": "v3", "x": 0.95, "y": 0.45},
            {"id": "v4", "x": 0.05, "y": 0.45},
            {"id": "v5", "x": 0.50, "y": 0.45},  # 水平ライン上の共有中点
            {"id": "v6", "x": 0.05, "y": 0.95},
            {"id": "v7", "x": 0.50, "y": 0.95},  # 下枠上の共有中点
            {"id": "v8", "x": 0.95, "y": 0.95},
        ]
        panels = [
            {"id": "p1", "vertex_ids": ["v1", "v4", "v5", "v3", "v2"]},  # CCW (v5 挿入で T-junction 排除)
            {"id": "p2", "vertex_ids": ["v4", "v6", "v7", "v5"]},        # CCW
            {"id": "p3", "vertex_ids": ["v5", "v7", "v8", "v3"]},        # CCW
        ]

    return {
        "version": 1,
        "canvas": {"width": W, "height": H},
        "frame": frame,
        "vertices": vertices,
        "panels": panels,
        "metadata": {"preset": preset}
    }


def validate_panel_layout_spec(spec_data: Any, context_name: str = "PANEL_LAYOUT_SPEC") -> Dict[str, Any]:
    """
    PANEL_LAYOUT_SPEC (v1) のデータ構造と平面分割トポロジーを厳格に検証・正規化する。
    - version: 1
    - canvas: width, height in [1, 8192]
    - frame: x, y, w, h
    - vertices: list of dict with unique id, x, y in [0.0, 1.0]
    - panels: list of dict with unique id, vertex_ids
    - Planar Subdivision Invariants (T-junction, self-intersection, edge incidence <= 2, area conservation)
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

    # 1. Version
    version = spec_data.get("version")
    if version != 1:
        raise ValueError(f"[{context_name}] Unsupported schema version: {version}. Expected version 1.")

    # 2. Canvas
    canvas = spec_data.get("canvas")
    if not isinstance(canvas, dict):
        raise ValueError(f"[{context_name}] 'canvas' must be a dictionary.")
    width = canvas.get("width")
    height = canvas.get("height")
    if not isinstance(width, int) or isinstance(width, bool) or width <= 0 or width > 8192:
        raise ValueError(f"[{context_name}] 'canvas.width' must be an integer between 1 and 8192, got {width!r}")
    if not isinstance(height, int) or isinstance(height, bool) or height <= 0 or height > 8192:
        raise ValueError(f"[{context_name}] 'canvas.height' must be an integer between 1 and 8192, got {height!r}")

    # 3. Layout Frame (未指定時はデフォルト補完)
    raw_frame = spec_data.get("frame")
    if raw_frame is None or not isinstance(raw_frame, dict):
        frame = {"x": 0.05, "y": 0.05, "w": 0.90, "h": 0.90}
    else:
        frame = {
            "x": round(float(raw_frame.get("x", 0.05)), 4),
            "y": round(float(raw_frame.get("y", 0.05)), 4),
            "w": round(float(raw_frame.get("w", 0.90)), 4),
            "h": round(float(raw_frame.get("h", 0.90)), 4),
        }

    # 4. Vertices
    vertices = spec_data.get("vertices")
    if not isinstance(vertices, list):
        raise ValueError(f"[{context_name}] 'vertices' must be a list.")
    if len(vertices) < 3:
        raise ValueError(f"[{context_name}] 'vertices' must have at least 3 vertices, got {len(vertices)}.")

    vertex_map = {}
    validated_vertices = []
    for idx, v in enumerate(vertices):
        v_ctx = f"{context_name}.vertices[{idx}]"
        if not isinstance(v, dict):
            raise ValueError(f"[{v_ctx}] Vertex must be a dictionary.")
        vid = v.get("id")
        if not isinstance(vid, str) or not vid.strip():
            raise ValueError(f"[{v_ctx}] Vertex 'id' must be a non-empty string.")
        if vid in vertex_map:
            raise ValueError(f"[{v_ctx}] Duplicate vertex id: '{vid}'")

        vx = v.get("x")
        vy = v.get("y")
        if vx is None or isinstance(vx, bool) or not isinstance(vx, (int, float)) or not math.isfinite(float(vx)):
            raise ValueError(f"[{v_ctx}] Vertex 'x' must be a finite float, got {vx!r}")
        if vy is None or isinstance(vy, bool) or not isinstance(vy, (int, float)) or not math.isfinite(float(vy)):
            raise ValueError(f"[{v_ctx}] Vertex 'y' must be a finite float, got {vy!r}")

        norm_x = max(0.0, min(1.0, float(vx)))
        norm_y = max(0.0, min(1.0, float(vy)))
        v_entry = {"id": vid, "x": round(norm_x, 4), "y": round(norm_y, 4)}
        vertex_map[vid] = (v_entry["x"], v_entry["y"])
        validated_vertices.append(v_entry)

    # 5. Panels (Count & Winding 正規化)
    panels = spec_data.get("panels")
    if not isinstance(panels, list):
        raise ValueError(f"[{context_name}] 'panels' must be a list.")
    if len(panels) < 1 or len(panels) > MAX_PANELS:
        raise ValueError(f"[{context_name}] 'panels' count must be between 1 and {MAX_PANELS}, got {len(panels)}.")

    seen_panel_ids = set()
    validated_panels = []
    for idx, p in enumerate(panels):
        p_ctx = f"{context_name}.panels[{idx}]"
        if not isinstance(p, dict):
            raise ValueError(f"[{p_ctx}] Panel must be a dictionary.")
        pid = p.get("id")
        if not isinstance(pid, str) or not pid.strip():
            raise ValueError(f"[{p_ctx}] Panel 'id' must be a non-empty string.")
        if pid in seen_panel_ids:
            raise ValueError(f"[{p_ctx}] Duplicate panel id: '{pid}'")
        seen_panel_ids.add(pid)

        v_ids = p.get("vertex_ids")
        if not isinstance(v_ids, list) or len(v_ids) < 3:
            raise ValueError(f"[{p_ctx}] 'vertex_ids' must be a list of at least 3 vertex IDs.")

        for vid in v_ids:
            if vid not in vertex_map:
                raise ValueError(f"[{p_ctx}] Undefined vertex reference: '{vid}'")

        # 反時計回り (CCW) に正規化
        ccw_v_ids = normalize_winding_ccw(v_ids, vertex_map)

        validated_panels.append({
            "id": pid,
            "vertex_ids": ccw_v_ids
        })

    candidate_spec = copy.deepcopy(spec_data)
    candidate_spec["version"] = 1
    candidate_spec["canvas"] = {"width": width, "height": height}
    candidate_spec["frame"] = frame
    candidate_spec["vertices"] = validated_vertices
    candidate_spec["panels"] = validated_panels
    if "metadata" not in candidate_spec or not isinstance(candidate_spec["metadata"], dict):
        candidate_spec["metadata"] = {}

    # 6. 平面分割トポロジー検証 (T-Junction, Self-Intersection, Edge Incidence, Area Conservation)
    topo_summary = validate_layout_topology(candidate_spec, context_name=context_name)
    candidate_spec["metadata"]["topology_summary"] = topo_summary

    return candidate_spec
