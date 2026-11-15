#!/usr/bin/env python3
"""Pobiera budynki OSM (Overpass) dla obu obszarow i zapisuje surowy wynik + date UTC."""
import json, sys, time, datetime, requests, pathlib
EP = "https://maps.mail.ru/osm/tools/overpass/api/interpreter"
AREAS = {  # south,west,north,east (WGS84) = kafle regionow EPSG:2180 przeliczone pyproj
    "trasa_c": (53.14550, 23.14371, 53.16800, 23.18850),  # kafel C + Sokolska/Kombatantow (S) i Wysockiego (E)
    "dojlidy": (53.09373, 23.16400, 53.11102, 23.21100),  # kafel Dojlidy + Dywizjonu 303 (W) i Kuronia (E)
}
out = pathlib.Path(__file__).resolve().parent.parent / "data"
for name, (s, w, n, e) in AREAS.items():
    q = f'[out:json][timeout:120];(way["building"]({s},{w},{n},{e});relation["building"]({s},{w},{n},{e}););out tags geom;'
    for i in range(5):
        try:
            r = requests.post(EP, data={"data": q}, timeout=180)
            if r.status_code == 200: break
        except requests.RequestException as ex:
            print("retry", ex.__class__.__name__)
        time.sleep(5 * 2**i)
    r.raise_for_status()
    ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    d = r.json()
    (out / f"overpass_{name}.json").write_text(json.dumps(d, ensure_ascii=False, separators=(",", ":")))
    (out / f"overpass_{name}.query.txt").write_text(f"# endpoint: {EP}\n# pobrano UTC: {ts}\n# osm_base: {d.get('osm3s',{}).get('timestamp_osm_base')}\n{q}\n")
    print(name, len(d["elements"]), ts, d.get("osm3s"))
