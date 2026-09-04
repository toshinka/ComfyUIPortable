import copy
import math
from typing import Dict, Any, List, Tuple, Optional

from .panel_layout_topology import (
    signed_area,
    normalize_winding_ccw,
    validate_layout_topology,
    MAX_PANELS
)


def line_intersection_with_segment(
    p1: Tuple[float, float],
    p2: Tuple[float, float],
    line_a: float,
    line_b: float,
    line_c: float,
    eps: float = 1e-6
) -> Optional[Tuple[float, float, float]]:
    """線分 p1-p2 と直線 a*x + b*y + c = 0 の交点 (ix, iy, t)"""
    d1 = line_a * p1[0] + line_b * p1[1] + line_c
    d2 = line_a * p2[0] + line_b * p2[1] + line_c

    if abs(d1 - d2) < 1e-9:
        return None

    t = d1 / (d1 - d2)
    if t < -eps or t > 1.0 + eps:
        return None

    t_clamped = max(0.0, min(1.0, t))
    ix = p1[0] + t_clamped * (p2[0] - p1[0])
    iy = p1[1] + t_clamped * (p2[1] - p1[1])
    return (ix, iy, t_clamped)


def clip_polygon_halfplane(
    v_ids: List[str],
    v_map: Dict[str, Tuple[float, float]],
    line_a: float,
    line_b: float,
    line_c: float,
    keep_positive: bool
) -> List[Tuple[Optional[str], Tuple[float, float], Optional[Tuple[str, str]]]]:
    """
    Sutherland-Hodgman スタイルの半平面クリッピング。
    多角形頂点を巡回しながら、クリップされた多角形の頂点シーケンスを出力する。
    要素: (vid_or_None, (x, y), edge_parent_or_None)
    """
    n = len(v_ids)
    pts = [v_map[vid] for vid in v_ids]
    dists = [line_a * p[0] + line_b * p[1] + line_c for p in pts]

    def is_inside(d: float) -> bool:
        return d >= -1e-5 if keep_positive else d <= 1e-5

    output = []
    for i in range(n):
        cur_vid = v_ids[i]
        next_vid = v_ids[(i + 1) % n]
        cur_pt = pts[i]
        next_pt = pts[(i + 1) % n]
        d_cur = dists[i]
        d_next = dists[(i + 1) % n]

        cur_in = is_inside(d_cur)
        next_in = is_inside(d_next)

        if cur_in and next_in:
            output.append((next_vid, next_pt, None))
        elif cur_in and not next_in:
            res = line_intersection_with_segment(cur_pt, next_pt, line_a, line_b, line_c)
            if res:
                ix, iy, _ = res
                output.append((None, (ix, iy), (cur_vid, next_vid)))
        elif not cur_in and next_in:
            res = line_intersection_with_segment(cur_pt, next_pt, line_a, line_b, line_c)
            if res:
                ix, iy, _ = res
                output.append((None, (ix, iy), (cur_vid, next_vid)))
            output.append((next_vid, next_pt, None))

    return output


