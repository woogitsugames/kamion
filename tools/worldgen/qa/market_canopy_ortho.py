"""Eave extents of the Knyszyn market canopies measured on the GUGiK orthophoto WMS (ADR 0227 D41; open data,
numbers only - no pixel is stored in git).

  measure:  uv run --project tools/worldgen python tools/worldgen/qa/market_canopy_ortho.py measure <out.json>
            -> per canopy: eave ends along its ridge axis, eave length / width, centre (EPSG:2180), and the clear gaps
               between consecutive canopies along the row; the input outlines are the current authored traces
               (overrides.yaml `kind: market_canopies_0227`, or the D41 geometry entry when present)
  classify: classify(rgb) on any (n, 3) array - the same code reads the synthetic rasters of
            tests/gis/test_rynek_p1_0227.py, so the generator outline and the photographed roofs use one ruler.

Method. One GetMap crop (WMS StandardResolution, layer Raster, EPSG:2180, same URL as qa/ortho_xsec.py and
qa/roundabout_ortho.py) of +-HALF m at RES m/px about the middle of the row. For every canopy a profile ALONG its
ridge axis (long axis of the minimum rectangle of the trace, through its centre), over +-BAND m across the ridge
(station = roof when >= ROOF_FRACTION of the band is roof): pixel = roof (dark graphite metal: blue-grey, B > R; the sunlit slopes are lighter but still bluish-green
G, B > R), shadow (very dark, v < SHADOW_V) or ground (light concrete / terracotta paving: R >= B). Eave ends = the
first non-roof run of >= MIN_GAP_M on either side of the centre (shorter runs = joints, PV frames, noise). Two
perpendicular profiles 0.3 m inside the hip starts (full width, no PV) give the eave width the same way. The clear gap between two canopies is the
distance between the facing eave ends along the mean row axis.

Accuracy. +-1 px (0.1 m) per edge on a clean edge, so +-0.2 m on a gap. Relief displacement of the roofs (~4 m above
the ground) is the same for neighbouring canopies of one height on one sheet, so it does not change the gaps; it
shifts absolute positions by up to ~0.5 m (UNVERIFIED: the sheet's projection centre is not published by the WMS).
The gaps between the three close canopies are shadowed ground (sun from the south); a gap narrower than MIN_GAP_M
would read as a joint - none is on this sheet. Sheet date: as in ADR 0227 (GUGiK 2025, 83186_1484206_N-34-106-B-b-1-2).
"""
from __future__ import annotations

import io
import json
import math
import sys
import time
import urllib.request
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[3]
WMS = ("https://mapy.geoportal.gov.pl/wss/service/PZGIK/ORTO/WMS/StandardResolution?SERVICE=WMS&VERSION=1.3.0"
       "&REQUEST=GetMap&LAYERS=Raster&STYLES=&CRS=EPSG:2180&BBOX={y0},{x0},{y1},{x1}&WIDTH={px}&HEIGHT={px}"
       "&FORMAT=image/png")
UA = {"User-Agent": "osm-research-client/1.0"}
HALF, RES = 70.0, 0.1
BAND = 1.2            # m either side of the trace centre line: the ridge zone (no PV within 0.25 of the half width) dominates
ROOF_FRACTION = 0.3
SEAM_STD = 9.0        # spread of B - R across a band that crosses the roof seams (concrete ~2-4)
STEP = 0.05
REACH = 8.0           # m sampled beyond the traced eave ends
MIN_GAP_M = 0.3       # a non-roof run shorter than this is a joint / frame / noise, not an eave end
SHADOW_V = 70.0
MARKET_KINDS = ("market_canopies_0227",)
GEOMETRY_KIND = "market_canopy_geometry_d41"


def classify(rgb):
    """(n, 3) RGB 0-255 -> 0 ground, 1 roof, 2 shadow. Graphite standing-seam roofs read blue-grey on GUGiK 2025
    (shade side v ~ 95, B - R ~ 37; sun side v ~ 160, G - R ~ 15-25); concrete is neutral to warm (B - R <= 0),
    terracotta stripes warm (R > G > B), shadow on the ground v < SHADOW_V."""
    a = np.asarray(rgb, float).reshape(-1, 3)
    r, g, b = a[:, 0], a[:, 1], a[:, 2]
    v = a.mean(1)
    roof = ((0.5 * (g + b) - r) > 7.0) | ((v < 135.0) & (b - r > 12.0))
    out = np.where(roof, 1, 0)
    return np.where(v < SHADOW_V, 2, out)


