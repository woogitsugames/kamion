"""Figure of the king on Rynek in Knyszyn (ADR 0325; replaces the lathed "bottle" of ADR 0320).

What stands there (Wikimedia Commons "Pomnik krola Zygmunta Augusta w Knyszynie, zdj. 18 lipca 2019 r" CC BY-SA 4.0,
"Podlaskie - Knyszyn - Knyszyn - pomnik" CC BY-SA 4.0, "Knyszyn Zygmunt II August" CC BY-SA 3.0; owner photos 1 / 8 -
reference only, nothing of them is in the repo or the build): a bronze figure wrapped in a floor-length cloak that
hides the arms - a faceted bell with broad vertical folds and a seam down the front -, fur lapels meeting in a V on the
chest, two chains with a jewel, a pleated ruff, a bearded head and an open crown of fleurons. NO hands or sceptre are
visible on the sculpture, so none are modelled. The lettering on the cloak and the plaque text are omitted.

A stylised low-poly sculpt, not a scan or a copy of the artwork: proportions read off the frontal Commons photo
(figure height = 2.5 x hem width, shoulders 0.58 of the hem, head with crown 0.16 of the height) at the hem width of
ADR 0320 (0.75 of the plinth top). All sizes WORKING_VALUE. Local frame: x right, y forward (front of the figure),
z up from the top of the plinth; `build()` places it in the world.

LOD0 ~2.3 k triangles in three bronze materials (base, patina for fur / ruff / beard, rubbed for crown and chains);
LOD1 ~0.3 k (cloak, head, crown, ruff, lapels) in one.
"""
from __future__ import annotations

import math

import numpy as np

BRONZE, PATINA, RUBBED = "monument_bronze", "monument_bronze_patina", "monument_bronze_rubbed"
H_SHOULDER = 2.40            # top of the straight part of the cloak
H_NECK = 2.54                # cloak closes under the ruff
HEAD_Y = 0.045               # the head sits forward of the cloak axis (side photo)

# Plan of the cloak: a faceted bell. Corners (ridges of the broad folds) at these angles (deg from +x, front = 90) stand
# proud of the base outline by `amp` (fraction of the radius at the hem); the planes between them are flat, so the hem
# is a polygon with a prow at the front seam. The facets fade into a rounded section at the shoulders.
CORNERS = ((-8, .080), (38, .060), (90, .105), (142, .060), (188, .080), (236, .095), (270, -.035), (304, .095))
FACET_AT_SHOULDER = 0.55     # share of the faceting left at shoulder height
COLS0 = (-8, -2, 15, 32, 38, 44, 64, 82, 86, 90, 94, 98, 116, 136, 142, 148, 165, 182, 188, 194, 212, 230, 236, 242,
         256, 266, 270, 274, 284, 298, 304, 310, 328, 346)
COLS1 = (-8, 38, 82, 90, 98, 142, 188, 236, 270, 304)
RINGS0 = (0.0, .04, .30, .62, .95, 1.28, 1.60, 1.90, 2.15, 2.30, H_SHOULDER, 2.45, 2.50, H_NECK)
RINGS1 = (0.0, .62, 1.60, 2.30, H_SHOULDER, H_NECK)


def _base_radius(theta_deg, z):
    t = min(max(z / H_SHOULDER, 0.0), 1.0)
    a = 0.325 + 0.235 * (1 - t) ** 1.12
    bf = 0.245 + 0.200 * (1 - t) + 0.030 * math.exp(-((z - 1.95) / 0.38) ** 2)      # chest
    bb = 0.225 + 0.215 * (1 - t)
    if z > H_SHOULDER:                                   # shoulders slope up to the neck
        s = min((z - H_SHOULDER) / (H_NECK - H_SHOULDER), 1.0)
        k = 1.0 - s ** 1.1
        a = 0.150 + (a - 0.150) * k
        bf = 0.150 + (bf - 0.150) * k
        bb = 0.140 + (bb - 0.140) * k
    th = math.radians(theta_deg)
    c, s_ = math.cos(th), math.sin(th)
    b = bf if s_ >= 0 else bb
    p = 2.6 - 0.5 * t
    return (abs(c / a) ** p + abs(s_ / b) ** p) ** (-1.0 / p)


