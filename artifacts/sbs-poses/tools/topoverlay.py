"""Overlay probe positions/frusta onto a top-down overview render (north up, 4:3, vfov 50, height H)."""
import json, math, sys
from pathlib import Path
from PIL import Image, ImageDraw
def overlay(top_png, center, height, cams, out, crop=None):
    im = Image.open(top_png).convert('RGB'); W, Hh = im.size
    mpp = 2 * height * math.tan(math.radians(25)) / Hh
    d = ImageDraw.Draw(im)
    def px(e, n): return (W / 2 + (e - center[0]) / mpp, Hh / 2 - (n - center[1]) / mpp)
    for lab, c, col, hfov in cams:
        e, n = c['pos'][:2]; h = math.atan2(c['look_at'][0] - e, c['look_at'][1] - n); p = px(e, n)
        for s in (-1, 1):
            a = h + s * math.radians(hfov / 2); d.line([p, px(e + 50 * math.sin(a), n + 50 * math.cos(a))], fill=col, width=1)
        d.ellipse((p[0] - 4, p[1] - 4, p[0] + 4, p[1] + 4), outline=col, width=2); d.text((p[0] + 5, p[1] - 5), lab, fill=col)
    if crop: im = im.crop(crop)
    im.save(out)
if __name__ == '__main__':
    pass
