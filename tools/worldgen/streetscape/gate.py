"""Depot gate kit (authored override `kind: depot_gate` in Data/Regions/<id>/overrides.yaml).

OSM rarely maps how a depot entrance is built (Kwadrat Park: one lift_gate node beside the road, no fence),
so the kit is an explicit authored override keyed by the OSM node where the two-way access road splits into
one-way entry/exit lanes around an island. It survives every regeneration; a node that disappears from the
graph is reported in the streetscape QA (`gates.stale`), never dropped silently.

The kit (prototypes in streetscape.life_props, fence meshes like streetscape.furniture.fences):
  * gatehouse (portiernia) on the island where it is >= island_min_w wide, glazed side toward the entry lane;
  * one striped boom barrier per lane, housing on the island kerb: `barrier_base` + `barrier_boom` (closed; the
    engine drives it: Game.World.DepotBarrier opens it for an approaching vehicle, map audit MA-003);
  * cantilever sliding gate across the two-way road `gate_offset_m` inside the depot, standing open
    behind the fence on the side given by `gate_side`;
  * panel fence returns (anthracite 3D panels on a concrete plinth) from both gate posts along the gate line,
    up to `fence_return_m`, cut by road surfaces and buildings.
OSM lift_gate / gate nodes within `replace_radius_m` of the split are replaced by the kit (counted in the QA).

r12 (ADR 0092, review 2026-11-11 s9 par. 4: "szlaban da się objechać z obu stron"):
  * `side_strips: {entry: {...}, exit: {...}}` - a raised kerbed strip along the OUTER edge of each lane at the
    housing line (toward_road_m / toward_depot_m along the lane, w_m wide, top: sidewalk_paving | verge_grass); the
    rest post of the boom stands on it;
  * `closure: {entry: {style: bollards | fence, max_m}, exit: {...}}` - from the outer edge of that strip straight
    across the yard to where the paved yard ends (plot edge / building), so that no vehicle fits round the boom:
    steel posts every CLOSURE_POST_M with a collision wall, or the 3D panel fence on a plinth. The line is exported
    (`report["gates"]["closure_lines"]`) so that the parking rule keeps its bays off it;
  * tyre scuffs on the kerb at both noses of the island and of the strips (`decal_tyre` bands).
"""

from __future__ import annotations

import math

import numpy as np
import shapely
import shapely.affinity
from shapely.geometry import LineString, Point

from roads import decals as DC
from roads import standards as S
from roads.network import side_extent, side_params

from . import life_props as LP


def _yaw(f):
    return math.atan2(f[1], f[0]) - math.pi / 2


def _chain_at_node(net, xy, way):
    """(chain, s at the node, sign of the direction pointing away from the node) of the chain built from
    OSM way `way` that ends at xy."""
    best = None
    for c in net.chains:
        if c.meta.get("absorbed"):
            continue
        if not any(str(e).startswith(f"w{way}:") for e, _ in c.edges):
            continue
        for s, sg in ((0.0, 1.0), (c.length, -1.0)):
            d = float(np.hypot(*(c.line.offset_point(s, 0.0) - xy)))
            if best is None or d < best[0]:
                best = (d, c, s, sg)
    return best


ISLAND_H = 0.16            # m, island top above the lane edge (kerb 15x30 laid proud; WORKING_VALUE)
ISLAND_BEFORE_M = 2.5      # m of island before / after the housing line along the lanes (WORKING_VALUE)
ISLAND_AFTER_M = 3.5
LOOP_SIZE = (2.0, 1.0)     # m, saw-cut induction loop (along x across the lane), sealant line 4 cm (WORKING_VALUE)


