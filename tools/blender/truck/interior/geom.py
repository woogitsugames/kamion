"""Mesh helpers for the A5 cab interior (bmesh based, deterministic, no operators in edit mode).

Frame (same as the A2 blockout): 1 unit = 1 m, Z up, truck faces +Y, driver side (LHD) = -X,
origin = ground under the front axle centre.
"""
import math

import bmesh
import bpy
from mathutils import Matrix, Vector

STATE = {"coll": None, "mats": {}, "q": 1.0}


def Q(n, lo=3):
    """Tessellation count scaled by the LOD quality factor STATE['q'] (1.0 = LOD0)."""
    return max(lo, int(round(n * STATE["q"])))


def V(*a):
    return Vector(a[0] if len(a) == 1 else a)


def link(ob, coll=None):
    (coll or STATE["coll"]).objects.link(ob)
    return ob


def finish(name, bm, mat, smooth=True, sharp=35.0, coll=None, recalc=True):
    if recalc:
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    if isinstance(mat, (list, tuple)):
        for m in mat:
            me.materials.append(STATE["mats"][m])
    else:
        me.materials.append(STATE["mats"][mat])
    if smooth:
        for p in me.polygons:
            p.use_smooth = True
        if sharp is not None and hasattr(me, "set_sharp_from_angle"):
            me.set_sharp_from_angle(angle=math.radians(sharp))
    return link(ob, coll)


# ---------------------------------------------------------------- modifiers
def bevel(ob, width, seg=2, angle=35, harden=True, clamp=True):
    if width <= 0:
        return ob
    m = ob.modifiers.new("bevel", "BEVEL")
    m.width = width
    m.segments = seg if STATE["q"] >= 0.75 else max(1, seg - 1)
    m.limit_method = "ANGLE"
    m.angle_limit = math.radians(angle)
    m.harden_normals = harden
    m.use_clamp_overlap = clamp
    m.miter_outer = "MITER_ARC"
    return ob


def subsurf(ob, lvl=1):
    m = ob.modifiers.new("subd", "SUBSURF")
    m.levels = lvl
    m.render_levels = lvl
    m.uv_smooth = "PRESERVE_BOUNDARIES"
    return ob


def solidify(ob, t, offset=-1.0):
    m = ob.modifiers.new("solid", "SOLIDIFY")
    m.thickness = t
    m.offset = offset
    m.use_even_offset = True
    return ob


def wnormal(ob):
    m = ob.modifiers.new("wn", "WEIGHTED_NORMAL")
    m.keep_sharp = True
    return ob


# ---------------------------------------------------------------- 2D profiles
def rrect(w, h, r, n=4, cx=0.0, cy=0.0):
    """Closed rounded rectangle (CCW), r clamped; n segments per corner."""
    r = min(r, w / 2 - 1e-4, h / 2 - 1e-4)
    n = max(1, int(round(n * STATE["q"])))
    pts = []
    for (ox, oy, a0) in ((w / 2 - r, h / 2 - r, 0), (-w / 2 + r, h / 2 - r, 90),
                         (-w / 2 + r, -h / 2 + r, 180), (w / 2 - r, -h / 2 + r, 270)):
        for i in range(n + 1):
            a = math.radians(a0 + 90 * i / n)
            pts.append((cx + ox + r * math.cos(a), cy + oy + r * math.sin(a)))
    return pts


def circle2(r, n, cx=0.0, cy=0.0, a0=0.0):
    return [(cx + r * math.cos(a0 + 2 * math.pi * i / n), cy + r * math.sin(a0 + 2 * math.pi * i / n)) for i in range(n)]


def bez(p0, p1, p2, p3, n):
    out = []
    for i in range(n + 1):
        t = i / n
        a, b, c, d = (1 - t) ** 3, 3 * t * (1 - t) ** 2, 3 * t * t * (1 - t), t ** 3
        out.append(tuple(a * p0[k] + b * p1[k] + c * p2[k] + d * p3[k] for k in range(len(p0))))
    return out


def polyline_smooth(pts, n_per=4, tension=0.5):
    """Catmull-Rom through 2D/3D points (open), returns dense list."""
    P = [Vector(p) for p in pts]
    out = []
    for i in range(len(P) - 1):
        p0 = P[i - 1] if i > 0 else P[i] * 2 - P[i + 1]
        p1, p2 = P[i], P[i + 1]
        p3 = P[i + 2] if i + 2 < len(P) else P[i + 1] * 2 - P[i]
        for k in range(n_per):
            t = k / n_per
            t2, t3 = t * t, t * t * t
            v = 0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3)
            out.append(tuple(v))
    out.append(tuple(P[-1]))
    return out


