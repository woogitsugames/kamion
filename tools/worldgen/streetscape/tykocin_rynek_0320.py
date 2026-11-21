"""Plac Czarnieckiego (market square) in Tykocin: monument and square furniture (ADR 0320).

Use ``build(buf, region, origin, overrides, zsurf, report)`` after the paved area plan is known. Anchors are
region-local E / N of tile `tykocin` (origin EPSG:2180 751371, 600319), measured on the GUGiK orthophoto 2024
(0.25 m, +-0.5 m): the square after its renewal is a paved plaza with the monument, two lawns and NO trees
(the paving itself is three `paved_area` overrides in Data/Regions/tykocin/overrides.yaml).

Monument of Stefan Czarniecki: silhouette and proportions from Wikimedia Commons "Tykocin pomnik Stefana
Czarnieckiego 01 / 05 / 08" (CC BY-SA 4.0), "Tykocin, pomnik Stefana Czarnieckiego, 1762 01" (CC BY-SA 3.0 pl) and
"Mglisty poranek na placu Czarnieckiego w Tykocinie z pomnikiem" (CC BY 4.0) - reference only, manifest in
Data/raw/refs/tykocin-rynek-commons. Stepped base, iron picket fence, plain block, waisted baroque pedestal, figure
with the mace in the outstretched right hand. Heights are WORKING_VALUE (about 7.4 m to the head, estimated against the
fence and the houses); the facing (south) is ESTIMATED from the light on the midday photos. A stylised low-poly figure,
not a scan or a copy of the sculpture; inscriptions and the cartouche are omitted.

Benches: ten dark elongated marks along the south edge of the plaza / east lawn on the orthophoto, identity ESTIMATED.
Lamp posts of the square are not resolvable on the orthophoto: none placed here (UNVERIFIED, see ADR 0320).
"""
from __future__ import annotations

import math

import numpy as np

from . import buildings_mesh as BM
from . import monument_kit as MK
from . import knyszyn_park_props_0227 as KP

REGION = "tykocin"
ASSET_ID = "tykocin_rynek_0320"
LAYERS = ("buildings", "buildings_low")
MONUMENT_EN = (438.0, -86.6)          # centre of the base, orthophoto 2024
MONUMENT_FORWARD = (0.0, -1.0)        # ESTIMATED: faces south (DW671)
BENCHES_EN = ((426.3, -100.1), (431.6, -99.25), (441.0, -98.4), (446.9, -97.4), (452.9, -96.75), (461.9, -95.9),
              (466.6, -95.25), (479.1, -93.4), (485.4, -93.0), (491.6, -91.9))
BENCH_ROW = (0.993, 0.118)            # direction of the row (south edge of the plaza), orthophoto
WELL_EN, WELL_HALF_M, WELL_YAW_DEG = (470.1, -81.0), 1.9, 35.0      # square stone-rimmed basin on the east lawn
BED_EN, BED_R_M = (489.4, -77.25), 4.2                              # octagonal bed on the east lawn
STRIP_EN = ((457.9, -73.6), (495.7, -65.1), (496.2, -67.6), (458.4, -76.1))   # long low frame, north of the east lawn
STONE, SAND, IRON, GILT = "plinth_grey", "monument_sandstone", "fence_anthracite", "monument_gilt"

# Pedestal: (z above the block cornice, half size) of a rounded-square section. WORKING_VALUE read off Commons
# cs152250558 (front elevation of the pedestal) - belly below, waist above, cornice plate under the figure.
PEDESTAL = ((0.00, .80), (0.10, .86), (0.45, .93), (0.85, .86), (1.30, .68), (1.75, .60), (2.15, .60), (2.15, .74),
            (2.30, .78), (2.30, .68), (2.42, .62))
