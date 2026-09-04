import math
from typing import Dict, Any, List, Tuple, Optional, Set

EPSILON = 1e-6
MIN_PANEL_AREA = 0.005
MAX_PANELS = 6
AREA_CONSERVATION_TOLERANCE = 0.001  # 厳格許容誤差 (1e-3)


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
    """点 pt が線分 p1-p2 の途中に乗っているか (端点を除く)"""
    d_p1 = math.hypot(pt[0] - p1[0], pt[1] - p1[1])
    d_p2 = math.hypot(pt[0] - p2[0], pt[1] - p2[1])
    if d_p1 < eps or d_p2 < eps:
        return False

    d_line = math.hypot(p2[0] - p1[0], p2[1] - p1[1])
    if d_line < eps:
        return False
    if abs((d_p1 + d_p2) - d_line) < eps:
        return True
    return False


def point_strictly_inside_convex_polygon(
    pt: Tuple[float, float],
    poly: List[Tuple[float, float]],
    eps: float = 1e-5
) -> bool:
    """点 pt が凸多角形 poly の真の内部 (境界を除く) にあるかを判定する"""
    n = len(poly)
    if n < 3:
        return False
    prev_sign = 0
    for i in range(n):
        o = poly[i]
        a = poly[(i + 1) % n]
        cp = cross_product_2d(o, a, pt)
        if abs(cp) <= eps:
            return False  # 辺上にある場合は内部ではない
        sign = 1 if cp > 0 else -1
        if prev_sign == 0:
            prev_sign = sign
        elif prev_sign != sign:
            return False
    return True


def polygon_self_intersects(pts: List[Tuple[float, float]]) -> bool:
    """多角形の非隣接辺同士が交差しているか (自己交差・bow-tie 等の検出)"""
    n = len(pts)
    if n < 4:
        return False
    for i in range(n):
        p1 = pts[i]
        p2 = pts[(i + 1) % n]
        for j in range(i + 2, n):
            if i == 0 and j == n - 1:
                continue
            p3 = pts[j]
            p4 = pts[(j + 1) % n]
            if segments_intersect(p1, p2, p3, p4):
                return True
    return False


def polygon_is_convex(pts: List[Tuple[float, float]], eps: float = 1e-4) -> bool:
    """多角形が凸多角形 (Convex) であるかを判定する (直線上の頂点・丸め誤差を許容)"""
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
    """全パネルのエッジ出現頻度 (Incidence) を集計する"""
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


def is_edge_on_frame_boundary(
    p1: Tuple[float, float],
    p2: Tuple[float, float],
    frame: Dict[str, float],
    eps: float = 1e-4
) -> bool:
    """
    辺の両端点 p1, p2 が、同じ Layout Frame 外枠境界線上 (上、下、左、右) にあるかを判定する。
    """
    fx_min = frame["x"]
    fx_max = frame["x"] + frame["w"]
    fy_min = frame["y"]
    fy_max = frame["y"] + frame["h"]

    # 上辺
    if abs(p1[1] - fy_min) <= eps and abs(p2[1] - fy_min) <= eps:
        return True
    # 下辺
    if abs(p1[1] - fy_max) <= eps and abs(p2[1] - fy_max) <= eps:
        return True
    # 左辺
    if abs(p1[0] - fx_min) <= eps and abs(p2[0] - fx_min) <= eps:
        return True
    # 右辺
    if abs(p1[0] - fx_max) <= eps and abs(p2[0] - fx_max) <= eps:
        return True

    return False


def detect_t_junctions(
    spec: Dict[str, Any],
    v_map: Dict[str, Tuple[float, float]]
) -> List[Dict[str, Any]]:
    """T-Junction の検出"""
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


def detect_duplicate_coordinates(
    vertices: List[Dict[str, Any]],
    eps: float = 1e-4
) -> Optional[Tuple[str, str]]:
    """別 ID なのに同じ座標を持つ頂点のペアを検出する"""
    n = len(vertices)
    for i in range(n):
        v1 = vertices[i]
        p1 = (v1["x"], v1["y"])
        for j in range(i + 1, n):
            v2 = vertices[j]
            p2 = (v2["x"], v2["y"])
            if math.hypot(p1[0] - p2[0], p1[1] - p2[1]) < eps:
                return (v1["id"], v2["id"])
    return None


def detect_orphan_vertices(spec: Dict[str, Any]) -> List[str]:
    """どのパネルからも参照されていない孤立頂点 ID を検出する"""
    referenced_ids = set()
    for p in spec.get("panels", []):
        for vid in p.get("vertex_ids", []):
            referenced_ids.add(vid)

    orphans = []
    for v in spec.get("vertices", []):
        if v["id"] not in referenced_ids:
            orphans.append(v["id"])
    return orphans