def _raised(lin, poly, zlane, src, top="sidewalk_paving"):
    """Raised kerbed island over `poly` (a CCW polygon): precast kerb ring 0.15 m (curb_concrete) with a vertical face,
    top surface `top` at the kerb level, hard collision. zlane(R) -> level of the lane / yard beside each ring vertex
    (the island top is ISLAND_H above it, so a long strip follows the fall of its lane). Returns the ring levels
    (R, top z per vertex) or None when the polygon is too thin for a kerb ring."""
    R = np.asarray(poly.exterior.coords)[:-1]
    n = len(R)
    inner = poly.buffer(-S.KERB_TOP_W, join_style="mitre")
    if inner.is_empty or inner.geom_type != "Polygon":
        return None
    ib = inner.exterior
    Ri = np.array([ib.interpolate(ib.project(Point(*q))).coords[0] for q in R])
    zl = np.asarray(zlane(R), float)
    zt = zl + ISLAND_H
    zb = zl - 0.08
    s_arc = np.concatenate([[0.0], np.cumsum(np.hypot(*np.diff(np.vstack([R, R[:1]]), axis=0).T))])
    buf = lin.buf
    for k in range(n):
        j = (k + 1) % n
        u0, u1 = s_arc[k], s_arc[k + 1]
        # kerb top (CCW seen from above = faces up) and the outer vertical face (faces out of a CCW ring)
        V = np.array([[*R[k], zt[k]], [*R[j], zt[j]], [*Ri[j], zt[j]], [*Ri[k], zt[k]]])
        buf.add("paved", "curb_concrete", V, [[u0, 0.0], [u1, 0.0], [u1, S.KERB_TOP_W], [u0, S.KERB_TOP_W]],
                [(0, 1, 2), (0, 2, 3)], src=src)
        F = np.array([[*R[k], zb[k]], [*R[j], zb[j]], [*R[j], zt[j]], [*R[k], zt[k]]])
        buf.add("paved", "curb_concrete", F, [[u0, 0.25], [u1, 0.25], [u1, 0.0], [u0, 0.0]], [(0, 1, 2), (0, 2, 3)], src=src)
    # top: constrained fill of the inner ring (a strip may be a bent band: a fan from the centroid would fold over)
    ipoly = shapely.Polygon(Ri)
    if not ipoly.is_valid:
        return None
    Vf = np.column_stack([Ri, zt])
    key = {(round(float(q[0]), 5), round(float(q[1]), 5)): k for k, q in enumerate(Ri)}
    Tf = []
    for g in shapely.delaunay_triangles(shapely.MultiPoint(Ri)).geoms:
        if not ipoly.buffer(1e-6).contains(g.representative_point()):
            continue
        ids = [key.get((round(x, 5), round(y, 5))) for x, y in list(g.exterior.coords)[:3]]
        if None in ids:
            continue
        a, b, c = (Ri[k] for k in ids)
        if (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0]) < 0:
            ids = [ids[0], ids[2], ids[1]]
        Tf.append(tuple(ids))
    buf.add("paved", top, Vf, Vf[:, :2].copy(), Tf, src=src)
    # collider: the island as a low prism (top + kerb ring + skirt), kerb surface
    Vc = np.vstack([np.column_stack([Ri, zt]), np.column_stack([R, zt]), np.column_stack([R, zb])])
    Tc = list(Tf)
    for k in range(n):
        j = (k + 1) % n
        Tc += [(n + k, n + j, j), (n + k, j, k)]                              # kerb top ring
        Tc += [(2 * n + k, 2 * n + j, n + j), (2 * n + k, n + j, n + k)]      # skirt
    buf.add("collision", "collision_curb", Vc, Vc[:, :2].copy(), Tc, src=src)
    return R, zt


def _island(lin, P_e, P_x, z_lane, src):
    """Raised kerbed refuge the barrier housings stand on (review 2026-11-10 A6: the booms stood on flush paving that
    could be driven round). Outline = the median between the two kerb backs (rows P_e / P_x, same stations) with rounded
    corners, block-paved top. Returns (polygon, top z) or (None, None) when the median is too narrow."""
    poly = shapely.Polygon(np.vstack([P_e, P_x[::-1]]))
    poly = shapely.make_valid(poly).buffer(-0.35, join_style="mitre").buffer(0.35, quad_segs=3)
    if poly.is_empty or poly.geom_type != "Polygon" or poly.area < 1.5:
        return None, None
    poly = shapely.geometry.polygon.orient(poly, 1.0).simplify(0.02)
    if _raised(lin, poly, lambda R: np.full(len(R), float(z_lane)), src) is None:
        return None, None
    return poly, float(z_lane) + ISLAND_H


CLOSURE_POST_M = 1.5       # m between the steel posts of a closure line (a car is 1.7-1.9 m wide; WORKING_VALUE)
SCUFF_M = 2.2              # m of kerb round each nose of an island that carries tyre rub (WORKING_VALUE)


