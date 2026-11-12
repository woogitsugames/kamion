"""Render the world control cameras of a region in Blender (visual QA renders; the game is URP, see README).

    blender -b --factory-startup -P tools/blender/world/render_control.py -- \
        --region bialystok-industrial-c --out <abs dir> [--cams id1,id2] [--res 1600x900]
        [--light overcast|lowsun|both] [--engine EEVEE|CYCLES] [--samples 64]

Imports the chunk GLBs listed in Data/Regions/<id>/generated/world_manifest.json (terrain LOD by distance,
road, bridge, markings, paved, buildings (LOD0 near / LOD1 far), furniture; never collision), the point
instances (instances_<ci>_<cj>.json: street props from art-source/world/props/street_props.glb, trees from
art-source/world/vegetation/trees*.glb with LOD0/LOD1/impostor by distance), replaces the engine material
placeholders by procedural weathered materials (same masks the engine shaders get: UV1 lane coordinate /
distance to the edge, terrain vertex colours), scatters grass/weed cards near the camera, and renders with
AgX under an overcast or a low-sun sky (Nishita). No bloom, no vignette, no chromatic aberration.
"""

import argparse
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Matrix, Vector

REPO = Path(__file__).resolve().parents[3]
VEG = REPO / "art-source" / "world" / "vegetation"
PROPS_GLB = REPO / "art-source" / "world" / "props" / "street_props.glb"


def args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--region", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--cams", default="")
    ap.add_argument("--res", default="1600x900")
    ap.add_argument("--engine", default="EEVEE")
    ap.add_argument("--samples", type=int, default=64)
    ap.add_argument("--light", default="overcast")
    ap.add_argument("--world-root", default="")
    ap.add_argument("--no-grass", action="store_true")
    ap.add_argument("--bld-lod1", action="store_true", help="LOD1 buildings at every distance (Low/Medium look)")
    ap.add_argument("--suffix", default="", help="appended to the output file names")
    ap.add_argument("--cams-file", default="", help="camera JSON (same schema) instead of generated/control_cameras.json")
    ap.add_argument("--props-glb", default="", help="street_props.glb of a non-default build (world-root/../props)")
    return ap.parse_args(argv)


# ============================================================================================ node helpers
class NB:
    """Tiny node-graph builder."""

    def __init__(self, mat):
        mat.use_nodes = True
        self.nt = mat.node_tree
        for n in list(self.nt.nodes):
            self.nt.nodes.remove(n)
        self.out = self.nt.nodes.new("ShaderNodeOutputMaterial")
        self.bsdf = self.nt.nodes.new("ShaderNodeBsdfPrincipled")
        self.link(self.bsdf.outputs["BSDF"], self.out.inputs["Surface"])
        self.tc = self.nt.nodes.new("ShaderNodeTexCoord")
        self.geo = self.nt.nodes.new("ShaderNodeNewGeometry")

    def link(self, a, b):
        self.nt.links.new(a, b)

    def node(self, kind, **inputs):
        n = self.nt.nodes.new(kind)
        for k, v in inputs.items():
            if hasattr(v, "is_output") or hasattr(v, "links"):
                self.link(v, n.inputs[k])
            else:
                n.inputs[k].default_value = v
        return n

    def math(self, op, a, b=None, clamp=False):
        n = self.nt.nodes.new("ShaderNodeMath")
        n.operation = op
        n.use_clamp = clamp
        for i, v in enumerate((a, b)):
            if v is None:
                continue
            if isinstance(v, (int, float)):
                n.inputs[i].default_value = v
            else:
                self.link(v, n.inputs[i])
        return n.outputs[0]

    def vmath(self, op, a, b=None):
        n = self.nt.nodes.new("ShaderNodeVectorMath")
        n.operation = op
        for i, v in enumerate((a, b)):
            if v is None:
                continue
            if isinstance(v, (tuple, list)):
                n.inputs[i].default_value = v
            else:
                self.link(v, n.inputs[i])
        return n.outputs["Vector"] if op not in ("LENGTH", "DOT_PRODUCT") else n.outputs["Value"]

    def uv(self, name):
        n = self.nt.nodes.new("ShaderNodeUVMap")
        n.uv_map = name
        return n.outputs["UV"]

    def sep(self, v):
        n = self.nt.nodes.new("ShaderNodeSeparateXYZ")
        self.link(v, n.inputs[0])
        return n.outputs["X"], n.outputs["Y"], n.outputs["Z"]

    def attr(self, name):
        n = self.nt.nodes.new("ShaderNodeAttribute")
        n.attribute_name = name
        return n

    def noise(self, vec, scale, detail=4.0, rough=0.55, dist=0.0):
        n = self.nt.nodes.new("ShaderNodeTexNoise")
        n.inputs["Scale"].default_value = scale
        n.inputs["Detail"].default_value = detail
        n.inputs["Roughness"].default_value = rough
        n.inputs["Distortion"].default_value = dist
        self.link(vec, n.inputs["Vector"])
        return n.outputs["Fac"]

    def voronoi(self, vec, scale, feature="F1", metric="EUCLIDEAN", rand=1.0):
        n = self.nt.nodes.new("ShaderNodeTexVoronoi")
        n.feature = feature
        n.distance = metric
        n.inputs["Scale"].default_value = scale
        n.inputs["Randomness"].default_value = rand
        self.link(vec, n.inputs["Vector"])
        return n

    def ramp(self, src, stops):
        r = self.nt.nodes.new("ShaderNodeValToRGB")
        cr = r.color_ramp
        cr.elements.remove(cr.elements[1])
        cr.elements[0].position, cr.elements[0].color = stops[0][0], (*stops[0][1], 1)
        for pos, col in stops[1:]:
            e = cr.elements.new(pos)
            e.color = (*col, 1)
        self.link(src, r.inputs["Fac"])
        return r.outputs["Color"]

    def mix(self, fac, a, b, blend="MIX"):
        n = self.nt.nodes.new("ShaderNodeMix")
        n.data_type = "RGBA"
        n.blend_type = blend
        for k, v in (("Factor", fac), ("A", a), ("B", b)):
            if isinstance(v, (int, float)):
                n.inputs[k].default_value = v
            elif isinstance(v, tuple):
                n.inputs[k].default_value = (*v, 1) if len(v) == 3 else v
            else:
                self.link(v, n.inputs[k])
        return n.outputs["Result"]

    def mixf(self, fac, a, b):
        n = self.nt.nodes.new("ShaderNodeMix")
        n.data_type = "FLOAT"
        for k, v in (("Factor", fac), ("A", a), ("B", b)):
            if isinstance(v, (int, float)):
                n.inputs[k].default_value = v
            else:
                self.link(v, n.inputs[k])
        return n.outputs["Result"]

    def bump(self, h, strength, dist=0.01, normal=None):
        b = self.node("ShaderNodeBump", Strength=strength, Distance=dist)
        self.link(h, b.inputs["Height"])
        if normal is not None:
            self.link(normal, b.inputs["Normal"])
        return b.outputs["Normal"]

    def finish(self, color, rough, normal=None, metal=None):
        self.link(color, self.bsdf.inputs["Base Color"]) if not isinstance(color, tuple) else \
            setattr(self.bsdf.inputs["Base Color"], "default_value", (*color, 1))
        if isinstance(rough, (int, float)):
            self.bsdf.inputs["Roughness"].default_value = rough
        else:
            self.link(rough, self.bsdf.inputs["Roughness"])
        if normal is not None:
            self.link(normal, self.bsdf.inputs["Normal"])
        if metal is not None:
            self.bsdf.inputs["Metallic"].default_value = metal

    def gauss(self, x, mu, sig):
        d = self.math("SUBTRACT", x, mu)
        q = self.math("DIVIDE", d, sig)
        q2 = self.math("MULTIPLY", q, q)
        return self.math("EXPONENT", self.math("MULTIPLY", q2, -1.0))

    def line_mask(self, coord, period, width):
        """1 near multiples of `period` (joints), width in the same units."""
        fr = self.math("FRACT", self.math("DIVIDE", coord, period))
        d = self.math("MINIMUM", fr, self.math("SUBTRACT", 1.0, fr))
        return self.math("LESS_THAN", self.math("MULTIPLY", d, period), width)


def new_mat(name):
    return bpy.data.materials.new(name)


def srgb(c):
    return tuple(((x / 255) ** 2.2) for x in c)


# ============================================================================================ materials
def crack_net(b, obj, scale, warp, width_m, seal_m, presence):
    """Meandering crack network: Voronoi cell edges in a domain-warped space (two octaves of warp), crack width
    modulated along the path, present only where a low-frequency mask is high. Returns (crack, seal) masks."""
    wv = b.nt.nodes.new("ShaderNodeTexNoise")
    wv.inputs["Scale"].default_value = scale * 2.2
    wv.inputs["Detail"].default_value = 3.0
    wv.inputs["Roughness"].default_value = 0.6
    b.link(obj, wv.inputs["Vector"])
    wcol = b.vmath("SUBTRACT", wv.outputs["Color"], (0.5, 0.5, 0.5))
    pw = b.vmath("ADD", obj, b.vmath("MULTIPLY", wcol, (warp, warp, 0.0)))
    cr = b.voronoi(pw, scale, feature="DISTANCE_TO_EDGE", rand=1.0)
    dist_m = b.math("DIVIDE", cr.outputs["Distance"], scale)                  # metres to the cell edge
    wmod = b.math("ADD", 0.45, b.math("MULTIPLY", b.noise(obj, scale * 9.0, 2.0), 1.1))
    pres = b.math("GREATER_THAN", b.noise(obj, scale * 0.8, 2.0, 0.5), presence)
    crack = b.math("MULTIPLY", b.math("LESS_THAN", dist_m, b.math("MULTIPLY", wmod, width_m)), pres)
    sealed = b.math("GREATER_THAN", b.noise(obj, scale * 0.5, 1.0), 0.45)       # sealing crews do whole stretches
    seal = b.math("MULTIPLY", b.math("MULTIPLY", b.math("LESS_THAN", dist_m, b.math("MULTIPLY", wmod, seal_m)), pres),
                  sealed)
    return crack, seal


