"""House plots (ADR 0107 -> ADR 0114 "wąsko i dobrze"): outline, fence by typology, gate + wicket, one continuous
driveway with a dropped kerb, a mown lawn and a small garden around every single-family house.

Data. The tile has no cadastral parcels (EGiB is not in the pipeline) and BDOT10k carries no plot fences; OSM has
barrier=fence / wall ways mostly around industrial plots. So:
  * a real OSM / BDOT barrier that runs past a house IS the plot edge there: the generated outline shrinks to it and
    no second fence is built along it (PARALLEL_SKIP_M);
  * everything else is a RULE (WORKING_VALUE, not survey): a rectangle in the frame of the house - front towards the
    nearest road, set back from the road footprint by a lawn strip, 3-6 m beside the house, 7-15 m behind it - shrunk
    until it clears roads, other buildings, paved yards and the plots laid out before it. Houses within GROUP_GAP_M
    share one plot (a house and its garage, the two halves of a semi).
Everything is derived from the building id (sha1), so a rebuild gives the same plots; no state is kept.

Typology (docs/refs/posesje-bialystok.md: 33 Mapillary frames P01-P33 + 7 Commons C01-C07; heights WORKING_VALUE from
that document). The fence follows the age class of the house (a rule from footprint / storeys / height, not data):
  old  (small, single storey; wooden houses)   pickets rust-red (C04, P06), full boards rust / brown (P08, P09),
                                               green chain-link in a frame (P10, C03)
  prl  (the two-storey 'kostka')               brick posts with pickets / boards (C01), black bars on a plinth (P12),
                                               chain-link, boards, precast concrete plates
  new  (large, after ~2000)                    brick posts with wrought bars (P24), plastered wall in graphite (P13,
                                               P14), horizontal lamellae (P15), precast concrete
Sides and back are mostly chain-link or the cheap variant of the front.

Budget (ADR 0114). ADR 0107 drew every bay / gate / driveway tile / thuja as a point instance: one draw per 64 m cell
x prototype x submesh, which cost up to +45 instanced draws on the worst Low camera, and everything vanished at 60 m
(default instance cull x lodBias 0.5). Now the whole plot is CHUNK GEOMETRY:
  * fences, gates, posts, bins, thujas, spruces, fruit trees, shrubs, flowers -> `furniture` layer, ONE material
    `plot_kit` (streetscape.plot_kit: one alpha-clip atlas) = one draw per chunk, shown with the chunk's LOD0 / LOD1
    (to ~300 m from the chunk edge on every tier - nothing pops near the cab);
  * lawn, driveway, path to the door -> `paved` layer (draped on the conformed ground like every yard): `plot_lawn`
    + the existing `yard_paving` / `yard_gravel`.
No point instances at all. The price: garden plants are static (no wind) and have no LOD of their own.

Driveway access: where the gate faces a kerbed road the kerb and the footway behind it are lowered over the width of
the driveway (`apply_drops`, called by roads.pipeline before the ribbons are meshed), so the driveway meets the
carriageway without a step - visually and in the collision mesh.

Does not touch streetscape.furniture (street fences / furniture: parallel work).
"""
from __future__ import annotations

import math

import numpy as np
import shapely
from shapely.geometry import LineString, Point, Polygon

from . import plot_kit as PK
from .facade_kit import hfloat, hpick

GROUP_GAP_M = 2.5             # houses closer than this share a plot
FRONT_M = (2.0, 9.0)          # fence line in front of the house: road edge - ROAD_CLEAR_M, clamped to this, m
FRONT_FREE_M = (4.0, 8.0)     # ... when no road lies within ROAD_SEARCH_M in front
BACK_M = (7.0, 15.0)          # behind the house, m
SIDE_M = (3.0, 6.0)           # beside the house, m
DRIVE_SIDE_MIN_M = 4.25       # the side the driveway passes the house on
ROAD_SEARCH_M = 45.0
ROAD_CLEAR_M = 1.5            # lawn strip between the road footprint (footway / verge) and the fence, m (refs P13,
                              # P14, P19, P20: 1-2 m)
MIN_MARGIN_M = 1.5            # a side is never pulled closer to the house than this
MIN_AREA_RATIO = 1.8          # plot area / footprint area below which no plot is built
PARALLEL_SKIP_M = 2.5         # a run this close to (and within ~25 deg of) an existing fence is not built
BIG_BUILDING_M2 = 80.0        # non-house buildings above this are obstacles; smaller ones are outbuildings of the plot
GATE_W_M = 3.5                # double-leaf gate opening (ref P24: ~3-3.5 m, UNVERIFIED)
SLIDE_W_M = 4.0               # sliding gate opening
WICKET_W_M = 1.0
SLIDE_SHARE = 0.18            # sliding gates are the rarer kind (no frame of one in the reference set)
TERRACE_MIN = 3               # houses in one group from which the row is a terrace (wicket per house, no gate / drive)
DRIVE_W_M = 3.0
# One driveway material for every plot (budget, ADR 0114): gravel driveways (ref P20) and the concrete edging strip
# each added a submesh to the chunk's paved mesh (+5 / +3 chunks); block paving is the common case.
DRIVE_MAT = "yard_paving"
# Chunk layer of the plot ground (lawn, driveway, path): like `paved`, but shown only with the chunk's LOD0 / LOD1 (as
# `furniture` is) - in r1 the lawns sat in `paved` (drawn to LOD2, ~700 m) and cost draws in every distant view.
GROUND_LAYER = "plot_ground"
PATH_W_M = 1.1
DROP_H_M = 0.03               # lowered kerb at a driveway, m above the gutter (WORKING_VALUE: 2-4 cm in practice)
DROP_RAMP_M = 1.0             # kerb ramps down over this length on either side of the driveway
DROP_REACH_M = 14.0           # a gate further than this from the carriageway gets no access
DITCH_FILL_M = 0.06           # roadside ditch depth left over a driveway (culvert), m
SEG_M = PK.BAY_M              # fence panels follow the ground in steps of the post pitch drawn into the atlas

# fence style -> (atlas row of the infill, height range m, plinth (kind, height m) | None, post swatch, brick posts)
STYLES = {
    "picket": ("picket", (1.2, 1.4), None, "wood_brown", False),
    "boards_rust": ("boards_rust", (1.6, 1.9), None, "wood_rust", False),
    "boards_brown": ("boards_brown", (1.6, 2.0), None, "wood_brown", False),
    "chainlink": ("chainlink", (1.2, 1.5), None, "steel_green", False),
    "concrete": ("concrete", (1.5, 1.8), None, "concrete", False),
    "bars": ("bars", (1.3, 1.5), ("brick", 0.32), "steel_black", False),
    "lamella": ("lamella", (1.6, 1.8), ("concrete", 0.22), "steel_graphite", False),
    "wall": ("wall", (1.6, 2.1), None, None, False),
    "brick_picket": ("picket", (1.5, 1.7), ("brick", 0.35), None, True),
    "brick_boards": ("boards_rust", (1.5, 1.8), ("brick", 0.35), None, True),
    "brick_bars": ("bars", (1.5, 1.8), ("brick", 0.35), None, True),
}
# age class -> [(front style, weight)], [(side / back style or 'front', weight)]
FRONT_BY_AGE = {
    "old": [("picket", 0.34), ("boards_rust", 0.14), ("boards_brown", 0.16), ("chainlink", 0.26), ("brick_picket", 0.10)],
    "prl": [("brick_picket", 0.18), ("brick_boards", 0.10), ("bars", 0.18), ("chainlink", 0.16), ("boards_brown", 0.12),
            ("picket", 0.10), ("concrete", 0.16)],
    "new": [("brick_bars", 0.22), ("wall", 0.22), ("lamella", 0.22), ("brick_boards", 0.08), ("bars", 0.12),
            ("concrete", 0.14)],
}
SIDE_BY_AGE = {
    "old": [("chainlink", 0.55), ("boards_brown", 0.20), ("front", 0.25)],
    "prl": [("chainlink", 0.50), ("concrete", 0.25), ("front", 0.25)],
    "new": [("wall", 0.28), ("concrete", 0.26), ("chainlink", 0.26), ("lamella", 0.20)],
}
SIDE_OF_BRICK = {"brick_picket": "picket", "brick_boards": "boards_rust", "brick_bars": "bars"}
GATE_FRAME = {"picket": "wood_brown", "boards_rust": "wood_rust", "boards_brown": "wood_brown",
              "chainlink": "steel_green", "bars": "steel_black", "lamella": "steel_graphite"}
