"""
Phase 3H Verification Contact Sheet & Evaluation Overlay Generator
==================================================================
Generates diagnostic contact sheets with 3-panel visualization per case:
  [ Target Region Map ] | [ Final Output ] | [ Evaluation Overlay ]

Generates:
1. Sheet D: Single A Exclusive Base Comparison (WF25 vs WF29, WF26 vs WF30)
2. Sheet E: Two Region Swap Exclusive Base Comparison (WF27 vs WF31, WF28 vs WF32)
3. Sheet F: Progressive Authoring Staging Causality (WF33 vs WF34)
4. Sheet G: Fast Draft 12 Regression Verification (WF32 vs WF32-Fast12, WF34 vs WF34-Fast12)
"""

import os
import sys
from PIL import Image, ImageDraw, ImageFont

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUTPUT_DIR = os.path.join(ROOT_DIR, "output", "Tegaki", "Phase3H")
CANONICAL_DIR = os.path.join(OUTPUT_DIR, "canonical")
PHASE3G_DIR = os.path.join(ROOT_DIR, "output", "Tegaki", "Phase3G", "canonical")


def get_font(size=20):
    for fn in ["arial.ttf", "segoeui.ttf", "tahoma.ttf"]:
        try:
            return ImageFont.truetype(fn, size)
        except Exception:
            pass
    return ImageFont.load_default()


