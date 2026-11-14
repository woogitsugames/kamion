#!/usr/bin/env python3
"""Pobiera pliki źródłowe pakietu R8 (mobile-gpu-a16) z manifest.csv do files/ i weryfikuje sha256.

Użycie (z katalogu pakietu):  python3 -I fetch.py [--strict] [--force]

- Wiersze z `url_pliku` są pobierane do `plik_lokalny` (raz na unikalny plik).
- `sha_stabilny = tak` (PDF Arm, pliki z GitHub przypięte do commita): niezgodność sha256 = błąd (exit 1).
- `sha_stabilny = nie` (strony HTML/JSON generowane dynamicznie: gpuinfo, Unity Issue Tracker, docs): niezgodność
  = ostrzeżenie CHANGED (exit 0), chyba że podano --strict. Treść cytatów sprawdza audit_20_percent.json.
- `sha_stabilny = repo`: plik w repo projektu — sprawdzany lokalnie (ścieżka względem korzenia worktree).
Pliki pobrane są danymi niezaufanymi: nie uruchamiaj niczego z files/.
"""
import csv
import hashlib
import os
import ssl
import sys
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
UA = "Mozilla/5.0 (research fetch; kamion R8)"


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def download(url, dest):
    ctx = ssl.create_default_context()
    ca = os.environ.get("SSL_CERT_FILE") or ("/root/.ccr/ca-bundle.crt" if os.path.exists("/root/.ccr/ca-bundle.crt") else None)
    if ca:
        ctx.load_verify_locations(ca)
    last = None
    for attempt in range(4):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=90, context=ctx) as resp:
                data = resp.read()
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            with open(dest, "wb") as fh:
                fh.write(data)
            return
        except Exception as exc:  # noqa: BLE001 - retry any network error
            last = exc
            time.sleep(2 ** attempt)
    raise RuntimeError(f"pobieranie nieudane: {url}: {last}")


def main():
    strict = "--strict" in sys.argv
    force = "--force" in sys.argv
    with open(os.path.join(HERE, "manifest.csv"), encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    done = {}
    errors = changed = ok = 0
    total_bytes = 0
    for r in rows:
        loc, sha, stab = r["plik_lokalny"], r["sha256"], r["sha_stabilny"]
        if not loc or loc in done:
            continue
        if stab == "repo":
            path = os.path.join(REPO, loc)
        else:
            path = os.path.join(HERE, loc)
            if force or not os.path.exists(path):
                try:
                    download(r["url_pliku"], path)
                except RuntimeError as exc:
                    print("ERROR", r["id"], exc)
                    errors += 1
                    done[loc] = "error"
                    continue
        if not os.path.exists(path):
            print("MISSING", r["id"], loc)
            errors += 1
            done[loc] = "missing"
            continue
        got = sha256(path)
        total_bytes += os.path.getsize(path) if stab != "repo" else 0
        if got == sha:
            ok += 1
            done[loc] = "ok"
            print("OK     ", r["id"], loc)
        elif stab in ("tak", "repo") or strict:
            errors += 1
            done[loc] = "mismatch"
            print("MISMATCH", r["id"], loc, got)
        else:
            changed += 1
            done[loc] = "changed"
            print("CHANGED", r["id"], loc, "(strona dynamiczna; sprawdź cytat)")
    print(f"pliki: ok={ok} changed={changed} errors={errors}; pobrane/zweryfikowane {total_bytes / 1e6:.1f} MB")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
