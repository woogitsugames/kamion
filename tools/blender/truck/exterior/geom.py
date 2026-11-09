"""Geometry helpers for the BIELIK exterior (Track A3/A4).

Frame (same as A2 concepts and the A5 interior): 1 unit = 1 m, Blender Z up,
truck faces +Y, driver side (LHD) = -X, origin = ground under the front axle centre.
All meshes get a UV layer 'UVMap' (world-scale box projection, 1 UV = 1 m) unless a
builder writes its own (lathe parts: u = around, v = along profile).
"""
import json
import math
import os

import bmesh
import bpy
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
DIMS = json.load(open(os.path.join(REPO, "art-source", "truck", "dims.json"), encoding="utf-8"))


def D(key):
    return DIMS["values"][key]["value"]


V = Vector

# ---------------------------------------------------------------- dims (dims.json)
WB = D("wheelbase_m")
TYRE_D = D("tyre_diameter_m")
TYRE_W = D("tyre_section_width_m")
TYRE_R = TYRE_D / 2
WHEEL_Z = D("static_loaded_radius_m")
FRONT_TRACK = D("front_track_m")
REAR_TRACK = D("rear_track_m")
DUAL_SPACING = D("dual_spacing_m")
FIFTH_H = D("fifth_wheel_height_m")
FIFTH_LEAD = D("fifth_wheel_lead_m")
REAR_OH = D("rear_overhang_m")
CAB_BACK_Y = -D("cab_back_behind_front_axle_m")
CAB_HALF_W = D("cab_width_m") / 2
ROOF_Z = D("overall_height_m")
FRAME_HALF_W = D("frame_width_outer_m") / 2
FRAME_TOP = D("frame_top_height_m")
RIM_R = D("rim_flange_diameter_m") / 2
PCD_R = D("wheel_pcd_m") / 2
FLOOR_Z = D("cab_interior_floor_m")
EYE = Vector(D("driver_eye_point_m"))

# ---------------------------------------------------------------- object registry
STATE = {"coll": None, "group": "misc", "mats": {}}


def set_group(name):
    """Logical group (stats, tilt test, LOD plan): cab, lower, frame, wheels, lights, mirrors, ..."""
    STATE["group"] = name


def link(ob):
    STATE["coll"].objects.link(ob)
    ob["group"] = STATE["group"]
    return ob


def mat(name):
    return STATE["mats"][name]


# ---------------------------------------------------------------- UV
def box_uv(bm, scale=1.0):
    """World-scale box projection (UV-ready for tiling textures; atlas packing is A6)."""
    uv = bm.loops.layers.uv.get("UVMap") or bm.loops.layers.uv.new("UVMap")
    for f in bm.faces:
        n = f.normal
        ax = max(range(3), key=lambda i: abs(n[i]))
        for lp in f.loops:
            co = lp.vert.co
            if ax == 0:
                lp[uv].uv = (co.y * scale, co.z * scale)
            elif ax == 1:
                lp[uv].uv = (co.x * scale, co.z * scale)
            else:
                lp[uv].uv = (co.x * scale, co.y * scale)


def obj_from_bm(name, bm, m, smooth=True, sharp=35.0, uv=True):
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    if uv and not bm.loops.layers.uv.get("UVMap"):
        box_uv(bm)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    me.materials.append(mat(m))
    if smooth:
        me.shade_smooth()
        if sharp is not None and hasattr(me, "set_sharp_from_angle"):
            me.set_sharp_from_angle(angle=math.radians(sharp))
    else:
        me.shade_flat()
    return link(ob)


def bevel(ob, width, seg=2, angle=40, harden=True):
    if width <= 0:
        return ob
    m = ob.modifiers.new("bevel", "BEVEL")
    m.width = width
    m.segments = seg
    m.limit_method = "ANGLE"
    m.angle_limit = math.radians(angle)
    m.harden_normals = harden
    m.miter_outer = "MITER_ARC"
    return ob


# ---------------------------------------------------------------- primitives
def box(name, c, s, m, bev=0.0, seg=2, rot=None):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=Vector(s), verts=bm.verts)
    if rot is not None:
        bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=rot)
    bmesh.ops.translate(bm, vec=Vector(c), verts=bm.verts)
    return bevel(obj_from_bm(name, bm, m), bev, seg)


