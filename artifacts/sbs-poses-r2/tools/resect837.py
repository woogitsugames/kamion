"""ADR 0140: 837235 resection with the island-nose chevron (U-4a) as the near anchor.
Chevron centre x and plate height (1.35 m, lower edge 0.9 m) measured on look/z837ch.png; portal west column x 584.
Variant A: chevron at the orthophoto position (overrides at_en); variant B: at the generated (snapped) instance."""
import math, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).parent))
import resect as X, proj, deckray as D, poselib as P

KEY = '837235577143499'; CID = 'sbs-g3-b-' + KEY
OBS = dict(chev_x=1102, chev_h=155, leg_x=584)
CHEV = {'ortho_at_en': (-217.3, -240.3), 'generated': (-212.027, -239.092)}
Z0 = 130.465


def model(ov, chev):
    cam, info, ref = X.make(CID, ov); w, h = X.size(ref)
    e, n = chev
    (bx, by), (tx, ty) = proj.project(cam, [(e, n, Z0 + 0.9), (e, n, Z0 + 2.25)], w, h)
    (lx, _), = proj.project(cam, [(*proj.FEET['L_nb_west'], proj.FOOT_U + X.Y_COL)], w, h)
    return np.array([(bx + tx) / 2 * w - OBS['chev_x'], (by - ty) * h - OBS['chev_h'], lx * w - OBS['leg_x']]), cam, info


def solve(chev):
    ov = dict(X.O[CID]); x = np.array([ov['east_delta_m'], ov['north_delta_m'], ov.get('heading_delta_deg', 0.0)])
    def ap(x):
        o = dict(ov); o['east_delta_m'], o['north_delta_m'], o['heading_delta_deg'] = map(float, x); return o
    for _ in range(40):
        r = model(ap(x), chev)[0]; J = np.zeros((3, 3))
        for i, d in enumerate((0.01, 0.01, 0.001)):
            dx = np.zeros(3); dx[i] = d; J[:, i] = (model(ap(x + dx), chev)[0] - r) / d
        st = np.linalg.lstsq(J, -r, rcond=None)[0]; st = st * min(1.0, 1.5 / max(1e-9, np.abs(st[:2]).max())); x = x + st
        if np.abs(st).max() < 1e-6: break
    o = ap(x); r, cam, info = model(o, chev)
    return o, r, cam, info


if __name__ == '__main__':
    cam0, info0, ref = X.make(CID, X.O[CID]); w, h = X.size(ref)
    for name, chev in CHEV.items():
        o, r, cam, info = solve(chev)
        (rx, _), = proj.project(cam, [(*proj.FEET['R_nb_east'], proj.FOOT_U + X.Y_COL)], w, h)
        print(name, 'move', [round(cam['pos'][i] - cam0['pos'][i], 2) for i in range(2)], 'heading %.2f (was %.2f)' % (info['heading'], info0['heading']),
              'resid', np.round(r, 2), 'portal dist %.1f' % math.dist(cam['pos'][:2], X.CENTER), 'east leg x %.0f (photo beam end ~736)' % (rx * w),
              'chev dist %.1f' % math.dist(cam['pos'][:2], chev), 'lat %.2f (was %.2f)' % (X.lateral(*cam['pos'][:2]), X.lateral(*cam0['pos'][:2])))


def write_r2():
    import json
    out = Path(__file__).resolve().parents[1] / 'r2'; out.mkdir(exist_ok=True)
    o, r, cam, info = solve(CHEV['ortho_at_en'])
    hs = [hh for hh in D.heights(*cam['pos'][:2]) if hh[2] == 'road_asphalt']
    o['absolute_u_m'] = round(hs[0][0] + o.get('eye_height_m', 2.2), 4)
    for k in ('east_delta_m', 'north_delta_m'):
        o[k] = round(o[k], 4)
    o['heading_delta_deg'] = round(o['heading_delta_deg'], 3)
    probes, plan = [], []
    for tag, eye in (('c0', o.get('eye_height_m', 2.2)), ('c1', 1.5)):
        ov = dict(o); ov['eye_height_m'] = eye; ov['absolute_u_m'] = round(hs[0][0] + eye, 4)
        pid = f'sbs-p140-837235-{tag}'
        c, inf = P.camera(X.R[CID], ov, pid)
        c['pose_confidence'] = 'C'; c['pose_reason'] = 'ADR0140 diagnostic probe only'
        probes.append(c)
        plan.append({'probe': pid, 'base': CID, 'rectified_horizon': ov.get('rectified_horizon_y_fraction'),
                     'override': {k: ov[k] for k in ('east_delta_m', 'north_delta_m', 'eye_height_m', 'absolute_u_m', 'heading_delta_deg')},
                     'pos': c['pos'], 'heading_grid_deg': round(inf['heading'], 3),
                     'note': f'chevron (orthophoto at_en) + portal west leg resection, eye {eye}'})
    c0, _ = P.camera(X.R[CID], X.O[CID]); probes.append(c0)
    (out / 'cameras.json').write_text(json.dumps({'schema': 'kamion/sbs-cameras/1', 'frame': 'E,N,absolute U', 'cameras': probes}, indent=1), encoding='utf-8')
    (out / 'plan.json').write_text(json.dumps(plan, indent=1), encoding='utf-8')
    (out / 'ids-16x9.txt').write_text(','.join(p['id'] for p in probes))
    print('r2', [p['pos'] for p in probes])


if __name__ == '__main__' and '--r2' in sys.argv:
    write_r2()
