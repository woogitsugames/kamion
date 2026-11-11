"""House plots (ADR 0107, review 0097 P1-h "domy na gołej łące"): plot outline, fence, gate + wicket, driveway and a
little garden around every single-family house.

Data. The tile has no cadastral parcels (EGiB is not in the pipeline) and BDOT10k carries no plot fences; OSM has
barrier=fence / wall ways mostly around industrial plots. So:
  * a real OSM / BDOT barrier that runs past a house IS the plot edge there: the generated outline shrinks to it and
    no second fence is built along it (PARALLEL_SKIP_M);
  * everything else is a RULE (WORKING_VALUE, not survey): a rectangle in the frame of the house - front towards the
    nearest road, set back to the road edge, 3-6 m beside the house, 7-15 m behind it - shrunk until it clears roads,
    other buildings, paved yards and the plots laid out before it. Houses within GROUP_GAP_M share one plot (a house
    and its garage, the two halves of a semi).
Everything is derived from the building id (sha1), so a rebuild gives the same plots; no state is kept.

Typology (WORKING_VALUE, the usual mix of a Białystok street of single-family houses; to be checked against the
owner's photos): street side - welded panels on a concrete plinth (anthracite / green), a wooden picket fence, a
prefabricated concrete fence; sides and back - mostly mesh on steel posts (green / galvanised), sometimes the
front type all round or concrete plates. Gate 3.5 m + wicket 1.0 m side by side on the street side, driveway of
pavers or gravel from the road edge past the house, a row of thujas along one fence on a third of the plots, 2-4
shrubs, 1-2 small (fruit-tree sized) broadleaf trees behind the house.

Budget (Low, ADR 0107): everything is POINT INSTANCES of a few prototypes (street_props.glb, drawn by WorldInstances
with GPU instancing) - no chunk mesh, no new chunk material, so the MeshRenderer draw count of the control cameras
does not change. Shrubs / trees are instances of the existing vegetation prototypes. No collision yet (open).

Does not touch streetscape.furniture (street fences / furniture: parallel work on `gpt-furniture-r1`).
"""
from __future__ import annotations

import math

import numpy as np
import shapely
from shapely.geometry import LineString, Point, Polygon

from . import facade_atlas as FA
from .facade_kit import hfloat, hpick

GROUP_GAP_M = 2.5             # houses closer than this share a plot
FRONT_M = (2.0, 9.0)          # fence line in front of the house: road edge - ROAD_CLEAR_M, clamped to this, m
FRONT_FREE_M = (4.0, 8.0)     # ... when no road lies within ROAD_SEARCH_M in front
BACK_M = (7.0, 15.0)          # behind the house, m
SIDE_M = (3.0, 6.0)           # beside the house, m
DRIVE_SIDE_MIN_M = 4.25       # the side the driveway passes the house on
ROAD_SEARCH_M = 45.0
ROAD_CLEAR_M = 1.0            # fence line off the road footprint (carriageway + pavement + verge), m
MIN_MARGIN_M = 1.5            # a side is never pulled closer to the house than this
MIN_AREA_RATIO = 1.8          # plot area / footprint area below which no plot is built
PARALLEL_SKIP_M = 1.6         # a bay this close to (and parallel with) an existing fence is not built
BIG_BUILDING_M2 = 80.0        # non-house buildings above this are obstacles; smaller ones are outbuildings of the plot
FENCE_H = {"mesh": 1.5, "panel": 1.5, "picket": 1.2, "concrete": 1.5}       # m (house fences; 2.03 m is industrial)
BAY_M = {"mesh": 2.5, "panel": 2.5, "picket": 2.5, "concrete": 2.0}
GATE_SLOT_M = 3.75            # 3.5 m double-leaf gate + posts
WICKET_SLOT_M = 1.25          # 1.0 m wicket + posts
TERRACE_MIN = 3               # houses in one group from which the row is a terrace (wicket per house, no gate / drive)
DRIVE_W_M = 3.0
DRIVE_TILE_M = 2.5
# Module of the plot outline, m. Rectangular plots are cut to whole modules and the gate group (3.75 + 1.25 m = two
# modules) starts on a module, so mesh / panel / picket fences close with whole 2.5 m bays: one prototype per type
# (no half bays). Where a run still has a rest (clipped plots, concrete bays of 2.0 m) the last bay is pushed back
# over the one before it by a whole number of the fence's own pattern pitch, so the doubled part shows no seam.
MODULE_M = 2.5
PITCH_M = {"mesh": 0.05, "panel": 0.05, "picket": 0.145}       # wire pitch of `fence_mesh`, picket + gap
# (front type, colour) weights and the side / back choice given the front
FRONT_TYPES = [("panel", "anthracite", 0.30), ("panel", "green", 0.15), ("picket", "wood", 0.20),
               ("mesh", "green", 0.15), ("mesh", "galv", 0.10), ("concrete", "concrete", 0.10)]
THUJA_SHARE = 0.35
TREE_SHARE = 0.7
FRUIT_TREE = ("maple", (3.2, 4.8))   # existing prototype scaled to an orchard tree (no fruit-tree prototype yet)


def _pick_w(items, *key):
    x = hfloat(*key) * sum(w for *_, w in items)
    for it in items:
        x -= it[-1]
        if x <= 0:
            return it[:-1]
    return items[-1][:-1]


def _frame(poly):
    r = np.asarray(poly.minimum_rotated_rectangle.exterior.coords)[:4]
    e0, e1 = r[1] - r[0], r[2] - r[1]
    l0, l1 = float(np.hypot(*e0)), float(np.hypot(*e1))
    eu = e0 / max(l0, 1e-6) if l0 >= l1 else e1 / max(l1, 1e-6)
    return r.mean(0), eu, np.array([-eu[1], eu[0]])