GATE_ROW = {"wall": "lamella", "concrete": "bars"}          # a wall / concrete fence has a steel gate
SURFACE_BY_AGE = {"old": 0.25, "prl": 0.6, "new": 0.9}      # share of block-paved driveways (the rest: gravel, P20)
THUJA_ROW_SHARE = {"old": 0.2, "prl": 0.45, "new": 0.65}
SPRUCE_SHARE = {"old": 0.4, "prl": 0.35, "new": 0.2}
FRUIT_SHARE = {"old": 0.85, "prl": 0.6, "new": 0.25}


def _pick_w(items, *key):
    x = hfloat(*key) * sum(w for *_, w in items)
    for it in items:
        x -= it[-1]
        if x <= 0:
            return it[0] if len(it) == 2 else it[:-1]
    return items[-1][0] if len(items[-1]) == 2 else items[-1][:-1]


def age_class(props, area, key):
    """'old' / 'prl' / 'new' from the footprint, storeys and height (a RULE - BDOT10k has no year of construction),
    with a fifth of the houses drifting one class (a renovated old house, an old fence kept at a new one)."""
    st = props.get("storeys") or 1
    h = props.get("height_m") or 6.0
    if area < 95.0 and st <= 1:
        base = "old"
    elif area >= 150.0 or (st >= 2 and h >= 8.5 and area >= 120.0):
        base = "new"
    else:
        base = "prl"
    x = hfloat(key, "age")
    if x < 0.12:
        return {"old": "prl", "prl": "old", "new": "prl"}[base]
    if x > 0.90:
        return {"old": "prl", "prl": "new", "new": "new"}[base]
    return base


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
        par = np.abs(ab @ t) / np.sqrt(L2) > 0.90
        return bool(np.any((d < r) & par))


def plan(houses, roads_poly, obstacles, barriers=(), seed=""):
    """Plot per house group. houses: [{id, poly, props?}] (single-family houses), roads_poly: road footprint,
    obstacles: polygons a plot must not cover (big buildings, paved yards), barriers: existing fence lines.
    Returns [dict(id, poly, front (unit xy), frame (c, eu, ev), houses, age, front_style, side_style, ...)], laid out
    in id order (deterministic)."""
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
        props = g[0].get("props") or {}
        age = age_class(props, g[0]["poly"].area, key)
        fs = _pick_w(FRONT_BY_AGE[age], key, "ft")
        ss = _pick_w(SIDE_BY_AGE[age], key, "side")
        if ss == "front":
            ss = SIDE_OF_BRICK.get(fs, fs)
        lo, hi = STYLES[fs][1]
        fh = round(lo + (hi - lo) * hfloat(key, "fh"), 2)
        lo, hi = STYLES[ss][1]
        sh = round(lo + (hi - lo) * hfloat(key, "sh"), 2)
        plots.append({"id": g[0]["id"], "poly": poly, "front": front, "frame": (c, eu, ev), "bbox": bb,
                      "houses": [h["id"] for h in g], "foot": foot, "house_polys": [h["poly"] for h in g],
                      "house_pts": [np.asarray(h["poly"].centroid.coords[0]) for h in g], "road_d": road_d,
                      "drive_side": drive_side, "age": age, "front_style": fs, "side_style": ss,
                      "front_h": fh, "side_h": sh,
                      "gate_kind": "slide" if (age != "old" and hfloat(key, "slide") < SLIDE_SHARE * 1.5) else "swing",
                      "surface": "paving" if hfloat(key, "surf") < SURFACE_BY_AGE[age] else "gravel", "key": key})
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


def _post_half(style):
    return 0.19 if STYLES[style][4] else 0.05


def layout(plot, cut=None, near=None, garages=()):
    """Fence runs, gate and wicket(s) of one plot.
    cut: polygon the fence does not cross (roads, buildings); near: _Near of existing fences (runs next to and
    parallel with one are not built); garages: outbuilding polygons of the plot (the gate lines up with one).
    Returns dict(runs=[dict(style, h, a, b, n, front)], gate=dict(m, n, t, w, kind)|None, wicket=dict|None,
    wickets=[dict], segs=[(a, b)])."""
    key = plot["key"]
    c, eu, ev = plot["frame"]
    front = plot["front"]
    bb = plot["bbox"]
    edges = _edges(plot["poly"])
    fr = [e for e in edges if float(e[4] @ front) > 0.7]
    out = {"runs": [], "gate": None, "wicket": None, "wickets": [], "segs": [], "garage": None}
    gate_iv = {}
    ge = None
    ph = _post_half(plot["front_style"])
    gw = SLIDE_W_M if plot.get("gate_kind") == "slide" else GATE_W_M
    gslot, wslot = gw + 4 * ph, WICKET_W_M + 4 * ph
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
        # a garage standing beside the house: the gate lines up with it (review 0107 P2-r7-b)
        for gp in sorted(garages, key=lambda q: -q.area):
            gc = np.asarray(gp.centroid.coords[0])
            s0 = float((gc - a) @ t)
            if gw / 2 + 0.5 <= s0 <= L - gw / 2 - 0.5:
                ray = LineString([a + t * s0, gc])
                if not ray.intersects(plot["foot"].difference(gp.buffer(0.3))):
                    sg = s0
                    out["garage"] = gp
                    hs = float((np.asarray(plot["foot"].centroid.coords[0]) - a) @ t)
                    w_side = 1.0 if hs > s0 else -1.0
                    break
        if len(plot["houses"]) >= TERRACE_MIN:               # terrace: a wicket in front of every house, no shared gate
            for k, hp in enumerate(plot["house_pts"]):
                w0 = float((hp - a) @ t) - wslot / 2
                if 0.3 <= w0 and w0 + wslot <= L - 0.3 and all(abs(w0 - x[0]) >= wslot + 1.0 for x in gate_iv.values()):
                    gate_iv[f"wicket{k}"] = (w0, w0 + wslot)
        elif plot["road_d"] is None:                         # no road in reach (review 0107 P2-r7-a): a wicket only
            if L >= wslot + 0.6:
                w0 = min(max(sg - wslot / 2, 0.3), L - wslot - 0.3)
                gate_iv["wicket"] = (w0, w0 + wslot)
        elif L >= gslot + wslot + 0.6:
            grp = gslot + wslot - 2 * ph                     # gate + wicket share the post between them
            g0 = sg - (gslot / 2 if w_side > 0 else gslot / 2 + wslot - 2 * ph)
            g0 = min(max(g0, 0.3), L - grp - 0.3)
            if w_side > 0:
                gate_iv["gate"], gate_iv["wicket"] = (g0, g0 + gslot), (g0 + gslot - 2 * ph, g0 + grp)
            else:
                gate_iv["wicket"], gate_iv["gate"] = (g0, g0 + wslot), (g0 + wslot - 2 * ph, g0 + grp)
        elif L >= gslot + 0.6:
            g0 = min(max(sg - gslot / 2, 0.3), L - gslot - 0.3)
            gate_iv["gate"] = (g0, g0 + gslot)
        elif L >= wslot + 0.6:
            w0 = min(max(sg - wslot / 2, 0.3), L - wslot - 0.3)
            gate_iv["wicket"] = (w0, w0 + wslot)
        for kind, (s0, s1) in list(gate_iv.items()):
            m = a + t * 0.5 * (s0 + s1)
            seg = LineString([a + t * s0, a + t * s1])
            if (cut is not None and seg.intersects(cut)) or (near is not None and near.parallel(m, t)):
                del gate_iv[kind]
                continue
            d = {"m": m, "n": n, "t": t, "w": gw if kind == "gate" else WICKET_W_M, "ph": ph,
                 "kind": plot.get("gate_kind", "swing") if kind == "gate" else "wicket"}
            if kind in ("gate", "wicket"):
                out[kind] = d
            else:
                out["wickets"].append(d)
        if out["gate"] is None:
            out["garage"] = None
    for e in edges:
        a, b, L, t, n = e
        is_front = float(n @ front) > 0.7
        style = plot["front_style"] if is_front else plot["side_style"]
        h = plot["front_h"] if is_front else plot["side_h"]
        ivs = [(0.0, L)]
        if ge is not None and e is ge:
            for s0, s1 in sorted(gate_iv.values()):
                ivs = [x for i0, i1 in ivs for x in ((i0, min(i1, s0)), (max(i0, s1), i1)) if x[1] - x[0] > 0.3]
        for i0, i1 in ivs:
            line = LineString([a + t * i0, a + t * i1])
            pieces = [line] if cut is None else [q for q in getattr(line.difference(cut), "geoms", [line.difference(cut)])
                                                 if q.geom_type == "LineString" and q.length > 0.6]
            for q in pieces:
                p0, p1 = (np.asarray(x) for x in q.coords[:2])
                Lq = float(np.hypot(*(p1 - p0)))
                # keep the stretches that no existing fence already closes (sampled every 2.5 m)
                ns = max(1, int(math.ceil(Lq / 2.5)))
                keep = [near is None or not near.parallel(p0 + t * (Lq * (k + 0.5) / ns), t) for k in range(ns)]
                k = 0
                while k < ns:
                    if not keep[k]:
                        k += 1
                        continue
                    k1 = k
                    while k1 < ns and keep[k1]:
                        k1 += 1
                    q0, q1 = p0 + t * (Lq * k / ns), p0 + t * (Lq * k1 / ns)
                    if np.hypot(*(q1 - q0)) > 0.6:
                        out["runs"].append({"style": style, "h": h, "a": q0, "b": q1, "n": n, "front": is_front})
                        out["segs"].append((q0, q1))
                    k = k1
    return out


