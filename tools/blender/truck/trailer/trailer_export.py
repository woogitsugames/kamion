"""Curtainsider semi-trailer 13.6 m tridem (fictional, no brand): game-ready export.

    blender -b --factory-startup --python tools/blender/truck/trailer/trailer_export.py -- \
        [--out ABS_DIR] [--renders ABS_DIR] [--no-renders] [--bake-scale 1.0] [--ao-samples 128] [--samples 96]

Pipeline (all from code, same contract as the TRAKT exterior A6, tools/blender/truck/exterior/a6_export.py):
 1. trailer_build.build(): source pieces with authoring materials + dense curtain sheets (normal-map source);
 2. game pieces: modifiers applied, transforms baked, 5 slots (Paint, Curtain, Trim, Metal, Lights); uv0 'Atlas',
    uv1 'Decal' (unused, 0.002), uv2 'Data' (x = light group, y = emissive mask), colour 'Col' (white);
 3. one UV atlas per slot (smart project + texel priority + pack); the 6 wheels share the UVs of wheel 1L;
 4. bake from the authoring materials: albedo, roughness / dirt / metallic, tint mask, AO; tangent normals of the
    curtain from the dense sheets (straps, buckle fans, roller scallops, wrinkles);
 5. textures per tier (High / Medium / Low) + stock-URP-Lit fallback (BaseMap / MaskMap per livery);
 6. LOD0-2 (drop lists + area-weighted collapse), parts with pivots in their axes, flat FBX hierarchy (rig in the
    manifest, rig_parent), sockets, convex COL_* hulls; FBX per LOD; trailer_manifest.json with physics_crosscheck;
 7. control renders: overcast + low sun, solo and coupled to the TRAKT tractor (art-source/truck/exterior/export).
Frame: Blender (x, y, z) -> Unity (x, z, y); origin = ground below the kingpin = physics trailer frame.
"""
import argparse
import json
import math
import os
import re
import sys
import tempfile
import time

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "exterior")))
import trailer_build as T  # noqa: E402
import geom as G  # noqa: E402
import materials as M  # noqa: E402
import scene as S  # noqa: E402
import a6_export as A  # noqa: E402  (generic helpers only: select, copy, bake io, decimation, FBX conventions)

V = Vector
REPO = G.REPO
PHYS = os.path.join(REPO, "game", "Assets", "_Project", "Vehicle", "Physics", "Definitions", "Data")
SLOT_MAT = {"Paint": "MI_Trl_Paint", "Curtain": "MI_Trl_Curtain", "Trim": "MI_Trl_Trim", "Metal": "MI_Trl_Metal",
            "Lights": "MI_Trl_Lights"}
BAKED = tuple(SLOT_MAT)
TINTED = ("Paint", "Curtain")
ATLAS_RES = {"Paint": 2048, "Curtain": 4096, "Trim": 4096, "Metal": 2048, "Lights": 1024}   # High tier
TIERS = {"High": 1, "Medium": 2, "Low": 4}
TRI_LIMIT = {0: 90000, 1: 25000, 2: 8000}
TRI_TARGET = {0: 89000, 1: 24500, 2: 7850}
MAT_SLOT = {"trl_paint": "Paint",
            "curtain_pvc": "Curtain", "roof_tarp": "Curtain", "strap": "Curtain",
            "galv": "Metal", "alu_extr": "Metal", "steel_wheel": "Metal", "steel": "Metal", "satin_alu": "Metal",
            "chrome": "Metal", "hub_cast": "Metal",
            "lens_red_o": "Lights", "lens_amber_o": "Lights", "lens_white_o": "Lights", "lamp_body": "Lights"}
PRIORITY = {"roof_tarp": 0.30, "gap": 0.5, "trl_chassis": 0.7, "grease": 0.6, "flap_rubber": 0.8, "interior": 0.12,
            "plywood": 0.25}
# same ids as the TRAKT tractor (one light controller for the combination) + PLATE
LIGHT_GROUPS = list(A.LIGHT_GROUPS) + ["PLATE"]
LIGHT_COLOUR = dict(A.LIGHT_COLOUR, PLATE=(1.0, 0.98, 0.95))
LIVERIES = {   # _PaintColor / _CurtainColor multiply the baked albedo (front wall 0.80, curtain 0.80, straps 0.52)
    "szary": {"_PaintColor": [0.98, 0.98, 0.97], "_PaintRoughness": 0.36, "_CurtainColor": [0.40, 0.42, 0.44],
              "label": "firanka szara, ściany białe"},
    "granat": {"_PaintColor": [0.98, 0.98, 0.97], "_PaintRoughness": 0.36, "_CurtainColor": [0.040, 0.068, 0.15],
               "label": "firanka granatowa, ściany białe"},
}
DUST = A.DUST
URP_LIT_DIRT = 0.5
PARTS_MOVING = ("WHEEL_", "DOOR_", "LEG_", "CRANK", "MUDFLAP_")
LOD1_DROP = ("_nutind", "_nutwasher", "_stud", "hinge_bolt", "lash_", "toolbox_latch", "socket_lid", "palm_lip", "hanger_bush", "damper_rod",
             "ubolt", "keeper_", "lockguide", "lockcatch", "buckle_lever", "buckle_hook", "doc_tube_clamp",
             "air_tank_strap", "mudflap_rib", "leg_foot_lug", "leg_foot_pin", "hubcap_plug", "kingpin_grease",
             "door_groove", "sideguard_groove", "top_rail_groove", "rear_led_", "brake_hose", "ebs_hose",
             "crank_grip_rod", "mudguard_stay", "side_marker_brk", "tension_lever", "stalk_base", "lockhandle",
             "hinge_barrel", "pallet_latch", "pallet_hinge", "spare_nut", "chock_holder_arm")
LOD2_DROP = LOD1_DROP + ("_nut", "lockcam", "hinge_strap", "buckle_", "strap_", "caliper", "brake_chamber",
                         "damper", "bellow", "hanger", "trailing_arm", "crossmember", "outrigger", "air_tank", "ebs_",
                         "air_line", "doc_tube", "coupling", "palm_", "socket_", "kingpin", "mudguard_lip",
                         "leg_xbrace", "leg_brace", "cross_shaft", "crank_shaft", "crank_holder", "leg_collar",
                         "dock_buffer", "lamp_panel_side", "plate_lamp", "tension_", "curtain_rear_wrap",
                         "curtain_front_strip", "stalk_", "side_reflector", "sideguard_post", "lockbar",
                         "door_frame", "beam_flange", "rup_brace", "tri_reflector", "contour_rear", "toolbox",
                         "leg_gearbox", "front_lamp", "rear_marker", "door_centre_seal", "rear_sill_face",
                         "coupler_plate", "front_cross", "_hubcap", "crank_hub", "crank_grip", "pallet_rib",
                         "pallet_strap", "spare_hanger", "spare_clamp", "spare_rod", "spare_carrier", "spare_disc",
                         "chock")


def a2u(v):
    return [round(float(v[0]), 5), round(float(v[2]), 5), round(float(v[1]), 5)]


def rel(p):
    return os.path.relpath(p, REPO).replace("\\", "/")


def tris_of(o):
    return A.tris_of(o)


def copy_piece(o, name, coll):
    c = o.copy()
    c.data = o.data.copy()
    c.name = name
    coll.objects.link(c)
    return c


# ---------------------------------------------------------------- game pieces
def slot_of(mname):
    return MAT_SLOT.get(mname, "Trim")


def light_group(oname):
    n = oname
    if not n.startswith(("rear_lens_", "rear_led_", "side_marker_lens", "front_lamp_lens", "stalk_lens",
                         "rear_marker_lens", "plate_lamp_lens")):
        return "NONE"
    sd = "L" if n.endswith(("_L", "_-1")) or "_L_" in n or "_-1_" in n else "R"
    if "_ind_" in n:
        return "IND_" + sd
    if "_tail_" in n or "_stop_" in n:
        return "TAIL_BRAKE"
    if "_rev_" in n:
        return "REVERSE"
    if "_fog_" in n:
        return "FOG"
    if n.startswith("side_marker_lens"):
        return "MARKER_SIDE"
    if n.startswith(("front_lamp_lens", "stalk_lens_w")):
        return "MARKER_FRONT"
    if n.startswith(("stalk_lens_r", "rear_marker_lens")):
        return "MARKER_REAR"
    if n.startswith("plate_lamp_lens"):
        return "PLATE"
    return "NONE"


def game_materials():
    out = {}
    for slot, name in SLOT_MAT.items():
        m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
        m.use_nodes = True
        m["slot"] = slot
        out[slot] = m
    return out


