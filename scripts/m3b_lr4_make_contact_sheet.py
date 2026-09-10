"""Create the bounded M3B-LR4 six-output visual contact sheet."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "docs/manga/verification/m3b_lr4"
ITEMS = [
    ("Seed 42 / OFF", "SEED_A_OFF.png"),
    ("Seed 42 / CLEAN_GLOBAL", "SEED_A_GLOBAL.png"),
    ("Seed 42 / CLEAN_MASKED", "SEED_A_MASKED.png"),
    ("Seed 77 / OFF", "SEED_B_OFF.png"),
    ("Seed 77 / CLEAN_GLOBAL", "SEED_B_GLOBAL.png"),
    ("Seed 77 / CLEAN_MASKED", "SEED_B_MASKED.png"),
]


def load_font(size: int):
    for name in ("arial.ttf", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            pass
    return ImageFont.load_default()


def main() -> None:
    thumb_w, thumb_h = 280, 410
    gap = 18
    header_h = 52
    label_h = 30
    sheet = Image.new("RGB", (3 * thumb_w + 4 * gap, header_h + 2 * (thumb_h + label_h + gap) + gap), "white")
    draw = ImageDraw.Draw(sheet)
    title_font = load_font(22)
    label_font = load_font(15)
    draw.text((gap, 14), "M3B-LR4 Figure-Union Mask Locality A/B", fill="black", font=title_font)
    for index, (label, filename) in enumerate(ITEMS):
        source = Image.open(EVIDENCE / filename).convert("RGB")
        source.thumbnail((thumb_w, thumb_h), Image.Resampling.LANCZOS)
        row, col = divmod(index, 3)
        x = gap + col * (thumb_w + gap)
        y = header_h + gap + row * (thumb_h + label_h + gap)
        cell = Image.new("RGB", (thumb_w, thumb_h), "#eeeeee")
        cell.paste(source, ((thumb_w - source.width) // 2, (thumb_h - source.height) // 2))
        sheet.paste(cell, (x, y))
        draw.text((x, y + thumb_h + 6), label, fill="black", font=label_font)
    output = EVIDENCE / "M3B_LR4_CONTACT_SHEET.png"
    sheet.save(output, format="PNG")
    print(output)


if __name__ == "__main__":
    main()