def _groups(houses):
    n = len(houses)
    par = list(range(n))

    def find(i):
        while par[i] != i:
            par[i] = par[par[i]]
            i = par[i]
        return i
    tree = shapely.STRtree([h["poly"] for h in houses])
    for i, h in enumerate(houses):
        for j in tree.query(h["poly"].buffer(GROUP_GAP_M)):
            if j > i and houses[j]["poly"].distance(h["poly"]) < GROUP_GAP_M:
                par[find(int(j))] = find(i)
    out = {}
    for i in range(n):
        out.setdefault(find(i), []).append(houses[i])
    return [sorted(g, key=lambda h: (-h["poly"].area, h["id"])) for g in sorted(out.values(), key=lambda g: min(h["id"] for h in g))]


def _segments(geom):
    out = []
    for g in getattr(geom, "geoms", [geom]):
        if g.geom_type == "LineString":
            c = np.asarray(g.coords)[:, :2]
            out += [(c[k], c[k + 1]) for k in range(len(c) - 1) if np.hypot(*(c[k + 1] - c[k])) > 0.5]
        elif g.geom_type in ("MultiLineString", "GeometryCollection"):
            out += _segments(g)
    return out


class _Near:
    """Existing fence segments: is a point next to one that runs parallel to direction t?"""

    def __init__(self):
        self.A, self.B = np.zeros((0, 2)), np.zeros((0, 2))
        self._new = []

    def add(self, segs):
        self._new += list(segs)

    def _flush(self):
        if self._new:
            self.A = np.vstack([self.A, np.array([s[0] for s in self._new])])
            self.B = np.vstack([self.B, np.array([s[1] for s in self._new])])
            self._new = []

    def parallel(self, m, t, r=PARALLEL_SKIP_M):
        self._flush()
        if not len(self.A):
            return False
        ab = self.B - self.A
        L2 = np.maximum((ab * ab).sum(1), 1e-9)
        k = np.clip(((m - self.A) * ab).sum(1) / L2, 0.0, 1.0)
        d = np.hypot(*(self.A + ab * k[:, None] - m).T)
        par = np.abs(ab @ t) / np.sqrt(L2) > 0.94
        return bool(np.any((d < r) & par))