def cloak_point(theta_deg, z, lift=0.0):
    """Point of the cloak surface (local x, y, z); `lift` = metres along the outward horizontal direction."""
    t = min(max(z / H_SHOULDER, 0.0), 1.0)
    th = (theta_deg + 8.0) % 360.0 - 8.0                 # -8 .. 352
    k = max(i for i, (ang, _) in enumerate(CORNERS) if ang <= th + 1e-9)
    (a0, m0), (a1, m1) = CORNERS[k], (CORNERS[k + 1] if k + 1 < len(CORNERS) else (CORNERS[0][0] + 360.0, CORNERS[0][1]))
    flare = (1 - t) ** 0.55                              # the folds open towards the hem
    p0 = _base_radius(a0, z) * (1 + m0 * flare)
    p1 = _base_radius(a1, z) * (1 + m1 * flare)
    # radius of the chord between the two corner points at this angle
    d0, d1 = math.radians(th - a0), math.radians(a1 - th)
    chord = p0 * p1 * math.sin(d0 + d1) / max(p0 * math.sin(d0) + p1 * math.sin(d1), 1e-9)
    w = FACET_AT_SHOULDER + (1 - FACET_AT_SHOULDER) * (1 - t) ** 0.8
    if z > H_SHOULDER:
        w *= 1.0 - min((z - H_SHOULDER) / (H_NECK - H_SHOULDER), 1.0)
    r = _base_radius(theta_deg, z) * (1 - w) + chord * w
    if z < 0.02:
        r *= 0.975                                       # hem rolled under
    r += lift
    a = math.radians(theta_deg)
    return np.array([r * math.cos(a), r * math.sin(a) + 0.035 * t, z])


class Sculpt:
    """Local-space triangles per material."""

    def __init__(self):
        self.parts = {}
        self.uv = {}          # (material, index of the part) -> (radius m, y of the axis) of its cylindrical UV

    def add(self, mat, V, T, orient=None, flat=False):
        """orient: None = as wound; "centre" = away from the piece's centroid (small convex pieces); "axis" = away
        from the vertical axis of the figure (pieces lying on the cloak). flat: every triangle gets its own vertices -
        the chunk writer smooths normals over shared vertices, which on a sharp little prism (nose, brow) or on the
        two sides of a plate gives normals that point nowhere near the faces (r3 render: white nose and fleurons)."""
        V, T = np.asarray(V, float).reshape(-1, 3), np.asarray(T, int).reshape(-1, 3)
        if orient:
            n = np.cross(V[T[:, 1]] - V[T[:, 0]], V[T[:, 2]] - V[T[:, 0]])
            d = V[T].mean(1) - (V.mean(0) if orient == "centre" else [0.0, 0.0, 0.0])
            if orient == "axis":
                d[:, 2] = 0.0
            T = np.where((np.einsum("ij,ij->i", n, d) < 0)[:, None], T[:, ::-1], T)
        if flat:
            V, T = V[T].reshape(-1, 3), np.arange(3 * len(T)).reshape(-1, 3)
        self.parts.setdefault(mat, []).append((V, T))

    def loft(self, mat, rings, cap_top=False, cap_bottom=False, closed=True, orient=None):
        """Quads between consecutive rings (each (n, 3), counter-clockwise seen from above)."""
        R = [np.asarray(r, float) for r in rings]
        n = len(R[0])
        V = np.concatenate(R)
        T = []
        for j in range(len(R) - 1):
            for i in range(n if closed else n - 1):
                a, b = j * n + i, j * n + (i + 1) % n
                T += [(a, b, b + n), (a, b + n, a + n)]
        if cap_top:
            b0 = (len(R) - 1) * n
            T += [(b0, b0 + i, b0 + i + 1) for i in range(1, n - 1)]
        if cap_bottom:
            T += [(0, i + 1, i) for i in range(1, n - 1)]
        self.add(mat, V, T, orient)

    def tube(self, mat, pts, radii, sides=4):
        P = [np.asarray(p, float) for p in pts]
        rings = []
        for k, p in enumerate(P):
            d = P[min(k + 1, len(P) - 1)] - P[max(k - 1, 0)]
            d /= np.linalg.norm(d)
            ref = np.array([0.0, 1.0, 0.0]) if abs(d[1]) < 0.9 else np.array([1.0, 0.0, 0.0])
            u = np.cross(d, ref)
            u /= np.linalg.norm(u)
            v = np.cross(d, u)
            rings.append([p + (u * math.cos(2 * math.pi * i / sides) + v * math.sin(2 * math.pi * i / sides)) * radii[k]
                          for i in range(sides)])
        self.loft(mat, rings, cap_top=True, cap_bottom=True)

    def plate(self, mat, outline):
        """Flat polygon (fan from vertex 0), both sides."""
        V = np.asarray(outline, float)
        T = [(0, i, i + 1) for i in range(1, len(V) - 1)]
        self.add(mat, V, T)                                   # the back gets its own vertices (own normals)
        self.add(mat, V, [(a, c, b) for a, b, c in T])

    def tris(self):
        return sum(len(t) for parts in self.parts.values() for _, t in parts)