def box_mm(name, x0, x1, y0, y1, z0, z1, m, bev=0.0, seg=2):
    return box(name, ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2),
               (abs(x1 - x0), abs(y1 - y0), abs(z1 - z0)), m, bev, seg)


def _axis_rot(axis):
    if axis == "X":
        return Matrix.Rotation(math.pi / 2, 3, "Y")
    if axis == "Y":
        return Matrix.Rotation(math.pi / 2, 3, "X")
    return Matrix.Identity(3)


def cyl(name, c, r, depth, m, axis="X", seg=32, bev=0.0, bseg=2, r2=None, smooth=True):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=seg,
                          radius1=r, radius2=r if r2 is None else r2, depth=depth)
    bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=_axis_rot(axis))
    bmesh.ops.translate(bm, vec=Vector(c), verts=bm.verts)
    return bevel(obj_from_bm(name, bm, m, smooth=smooth, sharp=40), bev, bseg, angle=50)


def rod(name, p0, p1, r, m, seg=12):
    p0, p1 = Vector(p0), Vector(p1)
    d = p1 - p0
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=seg, radius1=r, radius2=r, depth=d.length)
    q = d.normalized().to_track_quat("Z", "Y")
    bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=q.to_matrix())
    bmesh.ops.translate(bm, vec=(p0 + p1) / 2, verts=bm.verts)
    return obj_from_bm(name, bm, m, sharp=50)


def sphere(name, c, r, m, scale=(1, 1, 1), useg=24, vseg=12):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=useg, v_segments=vseg, radius=r)
    bmesh.ops.scale(bm, vec=Vector(scale), verts=bm.verts)
    bmesh.ops.translate(bm, vec=Vector(c), verts=bm.verts)
    return obj_from_bm(name, bm, m, sharp=80)


def tube(name, pts, r, m, seg=10, closed=False, caps=True):
    """Polyline sweep with a round section (handles, rails, hoses)."""
    pts = [Vector(p) for p in pts]
    bm = bmesh.new()
    rings = []
    n = len(pts)
    for i, p in enumerate(pts):
        if closed:
            t = (pts[(i + 1) % n] - pts[i - 1])
        else:
            t = (pts[min(i + 1, n - 1)] - pts[max(i - 1, 0)])
        t.normalize()
        u = t.orthogonal().normalized()
        if rings:  # keep frame continuous
            prev_u = rings[-1][1]
            u = (prev_u - t * prev_u.dot(t)).normalized()
        w = t.cross(u)
        ring = [bm.verts.new(p + (u * math.cos(2 * math.pi * k / seg) + w * math.sin(2 * math.pi * k / seg)) * r)
                for k in range(seg)]
        rings.append((ring, u))
    rr = [r_[0] for r_ in rings]
    pairs = list(zip(rr, rr[1:])) + ([(rr[-1], rr[0])] if closed else [])
    for a, b in pairs:
        for k in range(seg):
            bm.faces.new((a[k], a[(k + 1) % seg], b[(k + 1) % seg], b[k]))
    if caps and not closed:
        bm.faces.new(list(reversed(rr[0])))
        bm.faces.new(rr[-1])
    return obj_from_bm(name, bm, m, sharp=60)


