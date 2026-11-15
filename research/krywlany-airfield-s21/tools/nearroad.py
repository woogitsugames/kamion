"""Nearest OSM road way (highway with name, any class incl. cycleway/footway reported separately) for camera points."""
import sys, math, json, xml.etree.ElementTree as ET
from pyproj import Transformer
T = Transformer.from_crs(4326, 2180, always_xy=True)
root = ET.parse(sys.argv[1]).getroot()
nodes = {n.get('id'): T.transform(float(n.get('lon')), float(n.get('lat'))) for n in root.findall('node')}
ways = []
for w in root.findall('way'):
    t = {x.get('k'): x.get('v') for x in w.findall('tag')}
    if 'highway' in t:
        ways.append((w.get('id'), t.get('highway'), t.get('name', ''), [nodes[x.get('ref')] for x in w.findall('nd') if x.get('ref') in nodes]))


def dist(p, pts):
    best = 1e9
    for a, b in zip(pts, pts[1:]):
        dx, dy = b[0] - a[0], b[1] - a[1]
        L2 = dx * dx + dy * dy or 1e-9
        t = max(0, min(1, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / L2))
        best = min(best, math.hypot(a[0] + t * dx - p[0], a[1] + t * dy - p[1]))
    return best


for arg in sys.argv[2:]:
    name, lat, lon = arg.split(':')
    p = T.transform(float(lon), float(lat))
    road = min(((dist(p, w[3]), w) for w in ways if w[1] in ('trunk', 'primary', 'secondary', 'tertiary', 'residential', 'unclassified')), key=lambda x: x[0])
    anyw = min(((dist(p, w[3]), w) for w in ways), key=lambda x: x[0])
    print(name, f'road way {road[1][0]} ({road[1][2]}, {road[1][1]}) {road[0]:.1f} m', '|', f'any way {anyw[1][0]} ({anyw[1][1]} {anyw[1][2]}) {anyw[0]:.1f} m')
