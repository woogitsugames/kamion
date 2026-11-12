"""Bounded source-mesh diagnosis, run under the round's heavy slot."""
import hashlib
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).parent
sys.path.insert(0, str(ROOT / 'tools/worldgen'))
from streetscape import life_props as current
from streetscape.export import crease_normals

snapshot = OUT / 'baseline-life_props.py'
proof = json.loads((OUT / 'before-inputs.json').read_text(encoding='utf-8-sig'))
expected = proof['source_sha']['tools/worldgen/streetscape/life_props.py'].lower()
assert hashlib.sha256(snapshot.read_bytes()).hexdigest() == expected
spec = importlib.util.spec_from_file_location('streetscape._life4baseline', snapshot)
baseline = importlib.util.module_from_spec(spec)
spec.loader.exec_module(baseline)


def parts(module, r, w, n, side):
    mesh = module.Mesh()
    module.wheel(mesh, [0, 0, r], r, w, n, out_sign=side)
    return {p['mat']: p for p in crease_normals(mesh.out())}


def rows(p, mirror=False, backing=False, r=0, w=0):
    v, normal = p['V'], p['N']
    if backing:
        side = -1 if v[:, 0].mean() < 0 else 1
        depth = side * v[:, 0] - w / 2
        radial = np.linalg.norm(v[:, [1, 2]] - [0, r], axis=1)
        mask = (depth < -0.035) & (depth > -0.12) & (radial < r * .62)
        v, normal = v[mask], normal[mask]
    data = np.concatenate([v, normal], axis=1)
    if mirror:
        data *= [-1, 1, 1, -1, 1, 1]
    return Counter(map(tuple, np.round(data, 5)))


result = []
for r, w, n in ((.535, .385, 10), (.51, .32, 14), (.51, .62, 14)):
    row = dict(radius=r, width=w, segments=n)
    for label, module in (('baseline', baseline), ('candidate', current)):
        plus, minus = parts(module, r, w, n, 1), parts(module, r, w, n, -1)
        for mat in ('rim', 'tyre'):
            a, b = rows(plus[mat], True), rows(minus[mat])
            row[f'{label}_{mat}_mirror_mismatches'] = sum((a-b).values()) + sum((b-a).values())
        if label == 'candidate':
            a = rows(plus['tyre'], True, True, r, w)
            b = rows(minus['tyre'], False, True, r, w)
            row['candidate_backing_mirror_mismatches'] = sum((a-b).values()) + sum((b-a).values())
    result.append(row)
report = dict(baseline_sha=expected, cases=result,
              note='Exact frozen baseline source versus current, post-crease vertex/normal multisets at 1e-5. This diagnoses legacy tread asymmetry; it does not relax the near-rim invariant.')
(OUT / 'mirror-diagnosis.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
print(json.dumps(report, indent=2))
