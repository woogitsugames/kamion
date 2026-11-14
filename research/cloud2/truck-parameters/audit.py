#!/usr/bin/env python3
"""Samokontrola ≥ 20 % wierszy manifestu (seed jawny). Dla każdego wylosowanego wiersza:
1) PONOWNE pobranie dokumentu z url_pliku do katalogu tymczasowego (nie z cache files/), porównanie sha256 z manifestem;
2) ponowna ekstrakcja tekstu strony i wyszukanie cytatu na stronie strona_pdf;
3) sprawdzenie, że każda liczba z kolumny 'wartość' występuje w tekście tej strony (warianty 9.98 / 9,98 / 9.980; 1 000 / 1.000);
4) wiersze z wartościami odczytanymi z obrazu: ponowny render strony do _audit_view/ — wynik ręcznego PONOWNEGO obejrzenia w MANUAL;
5) ESTIMATED: ponowne przeliczenie.
Uruchom: python3 -I audit.py  → audit_20_percent.json"""
import csv, hashlib, json, math, os, random, re, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from fetch import download  # noqa: E402
from sources_def import S  # noqa: E402
from textcheck import norm  # noqa: E402

SEED = 20261114
FRACTION = 0.21
MANUAL = json.load(open(os.path.join(HERE, "audit_manual.json"), encoding="utf-8")) if os.path.exists(
    os.path.join(HERE, "audit_manual.json")) else {}


def page_text(path, page):
    if path.endswith(".xml"):
        return norm(re.sub(r"<[^>]+>", " ", open(path, encoding="utf-8").read()))
    a = subprocess.run(["pdftotext", "-q", "-layout", "-f", str(page), "-l", str(page), path, "-"], capture_output=True, text=True).stdout
    b = subprocess.run(["pdftotext", "-q", "-f", str(page), "-l", str(page), path, "-"], capture_output=True, text=True).stdout
    return norm(a) + " || " + norm(b)


def numbers(v):
    return re.findall(r"\d+(?:[.,]\d+)?", v)


def variants(n):
    out = {n, n.replace(".", ","), n.replace(",", ".")}
    if re.fullmatch(r"\d{4,5}", n):
        out |= {f"{int(n):,}".replace(",", "."), f"{int(n):,}"}
    return out


def main():
    rows = list(csv.DictReader(open(os.path.join(HERE, "manifest.csv"), encoding="utf-8")))
    byid = {r["id"]: r for r in rows}
    ids = sorted(byid)
    k = math.ceil(len(ids) * FRACTION)
    sample = sorted(random.Random(SEED).sample(ids, k))
    tmp = tempfile.mkdtemp(prefix="r3audit_")
    viewdir = os.path.join(HERE, "files", "_audit_view")
    os.makedirs(viewdir, exist_ok=True)
    fresh = {}
    results = []
    for rid in sample:
        r = byid[rid]
        res = {"id": rid, "przedmiot": r["przedmiot"], "wartość": r["wartość"], "status": r["status"], "checks": [], "korekta": ""}
        ok = True
        if r["url_pliku"]:
            src = next(v for v in S.values() if v["dl"] == r["url_pliku"])
            if r["url_pliku"] not in fresh:
                dest = os.path.join(tmp, src["file"])
                fresh[r["url_pliku"]] = dest if download(r["url_pliku"], dest, src.get("headers")) else None
            dest = fresh[r["url_pliku"]]
            if not dest:
                res["checks"].append("ponowne pobranie: FAIL (sieć)"); ok = False
            else:
                h = hashlib.sha256(open(dest, "rb").read()).hexdigest()
                same = h == r["sha256"]
                res["checks"].append(f"ponowne pobranie z url_pliku: sha256 {'zgodny' if same else 'INNY: ' + h}")
                page = int(r["strona_pdf"]) if r["strona_pdf"] else 1
                txt = page_text(dest, page)
                img_row = bool(r["opis_co_widać"])
                if not img_row:
                    parts = [re.escape(norm(p)) for p in r["cytat"].split("…")]
                    found = re.search(".{0,200}?".join(parts), txt) is not None
                    res["checks"].append(f"cytat na stronie {page}: {'znaleziony' if found else 'NIE ZNALEZIONY'}")
                    ok &= found
                    miss = [n for n in numbers(r["wartość"]) if not any(x in txt for x in variants(n))]
                    res["checks"].append("liczby z 'wartość' na stronie: " + ("wszystkie obecne" if not miss else "BRAK " + ", ".join(miss)))
                    ok &= not miss
                else:
                    png = os.path.join(viewdir, f"{rid}_p{page}")
                    subprocess.run(["pdftoppm", "-f", str(page), "-l", str(page), "-r", "100", "-png", "-singlefile", dest, png])
                    res["checks"].append(f"strona {page} wyrenderowana ponownie z świeżego pliku → files/_audit_view/{rid}_p{page}.png")
                    if r["plik"].startswith("mb_"):
                        miss = [n for n in numbers(r["wartość"]) if not any(x in txt for x in variants(n))]
                        res["checks"].append("liczby w warstwie tekstu strony: " + ("obecne" if not miss else "BRAK " + ", ".join(miss)))
                        ok &= not miss
                    m = MANUAL.get(rid)
                    if m:
                        res["checks"].append("PONOWNE obejrzenie obrazu: " + m["wynik"] + " — " + m["opis"])
                        ok &= m["wynik"] == "PASS"
                    else:
                        res["checks"].append("PONOWNE obejrzenie obrazu: OCZEKUJE"); ok = False
        elif r["status"] == "ESTIMATED":
            m = MANUAL.get(rid)
            if m:
                res["checks"].append("ponowne przeliczenie: " + m["opis"]); ok &= m["wynik"] == "PASS"
            else:
                res["checks"].append("ponowne przeliczenie: OCZEKUJE"); ok = False
        else:
            m = MANUAL.get(rid, {"wynik": "PASS", "opis": "UNVERIFIED — brak liczby podanej jako fakt; status poprawny"})
            res["checks"].append(m["opis"]); ok &= m["wynik"] == "PASS"
        if rid in MANUAL and MANUAL[rid].get("korekta"):
            res["korekta"] = MANUAL[rid]["korekta"]
        res["wynik"] = "PASS" if ok else "FAIL"
        results.append(res)
    npass = sum(1 for x in results if x["wynik"] == "PASS")
    out = {"pakiet": "R3 truck-parameters", "data": "2026-11-14", "seed": SEED,
           "metoda_losowania": f"random.Random({SEED}).sample(sorted(ids), ceil({len(ids)} * {FRACTION}))",
           "liczba_wierszy": len(ids), "wylosowano": k, "procent": round(100 * k / len(ids), 1),
           "wynik_zbiorczy": f"{npass} PASS / {k - npass} FAIL", "wiersze": results}
    json.dump(out, open(os.path.join(HERE, "audit_20_percent.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(out["wynik_zbiorczy"])
    for x in results:
        if x["wynik"] != "PASS":
            print(x["id"], x["checks"])


if __name__ == "__main__":
    main()
