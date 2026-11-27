"""Stone parts of the Czarniecki monument in Tykocin (ADR 0320 dopisek tykocin-plaza-s24): sculpted figure + pedestal.

    blender -b --factory-startup -P tools/blender/world/landmarks/make_czarniecki.py -- [--output <dir>] [--render <dir>] [--blend]
    blender -b --factory-startup -P tools/blender/world/landmarks/make_czarniecki.py -- --render-existing --render <abs dir> [--output <asset dir>]
    Look-dev options: --lighting clear|overcast, --lod lod0|lod1, --cams <comma-separated names>, --samples <n>.

Reads  art-source/world/landmarks/tykocin_czarniecki/dims.json (authored sizes and sources, all WORKING_VALUE).
Writes art-source/world/landmarks/tykocin_czarniecki/tykocin_czarniecki.npz (plain git, ~0.5 MB: the world build must
       not depend on LFS) and tykocin_czarniecki_meta.json (triangle counts, sha256 of this script and of dims.json).

Pipeline (skill blender-hero-asset, everything from code, nothing modelled by hand):
  1. high poly: the figure, head and cartouches are voxel-remeshed separately. The shoulders and collar are
     smoothed before adding the surface relief. Eyes, moustache and beard relief are carved on closed surfaces.
  2. low poly: quadric collapse to the LOD0 / LOD1 budgets (silhouette kept, flat cloth gets few triangles).
  3. architecture (steps, block, waisted pedestal with recessed panels, cornice): explicit grids swept round the
     square plan, hard edges where the profile is marked sharp.
  4. bake to COLOR_0 against the HIGH poly (BVH): ambient occlusion, cavity dirt, rain shelter, run-off streaks
     and lichen for sandstone (`facade_tint`); signed curvature and AO for the metal (`_BRONZE_PATINA`).
  5. export per LOD and material: V (x right, y forward, z up, metres), UV0 (metres), COLOR_0, triangles.

npz keys: "<lod>|<material>|V/UV/COL/T", lod in (lod0, lod1). Materials: monument_sandstone_aged (COLOR_0 = tint / 2,
a = 1), monument_bronze_patina (vambrace and glove: COLOR_0 = patina, wear, AO, 1 - ADR 0331), monument_gilt (mace),
plaza_sett_grey (sett-clad riser of the platform).

A stylised sculpt after the photos listed in dims.json - not a scan or a copy of the sculpture; no lettering.
"""
import hashlib
import json
import math
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector, noise
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree

REPO = Path(__file__).resolve().parents[4]
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ASSET = "tykocin_czarniecki"
OUT = REPO / "art-source" / "world" / "landmarks" / ASSET
DIMS = json.loads((OUT / "dims.json").read_text(encoding="utf-8"))
HZ, HS = DIMS["heights_m"], DIMS["half_sizes_m"]
STONE, PATINA, GILT, SETT = "monument_sandstone_aged", "monument_bronze_patina", "monument_gilt", "plaza_sett_grey"
VOXEL = 0.006
BUDGET = {"lod0": {"figure": 10500, "head": 3800, "cartouches": 1300}, "lod1": {"figure": 520, "head": 180, "cartouches": 96}}
ZF = HZ["cornice_top"]                 # top of the cornice = underside of the figure's slab
SLAB = HZ["figure_slab"]
RNG = np.random.default_rng(1762)
D2R = math.pi / 180.0


def arg(name):
    return argv[argv.index(name) + 1] if name in argv else None


# ------------------------------------------------------------------------------------------------ mesh primitives
class Pool:
    """Triangle / quad soup of closed primitives that the voxel remesh fuses."""

    def __init__(self):
        self.V, self.F, self.n = [], [], 0

    def add(self, V, F):
        V = np.asarray(V, float)
        self.V.append(V)
        self.F += [tuple(int(i) + self.n for i in f) for f in F]
        self.n += len(V)

    def obj(self, name):
        me = bpy.data.meshes.new(name)
        me.from_pydata(np.concatenate(self.V).tolist(), [], self.F)
        me.update()
        ob = bpy.data.objects.new(name, me)
        bpy.context.scene.collection.objects.link(ob)
        return ob


def rot_z(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1.0]])


def rot_x(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[1.0, 0, 0], [0, c, -s], [0, s, c]])


def rot_y(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, 0, s], [0, 1.0, 0], [-s, 0, c]])


def ellipsoid(pool, c, r, R=None, seg=20, rings=12, deform=None):
    V = [[0, 0, 1.0]]
    for i in range(1, rings):
        ph = math.pi * i / rings
        for j in range(seg):
            th = 2 * math.pi * j / seg
            V.append([math.sin(ph) * math.cos(th), math.sin(ph) * math.sin(th), math.cos(ph)])
    V.append([0, 0, -1.0])
    V = np.array(V) * np.asarray(r, float)
    if deform is not None:
        deform(V)
    if R is not None:
        V = V @ np.asarray(R).T
    V = V + np.asarray(c, float)
    F = []
    for j in range(seg):
        F.append((0, 1 + j, 1 + (j + 1) % seg))
    for i in range(rings - 2):
        a, b = 1 + i * seg, 1 + (i + 1) * seg
        for j in range(seg):
            F.append((a + j, b + j, b + (j + 1) % seg, a + (j + 1) % seg))
    last = len(V) - 1
    a = 1 + (rings - 2) * seg
    for j in range(seg):
        F.append((last, a + (j + 1) % seg, a + j))
    pool.add(V, F)


def smooth_path(P, n=6):
    """Catmull-Rom through the points, n samples per span."""
    P = np.asarray(P, float)
    if len(P) < 3:
        t = np.linspace(0, 1, n + 1)[:, None]
        return P[0] * (1 - t) + P[1] * t
    Q = np.vstack([2 * P[0] - P[1], P, 2 * P[-1] - P[-2]])
    out = []
    for i in range(1, len(Q) - 2):
        for k in range(n):
            t = k / n
            out.append(0.5 * ((2 * Q[i]) + (-Q[i - 1] + Q[i + 1]) * t + (2 * Q[i - 1] - 5 * Q[i] + 4 * Q[i + 1] - Q[i + 2]) * t * t
                              + (-Q[i - 1] + 3 * Q[i] - 3 * Q[i + 1] + Q[i + 2]) * t ** 3))
    out.append(P[-1])
    return np.array(out)


def tube(pool, path, radii, sides=12, smooth=6, flat=None, closed=False):
    """Capped tube along a path; radii per given point (interpolated). flat = (axis vector, factor) squashes the section."""
    P0 = np.asarray(path, float)
    r0 = np.broadcast_to(np.asarray(radii, float), (len(P0),)) if np.ndim(radii) else np.full(len(P0), float(radii))
    if closed:
        P0 = np.vstack([P0, P0[0]])
        r0 = np.r_[r0, r0[0]]
    P = smooth_path(P0, smooth) if smooth else P0
    s0 = np.r_[0, np.cumsum(np.linalg.norm(np.diff(P0, axis=0), axis=1))]
    s = np.r_[0, np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))]
    r = np.interp(s / s[-1], s0 / s0[-1], r0)
    if closed:
        P, r = P[:-1], r[:-1]
    n = len(P)
    V = []
    up = np.array([0.0, 0.0, 1.0])
    for i in range(n):
        a, b = P[(i - 1) % n if closed else max(i - 1, 0)], P[(i + 1) % n if closed else min(i + 1, n - 1)]
        t = (b - a) / max(np.linalg.norm(b - a), 1e-9)
        u = np.cross(t, up)
        if np.linalg.norm(u) < 1e-3:
            u = np.cross(t, [1.0, 0, 0])
        u /= np.linalg.norm(u)
        w = np.cross(t, u)
        for j in range(sides):
            th = 2 * math.pi * j / sides
            d = u * math.cos(th) + w * math.sin(th)
            if flat is not None:
                ax = np.asarray(flat[0], float)
                d = d - ax * np.dot(d, ax) * (1 - flat[1])
            V.append(P[i] + d * r[i])
    F = []
    m = n if closed else n - 1
    for i in range(m):
        a, b = i * sides, ((i + 1) % n) * sides
        for j in range(sides):
            F.append((a + j, a + (j + 1) % sides, b + (j + 1) % sides, b + j))
    V = list(V)
    if not closed:
        V += [P[0], P[-1]]
        c0, c1 = len(V) - 2, len(V) - 1
        for j in range(sides):
            F.append((c0, (j + 1) % sides, j))
            F.append((c1, (n - 1) * sides + j, (n - 1) * sides + (j + 1) % sides))
    pool.add(np.array(V), F)


def lathe(pool, zs, rfun, n=144, cfun=None, zfun=None):
    """Closed body: rings at heights zs, radius rfun(theta array, z) around cfun(z) = (x, y). theta from +x to +y."""
    th = np.linspace(0, 2 * math.pi, n, endpoint=False)
    rings = []
    for z in zs:
        r = rfun(th, z)
        c = cfun(z) if cfun else (0.0, 0.0)
        zz = zfun(th, z) if zfun else np.full(n, z)
        rings.append(np.stack([c[0] + r * np.cos(th), c[1] + r * np.sin(th), zz], 1))
    V = np.concatenate(rings)
    F = []
    for i in range(len(zs) - 1):
        a, b = i * n, (i + 1) * n
        for j in range(n):
            F.append((a + j, a + (j + 1) % n, b + (j + 1) % n, b + j))
    cb, ct = len(V), len(V) + 1
    V = np.vstack([V, rings[0].mean(0), rings[-1].mean(0)])
    top = (len(zs) - 1) * n
    for j in range(n):
        F.append((cb, (j + 1) % n, j))
        F.append((ct, top + j, top + (j + 1) % n))
    pool.add(V, F)


