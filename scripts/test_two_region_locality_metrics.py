import os
import sys
import glob
import numpy as np
from PIL import Image

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUTPUT_DIR = os.path.join(ROOT_DIR, "ComfyUI", "output", "Tegaki", "TwoRegionOracle")


def find_latest_image(prefix: str):
    matches = glob.glob(os.path.join(OUTPUT_DIR, f"{prefix}_*.png"))
    if not matches:
        return None
    matches.sort(key=os.path.getmtime)
    return matches[-1]


def calculate_locality_metrics():
    print("================================================================================")
    print("Evaluating Regional Locality Metrics (Phase 3C Oracle)")
    print("================================================================================")

    base_path = find_latest_image("Core_Locality_Base")
    variant_path = find_latest_image("Core_Locality_Variant")

    if not base_path or not variant_path:
        print(f"[METRIC PENDING] Base or Variant image not found in {OUTPUT_DIR}")
        print(f"  Base: {base_path}")
        print(f"  Variant: {variant_path}")
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

    # マスクの構築:
    # A: [0.05, 0.10, 0.42, 0.80]
    # B: [0.53, 0.10, 0.42, 0.80]
    mask_A = np.zeros((H, W), dtype=bool)
    mask_B = np.zeros((H, W), dtype=bool)

    ax0, ay0 = int(0.05 * W), int(0.10 * H)
    ax1, ay1 = int((0.05 + 0.42) * W), int((0.10 + 0.80) * H)
    mask_A[ay0:ay1, ax0:ax1] = True

    bx0, by0 = int(0.53 * W), int(0.10 * H)
    bx1, by1 = int((0.53 + 0.42) * W), int((0.10 + 0.80) * H)
    mask_B[by0:by1, bx0:bx1] = True

    mask_outside = ~(mask_A | mask_B)

    mean_diff_A = float(diff[mask_A].mean()) if mask_A.any() else 0.0
    mean_diff_B = float(diff[mask_B].mean()) if mask_B.any() else 0.0
    mean_diff_outside = float(diff[mask_outside].mean()) if mask_outside.any() else 0.0

    locality_ratio = mean_diff_A / (mean_diff_B + 1e-6)
    outside_isolation = mean_diff_A / (mean_diff_outside + 1e-6)

    print("\n--- Locality Measurement Results ---")
    print(f"  Mean Difference Inside Region A (Target Change): {mean_diff_A:.4f}")
    print(f"  Mean Difference Inside Region B (Fixed Partner): {mean_diff_B:.4f}")
    print(f"  Mean Difference Outside A/B (Background):        {mean_diff_outside:.4f}")
    print(f"  Locality Ratio (Delta_A / Delta_B):             {locality_ratio:.2f}x")
    print(f"  Outside Isolation (Delta_A / Delta_Outside):     {outside_isolation:.2f}x")

    # 評価判定
    # Region A の変化が Region B より有意に大きく、局所性が維持されているか
    is_localized = locality_ratio >= 1.5

    result = {
        "status": "PASS" if is_localized else "PARTIAL",
        "mean_diff_A": round(mean_diff_A, 4),
        "mean_diff_B": round(mean_diff_B, 4),
        "mean_diff_outside": round(mean_diff_outside, 4),
        "locality_ratio": round(locality_ratio, 2),
        "outside_isolation": round(outside_isolation, 2),
        "is_localized": is_localized
    }

    print("\n================================================================================")
    print(f"Result: {result['status']} (Locality Ratio: {locality_ratio:.2f}x)")
    print("================================================================================")
    return result


if __name__ == "__main__":
    calculate_locality_metrics()
