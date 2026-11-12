"""Vertical signs from OSM `traffic_sign` tags, roundabout signing and the sign audit of the start route (v3.4).

Rules (rozporządzenie w sprawie szczegółowych warunków technicznych dla znaków i sygnałów drogowych, Dz.U. 2019
poz. 2311 = [ZNAKI-Z1], Załącznik 1 (A-D) and 4 (E); placement distances WORKING_VALUE until checked against the
tables of [ZNAKI-Z1]):
  osm          node `traffic_sign=PL:<code>[;PL:<code>]` (values like `PL:B-33[40]`, `PL:A-7,B-33[50]`,
               `PL:B-1`), facing from `direction` / `traffic_sign:direction` (`forward` / `backward` along the nearest
               chain, or degrees clockwise from north = the direction the traffic travels); `highway=give_way` / `stop`
               nodes with a `direction` that the junction rule did not cover (> 25 m from a junction centre) get A-7 /
               B-20. Codes without a face of our own are reported (`unknown`), never invented.
  roundabout   every entry: A-7 + C-12 (junction_signs, unchanged) and C-9 on the splitter island when the entry is
               a separate one-way carriageway; every exit to a public road: an E-2a style board facing the ring
               traffic with the destinations of the exit (OSM `destination`, else route shields + street name).
  diagram      on GP/G entries of roundabouts with a ring radius >= 18 m (Putry, Bieżeństwa): an E-1 style
               diagram board ("tablica przeddrogowskazowa") 80 m before the ring: the ring with every arm at its
               real bearing, destinations at the arm ends.
  audit        route_signs in streetscape_qa.json: every sign within 12 m of the start route, by route chainage,
               and route_checks: roundabout entries on the route without A-7 / C-12, chains on the route with a
               limit != 50 km/h without a B-33 within 80 m after the junction.
Board colours follow the existing generator (green with red route shields where a national road number is signed,
white with black text for local destinations); our own schematic drawing, not the official typeface.
"""

from __future__ import annotations

import math
import re

import numpy as np

from roads import standards as S
from roads.network import RURAL

from . import furniture as FU
from . import signs as SG

CODE_RE = re.compile(r"([A-GPT]-\d+[a-z]?)(?:\[([^\]]+)\])?")
DIAGRAM_BEFORE_M = 80.0         # WORKING_VALUE (urban GP/G approach)
EXIT_BOARD_AFTER_M = 7.0        # board on the exit, metres after the ring edge, WORKING_VALUE
MIN_RING_R_DIAGRAM = 18.0
DIAGRAM_MIN_M = 40.0            # shorter approach chains (split by nodes) carry the board at L - 10 m, >= 40 m


def parse_traffic_sign(v):
    """'PL:B-33[40];PL:A-7' / 'PL:A-7,B-33[50]' -> ['B-33_40', 'A-7'] (only PL: or bare codes)."""
    out = []
    if not v:
        return out
    for part in re.split(r"[;,]", v):
        part = part.strip()
        if ":" in part:
            cc, part = part.split(":", 1)
            if cc.strip().upper() != "PL":
                continue
        m = CODE_RE.fullmatch(part.strip())
        if not m:
            continue
        code, val = m.group(1), m.group(2)
        if code == "B-33" and val and val.isdigit():
            out.append(f"B-33_{int(val)}")
        else:
            out.append(code)
    return out


def _bearing_dir(deg):
    a = math.radians(float(deg))
    return np.array([math.sin(a), math.cos(a)])


