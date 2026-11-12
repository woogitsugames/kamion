"""ADR 0130: write chosen poses as explicit authored overrides + matching sbs_cameras.json / sbs_references.json
entries (same formula as tools/refs/sbs_gate3.py prepare(); prepare itself is NOT run - it downloads/rectifies)."""
import json, math, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import poselib as P, deckray as D

def target(gps, base, fwd, right, axis):
    h = math.radians(axis)
    return base[0] + fwd * math.sin(h) + right * math.cos(h), base[1] + fwd * math.cos(h) - right * math.sin(h)

R, O = P.refs(), P.overrides()
CH = {
 '3281350541967811': dict(base=(-310.0, -193.05), fwd=0, right=0, axis=125, eye=1.4, hd=0.0, hz=0.77, probe='r2 a0',
   anchors='lattice portal behind, over the left (northbound) carriageway: leg x 0.145/0.434 photo vs 0.14/0.43 render; long low hall at the left edge and low white building block right at the horizon; road vanishing point / horizon 0.77',
   how='resection: GUGiK/generated portal (-260.8,-208.3) span 16 m, leg bearings + EC chimney bearings (heading = SfM within 0.1 deg); GPS of zsolt 2017 sequence ~73 m ahead along Andersa'),
 '297817221966185': dict(base=(-367.2, -150.1), fwd=0, right=0, axis=129, eye=1.4, hd=1.15, hz=0.75, probe='r2 b0',
   anchors='same portal far ahead in the image centre (x 0.445-0.566 photo / 0.44-0.56 render); blue industrial hall at the left edge x 0-0.2 in both; horizon 0.75',
   how='resection: portal legs + EC chimneys x 0.742/0.762 -> heading +1.15 deg; position ~85 m back from GPS (same sequence offset as 3281350, 2.7 s earlier)'),
 '1801374876712141': dict(base=None, fwd=20, right=0, axis=350, eye=2.2, hd=0.0, hz=0.56, probe='r1 d3 / r2 d0',
   anchors='noise screen starts close at the right edge (x 0.75-1.0, top y ~0.3); wide grass median with the opposite carriageway at x 0-0.3 on the left; horizon 0.56',
   how='forward 20 m along Al. Tysiaclecia (heading 350); horizon from far road/treeline'),
 '494288258686575': dict(base=None, fwd=0, right=3.0, axis=307, eye=1.7, hd=0.0, hz=0.72, probe='r2 c1/c2 (between)', deck=True,
   anchors='dark screen posts close at the right receding to x ~0.2 at the horizon; median barrier and second deck at the left edge; horizon 0.72',
   how='3 m right on the Putry deck (right lane, still road_asphalt in the generated deck); deck height from generated chunk GLB ray + 1.7 m'),
}

def build():
    out = {}
    for key, c in CH.items():
        cid = 'sbs-g3-b-' + key
        ref = R[cid]
        _, info = P.camera(ref, O[cid])
        base = c['base'] or tuple(info['gps_en'])
        e, n = target(info['gps_en'], base, c['fwd'], c['right'], c['axis'])
        hs = [h for h in D.heights(e, n) if h[2] == 'road_asphalt']
        if not hs: raise SystemExit(f'no road asphalt under {cid}')
        road_u = hs[0][0]
        ov = dict(O[cid])
        ov.update(east_delta_m=round(e - info['gps_en'][0], 4), north_delta_m=round(n - info['gps_en'][1], 4),
                  eye_height_m=c['eye'], absolute_u_m=round(road_u + c['eye'], 4), rectified_horizon_y_fraction=c['hz'])
        if c['hd']: ov['heading_delta_deg'] = c['hd']
        ov['pose_status'] = 'WORKING_VALUE'
        ov['pose_confidence'] = 'B'
        ov['pose_reason'] = f"ADR 0130 (s12): calibrated from diagnostic probe {c['probe']}; anchors: {c['anchors']}"
        old = O[cid].get('note', '').split(' ADR 0130:')[0]
        ov['note'] = (old + f" ADR 0130: {c['how']}. Generated road asphalt U {road_u} m (chunk GLB ray) + eye {c['eye']} m; "
                      f"rectified horizon {c['hz']} measured on the rectified photo (supersedes horizon_y_fraction). WORKING_VALUE, not surveyed.")
        cam, inf = P.camera(ref, ov)
        out[cid] = (ov, cam, inf)
    return out

if __name__ == '__main__':
    res = build()
    reg = P.REGION
    od = P.S.read(reg / 'sbs_authored_overrides.json')
    cd = P.S.read(reg / 'sbs_cameras.json')
    rd = P.S.read(reg / 'sbs_references.json')
    for cid, (ov, cam, inf) in res.items():
        od['authored_overrides'][cid] = ov
        for i, c in enumerate(cd['cameras']):
            if c['id'] == cid: cd['cameras'][i] = cam
        for r in rd['references']:
            if r['camera'] == cid:
                r['heading_grid_deg'] = inf['heading']; r['horizon_y_fraction'] = inf['horizon_rect']
                r['pose_status'] = ov['pose_status']; r['pose_confidence'] = ov['pose_confidence']; r['pose_reason'] = ov['pose_reason']
                r['authored_overrides'] = ov
        print(cid, cam['pos'], cam['look_at'], round(inf['heading'], 3), {k: ov[k] for k in ('east_delta_m', 'north_delta_m', 'absolute_u_m', 'eye_height_m')})
    if '--write' in sys.argv:
        for name, data in (('sbs_authored_overrides.json', od), ('sbs_cameras.json', cd), ('sbs_references.json', rd)):
            P.S.write(reg / name, data)
        print('written')