def mat_asphalt(name, base=0.075, lanes=True, yard=False):
    m = new_mat(name)
    b = NB(m)
    obj = b.tc.outputs["Object"]
    big = b.noise(obj, 0.035, 3.0, 0.5)
    mid = b.noise(obj, 0.6, 5.0, 0.6)
    agg = b.noise(obj, 180.0, 2.0, 0.5)
    tone = b.ramp(b.mixf(0.4, big, mid), [(0.3, (base * 0.82,) * 3), (0.55, (base, base, base * 0.97)),
                                           (0.72, (base * 1.22, base * 1.21, base * 1.17))])
    col = tone
    # meandering crack network with 2-4 cm bitumen sealant bands (patches are geometry decals, not a grid)
    crack, seal = crack_net(b, obj, 0.16, 2.2, 0.006, 0.03, 0.52)
    # sealant ~half the asphalt albedo (dusty bitumen), open crack darker but not black (r2 #5: black polylines)
    col = b.mix(b.math("MULTIPLY", seal, 0.75), col, (base * 0.5, base * 0.5, base * 0.5))
    col = b.mix(b.math("MULTIPLY", crack, 0.8), col, (base * 0.33, base * 0.33, base * 0.33))
    rough = b.mixf(seal, 0.9, 0.8)         # bitumen sealant: a little smoother than the aggregate, not glossy (dusty)
    if lanes:
        uv1 = b.uv("UVMap.001")
        u, v, _ = b.sep(uv1)
        valid = b.math("GREATER_THAN", u, -0.5)
        fr = b.math("FRACT", u)
        wheel = b.math("ADD", b.gauss(fr, 0.27, 0.075), b.gauss(fr, 0.73, 0.075))
        wheel = b.math("MULTIPLY", wheel, valid)
        wheel = b.math("MULTIPLY", wheel, b.math("ADD", 0.6, b.math("MULTIPLY", mid, 0.6)))
        col = b.mix(b.math("MULTIPLY", wheel, 0.5), col, (base * 0.62, base * 0.62, base * 0.64))
        rough = b.mixf(b.math("MULTIPLY", wheel, 0.7), rough, 0.74)
        gut = b.math("SUBTRACT", 1.0, b.math("DIVIDE", v, 0.7), clamp=True)
        gut = b.math("MULTIPLY", gut, b.math("ADD", 0.5, mid))
        col = b.mix(b.math("MULTIPLY", gut, 0.7), col, (0.16, 0.14, 0.11))
        # longitudinal paving joint between lanes: an open, wandering crack, sealed on some stretches
        jn = b.math("MULTIPLY", b.math("SUBTRACT", b.noise(obj, 0.9, 2.0), 0.5), 0.05)
        dj = b.math("MINIMUM", b.math("FRACT", b.math("ADD", u, jn)), b.math("SUBTRACT", 1.0, b.math("FRACT", b.math("ADD", u, jn))))
        jw = b.math("ADD", 0.004, b.math("MULTIPLY", b.noise(obj, 3.0, 2.0), 0.01))
        seam = b.math("MULTIPLY", b.math("LESS_THAN", dj, jw), valid)
        seamseal = b.math("MULTIPLY", b.math("MULTIPLY", b.math("LESS_THAN", dj, 0.012), valid),
                          b.math("GREATER_THAN", b.noise(obj, 0.05, 1.0), 0.5))
        col = b.mix(b.math("MULTIPLY", seamseal, 0.8), col, (0.02, 0.02, 0.02))
        col = b.mix(b.math("MULTIPLY", seam, 0.7), col, (0.015, 0.015, 0.015))
        rut = b.math("MULTIPLY", wheel, -0.5)
        h = b.math("ADD", b.math("MULTIPLY", agg, 1.0), rut)
    else:
        h = agg
        if yard:
            tyre = b.math("GREATER_THAN", b.noise(b.vmath("MULTIPLY", obj, (0.15, 1.5, 1)), 2.0, 2.0), 0.62)
            col = b.mix(b.math("MULTIPLY", tyre, 0.35), col, (0.03, 0.03, 0.03))
    nrm = b.bump(h, 0.22, 0.004)
    nrm = b.bump(b.math("MULTIPLY", crack, -1.0), 0.12, 0.003, nrm)
    nrm = b.bump(seal, 0.05, 0.002, nrm)
    b.finish(col, rough, nrm)
    return m


def mat_decal_patch(name, base=0.075):
    """Repair patch decal: UV = metres in the patch, UV1.x = age (0 fresh black .. 1 old grey); dark cut edge."""
    m = new_mat(name)
    b = NB(m)
    obj = b.tc.outputs["Object"]
    u, v, _ = b.sep(b.uv("UVMap"))
    age, seed, _ = b.sep(b.uv("UVMap.001"))
    n = b.noise(obj, 1.5, 4.0, 0.6)
    fresh = (0.032, 0.032, 0.031)
    old = (base * 1.15, base * 1.14, base * 1.1)
    col = b.mix(age, fresh, old)
    col = b.mix(b.math("MULTIPLY", n, 0.3), col, (base * 0.7, base * 0.7, base * 0.7))
    agg = b.noise(obj, 160.0, 2.0)
    col = b.mix(b.math("MULTIPLY", b.math("GREATER_THAN", agg, 0.62), b.math("MULTIPLY", age, 0.4)), col,
                (base * 1.6, base * 1.55, base * 1.5))
    b.finish(col, b.mixf(age, 0.55, 0.88), b.bump(agg, 0.2, 0.003))
    return m


def mat_decal_oil(name):
    """Oil stain: radial alpha from the centre (UV 0.5, 0.5) broken by noise, darker and glossier core."""
    m = new_mat(name)
    b = NB(m)
    obj = b.tc.outputs["Object"]
    uvv = b.uv("UVMap")
    d = b.vmath("LENGTH", b.vmath("SUBTRACT", uvv, (0.5, 0.5, 0.0)))
    n = b.noise(obj, 4.0, 4.0, 0.7)
    a = b.math("SUBTRACT", 1.0, b.math("DIVIDE", b.math("ADD", d, b.math("MULTIPLY", n, 0.35)), 0.62), clamp=True)
    a = b.math("POWER", a, 0.7)
    b.finish((0.012, 0.011, 0.010), b.mixf(a, 0.85, 0.3))
    b.link(b.math("MULTIPLY", a, 0.75), b.bsdf.inputs["Alpha"])
    try:
        m.surface_render_method = "DITHERED"
    except AttributeError:
        pass
    return m


def mat_decal_tyre(name):
    """Tyre scrub on dock aprons: UV.x = m along the track, UV.y = 0..1 across, UV1 = (track length, seed).
    Soft edges across, fade-in near the bumpers and fade-out at the far end, streaky along the track (rubber
    smeared in the direction of travel), broken into dashes by noise; never fully opaque."""
    m = new_mat(name)
    b = NB(m)
    obj = b.tc.outputs["Object"]
    u, v, _ = b.sep(b.uv("UVMap"))
    L, seed, _ = b.sep(b.uv("UVMap.001"))
    across = b.math("SUBTRACT", 1.0, b.math("ABSOLUTE", b.math("MULTIPLY", b.math("SUBTRACT", v, 0.5), 2.0)))
    across = b.math("POWER", across, 0.6)
    fin = b.math("MINIMUM", b.math("DIVIDE", u, 2.5, clamp=True),
                 b.math("DIVIDE", b.math("SUBTRACT", L, u), b.math("MULTIPLY", L, 0.45), clamp=True))
    streak = b.noise(b.node("ShaderNodeCombineXYZ", X=b.math("MULTIPLY", u, 0.15), Y=b.math("MULTIPLY", v, 6.0),
                            Z=b.math("MULTIPLY", seed, 37.0)).outputs[0], 1.0, 3.0, 0.6)
    brk = b.noise(obj, 0.9, 2.0, 0.5)
    a = b.math("MULTIPLY", across, fin)
    a = b.math("MULTIPLY", a, b.math("SUBTRACT", b.math("MULTIPLY", streak, 1.6), 0.35, clamp=True))
    a = b.math("MULTIPLY", a, b.math("SUBTRACT", b.math("MULTIPLY", brk, 2.2), 0.55, clamp=True))
    a = b.math("MULTIPLY", a, b.mixf(seed, 0.35, 0.6))
    b.finish((0.015, 0.015, 0.014), 0.6)
    b.link(a, b.bsdf.inputs["Alpha"])
    try:
        m.surface_render_method = "DITHERED"
    except AttributeError:
        pass
    return m


def mat_markings(name):
    m = new_mat(name)
    b = NB(m)
    obj = b.tc.outputs["Object"]
    wear = b.noise(obj, 3.0, 6.0, 0.7)
    grain = b.noise(obj, 90.0, 2.0)
    w2 = b.mixf(0.35, wear, grain)
    col = b.ramp(w2, [(0.36, (0.07, 0.07, 0.068)), (0.50, (0.38, 0.38, 0.36)), (0.65, (0.52, 0.52, 0.50))])
    big = b.noise(obj, 0.08, 2.0)
    col = b.mix(b.math("MULTIPLY", big, 0.35), col, (0.16, 0.15, 0.13))
    b.finish(col, 0.6, b.bump(grain, 0.1, 0.002))
    return m


def mat_kerb(name, base=0.25):
    m = new_mat(name)
    b = NB(m)
    obj = b.tc.outputs["Object"]
    u, v, _ = b.sep(b.uv("UVMap"))
    n = b.noise(obj, 4.0, 6.0, 0.6)
    col = b.ramp(n, [(0.35, (base * 0.82, base * 0.82, base * 0.8)), (0.65, (base, base, base * 0.97))])
    seg = b.voronoi(b.vmath("MULTIPLY", b.uv("UVMap"), (1.0, 0.0, 0.0)), 1.0)    # per 1 m segment tone
    col = b.mix(b.math("MULTIPLY", seg.outputs["Color"], 0.25), col, (base * 0.75, base * 0.74, base * 0.70))
    joint = b.line_mask(u, 1.0, 0.006)
    col = b.mix(b.math("MULTIPLY", joint, 0.9), col, (0.05, 0.05, 0.05))
    dirt = b.math("MULTIPLY", b.noise(obj, 0.7, 3.0), 0.8)
    col = b.mix(b.math("MULTIPLY", dirt, 0.45), col, (0.12, 0.11, 0.09))
    nrm = b.bump(b.math("MULTIPLY", joint, -1.0), 0.6, 0.004)
    nrm = b.bump(b.noise(obj, 60.0, 2.0), 0.15, 0.002, nrm)
    b.finish(col, 0.88, nrm)
    return m


def mat_pavers(name, c1, c2, w=0.20, h=0.10, rot_uv=True, moss=True):
    m = new_mat(name)
    b = NB(m)
    vec = b.uv("UVMap") if rot_uv else b.tc.outputs["Object"]
    br = b.nt.nodes.new("ShaderNodeTexBrick")
    br.offset = 0.5
    br.inputs["Scale"].default_value = 1.0
    br.inputs["Brick Width"].default_value = w
    br.inputs["Row Height"].default_value = h
    br.inputs["Mortar Size"].default_value = 0.004
    br.inputs["Mortar Smooth"].default_value = 0.3
    br.inputs["Bias"].default_value = 0.0
    br.inputs["Color1"].default_value = (*c1, 1)
    br.inputs["Color2"].default_value = (*c2, 1)
    br.inputs["Mortar"].default_value = (c1[0] * 0.45, c1[1] * 0.45, c1[2] * 0.42, 1)
    b.link(vec, br.inputs["Vector"])
    obj = b.tc.outputs["Object"]
    dirt = b.noise(obj, 0.25, 4.0)
    col = b.mix(b.math("MULTIPLY", dirt, 0.45), br.outputs["Color"], (c1[0] * 0.6, c1[1] * 0.58, c1[2] * 0.52))
    stain = b.math("GREATER_THAN", b.noise(obj, 0.9, 3.0), 0.63)
    col = b.mix(b.math("MULTIPLY", stain, 0.5), col, (c1[0] * 0.5, c1[1] * 0.5, c1[2] * 0.5))
    if moss:     # yards: second-scale variation (batches) + wandering tyre tracks along the yard's long axis
        big = b.noise(obj, 0.05, 3.0, 0.5)
        col = b.mix(b.math("MULTIPLY", big, 0.4), col, (c1[0] * 0.75, c1[1] * 0.75, c1[2] * 0.72))
        uu, vv, _ = b.sep(b.uv("UVMap"))
        tr = b.noise(b.vmath("MULTIPLY", b.combine(uu, vv, 0.0), (0.08, 1.4, 1.0)), 1.0, 2.0, 0.5)
        track = b.math("MULTIPLY", b.math("GREATER_THAN", tr, 0.58), b.math("ADD", 0.3, b.noise(obj, 0.3, 2.0)))
        col = b.mix(b.math("MULTIPLY", track, 0.45), col, (c1[0] * 0.5, c1[1] * 0.5, c1[2] * 0.5))
    if moss:     # weeds/moss in joints near the edge of the paved area (UV1.x = distance to edge)
        e, wdist, _ = b.sep(b.uv("UVMap.001"))
        near = b.math("SUBTRACT", 1.0, b.math("DIVIDE", e, 0.6), clamp=True)
        near_wall = b.math("SUBTRACT", 1.0, b.math("DIVIDE", wdist, 1.0), clamp=True)
        jm = br.outputs["Fac"]                       # brick Fac = 1 in the joints
        moss_f = b.math("MULTIPLY", b.math("MULTIPLY", near, jm), b.math("GREATER_THAN", b.noise(obj, 3.0, 3.0), 0.45))
        col = b.mix(b.math("MULTIPLY", moss_f, 0.9), col, (0.05, 0.07, 0.025))
        col = b.mix(b.math("MULTIPLY", near_wall, 0.5), col, (0.10, 0.09, 0.07))
    nrm = b.bump(br.outputs["Fac"], 0.35, 0.004)
    b.finish(col, 0.86, nrm)
    return m


