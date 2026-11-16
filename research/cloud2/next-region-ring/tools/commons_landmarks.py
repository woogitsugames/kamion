#!/usr/bin/env python3
"""Wikimedia Commons list=geosearch (gscoord, gsradius=1000 m, namespace 6, gsprimary=all, gslimit=500) dla kazdego punktu z panoramax/landmarks_def.json.
Respektuje 429 (Retry-After); odpowiedz 200 z kluczem "error" lub bez "query" = ponowienie (poprawka po recenzji 2026-11-14: wczesniej zera byly artefaktem bledow). Wynik: commons/geosearch_landmarks.json (url, utc, http, liczba, tytuly)."""
import subprocess, json, pathlib, datetime, time, sys, urllib.parse, re
root = pathlib.Path(__file__).resolve().parents[1]; (root / "commons").mkdir(exist_ok=True)
UA = "research-fetch/1.0 (generic)"
KW = re.compile(r"S8|S19|DK ?8|DK ?19|DK ?65|w[eę]ze[lł]|wiadukt|estakad|obwodnic|trasa|ekran|most|tunel|droga|ulica|rondo|kleeberg|maczk|anders|genera|lodow|jurowce|porosły|choroszcz", re.I)
out = []
for lm in json.load(open(root / "panoramax/landmarks_def.json")):
    url = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode({"action": "query", "list": "geosearch", "gscoord": f"{lm['lat']}|{lm['lon']}",
        "gsradius": 1000, "gsnamespace": 6, "gslimit": 500, "gsprimary": "all", "format": "json"})
    code = "000"; gs = None
    for a in range(10):
        r = subprocess.run(["curl", "-sS", "-m", "60", "-A", UA, "-D", str(root / "files/commons_hdr.txt"), "-w", "\n%{http_code}", url], capture_output=True, text=True)
        body, _, code = r.stdout.rpartition("\n")
        if code == "200":
            try: js = json.loads(body)
            except ValueError: js = {"error": "non-json"}
            if "error" not in js and "query" in js:  # 200 z kluczem "error" (np. ratelimited) = ponow, nie zero
                gs = js["query"].get("geosearch", []); break
        try: head = open(str(root / "files/commons_hdr.txt")).read()
        except OSError: head = ""
        ra = re.search(r"retry-after: (\d+)", head, re.I); time.sleep(int(ra.group(1)) + 3 if ra else 20)
    rec = {"landmark": lm["id"], "nazwa": lm["nazwa"], "url": url, "utc": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "http": code,
           "liczba_plikow_r1000m": None if gs is None else len(gs),
           "liczba_z_tytulem_drogowym": None if gs is None else sum(1 for g in gs if KW.search(g["title"])),
           "pliki": [] if gs is None else [{"title": g["title"], "pageid": g["pageid"], "lat": g["lat"], "lon": g["lon"], "dist": g["dist"]} for g in gs]}
    out.append(rec); print(lm["id"], code, rec["liczba_plikow_r1000m"], rec["liczba_z_tytulem_drogowym"], flush=True)
    json.dump({"metoda": __doc__, "slowa_kluczowe_regex": KW.pattern, "wyniki": out}, open(root / "commons/geosearch_landmarks.json", "w"), ensure_ascii=False, indent=0)
    time.sleep(3)
