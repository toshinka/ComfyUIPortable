"""Create the bounded M3B-LR5 four-output visual contact sheet."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "docs/manga/verification/m3b_lr5"
ITEMS = [
    ("Seed 42 / CAST_OFF", "SEED_A_CAST_OFF.png"),
    ("Seed 42 / CAST_MASKED", "SEED_A_CAST_MASKED.png"),
    ("Seed 77 / CAST_OFF", "SEED_B_CAST_OFF.png"),
    ("Seed 77 / CAST_MASKED", "SEED_B_CAST_MASKED.png"),
]


def load_font(size: int):
    for name in ("arial.ttf", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            pass
    return ImageFont.load_default()


def main() -> None:
    thumb_w, thumb_h = 420, 612
    gap = 24
    header_h = 56
    label_h = 32
    sheet = Image.new(
        "RGB",
        (2 * thumb_w + 3 * gap, header_h + 2 * (thumb_h + label_h + gap) + gap),
        "white",
    )
    draw = ImageDraw.Draw(sheet)
    title_font = load_font(24)
    label_font = load_font(16)
    draw.text((gap, 16), "M3B-LR5 CAST + Figure-Masked CLEAN Compatibility", fill="black", font=title_font)
    for index, (label, filename) in enumerate(ITEMS):
        source = Image.open(EVIDENCE / filename).convert("RGB")
        source.thumbnail((thumb_w, thumb_h), Image.Resampling.LANCZOS)
        row, col = divmod(index, 2)
        x = gap + col * (thumb_w + gap)
        y = header_h + gap + row * (thumb_h + label_h + gap)
        cell = Image.new("RGB", (thumb_w, thumb_h), "#eeeeee")
        cell.paste(source, ((thumb_w - source.width) // 2, (thumb_h - source.height) // 2))
        sheet.paste(cell, (x, y))
        draw.text((x, y + thumb_h + 6), label, fill="black", font=label_font)
    output = EVIDENCE / "M3B_LR5_CONTACT_SHEET.png"
    sheet.save(output, format="PNG")
    print(output)


if __name__ == "__main__":
    main()
