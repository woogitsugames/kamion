"""ADR 0140: pinhole projection of world points (E,N,U) through an SBS camera dict (pos, look_at, vertical fov_deg)."""
import math
import numpy as np

# Generated portal andersa-putry-approach-gantry after ADR 0127 (instances_2_4.json, sign_gantry_14_70)
FEET = {'L_nb_west': (-267.212, -212.934), 'R_nb_east': (-258.388, -202.066)}  # footing instances
FOOT_U = 130.059
PORTAL_H = 7.0  # sign_gantry_14_70: 14 m span, 7.0 m (rule height, ADR 0127)


def basis(cam):
    p = np.array(cam['pos'], float); f = np.array(cam['look_at'], float) - p
    f /= np.linalg.norm(f)
    r = np.cross(f, [0, 0, 1.0]); r /= np.linalg.norm(r)
    u = np.cross(r, f)
    return p, f, r, u


def project(cam, pts, w, h):
    p, f, r, u = basis(cam)
    tv = math.tan(math.radians(cam['fov_deg']) / 2); th = tv * w / h
    out = []
    for q in pts:
        d = np.array(q, float) - p
        z = d @ f
        out.append(((1 + (d @ r) / z / th) / 2, (1 - (d @ u) / z / tv) / 2))
    return out  # fractions of width / height


def portal_points():
    pts = {}
    for k, (e, n) in FEET.items():
        pts[k + '_foot'] = (e, n, FOOT_U)
        pts[k + '_top'] = (e, n, FOOT_U + PORTAL_H)
    return pts
