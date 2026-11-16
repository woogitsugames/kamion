#!/usr/bin/env python3
"""Statystyki: (1) OSM Overpass (tagi building, levels, roof:shape, wymiary obrysu), (2) buildings.geojson repo (BDOT10k funkcja+kondygnacje, LoD1 2024, LoD2 2017)."""
import json, collections, pathlib, statistics as st
from pyproj import Transformer
from shapely.geometry import Polygon, Point, shape
ROOT = pathlib.Path(__file__).resolve().parent.parent; REPO = ROOT.parents[2]
T = Transformer.from_crs(4326, 2180, always_xy=True)
def q(v, p):
    v = sorted(v); return round(v[min(len(v) - 1, int(p * len(v)))], 1) if v else None
def dims(poly):
    cs = list(poly.minimum_rotated_rectangle.exterior.coords)
    a = Point(cs[0]).distance(Point(cs[1])); b = Point(cs[1]).distance(Point(cs[2])); return max(a, b), min(a, b)
out = {"osm": {}, "repo": {}}
G = {"blok (apartments/residential)": {"apartments", "residential"}, "dom (house/detached/semidetached/terrace/bungalow)": {"house", "detached", "semidetached_house", "terrace", "bungalow"},
     "hala (industrial/warehouse)": {"industrial", "warehouse"}, "biuro/uslugi (office/retail/commercial/supermarket/public/school/hospital/university)": {"office", "retail", "commercial", "supermarket", "public", "school", "hospital", "university"},
     "pomocnicze (outbuilding/garage(s)/shed/garbage_shed/roof/carport/service/kiosk)": {"outbuilding", "garage", "garages", "shed", "garbage_shed", "roof", "carport", "service", "kiosk", "transformer_tower"},
     "yes (bez typu)": {"yes"}}
for area in ("trasa_c", "dojlidy"):
    els = json.load(open(ROOT / "data" / f"overpass_{area}.json"))["elements"]
    o = {"n": len(els), "building": dict(collections.Counter(e["tags"].get("building") for e in els).most_common()),
         "n_levels": sum("building:levels" in e["tags"] for e in els), "n_height": sum("height" in e["tags"] for e in els),
         "n_roof_shape": sum("roof:shape" in e["tags"] for e in els), "n_colour": sum("building:colour" in e["tags"] for e in els), "groups": {}}
    for g, tags in G.items():
        sel = [e for e in els if e["tags"].get("building") in tags and e["type"] == "way" and "geometry" in e]
        L, W, A = [], [], []
        for e in sel:
            p = Polygon([T.transform(x["lon"], x["lat"]) for x in e["geometry"]])
            if p.is_valid and p.area > 1: l, w = dims(p); L.append(l); W.append(w); A.append(p.area)
        lv = collections.Counter(e["tags"]["building:levels"] for e in sel if "building:levels" in e["tags"])
        o["groups"][g] = {"n": len(sel), "levels": dict(sorted(lv.items(), key=lambda kv: float(kv[0]))), "roof_shape": dict(collections.Counter(e["tags"]["roof:shape"] for e in sel if "roof:shape" in e["tags"])),
                          "dl_m_p10_p50_p90": [q(L, .1), q(L, .5), q(L, .9)], "szer_m_p10_p50_p90": [q(W, .1), q(W, .5), q(W, .9)], "pow_m2_p10_p50_p90": [q(A, .1), q(A, .5), q(A, .9)]}
    out["osm"][area] = o
F = {"blok (budynek wielorodzinny)": {"budynek wielorodzinny"}, "dom (budynek jednorodzinny)": {"budynek jednorodzinny"}, "hala (magazyn/produkcyjny)": {"magazyn", "produkcyjny", "industrial"},
     "biuro/uslugi (siedziba firmy, obiekt handlowo-uslugowy, urzad, szkola, szpital...)": None, "gospodarcze/garaz": {"budynek gospodarczy", "garaż"}}
OTHER_EX = {"budynek wielorodzinny", "budynek jednorodzinny", "magazyn", "produkcyjny", "industrial", "budynek gospodarczy", "garaż", "yes", "roof", "garbage_shed", "service", "silos", "stacja transformatorowa",
            "elektrociepłownia", "spalarnia śmieci", "stacja pomp", "szklarnia lub cieplarnia", "allotment_house", "construction", "dom letniskowy", "budynek produkcyjny zwierząt hodowlanych", "stacja paliw"}
for reg in ("bialystok-industrial-c", "bialystok-dojlidy"):
    fs = json.load(open(REPO / "Data/Regions" / reg / "buildings.geojson"))["features"]; o = {"n": len(fs), "groups": {}}
    for g, fn in F.items():
        sel = [f for f in fs if (f["properties"]["function"] in fn if fn else f["properties"]["function"] not in OTHER_EX)]
        H = [f["properties"]["height_lod1_2024_m"] for f in sel if f["properties"].get("height_lod1_2024_m")]
        R = [f["properties"]["height_lod2_2017_m"] for f in sel if f["properties"].get("height_lod2_2017_m")]
        EV = [f["properties"]["lod2_eave_rel_m"] for f in sel if f["properties"].get("lod2_eave_rel_m")]
        L, W, A, HS = [], [], [], []
        for f in sel:
            p = shape(f["geometry"]); l, w = dims(p); L.append(l); W.append(w); A.append(p.area)
            s, h = f["properties"].get("storeys"), f["properties"].get("height_lod1_2024_m")
            if s and h: HS.append(h / s)
        o["groups"][g] = {"n": len(sel), "storeys_bdot": dict(sorted(collections.Counter(str(f["properties"].get("storeys")) for f in sel).items())),
            "roof_type_lod2": dict(collections.Counter(str(f["properties"].get("roof_type_lod2")) for f in sel).most_common()),
            "h_lod1_p10_p50_p90": [q(H, .1), q(H, .5), q(H, .9)], "n_h": len(H), "h_lod2_kalenica_p10_p50_p90": [q(R, .1), q(R, .5), q(R, .9)], "okap_lod2_p10_p50_p90": [q(EV, .1), q(EV, .5), q(EV, .9)],
            "h_lod1_na_kondygnacje_p10_p50_p90": [round(x, 2) if x else None for x in (st.quantiles(HS, n=10)[0], st.median(HS), st.quantiles(HS, n=10)[-1])] if len(HS) > 5 else None,
            "dl_m_p10_p50_p90": [q(L, .1), q(L, .5), q(L, .9)], "szer_m_p10_p50_p90": [q(W, .1), q(W, .5), q(W, .9)], "pow_m2_p10_p50_p90": [q(A, .1), q(A, .5), q(A, .9)]}
    out["repo"][reg] = o
json.dump(out, open(ROOT / "data" / "stats.json", "w"), ensure_ascii=False, indent=1)
for k in out:
    for a, o in out[k].items():
        print("==", k, a, o["n"], {x: o[x] for x in o if x.startswith("n_")})
        for g, v in o["groups"].items(): print("  ", g, json.dumps(v, ensure_ascii=False))
