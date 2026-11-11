"""List OSM fire stations (amenity/building=fire_station) ranked by distance to the start route.

Usage (repo root):
    uv run --project tools/worldgen python tools/worldgen/streetscape/find_fire_station.py

Prints one JSON line per candidate: distance to the route polyline [m], OSM id, region-local
E/N [m], lon/lat, in-tile flag, tags.  Evidence for ADR 0070.
"""

from __future__ import annotations

import json
from pathlib import Path

import osmium
import yaml
from pyproj import Transformer
from shapely.geometry import LineString, Point, Polygon

REPO = Path(__file__).resolve().parents[3]
REGION = REPO / "Data" / "Regions" / "bialystok-industrial-c"
PBF = REPO / "Data" / "raw" / "osm" / "podlaskie-261108.osm.pbf"


def main() -> None:
    region = yaml.safe_load((REGION / "region.yaml").read_text(encoding="utf-8"))
    ox, oy = region["origin"]["x"], region["origin"]["y"]
    bb = region["bbox"]
    route = json.loads((REGION / "route_start.json").read_text(encoding="utf-8"))
    line = LineString([(e + ox, n + oy) for e, n in route["points_en"]])
    tr = Transformer.from_crs(4326, 2180, always_xy=True)
    fp = (osmium.FileProcessor(str(PBF)).with_locations()
          .with_filter(osmium.filter.TagFilter(("amenity", "fire_station"),
                                               ("building", "fire_station"))))
    out = []
    for o in fp:
        if o.is_node():
            pts = [(o.location.lon, o.location.lat)]
        elif o.is_way():
            try:
                pts = [(n.location.lon, n.location.lat) for n in o.nodes]
            except Exception:
                continue
        else:
            continue
        lon = sum(p[0] for p in pts) / len(pts)
        lat = sum(p[1] for p in pts) / len(pts)
        if not (22.9 < lon < 23.4 and 53.0 < lat < 53.25):
            continue
        xy = [tr.transform(*p) for p in pts]
        geom = Polygon(xy) if len(xy) >= 4 else Point(xy[0])
        c = geom.centroid
        out.append({
            "dist_route_m": round(line.distance(geom), 1),
            "osm_id": ("n" if o.is_node() else "w") + str(o.id),
            "e": round(c.x - ox, 1), "n": round(c.y - oy, 1),
            "lon": round(lon, 6), "lat": round(lat, 6),
            "in_tile": bb["xmin"] <= c.x <= bb["xmax"] and bb["ymin"] <= c.y <= bb["ymax"],
            "area_m2": round(geom.area, 1),
            "ring_en": [[round(x - ox, 2), round(y - oy, 2)] for x, y in xy] if len(xy) >= 4 else None,
            "tags": dict(o.tags),
        })
    out.sort(key=lambda d: d["dist_route_m"])
    for d in out[:12]:
        print(json.dumps(d, ensure_ascii=False))


if __name__ == "__main__":
    main()