def extrude_poly(name, pts2d, depth, m, plane="XZ", origin=(0, 0, 0), bev=0.0, bseg=2, normal_sign=1):
    """Extrude a 2D polygon (list of (a, b)). plane 'XZ': a->X, b->Z, depth along +Y*normal_sign.
    'YZ': a->Y, b->Z, depth along +X*normal_sign. 'XY': a->X, b->Y, depth +Z."""
    o = Vector(origin)
    bm = bmesh.new()

    def P(a, b, d):
        if plane == "XZ":
            return o + Vector((a, d * normal_sign, b))
        if plane == "YZ":
            return o + Vector((d * normal_sign, a, b))
        return o + Vector((a, b, d * normal_sign))

    f0 = [bm.verts.new(P(a, b, 0)) for a, b in pts2d]
    f1 = [bm.verts.new(P(a, b, depth)) for a, b in pts2d]
    n = len(pts2d)
    bm.faces.new(f0)
    bm.faces.new(list(reversed(f1)))
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((f0[i], f0[j], f1[j], f1[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    # triangulate caps only if concave
    return bevel(obj_from_bm(name, bm, m, sharp=40), bev, bseg, angle=40)


def rrect(w, h, r, n=4):
    """Rounded rectangle centred at 0 (2D points, CCW)."""
    r = min(r, w / 2 - 1e-4, h / 2 - 1e-4)
    pts = []
    for cx, cy, a0 in ((w / 2 - r, h / 2 - r, 0), (-w / 2 + r, h / 2 - r, 90), (-w / 2 + r, -h / 2 + r, 180),
                       (w / 2 - r, -h / 2 + r, 270)):
        for i in range(n + 1):
            a = math.radians(a0 + 90 * i / n)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def lathe(name, profile, center, m, seg=64, side=1, axis="X", uv_v=None, smooth=True, sharp=50, closed_ends=False,
          a0=0.0, a1=360.0):
    """Revolve profile [(r, x_axial)] around an axis through center. side flips the axial direction.
    UV: u = angle / 360, v = normalised arc length along the profile (or uv_v list)."""
    c = Vector(center)
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("UVMap")
    full = abs(a1 - a0) >= 359.99
    nseg = seg
    cols = []
    for i in range(nseg + (0 if full else 1)):
        a = math.radians(a0 + (a1 - a0) * i / nseg)
        ca, sa = math.cos(a), math.sin(a)
        col = []
        for r, x in profile:
            if axis == "X":
                p = c + Vector((side * x, r * ca, r * sa))
            elif axis == "Y":
                p = c + Vector((r * ca, side * x, r * sa))
            else:
                p = c + Vector((r * ca, r * sa, side * x))
            col.append(bm.verts.new(p))
        cols.append(col)
    if uv_v is None:
        s = [0.0]
        for (r0, x0), (r1, x1) in zip(profile, profile[1:]):
            s.append(s[-1] + math.hypot(r1 - r0, x1 - x0))
        uv_v = [v / (s[-1] or 1) for v in s]
    ncol = len(cols)
    rng = range(ncol) if full else range(ncol - 1)
    for i in rng:
        a, b = cols[i], cols[(i + 1) % ncol]
        u0, u1 = i / nseg, (i + 1) / nseg
        for j in range(len(profile) - 1):
            try:
                f = bm.faces.new((a[j], b[j], b[j + 1], a[j + 1]))
            except ValueError:
                continue
            for lp, (uu, vv) in zip(f.loops, ((u0, uv_v[j]), (u1, uv_v[j]), (u1, uv_v[j + 1]), (u0, uv_v[j + 1]))):
                lp[uvl].uv = (uu, vv)
    if closed_ends:
        for j in (0, len(profile) - 1):
            ring = [col[j] for col in cols]
            if profile[j][0] > 1e-6:
                try:
                    bm.faces.new(ring if j else list(reversed(ring)))
                except ValueError:
                    pass
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    return obj_from_bm(name, bm, m, smooth=smooth, sharp=sharp, uv=False)


def arch(name, cy, cz, r_in, r_out, x0, x1, a0, a1, m, n=28):
    """Band around the X axis (mudguards, arch liners). Angles in degrees: 90 = top, 0 = towards +Y."""
    bm = bmesh.new()
    rings = []
    for i in range(n + 1):
        a = math.radians(a0 + (a1 - a0) * i / n)
        ca, sa = math.cos(a), math.sin(a)
        rings.append([bm.verts.new((x, cy + r * ca, cz + r * sa)) for (x, r) in
                      ((x0, r_in), (x1, r_in), (x1, r_out), (x0, r_out))])
    for a, b in zip(rings, rings[1:]):
        for k in range(4):
            bm.faces.new((a[k], a[(k + 1) % 4], b[(k + 1) % 4], b[k]))
    bm.faces.new(rings[0])
    bm.faces.new(list(reversed(rings[-1])))
    return obj_from_bm(name, bm, m, sharp=40)


def boolean(ob, cutters, op="DIFFERENCE"):
    """Apply EXACT booleans with one or more cutter objects (cutters are deleted). Call before adding
    other modifiers (bevel) to ob: everything on the stack is applied."""
    if not isinstance(cutters, (list, tuple)):
        cutters = [cutters]
    for c in cutters:
        md = ob.modifiers.new("bool", "BOOLEAN")
        md.operation = op
        md.object = c
        md.solver = "EXACT"
        md.material_mode = "TRANSFER"   # pocket walls take the cutter's material (dark), not the paint
        c.hide_render = True
    apply_mods(ob)
    for c in cutters:
        bpy.data.objects.remove(c, do_unlink=True)
    return ob


def apply_mods(ob):
    """Bake the evaluated mesh (all modifiers) into ob.data and clear the stack."""
    dg = bpy.context.evaluated_depsgraph_get()
    dg.update()
    me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
    old = ob.data
    ob.modifiers.clear()
    ob.data = me
    if old.users == 0:
        bpy.data.meshes.remove(old)
    return ob


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


def smoothstep(e0, e1, x):
    t = max(0.0, min(1.0, (x - e0) / (e1 - e0)))
    return t * t * (3 - 2 * t)


# ---------------------------------------------------------------- lofted body
class Loft:
    """Body from horizontal rounded-rectangle sections (plan view), stacked in z.

    front/back: y of the front/back face as f(z) (number or [(z, v)] table); w: half width f(z);
    rf/rb: plan corner radius front/back f(z); arc_n: segments per corner. Roof edge rounded with roof_r.
    Surface evaluation (front_pt / side_pt) lets patches, lamps and gaps follow the shell exactly.
    """

    def __init__(self, front, back, w, rf, rb, z0, ztop, roof_r=0.1, arc_n=10, step=0.04, flat_n=6, roof_n=10):
        self.front, self.back, self.w, self.rf, self.rb = front, back, w, rf, rb
        self.z0, self.ztop, self.roof_r = z0, ztop, roof_r
        self.arc_n, self.step, self.flat_n, self.roof_n = arc_n, step, flat_n, roof_n

    def sec(self, z):
        yf, yb = lerp_tab(self.front, z), lerp_tab(self.back, z)
        w, rf, rb = lerp_tab(self.w, z), lerp_tab(self.rf, z), lerp_tab(self.rb, z)
        zr = self.ztop - self.roof_r
        if z > zr and self.roof_r > 0:
            t = min(z - zr, self.roof_r)
            ins = self.roof_r - math.sqrt(max(self.roof_r ** 2 - t * t, 0))
            yf, yb, w = yf - ins, yb + ins, w - ins
        lim = min(w, (yf - yb) / 2) - 0.004
        return yf, yb, w, max(min(rf, lim), 0.003), max(min(rb, lim), 0.003)

    def arc(self, cx, cy, r, a0, a1, n=None):
        n = n or self.arc_n
        return [(cx + r * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
                 cy + r * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]

    def _line(self, p0, p1, n):
        return [(p0[0] + (p1[0] - p0[0]) * i / n, p0[1] + (p1[1] - p0[1]) * i / n) for i in range(1, n)]

    def ring(self, z):
        yf, yb, w, rf, rb = self.sec(z)
        fr = self.arc(w - rf, yf - rf, rf, 90, 0)
        br = self.arc(w - rb, yb + rb, rb, 0, -90)
        bl = self.arc(-(w - rb), yb + rb, rb, -90, -180)
        fl = self.arc(-(w - rf), yf - rf, rf, 180, 90)
        n = self.flat_n
        return (fr + self._line(fr[-1], br[0], n) + br + self._line(br[-1], bl[0], n // 2 + 1) + bl
                + self._line(bl[-1], fl[0], n) + fl + self._line(fl[-1], fr[0], n + 2))

    def levels(self):
        zs, z = [], self.z0
        zr = self.ztop - self.roof_r
        while z < zr - 1e-6:
            zs.append(z)
            z += self.step
        for i in range(self.roof_n + 1):
            zs.append(zr + self.roof_r * math.sin(math.pi / 2 * i / self.roof_n))
        extra = []
        for tab in (self.front, self.w, self.rf, self.back):
            if not isinstance(tab, (int, float)):
                extra += [k for k, _ in tab if self.z0 < k < zr]
        out = []
        for v in sorted(set(round(v, 5) for v in zs + extra)):
            if not out or v - out[-1] > 0.006:
                out.append(v)
        return out

    def build(self, name, m, sharp=40, cap_bottom=True):
        bm = bmesh.new()
        rings = []
        for z in self.levels():
            rings.append([bm.verts.new((x, y, z)) for x, y in self.ring(z)])
        k = len(rings[0])
        for a, b in zip(rings, rings[1:]):
            for i in range(k):
                bm.faces.new((a[i], a[(i + 1) % k], b[(i + 1) % k], b[i]))
        if cap_bottom:
            bm.faces.new(list(reversed(rings[0])))
        bm.faces.new(rings[-1])
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
        return obj_from_bm(name, bm, m, sharp=sharp)

    # --- surface evaluation ---
    def _corner_poly(self, z, which):
        yf, yb, w, rf, rb = self.sec(z)
        if which == "front":
            return (w - rf, yf - rf), self.arc(w - rf, yf - rf, rf, 90, 0, 48)
        return (w - rb, yb + rb), self.arc(w - rb, yb + rb, rb, 0, -90, 48)

    @staticmethod
    def _interp(pts, c, key, val, off):
        for p0, p1 in zip(pts, pts[1:]):
            lo, hi = sorted((p0[key], p1[key]))
            if lo - 1e-9 <= val <= hi + 1e-9:
                t = 0 if hi == lo else (val - p0[key]) / (p1[key] - p0[key])
                px, py = p0[0] + (p1[0] - p0[0]) * t, p0[1] + (p1[1] - p0[1]) * t
                dx, dy = px - c[0], py - c[1]
                ln = math.hypot(dx, dy) or 1
                return px + dx / ln * off, py + dy / ln * off
        p = pts[-1] if abs(val - pts[-1][key]) < abs(val - pts[0][key]) else pts[0]
        return p[0], p[1]

    def front_pt(self, z, x, off):
        """Point on the front/corner surface at height z and lateral x (x beyond the flat part runs onto the
        corner arc; |x| > w wraps further round the corner by arc length)."""
        yf, yb, w, rf, rb = self.sec(z)
        ax, sg = abs(x), (1 if x >= 0 else -1)
        if ax <= w - rf:
            return (x, yf + off, z)
        # parametrise the corner by arc length beyond the flat part
        s = ax - (w - rf)
        a = min(s / rf, math.pi / 2)
        extra = max(0.0, s - rf * math.pi / 2)
        cx, cy = w - rf, yf - rf
        px = cx + (rf + off) * math.sin(a)
        py = cy + (rf + off) * math.cos(a) - extra
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

    def normal_front(self, z, x):
        p0 = Vector(self.front_pt(z, x, 0.0))
        p1 = Vector(self.front_pt(z, x, 0.01))
        return (p1 - p0).normalized()

    def patch(self, name, m, kind, z0, z1, p0, p1, off=0.006, nz=10, npar=28, side=1, thick=0.0, smooth=True):
        """Surface-following patch; kind 'front' (param = x, wraps round the corner) or 'side' (param = y).
        p0/p1 may be functions of z. thick>0 closes it into a raised panel."""
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
        if len(grids) == 2:
            a, b = grids
            edge = ([(i, 0) for i in range(nz)] + [(nz, j) for j in range(npar)]
                    + [(i, npar) for i in range(nz, 0, -1)] + [(0, j) for j in range(npar, 0, -1)])
            for (i0, j0), (i1, j1) in zip(edge, edge[1:] + edge[:1]):
                bm.faces.new((a[i0][j0], a[i1][j1], b[i1][j1], b[i0][j0]))
        return obj_from_bm(name, bm, m, smooth=smooth, sharp=60)

    def quad_patch(self, name, m, kind, corners, off=0.006, nu=24, nv=10, side=1, thick=0.0):
        """Bilinear patch from 4 corners (param, z): bottom-start, bottom-end, top-end, top-start."""
        (p00, z00), (p10, z10), (p11, z11), (p01, z01) = corners
        bm = bmesh.new()
        layers = [off] if thick <= 0 else [off, off + thick]
        grids = []
        for o in layers:
            g = []
            for i in range(nv + 1):
                v = i / nv
                row = []
                for j in range(nu + 1):
                    u = j / nu
                    p = (p00 * (1 - u) + p10 * u) * (1 - v) + (p01 * (1 - u) + p11 * u) * v
                    z = (z00 * (1 - u) + z10 * u) * (1 - v) + (z01 * (1 - u) + z11 * u) * v
                    co = self.front_pt(z, p, o) if kind == "front" else self.side_pt(z, p, side, o)
                    row.append(bm.verts.new(co))
                g.append(row)
            grids.append(g)
        for g in grids:
            for i in range(nv):
                for j in range(nu):
                    bm.faces.new((g[i][j], g[i][j + 1], g[i + 1][j + 1], g[i + 1][j]))
        if len(grids) == 2:
            a, b = grids
            edge = ([(i, 0) for i in range(nv)] + [(nv, j) for j in range(nu)]
                    + [(i, nu) for i in range(nv, 0, -1)] + [(0, j) for j in range(nu, 0, -1)])
            for (i0, j0), (i1, j1) in zip(edge, edge[1:] + edge[:1]):
                bm.faces.new((a[i0][j0], a[i1][j1], b[i1][j1], b[i0][j0]))
        return obj_from_bm(name, bm, m, sharp=60)

    def poly_patch(self, name, m, kind, poly, off=0.006, side=1, thick=0.0, sub=3):
        """Patch from an arbitrary convex-ish polygon [(param, z)] projected on the surface (fan-filled,
        subdivided so it follows curvature)."""
        bm = bmesh.new()
        layers = [off] if thick <= 0 else [off, off + thick]
        cp = sum(p for p, _ in poly) / len(poly)
        cz = sum(z for _, z in poly) / len(poly)
        shells = []
        for o in layers:
            def P(p, z, o=o):
                return self.front_pt(z, p, o) if kind == "front" else self.side_pt(z, p, side, o)
            rim = []
            n = len(poly)
            for i in range(n):
                (pa, za), (pb, zb) = poly[i], poly[(i + 1) % n]
                for k in range(sub):
                    t = k / sub
                    rim.append((pa + (pb - pa) * t, za + (zb - za) * t))
            rings = [rim]
            for lvl in (0.66, 0.33):
                rings.append([(cp + (p - cp) * lvl, cz + (z - cz) * lvl) for p, z in rim])
            vr = [[bm.verts.new(P(p, z)) for p, z in ring] for ring in rings]
            cv = bm.verts.new(P(cp, cz))
            m_ = len(rim)
            for a, b in zip(vr, vr[1:]):
                for i in range(m_):
                    bm.faces.new((a[i], a[(i + 1) % m_], b[(i + 1) % m_], b[i]))
            for i in range(m_):
                bm.faces.new((vr[-1][i], vr[-1][(i + 1) % m_], cv))
            shells.append(vr[0])
        if len(shells) == 2:
            a, b = shells
            m_ = len(a)
            for i in range(m_):
                bm.faces.new((a[i], b[i], b[(i + 1) % m_], a[(i + 1) % m_]))
        return obj_from_bm(name, bm, m, sharp=60)

    def gap_v(self, name, side, y, z0, z1, w=0.009, off=0.0015, m="gap"):
        f = y if callable(y) else (lambda z, v=y: v)
        return self.patch(name, m, "side", z0, z1, lambda z: f(z) - w / 2, lambda z: f(z) + w / 2, off=off, nz=12,
                          npar=1, side=side)

    def gap_h(self, name, side, z, y0, y1, w=0.009, off=0.0015, m="gap"):
        return self.patch(name, m, "side", z - w / 2, z + w / 2, y0, y1, off=off, nz=1, npar=24, side=side)


# ---------------------------------------------------------------- SVG brand mark (art-source/truck/brand/bielik.svg)
def load_svg_mark(path):
    """Returns (feathers: list of polygons, strokes: list of (polyline, width)). SVG units, y down."""
    import re
    txt = open(path, encoding="utf-8").read()
    feathers = []  # list of subpaths; for an evenodd path the first is the outline, the rest are holes
    for d in re.findall(r'<path[^>]*d="([^"]+)"', txt):
        for sub in d.split("M")[1:]:
            nums = [float(v) for v in re.findall(r"-?\d+\.?\d*", sub)]
            feathers.append(list(zip(nums[0::2], nums[1::2])))
    sw = float(re.search(r'stroke-width="([\d.]+)"', txt).group(1))
    strokes = []
    for pts in re.findall(r'<polyline points="([^"]+)"', txt):
        strokes.append(([tuple(float(v) for v in p.split(",")) for p in pts.split()], sw))
    return feathers, strokes
