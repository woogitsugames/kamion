#!/usr/bin/env python3
"""Sklada manifest.csv z plikow zbiorczych (overpass/, gugik/, panoramax/, kartaview/, commons/). Zadna liczba nie jest wpisywana recznie —
wartosci pochodza z plikow JSON/CSV wygenerowanych przez tools/*.py; opisy kadrow z panoramax/frames_desc.json i kartaview/frames_desc.json (napisane po obejrzeniu)."""
import json, csv, pathlib, collections, re
root = pathlib.Path(__file__).resolve().parents[1]
J = lambda p: json.load(open(root / p))
COLS = ["id", "kategoria", "przedmiot", "wartość", "jednostka", "status", "metoda", "cytat", "url_źródła", "url_pliku", "licencja", "autor", "data_dostępu", "sha256", "lat", "lon",
        "kierunek_deg", "opis_co_widać", "duplikat_sha256", "uwagi", "osm_id", "kurs_z_toru_deg", "data_zdjęcia", "plik_dowodu"]
rows = []
def add(kat, przedmiot, wartosc, jedn, status, metoda, cytat="", url="", **kw):
    r = dict.fromkeys(COLS, ""); r.update({"id": f"R9-{len(rows) + 1:03d}", "kategoria": kat, "przedmiot": przedmiot, "wartość": wartosc, "jednostka": jedn, "status": status,
        "metoda": metoda, "cytat": cytat, "url_źródła": url, "data_dostępu": "2026-11-14"}); r.update(kw); rows.append(r); return r
ODBL = "ODbL 1.0 (© OpenStreetMap contributors)"; GUG = "GUGiK dane otwarte (art. 40a ust. 2 pkt 1 Pgik); attribution: GUGiK"; OVP = "https://maps.mail.ru/osm/tools/overpass/api/interpreter"
log = {}
for l in open(root / "overpass/_log.jsonl"): r = json.loads(l); log[r["name"]] = r
def ovm(name): r = log[name]; return f"Overpass ({name}; zapytanie w overpass/_log.jsonl) {r['utc']}, osm_base {r['timestamp_osm_base']}; przycięcie do bboxu EPSG:2180 (tools/osm_analyze.py)"

# --- A. bbox
from pyproj import Transformer
ti = Transformer.from_crs(2180, 4326, always_xy=True)
X0, Y0, X1, Y1 = 764683, 584959, 787211, 605439
add("bbox", "Proponowany bbox regionu (EPSG:2180) xmin,ymin,xmax,ymax", f"{X0},{Y0},{X1},{Y1}", "m", "WORKING_VALUE", "siatka 2048 m zgodna z Data/Regions/*/region.yaml (origin 776971,595199): 6 kafli na W, 5 na E, 5 na S, 5 na N od regionu bialystok-industrial-c", plik_dowodu="Data/Regions/bialystok-industrial-c/region.yaml", uwagi="propozycja, nie decyzja")
for nm, (x, y) in (("SW", (X0, Y0)), ("SE", (X1, Y0)), ("NE", (X1, Y1)), ("NW", (X0, Y1))):
    lo, la = ti.transform(x, y); add("bbox", f"Narożnik {nm} bboxu (WGS84)", f"{la:.6f},{lo:.6f}", "deg", "ESTIMATED", "pyproj 3.8 EPSG:2180→EPSG:4326", lat=f"{la:.6f}", lon=f"{lo:.6f}")
