"""Track A5 — 2x2 contact sheets for the owner's open questions (trim colour, badge), JPEG <= 400 KB.

    uv run --no-project --with pillow python tools/blender/truck/interior/sheet.py OUT.jpg TITLE \
        img1.jpg "label 1" img2.jpg "label 2" img3.jpg "label 3" img4.jpg "label 4"
"""
import os
import sys

from PIL import Image, ImageDraw, ImageFont


def ui_font_path():
    """Inter (SIL OFL 1.1) as shipped with Blender: has Polish glyphs (Pillow's bundled Aileron does not).
    The font is only used to rasterise text into textures; it is not copied into the repo or the build."""
    import glob
    import shutil
    exe = shutil.which("blender")
    if exe:
        hits = glob.glob(os.path.join(os.path.dirname(os.path.realpath(exe)), "*", "datafiles", "fonts", "Inter.woff2"))
        if hits:
            return hits[0]
    return None


_FONT_PATH = ui_font_path()


def font(size):
    if _FONT_PATH:
        return ImageFont.truetype(_FONT_PATH, size)
    return ImageFont.load_default(size)  # fallback: Aileron (CC0), no Polish diacritics


def main():
    out, title, rest = sys.argv[1], sys.argv[2], sys.argv[3:]
    items = list(zip(rest[0::2], rest[1::2]))
    W, H = 1600, 900
    tw, th = W // 2, (H - 40) // 2
    sheet = Image.new("RGB", (W, H), (24, 24, 26))
    d = ImageDraw.Draw(sheet)
    f = font(22)
    d.text((14, 8), title, fill=(230, 230, 228), font=f)
    for i, (path, label) in enumerate(items[:4]):
        im = Image.open(path).convert("RGB")
        im = im.resize((tw, int(im.height * tw / im.width)), Image.LANCZOS)
        im = im.crop((0, (im.height - th) // 2, tw, (im.height - th) // 2 + th))
        x, y = (i % 2) * tw, 40 + (i // 2) * th
        sheet.paste(im, (x, y))
        d.rectangle([x, y + th - 34, x + 12 + int(d.textlength(label, font=f)) + 12, y + th], fill=(0, 0, 0))
        d.text((x + 12, y + th - 30), label, fill=(240, 240, 236), font=f)
    q = 88
    while True:
        sheet.save(out, quality=q, optimize=True)
        if os.path.getsize(out) <= 400 * 1024 or q <= 60:
            break
        q -= 4
    print("WROTE", out, q)


if __name__ == "__main__":
    main()