def to_game_piece(o, gm):
    me = o.data
    names = [m.name if m else "" for m in me.materials]
    for uvl in list(me.uv_layers):
        me.uv_layers.remove(uvl)
    for nm in ("Atlas", "Decal", "Data"):
        me.uv_layers.new(name=nm)
    col = me.color_attributes.new("Col", "BYTE_COLOR", "CORNER")
    prio = me.attributes.new("prio", "FLOAT", "FACE")
    grp = light_group(o.name)
    gi = LIGHT_GROUPS.index(grp)
    face_slot = []
    for p in me.polygons:
        mn = names[p.material_index] if p.material_index < len(names) else ""
        sl = slot_of(mn)
        face_slot.append(sl)
        pr = PRIORITY.get(mn, 1.0)
        if o.get("group") == "frame" and p.normal.z < -0.6:
            pr *= 0.6
        prio.data[p.index].value = pr
        emit = gi if sl == "Lights" else 0
        for li in p.loop_indices:
            me.uv_layers["Data"].data[li].uv = (emit, 1.0 if emit else 0.0)
            me.uv_layers["Decal"].data[li].uv = (0.002, 0.002)
            col.data[li].color = (1.0, 1.0, 1.0, 1.0)
    slots = []
    for sl in face_slot:
        if sl not in slots:
            slots.append(sl)
    # materials first, then indices: Mesh.materials.clear() drops material_index in Blender 4.x (A6 lesson)
    me.materials.clear()
    for sl in slots:
        me.materials.append(gm[sl])
    idx = {sl: i for i, sl in enumerate(slots)}
    for p, sl in zip(me.polygons, face_slot):
        p.material_index = idx[sl]
    o["slots"] = slots


# ---------------------------------------------------------------- UV atlas
def uv_master(o):
    """Wheels: only wheel_1L_* is unwrapped, the 5 other wheels copy its UVs (identical geometry). Right curtain
    (sheets, straps, buckles): mirrored copy of the left one's UVs - doubles the curtain texel density; dirt and
    creases are then symmetric (never seen side by side)."""
    if o.name.startswith("wheel_"):
        return o.name.startswith("wheel_1L_")
    return o.get("part") != "CURTAIN_R"


def uv_source_name(o):
    if o.name.startswith("wheel_"):
        return "wheel_1L_" + o.name.split("_", 2)[2]
    return re.sub(r"_R(_|$)", r"_L\1", o.name)


def split_long(objs, max_len=2.6, prefixes=("side_rail_", "top_rail_", "beam_web_", "beam_flange_", "sideguard_",
                                            "air_line_")):
    """Cut long profiles (13.6 m rails/beams) into <= max_len pieces along Y with split edges: smart project then
    makes one UV island per piece, so the longest island no longer sets the atlas scale (A6 lesson: coverage 0.18)."""
    for o in objs:
        if not o.name.startswith(prefixes):
            continue
        ys = [v.co.y for v in o.data.vertices]
        y0, y1 = min(ys), max(ys)
        n = math.ceil((y1 - y0) / max_len)
        if n < 2:
            continue
        bm = bmesh.new()
        bm.from_mesh(o.data)
        cut = []
        for k in range(1, n):
            y = y1 - (y1 - y0) * k / n
            r = bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=(0, y, 0),
                                       plane_no=(0, 1, 0))
            cut += [e for e in r["geom_cut"] if isinstance(e, bmesh.types.BMEdge)]
        bmesh.ops.split_edges(bm, edges=list({e for e in cut if e.is_valid}))
        bm.to_mesh(o.data)
        bm.free()


def unwrap_atlases(pieces):
    t0 = time.time()
    for slot in BAKED:
        mname = SLOT_MAT[slot]
        objs = [o for o in pieces if mname in [m.name for m in o.data.materials] and uv_master(o)]
        if not objs:
            continue
        for o in objs:
            o.data.uv_layers.active = o.data.uv_layers["Atlas"]

        def sel_faces():
            A.select(objs)
            bpy.ops.object.mode_set(mode="EDIT")
            for o in objs:
                bm = bmesh.from_edit_mesh(o.data)
                mi = [m.name for m in o.data.materials].index(mname)
                for f in bm.faces:
                    f.select = f.material_index == mi
                bmesh.update_edit_mesh(o.data)
        sel_faces()
        bpy.ops.uv.smart_project(angle_limit=math.radians(62), island_margin=0.0, area_weight=0.0,
                                 correct_aspect=True, scale_to_bounds=False)
        bpy.ops.object.mode_set(mode="OBJECT")
        for o in objs:
            me = o.data
            mi = [m.name for m in me.materials].index(mname)
            faces = [p.index for p in me.polygons if p.material_index == mi]
            uvl = me.uv_layers["Atlas"].data
            pr = me.attributes["prio"].data
            for isl in A.uv_islands(me, uvl, faces):
                area = sum(me.polygons[f].area for f in isl) or 1e-9
                k = sum(pr[f].value * me.polygons[f].area for f in isl) / area
                if abs(k - 1.0) < 1e-3:
                    continue
                lis = [li for f in isl for li in me.polygons[f].loop_indices]
                cu = sum(uvl[li].uv[0] for li in lis) / len(lis)
                cv = sum(uvl[li].uv[1] for li in lis) / len(lis)
                sc = math.sqrt(k)
                for li in lis:
                    u, v = uvl[li].uv
                    uvl[li].uv = (cu + (u - cu) * sc, cv + (v - cv) * sc)
        sel_faces()
        margin = 0.004 if ATLAS_RES[slot] >= 2048 else 0.007
        bpy.ops.uv.pack_islands(rotate=True, margin_method="FRACTION", margin=margin, shape_method="CONCAVE")
        bpy.ops.object.mode_set(mode="OBJECT")
        print(f"atlas {slot}: {len(objs)} pieces, {time.time() - t0:.0f} s")
    by_name = {o.name: o for o in pieces}
    for o in pieces:
        if uv_master(o):
            continue
        src = by_name.get(uv_source_name(o))
        if src is None:
            raise RuntimeError(f"no UV source for {o.name}")
        mirror = o.name.startswith("wheel_") and o.name.split("_")[1].endswith("R") or o.get("part") == "CURTAIN_R"
        copy_uv(src, o, mirror=mirror, dy=o.get("axle_y", 0.0) - src.get("axle_y", 0.0))


def copy_uv(src, dst, mirror, dy):
    """Per face: nearest source face of the (mirrored / shifted) centre, per loop: UV of the nearest source corner.
    Index copy is not safe: a box built on the right side has the same vertex order as the left one, not mirrored."""
    sm, dm = src.data, dst.data
    suv, duv = sm.uv_layers["Atlas"].data, dm.uv_layers["Atlas"].data
    bvh = BVHTree.FromPolygons([v.co for v in sm.vertices], [list(p.vertices) for p in sm.polygons])

    def to_src(q):
        q = q.copy()
        if mirror:
            q.x = -q.x
        q.y -= dy
        return q
    for p in dm.polygons:
        loc, nrm, idx, dist = bvh.find_nearest(to_src(p.center))
        if idx is None:
            continue
        sp = sm.polygons[idx]
        sv = [(sm.vertices[sm.loops[li].vertex_index].co, suv[li].uv.copy()) for li in sp.loop_indices]
        for li in p.loop_indices:
            q = to_src(dm.vertices[dm.loops[li].vertex_index].co)
            duv[li].uv = min(sv, key=lambda t: (t[0] - q).length_squared)[1]


# ---------------------------------------------------------------- bake
def emit_tint_mask(mats):
    """EMIT override: 1 on the tinted authoring materials (front wall paint, curtain, roof, straps)."""
    tinted = {k for k, v in MAT_SLOT.items() if v in TINTED}
    for m in mats:
        nt = m.node_tree
        out = next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL")
        if "_orig" not in m:
            lk = out.inputs["Surface"].links
            m["_orig"] = [lk[0].from_node.name, lk[0].from_socket.identifier] if lk else ["", ""]
        em = nt.nodes.get("BAKE_EMIT") or nt.nodes.new("ShaderNodeEmission")
        em.name = "BAKE_EMIT"
        for lk in list(em.inputs["Color"].links):
            nt.links.remove(lk)
        em.inputs["Color"].default_value = (1, 1, 1, 1) if m.name in tinted else (0, 0, 0, 1)
        tm = next((n for n in nt.nodes if n.label == "tint_mask"), None)     # r10: procedural livery mask (curtain band)
        if tm is not None and m.name in tinted:
            nt.links.new(tm.outputs[0], em.inputs["Color"])
        em.inputs["Strength"].default_value = 1.0
        nt.links.new(em.outputs[0], out.inputs["Surface"])


def joined_copy(objs, name, coll):
    cps = [copy_piece(o, o.name + "_j", coll) for o in objs if o.type == "MESH" and len(o.data.polygons)]
    A.select(cps, cps[0])
    if len(cps) > 1:
        bpy.ops.object.join()
    j = bpy.context.view_layer.objects.active
    j.name = name
    return j