def plan(houses, roads_poly, obstacles, barriers=(), seed=""):
    """Plot per house group. houses: [{id, poly}] (single-family houses), roads_poly: road footprint, obstacles:
    polygons a plot must not cover (big buildings, paved yards), barriers: existing fence lines (LineStrings).
    Returns [dict(id, poly, front (unit xy), frame (c, eu, ev), houses, style, gate, wicket, drive, ...)], laid out in
    id order (deterministic)."""
    shapely.prepare(roads_poly)
    road_clear = roads_poly.buffer(ROAD_CLEAR_M)
    bar_u = shapely.unary_union([b.buffer(0.5) for b in barriers]) if barriers else None
    static = [road_clear] + [o.buffer(1.0) for o in obstacles] + ([bar_u] if bar_u is not None else [])
    groups = _groups(houses)
    all_house = {h["id"]: h["poly"] for h in houses}
    plots, laid = [], []
    for g in groups:
        key = f"{seed}{g[0]['id']}"
        foot = shapely.unary_union([h["poly"] for h in g])
        c, eu, ev = _frame(g[0]["poly"])
        ring = np.concatenate([np.asarray(h["poly"].exterior.coords)[:, :2] for h in g]) - c
        U, V = ring @ eu, ring @ ev
        bb = [float(U.min()), float(U.max()), float(V.min()), float(V.max())]
        cu, cv = 0.5 * (bb[0] + bb[1]), 0.5 * (bb[2] + bb[3])
        # front = the frame direction with the nearest road in front of the house
        best = None
        for du, dv in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            d = eu * du + ev * dv
            p0 = c + eu * (bb[1] if du > 0 else bb[0] if du < 0 else cu) + ev * (bb[3] if dv > 0 else bb[2] if dv < 0 else cv)
            hit = LineString([p0, p0 + d * ROAD_SEARCH_M]).intersection(roads_poly)
            if not hit.is_empty:
                dist = float(Point(*p0).distance(hit))
                if best is None or dist < best[0]:
                    best = (dist, du, dv)
        if best is None:
            du, dv = hpick([(1, 0), (-1, 0), (0, 1), (0, -1)], key, "front")
            mf = FRONT_FREE_M[0] + (FRONT_FREE_M[1] - FRONT_FREE_M[0]) * hfloat(key, "mf")
            road_d = None
        else:
            road_d, du, dv = best
            mf = min(max(road_d - ROAD_CLEAR_M, FRONT_M[0]), FRONT_M[1])
        mb = BACK_M[0] + (BACK_M[1] - BACK_M[0]) * hfloat(key, "mb")
        ms = [SIDE_M[0] + (SIDE_M[1] - SIDE_M[0]) * hfloat(key, "ms", k) for k in (0, 1)]
        drive_side = 0 if hfloat(key, "drive") < 0.5 else 1
        ms[drive_side] = max(ms[drive_side], DRIVE_SIDE_MIN_M)
        # margins [u-, u+, v-, v+]
        if du:
            mg = [mb if du > 0 else mf, mf if du > 0 else mb, ms[0], ms[1]]
        else:
            mg = [ms[0], ms[1], mb if dv > 0 else mf, mf if dv > 0 else mb]
        others = [p.buffer(0.8) for hid, p in all_house.items() if hid not in {h["id"] for h in g}
                  and p.distance(foot) < 40.0]
        obs = shapely.unary_union(static + others + laid) if (static or others or laid) else Polygon()

        def rect(m):
            cs = [(bb[0] - m[0], bb[2] - m[2]), (bb[1] + m[1], bb[2] - m[2]), (bb[1] + m[1], bb[3] + m[3]),
                  (bb[0] - m[0], bb[3] + m[3])]
            return Polygon([c + eu * u + ev * v for u, v in cs])
        poly = rect(mg)
        for _ in range(60):
            a0 = poly.intersection(obs).area
            if a0 < 0.3:
                break
            trials = []
            for k in range(4):
                if mg[k] - 1.0 >= MIN_MARGIN_M - 1e-6:
                    m2 = list(mg)
                    m2[k] -= 1.0
                    trials.append((rect(m2).intersection(obs).area, k))
            if not trials:
                break
            a1, k = min(trials)
            if a1 >= a0 - 1e-3:
                break
            mg[k] -= 1.0
            poly = rect(mg)
        if poly.intersection(obs).area < 0.3:               # a clean rectangle: cut it down to whole modules
            for ks in ((2, 3) if du else (0, 1), (0, 1) if du else (2, 3)):
                size = (bb[1] - bb[0] + mg[0] + mg[1]) if ks == (0, 1) else (bb[3] - bb[2] + mg[2] + mg[3])
                cutm = size - math.floor(size / MODULE_M + 1e-6) * MODULE_M
                # take it off the back / the side without the driveway first, then the other one
                order = sorted(ks, key=lambda k: -mg[k])
                for k in order:
                    take = min(cutm, max(mg[k] - MIN_MARGIN_M, 0.0))
                    mg[k] -= take
                    cutm -= take
            poly = rect(mg)
        if poly.intersection(obs).area >= 0.3:              # still on something: cut it off, keep the house's part
            parts = [q for q in getattr(poly.difference(obs.buffer(0.01)), "geoms", [poly.difference(obs.buffer(0.01))])
                     if q.geom_type == "Polygon" and q.area > 1.0]
            parts = [q for q in parts if q.intersects(foot)]
            if not parts:
                continue
            poly = max(parts, key=lambda q: q.intersection(foot.buffer(1.0)).area).simplify(0.3)
        if poly.is_empty or poly.geom_type != "Polygon" or poly.area < MIN_AREA_RATIO * foot.area:
            continue
        front = eu * du + ev * dv
        ft, fc = _pick_w(FRONT_TYPES, key, "ft")
        x = hfloat(key, "side")
        if ft in ("mesh",):
            st, sc = ft, fc
        elif x < 0.60:
            st, sc = "mesh", ("green" if hfloat(key, "sidec") < 0.6 else "galv")
        elif x < 0.85:
            st, sc = ft, fc
        else:
            st, sc = "concrete", "concrete"
        gate_col = {"anthracite": "anthracite", "green": "green", "galv": "galv", "wood": "wood",
                    "concrete": "anthracite"}[fc]
        plots.append({"id": g[0]["id"], "poly": poly, "front": front, "frame": (c, eu, ev), "bbox": bb,
                      "houses": [h["id"] for h in g], "foot": foot,
                      "house_pts": [np.asarray(h["poly"].centroid.coords[0]) for h in g], "road_d": road_d, "drive_side": drive_side,
                      "front_style": (ft, fc), "side_style": (st, sc), "gate_col": gate_col,
                      "surface": "paving" if hfloat(key, "surf") < 0.6 else "gravel", "key": key})
        laid.append(poly)
    return plots


def _edges(poly):
    r = np.asarray(shapely.geometry.polygon.orient(poly).exterior.coords)[:, :2]
    out = []
    for a, b in zip(r[:-1], r[1:]):
        L = float(np.hypot(*(b - a)))
        if L > 0.3:
            t = (b - a) / L
            out.append((a, b, L, t, np.array([t[1], -t[0]])))        # outward normal of a CCW ring
    return out


