"""Road furniture: placement rules (point instances) and linear features (meshed into the chunk GLBs).

Point instances (prototypes in streetscape.props):
  lamps        along GP/G/Z/L/D chains, outer side of one-way carriageways / right side of two-way roads,
               spacing + height by class (standards.LAMP, WORKING_VALUE); OSM highway=street_lamp nodes kept.
  signs        A-7 + C-12 on every roundabout entry; B-20 at OSM highway=stop; A-7 at OSM give_way and on minor
               (Z/L) arms of unsignalised junctions with a higher-class road, D-1 on the major arms there; B-33 at
               the start of every chain with maxspeed != 50 km/h (repeated after each junction, the limit ends
               there); D-6 both sides of unsignalised P-10 crossings; D-15 at bus stops; schematic E-2 boards at
               the start of *_link chains tagged `destination` (green with route shields for numbered roads,
               white for local destinations). Heights: [ZNAKI-Z1] Table 1.11 (standards.SIGN_H_*).
  signals      S-1 heads on every inbound arm of signalised junctions: pole at the right kerb at the stop line;
               approaches with >= 3 lanes also get a cantilever mast over the lanes.
  other        bus shelters (OSM highway=bus_stop, else BDOT10k OT_OIKM_P), lift gates / sliding gates (OSM),
               bollards, benches, bins, power poles (BDOT10k OT_BUWT_P słup energetyczny, OSM power=pole),
               lattice pylons (OSM power=tower).
Linear meshes (layer 'furniture' + 'collision'):
  fences       OSM barrier=fence/yes -> 3D welded panel fence on a concrete plinth; barrier=wall -> prefabricated
               concrete panel fence; cut where they cross a carriageway.
  guard rails  steel W-beam (U-11a family) on bridge caps, on rural medians, and on rural sides where the
               ground falls > GUARDRAIL_EMBANKMENT_H within 4 m of the shoulder.
  noise walls  BDOT10k OT_OIKM_L ekran akustyczny (posts every 4 m, absorptive cassettes on a concrete plinth).
  walls        BDOT10k OT_BUUO_L ściana oporowa / OSM retaining_wall + pedestrian railing (U-12a) on top.
  wires        BDOT10k OT_SULN_L power lines between the poles (catenary sag).
"""

from __future__ import annotations

import hashlib
import math

import numpy as np
import shapely
from shapely.geometry import LineString, Point

from roads import standards as S
from roads.network import MEDIAN_RURAL, RURAL, URBAN, side_params, side_extent

RANK = {"A": 0, "S": 1, "GP": 2, "G": 3, "Z": 4, "L": 5, "D": 6}


def _h(key):
    return int(hashlib.sha1(key.encode()).hexdigest()[:8], 16)


def yaw_of(f):
    """Yaw (rad) that turns local +y onto direction f (E, N)."""
    return math.atan2(f[1], f[0]) - math.pi / 2


class Placer:
    def __init__(self, zsurf):
        self.items = []
        self.zsurf = zsurf
        self.pts = {}

    def near(self, group, p, r):
        for q in self.pts.get(group, []):
            if (q[0] - p[0]) ** 2 + (q[1] - p[1]) ** 2 < r * r:
                return True
        return False

    def add(self, proto, p, yaw, z=None, sz=1.0, src="", group=None):
        z = float(self.zsurf(np.array([p[0]]), np.array([p[1]]))[0]) if z is None else z
        it = {"p": proto, "e": round(float(p[0]), 3), "n": round(float(p[1]), 3), "z": round(z, 3),
              "yaw": round(float(yaw), 4), "src": src}
        if sz != 1.0:
            it["sz"] = round(float(sz), 3)
        self.items.append(it)
        if group:
            self.pts.setdefault(group, []).append((p[0], p[1]))
        return z


def side_surface_offset(c, side, s):
    kind, h, w, depth, mat = side_params(c, side, s)
    return kind, h, w, side_extent(kind, h, w, depth, mat)


# ------------------------------------------------------------------------------------------- carriageway check
GROUND_PROPS = ("lamp_", "sign_post", "signal_pole", "signal_mast", "bollard", "waste_bin", "bench", "power_pole",
                "street_cabinet", "bus_shelter", "pylon")


def clear_carriageway(pl, carriage, zsurf, report):
    """Ground-standing props whose base lies on a carriageway (rule placement near junction patches, OSM nodes
    drawn on the road axis) are pushed 0.8 m beyond the nearest carriageway edge; everything stacked on the same
    base (sign plates) moves with it and keeps its height above the base. Overhead items (signal heads on masts,
    gantry boards, booms) are not touched. Lamp / sign counts on the road were reported by the Unity importer."""
    import shapely
    from shapely.geometry import Point
    from shapely.ops import nearest_points
    inner = carriage.buffer(-0.05)
    shapely.prepare(inner)
    groups = {}
    for it in pl.items:
        groups.setdefault((round(it["e"], 2), round(it["n"], 2)), []).append(it)
    moved, left, drop = 0, [], set()
    for (e, n), items in groups.items():
        base = [it for it in items if it["p"].startswith(GROUND_PROPS)]
        if not base or not inner.contains(Point(e, n)):
            continue
        q = nearest_points(carriage.boundary, Point(e, n))[0]
        v = np.array([q.x - e, q.y - n])
        L = float(np.hypot(*v))
        new = np.array([q.x, q.y]) + (v / L if L > 1e-6 else np.array([1.0, 0.0])) * 0.8
        if inner.contains(Point(*new)):
            left.append({"p": base[0]["p"], "at": [round(e, 1), round(n, 1)], "src": base[0].get("src", "")})
            drop.update(id(it) for it in items)      # a pole in the middle of a lane is worse than a missing one
            continue
        z0 = float(zsurf(np.array([new[0]]), np.array([new[1]]))[0])
        dz = z0 - base[0]["z"]
        for it in items:
            it["e"], it["n"] = round(float(new[0]), 3), round(float(new[1]), 3)
            it["z"] = round(it["z"] + dz, 3)
        moved += 1
    if drop:
        pl.items[:] = [it for it in pl.items if id(it) not in drop]
    report["props_off_carriageway"] = {"moved": moved, "still_on_road": 0, "removed": left[:20]}