def bake_atlases(pieces, high, high_curtain, a):
    t0 = time.time()
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.use_denoising = False
    sc.render.bake.margin = 16
    sc.render.bake.margin_type = "EXTEND"
    A.setup_world()
    coll = A.new_collection("BAKE_PROXY")
    gmat_names = [SLOT_MAT[s] for s in BAKED]

    def proxy(objs, name, keep_pred=None):
        px = joined_copy(objs, name, coll)
        bm = bmesh.new()
        bm.from_mesh(px.data)
        keep = {i for i, m in enumerate(px.data.materials) if m and m.name in gmat_names}
        bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.material_index not in keep], context="FACES")
        bm.to_mesh(px.data)
        bm.free()
        px.data.uv_layers.active = px.data.uv_layers["Atlas"]
        px.data.uv_layers["Atlas"].active_render = True
        return px
    # UV-sharing copies (wheels 1R..3R, right curtain) are not baked: their texels belong to the master
    proxies = {"STATIC": proxy([o for o in pieces if not o.name.startswith("wheel_") and uv_master(o)],
                               "PROXY_STATIC"),
               "WHEELS": proxy([o for o in pieces if o.name.startswith("wheel_1L_")], "PROXY_WHEELS"),
               "CURTAIN": proxy([o for o in pieces if re.match(r"curtain_L_\d$", o.name)], "PROXY_CURTAIN")}
    res = {s: max(64, int(ATLAS_RES[s] * a.bake_scale)) for s in BAKED}
    imgs = {s: {} for s in BAKED}
    dummy = A.new_float_image("bake_dummy", 64)
    gms = {s: bpy.data.materials[SLOT_MAT[s]] for s in BAKED}
    for s, m in gms.items():
        nt = m.node_tree
        n = nt.nodes.get("BAKE_IMG") or nt.nodes.new("ShaderNodeTexImage")
        n.name = "BAKE_IMG"
        uvn = nt.nodes.get("BAKE_UV") or nt.nodes.new("ShaderNodeUVMap")
        uvn.name = "BAKE_UV"
        uvn.uv_map = "Atlas"
        nt.links.new(uvn.outputs[0], n.inputs[0])

    def set_targets(pass_name, only=None):
        """Each proxy bakes into its OWN images (key in pass_name): the bake margin (EXTEND, 16 px) fills every texel
        outside the current proxy's faces, so a second proxy baked into the same image overwrote neighbouring
        islands of the first one (left R70 plate came out tyre-black). Proxies are merged later with UV masks."""
        for s, m in gms.items():
            n = m.node_tree.nodes["BAKE_IMG"]
            if only and s not in only:
                n.image = dummy
            else:
                if pass_name not in imgs[s]:
                    im = A.new_float_image(f"bake_{s}_{pass_name}", res[s])
                    if pass_name.startswith("N"):
                        im.pixels.foreach_set(np.tile(np.array([0.5, 0.5, 1.0, 1.0], dtype=np.float32),
                                                      res[s] * res[s]))
                    elif pass_name.startswith("PM"):
                        im.pixels.foreach_set(np.tile(np.array([0.0, 0.0, 0.0, 1.0], dtype=np.float32),
                                                      res[s] * res[s]))
                    imgs[s][pass_name] = im
                n.image = imgs[s][pass_name]
            m.node_tree.nodes.active = n
    high_mats = sorted({sl.material for o in high for sl in o.material_slots if sl.material}, key=lambda m: m.name)
    hs_static = [joined_copy([o for o in high if not o.name.startswith("HI_wheel_")], "HIGH_STATIC", coll)]
    hs_wheel = [joined_copy([o for o in high if o.name.startswith("HI_wheel_1L_")], "HIGH_WHEELS", coll)]
    hs_curt = [joined_copy(high_curtain, "HIGH_CURTAIN", coll)]

    def run(pass_name, btype, key, samples, only=None, hs=None):
        px = proxies[key]
        pass_name = pass_name + "@" + key
        set_targets(pass_name, only)
        sc.cycles.samples = samples
        for o in bpy.data.objects:
            o.hide_render = True
        px.hide_render = False
        if btype == "AO":
            A.select([px], px)
            bpy.ops.object.bake(type="AO", margin=16, use_clear=False, target="IMAGE_TEXTURES")
        else:
            for o in hs:
                o.hide_render = False
            A.select(hs + [px], px)
            kw = {"normal_space": "TANGENT"} if btype == "NORMAL" else {}
            bpy.ops.object.bake(type=btype, use_selected_to_active=True, cage_extrusion=a.cage,
                                max_ray_distance=a.cage * 2.5, margin=16, use_clear=False, target="IMAGE_TEXTURES",
                                **kw)
        print(f"  bake {pass_name} {key}: {time.time() - t0:.0f} s")
    # normal: flat everywhere (pre-filled) except the curtain sheets (dense curtain, creases)
    A.mute_micro_bumps(high_mats, True)
    run("N", "NORMAL", "CURTAIN", 8, ("Curtain",), hs_curt)
    A.mute_micro_bumps(high_mats, False)
    for key, hs, only in (("STATIC", hs_static, None), ("WHEELS", hs_wheel, ("Trim", "Metal"))):
        A.emit_override(high_mats, "albedo")
        run("ALB", "EMIT", key, 16, only, hs)
        A.emit_override(high_mats, "rdm")
        run("RDM", "EMIT", key, 16, only, hs)
        if key == "STATIC":
            emit_tint_mask(high_mats)
            run("PM", "EMIT", key, 8, TINTED, hs)
        A.emit_restore(high_mats)
        run("AO", "AO", key, a.ao_samples, only)
    for o in bpy.data.objects:
        o.hide_render = False
    raw = {s: {k: A.img_array(im) for k, im in imgs[s].items()} for s in BAKED}
    # merge: STATIC everywhere; WHEELS / CURTAIN-normal inside their own islands (+ margin), never over a STATIC island
    groups = {"STATIC": [o for o in pieces if not o.name.startswith("wheel_") and uv_master(o)],
              "WHEELS": [o for o in pieces if o.name.startswith("wheel_1L_")],
              "CURTAIN": [o for o in pieces if re.match(r"curtain_L_\d$", o.name)]}
    out = {}
    for s in BAKED:
        mn = SLOT_MAT[s]
        cov_static = uv_coverage(groups["STATIC"], mn, res[s])
        o = {}
        for p in ("ALB", "RDM", "AO", "PM"):
            if f"{p}@STATIC" in raw[s]:
                o[p] = raw[s][f"{p}@STATIC"].copy()
        flat = np.zeros((res[s], res[s], 4), dtype=np.float32)
        flat[...] = (0.5, 0.5, 1.0, 1.0)
        o["N"] = flat
        if f"ALB@WHEELS" in raw[s]:
            reg = dilate(uv_coverage(groups["WHEELS"], mn, res[s]), 10) & ~cov_static
            for p in ("ALB", "RDM", "AO"):
                o[p][reg] = raw[s][f"{p}@WHEELS"][reg]
        if f"N@CURTAIN" in raw[s]:
            cov_c = uv_coverage(groups["CURTAIN"], mn, res[s])
            others = cov_static & ~cov_c
            reg = dilate(cov_c, 10) & ~others
            o["N"][reg] = raw[s]["N@CURTAIN"][reg]
        out[s] = o
    for px in list(proxies.values()) + hs_static + hs_wheel + hs_curt:
        bpy.data.objects.remove(px)
    print(f"bakes done in {time.time() - t0:.0f} s")
    return out


def uv_coverage(objs, mname, res):
    """Rasterise the 'Atlas' UV triangles of the faces using material `mname` (conservative by ~0.7 px).
    Row 0 = v 0 (Blender pixel order, same as A.img_array)."""
    m = np.zeros((res, res), dtype=bool)
    for o in objs:
        me = o.data
        names = [x.name for x in me.materials]
        if mname not in names:
            continue
        mi = names.index(mname)
        me.calc_loop_triangles()
        uv = np.empty(len(me.loops) * 2, dtype=np.float32)
        me.uv_layers["Atlas"].data.foreach_get("uv", uv)
        uv = uv.reshape(-1, 2) * res - 0.5
        for lt in me.loop_triangles:
            if lt.material_index != mi:
                continue
            P = uv[list(lt.loops)]
            x0, y0 = np.floor(P.min(axis=0) - 1).astype(int)
            x1, y1 = np.ceil(P.max(axis=0) + 1).astype(int)
            x0, y0, x1, y1 = max(x0, 0), max(y0, 0), min(x1, res - 1), min(y1, res - 1)
            if x1 < x0 or y1 < y0:
                continue
            X, Y = np.meshgrid(np.arange(x0, x1 + 1), np.arange(y0, y1 + 1))
            inside = np.ones(X.shape, dtype=bool)
            area = (P[1, 0] - P[0, 0]) * (P[2, 1] - P[0, 1]) - (P[2, 0] - P[0, 0]) * (P[1, 1] - P[0, 1])
            sgn = 1.0 if area >= 0 else -1.0
            for i in range(3):
                a, b = P[i], P[(i + 1) % 3]
                ex, ey = b[0] - a[0], b[1] - a[1]
                ln = math.hypot(ex, ey) or 1e-9
                d = sgn * (ex * (Y - a[1]) - ey * (X - a[0])) / ln
                inside &= d >= -0.7
            m[y0:y1 + 1, x0:x1 + 1] |= inside
    return m


