"""Create the bounded M3B-LR7 six-output contact sheet."""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_LR6 = ROOT / "docs/manga/verification/m3b_lr6"
EVIDENCE_LR7 = ROOT / "docs/manga/verification/m3b_lr7"

ITEMS = [
    ("Seed 42 / CAST_OFF (HISTORICAL)", EVIDENCE_LR6 / "SEED_A_CAST_OFF.png"),
    ("Seed 42 / CAST_HARD (HISTORICAL)", EVIDENCE_LR6 / "SEED_A_CAST_HARD.png"),
    ("Seed 42 / CAST_GLOBAL (NEW)", EVIDENCE_LR7 / "SEED_A_CAST_GLOBAL.png"),
    ("Seed 77 / CAST_OFF (HISTORICAL)", EVIDENCE_LR6 / "SEED_B_CAST_OFF.png"),
    ("Seed 77 / CAST_HARD (HISTORICAL)", EVIDENCE_LR6 / "SEED_B_CAST_HARD.png"),
    ("Seed 77 / CAST_GLOBAL (NEW)", EVIDENCE_LR7 / "SEED_B_CAST_GLOBAL.png"),
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
    sheet = Image.new(
        "RGB",
        (3 * thumb_w + 4 * gap, header_h + 2 * (thumb_h + label_h + gap) + gap),
        "white",
    )
    draw = ImageDraw.Draw(sheet)
    draw.text(
        (gap, 14),
        "M3B-LR7 CAST GLOBAL vs EFFECT-MASK Isolation Contact Sheet",
        fill="black",
        font=load_font(20),
    )

    for index, (label, path) in enumerate(ITEMS):
        if not path.exists():
            raise FileNotFoundError(f"Missing image for contact sheet: {path}")
        source = Image.open(path).convert("RGB")
        source.thumbnail((thumb_w, thumb_h), Image.Resampling.LANCZOS)
        row, col = divmod(index, 3)
        x = gap + col * (thumb_w + gap)
        y = header_h + gap + row * (thumb_h + label_h + gap)
        cell = Image.new("RGB", (thumb_w, thumb_h), "#eeeeee")
        cell.paste(source, ((thumb_w - source.width) // 2, (thumb_h - source.height) // 2))
        sheet.paste(cell, (x, y))

        color = "#0055aa" if "(NEW)" in label else "#555555"
        draw.text((x, y + thumb_h + 5), label, fill=color, font=load_font(13))

    output = EVIDENCE_LR7 / "M3B_LR7_CONTACT_SHEET.png"
    sheet.save(output, format="PNG")
    print(f"Contact sheet saved to: {output}")


if __name__ == "__main__":
    main()
