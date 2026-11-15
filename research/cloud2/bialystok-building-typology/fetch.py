#!/usr/bin/env python3
"""Pobiera pliki z manifest.csv (url_pliku) do files/ i weryfikuje sha256. Exit != 0 przy niezgodności lub błędzie pobrania."""
import csv, hashlib, pathlib, sys, time, requests
ROOT = pathlib.Path(__file__).resolve().parent; bad = 0
for r in csv.DictReader(open(ROOT / "manifest.csv", encoding="utf-8")):
    if not r["url_pliku"]: continue
    if "w repo" in r["uwagi"]:  # kadry Commons z 2026-11-15: plik JPG jest w repo — tylko weryfikacja sha256
        f = ROOT / r["uwagi"].split("plik ")[1].split(" ")[0]; h = hashlib.sha256(f.read_bytes()).hexdigest() if f.exists() else "MISSING"
        print(r["id"], "OK (repo)" if h == r["sha256"] else f"SHA MISMATCH {h}"); bad += h != r["sha256"]; continue
    sub = "panoramax" if "panoramax" in r["url_pliku"] else "kartaview"
    dst = ROOT / "files" / sub / (r["id"] + ".jpg"); dst.parent.mkdir(parents=True, exist_ok=True)
    data = None
    for i in range(4):
        try:
            q = requests.get(r["url_pliku"], timeout=90, headers={"User-Agent": "research-script/1.0 (generic)"})
            if q.status_code == 200: data = q.content; break
        except requests.RequestException: pass
        time.sleep(3 * 2**i)
    if data is None: print("FAIL download", r["id"]); bad += 1; continue
    dst.write_bytes(data); h = hashlib.sha256(data).hexdigest()
    print(r["id"], "OK" if h == r["sha256"] else f"SHA MISMATCH {h}"); bad += h != r["sha256"]
sys.exit(1 if bad else 0)
