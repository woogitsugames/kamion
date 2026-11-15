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
            "island_fill": "island_gravel"}
FEEDER_MAX_M = 60.0          # one-way carriageway between the ring and its split node (Knyszyn: 16.7-29.9 m)
SPLITTER_MIN_M2 = 3.0        # WORKING_VALUE: smaller splitters are left as asphalt
SPLITTER_MIN_W = 0.8         # WORKING_VALUE: narrower tips of a splitter are cut (kerb 2 x 0.15 + top)
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

    @property
    def r_out(self):
        return self.r_axis + self.w_ring / 2

    @property
    def r_in(self):
        return self.r_axis - self.w_ring / 2


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
        ta = next((_sec(net, c).truck_apron for c in grp if _sec(net, c).truck_apron), None)
        if ta and ta.get("code"):
            ap = (ISLAND, float(ta["height_m"]), float(ta["width_m"]), ISLAND_SKIRT_M, int(ta["code"]))
        else:
            ap = (ISLAND, S.KERB_HEIGHT_APRON, float(ta["width_m"]) if ta else S.ROUNDABOUT_APRON_W, ISLAND_SKIRT_M,
                  TRUCK_APRON_CODE["kostka"])
        ap = (ap[0], ap[1], min(ap[2], r - w / 2 - 1.0), ap[3], ap[4])       # at least 1 m of island inside
        out.append(Spec(id="cr:" + sorted(ring_nodes)[0], ring=grp, feeders=feeders, nodes=sorted(nodes), center=ctr,
                        r_axis=r, w_ring=w, apron=ap, opts=opts))
    return out


def _ribbon(c, s0=None, s1=None, n=None):
    s0 = 0.0 if s0 is None else s0
    s1 = c.length if s1 is None else s1
    n = n or max(8, int(math.ceil((s1 - s0) / 0.5)) + 1)
    s = np.linspace(s0, s1, n)
    hw = c.hw_at(s)
    return Polygon(np.vstack([c.line.offset_point(s, hw), c.line.offset_point(s, -hw)[::-1]])).buffer(0)


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
        k0, k1 = idxL[i], idxR[i1]
        seq = [k0]
        k = k0
        while k != k1 and len(seq) <= m:
            k = (k + 1) % m
            seq.append(k)
        pts = ext[seq].copy()
        pts[0], pts[-1] = arms[i].gutter(trims[i], +1), arms[i1].gutter(trims[i1], -1)
        keep = [0]
        for q in range(1, len(pts) - 1):
            if np.hypot(*(pts[q] - pts[keep[-1]])) >= 0.25 and np.hypot(*(pts[q] - pts[-1])) >= 0.25:
                keep.append(q)
        keep.append(len(pts) - 1)
        pts = pts[keep]
        tg = np.gradient(pts, axis=0)
        tg /= np.maximum(np.hypot(*tg.T), 1e-9)[:, None]
        out = np.column_stack([tg[:, 1], -tg[:, 0]])          # CCW boundary: outside is to the right of travel
        cs.append(Corner(kind="fillet", k=i, k1=i1, R=rc, center=None, tau_k=trims[i], tau_k1=trims[i1], arc=pts,
                         out=out))
    spec.outline = paved
    spec.splitters = _splitters(net, spec, ribs)
    return cs, trims


def _splitters(net, spec: Spec, ribs):
    ring_nodes = {x for c in spec.ring for x in (c.node_a, c.node_b)}
    by_far = {}
    for c in spec.feeders:
        far = c.node_b if c.node_a in ring_nodes else c.node_a
        by_far.setdefault(far, []).append(c)
    wmax, gap = float(spec.opts["splitter_w_m"]), float(spec.opts["splitter_gap_m"])
    keep_out = shapely.union_all(ribs + [Point(*spec.center).buffer(spec.r_out + gap, 96)])
    out = []
    for far in sorted(by_far):
        pair = by_far[far]
        if len(pair) != 2:
            continue
        f = np.linspace(0.0, 1.0, 60)
        legs = []
        for c in pair:                       # both legs from the split node (f = 0) to the ring (f = 1)
            s = f * c.length if c.node_a == far else (1.0 - f) * c.length
            legs.append(c.line.point(s))
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
        rings = [r0] + list(np.arange(math.floor(r0), 0.5, -1.0))
        V = [np.column_stack([spec.center + r * cs_[:-1], zg[:-1] + dz_top]) for r in rings]
        V.append(np.array([[spec.center[0], spec.center[1], float(np.mean(zg[:-1])) + dz_top]]))
        V = np.vstack(V)
        T = []
        for k in range(len(rings) - 1):
            b0, b1 = k * n, (k + 1) * n
            for i in range(n):
                i1 = (i + 1) % n
                T += [(b0 + i, b0 + i1, b1 + i1), (b0 + i, b1 + i1, b1 + i)]
        b0, cidx = (len(rings) - 1) * n, len(rings) * n
        T += [(b0 + i, b0 + (i + 1) % n, cidx) for i in range(n)]
        fill = str(spec.opts["island_fill"])
        COL = None
        if fill == "island_gravel":
            COL = np.zeros((len(V), 4))
            COL[:, 0] = 0.3                                   # light grime: a new roundabout (owner photo 9)
        buf.add("road", fill, V, V[:, :2].copy(), np.array(T), src=src + ":fill", COL=COL)
        buf.add("collision", "collision_grass" if fill == "verge_grass" else "collision_paving", V, V[:, :2].copy(),
                np.array(T), src=src + ":fill")
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
            "r_outer_m": round(spec.r_out, 2), "apron_m": round(spec.apron[2], 2), "apron_lip_m": round(spec.apron[1], 3),
            "island_r_m": round(spec.r_in - spec.apron[2], 2), "splitters": len(spec.splitters),
            "splitter_m2": [round(pg.area, 1) for _, pg in spec.splitters],
            "outline_m2": round(spec.outline.area, 1) if spec.outline is not None else None,
            "ring_chains": len(spec.ring), "feeders": len(spec.feeders), "notes": list(spec.notes)}
