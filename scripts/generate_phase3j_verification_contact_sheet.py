"""
Phase 3J: Verification Contact Sheet Generator
==============================================
Generates:
1. Sheet P: Base Semantic Contract Isolation (Legacy Base vs Background-Only Base)
2. Sheet Q: Character x Side Bias Matrix (Alice L / Alice R / Bob L / Bob R)
3. Sheet R: Two-Character Swap Matrix (Alice L / Bob R vs Bob L / Alice R)
4. Sheet S: Clean Per-Region Hint Evolution (PRH v1 BBox ON vs PRH v2 BBox OFF vs Swap)
5. Sheet T: Adaptive Shot Type Foundation (Full Body vs Half Body vs Bust Shot)
"""

import os
import sys
from PIL import Image, ImageDraw, ImageFont

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CANONICAL_DIR = os.path.join(ROOT_DIR, "output", "Tegaki", "Phase3J", "canonical")
OUTPUT_DIR = os.path.join(ROOT_DIR, "output", "Tegaki", "Phase3J")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def get_font(size=18, bold=False):
    try:
        fn = "arialbd.ttf" if bold else "arial.ttf"
        return ImageFont.truetype(fn, size)
    except Exception:
        return ImageFont.load_default()


def load_img(fn):
    p = os.path.join(CANONICAL_DIR, fn)
    if os.path.exists(p):
        return Image.open(p).convert("RGB")
    img = Image.new("RGB", (1024, 1024), (240, 235, 230))
    d = ImageDraw.Draw(img)
    d.text((350, 500), f"Missing: {fn}", fill=(200, 50, 50), font=get_font(24, bold=True))
    return img


def draw_panel_badge(draw, x, y, title, subtitle="", bg_color=(35, 25, 20, 240), border_color=(245, 130, 32), width=520):
    font_t = get_font(19, bold=True)
    font_s = get_font(13, bold=False)
    h = 56 if subtitle else 36
    draw.rectangle([x, y, x + width, y + h], fill=bg_color, outline=border_color, width=2)
    draw.text((x + 12, y + 6), title, fill=(255, 255, 255), font=font_t)
    if subtitle:
        draw.text((x + 12, y + 32), subtitle, fill=(210, 210, 210), font=font_s)


def generate_sheet_p():
    """Sheet P: Base Prompt Contract (2x1 Grid)"""
    print("Generating Sheet P (Base Semantic Contract Isolation)...")
    img_legacy = load_img("Cond01_LegacyBase_AliceL_BobR.png").resize((800, 800), Image.Resampling.LANCZOS)
    img_bgonly = load_img("Cond02_BgOnlyBase_AliceL_BobR.png").resize((800, 800), Image.Resampling.LANCZOS)

    canvas_w = 800 * 2 + 60
    canvas_h = 800 + 140
    sheet = Image.new("RGB", (canvas_w, canvas_h), (20, 18, 16))
    draw = ImageDraw.Draw(sheet)

    font_title = get_font(26, bold=True)
    draw.text((30, 20), "Sheet P: Phase 3J Base Semantic Contract Isolation (Legacy Base vs Background-Only Base)", fill=(245, 130, 32), font=font_title)
    font_sub = get_font(15, bold=False)
    draw.text((30, 52), "Seed 42 | Hyper12 | Staging: Alice Left [0.10], Bob Right [0.55] | Base-Only CN 0.75", fill=(200, 200, 200), font=font_sub)

    top_y = 80
    sheet.paste(img_legacy, (20, top_y))
    sheet.paste(img_bgonly, (800 + 40, top_y))

    draw_panel_badge(draw, 30, top_y + 10, "Legacy Base: 'two students standing'", "Subject count in Base conflicts with Regional attendance")
    draw_panel_badge(draw, 800 + 50, top_y + 10, "Canonical Base v2: 'empty school courtyard'", "Background-only Base: zero student/person keywords in Base Positive")

    out_path = os.path.join(OUTPUT_DIR, "Phase3J_Sheet_P_Base_Contract.png")
    sheet.save(out_path, quality=95)
    print(f"  Saved: {out_path}")


