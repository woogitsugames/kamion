"""Authored overrides for objects the data does not describe well enough (Data/Regions/<id>/overrides.yaml):

  kind: sign_gantry   overhead direction boards on a lattice gantry across a one-way carriageway, `distance_m`
                      before the node `before_node` on OSM way `osm_way`; boards = [{lanes: [i, ...] (0 = left
                      lane in the direction of travel), rows: [[[refs], destination], ...] | from_osm: [{way,
                      refs_extra}]}] (from_osm: OSM destination / destination:ref of that way, ADR 0069).
                      `form: cantilever` (ADR 0069): one column on `column_side` (L / R of travel, `column_offset_m`
                      behind the carriageway side strip) and a lattice arm over the boards. Board faces are our
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
from . import ec_chimneys as EC


def _yaw(f):
    return math.atan2(f[1], f[0]) - math.pi / 2


def _chains(net, way, xy):
    """Chains of OSM way `way` near xy, nearest first: [(lateral distance, chain, s)]. A node shared by two chains
    of the same way (p37: node 1852129066) is tried on both (ADR 0069)."""
    out = []
    for c in net.chains:
        if c.meta.get("absorbed") or not any(str(e).startswith(f"w{way}:") for e, _ in c.edges):
            continue
        s, lat = c.line.project(xy)
        out.append((abs(lat), c, float(s)))
    return sorted(out, key=lambda t: t[0])


def _board_rows(graph, bd, rep, oid):
    """Board rows [(refs, destination)]: explicit `rows`, or `from_osm` = [{way, refs_extra?}] read from the OSM
    destination / destination:ref tags of that way in the road graph (ADR 0069). Names split on ';'; refs pair with
    names from the end (fewer refs than names), all on the first row when there are more refs; `refs_extra` (E-route / DK numbers of the route
    relations, which the graph does not keep) go first on the first row."""
    if "rows" in bd:
        return [(list(r[0]), r[1]) for r in bd["rows"]]
    rows = []
    for spec in bd["from_osm"]:
        ed = next((e for e in graph["edges"] if e.get("osm_way") == spec["way"] and "destination" in e["attrs"]), None)
        if ed is None:
            if rep is not None:
                rep["stale"].append(f"{oid}:way{spec['way']}")
            continue
        names = [n.strip() for n in str(ed["attrs"]["destination"]["v"]).split(";") if n.strip()]
        refs = [r.strip() for r in str(ed["attrs"].get("destination:ref", {}).get("v", "")).split(";") if r.strip()]
        extra = [str(r) for r in spec.get("refs_extra", [])]
        off = len(names) - len(refs)                # fewer refs than names: they belong to the last names
        for i, n in enumerate(names):               # (OSM order: "Warszawa;Ełk" + "65" -> 65 on the Ełk row, p37)
            rr = [refs[i - off]] if 0 <= i - off < len(refs) else (refs if off < 0 and i == 0 else [])
            rows.append(((extra if i == 0 else []) + rr, n))
    return rows


def build(pl, net, graph, overrides, origin, boards, report):
    rep = {"gantries": [], "landmarks": [], "stale": []}
    nodes = {n["id"]: n for n in graph["nodes"]}
    ox, oy = origin
    for o in overrides:
        if o.get("kind") == "sign_gantry":
            nd = nodes.get(o["before_node"])
            hit = None
            for d_, c, s_node in (_chains(net, o["osm_way"], np.array([nd["x"] - ox, nd["y"] - oy])) if nd else []):
                if d_ > 15:
                    break
                dirn = int(c.dirn[c.idx(s_node)]) or 1
                s = s_node - dirn * o["distance_m"]
                if 0 < s < c.length:
                    hit = (c, s, dirn)
                    break
            if hit is None:
                rep["stale"].append(o["id"])
                continue
            c, s, dirn = hit
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
                rows = _board_rows(graph, bd, rep, o["id"])
                key = "OB_" + hashlib.sha1(repr(rows).encode()).hexdigest()[:8]
                if key not in boards:
                    im, wm, hm = SG.overhead_board(rows)
                    boards[key] = (round(wm, 3), round(hm, 3), im)
                wm, hm, _ = boards[key]
                hmax = max(hmax, hm)
                lat = float(np.mean([cen[i] for i in bd["lanes"] if i < len(cen)]))
                items.append((key, lat, hm))
            H = round(S.SIGN_H_OVERHEAD + 0.2 + hmax + 0.15, 1)
            yaw = _yaw(-travel)
            if o.get("form") == "cantilever":
                # one column beside the carriageway (column_side relative to travel), lattice arm over the lanes
                # (ADR 0069, Mapillary p37). Local +x of the prototype = left of travel; the arm of an "L" column
                # reaches to the right (-x).
                tl = 1.0 if dirn > 0 else -1.0                 # chain lateral sign of the travel-left side
                left = o.get("column_side", "R") == "L"
                csd = ("L" if tl > 0 else "R") if left else ("R" if tl > 0 else "L")
                csg = 1.0 if csd == "L" else -1.0
                lat_c = csg * (hw + side_extent(*side_params(c, csd, s)) + float(o.get("column_offset_m", 1.0)))
                reach = max(abs(lat_c - lat) + boards[key][0] / 2 for key, lat, _ in items) + 0.3
                reach = int(math.ceil(reach))
                LP.CANTILEVERS.add(("L" if left else "R", reach, int(round(H * 10))))
                q = c.line.offset_point(s, lat_c)
                pl.add(f"sign_cantilever_{'L' if left else 'R'}{reach}_{int(round(H * 10))}", q, yaw, z=z,
                       src=f"override:{o['id']}")
                pl.add("gantry_footing", q, yaw, z=z, src=f"override:{o['id']}")
                ctr, span = q, reach
            else:
                LP.GANTRIES.add((int(span), int(round(H * 10))))
                ctr = c.line.offset_point(s, 0.5 * (lat_l + lat_r))
                pl.add(f"sign_gantry_{int(span)}_{int(round(H * 10))}", ctr, yaw, z=z, src=f"override:{o['id']}")
                for sx in (-1, 1):            # column footings + colliders (local x of the gantry = (cos yaw, sin yaw))
                    q = ctr + np.array([math.cos(yaw), math.sin(yaw)]) * sx * int(span) / 2
                    pl.add("gantry_footing", q, yaw, z=z, src=f"override:{o['id']}")
            for key, lat, hm in items:
                p = c.line.offset_point(s, lat) - travel * 0.45
                pl.add(f"board_{key}", p, _yaw(-travel), z=z + S.SIGN_H_OVERHEAD + 0.2 + hm / 2,
                       src=f"override:{o['id']}")
            rep["gantries"].append({"id": o["id"], "form": o.get("form", "portal"), "span_m": int(span), "height_m": H,
                                    "at": [round(float(v), 1) for v in ctr],
                                    "boards": [{"key": k, "rows": [[r[0], r[1]] for r in _board_rows(graph, bd, None, o["id"])]}
                                               for (k, _, _), bd in zip(items, o["boards"])],
                                    "mapillary": o.get("mapillary", [])})
        elif o.get("kind") == "landmark":
            x, y = o["epsg2180"]
            p = np.array([x - ox, y - oy])
            authored = EC.active(o, origin)
            if authored is not None:
                # The matching hero plan adds this instance and its measured
                # triangle counts later; do not also register a generic cone.
                rep["landmarks"].append({"id": o["id"], "proto": authored["prototype"],
                                         "at": [round(float(v), 1) for v in p], "authored": True})
                continue
            name = f"landmark_chimney_{int(o['height_m'])}_{int(round(o['base_d_m'] * 10))}"
            LP.LANDMARKS[name] = (float(o["height_m"]), float(o["base_d_m"]), float(o["top_d_m"]))
            pl.add(name, p, 0.0, src=f"override:{o['id']}")
            rep["landmarks"].append({"id": o["id"], "proto": name, "at": [round(float(v), 1) for v in p]})
    report["landmarks"] = rep
    return rep
