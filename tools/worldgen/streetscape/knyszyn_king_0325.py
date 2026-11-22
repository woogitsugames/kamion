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

LOD0 ~2.9 k triangles in three bronze materials (base, patina for fur / ruff / beard, rubbed for crown and chains);
LOD1 ~0.3 k (cloak, head, crown, ruff, lapels) in one.
"""
from __future__ import annotations

import math

import numpy as np

BRONZE, PATINA, RUBBED = "monument_bronze", "monument_bronze_patina", "monument_bronze_rubbed"
H_SHOULDER = 2.40            # top of the straight part of the cloak
H_NECK = 2.54                # cloak closes under the ruff
H_BAND0, H_BAND1 = 2.865, 2.935     # crown band
H_TOP = 3.05                 # tips of the tall fleurons
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

    def add(self, mat, V, T, orient=None):
        """orient: None = as wound; "centre" = away from the piece's centroid (small convex pieces); "axis" = away
        from the vertical axis of the figure (pieces lying on the cloak)."""
        V, T = np.asarray(V, float).reshape(-1, 3), np.asarray(T, int).reshape(-1, 3)
        if orient:
            n = np.cross(V[T[:, 1]] - V[T[:, 0]], V[T[:, 2]] - V[T[:, 0]])
            d = V[T].mean(1) - (V.mean(0) if orient == "centre" else [0.0, 0.0, 0.0])
            if orient == "axis":
                d[:, 2] = 0.0
            T = np.where((np.einsum("ij,ij->i", n, d) < 0)[:, None], T[:, ::-1], T)
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
        self.add(mat, V, T + [(a, c, b) for a, b, c in T])

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


def _ellipse_ring(z, w, f, b, angles, y0=HEAD_Y, pinch=None):
    """Head section: half width w, front depth f, back depth b; pinch = {angle: radial offset}."""
    ring = []
    for th in angles:
        a = math.radians(th)
        c, s = math.cos(a), math.sin(a)
        d = f if s >= 0 else b
        r = (abs(c / w) ** 2.3 + abs(s / d) ** 2.3) ** (-1 / 2.3) + (pinch or {}).get(th, 0.0)
        ring.append([r * c, r * s + y0, z])
    return ring


HEAD_COLS0 = (0, 30, 55, 72, 82, 90, 98, 108, 125, 150, 180, 215, 250, 290, 325)
HEAD_COLS1 = (0, 60, 90, 120, 180, 270)
# z, half width, front depth, back depth, pinch {angle: radial offset}: eye sockets, bridge of the nose, mouth
HEAD_RINGS = ((2.50, .074, .074, .076, None), (2.585, .078, .080, .082, None),
              (2.615, .096, .104, .094, None),                                    # jaw under the beard
              (2.655, .110, .120, .104, {90: .004}),                              # chin
              (2.700, .117, .123, .114, {72: -.003, 108: -.003}),                 # mouth, cheeks
              (2.745, .121, .121, .123, {55: .004, 125: .004, 82: -.004, 98: -.004}),             # cheekbones
              (2.790, .122, .114, .128, {55: -.008, 72: -.020, 82: -.014, 98: -.014, 108: -.020, 125: -.008, 90: .002}),  # sockets
              (2.828, .124, .127, .131, {72: .004, 108: .004}),                   # brow ridge
              (2.870, .123, .121, .131, None),                                    # forehead, under the band
              (2.930, .112, .108, .120, None), (2.965, .070, .066, .080, None))


def _head_r(th, z):
    """Radius of the head loft at an angle / height (linear between the rings), for pieces lying on it."""
    rows = HEAD_RINGS
    k = max(i for i, r in enumerate(rows) if r[0] <= z + 1e-9)
    k = min(k, len(rows) - 2)
    u = (z - rows[k][0]) / (rows[k + 1][0] - rows[k][0])
    def rad(row):
        _, w, f, b, _ = row
        a = math.radians(th)
        c, s_ = math.cos(a), math.sin(a)
        d = f if s_ >= 0 else b
        return (abs(c / w) ** 2.3 + abs(s_ / d) ** 2.3) ** (-1 / 2.3)
    return rad(rows[k]) * (1 - u) + rad(rows[k + 1]) * u


def _on_head(th, z, lift=0.0):
    r = _head_r(th, z) + lift
    a = math.radians(th)
    return [r * math.cos(a), r * math.sin(a) + HEAD_Y, z]


def _head(sc, low):
    cols = HEAD_COLS1 if low else HEAD_COLS0
    rows = HEAD_RINGS[::2] if low else HEAD_RINGS          # 11 rings: every second one keeps the first and the last
    sc.loft(BRONZE, [_ellipse_ring(z, w, f, b, cols, pinch=None if low else pc) for z, w, f, b, pc in rows], cap_top=True)
    if low:      # beard and hair as one dark collar so the head keeps its two tones far away
        sc.loft(PATINA, [[_on_head(th, z, 0.012) for th in (20, 60, 90, 120, 160)] for z in (2.56, 2.69)], closed=False,
                orient="axis")
        return
    f = HEAD_Y + 0.121
    # nose: narrow bridge between the eyes, broad tip, nostril wings
    nose = [[0, f - 0.004, 2.832], [-0.011, f - 0.012, 2.808], [0.011, f - 0.012, 2.808], [0, f + 0.046, 2.740],
            [-0.025, f - 0.002, 2.728], [0.025, f - 0.002, 2.728], [0, f + 0.016, 2.720], [0, f + 0.022, 2.790]]
    sc.add(BRONZE, nose, [(0, 1, 7), (0, 7, 2), (1, 4, 7), (7, 4, 3), (2, 7, 5), (7, 3, 5), (4, 6, 3), (6, 5, 3),
                          (1, 2, 5), (1, 5, 4), (4, 5, 6)], orient="centre")
    for sx in (-1, 1):
        # brow: a bar sloping to the temple, overhanging the socket
        a = np.array([sx * 0.010, f + 0.006, 2.822])
        b = np.array([sx * 0.088, f - 0.036, 2.812])
        up, out = np.array([0, 0, 0.020]), np.array([0, 0.016, 0])
        V = [a, b, b + up, a + up, a + out, b + out + [0, 0.006, 0], b + up + out, a + up + out]
        T = [(4, 5, 6), (4, 6, 7), (3, 7, 6), (3, 6, 2), (0, 5, 4), (0, 1, 5), (1, 6, 5), (1, 2, 6), (0, 4, 7), (0, 7, 3)]
        sc.add(BRONZE, V, T, orient="centre")
        # eye: lids as a shallow lens in the socket, the dark slit between them in patina
        ex = sx * 0.046
        ey = f - 0.021
        lid = [[ex - 0.024, ey - 0.004, 2.792], [ex, ey + 0.010, 2.803], [ex + 0.024, ey - 0.004, 2.792], [ex, ey + 0.010, 2.781]]
        sc.add(BRONZE, lid + [[ex, ey + 0.016, 2.792]], [(0, 4, 1), (1, 4, 2), (2, 4, 3), (3, 4, 0)], orient="centre")
        slit = [[ex - 0.019, ey + 0.0105, 2.7915], [ex, ey + 0.0185, 2.7955], [ex + 0.019, ey + 0.0105, 2.7915], [ex, ey + 0.0185, 2.7885]]
        sc.add(PATINA, slit, [(0, 1, 3), (1, 2, 3)], orient="axis")
        # ear, half hidden by the hair
        c = np.array([sx * 0.124, HEAD_Y - 0.004, 2.760])
        V = [c + [0, 0.016, -0.030], c + [0, 0.020, 0.026], c + [0, -0.012, 0.030], c + [0, -0.010, -0.026],
             c + [sx * 0.020, -0.014, 0.004]]
        sc.add(BRONZE, V, [(0, 1, 4), (1, 2, 4), (2, 3, 4), (3, 0, 4)], orient="centre")
    # hair: a thick cap from temple to temple round the back, below the crown band
    hair_cols = (196, 212, 230, 250, 270, 290, 310, 328, 344)
    sc.loft(BRONZE, [[_on_head(th, z, lift) for th in hair_cols] for z, lift in
                     ((2.640, 0.002), (2.690, 0.016), (2.790, 0.018), (2.866, 0.008))], closed=False, orient="axis")
    # beard: from the sideburns round the jaw, thick over the chin, ending in a point over the ruff; moustache
    jaw_cols = (28, 46, 62, 78, 90, 102, 118, 134, 152)
    def jz(th):          # the beard line climbs to the ears at the sides
        return 2.668 + 0.075 * (abs(th - 90) / 62.0) ** 1.6
    top = [_on_head(th, jz(th), 0.002) for th in jaw_cols]
    bulge = [_on_head(th, jz(th) - 0.034, 0.016 + 0.012 * (1 - abs(th - 90) / 62.0)) for th in jaw_cols]
    low_ = [[x * 0.52, HEAD_Y + (y - HEAD_Y) * 0.92 + 0.010, 2.592 + 0.05 * abs(x) / 0.11] for x, y, _ in bulge]
    tip = [[x * 0.14, HEAD_Y + 0.112, 2.530] for x, _, _ in bulge]
    sc.loft(BRONZE, [tip, low_, bulge, top], closed=False, orient="axis")
    m = [[-0.052, f - 0.018, 2.694], [-0.026, f + 0.008, 2.712], [0, f + 0.012, 2.708], [0.026, f + 0.008, 2.712],
         [0.052, f - 0.018, 2.694], [0.026, f + 0.006, 2.692], [0, f + 0.010, 2.696], [-0.026, f + 0.006, 2.692]]
    sc.add(BRONZE, m, [(0, 7, 1), (7, 6, 1), (1, 6, 2), (6, 3, 2), (6, 5, 3), (5, 4, 3)], orient="axis")
    lip = [[-0.022, f + 0.003, 2.684], [0, f + 0.012, 2.686], [0.022, f + 0.003, 2.684], [0, f + 0.010, 2.674]]
    sc.add(BRONZE, lip, [(0, 3, 1), (1, 3, 2)], orient="axis")


def _ruff(sc, low):
    n = 8 if low else 26
    R, zc = 0.168, 2.560
    rings = [[], [], [], []]
    for i in range(n):
        a = 2 * math.pi * i / n
        wob = 0.0 if low else (0.010 if i % 2 else -0.010)
        c, s = math.cos(a), math.sin(a)
        for k, (dr, dz) in enumerate(((-0.060, 0.012), (0.0, 0.034 + wob), (0.022, 0.0), (0.0, -0.030 + wob))):
            rings[k].append([(R + dr) * c, (R * 0.96 + dr) * s + HEAD_Y * 0.7, zc + dz + (0.012 if s > 0 else 0) * (-s)])
    sc.loft(PATINA, [rings[3], rings[2], rings[1], rings[0]])


def _crown(sc, low):
    n = 6 if low else 12
    def ring(z, grow):
        return [[(0.128 + grow) * math.cos(2 * math.pi * i / n), (0.136 + grow) * math.sin(2 * math.pi * i / n) + HEAD_Y - 0.004, z]
                for i in range(n)]
    if low:
        sc.loft(RUBBED, [ring(H_BAND0, 0.0), ring(H_BAND1, 0.006)])
    else:        # band with a rolled lower edge, rim and inner face
        sc.loft(RUBBED, [ring(H_BAND0 - 0.004, -0.004), ring(H_BAND0 + 0.008, 0.006), ring(H_BAND0 + 0.018, 0.0),
                         ring(H_BAND1, 0.007), ring(H_BAND1 + 0.004, -0.004), ring(H_BAND1 - 0.03, -0.014)])
    k = 6 if low else 8
    for i in range(k):
        a = 2 * math.pi * (i + 0.5) / k + (0 if low else math.pi / 8 - math.pi / 8)
        c, s = math.cos(a), math.sin(a)
        base = np.array([0.134 * c, 0.142 * s + HEAD_Y - 0.004, H_BAND1 - 0.004])
        t = np.array([-s, c, 0.0])
        out = np.array([c, s, 0.0])
        tall = i % 2 == 0
        h = (H_TOP - H_BAND1) if tall else 0.072
        if low:
            sc.plate(RUBBED, [base - t * 0.04, base + t * 0.04, base + out * 0.012 + [0, 0, h]])
            continue
        w = 0.040 if tall else 0.030
        pts = [(-w, 0.0), (w, 0.0), (w * 0.5, h * 0.26), (w * 1.05, h * 0.58), (w * 0.42, h * 0.80), (0.0, h),
               (-w * 0.42, h * 0.80), (-w * 1.05, h * 0.58), (-w * 0.5, h * 0.26)]
        sc.plate(RUBBED, [base + t * u + np.array([0, 0, v]) + out * (0.016 * (v / h) ** 1.5) for u, v in pts])
        if tall:     # pearl between the fleurons, on the rim
            b2 = 2 * math.pi * (i + 1.0) / k
            sc.tube(RUBBED, [[0.132 * math.cos(b2), 0.140 * math.sin(b2) + HEAD_Y - 0.004, H_BAND1 - 0.01],
                             [0.132 * math.cos(b2), 0.140 * math.sin(b2) + HEAD_Y - 0.004, H_BAND1 + 0.022]], [0.011, 0.007], 4)


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
    sc.add(RUBBED, V, [(0, 1 + (i + 1) % 8, 1 + i) for i in range(8)], orient="axis")


def sculpt(low=False):
    """Local-space figure; z = 0 on the plinth."""
    sc = Sculpt()
    _cloak(sc, low)
    _head(sc, low)
    _ruff(sc, low)
    _crown(sc, low)
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
        for V, T in parts:
            V, T, UV = _unwrap(V, T)
            acc.add(layer, (remap or {}).get(mat, mat), o + V @ M, T, UV)
    return sc.tris()


UV_RADIUS_M = 0.40           # mean radius of the cloak: u = metres round the figure at that radius
UV_SEAM_RAD = math.radians(6.0)


def _unwrap(V, T):
    """Cylindrical UV0 in metres (u round the figure, v up) for the bronze set, whose rain streaks run along v. The
    seam is at the back; triangles across it get their own copies of the vertices one turn further."""
    # 0 near the front, the +-pi seam 6 degrees off the back centre (between two columns of the cloak, so no vertex
    # sits on it and round-off cannot flip its side)
    ang = (np.arctan2(V[:, 0], V[:, 1]) - UV_SEAM_RAD + math.pi) % (2 * math.pi) - math.pi
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
    return Vn, T2, np.column_stack([An * UV_RADIUS_M, Vn[:, 2]])
