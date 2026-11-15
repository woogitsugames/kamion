"""nDSM (NMPT 2023 0.5 m - NMT 1 m) roof levels for plant A and B.
1) components of nDSM>4 m in window, then split each component into height classes (1 m bins) via 2nd-level components;
2) report per level: median height, area, bbox E/N, roof z.
Also: profile along given lines."""
import sys, json, math
import numpy as np
from collections import deque
S = sys.argv[1]
mp = json.load(open(S + '/dem/nmpt_m63.json')); P = np.load(S + '/dem/nmpt_m63.npy')
mt = json.load(open(S + '/dem/nmt63/nmt.json')); Tm = np.load(S + '/dem/nmt63/nmt.npy')
H, W = P.shape
# upsample NMT to 0.5 m grid
rr = np.clip(np.floor(mt['N1'] - (mp['N1'] - np.arange(H) * 0.5 - 0.25)).astype(int), 0, Tm.shape[0] - 1)
cc = np.clip(np.floor(mp['E0'] + np.arange(W) * 0.5 + 0.25 - mt['E0']).astype(int), 0, Tm.shape[1] - 1)
G = Tm[np.ix_(rr, cc)]
N = P - G


def win(e0, e1, n0, n1):
    c0 = int((e0 - mp['E0']) / 0.5); c1 = int((e1 - mp['E0']) / 0.5)
    r0 = int((mp['N1'] - n1) / 0.5); r1 = int((mp['N1'] - n0) / 0.5)
    return r0, r1, c0, c1


def comps(mask):
    lab = np.zeros(mask.shape, int); k = 0; out = []
    for i in range(mask.shape[0]):
        for j in range(mask.shape[1]):
            if mask[i, j] and not lab[i, j]:
                k += 1; q = deque([(i, j)]); lab[i, j] = k; cells = []
                while q:
                    a, b = q.popleft(); cells.append((a, b))
                    for da, db in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        x, y = a + da, b + db
                        if 0 <= x < mask.shape[0] and 0 <= y < mask.shape[1] and mask[x, y] and not lab[x, y]:
                            lab[x, y] = k; q.append((x, y))
                out.append(cells)
    return out


name, e0, e1, n0, n1 = sys.argv[2], *map(float, sys.argv[3:7])
r0, r1, c0, c1 = win(e0, e1, n0, n1)
sub = N[r0:r1, c0:c1]; subP = P[r0:r1, c0:c1]
binw = float(sys.argv[7]) if len(sys.argv) > 7 else 1.5
levels = np.floor(np.nan_to_num(sub, nan=0) / binw)
mask = sub > 4
res = []
for k in np.unique(levels[mask]):
    m = mask & (levels == k)
    for cells in comps(m):
        if len(cells) < 400:  # < 100 m2
            continue
        a = np.array(cells)
        vals = sub[a[:, 0], a[:, 1]]; z = subP[a[:, 0], a[:, 1]]
        E = mp['E0'] + (c0 + a[:, 1]) * 0.5; Nn = mp['N1'] - (r0 + a[:, 0]) * 0.5
        res.append((float(np.median(vals)), len(cells) * 0.25, float(np.median(z)), E.min(), E.max(), Nn.min(), Nn.max()))
res.sort(key=lambda x: -x[1])
print(name, 'nan share', float(np.isnan(sub).mean()))
for h, A, z, ea, eb, na, nb in res[:14]:
    print(f'  H={h:5.2f} m  A={A:7.0f} m2  roof={z:7.2f}  E[{ea:.0f};{eb:.0f}] N[{na:.0f};{nb:.0f}]')
np.save(S + f'/m63/ndsm_{name}.npy', sub)
json.dump({'E0': e0, 'N1': n1, 'cell': 0.5}, open(S + f'/m63/ndsm_{name}.json', 'w'))