def resample(pts, n):
    """Resample an open 2D/3D polyline to n points evenly by arc length."""
    P = [Vector(p) for p in pts]
    L = [0.0]
    for i in range(1, len(P)):
        L.append(L[-1] + (P[i] - P[i - 1]).length)
    out = []
    for k in range(n):
        s = L[-1] * k / (n - 1)
        j = 1
        while j < len(L) - 1 and L[j] < s:
            j += 1
        t = (s - L[j - 1]) / max(L[j] - L[j - 1], 1e-9)
        out.append(tuple(P[j - 1].lerp(P[j], t)))
    return out


# ---------------------------------------------------------------- lofts
def loft(name, loops, mat, closed=True, cap0=False, cap1=False, smooth=True, sharp=35.0, coll=None, mat_idx=None,
         mat_seg=None):
    """Skin consecutive loops (lists of 3D points with equal count). closed = loops are rings."""
    bm = bmesh.new()
    rows = [[bm.verts.new(p) for p in lp] for lp in loops]
    n = len(loops[0])
    m = n if closed else n - 1
    for li, (a, b) in enumerate(zip(rows[:-1], rows[1:])):
        for i in range(m):
            j = (i + 1) % n
            try:
                f = bm.faces.new((a[i], a[j], b[j], b[i]))
                if mat_idx:
                    f.material_index = mat_idx(f)
                elif mat_seg:
                    f.material_index = mat_seg(i, li)
            except ValueError:
                pass
    if cap0 and closed:
        bm.faces.new(list(reversed(rows[0])))
    if cap1 and closed:
        bm.faces.new(rows[-1])
    return finish(name, bm, mat, smooth, sharp, coll)


def extrude_profile(name, prof2d, frame_o, frame_u, frame_v, frame_w, depth, mat, bev=0.0, bseg=2, sharp=35.0):
    """Prism: 2D closed profile in (u,v) plane at origin frame_o, extruded depth along w."""
    o, u, v, w = Vector(frame_o), Vector(frame_u), Vector(frame_v), Vector(frame_w)
    l0 = [o + u * p[0] + v * p[1] for p in prof2d]
    l1 = [p + w * depth for p in l0]
    ob = loft(name, [l0, l1], mat, closed=True, cap0=True, cap1=True, sharp=sharp)
    return bevel(ob, bev, bseg)


def panel(name, prof2d, center, normal, up, thick, mat, bev=0.002, bseg=2, sharp=35.0):
    """Flat plate with a 2D outline, placed with its face normal = normal (front face at center)."""
    n = Vector(normal).normalized()
    upv = Vector(up)
    u = upv.cross(n).normalized()
    v = n.cross(u).normalized()
    return extrude_profile(name, prof2d, Vector(center), u, v, -n, thick, mat, bev, bseg, sharp)


# ---------------------------------------------------------------- primitives
def box(name, c, s, mat, bev=0.0, seg=2, rot=None, angle=35):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=Vector(s), verts=bm.verts)
    if rot is not None:
        bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=rot)
    bmesh.ops.translate(bm, vec=Vector(c), verts=bm.verts)
    return bevel(finish(name, bm, mat), bev, seg, angle)


def box_mm(name, x0, x1, y0, y1, z0, z1, mat, bev=0.0, seg=2):
    return box(name, ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), (abs(x1 - x0), abs(y1 - y0), abs(z1 - z0)),
               mat, bev, seg)


def cyl(name, c, r, depth, mat, axis="Z", seg=24, bev=0.0, bseg=2, r2=None, rot=None):
    bm = bmesh.new()
    seg = Q(seg, 8)
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=seg, radius1=r,
                          radius2=r if r2 is None else r2, depth=depth)
    if axis == "X":
        bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(math.pi / 2, 3, "Y"))
    elif axis == "Y":
        bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(-math.pi / 2, 3, "X"))
    if rot is not None:
        bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=rot)
    bmesh.ops.translate(bm, vec=Vector(c), verts=bm.verts)
    return bevel(finish(name, bm, mat, sharp=40), bev, bseg, angle=50)


def rod(name, p0, p1, r, mat, seg=12, r1=None, cap=True):
    p0, p1 = Vector(p0), Vector(p1)
    d = p1 - p0
    seg = Q(seg, 6)
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=cap, cap_tris=False, segments=seg, radius1=r,
                          radius2=r if r1 is None else r1, depth=d.length)
    q = d.normalized().to_track_quat("Z", "Y")
    bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=q.to_matrix())
    bmesh.ops.translate(bm, vec=(p0 + p1) / 2, verts=bm.verts)
    return finish(name, bm, mat, sharp=50)


