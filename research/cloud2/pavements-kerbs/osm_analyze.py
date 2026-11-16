#!/usr/bin/env python3
"""Analiza surowych kafli OSM (files/osm/*.osm): ulice trasy C i Dojlid, tagi nawierzchni,
wezly kerb=*, manhole=*, tactile_paving. Wynik: osm_summary.json (do gita, maly)."""
import xml.etree.ElementTree as ET, pathlib, json, math, collections, sys
D = pathlib.Path(__file__).parent
nodes, ways = {}, {}
for f in sorted((D / "files" / "osm").glob("*.osm")):
    for ev, el in ET.iterparse(str(f)):
        if el.tag == "node":
            nodes[el.get("id")] = (float(el.get("lat")), float(el.get("lon")), {t.get("k"): t.get("v") for t in el.findall("tag")})
            el.clear()
        elif el.tag == "way":
            ways[el.get("id")] = ([n.get("ref") for n in el.findall("nd")], {t.get("k"): t.get("v") for t in el.findall("tag")})
            el.clear()
ROUTE = {"C": ["Generała Władysława Andersa", "Aleja Tysiąclecia Państwa Polskiego", "Sokólska", "Generała Stanisława Maczka",
               "Władysława Wysockiego", "Kombatantów", "Rondo Krzysztofa Jakuba Putry Wicemarszałka Sejmu RP"],
         "D": ["Jacka Kuronia", "Adama Mickiewicza", "Dywizjonu 303"]}
def dist(a, b):
    k = 111320.0
    return math.hypot((a[0] - b[0]) * k, (a[1] - b[1]) * k * math.cos(math.radians(a[0])))
def wlen(nd):
    pts = [nodes[n][:2] for n in nd if n in nodes]
    return sum(dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1)), pts
names = collections.Counter(t.get("name") for nd, t in ways.values() if t.get("highway") and t.get("name"))
if "--names" in sys.argv:
    for n, c in sorted(names.items()):
        if any(s in n for s in ("Anders", "Tysi", "Putr", "Sokól", "Wysock", "Kombat", "Maczk", "Kuroni", "Mickiew", "Dywizjon")):
            print(n, c)
    sys.exit()
out = {"streets": {}, "generated_from": "OSM API 0.6 /map, 2026-11-14 ~17:08-17:09 UTC"}
route_pts = {}
for reg, lst in ROUTE.items():
    for name in lst:
        ws = [(i, nd, t) for i, (nd, t) in ways.items() if t.get("name") == name and t.get("highway") in
              ("trunk", "primary", "secondary", "tertiary", "residential", "unclassified", "trunk_link", "primary_link", "secondary_link", "tertiary_link")]
        if not ws:
            continue
        tot = 0; surf = collections.Counter(); hw = collections.Counter(); lanes = collections.Counter(); pts_all = []
        for i, nd, t in ws:
            l, pts = wlen(nd); tot += l; surf[t.get("surface", "brak tagu")] += round(l); hw[t["highway"]] += round(l)
            lanes[t.get("lanes", "brak tagu")] += round(l); pts_all += [(p, i) for p in pts]
        route_pts[name] = pts_all
        out["streets"][name] = {"region": reg, "ways": len(ws), "way_ids": [i for i, _, _ in ws][:60], "length_m": round(tot),
                                "surface_m": dict(surf), "highway_m": dict(hw), "lanes_m": dict(lanes),
                                "bbox": [min(p[0][0] for p in pts_all), min(p[0][1] for p in pts_all), max(p[0][0] for p in pts_all), max(p[0][1] for p in pts_all)]}
def near(p, r=30):
    best = None
    for name, pts in route_pts.items():
        for q, wid in pts:
            if abs(q[0] - p[0]) < 0.0006 and abs(q[1] - p[1]) < 0.001:
                d = dist(p, q)
                if d < r and (best is None or d < best[0]):
                    best = (d, name, wid)
    return best
# wezly punktowe
pt = collections.defaultdict(lambda: collections.Counter()); manholes = []
for i, (la, lo, t) in nodes.items():
    for k in ("kerb", "manhole", "tactile_paving"):
        if k in t:
            b = near((la, lo))
            if b:
                pt[b[1]][f"{k}={t[k]}"] += 1
                if k == "manhole":
                    manholes.append({"node": i, "lat": la, "lon": lo, "street": b[1], "d_m": round(b[0], 1), "tags": t})
    if t.get("man_made") == "manhole":
        b = near((la, lo))
        if b: manholes.append({"node": i, "lat": la, "lon": lo, "street": b[1], "d_m": round(b[0], 1), "tags": t})
out["point_tags_within_30m"] = {k: dict(v) for k, v in pt.items()}
out["manholes_within_30m"] = manholes
# ciagi piesze/rowerowe w poblizu (srodek odcinka <= 30 m od osi ulicy)
side = collections.defaultdict(lambda: collections.Counter())
for i, (nd, t) in ways.items():
    if t.get("highway") in ("footway", "cycleway", "path"):
        l, pts = wlen(nd)
        if not pts: continue
        b = near(pts[len(pts) // 2])
        if b:
            key = "%s|surface=%s|colour=%s|segregated=%s|footway=%s" % (t["highway"], t.get("surface", "-"), t.get("surface:colour", t.get("colour", "-")), t.get("segregated", "-"), t.get("footway", "-"))
            side[b[1]][key] += round(l)
out["side_ways_m_within_30m"] = {k: dict(sorted(v.items(), key=lambda x: -x[1])) for k, v in side.items()}
(D / "osm_summary.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))
for n, s in out["streets"].items():
    print(n, s["region"], s["ways"], s["length_m"], s["surface_m"], s["bbox"])
print(json.dumps(out["point_tags_within_30m"], ensure_ascii=False))
print(len(manholes))
for k, v in out["side_ways_m_within_30m"].items():
    print(k, list(v.items())[:8])