def _cloak(sc, low):
    cols, zs = (COLS1, RINGS1) if low else (COLS0, RINGS0)
    rng = np.random.default_rng(325)
    rings = []
    for z in zs:
        ring = []
        for th in cols:
            p = cloak_point(th, z)
            if th == 90 and z < 1.62:
                p = cloak_point(th, z, lift=-0.022)          # seam between the two edges of the cloak
            elif not low and 0.02 < z < H_SHOULDER and th not in (86, 94):
                p = cloak_point(th, z, lift=float(rng.uniform(-0.009, 0.009)))   # hammered planes, not a lathe
            ring.append(p)
        rings.append(ring)
    sc.loft(BRONZE, rings, cap_top=True)


# --- head (ADR 0331): one smooth sheet sampled on a (theta, z) grid, the face carved by displacements -------------------
# Proportions read off the two Commons close-ups (cs20127375, cs7518515), in units of E = eyes -> chin: crown band
# 0.38 E above the eyes, tips of the fleurons 1.27 E, point of the beard 0.7 E under the chin, face 1.35 E wide with
# the hair. E = 0.165 m (heroic scale, the figure is ~1.6 x life size). All WORKING_VALUE.
Z_EYE = 2.835
Z_CHIN = 2.672
Z_NOSE = 2.766              # tip of the nose
Z_MOUTH = 2.716
Z_BEARD_TIP = 2.578

# rows of the head profile: z, half width, front depth, back depth (superellipse 2.4)
HEAD_PROFILE = ((2.560, .052, .052, .058), (2.620, .058, .060, .064), (2.660, .074, .080, .080),
                (2.700, .085, .092, .094), (2.740, .091, .098, .102), (2.780, .095, .100, .107),
                (2.820, .096, .099, .111), (2.860, .097, .101, .113), (2.900, .095, .097, .112),
                (2.935, .088, .088, .105), (2.962, .064, .066, .086), (2.976, .034, .034, .046), (2.984, .008, .008, .010))
# columns (degrees off the front) and rows: dense over the face, sparse behind the ears and under the crown
HEAD_D0 = (0, 3, 6, 9, 13, 17, 22, 28, 35, 43, 52, 62, 74, 88, 108, 145)
HEAD_Z0 = (2.579, 2.598, 2.615, 2.636, 2.652, 2.664, 2.675, 2.686, 2.696, 2.704, 2.710, 2.716, 2.722, 2.729,
           2.737, 2.746, 2.755, 2.762, 2.769, 2.777, 2.786, 2.795, 2.804, 2.812, 2.818, 2.824, 2.830, 2.836, 2.842,
           2.848, 2.854, 2.861, 2.870, 2.884, 2.900, 2.922, 2.950, 2.970, 2.983)
HEAD_D1 = (0, 25, 55, 90, 135)
HEAD_Z1 = (2.570, 2.640, 2.700, 2.760, 2.830, 2.900, 2.970)
ROLL_DEG = 1.6              # the head leans a little to its left (a cast, not a mirror)


def _g(u, u0, su, z, z0, sz):
    return math.exp(-((u - u0) / su) ** 2 - ((z - z0) / sz) ** 2)


def _smoothstep(e0, e1, x):
    t = min(max((x - e0) / (e1 - e0), 0.0), 1.0)
    return t * t * (3 - 2 * t)


def _profile(d, z):
    """Base radius of the skull at `d` degrees off the front (signed) and height z (from the head axis)."""
    rows = HEAD_PROFILE
    zs = [r[0] for r in rows]
    w = float(np.interp(z, zs, [r[1] for r in rows]))
    f = float(np.interp(z, zs, [r[2] for r in rows]))
    b = float(np.interp(z, zs, [r[3] for r in rows]))
    a = math.radians(90 + d)
    c, s = math.cos(a), math.sin(a)
    dd = f if s >= 0 else b
    p = 2.4
    return (abs(c / w) ** p + abs(s / dd) ** p) ** (-1 / p)


