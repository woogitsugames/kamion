"""Hero depot hall asset (ADR 0071): spec (streetscape.hero_depot) -> art-source/world/landmarks/<asset>/<asset>.glb.

blender -b --factory-startup -P tools/blender/world/landmarks/make_depot.py -- --spec <spec.json>
        [--render <abs dir>] [--blend]

One prototype per facade segment (`landmark_depot_<asset>_<NN>`, `.lod1`, `.lod2`) plus the roof
(`landmark_depot_<asset>_roof`). Geometry is built in the region frame (local E, N, U) and written relative to the
segment anchor with glTF axes (x, y, z) = (-dE, dU, dN), the frame of art-source/world/props/street_props.glb, so the
instance needs no rotation. Materials are world material NAMES (tools/worldgen/streetscape/materials.py): the engine
binds the region PBR sets by name; UV0 is in metres (u along the facade, v up). `--render` writes control renders
(plain colours of the material table, no textures) instead of the GLB.

Detail by LOD:  0  recessed openings with reveals, dock equipment (sectional door, shelter, leveller, bumpers, wheel
                   guides, number plate, signal and flood light), strip-window frames with mullions, louvre slats,
                   downpipes with hoppers, doors with steps / stairs, wall lights, coping, annexes, roof lights
                1  the same openings flush (no reveals), docks as shelter + leveller + guides, frames as flat bars
                2  walls with flush colour fields for docks / strips / louvres / drive doors, plain annex boxes
"""
import hashlib
import importlib.util
import json
import math
import sys
from pathlib import Path

import bmesh
import bpy
import numpy as np
from mathutils import Vector
from mathutils.geometry import tessellate_polygon

REPO = Path(__file__).resolve().parents[4]
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def arg(name, default=None):
    return argv[argv.index(name) + 1] if name in argv else default


SPEC_PATH = Path(arg("--spec"))
if not SPEC_PATH.is_absolute():
    SPEC_PATH = REPO / SPEC_PATH
SPEC = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
ASSET = SPEC["asset"]
OUT = REPO / "art-source" / "world" / "landmarks" / ASSET
PRM = SPEC["params"]
ZREF, ZBOT, ZTOP = SPEC["zref"], SPEC["zbot"], SPEC["ztop"]
ZPAR = ZTOP + PRM["parapet_h_m"]                 # top of the attic wall (coping sits on it)

WALL, ACCENT, GLASSB, PLINTH, FLASH = "kp_wall", "kp_accent", "kp_glass_block", "hall_plinth", "hall_flashing"

_spec = importlib.util.spec_from_file_location("wm", REPO / "tools" / "worldgen" / "streetscape" / "materials.py")
_wm = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_wm)
WORLD_MATS = _wm.M


