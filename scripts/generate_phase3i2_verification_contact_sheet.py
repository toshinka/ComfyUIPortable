"""
Phase 3I.2: Verification Contact Sheet Generator
================================================
Generates:
1. Sheet M: Causal Ablation Suite (Cond A vs Cond B vs Cond C vs Cond D)
2. Sheet N: Impact base_only_steps Ablation (Cond A: base_only=2 vs Cond E: base_only=0)
3. Sheet O: Regional Control Evolution (Cond A: Base-only vs Cond F: Shared Global 0.35 vs Cond G: Per-Region Hint 0.35)
"""

import os
import sys
from PIL import Image, ImageDraw, ImageFont

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CANONICAL_DIR = os.path.join(ROOT_DIR, "output", "Tegaki", "Phase3I2", "canonical")
OUTPUT_DIR = os.path.join(ROOT_DIR, "output", "Tegaki", "Phase3I2")
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
    # Fallback blank
    img = Image.new("RGB", (1024, 1024), (240, 235, 230))
    d = ImageDraw.Draw(img)
    d.text((400, 500), f"Missing: {fn}", fill=(200, 50, 50), font=get_font(24, bold=True))
    return img


def draw_panel_badge(draw, x, y, title, subtitle="", bg_color=(35, 25, 20, 240), border_color=(245, 130, 32)):
    font_t = get_font(20, bold=True)
    font_s = get_font(14, bold=False)
    w = 500
    h = 56 if subtitle else 36
    draw.rectangle([x, y, x + w, y + h], fill=bg_color, outline=border_color, width=2)
    draw.text((x + 12, y + 6), title, fill=(255, 255, 255), font=font_t)
    if subtitle:
        draw.text((x + 12, y + 32), subtitle, fill=(210, 210, 210), font=font_s)


def generate_sheet_m():
    """Sheet M: Causal Ablation (2x2 Grid)"""
    print("Generating Sheet M (Causal Ablation)...")
    img_a = load_img("CondA_Native20_CFG7_BaseOnly2.png").resize((768, 768), Image.Resampling.LANCZOS)
    img_b = load_img("CondB_Native12_CFG6_BaseOnly2.png").resize((768, 768), Image.Resampling.LANCZOS)
    img_c = load_img("CondC_Native20_CFG6_BaseOnly2.png").resize((768, 768), Image.Resampling.LANCZOS)
    img_d = load_img("CondD_Hyper12_CFG6_BaseOnly2.png").resize((768, 768), Image.Resampling.LANCZOS)

    canvas_w = 768 * 2 + 60
    canvas_h = 768 * 2 + 140
    sheet = Image.new("RGB", (canvas_w, canvas_h), (20, 18, 16))
    draw = ImageDraw.Draw(sheet)

    # Global Title
    font_title = get_font(26, bold=True)
    draw.text((30, 20), "Sheet M: Phase 3I.2 Causal Ablation Suite (Step / CFG / Hyper-SDXL LoRA)", fill=(245, 130, 32), font=font_title)
    font_sub = get_font(15, bold=False)
    draw.text((30, 52), "Fixed Seed: 42 | Prompt: Courtyard School | Target: Alice Left [0.10], Bob Right [0.55] | Base-Only CN", fill=(200, 200, 200), font=font_sub)

    # Paste panels
    top_y = 80
    sheet.paste(img_a, (20, top_y))
    sheet.paste(img_b, (768 + 40, top_y))
    sheet.paste(img_c, (20, top_y + 768 + 20))
    sheet.paste(img_d, (768 + 40, top_y + 768 + 20))

    # Badges
    draw_panel_badge(draw, 30, top_y + 10, "Cond A: Native Reference 20s", "Euler 20 steps, CFG 7.0, base_only=2, No LoRA -> FAIL (Alice 0/1)")
    draw_panel_badge(draw, 768 + 50, top_y + 10, "Cond B: Native Short 12s", "Euler 12 steps, CFG 6.0, base_only=2, No LoRA -> FAIL (Alice 0/1)")
    draw_panel_badge(draw, 30, top_y + 768 + 30, "Cond C: Native CFG 6.0 Control 20s", "Euler 20 steps, CFG 6.0, base_only=2, No LoRA -> FAIL (Alice 0/1)")
    draw_panel_badge(draw, 768 + 50, top_y + 768 + 30, "Cond D: Hyper 12s Control", "Euler 12 steps, CFG 6.0, Hyper-SDXL LoRA -> FAIL (Empty Wall)")

    out_path = os.path.join(OUTPUT_DIR, "Phase3I2_Sheet_M_Causal_Ablation.png")
    sheet.save(out_path, quality=95)
    print(f"  Saved: {out_path}")


