"""Static "life" props by land use (point instances of streetscape.life_props prototypes).

Rules (deterministic: every decision is a hash of a stable id, no RNG state; WORKING_VALUE rates):
  dock trailers   13.6 m semitrailers dropped at loading-dock doors (hero warehouse 55 %, other warehouses 35 %
                  of the doors): rear 0.45 m off the wall (bumpers), +y along the wall's outward normal. Mix:
                  curtainsider 70 % (6 plain fictional colours), dry box 15 %, reefer 15 %.
  parking         bays 2.5 x 5.0 m laid out in rows (5 m bay, 6 m aisle, 5 m bay = 16 m module) along the
                  dominant direction of every OSM amenity=parking / BDOT10k OT_KUKO_A parking polygon; a bay is
                  used only if its rectangle lies inside the polygon; occupancy 60 % (weekday staff parking).
                  85 % cars (hatch / sedan / estate), 15 % panel vans; colour shares of the Polish fleet
                  (silver/grey/black/white dominate, WORKING_VALUE).
  pallets         clusters of 2-6 stacks (empty EUR pallets 4-16 high, wrapped loads) against yard-facing hall
                  walls, 2-9 m from a corner (doors sit mid-wall), and beyond both ends of dock rows.
  bins            groups of 2-4 1100 l containers on paving next to blocks and offices (one corner per building).
  skips           one KP-7 skip at 25 % of the halls, on the yard next to a corner.
  cones           2-3 traffic cones at the ends of some dock rows.
  truck yards     on block-paved / concrete / asphalt yards >= 1200 m2 (not dock aprons, not car parks): rows of
                  3.8 m truck bays along every yard edge >= 20 m, rear 1.0 m off the edge, nose into the yard;
                  occupancy 40 %: trailer on its legs 55 %, trailer coupled to a tractor 28 %, solo tractor 17 %
                  (tractor colours plain, no lettering); nothing within 35 m in front of a dock row.
  containers      25 % of concrete / gravel / asphalt yards >= 1200 m2: one row of 2-6 ISO containers (20/40 ft)
                  along an edge, 30 % of them with a second container stacked on top.
  tyre scrub      decals (`decal_tyre`) in front of every dock door: 2-3 passes of the two trailer wheel tracks
                  (+-1.0 m), straight for the last 2-9 m before the bumpers, then bending to the side the trucks
                  swing in from (one side per dock row, R 22-45 m) up to 16-24 m out; lifted like oil stains.
Everything keeps clear of road surfaces (incl. flush yard roads), buildings and a 5 m corridor along the start
route, and must stand on a paved area. Liveries are plain colours; no lettering or logos.
"""

from __future__ import annotations

import hashlib
import math

import numpy as np
import shapely
import shapely.ops
from shapely import affinity
from shapely.geometry import LineString, Point, Polygon

from roads import decals as DC
from roads import standards as S

from . import life_props as LP

CAR_SHARE = [("silver", 0.22), ("grey", 0.20), ("black", 0.18), ("white", 0.18), ("blue", 0.12), ("red", 0.10)]
START_CLEAR_R = 120.0        # m around the route start kept free of parked vehicles (r5, WORKING_VALUE, interim)
START_CLEAR_L = 250.0        # m of route from the start ...
START_CLEAR_W = 45.0         # ... buffered by this half width (covers the yard seen from g3a_eye_s0012..s0212)
BODY_SHARE = [("hatch", 0.34), ("sedan", 0.16), ("estate", 0.22), ("suv", 0.28)]    # WORKING_VALUE street mix
OCCUPANCY = 0.72      # weekday daytime share of occupied bays (WORKING_VALUE; Polish city lots are mostly full)


def hf(*key):
    return int(hashlib.sha1(":".join(str(k) for k in key).encode()).hexdigest()[:8], 16) / 0xFFFFFFFF


def pick(shares, u):
    acc = 0.0
    for k, w in shares:
        acc += w
        if u < acc:
            return k
    return shares[-1][0]


def yaw_of(f):
    return math.atan2(f[1], f[0]) - math.pi / 2


def rect(c, f, half_len, half_w):
    """Rectangle centred at c with long axis f."""
    f = np.asarray(f, float) / np.linalg.norm(f)
    nrm = np.array([-f[1], f[0]])
    c = np.asarray(c, float)
    return Polygon([c - f * half_len - nrm * half_w, c + f * half_len - nrm * half_w, c + f * half_len + nrm * half_w,
                    c - f * half_len + nrm * half_w])