def layout(plot, cut=None, near=None):
    """Fence bays, gate, wicket and driveway of one plot.
    cut: polygon the fence does not cross (roads, buildings); near: _Near of existing fences (bays next to and
    parallel with one are not built). Returns dict(bays=[(proto, mid xy, normal xy, a, b)], gate, wicket, drive)."""
    key = plot["key"]
    c, eu, ev = plot["frame"]
    front = plot["front"]
    bb = plot["bbox"]
    edges = _edges(plot["poly"])
    fr = [e for e in edges if float(e[4] @ front) > 0.7]
    out = {"bays": [], "gate": None, "wicket": None, "wickets": [], "drive": [], "segs": []}
    gate_iv = {}
    if fr:
        ge = max(fr, key=lambda e: e[2])
        a, b, L, t, n = ge
        # driveway axis: between the house and the side fence on the drive side, in the plot frame
        side_ax = ev if abs(float(front @ eu)) > 0.5 else eu
        lo, hi = (bb[2], bb[3]) if side_ax is ev else (bb[0], bb[1])
        s_a, s_b = float((a - c) @ side_ax), float((b - c) @ side_ax)
        e_lo, e_hi = min(s_a, s_b), max(s_a, s_b)
        if plot["drive_side"] == 0:
            ax = 0.5 * (e_lo + lo)
            ax = min(ax, lo - DRIVE_W_M / 2 - 0.3) if lo - e_lo > DRIVE_W_M + 0.8 else ax
        else:
            ax = 0.5 * (hi + e_hi)
            ax = max(ax, hi + DRIVE_W_M / 2 + 0.3) if e_hi - hi > DRIVE_W_M + 0.8 else ax
        sg = (ax - s_a) / (s_b - s_a) * L if abs(s_b - s_a) > 1e-6 else L / 2      # along the edge from a
        w_side = 1.0 if (plot["drive_side"] == 0) == (s_b > s_a) else -1.0             # wicket towards the house
        if len(plot["houses"]) >= TERRACE_MIN:               # terrace: a wicket in front of every house, no shared gate
            for k, hp in enumerate(plot["house_pts"]):
                sw = float((hp - a) @ t)
                w0 = round((sw - WICKET_SLOT_M / 2) / WICKET_SLOT_M) * WICKET_SLOT_M       # on the half module
                # every fence run between the wickets and the corners is empty or at least one bay long
                if (0.0 <= w0 and w0 + WICKET_SLOT_M <= L + 1e-6 and (w0 < 1e-6 or w0 >= MODULE_M - 1e-6)
                        and (L - w0 - WICKET_SLOT_M < 0.3 or L - w0 - WICKET_SLOT_M >= MODULE_M - 1e-6)
                        and all(abs(w0 - x[0]) >= MODULE_M + WICKET_SLOT_M - 1e-6 for x in gate_iv.values())):
                    gate_iv[f"wicket{k}"] = (w0, w0 + WICKET_SLOT_M)
        elif L >= GATE_SLOT_M + WICKET_SLOT_M - 1e-6:
            # gate + wicket = two modules, starting on a module from corner a; a rest of the edge that is no whole
            # module goes to the far side when a pushed-back bay can close it, else the group ends on corner b
            grp = GATE_SLOT_M + WICKET_SLOT_M
            g0 = round((sg - (GATE_SLOT_M / 2 if w_side > 0 else GATE_SLOT_M / 2 + WICKET_SLOT_M)) / MODULE_M) * MODULE_M
            g0 = min(max(g0, 0.0), math.floor((L - grp) / MODULE_M + 1e-6) * MODULE_M)
            rest = L - g0 - grp
            if 0.3 < rest < MODULE_M - 1e-6:
                g0 = L - grp
            if w_side > 0:
                gate_iv["gate"], gate_iv["wicket"] = (g0, g0 + GATE_SLOT_M), (g0 + GATE_SLOT_M, g0 + grp)
            else:
                gate_iv["wicket"], gate_iv["gate"] = (g0, g0 + WICKET_SLOT_M), (g0 + WICKET_SLOT_M, g0 + grp)
        elif L >= GATE_SLOT_M + 0.5:
            g0 = 0.0 if sg < L / 2 else L - GATE_SLOT_M
            gate_iv["gate"] = (g0, g0 + GATE_SLOT_M)
        elif L >= WICKET_SLOT_M + 0.5:
            w0 = 0.0 if sg < L / 2 else L - WICKET_SLOT_M
            gate_iv["wicket"] = (w0, w0 + WICKET_SLOT_M)
        for kind, (s0, s1) in list(gate_iv.items()):
            m = a + t * 0.5 * (s0 + s1)
            seg = LineString([a + t * s0, a + t * s1])
            if (cut is not None and seg.intersects(cut)) or (near is not None and near.parallel(m, t)):
                del gate_iv[kind]
                continue
            if kind in ("gate", "wicket"):
                out[kind] = (f"plot_{kind}_{plot['gate_col']}", m, n)
            else:
                out["wickets"].append((f"plot_wicket_{plot['gate_col']}", m, n))
    for e in edges:
        a, b, L, t, n = e
        is_front = float(n @ front) > 0.7
        typ, col = plot["front_style"] if is_front else plot["side_style"]
        bay = BAY_M[typ]
        name = f"plot_fence_{typ}" + ("" if typ in ("picket", "concrete") else f"_{col}")
        ivs = [(0.0, L)]
        if fr and e is ge:
            for s0, s1 in sorted(gate_iv.values()):
                ivs = [x for i0, i1 in ivs for x in ((i0, min(i1, s0)), (max(i0, s1), i1)) if x[1] - x[0] > 0.3]
        for i0, i1 in ivs:
            line = LineString([a + t * i0, a + t * i1])
            pieces = [line] if cut is None else [q for q in getattr(line.difference(cut), "geoms", [line.difference(cut)])
                                                 if q.geom_type == "LineString" and q.length > 0.6]
            for q in pieces:
                p0, p1 = (np.asarray(x) for x in q.coords[:2])
                Lq = float(np.hypot(*(p1 - p0)))
                nb = int(Lq / bay + 1e-6)
                spans = [(k * bay, (k + 1) * bay, False) for k in range(nb)]
                rem = Lq - nb * bay
                if rem > 0.05 and typ == "concrete":        # 2.0 m plates: half bays, the last one pushed back
                    if rem > bay / 2:
                        spans.append((nb * bay, nb * bay + bay / 2, True))
                    if Lq >= bay / 2:
                        spans.append((Lq - bay / 2, Lq, True))
                elif rem > 0.05 and nb >= 1:                # one more whole bay, pushed back by whole pattern pitches
                    back = math.ceil((bay - rem) / PITCH_M[typ] - 1e-6) * PITCH_M[typ]
                    spans.append((nb * bay - back, nb * bay - back + bay, False))
                # a run shorter than a bay (clipped plots only) stays open: no prototype shorter than a bay
                for s0, s1, half in spans:
                    q0, q1 = p0 + t * s0, p0 + t * s1
                    m = 0.5 * (q0 + q1)
                    if near is not None and near.parallel(m, t):
                        continue
                    v = ""
                    if typ == "concrete" and not half:
                        v = "_a" if hfloat(key, "cv", round(float(m[0]), 1), round(float(m[1]), 1)) < 0.5 else "_b"
                    out["bays"].append((name + v + ("_h" if half else ""), m, n, q0, q1))
                out["segs"].append((p0, p1))
    if out["gate"] is not None:                             # driveway: road edge -> gate -> past the house front
        _, m, n = out["gate"]
        inward = -n
        depth_in = float(max((bb[1] - bb[0]) if abs(float(front @ eu)) > 0.5 else (bb[3] - bb[2]), 4.0))
        d_front = float(Point(*m).distance(plot["foot"]))
        L_in = min(d_front + min(depth_in, 7.0) + 0.5, 22.0)
        out["drive"] = [("in", m, inward, L_in)]
        if plot["road_d"] is not None:
            out["drive"].append(("out", m, n, None))        # length: to the road footprint (build)
    return out


