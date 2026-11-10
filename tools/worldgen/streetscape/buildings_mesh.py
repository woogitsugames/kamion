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

from . import facade_atlas as FA
from . import facade_kit as FK

HALL_FUNCS = {"magazyn", "produkcyjny", "warsztat remontowo-naprawczy", "elektrociepłownia", "spalarnia śmieci",
              "industrial", "warehouse", "silos", "stacja pomp", "straż pożarna", "construction"}
WAREHOUSE_FUNCS = {"magazyn", "produkcyjny", "warehouse", "industrial"}
RETAIL_FUNCS = {"obiekt handlowo-usługowy", "centrum handlowe", "supermarket"}
BLOCK_FUNCS = {"budynek wielorodzinny", "hotel"}
HOUSE_FUNCS = {"budynek jednorodzinny", "dom letniskowy"}
SHED_FUNCS = {"budynek gospodarczy", "garaż", "garages", "shed", "carport", "stacja transformatorowa", "garbage_shed",
              "transformer_tower", "service"}

HALL_WALLS = ["hall_wall_grey", "hall_wall_silver", "hall_wall_white", "hall_wall_ivory"]
# Białystok after thermo-modernisation (2000s-2010s): warm light pastels dominate (cream, light yellow, peach,
# sage), cool grey / blue less often; offices in the Andersa / Kwadrat Park industrial area: light grey and
# beige render, a few PRL-era plant offices in brick. WORKING_VALUE palette, to be checked against the owner's
# photo session (docs/map-decisions.md). Far (LOD1) variants: streetscape.materials._FAR_WALLS.
OFFICE_WALLS = ["plaster_light", "plaster_grey", "plaster_beige", "plaster_white", "plaster_light", "plaster_grey",
                "brick_red"]                     # brick 1 in 7 (v3.1 render: two neighbouring brick offices)
BLOCK_WALLS = ["plaster_cream", "plaster_grey", "plaster_pastel_blue", "plaster_light", "plaster_yellow",
               "plaster_peach", "plaster_sage"]
HOUSE_WALLS = ["plaster_light", "plaster_beige", "plaster_cream", "plaster_grey"]
ROOFS_PITCHED = ["roof_tiles_red", "roof_metal_graphite", "roof_tiles_brown"]
STOREY_H = {"office": 3.5, "block": 2.8, "house": 2.9}
ZBASE = {"block": 1.0, "office": 0.45}       # ground floor level above the ground (blocks: high basement), m


