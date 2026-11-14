"""ADR 0179 - points of an authored lamp row on the median of a dual carriageway (helper for `lamp_rows.json`).

The row itself is authored data (`Data/Regions/<id>/lamp_rows.json`, read by streetscape.furniture.lamp_rows); this
script only derives the median axis, so the numbers in the JSON can be reproduced:

    uv run --project tools/worldgen python tools/worldgen/qa/median_lamp_row.py --region bialystok-dojlidy \
        --name "Jacka Kuronia" --spacing 35 --min-gap 8 --max-gap 20

Median axis = midpoint between the axis of the carriageway whose geometry runs east and the nearest point of the
opposite carriageway of the same street name (roads.graph.json, OSM axes). Points where the two axes are closer than
--min-gap or farther than --max-gap are skipped (no median / junction bulb). Prints region-local E/N.
"""
import argparse
import json
from pathlib import Path

import numpy as np
import yaml
from shapely.geometry import LineString
from shapely.ops import linemerge, unary_union

REPO = Path(__file__).resolve().parents[3]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--region", required=True)
    ap.add_argument("--name", required=True)
    ap.add_argument("--spacing", type=float, default=35.0)
    ap.add_argument("--min-gap", type=float, default=8.0)
    ap.add_argument("--max-gap", type=float, default=20.0)
    ap.add_argument("--start", type=float, default=17.5, help="station of the first point on the east-bound axis")
    a = ap.parse_args()
    rdir = REPO / "Data" / "Regions" / a.region
    org = yaml.safe_load((rdir / "region.yaml").read_text(encoding="utf-8"))["origin"]
    o = np.array([org["x"], org["y"]])
    g = json.loads((rdir / "roads.graph.json").read_text(encoding="utf-8"))
    east, west, ways = [], [], set()
    for e in g["edges"]:
        if e["attrs"].get("name", {}).get("v") != a.name or e["attrs"].get("oneway", {}).get("v") != "yes":
            continue
        p = np.asarray(e["geometry"], float) - o
        (east if p[-1, 0] > p[0, 0] else west).append(LineString(p))
        ways.add(e["osm_way"])
    em = linemerge(east)
    lines = sorted(getattr(em, "geoms", [em]), key=lambda l: l.bounds[0])
    wm = unary_union(west)
    pts = []
    for l in lines:
        for s in np.arange(a.start, l.length, a.spacing):
            p = l.interpolate(float(s))
            q = wm.interpolate(wm.project(p))
            if a.min_gap <= p.distance(q) <= a.max_gap:
                pts.append([round((p.x + q.x) / 2, 1), round((p.y + q.y) / 2, 1)])
    print(json.dumps({"osm_way": sorted(ways), "points_en": pts}))


if __name__ == "__main__":
    main()
