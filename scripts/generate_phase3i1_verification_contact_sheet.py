"""
Phase 3I.1: Verification Contact Sheet Generator
================================================
Generates:
1. Sheet J: Regional-Only vs ControlNet-Assisted (WF33 vs WF37, WF34 vs WF38)
2. Sheet K: Reference vs Fast Draft 12 (WF38 Reference 20s vs WF39 Fast-12 12s)
3. Sheet L: Base-only CN vs Regional CN Propagation (WF40 vs WF42)
4. Diagnostic Overlay Sheet: WF35-39 Subject Presence & Approximate Bounding Boxes
"""

import os
import sys
import glob
from PIL import Image, ImageDraw, ImageFont

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUTPUT_DIR = os.path.join(ROOT_DIR, "output", "Tegaki", "Phase3I1")
CANONICAL_3I1_DIR = os.path.join(OUTPUT_DIR, "canonical")
CANONICAL_3I_DIR = os.path.join(ROOT_DIR, "output", "Tegaki", "Phase3I", "canonical")
CANONICAL_3H_DIR = os.path.join(ROOT_DIR, "output", "Tegaki", "Phase3H", "canonical")

os.makedirs(OUTPUT_DIR, exist_ok=True)


def get_font(size=18, bold=False):
    try:
        fn = "arialbd.ttf" if bold else "arial.ttf"
        return ImageFont.truetype(fn, size)
    except Exception:
        return ImageFont.load_default()


def find_image(directory, pattern):
    files = glob.glob(os.path.join(directory, pattern))
    return sorted(files)[-1] if files else None


def draw_header_badge(draw, x, y, title, subtitle="", bg_color=(40, 30, 20, 230), text_color=(255, 255, 255, 255)):
    font_t = get_font(18, bold=True)
    font_s = get_font(13, bold=False)
    w = 480
    h = 50 if subtitle else 32
    draw.rectangle([x, y, x + w, y + h], fill=bg_color, outline=(245, 130, 32, 255), width=2)
    draw.text((x + 10, y + 6), title, fill=text_color, font=font_t)
    if subtitle:
        draw.text((x + 10, y + 28), subtitle, fill=(220, 220, 220, 255), font=font_s)


def draw_box(draw, img_w, img_h, norm_box, outline_color, label, label_bg):
    font = get_font(14, bold=True)
    x0 = int(norm_box[0] * img_w)
    y0 = int(norm_box[1] * img_h)
    w = int(norm_box[2] * img_w)
    h = int(norm_box[3] * img_h)
    x1 = x0 + w
    y1 = y0 + h
    draw.rectangle([x0, y0, x1, y1], outline=outline_color, width=3)
    bw = len(label) * 9 + 12
    draw.rectangle([x0, y0 - 20, x0 + bw, y0], fill=label_bg)
    draw.text((x0 + 4, y0 - 18), label, fill=(255, 255, 255), font=font)


def generate_sheet_j():
    """Sheet J: Regional-only vs ControlNet (WF33 vs WF37, WF34 vs WF38)"""
    p33 = os.path.join(CANONICAL_3H_DIR, "wf33_authoring_alice_left_bob_right.png")
    p37 = find_image(CANONICAL_3I_DIR, "*WF37*")
    p34 = os.path.join(CANONICAL_3H_DIR, "wf34_authoring_alice_right_bob_left.png")
    p38 = find_image(CANONICAL_3I_DIR, "*WF38*")

    target_size = (600, 600)
    canvas_w = 1260
    canvas_h = 1380
    sheet = Image.new("RGB", (canvas_w, canvas_h), (248, 246, 240))
    draw = ImageDraw.Draw(sheet)

    # Title header
    draw.rectangle([0, 0, canvas_w, 60], fill=(45, 35, 25))
    draw.text((30, 15), "Sheet J: Regional-Only vs ControlNet-Assisted Layout Ablation", fill=(245, 130, 32), font=get_font(22, bold=True))

    panels = [
        ("WF33: Regional-Only (Alice Left, Bob Right)", "Euler 20s | No ControlNet | Shrinkage / Drift", p33, 20, 80),
        ("WF37: ControlNet-Assisted (Alice Left, Bob Right)", "Euler 20s | CN AnyTest 0.75 | Bob Present, Alice Missing", p37, 640, 80),
        ("WF34: Regional-Only (Alice Right, Bob Left)", "Euler 20s | No ControlNet | Swapped Identity Bleed", p34, 20, 720),
        ("WF38: ControlNet-Assisted (Alice Right, Bob Left)", "Euler 20s | CN AnyTest 0.75 | Bob Present, Alice Missing", p38, 640, 720)
    ]

    for title, subtitle, path, px, py in panels:
        if path and os.path.exists(path):
            img = Image.open(path).convert("RGB").resize(target_size, Image.Resampling.LANCZOS)
            sheet.paste(img, (px, py + 45))
        else:
            draw.rectangle([px, py + 45, px + target_size[0], py + 45 + target_size[1]], fill=(220, 220, 220))
            draw.text((px + 50, py + 200), f"Image not found:\n{path}", fill=(100, 100, 100), font=get_font(16))
        draw_header_badge(draw, px, py, title, subtitle)

    out_path = os.path.join(OUTPUT_DIR, "sheet_j_regional_only_vs_controlnet.png")
    sheet.save(out_path, quality=95)
    print(f"Generated: {out_path}")


