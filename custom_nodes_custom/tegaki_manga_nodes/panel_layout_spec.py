import copy
import json
import math
from typing import Dict, Any, List, Optional, Tuple

MIN_PANEL_AREA = 0.005
MAX_PANELS = 6


def get_default_panel_layout_spec(width: int = 832, height: int = 1216, preset: str = "3_basic") -> Dict[str, Any]:
    """
    既定の PANEL_LAYOUT_SPEC (v1) を生成する。
    Shared-Vertex Mesh 方式により、コマ間の隙間や重なりを排除。
    初期状態: 3 Panels Basic (上段 1 コマ、下段 2 コマ)
    """
    W = int(width)
    H = int(height)

    if preset == "1_full":
        # 1 コマ全画面
        vertices = [
            {"id": "v1", "x": 0.05, "y": 0.05},
            {"id": "v2", "x": 0.95, "y": 0.05},
            {"id": "v3", "x": 0.95, "y": 0.95},
            {"id": "v4", "x": 0.05, "y": 0.95},
        ]
        panels = [
            {"id": "p1", "vertex_ids": ["v1", "v2", "v3", "v4"]}
        ]
    elif preset == "4_grid":
        # 4 コマ田の字
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
            {"id": "p1", "vertex_ids": ["v1", "v2", "v5", "v4"]},
            {"id": "p2", "vertex_ids": ["v2", "v3", "v6", "v5"]},
            {"id": "p3", "vertex_ids": ["v4", "v5", "v8", "v7"]},
            {"id": "p4", "vertex_ids": ["v5", "v6", "v9", "v8"]},
        ]
    elif preset == "3_dynamic":
        # 3 コマ斜めカット (上段が斜め分割)
        vertices = [
            {"id": "v1", "x": 0.05, "y": 0.05},
            {"id": "v2", "x": 0.95, "y": 0.05},
            {"id": "v3", "x": 0.95, "y": 0.40},
            {"id": "v4", "x": 0.05, "y": 0.55},  # 斜めライン
            {"id": "v5", "x": 0.50, "y": 0.475}, # 共有中点
            {"id": "v6", "x": 0.50, "y": 0.95},
            {"id": "v7", "x": 0.05, "y": 0.95},
            {"id": "v8", "x": 0.95, "y": 0.95},
        ]
        panels = [
            {"id": "p1", "vertex_ids": ["v1", "v2", "v3", "v4"]},
            {"id": "p2", "vertex_ids": ["v4", "v5", "v6", "v7"]},
            {"id": "p3", "vertex_ids": ["v5", "v3", "v8", "v6"]},
        ]
    else:
        # 3 Panels Basic (上 1 コマ、下 2 コマ分割) - 既定
        vertices = [
            {"id": "v1", "x": 0.05, "y": 0.05},
            {"id": "v2", "x": 0.95, "y": 0.05},
            {"id": "v3", "x": 0.95, "y": 0.45},
            {"id": "v4", "x": 0.05, "y": 0.45},
            {"id": "v5", "x": 0.50, "y": 0.45}, # 下段分割の共有上頂点
            {"id": "v6", "x": 0.05, "y": 0.95},
            {"id": "v7", "x": 0.50, "y": 0.95}, # 下段分割の共有下頂点
            {"id": "v8", "x": 0.95, "y": 0.95},
        ]
        panels = [
            {"id": "p1", "vertex_ids": ["v1", "v2", "v3", "v5", "v4"]},
            {"id": "p2", "vertex_ids": ["v4", "v5", "v7", "v6"]},
            {"id": "p3", "vertex_ids": ["v5", "v3", "v8", "v7"]},
        ]

    return {
        "version": 1,
        "canvas": {"width": W, "height": H},
        "vertices": vertices,
        "panels": panels,
        "metadata": {"preset": preset}
    }


def polygon_signed_area(pts: List[Tuple[float, float]]) -> float:
    """Shoelace formula による多角形の符号付き面積"""
    n = len(pts)
    if n < 3:
        return 0.0
    area = 0.0
    for i in range(n):
        j = (i + 1) % n
        area += pts[i][0] * pts[j][1] - pts[j][0] * pts[i][1]
    return area * 0.5


def validate_panel_layout_spec(spec_data: Any, context_name: str = "PANEL_LAYOUT_SPEC") -> Dict[str, Any]:
    """
    PANEL_LAYOUT_SPEC (v1) のデータ構造を厳格に検証・正規化する。
    - version: 1
    - canvas: width, height in [1, 8192]
    - vertices: list of dict with unique id, x, y in [0.0, 1.0]
    - panels: list of dict with unique id, vertex_ids (length >= 3, all valid vertex references)
    - panel count: 1 <= count <= 6
    - 各パネルの多角形が最小面積以上であること
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

    # 3. Vertices
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
        vertex_map[vid] = v_entry
        validated_vertices.append(v_entry)

    # 4. Panels
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

        pts = []
        for vid in v_ids:
            if vid not in vertex_map:
                raise ValueError(f"[{p_ctx}] Undefined vertex reference: '{vid}'")
            v_ref = vertex_map[vid]
            pts.append((v_ref["x"], v_ref["y"]))

        # 面積チェック
        area = abs(polygon_signed_area(pts))
        if area < MIN_PANEL_AREA:
            raise ValueError(f"[{p_ctx}] Panel '{pid}' area ({area:.4f}) is smaller than minimum ({MIN_PANEL_AREA}).")

        validated_panels.append({
            "id": pid,
            "vertex_ids": list(v_ids)
        })

    validated_spec = copy.deepcopy(spec_data)
    validated_spec["version"] = 1
    validated_spec["canvas"] = {"width": width, "height": height}
    validated_spec["vertices"] = validated_vertices
    validated_spec["panels"] = validated_panels
    if "metadata" not in validated_spec or not isinstance(validated_spec["metadata"], dict):
        validated_spec["metadata"] = {}

    return validated_spec
