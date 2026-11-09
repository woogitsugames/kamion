"""Blender 4.2 test renders of the ground sets from driver eye height (2.5 m), overcast light (same preset values
as tools/blender/world/render_control.py: grey gradient sky, weak 40 deg-wide key, AgX, exposure -0.45).

    blender -b --factory-startup --python art-source/world/materials/_src/render_test.py -- --out <dir> [--tier High]

The node graph mirrors what the engine shader is expected to do (materials_spec.json): world-planar UV in metres,
macro variation at 64 m (+ rotated 264 m), MaskMap (AO into albedo, smoothness), crack layer over worn asphalt,
photo detail layer near the camera, decals with alpha.
"""
import math
import sys
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[1]
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUTDIR = Path(argv[argv.index("--out") + 1]) if "--out" in argv else ROOT / "_renders"
TIER = argv[argv.index("--tier") + 1] if "--tier" in argv else "High"
ONLY = argv[argv.index("--only") + 1].split(",") if "--only" in argv else None
OUTDIR.mkdir(parents=True, exist_ok=True)

TILE = {"asphalt_sma_fresh": (4, 4), "asphalt_worn": (4, 4), "asphalt_patch": (4, 4),
        "concrete_cast_5m_joints": (10, 10), "concrete_slab_3x1.5": (6, 6), "kerb_concrete_1m": (2, 0.5),
        "behaton_i_grey": (4, 4), "paving_20x10_grey": (4, 4), "grass_verge": (3, 3), "gravel_compacted": (3, 3)}
IMG = {}


def img(path, noncolor):
    key = (str(path), noncolor)
    if key not in IMG:
        im = bpy.data.images.load(str(path), check_existing=True)
        im.colorspace_settings.name = "Non-Color" if noncolor else "sRGB"
        im.alpha_mode = "CHANNEL_PACKED"
        IMG[key] = im
    return IMG[key]


def tex(name, kind, tier=TIER):
    return ROOT / name / tier / f"T_{name}_{kind}.png"


class G:
    def __init__(self, mat):
        self.nt = mat.node_tree
        self.n = self.nt.nodes
        self.l = self.nt.links
        for x in list(self.n):
            self.n.remove(x)

    def node(self, t, **kw):
        nd = self.n.new(t)
        for k, v in kw.items():
            setattr(nd, k, v)
        return nd

    def link(self, a, b):
        self.l.new(a, b)

    def math(self, op, a, b=None, vec=False):
        nd = self.node("ShaderNodeVectorMath" if vec else "ShaderNodeMath", operation=op)
        for i, x in enumerate((a, b)):
            if x is None:
                continue
            if isinstance(x, (int, float)):
                nd.inputs[i].default_value = (x, x, x) if vec else x
            elif isinstance(x, tuple):
                nd.inputs[i].default_value = x
            else:
                self.link(x, nd.inputs[i])
        return nd.outputs[0] if not vec or op not in ("DOT_PRODUCT", "LENGTH", "DISTANCE") else nd.outputs["Value"]

    def mix(self, a, b, f, blend="MIX"):
        nd = self.node("ShaderNodeMix", data_type="RGBA", blend_type=blend)
        for si, x in ((0, f), (6, a), (7, b)):
            sock = nd.inputs[si]
            if isinstance(x, (int, float)):
                sock.default_value = x if si == 0 else (x, x, x, 1.0)
            elif isinstance(x, tuple):
                sock.default_value = x
            else:
                self.link(x, sock)
        return nd.outputs[2]

    def image(self, im, uv):
        t = self.node("ShaderNodeTexImage", image=im, interpolation="Linear", extension="REPEAT")
        self.link(uv, t.inputs[0])
        return t

    def sep(self, col):
        s = self.node("ShaderNodeSeparateColor")
        self.link(col, s.inputs[0])
        return s.outputs


def uv_scaled(g, sx, sy, rot=0.0):
    uvn = g.node("ShaderNodeUVMap")
    m = g.node("ShaderNodeMapping")
    m.inputs["Scale"].default_value = (1 / sx, 1 / sy, 1)
    m.inputs["Rotation"].default_value = (0, 0, rot)
    g.link(uvn.outputs[0], m.inputs[0])
    return m.outputs[0]


def decode_n(g, col):
    return g.math("SUBTRACT", g.math("MULTIPLY", col, 2.0, vec=True), 1.0, vec=True)


