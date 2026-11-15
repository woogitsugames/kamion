"""Panoramax STAC search per tile bbox; logs queries and counts. usage: pano_search.py tiles_wgs84.json out.json"""
import json, sys, time, requests
UA = {"User-Agent": "research-client/1.0 (generic)"}
tiles = json.load(open(sys.argv[1]))
hosts = ["https://api.panoramax.xyz/api/search", "https://panoramax.openstreetmap.fr/api/search", "https://panoramax.ign.fr/api/search"]
res = {"queried_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "tiles": {}}
for k, b in tiles.items():
    res["tiles"][k] = {}
    for h in hosts:
        url = f"{h}?bbox={b[0]},{b[1]},{b[2]},{b[3]}&limit=500"
        try:
            r = requests.get(url, headers=UA, timeout=90); j = r.json()
            feats = j.get("features", [])
            res["tiles"][k][h] = {"url": url, "status": r.status_code, "n": len(feats), "features": feats}
            print(k, h.split('/')[2], r.status_code, len(feats), flush=True)
        except Exception as e:
            res["tiles"][k][h] = {"url": url, "error": str(e)}
            print(k, h, "ERR", e, flush=True)
        time.sleep(0.5)
json.dump(res, open(sys.argv[2], "w"))