def _side_strip(lin, c, s_k, g, lat_sign, cfg, roads_poly, keep_pt, src):
    """Raised kerbed strip along the outer edge of lane chain `c` at the housing station s_k (r12). g = sign of the
    direction away from the split node (toward the public road), lat_sign = outer side in the chain frame. Returns
    (polygon, zlane function, outer offset from the lane centre at s_k) or (None, None, None)."""
    out_m, in_m = float(cfg.get("toward_road_m", 6.0)), float(cfg.get("toward_depot_m", 5.0))
    w = float(cfg.get("w_m", 1.4))
    aa = np.arange(-in_m, out_m + 1e-6, 0.5)
    ss = np.clip(s_k + g * aa, 0.0, c.length)
    hw = np.asarray(c.hw_at(ss), float)
    inner = hw + S.KERB_TOP_W - 0.03
    A = np.array([c.line.offset_point(float(s_), float(lat_sign * o_)) for s_, o_ in zip(ss, inner)])
    B = np.array([c.line.offset_point(float(s_), float(lat_sign * (o_ + w))) for s_, o_ in zip(ss, inner)])
    poly = shapely.make_valid(shapely.Polygon(np.vstack([A, B[::-1]])))
    poly = poly.difference(roads_poly.buffer(0.05))
    poly = poly.buffer(-0.3, join_style="mitre").buffer(0.3, quad_segs=3)
    parts = [q for q in getattr(poly, "geoms", [poly]) if q.geom_type == "Polygon" and q.area > 1.0]
    parts = [q for q in parts if q.buffer(0.3).contains(Point(*keep_pt))] or sorted(parts, key=lambda q: -q.area)[:1]
    if not parts:
        return None, None, None
    poly = shapely.geometry.polygon.orient(parts[0], 1.0).simplify(0.02)

    def zlane(R):
        out = []
        for q in np.asarray(R, float):
            sq = float(np.clip(c.line.project(q)[0], 0.0, c.length))
            out.append(max(float(c.crossfall_z(sq, lat_sign * float(c.hw_at(sq)))), float(lin.z(q[None, :])[0])))
        return np.array(out)

    if _raised(lin, poly, zlane, src, top=cfg.get("top", "sidewalk_paving")) is None:
        return None, None, None
    k0 = int(np.argmin(np.abs(aa)))
    return poly, zlane, float(inner[k0] + w)


def _scuffs(buf, poly, zlane, t_axis, key, src):
    """Tyre rub on the kerb at both noses of a raised island (review s9: "wyspa czysta"): a dark band on the kerb top
    edge and on its face over SCUFF_M round the vertices that are extreme along t_axis. `decal_tyre` bands (UV0 =
    metres along, v inside 0.36..0.64 = full opacity, hard edge; UV1 = length, strength). Returns the triangle count."""
    R = np.asarray(shapely.geometry.polygon.orient(poly, 1.0).exterior.coords)[:-1]
    n = len(R)
    zt = np.asarray(zlane(R), float) + ISLAND_H
    seg = np.hypot(*np.diff(np.vstack([R, R[:1]]), axis=0).T)
    a = R @ np.asarray(t_axis, float)
    tris = 0
    for e, k0 in enumerate((int(np.argmin(a)), int(np.argmax(a)))):
        idx = [k0]                       # walk both ways from the nose vertex until SCUFF_M / 2 of kerb is covered
        d, k = 0.0, k0
        while d < SCUFF_M / 2 and len(idx) < n:
            d += seg[k]
            k = (k + 1) % n
            idx.append(k)
        d, k = 0.0, k0
        while d < SCUFF_M / 2 and len(idx) < n:
            k = (k - 1) % n
            d += seg[k]
            idx.insert(0, k)
        P, Z = R[idx], zt[idx]
        m = len(P)
        if m < 2:
            continue
        tt = np.gradient(P, axis=0)
        tt /= np.maximum(np.linalg.norm(tt, axis=1, keepdims=True), 1e-9)
        nout = np.column_stack([tt[:, 1], -tt[:, 0]])               # outward of a CCW ring
        ssl = np.concatenate([[0.0], np.cumsum(np.hypot(*np.diff(P, axis=0).T))])
        strength = 2.5              # >= 2.5: solid band, no macro break-up (WorldPBR.shader _DECAL_TYRE)
        uv1 = np.column_stack([np.full(2 * m, ssl[-1] + 6.5), np.full(2 * m, strength)])   # +6.5: no end fade on a short band
        uvu = np.tile(ssl + 2.5, 2)
        T = np.array([(i, i + 1, m + i + 1) for i in range(m - 1)] + [(i, m + i + 1, m + i) for i in range(m - 1)])
        # face: from 15 mm under the top edge down to 0.11 m, 4 mm proud at the top and 16 mm at the bottom (the batter
        # of a kerb face; it also keeps the decal's normal pointing up-and-out: test_decals_face_up)
        Vf = np.vstack([np.column_stack([P + nout * 0.016, Z - 0.11]), np.column_stack([P + nout * 0.004, Z - 0.015])])
        buf.add("markings", "decal_tyre", Vf, np.column_stack([uvu, np.repeat([0.36, 0.64], m)]), T, src=f"{src}:face{e}",
                UV1=uv1)
        # top edge: 0.10 m of the kerb top
        Vt = np.vstack([np.column_stack([P - nout * 0.002, Z + 0.004]), np.column_stack([P - nout * 0.10, Z + 0.004])])
        buf.add("markings", "decal_tyre", Vt, np.column_stack([uvu, np.repeat([0.3, 0.7], m)]), T, src=f"{src}:top{e}",
                UV1=uv1)
        tris += 2 * len(T)
    return tris


