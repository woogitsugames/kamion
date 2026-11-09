"""Track A6 — side-by-side comparison sheets (left | right, labelled), JPEG <= 400 KB.

    uv run --no-project --with pillow python tools/blender/truck/interior/beforeafter.py OUT.jpg TITLE \
        left.jpg "left label" right.jpg "right label"
"""
import os
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sheet import font  # noqa: E402


def main():
    out, title, l_img, l_lab, r_img, r_lab = sys.argv[1:7]
    W, half_h = 1600, 450
    sheet = Image.new("RGB", (W, half_h + 40), (24, 24, 26))
    d = ImageDraw.Draw(sheet)
    f = font(22)
    d.text((14, 8), title, fill=(230, 230, 228), font=f)
    for i, (path, label) in enumerate(((l_img, l_lab), (r_img, r_lab))):
        im = Image.open(path).convert("RGB").resize((W // 2, half_h), Image.LANCZOS)
        x = i * W // 2
        sheet.paste(im, (x, 40))
        d.rectangle([x, 40 + half_h - 34, x + 24 + int(d.textlength(label, font=f)), 40 + half_h], fill=(0, 0, 0))
        d.text((x + 12, 40 + half_h - 30), label, fill=(240, 240, 236), font=f)
    q = 90
    while True:
        sheet.save(out, quality=q, optimize=True)
        if os.path.getsize(out) <= 400 * 1024 or q <= 60:
            break
        q -= 4
    print("WROTE", out, q)


if __name__ == "__main__":
    main()
