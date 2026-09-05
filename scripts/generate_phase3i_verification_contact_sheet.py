"""
Phase 3I Verification Contact Sheet & Evaluation Overlay Generator
==================================================================
Generates diagnostic contact sheets with 4-panel / 3-panel visualization:
  [ Layout Guide / Target Map ] | [ Final Output ] | [ Evaluation Overlay ]

Generates:
1. Sheet H: ControlNet AnyTest Baseline & Character Scale Locking (WF35, WF36)
2. Sheet I: Production Authoring Staging Swap & Fast Draft Regression (WF37, WF38, WF39)
"""

import os
import sys
import json
import torch
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CUSTOM_NODES_DIR = os.path.join(ROOT_DIR, "custom_nodes_custom")
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
if CUSTOM_NODES_DIR not in sys.path:
    sys.path.insert(0, CUSTOM_NODES_DIR)

from tegaki_manga_nodes.layout_guide_generator import TegakiMangaLayoutGuideGenerator

OUTPUT_DIR = os.path.join(ROOT_DIR, "output", "Tegaki", "Phase3I")
CANONICAL_DIR = os.path.join(OUTPUT_DIR, "canonical")
PHASE3H_DIR = os.path.join(ROOT_DIR, "output", "Tegaki", "Phase3H", "canonical")


def get_font(size=20):
    for fn in ["arial.ttf", "segoeui.ttf", "tahoma.ttf"]:
        try:
            return ImageFont.truetype(fn, size)
        except Exception:
            pass
    return ImageFont.load_default()


def find_image_by_prefix(dir_path: str, prefix: str) -> str:
    if not os.path.exists(dir_path):
        return ""
    matches = [
        os.path.join(dir_path, f)
        for f in os.listdir(dir_path)
        if f.startswith(prefix) and f.endswith(".png")
    ]
    if matches:
        matches.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        return matches[0]
    return os.path.join(dir_path, f"{prefix}_00001_.png")



def render_layout_guide_pil(scene_plan: dict, width: int = 1024, height: int = 1024, guide_mode: str = "mannequin_capsule") -> Image.Image:
    """Invokes TegakiMangaLayoutGuideGenerator directly to render the exact guide image used by ControlNet."""
    gen = TegakiMangaLayoutGuideGenerator()
    tensor_img, _, _ = gen.generate_guide(
        scene_plan=scene_plan,
        target_panel_id=1,
        guide_style=guide_mode,
        color_mode="Black on White",
        line_thickness=4,
        include_panel_border=True,
        width=width,
        height=height
    )
    # tensor shape (1, H, W, 3) in [0, 1]
    np_img = (tensor_img[0].cpu().numpy() * 255.0).astype(np.uint8)
    return Image.fromarray(np_img)


def create_region_map(canvas_w: int, canvas_h: int, regions: list, guide_img: Image.Image = None) -> Image.Image:
    """
    Creates a schematic Target Region Map composited with the Layout Guide if provided.
    regions: list of dict(label, bounds=[x, y, w, h], color_rgb)
    """
    if guide_img is not None:
        base = guide_img.copy().convert("RGB").resize((canvas_w, canvas_h), Image.Resampling.LANCZOS)
    else:
        base = Image.new("RGB", (canvas_w, canvas_h), (250, 248, 245))

    draw = ImageDraw.Draw(base)

    # Grid background if no guide image
    if guide_img is None:
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
        odraw.rectangle([rx0, ry0, rx1, ry1], fill=(color[0], color[1], color[2], 50), outline=(color[0], color[1], color[2], 240), width=3)
        base.paste(overlay, (0, 0), overlay)

        # Label with dark outline for readability
        label_text = f"{r['label']}\n[{bx:.2f}, {by:.2f}, {bw:.2f}, {bh:.2f}]"
        draw.text((rx0 + 11, ry0 + 11), label_text, fill=(255, 255, 255), font=font)
        draw.text((rx0 + 10, ry0 + 10), label_text, fill=(30, 20, 10), font=font)

    return base


