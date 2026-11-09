"""Depot gate kit (authored override `kind: depot_gate` in Data/Regions/<id>/overrides.yaml).

OSM rarely maps how a depot entrance is built (Kwadrat Park: one lift_gate node beside the road, no fence),
so the kit is an explicit authored override keyed by the OSM node where the two-way access road splits into
one-way entry/exit lanes around an island. It survives every regeneration; a node that disappears from the
graph is reported in the streetscape QA (`gates.stale`), never dropped silently.

The kit (prototypes in streetscape.life_props, fence meshes like streetscape.furniture.fences):
  * gatehouse (portiernia) on the island where it is >= island_min_w wide, glazed side toward the entry lane;
  * one striped boom barrier per lane, housing on the island kerb, boom across the lane (closed position);
  * cantilever sliding gate across the two-way road `gate_offset_m` inside the depot, standing open
    behind the fence on the side given by `gate_side`;
  * panel fence returns (anthracite 3D panels on a concrete plinth) from both gate posts along the gate line,
    up to `fence_return_m`, cut by road surfaces and buildings.
OSM lift_gate / gate nodes within `replace_radius_m` of the split are replaced by the kit (counted in the QA).
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


def build(pl, lin, net, graph, overrides, roads_poly, bpoly, origin, report):
    rep = {"applied": [], "stale": [], "replaced_osm": 0}
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
        # --- barriers: housing on the median kerb, boom across each lane (prototype +x = boom, closed)
        bars = []
        for (c, s0, g), name in (((ce, se, ge), "entry"), ((cx, sx, gx), "exit")):
            s = s0 + g * dd[k]
            p_c = c.line.offset_point(s, 0.0)
            across = p_c - m
            across /= max(np.hypot(*across), 1e-9)
            hw = float(c.hw_at(s))
            base = p_c - across * (hw + S.KERB_TOP_W + 0.3)
            pl.add("barrier_arm", base, math.atan2(across[1], across[0]), src=f"{src}:{name}", group="barrier")
            bars.append((c, s, g, across, hw))
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
        for sd in (1.0, -1.0):
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
        for sd in (1.0, -1.0):
            p = c2.line.offset_point(sg, sd * (ow[sd] + 0.2))
            P = np.array([p, p + into * 0.01])
            lin.posts("fence_anthracite", P, 1.0, 0.14, 0.14, S.FENCE_H + 0.25, src=src)
        rep["applied"].append({"id": o["id"], "node": o["node"], "fence_m": round(total, 1),
                               "gatehouse": [round(float(v), 2) for v in placed[0]] if placed is not None else None,
                               "barrier_median_w": round(float(gap[k]), 2)})
    report["gates"] = rep
    return rep
