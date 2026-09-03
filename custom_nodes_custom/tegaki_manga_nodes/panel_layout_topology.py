import math
from typing import Dict, Any, List, Tuple, Optional, Set

EPSILON = 1e-6
MIN_PANEL_AREA = 0.005
MAX_PANELS = 6


def signed_area(pts: List[Tuple[float, float]]) -> float:
    """Shoelace formula による多角形の符号付き面積 (CCW: 正, CW: 負)"""
    n = len(pts)
    if n < 3:
        return 0.0
    area = 0.0
    for i in range(n):
        j = (i + 1) % n
        area += pts[i][0] * pts[j][1] - pts[j][0] * pts[i][1]
    return area * 0.5


def normalize_winding_ccw(
    v_ids: List[str],
    v_map: Dict[str, Tuple[float, float]]
) -> List[str]:
    """
    多角形の頂点順序を反時計回り (CCW) に正規化する。
    時計回り (CW) の場合は順序を反転する。
    """
    pts = [v_map[vid] for vid in v_ids if vid in v_map]
    if len(pts) < 3:
        return list(v_ids)
    sa = signed_area(pts)
    if sa < 0.0:
        return list(reversed(v_ids))
    return list(v_ids)


def cross_product_2d(o: Tuple[float, float], a: Tuple[float, float], b: Tuple[float, float]) -> float:
    """ベクトル OA と OB の外積 (z成分)"""
    return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])


def segments_intersect(
    p1: Tuple[float, float],
    p2: Tuple[float, float],
    p3: Tuple[float, float],
    p4: Tuple[float, float],
    eps: float = EPSILON
) -> bool:
    """
    線分 p1-p2 と p3-p4 が端点以外で真に内部交差するかを判定する。
    """
    def ccw(a, b, c):
        return cross_product_2d(a, b, c)

    d1 = ccw(p3, p4, p1)
    d2 = ccw(p3, p4, p2)
    d3 = ccw(p1, p2, p3)
    d4 = ccw(p1, p2, p4)

    # 端点での接触を許容するため、真の交差 (符号が真に異なる) のみを交差とする
    if ((d1 > eps and d2 < -eps) or (d1 < -eps and d2 > eps)) and \
       ((d3 > eps and d4 < -eps) or (d3 < -eps and d4 > eps)):
        return True
    return False


def point_on_segment(
    pt: Tuple[float, float],
    p1: Tuple[float, float],
    p2: Tuple[float, float],
    eps: float = 1e-5
) -> bool:
    """
    点 pt が線分 p1-p2 の途中に乗っているか (端点 p1, p2 自体を除く)
    """
    d_p1 = math.hypot(pt[0] - p1[0], pt[1] - p1[1])
    d_p2 = math.hypot(pt[0] - p2[0], pt[1] - p2[1])
    if d_p1 < eps or d_p2 < eps:
        return False  # 端点に一致する場合は False

    # 距離の和判定
    d_line = math.hypot(p2[0] - p1[0], p2[1] - p1[1])
    if d_line < eps:
        return False
    if abs((d_p1 + d_p2) - d_line) < eps:
        return True
    return False


def polygon_self_intersects(pts: List[Tuple[float, float]]) -> bool:
    """
    多角形の非隣接辺同士が交差しているか (自己交差・bow-tie 等の検出)
    """
    n = len(pts)
    if n < 4:
        return False
    for i in range(n):
        p1 = pts[i]
        p2 = pts[(i + 1) % n]
        for j in range(i + 2, n):
            if i == 0 and j == n - 1:
                continue  # 隣接辺
            p3 = pts[j]
            p4 = pts[(j + 1) % n]
            if segments_intersect(p1, p2, p3, p4):
                return True
    return False


def polygon_is_convex(pts: List[Tuple[float, float]], eps: float = 1e-6) -> bool:
    """
    多角形が凸多角形 (Convex) であるかを判定する。
    """
    n = len(pts)
    if n < 3:
        return False
    if n == 3:
        return True

    prev_sign = 0
    for i in range(n):
        o = pts[i]
        a = pts[(i + 1) % n]
        b = pts[(i + 2) % n]
        cp = cross_product_2d(o, a, b)
        if abs(cp) > eps:
            sign = 1 if cp > 0 else -1
            if prev_sign == 0:
                prev_sign = sign
            elif prev_sign != sign:
                return False
    return True


