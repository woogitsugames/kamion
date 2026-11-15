#!/usr/bin/env python3
"""Skan KartaView API 2.0 (photo, radius<=500 m) po siatce punktow w obu obszarach -> data/kartaview_<area>.json"""
import json, time, pathlib, requests, datetime
ROOT = pathlib.Path(__file__).resolve().parent.parent
AREAS = {"trasa_c": (53.1455, 23.1437, 53.1680, 23.1885), "dojlidy": (53.0937, 23.1640, 53.1110, 23.2110)}
for name, (s, w, n, e) in AREAS.items():
    seen = {}; lat = s + 0.003
    while lat < n:
        lon = w + 0.005
        while lon < e:
            page = 1
            while page <= 8:
                try:
                    r = requests.get("https://api.kartaview.org/2.0/photo/", params={"lat": lat, "lng": lon, "radius": 500, "itemsPerPage": 100, "page": page}, timeout=60)
                    d = r.json().get("result", {}).get("data", []) or []
                except Exception as ex:
                    print("err", ex); d = []
                for p in d: seen[p["id"]] = p
                if len(d) < 100: break
                page += 1
            lon += 0.008; time.sleep(0.3)
        lat += 0.005
    ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    json.dump({"fetched_utc": ts, "photos": list(seen.values())}, open(ROOT / "data" / f"kartaview_{name}.json", "w"))
    print(name, len(seen), ts)