def osm_signs(pl, net, src, origin, juncs, report, codes):
    """Signs mapped in OSM (nodes). Returns nothing; report["osm_signs"] = counts."""
    rep = {"placed": {}, "unknown": {}, "skipped_far": 0, "give_way_stop": 0}
    centres = [j.center if j.center is not None else np.mean([net.nodes[n]["xy"] for n in j.nodes], axis=0)
               for j in juncs]
    for nd in src["osm"]["nodes"]:
        t = nd["tags"]
        hw = t.get("highway")
        plates = parse_traffic_sign(t.get("traffic_sign"))
        if not plates and hw in ("give_way", "stop") and t.get("direction") in ("forward", "backward"):
            q = np.asarray(nd["geometry"]["coordinates"], float) - origin
            if any(np.hypot(*(q - c)) < 25.0 for c in centres):
                continue                      # junction_signs already signs it (A-7 / B-20 on the minor arm)
            plates = ["A-7" if hw == "give_way" else "B-20"]
            rep["give_way_stop"] += 1
        if not plates:
            continue
        known = [c for c in plates if c in SG.KNOWN or c.startswith("B-33_")]
        for c in plates:
            if c not in known:
                rep["unknown"][c] = rep["unknown"].get(c, 0) + 1
        if not known:
            continue
        q = np.asarray(nd["geometry"]["coordinates"], float) - origin
        hit = FU.nearest_chain(net, q, 15.0)
        if not hit:
            rep["skipped_far"] += 1
            continue
        _, c, s, lat = hit
        tang, _ = c.line.frame(s)
        d = t.get("traffic_sign:direction") or t.get("direction")
        if d in ("forward", "backward"):
            travel = tang * (1 if d == "forward" else -1)
        elif d is not None and re.fullmatch(r"-?\d+(\.\d+)?", str(d)):
            travel = _bearing_dir(d)
        else:                                  # no direction: right-hand traffic on the side the node is mapped on
            travel = tang if lat < 0 else -tang
        dn = 1 if np.dot(travel, tang) >= 0 else -1
        side_sgn = -1.0 * dn                    # right of travel
        kind, h, w, ext = FU.side_surface_offset(c, "R" if dn > 0 else "L", s)
        off = float(c.hw_at(s)) + (S.KERB_TOP_W + S.SIGN_LATERAL if kind != RURAL else ext + 0.5)
        p = c.line.offset_point(s, side_sgn * off)
        if pl.near("sign", p, 1.5):
            continue
        for cd in FU.sign_assembly(pl, p, -travel, known, f"osm:node/{nd['osm_node']}", sidewalk=w > 0.5):
            codes.add(cd)
            rep["placed"][cd] = rep["placed"].get(cd, 0) + 1
        pl.pts.setdefault("sign", []).append((p[0], p[1]))
    report["osm_signs"] = rep


def _attrs_at(net, graph_attrs, c, s):
    sec = c.section(float(np.clip(s, 0.5, c.length - 0.5)), net.sec_list)
    return graph_attrs.get(sec.edge_id, {})


def _arm_label(net, graph_attrs, arm):
    """(destinations, route refs, street name) of the road leaving through this arm."""
    a = _attrs_at(net, graph_attrs, arm.chain, float(arm.s(min(8.0, arm.L / 2))))
    dest = (a.get("destination") or {}).get("v") or ""
    ref = (a.get("ref") or {}).get("v") or ""
    name = (a.get("name") or {}).get("v") or ""
    refs = [r.strip() for r in ref.split(";") if r.strip()]
    dests = [x.strip() for x in dest.split(";") if x.strip()]
    return dests, refs, name


SHORT = {"Aleja Tysiąclecia Państwa Polskiego": "Al. Tysiąclecia", "Generała Władysława Andersa": "Andersa",
         "Generała Stanisława Maczka": "Maczka"}


def _short(name):
    if name in SHORT:
        return SHORT[name]
    for p in ("Generała ", "Rondo "):
        if name.startswith(p):
            name = name[len(p):]
    return name


def _ring_fit(net, j):
    """(centre, radius) of the ring through junction j (see _ring_radius)."""
    pts = [c.line.p for c in net.chains if c.roundabout and np.min(np.hypot(*(c.line.p - j.center).T)) < 60.0]
    P = np.concatenate(pts)
    A = np.column_stack([2 * P[:, 0], 2 * P[:, 1], np.ones(len(P))])
    (cx, cy, c0), *_ = np.linalg.lstsq(A, (P ** 2).sum(1), rcond=None)
    return np.array([cx, cy]), float(math.sqrt(max(c0 + cx * cx + cy * cy, 0.0)))


def _ring_arms(net, juncs, j):
    """Non-ring arms of every junction node on the same ring as j."""
    c, r = _ring_fit(net, j)
    out = []
    for k in juncs:
        if k.roundabout and k.center is not None and abs(np.hypot(*(k.center - c)) - r) < 15.0:
            out += [a for a in k.arms if not a.is_ring()]
    return out


def _ring_radius(net, j):
    """Radius of the ring through this junction: algebraic circle fit of every roundabout chain within 60 m (a ring
    is split into one junction per entry / exit node, so the junction centre is a node on the ring, not its centre)."""
    if j.center is None or not any(a.is_ring() for a in j.arms):
        return 0.0
    pts = [c.line.p for c in net.chains if c.roundabout and np.min(np.hypot(*(c.line.p - j.center).T)) < 60.0]
    if not pts:
        return 0.0
    P = np.concatenate(pts)
    A = np.column_stack([2 * P[:, 0], 2 * P[:, 1], np.ones(len(P))])
    b = (P ** 2).sum(1)
    (cx, cy, c0), *_ = np.linalg.lstsq(A, b, rcond=None)
    return float(math.sqrt(max(c0 + cx * cx + cy * cy, 0.0)))


def _barriers(src, origin):
    """BDOT10k noise barriers (OT_OIKM_L) as one geometry: boards never stand behind them (invisible from the road)."""
    import shapely
    from shapely.geometry import LineString
    ls = [LineString(np.asarray(f["geometry"]["coordinates"], float) - origin) for f in src["bdot10k"].get("OT_OIKM_L", [])]
    g = shapely.union_all(ls) if ls else None
    if g is not None:
        shapely.prepare(g)
    return g


