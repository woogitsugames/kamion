"""Control render of the parked-vehicle prototypes (ADR 0073): fixed cameras, overcast + low sun.

  blender -b -P tools/blender/world/render_cars.py -- <cars.json> <out dir> [--light overcast|lowsun] [--cams a,b]

cars.json comes from tools/worldgen/qa/car_preview.py (generator frame: x right, y nose, z up, metres; per-corner
normals as exported to the GLB). Materials are plain Principled equivalents of streetscape.materials.M (colour,
roughness, metal, alpha), so the render shows the SHAPES under a sky; the engine look is checked in WorldC.
Cameras (fixed, so iterations compare 1:1):
  row34f   lineup seen 3/4 from the front, eye 1.6 m      row34r   3/4 from the rear
  cab      from a truck cab (eye 2.5 m) 9 m beside the row side     side elevation (orthographic)
  close    one car 3/4 front at 5 m                        front / rear   elevation of the first three cars
"""

import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:]
SRC, OUT = Path(argv[0]).resolve(), Path(argv[1]).resolve()
LIGHT = argv[argv.index("--light") + 1] if "--light" in argv else "overcast"
CAMS = argv[argv.index("--cams") + 1].split(",") if "--cams" in argv else None
doc = json.loads(SRC.read_text(encoding="utf-8"))
TEX = Path(doc["textures"])

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene


def material(name, spec):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    col = list(spec.get("color", [0.5, 0.5, 0.5]))[:3] + [1.0]
    b.inputs["Base Color"].default_value = col
    b.inputs["Roughness"].default_value = float(spec.get("rough", 0.5))
    b.inputs["Metallic"].default_value = float(spec.get("metal", 0.0))
    tex = spec.get("texture")
    if tex and (TEX / f"{tex}.png").exists():
        im = nt.nodes.new("ShaderNodeTexImage")
        im.image = bpy.data.images.load(str(TEX / f"{tex}.png"))
        if spec.get("blend"):
            mul = nt.nodes.new("ShaderNodeMath")
            mul.operation = "MULTIPLY"
            mul.inputs[1].default_value = float(spec.get("alpha", 1.0))
            nt.links.new(im.outputs["Alpha"], mul.inputs[0])
            nt.links.new(mul.outputs[0], b.inputs["Alpha"])
        else:
            nt.links.new(im.outputs["Color"], b.inputs["Base Color"])
    elif spec.get("shader") == "car_glass":
        # UV0 u codes of WorldCarGlass.shader: >= 6 clear lamp cover (life_cars.LENS_U), >= 2 privacy pane
        uv = nt.nodes.new("ShaderNodeUVMap")
        sep = nt.nodes.new("ShaderNodeSeparateXYZ")
        nt.links.new(uv.outputs["UV"], sep.inputs[0])
        ab = nt.nodes.new("ShaderNodeMath")
        ab.operation = "ABSOLUTE"
        nt.links.new(sep.outputs["X"], ab.inputs[0])
        gt = nt.nodes.new("ShaderNodeMath")
        gt.operation = "GREATER_THAN"
        gt.inputs[1].default_value = 6.0
        nt.links.new(ab.outputs[0], gt.inputs[0])
        mix = nt.nodes.new("ShaderNodeMapRange")
        mix.inputs["To Min"].default_value = float(spec.get("alpha", 1.0))
        mix.inputs["To Max"].default_value = float(spec.get("lens_alpha", 0.10))
        nt.links.new(gt.outputs[0], mix.inputs["Value"])
        nt.links.new(mix.outputs["Result"], b.inputs["Alpha"])
    elif spec.get("blend"):
        b.inputs["Alpha"].default_value = float(spec.get("alpha", 1.0))
    if spec.get("blend"):
        m.blend_method = "BLEND"
    return m


mats = {k: material(k, v) for k, v in doc["materials"].items()}
names = list(doc["protos"])
PITCH = 2.6
for k, name in enumerate(names):
    V, N, T, UV, MI = [], [], [], [], []
    used = []
    for p in doc["protos"][name]:
        off = len(V)
        V += p["V"]
        N += p["N"]
        UV += p["UV"]
        T += [[a + off, b + off, c + off] for a, b, c in p["T"]]
        MI += [len(used)] * len(p["T"])
        used.append(p["mat"])
    me = bpy.data.meshes.new(name)
    me.from_pydata(V, [], T)
    for mn in used:
        me.materials.append(mats[mn])
    me.polygons.foreach_set("material_index", MI)
    uvl = me.uv_layers.new(name="UV0")
    for li, l in enumerate(me.loops):
        uvl.data[li].uv = UV[l.vertex_index]
    me.polygons.foreach_set("use_smooth", [True] * len(me.polygons))
    me.normals_split_custom_set_from_vertices(N)
    me.update()
    ob = bpy.data.objects.new(name, me)
    ob.location = (k * PITCH, 0.0, 0.0)
    sc.collection.objects.link(ob)

