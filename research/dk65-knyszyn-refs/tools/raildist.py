"""Distance from route sample points to railway line 38 ways (OSM API way/full)."""
import json, math, requests, xml.etree.ElementTree as ET
from pyproj import Transformer
UA = {"User-Agent": "research-client/1.0 (generic)"}
fw = Transformer.from_crs('EPSG:4326', 'EPSG:2180', always_xy=True)
segs = []
for wid in (173466803, 41533341, 406675496):
    r = requests.get(f"https://api.openstreetmap.org/api/0.6/way/{wid}/full", headers=UA, timeout=60); root = ET.fromstring(r.content)
    N = {n.get("id"): fw.transform(float(n.get("lon")), float(n.get("lat"))) for n in root.iter("node")}
    pts = [N[nd.get("ref")] for nd in root.find("way").iter("nd")]
    segs += [(pts[i - 1], pts[i], wid) for i in range(1, len(pts))]
pts = json.load(open('km_points.json'))
for p in pts:
    if p['km'] > 14: continue
    best = (1e9, None)
    for (a, b, wid) in segs:
        dx, dy = b[0] - a[0], b[1] - a[1]; L2 = dx * dx + dy * dy
        t = max(0, min(1, ((p['x'] - a[0]) * dx + (p['y'] - a[1]) * dy) / L2)); d = math.dist((p['x'], p['y']), (a[0] + t * dx, a[1] + t * dy))
        if d < best[0]: best = (d, wid)
    print(p['km'], p['tile'], round(best[0], 1), best[1])