def _in_front_of_barrier(edge, p, barriers, clearance=0.6):
    """p moved toward the carriageway edge point `edge` when a noise barrier crosses the sight line edge -> p."""
    if barriers is None:
        return p, False
    from shapely.geometry import LineString, Point
    seg = LineString([tuple(edge), tuple(p)])
    if not barriers.intersects(seg):
        return p, False
    hit = barriers.intersection(seg)
    dmin = min(Point(edge).distance(g) for g in getattr(hit, "geoms", [hit]))
    v = np.asarray(p, float) - np.asarray(edge, float)
    L = float(np.hypot(*v))
    return np.asarray(edge, float) + v / max(L, 1e-9) * max(0.5, dmin - clearance), True


def roundabout_signs(pl, net, juncs, graph_attrs, report, codes, boards, src=None, origin=None):
    rep = {"c9_islands": 0, "exit_boards": 0, "diagrams": 0, "diagram_at": [], "moved_before_barrier": 0}
    rep["_barriers"] = _barriers(src, origin) if src is not None else None
    for j in juncs:
        if not j.roundabout:
            continue
        arms = [a for a in j.arms if not a.is_ring()]
        radius = _ring_radius(net, j)
        for a in arms:
            dn = a.inbound_dirn()
            cls = a.cls(net.sec_list)
            if cls in ("D",) or a.L < 12:
                continue
            if dn > 0:
                rep.setdefault("entries", []).append({"junction": str(j.id), "cls": cls, "ring_r_m": round(radius, 1),
                                                      "arm_m": round(float(a.L), 1)})
                # C-9 on the splitter island = left of the inbound carriageway, near the entry
                d = 4.0
                if d < a.L - 2 and not a.chain.bridge[a.chain.idx(float(a.s(d)))]:
                    p = a.gutter(d, -1, extra=0.6)
                    if not pl.near("sign", p, 1.5):
                        for cd in FU.sign_assembly(pl, p, a.direction(d), ["C-9"], f"rule:roundabout_island:{j.id}"):
                            codes.add(cd)
                        pl.pts.setdefault("sign", []).append((p[0], p[1]))
                        rep["c9_islands"] += 1
                # E-1 diagram on major approaches of large roundabouts
                if cls in ("GP", "G") and radius >= MIN_RING_R_DIAGRAM and a.L > DIAGRAM_MIN_M + 10:
                    _diagram(pl, net, graph_attrs, j, a, _ring_arms(net, juncs, j), boards, rep)
            elif dn < 0 or dn == 0:
                dests, refs, name = _arm_label(net, graph_attrs, a)
                lines = dests[:2] if dests else ([_short(name)] if name else [])
                if not lines or cls in ("D", "L") and not dests:
                    continue
                d = EXIT_BOARD_AFTER_M
                if d > a.L - 2 or a.chain.bridge[a.chain.idx(float(a.s(d)))]:
                    continue
                # right side of the outbound traffic = left of the outward direction is wrong: outward IS the travel
                kind, h, w, ext = FU.side_surface_offset(a.chain, "R" if a.end == "a" else "L", float(a.s(d)))
                off = S.KERB_TOP_W + 1.0 if kind != RURAL else ext + 1.0
                p, mv = _in_front_of_barrier(a.gutter(d, -1, extra=0.0), a.gutter(d, -1, extra=off), rep["_barriers"])
                rep["moved_before_barrier"] += int(mv)
                if pl.near("sign", p, 2.0):
                    continue
                key = f"E-2a_{FU._h(';'.join(lines) + ','.join(refs)) % 100000:05d}"
                if key not in boards:
                    im, wm, hm = SG.direction_board(lines, refs, green=bool(refs))
                    boards[key] = (round(wm, 3), round(hm, 3), im)
                wm, hm, _ = boards[key]
                face = -a.direction(d)                     # readable by the ring traffic approaching the exit
                src = f"rule:roundabout_exit:{j.id}"
                z = pl.add("sign_post", p, FU.yaw_of(face), sz=S.SIGN_H_MIN + hm, src=src)
                pl.add(f"board_{key}", p, FU.yaw_of(face), z=z + S.SIGN_H_MIN + hm / 2, src=src)
                pl.pts.setdefault("sign", []).append((p[0], p[1]))
                rep["exit_boards"] += 1
    rep.pop("_barriers", None)
    report["roundabout_signs"] = rep


