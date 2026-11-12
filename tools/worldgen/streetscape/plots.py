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
import shapely.ops
from shapely.geometry import LineString, Point, Polygon

from . import plot_kit as PK
from .facade_kit import hfloat, hpick

GROUP_GAP_M = 2.5             # houses closer than this share a plot
FRONT_M = (2.6, 30.0)         # fence line in front of the house: road edge - ROAD_CLEAR_M, clamped to this, m
                              # (ADR 0124: was 2-9 m; 13 gates stood 15-25 m short of their street - the plot of a
                              # house set deep in its garden still reaches the street - and 2 m left no room for the
                              # door steps)
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
# Chunk layer of the kit geometry (fences, gates, plants). ADR 0124: its own node `plots` instead of a submesh of
# `furniture` (same draw count: one submesh either way) - the engine can then shorten the range of the plots in the
# mirror cameras (Game.World.PlotViewCull) without touching barriers, lamps and street fences.
KIT_LAYER = "plots"
PATH_W_M = 1.1
DROP_H_M = 0.03               # lowered kerb at a driveway, m above the gutter (WORKING_VALUE: 2-4 cm in practice)
DROP_RAMP_M = 1.0             # kerb ramps down over this length on either side of the driveway
DROP_REACH_M = 14.0           # a gate further than this from the carriageway gets no access
DITCH_FILL_M = 0.06           # roadside ditch depth left over a driveway (culvert), m
SEG_M = 2 * PK.BAY_M          # fence panels follow the ground in steps of two post pitches of the atlas (5.12 m)
STEP_ZONE_M = (1.6, 2.1)      # door steps of a house: width, depth from the wall (facade_kit.door_steps: landing 1.0 m
                              # + up to 3 goings of 0.3 m), m - no fence, no plant and no bin stands in it
GARAGE_ZONE_M = 5.5           # clear, paved depth in front of a garage door, m
HOUSE_KERB_M = 0.10           # kerb height on the streets of single-family houses (refs P08, P13, P24: 8-12 cm,
                              # WORKING_VALUE from proportion; main roads keep roads.standards.KERB_HEIGHT 0.13)
HOUSE_KERB_HW_M = 4.0         # ... only carriageways up to this half width (no collector / arterial)
KERB_BAND_M = 0.17            # kerb stone top (standards.KERB_TOP_W 0.15) + joint: the driveway paving starts behind it
WIRE_H_M = 7.4                # low-voltage bundle (AsXSn) on the street-lamp poles of the house streets, m above ground
DROP_H_HOUSE_M = 4.2          # service drop: height of the anchor on the house wall, m (clamped below the eaves)

# fence style -> (atlas row of the infill, height range m, plinth (kind, height m) | None, post swatch, brick posts)
STYLES = {
    "picket": ("picket", (1.2, 1.4), None, "wood_brown", False),
    "boards_rust": ("boards_rust", (1.6, 1.9), None, "wood_rust", False),
    "boards_brown": ("boards_brown", (1.6, 2.0), None, "wood_brown", False),
    "boards_grey": ("boards_grey", (1.5, 1.8), None, "wood_grey", False),
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
    "old": [("picket", 0.30), ("boards_rust", 0.12), ("boards_brown", 0.12), ("boards_grey", 0.12), ("chainlink", 0.24),
            ("brick_picket", 0.10)],
    "prl": [("brick_picket", 0.18), ("brick_boards", 0.10), ("bars", 0.18), ("chainlink", 0.16), ("boards_brown", 0.12),
            ("picket", 0.10), ("concrete", 0.16)],
    "new": [("brick_bars", 0.22), ("wall", 0.22), ("lamella", 0.22), ("brick_boards", 0.08), ("bars", 0.12),
            ("concrete", 0.14)],
}
SIDE_BY_AGE = {
    "old": [("chainlink", 0.45), ("boards_grey", 0.20), ("boards_brown", 0.10), ("front", 0.25)],
    "prl": [("chainlink", 0.50), ("concrete", 0.25), ("front", 0.25)],
    "new": [("wall", 0.28), ("concrete", 0.26), ("chainlink", 0.26), ("lamella", 0.20)],
}
SIDE_OF_BRICK = {"brick_picket": "picket", "brick_boards": "boards_rust", "brick_bars": "bars"}
GATE_FRAME = {"picket": "wood_brown", "boards_rust": "wood_rust", "boards_brown": "wood_brown", "boards_grey": "wood_grey",
              "chainlink": "steel_green", "bars": "steel_black", "lamella": "steel_graphite"}
GATE_ROW = {"wall": "lamella", "concrete": "bars"}          # a wall / concrete fence has a steel gate
SURFACE_BY_AGE = {"old": 0.25, "prl": 0.6, "new": 0.9}      # share of block-paved driveways (the rest: gravel, P20)
THUJA_ROW_MAX = 12            # plants per row (triangle budget: every plant is 36-60 triangles of the chunk mesh)
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
                      "surface": "paving" if hfloat(key, "surf") < SURFACE_BY_AGE[age] else "gravel", "key": key,
                      "house_h": float(props.get("height_m") or 6.0)})
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


