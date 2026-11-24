"""Rut contrast of the SAME ground window (g0..g1 m ahead of base camera) seen from cameras shifted back S m.
usage: rutdist.py <on_prefix> <off_prefix> [light...]   (cameras rf_0..rf_100). Row <-> distance: d = h*f/(y-yh), h=2.5 m (UNVERIFIED), yh=517."""
import sys
from pathlib import Path
import numpy as np
from PIL import Image
F, YH, H = 935.0, 517.0, 2.5
def lum(p):
    a = np.asarray(Image.open(p).convert('RGB'), float); return 0.2126*a[...,0]+0.7152*a[...,1]+0.0722*a[...,2]
def run(onp, offp, lt, g=(15, 35), shifts=(0, 20, 40, 70, 100)):
    res = {}
    for S in shifts:
        a = Path(f'{onp}-{lt}/rf_{S}.png'); b = Path(f'{offp}-{lt}/rf_{S}.png')
        if not (a.exists() and b.exists()): continue
        L1, L0 = lum(a), lum(b)
        rel = np.where(L0 > 4, 1 - L1/np.maximum(L0, 1e-3), 0.0)
        y0 = int(round(YH + F*H/(S+g[1]))); y1 = int(round(YH + F*H/(S+g[0])))
        vals, means, base = [], [], []
        for y in range(y0, max(y1, y0+1)+1):
            nz = np.nonzero(np.abs(L0[y]-L1[y]) > 0.25)[0]
            if len(nz) < 4: continue
            sp = rel[y][nz.min():nz.max()+1]
            vals.append(np.percentile(sp, 95)); means.append(sp.mean())
        res[S] = (y0, y1, 100*np.mean(vals) if vals else None, 100*np.mean(means) if means else None, len(vals))
    return res
if __name__ == '__main__':
    onp, offp = sys.argv[1], sys.argv[2]
    for lt in (sys.argv[3:] or ['clear', 'overcast']):
        print(f'== {onp} {lt}: ground window 15-35 m ahead of base; cam distance = S + ground')
        for S, (y0, y1, pk, mn, n) in run(onp, offp, lt).items():
            print(f'  S={S:3d}  cam dist {S+15:3d}-{S+35:3d} m  rows {y0}-{y1} (n={n})  peak {pk if pk is None else round(pk,1)} %  mean {mn if mn is None else round(mn,1)} %')
