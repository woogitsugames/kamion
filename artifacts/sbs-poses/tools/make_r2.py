"""ADR 0130 round 2 diagnostic probes (pose_confidence C, never production)."""
import json, math, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import poselib as P

R, O = P.refs(), P.overrides()
OUT = Path(__file__).resolve().parents[1] / 'r2'
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
        ov['rectified_horizon_y_fraction'] = hz
    pid = f'sbs-p130-{key[:6]}-{tag}'
    cam, inf = P.camera(ref, ov, pid)
    cam['pose_confidence'] = 'C'; cam['pose_reason'] = 'ADR0130 diagnostic probe only'
    if seat:
        cam['seat'] = seat
    probes.append(cam)
    plan.append({'probe': pid, 'base': cid, 'fwd_m': fwd, 'right_m': right, 'axis_deg': axis, 'eye_m': eye,
                 'heading_delta_deg': hd, 'horizon_y_fraction': ov.get('rectified_horizon_y_fraction', ov.get('horizon_y_fraction')), 'seat': seat or 'file',
                 'override': {k: ov[k] for k in ('east_delta_m', 'north_delta_m', 'eye_height_m', 'absolute_u_m', 'heading_delta_deg')},
                 'heading_grid_deg': round(inf['heading'], 3), 'pos': cam['pos'], 'note': note})



C328 = (-310.0, -193.05)
for tag, f, r, eye, hz, hd in [('a0',0,0,1.4,.77,0),('a1',0,0,2.2,.77,0),('a2',5,0,1.4,.77,0),('a3',-5,0,1.4,.77,0),('a4',0,1.5,1.4,.77,0),('a5',0,0,1.4,.74,0)]:
    add('3281350541967811', tag, C328, 125, fwd=f, right=r, eye=eye, hz=hz, hd=hd)
C297 = (-367.2, -150.1)
for tag, f, r, eye, hz in [('b0',0,0,1.4,.75),('b1',0,-3,1.4,.75),('b2',0,0,2.2,.75),('b3',-8,-2,1.4,.75),('b4',0,0,1.4,.72)]:
    add('297817221966185', tag, C297, 129, fwd=f, right=r, eye=eye, hz=hz, hd=1.15)
G494 = tuple(P.camera(R['sbs-g3-b-494288258686575'], O['sbs-g3-b-494288258686575'])[1]['gps_en'])
for tag, f, r, hz, hd in [('c0',0,1.5,.72,0),('c1',0,2.5,.72,0),('c2',0,3.5,.72,0),('c3',0,2.5,.75,0),('c4',-10,2.5,.72,0),('c5',10,2.5,.72,0),('c6',0,2.5,.72,3),('c7',0,2.5,.72,-3)]:
    add('494288258686575', tag, G494, 307, fwd=f, right=r, eye=1.7, hz=hz, hd=hd, seat='road', u_abs=141.888)
G180 = tuple(P.camera(R['sbs-g3-b-1801374876712141'], O['sbs-g3-b-1801374876712141'])[1]['gps_en'])
for tag, f, r, eye, hz in [('d0',20,0,2.2,.56),('d1',25,0,2.2,.56),('d2',30,0,2.2,.56),('d3',25,0,1.8,.56),('d4',25,1.5,2.2,.56),('d5',25,0,2.2,.53)]:
    add('1801374876712141', tag, G180, 350, fwd=f, right=r, eye=eye, hz=hz)
for k in ('3281350541967811','297817221966185','494288258686575','1801374876712141'):
    c, _ = P.camera(R['sbs-g3-b-'+k], O['sbs-g3-b-'+k]); probes.append(c)
(OUT / 'cameras.json').write_text(json.dumps({'schema': 'kamion/sbs-cameras/1', 'frame': 'E,N,absolute U', 'cameras': probes}, indent=1), encoding='utf-8')
(OUT / 'plan.json').write_text(json.dumps(plan, indent=1), encoding='utf-8')
ids43 = [p['id'] for p in probes if '180137' not in p['id']]
ids169 = [p['id'] for p in probes if '180137' in p['id']]
(OUT / 'ids-4x3.txt').write_text(','.join(ids43)); (OUT / 'ids-16x9.txt').write_text(','.join(ids169))
print(len(probes))
