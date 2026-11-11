"""Ortho (GUGiK 0.25 m, reference only) + generated carriageway edges / junction patches / OSM axes / start route.

    uv run --project tools/worldgen python artifacts/roads-p0-r10/scripts/ortho_overlay.py <outdir> name:E:N:half [...]

yellow = generated carriageway edges (between the junction trims), cyan = junction patch boundary,
circles = consistency cases (orange kerb, white prop, blue furniture, green obstacle),
magenta = OSM way geometry (roads.graph.json), red = route_start.json, white ticks every 10 m.
"""
import json
import sys
from pathlib import Path

import numpy as np
import rasterio
from PIL import Image, ImageDraw
from rasterio.windows import from_bounds

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "tools" / "worldgen"))
from roads import pipeline  # noqa: E402

RID = "bialystok-industrial-c"
out = Path(sys.argv[1])
out.mkdir(parents=True, exist_ok=True)
w = pipeline.build(RID)
ox, oy = w.origin
graph = json.loads((REPO / "Data/Regions" / RID / "roads.graph.json").read_text(encoding="utf-8"))
route = json.loads((REPO / "Data/Regions" / RID / "route_start.json").read_text(encoding="utf-8"))["points_en"]
cases = json.loads((REPO / "Data/Regions" / RID / "generated/road_consistency_qa.json").read_text(encoding="utf-8"))["cases"]
COL = {"kerb_on_carriageway": (255, 80, 0), "prop_on_carriageway": (255, 255, 255), "furniture_in_lane": (0, 120, 255),
       "obstacle_in_lane": (0, 255, 0), "prop_through_deck": (255, 255, 255)}
tif = REPO / "Data/raw/derived" / RID / "ortho_0p25m.tif"

for spec in sys.argv[2:]:
    name, e0, n0, half = spec.split(":")
    e0, n0, half = float(e0), float(n0), float(half)
    cx, cy = ox + e0, oy + n0
    with rasterio.open(tif) as ds:
        win = from_bounds(cx - half, cy - half, cx + half, cy + half, ds.transform)
        a = ds.read([1, 2, 3], window=win)
    im = Image.fromarray(np.moveaxis(a, 0, 2)).resize((960, 960), Image.LANCZOS)
    ppm = 960 / (2 * half)
    d = ImageDraw.Draw(im)

    def px(p):
        return ((p[0] - (e0 - half)) * ppm, ((n0 + half) - p[1]) * ppm)

    for ed in graph["edges"]:
        P = np.array(ed["geometry"]) - np.array([ox, oy])
        if np.any(np.hypot(P[:, 0] - e0, P[:, 1] - n0) < half * 1.5):
            d.line([px(p) for p in P], fill=(255, 0, 255), width=1)
    for c in w.net.chains:
        if c.meta.get("absorbed") or c.closed and False:
            continue
        s = c.line.s
        m = (s >= c.t_a) & (s <= c.length - c.t_b)
        if m.sum() < 2:
            continue
        P = c.line.p[m]
        if not np.any(np.hypot(P[:, 0] - e0, P[:, 1] - n0) < half * 1.5):
            continue
        N = c.line.n[m]
        hw = c.hw[m][:, None]
        d.line([px(p) for p in P + N * hw], fill=(255, 230, 0), width=2)
        d.line([px(p) for p in P - N * hw], fill=(255, 230, 0), width=2)
    for j in w.junctions:
        if np.hypot(*(j.center - np.array([e0, n0]))) < half * 1.5 and len(j.boundary) > 2:
            B = [px(p) for p, _ in j.boundary]
            d.line(B + [B[0]], fill=(0, 255, 255), width=2)
    d.line([px(p) for p in route], fill=(255, 0, 0), width=2)
    for cs in cases:                                   # road_consistency_qa.json: kerb / prop / furniture cases
        if cs["kind"] in COL and abs(cs["e"] - e0) < half and abs(cs["n"] - n0) < half:
            x, y = px((cs["e"], cs["n"]))
            d.ellipse([x - 5, y - 5, x + 5, y + 5], outline=COL[cs["kind"]], width=2)
    for k in range(int(-half), int(half) + 1, 10):
        x = (k + half) * ppm
        d.line([(x, 952), (x, 960)], fill=(255, 255, 255))
        d.line([(0, x), (8, x)], fill=(255, 255, 255))
    im.convert("RGB").save(out / f"{name}.jpg", quality=88)
    print(out / f"{name}.jpg")
