"""Landmark inventory of a region tile: what OSM says stands there vs what the game builds from buildings.geojson.

  uv run --project tools/worldgen python tools/worldgen/qa/landmark_inventory.py --region knyszyn \
      --out docs/reports/knyszyn-look/inventory_knyszyn.json

Reads the cached Geofabrik extract (Data/raw/osm, ODbL) and Data/Regions/<id>/buildings.geojson (BDOT10k / LoD1 /
LoD2). Every OSM object with a landmark tag (amenity, shop, tourism, historic, man_made, office, leisure, healthcare)
and every OSM building that is not a plain building=yes is joined to the game footprint under it (largest overlap for
areas, containment within 1 m for nodes).

Privacy / brands (CLAUDE.md rule 8, task rule "function only"): the output keeps a WHITELIST of tags. Names of shops
and companies, brands, operators, phone numbers, e-mail addresses and websites are never written; `name` survives only
for public, non-commercial objects (PUBLIC_AMENITY, historic, tourism=attraction|artwork|information).
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import osmium
import shapely
import yaml
from pyproj import Transformer
from shapely import wkb as _wkb
from shapely.geometry import Point, shape

REPO = Path(__file__).resolve().parents[3]
KEYS = ("amenity", "shop", "tourism", "historic", "man_made", "office", "leisure", "healthcare")
KEEP = KEYS + ("building", "building:levels", "roof:shape", "roof:levels", "roof:material", "roof:colour",
               "building:material", "building:colour", "material", "height", "religion", "denomination", "tower:type",
               "start_date", "heritage", "wikidata", "wikimedia_commons", "wikipedia", "shelter_type", "fuel:lpg")
PUBLIC_AMENITY = {"townhall", "place_of_worship", "school", "kindergarten", "fire_station", "library", "police",
                  "hospital", "clinic", "post_office", "community_centre", "marketplace", "fountain"}
NOISE = {("emergency", None), ("amenity", "bench"), ("amenity", "lounger"), ("amenity", "waste_disposal"),
         ("amenity", "post_box"), ("amenity", "parcel_locker"), ("amenity", "clock")}
GAME_KEYS = ("id", "function", "storeys", "height_m", "height_source", "roof_type_lod2", "height_lod2_2017_m",
             "lod2_eave_rel_m", "area_m2", "footprint_source")


def clean(tags):
    t = {k: v for k, v in tags.items() if k in KEEP}
    public = (tags.get("amenity") in PUBLIC_AMENITY or "historic" in tags
              or tags.get("tourism") in ("attraction", "artwork", "information")) and "shop" not in tags \
        and "brand" not in tags
    if public and tags.get("name"):
        t["name"] = tags["name"]
    return t


def inventory(region, pbf):
    reg = yaml.safe_load((REPO / "Data/Regions" / region / "region.yaml").read_text(encoding="utf-8"))
    bb = reg["bbox"]
    to2180 = Transformer.from_crs("EPSG:4326", "EPSG:2180", always_xy=True)
    to4326 = Transformer.from_crs("EPSG:2180", "EPSG:4326", always_xy=True)
    lo0, la0 = to4326.transform(bb["xmin"] - 50, bb["ymin"] - 50)
    lo1, la1 = to4326.transform(bb["xmax"] + 50, bb["ymax"] + 50)
    fab = osmium.geom.WKBFactory()
    pois, blds = [], []

    def inside(x, y):
        return bb["xmin"] <= x <= bb["xmax"] and bb["ymin"] <= y <= bb["ymax"]

    class H(osmium.SimpleHandler):
        def node(self, n):
            if not (lo0 <= n.location.lon <= lo1 and la0 <= n.location.lat <= la1):
                return
            t = dict(n.tags)
            if not any(k in t for k in KEYS):
                return
            x, y = to2180.transform(n.location.lon, n.location.lat)
            if inside(x, y):
                pois.append({"osm": f"node/{n.id}", "xy": [round(x, 1), round(y, 1)], "tags": clean(t)})

        def area(self, a):
            t = dict(a.tags)
            isb = "building" in t
            if not isb and not any(k in t for k in KEYS):
                return
            try:
                g = _wkb.loads(fab.create_multipolygon(a), hex=True)
            except Exception:       # broken multipolygon in the extract
                return
            g = shapely.transform(g, lambda c: np.column_stack(to2180.transform(c[:, 0], c[:, 1])))
            c = g.centroid
            if not inside(c.x, c.y):
                return
            rec = {"osm": f"{'way' if a.from_way() else 'relation'}/{a.orig_id()}",
                   "xy": [round(c.x, 1), round(c.y, 1)], "area_m2": round(g.area, 1), "tags": clean(t), "_geom": g}
            if isb:
                if t["building"] != "yes" or any(k in t for k in KEYS + ("building:levels", "roof:shape", "material")):
                    blds.append(rec)
            else:
                pois.append(rec)

    H().apply_file(str(pbf), locations=True)
    fc = json.loads((REPO / "Data/Regions" / region / "buildings.geojson").read_text(encoding="utf-8"))
    foot = [(shape(f["geometry"]), f["properties"]) for f in fc["features"]]
    tree = shapely.STRtree([g for g, _ in foot])

    def join(g):
        best, score = None, 0.0
        for i in tree.query(g.buffer(1.0)):
            fg = foot[i][0]
            s = (1.0 if fg.buffer(1.0).contains(g) else 0.0) if g.geom_type == "Point" else fg.intersection(g).area
            if s > score:
                best, score = i, s
        return None if best is None else {k: foot[best][1].get(k) for k in GAME_KEYS}

    out = []
    for r in pois + blds:
        t = r["tags"]
        if any((k, None) in NOISE or (k, t.get(k)) in NOISE for k in t) or (set(t) & set(KEYS)) == set() and \
                t.get("building") in ("outbuilding", "house", "garage", "construction"):
            continue
        g = r.pop("_geom", None)
        r["game"] = join(g if g is not None else Point(r["xy"]))
        out.append(r)
    out.sort(key=lambda r: r["osm"])
    funcs = {}
    for _, p in foot:
        funcs[str(p.get("function"))] = funcs.get(str(p.get("function")), 0) + 1
    multi = [{k: p.get(k) for k in GAME_KEYS} | {"xy": [round(g.centroid.x, 1), round(g.centroid.y, 1)]}
             for g, p in foot if p.get("function") in ("budynek wielorodzinny", "dom pogrzebowy", "stacja paliw",
                                                       "kościół", "szkoła podstawowa", "dom towarowy lub handlowy")]
    return {"region": region, "source_osm": pbf.name, "license": "OSM: ODbL 1.0 (c) OpenStreetMap contributors; "
            "footprints: GUGiK BDOT10k / LoD1 (see region.yaml)", "objects": out,
            "game_functions": dict(sorted(funcs.items(), key=lambda kv: -kv[1])), "game_key_buildings": multi}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--region", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--pbf", default=None)
    a = ap.parse_args()
    pbf = Path(a.pbf) if a.pbf else sorted((REPO / "Data/raw/osm").glob("*.osm.pbf"))[-1]
    res = inventory(a.region, pbf)
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(res, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(a.region, len(res["objects"]), "objects ->", out)


if __name__ == "__main__":
    main()
