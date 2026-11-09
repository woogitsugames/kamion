"""Track A2 — three silhouette concepts of the fictional EU 4x2 tractor (blockout level).

Run headless (Blender 4.2 LTS):
    blender -b --factory-startup --python tools/blender/truck/concepts.py -- \
        --concept A --out docs/reports/visual/truck-A2

Everything is generated from code; there is no hand-edited .blend.
Conventions (blockout scene, Blender Z-up): 1 unit = 1 m, truck faces +Y,
driver side (LHD) = -X, origin = ground point under the front axle centre.
Unity export axes are handled in a later step (A3+), not here.
Dimensions come from art-source/truck/dims.json (sources/WORKING_VALUE there).
"""
import argparse
import json
import math
import os
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
DIMS = json.load(open(os.path.join(REPO, "art-source", "truck", "dims.json"), encoding="utf-8"))


def D(key):
    return DIMS["values"][key]["value"]


# ---------------------------------------------------------------- dims
WB = D("wheelbase_m")                 # 3.70
TYRE_D = D("tyre_diameter_m")         # 1.0755
TYRE_W = D("tyre_section_width_m")    # 0.315
TYRE_R = TYRE_D / 2
WHEEL_Z = D("static_loaded_radius_m")  # wheel centre height
FRONT_TRACK = D("front_track_m")
REAR_TRACK = D("rear_track_m")
DUAL_SPACING = D("dual_spacing_m")
FIFTH_H = D("fifth_wheel_height_m")
FIFTH_LEAD = D("fifth_wheel_lead_m")
REAR_OH = D("rear_overhang_m")
CAB_BACK_Y = -D("cab_back_behind_front_axle_m")
CAB_HALF_W = D("cab_width_m") / 2
CAB_FLOOR_Z = D("cab_body_bottom_m")
ROOF_Z = D("overall_height_m")
FRAME_HALF_W = D("frame_width_outer_m") / 2
FRAME_TOP = D("frame_top_height_m")
RIM_R = D("rim_flange_diameter_m") / 2
PCD_R = D("wheel_pcd_m") / 2
FIG_H = 1.80


# ---------------------------------------------------------------- args
def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    p = argparse.ArgumentParser()
    p.add_argument("--concept", default="A", choices=["A", "B", "C"])
    p.add_argument("--out", required=True)
    p.add_argument("--views", default="34przod,bok,przod,34tyl,lakier")
    p.add_argument("--res", default="1600x900")
    p.add_argument("--samples", type=int, default=96)
    p.add_argument("--blend", default="")
    return p.parse_args(argv)


# ---------------------------------------------------------------- materials
MATS = {}


def make_mat(name, rgb, rough=0.5, metal=0.0, coat=0.0, spec=0.5):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*rgb, 1.0)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    b.inputs["Specular IOR Level"].default_value = spec
    b.inputs["Coat Weight"].default_value = coat
    m.diffuse_color = (*rgb, 1.0)
    MATS[name] = m
    return m


CLAY = {
    "paint": ((0.50, 0.50, 0.50), 0.55, 0.0, 0.0),
    "trim": ((0.30, 0.30, 0.30), 0.60, 0.0, 0.0),
    "chassis": ((0.22, 0.22, 0.22), 0.65, 0.0, 0.0),
    "metal": ((0.55, 0.55, 0.55), 0.45, 0.0, 0.0),
}
SEMANTIC = {  # same in clay and paint: they carry function, not style
    "dark": ((0.018, 0.018, 0.018), 0.55, 0.0, 0.0),
    "glass": ((0.012, 0.014, 0.016), 0.06, 0.0, 0.0),
    "lens": ((0.80, 0.82, 0.85), 0.08, 0.0, 0.0),
    "amber": ((0.55, 0.30, 0.05), 0.2, 0.0, 0.0),
    "red": ((0.35, 0.03, 0.025), 0.2, 0.0, 0.0),
    "rubber": ((0.025, 0.025, 0.025), 0.85, 0.0, 0.0),
    "plate": ((0.70, 0.70, 0.68), 0.5, 0.0, 0.0),
    "figure": ((0.33, 0.35, 0.38), 0.7, 0.0, 0.0),
}


def set_variant(paint=None):
    """paint=None -> clay; else dict with paint/trim/chassis/metal overrides."""
    tab = dict(CLAY)
    if paint:
        tab.update(paint)
    for k, (rgb, r, m, c) in {**tab, **SEMANTIC}.items():
        make_mat(k, rgb, r, m, c)


# ---------------------------------------------------------------- mesh helpers
COLL = None


def link(ob):
    COLL.objects.link(ob)
    return ob


def obj_from_bm(name, bm, mat, smooth=True, sharp=32.0):
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    me.materials.append(MATS[mat])
    if smooth:
        for p in me.polygons:
            p.use_smooth = True
        if hasattr(me, "set_sharp_from_angle"):
            me.set_sharp_from_angle(angle=math.radians(sharp))
    return link(ob)


def bevel(ob, width, seg=2, angle=40):
    if width <= 0:
        return ob
    m = ob.modifiers.new("bevel", "BEVEL")
    m.width = width
    m.segments = seg
    m.limit_method = "ANGLE"
    m.angle_limit = math.radians(angle)
    m.harden_normals = True
    return ob


def box(name, c, s, mat, bev=0.0, seg=2, rot=None):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=Vector(s), verts=bm.verts)
    if rot:
        bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=rot)
    bmesh.ops.translate(bm, vec=Vector(c), verts=bm.verts)
    return bevel(obj_from_bm(name, bm, mat), bev, seg)


def box_mm(name, x0, x1, y0, y1, z0, z1, mat, bev=0.0, seg=2):
    return box(name, ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2),
               (abs(x1 - x0), abs(y1 - y0), abs(z1 - z0)), mat, bev, seg)


def cyl(name, c, r, depth, mat, axis="X", seg=32, bev=0.0, bseg=2, r2=None):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=seg,
                          radius1=r, radius2=r if r2 is None else r2, depth=depth)
    if axis == "X":
        bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(math.pi / 2, 3, "Y"))
    elif axis == "Y":
        bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(math.pi / 2, 3, "X"))
    bmesh.ops.translate(bm, vec=Vector(c), verts=bm.verts)
    return bevel(obj_from_bm(name, bm, mat, sharp=40), bev, bseg, angle=50)


def rod(name, p0, p1, r, mat, seg=12):
    """Cylinder between two points."""
    p0, p1 = Vector(p0), Vector(p1)
    d = p1 - p0
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=seg, radius1=r, radius2=r, depth=d.length)
    q = d.normalized().to_track_quat("Z", "Y")
    bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=q.to_matrix())
    bmesh.ops.translate(bm, vec=(p0 + p1) / 2, verts=bm.verts)
    return obj_from_bm(name, bm, mat, sharp=50)


def sphere(name, c, r, mat, scale=(1, 1, 1)):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=24, v_segments=12, radius=r)
    bmesh.ops.scale(bm, vec=Vector(scale), verts=bm.verts)
    bmesh.ops.translate(bm, vec=Vector(c), verts=bm.verts)
    return obj_from_bm(name, bm, mat, sharp=80)


def arch(name, cy, cz, r_in, r_out, x0, x1, a0, a1, mat, n=24):
    """Mudguard band around the X axis; angles in degrees, 90 = top, 0 = towards +Y."""
    bm = bmesh.new()
    rings = []
    for i in range(n + 1):
        a = math.radians(a0 + (a1 - a0) * i / n)
        ca, sa = math.cos(a), math.sin(a)
        ring = [bm.verts.new((x, cy + r * ca, cz + r * sa)) for (x, r) in
                ((x0, r_in), (x1, r_in), (x1, r_out), (x0, r_out))]
        rings.append(ring)
    for i in range(n):
        a, b = rings[i], rings[i + 1]
        for k in range(4):
            bm.faces.new((a[k], a[(k + 1) % 4], b[(k + 1) % 4], b[k]))
    bm.faces.new(rings[0])
    bm.faces.new(list(reversed(rings[-1])))
    return obj_from_bm(name, bm, mat, sharp=40)