# ------------------------------------------------------------------------------------------------- road access
def plan_access(plots, net, carriage):
    """Where the driveway of each plot meets the carriageway: plot['access'] = dict(q, d_cw, chain, side, s, walk)
    and the list of kerb drops for apply_drops. net: roads network (chains with side profiles), carriage: polygon of
    the carriageway surfaces."""
    from roads import network as NW
    drops = []
    shapely.prepare(carriage)
    for plot in plots:
        plot["access"] = None
        g = plot["lay"]["gate"]
        if g is None:
            continue
        m, n = g["m"], g["n"]
        hit = LineString([m + n * 0.2, m + n * DROP_REACH_M]).intersection(carriage)
        if hit.is_empty:
            continue
        d_cw = float(Point(*m).distance(hit))
        q = m + n * d_cw
        best = None
        for c in net.chains:
            if c.meta.get("absorbed") or c.line is None:
                continue
            if Point(*q).distance(LineString(c.line.p)) > 25.0:
                continue
            s, lat = c.line.project(q + n * 0.3)
            if not (c.t_a + 1.5 < s < c.length - c.t_b - 1.5):
                continue
            i = int(c.idx(s))
            if c.bridge is not None and bool(c.bridge[i]):
                continue
            d_edge = abs(abs(lat) - 0.3 - float(c.hw_at(s)))
            if best is None or d_edge < best[0]:
                best = (d_edge, c, s, "L" if lat > 0 else "R", i)
        acc = {"q": q, "d_cw": d_cw, "chain": None, "walk": None, "kind": None}
        if best is not None and best[0] < 1.2:
            _, c, s, side, i = best
            d = c.side[side]
            kind, mat = int(d["kind"][i]), int(d["mat"][i])
            acc.update(chain=c.id, side=side, s=float(s), kind=kind, walk=NW.WALK_MATS[mat])
            if kind in (NW.URBAN, NW.RURAL) and mat != NW.MAT_FLUSH_ROAD:
                drops.append({"chain": c.id, "side": side, "s": float(s), "half": g["w"] / 2 + 0.4, "plot": plot["id"]})
        plot["access"] = acc
    return drops


def apply_drops(net, drops):
    """Lower the kerb (and with it the footway / verge behind: the profile hangs on the kerb height) over each driveway;
    fill the roadside ditch of a rural profile. Edits chain.side[..]['h'] in place, before the ribbons are meshed
    (roads.pipeline.build(side_edit=...)). Returns the number of drops applied."""
    from roads import network as NW
    from roads import standards as S
    chains = {c.id: c for c in net.chains}
    done = 0
    for dr in drops:
        c = chains.get(dr["chain"])
        if c is None:
            continue
        d = c.side[dr["side"]]
        s = np.asarray(c.line.s)
        k = np.clip((np.abs(s - dr["s"]) - dr["half"]) / DROP_RAMP_M, 0.0, 1.0)      # 0 on the driveway, 1 outside
        sel = k < 1.0
        if not sel.any():
            continue
        kind = np.asarray(d["kind"])
        h = np.asarray(d["h"], float)
        urban = sel & (kind == NW.URBAN) & (np.asarray(d["mat"]) != NW.MAT_FLUSH_ROAD) & (h > DROP_H_M)
        h[urban] = np.minimum(h[urban], DROP_H_M + (h[urban] - DROP_H_M) * k[urban])
        rural = sel & (kind == NW.RURAL)
        he = np.where((h > 0.05) & (h < 1.5), h, S.DITCH_DEPTH)
        h[rural] = np.minimum(he[rural], DITCH_FILL_M + (he[rural] - DITCH_FILL_M) * k[rural])
        d["h"] = h
        done += int(bool(urban.any() or rural.any()))
    return done


def region_plan(blds, roads_poly, carriage, yards, src, origin, bpoly, net=None, seed=""):
    """Plan every plot of the region once (pass 1 of build_world; the streetscape stage reuses it). blds:
    buildings_mesh.load() list, yards: polygons of paved yards, src: streetscape sources (OSM / BDOT barriers).
    Returns dict(plots=[... with 'lay' and 'access'], drops=[...])."""
    houses = [{"id": b["id"], "poly": b["poly"], "props": b.get("props") or {}} for b in blds if b["typ"] == "house"]
    obstacles = [b["poly"] for b in blds if b["typ"] != "house" and b["poly"].area >= BIG_BUILDING_M2]
    obstacles += [p for p in yards if p.area > 20.0]
    small = [b["poly"] for b in blds if b["typ"] != "house" and b["poly"].area < BIG_BUILDING_M2]
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
    for plot in plots:
        gar = [q for q in small if plot["poly"].contains(q.centroid)]
        plot["garages"] = gar
        plot["lay"] = layout(plot, cut, near, gar)
        near.add(plot["lay"]["segs"])
        plot["access"] = None
    drops = plan_access(plots, net, carriage) if net is not None else []
    return {"plots": plots, "drops": drops, "roads_poly": roads_poly}


