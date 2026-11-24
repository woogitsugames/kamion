"""Bake the cab interior as the windscreen sees it (ADR 0341, windscreen-s24).

Blender 4.2, background:
  blender -b --factory-startup --python tools/blender/truck/interior/bake_windscreen_reflection.py -- [--lod 1] [--res 1024]

What: an equirectangular panorama of the cab interior rendered from the driver's eye MIRRORED in the windscreen plane
(E'). For a planar mirror the ray reflected at any point P of the pane continues along the line E' -> P, so sampling this
panorama with the reflected direction R gives the exact reflection for the driver's eye and a small parallax error for
other heads / control cameras (centimetres of head motion against ~0.9 m to the dash). The windscreen is 1.5 deg from
vertical and nearly flat in the driver's half (crown R 10 m): one plane is enough.

Radiance in the panorama = relightable "albedo x sky visibility": every interior surface emits
    tint (vertex colour, linear) x AO (uv1 atlas of the LOD = the cab's sky visibility, baked by a6_export) x (1 + 1.5 wear)
- the albedo of the Kamion/Cab Interior shader contract (manifest shader_contract.formula, detail factor ~1 on average)
times its occlusion. Kamion/Truck Glass multiplies it at runtime by the current sky irradiance, the cab fill and the sun
on the dash (time of day, heading), so nothing time-dependent is baked. Glass, mirrors and displays are left out (glass:
not part of the image; mirrors: their RenderTextures are not available offline; displays: an LCD at daytime reflects as
a dark panel - an emitter at night is a later step). Back faces are transparent: from E' the camera sits in front of the
cab, the interior is seen from its inside through the (absent) windscreen.

Output: game/Assets/_Project/Rendering/Textures/Truck/T_CabWindscreenReflection.png (sRGB 8-bit, linear values encoded),
equirect, u = 0.5 - atan2(z, x) / 2pi, v = 0.5 + asin(y) / pi in the Unity CAB frame (x right, y up, z forward).
"""
import argparse
import math
import os
import sys

import bpy
from mathutils import Vector

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
EXPORT = os.path.join(REPO, "art-source", "truck", "interior", "export")
OUT = os.path.join(REPO, "game", "Assets", "_Project", "Rendering", "Textures", "Truck", "T_CabWindscreenReflection.png")
# Unity cab frame (relative to CAB_MOUNT_REF) -> A2/Blender: (x, z + 0.225, y + 1.15)
MOUNT_A2 = Vector((0.0, 0.225, 1.15))
EYE_CAB = Vector((-0.55, 1.35, 0.225))            # EYE_POINT (manifest named_objects, A2 (-0.55, 0.45, 2.5))
# Inner face of the windscreen (glass_interface.json surface grid: outer z 1.1448 at y 1.38 on the centre line, normal
# (0, 0.0262, 0.9997); inner face 6 mm behind along the normal).
PANE_P0_CAB = Vector((0.0, 1.38, 1.1448 - 0.006))
PANE_N_CAB = Vector((0.0, 0.0262, 0.99966)).normalized()
SKIP_PREFIX = ("CAB_Glass", "MIRROR_", "DISPLAY_")


def cab_to_a2(v):
    return Vector((v.x, v.z, v.y)) + MOUNT_A2


def mirrored_eye():
    d = (EYE_CAB - PANE_P0_CAB).dot(PANE_N_CAB)
    return EYE_CAB - 2.0 * d * PANE_N_CAB