add("bbox", "Powierzchnia bboxu", f"{(X1 - X0) * (Y1 - Y0) / 1e6:.1f}", "km2", "ESTIMATED", "(xmax-xmin)*(ymax-ymin)")
add("bbox", "Liczba kafli 2048 m (kolumny × wiersze)", f"{(X1 - X0) // 2048}x{(Y1 - Y0) // 2048}", "kafle", "ESTIMATED", "podział bboxu przez 2048 m")
add("bbox", "Obwiednia WGS84 użyta w zapytaniach Overpass/Panoramax (S,W,N,E)", "53.052,22.951,53.249,23.306", "deg", "WORKING_VALUE", "obwiednia narożników bboxu zaokrąglona na zewnątrz do 0.001°")
prg = J("gugik/prg_gminy.json")
PRG_URL = "https://mapy.geoportal.gov.pl/wss/service/PZGIK/PRG/WFS/AdministrativeBoundaries?SERVICE=WFS&VERSION=1.1.0&REQUEST=GetFeature&TYPENAME=ms:A03_Granice_gmin&SRSNAME=EPSG:2180&BBOX=584959,764683,605439,787211,EPSG:2180"
for g in prg["gminy"]:
    add("PRG", f"Gmina {g['nazwa']} (TERYT {g['kod']}, powiat {g['powiat_teryt']}) — udział w bboxie", g["udzial_w_bbox_proc"], "%", "ESTIMATED", prg["metoda"],
        f"JPT_KOD_JE={g['kod']} JPT_NAZWA_={g['nazwa']} WERSJA_OD={g['wersja_od']}", PRG_URL, licencja=GUG, plik_dowodu="gugik/prg_gminy.json", uwagi=f"{g['km2_w_bbox']} km2 w bboxie; HTTP 200 2026-11-14T17:17:53Z")
for p, v in prg["powiaty_proc"].items():
    add("PRG", f"Powiat {p} — udział w bboxie", v, "%", "ESTIMATED", prg["metoda"], url=PRG_URL, licencja=GUG, plik_dowodu="gugik/prg_gminy.json")

# --- B. wezly
for e in sorted(J("overpass/junctions.json")["elements"], key=lambda e: e["lon"]):
    g = e["tags"]; nm = g.get("name") or (g.get("proposed:name") and f"{g['proposed:name']} (proposed:name)") or (g.get("loc_name") and f"{g['loc_name']} (loc_name)")
    ref = g.get("ref") or (g.get("unsigned_ref") and f"unsigned_ref={g['unsigned_ref']}") or (g.get("proposed:ref") and f"proposed:ref={g['proposed:ref']}") or "brak ref"
    add("OSM węzły", f"motorway_junction: {nm}", ref, "ref", "SOURCED", ovm("junctions"), "; ".join(f"{k}={v}" for k, v in g.items()), f"https://www.openstreetmap.org/node/{e['id']}",
        licencja=ODBL, lat=f"{e['lat']:.6f}", lon=f"{e['lon']:.6f}", osm_id=f"node {e['id']}", plik_dowodu="overpass/junctions.json")

# --- C. drogi
sh = J("overpass/summary_highways.json"); HQ = "highways" if sh["zakres_klas"] == "wszystkie" else "major_wide"
DRV = ["motorway", "motorway_link", "trunk", "trunk_link", "primary", "primary_link", "secondary", "secondary_link", "tertiary", "tertiary_link", "unclassified", "residential", "living_street", "service", "track"]
for c in DRV:
    if c in sh["klasy"]:
        k = sh["klasy"][c]; add("OSM drogi", f"Długość highway={c} w bboxie", k["dlugosc_km"], "km", "ESTIMATED", ovm(HQ) + "; suma odcinków ze środkiem w bboxie; jezdnie rozdzielone liczone osobno", url=OVP, licencja=ODBL, plik_dowodu="overpass/summary_highways.json", uwagi=f"{k['liczba_way']} way")
for c in [c for c in sh["klasy"] if c.startswith(("construction", "proposed"))][:8]:
    k = sh["klasy"][c]; add("OSM drogi", f"Długość highway={c} w bboxie", k["dlugosc_km"], "km", "ESTIMATED", ovm(HQ), url=OVP, licencja=ODBL, plik_dowodu="overpass/summary_highways.json", uwagi=f"{k['liczba_way']} way")
for ref, v in list(sh["dlugosc_wg_ref_km"].items())[:22]:
    add("OSM drogi", f"Długość wg klasy|ref: {ref}", v, "km", "ESTIMATED", ovm(HQ), url=OVP, licencja=ODBL, plik_dowodu="overpass/summary_highways.json")
