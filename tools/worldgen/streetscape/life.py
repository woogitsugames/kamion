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
Everything keeps clear of road surfaces (incl. flush yard roads), buildings and a 5 m corridor along the start
route, and must stand on a paved area. Liveries are plain colours; no lettering or logos.
"""

from __future__ import annotations

import hashlib
import math

import numpy as np
import shapely
from shapely import affinity
from shapely.geometry import LineString, Point, Polygon

from roads import decals as DC
from roads import standards as S

from . import life_props as LP

CAR_SHARE = [("silver", 0.22), ("grey", 0.20), ("black", 0.18), ("white", 0.18), ("blue", 0.09), ("red", 0.07),
             ("green", 0.03), ("beige", 0.03)]
BODY_SHARE = [("hatch", 0.38), ("sedan", 0.24), ("estate", 0.38)]


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
            if not sp.free(body):
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


def parking(pl, paved, sp, report, buf=None, zsurf=None):
    cars = vans = bays = 0
    oil = 0
    for item in paved:
        if not item.get("parking"):
            continue
        for i, (c, nose) in enumerate(_bays(item["poly"], item["id"])):
            bays += 1
            key = (item["id"], i)
            if buf is not None and hf(*key, "oil") < 0.35:      # drip stain under the engine bay
                P0 = c + nose * 1.1 + np.array([nose[1], -nose[0]]) * (hf(*key, "ox") - 0.5) * 0.6

                def z_of(V2):
                    return zsurf(V2[:, 0], V2[:, 1]) + S.PAVED_LIFT + 0.008     # yard mesh is linear on 4 m cells
                DC.stain(buf, P0, z_of, 0.2 + hf(*key, "or") * 0.3, key, f"oil:{item['id']}:{i}")
                oil += 1
            if hf(*key, "occ") > 0.60:
                continue
            jit = (hf(*key, "jx") - 0.5) * 0.3
            c2 = c + np.array([nose[1], -nose[0]]) * jit + nose * (hf(*key, "jy") - 0.5) * 0.4
            yaw = yaw_of(nose) + (hf(*key, "yaw") - 0.5) * 0.08
            if hf(*key, "van") < 0.15:
                proto = f"van_{pick([('white', 0.5), ('silver', 0.25), ('white2', 0.25)], hf(*key, 'col'))}"
                fp = rect(c2, nose, 2.75, 1.05)
            else:
                proto = f"car_{pick(BODY_SHARE, hf(*key, 'body'))}_{pick(CAR_SHARE, hf(*key, 'col'))}"
                fp = rect(c2, nose, 2.4, 0.95)
            if not sp.free(fp):
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


def place(pl, docks, paved, blds, roads_poly, bpoly, route_P, report, buf=None, zsurf=None):
    rep = {}
    union = shapely.union_all([p["poly"] for p in paved])
    route = LineString(route_P) if route_P is not None and len(route_P) > 1 else None
    sp = Space(union, roads_poly, bpoly, route)
    dock_trailers(pl, docks, sp, rep)
    parking(pl, paved, sp, rep, buf, zsurf)
    yard_props(pl, blds, docks, sp, rep)
    report["life"] = rep
    return rep
