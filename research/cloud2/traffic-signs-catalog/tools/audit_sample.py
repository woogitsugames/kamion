"""Samokontrola 20 %: losowanie (seed 20261114) wierszy manifest.csv i catalog.csv + automatyczna kontrola tekstowa
(czy liczby z kolumny `wartość` występują na wskazanej stronie PDF). Kontrolę wizualną stron zapisano ręcznie w
audit_20_percent.json. Użycie: python -I tools/audit_sample.py ."""
import csv, json, math, random, re, sys
from pathlib import Path
D = Path(sys.argv[1]); SEED = 20261114
M = list(csv.DictReader(open(D / "manifest.csv", encoding="utf-8")))
K = list(csv.DictReader(open(D / "catalog.csv", encoding="utf-8")))
mids = random.Random(SEED).sample(sorted(r["id"] for r in M), math.ceil(0.2 * len(M)))
kids = random.Random(SEED).sample(sorted(r["kat_id"] for r in K), math.ceil(0.2 * len(K)))
TXT = {}
def pages(akt):
    key = {"Dz.U. 2019 poz. 2311": "2311_p", "Dz.U. 2019 poz. 2310": "2310_p"}.get(akt, "D" + akt.split()[1] + "%04d" % int(akt.split()[-1]) + "_p")
    if key not in TXT:
        t = open(D / "files" / "_derived" / f"{key}.txt", encoding="utf-8").read()
        parts = re.split(r"\n=== PDF p\.(\d+) ===\n", t)
        TXT[key] = {int(parts[i]): re.sub(r"\s+", " ", parts[i + 1]) for i in range(1, len(parts), 2)}
    return TXT[key]
out = {"seed": SEED, "metoda": "random.Random(seed).sample(sorted(ids), ceil(0.2*n))", "manifest": [], "catalog": []}
for r in M:
    if r["id"] not in mids: continue
    nums = re.findall(r"\d+(?:[.,]\d+)?", r["wartość"])
    pg = r["strona_pdf"]
    res = "n/d (strona '-')"
    if re.fullmatch(r"\d+", pg):
        txt = pages(r["akt"]).get(int(pg), "")
        hit = [n for n in nums if n.replace(".", ",") in txt or n in txt]
        res = f"tekst: {len(hit)}/{len(nums)} liczb na stronie" if nums else ("tekst: cytat " + ("TAK" if r["cytat"][:40].replace("…", "") in txt else "brak dosłownie (tabela-raster?)"))
    out["manifest"].append({"id": r["id"], "przedmiot": r["przedmiot"], "wartość": r["wartość"], "akt": r["akt"], "strona_pdf": pg, "auto": res})
for r in K:
    if r["kat_id"] not in kids: continue
    p2310 = pages("Dz.U. 2019 poz. 2310")
    name_ok = any(r["kod"] in t and r["nazwa"][:25] in t for t in p2310.values()) or "Dz.U. 20" in r["źródło_nazwy"][:9] or "Dz.U. 2021" in r["źródło_nazwy"] or "Dz.U. 2026" in r["źródło_nazwy"]
    out["catalog"].append({"kat_id": r["kat_id"], "kod": r["kod"], "nazwa": r["nazwa"], "auto_nazwa_w_2310": name_ok,
                           "kształt": r["kształt"], "barwy": f"{r['tło']} / {r['obrzeże_obwódka']} / {r['symbol_napis']}", "wzór": r["wzór_barwny_strona"]})
json.dump(out, open(D / "files" / "_derived" / "audit_auto.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(len(out["manifest"]), len(out["catalog"]))
for x in out["manifest"]: print(x["id"], x["strona_pdf"], x["akt"][-9:], "|", x["przedmiot"][:60], "|", x["wartość"][:40], "|", x["auto"])
print("pages:", sorted({(x["akt"][-9:], x["strona_pdf"]) for x in out["manifest"]}))
for x in out["catalog"]: print(x["kod"], x["auto_nazwa_w_2310"], x["kształt"], "|", x["barwy"][:70], "|", x["wzór"])
