"""Before/after sheets for the owner (rounding pass, 2026-11-10). Plain Python + Pillow, no Blender.

  python tools/blender/truck/exterior/rounding_sheet.py <before_dir> <after_dir> <out_dir> [<out_dir2> ...]

Inputs: build.py --mode a4 renders (34przod/bok/przod/top_kabina, white, overcast) of --shape b2 and --shape round.
Output: rounding_<view>.jpg (before left, after right, <= 1600 px wide) in every out_dir.
"""
import os
import sys

from PIL import Image, ImageDraw, ImageFont

# crop boxes in the 1600x900 control frames (same box for both variants)
CROPS = {"34przod": (400, 100, 1180, 730), "bok": (300, 150, 1080, 780), "przod": (240, 24, 1360, 900),
         "top_kabina": (360, 135, 1240, 765)}
TITLE = {"34przod": "3/4 przód", "bok": "bok", "przod": "przód", "top_kabina": "kabina z góry"}


def font(sz):
    for f in ("arial.ttf", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(f, sz)
        except OSError:
            pass
    return ImageFont.load_default()


def main():
    before, after, outs = sys.argv[1], sys.argv[2], sys.argv[3:]
    for v, box in CROPS.items():
        name = f"{v}_white_overcast.jpg"
        a = Image.open(os.path.join(before, name)).crop(box)
        b = Image.open(os.path.join(after, name)).crop(box)
        w = 790
        h = round(a.height * w / a.width)
        a, b = a.resize((w, h), Image.LANCZOS), b.resize((w, h), Image.LANCZOS)
        sheet = Image.new("RGB", (2 * w + 20, h + 44), (255, 255, 255))
        sheet.paste(a, (0, 44))
        sheet.paste(b, (w + 20, 44))
        d = ImageDraw.Draw(sheet)
        d.text((8, 8), f"PRZED — obecna kabina (B2) | {TITLE[v]}", fill=(0, 0, 0), font=font(24))
        d.text((w + 28, 8), f"PO — propozycja zaokrągleń | {TITLE[v]}", fill=(0, 0, 0), font=font(24))
        for o in outs:
            os.makedirs(o, exist_ok=True)
            sheet.save(os.path.join(o, f"rounding_{v}.jpg"), quality=90)
            print("WROTE", os.path.join(o, f"rounding_{v}.jpg"))


if __name__ == "__main__":
    main()
