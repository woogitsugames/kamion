"""Building meshes from footprints + heights (BDOT10k/OSM footprints, GUGiK LoD1 heights, LoD2 roof types)
with typology-driven facades.

Typologies (classify()):
  hall      warehouses, production halls, large retail boxes: sandwich-panel walls (vertical ribbing in the
            material, UV u = metres along the wall, v = metres above the reference ground), concrete plinth,
            graphite attic flashing, flat membrane roof with an attic, roof skylights on big halls, personnel
            doors, optional ribbon windows; warehouses facing a paved yard get loading docks
            (sectional door, dock shelter, bumpers, leveller lip with hazard stripes, dock number plate,
            wheel guides, dock light) and a concrete apron in front (handed to streetscape.paved).
  office    office / service buildings: plaster, window grid per storey (3.5 m), entrance door.
  block     multi-family blocks (Białystok wielka płyta): storey 2.8 m, window rhythm 3.0 m, flat roof.
  house     single-family houses: gable roof (LoD2 roof type / eave height when known), 2-3 windows per facade.
  shed      outbuildings, garages, transformer stations: plain walls, garage doors, flat roof.
Openings are real holes in the wall (column decomposition) with reveals, so close cameras see depth.
LOD0 (layer 'buildings') carries the detail; LOD1 ('buildings_low') is a plain prism with the same wall
materials; 'collision' gets the LOD1 prism as material 'collision_building'.
"""

from __future__ import annotations

import hashlib
import math

import numpy as np
import shapely
from shapely.geometry import Polygon, shape

from roads import standards as S

HALL_FUNCS = {"magazyn", "produkcyjny", "warsztat remontowo-naprawczy", "elektrociepłownia", "spalarnia śmieci",
              "industrial", "warehouse", "silos", "stacja pomp", "straż pożarna", "construction"}
WAREHOUSE_FUNCS = {"magazyn", "produkcyjny", "warehouse", "industrial"}
RETAIL_FUNCS = {"obiekt handlowo-usługowy", "centrum handlowe", "supermarket"}
BLOCK_FUNCS = {"budynek wielorodzinny", "hotel"}
HOUSE_FUNCS = {"budynek jednorodzinny", "dom letniskowy"}
SHED_FUNCS = {"budynek gospodarczy", "garaż", "garages", "shed", "carport", "stacja transformatorowa", "garbage_shed",
              "transformer_tower", "service"}

HALL_WALLS = ["hall_wall_grey", "hall_wall_silver", "hall_wall_white", "hall_wall_ivory"]
OFFICE_WALLS = ["plaster_light", "plaster_grey", "plaster_beige"]
BLOCK_WALLS = ["plaster_cream", "plaster_grey", "plaster_pastel_blue", "plaster_light"]
HOUSE_WALLS = ["plaster_light", "plaster_beige", "plaster_cream", "plaster_grey"]
ROOFS_PITCHED = ["roof_tiles_red", "roof_metal_graphite", "roof_tiles_brown"]


def hpick(key, seq, salt=""):
    h = int(hashlib.sha1((key + salt).encode()).hexdigest()[:8], 16)
    return seq[h % len(seq)]


def hfloat(key, salt=""):
    return int(hashlib.sha1((key + salt).encode()).hexdigest()[:8], 16) / 0xFFFFFFFF


def classify(p, area, ovr):
    if ovr.get("typology"):
        return ovr["typology"]
    f = p.get("function")
    h = p.get("height_m") or 6.0
    if f in HALL_FUNCS or (f in RETAIL_FUNCS and area > 1500):
        return "hall"
    if f in BLOCK_FUNCS:
        return "block"
    if f in HOUSE_FUNCS:
        return "house"
    if f in SHED_FUNCS or (area < 60 and h < 5):
        return "shed"
    return "office"