class Space:
    """Free space test: inside paved, outside roads / buildings / route corridor / already placed props."""

    def __init__(self, paved_union, roads_poly, bpoly, route):
        self.paved = paved_union.buffer(0.3)
        self.block = shapely.union_all([roads_poly.buffer(0.4), bpoly.buffer(0.25),
                                        route.buffer(5.0) if route is not None else Polygon()])
        shapely.prepare(self.paved)
        shapely.prepare(self.block)
        self.taken = []
        self.tree = None
        # r5 P1: the parked tractor / trailer prototypes are still generic boxes; until they are replaced by the
        # static LOD1/LOD2 of the real tractor and curtainsider exports they stay out of the player's first frames:
        # no parked vehicle within START_CLEAR_R of the route start or START_CLEAR_W of its first START_CLEAR_L.
        self.start_clear = Polygon()
        if route is not None and route.length > 1:
            head = shapely.ops.substring(route, 0.0, min(START_CLEAR_L, route.length))
            self.start_clear = shapely.union_all([Point(route.coords[0]).buffer(START_CLEAR_R),
                                                  head.buffer(START_CLEAR_W)])
        shapely.prepare(self.start_clear)
        self.start_cleared = 0

    def vehicle_free(self, poly, need_paved=True):
        """free() for parked tractors / trailers: also outside the start view."""
        if self.start_clear.intersects(poly):
            self.start_cleared += 1
            return False
        return self.free(poly, need_paved)

    def free(self, poly, need_paved=True):
        if need_paved and not self.paved.contains(poly):
            return False
        if self.block.intersects(poly):
            return False
        for t in self.taken[-400:]:
            if t.intersects(poly):
                return False
        return True

    def take(self, poly):
        self.taken.append(poly)


def dock_trailers(pl, docks, sp, report):
    n = 0
    for dk in docks:
        p, q = (np.asarray(x, float) for x in dk["edge"])
        d = (q - p) / np.linalg.norm(q - p)
        nout = np.array([d[1], -d[0]])
        hero = "9962cca0" in dk["id"]
        rate = 0.55 if hero else 0.35
        for dock in dk["docks"]:
            u = hf(dk["id"], dock["num"], "trailer")
            if u > rate:
                continue
            base = p + d * dock["u"] + nout * 0.45
            body = rect(base + nout * 6.8, nout, 6.8, 1.3)
            if not sp.vehicle_free(body):
                continue
            k = hf(dk["id"], dock["num"], "kind")
            if k < 0.70:
                proto = f"trailer_curtain_{int(hf(dk['id'], dock['num'], 'col') * len(LP.CURTAIN_COLOURS)) % len(LP.CURTAIN_COLOURS)}"
            elif k < 0.85:
                proto = "trailer_box_0"
            else:
                proto = "trailer_reefer_0"
            pl.add(proto, base, yaw_of(nout), z=dk["yard_z"], src=f"life:dock:{dk['id']}:{dock['num']}")
            sp.take(body)
            n += 1
    report["dock_trailers"] = n


def tyre_scrub(buf, docks, zsurf, report):
    """Tyre-scrub decals on the dock aprons (see module docstring). UV.x = metres along the track, UV.y = 0..1
    across, UV1 = (track length, pass seed): the material fades the ends and breaks the band with noise."""
    n = 0
    for dk in docks:
        p, q = (np.asarray(x, float) for x in dk["edge"])
        d = (q - p) / np.linalg.norm(q - p)
        nout = np.array([d[1], -d[0]])
        side = 1.0 if hf(dk["id"], "swing") < 0.5 else -1.0     # trucks swing in from one end of the row
        for dock in dk["docks"]:
            base = p + d * dock["u"] + nout * 0.45
            for k in range(2 + int(hf(dk["id"], dock["num"], "passes") > 0.5)):
                key = (dk["id"], dock["num"], k)
                s0 = 1.2 + hf(*key, "s0") * 1.5
                s_str = 2.0 + hf(*key, "str") * 7.0                    # straight part
                L = 16.0 + hf(*key, "len") * 8.0
                R = 22.0 + hf(*key, "r") * 23.0
                jit = (hf(*key, "j") - 0.5) * 0.35
                ss = np.arange(s0, L + 0.01, 1.5)
                bend = np.where(ss > s_str, (ss - s_str) ** 2 / (2 * R), 0.0)   # lateral offset of the arc
                for wx in (-1.0, 1.0):
                    w = 0.30 + hf(*key, wx, "w") * 0.16
                    lat = wx * 1.0 + jit + side * bend
                    C = base[None, :] + nout[None, :] * ss[:, None] + d[None, :] * lat[:, None]
                    t = np.gradient(C, axis=0)
                    t /= np.maximum(np.linalg.norm(t, axis=1, keepdims=True), 1e-9)
                    nn = np.column_stack([-t[:, 1], t[:, 0]])
                    A, B = C - nn * w / 2, C + nn * w / 2
                    V2 = np.vstack([A, B])
                    Z = zsurf(V2[:, 0], V2[:, 1]) + S.PAVED_LIFT + 0.008
                    m = len(ss)
                    T = np.array([(i, i + 1, m + i + 1) for i in range(m - 1)] + [(i, m + i + 1, m + i) for i in range(m - 1)])
                    if np.cross(np.append(t[0], 0), np.append(nn[0], 0))[2] < 0:
                        T = T[:, [0, 2, 1]]
                    uv = np.column_stack([np.tile(ss - s0, 2), np.repeat([0.0, 1.0], m)])
                    uv1 = np.column_stack([np.full(2 * m, L - s0), np.full(2 * m, hf(*key, wx, "seed"))])
                    buf.add("markings", "decal_tyre", np.column_stack([V2, Z]), uv, T,
                            src=f"tyre:{dk['id']}:{dock['num']}:{k}", UV1=uv1)
                    n += 1
    report["tyre_scrub_tracks"] = n


