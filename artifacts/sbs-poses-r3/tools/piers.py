import json, sys, math
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import poselib as P, proj
spec = json.load(open(P.REGION / 'generated/landmarks/viaduct_biezenstwa.spec.json', encoding='utf-8'))
cols = []
for di, d in enumerate(spec['decks']):
    for pi, p in enumerate(d['piers']):
        for ci, c in enumerate(p['cols']):
            cols.append((f'd{di}p{pi}c{ci}', c))
cams = {c['id']: c for c in json.load(open(Path(__file__).parents[1] / sys.argv[1] / 'cameras.json'))['cameras']}
for cid in sys.argv[2:]:
    c = cams[cid]
    out = []
    for name, (e, n, u) in cols:
        (x, y), = proj.project(c, [(e, n, u)], 1280, 960)
        p, f, r, up = proj.basis(c)
        import numpy as np
        if (np.array([e, n, u]) - p) @ f > 0 and -50 < x * 1280 < 1330:
            out.append((round(x * 1280), round(y * 960), name, round(math.dist(c['pos'][:2], (e, n)), 1)))
    print(cid, sorted(out))