# ------------------------------------------------------------------------------------------- prototypes
# Steel posts / frames are drawn with the fence's own alpha-tested mesh material, every vertex pinned to an opaque
# texel of `fence_mesh` (the centre of a vertical wire: 3 px wide at u = 0, full height): one submesh = one instanced
# draw per steel prototype instead of two (the post material has the same colour).
PIN_UV = (1.5 / 512.0, 0.5)


def _box(m, mat, c, hx, hy, hz, pin=False):
    if not pin:
        m.box(mat, c, hx, hy, hz)
        return
    c = np.asarray(c, float)
    P = [c + [sx * hx, sy * hy, sz * hz] for sz in (-1, 1) for sy in (-1, 1) for sx in (-1, 1)]
    for f in ((0, 2, 3, 1), (4, 5, 7, 6), (0, 1, 5, 4), (2, 6, 7, 3), (0, 4, 6, 2), (1, 3, 7, 5)):
        m.add(mat, [P[i] for i in f], [(0, 1, 2), (0, 2, 3)], [PIN_UV] * 4)


def _post(m, mat, x, s, h, deep=0.3, pin=False):
    _box(m, mat, [x, 0.0, (h - deep) / 2], s / 2, s / 2, (h + deep) / 2, pin)


def _dq(m, mat, x0, x1, z0, z1, y=0.0, uv=None):
    """Double-sided vertical quad in the xz plane at y."""
    uv = uv or [[x0, z0], [x1, z0], [x1, z1], [x0, z1]]
    A, B, C, D = [x0, y, z0], [x1, y, z0], [x1, y, z1], [x0, y, z1]
    m.quad(mat, A, B, C, D, uv)                              # faces -y ... +y by winding; both added
    m.quad(mat, B, A, D, C, [uv[1], uv[0], uv[3], uv[2]])


def fence_mesh(L, col, plinth, h):
    from . import props as PP
    mesh = f"fence_{col}_mesh"
    lod0, lod1 = PP.Mesh(), PP.Mesh()
    zb = 0.22 if plinth else 0.04
    for mm in (lod0, lod1):
        _dq(mm, mesh, -L / 2, L / 2, zb, h)
        if plinth:                                           # concrete plinth (podmurówka) 5 cm, 0.4 m into the ground
            mm.box("concrete_plinth", [0.0, 0.0, (zb - 0.4) / 2], L / 2, 0.03, (zb + 0.4) / 2)
    for x in (-L / 2, L / 2):
        _post(lod0, mesh, x, 0.06 if plinth else 0.05, h + 0.05, pin=True)
    return lod0, lod1, None


def fence_picket(L, h):
    from . import props as PP
    lod0, lod1 = PP.Mesh(), PP.Mesh()
    mat = "wood_planks"
    for x in (-L / 2, L / 2):
        _post(lod0, mat, x, 0.09, h + 0.05)
    for z in (0.30, h - 0.25):
        lod0.box(mat, [0.0, -0.035, z], L / 2, 0.012, 0.035)   # rails behind the pickets
    pw, gap = 0.09, 0.055
    n = int((L - 0.09) / (pw + gap))
    x0 = -((n - 1) * (pw + gap)) / 2
    for k in range(n):
        x = x0 + k * (pw + gap)
        top = h - 0.02 * ((k * 7) % 3)                        # hand-nailed: tops within 4 cm
        for mm in (lod0, lod1):
            _dq(mm, mat, x - pw / 2, x + pw / 2, 0.06, top, y=0.0,
                uv=[[0.06, x - pw / 2], [0.06, x + pw / 2], [top, x + pw / 2], [top, x - pw / 2]])
    return lod0, lod1, None