STALL_LINE_W = 0.12          # P-1e-like solid line 0.12 m (stand boundaries on private yards, WORKING_VALUE)
STALL_DEPTH_M = 17.5         # stand depth: tractor + 13.6 m trailer + clearance (WORKING_VALUE)
DRAIN_GRID_M = 24.0          # WORKING_VALUE: yard gullies / slot drains on a ~24 m grid (fall 0.5-1 %)
GULLY_SIZE = (0.50, 0.60)    # m, cast-iron gully grate (D400 class, typical 500 x 600, WORKING_VALUE)


def _quad_strip(buf, mat, C0, C1, w, zsurf, lift, src, uv1=None):
    """Straight decal strip from C0 to C1 (E, N), width w, subdivided every 2 m to follow the yard surface."""
    L = float(np.hypot(*(C1 - C0)))
    if L < 0.3:
        return
    n = max(1, int(math.ceil(L / 2.0)))
    d = (C1 - C0) / L
    nn = np.array([-d[1], d[0]])
    t = np.linspace(0, 1, n + 1)
    C = C0[None] + (C1 - C0)[None] * t[:, None]
    V2 = np.vstack([C - nn * w / 2, C + nn * w / 2])
    Z = zsurf(V2[:, 0], V2[:, 1]) + lift
    m = n + 1
    T = np.array([(i, i + 1, m + i + 1) for i in range(m - 1)] + [(i, m + i + 1, m + i) for i in range(m - 1)])
    # (i, i+1, m+i+1): right edge -> forward -> left edge = CCW seen from above (faces up)
    uv = np.column_stack([np.tile(t * L, 2), np.repeat([0.0, 1.0], m)])
    buf.add("markings", mat, np.column_stack([V2, Z]), uv, T, src=src,
            UV1=None if uv1 is None else np.tile(uv1, (2 * m, 1)))


def yard_markings(buf, stalls, zsurf, report):
    """Painted truck stand lines on yards (r4 W-H1): one line between neighbouring 3.8 m stands, perpendicular to the
    yard edge, plus a front line; worn paint (material marking_yard), broken where the dock manoeuvring area is."""
    n = 0
    for a, d, nin, u0, u1, mat, key, pg, keep_free in stalls:
        if mat == "yard_gravel" or hf(key, "paint") > 0.75:        # 25 % of yards without painted stands
            continue
        k = int(round((u1 - u0) / 3.8))
        for i in range(k + 1):
            base = a + d * (u0 + i * 3.8) + nin * 0.6
            tip = base + nin * STALL_DEPTH_M
            seg = LineString([base, tip])
            if keep_free.intersects(seg) or not pg.buffer(-0.3).contains(seg):
                continue
            _quad_strip(buf, "marking_yard", base, tip, STALL_LINE_W, zsurf, S.MARKING_LIFT, f"stall:{key}:{i}")
            n += 1
        f0, f1 = a + d * u0 + nin * (0.6 + STALL_DEPTH_M), a + d * u1 + nin * (0.6 + STALL_DEPTH_M)
        seg = LineString([f0, f1])
        if not keep_free.intersects(seg) and pg.buffer(-0.3).contains(seg):
            _quad_strip(buf, "marking_yard", f0, f1, STALL_LINE_W, zsurf, S.MARKING_LIFT, f"stall:{key}:front")
    report["stall_lines"] = n