def dilate(m, n):
    m = m.copy()
    for _ in range(n):
        g = m.copy()
        g[1:, :] |= m[:-1, :]
        g[:-1, :] |= m[1:, :]
        g[:, 1:] |= m[:, :-1]
        g[:, :-1] |= m[:, 1:]
        m = g
    return m


def compose_textures(baked, out_dir):
    """C = albedo (sRGB) + roughness; N = tangent normal (OpenGL +Y); M = AO, dirt, metallic (Paint/Curtain: tint
    mask). URP Lit fallback: BaseMap (albedo, _Dirt 0.5 baked, tinted per livery) + MaskMap (R metal, G AO, B dirt,
    A smoothness)."""
    files = {}
    for s, b in baked.items():
        alb, rdm, ao, nrm = b["ALB"], b["RDM"], b["AO"], b["N"]
        third = b["PM"][..., 0:1] if s in TINTED else rdm[..., 2:3]
        sets = {"C": np.dstack([A.lin2srgb(alb[..., :3]), rdm[..., 0:1]]),
                "N": nrm[..., :3].copy(),
                "M": np.dstack([ao[..., 0:1], np.clip(rdm[..., 1:2], 0, 1), third, np.ones_like(third)])}
        dm = np.clip(rdm[..., 1:2], 0, 1) * URP_LIT_DIRT
        variants = [(lv, LIVERIES[lv]) for lv in LIVERIES] if s in TINTED else [("", None)]
        for lvn, lv in variants:
            a3 = alb[..., :3]
            rough = rdm[..., 0:1]
            metal = rdm[..., 2:3] if s not in TINTED else np.zeros_like(rough)
            if lv is not None:
                pm = b["PM"][..., 0:1]
                tint = np.array(lv["_PaintColor" if s == "Paint" else "_CurtainColor"], dtype=np.float32)
                a3 = a3 * (1 - pm) + a3 * tint * pm
            a3 = a3 * (1 - dm) + np.array(DUST, dtype=np.float32) * dm
            rough = np.clip(rough + 0.35 * dm, 0, 1)
            metal = metal * (1 - dm)
            sfx = "_" + lvn if lvn else ""
            sets["BaseMap" + sfx] = np.dstack([A.lin2srgb(a3), np.ones_like(rough)])
            sets["MaskMap" + sfx] = np.dstack([metal, ao[..., 0:1], np.clip(rdm[..., 1:2], 0, 1), 1 - rough])
        for kind, arr in sets.items():
            cur = arr.astype(np.float32)
            for tier in TIERS:
                if tier != "High":
                    cur = A.down2(cur)
                    if kind == "N":
                        v = cur * 2 - 1
                        v /= np.maximum(np.linalg.norm(v, axis=2, keepdims=True), 1e-6)
                        cur = v * 0.5 + 0.5
                d = os.path.join(out_dir, "textures", tier)
                os.makedirs(d, exist_ok=True)
                p = os.path.join(d, f"T_Trl_{s}_{kind}.png")
                A.save_png(cur, p, alpha=kind != "N")
                files.setdefault(s, {}).setdefault(kind, {})[tier] = {"path": rel(p), "size": int(cur.shape[0])}
    return files


# ---------------------------------------------------------------- LODs, pivots
LG = T.LG


def frames():
    """Pivot frames (Blender): (origin, X, Y, Z) - axes stay the vehicle axes for every part."""
    X, Y, Z = V((1, 0, 0)), V((0, 1, 0)), V((0, 0, 1))
    O = V((0, 0, 0))
    f = {"CHASSIS": (O, X, Y, Z), "CURTAIN_L": (O, X, Y, Z), "CURTAIN_R": (O, X, Y, Z)}
    for i, ya in enumerate(T.AXLES):
        for s, sd in ((-1, "L"), (1, "R")):
            f[f"WHEEL_{i + 1}{sd}"] = (V((s * T.TRACK / 2, ya, T.WC)), X, Y, Z)
    for s, sd in ((-1, "L"), (1, "R")):
        f[f"LEG_{sd}"] = (V((s * LG["half_track"], LG["z"], LG["raised_foot_y"])), X, Y, Z)
        f[f"MUDFLAP_{sd}"] = (V((s * 1.0175, T.AXLES[-1] - 0.66 - 0.022, 1.08)), X, Y, Z)
    f["DOOR_RR"] = (V((T.POST_IN + 0.012, T.Y_REAR - 0.014, (T.DOOR_Z0 + T.DOOR_Z1) / 2)), X, Y, Z)
    f["DOOR_RL"] = (V((-(T.POST_IN + 0.012), T.Y_REAR - 0.014, (T.DOOR_Z0 + T.DOOR_Z1) / 2)), X, Y, Z)
    f["CRANK"] = (V((LG["half_track"] + 0.165, LG["z"], 1.02)), X, Y, Z)
    return f


ANIM = {
    "DOOR_RR": {"open": ("Z", "Y", "open = -270 deg about local +Y (Unity) (door folds back along the right side)")},
    "DOOR_RL": {"open": ("Z", "Y", "open = +270 deg about local +Y (Unity) (door folds back along the left side)")},
    "LEG_L": {"lower": ("Z", "Y", "translate along local -Y (Unity): 0 = raised (foot at raised_foot_y), "
                                  "-0.52 m = loweredFootY -0.07 (physics landingGear)")},
    "LEG_R": {"lower": ("Z", "Y", "same as LEG_L")},
    "CRANK": {"crank": ("X", "X", "rotation about local +X; physics crankSpeed 0.05 m/s (gear ratio is UNVERIFIED, "
                                  "WORKING_VALUE 1 turn = 0.01 m)")},
    "MUDFLAP_L": {"swing": ("X", "X", "+-20 deg about local +X")}, "MUDFLAP_R": {"swing": ("X", "X", "+-20 deg")},
}
for _i in range(1, 4):
    for _sd in "LR":
        ANIM[f"WHEEL_{_i}{_sd}"] = {"spin": ("X", "X", "forward roll = positive angle about local +X")}


def lod_pieces(master, lod, coll):
    drop = {0: (), 1: LOD1_DROP, 2: LOD2_DROP}[lod]
    out = []
    for o in master:
        if any(k in o.name for k in drop):
            continue
        c = copy_piece(o, f"{o.name}__L{lod}", coll)
        out.append(c)
    return out


def join_parts(pieces):
    groups = {}
    for o in pieces:
        groups.setdefault(o["part"], []).append(o)
    out = {}
    for part, objs in groups.items():
        A.select(objs, objs[0])
        if len(objs) > 1:
            bpy.ops.object.join()
        ob = bpy.context.view_layer.objects.active
        ob["part"] = part
        out[part] = ob
    return out


def sockets(master):
    def centre(pred):
        pts = [p for o in master if pred(o) for p in A.world_verts(o)]
        if not pts:
            return None
        lo, hi = A.bbox(pts)
        return (lo + hi) / 2
    out = {"KINGPIN": V((0, 0, T.KP_H)), "COUPLING_HEADS": centre(lambda o: o.name.startswith("palm_")),
           "CARGO_FLOOR_FRONT": V((0, T.Y_FRONT - 0.03, T.FLOOR)), "CARGO_FLOOR_REAR": V((0, T.Y_REAR + 0.06, T.FLOOR))}
    for i, ya in enumerate(T.AXLES):
        out[f"AXLE_{i + 1}"] = V((0, ya, T.WC))
    for sd in "LR":
        out[f"LIGHT_RearLamp_{sd}"] = centre(lambda o, sd=sd: o.name == f"rear_lamp_body_{sd}")
        out[f"LANDING_FOOT_{sd}"] = V(((-1 if sd == "L" else 1) * LG["half_track"], LG["z"], LG["raised_foot_y"]))
    out["LIGHT_Reverse"] = centre(lambda o: o.name.startswith("rear_lens_rev_"))
    out["LIGHT_Plate"] = centre(lambda o: o.name.startswith("plate_lamp_lens"))
    return {k: v for k, v in out.items() if v is not None}


