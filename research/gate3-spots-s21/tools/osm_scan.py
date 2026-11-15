"""Scan OSM XML for features relevant to G3 points. Usage: osm_scan.py file.xml"""
import sys, os, math, xml.etree.ElementTree as ET
sys.path.insert(0, os.path.dirname(__file__))
from geo import near, dist

root = ET.parse(sys.argv[1]).getroot()
nodes = {}
ntags = {}
for n in root.iter('node'):
    nodes[n.get('id')] = (float(n.get('lat')), float(n.get('lon')))
    t = {c.get('k'): c.get('v') for c in n.findall('tag')}
    if t:
        ntags[n.get('id')] = t

KEYS = ('barrier', 'bridge', 'junction', 'man_made', 'wall', 'traffic_sign', 'landuse', 'leisure', 'natural',
        'highway', 'area:highway', 'embankment', 'retaining_wall', 'tourism', 'artwork_type', 'historic', 'memorial', 'layer')


def length(nds):
    L = 0
    for a, b in zip(nds, nds[1:]):
        if a in nodes and b in nodes:
            L += dist(nodes[a], nodes[b])[0]
    return L


mode = sys.argv[2] if len(sys.argv) > 2 else 'ways'
for w in root.iter('way'):
    t = {c.get('k'): c.get('v') for c in w.findall('tag')}
    nds = [c.get('ref') for c in w.findall('nd')]
    if not t:
        continue
    interesting = any(k in t for k in ('barrier', 'bridge', 'junction', 'man_made', 'wall', 'landuse', 'leisure', 'natural',
                                      'area:highway', 'embankment', 'tourism', 'historic', 'memorial', 'area'))
    hw = t.get('highway')
    if hw in ('footway', 'cycleway', 'path', 'pedestrian') or (hw and mode == 'all'):
        interesting = True
    if not interesting:
        continue
    pts = [nodes[i] for i in nds if i in nodes]
    if not pts:
        continue
    c = (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts))
    closed = nds[0] == nds[-1]
    print('way', w.get('id'), f'L={length(nds):.1f}m', 'closed' if closed else '', f'c={c[0]:.6f},{c[1]:.6f}', near(*c), t)
for nid, t in ntags.items():
    if any(k in t for k in ('traffic_sign', 'man_made', 'tourism', 'historic', 'memorial', 'artwork_type', 'barrier', 'highway')):
        if t.get('highway') in ('crossing', 'traffic_signals', 'street_lamp', 'give_way', 'stop', 'bus_stop', 'turning_circle'):
            continue
        print('node', nid, nodes[nid], near(*nodes[nid]), t)
