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
Everything is deterministic (hash of the building id). The LOD0 layer ('buildings') gets the full kit. LOD1
('buildings_low': the Low/Medium tiers away from the route and High beyond the LOD switch) gets a cheap copy of the
silhouette pieces - gutters, downpipes, door canopies, chimneys - as single boxes without the faces that touch the
wall or never face the street (4-10 triangles each instead of 12-36), so a tier changes the detail density, never
the building (review r6 / HANDOVER pkt 7, ADR 0012 addendum r7). Balconies stay LOD0-only (open issue: one block
facade would cost ~2-3 k triangles). Dimensions WORKING_VALUE.
"""

from __future__ import annotations

import hashlib
import math

import numpy as np
import shapely

from . import facade_atlas as FA

ACCENT_HALL = ["hall_wall_accent_blue", "hall_wall_accent_red", "hall_wall_accent_green", "hall_wall_graphite"]
ACCENT_PLASTER = ["plaster_accent_terracotta", "plaster_accent_green", "plaster_accent_ochre", "plaster_accent_grey"]
L0 = "buildings"
L1 = "buildings_low"
# LOD1 material merge: every material is one submesh = one draw per chunk, so the LOD1 silhouette pieces reuse a
# material of the same tone that LOD1 already draws: gutter, canopy and leveller steel share the downpipe grey
# (lin. 0.20-0.30), the black dock shelter (0.025) and the dock door reveals take the graphite coping (0.045)
L1_MAT = {"gutter": "downpipe", "canopy_steel": "downpipe", "steel_checker": "downpipe",
          "roof_metal_graphite": "hall_flashing", "dock_shelter": "hall_flashing", "reveal_hall": "hall_flashing"}


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


def wall_pieces(wwo, acc, a, d, nout, L, zb, zt, ops, u_acc, vref, zsplits, usplits, mat_fn, layer=L0, **kw):
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
                    m = o[6]
                    if isinstance(m, tuple):          # atlas cells: keep the part of the cell this piece shows
                        fu = lambda u, m=m, o=o: m[2] + (m[3] - m[2]) * (u - o[0]) / (o[1] - o[0])
                        fv = lambda v, m=m, o=o: m[4] + (m[5] - m[4]) * (v - o[2]) / (o[3] - o[2])
                        m = (m[0], m[1], fu(ua), fu(ub), fv(va), fv(vb))
                    pc.append((ua - u0, ub - u0, va, vb, o[4], o[5], m))
            wwo(acc, layer, mat, a + d * u0, d, nout, u1 - u0, z0, z1, pc, u0=u_acc + u0, vref=vref, **kw)


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
    # LOD1: one pipe from the ground to the hopper top, front + two sides only (6 triangles)
    zt1 = z1 + (0.32 if hopper else 0.0)
    acc.box(L1, L1_MAT.get(mat, mat), v3(p, (z0 + zt1) / 2), np.append(d * 0.05, 0), np.append(nout * 0.05, 0), [0, 0, (zt1 - z0) / 2],
            skip=(0, 1, 2))


def gutter(acc, a, c, nout, z, mat="gutter", proud=0.12):
    d = c - a
    L = float(np.hypot(*d))
    d = d / L
    ctr = (a + c) / 2 + nout * (proud + 0.06)
    acc.box(L0, mat, v3(ctr, z - 0.06), np.append(d * (L / 2 + 0.05), 0), np.append(nout * 0.07, 0), [0, 0, 0.06])
    # LOD1: same box without the wall-side face and the two end caps (6 triangles)
    acc.box(L1, L1_MAT.get(mat, mat), v3(ctr, z - 0.06), np.append(d * (L / 2 + 0.05), 0), np.append(nout * 0.07, 0), [0, 0, 0.06],
            skip=(2, 4, 5))


def canopy(acc, a, d, nout, u, w, z, depth, mat="canopy_steel", posts=False, zg=None):
    p = a + d * u + nout * (depth / 2)
    acc.box(L0, mat, v3(p, z), np.append(d * w / 2, 0), np.append(nout * depth / 2, 0), [0, 0, 0.06])
    acc.box(L1, L1_MAT.get(mat, mat), v3(p, z), np.append(d * w / 2, 0), np.append(nout * depth / 2, 0), [0, 0, 0.06], skip=(2,))
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


def _aq(acc, P0, P1, P2, P3, uv):
    acc.quad(L0, "facade_atlas", P0, P1, P2, P3, uv=uv)


def _abox(acc, c, ax, ay, az, front=None, sw="pvc_white", skip=()):
    """Box in the facade atlas: face +ay (the street side) shows `front` (uv corners), the others a swatch.
    skip: 0 bottom, 1 top, 3 front, 4 -ax side, 5 +ax side."""
    c, ax, ay, az = (np.asarray(x, float) for x in (c, ax, ay, az))
    su = FA.swatch_uv(sw)
    if 3 not in skip:
        _aq(acc, c + ay - ax - az, c + ay + ax - az, c + ay + ax + az, c + ay - ax + az, front or su)
    if 5 not in skip:
        _aq(acc, c + ax + ay - az, c + ax - ay - az, c + ax - ay + az, c + ax + ay + az, su)
    if 4 not in skip:
        _aq(acc, c - ax - ay - az, c - ax + ay - az, c - ax + ay + az, c - ax - ay + az, su)
    if 1 not in skip:
        _aq(acc, c - ax + ay + az, c + ax + ay + az, c + ax - ay + az, c - ax - ay + az, su)
    if 0 not in skip:
        _aq(acc, c - ax - ay - az, c + ax - ay - az, c + ax + ay - az, c - ax + ay - az, su)


# satellite dishes: every dish of the city looks at the same satellite. Hot Bird 13 deg E from Białystok (53.13 N,
# 23.16 E): azimuth ~192 deg, elevation ~28 deg (geometry of the geostationary arc; WORKING_VALUE to +-2 deg); an
# offset dish is tilted ~20 deg less than the beam, so its face looks ~8 deg above the horizon
DISH_AZ = np.array([math.sin(math.radians(192.0)), math.cos(math.radians(192.0)), 0.0])
DISH_FACE = DISH_AZ * math.cos(math.radians(8.0)) + np.array([0, 0, math.sin(math.radians(8.0))])
BAL_GAP = 0.10                  # clear gap between the slab and the balustrade infill, m
BAL_V = (0.08, 1.02)            # rows of the `balf` cell the infill shows (bottom rail ... top rail), m


def balcony(acc, a, d, nout, u, w, zf, depth=1.15, variant=0, key="", inner=True):
    """Balcony at floor level zf (ADR 0094, review s9 P1-5: was a closed dark box).
    Slab 0.16 m, 4 cm proud of the balustrade on its three free sides. Balustrade = a `balf` cell of the facade atlas
    (sheet, bars, boards, glass, cloth - the variant the LOD1 row shows) on the front AND on both sides, both faces,
    carried 10 cm clear of the slab on corner posts (the gap shows the sky / the wall behind: the balustrade reads as
    a screen in front of the slab, not as the side of a box); 5 x 4 cm handrail on the three sides.
    inner: also the faces only an eye level with the balcony or above it can see - the balustrade faces that look
    into the balcony, the slab top, the handrail tops, the corner posts (10 cm, hidden behind the slab edge from below).
    The generator passes it for the two lowest storeys only: 20 instead of 34 triangles per balcony above them (the
    Low tier draws LOD0 along the route: r1 of ADR 0094 cost +4.6...5.0 % triangles on the block cameras).
    ADR 0081: 14 % glazed in above the balustrade, 18 % with a satellite dish, 30 % with a laundry line (WORKING_VALUE)."""
    d3, n3 = np.append(d, 0.0), np.append(nout, 0.0)
    hw = w / 2 + 0.1
    dep = depth - 0.03                               # balustrade line from the wall
    p = a + d * u + nout * ((depth + 0.01) / 2)
    acc.box(L0, "balcony_slab", v3(p, zf - 0.08), d3 * (hw + 0.04), n3 * ((depth + 0.01) / 2), [0, 0, 0.08],
            skip=(2,) if inner else (1, 2))
    cu, cv, cw, _ = FA.cell("balf", variant)
    va, vb = cv + BAL_V[0], cv + BAL_V[1]
    z0 = np.array([0, 0, BAL_GAP])
    up = np.array([0, 0, BAL_GAP + BAL_V[1] - BAL_V[0]])
    f = v3(a + d * u + nout * dep, zf)
    A_, B_ = f - d3 * hw, f + d3 * hw
    _aq(acc, A_ + z0, B_ + z0, B_ + up, A_ + up, [[cu, va], [cu + cw, va], [cu + cw, vb], [cu, vb]])
    if inner:
        _aq(acc, B_ - n3 * 0.04 + z0, A_ - n3 * 0.04 + z0, A_ - n3 * 0.04 + up, B_ - n3 * 0.04 + up,
            [[cu + cw, va], [cu, va], [cu, vb], [cu + cw, vb]])
    w0 = v3(a + d * u, zf)
    for sg in (-1, 1):
        # side screens: the first `dep` metres of the same cell, its end post at the free corner
        sw_, so_ = w0 + d3 * sg * hw, w0 + d3 * sg * hw + n3 * dep
        uw, uo = cu + dep, cu
        q = [(sw_, uw), (so_, uo)] if sg < 0 else [(so_, uo), (sw_, uw)]      # CCW seen from outside
        (P0, u0_), (P1, u1_) = q
        _aq(acc, P0 + z0, P1 + z0, P1 + up, P0 + up, [[u0_, va], [u1_, va], [u1_, vb], [u0_, vb]])
        if inner:
            _aq(acc, P1 + z0, P0 + z0, P0 + up, P1 + up, [[u1_, va], [u0_, va], [u0_, vb], [u1_, vb]])
        if inner:           # corner post under the screen (front + outer face)
            acc.box(L0, "downpipe", so_ - d3 * sg * 0.02 - n3 * 0.02 + [0, 0, BAL_GAP / 2], d3 * 0.02, n3 * 0.02,
                    [0, 0, BAL_GAP / 2], skip=(0, 1, 2, 4 if sg > 0 else 5))
    # handrail: 5 x 4 cm on the three open sides, 3 cm proud of the infill (top and outer faces only)
    rail = up + [0, 0, 0.01]
    acc.box(L0, "downpipe", f + n3 * 0.01 + rail, d3 * (hw + 0.03), n3 * 0.025, [0, 0, 0.02],
            skip=(0, 2, 4, 5) if inner else (0, 1, 2, 4, 5))
    for sg in (-1, 1):
        acc.box(L0, "downpipe", w0 + d3 * sg * hw + n3 * dep / 2 + rail, d3 * 0.025, n3 * dep / 2,
                [0, 0, 0.02], skip=(0, 2, 3, 4 if sg > 0 else 5) + (() if inner else (1,)))
    up = np.array([0, 0, 1.05])
    if hfloat(key, "glz") < 0.14:               # zabudowa balkonu: glazing above the balustrade, front + sides
        gv = int(hfloat(key, "glzv") * 97)
        g0 = f + up
        gup = np.array([0, 0, 1.45])
        _aq(acc, g0 - d3 * hw, g0 + d3 * hw, g0 + d3 * hw + gup, g0 - d3 * hw + gup, FA.uv_rect("balg", gv))
        gu, gv_, _, gh = FA.cell("balg", gv)          # sides: the first `dep` metres of the same glazing cell
        for sg in (-1, 1):
            s0, s1 = w0 + up + d3 * sg * hw, w0 + up + d3 * sg * hw + n3 * (depth - 0.03)
            ua_, ub_ = gu + dep, gu
            if sg < 0:
                s0, s1, ua_, ub_ = s1, s0, ub_, ua_
            _aq(acc, s0, s1, s1 + gup, s0 + gup, [[ua_, gv_], [ub_, gv_], [ub_, gv_ + gh], [ua_, gv_ + gh]])
    else:
        if hfloat(key, "line") < 0.30:          # laundry: cloths hanging from a line under the slab above
            x = -hw + 0.3
            k = 0
            while x < hw - 0.5:
                cw = 0.35 + 0.45 * hfloat(key, "cw", k)
                ch = 0.5 + 0.5 * hfloat(key, "ch", k)
                col = hpick(["cloth_white", "cloth_red", "cloth_blue", "cloth_dark", "cloth_yellow", "cloth_green",
                             "cloth_white"], key, "cc", k)
                c0 = w0 + d3 * x + n3 * (depth - 0.35) + [0, 0, 1.95]
                uvc = FA.swatch_uv(col)
                _aq(acc, c0 - [0, 0, ch], c0 + d3 * cw - [0, 0, ch], c0 + d3 * cw, c0, uvc)
                _aq(acc, c0 + d3 * cw - [0, 0, ch], c0 - [0, 0, ch], c0, c0 + d3 * cw, uvc)
                x += cw + 0.08 + 0.3 * hfloat(key, "cg", k)
                k += 1
        if hfloat(key, "dish") < 0.18 and float(n3 @ DISH_AZ) > -0.2:
            # satellite dish on an arm off the balustrade rail (review s9 P1-5: the dishes were white ovals hanging in
            # the air): 0.30 m horizontal arm, 0.42 m mast, offset dish 0.60 x 0.66 m facing the satellite, feed arm
            # and LNB in front of it. Only on balconies that see the southern sky.
            sgn = 1 if hfloat(key, "dside") < 0.5 else -1
            b0 = f + d3 * sgn * (hw - 0.30) + [0, 0, 1.0]
            m0 = b0 + n3 * 0.30
            acc.box(L0, "downpipe", b0 + n3 * 0.15, d3 * 0.018, n3 * 0.15, [0, 0, 0.018], skip=(2, 3))
            acc.box(L0, "downpipe", m0 + [0, 0, 0.21], d3 * 0.018, n3 * 0.018, [0, 0, 0.21], skip=(0,))
            nd = DISH_FACE
            t = np.cross([0, 0, 1.0], nd)
            t = t / np.linalg.norm(t)
            upv = np.cross(nd, t)
            c0 = m0 + [0, 0, 0.44] + nd * 0.05
            ring = [c0 + 0.30 * math.cos(i * math.pi / 4) * t + 0.33 * math.sin(i * math.pi / 4) * upv for i in range(8)]
            uvd = FA.swatch_uv("dish", 3)
            for i in range(1, 7):
                for tri in ((0, i, i + 1), (0, i + 1, i)):
                    acc.add(L0, "facade_atlas", [ring[j] for j in tri], [[0, 1, 2]], uvd)
            # feed arm from the lower rim to the focus, LNB at its end
            q0, q1 = c0 - upv * 0.33, c0 + nd * 0.34 - upv * 0.16
            us_ = FA.swatch_uv("steel_grey")
            _aq(acc, q0 - t * 0.012, q0 + t * 0.012, q1 + t * 0.012, q1 - t * 0.012, us_)
            _aq(acc, q0 + t * 0.012, q0 - t * 0.012, q1 - t * 0.012, q1 + t * 0.012, us_)
            acc.box(L0, "downpipe", q1, t * 0.03, upv * 0.03, nd * 0.045, skip=(1,))


def window_kit(acc, a, d, nout, o, key, p_ac):
    """Facade equipment at a window (ADR 0081): an AC outdoor unit on two brackets below the sill (share p_ac)."""
    if hfloat(key, "ac") >= p_ac:
        return
    d3, n3 = np.append(d, 0.0), np.append(nout, 0.0)
    um = o[0] + 0.45 if hfloat(key, "acs") < 0.5 else o[1] - 0.45
    c = v3(a + d * um + nout * 0.20, o[2] - 0.42)
    _abox(acc, c, d3 * 0.425, n3 * 0.15, [0, 0, 0.30], front=FA.uv_rect("ac", int(hfloat(key, "acv") * 97)), skip=(0,))
    for sg in (-1, 1):
        acc.box(L0, "downpipe", c + d3 * sg * 0.3 - [0, 0, 0.32] - n3 * 0.02, d3 * 0.015, n3 * 0.17, [0, 0, 0.015])


def wall_louvre(acc, a, d, nout, u, z, size=1.0, variant=0):
    """Ventilation louvre on a hall wall: `vent` cell of the facade atlas on a 4 cm frame box."""
    d3, n3 = np.append(d, 0.0), np.append(nout, 0.0)
    _abox(acc, v3(a + d * u + nout * 0.02, z), d3 * size / 2, n3 * 0.02, [0, 0, size / 2],
          front=FA.uv_rect("vent", variant), sw="galv")


def cage_ladder(acc, a, d, nout, u, z0, z1, mat="downpipe"):
    """Roof access ladder with a safety cage (drabina z koszem ochronnym, PN-EN ISO 14122-4: cage from 2.2-3.0 m above
    the ground, hoops <= 1.5 m apart, rungs 0.225-0.30 m; here 0.3 / 0.9 m, WORKING_VALUE), 0.25 m off the wall,
    stiles 1.1 m above the parapet. LOD0 only."""
    d3, n3 = np.append(d, 0.0), np.append(nout, 0.0)
    c = v3(a + d * u + nout * 0.25, 0.0)
    top = z1 + 1.1
    for sg in (-1, 1):                              # stiles
        acc.box(L0, mat, c + d3 * sg * 0.225 + [0, 0, (z0 + top) / 2], d3 * 0.02, n3 * 0.02, [0, 0, (top - z0) / 2], skip=(0,))
    z = z0 + 0.3
    while z < z1 + 0.05:                            # rungs
        acc.box(L0, mat, c + [0, 0, z], d3 * 0.205, n3 * 0.012, [0, 0, 0.012], skip=(4, 5))
        z += 0.3
    for zs in (z0 + 1.5, z1 - 0.6):                 # wall brackets
        for sg in (-1, 1):
            acc.box(L0, mat, c + d3 * sg * 0.225 - n3 * 0.125 + [0, 0, zs], d3 * 0.015, n3 * 0.125, [0, 0, 0.015], skip=(2, 3))
    zc0 = z0 + 2.5
    if top - zc0 < 1.0:
        return
    r = 0.35
    ang = [math.pi * k / 4 for k in range(5)]       # half hoop on the street side
    pts = [d3 * (r * math.cos(t)) + n3 * (r * math.sin(t) * 1.0 + 0.0) for t in ang]
    z = zc0
    while z < top + 0.01:                           # hoops: flat bar 5 cm, both faces
        for (p0, p1) in zip(pts, pts[1:]):
            A_, B_ = c + p0 + [0, 0, z - 0.025], c + p1 + [0, 0, z - 0.025]
            acc.quad(L0, mat, A_, B_, B_ + [0, 0, 0.05], A_ + [0, 0, 0.05])
            acc.quad(L0, mat, B_, A_, A_ + [0, 0, 0.05], B_ + [0, 0, 0.05])
        z += 0.9
    for k in (1, 2, 3):                             # vertical straps
        q = c + pts[k]
        t = np.cross([0, 0, 1.0], pts[k] / r)
        A_, B_ = q - t * 0.02 + [0, 0, zc0], q + t * 0.02 + [0, 0, zc0]
        acc.quad(L0, mat, A_, B_, B_ + [0, 0, top - zc0], A_ + [0, 0, top - zc0])
        acc.quad(L0, mat, B_, A_, A_ + [0, 0, top - zc0], B_ + [0, 0, top - zc0])


def chimney(acc, p, along, z0, z1, apron=None):
    """Brick chimney stack 0.56 x 0.44 m from z0 (inside the roof) to z1 with a sheet-metal cap (ADR 0091: the
    stack stands on the roof slope next to the ridge and ends 0.45 m above it).
    apron(xy) -> roof surface z: sheet flashing round the foot of the stack (obróbka komina, ADR 0094), 3 cm proud
    of the brick, from the roof surface 0.15 m up the stack, following the slope; LOD0, four faces."""
    along = np.asarray(along, float)
    across = np.array([-along[1], along[0]])
    c = v3(p, (z0 + z1) / 2)
    for layer in (L0, L1):
        acc.box(layer, "chimney_brick", c, np.append(along * 0.28, 0), np.append(across * 0.22, 0), [0, 0, (z1 - z0) / 2],
                skip=(0,))
    acc.box(L0, "hall_flashing", v3(p, z1 + 0.04), np.append(along * 0.33, 0), np.append(across * 0.27, 0), [0, 0, 0.04])
    if apron is not None:
        cs = [np.asarray(p, float) + along * (sx * 0.31) + across * (sy * 0.25) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
        zs = [float(apron(q)) for q in cs]
        for i in range(4):
            q0, q1, za, zb = cs[i], cs[(i + 1) % 4], zs[i], zs[(i + 1) % 4]
            acc.quad(L0, "hall_flashing", v3(q0, za - 0.04), v3(q1, zb - 0.04), v3(q1, zb + 0.15), v3(q0, za + 0.15))


def sign_instance(code, a, d, nout, u, z, src):
    p = a + d * u + nout * 0.05
    yaw = math.atan2(nout[1], nout[0]) - math.pi / 2
    return {"p": f"facade_sign_{code}", "e": round(float(p[0]), 3), "n": round(float(p[1]), 3), "z": round(float(z), 3),
            "yaw": round(float(yaw), 4), "src": src}


def machine_rooms(acc, poly, z, layer):
    """Lift machine rooms (one per ~30 m of a block's long axis) as plain boxes: the LOD1 roof silhouette of a
    wielka płyta block (v3.1; LOD0 gets them from roof_vents)."""
    r = poly.minimum_rotated_rectangle
    c = np.asarray(r.exterior.coords)[:4]
    e = [np.hypot(*(c[(i + 1) % 4] - c[i])) for i in range(4)]
    k = 0 if e[0] >= e[1] else 1
    along = (c[(k + 1) % 4] - c[k]) / max(e[k], 1e-6)
    across = np.array([-along[1], along[0]])
    ctr = np.asarray(r.centroid.coords[0])
    Lr = max(e)
    inner = poly.buffer(-2.0)
    if inner.is_empty:
        return
    for i in range(max(1, int(Lr // 30))):
        t = (i + 0.5) * Lr / max(1, int(Lr // 30)) - Lr / 2
        p = ctr + along * t
        if inner.contains(shapely.Point(*p)):
            acc.box(layer, "balcony_slab", v3(p, z + 1.1), np.append(along * 1.4, 0), np.append(across * 1.6, 0),
                    [0, 0, 1.1], skip=(0,))            # the face on the roof is never seen
