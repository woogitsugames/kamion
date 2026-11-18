"""Snap a lon to a way: snap.py file.osm way_id lon [lat] -> interpolated point on way polyline at given lon (or nearest to lat/lon)."""
import sys, math, xml.etree.ElementTree as ET
from pyproj import Transformer
T = Transformer.from_crs(4326, 2180, always_xy=True)
TI = Transformer.from_crs(2180, 4326, always_xy=True)
root = ET.parse(sys.argv[1]).getroot()
nodes = {n.get('id'): (float(n.get('lat')), float(n.get('lon'))) for n in root.findall('node')}
w = [x for x in root.findall('way') if x.get('id') == sys.argv[2]][0]
pts = [T.transform(nodes[nd.get('ref')][1], nodes[nd.get('ref')][0]) for nd in w.findall('nd') if nd.get('ref') in nodes]
lat, lon = float(sys.argv[3]), float(sys.argv[4])
p = T.transform(lon, lat)
best = None
for a, b in zip(pts, pts[1:]):
    dx, dy = b[0] - a[0], b[1] - a[1]
    t = max(0, min(1, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / (dx * dx + dy * dy)))
    q = (a[0] + t * dx, a[1] + t * dy)
    d = math.hypot(q[0] - p[0], q[1] - p[1])
    if best is None or d < best[0]:
        best = (d, q, math.degrees(math.atan2(dx, dy)) % 360)
lo, la = TI.transform(*best[1])
print(f'{la:.6f} {lo:.6f} E={best[1][0]:.1f} N={best[1][1]:.1f} dist_from_input={best[0]:.1f}m way_bearing={best[2]:.1f}')
