#!/usr/bin/env python3
"""Pobiera pelne listy zdjec sekwencji KartaView (2.0/sequence/{id}/photos) i przypisuje do osi ulic.
Wynik: files/kv_seq.json (lista zdjec <=30 m od osi ulic trasy)."""
import json, math, pathlib, sys, time, urllib.request
sys.path.insert(0, str(pathlib.Path(__file__).parent))
D = pathlib.Path(__file__).parent
SEQS = ["3686129", "2769366", "1155711", "2763230", "14055", "10733", "25209"]
import xml.etree.ElementTree as ET
STREETS = ["Generała Władysława Andersa", "Aleja Tysiąclecia Państwa Polskiego", "Sokólska", "Generała Stanisława Maczka",
           "Władysława Wysockiego", "Kombatantów", "Rondo Krzysztofa Jakuba Putry Wicemarszałka Sejmu RP",
           "Jacka Kuronia", "Adama Mickiewicza", "Dywizjonu 303"]
HW = ("trunk", "primary", "secondary", "tertiary", "residential", "unclassified")
nodes, axis = {}, []
for f in sorted((D / "files" / "osm").glob("*.osm")):
    for ev, el in ET.iterparse(str(f)):
        if el.tag == "node":
            nodes[el.get("id")] = (float(el.get("lat")), float(el.get("lon"))); el.clear()
        elif el.tag == "way":
            t = {x.get("k"): x.get("v") for x in el.findall("tag")}
            if t.get("name") in STREETS and t.get("highway") in HW:
                for n in el.findall("nd"):
                    if n.get("ref") in nodes: axis.append(nodes[n.get("ref")] + (t["name"], el.get("id")))
            el.clear()
def dist(a, b):
    return math.hypot((a[0] - b[0]) * 111320, (a[1] - b[1]) * 111320 * math.cos(math.radians(a[0])))
out = []
for s in SEQS:
    page = 1
    while True:
        u = f"https://api.kartaview.org/2.0/sequence/{s}/photos?itemsPerPage=500&page={page}"
        try:
            j = json.loads(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "research-client/1.0"}), timeout=90).read())
        except Exception as ex:
            print("ERR", u, ex); break
        data = (j.get("result") or {}).get("data") or []
        for p in data:
            la, lo = float(p["lat"]), float(p["lng"])
            if not (53.08 < la < 53.17 and 23.12 < lo < 23.26): continue
            b = min(axis, key=lambda q: dist((la, lo), q)); d = dist((la, lo), b)
            if d <= 45:
                out.append({"src": "kartaview", "id": p["id"], "lat": la, "lon": lo, "datetime": p.get("shotDate"), "azimuth": p.get("heading"),
                            "seq": s, "seq_index": p.get("sequenceIndex"), "file": p.get("fileurlProc"), "fileLTh": p.get("fileurlLTh"),
                            "d_node_m": round(d, 1), "street": b[2], "way": b[3]})
        print(s, page, len(data), len(out))
        if len(data) < 500: break
        page += 1; time.sleep(0.5)
(D / "files" / "kv_seq.json").write_text(json.dumps(out, ensure_ascii=False))
import collections
print(collections.Counter((o["seq"], o["street"][:16]) for o in out))
