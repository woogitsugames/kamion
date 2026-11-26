"""Plac Czarnieckiego (market square) in Tykocin: monument and square furniture (ADR 0320 + dopisek tykocin-plaza-s24).

Use ``build(buf, region, origin, overrides, zsurf, report)`` after the paved area plan is known. Anchors are
region-local E / N of tile `tykocin` (origin EPSG:2180 751371, 600319), measured on the GUGiK orthophoto 2024
(0.25 m, +-0.5 m): the square after its renewal is a paved plaza with the monument, two lawns and NO trees
(the paving itself is `paved_area` overrides in Data/Regions/tykocin/overrides.yaml).

Monument of Stefan Czarniecki (sandstone, 1762): the stone parts - steps, block, waisted pedestal with cartouches, the
figure with the gilt mace - are the hero asset art-source/world/landmarks/tykocin_czarniecki (Blender generator
tools/blender/world/landmarks/make_czarniecki.py: voxel-fused sculpt, LOD0 / LOD1, weathering baked into COLOR_0).
This module places it and adds what is thin iron or stands beside it: the picket fence on the platform with its
blank notice boards, the four stone posts with the chain, the planters with begonias. References: Wikimedia Commons
"Tykocin pomnik Stefana Czarnieckiego 01 / 05 / 08" (CC BY-SA 4.0), "Tykocin, pomnik Stefana Czarnieckiego, 1762 01"
(CC BY-SA 3.0 pl), "Mglisty poranek na placu Czarnieckiego w Tykocinie z pomnikiem" (CC BY 4.0) - reference only,
manifest in Data/raw/refs/tykocin-rynek-commons. Sizes WORKING_VALUE; the facing (south) is ESTIMATED from the light
on the midday photos. A stylised sculpt, not a scan or a copy of the sculpture; inscriptions and heraldry omitted.

Furniture: ten dark elongated marks along the south edge of the plaza / east lawn on the orthophoto (identity
ESTIMATED). The Commons photos show dark benches with cast-iron ends standing in loose pairs and low planter boxes
along the plaza edges, so six marks are benches (three variants) and four are planters; every piece is turned and
shifted a little (seeded by its index - nobody lines street furniture up with a string) and carries its own wear in
COLOR_0 (bleached, re-stained and replaced boards). Lamp posts of the square are not resolvable on the orthophoto:
none placed here (UNVERIFIED, see ADR 0320).
"""
from __future__ import annotations

import hashlib
import json
import math
from functools import lru_cache
from pathlib import Path

import numpy as np

from . import buildings_mesh as BM
from . import monument_kit as MK
from . import knyszyn_park_props_0227 as KP

REGION = "tykocin"
ASSET_ID = "tykocin_rynek_0320"
HERO = "tykocin_czarniecki"
HERO_DIR = Path(__file__).resolve().parents[3] / "art-source" / "world" / "landmarks" / HERO
LAYERS = ("buildings", "buildings_low")
MONUMENT_EN = (438.0, -86.6)          # centre of the base, orthophoto 2024
MONUMENT_FORWARD = (0.0, -1.0)        # ESTIMATED: faces south (DW671)
BENCHES_EN = ((426.3, -100.1), (431.6, -99.25), (441.0, -98.4), (446.9, -97.4), (452.9, -96.75), (461.9, -95.9),
              (466.6, -95.25), (479.1, -93.4), (485.4, -93.0), (491.6, -91.9))
