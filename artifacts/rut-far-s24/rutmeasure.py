"""Rut contrast vs. distance from final pixels: rel = 1 - lum(on)/lum(off) inside the road span of each row.
usage: rutmeasure.py <on_dir_prefix> <off_dir_prefix>   e.g. vqa/before vqa/before-off  (appends -clear/-overcast)"""
import sys
from pathlib import Path
import numpy as np
from PIL import Image

def lum(p):
    a = np.asarray(Image.open(p).convert('RGB'), float)
    return 0.2126*a[...,0]+0.7152*a[...,1]+0.0722*a[...,2]

def measure(on, off, horizon=520, cam_h=2.5, f=935.0, bands=((900,1080),(760,900),(660,760),(600,660),(565,600),(545,565))):
    L1, L0 = lum(on), lum(off)
    rel = np.where(L0 > 4, 1.0 - L1/np.maximum(L0, 1e-3), 0.0)
    out = []
    for y0, y1 in bands:
        vals = []; means = []
        for y in range(y0, y1):
            r = rel[y]; nz = np.nonzero(np.abs(L0[y]-L1[y]) > 0.25)[0]
            if len(nz) < 4: continue
            span = r[nz.min():nz.max()+1]
            vals.append(np.percentile(span, 95)); means.append(span.mean())
        if not vals: out.append((y0, y1, None)); continue
        ym = (y0+y1)/2; d = cam_h*f/max(ym-horizon, 1)
        out.append((y0, y1, round(d), 100*float(np.mean(vals)), 100*float(np.mean(means))))
    return out

if __name__ == '__main__':
    onp, offp = sys.argv[1], sys.argv[2]
    for lt in ('clear', 'overcast'):
        for cam in ('q_far', 'q_far2'):
            a = Path(f'{onp}-{lt}/{cam}.png'); b = Path(f'{offp}-{lt}/{cam}.png')
            if not (a.exists() and b.exists()): print('skip', lt, cam); continue
            print(f'== {onp} {lt} {cam}: rows | dist~m (h=2.5, UNVERIFIED) | peak rut darkening p95 % | mean in road span %')
            for r in measure(a, b):
                print('  ', r if r[2] is None else f'{r[0]}-{r[1]}  {r[2]:4d} m  peak {r[3]:5.1f}  mean {r[4]:5.1f}')