# ------------------------------------------------------------------------------------------------- ground
def _drive_axis(plot):
    """Centre line of the driveway inside the plot (gate -> beside the house / the garage door)."""
    lay = plot["lay"]
    g = lay["gate"]
    m, n = g["m"], g["n"]
    if lay.get("garage") is not None:
        gp = lay["garage"]
        end = np.asarray(shapely.ops.nearest_points(gp, Point(*m))[0].coords[0])
        return LineString([m + n * 0.3, end])
    c, eu, ev = plot["frame"]
    bb = plot["bbox"]
    front = plot["front"]
    depth_in = float(max((bb[1] - bb[0]) if abs(float(front @ eu)) > 0.5 else (bb[3] - bb[2]), 4.0))
    d_front = float(Point(*m).distance(plot["foot"]))
    L_in = min(d_front + min(depth_in, 7.0) + 0.5, 22.0)
    return LineString([m + n * 0.3, m - n * L_in])


def paved_items(rp, roads_poly, bpoly, paved):
    """Ground of the plots as paved-area items (streetscape.paved: draped on the smoothed ground, flush with the road
    edge, terrain conformed under them): driveway + path to the door (`yard_paving` / `yard_gravel`) and the mown
    lawn (`plot_lawn`). Fills plot['drive'] / plot['path'] / plot['lawn'] (polygons, may be None)."""
    import shapely.ops                                       # noqa: F401  (nearest_points in _drive_axis)
    taken = shapely.unary_union([roads_poly.buffer(0.02), bpoly] + [p["poly"] for p in paved])
    out = []
    plots = rp["plots"]
    others = {i: shapely.unary_union([q["poly"] for j, q in enumerate(plots) if j != i and q["poly"].distance(p["poly"]) < 30.0] or [Polygon()])
              for i, p in enumerate(plots)}
    for i, plot in enumerate(plots):
        lay = plot["lay"]
        hard = []
        plot["drive"] = plot["path"] = plot["lawn"] = None
        inner = plot["poly"].buffer(-0.25)
        if lay["gate"] is not None:
            g = lay["gate"]
            ax = _drive_axis(plot)
            drive = ax.buffer(DRIVE_W_M / 2, cap_style="flat", join_style="mitre").intersection(inner.union(
                LineString([g["m"] - g["n"] * 0.5, g["m"] + g["n"] * 0.5]).buffer(g["w"] / 2, cap_style="flat")))
            if plot.get("access") is not None:
                d_out = plot["access"]["d_cw"] + 0.5
            else:                                            # no carriageway in reach: out to the road footprint (a yard, a path)
                hit = LineString([g["m"], g["m"] + g["n"] * 8.0]).intersection(roads_poly)
                d_out = float(Point(*g["m"]).distance(hit)) + 0.3 if not hit.is_empty else 0.6
            apron = LineString([g["m"] - g["n"] * 0.3, g["m"] + g["n"] * d_out]).buffer(g["w"] / 2, cap_style="flat")
            plot["drive"] = shapely.unary_union([drive, apron]).buffer(0.01).difference(others[i])
            hard.append(plot["drive"])
        for wk in ([lay["wicket"]] if lay["wicket"] is not None else []) + lay["wickets"]:
            m, n = wk["m"], wk["n"]
            hit = LineString([m, m - n * 30.0]).intersection(plot["foot"])
            d_in = float(Point(*m).distance(hit)) if not hit.is_empty else 0.0
            hit = LineString([m, m + n * 6.0]).intersection(roads_poly)
            d_out = float(Point(*m).distance(hit)) + 0.3 if not hit.is_empty else 0.0
            if d_in < 0.5 and d_out < 0.5:
                continue
            path = LineString([m - n * max(d_in, 0.3), m + n * max(d_out, 0.3)]).buffer(PATH_W_M / 2, cap_style="flat").difference(others[i])
            plot["path"] = path if plot["path"] is None else plot["path"].union(path)
            hard.append(path)
        plot["hard"] = shapely.unary_union(hard) if hard else Polygon()
    for plot in plots:
        hard_u = plot["hard"]
        for k, q in enumerate(_polys(hard_u.difference(taken), 1.0)):
            out.append({"id": f"plot:{plot['id']}:drive{k}", "poly": q, "mat": DRIVE_MAT, "source": "plot", "parking": False,
                        "edging": False, "layer": GROUND_LAYER})
        lawn = plot["poly"].difference(taken).difference(hard_u.buffer(0.02))
        lawns = _polys(lawn, 6.0)
        plot["lawn"] = shapely.unary_union(lawns) if lawns else None
        for k, q in enumerate(lawns):
            out.append({"id": f"plot:{plot['id']}:lawn{k}", "poly": q, "mat": "plot_lawn", "source": "plot", "parking": False, "layer": GROUND_LAYER})
    return out


def _polys(g, min_area):
    g = g.buffer(-0.04).buffer(0.04)
    return [p.simplify(0.05) for p in getattr(g, "geoms", [g]) if p.geom_type == "Polygon" and p.area > min_area]


# ------------------------------------------------------------------------------------------------- geometry
class Kit:
    """Triangles of one plot in the `plot_kit` material. Quads / boxes get their own vertices (flat shading), ring
    shells share vertices (smooth)."""

    def __init__(self):
        self.V, self.UV, self.T = [], [], []
        self.n = 0

    def tris(self, V, UV, T):
        self.V.append(np.asarray(V, float).reshape(-1, 3))
        self.UV.append(np.asarray(UV, float).reshape(-1, 2))
        self.T.append(np.asarray(T, np.int64).reshape(-1, 3) + self.n)
        self.n += len(self.V[-1])

    def quad(self, P, UV):
        self.tris(P, UV, [(0, 1, 2), (0, 2, 3)])

    def box(self, c, t, hx, hy, z0, z1, uv, top=True, sides=(0, 1, 2, 3)):
        """Box centred on xy c, x axis along unit t, half sizes hx / hy, z0..z1; all vertices pinned to the texel uv
        (a swatch) unless uv is a callable (k, corner) -> uv for side k."""
        n = np.array([t[1], -t[0]])
        cs = [c - t * hx - n * hy, c + t * hx - n * hy, c + t * hx + n * hy, c - t * hx + n * hy]
        for k in sides:
            a, b = cs[(k + 1) % 4], cs[k]
            P = [[*a, z0], [*b, z0], [*b, z1], [*a, z1]]
            self.quad(P, [uv(k, j) for j in range(4)] if callable(uv) else [uv] * 4)
        if top:
            P = [[*cs[0], z1], [*cs[1], z1], [*cs[2], z1], [*cs[3], z1]]
            self.quad(P, [uv(4, j) for j in range(4)] if callable(uv) else [uv] * 4)

    def out(self):
        if not self.V:
            return None
        return np.concatenate(self.V), np.concatenate(self.UV), np.concatenate(self.T)


def _brick_uv(u0, w, h):
    v0, v1 = PK.row("brick")
    dv = (v1 - v0) * min(h / PK.ROW_H_M["brick"], 1.0)

    def uv(k, j):
        if k == 4:
            return PK.SWATCH["concrete"]
        uu = u0 + k * 0.41 / PK.KIT_M
        return [(uu, v0), (uu + w / PK.KIT_M, v0), (uu + w / PK.KIT_M, v0 + dv), (uu, v0 + dv)][j]
    return uv