def check_pairwise_polygon_overlap(
    panels: List[Dict[str, Any]],
    v_map: Dict[str, Tuple[float, float]]
) -> Optional[Tuple[str, str, str]]:
    """
    任意の 2 パネル間で内部が真に重なり合っていないかを幾何学的に検査する。
    戻り値: 重複を検知した場合 (panel_id_A, panel_id_B, reason)
    """
    n = len(panels)
    for i in range(n):
        pa = panels[i]
        pts_a = [v_map[vid] for vid in pa["vertex_ids"]]
        for j in range(i + 1, n):
            pb = panels[j]
            pts_b = [v_map[vid] for vid in pb["vertex_ids"]]

            # 1. 辺同士の真の内部交差検査
            na = len(pts_a)
            nb = len(pts_b)
            for ia in range(na):
                e1a = pts_a[ia]
                e2a = pts_a[(ia + 1) % na]
                for ib in range(nb):
                    e1b = pts_b[ib]
                    e2b = pts_b[(ib + 1) % nb]
                    if segments_intersect(e1a, e2a, e1b, e2b):
                        return (pa["id"], pb["id"], f"Edges intersect between {pa['vertex_ids'][ia]}-{pa['vertex_ids'][(ia+1)%na]} and {pb['vertex_ids'][ib]}-{pb['vertex_ids'][(ib+1)%nb]}")

            # 2. 一方の頂点が他方の真の内部にあるか
            for pt in pts_a:
                if point_strictly_inside_convex_polygon(pt, pts_b):
                    return (pa["id"], pb["id"], f"Vertex of '{pa['id']}' lies strictly inside panel '{pb['id']}'")
            for pt in pts_b:
                if point_strictly_inside_convex_polygon(pt, pts_a):
                    return (pa["id"], pb["id"], f"Vertex of '{pb['id']}' lies strictly inside panel '{pa['id']}'")

    return None


def check_area_conservation(
    spec: Dict[str, Any],
    v_map: Dict[str, Tuple[float, float]],
    frame: Dict[str, float],
    eps: float = AREA_CONSERVATION_TOLERANCE
) -> Tuple[bool, float, float]:
    """面積保存則の検証 (許容誤差 eps = 0.001)"""
    frame_w = frame["w"]
    frame_h = frame["h"]
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
    """Layout Frame 内をグリッドラスタライズして隙間・重複を診断する"""
    fx = frame["x"]
    fy = frame["y"]
    fw = frame["w"]
    fh = frame["h"]

    polys = [[v_map[vid] for vid in p["vertex_ids"]] for p in spec["panels"]]

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

    return {
        "gap_ratio": round(gap_cells / total_cells, 4),
        "overlap_ratio": round(overlap_cells / total_cells, 4),
        "total_cells_checked": total_cells
    }


