"""Roof tone of every building read off the region orthophoto -> generated override file (authored-override format).

  uv run --project tools/worldgen python tools/worldgen/qa/roof_tones_ortho.py --region knyszyn [--check]

Input : Data/raw/derived/<id>/ortho_0p25m.tif (GUGiK orthophoto resampled by build_region; reference use only, never a
        texture - docs/05 section 3), Data/Regions/<id>/buildings.geojson.
Output: Data/Regions/<id>/overrides.ortho_roofs.json - {"overrides": [{target: {building}, set: {roof_material}}...]},
        read by roads.pipeline.load_overrides BEFORE overrides.yaml, so a hand-authored entry for the same building
        wins. Regions without the file are untouched.

Method (all thresholds WORKING_VALUE, checked against the hand-read Rynek roofs, see --check):
  1. footprint shrunk by SHRINK_M (eaves, neighbours, georeferencing +-1 m); pixels inside it;
  2. vegetation dropped (green dominant), near-black dropped (photovoltaic panels, roof windows, deep shadow);
  3. the sunlit pitch only: pixels at or above the SUNLIT_PCT brightness percentile (a gable roof has one pitch in
     shade - its colour reads darker and bluer);
  4. median sRGB of the rest -> class by hue / saturation / value: red, brown, graphite, light grey;
  5. purity = share of the kept pixels whose own class equals the class of the median; below MIN_PURITY, under
     MIN_PX pixels or a class with no material -> no entry (the generator's neighbour palette decides).
The class -> material table only uses materials the house generator can draw (streetscape.buildings_mesh.ROOF_OVERRIDES).
"""
from __future__ import annotations

import argparse
import colorsys
import json
from pathlib import Path

import numpy as np
import rasterio
from rasterio import features
from rasterio.windows import from_bounds
from shapely.geometry import shape

REPO = Path(__file__).resolve().parents[3]
SHRINK_M = (1.2, 0.6)
SUNLIT_PCT = 55.0
MIN_PX = 40                    # 0.25 m pixels = 2.5 m2 of sunlit roof
MIN_PURITY = 0.55
MATERIAL = {"red": "roof_tiles_red", "brown": "roof_tiles_brown", "graphite": "roof_metal_graphite",
            "light_grey": "roof_sheet_grey"}
# hand-read roofs of ADR 0227 (overrides.yaml rynek-*-roof-0227): the classifier has to agree with them
CHECK = {"bdot:2002917F-3002-5C99-E053-CC2BA8C01CFC": "graphite", "bdot:2002917F-3066-5C99-E053-CC2BA8C01CFC": "red",
         "bdot:2002917F-3078-5C99-E053-CC2BA8C01CFC": "graphite", "bdot:2002917F-2E16-5C99-E053-CC2BA8C01CFC": "red"}


def classify_rgb(rgb):
    """Roof class of sRGB 0-255 values, array (..., 3) -> array of str ('' = none)."""
    a = np.asarray(rgb, dtype=float).reshape(-1, 3) / 255.0
    out = np.empty(len(a), dtype=object)
    for i, (r, g, b) in enumerate(a):
        h, s, v = colorsys.rgb_to_hsv(r, g, b)
        h *= 360.0
        warm = h <= 48.0 or h >= 340.0
        cool = 180.0 <= h <= 240.0           # sheet / felt roofs read blue-grey on the 2025 sheets (hue ~205, s 0.3)
        if s < 0.13 or (cool and s < 0.42):
            out[i] = "light_grey" if v >= 0.63 else "graphite"
        elif warm and s >= 0.26:
            out[i] = "red" if v >= 0.50 and (h <= 25.0 or h >= 340.0) else "brown" if v < 0.60 else ""
        elif warm:
            out[i] = "brown" if v < 0.50 else "light_grey" if s < 0.20 else ""
        else:
            out[i] = ""
    return out