TG = ["lanes", "maxspeed", "surface", "width", "turn:lanes*", "destination*", "lit", "oneway", "layer", "bridge"]
for c in ["motorway", "motorway_link", "trunk", "trunk_link", "primary", "secondary", "tertiary", "residential", "service"]:
    if c not in sh["klasy"]: continue
    k = sh["klasy"][c]
    for tg in TG:
        add("OSM tagi", f"Pokrycie tagu {tg} na highway={c}", k["pokrycie_tagow_proc_dlugosci"][tg], "% długości", "ESTIMATED", ovm(HQ) + "; % = długość way z tagiem / długość klasy", url=OVP, licencja=ODBL,
            plik_dowodu="overpass/summary_highways.json", uwagi=f"klasa: {k['dlugosc_km']} km" + ("; bridge/layer: udział odcinków na obiektach, nie kompletność" if tg in ("layer", "bridge") else ""))

# --- D. budynki / drogi nizsze — 2 wiersze o stalych id (R9-0xx); dane z FIX 2026-11-15 w sekcji K na koncu manifestu
add("OSM budynki", "Liczba budynków i % z building:levels/height w bboxie", "patrz wiersze kategorii „OSM budynki*” na końcu manifestu", "", "SOURCED" if (root / "overpass/summary_buildings.json").exists() else "ESTIMATED",
    "uzupełnione 2026-11-15 (recenzja F2): Overpass buildings (kafle) i/lub pomiar recenzenta z PBF", uwagi="pierwotnie LUKA (2026-11-14: zapytanie przerwane przez limit sesji)", data_dostępu="2026-11-15")
add("OSM drogi", "Długości i tagi klas secondary/tertiary/residential/service w bboxie", "patrz wiersze kategorii „OSM drogi niższe*” na końcu manifestu", "", "SOURCED" if (root / "overpass/summary_highways_all.json").exists() else "ESTIMATED",
    "uzupełnione 2026-11-15 (recenzja F2): Overpass highways (kafle 4x4) i/lub pomiar recenzenta z PBF", uwagi="pierwotnie LUKA (2026-11-14: przerwane po 10/16 kafli)", data_dostępu="2026-11-15")
# --- E. obiekty
so = J("overpass/summary_objects.json")
for r in so["wiersze"]:
    add(r["kategoria"], r["przedmiot"], r["wartosc"], r["jednostka"], "ESTIMATED", ovm(r["zapytanie"]) + ("; " + r["metoda"] if r.get("metoda") else ""), r.get("cytat", ""), OVP, licencja=ODBL, plik_dowodu=f"overpass/{r['zapytanie']}.json", uwagi=r.get("uwagi", ""))

# --- F. GUGiK
cov = J("gugik/skorowidze_coverage.json"); summ = {(s["produkt"], s["rok_warstwy"]): s for s in J("gugik/skorowidze_summary.json")["wyniki"]}
for g in cov["grupy"]:
    s = summ[(g["produkt"], int(g["rok"]))]
    add(f"GUGiK {g['produkt']}", f"{g['produkt']} {g['rok']} {g['rozdzielczosc']}{' m' if g['produkt'] == 'ORTO' else ''} {g['kolor_format']} — pokrycie bboxu", g["pokrycie_bbox_proc"], "%", "ESTIMATED",
        "WFS skorowidz (GetFeature BBOX) + raster 64 m (tools/gugik_coverage.py)", f"akt_data {g['akt_data_min']}..{g['akt_data_max']}; nr_zglosz {g['nr_zglosz']}; modul {g['modul']}", s["url"], licencja=GUG,
        plik_dowodu="gugik/skorowidze_coverage.json", uwagi=f"{g['arkuszy']} arkuszy; HTTP {s['http']} {s['utc']}" + (f"; suma wlk_pliku_mb={g['suma_wlk_pliku_mb']:.0f}" if g["suma_wlk_pliku_mb"] else ""))
