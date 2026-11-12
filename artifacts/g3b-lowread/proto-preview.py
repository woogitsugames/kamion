"""Silhouette previews of the ADR 0127 prototypes (orthographic, dark on sky grey), LOD0 | LOD1, at a chosen
pixel size - a quick check of what survives at distance before a full build. Usage: proto-preview.py"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "worldgen"))
from streetscape import life_props as LP  # noqa: E402
from streetscape import props as PR  # noqa: E402

OUT = Path(__file__).parent / "crops"


def raster(mesh, yaw_deg, m_per_px, ss=4):
    V = np.concatenate([v for p in mesh.prims.values() for v in p[0]])
    T, off = [], 0
    for p in mesh.prims.values():
        for v, t in zip(p[0], p[1]):
            pass
    # Mesh.add stores triangle indices already offset within the primitive
    tris = []
    for p in mesh.prims.values():
        Vp = np.concatenate(p[0])
        for t in np.concatenate(p[1]):
            tris.append(Vp[t])
    a = np.radians(yaw_deg)
    ux = np.array([np.cos(a), np.sin(a), 0.0])
    x = V @ ux
    x0, x1, z0, z1 = x.min() - 1, x.max() + 1, V[:, 2].min() - 0.5, V[:, 2].max() + 1
    s = ss / m_per_px
    W, H = int((x1 - x0) * s), int((z1 - z0) * s)
    im = Image.new("L", (W, H), 200)
    d = ImageDraw.Draw(im)
    for t in tris:
        d.polygon([((q @ ux - x0) * s, (z1 - q[2]) * s) for q in t], fill=40)
    return im.resize((max(1, W // ss), max(1, H // ss)), Image.BOX)


def sheet(name, lods, yaw, mpp_list):
    ims = []
    for mpp in mpp_list:
        for m in lods:
            r = raster(m, yaw, mpp)
            k = max(1, int(round(mpp / mpp_list[0])))
            ims.append(r.resize((r.width * k, r.height * k), Image.NEAREST))
    W = sum(i.width for i in ims) + 10 * (len(ims) - 1)
    H = max(i.height for i in ims)
    out = Image.new("L", (W, H), 200)
    x = 0
    for i in ims:
        out.paste(i, (x, H - i.height))
        x += i.width + 10
    if out.width > 1900:
        out = out.resize((1900, int(out.height * 1900 / out.width)), Image.LANCZOS)
    out.save(OUT / f"proto-{name}.png")
    print(name, out.size)


l0, l1, _ = PR.pylon()
sheet("pylon", (l0, l1), 0, (0.05, 0.2, 0.4))          # ~50 m, ~200 m, ~400 m on a 1280 px / 59 deg frame
g0, g1, _ = LP.sign_gantry(16.0, 7.6)
sheet("gantry", (g0, g1), 0, (0.03, 0.06, 0.12))       # ~30 m, ~60 m, ~120 m