def collision(master, coll):
    def pts(pred):
        return [p for o in master if pred(o) for p in A.world_verts(o)]
    body = pts(lambda o: o.get("group") in ("body", "curtain") or o.name.startswith("roof_"))
    frame = pts(lambda o: o.name.startswith(("side_rail", "beam_", "front_cross", "rear_sill", "coupler_plate")))
    rear = pts(lambda o: o.name.startswith(("rup_", "lamp_panel")))
    return {"COL_Body": A.kdop_hull(body, "COL_Body", coll), "COL_Frame": A.kdop_hull(frame, "COL_Frame", coll),
            "COL_RearGuard": A.kdop_hull(rear, "COL_RearGuard", coll)}


def export_lod(lod, master, a, manifest, coll):
    t0 = time.time()
    pieces = lod_pieces(master, lod, coll)
    raw = sum(tris_of(o) for o in pieces)
    k = 0.0
    if raw > TRI_TARGET[lod]:
        k = A.decimate_pieces(pieces, TRI_TARGET[lod], floor_tris={0: 60, 1: 24, 2: 8}[lod],
                              lights_min={0: 0.9, 1: 0.5, 2: 0.2}[lod])
    fr = frames()
    parts = join_parts(pieces)
    sfx = f"_LOD{lod}"
    root = bpy.data.objects.new(f"Trailer{sfx}", None)
    coll.objects.link(root)
    objs = {}
    for part, ob in parts.items():
        A.set_pivot(ob, *fr[part])
        A.finalize_mesh(ob)
        ob.name = part + sfx
        ob.data.name = ob.name
        objs[part] = ob
    for part, ob in objs.items():
        mw = ob.matrix_world.copy()
        ob.parent = root
        ob.matrix_parent_inverse = Matrix.Identity(4)
        ob.matrix_world = mw
    empties = {}
    for nm, p in sockets(master).items():
        e = bpy.data.objects.new(nm if lod == 0 else nm + sfx, None)
        coll.objects.link(e)
        e.empty_display_size = 0.08
        e.parent = root
        e.matrix_world = Matrix.Translation(p)
        empties[nm] = (e, p)
    cols = {}
    if lod == 0:
        cols = collision(master, coll)
        for nm, ob in cols.items():
            ob.parent = root
            ob.matrix_parent_inverse = Matrix.Identity(4)
    info = {"file": None, "root": root.name, "objects": {}, "empties": {}, "collision": {}, "tris_total": 0,
            "tris_before_decimation": raw, "decimate_area_budget_k": round(k, 2)}
    for part, ob in objs.items():
        e = {"role": part, "rig_parent": root.name, "fbx_parent": root.name, "tris": tris_of(ob),
             "materials": [m.name for m in ob.data.materials],
             "pivot_unity_vehicle": a2u(ob.matrix_world.translation),
             "rig_local_position_unity": a2u(ob.matrix_world.translation)}
        R = ob.matrix_world.to_3x3()
        if part in ANIM:
            e["animation"] = {kk: {"local_axis_blender": v[0], "local_axis_unity": v[1],
                                   "axis_unity_vehicle": a2u(R.col["XYZ".index(v[0])]), "convention": v[2]}
                              for kk, v in ANIM[part].items()}
        if part.startswith("WHEEL_"):
            pts = [ob.matrix_world @ v.co for v in ob.data.vertices]
            c = ob.matrix_world.translation
            e["tyre_outer_radius_m"] = round(max(math.hypot(p.y - c.y, p.z - c.z) for p in pts), 4)
            lo, hi = A.bbox(pts)
            e["width_m"] = round(hi.x - lo.x, 4)
        info["objects"][ob.name] = e
        info["tris_total"] += e["tris"]
    for nm, (eo, p) in empties.items():
        info["empties"][eo.name] = {"rig_parent": root.name, "fbx_parent": root.name,
                                    "position_unity_vehicle": a2u(p), "rig_local_position_unity": a2u(p)}
    for nm, ob in cols.items():
        info["collision"][nm] = {"tris": tris_of(ob), "verts": len(ob.data.vertices), "convex": True,
                                 "parent": root.name}
    os.makedirs(a.out, exist_ok=True)
    fbx = os.path.join(a.out, f"SM_Trailer_LOD{lod}.fbx")
    A.select([root] + list(root.children_recursive), root)
    bpy.ops.export_scene.fbx(filepath=fbx, use_selection=True, object_types={"EMPTY", "MESH"},
                             apply_unit_scale=True, apply_scale_options="FBX_SCALE_ALL", axis_forward="Z", axis_up="Y",
                             bake_space_transform=True, use_mesh_modifiers=False, mesh_smooth_type="FACE",
                             use_tspace=True, colors_type="SRGB", prioritize_active_color=True, add_leaf_bones=False,
                             bake_anim=False, path_mode="STRIP", embed_textures=False, use_custom_props=False)
    info["file"] = rel(fbx)
    info["file_bytes"] = os.path.getsize(fbx)
    info["build_s"] = round(time.time() - t0, 1)
    manifest["lods"][f"LOD{lod}"] = info
    print(f"LOD{lod}: {info['tris_total']} tris (raw {raw}), {len(objs)} objects -> {fbx}")
    return root, objs


# ---------------------------------------------------------------- texel density, crosscheck
def texel_density(master):
    out = {}
    for slot in BAKED:
        mn = SLOT_MAT[slot]
        a3 = auv = 0.0
        for o in master:
            if not uv_master(o):
                continue
            me = o.data
            names = [m.name for m in me.materials]
            if mn not in names:
                continue
            mi = names.index(mn)
            uvl = me.uv_layers["Atlas"].data
            for p in me.polygons:
                if p.material_index != mi:
                    continue
                a3 += p.area
                uv = [uvl[i].uv for i in p.loop_indices]
                for kk in range(1, len(uv) - 1):
                    auv += abs((uv[kk][0] - uv[0][0]) * (uv[kk + 1][1] - uv[0][1]) - (uv[kk + 1][0] - uv[0][0]) *
                               (uv[kk][1] - uv[0][1])) / 2
        d = ATLAS_RES[slot] * math.sqrt(auv / a3) if a3 > 0 else 0
        out[slot] = {"area_m2": round(a3, 2), "uv_coverage": round(auv, 3),
                     "px_per_m": {t: round(d / div) for t, div in TIERS.items()}}
    return out


def measure(master):
    def pts(pred):
        return [p for o in master if pred(o) for p in A.world_verts(o)]
    # body = load-carrying envelope; fittings excluded (door locks/hinges/keepers, tarpaulin fastening buckles and
    # tensioners, couplings, lamps) - the 96/53/EC exclusion list was not opened here (UNVERIFIED)
    fittings = ("lock", "keeper", "hinge", "stalk_", "palm_", "socket", "coupling", "buckle", "tension_",
                "door_centre", "contour")
    body = pts(lambda o: (o.get("group") in ("body", "curtain") and not o.name.startswith(fittings)) or
               o.name.startswith(("roof_", "side_rail")))
    lo, hi = A.bbox(body)
    front = [p for p in body if p.y > 0 and p.z > T.KP_H]
    swing = max(math.hypot(p.x, p.y) for p in front)
    allp = pts(lambda o: True)
    alo, ahi = A.bbox(allp)
    tyre = pts(lambda o: o.name == "wheel_1L_tyre")
    c = V((-T.TRACK / 2, T.AXLES[0], T.WC))
    feet = pts(lambda o: o.name.startswith("leg_foot_L"))
    return {"body_length": hi.y - lo.y, "body_width": hi.x - lo.x, "height": ahi.z, "y_front": hi.y, "y_rear": lo.y,
            "front_swing": swing, "overall_length": ahi.y - alo.y, "overall_width": ahi.x - alo.x,
            "tyre_r": max(math.hypot(p.y - c.y, p.z - c.z) for p in tyre),
            "tyre_w": max(p.x for p in tyre) - min(p.x for p in tyre),
            "foot": min(p.z for p in feet)}