def validate_layout_topology(spec: Dict[str, Any], context_name: str = "PANEL_LAYOUT_SPEC") -> Dict[str, Any]:
    """
    PANEL_LAYOUT_SPEC の平面分割 (Planar Subdivision) トポロジー契約を厳格に完全検証する。
    """
    vertices = spec.get("vertices", [])
    panels = spec.get("panels", [])

    # 1. Layout Frame の厳格検証
    raw_frame = spec.get("frame")
    if not isinstance(raw_frame, dict):
        raise ValueError(f"[{context_name}] 'frame' must be a dictionary.")

    for k in ("x", "y", "w", "h"):
        val = raw_frame.get(k)
        if val is None or isinstance(val, bool) or not isinstance(val, (int, float)) or not math.isfinite(float(val)):
            raise ValueError(f"[{context_name}.frame.{k}] Frame dimension must be a finite float, got {val!r}")

    fx = float(raw_frame["x"])
    fy = float(raw_frame["y"])
    fw = float(raw_frame["w"])
    fh = float(raw_frame["h"])

    if fw <= 0 or fh <= 0:
        raise ValueError(f"[{context_name}.frame] Dimensions must be positive, got w={fw}, h={fh}")
    if fx < 0 or fy < 0:
        raise ValueError(f"[{context_name}.frame] Coordinates must be >= 0, got x={fx}, y={fy}")
    if fx + fw > 1.0001 or fy + fh > 1.0001:
        raise ValueError(f"[{context_name}.frame] Frame exceeds normalized unit square [0, 1], got x+w={fx+fw}, y+h={fy+fh}")

    frame = {"x": fx, "y": fy, "w": fw, "h": fh}

    # 2. Vertices 検証 & Frame 包含
    v_map = {}
    for idx, v in enumerate(vertices):
        vid = v["id"]
        vx = float(v["x"])
        vy = float(v["y"])
        # Frame 境界包含チェック (許容誤差 1e-4)
        if vx < fx - 1e-4 or vx > fx + fw + 1e-4 or vy < fy - 1e-4 or vy > fy + fh + 1e-4:
            raise ValueError(
                f"[{context_name}.vertices[{idx}:{vid}]] Vertex ({vx}, {vy}) is outside the Layout Frame (x:[{fx},{fx+fw}], y:[{fy},{fy+fh}])."
            )
        v_map[vid] = (vx, vy)

    # 重複座標頂点の排除 (別IDで同一座標)
    dup_coord = detect_duplicate_coordinates(vertices)
    if dup_coord:
        raise ValueError(f"[{context_name}] Duplicate vertex coordinates detected between '{dup_coord[0]}' and '{dup_coord[1]}'.")

    # 3. 各 Panel 頂点サイクルの検証
    for idx, p in enumerate(panels):
        pid = p.get("id", f"p_{idx}")
        v_ids = p.get("vertex_ids", [])
        p_ctx = f"[{context_name}.panels[{idx}:{pid}]]"

        if len(v_ids) < 3:
            raise ValueError(f"{p_ctx} Panel must have at least 3 vertices, got {len(v_ids)}.")

        if len(set(v_ids)) != len(v_ids):
            raise ValueError(f"{p_ctx} Duplicate vertex ID in panel cycle: {v_ids}")

        pts = []
        for vid in v_ids:
            if vid not in v_map:
                raise ValueError(f"{p_ctx} References undefined vertex: '{vid}'")
            pts.append(v_map[vid])

        # ゼロ長エッジ
        n = len(pts)
        for i in range(n):
            p1 = pts[i]
            p2 = pts[(i + 1) % n]
            if math.hypot(p1[0] - p2[0], p1[1] - p2[1]) < EPSILON:
                raise ValueError(f"{p_ctx} Zero-length edge detected between vertex {v_ids[i]} and {v_ids[(i+1)%n]}.")

        # 自己交差検証
        if polygon_self_intersects(pts):
            raise ValueError(f"{p_ctx} Self-intersecting polygon detected (bow-tie shape).")

        # 面積検証
        area = abs(signed_area(pts))
        if area < MIN_PANEL_AREA:
            raise ValueError(f"{p_ctx} Panel area ({area:.4f}) is smaller than minimum ({MIN_PANEL_AREA}).")

        # 凸性検証
        if not polygon_is_convex(pts):
            raise ValueError(f"{p_ctx} Non-convex polygon detected. V1 planar subdivision requires convex panels.")

    # 孤立頂点の排除
    orphans = detect_orphan_vertices(spec)
    if orphans:
        raise ValueError(f"[{context_name}] Orphan vertices detected (not referenced by any panel): {orphans}")

    # 4. T-Junction の検出・禁止
    t_juncs = detect_t_junctions(spec, v_map)
    if t_juncs:
        tj = t_juncs[0]
        raise ValueError(
            f"[{context_name}] T-Junction detected: vertex '{tj['t_vertex_id']}' lies on edge {tj['edge']} of panel '{tj['panel_id']}', but is not included in its vertex cycle."
        )

    # 5. ペアワイズ多角形交差 (Exact Pairwise Overlap Check)
    overlap_err = check_pairwise_polygon_overlap(panels, v_map)
    if overlap_err:
        pa_id, pb_id, reason = overlap_err
        raise ValueError(f"[{context_name}] Exact polygon overlap detected between panel '{pa_id}' and '{pb_id}': {reason}")

    # 6. エッジ分類と厳格 Incidence
    incidence = build_edge_incidence(panels)
    for ek, p_list in incidence.items():
        v1_pos = v_map[ek[0]]
        v2_pos = v_map[ek[1]]
        count = len(p_list)
        if count > 2:
            raise ValueError(f"[{context_name}] Edge {ek} shared by {count} panels ({p_list}). Max allowed incidence is 2.")
        elif count == 1:
            # 外枠境界線上でなければならない
            if not is_edge_on_frame_boundary(v1_pos, v2_pos, frame):
                raise ValueError(
                    f"[{context_name}] Structural gap detected: internal edge {ek} has incidence 1 but does not lie on the Layout Frame boundary."
                )

    # 7. 面積保存則の検証 (許容誤差 0.001)
    is_conserved, total_area, frame_area = check_area_conservation(spec, v_map, frame, eps=AREA_CONSERVATION_TOLERANCE)
    if not is_conserved:
        raise ValueError(
            f"[{context_name}] Area conservation violated: sum of panel areas ({total_area}) != frame area ({frame_area}). Tolerance: {AREA_CONSERVATION_TOLERANCE}"
        )

    # 8. Diagnostic: Gap / Overlap (デバッグサマリー)
    diag = diagnose_gaps_and_overlaps(spec, v_map, frame)

    return {
        "status": "VALID",
        "panel_count": len(panels),
        "vertex_count": len(vertices),
        "unique_edges_count": len(incidence),
        "total_area": total_area,
        "frame_area": frame_area,
        "area_tolerance": AREA_CONSERVATION_TOLERANCE,
        "gap_ratio": diag["gap_ratio"],
        "overlap_ratio": diag["overlap_ratio"]
    }
