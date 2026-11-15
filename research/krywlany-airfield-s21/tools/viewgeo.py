"""Line-of-sight from observer points to runway 09R/27L over NMPT 2023 (0.5 m, leafy) and NMT (1 m, WCS).

Formula (README §3):
  z_eye = z_ground(obs) + h_eye ; alpha(s) = atan((z(s) - z_eye) / s)
  target near edge T_n (distance D_n), far edge T_f (D_f = D_n + 30 m along same bearing approx.)
  obstacle angle A_obs = max alpha(s) over 3 m <= s <= D_n - 2 m (surface = NMPT)
  visible if alpha(T_n) > A_obs (margin = alpha(T_n) - A_obs, deg)
  vertical extent of runway = alpha(T_n) - alpha(T_f)
Output JSON per point.
"""
import sys, json, math
import numpy as np
from pyproj import Transformer

T = Transformer.from_crs(4326, 2180, always_xy=True)
TI = Transformer.from_crs(2180, 4326, always_xy=True)
S = sys.argv[1]
nmpt = np.load(S + '/dem/nmpt.npy'); mp = json.load(open(S + '/dem/nmpt.json'))
nmt = np.load(S + '/dem/nmt/nmt.npy'); mt = json.load(open(S + '/dem/nmt/nmt.json'))


def sample(arr, meta, e, n):
    c = (e - meta['E0']) / meta['cell']; r = (meta['N1'] - n) / meta['cell']
    i, j = int(math.floor(r)), int(math.floor(c))
    if i < 0 or j < 0 or i >= arr.shape[0] or j >= arr.shape[1]:
        return float('nan')
    return float(arr[i, j])


def ground(e, n):
    """min NMPT in 1.5 m window (removes cars/poles) — road surface."""
    vals = [sample(nmpt, mp, e + dx, n + dy) for dx in (-0.75, 0, 0.75) for dy in (-0.75, 0, 0.75)]
    vals = [v for v in vals if not math.isnan(v)]
    return min(vals) if vals else float('nan')


# runway axis (OSM way 958211700 nodes 8866086772 -> 8866086773)
W = T.transform(23.1633183, 53.1010976); E = T.transform(23.1831747, 53.1007143)
ax = np.array(E) - np.array(W); L = float(np.hypot(*ax)); u = ax / L; nrm = np.array([-u[1], u[0]])  # nrm points north-ish
HALF = 15.0
# M58: pavement W end s=-11.4, E end s=1342.4 relative to node 8866086772 -> clamp s
S0, S1 = -11.4, 1342.4


def nearest_edge(p):
    p = np.array(p)
    s = float(np.dot(p - np.array(W), u)); s = min(max(s, S0), S1)
    c = float(np.dot(p - np.array(W), nrm))
    side = 1 if c >= 0 else -1
    near = np.array(W) + u * s + nrm * side * HALF
    far = np.array(W) + u * s + nrm * -side * HALF
    return near, far, s, c


def los(obs, target, h, step=0.5):
    e0, n0 = obs
    zg = ground(e0, n0); ze = zg + h
    v = np.array(target) - np.array(obs); D = float(np.hypot(*v)); d = v / D
    zt = sample(nmpt, mp, *target)
    at = math.degrees(math.atan2(zt - ze, D))
    best = (-90, None, None)
    clear = (1e9, None)
    s = 3.0
    while s < D - 1.0:
        e, n = e0 + d[0] * s, n0 + d[1] * s
        z = sample(nmpt, mp, e, n)
        if not math.isnan(z):
            a = math.degrees(math.atan2(z - ze, s))
            if a > best[0]:
                best = (a, s, z)
            cl = ze + (zt - ze) * s / D - z  # line of sight height above surface
            if cl < clear[0] and s < D - 5.0:
                clear = (cl, s)
        s += step
    globals()['_last_clear'] = clear
    return dict(D=round(D, 1), z_ground=round(zg, 2), z_eye=round(ze, 2), z_target=round(zt, 2), alpha_target_deg=round(at, 3),
                alpha_obs_deg=round(best[0], 3), obs_at_m=round(best[1], 1) if best[1] else None,
                obs_z=round(best[2], 2) if best[2] else None, obs_h_above_eye=round(best[2] - ze, 2) if best[2] else None,
                margin_deg=round(at - best[0], 3), visible=at > best[0], bearing_deg=round(math.degrees(math.atan2(d[0], d[1])) % 360, 1))


pts = json.load(open(sys.argv[2]))
out = []
for p in pts:
    if 'en' in p:
        e, n = p['en']
    else:
        e, n = T.transform(p['lon'], p['lat'])
    near, far, s, c = nearest_edge((e, n))
    if 'target_s' in p:
        s = p['target_s']; side = 1 if c >= 0 else -1
        near = np.array(W) + u * s + nrm * side * HALF; far = np.array(W) + u * s - nrm * side * HALF
    rec = dict(id=p['id'], name=p['name'], E=round(e, 1), N=round(n, 1))
    lo, la = TI.transform(e, n); rec['lat'] = round(la, 6); rec['lon'] = round(lo, 6)
    rec['s_target'] = round(s, 1); rec['c_obs'] = round(c, 1)
    rec['nmt_ground'] = round(sample(nmt, mt, e, n), 2)
    for h in (2.5, 1.7):
        # cross-section: 31 points from near edge to far edge (1 m step)
        nv = 0; clears = []
        for k in range(31):
            tp = near + (far - near) * k / 30.0
            r_ = los((e, n), tp, h)
            c_ = globals()['_last_clear']
            clears.append(round(c_[0], 2))
            if c_[0] > -0.10:
                nv += 1
        a = los((e, n), near, h)
        a['clearance_near_m'] = round(globals()['_last_clear'][0], 2); a['clearance_near_at_m'] = globals()['_last_clear'][1]
        b = los((e, n), far, h)
        a['clearance_far_m'] = round(globals()['_last_clear'][0], 2); a['clearance_far_at_m'] = globals()['_last_clear'][1]
        a['cross_section_visible_of_31'] = nv
        a['alpha_far_deg'] = b['alpha_target_deg']; a['far_visible'] = b['visible']; a['far_margin_deg'] = b['margin_deg']
        a['runway_vertical_extent_deg'] = round(a['alpha_target_deg'] - b['alpha_target_deg'], 4)
        rec[f'h{h}'] = a
    out.append(rec)
json.dump(out, open(sys.argv[3], 'w'), ensure_ascii=False, indent=1)
for r in out:
    for h in ('h2.5', 'h1.7'):
        x = r[h]
        print(r['id'], h, 'D', x['D'], 'brg', x['bearing_deg'], 'zg', x['z_ground'], 'nmt', r['nmt_ground'], 'zt', x['z_target'], 'aT', x['alpha_target_deg'],
              'aObs', x['alpha_obs_deg'], '@', x['obs_at_m'], 'h_obs', x['obs_h_above_eye'], 'vis', x['visible'], 'far', x['far_visible'], 'ext', x['runway_vertical_extent_deg'], 'clrN', x['clearance_near_m'], '@', x['clearance_near_at_m'], 'clrF', x['clearance_far_m'], '@', x['clearance_far_at_m'], 'xs', x['cross_section_visible_of_31'])