def tube(name, path, r, mat, seg=12, n_per=1, cap=True, radii=None):
    """Swept circle along a 3D polyline (parallel-transport frames)."""
    P = [Vector(p) for p in path]
    seg = Q(seg, 6)
    loops = []
    prev_n = None
    for i, p in enumerate(P):
        t = (P[min(i + 1, len(P) - 1)] - P[max(i - 1, 0)]).normalized()
        if prev_n is None:
            a = Vector((0, 0, 1)) if abs(t.z) < 0.9 else Vector((1, 0, 0))
            nrm = t.cross(a).normalized()
        else:
            nrm = (prev_n - t * prev_n.dot(t)).normalized()
        prev_n = nrm
        b = t.cross(nrm)
        rr = radii[i] if radii else r
        loops.append([p + (nrm * math.cos(2 * math.pi * k / seg) + b * math.sin(2 * math.pi * k / seg)) * rr
                      for k in range(seg)])
    return loft(name, loops, mat, closed=True, cap0=cap, cap1=cap, sharp=60)


def sphere(name, c, r, mat, scale=(1, 1, 1), u=16, v=8):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=Q(u, 8), v_segments=Q(v, 4), radius=r)
    bmesh.ops.scale(bm, vec=Vector(scale), verts=bm.verts)
    bmesh.ops.translate(bm, vec=Vector(c), verts=bm.verts)
    return finish(name, bm, mat, sharp=80)


def strip(name, pts, nrm, width, mat, offset=0.0006, u_len=None):
    """Flat ribbon (decal strip) along a 3D polyline; nrm = surface normal per point or single vector.
    UV: U = arc length / u_len (tiles), V = 0..1 across. Used for stitching decals."""
    P = [Vector(p) for p in pts]
    N = [Vector(n) for n in nrm] if isinstance(nrm, list) else [Vector(nrm)] * len(P)
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("UVMap")
    a_row, b_row, s_acc = [], [], [0.0]
    for i, p in enumerate(P):
        t = (P[min(i + 1, len(P) - 1)] - P[max(i - 1, 0)]).normalized()
        side = N[i].cross(t).normalized()
        base = p + N[i] * offset
        a_row.append(bm.verts.new(base - side * width / 2))
        b_row.append(bm.verts.new(base + side * width / 2))
        if i:
            s_acc.append(s_acc[-1] + (P[i] - P[i - 1]).length)
    L = u_len or width * 4
    for i in range(len(P) - 1):
        f = bm.faces.new((a_row[i], a_row[i + 1], b_row[i + 1], b_row[i]))
        for lp, (u, v) in zip(f.loops, ((s_acc[i] / L, 0), (s_acc[i + 1] / L, 0), (s_acc[i + 1] / L, 1), (s_acc[i] / L, 1))):
            lp[uvl].uv = (u, v)
    ob = finish(name, bm, mat, smooth=True, sharp=None, recalc=False)
    ob["decal"] = True
    return ob


def disc_uv(name, center, normal, up, r, mat, uv_rect=((0, 0), (1, 1)), n=40, off=0.0):
    """Round display face (ngon) with UVs mapped from the square uv_rect=((u0,v0),(u1,v1))."""
    c, u, v, nn = frame_at(center, normal, up)
    c = c + nn * off
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("UVMap")
    pts = [(math.cos(2 * math.pi * i / n), math.sin(2 * math.pi * i / n)) for i in range(n)]
    vs = [bm.verts.new(c + u * (px * r) + v * (py * r)) for px, py in pts]
    f = bm.faces.new(vs)
    (u0, v0), (u1, v1) = uv_rect
    for lp, (px, py) in zip(f.loops, pts):
        lp[uvl].uv = (u0 + (u1 - u0) * (px * 0.5 + 0.5), v0 + (v1 - v0) * (py * 0.5 + 0.5))
    ob = finish(name, bm, mat, smooth=False, recalc=False)
    ob["fixed_uv"] = True
    return ob


def plane_uv(name, corners, mat, uv=((0, 0), (1, 0), (1, 1), (0, 1))):
    """Single quad with explicit 0-1 UVs (displays, labels). corners CCW seen from the front."""
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("UVMap")
    vs = [bm.verts.new(Vector(c)) for c in corners]
    f = bm.faces.new(vs)
    for lp, t in zip(f.loops, uv):
        lp[uvl].uv = t
    ob = finish(name, bm, mat, smooth=False, recalc=False)
    ob["fixed_uv"] = True
    return ob


def frame_at(center, normal, up):
    n = Vector(normal).normalized()
    u = Vector(up).cross(n).normalized()
    v = n.cross(u).normalized()
    return Vector(center), u, v, n


def quad_on(center, normal, up, w, h, off=0.0):
    c, u, v, n = frame_at(center, normal, up)
    c = c + n * off
    return [c - u * w / 2 - v * h / 2, c + u * w / 2 - v * h / 2, c + u * w / 2 + v * h / 2, c - u * w / 2 + v * h / 2]


def parent_keep(child, parent):
    child.parent = parent
    child.matrix_parent_inverse = parent.matrix_world.inverted()
