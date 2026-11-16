#!/usr/bin/env python3
"""Pobiera surowe dane OSM (API 0.6 /map) dla kafli trasy C i Dojlid -> files/osm/*.osm.
Overpass (overpass-api.de i lustra) byl niedostepny przez proxy sesji 2026-11-14 ~17:06 UTC, dlatego API 0.6."""
import sys, time, pathlib, urllib.request, datetime
OUT = pathlib.Path(__file__).parent / "files" / "osm"
OUT.mkdir(parents=True, exist_ok=True)
# (nazwa, W, S, E, N), krok 0.02 x 0.01 deg
AREAS = [("c", 23.130, 53.130, 23.210, 53.160), ("d", 23.170, 53.090, 23.250, 53.125)]
def tiles(w, s, e, n, dx=0.02, dy=0.0125):
    x = w
    while x < e - 1e-9:
        y = s
        while y < n - 1e-9:
            yield round(x, 4), round(y, 4), round(min(x + dx, e), 4), round(min(y + dy, n), 4)
            y += dy
        x += dx
for name, w, s, e, n in AREAS:
    for bb in tiles(w, s, e, n):
        f = OUT / f"{name}_{bb[0]}_{bb[1]}.osm"
        if f.exists() and f.stat().st_size > 200:
            continue
        url = "https://api.openstreetmap.org/api/0.6/map?bbox=%s,%s,%s,%s" % bb
        for attempt in range(4):
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "research-client/1.0"})
                data = urllib.request.urlopen(req, timeout=120).read()
                f.write_bytes(data)
                print(datetime.datetime.utcnow().isoformat(), url, len(data))
                break
            except Exception as ex:
                print("ERR", url, ex, file=sys.stderr); time.sleep(3 * (attempt + 1))
        time.sleep(1)