def physics_crosscheck(meas):
    res = {"source": rel(os.path.join(PHYS, "curtainsider_tridem_13_6.trailer.json"))}
    try:
        trl = json.load(open(os.path.join(PHYS, "curtainsider_tridem_13_6.trailer.json"), encoding="utf-8"))
        tyre = json.load(open(os.path.join(PHYS, "tire_385_65_r22_5.tire.json"), encoding="utf-8"))
    except OSError as e:
        res["error"] = str(e)
        return res
    cb, lg = trl["cargoBay"], trl["landingGear"]
    clear_rail = T.TOPRAIL_Z - T.FLOOR
    rows = [
        ("kingpin height (dims fifth_wheel_height_m) / kingpinHeight", T.KP_H, trl["kingpinHeight"], 1e-3, ""),
        ("axle 1 z (WHEEL_1x pivot)", T.AXLES[0], trl["axles"][0]["positionZ"], 1e-3, ""),
        ("axle 2 z (WHEEL_2x pivot)", T.AXLES[1], trl["axles"][1]["positionZ"], 1e-3, ""),
        ("axle 3 z (WHEEL_3x pivot)", T.AXLES[2], trl["axles"][2]["positionZ"], 1e-3, ""),
        ("track (wheel pivots)", T.TRACK, trl["axles"][0]["trackWidth"], 1e-3, ""),
        ("wheel centre height (pivot) / tyre radius", T.WC, tyre["radius"], 1e-3, ""),
        ("tyre radius: mesh free / physics effective", round(meas["tyre_r"], 4), tyre["radius"], 1e-3,
         "expected: mesh = free radius 0.536 (ETRTO), physics = rolling radius; flatten in the shader as on the tractor"),
        ("tyre width: mesh / widthM", round(meas["tyre_w"], 4), tyre["widthM"], 0.01, "mesh incl. sidewall bulge"),
        ("landing gear z (LEG pivots)", LG["z"], lg["positionZ"], 1e-3, ""),
        ("landing gear half track", LG["half_track"], lg["halfTrack"], 1e-3, ""),
        ("landing gear raised foot (mesh foot bottom)", round(meas["foot"], 4), lg["raisedFootY"], 2e-3, ""),
        ("cargo floor height (art floor plane)", T.FLOOR, cb["floorHeight"], 1e-3, ""),
        ("cargo front z (inner face of the front wall)", round(T.Y_FRONT - 0.028, 3), cb["frontZ"], 0.01,
         "front wall 28 mm deep incl. ribs"),
        ("cargo length (front wall inner -> door inner)", round(T.Y_FRONT - 0.028 - (T.DOOR_FACE + 0.035), 3),
         cb["length"], 0.02, ""),
        ("cargo width (between curtains)", round(2 * T.CURT_X, 3), cb["width"], 0.04, ""),
        ("cargo height: clear under the top rail", round(clear_rail, 3), cb["height"], 0.02,
         "physics floorHeight + height = 4.00 m = legal max -> no room for roof/top rail; art: 2.58 m under the "
         "rail, ~2.66 m under the roof bows (class-typical 2.65-2.70 m at a 1.25-1.30 m deck)"),
        ("body length (front wall -> rear portal)", round(meas["body_length"], 3), 13.6, 0.01, ""),
        ("kingpin -> rear end (96/53/EC <= 12.00)", round(-meas["y_rear"], 3), 12.0, 0.005, ""),
        ("front swing radius (96/53/EC <= 2.04)", round(meas["front_swing"], 3), 2.04, 0.0, "must be <= 2.04"),
        ("body width (<= 2.55)", round(meas["body_width"], 3), 2.55, 0.0, "must be <= 2.55; lamps/stalks excluded"),
        ("overall height (<= 4.00)", round(meas["height"], 3), 4.0, 0.0, "must be <= 4.00"),
        ("tridem mass element centre y / wheel centre", T.WC, trl["massElements"][3]["center"]["y"], 1e-3, ""),
        ("landing gear mass element z", LG["z"], trl["massElements"][4]["center"]["z"], 1e-3, ""),
        ("combination length TRAKT + trailer (<= max_artic_length_m)",
         round(G.D("front_overhang_m") + G.D("wheelbase_m") - G.D("fifth_wheel_lead_m") - meas["y_rear"], 3),
         G.D("max_artic_length_m"), 0.0,
         "tractor front -> kingpin = front_overhang + wheelbase - fifth_wheel_lead = 4.60 m; with kingpin -> rear 12.00 "
         "the combination is 16.60 m > 16.50 m. Needs fifth_wheel_lead >= 0.65 m (or a shorter front overhang) - "
         "tractor/physics value in dims.json, not changed here (lead / vehicle-physics decision)"),
    ]
    res["rows"] = []
    for name, art, phys, tol, note in rows:
        if "<=" in name:
            ok = art <= phys + 1e-6
        else:
            ok = abs(art - phys) <= tol + 1e-9
        r = {"item": name, "art": art, "physics": phys, "match": bool(ok)}
        if note:
            r["note"] = note
        res["rows"].append(r)
    return res


# ---------------------------------------------------------------- preview materials (Cycles stand-in of the contract)
def preview_materials(tex, livery, dirt=0.5, lights=None):
    lv = LIVERIES[livery]
    lights = lights or {}

    def img(slot, kind):
        p = os.path.join(REPO, tex[slot][kind]["High"]["path"])
        im = bpy.data.images.load(p, check_existing=True)
        im.colorspace_settings.name = "sRGB" if kind == "C" else "Non-Color"
        return im
    for slot in BAKED:
        m = bpy.data.materials[SLOT_MAT[slot]]
        nt = m.node_tree
        for n in list(nt.nodes):
            nt.nodes.remove(n)
        out = nt.nodes.new("ShaderNodeOutputMaterial")
        b = nt.nodes.new("ShaderNodeBsdfPrincipled")
        nt.links.new(b.outputs[0], out.inputs[0])
        uv = nt.nodes.new("ShaderNodeUVMap")
        uv.uv_map = "Atlas"
        tc, tn, tm = (nt.nodes.new("ShaderNodeTexImage") for _ in range(3))
        tc.image, tn.image, tm.image = img(slot, "C"), img(slot, "N"), img(slot, "M")
        for t in (tc, tn, tm):
            nt.links.new(uv.outputs[0], t.inputs[0])
        sm = nt.nodes.new("ShaderNodeSeparateColor")
        nt.links.new(tm.outputs["Color"], sm.inputs[0])
        nm = nt.nodes.new("ShaderNodeNormalMap")
        nm.uv_map = "Atlas"
        nt.links.new(tn.outputs["Color"], nm.inputs["Color"])
        nt.links.new(nm.outputs[0], b.inputs["Normal"])
        dmask = M.math_node(nt, "MULTIPLY", sm.outputs[1], dirt, clamp=True)
        base = tc.outputs["Color"]
        rough = tc.outputs["Alpha"]
        if slot in TINTED:
            col = lv["_PaintColor" if slot == "Paint" else "_CurtainColor"]
            tint = nt.nodes.new("ShaderNodeMix")
            tint.data_type = "RGBA"
            tint.inputs[6].default_value = (1, 1, 1, 1)
            tint.inputs[7].default_value = (*col, 1)
            nt.links.new(sm.outputs[2], tint.inputs[0])
            mul = nt.nodes.new("ShaderNodeMix")
            mul.data_type = "RGBA"
            mul.blend_type = "MULTIPLY"
            mul.inputs[0].default_value = 1.0
            nt.links.new(base, mul.inputs[6])
            nt.links.new(tint.outputs[2], mul.inputs[7])
            base = mul.outputs[2]
            metal = 0.0
        else:
            metal = sm.outputs[2]
        mixd = nt.nodes.new("ShaderNodeMix")
        mixd.data_type = "RGBA"
        nt.links.new(dmask, mixd.inputs[0])
        nt.links.new(base, mixd.inputs[6])
        mixd.inputs[7].default_value = (*DUST, 1)
        nt.links.new(mixd.outputs[2], b.inputs["Base Color"])
        nt.links.new(M.math_node(nt, "ADD", rough, M.math_node(nt, "MULTIPLY", dmask, 0.35), clamp=True),
                     b.inputs["Roughness"])
        if isinstance(metal, float):
            b.inputs["Metallic"].default_value = 0.0
        else:
            nt.links.new(M.math_node(nt, "MULTIPLY", metal, M.math_node(nt, "SUBTRACT", 1.0, dmask, clamp=True)),
                         b.inputs["Metallic"])
        if slot == "Lights" and lights:
            dv = nt.nodes.new("ShaderNodeUVMap")
            dv.uv_map = "Data"
            sp = nt.nodes.new("ShaderNodeSeparateXYZ")
            nt.links.new(dv.outputs[0], sp.inputs[0])
            acc = None
            for gname, strength in lights.items():
                gi = LIGHT_GROUPS.index(gname)
                cmp_ = nt.nodes.new("ShaderNodeMath")
                cmp_.operation = "COMPARE"
                cmp_.inputs[1].default_value = gi
                cmp_.inputs[2].default_value = 0.25
                nt.links.new(sp.outputs[0], cmp_.inputs[0])
                cc = nt.nodes.new("ShaderNodeCombineColor")
                k = M.math_node(nt, "MULTIPLY", cmp_.outputs[0], strength)
                cr = nt.nodes.new("ShaderNodeMix")
                cr.data_type = "RGBA"
                cr.blend_type = "MULTIPLY"
                cr.inputs[0].default_value = 1.0
                cr.inputs[6].default_value = (*LIGHT_COLOUR[gname], 1)
                for i in range(3):
                    nt.links.new(k, cc.inputs[i])
                nt.links.new(cc.outputs[0], cr.inputs[7])
                if acc is None:
                    acc = cr.outputs[2]
                else:
                    ad = nt.nodes.new("ShaderNodeMix")
                    ad.data_type = "RGBA"
                    ad.blend_type = "ADD"
                    ad.inputs[0].default_value = 1.0
                    nt.links.new(acc, ad.inputs[6])
                    nt.links.new(cr.outputs[2], ad.inputs[7])
                    acc = ad.outputs[2]
            nt.links.new(acc, b.inputs["Emission Color"])
            b.inputs["Emission Strength"].default_value = 1.0