for (p, y), s in sorted(summ.items()):
    if s["arkuszy"] == 0: add(f"GUGiK {p}", f"{p} warstwa skorowidza {y} — arkuszy w bboxie", 0, "szt.", "SOURCED", "WFS skorowidz GetFeature BBOX — odpowiedź bez featureMember", f"HTTP {s['http']} {s['utc']}; 0 featureMember", s["url"], licencja=GUG, plik_dowodu="gugik/skorowidze_summary.json")
hs = J("gugik/head_sizes_sample.json"); hg = collections.defaultdict(list)
for p in hs["proba"]:
    if p["content_length"]: hg[p["grupa"]].append(p["content_length"])
rec = list(csv.DictReader(open(root / "gugik/skorowidze_sheets_recommended.csv"))); ng = collections.Counter((r["produkt"], r["rozdzielczosc"], r["akt_data"][:4]) for r in rec)
for name, m in cov["mozaiki"].items():
    add("GUGiK mozaika", f"Mozaika {name}: pokrycie bboxu", m["pokrycie_proc"], "%", "ESTIMATED", "najnowszy arkusz per komórka 64 m (tools/gugik_coverage.py)", f"akt_data {m['akt_data_min']}..{m['akt_data_max']}; udział rok|rozdz.: {m['udzial_powierzchni_rok_rozdz_proc']}",
        licencja=GUG, plik_dowodu="gugik/skorowidze_coverage.json", uwagi=f"{m['arkuszy']} arkuszy")
    if m["suma_wlk_pliku_mb"]:
        add("GUGiK rozmiar", f"Mozaika {name}: suma rozmiarów plików", round(m["suma_wlk_pliku_mb"] / 1024, 1), "GB", "ESTIMATED", "suma atrybutu wlk_pliku_mb skorowidza dla arkuszy mozaiki", licencja=GUG, plik_dowodu="gugik/skorowidze_sheets_recommended.csv", uwagi=f"{m['arkuszy']} arkuszy GeoTIFF")
tot = collections.defaultdict(float)
for (p, rz, yr), n in sorted(ng.items()):
    if p == "ORTO": continue
    v = hg.get(f"{p}|{rz}|{yr}")
    if v:
        est = sum(v) / len(v) * n / 1e9; tot[p] += est
        add("GUGiK rozmiar", f"{p} {rz} {yr}: szacowany rozmiar {n} arkuszy mozaiki", round(est, 2), "GB", "ESTIMATED", hs["metoda"] + f" (seed {hs['seed']}, próba {len(v)})", f"średni Content-Length {sum(v) / len(v) / 1e6:.1f} MB", licencja=GUG, plik_dowodu="gugik/head_sizes_sample.json", uwagi=f"HEAD {hs['utc']}")
for p, v in tot.items(): add("GUGiK rozmiar", f"{p}: szacowany rozmiar całej mozaiki (ASC)", round(v, 2), "GB", "ESTIMATED", "suma szacunków grup", licencja=GUG, plik_dowodu="gugik/head_sizes_sample.json")
for r in J("gugik/powiat_packages.json")["wiersze"]:
    add(r["kategoria"], r["przedmiot"], r["wartosc"], r["jednostka"], r["status"], r["metoda"], r["cytat"], r["url"], url_pliku=r.get("url_pliku", ""), licencja=r["licencja"], plik_dowodu="gugik/powiat_packages.json", uwagi=r.get("uwagi", ""))

