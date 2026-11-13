"""Read the cached Geofabrik extract and return Białystok layers as GeoDataFrames in EPSG:2180.

Layers:
  roads       – highway=* ways (LineString) with node ids + tags of interest
  landuse     – landuse=industrial / railway / commercial / retail / farmyard (areas)
  buildings   – building=* (areas)
  points      – highway=traffic_signals|stop|give_way|crossing|motorway_junction|mini_roundabout,
                door=loading_dock, amenity=fuel, etc. (nodes)

The parsed result is cached as GeoParquet-free pickles in Data/raw/derived/ (gitignored)
keyed by the extract sha256, so re-runs are fast and deterministic.
"""

from __future__ import annotations

import hashlib
import pickle
from pathlib import Path

import geopandas as gpd
import osmium
import shapely
from shapely import wkb

from fetch_osm import REPO_ROOT, download, load_manifest

WORK_CRS = "EPSG:2180"
# Białystok + ring road/S8/S19 surroundings, WGS84 (lon_min, lat_min, lon_max, lat_max)
BBOX_WGS84 = (22.98, 53.05, 23.32, 53.20)

ROAD_TAGS = (
    "highway", "name", "ref", "lanes", "lanes:forward", "lanes:backward", "maxspeed",
    "turn:lanes", "turn:lanes:forward", "turn:lanes:backward", "oneway", "junction",
    "surface", "bridge", "tunnel", "layer", "maxweight", "maxheight", "hgv", "access",
    "width", "sidewalk", "lit", "destination", "destination:ref", "int_ref", "service",
    # ADR 0164: truck limits (kept in sync with roadgraph.TRUCK_LIMIT_TAGS)
    "maxaxleload", "maxlength", "maxweight:hgv", "hgv:conditional", "maxgvweightrating:hgv",
)
AREA_KEYS_LANDUSE = {"industrial", "railway", "commercial", "retail", "farmyard", "construction"}
POINT_KEYS = {
    "highway": {"traffic_signals", "stop", "give_way", "crossing", "motorway_junction",
                "mini_roundabout", "bus_stop", "street_lamp"},
    "door": {"loading_dock"},
    "amenity": {"fuel", "loading_dock"},
    "railway": {"level_crossing", "crossing"},
}
CACHE_DIR = REPO_ROOT / "Data" / "raw" / "derived"


def _in_bbox(lon: float, lat: float) -> bool:
    x0, y0, x1, y1 = BBOX_WGS84
    return x0 <= lon <= x1 and y0 <= lat <= y1


def _parse(pbf: Path) -> dict[str, list[dict]]:
    bbox_poly = shapely.box(*BBOX_WGS84)
    wkbf = osmium.geom.WKBFactory()
    roads, landuse, buildings, points = [], [], [], []

    fp = (osmium.FileProcessor(str(pbf))
          .with_locations()
          .with_areas(osmium.filter.KeyFilter("landuse", "building"))
          .with_filter(osmium.filter.KeyFilter("highway", "landuse", "building", "door",
                                               "amenity", "railway")))
    for obj in fp:
        if obj.is_node():
            loc = obj.location
            if not loc.valid() or not _in_bbox(loc.lon, loc.lat):
                continue
            t = obj.tags
            hit = [k for k, vals in POINT_KEYS.items() if t.get(k) in vals]
            if not hit:
                continue
            points.append({
                "osm_id": obj.id, "kind": f"{hit[0]}={t.get(hit[0])}",
                **{k: t.get(k) for k in ("highway", "door", "amenity", "railway", "name", "ref",
                                         "crossing", "traffic_signals")},
                "geometry": shapely.Point(loc.lon, loc.lat),
            })
        elif obj.is_way():
            t = obj.tags
            if "highway" not in t:
                continue
            try:
                nodes = [(n.ref, n.location.lon, n.location.lat) for n in obj.nodes]
            except osmium.InvalidLocationError:
                continue
            if len(nodes) < 2:
                continue
            geom = shapely.LineString([(lo, la) for _, lo, la in nodes])
            if not geom.intersects(bbox_poly):
                continue
            rec = {"osm_id": obj.id, "node_ids": [n[0] for n in nodes]}
            rec.update({k: t.get(k) for k in ROAD_TAGS})
            rec["geometry"] = geom
            roads.append(rec)
        elif obj.is_area():
            t = obj.tags
            lu = t.get("landuse")
            b = t.get("building")
            if lu not in AREA_KEYS_LANDUSE and b is None:
                continue
            try:
                geom = wkb.loads(wkbf.create_multipolygon(obj), hex=True)
            except Exception:  # broken multipolygon in source data – skipped, counted by caller
                continue
            if not geom.intersects(bbox_poly):
                continue
            base = {"osm_id": obj.orig_id(), "osm_type": "way" if obj.from_way() else "relation",
                    "name": t.get("name"), "geometry": geom}
            if b is not None:
                buildings.append({**base, "building": b, "levels": t.get("building:levels"),
                                  "height": t.get("height"), "industrial": t.get("industrial"),
                                  "shop": t.get("shop"), "landuse": lu})
            if lu in AREA_KEYS_LANDUSE:
                landuse.append({**base, "landuse": lu, "industrial": t.get("industrial"),
                                "operator": t.get("operator")})
    return {"roads": roads, "landuse": landuse, "buildings": buildings, "points": points}


def load_layers() -> dict[str, gpd.GeoDataFrame]:
    pbf = download()
    sha = load_manifest()["sha256"]
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    # the kept tag list is part of the key (ADR 0069 added destination:ref; a stale pickle silently dropped it)
    tags_key = hashlib.sha1(repr(ROAD_TAGS).encode()).hexdigest()[:8]
    cache = CACHE_DIR / f"bialystok_layers_{sha[:16]}_{tags_key}.pkl"
    if cache.exists():
        raw = pickle.loads(cache.read_bytes())
    else:
        print(f"[osm_extract] parsing {pbf.name} (one-off, cached afterwards)")
        raw = _parse(pbf)
        cache.write_bytes(pickle.dumps(raw))
    out = {}
    for name, recs in raw.items():
        gdf = gpd.GeoDataFrame(recs, geometry="geometry", crs="EPSG:4326")
        sort_cols = [c for c in ("osm_type", "osm_id") if c in gdf.columns]
        gdf = gdf.sort_values(sort_cols).reset_index(drop=True)  # determinism
        out[name] = gdf.to_crs(WORK_CRS)
    return out


if __name__ == "__main__":
    layers = load_layers()
    for k, v in layers.items():
        print(k, len(v))
