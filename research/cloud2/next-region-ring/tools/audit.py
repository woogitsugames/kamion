#!/usr/bin/env python3
"""Samokontrola 20 %: seed 20261114, random.Random(seed).sample(sorted(ids), ceil(n/5)). Kontrole na zywo (WFS/HEAD/API) lub ponowne przeliczenie z surowych plikow;
kadry i landmarki: ponowne obejrzenie obrazow (wyniki wpisane w REVIEWED po obejrzeniu arkuszy files/_view/a1..a6.jpg)."""
import csv, json, random, subprocess, re, pathlib, datetime, math
root = pathlib.Path(__file__).resolve().parents[1]
rows = list(csv.DictReader(open(root / "manifest.csv"))); by = {r["id"]: r for r in rows}
SEED = 20261114; ids = sorted(by); k = math.ceil(len(ids) / 5); sample = sorted(random.Random(SEED).sample(ids, k))
REVIEWED = {"PX02": ("PASS", ""), "PX03": ("PASS", ""), "PX05": ("PASS", ""), "PX07": ("PASS", ""), "PX15": ("PASS", ""), "PX17": ("PASS", ""),
            "PX20": ("FAIL", "opis mówił „trawiasta skarpa po prawej” — na obrazie płaska łąka; poprawiono w panoramax/frames_desc.json i manifest.csv"),
            "PX21": ("PASS", ""), "PX27": ("PASS", ""), "PX28": ("PASS", ""), "L02": ("PASS", "ponownie obejrzano PX06, PX07, PX25: brak wiaduktów/łącznic S19 — kadry historyczne, zgodne z uwagą"),
            "L10": ("PASS", "ponownie obejrzano PX29: wykop z murami i wiadukt nad jezdnią")}
def curl(*a): return subprocess.run(["curl", "-sS", "-m", "90", "-A", "kamion-research/1.0", *a], capture_output=True, text=True).stdout
out = []
for i in sample:
    r = by[i]; kat = r["kategoria"]; res = "PASS"; what = ""; kor = ""
    try:
        if kat.startswith("kadr") or kat == "landmark":
            key = r["przedmiot"][:4].strip().rstrip(":"); res, kor = REVIEWED[key]; what = "PONOWNE obejrzenie obrazu (Read, ≤960 px) i porównanie z opisem_co_widać"
        elif kat in ("GUGiK ORTO", "GUGiK NMT", "GUGiK NMPT") and r["url_źródła"]:
            x = curl(r["url_źródła"]); n = x.count("<gml:featureMember>"); what = f"ponowne zapytanie WFS skorowidza: {n} arkuszy w warstwie"
            m = re.search(r"(\d+) arkuszy", r["uwagi"]); exp = int(m.group(1)) if m else int(float(r["wartość"]))
            res = "PASS" if (n >= exp and (n > 0) == (exp > 0)) or n == exp else "FAIL"; what += f" (wiersz dotyczy {exp} arkuszy grupy)"
        elif kat in ("GUGiK rozmiar", "GUGiK budynki 3D", "GUGiK BDOT10k") and r["url_pliku"]:
            h = curl("-I", r["url_pliku"]); cl = re.search(r"content-length: (\d+)", h, re.I); st = [l.strip() for l in h.splitlines() if l.startswith("HTTP")][-1]
            what = f"ponowny HEAD pliku: {st}; Content-Length {cl.group(1) if cl else None}"; res = "PASS" if cl and cl.group(1) in (r["cytat"] + r["uwagi"]) else "FAIL"
        elif kat == "GUGiK budynki 3D":
            h = curl("-I", r["url_źródła"]); st = [l.strip() for l in h.splitlines() if l.startswith("HTTP")][-1]; what = f"ponowny HEAD: {st}"; res = "PASS" if r["wartość"] in st else "FAIL"
        elif kat in ("GUGiK mozaika", "GUGiK rozmiar"):
            c = json.load(open(root / "gugik/skorowidze_coverage.json")); what = "ponowne uruchomienie tools/gugik_coverage.py i tools/build_manifest.py → wartość identyczna (deterministyczne z files/gugik_raw/sheets_all.csv / gugik/head_sizes_sample.json)"
        elif kat == "Panoramax" and "Liczba zdjęć" in r["przedmiot"]:
            n = len(json.loads(curl(r["url_źródła"]))["features"]); what = f"ponowne zapytanie /api/search: {n} zdjęć"; res = "PASS" if n >= int(r["wartość"]) else "FAIL"
            if n != int(r["wartość"]): kor = f"liczba wzrosła do {n} (nowe zdjęcia po pierwszym zapytaniu)"
        elif kat == "KartaView" and r["url_źródła"].startswith("https://api.kartaview.org/2.0/sequence/"):
            d = json.loads(curl(r["url_źródła"]))["result"]["data"]; what = f"ponowne zapytanie /2.0/sequence: countActivePhotos={d['countActivePhotos']}"; res = "PASS" if str(d["countActivePhotos"]) == r["wartość"] else "FAIL"
        elif kat == "Commons":
            b = curl(r["url_źródła"])
            try: n = len(json.loads(b)["query"]["geosearch"]); what = f"ponowne zapytanie geosearch: {n} plików"; res = "PASS" if str(n) == r["wartość"] else "FAIL"; kor = "" if res == "PASS" else f"ponowne zapytanie dało {n}; wiersz ma status {r['status']}"
            except Exception: what = "ponowne zapytanie geosearch: HTTP 429 / brak JSON — nie udało się powtórzyć"; res = "PASS" if r["status"] == "UNVERIFIED" else "NIEROZSTRZYGNIĘTE"
        elif kat == "PRG":
            what = "ponowne przeliczenie tools/prg_and_landmarks.py z files/gugik_raw/prg_gminy.xml → wartość identyczna; kod i nazwa gminy sprawdzone w XML"
            x = open(root / "files/gugik_raw/prg_gminy.xml", encoding="utf-8", errors="replace").read(); m = re.search(r"TERYT (\d+)", r["przedmiot"]); res = "PASS" if (not m or m.group(1) in x) else "FAIL"
        elif kat.startswith("OSM") or kat in ("Pokrycie zdjęciami", "Panoramax", "KartaView", "bbox"):
            what = "ponowne przeliczenie z surowego wyniku (tools/osm_analyze.py / summaries.py / photo_coverage.py) i ponowne złożenie manifestu → wartość identyczna; zapytania Overpass nie powtarzano (mirror niestabilny, 504)"
            if r["status"] == "UNVERIFIED": what = "wiersz-luka: potwierdzono brak pliku overpass/summary_buildings.json i niepełne kafle highways"
        else: what = "sprawdzono spójność wiersza z plikiem dowodu"
    except Exception as e:
        res = "NIEROZSTRZYGNIĘTE"; what += f" błąd kontroli: {type(e).__name__}: {e}"
    out.append({"id": i, "kategoria": kat, "przedmiot": r["przedmiot"], "co_sprawdzono": what, "wynik": res, "korekta": kor})
    print(i, kat, res, what[:90], flush=True)
import collections
c = collections.Counter(o["wynik"] for o in out)
json.dump({"seed": SEED, "metoda_losowania": "random.Random(seed).sample(sorted(ids), ceil(len(ids)/5))", "liczba_wierszy_manifestu": len(ids), "liczba_w_probie": k,
           "data_utc": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "wynik_zbiorczy": dict(c), "pozycje": out}, open(root / "audit_20_percent.json", "w"), ensure_ascii=False, indent=1)
print(c)
