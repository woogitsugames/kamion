"""Scan points 1 m outside the north fence (OSM way 483199984) and report runway cross-section visibility (1.7 / 2.5 m)."""
import sys, os, json, math, subprocess
import numpy as np
import xml.etree.ElementTree as ET
from pyproj import Transformer
T = Transformer.from_crs(4326, 2180, always_xy=True)
S = sys.argv[1]
root = ET.parse(S + '/m64/osm/airfield.osm').getroot()
nodes = {n.get('id'): (float(n.get('lat')), float(n.get('lon'))) for n in root.findall('node')}
w = [x for x in root.findall('way') if x.get('id') == '483199984'][0]
pts = [T.transform(nodes[nd.get('ref')][1], nodes[nd.get('ref')][0]) for nd in w.findall('nd') if nd.get('ref') in nodes]
out = []
step = float(sys.argv[2])
acc = 0
for a, b in zip(pts, pts[1:]):
    L = math.hypot(b[0] - a[0], b[1] - a[1])
    t = 0
    while t < L:
        if acc % step == 0:
            pass
        e = a[0] + (b[0] - a[0]) * t / L; n = a[1] + (b[1] - a[1]) * t / L
        out.append({'id': f'S{len(out)}', 'name': 'scan', 'en': [round(e, 1), round(n + 1.0, 1)]})
        t += step
json.dump(out, open(S + '/m64/scan_pts.json', 'w'))
print(len(out))
