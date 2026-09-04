"""
Phase 3G Verification Contact Sheet Generator
=============================================
Generates comparative contact sheets for Phase 3G verification:
1. Sheet A: Workflow 25 (Single A Top-Left) vs Workflow 26 (Single A Bottom-Right)
2. Sheet B: Workflow 27 (Two-Region Dog Left / Cat Right) vs Workflow 28 (Two-Region Dog Right / Cat Left SWAP)
3. Sheet C: Canonical Authoring Set (Workflows 21, 22, 23, 24)
"""

import os
import sys
from PIL import Image, ImageDraw, ImageFont

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUTPUT_DIR = os.path.join(ROOT_DIR, "output", "Tegaki", "Phase3G")
CANONICAL_DIR = os.path.join(OUTPUT_DIR, "canonical")
PHASE3F_DIR = os.path.join(ROOT_DIR, "output", "Tegaki", "Phase3F")


def get_font(size=20):
    for fn in ["arial.ttf", "segoeui.ttf", "tahoma.ttf"]:
        try:
            return ImageFont.truetype(fn, size)
        except Exception:
            pass
    return ImageFont.load_default()


def create_two_panel_comparison(
    left_title: str,
    left_sub: str,
    left_img_path: str,
    right_title: str,
    right_sub: str,
    right_img_path: str,
    sheet_title: str,
    out_filename: str
):
    print(f"[ContactSheet] Generating {out_filename}...")
    if not os.path.exists(left_img_path) or not os.path.exists(right_img_path):
        print(f"[WARN] One or both images missing: {left_img_path} / {right_img_path}")
        return

    left_img = Image.open(left_img_path).convert("RGB")
    right_img = Image.open(right_img_path).convert("RGB")

    panel_w, panel_h = 600, 600
    margin = 35
    header_h = 75
    label_h = 55

    sheet_w = 2 * panel_w + 3 * margin
    sheet_h = header_h + panel_h + label_h + 2 * margin

    # Futaba theme colors
    bg_color = (248, 246, 242)
    border_color = (190, 165, 145)
    accent_color = (210, 105, 30)
    text_color = (35, 25, 15)
    sub_color = (100, 85, 75)

    sheet = Image.new("RGB", (sheet_w, sheet_h), bg_color)
    draw = ImageDraw.Draw(sheet)

    title_font = get_font(24)
    item_title_font = get_font(18)
    sub_font = get_font(14)

    # Header
    draw.text((margin, 22), sheet_title, fill=text_color, font=title_font)
    draw.line([(margin, 65), (sheet_w - margin, 65)], fill=accent_color, width=2)

    items = [
        (left_title, left_sub, left_img, margin),
        (right_title, right_sub, right_img, margin * 2 + panel_w)
    ]

    for title, sub, img, x in items:
        y = header_h + margin
        thumb = img.copy()
        thumb.thumbnail((panel_w, panel_h), Image.Resampling.LANCZOS)

        bx = x + (panel_w - thumb.width) // 2
        by = y + (panel_h - thumb.height) // 2

        # Border
        draw.rectangle([bx - 2, by - 2, bx + thumb.width + 1, by + thumb.height + 1], outline=border_color, width=2)
        sheet.paste(thumb, (bx, by))

        # Labels
        ly = y + panel_h + 10
        draw.text((x, ly), title, fill=text_color, font=item_title_font)
        draw.text((x, ly + 24), sub, fill=sub_color, font=sub_font)

    out_path = os.path.join(OUTPUT_DIR, out_filename)
    sheet.save(out_path, quality=95)
    print(f"[SUCCESS] Saved contact sheet: {out_path}")


def build_sheet_a():
    create_two_panel_comparison(
        left_title="Workflow 25: Single Region A (Top-Left)",
        left_sub="Geometry: [0.05, 0.05, 0.45, 0.45] | Prompt: 'a white dog, full body' | Seed: 42",
        left_img_path=os.path.join(CANONICAL_DIR, "wf25_canonical_single_a_top_left.png"),
        right_title="Workflow 26: Single Region A (Bottom-Right)",
        right_sub="Geometry: [0.50, 0.50, 0.45, 0.45] | Prompt: 'a white dog, full body' | Seed: 42",
        right_img_path=os.path.join(CANONICAL_DIR, "wf26_canonical_single_a_bottom_right.png"),
        sheet_title="Sheet A: Canonical Single-Region Spatial Placement Oracle (WF25 Top-Left vs WF26 Bottom-Right)",
        out_filename="sheet_a_single_a_spatial_comparison.png"
    )


