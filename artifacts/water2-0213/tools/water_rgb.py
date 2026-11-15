"""ADR 0213: mean / median sRGB of the open water on the GUGiK orthophoto 2024 vs the top control render (same footprint).
uv run --project tools/worldgen python artifacts/water2-0213/tools/water_rgb.py <region> <cam_id> [<render.png> ...]
  -> prints one line per source; writes artifacts/water2-0213/<region>/ortho/<cam_id>.jpg (ortho crop, render footprint)
Water mask = BDOT10k OT_PTWP_A + OSM water areas (not intermittent) of generated/water_sources.json, eroded 3 m (no bank
pixels), minus 14 m around bridge edges (deck + its shadow). Top camera: eye 150 m over the NMT, vfov 50, 16:9, north up.
"""
import json
import math
import sys
from pathlib import Path

import numpy as np
import rasterio
import shapely
import shapely.geometry as G
from PIL import Image
from rasterio.windows import from_bounds

ROOT = Path(__file__).resolve().parents[3]
reg, cam = sys.argv[1], sys.argv[2]
renders = sys.argv[3:]
R = ROOT / "Data/Regions" / reg
import yaml
ry = yaml.safe_load((R / "region.yaml").read_text(encoding="utf-8"))
ox, oy = ry["origin"]["x"], ry["origin"]["y"]
cams = json.loads((R / "control_cameras_place.authored.json").read_text(encoding="utf-8"))["cameras"]
c = [k for k in cams if k["id"] == cam][0]
cx, cy = ox + c["pos_en"][0], oy + c["pos_en"][1]
vh = 2 * c["eye_m"] * math.tan(math.radians(c["fov_deg"] / 2))
hw = vh * 16 / 9
src = json.loads((R / "generated/water_sources.json").read_text(encoding="utf-8"))
polys = [G.shape(f["geometry"]) for f in src["bdot10k"]["OT_PTWP_A"]]
polys += [G.shape(a["geometry"]) for a in src["osm"]["areas"] if a["tags"].get("intermittent") != "yes"]
water = shapely.union_all([shapely.make_valid(p) for p in polys]).buffer(-3.0)
g = json.loads((R / "roads.graph.json").read_text(encoding="utf-8"))
br = [G.LineString(e["geometry"]) for e in g["edges"] if (e["attrs"].get("bridge") or {}).get("v") not in (None, "no")]
if br:
    water = water.difference(shapely.union_all(br).buffer(14.0))
shapely.prepare(water)
land = shapely.box(-1e7, -1e7, 1e7, 1e7).difference(water.buffer(28.0))
shapely.prepare(land)


def stats(rgb, E, N, name):
    ml = shapely.contains_xy(land, E.ravel(), N.ravel()).reshape(E.shape) & (rgb.sum(2) > 0)
    lp = rgb[ml].astype(float) @ np.array([0.2126, 0.7152, 0.0722])
    land_med = float(np.median(lp)) if len(lp) else float("nan")
    if len(lp):
        print(f"{name:28s} land median sRGB", np.median(rgb[ml].astype(float), 0))
    m = shapely.contains_xy(water, E.ravel(), N.ravel()).reshape(E.shape) & (rgb.sum(2) > 0)
    px = rgb[m].astype(float)
    if not len(px):
        print(f"{name:28s} no water pixels")
        return
    mean = px.mean(0)
    med = np.median(px, 0)
    lum = 0.2126 * mean[0] + 0.7152 * mean[1] + 0.0722 * mean[2]
    print(f"{name:28s} n={len(px):7d} mean sRGB {mean[0]:5.1f} {mean[1]:5.1f} {mean[2]:5.1f}  median {med[0]:4.0f} {med[1]:4.0f} "
          f"{med[2]:4.0f}  luma {lum:5.1f}  p10/p90 luma {np.percentile(px @ [0.2126, 0.7152, 0.0722], 10):5.1f}/"
          f"{np.percentile(px @ [0.2126, 0.7152, 0.0722], 90):5.1f}  land median luma {land_med:5.1f}  "
          f"water/land (median luma, linear) {(np.median(px @ [0.2126, 0.7152, 0.0722]) / 255) ** 2.2 / max((land_med / 255) ** 2.2, 1e-6):.3f}")


o = json.loads((R / "ortho.json").read_text(encoding="utf-8"))
ds = rasterio.open(ROOT / o["file"])
a = ds.read(window=from_bounds(cx - hw / 2, cy - vh / 2, cx + hw / 2, cy + vh / 2, ds.transform), boundless=True)[:3]
a = a.transpose(1, 2, 0)
H, W = a.shape[:2]
E, N = np.meshgrid(cx - hw / 2 + (np.arange(W) + 0.5) * hw / W, cy + vh / 2 - (np.arange(H) + 0.5) * vh / H)
stats(a, E, N, "orto 2024 " + cam)
od = ROOT / "artifacts/water2-0213" / reg / "ortho"
od.mkdir(parents=True, exist_ok=True)
Image.fromarray(a).resize((1920, 1080)).save(od / f"{cam}.jpg", quality=90)
for rp in renders:
    im = np.asarray(Image.open(rp).convert("RGB"))
    H, W = im.shape[:2]
    E, N = np.meshgrid(cx - hw / 2 + (np.arange(W) + 0.5) * hw / W, cy + vh / 2 - (np.arange(H) + 0.5) * vh / H)
    stats(im, E, N, Path(rp).parent.name + " " + Path(rp).stem)
