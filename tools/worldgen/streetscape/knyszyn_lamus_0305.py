"""Timber granary / shelter (lamus) by the presbytery of Knyszyn - authored from its BDOT10k footprint and owner photo
klattow-02 (ADR 0305). Same contract as knyszyn_dom_klattow_0305: ``hero_targets`` drops the rule shed (the footprint
keeps its collision prism), ``build`` adds the visible building.

SOURCED: footprint 12.05 x 6.67 m (BDOT10k 6fe1, 'budynek gospodarczy'; no LoD height). READ OFF THE PHOTO (local
reference only, no pixel used): weathered unpainted log walls on a low stone footing; a tall hipped shingle roof whose
lower part is flatter (kicked eaves, zalamanie polaci) and reaches far past the walls; an eyebrow dormer (wole oko)
low on the arcade slope; an open arcade (podcien) on six posts with braces (miecze) on both sides of every post,
under a head beam with the ends of the ceiling joists above it; a plank deck on a sill beam that stands proud of the
posts, with one plank step; a full-depth log room at the west end with one small square opening. ESTIMATED: which
long side carries the arcade (the church stands beyond the far end of the arcade on the photo, the building to the
right of the view axis -> the NNE side), every height and the roof pitches (round 3: eave edge 2.27 m, ridge 6.8 m,
kick 32 deg over 1.15 m, main slope ~51 deg, overhang 0.9 m - the roof is ~1.6 x the wall on the photo), arcade
2.1 m deep over 0.72 of the length. All member sizes WORKING_VALUE.

Round 3 (klattow-r3-s24): the shingle courses are geometry - every course is its own strip whose butt edge stands
SHINGLE_STEP proud of the course below, on all four slopes, in step round the hips (the flat quad of round 2 read as a
grey sheet). The texture set wood_shingles has the same course (SHINGLE_COURSE), so its butt shadow lies on the step.
"""
from __future__ import annotations

import math

import numpy as np
from shapely.geometry import Point, Polygon

from . import buildings_mesh as BM
from . import facade_kit as FK
from .knyszyn_dom_klattow_0305 import _Mesh, _Wall, L0, L1

REGION = "knyszyn"
BUILDING_ID = "bdot:40f8044a-d048-4ad8-ad57-d8b8a2886fe1"
ASSET_ID = "knyszyn_lamus_0305"
LOG, WOOD, SHINGLE, STONE, DARK = "log_wall_raw", "wood_planks_weathered", "roof_shingles_grey", "fieldstone_plinth", "plinth_dark"
BROW = "wood_planks"                                     # warm brown board of the eyebrow dormer (red-brown on the photo)
PLINTH_TOP = 0.25
EAVE_EDGE, RIDGE, ROOF_OV = 2.27, 6.80, 0.90              # lower edge of the shingles / ridge above the ground; overhang
KICK_RUN, KICK_DEG = 1.15, 32.0                           # flatter lower part of every slope (horizontal run, pitch)
SHINGLE_COURSE = 1.5 / 7                                  # exposure of a course along the slope = the set's course, m
SHINGLE_STEP = 0.05                                       # butt of a course above the course below, m
ARCADE_D, ARCADE_SHARE, POSTS, POST = 2.10, 0.72, 6, 0.20
BEAM_H, JOIST_H, PLATE_H = 0.22, 0.16, 0.16               # head beam, joist ends above it, top plate under the roof
BRACE_LEG, BRACE_HALF = 0.65, 0.06
DECK_OUT, DECK_SILL = 0.25, 0.42                          # deck past the post line; sill beam under its edge
DORMER_U, DORMER_HALF_W, DORMER_H = 0.58, 0.95, 0.60      # eyebrow: centre as a share of the arcade, half width, rise
ARCADE_SIDE = np.array([0.4366, 0.9])       # the long side that carries the arcade looks this way (E, N) - ESTIMATED
FLOOR = 0.35


def roof_profile(W):
    """(hw, zk, m, s_k, s_top): half span of the roof in plan, height of the kick line above the eave edge, tangent of
    the main slope, slope length of the kick and of the whole slope."""
    hw = W / 2 + ROOF_OV
    zk = KICK_RUN * math.tan(math.radians(KICK_DEG))
    m = (RIDGE - EAVE_EDGE - zk) / (hw - KICK_RUN)
    s_k = KICK_RUN / math.cos(math.radians(KICK_DEG))
    return hw, zk, m, s_k, s_k + math.hypot(hw - KICK_RUN, RIDGE - EAVE_EDGE - zk)