def layout(plot, cut=None, near=None, garages=(), gate_s=None, no_gate=False, garage_doors=()):
    """Fence runs, gate and wicket(s) of one plot.
    cut: polygon the fence does not cross (roads, buildings, door steps, garage doors); near: _Near of existing fences
    (runs next to and parallel with one are not built); garages: outbuilding polygons of the plot; garage_doors:
    [(door centre, outward normal, garage polygon)] - the gate lines up with a garage door that faces the street.
    gate_s: forced position of the gate centre along the front edge (m from its start; region_plan moves a gate that
    has no way to the carriageway); no_gate: wicket only.
    Returns dict(runs=[dict(style, h, a, b, n, front)], gate=dict(m, n, t, w, kind)|None, wicket=dict|None,
    wickets=[dict], segs=[(a, b)])."""
    key = plot["key"]
    c, eu, ev = plot["frame"]
    front = plot["front"]
    bb = plot["bbox"]
    edges = _edges(plot["poly"])
    fr = [e for e in edges if float(e[4] @ front) > 0.7]
    out = {"runs": [], "gate": None, "wicket": None, "wickets": [], "segs": [], "garage": None, "garage_pt": None,
           "gate_s": None, "gate_range": None}
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
        # ADR 0124 (review 0114 P2-r8-b): the DOOR of the garage is the target, when it looks at the street; else its
        # centroid as before
        targets = [(dc, gp) for dc, dn, gp in garage_doors if float(dn @ front) > 0.5]
        targets += [(np.asarray(gp.centroid.coords[0]), gp) for gp in sorted(garages, key=lambda q: -q.area)
                    if not any(gp is q for _, q in targets)]
        for gc, gp in targets:
            s0 = float((gc - a) @ t)
            if gw / 2 + 0.5 <= s0 <= L - gw / 2 - 0.5:
                ray = LineString([a + t * s0, gc])
                if not ray.intersects(plot["foot"].difference(gp.buffer(0.3))):
                    sg = s0
                    out["garage"] = gp
                    out["garage_pt"] = gc
                    hs = float((np.asarray(plot["foot"].centroid.coords[0]) - a) @ t)
                    w_side = 1.0 if hs > s0 else -1.0
                    break
        if gate_s is not None:
            sg = float(gate_s)
        out["gate_s"], out["gate_range"] = sg, (gslot / 2 + 0.3, L - gslot / 2 - 0.3)
        if no_gate:                                          # no way to a carriageway (ADR 0124): a wicket only,
            if L >= wslot + 0.6:                             # in front of the house door when it is known
                st = plot.get("steps") or []
                tgt = float((min(st, key=lambda q: float(np.hypot(*(q["p"] - a))))["p"] - a) @ t) if st else sg
                pad = min(3.0, (L - wslot) / 2)              # clear of the corner (a neighbour's fence ends there)
                w0 = min(max(tgt - wslot / 2, pad), L - wslot - pad)
                gate_iv["wicket"] = (w0, w0 + wslot)
        elif len(plot["houses"]) >= TERRACE_MIN:             # terrace: a wicket in front of every house, no shared gate
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
def door_zones(blds, roads_poly):
    """Where the buildings of a plot open (ADR 0124, review 0114 P1-r8-c / P2-r8-b), by the SAME rules as
    buildings_mesh (main facade = the edge nearest a road; house door in the middle bay; shed garage doors):
    steps {house id: dict(zone polygon of the door steps, p door centre on the wall, n outward normal, front)},
    doors [(garage door centre on the wall, outward normal, garage polygon, door zone polygon)]."""
    from . import buildings_mesh as BM
    steps, doors = {}, []
    for b in blds:
        if b["typ"] not in ("house", "shed"):
            continue
        poly = b["poly"]
        edges = BM.ring_edges(poly.exterior)
        if not edges:
            continue
        dist = [roads_poly.distance(Point(*(0.5 * (a + c)))) for a, c in edges]
        ei = int(np.argmin(dist))
        a, c = edges[ei]
        L = float(np.hypot(*(c - a)))
        if L < 0.05:
            continue
        d = (c - a) / L
        nout = np.array([d[1], -d[0]])
        if b["typ"] == "house":
            n = min(int((L - 1.0) // 2.7), 3)
            if n == 0 and L > 2.6:
                n = 1
            if n < 1:
                continue
            p0 = a + d * ((L - (n - 1) * 2.7) / 2 + (n // 2) * 2.7)
            w, dep = STEP_ZONE_M
            zone = Polygon([p0 - d * w / 2 - nout * 0.1, p0 + d * w / 2 - nout * 0.1, p0 + d * w / 2 + nout * dep, p0 - d * w / 2 + nout * dep])
            steps[b["id"]] = {"zone": zone, "p": p0, "n": nout, "front": p0 + nout * dep}
        elif L > 3.2 and hfloat(f"{b['id']}:{ei}", "gar") < 0.6:
            n = max(1, min(4, int(L // 3.2)))
            for i in range(n):
                p0 = a + d * ((i + 0.5) * L / n)
                zone = Polygon([p0 - d * 1.35 - nout * 0.1, p0 + d * 1.35 - nout * 0.1, p0 + d * 1.35 + nout * GARAGE_ZONE_M, p0 - d * 1.35 + nout * GARAGE_ZONE_M])
                doors.append((p0, nout, poly, zone))
    return steps, doors


def gate_access(m, n, w, net, carriage, block=None):
    """Way from a gate (centre m, outward normal n, opening w) to the carriageway. Returns (acc, drop):
    acc = None when no carriageway lies within DROP_REACH_M straight ahead or the way crosses `block` (buildings);
    else dict(q, d_cw, chain, side, s, kind, walk, ok). ok = the kerb there can be lowered (the gate faces a chain, not
    a junction patch or a chain end) or there is none (flush edge). drop: the kerb drop for apply_drops, or None."""
    from roads import network as NW
    hit = LineString([m + n * 0.2, m + n * DROP_REACH_M]).intersection(carriage)
    if hit.is_empty:
        return None, None
    d_cw = float(Point(*m).distance(hit))
    q = m + n * d_cw
    if block is not None and d_cw > 0.8 and LineString([m + n * 0.3, q]).buffer(w / 2 - 0.2, cap_style="flat").intersects(block):
        return None, None
    best = None
    for c in net.chains:
        if c.meta.get("absorbed") or c.line is None:
            continue
        if Point(*q).distance(LineString(c.line.p)) > 25.0:
            continue
        s, lat = c.line.project(q + n * 0.3)
        half = w / 2 + 0.4 + DROP_RAMP_M
        if not (c.t_a + half < s < c.length - c.t_b - half):          # the whole drop with its ramps lies on the chain
            continue
        i = int(c.idx(s))
        if c.bridge is not None and bool(c.bridge[i]):
            continue
        d_edge = abs(abs(lat) - 0.3 - float(c.hw_at(s)))
        if best is None or d_edge < best[0]:
            best = (d_edge, c, s, "L" if lat > 0 else "R", i)
    acc = {"q": q, "d_cw": d_cw, "chain": None, "walk": None, "kind": None, "ok": False, "kerbed": False}
    drop = None
    if best is not None and best[0] < 1.2:
        _, c, s, side, i = best
        d = c.side[side]
        kind, mat = int(d["kind"][i]), int(d["mat"][i])
        acc.update(chain=c.id, side=side, s=float(s), kind=kind, walk=NW.WALK_MATS[mat], ok=True,
                   kerbed=kind == NW.URBAN and mat != NW.MAT_FLUSH_ROAD)
        if kind in (NW.URBAN, NW.RURAL) and mat != NW.MAT_FLUSH_ROAD:
            drop = {"chain": c.id, "side": side, "s": float(s), "half": w / 2 + 0.4}
    return acc, drop


def plan_access(plots, net, carriage, relayout=None, block=None):
    """Where the driveway of each plot meets the carriageway: plot['access'] = dict(q, d_cw, chain, side, s, walk, ok)
    and the list of kerb drops for apply_drops. net: roads network (chains with side profiles), carriage: polygon of
    the carriageway surfaces.
    ADR 0124 (review 0114 P1-r8-a; ADR 0114 left 7 gates at full-height kerbs opposite junction patches and 13 with no
    way to the carriageway): a gate is kept only where its driveway reaches a carriageway edge whose kerb can be
    lowered. Otherwise relayout(plot, gate_s) moves it along the front edge in steps of 0.75 m (nearest first), and
    when no place works relayout(plot, None) rebuilds the front with a wicket only."""
    drops = []
    shapely.prepare(carriage)
    stats = {"moved": 0, "removed": 0, "removed_no_carriageway": 0, "removed_junction": 0}
    for plot in plots:
        plot["access"] = None
        g = plot["lay"]["gate"]
        if g is None:
            continue
        acc, drop = gate_access(g["m"], g["n"], g["w"], net, carriage, block)
        if (acc is None or not acc["ok"]) and relayout is not None:
            first = acc
            lay0 = plot["lay"]
            lo, hi = lay0["gate_range"]
            s0 = lay0["gate_s"]
            found = False
            if hi > lo:
                steps = sorted({round(min(max(s0 + sg * k * 0.75, lo), hi), 2) for k in range(1, 40) for sg in (-1, 1)},
                               key=lambda x: (abs(x - s0), x))
                for sx in steps:
                    lay = relayout(plot, sx)
                    g2 = lay["gate"]
                    if g2 is None:
                        continue
                    acc2, drop2 = gate_access(g2["m"], g2["n"], g2["w"], net, carriage, block)
                    if acc2 is not None and acc2["ok"]:
                        plot["lay"], acc, drop, found = lay, acc2, drop2, True
                        stats["moved"] += 1
                        break
            if not found:
                plot["lay"] = relayout(plot, None)
                stats["removed"] += 1
                stats["removed_no_carriageway" if first is None else "removed_junction"] += 1
                continue
        if acc is None or not acc["ok"]:
            continue
        if drop is not None:
            drop["plot"] = plot["id"]
            drops.append(drop)
        plot["access"] = acc
    return drops, stats


def apply_house_kerbs(net, plots):
    """ADR 0124 (review 0114 'krawędź ulicy': a tall road kerb stood along every house street; refs P08 / P13 / P24
    show 8-12 cm): the kerbs of the chains the house driveways open onto are HOUSE_KERB_M high. Only two-lane
    carriageways (half width <= HOUSE_KERB_HW_M) with at least two plots on them; the last 4 m before a junction
    patch keep the standard height (the patch kerbs are meshed at it). Edits chain.side[..]['h'] in place, before
    apply_drops. Returns {chain id: metres lowered}."""
    from roads import network as NW
    cnt = {}
    for p in plots:
        a = p.get("access")
        if a and a.get("chain"):
            cnt[a["chain"]] = cnt.get(a["chain"], 0) + 1
    out = {}
    for c in net.chains:
        if cnt.get(c.id, 0) < 2 or c.line is None or c.roundabout:
            continue
        if float(np.max(c.hw)) > HOUSE_KERB_HW_M:
            continue
        s = np.asarray(c.line.s)
        k = np.clip(np.minimum(s - c.t_a, c.length - c.t_b - s) / 4.0, 0.0, 1.0)      # 0 at the patches, 1 from 4 m on
        m_tot = 0.0
        for side in ("L", "R"):
            d = c.side[side]
            h = np.asarray(d["h"], float).copy()
            sel = (np.asarray(d["kind"]) == NW.URBAN) & (np.asarray(d["mat"]) != NW.MAT_FLUSH_ROAD) & (h > HOUSE_KERB_M) & (h < 0.2)
            if c.bridge is not None:
                sel &= ~np.asarray(c.bridge, bool)
            h[sel] = h[sel] + (HOUSE_KERB_M - h[sel]) * k[sel]
            d["h"] = h
            if len(s) > 1:
                m_tot += float(sel.sum()) * float(np.median(np.diff(s)))
        if m_tot > 0:
            out[c.id] = round(m_tot, 1)
    return out


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
    steps, gdoors = door_zones(blds, roads_poly)
    # ADR 0124 (review 0114 P1-r8-c "schody przed płotem", P2-r8-b "płot przecina bramę garażu"): no fence crosses
    # the door steps of a house or the clear depth in front of a garage door
    zones = [z["zone"] for z in steps.values()] + [d[3] for d in gdoors]
    cut = shapely.unary_union([roads_poly.buffer(0.3), bpoly.buffer(0.3)] + [z.buffer(0.15) for z in zones])
    shapely.prepare(cut)
    near0 = [sg for b in barriers for sg in _segments(b)]

    def lay_all(overrides):
        near = _Near()
        near.add(near0)
        for plot in plots:
            o = overrides.get(plot["id"], {})
            plot["lay"] = layout(plot, cut, near, plot["garages"], gate_s=o.get("gate_s"), no_gate=o.get("no_gate", False),
                                 garage_doors=plot["garage_doors"])
            near.add(plot["lay"]["segs"])
    for plot in plots:
        plot["garages"] = [q for q in small if plot["poly"].contains(q.centroid)]
        plot["garage_doors"] = [(dc, dn, gp) for dc, dn, gp, _ in gdoors if any(gp is q for q in plot["garages"])]
        plot["steps"] = [steps[h] for h in plot["houses"] if h in steps]
        plot["door_zones"] = [z["zone"] for z in plot["steps"]] + [d[3] for d in gdoors if any(d[2] is q for q in plot["garages"])]
        plot["garage_zones"] = [(d[0], d[1], d[3]) for d in gdoors if any(d[2] is q for q in plot["garages"])]
        plot["access"] = None
    lay_all({})
    drops, astats = [], {}
    if net is not None:
        ovr = {}

        def relayout(plot, gate_s):
            # one plot alone (the neighbours' fences as planned): good enough to test a gate position
            near = _Near()
            near.add(near0)
            if gate_s is None:
                ovr[plot["id"]] = {"no_gate": True}
                return layout(plot, cut, near, plot["garages"], no_gate=True, garage_doors=plot["garage_doors"])
            ovr[plot["id"]] = {"gate_s": gate_s}
            return layout(plot, cut, near, plot["garages"], gate_s=gate_s, garage_doors=plot["garage_doors"])
        shapely.prepare(bpoly)
        drops, astats = plan_access(plots, net, carriage, relayout, block=bpoly)
        lay_all(ovr)                                         # final fences with every moved / removed gate in place
        drops = []
        for p in plots:                                      # the access of the final layout (a neighbour's fence may
            p["access"] = None                               # have closed a gate the single-plot test accepted)
            g = p["lay"]["gate"]
            if g is None:
                continue
            acc, drop = gate_access(g["m"], g["n"], g["w"], net, carriage, bpoly)
            if acc is not None and acc["ok"]:
                p["access"] = acc
                if drop is not None:
                    drop["plot"] = p["id"]
                    drops.append(drop)
        bad = [p for p in plots if p["lay"]["gate"] is not None and p["access"] is None]
        if bad:                                              # rare: drop those gates too
            for p in bad:
                ovr[p["id"]] = {"no_gate": True}
            lay_all(ovr)
            astats["removed"] += len(bad)
            astats["removed_after_relayout"] = len(bad)
            for p in bad:
                p["access"] = None
            gone = {p["id"] for p in bad}
            drops = [d for d in drops if d["plot"] not in gone]
    return {"plots": plots, "drops": drops, "roads_poly": roads_poly, "carriage": carriage, "access_stats": astats}


# ------------------------------------------------------------------------------------------------- ground
def _drive_axis(plot):
    """Centre line of the driveway inside the plot (gate -> beside the house / the garage door)."""
    lay = plot["lay"]
    g = lay["gate"]
    m, n = g["m"], g["n"]
    if lay.get("garage") is not None:
        gp = lay["garage"]
        end = lay.get("garage_pt")
        if end is None:
            end = np.asarray(shapely.ops.nearest_points(gp, Point(*m))[0].coords[0])
        return LineString([m + n * 0.3, end])
    c, eu, ev = plot["frame"]
    bb = plot["bbox"]
    front = plot["front"]
    depth_in = float(max((bb[1] - bb[0]) if abs(float(front @ eu)) > 0.5 else (bb[3] - bb[2]), 4.0))
    d_front = float(Point(*m).distance(plot["foot"]))
    L_in = min(d_front + min(depth_in, 7.0) + 0.5, 40.0)
    return LineString([m + n * 0.3, m - n * L_in])


def paved_items(rp, roads_poly, bpoly, paved):
    """Ground of the plots as paved-area items (streetscape.paved: draped on the smoothed ground, flush with the road
    edge, terrain conformed under them): driveway + garage aprons + path to the door (`yard_paving`) and the mown
    lawn (`plot_lawn`). Fills plot['drive'] / plot['path'] / plot['lawn'] (polygons, may be None).
    ADR 0124: the hard surfaces of one plot are ONE union (driveway, apron, garage apron, path share their vertices -
    review 0114 P1-r8-b), the lawn is the plot minus that union; the path leads to the door steps, not to the wall."""
    import shapely.ops                                       # noqa: F401  (nearest_points in _drive_axis)
    taken = shapely.unary_union([roads_poly.buffer(0.02), bpoly] + [p["poly"] for p in paved])
    out = []
    plots = rp["plots"]
    others = {i: shapely.unary_union([q["poly"] for j, q in enumerate(plots) if j != i and q["poly"].distance(p["poly"]) < 30.0] or [Polygon()])
              for i, p in enumerate(plots)}
    for i, plot in enumerate(plots):
        lay = plot["lay"]
        hard, paths = [], []
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
        # paved depth in front of every garage door (review 0114 P2-r8-b: the garage opened onto the lawn)
        for dc, dn, zone in plot.get("garage_zones", ()):
            z = zone.intersection(plot["poly"].union(zone.intersection(roads_poly.buffer(1.5)))).difference(others[i])
            if not z.is_empty and z.area > 2.0:
                hard.append(z)
                if plot["drive"] is None:
                    plot["drive"] = z
        for wk in ([lay["wicket"]] if lay["wicket"] is not None else []) + lay["wickets"]:
            m, n = wk["m"], wk["n"]
            hit = LineString([m, m - n * 45.0]).intersection(plot["foot"])
            d_in = float(Point(*m).distance(hit)) if not hit.is_empty else 0.0
            hit = LineString([m, m + n * 6.0]).intersection(roads_poly)
            d_out = float(Point(*m).distance(hit)) + 0.3 if not hit.is_empty else 0.0
            if d_in < 0.5 and d_out < 0.5:
                continue
            line = LineString([m - n * max(d_in, 0.3), m + n * max(d_out, 0.3)])
            steps = plot.get("steps") or []
            if steps:                                        # to the foot of the nearest door steps, round a corner if needed
                st = min(steps, key=lambda q: float(np.hypot(*(q["front"] - m))))
                turn = m - n * min(max(float((m - st["front"]) @ n), 0.8), 60.0)
                cand = LineString([m + n * max(d_out, 0.3), turn, st["front"], st["p"] + st["n"] * 0.2])
                body = shapely.unary_union(plot["house_polys"]).buffer(-0.15)
                if not cand.intersects(body) and float(n @ st["n"]) > -0.2:
                    line = cand
            path = line.buffer(PATH_W_M / 2, cap_style="flat", join_style="mitre", mitre_limit=2.0).difference(others[i])
            paths.append(path)
            hard.append(path)
        plot["path"] = shapely.unary_union(paths) if paths else None
        plot["hard"] = shapely.unary_union(hard).buffer(0.03).buffer(-0.03) if hard else Polygon()
    for plot in plots:
        hard_u = plot["hard"]
        for k, q in enumerate(_polys(hard_u.difference(taken), 1.0)):
            out.append({"id": f"plot:{plot['id']}:drive{k}", "poly": q, "mat": DRIVE_MAT, "source": "plot", "parking": False,
                        "edging": False, "layer": GROUND_LAYER})
        lawn = plot["poly"].difference(taken).difference(hard_u.buffer(0.02))
        lawns = _polys(lawn, 6.0, simplify=0.12)
        plot["lawn"] = shapely.unary_union(lawns) if lawns else None
        for k, q in enumerate(lawns):
            out.append({"id": f"plot:{plot['id']}:lawn{k}", "poly": q, "mat": "plot_lawn", "source": "plot", "parking": False, "layer": GROUND_LAYER})
    return out


def _polys(g, min_area, simplify=0.05):
    g = g.buffer(-0.04).buffer(0.04)
    return [q for q in (p.simplify(simplify) for p in getattr(g, "geoms", [g]) if p.geom_type == "Polygon" and p.area > min_area)
            if q.geom_type == "Polygon" and not q.is_empty]


# ------------------------------------------------------------------------------------------------- geometry
def _fol(n):
    """COLOR_0 of a foliage vertex: normal * 0.5 + 0.5 (generator axes), a = 1 (Kamion/World PlotKit)."""
    n = np.asarray(n, float)
    n = n / max(float(np.linalg.norm(n)), 1e-9)
    return [n[0] * 0.5 + 0.5, n[1] * 0.5 + 0.5, n[2] * 0.5 + 0.5, 1.0]


class Kit:
    """Triangles of one plot in the `plot_kit` material. Quads / boxes get their own vertices (flat shading), ring
    shells share vertices (smooth). COLOR_0 (ADR 0124, shader Kamion/World PlotKit): hard surfaces a = 0 with
    rgb * 2 = albedo tint (`tint`, the plot's ageing), foliage a = 1 with rgb = normal."""

    def __init__(self, tint=(1.0, 1.0, 1.0)):
        self.V, self.UV, self.T, self.C = [], [], [], []
        self.n = 0
        self.tint = [min(max(float(c) * 0.5, 0.0), 1.0) for c in tint] + [0.0]

    def tris(self, V, UV, T, col=None):
        V = np.asarray(V, float).reshape(-1, 3)
        self.V.append(V)
        self.UV.append(np.asarray(UV, float).reshape(-1, 2))
        self.T.append(np.asarray(T, np.int64).reshape(-1, 3) + self.n)
        self.C.append(np.tile(self.tint, (len(V), 1)) if col is None else np.asarray(col, float).reshape(-1, 4))
        self.n += len(V)

    def quad(self, P, UV, col=None):
        self.tris(P, UV, [(0, 1, 2), (0, 2, 3)], col)

    def box(self, c, t, hx, hy, z0, z1, uv, top=True, sides=(0, 1, 2, 3), shift=(0.0, 0.0)):
        """Box centred on xy c, x axis along unit t, half sizes hx / hy, z0..z1; all vertices pinned to the texel uv
        (a swatch) unless uv is a callable (k, corner) -> uv for side k. shift: xy offset of the top (a leaning post)."""
        n = np.array([t[1], -t[0]])
        sh = np.asarray(shift, float)
        cs = [c - t * hx - n * hy, c + t * hx - n * hy, c + t * hx + n * hy, c - t * hx + n * hy]
        for k in sides:
            a, b = cs[(k + 1) % 4], cs[k]
            P = [[*a, z0], [*b, z0], [*(b + sh), z1], [*(a + sh), z1]]
            self.quad(P, [uv(k, j) for j in range(4)] if callable(uv) else [uv] * 4)
        if top:
            P = [[*(cs[0] + sh), z1], [*(cs[1] + sh), z1], [*(cs[2] + sh), z1], [*(cs[3] + sh), z1]]
            self.quad(P, [uv(4, j) for j in range(4)] if callable(uv) else [uv] * 4)

    def out(self):
        if not self.V:
            return None
        return np.concatenate(self.V), np.concatenate(self.UV), np.concatenate(self.T), np.concatenate(self.C)


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


LEAN_DEG = {"old": 3.0, "prl": 1.2, "new": 0.0}     # largest lean of a fence post by age class (review 0114 P2-r8-e)


def fence_run(kit, style, a, b, n, h, zf, key, col=None, ends=(True, True), lean_deg=0.0):
    """One straight fence run a -> b (outward normal n), height h above the ground zf(xy), in panels of SEG_M that
    follow the ground. col: list collecting collision quads. ADR 0124: ONE card per panel (the shader lights both
    faces; the two cards of ADR 0114 showed a ghost of every bar), and posts of old fences lean up to lean_deg."""
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
    ph = plinth[1] if plinth else 0.0
    rigid = brick or plinth is not None or style in ("wall", "concrete")
    ax, ay = round(float(a[0]), 1), round(float(a[1]), 1)
    # lean of every post (out of the fence plane), continuous along the run: panels are sheared between their posts
    lean = [0.0 if rigid or lean_deg <= 0 else math.tan(math.radians(lean_deg)) * (hfloat(key, "ln", ax, ay, k) * 2 - 1) ** 3 * h
            for k in range(nb + 1)]
    for k in range(nb):
        s0, s1 = cuts[k], cuts[k + 1]
        z0, z1 = Z[k], Z[k + 1]
        i0, i1 = (s0 + 0.19, s1 - 0.19) if brick else (s0, s1)          # infill between the brick posts
        if i1 - i0 > 0.05:
            if rowname not in PK.HALF_ROWS:                 # full-width rows tile (wall)
                uo = int(hfloat(key, "uo", ax, ay) * 4) * PK.BAY_M
                u0, u1 = (uo + s0) / PK.KIT_M, (uo + s1) / PK.KIT_M
            elif brick:
                u0, u1 = PK.uspan(rowname, 0.05, 0.05 + (i1 - i0))
            elif rowname in ("picket", "boards_rust", "boards_brown", "boards_grey"):
                # unframed rows: any stretch of the 5.12 m row, mirrored at random - neighbouring panels differ
                room = max(PK.HALF_M - (i1 - i0), 0.0)
                off = math.floor(hfloat(key, "uo", ax, ay, k) * room / 0.128) * 0.128
                u0, u1 = PK.uspan(rowname, off, off + (i1 - i0), hfloat(key, "mi", ax, ay, k) < 0.5)
            else:                                            # rows with posts drawn every BAY_M: a panel starts at a post
                u0, u1 = PK.uspan(rowname, 0.0, i1 - i0)
            f0, f1 = (i0 - s0) / (s1 - s0), (i1 - s0) / (s1 - s0)
            za, zb = z0 + (z1 - z0) * f0, z0 + (z1 - z0) * f1
            if rigid:                                        # ADR 0124 r2 (P2-r8-d): masonry / concrete / plinth bays are
                za = zb = min(z0, z1)                        # level and step at the posts; r1 sheared them along the slope
            la, lb = lean[k] + (lean[k + 1] - lean[k]) * f0, lean[k] + (lean[k + 1] - lean[k]) * f1
            lo = ph if plinth else -0.08
            A, B = a + t * i0, a + t * i1
            kit.quad([[*A, za + lo], [*B, zb + lo], [*(B + n * lb), zb + h], [*(A + n * la), za + h]],
                     [[u0, v0], [u1, v0], [u1, v1], [u0, v1]])
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
            kit.box(a + t * s0, t, 0.045, 0.045, z0 - 0.1, z0 + h + 0.04, PK.SWATCH[post], top=False, shift=n * lean[0])
    if brick and ends[1]:
        brick_post(kit, b, t, Z[-1], h + 0.12, (key, "e"))
    elif post and ends[1]:
        kit.box(b, t, 0.045, 0.045, Z[-1] - 0.1, Z[-1] + h + 0.04, PK.SWATCH[post], top=False, shift=n * lean[-1])
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
            kit.box(p, t, 0.05, 0.05, z - 0.1, z + hg + 0.10, frame, top=False)
    v0, v1 = PK.row(rowname)
    leaves = [(-W / 2 + 0.02, W / 2 - 0.02, 0.0)] if kind == "wicket" else \
        [(-W / 2 + 0.02, -0.012, 0.0), (0.012, W / 2 - 0.02, 0.0)] if kind == "swing" else \
        [(-W / 2 - 1.3, W / 2 + 0.05, -0.12)]
    for x0, x1, off in leaves:
        o = n * off
        zb, zt = z + 0.08, z + hg
        for (cx, hx, c0, c1) in ((0.5 * (x0 + x1), (x1 - x0) / 2, zb, zb + 0.045), (0.5 * (x0 + x1), (x1 - x0) / 2, zt - 0.045, zt),
                                 (x0 + 0.022, 0.022, zb, zt), (x1 - 0.022, 0.022, zb, zt)):
            kit.box(m + t * cx + o, t, hx, 0.022, c0, c1, frame, top=False, sides=(0, 2))
        m0 = 0.06 + int(hfloat(key, "gu", x0) * 2) * PK.BAY_M * (1.0 if x1 - x0 < PK.BAY_M - 0.2 else 0.0)
        u0, u1 = PK.uspan(rowname, m0, m0 + (x1 - x0 - 0.09))
        A, B = m + t * (x0 + 0.045) + o, m + t * (x1 - 0.045) + o
        kit.quad([[*A, zb + 0.045], [*B, zb + 0.045], [*B, zt - 0.03], [*A, zt - 0.03]],
                 [[u0, v0 + 0.06 * (v1 - v0)], [u1, v0 + 0.06 * (v1 - v0)], [u1, v1 - 0.04 * (v1 - v0)], [u0, v1 - 0.04 * (v1 - v0)]])
        if kind == "slide":                                  # ground beam of the cantilever gate
            kit.box(m + t * 0.5 * (x0 + x1) + o, t, (x1 - x0) / 2, 0.04, z + 0.02, z + 0.09, frame)
    if kind == "wicket":                                     # letter box on the post, street side
        box = PK.SWATCH[hpick(["galv", "steel_black", "steel_green", "wood_brown"], key, "mail")]
        p = m + t * (W / 2 + ph) + n * (ph + 0.05)
        kit.box(p, t, 0.13, 0.05, z + 0.95, z + 1.29, box)
    if col is not None:
        col.append((m - t * (W / 2), m + t * (W / 2), z - 0.1, z + hg))


def card(kit, p, z, sprite, W, H, ang, z_off=0.0):
    """Upright plant card W x H centred on p, in the vertical plane at angle ang. Foliage normals point away from the
    plant's axis and up (ADR 0124, review 0114 P1-r8-e: crossed cards lit per card showed a seam through the crown)."""
    u0, u1, v0, v1 = PK.sprite(sprite)
    r = np.array([math.cos(ang), math.sin(ang)])
    d = r * (W / 2)
    A, B = np.asarray(p) - d, np.asarray(p) + d
    kit.quad([[*A, z + z_off], [*B, z + z_off], [*B, z + z_off + H], [*A, z + z_off + H]],
             [[u0, v0], [u1, v0], [u1, v1], [u0, v1]],
             [_fol([-r[0] * 0.9, -r[1] * 0.9, 0.35]), _fol([r[0] * 0.9, r[1] * 0.9, 0.35]),
              _fol([r[0] * 0.6, r[1] * 0.6, 0.8]), _fol([-r[0] * 0.6, -r[1] * 0.6, 0.8])])


def thuja(kit, p, z, h, r, key, dead=False):
    """Columnar thuja ('Smaragd' / 'Brabant'). ADR 0124 (review 0114 P1-r8-d: a 6-sided prism with a sharp pyramid on
    top): a 5-sided core of the foliage row that ends in a blunt dome below the top, wrapped in two crossed silhouette
    cards of photographed twigs - the outline is ragged twig tips, the top is round. ~39 triangles (ADR 0114: 36-60)."""
    fr = (0.0, 0.22, 0.62, 0.86)                             # core rings (fractions of h); the dome closes at 0.93 h
    kk = (0.78, 0.92, 0.80, 0.46)
    v0, v1 = PK.row("thuja")
    sides = 5
    circ = 2 * math.pi * r
    span = min(circ / PK.KIT_M, 0.11) if dead else circ / PK.KIT_M
    u0 = (PK.THUJA_GREEN_U + 0.015 + hfloat(key, "tu") * (1 - PK.THUJA_GREEN_U - 0.03 - span)) if dead else \
        hfloat(key, "tu") * (PK.THUJA_GREEN_U - span - 0.01)
    a0 = hfloat(key, "ta") * 6.2832
    lean = (np.array([hfloat(key, "tlx"), hfloat(key, "tly")]) - 0.5) * 0.08
    V, UV, C = [], [], []
    for i, f in enumerate(fr):
        zz = f * h
        for j in range(sides + 1):
            jj = j % sides
            rr = r * 0.84 * kk[i] * (0.92 + 0.16 * hfloat(key, "tr", i, jj))
            ang = a0 + 2 * math.pi * j / sides
            V.append([p[0] + lean[0] * zz + math.cos(ang) * rr, p[1] + lean[1] * zz + math.sin(ang) * rr, z - 0.05 + zz])
            UV.append([u0 + span * j / sides, v0 + (v1 - v0) * (0.02, 0.36, 0.70, 0.98)[i]])
            C.append(_fol([math.cos(ang) * 0.9, math.sin(ang) * 0.9, 0.25 + 0.5 * f]))
    top = len(V)
    V.append([p[0] + lean[0] * h * 0.93, p[1] + lean[1] * h * 0.93, z - 0.05 + h * 0.93])
    UV.append([u0 + span * 0.5, v0 + (v1 - v0) * 0.72])
    C.append(_fol([0.0, 0.0, 1.0]))
    T = []
    m = sides + 1
    for i in range(len(fr) - 1):
        for j in range(sides):
            a_, b_, c_, d_ = i * m + j, i * m + j + 1, (i + 1) * m + j + 1, (i + 1) * m + j
            T += [(a_, b_, c_), (a_, c_, d_)]
    for j in range(sides):
        T.append(((len(fr) - 1) * m + j, (len(fr) - 1) * m + j + 1, top))
    kit.tris(V, UV, T, C)
    sp = "thuja_c" if dead or hfloat(key, "tsp") < 0.12 else ("thuja_a" if hfloat(key, "tsp") < 0.56 else "thuja_b")
    pc = np.asarray(p, float) + lean * h * 0.5
    for i in range(2):
        card(kit, pc, z - 0.05, sp, 2.5 * r, h * 1.02, a0 + 0.3 + i * math.pi / 2)


def spruce(kit, p, z, h, key):
    """Blue spruce (świerk kłujący, refs P02 / P17 / P18). ADR 0124: three crossed silhouette cards of photographed
    twigs (whorls, scalloped outline) and a trunk - 14 triangles (ADR 0114: up to 108 in drooping skirts that showed
    their construction from above)."""
    sp = "spruce_a" if hfloat(key, "ss") < 0.5 else "spruce_b"
    W = 0.40 * h + 0.9
    a0 = hfloat(key, "sa") * 3.1416
    kit.box(np.asarray(p, float), np.array([1.0, 0.0]), 0.07, 0.07, z - 0.1, z + h * 0.14, PK.SWATCH["trunk"], top=False)
    for i in range(3):
        card(kit, p, z, sp, W, h * 0.96, a0 + i * math.pi / 3, z_off=h * 0.04)


def big_tree(kit, p, z, h, key):
    """A grown garden tree (walnut, linden, maple: refs P05, P07, P08, P12 - the crowns stand above every roof):
    trunk + three crossed crown cards."""
    wm, hm = PK.SPRITE_M["tree_a"]
    W = h * (0.85 + 0.25 * hfloat(key, "bw"))
    H = W * hm / wm
    a0 = hfloat(key, "by") * 3.1416
    tr = 0.12 + 0.012 * h
    kit.box(np.asarray(p, float), np.array([math.cos(a0), math.sin(a0)]), tr, tr, z - 0.1, z + h - H * 0.86, PK.SWATCH["trunk"], top=False)
    for i in range(3):
        card(kit, p, z, "tree_a", W, H, a0 + i * math.pi / 3, z_off=h - H)


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
    sp = "shrub_a" if hfloat(key, "sh") < 0.7 else "shrub_b"
    wm, hm = PK.SPRITE_M[sp]
    k = h / hm
    a0 = hfloat(key, "sy") * 3.1416
    for i in range(2):
        card(kit, p, z - 0.04, sp, wm * k, h, a0 + i * math.pi / 2)


def hedge(kit, a, b, n, zf, h, key, thick=0.6):
    """Clipped broadleaf hedge a -> b (n: normal towards the street), refs P08 / P12: two leafy sides with a ragged top
    line and a top, in steps of SEG_M that follow the ground. 6 triangles per step."""
    L = float(np.hypot(*(b - a)))
    if L < 1.5:
        return 0.0
    t = (b - a) / L
    nb = max(1, int(math.ceil(L / SEG_M - 1e-6)))
    cuts = [L * k / nb for k in range(nb + 1)]
    Z = [zf(a + t * s) - 0.03 for s in cuts]
    H = [h * (0.92 + 0.16 * hfloat(key, "hh", k)) for k in range(nb + 1)]
    v0, v1 = PK.row("hedge")
    u_off = hfloat(key, "hu") * PK.KIT_M
    up = np.array([0.0, 0.0, 1.0])
    for k in range(nb):
        s0, s1 = cuts[k], cuts[k + 1]
        u0, u1 = (u_off + s0) / PK.KIT_M, (u_off + s1) / PK.KIT_M
        for sg in (1.0, -1.0):
            o = n * (thick / 2 * sg)
            A, B = a + t * s0 + o, a + t * s1 + o
            nn = np.array([n[0] * sg * 0.8, n[1] * sg * 0.8, 0.45])
            top = np.array([n[0] * sg * 0.45, n[1] * sg * 0.45, 0.85])
            kit.quad([[*A, Z[k]], [*B, Z[k + 1]], [*B, Z[k + 1] + H[k + 1] + 0.12], [*A, Z[k] + H[k] + 0.12]],
                     [[u0, v0], [u1, v0], [u1, v1], [u0, v1]], [_fol(nn), _fol(nn), _fol(top), _fol(top)])
        A, B = a + t * s0, a + t * s1
        o = n * (thick / 2)
        vm0, vm1 = v0 + (v1 - v0) * 0.30, v0 + (v1 - v0) * 0.62
        kit.quad([[*(A + o), Z[k] + H[k]], [*(B + o), Z[k + 1] + H[k + 1]], [*(B - o), Z[k + 1] + H[k + 1]], [*(A - o), Z[k] + H[k]]],
                 [[u0, vm0], [u1, vm0], [u1, vm1], [u0, vm1]], [_fol(up)] * 4)
    return L


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


def _wire(buf, a, za, b, zb, src, sag=0.03, half_w=0.013):
    """One conductor a -> b as a ribbon of the `wires` layer (furniture.power_lines convention: UV0 = side, physical
    half width; COLOR_0 = tangent)."""
    from . import furniture as FU
    L = float(np.hypot(*(b - a)))
    if L < 2.0:
        return 0
    tt, Z, dz = FU.catenary_span(L, za, zb, sag_ratio=sag)
    Q = a + (b - a) * tt[:, None]
    dvec = (b - a) / L
    tan = np.column_stack([np.repeat(dvec[None], len(tt), 0), dz])
    tan /= np.linalg.norm(tan, axis=1, keepdims=True)
    V = np.concatenate([np.column_stack([Q, Z - half_w]), np.column_stack([Q, Z + half_w])])
    m = len(Q)
    T = np.array([(i, i + 1, m + i + 1) for i in range(m - 1)] + [(i, m + i + 1, m + i) for i in range(m - 1)])
    uv = np.column_stack([np.repeat([-1.0, 1.0], m), np.full(2 * m, half_w)])
    col = np.column_stack([np.concatenate([tan, tan]) * 0.5 + 0.5, np.ones(2 * m)])
    buf.add("wires", "wire", V, uv, T, src=src, COL=col)
    return len(T)


def street_wires(buf, rp, items, zf, report):
    """Overhead low-voltage line of the house streets (ADR 0124; refs P01-P05, P13-P16, P21-P25: poles and wires are in
    nearly every frame of a Białystok street of single-family houses, none stood in the world). OSM has no
    power=minor_line in the tile and BDOT OT_SULN_L carries only the MV / HV lines, so this is a RULE (WORKING_VALUE):
    on every chain with at least two house driveways the street-lamp poles of the side with more lamps carry one
    insulated bundle (AsXSn) from pole to pole, and every house on the chain gets a service drop from the nearest
    pole to its wall. No new poles: the lamps of streetscape.furniture are the supports."""
    from roads import network as NW  # noqa: F401
    plots = rp["plots"]
    by_chain = {}
    for p in plots:
        a = p.get("access")
        if a and a.get("chain"):
            by_chain.setdefault(a["chain"], []).append(p)
    lamps = {}
    for it in items or ():
        if it["p"].startswith("lamp_") and it.get("src", "").startswith("rule:c:"):
            lamps.setdefault(it["src"][5:], []).append(it)
    rep = {"chains": 0, "spans": 0, "span_m": 0.0, "drops": 0, "tris": 0, "chains_without_lamps": 0}
    for cid, pls in sorted(by_chain.items()):
        if len(pls) < 2:
            continue
        ls = lamps.get(cid, [])
        side = pls[0]["access"]["side"]
        # lamps of one side, ordered along the street (projection on the direction of the gate row)
        q0 = np.asarray(pls[0]["access"]["q"])
        if len(ls) < 2:
            rep["chains_without_lamps"] += 1
            continue
        P = np.array([[it["e"], it["n"]] for it in ls])
        c0 = P.mean(0)
        _, _, vt = np.linalg.svd(P - c0)
        ax = vt[0]
        lat = (P - c0) @ np.array([-ax[1], ax[0]])
        sgn = np.sign(lat)
        keep = sgn >= 0 if (sgn >= 0).sum() >= (sgn < 0).sum() else sgn < 0
        if abs(lat).max() < 2.5:                             # all on one line already
            keep = np.ones(len(P), bool)
        idx = [i for i in np.argsort((P - c0) @ ax) if keep[i]]
        if len(idx) < 2:
            rep["chains_without_lamps"] += 1
            continue
        rep["chains"] += 1
        pts = [(P[i], float(ls[i]["z"]) + min(WIRE_H_M, _lamp_h(ls[i]["p"]) - 0.8)) for i in idx]
        for (a, za), (b, zb) in zip(pts, pts[1:]):
            L = float(np.hypot(*(b - a)))
            if 8.0 <= L <= 70.0:
                rep["tris"] += _wire(buf, a, za, b, zb, f"plotwire:{cid}", sag=0.025, half_w=0.016)
                rep["spans"] += 1
                rep["span_m"] += L
        for p in pls:                                        # service drop to the nearest wall of the house
            hp = p["house_polys"][0]
            j = min(range(len(pts)), key=lambda k: hp.distance(Point(*pts[k][0])))
            a, za = pts[j]
            d = hp.distance(Point(*a))
            if not (4.0 < d < 45.0):
                continue
            b = np.asarray(shapely.ops.nearest_points(hp, Point(*a))[0].coords[0])
            zb = zf(b) + min(DROP_H_HOUSE_M, max(p.get("house_h", 6.0) - 0.8, 2.6))
            rep["tris"] += _wire(buf, a, za - 0.25, b, zb, f"plotwire:{p['id']}", sag=0.035, half_w=0.009)
            rep["drops"] += 1
        _ = (side, q0)
    rep["span_m"] = round(rep["span_m"])
    report["street_wires"] = rep
    return rep


def _lamp_h(proto):
    for tok in proto.split("_"):
        if tok.endswith("m") and tok[:-1].isdigit():
            return float(tok[:-1])
    return 8.0


# ------------------------------------------------------------------------------------------------- build
SEE_THROUGH = ("picket", "chainlink", "bars", "brick_picket", "brick_bars")
HEDGE_SHARE = {"old": 0.34, "prl": 0.36, "new": 0.22}
BIG_TREE_SHARE = {"old": 0.6, "prl": 0.45, "new": 0.15}
AGE_TINT = {"old": (0.80, 0.14), "prl": (0.92, 0.08), "new": (1.0, 0.04)}      # mean albedo factor, spread (ageing)


def build(buf, rp, zf, surf_top, report, items=None):
    """Mesh every plot of the region plan into buf (layer `furniture`, material `plot_kit`; collision quads of the
    fences and closed gates; a paved strip over a grass verge / shoulder where the driveway crosses one).
    zf(xy) -> ground height (lawn / driveway surface), surf_top: furniture.SurfaceTop of the road meshes,
    items: placed street furniture (the lamp poles carry the overhead line of the house streets)."""
    import shapely.ops                                       # noqa: F401
    plots = rp["plots"]
    rep = {"plots": len(plots), "fence_m": {}, "gates": 0, "sliding_gates": 0, "wickets": 0, "drives": 0, "kerb_drops": len(rp["drops"]),
           "verge_overlays": 0, "thujas": 0, "spruces": 0, "fruit_trees": 0, "big_trees": 0, "shrubs": 0, "hedge_m": 0.0,
           "flower_cards": 0, "bins": 0, "tris": 0, "instances": 0, "plot_m2_median": 0.0, "age": {}, "styles_front": {},
           "styles_side": {}, "access": rp.get("access_stats", {}), "fence_step_zone_hits": 0}
    keepout = []
    for plot in plots:
        key, lay = plot["key"], plot["lay"]
        age = plot["age"]
        mean, spread = AGE_TINT[age]
        k0 = mean + spread * (hfloat(key, "tint") * 2 - 1)
        tint = (k0 * (1 + 0.04 * (hfloat(key, "tr") - 0.5)), k0, k0 * (1 - 0.05 * hfloat(key, "tb")))
        kit, col = Kit(tint), []
        src_id = f"plot:{plot['id']}"
        rep["age"][age] = rep["age"].get(age, 0) + 1
        rep["styles_front"][plot["front_style"]] = rep["styles_front"].get(plot["front_style"], 0) + 1
        rep["styles_side"][plot["side_style"]] = rep["styles_side"].get(plot["side_style"], 0) + 1
        zones = shapely.unary_union(plot.get("door_zones") or [Polygon()])
        for r in lay["runs"]:
            fence_run(kit, r["style"], r["a"], r["b"], r["n"], r["h"], zf, key, col, lean_deg=LEAN_DEG[age])
            rep["fence_m"][r["style"]] = rep["fence_m"].get(r["style"], 0.0) + float(np.hypot(*(r["b"] - r["a"])))
            rep["fence_step_zone_hits"] += int(LineString([r["a"], r["b"]]).intersects(zones))
        gates = ([lay["gate"]] if lay["gate"] is not None else []) + ([lay["wicket"]] if lay["wicket"] is not None else []) + lay["wickets"]
        for g in gates:
            gate_geo(kit, g, plot["front_style"], plot["front_h"], max(zf(g["m"] - g["t"] * g["w"] / 2), zf(g["m"] + g["t"] * g["w"] / 2)),
                     (key, g["kind"], round(float(g["m"][0]), 1)), col)
            if g["kind"] == "wicket":
                rep["wickets"] += 1
            else:
                rep["gates"] += 1
                rep["sliding_gates"] += g["kind"] == "slide"
        hard = [q for q in (plot.get("hard"),) if q is not None and not q.is_empty]
        hard_u = shapely.unary_union(hard + [zones]).buffer(0.35) if (hard or not zones.is_empty) else Polygon()
        keepout += hard
        if plot.get("drive") is not None and lay["gate"] is not None:
            rep["drives"] += 1
            rep["verge_overlays"] += _verge_overlay(buf, plot, surf_top, src_id, zf, rp.get("roads_poly"), rp.get("carriage"))
        # ---- garden
        poly = plot["poly"]
        foot = plot["foot"]
        free = poly.buffer(-0.9).difference(foot.buffer(1.0)).difference(hard_u)
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
                while s < s1 and k < THUJA_ROW_MAX:
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
            # a clipped hedge behind the street fence (refs P08, P12: the hedge stands above the fence)
            fr_runs = [r for r in lay["runs"] if r["front"] and np.hypot(*(r["b"] - r["a"])) > 3.0]
            hedged = None
            if fr_runs and plot["front_style"] in SEE_THROUGH and hfloat(key, "hedge") < HEDGE_SHARE[age] * 1.6 or \
                    fr_runs and hfloat(key, "hedge") < HEDGE_SHARE[age] * 0.5:
                hh = plot["front_h"] + (0.15 + 0.5 * hfloat(key, "hedge_h") if hfloat(key, "hedge_o") < 0.7 else -0.3)
                for r in fr_runs:
                    t = (r["b"] - r["a"]) / np.hypot(*(r["b"] - r["a"]))
                    c0, c1 = r["a"] + t * 0.35 - r["n"] * 0.55, r["b"] - t * 0.35 - r["n"] * 0.55
                    seg = LineString([c0, c1]).difference(hard_u.buffer(0.2))
                    for q in getattr(seg, "geoms", [seg]):
                        if q.geom_type == "LineString" and q.length > 1.5 and poly.contains(q):
                            q0, q1 = (np.asarray(x) for x in q.coords[:2])
                            rep["hedge_m"] += hedge(kit, q0, q1, r["n"], zf, max(hh, 0.9), (key, "hdg", round(float(q0[0]), 1)))
                            hedged = True
            # perennials along the front wall of the house and, sometimes, behind the street fence
            hedge_e = max(_edges(plot["house_polys"][0]), key=lambda e: float(e[4] @ plot["front"]) * 10 + e[2] * 0.01)
            a, b, L, t, n = hedge_e
            if float(n @ plot["front"]) > 0.6 and hfloat(key, "bed") < 0.7:
                q0, q1 = a + t * (0.15 * L) + n * 0.55, a + t * (0.85 * L) + n * 0.55
                bed = LineString([q0, q1]).difference(hard_u.buffer(0.3))
                for seg in getattr(bed, "geoms", [bed]):
                    if seg.geom_type == "LineString" and seg.length > 1.2 and poly.contains(seg):
                        c0, c1 = (np.asarray(x) for x in seg.coords[:2])
                        rep["flower_cards"] += flower_bed(kit, c0, c1, zf, (key, "bedh"))
            if fr_runs and not hedged and hfloat(key, "bed2") < (0.5 if age != "new" else 0.25):
                r = hpick(fr_runs, key, "bed2r")
                t = (r["b"] - r["a"]) / np.hypot(*(r["b"] - r["a"]))
                c0, c1 = r["a"] + t * 0.5 - r["n"] * 0.55, r["b"] - t * 0.5 - r["n"] * 0.55
                if not LineString([c0, c1]).intersects(hard_u) and poly.contains(LineString([c0, c1])):
                    rep["flower_cards"] += flower_bed(kit, c0, c1, zf, (key, "bedf"))
            front_g = free.intersection(Polygon([*(np.asarray(poly.centroid.coords[0]) + plot["front"] * 200 + s * np.array([-plot["front"][1], plot["front"][0]]) * 200 for s in (-1, 1)),
                                                 *(np.asarray(foot.centroid.coords[0]) + s * np.array([-plot["front"][1], plot["front"][0]]) * 200 for s in (1, -1))]))
            back_g = free.difference(front_g).buffer(-1.2)
            # grown trees first (they need the room): crowns above the roofs are what the reference streets look like
            if hfloat(key, "big") < BIG_TREE_SHARE[age] and poly.area > 380.0:
                for k in range(1 + int(hfloat(key, "nbig") < 0.3)):
                    reg = back_g.buffer(-1.5) if hfloat(key, "big_w", k) < 0.65 else front_g.buffer(-2.2)
                    reg = reg.difference(foot.buffer(3.5))
                    p = spot("big", k, reg, 6.0)
                    if p is not None:
                        big_tree(kit, p, zf(p), 7.5 + 5.0 * hfloat(key, "big_h", k), (key, "bt", k))
                        rep["big_trees"] += 1
            if hfloat(key, "spruce") < SPRUCE_SHARE[age]:
                for k in range(1 + int(hfloat(key, "nspruce") < 0.3)):
                    reg = front_g.buffer(-1.6) if hfloat(key, "spr_w", k) < 0.6 else back_g.buffer(-0.6)
                    p = spot("spruce", k, reg, 4.0)
                    if p is not None:
                        hh = (2.5 + 2.5 * hfloat(key, "sprh", k)) if age == "new" else (4.0 + 6.0 * hfloat(key, "sprh", k))
                        spruce(kit, p, zf(p), hh, (key, "spr", k))
                        rep["spruces"] += 1
            if hfloat(key, "tree") < FRUIT_SHARE[age] and poly.area > 250.0:
                for k in range(1 + int(hfloat(key, "ntree") * (4 if age == "old" else 3))):
                    p = spot("tree", k, back_g.buffer(-0.8), 4.2)
                    if p is not None:
                        fruit_tree(kit, p, zf(p), 3.0 + 1.4 * hfloat(key, "tree_h", k), (key, "ft", k))
                        rep["fruit_trees"] += 1
            near_fence = free.difference(poly.buffer(-2.4))
            near_house = free.intersection(foot.buffer(2.4))
            for k in range(4 + int(hfloat(key, "nshrub") * 6)):
                reg = near_house if hfloat(key, "shrub_where", k) < 0.4 and not near_house.is_empty else near_fence
                p = spot("shrub", k, reg, 1.4)
                if p is not None:
                    shrub(kit, p, zf(p), 0.8 + 1.1 * hfloat(key, "shrub_h", k), (key, "shr", k))
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
            buf.add(KIT_LAYER, "plot_kit", o[0], o[1], o[2], src=src_id, COL=o[3])
            rep["tris"] += len(o[2])
        for a, b, z0, z1 in col:
            V = np.array([[*a, z0], [*b, z0], [*b, z1], [*a, z1]])
            buf.add("collision", "collision_fence", V, V[:, :2], [(0, 1, 2), (0, 2, 3), (0, 2, 1), (0, 3, 2)], src=src_id)
    if items is not None:
        street_wires(buf, rp, items, zf, rep)
    rep["hedge_m"] = round(rep["hedge_m"])
    rep["list"] = [{"id": p["id"], "age": p["age"], "front": p["front_style"], "side": p["side_style"],
                    "c": [round(float(v), 1) for v in p["poly"].centroid.coords[0]],
                    "gate": None if p["lay"]["gate"] is None else {
                        "m": [round(float(v), 2) for v in p["lay"]["gate"]["m"]],
                        "n": [round(float(v), 3) for v in p["lay"]["gate"]["n"]], "kind": p["lay"]["gate"]["kind"]},
                    "wicket": None if p["lay"]["wicket"] is None else {
                        "m": [round(float(v), 2) for v in p["lay"]["wicket"]["m"]],
                        "n": [round(float(v), 3) for v in p["lay"]["wicket"]["n"]]},
                    "door": [[round(float(v), 2) for v in st["p"]] + [round(float(v), 3) for v in st["n"]] for st in p.get("steps") or []],
                    "access": None if p.get("access") is None else {"d_cw": round(p["access"]["d_cw"], 2),
                                                                    "walk": p["access"]["walk"], "chain": p["access"]["chain"],
                                                                    "q": [round(float(v), 2) for v in p["access"]["q"]],
                                                                    "kerbed": bool(p["access"].get("kerbed"))}}
                   for p in plots]
    rep["fence_m"] = {k: round(v) for k, v in sorted(rep["fence_m"].items())}
    rep["plot_m2_median"] = round(float(np.median([p["poly"].area for p in plots])), 1) if plots else 0.0
    report["plots"] = rep
    return {"keepout": keepout, "lawns": [p["lawn"] for p in plots if p.get("lawn") is not None], "plots": plots}


def _verge_overlay(buf, plot, surf_top, src_id, zf=None, roads_poly=None, carriage=None):
    """Between the gate apron (a paved item, cut at the road footprint) and the carriageway the driveway crosses
    whatever the road profile has there: a footway (stays as it is, lowered with the kerb), a grass verge / gravel
    shoulder, or the battered edge of the footprint with no surface at all. Pave that stretch.
    ADR 0124 (review 0114 P1-r8-a / b): the strip is a POLYGON - the driveway width clipped to the road footprint
    (+0.35 m of overlap onto the apron: no line of grass between the two) MINUS the carriageway and the kerb stone,
    so no paver lies on the asphalt, the lowered kerb stays a kerb, and the edge along the kerb is its true line
    instead of a staircase of grid cells. Draped 2 cm over the road-side surface, on the apron surface outside it."""
    from . import paved as PV
    acc = plot.get("access")
    if acc is None or surf_top is None or roads_poly is None or carriage is None:
        return 0
    footway = acc.get("walk") == "sidewalk_paving" and acc.get("kind") == 0
    g = plot["lay"]["gate"]
    m, n = g["m"], g["n"]
    L = acc["d_cw"]
    strip = LineString([m + n * 0.02, m + n * (L + 1.0)]).buffer(g["w"] / 2, cap_style="flat")
    band = KERB_BAND_M if acc.get("kerbed") else 0.02
    zone = strip.intersection(roads_poly.buffer(0.35)).difference(carriage.buffer(band))
    polys = [q for q in _polys(zone, 0.15, simplify=0.01) if q.distance(Point(*m)) < L]
    done = 0
    for poly in polys:
        T2 = PV.triangulate(poly, 0.5)
        if not len(T2):
            continue
        P = T2.reshape(-1, 2)
        q = np.round(P * 1000).astype(np.int64)
        u, first, inv = np.unique(q, axis=0, return_index=True, return_inverse=True)
        P = P[first]
        T = inv.ravel().reshape(-1, 3)
        top = np.array([surf_top.top(float(x), float(y)) for x, y in P])
        inside = shapely.contains(roads_poly, shapely.points(P))
        on_road = np.isfinite(top) & inside
        if footway:                                          # the footway is paved already: only the part without it
            tri_ok = ~(on_road[T].all(1))
            T = T[tri_ok]
            if not len(T):
                continue
        Z = np.array([top[i] if on_road[i] else zf(P[i]) for i in range(len(P))]) + 0.02
        # ADR 0124 r2 (r1: a wedge of grass between this strip and the apron on driveways oblique to the road,
        # `r16_kerb_0`): outside the road surfaces the strip lay 2 cm over the INTERPOLATED ground, and the terrain
        # mesh (1 m / 2 m grid, other triangle split) came through it on the batter of the footprint edge. There the
        # strip is now a ruled surface along the driveway (kerb side -> apron side), never lower than the highest
        # ground sample within 0.8 m + 3 cm.
        un = (P - m) @ n
        free = ~on_road
        if free.any() and on_road.any():
            u_in = float(un[on_road].max())                      # last vertex on a road surface, along the driveway
            u_out = float(un.max())
            tt = np.array([-n[1], n[0]])
            for i in np.nonzero(free)[0]:
                s_ = float((P[i] - m) @ tt)
                near_i = on_road & (np.abs((P - m) @ tt - s_) < 0.6)
                za = float(Z[near_i][np.argmax(un[near_i])]) if near_i.any() else Z[i]
                ua = float(un[near_i].max()) if near_i.any() else u_in
                zb = zf(m + tt * s_ + n * u_out) + 0.03
                f = min(max((un[i] - ua) / max(u_out - ua, 0.05), 0.0), 1.0)
                ring = max(zf(P[i] + d_ * 0.8) for d_ in (n, -n, tt, -tt, 0 * n))
                Z[i] = max(za + (zb - za) * f, ring + 0.03)
        V = np.column_stack([P, Z])
        buf.add(GROUND_LAYER, DRIVE_MAT, V, P.copy(), T, src=src_id + ":verge", UV1=np.tile([25.0, 25.0], (len(V), 1)))
        done = 1
    return done


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
