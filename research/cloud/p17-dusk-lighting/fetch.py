#!/usr/bin/env python3
"""Pobiera pliki wskazane w manifest.csv (kolumny: id, plik, url_pliku, sha256) do files/ i weryfikuje sha256.

Użycie:  python3 fetch.py [--manifest manifest.csv] [--out files] [--delay 2.0]
Exit 0 = wszystkie pliki pobrane i zgodne; exit 1 = brak/niezgodność (lista na stderr).
Tylko biblioteka standardowa. Pliki już obecne i zgodne są pomijane. HTTP 429/503: ponowienie
z odczekaniem (Retry-After). Ten sam url_pliku w kilku wierszach pobierany jest raz.
"""
import argparse, csv, hashlib, os, sys, time, urllib.error, urllib.request

UA = "research-fetch/1.0 (open-data reference collection)"

def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

def download(url, dest, delay):
    for attempt in range(6):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=180) as r, open(dest + ".part", "wb") as f:
                while True:
                    chunk = r.read(1 << 16)
                    if not chunk:
                        break
                    f.write(chunk)
            os.replace(dest + ".part", dest)
            return True
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504):
                wait = int(e.headers.get("Retry-After") or 0) or delay * (2 ** (attempt + 1))
                time.sleep(min(wait, 120))
                continue
            sys.stderr.write("HTTP %s: %s\n" % (e.code, url))
            return False
        except (urllib.error.URLError, OSError) as e:
            sys.stderr.write("błąd sieci (%s), ponawiam: %s\n" % (e, url))
            time.sleep(delay * (2 ** (attempt + 1)))
    return False

def main():
    ap = argparse.ArgumentParser()
    here = os.path.dirname(os.path.abspath(__file__))
    ap.add_argument("--manifest", default=os.path.join(here, "manifest.csv"))
    ap.add_argument("--out", default=os.path.join(here, "files"))
    ap.add_argument("--delay", type=float, default=2.0)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    todo = {}
    with open(a.manifest, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            url, digest, name = row.get("url_pliku", "").strip(), row.get("sha256", "").strip().lower(), row.get("plik", "").strip()
            if not url or not digest or not name:
                continue
            if name in todo and todo[name] != (url, digest):
                sys.stderr.write("sprzeczne wiersze dla pliku %s\n" % name)
                return 1
            todo[name] = (url, digest)
    bad, total = [], 0
    for name, (url, digest) in sorted(todo.items()):
        if os.path.basename(name) != name:
            bad.append((name, "niedozwolona nazwa")); continue
        dest = os.path.join(a.out, name)
        if not (os.path.exists(dest) and sha256(dest) == digest):
            if not download(url, dest, a.delay):
                bad.append((name, "nie pobrano")); continue
            time.sleep(a.delay)
        got = sha256(dest)
        if got != digest:
            bad.append((name, "sha256 %s != %s" % (got, digest))); continue
        total += os.path.getsize(dest)
        print("OK  %s  %d B" % (name, os.path.getsize(dest)))
    print("plików: %d, zgodnych: %d, łącznie %d B" % (len(todo), len(todo) - len(bad), total))
    for name, why in bad:
        sys.stderr.write("BŁĄD %s: %s\n" % (name, why))
    return 1 if bad else 0

if __name__ == "__main__":
    sys.exit(main())
