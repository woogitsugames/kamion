"""Dom Klattow (Koscielna, Knyszyn) - authored from its BDOT10k footprint and the owner's photos (ADR 0305).

``hero_targets(region, fc)`` is merged into buildings_mesh.load's hero map (the rule facade is dropped, the footprint
keeps its collision prism and masks); ``build(buf, region, blds, zsmooth, report, roads_poly)`` adds the house.

SOURCED: footprint with the porch (BDOT10k 2F22, 21.10 x 7.84 m body, porch 2.7 x 2.0 m on the street side), eave and
ridge heights (GUGiK LoD2 2017: eave 2.22 m, ridge 6.06 m above the ground), chimney positions (GUGiK orthophoto 2025,
reference only). READ OFF THE OWNER PHOTOS klattow-01, -03, -04, -05 (Data/raw/refs/owner-knyszyn-klattow-2026-11-19,
local reference only - no pixel of them is used): limewashed log walls on a fieldstone footing, vertical white
boarding in the gables with a small window under its own little roof, a pent roof (daszek okapowy) across each gable
at the eave line, white boxed eaves and barge boards, old ceramic S-tile roof with two brick chimneys, a porch with
board panels, diagonal lattice and a tiled gable roof, dark brown six-pane windows, a brown picket fence along the
footway. Opening positions are measured on the photos relative to the porch (street side: scale 0.0213 m/px from the
21.10 m wall; yard side: projective fit of photo 05) - ESTIMATED +-0.3 m. The west gable is on no photo: mirrored from
the east one (ESTIMATED). All member sizes WORKING_VALUE. No text, plaque, emblem or brand.
"""
from __future__ import annotations

import math

import numpy as np
from shapely.geometry import Polygon

from . import buildings_mesh as BM
from . import facade_kit as FK

REGION = "knyszyn"
BUILDING_ID = "bdot:2002917F-2F22-5C99-E053-CC2BA8C01CFC"
ASSET_ID = "knyszyn_dom_klattow_0305"
L0, L1 = "buildings", "buildings_low"

# materials (streetscape.materials, ADR 0305)
LOG, BOARD_W, STAIN, TRIM = "log_wall_white", "wood_planks_white", "wood_planks_stain", "wood_trim_brown"
TILE, STONE, SHEET, BRICK, DOOR = "roof_tiles_old", "fieldstone_plinth", "roof_sheet_grey", "chimney_brick", "wood_planks_red"
SOFFIT, CONCRETE, GLASS = "soffit_boards", "hall_plinth", "glass"

# heights above the ground datum z0 (median terrain under the footprint), m
PLINTH_TOP = 0.30        # fieldstone footing (photo 05: 0.2-0.4 m along the yard wall)
WALL_TOP = 2.25          # top log = LoD2 eave 2.22 m
EAVE_EDGE = 2.45         # top of the fascia = lower edge of the tiles
RIDGE = 6.05             # LoD2 ridge 6.06 m
EAVE_OV = 0.40           # boxed eave overhang of the long walls, m
GABLE_OV = 0.35          # roof overhang past the gable walls, m
FASCIA_H = 0.25
WIN_W, WIN_SILL, WIN_HEAD = 0.95, 1.17, 2.14      # six-pane casements right under the eave box (photo 01: 1.0 x 1.0 m)
# street wall: window centres relative to the porch centre, m (photo 01)
FRONT_WINDOWS = (-8.65, -4.98, -3.19, 2.34, 4.45, 8.12)
# yard wall from its EAST corner: (centre m, width m) and the door (photo 05, projective fit; photo 03 agrees: three
# windows, then the door)
BACK_WINDOWS = ((3.26, 0.95), (6.87, 0.95), (9.18, 0.95), (14.69, 0.72), (16.30, 0.72), (18.85, 0.90))
BACK_DOOR = (12.06, 0.92)
GABLE_WINDOWS = (-1.98, 1.98)                     # ground-floor windows of a gable wall, from its centre (photo 05)
GABLE_WIN = (0.76, 3.12, 4.06)                    # attic window: width, sill, head
PENT_OUT, PENT_Z = 0.55, (2.62, 2.34)             # pent roof across the gable: projection, z at the wall / outer edge
# chimneys on the ridge, relative to the porch centre (photo 01: -2.39 / +0.30 m; orthophoto: about 1 m east of the
# porch for the eastern one) - ESTIMATED +-0.5 m
CHIMNEYS = (-2.35, 0.55)
PORCH_EAVE, PORCH_RIDGE, PORCH_OV, PORCH_FRONT_OV = 2.22, 3.15, 0.25, 0.30
PORCH_RAIL, PORCH_BEAM = 1.10, 2.08               # top of the board panels / underside of the head beam
PORCH_DOOR_W = 1.10                               # clear opening of the porch front
PICKET_W, PICKET_PITCH, PICKET_H = 0.09, 0.14, 1.05
FENCE_PAST = (2.6, 4.5)                           # past the west / east corner, m (photo 01, ADR 0305)
OPENING_MARGIN = 0.30                            # clear wall beyond the opening's surround / sill, m
OPENING_TRIM = 0.105                             # widest window trim: 0.085 m surround + 0.02 m sill
ROAD_CLEAR_M = 0.15                               # the fence keeps this far off the road / footway footprint
WALKWAY_MIN_M = 1.4                               # footway left in front of pickets that stand on the modelled footway
BED = "plot_lawn"                                 # raised grass strip between the wall and the pickets


def hero_targets(region, feature_collection):
    if region != REGION:
        return {}
    for f in feature_collection["features"]:
        if f.get("id") == BUILDING_ID:
            ring = f["geometry"]["coordinates"][0][0]
            return {BUILDING_ID: ASSET_ID} if _frame(Polygon(ring)) is not None else {}
    return {}


