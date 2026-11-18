#!/usr/bin/env python3
"""Pliki zbiorcze dla manifestu: overpass/summary_objects.json (mosty, tunele, ekrany, bariery, stacje, MOP, sygnalizacje...),
panoramax/summary.json, panoramax/frames_course.json, gugik/powiat_packages.json (HEAD + GetFeatureInfo — wykonuje zapytania na zywo)."""
import json, pathlib, math, collections, subprocess, datetime, re, html, sys
from pyproj import Transformer
root = pathlib.Path(__file__).resolve().parents[1]
X0, Y0, X1, Y1 = 764683, 584959, 787211, 605439
t = Transformer.from_crs(4326, 2180, always_xy=True)
inb = lambda x, y: X0 <= x <= X1 and Y0 <= y <= Y1
def clen(g):
    p = [t.transform(q["lon"], q["lat"]) for q in g]
    return sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(p, p[1:]) if inb((a[0] + b[0]) / 2, (a[1] + b[1]) / 2))
def pos(e):
    if "center" in e: return e["center"]["lon"], e["center"]["lat"]
    if "lat" in e: return e["lon"], e["lat"]
    return None
def objects():
    W = []
    def add(kat, przedmiot, wartosc, jedn, zap, **kw): W.append({"kategoria": kat, "przedmiot": przedmiot, "wartosc": wartosc, "jednostka": jedn, "zapytanie": zap, **kw})
    d = json.load(open(root / "overpass/bridges_tunnels.json"))["elements"]; c = collections.Counter(); L = collections.defaultdict(float)
    for e in d:
        g = e["tags"]; s = clen(e["geometry"])
        if s <= 0: continue
        hw = g.get("highway"); grp = None
        if g.get("man_made") == "bridge": grp = "man_made=bridge (obrysy obiektów)"
        elif g.get("bridge") and hw in ("motorway", "motorway_link"): grp = "bridge na motorway(+link)"
        elif g.get("bridge") and hw in ("trunk", "trunk_link"): grp = "bridge na trunk(+link)"
        elif g.get("bridge") and hw in ("primary", "primary_link", "secondary", "secondary_link", "tertiary"): grp = "bridge na primary/secondary/tertiary"
        elif g.get("bridge") and hw in ("unclassified", "residential", "service", "track"): grp = "bridge na drogach niższych klas"
        elif g.get("bridge") and hw in ("footway", "path", "cycleway", "steps", "pedestrian"): grp = "bridge pieszo-rowerowe"
        elif g.get("bridge") and g.get("railway"): grp = "bridge kolejowe (rail + nieczynne)"
        elif g.get("bridge") and hw in ("construction", "proposed"): grp = "bridge w budowie/proponowane"
        elif g.get("tunnel") and hw in ("trunk", "primary", "secondary", "tertiary", "motorway"): grp = "tunnel na trunk/primary/secondary/tertiary"
        elif g.get("tunnel"): grp = "tunnel pozostałe (przejścia, przepusty drogowe, service)"
        if grp: c[grp] += 1; L[grp] += s
    for k in sorted(c, key=lambda k: -L[k]):
        add("OSM mosty/tunele", f"{k}: liczba way", c[k], "szt.", "bridges_tunnels", uwagi=f"łączna długość {L[k] / 1000:.2f} km (jezdnie osobno)")
    add("OSM mosty/tunele", "Mosty/wiadukty z nazwą (name lub bridge:name na way z bridge na motorway/trunk/primary)", sum(1 for e in d if e["tags"].get("bridge") and e["tags"].get("highway") in ("motorway", "trunk", "primary") and e["tags"].get("bridge:name")), "szt.", "bridges_tunnels", uwagi="name na tych way to nazwa ulicy, nie obiektu")
    d = json.load(open(root / "overpass/barriers.json"))["elements"]; c = collections.Counter(); L = collections.defaultdict(float)
    for e in d:
        g = e["tags"]; s = clen(e["geometry"])
        if s <= 0: continue
        k = "barrier=noise_barrier" if g.get("barrier") == "noise_barrier" else "barrier=wall + wall=noise_barrier" if g.get("wall") == "noise_barrier" else f"barrier={g.get('barrier')}" + (" (inne wall=*)" if g.get("wall") else "")
        c[k] += 1; L[k] += s
    c.setdefault("barrier=noise_barrier", 0)
    for k in sorted(c, key=lambda k: -L[k]):
        add("OSM ekrany/bariery", f"{k}: długość", round(L[k] / 1000, 2), "km", "barriers", uwagi=f"{c[k]} way")
    nb = [e for e in d if e["tags"].get("wall") == "noise_barrier" and clen(e["geometry"]) > 0]
    for tg in ("height", "material", "colour"):
        add("OSM ekrany/bariery", f"Ekrany (wall=noise_barrier) z tagiem {tg}", round(100 * sum(1 for e in nb if tg in e["tags"]) / len(nb), 1), "%", "barriers", uwagi=f"{sum(1 for e in nb if tg in e['tags'])}/{len(nb)} way")
    d = json.load(open(root / "overpass/services.json"))["elements"]; c = collections.Counter(); hg = 0; names = []
    for e in d:
        p = pos(e)
        if not p or not inb(*t.transform(*p)): continue
        g = e["tags"]
        k = g["highway"] if g.get("highway") in ("rest_area", "services", "toll_gantry") else g.get("amenity") or g.get("man_made")
        c[k] += 1
        if k == "fuel" and g.get("fuel:HGV_diesel") == "yes": hg += 1
        if k == "rest_area": names.append(f"{e['type']} {e['id']} {g.get('name', '(bez nazwy)')} operator={g.get('operator', '-')}")
    add("OSM MOP/stacje", "highway=services (MOP z usługami)", c.get("services", 0), "szt.", "services")
    add("OSM MOP/stacje", "highway=rest_area", c.get("rest_area", 0), "szt.", "services", cytat="; ".join(names), uwagi="wszystkie nazwane to MOR-y rowerowe (operator=Green Velo), nie MOP-y drogowe")
    add("OSM MOP/stacje", "amenity=fuel", c.get("fuel", 0), "szt.", "services", uwagi=f"w tym fuel:HGV_diesel=yes: {hg}")
    add("OSM MOP/stacje", "amenity=parking z hgv=yes/designated/only", c.get("parking", 0), "szt.", "services")
    add("OSM MOP/stacje", "highway=toll_gantry", c.get("toll_gantry", 0), "szt.", "services")
    add("OSM MOP/stacje", "amenity=weighbridge", c.get("weighbridge", 0), "szt.", "services")
    d = json.load(open(root / "overpass/signs_furniture.json"))["elements"]; c = collections.Counter()
    for e in d:
        g = e.get("tags", {})
        if "lat" in e and not inb(*t.transform(e["lon"], e["lat"])): continue
        c[g.get("highway") or ("traffic_sign" if "traffic_sign" in g else g.get("man_made"))] += 1
    for k in ("traffic_signals", "street_lamp", "traffic_sign", "milestone", "speed_camera", "gantry"):
        add("OSM wyposażenie", f"{'man_made' if k == 'gantry' else 'traffic_sign=*' if k == 'traffic_sign' else 'highway'}{'' if k == 'traffic_sign' else '=' + k} (węzły/way)", c.get(k, 0), "szt.", "signs_furniture")
    json.dump({"wiersze": W}, open(root / "overpass/summary_objects.json", "w"), ensure_ascii=False, indent=1); print(len(W), "object rows")