def _frame(poly):
    """(a, d, n, L, W): a = left end of the arcade side seen from outside, d along it, n out of it. None when the
    footprint is not the plain rectangle this module was written for."""
    rect = np.asarray(poly.minimum_rotated_rectangle.exterior.coords, float)[:4]
    if poly.area < 0.93 * Polygon(rect).area:
        return None
    if not Polygon(rect).exterior.is_ccw:
        rect = rect[::-1]
    best = None
    for k in range(4):
        a, b = rect[k], rect[(k + 1) % 4]
        L = float(np.linalg.norm(b - a))
        d = (b - a) / L
        n = np.array([d[1], -d[0]])
        s = float(n @ ARCADE_SIDE)
        if best is None or s > best[0]:
            best = (s, a, d, n, L, float(np.linalg.norm(rect[(k + 2) % 4] - b)))
    s, a, d, n, L, W = best
    return (a, d, n, L, W) if s > 0.8 and 9.0 < L < 16.0 and 5.0 < W < 9.0 else None


def hero_targets(region, feature_collection):
    if region != REGION:
        return {}
    for f in feature_collection["features"]:
        if f.get("id") == BUILDING_ID:
            return {BUILDING_ID: ASSET_ID} if _frame(Polygon(f["geometry"]["coordinates"][0][0])) is not None else {}
    return {}