def _closure_ray(a0, t, max_m, yardb, roads_b, bld_b, beyond_m):
    """One candidate closure line from a0 along unit t: the stretch over the paved yard (stops at a road or a
    building), continued over unpaved ground for up to beyond_m when a building stands there (a fence that stops at
    the edge of the paving can be driven round on the grass). Returns (LineString, why) or (None, why); why:
    building (ends on a wall: closed), yard_edge (ends where the paving ends), road (another carriageway), max_m."""
    line = LineString([a0, a0 + t * max_m])
    g = line.intersection(yardb).difference(roads_b).difference(bld_b)
    parts = [q for q in getattr(g, "geoms", [g]) if q.geom_type == "LineString" and q.length > 1.0]
    parts = [q for q in parts if q.distance(Point(*a0)) < 0.8]
    if not parts:
        return None, "no_room"
    L = max(float(np.hypot(*(np.asarray(c) - a0))) for c in parts[0].coords)
    end = a0 + t * L
    if L > max_m - 0.5:
        return LineString([a0, end]), "max_m"
    if bld_b.distance(Point(*end)) < 0.3:
        return LineString([a0, end]), "building"
    if roads_b.distance(Point(*end)) < 0.3:
        return LineString([a0, end]), "road"
    ext = LineString([end, end + t * beyond_m]).intersection(bld_b)
    if not ext.is_empty and roads_b.distance(LineString([end, end + t * beyond_m])) > 0.0:
        L2 = L + float(ext.distance(Point(*end)))
        return LineString([a0, a0 + t * L2]), "building"
    return LineString([a0, end]), "yard_edge"


def _closure(lin, a0, direction, cfg, yard, roads_poly, bpoly, src):
    """Line that keeps vehicles from driving round the boom: from a0 (outer edge of the side strip) to the nearest
    boundary of the paved yard. Candidates: rays within +-fan_deg of `direction` (straight out of the lane) every
    5 deg; the shortest one that ends on a building wins, else the shortest that ends at the edge of the paving (a ray
    that only reaches another road or max_m does not close anything and is the last resort). style bollards: yellow
    steel posts every CLOSURE_POST_M + one collision wall; style fence: anthracite 3D panels on a concrete plinth.
    Everything goes to the "paved" layer (a part in the chunk's furniture mesh would drag that whole mesh into the
    gate view, ADR 0071 r11). Returns (LineString or None, why it ends)."""
    t0 = direction / max(float(np.hypot(*direction)), 1e-9)
    max_m, beyond_m = float(cfg.get("max_m", 60.0)), float(cfg.get("beyond_m", 8.0))
    yardb, roads_b, bld_b = yard.buffer(0.3), roads_poly.buffer(0.4), bpoly.buffer(0.5)
    rank = {"building": 0, "yard_edge": 1, "road": 2, "max_m": 3}
    best = None
    fan = int(cfg.get("fan_deg", 60))
    for a in range(-fan, fan + 1, 5):
        ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
        t = np.array([t0[0] * ca - t0[1] * sa, t0[0] * sa + t0[1] * ca])
        ln, why = _closure_ray(a0, t, max_m, yardb, roads_b, bld_b, beyond_m)
        if ln is None:
            continue
        key = (rank[why], round(ln.length, 2), abs(a))
        if best is None or key < best[0]:
            best = (key, ln, why, t)
    if best is None:
        return None, "no_room"
    _, part, why, t = best
    buf = lin.buf
    n0 = len(buf.parts)
    if cfg.get("style", "bollards") == "fence":
        P = lin.dens(part, 1.0)
        Z = lin.z(P)
        lin.slab("concrete_plinth", P, Z - 0.2, Z + S.FENCE_PLINTH_H, 0.05, src)
        lin.ribbon("fence_anthracite_mesh", P, Z + S.FENCE_PLINTH_H, Z + S.FENCE_H, 0.0, src, both=True,
                   collision="collision_fence")
        lin.posts("fence_anthracite", P, S.FENCE_PANEL_W, 0.06, 0.04, S.FENCE_H + 0.05, src=src)
    else:
        p0 = np.asarray(part.coords[0])
        for d in np.arange(0.9, part.length - 0.2, CLOSURE_POST_M):
            q = p0 + t * d
            _bollard(buf, q, t, float(lin.z(q[None, :])[0]), src)
        P = lin.dens(part, 2.0)
        Z = lin.z(P)
        lin.ribbon("collision_fence", P, Z - 0.1, Z + 0.95, 0.0, src, both=True)
        for q in buf.parts[n0:]:
            if q.mat == "collision_fence":
                q.layer = "collision"
    for q in buf.parts[n0:]:
        if q.layer == "furniture":
            q.layer = "paved"
    return part, why


