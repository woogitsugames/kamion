"""ADR 0143 diagnostic probes (pose_confidence C, never production). usage: probes.py r1"""
import json, math, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import poselib as P, deckray as D
RND = sys.argv[1] if len(sys.argv) > 1 else 'r1'
OUT = Path(__file__).resolve().parents[1] / RND
OUT.mkdir(exist_ok=True)
R, O = P.refs(), P.overrides()
probes, plan = [], []


def surf(e, n, prefer=('road_asphalt',)):
    hs = D.heights(e, n)
    for h in hs:
        if h[2] in prefer:
            return h[0], h
    return (hs[0][0], hs[0]) if hs else (None, None)


def probe(key, tag, e, n, eye, heading, hz=None, note='', u=None, base_prefix='sbs-g3-b-'):
    cid = base_prefix + key
    ov = dict(O.get(cid, {}))
    _, inf0 = P.camera(R[cid], {k: v for k, v in ov.items() if k not in ('heading_delta_deg',)})
    gps = inf0['gps_en']
    ov['east_delta_m'] = round(e - gps[0], 4)
    ov['north_delta_m'] = round(n - gps[1], 4)
    if u is None:
        g, hit = surf(e, n)
        u = g + eye
    else:
        hit = ('given',)
    ov['eye_height_m'] = eye
    ov['absolute_u_m'] = round(u, 4)
    ov['heading_delta_deg'] = round((heading - inf0['heading'] + 540) % 360 - 180, 3)
    if hz is not None:
        ov['rectified_horizon_y_fraction'] = hz
    pid = f'sbs-p143-{key[:6]}-{tag}'
    cam, inf = P.camera(R[cid], ov, pid)
    cam['pose_confidence'] = 'C'; cam['pose_reason'] = 'ADR0143 diagnostic probe only'
    probes.append(cam)
    plan.append({'probe': pid, 'base': cid, 'override': {k: ov[k] for k in ('east_delta_m', 'north_delta_m', 'eye_height_m', 'absolute_u_m', 'heading_delta_deg') if k in ov},
                 'rectified_horizon': ov.get('rectified_horizon_y_fraction'), 'pos': cam['pos'], 'heading_grid_deg': round(inf['heading'], 3),
                 'surface': str(hit), 'note': note, 'aspect': R[cid]['width'] / R[cid]['height']})
    print(pid, cam['pos'], round(inf['heading'], 2), hit)


# ---- 494288 Putry deck NW-bound: dash = graph centreline (Andersa 2 lanes oneway)
A0, A1, A2 = (-458.0, -56.0), (-512.1, -11.7), (-542.1, 10.9)
def deck_pt(s, lat):
    """s = metres from A1 along the NW direction (negative = back towards A0), lat = metres right of the dash."""
    if s >= 0: p, q = A1, A2
    else: p, q = A0, A1
    L = math.dist(p, q); ux, uy = (q[0] - p[0]) / L, (q[1] - p[1]) / L
    base = A1
    return base[0] + s * ux + lat * uy, base[1] + s * uy - lat * ux, (math.degrees(math.atan2(ux, uy)) % 360)
K = '494288258686575'
if RND == 'r1':
    for s in (21.3, 14.0, 7.0, 0.0, -8.0):
        e, n, t = deck_pt(s, 1.1)
        probe(K, f's{int(round(s)):+d}', e, n, 1.3, t + 6.8, 0.716, f'{s} m from A1, 1.1 m right of dash, eye 1.3, heading tangent+6.8 (photo road VP x 441)')
    e, n, t = deck_pt(7.0, 1.1); probe(K, 'mh', e, n, 1.3, 309.37, 0.716, 's 7, Mapillary heading')
    e, n, t = deck_pt(7.0, 1.1); probe(K, 'e17', e, n, 1.7, t + 6.8, 0.716, 's 7, eye 1.7')

# ---- 810896 SE-bound Andersa main carriageway (layer 1), camera currently 5.0 m left of its centreline (in the median)
K = '810896133189484'
if RND == 'r1':
    cid = 'sbs-g3-b-' + K
    c0 = next(c for c in P.S.read(P.REGION / 'sbs_cameras.json')['cameras'] if c['id'] == cid)
    e0, n0 = c0['pos'][:2]
    hd = math.radians(128.1)
    ux, uy = math.sin(hd), math.cos(hd); rx, ry = uy, -ux   # right of SE direction = SW
    for tag, right, fwd in (('l0', 3.0, 0), ('r0', 7.0, 0), ('lb', 3.0, -10), ('lf', 3.0, 10)):
        probe(K, tag, e0 + right * rx + fwd * ux, n0 + right * ry + fwd * uy, 1.7, 78.674, None, f'{right} m right (SW) of production, {fwd} m along SE: left/right lane of SE-bound Andersa')


# ---- G3-A richlv 2020 sequence (car travelling WNW on the northern slip, camera looking ~60 deg left)
if RND == 'r1':
    K = '320326319617139'
    probe(K, 'p128', 541.5, -690.4, 0.9, 244.0003582, 0.7204818, 'ADR 0128 probe pose, exact (promotion candidate)', u=140.52, base_prefix='sbs-g3-a-')
    K = '482392746429891'
    for tag, e, n, eye, hd, hz in (('sa', 531.5, -685.0, 0.9, 246.09, 0.75), ('sb', 531.5, -685.0, 0.9, 242.69, 0.75),
                                   ('sc', 528.2, -682.4, 0.9, 246.09, 0.75), ('sd', 531.5, -685.0, 1.5, 246.09, 0.75)):
        probe(K, tag, e, n, eye, hd, hz, f'E {e} N {n} eye {eye} heading {hd} horizon {hz} (0128 shift of the same sequence = +3.3/-2.6 m, +3.4 deg)', base_prefix='sbs-g3-a-')

prod = {c['id']: c for c in P.S.read(P.REGION / 'sbs_cameras.json')['cameras']}
EXTRA = ['sbs-g3-b-837235577143499'] if RND == 'r1' else []
probes += [prod[b] for b in sorted({p['base'] for p in plan} | set(EXTRA))]
json.dump({'schema': 'kamion/sbs-cameras/1', 'frame': 'E,N,absolute U', 'cameras': probes}, open(OUT / 'cameras.json', 'w'), indent=1)
json.dump(plan, open(OUT / 'plan.json', 'w'), indent=1)
for asp, name in ((4 / 3, 'ids-4x3.txt'), (16 / 9, 'ids-16x9.txt')):
    ids = [p['probe'] for p in plan if abs(p['aspect'] - asp) < 0.05]
    bases = sorted({p['base'] for p in plan if abs(p['aspect'] - asp) < 0.05})
    if asp > 1.5: bases += EXTRA
    (OUT / name).write_text(','.join(ids + bases))