def build(buf, region, blds, zsmooth, report):
    result = {"id": ASSET_ID, "status": "skipped", "sources": [BUILDING_ID]}
    if region != REGION:
        return result
    report[ASSET_ID] = result
    b = next((x for x in blds if x["id"] == BUILDING_ID), None)
    fr = None if b is None or b["ovr"].get("hero_asset") != ASSET_ID else _frame(b["poly"])
    if fr is None:
        result["reason"] = "hero target missing or footprint changed; the rule building stays"
        return result
    a, d, n, L, W = fr
    ring = np.asarray(b["poly"].exterior.coords, float)
    zg = np.asarray(zsmooth(ring[:, 0], ring[:, 1]), float)
    if not np.all(np.isfinite(zg)):
        result["reason"] = "invalid terrain height"
        return result
    z0, zbot = float(np.median(zg)), float(zg.min()) - 0.5
    acc = BM.Acc()
    m = _Mesh(acc)
    d3, n3, up = np.r_[d, 0.0], np.r_[n, 0.0], np.array([0.0, 0.0, 1.0])

    def P(u, w, z):                      # u along the arcade side, w out of it (the body lies at w in [-W, 0])
        q = a + d * u + n * w
        return np.array([q[0], q[1], z])

    hw, zk, slope, s_k, s_top = roof_profile(W)
    ck, tk = math.cos(math.radians(KICK_DEG)), math.tan(math.radians(KICK_DEG))
    zE = z0 + EAVE_EDGE

    def prof(r):                         # height of the roof plane above the eave edge at horizontal run r
        return r * tk if r <= KICK_RUN else zk + (r - KICK_RUN) * slope

    def run_of(s):                       # horizontal run at slope length s
        return s * ck if s <= s_k else KICK_RUN + (s - s_k) / math.hypot(1.0, slope)

    def len_of(r):                       # slope length at horizontal run r
        return r / ck if r <= KICK_RUN else s_k + (r - KICK_RUN) * math.hypot(1.0, slope)

    zt = zE + prof(ROOF_OV) - 0.06                             # top of the walls = underside of the roof boards
    zp, zfl = z0 + PLINTH_TOP, z0 + FLOOR
    zpl0 = zt - PLATE_H                                        # top plate
    zj0 = zpl0 - JOIST_H                                       # joists (the ceiling of the arcade lies on them)
    zb0 = zj0 - BEAM_H                                         # head beam on the posts
    # plan: the arcade occupies [0, la] of the front (its far end is the east end); the log room [la, L] is full depth
    la = L * ARCADE_SHARE
    # outline of the log walls, counter-clockwise seen from above (u, w): recess of the arcade on the front
    plan = [(0.0, -ARCADE_D), (la, -ARCADE_D), (la, 0.0), (L, 0.0), (L, -W), (0.0, -W)]
    edges = list(zip(plan, plan[1:] + plan[:1]))
    outline = Polygon([a + d * u + n * w for u, w in plan])
    for k, ((u0, w0), (u1, w1)) in enumerate(edges):
        p0, p1 = a + d * u0 + n * w0, a + d * u1 + n * w1
        ln = float(np.linalg.norm(p1 - p0))
        t = (p1 - p0) / ln
        nrm = np.array([t[1], -t[0]])                    # outward: the side of the edge that leaves the wall outline
        if outline.contains(Point(*((p0 + p1) / 2 + nrm * 0.05))):
            nrm = -nrm
        dd = np.array([-nrm[1], nrm[0]])                 # left to right seen from outside
        a0 = p0 if float((p1 - p0) @ dd) > 0 else p1
        wl = _Wall(a0, dd, nrm, ln)
        ph = 4.0 * FK.hfloat(ASSET_ID, "log", k)
        for layer, zb in ((L0, zp), (L1, zbot)):
            m.quad(layer, LOG, [wl.p(0, zb), wl.p(ln, zb), wl.p(ln, zt), wl.p(0, zt)], wl.n3,
                   uv=[[ph, zb - zp], [ph + ln, zb - zp], [ph + ln, zt - zp], [ph, zt - zp]])
        e, v0 = 0.05, z0 - 0.10
        m.quad(L0, STONE, [wl.p(-e, zbot, e), wl.p(ln + e, zbot, e), wl.p(ln + e, zp, e), wl.p(-e, zp, e)], wl.n3,
               uv=[[ph, zbot - v0], [ph + ln, zbot - v0], [ph + ln, zp - v0], [ph, zp - v0]])
        m.quad(L0, STONE, [wl.p(-e, zp, e), wl.p(ln + e, zp, e), wl.p(ln + e, zp, 0), wl.p(-e, zp, 0)], up,
               uv=[[ph, zp - v0], [ph + ln, zp - v0], [ph + ln, zp - v0 + e], [ph, zp - v0 + e]])
        if k == 0:                                           # wall under the arcade: two plank doors
            for j, uc in enumerate((ln * 0.30, ln * 0.72)):
                for layer in (L0, L1):
                    m.quad(layer, WOOD if layer == L0 else DARK,
                           [wl.p(uc - 0.6, zfl, 0.03), wl.p(uc + 0.6, zfl, 0.03), wl.p(uc + 0.6, zfl + 1.85, 0.03),
                            wl.p(uc - 0.6, zfl + 1.85, 0.03)], wl.n3, grain="nat_ad", key=(ASSET_ID, "door", j))
        if k == 2:                                           # front of the log room: one small square opening, high up
            uo, zo, ho = 0.95, z0 + 1.78, 0.14
            m.quad(L0, DARK, [wl.p(uo - ho, zo, 0.012), wl.p(uo + ho, zo, 0.012), wl.p(uo + ho, zo + 2 * ho, 0.012),
                              wl.p(uo - ho, zo + 2 * ho, 0.012)], wl.n3)

    # ---- arcade: plank deck on a sill beam, posts with braces, head beam, joist ends, top plate, board ceiling
    front = _Wall(a, d, n, L)
    wd = DECK_OUT                                            # deck edge, out of the post line
    m.quad(L0, WOOD, [P(0, -ARCADE_D, zfl), P(la, -ARCADE_D, zfl), P(la, wd, zfl), P(0, wd, zfl)], up, grain="nat_ab",
           key=(ASSET_ID, "deck"))
    zs0 = zfl - DECK_SILL
    m.quad(L0, WOOD, [front.p(0, zs0, wd), front.p(la, zs0, wd), front.p(la, zfl, wd), front.p(0, zfl, wd)], n3,
           grain="ab", key=(ASSET_ID, "sill"))
    m.quad(L0, WOOD, [P(0, wd, zs0), P(0, -ARCADE_D, zs0), P(0, -ARCADE_D, zfl), P(0, wd, zfl)], -d3,
           grain="ab", key=(ASSET_ID, "sill_e"))
    m.quad(L0, WOOD, [P(la, 0, zs0), P(la, wd, zs0), P(la, wd, zfl), P(la, 0, zfl)], d3, grain="ab", key=(ASSET_ID, "sill_w"))
    for layer in (L0, L1):
        ws, zs_ = (wd - 0.04, zs0) if layer == L0 else (0.0, zfl)
        m.quad(layer, STONE if layer == L0 else LOG,
               [front.p(0, zbot, ws), front.p(la, zbot, ws), front.p(la, zs_, ws), front.p(0, zs_, ws)], n3,
               uv=[[0, zbot - z0 + 0.1], [la, zbot - z0 + 0.1], [la, zs_ - z0 + 0.1], [0, zs_ - z0 + 0.1]])
    m.quad(L0, STONE, [P(0.04, wd, zbot), P(0.04, -ARCADE_D, zbot), P(0.04, -ARCADE_D, zs0), P(0.04, wd, zs0)], -d3,
           uv=[[0, zbot - z0 + 0.1], [ARCADE_D + wd, zbot - z0 + 0.1], [ARCADE_D + wd, zs0 - z0 + 0.1], [0, zs0 - z0 + 0.1]])
    m.quad(L0, STONE, [P(la, 0, zbot), P(la, wd, zbot), P(la, wd, zs0), P(la, 0, zs0)], d3,
           uv=[[0, zbot - z0 + 0.1], [wd, zbot - z0 + 0.1], [wd, zs0 - z0 + 0.1], [0, zs0 - z0 + 0.1]])
    us_ = la * 0.42                                          # plank step in front of the deck
    m.box(L0, WOOD, P(us_, wd + 0.22, (zbot + z0 + 0.17) / 2), d3 * 0.75, n3 * 0.22, up * (z0 + 0.17 - zbot) / 2, grain=d3,
          key=(ASSET_ID, "step"), skip=("-z", "-y"))
    hb, hp = BEAM_H / 2, PLATE_H / 2
    m.box(L0, WOOD, P(la / 2, -POST / 2, zb0 + hb), d3 * la / 2, n3 * POST / 2, up * hb, grain=d3, key=(ASSET_ID, "beam"))
    m.box(L0, WOOD, P(la / 2, -POST / 2, zpl0 + hp), d3 * la / 2, n3 * POST / 2, up * hp, grain=d3, key=(ASSET_ID, "plate"),
          skip=("+z",))
    m.box(L1, WOOD, P(la / 2, -POST / 2, (zb0 + zt) / 2), d3 * la / 2, n3 * POST / 2, up * (zt - zb0) / 2, grain=d3,
          key=(ASSET_ID, "beam"), skip=("+z", "-x", "+x"))
    m.box(L0, WOOD, P(POST / 2, -ARCADE_D / 2, zb0 + hb), d3 * POST / 2, n3 * ARCADE_D / 2, up * hb, grain=n3, key=(ASSET_ID, "beam_end"))
    m.box(L0, WOOD, P(POST / 2, -ARCADE_D / 2, zpl0 + hp), d3 * POST / 2, n3 * ARCADE_D / 2, up * hp, grain=n3,
          key=(ASSET_ID, "plate_end"), skip=("+z",))
    zc = zj0 + JOIST_H
    m.quad(L0, WOOD, [P(0, 0, zc), P(la, 0, zc), P(la, -ARCADE_D, zc), P(0, -ARCADE_D, zc)], -up, grain="nat_ab",
           key=(ASSET_ID, "ceiling"))
    us = np.linspace(POST / 2, la - POST / 2, POSTS)
    for j, uc in enumerate(np.r_[us, (us[:-1] + us[1:]) / 2]):   # ceiling joists; their ends stand out over the head beam
        m.box(L0, WOOD, P(uc, (0.28 - ARCADE_D) / 2, zj0 + JOIST_H / 2), d3 * 0.075, n3 * (0.28 + ARCADE_D) / 2, up * JOIST_H / 2,
              grain=n3, key=(ASSET_ID, "joist", j), skip=("+z", "-y"))
    for j, uc in enumerate(us):
        for layer in (L0, L1):
            m.box(layer, WOOD, P(uc, -POST / 2, (zfl + zb0) / 2), d3 * POST / 2, n3 * POST / 2, up * (zb0 - zfl) / 2, grain=up,
                  key=(ASSET_ID, "post", j), skip=("-z", "+z"))
        for sgn in (-1.0, 1.0):                              # braces (miecze) to the head beam
            if (j == 0 and sgn < 0) or (j == POSTS - 1 and sgn > 0):
                continue
            c = P(uc + sgn * (POST / 2 + BRACE_LEG / 2), -POST / 2, zb0 - BRACE_LEG / 2)
            ax = (d3 * sgn + up) * (BRACE_LEG / 2 + 0.03)
            az = (up - d3 * sgn) / math.sqrt(2.0) * BRACE_HALF
            m.box(L0, WOOD, c, ax, n3 * 0.07, az, grain=ax, key=(ASSET_ID, "brace", j, sgn), skip=("-x", "+x"))
    # brace of the end post to the side beam (the east end of the arcade is open)
    c = P(POST / 2, -POST - BRACE_LEG / 2, zb0 - BRACE_LEG / 2)
    m.box(L0, WOOD, c, (up - n3) * (BRACE_LEG / 2 + 0.03), d3 * 0.07, (up + n3) / math.sqrt(2.0) * BRACE_HALF, grain=up - n3,
          key=(ASSET_ID, "brace_end"), skip=("-x", "+x"))

    # ---- hipped shingle roof with kicked eaves: four slopes of stepped courses that meet on the hips
    ov = ROOF_OV
    faces = (("front", a + d * (-ov) + n * ov, d, -n, L + 2 * ov, 0.0),
             ("back", a + d * (L + ov) + n * (-W - ov), -d, n, L + 2 * ov, 0.31),
             ("east", a + d * (-ov) + n * (-W - ov), n, d, W + 2 * ov, 0.67),
             ("west", a + d * (L + ov) + n * ov, -n, -d, W + 2 * ov, 1.03))

    def F(face, x, r, lift=0.0):
        _, o, t, q, _, _ = face
        p = o + t * x + q * r
        return np.array([p[0], p[1], zE + prof(r) + lift])

    def strip(layer, face, r0_, r1_, f0=0.0, f1=0.0):
        _, _, _, q, Lf, uoff = face
        pts = [F(face, r0_, r0_, f0), F(face, Lf - r0_, r0_, f0), F(face, Lf - r1_, r1_, f1), F(face, r1_, r1_, f1)]
        uv = [[uoff + r0_, len_of(r0_)], [uoff + Lf - r0_, len_of(r0_)], [uoff + Lf - r1_, len_of(r1_)], [uoff + r1_, len_of(r1_)]]
        if Lf - 2 * r1_ < 1e-4:
            m.poly(layer, SHINGLE, pts[:3], up - np.r_[q, 0.0], uv[:3])
        else:
            m.quad(layer, SHINGLE, pts, up - np.r_[q, 0.0], uv=uv)

    bounds = [k * SHINGLE_COURSE for k in range(int(math.ceil(s_top / SHINGLE_COURSE)))] + [s_top]
    if bounds[-1] - bounds[-2] < 0.04:                       # sliver under the ridge: part of the course below
        del bounds[-2]
    for face in faces:
        name, o, t, q, Lf, uoff = face
        out3 = np.r_[-q, 0.0]
        for sa, sb in zip(bounds[:-1], bounds[1:]):
            ra, rb = run_of(sa), min(run_of(sb), hw)
            cuts = [ra] + ([KICK_RUN] if ra < KICK_RUN - 1e-6 and KICK_RUN < rb - 1e-6 else []) + [rb]
            for r0_, r1_ in zip(cuts[:-1], cuts[1:]):        # the course is one strip, proud at its butt
                strip(L0, face, r0_, r1_, SHINGLE_STEP * (rb - r0_) / (rb - ra), SHINGLE_STEP * (rb - r1_) / (rb - ra))
            # butt of the course: the dark underside band of the set, just under this course's own butt line
            m.quad(L0, SHINGLE, [F(face, ra, ra), F(face, Lf - ra, ra), F(face, Lf - ra, ra, SHINGLE_STEP), F(face, ra, ra, SHINGLE_STEP)],
                   out3, uv=[[uoff + ra, sa - 0.012], [uoff + Lf - ra, sa - 0.012], [uoff + Lf - ra, sa - 0.003], [uoff + ra, sa - 0.003]])
        for r0_, r1_ in ((0.0, KICK_RUN), (KICK_RUN, hw)):   # LOD1: the two pitches as plain faces
            strip(L1, face, r0_, r1_)
            # LOD0: the same closed faces 2 cm under the courses. Round 3 review (P0): the shadow pass pulls every
            # vertex in along its normal, which opened slits between a course and its butt - dots of sun in the
            # roof's shadow. The shell is hidden by the courses and closes the caster.
            strip(L0, face, r0_, r1_, -0.02, -0.02)
        # eave board and the boarded underside of the overhang (to the wall line)
        m.quad(L0, WOOD, [F(face, 0, 0, -0.07), F(face, Lf, 0, -0.07), F(face, Lf, 0), F(face, 0, 0)], out3, grain="ab",
               key=(ASSET_ID, "edge", name))
        m.quad(L0, WOOD, [F(face, 0, 0, -0.07), F(face, Lf, 0, -0.07), F(face, Lf - ov, ov, -0.06), F(face, ov, ov, -0.06)], -up,
               grain="nat_ab", key=(ASSET_ID, "soffit", name))

    # ---- eyebrow dormer (wole oko) on the arcade slope, just above the kick line
    face = faces[0]
    _, o, t, q, Lf, uoff = face
    out3 = np.r_[-q, 0.0]
    xd, rf = ov + la * DORMER_U, KICK_RUN + 0.12
    sf, hood_t = len_of(rf), math.tan(math.radians(12.0))
    xs = np.linspace(-DORMER_HALF_W, DORMER_HALF_W, 13)
    hs = DORMER_H * np.cos(np.pi * xs / (2 * DORMER_HALF_W)) ** 2
    A = [F(face, xd + x_, rf, h_ + SHINGLE_STEP * 0.5) for x_, h_ in zip(xs, hs)]          # brow in the vertical front plane
    Bk = [F(face, xd + x_, rf + h_ / (slope - hood_t), SHINGLE_STEP * 0.5) for x_, h_ in zip(xs, hs)]   # hood runs back into the slope
    for i in range(len(xs) - 1):
        l0, l1 = float(np.linalg.norm(Bk[i] - A[i])), float(np.linalg.norm(Bk[i + 1] - A[i + 1]))
        quad = [A[i], A[i + 1], Bk[i + 1], Bk[i]]
        uv = [[uoff + xd + xs[i], sf], [uoff + xd + xs[i + 1], sf], [uoff + xd + xs[i + 1], sf + l1], [uoff + xd + xs[i], sf + l0]]
        if i == 0:
            m.poly(L0, SHINGLE, quad[:3], up, uv[:3])
        elif i == len(xs) - 2:
            m.poly(L0, SHINGLE, [quad[0], quad[1], quad[3]], up, [uv[0], uv[1], uv[3]])
        else:
            m.quad(L0, SHINGLE, quad, up, uv=uv)
    cb = F(face, xd, rf)                                     # brow board: two fans from the middle of its foot
    for half in (slice(0, 7), slice(6, 13)):
        m.poly(L0, BROW, [cb] + A[half], out3, [[0.3, 0.9]] + [[0.3 + x_, 0.9 + h_] for x_, h_ in zip(xs[half], hs[half])])
    hole = [F(face, xd + 0.36 * math.cos(g), rf, 0.09 + 0.36 * math.sin(g)) + out3 * 0.012 for g in np.linspace(0.0, math.pi, 9)]
    m.poly(L0, DARK, hole, out3, [[0.0, 0.0]] * len(hole))

    acc.flush(buf, ASSET_ID)
    result.update(status="applied",
                  confidence={"footprint": "SOURCED BDOT10k", "heights_pitches_arcade_side": "ESTIMATED from owner photo klattow-02",
                              "member_sizes": "WORKING_VALUE"},
                  body_m=[round(L, 2), round(W, 2)], arcade_m=[round(la, 2), ARCADE_D], posts=POSTS,
                  roof={"eave_edge_m": EAVE_EDGE, "ridge_m": RIDGE, "overhang_m": ROOF_OV, "kick_deg": KICK_DEG,
                        "wall_top_m": round(zt - z0, 2), "shingle_courses": len(bounds) - 1,
                        "course_m": round(SHINGLE_COURSE, 4), "step_m": SHINGLE_STEP, "dormer": "eyebrow"},
                  roof_pitch_deg=round(math.degrees(math.atan(slope)), 1), triangles={"lod0": m.n[L0], "lod1": m.n[L1]})
    return result
