#!/usr/bin/env python3
"""Analiza zbiorcza wynikow Overpass (files/overpass_raw/*.json) przycietych do bboxu R9 w EPSG:2180.
Dlugosc = suma odcinkow, ktorych srodek lezy w bboxie (EPSG:2180, metry plaskie). Pokrycie tagow = % dlugosci (drogi) / % liczby (obiekty).
Wyniki: overpass/summary_*.json (zbiorcze, do gita)."""
import json, pathlib, math, collections, sys
from pyproj import Transformer
root = pathlib.Path(__file__).resolve().parents[1]; raw = root / "files/overpass_raw"; out = root / "overpass"
X0, Y0, X1, Y1 = 764683, 584959, 787211, 605439
t = Transformer.from_crs(4326, 2180, always_xy=True)
log = {json.loads(l)["name"]: json.loads(l) for l in open(out / "_log.jsonl")}
def meta(name): r = log[name]; return {k: r[k] for k in ("utc", "endpoint", "timestamp_osm_base", "elements", "bytes", "sha256")}
def inb(x, y): return X0 <= x <= X1 and Y0 <= y <= Y1
def clipped_len(geom):
    pts = [t.transform(p["lon"], p["lat"]) for p in geom]; s = 0.0
    for (xa, ya), (xb, yb) in zip(pts, pts[1:]):
        if inb((xa + xb) / 2, (ya + yb) / 2): s += math.hypot(xb - xa, yb - ya)
    return s, pts
def center_in(e):
    if "center" in e: lo, la = e["center"]["lon"], e["center"]["lat"]
    elif "lat" in e: lo, la = e["lon"], e["lat"]
    else: return False
    return inb(*t.transform(lo, la))
TAGS = {"lanes": lambda g: "lanes" in g, "maxspeed": lambda g: "maxspeed" in g, "surface": lambda g: "surface" in g, "width": lambda g: "width" in g or "est_width" in g,
        "turn:lanes*": lambda g: any(k.startswith("turn:lanes") for k in g), "destination*": lambda g: any(k.startswith("destination") for k in g),
        "lit": lambda g: "lit" in g, "oneway": lambda g: "oneway" in g, "layer": lambda g: "layer" in g, "bridge": lambda g: g.get("bridge", "no") != "no",
        "tunnel": lambda g: g.get("tunnel", "no") != "no", "name": lambda g: "name" in g, "ref": lambda g: "ref" in g, "sidewalk*": lambda g: any(k.startswith("sidewalk") for k in g),
        "cycleway*": lambda g: any(k.startswith("cycleway") for k in g), "maxweight|hgv|maxheight": lambda g: any(k in g for k in ("maxweight", "hgv", "maxheight", "maxaxleload")),
        "shoulder*": lambda g: any(k.startswith("shoulder") for k in g), "lane_markings": lambda g: "lane_markings" in g, "smoothness": lambda g: "smoothness" in g}
def highways(src="highways"):
    d = json.load(open(raw / f"{src}.json"))
    L = collections.defaultdict(float); N = collections.Counter(); T = collections.defaultdict(lambda: collections.defaultdict(float))
    refs = collections.defaultdict(float); vals = {k: collections.defaultdict(lambda: collections.defaultdict(float)) for k in ("lanes", "maxspeed", "surface", "lit", "width")}
    for e in d["elements"]:
        g = e["tags"]; s, _ = clipped_len(e["geometry"])
        if s <= 0: continue
        c = g["highway"]
        if c in ("construction", "proposed"): c = f"{c}:{g.get(c, '?')}"
        L[c] += s; N[c] += 1
        for k, fn in TAGS.items():
            if fn(g): T[c][k] += s
        for k in vals:
            if k in g: vals[k][c][g[k]] += s
        if g["highway"] in ("motorway", "trunk", "primary", "secondary", "motorway_link", "trunk_link") and g.get("ref"): refs[(g["highway"], g["ref"])] += s
    res = {"zapytanie": meta(src), "zakres_klas": "wszystkie" if src == "highways" else "tylko motorway/trunk/primary(+link), construction, proposed (zapytanie major_wide; pelne zapytanie highways przerwane - limit sesji)", "bbox_epsg2180": [X0, Y0, X1, Y1], "klasy": {}}
    for c in sorted(L, key=lambda c: -L[c]):
        res["klasy"][c] = {"liczba_way": N[c], "dlugosc_km": round(L[c] / 1000, 2), "pokrycie_tagow_proc_dlugosci": {k: round(100 * T[c][k] / L[c], 1) for k in TAGS},
                           "wartosci_km": {k: {v: round(x / 1000, 2) for v, x in sorted(vals[k][c].items(), key=lambda q: -q[1])[:8]} for k in vals}}
    res["dlugosc_wg_ref_km"] = {f"{h}|{r}": round(v / 1000, 2) for (h, r), v in sorted(refs.items(), key=lambda q: -q[1])}
    json.dump(res, open(out / "summary_highways.json", "w"), ensure_ascii=False, indent=1)
    drv = ["motorway", "motorway_link", "trunk", "trunk_link", "primary", "primary_link", "secondary", "secondary_link", "tertiary", "tertiary_link", "unclassified", "residential", "living_street", "service"]
    print("class km n " + " ".join(TAGS))
    for c in drv:
        if c in res["klasy"]:
            k = res["klasy"][c]; print(c, k["dlugosc_km"], k["liczba_way"], " ".join(str(k["pokrycie_tagow_proc_dlugosci"][x]) for x in TAGS))
    print({c: res["klasy"][c]["dlugosc_km"] for c in res["klasy"] if c not in drv})
def buildings():
    d = json.load(open(raw / "buildings.json")); n = 0; c = collections.Counter(); typ = collections.Counter()
    for e in d["elements"]:
        if not center_in(e): continue
        g = e.get("tags", {})
        if e["type"] == "relation" and g.get("type") != "multipolygon": continue
        n += 1; typ[g.get("building")] += 1
        lv = "building:levels" in g; h = "height" in g or "building:height" in g
        c["building:levels"] += lv; c["height"] += h; c["levels_or_height"] += (lv or h); c["roof:shape"] += "roof:shape" in g; c["building:material|colour"] += any(k in g for k in ("building:material", "building:colour"))
        c["addr:housenumber"] += "addr:housenumber" in g; c["start_date"] += "start_date" in g; c["typ!=yes"] += g.get("building") != "yes"
    res = {"zapytanie": meta("buildings"), "liczba_budynkow_w_bbox": n, "pokrycie_proc": {k: round(100 * v / n, 1) for k, v in c.items()}, "liczby": dict(c), "typy_top20": dict(typ.most_common(20))}
    json.dump(res, open(out / "summary_buildings.json", "w"), ensure_ascii=False, indent=1); print(res)
if __name__ == "__main__":
    for a in sys.argv[1:]:
        if a == "highways_major": highways("major_wide")
        else: globals()[a]()
