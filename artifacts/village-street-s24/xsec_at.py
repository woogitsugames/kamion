"""Dump the resolved cross-section at a point of a region: section + chain side arrays.
usage: net1.py <region> <E> <N> <R> (cwd = repo root)"""
import sys, time
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path('tools/worldgen').resolve()))
from roads import network as N, standards as S, pipeline as P  # noqa
reg = sys.argv[1]; px, py = float(sys.argv[2]), float(sys.argv[3]); R = float(sys.argv[4])
t = time.time()
w = P.build(reg, collision=False)
print('build s', round(time.time() - t, 1), 'implied', getattr(w.net, 'implied_sidewalk_m', None))
net = w.net
pt = np.array([px, py])
for c in net.chains:
    d = np.hypot(*(c.line.p - pt).T)
    i = int(d.argmin())
    if d[i] > R:
        continue
    sec = net.sec_list[int(c.sec_idx[i])]
    print('---', c.id, 'len', round(c.length, 1), 'd', round(float(d[i]), 1), 'trim', round(c.t_a, 1), round(c.t_b, 1))
    print(' sec', sec.edge_id, sec.highway, sec.cls, 'lanes', sec.lanes, 'lane_w', sec.lane_w, 'edge', sec.edge_strip,
          'width', sec.width, sec.width_src, 'maxspeed', sec.maxspeed, sec.maxspeed_src)
    print(' prov', sec.provenance, 'osm_sidewalk', sec.osm_sidewalk, 'osm_shoulder', sec.osm_shoulder)
    print(' hw here', round(float(c.hw[i]), 3), 'hw min/max', round(float(c.hw.min()), 3), round(float(c.hw.max()), 3))
    print(' meta', {k: v for k, v in c.meta.items() if k not in ('rev',)})
    for sd in ('L', 'R'):
        s = c.side[sd]
        print(' ', sd, 'kind', int(s['kind'][i]), 'walk', bool(s['walk'][i]), 'h', float(s['raw']['h'][i]),
              'w', float(s['raw']['w'][i]), 'mat', int(s['mat'][i]), 'verge', float(s['verge'][i]),
              '| kinds', dict(zip(*np.unique(s['kind'], return_counts=True))), 'walk%', round(float(s['walk'].mean()), 2))