def _face(d, z, sx_eye=0.0):
    """Radial displacement of the face: brow, sockets and lids, nose, cheekbones, mouth (metres). `u` ~ metres across."""
    u = 0.095 * math.sin(math.radians(max(-90.0, min(90.0, d))))
    if abs(d) > 95:
        return 0.0
    e = Z_EYE + sx_eye * (1 if u > 0 else -1)
    au = abs(u)
    r = 0.004 * _g(u, 0, .05, z, 2.885, .022)                                   # forehead
    r += 0.010 * _g(au, .033, .024, z, e + .020, .008)                         # brow ridge
    r += 0.004 * _g(u, 0, .011, z, e + .012, .010)                             # glabella
    r -= 0.022 * _g(au, .035, .018, z, e + .003, .011)                         # eye socket
    r += 0.016 * _g(au, .034, .012, z, e + .001, .006)                         # eyeball
    r -= 0.004 * _g(au, .033, .014, z, e + .010, .003)                         # crease over the upper lid
    r -= 0.005 * _g(au, .033, .0055, z, e - .001, .0045)                      # carved iris
    r += 0.003 * _g(au, .037, .014, z, e - .014, .005)                         # lower lid
    r -= 0.006 * _g(au, .080, .016, z, 2.855, .022)                            # temple
    r += 0.008 * _g(au, .058, .020, z, e - .030, .015)                         # cheekbone
    r -= 0.006 * _g(au, .056, .020, z, 2.748, .018)                            # hollow under it
    # nose: a ridge growing from the bridge to the tip, wings at the base
    if Z_NOSE - 0.012 < z <= e + 0.012:
        prot = 0.004 + 0.034 * (1 - (z - Z_NOSE) / (e + 0.012 - Z_NOSE)) ** 1.15 if z >= Z_NOSE else \
            0.038 * (1 - (Z_NOSE - z) / 0.012) ** 0.6
        su = 0.0065 + 0.0045 * (1 - (z - Z_NOSE) / (e + 0.012 - Z_NOSE)) if z >= Z_NOSE else 0.011
        r += prot * math.exp(-(u / su) ** 2)
    r += 0.006 * _g(au, .014, .006, z, Z_NOSE - .003, .006)                    # nostril wings
    r += 0.004 * _g(u, 0, .008, z, Z_NOSE + .002, .007)                        # ball of the tip
    # mouth: lips and the slit between them; moustache over the upper lip, drooping at the ends
    r += 0.004 * _g(u, 0, .020, z, Z_MOUTH + .006, .005)
    r -= 0.009 * _g(u, 0, .018, z, Z_MOUTH, .0035)
    r += 0.006 * _g(u, 0, .014, z, Z_MOUTH - .009, .005)
    zm = Z_MOUTH + 0.012 - 11.0 * u * u
    r += 0.014 * math.exp(-((z - zm) / 0.0065) ** 2) * (1 - _smoothstep(0.040, 0.056, au)) * (1 - 0.35 * math.exp(-(u / .006) ** 2))
    r += 0.012 * _g(u, 0, .026, z, Z_CHIN + .010, .016)                       # chin
    return r


def _beard_line(d):
    """Upper edge of the beard (z) at d degrees off the front: under the lip, up past the mouth to the sideburns."""
    a = abs(d)
    return float(np.interp(a, (0, 12, 22, 70, 84, 92), (2.700, 2.704, 2.712, 2.800, 2.812, 2.760)))


def _beard(d, z, base):
    """Outer radius of the beard (0 = none): a thickness over the jaw and a pointed lobe under the chin."""
    a = abs(d)
    if a > 92:
        return 0.0
    rb = 0.0
    top = _beard_line(d)
    if z < top:
        thick = 0.007 + 0.017 * _smoothstep(top, Z_CHIN, z) * (1 - 0.5 * _smoothstep(40, 85, a))
        rb = base + thick * _smoothstep(top + 0.002, top - 0.012, z)
    if z < Z_CHIN + 0.02:       # the pointed lobe: front reach and half angle shrink to the tip
        s = (z - Z_BEARD_TIP) / (Z_CHIN + 0.02 - Z_BEARD_TIP)
        if s >= 0:
            s = min(s, 1.0)
            reach = 0.124 + 0.012 * s ** 0.5
            half = 3.0 + 64.0 * s ** 1.25
            if a < half:
                rb = max(rb, reach * (1 - (a / half) ** 2) ** 0.45)
    return rb


