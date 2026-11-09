"""Track A6 — game-ready cab interior: LODs, cleanup, material consolidation, AO atlas, FBX export, import manifest.

    blender -b --factory-startup --python tools/blender/truck/interior/a6_export.py -- \
        [--lods 0,1,2] [--out art-source/truck/interior/export] [--ao-samples 512] [--ao-distance 0.6] \
        [--urp-out DIR --urp-light overcast,lowsun --urp-res 1600x900]   # URP-like preview renders of LOD0

Reproducible: everything is regenerated from build_interior.py (same code, LOD = tessellation factor + detail
drops), so LOD0/1/2 always match. Per LOD:
 1. build at LOD tessellation (G.STATE['q'] 1.0 / 0.55 / 0.35) and drop sub-LOD details (LOD_DROP);
 2. apply modifiers, remove hidden faces (ray visibility from ~80 view points: driver/passenger head box, bunk,
    standing, footwells, render cameras, a ring of exterior cameras looking in through the glass);
 3. consolidate the ~45 authoring materials into 5 opaque detail slots + decal atlas + glass + display + mirror,
    moving per-material values into vertex data (shader contract in the manifest);
 4. re-layout UV1 ('Bake') for the AO atlas with texel priority on driver-visible surfaces; glass, decals,
    displays, mirrors and curtains map to a neutral (white) texel block; bake AO, denoise, dilate;
 5. join into draw-call groups with functional pivots (steering wheel, stalks, pedals, park-brake lever),
    displays and mirror glass as separate named quads, empties for eye/H-point/wheel centre/mount;
 6. export FBX (Unity: +Z forward, +Y up, metres) + textures per tier (High/Medium/Low) + manifest JSON.
"""
import argparse
import json
import math
import os
import shutil
import sys
import time

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_interior as BI  # noqa: E402
import geom as G  # noqa: E402
import materials as M  # noqa: E402

V = G.V
CAB_MOUNT = V(0.0, 0.225, 1.15)   # graybox CabPivot (TractorDimensions: cabBodyBottom, cab mid-length) in A2 frame
TRI_TARGET = {0: 90000, 1: 40000, 2: 20000}
AO_RES = {0: 2048, 1: 1024, 2: 512}
TIERS = {"High": 1.0, "Medium": 0.5, "Low": 0.25}

LOD1_DROP = ("rocker_led_", "hatch_pleat_", "din_btn_", "bunk_btn_", "fridge_vent", "socket_", "usb_p_", "cup_",
             "drawer_grip_", "rear_grip_", "oh_grip_", "_damper", "bunk_buckle_", "doc_clip_roller", "hvac_ring_",
             "start_ring", "stalk_boss_", "_lever_knob", "_lever_h", "_arm_pivot", "pocket_mat_", "spot_",
             "mirror_spine_", "bunk_strap_", "tweeter_grille_", "dash_spk_rim")
LOD2_DROP = LOD1_DROP + ("_cst_", "_ctr_", "_bst_", "_btr_", "rocker_icon_", "hvac_icon_", "low_icon_", "light_icon",
                         "defrost_", "reading_lamp_", "pillow", "blanket", "curtain_side_", "hatch_blind", "_hr_collar",
                         "_belt_latch_grip", "_belt_guide", "_buckle", "_pocket_edge", "door_spk_grille_", "vent_",
                         "din_unit_", "din_lcd_1", "bunk_lcd", "bunk_panel", "dome_", "wiper_", "ws_gasket_",
                         "opener_", "winswitch_", "mirrorswitch_", "uglove", "glove_gap", "pdash_parting",
                         "dash_parting", "rocker_", "hvac_btn_", "low_sw_", "mirror_pad", "light_rotary",
                         "_backpocket", "door_pull_", "dash_tray_lip", "doc_clip", "hatch_frame", "drawer_",
                         "_belt_latch", "tweeter_", "door_seal_", "win_channel_", "curtain_rail")

# ---------------------------------------------------------------- slots (game materials)
SLOT_OF = {
    "MI_Cab_Plastic": ("dash_soft", "dash_lower", "dash_mid", "dash_dark", "trim_insert", "trim_light", "metal_dark",
                       "piano", "switch", "knob", "gap", "led_off", "lamp_lens", "yellow", "ext_plastic"),
    "MI_Cab_Leather": ("leather", "leather_wheel", "leather_centre"),
    "MI_Cab_Fabric": ("headliner", "wall_fabric", "mattress", "curtain", "seat_fabric", "blind", "webbing"),
    "MI_Cab_Rubber": ("floor_mat", "rubber"),
    "MI_Cab_Metal": ("satin", "scuff_plate", "chrome", "paint"),
    "MI_Cab_Decal": ("stitch", "stitch_dark", "icons", "grille", "grille_dash"),
    "MI_Cab_Glass": ("windscreen", "side_glass", "cover_glass"),
    "MI_Cab_Display": ("disp_cluster", "disp_info", "disp_din", "disp_gauges"),
    "MI_Cab_MirrorRT": ("mirror",),
}
SLOT = {m: s for s, ms in SLOT_OF.items() for m in ms}
DETAIL_SET = {"MI_Cab_Plastic": ("dashgrain", 1024), "MI_Cab_Leather": ("leather", 1024),
              "MI_Cab_Fabric": ("fabric", 512), "MI_Cab_Rubber": ("rubbermat", 1024), "MI_Cab_Metal": ("brushed", 512)}
WEAR_MUL = {"leather": 2.3, "leather_wheel": 1.6, "leather_centre": 1.5, "floor_mat": 2.4, "scuff_plate": 1.3}
NO_AO = ("curtain_", "blind_", "hatch_blind",     # thin interpenetrating cloth (critic #15) and the rim, which
         "wheel_rim", "wheel_stitch")           # rotates (a baked occlusion pattern would turn with it): median value

# ---------------------------------------------------------------- functional groups (draw calls, pivots)
def group_of(name):
    """Export object an authoring object belongs to (None = static cab)."""
    if name.startswith(("wheel_rim", "wheel_stitch", "spoke_", "wheel_hub", "hub_gap", "emblem")):
        return "STEERING_WHEEL"
    for k, g in (("stalk_left", "STALK_Indicator"), ("stalk_retarder", "STALK_Retarder"), ("stalk_amt", "STALK_AMT")):
        if name.startswith(k):
            return g
    if name.startswith(("brake_arm", "brake_pad")):
        return "PEDAL_Brake"
    if name.startswith("accel_pad"):
        return "PEDAL_Accel"
    if name.startswith(("pbrake_lever", "pbrake_knob", "pbrake_ring")):
        return "LEVER_ParkBrake"
    disp = {"cluster_screen": "DISPLAY_Cluster", "info_screen": "DISPLAY_Infotainment", "din_lcd_0": "DISPLAY_Tachograph",
            "din_lcd_1": "DISPLAY_Radio", "bunk_lcd": "DISPLAY_BunkPanel"}
    if name in disp:
        return disp[name]
    mirr = {"mirror_main_glass_-1": "MIRROR_MainL", "mirror_main_glass_1": "MIRROR_MainR",
            "mirror_wide_glass_-1": "MIRROR_WideL", "mirror_wide_glass_1": "MIRROR_WideR",
            "kerb_glass": "MIRROR_Kerb", "front_glass": "MIRROR_Front"}
    if name in mirr:
        return mirr[name]
    if name.startswith(("windscreen", "side_glass", "cluster_glass")):
        return "CAB_Glass"
    if name.startswith(("back_skin", "roof_skin", "skin_", "front_skin", "door_skin_", "bpillar_skin_", "apillar_skin_",
                        "wiper_", "mirror_", "kerb_arm", "kerb_head", "front_arm", "front_head", "ws_gasket_")):
        return "CAB_ShellPlaceholder"
    return "CAB_Interior"


