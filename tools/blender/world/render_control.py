"""Render the world control cameras of a region in Blender (visual QA, not final art).

    blender -b --factory-startup -P tools/blender/world/render_control.py -- \
        --region bialystok-industrial-c --out artifacts/visual/world-c [--cams id1,id2] [--res 1600x900]
        [--engine EEVEE|CYCLES] [--samples 64]

Imports the chunk GLBs listed in Data/Regions/<id>/generated/world_manifest.json (terrain LOD by
distance, road, bridge, markings; never the collision mesh), replaces the placeholder materials by
simple procedural PBR materials, adds extruded LoD1 buildings as context, a Nishita sky + sun, and
renders every camera of generated/control_cameras.json. Ortho cameras render an emission-coded road
layer with a transparent background for the orthophoto overlay (tools/worldgen/roads/qa_ortho.py).
"""

import argparse
import json
import math
import sys
from pathlib import Path

import bpy
import bmesh
from mathutils import Matrix, Vector

REPO = Path(__file__).resolve().parents[3]


def args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--region", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--cams", default="")
    ap.add_argument("--res", default="1600x900")
    ap.add_argument("--engine", default="EEVEE")
    ap.add_argument("--samples", type=int, default=64)
    ap.add_argument("--world-root", default="")
    return ap.parse_args(argv)


# ------------------------------------------------------------------------------------------- materials
def _nodes(mat):
    mat.use_nodes = True
    nt = mat.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    tc = nt.nodes.new("ShaderNodeTexCoord")
    return nt, bsdf, tc


def _noise(nt, tc, scale, detail=4.0, rough=0.55, coord="Object"):
    n = nt.nodes.new("ShaderNodeTexNoise")
    n.inputs["Scale"].default_value = scale
    n.inputs["Detail"].default_value = detail
    n.inputs["Roughness"].default_value = rough
    nt.links.new(tc.outputs[coord], n.inputs["Vector"])
    return n


def _ramp(nt, src, stops):
    r = nt.nodes.new("ShaderNodeValToRGB")
    r.color_ramp.elements.remove(r.color_ramp.elements[1])
    e0 = r.color_ramp.elements[0]
    e0.position, e0.color = stops[0][0], (*stops[0][1], 1)
    for pos, col in stops[1:]:
        e = r.color_ramp.elements.new(pos)
        e.color = (*col, 1)
    nt.links.new(src, r.inputs["Fac"])
    return r


def _bump(nt, bsdf, src, strength, dist=0.02):
    b = nt.nodes.new("ShaderNodeBump")
    b.inputs["Strength"].default_value = strength
    b.inputs["Distance"].default_value = dist
    nt.links.new(src, b.inputs["Height"])
    nt.links.new(b.outputs["Normal"], bsdf.inputs["Normal"])


def mat_asphalt(name, base=0.075):
    m = bpy.data.materials.new(name)
    nt, bsdf, tc = _nodes(m)
    big = _noise(nt, tc, 0.08, 3.0, 0.5)                   # patches, repairs (10-20 m)
    mid = _noise(nt, tc, 0.9, 6.0, 0.6)                    # stains
    fine = _noise(nt, tc, 60.0, 2.0, 0.5)                  # aggregate
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "FLOAT"
    mix.inputs["Factor"].default_value = 0.45
    nt.links.new(big.outputs["Fac"], mix.inputs["A"])
    nt.links.new(mid.outputs["Fac"], mix.inputs["B"])
    b = base
    col = _ramp(nt, mix.outputs["Result"], [(0.30, (b * 0.70, b * 0.70, b * 0.70)), (0.50, (b, b, b * 0.97)),
                                            (0.68, (b * 1.35, b * 1.33, b * 1.28))])
    nt.links.new(col.outputs["Color"], bsdf.inputs["Base Color"])
    rr = _ramp(nt, mid.outputs["Fac"], [(0.3, (0.82, 0.82, 0.82)), (0.7, (0.95, 0.95, 0.95))])
    nt.links.new(rr.outputs["Color"], bsdf.inputs["Roughness"])
    _bump(nt, bsdf, fine.outputs["Fac"], 0.25, 0.004)
    return m


