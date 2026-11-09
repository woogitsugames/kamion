"""Facade kit per building typology (LOD0 detail on top of the walls built by streetscape.buildings_mesh).

hall    cladding schemes (one colour / dark lower band / accent top band; band edges moved off the openings),
        projecting parapet coping, vertical corner trims, downpipes with hopper heads through the parapet or
        an eaves gutter on the long walls (35 % of halls), canopies over personnel doors, a drive-in sectional
        door on some main facades, roof smoke vents, fascia signs with functional lettering (instances).
office  punched or ribbon windows (upper storeys), entrance canopy, downpipes at two corners, sign over the
        entrance (BIURO / RECEPCJA / SERWIS, instances).
block   wielka płyta: raw large panels with joints (30 %) or ETICS insulation with accent colour fields on the
        stairwell axis and on the gable ends (70 %); balconies / loggia slabs with sheet balustrades on the side
        away from the entrances; entrance canopies; ventilation stacks and lift machine rooms on the roof.
house   gutters on both eaves with corner downpipes, chimney; 12 % of small single-storey houses are wooden
        (horizontal boarding, natural or green-painted: the Podlasie wooden house).
Everything is deterministic (hash of the building id). Only the LOD0 layer ('buildings') gets the kit; LOD1
keeps the plain prism so the Low/Medium variant stays within its size budget. Dimensions WORKING_VALUE.
"""

from __future__ import annotations

import hashlib
import math

import numpy as np
import shapely

ACCENT_HALL = ["hall_wall_accent_blue", "hall_wall_accent_red", "hall_wall_accent_green", "hall_wall_graphite"]
ACCENT_PLASTER = ["plaster_accent_terracotta", "plaster_accent_green", "plaster_accent_ochre", "plaster_accent_grey"]
L0 = "buildings"


def hfloat(*key):
    return int(hashlib.sha1(":".join(str(k) for k in key).encode()).hexdigest()[:8], 16) / 0xFFFFFFFF


def hpick(seq, *key):
    return seq[int(hfloat(*key) * len(seq)) % len(seq)]


def v3(p, z):
    return np.array([p[0], p[1], z], float)


# ------------------------------------------------------------------------------------------- schemes
def hall_scheme(key, wall):
    u = hfloat(key, "scheme")
    if u < 0.40:
        s = {"low": None, "top": None}
    elif u < 0.75:
        s = {"low": ("hall_wall_graphite", 2.4 + hfloat(key, "lowh") * 1.0), "top": None}
    else:
        s = {"low": None, "top": (hpick(ACCENT_HALL, key, "top"), 1.0 + hfloat(key, "toph") * 0.8)}
    s["gutter"] = hfloat(key, "gutter") < 0.35
    s["wall"] = wall
    return s


def safe_z(z, ops, lo, hi, max_frac=1.0):
    """Move a horizontal band edge out of any opening it would cut (above the highest opening it crosses)."""
    for _ in range(6):
        hit = [o for o in ops if o[2] + 0.02 < z < o[3] - 0.02]
        if not hit:
            break
        z = max(o[3] for o in hit) + 0.3
    return z if lo + 0.2 < z < min(hi - 0.2, lo + max_frac * (hi - lo)) else None


def safe_u(u, ops, L):
    for _ in range(6):
        hit = [o for o in ops if o[0] - 0.05 < u < o[1] + 0.05]
        if not hit:
            break
        o = hit[0]
        u = o[0] - 0.15 if (u - o[0]) < (o[1] - u) else o[1] + 0.15
    return u if 0.3 < u < L - 0.3 else None


def wall_pieces(wwo, acc, a, d, nout, L, zb, zt, ops, u_acc, vref, zsplits, usplits, mat_fn, layer=L0):
    """Wall split into rectangles (u ranges x z ranges) of different materials; openings are clipped to every
    piece (splits are moved off the openings beforehand, so no fake jambs or sills appear)."""
    zs = [zb] + sorted({z for z in zsplits if z is not None and zb + 0.05 < z < zt - 0.05}) + [zt]
    us = [0.0] + sorted({u for u in usplits if u is not None and 0.05 < u < L - 0.05}) + [L]
    for u0, u1 in zip(us, us[1:]):
        for z0, z1 in zip(zs, zs[1:]):
            mat = mat_fn(u0, u1, z0, z1)
            pc = []
            for o in ops:
                ua, ub = max(o[0], u0), min(o[1], u1)
                va, vb = max(o[2], z0), min(o[3], z1)
                if ub - ua > 0.05 and vb - va > 0.05:
                    pc.append((ua - u0, ub - u0, va, vb, *o[4:]))
            wwo(acc, layer, mat, a + d * u0, d, nout, u1 - u0, z0, z1, pc, u0=u_acc + u0, vref=vref)