def generate_sheet_q():
    """Sheet Q: Character x Side Bias Matrix (2x2 Grid)"""
    print("Generating Sheet Q (Character x Side Bias Matrix)...")
    img_al = load_img("Cond03_AliceLeft_Hyper12.png").resize((768, 768), Image.Resampling.LANCZOS)
    img_ar = load_img("Cond04_AliceRight_Hyper12.png").resize((768, 768), Image.Resampling.LANCZOS)
    img_bl = load_img("Cond05_BobLeft_Hyper12.png").resize((768, 768), Image.Resampling.LANCZOS)
    img_br = load_img("Cond06_BobRight_Hyper12.png").resize((768, 768), Image.Resampling.LANCZOS)

    canvas_w = 768 * 2 + 60
    canvas_h = 768 * 2 + 140
    sheet = Image.new("RGB", (canvas_w, canvas_h), (20, 18, 16))
    draw = ImageDraw.Draw(sheet)

    font_title = get_font(26, bold=True)
    draw.text((30, 20), "Sheet Q: Phase 3J Single Character x Side Bias Matrix (Alice & Bob Left/Right)", fill=(245, 130, 32), font=font_title)
    font_sub = get_font(15, bold=False)
    draw.text((30, 52), "Seed 42 | Hyper12 | Background-Only Base | Investigating positional & identity preference", fill=(200, 200, 200), font=font_sub)

    top_y = 80
    sheet.paste(img_al, (20, top_y))
    sheet.paste(img_ar, (768 + 40, top_y))
    sheet.paste(img_bl, (20, top_y + 768 + 20))
    sheet.paste(img_br, (768 + 40, top_y + 768 + 20))

    draw_panel_badge(draw, 30, top_y + 10, "Cond 03: Alice Left Only (WF49)", "Target Area [0.10, 0.15, 0.35, 0.75]")
    draw_panel_badge(draw, 768 + 50, top_y + 10, "Cond 04: Alice Right Only (WF50)", "Target Area [0.55, 0.15, 0.35, 0.75]")
    draw_panel_badge(draw, 30, top_y + 768 + 30, "Cond 05: Bob Left Only (WF51)", "Target Area [0.10, 0.15, 0.35, 0.75]")
    draw_panel_badge(draw, 768 + 50, top_y + 768 + 30, "Cond 06: Bob Right Only (WF52)", "Target Area [0.55, 0.15, 0.35, 0.75]")

    out_path = os.path.join(OUTPUT_DIR, "Phase3J_Sheet_Q_Side_Bias_Matrix.png")
    sheet.save(out_path, quality=95)
    print(f"  Saved: {out_path}")


def generate_sheet_r():
    """Sheet R: Two-Character Swap Matrix (2x1 Grid)"""
    print("Generating Sheet R (Two-Character Swap Matrix)...")
    img_albr = load_img("Cond02_BgOnlyBase_AliceL_BobR.png").resize((800, 800), Image.Resampling.LANCZOS)
    img_blar = load_img("Cond07_TwoChar_BobL_AliceR_Hyper12.png").resize((800, 800), Image.Resampling.LANCZOS)

    canvas_w = 800 * 2 + 60
    canvas_h = 800 + 140
    sheet = Image.new("RGB", (canvas_w, canvas_h), (20, 18, 16))
    draw = ImageDraw.Draw(sheet)

    font_title = get_font(26, bold=True)
    draw.text((30, 20), "Sheet R: Phase 3J Two-Character Swap Matrix (Alice L / Bob R vs Bob L / Alice R)", fill=(245, 130, 32), font=font_title)
    font_sub = get_font(15, bold=False)
    draw.text((30, 52), "Seed 42 | Hyper12 | Background-Only Base | Comparing bidirectional spatial binding under base-only CN", fill=(200, 200, 200), font=font_sub)

    top_y = 80
    sheet.paste(img_albr, (20, top_y))
    sheet.paste(img_blar, (800 + 40, top_y))

    draw_panel_badge(draw, 30, top_y + 10, "Swap C1: Alice Left / Bob Right (WF48)", "Alice [0.10] + Bob [0.55] | Base-Only CN")
    draw_panel_badge(draw, 800 + 50, top_y + 10, "Swap C2: Bob Left / Alice Right", "Bob [0.10] + Alice [0.55] | Base-Only CN")

    out_path = os.path.join(OUTPUT_DIR, "Phase3J_Sheet_R_Swap_Matrix.png")
    sheet.save(out_path, quality=95)
    print(f"  Saved: {out_path}")