def mat_behaton(name, c1, c2, w=0.20, h=0.165, d=0.12, waist=0.2, mort=0.0035):
    """I-shaped interlocking blocks (behaton, 198 x 163 mm) in half-offset rows: per-block tone, darker tyre
    tracks along the yard's main direction (UV u = long axis), second-scale variation, settlement, weeds in the
    joints near the edges. Joint layout derived for the double-T block: wide ends protrude into the
    neighbouring rows where the neighbours' waists are."""
    m = new_mat(name)
    b = NB(m)
    obj = b.tc.outputs["Object"]
    u, v, _ = b.sep(b.uv("UVMap"))
    r = b.math("FLOOR", b.math("DIVIDE", v, h))
    fy = b.math("FRACT", b.math("DIVIDE", v, h))
    xu = b.math("ADD", b.math("DIVIDE", u, w), b.math("MULTIPLY", b.math("MODULO", r, 2.0), 0.5))
    fx = b.math("FRACT", xu)
    bi = b.math("FLOOR", xu)
    mw, mh = mort / w, mort / h
    jA = b.math("LESS_THAN", b.math("MINIMUM", fx, b.math("SUBTRACT", 1.0, fx)), mw)
    in_w = b.math("LESS_THAN", b.math("ABSOLUTE", b.math("SUBTRACT", fx, 0.5)), waist)
    dh = b.math("MINIMUM", b.math("ABSOLUTE", b.math("SUBTRACT", fy, d)), b.math("ABSOLUTE", b.math("SUBTRACT", fy, 1.0 - d)))
    jB = b.math("MULTIPLY", in_w, b.math("LESS_THAN", dh, mh))
    ends = b.math("MAXIMUM", b.math("LESS_THAN", fy, d), b.math("GREATER_THAN", fy, 1.0 - d))
    dv = b.math("MINIMUM", b.math("MINIMUM", b.math("ABSOLUTE", b.math("SUBTRACT", fx, 0.5 - waist)),
                                              b.math("ABSOLUTE", b.math("SUBTRACT", fx, 0.5 + waist))),
                b.math("ABSOLUTE", b.math("SUBTRACT", fx, 0.5)))
    jC = b.math("MULTIPLY", ends, b.math("LESS_THAN", dv, mw))
    joint = b.math("MAXIMUM", jA, b.math("MAXIMUM", jB, jC))
    # per-block tone (hash of the block cell; ends belong to the neighbours, ignored at this scale)
    cell = b.combine(bi, r, 0.0)
    wn = b.nt.nodes.new("ShaderNodeTexWhiteNoise")
    wn.noise_dimensions = "3D"
    b.link(cell, wn.inputs["Vector"])
    col = b.mix(wn.outputs["Value"], c1, c2)
    big = b.noise(obj, 0.05, 3.0, 0.5)                        # second-scale variation (batches, wear)
    col = b.mix(b.math("MULTIPLY", big, 0.45), col, tuple(x * 0.72 for x in c1))
    # tyre tracks: bands along u, wandering
    tr = b.noise(b.vmath("MULTIPLY", b.combine(u, v, 0.0), (0.08, 1.4, 1.0)), 1.0, 2.0, 0.5)
    track = b.math("MULTIPLY", b.math("GREATER_THAN", tr, 0.56), b.math("ADD", 0.4, b.noise(obj, 0.3, 2.0)))
    col = b.mix(b.math("MULTIPLY", track, 0.55), col, tuple(x * 0.42 for x in c1))
    stain = b.math("GREATER_THAN", b.noise(obj, 0.7, 3.0), 0.66)
    col = b.mix(b.math("MULTIPLY", stain, 0.45), col, tuple(x * 0.5 for x in c1))
    col = b.mix(b.math("MULTIPLY", joint, 0.85), col, tuple(x * 0.4 for x in c1))
    e, wdist, _ = b.sep(b.uv("UVMap.001"))
    near = b.math("SUBTRACT", 1.0, b.math("DIVIDE", e, 0.8), clamp=True)
    weeds = b.math("MULTIPLY", b.math("MULTIPLY", near, joint), b.math("GREATER_THAN", b.noise(obj, 2.5, 3.0), 0.42))
    col = b.mix(b.math("MULTIPLY", weeds, 0.9), col, (0.05, 0.07, 0.025))
    near_wall = b.math("SUBTRACT", 1.0, b.math("DIVIDE", wdist, 1.0), clamp=True)
    col = b.mix(b.math("MULTIPLY", near_wall, 0.5), col, (0.10, 0.09, 0.07))
    settle = b.noise(obj, 0.25, 2.0)
    nrm = b.bump(b.math("MULTIPLY", joint, -1.0), 0.35, 0.004)
    nrm = b.bump(settle, 0.25, 0.02, nrm)
    b.finish(col, b.mixf(track, 0.86, 0.75), nrm)
    return m


def mat_planks(name, col, period=0.14, rough=0.85):
    """Horizontal weatherboarding (UV v = metres above ground): board joints, per-board tone, grey weathering."""
    m = new_mat(name)
    b = NB(m)
    obj = b.tc.outputs["Object"]
    u, v, _ = b.sep(b.uv("UVMap"))
    row = b.math("FLOOR", b.math("DIVIDE", v, period))
    fr = b.math("FRACT", b.math("DIVIDE", v, period))
    wn = b.nt.nodes.new("ShaderNodeTexWhiteNoise")
    wn.noise_dimensions = "1D"
    b.link(row, wn.inputs["W"])
    base = b.mix(b.math("MULTIPLY", wn.outputs["Value"], 0.35), col, tuple(c * 0.75 for c in col))
    grain = b.noise(b.vmath("MULTIPLY", obj, (0.3, 0.3, 8.0)), 6.0, 3.0)
    base = b.mix(b.math("MULTIPLY", grain, 0.25), base, tuple(c * 0.8 for c in col))
    weather = b.math("MULTIPLY", b.noise(obj, 0.8, 3.0), 0.45)
    base = b.mix(weather, base, (0.20, 0.19, 0.17))
    j = b.math("LESS_THAN", fr, 0.08)
    base = b.mix(b.math("MULTIPLY", j, 0.8), base, tuple(c * 0.3 for c in col))
    splash = b.math("SUBTRACT", 1.0, b.math("DIVIDE", b.math("SUBTRACT", v, 0.3), 0.6), clamp=True)
    base = b.mix(b.math("MULTIPLY", splash, 0.5), base, (0.10, 0.09, 0.07))
    b.finish(base, rough, b.bump(b.math("SUBTRACT", fr, j), 0.4, 0.01))
    return m


def mat_large_panel(name, col):
    """Wielka płyta: precast panels with sealed joints (3.0 m x 2.8 m storey grid from 0.3 m), grey streaks
    under every joint, slightly different panel tones."""
    m = new_mat(name)
    b = NB(m)
    obj = b.tc.outputs["Object"]
    u, v, _ = b.sep(b.uv("UVMap"))
    vv = b.math("SUBTRACT", v, 0.3)
    jh = b.line_mask(vv, 2.8, 0.018)
    jv = b.line_mask(u, 3.0, 0.018)
    joint = b.math("MAXIMUM", jh, jv)
    cell = b.combine(b.math("FLOOR", b.math("DIVIDE", u, 3.0)), b.math("FLOOR", b.math("DIVIDE", vv, 2.8)), 0.0)
    wn = b.nt.nodes.new("ShaderNodeTexWhiteNoise")
    wn.noise_dimensions = "3D"
    b.link(cell, wn.inputs["Vector"])
    base = b.mix(b.math("MULTIPLY", wn.outputs["Value"], 0.3), col, tuple(c * 0.82 for c in col))
    agg = b.noise(obj, 30.0, 2.0)
    base = b.mix(b.math("MULTIPLY", agg, 0.2), base, tuple(c * 1.15 for c in col))
    fr = b.math("FRACT", b.math("DIVIDE", vv, 2.8))
    streak = b.math("MULTIPLY", b.math("SUBTRACT", 1.0, fr), b.math("GREATER_THAN", b.noise(
        b.vmath("MULTIPLY", obj, (4.0, 4.0, 0.2)), 1.0, 3.0), 0.55))
    base = b.mix(b.math("MULTIPLY", streak, 0.35), base, tuple(c * 0.55 for c in col))
    base = b.mix(b.math("MULTIPLY", joint, 0.85), base, (0.06, 0.06, 0.06))
    b.finish(base, 0.9, b.bump(b.math("MULTIPLY", joint, -1.0), 0.5, 0.01))
    return m


def mat_pallet(name, col):
    """EUR pallet sides (UV metres): boards 22 mm top/bottom, 78 mm blocks at 0 / 0.55 / 1.1 m, dark gaps."""
    m = new_mat(name)
    b = NB(m)
    obj = b.tc.outputs["Object"]
    u, v, _ = b.sep(b.uv("UVMap"))
    fv = b.math("FRACT", b.math("DIVIDE", v, 0.144))
    gapz = b.math("MULTIPLY", b.math("GREATER_THAN", fv, 0.16), b.math("LESS_THAN", fv, 0.84))
    fu = b.math("FRACT", b.math("DIVIDE", b.math("ADD", u, 0.05), 0.55))
    block = b.math("LESS_THAN", fu, 0.2)
    gap = b.math("MULTIPLY", gapz, b.math("SUBTRACT", 1.0, block))
    base = b.mix(b.math("MULTIPLY", b.noise(obj, 6.0, 3.0), 0.35), col, tuple(c * 0.7 for c in col))
    grey = b.math("MULTIPLY", b.noise(obj, 1.3, 2.0), 0.6)
    base = b.mix(grey, base, (0.22, 0.20, 0.17))
    base = b.mix(gap, base, (0.015, 0.012, 0.01))
    b.finish(base, 0.9, b.bump(b.math("MULTIPLY", gap, -1.0), 0.4, 0.01))
    return m


def mat_curtain(name, col):
    """Curtainsider: vertical folds (UV u = metres along the trailer), road grime toward the bottom, faded top."""
    m = new_mat(name)
    b = NB(m)
    obj = b.tc.outputs["Object"]
    u, v, _ = b.sep(b.uv("UVMap"))
    fold = b.math("SINE", b.math("MULTIPLY", u, 2 * math.pi / 0.31))
    sag = b.noise(b.vmath("MULTIPLY", obj, (1.0, 1.0, 0.3)), 0.8, 2.0)
    base = b.mix(b.math("MULTIPLY", b.noise(obj, 0.6, 3.0), 0.2), col, tuple(c * 0.8 for c in col))
    grime = b.math("SUBTRACT", 1.0, b.math("DIVIDE", v, 1.2), clamp=True)
    base = b.mix(b.math("MULTIPLY", grime, 0.45), base, (0.10, 0.09, 0.08))
    b.finish(base, 0.72, b.bump(b.math("ADD", b.math("MULTIPLY", fold, 0.5), sag), 0.25, 0.02))
    return m


def mat_boom(name):
    """Boom barrier: 0.5 m red / white bands along the tube (UV v = metres along the boom)."""
    m = new_mat(name)
    b = NB(m)
    u, v, _ = b.sep(b.uv("UVMap"))
    band = b.math("LESS_THAN", b.math("FRACT", b.math("DIVIDE", v, 1.0)), 0.5)
    col = b.mix(band, srgb((228, 228, 222)), srgb((182, 28, 30)))
    b.finish(col, 0.45)
    return m


