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
    e, n, t = deck_pt(21.3, 1.1)
    probe(K, 'lat', e, n, 1.3, t + 6.8, 0.716, 'production station, 1.1 m right of the dash (lateral fix only), eye 1.3, heading tangent+6.8')
    for tag, s_, eye in (('f0', -32.0, 1.0), ('f1', -32.0, 1.3), ('f2', -20.0, 1.15), ('f3', -45.0, 1.15)):
        e, n, t = deck_pt(s_, 0.85)
        probe(K, tag, e, n, eye, t + 7.5, 0.725, f'fit494b: s {s_} m, 0.85 m right of the dash, eye {eye}, heading tangent+7.5, horizon 0.725 (roll -3.7 not renderable)')

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

if RND == 'r2':
    K = '494288258686575'
    for tag, s_, lat, eye in (('g0', -32.0, 1.7, 1.15), ('g1', -32.0, 2.1, 1.15), ('g2', -26.0, 1.7, 1.15), ('g3', -38.0, 1.7, 1.15)):
        e, n, t = deck_pt(s_, lat)
        probe(K, tag, e, n, eye, t + 7.5, 0.725, f's {s_} m, {lat} m right of the graph centreline (generated dash ~0.85 m right of it), eye {eye}, heading tangent+7.5')
    K = '810896133189484'
    cid = 'sbs-g3-b-' + K
    c0 = next(c for c in P.S.read(P.REGION / 'sbs_cameras.json')['cameras'] if c['id'] == cid)
    e0, n0 = c0['pos'][:2]
    hd = math.radians(128.1); ux, uy = math.sin(hd), math.cos(hd); rx, ry = uy, -ux
    for tag, right, eye in (('m0', 3.5, 1.0), ('m1', 5.0, 1.0), ('m2', 3.5, 1.6)):
        probe(K, tag, e0 + right * rx, n0 + right * ry, eye, 78.674, None, f'{right} m SW of production (SE-bound Andersa, kerb 2.5H left from the photo), eye {eye}')
    K = '482392746429891'
    for tag, e, n, hd_ in (('sa', 531.5, -685.0, 246.09), ('pf', 537.383, -690.585, 252.472), ('pm', 534.4, -687.8, 249.3)):
        probe(K, tag, e, n, 0.9, hd_, 0.75, f'E {e} N {n} heading {hd_} eye 0.9 (pf = pier-column resection, piers low confidence)', base_prefix='sbs-g3-a-')

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