def lerp_tab(tab, z):
    if isinstance(tab, (int, float)):
        return float(tab)
    if z <= tab[0][0]:
        return tab[0][1]
    for (z0, v0), (z1, v1) in zip(tab, tab[1:]):
        if z <= z1:
            t = (z - z0) / (z1 - z0) if z1 > z0 else 0
            return v0 + (v1 - v0) * t
    return tab[-1][1]


# ---------------------------------------------------------------- lofted body
class Loft:
    """Body built from horizontal rounded-rectangle sections (plan view).

    front/back: y of the front/back face as f(z); w: half width f(z);
    rf/rb: plan corner radius front/back f(z); arc_n: segments per corner
    (1 = chamfer). Top edge rounded (roof_mode 'round') or chamfered.
    """

    def __init__(self, front, back, w, rf, rb, z0, ztop, roof_r=0.1, roof_mode="round",
                 arc_n=8, step=0.04):
        self.front, self.back, self.w, self.rf, self.rb = front, back, w, rf, rb
        self.z0, self.ztop, self.roof_r, self.roof_mode = z0, ztop, roof_r, roof_mode
        self.arc_n, self.step = arc_n, step

    def sec(self, z):
        yf, yb = lerp_tab(self.front, z), lerp_tab(self.back, z)
        w, rf, rb = lerp_tab(self.w, z), lerp_tab(self.rf, z), lerp_tab(self.rb, z)
        zr = self.ztop - self.roof_r
        if z > zr and self.roof_r > 0:
            t = min(z - zr, self.roof_r)
            ins = self.roof_r - math.sqrt(max(self.roof_r ** 2 - t * t, 0)) if self.roof_mode == "round" else t
            yf, yb, w = yf - ins, yb + ins, w - ins
        lim = min(w, (yf - yb) / 2) - 0.005
        return yf, yb, w, max(min(rf, lim), 0.002), max(min(rb, lim), 0.002)

    def arc(self, cx, cy, r, a0, a1):
        n = self.arc_n
        return [(cx + r * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
                 cy + r * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]

    def ring(self, z):
        yf, yb, w, rf, rb = self.sec(z)
        return (self.arc(w - rf, yf - rf, rf, 90, 0) + self.arc(w - rb, yb + rb, rb, 0, -90)
                + self.arc(-(w - rb), yb + rb, rb, -90, -180) + self.arc(-(w - rf), yf - rf, rf, 180, 90))

    def levels(self):
        zs, z = [], self.z0
        zr = self.ztop - self.roof_r
        while z < zr - 1e-6:
            zs.append(z)
            z += self.step
        n = 10 if self.roof_mode == "round" else 1
        for i in range(n + 1):
            zs.append(zr + self.roof_r * (math.sin(math.pi / 2 * i / n) if self.roof_mode == "round" else i / n))
        extra = []
        for tab in (self.front, self.w, self.rf):
            if not isinstance(tab, (int, float)):
                extra += [k for k, _ in tab if self.z0 < k < zr]
        return sorted(set(round(v, 5) for v in zs + extra))

    def build(self, name, mat, sharp=32):
        bm = bmesh.new()
        rings = []
        for z in self.levels():
            rings.append([bm.verts.new((x, y, z)) for x, y in self.ring(z)])
        m = len(rings[0])
        for a, b in zip(rings, rings[1:]):
            for k in range(m):
                bm.faces.new((a[k], a[(k + 1) % m], b[(k + 1) % m], b[k]))
        bm.faces.new(list(reversed(rings[0])))
        bm.faces.new(rings[-1])
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
        return obj_from_bm(name, bm, mat, sharp=sharp)

    # --- surface evaluation for decals/patches (windows, lamps, gaps) ---
    def _corner_poly(self, z, which):
        yf, yb, w, rf, rb = self.sec(z)
        if which == "front":
            c, pts = (w - rf, yf - rf), self.arc(w - rf, yf - rf, rf, 90, 0)
        else:
            c, pts = (w - rb, yb + rb), self.arc(w - rb, yb + rb, rb, 0, -90)
        return c, pts

    @staticmethod
    def _interp(pts, c, key, val, off):
        for p0, p1 in zip(pts, pts[1:]):
            lo, hi = sorted((p0[key], p1[key]))
            if lo - 1e-9 <= val <= hi + 1e-9:
                t = 0 if hi == lo else (val - p0[key]) / (p1[key] - p0[key])
                px, py = p0[0] + (p1[0] - p0[0]) * t, p0[1] + (p1[1] - p0[1]) * t
                dx, dy = p1[0] - p0[0], p1[1] - p0[1]
                ln = math.hypot(dx, dy) or 1
                nx, ny = dy / ln, -dx / ln
                if nx * (px - c[0]) + ny * (py - c[1]) < 0:
                    nx, ny = -nx, -ny
                return px + nx * off, py + ny * off
        p = pts[-1] if abs(val - pts[-1][key]) < abs(val - pts[0][key]) else pts[0]
        return p[0], p[1]

    def front_pt(self, z, x, off):
        yf, yb, w, rf, rb = self.sec(z)
        ax, sg = abs(x), (1 if x >= 0 else -1)
        if ax <= w - rf:
            return (x, yf + off, z)
        c, pts = self._corner_poly(z, "front")
        px, py = self._interp(pts, c, 0, min(ax, w), off)
        return (sg * px, py, z)

    def side_pt(self, z, y, side, off):
        yf, yb, w, rf, rb = self.sec(z)
        if y > yf - rf:
            c, pts = self._corner_poly(z, "front")
            px, py = self._interp(pts, c, 1, min(y, yf), off)
        elif y < yb + rb:
            c, pts = self._corner_poly(z, "back")
            px, py = self._interp(pts, c, 1, max(y, yb), off)
        else:
            px, py = w + off, y
        return (side * px, py, z)

    def patch(self, name, mat, kind, z0, z1, p0, p1, off=0.006, nz=10, npar=28, side=1, thick=0.0):
        """Surface-following patch. kind 'front' (param = x) or 'side' (param = y)."""
        f0 = p0 if callable(p0) else (lambda z, v=p0: v)
        f1 = p1 if callable(p1) else (lambda z, v=p1: v)
        bm = bmesh.new()
        layers = [off] if thick <= 0 else [off, off + thick]
        grids = []
        for o in layers:
            g = []
            for i in range(nz + 1):
                z = z0 + (z1 - z0) * i / nz
                row = []
                for j in range(npar + 1):
                    v = f0(z) + (f1(z) - f0(z)) * j / npar
                    co = self.front_pt(z, v, o) if kind == "front" else self.side_pt(z, v, side, o)
                    row.append(bm.verts.new(co))
                g.append(row)
            grids.append(g)
        for g in grids:
            for i in range(nz):
                for j in range(npar):
                    bm.faces.new((g[i][j], g[i][j + 1], g[i + 1][j + 1], g[i + 1][j]))
        if len(grids) == 2:  # close the rim so it reads as a raised panel
            a, b = grids
            edge = ([(i, 0) for i in range(nz)] + [(nz, j) for j in range(npar)]
                    + [(i, npar) for i in range(nz, 0, -1)] + [(0, j) for j in range(npar, 0, -1)])
            for (i0, j0), (i1, j1) in zip(edge, edge[1:] + edge[:1]):
                bm.faces.new((a[i0][j0], a[i1][j1], b[i1][j1], b[i0][j0]))
        return obj_from_bm(name, bm, mat, sharp=60)

    def quad_patch(self, name, mat, kind, corners, off=0.006, nu=24, nv=10, side=1):
        """Bilinear patch from 4 corners (param, z) in projection space:
        order = bottom-start, bottom-end, top-end, top-start. Allows slanted edges."""
        (p00, z00), (p10, z10), (p11, z11), (p01, z01) = corners
        bm = bmesh.new()
        g = []
        for i in range(nv + 1):
            v = i / nv
            row = []
            for j in range(nu + 1):
                u = j / nu
                p = (p00 * (1 - u) + p10 * u) * (1 - v) + (p01 * (1 - u) + p11 * u) * v
                z = (z00 * (1 - u) + z10 * u) * (1 - v) + (z01 * (1 - u) + z11 * u) * v
                co = self.front_pt(z, p, off) if kind == "front" else self.side_pt(z, p, side, off)
                row.append(bm.verts.new(co))
            g.append(row)
        for i in range(nv):
            for j in range(nu):
                bm.faces.new((g[i][j], g[i][j + 1], g[i + 1][j + 1], g[i + 1][j]))
        return obj_from_bm(name, bm, mat, sharp=60)

    def gap_v(self, name, side, y, z0, z1, w=0.012, off=0.004):
        return self.patch(name, "dark", "side", z0, z1, y - w / 2, y + w / 2, off=off, nz=4, npar=1, side=side)

    def gap_h(self, name, side, z, y0, y1, w=0.012, off=0.004):
        return self.patch(name, "dark", "side", z - w / 2, z + w / 2, y0, y1, off=off, nz=1, npar=12, side=side)


# ---------------------------------------------------------------- shared chassis
def wheel(name, y, side, x_c, outward):
    """One tyre + rim. outward: +1 if the rim face looks to +X."""
    cyl(name + "_tyre", (x_c, y, WHEEL_Z), TYRE_R, TYRE_W, "rubber", seg=64, bev=0.075, bseg=4)
    face_x = x_c + outward * (TYRE_W / 2 - 0.035)
    cyl(name + "_rim", (face_x, y, WHEEL_Z), RIM_R, 0.02, "metal", seg=48, bev=0.008)
    cyl(name + "_hub", (face_x + outward * 0.03, y, WHEEL_Z), 0.13, 0.06, "metal", seg=32, bev=0.01)
    for k in range(10):
        a = 2 * math.pi * k / 10
        cyl(f"{name}_nut{k}", (face_x + outward * 0.02, y + PCD_R * math.cos(a), WHEEL_Z + PCD_R * math.sin(a)),
            0.018, 0.04, "metal", seg=6)
    # hand-holes of the steel disc wheel (dark), a strong scale cue
    for k in range(5):
        a = 2 * math.pi * (k + 0.5) / 5
        cyl(f"{name}_hole{k}", (face_x + outward * 0.006, y + 0.215 * math.cos(a), WHEEL_Z + 0.215 * math.sin(a)),
            0.045, 0.012, "dark", seg=20)


def build_chassis(cfg):
    fx = FRONT_TRACK / 2
    for s in (-1, 1):
        wheel(f"wheel_F_{'L' if s < 0 else 'R'}", 0.0, s, s * fx, s)
        for k, off in (("o", +1), ("i", -1)):
            xc = s * (REAR_TRACK / 2 + off * DUAL_SPACING / 2)
            wheel(f"wheel_R_{'L' if s < 0 else 'R'}{k}", -WB, s, xc, s if k == "o" else -s)
    # frame rails + cross members
    y_front, y_end = 1.05, -WB - REAR_OH
    for s in (-1, 1):
        box_mm(f"frame_rail_{s}", s * (FRAME_HALF_W - 0.075), s * FRAME_HALF_W, y_end, y_front,
               FRAME_TOP - 0.28, FRAME_TOP, "chassis")
    for y in (-1.2, -2.3, -3.0, -4.3):
        box_mm(f"frame_cross_{y}", -FRAME_HALF_W + 0.07, FRAME_HALF_W - 0.07, y - 0.05, y + 0.05,
               FRAME_TOP - 0.22, FRAME_TOP - 0.04, "chassis")
    # axles
    box_mm("axle_front", -fx + 0.12, fx - 0.12, -0.06, 0.06, WHEEL_Z - 0.07, WHEEL_Z + 0.05, "chassis")
    cyl("axle_rear", (0, -WB, WHEEL_Z), 0.085, REAR_TRACK - 0.15, "chassis", seg=24)
    cyl("diff", (0, -WB, WHEEL_Z), 0.23, 0.30, "chassis", axis="Y", seg=32, bev=0.03)
    for s in (-1, 1):  # front leaf springs, rear air bellows
        box_mm(f"spring_F_{s}", s * 0.36, s * 0.46, -0.75, 0.75, WHEEL_Z + 0.06, WHEEL_Z + 0.16, "chassis")
        cyl(f"bellow_{s}", (s * 0.58, -WB - 0.42, 0.78), 0.14, 0.24, "rubber", axis="Z", seg=24, bev=0.03)
        box_mm(f"trailing_arm_{s}", s * 0.52, s * 0.64, -WB - 0.5, -WB + 0.9, 0.56, 0.66, "chassis")
    # engine/gearbox under the cab, propshaft
    box_mm("engine", -0.46, 0.46, -1.25, 0.55, 0.62, CAB_FLOOR_Z, "chassis", bev=0.03)
    box_mm("gearbox", -0.26, 0.26, -2.05, -1.25, 0.66, 0.98, "chassis", bev=0.03)
    rod("propshaft", (0, -2.05, 0.80), (0, -WB + 0.25, WHEEL_Z + 0.02), 0.055, "metal")
    # fifth wheel (top at FIFTH_H)
    fy = -WB + FIFTH_LEAD
    box_mm("fifth_mount", -0.55, 0.55, fy - 0.45, fy + 0.45, FRAME_TOP, FIFTH_H - 0.10, "chassis", bev=0.01)
    cyl("fifth_plate", (0, fy, FIFTH_H - 0.05), 0.47, 0.10, "chassis", axis="Z", seg=48, bev=0.02)
    box_mm("fifth_slot", -0.09, 0.09, fy - 0.50, fy - 0.02, FIFTH_H - 0.02, FIFTH_H + 0.002, "dark")
    # trailer connections: gooseneck + three coiled lines
    rod("gooseneck", (0, CAB_BACK_Y - 0.12, FRAME_TOP), (0, CAB_BACK_Y - 0.12, 2.05), 0.035, "chassis")
    box_mm("catwalk", -0.55, 0.55, CAB_BACK_Y - 0.70, CAB_BACK_Y - 0.08, FRAME_TOP, FRAME_TOP + 0.03, "chassis")
    for k, (x, mat) in enumerate(((-0.12, "red"), (0.0, "amber"), (0.12, "dark"))):
        coil(f"coil{k}", (x, CAB_BACK_Y - 0.15, 1.95), (x, CAB_BACK_Y - 0.95, 1.30), mat)
    # rear: light bar, mudguards, flaps
    box_mm("rear_lightbar", -1.20, 1.20, y_end - 0.04, y_end + 0.04, 0.78, 0.86, "chassis")
    for s in (-1, 1):
        box_mm(f"tail_{s}", s * 0.78, s * 1.20, y_end - 0.05, y_end - 0.01, 0.74, 0.90, "red", bev=0.01)
        box_mm(f"tail_amber_{s}", s * 1.02, s * 1.18, y_end - 0.055, y_end - 0.048, 0.76, 0.88, "amber")
        cfg.get("rear_guard", rear_guard_flat)(s)
    # fuel tank (left), AdBlue, battery box + aftertreatment (right), air tanks
    ft = cfg["fuel_tank"]
    box_mm("fuel_tank", -1.18, -FRAME_HALF_W - 0.02, ft[0], ft[1], 0.42, 1.02, "metal", bev=0.13, seg=5)
    for y in (ft[0] - 0.18, ft[1] + 0.18):
        box_mm(f"tank_strap_{y}", -1.19, -FRAME_HALF_W - 0.01, y - 0.025, y + 0.025, 0.40, 1.04, "chassis", bev=0.02)
    cyl("tank_cap", (-1.0, ft[0] - 0.35, 1.04), 0.06, 0.04, "chassis", axis="Z")
    box_mm("adblue", -1.12, -FRAME_HALF_W - 0.02, ft[1] - 0.05, ft[1] - 0.40, 0.55, 0.98, "trim", bev=0.06, seg=3)
    box_mm("aftertreatment", FRAME_HALF_W + 0.02, 1.16, -1.05, -2.05, 0.45, 1.02, "chassis", bev=0.06, seg=3)
    box_mm("battery_box", FRAME_HALF_W + 0.02, 1.10, -2.10, -2.70, 0.55, 0.98, "trim", bev=0.03)
    cyl("tailpipe", (0.9, -2.08, 0.38), 0.05, 0.14, "dark", axis="Z")
    for k, y in enumerate((-2.85,)):
        cyl(f"airtank{k}", (0.65, y, 0.62), 0.12, 0.55, "chassis", axis="X", bev=0.05, bseg=3)


def rear_guard_flat(s):
    x0, x1 = s * 0.58, s * 1.27
    box_mm(f"rear_guard_{s}", x0, x1, -WB - 0.72, -WB + 0.62, 1.10, 1.13, "trim", bev=0.008)
    box_mm(f"rear_guard_front_{s}", x0, x1, -WB + 0.60, -WB + 0.63, 0.80, 1.13, "trim")
    box_mm(f"mudflap_{s}", x0, x1, -WB - 0.74, -WB - 0.72, 0.28, 1.12, "rubber")


def coil(name, p0, p1, mat, r=0.045, turns=11):
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = 0.008
    cu.bevel_resolution = 2
    sp = cu.splines.new("POLY")
    p0, p1 = Vector(p0), Vector(p1)
    ax = (p1 - p0)
    u = ax.orthogonal().normalized()
    v = ax.normalized().cross(u)
    n = turns * 16
    sp.points.add(n)
    for i in range(n + 1):
        t = i / n
        a = 2 * math.pi * turns * t
        sag = Vector((0, 0, -0.18 * math.sin(math.pi * t)))
        p = p0 + ax * t + (u * math.cos(a) + v * math.sin(a)) * r + sag
        sp.points[i].co = (*p, 1)
    ob = bpy.data.objects.new(name, cu)
    cu.materials.append(MATS[mat])
    return link(ob)


def steps(name, s, y0, y1, mat, open_treads=False):
    """Step stack behind the front wheel, outer face flush with cab side."""
    xo, xi = s * (CAB_HALF_W - 0.005), s * (CAB_HALF_W - 0.30)
    box_mm(name, xo, xi, y1, y0, 0.40, CAB_FLOOR_Z + 0.02, mat, bev=0.015)
    for k, z in enumerate((0.47, 0.80)):  # two treads; third is the cab floor sill
        box_mm(f"{name}_recess{k}", xo + s * 0.004, xo - s * 0.22, y1 + 0.03, y0 - 0.03, z, z + 0.22, "dark")
        if open_treads:
            box_mm(f"{name}_tread{k}", xo + s * 0.008, xo - s * 0.22, y1 + 0.02, y0 - 0.02, z - 0.02, z + 0.015,
                   "metal")


def mannequin():
    """1.80 m reference figure built at the origin and parented to 'figure_root'
    (moved per camera so it never hides the truck)."""
    before = set(bpy.data.objects)
    _mannequin_parts(0.0, 0.0)
    root = link(bpy.data.objects.new("figure_root", None))
    for ob in set(bpy.data.objects) - before:
        if ob is not root:
            ob.parent = root
    return root


def _mannequin_parts(x, y):
    for s in (-1, 1):
        cyl(f"fig_leg{s}", (x + s * 0.10, y, 0.45), 0.075, 0.82, "figure", axis="Z", seg=16, bev=0.03)
        box(f"fig_foot{s}", (x + s * 0.10, y + 0.05, 0.035), (0.10, 0.26, 0.07), "figure", bev=0.02)
        rod(f"fig_arm{s}", (x + s * 0.235, y, 1.43), (x + s * 0.27, y + 0.02, 0.82), 0.045, "figure")
    box("fig_torso", (x, y, 1.17), (0.40, 0.22, 0.62), "figure", bev=0.08, seg=3)
    cyl("fig_neck", (x, y, 1.53), 0.05, 0.10, "figure", axis="Z", seg=16)
    sphere("fig_head", (x, y, FIG_H - 0.12), 0.10, "figure", scale=(0.95, 1.05, 1.2))


# ---------------------------------------------------------------- concept A
def concept_A():
    """TRAKT — flat-front long-haul: near-vertical glass, big framed grille, external visor."""
    cab = Loft(front=[(CAB_FLOOR_Z, 1.40), (2.02, 1.40), (2.08, 1.385), (3.02, 1.33), (ROOF_Z, 1.30)],
               back=CAB_BACK_Y, w=[(CAB_FLOOR_Z, CAB_HALF_W), (2.9, CAB_HALF_W), (ROOF_Z, CAB_HALF_W - 0.02)],
               rf=0.10, rb=0.10, z0=CAB_FLOOR_Z, ztop=ROOF_Z, roof_r=0.14, arc_n=6)
    cab.build("cab", "paint")
    cab.patch("windscreen", "glass", "front", 2.10, 3.00, -1.10, 1.10, off=0.006)
    # visor kept shallow: it must not become the frontmost point of the truck (measured, see _wymiary.json)
    box("sun_visor", (0, lerp_tab(cab.front, 3.06) + 0.07, 3.085), (2.30, 0.18, 0.05), "paint", bev=0.012)
    # grille: dark field + 4 horizontal paint bars + brand bar; headlamps high in cab corners
    cab.patch("grille", "dark", "front", 1.42, 1.96, -0.82, 0.82, off=0.004)
    for k, z in enumerate((1.51, 1.63, 1.75, 1.87)):
        box(f"grille_bar{k}", (0, 1.43, z), (1.60, 0.05, 0.05), "paint", bev=0.01)
    box("brand_bar", (0, 1.425, 1.97), (1.68, 0.05, 0.07), "trim", bev=0.01)
    box("badge", (0, 1.455, 1.97), (0.36, 0.01, 0.045), "lens")
    for s in (-1, 1):
        cab.patch(f"headlamp_frame_{s}", "dark", "front", 1.18, 1.39, s * 0.70, s * (CAB_HALF_W - 0.01), off=0.003)
        cab.patch(f"headlamp_{s}", "lens", "front", 1.20, 1.37, s * 0.72, s * (CAB_HALF_W - 0.025), off=0.006)
        cab.patch(f"headlamp_div_{s}", "dark", "front", 1.20, 1.37, s * 0.93, s * 0.95, off=0.008, nz=1, npar=1)
    side_glass_cab(cab, front=lambda z: lerp_tab(cab.front, z) - 0.14, rear=-0.66, z0=2.05, z1=2.86, pillar=0.35)
    doors(cab)
    mirrors_classic(cab, y=1.18, x_head=1.43)
    kerb_mirror(cab)
    roof_markers(cab)
    wipers(cab, 2.14)
    # bumper (painted) with lamps in its top corners
    bmp = Loft(front=1.445, back=0.66, w=CAB_HALF_W, rf=0.12, rb=0.04, z0=0.36, ztop=CAB_FLOOR_Z + 0.01,
               roof_r=0.03, arc_n=6)
    bmp.build("bumper", "paint")
    for s in (-1, 1):
        bmp.patch(f"fog_frame_{s}", "dark", "front", 0.80, 0.94, s * 0.88, s * 1.17, off=0.002)
        bmp.patch(f"fog_{s}", "lens", "front", 0.82, 0.92, s * 0.90, s * 1.15, off=0.004)
    bmp.patch("bumper_step", "dark", "front", 1.02, 1.05, -1.0, 1.0, off=0.003)
    bmp.patch("bumper_intake", "dark", "front", 0.44, 0.74, -0.86, 0.86, off=0.003)
    bmp.patch("bumper_lip", "trim", "front", 0.36, 0.43, -1.2, 1.2, off=0.004)
    bmp.patch("plate", "plate", "front", 0.57, 0.68, -0.26, 0.26, off=0.008)
    front_arches(cab, "trim")
    for s in (-1, 1):
        steps(f"steps_{s}", s, -0.58, CAB_BACK_Y, "trim")
        # short skirt between AdBlue and rear wheel
        box_mm(f"skirt_{s}", s * (CAB_HALF_W - 0.03), s * (CAB_HALF_W - 0.01), -2.55, -WB + 0.58, 0.42, 1.04,
               "trim", bev=0.005)
    return dict(fuel_tank=(-1.05, -2.15))


# ---------------------------------------------------------------- concept B
def concept_B():
    """BIELIK — sculpted aero: long rounded nose, 16 deg screen, camera mirrors, full skirts."""
    cab = Loft(front=[(CAB_FLOOR_Z, 1.495), (1.50, 1.495), (1.80, 1.475), (1.98, 1.43), (3.00, 1.07), (ROOF_Z, 0.92)],
               back=CAB_BACK_Y, w=[(CAB_FLOOR_Z, CAB_HALF_W), (2.6, CAB_HALF_W), (ROOF_Z, CAB_HALF_W - 0.06)],
               rf=[(CAB_FLOOR_Z, 0.30), (2.0, 0.36), (3.0, 0.42), (ROOF_Z, 0.45)], rb=0.14,
               z0=CAB_FLOOR_Z, ztop=ROOF_Z, roof_r=0.42, arc_n=10)
    cab.build("cab", "paint")
    # wrap-around screen, trapezoid in front projection (~19 deg rake)
    cab.quad_patch("windscreen", "glass", "front", [(-1.13, 2.03), (1.13, 2.03), (1.04, 2.96), (-1.04, 2.96)],
                   off=0.006, nu=44)
    # full-width light signature: lamps at the corners joined by a dark glass band
    cab.patch("light_band", "glass", "front", 1.735, 1.775, -0.62, 0.62, off=0.004, nz=1)
    for s in (-1, 1):
        cab.patch(f"headlamp_frame_{s}", "dark", "front", 1.69, 1.83, s * 0.60, s * (CAB_HALF_W - 0.01), off=0.003)
        cab.patch(f"headlamp_{s}", "lens", "front", 1.71, 1.81, s * 0.62, s * (CAB_HALF_W - 0.025), off=0.006)
    # trapezoid lower grille with three fins
    cab.quad_patch("lower_grille", "dark", "front", [(-0.52, 1.20), (0.52, 1.20), (0.80, 1.64), (-0.80, 1.64)],
                   off=0.004)
    for k, z in enumerate((1.31, 1.42, 1.53)):
        hw = 0.52 + (0.80 - 0.52) * (z - 1.20) / 0.44 - 0.03
        cab.patch(f"grille_fin{k}", "paint", "front", z, z + 0.03, -hw, hw, off=0.012, nz=1, npar=2)
    box("badge", (0, lerp_tab(cab.front, 1.91) + 0.008, 1.91), (0.40, 0.01, 0.06), "lens")
    for s in (-1, 1):  # glass with a beltline dropping towards the front (kerb view)
        yb_front = lerp_tab(cab.front, 1.90) - 0.45
        yt_front = lerp_tab(cab.front, 2.84) - 0.32
        cab.quad_patch(f"side_window_{s}", "glass", "side", [(-0.66, 2.06), (yb_front, 1.90), (yt_front, 2.84),
                                                              (-0.66, 2.84)], off=0.006, side=s)
        cab.patch(f"window_div_{s}", "dark", "side", 1.96, 2.85, 0.33, 0.37, off=0.010, side=s, nz=2, npar=2)
    doors(cab, front_top=1.97)
    cam_mirrors(cab)
    roof_markers(cab)
    wipers(cab, 2.14)
    bmp = Loft(front=1.52, back=0.66, w=CAB_HALF_W, rf=0.34, rb=0.04, z0=0.38, ztop=CAB_FLOOR_Z + 0.01,
               roof_r=0.04, arc_n=10)
    bmp.build("bumper", "paint")
    bmp.patch("bumper_intake", "dark", "front", 0.60, 0.80, -0.78, 0.78, off=0.003)
    bmp.patch("bumper_lip", "trim", "front", 0.38, 0.48, -1.20, 1.20, off=0.004)
    for s in (-1, 1):  # vertical air-curtain slots at the corners
        bmp.patch(f"air_curtain_{s}", "dark", "front", 0.56, 1.02, s * 0.97, s * 1.07, off=0.003)
        bmp.patch(f"fog_{s}", "lens", "front", 0.62, 0.68, s * 0.84, s * 0.94, off=0.004)
    bmp.patch("plate", "plate", "front", 0.92, 1.03, -0.26, 0.26, off=0.008)
    front_arches(cab, "paint", r_out=0.66)
    for s in (-1, 1):
        steps(f"steps_{s}", s, -0.58, CAB_BACK_Y, "paint")
        box_mm(f"skirt_{s}", s * (CAB_HALF_W - 0.03), s * (CAB_HALF_W - 0.005), CAB_BACK_Y - 0.02,
               -WB + 0.60, 0.40, 1.06, "paint", bev=0.008)
        box_mm(f"skirt_lip_{s}", s * (CAB_HALF_W - 0.03), s * (CAB_HALF_W - 0.002), CAB_BACK_Y - 0.02,
               -WB + 0.60, 0.40, 0.47, "trim")
        # cab side extenders (aero fairing between cab and trailer)
        box_mm(f"side_extender_{s}", s * (CAB_HALF_W - 0.05), s * (CAB_HALF_W - 0.03), CAB_BACK_Y - 0.32,
               CAB_BACK_Y + 0.02, 1.60, ROOF_Z - 0.40, "trim", bev=0.006)
    return dict(fuel_tank=(-1.05, -2.25), rear_guard=rear_guard_aero)


def rear_guard_aero(s):
    arch(f"rear_guard_{s}", -WB, WHEEL_Z, 0.60, 0.63, s * 0.58, s * 1.27, 20, 160, "trim")
    box_mm(f"mudflap_{s}", s * 0.58, s * 1.27, -WB - 0.66, -WB - 0.64, 0.28, 0.80, "rubber")


# ---------------------------------------------------------------- concept C
def concept_C():
    """NAREW — utilitarian/industrial: chamfered faceted cab, tall barred grille,
    separate dark visor, steel bumper with lamp pods, exposed chassis."""
    cab = Loft(front=[(CAB_FLOOR_Z, 1.42), (2.03, 1.42), (2.07, 1.405), (3.02, 1.375), (ROOF_Z, 1.36)],
               back=CAB_BACK_Y, w=[(CAB_FLOOR_Z, CAB_HALF_W), (ROOF_Z, CAB_HALF_W - 0.01)],
               rf=0.27, rb=0.06, z0=CAB_FLOOR_Z, ztop=ROOF_Z, roof_r=0.22, roof_mode="chamfer", arc_n=1)
    cab.build("cab", "paint", sharp=20)
    cab.patch("windscreen", "glass", "front", 2.10, 3.00, -0.93, 0.93, off=0.006)
    cab.patch("windscreen_frame", "dark", "front", 2.07, 3.03, -0.96, 0.96, off=0.003)
    # black textured corner panels wrapping the chamfers (replaceable, scuff-proof)
    for s in (-1, 1):
        cab.patch(f"corner_panel_{s}", "trim", "front", CAB_FLOOR_Z + 0.02, 1.98, s * 0.86, s * CAB_HALF_W,
                  off=0.004, thick=0.012, nz=4, npar=12)
        cab.patch(f"belt_crease_{s}", "dark", "side", 2.005, 2.02, -0.94, 1.0, off=0.003, side=s, nz=1, npar=16)
    box("sun_visor", (0, lerp_tab(cab.front, 3.08) + 0.07, 3.10), (2.38, 0.18, 0.12), "trim", bev=0.01)
    for k, x in enumerate((-0.75, -0.25, 0.25, 0.75)):
        box(f"visor_lamp{k}", (x, lerp_tab(cab.front, 3.08) + 0.163, 3.10), (0.10, 0.012, 0.045), "amber")
    cab.patch("grille", "dark", "front", 1.22, 1.96, -0.78, 0.78, off=0.004)
    for k in range(9):
        x = -0.68 + k * 0.17
        box(f"grille_bar{k}", (x, 1.44, 1.59), (0.05, 0.05, 0.74), "paint", bev=0.008)
    box("grille_top", (0, 1.445, 1.97), (1.62, 0.06, 0.07), "paint", bev=0.01)
    box("badge", (0, 1.48, 1.97), (0.34, 0.01, 0.045), "lens")
    side_glass_cab(cab, front=lambda z: 1.05, rear=-0.66, z0=2.05, z1=2.86, pillar=0.35)
    doors(cab)
    mirrors_classic(cab, y=1.20, x_head=1.45, tube=True)
    kerb_mirror(cab)
    roof_markers(cab)
    wipers(cab, 2.14)
    for s in (-1, 1):  # external grab rails both sides of the door; must stay inside the 2.55 m limit
        for y in (0.42, -0.88):
            x = s * (CAB_HALF_W + 0.016)
            rod(f"grab_{s}_{y}", (x, y, 1.30), (x, y, 2.20), 0.012, "metal")
            for z in (1.30, 2.20):
                rod(f"grab_mount_{s}_{y}_{z}", (s * (CAB_HALF_W - 0.01), y, z), (x, y, z), 0.010, "metal")
    # steel bumper in trim colour, lamp pods with round lenses, skid plate, tow eye
    bmp = Loft(front=1.49, back=0.66, w=CAB_HALF_W + 0.005, rf=0.12, rb=0.03, z0=0.42, ztop=CAB_FLOOR_Z + 0.01,
               roof_r=0.02, roof_mode="chamfer", arc_n=1)
    bmp.build("bumper", "trim", sharp=20)
    box("skid_plate", (0, 1.47, 0.40), (2.10, 0.16, 0.10), "chassis", bev=0.02)
    cyl("tow_eye", (0, 1.53, 0.58), 0.06, 0.08, "metal", axis="Y", seg=24)
    for s in (-1, 1):
        box(f"lamp_pod_{s}", (s * 0.95, 1.50, 0.97), (0.46, 0.04, 0.22), "dark", bev=0.015)
        for k, dx in enumerate((-0.11, 0.11)):
            cyl(f"lamp_{s}_{k}", (s * 0.95 + dx, 1.525, 0.97), 0.075, 0.02, "lens", axis="Y", seg=32)
        cyl(f"fog_{s}", (s * 0.95, 1.50, 0.62), 0.06, 0.03, "lens", axis="Y", seg=24)
    bmp.patch("plate", "plate", "front", 0.62, 0.73, -0.26, 0.26, off=0.008)
    front_arches(cab, "trim")
    for s in (-1, 1):
        steps(f"steps_{s}", s, -0.58, CAB_BACK_Y, "trim", open_treads=True)
    box_mm("toolbox", FRAME_HALF_W + 0.02, 1.10, -2.75, -3.05, 0.60, 0.98, "trim", bev=0.01)
    return dict(fuel_tank=(-1.05, -2.40))


# ---------------------------------------------------------------- shared cab parts
def side_glass_cab(cab, front, rear, z0, z1, pillar=None):
    for s in (-1, 1):
        cab.patch(f"side_window_{s}", "glass", "side", z0, z1, rear, front, off=0.006, side=s, npar=24)
        if pillar is not None:  # division bar between quarter light and door glass
            cab.patch(f"window_div_{s}", "paint", "side", z0 - 0.01, z1 + 0.01, pillar - 0.03, pillar + 0.03,
                      off=0.010, side=s, nz=2, npar=2)


def doors(cab, y_front=0.35, y_rear=-0.80, z_top=2.92, front_top=2.04):
    for s in (-1, 1):
        cab.gap_v(f"door_gap_f_{s}", s, y_front, CAB_FLOOR_Z + 0.02, front_top)
        cab.gap_v(f"door_gap_r_{s}", s, y_rear, CAB_FLOOR_Z + 0.02, z_top)
        cab.gap_h(f"door_gap_t_{s}", s, z_top, y_rear, y_front)
        cab.patch(f"door_handle_{s}", "dark", "side", 1.66, 1.71, -0.68, -0.52, off=0.012, side=s, nz=1, npar=2)


def cab_rear_details():
    y = CAB_BACK_Y - 0.004
    box_mm("rear_joint", -1.15, 1.15, y - 0.004, y, 2.04, 2.055, "dark")
    box_mm("rear_lower_panel", -1.20, 1.20, y - 0.02, y, CAB_FLOOR_Z, 1.42, "trim", bev=0.005)
    for s in (-1, 1):
        x = s * 0.42
        rod(f"rear_handle_{s}", (x, y - 0.06, 1.55), (x, y - 0.06, 2.25), 0.016, "metal")
        for z in (1.55, 2.25):
            rod(f"rear_handle_m_{s}_{z}", (x, y, z), (x, y - 0.06, z), 0.014, "metal")


def mirrors_classic(cab, y, x_head, tube=False):
    for s in (-1, 1):
        x0 = s * (CAB_HALF_W - 0.02)
        xh = s * x_head
        if tube:
            rod(f"mirror_arm_top_{s}", (x0, y, 2.95), (xh, y - 0.05, 2.80), 0.02, "metal")
            rod(f"mirror_arm_bot_{s}", (x0, y, 2.05), (xh, y - 0.05, 2.05), 0.02, "metal")
        else:
            box(f"mirror_arm_{s}", ((x0 + xh) / 2, y, 2.90), (abs(xh - x0), 0.06, 0.05), "trim", bev=0.012)
            rod(f"mirror_strut_{s}", (x0, y, 2.10), (xh, y - 0.04, 2.15), 0.015, "trim")
        box(f"mirror_main_{s}", (xh, y - 0.06, 2.50), (0.23, 0.08, 0.48), "trim", bev=0.025, seg=3)
        box(f"mirror_glass_{s}", (xh, y - 0.105, 2.50), (0.20, 0.01, 0.44), "glass")
        box(f"mirror_wide_{s}", (xh, y - 0.06, 2.12), (0.23, 0.08, 0.20), "trim", bev=0.025, seg=3)
        box(f"mirror_wide_glass_{s}", (xh, y - 0.105, 2.12), (0.20, 0.01, 0.16), "glass")


def kerb_mirror(cab):
    """Class VI front mirror over the passenger-side (right, +X) corner."""
    yf = lerp_tab(cab.front, 3.1)
    rod("kerb_arm", (0.95, yf - 0.05, 3.25), (0.95, yf + 0.12, 3.20), 0.015, "trim")
    box("kerb_mirror", (0.95, yf + 0.16, 3.10), (0.24, 0.06, 0.16), "trim", bev=0.02)


def cam_mirrors(cab):
    for s in (-1, 1):
        x0 = s * (CAB_HALF_W - 0.03)
        y0 = lerp_tab(cab.front, 2.95) - 0.40
        box(f"cam_arm_{s}", (s * (CAB_HALF_W + 0.10), y0, 2.96), (0.26, 0.07, 0.05), "trim", bev=0.02)
        box(f"cam_pod_{s}", (s * (CAB_HALF_W + 0.24), y0 - 0.02, 2.95), (0.09, 0.16, 0.10), "trim", bev=0.035, seg=3)
        cyl(f"cam_lens_{s}", (s * (CAB_HALF_W + 0.24), y0 - 0.10, 2.95), 0.022, 0.01, "glass", axis="Y", seg=16)


def roof_markers(cab):
    for s in (-1, 1):
        yf = lerp_tab(cab.front, ROOF_Z - 0.15)
        box(f"marker_front_{s}", (s * (CAB_HALF_W - 0.30), yf + 0.005 - cab.roof_r * 0.3, ROOF_Z - 0.10),
            (0.10, 0.03, 0.05), "lens")
        box(f"marker_rear_{s}", (s * (CAB_HALF_W - 0.20), CAB_BACK_Y - 0.01, ROOF_Z - 0.18), (0.10, 0.02, 0.05), "red")
        box(f"side_marker_{s}", (s * (CAB_HALF_W + 0.006), -1.4, 0.95), (0.012, 0.10, 0.04), "amber")


def wipers(cab, z):
    yf = lerp_tab(cab.front, z) + 0.03
    for k, (x0, x1) in enumerate(((-1.00, -0.12), (0.02, 0.90))):
        rod(f"wiper{k}", (x0, yf, z + 0.02), (x1, yf - 0.01, z + 0.10), 0.012, "dark")


def front_arches(cab, mat, r_out=0.65):
    for s in (-1, 1):
        arch(f"front_arch_{s}", 0.0, WHEEL_Z, r_out - 0.035, r_out, s * (CAB_HALF_W - 0.30), s * (CAB_HALF_W - 0.005),
             -8, 172, mat)


# ---------------------------------------------------------------- scene, lights, cameras
def setup_scene(res, samples):
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = samples
    sc.cycles.use_adaptive_sampling = True
    sc.cycles.use_denoising = True
    sc.render.resolution_x, sc.render.resolution_y = (int(v) for v in res.split("x"))
    sc.render.resolution_percentage = 100
    sc.render.image_settings.file_format = "JPEG"  # PNG of a noisy-grid render is ~0.9 MB; budget is 400 KB
    sc.render.image_settings.color_mode = "RGB"
    sc.render.image_settings.quality = 90
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.look = "None"
    sc.unit_settings.system = "METRIC"
    w = bpy.data.worlds.new("studio")
    w.use_nodes = True
    bg = w.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (0.62, 0.64, 0.66, 1)
    bg.inputs["Strength"].default_value = 0.85
    sc.world = w
    sun = bpy.data.lights.new("key", "SUN")
    sun.energy = 2.6
    sun.angle = math.radians(6)
    ob = bpy.data.objects.new("key", sun)
    ob.rotation_euler = (math.radians(42), 0, math.radians(-145))
    link(ob)
    # ground with 1 m grid (5 m major lines), object coords = metres
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=60)
    g = obj_from_bm("ground", bm, "figure", smooth=False)
    g.data.materials[0] = grid_material("grid", emissive=False)
    # vertical measuring backdrops, each visible only to the matching ortho camera
    for name, loc, rot in (("wall_bok", (9.0, 0, 0), (math.pi / 2, 0, math.pi / 2)),
                           ("wall_przod", (0, -14.0, 0), (math.pi / 2, 0, 0))):
        bm = bmesh.new()
        bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=30)
        bmesh.ops.translate(bm, vec=Vector((0, 30, 0)), verts=bm.verts)
        wo = obj_from_bm(name, bm, "figure", smooth=False)
        wo.location, wo.rotation_euler = loc, rot
        wo.data.materials[0] = grid_material(name, emissive=True)
        wo.visible_shadow = False
        wo.hide_render = True


