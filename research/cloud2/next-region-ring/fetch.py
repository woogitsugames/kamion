#!/usr/bin/env python3
"""Pobiera kadry z manifest.csv (wiersze 'kadr *', kolumna url_pliku) do files/frames/ i weryfikuje sha256. Exit != 0 przy niezgodnosci.
Uzycie: python3 -I fetch.py   (files/ jest w .gitignore; CC BY-SA 4.0 — referencja, nie tekstura)"""
import csv, hashlib, pathlib, subprocess, sys
root = pathlib.Path(__file__).resolve().parent; out = root / "files" / "frames"; out.mkdir(parents=True, exist_ok=True)
bad = 0; total = 0
for r in csv.DictReader(open(root / "manifest.csv", encoding="utf-8")):
    if not r["kategoria"].startswith("kadr") or not r["url_pliku"]: continue
    dest = root / r["plik_dowodu"]
    if not dest.exists() or hashlib.sha256(dest.read_bytes()).hexdigest() != r["sha256"]:
        subprocess.run(["curl", "-sS", "-m", "120", "-A", "kamion-research/1.0", "-o", str(dest), r["url_pliku"]], check=False)
    ok = dest.exists() and hashlib.sha256(dest.read_bytes()).hexdigest() == r["sha256"]
    total += dest.stat().st_size if dest.exists() else 0
    print("OK " if ok else "BAD", r["id"], dest.name); bad += not ok
print(f"{total / 1e6:.1f} MB, niezgodnych: {bad}"); sys.exit(1 if bad else 0)