def yard_drains(buf, paved, bpoly, zsurf, report):
    """Cast-iron gully grates on yards >= 600 m2 on a jittered DRAIN_GRID_M grid, >= 3 m inside the yard and away
    from buildings (procedural grate in the engine material drain_grate; UV0 0..1 over the grate)."""
    n = 0
    for item in paved:
        if item["mat"] not in ("yard_behaton", "yard_concrete", "yard_asphalt", "yard_paving", "yard_slabs"):
            continue
        for pi, pg in enumerate(getattr(item["poly"], "geoms", [item["poly"]])):
            if pg.geom_type != "Polygon" or pg.area < 600:
                continue
            inner = pg.buffer(-3.0)
            if inner.is_empty:
                continue
            x0, y0, x1, y1 = inner.bounds
            key = f"{item['id']}#{pi}"
            ox, oy = hf(key, "dx") * DRAIN_GRID_M, hf(key, "dy") * DRAIN_GRID_M
            for gx in np.arange(x0 + ox, x1, DRAIN_GRID_M):
                for gy in np.arange(y0 + oy, y1, DRAIN_GRID_M):
                    k = (key, round(float(gx), 1), round(float(gy), 1))
                    q = np.array([gx + (hf(*k, "jx") - 0.5) * 4, gy + (hf(*k, "jy") - 0.5) * 4])
                    if not inner.contains(Point(q)) or (bpoly is not None and bpoly.distance(Point(q)) < 2.0):
                        continue
                    ang = hf(key, "rot") * math.pi
                    d = np.array([math.cos(ang), math.sin(ang)])
                    nn = np.array([-d[1], d[0]])
                    hx, hy = GULLY_SIZE[0] / 2, GULLY_SIZE[1] / 2
                    V2 = np.array([q - d * hx - nn * hy, q + d * hx - nn * hy, q + d * hx + nn * hy, q - d * hx + nn * hy])
                    Z = zsurf(V2[:, 0], V2[:, 1]) + S.MARKING_LIFT * 0.5
                    buf.add("markings", "drain_grate", np.column_stack([V2, Z]), [[0, 0], [1, 0], [1, 1], [0, 1]],
                            np.array([(0, 1, 2), (0, 2, 3)]), src=f"drain:{key}")
                    n += 1
    report["yard_drains"] = n


def _edge_rows(poly, min_len):
    """(start, direction, inward normal, length) for every exterior edge of poly >= min_len."""
    ring = poly.exterior
    c = np.asarray(ring.coords)
    if not ring.is_ccw:
        c = c[::-1]
    for a, b in zip(c[:-1], c[1:]):
        L = float(np.hypot(*(b - a)))
        if L >= min_len:
            d = (b - a) / L
            yield a, d, np.array([-d[1], d[0]]), L          # CCW ring: interior on the left


DOCK_MANOEUVRE_M = 35.0      # WORKING_VALUE: kept free in front of dock rows (13.6 m trailer + tractor turning in)