def grid_material(name, emissive):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Roughness"].default_value = 0.9
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Object"], sep.inputs[0])

    def line(sock, period, width):
        a = nt.nodes.new("ShaderNodeMath"); a.operation = "DIVIDE"; a.inputs[1].default_value = period
        nt.links.new(sock, a.inputs[0])
        b = nt.nodes.new("ShaderNodeMath"); b.operation = "ADD"; b.inputs[1].default_value = 0.5
        nt.links.new(a.outputs[0], b.inputs[0])
        c = nt.nodes.new("ShaderNodeMath"); c.operation = "FRACT"
        nt.links.new(b.outputs[0], c.inputs[0])
        d = nt.nodes.new("ShaderNodeMath"); d.operation = "SUBTRACT"; d.inputs[1].default_value = 0.5
        nt.links.new(c.outputs[0], d.inputs[0])
        e = nt.nodes.new("ShaderNodeMath"); e.operation = "ABSOLUTE"
        nt.links.new(d.outputs[0], e.inputs[0])
        f = nt.nodes.new("ShaderNodeMath"); f.operation = "LESS_THAN"; f.inputs[1].default_value = width / period
        nt.links.new(e.outputs[0], f.inputs[0])
        return f.outputs[0]

    def both(period, width):
        mx = nt.nodes.new("ShaderNodeMath"); mx.operation = "MAXIMUM"
        nt.links.new(line(sep.outputs[0], period, width), mx.inputs[0])
        nt.links.new(line(sep.outputs[1], period, width), mx.inputs[1])
        return mx.outputs[0]

    mix1 = nt.nodes.new("ShaderNodeMix"); mix1.data_type = "RGBA"
    mix1.inputs[6].default_value = (0.42, 0.42, 0.41, 1)
    mix1.inputs[7].default_value = (0.24, 0.24, 0.24, 1)
    nt.links.new(both(1.0, 0.012), mix1.inputs[0])
    mix2 = nt.nodes.new("ShaderNodeMix"); mix2.data_type = "RGBA"
    nt.links.new(mix1.outputs[2], mix2.inputs[6])
    mix2.inputs[7].default_value = (0.12, 0.12, 0.12, 1)
    nt.links.new(both(5.0, 0.02), mix2.inputs[0])
    if emissive:
        em = nt.nodes.new("ShaderNodeEmission")
        em.inputs["Strength"].default_value = 1.0
        mix1.inputs[6].default_value = (0.60, 0.61, 0.62, 1)
        mix1.inputs[7].default_value = (0.47, 0.48, 0.49, 1)
        mix2.inputs[7].default_value = (0.36, 0.37, 0.38, 1)
        nt.links.new(mix2.outputs[2], em.inputs["Color"])
        nt.links.new(em.outputs[0], nt.nodes["Material Output"].inputs["Surface"])
    else:
        nt.links.new(mix2.outputs[2], bsdf.inputs["Base Color"])
    return m