# ------------------------------------------------------------------------------------------- geometry
class Acc:
    """Triangle accumulator per (layer, material)."""

    def __init__(self):
        self.d = {}

    def add(self, layer, mat, V, T, UV=None):
        V = np.asarray(V, float)
        if UV is None:
            UV = V[:, :2]
        lst = self.d.setdefault((layer, mat), [])
        lst.append((V, np.asarray(T, np.int64).reshape(-1, 3), np.asarray(UV, float)))

    def quad(self, layer, mat, a, b, c, d, uv=None):
        """CCW quad a-b-c-d (seen from the front)."""
        V = np.array([a, b, c, d], float)
        if uv is None:
            e1 = V[1] - V[0]
            L = np.linalg.norm(e1)
            H = np.linalg.norm(V[3] - V[0])
            uv = [[0, 0], [L, 0], [L, H], [0, H]]
        self.add(layer, mat, V, [[0, 1, 2], [0, 2, 3]], uv)

    def box(self, layer, mat, c, ax, ay, az):
        """Box centred at c with half-axis vectors ax, ay, az (all 6 faces, outward)."""
        c, ax, ay, az = (np.asarray(x, float) for x in (c, ax, ay, az))
        P = [c + sx * ax + sy * ay + sz * az for sz in (-1, 1) for sy in (-1, 1) for sx in (-1, 1)]
        faces = [(0, 2, 3, 1), (4, 5, 7, 6), (0, 1, 5, 4), (2, 6, 7, 3), (0, 4, 6, 2), (1, 3, 7, 5)]
        if np.dot(np.cross(ax, ay), az) < 0:
            faces = [f[::-1] for f in faces]
        for f in faces:
            self.quad(layer, mat, *[P[i] for i in f])

    def flush(self, buf, src):
        for (layer, mat), items in sorted(self.d.items()):
            V = np.concatenate([it[0] for it in items])
            UV = np.concatenate([it[2] for it in items])
            off = np.cumsum([0] + [len(it[0]) for it in items[:-1]])
            T = np.concatenate([it[1] + o for it, o in zip(items, off)])
            buf.add(layer, mat, V, UV, T, src=src)


def wall_with_openings(acc, layer, mat, p0, d, nout, L, zb, zt, openings, u0=0.0, vref=0.0):
    """Wall rectangle [0, L] x [zb, zt] in the vertical plane through p0 along d, minus rectangular
    openings [(ua, ub, va, vb, depth, kind, mat_in)]. Adds reveals and the recessed infill."""
    p0, d, nout = (np.asarray(x, float) for x in (p0, d, nout))
    ops = sorted([o for o in openings if o[1] > o[0] + 0.05 and o[3] > o[2] + 0.05], key=lambda o: o[0])
    us = sorted({0.0, L, *[o[0] for o in ops], *[o[1] for o in ops]})

    def P(u, z):
        return [p0[0] + d[0] * u, p0[1] + d[1] * u, z]

    for ua, ub in zip(us, us[1:]):
        if ub - ua < 1e-4:
            continue
        um = 0.5 * (ua + ub)
        cov = sorted([(o[2], o[3]) for o in ops if o[0] <= um <= o[1]])
        z = zb
        segs = []
        for va, vb in cov:
            if va > z:
                segs.append((z, va))
            z = max(z, vb)
        if z < zt:
            segs.append((z, zt))
        for za, zb2 in segs:
            acc.quad(layer, mat, P(ua, za), P(ub, za), P(ub, zb2), P(ua, zb2),
                     uv=[[u0 + ua, za - vref], [u0 + ub, za - vref], [u0 + ub, zb2 - vref], [u0 + ua, zb2 - vref]])
    n3 = np.append(nout[:2], 0.0)
    d3 = np.append(d[:2], 0.0)
    for (ua, ub, va, vb, depth, kind, mat_in) in ops:
        back = -n3 * depth
        A, B, C, D = (np.array(P(ua, va)), np.array(P(ub, va)), np.array(P(ub, vb)), np.array(P(ua, vb)))
        rv = "reveal_" + ("hall" if mat.startswith("hall") else "plaster")
        # reveals (facing into the opening)
        acc.quad(layer, rv, A, B, B + back, A + back)          # sill (faces up)
        acc.quad(layer, rv, D + back, C + back, C, D)          # head (faces down)
        acc.quad(layer, rv, A + back, D + back, D, A)          # left jamb (faces +d)
        acc.quad(layer, rv, B, C, C + back, B + back)          # right jamb (faces -d)
        w, h = ub - ua, vb - va
        acc.quad(layer, mat_in, A + back, B + back, C + back, D + back, uv=[[0, 0], [w, 0], [w, h], [0, h]])
        if kind == "window" and w > 1.25:                   # mullion
            um = 0.5 * (ua + ub)
            c = np.array(P(um, 0.5 * (va + vb))) + back + n3 * 0.04
            acc.box(layer, "window_frame", c, d3 * 0.035, n3 * 0.035, [0, 0, h / 2])
        if kind == "window":                                 # transom + sill flashing
            c = np.array(P(0.5 * (ua + ub), va)) + n3 * 0.03
            acc.box(layer, "hall_flashing" if mat.startswith("hall") else "window_sill", c, d3 * (w / 2 + 0.04),
                    n3 * 0.05, [0, 0, 0.02])


