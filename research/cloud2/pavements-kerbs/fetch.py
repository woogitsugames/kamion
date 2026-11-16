#!/usr/bin/env python3
"""Pobiera pliki z manifestu (url_pliku -> files/docs/<plik_lokalny>) i weryfikuje sha256. exit != 0 przy niezgodnosci.
Opcja --frames: dodatkowo kadry z frames_selected.json (NIEOBEJRZANE, poza manifestem) -> files/frames/."""
import csv, hashlib, json, pathlib, sys, urllib.request
D = pathlib.Path(__file__).parent
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) research-client/1.0"}
jobs = {}
for x in csv.DictReader(open(D / "manifest.csv", encoding="utf-8")):
    if x["sha256"]:
        jobs[x["plik_lokalny"]] = (x["url_pliku"], x["sha256"], D / "files" / "docs" / x["plik_lokalny"])
if "--frames" in sys.argv and (D / "frames_selected.json").exists():
    for f in json.load(open(D / "frames_selected.json")):
        jobs[f["file_local"]] = (f["url_pliku"], f["sha256"], D / "files" / "frames" / f["file_local"])
bad = 0
for name, (url, sha, path) in sorted(jobs.items()):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        try:
            path.write_bytes(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=180).read())
        except Exception as ex:
            print("FAIL download", name, ex); bad += 1; continue
    got = hashlib.sha256(path.read_bytes()).hexdigest()
    ok = got == sha
    print("OK  " if ok else "BAD ", name, got[:16], path.stat().st_size)
    bad += 0 if ok else 1
print("files:", len(jobs), "bad:", bad)
sys.exit(1 if bad else 0)