def generate_sheet_k():
    """Sheet K: WF38 Reference 20s vs WF39 Fast-12"""
    p38 = find_image(CANONICAL_3I_DIR, "*WF38*")
    p39 = find_image(CANONICAL_3I_DIR, "*WF39*")

    target_size = (700, 700)
    canvas_w = 1460
    canvas_h = 840
    sheet = Image.new("RGB", (canvas_w, canvas_h), (248, 246, 240))
    draw = ImageDraw.Draw(sheet)

    # Title header
    draw.rectangle([0, 0, canvas_w, 60], fill=(45, 35, 25))
    draw.text((30, 15), "Sheet K: Reference 20-Step vs Fast Draft 12-Step Regression (Swapped Alice Right, Bob Left)", fill=(245, 130, 32), font=get_font(22, bold=True))

    panels = [
        ("WF38: Reference 20s (Euler, CFG 7.0)", "48.08s | CN 0.75 | Bob Present (Far-Left), Alice MISSING", p38, 20, 80, (200, 40, 40)),
        ("WF39: Fast Draft 12s (Hyper-SDXL, CFG 6.0)", "30.08s (1.60x Speedup) | BOTH Bob & Alice PRESENT & LOCKED", p39, 740, 80, (34, 139, 34))
    ]

    for title, subtitle, path, px, py, status_col in panels:
        if path and os.path.exists(path):
            img = Image.open(path).convert("RGB").resize(target_size, Image.Resampling.LANCZOS)
            sheet.paste(img, (px, py + 45))
        else:
            draw.rectangle([px, py + 45, px + target_size[0], py + 45 + target_size[1]], fill=(220, 220, 220))
            draw.text((px + 50, py + 200), f"Image not found:\n{path}", fill=(100, 100, 100), font=get_font(16))
        draw_header_badge(draw, px, py, title, subtitle, bg_color=(40, 30, 20, 230), text_color=(255, 255, 255))
        # Status pill
        draw.rectangle([px + 520, py + 8, px + 680, py + 38], fill=status_col)
        status_text = "VISUAL FAIL" if "WF38" in title else "VISUAL PASS"
        draw.text((px + 535, py + 14), status_text, fill=(255, 255, 255), font=get_font(14, bold=True))

    out_path = os.path.join(OUTPUT_DIR, "sheet_k_reference_vs_fast12.png")
    sheet.save(out_path, quality=95)
    print(f"Generated: {out_path}")


def generate_sheet_l():
    """Sheet L: Base-only CN vs Regional CN Propagation (WF40 vs WF42)"""
    p40 = find_image(CANONICAL_3I1_DIR, "*WF40*")
    p42 = find_image(CANONICAL_3I1_DIR, "*WF42*")

    target_size = (700, 700)
    canvas_w = 1460
    canvas_h = 840
    sheet = Image.new("RGB", (canvas_w, canvas_h), (248, 246, 240))
    draw = ImageDraw.Draw(sheet)

    # Title header
    draw.rectangle([0, 0, canvas_w, 60], fill=(45, 35, 25))
    draw.text((30, 15), "Sheet L: ControlNet Conditioning Propagation A/B (Base-Only vs Regional Propagation)", fill=(245, 130, 32), font=get_font(22, bold=True))

    panels = [
        ("WF40: Base-Only ControlNet (Current Default)", "Euler 20s | CN in Base Sampler only | Regional Prompts unguided", p40, 20, 80),
        ("WF42: Regional ControlNet Propagation (Prototype)", "Euler 20s | CN cloned to Regional Prompts | Synchronous regional guidance", p42, 740, 80)
    ]

    for title, subtitle, path, px, py in panels:
        if path and os.path.exists(path):
            img = Image.open(path).convert("RGB").resize(target_size, Image.Resampling.LANCZOS)
            sheet.paste(img, (px, py + 45))
        else:
            draw.rectangle([px, py + 45, px + target_size[0], py + 45 + target_size[1]], fill=(220, 220, 220))
            draw.text((px + 50, py + 200), f"Image not found:\n{path}", fill=(100, 100, 100), font=get_font(16))
        draw_header_badge(draw, px, py, title, subtitle)

    out_path = os.path.join(OUTPUT_DIR, "sheet_l_base_only_vs_regional_propagation.png")
    sheet.save(out_path, quality=95)
    print(f"Generated: {out_path}")