def _frame(poly):
    """Body rectangle + porch of the footprint: (a, d, n, L, W, pu0, pu1, pd) - a = west corner of the street wall,
    d along it, n its outward normal; porch [pu0, pu1] along the wall, pd deep. None when the footprint is not the
    long house with one porch this module was written for."""
    body = poly.buffer(-1.4, join_style=2).buffer(1.4, join_style=2)
    if body.is_empty or body.geom_type != "Polygon":
        return None
    rect = np.asarray(body.minimum_rotated_rectangle.exterior.coords, float)[:4]
    if Polygon(rect).exterior.is_ccw is False:
        rect = rect[::-1]
    porch = poly.difference(body.buffer(0.08))
    parts = [g for g in getattr(porch, "geoms", [porch]) if g.geom_type == "Polygon" and g.area > 2.0]
    if len(parts) != 1:
        return None
    pc = np.asarray(parts[0].centroid.coords[0])
    best = None
    for k in range(4):
        a, b = rect[k], rect[(k + 1) % 4]
        L = float(np.linalg.norm(b - a))
        d = (b - a) / L
        n = np.array([d[1], -d[0]])
        off = float((pc - (a + b) / 2) @ n)
        if off > 0 and (best is None or L > best[3]):
            best = (a, d, n, L, float(np.linalg.norm(rect[(k + 2) % 4] - b)))
    # This is an authored photo layout, not a generic long house. Keep close to the sourced 21.10 x 7.84 m body.
    if best is None or not (20.0 <= best[3] <= 22.2 and 7.0 <= best[4] <= 8.7):
        return None
    a, d, n, L, W = best
    q = np.asarray(parts[0].exterior.coords) - a
    u, w = q @ d, q @ n
    pu0, pu1, pd = float(u.min()), float(u.max()), float(w.max())
    pc = (pu0 + pu1) / 2
    if not (2.4 <= pu1 - pu0 <= 2.8 and 1.7 <= pd <= 2.3):
        return None

    def fits(centre, width, length, trim=OPENING_TRIM):
        return (centre - width / 2 - trim >= OPENING_MARGIN and
                centre + width / 2 + trim <= length - OPENING_MARGIN)

    # Include all trim (especially the projecting sill), and keep street windows off the porch roof.
    for off in FRONT_WINDOWS:
        centre = pc + off
        if not fits(centre, WIN_W, L):
            return None
        if not (centre + WIN_W / 2 + OPENING_TRIM <= pu0 - PORCH_OV - 0.10 or
                centre - WIN_W / 2 - OPENING_TRIM >= pu1 + PORCH_OV + 0.10):
            return None
    if not all(fits(centre, width, L) for centre, width in BACK_WINDOWS + (BACK_DOOR,)):
        return None
    if not all(fits(W / 2 + off, WIN_W, W) for off in GABLE_WINDOWS):
        return None
    if not (fits(pc, 0.92, L) and fits(pc, pu1 - pu0, L, PORCH_OV)):
        return None
    # The attic trim must also sit below the sloping gable edge, including the small window roof.
    slope = (RIDGE - EAVE_EDGE) / (W / 2 + EAVE_OV)
    attic_half = GABLE_WIN[0] / 2 + 0.17
    if not fits(W / 2, 2 * attic_half, W, 0.0) or GABLE_WIN[2] + 0.26 > RIDGE - slope * attic_half:
        return None
    return a, d, n, L, W, pu0, pu1, pd


def _row(key):
    """One board row of the wood_siding set: (s0, va, vb) in UV metres (BM.WOOD_JOINT_V)."""
    J = BM.WOOD_JOINT_V
    k = int(FK.hfloat(key, "row") * len(J)) % len(J)
    j1 = J[k + 1] if k + 1 < len(J) else J[0] + 1.0
    return BM.WOOD_TILE_M[0] * FK.hfloat(key, "along"), (J[k] + 0.008) * BM.WOOD_TILE_M[1], (j1 - 0.008) * BM.WOOD_TILE_M[1]


class _Mesh:
    """Quad / triangle / box emitter that fixes the winding from the direction a face must be seen from and writes
    the UV0 conventions of the sets: 'row' = one board of wood_siding with its grain along an edge, 'nat' = metres."""

    def __init__(self, acc):
        self.acc = acc
        self.n = {L0: 0, L1: 0}

    def quad(self, layer, mat, pts, facing, uv=None, grain=None, key="", two_sided=False):
        """pts: 4 corners in loop order. grain: 'ab' / 'ad' = board grain along p0->p1 / p0->p3 (wood_planks* only);
        'nat_ab' / 'nat_ad' = natural metres with the set's u along that edge."""
        P = [np.asarray(p, float) for p in pts]
        if uv is None and grain and (str(mat).startswith("wood_planks") or grain.startswith("nat")):
            lab, lad = float(np.linalg.norm(P[1] - P[0])), float(np.linalg.norm(P[3] - P[0]))
            if grain.startswith("nat"):
                s0 = BM.WOOD_TILE_M[0] * FK.hfloat(key, "nu")
                v0 = BM.WOOD_ROW_M * int(FK.hfloat(key, "nv") * 19)
                uv = ([[s0, v0], [s0 + lab, v0], [s0 + lab, v0 + lad], [s0, v0 + lad]] if grain == "nat_ab" else
                      [[s0, v0], [s0, v0 + lab], [s0 + lad, v0 + lab], [s0 + lad, v0]])
            else:
                s0, va, vb = _row(key)
                uv = ([[s0, va], [s0 + lab, va], [s0 + lab, vb], [s0, vb]] if grain == "ab" else
                      [[s0, va], [s0, vb], [s0 + lad, vb], [s0 + lad, va]])
        nrm = np.cross(P[1] - P[0], P[3] - P[0])
        if float(nrm @ np.asarray(facing, float)) < 0:
            P = [P[0], P[3], P[2], P[1]]
            uv = None if uv is None else [uv[0], uv[3], uv[2], uv[1]]
        self.acc.quad(layer, mat, *P, uv=uv)
        self.n[layer] += 2
        if two_sided:
            self.acc.quad(layer, mat, P[0], P[3], P[2], P[1], uv=None if uv is None else [uv[0], uv[3], uv[2], uv[1]])
            self.n[layer] += 2

    def poly(self, layer, mat, pts, facing, uv, two_sided=False):
        """Convex polygon as a fan (pts in loop order, uv per point)."""
        P = np.asarray(pts, float)
        UV = np.asarray(uv, float)
        if len(P) < 3:
            return
        nrm = np.cross(P[1] - P[0], P[-1] - P[0])
        if float(nrm @ np.asarray(facing, float)) < 0:
            P, UV = P[::-1], UV[::-1]
        T = [[0, i, i + 1] for i in range(1, len(P) - 1)]
        self.acc.add(layer, mat, P, T, UV)
        self.n[layer] += len(T)
        if two_sided:
            self.acc.add(layer, mat, P[::-1], T, UV[::-1])
            self.n[layer] += len(T)

    def box(self, layer, mat, c, ax, ay, az, grain=None, key="", skip=()):
        """Box (half axes). grain: 3D direction of the wood grain (board-row UV on every face) or None.
        skip: faces left out, '-x' '+x' '-y' '+y' '-z' '+z' in terms of (ax, ay, az)."""
        c, ax, ay, az = (np.asarray(v, float) for v in (c, ax, ay, az))
        for name, o, e1, e2 in (("-x", -ax, ay, az), ("+x", ax, ay, az), ("-y", -ay, ax, az), ("+y", ay, ax, az),
                                ("-z", -az, ax, ay), ("+z", az, ax, ay)):
            if name in skip:
                continue
            pts = [c + o - e1 - e2, c + o + e1 - e2, c + o + e1 + e2, c + o - e1 + e2]
            g = None
            if grain is not None:
                gd = np.asarray(grain, float)
                g = "ab" if abs(float(e1 @ gd)) / (np.linalg.norm(e1) + 1e-9) >= abs(float(e2 @ gd)) / (np.linalg.norm(e2) + 1e-9) else "ad"
            self.quad(layer, mat, pts, o, grain=g, key=(key, name))


