"""
Generate Recurrent Cast Contact Sheet (Phase 3E)
================================================
Crops the 4 panels from manga_recurrent_cast_4panel.png and creates
a comprehensive review contact sheet:
- Full 4-panel page on the left
- 4 individual cropped panels with attendance and acting annotations on the right
"""

import os
import sys
from PIL import Image, ImageDraw, ImageFont

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUTPUT_DIR = os.path.join(ROOT_DIR, "output", "Tegaki", "Phase3E")
SOURCE_IMAGE = os.path.join(OUTPUT_DIR, "manga_recurrent_cast_4panel.png")
TARGET_SHEET = os.path.join(OUTPUT_DIR, "recurrent_cast_contact_sheet.png")


def generate_contact_sheet():
    if not os.path.exists(SOURCE_IMAGE):
        raise FileNotFoundError(f"Source image not found: {SOURCE_IMAGE}")

    full_img = Image.open(SOURCE_IMAGE).convert("RGB")
    W, H = full_img.size

    # Panel crops based on 4-grid layout (1024x1024)
    # p1: [0.05*W, 0.05*H, 0.48*W, 0.48*H]
    # p2: [0.52*W, 0.05*H, 0.95*W, 0.48*H]
    # p3: [0.05*W, 0.52*H, 0.48*W, 0.95*H]
    # p4: [0.52*W, 0.52*H, 0.95*W, 0.95*H]
    crop_boxes = {
        "p1": (int(0.04 * W), int(0.04 * H), int(0.49 * W), int(0.49 * H)),
        "p2": (int(0.51 * W), int(0.04 * H), int(0.96 * W), int(0.49 * H)),
        "p3": (int(0.04 * W), int(0.51 * H), int(0.49 * W), int(0.96 * H)),
        "p4": (int(0.51 * W), int(0.51 * H), int(0.96 * W), int(0.96 * H)),
    }

    crops = {pid: full_img.crop(box) for pid, box in crop_boxes.items()}

    panel_meta = {
        "p1": {
            "title": "Panel 1: Handshake (Alice + Bob)",
            "cast": "Attendance: Alice (Left) + Bob (Right)",
            "acting": "Action: Friendly handshake, facing each other, smiling"
        },
        "p2": {
            "title": "Panel 2: Solo Flower Bed (Alice ONLY)",
            "cast": "Attendance: Alice ONLY (Bob ABSENT)",
            "acting": "Action: Watering flowers with watering can, cheerful"
        },
        "p3": {
            "title": "Panel 3: Solo Garden Path (Bob ONLY)",
            "cast": "Attendance: Bob ONLY (Alice ABSENT)",
            "acting": "Action: Carrying large potted plant with both hands"
        },
        "p4": {
            "title": "Panel 4: School Gate Conflict (Alice + Bob)",
            "cast": "Attendance: Alice (Left) + Bob (Right)",
            "acting": "Action: Arguing intensely, both looking away, angry/annoyed"
        }
    }

    # Canvas dimensions
    # Left: Full page (1024x1024)
    # Right: 4 rows of crops (each crop scaled to 240x240) + text annotations
    header_h = 90
    crop_display_size = 240
    right_col_w = 640
    sheet_w = W + right_col_w + 80
    sheet_h = max(H, crop_display_size * 4 + 60) + header_h + 40

    sheet = Image.new("RGB", (sheet_w, sheet_h), (245, 243, 238))
    draw = ImageDraw.Draw(sheet)

    try:
        font_title = ImageFont.truetype("arial.ttf", 30)
        font_sub = ImageFont.truetype("arial.ttf", 18)
        font_crop_title = ImageFont.truetype("arial.ttf", 20)
        font_crop_desc = ImageFont.truetype("arial.ttf", 15)
    except Exception:
        font_title = ImageFont.load_default()
        font_sub = ImageFont.load_default()
        font_crop_title = ImageFont.load_default()
        font_crop_desc = ImageFont.load_default()

    # Header
    draw.text((30, 20), "Phase 3E: Recurrent Cast 4-Panel Verification Contact Sheet", fill=(40, 30, 20), font=font_title)
    draw.text((30, 58), "Impact Regional Backend + CAST_SPEC + Panel-Specific Acting Isolation (Seed=42)", fill=(100, 90, 80), font=font_sub)

    # Left Column: Full Page
    draw.text((30, header_h), "Full 4-Panel Manga Page (1024x1024)", fill=(40, 30, 20), font=font_crop_title)
    sheet.paste(full_img, (30, header_h + 30))
    draw.rectangle([30, header_h + 30, 30 + W, header_h + 30 + H], outline=(60, 50, 40), width=2)

    # Right Column: 4 Crops
    right_x = W + 60
    y_offset = header_h + 30
    row_h = crop_display_size + 15

    for idx, pid in enumerate(["p1", "p2", "p3", "p4"]):
        c_img = crops[pid].resize((crop_display_size, crop_display_size), Image.Resampling.LANCZOS)
        row_y = y_offset + idx * row_h

        # Paste crop
        sheet.paste(c_img, (right_x, row_y))
        draw.rectangle([right_x, row_y, right_x + crop_display_size, row_y + crop_display_size], outline=(60, 50, 40), width=2)

        # Draw annotations
        meta = panel_meta[pid]
        text_x = right_x + crop_display_size + 20
        draw.text((text_x, row_y + 10), meta["title"], fill=(30, 70, 140), font=font_crop_title)
        draw.text((text_x, row_y + 42), meta["cast"], fill=(40, 110, 50), font=font_crop_desc)
        draw.text((text_x, row_y + 68), meta["acting"], fill=(70, 60, 50), font=font_crop_desc)

    sheet.save(TARGET_SHEET, quality=95)
    print(f"[ContactSheet] Successfully generated: {TARGET_SHEET}")
    return TARGET_SHEET


if __name__ == "__main__":
    generate_contact_sheet()
