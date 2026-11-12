"""Blender side of kit_preview.py: mesh from kit.npz, atlas material (alpha clip, foliage occlusion from COLOR_0),
custom normals as the PlotKit shader uses them, a few fixed cameras -> <dir>/view_<k>.png."""
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector

d = Path(sys.argv[sys.argv.index("--") + 1])
z = np.load(d / "kit.npz")
V, UV, T, C = z["V"], z["UV"], z["T"], z["C"]
bpy.ops.wm.read_factory_settings(use_empty=True)
me = bpy.data.meshes.new("kit")
me.from_pydata(V.tolist(), [], T.tolist())
me.update()
uv = me.uv_layers.new(name="UVMap")
loops = np.array([l.vertex_index for l in me.loops])
uv.data.foreach_set("uv", UV[loops].ravel())
# colour attribute: foliage -> occlusion grey, hard -> tint
fol = C[:, 3] > 0.5
nf = C[:, :3] * 2 - 1
occ = np.clip(np.linalg.norm(nf, axis=1) * 1.02, 0, 1)
tint = np.where(fol[:, None], occ[:, None].repeat(3, 1), C[:, :3] * 2)
col = me.color_attributes.new(name="Col", type="FLOAT_COLOR", domain="POINT")
col.data.foreach_set("color", np.column_stack([tint, np.ones(len(V))]).ravel())
# normals: foliage from COLOR_0, hard from the face
me.calc_loop_triangles() if hasattr(me, "calc_loop_triangles") else None
fn = np.zeros((len(V), 3))
tri = V[T]
nn = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
nn /= np.maximum(np.linalg.norm(nn, axis=1, keepdims=True), 1e-9)
for k in range(3):
    np.add.at(fn, T[:, k], nn)
fn /= np.maximum(np.linalg.norm(fn, axis=1, keepdims=True), 1e-9)
nrm = np.where(fol[:, None], nf / np.maximum(np.linalg.norm(nf, axis=1, keepdims=True), 1e-9), fn)
me.normals_split_custom_set_from_vertices(nrm.tolist())
ob = bpy.data.objects.new("kit", me)
sc = bpy.context.scene
sc.collection.objects.link(ob)
mat = bpy.data.materials.new("plot_kit")
mat.use_nodes = True
nt = mat.node_tree
bsdf = nt.nodes["Principled BSDF"]
tex = nt.nodes.new("ShaderNodeTexImage")
tex.image = bpy.data.images.load(str(d / "plot_kit.png"))
vc = nt.nodes.new("ShaderNodeVertexColor")
vc.layer_name = "Col"
mul = nt.nodes.new("ShaderNodeMixRGB")
mul.blend_type = "MULTIPLY"
mul.inputs[0].default_value = 1.0
nt.links.new(tex.outputs["Color"], mul.inputs[1])
nt.links.new(vc.outputs["Color"], mul.inputs[2])
nt.links.new(mul.outputs["Color"], bsdf.inputs["Base Color"])
nt.links.new(tex.outputs["Alpha"], bsdf.inputs["Alpha"])
bsdf.inputs["Roughness"].default_value = 0.9
if "Specular IOR Level" in bsdf.inputs:
    bsdf.inputs["Specular IOR Level"].default_value = 0.1
mat.blend_method = "CLIP" if hasattr(mat, "blend_method") else mat.blend_method
try:
    mat.alpha_threshold = 0.5
    mat.shadow_method = "CLIP"
except Exception:
    pass
mat.use_backface_culling = False
me.materials.append(mat)
# ground
bpy.ops.mesh.primitive_plane_add(size=300, location=(25, 0, -0.01))
g = bpy.context.object
gm = bpy.data.materials.new("ground")
gm.use_nodes = True
gm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.09, 0.13, 0.05, 1)
gm.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 1.0
g.data.materials.append(gm)
# light: overcast-ish sky + weak sun
w = bpy.data.worlds.new("w")
sc.world = w
w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.62, 0.66, 0.72, 1)
w.node_tree.nodes["Background"].inputs[1].default_value = 1.0
sun = bpy.data.lights.new("sun", "SUN")
sun.energy = 2.2
sun.angle = 0.3
so = bpy.data.objects.new("sun", sun)
so.rotation_euler = (0.9, 0.0, 0.6)
sc.collection.objects.link(so)
sc.render.engine = "BLENDER_EEVEE_NEXT"
sc.render.resolution_x, sc.render.resolution_y = 1600, 740
sc.view_settings.view_transform = "Standard"
cam = bpy.data.cameras.new("cam")
co = bpy.data.objects.new("cam", cam)
sc.collection.objects.link(co)
sc.camera = co
views = [((5.5, -6.5, 1.6), (5.5, 0.5, 1.2), 62), ((16.5, -6.0, 1.6), (17.0, 1.0, 1.0), 62), ((31.5, -7.5, 1.6), (31.5, 0.5, 1.2), 62),
         ((40.6, -2.6, 1.5), (42.0, 0.0, 1.0), 60), ((8.0, -2.0, 1.6), (6.0, 6.5, 2.2), 62), ((20.0, -2.5, 1.7), (17.5, 6.5, 2.6), 62),
         ((2.0, -2.2, 1.5), (9.0, 0.4, 1.2), 55), ((12.0, 12.0, 9.0), (10.0, 4.0, 1.0), 55)]
for k, (p, look, fov) in enumerate(views):
    co.location = p
    dirv = Vector(look) - Vector(p)
    co.rotation_euler = dirv.to_track_quat("-Z", "Y").to_euler()
    cam.sensor_fit = "HORIZONTAL"
    cam.angle = np.radians(fov)
    sc.render.filepath = str(d / f"view_{k}.png")
    bpy.ops.render.render(write_still=True)