# ------------------------------------------------------------------------------------------- details
def coping(acc, a, c, nout, zt, mat="hall_flashing"):
    """Parapet coping: 0.06 m proud, 0.1 m over the wall top (drip edge)."""
    d = c - a
    L = float(np.hypot(*d))
    d = d / L
    ctr = (a + c) / 2 + nout * 0.03
    acc.box(L0, mat, v3(ctr, zt + 0.03), np.append(d * (L / 2 + 0.06), 0), np.append(nout * 0.11, 0), [0, 0, 0.05])


def corner_trim(acc, p, n_a, n_b, z0, z1, mat="hall_flashing"):
    """L-shaped corner flashing as one box at the outer corner (bisector of the two outward normals)."""
    bis = n_a + n_b
    ln = float(np.hypot(*bis))
    if ln < 0.3:
        return
    bis = bis / ln
    t = np.array([-bis[1], bis[0]])
    acc.box(L0, mat, v3(p + bis * 0.04, (z0 + z1) / 2), np.append(t * 0.09, 0), np.append(bis * 0.06, 0),
            [0, 0, (z1 - z0) / 2])


def downpipe(acc, a, d, nout, u, z0, z1, hopper=True, mat="downpipe"):
    """Square downpipe 0.1 m, 0.05 m off the wall, shoe kicked out at the bottom, hopper head at the top."""
    p = a + d * u + nout * 0.10
    acc.box(L0, mat, v3(p, (z0 + 0.3 + z1) / 2), np.append(d * 0.05, 0), np.append(nout * 0.05, 0),
            [0, 0, (z1 - z0 - 0.3) / 2])
    acc.box(L0, mat, v3(p + nout * 0.08, z0 + 0.18), np.append(d * 0.05, 0), np.append(nout * 0.12, 0), [0, 0, 0.12])
    if hopper:
        acc.box(L0, mat, v3(p + nout * 0.03, z1 + 0.15), np.append(d * 0.16, 0), np.append(nout * 0.10, 0), [0, 0, 0.17])


def gutter(acc, a, c, nout, z, mat="gutter", proud=0.12):
    d = c - a
    L = float(np.hypot(*d))
    d = d / L
    ctr = (a + c) / 2 + nout * (proud + 0.06)
    acc.box(L0, mat, v3(ctr, z - 0.06), np.append(d * (L / 2 + 0.05), 0), np.append(nout * 0.07, 0), [0, 0, 0.06])


def canopy(acc, a, d, nout, u, w, z, depth, mat="canopy_steel", posts=False, zg=None):
    p = a + d * u + nout * (depth / 2)
    acc.box(L0, mat, v3(p, z), np.append(d * w / 2, 0), np.append(nout * depth / 2, 0), [0, 0, 0.06])
    if posts and zg is not None:
        for sg in (-1, 1):
            q = a + d * (u + sg * (w / 2 - 0.12)) + nout * (depth - 0.12)
            acc.box(L0, mat, v3(q, (zg + z) / 2), [0.05, 0, 0], [0, 0.05, 0], [0, 0, (z - zg) / 2])


def downpipe_positions(L, ops, key, spacing, margin=1.2):
    out = []
    if L < 6:
        return out
    n = max(1, int(round(L / spacing)))
    ph = hfloat(key, "dp") - 0.5
    for i in range(n):
        u = (i + 0.5 + ph * 0.4) * L / n
        u = safe_u(u, [(o[0] - 0.4, o[1] + 0.4, *o[2:]) for o in ops], L)
        if u is not None and margin < u < L - margin:
            out.append(u)
    return out


