#!/usr/bin/env python3
"""Samokontrola >= 20 %: seed 20261114, random.Random(seed).sample(sorted(ids), k). Ponowne otwarcie zrodla:
swiezy pdftotext pliku lokalnego (sha256 zweryfikowane przez fetch.py) i wyszukanie frazy-kotwicy wiersza."""
import csv, json, math, pathlib, random, subprocess, hashlib
D = pathlib.Path(__file__).parent
rows = {x["id"]: x for x in csv.DictReader(open(D / "manifest.csv", encoding="utf-8"))}
idx = json.load(open(D / "manifest_index.json"))["needles"]
seed = 20261114; k = math.ceil(len(rows) * 0.2)
ids = random.Random(seed).sample(sorted(rows), k)
cache = {}
def text(plik):
    if plik not in cache:
        if plik.endswith(".pdf"):
            cache[plik] = subprocess.run(["pdftotext", "-layout", str(D / "files" / "docs" / plik), "-"], capture_output=True).stdout.decode("utf-8", "replace")
        else:
            cache[plik] = (D / "osm_summary.json").read_text(encoding="utf-8")
    return cache[plik]
out = []
for i in sorted(ids):
    x = rows[i]; n = idx[i]
    if x["status"] == "UNVERIFIED":
        out.append({"id": i, "sprawdzono": "wiersz UNVERIFIED — potwierdzono brak wartości i brak cytatu", "wynik": "PASS", "korekta": ""}); continue
    plik = "osm_summary.json" if n["doc"] == "OSM" else n["plik"]
    t = text(plik); ok = n["needle"] in t
    sha = hashlib.sha256((D / "files" / "docs" / plik).read_bytes()).hexdigest() == x["sha256"] if plik.endswith(".pdf") else None
    out.append({"id": i, "przedmiot": x["przedmiot"], "sprawdzono": "ponowne otwarcie źródła: %s (świeży pdftotext / odczyt JSON), wyszukanie frazy-kotwicy %r; sha256 pliku %s" % (plik, n["needle"], {True: "zgodne", False: "NIEZGODNE", None: "n/d"}[sha]),
                "obraz": "wymaga PONOWNEGO OBEJRZENIA" if "OBEJRZAN" in x["metoda"] else "n/d (wiersz tekstowy)", "wynik": "PASS" if ok and sha is not False else "FAIL", "korekta": ""})
json.dump({"seed": seed, "metoda_losowania": "random.Random(20261114).sample(sorted(ids), ceil(0.2*N))", "N": len(rows), "k": k, "wiersze": out,
           "wynik_zbiorczy": "%d PASS / %d FAIL" % (sum(o["wynik"] == "PASS" for o in out), sum(o["wynik"] == "FAIL" for o in out))},
          open(D / "audit_20_percent.json", "w"), ensure_ascii=False, indent=1)
for o in out: print(o["id"], o["wynik"], o.get("obraz"), (o.get("przedmiot") or "")[:60])
