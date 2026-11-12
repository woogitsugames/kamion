"""ADR 0143: resect 482392 (and check 320326) on viaduct_biezenstwa pier columns (spec pier_lines), photo x of the
columns at ~2 m above the ground (rectified 1280x960, hfov 90). Unknowns E, N, heading; eye/pitch fixed."""
import json, math, sys
import numpy as np
from scipy.optimize import least_squares
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
spec = json.load(open(ROOT / 'Data/Regions/bialystok-industrial-c/generated/landmarks/viaduct_biezenstwa.spec.json', encoding='utf-8'))
C = {}
for di, d in enumerate(spec['decks']):
    for pi, p in enumerate(d['piers']):
        for ci, c in enumerate(p['cols']):
            C[f'd{di}p{pi}c{ci}'] = np.array(c) + [0, 0, 2.0]
F = 640.0
def proj(x, pts, u, pitch):
    e, n, h = x
    hh, pp = math.radians(h), math.radians(pitch)
    f = np.array([math.sin(hh) * math.cos(pp), math.cos(hh) * math.cos(pp), math.sin(pp)])
    r = np.array([math.cos(hh), -math.sin(hh), 0]); up = np.cross(r, f)
    d = pts - [e, n, u]
    return 640 + F * (d @ r) / (d @ f)
def solve(obs, x0, u, pitch):
    names = list(obs); pts = np.array([C[k] for k in names]); px = np.array([obs[k] for k in names])
    sol = least_squares(lambda x: proj(x, pts, u, pitch) - px, x0)
    return sol.x, sol.fun
pitch = math.degrees(math.atan((2 * 0.75 - 1) * 0.75))
obs482 = {'d0p1c0': 607, 'd0p1c1': 675, 'd1p5c1': 828, 'd1p5c0': 960, 'd1p6c1': 1050, 'd1p6c0': 1145}
x, r = solve(obs482, [531.5, -685.0, 246.1], 139.64 + 0.9, pitch)
print('482392 E N heading', np.round(x, 3), 'resid px', np.round(r, 1))
for k in (0.0,):
    pass
