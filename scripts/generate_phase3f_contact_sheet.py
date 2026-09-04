"""
Phase 3F Contact Sheet Generator
================================
Creates visual summary contact sheets for Phase 3F zero-touch execution:
1. phase3f_zero_touch_gallery.png (wf21, wf22, wf23, wf24)
"""

import os
import sys
from PIL import Image, ImageDraw, ImageFont

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUTPUT_DIR = os.path.join(ROOT_DIR, "output", "Tegaki", "Phase3F")


def get_font(size=20):
    try:
        return ImageFont.truetype("arial.ttf", size)
    except Exception:
        return ImageFont.load_default()


def build_zero_touch_gallery():
    images_info = [
        ("Workflow 21: Recurrent Cast 4-Panel (Zero-Touch)", "wf21_zero_touch_recurrent_cast.png"),
        ("Workflow 22: Multi-Scene Same Cast Oracle (Zero-Touch)", "wf22_zero_touch_multiscene.png"),
        ("Workflow 23: Progressive 4-Panel Authoring (Zero-Touch)", "wf23_zero_touch_progressive_4panel.png"),
        ("Workflow 24: Progressive SubScene Oracle (Zero-Touch)", "wf24_zero_touch_progressive_subscene.png"),
    ]

    loaded = []
    for title, fname in images_info:
        p = os.path.join(OUTPUT_DIR, fname)
        if os.path.exists(p):
            img = Image.open(p).convert("RGB")
            loaded.append((title, img))
        else:
            print(f"[WARN] Missing image: {p}")

    if not loaded:
        print("[ERROR] No images found for contact sheet.")
        return

    # Create 2x2 grid
    thumb_w, thumb_h = 512, 512
    margin = 30
    header_h = 60
    label_h = 40

    cols = 2
    rows = (len(loaded) + cols - 1) // cols

    sheet_w = cols * thumb_w + (cols + 1) * margin
    sheet_h = header_h + rows * (thumb_h + label_h) + (rows + 1) * margin

    bg_color = (245, 243, 240)  # futaba cream
    border_color = (180, 150, 130)
    text_color = (40, 30, 20)

    sheet = Image.new("RGB", (sheet_w, sheet_h), bg_color)
    draw = ImageDraw.Draw(sheet)

    title_font = get_font(24)
    label_font = get_font(16)

    draw.text((margin, 18), "Phase 3F: Zero-Touch Execution & Progressive Authoring Suite", fill=text_color, font=title_font)

    for idx, (title, img) in enumerate(loaded):
        r = idx // cols
        c = idx % cols
        x = margin + c * (thumb_w + margin)
        y = header_h + margin + r * (thumb_h + label_h + margin)

        # Resize keeping aspect ratio
        thumb = img.copy()
        thumb.thumbnail((thumb_w, thumb_h), Image.Resampling.LANCZOS)
        # Center in box
        bx = x + (thumb_w - thumb.width) // 2
        by = y + (thumb_h - thumb.height) // 2

        # Draw border
        draw.rectangle([bx - 1, by - 1, bx + thumb.width, by + thumb.height], outline=border_color, width=2)
        sheet.paste(thumb, (bx, by))

        # Label
        draw.text((x, y + thumb_h + 8), title, fill=text_color, font=label_font)

    out_path = os.path.join(OUTPUT_DIR, "phase3f_zero_touch_gallery.png")
    sheet.save(out_path, quality=95)
    print(f"[SUCCESS] Created contact sheet: {out_path}")


if __name__ == "__main__":
    build_zero_touch_gallery()