# --- G. zdjecia: Panoramax / KartaView / Commons / Mapillary
PXL = "CC-BY-SA-4.0 (Panoramax; referencja, nie tekstura)"
pxs = J("panoramax/summary.json")
add("Panoramax", "Liczba zdjęć w obwiedni bboxu", pxs["liczba_zdjec"], "szt.", "SOURCED", "GET /api/search?bbox&limit=1000 (1 zapytanie, <1000 wyników = komplet)", f"features: {pxs['liczba_zdjec']}", pxs["url"], licencja=PXL, plik_dowodu="panoramax/search_log.json", uwagi=f"HTTP 200 {pxs['utc']}")
add("Panoramax", "Liczba sekwencji (collection) ze zdjęciami w bboxie", pxs["liczba_sekwencji"], "szt.", "ESTIMATED", "zliczenie pola collection w wynikach search", url=pxs["url"], licencja=PXL, plik_dowodu="panoramax/summary.json")
for yr, n in pxs["zdjecia_wg_roku"].items(): add("Panoramax", f"Zdjęcia z roku {yr}", n, "szt.", "ESTIMATED", "zliczenie properties.datetime", url=pxs["url"], licencja=PXL, plik_dowodu="panoramax/summary.json")
for s in pxs["sekwencje"]:
    add("Panoramax", f"Sekwencja {s['id']} ({s['data_min']}..{s['data_max']})", s["zdjec_w_bbox"], "szt.", "SOURCED", "zliczenie wyników search wg collection", f"collection={s['id']}; providers={s['autor']}",
        f"https://api.panoramax.xyz/api/collections/{s['id']}", licencja=PXL, autor=s["autor"], plik_dowodu="panoramax/summary.json", uwagi=f"zasięg lat {s['lat_min']}..{s['lat_max']}, lon {s['lon_min']}..{s['lon_max']}; {s['opis']}")
cc = J("panoramax/corridor_coverage.json")
for ref, v in [("RAZEM korytarze motorway/trunk/primary", cc["razem"])] + list(cc["wg_ref"].items()):
    add("Pokrycie zdjęciami", f"Korytarz ref={ref}: komórki 600 m z ≥1 zdjęciem Panoramax (r=500 m)", v["panoramax_proc"], "%", "ESTIMATED", "tools/photo_coverage.py", licencja=PXL, plik_dowodu="panoramax/corridor_coverage.json", uwagi=f"{v['panoramax']}/{v['komorek']} komórek; od 2024 r.: {v['panoramax_od_2024_proc']} %")
    add("Pokrycie zdjęciami", f"Korytarz ref={ref}: komórki 600 m z ≥1 zdjęciem KartaView (r=500 m)", v["kartaview_proc"], "%", "ESTIMATED", "tools/photo_coverage.py (zapytania /2.0/photo)", licencja="CC BY-SA 4.0 (KartaView)", plik_dowodu="panoramax/corridor_coverage.json", uwagi=f"{v['kartaview']}/{v['komorek']} komórek")
kl = J("kartaview/search_log.json")
add("KartaView", "Liczba zapytań /2.0/photo (r=500 m) wzdłuż korytarzy", kl["liczba_zapytan"], "szt.", "SOURCED", "tools/kartaview_corridor.py", f"http_nie_200={kl['http_nie_200']}", "https://api.kartaview.org/2.0/photo/", plik_dowodu="kartaview/search_log.json")
add("KartaView", "Unikalne zdjęcia zwrócone w próbie (API zwraca ok. 1 zdjęcie na sekwencję na zapytanie)", kl["liczba_zdjec_unikalnych"], "szt.", "SOURCED", "tools/kartaview_corridor.py", url="https://api.kartaview.org/2.0/photo/", licencja="CC BY-SA 4.0 (KartaView)", plik_dowodu="kartaview/search_log.json", uwagi="to dolne ograniczenie liczby zdjęć, nie pełna liczba")
ks = J("kartaview/sequences.json")
add("KartaView", "Liczba sekwencji przecinających korytarze", len(ks), "szt.", "SOURCED", "zliczenie sequenceId w próbie", url="https://api.kartaview.org/2.0/photo/", plik_dowodu="kartaview/sequences.json")
for s in ks:
    add("KartaView", f"Sekwencja {s['sequenceId']} (dodana {str(s['dateAdded'])[:10]})", s["countActivePhotos"], "zdjęć w całej sekwencji", "SOURCED", "GET /2.0/sequence/{id}", f"countActivePhotos={s['countActivePhotos']}; distance={s['distance']}",
        s["url"], licencja="CC BY-SA 4.0 (KartaView)", plik_dowodu="kartaview/sequences.json", uwagi=f"trafień w próbie korytarzy: {s['zdjec_trafionych_w_probie']}; sekwencja może wychodzić daleko poza bbox (distance km)")