# Figure: (z, half width, half depth, right offset, forward offset). Long coat to the ground, belted, fur cap.
FIGURE = ((0.00, .34, .28, 0, 0), (0.10, .30, .25, 0, 0), (0.50, .37, .28, 0, 0), (1.00, .34, .26, 0, 0),
          (1.32, .28, .21, 0, 0), (1.45, .30, .22, 0, 0), (1.72, .35, .24, 0, 0), (1.90, .37, .22, 0, 0),
          (1.98, .22, .17, 0, 0), (2.04, .10, .10, 0, .02), (2.10, .115, .125, 0, .03), (2.24, .125, .135, 0, .03),
          (2.34, .115, .12, 0, .02), (2.42, .07, .07, 0, .01))
CLOAK = ((0.30, .40, .27, -.16, -.10), (1.00, .42, .28, -.17, -.10), (1.60, .38, .25, -.14, -.09),
         (1.88, .26, .18, -.10, -.07), (1.96, .10, .08, -.06, -.05))


def _p(xy, z):
    return [float(xy[0]), float(xy[1]), float(z)]


def _box(acc, layer, mat, xy, z0, z1, hx, hy, axis=(1., 0.), skip=(0,)):
    a = np.asarray(axis, float); a /= np.linalg.norm(a)
    n = np.array([-a[1], a[0]])
    acc.box(layer, mat, _p(xy, (z0 + z1) / 2), np.r_[a * hx, 0.], np.r_[n * hy, 0.], [0., 0., (z1 - z0) / 2], skip=skip)


def _monument(acc, layer, at, z):
    low = layer == "buildings_low"
    f, r, up = MK.frame(MONUMENT_FORWARD)
    at = np.asarray(at, float)
    ax = r[:2]
    # stepped base: sett-clad lower step, two sandstone steps
    _box(acc, layer, STONE, at, z, z + .35, 2.45, 2.45, ax)
    _box(acc, layer, SAND, at, z + .35, z + .58, 2.05, 2.05, ax)
    _box(acc, layer, SAND, at, z + .58, z + .78, 1.55, 1.55, ax)
    # plain block with a base moulding and a cornice
    zb = z + .78
    _box(acc, layer, SAND, at, zb, zb + .16, 1.02, 1.02, ax)
    _box(acc, layer, SAND, at, zb + .16, zb + 1.42, .92, .92, ax)
    _box(acc, layer, SAND, at, zb + 1.42, zb + 1.56, 1.03, 1.03, ax, skip=())
    zp = zb + 1.56
    base = [at[0], at[1], zp]
    rings = [(h, s, s, 0., 0., 9.0) for h, s in (MK.thin(PEDESTAL) if low else PEDESTAL)]
    MK.lathe(acc, layer, SAND, base, MONUMENT_FORWARD, rings, sides=8 if low else 20)
    zf = zp + PEDESTAL[-1][0]
    fb = [at[0], at[1], zf]
    sides = 6 if low else 12
    MK.lathe(acc, layer, SAND, fb, MONUMENT_FORWARD, CLOAK, sides=sides)
    MK.lathe(acc, layer, SAND, fb, MONUMENT_FORWARD, FIGURE, sides=sides)
    o = np.asarray(fb, float)

    def q(right, fwd, h):
        return o + r * right + f * fwd + up * h
    ls = 4 if low else 6
    # right arm stretched out with the mace (gilt), left arm on the hip under the cloak
    MK.limb(acc, layer, SAND, [q(.30, .02, 1.86), q(.56, .12, 1.93), q(.86, .24, 2.06)], [.095, .085, .07], sides=ls)
    MK.limb(acc, layer, GILT, [q(.88, .25, 1.92), q(.90, .27, 2.50)], [.022, .026], sides=4)
    MK.sphere(acc, layer, GILT, q(.90, .27, 2.60), .11, sides=6 if low else 8, stacks=3 if low else 5)
    MK.limb(acc, layer, SAND, [q(-.30, .02, 1.84), q(-.50, .06, 1.48), q(-.30, .20, 1.28)], [.09, .08, .07], sides=ls)
    if low:
        return zf + 2.71 - z
    # cartouche block at the foot of the figure (blank) and the two volutes of the cornice
    _box(acc, layer, SAND, at + f[:2] * .60, zf - .30, zf + .16, .26, .08, ax, skip=())
    for sg in (-1., 1.):
        _box(acc, layer, SAND, at + r[:2] * sg * .80, zp + 1.86, zp + 2.20, .08, .30, ax, skip=())
    # iron fence on the upper step: rails and flat pickets, four low stone posts with a chain line outside it
    half, h0, h1 = 1.90, z + .58, z + .58 + 1.25
    for d, n in ((r, f), (f, r), (-r, f), (-f, r)):
        c = np.r_[at, 0.] + d * half
        for hz in (h0 + .12, h1 - .10):
            acc.box(layer, IRON, c + up * hz, n * half, d * .02, up * .02)
        npk = int(2 * half / .13)
        V, T = [], []
        for i in range(npk + 1):
            p = c + n * (-half + 2 * half * i / npk)
            b = len(V)
            V += [p - n * .012 + up * h0, p + n * .012 + up * h0, p + n * .012 + up * h1, p - n * .012 + up * h1]
            T += [[b, b + 1, b + 2], [b, b + 2, b + 3], [b, b + 2, b + 1], [b, b + 3, b + 2]]
        acc.add(layer, IRON, np.array(V), T)
    for sx in (-1., 1.):
        for sy in (-1., 1.):
            _box(acc, layer, STONE, at + r[:2] * sx * 3.1 + f[:2] * sy * 3.1, z, z + .72, .13, .13, ax)
    return zf + 2.71 - z


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