def brick_post(kit, p, t, z, h, key):
    """Brick post 0.38 m square with a concrete cap."""
    u0 = int(hfloat(key, "bu") * 20) * (PK.KIT_M / 39) / PK.KIT_M * 2
    kit.box(p, t, 0.19, 0.19, z - 0.12, z + h, _brick_uv(u0, 0.38, h + 0.12), top=False)
    kit.box(p, t, 0.23, 0.23, z + h, z + h + 0.07, PK.SWATCH["concrete"])


def fence_run(kit, style, a, b, n, h, zf, key, col=None, ends=(True, True)):
    """One straight fence run a -> b (outward normal n), height h above the ground zf(xy), in panels of SEG_M that
    follow the ground. col: list collecting collision quads."""
    rowname, _, plinth, post, brick = STYLES[style]
    L = float(np.hypot(*(b - a)))
    t = (b - a) / L
    v0, v1 = PK.row(rowname)
    if brick:
        nb = max(1, int(round(L / 2.8)))
        cuts = [L * k / nb for k in range(nb + 1)]
    else:
        nb = max(1, int(math.ceil(L / SEG_M - 1e-6)))
        cuts = [min(k * SEG_M, L) for k in range(nb + 1)]
    Z = [zf(a + t * s) for s in cuts]
    uoff = int(hfloat(key, "uo", round(float(a[0]), 1), round(float(a[1]), 1)) * 4) * PK.BAY_M
    ph = plinth[1] if plinth else 0.0
    for k in range(nb):
        s0, s1 = cuts[k], cuts[k + 1]
        z0, z1 = Z[k], Z[k + 1]
        i0, i1 = (s0 + 0.19, s1 - 0.19) if brick else (s0, s1)          # infill between the brick posts
        if i1 - i0 > 0.05:
            if brick:
                u0, u1 = (uoff + 0.05) / PK.KIT_M, (uoff + 0.05 + (i1 - i0)) / PK.KIT_M
            else:
                u0, u1 = (uoff + s0) / PK.KIT_M, (uoff + s1) / PK.KIT_M
            za, zb = z0 + (z1 - z0) * (i0 - s0) / (s1 - s0), z0 + (z1 - z0) * (i1 - s0) / (s1 - s0)
            lo = ph if plinth else -0.08
            for sg in (1.0, -1.0):
                o = n * (0.012 * sg)
                A, B = a + t * i0 + o, a + t * i1 + o
                P = [[*A, za + lo], [*B, zb + lo], [*B, zb + h], [*A, za + h]]
                UV = [[u0, v0], [u1, v0], [u1, v1], [u0, v1]]
                if sg < 0:
                    P, UV = [P[1], P[0], P[3], P[2]], [UV[1], UV[0], UV[3], UV[2]]
                kit.quad(P, UV)
            if plinth:
                hw = 0.11 if plinth[0] == "brick" else 0.06
                bv0, bv1 = PK.row("brick")
                for sg in (1.0, -1.0):
                    o = n * (hw * sg)
                    A, B = a + t * i0 + o, a + t * i1 + o
                    P = [[*A, za - 0.15], [*B, zb - 0.15], [*B, zb + ph], [*A, za + ph]]
                    if plinth[0] == "brick":
                        dv = (bv1 - bv0) * (ph + 0.15) / PK.ROW_H_M["brick"]
                        UV = [[i0 / PK.KIT_M, bv0], [i1 / PK.KIT_M, bv0], [i1 / PK.KIT_M, bv0 + dv], [i0 / PK.KIT_M, bv0 + dv]]
                    else:
                        UV = [PK.SWATCH["concrete"]] * 4
                    if sg < 0:
                        P, UV = [P[1], P[0], P[3], P[2]], [UV[1], UV[0], UV[3], UV[2]]
                    kit.quad(P, UV)
                A, B = a + t * i0, a + t * i1
                kit.quad([[*(A + n * hw), za + ph], [*(B + n * hw), zb + ph], [*(B - n * hw), zb + ph], [*(A - n * hw), za + ph]],
                         [PK.SWATCH["concrete"]] * 4)
        if brick and (k > 0 or ends[0]):
            brick_post(kit, a + t * s0, t, z0, h + 0.12, (key, k))
        elif post and k == 0 and ends[0]:
            kit.box(a + t * s0, t, 0.045, 0.045, z0 - 0.1, z0 + h + 0.04, PK.SWATCH[post])
    if brick and ends[1]:
        brick_post(kit, b, t, Z[-1], h + 0.12, (key, "e"))
    elif post and ends[1]:
        kit.box(b, t, 0.045, 0.045, Z[-1] - 0.1, Z[-1] + h + 0.04, PK.SWATCH[post])
    if col is not None:
        col.append((a, b, min(Z) - 0.1, max(Z) + h))


def gate_geo(kit, g, style, h, z, key, col=None):
    """Gate / wicket in the fence line: posts, leaf frame of box section, infill from the atlas row of the fence.
    kind 'swing' (two leaves), 'slide' (one leaf on the inside, running past the opening), 'wicket' (one leaf)."""
    rowname, _, _, _, brick = STYLES[style]
    rowname = GATE_ROW.get(rowname, rowname)
    frame = PK.SWATCH[GATE_FRAME.get(rowname, "steel_graphite")]
    m, n, t, W, kind = g["m"], g["n"], g["t"], g["w"], g["kind"]
    hg = min(h, 1.8) if rowname != "picket" else min(h, 1.35)
    ph = g["ph"]
    for sx in (-1, 1):
        p = m + t * (sx * (W / 2 + ph))
        if brick:
            brick_post(kit, p, t, z, max(h, hg) + 0.14, (key, "gp", sx))
        else:
            kit.box(p, t, 0.05, 0.05, z - 0.1, z + hg + 0.10, frame)
    v0, v1 = PK.row(rowname)
    leaves = [(-W / 2 + 0.02, W / 2 - 0.02, 0.0)] if kind == "wicket" else \
        [(-W / 2 + 0.02, -0.012, 0.0), (0.012, W / 2 - 0.02, 0.0)] if kind == "swing" else \
        [(-W / 2 - 1.3, W / 2 + 0.05, -0.12)]
    for x0, x1, off in leaves:
        o = n * off
        zb, zt = z + 0.08, z + hg
        for (cx, hx, c0, c1) in ((0.5 * (x0 + x1), (x1 - x0) / 2, zb, zb + 0.045), (0.5 * (x0 + x1), (x1 - x0) / 2, zt - 0.045, zt),
                                 (x0 + 0.022, 0.022, zb, zt), (x1 - 0.022, 0.022, zb, zt)):
            kit.box(m + t * cx + o, t, hx, 0.022, c0, c1, frame)
        u0 = 0.06 / PK.KIT_M + int(hfloat(key, "gu", x0) * 3) * 0.25
        u1 = u0 + (x1 - x0 - 0.09) / PK.KIT_M
        for sg in (1.0, -1.0):
            oo = o + n * (0.008 * sg)
            A, B = m + t * (x0 + 0.045) + oo, m + t * (x1 - 0.045) + oo
            P = [[*A, zb + 0.045], [*B, zb + 0.045], [*B, zt - 0.03], [*A, zt - 0.03]]
            UV = [[u0, v0 + 0.06 * (v1 - v0)], [u1, v0 + 0.06 * (v1 - v0)], [u1, v1 - 0.04 * (v1 - v0)], [u0, v1 - 0.04 * (v1 - v0)]]
            if sg < 0:
                P, UV = [P[1], P[0], P[3], P[2]], [UV[1], UV[0], UV[3], UV[2]]
            kit.quad(P, UV)
        if kind == "slide":                                  # ground beam of the cantilever gate
            kit.box(m + t * 0.5 * (x0 + x1) + o, t, (x1 - x0) / 2, 0.04, z + 0.02, z + 0.09, frame)
    if kind == "wicket":                                     # letter box on the post, street side
        box = PK.SWATCH[hpick(["galv", "steel_black", "steel_green", "wood_brown"], key, "mail")]
        p = m + t * (W / 2 + ph) + n * (ph + 0.05)
        kit.box(p, t, 0.13, 0.05, z + 0.95, z + 1.29, box)
    if col is not None:
        col.append((m - t * (W / 2), m + t * (W / 2), z - 0.1, z + hg))


