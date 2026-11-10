"""Orthophoto crop of a depot with data overlays (GUGiK ortho 0.25 m; BDOT/OSM footprints, road graph, gate3
cameras, optional extra polylines from a hero depot spec). Reference sheets for ADR 0071.

uv run --project tools/worldgen python tools/worldgen/qa/depot_ortho.py XMIN YMIN XMAX YMAX OUT.jpg [--plain]
    [--scale 1.0] [--spec Data/Regions/<id>/generated/landmarks/<asset>.spec.json] [--nolabels]
Coordinates: EPSG:2180.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

Image.MAX_IMAGE_PIXELS = None
REPO = Path(__file__).resolve().parents[3]


def crop(region, xmin, ymin, xmax, ymax, out, overlay=True, scale=1.0, labels=True, spec=None, grid=0.0):
    R = REPO / "Data" / "Regions" / region
    reg = json.loads((R / "terrain.json").read_text(encoding="utf-8"))
    X0, Y1 = reg["bbox"][0], reg["bbox"][3]
    import yaml
    org = yaml.safe_load((R / "region.yaml").read_text(encoding="utf-8"))["origin"]
    ox, oy = org["x"], org["y"]
    im = Image.open(REPO / "Data" / "raw" / "derived" / region / "ortho_0p25m.tif").convert("RGB")
    a = ((xmin - X0) * 4, (Y1 - ymax) * 4)
    b = ((xmax - X0) * 4, (Y1 - ymin) * 4)
    c = im.crop((int(a[0]), int(a[1]), int(b[0]), int(b[1])))
    if scale != 1.0:
        c = c.resize((int(c.width * scale), int(c.height * scale)), Image.LANCZOS)
    k = 4 * scale

    def P(x, y):
        return ((x - xmin) * k, (ymax - y) * k)
    d = ImageDraw.Draw(c)
    if overlay:
        g = json.loads((R / "buildings.geojson").read_text(encoding="utf-8"))
        for f in g["features"]:
            geom = f["geometry"]
            polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
            for poly in polys:
                ring = poly[0]
                cx = sum(p[0] for p in ring) / len(ring)
                cy = sum(p[1] for p in ring) / len(ring)
                if not (xmin < cx < xmax and ymin < cy < ymax):
                    continue
                d.line([P(*p[:2]) for p in ring], fill=(255, 220, 0), width=2)
                if labels:
                    pr = f["properties"]
                    d.text(P(cx, cy), f"{pr['id'][5:13]}\n{pr['function']}\n{pr['area_m2']:.0f}m2 h{pr['height_m']}",
                           fill=(255, 255, 0))
        gr = json.loads((R / "roads.graph.json").read_text(encoding="utf-8"))
        for e in gr["edges"]:
            pts = e.get("geometry") or e.get("points") or e.get("coords")
            if pts and any(xmin < p[0] < xmax and ymin < p[1] < ymax for p in pts):
                d.line([P(*p[:2]) for p in pts], fill=(0, 255, 255), width=1)
        cams = json.loads((R / "gate3_cameras.json").read_text(encoding="utf-8"))["cameras"]
        for cm in cams:
            x, y = cm["pos"][0] + ox, cm["pos"][1] + oy
            if xmin < x < xmax and ymin < y < ymax:
                q = P(x, y)
                d.ellipse([q[0] - 4, q[1] - 4, q[0] + 4, q[1] + 4], outline=(255, 0, 255), width=2)
                v = np.array([cm["look_at"][0] + ox - x, cm["look_at"][1] + oy - y])
                v = v / max(np.linalg.norm(v), 1e-6) * 12
                d.line([q, P(x + v[0], y + v[1])], fill=(255, 0, 255), width=2)
                if labels:
                    d.text((q[0] + 6, q[1] - 6), cm["id"], fill=(255, 0, 255))
    if grid:
        import math
        gx = math.ceil(xmin / grid) * grid
        while gx < xmax:
            d.line([P(gx, ymin), P(gx, ymax)], fill=(255, 255, 255) if gx % (2 * grid) == 0 else (150, 150, 150), width=1)
            if gx % (2 * grid) == 0:
                d.text((P(gx, ymax)[0] + 2, 2), f"{gx:.0f}"[-3:], fill=(255, 255, 0))
            gx += grid
        gy = math.ceil(ymin / grid) * grid
        while gy < ymax:
            d.line([P(xmin, gy), P(xmax, gy)], fill=(255, 255, 255) if gy % (2 * grid) == 0 else (150, 150, 150), width=1)
            if gy % (2 * grid) == 0:
                d.text((2, P(xmin, gy)[1] + 2), f"{gy:.0f}"[-3:], fill=(255, 255, 0))
            gy += grid
    if spec:
        sp = json.loads(Path(spec).read_text(encoding="utf-8"))
        for ln in sp.get("debug_lines", []):
            col = tuple(ln.get("rgb", (255, 60, 60)))
            d.line([P(p[0] + ox, p[1] + oy) for p in ln["pts"]], fill=col, width=ln.get("w", 2))
            if labels and ln.get("label"):
                d.text(P(ln["pts"][0][0] + ox, ln["pts"][0][1] + oy), ln["label"], fill=col)
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    c.save(out, quality=90)
    print(out, c.size)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("bbox", nargs=4, type=float)
    ap.add_argument("out")
    ap.add_argument("--region", default="bialystok-industrial-c")
    ap.add_argument("--plain", action="store_true")
    ap.add_argument("--nolabels", action="store_true")
    ap.add_argument("--scale", type=float, default=1.0)
    ap.add_argument("--spec")
    ap.add_argument("--grid", type=float, default=0.0)
    a = ap.parse_args()
    crop(a.region, *a.bbox, a.out, overlay=not a.plain, scale=a.scale, labels=not a.nolabels, spec=a.spec,
         grid=a.grid)