def storey_plan(typ, h, p):
    """(storeys, storey height, ground floor level) - BDOT10k LICZBAKONDYGNACJI (`storeys`) when it fits the
    LoD1 height (2.6-3.8 m per storey for blocks, 2.8-4.6 m for offices), else derived from the height."""
    sh = STOREY_H.get(typ, 4.0)
    zb = ZBASE.get(typ, 0.3)
    n = max(1, int(round((h - 1.0) / sh)))
    nb = p.get("storeys")
    if typ in ("office", "block") and nb:
        shb = (h - zb - 0.8) / float(nb)
        lo, hi = (2.6, 3.8) if typ == "block" else (2.8, 4.6)
        if lo <= shb <= hi:
            return int(nb), shb, zb
    if typ in ZBASE and n * sh + zb + 0.6 > h:
        n = max(1, int((h - zb - 0.6) // sh))
    return n, sh, zb


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

    def add(self, layer, mat, V, T, UV=None, UV1=None):
        V = np.asarray(V, float)
        if UV is None:
            UV = V[:, :2]
        lst = self.d.setdefault((layer, mat), [])
        lst.append((V, np.asarray(T, np.int64).reshape(-1, 3), np.asarray(UV, float),
                    None if UV1 is None else np.asarray(UV1, float)))

    def quad(self, layer, mat, a, b, c, d, uv=None, uv1=None):
        """CCW quad a-b-c-d (seen from the front)."""
        V = np.array([a, b, c, d], float)
        if uv is None:
            e1 = V[1] - V[0]
            L = np.linalg.norm(e1)
            H = np.linalg.norm(V[3] - V[0])
            uv = [[0, 0], [L, 0], [L, H], [0, H]]
        self.add(layer, mat, V, [[0, 1, 2], [0, 2, 3]], uv, uv1)

    def box(self, layer, mat, c, ax, ay, az, skip=()):
        """Box centred at c with half-axis vectors ax, ay, az (all 6 faces, outward). skip: face indices left out
        (0 -az, 1 +az, 2 -ay, 3 +ay, 4 -ax, 5 +ax), for the cheap LOD1 silhouette pieces whose hidden faces never show."""
        c, ax, ay, az = (np.asarray(x, float) for x in (c, ax, ay, az))
        P = [c + sx * ax + sy * ay + sz * az for sz in (-1, 1) for sy in (-1, 1) for sx in (-1, 1)]
        faces = [(0, 2, 3, 1), (4, 5, 7, 6), (0, 1, 5, 4), (2, 6, 7, 3), (0, 4, 6, 2), (1, 3, 7, 5)]
        if np.dot(np.cross(ax, ay), az) < 0:
            faces = [f[::-1] for f in faces]
        for k, f in enumerate(faces):
            if k not in skip:
                self.quad(layer, mat, *[P[i] for i in f])

    # parapet run-off coverage (REVIEW G3 wires-streaks-v2): hall_wall_* triangles with / without wall-top TEXCOORD_1
    runoff_tris = {"with_uv1": 0, "without_uv1": 0}

    def flush(self, buf, src):
        for (layer, mat), items in sorted(self.d.items()):
            if str(mat).startswith("hall_wall"):
                for it in items:
                    Acc.runoff_tris["with_uv1" if it[3] is not None else "without_uv1"] += len(it[1])
            V = np.concatenate([it[0] for it in items])
            UV = np.concatenate([it[2] for it in items])
            UV1 = (np.concatenate([it[3] if it[3] is not None else np.zeros((len(it[0]), 2)) for it in items])
                   if any(it[3] is not None for it in items) else None)
            off = np.cumsum([0] + [len(it[0]) for it in items[:-1]])
            T = np.concatenate([it[1] + o for it, o in zip(items, off)])
            buf.add(layer, mat, V, UV, T, src=src, UV1=UV1)


def cells(kind, *variants):
    """Opening infill drawn from the facade atlas (ADR 0081): one cell per variant, side by side across the opening.
    ("atlas", [(u0, v0, w, h) ...], fu0, fu1, fv0, fv1) - the f* fractions are the part of the opening a wall piece
    keeps (facade_kit.wall_pieces clips openings)."""
    return ("atlas", [FA.cell(kind, v) for v in variants], 0.0, 1.0, 0.0, 1.0)


RUNOFF_PERIOD_M = 24.0       # u period of the parapet_runoff layer (art-source/world/materials, sets_facade)


def runoff_uv1(runoff, ua, ub, za, zb):
    """TEXCOORD_1 of a wall quad [ua, ub] x [za, zb] for the parapet run-off streaks (Kamion/World PBR _RUNOFF):
    (u_offset + u, 1 + (z_top - z) / length_scale). The engine stores TEXCOORD_1 as half floats (WorldMeshBake), so u is
    shifted per quad by a whole number of layer periods: the pattern is unchanged (the layer tiles in u) but |u| stays
    below period + quad length (< 1/16 m half-float step) instead of the building perimeter (0.25-1 m steps -> pattern
    seams and smeared streaks on big halls). None when runoff is None."""
    if runoff is None:
        return None
    zt_r, uo, ls = runoff
    a = uo + ua
    sh = RUNOFF_PERIOD_M * math.floor(a / RUNOFF_PERIOD_M)
    a, b = a - sh, uo + ub - sh
    ka, kb = 1 + (zt_r - za) / ls, 1 + (zt_r - zb) / ls
    return [[a, ka], [b, ka], [b, kb], [a, kb]]


def wall_with_openings(acc, layer, mat, p0, d, nout, L, zb, zt, openings, u0=0.0, vref=0.0, runoff=None, reveal=None):
    """Wall rectangle [0, L] x [zb, zt] in the vertical plane through p0 along d, minus rectangular
    openings [(ua, ub, va, vb, depth, kind, mat_in)]. Adds reveals and the recessed infill.
    runoff = (z_top, u_offset, length_scale): the wall face gets TEXCOORD_1 = (u_offset + u, 1 + (z_top - z) /
    length_scale) for the parapet run-off streaks of halls (Kamion/World PBR _RUNOFF); otherwise no UV1."""
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
            uv1 = runoff_uv1(runoff, u0 + ua, u0 + ub, za, zb2)
            acc.quad(layer, mat, P(ua, za), P(ub, za), P(ub, zb2), P(ua, zb2),
                     uv=[[u0 + ua, za - vref], [u0 + ub, za - vref], [u0 + ub, zb2 - vref], [u0 + ua, zb2 - vref]], uv1=uv1)
    n3 = np.append(nout[:2], 0.0)
    d3 = np.append(d[:2], 0.0)
    for (ua, ub, va, vb, depth, kind, mat_in) in [o[:7] for o in ops]:
        back = -n3 * depth
        A, B, C, D = (np.array(P(ua, va)), np.array(P(ub, va)), np.array(P(ub, vb)), np.array(P(ua, vb)))
        rv = reveal or "reveal_" + ("hall" if mat.startswith("hall") else "plaster")
        # reveals (facing into the opening)
        acc.quad(layer, rv, A, B, B + back, A + back)          # sill (faces up)
        acc.quad(layer, rv, D + back, C + back, C, D)          # head (faces down)
        acc.quad(layer, rv, A + back, D + back, D, A)          # left jamb (faces +d)
        acc.quad(layer, rv, B, C, C + back, B + back)          # right jamb (faces -d)
        w, h = ub - ua, vb - va
        atlas = isinstance(mat_in, tuple)
        if atlas:                    # the cell carries frame, sashes, glass and what is behind it: no frame geometry
            _, rects, fa, fb, ga, gb = mat_in
            nr = len(rects)
            for j, (cu, cv, cw, ch) in enumerate(rects):
                a0, a1 = max(fa, j / nr), min(fb, (j + 1) / nr)
                if a1 - a0 < 1e-6:
                    continue
                t0, t1 = (a0 - fa) / (fb - fa), (a1 - fa) / (fb - fa)
                Pa, Pb = A + back + (B - A) * t0, A + back + (B - A) * t1
                lu0, lu1 = cu + cw * (a0 * nr - j), cu + cw * (a1 * nr - j)
                lv0, lv1 = cv + ch * ga, cv + ch * gb
                acc.quad(layer, "facade_atlas", Pa, Pb, Pb + (D - A), Pa + (D - A),
                         uv=[[lu0, lv0], [lu1, lv0], [lu1, lv1], [lu0, lv1]])
        else:
            acc.quad(layer, mat_in, A + back, B + back, C + back, D + back, uv=[[0, 0], [w, 0], [w, h], [0, h]])
        if atlas:
            pass
        elif kind in ("window", "balcony", "ribbon"):         # frame around the glass (PVC/alu profile, 7 cm face)
            fw = min(0.07, w / 5, h / 5)
            fr = back + n3 * 0.035
            Ao, Bo, Co, Do = A + fr, B + fr, C + fr, D + fr
            Ai, Bi = Ao + d3 * fw + [0, 0, fw], Bo - d3 * fw + [0, 0, fw]
            Ci, Di = Co - d3 * fw - [0, 0, fw], Do + d3 * fw - [0, 0, fw]
            fm = "hall_flashing" if mat.startswith("hall") else "window_frame"
            acc.quad(layer, fm, Ao, Bo, Bi, Ai)
            acc.quad(layer, fm, Bo, Co, Ci, Bi)
            acc.quad(layer, fm, Co, Do, Di, Ci)
            acc.quad(layer, fm, Do, Ao, Ai, Di)
        if not atlas and kind in ("window", "balcony") and w > 1.25:      # mullion
            um = 0.5 * (ua + ub)
            c = np.array(P(um, 0.5 * (va + vb))) + back + n3 * 0.04
            acc.box(layer, "window_frame", c, d3 * 0.035, n3 * 0.035, [0, 0, h / 2])
        if not atlas and kind == "ribbon":                   # ribbon window: mullions every ~1.35 m + transom
            k = max(1, int(round(w / 1.35)))
            for i in range(1, k):
                c = np.array(P(ua + w * i / k, 0.5 * (va + vb))) + back + n3 * 0.04
                acc.box(layer, "window_frame", c, d3 * 0.03, n3 * 0.035, [0, 0, h / 2])
            c = np.array(P(0.5 * (ua + ub), va + h * 0.72)) + back + n3 * 0.04
            acc.box(layer, "window_frame", c, d3 * (w / 2), n3 * 0.03, [0, 0, 0.025])
        if kind in ("window", "ribbon"):                     # transom + sill flashing
            c = np.array(P(0.5 * (ua + ub), va)) + n3 * 0.03
            acc.box(layer, "hall_flashing" if mat.startswith("hall") else "window_sill", c, d3 * (w / 2 + 0.04),
                    n3 * 0.05, [0, 0, 0.02], skip=(2,))           # the wall-side face is never seen


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
def facade_openings(typ, L, zref, ztop, storeys, key, is_main, docks_here, variant=None, sh=None, zbase=0.3):
    """Openings for one wall edge (u along the edge from its start), in absolute z:
    (ua, ub, va, vb, depth, kind, infill[, meta]). infill: a material name or atlas cells (cells()).
    variant: ribbon (office: ribbon windows on the upper storeys), balcony (block: balcony doors every second
    bay from the 1st floor), drive_door (hall: one 4.0 x 4.5 m sectional door on the main facade), main.
    Blocks and offices read the storey rows of the facade_far set (FA.far_plan), so LOD0 and LOD1 show the same
    windows; sill and window height scale with the storey height (k = sh / FA.FAR_ROW_H) on both."""
    variant = variant or {}
    ops = []
    hv = lambda *k: FA.hint(key, *k)
    if typ == "hall":
        if docks_here:
            return ops
        if is_main and L > 6:
            n = max(1, int(L // 40))
            for i in range(n):
                um = (i + 0.5) * L / n + (2.5 if i % 2 else -2.5)
                ops.append((um - 0.5, um + 0.5, zref + 0.15, zref + 2.25, 0.08, "door", cells("door_steel", hv("pd", i))))
        if L > 18 and hfloat(key, "win") < 0.55:
            zw = min(zref + 3.2, ztop - 1.6)
            pitch = 6.0
            n = int((L - 6) // pitch)
            wv = hv("hw")                       # one window type per wall
            for i in range(n):
                um = (L - (n - 1) * pitch) / 2 + i * pitch
                if any(abs(um - (o[0] + o[1]) / 2) < 1.6 for o in ops):
                    continue
                ops.append((um - 1.0, um + 1.0, zw, zw + 1.0, 0.12, "window", cells("hallw", wv)))
        if variant.get("drive_door") and variant.get("main") and L > 25 and ztop - zref > 5.5:
            um = L - 7.0
            ops = [o for o in ops if o[1] < um - 2.6 or o[0] > um + 2.6]
            ops.append((um - 2.0, um + 2.0, zref + 0.02, zref + 4.5, 0.2, "door", "garage_door"))
        return ops
    if typ == "shed":
        if is_main and L > 3.2 and hfloat(key, "gar") < 0.6:
            n = max(1, min(4, int(L // 3.2)))
            for i in range(n):
                um = (i + 0.5) * L / n
                ops.append((um - 1.25, um + 1.25, zref + 0.05, zref + 2.2, 0.1, "door", cells("garage", hv("g", i))))
        elif is_main and L > 2:
            ops.append((L / 2 - 0.5, L / 2 + 0.5, zref + 0.05, zref + 2.15, 0.06, "door", cells("door_steel", hv("sd"))))
        return ops
    sh = sh or {"office": 3.5, "block": 2.8, "house": 2.9}[typ]
    pitch = {"office": 3.0, "block": 3.0, "house": 3.6}[typ]
    n = int((L - 1.0) // pitch)
    if typ == "house":
        n = min(n, 3)
    if n < 1:
        return ops
    um0 = (L - (n - 1) * pitch) / 2
    door_i = n // 2 if is_main else -1
    if typ == "house":
        for s in range(storeys):
            z0 = zref + zbase + s * sh
            if z0 + 0.9 + 1.4 > ztop - 0.3:
                break
            for i in range(n):
                um = um0 + i * pitch
                if s == 0 and i == door_i:
                    ops.append((um - 0.5, um + 0.5, zref + 0.15, zref + 2.4, 0.15, "door", cells("door_house", hv("hd"))))
                    continue
                ops.append((um - 0.6, um + 0.6, z0 + 0.9, z0 + 2.3, 0.14, "window", cells("house", hv("hw", s, i))))
        return ops
    k = sh / FA.FAR_ROW_H
    if typ == "block" and variant.get("basement") and zbase >= 0.8:   # basement windows in the high plinth
        for i in range(n):
            if i == door_i or hv("bs", i) % 3 == 0:
                continue
            um = um0 + i * pitch
            ops.append((um - 0.45, um + 0.45, zref + 0.25, zref + 0.70, 0.10, "window", cells("base", hv("b", i))))
    groups = FA.far_groups(typ, storeys, variant.get("balcony"), variant.get("ribbon"), key.rsplit(":", 1)[0])
    ns = FA.far_storeys(groups, sh, ztop - 0.3 - zref - zbase)
    plan = FA.far_plan(groups[:ns], key)
    for s in range(ns):
        z0 = zref + zbase + s * sh
        group, row, off = FA.far_storey(plan, s)
        if group == "ribbon":
            vs = [v for i in range(n) for v in (FA.far_entry(group, row, off, i)[1],) * 2]
            ops.append((um0 - 1.5, um0 + (n - 1) * pitch + 1.5, z0 + 0.9 * k, z0 + 2.5 * k, 0.12, "ribbon", cells("off", *vs)))
            continue
        for i in range(n):
            um = um0 + i * pitch
            if i == door_i:
                if s == 0:
                    ops.append((um - 0.8, um + 0.8, zref + 0.15, zref + 2.4, 0.15, "door",
                                cells("door_block", hv("db") if typ == "block" else 1 + hv("db") % 2)))
                    continue
                if typ == "block":                # stairwell axis above the entrance
                    ops.append((um - 0.6, um + 0.6, z0 + 0.9 * k, z0 + 2.1 * k, 0.14, "window", cells("stair", hv("st"))))
                    continue
            ck, cv = FA.far_entry(group, row, off, i)
            if ck == "bal":                       # balcony door + window; the balcony itself: build() (meta)
                ops.append((um - 1.05, um - 0.15, z0 + 0.05, z0 + 0.05 + 2.2 * k, 0.14, "bdoor", cells("bdoor", cv), cv))
                ops.append((um - 0.15, um + 0.95, z0 + 0.05 + 0.85 * k, z0 + 0.05 + 2.2 * k, 0.14, "window", cells("bwin", cv)))
                continue
            w = FA.KINDS[ck][0]
            ops.append((um - w / 2, um + w / 2, z0 + 0.9 * k, z0 + (0.9 + FA.KINDS[ck][1]) * k, 0.14, "window", cells(ck, cv)))
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
    # dock floodlight on a short wall arm above the shelter, left of centre (LED head tilted to the apron)
    zl = zf + sh + 0.75
    acc.box(layer, "steel_galv", P(-0.9, zl, 0.25), np.append(d * 0.025, 0), np.append(nout * 0.25, 0), [0, 0, 0.025])
    acc.box(layer, "luminaire_housing", P(-0.9, zl - 0.06, 0.55), np.append(d * 0.16, 0), np.append(nout * 0.1, 0),
            [0, 0, 0.05])
    acc.quad(layer, "lamp_glass", P(-1.04, zl - 0.115, 0.47), P(-0.76, zl - 0.115, 0.47), P(-0.76, zl - 0.115, 0.63),
             P(-1.04, zl - 0.115, 0.63))


def build_dock_lod1(acc, p, d, nout, u, zy, num, layer="buildings_low"):
    """LOD1 counterpart of build_dock (Low / Medium away from the route, High beyond the LOD switch): the same
    silhouette - black shelter frame (two curtains + header) with the yellow guide stripes, leveller block,
    wheel guides on the apron - as boxes without their wall-side / bottom faces, in materials LOD1 draws anyway
    (FK.L1_MAT: one draw per material per chunk). Hazard stripes, number plate, bumpers, signal light and floodlight
    are LOD0 detail. review r6 / HANDOVER pkt 7 (Low and High show the same docks)."""
    zf = zy + S.DOCK_FLOOR_H
    c = p + d * u
    W = S.DOCK_DOOR_W

    def P(off_u, z, out=0.0):
        q = c + d * off_u + nout * out
        return np.array([q[0], q[1], z])
    sw, sh, sd = S.DOCK_SHELTER_W, S.DOCK_SHELTER_H, S.DOCK_SHELTER_D
    side = (sw - W) / 2 + 0.05
    shelter = FK.L1_MAT["dock_shelter"]
    for sgn in (-1, 1):
        cc = P(sgn * (W / 2 + side / 2), zf + sh / 2 - 0.1, sd / 2)
        acc.box(layer, shelter, cc, np.append(d * side / 2, 0), np.append(nout * sd / 2, 0),
                [0, 0, sh / 2 - 0.1], skip=(0, 2))
        x = sgn * (W / 2 + side / 2)
        acc.quad(layer, "paint_yellow", P(x - 0.05, zf + 0.1, sd + 0.005), P(x + 0.05, zf + 0.1, sd + 0.005),
                 P(x + 0.05, zf + sh - 0.5, sd + 0.005), P(x - 0.05, zf + sh - 0.5, sd + 0.005))
    acc.box(layer, shelter, P(0, zf + sh - 0.35, sd / 2), np.append(d * (sw / 2 + 0.05), 0),
            np.append(nout * sd / 2, 0), [0, 0, 0.35], skip=(2,))
    # leveller block (lip + front in one box: top, front, ends)
    steel = FK.L1_MAT["steel_checker"]
    acc.box(layer, steel, P(0, zf - 0.17, 0.2), np.append(d * 1.0, 0), np.append(nout * 0.2, 0),
            [0, 0, 0.17], skip=(0, 2))
    for sgn in (-1, 1):            # wheel guides on the apron: top, both sides, the far end
        acc.box(layer, "paint_yellow", P(sgn * 1.35, zy + 0.12, 2.6), np.append(d * 0.06, 0), np.append(nout * 2.2, 0),
                [0, 0, 0.12], skip=(0, 2))


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


def lod1_wall(acc, typ, wall, a, c_, nout, L, zbot, zref, zt, u_acc, storeys, sh, zbase, kind, pitched, zone_wall=None,
              runoff=None, pieces=None, fkey="", balcony=False):
    """LOD1 wall edge: cheap (8-14 triangles) but not a box face - plinth, window zone (office / block: far facade
    material, UV1 = (bay, storey) grid), wall above, projecting coping at the attic. runoff: as wall_with_openings
    (hall_wall_* bands get the same wall-top TEXCOORD_1 as LOD0, so the streaks do not pop at the LOD switch).
    pieces(layer): draws the wall zbot..zt itself (halls: the LOD0 plinth / colour bands / dock openings, see build());
    lod1_wall then only adds the coping ledge."""
    lay = "buildings_low"

    def P(q, z):
        return [float(q[0]), float(q[1]), float(z)]

    def band(z0, z1, mat, uv1=None):
        if z1 - z0 < 0.02:
            return
        if uv1 is None and str(mat).startswith("hall_wall"):
            uv1 = runoff_uv1(runoff, u_acc, u_acc + L, z0, z1)
        acc.quad(lay, mat, P(a, z0), P(c_, z0), P(c_, z1), P(a, z1),
                 uv=[[u_acc, z0 - zref], [u_acc + L, z0 - zref], [u_acc + L, z1 - zref], [u_acc, z1 - zref]], uv1=uv1)
    if pitched or typ not in ("hall", "office", "block") or L < 3.0:     # short jogs (half of all edges): plain
        band(zbot, zt, wall)
        return
    zpl = zref + (0.6 if typ == "hall" else zbase - 0.1)
    if pieces is not None:
        pieces(lay)
        z = zt
    else:
        band(zbot, zpl, "hall_plinth" if typ == "hall" else "plinth_dark")
        z = zpl
    if typ in ("office", "block") and L > 2.5:
        # ADR 0081: the window zone is drawn from the storey rows of the facade_far set - one quad per chunk of
        # storeys that are consecutive rows (FA.far_plan, the plan LOD0 reads its cells from) and per 8 bays (one
        # atlas period: half-float UV), UV0 in row atlas metres; the wall left and right of the bays takes the plain
        # strip of the same material (same tone as the zone)
        n = int((L - 1.0) // FA.FAR_PITCH)
        zw0 = zref + zbase
        groups = FA.far_groups(typ, storeys, balcony, kind == "ribbon", fkey.rsplit(":", 1)[0])
        ns = FA.far_storeys(groups, sh, zt - 0.3 - zw0)
        if n >= 1 and ns >= 1:
            far = f"{zone_wall or wall}__far_{kind}"
            ua = (L - n * FA.FAR_PITCH) / 2
            ub = ua + n * FA.FAR_PITCH
            zw1 = min(zw0 + ns * sh, zt - 0.3)
            d_ = (c_ - a) / L
            pv0, pv1 = FA.FAR_PLAIN_V

            def fq(u0, u1, z0, z1, uv):
                acc.quad(lay, far, P(a + d_ * u0, z0), P(a + d_ * u1, z0), P(a + d_ * u1, z1), P(a + d_ * u0, z1), uv=uv)
            plain = [[0.2, pv0], [1.2, pv0], [1.2, pv1], [0.2, pv1]]
            kk = sh / FA.FAR_ROW_H
            plan = FA.far_plan(groups[:ns], fkey)
            # the wall above the last storey (attic band) rides on the last chunk when the atlas is plain above its row
            fold = FA.far_plain_above(plan[-1][2], plan[-1][3] + plan[-1][1] - 1) and zt - zw1 < 0.85 * kk
            ztop = zt if fold else zw1
            fq(0.0, ua, z, ztop, plain)
            fq(ub, L, z, ztop, plain)
            for s0, cnt, g, r0, off in plan:
                z0 = z if s0 == 0 else zw0 + s0 * sh
                z1 = ztop if s0 + cnt == ns else zw0 + (s0 + cnt) * sh
                vr = FA.far_row_v(g, r0)
                v0, v1 = vr + (z0 - zw0 - s0 * sh) / kk, vr + (z1 - zw0 - s0 * sh) / kk
                # one quad for all bays: the atlas repeats every 8 bays; half-float u only rounds the two ends
                x0 = off * FA.FAR_PITCH
                fq(ua, ub, z0, z1, [[x0, v0], [x0 + ub - ua, v0], [x0 + ub - ua, v1], [x0, v1]])
            z = ztop
    if z < zt:
        band(z, zt, wall)
    # coping ledge over the top 0.25 m: one face leaning 0.12 m out at its foot (drip edge) and meeting the wall line
    # 5 cm above the roof, so it closes against the roof polygon without a top face (r10: -2 triangles per edge, pays
    # for the storey-row quads of ADR 0081)
    o = nout * 0.12
    za, zb_ = zt - 0.25, zt + 0.05
    acc.quad(lay, "hall_flashing", P(a + o, za), P(c_ + o, za), P(c_, zb_), P(a, zb_))


def build(buf, blds, hf, zsample, yard_union, roads_poly, report, sign_out=None):
    """Generate building meshes into buf; returns dock descriptions (for the paved aprons)."""
    all_docks = []
    counts = {}
    Acc.runoff_tris = {"with_uv1": 0, "without_uv1": 0}
    signs = []
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
        if typ == "roof":            # canopy on columns (fuel station, market / parking roof)
            # Both layers (W-H4): the LOD1 tier draws the same deck, fascia and columns, so
            # a tier switch never removes a roof structure from the street.
            zc = zref + min(max(h, 4.8), 6.0)
            cc = np.asarray(poly.minimum_rotated_rectangle.exterior.coords)[:4]
            cen = np.asarray(poly.centroid.coords[0])
            for layer in ("buildings", "buildings_low"):
                roof_flat(acc, layer, poly, zc + 0.6, mat="hall_flashing", attic=0.0)
                for a, c_ in ring_edges(poly.exterior):      # 0.6 m fascia band all round (was a 1 cm box)
                    acc.quad(layer, "canopy_fascia", [a[0], a[1], zc], [c_[0], c_[1], zc], [c_[0], c_[1], zc + 0.6],
                             [a[0], a[1], zc + 0.6])
                for q in cc:
                    v = cen + (q - cen) * 0.7
                    acc.box(layer, "steel_painted", [v[0], v[1], (zref + zc) / 2], [0.15, 0, 0], [0, 0.15, 0],
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
        storeys, sh, zbase = storey_plan(typ, h, p)
        pitched = typ == "house" and (p.get("roof_type_lod2") in (None, "1030", "1040", "1130", "1050"))
        rect = poly.minimum_rotated_rectangle
        rc_ = np.asarray(rect.exterior.coords)[:4]
        re_ = [float(np.linalg.norm(rc_[(i + 1) % 4] - rc_[i])) for i in range(4)]
        rk_ = 0 if re_[0] >= re_[1] else 1
        rect_along = (rc_[(rk_ + 1) % 4] - rc_[rk_]) / max(re_[rk_], 1e-6)
        rect_short = min(re_[0], re_[1])
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
        lens = [float(np.linalg.norm(c_ - a)) for a, c_ in edges]
        # block: balconies on the long side(s) away from the main (entrance) facade
        bal_edges = set()
        if typ == "block" and storeys >= 3 and lens:
            far = sorted(range(len(edges)), key=lambda i: -dist[i])
            for i in far[:2]:
                if lens[i] > 12 and i != main:
                    bal_edges.add(i)
        variant = {"ribbon": typ == "office" and FK.hfloat(key, "ribbon") < 0.5,
                   "drive_door": typ == "hall" and FK.hfloat(key, "drive") < 0.5, "basement": typ == "block"}
        scheme = FK.hall_scheme(key, wall) if typ == "hall" else None
        insulated = typ == "block" and FK.hfloat(key, "etics") < 0.7
        # v3.1 horizontal bands: insulated blocks (35 %) get the window rows in the accent colour from the 1st
        # floor up; punched-window offices with >= 2 storeys (40 %) get darker spandrel bands between the rows
        # ribbon-window offices of >= 3 storeys (60 %): dark spandrel panels between the ribbons (1970s office
        # towers of the Białystok plants)
        bands = ((insulated and storeys >= 3 and FK.hfloat(key, "bands") < 0.35) or
                 (typ == "office" and not variant["ribbon"] and storeys >= 2 and FK.hfloat(key, "spandrel") < 0.4) or
                 (typ == "office" and variant["ribbon"] and storeys >= 3 and FK.hfloat(key, "spandrel") < 0.6))
        if typ == "block" and not insulated:
            wall = "panel_concrete"
        accent = FK.hpick(FK.ACCENT_PLASTER, key, "accent")
        wooden = typ == "house" and storeys == 1 and poly.area < 120 and FK.hfloat(key, "wood") < 0.12
        if wooden:
            wall = "wood_planks" if FK.hfloat(key, "woodc") < 0.6 else "wood_planks_green"
        u_acc = 0.0
        dock_edges = {tuple(np.round(dk["edge"][0], 2)): dk for dk in docks}
        nouts = []
        signed = laddered = False
        for ei, (a, c_) in enumerate(edges):
            L = float(np.linalg.norm(c_ - a))
            if L < 0.05:
                nouts.append(np.array([0.0, 0.0]))
                continue
            d = (c_ - a) / L
            nout = np.array([d[1], -d[0]])
            nouts.append(nout)
            lod1_main, lod1_zone = wall, None        # LOD1 colours follow what dominates the LOD0 wall (W-H4)
            lod1_pieces = None
            dk = dock_edges.get(tuple(np.round(a, 2)))
            zt = zeave
            is_main = ei == main or (typ == "hall" and L > 30)
            ops = facade_openings(typ, L, zref, zt, storeys, f"{key}:{ei}", is_main, dk is not None,
                                  dict(variant, balcony=ei in bal_edges, main=ei == main), sh=sh, zbase=zbase)
            if dk:
                zf = dk["yard_z"] + S.DOCK_FLOOR_H
                for dock in dk["docks"]:
                    ops.append((dock["u"] - S.DOCK_DOOR_W / 2, dock["u"] + S.DOCK_DOOR_W / 2, zf, zf + S.DOCK_DOOR_H,
                                0.25, "dock", "dock_door"))
            if typ == "hall":
                # plinth (concrete, up to dock floor) + cladding scheme + coping on top
                zpl = (dk["yard_z"] + S.DOCK_FLOOR_H) if dk else zref + 0.6
                zlow = FK.safe_z(zref + scheme["low"][1], ops, zpl, zt - 0.4, 0.45) if scheme["low"] else None
                ztopb = FK.safe_z(zt - 0.4 - scheme["top"][1], ops, zpl, zt - 0.4) if scheme["top"] else None

                def hall_mat(u0, u1, z0, z1, zpl=zpl, zlow=zlow, ztopb=ztopb):
                    if z1 <= zpl + 1e-6:
                        return "hall_plinth"
                    if zlow is not None and z1 <= zlow + 1e-6:
                        return scheme["low"][0]
                    if ztopb is not None and z0 >= ztopb - 1e-6:
                        return scheme["top"][0]
                    return wall
                # parapet run-off streaks (zacieki pod attyką): wall-top space in UV1, per-building pattern offset
                # (one constant shift per building, so u stays continuous round the corners) and streak length
                # scale (gutter halls shorter: the gutter takes most of the water)
                ro = (zt - 0.4, RUNOFF_PERIOD_M * FK.hfloat(key, "runoff_u"),
                      (0.55 if scheme["gutter"] else 0.8) + 0.7 * FK.hfloat(key, "runoff_l"))
                lod1_ro = (zt - 0.25, ro[1], ro[2])                  # LOD1: coping ledge over the top 0.25 m
                FK.wall_pieces(wall_with_openings, acc, a, d, nout, L, zbot, zt - 0.4, ops, u_acc, zref,
                               [zpl, zlow, ztopb], [], hall_mat, runoff=ro)

                # LOD1 hall wall (HANDOVER pkt 7): the same plinth height, colour bands and dock doors as LOD0
                # (dock doors as recessed openings, ~10 triangles each; windows / personnel doors stay LOD0
                # detail), so Low and High show the same hall. Before: one ivory band, the red top band of this
                # hall and every dock existed on High only.
                def lod1_pieces(lay, a=a, d=d, nout=nout, L=L, zt=zt, hall_mat=hall_mat, zs=[zpl, zlow, ztopb],
                                dock_ops=[o for o in ops if o[5] == "dock"], ro=lod1_ro):
                    FK.wall_pieces(wall_with_openings, acc, a, d, nout, L, zbot, zt, dock_ops, u_acc, zref, zs, [],
                                   hall_mat, layer=lay, runoff=ro, reveal=FK.L1_MAT["reveal_hall"])
                P3 = lambda q, z: [q[0], q[1], z]
                acc.quad("buildings", "hall_flashing", P3(a + nout * 0.03, zt - 0.4), P3(c_ + nout * 0.03, zt - 0.4),
                         P3(c_ + nout * 0.03, zt), P3(a + nout * 0.03, zt))
                if scheme["gutter"] and L > 20:
                    FK.gutter(acc, a, c_, nout, zt - 0.02)
                    for u in FK.downpipe_positions(L, ops, f"{key}:{ei}", 18.0):
                        FK.downpipe(acc, a, d, nout, u, zbot + 0.4, zt - 0.12, hopper=False)
                else:
                    FK.coping(acc, a, c_, nout, zt)
                    for u in FK.downpipe_positions(L, ops, f"{key}:{ei}", 22.0):
                        FK.downpipe(acc, a, d, nout, u, zbot + 0.4, zt - 0.75, hopper=True)
                # ADR 0081 hall kit: wall louvres (half of the dockless walls), one caged roof ladder per bigger hall
                if not dk and L > 14 and zt - zref > 5.0 and FK.hfloat(key, ei, "louvre") < 0.5:
                    for j in range(1 + int(L > 40)):
                        u = FK.safe_u(2.6 if j == 0 else L - 2.6, [(o[0] - 0.7, o[1] + 0.7, *o[2:]) for o in ops], L)
                        if u is not None:
                            FK.wall_louvre(acc, a, d, nout, u, min(zref + 3.4, zt - 1.6), 1.0, FA.hint(key, ei, "lv"))
                if not dk and not laddered and ei != main and L > 10 and zt - zref > 6.0 and poly.area > 600:
                    u = FK.safe_u(L - 1.6, [(o[0] - 0.8, o[1] + 0.8, *o[2:]) for o in ops], L)
                    if u is not None and u > L / 2:
                        FK.cage_ladder(acc, a, d, nout, u, zref + 0.25, zt)
                        laddered = True
                for o in ops:                                         # canopies over personnel doors
                    if o[5] == "door" and o[6] != "garage_door":
                        FK.canopy(acc, a, d, nout, (o[0] + o[1]) / 2, o[1] - o[0] + 0.8, o[3] + 0.35, 0.9)
                if dk:
                    for dock in dk["docks"]:
                        build_dock(acc, "buildings", a, d, nout, dock["u"], dk["yard_z"], dock["num"])
                        build_dock_lod1(acc, a, d, nout, dock["u"], dk["yard_z"], dock["num"])
                    # canopy over the dock row (steel, typical) only for hero buildings
                    if hero:
                        u0d, u1d = dk["docks"][0]["u"] - 2.2, dk["docks"][-1]["u"] + 2.2
                        cz = zf + S.DOCK_SHELTER_H + 0.9
                        cm = a + d * (0.5 * (u0d + u1d)) + nout * 1.0
                        for lay_, sk_ in (("buildings", ()), ("buildings_low", (2,))):
                            acc.box(lay_, "steel_painted", [cm[0], cm[1], cz], np.append(d * (u1d - u0d) / 2, 0),
                                    np.append(nout * 1.0, 0), [0, 0, 0.08], skip=sk_)
                        signs.append(FK.sign_instance("dostawy", a, d, nout, u0d - 3.0 if u0d > 6 else u1d + 3.0,
                                                      cz + 1.2, f"{key}:{ei}"))
                if is_main and not signed and L > 25 and (hero or FK.hfloat(key, "sign") < 0.6):
                    code = "hala_a" if hero else FK.hpick(["hala_b", "hala_c", "hala_d", "magazyn"], key, "code")
                    u = FK.safe_u(L * (0.18 if FK.hfloat(key, "su") < 0.5 else 0.82), ops, L)
                    if u is not None and zt - zref > 6.5:
                        signs.append(FK.sign_instance(code, a, d, nout, u, zt - 1.6, f"{key}:{ei}"))
                        signed = True
            else:
                zpl = zref + (zbase - 0.1 if typ in ZBASE else 0.35)
                usplits = []
                if insulated and ei == main and L > 12:              # accent field on the stairwell axis
                    door = [o for o in ops if o[5] == "door"]
                    if door:
                        um = (door[0][0] + door[0][1]) / 2
                        usplits = [FK.safe_u(um - 1.6, ops, L), FK.safe_u(um + 1.6, ops, L)]
                lod1_ro = ((zt, RUNOFF_PERIOD_M * FK.hfloat(key, "runoff_u"), 0.6 + 0.7 * FK.hfloat(key, "runoff_l"))
                           if str(wall).startswith("hall_wall") else None)
                # r10 r2: flat-roofed blocks and offices streak under the attic coping too (LOD0 only: the LOD1 window
                # zone is the row atlas, it has no wall-top UV1)
                lod0_ro = lod1_ro
                if lod0_ro is None and typ in ("block", "office") and not pitched:
                    lod0_ro = (zt, RUNOFF_PERIOD_M * FK.hfloat(key, "runoff_u"), 0.5 + 0.6 * FK.hfloat(key, "runoff_l"))
                # accent colour on the gable ends only: an edge across the long axis, about as long as the block is
                # deep (before r10 every edge < 16 m qualified, so stepped blocks came out accent-coloured all round)
                gable_accent = (insulated and L < 16 and FK.hfloat(key, "gable") < 0.6 and L > 0.7 * rect_short and
                                abs(float(d @ rect_along)) < 0.3)
                band_z = []                                            # (z0, z1) of each band
                if bands and ei not in bal_edges and not gable_accent and typ in ("block", "office"):
                    kk_ = sh / FA.FAR_ROW_H                               # sill 0.9 k, head 2.35 k / 2.5 k (facade_openings)
                    ns_ = FA.far_storeys(FA.far_groups(typ, storeys, False, variant["ribbon"], key), sh, zt - 0.3 - zref - zbase)
                    for st_ in range(ns_):
                        z0_ = zref + zbase + st_ * sh
                        if typ == "block" and st_ >= 1:
                            band_z.append((z0_ + 0.9 * kk_ - 0.12, min(z0_ + 2.35 * kk_ + 0.12, zt - 0.2)))
                        if typ == "office" and st_ + 1 < ns_:
                            band_z.append((z0_ + 2.5 * kk_ + 0.08, z0_ + sh + 0.9 * kk_ - 0.08))
                band_mat = accent if typ == "block" else "plaster_band_grey"
                if gable_accent:
                    lod1_main = accent
                elif band_z and typ == "block":
                    lod1_zone = band_mat                 # accent window rows -> accent window zone on LOD1

                def plaster_mat(u0, u1, z0, z1, usplits=usplits, gable_accent=gable_accent, zpl=zpl, band_z=band_z):
                    if z1 <= zpl + 1e-6:
                        return "plinth_dark"
                    if gable_accent:
                        return accent
                    if len(usplits) == 2 and None not in usplits and usplits[0] - 1e-6 <= u0 and u1 <= usplits[1] + 1e-6:
                        return accent
                    zm = 0.5 * (z0 + z1)
                    if any(b0 <= zm <= b1 for b0, b1 in band_z):
                        return band_mat
                    return wall
                FK.wall_pieces(wall_with_openings, acc, a, d, nout, L, zbot, zt, ops, u_acc, zref,
                               [zpl] + [z for b in band_z for z in b],
                               [u for u in usplits if u is not None] if None not in usplits else [], plaster_mat,
                               runoff=lod0_ro)   # sheds / small halls clad in sheet; plaster of blocks / offices
                if typ in ("block", "office"):                       # attic coping (obróbka attyki): silhouette
                    FK.coping(acc, a, c_, nout, zt, mat="hall_flashing")
                if typ == "block":
                    if L > 8:                                        # downpipes at the wall ends
                        for u in (0.35, L - 0.35):
                            FK.downpipe(acc, a, d, nout, u, zbot + 0.4, zt - 0.4, hopper=True)
                    for o in ops:
                        okey = f"{key}:{ei}:{o[0]:.1f}:{o[2]:.1f}"
                        if o[5] == "bdoor":
                            FK.balcony(acc, a, d, nout, o[0] + 1.05, 2.4, o[2] - 0.03, variant=o[7], key=okey)
                        elif o[5] == "window" and o[1] - o[0] > 1.0 and o[2] > zref + zbase:
                            FK.window_kit(acc, a, d, nout, o, okey, 0.05)
                        elif o[5] == "door":
                            FK.canopy(acc, a, d, nout, (o[0] + o[1]) / 2, 2.6, o[3] + 0.3, 1.4, mat="balcony_slab")
                elif typ == "office":
                    for o in ops:
                        if o[5] == "window":
                            FK.window_kit(acc, a, d, nout, o, f"{key}:{ei}:{o[0]:.1f}:{o[2]:.1f}", 0.10)
                        if o[5] == "door":
                            FK.canopy(acc, a, d, nout, (o[0] + o[1]) / 2, 3.2, o[3] + 0.45, 1.6, posts=False)
                            if not signed and zt - zref > 4.0:
                                code = FK.hpick(["biuro", "recepcja", "serwis", "biuro"], key, "osign")
                                signs.append(FK.sign_instance(code, a, d, nout, (o[0] + o[1]) / 2, o[3] + 1.05,
                                                              f"{key}:{ei}"))
                                signed = True
                    if L > 8:
                        for u in (0.35, L - 0.35):
                            FK.downpipe(acc, a, d, nout, u, zbot + 0.4, zt - 0.4, hopper=True)
                elif typ == "house":
                    for o in ops:
                        if o[5] == "door":
                            FK.canopy(acc, a, d, nout, (o[0] + o[1]) / 2, 1.6, o[3] + 0.25, 0.9,
                                      mat="roof_metal_graphite" if not wooden else "wood_planks")
            # collision: plain wall
            acc.quad("collision", "collision_building", [a[0], a[1], zbot], [c_[0], c_[1], zbot], [c_[0], c_[1], zt],
                     [a[0], a[1], zt])
            # LOD1 (v3.1): plinth band, window zone with the far facade material (window grid in UV1), wall above,
            # projecting coping at the attic; pitched houses keep the plain wall
            lod1_wall(acc, typ, lod1_main, a, c_, nout, L, zbot, zref, zt, u_acc, storeys, sh, zbase,
                      "ribbon" if variant["ribbon"] else typ, pitched, zone_wall=lod1_zone, runoff=lod1_ro,
                      pieces=lod1_pieces, fkey=f"{key}:{ei}", balcony=ei in bal_edges)
            u_acc += L
        if typ == "hall" and len(edges) >= 3:                       # corner flashings
            for i, (a, c_) in enumerate(edges):
                FK.corner_trim(acc, a, nouts[i - 1], nouts[i], zref + 0.6, zeave - 0.4)
        # courtyard walls (holes), plain
        hole_ro = ((zeave, RUNOFF_PERIOD_M * FK.hfloat(key, "runoff_u"), 0.6 + 0.7 * FK.hfloat(key, "runoff_l"))
                   if str(wall).startswith("hall_wall") else None)   # courtyard sheet walls streak as well
        for hole in poly.interiors if not pitched else []:
            uh = 0.0
            for a, c_ in ring_edges(hole):
                L = float(np.linalg.norm(c_ - a))
                acc.quad("buildings", wall, [a[0], a[1], zbot], [c_[0], c_[1], zbot], [c_[0], c_[1], zeave], [a[0], a[1], zeave],
                         uv1=runoff_uv1(hole_ro, uh, uh + L, zbot, zeave))
                uh += L
        if pitched:
            roof = hpick(key, ROOFS_PITCHED, "roof")
            for layer in ("buildings", "buildings_low"):
                gable(acc, layer, work, zeave, ztop, wall, roof)
            gable(acc, "collision", work, zeave, ztop, "collision_building", "collision_building")
            # eaves gutters (long sides) + downpipes at two corners, chimney
            cw = np.asarray(work.exterior.coords)[:4]
            ew = [np.linalg.norm(cw[(i + 1) % 4] - cw[i]) for i in range(4)]
            kk = 0 if ew[0] >= ew[1] else 1
            for i in (kk, kk + 2):
                a, c_ = cw[i % 4], cw[(i + 1) % 4]
                dd_ = (c_ - a) / max(np.linalg.norm(c_ - a), 1e-6)
                nn_ = np.array([dd_[1], -dd_[0]])
                FK.gutter(acc, a, c_, nn_, zeave - 0.25, proud=0.38)
                FK.downpipe(acc, a, dd_, nn_ * 1.0, 0.25 if i == kk else float(np.linalg.norm(c_ - a)) - 0.25,
                            zbot + 0.4, zeave - 0.35, hopper=False)
            if not wooden or FK.hfloat(key, "wchim") < 0.8:
                FK.chimney(acc, work, ztop, key)
        else:
            roof_flat(acc, "buildings", poly, zeave, attic=0.3 if typ in ("hall", "office", "block") else 0.15,
                      skylights=typ == "hall", key=key)
            # LOD1 roof stays one flat polygon (an attic inset is invisible from the road and cost 1.3 MiB in Low);
            # the coping ledge (5 cm above the roof) reads as the attic rim
            roof_flat(acc, "buildings_low", poly, zeave, attic=0.0)
            tall_office = typ == "office" and storeys >= 5          # lift / plant rooms break the box top
            if typ == "block" or tall_office:
                FK.machine_rooms(acc, poly, zeave, "buildings_low")
            roof_flat(acc, "collision", poly, zeave, mat="collision_building", attic=0.0)
            if typ == "hall" and poly.area > 600:
                FK.roof_vents(acc, poly, zeave - 0.3, key, "hall")
            elif typ == "block":
                FK.roof_vents(acc, poly, zeave - 0.3, key, "block")
            elif tall_office:
                FK.machine_rooms(acc, poly, zeave - 0.3, "buildings")
        acc.flush(buf, key)
    report.update({"typologies": counts, "docks": sum(len(d["docks"]) for d in all_docks),
                   "dock_facades": [d["id"] for d in all_docks], "facade_signs": len(signs),
                   "hall_wall_runoff_tris": dict(Acc.runoff_tris)})
    if sign_out is not None:
        sign_out.extend(signs)
    return all_docks