def add_camera(name, loc, target=None, lens=45, ortho=None, rot=None):
    cam = bpy.data.cameras.new(name)
    cam.sensor_width = 36
    cam.clip_end = 300
    if ortho:
        cam.type = "ORTHO"
        cam.ortho_scale = ortho
    else:
        cam.lens = lens
    ob = bpy.data.objects.new(name, cam)
    ob.location = loc
    if target is not None:
        d = Vector(target) - Vector(loc)
        ob.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    if rot is not None:
        ob.rotation_euler = rot
    return link(ob)


CAMS = {  # fig = reference-figure ground position for that view
    "34przod": dict(loc=(-8.6, 10.2, 1.65), target=(-0.15, -0.9, 1.75), lens=42, fig=(2.7, 2.3)),
    "bok": dict(loc=(-30, -0.75, 1.95), rot=(math.radians(90), 0, math.radians(-90)), ortho=10.6, fig=(-2.0, 2.25)),
    "przod": dict(loc=(-0.45, 30, 2.15), rot=(math.radians(90), 0, math.radians(180)), ortho=8.4, fig=(-2.0, 2.25)),
    "34tyl": dict(loc=(-8.8, -14.8, 2.4), target=(0.45, -1.5, 1.65), lens=42, fig=(2.3, -5.9)),
}
CAMS["lakier"] = CAMS["34przod"]