PLANTER_MARKS = (1, 4, 6, 8)          # ESTIMATED: which marks are planter boxes (Commons fog photo: boxes along the edges)
BENCH_ROW = (0.993, 0.118)            # direction of the row (south edge of the plaza), orthophoto
WELL_EN, WELL_HALF_M, WELL_YAW_DEG = (470.1, -81.0), 1.9, 35.0      # square stone-rimmed basin on the east lawn
BED_EN, BED_R_M = (489.4, -77.25), 4.2                              # octagonal bed on the east lawn
STRIP_EN = ((457.9, -73.6), (495.7, -65.1), (496.2, -67.6), (458.4, -76.1))   # long low frame, north of the east lawn
STONE, IRON, GILT = "plinth_grey", "fence_anthracite", "monument_gilt"
SAND = "monument_sandstone_aged"      # hero asset stone: COLOR_0 = weathering tint / 2 (facade_tint)
WOOD = "wood_planks_bench"            # dark stained slats / planter boards: COLOR_0 = wear tint / 2
FLOWERS = "planter_flowers"           # foliage set, COLOR_0 = blossom / leaf colour / 2
PLATE = "plaster_white"               # blank notice boards on the fence (lettering omitted)
PLATFORM_TOP, FENCE_HALF, FENCE_H = 0.42, 2.20, 1.25
# planters with red begonias round the monument: (right, forward) of the box centre in the monument frame, ESTIMATED
# from Commons 01 / 08 and the fog photo (boxes outside the chain, two per side)
MONUMENT_PLANTERS = ((-1.9, 3.75), (2.0, 3.7), (3.75, 1.55), (3.7, -1.7), (-3.7, 1.6), (-3.75, -1.5), (-1.6, -3.7), (1.75, -3.75))
BEGONIA = ((1.9, 0.10, 0.22), (2.0, 0.22, 0.30), (1.7, 0.08, 0.16))      # tint x the FLOWERS colour: reds
PETUNIA = ((0.85, 0.45, 1.9), (1.9, 1.5, 1.9), (1.2, 0.3, 1.6))          # purple, pale pink, magenta
LEAF = ((0.13, 0.95, 0.12), (0.10, 0.75, 0.09), (0.18, 1.15, 0.14))
BENCH_VARIANTS = ("arms", "plain", "backless")


def _p(xy, z):
    return [float(xy[0]), float(xy[1]), float(z)]


def _h(*key):
    """Deterministic 0..1 from a key (placement jitter and wear must not change between builds)."""
    return int(hashlib.sha256("|".join(str(k) for k in key).encode()).hexdigest()[:8], 16) / 0xFFFFFFFF


def _box(acc, layer, mat, xy, z0, z1, hx, hy, axis=(1., 0.), skip=(0,)):
    a = np.asarray(axis, float); a /= np.linalg.norm(a)
    n = np.array([-a[1], a[0]])
    acc.box(layer, mat, _p(xy, (z0 + z1) / 2), np.r_[a * hx, 0.], np.r_[n * hy, 0.], [0., 0., (z1 - z0) / 2], skip=skip)


def _obox(acc, layer, mat, c, ax, ay, az, col=None, uv0=(0.0, 0.0), skip=(), col_ends=None):
    """Oriented box (half-axis vectors) with per-face vertices, UV0 in metres (u along `ax`) and COLOR_0.

    col = tint / 2 (rgb; a = 1 is added); col_ends = tint of the two end faces (soaked end grain).
    skip: faces left out (0 -az, 1 +az, 2 -ay, 3 +ay, 4 -ax, 5 +ax)."""
    c, ax, ay, az = (np.asarray(x, float) for x in (c, ax, ay, az))
    lx, ly, lz = (float(np.linalg.norm(v)) for v in (ax, ay, az))
    sg = [(sx, sy, sz) for sz in (-1, 1) for sy in (-1, 1) for sx in (-1, 1)]
    faces = [(0, 2, 3, 1), (4, 5, 7, 6), (0, 1, 5, 4), (2, 6, 7, 3), (0, 4, 6, 2), (1, 3, 7, 5)]
    if np.dot(np.cross(ax, ay), az) < 0:
        faces = [f[::-1] for f in faces]
    V, UV, COL, T = [], [], [], []
    for k, f in enumerate(faces):
        if k in skip:
            continue
        b = len(V)
        for i in f:
            sx, sy, sz = sg[i]
            V.append(c + sx * ax + sy * ay + sz * az)
            UV.append((uv0[0] + sx * lx, uv0[1] + 0.5 * (sy * ly + sz * lz)))
            if col is not None:
                cc = np.asarray(col_ends if (col_ends is not None and k in (4, 5)) else col, float)
                COL.append([cc[0], cc[1], cc[2], 1.0])
        T += [[b, b + 1, b + 2], [b, b + 2, b + 3]]
    acc.add(layer, mat, np.array(V), T, np.array(UV), COL=(np.array(COL) if col is not None else None))