def _bollard(buf, q, t, z, src, w=0.11, h=0.95):
    """Yellow steel post on the island. Layer "paved" like the island itself: in the chunk's furniture mesh the two
    posts stretched that mesh's bounds to the gate and put its 19 k triangles into the gate view (Low estimate +10 %)."""
    nn = np.array([-t[1], t[0]])
    c4 = [q + sx * t * w / 2 + sy * nn * w / 2 for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]     # CCW from above
    V = np.array([[*c, z - 0.05] for c in c4] + [[*c, z + h] for c in c4])
    T = [(4, 5, 6), (4, 6, 7)]
    for k in range(4):
        j = (k + 1) % 4
        T += [(k, j, 4 + j), (k, 4 + j, 4 + k)]
    buf.add("paved", "paint_yellow", V, V[:, :2].copy(), T, src=src)


def _loop(buf, c, s, g, lat_feed, src):
    """Saw-cut induction loop in the lane: a rectangle of bitumen-sealed cuts with chamfered corners and a feeder cut
    toward the island (lat_feed = lateral position of the housing in the chain frame)."""
    hl, hw_ = LOOP_SIZE[0] / 2, LOOP_SIZE[1] / 2
    ch = 0.25
    pts = [(-hl + ch, -hw_), (hl - ch, -hw_), (hl, -hw_ + ch), (hl, hw_ - ch), (hl - ch, hw_), (-hl + ch, hw_),
           (-hl, hw_ - ch), (-hl, -hw_ + ch)]
    sgn = 1.0 if lat_feed >= 0 else -1.0
    segs = list(zip(pts, pts[1:] + pts[:1])) + [((0.0, sgn * hw_), (0.0, lat_feed))]
    hw = float(c.hw_at(s))
    for k, (a, b) in enumerate(segs):
        A = np.array([[s + g * a[0], a[1]], [s + g * b[0], b[1]]])
        d = A[1] - A[0]
        L = float(np.hypot(*d))
        if L < 0.05:
            continue
        nn = np.array([-d[1], d[0]]) / L * 0.02
        Q = np.array([A[0] - nn, A[1] - nn, A[1] + nn, A[0] + nn])
        V = []
        for q in Q:
            lat = float(np.clip(q[1], -hw + 0.02, hw - 0.02))
            V.append([*c.line.offset_point(float(q[0]), lat), float(c.crossfall_z(float(q[0]), lat)) + DC.LIFT_OIL])
        V = np.array(V)
        T = [(0, 1, 2), (0, 2, 3)]
        e1, e2 = V[1, :2] - V[0, :2], V[3, :2] - V[0, :2]
        if e1[0] * e2[1] - e1[1] * e2[0] < 0:
            T = [(0, 2, 1), (0, 3, 2)]
        buf.add("markings", "decal_sealant", V, [[0, 0], [L, 0], [L, 1], [0, 1]], T, src=f"{src}:{k}")