def ring_edges(ring):
    c = np.asarray(ring.coords)[:-1]
    keep = []
    n = len(c)
    for i in range(n):              # drop nearly collinear / tiny vertices
        a, b, cc = c[i - 1], c[i], c[(i + 1) % n]
        v1, v2 = b - a, cc - b
        cr = abs(v1[0] * v2[1] - v1[1] * v2[0]) / max(np.linalg.norm(v1) * np.linalg.norm(v2), 1e-9)
        if cr > 0.03 or np.linalg.norm(v1) > 6:
            keep.append(b)
    c = np.asarray(keep) if len(keep) >= 3 else c
    return [(c[i], c[(i + 1) % len(c)]) for i in range(len(c))]


def roof_flat(acc, layer, poly, z, mat="roof_membrane", attic=0.3, skylights=False, key=""):
    inner = poly.buffer(-0.25, join_style="mitre")
    if inner.is_empty or attic <= 0:
        inner, attic = poly, 0.0
    for g in getattr(inner, "geoms", [inner]):
        if g.geom_type != "Polygon":
            continue
        tri = shapely.constrained_delaunay_triangles(g)
        T = np.array([np.asarray(t.exterior.coords)[:3] for t in tri.geoms])
        if not len(T):
            continue
        cr = (T[:, 1, 0] - T[:, 0, 0]) * (T[:, 2, 1] - T[:, 0, 1]) - (T[:, 1, 1] - T[:, 0, 1]) * (T[:, 2, 0] - T[:, 0, 0])
        T[cr < 0] = T[cr < 0][:, [0, 2, 1]]
        V = np.concatenate([T.reshape(-1, 2), np.full((len(T) * 3, 1), z - attic)], axis=1)
        acc.add(layer, mat, V, np.arange(len(V)).reshape(-1, 3), V[:, :2])
        if attic > 0:   # attic: inner faces + cap
            for ring in [g.exterior, *g.interiors]:
                cc = np.asarray(ring.coords)
                if ring.is_ccw != (ring is g.exterior):
                    cc = cc[::-1]
                for a, b in zip(cc, cc[1:]):
                    # inner face looks into the roof (left of CCW travel)
                    acc.quad(layer, "hall_flashing", [b[0], b[1], z - attic], [a[0], a[1], z - attic],
                             [a[0], a[1], z], [b[0], b[1], z])
        cap = poly.difference(g)
        for cg in getattr(cap, "geoms", [cap]):
            if cg.geom_type != "Polygon" or cg.area < 1e-3:
                continue
            tri = shapely.constrained_delaunay_triangles(cg)
            T = np.array([np.asarray(t.exterior.coords)[:3] for t in tri.geoms])
            if not len(T):
                continue
            cr = (T[:, 1, 0] - T[:, 0, 0]) * (T[:, 2, 1] - T[:, 0, 1]) - (T[:, 1, 1] - T[:, 0, 1]) * (T[:, 2, 0] - T[:, 0, 0])
            T[cr < 0] = T[cr < 0][:, [0, 2, 1]]
            V = np.concatenate([T.reshape(-1, 2), np.full((len(T) * 3, 1), z)], axis=1)
            acc.add(layer, "hall_flashing", V, np.arange(len(V)).reshape(-1, 3), V[:, :2])
    if skylights and poly.area > 3000:
        core = poly.buffer(-8.0)
        if core.is_empty:
            return
        ang = _angle(poly)
        ca, sa = math.cos(ang), math.sin(ang)
        x0, y0, x1, y1 = shapely.affinity.rotate(core, -ang, origin=(0, 0), use_radians=True).bounds
        for gx in np.arange(x0 + 3, x1 - 3, 12.0):
            for gy in np.arange(y0 + 3, y1 - 3, 9.0):
                cx, cy = gx * ca - gy * sa, gx * sa + gy * ca
                if not core.contains(shapely.Point(cx, cy)):
                    continue
                acc.box(layer, "skylight", [cx, cy, z - attic + 0.25], [ca * 1.5, sa * 1.5, 0], [-sa * 1.0, ca * 1.0, 0],
                        [0, 0, 0.25])