def mat_concrete_struct(name, base=0.30):
    """Structural concrete (decks, piers, abutments): low-contrast cloudy tone, faint vertical rain streaks and
    a darker weathered band at the bottom of vertical faces. No oil, tyre marks or joints (those are yard
    features; reusing the yard material put oil blotches on the Andersa deck beams)."""
    m = new_mat(name)
    b = NB(m)
    obj = b.tc.outputs["Object"]
    n = b.noise(obj, 0.4, 4.0, 0.55)
    col = b.ramp(n, [(0.35, (base * 0.9, base * 0.9, base * 0.88)), (0.65, (base * 1.04, base * 1.03, base))])
    streak = b.noise(b.vmath("MULTIPLY", obj, (3.0, 3.0, 0.15)), 1.0, 3.0, 0.6)
    col = b.mix(b.math("MULTIPLY", b.math("GREATER_THAN", streak, 0.6), 0.25), col,
                (base * 0.7, base * 0.7, base * 0.68))
    nrm = b.bump(b.noise(obj, 60.0, 2.0), 0.1, 0.002)
    b.finish(col, 0.88, nrm)
    return m


def mat_concrete_yard(name, base=0.27, jx=5.0, jy=5.0, slabs=False):
    m = new_mat(name)
    b = NB(m)
    obj = b.tc.outputs["Object"]
    u, v, _ = b.sep(b.uv("UVMap"))
    n = b.noise(obj, 0.5, 5.0, 0.6)
    col = b.ramp(n, [(0.3, (base * 0.8, base * 0.8, base * 0.78)), (0.7, (base * 1.05, base * 1.04, base))])
    if slabs:
        cell = b.voronoi(b.vmath("MULTIPLY", b.combine(b.math("FLOOR", b.math("DIVIDE", u, jx)),
                                                       b.math("FLOOR", b.math("DIVIDE", v, jy))), (1.0, 1.0, 1.0)), 1.0)
        col = b.mix(b.math("MULTIPLY", cell.outputs["Color"], 0.35), col, (base * 0.75, base * 0.74, base * 0.7))
    jt = b.math("MAXIMUM", b.line_mask(u, jx, 0.008 if not slabs else 0.02), b.line_mask(v, jy, 0.008 if not slabs else 0.02))
    col = b.mix(b.math("MULTIPLY", jt, 0.9), col, (0.03, 0.03, 0.03))
    oil = b.math("GREATER_THAN", b.noise(obj, 0.35, 4.0, 0.7), 0.64)
    col = b.mix(b.math("MULTIPLY", oil, 0.55), col, (base * 0.35, base * 0.34, base * 0.33))
    tyre = b.math("GREATER_THAN", b.noise(b.vmath("MULTIPLY", obj, (0.1, 1.2, 1)), 2.0, 2.0), 0.64)
    col = b.mix(b.math("MULTIPLY", tyre, 0.3), col, (0.05, 0.05, 0.05))
    e, wdist, _ = b.sep(b.uv("UVMap.001"))
    near_wall = b.math("SUBTRACT", 1.0, b.math("DIVIDE", wdist, 1.5), clamp=True)
    col = b.mix(b.math("MULTIPLY", near_wall, 0.5), col, (0.12, 0.11, 0.09))
    nrm = b.bump(b.math("MULTIPLY", jt, -1.0), 0.5, 0.005)
    nrm = b.bump(b.noise(obj, 70.0, 2.0), 0.12, 0.002, nrm)
    b.finish(col, 0.86, nrm)
    return m


def _combine(self, x, y, z=0.0):
    n = self.nt.nodes.new("ShaderNodeCombineXYZ")
    for i, val in enumerate((x, y, z)):
        if isinstance(val, (int, float)):
            n.inputs[i].default_value = val
        else:
            self.link(val, n.inputs[i])
    return n.outputs[0]


NB.combine = _combine


def mat_gravel(name):
    m = new_mat(name)
    b = NB(m)
    obj = b.tc.outputs["Object"]
    n = b.noise(obj, 1.5, 6.0, 0.7)
    col = b.ramp(n, [(0.3, (0.12, 0.11, 0.09)), (0.55, (0.20, 0.18, 0.15)), (0.75, (0.26, 0.24, 0.20))])
    vv = b.voronoi(obj, 60.0)
    col = b.mix(b.math("MULTIPLY", vv.outputs["Distance"], 0.5), col, (0.08, 0.075, 0.07))
    b.finish(col, 0.95, b.bump(vv.outputs["Distance"], 0.4, 0.01))
    return m


def mat_terrain(name):
    m = new_mat(name)
    b = NB(m)
    obj = b.tc.outputs["Object"]
    a = b.attr("Color")
    sepc = b.nt.nodes.new("ShaderNodeSeparateColor")
    b.link(a.outputs["Color"], sepc.inputs[0])
    R, G, B = sepc.outputs[0], sepc.outputs[1], sepc.outputs[2]
    A = a.outputs["Alpha"]
    big = b.noise(obj, 0.04, 4.0, 0.6)
    mid = b.noise(obj, 0.5, 5.0, 0.6)
    fine = b.noise(obj, 6.0, 3.0, 0.6)
    mown = b.ramp(b.mixf(0.5, big, mid), [(0.3, srgb((52, 70, 32))), (0.55, srgb((66, 84, 38))), (0.75, srgb((84, 94, 48)))])
    rough_g = b.ramp(b.mixf(0.5, big, mid), [(0.25, srgb((60, 72, 36))), (0.45, srgb((86, 92, 52))),
                                             (0.62, srgb((112, 106, 70))), (0.8, srgb((74, 82, 44)))])
    forest = b.ramp(b.mixf(0.5, mid, fine), [(0.3, srgb((64, 56, 40))), (0.5, srgb((78, 72, 50))), (0.65, srgb((66, 76, 42))),
                                            (0.8, srgb((84, 90, 52)))])
    bare = b.ramp(mid, [(0.3, srgb((104, 96, 80))), (0.7, srgb((132, 122, 100)))])
    col = b.mix(B, mown, rough_g)
    col = b.mix(b.math("MULTIPLY", A, b.math("ADD", 0.4, b.math("MULTIPLY", fine, 0.8))), col, bare)
    col = b.mix(G, col, forest)
    # dirt/sand strip at the road edge (0-0.8 m) and dry tufts
    edge = b.math("SUBTRACT", 1.0, b.math("DIVIDE", R, 0.045), clamp=True)
    edge = b.math("MULTIPLY", edge, b.math("ADD", 0.3, fine))
    col = b.mix(b.math("MINIMUM", edge, 0.85), col, srgb((112, 102, 84)))
    nrm = b.bump(fine, 0.5, 0.03)
    b.finish(col, 0.95, nrm)
    return m


def mat_hall(name, col, ribs="h"):
    m = new_mat(name)
    b = NB(m)
    obj = b.tc.outputs["Object"]
    u, v, _ = b.sep(b.uv("UVMap"))
    if ribs == "h":        # horizontal panels 1.0 m with micro ribs every 0.1 m
        j = b.line_mask(v, 1.0, 0.01)
        micro = b.math("SINE", b.math("MULTIPLY", v, 2 * math.pi / 0.1))
        h = b.math("ADD", b.math("MULTIPLY", micro, 0.15), b.math("MULTIPLY", j, -1.0))
    else:                  # vertical trapezoid ribs every 0.25 m, panel joints 1.0 m
        fr = b.math("FRACT", b.math("DIVIDE", u, 0.25))
        rib = b.math("LESS_THAN", fr, 0.22)
        j = b.line_mask(u, 1.0, 0.008)
        h = b.math("SUBTRACT", rib, j)
    base = b.mix(b.math("MULTIPLY", b.noise(obj, 0.3, 3.0), 0.15), col, tuple(c * 0.85 for c in col))
    streak = b.noise(b.vmath("MULTIPLY", obj, (6.0, 6.0, 0.15)), 1.0, 3.0, 0.6)
    b.math("SUBTRACT", 1.0, b.math("DIVIDE", b.math("ABSOLUTE", b.math("SUBTRACT", v, 12.0)), 30.0), clamp=True)
    base = b.mix(b.math("MULTIPLY", b.math("GREATER_THAN", streak, 0.58), 0.25), base, tuple(c * 0.6 for c in col))
    splash = b.math("SUBTRACT", 1.0, b.math("DIVIDE", b.math("SUBTRACT", v, 0.5), 0.8), clamp=True)
    base = b.mix(b.math("MULTIPLY", splash, 0.55), base, (0.12, 0.11, 0.09))
    base = b.mix(b.math("MULTIPLY", j, 0.6), base, tuple(c * 0.4 for c in col))
    b.finish(base, 0.48, b.bump(h, 0.25, 0.01), metal=0.25)
    return m


def mat_plaster(name, col):
    m = new_mat(name)
    b = NB(m)
    obj = b.tc.outputs["Object"]
    u, v, _ = b.sep(b.uv("UVMap"))
    n = b.noise(obj, 1.2, 5.0, 0.6)
    base = b.mix(b.math("MULTIPLY", n, 0.25), col, tuple(c * 0.8 for c in col))
    streak = b.noise(b.vmath("MULTIPLY", obj, (5.0, 5.0, 0.2)), 1.0, 3.0)
    base = b.mix(b.math("MULTIPLY", b.math("GREATER_THAN", streak, 0.6), 0.25), base, tuple(c * 0.6 for c in col))
    splash = b.math("SUBTRACT", 1.0, b.math("DIVIDE", b.math("SUBTRACT", v, 0.3), 0.7), clamp=True)
    base = b.mix(b.math("MULTIPLY", splash, 0.5), base, (0.12, 0.11, 0.09))
    b.finish(base, 0.9, b.bump(b.noise(obj, 40.0, 3.0), 0.15, 0.003))
    return m


def mat_lines_v(name, col, period, width=0.01, rough=0.5, metal=0.3, horizontal=True, dirt_h=0.6, dirt_k=0.4):
    """Panels with grooves (sectional doors, noise-barrier cassettes, concrete fence panels); dirt from the
    bottom edge up to dirt_h (m of UV v), streaked vertically by noise (dock doors: road spray, rubber)."""
    m = new_mat(name)
    b = NB(m)
    obj = b.tc.outputs["Object"]
    u, v, _ = b.sep(b.uv("UVMap"))
    j = b.line_mask(v if horizontal else u, period, width)
    base = b.mix(b.math("MULTIPLY", b.noise(obj, 0.8, 4.0), 0.2), col, tuple(c * 0.8 for c in col))
    base = b.mix(b.math("MULTIPLY", j, 0.7), base, tuple(c * 0.35 for c in col))
    dirt = b.math("SUBTRACT", 1.0, b.math("DIVIDE", v, dirt_h), clamp=True)
    streak = b.noise(b.node("ShaderNodeCombineXYZ", X=b.math("MULTIPLY", u, 6.0), Y=b.math("MULTIPLY", v, 0.4)).outputs[0],
                     1.0, 3.0, 0.6)
    dirt = b.math("MULTIPLY", dirt, b.math("ADD", 0.55, b.math("MULTIPLY", streak, 0.9)), clamp=True)
    base = b.mix(b.math("MULTIPLY", dirt, dirt_k), base, (0.1, 0.09, 0.07))
    b.finish(base, rough, b.bump(b.math("MULTIPLY", j, -1.0), 0.4, 0.01), metal=metal)
    return m


def mat_hazard(name):
    m = new_mat(name)
    b = NB(m)
    u, v, _ = b.sep(b.uv("UVMap"))
    s = b.math("FRACT", b.math("DIVIDE", b.math("ADD", u, v), 0.2))
    st = b.math("LESS_THAN", s, 0.5)
    col = b.mix(st, srgb((25, 25, 25)), srgb((215, 165, 20)))
    b.finish(col, 0.55)
    return m


