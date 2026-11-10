"""OSM ground truth for road fidelity (ADR 0075): every highway way in the tile (+ margin) with ALL its tags,
plus the OSM features that describe separations (landuse=grass areas, junction=roundabout rings,
crossing:island nodes, traffic_signals / stop / give_way nodes).

Source: the Geofabrik extract named in Data/SourceManifests/osm-geofabrik-podlaskie.json (file slice, never the
public Overpass / tile servers, docs/05 §3). ODbL 1.0, © OpenStreetMap contributors.

Output (gitignored cache): Data/raw/derived/<region>/fidelity_osm_<sha8>.json, coordinates EPSG:2180 (double).
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
MARGIN_M = 150.0
NODE_KEYS = {"highway": {"traffic_signals", "stop", "give_way", "crossing", "turning_circle", "mini_roundabout"},
             "crossing:island": None, "traffic_calming": None}


def manifest():
    return json.loads((REPO / "Data/SourceManifests/osm-geofabrik-podlaskie.json").read_text(encoding="utf-8"))


def _bbox(region):
    b = region["bbox"]
    return (b["xmin"] - MARGIN_M, b["ymin"] - MARGIN_M, b["xmax"] + MARGIN_M, b["ymax"] + MARGIN_M)


def extract(region: dict, force=False) -> dict:
    import osmium
    from pyproj import Transformer
    man = manifest()
    pbf = REPO / man["local_path"]
    cache = REPO / "Data/raw/derived" / region["id"] / f"fidelity_osm_{man['sha256'][:8]}.json"
    if cache.exists() and not force:
        return json.loads(cache.read_text(encoding="utf-8"))
    x0, y0, x1, y1 = _bbox(region)
    to_wgs = Transformer.from_crs(2180, 4326, always_xy=True)
    to_2180 = Transformer.from_crs(4326, 2180, always_xy=True)
    lons, lats = to_wgs.transform([x0, x1, x0, x1], [y0, y0, y1, y1])
    lo0, lo1, la0, la1 = min(lons), max(lons), min(lats), max(lats)
    ways, areas, nodes = [], [], []
    fp = (osmium.FileProcessor(str(pbf)).with_locations()
          .with_filter(osmium.filter.KeyFilter("highway", "landuse", "area:highway", "traffic_calming",
                                               "crossing:island")))
    for o in fp:
        if o.is_node():
            lo, la = o.location.lon, o.location.lat
            if not (lo0 <= lo <= lo1 and la0 <= la <= la1):
                continue
            tg = dict(o.tags)
            keep = any(k in tg and (v is None or tg[k] in v) for k, v in NODE_KEYS.items())
            if keep:
                x, y = to_2180.transform(lo, la)
                nodes.append({"id": o.id, "xy": [round(x, 3), round(y, 3)], "tags": tg})
            continue
        if not o.is_way():
            continue
        try:
            ll = [(n.location.lon, n.location.lat) for n in o.nodes]
        except Exception:
            continue
        if not any(lo0 <= a <= lo1 and la0 <= b <= la1 for a, b in ll):
            continue
        tg = dict(o.tags)
        xs, ys = to_2180.transform([a for a, _ in ll], [b for _, b in ll])
        geom = [[round(x, 3), round(y, 3)] for x, y in zip(xs, ys)]
        rec = {"id": o.id, "tags": tg, "nodes": [n.ref for n in o.nodes], "geometry": geom}
        if "highway" in tg and tg.get("area") != "yes":
            ways.append(rec)
        elif tg.get("landuse") == "grass" or "area:highway" in tg or tg.get("area") == "yes":
            areas.append(rec)
    out = {"source": {"id": man["id"], "url": man["url"], "snapshot": man["snapshot"], "sha256": man["sha256"],
                      "downloaded_utc": man["downloaded_utc"], "license": man["license"],
                      "attribution": man["attribution"]},
           "crs": "EPSG:2180", "bbox": [x0, y0, x1, y1],
           "ways": sorted(ways, key=lambda r: r["id"]), "areas": sorted(areas, key=lambda r: r["id"]),
           "nodes": sorted(nodes, key=lambda r: r["id"])}
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps(out, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    return out


def digest(osm: dict) -> str:
    return hashlib.sha256(json.dumps(osm, sort_keys=True).encode()).hexdigest()
