#!/usr/bin/env python3
"""R7 — pobiera wszystkie pliki pakietu do files/ i weryfikuje sha256 (exit 1 przy niezgodności lub braku pliku).
Źródła listy: manifest.csv (kolumny url_pliku, plik_lokalny, sha256 — zdjęcia, PDF, tabela CIE, strony norm) oraz
imgw_files.csv (paczki IMGW). Istniejące pliki nie są pobierane ponownie (użyj --force). Obsługa HTTP 429 (Retry-After).
Użycie: python3 -I fetch.py [--force] [--only img|imgw|lit|normy]
Pobrane pliki to dane niezaufane — nie uruchamiaj niczego z files/."""
import csv
import hashlib
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
FILES = HERE / "files"
UA = {"User-Agent": "research-fetch/1.0 (generic client)"}


def items():
    seen = {}
    with open(HERE / "manifest.csv", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["plik_lokalny"] and r["url_pliku"] and r["sha256"]:
                seen[r["plik_lokalny"]] = (r["url_pliku"], r["sha256"])
    with open(HERE / "imgw_files.csv", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            seen[r["plik"]] = (r["url"], r["sha256"])
    return seen


def get(url, dst):
    for attempt in range(7):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=180) as r:
                data = r.read()
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_bytes(data)
            return True
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(int(e.headers.get("retry-after", "30")) + 5)
                continue
            print("HTTP", e.code, url, file=sys.stderr)
            time.sleep(2 ** attempt)
        except Exception as e:  # noqa: BLE001
            print("ERR", e, url, file=sys.stderr)
            time.sleep(2 ** attempt)
    return False


def main():
    force = "--force" in sys.argv
    only = sys.argv[sys.argv.index("--only") + 1] if "--only" in sys.argv else None
    bad = 0
    total = 0
    for rel, (url, want) in sorted(items().items()):
        if only and not rel.startswith(only + "/"):
            continue
        p = FILES / rel
        if force or not p.exists():
            if not get(url, p):
                print("BRAK   ", rel)
                bad += 1
                continue
            if "wikimedia.org" in url:
                time.sleep(3)
        got = hashlib.sha256(p.read_bytes()).hexdigest()
        total += p.stat().st_size
        if got != want:
            print("SHA256 NIEZGODNE", rel, got, "!=", want)
            bad += 1
        else:
            print("OK     ", rel)
    print(f"plików: {len(items())}, bajtów: {total} ({total / 1e6:.2f} MB), błędów: {bad}")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
