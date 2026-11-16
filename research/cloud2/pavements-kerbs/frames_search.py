#!/usr/bin/env python3
"""Szuka kadrow Panoramax (api.panoramax.xyz, STAC /api/search) i KartaView (api.kartaview.org 2.0)
wzdluz osi ulic trasy C i Dojlid (punkty z files/osm). Wynik: files/candidates.json."""
import json, math, pathlib, sys, time, urllib.request, urllib.parse, xml.etree.ElementTree as ET
D = pathlib.Path(__file__).parent
STREETS = {"Generała Władysława Andersa": "C", "Aleja Tysiąclecia Państwa Polskiego": "C", "Sokólska": "C",
           "Generała Stanisława Maczka": "C", "Władysława Wysockiego": "C", "Kombatantów": "C",
           "Rondo Krzysztofa Jakuba Putry Wicemarszałka Sejmu RP": "C",
           "Jacka Kuronia": "D", "Adama Mickiewicza": "D", "Dywizjonu 303": "D"}
HW = ("trunk", "primary", "secondary", "tertiary", "residential", "unclassified")
nodes, ways = {}, {}
for f in sorted((D / "files" / "osm").glob("*.osm")):
    for ev, el in ET.iterparse(str(f)):
        if el.tag == "node":
            nodes[el.get("id")] = (float(el.get("lat")), float(el.get("lon"))); el.clear()
        elif el.tag == "way":
            t = {x.get("k"): x.get("v") for x in el.findall("tag")}
            if t.get("name") in STREETS and t.get("highway") in HW:
                ways[el.get("id")] = ([n.get("ref") for n in el.findall("nd")], t)
            el.clear()
def dist(a, b):
    return math.hypot((a[0] - b[0]) * 111320, (a[1] - b[1]) * 111320 * math.cos(math.radians(a[0])))
axis = []  # (lat, lon, street, way)
for wid, (nd, t) in ways.items():
    for n in nd:
        if n in nodes: axis.append((nodes[n][0], nodes[n][1], t["name"], wid))
# punkty probkowania co ~120 m
samples = []
for p in axis:
    if all(dist(p, q) > 120 for q in samples): samples.append(p)
print("axis nodes", len(axis), "samples", len(samples))
def get(url):
    for a in range(4):
        try:
            return json.loads(urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "research-client/1.0"}), timeout=60).read())
        except Exception as ex:
            print("ERR", url[:90], ex, file=sys.stderr); time.sleep(2 * (a + 1))
    return None
def nearest(lat, lon):
    b = min(axis, key=lambda q: dist((lat, lon), q)); return round(dist((lat, lon), b), 1), b[2], b[3]
cand = {}
for i, (la, lo, st, wid) in enumerate(samples):
    dla, dlo = 60 / 111320, 60 / (111320 * math.cos(math.radians(la)))
    j = get("https://api.panoramax.xyz/api/search?limit=40&bbox=%.6f,%.6f,%.6f,%.6f" % (lo - dlo, la - dla, lo + dlo, la + dla))
    for f in (j or {}).get("features", []):
        pr = f["properties"]; g = f["geometry"]["coordinates"]
        d, s2, w2 = nearest(g[1], g[0])
        cand["pmx:" + f["id"]] = {"src": "panoramax", "id": f["id"], "lat": g[1], "lon": g[0], "datetime": pr.get("datetime"),
            "azimuth": pr.get("view:azimuth"), "fov": pr.get("pers:interior_orientation", {}).get("field_of_view"),
            "license": pr.get("license"), "producer": [p.get("name") for p in f.get("providers", [])],
            "sd": f["assets"].get("sd", {}).get("href"), "hd": f["assets"].get("hd", {}).get("href"),
            "self": next((l["href"] for l in f["links"] if l["rel"] == "self"), None), "collection": f.get("collection"),
            "d_axis_m": d, "street": s2, "way": w2}
    k = get("https://api.kartaview.org/2.0/photo/?lat=%.6f&lng=%.6f&radius=50&itemsPerPage=40" % (la, lo))
    for p in ((k or {}).get("result") or {}).get("data") or []:
        d, s2, w2 = nearest(float(p["lat"]), float(p["lng"]))
        cand["kv:" + p["id"]] = {"src": "kartaview", "id": p["id"], "lat": float(p["lat"]), "lon": float(p["lng"]),
            "datetime": p.get("shotDate") or p.get("dateAdded"), "azimuth": p.get("heading"), "seq": p.get("sequenceId"),
            "seq_index": p.get("sequenceIndex"), "user": p.get("username"), "file": p.get("fileurlProc") or p.get("fileurl"),
            "fileLTh": p.get("fileurlLTh"), "d_axis_m": d, "street": s2, "way": w2}
    if i % 20 == 0:
        print(i, len(cand)); (D / "files" / "candidates.json").write_text(json.dumps(cand, ensure_ascii=False))
    time.sleep(0.2)
(D / "files" / "candidates.json").write_text(json.dumps(cand, ensure_ascii=False, indent=0))
import collections
print(collections.Counter((c["src"], c["street"]) for c in cand.values()))