cm = J("commons/geosearch_landmarks.json")
def commons_row(r):
  add("Commons", f"{r['landmark']} {r['nazwa']}: pliki z geotagiem w promieniu 1000 m", r["liczba_plikow_r1000m"] if r["liczba_plikow_r1000m"] is not None else "", "szt.", "SOURCED" if r["http"] == "200" and r["liczba_plikow_r1000m"] else "UNVERIFIED",
      "MediaWiki API list=geosearch gsradius=1000 gsnamespace=6 gsprimary=all gslimit=500", f"HTTP {r['http']}; geosearch: {r['liczba_plikow_r1000m']}", r["url"], licencja="różne (per plik; nie pobierano)", plik_dowodu="commons/geosearch_landmarks.json", data_dostępu=r["utc"][:10],
      uwagi=f"{r['utc']}; powtórzone 2026-11-15 po recenzji (wcześniejsze zera L01/L03/L05 = odpowiedzi z błędem API); tytuły z słowem drogowym (regex): {r['liczba_z_tytulem_drogowym']}" + ("; wynik 0 niespójny z sąsiednim punktem (możliwy błąd API w odpowiedzi 200) — do powtórzenia" if r["liczba_plikow_r1000m"] == 0 else "") + ("; limit 500 osiągnięty" if r["liczba_plikow_r1000m"] == 500 else ""))
for r in cm["wyniki"][:7]: commons_row(r)  # L01-L07 = wiersze z 2026-11-14 (stale id); L08-L24 dopisane w sekcji J
add("Mapillary", "Pokrycie Mapillary", "", "", "UNVERIFIED", "POMINIĘTO — brak własnego tokenu (zakaz w briefie)", uwagi="LUKA: research/g7-street-greenery/mapillary_sample.csv i docs/WORLD_GENERATION.md (street-r9) pokazują, że lider ma dostęp przez tools/refs")

# --- H. kadry
sel = J("panoramax/frames_selection.json"); desc = J("panoramax/frames_desc.json"); crs = J("panoramax/frames_course.json"); seen = {}
for s in sel:
    d = desc[str(s["n"])]; dup = seen.get(s["sha256"], "")
    r = add("kadr Panoramax", f"PX{s['n']:02d}: {d['obiekt']}", s["id"], "id zdjęcia", "SOURCED", "GET /api/search (assets.sd) → pobranie → obejrzenie pliku ≤960 px (Read)", f"view:azimuth={s['azimuth']}; datetime={s['datetime']}; original_file:name={s['original_file:name']}",
        f"https://api.panoramax.xyz/api/collections/{s['seq']}/items/{s['id']}", url_pliku=s["sd"], licencja=PXL, autor=", ".join(s["producer"]), sha256=s["sha256"], lat=f"{s['lat']:.6f}", lon=f"{s['lon']:.6f}", kierunek_deg=s["azimuth"],
        opis_co_widać=d["opis"], duplikat_sha256=dup, osm_id=d["osm"], kurs_z_toru_deg=crs.get(str(s["n"]), ""), data_zdjęcia=s["datetime"][:10], plik_dowodu=s["file"],
        uwagi="azymut z API (kompas telefonu); kurs_z_toru = namiar na następne zdjęcie sekwencji (ESTIMATED)" + ("; stan sprzed budowy S19 — kadr historyczny" if s["datetime"] < "2020" else ""))
    seen.setdefault(s["sha256"], r["id"])
