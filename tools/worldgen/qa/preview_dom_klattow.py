"""Blender preview of the Dom Klattow mesh (ADR 0305) - geometry check before the world build, not a game render.

  blender -b -P tools/worldgen/qa/preview_dom_klattow.py -- <parts.json> <materials root> <out dir> [layer]

parts.json: [{layer, mat, V, UV, T, color, set, tile}] exported from streetscape.knyszyn_dom_klattow_0305.build
(V relative to the house centre, metres; E = x, N = y). Materials: BaseColor of the set x 2 x colour (the engine's
modulation rule), no normal maps. Views: across the street (owner photo klattow-01), yard corner (klattow-05), street
corner (klattow-04).
"""
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:]
parts = json.load(open(argv[0]))
mat_root, out = Path(argv[1]), Path(argv[2])
layer = argv[3] if len(argv) > 3 else "buildings"
out.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene

for p in parts:
    if p["layer"] != layer:
        continue
    me = bpy.data.meshes.new(p["mat"])
    me.from_pydata([tuple(v) for v in p["V"]], [], [tuple(t) for t in p["T"]])
    uvl = me.uv_layers.new(name="UV0")
    tile = p["tile"] or [1.0, 1.0]
    for li, loop in enumerate(me.loops):
        u, v = p["UV"][loop.vertex_index]
        uvl.data[li].uv = (u / tile[0], v / tile[1])
    mt = bpy.data.materials.new(p["mat"])
    mt.use_nodes = True
    mt.use_backface_culling = True
    bsdf = mt.node_tree.nodes["Principled BSDF"]
    col = p["color"]
    bsdf.inputs["Roughness"].default_value = 0.1 if p["mat"] == "glass" else 0.85
    png = mat_root / str(p["set"]) / "High" / f"T_{p['set']}_BaseColor.png" if p["set"] else None
    if png and png.exists():
        tex = mt.node_tree.nodes.new("ShaderNodeTexImage")
        tex.image = bpy.data.images.load(str(png))
        mul = mt.node_tree.nodes.new("ShaderNodeMix")
        mul.data_type, mul.blend_type = "RGBA", "MULTIPLY"
        mul.inputs[0].default_value = 1.0
        mul.inputs[7].default_value = (2 * col[0], 2 * col[1], 2 * col[2], 1)
        mt.node_tree.links.new(tex.outputs["Color"], mul.inputs[6])
        mt.node_tree.links.new(mul.outputs[2], bsdf.inputs["Base Color"])
    else:
        bsdf.inputs["Base Color"].default_value = (*col, 1)
    me.materials.append(mt)
    ob = bpy.data.objects.new(p["mat"], me)
    sc.collection.objects.link(ob)

# ground, sun, sky
bpy.ops.mesh.primitive_plane_add(size=200, location=(0, 0, 0))
g = bpy.context.object
gm = bpy.data.materials.new("ground")
gm.use_nodes = True
gm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.09, 0.14, 0.05, 1)
g.data.materials.append(gm)
sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN"))
sun.data.energy = 4.0
sun.rotation_euler = (math.radians(50), 0, math.radians(200))      # from the south-south-west, as on photo 01
sc.collection.objects.link(sun)
w = bpy.data.worlds.new("w")
w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.35, 0.50, 0.85, 1)
w.node_tree.nodes["Background"].inputs[1].default_value = 1.0
sc.world = w
sc.render.engine = "CYCLES"
sc.cycles.samples = 48
sc.cycles.use_denoising = True
sc.render.resolution_x, sc.render.resolution_y = 1600, 900
sc.view_settings.view_transform = "Standard"

d = Vector((0.928, -0.3725, 0))            # along the street wall, west to east
n = Vector((-0.3725, -0.928, 0))           # out of the street wall
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
sc.collection.objects.link(cam)
sc.camera = cam
views = {
    "street": (n * 22.0 + d * 0.5 + Vector((0, 0, 1.6)), Vector((0, 0, 2.6)), 38),
    "yard_ne": (-n * 17.0 + d * 19.0 + Vector((0, 0, 1.6)), d * 2.0 + Vector((0, 0, 2.4)), 40),
    "street_se": (n * 12.0 + d * 22.0 + Vector((0, 0, 1.6)), d * 6.0 + Vector((0, 0, 2.6)), 40),
    "porch": (n * 8.0 + d * 1.5 + Vector((0, 0, 1.6)), n * 2.0 + Vector((0, 0, 1.9)), 40),
}
for name, (pos, tgt, fov) in views.items():
    cam.location = pos
    cam.rotation_euler = (tgt - pos).to_track_quat("-Z", "Y").to_euler()
    cam.data.angle = math.radians(fov * 16 / 9) if False else 2 * math.atan(math.tan(math.radians(fov) / 2) * 16 / 9)
    sc.render.filepath = str(out / f"preview_{layer}_{name}.png")
    bpy.ops.render.render(write_still=True)
print("PREVIEW_OK", out)