def _runs_from(cls, k0, sign, min_px):
    """Index of the last roof pixel walking from k0 in `sign` direction until a non-roof run of >= min_px."""
    k, last, miss = k0, k0, 0
    while 0 < k < len(cls) - 1:
        k += sign
        if cls[k] == 1:
            last, miss = k, 0
        else:
            miss += 1
            if miss >= min_px:
                break
    return last


def frame(poly):
    """centre, unit long axis (pointing south-ish, -N), unit across, length, width of a 4-corner trace."""
    from shapely.geometry import Polygon
    pg = Polygon(np.asarray(poly, float))
    rect = np.asarray(pg.minimum_rotated_rectangle.exterior.coords, float)[:4]
    e = np.roll(rect, -1, axis=0) - rect
    L = np.hypot(*e.T)
    i = int(np.argmax(L))
    ax = e[i] / L[i]
    if ax[1] > 0:
        ax = -ax
    return np.asarray(pg.centroid.coords[0], float), ax, np.array([-ax[1], ax[0]]), float(L[i]), float(L[(i + 1) % 4])


def profile(sample, c, ax, across, half_len, band=BAND):
    """Classified profile along `ax` through c, +-half_len, over +-band across: a station is roof when at least
    ROOF_FRACTION of its band pixels are roof (the ridge band mixes the shade and the sun slope), shadow when at
    least half are shadow, else ground. sample(x, y) -> (n, 3)."""
    s = np.arange(-half_len, half_len + 1e-9, STEP)
    lat = np.arange(-band, band + 1e-9, RES)
    X = c[0] + s[:, None] * ax[0] + lat[None, :] * across[0]
    Y = c[1] + s[:, None] * ax[1] + lat[None, :] * across[1]
    rgb = sample(X.ravel(), Y.ravel()).reshape(len(s), len(lat), 3).astype(float)
    k = classify(rgb.reshape(-1, 3)).reshape(len(s), len(lat))
    roof, shade = (k == 1).mean(1), (k == 2).mean(1)
    # the sunlit slope of a standing-seam roof is striped (B - R swings -18..+41 across the seams); concrete and
    # terracotta are flat (B - R spread <= 4): a band crossing the seams reads as roof by its spread
    seams = (np.std(rgb[:, :, 2] - rgb[:, :, 0], axis=1) >= SEAM_STD) & (rgb.mean(axis=(1, 2)) >= SHADOW_V)
    return s, np.where((roof >= ROOF_FRACTION) | seams, 1, np.where(shade >= 0.5, 2, 0))


def measure_canopy(sample, poly):
    """Eave ends along the ridge (band +-BAND about the ridge line: clear of the PV rows) and the eave width across,
    read 0.3 m inside both hip starts (full roof width, no PV modules there)."""
    c, ax, across, L, W = frame(poly)
    s, cls = profile(sample, c, ax, across, L / 2 + REACH)
    k0 = int(np.argmin(np.abs(s)))
    if cls[k0] != 1:
        raise ValueError("canopy centre is not on a roof pixel")
    mp = max(1, int(round(MIN_GAP_M / STEP)))
    a0, a1 = s[_runs_from(cls, k0, -1, mp)], s[_runs_from(cls, k0, +1, mp)]
    mid = (a0 + a1) / 2
    widths, offs = [], []
    for at in (a0 + W / 2 - 0.3, a1 - W / 2 + 0.3):
        sw, clw = profile(sample, c + ax * at, across, ax, W / 2 + REACH, band=1.0)
        k1 = int(np.argmin(np.abs(sw)))
        if clw[k1] != 1:
            continue
        b0, b1 = sw[_runs_from(clw, k1, -1, mp)], sw[_runs_from(clw, k1, +1, mp)]
        widths.append(b1 - b0)
        offs.append((b0 + b1) / 2)
    if not widths:
        raise ValueError("no clean width station")
    ctr = c + ax * mid + across * float(np.mean(offs))
    return {"centre_epsg2180": [round(float(v), 2) for v in ctr],
            "axis": [round(float(v), 4) for v in ax],
            "eave_north_epsg2180": [round(float(v), 2) for v in c + ax * a0 + across * float(np.mean(offs))],
            "eave_south_epsg2180": [round(float(v), 2) for v in c + ax * a1 + across * float(np.mean(offs))],
            "eave_length_m": round(float(a1 - a0), 2), "eave_width_m": round(float(np.mean(widths)), 2),
            "width_stations_m": [round(float(w), 2) for w in widths],
            "trace_length_m": round(L, 2), "trace_width_m": round(W, 2)}


