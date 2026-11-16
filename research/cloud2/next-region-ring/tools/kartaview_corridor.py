#!/usr/bin/env python3
"""KartaView API 2.0 /photo (lat,lng,radius<=500, itemsPerPage<=150): proba wzdluz korytarzy motorway/trunk/primary(+link) w bboxie R9.
Punkty probkowania: srodki komorek 600 m (EPSG:2180), przez ktore przechodzi os drogi (files/overpass_raw/major_wide.json).
Wynik: files/kartaview_raw/photos.jsonl + kartaview/search_log.json (kazde zapytanie: url, utc, http, n)."""
import json, subprocess, pathlib, datetime, time, sys, math
from pyproj import Transformer
root = pathlib.Path(__file__).resolve().parents[1]
raw = root / "files/kartaview_raw"; raw.mkdir(parents=True, exist_ok=True); (root / "kartaview").mkdir(exist_ok=True)
X0, Y0, X1, Y1 = 764683, 584959, 787211, 605439; C = 600
t = Transformer.from_crs(4326, 2180, always_xy=True); ti = Transformer.from_crs(2180, 4326, always_xy=True)
d = json.load(open(root / "files/overpass_raw/major_wide.json"))
cells = set()
for e in d["elements"]:
    if e["tags"]["highway"] not in ("motorway", "motorway_link", "trunk", "trunk_link", "primary", "primary_link"): continue
    pts = [t.transform(p["lon"], p["lat"]) for p in e["geometry"]]
    for (xa, ya), (xb, yb) in zip(pts, pts[1:]):
        n = max(1, int(math.hypot(xb - xa, yb - ya) / 100))
        for k in range(n + 1):
            x, y = xa + (xb - xa) * k / n, ya + (yb - ya) * k / n
            if X0 <= x <= X1 and Y0 <= y <= Y1: cells.add((int((x - X0) // C), int((y - Y0) // C)))
photos = {}; log = []
for n, (i, j) in enumerate(sorted(cells)):
    lon, lat = ti.transform(X0 + (i + .5) * C, Y0 + (j + .5) * C)
    page = 1
    while True:
        url = f"https://api.kartaview.org/2.0/photo/?lat={lat:.6f}&lng={lon:.6f}&radius=500&itemsPerPage=150&page={page}"
        r = subprocess.run(["curl", "-sS", "-m", "60", "-A", "research-fetch/1.0", "-w", "\n%{http_code}", url], capture_output=True, text=True)
        body, _, code = r.stdout.rpartition("\n")
        try: res = json.loads(body)["result"]
        except Exception: res = {"data": [], "hasMoreData": False}
        log.append({"url": url, "utc": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "http": code, "n": len(res["data"])})
        for p in res["data"]:
            photos[p["id"]] = {k: p.get(k) for k in ("id", "sequenceId", "sequenceIndex", "lat", "lng", "heading", "shotDate", "dateAdded", "fileurlProc", "fileurlLTh", "fileurlTh", "width", "height", "wayId", "projection", "fieldOfView")}
        if not res.get("hasMoreData") or page >= 40: break
        page += 1; time.sleep(0.2)
    if n % 25 == 0: print(n, len(cells), len(photos), file=sys.stderr, flush=True)
    time.sleep(0.2)
with open(raw / "photos.jsonl", "w") as f:
    for p in photos.values(): f.write(json.dumps(p) + "\n")
json.dump({"komorka_m": C, "liczba_punktow": len(cells), "liczba_zapytan": len(log), "http_nie_200": sum(1 for l in log if l["http"] != "200"),
           "liczba_zdjec_unikalnych": len(photos), "zapytania": log}, open(root / "kartaview/search_log.json", "w"))
print(len(cells), len(photos))