# ---------------------------------------------------------------- QA renders
CAMS = {
    "34tyl": dict(loc=(-9.0, -21.5, 2.6), target=(0.0, -6.6, 1.9), lens=32),
    "bok": dict(loc=(-30, -5.2, 2.0), rot=(math.radians(90), 0, math.radians(-90)), ortho=15.6),
    "zestaw_34przod": dict(loc=(-10.5, 10.5, 2.7), target=(0.2, -3.6, 1.9), lens=30),
    "zestaw_bok": dict(loc=(-30, -3.4, 2.0), rot=(math.radians(90), 0, math.radians(-90)), ortho=19.5),
    "zbl_lampy": dict(loc=(-2.5, -14.9, 1.3), target=(-0.75, -12.0, 0.95), lens=40),
    "zbl_kolo": dict(loc=(-3.9, -5.4, 0.85), target=(-1.1, -7.7, 0.62), lens=32),
    "zbl_noga": dict(loc=(3.4, -0.4, 1.05), target=(0.9, -2.3, 0.85), lens=36),
    "zbl_firanka": dict(loc=(-4.6, -1.6, 2.2), target=(-1.27, -5.4, 2.1), lens=40),
}


def import_tractor():
    """TRAKT LOD0 FBX + its game materials (A6 preview), placed so its fifth-wheel kingpin = trailer kingpin."""
    man = json.load(open(os.path.join(REPO, "art-source", "truck", "exterior", "export", "truck_exterior_manifest.json"),
                         encoding="utf-8"))
    before = set(bpy.data.objects.keys())
    bpy.ops.import_scene.fbx(filepath=os.path.join(REPO, man["lods"]["LOD0"]["file"]), axis_forward="Z", axis_up="Y")
    new = [o for o in bpy.data.objects if o.name not in before]
    root = next(o for o in new if o.name.startswith("TruckExterior_LOD0"))
    bpy.context.view_layer.update()
    kp = next(o for o in new if o.name.startswith("FIFTH_WHEEL_KINGPIN")).matrix_world.translation.copy()
    root.location = root.location + (V((0, 0, T.KP_H)) - kp)
    for o in new:
        if o.name.startswith("COL_") or o.type == "EMPTY":
            o.hide_render = True
    A.preview_materials(man["textures"], "white")
    return new


def qa_renders(a, tex, roots, objs0, manifest):
    os.makedirs(a.renders, exist_ok=True)
    sc = bpy.context.scene
    S.setup_render("1600x900", a.samples)
    S.yard()
    out = []

    def show_only(lod):
        for k, r in roots.items():
            for o in [r] + list(r.children_recursive):
                o.hide_render = (k != lod) or o.name.startswith("COL_")

    def cam(view, res=(1600, 900)):
        c = CAMS[view]
        cm = S.add_camera("cam_" + view, c["loc"], c.get("target"), c.get("lens", 40), c.get("ortho"), c.get("rot"))
        sc.camera = cm
        sc.render.resolution_x, sc.render.resolution_y = res

    def render(name, label):
        S.stamp(label)
        sc.render.filepath = os.path.join(a.renders, name)
        bpy.ops.render.render(write_still=True)
        out.append(sc.render.filepath)
        print("WROTE", sc.render.filepath)
    legs = [objs0[p] for p in ("LEG_L", "LEG_R")]
    base = {o.name: o.matrix_basis.copy() for o in legs}

    def legs_down(down):
        for o in legs:
            o.matrix_basis = base[o.name] @ Matrix.Translation((0, 0, -LG["raised_foot_y"] if down else 0.0))
    t0 = manifest["lods"]["LOD0"]["tris_total"]
    show_only(0)
    legs_down(True)
    S.lighting("overcast")
    for livery in LIVERIES:
        preview_materials(tex, livery)
        cam("34tyl")
        render(f"34tyl_{livery}_overcast_lod0.jpg", f"Naczepa firanka 13,6 m tridem | LOD0 {t0} tr. | materiały gry "
                                                   f"(atlasy) | {LIVERIES[livery]['label']} | pochmurno")
    preview_materials(tex, "szary")
    cam("bok")
    render("bok_szary_overcast_lod0.jpg", "Naczepa | LOD0 | bok (ortho) | pochmurno | podpory opuszczone")
    cam("zbl_kolo")
    render("zbl_kolo_overcast_lod0.jpg", "Naczepa | LOD0 | tridem 385/65 R22.5, felgi stalowe, natrysk z kół | pochmurno")
    cam("zbl_noga")
    render("zbl_noga_overcast_lod0.jpg", "Naczepa | LOD0 | podpory z korbą (prawa strona), osłona boczna | pochmurno")
    cam("zbl_firanka")
    render("zbl_firanka_overcast_lod0.jpg", "Naczepa | LOD0 | firanka: pasy, napinacze, fałdy (normal map) | pochmurno")
    preview_materials(tex, "szary", lights={"TAIL_BRAKE": 0.6, "MARKER_REAR": 1.5, "MARKER_SIDE": 1.5,
                                            "IND_L": 2.5, "PLATE": 1.0})
    cam("zbl_lampy")
    render("zbl_lampy_overcast_lod0.jpg", "Naczepa | LOD0 | lampy tylne: pozycja + kierunek L + obrysowe + tablica "
                                          "(grupy emisji z UV2) | pochmurno")
    preview_materials(tex, "szary")
    S.lighting("lowsun")
    cam("34tyl")
    render("34tyl_szary_lowsun_lod0.jpg", "Naczepa | LOD0 | firanka szara | niskie słońce (~8°)")
    cam("zbl_firanka")
    render("zbl_firanka_lowsun_lod0.jpg", "Naczepa | LOD0 | firanka pod światło smugowe | niskie słońce (~8°)")
    # coupled to the TRAKT tractor (legs raised)
    legs_down(False)
    tractor = import_tractor()
    preview_materials(tex, "szary")
    for light in ("overcast", "lowsun"):
        S.lighting(light)
        cam("zestaw_34przod")
        render(f"zestaw_34przod_{light}_lod0.jpg", f"Zestaw TRAKT + naczepa (LOD0 obu) | sworzeń = siodło 1,15 m | "
                                                   f"{'pochmurno' if light == 'overcast' else 'niskie słońce (~8°)'}")
    S.lighting("overcast")
    cam("zestaw_bok")
    render("zestaw_bok_overcast_lod0.jpg", "Zestaw TRAKT + naczepa | bok (ortho) | długość zestawu i promienie "
                                           "(96/53/EC: 16,50 m)")
    for o in tractor:
        o.hide_render = True
    # LODs
    legs_down(True)
    for lod in sorted(roots):
        show_only(lod)
        if lod:
            for p in ("LEG_L", "LEG_R"):
                o = bpy.data.objects.get(f"{p}_LOD{lod}")
                if o is not None:
                    o.matrix_basis = o.matrix_basis @ Matrix.Translation((0, 0, -LG["raised_foot_y"]))
        cam("34tyl", (960, 540))
        render(f"lod{lod}_34tyl.jpg", f"LOD{lod}: {manifest['lods'][f'LOD{lod}']['tris_total']} trójkątów")
    # pivots: doors open, legs lowered, crank turned, mudflaps swung; gizmos on every moving part
    show_only(0)
    saved = {}
    rot = {"DOOR_RR": ("Z", math.radians(110)), "DOOR_RL": ("Z", math.radians(-110)),
           "CRANK": ("X", math.radians(90)), "MUDFLAP_L": ("X", math.radians(20)), "MUDFLAP_R": ("X", math.radians(20))}
    gizmos = []
    for part, o in objs0.items():
        if part.startswith(PARTS_MOVING):
            gizmos += A.axis_gizmo(o, "WHEEL_" if part.startswith("WHEEL_") else part)
        if part in rot:
            saved[o.name] = o.matrix_basis.copy()
            ax, ang = rot[part]
            o.matrix_basis = o.matrix_basis @ Matrix.Rotation(ang, 4, ax)
    S.lighting("overcast")
    pv = S.add_camera("cam_pivots", (6.5, -18.5, 4.2), (0.2, -9.5, 1.4), 30)
    sc.camera = pv
    sc.render.resolution_x, sc.render.resolution_y = 1600, 900
    render("pivoty_34tyl.jpg", "Piwoty naczepy: drzwi 110°, podpory opuszczone, chlapacze 20°, korba; osie: czerwona = X, "
                               "zielona = Y Unity (góra), niebieska = Z Unity (przód)")
    for nm, mb in saved.items():
        bpy.data.objects[nm].matrix_basis = mb
    for g in gizmos:
        bpy.data.objects.remove(g)
    legs_down(False)
    return out


