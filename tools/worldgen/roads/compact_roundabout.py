"""Compact roundabout built as ONE junction (ADR 0218 section 5c, owner D75).

A small roundabout whose arms split into one-way entry / exit carriageways right at the ring (DK65 x DW671 in Knyszyn:
OSM way 1426801304, axis radius 8.65 m, 8 ring nodes on a 54 m circumference, ring edges 1.6-11.6 m) cannot be built
by the generic junction machinery: every ring node is a junction, the ring chain between the exit and the entry of
one arm enters the same cluster with both ends and the four patches self-intersect (render r1 of int-dk65-s22).

With the authored key `compact_roundabout` on the ring way (`set: {compact_roundabout: {...}}`, only there) the whole
roundabout becomes one junction:

  * nodes = ring nodes + the split nodes of the one-way feeders; the ring chains and the feeders are absorbed
    (no ribbons), the arms of the junction are the roads leaving the split nodes;
  * paved outline = disc of the outer ring radius (fitted axis radius + ring width / 2) + feeder carriageways
    (axis +- half width) + the arm stubs, closed morphologically with `closing_r_m` (kerb returns between an exit
    and the next entry). The pieces of the outline between two arms are the junction's corners (kind "fillet" with
    an explicit polyline and per-point outward normals), so kerbs / sidewalks / verges of the arms run round them
    with the ordinary corner strips;
  * centre island = truck apron (lip, 2 % rise, own surface: the ring's `truck_apron`, else the rule) as a full
    annulus + island kerb + gravel inside, laid on the patch;
  * splitter islands = the gap between the entry and the exit of one arm, narrowed to `splitter_w_m` about the
    middle line: kerbed traffic islands (gores.Island), at least `SPLITTER_MIN_M2`.

ADR 0274 (kerb mode, on when the key carries `entry_r_m` / `exit_r_m`):
  * the one-way lanes are not the mapped lines (GPS-traced, nearly tangent to the ring: wide funnels and fat asphalt
    patches between the arms) but designed lanes (lay_lanes): parallel to the arm axis, at most `splitter_w_m / 2 +
    lane_w_m / 2` from it, joining the ring axis with an arc whose outer kerb has the radius `entry_r_m` (kerb on
    the right of the entering lane) / `exit_r_m`; the outline is the ring disc + these lanes + the arm ends, with
    the same radii as fillets wherever a concave corner is left;
  * `crossings: [osm way of the arm, ...]`: pedestrian crossing P-10 across the entry and the exit lane,
    `crossing_offset_m` outside the ring carriageway, the splitter island is cut through at road level (refuge);
  * P-13 across every entry lane along the edge of the ring carriageway (Dz.U. 2019 poz. 2311 zal. 2 pkt 4.2.4 with
    4.2.3 and 8.4), not at the split node;
  * centre island fill: concentric rings with fewer segments towards the centre and a smooth height field.

ADR 0227 D41: `outer_diameter_m` (optional) replaces the fitted ring axis radius by outer_diameter_m / 2 - ring width
/ 2 (range and plausibility checked, else stale); report: r_axis_m vs r_axis_fit_m.

Nothing here runs for a ring without the key: every other region is byte-identical.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np
import shapely
from shapely.geometry import LineString, Point, Polygon

from . import standards as S

KEY = "compact_roundabout"
DEFAULTS = {"closing_r_m": 8.0,        # WORKING_VALUE: radius of the kerb returns exit -> next entry (photo 9: 6-10 m)
            "splitter_w_m": 2.4,       # WORKING_VALUE: widest part of a splitter island (photo 9: ~2-3 m at the ring)
            "splitter_gap_m": 0.6,     # WORKING_VALUE: splitter nose this far outside the outer ring edge
            "lane_w_m": 4.5,           # WORKING_VALUE: entry / exit lane kept clear along the outer kerb (photo 9: ~4.2)
            "lane_clear_m": 1.9,       # WORKING_VALUE: no island this close to a feeder axis (truck half width + 0.6)
            "island_fill": "island_sand"}
# ADR 0274 keys (no default: without entry_r_m / exit_r_m the ADR 0218 outline is built)
KERB_DEFAULTS = {"entry_r_m": 6.0,          # WORKING_VALUE: kerb radius on the right of an entry lane
                 "exit_r_m": 8.0,           # WORKING_VALUE: kerb radius on the right of an exit lane
                 "crossing_offset_m": 5.0,  # WORKING_VALUE: near edge of P-10 from the edge of the ring carriageway
                 "crossings": []}           # osm ways of the two-way arms that carry a pedestrian crossing
# accepted ranges (review s23 D18 P2-6: values are validated, a bad entry is stale and never raises)
LIMITS = {"closing_r_m": (1.0, 30.0), "splitter_w_m": (0.6, 8.0), "splitter_gap_m": (0.0, 3.0), "lane_w_m": (2.5, 7.0),
          "lane_clear_m": (1.0, 4.0), "entry_r_m": (2.0, 30.0), "exit_r_m": (2.0, 40.0), "crossing_offset_m": (0.0, 15.0),
          "outer_diameter_m": (14.0, 40.0)}
# ADR 0227 D41 (d): `outer_diameter_m` = outer kerb diameter of the ring carriageway, authored when the mapped ring axis
# (least-squares circle through the OSM ring) is known to be off (Knyszyn: OSM 22.3 m outer vs ~26 m on owner photo 9).
# The ring axis radius becomes outer_diameter_m / 2 - ring width / 2 about the fitted centre; the designed lanes
# (kerb mode) meet the ring on that circle. The ring may move at most OUTER_D_MAX_SHIFT of the fitted axis radius
# (at least OUTER_D_MIN_SHIFT_M): a value further off is a different roundabout (wrong target, typo) - stale, fitted
# radius kept.
OUTER_D_MAX_SHIFT = 0.4
OUTER_D_MIN_SHIFT_M = 2.0
FILLS = ("island_sand", "island_gravel", "verge_grass")
RING_INNER_MIN_M = 1.5       # a ring whose inner carriageway edge is closer to the centre has no room for an island
FEEDER_MAX_M = 80.0          # one-way carriageway between the ring and its split node (Knyszyn: 16.7-29.9 m as
                             # mapped, up to 50 m with the authored carriageway_split of DK65, ADR 0274)
SPLITTER_MIN_M2 = 3.0        # WORKING_VALUE: smaller splitters are left as asphalt
SPLITTER_MIN_W = 0.6         # WORKING_VALUE: narrower tips of a splitter are cut (kerb 2 x 0.15 + top)
STUB_MAX_M = 30.0
ISLAND_SKIRT_M = 0.35
RING_STEP_M = 0.6


@dataclass
class Spec:
    id: str
    ring: list                       # ring chains
    feeders: list                    # absorbed one-way chains ring <-> split node
    nodes: list
    center: np.ndarray
    r_axis: float
    w_ring: float                    # asphalt width of the ring
    apron: tuple                     # side params (kind, h, w, depth, mat code) of the island side
    opts: dict
    outline: Polygon | None = None
    splitters: list = field(default_factory=list)
    notes: list = field(default_factory=list)
    mouths: dict = field(default_factory=dict)      # kerb mode: split node -> {"mid": axis ring <- split, "half_w"}
    crossings: list = field(default_factory=list)   # kerb mode: planned P-10 (stripes as polygons)
    p13: list = field(default_factory=list)         # kerb mode: (arm chain id, polyline along the ring edge)
    r_axis_fit: float | None = None                 # fitted (OSM) ring axis radius; differs from r_axis only with the
                                                    # authored `outer_diameter_m` (ADR 0227 D41)

    @property
    def r_out(self):
        return self.r_axis + self.w_ring / 2

    @property
    def r_in(self):
        return self.r_axis - self.w_ring / 2


def validate(o):
    """The options dict of a `compact_roundabout` key, or None when a key is unknown or a value is not usable."""
    if not isinstance(o, dict) or set(o) - set(LIMITS) - {"island_fill", "crossings"}:
        return None
    out = {}
    for k, v in o.items():
        if k == "island_fill":
            if v not in FILLS:
                return None
            out[k] = v
        elif k == "crossings":
            if not isinstance(v, list) or any(isinstance(w, bool) or not isinstance(w, int) for w in v):
                return None
            out[k] = list(v)
        else:
            if isinstance(v, bool) or not isinstance(v, (int, float)) or not LIMITS[k][0] <= float(v) <= LIMITS[k][1]:
                return None                                    # NaN fails the comparison too
            out[k] = float(v)
    return out


def override_ids(net, ring) -> list:
    """ids of the authored overrides that put the key on these ring chains."""
    out = []
    for c in ring:
        for i in np.unique(c.sec_idx):
            oid = str(net.sec_list[int(i)].provenance.get("compact_roundabout", "")).split(":", 1)[-1]
            if oid and oid not in out:
                out.append(oid)
    return out


def kerb_mode(opts) -> bool:
    return "entry_r_m" in opts or "exit_r_m" in opts


def _fit_circle(pts):
    A = np.column_stack([2 * pts, np.ones(len(pts))])
    sol = np.linalg.lstsq(A, (pts ** 2).sum(1), rcond=None)[0]
    c = sol[:2]
    return c, float(math.sqrt(sol[2] + c @ c))


def _sec(net, c):
    return net.sec_list[int(c.sec_idx[0])]


def specs(net, junction_nodes=None) -> list:
    """Compact roundabouts of the network: connected groups of ring chains with the key on one of their sections."""
    from .network import ISLAND, TRUCK_APRON_CODE
    ring_chains = [c for c in net.chains if c.roundabout and not c.closed]
    flagged = [c for c in ring_chains if any(getattr(net.sec_list[int(i)], "compact", None) is not None
                                             for i in np.unique(c.sec_idx))]
    out, seen = [], set()
    for c0 in sorted(flagged, key=lambda c: c.id):
        if c0.id in seen:
            continue
        grp, nodes, grew = [c0], {c0.node_a, c0.node_b}, True
        while grew:
            grew = False
            for c in ring_chains:
                if c not in grp and (c.node_a in nodes or c.node_b in nodes):
                    grp.append(c)
                    nodes |= {c.node_a, c.node_b}
                    grew = True
        seen |= {c.id for c in grp}
        grp.sort(key=lambda c: c.id)
        opts = dict(DEFAULTS)
        for c in grp:
            for i in np.unique(c.sec_idx):
                o = getattr(net.sec_list[int(i)], "compact", None)
                if o:
                    opts.update(o)
        ring_nodes = set(nodes)
        feeders = []
        for c in net.chains:
            if c in grp or c.closed or c.roundabout:
                continue
            ina, inb = c.node_a in ring_nodes, c.node_b in ring_nodes
            if ina == inb or c.length > FEEDER_MAX_M or not bool((c.dirn != 0).all()):
                continue
            far = c.node_b if ina else c.node_a
            if junction_nodes is not None and far not in junction_nodes:
                continue
            feeders.append(c)
        feeders.sort(key=lambda c: c.id)
        for c in feeders:
            nodes.add(c.node_b if c.node_a in ring_nodes else c.node_a)
        ctr, r = _fit_circle(np.vstack([c.line.p for c in grp]))
        w = float(np.mean([2 * float(np.mean(c.hw)) for c in grp]))
        r_fit, notes = r, []
        if "outer_diameter_m" in opts:
            r_new = float(opts["outer_diameter_m"]) / 2 - w / 2
            if abs(r_new - r) <= max(OUTER_D_MIN_SHIFT_M, OUTER_D_MAX_SHIFT * r) and r_new - w / 2 >= RING_INNER_MIN_M + 0.2:
                r = r_new                       # reported as r_axis_m / r_axis_fit_m (report_one), not a note
            else:
                net.overrides_stale += [i for i in override_ids(net, grp) if i not in net.overrides_stale]
                notes.append(f"outer diameter {float(opts['outer_diameter_m']):.2f} m rejected (fitted axis r {r:.2f} m)")
                opts = {k: v for k, v in opts.items() if k != "outer_diameter_m"}
        ta = next((_sec(net, c).truck_apron for c in grp if _sec(net, c).truck_apron), None)
        if ta and ta.get("code"):
            ap = (ISLAND, float(ta["height_m"]), float(ta["width_m"]), ISLAND_SKIRT_M, int(ta["code"]))
        else:
            ap = (ISLAND, S.KERB_HEIGHT_APRON, float(ta["width_m"]) if ta else S.ROUNDABOUT_APRON_W, ISLAND_SKIRT_M,
                  TRUCK_APRON_CODE["kostka"])
        if r - w / 2 < RING_INNER_MIN_M + 0.2:
            # review s23 D18 P2-3: no room for an apron and an island - the generic machinery builds this ring
            net.overrides_stale += [i for i in override_ids(net, grp) if i not in net.overrides_stale]
            continue
        ap = (ap[0], ap[1], max(0.2, min(ap[2], r - w / 2 - 1.0)), ap[3], ap[4])       # at least 1 m of island inside
        if kerb_mode(opts):
            opts = {**KERB_DEFAULTS, **opts}
        out.append(Spec(id="cr:" + sorted(ring_nodes)[0], ring=grp, feeders=feeders, nodes=sorted(nodes), center=ctr,
                        r_axis=r, w_ring=w, apron=ap, opts=opts, notes=notes, r_axis_fit=r_fit))
    return out


LANE_ARC_STEP_M = 0.5
LANE_AXIS_MISS_M = 3.0       # an arm whose axis passes further from the ring centre keeps its mapped lanes
LANE_AXIS_AT_M = 14.0        # the arm axis is read off the pair of lanes this far outside the ring axis


def _arc(q, p0, p1, step=LANE_ARC_STEP_M):
    """Points of the shorter arc about q from p0 to p1 (p0 excluded)."""
    a0, a1 = math.atan2(*(p0 - q)[::-1]), math.atan2(*(p1 - q)[::-1])
    da = (a1 - a0 + math.pi) % (2 * math.pi) - math.pi
    r = float(np.hypot(*(p0 - q)))
    t = a0 + da * np.linspace(0.0, 1.0, max(2, int(abs(da) * r / step) + 2))[1:]
    return q + r * np.column_stack([np.cos(t), np.sin(t)])


def _reline_new(c, pts):
    """Give the chain a new centre line of another length: resampled to network.DENSE, the per-station arrays
    carried over by the fraction of the length (a feeder is one section, one direction)."""
    from .geom import Polyline, cumlen
    from .network import DENSE
    s_new = cumlen(pts)
    L = float(s_new[-1])
    n = max(2, int(round(L / DENSE)) + 1)
    t = np.linspace(0.0, L, n)
    q = np.column_stack([np.interp(t, s_new, pts[:, 0]), np.interp(t, s_new, pts[:, 1])])
    m = len(c.hw)
    j = np.clip(np.round(t / max(L, 1e-9) * (m - 1)).astype(int), 0, m - 1)
    c.hw = np.interp(t / max(L, 1e-9) * (m - 1), np.arange(m), c.hw)
    c.sec_idx, c.dirn, c.bridge = c.sec_idx[j], c.dirn[j], c.bridge[j]
    c.meta["rev"] = c.meta["rev"][j]
    if "center_offset" in c.meta:
        del c.meta["center_offset"]
    c.line = Polyline(q)


def lay_lanes(net) -> list:
    """ADR 0274 (kerb mode): the one-way lanes of every arm are laid as designed lanes instead of the mapped GPS
    traces. Seen along the arm axis (the middle line of the pair LANE_AXIS_AT_M outside the ring axis, straight
    from there to the ring) a lane keeps its mapped distance from the axis up to `splitter_w_m / 2 + lane_w_m / 2`, runs parallel to the axis at
    that distance and joins the ring axis with an arc of the kerb radius + half the lane (entry_r_m / exit_r_m: the
    kerb on the outside of the turn then has exactly that radius), then follows the ring axis to its mapped ring
    node - or, when that node lies before the point where the arc would touch the ring axis, an arc of the same
    radius runs from the lane line into the node. Further out than LANE_AXIS_AT_M the mapped / authored line stays.
    A lane that cannot be laid like that (axis misses the centre, no room for the arc) keeps its mapped line; the reason is returned and reported in the roundabout's notes.
    Idempotent (chain.meta["cr_lane"]); nothing happens for rings without the kerb-mode key."""
    notes = []
    for spec in specs(net):
        if not kerb_mode(spec.opts):
            continue
        o = spec.opts
        ring_nodes = {x for c in spec.ring for x in (c.node_a, c.node_b)}
        off = float(o["splitter_w_m"]) / 2 + float(o["lane_w_m"]) / 2
        by_far = {}
        for c in spec.feeders:
            by_far.setdefault(c.node_b if c.node_a in ring_nodes else c.node_a, []).append(c)
        for far in sorted(by_far):
            pair = by_far[far]
            if len(pair) != 2 or any(c.meta.get("cr_lane") for c in pair):
                continue
            # local axis of the arm near the ring: the middle line of the pair LANE_AXIS_AT_M outside the ring axis
            # (a long arm is not straight back to its split node)
            f = np.linspace(0.0, 1.0, 160)
            L2 = [c.line.point(f * c.length if c.node_a == far else (1.0 - f) * c.length) for c in pair]
            mid = (L2[0] + L2[1]) / 2
            k = int(np.argmax(np.hypot(*(mid - spec.center).T) <= spec.r_axis + LANE_AXIS_AT_M))
            S0 = mid[k]
            d = sum((q[min(k + 3, len(f) - 1)] - q[max(k - 3, 0)]) for q in L2)
            d = d / max(float(np.hypot(*d)), 1e-9)             # inward along the arm axis
            nl = np.array([-d[1], d[0]])
            xo, yo = float((spec.center - S0) @ d), float((spec.center - S0) @ nl)
            if abs(yo) > LANE_AXIS_MISS_M or xo <= 0:
                notes.append((spec.id, f"arm at {far}: axis passes {abs(yo):.1f} m from the ring centre, mapped lanes kept"))
                continue
            new = []
            for c in pair:
                P = c.line.p if c.node_a == far else c.line.p[::-1]       # split node -> ring node
                x, y = (P - S0) @ d, (P - S0) @ nl
                sg = 1.0 if y[-1] >= 0 else -1.0
                toward = 1 if c.node_b in ring_nodes else -1
                entry = int(c.dirn[len(c.dirn) // 2]) * toward > 0
                hw = float(np.mean(c.hw))
                rk = float(o["entry_r_m"] if entry else o["exit_r_m"])
                node = P[-1]
                if spec.r_axis_fit is not None and abs(spec.r_axis - spec.r_axis_fit) > 1e-6:
                    # authored outer diameter: the lane meets the ring axis on the authored circle, at the bearing of
                    # its mapped ring node (the ring chains themselves are absorbed, no ribbon is built from them)
                    rv = node - spec.center
                    node = spec.center + rv * (spec.r_axis / max(float(np.hypot(*rv)), 1e-9))
                xn, yn = float((node - S0) @ d), float((node - S0) @ nl)
                a_node = math.atan2(*(node - spec.center)[::-1])
                i0 = int(np.argmax(x >= 0.0))                  # mapped / authored line up to the local axis origin
                pts = None
                for rc in (rk + hw, 0.8 * rk + hw, 0.6 * rk + hw):
                    yq = sg * (off + rc)
                    tail = None
                    disc_ = (spec.r_axis + rc) ** 2 - (yq - yo) ** 2
                    if disc_ > 0:
                        xq = xo - math.sqrt(disc_)
                        q = S0 + d * xq + nl * yq
                        t_ring = spec.center + (q - spec.center) * spec.r_axis / (spec.r_axis + rc)
                        a_t = math.atan2(*(t_ring - spec.center)[::-1])
                        # counter-clockwise ring: an entry meets the ring before its node, an exit after it
                        da = (a_node - a_t) % (2 * math.pi) if entry else (a_t - a_node) % (2 * math.pi)
                        if da <= math.pi / 2:
                            ang = a_t + (1.0 if entry else -1.0) * da * np.linspace(
                                0.0, 1.0, max(2, int(da * spec.r_axis / LANE_ARC_STEP_M) + 2))[1:]
                            ring_arc = spec.center + spec.r_axis * np.column_stack([np.cos(ang), np.sin(ang)])
                            ring_arc[-1] = node
                            tail = np.vstack([_arc(q, S0 + d * xq + nl * sg * off, t_ring), ring_arc])
                    if tail is None and rc ** 2 - (yn - yq) ** 2 > 0:
                        # the mapped ring node lies before the point where the arc would touch the ring axis: the
                        # arc of the same radius runs from the lane line straight into the node
                        xq = xn - math.sqrt(rc ** 2 - (yn - yq) ** 2)
                        q = S0 + d * xq + nl * yq
                        tail = _arc(q, S0 + d * xq + nl * sg * off, node)
                    keep = (x >= 0.0) & (x < xq - 0.25) & (np.arange(len(x)) >= i0)
                    if tail is None or xq < 0.5:
                        continue
                    head = S0 + np.outer(x[keep], d) + np.outer(sg * np.minimum(np.abs(y[keep]), off), nl)
                    pts = np.vstack([P[:i0], head, S0 + d * xq + nl * sg * off, tail])
                    break
                if pts is None and abs(yn) <= off + 0.05:
                    # the ring node itself lies inside the designed lane line: the mapped line, held within it
                    keep = np.arange(len(x)) >= i0
                    pts = np.vstack([P[:i0], S0 + np.outer(x[keep], d) + np.outer(sg * np.minimum(np.abs(y[keep]), off), nl)])
                    pts[-1] = node
                if pts is None:
                    notes.append((spec.id, f"lane {c.id}: no room for the designed lane, mapped line kept"))
                    new = None
                    break
                new.append((c, pts if c.node_a == far else pts[::-1]))
            for c, pts in new or []:
                _reline_new(c, pts)
                c.meta["cr_lane"] = True
    net.cr_lane_notes = getattr(net, "cr_lane_notes", []) + notes
    return notes


def _ribbon(c, s0=None, s1=None, n=None):
    s0 = 0.0 if s0 is None else s0
    s1 = c.length if s1 is None else s1
    n = n or max(8, int(math.ceil((s1 - s0) / 0.5)) + 1)
    s = np.linspace(s0, s1, n)
    hw = c.hw_at(s)
    return Polygon(np.vstack([c.line.offset_point(s, hw), c.line.offset_point(s, -hw)[::-1]])).buffer(0)


def _corner_points(ext, k0, k1, p0, p1, direction):
    """Outline vertices k0 .. k1 (counter-clockwise, wrapping) as the polyline of one corner, with its ends put on
    the gutter points p0 / p1 and vertices closer than 0.25 m dropped. Always >= 2 distinct points (review s23 D18
    P2-4: k0 == k1 - two arms meeting in one outline vertex - gave one point and np.gradient raised, aborting
    build_world); returns (points, True) when the corner had to be made up."""
    m = len(ext)
    seq, k = [k0], k0
    while k != k1 and len(seq) <= m:
        k = (k + 1) % m
        seq.append(k)
    pts = ext[seq].copy()
    touch = len(pts) < 2
    if touch:
        pts = np.vstack([pts[0], pts[0]])
    pts[0], pts[-1] = p0, p1
    keep = [0]
    for q in range(1, len(pts) - 1):
        if np.hypot(*(pts[q] - pts[keep[-1]])) >= 0.25 and np.hypot(*(pts[q] - pts[-1])) >= 0.25:
            keep.append(q)
    keep.append(len(pts) - 1)
    pts = pts[keep]
    if np.hypot(*(pts[-1] - pts[0])) < 1e-6:
        pts = np.vstack([pts[0], pts[0] + np.asarray(direction, float) * 0.01])
        touch = True
    return pts, touch


def _on_boundary(pg, p, tol=0.03):
    return pg.exterior.distance(Point(*p)) < tol


def corners(net, j, spec: Spec, max_trim=None):
    """(corners, trims) of the one junction of a compact roundabout; sets spec.outline / spec.splitters."""
    from .junctions import Corner
    arms, n = j.arms, len(j.arms)
    rc = float(spec.opts["closing_r_m"])
    disc = Point(*spec.center).buffer(spec.r_out, 96)
    ribs = [_ribbon(c) for c in spec.feeders]
    stubs, dmax = [], []
    for a in arms:
        dm = float(min(a.L - 0.5, STUB_MAX_M, (max_trim or {}).get(len(stubs), 1e9) + 1.5))
        d = np.linspace(0.0, dm, max(4, int(dm / 0.5) + 1))
        stubs.append(Polygon(np.vstack([a.gutter(d, +1), a.gutter(d, -1)[::-1]])).buffer(0))
        dmax.append(dm)
    if kerb_mode(spec.opts):
        closed = _kerb_outline(net, spec, arms, disc, stubs)
    else:
        raw = shapely.union_all([disc] + ribs + stubs)
        closed = raw.buffer(rc, 32).buffer(-rc, 32)
    closed = max(getattr(closed, "geoms", [closed]), key=lambda g: g.area)
    paved = Polygon(closed.exterior)
    trims = {}
    for i, a in enumerate(arms):
        t = None
        for cand in np.arange(1.0, dmax[i] - 1.5, 0.5):
            if all(_on_boundary(paved, a.gutter(dd, sd)) for dd in (cand, cand + 1.0) for sd in (+1, -1)):
                t = float(cand)
                break
        if t is None:
            t = max(0.5, dmax[i] - 2.0)
            spec.notes.append(f"arm {a.chain.id}: outline does not join the arm gutters, trim {t:.1f} m")
        trims[i] = t
    for i, a in enumerate(arms):
        t = trims[i]
        pr, pl, dv = a.gutter(t, -1), a.gutter(t, +1), a.direction(t)
        lat = (pl - pr) / max(float(np.hypot(*(pl - pr))), 1e-9)
        q = [pr - lat * 1.0, pl + lat * 1.0, pl + lat * 1.0 + dv * 80.0, pr - lat * 1.0 + dv * 80.0]
        cut = Polygon(q)
        # the cut line passes exactly through the two gutter points: make them vertices of the outline
        paved = paved.difference(cut)
        paved = max(getattr(paved, "geoms", [paved]), key=lambda g: g.area)
    paved = shapely.segmentize(Polygon(paved.exterior), 1.0)
    ext = np.asarray(paved.exterior.coords)[:-1]
    if not paved.exterior.is_ccw:
        ext = ext[::-1]

    def nearest(p):
        d = np.hypot(*(ext - p).T)
        k = int(np.argmin(d))
        return k, float(d[k])

    idxL, idxR = {}, {}
    for i, a in enumerate(arms):
        idxL[i], dl = nearest(a.gutter(trims[i], +1))
        idxR[i], dr = nearest(a.gutter(trims[i], -1))
        if max(dl, dr) > 0.05:
            spec.notes.append(f"arm {a.chain.id}: end section {max(dl, dr):.2f} m off the outline")
    cs = []
    m = len(ext)
    for i in range(n):
        i1 = (i + 1) % n
        pts, touch = _corner_points(ext, idxL[i], idxR[i1], arms[i].gutter(trims[i], +1), arms[i1].gutter(trims[i1], -1),
                                    arms[i].direction(trims[i]))
        if touch:
            spec.notes.append(f"corner {arms[i].chain.id} -> {arms[i1].chain.id}: arms touch on the outline")
        tg = np.gradient(pts, axis=0)
        tg /= np.maximum(np.hypot(*tg.T), 1e-9)[:, None]
        out = np.column_stack([tg[:, 1], -tg[:, 0]])          # CCW boundary: outside is to the right of travel
        cs.append(Corner(kind="fillet", k=i, k1=i1, R=rc, center=None, tau_k=trims[i], tau_k1=trims[i1], arc=pts,
                         out=out))
    spec.outline = paved
    spec.splitters = _splitters(net, spec, paved)
    if kerb_mode(spec.opts):
        _plan_crossings(net, spec, arms)
    return cs, trims


def _legs(spec: Spec, n=80):
    """{split node: (the two feeders, their axes sampled from the split node (row 0) to the ring (row n - 1))}."""
    ring_nodes = {x for c in spec.ring for x in (c.node_a, c.node_b)}
    by_far = {}
    for c in spec.feeders:
        far = c.node_b if c.node_a in ring_nodes else c.node_a
        by_far.setdefault(far, []).append(c)
    f = np.linspace(0.0, 1.0, n)
    out = {}
    for far in sorted(by_far):
        pair = by_far[far]
        if len(pair) != 2:
            continue
        legs = []
        for c in pair:
            sv = f * c.length if c.node_a == far else (1.0 - f) * c.length
            legs.append(c.line.point(sv))
        out[far] = (pair, legs)
    return out


def _kerb_outline(net, spec: Spec, arms, disc, stubs):
    """ADR 0274: paved area = ring disc + the designed lanes (lay_lanes, full width) + the arm ends; sets
    spec.mouths (middle line and half width of every pair of lanes, split node -> ring)."""
    legs = _legs(spec)
    spec.mouths, strips = {}, []
    for a in arms:
        if a.node not in legs:
            continue
        pair, (l0, l1) = legs[a.node]
        hw_f = float(np.mean([np.mean(c.hw) for c in pair]))
        mid, half = (l0 + l1) / 2, np.hypot(*(l0 - l1).T) / 2 + hw_f
        spec.mouths[a.node] = {"mid": mid, "half_w": half}
        # at the split node the two lanes lie on each other: the carriageway is never narrower than the arm (or than
        # the mouth at its widest, where the arm is wider than that: it then narrows 1 : MOUTH_TAPER per side)
        hw_arm = float(a.chain.hw_at(a.s(0.0)))
        dist = np.concatenate([[0.0], np.cumsum(np.hypot(*np.diff(mid, axis=0).T))])
        w = np.maximum(half, np.maximum(min(hw_arm, float(half.max())), hw_arm - dist / MOUTH_TAPER))
        k = int(np.argmax(w <= half + 1e-9)) if (w <= half + 1e-9).any() else len(half) - 1
        if k >= 1:
            sl = slice(0, min(k + 2, len(mid)))
            tg = np.gradient(mid[sl], axis=0)
            tg /= np.maximum(np.hypot(*tg.T), 1e-9)[:, None]
            nl = np.column_stack([-tg[:, 1], tg[:, 0]])
            strips.append(Polygon(np.vstack([mid[sl] + nl * w[sl, None], (mid[sl] - nl * w[sl, None])[::-1]])).buffer(0))
    spec.notes += [t for sid, t in getattr(net, "cr_lane_notes", []) if sid == spec.id and t not in spec.notes]
    raw = shapely.union_all([disc] + list(stubs) + strips + [_ribbon(c) for c in spec.feeders])
    # the kerb radii are in the lanes already (lay_lanes); what is left are the cusps where the returns of two
    # neighbouring arms meet before the ring kerb and the slivers where a return runs into the ring disc
    out = raw.buffer(NOSE_R_M, 32).buffer(-NOSE_R_M, 32)
    return out.buffer(-1.0, 16).buffer(1.0, 16)              # nubs: corners of ribbons proud of a return


def _splitters(net, spec: Spec, paved):
    """Splitter islands: what is left between the entry and the exit of one arm when a lane `lane_w_m` wide is kept
    clear along the outer kerb (and `lane_clear_m` about each feeder axis), at most `splitter_w_m` wide about the
    middle line, from `splitter_gap_m` outside the ring to where it gets narrower than SPLITTER_MIN_W."""
    all_legs = _legs(spec, 60)
    wmax, gap = float(spec.opts["splitter_w_m"]), float(spec.opts["splitter_gap_m"])
    lane = paved.exterior.buffer(float(spec.opts["lane_w_m"]), 16)
    keep_out = shapely.union_all([LineString(c.line.p).buffer(float(spec.opts["lane_clear_m"]), 8)
                                  for c in spec.feeders] + [lane, Point(*spec.center).buffer(spec.r_out + gap, 96)])
    out = []
    for far in sorted(all_legs):
        _pair, legs = all_legs[far]          # both legs from the split node (row 0) to the ring (last row)
        between = Polygon(np.vstack([legs[0], legs[1][::-1]])).buffer(0)
        mid = LineString((legs[0] + legs[1]) / 2)
        g = between.difference(keep_out).intersection(mid.buffer(wmax / 2, 16))
        g = g.buffer(-SPLITTER_MIN_W / 2, 8).buffer(SPLITTER_MIN_W / 2, 8)
        parts = [p for p in getattr(g, "geoms", [g]) if p.geom_type == "Polygon" and p.area >= SPLITTER_MIN_M2]
        if not parts:
            spec.notes.append(f"no splitter island at {far} (gap too narrow)")
            continue
        pg = max(parts, key=lambda p: p.area)
        out.append((f"{spec.id}:splitter:{far}", Polygon(pg.exterior).simplify(0.03)))
    return out


MOUTH_TAPER = 5.0            # WORKING_VALUE: the arm narrows to its two lanes 1 : 5 per side behind the split node
NOSE_R_M = 4.0               # WORKING_VALUE: kerb nose between two returns that meet before the ring kerb
P13_INSET_M = 0.15           # WORKING_VALUE: bases of the P-13 triangles this far outside the ring carriageway edge
P13_SIDE_M = 0.30            # WORKING_VALUE: P-13 / P-10 end this far from a kerb face
P13_MIN_M = 1.5


def _arm_way(net, a) -> int | None:
    try:
        return int(str(a.chain.section(a.s(min(1.0, a.L / 2)), net.sec_list).edge_id).split(":")[0].lstrip("w"))
    except (AttributeError, IndexError, ValueError):
        return None


def _plan_crossings(net, spec: Spec, arms):
    """ADR 0274: P-10 across the lanes of the arms listed in `crossings` (the splitter is cut through: a refuge at
    road level) and P-13 across every entry lane along the edge of the ring carriageway."""
    from . import standards as S_
    o = spec.opts
    ways = set(o.get("crossings") or [])
    ring_nodes = {x for c in spec.ring for x in (c.node_a, c.node_b)}
    legs = _legs(spec)
    uncut = shapely.union_all([pg for _, pg in spec.splitters]) if spec.splitters else Polygon()
    spec.crossings, spec.p13 = [], []
    found = set()
    for a in arms:
        m = spec.mouths.get(a.node)
        if m is None:
            continue
        mid = m["mid"][::-1]                                  # from the ring outwards
        r = np.hypot(*(mid - spec.center).T)
        way = _arm_way(net, a)
        if way in ways:
            found.add(way)
            rc = spec.r_out + float(o["crossing_offset_m"]) + S_.P10_WIDTH / 2
            k = int(np.argmax(r >= rc))
            if r[k] < rc or k == 0 or r[-1] < rc + S_.P10_WIDTH / 2 + 0.5:
                spec.notes.append(f"arm {a.chain.id}: no room for the crossing {o['crossing_offset_m']:.1f} m off the ring")
            else:
                w = (rc - r[k - 1]) / max(r[k] - r[k - 1], 1e-9)
                c0 = mid[k - 1] + w * (mid[k] - mid[k - 1])
                t = mid[min(k + 3, len(mid) - 1)] - mid[max(k - 4, 0)]
                t /= max(float(np.hypot(*t)), 1e-9)
                nrm = np.array([-t[1], t[0]])
                reach = float(m["half_w"].max()) + 1.0
                h = S_.P10_WIDTH / 2
                band = Polygon([c0 - t * h - nrm * reach, c0 + t * h - nrm * reach, c0 + t * h + nrm * reach,
                                c0 - t * h + nrm * reach])
                # lanes: what all three lines across the band (near edge, middle, far edge) have in common - the kerb
                # returns and the island nose curve inside the 4 m of the crossing
                free = spec.outline.difference(uncut)
                spans = {}
                for dt in (-h, 0.0, h):
                    cut_ = LineString([c0 + t * dt - nrm * reach, c0 + t * dt + nrm * reach]).intersection(free)
                    seen = set()
                    for seg in getattr(cut_, "geoms", [cut_]):
                        if seg.geom_type != "LineString" or seg.length < 1.0:
                            continue
                        la = np.sort((np.asarray(seg.coords) - c0) @ nrm)
                        # no island on this line (beyond its tail): both lanes, up to the middle line
                        both = la[0] < -0.5 and la[-1] > 0.5
                        for sd, lo_, hi_ in ((-1, la[0], 0.0), (1, 0.0, la[-1])) if both else (
                                (1 if 0.5 * (la[0] + la[-1]) > 0 else -1, la[0], la[-1]),):
                            if sd not in seen:
                                seen.add(sd)
                                spans.setdefault(sd, []).append((lo_, hi_))
                stripes, lanes = [], []
                for sd in sorted(spans):
                    if len(spans[sd]) != 3:
                        continue
                    la = (max(v[0] for v in spans[sd]), min(v[1] for v in spans[sd]))
                    if la[-1] - la[0] < 2 * P13_SIDE_M + 2 * S_.P10_STRIPE:
                        continue
                    lo, hi = la[0] + P13_SIDE_M, la[-1] - P13_SIDE_M
                    nb = int(math.floor((hi - lo + S_.P10_GAP) / (S_.P10_STRIPE + S_.P10_GAP)))
                    if nb < 2:
                        continue
                    x0 = (lo + hi) / 2 - (nb * S_.P10_STRIPE + (nb - 1) * S_.P10_GAP) / 2
                    lanes.append([round(float(la[0]), 2), round(float(la[-1]), 2)])
                    for b in range(nb):
                        xa = x0 + b * (S_.P10_STRIPE + S_.P10_GAP)
                        stripes.append(Polygon([c0 - t * h + nrm * xa, c0 + t * h + nrm * xa,
                                                c0 + t * h + nrm * (xa + S_.P10_STRIPE), c0 - t * h + nrm * (xa + S_.P10_STRIPE)]))
                if stripes:
                    cut = []
                    for sid, pg in spec.splitters:
                        if not pg.intersects(band):
                            cut.append((sid, pg))
                            continue
                        rest = pg.difference(band)
                        pieces = sorted((g for g in getattr(rest, "geoms", [rest])
                                         if g.geom_type == "Polygon" and g.area >= SPLITTER_MIN_M2),
                                        key=lambda g: g.distance(Point(*spec.center)))
                        cut += [(f"{sid}:{chr(97 + n)}", g) for n, g in enumerate(pieces)]
                    spec.splitters = cut
                    spec.crossings.append({"arm": a.chain.id, "osm_way": way, "center": c0, "dir": t, "stripes": stripes,
                                           "lanes_lat_m": lanes, "band": band,
                                           "near_edge_from_ring_m": round(float(np.hypot(*(c0 - spec.center)) - h - spec.r_out), 2)})
                else:
                    spec.notes.append(f"arm {a.chain.id}: crossing has no lane to cross")
        # P-13: the entry lane is on the side of the feeder that runs towards the ring
        pair, (l0, l1) = legs[a.node]
        side = 1.0
        for c, leg in zip(pair, (l0, l1)):
            toward = 1 if c.node_b in ring_nodes else -1
            if int(c.dirn[len(c.dirn) // 2]) * toward > 0:
                u = mid[0] - spec.center
                side = 1.0 if float(u[0] * (leg[-1] - mid[0])[1] - u[1] * (leg[-1] - mid[0])[0]) >= 0 else -1.0
        k = int(np.argmax(r >= spec.r_out + 1.0))
        phi = math.atan2(*(mid[k] - spec.center)[::-1])
        rp = spec.r_out + P13_INSET_M
        lane_ok = spec.outline.buffer(-P13_SIDE_M).difference(shapely.union_all([pg for _, pg in spec.splitters] + [Polygon()]).buffer(P13_SIDE_M))
        shapely.prepare(lane_ok)
        th = phi + side * np.radians(np.arange(0.0, 75.0, 0.25))
        cs_ = np.column_stack([np.cos(th), np.sin(th)])
        # ... and no further from the middle line than the mouth is wide (a return may leave asphalt along the ring)
        u_out = mid[min(k + 4, len(mid) - 1)] - mid[k]
        u_out /= max(float(np.hypot(*u_out)), 1e-9)
        lat = ((spec.center + rp * cs_) - mid[k]) @ np.array([-u_out[1], u_out[0]])
        ok = np.abs(lat) <= float(m["half_w"][::-1][k]) + 0.5
        for rr in (rp + 0.05, rp + 0.4, rp + 0.75, spec.r_out + 1.3):
            pt = spec.center + rr * cs_
            ok &= shapely.contains_xy(lane_ok, pt[:, 0], pt[:, 1])
        if ok.any():
            i0 = int(np.argmax(ok))
            i1 = i0
            while i1 + 1 < len(ok) and ok[i1 + 1]:
                i1 += 1
            Q = spec.center + rp * cs_[i0:i1 + 1]
            if side < 0:
                Q = Q[::-1]                                   # drawn counter-clockwise: tips point outwards
            if float(np.sum(np.hypot(*np.diff(Q, axis=0).T))) >= P13_MIN_M:
                spec.p13.append((a.chain.id, Q))
                continue
        spec.notes.append(f"arm {a.chain.id}: no entry lane found for P-13")
    for w in sorted(ways - found):
        spec.notes.append(f"crossings: way {w} is not an arm of this roundabout")


def build_markings(buf, net, juncs, report=None) -> dict:
    """P-10 / P-13 of the kerb-mode compact roundabouts, draped on the junction patch (decals, markings layer)."""
    from .authored_paint import _drape_polygon, _p13_row
    from .through_lines import _Top
    top, rep = None, {"P-10": 0, "P-13": 0, "tris": 0, "tris_off_carriageway": 0}
    for j in juncs:
        spec = getattr(j, "compact", None)
        if spec is None or not kerb_mode(spec.opts):
            continue
        top = top or _Top(buf.parts)
        for cr in spec.crossings:
            for g in cr["stripes"]:
                n, lost = _drape_polygon(buf, top, g, f"P-10@{spec.id}:{cr['arm']}", 2.0)
                rep["tris"] += n
                rep["tris_off_carriageway"] += lost
            rep["P-10"] += 1
        for cid, Q in spec.p13:
            for tri in _p13_row(Q):
                n, lost = _drape_polygon(buf, top, tri, f"P-13@{spec.id}:{cid}", 2.0)
                rep["tris"] += n
                rep["tris_off_carriageway"] += lost
            rep["P-13"] += 1
    if report is not None and (rep["P-10"] or rep["P-13"]):
        report["compact_roundabout_markings"] = rep
    return rep


FILL_RIM_BAND_M = 0.25       # the kerb line's own unevenness fades over this band; inside it the fill is smooth
FILL_RING_M = 0.7            # radial pitch of the rings
FILL_SEG_M = 0.6             # arc length of a ring segment (never more segments than the kerb line has)
FILL_HARMONICS = 2           # of the kerb line's deviation from its plane that reach into the fill (tilt + saddle)


def island_fill_mesh(center, r0, z_rim, dz_top=0.0):
    """ADR 0274: top of the centre island as concentric rings. `z_rim` = heights of the kerb line at len(z_rim) equal
    angles (ring 0, kept exactly: watertight against the kerb). Inside, the height is the plane fitted to the kerb
    line plus the first FILL_HARMONICS angular harmonics of its deviation, fading with (r / r0)^2 - the old fill copied
    every sample's own deviation along its radius (spokes: radial shading in render r3) and closed the centre with a
    fan of one sliver per kerb sample. Segment counts fall with the radius; the centre is a fan of 8.
    Returns (V (n, 3), T (m, 3) counter-clockwise from above)."""
    center = np.asarray(center, float)
    z_rim = np.asarray(z_rim, float)
    n = len(z_rim)
    ang = np.arange(n) * 2 * math.pi / n
    cs_ = np.column_stack([np.cos(ang), np.sin(ang)])
    pl = np.linalg.lstsq(np.column_stack([r0 * cs_, np.ones(n)]), z_rim, rcond=None)[0]
    dev = z_rim - (r0 * cs_) @ pl[:2] - pl[2]
    F = np.fft.rfft(dev)
    F[FILL_HARMONICS + 1:] = 0.0
    F[0] = 0.0

    def height(r, a):
        k = np.arange(1, FILL_HARMONICS + 1)
        low = (2.0 / n) * np.real(F[1:FILL_HARMONICS + 1][None, :] * np.exp(1j * np.outer(a, k))).sum(1) if n > 2 * FILL_HARMONICS else 0.0
        return r * (np.cos(a) * pl[0] + np.sin(a) * pl[1]) + pl[2] + low * (r / r0) ** 2 + dz_top

    radii, counts = [r0], [n]
    r = r0 - FILL_RIM_BAND_M
    if r > 0.3:
        radii.append(r)
        counts.append(n)
        r -= FILL_RING_M
        while r > 0.75:
            radii.append(r)
            counts.append(int(min(n, max(8, round(2 * math.pi * r / FILL_SEG_M)))))
            r -= FILL_RING_M
    for k in range(1, len(counts)):                           # a ring has at least half the segments of the one outside
        counts[k] = max(counts[k], -(-counts[k - 1] // 2))
    while counts[-1] > 8:                                     # ... down to 8 around the centre vertex
        radii.append(radii[-1] * 0.6)
        counts.append(max(8, -(-counts[-1] // 2)))
    V, start = [], []
    for k, (rr, m) in enumerate(zip(radii, counts)):
        a = np.arange(m) * 2 * math.pi / m
        z = z_rim + dz_top if k == 0 else height(rr, a)
        start.append(sum(len(v) for v in V))
        V.append(np.column_stack([center[0] + rr * np.cos(a), center[1] + rr * np.sin(a), z]))
    cidx = sum(len(v) for v in V)
    V.append(np.array([[center[0], center[1], float(pl[2]) + dz_top]]))
    T = []
    for k in range(len(radii) - 1):
        na, nb, a0, b0 = counts[k], counts[k + 1], start[k], start[k + 1]
        i = jb = 0
        while i < na or jb < nb:                              # zip the two rings by angle
            ta, tb = (i + 0.5) / na, (jb + 0.5) / nb
            if jb >= nb or (i < na and ta <= tb):
                T.append((a0 + i % na, a0 + (i + 1) % na, b0 + jb % nb))
                i += 1
            else:
                T.append((a0 + i % na, b0 + (jb + 1) % nb, b0 + jb % nb))
                jb += 1
    m, b0 = counts[-1], start[-1]
    T += [(b0 + i, b0 + (i + 1) % m, cidx) for i in range(m)]
    return np.vstack(V), np.array(T)


def plan_islands(net, juncs, gp):
    """Splitter islands of the compact roundabouts as kerbed traffic islands of the gore plan."""
    from .gores import Island
    for j in juncs:
        spec = getattr(j, "compact", None)
        if spec is None:
            continue
        for sid, pg in spec.splitters:
            gp.islands.append(Island(sid, pg, "sidewalk_paving"))


def build(buf, net, juncs) -> list:
    """Centre islands (truck apron annulus + island kerb + fill) on the patches of the compact roundabouts."""
    from . import meshing as M
    from .gores import _MeshSurface
    from .network import side_profile
    rep = []
    todo = [j for j in juncs if getattr(j, "compact", None) is not None]
    if not todo:
        return rep
    ms = _MeshSurface(buf.parts)
    for j in todo:
        spec = j.compact
        ri = spec.r_in
        n = max(48, int(math.ceil(2 * math.pi * ri / RING_STEP_M)))
        ang = np.linspace(0.0, 2 * math.pi, n + 1)
        ang[-1] = 0.0
        cs_ = np.column_stack([np.cos(ang), np.sin(ang)])
        G = spec.center + ri * cs_
        OUT = -cs_
        z = [ms.z(p, None, reach=1.5) for p in G[:-1]]
        if any(v is None for v in z):
            spec.notes.append("no patch surface under the island")
            rep.append(report_one(spec, built=False))
            continue
        zg = np.array(z + [z[0]])
        _sink_under_island(buf, j, spec)
        params = [spec.apron] * (n + 1)
        kap = np.full(n + 1, 1.0 / ri)
        src = f"island:{spec.id}"
        for coarse in (False, True):
            M._emit_strip(buf, G, OUT, zg, params, kap, np.zeros(n + 1), False, None, coarse, src + ":apron")
        prof = side_profile(*spec.apron)
        u_in, dz_top = prof[-1][0], prof[-2][3]            # inner edge of the kerb top band, kerb top above the gutter
        r0 = ri - u_in
        # review s23 D18 P2-2 + ADR 0274 (c): one mesher for both modes - no duplicated ring at an integer r0, no
        # sliver fan, no spokes (island_fill_mesh)
        V, T = island_fill_mesh(spec.center, r0, zg[:-1], dz_top)
        fill = str(spec.opts["island_fill"])
        COL = None
        if fill == "island_gravel":
            COL = np.zeros((len(V), 4))
            COL[:, 0] = 0.3                                   # light grime: a new roundabout (owner photo 9)
        buf.add("road", fill, V, V[:, :2].copy(), T, src=src + ":fill", COL=COL)
        buf.add("collision", "collision_grass" if fill == "verge_grass" else "collision_paving", V, V[:, :2].copy(),
                T, src=src + ":fill")
        rep.append(report_one(spec, built=True))
    return rep


SINK_M = 0.25                # asphalt of the patch under the island is lowered by this much (hidden bowl)
SINK_EDGE_M = 0.05           # ... inside this distance from the apron lip


def _sink_under_island(buf, j, spec: Spec):
    """The patch keeps running under the centre island (terrain footprint, watertight collision), but a tilted or
    warped patch surface must not come up through the apron (lip 4 cm + 2 %): its triangles are cut on the circle
    of the apron lip and everything inside is lowered by SINK_M. The surface outside the lip does not move."""
    from .aprons import _Acc, _tris_of
    from .meshing import Part
    r = spec.r_in - SINK_EDGE_M
    disc = Point(*spec.center).buffer(r, 96)
    shapely.prepare(disc)
    new_parts = []
    for p in buf.parts:
        if p.src != j.id or p.layer not in ("road", "collision") or not len(p.T):
            continue
        if not (p.mat.startswith("road_") or p.mat == "collision_asphalt"):
            continue
        tri2 = p.V[p.T][:, :, :2]
        rr = np.hypot(*(tri2 - spec.center).transpose(2, 0, 1))
        near = rr.min(1) < r + 0.01
        if not near.any():
            continue
        inside = _Acc()
        outside = _Acc()
        drop = np.zeros(len(p.T), bool)
        for k in np.where(near)[0]:
            tp = Polygon(tri2[k])
            if tp.area < 1e-8:
                continue
            if rr[k].max() <= r:
                inside.add(p, k, tri2[k])
                drop[k] = True
                continue
            cut = tp.intersection(disc)
            if cut.area < 1e-5:
                continue
            for t in _tris_of(cut):
                inside.add(p, k, t)
            for t in _tris_of(tp.difference(disc)):
                outside.add(p, k, t)
            drop[k] = True
        if not drop.any():
            continue
        p.T = p.T[~drop]
        for acc, sink in ((outside, False), (inside, True)):
            if not acc.V:
                continue
            V, UV, UV1, COL, T = acc.arrays()
            if sink:
                V = V.copy()
                V[np.hypot(*(V[:, :2] - spec.center).T) < r - 0.02, 2] -= SINK_M
            new_parts.append(Part(p.layer, p.mat, V, UV, T, p.footprint, p.src, UV1, COL))
    buf.parts[:] = [p for p in buf.parts if len(p.T)] + new_parts


def report_one(spec: Spec, built=True) -> dict:
    return {"id": spec.id, "built": built, "center_en": [round(float(v), 2) for v in spec.center],
            "r_axis_m": round(spec.r_axis, 2), "ring_asphalt_m": round(spec.w_ring, 2),
            "r_outer_m": round(spec.r_out, 2),
            "r_axis_fit_m": round(spec.r_axis_fit if spec.r_axis_fit is not None else spec.r_axis, 2), "apron_m": round(spec.apron[2], 2), "apron_lip_m": round(spec.apron[1], 3),
            "island_r_m": round(spec.r_in - spec.apron[2], 2), "splitters": len(spec.splitters),
            "splitter_m2": [round(pg.area, 1) for _, pg in spec.splitters],
            "outline_m2": round(spec.outline.area, 1) if spec.outline is not None else None,
            "ring_chains": len(spec.ring), "feeders": len(spec.feeders), "notes": list(spec.notes),
            "mode": "kerbs" if kerb_mode(spec.opts) else "closing",
            "splitter_len_m": [round(_long_side(pg), 1) for _, pg in spec.splitters],
            "crossings": [{"arm": c["arm"], "near_edge_from_ring_m": c["near_edge_from_ring_m"],
                           "stripes": len(c["stripes"])} for c in spec.crossings],
            "p13_entries": len(spec.p13)}


def _long_side(pg) -> float:
    e = np.hypot(*np.diff(np.asarray(pg.minimum_rotated_rectangle.exterior.coords)[:3], axis=0).T)
    return float(max(e))
