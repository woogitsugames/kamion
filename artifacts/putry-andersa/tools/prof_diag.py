"""Profiles of the two Andersa / DK8 viaduct chains (ADR 0146): generator z vs NMT on the axis. Runs the road
pipeline up to build_profiles (no meshing). Usage: uv run --project tools/worldgen python artifacts/putry-andersa/tools/prof_diag.py [out.json]"""
import sys, json
from pathlib import Path
REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / 'tools/worldgen'))
import numpy as np
from roads import pipeline as PL, profile as P, meshing as M

class Stop(Exception):
    pass
def _stop(*a, **k):
    raise Stop()
real = P.mark_walled_ramps
box = {}
def grab(net, hf):
    box['net'], box['hf'] = net, hf
    box['walled'] = real(net, hf)
    box['fills'] = M.build_median_fills(M.MeshBuf(), net)
    raise Stop()
P.mark_walled_ramps = grab
try:
    PL.build('bialystok-industrial-c')
except Stop:
    pass
net, hf = box['net'], box['hf']
out = {}
for c in net.chains:
    if any(k in c.id for k in ('w1101181473', 'w173956078', 'w284022563', 'w606396460', 'w606396463', 'w173956083', 'w268473388')):
        s = c.line.s
        zn = hf.sample(c.line.p[:, 0], c.line.p[:, 1])
        wl = c.meta.get('walled')
        rows = []
        for i in range(0, len(s), max(1, int(10 / (s[1] - s[0])))):
            rows.append([round(float(s[i]), 1), round(float(c.line.p[i, 0]), 1), round(float(c.line.p[i, 1]), 1),
                         round(float(c.z[i]), 2), round(float(zn[i]), 2), int(bool(c.bridge[i])), int(bool(wl[i])) if wl is not None else 0])
        out[c.id] = rows
        print(c.id, 'len', round(c.length, 1), 'nodes', c.node_a, c.node_b)
        for r in rows:
            print('  ', r)
print('median_fills', box['fills'])
if len(sys.argv) > 1:
    Path(sys.argv[1]).write_text(json.dumps({'cols': ['s', 'E', 'N', 'z', 'nmt_axis', 'bridge', 'walled'], 'chains': out, 'walled_ramps': box['walled'], 'median_fills': box['fills']}, indent=0))