def generate_sheet_n():
    """Sheet N: Impact base_only_steps Ablation (2x1 Grid)"""
    print("Generating Sheet N (base_only_steps Ablation)...")
    img_a = load_img("CondA_Native20_CFG7_BaseOnly2.png").resize((800, 800), Image.Resampling.LANCZOS)
    img_e = load_img("CondE_Native20_CFG7_BaseOnly0.png").resize((800, 800), Image.Resampling.LANCZOS)

    canvas_w = 800 * 2 + 60
    canvas_h = 800 + 140
    sheet = Image.new("RGB", (canvas_w, canvas_h), (20, 18, 16))
    draw = ImageDraw.Draw(sheet)

    font_title = get_font(26, bold=True)
    draw.text((30, 20), "Sheet N: Phase 3I.2 Impact RegionalSampler base_only_steps Ablation", fill=(245, 130, 32), font=font_title)
    font_sub = get_font(15, bold=False)
    draw.text((30, 52), "Evaluating whether initial Base-only sampling steps prevent regional character emergence or initialize latent", fill=(200, 200, 200), font=font_sub)

    top_y = 80
    sheet.paste(img_a, (20, top_y))
    sheet.paste(img_e, (800 + 40, top_y))

    draw_panel_badge(draw, 30, top_y + 10, "Cond A: base_only_steps = 2 (Standard)", "Background latent initialized; characters suppressed by strong prior -> FAIL")
    draw_panel_badge(draw, 800 + 50, top_y + 10, "Cond E: base_only_steps = 0 (Ablation)", "No base latent initialization; unmasked canvas fails -> PURE NOISE (HARMFUL)")

    out_path = os.path.join(OUTPUT_DIR, "Phase3I2_Sheet_N_BaseOnlySteps_Ablation.png")
    sheet.save(out_path, quality=95)
    print(f"  Saved: {out_path}")


def generate_sheet_o():
    """Sheet O: Regional Control Evolution (3x1 Grid)"""
    print("Generating Sheet O (Regional Control Evolution)...")
    img_a = load_img("CondA_Native20_CFG7_BaseOnly2.png").resize((600, 600), Image.Resampling.LANCZOS)
    img_f = load_img("CondF_SharedGlobal_035.png").resize((600, 600), Image.Resampling.LANCZOS)
    img_g = load_img("CondG_PerRegionHint_035.png").resize((600, 600), Image.Resampling.LANCZOS)

    canvas_w = 600 * 3 + 80
    canvas_h = 600 + 140
    sheet = Image.new("RGB", (canvas_w, canvas_h), (20, 18, 16))
    draw = ImageDraw.Draw(sheet)

    font_title = get_font(26, bold=True)
    draw.text((30, 20), "Sheet O: Phase 3I.2 Regional Control Evolution (Base-Only vs Shared Global vs Per-Region Hint)", fill=(245, 130, 32), font=font_title)
    font_sub = get_font(15, bold=False)
    draw.text((30, 52), "Euler 20s, CFG 7.0 | Comparing ControlNet injection strategies and artifact suppression", fill=(200, 200, 200), font=font_sub)

    top_y = 80
    sheet.paste(img_a, (20, top_y))
    sheet.paste(img_f, (600 + 40, top_y))
    sheet.paste(img_g, (600 * 2 + 60, top_y))

    draw_panel_badge(draw, 30, top_y + 10, "Cond A: Base-Only CN", "Regional samplers receive NO ControlNet; subject suppression -> FAIL")
    draw_panel_badge(draw, 600 + 50, top_y + 10, "Cond F: Shared Global CN (0.35)", "Full guide passed to all regions -> LITERAL MANNEQUINS / OVERCONSTRAINED")
    draw_panel_badge(draw, 600 * 2 + 70, top_y + 10, "Cond G: Per-Region Hint (0.35)", "Isolated character hints -> Wireframe artifact resolved, but wall prior dominates")

    out_path = os.path.join(OUTPUT_DIR, "Phase3I2_Sheet_O_Regional_Control_Evolution.png")
    sheet.save(out_path, quality=95)
    print(f"  Saved: {out_path}")


def main():
    generate_sheet_m()
    generate_sheet_n()
    generate_sheet_o()
    print("All Phase 3I.2 Contact Sheets generated successfully!")


if __name__ == "__main__":
    main()