def create_region_map(canvas_w: int, canvas_h: int, regions: list) -> Image.Image:
    """
    Creates a schematic Target Region Map.
    regions: list of dict(label, bounds=[x, y, w, h], color_rgb)
    """
    img = Image.new("RGB", (canvas_w, canvas_h), (250, 248, 245))
    draw = ImageDraw.Draw(img)

    # Grid background
    grid_step = canvas_w // 8
    for gx in range(0, canvas_w, grid_step):
        draw.line([(gx, 0), (gx, canvas_h)], fill=(230, 225, 220), width=1)
    for gy in range(0, canvas_h, grid_step):
        draw.line([(0, gy), (canvas_w, gy)], fill=(230, 225, 220), width=1)

    # Canvas border
    draw.rectangle([0, 0, canvas_w - 1, canvas_h - 1], outline=(180, 160, 140), width=2)

    font = get_font(max(14, canvas_w // 35))
    for r in regions:
        bx, by, bw, bh = r["bounds"]
        rx0 = int(round(bx * canvas_w))
        ry0 = int(round(by * canvas_h))
        rx1 = int(round((bx + bw) * canvas_w))
        ry1 = int(round((by + bh) * canvas_h))
        color = r.get("color", (245, 130, 32))

        # Fill semi-transparent box
        overlay = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
        odraw = ImageDraw.Draw(overlay)
        odraw.rectangle([rx0, ry0, rx1, ry1], fill=(color[0], color[1], color[2], 60), outline=(color[0], color[1], color[2], 240), width=3)
        img.paste(overlay, (0, 0), overlay)

        # Label
        label_text = f"{r['label']}\n[{bx:.2f}, {by:.2f}, {bw:.2f}, {bh:.2f}]"
        draw.text((rx0 + 10, ry0 + 10), label_text, fill=(30, 20, 10), font=font)

    return img


def create_evaluation_overlay(base_img: Image.Image, regions: list) -> Image.Image:
    """
    Overlays semi-transparent region boundaries on top of base generated image.
    """
    w, h = base_img.size
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    odraw = ImageDraw.Draw(overlay)
    font = get_font(max(14, w // 35))

    for r in regions:
        bx, by, bw, bh = r["bounds"]
        rx0 = int(round(bx * w))
        ry0 = int(round(by * h))
        rx1 = int(round((bx + bw) * w))
        ry1 = int(round((by + bh) * w))
        color = r.get("color", (245, 130, 32))

        odraw.rectangle([rx0, ry0, rx1, ry1], fill=(color[0], color[1], color[2], 50), outline=(color[0], color[1], color[2], 255), width=3)
        tag = f"Target: {r['label']}"
        odraw.text((rx0 + 8, ry0 + 8), tag, fill=(255, 255, 255, 240), font=font)
        odraw.text((rx0 + 7, ry0 + 7), tag, fill=(color[0], color[1], color[2], 255), font=font)

    composite = base_img.convert("RGBA")
    composite.paste(overlay, (0, 0), overlay)
    return composite.convert("RGB")


def create_3panel_row(
    title: str,
    subtitle: str,
    raw_img_path: str,
    regions: list,
    thumb_size: int = 400
) -> Image.Image:
    """Creates a single diagnostic row: Target Map | Output | Evaluation Overlay"""
    if os.path.exists(raw_img_path):
        raw_img = Image.open(raw_img_path).convert("RGB")
    else:
        raw_img = Image.new("RGB", (thumb_size, thumb_size), (240, 230, 230))
        d = ImageDraw.Draw(raw_img)
        d.text((20, 20), f"MISSING:\n{os.path.basename(raw_img_path)}", fill=(180, 40, 40), font=get_font(16))

    region_map = create_region_map(raw_img.width, raw_img.height, regions)
    overlay_img = create_evaluation_overlay(raw_img, regions)

    margin = 20
    header_h = 45
    row_w = 3 * thumb_size + 4 * margin
    row_h = thumb_size + header_h + 2 * margin

    row_img = Image.new("RGB", (row_w, row_h), (248, 246, 242))
    draw = ImageDraw.Draw(row_img)

    title_font = get_font(18)
    sub_font = get_font(13)
    panel_tag_font = get_font(12)

    draw.text((margin, 10), title, fill=(35, 25, 15), font=title_font)
    draw.text((margin, 30), subtitle, fill=(110, 95, 85), font=sub_font)

    panels = [
        ("1. Target Region Map", region_map),
        ("2. Final Generated Image", raw_img),
        ("3. Evaluation Overlay", overlay_img)
    ]

    for idx, (ptag, pimg) in enumerate(panels):
        px = margin + idx * (thumb_size + margin)
        py = header_h + margin // 2

        thumb = pimg.copy()
        thumb.thumbnail((thumb_size, thumb_size), Image.Resampling.LANCZOS)
        bx = px + (thumb_size - thumb.width) // 2
        by = py + (thumb_size - thumb.height) // 2

        draw.rectangle([bx - 1, by - 1, bx + thumb.width, by + thumb.height], outline=(190, 170, 150), width=1)
        row_img.paste(thumb, (bx, by))
        draw.text((px, py - 18), ptag, fill=(80, 60, 40), font=panel_tag_font)

    return row_img


def build_sheet_d():
    """Sheet D: Single A Exclusive Base Comparison"""
    print("[ContactSheet] Building Sheet D (Single A Exclusive Base)...")
    regions_tl = [{"label": "Region A: White Dog", "bounds": [0.05, 0.05, 0.45, 0.45], "color": (245, 130, 32)}]
    regions_br = [{"label": "Region A: White Dog", "bounds": [0.50, 0.50, 0.45, 0.45], "color": (245, 130, 32)}]

    row1 = create_3panel_row(
        title="Workflow 25 (Baseline Top-Left): Uncontrolled Base",
        subtitle="Geometry: [0.05, 0.05, 0.45, 0.45] | Finding: Dog at TL + Unexpected Anime Girl in Background",
        raw_img_path=os.path.join(PHASE3G_DIR, "wf25_canonical_single_a_top_left.png"),
        regions=regions_tl
    )
    row2 = create_3panel_row(
        title="Workflow 29 (Exclusive Base Top-Left): Subject-Suppressed Base",
        subtitle="Geometry: [0.05, 0.05, 0.45, 0.45] | Expected: Dog at TL + Unexpected Girl Suppressed",
        raw_img_path=os.path.join(CANONICAL_DIR, "wf29_canonical_single_a_top_left_exclusive_base.png"),
        regions=regions_tl
    )
    row3 = create_3panel_row(
        title="Workflow 26 (Baseline Bottom-Right): Uncontrolled Base",
        subtitle="Geometry: [0.50, 0.50, 0.45, 0.45] | Finding: Dog at BR + Unexpected Anime Girl in Background",
        raw_img_path=os.path.join(PHASE3G_DIR, "wf26_canonical_single_a_bottom_right.png"),
        regions=regions_br
    )
    row4 = create_3panel_row(
        title="Workflow 30 (Exclusive Base Bottom-Right): Subject-Suppressed Base",
        subtitle="Geometry: [0.50, 0.50, 0.45, 0.45] | Expected: Dog at BR + Unexpected Girl Suppressed",
        raw_img_path=os.path.join(CANONICAL_DIR, "wf30_canonical_single_a_bottom_right_exclusive_base.png"),
        regions=regions_br
    )

    header_h = 70
    sheet_w = row1.width
    sheet_h = header_h + row1.height + row2.height + row3.height + row4.height + 30

    sheet = Image.new("RGB", (sheet_w, sheet_h), (245, 242, 237))
    draw = ImageDraw.Draw(sheet)
    draw.text((25, 20), "Sheet D: Single A Subject Exclusivity & Overlay Diagnostics (WF25 vs WF29, WF26 vs WF30)", fill=(35, 25, 15), font=get_font(24))
    draw.line([(25, 58), (sheet_w - 25, 58)], fill=(210, 105, 30), width=2)

    y = header_h
    for r in [row1, row2, row3, row4]:
        sheet.paste(r, (0, y))
        y += r.height + 8

    out_path = os.path.join(OUTPUT_DIR, "sheet_d_subject_exclusivity_single_a.png")
    sheet.save(out_path, quality=95)
    print(f"[SUCCESS] Saved Sheet D: {out_path}")


def build_sheet_e():
    """Sheet E: Two Region Swap Exclusive Base Comparison"""
    print("[ContactSheet] Building Sheet E (Two Region Swap Exclusive Base)...")
    regions_lr = [
        {"label": "Region A: Dog (Left)", "bounds": [0.05, 0.15, 0.45, 0.70], "color": (245, 130, 32)},
        {"label": "Region B: Cat (Right)", "bounds": [0.50, 0.15, 0.45, 0.70], "color": (37, 99, 235)}
    ]
    regions_swap = [
        {"label": "Region A: Dog (Right)", "bounds": [0.50, 0.15, 0.45, 0.70], "color": (245, 130, 32)},
        {"label": "Region B: Cat (Left)", "bounds": [0.05, 0.15, 0.45, 0.70], "color": (37, 99, 235)}
    ]

    row1 = create_3panel_row(
        title="Workflow 27 (Baseline Dog Left, Cat Right): Uncontrolled Base",
        subtitle="Left: Dog [0.05, 0.15, 0.45, 0.70] | Right: Cat [0.50, 0.15, 0.45, 0.70]",
        raw_img_path=os.path.join(PHASE3G_DIR, "wf27_canonical_two_region_dog_cat_left_right.png"),
        regions=regions_lr
    )
    row2 = create_3panel_row(
        title="Workflow 31 (Exclusive Base Dog Left, Cat Right): Subject-Suppressed Base",
        subtitle="Left: Dog [0.05, 0.15, 0.45, 0.70] | Right: Cat [0.50, 0.15, 0.45, 0.70] + Clean Background",
        raw_img_path=os.path.join(CANONICAL_DIR, "wf31_canonical_two_region_dog_cat_lr_exclusive_base.png"),
        regions=regions_lr
    )
    row3 = create_3panel_row(
        title="Workflow 28 (Baseline Dog Right, Cat Left SWAP): Uncontrolled Base",
        subtitle="Right: Dog [0.50, 0.15, 0.45, 0.70] | Left: Cat [0.05, 0.15, 0.45, 0.70]",
        raw_img_path=os.path.join(PHASE3G_DIR, "wf28_canonical_two_region_dog_cat_swap.png"),
        regions=regions_swap
    )
    row4 = create_3panel_row(
        title="Workflow 32 (Exclusive Base Dog Right, Cat Left SWAP): Subject-Suppressed Base",
        subtitle="Right: Dog [0.50, 0.15, 0.45, 0.70] | Left: Cat [0.05, 0.15, 0.45, 0.70] + Clean Background",
        raw_img_path=os.path.join(CANONICAL_DIR, "wf32_canonical_two_region_dog_cat_swap_exclusive_base.png"),
        regions=regions_swap
    )

    header_h = 70
    sheet_w = row1.width
    sheet_h = header_h + row1.height + row2.height + row3.height + row4.height + 30

    sheet = Image.new("RGB", (sheet_w, sheet_h), (245, 242, 237))
    draw = ImageDraw.Draw(sheet)
    draw.text((25, 20), "Sheet E: Two-Region Swap Subject Exclusivity & Overlay Diagnostics (WF27 vs WF31, WF28 vs WF32)", fill=(35, 25, 15), font=get_font(24))
    draw.line([(25, 58), (sheet_w - 25, 58)], fill=(210, 105, 30), width=2)

    y = header_h
    for r in [row1, row2, row3, row4]:
        sheet.paste(r, (0, y))
        y += r.height + 8

    out_path = os.path.join(OUTPUT_DIR, "sheet_e_subject_exclusivity_two_region_swap.png")
    sheet.save(out_path, quality=95)
    print(f"[SUCCESS] Saved Sheet E: {out_path}")


def build_sheet_f():
    """Sheet F: Progressive Authoring Staging Causality"""
    print("[ContactSheet] Building Sheet F (Progressive Authoring Staging Causality)...")
    regions_alice_l_bob_r = [
        {"label": "Alice: Blonde Twin Tails (Left)", "bounds": [0.05, 0.15, 0.42, 0.70], "color": (245, 130, 32)},
        {"label": "Bob: Short Dark Hair (Right)", "bounds": [0.53, 0.15, 0.42, 0.70], "color": (37, 99, 235)}
    ]
    regions_alice_r_bob_l = [
        {"label": "Alice: Blonde Twin Tails (Right)", "bounds": [0.53, 0.15, 0.42, 0.70], "color": (245, 130, 32)},
        {"label": "Bob: Short Dark Hair (Left)", "bounds": [0.05, 0.15, 0.42, 0.70], "color": (37, 99, 235)}
    ]

    row1 = create_3panel_row(
        title="Workflow 33: Production Authoring (Alice Left, Bob Right)",
        subtitle="Staging UI: Alice [0.05, 0.15, 0.42, 0.70] | Bob [0.53, 0.15, 0.42, 0.70] | Courtyard Scene",
        raw_img_path=os.path.join(CANONICAL_DIR, "wf33_authoring_alice_left_bob_right.png"),
        regions=regions_alice_l_bob_r
    )
    row2 = create_3panel_row(
        title="Workflow 34: Production Authoring SWAP (Alice Right, Bob Left)",
        subtitle="Staging UI: Alice [0.53, 0.15, 0.42, 0.70] | Bob [0.05, 0.15, 0.42, 0.70] | Courtyard Scene",
        raw_img_path=os.path.join(CANONICAL_DIR, "wf34_authoring_alice_right_bob_left.png"),
        regions=regions_alice_r_bob_l
    )

    header_h = 70
    sheet_w = row1.width
    sheet_h = header_h + row1.height + row2.height + 25

    sheet = Image.new("RGB", (sheet_w, sheet_h), (245, 242, 237))
    draw = ImageDraw.Draw(sheet)
    draw.text((25, 20), "Sheet F: Production Progressive Authoring Staging Causality (WF33 vs WF34 SWAP)", fill=(35, 25, 15), font=get_font(24))
    draw.line([(25, 58), (sheet_w - 25, 58)], fill=(210, 105, 30), width=2)

    y = header_h
    for r in [row1, row2]:
        sheet.paste(r, (0, y))
        y += r.height + 8

    out_path = os.path.join(OUTPUT_DIR, "sheet_f_authoring_staging_causality.png")
    sheet.save(out_path, quality=95)
    print(f"[SUCCESS] Saved Sheet F: {out_path}")


def build_sheet_g():
    """Sheet G: Fast Draft Profile Regression Verification"""
    print("[ContactSheet] Building Sheet G (Fast Draft Profile Regression)...")
    regions_swap = [
        {"label": "Region A: Dog (Right)", "bounds": [0.50, 0.15, 0.45, 0.70], "color": (245, 130, 32)},
        {"label": "Region B: Cat (Left)", "bounds": [0.05, 0.15, 0.45, 0.70], "color": (37, 99, 235)}
    ]
    regions_authoring_swap = [
        {"label": "Alice: Blonde Twin Tails (Right)", "bounds": [0.53, 0.15, 0.42, 0.70], "color": (245, 130, 32)},
        {"label": "Bob: Short Dark Hair (Left)", "bounds": [0.05, 0.15, 0.42, 0.70], "color": (37, 99, 235)}
    ]

    row1 = create_3panel_row(
        title="Workflow 32: Reference Mode (20 steps, Euler/Normal, CFG 7.0)",
        subtitle="Exclusive Base Swap: Dog Right, Cat Left",
        raw_img_path=os.path.join(CANONICAL_DIR, "wf32_canonical_two_region_dog_cat_swap_exclusive_base.png"),
        regions=regions_swap
    )
    row2 = create_3panel_row(
        title="Workflow 32: Fast Draft 12 Profile (12 steps, Hyper-SDXL, CFG 6.0)",
        subtitle="Exclusive Base Swap: Speedup & Seam-free verification",
        raw_img_path=os.path.join(CANONICAL_DIR, "wf32_fast12_swap_exclusive_base.png"),
        regions=regions_swap
    )
    row3 = create_3panel_row(
        title="Workflow 34: Reference Mode (20 steps, Euler/Normal, CFG 7.0)",
        subtitle="Production Authoring Swap: Alice Right, Bob Left",
        raw_img_path=os.path.join(CANONICAL_DIR, "wf34_authoring_alice_right_bob_left.png"),
        regions=regions_authoring_swap
    )
    row4 = create_3panel_row(
        title="Workflow 34: Fast Draft 12 Profile (12 steps, Hyper-SDXL, CFG 6.0)",
        subtitle="Production Authoring Swap: Speedup & Staging preservation",
        raw_img_path=os.path.join(CANONICAL_DIR, "wf34_fast12_authoring_swap.png"),
        regions=regions_authoring_swap
    )

    header_h = 70
    sheet_w = row1.width
    sheet_h = header_h + row1.height + row2.height + row3.height + row4.height + 30

    sheet = Image.new("RGB", (sheet_w, sheet_h), (245, 242, 237))
    draw = ImageDraw.Draw(sheet)
    draw.text((25, 20), "Sheet G: Fast Draft 12 Profile Regression & Semantic Integrity Check", fill=(35, 25, 15), font=get_font(24))
    draw.line([(25, 58), (sheet_w - 25, 58)], fill=(210, 105, 30), width=2)

    y = header_h
    for r in [row1, row2, row3, row4]:
        sheet.paste(r, (0, y))
        y += r.height + 8

    out_path = os.path.join(OUTPUT_DIR, "sheet_g_fast_draft_regression.png")
    sheet.save(out_path, quality=95)
    print(f"[SUCCESS] Saved Sheet G: {out_path}")


def generate_all_phase3h_sheets():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    build_sheet_d()
    build_sheet_e()
    build_sheet_f()
    build_sheet_g()


if __name__ == "__main__":
    generate_all_phase3h_sheets()
