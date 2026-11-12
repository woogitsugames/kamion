"""Gaps between carriageways: island or paved gore? (ADR 0077, owner: "roads literally as in OSM")

The generator builds one ribbon per OSM carriageway plus junction patches. Whatever lies between two ribbons used to
become an island by default (kerbs on both edges, terrain / grass between them), also where OSM only draws two axes
converging on a node (merge / diverge tips, slip lanes beside the main road). On the ground those places are paved.

Rule (ADR 0077): a gap between carriageways is an island only where the data says so:
  * OSM: separate one-way carriageways with a real gap (a median at least GORE_MIN_ISLAND_W wide), a roundabout
    centre, `area:highway=traffic_island` / `traffic_calming=island` areas (none in the Białystok tile);
  * orthophoto-confirmed islands as `kind: traffic_island` authored overrides (polygon, evidence).
Everything else is paved:
  * narrow slivers: the part of a gap that a kerbed island of GORE_MIN_ISLAND_W cannot fill (tips where two
    carriageways converge, slivers beside a parallel slip lane) when it is short (< GORE_SLIVER_MAX_LEN_M: a long
    narrow strip is a real median with a barrier);
  * enclosed holes smaller than GORE_MIN_ISLAND_M2;
  * `kind: paved_gore` authored overrides: gaps the orthophoto shows as continuous asphalt (point + radius).

A paved gore = (a) the kerbs of the ribbons / junction corners that face it are dropped below the surface
(`plan`, before meshing), (b) an asphalt fill triangulated between the carriageway edges with heights read off the
generated carriageway surface, visual + collision (`build`, after meshing).

`traffic_island` overrides are raised kerbed islands laid on the carriageway (kerb S.KERB_HEIGHT, paved or grass top).
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field

import numpy as np
import shapely
from shapely.geometry import Point, Polygon

from . import standards as S
from .network import URBAN
from .geom import smooth_1d
from .network import DENSE

GORE_MIN_ISLAND_W = 2.0        # WORKING_VALUE: narrowest kerbed island / median the generator builds (pedestrian refuge
                               # islands are >= 2.0 m wide; narrower separations are paint or a continuous surface)
GORE_MIN_NOSE_W = 4.0          # WORKING_VALUE: clear width at which a kerbed nose starts between same-direction
                               # carriageways (merge / diverge gore); narrower = continuous surface / painted P-21
GORE_MERGE_MAX_LEN_M = 90.0    # WORKING_VALUE: longer same-direction strips are a separator (collector road), keep
GORE_MIN_ISLAND_M2 = 5.0       # WORKING_VALUE: smaller enclosed islands are painted, not kerbed
GORE_SLIVER_MIN_M2 = 1.5       # ignore numerical crumbs
GORE_SLIVER_MAX_LEN_M = 60.0   # WORKING_VALUE: a longer uniformly narrow strip is a median, keep it
GORE_HATCH_MIN_M2 = 12.0       # WORKING_VALUE: smaller merge tips carry no paint (two edge lines meet)
P21_STRIPE_W_M = 0.5           # WORKING_VALUE: P-21 oblique stripe width / gap read off the 0.08 m orthophoto
P21_STRIPE_GAP_M = 1.0
P21_EDGE_INSET_M = 0.35        # border line this far inside the gore outline
GORE_MAX_SLOPE = 0.10          # fill edges steeper than this (+ GORE_MAX_STEP_M) = carriageways at different heights
GORE_MAX_STEP_M = 0.15         # (ramp wall, viaduct abutment): no fill. WORKING_VALUE
GORE_MAX_STEP_AUTHORED_M = 0.35  # authored paved_gore (orthophoto says continuous): tolerate patch height mismatch
GORE_OVERRIDE_CLOSE_M = 3.5    # authored paved_gore: default closing radius (gaps up to 7 m wide); `close_m` per override
GORE_KERB_DROP_M = 0.06        # kerb top this far below the surface along a paved gore (hidden under the fill)
GORE_OVERLAP_M = 0.06          # fill reaches this far under the neighbouring carriageways (no cracks)
GORE_VISUAL_DZ = -0.004        # fill this much below the carriageway where they overlap (no z-fighting)
GORE_SURFACES = {"sett": "road_sett", "paving": "road_paving", "concrete": "road_concrete"}   # paved_gore `surface:`
CARRIAGEWAY_MATS = {"road_asphalt", "road_asphalt_new", "road_concrete", "road_paving", "road_sett", "road_gravel"}


@dataclass
class Gore:
    poly: Polygon
    why: str                      # "sliver" | "hole" | "override:<id>"
    mat: str = "road_asphalt"
    area: float = 0.0
    built: bool = False
    note: str = ""
    hatch: bool = False           # painted exclusion zone P-21 (paint only, no kerb, no collision obstacle)


@dataclass
class Island:
    id: str
    poly: Polygon
    surface: str = "sidewalk_paving"
    built: bool = False
    note: str = ""
    patches: list = field(default_factory=list)      # [(Polygon, surface)]: parts of the top with another surface (ADR 0128)
    ring: object = None                              # kerb line (n, 2) and its top heights, set when built
    ring_top: object = None

    def top_z(self, p):
        """Height of the island top at p (kerb top at the nearest kerb-line vertex), None before the island is built."""
        if self.ring is None:
            return None
        return float(self.ring_top[int(np.argmin(np.hypot(self.ring[:, 0] - p[0], self.ring[:, 1] - p[1])))])


@dataclass
class GorePlan:
    gores: list = field(default_factory=list)
    islands: list = field(default_factory=list)
    rejected: list = field(default_factory=list)
    flush_m: float = 0.0
    overrides_applied: list = field(default_factory=list)
    overrides_stale: list = field(default_factory=list)


def _chain_polys(c):
    """Ground carriageway polygons of a chain between its junction trims (bridge stations excluded)."""
    if c.meta.get("absorbed"):
        return []
    s0, s1 = c.t_a, c.length - c.t_b
    if s1 - s0 < 0.5:
        return []
    st = np.unique(np.concatenate([[s0], c.line.s[(c.line.s > s0) & (c.line.s < s1)], [s1]]))
    br = c.interp(c.bridge.astype(float), st) > 0.5
    hw = c.hw_at(st)
    out = []
    i = 0
    while i < len(st):
        if br[i]:
            i += 1
            continue
        k = i
        while k + 1 < len(st) and not br[k + 1]:
            k += 1
        if k > i:
            sl = slice(i, k + 1)
            L = c.line.offset_point(st[sl], hw[sl])
            R = c.line.offset_point(st[sl], -hw[sl])
            pg = Polygon(np.concatenate([L, R[::-1]]))
            if not pg.is_valid:
                pg = pg.buffer(0)
            if pg.area > 0.1:
                out.append(pg)
        i = k + 1
    return out


def carriageway_union(net, juncs):
    polys = []
    for c in net.chains:
        polys += _chain_polys(c)
    for j in juncs:
        if len(j.boundary) >= 3 and not all(
                bool(a.chain.bridge[a.chain.idx(a.s(j.trims[i]))]) for i, a in enumerate(j.arms)):
            pg = Polygon(np.array([p for p, _ in j.boundary]))
            if pg.is_valid:
                polys.append(pg)
            else:
                # self-intersecting outline: exactly the lobes meshing._repair_fill triangulates (make_valid, parts
                # > 0.3 m2). buffer(0) kept a different set (non-zero winding), so a 32 m2 hole of the visual patch of
                # j:n1882887385 (s 610) was "carriageway" here and its paved_gore override went stale.
                fixed = shapely.make_valid(pg)
                polys += [g for g in getattr(fixed, "geoms", [fixed]) if g.geom_type == "Polygon" and g.area > 0.3]
    return shapely.union_all(polys)


def _parts(g):
    if g.is_empty:
        return []
    return [p for p in getattr(g, "geoms", [g]) if isinstance(p, Polygon) and p.area > 0]


def _length(pg):
    r = pg.minimum_rotated_rectangle
    xy = np.asarray(r.exterior.coords)
    return float(max(np.hypot(*(xy[1] - xy[0])), np.hypot(*(xy[2] - xy[1]))))


class _ChainSurface:
    """Height of the nearest carriageway (chain cross-section, extrapolated inside junction trims)."""

    def __init__(self, net):
        self.chains = [c for c in net.chains if not c.meta.get("absorbed")]
        self.tree = shapely.STRtree([shapely.LineString(c.line.p) for c in self.chains])

    def z(self, p, reach=14.0):
        best = None
        for k in self.tree.query(Point(*p).buffer(reach)):
            c = self.chains[int(k)]
            s, lat = c.line.project(np.asarray(p, float))
            s = float(np.clip(s, 0.0, c.length))
            if bool(c.bridge[c.idx(s)]):
                continue
            hw = float(c.hw_at(s))
            q = c.line.offset_point(s, float(np.clip(lat, -hw, hw)))
            d = float(np.hypot(*(q - np.asarray(p, float))))        # distance to the carriageway (0 inside it)
            if best is None or d < best[0]:
                best = (d, float(c.crossfall_z(s, float(np.clip(lat, -hw, hw)))))
        return None if best is None or best[0] > 9.0 else best[1]

    def same_direction(self, pg):
        """True when the two carriageways nearest to the gap are one-way and run the same way."""
        p = np.array(pg.representative_point().coords[0])
        near = []
        for k in self.tree.query(Point(*p).buffer(20.0)):
            c = self.chains[int(k)]
            s, lat = c.line.project(p)
            if s <= 0.0 or s >= c.length:
                continue
            d = abs(lat) - float(c.hw_at(s))
            if d > 5.0:
                continue
            i = int(c.idx(s))
            near.append((d, int(c.dirn[i]), c.line.t[i] * float(c.dirn[i]), bool(c.roundabout)))
        near.sort(key=lambda x: x[0])
        if len(near) < 2:
            return False
        (_, d0, t0, r0), (_, d1, t1, r1) = near[:2]
        return d0 != 0 and d1 != 0 and not r0 and not r1 and float(np.dot(t0, t1)) > 0.7


def _triangulate(pg, step=1.5):
    pg = shapely.segmentize(pg, step)
    tris = shapely.constrained_delaunay_triangles(pg)
    V, key, T = [], {}, []
    for t in getattr(tris, "geoms", []):
        ids = []
        for x, y in np.asarray(t.exterior.coords)[:3]:
            k = (round(float(x), 4), round(float(y), 4))
            if k not in key:
                key[k] = len(V)
                V.append([float(x), float(y)])
            ids.append(key[k])
        T.append(ids)
    if not T:
        return None, None
    V, T = np.array(V), np.array(T)
    a, b, c = V[T[:, 0]], V[T[:, 1]], V[T[:, 2]]
    cr = (b[:, 0] - a[:, 0]) * (c[:, 1] - a[:, 1]) - (b[:, 1] - a[:, 1]) * (c[:, 0] - a[:, 0])
    T[cr < 0] = T[cr < 0][:, [0, 2, 1]]
    return V, T


def _worst_step(V, Z, T):
    """Largest height excess of a fill edge over GORE_MAX_SLOPE x length (m)."""
    worst = 0.0
    for i, k in ((0, 1), (1, 2), (2, 0)):
        d = np.hypot(*(V[T[:, i]] - V[T[:, k]]).T)
        dz = np.abs(Z[T[:, i]] - Z[T[:, k]])
        worst = max(worst, float(np.max(dz - GORE_MAX_SLOPE * d)))
    return worst


def _slope_ok(V, Z, T, authored=False):
    return _worst_step(V, Z, T) <= (GORE_MAX_STEP_AUTHORED_M if authored else GORE_MAX_STEP_M)


def plan(net, juncs, overrides, origin) -> GorePlan:
    """Decide which gaps are paved, drop the kerbs facing them. Call after junctions + profiles, before meshing."""
    gp = GorePlan()
    if os.environ.get("WORLDGEN_NO_GORES"):      # A/B switch for the fidelity "before" measurement (ADR 0077)
        return gp
    U = carriageway_union(net, juncs)
    surf = _ChainSurface(net)
    cand = []
    r = GORE_MIN_ISLAND_W / 2
    narrow = U.buffer(r, quad_segs=6).buffer(-r, quad_segs=6).difference(U)
    for pg in _parts(narrow):
        if pg.area < GORE_SLIVER_MIN_M2 or _length(pg) > GORE_SLIVER_MAX_LEN_M:
            continue
        cand.append(Gore(pg, "sliver"))
    # merge / diverge gores: between two one-way carriageways running the SAME way (slip lane beside the main road,
    # on-ramp before its merge node) the kerbed nose starts only where the gap reaches GORE_MIN_NOSE_W; before that
    # the surface is continuous (painted P-21 at most). Medians (opposite directions) are not touched by this rule.
    r2 = GORE_MIN_NOSE_W / 2
    for pg in _parts(U.buffer(r2, quad_segs=6).buffer(-r2, quad_segs=6).difference(U)):
        if pg.area < GORE_SLIVER_MIN_M2 or _length(pg) > GORE_MERGE_MAX_LEN_M:
            continue
        if surf.same_direction(pg):
            # owner reference 2026-11-10 (docs/refs/owner-aerials-2026-11-10.md) + orthophoto (s 1440): the surface
            # in front of a channelising island nose is a painted P-21 exclusion zone across the whole nose width
            # ADR 0093: no paint from this rule. The P-21 ladders it used to draw (>= GORE_HATCH_MIN_M2) did not match
            # the orthophoto anywhere they were checked; exclusion zones come only from `painted_zone` overrides.
            cand.append(Gore(pg, "merge"))
    for body in _parts(U):
        for ring in body.interiors:
            hole = Polygon(ring)
            if GORE_SLIVER_MIN_M2 <= hole.area < GORE_MIN_ISLAND_M2:
                cand.append(Gore(hole, "hole"))
    ov = [o for o in overrides if o.get("kind") == "paved_gore"]
    if ov:
        gap_sets = {}
        for o in ov:
            pt = Point(*o["at_en"])
            rad = float(o.get("radius_m", 40.0))
            cm = float(o.get("close_m", GORE_OVERRIDE_CLOSE_M))      # half of the widest gap this override may pave
            if cm not in gap_sets:
                gg = _parts(U.buffer(cm, quad_segs=6).buffer(-cm, quad_segs=6).difference(U))
                gap_sets[cm] = (gg, shapely.STRtree(gg))
            gaps, gtree = gap_sets[cm]
            hit = [gaps[int(k)] for k in gtree.query(pt.buffer(1.5)) if gaps[int(k)].distance(pt) <= 1.5]
            if not hit:
                gp.overrides_stale.append(o["id"])
                continue
            for g in hit:
                for pg in _parts(g.intersection(pt.buffer(rad))):
                    if pg.area >= GORE_SLIVER_MIN_M2:
                        cand.append(Gore(pg, "override:" + o["id"], mat=GORE_SURFACES.get(o.get("surface"), "road_asphalt")))
            gp.overrides_applied.append({"id": o["id"], "targets": [f"gap@{o['at_en'][0]:.0f},{o['at_en'][1]:.0f}"]})
    # one polygon per place (an override gap swallows the slivers inside it)
    # authored overrides first, in file order (a small hatched zone listed before the larger plain gap keeps its
    # paint), then merge gores, then slivers / holes by area
    order = {id(g): i for i, g in enumerate(cand)}
    cand.sort(key=lambda g: ({"o": 0, "m": 1}.get(g.why[0], 2), order[id(g)] if g.why[0] == "o" else -g.poly.area))
    taken = None
    for g in cand:
        pg = g.poly if taken is None else g.poly.difference(taken.buffer(0.05))
        for part in _parts(pg):
            if part.area < GORE_SLIVER_MIN_M2:
                continue
            V, T = _triangulate(part)
            if V is None:
                continue
            Z = np.array([surf.z(p) for p in V], dtype=object)
            if any(z is None for z in Z):
                gp.rejected.append({"why": g.why, "xy": [round(v, 1) for v in part.centroid.coords[0]],
                                    "area_m2": round(part.area, 1), "reason": "no carriageway height nearby"})
                continue
            Z = Z.astype(float)
            if not _slope_ok(V, Z, T, g.why.startswith("override")):
                gp.rejected.append({"why": g.why, "xy": [round(v, 1) for v in part.centroid.coords[0]],
                                    "area_m2": round(part.area, 1), "reason": "carriageways at different heights",
                                    "step_m": round(_worst_step(V, Z, T), 2)})
                continue
            gp.gores.append(Gore(part, g.why, mat=g.mat, area=float(part.area), hatch=g.hatch))
            taken = part if taken is None else taken.union(part)
    for o in overrides:
        if o.get("kind") != "traffic_island":
            continue
        pg = (Polygon(np.array(o["polygon_en"], float)) if o.get("polygon_en")       # region-local E/N (ADR 0093)
              else Polygon(np.array(o["polygon_epsg2180"]) - np.array(origin)))
        if not pg.is_valid or not pg.intersects(U.buffer(8.0)):
            gp.overrides_stale.append(o["id"])
            continue
        isl = Island(o["id"], pg, o.get("surface", "sidewalk_paving"))
        # ADR 0128: `patches: [{surface, polygon_en}]` - parts of the island top with another surface inside the one
        # kerb ring (a footpath crossing a gravel nose); only the part inside the island counts
        for pt in o.get("patches", []):
            pp = Polygon(np.array(pt["polygon_en"], float)).buffer(0)
            if pp.is_valid and pp.intersects(pg):
                isl.patches.append((pp, pt["surface"]))
        gp.islands.append(isl)
        gp.overrides_applied.append({"id": o["id"], "targets": ["island"]})
    if gp.gores:
        _drop_kerbs(net, gp)
    return gp


def _drop_kerbs(net, gp):
    zone = shapely.union_all([g.poly for g in gp.gores]).buffer(0.35)
    shapely.prepare(zone)
    minx, miny, maxx, maxy = zone.bounds
    sig = 2.0 / DENSE
    for c in net.chains:
        if c.meta.get("absorbed") or not c.side:
            continue
        lo, hi = c.line.p.min(0) - 15, c.line.p.max(0) + 15
        if lo[0] > maxx or hi[0] < minx or lo[1] > maxy or hi[1] < miny:
            continue
        touched = False
        for side, sgn in (("L", 1.0), ("R", -1.0)):
            d = c.side[side]
            probe = c.line.p + c.line.n * (sgn * (c.hw + 0.3))[:, None]
            # all side kinds: a shoulder / verge side left as it was pokes through the fill (33 verge_grass / shoulder
            # obstacle_in_lane cases when only kerbed sides were dropped, measured 2026-11-11)
            m = shapely.contains_xy(zone, probe[:, 0], probe[:, 1]) & ~c.bridge
            if not m.any():
                continue
            kind0 = d["kind"].copy()
            h0, w0, depth0 = d["h"].copy(), d["w"].copy(), d["depth"].copy()
            d["kind"][m] = URBAN
            d["mat"][m] = 0
            d["raw"]["h"][m] = -GORE_KERB_DROP_M
            d["raw"]["w"][m] = 0.0
            d["raw"]["depth"][m] = S.FLANGE_DEPTH
            d["h"], d["w"], d["depth"] = (smooth_1d(d["raw"]["h"], sig), smooth_1d(d["raw"]["w"], sig),
                                          smooth_1d(d["raw"]["depth"], sig))
            d["h"][m] = -GORE_KERB_DROP_M          # no kerb ridge inside the paved zone (smoothing ramps outside it)
            # outside the zone only the kerb of a kerbed side ramps down; strip width / depth and the whole profile
            # of shoulder sides (embankments of the viaduct ramps) stay as they were. Smoothing them too narrowed
            # the verge next to the gore nose to nothing: 12 new steep grass faces of 0.5-0.7 m (terrain_walls_qa,
            # E 786 N -831, E 321 N -603, E 48 N -460).
            out = ~m
            d["w"][out], d["depth"][out] = w0[out], depth0[out]
            keep = out & (kind0 != URBAN)
            d["h"][keep] = h0[keep]
            gp.flush_m += float(m.sum() * DENSE)
            touched = True
        if touched:
            c.meta["gore_flush"] = True


class _MeshSurface:
    """Exact height of the generated ground carriageway under / next to a point (triangles of the visual mesh)."""

    def __init__(self, parts):
        tris = []
        for p in parts:
            if p.layer == "road" and p.mat in CARRIAGEWAY_MATS and len(p.T):
                tris.append(p.V[p.T])
        self.tri = np.concatenate(tris)
        a2 = np.abs((self.tri[:, 1, 0] - self.tri[:, 0, 0]) * (self.tri[:, 2, 1] - self.tri[:, 0, 1])
                    - (self.tri[:, 2, 0] - self.tri[:, 0, 0]) * (self.tri[:, 1, 1] - self.tri[:, 0, 1]))
        self.tri = self.tri[a2 > 1e-5]
        ring = np.concatenate([self.tri[:, :, :2], self.tri[:, :1, :2]], axis=1)
        self.polys = shapely.polygons(ring)
        self.tree = shapely.STRtree(self.polys)

    def z(self, p, zref=None, reach=1.0):
        pt = Point(*p)
        idx = self.tree.query(pt, predicate="dwithin", distance=reach)
        if not len(idx):
            return None
        d = shapely.distance(self.polys[idx], pt)
        if zref is not None:
            ok = np.abs(self.tri[idx][:, :, 2].mean(1) - zref) < 1.5
            if ok.any():
                idx, d = idx[ok], d[ok]
        k = int(idx[int(np.argmin(d))])
        t = self.tri[k]
        q = shapely.ops.nearest_points(self.polys[k], pt)[0]
        # plane through the triangle
        n = np.cross(t[1] - t[0], t[2] - t[0])
        if abs(n[2]) < 1e-9:
            return float(t[:, 2].mean())
        return float(t[0, 2] - (n[0] * (q.x - t[0, 0]) + n[1] * (q.y - t[0, 1])) / n[2])


def build(buf, net, gp: GorePlan):
    """Asphalt fills of the paved gores and the authored islands (visual + collision). Call after ribbons + patches."""
    import shapely.ops  # noqa: F401
    if not gp.gores and not gp.islands:
        return
    ms = _MeshSurface(buf.parts)
    cs = _ChainSurface(net)
    for g in gp.gores:
        pg = g.poly.buffer(GORE_OVERLAP_M, join_style="mitre")
        V, T = _triangulate(pg)
        if V is None:
            g.note = "triangulation failed"
            continue
        Z = np.zeros(len(V))
        ok = True
        for i, p in enumerate(V):
            zr = cs.z(p)
            z = ms.z(p, zr)
            if z is None:
                z = zr
            if z is None:
                ok = False
                break
            Z[i] = z
        if not ok or not _slope_ok(V, Z, T, True):
            g.note = "height mismatch on the generated surface"
            continue
        V3 = np.column_stack([V, Z + GORE_VISUAL_DZ])
        buf.add("road", g.mat, V3, V.copy(), T, footprint=True, src="gore:" + g.why)
        buf.add("collision", "collision_asphalt", np.column_stack([V, Z]), V.copy(), T, src="gore:" + g.why)
        g.built = True
    for isl in gp.islands:
        _build_island(buf, isl, ms, cs)


def _build_island(buf, isl: Island, ms, cs):
    pg = shapely.segmentize(isl.poly.buffer(0), 1.0)
    ring = np.asarray(pg.exterior.coords)[:-1]
    if Polygon(ring).exterior.is_ccw is False:
        ring = ring[::-1]
    zr = []
    for p in ring:
        z0 = cs.z(p)
        z = ms.z(p, z0, reach=2.0)
        zr.append(z if z is not None else z0)
    if any(z is None for z in zr):
        isl.note = "no carriageway under the island"
        return
    zr = np.array(zr)
    h = S.KERB_HEIGHT
    n = len(ring)
    tw = S.KERB_TOP_W
    inner_pg = Polygon(ring).buffer(-tw, join_style="mitre")
    # kerb face (vertical) + kerb top band + inner top surface
    face = np.concatenate([np.column_stack([ring, zr - 0.02]), np.column_stack([ring, zr + h])])
    T = []
    for i in range(n):
        k = (i + 1) % n
        T += [(i, k, n + k), (i, n + k, n + i)]
    along = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(np.vstack([ring, ring[:1]]), axis=0).T))])[:n]
    UV = np.concatenate([np.column_stack([along, np.zeros(n)]), np.column_stack([along, np.full(n, h)])])
    buf.add("road", "curb_concrete", face, UV, np.array(T), src="island:" + isl.id)
    buf.add("collision", "collision_curb", face, UV, np.array(T), src="island:" + isl.id)
    zmean = float(zr.mean())

    def top(poly, mat, cmat, lift):
        V, Tt = _triangulate(poly, 2.0)
        if V is None:
            return
        # height: nearest ring vertex (kerb line follows the carriageway)
        d = np.hypot(V[:, None, 0] - ring[None, :, 0], V[:, None, 1] - ring[None, :, 1])
        z = zr[np.argmin(d, axis=1)] + h + lift
        buf.add("road", mat, np.column_stack([V, z]), V.copy(), Tt, src="island:" + isl.id)
        buf.add("collision", cmat, np.column_stack([V, z]), V.copy(), Tt, src="island:" + isl.id)

    if inner_pg.is_empty or inner_pg.area < 0.5:
        top(Polygon(ring), "curb_concrete", "collision_curb", 0.0)
    else:
        top(Polygon(ring).difference(inner_pg), "curb_concrete", "collision_curb", 0.0)
        rest = inner_pg
        for pp, surf in isl.patches:            # ADR 0128: authored sub-surfaces, first listed wins where they overlap
            for part in _parts(rest.intersection(pp)):
                if part.area >= 0.05:
                    top(part, surf, "collision_grass" if surf == "verge_grass" else "collision_paving", 0.0)
            rest = rest.difference(pp)
        for part in _parts(rest):
            if part.area < 0.05:
                continue
            grass = isl.surface == "verge_grass"
            top(part, isl.surface, "collision_grass" if grass else "collision_paving", 0.0)
    isl.built = True
    isl.ring, isl.ring_top = ring, zr + h
    isl.note = f"z {zmean:.2f}"


def _clip_tris(p, idx, zone):
    """Parts of the triangles p.T[idx] outside `zone`, re-triangulated; new vertices (position, UV, UV1, COL
    interpolated in the plane of their triangle) are appended to the part. Returns the new triangle rows."""
    out = []
    V, UV, UV1, COL = [p.V], [p.UV], [p.UV1], [p.COL]
    nv = len(p.V)
    for i in idx:
        t = p.T[i]
        A = p.V[t]
        rest = Polygon(A[:, :2]).difference(zone)
        if rest.is_empty or rest.area < 1e-4:
            continue
        M = np.column_stack([A[:, :2], np.ones(3)])
        try:
            Mi = np.linalg.inv(M)
        except np.linalg.LinAlgError:
            continue
        ccw = Polygon(A[:, :2]).exterior.is_ccw
        for piece in _parts(rest):
            if piece.area < 1e-4:
                continue
            for tri in shapely.get_parts(shapely.delaunay_triangles(piece)):
                if not piece.contains(tri.representative_point()) or tri.area < 1e-6:
                    continue
                q = np.asarray(tri.exterior.coords)[:3]
                if Polygon(q).exterior.is_ccw != ccw:
                    q = q[::-1]
                W = np.column_stack([q, np.ones(3)]) @ Mi           # barycentric weights of the 3 new vertices
                V.append(W @ A)
                UV.append(W @ p.UV[t])
                if p.UV1 is not None:
                    UV1.append(W @ p.UV1[t])
                if p.COL is not None:
                    COL.append(W @ p.COL[t])
                out.append((nv, nv + 1, nv + 2))
                nv += 3
    if out:
        p.V, p.UV = np.concatenate(V), np.concatenate(UV)
        if p.UV1 is not None:
            p.UV1 = np.concatenate(UV1)
        if p.COL is not None:
            p.COL = np.concatenate(COL)
    return np.array(out, dtype=p.T.dtype).reshape(-1, 3)


def _drop_verge_in_islands(buf, gp: GorePlan) -> int:
    """ADR 0110: the grass strips behind kerbs (meshing._emit_verge, src "...:vg") do not run under an authored
    traffic island or a paved gore fill (dk8-ramp-split-island: paving with grass strips showing through it)."""
    polys = [i.poly.buffer(0.30) for i in gp.islands] + [g.poly.buffer(0.10) for g in gp.gores if g.built]
    if not polys:
        return 0
    zone = shapely.union_all(polys)
    shapely.prepare(zone)
    b = zone.bounds
    n = 0
    keep = []
    for p in buf.parts:
        if p.src.endswith(":vg") and len(p.T):
            lo, hi = p.V[:, :2].min(0), p.V[:, :2].max(0)
            if not (hi[0] < b[0] or lo[0] > b[2] or hi[1] < b[1] or lo[1] > b[3]):
                tri = p.V[p.T]
                cen = tri.mean(1)
                drop = shapely.contains_xy(zone, cen[:, 0], cen[:, 1])
                for k in range(3):
                    drop |= shapely.contains_xy(zone, tri[:, k, 0], tri[:, k, 1])
                if drop.any():
                    n += int(drop.sum())
                    # ADR 0123 (REVIEW s10-0117 P2-6, the black slot behind the nose of the Putry N median): a strip
                    # triangle that only touches the zone is CUT at its outline, not dropped whole - the straights
                    # of a strip are one quad per run (Douglas-Peucker), so dropping it bared the ground for metres
                    # beside the island (terrain 0.15-0.2 m below the kerb top, in shadow)
                    newT = _clip_tris(p, np.where(drop)[0], zone)
                    p.T = np.concatenate([p.T[~drop], newT]) if len(newT) else p.T[~drop]
        if len(p.T):
            keep.append(p)
    buf.parts[:] = keep
    return n


def drop_kerbs_in_fills(buf, gp: GorePlan) -> int:
    """Remove the kerbs (render + collision, top and face) lying inside a built paved gore. plan() sinks them 6 cm so
    that the ribbon edge has no ridge; the sunk strip must not stay in the mesh (REVIEW 0077 #1). Returns triangles
    removed. meshing.cull_sides_on_carriageway only takes kerbs with carriageway all around at 0.30 m."""
    _drop_verge_in_islands(buf, gp)
    built = [g.poly.buffer(-0.10) for g in gp.gores if g.built]
    built = [b for b in built if not b.is_empty]
    if not built:
        return 0
    zone = shapely.union_all(built)
    shapely.prepare(zone)
    n = 0
    keep = []
    for p in buf.parts:
        if (p.layer in ("road", "bridge", "collision") and p.mat in ("curb_concrete", "collision_curb") and len(p.T)
                and not p.src.startswith("island:")):
            cen = p.V[p.T].mean(1)
            drop = shapely.contains_xy(zone, cen[:, 0], cen[:, 1])
            if drop.any():
                n += int(drop.sum())
                p.T = p.T[~drop]
        if len(p.T):
            keep.append(p)
    buf.parts[:] = keep
    return n


def kerbs_in_fills(buf, gp: GorePlan) -> int:
    """Kerb triangles (render, top or face) whose centre lies inside a built paved gore, within 0.5 m of its height.
    Must be 0 (ADR 0093): a kerb hidden under a fill is removed from the mesh, not sunk (REVIEW 0077 #1: sunk kerbs
    showed as grey strips on the lane wherever the fill did not cover them)."""
    built = [g.poly.buffer(-0.10) for g in gp.gores if g.built]
    built = [b for b in built if not b.is_empty]
    if not built:
        return 0
    zone = shapely.union_all(built)
    shapely.prepare(zone)
    n = 0
    for p in buf.parts:
        if p.layer not in ("road", "bridge") or p.mat != "curb_concrete" or len(p.T) == 0 or p.src.startswith("island:"):
            continue
        cen = p.V[p.T].mean(1)
        n += int(shapely.contains_xy(zone, cen[:, 0], cen[:, 1]).sum())
    return n


def report(gp: GorePlan) -> dict:
    by = {}
    for g in gp.gores:
        k = g.why.split(":")[0]
        by.setdefault(k, {"count": 0, "area_m2": 0.0})
        by[k]["count"] += 1
        by[k]["area_m2"] = round(by[k]["area_m2"] + g.area, 1)
    return {"rule": {"min_island_w_m": GORE_MIN_ISLAND_W, "min_island_m2": GORE_MIN_ISLAND_M2,
                     "sliver_max_len_m": GORE_SLIVER_MAX_LEN_M, "max_slope": GORE_MAX_SLOPE, "status": "WORKING_VALUE"},
            "paved": by, "kerb_dropped_m": round(gp.flush_m, 1),
            "gores": [{"why": g.why, "area_m2": round(g.area, 1), "built": g.built, "hatch": g.hatch, "note": g.note,
                       "xy": [round(v, 1) for v in g.poly.centroid.coords[0]]} for g in gp.gores],
            "islands": [{"id": i.id, "area_m2": round(i.poly.area, 1), "surface": i.surface, "built": i.built,
                         "note": i.note} for i in gp.islands],
            "rejected": gp.rejected}
