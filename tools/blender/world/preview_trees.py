"""Look development of the tree library (ADR 0187): line-up of prototypes at LOD0 or LOD1, EEVEE, overcast light.

    blender -b --factory-startup -P tools/blender/world/preview_trees.py -- --out <png> [--species spruce,pineyoung]
        [--lod 0|1] [--scale-to-h] [--res 1920x900]

Nothing is exported or baked. The red post is 1.75 m.
"""
import math
import sys
from pathlib import Path

import bpy

sys.path.insert(0, str(Path(__file__).resolve().parent))
argv = sys.argv[sys.argv.index("--") + 1:]
_keep = list(sys.argv)
sys.argv = sys.argv[:sys.argv.index("--") + 1]          # make_trees reads --out for its own purpose
import make_trees as MT                                   # noqa: E402
sys.argv = _keep


def arg(name, default):
    return argv[argv.index(name) + 1] if name in argv else default


out = arg("--out", "preview.png")
species = arg("--species", "spruce,pineyoung,birchyoung,shrub,floor,birch,pine").split(",")
lod = int(arg("--lod", "0"))
rx, ry = (int(v) for v in arg("--res", "1920x900").split("x"))
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
x = 0.0
hmax = 0.0
for sp in species:
    for v in range(MT.NVAR.get(sp, 3)):
        g, H = MT.grow(sp, v, lod)
        if lod == 1 and sp not in MT.NEW_SPECIES:
            g0, _ = MT.grow(sp, v, 0)
            g = MT.reuse_leaf_lod(g0, g, sum(map(ord, sp)) * 31 + v)
        ob = MT.to_object(f"{sp}_{v}", g)
        w = max(max(abs(c[0]), abs(c[1])) for c in ob.bound_box)
        x += w + 0.6
        ob.location = (x, 0, 0)
        x += w + 0.6
        hmax = max(hmax, H)
        print("[preview]", sp, v, "lod", lod, "H", round(H, 2), "tris", sum(len(p.vertices) - 2 for p in ob.data.polygons),
              "mats", len(ob.data.materials))
me = bpy.data.meshes.new("post")
me.from_pydata([(-0.6, 0, 0), (-0.45, 0, 0), (-0.45, 0, 1.75), (-0.6, 0, 1.75)], [], [(0, 1, 2, 3)])
m = bpy.data.materials.new("post")
m.diffuse_color = (0.8, 0.1, 0.1, 1)
me.materials.append(m)
sc.collection.objects.link(bpy.data.objects.new("post", me))
me = bpy.data.meshes.new("ground")
me.from_pydata([(-5, -30, 0), (x + 5, -30, 0), (x + 5, 30, 0), (-5, 30, 0)], [], [(0, 1, 2, 3)])
m = bpy.data.materials.new("ground")
m.use_nodes = True
m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.05, 0.06, 0.03, 1)
me.materials.append(m)
sc.collection.objects.link(bpy.data.objects.new("ground", me))
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
sc.collection.objects.link(cam)
cam.data.type = "ORTHO"
span = max(x + 2, (hmax + 1.5) * rx / ry)
cam.data.ortho_scale = span
cam.location = (x / 2, -80, span * ry / rx / 2 - 0.5)
cam.rotation_euler = (math.pi / 2, 0, 0)
sc.camera = cam
sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN"))
sun.data.energy = 2.0
sun.rotation_euler = (math.radians(50), 0, math.radians(35))
sc.collection.objects.link(sun)
sc.world = bpy.data.worlds.new("w")
sc.world.use_nodes = True
bg = sc.world.node_tree.nodes["Background"]
bg.inputs["Color"].default_value = (0.62, 0.68, 0.75, 1)
bg.inputs["Strength"].default_value = 1.2
sc.render.engine = "BLENDER_EEVEE_NEXT"
sc.render.resolution_x, sc.render.resolution_y = rx, ry
sc.view_settings.view_transform = "Standard"
sc.render.filepath = out
sc.render.image_settings.file_format = "PNG"
bpy.ops.render.render(write_still=True)
