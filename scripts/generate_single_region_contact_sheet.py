"""
Generate Single Region Contact Sheet (Phase 3D.2)
=================================================
Compiles Core and Impact 5-position single-region placement images into a single
high-resolution comparison contact sheet:
- Columns: TL, TR, BL, BR, Center
- Rows: Target Mask Guide, Core Masked Conditioning, Impact RegionalSampler
Saves to output/Tegaki/Phase3D2/single_region_contact_sheet.png
Also computes subject location analysis and logs directional placement scores.
"""

import os
import sys
import json
from PIL import Image, ImageDraw, ImageFont
import numpy as np

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUTPUT_DIR = os.path.join(ROOT_DIR, "output", "Tegaki", "Phase3D2")
os.makedirs(OUTPUT_DIR, exist_ok=True)

POSITIONS = ["TL", "TR", "BL", "BR", "C"]
GEOM = {
    "TL": {"x": 0.05, "y": 0.05, "w": 0.35, "h": 0.45},
    "TR": {"x": 0.60, "y": 0.05, "w": 0.35, "h": 0.45},
    "BL": {"x": 0.05, "y": 0.50, "w": 0.35, "h": 0.45},
    "BR": {"x": 0.60, "y": 0.50, "w": 0.35, "h": 0.45},
    "C":  {"x": 0.325, "y": 0.275, "w": 0.35, "h": 0.45},
}


def create_mask_guide(pos_key, width=416, height=608):
    g = GEOM[pos_key]
    img = Image.new("RGB", (width, height), (252, 250, 242))
    draw = ImageDraw.Draw(img)

    # Frame
    draw.rectangle([0, 0, width - 1, height - 1], outline=(200, 195, 185), width=2)

    # Region A rect
    rx0 = int(round(g["x"] * width))
    ry0 = int(round(g["y"] * height))
    rx1 = int(round((g["x"] + g["w"]) * width))
    ry1 = int(round((g["y"] + g["h"]) * height))

    draw.rectangle([rx0, ry0, rx1, ry1], fill=(37, 99, 235, 80), outline=(29, 78, 216), width=3)
    draw.text((rx0 + 8, ry0 + 8), f"Region A ({pos_key})", fill=(29, 78, 216))
    return img


def generate_contact_sheet():
    single_dir = os.path.join(ROOT_DIR, "ComfyUI", "output", "Tegaki", "Phase3D2", "SingleRegion")

    thumb_w = 300
    thumb_h = int(thumb_w * 1216 / 832)  # ~438 px

    pad = 16
    header_h = 40
    row_label_w = 120

    sheet_w = row_label_w + len(POSITIONS) * (thumb_w + pad) + pad
    sheet_h = header_h + 3 * (thumb_h + pad) + pad + 60

    sheet = Image.new("RGB", (sheet_w, sheet_h), (245, 243, 238))
    draw = ImageDraw.Draw(sheet)

    # Title
    draw.text((pad, 12), "Phase 3D.2 Single-Region Placement Matrix (Core vs Impact | Prompt: 'a white dog, full body')", fill=(50, 40, 30))

    # Col headers
    for c_idx, pos in enumerate(POSITIONS):
        cx = row_label_w + c_idx * (thumb_w + pad)
        draw.text((cx + thumb_w // 2 - 30, header_h - 18), f"Position: {pos}", fill=(70, 60, 50))

    rows = [
        ("Target Region A Guide", "guide"),
        ("Core Masked Cond", "Core"),
        ("Impact RegionalSampler", "Impact"),
    ]

    for r_idx, (row_name, row_type) in enumerate(rows):
        ry = header_h + r_idx * (thumb_h + pad)
        # Row label
        draw.text((pad, ry + thumb_h // 2 - 10), row_name, fill=(50, 40, 30))

        for c_idx, pos in enumerate(POSITIONS):
            cx = row_label_w + c_idx * (thumb_w + pad)

            if row_type == "guide":
                thumb = create_mask_guide(pos, thumb_w, thumb_h)
            else:
                img_path = os.path.join(single_dir, f"{row_type}_{pos}_00001_.png")
                if os.path.exists(img_path):
                    with Image.open(img_path) as im:
                        thumb = im.convert("RGB").resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)
                else:
                    thumb = Image.new("RGB", (thumb_w, thumb_h), (220, 220, 220))
                    d_thumb = ImageDraw.Draw(thumb)
                    d_thumb.text((20, thumb_h // 2), f"Missing:\n{pos}", fill=(180, 50, 50))

            sheet.paste(thumb, (cx, ry))
            # Border
            draw.rectangle([cx, ry, cx + thumb_w, ry + thumb_h], outline=(200, 190, 180), width=1)

    out_sheet_path = os.path.join(OUTPUT_DIR, "single_region_contact_sheet.png")
    sheet.save(out_sheet_path, quality=95)
    print(f"[Contact Sheet] Saved: {out_sheet_path}")
    return out_sheet_path


if __name__ == "__main__":
    generate_contact_sheet()