def mat_flat(name, col, rough=0.85, metal=0.0, noise=0.12):
    m = new_mat(name)
    b = NB(m)
    obj = b.tc.outputs["Object"]
    base = b.mix(b.math("MULTIPLY", b.noise(obj, 2.0, 4.0), noise), col, tuple(c * 0.7 for c in col))
    b.finish(base, rough, metal=metal)
    return m


def mat_glass(name, tint=(0.02, 0.025, 0.03)):
    m = new_mat(name)
    b = NB(m)
    b.finish(tint, 0.06, metal=0.0)
    b.bsdf.inputs["Specular IOR Level"].default_value = 0.8
    return m


def mat_screen_glass(name):
    """Transparent noise-screen panels (PMMA / glass): mostly see-through, faint grey tint, sky reflection."""
    m = new_mat(name)
    b = NB(m)
    b.finish((0.6, 0.64, 0.64), 0.08)
    b.bsdf.inputs["Alpha"].default_value = 0.18
    try:
        m.surface_render_method = "DITHERED"
    except AttributeError:
        pass
    m.use_backface_culling = False
    return m


def mat_emit(name, col, strength=1.0):
    m = new_mat(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*col, 1)
    em.inputs["Strength"].default_value = strength
    nt.links.new(em.outputs["Emission"], out.inputs["Surface"])
    return m


def mat_far_facade(name, col, grid, base_mat=None):
    """LOD1 far facade (v3.1, buildings_mesh.lod1_wall): wall colour + window grid from UV1 (one unit = one bay x
    one storey): glass panes with a light frame, per-window tone variation (curtains / reflections) from a hash
    of the cell, so far blocks are not boxes and not a repeated texture."""
    m = new_mat(name)
    b = NB(m)
    obj = b.tc.outputs["Object"]
    u, v, _ = b.sep(b.uv("UVMap.001"))
    fu, fv = b.math("FRACT", u), b.math("FRACT", v)
    hw = grid["win_w"] / 2
    inx = b.math("LESS_THAN", b.math("ABSOLUTE", b.math("SUBTRACT", fu, 0.5)), hw + 1e-4)
    iny = b.math("MULTIPLY", b.math("GREATER_THAN", fv, grid["sill"]), b.math("LESS_THAN", fv, grid["head"]))
    win = b.math("MULTIPLY", inx, iny)
    frx = b.math("LESS_THAN", b.math("ABSOLUTE", b.math("SUBTRACT", fu, 0.5)), hw - 0.025)
    fry = b.math("MULTIPLY", b.math("GREATER_THAN", fv, grid["sill"] + 0.03), b.math("LESS_THAN", fv, grid["head"] - 0.03))
    pane = b.math("MULTIPLY", frx, fry)
    cell = b.combine(b.math("FLOOR", u), b.math("FLOOR", v), 0.0)
    wn = b.nt.nodes.new("ShaderNodeTexWhiteNoise")
    wn.noise_dimensions = "3D"
    b.link(cell, wn.inputs["Vector"])
    tone = b.ramp(wn.outputs["Value"], [(0.0, (0.020, 0.024, 0.028)), (0.7, (0.045, 0.050, 0.055)),
                                         (0.92, (0.20, 0.19, 0.17)), (1.0, (0.33, 0.31, 0.27))])
    wall = b.mix(b.math("MULTIPLY", b.noise(obj, 0.4, 3.0), 0.18), col, tuple(c * 0.82 for c in col))
    streak = b.noise(b.vmath("MULTIPLY", obj, (5.0, 5.0, 0.2)), 1.0, 3.0)
    wall = b.mix(b.math("MULTIPLY", b.math("GREATER_THAN", streak, 0.6), 0.2), wall, tuple(c * 0.65 for c in col))
    frame = b.mix(win, wall, (0.55, 0.55, 0.53))
    b.finish(b.mix(pane, frame, tone), 0.85)
    return m


def mat_forest(name):
    """Forest HLOD (v3.1): baked edge / canopy textures (make_trees.py) as base colour; the edge is alpha-tested."""
    m = new_mat(name)
    b = NB(m)
    tex = b.nt.nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(str(VEG / f"{name}.png"))
    tex.interpolation = "Cubic"
    b.link(b.uv("UVMap"), tex.inputs["Vector"])
    b.bsdf.inputs["Roughness"].default_value = 0.95
    b.link(tex.outputs["Color"], b.bsdf.inputs["Base Color"])
    npath = VEG / f"{name}_n.png"
    if npath.exists():           # v3.4: albedo + sky visibility (the engine also uses the normals; ADR 0023)
        nt_ = b.nt.nodes.new("ShaderNodeTexImage")
        nt_.image = bpy.data.images.load(str(npath))
        nt_.image.colorspace_settings.name = "Non-Color"
        b.link(b.uv("UVMap"), nt_.inputs["Vector"])
        sep = b.nt.nodes.new("ShaderNodeSeparateColor")
        b.link(nt_.outputs["Color"], sep.inputs["Color"])
        mix = b.nt.nodes.new("ShaderNodeMix")
        mix.data_type = "RGBA"
        mix.blend_type = "MULTIPLY"
        b.link(sep.outputs["Blue"], mix.inputs["Factor"])
        b.link(tex.outputs["Color"], mix.inputs[6])
        mix.inputs[7].default_value = (0.35, 0.35, 0.35, 1.0)
        inv = b.nt.nodes.new("ShaderNodeMath")
        inv.operation = "SUBTRACT"
        inv.inputs[0].default_value = 1.0
        b.link(sep.outputs["Blue"], inv.inputs[1])
        b.link(inv.outputs[0], mix.inputs["Factor"])
        b.link(mix.outputs[2], b.bsdf.inputs["Base Color"])
    if name.startswith("forest_edge"):
        b.link(tex.outputs["Alpha"], b.bsdf.inputs["Alpha"])
        try:
            m.surface_render_method = "DITHERED"
        except AttributeError:
            pass
        m.use_backface_culling = False
    else:                       # canopy is single sided (glTF doubleSided false): never seen from below
        m.use_backface_culling = True
    return m


def build_materials():
    g = lambda c: srgb(c)
    M = {
        **{f"forest_{k}_{mix}": mat_forest(f"forest_{k}_{mix}") for k in ("edge", "canopy")
           for mix in ("conifer", "mixed", "broadleaf")},
        "road_asphalt": mat_asphalt("road_asphalt"),
        "road_asphalt_new": mat_asphalt("road_asphalt_new", 0.055),
        "yard_asphalt": mat_asphalt("yard_asphalt", 0.08, lanes=False, yard=True),
        "path_asphalt": mat_asphalt("path_asphalt", 0.085, lanes=False),
        "road_concrete": mat_concrete_yard("road_concrete", 0.27, 5.0, 3.5),
        "road_paving": mat_pavers("road_paving", g((92, 88, 82)), g((100, 96, 88)), moss=False),
        "road_sett": mat_pavers("road_sett", g((80, 76, 72)), g((90, 86, 80)), 0.12, 0.12, moss=False),
        "road_gravel": mat_gravel("road_gravel"),
        "curb_concrete": mat_kerb("curb_concrete", 0.26),
        "sidewalk_paving": mat_pavers("sidewalk_paving", g((122, 120, 114)), g((112, 110, 104)), moss=False),
        "apron_sett": mat_pavers("apron_sett", g((104, 90, 84)), g((92, 80, 76)), 0.12, 0.12, moss=False),
        "bridge_concrete": mat_concrete_struct("bridge_concrete", 0.30),
        "bridge_soffit": mat_concrete_struct("bridge_soffit", 0.15),
        "barrier_steel": mat_flat("barrier_steel", (0.30, 0.31, 0.31), 0.5, 0.9, 0.3),
        "verge_grass": mat_terrain("verge_grass"),
        "shoulder_gravel": mat_gravel("shoulder_gravel"),
        "terrain_grass": mat_terrain("terrain_grass"),
        "marking_white": mat_markings("marking_white"),
        "yard_paving": mat_pavers("yard_paving", g((118, 117, 112)), g((106, 105, 100))),
        "cycle_red": mat_pavers("cycle_red", g((120, 62, 54)), g((108, 56, 50))),
        "yard_concrete": mat_concrete_yard("yard_concrete", 0.28, 5.0, 5.0),
        "yard_slabs": mat_concrete_yard("yard_slabs", 0.26, 3.0, 1.5, slabs=True),
        "yard_gravel": mat_gravel("yard_gravel"),
        "hall_wall_grey": mat_hall("hall_wall_grey", g((182, 184, 182)), "h"),
        "hall_wall_silver": mat_hall("hall_wall_silver", g((166, 170, 172)), "v"),
        "hall_wall_white": mat_hall("hall_wall_white", g((196, 197, 194)), "h"),
        "hall_wall_ivory": mat_hall("hall_wall_ivory", g((196, 186, 160)), "v"),
        "hall_plinth": mat_concrete_yard("hall_plinth", 0.24, 6.0, 100.0),
        "hall_flashing": mat_flat("hall_flashing", g((58, 62, 66)), 0.5, 0.3),
        "roof_membrane": mat_flat("roof_membrane", g((70, 70, 70)), 0.85),
        "skylight": mat_flat("skylight", g((190, 192, 190)), 0.3),
        "reveal_hall": mat_flat("reveal_hall", g((140, 142, 142)), 0.6),
        "reveal_plaster": mat_flat("reveal_plaster", g((160, 156, 146)), 0.85),
        "plaster_light": mat_plaster("plaster_light", g((196, 192, 182))),
        "plaster_grey": mat_plaster("plaster_grey", g((150, 150, 148))),
        "plaster_beige": mat_plaster("plaster_beige", g((190, 176, 150))),
        "plaster_cream": mat_plaster("plaster_cream", g((200, 184, 146))),
        "plaster_pastel_blue": mat_plaster("plaster_pastel_blue", g((150, 166, 176))),
        "brick_red": mat_pavers("brick_red", g((116, 70, 56)), g((104, 64, 52)), 0.25, 0.065, rot_uv=True, moss=False),
        "plinth_dark": mat_flat("plinth_dark", g((90, 90, 88)), 0.9),
        "roof_tiles_red": mat_lines_v("roof_tiles_red", g((120, 52, 36)), 0.33, 0.03, 0.7, 0.0),
        "roof_tiles_brown": mat_lines_v("roof_tiles_brown", g((76, 50, 40)), 0.33, 0.03, 0.7, 0.0),
        "roof_metal_graphite": mat_lines_v("roof_metal_graphite", g((52, 54, 56)), 0.35, 0.03, 0.45, 0.4),
        "glass": mat_glass("glass"),
        "door_glass": mat_glass("door_glass"),
        "window_frame": mat_flat("window_frame", g((200, 200, 196)), 0.5, 0.0, 0.05),
        "door_steel": mat_flat("door_steel", g((120, 124, 126)), 0.5, 0.4),
        "garage_door": mat_lines_v("garage_door", g((160, 160, 156)), 0.55, 0.012, 0.5, 0.3),
        "dock_door": mat_lines_v("dock_door", g((150, 156, 160)), 0.6, 0.012, 0.45, 0.3, dirt_h=1.1, dirt_k=0.6),
        "dock_shelter": mat_flat("dock_shelter", (0.022, 0.022, 0.022), 0.75),
        "hazard_stripes": mat_hazard("hazard_stripes"),
        "noise_panel": mat_lines_v("noise_panel", g((104, 116, 108)), 0.5, 0.015, 0.6, 0.3),
        "concrete_fence": mat_lines_v("concrete_fence", g((140, 136, 128)), 0.5, 0.02, 0.9, 0.0),
        "concrete_wall": mat_concrete_yard("concrete_wall", 0.26, 4.0, 100.0),
        "steel_galv": mat_flat("steel_galv", (0.33, 0.34, 0.34), 0.55, 0.85, 0.3),
        "barrier_post": mat_flat("barrier_post", (0.30, 0.31, 0.31), 0.55, 0.85, 0.3),
        "yard_behaton": mat_behaton("yard_behaton", g((112, 111, 106)), g((98, 97, 93))),
        "decal_patch": mat_decal_patch("decal_patch"),
        "decal_oil": mat_decal_oil("decal_oil"),
        "decal_tyre": mat_decal_tyre("decal_tyre"),
        "hall_wall_graphite": mat_hall("hall_wall_graphite", g((66, 70, 74)), "v"),
        "hall_wall_accent_blue": mat_hall("hall_wall_accent_blue", g((58, 84, 112)), "v"),
        "hall_wall_accent_red": mat_hall("hall_wall_accent_red", g((126, 58, 50)), "v"),
        "hall_wall_accent_green": mat_hall("hall_wall_accent_green", g((64, 98, 80)), "v"),
        "booth_panel": mat_hall("booth_panel", g((176, 178, 176)), "h"),
        "balcony_panel": mat_lines_v("balcony_panel", g((150, 154, 156)), 0.12, 0.01, 0.6, 0.3, horizontal=False),
        "balcony_slab": mat_concrete_yard("balcony_slab", 0.27, 100.0, 100.0),
        "panel_concrete": mat_large_panel("panel_concrete", g((150, 146, 136))),
        "plaster_accent_terracotta": mat_plaster("plaster_accent_terracotta", g((168, 96, 70))),
        "plaster_accent_green": mat_plaster("plaster_accent_green", g((120, 142, 112))),
        "plaster_accent_ochre": mat_plaster("plaster_accent_ochre", g((190, 150, 88))),
        "plaster_accent_grey": mat_plaster("plaster_accent_grey", g((104, 106, 108))),
        "wood_planks": mat_planks("wood_planks", g((112, 84, 58))),
        "wood_planks_green": mat_planks("wood_planks_green", g((70, 96, 78))),
        "chimney_brick": mat_pavers("chimney_brick", g((116, 58, 44)), g((104, 52, 42)), 0.25, 0.065, rot_uv=True,
                                    moss=False),
        "pallet_wood": mat_pallet("pallet_wood", g((150, 124, 92))),
        "gate_boom": mat_boom("gate_boom"),
        "trailer_curtain_grey": mat_curtain("trailer_curtain_grey", g((110, 112, 112))),
        "trailer_curtain_blue": mat_curtain("trailer_curtain_blue", g((52, 64, 88))),
        "trailer_curtain_white": mat_curtain("trailer_curtain_white", g((196, 198, 196))),
        "trailer_curtain_red": mat_curtain("trailer_curtain_red", g((112, 52, 46))),
        "trailer_curtain_green": mat_curtain("trailer_curtain_green", g((62, 84, 70))),
        "trailer_curtain_silver": mat_curtain("trailer_curtain_silver", g((160, 162, 162))),
        "trailer_box_white": mat_lines_v("trailer_box_white", g((200, 202, 200)), 1.2, 0.006, 0.45, 0.1, horizontal=False),
        "bridge_fascia_red": mat_plaster("bridge_fascia_red", g((150, 52, 44))),
        "bridge_fascia_green": mat_plaster("bridge_fascia_green", g((70, 118, 84))),
        "pier_yellow": mat_plaster("pier_yellow", g((178, 166, 98))),
        "noise_glass": mat_screen_glass("noise_glass"),
        "chimney_concrete": mat_plaster("chimney_concrete", g((150, 150, 146))),
        "chimney_red": mat_flat("chimney_red", g((160, 48, 40)), 0.85),
        "chimney_white": mat_flat("chimney_white", g((206, 206, 202)), 0.85),
        "signal_red_on": mat_emit("signal_red_on", (1.0, 0.08, 0.03), 18.0),
        "signal_green_on": mat_emit("signal_green_on", (0.1, 1.0, 0.55), 14.0),
        # v3.1 facade palette + walled ramps
        "plaster_yellow": mat_plaster("plaster_yellow", g((206, 188, 132))),
        "plaster_peach": mat_plaster("plaster_peach", g((206, 168, 140))),
        "plaster_sage": mat_plaster("plaster_sage", g((160, 170, 146))),
        "plaster_white": mat_plaster("plaster_white", g((208, 208, 204))),
        "plaster_band_grey": mat_plaster("plaster_band_grey", g((112, 114, 114))),
        "ramp_wall_blocks": mat_pavers("ramp_wall_blocks", g((150, 146, 138)), g((136, 132, 126)), 0.40, 0.20,
                                       rot_uv=True, moss=False),
    }
    # LOD1 far facades <wall>__far_<kind>: colour of the wall material in this table (render sRGB values)
    wall_rgb = {"plaster_light": (196, 192, 182), "plaster_grey": (150, 150, 148), "plaster_beige": (190, 176, 150),
                "plaster_cream": (200, 184, 146), "plaster_pastel_blue": (150, 166, 176), "plaster_yellow": (206, 188, 132),
                "plaster_peach": (206, 168, 140), "plaster_sage": (160, 170, 146), "plaster_white": (208, 208, 204),
                "brick_red": (112, 68, 55), "panel_concrete": (150, 146, 136)}
    grids = {"block": {"win_w": 0.50, "sill": 0.32, "head": 0.84}, "office": {"win_w": 0.50, "sill": 0.26, "head": 0.71},
             "ribbon": {"win_w": 1.00, "sill": 0.26, "head": 0.71}}
    for w_, rgb in wall_rgb.items():
        for k_, gr in grids.items():
            M[f"{w_}__far_{k_}"] = mat_far_facade(f"{w_}__far_{k_}", g(rgb), gr)
    return M


