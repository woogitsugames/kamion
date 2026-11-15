"""Building heights: NMPT 2023 (0.5 m) inside OSM polygon minus NMT ground (median of NMT in 3-8 m ring outside).
Prints max, p95, p50 of (NMPT - ground) inside polygon shrunk by 1 m."""
import sys, json, math
import numpy as np
import xml.etree.ElementTree as ET
from pyproj import Transformer
class Path:
    def __init__(self, P):
        self.P = [tuple(p) for p in P]
    def contains_point(self, q, radius=0):
        x, y = q; c = False; P = self.P
        for i in range(len(P)):
            a, b = P[i], P[i - 1]
            if (a[1] > y) != (b[1] > y):
                xi = a[0] + (y - a[1]) * (b[0] - a[0]) / (b[1] - a[1])
                if x < xi:
                    c = not c
        return c
S = sys.argv[1]
ids = sys.argv[2].split(',')
extra = json.loads(sys.argv[3]) if len(sys.argv) > 3 else {}
T = Transformer.from_crs(4326, 2180, always_xy=True)
nmpt = np.load(S + '/dem/nmpt.npy'); mp = json.load(open(S + '/dem/nmpt.json'))
nmt = np.load(S + '/dem/nmt/nmt.npy'); mt = json.load(open(S + '/dem/nmt/nmt.json'))
root = ET.parse(S + '/m64/osm/airfield.osm').getroot()
nodes = {n.get('id'): (float(n.get('lat')), float(n.get('lon'))) for n in root.findall('node')}
ways = {w.get('id'): w for w in root.findall('way')}
polys = {}
for i in ids:
    w = ways[i]
    polys[i] = [T.transform(nodes[nd.get('ref')][1], nodes[nd.get('ref')][0]) for nd in w.findall('nd')]
for k, v in extra.items():
    polys[k] = v
for k, P in polys.items():
    P = np.array(P)
    path = Path(P)
    e0, n0 = P.min(0) - 10; e1, n1 = P.max(0) + 10
    ins, ring_g = [], []
    E = np.arange(e0, e1, 0.5); N = np.arange(n0, n1, 0.5)
    for e in E:
        for n in N:
            r = int((mp['N1'] - n) / 0.5); c = int((e - mp['E0']) / 0.5)
            if path.contains_point((e, n), radius=-2.0) or path.contains_point((e, n), radius=2.0):
                pass
            inside = path.contains_point((e, n))
            # distance to polygon edges
            d = min(abs((P[j + 1][0] - P[j][0]) * (n - P[j][1]) - (P[j + 1][1] - P[j][1]) * (e - P[j][0])) / max(np.linalg.norm(P[j + 1] - P[j]), 1e-6)
                    if 0 <= np.dot(np.array([e, n]) - P[j], P[j + 1] - P[j]) <= np.dot(P[j + 1] - P[j], P[j + 1] - P[j])
                    else min(np.linalg.norm(np.array([e, n]) - P[j]), np.linalg.norm(np.array([e, n]) - P[j + 1])) for j in range(len(P) - 1))
            if inside and d > 1.0:
                ins.append(float(nmpt[r, c]))
            elif not inside and 3 <= d <= 8:
                rr = int((mt['N1'] - n)); cc = int((e - mt['E0']))
                ring_g.append(float(nmt[rr, cc]))
    g = float(np.nanmedian(ring_g)); a = np.array(ins) - g
    print(k, 'ground', round(g, 2), 'n', len(ins), 'max', round(float(np.nanmax(a)), 2), 'p95', round(float(np.nanpercentile(a, 95)), 2),
          'p50', round(float(np.nanmedian(a)), 2), 'p10', round(float(np.nanpercentile(a, 10)), 2))