def _strands(d, z):
    """Wavy grooves of the cast hair / beard: a few millimetres, no two the same."""
    return 0.0028 * math.sin(math.radians(d) * 23.0 + 9.0 * z + 1.3 * math.sin(z * 61.0)) \
        + 0.0015 * math.sin(math.radians(d) * 41.0 - 30.0 * z)


def _hair(d, z):
    """Thickness of the hair: a short bob of curls behind the ears and on the temples, under the crown band."""
    a = abs(d)
    if z < 2.688 or a < 72:
        return 0.0
    edge = _smoothstep(72, 88, a) if z > 2.835 else _smoothstep(92, 104, a)
    curls = 0.0035 * math.sin(math.radians(d) * 14.0) * math.sin(z * 170.0) + 0.003 * math.sin(z * 95.0 + d * 0.11)
    return edge * _smoothstep(2.688, 2.715, z) * (0.013 + curls)


def head_point(d, z, low=False):
    """Local point of the head surface at d degrees off the front (+ = figure's left, -x) and height z."""
    base = _profile(d, z)
    sx = 0.0015                                       # one eye a little higher than the other
    r = base + (0.0 if low else _face(d, z, sx))
    beard = _beard(d, z, r)
    if beard > 0:
        bead = beard + (0.0 if low else _strands(d, z))
        k = 260.0                                     # smooth max over ~5 mm: the beard grows out of the face
        r = math.log(math.exp(k * r) + math.exp(k * bead)) / k
    h = _hair(d, z)
    if h > 0:
        r += h + (0.0 if low else 0.5 * _strands(d, z + 0.3))
    a = math.radians(90 + d)
    x, y = r * math.cos(a), r * math.sin(a) + HEAD_Y
    if z < Z_CHIN + 0.02 and abs(d) < 30:             # the point of the beard swings a little to one side
        x += 0.006 * _smoothstep(Z_CHIN + 0.02, Z_BEARD_TIP, z)
    # roll about the forward axis through the neck
    rr = math.radians(ROLL_DEG)
    zc = 2.60
    x, z2 = x * math.cos(rr) - (z - zc) * math.sin(rr), x * math.sin(rr) + (z - zc) * math.cos(rr) + zc
    return [x, y, z2]


def _head(sc, low):
    ds = HEAD_D1 if low else HEAD_D0
    cols = sorted({-d for d in ds} | set(ds)) + [180]
    cols = [c for c in cols if c != -180]
    zs = HEAD_Z1 if low else HEAD_Z0
    # ring order counter-clockwise seen from above: theta = 90 + d grows with d
    rings = [[head_point(d, z, low) for d in cols] for z in zs]
    sc.loft(BRONZE, rings, cap_top=True)
    sc.uv[(BRONZE, len(sc.parts[BRONZE]) - 1)] = (0.10, HEAD_Y)      # streaks of the cast at the scale of the face
    if low:
        return
    for sx in (-1, 1):
        _ear(sc, sx)


def _ear(sc, sx):
    """Ear: a shell with a rolled rim and a hollow bowl, its back edge standing ~1.5 cm off the head (prominent on the
    photos, at the height of the eyes to the nose). sx = +1: the figure's right (+x)."""
    zc = 2.796
    root = np.array(head_point(sx * -84.0, zc))       # front edge, grown into the cheek behind the sideburn
    out = np.array([sx, 0.0, 0.0])
    back = np.array([0.0, -1.0, 0.0])
    up = np.array([0.0, 0.0, 1.0])
    n = 12
    # (scale of the outline, offset along `out`): back of the rim, crest of the rim, inner slope, bowl
    rings = []
    for scale, off in ((0.92, -0.006), (1.0, 0.003), (0.72, 0.001), (0.34, -0.006)):
        ring = []
        for i in range(n):
            a = 2 * math.pi * i / n
            s_, c_ = math.sin(a), math.cos(a)
            hz = 0.036 * s_ * (1.0 if s_ > 0 else 0.80)          # lobe smaller than the top
            along = 0.022 + 0.020 * c_                           # 0.2 .. 4.2 cm behind the root
            p = root + back * (0.022 + (along - 0.022) * scale) + up * hz * scale
            p = p + out * (0.004 + 0.30 * (along - 0.002) * max(scale, 0.6) + off)
            ring.append(p)
        rings.append(ring)
    sc.loft(BRONZE, rings, cap_top=True, orient="centre")