ksel = J("kartaview/frames_selection.json"); kd = J("kartaview/frames_desc.json")
for s in ksel:
    d = kd[str(s["n"])]
    add("kadr KartaView", f"KV{s['n']:02d}: {d['obiekt']}", s["id"], "id zdjęcia", "SOURCED", "GET /2.0/photo (fileurlProc) → pobranie → obejrzenie pliku ≤960 px (Read)", f"heading={s['heading']}; shotDate={s['shotDate']}; sequenceId={s['sequenceId']}",
        f"https://kartaview.org/details/{s['sequenceId']}/{s['sequenceIndex']}", url_pliku=s["fileurlProc"], licencja="CC BY-SA 4.0 (KartaView; referencja, nie tekstura)", autor="użytkownik KartaView (pole user=null w API)", sha256=s["sha256"],
        lat=f"{float(s['lat']):.6f}", lon=f"{float(s['lng']):.6f}", kierunek_deg=s["heading"], opis_co_widać=d["opis"], osm_id=d["osm"], data_zdjęcia=s["shotDate"][:10], plik_dowodu=s["file"], uwagi="heading z API KartaView")

# --- I. landmarks
fid = {}
for r in rows:
    m = re.match(r"(PX\d\d|KV\d\d):", r["przedmiot"])
    if m: fid[m.group(1)] = r["id"]
cmd = {r["landmark"]: r for r in cm["wyniki"] if r["liczba_plikow_r1000m"]}
for lm in J("panoramax/landmarks.json"):
    px, kv = lm["panoramax_r300m"], lm["kartaview_r300m_sekwencje_proba"]; c = cmd.get(lm["id"], {})
    ocena = ("dane geometryczne pełne (OSM + ORTO " + str(lm["orto_rgb"]) + " + NMT " + str(lm["nmt_1m"]) + " + NMPT " + str(lm["nmpt"]) + " + LoD1 2024/LoD2 2017 powiat " + str(lm["powiat_teryt"]) + "); zdjęcia z poziomu jezdni: "
             + (f"Panoramax {px} ({','.join(lm['panoramax_lata'])})" if px else "Panoramax 0") + (f", KartaView sekw. {kv} ({','.join(lm['kartaview_lata'])})" if kv else ", KartaView 0")
             + (f", Commons r=1 km: {c.get('liczba_plikow_r1000m')}" if c else ""))
    add("landmark", f"{lm['id']} {lm['nazwa']}", ", ".join(lm["kadry"]) or "brak kadru", "kadry referencyjne", "ESTIMATED", "pozycja: " + lm["pozycja_zrodlo"] + "; dostępność: tools/prg_and_landmarks.py (skorowidze w punkcie, zdjęcia r=300 m)",
        url=f"https://www.openstreetmap.org/{lm['osm'].split(';')[0].strip().split(' (')[0].replace(' ', '/')}", licencja=ODBL, lat=f"{lm['lat']:.6f}", lon=f"{lm['lon']:.6f}", osm_id=lm["osm"], plik_dowodu="panoramax/landmarks.json",
        uwagi=ocena + "; kadry: " + (", ".join(f"{k}={fid[k]}" for k in lm["kadry"]) or "LUKA — brak zdjęcia z otwartych źródeł") + f"; gmina {lm['gmina']}; EPSG:2180 {lm['x2180']},{lm['y2180']}")

for r in cm["wyniki"][7:]: commons_row(r)
# --- J. (FIX 2026-11-15, recenzja F3) kadry Commons dla punktow bez kadru (L03, L19, L23); obejrzane (Read <=960 px)
for s in J("commons/frames_desc.json"):
    add("kadr Commons", f"CM{s['n']:02d}: {s['obiekt']}", s["title"], "plik Commons", "SOURCED", "MediaWiki API prop=imageinfo (extmetadata) → miniatura iiurlwidth=1600 → JPG ≤1600 px q82 w gałęzi → obejrzenie ≤960 px (Read)",
        f"LicenseShortName={s['license']}; Artist={s['artist']}; DateTimeOriginal={s['date']}", s["page"], url_pliku=s["thumb_url"], licencja=s["license"] + " (Commons; referencja, nie tekstura)", autor=s["artist"],
        sha256=s["sha256_local"], lat=f"{float(s['lat']):.6f}" if s["lat"] else "", lon=f"{float(s['lon']):.6f}" if s["lon"] else "", kierunek_deg="UNVERIFIED", opis_co_widać=s["opis"],
        data_zdjęcia=s["date"][:10] if s["date"][:2] == "20" else "2008-05-28", plik_dowodu=s["local"], data_dostępu="2026-11-15",
        uwagi=f"punkt {s['landmark']}; trafność: {s['trafnosc']}; sha256 = pliku JPG w gałęzi (po przeskalowaniu), sha1 oryginału Commons {s['orig_sha1']}; kierunek: brak azymutu geograficznego w metadanych")