def truck_yards(pl, paved, sp, report, docks=(), stalls=None):
    """stalls (list, optional): collects (a, d, nin, u_from, u_to, mat) of every truck stand row for the painted
    stall lines (yard_markings)."""
    cnt = {"yard_trailers": 0, "coupled": 0, "solo_tractors": 0, "containers": 0}
    k_rear, k_front = LP.tractor_extent()
    zones = []
    for dk in docks:                                   # manoeuvring area in front of every dock row stays free
        p, q = (np.asarray(x, float) for x in dk["edge"])
        d = (q - p) / np.linalg.norm(q - p)
        nout = np.array([d[1], -d[0]])
        a0 = p + d * (dk["docks"][0]["u"] - 6.0)
        a1 = p + d * (dk["docks"][-1]["u"] + 6.0)
        zones.append(Polygon([a0, a1, a1 + nout * DOCK_MANOEUVRE_M, a0 + nout * DOCK_MANOEUVRE_M]))
    keep_free = shapely.union_all(zones) if zones else Polygon()
    shapely.prepare(keep_free)
    for item in paved:
        if item.get("parking") or item.get("source") == "dock_apron":
            continue
        if item["mat"] not in ("yard_behaton", "yard_concrete", "yard_asphalt", "yard_gravel"):
            continue
        poly = item["poly"]
        polys = list(getattr(poly, "geoms", [poly]))
        for pi, pg in enumerate(polys):
            if pg.geom_type != "Polygon" or pg.area < 1200:
                continue
            ykey = f"{item['id']}#{pi}"
            if item["mat"] != "yard_gravel":
                for ei, (a, d, nin, L) in enumerate(_edge_rows(pg, 20.0)):
                    nb = int((L - 4.0) // 3.8)
                    if stalls is not None and nb >= 2:
                        stalls.append((a, d, nin, 2.0, 2.0 + nb * 3.8, item["mat"], f"{ykey}:{ei}", pg, keep_free))
                    for i in range(nb):
                        key = (ykey, ei, i)
                        if hf(*key, "occ") > 0.40:
                            continue
                        u = 2.0 + 1.9 + i * 3.8
                        base = a + d * u + nin * 1.0
                        r = hf(*key, "what")
                        yaw = yaw_of(nin) + (hf(*key, "yaw") - 0.5) * 0.05
                        if r < 0.55 or r < 0.83:
                            body = rect(base + nin * 6.8, nin, 6.9, 1.35)
                            coupled = r >= 0.55
                            if coupled:
                                kp = base + nin * LP.TRAILER_KINGPIN
                                body = shapely.union_all([body, rect(kp + nin * (k_rear + k_front) / 2, nin,
                                                                     (k_front - k_rear) / 2 + 0.2, 1.35)])
                            if keep_free.intersects(body) or not sp.vehicle_free(body):
                                continue
                            k = hf(*key, "kind")
                            if k < 0.70:
                                proto = f"trailer_curtain_{int(hf(*key, 'col') * len(LP.CURTAIN_COLOURS)) % len(LP.CURTAIN_COLOURS)}"
                            elif k < 0.85:
                                proto = "trailer_box_0"
                            else:
                                proto = "trailer_reefer_0"
                            pl.add(proto, base, yaw, src=f"life:yard:{ykey}")
                            cnt["yard_trailers"] += 1
                            if coupled:
                                tc = LP.TRACTOR_COLOURS[int(hf(*key, "tc") * len(LP.TRACTOR_COLOURS)) % len(LP.TRACTOR_COLOURS)]
                                pl.add(f"tractor_{tc}", base + nin * LP.TRAILER_KINGPIN, yaw, src=f"life:yard:{ykey}")
                                cnt["coupled"] += 1
                            sp.take(body)
                        else:                                   # solo tractor, nose into the yard
                            o = base - nin * k_rear + nin * 0.2
                            body = rect(o + nin * (k_rear + k_front) / 2, nin, (k_front - k_rear) / 2 + 0.2, 1.35)
                            if keep_free.intersects(body) or not sp.vehicle_free(body):
                                continue
                            tc = LP.TRACTOR_COLOURS[int(hf(*key, "tc") * len(LP.TRACTOR_COLOURS)) % len(LP.TRACTOR_COLOURS)]
                            pl.add(f"tractor_{tc}", o, yaw, src=f"life:yard:{ykey}")
                            sp.take(body)
                            cnt["solo_tractors"] += 1
            if item["mat"] in ("yard_concrete", "yard_gravel", "yard_asphalt") and hf(ykey, "cont") < 0.25:
                edges = list(_edge_rows(pg, 16.0))
                if not edges:
                    continue
                a, d, nin, L = edges[int(hf(ykey, "cedge") * len(edges)) % len(edges)]
                u = 3.0 + hf(ykey, "cu") * max(0.0, L - 30.0) * 0.5
                for i in range(2 + int(hf(ykey, "cn") * 5)):
                    ft = 40 if hf(ykey, i, "ft") < 0.55 else 20
                    hl = LP.CONTAINER_L[ft] / 2
                    c = a + d * (u + hl) + nin * (1.6 + hf(ykey, i, "off") * 0.3)
                    fp = rect(c, d, hl + 0.1, 1.3)
                    if keep_free.intersects(fp) or not sp.free(fp):
                        break
                    col = int(hf(ykey, i, "cc") * len(LP.CONTAINER_COLOURS)) % len(LP.CONTAINER_COLOURS)
                    yaw = yaw_of(d) + (hf(ykey, i, "y") - 0.5) * 0.03
                    z0 = pl.add(f"container_{ft}_{col}", c, yaw, src=f"life:containers:{ykey}")
                    cnt["containers"] += 1
                    if hf(ykey, i, "stack") < 0.30:
                        col2 = (col + 1 + int(hf(ykey, i, "c2") * 4)) % len(LP.CONTAINER_COLOURS)
                        pl.add(f"container_{ft}_{col2}", c + d * (hf(ykey, i, "sd") - 0.5) * 0.1, yaw + 0.01,
                               z=z0 + LP.CONTAINER_H, src=f"life:containers:{ykey}")
                        cnt["containers"] += 1
                    sp.take(fp)
                    u += 2 * hl + 0.4 + hf(ykey, i, "gap") * 0.6
    report.update(cnt)


def _bays(poly, key):
    """Bay centres + nose directions laid out along the dominant direction of the parking polygon."""
    r = poly.minimum_rotated_rectangle
    c = np.asarray(r.exterior.coords)
    e = np.diff(c, axis=0)
    k = int(np.argmax(np.hypot(e[:, 0], e[:, 1])))
    ang = math.atan2(e[k, 1], e[k, 0])
    ca, sa = math.cos(ang), math.sin(ang)
    loc = affinity.rotate(poly, -ang, origin=(0, 0), use_radians=True)
    inner = loc.buffer(-0.3)
    if inner.is_empty:
        return []
    shapely.prepare(inner)
    x0, y0, x1, y1 = loc.bounds
    # phase of the 16 m module from the polygon id (no grid alignment between neighbouring lots)
    ph = hf(key, "phase") * 2.0
    out = []
    y = y0 + 0.4 + ph
    row = 0
    while y + 5.0 < y1:
        for yc, nose in ((y + 2.5, -1.0), (y + 13.5, 1.0)):
            if yc + 2.5 > y1:
                continue
            x = x0 + 0.4 + hf(key, "x", row) * 1.0
            while x + 2.5 < x1:
                bay = Polygon([(x, yc - 2.5), (x + 2.5, yc - 2.5), (x + 2.5, yc + 2.5), (x, yc + 2.5)])
                if inner.contains(bay):
                    cx, cy = x + 1.25, yc
                    out.append((np.array([cx * ca - cy * sa, cx * sa + cy * ca]),
                                np.array([-sa * nose, ca * nose])))
                x += 2.5
        y += 16.0
        row += 1
    return out


def _strip_bays(poly, key):
    """One row of bays in a narrow parking strip (OSM parking=street_side / lane polygons, short side < 7 m):
    short side < 3.6 m -> parallel bays 6.0 m pitch (car axis along the strip), else perpendicular bays 2.5 m pitch
    (nose to a hashed side). Returns (centre, nose, overhang_ok)."""
    r = poly.minimum_rotated_rectangle
    c = np.asarray(r.exterior.coords)
    e = np.diff(c, axis=0)
    k = int(np.argmax(np.hypot(e[:, 0], e[:, 1])))
    f = e[k] / np.hypot(*e[k])
    nrm = np.array([-f[1], f[0]])
    w = float(np.hypot(*e[(k + 1) % 4]))
    L = float(np.hypot(*e[k]))
    a = c[k] + nrm * (w / 2) * (1 if np.dot(c[(k + 2) % 4] - c[k], nrm) > 0 else -1)
    parallel = w < 3.6
    pitch = 6.0 if parallel else 2.5
    side = 1.0 if hf(key, "side") < 0.5 else -1.0
    out = []
    t = 0.6 + hf(key, "ph") * 1.0 + pitch / 2
    inner = poly.buffer(0.6)
    shapely.prepare(inner)
    while t + pitch / 2 < L:
        cc = a + f * t
        if inner.contains(Point(cc)):
            out.append((cc, f.copy() if parallel else nrm * side))
        t += pitch
    return out


def parking(pl, paved, sp, report, buf=None, zsurf=None, park_union=None):
    """Bays in every paved area that is (or overlaps) a car park: OSM amenity=parking (incl. parking=street_side
    strips) and BDOT10k OT_KUKO_A parking. A BDOT yard polygon earlier in the paved priority list used to swallow
    the OSM car park (parking flag lost -> empty lots in front of the route, REVIEW r5 W-H3+)."""
    cars = vans = bays = 0
    oil = 0
    regions = []
    for item in paved:
        if item.get("source") == "dock_apron":
            continue
        if item.get("parking"):
            regions.append((item["id"], item["poly"]))
        elif park_union is not None and item["poly"].intersects(park_union):
            g = item["poly"].intersection(park_union)
            for k, p in enumerate(getattr(g, "geoms", [g])):
                if p.geom_type == "Polygon" and p.area > 25.0:
                    regions.append((f"{item['id']}~p{k}", p))
    for rid, poly in regions:
        r = poly.minimum_rotated_rectangle
        ee = np.hypot(*np.diff(np.asarray(r.exterior.coords), axis=0).T)
        strip = float(min(ee[:2])) < 7.0
        layout = [(c, n, True) for c, n in _strip_bays(poly, rid)] if strip else [(c, n, False) for c, n in _bays(poly, rid)]
        item = {"id": rid}
        for i, (c, nose, strip_bay) in enumerate(layout):
            bays += 1
            key = (item["id"], i)
            if buf is not None and hf(*key, "oil") < 0.35:      # drip stain under the engine bay
                P0 = c + nose * 1.1 + np.array([nose[1], -nose[0]]) * (hf(*key, "ox") - 0.5) * 0.6

                def z_of(V2):
                    return zsurf(V2[:, 0], V2[:, 1]) + S.PAVED_LIFT + 0.008     # yard mesh is linear on 4 m cells
                DC.stain(buf, P0, z_of, 0.2 + hf(*key, "or") * 0.3, key, f"oil:{item['id']}:{i}")
                oil += 1
            if hf(*key, "occ") > OCCUPANCY:
                continue
            jit = (hf(*key, "jx") - 0.5) * 0.3
            c2 = c + np.array([nose[1], -nose[0]]) * jit + nose * (hf(*key, "jy") - 0.5) * 0.4
            yaw = yaw_of(nose) + (hf(*key, "yaw") - 0.5) * 0.08
            if hf(*key, "van") < 0.15:
                proto = f"van_{pick([('white', 0.5), ('silver', 0.25), ('white2', 0.25)], hf(*key, 'col'))}"
                hl = LP.VAN["L"] / 2 + 0.05
            else:
                body = pick(BODY_SHARE, hf(*key, 'body'))
                proto = f"car_{body}_{pick(CAR_SHARE, hf(*key, 'col'))}"
                hl = LP.CARS[body]["L"] / 2 + 0.05
            # strip bays: nose / tail may overhang the kerb line by up to 0.45 m (as parked cars do), so the
            # free-space test uses a footprint shortened by that much; lots keep the full footprint
            fp = rect(c2, nose, hl - (0.45 if strip_bay else 0.0), 1.05 if proto.startswith("van") else 0.95)
            if not sp.free(fp, need_paved=not strip_bay):
                continue
            pl.add(proto, c2, yaw, src=f"life:parking:{item['id']}")
            sp.take(fp)
            if proto.startswith("van"):
                vans += 1
            else:
                cars += 1
    report["parking"] = {"bays": bays, "cars": cars, "vans": vans, "oil_stains": oil}


def _wall_edges(poly):
    ring = poly.exterior
    c = np.asarray(ring.coords)
    if not ring.is_ccw:
        c = c[::-1]
    for a, b in zip(c[:-1], c[1:]):
        L = float(np.hypot(*(b - a)))
        if L > 6.0:
            d = (b - a) / L
            yield a, b, L, d, np.array([d[1], -d[0]])


def _pallet_cluster(pl, sp, a, d, nout, u0, key, nmax, src):
    """Stacks along the wall from station u0 (direction d), 0.5 m off the wall."""
    n = 0
    u = u0
    for i in range(nmax):
        k = hf(key, i, "kind")
        if k < 0.25:
            proto, hl = "pallet_load", 0.6
        else:
            proto, hl = f"pallets_empty_{[4, 8, 12, 16][int(hf(key, i, 'h') * 4) % 4]}", 0.6
        c = a + d * (u + hl) + nout * (0.5 + 0.4 + hf(key, i, "off") * 0.15)
        fp = rect(c, d, hl + 0.05, 0.45)
        if not sp.free(fp):
            break
        yaw = yaw_of(d) + (hf(key, i, "yaw") - 0.5) * 0.12
        pl.add(proto, c, yaw, src=src)
        sp.take(fp)
        n += 1
        u += 2 * hl + 0.25 + hf(key, i, "gap") * (0.9 if i % 3 == 2 else 0.2)
    return n


def yard_props(pl, blds, docks, sp, report):
    cnt = {"pallets": 0, "bins": 0, "skips": 0, "cones": 0}
    dock_edges = {}
    for dk in docks:
        dock_edges.setdefault(dk["id"].split(":docks")[0], []).append(dk)
    for b in blds:
        typ, key, poly = b["typ"], b["id"], b["poly"]
        if typ == "hall":
            for ei, (a, q, L, d, nout) in enumerate(_wall_edges(poly)):
                ek = f"{key}:{ei}"
                if hf(ek, "pal") < 0.45 and L > 14:
                    # near one corner (doors are mid-wall)
                    a0, d0 = (a, d) if hf(ek, "end") < 0.5 else (q, -d)
                    cnt["pallets"] += _pallet_cluster(pl, sp, a0, d0, nout, 2.0 + hf(ek, "u") * 5, ek,
                                                      2 + int(hf(ek, "n") * 5), f"life:pallets:{key}")
            if hf(key, "skip") < 0.25:
                for ei, (a, q, L, d, nout) in enumerate(_wall_edges(poly)):
                    c = a + d * 4.0 + nout * 2.2
                    fp = rect(c, d, 2.05, 1.0)
                    if sp.free(fp):
                        pl.add("skip_kp7", c, yaw_of(d), src=f"life:skip:{key}")
                        sp.take(fp)
                        cnt["skips"] += 1
                        break
            # ends of dock rows: pallets + cones
            for dk in dock_edges.get(key, []):
                p0, p1 = (np.asarray(x, float) for x in dk["edge"])
                d = (p1 - p0) / np.linalg.norm(p1 - p0)
                nout = np.array([d[1], -d[0]])
                u_first, u_last = dk["docks"][0]["u"], dk["docks"][-1]["u"]
                cnt["pallets"] += _pallet_cluster(pl, sp, p0, d, nout, u_last + 2.8, dk["id"] + ":endB",
                                                  2 + int(hf(dk["id"], "nb") * 4), f"life:pallets:{dk['id']}")
                cnt["pallets"] += _pallet_cluster(pl, sp, p0 + d * u_first, -d, nout, 2.8, dk["id"] + ":endA",
                                                  1 + int(hf(dk["id"], "na") * 3), f"life:pallets:{dk['id']}")
                if hf(dk["id"], "cones") < 0.5:
                    for i in range(2 + int(hf(dk["id"], "nc") * 2)):
                        c = p0 + d * (u_last + 2.2 + i * 0.9) + nout * (5.0 + hf(dk["id"], i, "co") * 1.5)
                        fp = Point(*c).buffer(0.25)
                        if sp.free(fp):
                            pl.add("cone", c, hf(dk["id"], i, "cy") * 6.283, src=f"life:cones:{dk['id']}")
                            sp.take(fp)
                            cnt["cones"] += 1
        elif typ in ("block", "office"):
            edges = list(_wall_edges(poly))
            if not edges:
                continue
            start = int(hf(key, "binedge") * len(edges))
            for k in range(len(edges)):
                a, q, L, d, nout = edges[(start + k) % len(edges)]
                nb = 2 + int(hf(key, "nbins") * 3)
                u = 1.5
                c0 = a + d * u + nout * 1.4
                fp = rect(a + d * (u + nb * 0.7) + nout * 1.4, d, nb * 0.7 + 0.1, 0.6)
                if not sp.free(fp):
                    continue
                for i in range(nb):
                    c = c0 + d * (0.7 + i * 1.4)
                    col = LP.BIN_COLOURS[int(hf(key, i, "bc") * len(LP.BIN_COLOURS)) % len(LP.BIN_COLOURS)]
                    pl.add(f"bin_1100_{col}", c, yaw_of(-nout) + (hf(key, i, "by") - 0.5) * 0.15,
                           src=f"life:bins:{key}")
                    cnt["bins"] += 1
                sp.take(fp)
                break
    report.update(cnt)


def place(pl, docks, paved, blds, roads_poly, bpoly, route_P, report, buf=None, zsurf=None, park_polys=None):
    rep = {}
    union = shapely.union_all([p["poly"] for p in paved])
    route = LineString(route_P) if route_P is not None and len(route_P) > 1 else None
    sp = Space(union, roads_poly, bpoly, route)
    dock_trailers(pl, docks, sp, rep)
    if buf is not None and zsurf is not None:
        tyre_scrub(buf, docks, zsurf, rep)
    pu = shapely.union_all([shapely.make_valid(p) for p in park_polys]) if park_polys else None
    parking(pl, paved, sp, rep, buf, zsurf, pu)
    stalls = []
    truck_yards(pl, paved, sp, rep, docks, stalls)
    yard_props(pl, blds, docks, sp, rep)
    if buf is not None and zsurf is not None:
        yard_markings(buf, stalls, zsurf, rep)
        yard_drains(buf, paved, bpoly, zsurf, rep)
    rep["start_view_vehicles_skipped"] = sp.start_cleared
    report["life"] = rep
    return rep
