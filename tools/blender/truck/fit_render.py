"""TRAKT A6 — visual fit check: exported exterior LOD0 + cab interior LOD0 together (as the A7 prefab nests them),
clay materials, the exterior glass clear. Renders the seams a player can see: the windscreen base / A-pillars from the
driver's eye, and the cab seen from outside through the windscreen and the door glass.

    blender -b --factory-startup --python tools/blender/truck/fit_render.py -- --out DIR [--samples 48]
"""
import math
import os
import sys

import bpy
from mathutils import Vector as V

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import check_fit as CF  # noqa: E402

REPO = CF.REPO
EYE = V((-0.55, 0.45, 2.50))
CAMS = {   # name: (location, target, lens mm) in the A2 frame
    "fit_oko_przod": (EYE, EYE + V((0.10, 1.0, -0.30)), 22),
    "fit_oko_slupek_lewy": (EYE, EYE + V((-0.75, 1.0, -0.10)), 24),
    "fit_oko_slupek_prawy": (EYE, EYE + V((1.0, 0.75, -0.18)), 24),
    "fit_zewn_szyba": (V((-2.6, 5.2, 2.75)), V((-0.2, 1.1, 2.35)), 40),
    "fit_zewn_drzwi": (V((-4.2, 0.9, 2.35)), V((-0.6, 0.2, 2.30)), 35),
}


def clay(name, rgb, rough=0.6):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*rgb, 1)
    b.inputs["Roughness"].default_value = rough
    return m


def glass():
    m = bpy.data.materials.new("fit_glass")
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    tr.inputs["Color"].default_value = (0.86, 0.92, 0.90, 1)
    gl = nt.nodes.new("ShaderNodeBsdfGlossy")
    gl.inputs["Roughness"].default_value = 0.02
    fr = nt.nodes.new("ShaderNodeLayerWeight")
    fr.inputs["Blend"].default_value = 0.10
    mx = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(fr.outputs["Fresnel"], mx.inputs[0])
    nt.links.new(tr.outputs[0], mx.inputs[1])
    nt.links.new(gl.outputs[0], mx.inputs[2])
    nt.links.new(mx.outputs[0], out.inputs[0])
    return m


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    out = os.path.abspath(CF.arg(argv, "--out", os.path.join(REPO, "docs", "reports", "visual", "truck-A6-exterior")))
    samples = int(CF.arg(argv, "--samples", "48"))
    ext = os.path.join(REPO, "art-source/truck/exterior/export/SM_TruckExterior_LOD0.fbx")
    itr = os.path.join(REPO, "art-source/truck/interior/export/SM_CabInterior_LOD0.fbx")
    bpy.ops.wm.read_factory_settings(use_empty=True)
    import json
    em = json.load(open(os.path.join(os.path.dirname(ext), "truck_exterior_manifest.json"), encoding="utf-8"))
    eo = CF.import_fbx(ext, em["origin"]["a2_frame"])
    io = CF.import_fbx(itr, CF.CAB_MOUNT_A2)
    m_ext, m_dark = clay("fit_ext", (0.80, 0.80, 0.78), 0.35), clay("fit_ext_dark", (0.06, 0.06, 0.06), 0.5)
    m_int, m_gl = clay("fit_int", (0.30, 0.28, 0.26), 0.7), glass()
    for o in eo:
        if o.type != "MESH":
            continue
        if o.name.startswith("COL_"):
            o.hide_render = True
            continue
        mats = [s.material.name if s.material else "" for s in o.material_slots]
        o.data.materials.clear()
        if o.name.startswith(("GLASS_", "MIRROR_")):
            o.data.materials.append(m_gl if o.name.startswith("GLASS_") else m_dark)
            continue
        # keep the paint / trim split readable: Paint -> light clay, everything else dark
        for mn in mats:
            o.data.materials.append(m_ext if "Paint" in mn else m_dark)
    for o in io:
        if o.type != "MESH":
            continue
        if o.name.startswith(CF.INT_SKIP):
            o.hide_render = True
            continue
        o.data.materials.clear()
        o.data.materials.append(m_int)
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
        pass
    sc.cycles.samples = samples
    sc.cycles.use_denoising = True
    sc.render.resolution_x, sc.render.resolution_y = 1280, 720
    sc.view_settings.view_transform = "AgX"
    w = bpy.data.worlds.new("fit_sky")
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs["Color"].default_value = (0.75, 0.80, 0.85, 1)
    w.node_tree.nodes["Background"].inputs["Strength"].default_value = 1.2
    sc.world = w
    bpy.ops.mesh.primitive_plane_add(size=60, location=(0, -2, 0))
    bpy.context.active_object.data.materials.append(clay("fit_ground", (0.25, 0.25, 0.25), 0.9))
    sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN"))
    sun.data.energy = 2.5
    sun.rotation_euler = (math.radians(50), 0, math.radians(-35))
    sc.collection.objects.link(sun)
    os.makedirs(out, exist_ok=True)
    for name, (loc, tgt, lens) in CAMS.items():
        cd = bpy.data.cameras.new(name)
        cd.lens = lens
        cd.clip_start = 0.02
        cam = bpy.data.objects.new(name, cd)
        sc.collection.objects.link(cam)
        cam.location = loc
        cam.rotation_euler = (V(tgt) - V(loc)).to_track_quat("-Z", "Y").to_euler()
        sc.camera = cam
        sc.render.filepath = os.path.join(out, name + ".jpg")
        sc.render.image_settings.file_format = "JPEG"
        bpy.ops.render.render(write_still=True)
        print("WROTE", sc.render.filepath)


if __name__ == "__main__":
    main()