# ground: concrete block paving grey, 60 x 60 m
bpy.ops.mesh.primitive_plane_add(size=120, location=(len(names) * PITCH / 2, 0, 0))
g = bpy.context.object
gm = bpy.data.materials.new("ground")
gm.use_nodes = True
gb = gm.node_tree.nodes["Principled BSDF"]
gb.inputs["Base Color"].default_value = (0.22, 0.215, 0.205, 1)
gb.inputs["Roughness"].default_value = 0.9
g.data.materials.append(gm)
# a wall behind the row (a hall facade: gives the paint something to mirror besides the sky)
bpy.ops.mesh.primitive_cube_add(size=1, location=(len(names) * PITCH / 2, -14, 4))
w = bpy.context.object
w.scale = (60, 1, 8)
wm = bpy.data.materials.new("wall")
wm.use_nodes = True
wm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.16, 0.17, 0.18, 1)
wm.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.7
w.data.materials.append(wm)

world = bpy.data.worlds.new("w")
sc.world = world
world.use_nodes = True
nt = world.node_tree
bg = nt.nodes["Background"]
if LIGHT == "overcast":
    # CIE-like overcast: brighter at the zenith, grey horizon
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    nt.links.new(tc.outputs["Generated"], sep.inputs[0])
    nt.links.new(sep.outputs["Z"], ramp.inputs[0])
    ramp.color_ramp.elements[0].position = 0.0
    ramp.color_ramp.elements[0].color = (0.30, 0.31, 0.33, 1)
    ramp.color_ramp.elements[1].position = 0.6
    ramp.color_ramp.elements[1].color = (0.95, 0.97, 1.0, 1)
    nt.links.new(ramp.outputs[0], bg.inputs["Color"])
    bg.inputs["Strength"].default_value = 1.1
else:
    sky = nt.nodes.new("ShaderNodeTexSky")
    sky.sky_type = "NISHITA"
    sky.sun_elevation = math.radians(12)
    sky.sun_rotation = math.radians(-125)
    sky.air_density = 1.5
    sky.dust_density = 2.0
    nt.links.new(sky.outputs[0], bg.inputs["Color"])
    bg.inputs["Strength"].default_value = 0.12

sc.render.engine = "CYCLES"
sc.cycles.samples = 48
sc.cycles.use_denoising = True
try:
    pr = bpy.context.preferences.addons["cycles"].preferences
    pr.compute_device_type = "OPTIX"
    pr.get_devices()
    for d in pr.devices:
        d.use = True
    sc.cycles.device = "GPU"
except Exception as e:      # CPU fallback
    print("GPU not used:", e)
sc.view_settings.view_transform = "Filmic"
sc.view_settings.look = "None"
sc.render.resolution_x, sc.render.resolution_y = 1920, 800
sc.render.image_settings.file_format = "JPEG"
sc.render.image_settings.quality = 92

n = len(names)
cx = (n - 1) * PITCH / 2


def cam(name, pos, look, lens=35, ortho=None, res=(1920, 800), clip=None):
    if CAMS and name not in CAMS:
        return
    cd = bpy.data.cameras.new(name)
    if ortho:
        cd.type = "ORTHO"
        cd.ortho_scale = ortho
    cd.lens = lens
    if clip:
        cd.clip_end = clip
    ob = bpy.data.objects.new(name, cd)
    ob.location = pos
    d = Vector(look) - Vector(pos)
    ob.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    sc.collection.objects.link(ob)
    sc.camera = ob
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.filepath = str(OUT / f"{name}_{LIGHT}.jpg")
    bpy.ops.render.render(write_still=True)


cam("row34f", (-4.5, 7.5, 1.6), (cx * 0.7, 0.3, 0.7), lens=32)
cam("row34r", (-4.5, -7.5, 1.6), (cx * 0.7, -0.3, 0.7), lens=32)
cam("cab", (cx + 3.0, 11.0, 2.5), (cx - 1.5, 0.0, 0.6), lens=28)
cam("close", (-3.3, 5.2, 1.55), (0.3, 0.6, 0.72), lens=35, res=(1600, 900))
cam("closer", (PITCH * 2 - 2.6, -5.6, 1.55), (PITCH * 2 + 0.2, -0.6, 0.72), lens=35, res=(1600, 900))
# side elevations: cars rotated so that each is seen from its right side, two rows
if not CAMS or "side" in CAMS:
    obs = [o for o in sc.objects if o.name in names]
    for k, o in enumerate(obs):
        o.location = ((k % 4) * 5.3, 30.0, 0.0)
        o.rotation_euler = (0, 0, math.radians(90))
        if k >= 4:
            o.location = ((k % 4) * 5.3, 60.0, 0.0)
    for row, yy in ((0, 30.0), (1, 60.0)):
        if n > row * 4:
            cam(f"side{row}", (8.0, yy - 20.0, 0.95), (8.0, yy, 0.95), ortho=21.6, res=(1920, 540), clip=26.0)
    for k, o in enumerate(obs):                       # front / rear elevations
        o.location = ((k % 4) * 2.6, 30.0 if k < 4 else 60.0, 0.0)
        o.rotation_euler = (0, 0, math.radians(180))
    cam("front", (3.9, 30.0 - 20.0, 0.95), (3.9, 30.0, 0.95), ortho=10.6, res=(1920, 540), clip=26.0)
    for o in obs:
        o.rotation_euler = (0, 0, 0)
    cam("rear", (3.9, 30.0 - 20.0, 0.95), (3.9, 30.0, 0.95), ortho=10.6, res=(1920, 540), clip=26.0)