def panoramax():
    its = [json.loads(l) for l in open(root / "files/panoramax_raw/items.jsonl")]; lg = json.load(open(root / "panoramax/search_log.json"))
    by = collections.defaultdict(list)
    for i in its: by[i["collection"]].append(i)
    seqs = []
    for k, v in sorted(by.items(), key=lambda q: -len(q[1])):
        d = sorted(i["datetime"] for i in v); road = len(v) > 100
        seqs.append({"id": k, "zdjec_w_bbox": len(v), "data_min": d[0][:10], "data_max": d[-1][:10], "lat_min": round(min(i["lat"] for i in v), 4), "lat_max": round(max(i["lat"] for i in v), 4),
                     "lon_min": round(min(i["lon"] for i in v), 4), "lon_max": round(max(i["lon"] for i in v), 4), "autor": ", ".join(v[0]["producer"]), "aparat": v[0]["model"],
                     "z_azymutem": sum(1 for i in v if i["azimuth"] is not None), "opis": "przejazd samochodem S8→DK8→DK8/19 (kadry co ok. 75 m)" if road else "pojedyncze zdjęcia punktowe (POI/MapComplete)"})
    json.dump({"url": lg["zapytania"][0]["url"], "utc": lg["zapytania"][0]["utc"], "liczba_zdjec": len(its), "liczba_sekwencji": len(by),
               "zdjecia_wg_roku": dict(sorted(collections.Counter(i["datetime"][:4] for i in its).items())), "zdjecia_z_azymutem": sum(1 for i in its if i["azimuth"] is not None), "sekwencje": seqs},
              open(root / "panoramax/summary.json", "w"), ensure_ascii=False, indent=1)
    seq = {k: sorted(v, key=lambda i: i["datetime"]) for k, v in by.items()}
    def brg(a, b):
        la1, lo1, la2, lo2 = map(math.radians, (a["lat"], a["lon"], b["lat"], b["lon"]))
        return (math.degrees(math.atan2(math.sin(lo2 - lo1) * math.cos(la2), math.cos(la1) * math.sin(la2) - math.sin(la1) * math.cos(la2) * math.cos(lo2 - lo1))) + 360) % 360
    out = {}
    for s in json.load(open(root / "panoramax/frames_selection.json")):
        v = seq[s["seq"]]; n = next(i for i, q in enumerate(v) if q["id"] == s["id"])
        if len(v) > 100: out[str(s["n"])] = round(brg(v[n], v[n + 1]) if n + 1 < len(v) else brg(v[n - 1], v[n]))
    json.dump(out, open(root / "panoramax/frames_course.json", "w")); print("panoramax ok")
