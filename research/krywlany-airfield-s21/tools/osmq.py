"""List OSM ways/nodes with selected tags from an .osm file; compute centroid, length, bbox dims (m)."""
import sys, math, xml.etree.ElementTree as ET

f = sys.argv[1]
keys = sys.argv[2].split(',')
root = ET.parse(f).getroot()
nodes = {}
for n in root.findall('node'):
    nodes[n.get('id')] = (float(n.get('lat')), float(n.get('lon')))


def tags(e):
    return {t.get('k'): t.get('v') for t in e.findall('tag')}


def m(a, b):
    lat0 = math.radians((a[0] + b[0]) / 2)
    dx = (b[1] - a[1]) * 111320 * math.cos(lat0)
    dy = (b[0] - a[0]) * 110540
    return math.hypot(dx, dy)


for n in root.findall('node'):
    t = tags(n)
    if any(k in t for k in keys):
        print('node', n.get('id'), f"{float(n.get('lat')):.6f},{float(n.get('lon')):.6f}", t)
for w in root.findall('way'):
    t = tags(w)
    if any(k in t for k in keys):
        pts = [nodes[nd.get('ref')] for nd in w.findall('nd') if nd.get('ref') in nodes]
        if not pts:
            continue
        L = sum(m(pts[i], pts[i + 1]) for i in range(len(pts) - 1))
        la = sum(p[0] for p in pts) / len(pts)
        lo = sum(p[1] for p in pts) / len(pts)
        segs = [round(m(pts[i], pts[i + 1]), 1) for i in range(len(pts) - 1)]
        print('way', w.get('id'), f'{la:.6f},{lo:.6f}', f'L={L:.0f}m', 'segs=' + str(segs[:8]), t)
for r in root.findall('relation'):
    t = tags(r)
    if any(k in t for k in keys):
        print('rel', r.get('id'), t)
