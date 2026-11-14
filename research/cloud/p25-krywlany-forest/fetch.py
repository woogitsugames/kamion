#!/usr/bin/env python3
"""Pobiera pliki z manifest.csv (kolumna url_pliku) do files/ i weryfikuje sumy kontrolne. Tylko stdlib.

Użycie:  python3 -I fetch.py [--out files] [--strict] [--thumbs-only] [--tries N]

Weryfikacja: sha256 z manifestu, a gdy puste (oryginał z Commons był niedostępny dla autora — HTTP 429) — sha1 oryginału
z API Commons (files_index.csv). Gdy oryginał nadal zwraca 429, pobierana jest miniatura 1280 px (ta, którą autor oglądał)
i weryfikowane jest jej sha256 — niezgodność miniatury to tylko OSTRZEŻENIE (Commons może ją przerenderować).
Kod wyjścia: 0 = wszystko zgodne; 1 = niezgodna suma oryginału; 2 = błąd pobierania; z --strict także 3, gdy jakiś plik
istnieje tylko jako miniatura.
"""
import csv, hashlib, os, sys, time, urllib.request, urllib.error

UA = "research-fetch/1.0 (open-data reference collection)"
HERE = os.path.dirname(os.path.abspath(__file__))

def get(url, tries):
    last = None
    for t in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=180) as r:
                return r.read(), None
        except urllib.error.HTTPError as e:
            last = "HTTP %d" % e.code
            if e.code == 429 and t + 1 < tries:
                time.sleep(min(float(e.headers.get("retry-after") or 10), 60) + 2)
                continue
            if e.code != 429:
                break
        except Exception as e:  # sieć
            last = repr(e)
            time.sleep(2 + 2 * t)
    return None, last

def main():
    a = sys.argv[1:]
    out = a[a.index("--out") + 1] if "--out" in a else os.path.join(HERE, "files")
    tries = int(a[a.index("--tries") + 1]) if "--tries" in a else 3
    strict, thumbs_only = "--strict" in a, "--thumbs-only" in a
    os.makedirs(out, exist_ok=True)
    idx = {}
    p = os.path.join(HERE, "files_index.csv")
    if os.path.exists(p):
        with open(p, encoding="utf-8", newline="") as f:
            idx = {r["url_pliku"]: r for r in csv.DictReader(f)}
    with open(os.path.join(HERE, "manifest.csv"), encoding="utf-8", newline="") as f:
        rows = [r for r in csv.DictReader(f) if r.get("url_pliku")]
    seen, bad, err, thumb_only, ok = set(), 0, 0, 0, 0
    for r in rows:
        url = r["url_pliku"]
        if url in seen:
            continue
        seen.add(url)
        x = idx.get(url, {})
        name = r["id"] + "_" + (x.get("id") or "plik") + ".jpg"
        dst = os.path.join(out, name)
        data = None
        if not thumbs_only:
            if os.path.exists(dst):
                data = open(dst, "rb").read()
            else:
                data, why = get(url, tries)
        if data is not None:
            s256, s1 = hashlib.sha256(data).hexdigest(), hashlib.sha1(data).hexdigest()
            exp256, exp1 = r.get("sha256") or x.get("sha256"), x.get("sha1")
            if (exp256 and s256 != exp256) or (not exp256 and exp1 and s1 != exp1):
                print("NIEZGODNA SUMA", r["id"], url); bad += 1; continue
            if not exp256 and not exp1:
                print("BRAK SUMY W MANIFEŚCIE", r["id"]); bad += 1; continue
            open(dst, "wb").write(data); ok += 1
            print("ok ", r["id"], name, len(data), "B", "sha256" if exp256 else "sha1(Commons)")
            continue
        tu = x.get("url_miniatury")
        if not tu:
            print("BŁĄD POBIERANIA", r["id"], url); err += 1; continue
        tdst = os.path.join(out, r["id"] + "_" + x["id"] + "_1280px.jpg")
        td = open(tdst, "rb").read() if os.path.exists(tdst) else get(tu, max(tries, 6))[0]
        if td is None:
            print("BŁĄD POBIERANIA (oryginał i miniatura)", r["id"], url); err += 1; continue
        open(tdst, "wb").write(td); thumb_only += 1
        match = hashlib.sha256(td).hexdigest() == x.get("sha256_miniatury")
        print("miniatura", r["id"], os.path.basename(tdst), len(td), "B", "sha256 zgodne" if match else "OSTRZEŻENIE: sha256 miniatury inne (przerenderowana?)")
        time.sleep(1.5)
    print("RAZEM: %d plików; oryginały ok=%d; tylko miniatura=%d; niezgodne=%d; błędy=%d" % (len(seen), ok, thumb_only, bad, err))
    sys.exit(1 if bad else 2 if err else 3 if (strict and thumb_only) else 0)

if __name__ == "__main__":
    main()
