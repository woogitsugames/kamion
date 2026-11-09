"""OSM context the road generator needs beyond roads.graph.json: crossings, signals, give-way/stop
points and footway/cycleway lines (to decide where sidewalks are plausible).

Written once per region to Data/Regions/<id>/generated/osm_context.json (small, committed) so road
generation is reproducible without the 30 MB OSM layer cache. ODbL: © OpenStreetMap contributors.
"""

from __future__ import annotations

import math

import shapely
from shapely.geometry import LineString

SCHEMA = "truck-sim-pl/osm-context/1"
FOOT = {"footway", "cycleway", "path", "pedestrian", "steps"}
POINT_KINDS = {"highway=crossing", "highway=traffic_signals", "highway=give_way", "highway=stop",
               "highway=bus_stop"}


def _clean(v):
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return None
    return v


def extract(bbox) -> dict:
    import osm_extract
    layers = osm_extract.load_layers()
    tile = shapely.box(*bbox)
    pts = []
    for r in layers["points"].sort_values("osm_id").itertuples():
        if r.kind not in POINT_KINDS or not tile.contains(r.geometry):
            continue
        d = {"osm_node": int(r.osm_id), "kind": r.kind, "x": round(r.geometry.x, 2), "y": round(r.geometry.y, 2)}
        for k in ("crossing", "traffic_signals"):
            v = _clean(getattr(r, k, None))
            if v is not None:
                d[k] = str(v)
        pts.append(d)
    roads = layers["roads"]
    foot = roads[roads.highway.isin(FOOT) & roads.geometry.intersects(tile)].sort_values("osm_id")
    lines = []
    for r in foot.itertuples():
        g = r.geometry.intersection(tile)
        parts = getattr(g, "geoms", [g])
        for k, part in enumerate(parts):
            if part.geom_type != "LineString" or part.length < 1.0:
                continue
            part = part.simplify(0.2)
            lines.append({"osm_way": int(r.osm_id), "part": k, "highway": r.highway,
                          "geometry": [[round(x, 2), round(y, 2)] for x, y in part.coords]})
    return {"schema": SCHEMA, "crs": "EPSG:2180", "bbox": list(bbox), "points": pts, "footways": lines,
            "license": "ODbL 1.0, © OpenStreetMap contributors"}


def footway_lines(ctx: dict) -> list[LineString]:
    return [LineString(f["geometry"]) for f in ctx["footways"]]
