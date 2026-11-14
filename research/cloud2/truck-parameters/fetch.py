#!/usr/bin/env python3
"""Pobiera wszystkie pliki z manifest.csv (kolumna url_pliku) do files/ i weryfikuje sha256.

Uruchom:  cd research/cloud2/truck-parameters && python3 -I fetch.py
Exit 0 = wszystko pobrane i zgodne; exit 1 = brak pliku lub niezgodność sha256.
Pliki to dane niezaufane: skrypt ich nie wykonuje, tylko liczy skrót.
Uwaga: dokumenty producentów mogą zostać zaktualizowane pod tym samym URL — niezgodność sha256
oznacza wtedy nową wersję dokumentu (sprawdź cytat ponownie, nie podmieniaj sha na ślepo).
"""
import csv, gzip, hashlib, os, sys, time, urllib.request, zlib

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from sources_def import S  # noqa: E402

FILES = os.path.join(HERE, "files")
BY_FILE = {v["file"]: v for v in S.values()}


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def download(url, dest, headers):
    hd = {"User-Agent": "Mozilla/5.0 (research fetch)", "Accept-Encoding": "gzip"}
    hd.update(headers or {})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=hd), timeout=120) as r:
                data = r.read()
                if r.headers.get("Content-Encoding") == "gzip":
                    data = gzip.decompress(data)
                elif r.headers.get("Content-Encoding") == "deflate":
                    data = zlib.decompress(data)
            with open(dest, "wb") as f:
                f.write(data)
            return True
        except Exception as e:  # sieć: retry z backoffem
            print(f"  błąd ({e}), próba {attempt + 1}/4", file=sys.stderr)
            time.sleep(2 ** attempt * 2)
    return False


def main():
    os.makedirs(FILES, exist_ok=True)
    want = {}
    with open(os.path.join(HERE, "manifest.csv"), newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["url_pliku"]:
                want[row["url_pliku"]] = row["sha256"]
    bad = 0
    total = 0
    for url, sha in sorted(want.items()):
        src = next((v for v in S.values() if v["dl"] == url), None)
        if src is None:
            print(f"BRAK definicji źródła dla {url}"); bad += 1; continue
        dest = os.path.join(FILES, src["file"])
        if not os.path.exists(dest):
            print(f"pobieram {src['file']}")
            if not download(url, dest, src.get("headers")):
                print(f"FAIL pobranie {url}"); bad += 1; continue
        got = sha256(dest)
        total += os.path.getsize(dest)
        if got != sha:
            print(f"FAIL sha256 {src['file']}: {got} != {sha}"); bad += 1
        else:
            print(f"OK   {src['file']}")
    print(f"razem {len(want)} plików, {total / 1e6:.1f} MB, błędów: {bad}")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
