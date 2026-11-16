"""D29: truck targets per lattice cell (ADR 0203) along two Podlasie corridors, OSM API 0.6 map calls.
Usage: python corridor_targets.py <plan.json> <rawdir> <out.json>. Names of objects are never stored."""
import json, sys, time, math, urllib.request, urllib.error
from collections import defaultdict
from pathlib import Path
from pyproj import Transformer
from shapely.geometry import box, Point, Polygon, LineString

X0, Y0, T = 776971.0, 595199.0, 2048.0
API = "https://api.openstreetmap.org/api/0.6"
UA = {"User-Agent": "osm-research-client/1.0"}
CAT_SHOP = ("supermarket", "mall", "doityourself", "wholesale", "department_store", "trade")
MAJOR = ("motorway", "trunk", "primary", "secondary", "tertiary")
to2180 = Transformer.from_crs("EPSG:4326", "EPSG:2180", always_xy=True)
to4326 = Transformer.from_crs("EPSG:2180", "EPSG:4326", always_xy=True)

def cats(t, area):
    out = []
    b = t.get("building")
    if b in ("industrial", "warehouse", "manufacture") and area is not None and area >= 1000: out.append("hall_1000m2")
    if b == "warehouse" or t.get("industrial") in ("warehouse", "logistics"): out.append("warehouse")
    if t.get("man_made") == "works": out.append("works")
    if t.get("amenity") == "fuel":
        out.append("fuel")
        if t.get("fuel:HGV_diesel") == "yes" or t.get("hgv") in ("yes", "designated"): out.append("fuel_hgv")
    if t.get("amenity") == "parking" and (t.get("hgv") in ("yes", "designated") or t.get("parking") == "truck"): out.append("truck_parking")
    if t.get("highway") in ("services", "rest_area"): out.append("services")
    if t.get("shop") in CAT_SHOP: out.append("retail_delivery")
    # D29 extra (agri/industry gameplay)
    if t.get("man_made") == "silo" or b in ("silo", "grain_silo"): out.append("silo")
    if t.get("industrial") == "dairy" or t.get("product") in ("milk", "dairy") or t.get("craft") == "dairy": out.append("dairy")
    if t.get("craft") == "sawmill" or t.get("industrial") == "sawmill": out.append("sawmill")
    if t.get("landuse") == "quarry": out.append("quarry")
    if b in ("farm_auxiliary", "barn", "cowshed") and area is not None and area >= 1000: out.append("farm_hall_1000m2")
    if t.get("shop") == "agrarian": out.append("agri_shop")
    return out

def fetch(bb4326, path):
    if path.exists(): return json.loads(path.read_text())
    url = f"{API}/map.json?bbox={bb4326[0]:.6f},{bb4326[1]:.6f},{bb4326[2]:.6f},{bb4326[3]:.6f}"
    for k in range(4):
        try:
            r = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=180)
            d = json.load(r); path.write_text(json.dumps(d)); time.sleep(1.5); return d
        except urllib.error.HTTPError as e:
            if e.code == 400: return None  # too many nodes
            time.sleep(2 ** (k + 1))
        except Exception:
            time.sleep(2 ** (k + 1))
    raise RuntimeError(url)

def cell_elements(i, j, raw):
    bb = (X0 + T * i, Y0 + T * j, X0 + T * (i + 1), Y0 + T * (j + 1))
    def ll(b):
        xs = [to4326.transform(x, y) for x in (b[0], b[2]) for y in (b[1], b[3])]
        return (min(p[0] for p in xs), min(p[1] for p in xs), max(p[0] for p in xs), max(p[1] for p in xs))
    d = fetch(ll(bb), raw / f"c_{i}_{j}.json")
    if d is not None: return bb, d["elements"]
    els = {}
    mx, my = (bb[0] + bb[2]) / 2, (bb[1] + bb[3]) / 2
    for q, sb in enumerate([(bb[0], bb[1], mx, my), (mx, bb[1], bb[2], my), (bb[0], my, mx, bb[3]), (mx, my, bb[2], bb[3])]):
        dq = fetch(ll(sb), raw / f"c_{i}_{j}_q{q}.json")
        if dq is None: raise RuntimeError("quadrant too big")
        for e in dq["elements"]: els[(e["type"], e["id"])] = e
    return bb, list(els.values())

def count(bb, elements):
    nodes = {e["id"]: e for e in elements if e["type"] == "node"}
    tb = box(*bb); c = defaultdict(float); places = set()
    xy = lambda n: to2180.transform(n["lon"], n["lat"])
    for n in nodes.values():
        t = n.get("tags")
        if not t: continue
        p = Point(*xy(n))
        if not tb.contains(p): continue
        if t.get("place") in ("city", "town", "village") and t.get("name"): places.add(f"{t['name']} ({t['place']})")
        for k in cats(t, None): c[k] += 1
    for w in (e for e in elements if e["type"] == "way"):
        t = w.get("tags") or {}
        pts = [xy(nodes[k]) for k in w["nodes"] if k in nodes]
        if len(pts) < 2: continue
        hw = (t.get("highway") or "").replace("_link", "")
        if hw in MAJOR:
            c[f"km_{hw}"] += LineString(pts).intersection(tb).length / 1000
        if w["nodes"][0] != w["nodes"][-1] or len(pts) < 4: continue
        pg = Polygon(pts)
        if not pg.is_valid: pg = pg.buffer(0)
        lu = t.get("landuse")
        if lu in ("industrial", "commercial", "farmyard", "quarry"): c[f"{lu}_ha"] += pg.intersection(tb).area / 1e4
        if not tb.contains(pg.representative_point()): continue
        if t.get("building"): c["buildings"] += 1
        for k in cats(t, pg.area): c[k] += 1
    return {k: (round(v, 2) if (k.startswith("km_") or k.endswith("_ha")) else int(v)) for k, v in sorted(c.items())}, sorted(places)

def main():
    plan, raw, out = json.loads(Path(sys.argv[1]).read_text()), Path(sys.argv[2]), Path(sys.argv[3])
    raw.mkdir(parents=True, exist_ok=True)
    P = plan["podlasie"]
    corr = {"monki_grajewo_dk65": P["monki_grajewo_dk65"]["cells"],
            "loop_s8_dw671": P["s8_bialystok_to_tykocin_junction"]["cells"] + P["tykocin_to_s8_dw671"]["cells"]}
    res = {"source": "OSM API 0.6 map.json per lattice cell, 2026-11-16, ODbL 1.0 (c) OpenStreetMap contributors",
           "lattice": "ADR 0203 x=776971+2048i, y=595199+2048j (EPSG:2180)", "corridors": {}}
    for name, cells in corr.items():
        tot = defaultdict(float); per = []; allpl = set()
        for cell in cells:
            i, j = cell["ij"]
            bb, els = cell_elements(i, j, raw)
            c, pl = count(bb, els)
            per.append({"ij": [i, j], "route_m": cell["length_m"], "kinds": cell["kinds"], "counts": c, "places": pl})
            allpl |= set(pl)
            for k, v in c.items(): tot[k] += v
            print(name, i, j, c.get("buildings", 0), flush=True)
        res["corridors"][name] = {"tiles": len(cells), "route_km": round(sum(c["length_m"] for c in cells) / 1000, 1),
                                  "totals": {k: round(v, 2) for k, v in sorted(tot.items())},
                                  "places": sorted(allpl), "cells": per}
    out.write_text(json.dumps(res, indent=1, ensure_ascii=False, sort_keys=True) + "\n")

if __name__ == "__main__":
    main()