def build_sheet_b():
    create_two_panel_comparison(
        left_title="Workflow 27: Dog Left, Cat Right",
        left_sub="Dog: [0.05, 0.15, 0.45, 0.70] | Cat: [0.50, 0.15, 0.45, 0.70] | Seed: 42",
        left_img_path=os.path.join(CANONICAL_DIR, "wf27_canonical_two_region_dog_cat_left_right.png"),
        right_title="Workflow 28: Dog Right, Cat Left (SWAP)",
        right_sub="Dog: [0.50, 0.15, 0.45, 0.70] | Cat: [0.05, 0.15, 0.45, 0.70] | Seed: 42",
        right_img_path=os.path.join(CANONICAL_DIR, "wf28_canonical_two_region_dog_cat_swap.png"),
        sheet_title="Sheet B: Two-Region Semantic Binding & Spatial Swap Oracle (WF27 vs WF28 SWAP)",
        out_filename="sheet_b_two_region_swap_comparison.png"
    )


def build_sheet_c():
    images_info = [
        ("Workflow 21: Recurrent Cast 4-Panel", "wf21_zero_touch_recurrent_cast.png"),
        ("Workflow 22: Multi-Scene Same Cast", "wf22_zero_touch_multiscene.png"),
        ("Workflow 23: Progressive 4-Panel Authoring", "wf23_zero_touch_progressive_4panel.png"),
        ("Workflow 24: Progressive SubScene Oracle", "wf24_zero_touch_progressive_subscene.png"),
    ]

    loaded = []
    for title, fname in images_info:
        p = os.path.join(PHASE3F_DIR, fname)
        if os.path.exists(p):
            img = Image.open(p).convert("RGB")
            loaded.append((title, img))

    if not loaded:
        print("[WARN] No images found for Sheet C.")
        return

    thumb_w, thumb_h = 512, 512
    margin = 30
    header_h = 60
    label_h = 40
    cols = 2
    rows = 2

    sheet_w = cols * thumb_w + (cols + 1) * margin
    sheet_h = header_h + rows * (thumb_h + label_h) + (rows + 1) * margin

    sheet = Image.new("RGB", (sheet_w, sheet_h), (248, 246, 242))
    draw = ImageDraw.Draw(sheet)

    title_font = get_font(24)
    label_font = get_font(16)

    draw.text((margin, 18), "Sheet C: Canonical Manga Authoring Set (Workflows 21-24)", fill=(35, 25, 15), font=title_font)
    draw.line([(margin, 52), (sheet_w - margin, 52)], fill=(210, 105, 30), width=2)

    for idx, (title, img) in enumerate(loaded):
        r = idx // cols
        c = idx % cols
        x = margin + c * (thumb_w + margin)
        y = header_h + margin + r * (thumb_h + label_h + margin)

        thumb = img.copy()
        thumb.thumbnail((thumb_w, thumb_h), Image.Resampling.LANCZOS)
        bx = x + (thumb_w - thumb.width) // 2
        by = y + (thumb_h - thumb.height) // 2

        draw.rectangle([bx - 1, by - 1, bx + thumb.width, by + thumb.height], outline=(190, 165, 145), width=2)
        sheet.paste(thumb, (bx, by))
        draw.text((x, y + thumb_h + 8), title, fill=(35, 25, 15), font=label_font)

    out_path = os.path.join(OUTPUT_DIR, "sheet_c_authoring_gallery.png")
    sheet.save(out_path, quality=95)
    print(f"[SUCCESS] Saved contact sheet: {out_path}")


def generate_all_sheets():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    build_sheet_a()
    build_sheet_b()
    build_sheet_c()


if __name__ == "__main__":
    generate_all_sheets()