def frames():
    """Pivot frames (origin, X, Y, Z axes in the A2 frame) of the animated parts."""
    n, u, v = BI.wheel_frame()
    C = BI.WHEEL_C
    base = C - n * 0.10
    piv = {"STEERING_WHEEL": (C, u, v, n)}
    for g, side, dz in (("STALK_Indicator", -1, 0.005), ("STALK_Retarder", 1, 0.022), ("STALK_AMT", 1, -0.018)):
        piv[g] = (base + u * (side * 0.06) + v * dz, u, v, n)
    X, Y, Z = V(1, 0, 0), V(0, 1, 0), V(0, 0, 1)
    piv["PEDAL_Brake"] = (V(BI.SEAT_X + 0.07, 1.33, 1.86), X, Y, Z)
    piv["PEDAL_Accel"] = (V(BI.SEAT_X + 0.235, 1.16, 1.42), X, Y, Z)
    x = -0.205
    piv["LEVER_ParkBrake"] = (V(x, BI.dash_face_y(x) - 0.004, 1.90) + V(0, -0.005, -0.03), X, Y, Z)
    return piv


ANIM_AXES = {  # rotation axes in the pivot's local frame (Blender local; Unity mapping in the manifest)
    "STEERING_WHEEL": {"steer": "Z"},
    "STALK_Indicator": {"up_down_indicators": "Z", "pull_flash_push_wipe": "Y"},
    "STALK_Retarder": {"steps_up_down": "Z"},
    "STALK_AMT": {"up_down_mode": "Z"},
    "PEDAL_Brake": {"press": "X"},
    "PEDAL_Accel": {"press": "X"},
    "LEVER_ParkBrake": {"pull": "X"},
}


def b2u(v):
    """A2/Blender frame vector -> Unity (left-handed, Y up, +Z forward): (x, z, y)."""
    return [round(v[0], 5), round(v[2], 5), round(v[1], 5)]


# ---------------------------------------------------------------- helpers
def select(objs, active=None):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = active or (objs[0] if objs else None)


def tris_of(o):
    me = o.data
    me.calc_loop_triangles()
    return len(me.loop_triangles)


def apply_modifiers(objs):
    dg = bpy.context.evaluated_depsgraph_get()
    for o in objs:
        if o.type != "MESH" or not o.modifiers:
            continue
        me = bpy.data.meshes.new_from_object(o.evaluated_get(dg), preserve_all_data_layers=True, depsgraph=dg)
        old = o.data
        o.modifiers.clear()
        o.data = me
        if old.users == 0:
            bpy.data.meshes.remove(old)


def bake_transforms(objs):
    """Put every authoring object's world matrix into its mesh (identity object transforms)."""
    for o in objs:
        if o.type == "MESH" and o.matrix_world != Matrix.Identity(4):
            o.data.transform(o.matrix_world)
            o.matrix_world = Matrix.Identity(4)


def viewpoints():
    E = BI.EYE
    pts = []
    for dx in (-0.12, 0.0, 0.12):          # driver head box (seat travel, lean, look-around)
        for dy in (-0.12, 0.0, 0.10):
            for dz in (-0.08, 0.0, 0.06):
                pts.append(E + V(dx, dy, dz))
    P = V(-E.x, E.y, E.z - 0.02)
    pts += [P + V(dx, dy, 0) for dx in (-0.1, 0.1) for dy in (-0.1, 0.1)]
    pts += [V(x, y, z) for x in (-0.8, 0.0, 0.8) for y in (-0.55, -0.25) for z in (2.10, 2.35)]   # bunk
    pts += [V(x, y, 2.95) for x in (-0.5, 0.0, 0.5) for y in (-0.2, 0.35, 0.75)]                    # standing
    pts += [V(s * 0.55, 0.62, 1.85) for s in (-1, 1)] + [V(0, 0.4, 1.7), V(-0.9, 0.4, 2.0)]       # footwells
    for loc, _t, _f in BI.cameras().values():
        pts.append(V(loc))
    for k in range(16):                    # exterior ring through the glass (chase / free cameras)
        a = 2 * math.pi * k / 16
        for r, z in ((4.5, 2.6), (6.5, 3.6)):
            pts.append(V(r * math.sin(a), 0.4 + r * math.cos(a), z))
    pts.append(V(0, 9.0, 4.5))
    return pts


def remove_hidden(objs, keep):
    """Delete faces that no view point can see (closed-volume caps, faces pressed against walls, undersides)."""
    occl = [o for o in objs if o.type == "MESH" and not o.name.startswith(("windscreen", "side_glass", "cluster_glass"))
            and not o.get("decal")]
    verts, polys, owner = [], [], []
    for o in occl:
        me = o.data
        base = len(verts)
        verts.extend(v.co.copy() for v in me.vertices)
        for p in me.polygons:
            polys.append([base + i for i in p.vertices])
            owner.append((o.name, p.index))
    bvh = BVHTree.FromPolygons(verts, polys, epsilon=0.0)
    vps = viewpoints()
    import random
    rng = random.Random(6)
    removed = 0
    total = 0
    for o in objs:
        if o.type != "MESH" or o.name in keep or o.get("decal") or o.get("fixed_uv"):
            continue
        me = o.data
        bm = bmesh.new()
        bm.from_mesh(me)
        bm.faces.ensure_lookup_table()
        dead = []
        for f in bm.faces:
            total += 1
            c = f.calc_center_median()
            nrm = f.normal
            # centre, near each corner, and area-proportional random points (large caps partly covered by bezels and
            # switches must not lose their visible parts)
            samples = [c] + [c.lerp(v.co, k) for v in f.verts for k in (0.8, 0.97)]
            vs = [v.co for v in f.verts]
            extra = min(40, int(f.calc_area() / 0.0002))
            for _ in range(extra):
                i = rng.randrange(1, len(vs) - 1)
                r1, r2 = rng.random(), rng.random()
                if r1 + r2 > 1:
                    r1, r2 = 1 - r1, 1 - r2
                samples.append(vs[0] + (vs[i] - vs[0]) * r1 + (vs[i + 1] - vs[0]) * r2)
            seen = False
            for vp in vps:
                for s in samples:
                    sp = s + nrm * 0.0015
                    d = vp - sp
                    L = d.length
                    if L < 1e-6 or d.dot(nrm) <= 0:
                        continue
                    hit = bvh.ray_cast(sp, d / L, L)
                    if hit[0] is None:
                        seen = True
                        break
                if seen:
                    break
            if not seen:
                # conservative: cull only faces that are also covered (something within 5 cm in front of them:
                # pressed against a wall, buried in a volume, resting on the floor); unseen faces in open air stay
                cov = bvh.ray_cast(c + nrm * 0.0015, nrm, 0.05)
                if cov[0] is not None:
                    dead.append(f)
        if dead:
            removed += len(dead)
            bmesh.ops.delete(bm, geom=dead, context="FACES")
            bm.to_mesh(me)
        bm.free()
    return removed, total


# ---------------------------------------------------------------- material consolidation
_MEAN_G = {}


def mean_rough(tset):
    if tset not in _MEAN_G:
        im = bpy.data.images.load(os.path.join(M.TEX, f"{tset}_orm.png"), check_existing=True)
        px = np.empty(len(im.pixels), dtype=np.float32)
        im.pixels.foreach_get(px)
        _MEAN_G[tset] = float(px.reshape(-1, 4)[:, 1].mean())
    return _MEAN_G[tset]


def slot_material(slot):
    m = bpy.data.materials.get(slot) or bpy.data.materials.new(slot)
    m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    col = {"MI_Cab_Plastic": (0.06, 0.06, 0.06), "MI_Cab_Leather": (0.04, 0.04, 0.04), "MI_Cab_Fabric": (0.2, 0.2, 0.2),
           "MI_Cab_Rubber": (0.04, 0.04, 0.04), "MI_Cab_Metal": (0.5, 0.5, 0.5), "MI_Cab_Decal": (0.6, 0.6, 0.6),
           "MI_Cab_Glass": (0.8, 0.85, 0.85), "MI_Cab_Display": (0.02, 0.02, 0.02), "MI_Cab_MirrorRT": (0.9, 0.9, 0.9)}[slot]
    if b:
        b.inputs["Base Color"].default_value = (*col, 1)
    return m