def roof_vents(acc, poly, z, key, kind):
    """kind 'hall': smoke vents (klapy dymowe) + small fan boxes; 'block': ventilation stacks along the
    long axis and lift machine rooms; returns triangles added (approx)."""
    r = poly.minimum_rotated_rectangle
    c = np.asarray(r.exterior.coords)[:4]
    e = [np.hypot(*(c[(i + 1) % 4] - c[i])) for i in range(4)]
    k = 0 if e[0] >= e[1] else 1
    along = (c[(k + 1) % 4] - c[k]) / max(e[k], 1e-6)
    across = np.array([-along[1], along[0]])
    ctr = np.asarray(r.centroid.coords[0])
    Lr, Wr = max(e), min(e)
    inner = poly.buffer(-2.0)
    if inner.is_empty:
        return
    shapely.prepare(inner)
    if kind == "hall":
        for i, t in enumerate(np.arange(-Lr / 2 + 6, Lr / 2 - 6, 11.0)):
            for j, s in enumerate((-Wr * 0.25, Wr * 0.25)):
                if hfloat(key, "vent", i, j) > 0.45:
                    continue
                p = ctr + along * (t + 3.0) + across * s
                if not inner.contains(shapely.Point(*p)):
                    continue
                acc.box(L0, "roof_vent", v3(p, z + 0.25), np.append(along * 1.0, 0), np.append(across * 0.6, 0),
                        [0, 0, 0.25])
                q = p + along * 2.4
                if hfloat(key, "fan", i, j) < 0.5 and inner.contains(shapely.Point(*q)):
                    acc.box(L0, "roof_vent", v3(q, z + 0.35), np.append(along * 0.35, 0), np.append(across * 0.35, 0),
                            [0, 0, 0.35])
    elif kind == "block":
        for i, t in enumerate(np.arange(-Lr / 2 + 2.0, Lr / 2 - 1.5, 3.0)):
            for s in (-0.9, 0.9):
                if hfloat(key, "stack", i, s) < 0.35:
                    continue
                p = ctr + along * t + across * s
                if inner.contains(shapely.Point(*p)):
                    acc.box(L0, "balcony_slab", v3(p, z + 0.55), np.append(along * 0.45, 0), np.append(across * 0.3, 0),
                            [0, 0, 0.55])
        nmr = max(1, int(Lr // 30))
        for i in range(nmr):
            t = (i + 0.5) * Lr / nmr - Lr / 2
            p = ctr + along * t
            if inner.contains(shapely.Point(*p)):
                acc.box(L0, "balcony_slab", v3(p, z + 1.1), np.append(along * 1.4, 0), np.append(across * 1.6, 0),
                        [0, 0, 1.1])


def balcony(acc, a, d, nout, u, w, zf, depth=1.15):
    """Slab at floor level zf + front and side sheet balustrades (1.0 m)."""
    p = a + d * u + nout * (depth / 2)
    acc.box(L0, "balcony_slab", v3(p, zf - 0.09), np.append(d * (w / 2 + 0.1), 0), np.append(nout * depth / 2, 0),
            [0, 0, 0.09])
    f = a + d * u + nout * (depth - 0.03)
    acc.box(L0, "balcony_panel", v3(f, zf + 0.5), np.append(d * (w / 2 + 0.1), 0), np.append(nout * 0.03, 0),
            [0, 0, 0.5])
    for sg in (-1, 1):
        s = a + d * (u + sg * (w / 2 + 0.07)) + nout * (depth / 2)
        acc.box(L0, "balcony_panel", v3(s, zf + 0.5), np.append(d * 0.03, 0), np.append(nout * depth / 2, 0), [0, 0, 0.5])


def chimney(acc, rect_poly, zridge, key):
    c = np.asarray(rect_poly.exterior.coords)[:4]
    e = [np.hypot(*(c[(i + 1) % 4] - c[i])) for i in range(4)]
    k = 0 if e[0] >= e[1] else 1
    along = (c[(k + 1) % 4] - c[k]) / max(e[k], 1e-6)
    ctr = np.asarray(rect_poly.centroid.coords[0])
    t = (hfloat(key, "chim") - 0.5) * max(e) * 0.5
    p = ctr + along * t
    acc.box(L0, "chimney_brick", v3(p, zridge - 0.2), np.append(along * 0.3, 0),
            np.append(np.array([-along[1], along[0]]) * 0.25, 0), [0, 0, 1.0])


def sign_instance(code, a, d, nout, u, z, src):
    p = a + d * u + nout * 0.05
    yaw = math.atan2(nout[1], nout[0]) - math.pi / 2
    return {"p": f"facade_sign_{code}", "e": round(float(p[0]), 3), "n": round(float(p[1]), 3), "z": round(float(z), 3),
            "yaw": round(float(yaw), 4), "src": src}