def box(pool, c, h, R=None):
    P = np.array([[sx, sy, sz] for sz in (-1, 1) for sy in (-1, 1) for sx in (-1, 1)], float) * np.asarray(h, float)
    if R is not None:
        P = P @ np.asarray(R).T
    pool.add(P + np.asarray(c, float), [(0, 2, 3, 1), (4, 5, 7, 6), (0, 1, 5, 4), (2, 6, 7, 3), (0, 4, 6, 2), (1, 3, 7, 5)])


def sstep(a, b, x):
    t = np.clip((np.asarray(x, float) - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def angdiff(th, a):
    return np.abs((np.asarray(th) - a + math.pi) % (2 * math.pi) - math.pi)


# ------------------------------------------------------------------------------------------------ the figure
# z = 0 at the top of the figure's own slab. theta: 0 = his right (+x), 90 deg = front (+y).
BODY_Z = (0.40, 0.90, 1.38, 1.50, 1.74, 1.93, 2.00, 2.05)
BODY_A = (0.345, 0.315, 0.275, 0.245, 0.300, 0.325, 0.220, 0.110)        # half width
BODY_BF = (0.280, 0.255, 0.225, 0.200, 0.235, 0.195, 0.150, 0.105)       # depth to the front
BODY_BB = (0.270, 0.245, 0.215, 0.190, 0.210, 0.185, 0.150, 0.105)       # depth to the back
HEM_Z = 0.40
SASH_Z = 1.50


def fold_relief(th, t, folds):
    """Raised cloth overhangs and their offset, narrower grooves. Values are WORKING_VALUE."""
    relief = np.zeros_like(th)
    for angle, drift, width, depth in folds:
        centre = (angle + drift * t) * D2R
        crest = angdiff(th, centre) / (width * D2R)
        groove = angdiff(th, centre + width * 0.90 * D2R) / (width * 0.55 * D2R)
        relief += depth * (np.exp(-crest**2) - 0.60 * np.exp(-groove**2))
    return relief


# Wide, uneven falls in the fold banks visible in Commons 01 and “1762 01”.
ZUPAN_FOLDS = ((39, 22, 11, 0.048), (70, 11, 9, 0.040), (100, -11, 8, 0.061),
               (126, -23, 11, 0.041), (155, -27, 12, 0.031), (226, -10, 15, 0.038),
               (302, 18, 17, 0.036))
DELIA_FOLDS = ((-36, 25, 13, 0.046), (-11, 15, 9, 0.065), (21, 5, 10, 0.054),
               (153, -10, 11, 0.059), (188, -17, 10, 0.047), (219, 8, 11, 0.053),
               (254, -13, 14, 0.043), (285, -11, 11, 0.051))


def body_r(th, z, folds=True):
    z = max(z, HEM_Z)
    a, bf, bb = (np.interp(z, BODY_Z, t) for t in (BODY_A, BODY_BF, BODY_BB))
    c, s = np.cos(th), np.sin(th)
    b = np.where(s >= 0, bf, bb)
    p = 2.5
    r = (np.abs(c / a) ** p + np.abs(s / b) ** p) ** (-1.0 / p)
    if folds and z < SASH_Z - 0.03:
        t = (z - HEM_Z) / (SASH_Z - 0.03 - HEM_Z)
        r += (1 - t) ** 0.73 * fold_relief(th, t, ZUPAN_FOLDS)
    if folds and z > SASH_Z:
        t = sstep(1.55, 1.99, z)
        cloth = ((56, 12, 14, 0.014), (115, 8, 14, 0.011), (145, -8, 17, 0.022))
        r += np.sin(math.pi * t) * fold_relief(th, t, cloth)
    return r


def opening(z):
    """Half angle (rad) of the open front of the delia."""
    return np.interp(z, (0.20, 1.0, 1.5, 1.9, 2.04), (48, 41, 31, 25, 18)) * D2R


def cloak_r_raw(th, z):
    t = np.clip((z - 0.20) / 1.84, 0, 1)
    r = body_r(th, z, folds=False) + 0.050 + 0.055 * (1 - t)
    r += (1 - t) ** 0.65 * fold_relief(th, t, DELIA_FOLDS)
    wing = np.interp(z, (0.20, 0.60, 1.05, 1.50, 1.86, 2.0), (0.42, 0.80, 1.0, 0.50, 0.0, 0.0))
    r = r + 0.40 * wing * np.exp(-(angdiff(th, 14 * D2R) / (30 * D2R)) ** 2)        # thrown back over the right arm
    left = sstep(0.95, 1.20, z) * (1 - sstep(1.62, 1.82, z))
    r = r + 0.085 * left * np.exp(-(angdiff(th, 186 * D2R) / (36 * D2R)) ** 2)      # gathered on the left arm
    if z > 1.93:
        r = r * (1 - 0.55 * sstep(1.93, 2.06, z))
    return r


def cloak_r(th, z):
    g = opening(z)
    m = sstep(g, g + 9 * D2R, angdiff(th, 90 * D2R))
    return m * cloak_r_raw(th, z) + (1 - m) * (body_r(th, z, folds=False) - 0.05)


def edge_point(z, side, lift=0.012):
    th = 90 * D2R + side * (opening(z) + 8 * D2R)
    r = float(cloak_r_raw(np.array([th]), z)[0]) + lift
    return np.array([r * math.cos(th), r * math.sin(th), z])


# pose (z above the slab)
R_SH, R_EL, R_WR, R_FIST = np.array([0.31, 0.0, 1.96]), np.array([0.55, 0.22, 1.91]), np.array([0.76, 0.43, 1.96]), np.array([0.81, 0.48, 1.975])
L_SH, L_EL, L_WR, L_FIST = np.array([-0.31, 0.0, 1.96]), np.array([-0.44, -0.05, 1.58]), np.array([-0.31, 0.17, 1.47]), np.array([-0.275, 0.215, 1.46])
MACE_AXIS = np.array([-0.25, 0.35, 0.90]) / np.linalg.norm([-0.25, 0.35, 0.90])
HEAD_C = np.array([0.025, 0.035, 2.275])
HEAD_R = rot_z(-26 * D2R) @ rot_x(4 * D2R)          # slight lift towards the extended right arm; WORKING_VALUE
FUR_PTS, FUR_W, STRAND_PTS = [], [], []             # sample points (and strength) of fur / hair for the surface detail


def head_p(p):
    return HEAD_C + HEAD_R @ np.asarray(p, float)


def build_figure():
    P = Pool()
    # own slab, slightly irregular
    lathe(P, (-SLAB, -SLAB + 0.02, -0.012, 0.0), lambda th, z: (np.abs(np.cos(th) / 0.60) ** 5 + np.abs(np.sin(th) / 0.52) ** 5) ** -0.2
          * (1 + 0.012 * np.sin(5 * th + 1)) * (0.985 if z > -0.005 else 1.0), n=96)
    # boots and legs
    for sx, fy, yaw in ((-1, 0.10, 14), (1, 0.15, -18)):
        x = sx * 0.185
        ellipsoid(P, (x + sx * 0.02, fy + 0.03, 0.07), (0.085, 0.185, 0.075), rot_z(yaw * D2R))
        tube(P, [(x, fy - 0.07, 0.05), (x, fy - 0.07, 0.36), (x * 0.95, fy - 0.05, 0.66), (x * 0.8, 0.0, 1.10)], [0.088, 0.108, 0.102, 0.135], sides=14)
        tube(P, [(x, fy - 0.07, 0.40), (x, fy - 0.07, 0.45)], [0.118, 0.112], sides=14, smooth=0)       # boot top roll
    # support between the legs (armour heap) and the helmet at his left foot
    ellipsoid(P, (0.0, -0.12, 0.24), (0.21, 0.19, 0.30))
    hc = np.array([-0.335, 0.235, 0.165])
    hR = rot_z(25 * D2R) @ rot_x(-28 * D2R)
    ellipsoid(P, hc, (0.165, 0.195, 0.165), hR)
    ellipsoid(P, hc + hR @ np.array([0, 0.0, -0.035]), (0.185, 0.215, 0.035), hR)                       # rim
    ellipsoid(P, hc + hR @ np.array([0, -0.20, -0.06]), (0.13, 0.10, 0.03), hR @ rot_x(-25 * D2R))        # neck guard
    ellipsoid(P, hc + hR @ np.array([0, 0.0, 0.165]), (0.03, 0.03, 0.04), hR)                           # finial
    # zupan
    zs = np.r_[np.linspace(HEM_Z, 1.38, 22), 1.44, 1.50, np.linspace(1.56, 2.05, 30)]
    lathe(P, zs, body_r, zfun=lambda th, z: np.full(len(th), z) + (0.035 * np.sin(3 * th + 1.2) + 0.02 * np.sin(8 * th) if z <= HEM_Z else 0.0))
    # sash with a buckle, the sabre strap running down to his left hip
    lathe(P, (1.435, 1.452, 1.50, 1.548, 1.565), lambda th, z: body_r(th, z, False) + (0.0 if z in (1.435, 1.565) else 0.024))
    box(P, (0.01, float(body_r(np.array([90 * D2R]), 1.5, False)[0]) + 0.025, 1.50), (0.055, 0.02, 0.05))
    th = np.linspace(0, 2 * math.pi, 40, endpoint=False)
    zz = 1.385 - 0.075 * np.cos(th - 200 * D2R)
    rr = np.array([float(body_r(np.array([t]), z, False)[0]) + 0.02 for t, z in zip(th, zz)])
    tube(P, np.stack([rr * np.cos(th), rr * np.sin(th), zz], 1), 0.03, sides=8, smooth=0, closed=True, flat=((0, 0, 1.0), 1.5))
    # Raised closure along the opening of the zupan (Commons 08); sculpted dimensions are WORKING_VALUE.
    seam = []
    for k in range(6):
        z = 1.61 + 0.055 * k
        y = float(body_r(np.array([90 * D2R]), z, False)[0])
        x = 0.010 - 0.0025 * k
        seam.append((x, y - 0.008, z))
        for side in (-1, 1):
            tube(P, [(x, y + 0.008, z), (x + side * 0.037, y + 0.002, z + side * 0.004),
                     (x + side * 0.060, y - 0.010, z + side * 0.004)],
                 [0.010, 0.012, 0.008], sides=10, smooth=4)
        ellipsoid(P, (x, y + 0.014, z), (0.019, 0.016, 0.017), seg=14, rings=9)
    tube(P, seam, 0.019, sides=12, smooth=3)
    lathe(P, (1.980, 2.018, 2.070, 2.091, 2.100),
          lambda th, z: body_r(th, z, False) * np.interp(z, (1.980, 2.018, 2.091, 2.100), (1.0, 1.0, 1.12, 1.0)),
          n=80)
    # delia: body of the cloak, fur edges, collar
    zs = np.r_[np.linspace(0.20, 1.74, 28), np.linspace(1.77, 2.06, 24)]
    lathe(P, zs, cloak_r, n=180, zfun=lambda th, z: np.full(len(th), z) + (0.05 * np.sin(2 * th + 0.4) + 0.025 * np.sin(7 * th) if z <= 0.20 else 0.0))
    for side in (-1, 1):
        path = [edge_point(z, side) for z in np.linspace(0.24, 1.98, 26)]
        tube(P, path, np.interp(np.linspace(0, 1, 26), (0, 0.5, 0.85, 1), (0.072, 0.066, 0.058, 0.048)), sides=16, smooth=3)
        FUR_PTS.extend(smooth_path(path, 4))
        FUR_W.extend([1.0] * (len(FUR_PTS) - len(FUR_W)))
    # The delia rolls over the shoulders and opens over the standing collar.
    th = np.linspace(118 * D2R, 420 * D2R, 50)
    collar = np.stack([0.194 * np.cos(th), -0.015 + 0.171 * np.sin(th),
                       2.027 - 0.031 * np.sin(th) + 0.008 * np.cos(th)], 1)
    tube(P, collar, 0.050, sides=16, smooth=0, flat=((0, 0, 1), 0.79))
    FUR_PTS.extend(collar)
    FUR_W.extend([1.0] * (len(FUR_PTS) - len(FUR_W)))
    # fur lining shown on the turned-back wing (his right) - only sample points, the surface is the cloak
    for z in np.linspace(0.45, 1.70, 14):
        for a in np.linspace(-8, 52, 9):
            t = a * D2R
            r = float(cloak_r_raw(np.array([t]), z)[0])
            FUR_PTS.append(np.array([r * math.cos(t), r * math.sin(t), z]))
            FUR_W.append(0.55)
    # right arm: wide sleeve to the elbow with a fur cuff, vambrace, gauntlet round the mace
    ellipsoid(P, R_SH + (-0.020, 0.013, -0.023), (0.174, 0.154, 0.128), rot_z(26 * D2R), seg=32, rings=22)
    tube(P, [R_SH + (0, 0, -0.02), (R_SH + R_EL) / 2 + (0, 0, 0.01), R_EL], [0.125, 0.125, 0.135], sides=16, smooth=4)
    d = (R_EL - R_SH) / np.linalg.norm(R_EL - R_SH)
    cuff_c = R_EL + d * 0.01
    u = np.cross(d, [0, 0, 1.0]); u /= np.linalg.norm(u); w = np.cross(d, u)
    ring = [cuff_c + (u * math.cos(t) + w * math.sin(t)) * 0.125 for t in np.linspace(0, 2 * math.pi, 16, endpoint=False)]
    tube(P, ring, 0.062, sides=10, smooth=0, closed=True)
    FUR_PTS.extend(ring)
    FUR_W.extend([1.0] * (len(FUR_PTS) - len(FUR_W)))
    # sleeve mouth hanging below the cuff
    ellipsoid(P, R_EL + (-0.03, -0.03, -0.11), (0.10, 0.12, 0.13), rot_x(18 * D2R))
    tube(P, [R_EL, (R_EL + R_WR) / 2, R_WR], [0.068, 0.062, 0.052], sides=12, smooth=3)
    d = R_WR - R_EL
    u = np.cross(d, [0, 0, 1.0]); u /= np.linalg.norm(u)
    w = np.cross(d / np.linalg.norm(d), u)
    for t, radius in ((0.44, 0.066), (0.88, 0.056)):
        ring = [R_EL + d * t + (u * math.cos(a) + w * math.sin(a)) * radius
                for a in np.linspace(0, 2 * math.pi, 24, endpoint=False)]
        tube(P, ring, 0.011, sides=10, smooth=0, closed=True)
    ellipsoid(P, R_FIST, (0.063, 0.063, 0.075), rot_z(20 * D2R))
    for z, radius in ((-0.046, 0.016), (-0.019, 0.019), (0.010, 0.019), (0.039, 0.018)):
        fingers = R_FIST + (0, 0, z)
        tube(P, [fingers + (-0.034, 0.034, 0), fingers + (0.014, 0.060, 0), fingers + (0.050, 0.032, 0)],
             radius, sides=10, smooth=4)
    ellipsoid(P, R_WR + (0.0, 0.0, 0.0), (0.066, 0.066, 0.05), seg=12, rings=8)                         # gauntlet cuff
    # left arm: sleeve, fur cuff on the forearm, hand on the sabre hilt
    ellipsoid(P, L_SH + (0.027, -0.007, -0.063), (0.153, 0.154, 0.153), rot_y(-22 * D2R), seg=32, rings=22)
    tube(P, [L_SH + (0, 0, -0.02), (L_SH + L_EL) / 2 + (-0.02, -0.01, 0), L_EL, (L_EL + L_WR) / 2 + (-0.01, 0, -0.02), L_WR], [0.125, 0.125, 0.130, 0.120, 0.10], sides=16, smooth=4)
    d = (L_WR - L_EL) / np.linalg.norm(L_WR - L_EL)
    cuff_c = L_EL + d * 0.20
    u = np.cross(d, [0, 0, 1.0]); u /= np.linalg.norm(u); w = np.cross(d, u)
    ring = [cuff_c + (u * math.cos(t) + w * math.sin(t)) * 0.115 for t in np.linspace(0, 2 * math.pi, 16, endpoint=False)]
    tube(P, ring, 0.066, sides=10, smooth=0, closed=True)
    FUR_PTS.extend(ring)
    FUR_W.extend([1.0] * (len(FUR_PTS) - len(FUR_W)))
    ellipsoid(P, L_FIST, (0.062, 0.07, 0.065), rot_z(-30 * D2R))
    # sabre: grip and guard under the hand, curved scabbard down his left side
    tube(P, [L_FIST + (0.03, 0.06, 0.07), L_FIST, L_FIST + (-0.02, -0.03, -0.06)], 0.026, sides=8, smooth=3)
    box(P, L_FIST + (-0.02, -0.03, -0.075), (0.02, 0.085, 0.016), rot_z(-25 * D2R))
    tube(P, [L_FIST + (-0.025, -0.04, -0.08), (-0.385, 0.03, 1.08), (-0.425, -0.10, 0.80), (-0.43, -0.25, 0.58)], [0.04, 0.04, 0.036, 0.026], sides=10, smooth=5,
         flat=((1.0, 0, 0), 0.55))
    ob = P.obj("figure_src")
    ob.location = (0, 0, ZF + SLAB)
    return ob


def carve_face(vertices):
    """Relief on the front of the stone head. All profile dimensions are WORKING_VALUE."""
    x, y, z = vertices.T
    x *= 0.85 + 0.15 * sstep(-0.13, 0.03, z)
    front = sstep(0.030, 0.085, y)
    depth = 0.040 * np.exp(-((x + 0.002) / 0.020)**2 - ((z + 0.008) / 0.049)**2)
    depth += 0.032 * np.exp(-((x + 0.003) / 0.024)**2 - ((z + 0.039) / 0.017)**2)
    for side in (-1, 1):
        u = side * x
        eye_x = (u - 0.045) / 0.029
        eye_z = z - (0.008 + 0.08 * (u - 0.045) + side * 0.002)
        arch = np.clip(1 - eye_x**2, 0, 1)
        eye_falloff = 1 - sstep(0.74, 1.04, np.abs(eye_x))
        upper = eye_z - (0.003 + 0.010 * arch)
        lower = eye_z - (0.003 - 0.009 * arch)
        # A broad orbital plane, closed at the corners by both lids. The globe is plain stone.
        depth -= 0.007 * np.exp(-0.65 * eye_x**2 - (eye_z / 0.024)**2)
        depth += 0.018 * eye_falloff * np.exp(-(eye_x / 0.93)**2 - ((eye_z - 0.002) / 0.011)**2)
        depth += 0.015 * eye_falloff * np.exp(-(upper / 0.0055)**2)
        depth += 0.012 * eye_falloff * np.exp(-(lower / 0.0055)**2)
        depth -= 0.006 * eye_falloff * np.exp(-((upper - 0.009) / 0.0045)**2)
        brow_z = eye_z - (0.029 + 0.007 * arch)
        depth += 0.020 * np.exp(-(eye_x / 1.28)**2 - (brow_z / 0.014)**2)
        depth += 0.018 * np.exp(-((u - 0.065) / 0.025)**2 - ((z + 0.028) / 0.025)**2)
        depth += 0.016 * np.exp(-((u - 0.021) / 0.013)**2 - ((z + 0.045) / 0.011)**2)
        depth -= 0.010 * np.exp(-((u - 0.020) / 0.008)**2 - ((z + 0.053) / 0.005)**2)
        depth -= 0.006 * np.exp(-((u - 0.038 + 0.32 * (z + 0.057)) / 0.010)**2 - ((z + 0.068) / 0.019)**2)

        # A continuous sweep on each side of the philtrum, tapering against the cheek.
        t = np.clip((u - 0.005) / 0.077, 0, 1)
        centre = -0.061 - (0.043 + side * 0.004) * t**1.55
        across = (z - centre) / (0.023 - 0.015 * t)
        whisker = sstep(0.001, 0.019, u) * (1 - sstep(0.058, 0.082, u))
        relief = 0.038 * np.exp(-across**2)
        for groove in (-0.46, 0.32):
            relief -= 0.0045 * np.exp(-((across - groove) / 0.22)**2)
        depth += whisker * relief
    depth -= 0.008 * np.exp(-(x / 0.038)**4 - ((z + 0.087 + 0.07 * x) / 0.006)**2)
    depth += 0.006 * np.exp(-(x / 0.037)**4 - ((z + 0.098) / 0.009)**2)
    y += front * depth


def carve_beard(vertices):
    """Slightly cleft, compact chin beard with incised, diverging locks."""
    x, y, z = vertices.T
    chin = sstep(-0.045, 0.064, -z)
    x *= 1 - 0.32 * chin
    cleft = np.exp(-(x / 0.019)**2) * chin
    z += 0.015 * cleft + 0.07 * x
    front = sstep(-0.008, 0.033, y)
    across = x - 1.8 * x * z + 0.11 * z + 1.9 * z**2
    channels = (0.5 + 0.5 * np.cos(2 * math.pi * (across + 0.002) / 0.023))**4
    y -= front * (0.009 * cleft + (0.004 + 0.003 * chin) * channels)


def build_head():
    """Keep the uncovered forehead and receding temples seen in Commons 01 and “1762 01”."""
    P = Pool()
    tube(P, [(0.0, -0.01, 1.98), HEAD_C + (0, -0.02, -0.08)], [0.085, 0.075], sides=12, smooth=0)
    ellipsoid(P, HEAD_C, (0.110, 0.129, 0.153), HEAD_R, seg=192, rings=112, deform=carve_face)
    ellipsoid(P, head_p((0, -0.034, 0.002)), (0.119, 0.116, 0.128), HEAD_R, seg=48, rings=32)
    for sx in (-1, 1):
        ellipsoid(P, head_p((sx * 0.106, 0.010, -0.015)), (0.016, 0.024, 0.035), HEAD_R, seg=20, rings=14)
        ellipsoid(P, head_p((sx * 0.074, 0.037, -0.099)), (0.027, 0.035, 0.048), HEAD_R @ rot_y(-sx * 18 * D2R))
    ellipsoid(P, head_p((0, 0.074, -0.151)), (0.086, 0.062, 0.092), HEAD_R @ rot_x(-18 * D2R),
              seg=120, rings=64, deform=carve_beard)
    for c, r in (((0, -0.036, 0.003), (0.132, 0.131, 0.141)),
                 ((0.087, 0.011, -0.039), (0.045, 0.067, 0.087)),
                 ((-0.087, 0.011, -0.039), (0.047, 0.066, 0.086))):
        STRAND_PTS.append((np.asarray(c, float), np.asarray(r, float)))
    ob = P.obj("head_src")
    ob.location = (0, 0, ZF + SLAB)
    return ob


def build_cartouches():
    """Blank baroque cartouche hanging over the cornice on each face: shield, scrolls, crown (heraldry omitted)."""
    P = Pool()
    h = HS["cornice"]
    for k in range(4):
        R = rot_z(k * math.pi / 2)

        def q(p):
            return R @ np.asarray(p, float)
        c = np.array([0.0, h + 0.015, ZF - 0.20])
        ellipsoid(P, q(c), (0.20, 0.075, 0.235), R)
        ellipsoid(P, q(c + (0, 0.035, -0.01)), (0.135, 0.06, 0.165), R)                                  # boss of the shield
        ellipsoid(P, q(c + (0, 0.0, -0.27)), (0.09, 0.05, 0.075), R)                                      # drop below
        th = np.linspace(0, 2 * math.pi, 22, endpoint=False)
        frame = [q(c + (0.205 * math.cos(t) * (1 + 0.10 * math.cos(2 * t)), 0.02, 0.245 * math.sin(t) - 0.01)) for t in th]
        tube(P, frame, 0.036, sides=8, smooth=0, closed=True)                                            # rolled frame
        for sx in (-1, 1):
            ellipsoid(P, q(c + (sx * 0.20, 0.03, 0.15)), (0.062, 0.05, 0.062), R, seg=12, rings=8)       # volutes at the shoulders
            ellipsoid(P, q(c + (sx * 0.17, 0.03, -0.17)), (0.05, 0.045, 0.05), R, seg=12, rings=8)
        # crown: band and five knobs, sitting on the cornice edge
        ellipsoid(P, q(c + (0, 0.0, 0.215)), (0.125, 0.07, 0.04), R)
        for i in range(5):
            x = -0.10 + 0.05 * i
            ellipsoid(P, q(c + (x, 0.0, 0.265 + 0.02 * (1 - abs(i - 2) / 2))), (0.026, 0.03, 0.036), R, seg=10, rings=6)
    return P.obj("cartouche_src")


def remesh(ob, voxel=VOXEL, passes=3):
    bpy.ops.object.select_all(action="DESELECT")
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    ob.data.remesh_voxel_size = voxel
    ob.data.remesh_voxel_adaptivity = 0.0
    bpy.ops.object.voxel_remesh()
    m = ob.modifiers.new("smooth", "SMOOTH")
    m.factor, m.iterations = 0.5, passes
    bpy.ops.object.modifier_apply(modifier="smooth")


def smooth_shoulders(ob):
    """Blend the shoulder seams after the voxel union, with a fade towards sash and cuffs."""
    weights = ob.vertex_groups.new(name="Shoulders and upper delia")
    co = np.empty(len(ob.data.vertices) * 3, dtype=np.float32)
    ob.data.vertices.foreach_get("co", co)
    x, _, z = co.reshape(-1, 3).T
    z -= ZF + SLAB
    strength = sstep(1.70, 1.88, z) * (1 - sstep(0.41, 0.52, np.abs(x)))
    for i in np.flatnonzero(strength > 0):
        weights.add([int(i)], float(strength[i]), "REPLACE")
    modifier = ob.modifiers.new("Blend carved shoulders", "SMOOTH")
    modifier.vertex_group = weights.name
    modifier.factor, modifier.iterations = 0.65, 18
    bpy.ops.object.modifier_apply(modifier=modifier.name)


def detail_figure(ob):
    """Fur and hair curls displaced along the surface normal."""
    me = ob.data
    n = len(me.vertices)
    co = np.empty(n * 3)
    me.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)
    no = np.empty(n * 3)
    me.vertices.foreach_get("normal", no)
    no = no.reshape(-1, 3)
    base = np.array([0, 0, ZF + SLAB])
    kd = KDTree(len(FUR_PTS))
    for i, p in enumerate(FUR_PTS):
        kd.insert(Vector(p + base), i)
    kd.balance()
    loc = (co - base - HEAD_C) @ HEAD_R                        # head-local coordinates
    strand = np.zeros(n)
    for c, r in STRAND_PTS:
        dd = np.linalg.norm((loc - c) / (r * 1.10), axis=1)
        strand = np.maximum(strand, 1 - sstep(0.80, 1.0, dd))
    strand *= (1 - sstep(0.045, 0.084, loc[:, 1])) * sstep(-0.145, -0.098, loc[:, 2])
    cand = np.nonzero((co[:, 2] > ZF + SLAB + 0.15))[0]
    disp = np.zeros(n)
    curl_dir = np.array([0.45, 0.25, 0.86])
    for i in cand:
        p = co[i]
        if strand[i] > 0.01:
            v = Vector(p * 9.0)
            ph = 2.6 * noise.noise(v)
            disp[i] += strand[i] * 0.0048 * math.sin(2 * math.pi * (loc[i, 0] + 0.35 * loc[i, 1]) / 0.040 + ph + 6.0 * loc[i, 2])
            continue
        _, idx, dist = kd.find(Vector(p))
        if dist < 0.105:
            wgt = (1.0 - float(sstep(0.062, 0.105, dist))) * FUR_W[idx]
            # wavy locks: a stripe pattern whose phase is warped by two octaves of noise, plus fine tufts
            ph = 5.0 * noise.noise(Vector(p * 6.0)) + 2.0 * noise.noise(Vector(p * 15.0 + Vector((3.1, 0.7, 5.2))))
            s = math.sin(2 * math.pi * float(np.dot(p, curl_dir)) / 0.085 + ph)
            shoulder = float(sstep(1.72, 1.93, p[2] - base[2]) * (1 - sstep(0.37, 0.50, abs(p[0]))))
            disp[i] += (1 - 0.50 * shoulder) * wgt * (0.0085 * s + 0.0045 * noise.noise(Vector(p * 21.0)))
    co2 = co + no * disp[:, None]
    me.vertices.foreach_set("co", co2.ravel())
    me.update()


def tri_count(ob):
    me = ob.data
    return int(sum(len(p.vertices) - 2 for p in me.polygons))


def decimated(ob, target, name):
    """Copy of the object collapsed to about `target` triangles."""
    new = ob.copy()
    new.data = ob.data.copy()
    new.name = name
    bpy.context.scene.collection.objects.link(new)
    bpy.ops.object.select_all(action="DESELECT")
    new.select_set(True)
    bpy.context.view_layer.objects.active = new
    m = new.modifiers.new("tri", "TRIANGULATE")
    bpy.ops.object.modifier_apply(modifier="tri")
    m = new.modifiers.new("dec", "DECIMATE")
    m.ratio = min(1.0, target / max(tri_count(new), 1))
    bpy.ops.object.modifier_apply(modifier="dec")
    return new


def mesh_arrays(ob):
    me = ob.data
    me.calc_loop_triangles()
    V = np.empty(len(me.vertices) * 3)
    me.vertices.foreach_get("co", V)
    T = np.empty(len(me.loop_triangles) * 3, np.int64)
    me.loop_triangles.foreach_get("vertices", T)
    return V.reshape(-1, 3), T.reshape(-1, 3)


# ------------------------------------------------------------------------------------------------ architecture
def profile(low=False):
    """Outline of the square monument from the paving up: list of (material, class, sharp-split segments of (z, half))."""
    st = HS["steps"]
    pz, sz, bt, bn, vb, vt, ct = (HZ[k] for k in ("platform_top", "steps_top", "block_top", "band_top", "vase_bottom", "vase_top", "cornice_top"))
    hp, hb = HS["platform"], HS["block"]
    cap = 0.12
    segs = [(SETT, "platform", [(-0.25, hp - 0.04), (pz - cap, hp - 0.04)]),
            (STONE, "cap", [(pz - cap, hp - 0.04), (pz - cap, hp)]), (STONE, "cap", [(pz - cap, hp), (pz, hp)]),
            (STONE, "cap", [(pz, hp), (pz, st[0])])]
    n = len(st)
    rise = (sz - pz) / n
    for i in range(n):
        z0, z1 = pz + rise * i, pz + rise * (i + 1)
        nxt = st[i + 1] if i + 1 < n else hb + 0.06
        segs += [(STONE, "step", [(z0, st[i]), (z1, st[i])]), (STONE, "step", [(z1, st[i]), (z1, nxt)])]
    # block: plinth course, shaft, top band (inscribed course) set back, torus under the vase
    segs += [(STONE, "block", [(sz, hb + 0.06), (sz + 0.15, hb + 0.06)]), (STONE, "block", [(sz + 0.15, hb + 0.06), (sz + 0.19, hb)]),
             (STONE, "block", [(sz + 0.19, hb), (bt, hb)]), (STONE, "block", [(bt, hb), (bt, hb + 0.035)]),
             (STONE, "block", [(bt, hb + 0.035), (bt + 0.05, hb + 0.035)]), (STONE, "band", [(bt + 0.05, hb + 0.035), (bt + 0.05, hb - 0.03)]),
             (STONE, "band", [(bt + 0.05, hb - 0.03), (bn, hb - 0.03)])]
    torus = [(bn + (vb - bn) * (0.5 - 0.5 * math.cos(t)), hb - 0.03 + 0.04 * math.sin(t) - 0.07 * (t / math.pi)) for t in np.linspace(0, math.pi, 3 if low else 7)]
    segs.append((STONE, "band", torus))
    hv = vt - vb
    # waisted vase: z fraction, half size (belly at 0.22 of the height; neck 0.64 of the belly - Commons 05 / 01)
    bel, nk = HS["vase_belly"], HS["vase_neck"]
    V0 = [(0.00, hb - 0.10), (0.04, bel - 0.10), (0.11, bel - 0.02), (0.22, bel), (0.33, bel - 0.035), (0.46, bel - 0.15),
          (0.58, nk + 0.07), (0.70, nk + 0.015), (0.82, nk), (1.00, nk)]
    if low:
        V0 = [V0[i] for i in (0, 1, 3, 5, 7, 9)]
    else:
        zf = np.linspace(0, 1, 24)
        V0 = list(zip(zf, np.interp(zf, [p[0] for p in V0], [p[1] for p in V0])))
        V0 = [(a, b) for a, b in V0]
    segs.append((STONE, "vase", [(vb + f * hv, h) for f, h in V0]))
    ch = HS["cornice"]
    hc = ct - vt
    segs += [(STONE, "cornice", [(vt, nk), (vt, nk + 0.03)]), (STONE, "cornice", [(vt, nk + 0.03), (vt + 0.10 * hc, nk + 0.03)]),
             (STONE, "cornice", [(vt + 0.10 * hc, nk + 0.03), (vt + 0.22 * hc, nk + 0.05), (vt + 0.42 * hc, nk + 0.10), (vt + 0.55 * hc, ch - 0.035)]),
             (STONE, "cornice", [(vt + 0.55 * hc, ch - 0.035), (vt + 0.55 * hc, ch)]), (STONE, "cornice", [(vt + 0.55 * hc, ch), (vt + 0.78 * hc, ch)]),
             (STONE, "cornice", [(vt + 0.78 * hc, ch), (vt + 0.90 * hc, ch - 0.04), (ct, ch - 0.055)]),
             (STONE, "cornice", [(ct, ch - 0.055), (ct, 0.0)])]
    return segs


def refine(seg, step):
    out = [seg[0]]
    for a, b in zip(seg, seg[1:]):
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        k = max(1, int(math.ceil(L / step)))
        out += [(a[0] + (b[0] - a[0]) * i / k, a[1] + (b[1] - a[1]) * i / k) for i in range(1, k + 1)]
    return out


def build_architecture(low=False):
    """Per material: V, UV, T, cls (class id per vertex) - four sides swept along the profile, split at sharp edges."""
    out = {}
    vb, vt = HZ["vase_bottom"], HZ["vase_top"]
    p_lo, p_hi = vb + 0.30, vt - 0.13
    s_base = np.linspace(-1, 1, 5 if low else 15)
    for mat, cls, seg in profile(low):
        seg = seg if low else refine(seg, 0.085 if cls in ("vase", "block", "band") else 0.16)
        if cls == "vase" and not low:
            zs = [p[0] for p in seg]
            hs = [p[1] for p in seg]
            zz = np.unique(np.round(np.r_[zs, p_lo, p_lo + 0.035, p_hi - 0.035, p_hi], 4))
            seg = [(z, float(np.interp(z, zs, hs))) for z in zz]
        d = out.setdefault(mat, {"V": [], "UV": [], "T": [], "cls": [], "n": 0})
        for k in range(4):
            # Rear face: shared corner heights and silhouette, fewer columns for the vertex bake.
            s_vals = np.linspace(-1, 1, 9) if not low and k == 2 else s_base
            if cls == "vase" and not low:
                s_vals = np.unique(np.round(np.r_[s_vals, -0.845, -0.795, 0.795, 0.845], 4))
            if cls == "cornice" and seg[-1][1] == 0.0:
                s_vals = np.array([-1.0, 1.0])
            nrm = np.array([math.cos(math.pi / 2 * (k + 1)), math.sin(math.pi / 2 * (k + 1)), 0.0])     # k = 0: front (+y)
            tan = np.cross([0, 0, 1.0], nrm)
            ns, nz = len(s_vals), len(seg)
            base = d["n"]
            for j, (z, h) in enumerate(seg):
                for s in s_vals:
                    inset = 0.0
                    if cls == "vase" and not low:
                        inset = 0.022 * float(sstep(0.845, 0.795, abs(s))) * float(sstep(p_lo, p_lo + 0.035, z)) * float(1 - sstep(p_hi - 0.035, p_hi, z))
                    d["V"].append(nrm * (h - inset) + tan * s * h + np.array([0, 0, z]))
                    horizontal = abs(seg[min(j + 1, nz - 1)][0] - seg[max(j - 1, 0)][0]) < 1e-6
                    d["UV"].append((s * h + 3.37 * k, h if horizontal else z))
                    d["cls"].append(cls)
            for j in range(nz - 1):
                for i in range(ns - 1):
                    a = base + j * ns + i
                    d["T"] += [(a, a + 1, a + ns + 1), (a, a + ns + 1, a + ns)]
            d["n"] += ns * nz
    if not low:
        inscription_frame(out.setdefault(STONE, {"V": [], "UV": [], "T": [], "cls": [], "n": 0}))
    return {m: {"V": np.array(d["V"]), "UV": np.array(d["UV"]), "T": np.array(d["T"], np.int64), "cls": np.array(d["cls"])} for m, d in out.items()}


# plaza-barn-fix-s24 (critic s24 day 27): the front of the block read as a blank new slab. The block carries an
# inscription panel on the photos, but no legible source of its text exists here: a smooth field framed by a raised
# moulding (no invented lettering). Frame on the front face (+y), field centred on the block shaft; sizes WORKING_VALUE.
FRAME = {"cz": None, "hw": 0.60, "hh": 0.36, "bar": 0.055, "proud": 0.018}


def inscription_frame(d):
    """Four raised bars (5 faces each, back face against the block omitted) - 40 triangles, LOD0 only."""
    sz, bt, hb = HZ["steps_top"], HZ["block_top"], HS["block"]
    cz = FRAME["cz"] or 0.5 * ((sz + 0.19) + bt) + 0.04
    hw, hh, b, pr = FRAME["hw"], FRAME["hh"], FRAME["bar"], FRAME["proud"]
    bars = [((0.0, cz + hh - b / 2), (hw, b / 2)), ((0.0, cz - hh + b / 2), (hw, b / 2)),
            ((-hw + b / 2, cz), (b / 2, hh - b)), ((hw - b / 2, cz), (b / 2, hh - b))]
    for (x, z), (ax, az) in bars:
        y0, y1 = hb, hb + pr
        P = [np.array([x + sx * ax, y, z + sz_ * az]) for y in (y0, y1) for sz_ in (-1, 1) for sx in (-1, 1)]
        # faces CCW seen from outside: front (+y), top, bottom, left, right
        quads = [(6, 7, 5, 4), (2, 3, 7, 6), (4, 5, 1, 0), (2, 6, 4, 0), (7, 3, 1, 5)]
        for q in quads:
            base = d["n"]
            for i in q:
                d["V"].append(P[i])
                d["UV"].append((P[i][0], P[i][2]))
                d["cls"].append("frame")
            d["T"] += [(base, base + 1, base + 2), (base, base + 2, base + 3)]
            d["n"] += 4


def build_mace(low=False):
    """Gilt buława with a ring joint across the head, visible in Commons “1762 01”."""
    L, hd = DIMS["figure"]["mace_length_m"], DIMS["figure"]["mace_head_diameter_m"] / 2
    o = R_FIST + np.array([0, 0, ZF + SLAB]) - MACE_AXIS * 0.20
    neck = L - 2 * hd
    prof = [(0.0, 0.0), (0.0, 0.030), (0.025, 0.036), (0.052, 0.025),
            (neck - 0.060, 0.024), (neck - 0.042, 0.034), (neck - 0.008, 0.031)]
    sections = ((0.12, 0.41, 0.71, 1.0) if low else
                (0.12, 0.22, 0.33, 0.44, 0.485, 0.50, 0.515, 0.57, 0.68, 0.79, 0.90, 1.0))
    for t in sections:
        a = math.pi * t
        radius = hd * math.sin(a) - (0.0045 if not low and t == 0.50 else 0.0)
        prof.append((L - hd - hd * math.cos(a), radius))
    sides = 6 if low else 14
    u = np.cross(MACE_AXIS, [0, 0, 1.0]); u /= np.linalg.norm(u); w = np.cross(MACE_AXIS, u)
    V, T = [], []
    for s, r in prof:
        for j in range(sides):
            th = 2 * math.pi * j / sides
            V.append(o + MACE_AXIS * s + (u * math.cos(th) + w * math.sin(th)) * r)
    for i in range(len(prof) - 1):
        for j in range(sides):
            a, b = i * sides + j, i * sides + (j + 1) % sides
            T += [(a, b, b + sides), (a, b + sides, a + sides)]
    V = np.array(V)
    return {"V": V, "UV": V[:, :2].copy(), "T": np.array(T, np.int64)}


# ------------------------------------------------------------------------------------------------ bake
def hemi_dirs(n, seed):
    r = np.random.default_rng(seed)
    u, v = r.random(n), r.random(n)
    rad, ph = np.sqrt(u), 2 * math.pi * v
    return np.stack([rad * np.cos(ph), rad * np.sin(ph), np.sqrt(1 - u)], 1)        # cosine weighted, +z


def vertex_normals(V, T):
    n = np.zeros_like(V)
    fn = np.cross(V[T[:, 1]] - V[T[:, 0]], V[T[:, 2]] - V[T[:, 0]])
    for k in range(3):
        np.add.at(n, T[:, k], fn)
    ln = np.linalg.norm(n, axis=1, keepdims=True)
    n = np.where(ln > 1e-12, n / np.maximum(ln, 1e-12), [0.0, 0.0, 1.0])
    return n


def occlusion(bvh, V, N, dirs, maxd):
    """Unoccluded share of the cosine-weighted hemisphere within maxd (1 = open)."""
    out = np.empty(len(V))
    for i in range(len(V)):
        n = N[i]
        t = np.cross(n, [0.0, 0.0, 1.0] if abs(n[2]) < 0.9 else [1.0, 0.0, 0.0])
        t /= np.linalg.norm(t)
        b = np.cross(n, t)
        o = Vector(V[i] + n * 0.004)
        hit = 0
        for d in dirs:
            w = t * d[0] + b * d[1] + n * d[2]
            if bvh.ray_cast(o, Vector(w), maxd)[0] is not None:
                hit += 1
        out[i] = 1.0 - hit / len(dirs)
    return out


def surface_curvature(bvh, vertices, normals, radius=0.023):
    """Signed normal change at a fixed footprint on the source sculpt. Convex is positive."""
    values = np.zeros(len(vertices))
    for i, (vertex, normal) in enumerate(zip(vertices, normals)):
        p, n, _, _ = bvh.find_nearest(Vector(vertex), radius)
        if p is None or n.dot(Vector(normal)) < 0.5:
            continue
        axis = Vector((0, 0, 1)) if abs(n.z) < 0.9 else Vector((1, 0, 0))
        u = n.cross(axis).normalized()
        v = n.cross(u)
        samples = []
        for tangent in (u, -u, v, -v):
            q, nq, _, _ = bvh.find_nearest(p + radius * tangent, radius)
            if q is not None and n.dot(nq) > 0.35:
                samples.append((nq - n).dot(tangent))
        if samples:
            values[i] = np.mean(samples)
    return values


def bronze_colors(bvh, vertices, normals, ao, cavity):
    curvature = surface_curvature(bvh, vertices, normals)
    concave = sstep(0.02, 0.25, -curvature)
    convex = sstep(0.22, 0.65, curvature)
    # Gravity-aligned streaks follow the outside of the gauntlet. Curvature and short AO
    # put the strongest green in finger cuts and below the raised seams.
    phase = 112 * vertices[:, 0] - 138 * vertices[:, 1]
    streak = (0.5 + 0.5 * np.sin(phase + 0.6 * np.sin(0.37 * phase))) ** 5
    runoff = streak * (0.35 + 0.65 * np.maximum(-normals[:, 2], 0))
    patina = np.clip(0.59 + 0.63 * (1 - cavity) + 0.24 * concave + 0.16 * runoff - 0.30 * convex, 0, 1)
    wear = (0.13 + 0.65 * convex) * cavity * (1 - 0.45 * runoff)
    return np.stack([patina, wear, ao, np.ones(len(vertices))], axis=1)


def shelter(bvh, V, N, maxd=6.0):
    """Share of the sky cone (within ~35 deg of the zenith) hidden from the vertex: 1 = never rained on."""
    r = np.random.default_rng(5)
    dirs = []
    while len(dirs) < 14:
        d = r.normal(size=3)
        d[2] = abs(d[2]) + 1.4
        dirs.append(d / np.linalg.norm(d))
    out = np.empty(len(V))
    for i in range(len(V)):
        o = Vector(V[i] + N[i] * 0.006 + np.array([0, 0, 0.002]))
        out[i] = sum(1 for d in dirs if bvh.ray_cast(o, Vector(d), maxd)[0] is not None) / len(dirs)
    return out


STREAKS = None


def streak_field(V, N, cls):
    """Run-off stains below the ledges of the architecture: dark tails under the cornice, the band and the block top."""
    global STREAKS
    if STREAKS is None:
        r = np.random.default_rng(62)
        STREAKS = []
        for z_top, half, length, count in ((HZ["vase_top"] - 0.02, HS["vase_neck"], 1.5, 26), (HZ["block_top"], HS["block"], 1.1, 30),
                                           (HZ["vase_bottom"] + 0.35, HS["vase_belly"], 0.55, 18), (HZ["steps_top"] + 0.19, HS["block"], 0.5, 10)):
            for _ in range(count):
                STREAKS.append((int(r.integers(0, 4)), float(r.uniform(-1, 1)), z_top, float(r.uniform(0.35, 1.0)) * length,
                                float(r.uniform(0.035, 0.11)), float(r.uniform(0.35, 1.0))))
    out = np.zeros(len(V))
    side = (np.round(np.arctan2(N[:, 1], N[:, 0]) / (math.pi / 2)).astype(int) - 1) % 4
    for i in range(len(V)):
        if cls[i] not in ("vase", "block", "band") or abs(N[i, 2]) > 0.75:
            continue
        k = side[i]
        tan = np.array([-math.sin(math.pi / 2 * (k + 1)), math.cos(math.pi / 2 * (k + 1))])
        u = float(V[i, 0] * tan[0] + V[i, 1] * tan[1])
        acc = 0.0
        for sk, s0, zt, ln, sig, amp in STREAKS:
            if sk != k:
                continue
            dz = zt - V[i, 2]
            if dz < -0.02 or dz > ln:
                continue
            half = np.interp(zt, (HZ["block_top"], HZ["vase_top"]), (HS["block"], HS["vase_neck"]))
            du = u - s0 * half * 0.92
            acc += amp * math.exp(-(du / sig) ** 2) * (1 - dz / ln) ** 1.3 * min(1.0, (dz + 0.02) / 0.06)
        out[i] = min(acc, 1.0)
    return out


def weather_colors(bvh, V, N, cls):
    """COLOR_0 of the sandstone: rgb = tint / 2 (shader: albedo *= 2 * rgb), a = 1."""
    ao = occlusion(bvh, V, N, hemi_dirs(40, 1), 1.2)
    cav = occlusion(bvh, V, N, hemi_dirs(20, 2), 0.07)
    sh = shelter(bvh, V, N)
    streak = streak_field(V, N, cls)
    # the carved fur holds soot and algae (Commons "1762 01": fur bands and lining clearly darker than the zupan)
    kd = KDTree(len(FUR_PTS))
    for k, q in enumerate(FUR_PTS):
        kd.insert(Vector(q + np.array([0, 0, ZF + SLAB])), k)
    kd.balance()
    col = np.empty((len(V), 4))
    fresh = np.isin(cls, ("block", "step", "cap", "frame"))   # the lower parts were renewed: paler, cleaner stone
    for i in range(len(V)):
        p, n = V[i], N[i]
        v = Vector(p)
        blot = 0.5 + 0.5 * noise.noise(v * 2.3)               # metre-scale tone drift
        fine = 0.5 + 0.5 * noise.noise(v * 11.0 + Vector((7, 3, 1)))
        up = max(n[2], 0.0)
        down = max(-n[2], 0.0)
        # black crust: in creases and where the rain never washes the stone; rain-washed fronts stay pale
        crust = 0.85 * (1 - cav[i]) ** 1.1 + 0.50 * sh[i] * (0.35 + 0.65 * down) + 0.42 * (1 - ao[i]) ** 1.5
        crust = 1.05 * crust * (0.75 + 0.5 * blot)
        # dirt lies on ledges and shoulders that the rain does not rinse clean
        crust += 0.20 * up * (0.4 + 0.6 * fine) * (0.3 + 0.7 * sh[i])
        if fresh[i]:
            # plaza-barn-fix-s24 (critic s24 day 27 "cokol za czysty"): the renewed plinth has weathered too - less
            # cleaning (0.45 -> 0.72), the run-off tails from the band are NOT reduced, and the lower part carries a
            # darker film: splash soil and algae over the treads and risers and up the foot of the block (Commons 01 / 08:
            # grey-green bloom on the lowest course, dark tails under the band). WORKING_VALUE.
            crust *= 0.72
            z = float(p[2])
            sz = HZ["steps_top"]
            if z >= sz - 0.02:                                  # block: foot film 0.8 m up from the top step
                foot = float(1 - sstep(sz, sz + 0.80, z)) * (1 - up)
            else:                                               # steps and cap: everything low, treads most
                foot = 0.55 * float(1 - sstep(0.0, sz, z)) + 0.35 * up
            foot *= 0.65 + 0.7 * fine * blot
            crust += 0.75 * float(np.clip(foot, 0, 1))
        crust += 0.85 * streak[i] * (1.15 if fresh[i] else 1.0)
        if cls[i] in ("fig", "head"):
            _, fk, fd = kd.find(v)
            crust += 0.30 * FUR_W[fk] * float(1 - sstep(0.06, 0.12, fd))
        if cls[i] == "head":
            local = (p - (HEAD_C + np.array([0, 0, ZF + SLAB]))) @ HEAD_R
            # Pick out the facial carving under diffuse light with abrasion at exposed planes
            # and soot in short, sheltered cuts. Keep pigment continuous across the eyelids.
            face = float(sstep(0.055, 0.105, local[1]) * sstep(-0.16, -0.07, local[2]))
            crust += face * 0.48 * (1 - cav[i])
        if cls[i] == "vase":
            z = p[2] - HZ["vase_bottom"]
            damp_belly = float(sstep(-0.01, 0.14, z) * (1 - sstep(0.24, 0.68, z)))
            crust += damp_belly * (0.16 + 0.23 * blot) * (1 - 0.60 * up)
        crust = float(np.clip(crust, 0, 1))
        washed = (1 - sh[i]) * (0.25 + 0.75 * up) * ao[i]
        base = np.array([1.0, 1.0, 1.0]) * (0.92 + 0.16 * blot) * (0.97 + 0.06 * fine)
        if fresh[i]:
            base = base * np.array([1.13, 1.11, 1.06])          # plaza-barn-fix-s24: was 1.24 / 1.22 / 1.16 (read as new)
        elif cls[i] in ("vase", "band", "cornice", "cart"):
            base = base * np.array([0.97, 0.96, 0.95])
        base = base * (1 + 0.13 * washed)
        # iron-stained ochre patches of the old stone
        ochre = sstep(0.60, 0.85, 0.5 + 0.5 * noise.noise(v * 3.7 + Vector((11, 5, 2)))) * (0.0 if fresh[i] else 1.0)
        base = base * (1 - ochre * np.array([0.0, 0.07, 0.20]))
        tint = base * (1 - crust) + np.array([0.27, 0.265, 0.25]) * (0.85 + 0.3 * fine) * crust
        # lichen / algae: north side (-y), sheltered damp places and the foot of the monument
        north = max(-n[1], 0.0)
        lich = sstep(0.52, 0.80, 0.5 + 0.5 * noise.noise(v * 5.1 + Vector((2, 9, 4)))) * (0.25 + 0.75 * north) * (0.35 + 0.65 * up + 0.3 * sh[i])
        damp = float(1 - sstep(0.0, 0.5, p[2])) * 0.55 + (float(1 - sstep(HZ["steps_top"], HZ["steps_top"] + 0.35, p[2])) * 0.25 if p[2] > HZ["platform_top"] else 0.0)
        g = float(np.clip(lich * (0.5 if fresh[i] else 0.9) + damp * (0.4 + 0.6 * fine) * (0.5 + 0.5 * north), 0, 1))
        tint = tint * (1 - g) + tint * np.array([0.70, 0.76, 0.56]) * g
        tint = tint * (0.50 + 0.50 * ao[i])
        col[i, :3] = np.clip(tint * 0.5, 0.04, 0.98)
        col[i, 3] = 1.0
    return col, ao, cav


def cyl_uv(V, T, axis_xy, r0=0.30, period=None):
    """Cylindrical UV in metres (u around at radius r0, v up); vertices of triangles across the seam are duplicated."""
    th = np.arctan2(V[:, 0] - axis_xy[0], V[:, 1] - axis_xy[1])                    # seam at the back (-y)
    u = th * r0
    per = 2 * math.pi * r0
    V2, UV, extra = [V], [np.stack([u, V[:, 2]], 1)], {}
    T2 = T.copy()
    n = len(V)
    add_v, add_uv = [], []
    for ti, tri in enumerate(T):
        uu = u[tri]
        if uu.max() - uu.min() > per / 2:
            for c in range(3):
                if uu[c] < 0:
                    key = int(tri[c])
                    if key not in extra:
                        extra[key] = n + len(add_v)
                        add_v.append(V[key])
                        add_uv.append((uu[c] + per, V[key, 2]))
                    T2[ti, c] = extra[key]
    src = np.arange(n)
    if add_v:
        V2.append(np.array(add_v))
        UV.append(np.array(add_uv))
        src = np.r_[src, np.array(list(extra.keys()), np.int64)[np.argsort(list(extra.values()))]]
    return np.concatenate(V2), np.concatenate(UV), T2, src


def submesh(V, UV, COL, T, mask):
    """Triangles T[mask] with their own compact vertex set."""
    t = T[mask]
    used = np.unique(t)
    remap = -np.ones(len(V), np.int64)
    remap[used] = np.arange(len(used))
    return V[used], UV[used], (None if COL is None else COL[used]), remap[t], used


def seg_dist(P, a, b):
    ab = b - a
    t = np.clip(((P - a) @ ab) / (ab @ ab), 0, 1)
    return np.linalg.norm(P - (a + t[:, None] * ab), axis=1)


# ------------------------------------------------------------------------------------------------ main
def main():
    out = Path(arg("--output")) if arg("--output") else OUT
    bpy.ops.wm.read_factory_settings(use_empty=True)
    fig = build_figure()
    cart = build_cartouches()
    head = build_head()
    remesh(fig)
    bpy.context.view_layer.objects.active = fig
    smooth_shoulders(fig)
    detail_figure(fig)
    remesh(head, VOXEL * 0.40, passes=2)
    detail_figure(head)
    remesh(cart, VOXEL * 1.5)
    high = {"figure": mesh_arrays(fig), "head": mesh_arrays(head), "cartouches": mesh_arrays(cart)}
    arch_hi = build_architecture(False)
    # BVH of everything that casts occlusion / shelter: high sculpts + architecture
    bv, bt, off = [], [], 0
    for V, T in list(high.values()) + [(d["V"], d["T"]) for d in arch_hi.values()]:
        bv.append(V)
        if T.shape[1] == 3:
            bt.append(T + off)
        off += len(V)
    # high sculpts are quads after the voxel remesh: mesh_arrays triangulates through loop_triangles
    bvh = BVHTree.FromPolygons(np.concatenate(bv).tolist(), np.concatenate(bt).tolist(), all_triangles=True)
    base = np.array([0, 0, ZF + SLAB])
    data, stats = {}, {"high_tris": {k: int(len(v[1])) for k, v in high.items()}}

    def put(lod, mat, V, UV, COL, T):
        area = np.linalg.norm(np.cross(V[T[:, 1]] - V[T[:, 0]], V[T[:, 2]] - V[T[:, 0]]), axis=1)
        T = T[area > 1e-9]                                       # fan tips of the lathes / the cap of the cornice
        key = f"{lod}|{mat}"
        if key in data:
            o = len(data[key]["V"])
            for k, a in (("V", V), ("UV", UV), ("COL", COL)):
                data[key][k] = np.concatenate([data[key][k], a])
            data[key]["T"] = np.concatenate([data[key]["T"], T + o])
        else:
            data[key] = {"V": V, "UV": UV, "COL": COL, "T": T}

    for lod in ("lod0", "lod1"):
        low = lod == "lod1"
        tris = {}
        for name, src in (("figure", fig), ("head", head), ("cartouches", cart)):
            ob = decimated(src, BUDGET[lod][name], f"{name}_{lod}")
            V, T = mesh_arrays(ob)
            tris[name] = int(len(T))
            N = vertex_normals(V, T)
            cls = np.full(len(V), {"figure": "fig", "head": "head", "cartouches": "cart"}[name])
            COL, ao, cav = weather_colors(bvh, V, N, cls)
            if name != "cartouches":
                V2, UV, T2, srci = cyl_uv(V, T, (0.0, 0.0), r0=0.30 if name == "figure" else 0.12)
            else:
                V2, UV, T2, srci = V, np.stack([V[:, 0] + V[:, 1], V[:, 2]], 1), T, np.arange(len(V))
            COL2 = COL[srci]
            mask_metal = np.zeros(len(T2), bool)
            if name == "figure" and not low:
                cen = V2[T2].mean(1)
                a = R_EL + base + (R_WR - R_EL) * 0.30
                mask_metal = (seg_dist(cen, a, R_WR + base) < 0.088) | (np.linalg.norm((cen - (R_FIST + base)) / np.array([0.085, 0.09, 0.095]), axis=1) < 1.0)
                Vm, UVm, _, Tm, used = submesh(V2, UV, None, T2, mask_metal)
                source = srci[used]
                put(lod, PATINA, Vm, UVm, bronze_colors(bvh, Vm, N[source], ao[source], cav[source]), Tm)
            Vs, UVs, COLs, Ts, _ = submesh(V2, UV, COL2, T2, ~mask_metal)
            put(lod, STONE, Vs, UVs, COLs, Ts)
        arch = build_architecture(low)
        for mat, d in arch.items():
            N = vertex_normals(d["V"], d["T"])
            if mat == STONE:
                COL, _, _ = weather_colors(bvh, d["V"], N, d["cls"])
            else:
                COL = np.tile([0.5, 0.5, 0.5, 0.0], (len(d["V"]), 1))
            put(lod, mat, d["V"], d["UV"], COL, d["T"])
            tris[f"architecture:{mat}"] = int(len(d["T"]))
        m = build_mace(low)
        put(lod, GILT, m["V"], m["UV"], np.tile([0.5, 0.5, 0.5, 0.0], (len(m["V"]), 1)), m["T"])
        tris["mace"] = int(len(m["T"]))
        tris["total"] = int(sum(len(v["T"]) for k, v in data.items() if k.startswith(lod)))
        stats[lod] = tris
    arrays = {}
    for key, d in data.items():
        arrays[f"{key}|V"] = d["V"].astype(np.float32)
        arrays[f"{key}|UV"] = d["UV"].astype(np.float32)
        arrays[f"{key}|COL"] = np.clip(np.round(d["COL"] * 255), 0, 255).astype(np.uint8)
        arrays[f"{key}|T"] = d["T"].astype(np.int32)
    out.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(out / f"{ASSET}.npz", **arrays)
    allv = np.concatenate([d["V"] for k, d in data.items() if k.startswith("lod0")])
    meta = {"asset": ASSET, "generator": "tools/blender/world/landmarks/make_czarniecki.py",
            "generator_sha256": hashlib.sha256(Path(__file__).read_bytes().replace(b"\r\n", b"\n")).hexdigest(),
            "dims_sha256": hashlib.sha256((OUT / "dims.json").read_bytes().replace(b"\r\n", b"\n")).hexdigest(),
            "blender": bpy.app.version_string, "voxel_m": VOXEL, "tris": stats,
            "bbox_min": [round(float(x), 3) for x in allv.min(0)], "bbox_max": [round(float(x), 3) for x in allv.max(0)],
            "figure_base_z": ZF, "height_m": round(float(allv[:, 2].max()), 3),
            "materials": sorted({k.split("|")[1] for k in data})}
    (out / f"{ASSET}_meta.json").write_text(json.dumps(meta, indent=1) + "\n", encoding="utf-8", newline="\n")
    print("CZARNIECKI", json.dumps(stats))
    if arg("--render"):
        render(data, Path(arg("--render")))
    if "--blend" in argv:
        bpy.ops.wm.save_as_mainfile(filepath=str(out / f"{ASSET}.blend"))


# ------------------------------------------------------------------------------------------------ look-dev render
TINT = {STONE: (0.37, 0.335, 0.265), PATINA: (0.06, 0.132, 0.092), GILT: (0.55, 0.40, 0.10), SETT: (0.285, 0.282, 0.272)}


def render(data, out_dir):
    """Cycles look-dev with the baked vertex tint and fixed comparison cameras (QA only)."""
    out_dir.mkdir(parents=True, exist_ok=True)
    render_lod = arg("--lod") or "lod0"
    lighting = arg("--lighting") or "clear"
    if render_lod not in BUDGET or lighting not in ("clear", "overcast"):
        raise ValueError(f"Unsupported look-dev preset: {render_lod}, {lighting}")
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    for key, d in data.items():
        lod, mat = key.split("|")
        if lod != render_lod:
            continue
        me = bpy.data.meshes.new(key)
        me.from_pydata(d["V"].tolist(), [], d["T"].tolist())
        me.polygons.foreach_set("use_smooth", [True] * len(me.polygons))
        ca = me.color_attributes.new("Col", "FLOAT_COLOR", "POINT")
        c = d["COL"].copy()
        if mat == PATINA:
            pat = 0.90 * sstep(0.22, 0.85, c[:, 0])
            rub = 0.58 * sstep(0.16, 0.82, c[:, 1]) * (1 - 0.75 * pat)
            base = np.array([0.195, 0.172, 0.122])
            worn = base + (np.array([0.36, 0.285, 0.180]) - base) * rub[:, None]
            tinted = worn + (np.array(TINT[mat]) - worn) * pat[:, None]
            color = tinted * (0.50 + 0.50 * c[:, 2, None])
        elif mat == STONE:
            color = 2 * np.array(TINT[mat]) * c[:, :3]
        else:
            color = np.broadcast_to(TINT[mat], c[:, :3].shape)
        c[:, :3], c[:, 3] = color, 1.0
        ca.data.foreach_set("color", c.ravel())
        me.update()
        ob = bpy.data.objects.new(key, me)
        bpy.context.scene.collection.objects.link(ob)
        m = bpy.data.materials.new(mat)
        m.use_nodes = True
        nt = m.node_tree
        b = nt.nodes["Principled BSDF"]
        vc = nt.nodes.new("ShaderNodeVertexColor")
        vc.layer_name = "Col"
        nt.links.new(vc.outputs["Color"], b.inputs["Base Color"])
        b.inputs["Roughness"].default_value = 0.4 if mat == GILT else 0.9
        b.inputs["Metallic"].default_value = 0.9 if mat == GILT else (0.3 if mat == PATINA else 0.0)
        me.materials.append(m)
    bpy.ops.mesh.primitive_plane_add(size=80)
    g = bpy.context.object
    gm = bpy.data.materials.new("ground")
    gm.use_nodes = True
    gm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.25, 0.24, 0.23, 1)
    g.data.materials.append(gm)
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.samples = int(arg("--samples") or 48)
    sc.cycles.use_denoising = True
    try:
        sc.cycles.device = "GPU"
        prefs = bpy.context.preferences.addons["cycles"].preferences
        prefs.compute_device_type = "OPTIX"
        prefs.get_devices()
        for dv in prefs.devices:
            dv.use = True
    except Exception as e:                                       # CPU is fine for a look-dev frame
        print("GPU not used:", e)
    w = bpy.data.worlds.new("w")
    sc.world = w
    w.use_nodes = True
    sc.view_settings.view_transform = "Filmic"
    background = w.node_tree.nodes["Background"]
    if lighting == "clear":
        sky = w.node_tree.nodes.new("ShaderNodeTexSky")
        sky.sky_type = "NISHITA"
        sky.sun_elevation = math.radians(48)
        sky.sun_rotation = math.radians(200)
        sky.sun_intensity = 0.35
        w.node_tree.links.new(sky.outputs[0], background.inputs[0])
        sc.view_settings.exposure = -2.5
    else:
        background.inputs["Color"].default_value = (0.58, 0.63, 0.70, 1)
        soft_light = bpy.data.lights.new("Cloud cover", "AREA")
        soft_light.energy, soft_light.size = 2200, 14
        lamp = bpy.data.objects.new(soft_light.name, soft_light)
        sc.collection.objects.link(lamp)
        lamp.location = (-2, 5, 15)
        lamp.rotation_euler = (Vector((0, 0, 6)) - lamp.location).to_track_quat("-Z", "Y").to_euler()
        sc.view_settings.exposure = -0.5
    cams = {"front_below": ((0.6, 9.5, 1.6), (0.1, 0.0, 5.9), 30, (900, 1200)), "front_left": ((-7.5, 8.5, 1.6), (0.0, 0.0, 4.6), 38, (900, 1200)),
            "figure_front": ((0.5, 16.0, 4.0), (0.1, 0.0, 6.15), 14, (1000, 1200)), "figure_left": ((-11.0, 11.0, 4.5), (0.0, 0.1, 6.15), 14, (1000, 1200)),
            "figure_right": ((12.0, 9.0, 4.5), (0.0, 0.1, 6.15), 14, (1000, 1200)), "figure_back": ((-3.0, -15.0, 5.0), (0.0, 0.0, 6.15), 14, (1000, 1200)),
            "head": ((1.6, 5.0, 6.6), (0.03, 0.05, 7.22), 9, (900, 900)), "pedestal": ((-1.2, 7.0, 1.6), (0.0, 0.0, 3.4), 40, (900, 1200))}
    # Same 3/4 azimuth and eye height on both stations. Distance is horizontal to the monument axis.
    for distance, elevation_target in ((6, 4.5), (15, 4.0)):
        position = (0.6 * distance, 0.8 * distance, 1.7)
        cams[f"eye_34_{distance}m"] = (position, (0.0, 0.0, elevation_target), 56, (1000, 1200))
    only = arg("--cams")
    for name, (pos, tgt, fov, res) in cams.items():
        if only and name not in only.split(","):
            continue
        cd = bpy.data.cameras.new(name)
        cd.sensor_fit = "VERTICAL"
        cd.angle_y = math.radians(fov)
        cam = bpy.data.objects.new(name, cd)
        sc.collection.objects.link(cam)
        cam.location = pos
        cam.rotation_euler = (Vector(tgt) - Vector(pos)).to_track_quat("-Z", "Y").to_euler()
        sc.camera = cam
        sc.render.resolution_x, sc.render.resolution_y = res
        sc.render.filepath = str(out_dir / f"{name}.png")
        bpy.ops.render.render(write_still=True)


if "--render-existing" in argv:
    if not arg("--render"):
        raise ValueError("--render-existing requires --render")
    bpy.ops.wm.read_factory_settings(use_empty=True)
    data = {}
    source = Path(arg("--output")) if arg("--output") else OUT
    with np.load(source / f"{ASSET}.npz") as asset:
        for key in asset:
            lod, mat, channel = key.split("|")
            data.setdefault(f"{lod}|{mat}", {})[channel] = asset[key] / 255.0 if channel == "COL" else asset[key]
    render(data, Path(arg("--render")))
else:
    main()