def thuja(kit, p, z, h, r, key, dead=False):
    """Columnar thuja ('Smaragd' / 'Brabant'): one 5-sided shell of the foliage row, every ring jittered."""
    zs = [0.0]
    while zs[-1] < h - 1e-6:
        zs.append(min(zs[-1] + PK.ROW_H_M["thuja"], h))
    if len(zs) > 2 and zs[-1] - zs[-2] < 0.35:
        zs.pop(-2)
    v0, v1 = PK.row("thuja")
    sides = 5
    circ = 2 * math.pi * r
    span = min(circ / PK.KIT_M, 0.11) if dead else circ / PK.KIT_M
    u0 = (PK.THUJA_GREEN_U + 0.015 + hfloat(key, "tu") * (1 - PK.THUJA_GREEN_U - 0.03 - span)) if dead else \
        hfloat(key, "tu") * (PK.THUJA_GREEN_U - span - 0.01)
    a0 = hfloat(key, "ta") * 6.2832
    lean = (np.array([hfloat(key, "tlx"), hfloat(key, "tly")]) - 0.5) * 0.10
    V, UV = [], []
    for i, zz in enumerate(zs):
        f = zz / h
        k = 0.66 + 0.34 * min(f / 0.14, 1.0) if f < 0.14 else 1.0 - 0.20 * ((f - 0.14) / 0.5) if f < 0.64 else \
            0.80 * (1.0 - ((f - 0.64) / 0.36) ** 1.6) + 0.07
        for j in range(sides + 1):
            jj = j % sides
            rr = r * k * (0.86 + 0.28 * hfloat(key, "tr", i, jj))
            ang = a0 + 2 * math.pi * j / sides
            V.append([p[0] + lean[0] * zz + math.cos(ang) * rr, p[1] + lean[1] * zz + math.sin(ang) * rr, z - 0.05 + zz])
            UV.append([u0 + span * j / sides, v0 if i % 2 == 0 else v1])
    T = []
    m = sides + 1
    for i in range(len(zs) - 1):
        for j in range(sides):
            a_, b_, c_, d_ = i * m + j, i * m + j + 1, (i + 1) * m + j + 1, (i + 1) * m + j
            T += [(a_, b_, c_), (a_, c_, d_)]
    kit.tris(V, UV, T)


def spruce(kit, p, z, h, key):
    """Blue spruce (świerk kłujący, refs P02 / P17 / P18): tiers of drooping branch skirts from the spruce row."""
    nt = int(min(max(round(h / 0.75), 4), 9))
    rb = 0.20 * h + 0.45
    v0, v1 = PK.row("spruce")
    sides = 6
    a0 = hfloat(key, "sa") * 6.2832
    for i in range(nt):
        f = i / nt
        zlo = h * (0.07 + 0.86 * f)
        zhi = min(zlo + 1.7 * h * 0.86 / nt, h)
        rlo = rb * (1 - f) ** 0.85 + 0.06
        rhi = 0.22 * rlo
        span = 2 * math.pi * rlo / PK.KIT_M
        u0 = hfloat(key, "su", i) * (1.0 - span)
        V, UV = [], []
        for ring, (zz, rr, vv) in enumerate(((zlo, rlo, v0), (zhi, rhi, v1))):
            for j in range(sides + 1):
                jj = j % sides
                ang = a0 + i * 0.5 + 2 * math.pi * j / sides
                r2 = rr * (0.85 + 0.3 * hfloat(key, "sr", i, jj)) if ring == 0 else rr
                droop = -0.10 * rlo * hfloat(key, "sd", i, jj) if ring == 0 else 0.0
                V.append([p[0] + math.cos(ang) * r2, p[1] + math.sin(ang) * r2, z + zz + droop])
                UV.append([u0 + span * j / sides, vv])
        m = sides + 1
        T = []
        for j in range(sides):
            T += [(j, j + 1, m + j + 1), (j, m + j + 1, m + j)]
        kit.tris(V, UV, T)
    kit.box(np.asarray(p, float), np.array([1.0, 0.0]), 0.07, 0.07, z - 0.1, z + h * 0.12, PK.SWATCH["trunk"], top=False)


def card(kit, p, z, sprite, W, H, ang, z_off=0.0):
    """Upright sprite card W x H centred on p, facing angle ang."""
    u0, u1 = PK.SPRITE[sprite]
    v0, v1 = PK.row("sprites")
    d = np.array([math.cos(ang), math.sin(ang)]) * (W / 2)
    A, B = np.asarray(p) - d, np.asarray(p) + d
    kit.quad([[*A, z + z_off], [*B, z + z_off], [*B, z + z_off + H], [*A, z + z_off + H]],
             [[u0, v0], [u1, v0], [u1, v1], [u0, v1]])


def fruit_tree(kit, p, z, h, key):
    """Small orchard tree (apple): a trunk and three crossed crown cards."""
    sp = "apple_a" if hfloat(key, "fa") < 0.5 else "apple_b"
    wm, hm = PK.SPRITE_M[sp]
    k = h / 3.4
    a0 = hfloat(key, "fy") * 3.1416
    tr = 0.05 + 0.02 * k
    kit.box(np.asarray(p, float), np.array([math.cos(a0), math.sin(a0)]), tr, tr, z - 0.1, z + 0.36 * h, PK.SWATCH["trunk"], top=False)
    for i in range(3):
        card(kit, p, z, sp, wm * k, hm * k, a0 + i * math.pi / 3, z_off=h - hm * k)


def shrub(kit, p, z, h, key):
    sp = "shrub_a" if hfloat(key, "sh") < 0.6 else "shrub_b"
    wm, hm = PK.SPRITE_M[sp]
    k = h / hm
    a0 = hfloat(key, "sy") * 3.1416
    for i in range(2):
        card(kit, p, z - 0.04, sp, wm * k, h, a0 + i * math.pi / 2)


