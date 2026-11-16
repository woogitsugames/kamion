"""ADR 0242: roof and ground levels of authored building volumes from the GUGiK digital surface model (NMPT 0.5 m,
PL-EVRF2007-NH), read through the public WCS - the source of the heights in Data/Regions/<id>/overrides.yaml that
used to be read off single photos.

    uv run --project tools/worldgen python tools/worldgen/qa/dsm_roof_levels.py --region bialystok-dojlidy \
        --bbox-en 0 220 800 560 [--cache <file.asc>]

Prints, per `building_part` override and per BDOT10k building cut by one, the DSM percentiles inside the ring
(shrunk by 0.8 m) and the 10th percentile of a 1.5-4 m ring outside it (ground beside the wall). Nothing is written
to the region; the grid is not kept in git (open data of GUGiK, Pgik art. 40a; attribution in docs/LICENSES.md).
The service does not state the survey date of a cell - treat the levels as +-0.2 m and the date as UNVERIFIED."""
import argparse
import json
import re
import sys
import urllib.request
from pathlib import Path

import numpy as np
import yaml
from shapely import contains_xy
from shapely.affinity import translate
from shapely.geometry import Polygon, shape

REPO = Path(__file__).resolve().parents[3]
WCS = ("https://mapy.geoportal.gov.pl/wss/service/PZGIK/NMPT/GRID1/WCS/DigitalSurfaceModel?SERVICE=WCS&VERSION=2.0.1"
       "&REQUEST=GetCoverage&COVERAGEID=DSM_PL-EVRF2007-NH&FORMAT=image/x-aaigrid")
UA = "osm-research-client/1.0"


def parse_aaigrid(raw):
    """(header dict, array rows north -> south) of an Arc/Info ASCII grid, also inside a multipart WCS reply."""
    txt = raw[raw.index(b"ncols"):]
    end = txt.find(b"\n--")
    lines = (txt[:end] if end > 0 else txt).split(b"\n")
    hdr, k = {}, 0
    while lines[k].split() and re.match(rb"[A-Za-z_]+$", lines[k].split()[0]):
        hdr[lines[k].split()[0].decode().lower()] = float(lines[k].split()[1])
        k += 1
    return hdr, np.loadtxt(lines[k:k + int(hdr["nrows"])], dtype=np.float32, ndmin=2)


def ring_stats(grid, hdr, poly, shrink=0.8):
    """DSM levels inside `poly` (coordinates of the grid) and the ground beside it."""
    nr, nc = grid.shape
    cs = hdr["cellsize"]
    xs = hdr["xllcorner"] + (np.arange(nc) + 0.5) * cs
    ys = hdr["yllcorner"] + (nr - np.arange(nr) - 0.5) * cs
    xx, yy = np.meshgrid(xs, ys)
    v = grid[contains_xy(poly.buffer(-shrink), xx, yy)]
    g = grid[contains_xy(poly.buffer(4.0).difference(poly.buffer(1.5)), xx, yy)]
    if not len(v) or not len(g):
        return None
    q = lambda a, p: round(float(np.percentile(a, p)), 2)
    return {"cells": int(len(v)), "roof_p5": q(v, 5), "roof_p50": q(v, 50), "roof_p95": q(v, 95),
            "roof_max": round(float(v.max()), 2), "ground_p10": q(g, 10)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--region", required=True)
    ap.add_argument("--bbox-en", nargs=4, type=float, required=True, metavar=("E0", "N0", "E1", "N1"),
                    help="region-local box, metres")
    ap.add_argument("--cache", help="keep / reuse the downloaded grid (outside git)")
    a = ap.parse_args()
    rd = REPO / "Data" / "Regions" / a.region
    org = yaml.safe_load((rd / "region.yaml").read_text(encoding="utf-8"))["origin"]
    ox, oy = float(org["x"]), float(org["y"])
    e0, n0, e1, n1 = a.bbox_en
    if a.cache and Path(a.cache).exists():
        raw = Path(a.cache).read_bytes()
    else:
        url = f"{WCS}&SUBSET=x({ox + e0},{ox + e1})&SUBSET=y({oy + n0},{oy + n1})"
        raw = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=180).read()
        if a.cache:
            Path(a.cache).write_bytes(raw)
    hdr, grid = parse_aaigrid(raw)
    hdr = {**hdr, "xllcorner": hdr["xllcorner"] - ox, "yllcorner": hdr["yllcorner"] - oy}      # region-local
    ov = (yaml.safe_load((rd / "overrides.yaml").read_text(encoding="utf-8")) or {}).get("overrides", [])
    parts = [o for o in ov if o.get("kind") == "building_part"]
    cut = {i for o in parts for i in o.get("cut_from") or []}
    rows = []
    for f in json.loads((rd / "buildings.geojson").read_text(encoding="utf-8"))["features"]:
        if f["properties"]["id"] in cut:
            p = f["properties"]
            rows.append((p["id"], translate(shape(f["geometry"]), -ox, -oy),
                         f"LoD1 {p.get('height_m')} m above {p.get('ground_z_evrf2007')}"))
    rows += [(o["id"], Polygon(o["polygon_en"]), f"authored {o['height_m']} m above {o.get('ground_z_evrf2007')}")
             for o in parts]
    for name, poly, note in rows:
        st = ring_stats(grid, hdr, poly)
        if st:
            print(f"{name}: {note}; DSM {st}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
