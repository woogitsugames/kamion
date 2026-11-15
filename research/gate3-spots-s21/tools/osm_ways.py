"""Print endpoints/nodes of given ways and circle fit. Usage: osm_ways.py file.xml id1,id2 [fit]"""
import sys, os, math, xml.etree.ElementTree as ET
sys.path.insert(0, os.path.dirname(__file__))
from geo import near, dist
root = ET.parse(sys.argv[1]).getroot()
nodes = {n.get('id'): (float(n.get('lat')), float(n.get('lon'))) for n in root.iter('node')}
ids = sys.argv[2].split(',')
allpts = []
for w in root.iter('way'):
    if w.get('id') not in ids:
        continue
    t = {c.get('k'): c.get('v') for c in w.findall('tag')}
    nds = [c.get('ref') for c in w.findall('nd')]
    pts = [nodes[i] for i in nds if i in nodes]
    allpts += pts
    L = sum(dist(a, b)[0] for a, b in zip(pts, pts[1:]))
    print('way', w.get('id'), 'n', len(pts), f'L={L:.1f}', 'start', pts[0], 'end', pts[-1], 'bearing', round(dist(pts[0], pts[-1])[1]), {k: v for k, v in t.items() if k in ('highway', 'name', 'barrier', 'wall', 'layer', 'bridge', 'embankment', 'height', 'lanes', 'oneway', 'destination', 'junction')})
    if len(sys.argv) > 4:
        for p in pts:
            print('   ', p, near(*p))
if len(sys.argv) > 3 and sys.argv[3] == 'fit':
    la0 = sum(p[0] for p in allpts) / len(allpts); lo0 = sum(p[1] for p in allpts) / len(allpts)
    xy = [((p[1] - lo0) * math.cos(math.radians(la0)) * 111320, (p[0] - la0) * 110574) for p in allpts]
    # algebraic circle fit (Kasa)
    n = len(xy); sx = sum(x for x, y in xy); sy = sum(y for x, y in xy)
    sxx = sum(x * x for x, y in xy); syy = sum(y * y for x, y in xy); sxy = sum(x * y for x, y in xy)
    sxz = sum(x * (x * x + y * y) for x, y in xy); syz = sum(y * (x * x + y * y) for x, y in xy); sz = sum(x * x + y * y for x, y in xy)
    import itertools
    A = [[sxx, sxy, sx], [sxy, syy, sy], [sx, sy, n]]; B = [sxz, syz, sz]
    def det(m):
        return (m[0][0] * (m[1][1] * m[2][2] - m[1][2] * m[2][1]) - m[0][1] * (m[1][0] * m[2][2] - m[1][2] * m[2][0]) + m[0][2] * (m[1][0] * m[2][1] - m[1][1] * m[2][0]))
    D = det(A); sol = []
    for i in range(3):
        M = [row[:] for row in A]
        for r in range(3):
            M[r][i] = B[r]
        sol.append(det(M) / D)
    a, b, c = sol
    cx, cy = a / 2, b / 2; r = math.sqrt(c + cx * cx + cy * cy)
    lat = la0 + cy / 110574; lon = lo0 + cx / (math.cos(math.radians(la0)) * 111320)
    res = [abs(math.hypot(x - cx, y - cy) - r) for x, y in xy]
    print(f'circle centre {lat:.6f},{lon:.6f} r={r:.1f} m (diam {2*r:.1f}) n={n} max_resid={max(res):.1f} m')