def edge_key(v1_id: str, v2_id: str) -> Tuple[str, str]:
    """無向エッジの正準キー (辞書順ソート)"""
    return (v1_id, v2_id) if v1_id < v2_id else (v2_id, v1_id)


def build_edge_incidence(panels: List[Dict[str, Any]]) -> Dict[Tuple[str, str], List[str]]:
    """
    全パネルのエッジ出現頻度 (Incidence) を集計する。
    戻り値: { (v_min, v_max): [panel_id, ...] }
    """
    incidence = {}
    for p in panels:
        pid = p["id"]
        v_ids = p["vertex_ids"]
        n = len(v_ids)
        for i in range(n):
            ek = edge_key(v_ids[i], v_ids[(i + 1) % n])
            if ek not in incidence:
                incidence[ek] = []
            incidence[ek].append(pid)
    return incidence


def detect_t_junctions(
    spec: Dict[str, Any],
    v_map: Dict[str, Tuple[float, float]]
) -> List[Dict[str, Any]]:
    """
    T-Junction の検出。
    あるパネルの辺 E = (v1, v2) の途中に、別のパネルの頂点 vt が乗っているにもかかわらず、
    そのパネルの頂点サイクルに vt が挿入されていない状態を検出して報告する。
    """
    t_junctions = []
    for p in spec["panels"]:
        pid = p["id"]
        v_ids = p["vertex_ids"]
        v_set = set(v_ids)
        n = len(v_ids)
        for i in range(n):
            v1_id = v_ids[i]
            v2_id = v_ids[(i + 1) % n]
            p1 = v_map[v1_id]
            p2 = v_map[v2_id]

            for vt_id, pt in v_map.items():
                if vt_id in v_set:
                    continue
                if point_on_segment(pt, p1, p2):
                    t_junctions.append({
                        "panel_id": pid,
                        "edge": (v1_id, v2_id),
                        "t_vertex_id": vt_id,
                        "t_vertex_pos": pt
                    })
    return t_junctions


def check_area_conservation(
    spec: Dict[str, Any],
    v_map: Dict[str, Tuple[float, float]],
    frame: Dict[str, float],
    eps: float = 0.005
) -> Tuple[bool, float, float]:
    """
    面積保存則の検証。
    全パネルの面積合計が Layout Frame の面積と一致しているか。
    """
    frame_w = frame.get("w", 0.90)
    frame_h = frame.get("h", 0.90)
    frame_area = frame_w * frame_h

    total_panel_area = 0.0
    for p in spec["panels"]:
        pts = [v_map[vid] for vid in p["vertex_ids"]]
        total_panel_area += abs(signed_area(pts))

    is_conserved = abs(total_panel_area - frame_area) <= eps
    return is_conserved, round(total_panel_area, 4), round(frame_area, 4)


def diagnose_gaps_and_overlaps(
    spec: Dict[str, Any],
    v_map: Dict[str, Tuple[float, float]],
    frame: Dict[str, float],
    grid_w: int = 90,
    grid_h: int = 90
) -> Dict[str, float]:
    """
    Layout Frame 内をグリッドラスタライズして、隙間率 (gap_ratio) と
    重複率 (overlap_ratio) を診断する。
    """
    fx = frame.get("x", 0.05)
    fy = frame.get("y", 0.05)
    fw = frame.get("w", 0.90)
    fh = frame.get("h", 0.90)

    # 各パネルの多角形リスト
    polys = []
    for p in spec["panels"]:
        pts = [v_map[vid] for vid in p["vertex_ids"]]
        polys.append(pts)

    def pt_in_poly(px, py, pts):
        inside = False
        n = len(pts)
        for i in range(n):
            j = (i + 1) % n
            xi, yi = pts[i]
            xj, yj = pts[j]
            if ((yi > py) != (yj > py)) and (px < (xj - xi) * (py - yi) / (yj - yi + 1e-7) + xi):
                inside = not inside
        return inside

    gap_cells = 0
    overlap_cells = 0
    total_cells = grid_w * grid_h

    for gy in range(grid_h):
        cy = fy + (gy + 0.5) * (fh / grid_h)
        for gx in range(grid_w):
            cx = fx + (gx + 0.5) * (fw / grid_w)

            count = 0
            for poly in polys:
                if pt_in_poly(cx, cy, poly):
                    count += 1

            if count == 0:
                gap_cells += 1
            elif count > 1:
                overlap_cells += 1

    gap_ratio = gap_cells / total_cells
    overlap_ratio = overlap_cells / total_cells

    return {
        "gap_ratio": round(gap_ratio, 4),
        "overlap_ratio": round(overlap_ratio, 4),
        "total_cells_checked": total_cells
    }


