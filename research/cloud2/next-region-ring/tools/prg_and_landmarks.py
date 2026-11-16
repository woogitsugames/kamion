#!/usr/bin/env python3
"""(1) PRG gminy (files/gugik_raw/prg_gminy.xml, WFS 1.1.0, osie N,E) -> gugik/prg_gminy.json: udzial w bboxie R9 (raster 128 m, punkt w wielokacie).
(2) Dla kazdego landmarku: centroid geometrii OSM (pierwszy way/node z listy), powiat/gmina (PRG), najlepsze ORTO RGB / NMT 1 m / NMPT w punkcie (skorowidze),
    Panoramax i KartaView w promieniu 300 m (liczba, lata). -> panoramax/landmarks.json"""
import re, json, csv, pathlib, math, collections
from pyproj import Transformer
root = pathlib.Path(__file__).resolve().parents[1]
X0, Y0, X1, Y1 = 764683, 584959, 787211, 605439
t = Transformer.from_crs(4326, 2180, always_xy=True); ti = Transformer.from_crs(2180, 4326, always_xy=True)
x = open(root / "files/gugik_raw/prg_gminy.xml", encoding="utf-8", errors="replace").read()
gm = []
for f in re.findall(r"<gml:featureMember>(.*?)</gml:featureMember>", x, flags=re.S):
    a = dict(re.findall(r"<ms:(\w+)>([^<]*)</ms:\w+>", f)); rings = []
    for pl in re.findall(r"<gml:exterior>.*?<gml:posList[^>]*>([^<]*)</gml:posList>", f, flags=re.S):
        v = list(map(float, pl.split())); rings.append([(v[i + 1], v[i]) for i in range(0, len(v), 2)])  # (E, N)
    gm.append({"kod": a["JPT_KOD_JE"], "nazwa": a["JPT_NAZWA_"], "wersja_od": a["WERSJA_OD"], "wazny_od": a["WAZNY_OD"], "powierzchnia_ha": a["JPT_POWIER"], "rings": rings})
def pip(px, py, ring):
    c = False; n = len(ring); j = n - 1
    for i in range(n):
        xi, yi = ring[i]; xj, yj = ring[j]
        if (yi > py) != (yj > py) and px < (xj - xi) * (py - yi) / (yj - yi) + xi: c = not c
        j = i
    return c
def gmina(px, py):
    for g in gm:
        if any(pip(px, py, r) for r in g["rings"]): return g