def roof_pixels(img, transform, poly):
    for d in SHRINK_M:
        g = poly.buffer(-d)
        if not g.is_empty and g.area >= 6.0:
            break
    else:
        return None
    x0, y0, x1, y1 = g.bounds
    w = from_bounds(x0, y0, x1, y1, transform).round_offsets().round_lengths()
    c0, r0 = max(int(w.col_off), 0), max(int(w.row_off), 0)
    c1, r1 = min(c0 + int(w.width) + 1, img.shape[2]), min(r0 + int(w.height) + 1, img.shape[1])
    if c1 - c0 < 2 or r1 - r0 < 2:
        return None
    sub = img[:, r0:r1, c0:c1]
    tr = rasterio.windows.transform(rasterio.windows.Window(c0, r0, c1 - c0, r1 - r0), transform)
    m = features.geometry_mask([g], (r1 - r0, c1 - c0), tr, invert=True)
    px = sub[:, m].T.astype(float)
    if len(px) == 0:
        return None
    r, gch, b = px[:, 0], px[:, 1], px[:, 2]
    v = px.max(axis=1)
    keep = (v > 46) & ~((gch > r * 1.06) & (gch > b * 1.06))          # not near-black, not vegetation
    px = px[keep]
    if len(px) < MIN_PX:
        return None
    lum = px @ np.array([0.299, 0.587, 0.114])
    return px[lum >= np.percentile(lum, SUNLIT_PCT)]


def read(region):
    reg = REPO / "Data/Regions" / region
    tif = REPO / "Data/raw/derived" / region / "ortho_0p25m.tif"
    fc = json.loads((reg / "buildings.geojson").read_text(encoding="utf-8"))
    rows = {}
    with rasterio.open(tif) as ds:
        img = ds.read([1, 2, 3])
        tr = ds.transform
    for f in fc["features"]:
        poly = shape(f["geometry"])
        if poly.geom_type == "MultiPolygon":
            poly = max(poly.geoms, key=lambda q: q.area)
        px = roof_pixels(img, tr, poly)
        if px is None or len(px) < MIN_PX * (100 - SUNLIT_PCT) / 100:
            continue
        med = np.median(px, axis=0)
        cls = classify_rgb(med)[0]
        if not cls:
            continue
        purity = float(np.mean(classify_rgb(px[:: max(1, len(px) // 400)]) == cls))
        rows[f["id"]] = {"class": cls, "rgb": [int(round(c)) for c in med], "purity": round(purity, 2), "n": int(len(px)),
                         "function": f["properties"].get("function")}
    return rows, len(fc["features"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--region", required=True)
    ap.add_argument("--check", action="store_true", help="only compare with the hand-read roofs, write nothing")
    a = ap.parse_args()
    rows, total = read(a.region)
    bad = [(k, v, rows.get(k, {}).get("class")) for k, v in CHECK.items() if k in rows and rows[k]["class"] != v]
    if a.region == "knyszyn":
        for k, v in CHECK.items():
            print("check", k[-17:-13], v, rows.get(k))
    kept = {k: r for k, r in rows.items() if r["purity"] >= MIN_PURITY}
    hist = {}
    for r in kept.values():
        hist[r["class"]] = hist.get(r["class"], 0) + 1
    print(a.region, "buildings", total, "read", len(rows), "kept", len(kept), hist)
    if a.check:
        raise SystemExit(1 if bad else 0)
    out = {"schema": "truck-sim-pl/overrides-generated/1",
           "generator": "tools/worldgen/qa/roof_tones_ortho.py (do not edit by hand; hand-authored roofs go to "
                        "overrides.yaml and win)",
           "source": f"Data/raw/derived/{a.region}/ortho_0p25m.tif (Data/Regions/{a.region}/ortho.json; GUGiK orthophoto, "
                     "reference only)",
           "status": "ESTIMATED: class of the median sRGB of the sunlit roof pixels; thresholds WORKING_VALUE",
           "params": {"shrink_m": SHRINK_M, "sunlit_pct": SUNLIT_PCT, "min_px": MIN_PX, "min_purity": MIN_PURITY},
           "summary": {"buildings": total, "read": len(rows), "kept": len(kept), "classes": hist},
           "overrides": [{"id": f"roof-ortho:{k}", "target": {"building": k}, "confidence": "medium",
                          "reason": f"orthophoto roof tone {r['class']}, median sRGB {r['rgb']}, purity {r['purity']}, "
                                    f"{r['n']} px",
                          "verify": "street-level photo", "set": {"roof_material": MATERIAL[r["class"]]}}
                         for k, r in sorted(kept.items())]}
    p = REPO / "Data/Regions" / a.region / "overrides.ortho_roofs.json"
    p.write_text(json.dumps(out, ensure_ascii=False, indent=0) + "\n", encoding="utf-8")
    print("->", p, p.stat().st_size, "bytes")


if __name__ == "__main__":
    main()