def flower_bed(kit, a, b, zf, key):
    """Perennials along a -> b: a zig-zag of flower cards over a strip of bare soil."""
    L = float(np.hypot(*(b - a)))
    if L < 1.2:
        return 0
    t = (b - a) / L
    n = np.array([t[1], -t[0]])
    za, zb = zf(a) + 0.025, zf(b) + 0.025
    kit.quad([[*(a - n * 0.32), za], [*(b - n * 0.32), zb], [*(b + n * 0.32), zb], [*(a + n * 0.32), za]],
             [PK.SWATCH["soil"]] * 4)
    cnt = int(L / 0.62)
    base = math.atan2(t[1], t[0])
    for k in range(cnt):
        s = (k + 0.5) * L / cnt
        p = a + t * s + n * (0.12 * (hfloat(key, "fl", k) - 0.5))
        sp = hpick(["flowers_a", "flowers_b", "flowers_c", "flowers_a"], key, "fs", k // 3)
        hh = 0.38 + 0.3 * hfloat(key, "fh", k)
        card(kit, p, zf(p), sp, 0.95, hh, base + (0.5 if k % 2 else -0.5))
    return cnt


def bins(kit, p, t, z, key):
    """Two or three wheelie bins in a row along t."""
    cnt = 2 + int(hfloat(key, "bn") * 2)
    for k in range(cnt):
        q = p + t * (k * 0.62)
        hh = 0.94 if k < 2 else 1.06
        kit.box(q, t, 0.24, 0.27, z, z + hh, PK.SWATCH["bin_dark"], top=False)
        kit.box(q, t, 0.26, 0.29, z + hh, z + hh + 0.05, PK.SWATCH[["bin_dark", "lid_yellow", "lid_brown"][k]])
    return cnt


# ------------------------------------------------------------------------------------------------- build
def build(buf, rp, zf, surf_top, report):
    """Mesh every plot of the region plan into buf (layer `furniture`, material `plot_kit`; collision quads of the
    fences and closed gates; a paved strip over a grass verge / shoulder where the driveway crosses one).
    zf(xy) -> ground height (lawn / driveway surface), surf_top: furniture.SurfaceTop of the road meshes."""
    plots = rp["plots"]
    rep = {"plots": len(plots), "fence_m": {}, "gates": 0, "sliding_gates": 0, "wickets": 0, "drives": 0, "kerb_drops": len(rp["drops"]),
           "verge_overlays": 0, "thujas": 0, "spruces": 0, "fruit_trees": 0, "shrubs": 0, "flower_cards": 0, "bins": 0,
           "tris": 0, "instances": 0, "plot_m2_median": 0.0, "age": {}, "styles_front": {}, "styles_side": {}}
    keepout = []
    for plot in plots:
        key, lay = plot["key"], plot["lay"]
        kit, col = Kit(), []
        src_id = f"plot:{plot['id']}"
        rep["age"][plot["age"]] = rep["age"].get(plot["age"], 0) + 1
        rep["styles_front"][plot["front_style"]] = rep["styles_front"].get(plot["front_style"], 0) + 1
        rep["styles_side"][plot["side_style"]] = rep["styles_side"].get(plot["side_style"], 0) + 1
        for r in lay["runs"]:
            fence_run(kit, r["style"], r["a"], r["b"], r["n"], r["h"], zf, key, col)
            rep["fence_m"][r["style"]] = rep["fence_m"].get(r["style"], 0.0) + float(np.hypot(*(r["b"] - r["a"])))
        gates = ([lay["gate"]] if lay["gate"] is not None else []) + ([lay["wicket"]] if lay["wicket"] is not None else []) + lay["wickets"]
        for g in gates:
            gate_geo(kit, g, plot["front_style"], plot["front_h"], max(zf(g["m"] - g["t"] * g["w"] / 2), zf(g["m"] + g["t"] * g["w"] / 2)),
                     (key, g["kind"], round(float(g["m"][0]), 1)), col)
            if g["kind"] == "wicket":
                rep["wickets"] += 1
            else:
                rep["gates"] += 1
                rep["sliding_gates"] += g["kind"] == "slide"
        hard = [q for q in (plot.get("drive"), plot.get("path")) if q is not None]
        hard_u = shapely.unary_union(hard).buffer(0.35) if hard else Polygon()
        keepout += hard
        if plot.get("drive") is not None:
            rep["drives"] += 1
            rep["verge_overlays"] += _verge_overlay(buf, plot, surf_top, src_id)
        # ---- garden
        poly = plot["poly"]
        foot = plot["foot"]
        free = poly.buffer(-0.9).difference(foot.buffer(1.0)).difference(hard_u)
        age = plot["age"]
        placed = []

        def spot(tag, k, region, clear):
            if region.is_empty:
                return None
            x0, y0, x1, y1 = region.bounds
            for i in range(14):
                p = np.array([x0 + (x1 - x0) * hfloat(key, tag, k, i, "x"), y0 + (y1 - y0) * hfloat(key, tag, k, i, "y")])
                if region.contains(Point(*p)) and all(np.hypot(*(p - q)) > clear for q in placed):
                    placed.append(p)
                    return p
            return None
        if not free.is_empty:
            edges = _edges(poly)
            sideback = [e for e in edges if float(e[4] @ plot["front"]) < 0.7 and e[2] > 5.0]
            rows = []
            if hfloat(key, "thuja") < THUJA_ROW_SHARE[age] and sideback:
                rows.append(hpick(sorted(sideback, key=lambda e: -e[2])[:3], key, "thuja_e"))
                if hfloat(key, "thuja2") < 0.35 and len(sideback) > 1:
                    rows.append(hpick([e for e in sideback if e is not rows[0]], key, "thuja_e2"))
            if age == "new" and hfloat(key, "thuja_f") < 0.35:
                rows += [e for e in edges if float(e[4] @ plot["front"]) > 0.7][:1]
            for ri, (a, b, L, t, n) in enumerate(rows):
                hb = 1.3 + 2.4 * hfloat(key, "thh", ri) ** 1.3          # the row's planting age: 1.3 - 3.7 m
                pitch = 0.72 + 0.34 * hfloat(key, "thp", ri)
                s0 = 0.9 + hfloat(key, "ths", ri) * 0.35 * L
                s1 = L - 0.9 - hfloat(key, "the", ri) * 0.25 * L
                s, k = s0, 0
                while s < s1:
                    k += 1
                    step = pitch * (0.8 + 0.4 * hfloat(key, "thd", ri, k))      # +-20 % spacing (review 0107 P1-r7-e)
                    p = a + t * s - n * (0.65 + 0.2 * hfloat(key, "tho", ri, k))
                    s += step
                    if hfloat(key, "thg", ri, k) < 0.07:                # a gap: one died and was dug out
                        continue
                    if not poly.buffer(-0.35).contains(Point(*p)) or foot.distance(Point(*p)) < 0.7 or hard_u.contains(Point(*p)):
                        continue
                    dead = hfloat(key, "thx", ri, k) < 0.04
                    hh = hb * (0.7 + 0.6 * hfloat(key, "thz", ri, k)) * (0.75 if dead else 1.0)     # +-30 % height
                    rr = (0.26 + 0.07 * hh) * (0.85 + 0.3 * hfloat(key, "thw", ri, k))
                    thuja(kit, p, zf(p), hh, rr, (key, ri, k), dead)
                    placed.append(p)
                    rep["thujas"] += 1
            # perennials along the front wall of the house and, sometimes, behind the street fence
            hedge = max(_edges(plot["house_polys"][0]), key=lambda e: float(e[4] @ plot["front"]) * 10 + e[2] * 0.01)
            a, b, L, t, n = hedge
            if float(n @ plot["front"]) > 0.6 and hfloat(key, "bed") < 0.7:
                q0, q1 = a + t * (0.15 * L) + n * 0.55, a + t * (0.85 * L) + n * 0.55
                bed = LineString([q0, q1]).difference(hard_u.buffer(0.3))
                for seg in getattr(bed, "geoms", [bed]):
                    if seg.geom_type == "LineString" and seg.length > 1.2 and poly.contains(seg):
                        c0, c1 = (np.asarray(x) for x in seg.coords[:2])
                        rep["flower_cards"] += flower_bed(kit, c0, c1, zf, (key, "bedh"))
            fr_runs = [r for r in lay["runs"] if r["front"] and np.hypot(*(r["b"] - r["a"])) > 3.0]
            if fr_runs and hfloat(key, "bed2") < (0.5 if age != "new" else 0.25):
                r = hpick(fr_runs, key, "bed2r")
                t = (r["b"] - r["a"]) / np.hypot(*(r["b"] - r["a"]))
                c0, c1 = r["a"] + t * 0.5 - r["n"] * 0.55, r["b"] - t * 0.5 - r["n"] * 0.55
                if not LineString([c0, c1]).intersects(hard_u) and poly.contains(LineString([c0, c1])):
                    rep["flower_cards"] += flower_bed(kit, c0, c1, zf, (key, "bedf"))
            front_g = free.intersection(Polygon([*(np.asarray(poly.centroid.coords[0]) + plot["front"] * 200 + s * np.array([-plot["front"][1], plot["front"][0]]) * 200 for s in (-1, 1)),
                                                 *(np.asarray(foot.centroid.coords[0]) + s * np.array([-plot["front"][1], plot["front"][0]]) * 200 for s in (1, -1))]))
            back_g = free.difference(front_g).buffer(-1.2)
            if hfloat(key, "spruce") < SPRUCE_SHARE[age]:
                for k in range(1 + int(hfloat(key, "nspruce") < 0.25)):
                    reg = front_g.buffer(-1.6) if hfloat(key, "spr_w", k) < 0.6 else back_g.buffer(-0.6)
                    p = spot("spruce", k, reg, 4.0)
                    if p is not None:
                        hh = (2.5 + 2.5 * hfloat(key, "sprh", k)) if age == "new" else (4.0 + 5.0 * hfloat(key, "sprh", k))
                        spruce(kit, p, zf(p), hh, (key, "spr", k))
                        rep["spruces"] += 1
            if hfloat(key, "tree") < FRUIT_SHARE[age] and poly.area > 250.0:
                for k in range(1 + int(hfloat(key, "ntree") * (3 if age == "old" else 2))):
                    p = spot("tree", k, back_g.buffer(-0.8), 4.2)
                    if p is not None:
                        fruit_tree(kit, p, zf(p), 3.0 + 1.4 * hfloat(key, "tree_h", k), (key, "ft", k))
                        rep["fruit_trees"] += 1
            near_fence = free.difference(poly.buffer(-2.4))
            near_house = free.intersection(foot.buffer(2.4))
            for k in range(2 + int(hfloat(key, "nshrub") * 4)):
                reg = near_house if hfloat(key, "shrub_where", k) < 0.45 and not near_house.is_empty else near_fence
                p = spot("shrub", k, reg, 1.5)
                if p is not None:
                    shrub(kit, p, zf(p), 0.8 + 0.9 * hfloat(key, "shrub_h", k), (key, "shr", k))
                    rep["shrubs"] += 1
        # bins inside the fence next to the gate (collection day is a walk of two metres)
        g = lay["gate"] or lay["wicket"]
        if g is not None and hfloat(key, "bins") < 0.8:
            sx = 1.0 if hfloat(key, "bins_s") < 0.5 else -1.0
            p = g["m"] + g["t"] * (sx * (g["w"] / 2 + 2 * g["ph"] + 0.45)) - g["n"] * 0.55
            ok = poly.buffer(-0.3).contains(Point(*p)) and poly.buffer(-0.3).contains(Point(*(p + g["t"] * sx * 1.4)))
            if ok and not hard_u.buffer(-0.3).contains(Point(*p)):
                rep["bins"] += bins(kit, p, g["t"] * sx, zf(p), key)
        o = kit.out()
        if o is not None:
            buf.add("furniture", "plot_kit", o[0], o[1], o[2], src=src_id)
            rep["tris"] += len(o[2])
        for a, b, z0, z1 in col:
            V = np.array([[*a, z0], [*b, z0], [*b, z1], [*a, z1]])
            buf.add("collision", "collision_fence", V, V[:, :2], [(0, 1, 2), (0, 2, 3), (0, 2, 1), (0, 3, 2)], src=src_id)
    rep["list"] = [{"id": p["id"], "age": p["age"], "front": p["front_style"], "side": p["side_style"],
                    "c": [round(float(v), 1) for v in p["poly"].centroid.coords[0]],
                    "gate": None if p["lay"]["gate"] is None else {
                        "m": [round(float(v), 2) for v in p["lay"]["gate"]["m"]],
                        "n": [round(float(v), 3) for v in p["lay"]["gate"]["n"]], "kind": p["lay"]["gate"]["kind"]},
                    "access": None if p.get("access") is None else {"d_cw": round(p["access"]["d_cw"], 2),
                                                                    "walk": p["access"]["walk"], "chain": p["access"]["chain"]}}
                   for p in plots]
    rep["fence_m"] = {k: round(v) for k, v in sorted(rep["fence_m"].items())}
    rep["plot_m2_median"] = round(float(np.median([p["poly"].area for p in plots])), 1) if plots else 0.0
    report["plots"] = rep
    return {"keepout": keepout, "lawns": [p["lawn"] for p in plots if p.get("lawn") is not None], "plots": plots}


def _verge_overlay(buf, plot, surf_top, src_id):
    """Where the driveway crosses a grass verge / gravel shoulder of the road (no footway there), pave that stretch:
    a strip draped 2 cm over the road-side surface, from the carriageway edge to the road footprint edge."""
    acc = plot.get("access")
    if acc is None or surf_top is None or acc.get("walk") == "sidewalk_paving" and acc.get("kind") == 0:
        return 0
    g = plot["lay"]["gate"]
    m, n, t = g["m"], g["n"], g["t"]
    L = acc["d_cw"]
    ns = max(2, int(math.ceil(L / 0.5)))
    lat = np.linspace(-g["w"] / 2, g["w"] / 2, 5)
    V, UV, ok = [], [], []
    for i in range(ns + 1):
        d = L * i / ns + 0.05
        for x in lat:
            p = m + n * d + t * x
            z = surf_top.top(float(p[0]), float(p[1]))
            ok.append(np.isfinite(z))
            V.append([p[0], p[1], (z if np.isfinite(z) else 0.0) + 0.02])
            UV.append([p[0], p[1]])
    T = []
    nl = len(lat)
    for i in range(ns):
        for j in range(nl - 1):
            a_, b_, c_, d_ = i * nl + j, i * nl + j + 1, (i + 1) * nl + j + 1, (i + 1) * nl + j
            if ok[a_] and ok[b_] and ok[c_] and ok[d_]:
                T += [(a_, d_, c_), (a_, c_, b_)]
    if not T:
        return 0
    V = np.asarray(V)
    T = np.asarray(T)
    nrm = np.cross(V[T[:, 1]] - V[T[:, 0]], V[T[:, 2]] - V[T[:, 0]])
    T[nrm[:, 2] < 0] = T[nrm[:, 2] < 0][:, [0, 2, 1]]
    buf.add(GROUND_LAYER, DRIVE_MAT, V, np.asarray(UV), T, src=src_id + ":verge",
            UV1=np.tile([25.0, 25.0], (len(V), 1)))
    return 1


def lawn_mask(col, lawns, hf, rasterize):
    """Terrain ground masks around the plots: the lawn itself is a draped `plot_lawn` surface; here the 1 m grit strip
    the terrain shader draws along every paved edge (R = distance / 20 m) is taken off the lawn edges (a lawn is no
    yard: grass meets grass under the fence) and the terrain next to a lawn counts as mown."""
    if not lawns:
        return col
    from scipy import ndimage
    inside = rasterize(lawns, hf)
    ring = ndimage.binary_dilation(inside, iterations=4) & ~inside
    hard = (col[..., 0] <= 0.0) & ~inside                    # roads, yards, driveways
    near_hard = ndimage.binary_dilation(hard, iterations=2)
    fix = ring & ~near_hard
    col[..., 0] = np.where(fix, np.maximum(col[..., 0], 0.3), col[..., 0])
    # beyond the chunk's LOD1 the lawn surface is not drawn: the terrain under it must read as grass, not as grit
    col[..., 0] = np.where(ndimage.binary_erosion(inside, iterations=1), np.maximum(col[..., 0], 0.3), col[..., 0])
    m = ndimage.gaussian_filter((inside | ring).astype(np.float32), 1.0)
    col[..., 2] = col[..., 2] * (1.0 - m) + np.minimum(col[..., 2], 0.12) * m
    return col