EMIT = {"road_asphalt": (0.06, 0.06, 0.06), "curb_concrete": (1.0, 1.0, 1.0), "sidewalk_paving": (1.0, 0.55, 0.15),
        "apron_sett": (1.0, 0.3, 0.1), "marking_white": (1.0, 1.0, 0.0), "bridge_concrete": (0.35, 0.45, 1.0),
        "barrier_steel": (0.2, 0.3, 1.0), "road_paving": (0.6, 0.35, 0.2), "road_concrete": (0.3, 0.3, 0.3),
        "road_sett": (0.5, 0.3, 0.2), "road_gravel": (0.5, 0.45, 0.3), "yard_paving": (0.0, 0.8, 0.8),
        "yard_concrete": (0.0, 0.5, 1.0), "yard_asphalt": (0.6, 0.0, 0.6), "yard_slabs": (0.0, 0.8, 0.0),
        "yard_gravel": (0.5, 0.35, 0.2), "cycle_red": (1.0, 0.0, 0.0)}


# ============================================================================================ scene
def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def import_glb(path):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(path), merge_vertices=False)
    return [o for o in bpy.data.objects if o not in before]


def import_chunk(path, keep, root):
    new = import_glb(path)
    out = []
    for o in new:
        if o.type != "MESH" or o.name.split(".")[0] not in keep:
            bpy.data.objects.remove(o, do_unlink=True)
            continue
        o.parent = root
        out.append(o)
    return out


def assign_materials(objs, mats, emit=False):
    cache = {}
    for o in objs:
        if o.type != "MESH":
            continue
        for slot in o.material_slots:
            if slot.material is None:
                continue
            key = slot.material.name.split(".")[0]
            if emit:
                if key not in cache:
                    cache[key] = mat_emit("emit_" + key, EMIT.get(key, (0.5, 0, 0.5)))
                slot.material = cache[key]
            elif key in mats:
                slot.material = mats[key]


def load_protos(mats):
    """Street props + trees as hidden prototype objects (props rotated into the E,N,U frame)."""
    coll = bpy.data.collections.new("protos")
    bpy.context.scene.collection.children.link(coll)
    protos = {}
    files = [(PROPS_GLB, True), (VEG / "trees.glb", False),
             (VEG / "trees_lod2.glb", False)]
    for path, rot in files:
        if not path.exists():
            continue
        for o in import_glb(path):
            if o.type != "MESH":
                continue
            if rot:
                o.data.transform(Matrix.Rotation(math.pi, 4, "Z"))
            o.matrix_world = Matrix.Identity(4)
            for c in o.users_collection:
                c.objects.unlink(o)
            coll.objects.link(o)
            o.hide_render = True
            o.hide_viewport = True
            protos[o.name] = o
    assign_materials(list(protos.values()), mats)
    for o in protos.values():
        for s in o.material_slots:
            if s.material and s.material.name.startswith(("sign_", "plate_back")):
                s.material.use_backface_culling = True      # the plate back hides the face from behind
            if s.material and s.material.name.startswith(("leaves", "impostor", "fence")):
                try:
                    s.material.surface_render_method = "DITHERED"
                except AttributeError:
                    pass
            if s.material and s.material.name.startswith("impostor") and not s.material.get("views_mapped"):
                _impostor_view0(s.material)
    return protos


def _impostor_view0(m):
    """v3.4 impostors hold IMP_NF views side by side (make_trees.py); the Blender render turns each impostor quad to
    the camera (place_trees) and shows view 0 (the engine blends the two views around the camera azimuth)."""
    meta = json.loads((VEG / "trees_meta.json").read_text(encoding="utf-8"))["trees"]
    name = m.name.split(".")[0][len("impostor_"):]
    n = int(meta.get(name, {}).get("impostor_views", 1))
    m["views_mapped"] = True
    if n <= 1:
        return
    nt = m.node_tree
    for tex in [x for x in nt.nodes if x.type == "TEX_IMAGE"]:
        uv = nt.nodes.new("ShaderNodeUVMap")
        mp = nt.nodes.new("ShaderNodeMapping")
        mp.inputs["Scale"].default_value = (1.0 / n, 1.0, 1.0)
        nt.links.new(uv.outputs["UV"], mp.inputs["Vector"])
        nt.links.new(mp.outputs["Vector"], tex.inputs["Vector"])


def place_props(insts, protos, cam_pos, radius):
    n = 0
    for it in insts:
        p = it["p"]
        if p.startswith("tree_"):
            continue
        if math.hypot(it["e"] - cam_pos[0], it["n"] - cam_pos[1]) > radius and not p.startswith("landmark_"):
            continue
        far = math.hypot(it["e"] - cam_pos[0], it["n"] - cam_pos[1]) > 120
        src = protos.get(p + ".lod1") if far else None
        src = src or protos.get(p)
        if src is None:
            continue
        ob = bpy.data.objects.new(p, src.data)
        ob.location = (it["e"], it["n"], it["z"])
        ob.rotation_euler = (0, 0, it["yaw"])
        if "sz" in it:
            ob.scale = (1, 1, it["sz"])
        bpy.context.scene.collection.objects.link(ob)
        n += 1
    return n