def _ruff(sc, low):
    """Pleated ruff: figure-of-eight pleats, chunky (the close-up: as tall as the chin-to-mouth distance), up to the
    jaw at the sides, tucked under the beard at the front; its underside runs down into the neck of the cloak."""
    n = 8 if low else 48
    R, zc = 0.158, 2.632
    prof = ((-0.040, -(zc - H_NECK) - 0.010), (-0.050, -0.030), (0.004, -0.034), (0.030, 0.004), (-0.010, 0.040),
            (-0.064, 0.020))
    rings = [[] for _ in prof]
    for i in range(n):
        a = 2 * math.pi * i / n
        wob = 0.0 if low else math.sin(math.pi * i / 2) * (1.0 + 0.25 * math.sin(i * 1.7))     # rounded lobes, 4 vertices each
        c, s = math.cos(a), math.sin(a)
        fr = max(s, 0.0) ** 3                             # dips and tucks in under the beard at the front
        for k, (dr, dz) in enumerate(prof):
            rr = R + dr + (0.0 if low else 0.015 * wob * (1 if k in (2, 4) else 0.4 if k == 3 else 0.0))
            zz = zc + dz + (0.0 if low else 0.006 * wob * (1 if k == 4 else -1 if k == 2 else 0.0))
            if k > 0:
                zz -= 0.050 * fr
                rr -= 0.058 * fr
            rings[k].append([rr * c, rr * 0.96 * s + HEAD_Y * 0.7, zz])
    sc.loft(PATINA, rings)


# crown: band hugging the hair, 4 tall and 4 low fleurons (the tall one at the front), stones on the band
H_BAND0 = 2.896
H_BAND1 = 2.944
H_TOP_DRAWN = 3.035
# The head, ruff and crown are drawn round E = 0.165 m and then scaled about the neck: the frontal Commons photo
# (cs7518515) gives crown-to-beard 0.18 of the figure height (~0.55 m), the drawn head is 0.46 m.
HEAD_SCALE = 1.12
HEAD_PIVOT_Z = 2.55
H_TOP = HEAD_PIVOT_Z + (H_TOP_DRAWN - HEAD_PIVOT_Z) * HEAD_SCALE        # tips of the tall fleurons, as built
FLEURON_TALL = ((0.00, 0.00), (0.50, 0.00), (0.58, 0.24), (1.00, 0.46), (0.86, 0.70), (0.52, 0.58), (0.40, 0.82),
                (0.16, 0.92))
FLEURON_LOW = ((0.00, 0.00), (0.70, 0.00), (0.40, 0.30), (0.30, 0.80))


def _crown_r(th, z, grow=0.0):
    """Point on the band: an oval round the hair, flaring 9 mm towards the rim."""
    t = (z - H_BAND0) / (H_BAND1 - H_BAND0)
    a = math.radians(th)
    w, f, b = 0.113 + 0.009 * t + grow, 0.112 + 0.009 * t + grow, 0.130 + 0.009 * t + grow
    c, s = math.cos(a), math.sin(a)
    dd = f if s >= 0 else b
    r = (abs(c / w) ** 2.2 + abs(s / dd) ** 2.2) ** (-1 / 2.2)
    return np.array([r * c, r * s + HEAD_Y - 0.004, z])


