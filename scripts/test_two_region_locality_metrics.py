import os
import sys
import glob
import json
from typing import Dict, Any, Optional
import numpy as np
from PIL import Image

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUTPUT_DIR = os.path.join(ROOT_DIR, "ComfyUI", "output", "Tegaki", "TwoRegionOracle")
CUSTOM_NODES_DIR = os.path.join(ROOT_DIR, "ComfyUI", "custom_nodes")
if CUSTOM_NODES_DIR not in sys.path:
    sys.path.insert(0, CUSTOM_NODES_DIR)
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from custom_nodes.tegaki_manga_nodes.two_region_spec import validate_two_region_spec, get_default_two_region_spec


def find_latest_image(prefix: str) -> Optional[str]:
    matches = glob.glob(os.path.join(OUTPUT_DIR, f"{prefix}_*.png"))
    if not matches:
        return None
    matches.sort(key=os.path.getmtime)
    return matches[-1]


def build_masks_from_spec(spec_data: Dict[str, Any], H: int, W: int):
    spec = validate_two_region_spec(spec_data)
    mask_A = np.zeros((H, W), dtype=bool)
    mask_B = np.zeros((H, W), dtype=bool)

    for reg in spec["regions"]:
        if not reg.get("enabled", True):
            continue
        rid = reg["id"]
        rx = int(round(reg["x"] * W))
        ry = int(round(reg["y"] * H))
        rw = int(round(reg["w"] * W))
        rh = int(round(reg["h"] * H))

        x0 = max(0, min(W, rx))
        y0 = max(0, min(H, ry))
        x1 = max(0, min(W, rx + rw))
        y1 = max(0, min(H, ry + rh))

        if x1 > x0 and y1 > y0:
            if rid == "A":
                mask_A[y0:y1, x0:x1] = True
            elif rid == "B":
                mask_B[y0:y1, x0:x1] = True

    return mask_A, mask_B


def calculate_locality_metrics(spec_override: Optional[Dict[str, Any]] = None):
    print("================================================================================")
    print("Evaluating Regional Locality Metrics (Phase 3C.1 Spec-Driven)")
    print("================================================================================")

    base_path = find_latest_image("Core_Locality_Base")
    variant_path = find_latest_image("Core_Locality_Variant")

    if not base_path or not variant_path:
        print(f"[METRIC PENDING] Base or Variant image not found in {OUTPUT_DIR}")
        return {
            "status": "SKIPPED",
            "reason": "images_not_yet_generated"
        }

    print(f"  Base Image:    {os.path.basename(base_path)}")
    print(f"  Variant Image: {os.path.basename(variant_path)}")

    img_base = np.array(Image.open(base_path).convert("RGB"), dtype=np.float32) / 255.0
    img_var = np.array(Image.open(variant_path).convert("RGB"), dtype=np.float32) / 255.0

    H, W, _ = img_base.shape
    diff = np.abs(img_base - img_var).mean(axis=2)  # [H, W]

    # Spec 駆動によるマスク生成
    spec = spec_override or get_default_two_region_spec(W, H)
    mask_A, mask_B = build_masks_from_spec(spec, H, W)

    # 4 分割領域の導出:
    # 1. A-only (A \ B)
    # 2. B-only (B \ A)
    # 3. Overlap (A ∩ B)
    # 4. Outside (not (A or B))
    mask_A_only = mask_A & (~mask_B)
    mask_B_only = mask_B & (~mask_A)
    mask_overlap = mask_A & mask_B
    mask_outside = ~(mask_A | mask_B)

    mean_diff_A_total = float(diff[mask_A].mean()) if mask_A.any() else 0.0
    mean_diff_B_total = float(diff[mask_B].mean()) if mask_B.any() else 0.0
    mean_diff_A_only = float(diff[mask_A_only].mean()) if mask_A_only.any() else 0.0
    mean_diff_B_only = float(diff[mask_B_only].mean()) if mask_B_only.any() else 0.0
    mean_diff_overlap = float(diff[mask_overlap].mean()) if mask_overlap.any() else 0.0
    mean_diff_outside = float(diff[mask_outside].mean()) if mask_outside.any() else 0.0

    # 局所性比率 (Target A_only / Fixed B_only)
    locality_ratio = mean_diff_A_only / (mean_diff_B_only + 1e-6)
    outside_isolation = mean_diff_A_only / (mean_diff_outside + 1e-6)

    print("\n--- Spec-Driven Spatial Locality Measurements ---")
    print(f"  Difference Inside Region A (Total Target):    {mean_diff_A_total:.4f}")
    print(f"  Difference Inside Region B (Total Partner):   {mean_diff_B_total:.4f}")
    print(f"  Difference Inside A-only (Exclusive Target):  {mean_diff_A_only:.4f}")
    print(f"  Difference Inside B-only (Exclusive Partner): {mean_diff_B_only:.4f}")
    print(f"  Difference Inside Overlap (A ∩ B):            {mean_diff_overlap:.4f}")
    print(f"  Difference Outside A/B (Background):          {mean_diff_outside:.4f}")
    print(f"  Spatial Locality Ratio (Delta_A_only / Delta_B_only):     {locality_ratio:.2f}x")
    print(f"  Outside Isolation Ratio (Delta_A_only / Delta_Outside):   {outside_isolation:.2f}x")

    # Diagnostic 判定
    is_spatially_localized = locality_ratio >= 1.5

    result = {
        "status": "PASS" if is_spatially_localized else "PARTIAL",
        "diagnostic": "SPATIALLY_LOCALIZED" if is_spatially_localized else "ATTRIBUTE_DIFFUSED",
        "mean_diff_A_total": round(mean_diff_A_total, 4),
        "mean_diff_B_total": round(mean_diff_B_total, 4),
        "mean_diff_A_only": round(mean_diff_A_only, 4),
        "mean_diff_B_only": round(mean_diff_B_only, 4),
        "mean_diff_overlap": round(mean_diff_overlap, 4),
        "mean_diff_outside": round(mean_diff_outside, 4),
        "spatial_locality_ratio": round(locality_ratio, 2),
        "outside_isolation_ratio": round(outside_isolation, 2),
        "raw_metric_note": "Pixel difference measures spatial change locality, not full semantic correctness."
    }

    print("\n================================================================================")
    print(f"Diagnostic Result: {result['status']} (Spatial Locality Ratio: {locality_ratio:.2f}x)")
    print(f"Note: {result['raw_metric_note']}")
    print("================================================================================")
    return result


if __name__ == "__main__":
    calculate_locality_metrics()
