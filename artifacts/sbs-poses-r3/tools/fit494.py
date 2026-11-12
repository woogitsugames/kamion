"""ADR 0143: resect 494288 (Putry deck, NW-bound) with roll: unknowns s (m along from A1), lat (m right of the dash),
eye, heading, pitch, roll. Observations on the rectified photo 1280x960 (hfov 41.82): 5 median lamp forks
(instances lamp_double*, base z + 10.9 m) and 3 points on the lane dash (graph centreline, deck surface)."""
import json, glob, math, sys
import numpy as np
from scipy.optimize import least_squares
ROOT = __import__('pathlib').Path(__file__).resolve().parents[3]
A0, A1, A2 = np.array((-458.0, -56.0)), np.array((-512.1, -11.7)), np.array((-542.1, 10.9))
F = 640 / math.tan(math.radians(41.8226 / 2))
PH_L = np.array([(222, 455), (228, 557), (186, 611), (124, 630), (58, 655)], float)
PH_D = np.array([(280, 880), (360, 790), (397, 740)], float)
PH_E = np.array([(955, 880), (745, 800)], float)  # right edge line (rough)
U = lambda s: 139.815 + 0.0181 * s
lamps = []
for f in glob.glob(str(ROOT / 'Data/raw/derived/bialystok-industrial-c/world/instances_*.json')):
    for it in json.load(open(f, encoding='utf-8'))['instances']:
        if 'lamp_double' in it['p'] and -760 < it['e'] < -400 and -90 < it['n'] < 80:
            lamps.append((it['e'], it['n'], it['z'] + 10.9))
lamps = np.array(sorted(lamps, key=lambda t: t[0], reverse=True))

def axis(s):
    p, q = (A1, A2) if s >= 0 else (A0, A1)
    u = (q - p) / np.linalg.norm(q - p)
    return A1 + s * u, u

def ground(s, lat):
    c, u = axis(s); r = np.array([u[1], -u[0]])
    return np.array([*(c + lat * r), U(s)])

def rot(h, p, r):
    h, p, r = map(math.radians, (h, p, r))
    f = np.array([math.sin(h) * math.cos(p), math.cos(h) * math.cos(p), math.sin(p)])
    rt = np.array([math.cos(h), -math.sin(h), 0.0]); up = np.cross(rt, f)
    rt2 = math.cos(r) * rt + math.sin(r) * up; up2 = math.cos(r) * up - math.sin(r) * rt
    return f, rt2, up2

def project(cam, pts, h, p, r):
    f, rt, up = rot(h, p, r)
    d = pts - cam; z = d @ f
    return np.stack([640 + F * (d @ rt) / z, 480 - F * (d @ up) / z], 1), z

def residual(x, W=7.0, edge=False):
    s, lat, eye, h, p, r = x
    cam = ground(s, lat); cam[2] += eye
    _, u = axis(s)
    ahead = lamps[((lamps[:, :2] - cam[:2]) @ u) > 3]
    ahead = ahead[np.argsort(((ahead[:, :2] - cam[:2]) @ u))][:5]
    pl, _ = project(cam, ahead, h, p, r)
    res = list((pl - PH_L[:len(pl)]).ravel())
    line = np.array([ground(s + t, 0) for t in np.linspace(3, 120, 400)])
    pd, z = project(cam, line, h, p, r); pd = pd[z > 0]
    for q in PH_D:
        res.append(np.min(np.linalg.norm(pd - q, axis=1)))
    if edge:
        le = np.array([ground(s + t, W / 2) for t in np.linspace(3, 120, 400)])
        pe, z = project(cam, le, h, p, r); pe = pe[z > 0]
        for q in PH_E: res.append(np.min(np.linalg.norm(pe - q, axis=1)))
    return np.array(res)

if __name__ == '__main__':
  best = None
  for s0 in (-10, 0, 10, 20):
    for h0 in (309, 314):
      sol = least_squares(residual, [s0, 1.1, 1.3, h0, 7, 0], bounds=([-40, -3, 0.9, 290, -5, -10], [40, 3.5, 2.0, 330, 15, 10]))
      if best is None or sol.cost < best.cost: best = sol
  x = best.x
  print('fit s lat eye heading pitch roll:', np.round(x, 3), 'rms px', round(float(np.sqrt(np.mean(best.fun ** 2))), 1))
  print('residuals', np.round(best.fun, 1))
  cam = ground(x[0], x[1]); print('cam E N U', np.round(cam + [0, 0, x[2]], 3), 'deck U', round(U(x[0]), 3))
  # horizon fraction without roll for the renderer
  print('rect horizon fraction', round(0.5 + F * math.tan(math.radians(x[4])) / 960, 4))
  for W in (7.0, 7.5, 8.0):
      sol = least_squares(lambda y: residual(y, W, True), x, bounds=([-40, -3, 0.9, 290, -5, -10], [40, 3.5, 2.0, 330, 15, 10]))
      print('with edge W', W, np.round(sol.x, 3), 'rms', round(float(np.sqrt(np.mean(sol.fun ** 2))), 1))
