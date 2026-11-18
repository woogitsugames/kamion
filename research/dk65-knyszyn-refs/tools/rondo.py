import requests, sys, json, math, xml.etree.ElementTree as ET
from pyproj import Transformer
UA = {"User-Agent": "research-client/1.0 (generic)"}
fw = Transformer.from_crs('EPSG:4326', 'EPSG:2180', always_xy=True)
bw = Transformer.from_crs('EPSG:2180', 'EPSG:4326', always_xy=True)
def mapq(x, y, h):
    a = bw.transform(x - h, y - h); b = bw.transform(x + h, y + h)
    r = requests.get("https://api.openstreetmap.org/api/0.6/map", params={"bbox": f"{a[0]},{a[1]},{b[0]},{b[1]}"}, headers=UA, timeout=90)
    r.raise_for_status(); return ET.fromstring(r.content)
name, x, y, h = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4])
root = mapq(x, y, h)
open(sys.argv[5], "wb").write(ET.tostring(root))
nodes = {n.get("id"): (float(n.get("lon")), float(n.get("lat")), {t.get("k"): t.get("v") for t in n.iter("tag")}) for n in root.iter("node")}
print("== ways in bbox", name)
for w in root.iter("way"):
    tags = {t.get("k"): t.get("v") for t in w.iter("tag")}
    if not tags: continue
    nds = [nd.get("ref") for nd in w.iter("nd")]
    pts = [fw.transform(*nodes[i][:2]) for i in nds if i in nodes]
    L = sum(math.dist(pts[i - 1], pts[i]) for i in range(1, len(pts)))
    key = {k: v for k, v in tags.items() if k in ("highway", "junction", "ref", "name", "lanes", "width", "oneway", "area:highway", "landuse", "natural", "barrier", "traffic_calming", "construction", "railway", "man_made", "leisure", "surface", "crossing", "lit", "building", "amenity", "highway:category:pl", "destination", "turn:lanes")}
    extra = ""
    if tags.get("junction") == "roundabout" and pts:
        cx = sum(p[0] for p in pts) / len(pts); cy = sum(p[1] for p in pts) / len(pts)
        rs = [math.dist((cx, cy), p) for p in pts]
        extra = f" RING centroid=({cx:.1f},{cy:.1f}) r_min={min(rs):.1f} r_max={max(rs):.1f} r_mean={sum(rs)/len(rs):.1f} n={len(pts)} closed={nds[0]==nds[-1]}"
    if key: print(w.get("id"), f"v{w.get('version')} {w.get('timestamp')[:10]}", key, f"L={L:.1f}m", extra)
print("== tagged nodes")
for i, (lo, la, t) in nodes.items():
    if t and any(k in t for k in ("highway", "traffic_sign", "crossing", "railway", "barrier", "public_transport", "man_made")):
        X, Y = fw.transform(lo, la); print(i, round(X, 1), round(Y, 1), {k: v for k, v in t.items()})