def _lattice(m, layer, mat, o, ex, ey, outline, facing, key, pitch=0.105, lath=0.028):
    """Diagonal lattice (kratka) in the plane o + x ex + y ey inside the convex `outline` [(x, y)]: two layers of
    laths at +-45 deg, the second 12 mm behind the first, both seen from either side. Returns the lath count."""
    o, ex, ey = (np.asarray(v, float) for v in (o, ex, ey))
    back = -np.asarray(facing, float) / np.linalg.norm(facing)
    panel = Polygon(outline)
    xs, ys = np.asarray(outline, float).T
    count = 0
    for layer_k, sgn in enumerate((1.0, -1.0)):
        t = np.array([math.sqrt(0.5), sgn * math.sqrt(0.5)])
        p = np.array([-t[1], t[0]])
        cs = np.outer(xs, p[:1]).ravel() + ys * p[1]
        along = xs * t[0] + ys * t[1]
        c0 = math.floor(cs.min() / pitch) * pitch + pitch * FK.hfloat(key, layer_k, "ph")
        for c in np.arange(c0, cs.max() + pitch, pitch):
            a0, a1 = along.min() - 0.1, along.max() + 0.1
            strip = Polygon([t * a0 + p * (c - lath / 2), t * a1 + p * (c - lath / 2),
                             t * a1 + p * (c + lath / 2), t * a0 + p * (c + lath / 2)])
            g = strip.intersection(panel)
            if g.is_empty or g.geom_type != "Polygon" or g.area < 1e-4:
                continue
            xy = np.asarray(g.exterior.coords)[:-1]
            s0, va, vb = _row((key, layer_k, round(float(c), 3)))
            uv = np.column_stack((s0 + xy @ t, va + (xy @ p - (c - lath / 2)) / lath * (vb - va)))
            pts = o + np.outer(xy[:, 0], ex) + np.outer(xy[:, 1], ey) + back * (0.012 * layer_k)
            m.poly(layer, mat, pts, facing, uv, two_sided=True)
            count += 1
    return count


class _Wall:
    """Wall plane: a (E, N) at u = 0, d along (left to right seen from outside), n outward."""

    def __init__(self, a, d, n, L):
        self.a, self.d, self.n, self.L = np.asarray(a, float), np.asarray(d, float), np.asarray(n, float), float(L)
        self.d3, self.n3 = np.r_[self.d, 0.0], np.r_[self.n, 0.0]

    def p(self, u, z, out=0.0):
        q = self.a + self.d * u + self.n * out
        return np.array([q[0], q[1], z])


def _window(m, wl, uc, w, zs, zh, key, low=False, surround=True):
    """Dark brown two-light casement with three panes a light (photo 05), board surround with a sill."""
    u0, u1 = uc - w / 2, uc + w / 2
    if low:
        m.quad(L1, "plinth_dark", [wl.p(u0, zs, 0.03), wl.p(u1, zs, 0.03), wl.p(u1, zh, 0.03), wl.p(u0, zh, 0.03)], wl.n3)
        return
    m.quad(L0, GLASS, [wl.p(u0, zs, 0.025), wl.p(u1, zs, 0.025), wl.p(u1, zh, 0.025), wl.p(u0, zh, 0.025)], wl.n3)

    def bar(a0, a1, b0, b1, out=0.045):
        m.quad(L0, TRIM, [wl.p(a0, b0, out), wl.p(a1, b0, out), wl.p(a1, b1, out), wl.p(a0, b1, out)], wl.n3)
    f, mu = 0.05, 0.022
    bar(u0, u0 + f, zs, zh), bar(u1 - f, u1, zs, zh), bar(u0, u1, zs, zs + f), bar(u0, u1, zh - f, zh)
    bar(uc - 0.035, uc + 0.035, zs, zh)                                       # meeting stiles
    for k in (1, 2):                                                          # two glazing bars a light
        zb = zs + (zh - zs) * k / 3 + (0.03 if k == 2 else 0.0)
        bar(u0 + f, u1 - f, zb - mu / 2, zb + mu / 2, 0.04)
    if surround:
        s, pr = 0.085, 0.035
        for a0, a1, b0, b1, ext in ((u0 - s, u0, zs - 0.02, zh + s, pr), (u1, u1 + s, zs - 0.02, zh + s, pr),
                                    (u0 - s, u1 + s, zh, zh + s, pr), (u0 - s - 0.02, u1 + s + 0.02, zs - 0.06, zs, 0.06)):
            c = (wl.p(a0, b0) + wl.p(a1, b1)) / 2 + wl.n3 * (ext / 2)
            m.box(L0, TRIM, c, wl.d3 * (a1 - a0) / 2, wl.n3 * (ext / 2), [0, 0, (b1 - b0) / 2], skip=("-y",))