def _fleuron(sc, th, tall, low):
    base = _crown_r(th, H_BAND1 - 0.004)
    a = math.radians(th)
    out = np.array([math.cos(a), math.sin(a), 0.0])
    t = np.array([-math.sin(a), math.cos(a), 0.0])
    h = (H_TOP_DRAWN - H_BAND1 + 0.004 - 0.020) if tall else 0.058      # + the ball: 2 x 9 mm
    w = 0.050 if tall else 0.014
    shape = FLEURON_TALL if tall else FLEURON_LOW
    if low:
        sc.plate(RUBBED, [base - t * w, base + t * w, base + out * 0.010 + [0, 0, h + (0.018 if tall else 0.0)]])      # no ball on LOD1
        return
    half = [(u, v) for u, v in shape[1:]]
    outline = [(u, v) for u, v in half] + [(0.0, 1.0)] + [(-u, v) for u, v in reversed(half)]

    def pt(u, v, off):
        lean = 0.014 * v ** 1.6                       # the tips lean out
        return base + t * (u * w) + np.array([0, 0, v * h]) + out * (lean + off)
    front = [pt(u, v, 0.0045) for u, v in outline]
    backf = [pt(u, v, -0.0045) for u, v in outline]
    c_front, c_back = pt(0.0, 0.42, 0.0060), pt(0.0, 0.42, -0.0060)
    n = len(outline)
    V = front + backf + [c_front, c_back]
    T = [(2 * n, i, (i + 1) % n) for i in range(n - 1)] + [(2 * n + 1, n + (i + 1) % n, n + i) for i in range(n - 1)]
    T += [(2 * n, n - 1, 0), (2 * n + 1, n, 2 * n - 1)]
    for i in range(n):
        j = (i + 1) % n
        T += [(i, n + i, n + j), (i, n + j, j)]
    sc.add(RUBBED, V, T, orient="centre", flat=True)
    top = pt(0.0, 1.0, 0.0)          # ball on the tip (the low points are pearls on stalks)
    rb = 0.009 if tall else 0.010
    sc.tube(RUBBED, [top + [0, 0, -0.002], top + [0, 0, rb], top + [0, 0, 2 * rb]], [0.6 * rb, rb, 0.3 * rb], 4)
    if tall:          # oval stone in the heart of the leaf
        c = pt(0.0, 0.40, 0.0)
        sc.tube(RUBBED, [c, c + out * 0.008, c + out * 0.011], [0.010, 0.008, 0.002], 4)


def _crown(sc, low):
    n = 8 if low else 16
    ths = [360.0 * i / n + 90.0 for i in range(n)]
    if low:
        sc.loft(RUBBED, [[_crown_r(th, H_BAND0) for th in ths], [_crown_r(th, H_BAND1, 0.004) for th in ths]])
    else:        # rolled lower edge, a raised moulding with the stones, the rim, the inner face
        rows = ((H_BAND0 - 0.003, -0.003), (H_BAND0 + 0.006, 0.006), (H_BAND0 + 0.014, 0.002), (H_BAND0 + 0.024, 0.008),
                (H_BAND0 + 0.034, 0.002), (H_BAND1, 0.008), (H_BAND1 + 0.004, -0.002), (H_BAND1 - 0.03, -0.010))
        sc.loft(RUBBED, [[_crown_r(th, z, g) for th in ths] for z, g in rows])
        for i in range(8):     # oval stones between the fleurons, on the moulding
            th = 90.0 + 45.0 * i + 22.5
            p = _crown_r(th, H_BAND0 + 0.024, 0.008)
            a = math.radians(th)
            out = np.array([math.cos(a), math.sin(a), 0.0])
            sc.tube(RUBBED, [p - out * 0.002, p + out * 0.006, p + out * 0.009], [0.009, 0.007, 0.002], 4)
    for i in range(8):
        _fleuron(sc, 90.0 + 45.0 * i, i % 2 == 0, low)


LAPEL = ((2.500, 36, .135), (2.40, 31, .150), (2.25, 25, .150), (2.08, 19, .135), (1.90, 13.5, .115), (1.74, 9, .095),
         (1.62, 5.5, .075), (1.55, 3.5, .050))          # z, degrees off the front, width m


def _lapels(sc, low):
    if low:
        rows = LAPEL[::3] + (LAPEL[-1],)
    else:          # a row between every two: tufts of the fur every ~8 cm
        rows = []
        for a, b in zip(LAPEL[:-1], LAPEL[1:]):
            rows += [a, tuple(0.5 * (u + v) for u, v in zip(a, b))]
        rows.append(LAPEL[-1])
    for sx in (-1, 1):
        inner, crest, outer = [], [], []
        for k, (z, off, w) in enumerate(rows):
            r_here = float(np.hypot(*cloak_point(90, z)[:2]))
            dw = math.degrees(w / max(r_here, 0.1))                     # width in degrees at this height
            jag = 0.0 if low else (0.020 if k % 2 else -0.010)          # tufts of the fur along the outer edge
            th_in, th_out = 90 + sx * off, 90 + sx * (off + dw + math.degrees(jag / r_here))
            inner.append(cloak_point(th_in, z, 0.004))
            crest.append(cloak_point(0.5 * (th_in + th_out), z, 0.050 if k % 2 or low else 0.030))
            outer.append(cloak_point(th_out, z, 0.004))
        sc.loft(PATINA, [inner, crest, outer], closed=False, orient="axis")