def emission_material(name, ao_img):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    col = nt.nodes.new("ShaderNodeVertexColor")
    col.layer_name = "Col"
    uv_bake = nt.nodes.new("ShaderNodeUVMap")
    uv_bake.uv_map = "Bake"
    ao = nt.nodes.new("ShaderNodeTexImage")
    ao.image = ao_img
    ao.interpolation = "Linear"
    nt.links.new(uv_bake.outputs["UV"], ao.inputs["Vector"])
    uv_data = nt.nodes.new("ShaderNodeUVMap")
    uv_data.uv_map = "Data0"
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(uv_data.outputs["UV"], sep.inputs["Vector"])
    wear = nt.nodes.new("ShaderNodeMath")
    wear.operation = "MULTIPLY_ADD"
    wear.inputs[1].default_value = 1.5
    wear.inputs[2].default_value = 1.0
    nt.links.new(sep.outputs["X"], wear.inputs[0])
    m1 = nt.nodes.new("ShaderNodeMixRGB")
    m1.blend_type = "MULTIPLY"
    m1.inputs["Fac"].default_value = 1.0
    nt.links.new(col.outputs["Color"], m1.inputs[1])
    nt.links.new(ao.outputs["Color"], m1.inputs[2])
    m2 = nt.nodes.new("ShaderNodeVectorMath")
    m2.operation = "SCALE"
    nt.links.new(m1.outputs["Color"], m2.inputs[0])
    nt.links.new(wear.outputs["Value"], m2.inputs["Scale"])
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Strength"].default_value = 1.0
    nt.links.new(m2.outputs["Vector"], em.inputs["Color"])
    # back faces and everything in front of the pane transparent (the camera at E' is outside the cab; the shell
    # placeholder's outer front faces around the opening are not part of the reflected image)
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    mix = nt.nodes.new("ShaderNodeMixShader")
    rel = nt.nodes.new("ShaderNodeVectorMath")
    rel.operation = "SUBTRACT"
    nt.links.new(geo.outputs["Position"], rel.inputs[0])
    rel.inputs[1].default_value = tuple(cab_to_a2(PANE_P0_CAB))
    dist = nt.nodes.new("ShaderNodeVectorMath")
    dist.operation = "DOT_PRODUCT"
    nt.links.new(rel.outputs["Vector"], dist.inputs[0])
    n = PANE_N_CAB
    dist.inputs[1].default_value = (n.x, n.z, n.y)
    front = nt.nodes.new("ShaderNodeMath")
    front.operation = "GREATER_THAN"
    front.inputs[1].default_value = -0.012
    nt.links.new(dist.outputs["Value"], front.inputs[0])
    hide = nt.nodes.new("ShaderNodeMath")
    hide.operation = "MAXIMUM"
    nt.links.new(geo.outputs["Backfacing"], hide.inputs[0])
    nt.links.new(front.outputs["Value"], hide.inputs[1])
    nt.links.new(hide.outputs["Value"], mix.inputs["Fac"])
    nt.links.new(em.outputs["Emission"], mix.inputs[1])
    nt.links.new(tr.outputs["BSDF"], mix.inputs[2])
    nt.links.new(mix.outputs["Shader"], out.inputs["Surface"])
    return m


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--lod", type=int, default=1)
    ap.add_argument("--res", type=int, default=1024)
    ap.add_argument("--samples", type=int, default=32)
    ap.add_argument("--out", default=OUT)
    a = ap.parse_args(argv)

    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=os.path.join(EXPORT, f"SM_CabInterior_LOD{a.lod}.fbx"))
    ao_path = os.path.join(EXPORT, "textures", "High", f"T_Cab_AO_LOD{a.lod}.png")
    ao_img = bpy.data.images.load(ao_path)
    ao_img.colorspace_settings.name = "Non-Color"
    mat = emission_material("MI_Probe", ao_img)
    kept = 0
    for o in list(bpy.data.objects):
        if o.type != "MESH":
            continue
        if o.name.startswith(SKIP_PREFIX):
            bpy.data.objects.remove(o)
            continue
        o.data.materials.clear()
        o.data.materials.append(mat)
        for p in o.data.polygons:
            p.material_index = 0
        kept += 1

    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    try:
        prefs = bpy.context.preferences.addons["cycles"].preferences
        prefs.compute_device_type = "OPTIX"
        prefs.get_devices()
        for d in prefs.devices:
            d.use = d.type == "OPTIX"
        sc.cycles.device = "GPU"
    except Exception:
        sc.cycles.device = "CPU"
    sc.cycles.samples = a.samples
    sc.cycles.use_denoising = False
    sc.cycles.max_bounces = 0
    sc.cycles.transparent_max_bounces = 16
    sc.render.resolution_x, sc.render.resolution_y = a.res, a.res // 2
    sc.render.resolution_percentage = 100
    sc.view_settings.view_transform = "Standard"
    sc.view_settings.look = "None"
    sc.view_settings.exposure = 0.0
    sc.view_settings.gamma = 1.0
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGB"
    sc.render.image_settings.color_depth = "8"
    world = bpy.data.worlds.new("black")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.0
    sc.world = world

    cd = bpy.data.cameras.new("windscreen_probe")
    cd.type = "PANO"
    cd.panorama_type = "EQUIRECTANGULAR"
    cd.clip_start = 0.01
    cam = bpy.data.objects.new("windscreen_probe", cd)
    sc.collection.objects.link(cam)
    e = mirrored_eye()
    cam.location = cab_to_a2(e)
    # Equirect image centre = +X (A2) = +X (Unity cab), u = 0.5 - atan2(y_a2, x_a2) / 2pi = 0.5 - atan2(z_cab, x_cab) / 2pi
    cam.rotation_euler = (math.pi / 2, 0, -math.pi / 2)
    sc.camera = cam
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    sc.render.filepath = a.out
    bpy.ops.render.render(write_still=True)
    print(f"WINDSCREEN_PROBE: OK lod={a.lod} meshes={kept} eye'={tuple(round(v, 4) for v in e)} (cab) -> {a.out}")


if __name__ == "__main__":
    main()