def fence_concrete(L, variant, h):
    from . import props as PP
    lod0, lod1 = PP.Mesh(), PP.Mesh()
    u0, v0, w, hh = FA.fence_uv("plate", variant)
    pu, pv, pw, ph = FA.fence_post_uv()
    uw = w * L / FA.FENCE_BAY[0]
    for mm in (lod0, lod1):
        for sg in (1, -1):
            y = 0.025 * sg
            A, B, C, D = [-L / 2 * sg, y, -0.3], [L / 2 * sg, y, -0.3], [L / 2 * sg, y, h], [-L / 2 * sg, y, h]
            uv = [[u0, v0 + hh - h - 0.3], [u0 + uw, v0 + hh - h - 0.3], [u0 + uw, v0 + hh], [u0, v0 + hh]]
            mm.quad("concrete_fence", B, A, D, C, [uv[1], uv[0], uv[3], uv[2]])     # faces +y (sg > 0) / -y
    lod0.quad("concrete_fence", [-L / 2, -0.025, h], [L / 2, -0.025, h], [L / 2, 0.025, h], [-L / 2, 0.025, h],
              [[pu + 0.02, pv + 0.1], [pu + 0.02, pv + 0.1 + L], [pu + 0.07, pv + 0.1 + L], [pu + 0.07, pv + 0.1]])
    for x in (-L / 2, L / 2):                                # H-posts 12 x 14 cm, 8 cm above the plates
        z0, z1 = -0.3, h + 0.08
        cs = [(x - 0.06, -0.07), (x + 0.06, -0.07), (x + 0.06, 0.07), (x - 0.06, 0.07)]
        vv = ph * min(1.0, (z1 - z0) / 2.4)
        for j in range(4):
            a_, b_ = cs[j], cs[(j + 1) % 4]
            uu = pu + 0.02 + 0.07 * j
            lod0.quad("concrete_fence", [a_[0], a_[1], z0], [b_[0], b_[1], z0], [b_[0], b_[1], z1], [a_[0], a_[1], z1],
                      [[uu, pv], [uu + 0.06, pv], [uu + 0.06, pv + vv], [uu, pv + vv]])
        lod0.quad("concrete_fence", [cs[0][0], cs[0][1], z1], [cs[1][0], cs[1][1], z1], [cs[2][0], cs[2][1], z1],
                  [cs[3][0], cs[3][1], z1], [[pu + 0.05, pv + 1.0], [pu + 0.15, pv + 1.0], [pu + 0.15, pv + 1.1], [pu + 0.05, pv + 1.1]])
    return lod0, lod1, None


def gate(W, col, h=1.5, leaves=2):
    """Swing gate / wicket in a slot W + 0.25 m: square posts, leaf frames of 4 cm box section, infill = the fence
    mesh (steel) or pickets (wood). Leaves hang 8 cm clear of the ground."""
    from . import props as PP
    lod0, lod1 = PP.Mesh(), PP.Mesh()
    wood = col == "wood"
    frame = "wood_planks" if wood else f"fence_{col}_mesh"
    pin = not wood
    for x in (-(W / 2 + 0.06), W / 2 + 0.06):
        _post(lod0, frame, x, 0.10, h + 0.12, pin=pin)
        _post(lod1, frame, x, 0.10, h + 0.12, pin=pin)
    lw = W / leaves
    for k in range(leaves):
        x0, x1 = -W / 2 + k * lw + 0.015, -W / 2 + (k + 1) * lw - 0.015
        for z in (0.10, h - 0.02):
            _box(lod0, frame, [0.5 * (x0 + x1), 0.0, z], (x1 - x0) / 2, 0.02, 0.02, pin)
        for x in (x0 + 0.02, x1 - 0.02):
            _box(lod0, frame, [x, 0.0, 0.5 * (0.10 + h - 0.02)], 0.02, 0.02, 0.5 * (h - 0.12), pin)
        if wood:
            pw, gap = 0.09, 0.055
            n = int((x1 - x0 - 0.04) / (pw + gap))
            xs = 0.5 * (x0 + x1) - ((n - 1) * (pw + gap)) / 2
            for i in range(n):
                x = xs + i * (pw + gap)
                for mm in (lod0, lod1):
                    _dq(mm, frame, x - pw / 2, x + pw / 2, 0.08, h, y=0.022,
                        uv=[[0.08, x - pw / 2], [0.08, x + pw / 2], [h, x + pw / 2], [h, x - pw / 2]])
        else:
            for mm in (lod0, lod1):
                _dq(mm, f"fence_{col}_mesh", x0 + 0.04, x1 - 0.04, 0.12, h - 0.04)
    return lod0, lod1, None


def drive_tile(L, mat, W=DRIVE_W_M):
    """Driveway tile W x L m, top 4 cm over its origin, skirts 0.35 m down (it steps with the ground like the kerbed
    edge of a paved drive). UV0 in metres."""
    from . import props as PP
    lod0, lod1 = PP.Mesh(), PP.Mesh()
    z = 0.04
    c = [(-W / 2, -L / 2), (W / 2, -L / 2), (W / 2, L / 2), (-W / 2, L / 2)]
    for mm in (lod0, lod1):
        mm.quad(mat, *[[x, y, z] for x, y in c], [[x, y] for x, y in c])
    for j in range(4):
        (ax, ay), (bx, by) = c[j], c[(j + 1) % 4]
        e = math.hypot(bx - ax, by - ay)
        lod0.quad(mat, [ax, ay, z - 0.35], [bx, by, z - 0.35], [bx, by, z], [ax, ay, z], [[0, 0], [e, 0], [e, 0.35], [0, 0.35]])
    return lod0, lod1, None


def thuja(h=2.3, r=0.42):
    """Columnar thuja ('Smaragd'): opaque dark core + alpha leaf shell (the clipped-hedge materials of ADR 0049)."""
    from . import props as PP
    from .hedge_textures import HEDGE_TILE_M
    lod0, lod1 = PP.Mesh(), PP.Mesh()
    prof = [(0.0, 0.55), (0.12, 0.95), (0.45, 1.0), (0.75, 0.72), (0.93, 0.34), (1.0, 0.05)]     # (height share, radius share)

    def shell(mm, mat, seg, rr, tile, grow=0.0):
        ang = np.linspace(0, 2 * math.pi, seg + 1)
        rings = [(np.column_stack([np.cos(ang) * (rr * k + grow), np.sin(ang) * (rr * k + grow), np.full(seg + 1, f * h)]),
                  np.column_stack([ang * rr / tile, np.full(seg + 1, f * h / tile)])) for f, k in prof]
        for (V0, U0), (V1, U1) in zip(rings, rings[1:]):
            for i in range(seg):
                mm.quad(mat, V0[i], V0[i + 1], V1[i + 1], V1[i], [U0[i], U0[i + 1], U1[i + 1], U1[i]])
    shell(lod0, "hedge_thuja", 7, r - 0.07, 1.0)
    shell(lod0, "hedge_shell_thuja", 9, r, HEDGE_TILE_M, grow=0.02)
    shell(lod1, "hedge_thuja", 5, r - 0.03, 1.0)
    return lod0, lod1, None


