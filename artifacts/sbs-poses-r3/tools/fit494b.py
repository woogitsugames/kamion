"""ADR 0143 variant: same as fit494 but with a free common fork-height offset dz (lamp height in the world is a
photo-scaled WORKING_VALUE and base level console vs ground is uncertain) -> the fit uses lamp x, the 1/d ladder of y and the dash."""
import numpy as np, math
from scipy.optimize import least_squares
import fit494 as M

def res(x):
    s, lat, eye, h, p, r, dz = x
    cam = M.ground(s, lat); cam[2] += eye
    _, u = M.axis(s)
    L = M.lamps.copy(); L[:, 2] += dz
    pa, za = M.project(cam, L, h, p, r)
    ok = (za > 3) & (pa[:, 0] > -40) & (pa[:, 0] < 1320) & (pa[:, 1] > 0)
    ahead = L[ok][np.argsort(za[ok])][:5]
    pl, _ = M.project(cam, ahead, h, p, r)
    if len(pl) < 5: return np.full(15, 300.0)
    out = list((pl - M.PH_L[:len(pl)]).ravel())
    line = np.array([M.ground(s + t, 0) for t in np.linspace(3, 120, 400)])
    pd, z = M.project(cam, line, h, p, r); pd = pd[z > 0]
    out += [np.min(np.linalg.norm(pd - q, axis=1)) for q in M.PH_D]
    # road VP of the near dash (tangent) at photo (441, 687)
    f, rt, up = M.rot(h, p, r); _, uu = M.axis(s); d = np.array([uu[0], uu[1], 0.0181])
    vp = np.array([640 + M.F * (d @ rt) / (d @ f), 480 - M.F * (d @ up) / (d @ f)])
    out += list((vp - [441, 687]) * 2)
    return np.array(out)

rows = []
for s0 in range(-60, 31, 5):
    lo = [-80, -3, 0.9, 290, 0, -8, -12]; hi = [40, 3.5, 2.0, 330, 15, 8, 6]
    sol = least_squares(res, [s0, 1.1, 1.3, 314, 7, 0, -4], bounds=(lo, hi))
    rows.append((sol.cost, sol))
rows.sort(key=lambda t: t[0])
seen = set()
for c, sol in rows:
    k = round(sol.x[0])
    if k in seen: continue
    seen.add(k)
    x = sol.x; cam = M.ground(x[0], x[1])
    print('s %.1f lat %.2f eye %.2f head %.2f pitch %.2f roll %.2f dz %.2f | rms %.1f | E %.2f N %.2f' % (*x, math.sqrt(np.mean(sol.fun ** 2)), cam[0], cam[1]))
    if len(seen) > 6: break
best = rows[0][1]; print('residuals best', np.round(best.fun, 1))