def decal_uv(mname, uv):
    """Remap a decal's UV into the decal atlas bands (v up): stitch 0.88-0.995 (tiles in U), grille 0.505-0.87
    (tiles in U), icons 0.005-0.495 (8 x 4 cells)."""
    u, v = uv
    if mname.startswith("stitch"):
        return (u, 0.88 + 0.115 * min(max(v, 0.0), 1.0))
    if mname.startswith("grille"):
        return (u, 0.505 + 0.365 * min(max(v, 0.0), 1.0))
    return (u, 0.005 + 0.49 * min(max(v, 0.0), 1.0))


def consolidate(objs):
    """Write the vertex-data contract and swap authoring materials for slot materials (per face)."""
    slots = {s: slot_material(s) for s in SLOT_OF}
    for o in objs:
        if o.type != "MESH":
            continue
        me = o.data
        if not me.polygons:
            continue
        if "UVMap" not in me.uv_layers:
            me.uv_layers.new(name="UVMap")
        if "Bake" not in me.uv_layers:
            me.uv_layers.new(name="Bake")
        for nm in ("Data0", "Data1"):
            if nm not in me.uv_layers:
                me.uv_layers.new(name=nm)
        col = me.color_attributes.get("Col") or me.color_attributes.new("Col", "FLOAT_COLOR", "CORNER")
        wear = me.attributes.get("wear")
        uv0 = me.uv_layers["UVMap"].data
        d0 = me.uv_layers["Data0"].data
        d1 = me.uv_layers["Data1"].data
        mats = [s.material for s in o.material_slots]
        new_index = []
        for mat in mats:
            nm = mat.name if mat else "gap"
            new_index.append(list(SLOT_OF).index(SLOT.get(nm, "MI_Cab_Plastic")))
        for p in me.polygons:
            mat = mats[p.material_index] if mats else None
            nm = mat.name if mat else "gap"
            prm = M.PARAMS.get(nm, {"kind": "simple", "tint": (0.05, 0.05, 0.05), "rough": 0.6, "metal": 0.0})
            slot = SLOT.get(nm, "MI_Cab_Plastic")
            if prm["kind"] == "pbr":
                rough = prm["rough_add"] + prm["rough_mul"] * mean_rough(prm["tset"])
                strength = min(1.0, prm["nstr"] / 1.25)
                tile = prm["tile"]
                metal = prm["metal"]
                perf = 1.0 if prm.get("perforate") else 0.0
            else:
                rough, strength, tile, metal, perf = prm.get("rough", 0.6), 0.0, 1.0, prm.get("metal", 0.0), 0.0
            tint = prm["tint"]
            for li in p.loop_indices:
                vi = me.loops[li].vertex_index
                col.data[li].color = (tint[0], tint[1], tint[2], max(0.02, min(1.0, rough)))
                w = wear.data[vi].value if wear else 0.0
                wm = WEAR_MUL.get(nm, 1.0)
                d0[li].uv = (w * (wm - 1.0) / 1.5 if wm > 1.0 else 0.0, strength)
                d1[li].uv = (perf, metal)
                if slot == "MI_Cab_Decal":
                    uv0[li].uv = decal_uv(nm, tuple(uv0[li].uv))
                elif not o.get("fixed_uv"):
                    uv0[li].uv = (uv0[li].uv[0] / (BI_UVK * tile), uv0[li].uv[1] / (BI_UVK * tile))
        # material slots -> slot materials
        me.materials.clear()
        for s in SLOT_OF:
            me.materials.append(slots[s])
        for p in me.polygons:
            if mats:
                p.material_index = new_index[p.material_index]
    return slots


BI_UVK = 1.0  # UVMap scale: build_interior writes UVMap in metres (k from auto_uv applied) -> 1.0


# ---------------------------------------------------------------- UV1 (AO atlas) layout
def texel_weight(name):
    hi = ("dash_main", "binnacle", "wheel_", "spoke_", "door_trim", "door_sill", "door_armrest", "apillar_trim",
          "drv_", "stack_", "door_insert", "dash_insert", "dash_tray", "column_shroud")
    lo = ("bunk_base", "drawer_", "rear_oh", "rear_lid", "upper_bunk", "floor_slab", "back_wall", "side_rear",
          "footwell_wall", "_bellows", "_base", "_rail", "_pan", "skin", "roof_", "mirror_", "kerb_", "front_")
    if name.startswith(lo) or any(k in name for k in ("skin", "_bellows", "_rail_")):
        return 0.45
    if name.startswith(hi):
        return 1.6
    return 1.0


def layout_bake_uv(objs, receivers):
    for o in objs:
        o.data.uv_layers.active = o.data.uv_layers["Bake"]
    rec = [o for o in receivers if len(o.data.polygons)]
    select(rec)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(60), island_margin=0.0, area_weight=0.0, correct_aspect=True,
                             scale_to_bounds=False)
    bpy.ops.object.mode_set(mode="OBJECT")
    for o in rec:  # uniform density, then texel priority
        me = o.data
        uv = me.uv_layers["Bake"].data
        a3 = sum(p.area for p in me.polygons)
        auv = 0.0
        for p in me.polygons:
            pts = [uv[li].uv for li in p.loop_indices]
            for i in range(1, len(pts) - 1):
                auv += abs((pts[i] - pts[0]).cross(pts[i + 1] - pts[0])) / 2
        k = math.sqrt(a3 / max(auv, 1e-12)) * texel_weight(o["src"] if "src" in o else o.name)
        for d in uv:
            d.uv = d.uv * k
    select(rec)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.select_all(action="SELECT")
    bpy.ops.uv.pack_islands(udim_source="CLOSEST_UDIM", rotate=True, scale=True, margin_method="FRACTION",
                            margin=0.003, shape_method="CONCAVE")
    bpy.ops.object.mode_set(mode="OBJECT")
    for o in rec:
        for d in o.data.uv_layers["Bake"].data:
            d.uv = d.uv * 0.985
    for o in objs:   # non-receivers -> neutral block (glass, displays, mirrors), cloth block, or marked for transfer
        if o in rec:
            continue
        g = group_of(o.name)
        transfer = (o.get("decal") or o.get("fixed_uv")) and not o.name.startswith(NO_AO)             and g != "CAB_Glass" and not g.startswith(("DISPLAY_", "MIRROR_"))
        tgt = (0.999, 0.9785) if o.name.startswith(NO_AO) else (0.999, 0.999)
        for d in o.data.uv_layers["Bake"].data:
            d.uv = tgt
        if transfer:
            at = o.data.attributes.get("uv1_transfer") or o.data.attributes.new("uv1_transfer", "INT", "FACE")
            for d in at.data:
                d.value = 1
    for o in objs:
        o.data.uv_layers.active = o.data.uv_layers["UVMap"]


def transfer_decal_uv1(obs):
    """After the bake: decal faces (stitches, seams, icons, grilles, belt webbing) take the UV1 of the nearest
    receiver triangle, so they inherit the occlusion of the surface right under them (instead of glowing under the
    full sky ambient in URP)."""
    from mathutils.interpolate import poly_3d_calc
    tv, tp, tri_uv = [], [], []
    for o in obs:
        me = o.data
        at = me.attributes.get("uv1_transfer")
        me.calc_loop_triangles()
        uv = me.uv_layers["Bake"].data
        mw = o.matrix_world
        for t in me.loop_triangles:
            if at and at.data[t.polygon_index].value:
                continue
            base = len(tv)
            tv.extend(mw @ me.vertices[i].co for i in t.vertices)
            tp.append((base, base + 1, base + 2))
            tri_uv.append([uv[li].uv.copy() for li in t.loops])
    bvh = BVHTree.FromPolygons(tv, tp, epsilon=0.0)
    n = 0
    for o in obs:
        me = o.data
        at = me.attributes.get("uv1_transfer")
        if not at:
            continue
        uv = me.uv_layers["Bake"].data
        mw = o.matrix_world
        for p in me.polygons:
            if not at.data[p.index].value:
                continue
            for li in p.loop_indices:
                co = mw @ me.vertices[me.loops[li].vertex_index].co
                hit = bvh.find_nearest(co, 0.03)
                if hit[0] is None:
                    continue
                k = hit[2]
                w = poly_3d_calc([tv[i] for i in tp[k]], hit[0])
                uv[li].uv = sum((tri_uv[k][j] * w[j] for j in range(3)), Vector((0.0, 0.0)))
                n += 1
        me.attributes.remove(at)
    return n


