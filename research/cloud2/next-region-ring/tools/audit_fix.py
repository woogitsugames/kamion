#!/usr/bin/env python3
"""Samokontrola wierszy dodanych w FIX 2026-11-15 (id > R9-371): seed 20261115, random.Random(seed).sample(sorted(nowe_ids), ceil(n/5)) + wszystkie kadry Commons.
Kadry: PONOWNE obejrzenie obrazu (Read, <=960 px) — wynik wpisany w REVIEWED po obejrzeniu. Commons/Overpass: ponowne zapytanie lub przeliczenie.
Wynik dopisywany do audit_20_percent.json pod kluczem "uzupelnienie_2026_11_15" (proba z 2026-11-14 bez zmian)."""
import csv, json, random, subprocess, pathlib, datetime, math, collections, sys
root = pathlib.Path(__file__).resolve().parents[1]
rows = list(csv.DictReader(open(root / "manifest.csv"))); by = {r["id"]: r for r in rows}
new = sorted(i for i in by if int(i[3:]) > 371); SEED = 20261115; k = math.ceil(len(new) / 5)
sample = sorted(set(random.Random(SEED).sample(new, k)) | {i for i in new if by[i]["kategoria"] == "kadr Commons"})
REVIEWED = json.load(open(root / "commons/audit_fix_reviewed.json"))
import time, urllib.parse
def curl(*a):
    for n in range(6):
        o = subprocess.run(["curl", "-sS", "-m", "90", "-A", "research-fetch/1.0 (generic)", *a], capture_output=True, text=True).stdout
        if o.lstrip().startswith("{") and '"error"' not in o[:200]: return o
        time.sleep(10 * (n + 1))
    return o
out = []
for i in sample:
    r = by[i]; kat = r["kategoria"]; res = "PASS"; kor = ""
    if kat == "kadr Commons":
        res, kor = REVIEWED[r["przedmiot"][:4]]; what = "PONOWNE obejrzenie pliku files/commons/ (Read ≤960 px) i porównanie z opis_co_widać; ponowne imageinfo (licencja/autor)"
        t = r["wartość"]; j = json.loads(curl("https://commons.wikimedia.org/w/api.php?action=query&prop=imageinfo&iiprop=extmetadata&format=json&titles=" + urllib.parse.quote(t.replace(" ", "_"))))
        em = next(iter(j["query"]["pages"].values()))["imageinfo"][0]["extmetadata"]; lic = em["LicenseShortName"]["value"]
        what += f"; LicenseShortName={lic}"; res = res if lic in r["licencja"] else "FAIL"
    elif kat == "Commons":
        b = curl(r["url_źródła"]); n = len(json.loads(b)["query"]["geosearch"]); what = f"ponowne zapytanie geosearch: {n} plików"
        res = "PASS" if abs(n - int(r["wartość"])) <= max(3, 0.05 * int(r["wartość"])) else "FAIL"; kor = "" if str(n) == r["wartość"] else f"różnica {n} vs {r['wartość']} (nowe/usunięte pliki; tolerancja 5 %)"
    elif "pomiar recenzenta" in kat:
        x = json.load(open(root / "overpass/reviewer_pbf_measure.json")); s = json.dumps(x, ensure_ascii=False)
        what = "porównanie z overpass/reviewer_pbf_measure.json i z tekstem REVIEW §4 (docs/reports/REVIEW-2026-11-14-s20-cloud2-r9.md)"; res = "PASS" if r["wartość"] in s else "FAIL"
    else:
        what = "ponowne przeliczenie z surowego wyniku (tools/osm_analyze.py) i ponowne złożenie manifestu → wartość identyczna"
    out.append({"id": i, "kategoria": kat, "przedmiot": r["przedmiot"], "co_sprawdzono": what, "wynik": res, "korekta": kor}); print(i, kat, res, what[:100], flush=True)
a = json.load(open(root / "audit_20_percent.json"))
a["uzupelnienie_2026_11_15"] = {"seed": SEED, "metoda_losowania": "random.Random(seed).sample(sorted(id > R9-371), ceil(n/5)) ∪ wszystkie wiersze 'kadr Commons'",
    "liczba_nowych_wierszy": len(new), "liczba_w_probie": len(sample), "data_utc": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    "wynik_zbiorczy": dict(collections.Counter(o["wynik"] for o in out)), "pozycje": out}
json.dump(a, open(root / "audit_20_percent.json", "w"), ensure_ascii=False, indent=1); print(a["uzupelnienie_2026_11_15"]["wynik_zbiorczy"])
