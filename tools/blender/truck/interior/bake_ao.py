"""Track A5 — bake one ambient-occlusion atlas for the whole cab interior (UV layer 'Bake').

    blender -b --factory-startup --python tools/blender/truck/interior/bake_ao.py -- [--res 2048] [--samples 128]

Builds the same scene as build_interior.py, then bakes Cycles AO (distance 0.35 m: cab-scale contact
shadows, not sky occlusion) for every interior mesh into a single shared atlas:
    art-source/truck/interior/textures/cab_ao_atlas.png   (8-bit grey, regenerable -> not committed)
    docs/reports/visual/truck-A5/ao_atlas_preview.jpg     (small preview for QA: overlaps/islands visible)
The atlas proves the 'Bake' UV layout is bake-ready (non-overlapping, uniform texel density) and is the
AO input the game material multiplies with the tiled detail maps (A6/A7).
"""
import argparse
import os
import sys
import time

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_interior as BI  # noqa: E402


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    p = argparse.ArgumentParser()
    p.add_argument("--res", type=int, default=2048)
    p.add_argument("--samples", type=int, default=64)
    p.add_argument("--distance", type=float, default=0.35)
    a = p.parse_args(argv)
    sys_argv = sys.argv
    sys.argv = [sys_argv[0], "--", "--out", os.path.join(BI.REPO, "artifacts")]
    ba = BI.parse_args()
    sys.argv = sys_argv
    BI.build(ba)
    BI.setup_render(ba)
    sc = bpy.context.scene
    sc.cycles.samples = a.samples
    if sc.world is None:
        sc.world = bpy.data.worlds.new("bake")
    sc.world.light_settings.distance = a.distance
    img = bpy.data.images.new("cab_ao_atlas", a.res, a.res, alpha=False, float_buffer=False, is_data=True)
    objs = [o for c, col in BI.COLLS.items() if c != "backdrop" for o in col.objects
            if o.type == "MESH" and not o.get("fixed_uv") and not o.get("decal")]
    mats = set()
    for o in objs:
        o.data.uv_layers.active = o.data.uv_layers["Bake"]
        for slot in o.material_slots:
            if slot.material:
                mats.add(slot.material)
    for m in mats:
        nt = m.node_tree
        n = nt.nodes.new("ShaderNodeTexImage")
        n.image = img
        n.name = "BAKE_TARGET"
        nt.nodes.active = n
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    sc.render.bake.margin = 4
    sc.render.bake.margin_type = "EXTEND"
    t = time.time()
    bpy.ops.object.bake(type="AO")
    print("BAKED", len(objs), "objects in", round(time.time() - t, 1), "s")
    out = os.path.join(BI.REPO, "art-source", "truck", "interior", "textures", "cab_ao_atlas.png")
    img.filepath_raw = out
    img.file_format = "PNG"
    img.save()
    # preview for the report
    prev = os.path.join(BI.REPO, "docs", "reports", "visual", "truck-A5", "ao_atlas_preview.jpg")
    pi = img.copy()
    pi.scale(800, 800)
    pi.filepath_raw = prev
    pi.file_format = "JPEG"
    sc.render.image_settings.quality = 80
    pi.save()
    print("WROTE", out, prev)
    # QA render: the baked atlas shown as flat emission through the 'Bake' UVs from two control cameras
    m = bpy.data.materials.new("ao_preview")
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    o_ = nt.nodes.new("ShaderNodeOutputMaterial")
    uvn = nt.nodes.new("ShaderNodeUVMap")
    uvn.uv_map = "Bake"
    tx = nt.nodes.new("ShaderNodeTexImage")
    tx.image = img
    em = nt.nodes.new("ShaderNodeEmission")
    nt.links.new(uvn.outputs["UV"], tx.inputs["Vector"])
    nt.links.new(tx.outputs["Color"], em.inputs["Color"])
    nt.links.new(em.outputs[0], o_.inputs["Surface"])
    for o in bpy.data.objects:
        if o.type == "MESH" and o not in objs:
            o.hide_render = True
    for o in objs:
        for slot in o.material_slots:
            slot.material = m
    sc.world.use_nodes = False
    sc.world.color = (0.0, 0.0, 0.0)
    sc.view_settings.exposure = 0.0
    sc.cycles.samples = 16
    sc.render.resolution_x, sc.render.resolution_y = 800, 450
    cams = BI.cameras()
    for cname in ("kierowca", "lezanka"):
        loc, tgt, fov = cams[cname]
        sc.camera = BI.look_cam(cname, loc, tgt, fov)
        sc.render.filepath = os.path.join(BI.REPO, "docs", "reports", "visual", "truck-A5", f"ao_check_{cname}.jpg")
        bpy.ops.render.render(write_still=True)
        print("WROTE", sc.render.filepath)


if __name__ == "__main__":
    main()