def gaps(rows):
    """Clear gaps between consecutive canopies (north to south) along the mean row axis."""
    ax = np.mean([r["axis"] for r in rows], axis=0)
    ax /= np.hypot(*ax)
    order = sorted(rows, key=lambda r: float(np.asarray(r["centre_epsg2180"]) @ ax))
    out = []
    for p, q in zip(order, order[1:]):
        g = float((np.asarray(q["eave_north_epsg2180"]) - np.asarray(p["eave_south_epsg2180"])) @ ax)
        out.append({"between": [p["id"], q["id"]], "clear_gap_m": round(g, 2)})
    return [r["id"] for r in order], out


def rectangle(row, width=None):
    """Four EPSG:2180 corners of the measured eave rectangle (north-west first, clockwise)."""
    ax = np.asarray(row["axis"], float)
    across = np.array([-ax[1], ax[0]])
    c = np.asarray(row["centre_epsg2180"], float)
    hl, hw = row["eave_length_m"] / 2, (width or row["eave_width_m"]) / 2
    pts = [c - ax * hl - across * hw, c - ax * hl + across * hw, c + ax * hl + across * hw, c + ax * hl - across * hw]
    return [[round(float(x), 2), round(float(y), 2)] for x, y in pts]


def _authored(region="knyszyn"):
    import yaml
    ov = yaml.safe_load((REPO / "Data/Regions" / region / "overrides.yaml").read_text(encoding="utf-8"))["overrides"]
    base = next(o for o in ov if o.get("kind") in MARKET_KINDS)
    return [(c["id"], c["polygon_epsg2180"]) for c in base["canopies"]]


def measure(out):
    from PIL import Image
    canopies = _authored()
    P = np.vstack([np.asarray(p, float) for _, p in canopies])
    cx, cy = (P.min(0) + P.max(0)) / 2
    px = int(round(2 * HALF / RES))
    u = WMS.format(x0=cx - HALF, x1=cx + HALF, y0=cy - HALF, y1=cy + HALF, px=px)
    for k in range(4):
        try:
            data = urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=120).read()
            break
        except Exception:
            time.sleep(2 ** (k + 1))
    else:
        raise SystemExit("WMS failed")
    A = np.asarray(Image.open(io.BytesIO(data)).convert("RGB"), float)

    def sample(x, y):
        col = np.clip(((np.asarray(x) - (cx - HALF)) / RES).astype(int), 0, px - 1)
        row = np.clip((((cy + HALF) - np.asarray(y)) / RES).astype(int), 0, px - 1)
        return A[row, col]

    rows = []
    for cid, poly in canopies:
        r = measure_canopy(sample, poly)
        r["id"] = cid
        rows.append(r)
    order, gp = gaps(rows)
    doc = {"source": "GUGiK ORTO WMS StandardResolution, layer Raster (GUGiK 2025 sheet per ADR 0227); numbers only",
           "method": "tools/worldgen/qa/market_canopy_ortho.py (docstring)", "crop_centre_epsg2180": [cx, cy],
           "res_m": RES, "band_m": BAND, "min_gap_m": MIN_GAP_M, "accuracy": "+-0.1 m per edge, +-0.2 m per gap",
           "order_north_to_south": order, "canopies": rows, "gaps": gp,
           "rectangles_epsg2180": {r["id"]: rectangle(r) for r in rows}}
    Path(out).write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"gaps": gp, "lengths": {r["id"]: r["eave_length_m"] for r in rows},
                      "widths": {r["id"]: r["eave_width_m"] for r in rows}}, indent=1))


def main(argv):
    if len(argv) == 2 and argv[0] == "measure":
        measure(argv[1])
    else:
        raise SystemExit(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])