def sha(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def hf(*key):
    """Deterministic 0..1 hash (wear / asymmetry choices are stable between builds)."""
    return int(hashlib.sha1(repr(key).encode()).hexdigest()[:8], 16) / 0xFFFFFFFF


# ---------------------------------------------------------------------------------------------------- mesh soup
class MB:
    def __init__(self):
        self.V, self.F, self.UV, self.M = [], [], [], []

    def poly(self, P, UV, mat, hint=None):
        P = [np.asarray(p, float) for p in P]
        if hint is not None:
            n = np.cross(P[1] - P[0], P[-1] - P[0])
            if float(np.dot(n, hint)) < 0:
                P, UV = P[::-1], UV[::-1]
        b = len(self.V)
        self.V += P
        self.F.append(tuple(range(b, b + len(P))))
        self.UV.append([tuple(map(float, u)) for u in UV])
        self.M.append(mat)

    def tris(self):
        return sum(len(f) - 2 for f in self.F)

    def to_object(self, name, anchor):
        me = bpy.data.meshes.new(name)
        a = np.asarray(anchor, float)
        V = np.array(self.V).reshape(-1, 3) - a
        V = np.column_stack([-V[:, 0], -V[:, 1], V[:, 2]])          # Blender (-dE, -dN, dU) -> glTF (-dE, dU, dN)
        me.from_pydata([tuple(v) for v in V], [], self.F)
        uvl = me.uv_layers.new(name="UVMap")
        k = 0
        for uvs in self.UV:
            for u in uvs:
                uvl.data[k].uv = u
                k += 1
        names = sorted(set(self.M))
        for n in names:
            me.materials.append(material(n))
        idx = {n: i for i, n in enumerate(names)}
        for p, m in zip(me.polygons, self.M):
            p.material_index = idx[m]
            p.use_smooth = False
        me.update()
        ob = bpy.data.objects.new(name, me)
        bpy.context.scene.collection.objects.link(ob)
        me.calc_loop_triangles()
        return ob, len(me.loop_triangles)


_MATS = {}


def material(name):
    if name in _MATS:
        return _MATS[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    d = WORLD_MATS.get(name, {})
    bsdf = m.node_tree.nodes["Principled BSDF"]
    c = d.get("color", [0.5, 0.0, 0.5])
    bsdf.inputs["Base Color"].default_value = (c[0], c[1], c[2], 1)
    bsdf.inputs["Roughness"].default_value = d.get("rough", 0.6)
    bsdf.inputs["Metallic"].default_value = d.get("metal", 0.0)
    if "--render" in argv and name in (WALL, "dock_door"):       # preview only: course / leaf lines so scale reads
        nt = m.node_tree
        tc = nt.nodes.new("ShaderNodeTexCoord")
        sep = nt.nodes.new("ShaderNodeSeparateXYZ")
        mth = nt.nodes.new("ShaderNodeMath")
        mth.operation = "FRACT"
        mul = nt.nodes.new("ShaderNodeMath")
        mul.operation = "MULTIPLY"
        mul.inputs[1].default_value = 1.0 / (0.25 if name == WALL else 0.5)
        gt = nt.nodes.new("ShaderNodeMath")
        gt.operation = "GREATER_THAN"
        gt.inputs[1].default_value = 0.22 if name == WALL else 0.04
        mix = nt.nodes.new("ShaderNodeMixRGB")
        mix.inputs[1].default_value = (c[0] * 0.6, c[1] * 0.6, c[2] * 0.6, 1)
        mix.inputs[2].default_value = (c[0], c[1], c[2], 1)
        nt.links.new(tc.outputs["UV"], sep.inputs[0])
        nt.links.new(sep.outputs["X" if name == WALL else "Y"], mul.inputs[0])
        nt.links.new(mul.outputs[0], mth.inputs[0])
        nt.links.new(mth.outputs[0], gt.inputs[0])
        nt.links.new(gt.outputs[0], mix.inputs[0])
        nt.links.new(mix.outputs[0], bsdf.inputs["Base Color"])
    m.use_backface_culling = True
    _MATS[name] = m
    return m


# ---------------------------------------------------------------------------------------------------- facade frame
class Fr:
    """Frame of a wall: a = start (E, N), d = along, n = outward. P(u, z, o) = point u along, o metres proud."""

    def __init__(self, a, b, u_off=0.0):
        self.a = np.asarray(a, float)
        b = np.asarray(b, float)
        self.L = float(np.linalg.norm(b - self.a))
        self.d = (b - self.a) / self.L
        self.n = np.array([self.d[1], -self.d[0]])
        self.n3 = np.array([self.n[0], self.n[1], 0.0])
        self.d3 = np.array([self.d[0], self.d[1], 0.0])
        self.u_off = u_off                  # UV u offset (continuous cladding courses round the building)

    def P(self, u, z, o=0.0):
        q = self.a + self.d * u + self.n * o
        return np.array([q[0], q[1], z])

    def front(self, mb, u0, u1, z0, z1, mat, o=0.0, uv=None):
        if u1 - u0 < 1e-4 or z1 - z0 < 1e-4:
            return
        if uv is None:
            uv = [(self.u_off + u0, z0 - ZREF), (self.u_off + u1, z0 - ZREF), (self.u_off + u1, z1 - ZREF),
                  (self.u_off + u0, z1 - ZREF)]
            if mat == WALL:           # trapezoid_sheet has vertical ribs along u: swapped UV lays the sheet horizontally
                uv = [(v, u) for u, v in uv]
        mb.poly([self.P(u0, z0, o), self.P(u1, z0, o), self.P(u1, z1, o), self.P(u0, z1, o)], uv, mat, self.n3)

    def box(self, mb, u0, u1, z0, z1, o0, o1, mat, faces="flrt", uvs=1.0):
        """Box between offsets o0 (wall side) and o1 (front). faces: f front, k back, l / r ends, t top, B bottom."""
        P = self.P
        w, h, dp = (u1 - u0) * uvs, (z1 - z0) * uvs, abs(o1 - o0) * uvs
        if "f" in faces:
            mb.poly([P(u0, z0, o1), P(u1, z0, o1), P(u1, z1, o1), P(u0, z1, o1)], [(0, 0), (w, 0), (w, h), (0, h)], mat, self.n3)
        if "k" in faces:
            mb.poly([P(u0, z0, o0), P(u1, z0, o0), P(u1, z1, o0), P(u0, z1, o0)], [(0, 0), (w, 0), (w, h), (0, h)], mat, -self.n3)
        if "l" in faces:
            mb.poly([P(u0, z0, o0), P(u0, z0, o1), P(u0, z1, o1), P(u0, z1, o0)], [(0, 0), (dp, 0), (dp, h), (0, h)], mat, -self.d3)
        if "r" in faces:
            mb.poly([P(u1, z0, o0), P(u1, z0, o1), P(u1, z1, o1), P(u1, z1, o0)], [(0, 0), (dp, 0), (dp, h), (0, h)], mat, self.d3)
        if "t" in faces:
            mb.poly([P(u0, z1, o0), P(u1, z1, o0), P(u1, z1, o1), P(u0, z1, o1)], [(0, 0), (w, 0), (w, dp), (0, dp)], mat, (0, 0, 1))
        if "B" in faces:
            mb.poly([P(u0, z0, o0), P(u1, z0, o0), P(u1, z0, o1), P(u0, z0, o1)], [(0, 0), (w, 0), (w, dp), (0, dp)], mat, (0, 0, -1))

    def reveal(self, mb, u0, u1, z0, z1, depth, mat, sill=True):
        """Four reveal faces of an opening recessed by depth."""
        P = self.P
        dp = depth
        mb.poly([P(u0, z0, 0), P(u0, z0, -dp), P(u0, z1, -dp), P(u0, z1, 0)], [(0, 0), (dp, 0), (dp, z1 - z0), (0, z1 - z0)], mat, self.d3)
        mb.poly([P(u1, z0, 0), P(u1, z0, -dp), P(u1, z1, -dp), P(u1, z1, 0)], [(0, 0), (dp, 0), (dp, z1 - z0), (0, z1 - z0)], mat, -self.d3)
        mb.poly([P(u0, z1, 0), P(u1, z1, 0), P(u1, z1, -dp), P(u0, z1, -dp)], [(0, 0), (u1 - u0, 0), (u1 - u0, dp), (0, dp)], mat, (0, 0, -1))
        if sill:
            mb.poly([P(u0, z0, 0), P(u1, z0, 0), P(u1, z0, -dp), P(u0, z0, -dp)], [(0, 0), (u1 - u0, 0), (u1 - u0, dp), (0, dp)], mat, (0, 0, 1))


def ground_at(e, u):
    g = e["ground"]
    us = [p[0] for p in g]
    zs = [p[1] for p in g]
    return float(np.interp(u, us, zs))


# ---------------------------------------------------------------------------------------------------- features
def edge_openings(e, annexes, lod):
    """[(u0, u1, z0, z1, kind, data)] of an edge; z absolute."""
    f = e["features"]
    ops = []
    if "docks" in f:
        dk = f["docks"]
        zf = dk["yard_z"] + PRM["dock_floor_h_m"]
        for k in range(dk["count"]):
            u = dk["first_u_m"] + k * dk["pitch_m"]
            hw = PRM["dock_shelter_w_m"] / 2 if lod == 2 else PRM["dock_door_w_m"] / 2
            ops.append((u - hw, u + hw, zf, zf + (PRM["dock_shelter_h_m"] if lod == 2 else PRM["dock_door_h_m"]), "dock",
                        {"num": dk["first_num"] + k, "open": float(dk["open"].get(str(dk["first_num"] + k), 0.0)),
                         "yard_z": dk["yard_z"], "guide": (dk["first_num"] + k) not in dk["missing_guides"]}))
    for s in f.get("strips") or []:
        zs = ZREF + float(s.get("sill_m", PRM["strip_sill_m"]))
        ops.append((s["u0_m"], s["u1_m"], zs, zs + float(s.get("h_m", PRM["strip_h_m"])), "strip", s))
    for s in f.get("louvres") or []:
        zs = ZREF + float(s.get("sill_m", PRM["strip_sill_m"]))
        ops.append((s["u0_m"], s["u1_m"], zs, zs + float(s.get("h_m", PRM["strip_h_m"])), "louvre", s))
    for dr in f.get("drive_doors") or []:
        zg = ground_at(e, dr["u_m"]) + 0.02
        ops.append((dr["u_m"] - dr["w_m"] / 2, dr["u_m"] + dr["w_m"] / 2, zg, zg + dr["h_m"], "drive", dr))
    if lod < 2:
        for dr in f.get("doors") or []:
            zg = ground_at(e, dr["u_m"]) + 0.15
            if dr.get("stairs") and "docks" in f:
                zg = f["docks"]["yard_z"] + PRM["dock_floor_h_m"]
            ops.append((dr["u_m"] - 0.5, dr["u_m"] + 0.5, zg, zg + 2.1, "door", dr))
        ow = f.get("office_windows")
        if ow:
            n = int((ow["u1_m"] - ow["u0_m"]) // ow["bay_m"])
            for k in range(n):
                uc = ow["u0_m"] + (k + 0.5) * ow["bay_m"]
                for sl in ow["sills_m"]:
                    zs = ZREF + sl
                    ops.append((uc - ow["w_m"] / 2, uc + ow["w_m"] / 2, zs, zs + ow["h_m"], "window", ow))
    else:
        ow = f.get("office_windows")
        if ow:
            for sl in ow["sills_m"]:
                ops.append((ow["u0_m"], ow["u1_m"], ZREF + sl + 0.2, ZREF + sl + ow["h_m"] - 0.2, "band", ow))
    return sorted(ops, key=lambda o: o[0])


def plinth_top(e, u):
    f = e["features"]
    if "docks" in f:
        dk = f["docks"]
        u0 = dk["first_u_m"] - 3.2
        u1 = dk["first_u_m"] + (dk["count"] - 1) * dk["pitch_m"] + 6.4      # incl. the stair door next to the row
        if u0 <= u <= u1:
            return dk["yard_z"] + PRM["dock_floor_h_m"]
    return ZREF + PRM["plinth_h_m"]


def build_wall(mb, e, fr, ua, ub, ops, lod):
    """Wall between stations ua..ub with rectangular openings cut out (columns between opening edges)."""
    cuts = {ua, ub}
    for o in ops:
        for u in (o[0], o[1]):
            if ua < u < ub:
                cuts.add(u)
    f = e["features"]
    if "docks" in f:                                  # plinth step at the ends of the dock platform
        dk = f["docks"]
        for u in (dk["first_u_m"] - 3.2, dk["first_u_m"] + (dk["count"] - 1) * dk["pitch_m"] + 6.4):
            if ua < u < ub:
                cuts.add(u)
    cs = sorted(cuts)
    for u0, u1 in zip(cs[:-1], cs[1:]):
        um = (u0 + u1) / 2
        zp = plinth_top(e, um)
        col = sorted([o for o in ops if o[0] <= um <= o[1]], key=lambda o: o[2])
        z = ZBOT
        spans = []
        for o in col:
            if o[2] > z:
                spans.append((z, o[2]))
            z = max(z, o[3])
        if z < ZPAR:
            spans.append((z, ZPAR))
        for z0, z1 in spans:
            if z0 < zp < z1:
                fr.front(mb, u0, u1, z0, zp, PLINTH)
                fr.front(mb, u0, u1, zp, z1, WALL)
            else:
                fr.front(mb, u0, u1, z0, z1, PLINTH if z1 <= zp else WALL)


def build_dock(mb, fr, o, lod):
    u0, u1, zf, z1, _, d = o
    uc = (u0 + u1) / 2
    W = PRM["dock_door_w_m"]
    u0, u1, z1 = uc - W / 2, uc + W / 2, zf + PRM["dock_door_h_m"]
    sw, sh, sd = PRM["dock_shelter_w_m"], PRM["dock_shelter_h_m"], PRM["dock_shelter_d_m"]
    side = (sw - W) / 2 + 0.05
    zy = d["yard_z"]
    num = d["num"]
    if lod == 2:                       # opening = the whole shelter rectangle: door + dark frame bars, flush
        fr.front(mb, u0, u1, zf, z1, "dock_door", uv=[(0, 0), (W, 0), (W, z1 - zf), (0, z1 - zf)])
        fr.front(mb, uc - sw / 2, u0, zf, zf + sh, "dock_shelter")
        fr.front(mb, u1, uc + sw / 2, zf, zf + sh, "dock_shelter")
        fr.front(mb, u0, u1, z1, zf + sh, "dock_shelter")
        return
    rec = 0.22 if lod == 0 else 0.0
    lift = d["open"] * (z1 - zf) if lod == 0 else 0.0
    if lod == 0:
        fr.reveal(mb, u0, u1, zf, z1, rec, FLASH, sill=False)
        # dock floor seen through an open door + dark interior
        if lift > 0:
            fr.front(mb, u0, u1, zf, zf + lift, "dock_shelter", o=-2.4)
            P = fr.P
            mb.poly([P(u0, zf, -2.4), P(u1, zf, -2.4), P(u1, zf, -rec), P(u0, zf, -rec)],
                    [(0, 0), (W, 0), (W, 2.2), (0, 2.2)], "concrete_base", (0, 0, 1))
            for uu, hn in ((u0, fr.d3), (u1, -fr.d3)):
                mb.poly([P(uu, zf, -rec), P(uu, zf, -2.4), P(uu, zf + lift, -2.4), P(uu, zf + lift, -rec)],
                        [(0, 0), (2.2, 0), (2.2, lift), (0, lift)], "dock_shelter", hn)
            mb.poly([P(u0, zf + lift, -2.4), P(u1, zf + lift, -2.4), P(u1, zf + lift, -rec), P(u0, zf + lift, -rec)],
                    [(0, 0), (W, 0), (W, 2.2), (0, 2.2)], "dock_shelter", (0, 0, -1))
            fr.box(mb, u0, u1, zf + lift - 0.06, zf + lift, -rec - 0.05, -rec, "rubber_black", faces="B")
    fr.front(mb, u0, u1, zf + lift, z1, "dock_door", o=-rec, uv=[(0, 0), (W, 0), (W, z1 - zf - lift), (0, z1 - zf - lift)])
    if lod == 0 and lift == 0:        # row of small vision panels in the 4th leaf
        for k in range(3):
            uu = u0 + W * (0.2 + 0.3 * k)
            fr.front(mb, uu - 0.3, uu + 0.3, zf + 1.62, zf + 1.86, "glass", o=-rec + 0.012)
    # shelter: side curtains + header (PVC on a steel frame); wear: one side curtain slightly shorter on some docks
    faces = "flrt" if lod == 0 else "flr"
    for sgn in (-1, 1):
        ue = uc + sgn * (W / 2 + side)
        ui = uc + sgn * (W / 2 - 0.3)
        a, b = min(ue, ui), max(ue, ui)
        zb = zf - 0.1 + (0.25 if hf(ASSET, num, sgn, "sag") < 0.2 else 0.0)
        fr.box(mb, a, b, zb, zf + sh - 0.7, 0.0, sd, "dock_shelter", faces=faces)
        if lod == 0:                  # yellow guide strip on the curtain face
            um = uc + sgn * (W / 2 + side / 2 - 0.1)
            fr.front(mb, um - 0.05, um + 0.05, zb + 0.15, zf + sh - 0.9, "paint_yellow", o=sd + 0.006)
    fr.box(mb, uc - sw / 2 - 0.05, uc + sw / 2 + 0.05, zf + sh - 0.7, zf + sh, 0.0, sd + 0.02, "dock_shelter",
           faces="flrtB" if lod == 0 else "flrB")
    if lod == 0:
        fr.box(mb, uc - sw / 2 - 0.08, uc + sw / 2 + 0.08, zf + sh, zf + sh + 0.05, 0.0, sd + 0.06, "steel_galv", faces="flrt")
    # leveller lip + hazard stripes on its front, steel bumper plates + rubber bumpers
    fr.box(mb, uc - 1.0, uc + 1.0, zf - 0.34, zf, 0.0, 0.4, "steel_checker", faces="lrt")
    fr.front(mb, uc - 1.0, uc + 1.0, zf - 0.34, zf, "hazard_stripes", o=0.4, uv=[(0, 0), (2.0, 0), (2.0, 0.34), (0, 0.34)])
    if lod == 0:
        for sgn in (-1, 1):
            if hf(ASSET, num, sgn, "bumper") < 0.08:
                continue                       # a lost bumper: bare steel plate only
            ub = uc + sgn * 1.2
            fr.box(mb, ub - 0.16, ub + 0.16, zf - 0.55, zf - 0.02, 0.0, 0.02, "steel_galv", faces="flrt")
            fr.box(mb, ub - 0.125, ub + 0.125, zf - 0.5, zf - 0.05, 0.02, PRM["bumper_proud_m"], "rubber_black", faces="flrt")
    # wheel guides on the apron (yellow steel tube, 4.2 m), both sides
    if d["guide"] or lod > 0:
        for sgn in (-1, 1):
            ug = uc + sgn * 1.42
            fr.box(mb, ug - 0.05, ug + 0.05, zy + 0.14, zy + 0.24, 0.45, 4.4, "paint_yellow", faces="flrtB" if lod == 0 else "lrt")
            if lod == 0:                      # feet of the guide tube + its bent-down nose
                for og in (0.6, 2.4, 4.2):
                    fr.box(mb, ug - 0.04, ug + 0.04, zy - 0.05, zy + 0.14, og, og + 0.1, "paint_yellow", faces="flrk")
                Pg = fr.P
                for sx in (-0.05, 0.05):
                    mb.poly([Pg(ug + sx, zy + 0.14, 4.4), Pg(ug + sx, zy, 4.75), Pg(ug + sx, zy + 0.1, 4.75), Pg(ug + sx, zy + 0.24, 4.4)],
                            [(0, 0), (0.4, 0), (0.4, 0.1), (0, 0.1)], "paint_yellow", fr.d3 * (1 if sx > 0 else -1))
                mb.poly([Pg(ug - 0.05, zy + 0.24, 4.4), Pg(ug + 0.05, zy + 0.24, 4.4), Pg(ug + 0.05, zy + 0.1, 4.75), Pg(ug - 0.05, zy + 0.1, 4.75)],
                        [(0, 0), (0.1, 0), (0.1, 0.4), (0, 0.4)], "paint_yellow", (0, 0, 1))
    if lod == 0:
        # number plate above the shelter (white plate, black digits: atlas u = digit / 10)
        s = str(num)
        pw = 0.32 * len(s)
        z0 = zf + sh + 0.22
        du = (hf(ASSET, num, "plate") - 0.5) * 0.08
        fr.box(mb, uc + du - pw / 2 - 0.07, uc + du + pw / 2 + 0.07, z0 - 0.07, z0 + 0.47, 0.0, 0.03, "plate_white", faces="flrt")
        for k, ch in enumerate(s):
            x0 = uc + du - pw / 2 + k * 0.32
            dg = int(ch)
            fr.front(mb, x0, x0 + 0.32, z0, z0 + 0.4, "dock_digits", o=0.036,
                     uv=[(dg / 10, 0), ((dg + 1) / 10, 0), ((dg + 1) / 10, 1), (dg / 10, 1)])
        # signal light box right of the door, conduit down to the control box
        ul = uc + W / 2 + side + 0.38
        fr.box(mb, ul - 0.11, ul + 0.11, zf + 1.5, zf + 1.95, 0.0, 0.14, "dock_light", faces="flrtB")
        fr.box(mb, ul - 0.02, ul + 0.02, zf + 0.9, zf + 1.5, 0.0, 0.03, "steel_galv", faces="flr")
        fr.box(mb, ul - 0.15, ul + 0.15, zf + 0.5, zf + 0.9, 0.0, 0.12, "steel_painted_grey", faces="flrtB")
        # floodlight on a wall arm above the shelter, left of centre
        zl = zf + sh + 0.95
        fr.box(mb, uc - 0.93, uc - 0.87, zl - 0.03, zl + 0.03, 0.0, 0.5, "steel_galv", faces="lrtB")
        fr.box(mb, uc - 1.06, uc - 0.74, zl - 0.11, zl - 0.02, 0.42, 0.66, "luminaire_housing", faces="flrtk")
        P = fr.P
        mb.poly([P(uc - 1.04, zl - 0.112, 0.44), P(uc - 0.76, zl - 0.112, 0.44), P(uc - 0.76, zl - 0.112, 0.64),
                 P(uc - 1.04, zl - 0.112, 0.64)], [(0, 0), (1, 0), (1, 1), (0, 1)], "lamp_glass", (0, 0, -1))


def build_strip(mb, fr, o, lod, louvre=False):
    u0, u1, z0, z1, _, _ = o
    fw = PRM["strip_frame_m"]
    if lod == 2:
        if louvre:
            fr.front(mb, u0, u1, z0, z1, ACCENT)
        else:
            fr.front(mb, u0, u1, z0, z0 + fw, ACCENT)
            fr.front(mb, u0, u1, z0 + fw, z1 - fw, GLASSB)
            fr.front(mb, u0, u1, z1 - fw, z1, ACCENT)
        return
    rec = 0.06 if lod == 0 else 0.0
    # vermilion frame (flush bars at LOD1, proud box bars at LOD0)
    bars = [(u0, u1, z0, z0 + fw), (u0, u1, z1 - fw, z1), (u0, u0 + fw, z0 + fw, z1 - fw), (u1 - fw, u1, z0 + fw, z1 - fw)]
    for a, b, c, d in bars:
        if lod == 0:
            fr.box(mb, a, b, c, d, -rec, 0.05, ACCENT, faces="flrtB")
        else:
            fr.front(mb, a, b, c, d, ACCENT)
    gi = (u0 + fw, u1 - fw, z0 + fw, z1 - fw)
    if louvre:
        fr.front(mb, gi[0], gi[1], gi[2], gi[3], "dock_shelter", o=-rec - 0.05)
        if lod == 0:
            P = fr.P
            n = int((gi[3] - gi[2]) / 0.42)                # broad slats with dark gaps (CC0 photo)
            for k in range(n):
                za = gi[2] + (k + 0.12) * (gi[3] - gi[2]) / n
                zb = za + 0.27
                mb.poly([P(gi[0], za, 0.02), P(gi[1], za, 0.02), P(gi[1], zb, -rec - 0.04), P(gi[0], zb, -rec - 0.04)],
                        [(0, 0), (gi[1] - gi[0], 0), (gi[1] - gi[0], 0.2), (0, 0.2)], ACCENT, fr.n3)
            m = int((gi[1] - gi[0]) // 1.5)
            for k in range(1, m + 1):                       # vertical frame posts
                uu = gi[0] + k * (gi[1] - gi[0]) / (m + 1)
                fr.box(mb, uu - 0.04, uu + 0.04, gi[2], gi[3], 0.0, 0.04, ACCENT, faces="flr")
        return
    fr.front(mb, gi[0], gi[1], gi[2], gi[3], GLASSB, o=-rec,
             uv=[(0, 0), (gi[1] - gi[0], 0), (gi[1] - gi[0], gi[3] - gi[2]), (0, gi[3] - gi[2])])
    if lod == 0:
        pitch = PRM["strip_mullion_m"]
        n = max(1, int(round((gi[1] - gi[0]) / pitch)))
        for k in range(1, n):
            uu = gi[0] + k * (gi[1] - gi[0]) / n
            wide = k % 5 == 0                               # a stronger post every 6 m
            hw = 0.05 if wide else 0.022
            fr.front(mb, uu - hw, uu + hw, gi[2], gi[3], ACCENT if wide else "window_frame", o=-rec + 0.015)
        zm = (gi[2] + gi[3]) / 2
        fr.front(mb, gi[0], gi[1], zm - 0.02, zm + 0.02, "window_frame", o=-rec + 0.012)
        # sheet-metal sill under the strip
        fr.box(mb, u0 - 0.03, u1 + 0.03, z0 - 0.03, z0, 0.0, 0.09, FLASH, faces="flrtB")


def build_door(mb, e, fr, o, lod):
    u0, u1, z0, z1, _, d = o
    rec = 0.12 if lod == 0 else 0.0
    if lod == 0:
        fr.reveal(mb, u0, u1, z0, z1, rec, FLASH, sill=False)
    fr.front(mb, u0, u1, z0, z1, "door_steel", o=-rec)
    if lod > 0:
        return
    uc = (u0 + u1) / 2
    fr.box(mb, uc + 0.32, uc + 0.36, z0 + 0.95, z0 + 1.1, -rec, -rec + 0.06, "steel_galv", faces="flrtB")   # handle
    zg = ground_at(e, uc)
    if d.get("stairs"):
        # steel platform + stair flight parallel to the wall, descending away from the dock row, with a railing
        fr.box(mb, uc - 0.7, uc + 0.7, z0 - 0.06, z0, 0.0, 1.1, "steel_checker", faces="flrtB")
        nst = max(2, int(round((z0 - zg) / 0.18)))
        for k in range(nst):
            zs = z0 - (k + 1) * (z0 - zg) / nst
            ua = uc + 0.7 + k * 0.27
            fr.box(mb, ua, ua + 0.27, zs - 0.04, zs, 0.1, 1.1, "steel_checker", faces="flrtB")
        ue = uc + 0.7 + nst * 0.27
        P = fr.P
        for oo in (0.1, 1.1):                               # stringers
            mb.poly([P(uc + 0.7, z0 - 0.2, oo), P(ue, zg - 0.02, oo), P(ue, zg + 0.18, oo), P(uc + 0.7, z0, oo)],
                    [(0, 0), (1, 0), (1, 0.2), (0, 0.2)], "steel_galv", fr.n3 if oo > 0.5 else -fr.n3)
        for ua, za in ((uc - 0.68, z0), (uc + 0.68, z0), (ue - 0.05, zg + 0.1)):       # railing posts + top rail
            fr.box(mb, ua - 0.02, ua + 0.02, za, za + 1.1, 1.06, 1.1, "paint_yellow", faces="flrk")
        fr.box(mb, uc - 0.7, uc + 0.7, z0 + 1.06, z0 + 1.1, 1.06, 1.1, "paint_yellow", faces="ftkB")
        mb.poly([P(uc + 0.7, z0 + 1.06, 1.1), P(ue, zg + 1.16, 1.1), P(ue, zg + 1.2, 1.1), P(uc + 0.7, z0 + 1.1, 1.1)],
                [(0, 0), (1, 0), (1, 0.04), (0, 0.04)], "paint_yellow", fr.n3)
        for oo in (0.0,):
            fr.box(mb, uc - 0.7, uc - 0.66, z0 - 0.06 - (z0 - zg), z0 - 0.06, 1.0, 1.08, "steel_galv", faces="flrk")
            fr.box(mb, uc + 0.62, uc + 0.66, z0 - 0.06 - (z0 - zg), z0 - 0.06, 1.0, 1.08, "steel_galv", faces="flrk")
    else:
        fr.box(mb, u0 - 0.25, u1 + 0.25, zg - 0.3, z0, 0.0, 0.9, "concrete_base", faces="flrt")          # step slab
    if d.get("canopy"):
        fr.box(mb, u0 - 0.5, u1 + 0.5, z1 + 0.25, z1 + 0.33, 0.0, 1.3, "canopy_steel", faces="flrtB")
        for uu in (u0 - 0.45, u1 + 0.45):
            P = fr.P
            mb.poly([P(uu, z1 + 0.25, 1.25), P(uu, z1 + 0.9, 0.02), P(uu, z1 + 0.95, 0.02), P(uu, z1 + 0.3, 1.25)],
                    [(0, 0), (1, 0), (1, 0.05), (0, 0.05)], "steel_galv", fr.d3)
            mb.poly([P(uu, z1 + 0.25, 1.25), P(uu, z1 + 0.9, 0.02), P(uu, z1 + 0.95, 0.02), P(uu, z1 + 0.3, 1.25)],
                    [(0, 0), (1, 0), (1, 0.05), (0, 0.05)], "steel_galv", -fr.d3)
    # bulkhead light above the door
    fr.box(mb, uc - 0.14, uc + 0.14, z1 + 0.42, z1 + 0.52, 0.0, 0.1, "luminaire_housing", faces="flrtB")


def build_drive(mb, e, fr, o, lod):
    u0, u1, z0, z1, _, d = o
    W = u1 - u0
    if lod == 2:
        fr.front(mb, u0, u1, z0, z1, "dock_door", uv=[(0, 0), (W, 0), (W, z1 - z0), (0, z1 - z0)])
        return
    rec = 0.22 if lod == 0 else 0.0
    if lod == 0:
        fr.reveal(mb, u0, u1, z0, z1, rec, FLASH, sill=False)
    fr.front(mb, u0, u1, z0, z1, "dock_door", o=-rec, uv=[(0, 0), (W, 0), (W, z1 - z0), (0, z1 - z0)])
    if lod == 0:
        for uu in (u0 - 0.45, u1 + 0.45):                   # protection bollards
            fr.box(mb, uu - 0.08, uu + 0.08, z0 - 0.1, z0 + 1.0, 0.35, 0.51, "paint_yellow", faces="flrtk")
        fr.box(mb, u0 - 0.1, u1 + 0.1, z1, z1 + 0.1, 0.0, 0.06, FLASH, faces="flrtB")
        fr.box(mb, (u0 + u1) / 2 - 0.16, (u0 + u1) / 2 + 0.16, z1 + 0.5, z1 + 0.6, 0.0, 0.24, "luminaire_housing", faces="flrtB")


def build_window(mb, fr, o, lod):
    u0, u1, z0, z1, _, _ = o
    rec = 0.1 if lod == 0 else 0.0
    if lod == 0:
        fr.reveal(mb, u0, u1, z0, z1, rec, FLASH)
    fr.front(mb, u0, u1, z0, z1, "glass", o=-rec)
    if lod == 0:
        um = (u0 + u1) / 2
        for a, b, c, d in ((u0, u1, z0, z0 + 0.05), (u0, u1, z1 - 0.05, z1), (u0, u0 + 0.05, z0, z1), (u1 - 0.05, u1, z0, z1),
                           (um - 0.025, um + 0.025, z0, z1)):
            fr.front(mb, a, b, c, d, "window_frame", o=-rec + 0.012)
        fr.box(mb, u0 - 0.04, u1 + 0.04, z0 - 0.03, z0, 0.0, 0.07, FLASH, faces="flrtB")


def build_downpipe(mb, e, fr, u, lod):
    if lod == 2:
        return
    r = PRM["downpipe_d_m"] / 2
    zg = ground_at(e, u)
    zt = ZTOP - 0.25
    if lod == 0:
        fr.box(mb, u - 0.17, u + 0.17, zt, zt + 0.3, 0.0, 0.26, "downpipe", faces="flrtB")       # rainwater hopper
        fr.box(mb, u - r, u + r, zg + 0.25, zt, 0.04, 0.04 + 2 * r, "downpipe", faces="flr")
        for zb in np.arange(zg + 1.2, zt - 0.5, 2.6):                                           # brackets
            fr.box(mb, u - r - 0.02, u + r + 0.02, zb, zb + 0.04, 0.0, 0.04 + 2 * r + 0.01, "steel_galv", faces="flr")
        fr.box(mb, u - r - 0.015, u + r + 0.015, zg - 0.05, zg + 0.25, 0.03, 0.06 + 2 * r, "steel_painted_grey", faces="flrt")  # cast shoe
    else:
        fr.box(mb, u - r, u + r, zg, zt + 0.25, 0.0, 0.04 + 2 * r, "downpipe", faces="flr")


def build_annex(mb, ax, lod):
    q = [np.asarray(p, float) for p in ax["quad"]]            # p0 (on the wall), p1, p2 (front), p3 (on the wall)
    zg = ZREF
    h = ax["h_m"]
    style = ax["style"]
    mat = ACCENT if style in ("accent", "portal") else WALL
    walls = [Fr(q[0], q[1]), Fr(q[1], q[2]), Fr(q[2], q[3])]
    front = walls[1]
    if style == "portal" and lod < 2:
        pw = 1.0                                              # portal piers + lintel, glazed entrance set back
        zl = zg + h - 1.5
        for fr in (walls[0], walls[2]):
            fr.front(mb, 0, fr.L, ZBOT, zg + h, mat)
        front.front(mb, 0, pw, ZBOT, zg + h, mat)
        front.front(mb, front.L - pw, front.L, ZBOT, zg + h, mat)
        front.front(mb, pw, front.L - pw, zl, zg + h, mat)
        P = front.P
        dp = 0.9
        for uu, hn in ((pw, front.d3), (front.L - pw, -front.d3)):
            mb.poly([P(uu, zg, 0), P(uu, zg, -dp), P(uu, zl, -dp), P(uu, zl, 0)], [(0, 0), (dp, 0), (dp, zl - zg), (0, zl - zg)], mat, hn)
        mb.poly([P(pw, zl, 0), P(front.L - pw, zl, 0), P(front.L - pw, zl, -dp), P(pw, zl, -dp)],
                [(0, 0), (front.L - 2 * pw, 0), (front.L - 2 * pw, dp), (0, dp)], mat, (0, 0, -1))
        mb.poly([P(pw, zg + 0.16, 0.4), P(front.L - pw, zg + 0.16, 0.4), P(front.L - pw, zg + 0.16, -dp), P(pw, zg + 0.16, -dp)],
                [(0, 0), (front.L - 2 * pw, 0), (front.L - 2 * pw, dp + 0.4), (0, dp + 0.4)], "concrete_base", (0, 0, 1))
        front.front(mb, pw, front.L - pw, ZBOT, zg + 0.16, "concrete_base", o=0.4)
        # glazed screen: transom at 2.3 m, door pair in the middle
        front.front(mb, pw, front.L - pw, zg + 0.16, zl, "glass", o=-dp)
        if lod == 0:
            n = 4
            for k in range(n + 1):
                uu = pw + k * (front.L - 2 * pw) / n
                front.front(mb, uu - 0.03, uu + 0.03, zg + 0.16, zl, "window_frame", o=-dp + 0.015)
            for zz in (zg + 2.4, zg + 5.0):
                if zz < zl - 0.3:
                    front.front(mb, pw, front.L - pw, zz - 0.03, zz + 0.03, "window_frame", o=-dp + 0.012)
            um = front.L / 2
            front.front(mb, um - 0.95, um + 0.95, zg + 0.16, zg + 2.37, "door_glass", o=-dp + 0.02)
            front.front(mb, um - 0.02, um + 0.02, zg + 0.16, zg + 2.37, "window_frame", o=-dp + 0.03)
            front.box(mb, um - 1.6, um + 1.6, zg + 2.75, zg + 2.83, -dp, 0.55, "canopy_steel", faces="flrtB")
    else:
        for k, fr in enumerate(walls):
            zp = zg + PRM["plinth_h_m"]
            if lod < 2 and k == 1 and ax.get("door") and style != "portal":
                um = fr.L / 2
                dw = 0.9 if ax["door"] == "double" else 0.5
                z0 = zg + 0.12
                fr.front(mb, 0, um - dw, ZBOT, zp, PLINTH)
                fr.front(mb, um + dw, fr.L, ZBOT, zp, PLINTH)
                fr.front(mb, um - dw, um + dw, ZBOT, z0, PLINTH)
                fr.front(mb, 0, um - dw, zp, zg + h, mat)
                fr.front(mb, um + dw, fr.L, zp, zg + h, mat)
                fr.front(mb, um - dw, um + dw, z0 + 2.1, zg + h, mat)
                rec = 0.1 if lod == 0 else 0.0
                if lod == 0:
                    fr.reveal(mb, um - dw, um + dw, z0, z0 + 2.1, rec, FLASH, sill=False)
                    fr.box(mb, um - dw - 0.3, um + dw + 0.3, zg - 0.3, z0, 0.0, 0.8, "concrete_base", faces="flrt")
                    fr.box(mb, um - 0.14, um + 0.14, z0 + 2.3, z0 + 2.4, 0.0, 0.1, "luminaire_housing", faces="flrtB")
                    if ax["door"] == "double":
                        fr.front(mb, um - 0.015, um + 0.015, z0, z0 + 2.1, FLASH, o=-rec + 0.01)
                fr.front(mb, um - dw, um + dw, z0, z0 + 2.1, "door_steel", o=-rec)
            else:
                fr.front(mb, 0, fr.L, ZBOT, zp, PLINTH if style != "portal" else mat)
                fr.front(mb, 0, fr.L, zp, zg + h, mat)
    # roof + coping
    zr = zg + h
    roofm = ACCENT if style in ("accent", "portal") else "roof_membrane"
    mb.poly([(*q[0], zr), (*q[1], zr), (*q[2], zr), (*q[3], zr)], [(0, 0), (1, 0), (1, 1), (0, 1)], roofm, (0, 0, 1))
    if lod == 0 and style != "portal":
        for fr in walls:
            fr.box(mb, -0.03, fr.L + 0.03, zr - 0.02, zr + 0.08, -0.2, 0.04, FLASH, faces="fktB")
        # eaves gutter + downpipe on the front
        front.box(mb, 0.0, front.L, zr - 0.2, zr - 0.08, 0.04, 0.16, "gutter", faces="flrB")
        front.box(mb, 0.25, 0.35, zg + 0.1, zr - 0.2, 0.04, 0.14, "downpipe", faces="flr")


def build_segment(seg, lod):
    e = SPEC["edges"][seg["edge"]]
    ua, ub = seg["u"]
    u_off = sum(x["L"] for x in SPEC["edges"][:seg["edge"]])
    fr = Fr(e["a"], e["b"], u_off)
    annexes = [ax for ax in SPEC["annexes"] if ax["edge"] == e["i"]]
    ops = edge_openings(e, annexes, lod)
    mb = MB()
    seg_ops = [o for o in ops if ua - 1e-6 <= (o[0] + o[1]) / 2 < ub + 1e-6]
    # an opening belongs to the segment that holds its centre; the wall of both neighbours is cut to its edges
    build_wall(mb, e, fr, ua, ub, ops, lod)
    for o in ops:
        mid = (o[0] + o[1]) / 2
        if not (ua - 1e-6 <= mid < ub + 1e-6):
            # the part of a long opening (strip) that reaches into this segment is drawn here
            if o[4] in ("strip", "louvre", "band") and o[0] < ub and o[1] > ua:
                pass
            else:
                continue
        kind = o[4]
        if kind == "dock":
            build_dock(mb, fr, o, lod)
        elif kind in ("strip", "louvre"):          # long strips are clipped to the segment (a frame post at the cut)
            c0, c1 = max(o[0], ua), min(o[1], ub)
            if c1 - c0 > 0.05:
                build_strip(mb, fr, (c0, c1, o[2], o[3], kind, o[5]), lod, louvre=kind == "louvre")
        elif kind == "band":
            c0, c1 = max(o[0], ua), min(o[1], ub)
            if c1 - c0 > 0.05:
                fr.front(mb, c0, c1, o[2], o[3], "glass")
        elif kind == "door":
            build_door(mb, e, fr, o, lod)
        elif kind == "drive":
            build_drive(mb, e, fr, o, lod)
        elif kind == "window":
            build_window(mb, fr, o, lod)
    f = e["features"]
    for u in f.get("downpipes") or []:
        if ua <= u < ub or (u == e["L"] and ub == e["L"]):
            build_downpipe(mb, e, fr, min(max(u, 0.2), e["L"] - 0.2), lod)
    if lod == 0:
        for u in f.get("wall_lights") or []:
            if ua <= u < ub:
                z = ground_at(e, u) + 5.2
                fr.box(mb, u - 0.03, u + 0.03, z - 0.03, z + 0.03, 0.0, 0.45, "steel_galv", faces="lrtB")
                fr.box(mb, u - 0.2, u + 0.2, z - 0.1, z - 0.01, 0.35, 0.7, "luminaire_housing", faces="flrtk")
                P = fr.P
                mb.poly([P(u - 0.18, z - 0.102, 0.37), P(u + 0.18, z - 0.102, 0.37), P(u + 0.18, z - 0.102, 0.68),
                         P(u - 0.18, z - 0.102, 0.68)], [(0, 0), (1, 0), (1, 1), (0, 1)], "lamp_glass", (0, 0, -1))
        if "docks" in f:                                         # yellow corner bollards at both ends of the dock row
            dk = f["docks"]
            for u in (dk["first_u_m"] - 2.6, dk["first_u_m"] + (dk["count"] - 1) * dk["pitch_m"] + 2.6):
                if ua <= u < ub:
                    fr.box(mb, u - 0.09, u + 0.09, dk["yard_z"] - 0.1, dk["yard_z"] + 1.1, 0.5, 0.68, "paint_yellow", faces="flrtk")
    # coping (attic flashing) and the parapet inner face are part of the wall segment
    if lod < 2:
        fr.box(mb, ua, ub, ZPAR, ZPAR + PRM["coping_h_m"], -PRM["parapet_t_m"] - 0.03, 0.05, FLASH,
               faces="fktB" if lod == 0 else "fkt")
    else:
        fr.box(mb, ua, ub, ZPAR, ZPAR + PRM["coping_h_m"], -PRM["parapet_t_m"], 0.05, FLASH, faces="ft")
    if lod < 2:                                                  # parapet inner face (looks into the roof)
        t = PRM["parapet_t_m"]
        mb.poly([fr.P(ua, ZTOP, -t), fr.P(ub, ZTOP, -t), fr.P(ub, ZPAR, -t), fr.P(ua, ZPAR, -t)],
                [(0, 0), (ub - ua, 0), (ub - ua, ZPAR - ZTOP), (0, ZPAR - ZTOP)], FLASH, -fr.n3)
    for ax in annexes:
        um = (ax["u"][0] + ax["u"][1]) / 2
        if ua <= um < ub:
            build_annex(mb, ax, lod)
    return mb


def build_roof(lod):
    mb = MB()
    ring = [np.asarray(p, float) for p in SPEC["ring"]]
    holes = [[np.asarray(p, float) for p in h] for h in SPEC["holes"]]
    t = PRM["parapet_t_m"]
    import_ring = [Vector((p[0], p[1], 0)) for p in ring]
    hole_rings = [[Vector((p[0], p[1], 0)) for p in h] for h in holes]
    allp = ring + [p for h in holes for p in h]
    for tri in tessellate_polygon([import_ring] + hole_rings):
        P = [(allp[i][0], allp[i][1], ZTOP) for i in tri]
        mb.poly(P, [(p[0], p[1]) for p in P], "roof_membrane", (0, 0, 1))
    zc = ZREF + PRM["court_roof_h_m"]
    for h in holes:                                               # inner ring: lower light roof + its walls
        for tri in tessellate_polygon([[Vector((p[0], p[1], 0)) for p in h]]):
            P = [(h[i][0], h[i][1], zc) for i in tri]
            mb.poly(P, [(p[0], p[1]) for p in P], "kp_roof_white", (0, 0, 1))
        cen = np.mean(np.array(h), axis=0)
        n = len(h)
        for i in range(n):
            a, b = h[i], h[(i + 1) % n]
            L = float(np.linalg.norm(b - a))
            if L < 0.05:
                continue
            mid = (a + b) / 2
            mb.poly([(*a, zc), (*b, zc), (*b, ZTOP), (*a, ZTOP)], [(0, 0), (L, 0), (L, ZTOP - zc), (0, ZTOP - zc)], WALL,
                    np.append(cen - mid, 0.0))
    for p in SPEC["roof"]["patches"]:
        R = [np.asarray(q, float) for q in p["ring"]]
        mb.poly([(q[0], q[1], ZTOP + 0.03) for q in R], [(q[0], q[1]) for q in R], p["mat"], (0, 0, 1))
    if lod == 2:
        return mb
    from_poly = _Poly(ring, holes)
    sp = PRM["skylight_pitch_m"]
    sz = PRM["skylight_size_m"] / 2
    e0 = SPEC["edges"][0]
    ax = (np.asarray(e0["b"]) - np.asarray(e0["a"])) / e0["L"]
    ay = np.array([-ax[1], ax[0]])
    org = np.asarray(e0["a"], float)
    cnt = 0
    if SPEC["roof"]["skylights"] and lod == 0:
        ext = 400.0
        for i in range(int(ext / sp[0])):
            for j in range(int(ext / sp[1])):
                c = org + ax * (4.0 + i * sp[0] + (sp[0] / 2 if j % 2 else 0.0)) + ay * (5.0 + j * sp[1])
                if not from_poly.inside(c, 4.0):
                    continue
                if hf(ASSET, "sky", i, j) < 0.06 or any(_Poly._in(np.array(pp["ring"]), c) for pp in SPEC["roof"]["patches"]):
                    continue                               # a few fields without a roof light (as on the orthophoto)
                cs = [c + ax * sx * sz + ay * sy * sz for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
                z0, z1 = ZTOP, ZTOP + 0.35
                for k in range(4):
                    p, q = cs[k], cs[(k + 1) % 4]
                    mb.poly([(*p, z0), (*q, z0), (*q, z1), (*p, z1)], [(0, 0), (1, 0), (1, 0.3), (0, 0.3)], "roof_vent",
                            np.append((p + q) / 2 - c, 0.0))
                mb.poly([(*p, z1) for p in cs], [(0, 0), (1, 0), (1, 1), (0, 1)], "skylight", (0, 0, 1))
                cnt += 1
    # mushroom roof fans along the yard side (photo: fans above the parapet line)
    nv = SPEC["roof"]["vents"]
    for k in range(nv):
        c = org + ax * (20.0 + hf(ASSET, "vent", k, 0) * (e0["L"] - 40.0)) + ay * (9.0 + hf(ASSET, "vent", k, 1) * 100.0)
        if not from_poly.inside(c, 3.0):
            continue
        r = 0.45
        for a0, a1 in zip(np.linspace(0, 2 * math.pi, 7)[:-1], np.linspace(0, 2 * math.pi, 7)[1:]):
            p = c + r * 0.7 * np.array([math.cos(a0), math.sin(a0)])
            q = c + r * 0.7 * np.array([math.cos(a1), math.sin(a1)])
            mb.poly([(*p, ZTOP), (*q, ZTOP), (*q, ZTOP + 1.0), (*p, ZTOP + 1.0)], [(0, 0), (1, 0), (1, 1), (0, 1)], "roof_vent",
                    np.append((p + q) / 2 - c, 0.0))
            p2 = c + r * 1.4 * np.array([math.cos(a0), math.sin(a0)])
            q2 = c + r * 1.4 * np.array([math.cos(a1), math.sin(a1)])
            mb.poly([(*p2, ZTOP + 1.0), (*q2, ZTOP + 1.0), (c[0], c[1], ZTOP + 1.35)], [(0, 0), (1, 0), (0.5, 1)], "roof_vent",
                    (0, 0, 1))
            mb.poly([(*p2, ZTOP + 1.0), (*q2, ZTOP + 1.0), (c[0], c[1], ZTOP + 0.95)], [(0, 0), (1, 0), (0.5, 1)], "roof_vent",
                    (0, 0, -1))
    if lod == 0:
        build_roof.skylights = cnt
    return mb


class _Poly:
    def __init__(self, ring, holes):
        self.r = np.array(ring)
        self.h = [np.array(h) for h in holes]

    @staticmethod
    def _in(R, p):
        x, y = p
        c = False
        n = len(R)
        for i in range(n):
            x0, y0 = R[i]
            x1, y1 = R[(i + 1) % n]
            if (y0 > y) != (y1 > y) and x < (x1 - x0) * (y - y0) / (y1 - y0) + x0:
                c = not c
        return c

    @staticmethod
    def _dist(R, p):
        d = 1e9
        n = len(R)
        for i in range(n):
            a, b = R[i], R[(i + 1) % n]
            t = np.clip(np.dot(p - a, b - a) / max(np.dot(b - a, b - a), 1e-9), 0, 1)
            d = min(d, float(np.linalg.norm(a + t * (b - a) - p)))
        return d

    def inside(self, p, margin):
        if not self._in(self.r, p) or self._dist(self.r, p) < margin:
            return False
        for h in self.h:
            if self._in(h, p) or self._dist(h, p) < margin:
                return False
        return True


# ---------------------------------------------------------------------------------------------------- main
def main():
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    segs = []
    mats = set()
    for k, seg in enumerate(SPEC["segments"]):
        name = f"landmark_depot_{ASSET}_{k:02d}"
        tris = []
        for lod in range(3):
            mb = build_segment(seg, lod)
            mats |= set(mb.M)
            _, n = mb.to_object(name + ("" if lod == 0 else f".lod{lod}"), seg["anchor"])
            tris.append(n)
        e = SPEC["edges"][seg["edge"]]
        segs.append({"name": name, "anchor": seg["anchor"], "tris": tris, "facade": e["name"], "u": seg["u"]})
    name = f"landmark_depot_{ASSET}_roof"
    tris = []
    for lod in range(3):
        mb = build_roof(lod)
        mats |= set(mb.M)
        _, n = mb.to_object(name + ("" if lod == 0 else f".lod{lod}"), SPEC["roof"]["anchor"])
        tris.append(n)
    segs.append({"name": name, "anchor": SPEC["roof"]["anchor"], "tris": tris, "facade": "roof", "u": [0, 0]})
    unknown = sorted(m for m in mats if m not in WORLD_MATS)
    if unknown:
        raise SystemExit(f"materials not in streetscape.materials: {unknown}")
    OUT.mkdir(parents=True, exist_ok=True)
    glb = OUT / f"{ASSET}.glb"
    if "--render" in argv:
        render(Path(arg("--render")), segs)
        return
    bpy.ops.export_scene.gltf(filepath=str(glb), export_format="GLB", export_yup=True, export_apply=False,
                              export_texcoords=True, export_normals=True, export_materials="EXPORT",
                              export_image_format="NONE", export_tangents=False, export_animations=False,
                              export_cameras=False, export_lights=False, export_extras=False)
    if "--blend" in argv:
        bpy.ops.wm.save_as_mainfile(filepath=str(OUT / f"{ASSET}.blend"))
    meta = {
        "schema": "truck-sim-pl/hero-depot-asset/1", "asset": ASSET, "spec": SPEC_PATH.relative_to(REPO).as_posix(),
        "spec_sha256": sha(SPEC), "glb_sha256": hashlib.sha256(glb.read_bytes()).hexdigest(),
        "blender": bpy.app.version_string, "materials": sorted(mats), "segments": segs,
        "tris_total": [int(sum(s_["tris"][k] for s_ in segs)) for k in range(3)],
        "skylights": getattr(build_roof, "skylights", 0),
        "axes": "glTF (x, y, z) = (-dE, dU, dN) relative to the segment anchor (local E, N, U)",
    }
    (OUT / f"{ASSET}_meta.json").write_text(json.dumps(meta, indent=1, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print("DEPOT_RESULT: OK", glb, meta["tris_total"], len(segs), "segments")


def render(out, segs):
    """Control renders in world placement: EEVEE, sky + sun, flat yard plane. Cameras: start camera of route G3-A,
    the dock row, the CC0 reference photo position, the SW facade, a top view for the orthophoto montage."""
    out.mkdir(parents=True, exist_ok=True)
    sc = bpy.context.scene
    for sg in segs:
        for suf in ("", ".lod1", ".lod2"):
            a = sg["anchor"]
            bpy.data.objects[sg["name"] + suf].location = (-a[0], -a[1], a[2])
    dk_e = next(e for e in SPEC["edges"] if "docks" in e["features"])
    yz = dk_e["features"]["docks"]["yard_z"]
    cen = SPEC["roof"]["anchor"]
    bpy.ops.mesh.primitive_plane_add(size=1200, location=(-cen[0], -cen[1], yz))
    g = bpy.context.object
    gm = bpy.data.materials.new("ground")
    gm.use_nodes = True
    gm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.27, 0.265, 0.255, 1)
    gm.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.9
    g.data.materials.append(gm)
    w = bpy.data.worlds.new("w")
    sc.world = w
    w.use_nodes = True
    sky = w.node_tree.nodes.new("ShaderNodeTexSky")
    sky.sky_type = "NISHITA"
    sun_el, sun_az = float(arg("--sun-el", "38")), float(arg("--sun-az", "150"))     # azimuth from north, clockwise
    sky.sun_elevation = math.radians(sun_el)
    sky.sun_rotation = math.radians(sun_az + 180.0)
    w.node_tree.links.new(sky.outputs["Color"], w.node_tree.nodes["Background"].inputs["Color"])
    w.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.22
    # Blender scene axes are (-E, -N, U): a direction with azimuth az points to (-sin az, -cos az)
    sd = Vector((-math.sin(math.radians(sun_az)) * math.cos(math.radians(sun_el)),
                 -math.cos(math.radians(sun_az)) * math.cos(math.radians(sun_el)), math.sin(math.radians(sun_el))))
    bpy.ops.object.light_add(type="SUN")
    sun = bpy.context.object
    sun.rotation_euler = sd.to_track_quat("Z", "Y").to_euler()
    sun.data.energy = 3.2
    sun.data.angle = math.radians(1.0)
    sc.render.engine = "BLENDER_EEVEE_NEXT"
    sc.view_settings.view_transform = "AgX"
    sc.render.resolution_x, sc.render.resolution_y = 1600, 900
    sc.eevee.use_shadows = True
    try:
        sc.eevee.use_raytracing = True
        sc.eevee.use_gtao = True
    except Exception:      # noqa: BLE001
        pass
    a = np.asarray(dk_e["a"])
    d = (np.asarray(dk_e["b"]) - a) / dk_e["L"]
    n = np.array([d[1], -d[0]])
    dk = dk_e["features"]["docks"]
    um = dk["first_u_m"] + (dk["count"] - 1) * dk["pitch_m"] / 2

    def pt(u, o, z):
        q = a + d * u + n * o
        return (float(q[0]), float(q[1]), yz + z)
    cams = {
        "g3a_eye_s0012": ((720.978, -411.552, 143.882), (701.459, -446.48, 143.159), 60.0),
        "docks_front": (pt(um, 34.0, 2.5), pt(um, 0.0, 3.0), 60.0),
        "docks_34": (pt(um + 30.0, 16.0, 2.2), pt(um - 4.0, 0.0, 2.6), 55.0),
        "dock_close": (pt(dk["first_u_m"] + 2.0 * dk["pitch_m"] + 4.5, 7.5, 1.7), pt(dk["first_u_m"] + 2.5 * dk["pitch_m"], 0.0, 2.4), 55.0),
        # CC0 photo 20210904_101250 (Rakoon): crop 1150 x 420 px at (0, 930) of 3840 x 2160; camera station solved from
        # the louvre panel scale (about 95 m due south of the south corner), hfov of the crop about 22 deg
        "photo_cc0_20210904": ((612.9, -614.5, yz + 1.6), (615.7, -519.5, yz + 6.7), 12.5),
        "se_north": (pt(118.0, 42.0, 2.5), pt(96.0, 0.0, 5.0), 60.0),
        "sw_facade": ((560.0, -560.0, yz + 1.7), (520.0, -470.0, yz + 5.0), 60.0),
        "aerial": ((720.0, -560.0, yz + 70.0), (640.0, -430.0, yz + 5.0), 50.0),
    }
    lods = {"": "lod0", ".lod1": "lod1", ".lod2": "lod2"}
    only = arg("--cams")
    for suf, tag in lods.items():
        for sg in segs:
            for s2 in lods:
                bpy.data.objects[sg["name"] + s2].hide_render = s2 != suf
        for cid, (pos, look, fov) in cams.items():
            if tag != "lod0" and cid not in ("docks_front", "g3a_eye_s0012", "aerial"):
                continue
            if only and cid not in only.split(","):
                continue
            cd = bpy.data.cameras.new(cid)
            cd.sensor_fit = "HORIZONTAL"
            cd.angle = 2 * math.atan(math.tan(math.radians(fov) / 2) * 16 / 9)
            cd.clip_start = 0.3
            cd.clip_end = 3000
            co = bpy.data.objects.new(cid, cd)
            sc.collection.objects.link(co)
            p = Vector((-pos[0], -pos[1], pos[2]))
            l = Vector((-look[0], -look[1], look[2]))
            co.location = p
            co.rotation_euler = (l - p).to_track_quat("-Z", "Y").to_euler()
            sc.camera = co
            sc.render.filepath = str(out / f"{cid}__{tag}.png")
            bpy.ops.render.render(write_still=True)
    # top view (orthographic, north up) for the montage with the orthophoto
    if not only or "top" in only.split(","):
        for sg in segs:
            for s2 in lods:
                bpy.data.objects[sg["name"] + s2].hide_render = s2 != ""
        cd = bpy.data.cameras.new("top")
        cd.type = "ORTHO"
        cd.ortho_scale = 260.0
        cd.clip_end = 500
        co = bpy.data.objects.new("top", cd)
        sc.collection.objects.link(co)
        co.location = (-cen[0], -cen[1], yz + 200.0)
        co.rotation_euler = (0, 0, math.pi)                   # scene is rotated 180 deg about U: image up = north
        sc.camera = co
        sc.render.resolution_x, sc.render.resolution_y = 1300, 1300
        sc.render.filepath = str(out / "top__lod0.png")
        bpy.ops.render.render(write_still=True)
    print("DEPOT_RENDER: OK", out)


main()
