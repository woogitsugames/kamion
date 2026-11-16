"""ADR 0203: carriageway width at trunk / trunk_link edge midpoints: orthophoto (grey asphalt run across the axis)
vs generated world (road_asphalt + markings run across the axis). Median of 7 profiles 6 m apart. Width in m."""
import json, sys, colorsys, numpy as np, rasterio
from PIL import Image
sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parents[1])); sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parent))
import junction_topview as jt
from roads import pipeline
R = __import__('os').environ.get('REGION', 'bialystok-maczka')
g = json.load(open(f'Data/Regions/{R}/roads.graph.json', encoding='utf-8'))
reg = pipeline.load_region(R); ox, oy = reg['origin']['x'], reg['origin']['y']
o = rasterio.open(json.load(open(f'Data/Regions/{R}/ortho.json'))['file']); A = o.read(); T = o.transform
world = jt.load_world(R)
ROAD = {(62, 62, 66), (245, 245, 245)}
def frame(e):
    P = np.array(e['geometry']); s = np.r_[0, np.cumsum(np.hypot(*np.diff(P, axis=0).T))]
    f = lambda q: np.array([np.interp(q, s, P[:, 0]), np.interp(q, s, P[:, 1])])
    return f, s[-1]
def run(mask):            # contiguous True run through the centre, gaps <= 3 samples (0.75 m) bridged
    n = len(mask); c = n // 2
    if not mask[c - 2:c + 3].any(): return 0.0
    def ext(step):
        i, gap, last = c, 0, c
        while 0 <= i + step < n:
            i += step
            if mask[i]: last, gap = i, 0
            else:
                gap += 1
                if gap > 3: break
        return last
    return (ext(1) - ext(-1) + 1) * 0.25
rows = []
for e in g['edges']:
    a = e['attrs']
    if a['highway']['v'] not in ('trunk', 'trunk_link') or e['length_m'] < 35: continue
    f, L = frame(e); wo, wg = [], []
    for q in np.linspace(max(L / 2 - 18, 3), min(L / 2 + 18, L - 3), 7):
        p = f(q); t = f(min(q + 1, L)) - f(max(q - 1, 0)); t /= np.hypot(*t); nrm = np.array([-t[1], t[0]])
        d = np.arange(-15, 15.01, 0.25); pts = p[None] + d[:, None] * nrm[None]
        col = ((pts[:, 0] - T.c) / T.a).astype(int); row = ((pts[:, 1] - T.f) / T.e).astype(int)
        ok = (col >= 0) & (col < A.shape[2]) & (row >= 0) & (row < A.shape[1])
        if not ok.all(): continue
        rgb = A[:3, row, col].T / 255.0
        mx, mn = rgb.max(1), rgb.min(1); sat = (mx - mn) / np.maximum(mx, 1e-6)
        wo.append(run(((sat < 0.16) & (mx > 0.22) & (mx < 0.72)) | ((sat < 0.10) & (mx >= 0.72))))
        img, _ = jt.topview(world, p[0] - ox, p[1] - oy, 32.0, 128)
        px = np.array(img)
        gm = []
        for dd in d:
            x = (dd * nrm[0] + 16) * 4; y = (16 - dd * nrm[1]) * 4
            gm.append(tuple(px[int(np.clip(y, 0, 127)), int(np.clip(x, 0, 127))]) in ROAD)
        wg.append(run(np.array(gm)))
    if wo:
        m = f(L / 2)
        rows.append(dict(way=e['osm_way'], hw=a['highway']['v'], lanes=a['lanes']['v'], x=round(m[0]), y=round(m[1]), L=round(e['length_m']),
                         ortho_m=round(float(np.median(wo)), 2), gen_m=round(float(np.median(wg)), 2)))
rows.sort(key=lambda r: -r['x'])
json.dump(rows, open(sys.argv[1], 'w'), indent=1)
for r in rows: print(r['hw'][:10].ljust(10), r['way'], 'lanes', r['lanes'], 'x', r['x'], 'y', r['y'], 'ortho', r['ortho_m'], 'gen', r['gen_m'], 'diff', round(r['gen_m'] - r['ortho_m'], 2))
