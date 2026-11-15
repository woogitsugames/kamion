"""Features inside / near aerodrome polygon (way 234838628)."""
import sys, math, xml.etree.ElementTree as ET
root = ET.parse(sys.argv[1]).getroot()
AERO = sys.argv[2] if len(sys.argv) > 2 else '234838628'
nodes = {n.get('id'): (float(n.get('lat')), float(n.get('lon'))) for n in root.findall('node')}
ways = {w.get('id'): w for w in root.findall('way')}


def tags(e):
    return {t.get('k'): t.get('v') for t in e.findall('tag')}


def pts(w):
    return [nodes[nd.get('ref')] for nd in w.findall('nd') if nd.get('ref') in nodes]


poly = pts(ways[AERO])


def inside(p, poly):
    x, y = p[1], p[0]
    c = False
    for i in range(len(poly)):
        a, b = poly[i], poly[i - 1]
        if (a[0] > y) != (b[0] > y):
            xi = a[1] + (y - a[0]) * (b[1] - a[1]) / (b[0] - a[0])
            if x < xi:
                c = not c
    return c


def dist_m(a, b):
    lat0 = math.radians(a[0])
    return math.hypot((b[1] - a[1]) * 111320 * math.cos(lat0), (b[0] - a[0]) * 110540)


def area(ps):
    lat0 = math.radians(ps[0][0])
    xy = [((p[1]) * 111320 * math.cos(lat0), p[0] * 110540) for p in ps]
    return abs(sum(xy[i][0] * xy[i - 1][1] - xy[i - 1][0] * xy[i][1] for i in range(len(xy)))) / 2


for wid, w in ways.items():
    t = tags(w)
    p = pts(w)
    if not p or wid == AERO:
        continue
    c = (sum(q[0] for q in p) / len(p), sum(q[1] for q in p) / len(p))
    ins = inside(c, poly)
    near = min(dist_m(c, q) for q in poly)
    if 'building' in t and (ins or near < 40):
        segs = [round(dist_m(p[i], p[i + 1]), 1) for i in range(len(p) - 1)]
        print('BLD', wid, f'{c[0]:.6f},{c[1]:.6f}', 'in' if ins else f'out{near:.0f}m', f'A={area(p):.0f}', segs[:6], t)
    if t.get('barrier') in ('gate', 'fence', 'wall') and (ins or near < 60):
        L = sum(dist_m(p[i], p[i + 1]) for i in range(len(p) - 1))
        print('BAR', wid, f'{c[0]:.6f},{c[1]:.6f}', f'L={L:.0f}', t)
    if t.get('amenity') == 'parking' and (ins or near < 80):
        print('PARK', wid, f'{c[0]:.6f},{c[1]:.6f}', f'A={area(p):.0f}', t)
    if t.get('highway') == 'service' and (ins or near < 30):
        print('SERV', wid, f'{c[0]:.6f},{c[1]:.6f}', t)
for n in root.findall('node'):
    t = tags(n)
    if t.get('barrier') in ('gate', 'lift_gate', 'swing_gate', 'sliding_gate') or t.get('aeroway') or t.get('man_made') in ('mast', 'tower'):
        p = nodes[n.get('id')]
        near = min(dist_m(p, q) for q in poly)
        if inside(p, poly) or near < 40:
            print('NODE', n.get('id'), f'{p[0]:.6f},{p[1]:.6f}', f'{near:.0f}m', t)