def create_evaluation_overlay(base_img: Image.Image, regions: list) -> Image.Image:
    """
    Overlays semi-transparent region boundaries and silhouette containment indicators.
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

        odraw.rectangle([rx0, ry0, rx1, ry1], fill=(color[0], color[1], color[2], 45), outline=(color[0], color[1], color[2], 255), width=3)
        tag = f"Locked: {r['label']}"
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
    scene_plan: dict = None,
    guide_mode: str = "mannequin_capsule",
    thumb_size: int = 400
) -> Image.Image:
    """Creates a single diagnostic row: [ Layout Guide / Target Map ] | [ Final Output ] | [ Evaluation Overlay ]"""
    if os.path.exists(raw_img_path):
        raw_img = Image.open(raw_img_path).convert("RGB")
    else:
        raw_img = Image.new("RGB", (thumb_size, thumb_size), (240, 230, 230))
        d = ImageDraw.Draw(raw_img)
        d.text((20, 20), f"MISSING:\n{os.path.basename(raw_img_path)}", fill=(180, 40, 40), font=get_font(16))

    guide_img = None
    if scene_plan:
        try:
            guide_img = render_layout_guide_pil(scene_plan, raw_img.width, raw_img.height, guide_mode)
        except Exception as e:
            print(f"Warning: Failed to render layout guide: {e}")

    region_map = create_region_map(raw_img.width, raw_img.height, regions, guide_img)
    overlay_img = create_evaluation_overlay(raw_img, regions)

    margin = 20
    header_h = 65
    row_w = 3 * thumb_size + 4 * margin
    row_h = thumb_size + header_h + 2 * margin

    row_img = Image.new("RGB", (row_w, row_h), (248, 246, 242))
    draw = ImageDraw.Draw(row_img)

    title_font = get_font(18)
    sub_font = get_font(13)
    panel_tag_font = get_font(12)

    draw.text((margin, 10), title, fill=(35, 25, 15), font=title_font)
    draw.text((margin, 35), subtitle, fill=(110, 95, 85), font=sub_font)

    panels = [
        ("1. Layout Guide / Target Region Map", region_map),
        ("2. Final Generated Output", raw_img),
        ("3. ControlNet Boundary Alignment Overlay", overlay_img)
    ]

    for idx, (ptag, pimg) in enumerate(panels):
        px = margin + idx * (thumb_size + margin)
        py = header_h + 20

        thumb = pimg.copy()
        thumb.thumbnail((thumb_size, thumb_size), Image.Resampling.LANCZOS)
        bx = px + (thumb_size - thumb.width) // 2
        by = py + (thumb_size - thumb.height) // 2

        draw.rectangle([bx - 1, by - 1, bx + thumb.width, by + thumb.height], outline=(190, 170, 150), width=1)
        row_img.paste(thumb, (bx, by))
        draw.text((px, py - 18), ptag, fill=(80, 60, 40), font=panel_tag_font)

    return row_img


def build_sheet_h():
    """Sheet H: ControlNet AnyTest Baseline & Scale Locking"""
    print("\n[ContactSheet] Building Sheet H (ControlNet AnyTest & Scale Locking)...")

    # WF35: Dog Top-Left Box Wireframe
    plan_wf35 = {
        "panel_box": [0.05, 0.05, 0.90, 0.90],
        "staging_boxes": [
            {"character": "white dog", "staging_box": [0.05, 0.05, 0.45, 0.45]}
        ]
    }
    regions_wf35 = [{"label": "Region A: Dog (Wireframe)", "bounds": [0.05, 0.05, 0.45, 0.45], "color": (245, 130, 32)}]

    # WF36: Alice Tall Portrait Capsule Mannequin
    plan_wf36 = {
        "panel_box": [0.05, 0.05, 0.90, 0.90],
        "staging_boxes": [
            {"character": "alice", "staging_box": [0.15, 0.08, 0.70, 0.84]}
        ]
    }
    regions_wf36 = [{"label": "Alice (Locked Scale Portrait)", "bounds": [0.15, 0.08, 0.70, 0.84], "color": (245, 130, 32)}]

    # Reference WF29 from Phase 3H (Dog TL without ControlNet)
    row0 = create_3panel_row(
        title="Phase 3H Baseline Reference: WF29 (Dog TL, Pure Latent Masking, NO ControlNet)",
        subtitle="Geometry: [0.05, 0.05, 0.45, 0.45] | Finding: Subject exclusive but lacks physical lineart/pose guidance",
        raw_img_path=os.path.join(PHASE3H_DIR, "wf29_canonical_single_a_top_left_exclusive_base.png"),
        regions=regions_wf35
    )

    # WF35: AnyTest Baseline
    wf35_img = find_image_by_prefix(CANONICAL_DIR, "WF35_Phase3I_ControlNet_35_AnyTest_Baseline")
    row1 = create_3panel_row(
        title="Workflow 35: AnyTest v4 Native Baseline (Wireframe Layout Guide)",
        subtitle="Geometry: [0.05, 0.05, 0.45, 0.45] | CN: AnyTest v4 Illustrious (Weight: 0.80, End: 0.80)",
        raw_img_path=wf35_img,
        regions=regions_wf35,
        scene_plan=plan_wf35,
        guide_mode="box_wireframe"
    )

    # WF36: Scale Locking
    wf36_img = find_image_by_prefix(CANONICAL_DIR, "WF36_Phase3I_ControlNet_36_ScaleLock_Single_Alice")
    row2 = create_3panel_row(
        title="Workflow 36: ControlNet Scale Lock (Alice Tall Portrait Capsule Mannequin)",
        subtitle="Staging Box: [0.15, 0.08, 0.70, 0.84] | Resolution: Case B perspective shrinkage resolved!",
        raw_img_path=wf36_img,
        regions=regions_wf36,
        scene_plan=plan_wf36,
        guide_mode="mannequin_capsule"
    )

    header_h = 70
    sheet_w = row0.width
    sheet_h = header_h + row0.height + row1.height + row2.height + 30

    sheet = Image.new("RGB", (sheet_w, sheet_h), (245, 242, 237))
    draw = ImageDraw.Draw(sheet)
    draw.text((25, 20), "Sheet H: Phase 3I ControlNet AnyTest & Scale Locking Diagnostics (WF35, WF36)", fill=(35, 25, 15), font=get_font(24))
    draw.line([(25, 58), (sheet_w - 25, 58)], fill=(210, 105, 30), width=2)

    y = header_h
    for r in [row0, row1, row2]:
        sheet.paste(r, (0, y))
        y += r.height + 10

    out_path = os.path.join(OUTPUT_DIR, "sheet_h_controlnet_scale_locking.png")
    sheet.save(out_path, quality=95)
    print(f"[SUCCESS] Saved Sheet H: {out_path}")


def build_sheet_i():
    """Sheet I: Production Authoring Staging Swap & Fast Draft Regression"""
    print("\n[ContactSheet] Building Sheet I (Staging Swap & Fast Draft Regression)...")

    # WF37: Alice Left, Bob Right
    plan_wf37 = {
        "panel_box": [0.05, 0.05, 0.90, 0.90],
        "staging_boxes": [
            {"character": "alice", "staging_box": [0.08, 0.16, 0.40, 0.68]},
            {"character": "bob", "staging_box": [0.52, 0.16, 0.40, 0.68]}
        ]
    }
    regions_wf37 = [
        {"label": "Alice (Left)", "bounds": [0.08, 0.16, 0.40, 0.68], "color": (245, 130, 32)},
        {"label": "Bob (Right)", "bounds": [0.52, 0.16, 0.40, 0.68], "color": (37, 99, 235)}
    ]

    # WF38 & WF39: Alice Right, Bob Left (Swapped)
    plan_wf38 = {
        "panel_box": [0.05, 0.05, 0.90, 0.90],
        "staging_boxes": [
            {"character": "alice", "staging_box": [0.52, 0.16, 0.40, 0.68]},
            {"character": "bob", "staging_box": [0.08, 0.16, 0.40, 0.68]}
        ]
    }
    regions_wf38 = [
        {"label": "Alice (Right)", "bounds": [0.52, 0.16, 0.40, 0.68], "color": (245, 130, 32)},
        {"label": "Bob (Left)", "bounds": [0.08, 0.16, 0.40, 0.68], "color": (37, 99, 235)}
    ]

    wf37_img = find_image_by_prefix(CANONICAL_DIR, "WF37_Phase3I_Authoring_37_AliceLeft_BobRight_CNAssist")
    row1 = create_3panel_row(
        title="Workflow 37: Authoring Pipeline (Alice Left, Bob Right) + ControlNet Assist",
        subtitle="Alice: [0.08, 0.16, 0.40, 0.68] | Bob: [0.52, 0.16, 0.40, 0.68] | Profile: Reference 20 (CFG 7.0)",
        raw_img_path=wf37_img,
        regions=regions_wf37,
        scene_plan=plan_wf37,
        guide_mode="mannequin_capsule"
    )

    wf38_img = find_image_by_prefix(CANONICAL_DIR, "WF38_Phase3I_Authoring_38_AliceRight_BobLeft_CNAssist")
    row2 = create_3panel_row(
        title="Workflow 38: Authoring Pipeline (Alice Right, Bob Left SWAP) + ControlNet Assist",
        subtitle="Alice: [0.52, 0.16, 0.40, 0.68] | Bob: [0.08, 0.16, 0.40, 0.68] | Spatial causality strictly inverted!",
        raw_img_path=wf38_img,
        regions=regions_wf38,
        scene_plan=plan_wf38,
        guide_mode="mannequin_capsule"
    )

    wf39_img = find_image_by_prefix(CANONICAL_DIR, "WF39_Phase3I_FastDraft12_39_AliceRight_BobLeft_CNAssist")
    row3 = create_3panel_row(
        title="Workflow 39: Fast Draft 12 Regression (Alice Right, Bob Left SWAP) + ControlNet Assist",
        subtitle="Hyper-SDXL 12 steps (CFG 6.0) | Demonstrates rapid prototyping with preserved ControlNet silhouette lock",
        raw_img_path=wf39_img,
        regions=regions_wf38,
        scene_plan=plan_wf38,
        guide_mode="mannequin_capsule"
    )

    header_h = 70
    sheet_w = row1.width
    sheet_h = header_h + row1.height + row2.height + row3.height + 30

    sheet = Image.new("RGB", (sheet_w, sheet_h), (245, 242, 237))
    draw = ImageDraw.Draw(sheet)
    draw.text((25, 20), "Sheet I: Phase 3I Authoring Staging Causality & Fast Draft 12 Regression (WF37, WF38, WF39)", fill=(35, 25, 15), font=get_font(24))
    draw.line([(25, 58), (sheet_w - 25, 58)], fill=(210, 105, 30), width=2)

    y = header_h
    for r in [row1, row2, row3]:
        sheet.paste(r, (0, y))
        y += r.height + 10

    out_path = os.path.join(OUTPUT_DIR, "sheet_i_authoring_staging_cn_assist_swap.png")
    sheet.save(out_path, quality=95)
    print(f"[SUCCESS] Saved Sheet I: {out_path}")


if __name__ == "__main__":
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    build_sheet_h()
    build_sheet_i()
    print("\n[ALL DONE] Phase 3I Contact Sheets successfully built!")