def _chains(sc):
    for half_deg, z_top, z_low, lift, n in ((27, 2.475, 1.99, 0.022, 27), (15, 2.50, 2.14, 0.018, 19)):
        pts, rad = [], []
        for i in range(n):
            t = -1 + 2 * i / (n - 1)
            z = z_low + (z_top - z_low) * abs(t) ** 1.7
            pts.append(cloak_point(90 + t * half_deg, z, lift))
            rad.append(0.015 if i % 2 else 0.009)                      # links
        sc.tube(RUBBED, pts, rad, 4)
    # jewel under the long chain
    c = cloak_point(90, 1.93, 0.030)
    ring = [[c[0] + 0.045 * math.cos(2 * math.pi * i / 8), c[1] - 0.012, c[2] + 0.050 * math.sin(2 * math.pi * i / 8)] for i in range(8)]
    V = [c + [0, 0.012, 0]] + ring
    sc.add(RUBBED, V, [(0, 1 + (i + 1) % 8, 1 + i) for i in range(8)], orient="axis", flat=True)


def sculpt(low=False):
    """Local-space figure; z = 0 on the plinth."""
    sc = Sculpt()
    _cloak(sc, low)
    before = {m: len(p) for m, p in sc.parts.items()}
    _head(sc, low)
    _ruff(sc, low)
    _crown(sc, low)
    piv = np.array([0.0, HEAD_Y, HEAD_PIVOT_Z])
    for m, parts in sc.parts.items():          # head, ruff and crown were drawn at 1 : HEAD_SCALE
        for k in range(before.get(m, 0), len(parts)):
            V, T = parts[k]
            parts[k] = (piv + (V - piv) * HEAD_SCALE, T)
    _lapels(sc, low)
    if not low:
        _chains(sc)
    return sc


def build(acc, layer, base, forward, low=False, remap=None):
    """Add the figure to a buildings_mesh.Acc: `base` = (x, y, z) of the plinth top centre, `forward` = horizontal unit
    vector of the figure's front. Returns the triangle count."""
    f = np.array([forward[0], forward[1], 0.0], float)
    f /= np.linalg.norm(f)
    r = np.array([f[1], -f[0], 0.0])
    M = np.stack([r, f, np.array([0.0, 0.0, 1.0])])          # rows: local x, y, z axes in world
    sc = sculpt(low)
    o = np.asarray(base, float)
    for mat, parts in sc.parts.items():
        for k, (V, T) in enumerate(parts):
            V, T, UV = _unwrap(V, T, *sc.uv.get((mat, k), (UV_RADIUS_M, 0.0)))
            acc.add(layer, (remap or {}).get(mat, mat), o + V @ M, T, UV)
    return sc.tris()


UV_RADIUS_M = 0.40           # mean radius of the cloak: u = metres round the figure at that radius
UV_SEAM_RAD = math.radians(6.0)


def _unwrap(V, T, radius=UV_RADIUS_M, y0=0.0):
    """Cylindrical UV0 in metres (u round the figure, v up) for the bronze set, whose rain streaks run along v. The
    seam is at the back; triangles across it get their own copies of the vertices one turn further."""
    # 0 near the front, the +-pi seam 6 degrees off the back centre (between two columns of the cloak, so no vertex
    # sits on it and round-off cannot flip its side)
    ang = (np.arctan2(V[:, 0], V[:, 1] - y0) - UV_SEAM_RAD + math.pi) % (2 * math.pi) - math.pi
    V2, A2, T2 = [V], [ang], T.copy()
    extra = {}
    for k, tri in enumerate(T):
        a = ang[tri]
        if a.max() - a.min() > math.pi:                  # crosses the back seam
            for j, vi in enumerate(tri):
                if ang[vi] < 0:
                    if vi not in extra:
                        extra[vi] = len(V) + len(extra)
                    T2[k, j] = extra[vi]
    if extra:
        idx = np.array(sorted(extra, key=extra.get))
        V2.append(V[idx])
        A2.append(ang[idx] + 2 * math.pi)
    Vn, An = np.concatenate(V2), np.concatenate(A2)
    return Vn, T2, np.column_stack([An * radius, Vn[:, 2]])