# ------------------------------------------------------------------------------------------- lamps
def lamps(pl, net, osm_nodes, origin, report):
    n0 = 0
    for nd in osm_nodes:
        if nd["tags"].get("highway") == "street_lamp":
            x, y = np.asarray(nd["geometry"]["coordinates"]) - origin
            pl.add("lamp_10m", (x, y), 0.0, src=f"osm:node/{nd['osm_node']}", group="lamp")
            n0 += 1
    n = 0
    for c in net.chains:
        if c.meta.get("absorbed") or c.roundabout:
            continue
        sec = c.section(c.length / 2, net.sec_list)
        if sec.cls not in S.LAMP or sec.highway in ("service",) and c.length < 60:
            continue
        spec = S.LAMP[sec.cls]
        # older side-street family (critic R2 #10): one family per street (hash of the chain), never on G/GP;
        # residential streets 65 % old (spun-concrete poles dominate), other L/D roads 30 % (grey steel)
        proto = f"lamp_{int(spec['h'])}m"
        if sec.cls in ("L", "D", "Z") and sec.highway not in ("primary", "secondary", "trunk"):
            u = _h(c.id + ":lampfamily") % 100
            res = sec.highway in ("residential", "living_street")
            if u < (65 if res else 30):
                proto = "lamp_old_concrete_9m" if (res and u < 50) or (not res and u < 8) else "lamp_old_steel_8m"
        oneway = sec.oneway
        sides = ["R"] if (oneway and (c.dirn > 0).mean() >= 0.5) or not oneway else ["L"]
        s0, s1 = c.t_a + 4, c.length - c.t_b - 4
        if s1 - s0 < spec["spacing"] * 0.6:
            continue
        for side in sides:
            sgn = 1.0 if side == "L" else -1.0
            for s in np.arange(s0 + (_h(c.id) % 7), s1, spec["spacing"]):
                kind, h, w, ext = side_surface_offset(c, side, s)
                if kind == MEDIAN_RURAL:
                    continue
                hw = float(c.hw_at(s))
                off = hw + (S.KERB_TOP_W + S.LAMP_OFFSET if kind == URBAN else ext + 0.8)
                p = c.line.offset_point(s, sgn * off)
                if pl.near("lamp", p, spec["spacing"] * 0.45):
                    continue
                t, nn = c.line.frame(s)
                face = -nn * sgn                       # bracket toward the road
                z = None
                if c.bridge[c.idx(s)]:
                    z = float(c.crossfall_z(s, sgn * hw)) + S.BRIDGE_KERB_H
                    p = c.line.offset_point(s, sgn * (hw + S.KERB_TOP_W + 0.6))
                pl.add(proto if z is None else f"lamp_{int(spec['h'])}m", p, yaw_of(face), z=z, src=f"rule:{c.id}",
                       group="lamp")
                n += 1
    report["lamps"] = {"osm": n0, "rule": n,
                       "by_family": {k: sum(1 for it in pl.items if it["p"] == k) for k in
                                     sorted({it["p"] for it in pl.items if it["p"].startswith("lamp_")})}}


# ------------------------------------------------------------------------------------------- signs
def sign_assembly(pl, p, face, plates, src, z=None, sidewalk=False):
    """Post + plates stacked from the lower edge (Table 1.11: >= 2.00 m, 2.20 m on a sidewalk)."""
    import streetscape.signs as SG
    yaw = yaw_of(face)
    zb = pl.add("sign_post", p, yaw, z=z, sz=1.0, src=src)
    zc = zb + (S.SIGN_H_SIDEWALK if sidewalk else S.SIGN_H_MIN)
    centres = []
    for code in reversed(plates):              # plates listed top first
        shape, _ = SG.face(code)
        size = S.SIGN_SIZE[shape] * (math.sqrt(3) / 2 if shape == "triangle" else 1.0)
        centres.append((code, zc + size / 2, shape))
        zc += size + 0.05
    pl.items[-1]["sz"] = round(zc - zb + 0.05, 3)
    for code, zcen, shape in centres:
        if shape == "triangle":                  # inverted triangle: centroid 1/3 from the top edge
            h = S.SIGN_SIZE["triangle"] * math.sqrt(3) / 2
            zcen = zcen - h / 2 + 2 * h / 3
        pl.add(f"plate_{code}", p, yaw, z=zcen, src=src)
    return [c for c, _, _ in centres]


