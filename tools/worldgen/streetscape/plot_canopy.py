"""Tree crowns around the single-family houses, read off the GUGiK orthophoto (ADR 0132).

    uv run --project tools/worldgen python tools/worldgen/streetscape/plot_canopy.py --region bialystok-industrial-c
        [--preview out.jpg cx cy r]      (local metres; crowns drawn over the orthophoto crop, QA only)

Why. The reference frames of the house streets (docs/refs/posesje-bialystok.md) are dominated by trees taller than the
houses and by shrubs along the fences; BDOT10k has no garden trees (OT_OIPR_P: a handful of points) and GUGiK "Modele 3D
drzew" / NMPT are not ingested. The 0.25 m orthophoto mosaic (Data/Regions/<id>/ortho.json, GUGiK open data, summer
flight) shows every crown. It stays what docs/05 par. 3 says it is - a reference, never a texture: only POSITIONS and
crown RADII are derived here, no pixel reaches the game.

Method (all thresholds WORKING_VALUE, tuned by eye on the preview overlays, artifacts/buildings-r9/canopy/*.jpg):
  vegetation  green chromaticity g / (r + g + b) > G_MIN and g > r, g > b
  crown       vegetation that is dark (local luma < LUMA_MAX: crowns are self-shadowed, lawns and dry grass are bright)
              or rough (local luma std > STD_MIN), opened / closed by 0.25-0.75 m
  crowns      local maxima of the distance transform of the crown mask: centre + radius (R_SHRUB_M .. R_MAX_M), greedy
              from the largest, two crowns never closer than 0.8 x the sum of their radii
  conifer     crown whose mean colour is dark and blue-ish (b / g > CONIFER_BG): spruce / thuja, else broadleaf
Only crowns within REACH_M of a house footprint are kept (forests and street trees have their own sources), never
inside a BDOT forest polygon, never centred on a building. Output: Data/Regions/<id>/plot_canopy.json (in git): crowns
in region-local metres [e, n, r, conifer 0/1, luma]. The streetscape stage reads the JSON (plots.py); without it the
garden trees fall back to the hash rule of ADR 0124.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
from scipy import ndimage

REPO = Path(__file__).resolve().parents[3]
G_MIN = 0.345
LUMA_MAX = 118.0
STD_MIN = 8.0
LUMA_VEG_MAX = 150.0
R_SHRUB_M = 0.7
R_TREE_M = 1.25
R_MAX_M = 6.5
REACH_M = 45.0
CONIFER_BG = 0.80
CONIFER_LUMA = 62.0
VERSION = 1


def _disk(r):
    y, x = np.ogrid[-r:r + 1, -r:r + 1]
    return x * x + y * y <= r * r


def crown_mask(rgb):
    """rgb uint8 [H, W, 3] at 0.25 m -> (crown mask bool, luma float32)."""
    a = rgb.astype(np.float32)
    s = a.sum(2) + 1.0
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    luma = 0.299 * r + 0.587 * g + 0.114 * b
    veg = (g / s > G_MIN) & (g >= r) & (g >= 0.97 * b) & (luma < LUMA_VEG_MAX)
    m1 = ndimage.uniform_filter(luma, 9)
    m2 = ndimage.uniform_filter(luma * luma, 9)
    std = np.sqrt(np.maximum(m2 - m1 * m1, 0.0))            # roughness over 2.25 m: lit / shaded lumps of a crown
    # a crown is ROUGH vegetation; a lush meadow or a watered lawn is as green and as dark, but smooth
    crown = veg & (std > STD_MIN) & (m1 < LUMA_MAX)
    # deep shade inside a crown has no chroma: dark texels touching a crown belong to it
    dark = (luma < 45.0) & ndimage.binary_dilation(crown, iterations=2)
    crown = ndimage.binary_opening(crown | dark, structure=np.ones((3, 3), bool), iterations=1)
    crown = ndimage.binary_closing(crown, structure=np.ones((3, 3), bool), iterations=2)
    crown = ndimage.binary_opening(crown, structure=_disk(2))
    return crown, luma


def crowns_of(mask, rgb, res=0.25):
    """Crown mask -> [(row, col, radius m, conifer, luma)] greedy from the largest."""
    dist = ndimage.distance_transform_edt(mask) * res
    k = int(round(R_SHRUB_M / res))
    peak = (dist == ndimage.maximum_filter(dist, size=2 * k + 1)) & (dist >= R_SHRUB_M)
    jj, ii = np.nonzero(peak)
    order = np.argsort(-dist[jj, ii], kind="stable")
    a = rgb.astype(np.float32)
    out = []
    cell = {}                                                # 8 m grid of accepted crowns (greedy separation test)
    for o in order:
        j, i = int(jj[o]), int(ii[o])
        rr = float(min(dist[j, i], R_MAX_M))
        cj, ci = int(j * res // 8), int(i * res // 8)
        ok = True
        for dj in (-2, -1, 0, 1, 2):
            for di in (-2, -1, 0, 1, 2):
                for (j2, i2, r2) in cell.get((cj + dj, ci + di), ()):
                    if np.hypot(j - j2, i - i2) * res < 0.8 * (rr + r2):
                        ok = False
                        break
                if not ok:
                    break
            if not ok:
                break
        if not ok:
            continue
        cell.setdefault((cj, ci), []).append((j, i, rr))
        q = max(1, int(rr / res * 0.6))
        win = a[max(j - q, 0):j + q + 1, max(i - q, 0):i + q + 1].reshape(-1, 3).mean(0)
        luma = float(0.299 * win[0] + 0.587 * win[1] + 0.114 * win[2])
        conifer = int(win[2] / max(win[1], 1.0) > CONIFER_BG and luma < CONIFER_LUMA)
        out.append((j, i, rr, conifer, luma))
    return out


def _load(region_id):
    import rasterio
    import yaml
    rdir = REPO / "Data" / "Regions" / region_id
    reg = yaml.safe_load((rdir / "region.yaml").read_text(encoding="utf-8"))
    meta = json.loads((rdir / "ortho.json").read_text(encoding="utf-8"))
    return rdir, reg, meta, rasterio.open(REPO / meta["file"])


def build(region_id):
    import shapely
    from rasterio import features as RF
    from rasterio.transform import from_origin
    rdir, reg, meta, ds = _load(region_id)
    ox, oy = reg["origin"]["x"], reg["origin"]["y"]
    res = float(meta["res_m"])
    sys.path.insert(0, str(REPO / "tools" / "worldgen"))
    from streetscape import buildings_mesh as BM
    from streetscape import paved as PV
    from streetscape import sources as SRC
    from roads import pipeline
    src = SRC.load(region_id)
    origin = np.array([ox, oy])
    fc = json.loads((rdir / "buildings.geojson").read_text(encoding="utf-8"))
    blds = BM.load(fc, origin, pipeline.load_overrides(region_id))
    houses = [b["poly"] for b in blds if b["typ"] == "house"]
    allb = shapely.union_all([b["poly"] for b in blds])
    zone = shapely.union_all([h.buffer(REACH_M) for h in houses])
    polys = [PV._poly_local(f["geometry"]["coordinates"], origin) for f in src["bdot10k"].get("OT_PTLZ_A", [])]
    if polys:
        zone = zone.difference(shapely.union_all([p if p.is_valid else shapely.make_valid(p) for p in polys]))
    rgb = np.moveaxis(ds.read([1, 2, 3]), 0, 2)
    H, W = rgb.shape[:2]
    x0, y1 = ds.bounds.left, ds.bounds.top
    tr = from_origin(x0 - ox, y1 - oy, res, res)
    zmask = RF.rasterize([(zone, 1)], out_shape=(H, W), transform=tr, fill=0, dtype="uint8").astype(bool)
    bmask = RF.rasterize([(allb, 1)], out_shape=(H, W), transform=tr, fill=0, dtype="uint8").astype(bool)
    mask, _ = crown_mask(rgb)
    mask &= ndimage.binary_dilation(zmask, iterations=8)
    # a crown may hang over a roof, a roof is never a crown: the inside of the footprints is cut out
    cr = crowns_of(mask & ~ndimage.binary_erosion(bmask, iterations=4), rgb, res)
    out = []
    for j, i, r, con, luma in cr:
        if not zmask[j, i] or bmask[j, i]:
            continue
        out.append([round(x0 + (i + 0.5) * res - ox, 2), round(y1 - (j + 0.5) * res - oy, 2), round(r, 2), con, round(luma)])
    out.sort()
    doc = {"version": VERSION, "source": meta["source_manifest"], "ortho_sha256": meta["sha256"], "res_m": res,
           "units": "region-local metres (origin of region.yaml): [e, n, crown radius m, conifer, mean luma]",
           "params": {"G_MIN": G_MIN, "LUMA_MAX": LUMA_MAX, "STD_MIN": STD_MIN, "R_SHRUB_M": R_SHRUB_M, "R_TREE_M": R_TREE_M,
                      "R_MAX_M": R_MAX_M, "REACH_M": REACH_M, "CONIFER_BG": CONIFER_BG, "CONIFER_LUMA": CONIFER_LUMA},
           "counts": {"crowns": len(out), "trees": sum(1 for c in out if c[2] >= R_TREE_M),
                      "conifers": sum(1 for c in out if c[3] and c[2] >= R_TREE_M),
                      "shrubs": sum(1 for c in out if c[2] < R_TREE_M),
                      "crown_cover_of_zone": round(float((mask & zmask).sum()) / max(float(zmask.sum()), 1.0), 4)},
           "crowns": out}
    (rdir / "plot_canopy.json").write_text(json.dumps(doc, separators=(",", ":")).replace("],[", "],\n[") + "\n", encoding="utf-8")
    return doc


def load(region_id):
    """Crowns of the region as an array [n, 5] (e, n, r, conifer, luma) or None when the product is absent."""
    f = REPO / "Data" / "Regions" / region_id / "plot_canopy.json"
    if not f.exists():
        return None
    doc = json.loads(f.read_text(encoding="utf-8"))
    return np.asarray(doc["crowns"], float).reshape(-1, 5)


def preview(region_id, out, cx, cy, r):
    from PIL import Image, ImageDraw
    from rasterio.windows import from_bounds
    rdir, reg, meta, ds = _load(region_id)
    ox, oy = reg["origin"]["x"], reg["origin"]["y"]
    w = from_bounds(ox + cx - r, oy + cy - r, ox + cx + r, oy + cy + r, ds.transform)
    rgb = np.moveaxis(ds.read([1, 2, 3], window=w), 0, 2)
    mask, _ = crown_mask(rgb)
    cr = crowns_of(mask, rgb, float(meta["res_m"]))
    k = 2
    im = Image.fromarray(rgb).resize((rgb.shape[1] * k, rgb.shape[0] * k), Image.LANCZOS)
    edge = mask ^ ndimage.binary_erosion(mask)
    ov = np.asarray(im).copy()
    ov[np.kron(edge, np.ones((k, k), bool))] = (255, 255, 0)
    im2 = Image.fromarray(ov)
    d = ImageDraw.Draw(im2)
    for j, i, rr, con, luma in cr:
        px = rr / float(meta["res_m"]) * k
        col = (0, 200, 255) if con else ((255, 60, 60) if rr >= R_TREE_M else (255, 160, 255))
        d.ellipse([i * k - px, j * k - px, i * k + px, j * k + px], outline=col, width=2)
    Image.fromarray(np.concatenate([np.asarray(im), np.asarray(im2)], 1)).save(out, quality=88)
    print(out, len(cr), "crowns in the crop")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--region", default="bialystok-industrial-c")
    ap.add_argument("--preview", nargs=4, metavar=("OUT", "CX", "CY", "R"))
    a = ap.parse_args()
    if a.preview:
        preview(a.region, a.preview[0], *map(float, a.preview[1:]))
    else:
        doc = build(a.region)
        print(json.dumps(doc["counts"]), hashlib.sha256(json.dumps(doc["crowns"]).encode()).hexdigest()[:12])