def bake_ao(receivers, hide, res, samples, distance, out_png):
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
    sc.cycles.samples = samples
    sc.cycles.max_bounces = 6
    sc.cycles.diffuse_bounces = 4
    sc.cycles.glossy_bounces = 0
    sc.cycles.sample_clamp_indirect = 4.0
    w = bpy.data.worlds.new("bake_white")       # uniform white sky, strength 1 -> open upward surface = 1.0
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs["Color"].default_value = (1, 1, 1, 1)
    w.node_tree.nodes["Background"].inputs["Strength"].default_value = 1.0
    sc.world = w
    for o in bpy.data.objects:
        if o.type == "LIGHT":
            o.hide_render = True
    img = bpy.data.images.new("ao_bake", res, res, alpha=True, float_buffer=True, is_data=True)
    img.generated_color = (0, 0, 0, 0)
    for o in hide:
        o.hide_render = True
    mats = set()
    for o in receivers:
        o.data.uv_layers.active = o.data.uv_layers["Bake"]
        for s in o.material_slots:
            mats.add(s.material)
    for m in mats:   # bounce colour = the real per-face albedo (vertex tint), not the slot placeholder
        nt = m.node_tree
        b = nt.nodes.get("Principled BSDF")
        if b and not b.inputs["Base Color"].links:
            vc = nt.nodes.new("ShaderNodeVertexColor")
            vc.layer_name = "Col"
            vc.name = "BAKE_VC"
            nt.links.new(vc.outputs["Color"], b.inputs["Base Color"])
        n = nt.nodes.new("ShaderNodeTexImage")
        n.image = img
        n.name = "BAKE_TARGET"
        nt.nodes.active = n
    select(receivers)
    sc.render.bake.margin = 6
    sc.render.bake.margin_type = "EXTEND"
    t = time.time()
    bpy.ops.object.bake(type="DIFFUSE", pass_filter={"DIRECT", "INDIRECT"})
    print("cab ambient baked", res, samples, "spp in", round(time.time() - t, 1), "s")
    for m in mats:
        nt = m.node_tree
        nt.nodes.remove(nt.nodes["BAKE_TARGET"])
        if "BAKE_VC" in nt.nodes:
            nt.nodes.remove(nt.nodes["BAKE_VC"])
    for o in hide:
        o.hide_render = False
    for o in receivers:
        o.data.uv_layers.active = o.data.uv_layers["UVMap"]
    px = np.empty(res * res * 4, dtype=np.float32)
    img.pixels.foreach_get(px)
    a = px.reshape(res, res, 4)
    ao, cov = a[..., 0].copy(), (a[..., 3] > 0.5).astype(np.float32)
    # denoise inside islands: normalised Gaussian (sigma ~1.2 px), never across empty texels
    k = np.exp(-0.5 * (np.arange(-4, 5) / 2.6) ** 2).astype(np.float32)
    k /= k.sum()

    def blur(x):
        for _ in range(2):
            x = sum(w * np.roll(x, i - 4, axis=0) for i, w in enumerate(k))
            x = sum(w * np.roll(x, i - 4, axis=1) for i, w in enumerate(k))
        return x
    num, den = blur(ao * cov), blur(cov)
    den_ok = den > 1e-3
    ao = np.where((cov > 0) & den_ok, num / np.maximum(den, 1e-3), ao)
    ao = np.clip(ao, 0, 1)
    filled = cov > 0
    for _ in range(12):                    # dilation for mip safety
        if filled.all():
            break
        acc = np.zeros_like(ao)
        cnt = np.zeros_like(ao)
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            acc += np.roll(np.roll(ao * filled, dy, 0), dx, 1)
            cnt += np.roll(np.roll(filled.astype(np.float32), dy, 0), dx, 1)
        grow = (~filled) & (cnt > 0)
        ao = np.where(grow, acc / np.maximum(cnt, 1), ao)
        filled = filled | grow
    ao[~filled] = 1.0
    blk = max(4, res // 128)
    cloth = float(np.median(ao[cov > 0])) if (cov > 0).any() else 0.4
    ao[-blk:, -blk:] = 1.0                 # neutral block: glass, decals, displays, mirrors
    ao[-3 * blk:-2 * blk, -blk:] = cloth   # cloth block: curtains / blinds get the median cab ambient
    bpy.data.images.remove(img)
    return ao


def save_gray(arr, path, size=None):
    res = arr.shape[0]
    im = bpy.data.images.new(os.path.basename(path), res, res, alpha=False, float_buffer=False, is_data=True)
    rgba = np.ones((res, res, 4), np.float32)
    rgba[..., 0] = rgba[..., 1] = rgba[..., 2] = arr
    im.pixels.foreach_set(rgba.ravel())
    if size and size != res:
        im.scale(size, size)
    im.filepath_raw = path
    im.file_format = "PNG"
    im.save()
    bpy.data.images.remove(im)


# ---------------------------------------------------------------- joining, pivots, hierarchy
def join_groups(objs):
    groups = {}
    for o in objs:
        if o.type == "MESH" and len(o.data.polygons):
            o["src"] = o.name
            groups.setdefault(group_of(o.name), []).append(o)
    out = {}
    for g, members in groups.items():
        select(members, members[0])
        if len(members) > 1:
            bpy.ops.object.join()
        ob = bpy.context.view_layer.objects.active
        ob.name = g
        ob.data.name = g
        out[g] = ob
    return out


def set_pivot(ob, origin, X, Y, Z):
    R = Matrix((X, Y, Z)).transposed().to_4x4()
    T = Matrix.Translation(origin) @ R
    ob.data.transform(T.inverted())
    ob.matrix_world = T


def finalize_mesh(ob):
    """Triangulate (exact tri counts, stable tangents), drop unused slots, clear custom attributes not exported."""
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bmesh.ops.triangulate(bm, faces=bm.faces[:], quad_method="BEAUTY", ngon_method="BEAUTY")
    bm.to_mesh(ob.data)
    bm.free()
    used = sorted({p.material_index for p in ob.data.polygons})
    mats = [ob.data.materials[i] for i in used]
    remap = {i: k for k, i in enumerate(used)}
    idx = [remap[p.material_index] for p in ob.data.polygons]
    ob.data.materials.clear()
    for m in mats:
        ob.data.materials.append(m)
    for p, i in zip(ob.data.polygons, idx):
        p.material_index = i
    if "wear" in ob.data.attributes:
        ob.data.attributes.remove(ob.data.attributes["wear"])
    ob.data.color_attributes.active_color = ob.data.color_attributes["Col"]


# ---------------------------------------------------------------- textures per tier
def tex_image(fname):
    im = bpy.data.images.load(os.path.join(M.TEX, fname), check_existing=True)
    px = np.empty(len(im.pixels), dtype=np.float32)
    im.pixels.foreach_get(px)
    return px.reshape(im.size[1], im.size[0], 4)


def write_rgba(arr, path, size):
    h, w = arr.shape[:2]
    im = bpy.data.images.new(os.path.basename(path), w, h, alpha=True, float_buffer=False, is_data=True)
    im.pixels.foreach_set(arr.astype(np.float32).ravel())
    if size != w:
        im.scale(size, max(1, int(size * h / w)))
    im.filepath_raw = path
    im.file_format = "PNG"
    im.save()
    bpy.data.images.remove(im)


def build_textures(out_dir):
    """Per slot: _Detail (R variation, G micro-AO, B roughness, A perforation/extra) + _Normal (OpenGL, +Y up);
    decal atlas (RGBA, A = coverage); display placeholders; glass grime. Sizes per tier (power of two, ASTC 4x4..8x8)."""
    written = {}
    perf = tex_image("perforation_mask.png")[..., 0]
    for slot, (tset, base) in DETAIL_SET.items():
        var = tex_image(f"{tset}_var.png")
        orm = tex_image(f"{tset}_orm.png")
        nrm = tex_image(f"{tset}_nrm.png")
        h = var.shape[0]
        det = np.ones((h, h, 4), np.float32)
        det[..., 0] = var[..., 0]
        det[..., 1] = orm[..., 0]
        det[..., 2] = orm[..., 1]
        if slot == "MI_Cab_Leather":   # perforation (4 cm tile) baked 3 x 3 into the 12 cm leather tile
            ph = perf.shape[0]
            yy, xx = np.meshgrid(np.arange(h), np.arange(h), indexing="ij")
            det[..., 3] = perf[(yy * 3 * ph // h) % ph, (xx * 3 * ph // h) % ph]
        for tier, f in TIERS.items():
            size = max(128, int(base * f))
            d = os.path.join(out_dir, tier)
            os.makedirs(d, exist_ok=True)
            p1 = os.path.join(d, f"T_{slot[3:]}_Detail.png")
            p2 = os.path.join(d, f"T_{slot[3:]}_Normal.png")
            write_rgba(det, p1, size)
            write_rgba(nrm, p2, size)
            written.setdefault(slot, {})[tier] = {"detail": p1, "normal": p2, "size": size}
    # decal atlas 1024: icons band (bottom), grille band, stitch band (top)
    A = 1024
    atlas = np.zeros((A, A, 4), np.float32)
    atlas[..., :3] = 1.0
    ic = tex_image("icons_atlas.png")
    gr = tex_image("grille_mask.png")
    st = tex_image("stitch_rgba.png")

    def put(src, v0, v1, alpha_from):
        rows = int(round(v1 * A)) - int(round(v0 * A))
        ys = np.linspace(0, src.shape[0] - 1, rows).astype(int)
        xs = np.linspace(0, src.shape[1] - 1, A).astype(int)
        blk = src[ys][:, xs]
        r0 = int(round(v0 * A))
        alpha = blk[..., 3] if alpha_from == "alpha" else blk[..., 0]
        atlas[r0:r0 + rows, :, 3] = alpha
        if alpha_from == "alpha":
            atlas[r0:r0 + rows, :, :3] = blk[..., :3]
    put(ic, 0.005, 0.495, "mask")
    put(gr, 0.505, 0.87, "mask")
    put(st, 0.88, 0.995, "alpha")
    for tier, f in TIERS.items():
        p = os.path.join(out_dir, tier, "T_Cab_Decal.png")
        write_rgba(atlas, p, max(256, int(A * f)))
        written.setdefault("MI_Cab_Decal", {})[tier] = {"atlas": p, "size": max(256, int(A * f))}
    gm = tex_image("grime_mask.png")
    for tier, f in TIERS.items():
        p = os.path.join(out_dir, tier, "T_Cab_GlassGrime.png")
        write_rgba(gm, p, max(128, int(512 * f)))
        written.setdefault("MI_Cab_Glass", {})[tier] = {"grime": p, "size": max(128, int(512 * f))}
    dd = os.path.join(out_dir, "Displays")
    os.makedirs(dd, exist_ok=True)
    for f in ("display_cluster.png", "display_infotainment.png", "display_din.png"):
        shutil.copy(os.path.join(M.TEX, f), os.path.join(dd, "T_" + f.replace("display_", "Display_")))
    return written


# ---------------------------------------------------------------- preview of the game material contract
def preview_materials(slot_textures, ao_path):
    """Blender (EEVEE) implementation of the shader contract for the URP-like control renders."""
    ao_img = bpy.data.images.load(ao_path, check_existing=True)
    ao_img.colorspace_settings.name = "Non-Color"
    for slot in ("MI_Cab_Plastic", "MI_Cab_Leather", "MI_Cab_Fabric", "MI_Cab_Rubber", "MI_Cab_Metal"):
        m = bpy.data.materials[slot]
        nt = m.node_tree
        for n in list(nt.nodes):
            nt.nodes.remove(n)
        out = nt.nodes.new("ShaderNodeOutputMaterial")
        b = nt.nodes.new("ShaderNodeBsdfPrincipled")
        nt.links.new(b.outputs[0], out.inputs["Surface"])

        def uvn(name):
            n = nt.nodes.new("ShaderNodeUVMap")
            n.uv_map = name
            return n.outputs["UV"]

        def tex(path, uv, noncolor=True):
            t = nt.nodes.new("ShaderNodeTexImage")
            t.image = bpy.data.images.load(path, check_existing=True)
            t.image.colorspace_settings.name = "Non-Color"
            nt.links.new(uv, t.inputs["Vector"])
            return t
        tt = slot_textures[slot]["High"]
        det = tex(tt["detail"], uvn("UVMap"))
        nrm = tex(tt["normal"], uvn("UVMap"))
        aot = nt.nodes.new("ShaderNodeTexImage")
        aot.image = ao_img
        nt.links.new(uvn("Bake"), aot.inputs["Vector"])
        col = nt.nodes.new("ShaderNodeVertexColor")
        col.layer_name = "Col"
        sep = nt.nodes.new("ShaderNodeSeparateColor")
        nt.links.new(det.outputs["Color"], sep.inputs[0])
        d0 = nt.nodes.new("ShaderNodeSeparateXYZ")
        nt.links.new(uvn("Data0"), d0.inputs[0])
        d1 = nt.nodes.new("ShaderNodeSeparateXYZ")
        nt.links.new(uvn("Data1"), d1.inputs[0])
        mixw = M._math(nt, "GREATER_THAN", d0.outputs["Y"], 0.001)                     # detailMix
        var = M._math(nt, "MULTIPLY_ADD", sep.outputs[0], 0.6)
        var.node.inputs[2].default_value = 0.7
        mao = M._math(nt, "MULTIPLY_ADD", sep.outputs[1], 0.6)
        mao.node.inputs[2].default_value = 0.4
        dmul = M._math(nt, "MULTIPLY", var, mao)
        f = M._math(nt, "ADD", M._math(nt, "MULTIPLY", M._math(nt, "SUBTRACT", dmul, 1.0), mixw), 1.0)
        perf = M._math(nt, "ADD", M._math(nt, "MULTIPLY", M._math(nt, "SUBTRACT", det.outputs["Alpha"], 1.0), d1.outputs["X"]), 1.0)
        wearf = M._math(nt, "MULTIPLY_ADD", d0.outputs["X"], 1.5)
        wearf.node.inputs[2].default_value = 1.0
        k = M._math(nt, "MULTIPLY", M._math(nt, "MULTIPLY", f, perf), wearf)
        base = M._mix_rgb(nt, 1.0, col.outputs["Color"], k, "MULTIPLY")
        nt.links.new(base, b.inputs["Base Color"])
        amb = M._mix_rgb(nt, 1.0, base, ambient_node(nt), "MULTIPLY")
        amb = M._mix_rgb(nt, 1.0, amb, aot.outputs["Color"], "MULTIPLY")      # URP: occlusion on ambient only
        # metals have no diffuse: their ambient is the (occluded) reflection probe; approximated as a dim term
        mf = M._math(nt, "MULTIPLY_ADD", d1.outputs["Y"], -0.8)
        mf.node.inputs[2].default_value = 1.0
        amb = M._mix_rgb(nt, 1.0, amb, mf, "MULTIPLY")
        nt.links.new(amb, b.inputs["Emission Color"])
        b.inputs["Emission Strength"].default_value = 1.0
        r = M._math(nt, "MULTIPLY_ADD", M._math(nt, "SUBTRACT", sep.outputs[2], 0.5), M._math(nt, "MULTIPLY", mixw, 0.4))
        nt.links.new(col.outputs["Alpha"], r.node.inputs[2])
        r = M._math(nt, "SUBTRACT", r, M._math(nt, "MULTIPLY", M._math(nt, "MINIMUM", wearf, 2.0), 0.0))
        nt.links.new(M._math(nt, "MINIMUM", M._math(nt, "MAXIMUM", r, 0.04), 1.0), b.inputs["Roughness"])
        nt.links.new(d1.outputs["Y"], b.inputs["Metallic"])
        nm = nt.nodes.new("ShaderNodeNormalMap")
        nm.uv_map = "UVMap"
        nt.links.new(nrm.outputs["Color"], nm.inputs["Color"])
        nt.links.new(M._math(nt, "MULTIPLY", d0.outputs["Y"], 1.25), nm.inputs["Strength"])
        nt.links.new(nm.outputs["Normal"], b.inputs["Normal"])
        b.inputs["Specular IOR Level"].default_value = 0.35
    # decals
    m = bpy.data.materials["MI_Cab_Decal"]
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(b.outputs[0], out.inputs["Surface"])
    t = nt.nodes.new("ShaderNodeTexImage")
    t.image = bpy.data.images.load(slot_textures["MI_Cab_Decal"]["High"]["atlas"], check_existing=True)
    uvn_ = nt.nodes.new("ShaderNodeUVMap")
    uvn_.uv_map = "UVMap"
    nt.links.new(uvn_.outputs["UV"], t.inputs["Vector"])
    col = nt.nodes.new("ShaderNodeVertexColor")
    col.layer_name = "Col"
    nt.links.new(M._mix_rgb(nt, 1.0, col.outputs["Color"], t.outputs["Color"], "MULTIPLY"), b.inputs["Base Color"])
    nt.links.new(t.outputs["Alpha"], b.inputs["Alpha"])
    b.inputs["Roughness"].default_value = 0.6
    m.blend_method = "CLIP"
    # glass: thin, mostly transparent, Fresnel reflection, no shadow
    m = bpy.data.materials["MI_Cab_Glass"]
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    tr.inputs["Color"].default_value = (0.90, 0.93, 0.92, 1)
    gl = nt.nodes.new("ShaderNodeBsdfGlossy")
    gl.inputs["Roughness"].default_value = 0.02
    fr = nt.nodes.new("ShaderNodeLayerWeight")
    fr.inputs["Blend"].default_value = 0.08
    mx = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(fr.outputs["Fresnel"], mx.inputs[0])
    nt.links.new(tr.outputs[0], mx.inputs[1])
    nt.links.new(gl.outputs[0], mx.inputs[2])
    nt.links.new(mx.outputs[0], out.inputs["Surface"])
    m.blend_method = "BLEND"
    try:
        m.use_transparent_shadow = True
    except AttributeError:
        pass
    # displays: emissive placeholders (runtime render textures in the game)
    m = bpy.data.materials["MI_Cab_Display"]
    for ob in bpy.data.objects:
        if ob.name.startswith("DISPLAY_"):
            src = {"DISPLAY_Cluster": "disp_cluster", "DISPLAY_Infotainment": "disp_info"}.get(ob.name.rsplit("_LOD", 1)[0],
                                                                                              "disp_din")
            ob.data.materials[0] = bpy.data.materials[src]
    m = bpy.data.materials["MI_Cab_MirrorRT"]
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (0.85, 0.86, 0.87, 1)
    b.inputs["Metallic"].default_value = 1.0
    b.inputs["Roughness"].default_value = 0.02


AMB = {"overcast": ((0.76, 0.78, 0.82), 1.35, 0.15), "lowsun": ((0.48, 0.47, 0.47), 0.30, 0.20)}
AMB_KIND = ["overcast"]


def ambient_node(nt):
    """SH-like ambient of the sky for the URP emulation: E(n) ~ sky colour * strength * lerp(ground, 1, up-ness)."""
    col, strength, ground = AMB[AMB_KIND[0]]
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(geo.outputs["Normal"], sep.inputs[0])
    up = M._math(nt, "MULTIPLY_ADD", sep.outputs["Z"], 0.5)
    up.node.inputs[2].default_value = 0.5
    f = M._math(nt, "MULTIPLY_ADD", up, 1.0 - ground)
    f.node.inputs[2].default_value = ground
    return M._mix_rgb(nt, 1.0, tuple(c * strength for c in col), f, "MULTIPLY")


def add_ambient_to_backdrop(skip):
    """Backdrop materials get the same explicit ambient term (world lighting is off in the URP emulation)."""
    for m in bpy.data.materials:
        if m.name in skip or not m.use_nodes or m.name.startswith(("disp_", "sky_dome", "MI_Cab_Glass")):
            continue
        if m.name.startswith("MI_Cab") and m.name != "MI_Cab_Decal":
            continue
        nt = m.node_tree
        for b in [n for n in nt.nodes if n.type == "BSDF_PRINCIPLED"]:
            ln = b.inputs["Emission Color"].links
            if ln and ln[0].from_node.label == "AMB":
                nt.nodes.remove(ln[0].from_node)
            elif ln or b.inputs["Emission Strength"].default_value > 0:
                continue
            src = (b.inputs["Base Color"].links[0].from_socket if b.inputs["Base Color"].links
                   else tuple(b.inputs["Base Color"].default_value)[:3])
            mix = M._mix_rgb(nt, 1.0, src, ambient_node(nt), "MULTIPLY")
            mix.node.label = "AMB"
            nt.links.new(mix, b.inputs["Emission Color"])
            b.inputs["Emission Strength"].default_value = 1.0


def sky_dome(kind):
    """Visible sky on a big emissive sphere (EEVEE without light probes: emission adds no light to the scene)."""
    me = bpy.data.meshes.new("sky_dome")
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=48, v_segments=24, radius=1400.0)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new("sky_dome", me)
    bpy.context.scene.collection.objects.link(ob)
    m = bpy.data.materials.new("sky_dome")
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    nrm = nt.nodes.new("ShaderNodeVectorMath")
    nrm.operation = "NORMALIZE"
    nt.links.new(geo.outputs["Position"], nrm.inputs[0])
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(nrm.outputs[0], sep.inputs[0])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    if kind == "overcast":
        z = M._math(nt, "MULTIPLY_ADD", sep.outputs["Z"], 0.5)
        z.node.inputs[2].default_value = 0.5
        ramp.color_ramp.elements[0].color = (0.60, 0.61, 0.62, 1)
        ramp.color_ramp.elements[1].position = 0.6
        ramp.color_ramp.elements[1].color = (0.80, 0.82, 0.86, 1)
        strength = 1.35
    else:
        z = M._math(nt, "MULTIPLY_ADD", sep.outputs["Z"], 0.5)
        z.node.inputs[2].default_value = 0.5
        ramp.color_ramp.elements[0].position = 0.5
        ramp.color_ramp.elements[0].color = (0.62, 0.56, 0.48, 1)
        ramp.color_ramp.elements[1].position = 0.8
        ramp.color_ramp.elements[1].color = (0.30, 0.40, 0.55, 1)
        strength = 0.30
    nt.links.new(z, ramp.inputs[0])
    em = nt.nodes.new("ShaderNodeEmission")
    nt.links.new(ramp.outputs[0], em.inputs["Color"])
    em.inputs["Strength"].default_value = strength
    nt.links.new(em.outputs[0], out.inputs["Surface"])
    me.materials.append(m)
    ob.visible_shadow = False
    return ob


def setup_urp_like(kind, res):
    """'URP-like' preview = URP's lighting model, emulated in EEVEE: direct light (sun, shadow map) + ambient from an
    SH-like sky term x baked occlusion; no bounce/GI, no SSAO, no screen-space or probe reflections; HDR-free gradient
    sky. World lighting is black; the sky is seen on an emissive dome. AgX, same exposure as the Cycles renders."""
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_EEVEE_NEXT"
    e = sc.eevee
    e.use_raytracing = False
    e.use_gtao = False
    e.use_shadows = True
    e.use_soft_shadows = True
    e.taa_render_samples = 32
    sc.render.resolution_x, sc.render.resolution_y = (int(v) for v in res.split("x"))
    sc.render.image_settings.file_format = "JPEG"
    sc.render.image_settings.quality = 88
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.look = "None"
    BI.set_lighting(kind)                       # sun lamp + exposure as in the Cycles renders
    w = bpy.data.worlds.new("urp_black")
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.0
    sc.world = w
    for o in [o for o in bpy.data.objects if o.name.startswith("sky_dome")]:
        bpy.data.objects.remove(o)
    sky_dome(kind)


# ---------------------------------------------------------------- per LOD
def process_lod(lod, a, out_dir, manifest):
    t0 = time.time()
    sys_argv = sys.argv
    sys.argv = [sys_argv[0], "--", "--out", os.path.join(BI.REPO, "artifacts"), "--lod", str(lod), "--no-backdrop"]
    ba = BI.parse_args()
    sys.argv = sys_argv
    BI.build(ba)
    for e in [o for o in bpy.data.objects if o.type == "EMPTY"]:
        bpy.data.objects.remove(e)
    objs = [o for c in BI.COLLS.values() for o in c.objects if o.type == "MESH"]
    drop = LOD2_DROP if lod == 2 else LOD1_DROP if lod == 1 else ()
    for o in list(objs):
        if any(k in o.name for k in drop):
            objs.remove(o)
            bpy.data.objects.remove(o)
    apply_modifiers(objs)
    bake_transforms(objs)
    tri_raw = sum(tris_of(o) for o in objs)
    keep = {o.name for o in objs if group_of(o.name) not in ("CAB_Interior", "CAB_ShellPlaceholder")}
    removed, tested = remove_hidden(objs, keep)
    tri_clean = sum(tris_of(o) for o in objs)
    print(f"LOD{lod}: raw {tri_raw} tris, hidden faces removed {removed}/{tested}, now {tri_clean} tris")
    consolidate(objs)
    # receivers of the AO atlas
    receivers = [o for o in objs if not o.get("decal") and not o.get("fixed_uv")
                 and group_of(o.name) not in ("CAB_Glass",) and not o.name.startswith(NO_AO)]
    layout_bake_uv(objs, receivers)
    groups = join_groups(objs)
    piv = frames()
    root = bpy.data.objects.new(f"CabInterior_LOD{lod}", None)
    bpy.context.scene.collection.objects.link(root)
    root.matrix_world = Matrix.Translation(CAB_MOUNT)
    for g, ob in groups.items():
        if g in piv:
            set_pivot(ob, *piv[g])
        else:
            set_pivot(ob, CAB_MOUNT, V(1, 0, 0), V(0, 1, 0), V(0, 0, 1))
        finalize_mesh(ob)
    # AO bake on the joined meshes (receivers = opaque groups; glass hidden so rays pass; decals/quads excluded)
    hide = [ob for g, ob in groups.items() if g == "CAB_Glass"]
    rec = [ob for g, ob in groups.items() if not g.startswith(("CAB_Glass", "DISPLAY_", "MIRROR_"))]
    res = AO_RES[lod] if not a.ao_res else a.ao_res
    ao = bake_ao(rec, hide, res, a.ao_samples, a.ao_distance, None)
    print("decal UV1 transferred:", transfer_decal_uv1(list(groups.values())), "loops")
    tex_dir = os.path.join(out_dir, "textures")
    ao_files = {}
    for tier, f in TIERS.items():
        size = max(256, int(AO_RES[0] * f)) if lod == 0 else max(256, int(res * f / TIERS["High"]))
        size = min(size, res)
        d = os.path.join(tex_dir, tier)
        os.makedirs(d, exist_ok=True)
        p = os.path.join(d, f"T_Cab_AO_LOD{lod}.png")
        save_gray(ao, p, size)
        ao_files[tier] = {"path": p, "size": size}
    # names, parenting, empties
    for g, ob in groups.items():
        ob.name = f"{g}_LOD{lod}"
        ob.data.name = ob.name
        mw = ob.matrix_world.copy()
        ob.parent = root
        ob.matrix_parent_inverse = Matrix.Identity(4)
        ob.matrix_world = mw
    empties = {"EYE_POINT": BI.EYE, "H_POINT": BI.HPT, "WHEEL_CENTRE": BI.WHEEL_C,
               "CAB_MOUNT_REF": CAB_MOUNT}
    for nm, p in empties.items():
        e = bpy.data.objects.new(nm if lod == 0 else f"{nm}_LOD{lod}", None)
        bpy.context.scene.collection.objects.link(e)
        e.parent = root
        e.matrix_world = Matrix.Translation(p)
    # stats
    info = {"file": None, "root": root.name, "objects": {}, "tris_total": 0}
    for g, ob in groups.items():
        t = tris_of(ob)
        info["objects"][ob.name] = {"tris": t, "materials": [m.name for m in ob.data.materials],
                                    "pivot_unity_local": b2u(ob.matrix_world.translation - CAB_MOUNT),
                                    "role": g}
        if g in ANIM_AXES:
            R = ob.matrix_world.to_3x3()
            info["objects"][ob.name]["animation"] = {
                k: {"local_axis_blender": ax, "axis_unity_cab": b2u(R.col["XYZ".index(ax)]),
                    "local_axis_unity": {"X": "X", "Y": "Z", "Z": "Y"}[ax]} for k, ax in ANIM_AXES[g].items()}
        info["tris_total"] += t
    info["empties_unity_local"] = {k: b2u(p - CAB_MOUNT) for k, p in empties.items()}
    info["ao_atlas"] = ao_files
    info["hidden_faces_removed"] = removed
    info["tris_before_cleanup"] = tri_raw
    info["build_s"] = round(time.time() - t0, 1)
    # export
    fbx = os.path.join(out_dir, f"SM_CabInterior_LOD{lod}.fbx")
    select([root] + list(root.children_recursive), root)
    bpy.ops.export_scene.fbx(filepath=fbx, use_selection=True, object_types={"EMPTY", "MESH"},
                             apply_unit_scale=True, apply_scale_options="FBX_SCALE_ALL", axis_forward="Z", axis_up="Y",
                             bake_space_transform=True, use_mesh_modifiers=False, mesh_smooth_type="FACE",
                             use_tspace=True, colors_type="SRGB", prioritize_active_color=True, add_leaf_bones=False,
                             bake_anim=False, path_mode="STRIP", embed_textures=False, use_custom_props=False)
    info["file"] = os.path.relpath(fbx, BI.REPO).replace("\\", "/")
    info["file_bytes"] = os.path.getsize(fbx)
    for t in ao_files.values():
        t["path"] = os.path.relpath(t["path"], BI.REPO).replace("\\", "/")
    manifest["lods"][f"LOD{lod}"] = info
    print(f"LOD{lod}: {info['tris_total']} tris in {len(groups)} objects -> {fbx} ({info['file_bytes'] // 1024} KB)")
    return groups, root


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    p = argparse.ArgumentParser()
    p.add_argument("--lods", default="0,1,2")
    p.add_argument("--out", default=os.path.join(BI.REPO, "art-source", "truck", "interior", "export"))
    p.add_argument("--ao-samples", type=int, default=4096)
    p.add_argument("--ao-distance", type=float, default=0.6)
    p.add_argument("--ao-res", type=int, default=0)
    p.add_argument("--urp-out", default="")
    p.add_argument("--urp-light", default="overcast,lowsun")
    p.add_argument("--urp-res", default="1600x900")
    p.add_argument("--urp-cams", default="all")
    p.add_argument("--manifest", default="")
    p.add_argument("--debug-ao", action="store_true", help="URP renders show only the AO atlas (QA)")
    p.add_argument("--debug-col", action="store_true", help="URP renders show only the vertex tint (QA)")
    a = p.parse_args(argv)
    out = os.path.abspath(a.out)
    os.makedirs(out, exist_ok=True)
    tex = None
    man_path = a.manifest or os.path.join(out, "cab_interior_manifest.json")
    manifest = {"asset": "cab interior (brand-neutral), track A6", "generator": "tools/blender/truck/interior/a6_export.py",
                "lods": {}}
    if os.path.exists(man_path):
        old = json.load(open(man_path, encoding="utf-8"))
        manifest["lods"].update(old.get("lods", {}))
    lods = [int(x) for x in a.lods.split(",") if x != ""]
    for lod in sorted(lods, reverse=True):          # LOD0 last: its scene stays loaded for the URP-like renders
        process_lod(lod, a, out, manifest)
        if tex is None:
            tex = build_textures(os.path.join(out, "textures"))
    manifest.update(contract(tex, out))
    json.dump(manifest, open(man_path, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print("WROTE", man_path)
    if a.urp_out and 0 in lods:
        urp_renders(a, tex, manifest)


def rel(pth):
    return os.path.relpath(pth, BI.REPO).replace("\\", "/")


def contract(tex, out):
    mats = {}
    for slot in SLOT_OF:
        e = {"slot": slot}
        if slot in DETAIL_SET:
            e["detail_set"] = DETAIL_SET[slot][0]
            e["textures"] = {t: {k: (rel(v) if isinstance(v, str) else v) for k, v in d.items()} for t, d in tex[slot].items()}
        elif slot in tex:
            e["textures"] = {t: {k: (rel(v) if isinstance(v, str) else v) for k, v in d.items()} for t, d in tex[slot].items()}
        mats[slot] = e
    mats["MI_Cab_Plastic"]["metallic_from"] = mats["MI_Cab_Metal"]["metallic_from"] = "uv3.y"
    mats["MI_Cab_Decal"]["notes"] = "alpha clip 0.5; colour = vertex tint x atlas RGB; bands: icons v 0.005-0.495, grille 0.505-0.87, stitch 0.88-0.995 (U repeats)"
    mats["MI_Cab_Glass"]["notes"] = "transparent, Fresnel reflection (reflection probe), grime from T_Cab_GlassGrime on uv0 (1 tile = 1.1 m)"
    mats["MI_Cab_Display"]["notes"] = "unlit emissive; each DISPLAY_* object gets its own runtime RenderTexture / UI texture (uv0 0-1)"
    mats["MI_Cab_MirrorRT"]["notes"] = "each MIRROR_* quad shows its own mirror camera RenderTexture (uv0 0-1, mirror flip in the camera)"
    return {
        "units": "metres", "unity_axes": "+X right (passenger side), +Y up, +Z forward; driver at -X (LHD)",
        "frame_mapping": "A2/Blender (x, y, z) -> Unity (x, z, y); FBX exported with axis_forward=Z, axis_up=Y, "
                         "bake_space_transform, FBX_SCALE_ALL. Unity import: Scale Factor 1, Convert Units on, "
                         "Bake Axis Conversion off; check EYE_POINT local position below after import.",
        "origin": {"name": "CAB_MOUNT_REF", "a2_frame": list(CAB_MOUNT), "unity_vehicle": [0.0, 1.15, 3.925],
                   "note": "= graybox CabPivot (TractorDimensions: y = cabBodyBottom, z = CabRearZ + cabLen/2). Parent "
                           "CabInterior_LODn to the cab-suspension pivot with localPosition 0, localRotation 0."},
        "tiers": {"High": "LOD0 + High textures", "Medium": "LOD1 + Medium textures", "Low": "LOD2 + Low textures",
                  "texture_compression": "ASTC: Normal 5x5 (High) / 6x6; Detail 6x6 (High) / 8x8; AO 6x6 / 8x8; "
                                         "Decal 6x6; all power-of-two squares, mipmaps on, AO + Detail + Normal linear (not sRGB)"},
        "materials": mats,
        "shader_contract": {
            "name": "Kamion/CabInterior (Shader Graph, URP Lit, opaque)",
            "per_material": "_Detail (RGBA linear: R variation, G micro-AO, B roughness, A perforation mask), "
                            "_Normal (tangent space, OpenGL +Y), _AO (UV1 atlas of the LOD), _DetailTiling = 1 "
                            "(tiling is already in UV0)",
            "vertex": {
                "color.rgb": "base tint, sRGB-encoded -> convert to linear in the shader",
                "color.a": "base roughness (linear)",
                "uv0": "tiled detail UV (pre-scaled per authoring material)",
                "uv1": "AO atlas UV (unique, non-overlapping; neutral white block for glass/decals/displays/mirrors/curtains)",
                "uv2.x": "wear amount (brightens albedo, lowers roughness)", "uv2.y": "detail strength s (0..1)",
                "uv3.x": "perforation flag (leather centre panels)", "uv3.y": "metallic"},
            "formula": {
                "detailMix": "s > 0 ? 1 : 0",
                "albedo": "tint * lerp(1, (0.7 + 0.6*R) * (0.4 + 0.6*G), detailMix) * lerp(1, A, uv3.x) * (1 + 1.5*uv2.x)",
                "roughness": "saturate(color.a + (B - 0.5) * 0.4 * detailMix - 0.25*uv2.x)",
                "normal": "UnpackNormal(_Normal) with strength 1.25*s",
                "metallic": "uv3.y",
                "occlusion": "_AO.r on uv1 (URP: occlusion -> indirect/ambient only)"},
        },
        "named_objects": {
            "eye_point": "EYE_POINT (driver ocular point, UNECE R46-based; parent of the cab camera)",
            "mirrors_render_texture": ["MIRROR_MainL", "MIRROR_MainR", "MIRROR_WideL", "MIRROR_WideR", "MIRROR_Kerb",
                                       "MIRROR_Front"],
            "displays_runtime_ui": {"DISPLAY_Cluster": "12.3 in instrument cluster, 1560x600 layout (sightline-tested)",
                                    "DISPLAY_Infotainment": "10.1 in centre screen", "DISPLAY_Tachograph": "1DIN tacho LCD",
                                    "DISPLAY_Radio": "1DIN radio LCD (LOD0/1)", "DISPLAY_BunkPanel": "bunk climate panel LCD (LOD0/1)"},
            "animated": {k: v for k, v in ANIM_AXES.items()},
            "static": ["CAB_Interior", "CAB_Glass", "CAB_ShellPlaceholder (exterior skin/mirror housings placeholder until A3; "
                       "disable when the A3 exterior is in)"],
        },
        "textures_root": rel(os.path.join(out, "textures")),
    }


def urp_renders(a, tex, manifest):
    import backdrop as BD
    ao = os.path.join(BI.REPO, manifest["lods"]["LOD0"]["ao_atlas"]["High"]["path"])
    BD.build(BI.group)
    os.makedirs(a.urp_out, exist_ok=True)
    cams = BI.cameras()
    want = None if a.urp_cams == "all" else set(a.urp_cams.split(","))
    for kind in a.urp_light.split(","):
        AMB_KIND[0] = kind
        preview_materials(tex, ao)
        mr = bpy.data.materials["MI_Cab_MirrorRT"].node_tree.nodes.get("Principled BSDF")
        mr.inputs["Emission Color"].default_value = (0.30, 0.31, 0.32, 1)   # stands in for the mirror RenderTexture
        mr.inputs["Emission Strength"].default_value = 1.0
        if a.debug_ao or a.debug_col:
            debug_ao_materials(ao, col=a.debug_col)
        add_ambient_to_backdrop(set())
        setup_urp_like(kind, a.urp_res)
        if a.debug_ao or a.debug_col:
            bpy.context.scene.view_settings.exposure = 0.0   # show the map values as they are
        for cname in BI.LIGHT_CAMS[kind]:
            if want and cname not in want:
                continue
            loc, tgt, fov = cams[cname]
            bpy.context.scene.camera = BI.look_cam(cname, loc, tgt, fov)
            fn = os.path.join(a.urp_out, f"{cname}_{kind}_urp.jpg")
            bpy.context.scene.render.filepath = fn
            bpy.ops.render.render(write_still=True)
            print("WROTE", fn)


def debug_ao_materials(ao, col=False):
    dbg = bpy.data.materials.get("ao_debug") or bpy.data.materials.new("ao_debug")
    dbg.use_nodes = True
    nt = dbg.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    o_ = nt.nodes.new("ShaderNodeOutputMaterial")
    uvn = nt.nodes.new("ShaderNodeUVMap")
    uvn.uv_map = "Bake"
    tx = nt.nodes.new("ShaderNodeTexImage")
    tx.image = bpy.data.images.load(ao, check_existing=True)
    em = nt.nodes.new("ShaderNodeEmission")
    nt.links.new(uvn.outputs["UV"], tx.inputs["Vector"])
    nt.links.new(tx.outputs["Color"], em.inputs["Color"])
    if col:
        vc = nt.nodes.new("ShaderNodeVertexColor")
        vc.layer_name = "Col"
        nt.links.new(M._math(nt, "POWER", vc.outputs["Color"], 0.45), em.inputs["Color"])
    nt.links.new(em.outputs[0], o_.inputs["Surface"])
    for ob in bpy.data.objects:
        if ob.type == "MESH" and ob.name.startswith(("CAB_Interior", "STEERING", "STALK", "PEDAL", "LEVER")):
            for i in range(len(ob.data.materials)):
                ob.data.materials[i] = dbg


if __name__ == "__main__":
    main()
