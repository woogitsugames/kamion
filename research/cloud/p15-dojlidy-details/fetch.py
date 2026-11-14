#!/usr/bin/env python3
"""Pobiera pliki z manifest.csv (kolumny: plik, url_pliku, sha256, sha1_commons) do files/ i weryfikuje sumy.

Uruchomienie:  python3 -I fetch.py [--out files] [--skip-large]
Exit 0 = wszystkie pliki pobrane i zgodne; exit 1 = brak pliku lub niezgodność sumy.
Weryfikacja: sha256, gdy jest w manifeście; w przeciwnym razie sha1 z API Wikimedia Commons
(oryginałów Commons nie dało się pobrać w sesji badawczej — upload.wikimedia.org zwracał HTTP 429).
Tylko biblioteka standardowa. Pobrane pliki to niezaufane dane — nie uruchamiaj niczego z files/.
"""
import csv, hashlib, os, sys, time, urllib.error, urllib.parse, urllib.request

UA = "kamion-research/1.0 (open-data reference collection)"
HERE = os.path.dirname(os.path.abspath(__file__))


THROTTLED = set()  # hosty, które kazały czekać dłużej niż 120 s (HTTP 429 + Retry-After)


def download(url, tries=6):
    host = urllib.parse.urlsplit(url).netloc
    if host in THROTTLED:
        raise RuntimeError("host %s dławi ruch (HTTP 429) — uruchom fetch.py ponownie później" % host)
    delay = 5
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=300) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504) and i < tries - 1:
                ra = e.headers.get("Retry-After", "")
                if e.code == 429 and ra.isdigit() and int(ra) > 120:
                    THROTTLED.add(host)
                    raise RuntimeError("HTTP 429, Retry-After %s s (%s) — uruchom ponownie później" % (ra, host))
                wait = int(ra) if ra.isdigit() else delay
                print("   HTTP %d — czekam %d s" % (e.code, wait), flush=True)
                time.sleep(wait)
                delay *= 2
                continue
            raise
        except (urllib.error.URLError, TimeoutError, ConnectionError):
            if i == tries - 1:
                raise
            time.sleep(delay)
            delay *= 2
    raise RuntimeError("nie pobrano: " + url)


def main():
    out = os.path.join(HERE, "files")
    skip_large = "--skip-large" in sys.argv
    if "--out" in sys.argv:
        out = os.path.abspath(sys.argv[sys.argv.index("--out") + 1])
    os.makedirs(out, exist_ok=True)
    files = {}
    with open(os.path.join(HERE, "manifest.csv"), encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            if r["plik"] and r["url_pliku"]:
                prev = files.setdefault(r["plik"], (r["url_pliku"], r["sha256"], r["sha1_commons"]))
                if prev != (r["url_pliku"], r["sha256"], r["sha1_commons"]):
                    print("BŁĄD manifestu: różne dane dla pliku", r["plik"])
                    return 1
    bad = 0
    total = 0
    for name, (url, sha256, sha1) in sorted(files.items()):
        if os.sep in name or "/" in name or name.startswith("."):
            print("BŁĄD: niedozwolona nazwa pliku", name)
            return 1
        if skip_large and name.startswith("dzu_"):
            print("POMINIĘTO (--skip-large):", name)
            continue
        path = os.path.join(out, name)
        if os.path.exists(path):
            data = open(path, "rb").read()
        else:
            try:
                data = download(url)
            except Exception as e:  # noqa: BLE001
                print("BŁĄD pobierania %s: %s" % (name, e))
                bad += 1
                continue
            with open(path, "wb") as fo:
                fo.write(data)
            time.sleep(1.5)
        total += len(data)
        if sha256:
            ok = hashlib.sha256(data).hexdigest() == sha256
            kind = "sha256"
        elif sha1:
            ok = hashlib.sha1(data).hexdigest() == sha1
            kind = "sha1(Commons API)"
        else:
            ok = False
            kind = "brak sumy"
        print("%s %-48s %9d B  %s  sha256=%s" % ("OK " if ok else "ZLE", name, len(data), kind, hashlib.sha256(data).hexdigest()))
        if not ok:
            bad += 1
    print("plików: %d, bajtów: %d, błędów: %d" % (len(files), total, bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