VIEW_LABEL = {
    "34przod": "3/4 przód (persp.)", "bok": "bok lewy (ortho)", "przod": "przód (ortho)",
    "34tyl": "3/4 tył (persp.)", "lakier": "3/4 przód, wariant lakieru",
}
PAINTS = {
    "A": {"paint": ((0.085, 0.14, 0.20), 0.32, 0.0, 0.6), "trim": ((0.05, 0.05, 0.05), 0.6, 0, 0),
          "chassis": ((0.03, 0.03, 0.03), 0.6, 0, 0), "metal": ((0.6, 0.6, 0.6), 0.35, 1.0, 0)},
    "B": {"paint": ((0.060, 0.095, 0.072), 0.30, 0.0, 0.6), "trim": ((0.06, 0.06, 0.065), 0.55, 0, 0),
          "chassis": ((0.03, 0.03, 0.03), 0.6, 0, 0), "metal": ((0.6, 0.6, 0.6), 0.35, 1.0, 0)},
    "C": {"paint": ((0.40, 0.235, 0.06), 0.38, 0.0, 0.4), "trim": ((0.10, 0.10, 0.10), 0.6, 0, 0),
          "chassis": ((0.03, 0.03, 0.03), 0.6, 0, 0), "metal": ((0.55, 0.55, 0.55), 0.4, 1.0, 0)},
}
NAMES = {"A": "A · TRAKT — płaski front, long-haul", "B": "B · BIELIK — aero, rzeźbiona bryła",
         "C": "C · NAREW — użytkowa, przemysłowa"}