# ---------------------------------------------------------------- main
def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    p = argparse.ArgumentParser()
    p.add_argument("--out", default=os.path.join(REPO, "art-source", "truck", "trailer", "export"))
    p.add_argument("--renders", default=os.path.join(REPO, "docs", "reports", "visual", "trailer-curtainsider"))
    p.add_argument("--no-renders", action="store_true")
    p.add_argument("--bake-scale", type=float, default=1.0)
    p.add_argument("--ao-samples", type=int, default=128)
    p.add_argument("--samples", type=int, default=96)
    p.add_argument("--cage", type=float, default=0.02)
    p.add_argument("--blend", default="")
    a = p.parse_args(argv)
    a.out = os.path.abspath(a.out)
    a.renders = "" if a.no_renders else os.path.abspath(a.renders)
    t0 = time.time()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    M.TEX_DIR = os.path.join(tempfile.gettempdir(), "kamion_trailer_src")   # generated source images, not in git
    S.setup_render("1600x900", 64)
    M.PARAMS["dirt"] = 1.0       # grime authored at full strength: the dirt mask is baked at 1, the game scales it
    built = T.build(hi=True)
    srcs = built["pieces"]
    hi_curt = built["high_only"]
    A.apply_modifiers(srcs + hi_curt)
    A.bake_transforms(srcs + hi_curt)
    split_long(srcs)
    for o in srcs:
        if o.name.startswith("wheel_"):
            o["axle_y"] = T.AXLES[int(o.name.split("_")[1][0]) - 1]
    hcoll = A.new_collection("HIGH")
    high = []
    for o in srcs:
        h = copy_piece(o, "HI_" + o.name, hcoll)
        high.append(h)
    gcoll = A.new_collection("GAME")
    for o in srcs:
        for c in list(o.users_collection):
            c.objects.unlink(o)
        gcoll.objects.link(o)
    gm = game_materials()
    for o in srcs:
        to_game_piece(o, gm)
    tri_pieces = sum(tris_of(o) for o in srcs)
    print(f"pieces: {len(srcs)}, tris {tri_pieces}")
    unwrap_atlases(srcs)
    baked = bake_atlases(srcs, high, hi_curt, a)
    tex = compose_textures(baked, a.out)
    meas = measure(srcs)
    for o in high + hi_curt:
        bpy.data.objects.remove(o)
    td = texel_density(srcs)
    manifest = {"asset": "Curtainsider semi-trailer 13.6 m tridem (fictional, no brand)",
                "generator": "tools/blender/truck/trailer/trailer_export.py (+ trailer_build.py)", "lods": {}}
    lcoll = A.new_collection("LODS")
    roots, objs0 = {}, {}
    for lod in (0, 1, 2):
        root, objs = export_lod(lod, srcs, a, manifest, lcoll)
        roots[lod] = root
        if lod == 0:
            objs0 = objs
    for o in srcs:
        o.hide_render = True
        o.hide_viewport = True
    manifest.update(meta(tex, td, tri_pieces, meas))
    man_path = os.path.join(a.out, "trailer_manifest.json")
    with open(man_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=1, ensure_ascii=False)
    print("WROTE", man_path)
    if a.blend:
        bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(a.blend))
    if a.renders:
        manifest["qa_renders"] = [rel(x) for x in qa_renders(a, tex, roots, objs0, manifest)]
        with open(man_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=1, ensure_ascii=False)
    print(f"trailer export done in {time.time() - t0:.0f} s")


def meta(tex, td, tri_pieces, meas):
    return {
        "units": "metres",
        "unity_axes": "+X right (kerb side), +Y up, +Z forward",
        "frame_mapping": "Blender (x, y, z) -> Unity (x, z, y); FBX axis_forward=Z, axis_up=Y, bake_space_transform, "
                         "FBX_SCALE_ALL (same as the TRAKT exterior). Unity import: Scale Factor 1, Convert Units on, "
                         "Bake Axis Conversion off. Positions are in the Unity trailer frame.",
        "origin": {"name": "Trailer_LODn root", "unity_trailer": [0.0, 0.0, 0.0],
                   "note": "ground below the kingpin = physics trailer frame (curtainsider_tridem_13_6.trailer.json: "
                           "axles at negative z, kingpinHeight above the origin). Hitch: put the root so that "
                           "KINGPIN coincides with the tractor socket FIFTH_WHEEL_KINGPIN."},
        "rig_note": "Flat FBX hierarchy (every part and socket is a direct child of the root), as on the tractor. All "
                    "rig parents are the root: WHEEL_1L..3R spin, DOOR_RL/RR swing on the rear-post hinges, LEG_L/R "
                    "translate (inner leg + sand shoe), CRANK turns, MUDFLAP_L/R swing, CURTAIN_L/R are static "
                    "(separate for a later curtain-open variant). LOD1/LOD2: same parts and pivots (LOD2 has no "
                    "CRANK detail beyond the arm).",
        "lod_targets": {f"LOD{k}": f"<= {v}" for k, v in TRI_LIMIT.items()},
        "lod_screen_size_suggestion": {"LOD0": 0.40, "LOD1": 0.16, "LOD2": 0.05, "cull": 0.005},
        "tris_source_pieces": tri_pieces,
        "slots": SLOT_MAT,
        "tiers": {"High": "LOD0-1 + High textures", "Medium": "LOD1-2 + Medium textures", "Low": "LOD2 + Low textures",
                  "texture_compression": "ASTC as the tractor: C 6x6 (High) / 8x8, N 5x5 (High) / 6x6, M 8x8; power-"
                                         "of-two squares, mipmaps on; N and M linear, C sRGB"},
        "textures": tex,
        "liveries": LIVERIES,
        "shader_contract": {
            "name": "Kamion/TruckExterior (same contract as the tractor; Curtain is a second tinted slot)",
            "uv0 'Atlas'": "unique atlas UV per slot; the 6 wheels share the UVs of WHEEL_1L (right side mirrored)",
            "uv1 'Decal'": "unused (0.002, 0.002) - kept for layout parity with the tractor",
            "uv2 'Data'": "x = light group id (light_groups), y = emissive mask (1 on lamp lenses)",
            "color 'Col'": "white",
            "textures": "T_Trl_<Slot>_C (RGB albedo sRGB, A roughness), _N (tangent normal, OpenGL +Y), _M (R AO, G "
                        "dirt mask at full strength, B metallic; Paint/Curtain: B = tint mask)",
            "albedo": "C.rgb; Paint: lerp(1, _PaintColor, M.b) * C.rgb; Curtain: lerp(1, _CurtainColor, M.b) * C.rgb; "
                      "then lerp(albedo, _DirtColor, saturate(M.g * _Dirt))",
            "roughness": "C.a + 0.35 * M.g * _Dirt",
            "metallic": "M.b (Trim/Metal/Lights), 0 on Paint/Curtain; * (1 - saturate(M.g * _Dirt))",
            "occlusion": "M.r",
            "emission": "Lights: _LightState[uv2.x] * uv2.y (ids shared with the tractor + 13 = PLATE)",
            "_Dirt": "0 washed, 0.5 = renders, 1 = very dirty",
            "_DirtColor": list(DUST),
            "urp_lit_fallback": "stock URP Lit: _BaseMap = T_Trl_<Slot>_BaseMap[_<livery>] (_Dirt 0.5 baked), "
                                "_MetallicGlossMap and _OcclusionMap = T_Trl_<Slot>_MaskMap[_<livery>] (R metal, G AO, "
                                "B dirt, A smoothness), _BumpMap = T_Trl_<Slot>_N. Loses the dirt slider and lights.",
            "light_groups": {i: g for i, g in enumerate(LIGHT_GROUPS)},
            "light_colours_linear": LIGHT_COLOUR,
            "texel_density": td,
            "texel_density_note": "no texel-density ADR in the repo yet (same open point as the tractor A6 README)",
        },
        "measured": {k: round(v, 4) for k, v in meas.items()},
        "physics_crosscheck": physics_crosscheck(meas),
        "dims_reference": "art-source/truck/dims.json (trailer_* keys, ADR 0014)",
        "licences": "own work generated by code; tyre lettering in Inter (OFL, already in docs/LICENSES.md); no "
                    "downloaded textures, scans or HDRI; no brand, logo or manufacturer shape",
    }


if __name__ == "__main__":
    main()
