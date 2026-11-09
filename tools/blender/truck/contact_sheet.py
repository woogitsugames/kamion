"""Side-by-side comparison sheet of the three A2 concepts.

    uv run --with pillow python tools/blender/truck/contact_sheet.py docs/reports/visual/truck-A2

Columns = concepts A/B/C, rows = paint 3/4 front, side ortho, front ortho, 3/4 rear.
Output: <dir>/porownanie-koncepcji.jpg (kept under ~400 KB).
"""
import os
import sys

from PIL import Image, ImageDraw, ImageFont

STAMP_PX = 26  # Blender stamp bar height at 1600x900 / font 20
ROWS = [("lakier", "3/4 przód — lakier"), ("bok", "bok (ortho)"), ("przod", "przód (ortho)"),
        ("34tyl", "3/4 tył")]
COLS = [("A", "A · TRAKT"), ("B", "B · BIELIK"), ("C", "C · NAREW")]
TW = 600
TH = int((TW - 6) * (900 - STAMP_PX) / 1600) + 4  # tile keeps the render aspect, no crop
HEAD, LEFT = 44, 0


def font(size):
    for name in ("arial.ttf", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            pass
    return ImageFont.load_default(size=size)


def main(d):
    sheet = Image.new("RGB", (LEFT + TW * len(COLS), HEAD + (TH + 30) * len(ROWS)), (238, 238, 236))
    dr = ImageDraw.Draw(sheet)
    fh, fr = font(26), font(18)
    for ci, (c, title) in enumerate(COLS):
        dr.text((LEFT + ci * TW + 12, 8), title, fill=(20, 20, 20), font=fh)
    for ri, (v, label) in enumerate(ROWS):
        y0 = HEAD + ri * (TH + 30)
        dr.text((LEFT + 12, y0 + 4), label, fill=(60, 60, 60), font=fr)
        for ci, (c, _) in enumerate(COLS):
            im = Image.open(os.path.join(d, f"koncepcja-{c}_{v}.jpg")).convert("RGB")
            im = im.crop((0, STAMP_PX, im.width, im.height))
            im = im.resize((TW - 6, TH - 4), Image.LANCZOS)
            sheet.paste(im, (LEFT + ci * TW + 3, y0 + 28))
    out = os.path.join(d, "porownanie-koncepcji.jpg")
    sheet.save(out, quality=86, optimize=True)
    print(out, os.path.getsize(out) // 1024, "KB")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "docs/reports/visual/truck-A2")