def _diagram(pl, net, graph_attrs, j, entry, arms, boards, rep):
    """E-1 style board before the entry `entry`: arms by bearing relative to the approach (bottom of the board)."""
    approach = -entry.direction(0.0)                   # travel direction toward the ring
    base = math.atan2(approach[1], approach[0])
    seen, items = set(), []
    for a in arms:
        o = a.direction(0.0)
        ang = math.degrees(math.atan2(o[1], o[0]) - base)
        ang = (ang + 180.0) % 360.0 - 180.0             # 0 = straight on, + = left (counter-clockwise)
        dests, refs, name = _arm_label(net, graph_attrs, a)
        if a.inbound_dirn() > 0 and not dests:
            continue                                  # entry carriageway of a pair: the exit arm carries the label
        k = round(ang / 20.0)
        if k in seen:
            continue
        seen.add(k)
        lab = dests[:2] if dests else ([_short(name)] if name else [])
        if abs(ang) > 160 or not lab:
            continue                                  # the approach itself (U-turn) is not signed
        items.append((ang, lab, refs))
    if len(items) < 2:
        return
    key = f"E-1_{FU._h(str(j.id) + str(entry.key)) % 100000:05d}"
    im, wm, hm = SG.roundabout_diagram(sorted(items))
    boards[key] = (round(wm, 3), round(hm, 3), im)
    d = min(DIAGRAM_BEFORE_M, entry.L - 10.0)
    s = float(entry.s(d))
    if entry.chain.bridge[entry.chain.idx(s)]:
        return
    kind, h, w, ext = FU.side_surface_offset(entry.chain, "L" if entry.end == "a" else "R", s)
    off = S.KERB_TOP_W + 1.2 if kind != RURAL else ext + 1.2
    p = entry.gutter(d, +1, extra=off + wm * 0.5)        # right of the inbound traffic
    p, mv = _in_front_of_barrier(entry.gutter(d, +1, extra=0.0), p, rep["_barriers"])
    rep["moved_before_barrier"] += int(mv)
    if pl.near("sign", p, 3.0):
        return
    face = entry.direction(d)                         # toward the approaching driver
    right = np.array([face[1], -face[0]])
    src = f"rule:roundabout_diagram:{j.id}"
    zs = []
    for sx in (-0.35, 0.35):
        zs.append(pl.add("sign_post", p + right * sx * wm, FU.yaw_of(face), sz=S.SIGN_H_MIN + hm, src=src))
    pl.add(f"board_{key}", p, FU.yaw_of(face), z=min(zs) + S.SIGN_H_MIN + hm / 2, src=src)
    pl.pts.setdefault("sign", []).append((p[0], p[1]))
    rep["diagrams"] += 1
    rep["diagram_at"].append([round(float(p[0]), 1), round(float(p[1]), 1)])


def route_audit(items, route_P, net, juncs, report):
    """Signs along the start route (within 12 m of the route polyline) and the rule checks."""
    if route_P is None or len(route_P) < 2:
        report["route_signs"] = []
        return
    from shapely.geometry import LineString, Point
    line = LineString(route_P)
    out = []
    for it in items:
        p = it["p"]
        if not (p.startswith("plate_") or p.startswith("board_")):
            continue
        q = Point(it["e"], it["n"])
        dd = line.distance(q)
        if dd > 12.0:
            continue
        s = line.project(q)
        a = line.interpolate(max(s - 1.0, 0.0))
        b = line.interpolate(min(s + 1.0, line.length))
        tx, ty = b.x - a.x, b.y - a.y
        yaw = it["yaw"]
        fx, fy = -math.sin(yaw), math.cos(yaw)                   # facing (local +y) in (E, N)
        facing_route = (fx * tx + fy * ty) < 0                  # readable by a driver on the route
        out.append({"s_m": round(s, 1), "code": p.split("_", 1)[1], "offset_m": round(dd, 1),
                    "faces_route_driver": bool(facing_route), "src": it.get("src", ""), "e": it["e"], "n": it["n"]})
    out.sort(key=lambda r: r["s_m"])
    report["route_signs"] = out
    # ring junctions on the route (one per ring node); the entry is the first of each ring along the route
    ring_s = sorted(line.project(Point(*j.center)) for j in juncs
                    if j.roundabout and j.center is not None and line.distance(Point(*j.center)) <= 45)
    entries = [s for k, s in enumerate(ring_s) if k == 0 or s - ring_s[k - 1] > 80.0]
    checks = []
    for s in entries:
        j = min((j for j in juncs if j.roundabout and j.center is not None),
                key=lambda j: abs(line.project(Point(*j.center)) - s) + line.distance(Point(*j.center)))
        near = [r for r in out if s - 70 < r["s_m"] < s and r["faces_route_driver"]]
        have = {r["code"] for r in near}
        checks.append({"junction": str(j.id), "s_m": round(s, 1), "A-7": "A-7" in have, "C-12": "C-12" in have,
                       "E-1": any(r["code"].startswith("E-1") and r["faces_route_driver"]
                                  for r in out if s - 140 < r["s_m"] < s)})
    report["route_checks"] = checks
