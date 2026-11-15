import sys, json, math
sys.path.insert(0, r"C:/Users/matma/Documents/Claude/kamion/tools/refs")
import mapillary_fetch as M
import requests
from pyproj import Transformer
tok = M.resolve_token()
assert tok, "no token"
t = Transformer.from_crs(2180, 4326, always_xy=True)
t2 = Transformer.from_crs(4326, 2180, always_xy=True)
ox, oy = 759563.0, 610559.0
X = (-732.15, -533.39)
lon0, lat0 = t.transform(ox + X[0] - 350, oy + X[1] - 350)
lon1, lat1 = t.transform(ox + X[0] + 350, oy + X[1] + 350)
out = []
for layer in ("traffic_signs",):
    r = requests.get("https://graph.mapillary.com/map_features", headers={"Authorization": f"OAuth {tok}"},
                     params={"bbox": f"{lon0:.6f},{lat0:.6f},{lon1:.6f},{lat1:.6f}",
                             "fields": "id,object_value,object_type,geometry,first_seen_at,last_seen_at", "limit": 500}, timeout=60)
    print(r.status_code)
    d = r.json().get("data", [])
    for f in d:
        lon, lat = f["geometry"]["coordinates"]
        x, y = t2.transform(lon, lat)
        e, n = x - ox, y - oy
        out.append((round(math.hypot(e - X[0], n - X[1]), 1), f["object_value"], round(e, 1), round(n, 1), f.get("last_seen_at", "")[:10]))
for o in sorted(out):
    print(o)