def generic_split_panel(
    spec_data: Dict[str, Any],
    target_panel_id: str,
    split_mode: str = "horizontal",
    split_ratio: float = 0.5
) -> Dict[str, Any]:
    """
    一般分割アルゴリズム (Sutherland-Hodgman Polygon Clipping with Intersection Propagation):
    - target_panel を直線で安全に分割
    - 交点頂点を隣接する全パネルの vertex cycle へ自動挿入 (T-Junction 防止)
    - 面積保存則とトポロジー検証を実行し、失敗時はロールバック
    """
    spec = copy.deepcopy(spec_data)
    if len(spec["panels"]) >= MAX_PANELS:
        raise ValueError(f"Panel capacity limit reached ({MAX_PANELS} max). Cannot split further.")

    target_idx = next((i for i, p in enumerate(spec["panels"]) if p["id"] == target_panel_id), None)
    if target_idx is None:
        raise ValueError(f"Target panel '{target_panel_id}' not found in spec.")

    target_panel = spec["panels"][target_idx]
    v_map = {v["id"]: (float(v["x"]), float(v["y"])) for v in spec["vertices"]}
    target_pts = [v_map[vid] for vid in target_panel["vertex_ids"]]

    min_x = min(p[0] for p in target_pts)
    max_x = max(p[0] for p in target_pts)
    min_y = min(p[1] for p in target_pts)
    max_y = max(p[1] for p in target_pts)

    dx = max(1e-4, max_x - min_x)
    dy = max(1e-4, max_y - min_y)

    ratio = max(0.1, min(0.9, float(split_ratio)))
    if split_mode == "horizontal":
        split_y = min_y + ratio * dy
        la, lb, lc = 0.0, 1.0, -split_y
    elif split_mode == "vertical":
        split_x = min_x + ratio * dx
        la, lb, lc = 1.0, 0.0, -split_x
    elif split_mode in ("diag_slash", "diagonal_slash"):
        # / 方向 (左下から右上):
        # 傾き slope = dy / dx, 切片 c = -(slope * max_x + min_y)
        slope = dy / dx
        la = slope
        lb = 1.0
        lc = -(slope * max_x + min_y)
    elif split_mode in ("diag_backslash", "diagonal_backslash", "diagonal"):
        # \ 方向 (左上から右下):
        slope = dy / dx
        la = slope
        lb = -1.0
        lc = min_y - slope * min_x
    else:
        raise ValueError(f"Unsupported split mode: '{split_mode}'")

    # Sutherland-Hodgman で 2 つの半平面にクリッピング
    clip_pos = clip_polygon_halfplane(target_panel["vertex_ids"], v_map, la, lb, lc, keep_positive=True)
    clip_neg = clip_polygon_halfplane(target_panel["vertex_ids"], v_map, la, lb, lc, keep_positive=False)

    if len(clip_pos) < 3 or len(clip_neg) < 3:
        raise ValueError(f"Split line did not divide panel '{target_panel_id}' into 2 valid polygons.")

    # 新設交点頂点を Global Mesh に登録
    created_new_vertices = []
    
    def resolve_vertex(item):
        vid, (ix, iy), edge_parent = item
        if vid is not None:
            return vid
        # 既存頂点への近傍検索
        for ex_vid, (vx, vy) in v_map.items():
            if math.hypot(vx - ix, vy - iy) < 1e-4:
                return ex_vid
        # 新設頂点
        max_v_num = max(0, *[int(v["id"].replace("v", "")) for v in spec["vertices"] if v["id"].startswith("v") and v["id"][1:].isdigit()])
        new_vid = f"v{max_v_num + 1}"
        new_v_entry = {"id": new_vid, "x": round(ix, 4), "y": round(iy, 4)}
        spec["vertices"].append(new_v_entry)
        v_map[new_vid] = (new_v_entry["x"], new_v_entry["y"])
        if edge_parent:
            created_new_vertices.append((new_vid, edge_parent[0], edge_parent[1]))
        return new_vid

    vids_a = [resolve_vertex(item) for item in clip_pos]
    vids_b = [resolve_vertex(item) for item in clip_neg]

    # T-Junction 防止: 新設頂点をエッジ (ev1, ev2) を共有するすべての他パネルへ挿入
    for new_vid, ev1, ev2 in created_new_vertices:
        for p in spec["panels"]:
            if p["id"] == target_panel_id:
                continue
            vids = p["vertex_ids"]
            n = len(vids)
            for i in range(n):
                v_a = vids[i]
                v_b = vids[(i + 1) % n]
                if (v_a == ev1 and v_b == ev2) or (v_a == ev2 and v_b == ev1):
                    vids.insert(i + 1, new_vid)
                    break

    # 重複IDの連続除去
    def dedupe_cycle(cycle):
        res = []
        for v in cycle:
            if not res or res[-1] != v:
                res.append(v)
        if len(res) > 1 and res[0] == res[-1]:
            res.pop()
        return res

    vids_a_clean = normalize_winding_ccw(dedupe_cycle(vids_a), v_map)
    vids_b_clean = normalize_winding_ccw(dedupe_cycle(vids_b), v_map)

    max_p_num = max(0, *[int(p["id"].replace("p", "")) for p in spec["panels"] if p["id"].startswith("p") and p["id"][1:].isdigit()])
    new_pid_b = f"p{max_p_num + 1}"

    spec["panels"][target_idx] = {
        "id": target_panel_id,
        "vertex_ids": vids_a_clean
    }
    spec["panels"].append({
        "id": new_pid_b,
        "vertex_ids": vids_b_clean
    })

    for p in spec["panels"]:
        if p["id"] != target_panel_id:
            p["vertex_ids"] = normalize_winding_ccw(dedupe_cycle(p["vertex_ids"]), v_map)

    # 参照されている全頂点 ID を収集し、未参照頂点を prune
    all_referenced_vids = set()
    for p in spec["panels"]:
        for vid in p["vertex_ids"]:
            all_referenced_vids.add(vid)
    spec["vertices"] = [v for v in spec["vertices"] if v["id"] in all_referenced_vids]

    # 厳格なトポロジー・面積保存・T-Junction 検証 (失敗時例外で自動ロールバック)
    validate_layout_topology(spec, context_name="GenericSplit")

    return spec