def powiaty():
    O = "https://opendata.geoportal.gov.pl"; W = "https://mapy.geoportal.gov.pl/wss/service/PZGIK"; R = []
    GUG = "GUGiK dane otwarte (art. 40a ust. 2 pkt 1 Pgik); attribution: GUGiK"; CC = "CC BY 4.0 (panel GetFeatureInfo GUGiK)"
    def head(u):
        h = subprocess.run(["curl", "-sS", "-m", "60", "-I", u], capture_output=True, text=True).stdout
        st = [l.strip() for l in h.splitlines() if l.startswith("HTTP")][-1]; cl = re.search(r"content-length: (\d+)", h, re.I); lm = re.search(r"last-modified: ([^\r\n]+)", h, re.I)
        return st, int(cl.group(1)) if cl else None, lm.group(1).strip() if lm else None
    def gfi(svc, layer, x, y):
        u = f"{W}/{svc}?SERVICE=WMS&VERSION=1.1.1&REQUEST=GetFeatureInfo&LAYERS={layer}&QUERY_LAYERS={layer}&SRS=EPSG:2180&BBOX={x - 50},{y - 50},{x + 50},{y + 50}&WIDTH=101&HEIGHT=101&X=50&Y=50&INFO_FORMAT=text/html&FEATURE_COUNT=10"
        r = subprocess.run(["curl", "-sS", "-m", "60", "-w", "\n%{http_code}", u], capture_output=True, text=True); body, _, code = r.stdout.rpartition("\n")
        body = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", body, flags=re.S); hrefs = re.findall(r'href="([^"]+)"', body)
        txt = html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", body))).strip().replace("Kliknij w celu rozwinięcia zawartości. --> ", "")
        return u, code, txt, hrefs
    now = lambda: datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    PT = {"2061": (777995, 596223, "Białystok"), "2002": (766882, 595756, "białostocki")}
    for teryt, (x, y, nm) in PT.items():
        u, code, txt, hrefs = gfi("BDOT/WMS/PobieranieBDOT10k", "Powiaty", x, y); gp = [h for h in hrefs if "GPKG" in h][0]; st, cl, lm = head(gp)
        R.append({"kategoria": "GUGiK BDOT10k", "przedmiot": f"BDOT10k powiat {teryt} ({nm}) — paczka GPKG: data modyfikacji pliku", "wartosc": lm, "jednostka": "Last-Modified", "status": "SOURCED", "metoda": "WMS GetFeatureInfo (warstwa Powiaty) → link; HEAD pliku",
                  "cytat": txt[:160], "url": u, "url_pliku": gp, "licencja": GUG, "uwagi": f"GFI HTTP {code} {now()}; HEAD: {st}; Content-Length {cl} B ({cl / 1e6:.1f} MB)"})
        R.append({"kategoria": "GUGiK rozmiar", "przedmiot": f"BDOT10k powiat {teryt} GPKG.zip — rozmiar", "wartosc": round(cl / 1e6, 1), "jednostka": "MB", "status": "SOURCED", "metoda": "HEAD Content-Length", "cytat": f"Content-Length: {cl}", "url": gp, "url_pliku": gp, "licencja": GUG, "uwagi": f"{st} {now()}"})
        for layer, lbl in (("Modele_3D_budynkow_LoD1_2024", "LoD1 2024"), ("Modele_3D_budynkow_LoD1_2022", "LoD1 2022"), ("Modele_3D_budynkow_LoD2_2017", "LoD2 2017")):
            u, code, txt, hrefs = gfi("FOTO/WMS/ModeleBudynkow3D", layer, x, y); m = re.search(r"Liczba budynków (\d+)", txt); f = hrefs[0]; st, cl, lm = head(f)
            R.append({"kategoria": "GUGiK budynki 3D", "przedmiot": f"Modele 3D budynków {lbl}, powiat {teryt} ({nm}) — liczba budynków", "wartosc": m.group(1) if m else "", "jednostka": "szt.", "status": "SOURCED" if m else "UNVERIFIED",
                      "metoda": f"WMS GetFeatureInfo warstwa {layer}", "cytat": txt[:170], "url": u, "url_pliku": f, "licencja": CC, "uwagi": f"GFI HTTP {code} {now()}; plik: {st}; {cl} B ({(cl or 0) / 1e6:.1f} MB); Last-Modified {lm}"})
            R.append({"kategoria": "GUGiK rozmiar", "przedmiot": f"Modele 3D budynków {lbl}, powiat {teryt} — rozmiar ZIP", "wartosc": round((cl or 0) / 1e6, 1), "jednostka": "MB", "status": "SOURCED", "metoda": "HEAD Content-Length", "cytat": f"Content-Length: {cl}", "url": f, "url_pliku": f, "licencja": CC, "uwagi": f"{st} {now()}"})
        f = f"{O}/InneDane/Drzewa3D/LOD1/2023/20/{teryt}.zip"; st, cl, lm = head(f)
        R.append({"kategoria": "GUGiK rozmiar", "przedmiot": f"Modele 3D drzew LoD1 2023, powiat {teryt} — rozmiar ZIP", "wartosc": round((cl or 0) / 1e9, 2), "jednostka": "GB", "status": "SOURCED", "metoda": "HEAD Content-Length (URL wg tools/worldgen/ingest.py)", "cytat": f"Content-Length: {cl}; Last-Modified: {lm}", "url": f, "url_pliku": f, "licencja": CC, "uwagi": f"{st} {now()}"})
        f = f"{O}/InneDane/Budynki3D/LOD1/2025/20/{teryt}.zip"; st, cl, lm = head(f)
        R.append({"kategoria": "GUGiK budynki 3D", "przedmiot": f"Modele 3D budynków LoD1 2025, powiat {teryt} — dostępność pod wzorcem URL", "wartosc": st.split(" ", 1)[1], "jednostka": "kod HTTP", "status": "SOURCED", "metoda": "HEAD (wzorzec URL z LoD1 2024 z podmienionym rokiem)", "cytat": st, "url": f, "licencja": CC, "uwagi": f"{now()}; warstwy WMS ModeleBudynkow3D: LoD1 2019/2021/2022/2024, LoD2 2017 — brak 2025"})
    json.dump({"wiersze": R}, open(root / "gugik/powiat_packages.json", "w"), ensure_ascii=False, indent=1); print(len(R), "powiat rows")
if __name__ == "__main__":
    for a in sys.argv[1:]: globals()[a]()
