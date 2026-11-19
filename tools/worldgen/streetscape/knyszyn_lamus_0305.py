"""Timber granary / shelter (lamus) by the presbytery of Knyszyn - authored from its BDOT10k footprint and owner photo
klattow-02 (ADR 0305). Same contract as knyszyn_dom_klattow_0305: ``hero_targets`` drops the rule shed (the footprint
keeps its collision prism), ``build`` adds the visible building.

SOURCED: footprint 12.05 x 6.67 m (BDOT10k 6fe1, 'budynek gospodarczy'; no LoD height). READ OFF THE PHOTO (local
reference only, no pixel used): unpainted log walls on a low stone footing, a tall hipped shingle roof with wide
eaves, an open arcade (podcien) on posts with braces along the long side that looks north-north-east, a full-depth
log room at its west end, a plank floor under the arcade. ESTIMATED: which long side carries the arcade (the church
stands beyond the far end of the arcade on the photo, the building to the right of the view axis -> the NNE side),
eave 2.7 m, ridge 6.5 m, arcade 1.7 m deep over 0.72 of the length, five posts. All member sizes WORKING_VALUE.
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
LOG, WOOD, SHINGLE, STONE, DARK = "log_wall_raw", "wood_planks", "roof_shingles_grey", "fieldstone_plinth", "plinth_dark"
PLINTH_TOP, EAVE, RIDGE, ROOF_OV = 0.25, 2.70, 6.50, 0.55
ARCADE_D, ARCADE_SHARE, POSTS, POST = 1.70, 0.72, 5, 0.20
ARCADE_SIDE = np.array([0.4366, 0.9])       # the long side that carries the arcade looks this way (E, N) - ESTIMATED
FLOOR = 0.32


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

    zp, ze, zr, zfl = z0 + PLINTH_TOP, z0 + EAVE, z0 + RIDGE, z0 + FLOOR
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
            m.quad(layer, LOG, [wl.p(0, zb), wl.p(ln, zb), wl.p(ln, ze), wl.p(0, ze)], wl.n3,
                   uv=[[ph, zb - zp], [ph + ln, zb - zp], [ph + ln, ze - zp], [ph, ze - zp]])
        e, v0 = 0.05, z0 - 0.10
        m.quad(L0, STONE, [wl.p(-e, zbot, e), wl.p(ln + e, zbot, e), wl.p(ln + e, zp, e), wl.p(-e, zp, e)], wl.n3,
               uv=[[ph, zbot - v0], [ph + ln, zbot - v0], [ph + ln, zp - v0], [ph, zp - v0]])
        m.quad(L0, STONE, [wl.p(-e, zp, e), wl.p(ln + e, zp, e), wl.p(ln + e, zp, 0), wl.p(-e, zp, 0)], up,
               uv=[[ph, zp - v0], [ph + ln, zp - v0], [ph + ln, zp - v0 + e], [ph, zp - v0 + e]])
        if k == 0:                                           # wall under the arcade: two plank doors
            for j, uc in enumerate((ln * 0.30, ln * 0.72)):
                for layer in (L0, L1):
                    m.quad(layer, WOOD if layer == L0 else DARK,
                           [wl.p(uc - 0.6, zfl, 0.03), wl.p(uc + 0.6, zfl, 0.03), wl.p(uc + 0.6, zfl + 1.95, 0.03),
                            wl.p(uc - 0.6, zfl + 1.95, 0.03)], wl.n3, grain="nat_ad", key=(ASSET_ID, "door", j))
        if k == 2:                                           # front of the log room: a small shuttered opening
            m.quad(L0, WOOD, [wl.p(ln / 2 - 0.3, z0 + 1.55, 0.03), wl.p(ln / 2 + 0.3, z0 + 1.55, 0.03),
                              wl.p(ln / 2 + 0.3, z0 + 2.05, 0.03), wl.p(ln / 2 - 0.3, z0 + 2.05, 0.03)], wl.n3,
                   grain="nat_ad", key=(ASSET_ID, "shutter"))

    # arcade: plank floor on a stone edge, posts with braces, head beam
    front = _Wall(a, d, n, L)
    m.box(L0, WOOD, P(la / 2, -ARCADE_D / 2, zfl - 0.03), d3 * la / 2, n3 * ARCADE_D / 2, up * 0.03, grain=d3,
          key=(ASSET_ID, "deck"), skip=("-z",))
    for layer in (L0, L1):
        m.quad(layer, STONE if layer == L0 else LOG, [front.p(0, zbot), front.p(la, zbot), front.p(la, zfl - 0.06), front.p(0, zfl - 0.06)], n3,
               uv=[[0, zbot - z0 + 0.1], [la, zbot - z0 + 0.1], [la, zfl - 0.06 - z0 + 0.1], [0, zfl - 0.06 - z0 + 0.1]])
    m.quad(L0, STONE, [P(0, 0, zbot), P(0, -ARCADE_D, zbot), P(0, -ARCADE_D, zfl - 0.06), P(0, 0, zfl - 0.06)], -d3,
           uv=[[0, zbot - z0 + 0.1], [ARCADE_D, zbot - z0 + 0.1], [ARCADE_D, zfl - 0.06 - z0 + 0.1], [0, zfl - 0.06 - z0 + 0.1]])
    hb = 0.11                                                # half height of the head beam
    zb0 = ze - 2 * hb
    m.box(L0, WOOD, P(la / 2, -POST / 2, zb0 + hb), d3 * la / 2, n3 * POST / 2, up * hb, grain=d3, key=(ASSET_ID, "beam"))
    m.box(L1, WOOD, P(la / 2, -POST / 2, zb0 + hb), d3 * la / 2, n3 * POST / 2, up * hb, grain=d3, key=(ASSET_ID, "beam"),
          skip=("+z", "-x", "+x"))
    m.box(L0, WOOD, P(POST / 2, -ARCADE_D / 2, zb0 + hb), d3 * POST / 2, n3 * ARCADE_D / 2, up * hb, grain=n3, key=(ASSET_ID, "beam_end"))
    us = np.linspace(POST / 2, la - POST / 2, POSTS)
    for j, uc in enumerate(us):
        for layer in (L0, L1):
            m.box(layer, WOOD, P(uc, -POST / 2, (zfl + zb0) / 2), d3 * POST / 2, n3 * POST / 2, up * (zb0 - zfl) / 2, grain=up,
                  key=(ASSET_ID, "post", j), skip=("-z", "+z"))
        for sgn in (-1.0, 1.0):                              # braces (miecze) to the head beam, 0.55 m legs
            if (j == 0 and sgn < 0) or (j == POSTS - 1 and sgn > 0):
                continue
            leg, hb2 = 0.55, 0.045
            c = P(uc + sgn * (POST / 2 + leg / 2), -POST / 2, zb0 - leg / 2)
            ax = (d3 * sgn + up) * (leg / 2)
            az = (up - d3 * sgn) / math.sqrt(2.0) * hb2
            m.box(L0, WOOD, c, ax, n3 * hb2, az, grain=ax, key=(ASSET_ID, "brace", j, sgn))

    # hipped shingle roof over the whole footprint
    ov = ROOF_OV
    hw = W / 2 + ov
    slope = (RIDGE - EAVE) / hw
    zev = ze - 0.02
    r0, r1 = -ov + hw, L + ov - hw                           # ridge ends along u
    slen = math.hypot(hw, RIDGE - EAVE)
    c_w = -W / 2
    E = {"fl": P(-ov, ov, zev), "fr": P(L + ov, ov, zev), "bl": P(-ov, -W - ov, zev), "br": P(L + ov, -W - ov, zev),
         "rl": P(r0, c_w, zr), "rr": P(r1, c_w, zr)}
    for layer in (L0, L1):
        m.quad(layer, SHINGLE, [E["fl"], E["fr"], E["rr"], E["rl"]], n3 + up,
               uv=[[-ov, 0], [L + ov, 0], [r1, slen], [r0, slen]])
        m.quad(layer, SHINGLE, [E["br"], E["bl"], E["rl"], E["rr"]], up - n3,
               uv=[[0.3, 0.05], [L + 2 * ov + 0.3, 0.05], [L + 2 * ov + 0.3 - hw, slen + 0.05], [hw + 0.3, slen + 0.05]])
        m.poly(layer, SHINGLE, [E["bl"], E["fl"], E["rl"]], up - d3, [[0.1, 0.02], [2 * hw + 0.1, 0.02], [hw + 0.1, slen + 0.02]])
        m.poly(layer, SHINGLE, [E["fr"], E["br"], E["rr"]], up + d3, [[0.2, 0.08], [2 * hw + 0.2, 0.08], [hw + 0.2, slen + 0.08]])
    # underside of the eaves (boards) and the edge of the shingle courses
    for (pa, pb, face) in ((E["fl"], E["fr"], n3), (E["br"], E["bl"], -n3), (E["bl"], E["fl"], -d3), (E["fr"], E["br"], d3)):
        m.quad(L0, WOOD, [pa, pb, pb - up * 0.07, pa - up * 0.07], face, grain="ab", key=(ASSET_ID, "edge", tuple(np.round(face, 1))))
    under = [P(-ov, ov, zev - 0.07), P(L + ov, ov, zev - 0.07), P(L + ov, -W - ov, zev - 0.07), P(-ov, -W - ov, zev - 0.07)]
    m.quad(L0, WOOD, under, -up, grain="nat_ab", key=(ASSET_ID, "soffit"))

    acc.flush(buf, ASSET_ID)
    result.update(status="applied",
                  confidence={"footprint": "SOURCED BDOT10k", "heights_arcade_side": "ESTIMATED from owner photo klattow-02",
                              "member_sizes": "WORKING_VALUE"},
                  body_m=[round(L, 2), round(W, 2)], arcade_m=[round(la, 2), ARCADE_D], posts=POSTS,
                  roof_pitch_deg=round(math.degrees(math.atan(slope)), 1), triangles={"lod0": m.n[L0], "lod1": m.n[L1]})
    return result