def validate_layout_topology(spec: Dict[str, Any], context_name: str = "PANEL_LAYOUT_SPEC") -> Dict[str, Any]:
    """
    PANEL_LAYOUT_SPEC の平面分割 (Planar Subdivision) トポロジーを包括的に検証する。
    違反があれば ValueError を投げて fail-closed とする。
    """
    vertices = spec.get("vertices", [])
    panels = spec.get("panels", [])

    v_map = {v["id"]: (float(v["x"]), float(v["y"])) for v in vertices}

    # 1. 各 Panel 頂点サイクルの検証
    for idx, p in enumerate(panels):
        pid = p.get("id", f"p_{idx}")
        v_ids = p.get("vertex_ids", [])
        p_ctx = f"[{context_name}.panels[{idx}:{pid}]]"

        if len(v_ids) < 3:
            raise ValueError(f"{p_ctx} Panel must have at least 3 vertices, got {len(v_ids)}.")

        # 重複頂点チェック (同一サイクル内での重複)
        if len(set(v_ids)) != len(v_ids):
            raise ValueError(f"{p_ctx} Duplicate vertex ID in panel cycle: {v_ids}")

        pts = []
        for vid in v_ids:
            if vid not in v_map:
                raise ValueError(f"{p_ctx} References undefined vertex: '{vid}'")
            pts.append(v_map[vid])

        # ゼロ長エッジの検証
        n = len(pts)
        for i in range(n):
            p1 = pts[i]
            p2 = pts[(i + 1) % n]
            if math.hypot(p1[0] - p2[0], p1[1] - p2[1]) < EPSILON:
                raise ValueError(f"{p_ctx} Zero-length edge detected between vertex {v_ids[i]} and {v_ids[(i+1)%n]}.")

        # 自己交差検証 (bow-tie 等)
        if polygon_self_intersects(pts):
            raise ValueError(f"{p_ctx} Self-intersecting polygon detected (bow-tie shape).")

        # 面積検証
        area = abs(signed_area(pts))
        if area < MIN_PANEL_AREA:
            raise ValueError(f"{p_ctx} Panel area ({area:.4f}) is smaller than minimum ({MIN_PANEL_AREA}).")

        # 凸性検証 (Convex V1 Policy)
        if not polygon_is_convex(pts):
            raise ValueError(f"{p_ctx} Non-convex polygon detected. V1 planar subdivision requires convex panels.")

    # 2. Edge Incidence の検証
    incidence = build_edge_incidence(panels)
    for ek, p_list in incidence.items():
        if len(p_list) > 2:
            raise ValueError(f"[{context_name}] Edge {ek} shared by {len(p_list)} panels ({p_list}). Max allowed incidence is 2.")

    # 3. T-Junction の検出・禁止
    t_juncs = detect_t_junctions(spec, v_map)
    if t_juncs:
        tj = t_juncs[0]
        raise ValueError(
            f"[{context_name}] T-Junction detected: vertex '{tj['t_vertex_id']}' lies on edge {tj['edge']} of panel '{tj['panel_id']}', but is not included in its vertex cycle."
        )

    # 4. Layout Frame & 面積保存則の検証
    frame = spec.get("frame", {"x": 0.05, "y": 0.05, "w": 0.90, "h": 0.90})
    is_conserved, total_area, frame_area = check_area_conservation(spec, v_map, frame)
    if not is_conserved:
        raise ValueError(
            f"[{context_name}] Area conservation violated: sum of panel areas ({total_area}) != frame area ({frame_area})."
        )

    # 5. Diagnostic: Gap / Overlap
    diag = diagnose_gaps_and_overlaps(spec, v_map, frame)
    if diag["overlap_ratio"] > 0.01:
        raise ValueError(f"[{context_name}] Panel overlap detected (overlap_ratio: {diag['overlap_ratio']:.2%}).")
    if diag["gap_ratio"] > 0.01:
        raise ValueError(f"[{context_name}] Panel gap detected (gap_ratio: {diag['gap_ratio']:.2%}).")

    return {
        "status": "VALID",
        "panel_count": len(panels),
        "vertex_count": len(vertices),
        "unique_edges_count": len(incidence),
        "total_area": total_area,
        "frame_area": frame_area,
        "gap_ratio": diag["gap_ratio"],
        "overlap_ratio": diag["overlap_ratio"]
    }