def place_trees(insts, protos, cam_pos, radius, lod_m=(80.0, 250.0), far_cells=frozenset()):
    """One point cloud per (prototype, LOD) -> Instance on Points (scale = h / href, yaw, lean). lod_m = LOD0 / LOD1
    limits of the High tree policy (world_manifest lod_policy); trees of forest HLOD cells drawn as HLOD are skipped."""
    meta = json.loads((VEG / "trees_meta.json").read_text(encoding="utf-8"))["trees"]
    groups = {}
    for it in insts:
        if not it["p"].startswith("tree_") or it.get("fc") in far_cells:
            continue
        d = math.hypot(it["e"] - cam_pos[0], it["n"] - cam_pos[1])
        if d > radius:
            continue
        name = f"{it['p']}_{it['v']}"
        lod = "" if d < lod_m[0] else (".lod1" if d < lod_m[1] else ".lod2")
        groups.setdefault((name, lod), []).append(it)
    total = 0
    for (name, lod), pts in sorted(groups.items()):
        src = protos.get(name + lod) or protos.get(name)
        if src is None:
            continue
        href = meta[name]["href_m"]
        me = bpy.data.meshes.new(f"pts_{name}{lod}")
        me.from_pydata([(t["e"], t["n"], t["z"] - 0.15) for t in pts], [], [])
        sc = me.attributes.new("sc", "FLOAT", "POINT")
        sc.data.foreach_set("value", [t["h"] / href for t in pts])
        rot = me.attributes.new("rot", "FLOAT_VECTOR", "POINT")
        flat = []
        for t in pts:
            if lod == ".lod2":       # billboard: view 0 (camera at -Y of the tree) turned toward the camera
                flat += [0.0, 0.0, math.atan2(cam_pos[0] - t["e"], -(cam_pos[1] - t["n"]))]
                continue
            flat += [t["lean"] * math.cos(t["yaw"] * 3), t["lean"] * math.sin(t["yaw"] * 3), t["yaw"]]
        rot.data.foreach_set("vector", flat)
        ob = bpy.data.objects.new(f"trees_{name}{lod}", me)
        bpy.context.scene.collection.objects.link(ob)
        ng = bpy.data.node_groups.new(f"inst_{name}{lod}", "GeometryNodeTree")
        ng.interface.new_socket(name="Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
        ng.interface.new_socket(name="Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
        N, L = ng.nodes, ng.links
        gi, go = N.new("NodeGroupInput"), N.new("NodeGroupOutput")
        inst = N.new("GeometryNodeInstanceOnPoints")
        info = N.new("GeometryNodeObjectInfo")
        info.inputs["Object"].default_value = src
        a_sc = N.new("GeometryNodeInputNamedAttribute")
        a_sc.data_type = "FLOAT"
        a_sc.inputs["Name"].default_value = "sc"
        a_rot = N.new("GeometryNodeInputNamedAttribute")
        a_rot.data_type = "FLOAT_VECTOR"
        a_rot.inputs["Name"].default_value = "rot"
        L.new(gi.outputs["Geometry"], inst.inputs["Points"])
        L.new(info.outputs["Geometry"], inst.inputs["Instance"])
        L.new(a_sc.outputs["Attribute"], inst.inputs["Scale"])
        L.new(a_rot.outputs["Attribute"], inst.inputs["Rotation"])
        L.new(inst.outputs["Instances"], go.inputs["Geometry"])
        ob.modifiers.new("inst", "NODES").node_group = ng
        total += len(pts)
    return total


def add_grass(terrain_objs, cam_pos, radius=55.0):
    """Grass / weed cards scattered on the LOD0 terrain near the camera, density from the ground masks
    (more in unmown grass, along the kerb line; none on forest floor or bare ground)."""
    path = VEG / "grass_tuft.png"
    if not path.exists():
        return
    m = bpy.data.materials.new("grass_tuft")
    b = NB(m)
    tex = b.nt.nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(str(path))
    # per-instance tint
    oi = b.nt.nodes.new("ShaderNodeObjectInfo")
    # ~7 % dead tufts, straw tint kept close to the live colour (the saturated yellow read as polka dots)
    dead = b.math("LESS_THAN", oi.outputs["Random"], 0.07)
    tint = b.mix(dead, (1.0, 1.0, 1.0), (1.22, 1.06, 0.78), blend="MULTIPLY")
    # live tufts a little darker than the card texture so they sit in the ground colour instead of sparkling
    vary = b.mix(b.math("MULTIPLY", oi.outputs["Random"], 0.35), (0.80, 0.84, 0.74), (0.70, 0.80, 0.64), blend="MIX")
    colt = b.mix(1.0, tex.outputs["Color"], tint, blend="MULTIPLY")
    colt = b.mix(1.0, colt, vary, blend="MULTIPLY")
    b.link(colt, b.bsdf.inputs["Base Color"])
    b.link(tex.outputs["Alpha"], b.bsdf.inputs["Alpha"])
    b.bsdf.inputs["Roughness"].default_value = 0.9
    try:
        m.surface_render_method = "DITHERED"
    except AttributeError:
        pass
    me = bpy.data.meshes.new("tuft")
    V, F, UV = [], [], []
    for k in range(3):
        a = k * math.pi / 3
        c, s = math.cos(a) * 0.35, math.sin(a) * 0.35
        base = len(V)
        V += [(-c, -s, 0), (c, s, 0), (c, s, 0.5), (-c, -s, 0.5)]
        UV += [(0, 0), (1, 0), (1, 1), (0, 1)]
        F.append((base, base + 1, base + 2, base + 3))
    me.from_pydata(V, [], F)
    uvl = me.uv_layers.new()
    for poly in me.polygons:
        for li in poly.loop_indices:
            uvl.data[li].uv = UV[me.loops[li].vertex_index]
    me.materials.append(m)
    tuft = bpy.data.objects.new("tuft", me)
    bpy.context.scene.collection.objects.link(tuft)
    tuft.hide_render = True
    for t in terrain_objs:
        loc = t.matrix_world.inverted() @ Vector(cam_pos)
        ng = bpy.data.node_groups.new("grass", "GeometryNodeTree")
        ng.interface.new_socket(name="Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
        ng.interface.new_socket(name="Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
        N, L = ng.nodes, ng.links
        gi, go = N.new("NodeGroupInput"), N.new("NodeGroupOutput")
        pos = N.new("GeometryNodeInputPosition")
        dist = N.new("ShaderNodeVectorMath")
        dist.operation = "DISTANCE"
        dist.inputs[1].default_value = (loc.x, loc.y, loc.z)
        L.new(pos.outputs[0], dist.inputs[0])
        near = N.new("FunctionNodeCompare")
        near.data_type = "FLOAT"
        near.operation = "LESS_THAN"
        near.inputs[1].default_value = radius
        L.new(dist.outputs["Value"], near.inputs[0])
        col = N.new("GeometryNodeInputNamedAttribute")
        col.data_type = "FLOAT_COLOR"
        col.inputs["Name"].default_value = "Color"
        sepc = N.new("FunctionNodeSeparateColor")
        L.new(col.outputs["Attribute"], sepc.inputs[0])
        # density = 26 * (0.25 + B) * (1 - G) * (1 - A) * (dist-to-road > 0.5 m): mown grass = many small tufts
        # (reads as texture), unmown = fewer, taller ones
        mB = N.new("ShaderNodeMath"); mB.operation = "ADD"; mB.inputs[1].default_value = 0.25
        L.new(sepc.outputs[2], mB.inputs[0])
        g1 = N.new("ShaderNodeMath"); g1.operation = "SUBTRACT"; g1.inputs[0].default_value = 1.0
        L.new(sepc.outputs[1], g1.inputs[1])
        d0 = N.new("ShaderNodeMath"); d0.operation = "MULTIPLY"
        L.new(mB.outputs[0], d0.inputs[0]); L.new(g1.outputs[0], d0.inputs[1])
        rr = N.new("ShaderNodeMath"); rr.operation = "GREATER_THAN"; rr.inputs[1].default_value = 0.035
        L.new(sepc.outputs[0], rr.inputs[0])
        d1 = N.new("ShaderNodeMath"); d1.operation = "MULTIPLY"
        L.new(d0.outputs[0], d1.inputs[0]); L.new(rr.outputs[0], d1.inputs[1])
        d2 = N.new("ShaderNodeMath"); d2.operation = "MULTIPLY"; d2.inputs[1].default_value = 26.0
        L.new(d1.outputs[0], d2.inputs[0])
        dist_pts = N.new("GeometryNodeDistributePointsOnFaces")
        dist_pts.distribute_method = "RANDOM"
        L.new(gi.outputs["Geometry"], dist_pts.inputs["Mesh"])
        L.new(near.outputs[0], dist_pts.inputs["Selection"])
        # clustered density (no polka dots): patches of ~4-8 m where the noise is high, bare in between
        cn = N.new("ShaderNodeTexNoise")
        cn.inputs["Scale"].default_value = 0.18
        cn.inputs["Detail"].default_value = 3.0
        cpos = N.new("GeometryNodeInputPosition")
        L.new(cpos.outputs[0], cn.inputs["Vector"])
        cl = N.new("ShaderNodeMapRange")
        cl.inputs["From Min"].default_value = 0.42
        cl.inputs["From Max"].default_value = 0.62
        cl.inputs["To Min"].default_value = 0.05
        cl.inputs["To Max"].default_value = 2.2
        L.new(cn.outputs["Fac"], cl.inputs["Value"])
        d3 = N.new("ShaderNodeMath"); d3.operation = "MULTIPLY"
        L.new(d2.outputs[0], d3.inputs[0]); L.new(cl.outputs["Result"], d3.inputs[1])
        L.new(d3.outputs[0], dist_pts.inputs["Density"])
        inst = N.new("GeometryNodeInstanceOnPoints")
        info = N.new("GeometryNodeObjectInfo")
        info.inputs["Object"].default_value = tuft
        rnd = N.new("FunctionNodeRandomValue")
        rnd.data_type = "FLOAT_VECTOR"
        rnd.inputs["Min"].default_value = (0, 0, 0)
        rnd.inputs["Max"].default_value = (0.25, 0.25, 6.28)
        rs = N.new("FunctionNodeRandomValue")
        rs.data_type = "FLOAT"
        rs.inputs[2].default_value = 0.45
        rs.inputs[3].default_value = 1.25
        L.new(dist_pts.outputs["Points"], inst.inputs["Points"])
        L.new(info.outputs["Geometry"], inst.inputs["Instance"])
        L.new(rnd.outputs["Value"], inst.inputs["Rotation"])
        # mown verges (B = 0) get short tufts, unmown grass tall ones
        sB = N.new("ShaderNodeMath"); sB.operation = "MULTIPLY_ADD"
        L.new(sepc.outputs[2], sB.inputs[0]); sB.inputs[1].default_value = 0.95; sB.inputs[2].default_value = 0.2
        sS = N.new("ShaderNodeMath"); sS.operation = "MULTIPLY"
        L.new(rs.outputs[1], sS.inputs[0]); L.new(sB.outputs[0], sS.inputs[1])
        # taller toward the kerb / road edge (R = distance to the road / 20 m): x1.35 at the kerb, x0.9 beyond 2.5 m
        kr = N.new("ShaderNodeMapRange")
        kr.inputs["From Min"].default_value = 0.03
        kr.inputs["From Max"].default_value = 0.125
        kr.inputs["To Min"].default_value = 1.35
        kr.inputs["To Max"].default_value = 0.9
        L.new(sepc.outputs[0], kr.inputs["Value"])
        sK = N.new("ShaderNodeMath"); sK.operation = "MULTIPLY"
        L.new(sS.outputs[0], sK.inputs[0]); L.new(kr.outputs["Result"], sK.inputs[1])
        L.new(sK.outputs[0], inst.inputs["Scale"])
        join = N.new("GeometryNodeJoinGeometry")
        L.new(gi.outputs["Geometry"], join.inputs[0])
        L.new(inst.outputs["Instances"], join.inputs[0])
        L.new(join.outputs[0], go.inputs["Geometry"])
        t.modifiers.new("grass", "NODES").node_group = ng


def setup_world(scene, engine, samples, res, light):
    w, h = (int(x) for x in res.split("x"))
    scene.render.resolution_x, scene.render.resolution_y = w, h
    scene.render.resolution_percentage = 100
    if engine == "CYCLES":
        scene.render.engine = "CYCLES"
        scene.cycles.samples = samples
        scene.cycles.use_denoising = True
    else:
        scene.render.engine = "BLENDER_EEVEE_NEXT"
        scene.eevee.taa_render_samples = samples
        try:
            scene.eevee.use_shadows = True
            scene.eevee.shadow_ray_count = 2
            scene.eevee.shadow_step_count = 8
            scene.eevee.use_raytracing = False
            scene.eevee.use_gtao = True
            scene.eevee.gtao_distance = 1.5
            scene.eevee.fast_gi_method = "GLOBAL_ILLUMINATION"
        except AttributeError:
            pass
    scene.view_settings.view_transform = "AgX"
    looks = [i.identifier for i in scene.view_settings.bl_rna.properties["look"].enum_items]
    for lk in ("AgX - Base Contrast", "AgX - Medium High Contrast"):
        if lk in looks:
            scene.view_settings.look = lk
            break
    world = bpy.data.worlds.new("sky")
    scene.world = world
    world.use_nodes = True
    nt = world.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    sky = nt.nodes.new("ShaderNodeTexSky")
    sky.sky_type = "NISHITA"
    sky.altitude = 150
    sky.air_density = 1.0
    bg = nt.nodes.new("ShaderNodeBackground")
    out = nt.nodes.new("ShaderNodeOutputWorld")
    sun = bpy.data.lights.new("sun", "SUN")
    so = bpy.data.objects.new("sun", sun)
    scene.collection.objects.link(so)
    # horizon haze: the view direction's z drives a mix toward a haze colour at / below the horizon (the tile
    # ends 1 km away; below the horizon the camera sees haze, not the black Nishita ground)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sepz = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Generated"], sepz.inputs[0])
    hz = nt.nodes.new("ShaderNodeMapRange")
    hz.inputs["From Min"].default_value = -0.02
    hz.inputs["From Max"].default_value = 0.25
    hz.inputs["To Min"].default_value = 1.0
    hz.inputs["To Max"].default_value = 0.0
    nt.links.new(sepz.outputs["Z"], hz.inputs["Value"])
    mixh = nt.nodes.new("ShaderNodeMix")
    mixh.data_type = "RGBA"
    nt.links.new(hz.outputs["Result"], mixh.inputs["Factor"])
    if light == "lowsun":
        el, az = 8.0, 235.0           # late afternoon, WSW (autumn in Białystok)
        sky.sun_elevation = math.radians(el)
        sky.sun_rotation = math.radians(az)
        sky.dust_density = 2.5
        sky.sun_disc = False
        nt.links.new(sky.outputs["Color"], mixh.inputs["A"])
        mixh.inputs["B"].default_value = (0.55, 0.50, 0.44, 1)
        bg.inputs["Strength"].default_value = 0.30
        sun.energy = 3.0
        sun.angle = math.radians(0.6)
        sun.color = (1.0, 0.80, 0.60)
        scene.view_settings.exposure = -0.3
        # Lighting (non-camera rays) differs from the visible sky: the single-scattering sky is far too blue as
        # an irradiance source at 8 deg sun (teal shadows next to orange light). Desaturate it to 50 % and give
        # the lower hemisphere a warm-grey ground bounce (dry grass / asphalt / concrete, albedo ~0.15-0.25)
        # so shadowed walls are lit half by the sky and half by the ground (cool grey, not cyan).
        bw = nt.nodes.new("ShaderNodeRGBToBW")
        nt.links.new(sky.outputs["Color"], bw.inputs["Color"])
        desat = nt.nodes.new("ShaderNodeMix")
        desat.data_type = "RGBA"
        desat.inputs["Factor"].default_value = 0.5
        nt.links.new(sky.outputs["Color"], desat.inputs["A"])
        nt.links.new(bw.outputs["Val"], desat.inputs["B"])
        gz = nt.nodes.new("ShaderNodeMapRange")
        gz.inputs["From Min"].default_value = -0.06
        gz.inputs["From Max"].default_value = 0.04
        gz.inputs["To Min"].default_value = 1.0
        gz.inputs["To Max"].default_value = 0.0
        nt.links.new(sepz.outputs["Z"], gz.inputs["Value"])
        ground = nt.nodes.new("ShaderNodeMix")
        ground.data_type = "RGBA"
        nt.links.new(gz.outputs["Result"], ground.inputs["Factor"])
        nt.links.new(desat.outputs["Result"], ground.inputs["A"])
        ground.inputs["B"].default_value = (0.60, 0.56, 0.50, 1)
        lp = nt.nodes.new("ShaderNodeLightPath")
        cam = nt.nodes.new("ShaderNodeMix")
        cam.data_type = "RGBA"
        nt.links.new(lp.outputs["Is Camera Ray"], cam.inputs["Factor"])
        nt.links.new(ground.outputs["Result"], cam.inputs["A"])
        nt.links.new(mixh.outputs["Result"], cam.inputs["B"])
        mixh = cam
    else:                             # overcast: grey gradient sky + very soft weak key light
        el, az = 40.0, 200.0
        grad = nt.nodes.new("ShaderNodeMix")
        grad.data_type = "RGBA"
        nt.links.new(sepz.outputs["Z"], grad.inputs["Factor"])
        grad.inputs["A"].default_value = (0.78, 0.80, 0.82, 1)
        grad.inputs["B"].default_value = (0.55, 0.58, 0.63, 1)
        nt.links.new(grad.outputs["Result"], mixh.inputs["A"])
        mixh.inputs["B"].default_value = (0.74, 0.76, 0.77, 1)
        bg.inputs["Strength"].default_value = 1.0
        sun.energy = 0.9
        sun.angle = math.radians(40)
        sun.color = (0.97, 0.98, 1.0)
        scene.view_settings.exposure = -0.45
    nt.links.new(mixh.outputs["Result"], bg.inputs["Color"])
    nt.links.new(bg.outputs["Background"], out.inputs["Surface"])
    # light travels from azimuth az (from north, clockwise) and elevation el
    so.rotation_euler = (math.radians(90 - el), 0, math.radians(180 - az))
    scene.render.image_settings.file_format = "JPEG"
    scene.render.image_settings.quality = 88


def add_far_ground(z, pos):
    """Large plane beyond the tile (distant fields and woods), so the horizon is land, not void."""
    me = bpy.data.meshes.new("far_ground")
    R = 15000.0
    me.from_pydata([(pos[0] - R, pos[1] - R, z), (pos[0] + R, pos[1] - R, z), (pos[0] + R, pos[1] + R, z),
                    (pos[0] - R, pos[1] + R, z)], [], [(0, 1, 2, 3)])
    m = new_mat("far_ground")
    b = NB(m)
    obj = b.tc.outputs["Object"]
    n = b.noise(obj, 0.004, 4.0, 0.6)
    col = b.ramp(n, [(0.4, srgb((44, 54, 34))), (0.55, srgb((70, 80, 46))), (0.7, srgb((96, 94, 62)))])
    b.finish(col, 0.95)
    me.materials.append(m)
    ob = bpy.data.objects.new("far_ground", me)
    bpy.context.scene.collection.objects.link(ob)


def look_at(obj, target):
    d = Vector(target) - obj.location
    obj.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()


def main():
    a = args()
    cams = json.loads((Path(a.cams_file) if a.cams_file else
                       REPO / f"Data/Regions/{a.region}/generated/control_cameras.json").read_text(encoding="utf-8"))
    if a.props_glb:
        global PROPS_GLB
        PROPS_GLB = Path(a.props_glb)
    man = json.loads((REPO / f"Data/Regions/{a.region}/generated/world_manifest.json").read_text(encoding="utf-8"))
    wanted = [c for c in cams["cameras"] if not a.cams or c["id"] in a.cams.split(",")]
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    world_root = Path(a.world_root) if a.world_root else None
    lights = ["overcast", "lowsun"] if a.light == "both" else [a.light]
    for cam in wanted:
        for light in (lights if cam["type"] != "ortho" else ["overcast"]):
            render_cam(a, cam, man, out, world_root, light)


def render_cam(a, cam, man, out, world_root, light):
    reset()
    scene = bpy.context.scene
    ortho = cam["type"] == "ortho"
    setup_world(scene, a.engine, a.samples, "1600x1600" if ortho else a.res, light)
    root = bpy.data.objects.new("world_root", None)
    root.rotation_euler = (0, 0, math.pi)      # Blender import (-E, -N, U) -> (E, N, U)
    scene.collection.objects.link(root)
    if ortho:
        ctr = cam["center"]
        tgt = (ctr[0], ctr[1], 0)
        radius = cam["size_m"] * 0.8
    else:
        tgt = cam["look_at"]
        radius = 1100.0
    pos = cam.get("pos", [tgt[0], tgt[1], 0])
    pol = man.get("lod_policy", {}).get("High", {})
    tree_lod_m = tuple(lim for lim, _ in pol.get("tree", [[80, 0], [250, 0]])[:2])
    hlod_m = pol.get("forest_hlod_m", 1e9)
    far_cells = set()
    objs, terrain0, insts = [], [], []
    for ch in man["chunks"]:
        b = ch["bounds_local_m"]
        cx, cy = (b["e_min"] + b["e_max"]) / 2, (b["n_min"] + b["n_max"]) / 2
        dist = min(math.hypot(cx - pos[0], cy - pos[1]), math.hypot(cx - tgt[0], cy - tgt[1]))
        if dist > radius + 190:
            continue
        if ortho:
            keep = {"road", "bridge", "markings", "paved"}
        else:
            lod = 0 if dist < 330 else (1 if dist < 600 else 2)
            keep = {f"terrain_lod{lod}", "road", "bridge", "markings", "paved", "furniture"}
            keep.add("buildings" if dist < 700 and not a.bld_lod1 else "buildings_lod1")
            for fc in ch.get("forest_cells", []):
                bb = fc["bbox_local_m"]
                dx = max(bb[0] - pos[0], 0.0, pos[0] - bb[2])
                dy = max(bb[1] - pos[1], 0.0, pos[1] - bb[3])
                if math.hypot(dx, dy) > hlod_m:
                    far_cells.add(fc["id"])
                    keep.add(f"forest_hlod_{fc['id']}")
        path = (world_root / Path(ch["file"]).name) if world_root else REPO / ch["file"]
        new = import_chunk(path, keep, root)
        objs += new
        terrain0 += [o for o in new if o.name.startswith("terrain_lod0")]
        ip = (world_root / Path(ch["instances"]["file"]).name) if world_root else REPO / ch["instances"]["file"]
        if not ortho and ip.exists():
            insts += json.loads(ip.read_text(encoding="utf-8"))["instances"]
    if ortho:
        assign_materials(objs, None, emit=True)
        scene.render.film_transparent = True
        scene.render.image_settings.file_format = "PNG"
        scene.render.image_settings.color_mode = "RGBA"
        scene.view_settings.view_transform = "Standard"
        scene.view_settings.exposure = 0
    else:
        mats = build_materials()
        assign_materials(objs, mats)
        zmin = min((min((o.matrix_world @ Vector(c)).z for c in o.bound_box) for o in objs if o.name.startswith("terrain")),
                   default=pos[2] - 10)
        add_far_ground(zmin - 2.0, pos)
        protos = load_protos(mats)
        n_props = place_props(insts, protos, pos, 650.0)
        n_trees = place_trees(insts, protos, pos, 1300.0, tree_lod_m, frozenset(far_cells))
        bpy.context.view_layer.update()
        if not a.no_grass:
            add_grass(terrain0, pos)
        print(f"[render] {cam['id']}/{light}: {len(objs)} chunk objects, {n_props} props, {n_trees} trees, "
              f"{len(far_cells)} forest HLOD cells")
    cd = bpy.data.cameras.new(cam["id"])
    co = bpy.data.objects.new(cam["id"], cd)
    scene.collection.objects.link(co)
    scene.camera = co
    cd.clip_start, cd.clip_end = 0.1, 4000
    if ortho:
        cd.type = "ORTHO"
        cd.ortho_scale = cam["size_m"]
        co.location = (cam["center"][0], cam["center"][1], cam["height"])
        co.rotation_euler = (0, 0, 0)
        fn = cam["id"] + ".png"
    else:
        cd.angle = math.radians(cam["fov_deg"])
        co.location = cam["pos"]
        look_at(co, cam["look_at"])
        fn = f"{cam['id']}__{light}{a.suffix}.jpg"
    scene.render.filepath = str(out / fn)
    bpy.ops.render.render(write_still=True)
    print(f"[render] wrote {scene.render.filepath}")


main()
