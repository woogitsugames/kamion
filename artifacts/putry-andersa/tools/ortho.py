"""GUGiK WMS HighResolution 0.08 m cells -> crops in local E,N (ADR 0146). Usage: ortho.py crop E N half_m scale out.jpg"""
import sys, json
from pathlib import Path
from PIL import Image, ImageDraw
REPO = Path(__file__).resolve().parents[3]
R = REPO / 'Data/raw/refs/gugik-ortho-hr/bialystok-industrial-c'
X0B, Y0B = 776971.0, 595199.0      # region bbox xmin, ymin (EPSG:2180)
OX, OY = 777995.0, 596223.0        # local origin
C = 128.0; RES = 0.08

def window(e0, n0, e1, n1):
    """RGB image of local window [e0,e1]x[n0,n1] at 0.08 m, north up; missing cells grey."""
    x0, y0, x1, y1 = e0 + OX, n0 + OY, e1 + OX, n1 + OY
    W = Image.new('RGB', (int(round((x1 - x0) / RES)), int(round((y1 - y0) / RES))), (60, 60, 60))
    for ix in range(int((x0 - X0B) // C), int((x1 - X0B) // C) + 1):
        for iy in range(int((y0 - Y0B) // C), int((y1 - Y0B) // C) + 1):
            f = R / f'c_{ix:02d}_{iy:02d}.jpg'
            if not f.exists():
                continue
            cx0, cyt = X0B + ix * C, Y0B + (iy + 1) * C
            W.paste(Image.open(f), (int(round((cx0 - x0) / RES)), int(round((y1 - cyt) / RES))))
    return W

def crop(e, n, half, scale, out, marks=()):
    im = window(e - half, n - half, e + half, n + half)
    im = im.resize((int(im.width * scale), int(im.height * scale)), Image.LANCZOS)
    d = ImageDraw.Draw(im)
    k = scale / RES
    for g in range(-int(half), int(half) + 1, 5):          # 5 m grid ticks
        u = (g + half) * k
        d.line([(u, 0), (u, 8)], fill=(255, 255, 0)); d.line([(0, u), (8, u)], fill=(255, 255, 0))
    for (me, mn, lab) in marks:
        u, v = (me - e + half) * k, (n + half - mn) * k
        d.ellipse([u - 4, v - 4, u + 4, v + 4], outline=(255, 0, 0)); d.text((u + 6, v - 6), lab, fill=(255, 0, 0))
    im.save(out, quality=90)

if __name__ == '__main__':
    e, n, half, scale = map(float, sys.argv[2:6])
    rows = json.loads((REPO / 'Data/Regions/bialystok-industrial-c/lamp_rows.json').read_text(encoding='utf-8'))['rows']
    marks = [(p[0], p[1], str(i)) for r in rows for i, p in enumerate(r['points_en'])]
    crop(e, n, half, scale, sys.argv[6], marks)