def build(pl, lin, net, graph, overrides, roads_poly, bpoly, origin, report, paved=None):
    rep = {"applied": [], "stale": [], "replaced_osm": 0, "closure_lines": []}
    yard = shapely.union_all([it["poly"] for it in paved]) if paved else None
    nodes = {n["id"]: n for n in graph["nodes"]}
    for o in overrides:
        if o.get("kind") != "depot_gate":
            continue
        nd = nodes.get(o["node"])
        if nd is None:
            rep["stale"].append(o["id"])
            continue
        ox, oy = origin
        xy = np.array([nd["x"] - ox, nd["y"] - oy])
        main = _chain_at_node(net, xy, o["depot_way"])
        lanes = [_chain_at_node(net, xy, w) for w in (o["entry_way"], o["exit_way"])]
        if main is None or any(x is None for x in lanes) or main[0] > 25 or any(x[0] > 25 for x in lanes):
            rep["stale"].append(o["id"])
            continue
        # replace OSM barrier points around the split
        rr = o.get("replace_radius_m", 25.0)
        keep = []
        for it in pl.items:
            if it["p"] in ("lift_gate", "sliding_gate") and math.hypot(it["e"] - xy[0], it["n"] - xy[1]) < rr:
                rep["replaced_osm"] += 1
                continue
            keep.append(it)
        pl.items[:] = keep
        src = f"override:{o['id']}"
        # --- median between the lanes: first station (from the node) where the lanes' kerbs are >= 0.8 m apart
        (_, ce, se, ge), (_, cx, sx, gx) = lanes
        dd = np.arange(3.0, 70.0, 0.5)
        pe = ce.line.offset_point(se + ge * dd, 0.0)
        px = cx.line.offset_point(sx + gx * dd, 0.0)
        hwe = ce.hw_at(se + ge * dd)
        hwx = cx.hw_at(sx + gx * dd)
        gap = np.hypot(*(pe - px).T) - hwe - hwx - 2 * S.KERB_TOP_W
        ok = np.nonzero(gap >= o.get("median_min_w", 0.8))[0]
        if not len(ok):
            rep["stale"].append(o["id"] + ":median")
            continue
        k = min(ok[0] + int(o.get("barrier_past_nose_m", 3.0) / 0.5), len(dd) - 1)
        m = 0.5 * (pe[k] + px[k])
        free = shapely.union_all([roads_poly.buffer(0.3), bpoly.buffer(0.8)])
        # --- raised kerbed island under the two housings (r11): the median between the kerb backs, ISLAND_BEFORE_M
        #     before to ISLAND_AFTER_M after the housing line (WORKING_VALUE: no open photo of the gate, ADR 0071)
        isl_z = None
        isl_poly = None
        if o.get("island", True):
            j0 = max(int(ok[0]), k - int(ISLAND_BEFORE_M / 0.5))
            j1 = min(len(dd) - 1, k + int(ISLAND_AFTER_M / 0.5))
            u = px[j0:j1 + 1] - pe[j0:j1 + 1]
            u /= np.maximum(np.hypot(*u.T), 1e-9)[:, None]
            P_e = pe[j0:j1 + 1] + u * (hwe[j0:j1 + 1] + S.KERB_TOP_W - 0.03)[:, None]
            P_x = px[j0:j1 + 1] - u * (hwx[j0:j1 + 1] + S.KERB_TOP_W - 0.03)[:, None]
            s_k = se + ge * dd[k]
            lat_k = float(ce.line.project(pe[k] + u[k - j0] * hwe[k])[1])
            z_lane = max(float(ce.crossfall_z(s_k, lat_k)), float(lin.z(m[None, :])[0]))
            isl_poly, isl_z = _island(lin, P_e, P_x, z_lane, f"{src}:island")
            if isl_poly is None:
                rep["stale"].append(o["id"] + ":island")
        # --- barriers: housing on the median kerb, boom over each lane, raised (MA-003)
        bars = []
        wear_cases = []
        strips = {}
        clos = {}
        for (c, s0, g), name in (((ce, se, ge), "entry"), ((cx, sx, gx), "exit")):
            s = s0 + g * dd[k]
            p_c = c.line.offset_point(s, 0.0)
            across = p_c - m
            across /= max(np.hypot(*across), 1e-9)
            hw = float(c.hw_at(s))
            base = p_c - across * (hw + S.KERB_TOP_W + 0.3)
            # automatic barrier (MA-003): static housing + the boom as its own instance in the hinge frame; the engine
            # turns the boom into a Game.World.DepotBarrier (opens for an approaching vehicle, solid when closed)
            yaw_b = math.atan2(across[1], across[0])
            on_island = isl_poly is not None and isl_poly.contains(Point(*base))
            zb = pl.add("barrier_base", base, yaw_b,
                        z=isl_z if on_island else None, src=f"{src}:{name}", group="barrier")
            if on_island:      # saw-cut presence / safety loops before and after the boom
                lat_h = float(c.line.project(base)[1])
                appr = g if name == "entry" else -g
                _loop(lin.buf, c, s + appr * 3.4, g, lat_h, f"loop:{src}:{name}:a")
                _loop(lin.buf, c, s - appr * 1.9, g, lat_h, f"loop:{src}:{name}:b")
            side_y = np.array([-math.sin(yaw_b), math.cos(yaw_b)])            # prototype +y in E, N
            t_lane = c.line.frame(s)[0] * g                                   # away from the split node along the lane
            travel_dir = t_lane if name == "exit" else -t_lane                # entry traffic runs toward the node
            wear_cases.append({"chain": c, "station": s, "travel": travel_dir, "name": name, "src": src})
            pl.add("barrier_boom", base + side_y * LP.BOOM_SIDE, yaw_b, z=zb + LP.BOOM_HINGE[2], src=f"{src}:{name}:boom")
            pl.items[-1]["barrier"] = {"L": LP.BOOM_L, "open_deg": LP.BOOM_OPEN_DEG, "lane": name,
                                       "travel": 1.0 if float(np.dot(travel_dir, side_y)) >= 0 else -1.0}
            bars.append((c, s, g, across, hw))
            # r12: raised strip under the rest post on the outer side of the lane + the closure line to the plot edge
            scfg = (o.get("side_strips") or {}).get(name)
            if scfg and on_island:
                rest = base + across * (LP.BOOM_L - 0.25) + side_y * LP.BOOM_SIDE
                lat_sign = 1.0 if float(np.dot(c.line.offset_point(s, 1.0) - c.line.offset_point(s, 0.0), across)) > 0 else -1.0
                sp, szl, s_out = _side_strip(lin, c, s, g, lat_sign, scfg, roads_poly, rest, f"{src}:strip:{name}")
                if sp is None:
                    rep["stale"].append(f"{o['id']}:strip:{name}")
                else:
                    strips[name] = {"poly": sp, "zlane": szl, "rest_on_strip": bool(sp.buffer(-0.1).contains(Point(*rest))),
                                    "t": c.line.frame(s)[0]}
                    ccfg = (o.get("closure") or {}).get(name)
                    if ccfg and yard is not None:
                        a0 = p_c + across * (s_out - 0.25)
                        ln, why = _closure(lin, a0, across, ccfg, yard, roads_poly, bpoly, f"{src}:closure:{name}")
                        if ln is None:
                            rep["stale"].append(f"{o['id']}:closure:{name}:{why}")
                        else:
                            clos[name] = {"style": ccfg.get("style", "bollards"), "m": round(float(ln.length), 1), "ends": why}
                            rep["closure_lines"].append([[round(float(v), 2) for v in q] for q in ln.coords])
            # oil stains where vehicles wait in front of the boom (approach side)
            for mm_ in range(2):
                s_w = s + (g if name == "entry" else -g) * (2.5 + mm_ * 1.7)
                P0 = c.line.offset_point(s_w, 0.15 * (mm_ - 0.5))

                def z_of(V2, c=c):
                    out = []
                    for q in V2:
                        ss, ll = c.line.project(q)
                        out.append(float(c.crossfall_z(ss, np.clip(ll, -c.hw_at(ss), c.hw_at(ss)))) + DC.LIFT_OIL)
                    return np.array(out)
                DC.stain(lin.buf, P0, z_of, 0.35, (o["id"], name, mm_), f"oil:{src}:{name}:{mm_}")
        # --- sliding gate across the two-way road, inside the depot
        _, c2, s2, g2 = main
        sg = s2 + g2 * o.get("gate_offset_m", 14.0)
        t, nn = c2.line.frame(sg)
        hw2 = float(c2.hw_at(sg))
        # gate_side is relative to the direction into the depot; lateral offsets below are in the chain frame
        side = (1.0 if o.get("gate_side", "left") == "left" else -1.0) * g2
        # gate posts outside the carriageway AND its kerb / sidewalk (the gate closes the whole access)
        ext = {sd: side_extent(*side_params(c2, "L" if sd > 0 else "R", sg)) for sd in (1.0, -1.0)}
        ow = {sd: hw2 + ext[sd] + 0.3 for sd in (1.0, -1.0)}
        open_w = ow[side]
        post = c2.line.offset_point(sg, side * open_w)
        # leaf behind the fence line (depot side), +x of the prototype = closing direction (toward the road)
        into = t * g2
        if o.get("sliding_gate", True):
            pl.add("cantilever_gate", post + into * 0.25, math.atan2(-side * nn[1], -side * nn[0]), src=f"{src}:gate",
                   group="gate")
        # --- gatehouse: just inside the fence next to the gate post opposite the gate leaf, glazed side to the
        #     road; fallback: beside the entry lane before the barrier
        def box_at(ctr, along):
            bx_ = shapely.affinity.rotate(shapely.box(-1.9, -1.3, 1.9, 1.3), math.atan2(along[1], along[0]),
                                          origin=(0, 0), use_radians=True)
            return shapely.affinity.translate(bx_, *ctr)
        cands = []
        for ins, off in ((3.0, 1.6), (4.5, 1.6), (3.0, 3.0), (6.0, 2.5)):
            ctr = c2.line.offset_point(sg + g2 * ins, -side * (ow[-side] + 0.4 + off))
            cands.append((ctr, c2.line.offset_point(sg + g2 * ins, 0.0) - ctr, t))
        c, s_b, g, across, hw = bars[0]
        for back, off in ((5.0, 0.0), (8.0, 0.0), (5.0, 1.5), (11.0, 1.0)):
            s = s_b + g * back
            lat_sign = 1.0 if float(np.dot(c.line.offset_point(s, 1.0) - c.line.offset_point(s, 0.0), across)) > 0 else -1.0
            ext = side_extent(*side_params(c, "L" if lat_sign > 0 else "R", s))
            ctr = c.line.offset_point(s, lat_sign * (hw + ext + 1.6 + off))
            cands.append((ctr, -across, c.line.frame(s)[0]))
        placed = None
        for ctr, face, along in cands:
            if not free.intersects(box_at(ctr, along)):
                placed = (ctr, face / max(np.hypot(*face), 1e-9))
                break
        if placed is not None:
            pl.add("gatehouse", placed[0], _yaw(placed[1]), src=src, group="gatehouse")
        else:
            rep["stale"].append(o["id"] + ":gatehouse_no_space")
        # --- fence returns from both gate posts along the gate line
        flen = o.get("fence_return_m", 30.0)
        cutter = shapely.union_all([roads_poly.buffer(0.4), bpoly.buffer(0.5)])
        total = 0.0
        for sd in ((1.0, -1.0) if o.get("fence", True) else ()):
            a = c2.line.offset_point(sg, sd * (ow[sd] + 0.4))
            b = c2.line.offset_point(sg, sd * (ow[sd] + 0.4 + flen))
            line = LineString([a, b])
            g = line.difference(cutter)
            parts = [p for p in getattr(g, "geoms", [g]) if p.geom_type == "LineString" and p.length > 2.0]
            # keep only the piece attached to the gate post (a fence does not jump over a road)
            parts = [p for p in parts if p.distance(Point(*a)) < 1.0]
            for part in parts:
                P = lin.dens(part, 1.0)
                Z = lin.z(P)
                lin.slab("concrete_plinth", P, Z - 0.2, Z + S.FENCE_PLINTH_H, 0.05, src)
                lin.ribbon("fence_anthracite_mesh", P, Z + S.FENCE_PLINTH_H, Z + S.FENCE_H, 0.0, src, both=True,
                           collision="collision_fence")
                lin.posts("fence_anthracite", P, S.FENCE_PANEL_W, 0.06, 0.04, S.FENCE_H + 0.05, src=src)
                total += part.length
        # gate posts (0.12 m steel) at both sides of the opening
        for sd in ((1.0, -1.0) if o.get("fence", True) or o.get("sliding_gate", True) else ()):
            p = c2.line.offset_point(sg, sd * (ow[sd] + 0.2))
            P = np.array([p, p + into * 0.01])
            lin.posts("fence_anthracite", P, 1.0, 0.14, 0.14, S.FENCE_H + 0.25, src=src)
        if isl_poly is not None:
            # yellow steel bollards at both noses of the island (protect the housings from a cut corner)
            ex = np.asarray(isl_poly.exterior.coords)
            t_m = ce.line.frame(se + ge * dd[k])[0]
            n_m = np.array([-t_m[1], t_m[0]])
            a_ = (ex - m) @ t_m
            for a0 in (a_.min() + 0.55, a_.max() - 0.55):         # on the island's centre line, 0.55 m from each end
                cut = isl_poly.intersection(LineString([m + t_m * a0 - n_m * 6.0, m + t_m * a0 + n_m * 6.0]))
                if cut.is_empty:
                    continue
                q = np.asarray(cut.centroid.coords[0])
                _bollard(lin.buf, q, t_m, isl_z, f"{src}:bollard")
            # r12: tyre rub on the kerb noses of the island and of the side strips
            scuff = 0
            if o.get("scuffs", True):
                scuff += _scuffs(lin.buf, isl_poly, lambda R: np.full(len(R), isl_z - ISLAND_H), t_m, (o["id"], "isl"),
                                 f"scuff:{src}:island")
                for nm, st_ in strips.items():
                    scuff += _scuffs(lin.buf, st_["poly"], st_["zlane"], st_["t"], (o["id"], nm), f"scuff:{src}:{nm}")
            rep["scuff_tris"] = scuff
            # asphalt repair patches hashed onto the lanes right at the booms sat under the loops like pasted
            # rectangles (review A6): none within 14 m of the housing line
            keep = [p_ for p_ in lin.buf.parts
                    if not (p_.mat == "decal_patch" and float(np.hypot(*(p_.V[:, :2].mean(axis=0) - m))) < 14.0)]
            rep["patches_removed_at_gate"] = len(lin.buf.parts) - len(keep)
            lin.buf.parts[:] = keep
        from .gate_wear import emit as paired_tyre_tracks
        paired_tyre_tracks(lin.buf, wear_cases, (graph["bbox"][2]-graph["bbox"][0])*.5,
                           [isl_poly]+[st_["poly"] for st_ in strips.values()], rep)
        rep["applied"].append({"id": o["id"], "node": o["node"], "fence_m": round(total, 1),
                               "island_m2": round(float(isl_poly.area), 1) if isl_poly is not None else 0.0,
                               "gatehouse": [round(float(v), 2) for v in placed[0]] if placed is not None else None,
                               "barrier_median_w": round(float(gap[k]), 2),
                               "side_strips": {nm: {"m2": round(float(v["poly"].area), 1), "rest_on_strip": v["rest_on_strip"]}
                                               for nm, v in strips.items()},
                               "closure": clos})
    report["gates"] = rep
    return rep


def no_parking(report, margin=1.6):
    """Polygons round the closure lines of the gates (r12): the parking rule lays no bay across a fence / post line."""
    return [LineString(c).buffer(margin, cap_style="flat") for c in (report.get("gates") or {}).get("closure_lines", [])]
