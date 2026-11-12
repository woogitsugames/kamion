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
            c = len(V)
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
                UV = np.column_stack([UV[:, 0], np.clip(V[:, 2] / atlas_height, 0.002, 0.998)])
            res.append({"V": V, "T": np.concatenate(Ts), "UV": UV, "mat": mat})
        return res


LAMP_OLD = (("concrete", 9), ("steel", 8))     # (kind, height m) of the older side-street family

# ------------------------------------------------------------------------------------------- builders
def lamp(h, bracket, double=False):
    m, l1, col = Mesh(), Mesh(), Mesh()
    m.pole_height = l1.pole_height = h
    for mm, seg in ((m, 12), (l1, 6)):
        # ADR 0102: buried footing, 8 cm cap above the local surface. Same primitive/material budget.
        mm.box("concrete_base", [0, 0, -0.01], 0.25, 0.25, 0.09)
        mm.tube("steel_galv", [0, 0, 0.06], [0, 0, h - 0.3], 0.085, 0.040, seg)
        for sgn in ((1, -1) if double else (1,)):
            top = np.array([0, 0, h - 0.4])
            end = np.array([0, sgn * bracket, h])
            mm.tube("steel_galv", top, end, 0.03, 0.03, seg // 2)
            mm.box("luminaire_housing", end + [0, sgn * 0.32, -0.03], 0.16, 0.34, 0.05)
            mm.quad("lamp_glass", end + [-0.13, sgn * 0.04, -0.081], end + [0.13, sgn * 0.04, -0.081],
                    end + [0.13, sgn * 0.6, -0.081], end + [-0.13, sgn * 0.6, -0.081])
    col.tube("collision_steel", [0, 0, 0], [0, 0, h], 0.12, 0.12, 6)
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
    return m, l1, None


def board(code, w, h):
    m = Mesh()
    y = 0.06
    # face normal +y like the plates (the old winding showed every E-2 / gantry board's grey back to the driver)
    m.quad(f"sign_{code}", [-w / 2, y, -h / 2], [-w / 2, y, h / 2], [w / 2, y, h / 2], [w / 2, y, -h / 2],
           uv=((1, 0), (1, 1), (0, 1), (0, 0)))   # u mirrored as on the plates
    m.quad("plate_back", [w / 2, y - 0.01, -h / 2], [w / 2, y - 0.01, h / 2], [-w / 2, y - 0.01, h / 2],
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


def bus_shelter():
    m, col = Mesh(), Mesh()
    W, D, H = 4.0, 1.5, 2.5
    for x in (-W / 2, 0, W / 2):
        for y in (-D / 2, D / 2):
            m.box("steel_painted", [x, y, H / 2], 0.04, 0.04, H / 2)
    m.box("shelter_roof", [0, 0.05, H + 0.05], W / 2 + 0.1, D / 2 + 0.2, 0.05)
    # glass back wall and side walls
    m.quad("shelter_glass", [W / 2, -D / 2, 0.15], [-W / 2, -D / 2, 0.15], [-W / 2, -D / 2, H - 0.1], [W / 2, -D / 2, H - 0.1])
    m.quad("shelter_glass", [-W / 2, -D / 2, 0.15], [W / 2, -D / 2, 0.15], [W / 2, -D / 2, H - 0.1], [-W / 2, -D / 2, H - 0.1])
    for x in (-W / 2, W / 2):
        m.quad("shelter_glass", [x, -D / 2, 0.15], [x, D / 2 - 0.3, 0.15], [x, D / 2 - 0.3, H - 0.1], [x, -D / 2, H - 0.1])
        m.quad("shelter_glass", [x, D / 2 - 0.3, 0.15], [x, -D / 2, 0.15], [x, -D / 2, H - 0.1], [x, D / 2 - 0.3, H - 0.1])
    m.box("bench_wood", [0, -D / 2 + 0.3, 0.45], 1.2, 0.2, 0.03)
    m.box("steel_painted", [0, -D / 2 + 0.3, 0.22], 1.0, 0.03, 0.22)
    col.box("collision_steel", [0, 0, H / 2], W / 2, D / 2, H / 2)
    return m, m, col


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
    m, l1, col = Mesh(), Mesh(), Mesh()
    for mm, seg in ((m, 8), (l1, 4)):
        mm.tube("concrete_pole", [0, 0, -0.5], [0, 0, 12.0], 0.16, 0.09, seg)
        mm.box("steel_galv", [0, 0, 11.5], 0.9, 0.05, 0.05)
        for x in (-0.8, 0, 0.8):
            mm.tube("insulator", [x, 0, 11.55], [x, 0, 11.85], 0.04, 0.04, 6)
    col.tube("collision_steel", [0, 0, 0], [0, 0, 12.0], 0.2, None, 6)
    return m, l1, col


def pylon(h=32.0):
    m, col = Mesh(), Mesh()
    b, t = 3.2, 0.8
    for sx in (-1, 1):
        for sy in (-1, 1):
            m.tube("steel_galv_dark", [sx * b, sy * b, 0], [sx * t, sy * t, h], 0.08, 0.06, 4)
    for z in np.arange(3, h - 1, 3.5):
        f = z / h
        w = b + (t - b) * f
        for a, c in (((-w, -w), (w, -w)), ((w, -w), (w, w)), ((w, w), (-w, w)), ((-w, w), (-w, -w))):
            m.tube("steel_galv_dark", [a[0], a[1], z], [c[0], c[1], z], 0.03, 0.03, 3, cap=False)
            m.tube("steel_galv_dark", [a[0], a[1], z], [c[0] * 0.95, c[1] * 0.95, z + 3.5], 0.025, 0.025, 3, cap=False)
    for zz, L in ((h * 0.72, 6.0), (h * 0.86, 4.5)):
        m.tube("steel_galv_dark", [-L, 0, zz], [L, 0, zz], 0.08, 0.08, 4)
    col.box("collision_steel", [0, 0, h / 2], b, b, h / 2)
    return m, m, col


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
    P["sign_post"] = sign_post()
    for c in sorted(sign_codes):
        P[f"plate_{c}"] = plate(c)
    for c, (w, h) in sorted(boards.items()):
        P[f"board_{c}"] = board(c, w, h)
    for lit in ("red", "green", "off"):          # off: emergency signals at rest (ADR 0074)
        P[f"signal_head_{lit}"] = signal_head(lit)
    P["signal_pole"] = signal_pole()
    P["signal_mast"] = signal_pole(S.SIGNAL_MAST_H, 6.0)
    P["bus_shelter"] = bus_shelter()
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
