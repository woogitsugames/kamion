"""Rut contrast of the SAME ground slices (g m ahead of the base camera rg_0) seen from cameras rg_S (S m behind it).
usage: rutdist.py <on_prefix> <off_prefix> [light...]
Row <-> distance: d = h*f/(y-yh), h = 2.0 m (fitted: best along-road alignment of the rut profile between rg_0, rg_20, rg_40; corr 0.89), yh = 517 px, f = 935 px (60 deg vertical fov, 1080 px)."""
import sys
from pathlib import Path
import numpy as np
from PIL import Image
F, YH, H = 935.0, 517.0, 2.0
SLICES = ((15, 25), (25, 40), (40, 60))
SHIFTS = (0, 20, 40, 70, 100)
def lum(p):
    a = np.asarray(Image.open(p).convert('RGB'), float); return 0.2126*a[...,0]+0.7152*a[...,1]+0.0722*a[...,2]
def cell(L1, L0, S, g):
    rel = np.where(L0 > 4, 1 - L1/np.maximum(L0, 1e-3), 0.0)
    ya = YH + F*H/(S+g[1]); yb = YH + F*H/(S+g[0])
    rows = range(int(np.floor(ya)), int(np.ceil(yb)))
    vals, means = [], []
    for y in rows:
        nz = np.nonzero(np.abs(L0[y]-L1[y]) > 0.25)[0]
        if len(nz) < 4: continue
        sp = rel[y][nz.min():nz.max()+1]; vals.append(np.percentile(sp, 95)); means.append(sp.mean())
    return (100*np.mean(vals), 100*np.mean(means), len(vals)) if vals else None
def table(onp, offp, lt):
    imgs = {S: (lum(f'{onp}-{lt}/rg_{S}.png'), lum(f'{offp}-{lt}/rg_{S}.png')) for S in SHIFTS if Path(f'{onp}-{lt}/rg_{S}.png').exists() and Path(f'{offp}-{lt}/rg_{S}.png').exists()}
    out = {}
    for g in SLICES:
        for S, (a, b) in imgs.items(): out[(g, S)] = cell(a, b, S, g)
    return imgs.keys(), out
if __name__ == '__main__':
    onp, offp = sys.argv[1], sys.argv[2]
    for lt in (sys.argv[3:] or ['clear', 'overcast']):
        Ss, out = table(onp, offp, lt)
        print(f'== {onp} {lt}: peak (p95 of relative rut darkening, %) / mean %, same ground slice, camera S m farther back (rows n)')
        for g in SLICES:
            print(f'  ground {g[0]}-{g[1]} m: ' + ' | '.join(f'S={S}({S+g[0]}-{S+g[1]}m): ' + ('-' if out[(g,S)] is None else f'{out[(g,S)][0]:.1f}/{out[(g,S)][1]:.1f} n{out[(g,S)][2]}') for S in Ss))