def _angle(poly):
    r = np.asarray(poly.minimum_rotated_rectangle.exterior.coords)
    d = np.diff(r, axis=0)
    k = int(np.argmax(np.hypot(d[:, 0], d[:, 1])))
    return math.atan2(d[k, 1], d[k, 0])


def gable(acc, layer, rect, zeave, zridge, wall_mat, roof_mat):
    """Gable roof over a rectangle (ridge along the long side) + gable-end wall triangles."""
    c = np.asarray(rect.exterior.coords)[:4]
    if not Polygon(c).exterior.is_ccw:
        c = c[::-1]
    e = [np.linalg.norm(c[(i + 1) % 4] - c[i]) for i in range(4)]
    k = 0 if e[0] >= e[1] else 1          # c[k]->c[k+1] is a long side
    a, b, cc, d = (c[(k + i) % 4] for i in range(4))
    m1, m2 = 0.5 * (a + d), 0.5 * (b + cc)  # ridge ends above the short sides
    ov = 0.4
    t = (b - a) / np.linalg.norm(b - a)
    m1o, m2o = m1 - t * ov, m2 + t * ov
    def P(p, z):
        return [p[0], p[1], z]
    # slopes with overhang
    nn1 = (a - m1) / max(np.linalg.norm(a - m1), 1e-6)
    nn2 = (cc - m2) / max(np.linalg.norm(cc - m2), 1e-6)
    drop = ov * (zridge - zeave) / max(np.linalg.norm(a - m1), 1e-6)
    ao, bo = a - t * ov + nn1 * ov, b + t * ov + nn1 * ov
    co, do = cc + t * ov + nn2 * ov, d - t * ov + nn2 * ov
    acc.quad(layer, roof_mat, P(ao, zeave - drop), P(bo, zeave - drop), P(m2o, zridge), P(m1o, zridge))
    acc.quad(layer, roof_mat, P(co, zeave - drop), P(do, zeave - drop), P(m1o, zridge), P(m2o, zridge))
    # gable triangles (short sides): b->cc and d->a
    for p, q, m in ((b, cc, m2), (d, a, m1)):
        V = [P(p, zeave), P(q, zeave), P(m, zridge)]
        L = np.linalg.norm(q - p)
        acc.add(layer, wall_mat, V, [[0, 1, 2]], [[0, zeave], [L, zeave], [L / 2, zridge]])


