"""ADR 0206: painted-line profile across a trunk edge on the orthophoto. Brightness along the normal (-15..+15 m, 0.1 m)
averaged over 12 m of the edge; peaks = solid (edge) lines and dashed lane lines. Prints peak offsets (m, + = left of
travel direction) and their strength (solid ~ high, dashed ~ half). usage: line_profile.py way [way ...]"""
import json, sys, numpy as np, rasterio
from scipy.ndimage import map_coordinates
R = 'bialystok-kleeberga'
g = json.load(open(f'Data/Regions/{R}/roads.graph.json', encoding='utf-8'))
o = rasterio.open(json.load(open(f'Data/Regions/{R}/ortho.json'))['file']); A = o.read().astype(float); T = o.transform
L = A.mean(0)
for w in map(int, sys.argv[1:]):
    for e in [e for e in g['edges'] if e['osm_way'] == w]:
        P = np.array(e['geometry']); s = np.r_[0, np.cumsum(np.hypot(*np.diff(P, axis=0).T))]
        f = lambda q: np.array([np.interp(q, s, P[:, 0]), np.interp(q, s, P[:, 1])])
        d = np.arange(-15, 15.001, 0.1); prof = np.zeros_like(d); n = 0
        for q in np.linspace(max(s[-1] / 2 - 6, 1), min(s[-1] / 2 + 6, s[-1] - 1), 25):
            p = f(q); t = f(min(q + 1, s[-1])) - f(max(q - 1, 0)); t /= np.hypot(*t); nrm = np.array([-t[1], t[0]])
            pts = p[None] + d[:, None] * nrm[None]
            col = (pts[:, 0] - T.c) / T.a - 0.5; row = (pts[:, 1] - T.f) / T.e - 0.5
            prof += map_coordinates(L, [row, col], order=1, mode='nearest'); n += 1
        prof /= n; base = np.median(prof)
        pk = [i for i in range(2, len(d) - 2) if prof[i] == prof[i - 2:i + 3].max() and prof[i] - base > 12]
        m = f(s[-1] / 2)
        print(w, e['attrs']['highway']['v'], 'L', e['attrs']['lanes']['v'], f'@{m[0]:.0f},{m[1]:.0f}', 'base', round(base),
              ' '.join(f"{d[i]:+.1f}({prof[i]-base:.0f})" for i in pk))