def stamp(text):
    r = bpy.context.scene.render
    r.use_stamp = True
    for a in ("date", "time", "render_time", "frame", "frame_range", "memory", "hostname", "camera", "lens",
              "scene", "marker", "filename", "sequencer_strip"):
        if hasattr(r, "use_stamp_" + a):
            setattr(r, "use_stamp_" + a, False)
    r.use_stamp_note = True
    r.stamp_note_text = text
    r.stamp_font_size = 20
    r.stamp_background = (0.08, 0.08, 0.08, 0.85)
    r.stamp_foreground = (0.92, 0.92, 0.92, 1)
    if hasattr(r, "use_stamp_labels"):
        r.use_stamp_labels = False


def measure(concept, out_dir):
    """Measured bounding box of the built truck (evaluated, with modifiers) -> JSON next to renders."""
    dg = bpy.context.evaluated_depsgraph_get()

    def bbox(pred):
        lo, hi = Vector((1e9,) * 3), Vector((-1e9,) * 3)
        for ob in bpy.data.objects:
            if ob.type not in {"MESH", "CURVE"} or not pred(ob):
                continue
            ev = ob.evaluated_get(dg)
            for c in ev.bound_box:
                w = ob.matrix_world @ Vector(c)
                lo = Vector(map(min, lo, w))
                hi = Vector(map(max, hi, w))
        return lo, hi

    truck = lambda ob: (ob.parent is None or ob.parent.name != "figure_root") and ob.name != "ground" \
        and not ob.name.startswith("wall_")
    body = lambda ob: truck(ob) and not ob.name.startswith(("mirror", "cam_", "kerb"))
    lo, hi = bbox(truck)
    blo, bhi = bbox(body)
    fifth = bpy.data.objects["fifth_plate"]
    fz = max((fifth.matrix_world @ Vector(c)).z for c in fifth.evaluated_get(dg).bound_box)
    res = {
        "concept": concept,
        "overall_length_m": round(hi.y - lo.y, 3),
        "front_overhang_m (axle->front)": round(hi.y, 3),
        "rear_overhang_m (axle->rear incl. lamps)": round(-lo.y - WB, 3),
        "wheelbase_m": WB,
        "overall_height_m": round(hi.z, 3),
        "width_body_m (no mirrors)": round(bhi.x - blo.x, 3),
        "width_incl_mirrors_m": round(hi.x - lo.x, 3),
        "fifth_wheel_height_m": round(fz, 3),
        "tyre_diameter_m": TYRE_D,
        "front_track_m": FRONT_TRACK,
        "rear_track_m": REAR_TRACK,
    }
    with open(os.path.join(out_dir, f"koncepcja-{concept}_wymiary.json"), "w", encoding="utf-8") as f:
        json.dump(res, f, indent=2, ensure_ascii=False)
    print("MEASURED", json.dumps(res, ensure_ascii=False))
    return res