def junction_signs(pl, net, juncs, ctx_points, report, codes):
    cnt = {}

    def put(arm, plates, src, extra=None):
        d = arm.chain.t_a if arm.end == "a" else arm.chain.t_b
        d = d + 3.0
        if d > arm.L - 2:
            return
        c = arm.chain
        s = float(arm.s(d))
        side = "L" if arm.end == "a" else "R"         # right of inbound traffic = left of outward direction
        kind, h, w, ext = side_surface_offset(c, side, s)
        off = S.KERB_TOP_W + S.SIGN_LATERAL if kind != RURAL else ext + 0.5
        p = arm.gutter(d, +1, extra=off if extra is None else extra)
        face = arm.direction(d)
        if pl.near("sign", p, 1.5):
            return
        z = None
        if c.bridge[c.idx(s)]:
            return
        for cd in sign_assembly(pl, p, face, plates, src, z=z, sidewalk=w > 0.5):
            codes.add(cd)
            cnt[cd] = cnt.get(cd, 0) + 1
        pl.pts.setdefault("sign", []).append((p[0], p[1]))

    pts = {}
    for q in ctx_points:
        pts.setdefault(q["kind"], []).append(np.array([q["e"], q["n"]]))
    for j in juncs:
        inb = [a for a in j.arms if a.inbound_dirn() >= 0 and not a.is_ring()]
        if j.roundabout:
            for a in inb:
                put(a, ["A-7", "C-12"], f"rule:roundabout:{j.id}")
            continue
        if j.signalized:
            continue
        ranks = [RANK[a.cls(net.sec_list)] for a in j.arms]
        best = min(ranks)
        ctr = j.center if j.center is not None else np.mean([net.nodes[n]["xy"] for n in j.nodes], axis=0)
        stop = any(np.hypot(*(q - ctr)) < 25 for q in pts.get("highway=stop", []))
        give = any(np.hypot(*(q - ctr)) < 25 for q in pts.get("highway=give_way", []))
        for a in inb:
            r = RANK[a.cls(net.sec_list)]
            if r > best and a.cls(net.sec_list) in ("Z", "L", "G") or (r > best and (stop or give) and r < 6):
                put(a, ["B-20" if stop else "A-7"], f"rule:minor:{j.id}")
            elif r == best and best <= RANK["Z"] and max(ranks) > best and max(ranks) < 6:
                put(a, ["D-1"], f"rule:major:{j.id}")
    report["junction_signs"] = cnt


def speed_signs(pl, net, report, codes):
    n = 0
    for c in net.chains:
        if c.meta.get("absorbed") or c.roundabout or c.length < 80:
            continue
        sec = c.section(c.length / 2, net.sec_list)
        v = sec.maxspeed
        if not v or int(v) == 50:
            continue
        dirs = [1] if (c.dirn > 0).mean() >= 0.5 else [-1] if (c.dirn < 0).mean() >= 0.5 else [1, -1]
        for dn in dirs:
            s = (c.t_a + S.SPEED_SIGN_AFTER_JUNCTION) if dn > 0 else (c.length - c.t_b - S.SPEED_SIGN_AFTER_JUNCTION)
            if not (0 < s < c.length) or c.bridge[c.idx(s)]:
                continue
            side = "R" if dn > 0 else "L"
            sgn = -1.0 if side == "R" else 1.0
            kind, h, w, ext = side_surface_offset(c, side, s)
            off = float(c.hw_at(s)) + (S.KERB_TOP_W + S.SIGN_LATERAL if kind != RURAL else ext + 0.5)
            p = c.line.offset_point(s, sgn * off)
            t, _ = c.line.frame(s)
            code = f"B-33_{int(v)}"
            sign_assembly(pl, p, -t * dn, [code], f"rule:maxspeed:{c.id}", sidewalk=w > 0.5)
            codes.add(code)
            n += 1
    report["speed_signs"] = n


def nearest_chain(net, p, maxd=25.0):
    best = None
    for c in net.chains:
        lo, hi = c.line.p.min(0) - maxd, c.line.p.max(0) + maxd
        if not (lo[0] <= p[0] <= hi[0] and lo[1] <= p[1] <= hi[1]):
            continue
        s, lat = c.line.project(np.asarray(p, float))
        d = abs(lat) - float(c.hw_at(s))
        if d < maxd and (best is None or d < best[0]):
            best = (d, c, s, lat)
    return best


def crossing_signs(pl, net, ctx_points, report, codes):
    n = 0
    for q in ctx_points:
        if q["kind"] != "highway=crossing" or q.get("crossing") in ("unmarked", "no", "traffic_signals") \
                or q.get("crossing") == "uncontrolled" and False:
            continue
        hit = nearest_chain(net, (q["e"], q["n"]), 3.0)
        if not hit:
            continue
        _, c, s, _ = hit
        if c.roundabout or c.bridge[c.idx(s)]:
            continue
        hw = float(c.hw_at(s))
        t, _ = c.line.frame(s)
        dirs = [1] if (c.dirn > 0).mean() >= 0.5 else [-1] if (c.dirn < 0).mean() >= 0.5 else [1, -1]
        for dn in dirs:
            side = "R" if dn > 0 else "L"
            sgn = -1.0 if side == "R" else 1.0
            ss = s - dn * (S.P10_WIDTH / 2 + 0.5)
            kind, h, w, ext = side_surface_offset(c, side, ss)
            p = c.line.offset_point(ss, sgn * (hw + S.KERB_TOP_W + S.SIGN_LATERAL))
            if pl.near("sign", p, 1.0):
                continue
            sign_assembly(pl, p, -t * dn, ["D-6"], f"osm:node/{q['osm_node']}", sidewalk=w > 0.5)
            pl.pts.setdefault("sign", []).append((p[0], p[1]))
            codes.add("D-6")
            n += 1
    report["crossing_signs"] = n


