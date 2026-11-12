"""Orthophoto crop (GUGiK 2024, 0.25 m, reference only) with the noise-barrier source lines (BDOT10k OT_OIKM_L red,
OSM noise walls yellow) and an SBS camera pose (cyan dot + heading). Usage: ortho-check.py <cam-id-fragment> [half_m]"""
import json
import sys
from pathlib import Path

import numpy as np
import rasterio
from PIL import Image, ImageDraw
from rasterio.windows import from_bounds

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "worldgen"))
from streetscape import furniture as F  # noqa: E402
from streetscape import sources as SRC  # noqa: E402

RID = "bialystok-industrial-c"
OX, OY = 777995.0, 596223.0
frag = sys.argv[1]
half = float(sys.argv[2]) if len(sys.argv) > 2 else 90.0
cams = json.loads((ROOT / f"Data/Regions/{RID}/sbs_cameras.json").read_text(encoding="utf-8"))["cameras"]
cam = next(c for c in cams if frag in c["id"])
cx, cy = cam["pos"][0], cam["pos"][1]
lx, ly = cam["look_at"][0], cam["look_at"][1]
tif = ROOT / f"Data/raw/derived/{RID}/ortho_0p25m.tif"
with rasterio.open(tif) as ds:
    w = from_bounds(OX + cx - half, OY + cy - half, OX + cx + half, OY + cy + half, ds.transform)
    a = ds.read([1, 2, 3], window=w, boundless=True)
im = Image.fromarray(np.moveaxis(a, 0, -1)).convert("RGB")
sc = 1000 / im.width
im = im.resize((1000, 1000), Image.LANCZOS)
d = ImageDraw.Draw(im)


def px(e, n):
    return ((e - (cx - half)) / (2 * half) * 1000, (cy + half - n) / (2 * half) * 1000)


src = SRC.load(RID)
for f in src["bdot10k"]["OT_OIKM_L"]:
    P = np.asarray(f["geometry"]["coordinates"], float)[:, :2] - [OX, OY]
    d.line([px(*p) for p in P], fill=(255, 40, 40), width=2)
    for p in (P[0], P[-1]):
        if abs(p[0] - cx) < half and abs(p[1] - cy) < half:
            print("bdot end", f["id"][-8:], np.round(p, 1))
for f in src["osm"]["ways"]:
    if F.is_noise_wall(f["tags"]):
        P = np.asarray(f["geometry"]["coordinates"], float)[:, :2] - [OX, OY]
        d.line([px(*p) for p in P], fill=(255, 230, 0), width=1)
        for p in (P[0], P[-1]):
            if abs(p[0] - cx) < half and abs(p[1] - cy) < half:
                print("osm end", f["osm_way"], np.round(p, 1))
x, y = px(cx, cy)
d.ellipse([x - 5, y - 5, x + 5, y + 5], outline=(0, 255, 255), width=2)
v = np.array([lx - cx, ly - cy])
v = v / np.hypot(*v) * 25
d.line([px(cx, cy), px(cx + v[0], cy + v[1])], fill=(0, 255, 255), width=2)
for k in range(-int(half) // 20 * 20, int(half) + 1, 20):        # 20 m grid ticks, labelled in local E / N
    d.text(px(cx + k, cy + half - 1), f"{cx + k:.0f}", fill=(255, 255, 255))
    d.text(px(cx - half + 1, cy + k), f"{cy + k:.0f}", fill=(255, 255, 255))
out = Path(__file__).parent / "crops" / f"ortho-{frag}.jpg"
im.save(out, quality=88)
print(out, "cam", cx, cy)