def build(buf, region, origin, overrides, zsurf, report):
    """Build the square objects of Tykocin. `zsurf` samples the finished surface for arrays of local E, N."""
    if region != REGION:
        return None
    result = {"id": ASSET_ID, "status": "skipped", "monument": None, "benches": [], "refused": [],
              "lamps": "UNVERIFIED - none placed (not resolvable on the orthophoto)",
              "trees": "none on the square (orthophoto 2024)", "figure": "STYLISED_NOT_APPROVED"}
    report[ASSET_ID] = result
    acc = BM.Acc()

    def ground(p):
        return float(np.asarray(zsurf(np.array([p[0]]), np.array([p[1]]))).ravel()[0])

    z = ground(MONUMENT_EN)
    if math.isfinite(z):
        for layer in LAYERS:
            top = _monument(acc, layer, MONUMENT_EN, z)
        f, r, _ = MK.frame(MONUMENT_FORWARD)
        KP._box(acc, "collision", "collision_building", MONUMENT_EN, z - .1, z + .78, 2.45, 2.45, r[:2])
        KP._box(acc, "collision", "collision_building", MONUMENT_EN, z + .78, z + top, 1.0, 1.0, r[:2])
        result["monument"] = {"at_en": list(MONUMENT_EN), "height_m": round(top, 2), "facing": "south (ESTIMATED)",
                              "dimensions": "WORKING_VALUE"}
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
    for xy in BENCHES_EN:
        z = ground(xy)
        if not math.isfinite(z):
            result["refused"].append({"at": list(xy), "reason": "non-finite terrain"})
            continue
        for layer in LAYERS:
            KP._bench(acc, layer, np.asarray(xy, float), z, row, toward)
        KP._box(acc, "collision", "collision_steel", np.asarray(xy, float), z - .1, z + .9, .91, .30, row)
        result["benches"].append({"at_en": list(xy), "confidence": "ESTIMATED (orthophoto mark)"})
    # LOD1 reuses materials that the chunk already has
    for old, new in {"bench_wood": "wood_planks", STONE: "plaster_grey", SAND: "plaster_beige", GILT: "plaster_yellow",
                     "steel_painted": "plinth_dark", IRON: "plinth_dark",
                     "bed_soil": "plinth_dark"}.items():
        parts = acc.d.pop(("buildings_low", old), [])
        if parts:
            acc.d.setdefault(("buildings_low", new), []).extend(parts)
    tris = {}
    for (layer, mat), items in acc.d.items():
        tris[layer] = tris.get(layer, 0) + int(sum(len(it[1]) for it in items))
    acc.flush(buf, ASSET_ID)
    result.update(status="applied" if tris else "skipped", tris=tris)
    return result