def direction_boards(pl, net, graph_attrs, report, boards):
    """Schematic E-2 boards at the start of *_link chains with a destination tag."""
    import streetscape.signs as SG
    n = 0
    for c in net.chains:
        if c.meta.get("absorbed"):
            continue
        sec = c.section(c.t_a + 1, net.sec_list)
        if not sec.highway.endswith("_link") or not sec.oneway:
            continue
        a = graph_attrs.get(sec.edge_id, {})
        dest = (a.get("destination") or {}).get("v")
        if not dest:
            continue
        ref = (a.get("ref") or {}).get("v") or ""
        fwd = (c.dirn > 0).mean() >= 0.5
        s = c.t_a + 6 if fwd else c.length - c.t_b - 6
        if not (0 < s < c.length):
            continue
        dn = 1 if fwd else -1
        sgn = -1.0 if fwd else 1.0
        hw = float(c.hw_at(s))
        side = "R" if fwd else "L"
        kind, h, w, ext = side_surface_offset(c, side, s)
        p = c.line.offset_point(s, sgn * (hw + (S.KERB_TOP_W + 1.2 if kind != RURAL else ext + 1.0)))
        t, _ = c.line.frame(s)
        key = f"E-2_{_h(dest + ref) % 100000:05d}"
        refs = [r.strip() for r in ref.split(";") if r.strip()]
        if key not in boards:
            im, wm, hm = SG.direction_board(dest.split(";"), refs, green=bool(refs))
            boards[key] = (round(wm, 3), round(hm, 3), im)
        wm, hm, _ = boards[key]
        z = pl.add("sign_post", p - t * dn * 0 + np.array([0, 0]), yaw_of(-t * dn), sz=S.SIGN_H_MIN + hm,
                   src=f"rule:destination:{c.id}")
        pl.add(f"board_{key}", p, yaw_of(-t * dn), z=z + S.SIGN_H_MIN + hm / 2, src=f"rule:destination:{c.id}")
        n += 1
    report["direction_boards"] = n


# ------------------------------------------------------------------------------------------- signals
def signals(pl, net, juncs, report):
    n = 0
    for j in juncs:
        if not j.signalized:
            continue
        for k, a in enumerate(j.arms):
            if a.inbound_dirn() < 0 or a.is_ring():
                continue
            d = (a.chain.t_a if a.end == "a" else a.chain.t_b) + 1.0
            if d > a.L - 1:
                continue
            c = a.chain
            s = float(a.s(d))
            if c.bridge[c.idx(s)]:
                continue
            side = "L" if a.end == "a" else "R"
            kind, h, w, ext = side_surface_offset(c, side, s)
            p = a.gutter(d, +1, extra=S.KERB_TOP_W + 0.6)
            face = a.direction(d)
            lit = "red" if (_h(j.id) + k) % 2 == 0 else "green"
            sec = c.section(s, net.sec_list)
            lanes_in = sec.lanes if sec.oneway else max(1, sec.lanes_fwd if a.end == "b" else sec.lanes_bwd)
            right = np.array([face[1], -face[0]])                # from the right kerb toward the carriageway
            if lanes_in >= S.SIGNAL_CANTILEVER_LANES:
                z = pl.add("signal_mast", p, yaw_of(right), src=f"rule:signal:{j.id}")
                head = p + right * 5.0
                pl.add(f"signal_head_{lit}", head, yaw_of(face), z=z + S.SIGNAL_MAST_H - 1.25, src=f"rule:signal:{j.id}")
            else:
                z = pl.add("signal_pole", p, yaw_of(face), src=f"rule:signal:{j.id}")
            pl.add(f"signal_head_{lit}", p + face * 0.15, yaw_of(face), z=z + 2.9, src=f"rule:signal:{j.id}")
            # repeater on the left (median kerb) of one-way approaches with >= 2 lanes, as on the Andersa / Maczka
            # photos (S-1 repeated on the left side; Dz.U. 2019 poz. 2311 zał. 3 - paragraph UNVERIFIED, not re-read)
            if sec.oneway and lanes_in >= 2:
                pL = a.gutter(d, -1, extra=S.KERB_TOP_W + 0.6)
                zl = pl.add("signal_pole", pL, yaw_of(face), src=f"rule:signal:{j.id}:left")
                pl.add(f"signal_head_{lit}", pL + face * 0.15, yaw_of(face), z=zl + 2.9, src=f"rule:signal:{j.id}:left")
                rep_left = report.setdefault("signal_repeaters_left", 0)
                report["signal_repeaters_left"] = rep_left + 1
            n += 1
    report["signal_approaches"] = n


