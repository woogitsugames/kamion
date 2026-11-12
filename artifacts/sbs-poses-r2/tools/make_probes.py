"""ADR 0140 diagnostic probes (pose_confidence C, never production): resected pose s0 + along-axis / eye / heading
variants, plus the production cameras (before)."""
import json, math, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import poselib as P, resect as X, deckray as D

OUT = Path(__file__).resolve().parents[1] / 'r1'
OUT.mkdir(exist_ok=True)
probes, plan = [], []


def variant(key, tag, s, fwd=0.0, eye=None, hd=0.0, hz=None, note=''):
    cid = 'sbs-g3-b-' + key
    ov = dict(s['ov'])
    a = math.radians(X.AX + 180)  # northbound direction (towards NW) for "forward" along Andersa
    if key in ('3281350541967811', '297817221966185'):
        a = math.radians(X.AX)  # zsolt frames drive SE
    ov['east_delta_m'] = round(ov['east_delta_m'] + fwd * math.sin(a), 4)
    ov['north_delta_m'] = round(ov['north_delta_m'] + fwd * math.cos(a), 4)
    ov['heading_delta_deg'] = round(ov.get('heading_delta_deg', 0) + hd, 3)
    cam0, info0 = P.camera(X.R[cid], ov)
    e, n = cam0['pos'][:2]
    hs = [h for h in D.heights(e, n) if h[2] == 'road_asphalt']
    eye = eye or ov.get('eye_height_m', 1.4)
    ov['eye_height_m'] = eye
    ov['absolute_u_m'] = round(hs[0][0] + eye, 4)
    if hz is not None:
        ov['rectified_horizon_y_fraction'] = hz
    pid = f'sbs-p140-{key[:6]}-{tag}'
    cam, inf = P.camera(X.R[cid], ov, pid)
    cam['pose_confidence'] = 'C'; cam['pose_reason'] = 'ADR0140 diagnostic probe only'
    probes.append(cam)
    plan.append({'probe': pid, 'base': cid, 'fwd_m': fwd, 'eye_m': eye, 'heading_delta_extra_deg': hd,
                 'rectified_horizon': ov.get('rectified_horizon_y_fraction'), 'override': {k: ov[k] for k in (
                     'east_delta_m', 'north_delta_m', 'eye_height_m', 'absolute_u_m', 'heading_delta_deg')},
                 'pos': cam['pos'], 'heading_grid_deg': round(inf['heading'], 3), 'note': note})


sol = {k: X.solve(k) for k in X.M}
for k, s in sol.items():
    variant(k, 's0', s, note='resected (legs 14 m portal + prior)')
    variant(k, 'fp', s, fwd=2.0 if k[:3] in ('275', '328') else 6.0, note='2/6 m further along the driving direction')
    variant(k, 'fm', s, fwd=-2.0 if k[:3] in ('275', '328') else -6.0, note='2/6 m back')
    if k.startswith('837235'):
        variant(k, 'h0', s, hd=s['heading_before'] - s['heading_after'], note='resected position, reviewed heading')
    if k.startswith('3281350') or k.startswith('297817'):
        variant(k, 'zp', s, hz=s['info']['horizon_rect'] + 0.03, note='horizon +0.03 (chimney tops say ~+0.04)')
    if k.startswith('275528'):
        variant(k, 'e2', s, eye=1.3, note='eye 1.3 m (ADR 0127 frontal estimate)')
def partial(key, tag, right=0.0, eye=None, hd=0.0, hz=None, note=''):
    cid = 'sbs-g3-b-' + key
    ov = dict(X.O[cid])
    _, info = P.camera(X.R[cid], ov)
    h = math.radians(info['heading'])
    ov['east_delta_m'] = round(ov.get('east_delta_m', 0) + right * math.cos(h), 4)
    ov['north_delta_m'] = round(ov.get('north_delta_m', 0) - right * math.sin(h), 4)
    if hd:
        ov['heading_delta_deg'] = round(ov.get('heading_delta_deg', 0) + hd, 3)
    if hz is not None:
        ov['rectified_horizon_y_fraction'] = hz
    if right or eye:
        cam0, _ = P.camera(X.R[cid], ov)
        hs = [hh for hh in D.heights(*cam0['pos'][:2]) if hh[2] == 'road_asphalt']
        eye = eye or ov.get('eye_height_m', 2.2)
        ov['eye_height_m'] = eye
        ov['absolute_u_m'] = round(hs[0][0] + eye, 4)
    pid = f'sbs-p140-{key[:6]}-{tag}'
    cam, inf = P.camera(X.R[cid], ov, pid)
    cam['pose_confidence'] = 'C'; cam['pose_reason'] = 'ADR0140 diagnostic probe only'
    probes.append(cam)
    plan.append({'probe': pid, 'base': cid, 'right_m': right, 'eye_m': ov.get('eye_height_m'), 'heading_delta_extra_deg': hd,
                 'rectified_horizon': ov.get('rectified_horizon_y_fraction'), 'pos': cam['pos'],
                 'override': {k: ov[k] for k in ('east_delta_m', 'north_delta_m', 'eye_height_m', 'absolute_u_m', 'heading_delta_deg') if k in ov},
                 'heading_grid_deg': round(inf['heading'], 3), 'note': note})


partial('150280503737744', 's0', hz=0.50, hd=-2.2, note='horizon 0.50 (road VP / far road end on photo vs render), heading -2.2 (VP x)')
partial('150280503737744', 'z0', hz=0.50, note='horizon 0.50 only')
partial('3678296072299092', 's0', hz=0.559, note='horizon 0.559 (near-road VP photo 384 px vs render 403 px)')
partial('180137487671214'[:15] + '1', 'l1', right=1.5, eye=1.8, note='1.5 m right, eye 1.8')
partial('1801374876712141', 'l2', right=1.0, eye=2.2, note='1.0 m right')
partial('1801374876712141', 'l3', right=2.5, eye=1.8, note='2.5 m right, eye 1.8')
for k in ('150280503737744', '3678296072299092', '1801374876712141'):
    c, _ = P.camera(X.R['sbs-g3-b-' + k], X.O['sbs-g3-b-' + k]); probes.append(c)
for k in X.M:
    c, _ = P.camera(X.R['sbs-g3-b-' + k], X.O['sbs-g3-b-' + k]); probes.append(c)
(OUT / 'cameras.json').write_text(json.dumps({'schema': 'kamion/sbs-cameras/1', 'frame': 'E,N,absolute U', 'cameras': probes}, indent=1), encoding='utf-8')
(OUT / 'plan.json').write_text(json.dumps(plan, indent=1), encoding='utf-8')
wide = ('275528', '837235', '150280', '367829', '180137')
(OUT / 'ids-16x9.txt').write_text(','.join(p['id'] for p in probes if any(w in p['id'] for w in wide)))
(OUT / 'ids-4x3.txt').write_text(','.join(p['id'] for p in probes if not any(w in p['id'] for w in wide)))
print(len(probes))