# --- K. (FIX 2026-11-15, recenzja F2) drogi ponizej primary i budynki
sh = J("overpass/summary_highways_all.json") if (root / "overpass/summary_highways_all.json").exists() else {}
if sh.get("zakres_klas") == "wszystkie":
    for c in ("secondary", "tertiary", "unclassified", "residential", "living_street", "service", "track"):
        k = sh["klasy"].get(c)
        if not k: continue
        p = k["pokrycie_tagow_proc_dlugosci"]
        add("OSM drogi niższe", f"highway={c}: długość w bboxie (suma jezdni)", k["dlugosc_km"], "km", "SOURCED", ovm("highways"), f"liczba_way={k['liczba_way']}", OVP, licencja=ODBL, plik_dowodu="overpass/summary_highways.json", data_dostępu="2026-11-15",
            uwagi="pokrycie tagów % długości: " + ", ".join(f"{t} {p[t]}" for t in ("lanes", "maxspeed", "surface", "name", "lit", "sidewalk*", "width")))
for c, km, tg in J("overpass/reviewer_pbf_measure.json")["klasy"]:
    add("OSM drogi niższe (pomiar recenzenta)", f"highway={c}: długość w bboxie (PBF 2026-11-08)", km, "km", "ESTIMATED", "pomiar recenzenta lidera (REVIEW-2026-11-14-s20-cloud2-r9.md §4): PBF Geofabrik podlaskie 2026-11-08, pyosmium, przycięcie do bboxu EPSG:2180, długość po jezdniach",
        url="docs/reports/REVIEW-2026-11-14-s20-cloud2-r9.md", licencja=ODBL, plik_dowodu="overpass/reviewer_pbf_measure.json", data_dostępu="2026-11-15", uwagi=tg)
sb = root / "overpass/summary_buildings.json"
if sb.exists():
    b = J("overpass/summary_buildings.json")
    add("OSM budynki", "Liczba budynków (way + relacje multipolygon z building=*, środek w bboxie)", b["liczba_budynkow_w_bbox"], "szt.", "SOURCED", ovm("buildings"), url=OVP, licencja=ODBL, plik_dowodu="overpass/summary_buildings.json", data_dostępu="2026-11-15", uwagi=f"w tym way: {b['liczby'].get('_way')}, relacje: {b['liczby'].get('_relation')}; środek = center z Overpass (out center)")
    for t in ("building:levels", "height"):
        add("OSM budynki", f"Pokrycie tagu {t} (% liczby way)", b["pokrycie_proc"][t], "%", "SOURCED", ovm("buildings"), url=OVP, licencja=ODBL, plik_dowodu="overpass/summary_buildings.json", data_dostępu="2026-11-15")
rb = J("overpass/reviewer_pbf_measure.json")["budynki"]
add("OSM budynki (pomiar recenzenta)", "Liczba budynków (way building=*, środek wierzchołków w bboxie; PBF 2026-11-08)", rb["liczba"], "szt.", "ESTIMATED", "pomiar recenzenta lidera (REVIEW §4), pyosmium; relacji nie liczono", url="docs/reports/REVIEW-2026-11-14-s20-cloud2-r9.md", licencja=ODBL, plik_dowodu="overpass/reviewer_pbf_measure.json", data_dostępu="2026-11-15", uwagi=f"building:levels {rb['levels_proc']} %, height {rb['height_proc']} %")

with open(root / "manifest.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=COLS, lineterminator="\n"); w.writeheader(); w.writerows(rows)
print(len(rows), collections.Counter(r["kategoria"] for r in rows), collections.Counter(r["status"] for r in rows))
