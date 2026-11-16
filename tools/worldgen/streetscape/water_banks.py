"""Bank vegetation of the opt-in water stage, read off the GUGiK orthophoto (ADR 0213).

    uv run --project tools/worldgen python tools/worldgen/streetscape/water_banks.py --region dk65-02
        [--preview out.jpg cx cy r]      (local metres; classes drawn over the orthophoto crop, QA only)

Why. ADR 0210 left the river banks as a clean line of mown grass; the 2024 orthophoto of the Supraśl / Biała shows a
belt of tall herbaceous bank vegetation (reed, sedge, reed canary grass, nettle) 2-25 m wide on most of the banks,
willow / alder shrubs and single trees on the rest, and a few grazed or mown stretches down to the water. As in
ADR 0132 (plot_canopy) the orthophoto stays a reference, never a texture: only the WIDTH of the belt along the shore
and the POSITIONS / radii of woody crowns are derived here, no pixel reaches the game.

Method (thresholds WORKING_VALUE, tuned by eye on the preview overlays, artifacts/water2-0213/banks/*.jpg):
  shore       outline of the region's water bodies (water.Plan sources: BDOT10k OT_PTWP_A + OSM water areas, not
              intermittent), sampled every SHORE_STEP_M with the outward normal
  crown       plot_canopy.crown_mask (green, rough or self-shadowed lumps)
  tall herb   vegetation (green or straw: g >= b, not dark water) that is ROUGH at 1 m (luma std over 2.25 m >
              HERB_STD_MIN) and not a crown: a reed / sedge belt is a mottle of light blades and dark gaps; a mown or
              grazed meadow is smooth
  belt        walking out from the shore (0.5 m, then 1 m steps) the run of tall-herb cells (one gap cell allowed),
              starting within BELT_START_M of the water; its width is median-filtered along the shore (MEDIAN_N
              samples) and kept where >= BELT_MIN_M
  crowns      plot_canopy.crowns_of on the crowns within CROWN_REACH_M of the water, outside BDOT forests
Output: Data/Regions/<id>/water_banks.json (in git): belt runs (polylines of [e, n, nx, ny, width]) and crowns
[e, n, r] in region-local metres. The water stage (streetscape.water) builds reed ribbons and shrub instances from it;
without the file the banks stay as in ADR 0210.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import shapely
from scipy import ndimage

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "tools" / "worldgen"))
from streetscape import plot_canopy as PC  # noqa: E402

VERSION = 1
SHORE_STEP_M = 1.0
BELT_MAX_M = 24.0
BELT_START_M = 2.5
BELT_MIN_M = 1.5
MEDIAN_N = 9
OUT_EVERY = 2            # runs are written every 2 m (= reeds.SEG_M)
HERB_STD_MIN = 9.0       # luma std over 2.25 m (0.25 m pixels): mottled tall herbs vs smooth meadow
HERB_LUMA = (40.0, 165.0)
HERB_FRAC = 0.45         # share of tall-herb pixels in a 1 m cell
CROWN_FRAC = 0.5
ROAD_CLEAR_M = 3.0
CROWN_R_MIN = 1.0       # bank crowns smaller than this are the dark shore line, not a shrub
WOODY_LUMA = 72.0      # local mean luma (3.25 m) of a self-shadowed woody crown
CROWN_REACH_M = 18.0
BLOCK_PX = 1024
PAD_PX = 24


def _water_local(region_id, origin):
    from streetscape import water as WT
    src = WT.load(region_id)
    polys = []
    bd = src["bdot10k"]
    flow = [WT._local(f["geometry"], origin) for f in bd.get("OT_PTWP_A", [])]
    polys += flow
    bflow = shapely.union_all([shapely.make_valid(p) for p in flow]) if flow else None
    for a in src["osm"]["areas"]:
        t = a["tags"]
        if t.get("intermittent") == "yes":
            continue
        g = WT._local(a["geometry"], origin)
        if WT._flowing_area(t) and bflow is not None and g.intersects(bflow):
            continue
        polys.append(g)
    u = shapely.union_all([shapely.make_valid(p) for p in polys]) if polys else shapely.Polygon()
    return shapely.unary_union([p for p in WT._parts(u) if p.geom_type == "Polygon" and p.area >= WT.MIN_AREA_M2])


def classify(rgb):
    """rgb uint8 [H, W, 3] at 0.25 m -> (woody crown bool, tall herb bool). plot_canopy.crown_mask marks every rough
    green lump - on a river bank that is mostly the reed / sedge / nettle belt itself. A woody crown (willow, alder)
    is the DARK part of it (self-shadowed mass, local mean luma < WOODY_LUMA); the rest of the rough vegetation is
    the tall-herb belt."""
    crown, luma = PC.crown_mask(rgb)
    a = rgb.astype(np.float32)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    m1 = ndimage.uniform_filter(luma, 9)
    m2 = ndimage.uniform_filter(luma * luma, 9)
    std = np.sqrt(np.maximum(m2 - m1 * m1, 0.0))
    woody = crown & (ndimage.uniform_filter(luma, 13) < WOODY_LUMA)
    woody = ndimage.binary_opening(woody, structure=PC._disk(3))
    veg = (g >= 0.97 * b) & (m1 > HERB_LUMA[0]) & (m1 < HERB_LUMA[1]) & (r < 1.35 * g)
    herb = ((veg & (std > HERB_STD_MIN)) | crown) & ~woody
    return woody, herb


def _maps(ds, ox, oy, band):
    """1 m maps (2048 x 2048, row 0 = north) of crown / tall-herb share inside the band mask, + the 0.25 m crown mask
    (for crowns_of) as a sparse dict of blocks."""
    from rasterio.windows import Window
    H, W = ds.height, ds.width
    k = 4
    crown_f = np.zeros((H // k, W // k), np.float32)
    herb_f = np.zeros((H // k, W // k), np.float32)
    crown_px = {}
    for by in range(0, H, BLOCK_PX):
        for bx in range(0, W, BLOCK_PX):
            if not band[by // k:(by + BLOCK_PX) // k, bx // k:(bx + BLOCK_PX) // k].any():
                continue
            y0, x0 = max(by - PAD_PX, 0), max(bx - PAD_PX, 0)
            y1, x1 = min(by + BLOCK_PX + PAD_PX, H), min(bx + BLOCK_PX + PAD_PX, W)
            rgb = np.moveaxis(ds.read([1, 2, 3], window=Window(x0, y0, x1 - x0, y1 - y0)), 0, 2)
            cr, hb = classify(rgb)
            sl = (slice(by - y0, by - y0 + BLOCK_PX), slice(bx - x0, bx - x0 + BLOCK_PX))
            cr, hb = cr[sl], hb[sl]
            hh, ww = cr.shape
            crown_f[by // k:by // k + hh // k, bx // k:bx // k + ww // k] = cr.reshape(hh // k, k, ww // k, k).mean((1, 3))
            herb_f[by // k:by // k + hh // k, bx // k:bx // k + ww // k] = hb.reshape(hh // k, k, ww // k, k).mean((1, 3))
            crown_px[(by, bx)] = (cr, rgb[sl])
    return crown_f, herb_f, crown_px


def build(region_id):
    from rasterio import features as RF
    from rasterio.transform import from_origin
    rdir, reg, meta, ds = PC._load(region_id)
    ox, oy = reg["origin"]["x"], reg["origin"]["y"]
    origin = np.array([ox, oy])
    res = float(meta["res_m"])
    x0, y1 = ds.bounds.left, ds.bounds.top
    water = _water_local(region_id, origin)
    tile = shapely.box(x0 - ox, ds.bounds.bottom - oy, ds.bounds.right - ox, y1 - oy)
    n1 = ds.height // 4
    tr1 = from_origin(x0 - ox, y1 - oy, 1.0, 1.0)
    wmask = RF.rasterize([(water, 1)], out_shape=(n1, n1), transform=tr1, fill=0, dtype="uint8").astype(bool) \
        if not water.is_empty else np.zeros((n1, n1), bool)
    band = ndimage.binary_dilation(wmask, iterations=int(BELT_MAX_M + 2)) & ~wmask
    crown_f, herb_f, crown_px = _maps(ds, ox, oy, band)
    # forests (BDOT OT_PTLZ_A): their own trees; no bank crowns inside them
    from streetscape import sources as SRC
    from streetscape import paved as PV
    src = SRC.load(region_id)
    fpolys = [PV._poly_local(f["geometry"]["coordinates"], origin) for f in src["bdot10k"].get("OT_PTLZ_A", [])]
    forest = shapely.union_all([p if p.is_valid else shapely.make_valid(p) for p in fpolys]) if fpolys else shapely.Polygon()
    fmask = RF.rasterize([(forest, 1)], out_shape=(n1, n1), transform=tr1, fill=0, dtype="uint8").astype(bool) \
        if not forest.is_empty else np.zeros((n1, n1), bool)

    def cell(e, n):
        i = np.clip(np.floor(e - (x0 - ox)).astype(int), 0, n1 - 1)
        j = np.clip(np.floor((y1 - oy) - n).astype(int), 0, n1 - 1)
        return j, i

    # roads / bridges (graph edges, width + ROAD_CLEAR_M each side): no belt on or under them
    graph = json.loads((rdir / "roads.graph.json").read_text(encoding="utf-8"))
    rp = []
    for e_ in graph["edges"]:
        wv = (e_["attrs"].get("width") or {}).get("v") or 6.0
        try:
            wv = float(wv)
        except (TypeError, ValueError):
            wv = 6.0
        rp.append(shapely.LineString(np.asarray(e_["geometry"], float) - origin).buffer(wv / 2 + ROAD_CLEAR_M))
    roads = shapely.union_all(rp) if rp else shapely.Polygon()
    rmask = RF.rasterize([(roads, 1)], out_shape=(n1, n1), transform=tr1, fill=0, dtype="uint8").astype(bool)         if not roads.is_empty else np.zeros((n1, n1), bool)
    herb_c = (herb_f >= HERB_FRAC) & ~rmask
    crown_c = crown_f >= CROWN_FRAC
    runs = []
    nshore = 0
    from streetscape import water as WT
    for ring in [r_ for p in WT._parts(water) for r_ in [p.exterior, *p.interiors]]:
        L = ring.length
        if L < 4 * SHORE_STEP_M:
            continue
        s = np.arange(0.0, L, SHORE_STEP_M)
        P = np.array([[ring.interpolate(x).x, ring.interpolate(x).y] for x in s])
        T = np.gradient(np.vstack([P[-1:], P, P[:1]]), axis=0)[1:-1]
        T /= np.maximum(np.linalg.norm(T, axis=1, keepdims=True), 1e-9)
        Nm = np.column_stack([T[:, 1], -T[:, 0]])
        # outward = away from the water (test 1.5 m out)
        q = P + Nm * 1.5
        jj, ii = cell(q[:, 0], q[:, 1])
        flip = wmask[jj, ii]
        Nm[flip] *= -1
        steps = np.concatenate([[0.5], np.arange(1.5, BELT_MAX_M + 0.1, 1.0)])
        width = np.zeros(len(P))
        inside = shapely.contains_xy(tile.buffer(-1.0), P[:, 0], P[:, 1])
        for k_ in range(len(P)):
            if not inside[k_]:
                continue
            Q = P[k_] + Nm[k_] * steps[:, None]
            jj, ii = cell(Q[:, 0], Q[:, 1])
            ok = herb_c[jj, ii] & ~wmask[jj, ii]
            started, gap, w = False, 0, 0.0
            for d, o in zip(steps, ok):
                if not started:
                    if o and d <= BELT_START_M:
                        started = True
                    elif d > BELT_START_M:
                        break
                    else:
                        continue
                if o:
                    gap, w = 0, d + 0.5
                else:
                    gap += 1
                    if gap > 1:
                        break
            width[k_] = w
        width = ndimage.median_filter(width, size=MEDIAN_N, mode="wrap")
        nshore += int(inside.sum())
        on = (width >= BELT_MIN_M) & inside
        lab, n = ndimage.label(on)
        for r_ in range(1, n + 1):
            idx = np.nonzero(lab == r_)[0]
            if len(idx) < 2 * OUT_EVERY + 1:
                continue
            runs.append([[round(float(P[k_, 0]), 2), round(float(P[k_, 1]), 2), round(float(Nm[k_, 0]), 3),
                          round(float(Nm[k_, 1]), 3), round(float(width[k_]) * 2) / 2] for k_ in idx[::OUT_EVERY]])
    # crowns near the water, outside forests
    near = ndimage.binary_dilation(wmask, iterations=int(CROWN_REACH_M)) & ~wmask & ~fmask & ~rmask
    crowns = []
    for (by, bx), (cr, rgb) in sorted(crown_px.items()):
        nb = near[by // 4:(by + cr.shape[0]) // 4, bx // 4:(bx + cr.shape[1]) // 4]
        m = cr & np.kron(nb, np.ones((4, 4), bool))[:cr.shape[0], :cr.shape[1]]
        if not m.any():
            continue
        for j, i, rr, con, luma in PC.crowns_of(m, rgb, res):
            if rr < CROWN_R_MIN:
                continue
            e = x0 + (bx + i + 0.5) * res - ox
            n_ = y1 - (by + j + 0.5) * res - oy
            crowns.append([round(e, 2), round(n_, 2), round(rr, 2)])
    crowns.sort()
    belt_m = sum(len(r_) for r_ in runs) * SHORE_STEP_M * OUT_EVERY
    doc = {"version": VERSION, "source": meta["source_manifest"], "ortho_sha256": meta["sha256"], "res_m": res,
           "units": "region-local metres (origin of region.yaml); runs: shore samples [e, n, outward nx, ny, belt width m] "
                    f"every {SHORE_STEP_M * OUT_EVERY} m; crowns: [e, n, crown radius m]",
           "params": {"BELT_MAX_M": BELT_MAX_M, "BELT_START_M": BELT_START_M, "BELT_MIN_M": BELT_MIN_M,
                      "MEDIAN_N": MEDIAN_N, "HERB_STD_MIN": HERB_STD_MIN, "HERB_LUMA": list(HERB_LUMA),
                      "HERB_FRAC": HERB_FRAC, "CROWN_FRAC": CROWN_FRAC, "WOODY_LUMA": WOODY_LUMA, "CROWN_R_MIN": CROWN_R_MIN, "ROAD_CLEAR_M": ROAD_CLEAR_M, "CROWN_REACH_M": CROWN_REACH_M},
           "counts": {"shore_m": nshore * SHORE_STEP_M, "belt_m": belt_m,
                      "belt_share": round(belt_m / max(nshore * SHORE_STEP_M, 1.0), 3), "runs": len(runs),
                      "crowns": len(crowns)},
           "runs": runs, "crowns": crowns}
    txt = json.dumps(doc, separators=(",", ":")).replace("],[", "],\n[") + "\n"
    (rdir / "water_banks.json").write_text(txt, encoding="utf-8", newline="\n")
    return doc


def load(region_id):
    f = REPO / "Data" / "Regions" / region_id / "water_banks.json"
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else None


def preview(region_id, out, cx, cy, r):
    """Orthophoto crop | the same crop with tall herb (yellow), crowns (red), belt runs (cyan width ticks)."""
    from PIL import Image, ImageDraw
    from rasterio.windows import from_bounds
    rdir, reg, meta, ds = PC._load(region_id)
    ox, oy = reg["origin"]["x"], reg["origin"]["y"]
    res = float(meta["res_m"])
    w = from_bounds(ox + cx - r, oy + cy - r, ox + cx + r, oy + cy + r, ds.transform)
    rgb = np.moveaxis(ds.read([1, 2, 3], window=w), 0, 2)
    cr, hb = classify(rgb)
    ov = rgb.copy()
    ov[hb] = (ov[hb] * 0.4 + np.array([255, 230, 0]) * 0.6).astype(np.uint8)
    ov[cr] = (ov[cr] * 0.5 + np.array([255, 40, 40]) * 0.5).astype(np.uint8)
    k = 2
    im2 = Image.fromarray(ov).resize((rgb.shape[1] * k, rgb.shape[0] * k), Image.NEAREST)
    d = ImageDraw.Draw(im2)
    doc = load(region_id)
    px = lambda e, n: ((e - (cx - r)) / res * k, ((cy + r) - n) / res * k)
    if doc:
        for run in doc["runs"]:
            for e, n, nx, ny, wd in run[::2]:
                if abs(e - cx) < r and abs(n - cy) < r:
                    d.line([px(e, n), px(e + nx * wd, n + ny * wd)], fill=(0, 255, 255), width=1)
        for e, n, rr in doc["crowns"]:
            if abs(e - cx) < r and abs(n - cy) < r:
                a, b = px(e, n)
                q = rr / res * k
                d.ellipse([a - q, b - q, a + q, b + q], outline=(255, 0, 255), width=2)
    im = Image.fromarray(rgb).resize((rgb.shape[1] * k, rgb.shape[0] * k), Image.LANCZOS)
    Image.fromarray(np.concatenate([np.asarray(im), np.asarray(im2)], 1)).save(out, quality=88)
    print(out)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--region", required=True)
    ap.add_argument("--preview", nargs=4, metavar=("OUT", "CX", "CY", "R"))
    a = ap.parse_args()
    if a.preview:
        preview(a.region, a.preview[0], *map(float, a.preview[1:]))
    else:
        doc = build(a.region)
        print(json.dumps(doc["counts"]), hashlib.sha256(json.dumps([doc["runs"], doc["crowns"]]).encode()).hexdigest()[:12])
