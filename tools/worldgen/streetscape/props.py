"""Street-furniture prototypes (our own procedural meshes) -> art-source/world/props/street_props.glb.

Local frame of every prototype: x = right, y = front (the face a driver sees / the side toward the road),
z = up, origin at the ground point. Instances (streetscape.furniture) carry (E, N, U, yaw, scale_z) where
yaw rotates local +y onto the facing direction. Nodes: "<proto>" (LOD0), "<proto>.lod1", "<proto>.col"
(collision, simplified). Dimensions: roads.standards (cited / WORKING_VALUE).
"""

from __future__ import annotations

import math

import numpy as np

from roads import standards as S

from . import signs as SG


class Mesh:
    def __init__(self, pole_height=None):
        self.prims = {}
        self.pole_height = pole_height
        self.ground_z = 0.0          # ADR 0162: atlas v counts metres above this (a mast sunk under a viaduct)

    def add(self, mat, V, T, UV=None):
        V = np.asarray(V, float)
        UV = np.zeros((len(V), 2)) if UV is None else np.asarray(UV, float)
        p = self.prims.setdefault(mat, [[], [], []])
        off = sum(len(v) for v in p[0])
        p[0].append(V)
        p[1].append(np.asarray(T, np.int64).reshape(-1, 3) + off)
        p[2].append(UV)

    def tube(self, mat, p0, p1, r0, r1=None, seg=10, cap=True):
        r1 = r0 if r1 is None else r1
        p0, p1 = np.asarray(p0, float), np.asarray(p1, float)
        ax = p1 - p0
        L = np.linalg.norm(ax)
        ax /= L
        ref = np.array([0, 0, 1.0]) if abs(ax[2]) < 0.9 else np.array([1.0, 0, 0])
        u = np.cross(ax, ref)
        u /= np.linalg.norm(u)
        v = np.cross(ax, u)
        a = np.linspace(0, 2 * math.pi, seg + 1)
        ring = np.cos(a)[:, None] * u + np.sin(a)[:, None] * v
        V = np.concatenate([p0 + ring * r0, p1 + ring * r1])
        UV = np.column_stack([np.tile(a / (2 * math.pi), 2), np.repeat([0, L], seg + 1)])
        n = seg + 1
        T = [(i, i + 1, n + i + 1) for i in range(seg)] + [(i, n + i + 1, n + i) for i in range(seg)]
        self.add(mat, V, T, UV)
        if cap:
            self.add(mat, np.concatenate([[p1], p1 + ring[:-1] * r1]),
                     [(0, 1 + (i + 1) % seg, 1 + i) for i in range(seg)][::1])

    def box(self, mat, c, hx, hy, hz):
        c = np.asarray(c, float)
        P = [c + [sx * hx, sy * hy, sz * hz] for sz in (-1, 1) for sy in (-1, 1) for sx in (-1, 1)]
        faces = [(0, 2, 3, 1), (4, 5, 7, 6), (0, 1, 5, 4), (2, 6, 7, 3), (0, 4, 6, 2), (1, 3, 7, 5)]
        for f in faces:
            q = [P[i] for i in f]
            e1 = np.linalg.norm(q[1] - q[0])
            e2 = np.linalg.norm(q[3] - q[0])
            self.add(mat, q, [(0, 1, 2), (0, 2, 3)], [[0, 0], [e1, 0], [e1, e2], [0, e2]])

    def quad(self, mat, a, b, c, d, uv=((0, 0), (1, 0), (1, 1), (0, 1))):
        self.add(mat, [a, b, c, d], [(0, 1, 2), (0, 2, 3)], uv)

    def out(self):
        res = []
        for mat, (Vs, Ts, UVs) in sorted(self.prims.items()):
            V, UV = np.concatenate(Vs), np.concatenate(UVs)
            # ADR 0102: atlas height is the physical pole height, not one repeating dirt band every metre.
            if self.pole_height and mat in ("steel_galv", "steel_painted_grey", "concrete_pole", "steel_painted", "concrete_base"):
                mat = {"steel_galv": "furniture_galv", "steel_painted_grey": "furniture_grey",
                       "concrete_pole": "furniture_concrete", "steel_painted": "furniture_bollard",
                       "concrete_base": "furniture_footing"}[mat]
                atlas_height = 0.9 if self.pole_height <= 1 else 9.0
                UV = np.column_stack([UV[:, 0], np.clip((V[:, 2] - self.ground_z) / atlas_height, 0.002, 0.998)])
            res.append({"V": V, "T": np.concatenate(Ts), "UV": UV, "mat": mat})
        return res


LAMP_OLD = (("concrete", 9), ("steel", 8))     # (kind, height m) of the older side-street family

# ------------------------------------------------------------------------------------------- builders
# ZDM Białystok PFU (research G5-010 / G5-011 rows, SOURCED): galvanised tapered steel columns, luminaires "do 11 m",
# a door recess of at least 600 x 130 mm, the lowest ~0.3 m of the column painted grey (the paint band is drawn in
# the furniture_galv atlas, furniture_textures.pole_texture: no extra material). Door position UNVERIFIED: lower edge
# 0.5 m (WORKING_VALUE), on the side away from the road.
LAMP_DOOR = (0.60, 0.13)
LAMP_DOOR_Z = 0.5


