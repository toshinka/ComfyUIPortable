"""Create the bounded M3B-LR6 six-output contact sheet."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "docs/manga/verification/m3b_lr6"
ITEMS = [
    ("Seed 42 / CAST_OFF", "SEED_A_CAST_OFF.png"),
    ("Seed 42 / CAST_HARD", "SEED_A_CAST_HARD.png"),
    ("Seed 42 / CAST_SOFT", "SEED_A_CAST_SOFT.png"),
    ("Seed 77 / CAST_OFF", "SEED_B_CAST_OFF.png"),
    ("Seed 77 / CAST_HARD", "SEED_B_CAST_HARD.png"),
    ("Seed 77 / CAST_SOFT", "SEED_B_CAST_SOFT.png"),
]


def load_font(size: int):
    for name in ("arial.ttf", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            pass
    return ImageFont.load_default()


def main() -> None:
    thumb_w, thumb_h = 260, 380
    gap = 18
    header_h = 50
    label_h = 28
    mask_h = 230
    sheet = Image.new(
        "RGB",
        (3 * thumb_w + 4 * gap, header_h + 2 * (thumb_h + label_h + gap) + mask_h + 2 * gap),
        "white",
    )
    draw = ImageDraw.Draw(sheet)
    draw.text((gap, 14), "M3B-LR6 CAST Soft-Edge Figure Mask Compatibility", fill="black", font=load_font(21))
    for index, (label, filename) in enumerate(ITEMS):
        source = Image.open(EVIDENCE / filename).convert("RGB")
        source.thumbnail((thumb_w, thumb_h), Image.Resampling.LANCZOS)
        row, col = divmod(index, 3)
        x = gap + col * (thumb_w + gap)
        y = header_h + gap + row * (thumb_h + label_h + gap)
        cell = Image.new("RGB", (thumb_w, thumb_h), "#eeeeee")
        cell.paste(source, ((thumb_w - source.width) // 2, (thumb_h - source.height) // 2))
        sheet.paste(cell, (x, y))
        draw.text((x, y + thumb_h + 5), label, fill="black", font=load_font(14))

    mask_y = header_h + 2 * (thumb_h + label_h + gap) + gap
    for col, (label, filename) in enumerate((("HARD mask", "M3B_LR6_HARD_MASK.png"), ("SOFT mask / radius 16", "M3B_LR6_SOFT_MASK.png"))):
        source = Image.open(EVIDENCE / filename).convert("L")
        source.thumbnail((thumb_w, mask_h - 30), Image.Resampling.LANCZOS)
        x = gap + col * (thumb_w + gap)
        draw.text((x, mask_y), label, fill="black", font=load_font(14))
        sheet.paste(source.convert("RGB"), (x, mask_y + 24))

    output = EVIDENCE / "M3B_LR6_CONTACT_SHEET.png"
    sheet.save(output, format="PNG")
    print(output)


if __name__ == "__main__":
    main()