def _door(m, wl, uc, w, z0, z1, key, low=False):
    u0, u1 = uc - w / 2, uc + w / 2
    if low:
        m.quad(L1, "plinth_dark", [wl.p(u0, z0, 0.03), wl.p(u1, z0, 0.03), wl.p(u1, z1, 0.03), wl.p(u0, z1, 0.03)], wl.n3)
        return
    m.quad(L0, DOOR, [wl.p(u0, z0, 0.03), wl.p(u1, z0, 0.03), wl.p(u1, z1, 0.03), wl.p(u0, z1, 0.03)], wl.n3,
           grain="nat_ad", key=(key, "leaf"))
    s = 0.09
    for a0, a1, b0, b1 in ((u0 - s, u0, z0, z1 + s), (u1, u1 + s, z0, z1 + s), (u0 - s, u1 + s, z1, z1 + s)):
        c = (wl.p(a0, b0) + wl.p(a1, b1)) / 2 + wl.n3 * 0.02
        m.box(L0, TRIM, c, wl.d3 * (a1 - a0) / 2, wl.n3 * 0.02, [0, 0, (b1 - b0) / 2], skip=("-y",))


def _fence_line(a, d, n, L, pu0, pu1, pd, roads_poly, carriage=None):
    """Offset of the picket line from the street wall and its two runs [(u0, u1)]: (w, runs, on_footway, walkway m).
    The photos show the pickets flush with the porch front, along the back of the footway. Where the generated
    footway reaches further towards the wall than the real one (Koscielna: its back edge lies ~1 m from the wall,
    the porch is 2 m deep), the line still goes to the porch front when at least WALKWAY_MIN_M of footway stays
    between the pickets and the carriageway; otherwise it is pulled back off the road footprint, and dropped when no
    line 0.8 m or more off the wall is clear."""
    runs = [(-FENCE_PAST[0], pu0), (pu1, L + FENCE_PAST[1])]
    w = pd - 0.03
    if roads_poly is None:
        return w, runs, False, None

    def strips(w_):
        return [Polygon([a + d * u0 + n * 0.3, a + d * u1 + n * 0.3, a + d * u1 + n * w_, a + d * u0 + n * w_]) for u0, u1 in runs]
    if min(float(roads_poly.distance(st)) for st in strips(w)) >= ROAD_CLEAR_M:
        return w, runs, False, None
    if carriage is not None and not carriage.is_empty:
        walk = min(float(carriage.distance(st)) for st in strips(w))
        if walk >= WALKWAY_MIN_M:
            return w, runs, True, walk
    while w >= 0.8:                                           # the whole strip between the wall and the pickets is clear
        if min(float(roads_poly.distance(st)) for st in strips(w)) >= ROAD_CLEAR_M:
            return w, runs, False, None
        w -= 0.1
    return None