def protos():
    """{prototype name: (lod0, lod1, collision)} of the plot kit (street_props.glb)."""
    P = {}
    for col in ("green", "galv"):
        P[f"plot_fence_mesh_{col}"] = fence_mesh(BAY_M["mesh"], col, False, FENCE_H["mesh"])
    for col in ("anthracite", "green"):
        P[f"plot_fence_panel_{col}"] = fence_mesh(BAY_M["panel"], col, True, FENCE_H["panel"])
    P["plot_fence_picket"] = fence_picket(BAY_M["picket"], FENCE_H["picket"])
    P["plot_fence_concrete_a"] = fence_concrete(BAY_M["concrete"], 0, FENCE_H["concrete"])
    P["plot_fence_concrete_b"] = fence_concrete(BAY_M["concrete"], 2, FENCE_H["concrete"])
    P["plot_fence_concrete_h"] = fence_concrete(BAY_M["concrete"] / 2, 4, FENCE_H["concrete"])
    for col in ("green", "galv", "anthracite", "wood"):
        hh = 1.25 if col == "wood" else 1.5
        P[f"plot_gate_{col}"] = gate(GATE_SLOT_M - 0.25, col, hh, 2)
        P[f"plot_wicket_{col}"] = gate(WICKET_SLOT_M - 0.25, col, hh, 1)
    for surf, mat in (("paving", "yard_paving"), ("gravel", "yard_gravel")):
        P[f"plot_drive_{surf}"] = drive_tile(DRIVE_TILE_M, mat)
    P["plot_thuja"] = thuja()
    return P


# ------------------------------------------------------------------------------------------- build
def _yaw(f):
    return math.atan2(f[1], f[0]) - math.pi / 2


