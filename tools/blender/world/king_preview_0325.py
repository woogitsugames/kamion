"""Blender look-dev render of the Knyszyn king (ADR 0325), QA only - the shipped asset is the generator mesh.

  blender -b -P tools/blender/world/king_preview_0325.py -- <king.obj> <out_dir> [samples]

Cycles, Nishita sky + sun (clear noon, like the visual-QA `clear` preset), grey paving plane. Cameras at pedestrian eye
height matching the QA cameras king_front / king_34 / king_side / king_head / king_square of the region.
"""
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:]
obj_path, out_dir = Path(argv[0]).resolve(), Path(argv[1]).resolve()
samples = int(argv[2]) if len(argv) > 2 else 96
out_dir.mkdir(parents=True, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.obj_import(filepath=str(obj_path), forward_axis="Y", up_axis="Z")
mtl = {}
cur = None
for line in obj_path.with_suffix(".mtl").read_text().splitlines():
    p = line.split()
    if not p:
        continue
    if p[0] == "newmtl":
        cur = mtl.setdefault(p[1], {})
    elif p[0] in ("Kd",):
        cur["color"] = [float(x) for x in p[1:4]]
    elif p[0] in ("Pr", "Pm"):
        cur[p[0]] = float(p[1])
for m in bpy.data.materials:
    d = mtl.get(m.name.split(".")[0])
    if not d:
        continue
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*d["color"], 1.0)      # linear values of the manifest
    b.inputs["Roughness"].default_value = d.get("Pr", 0.9)
    b.inputs["Metallic"].default_value = d.get("Pm", 0.0)
for o in bpy.data.objects:
    if o.type == "MESH":
        for poly in o.data.polygons:
            poly.use_smooth = not o.name.startswith(("monument_granite", "steel_painted"))

bpy.ops.mesh.primitive_plane_add(size=80, location=(0, 0, 0))
g = bpy.data.materials.new("ground")
g.use_nodes = True
g.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.26, 0.255, 0.245, 1)
g.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.85
bpy.context.object.data.materials.append(g)

sc = bpy.context.scene
w = bpy.data.worlds.new("w")
sc.world = w
w.use_nodes = True
sky = w.node_tree.nodes.new("ShaderNodeTexSky")
sky.sky_type = "NISHITA"
sky.sun_elevation = math.radians(48)
sky.sun_rotation = math.radians(-35)        # sun in front of the figure, to its left
sky.sun_intensity = 1.0
w.node_tree.links.new(sky.outputs[0], w.node_tree.nodes["Background"].inputs[0])
w.node_tree.nodes["Background"].inputs[1].default_value = 0.12

sc.render.engine = "CYCLES"
sc.cycles.samples = samples
sc.cycles.use_denoising = True
sc.view_settings.view_transform = "Filmic"
sc.view_settings.exposure = -0.3
sc.render.resolution_x, sc.render.resolution_y = 760, 1000

cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
sc.collection.objects.link(cam)
sc.camera = cam


def shot(name, pos, target, vfov, res=(760, 1000)):
    cam.location = pos
    cam.rotation_euler = (Vector(target) - Vector(pos)).to_track_quat("-Z", "Y").to_euler()
    sc.render.resolution_x, sc.render.resolution_y = res
    cam.data.sensor_fit = "VERTICAL"
    cam.data.angle = math.radians(vfov)
    sc.render.filepath = str(out_dir / f"{name}.png")
    bpy.ops.render.render(write_still=True)


shot("front", (0.0, 6.0, 1.6), (0, 0, 2.45), 40)
shot("three_quarter", (3.15, 4.5, 1.6), (0, 0, 2.45), 40)
shot("side", (-6.0, 0.0, 1.6), (0, 0, 2.45), 40)
shot("back", (1.5, -6.0, 1.6), (0, 0, 2.45), 40)
shot("head", (0.0, 4.5, 1.7), (0, 0.03, 3.72), 16, (1000, 1000))
shot("head_34", (2.6, 3.7, 1.7), (0, 0.03, 3.72), 16, (1000, 1000))
shot("square", (2.0, 25.0, 2.5), (0, 0, 2.6), 30, (1280, 720))