def whiteout(g, n1, n2):
    """Whiteout blend of two decoded tangent normals."""
    s1 = g.node("ShaderNodeSeparateXYZ"); g.link(n1, s1.inputs[0])
    s2 = g.node("ShaderNodeSeparateXYZ"); g.link(n2, s2.inputs[0])
    c = g.node("ShaderNodeCombineXYZ")
    g.link(g.math("ADD", s1.outputs[0], s2.outputs[0]), c.inputs[0])
    g.link(g.math("ADD", s1.outputs[1], s2.outputs[1]), c.inputs[1])
    g.link(g.math("MULTIPLY", s1.outputs[2], s2.outputs[2]), c.inputs[2])
    return g.math("NORMALIZE", c.outputs[0], vec=True)


def ground_material(name, set_name, *, cracks=False, detail=False, albedo_variant=None, macro=0.22):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    g = G(m)
    sx, sy = TILE[set_name]
    uv = uv_scaled(g, sx, sy)
    kind = f"BaseColor_{albedo_variant}" if albedo_variant else "BaseColor"
    base = g.image(img(tex(set_name, kind), False), uv).outputs[0]
    mt = g.image(img(tex(set_name, "MaskMap"), True), uv)
    mask = list(g.sep(mt.outputs[0])) + [mt.outputs["Alpha"]]
    nrm = decode_n(g, g.image(img(tex(set_name, "Normal"), True), uv).outputs[0])
    var = g.image(img(tex(set_name, "Var"), True), uv)
    # per-element tone jitter: id + world tile index -> hash (anti-repeat for paving / slabs)
    floor_uv = g.math("FLOOR", uv, vec=True)
    idv = g.node("ShaderNodeCombineXYZ")
    g.link(g.sep(var.outputs[0])[1], idv.inputs[0])
    g.link(g.math("DOT_PRODUCT", floor_uv, (0.37, 0.71, 0.0), vec=True), idv.inputs[1])
    wn = g.node("ShaderNodeTexWhiteNoise", noise_dimensions="3D")
    g.link(idv.outputs[0], wn.inputs["Vector"])
    jit = g.math("ADD", g.math("MULTIPLY", g.math("SUBTRACT", wn.outputs["Value"], 0.5), 0.10), 1.0)
    alb = g.mix(base, jit, 1.0, "MULTIPLY")
    # macro variation, two samples (64 m and 264 m rotated) like Kamion/World Surface
    m1 = g.sep(g.image(img(ROOT / "macro_variation" / TIER / "T_macro_variation.png", True),
                       uv_scaled(g, 64, 64)).outputs[0])
    m2 = g.sep(g.image(img(ROOT / "macro_variation" / TIER / "T_macro_variation.png", True),
                       uv_scaled(g, 264, 264, 0.6)).outputs[0])
    mm = g.math("ADD", g.math("MULTIPLY", g.math("SUBTRACT", m1[0], 0.5), 2 * macro),
                g.math("MULTIPLY", g.math("SUBTRACT", m2[1], 0.5), 1.4 * macro))
    alb = g.mix(alb, g.math("ADD", mm, 1.0), 1.0, "MULTIPLY")
    rough = g.math("SUBTRACT", 1.0, mask[3])
    if cracks:
        cuv = uv_scaled(g, 16, 16)
        cm = g.sep(g.image(img(tex("asphalt_cracks_layer", "Mask"), True), cuv).outputs[0])
        cn = decode_n(g, g.image(img(tex("asphalt_cracks_layer", "Normal"), True), cuv).outputs[0])
        nrm = whiteout(g, nrm, cn)
        presence = g.node("ShaderNodeMapRange")
        g.link(m1[2], presence.inputs[0])
        presence.inputs[1].default_value, presence.inputs[2].default_value = 0.22, 0.45
        crack = g.math("MULTIPLY", cm[0], presence.outputs[0])
        seal = g.math("MULTIPLY", cm[1], presence.outputs[0])
        alb = g.mix(alb, g.math("SUBTRACT", 1.0, g.math("MULTIPLY", crack, 0.7)), 1.0, "MULTIPLY")
        alb = g.mix(alb, (0.03, 0.029, 0.028, 1), seal)
        rough = g.mix(rough, 0.45, seal)
    if detail:
        duv = uv_scaled(g, 1.0, 1.0)
        dal = g.image(img(ROOT / "asphalt_detail_photo" / "High" / "T_asphalt_detail_photo_DetailAlbedo.png", False), duv)
        dn = decode_n(g, g.image(img(ROOT / "asphalt_detail_photo" / "High" / "T_asphalt_detail_photo_DetailNormal.png", True), duv).outputs[0])
        cam = g.node("ShaderNodeCameraData")
        fade = g.node("ShaderNodeMapRange")
        g.link(cam.outputs["View Distance"], fade.inputs[0])
        fade.inputs[1].default_value, fade.inputs[2].default_value = 12.0, 30.0
        fade.inputs[3].default_value, fade.inputs[4].default_value = 1.0, 0.0
        dmul = g.math("MULTIPLY", dal.outputs[0], 4.594794, vec=True)
        alb = g.mix(alb, g.mix((1, 1, 1, 1), dmul, fade.outputs[0]), 1.0, "MULTIPLY")
        nrm = whiteout(g, nrm, g.mix((0, 0, 1, 1), dn, fade.outputs[0]))
    ao = g.mix((1, 1, 1, 1), mask[1], 0.85)
    alb = g.mix(alb, ao, 1.0, "MULTIPLY")
    enc = g.math("ADD", g.math("MULTIPLY", nrm, 0.5, vec=True), 0.5, vec=True)
    nm = g.node("ShaderNodeNormalMap")
    g.link(enc, nm.inputs["Color"])
    bsdf = g.node("ShaderNodeBsdfPrincipled")
    g.link(alb, bsdf.inputs["Base Color"])
    g.link(rough, bsdf.inputs["Roughness"])
    g.link(nm.outputs[0], bsdf.inputs["Normal"])
    bsdf.inputs["Specular IOR Level"].default_value = 0.5
    out = g.node("ShaderNodeOutputMaterial")
    g.link(bsdf.outputs[0], out.inputs[0])
    return m


