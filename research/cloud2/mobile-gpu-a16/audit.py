#!/usr/bin/env python3
"""Samokontrola R8: losuje ≥ 20 % wierszy manifestu, PONOWNIE pobiera źródło z sieci (albo czyta plik z repo)
i sprawdza, czy cytat występuje w świeżej treści. Wynik: audit_20_percent.json.

Użycie:  python3 -I audit.py <katalog_roboczy_poza_files>
Losowanie: random.Random(20261114).sample(sorted(ids), k), k = ceil(0.2 * n).
Normalizacja tekstu: NFKC (ligatury PDF), zamiana nbsp/typograficznych znaków, zwinięcie białych znaków, bez markdown `*`.
Cytat dzielony na fragmenty po ' … ' — każdy fragment musi wystąpić. Cytaty złożone z komórek tabel (Arm datasheet,
listy JSON gpuinfo) mają tryb 'manual' — wynik wpisuje się ręcznie po obejrzeniu strony (pole manual_override).
"""
import csv
import html
import json
import math
import os
import random
import re
import subprocess
import sys
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
SEED = 20261114
sys.path.insert(0, HERE)
from fetch import download  # noqa: E402

# wyniki ręczne (ponowne obejrzenie stron PDF jako obrazów / pól JSON) — wypełniane po przeglądzie
MANUAL = {}
if os.path.exists(os.path.join(HERE, "audit_manual.json")):
    with open(os.path.join(HERE, "audit_manual.json"), encoding="utf-8") as fh:
        MANUAL = json.load(fh)


def norm(s):
    s = unicodedata.normalize("NFKC", s)
    s = s.replace(" ", " ").replace("’", "'").replace("“", '"').replace("”", '"').replace("`", "")
    s = s.replace("*", "").replace("\\_", "_").replace("•", " ")
    s = re.sub(r"\s+", " ", s)
    return s.strip().lower()


def text_of(path):
    if path.endswith(".pdf"):
        return subprocess.run(["pdftotext", "-raw", path, "-"], capture_output=True, text=True).stdout
    raw = open(path, encoding="utf-8", errors="ignore").read()
    if path.endswith(".json"):
        try:
            d = json.loads(raw)
            if isinstance(d, dict) and "description" in d:
                return html.unescape(re.sub(r"<[^>]+>", " ", d["description"])) + " " + json.dumps(d, ensure_ascii=False)
        except ValueError:
            pass
        return raw
    if path.endswith(".md"):
        raw = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", raw)
        return raw
    if path.endswith((".html",)):
        raw = re.sub(r"<script.*?</script>|<style.*?</style>", " ", raw, flags=re.S)
        return html.unescape(re.sub(r"<[^>]+>", " ", raw))
    return raw


def main():
    work = sys.argv[1]
    os.makedirs(work, exist_ok=True)
    rows = list(csv.DictReader(open(os.path.join(HERE, "manifest.csv"), encoding="utf-8")))
    by_id = {r["id"]: r for r in rows}
    ids = sorted(by_id)
    k = math.ceil(0.2 * len(ids))
    sample = random.Random(SEED).sample(ids, k)
    fresh = {}
    out = []
    for rid in sorted(sample):
        r = by_id[rid]
        entry = {"id": rid, "przedmiot": r["przedmiot"], "status": r["status"], "cytat": r["cytat"],
                 "źródło": r["url_źródła"]}
        if not r["cytat"]:
            entry.update(sprawdzono="brak cytatu (wiersz ESTIMATED/UNVERIFIED) — sprawdzono metodę/obliczenie ręcznie",
                         wynik=MANUAL.get(rid, {}).get("wynik", "TODO"), korekta=MANUAL.get(rid, {}).get("korekta", ""))
            out.append(entry)
            continue
        if r["sha_stabilny"] == "repo":
            path = os.path.join(REPO, r["plik_lokalny"])
            how = "ponowne otwarcie pliku w repo (" + r["plik_lokalny"] + ")"
        else:
            url = r["url_pliku"]
            if url not in fresh:
                dest = os.path.join(work, re.sub(r"[^A-Za-z0-9._-]", "_", url)[-120:])
                if not dest.endswith((".pdf", ".json", ".html", ".md", ".adoc", ".cs")):
                    dest += os.path.splitext(r["plik_lokalny"])[1]
                download(url, dest)
                fresh[url] = dest
            path = fresh[url]
            how = "ponowne pobranie z sieci 2026-11-14 i wyszukanie cytatu (" + url + ")"
        txt = norm(text_of(path))
        parts = re.split(r"\s…\s|…|\.\.\.|;\s", r["cytat"])
        parts = [re.sub(r"\s*\((\d{5})\)\s*$", "", f) for f in parts]
        frags = [norm(f) for f in parts if norm(f)]
        missing = [f for f in frags if f not in txt]
        entry["sprawdzono"] = how
        if rid in MANUAL:
            entry["wynik"] = MANUAL[rid]["wynik"]
            entry["korekta"] = MANUAL[rid].get("korekta", "")
            entry["sprawdzono"] += "; " + MANUAL[rid]["sprawdzono"]
            entry["automat_brakujące_fragmenty"] = missing
        else:
            entry["wynik"] = "PASS" if not missing else "FAIL"
            entry["korekta"] = "" if not missing else "brak fragmentów: " + " | ".join(missing)
        out.append(entry)
    res = {
        "pakiet": "R8 mobile-gpu-a16", "data": "2026-11-14", "seed": SEED,
        "metoda_losowania": "random.Random(20261114).sample(sorted(ids), k), k = ceil(0.2 * n)",
        "n_wierszy": len(ids), "k": k,
        "pass": sum(1 for e in out if e["wynik"] == "PASS"),
        "fail": sum(1 for e in out if e["wynik"] == "FAIL"),
        "todo": sum(1 for e in out if e["wynik"] not in ("PASS", "FAIL")),
        "wiersze": out,
    }
    with open(os.path.join(HERE, "audit_20_percent.json"), "w", encoding="utf-8") as fh:
        json.dump(res, fh, ensure_ascii=False, indent=2)
    print(f"k={k} PASS={res['pass']} FAIL={res['fail']} TODO={res['todo']}")
    for e in out:
        if e["wynik"] != "PASS":
            print(e["id"], e["wynik"], e["przedmiot"], "|", e.get("korekta", ""))


if __name__ == "__main__":
    main()