def generate_diagnostic_overlay():
    """Diagnostic Overlay: WF35-WF39 with expected vs observed bounding boxes"""
    cases = [
        ("WF35", "White Dog (TL wireframe)", find_image(CANONICAL_3I_DIR, "*WF35*"), [
            {"label": "Target: Dog [0.10, 0.10, 0.40, 0.40]", "box": [0.10, 0.10, 0.30, 0.30], "color": (220, 20, 60), "type": "expected"},
            {"label": "Observed: Empty Room (MISSING)", "box": None, "color": None, "type": "missing"}
        ], "FAIL"),
        ("WF36", "Alice Tall Portrait", find_image(CANONICAL_3I_DIR, "*WF36*"), [
            {"label": "Target: Alice [0.25, 0.15, 0.50, 0.75]", "box": [0.25, 0.15, 0.50, 0.75], "color": (220, 20, 60), "type": "expected"},
            {"label": "Observed: Flat Grey (MISSING)", "box": None, "color": None, "type": "missing"}
        ], "FAIL"),
        ("WF37", "Alice Left, Bob Right", find_image(CANONICAL_3I_DIR, "*WF37*"), [
            {"label": "Target: Alice Left", "box": [0.05, 0.15, 0.42, 0.70], "color": (220, 20, 60), "type": "expected"},
            {"label": "Target: Bob Right", "box": [0.53, 0.15, 0.42, 0.70], "color": (30, 136, 229), "type": "expected"},
            {"label": "Observed: Bob (Center-Right)", "box": [0.45, 0.12, 0.40, 0.85], "color": (46, 139, 87), "type": "observed"},
            {"label": "Alice MISSING", "box": None, "color": None, "type": "missing"}
        ], "FAIL"),
        ("WF38", "Bob Left, Alice Right Swapped", find_image(CANONICAL_3I_DIR, "*WF38*"), [
            {"label": "Target: Bob Left", "box": [0.05, 0.15, 0.42, 0.70], "color": (30, 136, 229), "type": "expected"},
            {"label": "Target: Alice Right", "box": [0.53, 0.15, 0.42, 0.70], "color": (220, 20, 60), "type": "expected"},
            {"label": "Observed: Bob (Far-Left)", "box": [0.00, 0.10, 0.35, 0.88], "color": (46, 139, 87), "type": "observed"},
            {"label": "Alice MISSING", "box": None, "color": None, "type": "missing"}
        ], "FAIL"),
        ("WF39", "Fast-12 Swapped Alice Right, Bob Left", find_image(CANONICAL_3I_DIR, "*WF39*"), [
            {"label": "Target: Bob Left", "box": [0.05, 0.15, 0.42, 0.70], "color": (30, 136, 229), "type": "expected"},
            {"label": "Target: Alice Right", "box": [0.53, 0.15, 0.42, 0.70], "color": (220, 20, 60), "type": "expected"},
            {"label": "Observed: Bob (Left)", "box": [0.08, 0.12, 0.40, 0.85], "color": (46, 139, 87), "type": "observed"},
            {"label": "Observed: Alice (Right)", "box": [0.55, 0.14, 0.38, 0.84], "color": (245, 130, 32), "type": "observed"}
        ], "PASS")
    ]

    panel_w = 400
    panel_h = 400
    canvas_w = 2100
    canvas_h = 560
    sheet = Image.new("RGB", (canvas_w, canvas_h), (248, 246, 240))
    draw = ImageDraw.Draw(sheet)

    # Title header
    draw.rectangle([0, 0, canvas_w, 50], fill=(45, 35, 25))
    draw.text((20, 12), "Phase 3I Diagnostic Overlay: Expected Staging Boxes (Dashed/Outline) vs Observed Subjects", fill=(245, 130, 32), font=get_font(20, bold=True))

    for idx, (cid, desc, path, annotations, status) in enumerate(cases):
        px = 20 + idx * 415
        py = 70

        if path and os.path.exists(path):
            img = Image.open(path).convert("RGB").resize((panel_w, panel_h), Image.Resampling.LANCZOS)
            img_draw = ImageDraw.Draw(img)

            # Draw annotations onto image
            for ann in annotations:
                if ann["box"]:
                    col = ann["color"]
                    draw_box(img_draw, panel_w, panel_h, ann["box"], col, ann["label"], col)

            sheet.paste(img, (px, py + 35))
        else:
            draw.rectangle([px, py + 35, px + panel_w, py + 35 + panel_h], fill=(220, 220, 220))
            draw.text((px + 20, py + 150), f"Not found:\n{path}", fill=(100, 100, 100), font=get_font(14))

        # Header pill
        bg_col = (34, 139, 34) if status == "PASS" else (180, 40, 40)
        draw.rectangle([px, py, px + panel_w, py + 30], fill=(50, 40, 30))
        draw.text((px + 8, py + 6), f"{cid}: {desc}", fill=(255, 255, 255), font=get_font(13, bold=True))
        draw.rectangle([px + panel_w - 70, py + 3, px + panel_w - 5, py + 27], fill=bg_col)
        draw.text((px + panel_w - 60, py + 7), status, fill=(255, 255, 255), font=get_font(12, bold=True))

    out_path = os.path.join(OUTPUT_DIR, "sheet_diagnostic_overlay_wf35_39.png")
    sheet.save(out_path, quality=95)
    print(f"Generated: {out_path}")


def generate_all_sheets():
    generate_sheet_j()
    generate_sheet_k()
    generate_sheet_l()
    generate_diagnostic_overlay()


if __name__ == "__main__":
    generate_all_sheets()