def oil_material(cell):
    m = bpy.data.materials.new(f"oil_{cell}")
    m.use_nodes = True
    m.surface_render_method = "DITHERED"
    g = G(m)
    uvn = g.node("ShaderNodeUVMap")
    mp = g.node("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (0.5, 0.5, 1)
    mp.inputs["Location"].default_value = ((cell % 2) * 0.5, (1 - cell // 2) * 0.5, 0)
    g.link(uvn.outputs[0], mp.inputs[0])
    t = g.image(img(tex("oil_stain_alpha", "BaseColor"), False), mp.outputs[0])
    t.extension = "CLIP"
    mkt = g.image(img(tex("oil_stain_alpha", "MaskMap"), True), mp.outputs[0])
    mk = list(g.sep(mkt.outputs[0])) + [mkt.outputs["Alpha"]]
    bsdf = g.node("ShaderNodeBsdfPrincipled")
    g.link(t.outputs[0], bsdf.inputs["Base Color"])
    g.link(t.outputs[1], bsdf.inputs["Alpha"])
    g.link(g.math("SUBTRACT", 1.0, mk[3]), bsdf.inputs["Roughness"])
    out = g.node("ShaderNodeOutputMaterial")
    g.link(bsdf.outputs[0], out.inputs[0])
    return m


def quad(name, x0, y0, x1, y1, z, mat, uv_world=True, rot=0.0):
    me = bpy.data.meshes.new(name)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    pts = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    if rot:
        ca, sa = math.cos(rot), math.sin(rot)
        pts = [(cx + (x - cx) * ca - (y - cy) * sa, cy + (x - cx) * sa + (y - cy) * ca) for x, y in pts]
    me.from_pydata([(x, y, z) for x, y in pts], [], [(0, 1, 2, 3)])
    uvl = me.uv_layers.new(name="UVMap")
    for li, lp in enumerate(me.loops):
        x, y = pts[lp.vertex_index]
        uvl.data[li].uv = (x, y) if uv_world else ((0, 0), (1, 0), (1, 1), (0, 1))[lp.vertex_index]
    me.materials.append(mat)
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def kerb(name, x_face, y0, y1, side, mat, h=0.15, w=0.15):
    """Kerb along +y: vertical face at x_face toward the road, top face w wide. UV u = along, v = across profile."""
    me = bpy.data.meshes.new(name)
    xf, xb = x_face, x_face + side * w
    V = [(xf, y0, 0.0), (xf, y1, 0.0), (xf, y1, h), (xf, y0, h), (xb, y1, h), (xb, y0, h)]
    me.from_pydata(V, [], [(0, 1, 2, 3) if side > 0 else (1, 0, 3, 2), (3, 2, 4, 5) if side > 0 else (2, 3, 5, 4)])
    uvl = me.uv_layers.new(name="UVMap")
    prof = {0: 0.0, 1: 0.0, 2: h, 3: h, 4: h + w, 5: h + w}
    for li, lp in enumerate(me.loops):
        vi = lp.vertex_index
        uvl.data[li].uv = (V[vi][1], prof[vi])
    me.materials.append(mat)
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def setup(res=(1280, 720), samples=48):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    IMG.clear()
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_EEVEE_NEXT"
    sc.eevee.taa_render_samples = samples
    for k, v in (("use_shadows", True), ("use_gtao", True), ("gtao_distance", 0.5), ("use_raytracing", False)):
        try:
            setattr(sc.eevee, k, v)
        except AttributeError:
            pass
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.view_settings.view_transform = "AgX"
    looks = [i.identifier for i in sc.view_settings.bl_rna.properties["look"].enum_items]
    for lk in ("AgX - Base Contrast", "AgX - Medium High Contrast"):
        if lk in looks:
            sc.view_settings.look = lk
            break
    sc.view_settings.exposure = -0.45
    w = bpy.data.worlds.new("sky")
    sc.world = w
    w.use_nodes = True
    nt = w.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sz = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Generated"], sz.inputs[0])
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs["From Min"].default_value, mr.inputs["From Max"].default_value = -0.02, 0.6
    nt.links.new(sz.outputs["Z"], mr.inputs[0])
    mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = "RGBA"
    nt.links.new(mr.outputs[0], mx.inputs[0])
    mx.inputs[6].default_value = (0.74, 0.76, 0.77, 1)
    mx.inputs[7].default_value = (0.55, 0.58, 0.63, 1)
    bg = nt.nodes.new("ShaderNodeBackground")
    nt.links.new(mx.outputs[2], bg.inputs[0])
    out = nt.nodes.new("ShaderNodeOutputWorld")
    nt.links.new(bg.outputs[0], out.inputs[0])
    sun = bpy.data.lights.new("sun", "SUN")
    sun.energy, sun.angle, sun.color = 0.9, math.radians(40), (0.97, 0.98, 1.0)
    so = bpy.data.objects.new("sun", sun)
    sc.collection.objects.link(so)
    el, az = 40.0, 200.0
    so.rotation_euler = (math.radians(90 - el), 0, math.radians(180 - az))
    sc.render.image_settings.file_format = "JPEG"
    sc.render.image_settings.quality = 88
    return sc


def camera(sc, x, y, z=2.5, pitch_down=6.0, yaw=0.0, lens=24.0):
    cd = bpy.data.cameras.new("cam")
    cd.lens, cd.sensor_width = lens, 36.0
    cd.clip_end = 3000
    co = bpy.data.objects.new("cam", cd)
    sc.collection.objects.link(co)
    co.location = (x, y, z)
    co.rotation_euler = (math.radians(90 - pitch_down), 0, math.radians(yaw))
    sc.camera = co


def render(sc, name):
    sc.render.filepath = str(OUTDIR / f"{name}.jpg")
    bpy.ops.render.render(write_still=True)
    print("RENDER", sc.render.filepath, flush=True)


def scene_street():
    """Urban dual carriageway like Andersa at Rondo Bieżeństwa: worn asphalt + cracks + patches + oil,
    15 cm kerbs, late-autumn verge, 20x10 footway. Camera: right lane, 2.5 m."""
    sc = setup()
    worn = ground_material("worn", "asphalt_worn", cracks=True, detail=True)
    patch = ground_material("patch", "asphalt_patch", detail=True)
    kerbm = ground_material("kerb", "kerb_concrete_1m", macro=0.1)
    grass = ground_material("grass", "grass_verge", albedo_variant="late_autumn")
    pav = ground_material("pav", "paving_20x10_grey")
    Y0, Y1 = -20, 400
    quad("road_r", -3.5, Y0, 3.5, Y1, 0.0, worn)
    quad("road_l", -13.5, Y0, -6.5, Y1, 0.0, worn)
    kerb("k1", 3.5, Y0, Y1, +1, kerbm)
    kerb("k2", -3.5, Y0, Y1, -1, kerbm)
    kerb("k3", -6.5, Y0, Y1, +1, kerbm)
    kerb("k4", -13.5, Y0, Y1, -1, kerbm)
    quad("verge_r", 3.65, Y0, 5.6, Y1, 0.125, grass)
    quad("walk_r", 5.6, Y0, 7.6, Y1, 0.14, pav)
    quad("grass_r", 7.6, Y0, 3000, Y1, 0.12, grass)
    quad("median", -6.35, Y0, -3.65, Y1, 0.125, grass)
    quad("grass_l", -3000, Y0, -13.65, Y1, 0.12, grass)
    quad("far", -3000, Y1, 3000, 3000, 0.0, grass)
    # patches: jittered size/rotation/age, not on a grid (REVIEW r2 #5)
    for (x0, y0, x1, y1, r) in ((0.6, 9.0, 2.7, 12.3, 0.03), (-2.9, 23.0, -0.4, 29.5, -0.05),
                                (1.2, 41.0, 3.2, 42.4, 0.08), (-3.3, 58.0, 3.3, 63.0, 0.0)):
        quad(f"patch{y0}", x0, y0, x1, y1, 0.002, patch, rot=r)
    quad("oil0", 0.9, 16.0, 2.6, 17.7, 0.0035, oil_material(0), uv_world=False, rot=0.4)
    quad("oil3", -1.9, 33.0, -0.9, 34.0, 0.0035, oil_material(3), uv_world=False)
    camera(sc, 1.75, -18.0, 2.5, pitch_down=5.0)
    render(sc, "street_driver_eye_overcast")


def scene_yard():
    """Logistics yard: behaton apron with oil, JOMB plates, cast concrete, fresh SMA access road, gravel."""
    sc = setup()
    beh = ground_material("beh", "behaton_i_grey")
    jomb = ground_material("jomb", "concrete_slab_3x1.5")
    conc = ground_material("conc", "concrete_cast_5m_joints")
    sma = ground_material("sma", "asphalt_sma_fresh", detail=True)
    grav = ground_material("grav", "gravel_compacted")
    grass = ground_material("grass", "grass_verge")
    kerbm = ground_material("kerb", "kerb_concrete_1m", macro=0.1)
    quad("beh", -2.0, -10, 40, 22, 0.0, beh)
    quad("jomb", -2.0, 22, 40, 46, 0.0, jomb)
    quad("conc", -2.0, 46, 40, 120, 0.0, conc)
    quad("sma", -10.0, -10, -2.15, 300, 0.0, sma)
    kerb("ky", -2.0, -10, 300, +1, kerbm, h=0.02)          # flush kerb at the yard edge
    quad("grav", -12.5, -10, -10.0, 300, -0.01, grav)
    quad("grass", -3000, -10, -12.5, 300, 0.0, grass)
    quad("grass2", 40, -10, 3000, 300, 0.0, grass)
    quad("beh2", -2.0, 120, 40, 300, 0.0, beh)
    quad("far", -3000, 300, 3000, 3000, 0.0, grass)
    for i, (x, y, cell, s, r) in enumerate(((3.0, 4.0, 0, 1.6, 0.3), (7.5, 9.0, 1, 3.0, 1.2), (12.0, 3.0, 2, 2.2, 0.0),
                                            (4.5, 15.0, 3, 1.2, 0.0), (9.0, 28.0, 1, 3.2, 1.4), (16.0, 52.0, 0, 1.6, 0.0))):
        quad(f"oil{i}", x - s / 2, y - s / 2, x + s / 2, y + s / 2, 0.0035 + 0.001 * (y > 22),
             oil_material(cell), uv_world=False, rot=r)
    camera(sc, 2.0, -9.0, 2.5, pitch_down=7.0, yaw=-12.0)
    render(sc, "yard_driver_eye_overcast")


def scene_tiling():
    """One material per frame on a 600 m plane, 2.5 m eye, looking 9 deg down: repetition check."""
    for setn, kw in (("asphalt_worn", dict(cracks=True, detail=True)), ("asphalt_sma_fresh", dict(detail=True)),
                     ("behaton_i_grey", {}), ("paving_20x10_grey", {}), ("concrete_cast_5m_joints", {}),
                     ("concrete_slab_3x1.5", {}), ("grass_verge", {}), ("gravel_compacted", {})):
        sc = setup(res=(640, 360), samples=32)
        m = ground_material(setn, setn, **kw)
        quad("p", -3000, -10, 3000, 600, 0.0, m)
        g = ground_material("g", "grass_verge")
        quad("far", -3000, 600, 3000, 3000, 0.0, g)
        camera(sc, 0.0, 0.0, 2.5, pitch_down=9.0, yaw=-20.0)
        render(sc, f"tiling_{setn}")


if __name__ == "__main__":
    todo = ONLY or ["street", "yard", "tiling"]
    for t in todo:
        {"street": scene_street, "yard": scene_yard, "tiling": scene_tiling}[t]()