# ------------------------------------------------------------------------------------------- misc points
def misc_points(pl, net, src, origin, report, codes):
    cnt = {}
    stops = [np.asarray(nd["geometry"]["coordinates"]) - origin for nd in src["osm"]["nodes"]
             if nd["tags"].get("highway") == "bus_stop"]
    for f in src["bdot10k"]["OT_OIKM_P"]:
        q = np.asarray(f["geometry"]["coordinates"]) - origin
        if all(np.hypot(*(q - s)) > 30 for s in stops):
            stops.append(q)
    for q in stops:
        hit = nearest_chain(net, q, 20.0)
        if not hit:
            continue
        _, c, s, lat = hit
        sgn = 1.0 if lat > 0 else -1.0
        side = "L" if sgn > 0 else "R"
        kind, h, w, ext = side_surface_offset(c, side, s)
        hw = float(c.hw_at(s))
        t, nn = c.line.frame(s)
        p = c.line.offset_point(s, sgn * (hw + max(ext, 2.2) + 1.0))
        pl.add("bus_shelter", p, yaw_of(-nn * sgn), src="bus_stop")
        dn = -1 if side == "L" else 1          # traffic on this side travels +s on the right side
        ps = c.line.offset_point(s + dn * 4.0, sgn * (hw + S.KERB_TOP_W + 0.6))
        sign_assembly(pl, ps, -t * dn, ["D-15"], "bus_stop", sidewalk=True)
        codes.add("D-15")
        cnt["bus_stop"] = cnt.get("bus_stop", 0) + 1
    for nd in src["osm"]["nodes"]:
        t = nd["tags"]
        q = np.asarray(nd["geometry"]["coordinates"]) - origin
        proto = None
        if t.get("barrier") == "lift_gate":
            proto = "lift_gate"
        elif t.get("barrier") in ("gate", "sliding_gate", "swing_gate"):
            proto = "sliding_gate"
        elif t.get("barrier") == "bollard":
            proto = "bollard"
        elif t.get("amenity") == "bench":
            proto = "bench"
        elif t.get("amenity") == "waste_basket":
            proto = "waste_bin"
        elif t.get("man_made") == "street_cabinet":
            proto = "street_cabinet"
        elif t.get("power") == "tower":
            proto = "pylon"
        elif t.get("power") == "pole":
            proto = "power_pole"
        if not proto:
            continue
        yaw = 0.0
        p = q
        if proto in ("lift_gate", "sliding_gate"):
            hit = nearest_chain(net, q, 6.0)
            if hit:
                _, c, s, lat = hit
                tt, nn = c.line.frame(s)
                hw = float(c.hw_at(s))
                if proto == "lift_gate":
                    p = c.line.offset_point(s, -(hw + 0.5))           # post at the right edge, boom across
                    yaw = math.atan2(nn[1], nn[0])                    # local +x -> chain left normal
                else:
                    p = c.line.offset_point(s, 0.0)
                    yaw = math.atan2(nn[1], nn[0])
        if pl.near(proto, p, 3.0):
            continue
        pl.add(proto, p, yaw, src=f"osm:node/{nd['osm_node']}", group=proto)
        cnt[proto] = cnt.get(proto, 0) + 1
    for f in src["bdot10k"]["OT_BUWT_P"]:
        if f["props"].get("rodzaj") != "słup energetyczny":
            continue
        q = np.asarray(f["geometry"]["coordinates"]) - origin
        if pl.near("power_pole", q, 4.0) or pl.near("pylon", q, 8.0):
            continue
        pl.add("power_pole", q, (_h(f["id"]) % 360) * math.pi / 180, src=f"bdot:{f['id']}", group="power_pole")
        cnt["power_pole"] = cnt.get("power_pole", 0) + 1
    report["points"] = cnt


# ------------------------------------------------------------------------------------------- linear
class Lin:
    def __init__(self, buf, zsurf):
        self.buf, self.zsurf = buf, zsurf

    def z(self, P):
        return self.zsurf(P[:, 0], P[:, 1])

    def dens(self, line, step):
        L = line.length
        n = max(1, int(math.ceil(L / step)))
        P = np.array([line.interpolate(L * k / n).coords[0] for k in range(n + 1)])
        return P

    def ribbon(self, mat, P, zb, zt, offset=0.0, src="", both=True, collision=None):
        """Vertical strip along P from zb to zt (arrays), both faces."""
        d = np.gradient(P, axis=0)
        d /= np.maximum(np.hypot(d[:, 0], d[:, 1]), 1e-9)[:, None]
        nrm = np.column_stack([-d[:, 1], d[:, 0]])
        Q = P + nrm * offset
        s = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(Q, axis=0).T))])
        n = len(Q)
        V = np.concatenate([np.column_stack([Q, zb]), np.column_stack([Q, zt])])
        UV = np.column_stack([np.tile(s, 2), np.concatenate([zb - zb, zt - zb])])
        T = [(k, k + 1, n + k + 1) for k in range(n - 1)] + [(k, n + k + 1, n + k) for k in range(n - 1)]
        T = np.array(T)
        self.buf.add("furniture", mat, V, UV, T, src=src)
        if both:
            self.buf.add("furniture", mat, V, UV, T[:, [0, 2, 1]], src=src)
        if collision:
            self.buf.add("collision", collision, V, UV, np.concatenate([T, T[:, [0, 2, 1]]]), src=src)

    def slab(self, mat, P, zb, zt, thick, src="", collision=None):
        # right face (offset -t/2) keeps the ribbon winding (faces right), the left face is flipped; the top faces up
        # only (nobody sees its underside). Before v3 both sides had the same winding -> see-through from one side.
        self.ribbon(mat, P, zb, zt, -thick / 2, src, both=False, collision=None)
        self.ribbon(mat, P[::-1], zb[::-1] if np.ndim(zb) else zb, zt[::-1] if np.ndim(zt) else zt, -thick / 2, src,
                    both=False, collision=None)
        d = np.gradient(P, axis=0)
        d /= np.maximum(np.hypot(d[:, 0], d[:, 1]), 1e-9)[:, None]
        nrm = np.column_stack([-d[:, 1], d[:, 0]])
        A, B = P - nrm * thick / 2, P + nrm * thick / 2
        n = len(P)
        V = np.concatenate([np.column_stack([A, zt]), np.column_stack([B, zt])])
        T = np.array([(k, k + 1, n + k + 1) for k in range(n - 1)] + [(k, n + k + 1, n + k) for k in range(n - 1)])
        self.buf.add("furniture", mat, V, V[:, :2], T, src=src)
        if collision:
            self.ribbon(collision, P, zb, zt, 0.0, src, both=False, collision=None)
            self.buf.parts[-1].layer = "collision"

    def posts(self, mat, P, spacing, w, d, h, zb=None, src=""):
        line = LineString(P)
        L = line.length
        ss = np.arange(0, L + 1e-6, spacing)
        Q = np.array([line.interpolate(s).coords[0] for s in ss])
        if len(Q) < 1:
            return
        Z = self.z(Q) if zb is None else np.interp(ss, np.concatenate([[0], np.cumsum(np.hypot(*np.diff(P, axis=0).T))]), zb)
        dd = np.gradient(Q, axis=0) if len(Q) > 1 else np.array([[1.0, 0.0]])
        dd /= np.maximum(np.hypot(dd[:, 0], dd[:, 1]), 1e-9)[:, None]
        Vs, Ts = [], []
        for q, z, t in zip(Q, Z, dd):
            nn = np.array([-t[1], t[0]])
            c = [q[0], q[1], z - 0.3 + (h + 0.3) / 2]
            hx, hy, hz = t * w / 2, nn * d / 2, (h + 0.3) / 2
            P8 = [np.array(c) + np.append(sx * hx + sy * hy, sz * hz) for sz in (-1, 1) for sy in (-1, 1) for sx in (-1, 1)]
            faces = [(4, 5, 7, 6), (0, 1, 5, 4), (2, 6, 7, 3), (0, 4, 6, 2), (1, 3, 7, 5)]
            base = len(Vs)
            Vs += P8
            for f in faces:
                Ts += [(base + f[0], base + f[1], base + f[2]), (base + f[0], base + f[2], base + f[3])]
        V = np.array(Vs)
        self.buf.add("furniture", mat, V, V[:, :2], np.array(Ts), src=src)