def build(pl, blds, roads_poly, bpoly, paved, src, origin, zground, report, seed=""):
    """Lay out and instance the plots of every house of the region. pl: furniture.Placer (items = instances),
    blds: buildings_mesh.load() list, paved: paved areas [{poly}], src: streetscape sources (OSM / BDOT barriers),
    zground(e, n): terrain height. Returns dict(keepout=[polygons trees must not stand on], lawns=[plot polygons])."""
    houses = [{"id": b["id"], "poly": b["poly"]} for b in blds if b["typ"] == "house"]
    obstacles = [b["poly"] for b in blds if b["typ"] != "house" and b["poly"].area >= BIG_BUILDING_M2]
    obstacles += [p["poly"] for p in paved if p["poly"].area > 20.0]
    barriers = []
    for f in src["osm"]["ways"]:
        if f["tags"].get("barrier") in ("fence", "yes", "wall", "retaining_wall", "hedge"):
            barriers.append(LineString(np.asarray(f["geometry"]["coordinates"], float)[:, :2] - np.asarray(origin)[:2]))
    for layer in ("OT_BUUO_L", "OT_OIKM_L"):
        for f in src["bdot10k"].get(layer, []):
            g = f["geometry"]
            for cs in ([g["coordinates"]] if g["type"] == "LineString" else g["coordinates"] if g["type"] == "MultiLineString" else []):
                barriers.append(LineString(np.asarray(cs, float)[:, :2] - np.asarray(origin)[:2]))
    plots = plan(houses, roads_poly, obstacles, barriers, seed)
    cut = shapely.unary_union([roads_poly.buffer(0.3), bpoly.buffer(0.3)])
    shapely.prepare(cut)
    near = _Near()
    near.add([s for b in barriers for s in _segments(b)])
    rep = {"houses": len(houses), "plots": len(plots), "fence_m": {}, "bays": 0, "gates": 0, "wickets": 0,
           "drive_tiles": 0, "thujas": 0, "shrubs": 0, "trees": 0, "instances": 0, "plot_m2_median": 0.0}
    n0 = len(pl.items)
    keepout, lawns = [], []

    def zg(p):
        return float(np.asarray(zground(np.array([p[0]]), np.array([p[1]]))).ravel()[0])

    def veg(proto_sp, p, h, key, k):
        pl.items.append({"p": f"tree_{proto_sp}", "v": int(hfloat(key, "tv", k) * 3) % 3, "e": round(float(p[0]), 2),
                         "n": round(float(p[1]), 2), "z": round(zg(p), 2), "h": round(float(h), 1),
                         "yaw": round(hfloat(key, "ty", k) * 6.2832, 3), "lean": 0.0, "src": f"plot:{key}"})

    for plot in plots:
        key = plot["key"]
        lay = layout(plot, cut, near)
        src_id = f"plot:{plot['id']}"
        for name, m, n, q0, q1 in lay["bays"]:
            z = min(zg(q0), zg(q1))
            pl.add(name, m, _yaw(n), z=z, src=src_id)
            typ = name.split("_")[2]
            rep["fence_m"][typ] = rep["fence_m"].get(typ, 0.0) + float(np.hypot(*(q1 - q0)))
        rep["bays"] += len(lay["bays"])
        for kind in ("gate", "wicket"):
            if lay[kind] is not None:
                name, m, n = lay[kind]
                pl.add(name, m, _yaw(n), z=zg(m), src=src_id)
                rep[kind + "s"] += 1
        for name, m, n in lay["wickets"]:
            pl.add(name, m, _yaw(n), z=zg(m), src=src_id)
            rep["wickets"] += 1
        drive_polys = []
        for which, m, d, L in lay["drive"]:
            t = np.array([-d[1], d[0]])
            if L is None:                                    # outside: to the road footprint, at most 12 m
                hit = LineString([m + d * 0.2, m + d * 12.0]).intersection(roads_poly)
                if hit.is_empty:
                    continue
                L = float(Point(*m).distance(hit)) + 0.15
            if L < 0.6:
                continue
            surf = plot["surface"]
            nb = int(L / DRIVE_TILE_M + 1e-6)
            spans = [(k * DRIVE_TILE_M, (k + 1) * DRIVE_TILE_M) for k in range(nb)]
            if L - nb * DRIVE_TILE_M > 0.1:                  # the last tile ends on the run's end (laps the one before;
                spans.append((L - DRIVE_TILE_M, L))          # outside the gate a short run laps under the gate)
            for s0, s1 in spans:
                cm = m + d * 0.5 * (s0 + s1)
                hl = 0.5 * (s1 - s0)
                pts = [cm, cm + d * hl + t * 1.4, cm + d * hl - t * 1.4, cm - d * hl + t * 1.4, cm - d * hl - t * 1.4]
                if which == "in" and any(plot["foot"].distance(Point(*q)) < 0.25 for q in pts):
                    continue                                 # never under the house wall
                z = max(zg(q) for q in pts) - 0.01
                pl.add(f"plot_drive_{surf}", cm, _yaw(d), z=z, src=src_id)
                rep["drive_tiles"] += 1
            drive_polys.append(LineString([m, m + d * L]).buffer(DRIVE_W_M / 2 + 0.3, cap_style="flat"))
        keepout += drive_polys
        near.add(lay["segs"])
        lawns.append(plot["poly"])
        # ---- garden
        poly = plot["poly"]
        free = poly.buffer(-1.0).difference(plot["foot"].buffer(1.2))
        for dp in drive_polys:
            free = free.difference(dp.buffer(0.5))
        if free.is_empty:
            continue
        edges = [e for e in _edges(poly) if float(e[4] @ plot["front"]) < 0.7] or _edges(poly)
        if hfloat(key, "thuja") < THUJA_SHARE and edges:
            a, b, L, t, n = hpick(sorted(edges, key=lambda e: -e[2])[:2], key, "thuja_e")
            cnt = 5 + int(hfloat(key, "thuja_n") * 6)
            s0 = 1.2 + hfloat(key, "thuja_s") * max(L - 2.4 - cnt * 0.9, 0.0)
            for k in range(cnt):
                p = a + t * (s0 + k * 0.9) - n * 0.8
                if s0 + k * 0.9 > L - 1.0 or not free.buffer(0.6).contains(Point(*p)):
                    continue
                pl.add("plot_thuja", p, hfloat(key, "thy", k) * 6.2832, z=zg(p) - 0.05,
                       sz=0.75 + 0.4 * hfloat(key, "thz", k) * (0.6 + 0.4 * hfloat(key, "thzz")), src=src_id)
                rep["thujas"] += 1
        x0, y0, x1, y1 = free.bounds
        placed = []

        def spot(tag, k, region, clear):
            for i in range(12):
                p = np.array([x0 + (x1 - x0) * hfloat(key, tag, k, i, "x"), y0 + (y1 - y0) * hfloat(key, tag, k, i, "y")])
                if region.contains(Point(*p)) and all(np.hypot(*(p - q)) > clear for q in placed):
                    placed.append(p)
                    return p
            return None
        near_fence = free.difference(poly.buffer(-2.6))
        near_house = free.intersection(plot["foot"].buffer(2.6))
        for k in range(2 + int(hfloat(key, "nshrub") * 3)):
            reg = near_house if hfloat(key, "shrub_where", k) < 0.45 and not near_house.is_empty else near_fence
            p = spot("shrub", k, reg, 1.6) if not reg.is_empty else None
            if p is not None:
                veg("shrub", p, 1.0 + 1.2 * hfloat(key, "shrub_h", k), key, k)
                rep["shrubs"] += 1
        back = poly.buffer(-2.5).difference(plot["foot"].buffer(3.5))
        for dp in drive_polys:
            back = back.difference(dp.buffer(1.5))
        if hfloat(key, "tree") < TREE_SHARE and not back.is_empty and poly.area > 300.0:
            for k in range(1 + int(hfloat(key, "ntree") * 2)):
                p = spot("tree", k, back, 4.5)
                if p is not None:
                    lo, hi = FRUIT_TREE[1]
                    veg(FRUIT_TREE[0], p, lo + (hi - lo) * hfloat(key, "tree_h", k), key, 100 + k)
                    rep["trees"] += 1
    rep["fence_m"] = {k: round(v) for k, v in sorted(rep["fence_m"].items())}
    rep["instances"] = len(pl.items) - n0
    rep["plot_m2_median"] = round(float(np.median([p["poly"].area for p in plots])), 1) if plots else 0.0
    rep["styles_front"] = {}
    for p in plots:
        k = "_".join(p["front_style"])
        rep["styles_front"][k] = rep["styles_front"].get(k, 0) + 1
    report["plots"] = rep
    return {"keepout": keepout, "lawns": lawns, "plots": plots}


def lawn_mask(col, lawns, hf, rasterize):
    """Mown lawn inside the plots: the 'unmown' channel (B) of the terrain ground masks drops to turf level."""
    if not lawns:
        return col
    from scipy import ndimage
    m = ndimage.gaussian_filter(rasterize(lawns, hf).astype(np.float32), 1.0)
    col[..., 2] = col[..., 2] * (1.0 - m) + np.minimum(col[..., 2], 0.12) * m
    return col
