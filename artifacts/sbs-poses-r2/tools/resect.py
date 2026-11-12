"""ADR 0140: re-resect the 4 Andersa-portal SBS poses against the 14 m portal (ADR 0127).

Unknowns per frame: E, N, heading (eye height and rectified horizon kept, height re-sampled from the generated road).
Observations: photo x of both portal columns (measured on the rectified photo, 1280 px, look/z*.png) + one prior:
  frontal grobin frames (275528, 837235): lateral offset across the carriageway = the current lane (lane dashes agree
  on photo and render, camera in the middle lane);
  rear zsolt frames (3281350, 297817): heading from the EC chimney bearings (~1.3 km, ADR 0130), i.e. the chimney
  image x of the reviewed pose is preserved.
Prints the solution, residuals and the column-top check (world 7.0 m rule height vs photo), writes probes/plan."""
import json, math, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).parent))
import poselib as P, proj, deckray as D

R, O = P.refs(), P.overrides()
AX = math.degrees(math.atan2(proj.FEET['R_nb_east'][0] - proj.FEET['L_nb_west'][0],
                             proj.FEET['R_nb_east'][1] - proj.FEET['L_nb_west'][1])) + 90  # road axis (SE), deg
CENTER = np.mean(list(proj.FEET.values()), axis=0)
CHIMNEYS = [(778619.25 - P.ORIGIN['x'], 595139.04 - P.ORIGIN['y']), (778713.26 - P.ORIGIN['x'], 595089.71 - P.ORIGIN['y'])]
Y_COL = 6.0  # column point used for x (m above the footing); columns are near-vertical in all four frames

# photo measurements, x px of 1280 (column centre at beam level), beam top y px
M = {
    '275528677534382': dict(x={'L_nb_west': 377, 'R_nb_east': 964}, top_y=160, prior='lateral'),
    '837235577143499': dict(x={'L_nb_west': 584, 'R_nb_east': 736}, top_y=332, prior='lateral'),
    '3281350541967811': dict(x={'R_nb_east': 189, 'L_nb_west': 560}, top_y=556, prior='chimney', chimney_x=(936 / 1280, 910 / 1280)),
    '297817221966185': dict(x={'R_nb_east': 571, 'L_nb_west': 722}, top_y=670, prior='chimney', chimney_x=(976 / 1280, 950 / 1280)),  # chimney-1 (W) right, chimney-2 left (look/z*ch.png)
}


def lateral(e, n):
    a = math.radians(AX)
    return (e - CENTER[0]) * math.cos(a) - (n - CENTER[1]) * math.sin(a)


def make(cid, ov):
    ref = R[cid]
    cam, info = P.camera(ref, ov)
    return cam, info, ref


def size(ref):
    return 1280, round(1280 * ref['height'] / ref['width'])


def residuals(cid, ov, meas, base_lat, base_chim):
    cam, info, ref = make(cid, ov)
    w, h = size(ref)
    res = []
    for k, xpx in meas['x'].items():
        e, n = proj.FEET[k]
        (fx, _), = proj.project(cam, [(e, n, proj.FOOT_U + Y_COL)], w, h)
        res.append(fx * w - xpx)
    if meas['prior'] == 'lateral':
        res.append((lateral(*cam['pos'][:2]) - base_lat) * 50)  # 1 cm ~ 0.5 px
    else:
        pr = proj.project(cam, [(e, n, 200.0) for e, n in CHIMNEYS], w, h)
        for (fx, _), bx in zip(pr, base_chim):
            res.append((fx - bx) * w * 3)
    return np.array(res)


def solve(key):
    cid = 'sbs-g3-b-' + key
    meas = M[key]
    ov = dict(O[cid])
    cam0, info0, ref = make(cid, ov)
    w, h = size(ref)
    base_lat = lateral(*cam0['pos'][:2])
    if 'chimney_x' in meas:
        base_chim = meas['chimney_x']
    else:
        base_chim = [p[0] for p in proj.project(cam0, [(e, n, 200.0) for e, n in CHIMNEYS], w, h)]
    x = np.array([ov.get('east_delta_m', 0.0), ov.get('north_delta_m', 0.0), ov.get('heading_delta_deg', 0.0)])
    def apply(x):
        o = dict(ov); o['east_delta_m'], o['north_delta_m'], o['heading_delta_deg'] = map(float, x)
        return o
    for _ in range(30):
        r = residuals(cid, apply(x), meas, base_lat, base_chim)
        J = np.zeros((len(r), 3))
        for i, d in enumerate((0.01, 0.01, 0.001)):
            dx = np.zeros(3); dx[i] = d
            J[:, i] = (residuals(cid, apply(x + dx), meas, base_lat, base_chim) - r) / d
        step = np.linalg.lstsq(J, -r, rcond=None)[0]
        x = x + step
        if np.abs(step).max() < 1e-5:
            break
    o = apply(x)
    cam1, info1, _ = make(cid, o)
    # height from the generated road under the new position (chunk GLB ray) + kept eye height
    e, n = cam1['pos'][:2]
    hs = [hh for hh in D.heights(e, n) if hh[2] == 'road_asphalt']
    road_u = hs[0][0] if hs else None
    eye = ov.get('eye_height_m', 1.4)
    if road_u is not None:
        o['absolute_u_m'] = round(road_u + eye, 4)
    o['east_delta_m'] = round(o['east_delta_m'], 4); o['north_delta_m'] = round(o['north_delta_m'], 4)
    o['heading_delta_deg'] = round(o['heading_delta_deg'], 3)
    cam1, info1, _ = make(cid, o)
    r = residuals(cid, o, meas, base_lat, base_chim)
    tops = proj.project(cam1, [(e_, n_, proj.FOOT_U + proj.PORTAL_H) for e_, n_ in proj.FEET.values()], w, h)
    return dict(cid=cid, ov=o, cam=cam1, info=info1, before=cam0, road_u=road_u,
                dist_before=float(np.hypot(*(np.array(cam0['pos'][:2]) - CENTER))),
                dist_after=float(np.hypot(*(np.array(cam1['pos'][:2]) - CENTER))),
                move=[round(cam1['pos'][i] - cam0['pos'][i], 3) for i in range(3)],
                heading_before=round(info0['heading'], 3), heading_after=round(info1['heading'], 3),
                resid_px=[round(float(v), 2) for v in r],
                top_y_model=[round(t[1] * h, 1) for t in tops], top_y_photo=meas['top_y'])


if __name__ == '__main__':
    out = {}
    for key in M:
        s = solve(key)
        out[key] = s
        print(key, 'dist %.1f -> %.1f m' % (s['dist_before'], s['dist_after']), 'move', s['move'],
              'heading', s['heading_before'], '->', s['heading_after'], 'resid', s['resid_px'],
              'top y model', s['top_y_model'], 'photo', s['top_y_photo'], 'road U', s['road_u'])
    Path(__file__).resolve().parents[1].joinpath('resection.json').write_text(json.dumps(
        {k: {kk: vv for kk, vv in v.items()} for k, v in out.items()}, indent=1, default=str), encoding='utf-8')