def cut_by(line, poly):
    if poly is None or poly.is_empty:
        return [line]
    g = line.difference(poly)
    return [p for p in getattr(g, "geoms", [g]) if p.geom_type == "LineString" and p.length > 1.0]


def fences(lin, src, origin, roads_poly, report):
    n = {"panel_m": 0.0, "concrete_m": 0.0, "retaining_m": 0.0}
    cutter = roads_poly.buffer(0.3) if roads_poly is not None else None
    for f in src["osm"]["ways"]:
        b = f["tags"].get("barrier")
        if b not in ("fence", "yes", "wall", "retaining_wall"):
            continue
        line = LineString(np.asarray(f["geometry"]["coordinates"], float) - origin)
        key = f"osm:way/{f['osm_way']}:{f['part']}"
        for part in cut_by(line, cutter):
            P = lin.dens(part, 2.0)              # 2 m: the Low terrain band is 2 m, posts sample the ground themselves
            Z = lin.z(P)
            if b in ("fence", "yes"):
                col = ["fence_green", "fence_anthracite", "fence_galv"][_h(key) % 3]
                lin.slab("concrete_plinth", P, Z - 0.2, Z + S.FENCE_PLINTH_H, 0.05, key)
                lin.ribbon(f"{col}_mesh", P, Z + S.FENCE_PLINTH_H, Z + S.FENCE_H, 0.0, key, both=True,
                           collision="collision_fence")
                lin.posts(col, P, S.FENCE_PANEL_W, 0.06, 0.04, S.FENCE_H + 0.05, src=key)
                n["panel_m"] += part.length
            elif b == "wall":
                lin.slab("concrete_fence", P, Z - 0.2, Z + S.CONCRETE_FENCE_H, 0.05, key, collision="collision_fence")
                lin.posts("concrete_fence_post", P, S.CONCRETE_FENCE_POST, 0.12, 0.12, S.CONCRETE_FENCE_H + 0.1, src=key)
                n["concrete_m"] += part.length
            else:
                retaining(lin, P, key)
                n["retaining_m"] += part.length
    for f in src["bdot10k"]["OT_BUUO_L"]:
        line = LineString(np.asarray(f["geometry"]["coordinates"], float) - origin)
        for part in cut_by(line, cutter):
            retaining(lin, lin.dens(part, 1.0), f"bdot:{f['id']}")
            n["retaining_m"] += part.length
    report["fences"] = {k: round(v) for k, v in n.items()}


def retaining(lin, P, key):
    d = np.gradient(P, axis=0)
    d /= np.maximum(np.hypot(d[:, 0], d[:, 1]), 1e-9)[:, None]
    nrm = np.column_stack([-d[:, 1], d[:, 0]])
    za, zb = lin.z(P + nrm * 2.0), lin.z(P - nrm * 2.0)
    top = np.maximum(za, zb) + 0.15
    bot = np.minimum(za, zb) - 0.4
    top = np.maximum(top, bot + 1.0)
    lin.slab("concrete_wall", P, bot, top, 0.35, key, collision="collision_fence")
    hi = np.where((za > zb)[:, None], nrm, -nrm)
    rail = P + hi * 0.0
    lin.posts("steel_galv", rail, 2.0, 0.05, 0.05, S.RAILING_H, zb=top, src=key + ":railing")
    for zr in (S.RAILING_H - 0.05, 0.55):
        lin.slab("steel_galv", rail, top + zr - 0.03, top + zr + 0.03, 0.05, key + ":railing")


def guardrail(lin, P, Z, key):
    """Steel W-beam on posts (top GUARDRAIL_H), Z = ground/surface height along P."""
    lin.posts("barrier_post", P, S.GUARDRAIL_POST_SPACING, 0.1, 0.05, S.GUARDRAIL_H - 0.05, zb=Z, src=key)
    d = np.gradient(P, axis=0)
    d /= np.maximum(np.hypot(d[:, 0], d[:, 1]), 1e-9)[:, None]
    nrm = np.column_stack([-d[:, 1], d[:, 0]])
    # W profile (two bulges toward the road side, +nrm): 5 points of the 0.31 m high beam
    prof = [(0.0, -0.31), (0.05, -0.24), (0.0, -0.155), (0.05, -0.07), (0.0, 0.0)]
    rows = []
    for o, dz in prof:
        rows.append(np.column_stack([P + nrm * (0.08 + o), Z + S.GUARDRAIL_H + dz]))
    n = len(P)
    V = np.concatenate(rows)
    s = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(P, axis=0).T))])
    UV = np.column_stack([np.tile(s, len(rows)), np.repeat(np.arange(len(rows)) * 0.08, n)])
    T = []
    for r in range(len(rows) - 1):
        a, b = r * n, (r + 1) * n
        T += [(a + k, a + k + 1, b + k + 1) for k in range(n - 1)] + [(a + k, b + k + 1, b + k) for k in range(n - 1)]
    T = np.array(T)
    lin.buf.add("furniture", "barrier_steel", V, UV, T, src=key)
    lin.buf.add("furniture", "barrier_steel", V, UV, T[:, [0, 2, 1]], src=key)
    lin.buf.add("collision", "collision_steel", V, UV, np.concatenate([T, T[:, [0, 2, 1]]]), src=key)