# ------------------------------------------------------------------------------------------- facades
def facade_openings(typ, L, zref, ztop, storeys, key, is_main, docks_here):
    """Openings for one wall edge (u along the edge from its start), in absolute z."""
    ops = []
    if typ == "hall":
        if docks_here:
            return ops
        if is_main and L > 6:
            n = max(1, int(L // 40))
            for i in range(n):
                um = (i + 0.5) * L / n + (2.5 if i % 2 else -2.5)
                ops.append((um - 0.5, um + 0.5, zref + 0.15, zref + 2.25, 0.08, "door", "door_steel"))
        if L > 18 and hfloat(key, "win") < 0.55:
            zw = min(zref + 3.2, ztop - 1.6)
            pitch = 6.0
            n = int((L - 6) // pitch)
            for i in range(n):
                um = (L - (n - 1) * pitch) / 2 + i * pitch
                if any(abs(um - (o[0] + o[1]) / 2) < 1.6 for o in ops):
                    continue
                ops.append((um - 1.0, um + 1.0, zw, zw + 1.0, 0.12, "window", "glass"))
        return ops
    if typ == "shed":
        if is_main and L > 3.2 and hfloat(key, "gar") < 0.6:
            n = max(1, min(4, int(L // 3.2)))
            for i in range(n):
                um = (i + 0.5) * L / n
                ops.append((um - 1.25, um + 1.25, zref + 0.05, zref + 2.2, 0.1, "door", "garage_door"))
        elif is_main and L > 2:
            ops.append((L / 2 - 0.45, L / 2 + 0.45, zref + 0.05, zref + 2.05, 0.06, "door", "door_steel"))
        return ops
    sh = {"office": 3.5, "block": 2.8, "house": 2.9}[typ]
    ww, wh, sill, pitch = {"office": (1.5, 1.6, 0.9, 3.0), "block": (1.5, 1.45, 0.9, 3.0),
                           "house": (1.2, 1.4, 0.9, 3.6)}[typ]
    n = int((L - 1.0) // pitch)
    if typ == "house":
        n = min(n, 3)
    if n < 1:
        return ops
    door_i = n // 2 if is_main else -1
    for s in range(storeys):
        z0 = zref + 0.3 + s * sh
        if z0 + sill + wh > ztop - 0.3:
            break
        for i in range(n):
            um = (L - (n - 1) * pitch) / 2 + i * pitch
            if s == 0 and i == door_i:
                dw = 1.6 if typ != "house" else 1.0
                ops.append((um - dw / 2, um + dw / 2, zref + 0.15, zref + 2.4, 0.15, "door",
                            "door_glass" if typ == "office" else "door_steel"))
                continue
            w = ww if not (typ == "block" and i % 3 == 2) else 0.9
            ops.append((um - w / 2, um + w / 2, z0 + sill, z0 + sill + wh, 0.14, "window", "glass"))
    return ops


def docks_for(b, poly, yard, hero, zsample):
    """Dock positions along yard-facing facades of a warehouse hall."""
    out = []
    if yard is None or yard.is_empty:
        return out
    ring = poly.exterior
    edges = ring_edges(ring)
    if not ring.is_ccw:
        edges = [(q, p) for p, q in edges[::-1]]
    num = 1
    for ei, (p, q) in enumerate(edges):
        L = float(np.linalg.norm(q - p))
        if L < 16:
            continue
        d = (q - p) / L
        nout = np.array([d[1], -d[0]])
        strip = Polygon([p + nout * 2, q + nout * 2, q + nout * 14, p + nout * 14])
        if strip.intersection(yard).area / strip.area < 0.6:
            continue
        n = int((L - 8) // S.DOCK_PITCH)
        if hero:
            n = min(n, hero.get("max_docks_per_facade", 24))
        else:
            n = min(n, 12)
        if n < 2:
            continue
        u0 = (L - (n - 1) * S.DOCK_PITCH) / 2
        mid = p + d * (L / 2) + nout * 3
        zy = float(zsample(np.array([mid[0]]), np.array([mid[1]]))[0])
        docks = []
        for i in range(n):
            u = u0 + i * S.DOCK_PITCH
            docks.append({"u": u, "num": num})
            num += 1
        a0 = p + d * (u0 - 2.5)
        a1 = p + d * (u0 + (n - 1) * S.DOCK_PITCH + 2.5)
        apron = Polygon([a0, a1, a1 + nout * S.DOCK_APRON_L, a0 + nout * S.DOCK_APRON_L])
        out.append({"id": f"{b['id']}:docks{ei}", "edge": (p, q), "docks": docks, "yard_z": zy, "apron": apron})
    return out


def build_dock(acc, layer, p, d, nout, u, zy, num):
    """One loading dock at u along the wall (yard level zy)."""
    zf = zy + S.DOCK_FLOOR_H
    c = p + d * u
    W, H = S.DOCK_DOOR_W, S.DOCK_DOOR_H
    def P(off_u, z, out=0.0):
        q = c + d * off_u + nout * out
        return np.array([q[0], q[1], z])
    # shelter: two side curtains + header (black PVC), proud of the wall
    sw, sh, sd = S.DOCK_SHELTER_W, S.DOCK_SHELTER_H, S.DOCK_SHELTER_D
    side = (sw - W) / 2 + 0.05
    for sgn in (-1, 1):
        cc = P(sgn * (W / 2 + side / 2), zf + sh / 2 - 0.1, sd / 2)
        acc.box(layer, "dock_shelter", cc, np.append(d * side / 2, 0), np.append(nout * sd / 2, 0), [0, 0, sh / 2 - 0.1])
        # yellow guide stripe on the curtain face
        acc.box(layer, "paint_yellow", P(sgn * (W / 2 + side / 2), zf + sh / 2 - 0.1, sd + 0.005),
                np.append(d * 0.05, 0), np.append(nout * 0.005, 0), [0, 0, sh / 2 - 0.3])
    acc.box(layer, "dock_shelter", P(0, zf + sh - 0.35, sd / 2), np.append(d * (sw / 2 + 0.05), 0),
            np.append(nout * sd / 2, 0), [0, 0, 0.35])
    # leveller lip (steel) + hazard stripes front, bumpers
    acc.box(layer, "steel_checker", P(0, zf - 0.03, 0.2), np.append(d * 1.0, 0), np.append(nout * 0.2, 0), [0, 0, 0.03])
    acc.quad(layer, "hazard_stripes", P(-1.0, zf - 0.33, 0.405), P(1.0, zf - 0.33, 0.405), P(1.0, zf - 0.06, 0.405),
             P(-1.0, zf - 0.06, 0.405), uv=[[0, 0], [2.0, 0], [2.0, 0.27], [0, 0.27]])
    acc.box(layer, "steel_checker", P(0, zf - 0.2, 0.2), np.append(d * 1.0, 0), np.append(nout * 0.2, 0), [0, 0, 0.14])
    for sgn in (-1, 1):
        acc.box(layer, "rubber_black", P(sgn * 1.15, zf - 0.25, 0.06), np.append(d * 0.13, 0), np.append(nout * 0.06, 0),
                [0, 0, 0.25])
        # wheel guide (yellow steel tube on the apron)
        acc.box(layer, "paint_yellow", P(sgn * 1.35, zy + 0.12, 2.6), np.append(d * 0.06, 0), np.append(nout * 2.2, 0),
                [0, 0, 0.12])
    # number plate above the shelter (white plate, black digits: atlas UV)
    s = str(num)
    pw = 0.32 * len(s)
    z0 = zf + sh + 0.15
    acc.quad(layer, "plate_white", P(-pw / 2 - 0.06, z0 - 0.06, 0.03), P(pw / 2 + 0.06, z0 - 0.06, 0.03),
             P(pw / 2 + 0.06, z0 + 0.46, 0.03), P(-pw / 2 - 0.06, z0 + 0.46, 0.03))
    for k, ch in enumerate(s):
        x0 = -pw / 2 + k * 0.32
        dgt = int(ch)
        acc.quad(layer, "dock_digits", P(x0, z0, 0.035), P(x0 + 0.32, z0, 0.035), P(x0 + 0.32, z0 + 0.4, 0.035),
                 P(x0, z0 + 0.4, 0.035), uv=[[dgt / 10, 0], [(dgt + 1) / 10, 0], [(dgt + 1) / 10, 1], [dgt / 10, 1]])
    # dock signal light (red/green box) right of the door
    acc.box(layer, "dock_light", P(W / 2 + side + 0.35, zf + 1.4, 0.08), np.append(d * 0.12, 0), np.append(nout * 0.08, 0),
            [0, 0, 0.22])


# ------------------------------------------------------------------------------------------- main
def load(fc, origin, overrides):
    ox, oy = origin
    ovr = {o["target"]["building"]: o["set"] for o in overrides if o.get("target", {}).get("building")}
    out = []
    for f in fc["features"]:
        p = f["properties"]
        for k, poly in enumerate(f["geometry"]["coordinates"]):
            pl = Polygon(np.asarray(poly[0]) - [ox, oy], [np.asarray(h) - [ox, oy] for h in poly[1:]])
            pl = shapely.make_valid(pl)
            if pl.geom_type != "Polygon":
                pl = max(getattr(pl, "geoms", [pl]), key=lambda g: g.area if g.geom_type == "Polygon" else 0)
                if pl.geom_type != "Polygon":
                    continue
            pl = shapely.orient_polygons(pl) if hasattr(shapely, "orient_polygons") else shapely.geometry.polygon.orient(pl)
            bid = f["id"] if k == 0 else f"{f['id']}#{k}"
            o = ovr.get(f["id"], {})
            out.append({"id": bid, "poly": pl, "props": p, "ovr": o, "typ": "roof" if p.get("is_roof_only") else
                        classify(p, pl.area, o)})
    return out


def build(buf, blds, hf, zsample, yard_union, roads_poly, report):
    """Generate building meshes into buf; returns dock descriptions (for the paved aprons)."""
    all_docks = []
    counts = {}
    for b in blds:
        poly, p, typ = b["poly"], b["props"], b["typ"]
        counts[typ] = counts.get(typ, 0) + 1
        ring = np.asarray(poly.exterior.coords)
        zg = hf.sample(ring[:, 0], ring[:, 1])
        zref = float(np.median(zg))
        zbot = float(np.min(zg)) - 0.5
        h = float(p.get("height_m") or 6.0)
        ztop = zref + h
        key = b["id"]
        acc = Acc()
        if typ == "roof":            # canopy on columns (fuel station)
            zc = zref + min(max(h, 4.8), 6.0)
            roof_flat(acc, "buildings", poly, zc + 0.6, mat="hall_flashing", attic=0.0)
            for g in [poly]:
                acc.box("buildings", "canopy_fascia", [*g.centroid.coords[0], zc + 0.3], [0.01, 0, 0], [0, 0.01, 0], [0, 0, 0.01])
            cc = np.asarray(poly.minimum_rotated_rectangle.exterior.coords)[:4]
            for q in cc:
                v = np.asarray(poly.centroid.coords[0]) + (q - np.asarray(poly.centroid.coords[0])) * 0.7
                acc.box("buildings", "steel_painted", [v[0], v[1], (zref + zc) / 2], [0.15, 0, 0], [0, 0.15, 0],
                        [0, 0, (zc - zref) / 2 + 0.3])
            acc.flush(buf, key)
            continue
        if typ == "hall":
            wall = b["ovr"].get("wall_material") or hpick(key, HALL_WALLS)
        elif typ == "block":
            wall = hpick(key, BLOCK_WALLS)
        elif typ == "house":
            wall = hpick(key, HOUSE_WALLS)
        elif typ == "shed":
            wall = hpick(key, ["plaster_grey", "plaster_light", "brick_red", "hall_wall_silver"])
        else:
            wall = hpick(key, OFFICE_WALLS)
        hero = b["ovr"].get("hero")
        docks = []
        if typ == "hall" and (p.get("function") in WAREHOUSE_FUNCS or b["ovr"].get("docks")) and poly.area > 800:
            docks = docks_for(b, poly, yard_union, b["ovr"] if hero else None, zsample)
            all_docks += docks
        storeys = max(1, int(round((h - 1.0) / {"office": 3.5, "block": 2.8, "house": 2.9}.get(typ, 4.0))))
        pitched = typ == "house" and (p.get("roof_type_lod2") in (None, "1030", "1040", "1130", "1050"))
        rect = poly.minimum_rotated_rectangle
        if pitched and poly.area / max(rect.area, 1e-6) > 0.82 and poly.area < 400:
            work = shapely.geometry.polygon.orient(rect)
        else:
            work = poly
            pitched = False
        zeave = ztop
        if pitched:
            c = np.asarray(work.exterior.coords)
            w_short = min(np.linalg.norm(c[1] - c[0]), np.linalg.norm(c[2] - c[1]))
            rise = 0.5 * w_short * math.tan(math.radians(35))
            eave_rel = p.get("lod2_eave_rel_m")
            zeave = zref + (eave_rel if eave_rel and 2.4 < eave_rel < h - 0.5 else max(h - rise, 2.6))
            ztop = max(ztop, zeave + 1.0)
        # main facade = edge closest to a road
        edges = ring_edges(work.exterior)
        dist = [roads_poly.distance(shapely.Point(*(0.5 * (a + c_)))) if roads_poly is not None else 0 for a, c_ in edges]
        main = int(np.argmin(dist)) if dist else 0
        u_acc = 0.0
        dock_edges = {tuple(np.round(dk["edge"][0], 2)): dk for dk in docks}
        for ei, (a, c_) in enumerate(edges):
            L = float(np.linalg.norm(c_ - a))
            if L < 0.05:
                continue
            d = (c_ - a) / L
            nout = np.array([d[1], -d[0]])
            dk = dock_edges.get(tuple(np.round(a, 2)))
            zt = zeave
            ops = facade_openings(typ, L, zref, zt, storeys, f"{key}:{ei}", ei == main or (typ == "hall" and L > 30),
                                  dk is not None)
            if dk:
                zf = dk["yard_z"] + S.DOCK_FLOOR_H
                for dock in dk["docks"]:
                    ops.append((dock["u"] - S.DOCK_DOOR_W / 2, dock["u"] + S.DOCK_DOOR_W / 2, zf, zf + S.DOCK_DOOR_H,
                                0.25, "dock", "dock_door"))
            if typ == "hall":
                # plinth (concrete, up to dock floor) + sandwich panels + flashing band on top
                zpl = (dk["yard_z"] + S.DOCK_FLOOR_H) if dk else zref + 0.6
                wall_with_openings(acc, "buildings", "hall_plinth", a, d, nout, L, zbot, zpl,
                                   [o for o in ops if o[2] < zpl], u0=u_acc, vref=zref)
                wall_with_openings(acc, "buildings", wall, a, d, nout, L, zpl, zt - 0.4,
                                   [(o[0], o[1], max(o[2], zpl), o[3], o[4], o[5], o[6]) for o in ops if o[3] > zpl],
                                   u0=u_acc, vref=zref)
                P3 = lambda q, z: [q[0], q[1], z]
                acc.quad("buildings", "hall_flashing", P3(a + nout * 0.03, zt - 0.4), P3(c_ + nout * 0.03, zt - 0.4),
                         P3(c_ + nout * 0.03, zt), P3(a + nout * 0.03, zt))
                if dk:
                    for dock in dk["docks"]:
                        build_dock(acc, "buildings", a, d, nout, dock["u"], dk["yard_z"], dock["num"])
                    # canopy over the dock row (steel, typical) only for hero buildings
                    if hero:
                        u0d, u1d = dk["docks"][0]["u"] - 2.2, dk["docks"][-1]["u"] + 2.2
                        cz = zf + S.DOCK_SHELTER_H + 0.9
                        cm = a + d * (0.5 * (u0d + u1d)) + nout * 1.0
                        acc.box("buildings", "steel_painted", [cm[0], cm[1], cz], np.append(d * (u1d - u0d) / 2, 0),
                                np.append(nout * 1.0, 0), [0, 0, 0.08])
            else:
                zpl = zref + 0.35
                wall_with_openings(acc, "buildings", "plinth_dark", a, d, nout, L, zbot, zpl,
                                   [o for o in ops if o[2] < zpl], u0=u_acc, vref=zref)
                wall_with_openings(acc, "buildings", wall, a, d, nout, L, zpl, zt,
                                   [(o[0], o[1], max(o[2], zpl), o[3], o[4], o[5], o[6]) for o in ops if o[3] > zpl],
                                   u0=u_acc, vref=zref)
            # LOD1 + collision: plain wall
            for layer, mat in (("buildings_low", wall), ("collision", "collision_building")):
                acc.quad(layer, mat, [a[0], a[1], zbot], [c_[0], c_[1], zbot], [c_[0], c_[1], zt], [a[0], a[1], zt],
                         uv=[[u_acc, zbot - zref], [u_acc + L, zbot - zref], [u_acc + L, zt - zref], [u_acc, zt - zref]])
            u_acc += L
        # courtyard walls (holes), plain
        for hole in poly.interiors if not pitched else []:
            for a, c_ in ring_edges(hole):
                L = float(np.linalg.norm(c_ - a))
                acc.quad("buildings", wall, [a[0], a[1], zbot], [c_[0], c_[1], zbot], [c_[0], c_[1], zeave], [a[0], a[1], zeave])
        if pitched:
            roof = hpick(key, ROOFS_PITCHED, "roof")
            for layer in ("buildings", "buildings_low"):
                gable(acc, layer, work, zeave, ztop, wall, roof)
            gable(acc, "collision", work, zeave, ztop, "collision_building", "collision_building")
        else:
            roof_flat(acc, "buildings", poly, zeave, attic=0.3 if typ in ("hall", "office", "block") else 0.15,
                      skylights=typ == "hall", key=key)
            roof_flat(acc, "buildings_low", poly, zeave, attic=0.0)
            roof_flat(acc, "collision", poly, zeave, mat="collision_building", attic=0.0)
        acc.flush(buf, key)
    report.update({"typologies": counts, "docks": sum(len(d["docks"]) for d in all_docks),
                   "dock_facades": [d["id"] for d in all_docks]})
    return all_docks