def main():
    a = parse_args()
    a.out = os.path.abspath(a.out)  # Blender would resolve a relative output path against the drive root
    bpy.ops.wm.read_factory_settings(use_empty=True)
    global COLL
    COLL = bpy.context.scene.collection
    set_variant(None)
    setup_scene(a.res, a.samples)
    cfg = {"A": concept_A, "B": concept_B, "C": concept_C}[a.concept]()
    build_chassis(cfg)
    fig = mannequin()
    cab_rear_details()
    os.makedirs(a.out, exist_ok=True)
    measure(a.concept, a.out)
    sc = bpy.context.scene
    for v in a.views.split(","):
        c = CAMS[v]
        cam = add_camera("cam_" + v, c["loc"], c.get("target"), c.get("lens", 45), c.get("ortho"), c.get("rot"))
        sc.camera = cam
        fig.location = (*c["fig"], 0.0)
        for wname in ("wall_bok", "wall_przod"):
            bpy.data.objects[wname].hide_render = (wname != "wall_" + v)
        set_variant(PAINTS[a.concept] if v == "lakier" else None)
        stamp(f"{NAMES[a.concept]}  |  {VIEW_LABEL[v]}  |  siatka 1 m / 5 m, figura 1,80 m  |  blockout A2")
        sc.render.filepath = os.path.join(a.out, f"koncepcja-{a.concept}_{v}.jpg")
        bpy.ops.render.render(write_still=True)
        print("WROTE", sc.render.filepath)
    if a.blend:
        set_variant(None)
        os.makedirs(os.path.dirname(a.blend), exist_ok=True)
        bpy.ops.wm.save_as_mainfile(filepath=a.blend)


if __name__ == "__main__":
    main()