def guardrails(lin, net, zground, report):
    m = {"bridge": 0.0, "median": 0.0, "embankment": 0.0}
    drops, runs = [], []
    for c in net.chains:
        if c.meta.get("absorbed"):
            continue
        s0, s1 = c.t_a, c.length - c.t_b
        if s1 - s0 < 10:
            continue
        ss = np.arange(s0, s1, 1.0)
        hw = c.hw_at(ss)
        br = c.bridge[c.idx(ss)]
        for side, sgn in (("L", 1.0), ("R", -1.0)):
            kinds = np.array([side_params(c, side, s)[0] for s in ss])
            ext = np.array([side_extent(*side_params(c, side, s)) for s in ss])
            zg = c.crossfall_z(ss, sgn * hw)
            want = np.zeros(len(ss), int)            # 1 bridge, 2 median, 3 embankment
            off = np.zeros(len(ss))
            zb = zg.copy()
            # bridges: rail on the cap, 0.5 m behind the kerb
            want[br] = 1
            off[br] = hw[br] + S.KERB_TOP_W + 0.5
            zb[br] = zg[br] + S.BRIDGE_KERB_H
            med = (kinds == MEDIAN_RURAL) & ~br
            want[med] = 2
            off[med] = hw[med] + S.PAVED_SHOULDER_MEDIAN + S.GUARDRAIL_OFFSET
            zb[med] = zg[med] - 0.02
            rur = (kinds == RURAL) & ~br
            if rur.any():
                # embankment height = road edge minus the ground at the toe of the fill slope: berm 1 m +
                # slope 1:1.5 of a 2 m fill + 1 m = profile end + 5 m (the old probe at +2 m only ever saw
                # the berm, so the rule never fired); take the lowest of three probes (5, 7, 9 m)
                drop = np.full(len(ss), -1e9)            # zground = natural ground (NMT), not the conformed terrain
                for extra in (5.0, 7.0, 9.0):
                    P_out = c.line.offset_point(ss, sgn * (hw + ext + extra))
                    drop = np.maximum(drop, zg - zground(P_out[:, 0], P_out[:, 1]))
                drops.append(float(drop[rur].max()))
                emb = rur & (drop > S.GUARDRAIL_EMBANKMENT_H)
                # extend 12 m each way (approach), close small gaps
                from scipy import ndimage
                emb = ndimage.binary_dilation(emb, iterations=12) & rur
                want[emb] = 3
                off[emb] = hw[emb] + S.PAVED_SHOULDER + S.GUARDRAIL_OFFSET
                zb[emb] = zg[emb] - S.CROSSFALL * S.PAVED_SHOULDER
            # runs
            k = 0
            while k < len(ss):
                if want[k] == 0:
                    k += 1
                    continue
                kk = k
                while kk + 1 < len(ss) and want[kk + 1] == want[k]:
                    kk += 1
                if kk - k >= 8:
                    sl = slice(k, kk + 1)
                    P = c.line.offset_point(ss[sl], sgn * off[sl])
                    if sgn > 0:                          # beam faces the road: road is on the right of travel
                        P, Zr = P[::-1], zb[sl][::-1]
                    else:
                        Zr = zb[sl]
                    guardrail(lin, P, Zr, f"{c.id}:{side}:{['', 'bridge', 'median', 'embankment'][want[k]]}")
                    if want[k] == 3:
                        runs.append({"chain": c.id, "side": side, "s": [round(float(ss[k]), 1), round(float(ss[kk]), 1)],
                                     "max_drop_m": round(float(drop[sl].max()), 2),
                                     "at": [round(float(v), 1) for v in c.line.offset_point(ss[(k + kk) // 2], 0.0)]})
                    m[["", "bridge", "median", "embankment"][want[k]]] += kk - k
                k = kk + 1
    report["guardrails_m"] = {k: round(v) for k, v in m.items()}
    d = np.array(drops) if drops else np.zeros(1)
    report["embankment_check"] = {"rural_sides": len(drops), "max_drop_m": round(float(d.max()), 2),
                                  "p95_drop_m": round(float(np.percentile(d, 95)), 2),
                                  "threshold_m": S.GUARDRAIL_EMBANKMENT_H, "runs": runs,
                                  "ground": "NMT (decks removed) at the profile end + 5 / 7 / 9 m"}


def noise_barriers(lin, src, origin, roads_poly, report):
    L = 0.0
    cutter = roads_poly.buffer(0.2) if roads_poly is not None else None
    for f in src["bdot10k"]["OT_OIKM_L"]:
        line = LineString(np.asarray(f["geometry"]["coordinates"], float) - origin)
        for part in cut_by(line, cutter):
            P = lin.dens(part, 2.0)
            Z = lin.z(P)
            key = f"bdot:{f['id']}"
            lin.slab("concrete_plinth", P, Z - 0.4, Z + 0.5, 0.2, key)
            lin.slab("noise_panel", P, Z + 0.5, Z + S.NOISE_BARRIER_H, 0.12, key, collision="collision_fence")
            lin.posts("steel_painted", P, S.NOISE_BARRIER_POST, 0.2, 0.2, S.NOISE_BARRIER_H + 0.1, src=key)
            L += part.length
    report["noise_barriers_m"] = round(L)


WIRE_HALF_W = 0.012          # m; conductor ~24 mm incl. sag ripple (WORKING_VALUE, AFL-6 70-120 mm2 class)


# Supports of BDOT10k power lines (OT_SULN_L). The line vertices are the angle points; BDOT / OSM poles (OT_BUWT_P,
# power=pole/tower) cover only part of them (tile C: 44 of 74 vertices without a pole within 10 m), so conductors hung
# in the air (REVIEW r4 W-H2). Every angle point gets a support unless a mapped one stands within SUPPORT_SNAP_M (the
# span then ends on that pole), and straight runs get intermediate supports every <= span max. WORKING_VALUE: typical
# MV overhead line spans 60-100 m on concrete poles, HV 110 kV 250-400 m on lattice towers (no source in repo).
SUPPORT_SNAP_M = {"power_pole": 10.0, "pylon": 15.0}
SPAN_MAX_M = {"power_pole": 80.0, "pylon": 350.0}


def _nearest_support(pl, q, r):
    best, bd = None, r * r
    for g in ("power_pole", "pylon"):
        for p in pl.pts.get(g, []):
            d = (p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2
            if d < bd:
                best, bd = np.array([p[0], p[1]], float), d
    return best


def power_supports(pl, P, hv, key, roads_poly, report):
    """Support points of one line (E, N): angle points + intermediate supports, snapped to mapped poles; adds the
    missing supports as instances. Returns the support polyline."""
    proto = "pylon" if hv else "power_pole"
    span = SPAN_MAX_M[proto]
    pts = [P[0]]
    for a, b in zip(P, P[1:]):
        L = float(np.hypot(*(b - a)))
        k = max(1, int(math.ceil(L / span)))
        pts += [a + (b - a) * (i / k) for i in range(1, k + 1)]
    out = []
    for i, q in enumerate(pts):
        d = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)])
        d = d / max(np.linalg.norm(d), 1e-9)
        snap = _nearest_support(pl, q, SUPPORT_SNAP_M[proto])
        if snap is not None:
            out.append(snap)
            for it in pl.items:                        # mapped pole: turn its cross-arm across the line
                if it["p"] in ("power_pole", "pylon") and abs(it["e"] - snap[0]) < 2e-3 and abs(it["n"] - snap[1]) < 2e-3:
                    it["yaw"] = round(float(yaw_of(d)), 4)
            continue
        if roads_poly is not None and roads_poly.contains(Point(float(q[0]), float(q[1]))):
            continue                                   # never on a carriageway: the span runs on to the next support
        pl.add(proto, q, yaw_of(d), src=f"rule:power_support:{key}", group=proto)   # arms (local x) across the line
        report["supports_added"] = report.get("supports_added", 0) + 1
        out.append(np.asarray(q, float))
    return np.array(out)


def power_lines(lin, src, origin, report, pl=None, roads_poly=None):
    n = 0
    sup_rep = {}
    if roads_poly is not None:
        from shapely.prepared import prep
        roads_poly = prep(roads_poly.buffer(1.0))
    for f in src["bdot10k"]["OT_SULN_L"]:
        hv = "wysokiego" in (f["props"].get("rodzaj") or "")
        P = np.asarray(f["geometry"]["coordinates"], float) - origin
        if len(P) < 2:
            continue
        if pl is not None:
            P = power_supports(pl, P, hv, f["id"], roads_poly, sup_rep)
            if len(P) < 2:
                continue
        h, sep = (23.0, 5.0) if hv else (11.7, 0.8)
        for a, b in zip(P, P[1:]):
            L = float(np.hypot(*(b - a)))
            if L < 5:
                continue
            k = max(2, int(L / 5))
            t = np.linspace(0, 1, k + 1)
            Q = a + (b - a) * t[:, None]
            za, zb = lin.z(a[None])[0] + h, lin.z(b[None])[0] + h
            sag = 0.015 * L * 4 * t * (1 - t)
            Z = za + (zb - za) * t - sag
            dvec = (b - a) / L
            nn = np.array([-dvec[1], dvec[0]])
            # 3D tangent of the sagging wire per sample (engine ribbon, ADR 0022 / REVIEW r4 W-H2)
            dz = np.gradient(Z, t * L) if len(t) > 1 else np.zeros_like(t)
            tan = np.column_stack([np.repeat(dvec[None], len(t), 0), dz])
            tan /= np.linalg.norm(tan, axis=1, keepdims=True)
            for o in (-sep, 0.0, sep):
                QQ = Q + nn * o
                V = np.concatenate([np.column_stack([QQ, Z - WIRE_HALF_W]), np.column_stack([QQ, Z + WIRE_HALF_W])])
                m = len(QQ)
                T = np.array([(i, i + 1, m + i + 1) for i in range(m - 1)] + [(i, m + i + 1, m + i) for i in range(m - 1)])
                # layer "wires": the engine re-expands each ribbon towards the camera to >= 1 px with coverage alpha
                # (Kamion/World Wire): UV0 = (side -1/+1, physical half width m), COLOR_0 = tangent * 0.5 + 0.5
                uv = np.column_stack([np.repeat([-1.0, 1.0], m), np.full(2 * m, WIRE_HALF_W)])
                col = np.concatenate([tan, tan]) * 0.5 + 0.5
                col = np.column_stack([col, np.ones(2 * m)])
                lin.buf.add("wires", "wire", V, uv, T, src=f"bdot:{f['id']}", COL=col)
        n += 1
    report["power_lines"] = n
    report["power_supports_added"] = sup_rep.get("supports_added", 0)