def build(buf, region, blds, zsmooth, report, roads_poly=None, carriage=None, surface=None):
    """surface: streetscape.furniture.SurfaceTop of the road layer (exact footway top) or None."""
    result = {"id": ASSET_ID, "status": "skipped", "sources": [BUILDING_ID]}
    if region != REGION:
        return result
    report[ASSET_ID] = result
    b = next((x for x in blds if x["id"] == BUILDING_ID), None)
    if b is None or b["ovr"].get("hero_asset") != ASSET_ID:
        result["reason"] = "hero target missing; the rule house stays"
        return result
    fr = _frame(b["poly"])
    if fr is None:
        result["reason"] = "footprint is not the long house with one porch"
        return result
    a, d, n, L, W, pu0, pu1, pd = fr
    ring = np.asarray(b["poly"].exterior.coords, float)
    zg = np.asarray(zsmooth(ring[:, 0], ring[:, 1]), float)
    if not np.all(np.isfinite(zg)):
        result["reason"] = "invalid terrain height"
        return result
    z0, zbot = float(np.median(zg)), float(zg.min()) - 0.5
    acc = BM.Acc()
    m = _Mesh(acc)
    d3, n3, up = np.r_[d, 0.0], np.r_[n, 0.0], np.array([0.0, 0.0, 1.0])
    pc, pw = (pu0 + pu1) / 2, pu1 - pu0

    def P(u, w, z):
        q = a + d * u + n * w
        return np.array([q[0], q[1], z])

    front = _Wall(a, d, n, L)
    east = _Wall(a + d * L, -n, d, W)
    back = _Wall(a + d * L - n * W, -d, -n, L)
    west = _Wall(a - n * W, n, -d, W)
    walls = (("front", front), ("east", east), ("back", back), ("west", west))
    zp, zw, ze, zr = z0 + PLINTH_TOP, z0 + WALL_TOP, z0 + EAVE_EDGE, z0 + RIDGE
    zs = ze - FASCIA_H                                         # soffit of the boxed eave
    slope = (RIDGE - EAVE_EDGE) / (W / 2 + EAVE_OV)
    slen = math.hypot(W / 2 + EAVE_OV, RIDGE - EAVE_EDGE)

    # ---- footing, log walls, corner boards
    for name, wl in walls:
        ph = 4.0 * FK.hfloat(ASSET_ID, name, "log")
        m.quad(L0, LOG, [wl.p(0, zp), wl.p(wl.L, zp), wl.p(wl.L, zw), wl.p(0, zw)], wl.n3,
               uv=[[ph, 0], [ph + wl.L, 0], [ph + wl.L, zw - zp], [ph, zw - zp]])
        m.quad(L1, LOG, [wl.p(0, zbot), wl.p(wl.L, zbot), wl.p(wl.L, zw), wl.p(0, zw)], wl.n3,
               uv=[[ph, zbot - zp], [ph + wl.L, zbot - zp], [ph + wl.L, zw - zp], [ph, zw - zp]])
        e, v0 = 0.04, z0 - 0.10                                # footing 4 cm proud; the damp foot of the set at the ground
        m.quad(L0, STONE, [wl.p(-e, zbot, e), wl.p(wl.L + e, zbot, e), wl.p(wl.L + e, zp, e), wl.p(-e, zp, e)], wl.n3,
               uv=[[ph, zbot - v0], [ph + wl.L, zbot - v0], [ph + wl.L, zp - v0], [ph, zp - v0]])
        m.quad(L0, STONE, [wl.p(-e, zp, e), wl.p(wl.L + e, zp, e), wl.p(wl.L + e, zp, 0), wl.p(-e, zp, 0)], up,
               uv=[[ph, zp - v0], [ph + wl.L, zp - v0], [ph + wl.L, zp - v0 + e], [ph, zp - v0 + e]])
        for k, uc in enumerate((0.07 - 0.0125, wl.L - 0.07 + 0.0125)):       # white corner boards 0.14 m
            c = wl.p(uc, (zp + zw) / 2, 0.0125)
            m.box(L0, BOARD_W, c, wl.d3 * 0.0825, wl.n3 * 0.0125, up * (zw - zp) / 2, grain=up,
                  key=(ASSET_ID, name, "corner", k), skip=("-y", "-z", "+z"))

    # ---- windows and doors
    for low in (False, True):
        for k, off in enumerate(FRONT_WINDOWS):
            _window(m, front, pc + off, WIN_W, z0 + WIN_SILL, z0 + WIN_HEAD, ("fw", k), low)
        for k, (uc, w) in enumerate(BACK_WINDOWS):
            _window(m, back, uc, w, z0 + WIN_SILL, z0 + WIN_HEAD, ("bw", k), low)
        _door(m, back, BACK_DOOR[0], BACK_DOOR[1], zp, z0 + 2.12, "bd", low)
        for name, wl in (("east", east), ("west", west)):
            for k, off in enumerate(GABLE_WINDOWS):
                _window(m, wl, W / 2 + off, WIN_W, z0 + WIN_SILL, z0 + WIN_HEAD, (name, "gw", k), low)
            _window(m, wl, W / 2, GABLE_WIN[0], z0 + GABLE_WIN[1], z0 + GABLE_WIN[2], (name, "attic"), low)
    _door(m, front, pc, 0.92, zp, z0 + 2.10, "fd")

    # ---- gables: vertical white boarding, attic window with its little roof, pent roof at the eave line
    for name, wl in (("east", east), ("west", west)):
        zr0 = ze + slope * EAVE_OV                              # roof underside on the wall line
        ph, pv = BM.WOOD_TILE_M[0] * FK.hfloat(ASSET_ID, name, "gu"), BM.WOOD_ROW_M * int(19 * FK.hfloat(ASSET_ID, name, "gv"))
        prof = [(0.0, zw), (W, zw), (W, zr0), (W / 2, zr), (0.0, zr0)]
        for layer in (L0, L1):
            m.poly(layer, BOARD_W, [wl.p(u, z) for u, z in prof], wl.n3, [[z - zw + ph, u + pv] for u, z in prof])
        uc, (gw, gs, gh) = W / 2, GABLE_WIN
        c0, c1, zc = uc - gw / 2 - 0.17, uc + gw / 2 + 0.17, z0 + gh
        lid = [wl.p(c0, zc + 0.13, 0.27), wl.p(c1, zc + 0.13, 0.27), wl.p(c1, zc + 0.26, 0.0), wl.p(c0, zc + 0.26, 0.0)]
        m.quad(L0, SHEET, lid, up)
        m.quad(L0, SOFFIT, lid, -up)
        m.quad(L0, BOARD_W, [wl.p(c0, zc + 0.06, 0.27), wl.p(c1, zc + 0.06, 0.27), wl.p(c1, zc + 0.13, 0.27),
                             wl.p(c0, zc + 0.13, 0.27)], wl.n3, grain="ab", key=(name, "lidf"))
        for k, (uu, sgn) in enumerate(((c0, -1.0), (c1, 1.0))):
            m.poly(L0, BOARD_W, [wl.p(uu, zc + 0.06, 0.0), wl.p(uu, zc + 0.06, 0.27), wl.p(uu, zc + 0.13, 0.27),
                                 wl.p(uu, zc + 0.26, 0.0)], wl.d3 * sgn, [[0, 0.3], [0.27, 0.3], [0.27, 0.37], [0, 0.42]])
        o = EAVE_OV
        zi, zo = z0 + PENT_Z[0], z0 + PENT_Z[1]
        pent = [wl.p(-o, zo, PENT_OUT), wl.p(W + o, zo, PENT_OUT), wl.p(W + o, zi, 0.0), wl.p(-o, zi, 0.0)]
        m.quad(L0, SHEET, pent, up)
        m.quad(L1, SHEET, pent, up)
        m.quad(L0, SOFFIT, [wl.p(-o, zo - 0.10, PENT_OUT), wl.p(W + o, zo - 0.10, PENT_OUT), wl.p(W + o, zo - 0.10, 0.0),
                            wl.p(-o, zo - 0.10, 0.0)], -up)
        m.quad(L0, BOARD_W, [wl.p(-o, zo - 0.10, PENT_OUT), wl.p(W + o, zo - 0.10, PENT_OUT), wl.p(W + o, zo, PENT_OUT),
                             wl.p(-o, zo, PENT_OUT)], wl.n3, grain="ab", key=(name, "pentf"))
        for uu, sgn in ((-o, -1.0), (W + o, 1.0)):
            m.poly(L0, BOARD_W, [wl.p(uu, zo - 0.10, 0.0), wl.p(uu, zo - 0.10, PENT_OUT), wl.p(uu, zo, PENT_OUT),
                                 wl.p(uu, zi, 0.0)], wl.d3 * sgn, [[0, 0.6], [PENT_OUT, 0.6], [PENT_OUT, 0.7], [0, 0.98]])

    # ---- main roof: old tile on two slopes, a ridge that sags a little, ridge tiles, barge boards, boxed eaves
    us = np.linspace(-GABLE_OV, L + GABLE_OV, 9)

    def ridge_z(u, layer):
        if layer == L1 or u <= us[0] + 1e-6 or u >= us[-1] - 1e-6:
            return zr
        return zr - 0.05 * math.sin(math.pi * (u + GABLE_OV) / (L + 2 * GABLE_OV)) + 0.016 * (FK.hfloat(ASSET_ID, "sag", round(u, 2)) - 0.5)

    for layer, uu in ((L0, us), (L1, us[[0, -1]])):
        for u0, u1 in zip(uu[:-1], uu[1:]):
            r0, r1 = ridge_z(u0, layer), ridge_z(u1, layer)
            m.quad(layer, TILE, [P(u0, EAVE_OV, ze), P(u1, EAVE_OV, ze), P(u1, -W / 2, r1), P(u0, -W / 2, r0)], n3 + up,
                   uv=[[u0, 0], [u1, 0], [u1, slen], [u0, slen]])
            m.quad(layer, TILE, [P(u1, -W - EAVE_OV, ze), P(u0, -W - EAVE_OV, ze), P(u0, -W / 2, r0), P(u1, -W / 2, r1)],
                   up - n3, uv=[[-u1, 0.17], [-u0, 0.17], [-u0, slen + 0.17], [-u1, slen + 0.17]])
            if layer == L0:
                for sgn in (1.0, -1.0):                         # ridge tiles
                    wa = -W / 2 + sgn * 0.15
                    m.quad(L0, TILE, [P(u0, wa, r0 - 0.15 * slope + 0.03), P(u1, wa, r1 - 0.15 * slope + 0.03),
                                      P(u1, -W / 2, r1 + 0.07), P(u0, -W / 2, r0 + 0.07)], n3 * sgn + up,
                           uv=[[u0 * sgn, 0.02], [u1 * sgn, 0.02], [u1 * sgn, 0.16], [u0 * sgn, 0.16]])
    for ue, ui, sgn in ((-GABLE_OV, 0.0, -1.0), (L + GABLE_OV, L, 1.0)):
        for wv, fz in ((EAVE_OV, 1.0), (-W - EAVE_OV, -1.0)):
            m.quad(L0, SOFFIT, [P(ue, wv, ze - 0.03), P(ui, wv, ze - 0.03), P(ui, -W / 2, zr - 0.03), P(ue, -W / 2, zr - 0.03)], -up)
            m.quad(L0, BOARD_W, [P(ue, wv, ze + 0.02), P(ue, -W / 2, zr + 0.02), P(ue, -W / 2, zr - 0.18), P(ue, wv, ze - 0.18)],
                   d3 * sgn, grain="ab", key=(ASSET_ID, "barge", sgn, fz), two_sided=True)
    for name, wl in (("front", front), ("back", back)):
        g = GABLE_OV
        m.quad(L0, SOFFIT, [wl.p(-g, zs, 0), wl.p(wl.L + g, zs, 0), wl.p(wl.L + g, zs, EAVE_OV), wl.p(-g, zs, EAVE_OV)], -up)
        for layer in (L0, L1):
            m.quad(layer, BOARD_W, [wl.p(-g, zs, EAVE_OV), wl.p(wl.L + g, zs, EAVE_OV), wl.p(wl.L + g, ze, EAVE_OV),
                                    wl.p(-g, ze, EAVE_OV)], wl.n3, grain="nat_ab", key=(ASSET_ID, name, "fascia"))
        for uu, sgn in ((-g, -1.0), (wl.L + g, 1.0)):
            m.poly(L0, BOARD_W, [wl.p(uu, zs, 0), wl.p(uu, zs, EAVE_OV), wl.p(uu, ze, EAVE_OV), wl.p(uu, ze + slope * EAVE_OV, 0)],
                   wl.d3 * sgn, [[0, 1.0], [EAVE_OV, 1.0], [EAVE_OV, 1.0 + FASCIA_H], [0, 1.0 + FASCIA_H + 0.1]])

    # ---- chimneys
    for k, off in enumerate(CHIMNEYS):
        cz0, cz1 = zr - 0.65, zr + 0.62
        c = P(pc + off, -W / 2 - 0.10, (cz0 + cz1) / 2)
        for layer in (L0, L1):
            m.box(layer, BRICK, c, d3 * 0.27, n3 * 0.27, up * (cz1 - cz0) / 2, skip=("-z",))
        m.box(L0, CONCRETE, P(pc + off, -W / 2 - 0.10, cz1 + 0.03), d3 * 0.31, n3 * 0.31, up * 0.03)

    # ---- porch: concrete floor and step, posts, board panels, lattice, tiled gable roof
    zf, zrl, zbm, zpe, zpr = z0 + 0.28, z0 + PORCH_RAIL, z0 + PORCH_BEAM, z0 + PORCH_EAVE, z0 + PORCH_RIDGE
    pfront = _Wall(a + d * pu0 + n * pd, d, n, pw)
    pwest = _Wall(a + d * pu0, n, -d, pd)
    peast = _Wall(a + d * pu1 + n * pd, -n, d, pd)
    psl = (PORCH_RIDGE - PORCH_EAVE) / (pw / 2 + PORCH_OV)
    pslen = math.hypot(pw / 2 + PORCH_OV, PORCH_RIDGE - PORCH_EAVE)
    wf, wb = pd + PORCH_FRONT_OV, -0.6
    for layer in (L0, L1):
        m.quad(layer, TILE, [P(pu0 - PORCH_OV, wf, zpe), P(pu0 - PORCH_OV, wb, zpe), P(pc, wb, zpr), P(pc, wf, zpr)], up - d3,
               uv=[[wf, 0], [wb, 0], [wb, pslen], [wf, pslen]])
        m.quad(layer, TILE, [P(pu1 + PORCH_OV, wb, zpe), P(pu1 + PORCH_OV, wf, zpe), P(pc, wf, zpr), P(pc, wb, zpr)], up + d3,
               uv=[[wb + 0.1, 0.17], [wf + 0.1, 0.17], [wf + 0.1, pslen + 0.17], [wb + 0.1, pslen + 0.17]])
    # LOD1: three board walls with a dark doorway under the same roof
    for wl in (pfront, pwest, peast):
        m.quad(L1, STAIN, [wl.p(0, zbot), wl.p(wl.L, zbot), wl.p(wl.L, zpe), wl.p(0, zpe)], wl.n3, grain="nat_ad", key=(ASSET_ID, "l1"))
    m.quad(L1, "plinth_dark", [pfront.p(pw / 2 - 0.5, zf, 0.03), pfront.p(pw / 2 + 0.5, zf, 0.03), pfront.p(pw / 2 + 0.5, zbm, 0.03),
                               pfront.p(pw / 2 - 0.5, zbm, 0.03)], n3)
    gz = zpr - psl * (pw / 2)                                   # roof underside over the porch side walls
    m.poly(L1, STAIN, [pfront.p(0, zpe), pfront.p(pw, zpe), pfront.p(pw, gz), pfront.p(pw / 2, zpr), pfront.p(0, gz)], n3,
           [[0, 0], [0, pw], [gz - zpe, pw], [zpr - zpe, pw / 2], [gz - zpe, 0]])
    # LOD0
    m.box(L0, CONCRETE, P(pc, pd / 2, (zbot + zf) / 2), d3 * pw / 2, n3 * pd / 2, up * (zf - zbot) / 2, skip=("-z", "-y"))
    m.box(L0, CONCRETE, P(pc, pd + 0.16, (zbot + z0 + 0.13) / 2), d3 * 0.70, n3 * 0.16, up * (z0 + 0.13 - zbot) / 2, skip=("-z", "-y"))
    jl, jr = pw / 2 - PORCH_DOOR_W / 2 - 0.05, pw / 2 + PORCH_DOOR_W / 2 + 0.05     # door posts (centres), porch u
    for k, (uu, ww) in enumerate(((0.05, pd - 0.05), (pw - 0.05, pd - 0.05), (jl, pd - 0.05), (jr, pd - 0.05), (0.05, 0.05), (pw - 0.05, 0.05))):
        m.box(L0, STAIN, P(pu0 + uu, ww, (zf + zbm) / 2), d3 * 0.05, n3 * 0.05, up * (zbm - zf) / 2, grain=up,
              key=(ASSET_ID, "post", k), skip=("-z", "+z"))
    hb = (zpe - zbm) / 2
    m.box(L0, STAIN, P(pc, pd - 0.05, zbm + hb), d3 * pw / 2, n3 * 0.05, up * hb, grain=d3, key=(ASSET_ID, "beam", 0))
    for k, uu in enumerate((pu0 + 0.05, pu1 - 0.05)):
        m.box(L0, STAIN, P(uu, pd / 2 - 0.05, zbm + hb), d3 * 0.05, n3 * (pd / 2 - 0.05), up * hb, grain=n3, key=(ASSET_ID, "beam", 1 + k))
    spans = [(pfront, 0.10, jl - 0.05, -0.05), (pfront, jr + 0.05, pw - 0.10, -0.05), (pwest, 0.10, pd - 0.10, -0.05), (peast, 0.10, pd - 0.10, -0.05)]
    laths = 0
    for k, (wl, s0, s1, out) in enumerate(spans):
        if s1 - s0 < 0.2:
            continue
        m.quad(L0, STAIN, [wl.p(s0, zf, out), wl.p(s1, zf, out), wl.p(s1, zrl - 0.07, out), wl.p(s0, zrl - 0.07, out)], wl.n3,
               grain="nat_ad", key=(ASSET_ID, "panel", k), two_sided=True)
        m.box(L0, STAIN, wl.p((s0 + s1) / 2, zrl - 0.035, out), wl.d3 * (s1 - s0) / 2, wl.n3 * 0.04, up * 0.035, grain=wl.d3,
              key=(ASSET_ID, "rail", k))
        laths += _lattice(m, L0, STAIN, wl.p(s0, zrl, out), wl.d3, up, [(0, 0), (s1 - s0, 0), (s1 - s0, zbm - zrl), (0, zbm - zrl)],
                          wl.n3, (ASSET_ID, "lat", k))
    laths += _lattice(m, L0, STAIN, pfront.p(0, zpe, -0.05), d3, up,
                      [(0.02, 0), (pw - 0.02, 0), (pw - 0.02, gz - zpe - 0.03), (pw / 2, zpr - zpe - 0.05), (0.02, gz - zpe - 0.03)],
                      n3, (ASSET_ID, "lat", "gable"))
    for sgn, ue in ((-1.0, pu0 - PORCH_OV), (1.0, pu1 + PORCH_OV)):
        m.quad(L0, BOARD_W, [P(ue, wf, zpe + 0.02), P(pc, wf, zpr + 0.02), P(pc, wf, zpr - 0.14), P(ue, wf, zpe - 0.14)], n3,
               grain="ab", key=(ASSET_ID, "pbarge", sgn), two_sided=True)
        m.quad(L0, BOARD_W, [P(ue, EAVE_OV, zpe - 0.10), P(ue, wf, zpe - 0.10), P(ue, wf, zpe), P(ue, EAVE_OV, zpe)], d3 * sgn,
               grain="ab", key=(ASSET_ID, "pfascia", sgn))
        m.quad(L0, STAIN, [P(ue, wf, zpe - 0.02), P(ue, EAVE_OV, zpe - 0.02), P(pc, EAVE_OV, zpr - 0.02), P(pc, wf, zpr - 0.02)], -up,
               grain="nat_ab", key=(ASSET_ID, "punder", sgn))

    # ---- picket fence along the footway (LOD0)
    fence = _fence_line(a, d, n, L, pu0, pu1, pd, roads_poly, carriage)
    pickets = 0

    def ground(q):
        """Top of the footway mesh where the point stands on it, else the smoothed terrain."""
        z = np.asarray(zsmooth(q[:, 0], q[:, 1]), float).copy()
        if surface is not None:
            for i, (e_, n_) in enumerate(q):
                t = surface.top(float(e_), float(n_))
                if math.isfinite(t) and abs(t - z[i]) < 0.6:
                    z[i] = max(z[i], t)
        return z

    if fence is not None:
        fw, runs = fence[0], fence[1]
        af = a + n * fw
        for r, (u0, u1) in enumerate(runs):
            nb = max(1, int(math.ceil((u1 - u0) / 2.4)))
            ub = np.linspace(u0, u1, nb + 1)
            gb = ground(af[None, :] + np.outer(ub, d))
            gw = ground(a[None, :] + n[None, :] * 0.045 + np.outer(ub, d))           # ground at the footing
            for j, (ua, zb_) in enumerate(zip(ub, gb)):          # posts behind the pickets
                m.box(L0, STAIN, np.r_[af + d * ua - n * 0.09, zb_ + 0.56], d3 * 0.045, n3 * 0.045, up * 0.56, grain=up,
                      key=(ASSET_ID, "fpost", r, j), skip=("-z",))
            for j in range(nb):
                ua, ub_, za, zb_ = ub[j], ub[j + 1], gb[j], gb[j + 1]
                # grass strip between the footing and the pickets, 5 cm proud of whatever lies under it (terrain or
                # the modelled footway), with a concrete edging under the pickets
                b0, b1 = max(ua, 0.0), min(ub_, L)
                if b1 - b0 > 0.05:
                    f0, f1 = (b0 - ua) / (ub_ - ua), (b1 - ua) / (ub_ - ua)
                    zf0, zf1 = za + (zb_ - za) * f0 + 0.05, za + (zb_ - za) * f1 + 0.05
                    zw0 = max(gw[j] + (gw[j + 1] - gw[j]) * f0 + 0.05, zf0)
                    zw1 = max(gw[j] + (gw[j + 1] - gw[j]) * f1 + 0.05, zf1)
                    q = [np.r_[a + d * b0 + n * 0.045, zw0], np.r_[a + d * b1 + n * 0.045, zw1],
                         np.r_[af + d * b1 - n * 0.03, zf1], np.r_[af + d * b0 - n * 0.03, zf0]]
                    m.quad(L0, BED, q, up, uv=[[float(p_[0]), float(p_[1])] for p_ in q])
                    m.quad(L0, CONCRETE, [np.r_[af + d * b0 - n * 0.03, zf0 - 0.25], np.r_[af + d * b1 - n * 0.03, zf1 - 0.25],
                                          np.r_[af + d * b1 - n * 0.03, zf1], np.r_[af + d * b0 - n * 0.03, zf0]], n3)
                ax = np.r_[d * (ub_ - ua) / 2, (zb_ - za) / 2]
                for h in (0.28, 0.82):                           # two rails
                    m.box(L0, STAIN, np.r_[af + d * (ua + ub_) / 2 - n * 0.022, (za + zb_) / 2 + h], ax, n3 * 0.022, up * 0.04,
                          grain=ax, key=(ASSET_ID, "frail", r, j, h), skip=("+y",))
                npk = max(1, int(round((ub_ - ua) / PICKET_PITCH)))
                for k in range(npk):
                    uc = ua + (k + 0.5) * (ub_ - ua) / npk
                    g = za + (zb_ - za) * (k + 0.5) / npk
                    key = (ASSET_ID, "picket", r, j, k)
                    top = g + PICKET_H + 0.012 * (FK.hfloat(key, "top") - 0.5)
                    BM.wood_board(acc, STAIN, af, d, n, uc - PICKET_W / 2, uc + PICKET_W / 2, g + 0.05, top, 0.022, key, layer=L0)
                    m.n[L0] += 8
                    m.quad(L0, STAIN, [np.r_[af + d * (uc - PICKET_W / 2), g + 0.05], np.r_[af + d * (uc + PICKET_W / 2), g + 0.05],
                                       np.r_[af + d * (uc + PICKET_W / 2), top], np.r_[af + d * (uc - PICKET_W / 2), top]], -n3,
                           grain="ad", key=(key, "b"))
                    pickets += 1

    acc.flush(buf, ASSET_ID)
    result.update(
        status="applied",
        confidence={"footprint_porch": "SOURCED BDOT10k", "eave_ridge": "SOURCED GUGiK LoD2 2017",
                    "openings_chimneys": "ESTIMATED from owner photos / orthophoto (+-0.3-0.5 m)",
                    "west_gable": "ESTIMATED (mirrors the east gable)", "member_sizes": "WORKING_VALUE"},
        body_m=[round(L, 2), round(W, 2)], porch_m=[round(pw, 2), round(pd, 2)], porch_centre_u_m=round(pc, 2),
        ground_z=[round(float(zg.min()), 2), round(z0, 2), round(float(zg.max()), 2)],
        roof_pitch_deg=round(math.degrees(math.atan(slope)), 1),
        windows={"street": len(FRONT_WINDOWS), "yard": len(BACK_WINDOWS), "gables": 2 * (len(GABLE_WINDOWS) + 1)},
        doors=2, chimneys=len(CHIMNEYS), lattice_laths=laths,
        fence={"offset_from_wall_m": None if fence is None else round(fence[0], 2), "pickets": pickets,
               "on_modelled_footway": bool(fence and fence[2]),
               "walkway_left_m": None if not (fence and fence[3] is not None) else round(fence[3], 2)},
        triangles={"lod0": m.n[L0], "lod1": m.n[L1]})
    return result
