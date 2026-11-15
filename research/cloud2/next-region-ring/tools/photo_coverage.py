#!/usr/bin/env python3
"""Pokrycie korytarzy zdjeciami: komorki 600 m (EPSG:2180) przecinane przez os drog motorway/trunk/primary(+link) w bboxie R9, grupowane wg ref.
Panoramax: komorka pokryta, gdy >=1 zdjecie w promieniu 500 m od srodka komorki. KartaView: gdy zapytanie /photo (r=500 m) zwrocilo n>=1.
Wynik: panoramax/corridor_coverage.json"""
import json, pathlib, math, collections, re
from pyproj import Transformer
root = pathlib.Path(__file__).resolve().parents[1]
X0, Y0, X1, Y1 = 764683, 584959, 787211, 605439; C = 600
t = Transformer.from_crs(4326, 2180, always_xy=True); ti = Transformer.from_crs(2180, 4326, always_xy=True)
d = json.load(open(root / "files/overpass_raw/major_wide.json"))
cells = collections.defaultdict(set)
for e in d["elements"]:
    g = e["tags"]
    if g["highway"] not in ("motorway", "motorway_link", "trunk", "trunk_link", "primary", "primary_link"): continue
    key = ("S" if g["highway"].startswith("motorway") else "") and g.get("ref") or g.get("ref") or f"({g['highway']} bez ref)"
    pts = [t.transform(p["lon"], p["lat"]) for p in e["geometry"]]
    for (xa, ya), (xb, yb) in zip(pts, pts[1:]):
        n = max(1, int(math.hypot(xb - xa, yb - ya) / 100))
        for k in range(n + 1):
            x, y = xa + (xb - xa) * k / n, ya + (yb - ya) * k / n
            if X0 <= x <= X1 and Y0 <= y <= Y1: cells[(int((x - X0) // C), int((y - Y0) // C))].add(key)
px = [json.loads(l) for l in open(root / "files/panoramax_raw/items.jsonl")]
pxy = [(t.transform(p["lon"], p["lat"]), p["datetime"][:4]) for p in px]
kv = {}
for q in json.load(open(root / "kartaview/search_log.json"))["zapytania"]:
    m = re.search(r"lat=([\d.]+)&lng=([\d.]+)", q["url"]); x, y = t.transform(float(m.group(2)), float(m.group(1)))
    kv[(int((x - X0) // C), int((y - Y0) // C))] = max(kv.get((int((x - X0) // C), int((y - Y0) // C)), 0), q["n"] or 0)
res = collections.defaultdict(lambda: {"komorek": 0, "panoramax": 0, "panoramax_od_2024": 0, "kartaview": 0, "ktorekolwiek": 0})
allc = {"komorek": 0, "panoramax": 0, "panoramax_od_2024": 0, "kartaview": 0, "ktorekolwiek": 0}
for (i, j), refs in cells.items():
    cx, cy = X0 + (i + .5) * C, Y0 + (j + .5) * C
    near = [yr for (x, y), yr in pxy if math.hypot(x - cx, y - cy) <= 500]
    p = bool(near); p24 = any(yr >= "2024" for yr in near); k = kv.get((i, j), 0) > 0
    for tgt in [res[r] for r in refs] + [allc]:
        tgt["komorek"] += 1; tgt["panoramax"] += p; tgt["panoramax_od_2024"] += p24; tgt["kartaview"] += k; tgt["ktorekolwiek"] += (p or k)
def pc(v): return {**v, **{f"{k}_proc": round(100 * v[k] / v["komorek"], 1) for k in ("panoramax", "panoramax_od_2024", "kartaview", "ktorekolwiek")}}
out = {"metoda": __doc__, "komorka_m": C, "razem": pc(allc), "wg_ref": {r: pc(v) for r, v in sorted(res.items(), key=lambda q: -q[1]["komorek"])}}
json.dump(out, open(root / "panoramax/corridor_coverage.json", "w"), ensure_ascii=False, indent=1)
print(out["razem"])
for r, v in out["wg_ref"].items(): print(r, v["komorek"], v["panoramax_proc"], v["panoramax_od_2024_proc"], v["kartaview_proc"], v["ktorekolwiek_proc"])
