"""ADR 0130 round 1 diagnostic probes (pose_confidence C, never production)."""
import json, math, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import poselib as P

R, O = P.refs(), P.overrides()
OUT = Path(__file__).resolve().parents[1] / 'r1'
OUT.mkdir(exist_ok=True)


def shift(gps, target, fwd=0.0, right=0.0, axis=125.0):
    h = math.radians(axis)
    e = target[0] + fwd * math.sin(h) + right * math.cos(h)
    n = target[1] + fwd * math.cos(h) - right * math.sin(h)
    return round(e - gps[0], 4), round(n - gps[1], 4), (e, n)


probes, plan = [], []
def add(key, tag, target, axis, fwd=0, right=0, eye=1.4, hd=0.0, hz=None, seat=None, note='', u_abs=None):
    cid = 'sbs-g3-b-' + key
    ref, base = R[cid], dict(O[cid])
    _, info = P.camera(ref, base)
    de, dn, (e, n) = shift(info['gps_en'], target, fwd, right, axis)
    ov = {k: v for k, v in base.items() if k not in ('east_delta_m', 'north_delta_m', 'absolute_u_m', 'eye_height_m', 'heading_delta_deg')}
    ov.update(east_delta_m=de, north_delta_m=dn, eye_height_m=eye, heading_delta_deg=hd)
    ov['absolute_u_m'] = round(P.terrain(e, n) + eye, 4) if u_abs is None else u_abs
    if hz is not None:
        ov['horizon_y_fraction'] = hz
    pid = f'sbs-p130-{key[:6]}-{tag}'
    cam, inf = P.camera(ref, ov, pid)
    cam['pose_confidence'] = 'C'; cam['pose_reason'] = 'ADR0130 diagnostic probe only'
    if seat:
        cam['seat'] = seat
    probes.append(cam)
    plan.append({'probe': pid, 'base': cid, 'fwd_m': fwd, 'right_m': right, 'axis_deg': axis, 'eye_m': eye,
                 'heading_delta_deg': hd, 'horizon_y_fraction': ov.get('horizon_y_fraction'), 'seat': seat or 'file',
                 'override': {k: ov[k] for k in ('east_delta_m', 'north_delta_m', 'eye_height_m', 'absolute_u_m', 'heading_delta_deg')},
                 'heading_grid_deg': round(inf['heading'], 3), 'pos': cam['pos'], 'note': note})


# 3281350: portal legs (GUGiK/generated portal at (-260.8,-208.3), span 16 m) resected with heading from EC chimneys
C328 = (-310.0, -193.05)
add('3281350541967811', 'a0', C328, 125, note='resection: legs x=0.145/0.434, chimneys -> heading = SfM')
add('3281350541967811', 'a1', C328, 125, eye=2.2)
add('3281350541967811', 'a2', C328, 125, fwd=5)
add('3281350541967811', 'a3', C328, 125, fwd=-5)
add('3281350541967811', 'a4', C328, 125, right=2)
add('3281350541967811', 'a5', C328, 125, right=-2)
add('3281350541967811', 'a6', C328, 125, hd=2)
add('3281350541967811', 'a7', C328, 125, hd=-2)
# 297817: portal far (legs x=0.445/0.566) + chimneys x=0.742/0.762 -> heading +1.15 deg
C297 = (-367.2, -150.1)
add('297817221966185', 'b0', C297, 129, hd=1.15, note='resection: legs + chimneys')
add('297817221966185', 'b1', C297, 129, hd=1.15, eye=2.2)
add('297817221966185', 'b2', C297, 129, fwd=10, hd=1.15)
add('297817221966185', 'b3', C297, 129, fwd=-10, hd=1.15)
add('297817221966185', 'b4', C297, 129, right=-3, hd=1.15)
add('297817221966185', 'b5', C297, 129, right=3, hd=1.15)
add('297817221966185', 'b6', C297, 129, hd=0)
# 494288 (Putry deck): along deck axis 307, lateral; reseat on road collision (+1.7 m)
G494 = tuple(P.camera(R['sbs-g3-b-494288258686575'], O['sbs-g3-b-494288258686575'])[1]['gps_en'])
for tag, f, r, hz in [('c0', 0, 0, None), ('c1', -20, 0, None), ('c2', -10, 0, None), ('c3', 10, 0, None), ('c4', 20, 0, None),
                      ('c5', 0, -3.5, None), ('c6', 0, 3.5, None), ('c7', 0, 0, 0.72), ('c8', 20, 0, 0.72), ('c9', -20, 0, 0.72)]:
    add('494288258686575', tag, G494, 307, fwd=f, right=r, eye=1.7, hz=hz, seat='road', u_abs=141.888)
# 1801374: forward along heading 353 (lead: +15..20 m), eye 2.2/1.6, horizon 0.62/0.57
G180 = tuple(P.camera(R['sbs-g3-b-1801374876712141'], O['sbs-g3-b-1801374876712141'])[1]['gps_en'])
for tag, f, eye, hz in [('d0', 0, 2.2, None), ('d1', 10, 2.2, None), ('d2', 15, 2.2, None), ('d3', 20, 2.2, None), ('d4', 25, 2.2, None),
                        ('d5', 15, 1.6, None), ('d6', 20, 1.6, None), ('d7', 15, 2.2, 0.57), ('d8', 20, 2.2, 0.57)]:
    add('1801374876712141', tag, G180, 350, fwd=f, eye=eye, hz=hz)

# top-down overview cameras (4:3), north up
def top(tid, en, hgt=110):
    u = P.terrain(*en) + hgt
    probes.append({'id': tid, 'kind': 'photo_match', 'seat': 'file', 'type': 'persp', 'pos': [en[0], en[1], round(u, 3)],
                   'look_at': [en[0], en[1] + 0.5, round(u - hgt, 3)], 'fov_deg': 50.0, 'segment': 'G3-B',
                   'pose_confidence': 'C', 'pose_reason': 'ADR0130 top-down overview', 'note': 'overview'})
top('sbs-p130-top-494288', G494)
top('sbs-p130-top-180137', G180)
top('sbs-p130-top-portal', (-290.0, -190.0))
(OUT / 'cameras.json').write_text(json.dumps({'schema': 'kamion/sbs-cameras/1', 'frame': 'E,N,absolute U', 'cameras': probes}, indent=1), encoding='utf-8')
(OUT / 'plan.json').write_text(json.dumps(plan, indent=1), encoding='utf-8')
ids43 = [p['id'] for p in probes if '180137' not in p['id'] or 'top' in p['id']]
ids169 = [p['id'] for p in probes if '180137' in p['id'] and 'top' not in p['id']]
(OUT / 'ids-4x3.txt').write_text(','.join(ids43)); (OUT / 'ids-16x9.txt').write_text(','.join(ids169))
print(len(probes), len(ids43), len(ids169))
for p in plan: print(p['probe'], p['pos'], p['heading_grid_deg'])