def generate_sheet_s():
    """Sheet S: Clean Per-Region Hint Evolution (3x1 Grid)"""
    print("Generating Sheet S (Clean Per-Region Hint Evolution)...")
    img_prh_on = load_img("Cond09_PRH_v1_BBoxON_BobL_AliceR.png").resize((600, 600), Image.Resampling.LANCZOS)
    img_prh_off = load_img("Cond10_PRH_v2_BBoxOFF_BobL_AliceR.png").resize((600, 600), Image.Resampling.LANCZOS)
    img_prh_swap = load_img("Cond11_PRH_v2_BBoxOFF_AliceL_BobR.png").resize((600, 600), Image.Resampling.LANCZOS)

    canvas_w = 600 * 3 + 80
    canvas_h = 600 + 140
    sheet = Image.new("RGB", (canvas_w, canvas_h), (20, 18, 16))
    draw = ImageDraw.Draw(sheet)

    font_title = get_font(26, bold=True)
    draw.text((30, 20), "Sheet S: Phase 3J Clean Per-Region Hint v2 Evolution & Attenuation", fill=(245, 130, 32), font=font_title)
    font_sub = get_font(15, bold=False)
    draw.text((30, 52), "Seed 42 | Hyper12 | Regional CN 0.35, end 0.60 | Evaluating box outline removal & swap", fill=(200, 200, 200), font=font_sub)

    top_y = 80
    sheet.paste(img_prh_on, (20, top_y))
    sheet.paste(img_prh_off, (600 + 40, top_y))
    sheet.paste(img_prh_swap, (600 * 2 + 60, top_y))

    draw_panel_badge(draw, 30, top_y + 10, "PRH-v1: BBox Outline ON", "Mannequin capsule with box outline -> Hallucination risk", width=500)
    draw_panel_badge(draw, 600 + 50, top_y + 10, "PRH-v2: BBox Outline OFF (WF53)", "Clean silhouette mannequin -> Doorframe artifact resolved", width=500)
    draw_panel_badge(draw, 600 * 2 + 70, top_y + 10, "PRH-v2 Swap: Alice L / Bob R", "Clean hint tested on reversed character placement", width=500)

    out_path = os.path.join(OUTPUT_DIR, "Phase3J_Sheet_S_PerRegionHint_Evolution.png")
    sheet.save(out_path, quality=95)
    print(f"  Saved: {out_path}")


def generate_sheet_t():
    """Sheet T: Adaptive Shot Type Foundation (3x1 Grid)"""
    print("Generating Sheet T (Adaptive Shot Type Foundation)...")
    img_full = load_img("Cond03_AliceLeft_Hyper12.png").resize((600, 600), Image.Resampling.LANCZOS)
    img_half = load_img("Cond13_ShotType_HalfBody_Alice.png").resize((600, 600), Image.Resampling.LANCZOS)
    img_bust = load_img("Cond14_ShotType_Bust_Alice.png").resize((600, 600), Image.Resampling.LANCZOS)

    canvas_w = 600 * 3 + 80
    canvas_h = 600 + 140
    sheet = Image.new("RGB", (canvas_w, canvas_h), (20, 18, 16))
    draw = ImageDraw.Draw(sheet)

    font_title = get_font(26, bold=True)
    draw.text((30, 20), "Sheet T: Phase 3J Adaptive Character Shot Type Foundation (Full / Half / Bust)", fill=(245, 130, 32), font=font_title)
    font_sub = get_font(15, bold=False)
    draw.text((30, 52), "Seed 42 | Hyper12 | Background-Only Base | Isolated character mannequin guide adaptation", fill=(200, 200, 200), font=font_sub)

    top_y = 80
    sheet.paste(img_full, (20, top_y))
    sheet.paste(img_half, (600 + 40, top_y))
    sheet.paste(img_bust, (600 * 2 + 60, top_y))

    draw_panel_badge(draw, 30, top_y + 10, "Shot Type: full_body", "Full height mannequin: head, torso, legs, feet", width=500)
    draw_panel_badge(draw, 600 + 50, top_y + 10, "Shot Type: half_body", "Waist up mannequin: head, torso, arms; lower 40% clean", width=500)
    draw_panel_badge(draw, 600 * 2 + 70, top_y + 10, "Shot Type: bust", "Chest up mannequin: head, shoulders, chest; lower 55% clean", width=500)

    out_path = os.path.join(OUTPUT_DIR, "Phase3J_Sheet_T_Shot_Types.png")
    sheet.save(out_path, quality=95)
    print(f"  Saved: {out_path}")


def generate_all_sheets():
    generate_sheet_p()
    generate_sheet_q()
    generate_sheet_r()
    generate_sheet_s()
    generate_sheet_t()
    print("\n[SUCCESS] All Phase 3J Verification Contact Sheets generated successfully.")


if __name__ == "__main__":
    generate_all_sheets()
