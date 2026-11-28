"""Streetscape source data for a region tile: paved areas, street furniture hints, vegetation, fences.

Read once from the raw OSM extract (Geofabrik, ODbL) and the county BDOT10k GeoPackage (GUGiK) and
written to Data/Regions/<id>/generated/streetscape_sources.json (small, committed) so the streetscape
generator is reproducible without the raw files. Coordinates: EPSG:2180, 2 decimals.

OSM (© OpenStreetMap contributors, ODbL 1.0):
  areas  amenity=parking, area:highway=*, highway=* + area=yes, landuse=* (industrial, commercial,
         retail, grass), leisure, natural=wood/scrub
  ways   barrier=* (fence, wall, guard_rail, hedge, retaining_wall, kerb, jersey_barrier),
         natural=tree_row, highway=footway/cycleway/path (for set-back sidewalks)
  nodes  highway=street_lamp|traffic_signals|bus_stop|crossing|give_way|stop|speed_camera,
         traffic_sign=*, natural=tree, barrier=gate|lift_gate|bollard, power=pole|tower,
         man_made=street_cabinet, amenity=* (bench, waste_basket, ...)
BDOT10k (GUGiK, version 2024-09-23):
  OT_PTPL_A plac (MATERIALNAWIERZCHNI), OT_KUKO_A parking / fuel station, OT_PTKM_A road land,
  OT_SKRP_L footpaths/cycle paths (aleja lub pasaż, droga dla rowerów), OT_OIKM_L noise barriers,
  OT_OIKM_P bus/tram stops, OT_OIPR_P single trees / shrub clumps, OT_OIPR_L tree rows,
  OT_PTLZ_A forest (KATEGORIA iglasty/liściasty/mieszany), OT_PTTR_A grassland, OT_PTNZ_A unbuilt land,
  OT_PTZB_A built-up land (RODZAJ), OT_BUUO_L retaining walls, OT_BUWT_P poles/masts, OT_SULN_L power lines.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import shapely
from shapely import wkb

SCHEMA = "truck-sim-pl/streetscape-sources/2"
REPO = Path(__file__).resolve().parents[3]

OSM_NODE_KEYS = {
    "public_transport": {"stop_position"},  # actual on-road stops, not platform/shelter projection (ADR0099)
    "highway": {"street_lamp", "traffic_signals", "bus_stop", "crossing", "give_way", "stop", "speed_camera",
                "milestone"},
    "barrier": {"gate", "lift_gate", "bollard", "swing_gate", "sliding_gate", "toll_booth", "block"},
    "natural": {"tree"},
    "power": {"pole", "tower"},
    "man_made": {"street_cabinet", "flagpole", "mast", "advertising"},
    "amenity": {"bench", "waste_basket", "parking_entrance", "post_box", "recycling", "vending_machine"},
    "advertising": None,
    "traffic_sign": None,
}
OSM_WAY_KEYS = {
    "barrier": None,
    "natural": {"tree_row"},
    "man_made": {"embankment"},
    "power": {"line", "minor_line"},
}
OSM_AREA_KEYS = {
    "amenity": {"parking", "fuel", "loading_dock"},
    "area:highway": None,
    "landuse": {"industrial", "commercial", "retail", "grass", "construction", "brownfield", "garages"},
    "natural": {"wood", "scrub", "grassland"},
    "leisure": {"park", "pitch", "playground"},
    "highway": None,           # only with area=yes
    "parking": None,
}
KEEP_TAGS = ("amenity", "area:highway", "landuse", "natural", "leisure", "highway", "parking", "surface", "name",
             "barrier", "fence_type", "material", "height", "traffic_sign", "direction", "traffic_signals",
             "crossing", "power", "man_made", "operator", "access", "area", "access", "support", "lamp_mount",
             "light:count", "maxspeed", "ref", "shelter", "bench", "bin", "public_transport", "covered", "leaf_type",
             "genus", "species", "leaf_cycle", "denotation", "layer", "location", "advertising", "wall", "bus",
             "cables", "voltage", "circuits", "line",
             # ADR 0279 P1 (D25): value of B-18 (node maxweight, e.g. Knyszyn osm:node/3047681870 maxweight=10 in the
             # OSM API 2026-11-16) and the direction key signs_route.osm_signs already reads
             "maxweight", "maxheight", "traffic_sign:direction")

BDOT_LAYERS = {
    "OT_PTPL_A": ("MATERIALNAWIERZCHNI",), "OT_KUKO_A": ("RODZAJ",), "OT_PTKM_A": (),
    "OT_SKRP_L": ("RODZAJ", "MATERIALNAWIERZCHNI", "SZEROKOSC"), "OT_OIKM_L": ("RODZAJ",),
    "OT_OIKM_P": ("RODZAJ", "NAZWA"), "OT_OIPR_P": ("RODZAJ",), "OT_OIPR_L": ("RODZAJ",),
    "OT_PTLZ_A": ("RODZAJ", "KATEGORIA"), "OT_PTTR_A": ("RODZAJ",), "OT_PTNZ_A": ("RODZAJ",),
    "OT_PTZB_A": ("RODZAJ",), "OT_BUUO_L": ("RODZAJ",), "OT_BUWT_P": ("RODZAJ", "WYSOKOSC"),
    "OT_SULN_L": ("RODZAJ",), "OT_PTRK_A": ("RODZAJ",),
}


def _round_geom(g):
    if g.geom_type == "Point":
        return {"type": "Point", "coordinates": [round(g.x, 2), round(g.y, 2)]}
    if g.geom_type == "LineString":
        return {"type": "LineString", "coordinates": [[round(x, 2), round(y, 2)] for x, y in g.coords]}
    if g.geom_type == "Polygon":
        return {"type": "Polygon", "coordinates": [[[round(x, 2), round(y, 2)] for x, y in r.coords]
                                                  for r in [g.exterior, *g.interiors]]}
    raise ValueError(g.geom_type)


def _parts(g):
    if g.is_empty:
        return []
    if hasattr(g, "geoms"):
        out = []
        for p in g.geoms:
            out += _parts(p)
        return out
    return [g]


def _tags(t) -> dict:
    return {k: t.get(k) for k in KEEP_TAGS if t.get(k) is not None}


def _match(t, spec) -> bool:
    for k, vals in spec.items():
        v = t.get(k)
        if v is None:
            continue
        if k == "highway" and spec is OSM_AREA_KEYS and t.get("area") != "yes":
            continue
        if vals is None or v in vals:
            return True
    return False


def _osm_way_points(way):
    pts = []
    for node in way.nodes:
        try:
            loc = node.location
            if not loc.valid():
                return []
            pts.append((loc.lon, loc.lat))
        except Exception as exc:
            if type(exc).__name__ == "InvalidLocationError":
                return []
            raise
    return pts


def _clip_osm_way(way_id: int, tags: dict, line, tile) -> list[dict]:
    if not line.intersects(tile):
        return []
    out = []
    for k, part in enumerate(_parts(line.intersection(tile))):
        if part.geom_type == "LineString" and part.length >= 0.5:
            out.append({"osm_way": way_id, "part": k, "tags": tags, "geometry": _round_geom(part.simplify(0.1))})
    return out


def extract_osm(bbox, pbf: Path) -> dict:
    import osmium
    from pyproj import Transformer
    tr = Transformer.from_crs("EPSG:4326", "EPSG:2180", always_xy=True)
    inv = Transformer.from_crs("EPSG:2180", "EPSG:4326", always_xy=True)
    lo = inv.transform(bbox[0] - 50, bbox[1] - 50)
    hi = inv.transform(bbox[2] + 50, bbox[3] + 50)
    ll_box = shapely.box(*lo, *hi)
    tile = shapely.box(*bbox)

    def proj(g):
        return shapely.transform(g, lambda xy: np.column_stack(tr.transform(xy[:, 0], xy[:, 1])))

    keys = sorted(set(OSM_NODE_KEYS) | set(OSM_WAY_KEYS) | set(OSM_AREA_KEYS))
    wkbf = osmium.geom.WKBFactory()
    nodes, ways, areas = [], [], []
    fp = (osmium.FileProcessor(str(pbf)).with_locations()
          .with_areas(osmium.filter.KeyFilter(*OSM_AREA_KEYS.keys()))
          .with_filter(osmium.filter.KeyFilter(*keys)))
    for obj in fp:
        t = obj.tags
        if obj.is_node():
            loc = obj.location
            if not loc.valid() or not (lo[0] <= loc.lon <= hi[0] and lo[1] <= loc.lat <= hi[1]):
                continue
            if not _match(t, OSM_NODE_KEYS):
                continue
            g = proj(shapely.Point(loc.lon, loc.lat))
            if tile.contains(g):
                nodes.append({"osm_node": obj.id, "tags": _tags(t), "geometry": _round_geom(g)})
        elif obj.is_way():
            if not _match(t, OSM_WAY_KEYS):
                continue
            pts = _osm_way_points(obj)
            if len(pts) < 2:
                continue
            line = shapely.LineString(pts)
            if line.intersects(ll_box):
                ways.extend(_clip_osm_way(obj.id, _tags(t), proj(line), tile))
        elif obj.is_area():
            if not _match(t, OSM_AREA_KEYS):
                continue
            try:
                g = wkb.loads(wkbf.create_multipolygon(obj), hex=True)
            except Exception:
                continue
            if not g.intersects(ll_box):
                continue
            g = shapely.make_valid(proj(g)).intersection(tile)
            for k, part in enumerate(_parts(g)):
                if part.geom_type == "Polygon" and part.area >= 4.0:
                    areas.append({"osm_id": obj.orig_id(), "osm_type": "way" if obj.from_way() else "relation",
                                  "part": k, "tags": _tags(t), "geometry": _round_geom(part.simplify(0.1))})
    key = (lambda d: (d.get("osm_type", ""), d.get("osm_id", d.get("osm_way", d.get("osm_node"))), d.get("part", 0)))
    return {"nodes": sorted(nodes, key=key), "ways": sorted(ways, key=key), "areas": sorted(areas, key=key)}


def extract_bdot(bbox, gpkg_zip: Path, gdir: Path) -> dict:
    import pyogrio
    import sys
    sys.path.insert(0, str(REPO / "tools" / "worldgen"))
    from build_region import extract_from_zip
    tile = shapely.box(*bbox)
    out = {}
    for layer, cols in BDOT_LAYERS.items():
        try:
            gp = extract_from_zip(gpkg_zip, f"__{layer}.gpkg", gdir)
        except StopIteration:      # ADR 0204: a powiat without objects of a class ships no file for it (2008: OIKM_L)
            out[layer] = []
            continue
        df = pyogrio.read_dataframe(gp, bbox=bbox)
        df = df.sort_values("LOKALNYID").reset_index(drop=True)
        feats = []
        for r in df.itertuples():
            g = shapely.make_valid(r.geometry).intersection(tile)
            props = {}
            for c in cols:
                v = getattr(r, c, None)
                if v is None or (isinstance(v, float) and math.isnan(v)):
                    continue
                props[c.lower()] = v.item() if hasattr(v, "item") else v
            for k, part in enumerate(_parts(g)):
                if part.geom_type not in ("Point", "LineString", "Polygon"):
                    continue
                if part.geom_type == "Polygon" and part.area < 2.0:
                    continue
                if part.geom_type != "Point":
                    part = part.simplify(0.1)
                feats.append({"id": f"{r.LOKALNYID}:{k}", "props": props, "geometry": _round_geom(part)})
        out[layer] = feats
    return out


def extract(region: dict) -> dict:
    import sys
    sys.path.insert(0, str(REPO / "tools" / "worldgen"))
    from build_region import manifest_files
    from fetch_osm import download
    b = region["bbox"]
    bbox = (b["xmin"], b["ymin"], b["xmax"], b["ymax"])
    t = region["teryt_powiat"]
    z = manifest_files(f"gugik-bdot10k-{t}")[0]
    gdir = REPO / "Data" / "raw" / "gugik" / f"bdot10k-{t}" / "gpkg"
    bdot = extract_bdot(bbox, z, gdir)
    extra = region.get("teryt_powiat_extra") or []
    for tx in extra:                 # ADR 0208: tile across a powiat boundary - every powiat's package, merged by id
        more = extract_bdot(bbox, manifest_files(f"gugik-bdot10k-{tx}")[0],
                            REPO / "Data" / "raw" / "gugik" / f"bdot10k-{tx}" / "gpkg")
        for layer, feats in more.items():
            seen = {f["id"] for f in bdot[layer]}
            bdot[layer] = sorted(bdot[layer] + [f for f in feats if f["id"] not in seen], key=lambda f: f["id"])
        t = ", ".join([t, tx])
    return {"schema": SCHEMA, "crs": "EPSG:2180", "bbox": list(bbox),
            "license": {"osm": "ODbL 1.0, © OpenStreetMap contributors",
                        "bdot10k": "GUGiK BDOT10k (powiat %s), free use, art. 40a ust. 2 pkt 1 Pgik" % t},
            "osm": extract_osm(bbox, download()), "bdot10k": bdot}


def write(region_id: str, data: dict) -> Path:
    p = REPO / "Data" / "Regions" / region_id / "generated" / "streetscape_sources.json"
    p.write_text(json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n",
                 encoding="utf-8", newline="\n")
    return p


def load(region_id: str) -> dict:
    p = REPO / "Data" / "Regions" / region_id / "generated" / "streetscape_sources.json"
    return json.loads(p.read_text(encoding="utf-8"))


def to_shape(g: dict):
    return shapely.geometry.shape(g)


def extract_osm_power_ways_by_bboxes(bboxes: dict[str, tuple[float, float, float, float]], pbf: Path | None = None) -> dict[str, list[dict]]:
    """Extract OSM power=line|minor_line ways clipped to each bbox in a single PBF pass."""
    import sys
    import osmium
    from pyproj import Transformer
    if pbf is None:
        sys.path.insert(0, str(REPO / "tools" / "worldgen"))
        from fetch_osm import download
        pbf = download()
    tr = Transformer.from_crs("EPSG:4326", "EPSG:2180", always_xy=True)
    boxes = {rid: shapely.box(*b) for rid, b in bboxes.items()}
    out = {rid: [] for rid in bboxes}

    class _PowerHandler(osmium.SimpleHandler):
        def way(self, w):
            pw = w.tags.get("power")
            if pw not in ("line", "minor_line"):
                return
            pts = _osm_way_points(w)
            if len(pts) < 2:
                return
            lons, lats = zip(*pts)
            xs, ys = tr.transform(lons, lats)
            ls = shapely.LineString(np.column_stack([xs, ys]))
            tags = _tags(w.tags)
            for rid, tile in boxes.items():
                out[rid].extend(_clip_osm_way(w.id, tags, ls, tile))

    _PowerHandler().apply_file(str(pbf), locations=True)
    key = lambda d: (d["osm_way"], d["part"])
    return {rid: sorted(ws, key=key) for rid, ws in out.items()}


def refresh_power_ways(region: dict, data: dict) -> dict:
    """Merge freshly extracted OSM power=line|minor_line ways into an existing streetscape_sources dict."""
    b = region["bbox"]
    bbox = (b["xmin"], b["ymin"], b["xmax"], b["ymax"])
    rid = region["id"]
    pw = extract_osm_power_ways_by_bboxes({rid: bbox})[rid]
    ways = [w for w in data["osm"]["ways"] if w["tags"].get("power") not in ("line", "minor_line")] + pw
    ways.sort(key=lambda d: (d.get("osm_type", ""), d.get("osm_way", 0), d.get("part", 0)))
    return {**data, "schema": SCHEMA, "osm": {**data["osm"], "ways": ways}}


def main():
    import argparse
    import sys
    sys.path.insert(0, str(REPO / "tools" / "worldgen"))
    from roads import pipeline
    ap = argparse.ArgumentParser(description="Extract or refresh streetscape_sources.json")
    ap.add_argument("--refresh-power", action="store_true", help="Refresh OSM power ways in existing files")
    ap.add_argument("--regions", nargs="*")
    a = ap.parse_args()
    rids = a.regions or sorted(d.name for d in pipeline.REGIONS.iterdir() if (d / "region.yaml").exists())
    if a.refresh_power:
        regs = {rid: pipeline.load_region(rid) for rid in rids
                if (pipeline.REGIONS / rid / "generated" / "streetscape_sources.json").exists()}
        bboxes = {rid: (r["bbox"]["xmin"], r["bbox"]["ymin"], r["bbox"]["xmax"], r["bbox"]["ymax"])
                  for rid, r in regs.items()}
        pw_map = extract_osm_power_ways_by_bboxes(bboxes)
        for rid, r in regs.items():
            data = load(rid)
            ways = [w for w in data["osm"]["ways"] if w["tags"].get("power") not in ("line", "minor_line")] + pw_map[rid]
            ways.sort(key=lambda d: (d.get("osm_type", ""), d.get("osm_way", 0), d.get("part", 0)))
            write(rid, {**data, "schema": SCHEMA, "osm": {**data["osm"], "ways": ways}})


if __name__ == "__main__":
    main()
