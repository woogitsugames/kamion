"""Authored overrides for objects the data does not describe well enough (Data/Regions/<id>/overrides.yaml):

  kind: sign_gantry   overhead direction boards on a lattice gantry across a one-way carriageway, `distance_m`
                      before the node `before_node` on OSM way `osm_way`; boards = [{lanes: [i, ...] (0 = left
                      lane in the direction of travel), rows: [[[refs], destination], ...]}]. Board faces are our
                      own schematic drawings (signs.overhead_board); bottom edge 5.20 m above the road
                      (>= 5.00 m, Tabl. 1.11 [ZNAKI-Z1], standards.SIGN_H_OVERHEAD).
  kind: landmark      distant landmark (chimney) taken from OSM with its tags copied into the override (the object
                      lies outside the tile bbox, so the regular OSM extract does not contain it).
Both are reported in streetscape QA (`landmarks`) with stale entries listed, never dropped silently.
"""

from __future__ import annotations

import hashlib
import math

import numpy as np

from roads import standards as S
from roads.markings import lane_layout
from roads.network import side_extent, side_params

from . import life_props as LP
from . import signs as SG


def _yaw(f):
    return math.atan2(f[1], f[0]) - math.pi / 2


def _chain(net, way, xy):
    best = None
    for c in net.chains:
        if c.meta.get("absorbed") or not any(str(e).startswith(f"w{way}:") for e, _ in c.edges):
            continue
        s, lat = c.line.project(xy)
        d = abs(lat)
        if best is None or d < best[0]:
            best = (d, c, float(s))
    return best


def build(pl, net, graph, overrides, origin, boards, report):
    rep = {"gantries": [], "landmarks": [], "stale": []}
    nodes = {n["id"]: n for n in graph["nodes"]}
    ox, oy = origin
    for o in overrides:
        if o.get("kind") == "sign_gantry":
            nd = nodes.get(o["before_node"])
            hit = _chain(net, o["osm_way"], np.array([nd["x"] - ox, nd["y"] - oy])) if nd else None
            if hit is None or hit[0] > 15:
                rep["stale"].append(o["id"])
                continue
            _, c, s_node = hit
            dirn = int(c.dirn[c.idx(s_node)]) or 1
            s = s_node - dirn * o["distance_m"]
            if not (0 < s < c.length):
                rep["stale"].append(o["id"])
                continue
            sec = c.section(s, net.sec_list)
            hw = float(c.hw_at(s))
            _, _, lanes = lane_layout(sec, hw, dirn)
            cen = lanes["fwd"]
            t, _ = c.line.frame(s)
            travel = t * dirn
            # columns outside the carriageway and its side strips
            lat_l = hw + side_extent(*side_params(c, "L", s)) + 1.0
            lat_r = -(hw + side_extent(*side_params(c, "R", s)) + 1.0)
            span = round(lat_l - lat_r)
            z = float(c.crossfall_z(s, 0.0))
            items = []
            hmax = 0.0
            for bd in o["boards"]:
                rows = [(list(r[0]), r[1]) for r in bd["rows"]]
                key = "OB_" + hashlib.sha1(repr(rows).encode()).hexdigest()[:8]
                if key not in boards:
                    im, wm, hm = SG.overhead_board(rows)
                    boards[key] = (round(wm, 3), round(hm, 3), im)
                wm, hm, _ = boards[key]
                hmax = max(hmax, hm)
                lat = float(np.mean([cen[i] for i in bd["lanes"] if i < len(cen)]))
                items.append((key, lat, hm))
            H = round(S.SIGN_H_OVERHEAD + 0.2 + hmax + 0.15, 1)
            LP.GANTRIES.add((int(span), int(round(H * 10))))
            ctr = c.line.offset_point(s, 0.5 * (lat_l + lat_r))
            pl.add(f"sign_gantry_{int(span)}_{int(round(H * 10))}", ctr, _yaw(-travel), z=z, src=f"override:{o['id']}")
            for key, lat, hm in items:
                p = c.line.offset_point(s, lat) - travel * 0.45
                pl.add(f"board_{key}", p, _yaw(-travel), z=z + S.SIGN_H_OVERHEAD + 0.2 + hm / 2,
                       src=f"override:{o['id']}")
            rep["gantries"].append({"id": o["id"], "span_m": int(span), "height_m": H,
                                    "at": [round(float(v), 1) for v in ctr]})
        elif o.get("kind") == "landmark":
            x, y = o["epsg2180"]
            p = np.array([x - ox, y - oy])
            name = f"landmark_chimney_{int(o['height_m'])}_{int(round(o['base_d_m'] * 10))}"
            LP.LANDMARKS[name] = (float(o["height_m"]), float(o["base_d_m"]), float(o["top_d_m"]))
            pl.add(name, p, 0.0, src=f"override:{o['id']}")
            rep["landmarks"].append({"id": o["id"], "proto": name, "at": [round(float(v), 1) for v in p]})
    report["landmarks"] = rep
    return rep