def lamp(h, bracket, double=False):
    m, l1, col = Mesh(), Mesh(), Mesh()
    m.pole_height = l1.pole_height = h
    for mm, seg in ((m, 12), (l1, 6)):
        # ADR 0102: buried footing, 8 cm cap above the local surface. Same primitive/material budget.
        mm.box("concrete_base", [0, 0, -0.01], 0.25, 0.25, 0.09)
        mm.tube("steel_galv", [0, 0, 0.06], [0, 0, h - 0.3], 0.085, 0.040, seg)
        if seg > 6:                     # ADR 0162: door of the cable recess (same galv material, LOD0 only)
            r_door = 0.085 - 0.045 * (LAMP_DOOR_Z + LAMP_DOOR[0] / 2 - 0.06) / (h - 0.36)
            mm.box("steel_galv", [0, -r_door + 0.004, LAMP_DOOR_Z + LAMP_DOOR[0] / 2], LAMP_DOOR[1] / 2, 0.008,
                   LAMP_DOOR[0] / 2)
        for sgn in ((1, -1) if double else (1,)):
            top = np.array([0, 0, h - 0.4])
            end = np.array([0, sgn * bracket, h])
            mm.tube("steel_galv", top, end, 0.03, 0.03, seg // 2)
            mm.box("luminaire_housing", end + [0, sgn * 0.32, -0.03], 0.16, 0.34, 0.05)
            mm.quad("lamp_glass", end + [-0.13, sgn * 0.04, -0.081], end + [0.13, sgn * 0.04, -0.081],
                    end + [0.13, sgn * 0.6, -0.081], end + [-0.13, sgn * 0.6, -0.081])
    col.tube("collision_steel", [0, 0, 0], [0, 0, h], 0.12, 0.12, 6)
    return m, l1, col


# Luminaire height of the DK8 median columns above the road (ADR 0146), WORKING_VALUE 9.4-11.3 m: Mapillary
# 494288258686575 with the focal length measured in the frame (1900 px of 2048: 5.57 m lane-dash module of the 0.08 m
# orthophoto, eye 1.0 m from the 3.5 m lane) -> head 9.0 m above the eye = 10.0 m above the deck; orthophoto shadows:
# luminaire shadow on the NE deck 11.3 m, fork shadow of ground column 1 10.8 m at 1.05-1.13 m of shadow per metre.
LAMP_Y_H_M = 10.3
LAMP_MAST_SINK_M = 7.5        # WORKING_VALUE: deepest gap floor under the Putry decks is 6.2 m below the deck (NMT)
LAMP_Y_ARM_R_LOD1 = 0.06     # WORKING_VALUE (ADR 0146): arm radius of the Low mesh, so a 7-9 cm tube does not alias away


def lamp_y(h=10.3, reach=1.3, rise=1.0, console=False, sink=0.0):
    """Median double-arm column of DK8 / Andersa at Rondo Putry (ADR 0133, reshaped in ADR 0146): tapered galvanised
    column, two arms leaving the column top steeply and bending out in an arc to a flat LED housing on each side
    (+y and -y, across both carriageways). Luminaires at `h` above the origin.
    ADR 0146, GUGiK orthophoto 0.08 m (ground column at E -759.9 N 63.5): arm tips 3.8-4.0 m apart including the
    0.65 m housings (-> `reach` 1.3 m to the arm end), arm rise ~1.0 m (shadow of both arms); Mapillary
    494288258686575: rise / half span ~0.5, arc shape. WORKING_VALUE +-0.2 m.
    sink > 0: a mast standing on the ground in the gap between two decks (origin = deck level, shaft continues `sink`
    m below it into the ground under the viaduct, no footing in the mesh). console=True (ADR 0133, kept for other
    rows): column on a steel console bolted to the deck fascia on its +y side."""
    m, l1, col = Mesh(), Mesh(), Mesh()
    m.pole_height = l1.pole_height = h
    if sink > 0:                     # ADR 0162: the grey foot band of the galv atlas belongs on the real ground
        m.ground_z = l1.ground_z = -sink
    hj = h - rise
    for mm, seg, bends, r_arm in ((m, 12, 5, None), (l1, 6, 3, LAMP_Y_ARM_R_LOD1)):
        if console:
            mm.box("steel_galv", [0, 0, 0.015], 0.17, 0.17, 0.015)                      # base plate on the console
            mm.box("steel_galv", [0, 0.105, -0.17], 0.13, 0.255, 0.17)                 # console into the fascia
        elif sink <= 0:
            mm.box("concrete_base", [0, 0, -0.01], 0.25, 0.25, 0.09)
        z0 = -sink if sink > 0 else (0.03 if console else 0.06)
        r_base = 0.095 + 0.0035 * sink                                                # same taper continued downward
        mm.tube("steel_galv", [0, 0, z0], [0, 0, hj + 0.12], r_base, 0.055, seg)
        for sgn in (1, -1):
            pts = [np.array([0.0, 0.0, hj])]
            for k in range(1, bends + 1):                # quarter ellipse: vertical at the column, flat at the housing
                a = k / bends * math.pi / 2
                pts.append(np.array([0.0, sgn * reach * (1 - math.cos(a)), hj + rise * math.sin(a)]))
            for k, (a_, b_) in enumerate(zip(pts[:-1], pts[1:])):
                r0 = r_arm or (0.045 - 0.010 * k / bends)
                r1 = r_arm or (0.045 - 0.010 * (k + 1) / bends)
                mm.tube("steel_galv", a_, b_, r0, r1, max(4, seg // 2), cap=False)
            end = pts[-1]
            mm.box("luminaire_housing", end + [0, sgn * 0.32, -0.03], 0.16, 0.34, 0.05)
            mm.quad("lamp_glass", end + [-0.13, sgn * 0.04, -0.081], end + [0.13, sgn * 0.04, -0.081],
                    end + [0.13, sgn * 0.6, -0.081], end + [-0.13, sgn * 0.6, -0.081])
    col.tube("collision_steel", [0, 0, -sink], [0, 0, hj], 0.12, 0.12, 6)
    return m, l1, col


def lamp_old(h, kind):
    """Second lamp family for side streets (critic R2 #10): older installations still common on Polish residential
    and industrial access roads (shapes typical, no product copied; dimensions WORKING_VALUE).
      kind "concrete": spun-concrete pole (żerdź wirowana, 0.30 -> 0.14 m) with a steel arm rising in an arc and an
        elongated "cobra" sodium luminaire (orange-tinted bowl);
      kind "steel":    thin grey-painted steel pole with a straight arm tilted up 15 deg and a box luminaire."""
    m, l1, col = Mesh(), Mesh(), Mesh()
    m.pole_height = l1.pole_height = h
    for mm, seg in ((m, 10), (l1, 5)):
        if kind == "concrete":
            mm.tube("concrete_pole", [0, 0, -0.3], [0, 0, 0], 0.15, 0.15, seg, cap=False)
            mm.tube("concrete_pole", [0, 0, 0], [0, 0, h], 0.15, 0.07, seg)
            pts = [np.array([0.0, 0.05, h - 1.4])]
            bends = 6 if seg > 5 else 3
            for k in range(1, bends + 1):              # same silhouette, fewer sections on Low
                a = k / bends * math.pi / 2
                pts.append(np.array([0.0, 0.05 + 1.2 * math.sin(a), h - 1.4 + 1.0 * (1 - math.cos(a)) + 0.35 * math.sin(a)]))
            pts.append(pts[-1] + [0, 0.5, 0.06])
            for a_, b_ in zip(pts[:-1], pts[1:]):
                mm.tube("steel_painted_grey", a_, b_, 0.03, 0.03, max(4, seg // 2), cap=False)
            for zb in (h - 1.4, h - 0.7):               # clamp bands
                rr = 0.15 - 0.08 * zb / h + 0.004
                mm.tube("steel_painted_grey", [0, 0, zb], [0, 0, zb + 0.08], rr, rr, seg, cap=False)
            e = pts[-1]
            # A sloped, bevelled sodium housing rather than a flat LED box; same 12 housing triangles.
            # Generic proportions, WORKING_VALUE; no manufacturer's model or branding.
            housing = e + np.array([[-.11,.06,-.10], [.11,.06,-.10], [-.12,.66,-.10], [.12,.66,-.10],
                                    [-.17,-.05,.10], [.17,-.05,.10], [-.16,.78,.06], [.16,.78,.06]])
            faces = [(0,2,3,1), (4,5,7,6), (0,1,5,4), (2,6,7,3), (0,4,6,2), (1,3,7,5)]
            triangles = [t for a,b,c,d in faces for t in ((a,b,c),(a,c,d))]
            mm.add("luminaire_old", housing, triangles)
            mm.quad("lamp_glass_sodium", e + [-.10,.09,-.102], e + [-.11,.63,-.102],
                    e + [.11,.63,-.102], e + [.10,.09,-.102])
        else:
            mm.box("concrete_base", [0, 0, -0.01], 0.2, 0.2, 0.09)
            mm.tube("steel_painted_grey", [0, 0, 0.06], [0, 0, h - 0.2], 0.075, 0.05, seg)
            if seg > 5:
                mm.box("steel_painted_grey", [0, -0.073, 0.55], 0.033, 0.005, 0.13)  # flush service hatch
            top = np.array([0, 0, h - 0.35])
            end = top + np.array([0, 1.4 * math.cos(math.radians(15)), 1.4 * math.sin(math.radians(15))])
            mm.tube("steel_painted_grey", top, end, 0.03, 0.03, max(4, seg // 2))
            mm.box("luminaire_old", end + [0, 0.28, 0.0], 0.14, 0.3, 0.07)
            mm.quad("lamp_glass_sodium", end + [-0.11, 0.04, -0.072], end + [0.11, 0.04, -0.072],
                    end + [0.11, 0.52, -0.072], end + [-0.11, 0.52, -0.072])
    col.tube("collision_steel", [0, 0, 0], [0, 0, h],
             0.16 if kind == "concrete" else 0.13, 0.08 if kind == "concrete" else 0.13, 6)
    return m, l1, col


def lamp_arc(h=9.0, reach=2.2, double=False):
    """Arched single / double arm column ("pastoral"): tapered galvanised steel column, arm rising in one continuous
    arc to `reach`, elongated sodium "cobra" luminaire. The lamp family of the Kwadrat Park access road and yard
    (CC0 photo 20210904_101250, Rakoon, Commons: tall arched columns along the lane; reference only, proportions
    by eye: column ~9 m, arm ~2 m; WORKING_VALUE). Arm along +y."""
    m, l1, col = Mesh(), Mesh(), Mesh()
    m.pole_height = l1.pole_height = h
    for mm, seg in ((m, 10), (l1, 5)):
        mm.box("concrete_base", [0, 0, -0.01], 0.28, 0.28, 0.09)
        mm.tube("steel_galv", [0, 0, 0.08], [0, 0, 1.1], 0.095, 0.085, seg)             # base section with the hatch
        mm.tube("steel_galv", [0, 0, 1.1], [0, 0, h - 1.6], 0.075, 0.045, seg)
        if seg > 5:
            mm.box("steel_galv", [0, -0.092, 0.62], 0.045, 0.006, 0.16)                 # service hatch
            mm.tube("steel_galv", [0, 0, 1.08], [0, 0, 1.13], 0.10, 0.08, seg)          # collar
        for sgn in ((1, -1) if double else (1,)):
            pts = [np.array([0.0, 0.0, h - 1.6])]
            n = 8 if seg > 5 else 4
            for k in range(1, n + 1):                                                    # quarter ellipse up and out
                a = k / n * math.pi / 2
                pts.append(np.array([0.0, sgn * reach * (1 - math.cos(a)), h - 1.6 + 1.6 * math.sin(a)]))
            for a_, b_ in zip(pts[:-1], pts[1:]):
                mm.tube("steel_galv", a_, b_, 0.04, 0.035, max(4, seg // 2), cap=False)
            e = pts[-1]
            mm.box("luminaire_old", e + [0, sgn * 0.34, -0.02], 0.13, 0.38, 0.07)
            mm.quad("lamp_glass_sodium", e + [-0.10, sgn * 0.05, -0.092], e + [0.10, sgn * 0.05, -0.092],
                    e + [0.10, sgn * 0.66, -0.092], e + [-0.10, sgn * 0.66, -0.092])
    col.tube("collision_steel", [0, 0, 0], [0, 0, h], 0.13, 0.13, 6)
    return m, l1, col


def sign_post():
    m, l1, col = Mesh(), Mesh(), Mesh()
    # Render only a short buried end: the instance scales z by its height (sz up to ~5). Real underground
    # foundation depth is not a render-mesh dimension; long hidden ends confuse lowest-point contact audits.
    m.tube("steel_galv", [0, 0, -0.03], [0, 0, 1.0], S.SIGN_POST_D / 2, None, 10)
    l1.tube("steel_galv", [0, 0, -0.03], [0, 0, 1.0], S.SIGN_POST_D / 2, None, 4)
    col.tube("collision_steel", [0, 0, 0], [0, 0, 1.0], 0.05, None, 4)
    return m, l1, col


def plate(code):
    """Sign plate centred at (0, 0, 0), facing +y, on the post (axis at y = 0).

    Polish plates are aluminium sheet with a folded (double-bent) edge, ~25 mm deep (catalogue practice,
    WORKING_VALUE): face (retroreflective foil, our weathered texture), rim, grey mill-finish back with a label
    (signs.plate_back) and two galvanised clamps (obejmy) around the Ø60 mm post."""
    shape, _ = SG.face(code)
    size = S.SIGN_SIZE[shape]
    m, l1 = Mesh(), Mesh()
    rim = 0.025
    y = S.SIGN_POST_D / 2 + 0.012 + rim             # face; the back clears the post by 12 mm
    n = {"disc": 32, "octagon": 8, "triangle": 3, "diamond": 4, "square": 4}[shape]
    r = size / 2
    if shape == "triangle":         # inverted triangle (A-7), side = size
        h = size * math.sqrt(3) / 2
        pts2 = [(-size / 2, h / 3), (size / 2, h / 3), (0, -2 * h / 3)]
        top = (512 - 496 * math.sqrt(3) / 2) / 2          # signs.a7(): side 496 px centred in 512
        uvs = [(8 / 512, 1 - top / 512), (504 / 512, 1 - top / 512), (0.5, 1 - (512 - top) / 512)]
    else:
        rot = {"disc": 0, "octagon": math.pi / 8, "diamond": 0, "square": math.pi / 4}[shape]
        rr = r * (1 / math.cos(math.pi / 4) if shape == "square" else 1)
        pts2 = [(rr * math.cos(rot + 2 * math.pi * k / n), rr * math.sin(rot + 2 * math.pi * k / n)) for k in range(n)]
        if shape == "square":
            pts2 = [(max(-r, min(r, x)), max(-r, min(r, z))) for x, z in pts2]
        uvs = [(0.5 + x / size, 0.5 + z / size) for x, z in pts2]
    # one winding for every shape (clockwise in (x, z), as the triangle): the counter-clockwise discs / octagons /
    # squares had their face culled from the front, so B-33 / C-12 showed the grey back to the driver (review r4 W-H3:
    # "one grey plate seen from behind")
    area2 = sum(pts2[k][0] * pts2[(k + 1) % len(pts2)][1] - pts2[(k + 1) % len(pts2)][0] * pts2[k][1] for k in range(len(pts2)))
    if area2 > 0:
        pts2, uvs = pts2[::-1], uvs[::-1]
    k_ = len(pts2)
    hh = size * (math.sqrt(3) / 2 if shape == "triangle" else 1.0)
    for mm, full in ((m, True), (l1, False)):
        V = [[0, y, 0]] + [[x, y, z] for x, z in pts2]
        # u runs against local +x: seen from the front (+y) in Unity, local +x is on the viewer's left (the C-12 arrows
        # turned clockwise and digits would read mirrored; checked on route-putry-entry-signs, ADR 0023)
        UV = [(0.5, 0.5)] + [(1.0 - u, v) for u, v in uvs]
        T = [(0, 1 + (k + 1) % k_, 1 + k) for k in range(k_)]
        T = [(a, c, b) for a, b, c in T]        # face +y
        mm.add(f"sign_{code}", V, T, UV)
        yb = y - rim if full else y - 0.004
        Vb = [[0, yb, 0]] + [[x, yb, z] for x, z in pts2]
        # ADR0120: one 1 m atlas width, with the same normalised clamp heights for every shape.
        # The 0.6 vertical inset keeps the A-7 centroid-based triangle inside the texture.
        UVb = [(0.5, 0.5)] + [(0.5 - x, 0.5 + 0.6 * z / hh) for x, z in pts2]
        mm.add("plate_back", Vb, [(0, 1 + (k + 1) % k_, 1 + k) for k in range(k_)], UVb)
        if full:                                    # folded rim (outward normals)
            Vr, Tr, UVr = [], [], []
            for k in range(k_):
                (x0, z0), (x1, z1) = pts2[k], pts2[(k + 1) % k_]
                o = len(Vr)
                Vr += [[x0, y, z0], [x1, y, z1], [x1, yb, z1], [x0, yb, z0]]
                UVr += [(0.05, 0.05), (0.20, 0.05), (0.20, 0.20), (0.05, 0.20)]
                Tr += [(o, o + 2, o + 1), (o, o + 3, o + 2), (o, o + 1, o + 2), (o, o + 2, o + 3)]   # both sides
            mm.add("plate_back", Vr, Tr, UVr)
    for zc in (-hh * 0.28, hh * 0.22):              # clamps around the post, behind the plate
        m.box("steel_galv", [0, 0.0, zc], S.SIGN_POST_D / 2 + 0.008, S.SIGN_POST_D / 2 + 0.008, 0.022)
        m.box("steel_galv", [0, (S.SIGN_POST_D / 2 + y - rim) / 2 + 0.004, zc], 0.06, (y - rim - S.SIGN_POST_D / 2) / 2, 0.018)
    # ADR0120 r2: retain rear mounting hardware on Low without another material slot.
    # Low reuses its EXISTING plate_back slot. steel_galv would add a draw on every Low sign.
    # Two simple rear spacers stand in for the High collar/rail assembly: 24 triangles total.
    hardware = Mesh()
    for zc in (-hh * 0.28, hh * 0.22):
        hardware.box("plate_back", [0, 0.012, zc], 0.065, y - 0.004 - 0.012, 0.018)
    for part in hardware.out():
        l1.add("plate_back", part["V"], part["T"], np.full((len(part["V"]), 2), 0.10))
    return m, l1, None


# ADR 0162 (budget): OB code -> v height of the plain grey back band that export.py appends under the board face in
# the board's own texture. Face, back sheet and rails then share ONE material: 1 instanced draw per board, not 3
# (the 3 new al. Tysiąclecia portals added 5 boards = +15 draws on the Putry approach cameras).
BOARD_BAND = {}
BOARD_BAND_PX = 16
BOARD_BACK_SRGB = (126, 128, 128)        # = materials "board_back" colour 0.21/0.22/0.22 linear (ADR 0127 plain back)


def board(code, w, h):
    m = Mesh()
    y = 0.06
    band = BOARD_BAND.get(code) if code.startswith("OB_") else None
    v0 = band or 0.0
    # face normal +y like the plates (the old winding showed every E-2 / gantry board's grey back to the driver)
    m.quad(f"sign_{code}", [-w / 2, y, -h / 2], [-w / 2, y, h / 2], [w / 2, y, h / 2], [w / 2, y, -h / 2],
           uv=((1, v0), (1, 1), (0, 1), (0, v0)))   # u mirrored as on the plates
    if band:
        # overhead board with a back band: back sheet + rails sample the band centre (plain grey, ADR 0127)
        buv = (0.5, band / 2)
        m.quad(f"sign_{code}", [w / 2, y - 0.01, -h / 2], [w / 2, y - 0.01, h / 2], [-w / 2, y - 0.01, h / 2],
               [-w / 2, y - 0.01, -h / 2], uv=(buv,) * 4)
        tmp = Mesh()
        for sx in (-1, 1):
            tmp.box("rail", [sx * w / 2 * 0.7, 0.02, 0], 0.03, 0.03, h / 2)
        for V, T, _ in zip(*tmp.prims["rail"]):
            m.add(f"sign_{code}", V, T - T.min(), np.tile(buv, (len(V), 1)))
        return m, m, None
    # overhead boards (gantries, "OB_") without a band: plain grey sheet back (ADR 0127), other boards the plate back
    m.quad("board_back" if code.startswith("OB_") else "plate_back",
           [w / 2, y - 0.01, -h / 2], [w / 2, y - 0.01, h / 2], [-w / 2, y - 0.01, h / 2],
           [-w / 2, y - 0.01, -h / 2],
           uv=((0.05, 0.05), (0.05, 0.20), (0.20, 0.20), (0.20, 0.05)))
    for sx in (-1, 1):
        m.box("steel_galv", [sx * w / 2 * 0.7, 0.02, 0], 0.03, 0.03, h / 2)   # rails (Z-profile)
    return m, m, None


def signal_head(lit):
    """S-1 three-aspect head (Ø300 mm lenses) with a black contrast back plate and white border."""
    m, l1 = Mesh(), Mesh()
    for mm in (m, l1):
        mm.box("signal_housing", [0, 0.0, 0], 0.18, 0.13, 0.52)
        mm.box("signal_backplate", [0, -0.14, 0], 0.33, 0.01, 0.68)
        mm.box("signal_border", [0, -0.152, 0], 0.36, 0.002, 0.71)
    for k, col in enumerate(("red", "yellow", "green")):
        z = 0.34 - k * 0.34
        on = col == lit
        mat = f"signal_{col}_{'on' if on else 'off'}"
        n = 16
        pts = [(0.15 * math.cos(2 * math.pi * i / n), 0.15 * math.sin(2 * math.pi * i / n)) for i in range(n)]
        V = [[0, 0.135, z]] + [[x, 0.135, z + zz] for x, zz in pts]
        T = [(0, 1 + i, 1 + (i + 1) % n) for i in range(n)]
        m.add(mat, V, T)
        l1.add(mat, V, T)
        m.box("signal_housing", [0, 0.25, z + 0.13], 0.17, 0.12, 0.01)      # visor (simplified)
    return m, l1, None


def signal_pole(h=S.SIGNAL_POLE_H, arm=0.0):
    """S-1 pole, or (arm > 0) a mast with a curved arm (ADR 0069, Mapillary p42 / p45 / p47 2024: the tapered pole
    bends over in a ~1.5 m radius into a horizontal arm; the arm is at h - 0.4). Arm along local +y."""
    m, l1, col = Mesh(), Mesh(), Mesh()
    R = S.SIGNAL_MAST_BEND_R
    za = h - 0.4                                        # arm axis height
    for mm, seg, nb in ((m, 10, 6), (l1, 5, 2)):
        if not arm:
            mm.tube("steel_galv", [0, 0, -0.1], [0, 0, h], 0.07, 0.06, seg)
            continue
        mm.tube("steel_galv", [0, 0, -0.1], [0, 0, za - R], 0.13, 0.11, seg, cap=False)
        prev, r_prev = np.array([0.0, 0.0, za - R]), 0.11
        for k in range(1, nb + 1):                      # quarter bend: centre (0, R, za - R)
            a = 0.5 * math.pi * k / nb
            q = np.array([0.0, R - R * math.cos(a), za - R + R * math.sin(a)])
            r = 0.11 - 0.03 * k / nb
            mm.tube("steel_galv", prev, q, r_prev, r, seg, cap=False)
            prev, r_prev = q, r
        mm.tube("steel_galv", prev, [0, arm, za], r_prev, 0.05, seg, cap=True)
    col.tube("collision_steel", [0, 0, 0], [0, 0, h], 0.15, None, 6)
    return m, l1, col


# ---------------------------------------------------------------- BKM bus shelter (ADR 0162, research G5)
# Białystok city shelters, BKM "Wzór plastyczny wiaty przystankowej" (SIWZ 2019 zał. 1 / 2020 zał. 6, research
# G5-001 / G5-005, SOURCED): modular steel frame, module 2 m; roof length n x 2 m + "dwa występy boczne zadaszenia po
# min 0,5 m" -> 5 / 7 / 9 m for 2 / 3 / 4 modules (3 modules = the standard shelter); 2.6 m from the pavement to the
# roof; wall 1.07 m deep, roof 0.55 m beyond the back posts and 1.4 m from the back posts to the road-side edge; glass
# 0.6 x 0.99 m, lowest edge 0.15 m above the pavement; bench seat 0.4 m, 2 seat slats + 3 back slats; two lit
# timetable cases in the back wall of the module opposite the bench; gutter along the low edge with a downpipe; frame
# powder-coated RAL 3020 (traffic red); roof smoked multiwall polycarbonate. D-15 rack (zał. 07c, G5-004, typ B over
# the roof): panel 0.55 x 0.805 m. Read off the drawings, WORKING_VALUE: roof rise 0.25 m toward the road (2019 side
# view: 0.26 m over 1.7 m; 2020: 0.21 m over 1.95 m), post section 80 x 60 mm, frame bars 40 mm, timetable case
# 0.92 x 0.78 m with its lower edge at 1.1 m (2020 elevation "1,1 m"). The older black shelters (Commons, ul. Lipowa,
# G5-020) are the same frame in graphite - their share is WORKING_VALUE (furniture.SHELTER_BLACK_SHARE).
SHELTER_MODULE_M = 2.0
SHELTER_SIDE_OVERHANG_M = 0.5
SHELTER_H_M = 2.6
SHELTER_WALL_D_M = 1.07
SHELTER_BACK_OVERHANG_M = 0.55
SHELTER_ROOF_FROM_BACK_M = 1.4
SHELTER_PANE_W_M, SHELTER_PANE_H_M = 0.99, 0.6
SHELTER_PANE_BOTTOM_M = 0.15
SHELTER_SEAT_H_M = 0.4
SHELTER_ROOF_RISE_M = 0.25          # WORKING_VALUE
SHELTER_POST = (0.08, 0.06)         # WORKING_VALUE (profile zamknięte o przekroju prostokątnym)
SHELTER_BAR = 0.04                  # WORKING_VALUE
D15_RACK_W_M, D15_RACK_H_M = 0.55, 0.805
SHELTER_MODULES = {"bus_shelter_5m": 2, "bus_shelter": 3, "bus_shelter_9m": 4}
# shelter atlas (furniture_textures.shelter_atlas, 512 x 512, v up): uv of the flat swatches and the picture regions
SHELTER_UV = {"red": (0.125, 0.94), "black": (0.375, 0.94), "wood": (0.625, 0.94), "roof": (0.875, 0.94)}
SHELTER_UV_BAND = (0.0, 0.76, 1.0, 0.86)          # blue information board on the road-side roof edge
SHELTER_UV_TIMETABLE = (0.02, 0.27, 0.48, 0.73)   # timetable poster behind the case glass
SHELTER_UV_D15 = (0.53, 0.25, 0.87, 0.75)         # D-15 rack face (0.55 x 0.805 m)


def _flat_copy(dst, mat, uv, src):
    """Copy every primitive of `src` into `dst` as `mat` with one constant uv (a flat atlas swatch)."""
    for _, (Vs, Ts, _) in sorted(src.prims.items()):
        V = np.concatenate(Vs)
        dst.add(mat, V, np.concatenate(Ts), np.tile(np.asarray(uv, float), (len(V), 1)))


def _uv_quad(mm, mat, a, b, c, d, reg):
    """Quad a-b-c-d mapped to the atlas rectangle reg = (u0, v0, u1, v1): a -> (u0, v0), b -> (u1, v0), c -> (u1, v1),
    d -> (u0, v1). Seen from the front, local +x is on the viewer's left (props.plate), so a is the bottom corner on
    +x when the image must read left to right."""
    u0, v0, u1, v1 = reg
    mm.quad(mat, a, b, c, d, uv=((u0, v0), (u1, v0), (u1, v1), (u0, v1)))


def bus_shelter_bkm(modules=3, colour="red"):
    """BKM shelter (constants above). Local frame: +y = the road side (the open front and the high roof edge), origin
    on the pavement in the middle of the wall depth. Materials: shelter_paint (one atlas for the frame, roof sheet,
    bench, timetable posters, information board and D-15 rack) and shelter_glass_clear - two slots (the old generic
    shelter had four): every slot is a draw per prototype on Low."""
    paint = SHELTER_UV[colour]
    L = modules * SHELTER_MODULE_M
    RL = L + 2 * SHELTER_SIDE_OVERHANG_M
    yb, yf = -SHELTER_WALL_D_M / 2, SHELTER_WALL_D_M / 2              # back / front post lines
    y_back_edge = yb - SHELTER_BACK_OVERHANG_M
    y_front_edge = yb + SHELTER_ROOF_FROM_BACK_M
    z0 = SHELTER_H_M                                                   # roof underside at the low (back) edge

    def zr(y):                                                         # roof underside above the pavement at y
        return z0 + SHELTER_ROOF_RISE_M * (y - y_back_edge) / (y_front_edge - y_back_edge)

    m, l1, col = Mesh(), Mesh(), Mesh()
    fr, fr1 = Mesh(), Mesh()                                           # frame (flat paint), LOD0 / LOD1
    px, py = SHELTER_POST[0] / 2, SHELTER_POST[1] / 2
    xs = [-L / 2 + k * SHELTER_MODULE_M for k in range(modules + 1)]
    for x in xs:
        for y in (yb, yf):
            fr.box("p", [x, y, zr(y) / 2], px, py, zr(y) / 2)
            fr1.box("p", [x, y, zr(y) / 2], px, py, zr(y) / 2)
    b = SHELTER_BAR / 2
    z_rows = [SHELTER_PANE_BOTTOM_M + k * SHELTER_PANE_H_M for k in range(4)]   # 0.15 / 0.75 / 1.35 / 1.95
    for z in z_rows:                                                   # back wall rails and the side wall rails
        fr.box("p", [0, yb, z], L / 2, b, b)
        for x in (-L / 2, L / 2):
            fr.box("p", [x, 0, z], b, SHELTER_WALL_D_M / 2, b)
    fr1.box("p", [0, yb, z_rows[-1]], L / 2, b, b)
    for k in range(modules):                                           # one mullion per module: 2 panes of 0.99 m
        xm = -L / 2 + (k + 0.5) * SHELTER_MODULE_M
        fr.box("p", [xm, yb, (z_rows[0] + z_rows[-1]) / 2], b, b, (z_rows[-1] - z_rows[0]) / 2)
    # roof frame: low back edge, high road-side fascia, end rafters and one rafter per post pair, Y brackets at the
    # back posts carrying the 0.55 m overhang (2019 / 2020 side views)
    for mm in (fr, fr1):
        mm.box("p", [0, y_back_edge + 0.03, z0 + 0.03], RL / 2, 0.03, 0.04)
        mm.box("p", [0, y_front_edge - 0.03, zr(y_front_edge) + 0.04], RL / 2, 0.03, 0.06)
    for x in [-RL / 2 + 0.03] + xs + [RL / 2 - 0.03]:
        fr.tube("p", [x, y_back_edge, z0 + 0.04], [x, y_front_edge, zr(y_front_edge) + 0.04], 0.03, None, 4, cap=False)
    for x in xs:
        fr.tube("p", [x, yb, z0 - 0.42], [x, y_back_edge + 0.08, z0 + 0.02], 0.025, None, 4, cap=False)
        fr.tube("p", [x, yb, z0 - 0.42], [x, yb + 0.25, zr(yb + 0.25) + 0.02], 0.025, None, 4, cap=False)
    # gutter along the low edge and the downpipe to the pavement at the -x end
    fr.tube("p", [-RL / 2, y_back_edge - 0.04, z0 - 0.02], [RL / 2, y_back_edge - 0.04, z0 - 0.02], 0.045, None, 6)
    fr.tube("p", [-L / 2 - 0.12, y_back_edge - 0.04, z0 - 0.06], [-L / 2 - 0.12, yb - 0.1, 0.05], 0.035, None, 6)
    # D-15 rack over the roof (typ B) at the +x end, panel across the road direction, readable from both sides
    xr, yr = L / 2 - 0.2, y_front_edge - 0.45
    zr0 = zr(yr) + 0.15
    for mm in (fr, fr1):
        mm.box("p", [xr, yr - D15_RACK_W_M / 2 - 0.03, (zr0 + D15_RACK_H_M + zr(yr)) / 2], 0.03, 0.03,
               (zr0 + D15_RACK_H_M - zr(yr)) / 2)
    _flat_copy(m, "shelter_paint", paint, fr)
    _flat_copy(l1, "shelter_paint", paint, fr1)
    for mm in (m, l1):
        for sx in (1, -1):                                             # D-15 faces, back to back
            x = xr + sx * 0.012
            a = [x, yr + sx * D15_RACK_W_M / 2, zr0]
            bb = [x, yr - sx * D15_RACK_W_M / 2, zr0]
            _uv_quad(mm, "shelter_paint", a, bb, [bb[0], bb[1], zr0 + D15_RACK_H_M],
                     [a[0], a[1], zr0 + D15_RACK_H_M], SHELTER_UV_D15)
        # blue information board along the road-side roof edge (no logo, no text of a real operator)
        yf_b = y_front_edge + 0.005
        zb0 = zr(y_front_edge) - 0.02
        _uv_quad(mm, "shelter_paint", [L / 2 + 0.3, yf_b, zb0], [-L / 2 - 0.3, yf_b, zb0],
                 [-L / 2 - 0.3, yf_b, zb0 + 0.24], [L / 2 + 0.3, yf_b, zb0 + 0.24], SHELTER_UV_BAND)
    # timetable cases: two in the back wall of the +x module (the viewer's left seen from the road), faces +y
    for mm in (m, l1):
        for k in range(2 if mm is m else 1):
            xc = L / 2 - SHELTER_MODULE_M * (0.27 + 0.48 * k)
            tmp = Mesh()
            tmp.box("p", [xc, yb + 0.045, 1.1 + 0.39], 0.46, 0.03, 0.39)
            _flat_copy(mm, "shelter_paint", paint, tmp)
            y = yb + 0.077
            _uv_quad(mm, "shelter_paint", [xc + 0.42, y, 1.14], [xc - 0.42, y, 1.14], [xc - 0.42, y, 1.84],
                     [xc + 0.42, y, 1.84], SHELTER_UV_TIMETABLE)
    # bench in the -x module: 2 seat slats 160 x 45 mm at 0.4 m, 3 back slats 80 x 30 mm, two brackets on the wall
    tw, t1 = Mesh(), Mesh()
    xb = -L / 2 + SHELTER_MODULE_M / 2
    for k in range(2):
        tw.box("p", [xb, yb + 0.12 + k * 0.175, SHELTER_SEAT_H_M - 0.0225], 0.92, 0.08, 0.0225)
    for k in range(3):
        tw.box("p", [xb, yb + 0.05, SHELTER_SEAT_H_M + 0.2 + k * 0.13], 0.92, 0.015, 0.04)
    t1.box("p", [xb, yb + 0.2, SHELTER_SEAT_H_M - 0.0225], 0.92, 0.17, 0.0225)
    _flat_copy(m, "shelter_paint", SHELTER_UV["wood"], tw)
    _flat_copy(l1, "shelter_paint", SHELTER_UV["wood"], t1)
    br = Mesh()
    for x in (xb - 0.75, xb + 0.75):
        br.box("p", [x, yb + 0.2, SHELTER_SEAT_H_M / 2], 0.02, 0.02, SHELTER_SEAT_H_M / 2)
        br.box("p", [x, yb + 0.18, SHELTER_SEAT_H_M - 0.06], 0.02, 0.16, 0.015)
    _flat_copy(m, "shelter_paint", paint, br)
    # glass: back wall and both side walls, one double-sided sheet each between the lowest and the highest rail;
    # UV0 v = 1 at the foot -> 0 at the top (road film of the clear-sheet shader, as the noise screens)
    zg0, zg1 = z_rows[0], z_rows[-1]
    for mm in (m, l1):
        sheets = [([L / 2, yb, zg0], [-L / 2, yb, zg0], [-L / 2, yb, zg1], [L / 2, yb, zg1])]
        for x in (-L / 2, L / 2):
            sheets.append(([x, yf, zg0], [x, yb, zg0], [x, yb, zg1], [x, yf, zg1]))
        for a, bq, c, d in sheets:
            uv = ((0, 1), (1, 1), (1, 0), (0, 0))
            mm.quad("shelter_glass_clear", a, bq, c, d, uv=uv)
            mm.quad("shelter_glass_clear", bq, a, d, c, uv=((1, 1), (0, 1), (0, 0), (1, 0)))
    # roof sheet (double sided: seen from under the shelter and from a truck cab above)
    for mm in (m, l1):
        a = [RL / 2, y_back_edge, z0 + 0.06]
        bq = [-RL / 2, y_back_edge, z0 + 0.06]
        c = [-RL / 2, y_front_edge, zr(y_front_edge) + 0.06]
        d = [RL / 2, y_front_edge, zr(y_front_edge) + 0.06]
        ru = (SHELTER_UV["roof"],) * 4                  # smoked polycarbonate swatch of the atlas (one slot less)
        mm.quad("shelter_paint", d, c, bq, a, uv=ru)
        mm.quad("shelter_paint", a, bq, c, d, uv=ru)
    # collision: the walled part up to the roof, the roof slab (a truck mirror reaches 2.6-2.9 m)
    col.box("collision_steel", [0, 0, z0 / 2], L / 2 + 0.05, SHELTER_WALL_D_M / 2 + 0.05, z0 / 2)
    col.box("collision_steel", [0, (y_back_edge + y_front_edge) / 2, (z0 + zr(y_front_edge)) / 2 + 0.05], RL / 2,
            (y_front_edge - y_back_edge) / 2, (zr(y_front_edge) - z0) / 2 + 0.1)
    return m, l1, col


def bus_shelter():
    """Default prototype "bus_shelter": the standard BKM shelter of 3 modules (7 m roof), red RAL 3020."""
    return bus_shelter_bkm(3, "red")


# ---------------------------------------------------------------- road barriers of the ZDM standard (ADR 0162, G5)
# ZDM Białystok, standard 2018 (research G5-010, SOURCED): panel U-12a "olsztyński": two posts of Ø60.3 mm galvanised
# tube 2.0 m apart, 1.10 m above the ground (1.50 m long), a loop of Ø48.3 mm tube between them, 0.64 m high (G5
# manifest), painted yellow RAL 1012. Segment fence U-12: 2.50 x 0.83 m (5 flat horizontal wires 15 x 6 mm, verticals
# every 5 cm), yellow RAL 1012, posts 60 x 40 mm red RAL 3020 (post height WORKING_VALUE). Pylon U-5a: polyethylene,
# yellow RAL 1012 with retroreflective foil, 0.90 m high, Ø0.20 m, base 0.30 m. Placed only where data shows them:
# the region's OSM / BDOT10k carry none (no barrier=guard_rail / handrail / bollard=U-5a), so ADR 0162 builds the
# prototypes and places none; a placement needs a photo-read authored run first (backlog in the ADR).
U12A_POST_D = 0.0603
U12A_RAIL_D = 0.0483
U12A_BAY_M = 2.0
U12A_H_M = 1.10
U12A_LOOP_H_M = 0.64
U12_PANEL = (2.50, 0.83)
U5A_H_M, U5A_D_M, U5A_BASE_M = 0.90, 0.20, 0.30


def railing_u12a():
    """One 2.0 m bay of U-12a, post at local x = -1.0 (a run adds the closing post as `railing_u12a_post`); the bay
    runs along local x, origin at the ground under the bay centre."""
    m, l1, col = Mesh(), Mesh(), Mesh()
    for mm, seg, bends in ((m, 8, 5), (l1, 4, 2)):
        mm.tube("paint_ral1012", [-U12A_BAY_M / 2, 0, -0.05], [-U12A_BAY_M / 2, 0, U12A_H_M], U12A_POST_D / 2, None, seg)
        r = U12A_LOOP_H_M / 2
        ztop = U12A_H_M - 0.03
        zc = ztop - r
        xa, xb = -U12A_BAY_M / 2 + U12A_POST_D / 2 + r, U12A_BAY_M / 2 - U12A_POST_D / 2 - r
        loop = []
        for k in range(bends + 1):                                    # right end: half circle, top -> bottom
            a = math.pi / 2 - math.pi * k / bends
            loop.append([xb + r * math.cos(a), 0, zc + r * math.sin(a)])
        for k in range(bends + 1):                                    # left end: bottom -> top
            a = -math.pi / 2 - math.pi * k / bends
            loop.append([xa + r * math.cos(a), 0, zc + r * math.sin(a)])
        loop.append(loop[0])
        for p0, p1 in zip(loop[:-1], loop[1:]):
            mm.tube("paint_ral1012", p0, p1, U12A_RAIL_D / 2, None, max(4, seg - 2), cap=False)
    col.box("collision_steel", [0, 0, U12A_H_M / 2], U12A_BAY_M / 2, 0.04, U12A_H_M / 2)
    return m, l1, col


def railing_u12a_post():
    m, l1 = Mesh(), Mesh()
    m.tube("paint_ral1012", [0, 0, -0.05], [0, 0, U12A_H_M], U12A_POST_D / 2, None, 8)
    l1.tube("paint_ral1012", [0, 0, -0.05], [0, 0, U12A_H_M], U12A_POST_D / 2, None, 4)
    return m, l1, None


def fence_u12():
    """One U-12 segment (2.50 x 0.83 m) between two red posts; origin at the ground under the segment centre."""
    m, l1, col = Mesh(), Mesh(), Mesh()
    w, h = U12_PANEL
    z0 = 0.12                                                         # WORKING_VALUE: clearance under the segment
    for mm, verticals in ((m, True), (l1, False)):
        for x in (-w / 2, w / 2):
            mm.box("paint_ral3020", [x, 0, (z0 + h + 0.05) / 2 - 0.02], 0.02, 0.03, (z0 + h + 0.05) / 2)
        for k in range(5):
            mm.box("paint_ral1012", [0, 0, z0 + k * h / 4], w / 2 - 0.02, 0.003, 0.0075)
        if verticals:
            for x in np.arange(-w / 2 + 0.05, w / 2 - 0.01, 0.05):
                mm.box("paint_ral1012", [x, 0, z0 + h / 2], 0.0025, 0.0025, h / 2)
        else:
            mm.quad("paint_ral1012", [w / 2, 0, z0], [-w / 2, 0, z0], [-w / 2, 0, z0 + h], [w / 2, 0, z0 + h])
            mm.quad("paint_ral1012", [-w / 2, 0, z0], [w / 2, 0, z0], [w / 2, 0, z0 + h], [-w / 2, 0, z0 + h])
    col.box("collision_steel", [0, 0, (z0 + h) / 2], w / 2, 0.04, (z0 + h) / 2)
    return m, l1, col


def pylon_u5a():
    m, l1, col = Mesh(), Mesh(), Mesh()
    for mm, seg in ((m, 12), (l1, 6)):
        mm.tube("paint_ral1012", [0, 0, 0], [0, 0, 0.06], U5A_BASE_M / 2, U5A_BASE_M / 2, seg)
        mm.tube("paint_ral1012", [0, 0, 0.06], [0, 0, U5A_H_M - 0.15], U5A_D_M / 2, U5A_D_M / 2 * 0.85, seg, cap=False)
        mm.tube("paint_white_reflective", [0, 0, U5A_H_M - 0.15], [0, 0, U5A_H_M - 0.04], U5A_D_M / 2 * 0.85,
                U5A_D_M / 2 * 0.8, seg, cap=False)
        mm.tube("paint_ral1012", [0, 0, U5A_H_M - 0.04], [0, 0, U5A_H_M], U5A_D_M / 2 * 0.8, U5A_D_M / 2 * 0.6, seg)
    col.tube("collision_steel", [0, 0, 0], [0, 0, U5A_H_M], U5A_D_M / 2, None, 6)
    return m, l1, col


def lift_gate():
    m, col = Mesh(), Mesh()
    m.box("steel_painted", [0, 0, 0.5], 0.17, 0.17, 0.5)
    m.box("gate_boom", [2.6, 0, 0.95], 2.5, 0.035, 0.05)
    m.box("steel_galv", [5.2, 0, 0.45], 0.04, 0.04, 0.45)
    col.box("collision_steel", [0, 0, 0.5], 0.17, 0.17, 0.5)
    return m, m, col


def sliding_gate(w=8.0):
    m, col = Mesh(), Mesh()
    m.box("fence_green", [0, 0, 1.0], w / 2, 0.03, 0.04)
    m.box("fence_green", [0, 0, 0.1], w / 2, 0.03, 0.04)
    for x in np.arange(-w / 2, w / 2 + 0.01, 0.12):
        m.box("fence_green", [x, 0, 1.0], 0.012, 0.012, 0.95)
    for x in (-w / 2 - 0.2, w / 2 + 0.2):
        m.box("fence_green", [x, 0, 1.05], 0.06, 0.06, 1.05)
    col.box("collision_steel", [0, 0, 1.0], w / 2, 0.05, 1.0)
    return m, m, col


def bollard():
    m, col = Mesh(), Mesh()
    m.pole_height = 0.9
    m.tube("steel_painted", [0, 0, -0.1], [0, 0, 0.9], 0.06, None, 10)
    m.tube("paint_white_reflective", [0, 0, 0.75], [0, 0, 0.82], 0.062, None, 10, cap=False)
    col.tube("collision_steel", [0, 0, 0], [0, 0, 0.9], 0.07, None, 6)
    return m, m, col


def hoop_bollard():
    """OSM barrier=cycle_barrier / bollard=hoop only; no invented placements. Dimensions WORKING_VALUE."""
    m, l1, col = Mesh(1.0), Mesh(1.0), Mesh()
    for mm, seg, bends in ((m, 8, 6), (l1, 4, 3), (col, 4, 3)):
        mat = "collision_steel" if mm is col else "steel_painted"
        for x in (-0.45, 0.45):
            mm.tube(mat, [x, 0, -0.3], [x, 0, 0.8], 0.03, seg=seg, cap=False)
        pts = [[0.45 * math.cos(k * math.pi / bends), 0, 0.8 + 0.2 * math.sin(k * math.pi / bends)]
               for k in range(bends + 1)]
        for a, b in zip(pts[:-1], pts[1:]):
            mm.tube(mat, a, b, 0.03, seg=seg, cap=False)
    return m, l1, col


def power_pole():
    """Spun-concrete distribution pole. ADR 0162: ONE height for the mesh, the wire attachment (furniture.power_lines)
    and the deck-clearance check (standards.GROUND_PROP_H["power_pole"], was 10 m against this 12 m mesh). No source
    gives the pole series of the region (research G5: UNVERIFIED); 12.0 m above the ground stays WORKING_VALUE."""
    H = S.GROUND_PROP_H["power_pole"]
    m, l1, col = Mesh(), Mesh(), Mesh()
    for mm, seg in ((m, 8), (l1, 4)):
        mm.tube("concrete_pole", [0, 0, -0.5], [0, 0, H], 0.16, 0.09, seg)
        mm.box("steel_galv", [0, 0, H - 0.5], 0.9, 0.05, 0.05)
        for x in (-0.8, 0, 0.8):
            mm.tube("insulator", [x, 0, H - 0.45], [x, 0, H - 0.15], 0.04, 0.04, 6)
    col.tube("collision_steel", [0, 0, 0], [0, 0, H], 0.2, None, 6)
    return m, l1, col


# 110 kV double-circuit lattice tower (ADR 0127). Shape read off Mapillary 3678296072299092 (grobin 2019, the tower
# at region-local E,N = -369,-69 beside Andersa): slender square shaft, three cross-arm levels of about equal
# length, a short peak with the earth wire. BDOT10k OT_BUWT_P carries no height: total 32 m, arm levels and lengths
# are WORKING_VALUE (typical 110 kV double-circuit series; arm spacing ~4 m, lowest arm ~20 m).
PYLON_ARM_Z = (20.0, 24.0, 28.0)     # cross-arm levels (m above ground) for h = 32
PYLON_ARM_L = 4.3                    # arm tip from the axis (m): 8.6 m tip to tip on the GUGiK hi-res orthophoto of
#                                      the tower at Andersa (ADR 0139, artifacts/g3b-r2/crops/ortho-pylon-hr.jpg); was 3.3
PYLON_INSULATOR_M = 1.3              # suspension string: conductor hangs this far under the arm tip
PYLON_PANELS = (0.0, 4.5, 8.5, 12.0, 15.0, 17.5, 20.0, 22.0, 24.0, 26.0, 28.0, 30.0)
PYLON_PANELS_LOD1 = (0.0, 6.5, 12.0, 16.5, 20.0, 22.0, 24.0, 26.0, 28.0, 30.0)


def pylon_half_width(z, h=32.0):
    """Half width of the square shaft at height z: 2.3 m at the foot, 0.75 m under the lowest arm, 0.45 m at the
    top arm, closing to the peak."""
    k = h / 32.0
    return float(np.interp(z, [0.0, 19.0 * k, 29.0 * k, h], [2.3, 0.75, 0.45, 0.08]))


def pylon(h=32.0):
    """LOD0: legs + horizontal and X lacing per panel, trussed arms, insulator strings. LOD1 (from 80 m x lodBias,
    i.e. 40 m on Low): the same silhouette with 3-sided members about 1.6 x thicker and no horizontals, so the
    shaft still reads as a dark lattice at 150-400 m instead of dissolving into single pixels (review s11-0125 P1)."""
    m, l1, col = Mesh(), Mesh(), Mesh()
    k = h / 32.0
    mat = "pylon_steel"
    faces = (((-1, -1), (1, -1)), ((1, -1), (1, 1)), ((1, 1), (-1, 1)), ((-1, 1), (-1, -1)))
    for lod, mm in enumerate((m, l1)):
        r_leg, r_lace, seg = ((0.085, 0.035, 4), (0.13, 0.06, 3))[lod]
        zs = [z * k for z in (PYLON_PANELS, PYLON_PANELS_LOD1)[lod]] + [h]
        for z0, z1 in zip(zs[:-1], zs[1:]):
            w0, w1 = pylon_half_width(z0, h), pylon_half_width(z1, h)
            for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
                mm.tube(mat, [sx * w0, sy * w0, z0], [sx * w1, sy * w1, z1], r_leg, None, seg, cap=False)
            if z1 >= h - 1e-6:
                continue                                       # peak: legs only
            for (ax, ay), (bx_, by) in faces:
                mm.tube(mat, [ax * w0, ay * w0, z0], [bx_ * w1, by * w1, z1], r_lace, None, 3, cap=False)
                mm.tube(mat, [bx_ * w0, by * w0, z0], [ax * w1, ay * w1, z1], r_lace, None, 3, cap=False)
                if lod == 0:
                    mm.tube(mat, [ax * w1, ay * w1, z1], [bx_ * w1, by * w1, z1], r_lace, None, 3, cap=False)
        for za in PYLON_ARM_Z:
            za *= k
            w = pylon_half_width(za, h)
            wu = pylon_half_width(za + 1.3 * k, h)
            for sx in (-1, 1):
                tip = [sx * PYLON_ARM_L, 0.0, za]
                for sy in (-1, 1):                              # two bottom chords + two ties from 1.3 m above
                    mm.tube(mat, [sx * w, sy * w, za], tip, r_leg * 0.8, None, seg, cap=False)
                    mm.tube(mat, [sx * wu, sy * wu, za + 1.3 * k], tip, r_lace * 1.3, None, 3, cap=False)
                if lod == 0:
                    mm.tube("insulator", tip, [tip[0], 0.0, za - PYLON_INSULATOR_M], 0.07, None, 6)
                else:
                    mm.tube("insulator", tip, [tip[0], 0.0, za - PYLON_INSULATOR_M], 0.08, None, 3, cap=False)
    b = pylon_half_width(0.0, h)
    col.box("collision_steel", [0, 0, h / 2], b, b, h / 2)
    return m, l1, col


def bench():
    m = Mesh()
    m.box("bench_wood", [0, 0, 0.45], 0.9, 0.22, 0.025)
    m.box("bench_wood", [0, -0.2, 0.75], 0.9, 0.02, 0.12)
    for x in (-0.75, 0.75):
        m.box("steel_painted", [x, 0, 0.22], 0.03, 0.2, 0.22)
    return m, m, None


def waste_bin():
    m = Mesh()
    m.tube("steel_painted", [0, 0, 0.0], [0, 0, 0.75], 0.2, 0.22, 12)
    m.tube("steel_galv", [0, 0, -0.3], [0, 0, 0.9], 0.03, None, 6)
    return m, m, None


def street_cabinet():
    m, col = Mesh(), Mesh()
    m.box("cabinet_grey", [0, 0, 0.7], 0.45, 0.2, 0.7)
    col.box("collision_steel", [0, 0, 0.7], 0.45, 0.2, 0.7)
    return m, m, col


def build_all(sign_codes, boards):
    """{proto: (lod0 Mesh, lod1 Mesh, collision Mesh|None)} for every prototype used."""
    P = {}
    for cls, d in S.LAMP.items():
        P[f"lamp_{int(d['h'])}m"] = lamp(d["h"], d["bracket"])
    for kind, hh in LAMP_OLD:
        P[f"lamp_old_{kind}_{hh}m"] = lamp_old(float(hh), kind)
    P["lamp_arc_9m"] = lamp_arc(9.0)
    P["lamp_arc_9m_double"] = lamp_arc(9.0, double=True)
    # ADR 0133 / 0146: DK8 median row (authored lamp_rows.json). Luminaires LAMP_Y_H_M above the road; in the gap
    # between the decks the mast stands on the ground under the viaduct (LAMP_MAST_SINK_M of shaft below deck level).
    P["lamp_double_10m"] = lamp_y(LAMP_Y_H_M)
    P["lamp_double_mast_10m"] = lamp_y(LAMP_Y_H_M, sink=LAMP_MAST_SINK_M)
    P["sign_post"] = sign_post()
    for c in sorted(sign_codes):
        P[f"plate_{c}"] = plate(c)
    for c, (w, h) in sorted(boards.items()):
        P[f"board_{c}"] = board(c, w, h)
    for lit in ("red", "green", "off"):          # off: emergency signals at rest (ADR 0074)
        P[f"signal_head_{lit}"] = signal_head(lit)
    P["signal_pole"] = signal_pole()
    P["signal_mast"] = signal_pole(S.SIGNAL_MAST_H, 6.0)
    for name, n in SHELTER_MODULES.items():          # ADR 0162: BKM 5 / 7 / 9 m red, older 7 m graphite
        P[name] = bus_shelter_bkm(n, "red")
    P["bus_shelter_black"] = bus_shelter_bkm(3, "black")
    P["railing_u12a"] = railing_u12a()
    P["railing_u12a_post"] = railing_u12a_post()
    P["fence_u12"] = fence_u12()
    P["pylon_u5a"] = pylon_u5a()
    P["lift_gate"] = lift_gate()
    P["sliding_gate"] = sliding_gate()
    P["bollard"] = bollard()
    P["bollard_hoop"] = hoop_bollard()
    P["power_pole"] = power_pole()
    P["pylon"] = pylon()
    P["bench"] = bench()
    P["waste_bin"] = waste_bin()
    P["street_cabinet"] = street_cabinet()
    from . import life_props as LP
    P.update(LP.build_all())
    P.update(LP.build_registered())
    from . import gate3_landmarks as G3          # ADR 0125: sign assemblies registered by gate3_landmarks.build
    P.update(G3.prototypes())
    return P