def mat_concrete(name, base=0.38, scale=3.0):
    m = bpy.data.materials.new(name)
    nt, bsdf, tc = _nodes(m)
    n = _noise(nt, tc, scale, 6.0, 0.6)
    col = _ramp(nt, n.outputs["Fac"], [(0.35, (base * 0.82, base * 0.82, base * 0.80)), (0.65, (base, base, base * 0.96))])
    nt.links.new(col.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.85
    f = _noise(nt, tc, 80.0, 2.0)
    _bump(nt, bsdf, f.outputs["Fac"], 0.15, 0.003)
    return m


def mat_pavers(name, c1, c2, w=0.20, h=0.10):
    m = bpy.data.materials.new(name)
    nt, bsdf, tc = _nodes(m)
    br = nt.nodes.new("ShaderNodeTexBrick")
    br.inputs["Scale"].default_value = 1.0
    br.inputs["Brick Width"].default_value = w
    br.inputs["Row Height"].default_value = h
    br.inputs["Mortar Size"].default_value = 0.006
    br.inputs["Color1"].default_value = (*c1, 1)
    br.inputs["Color2"].default_value = (*c2, 1)
    br.inputs["Mortar"].default_value = (c1[0] * 0.6, c1[1] * 0.6, c1[2] * 0.6, 1)
    nt.links.new(tc.outputs["Object"], br.inputs["Vector"])
    dirt = _noise(nt, tc, 0.6, 4.0)
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.blend_type = "MULTIPLY"
    mix.inputs["Factor"].default_value = 0.35
    nt.links.new(br.outputs["Color"], mix.inputs["A"])
    nt.links.new(dirt.outputs["Color"], mix.inputs["B"])
    nt.links.new(mix.outputs["Result"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.88
    _bump(nt, bsdf, br.outputs["Fac"], 0.3, 0.004)
    return m


def mat_grass(name):
    m = bpy.data.materials.new(name)
    nt, bsdf, tc = _nodes(m)
    big = _noise(nt, tc, 0.05, 4.0, 0.6)
    mid = _noise(nt, tc, 0.7, 5.0, 0.6)
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "FLOAT"
    mix.inputs["Factor"].default_value = 0.4
    nt.links.new(big.outputs["Fac"], mix.inputs["A"])
    nt.links.new(mid.outputs["Fac"], mix.inputs["B"])
    col = _ramp(nt, mix.outputs["Result"], [(0.32, (0.050, 0.075, 0.025)), (0.5, (0.085, 0.105, 0.040)),
                                            (0.66, (0.140, 0.130, 0.065))])
    nt.links.new(col.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.96
    f = _noise(nt, tc, 25.0, 3.0)
    _bump(nt, bsdf, f.outputs["Fac"], 0.5, 0.02)
    return m


def mat_paint(name):
    m = bpy.data.materials.new(name)
    nt, bsdf, tc = _nodes(m)
    wear = _noise(nt, tc, 2.5, 6.0, 0.7)
    col = _ramp(nt, wear.outputs["Fac"], [(0.38, (0.30, 0.30, 0.29)), (0.55, (0.62, 0.62, 0.60)), (0.7, (0.70, 0.70, 0.67))])
    nt.links.new(col.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.6
    return m


def mat_flat(name, col, rough=0.85, metal=0.0):
    m = bpy.data.materials.new(name)
    nt, bsdf, tc = _nodes(m)
    bsdf.inputs["Base Color"].default_value = (*col, 1)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metal
    return m


def mat_emit(name, col):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*col, 1)
    em.inputs["Strength"].default_value = 1.0
    nt.links.new(em.outputs["Emission"], out.inputs["Surface"])
    return m


def build_materials():
    return {
        "road_asphalt": mat_asphalt("road_asphalt"),
        "road_concrete": mat_concrete("road_concrete", 0.30, 1.5),
        "road_paving": mat_pavers("road_paving", (0.24, 0.22, 0.20), (0.27, 0.25, 0.22)),
        "road_sett": mat_pavers("road_sett", (0.20, 0.18, 0.17), (0.23, 0.21, 0.19), 0.12, 0.12),
        "road_gravel": mat_concrete("road_gravel", 0.26, 8.0),
        "curb_concrete": mat_concrete("curb_concrete", 0.36, 4.0),
        "sidewalk_paving": mat_pavers("sidewalk_paving", (0.30, 0.29, 0.27), (0.33, 0.32, 0.30)),
        "apron_sett": mat_pavers("apron_sett", (0.26, 0.21, 0.18), (0.30, 0.25, 0.21), 0.12, 0.12),
        "bridge_concrete": mat_concrete("bridge_concrete", 0.27, 1.0),
        "barrier_steel": mat_flat("barrier_steel", (0.55, 0.56, 0.57), 0.4, 0.85),
        "verge_grass": mat_grass("verge_grass"),
        "shoulder_gravel": mat_concrete("shoulder_gravel", 0.26, 8.0),
        "terrain_grass": mat_grass("terrain_grass"),
        "marking_white": mat_paint("marking_white"),
    }


EMIT = {"road_asphalt": (0.06, 0.06, 0.06), "curb_concrete": (1.0, 1.0, 1.0), "sidewalk_paving": (1.0, 0.55, 0.15),
        "apron_sett": (1.0, 0.3, 0.1), "marking_white": (1.0, 1.0, 0.0), "bridge_concrete": (0.35, 0.45, 1.0),
        "barrier_steel": (0.2, 0.3, 1.0), "road_paving": (0.6, 0.35, 0.2), "road_concrete": (0.3, 0.3, 0.3),
        "road_sett": (0.5, 0.3, 0.2), "road_gravel": (0.5, 0.45, 0.3)}


# ------------------------------------------------------------------------------------------- scene
def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def import_chunk(path, keep, root):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(path), merge_vertices=False)
    new = [o for o in bpy.data.objects if o not in before]
    for o in new:
        if o.type != "MESH" or o.name.split(".")[0] not in keep:
            bpy.data.objects.remove(o, do_unlink=True)
            continue
        o.parent = root
    return [o for o in bpy.data.objects if o not in before]


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


def add_buildings(path, center, radius, root):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    # muted facade albedos (sheet metal / plaster / brick), WORKING_VALUE for context only
    palette = {"magazyn": [(0.36, 0.37, 0.38), (0.30, 0.32, 0.34), (0.40, 0.39, 0.37)],
               "produkcyjny": [(0.33, 0.33, 0.33), (0.27, 0.29, 0.31), (0.38, 0.36, 0.33)],
               None: [(0.42, 0.39, 0.34), (0.36, 0.35, 0.33), (0.45, 0.41, 0.35), (0.34, 0.25, 0.21)]}
    mats = {}
    bm = None
    count = 0
    for b in data["buildings"]:
        ring = b["ring"]
        cx = sum(p[0] for p in ring) / len(ring)
        cy = sum(p[1] for p in ring) / len(ring)
        if math.hypot(cx - center[0], cy - center[1]) > radius or len(ring) < 3:
            continue
        pal = palette.get(b.get("function"), palette[None])
        k = sum(ord(ch) for ch in b["id"]) % len(pal)      # deterministic variation
        col = pal[k]
        key = (b.get("function") in ("magazyn", "produkcyjny"), k)
        if key not in mats:
            mats[key] = mat_flat(f"bld_{len(mats)}", col, 0.85)
        me = bpy.data.meshes.new("bld")
        bm = bmesh.new()
        z0, z1 = b["z0"] - 1.0, b["z0"] + b["h"]
        bot = [bm.verts.new((x, y, z0)) for x, y in ring]
        top = [bm.verts.new((x, y, z1)) for x, y in ring]
        n = len(ring)
        area = sum(ring[i][0] * ring[(i + 1) % n][1] - ring[(i + 1) % n][0] * ring[i][1] for i in range(n))
        order = range(n) if area > 0 else range(n - 1, -1, -1)
        o_ = list(order)
        try:
            bm.faces.new([top[i] for i in o_])
        except ValueError:
            pass
        for a in range(n):
            i, j = o_[a], o_[(a + 1) % n]
            try:
                bm.faces.new([bot[i], bot[j], top[j], top[i]])
            except ValueError:
                pass
        bm.to_mesh(me)
        bm.free()
        ob = bpy.data.objects.new("bld", me)
        ob.data.materials.append(mats[key])
        bpy.context.scene.collection.objects.link(ob)
        count += 1
    return count


def _leaf_mat(name, col):
    m = bpy.data.materials.new(name)
    nt, bsdf, tc = _nodes(m)
    n = _noise(nt, tc, 0.35, 3.0, 0.6)
    ramp = _ramp(nt, n.outputs["Fac"], [(0.35, tuple(c * 0.75 for c in col)), (0.65, tuple(c * 1.25 for c in col))])
    nt.links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.92
    f = _noise(nt, tc, 6.0, 4.0)
    _bump(nt, bsdf, f.outputs["Fac"], 0.6, 0.2)
    return m


def _tree_parts(kind):
    """Low-poly context vegetation, unit height (scaled by the per-point height h):
    pine = thin trunk + irregular crown in the top third; shrub = irregular blob. One material per part."""
    import random
    rnd = random.Random(7 if kind == 0 else 11)
    parts = []

    def mesh(name, build, mat):
        me = bpy.data.meshes.new(name)
        bm = bmesh.new()
        build(bm)
        bm.to_mesh(me)
        bm.free()
        me.materials.append(mat)
        for poly in me.polygons:
            poly.use_smooth = False
        parts.append(bpy.data.objects.new(name, me))

    if kind == 0:
        mesh("tpl_trunk", lambda bm: bmesh.ops.create_cone(
            bm, cap_ends=True, segments=6, radius1=0.014, radius2=0.008, depth=0.72,
            matrix=Matrix.Translation((0, 0, 0.36))), mat_flat("bark", (0.11, 0.075, 0.05), 0.9))

        def crown(bm):
            r = bmesh.ops.create_icosphere(bm, subdivisions=1, radius=1.0,
                                           matrix=Matrix.Diagonal((0.15, 0.13, 0.17, 1)))
            for v in r["verts"]:
                v.co.x += rnd.uniform(-0.035, 0.035)
                v.co.y += rnd.uniform(-0.035, 0.035)
                v.co.z = v.co.z * rnd.uniform(0.7, 1.1) + 0.80
        mesh("tpl_crown", crown, _leaf_mat("pine_leaf", (0.032, 0.048, 0.022)))
    else:
        def blob(bm):
            r = bmesh.ops.create_icosphere(bm, subdivisions=2, radius=0.5)
            for v in r["verts"]:
                v.co *= rnd.uniform(0.8, 1.15)
                v.co.z = v.co.z * 0.8 + 0.42
        mesh("tpl_shrub", blob, _leaf_mat("shrub_leaf", (0.045, 0.062, 0.026)))
    return parts


def add_trees(path, center, radius):
    p = Path(path)
    if not p.exists():
        return 0
    data = json.loads(p.read_text(encoding="utf-8"))
    sel = [t for t in data["trees"] if math.hypot(t[0] - center[0], t[1] - center[1]) < radius]
    if not sel:
        return 0
    for kind in (0, 1):
        pts = [t for t in sel if t[4] == kind]
        if not pts:
            continue
        for part in _tree_parts(kind):
            me = bpy.data.meshes.new(f"pts_{part.name}")
            me.from_pydata([(t[0], t[1], t[2] - 0.2) for t in pts], [], [])
            attr = me.attributes.new("h", "FLOAT", "POINT")
            attr.data.foreach_set("value", [t[3] for t in pts])
            ob = bpy.data.objects.new(f"scatter_{part.name}", me)
            bpy.context.scene.collection.objects.link(ob)
            ng = bpy.data.node_groups.new(f"scatter_{part.name}", "GeometryNodeTree")
            ng.interface.new_socket(name="Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
            ng.interface.new_socket(name="Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
            n = ng.nodes
            gi, go = n.new("NodeGroupInput"), n.new("NodeGroupOutput")
            inst = n.new("GeometryNodeInstanceOnPoints")
            info = n.new("GeometryNodeObjectInfo")
            info.inputs["Object"].default_value = part
            h = n.new("GeometryNodeInputNamedAttribute")
            h.data_type = "FLOAT"
            h.inputs["Name"].default_value = "h"
            rot = n.new("FunctionNodeRandomValue")
            rot.data_type = "FLOAT_VECTOR"
            rot.inputs["Min"].default_value = (0, 0, 0)
            rot.inputs["Max"].default_value = (0.06, 0.06, 6.283)
            rot.inputs["Seed"].default_value = 3 + kind      # same seed for trunk and crown of a tree
            real = n.new("GeometryNodeRealizeInstances")
            L = ng.links
            L.new(gi.outputs["Geometry"], inst.inputs["Points"])
            L.new(info.outputs["Geometry"], inst.inputs["Instance"])
            L.new(h.outputs["Attribute"], inst.inputs["Scale"])
            L.new(rot.outputs["Value"], inst.inputs["Rotation"])
            L.new(inst.outputs["Instances"], real.inputs["Geometry"])
            L.new(real.outputs["Geometry"], go.inputs["Geometry"])
            mod = ob.modifiers.new("scatter", "NODES")
            mod.node_group = ng
            ob.data.materials.append(part.data.materials[0])
    return len(sel)


def setup_world(scene, engine, samples, res):
    w, h = (int(x) for x in res.split("x"))
    scene.render.resolution_x, scene.render.resolution_y = w, h
    scene.render.resolution_percentage = 100
    if engine == "CYCLES":
        scene.render.engine = "CYCLES"
        scene.cycles.samples = samples
        scene.cycles.use_denoising = True
        scene.cycles.device = "CPU"
    else:
        scene.render.engine = "BLENDER_EEVEE_NEXT"
        scene.eevee.taa_render_samples = samples
        try:
            scene.eevee.use_shadows = True
            scene.eevee.shadow_ray_count = 2
            scene.eevee.use_raytracing = False
            scene.eevee.use_gtao = True
            scene.eevee.gtao_distance = 2.0
        except AttributeError:
            pass
    scene.view_settings.view_transform = "AgX"
    looks = [i.identifier for i in scene.view_settings.bl_rna.properties["look"].enum_items]
    for lk in ("AgX - Medium High Contrast", "AgX - Base Contrast"):
        if lk in looks:
            scene.view_settings.look = lk
            break
    scene.view_settings.exposure = -0.9
    world = bpy.data.worlds.new("sky")
    scene.world = world
    world.use_nodes = True
    nt = world.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    sky = nt.nodes.new("ShaderNodeTexSky")
    sky.sky_type = "NISHITA"
    sky.sun_elevation = math.radians(32)
    sky.sun_rotation = math.radians(215)
    sky.altitude = 150
    sky.air_density = 1.0
    sky.dust_density = 1.0
    bg = nt.nodes.new("ShaderNodeBackground")
    bg.inputs["Strength"].default_value = 0.30
    out = nt.nodes.new("ShaderNodeOutputWorld")
    nt.links.new(sky.outputs["Color"], bg.inputs["Color"])
    nt.links.new(bg.outputs["Background"], out.inputs["Surface"])
    sun = bpy.data.lights.new("sun", "SUN")
    sun.energy = 4.5
    sun.angle = math.radians(0.6)
    sun.color = (1.0, 0.96, 0.9)
    so = bpy.data.objects.new("sun", sun)
    scene.collection.objects.link(so)
    # sun in the SW (azimuth 215 deg from north, elevation 32 deg): light travels toward NE.
    # Unrotated light points along -Z; X tilt sends it toward +Y (north), Z turns it by -35 deg (to NE).
    so.rotation_euler = (math.radians(90 - 32), 0, math.radians(-35))
    scene.render.image_settings.file_format = "JPEG"
    scene.render.image_settings.quality = 86


def look_at(obj, target):
    d = Vector(target) - obj.location
    obj.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()


def main():
    a = args()
    cams = json.loads((REPO / f"Data/Regions/{a.region}/generated/control_cameras.json").read_text(encoding="utf-8"))
    man = json.loads((REPO / f"Data/Regions/{a.region}/generated/world_manifest.json").read_text(encoding="utf-8"))
    wanted = [c for c in cams["cameras"] if not a.cams or c["id"] in a.cams.split(",")]
    out = Path(a.out)
    if not out.is_absolute():
        out = REPO / out
    out.mkdir(parents=True, exist_ok=True)
    world_root = Path(a.world_root) if a.world_root else None
    for cam in wanted:
        reset()
        scene = bpy.context.scene
        ortho = cam["type"] == "ortho"
        setup_world(scene, a.engine, a.samples, "1600x1600" if ortho else a.res)
        root = bpy.data.objects.new("world_root", None)
        root.rotation_euler = (0, 0, math.pi)      # Blender import (-E, -N, U) -> (E, N, U)
        scene.collection.objects.link(root)
        if ortho:
            ctr = cam["center"]
            tgt = (ctr[0], ctr[1], 0)
            radius = cam["size_m"] * 0.8
        else:
            tgt = cam["look_at"]
            radius = 900.0
        pos = cam.get("pos", [tgt[0], tgt[1], 0])
        objs = []
        for ch in man["chunks"]:
            b = ch["bounds_local_m"]
            cx, cy = (b["e_min"] + b["e_max"]) / 2, (b["n_min"] + b["n_max"]) / 2
            dist = min(math.hypot(cx - pos[0], cy - pos[1]), math.hypot(cx - tgt[0], cy - tgt[1]))
            if dist > radius + 190:
                continue
            if ortho:
                keep = {"road", "bridge", "markings"}
            else:
                lod = 0 if dist < 330 else (1 if dist < 600 else 2)
                keep = {f"terrain_lod{lod}", "road", "bridge", "markings"}
            path = (world_root / Path(ch["file"]).name) if world_root else REPO / ch["file"]
            objs += import_chunk(path, keep, root)
        if ortho:
            assign_materials(objs, None, emit=True)
            scene.render.film_transparent = True
            scene.render.image_settings.file_format = "PNG"
            scene.render.image_settings.color_mode = "RGBA"
            scene.view_settings.view_transform = "Standard"
            scene.view_settings.exposure = 0
        else:
            assign_materials(objs, build_materials())
            n = add_buildings(REPO / f"Data/raw/derived/{a.region}/world/preview_buildings.json",
                              tgt, 800.0, root)
            nt_ = add_trees(REPO / f"Data/raw/derived/{a.region}/world/preview_trees.json", tgt, 900.0)
            print(f"[render] {cam['id']}: {len(objs)} objects, {n} buildings, {nt_} trees")
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
        else:
            cd.angle = math.radians(cam["fov_deg"])
            co.location = cam["pos"]
            look_at(co, cam["look_at"])
        scene.render.filepath = str(out / (cam["id"] + (".png" if ortho else ".jpg")))
        bpy.ops.render.render(write_still=True)
        print(f"[render] wrote {scene.render.filepath}")


main()