C = 128; cnt = collections.Counter(); tot = 0
for i in range((X1 - X0) // C):
    for j in range((Y1 - Y0) // C):
        g = gmina(X0 + (i + .5) * C, Y0 + (j + .5) * C); cnt[g["kod"] if g else "?"] += 1; tot += 1
json.dump({"zrodlo": "PRG WFS A03_Granice_gmin (files/gugik_raw/prg_gminy.xml)", "metoda": "raster 128 m, punkt w wielokacie (pierscienie zewnetrzne)",
           "gminy": [{k: g[k] for k in ("kod", "nazwa", "wersja_od", "wazny_od", "powierzchnia_ha")} | {"powiat_teryt": g["kod"][:4], "udzial_w_bbox_proc": round(100 * cnt[g["kod"]] / tot, 1),
                      "km2_w_bbox": round(cnt[g["kod"]] * C * C / 1e6, 1)} for g in sorted(gm, key=lambda g: -cnt[g["kod"]])],
           "poza_gminami_proc": round(100 * cnt["?"] / tot, 1),
           "powiaty_proc": {p: round(100 * sum(v for k, v in cnt.items() if k[:4] == p) / tot, 1) for p in ("2061", "2002")}}, open(root / "gugik/prg_gminy.json", "w"), ensure_ascii=False, indent=1)
sheets = list(csv.DictReader(open(root / "files/gugik_raw/sheets_all.csv")))
for r in sheets:
    a, b = r["box"].split(" "); r["xa"], r["ya"] = map(float, a.split(",")); r["xb"], r["yb"] = map(float, b.split(","))
def best(px, py, pred):
    c = [r for r in sheets if pred(r) and r["xa"] <= px <= r["xb"] and r["ya"] <= py <= r["yb"]]
    return max(c, key=lambda r: r["akt_data"]) if c else None
geo = {}
for fn in ("bridges_tunnels", "barriers"):
    for e in json.load(open(root / f"overpass/{fn}.json"))["elements"]: geo[("way", e["id"])] = e["geometry"]
for fn in ("junctions", "services"):
    for e in json.load(open(root / f"overpass/{fn}.json"))["elements"]:
        if e["type"] == "node": geo[("node", e["id"])] = [{"lat": e["lat"], "lon": e["lon"]}]
px = [json.loads(l) for l in open(root / "files/panoramax_raw/items.jsonl")]
kv = [json.loads(l) for l in open(root / "files/kartaview_raw/photos.jsonl")]
pxy = [(t.transform(p["lon"], p["lat"]), p["datetime"][:4]) for p in px]
kxy = [(t.transform(float(p["lng"]), float(p["lat"])), p["shotDate"][:4]) for p in kv]
out = []
for lm in json.load(open(root / "panoramax/landmarks_def.json")):
    ids = re.findall(r"(node|way) (\d+)", lm["osm"]); src = "wpisane recznie (przyblizone)"
    for typ, i in ids:
        if (typ, int(i)) in geo:
            g = geo[(typ, int(i))]; lm["lat"] = round(sum(p["lat"] for p in g) / len(g), 6); lm["lon"] = round(sum(p["lon"] for p in g) / len(g), 6); src = f"centroid wierzcholkow OSM {typ} {i}"; break
    X, Y = t.transform(lm["lon"], lm["lat"]); g = gmina(X, Y)
    o = best(X, Y, lambda r: r["produkt"] == "ORTO" and r["kolor"] == "RGB"); n = best(X, Y, lambda r: r["produkt"] == "NMT" and r["char_przestrz"].startswith("1.00") and "ARC" in r["format"]); m = best(X, Y, lambda r: r["produkt"] == "NMPT")
    pn = [yr for (a, b), yr in pxy if math.hypot(a - X, b - Y) <= 300]; kn = [yr for (a, b), yr in kxy if math.hypot(a - X, b - Y) <= 300]
    out.append({**lm, "pozycja_zrodlo": src, "x2180": round(X), "y2180": round(Y), "w_bbox": X0 <= X <= X1 and Y0 <= Y <= Y1, "gmina": g["nazwa"] if g else None, "powiat_teryt": g["kod"][:4] if g else None,
        "orto_rgb": f"{o['akt_data']} / {o['piksel']} m" if o else None, "orto_godlo": o["godlo"] if o else None, "nmt_1m": n["akt_data"] if n else None, "nmpt": f"{m['akt_data']} / {m['char_przestrz']}" if m else None,
        "lod1_2024": "tak (pakiet powiatu)", "lod2_2017": "tak (pakiet powiatu, stan 2017)",
        "panoramax_r300m": len(pn), "panoramax_lata": sorted(set(pn)), "kartaview_r300m_sekwencje_proba": len(kn), "kartaview_lata": sorted(set(kn))})
json.dump(out, open(root / "panoramax/landmarks.json", "w"), ensure_ascii=False, indent=1)
for o in out: print(o["id"], o["nazwa"][:40], o["lat"], o["lon"], o["w_bbox"], o["gmina"], o["orto_rgb"], o["nmt_1m"], o["nmpt"], o["panoramax_r300m"], o["panoramax_lata"], o["kartaview_r300m_sekwencje_proba"], o["kartaview_lata"])
print(json.load(open(root / "gugik/prg_gminy.json"))["powiaty_proc"]); print([(g["nazwa"], g["udzial_w_bbox_proc"]) for g in json.load(open(root / "gugik/prg_gminy.json"))["gminy"]])