def _bar(acc, layer, mat, p0, p1, wdir, w, d, col=None):
    """Flat bar from p0 to p1: width w along `wdir`, depth d across both."""
    p0, p1, wdir = (np.asarray(x, float) for x in (p0, p1, wdir))
    ax = (p1 - p0) / 2
    wdir = wdir - ax * np.dot(wdir, ax) / np.dot(ax, ax)
    wdir = wdir / np.linalg.norm(wdir)
    dd = np.cross(ax, wdir)
    dd /= np.linalg.norm(dd)
    _obox(acc, layer, mat, (p0 + p1) / 2, ax, wdir * w / 2, dd * d / 2, col=col)


@lru_cache(maxsize=1)
def hero():
    """(LOD -> material -> arrays, meta) of the Blender asset; frame: x right, y forward, z up from the paving."""
    z = np.load(HERO_DIR / f"{HERO}.npz")
    out = {}
    for k in z.files:
        lod, mat, name = k.split("|")
        out.setdefault(lod, {}).setdefault(mat, {})[name] = z[k]
    return out, json.loads((HERO_DIR / f"{HERO}_meta.json").read_text(encoding="utf-8"))


def _monument(acc, layer, at, z):
    low = layer == "buildings_low"
    f, r, up = MK.frame(MONUMENT_FORWARD)
    at = np.asarray(at, float)
    o = np.array([at[0], at[1], z])
    parts, meta = hero()
    for mat, d in parts["lod1" if low else "lod0"].items():
        v = d["V"].astype(float)
        V = o + np.outer(v[:, 0], r) + np.outer(v[:, 1], f) + np.outer(v[:, 2], up)
        col = d["COL"].astype(float) / 255.0
        acc.add(layer, mat, V, d["T"].astype(np.int64), d["UV"].astype(float), COL=col if col[:, 3].max() > 0.5 else None)
    top = float(meta["height_m"])
    if low:
        return top
    ax = r[:2]
    # iron fence on the platform: corner posts with a spike, two rails, flat pickets with spear heads
    h0 = z + PLATFORM_TOP
    for sx in (-1., 1.):
        for sy in (-1., 1.):
            c = at + r[:2] * sx * FENCE_HALF + f[:2] * sy * FENCE_HALF
            _box(acc, layer, IRON, c, h0, h0 + FENCE_H + .12, .03, .03, ax)
            b = np.r_[c, h0 + FENCE_H + .12]
            q = [b + r * sa * .03 + f * sb * .03 for sa, sb in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
            acc.add(layer, IRON, np.array(q + [b + up * .10]), [[i, (i + 1) % 4, 4] for i in range(4)])
    for d, n in ((r, f), (f, -r), (-r, -f), (-f, r)):          # side direction d, outward normal n
        c = np.r_[at, 0.] + n * FENCE_HALF
        for hz in (h0 + .13, h0 + FENCE_H - .20):
            acc.box(layer, IRON, c + up * hz, d * FENCE_HALF, n * .012, up * .02)
        npk = int(round(2 * FENCE_HALF / .125))
        V, T = [], []
        for i in range(1, npk):
            p = c + d * (-FENCE_HALF + 2 * FENCE_HALF * i / npk)
            for face in (1., -1.):                             # both faces with their own vertices
                b = len(V)
                e = d * .013 * face
                zs, zt = h0 + .04, h0 + FENCE_H - .09
                V += [p - e + up * zs, p + e + up * zs, p + e + up * zt, p - e + up * zt,
                      p + e * 1.9 + up * (zt + .03), p - e * 1.9 + up * (zt + .03), p + up * (zt + .13)]
                T += [[b, b + 1, b + 2], [b, b + 2, b + 3], [b + 5, b + 4, b + 6], [b + 3, b + 2, b + 4], [b + 3, b + 4, b + 5]]
        if np.dot(np.cross(d, up), n) < 0:                     # keep the first face of every picket turned outwards
            T = [[t[0], t[2], t[1]] for t in T]
        acc.add(layer, IRON, np.array(V), T)
    # blank notice boards on the front of the fence (Commons 01: small plates and a framed double board)
    front = np.r_[at, 0.] + f * (FENCE_HALF + .03)
    for off, hw, hh, zc, framed in ((-1.35, .24, .17, .78, False), (-.72, .11, .15, .78, False), (.0, .46, .26, .72, True),
                                    (1.38, .25, .17, .80, False)):
        c = front + r * off + up * (h0 + zc)
        if framed:
            acc.box(layer, IRON, c, r * (hw + .04), f * .014, up * (hh + .04))
            for sg in (-1., 1.):
                acc.box(layer, PLATE, c + r * sg * hw * .5 + f * .016, r * (hw * .5 - .03), f * .004, up * (hh - .03))
        else:
            acc.box(layer, PLATE, c, r * hw, f * .006, up * hh)
    # four stone posts with the chain hanging between them
    posts = [at + r[:2] * sx * 3.1 + f[:2] * sy * 3.1 for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    for k, c in enumerate(posts):
        sh = 0.40 + 0.05 * _h("post", k)
        _obox(acc, layer, SAND, np.r_[c, z + .33], np.r_[ax * .14, 0.], np.r_[-ax[1] * .14, ax[0] * .14, 0.], [0., 0., .39],
              col=(sh, sh * .98, sh * .93), skip=(0,))
    for k in range(4):
        a, b = np.r_[posts[k], z + .58], np.r_[posts[(k + 1) % 4], z + .58]
        side = (b - a) / np.linalg.norm(b - a)
        nseg = 12
        sag = .26 + .05 * _h("chain", k)
        pts = [a + (b - a) * i / nseg - up * sag * (1 - (2 * i / nseg - 1) ** 2) for i in range(nseg + 1)]
        for i in range(nseg):                                  # links alternate flat / on edge
            _bar(acc, layer, IRON, pts[i], pts[i + 1], np.cross(side, up) if i % 2 else up, .055, .022)
    return top


def _well(acc, layer, at, z):
    a = math.radians(WELL_YAW_DEG)
    ax = np.array([math.cos(a), math.sin(a)])
    n = np.array([-ax[1], ax[0]])
    h, t = WELL_HALF_M, .30
    for d, m, hx, hy in ((ax, n, t / 2, h), (-ax, n, t / 2, h), (n, ax, h - t, t / 2), (-n, ax, h - t, t / 2)):
        _box(acc, layer, STONE, np.asarray(at) + d * (h - t / 2), z - .05, z + .45, hx, hy, ax)
    c = [np.asarray(at) + ax * sx * (h - t) + n * sy * (h - t) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    acc.quad(layer, "bed_soil", *[_p(p, z + .12) for p in c])


def _bed(acc, layer, at, z):
    pts = [np.asarray(at) + BED_R_M * np.array([math.cos(a), math.sin(a)])
           for a in (math.pi / 8 + 2 * math.pi * i / 8 for i in range(8))]
    V = [_p(at, z + .06)] + [_p(p, z + .04) for p in pts]
    acc.add(layer, "bed_soil", V, [[0, i + 1, (i + 1) % 8 + 1] for i in range(8)])
    for i in range(8):                       # low stone edging
        p, q = pts[i], pts[(i + 1) % 8]
        d = (q - p) / np.linalg.norm(q - p)
        _box(acc, layer, STONE, (p + q) / 2, z - .05, z + .14, float(np.linalg.norm(q - p)) / 2 + .05, .09, d)


def _strip(acc, layer, z_at):
    P = [np.asarray(p, float) for p in STRIP_EN]
    for i in range(4):
        p, q = P[i], P[(i + 1) % 4]
        d = (q - p) / np.linalg.norm(q - p)
        z = min(z_at(p), z_at(q))
        _box(acc, layer, STONE, (p + q) / 2, z - .1, z + .38, float(np.linalg.norm(q - p)) / 2 + .12, .12, d)


def _flowers(acc, layer, c, z, t, n, hl, hw, hgt, palette, key):
    """Flower mass of a planter: a lumpy mound + standing tufts, blossom / leaf colour per vertex (COLOR_0)."""
    low = layer == "buildings_low"
    t3, n3 = np.r_[t, 0.], np.r_[n, 0.]
    c3 = np.r_[c, z]
    nu, nv = (3, 2) if low else (8, 4)
    V, COL, T = [], [], []
    for j in range(nv + 1):
        for i in range(nu + 1):
            u, v = 2 * i / nu - 1, 2 * j / nv - 1
            inner = 0 < i < nu and 0 < j < nv
            hh = hgt * (1 - max(abs(u) ** 4, abs(v) ** 2)) ** 0.5 * (0.65 + 0.6 * _h(key, "h", i, j)) if inner else -0.02
            spill = 1.0 if inner else 1.07                      # the plants hang over the rim
            V.append(c3 + t3 * u * hl * spill + n3 * v * hw * spill + np.array([0, 0, hh]))
            pal = palette if _h(key, "c", i, j) < 0.58 else LEAF
            cc = np.array(pal[int(_h(key, "k", i, j) * len(pal)) % len(pal)]) * (0.75 + 0.35 * _h(key, "s", i, j))
            COL.append([*np.clip(cc * 0.5, 0, 1), 1.0])
    for j in range(nv):
        for i in range(nu):
            a = j * (nu + 1) + i
            T += [[a, a + 1, a + nu + 2], [a, a + nu + 2, a + nu + 1]]
    V = np.array(V)
    acc.add(layer, FLOWERS, V, T, V[:, :2].copy(), COL=np.array(COL))
    if low:
        return
    V, COL, T = [], [], []
    for k in range(16):                                         # tufts standing out of the mound
        u, v = 1.7 * _h(key, "tu", k) - 0.85, 1.5 * _h(key, "tv", k) - 0.75
        base = c3 + t3 * u * hl + n3 * v * hw + np.array([0, 0, hgt * (0.35 + 0.4 * (1 - max(abs(u), abs(v))))])
        a = math.pi * _h(key, "ta", k)
        d = (t3 * math.cos(a) + n3 * math.sin(a)) * (0.07 + 0.05 * _h(key, "tw", k))
        lean = (t3 * (_h(key, "tl", k) - .5) + n3 * (_h(key, "tm", k) - .5)) * 0.10 + np.array([0, 0, 0.11 + 0.09 * _h(key, "th", k)])
        pal = palette if _h(key, "tc", k) < 0.75 else LEAF
        cc = np.clip(np.array(pal[k % len(pal)]) * (0.8 + 0.4 * _h(key, "ts", k)) * 0.5, 0, 1)
        dark = np.clip(np.array(LEAF[k % len(LEAF)]) * 0.5, 0, 1)
        for face in (1, -1):
            b = len(V)
            V += [base - d * face, base + d * face, base + d * face + lean, base - d * face + lean]
            COL += [[*dark, 1.0], [*dark, 1.0], [*cc, 1.0], [*cc, 1.0]]
            T += [[b, b + 1, b + 2], [b, b + 2, b + 3]]
    V = np.array(V)
    acc.add(layer, FLOWERS, V, T, V[:, :2].copy(), COL=np.array(COL))


def _planter(acc, layer, at, z, t, hl, hw, h, flower_h, palette, key):
    """Dark boarded planter box on low feet with a flower mass (Commons: begonias at the monument, boxes on the edges)."""
    low = layer == "buildings_low"
    t = np.asarray(t, float) / np.linalg.norm(t)
    n = np.array([-t[1], t[0]])
    t3, n3, up = np.r_[t, 0.], np.r_[n, 0.], np.array([0., 0., 1.])
    c = np.r_[np.asarray(at, float), z]
    age = _h(key, "age")
    for k, (d, nn, half, other) in enumerate(((t3, n3, hl + .014, hw), (t3, -n3, hl + .014, hw), (n3, t3, hw, hl), (n3, -t3, hw, hl))):
        rows = 1 if low else 3
        for j in range(rows):                                   # three boards per side, each its own tone
            z0 = .06 + (h - .06) * j / rows
            z1 = .06 + (h - .06) * (j + 1) / rows - (.0 if low else .008)
            g = 0.36 + 0.30 * _h(key, "b", k, j) + 0.25 * age
            col = np.array([g, g * (0.97 + 0.05 * age), g * (0.90 + 0.14 * age)])     # greyer with age
            if j == 0 and not low:
                col = col * 0.72                                # splash-soiled bottom board
            _obox(acc, layer, WOOD, c + nn * other + up * (z0 + z1) / 2, d * half, nn * .014, up * (z1 - z0) / 2,
                  col=np.clip(col, 0.05, 0.98), uv0=(7.3 * _h(key, "u", k, j), 0.137 * int(19 * _h(key, "v", k, j)) + .068))
    if not low:
        for sx in (-1, 1):
            for sy in (-1, 1):
                _obox(acc, layer, WOOD, c + t3 * sx * (hl - .05) + n3 * sy * (hw - .04) + up * .03, t3 * .04, n3 * .04, up * .03,
                      col=(.2, .19, .18), skip=(0, 1))
    _flowers(acc, layer, c[:2], z + h - .03, t, n, hl - .02, hw - .02, flower_h, palette, key)


def _bench(acc, layer, at, z, t, n, variant, key, z_at):
    """Bench with cast-iron ends and dark stained slats; variants: 0 = with arms (1.8 m), 1 = plain back (1.5 m),
    2 = backless (1.8 m). Each slat has its own tone (bleached / re-stained / replaced), sits a few mm off and the
    worn front edge of the seat is paler. Dimensions WORKING_VALUE (typical Polish cast-end park bench)."""
    low = layer == "buildings_low"
    t = np.asarray(t, float) / np.linalg.norm(t)
    n = np.asarray(n, float) / np.linalg.norm(n)
    t3, n3, up = np.r_[t, 0.], np.r_[n, 0.], np.array([0., 0., 1.])
    L = (1.80, 1.50, 1.80)[variant]
    back = variant != 2
    e = L / 2 - .12
    c = np.asarray(at, float)

    def gz(off_t, off_n):
        zz = float(z_at(c + t * off_t + n * off_n)) if z_at is not None else float(z)
        return zz if math.isfinite(zz) else float(z)
    feet = {(sd, k): gz(sd * e, o) for sd in (-1, 1) for k, o in (("f", .22), ("b", -.25))}
    zr = max(float(z), max(feet.values()) - .04)
    c3 = np.r_[c, zr]
    age = _h(key, "age")                                        # 0 freshly re-stained .. 1 bleached grey
    swap = int(_h(key, "swap") * 9)                             # index of a replaced (pale, new) board; >= count = none

    def slat_col(i, front=False):
        g = 0.42 + 0.22 * _h(key, "g", i) + 0.36 * age
        col = np.array([g, g * (0.96 + 0.06 * age), g * (0.86 + 0.20 * age)])
        if i == swap:
            col = np.array([0.98, 0.84, 0.62])                  # replaced board: fresh pale softwood
        if front:
            col = col * 1.22 + 0.04                             # edge rubbed by legs and coats
        return np.clip(col, 0.05, 0.98)

    if low:
        _obox(acc, layer, WOOD, c3 + n3 * .01 + up * .44, t3 * L / 2, n3 * .20, up * .02, col=slat_col(2), skip=(0,))
        if back:
            _obox(acc, layer, WOOD, c3 - n3 * .27 + up * .72, t3 * L / 2, n3 * .02, up * .15, col=slat_col(6))
        for sd in (-1, 1):
            _box(acc, layer, IRON, c + t * sd * e + n * .20, min(feet[(sd, "f")], zr) - .06, zr + .43, .02, .025, t)
            _box(acc, layer, IRON, c + t * sd * e - n * .24, min(feet[(sd, "b")], zr) - .06, zr + (.88 if back else .43), .02, .025, t)
        return
    for sd in (-1, 1):                                          # cast ends: bars in the (n, z) plane
        o = c3 + t3 * sd * e

        def P(a, b, zabs=None, o=o):
            return o + n3 * a + up * b if zabs is None else np.r_[(o + n3 * a)[:2], zabs]
        zf, zb = min(feet[(sd, "f")], zr) - .05, min(feet[(sd, "b")], zr) - .05
        segs = [(P(.25, 0, zf), P(.19, .21)), (P(.19, .21), P(.225, .41)), (P(.235, .405), P(-.215, .395))]
        if back:
            segs += [(P(-.27, 0, zb), P(-.20, .40)), (P(-.20, .40), P(-.315, .90))]
        else:
            segs += [(P(-.25, 0, zb), P(-.19, .21)), (P(-.19, .21), P(-.225, .405))]
        if variant == 0:
            segs += [(P(.225, .41), P(.255, .645)), (P(-.265, .66), P(.285, .645))]
        for a, b in segs:
            _bar(acc, layer, IRON, a, b, t3, .042, .04)
    _bar(acc, layer, IRON, c3 - t3 * e + up * .22, c3 + t3 * e + up * .22, n3, .022, .022)      # tie rod
    nseat = 4 if variant == 1 else 5
    w = .092 if variant == 1 else .072
    pitch = (.41 - w) / (nseat - 1)
    for i in range(nseat):
        off = .205 - w / 2 - pitch * i
        dz = .004 * (_h(key, "dz", i) - .5) - .006 * (1 - abs(2 * i / (nseat - 1) - 1)) * age          # sagging middle boards
        yaw = .006 * (_h(key, "yw", i) - .5)
        _obox(acc, layer, WOOD, c3 + n3 * off + up * (.43 + dz), (t3 + n3 * yaw) * L / 2, n3 * w / 2, up * .017,
              col=slat_col(i, front=(i == 0)), col_ends=slat_col(i) * 0.7,
              uv0=(5.1 * _h(key, "u", i), 0.137 * int(19 * _h(key, "v", i)) + .068))
    if back:
        nb = 2 if variant == 1 else 3
        wb = .11 if variant == 1 else .085
        lean = np.array([-.115, .50]) / np.linalg.norm([-.115, .50])            # direction of the back upright in (n, z)
        missing = 1 if (variant == 0 and _h(key, "miss") < 0.22) else -1         # a bench with one back board gone
        for i in range(nb):
            if i == missing:
                continue
            s = .16 + (.44 - wb) * i / (nb - 1) + wb / 2
            pc = c3 + n3 * (-.20 + lean[0] * s + .028) + up * (.40 + lean[1] * s)
            yaw = .006 * (_h(key, "byw", i) - .5)
            _obox(acc, layer, WOOD, pc, (t3 + up * yaw) * L / 2, (n3 * lean[0] + up * lean[1]) * wb / 2, (n3 * lean[1] - up * lean[0]) * .015,
                  col=slat_col(5 + i), col_ends=slat_col(5 + i) * 0.7,
                  uv0=(5.1 * _h(key, "bu", i), 0.137 * int(19 * _h(key, "bv", i)) + .068))


def build(buf, region, origin, overrides, zsurf, report):
    """Build the square objects of Tykocin. `zsurf` samples the finished surface for arrays of local E, N."""
    if region != REGION:
        return None
    result = {"id": ASSET_ID, "status": "skipped", "monument": None, "benches": [], "planters": [], "refused": [],
              "lamps": "UNVERIFIED - none placed (not resolvable on the orthophoto)",
              "trees": "none on the square (orthophoto 2024)", "figure": "HERO_ASSET_NOT_APPROVED (awaits visual-critic)"}
    report[ASSET_ID] = result
    acc = BM.Acc()

    def ground(p):
        return float(np.asarray(zsurf(np.array([p[0]]), np.array([p[1]]))).ravel()[0])

    z = ground(MONUMENT_EN)
    if math.isfinite(z):
        for layer in LAYERS:
            top = _monument(acc, layer, MONUMENT_EN, z)
        f, r, _ = MK.frame(MONUMENT_FORWARD)
        KP._box(acc, "collision", "collision_building", MONUMENT_EN, z - .1, z + PLATFORM_TOP, 2.45, 2.45, r[:2])
        KP._box(acc, "collision", "collision_building", MONUMENT_EN, z + PLATFORM_TOP, z + .9, 1.65, 1.65, r[:2])
        KP._box(acc, "collision", "collision_building", MONUMENT_EN, z + .9, z + top, 1.0, 1.0, r[:2])
        meta = hero()[1]
        result["monument"] = {"at_en": list(MONUMENT_EN), "height_m": round(top, 2), "facing": "south (ESTIMATED)",
                              "dimensions": "WORKING_VALUE", "hero_asset": HERO, "hero_tris": meta["tris"]}
        for k, (pr, pf) in enumerate(MONUMENT_PLANTERS):
            key = ("mp", k)
            xy = np.asarray(MONUMENT_EN) + r[:2] * (pr + .25 * (_h(key, "x") - .5)) + f[:2] * (pf + .25 * (_h(key, "y") - .5))
            zz = ground(xy)
            if not math.isfinite(zz):
                continue
            side = r[:2] if abs(pf) > abs(pr) else f[:2]
            a = math.radians(16.0 * (_h(key, "yaw") - .5))
            t = np.array([side[0] * math.cos(a) - side[1] * math.sin(a), side[0] * math.sin(a) + side[1] * math.cos(a)])
            for layer in LAYERS:
                _planter(acc, layer, xy, zz, t, .55, .26, .46, .30, BEGONIA, key)
            KP._box(acc, "collision", "collision_steel", xy, zz - .1, zz + .7, .57, .28, t)
            result["planters"].append({"at_en": [round(float(v), 2) for v in xy], "kind": "begonias at the monument",
                                       "confidence": "ESTIMATED (Commons photos)"})
    else:
        result["refused"].append({"at": list(MONUMENT_EN), "reason": "non-finite terrain"})
    for at, fn in ((WELL_EN, _well), (BED_EN, _bed)):
        z = ground(at)
        if math.isfinite(z):
            for layer in LAYERS:
                fn(acc, layer, at, z)
    if all(math.isfinite(ground(p)) for p in STRIP_EN):
        for layer in LAYERS:
            _strip(acc, layer, ground)
    row = np.asarray(BENCH_ROW, float) / np.linalg.norm(BENCH_ROW)
    toward = np.array([-row[1], row[0]])                 # north: the benches look at the plaza
    nb = 0
    for k, xy0 in enumerate(BENCHES_EN):
        key = ("mark", k)
        # nobody sets street furniture out with a string: 2-9 deg either way, +-0.25 m across the row, +-0.3 m along it
        a = math.radians((2.0 + 7.0 * _h(key, "yaw")) * (1.0 if _h(key, "sign") < .5 else -1.0))
        t = np.array([row[0] * math.cos(a) - row[1] * math.sin(a), row[0] * math.sin(a) + row[1] * math.cos(a)])
        n = np.array([-t[1], t[0]])
        xy = np.asarray(xy0, float) + toward * .5 * (_h(key, "dn") - .5) + row * .6 * (_h(key, "dt") - .5)
        z = ground(xy)
        if not math.isfinite(z):
            result["refused"].append({"at": list(xy0), "reason": "non-finite terrain"})
            continue
        if k in PLANTER_MARKS:
            for layer in LAYERS:
                _planter(acc, layer, xy, z, t, .62, .23, .40, .22, PETUNIA, key)
            KP._box(acc, "collision", "collision_steel", xy, z - .1, z + .6, .64, .25, t)
            result["planters"].append({"at_en": list(xy0), "kind": "edge planter", "confidence": "ESTIMATED (orthophoto mark)"})
            continue
        variant = (0, 1, 0, 2, 0, 1)[nb % 6]
        nb += 1
        for layer in LAYERS:
            _bench(acc, layer, xy, z, t, n, variant, key, ground)
        KP._box(acc, "collision", "collision_steel", xy, z - .1, z + .9, (.90, .75, .90)[variant], .30, t)
        result["benches"].append({"at_en": list(xy0), "variant": BENCH_VARIANTS[variant], "yaw_off_deg": round(math.degrees(a), 1),
                                  "confidence": "ESTIMATED (orthophoto mark)"})
    # LOD1 reuses materials that the chunk already has - except the weathered stone, the bench wood and the flowers,
    # which keep their COLOR_0 tint so that nothing changes colour at the LOD switch (3 extra low draws in one chunk)
    for old, new in {STONE: "plaster_grey", GILT: "plaster_yellow", IRON: "plinth_dark", "bed_soil": "plinth_dark"}.items():
        parts = acc.d.pop(("buildings_low", old), [])
        if parts:
            acc.d.setdefault(("buildings_low", new), []).extend(parts)
    tris = {}
    for (layer, mat), items in acc.d.items():
        tris[layer] = tris.get(layer, 0) + int(sum(len(it[1]) for it in items))
    acc.flush(buf, ASSET_ID)
    result.update(status="applied" if tris else "skipped", tris=tris)
    return result
