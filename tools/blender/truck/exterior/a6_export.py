"""Track A6 (exterior) — game-ready TRAKT tractor exterior: rigid parts with pivots, hidden-face cleanup, atlased
slot materials with baked detail (normal / colour / AO / dirt), LOD0-3, convex collision, FBX per LOD, manifest,
glass interface for the interior, QA renders.

    blender -b --factory-startup --python tools/blender/truck/exterior/a6_export.py -- \
        [--out ABS_DIR] [--renders ABS_DIR] [--bake-scale 1.0] [--ao-samples 256] [--no-renders] [--blend ABS.blend]

Pipeline (all from the A4 generator, nothing hand-edited):
 1. build the A4 exterior (body.py / chassis.py, classic mirrors), keep a full-detail copy as the bake source (HIGH);
 2. game pieces: apply modifiers, bake transforms, cut the doors out of the cab shell (rims added), replace mirror
    glass by MIRROR_* quads, the TRAKT wordmark by a decal quad, drop bake-only detail (panel-gap strips, frame
    bolts, wordmark strokes) - they live on in the normal/colour maps;
 3. remove faces no camera can see (rays to ~400 exterior + in-cab view points; moving parts tested only against
    themselves so opening a door or steering never reveals a hole);
 4. 6 game slots (Paint, Trim, Metal, Glass, Lights, MirrorRT); one UV atlas per baked slot (uv0 'Atlas', uniform
    texel density, low-priority surfaces scaled down); right wheels share the left wheels' UVs (mirrored);
 5. bake from HIGH: tangent normal, clean albedo, roughness, metallic, dirt mask (road film / streaks / cavities at
    full strength), paint mask, AO (static parts and wheels separately: a spinning wheel must not carry arch shadow);
 6. LOD1-3 = LOD0 pieces minus drop lists, decimated (collapse keeps UVs) to the triangle targets; join per rigid
    part, pivots, hierarchy, sockets; FBX per LOD (Unity: +Z forward, +Y up, metres, origin = ground under the
    rear axle = physics vehicle frame); textures High/Medium/Low; convex COL_* hulls (k-DOP, <= 255 tris);
 7. manifest JSON, glass_interface.json (exterior owns windscreen + side glass), QA renders (game materials).
"""
import argparse
import json
import math
import os
import re
import sys
import time

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import geom as G  # noqa: E402
import materials as M  # noqa: E402
import body as B  # noqa: E402
import chassis as C  # noqa: E402
import scene as S  # noqa: E402

V = Vector
REPO = G.REPO
WB = G.WB
ROOT_A2 = V((0.0, -WB, 0.0))          # Unity vehicle origin (physics frame): ground under the rear axle
CAB_MOUNT = V((0.0, 0.225, 1.15))     # = interior CAB_MOUNT_REF = graybox CabPivot (A2 frame)
TRUCK_GROUPS = ("cab", "lower", "frame", "wheels", "mirrors")
SLOT_MAT = {"Paint": "MI_Ext_Paint", "Trim": "MI_Ext_Trim", "Metal": "MI_Ext_Metal", "Glass": "MI_Ext_Glass",
            "Lights": "MI_Ext_Lights", "MirrorRT": "MI_Ext_MirrorRT"}
BAKED = ("Paint", "Trim", "Metal", "Lights")
ATLAS_RES = {"Paint": 2048, "Trim": 2048, "Metal": 2048, "Lights": 1024}
DECAL_RES = 1024
TIERS = {"High": 1, "Medium": 2, "Low": 4}          # divisor of the High size
TRI_TARGET = {1: 43000, 2: 14500, 3: 3200}
TRI_LIMIT = {0: 100000, 1: 45000, 2: 15500, 3: 4000}

MAT_SLOT = {
    "paint": "Paint",
    "alu_brushed": "Metal", "alu_wheel": "Metal", "chrome": "Metal", "satin_alu": "Metal", "steel": "Metal",
    "checker": "Metal", "perforated": "Metal", "wordmark": "Metal",
    "glass": "Glass", "glass_tint": "Glass",
    "lamp_inner": "Lights", "reflector": "Lights", "dark_chrome": "Lights", "led_drl": "Lights", "led_off": "Lights",
    "lens_amber": "Lights", "lens_red": "Lights", "projector": "Lights",
    "mirror": "MirrorRT",
}   # everything else (plastics, rubber, tyres, chassis, graphite, honeycomb, frit, plate, grease, ...) -> Trim

LIGHT_GROUPS = ["NONE", "DRL", "LOW_BEAM", "HIGH_BEAM", "IND_L", "IND_R", "TAIL_BRAKE", "REVERSE", "MARKER_FRONT",
                "MARKER_SIDE", "MARKER_REAR", "FOG", "WORK"]
LIGHT_COLOUR = {"DRL": (1.0, 0.97, 0.92), "LOW_BEAM": (1.0, 0.96, 0.90), "HIGH_BEAM": (1.0, 0.97, 0.94),
                "IND_L": (1.0, 0.42, 0.02), "IND_R": (1.0, 0.42, 0.02), "TAIL_BRAKE": (1.0, 0.03, 0.01),
                "REVERSE": (1.0, 1.0, 1.0), "MARKER_FRONT": (1.0, 0.97, 0.92), "MARKER_SIDE": (1.0, 0.42, 0.02),
                "MARKER_REAR": (1.0, 0.03, 0.01), "FOG": (1.0, 0.95, 0.85), "WORK": (1.0, 0.98, 0.95)}
LIVERIES = {   # game material variants of MI_Ext_Paint (linear colours, same as the A4 render materials)
    "white": {"_PaintColor": [0.78, 0.785, 0.78], "_PaintRoughness": 0.32, "_PaintMetallic": 0.0, "_ClearCoat": 1.0,
              "_DecalColor": [0.10, 0.104, 0.11], "_DecalMetallic": 1.0, "_DecalRoughness": 0.30,
              "label": "biel flotowa"},
    "dark": {"_PaintColor": [0.020, 0.040, 0.034], "_PaintRoughness": 0.30, "_PaintMetallic": 0.35, "_ClearCoat": 1.0,
             "_DecalColor": [0.62, 0.63, 0.64], "_DecalMetallic": 1.0, "_DecalRoughness": 0.32,
             "label": "zielen butelkowa (ciemna)"},
}
DUST = (0.15, 0.135, 0.11)

DOOR_PIECES = ("door_skirt_", "door_handle_", "door_lock_", "win_frame_", "belt_seal_", "door_shell_")
LOD1_DROP = ("_nut", "_washer", "_hubbolt", "battery_latch", "door_lock_", "emblem_dash", "extender_hinge",
             "washer_nozzle", "antenna_base", "fifth_pin", "fifth_grease", "fifth_handle_grip", "catwalk_ladder",
             "catwalk_brk", "rear_lamp_brk", "trailer_socket_brk", "fairing_brk", "spring_hanger", "tank_saddle",
             "mudflap_rib", "socket_lid", "proj_shroud", "air_tank_strap", "tank_bead", "fuel_neck", "exhaust_tip",
             "bellow_plate", "palm_face", "coil_head", "work_lamp", "extender_flap", "diff_nose", "kingpin")
LOD2_DROP = LOD1_DROP + ("coil", "damper_", "brake_chamber", "caliper_", "tie_rod", "drag_link", "steering_box",
                         "propshaft", "anti_roll", "leaf_", "handle_bar", "handle_back", "door_handle", "mirror_strut",
                         "horn", "flap_arm", "catwalk", "gooseneck", "step_nose", "eats_band", "fuel_cap", "oil_pan",
                         "gearbox", "engine", "radiator", "cab_pivot", "frame_horn", "frame_front_cross",
                         "frame_cross", "axle_arm", "trailing_arm", "guard_arm", "hb_mask", "proj_bowl", "socket",
                         "brake_disc", "_dish", "belt_seal", "wiper_pivot", "arch_brush", "bstep_tread", "fog_back",
                         "fog_bowl", "battery_lid", "adblue_cap", "diff", "front_axle", "axle_rear", "bellow_",
                         "front_mudflap_clamp", "lamp_gasket", "rear_joint", "air_tank", "exhaust_out",
                         "fifth_handle", "fifth_lock", "fifth_bracket", "fifth_mount", "plate_holder",
                         "marker_front_led", "catwalk_grab", "coupling_panel", "_hubcap", "_hub")
LOD3_KEEP = ("cab_shell", "door_shell_", "door_skirt", "side_glass", "windscreen", "lower_fairing", "arch_flare",
             "side_fairing", "side_extender", "rear_guard", "fuel_tank", "adblue_tank", "battery_box", "eats_box",
             "frame_rail", "fifth_plate", "lamp_lens", "lamp_back", "drl_", "indicator_", "rear_lens", "marker_",
             "side_marker", "side_repeater", "mirror_main_", "mirror_wide_", "mirror_arm", "front_mirror",
             "grille_back", "grille_frame", "grille_bar", "roof_lip", "_tyre", "_rim", "_disc", "fog_lens", "fog_led",
             "decal_", "frit_", "hb_led", "rear_lamp_", "mudflap_", "front_mudflap_", "spoiler_lip", "intake_mesh",
             "road_frame", "road_back", "step_tread", "roof_hatch", "rear_lower_panel")


# ---------------------------------------------------------------- small helpers
def a2u(v):
    """A2/Blender vector -> Unity axes (x, z, y) (left-handed, +Y up, +Z forward)."""
    return [round(float(v[0]), 5), round(float(v[2]), 5), round(float(v[1]), 5)]


def a2u_point(p):
    return a2u(V(p) - ROOT_A2)


def select(objs, active=None):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = active or (objs[0] if objs else None)


def tris_of(o):
    if o.type != "MESH":
        return 0
    me = o.data
    me.calc_loop_triangles()
    return len(me.loop_triangles)


def world_verts(o):
    mw = o.matrix_world
    return [mw @ v.co for v in o.data.vertices]


def bbox(points):
    lo = V([min(p[i] for p in points) for i in range(3)])
    hi = V([max(p[i] for p in points) for i in range(3)])
    return lo, hi


def side_of(name):
    m = re.search(r"_(-?1)(?:_|$)", name)
    return "L" if m and m.group(1) == "-1" else "R"


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
    for o in objs:
        if o.type == "MESH" and o.matrix_world != Matrix.Identity(4):
            o.data.transform(o.matrix_world)
            o.matrix_world = Matrix.Identity(4)


def copy_object(o, name, coll):
    c = o.copy()
    c.data = o.data.copy()
    c.name = name
    for k in list(c.keys()):
        if k not in ("group", "part", "src"):
            del c[k]
    coll.objects.link(c)
    return c


def new_collection(name):
    c = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(c)
    return c


# ---------------------------------------------------------------- 1. source scene (= A4 exterior, classic mirrors)
def build_source():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    G.STATE["coll"] = bpy.context.scene.collection
    S.setup_render("1600x900", 64)
    M.PARAMS["dirt"] = 1.0       # authoring grime at full strength: the dirt mask is baked at 1, the game scales it
    M.build_library("white")
    C.make_tyre_materials()
    subpaths, strokes = G.load_svg_mark(os.path.join(REPO, "art-source", "truck", "brand", "trakt.svg"))
    B.cab_shell()
    B.glazing()
    B.doors_and_gaps()
    B.front_face(subpaths, strokes)
    B.headlamps()
    B.corners_roof_rear()
    B.mirrors("classic", front=True)
    B.lower_fairing()
    C.build_all()
    # decal quad over the TRAKT wordmark (the stroke geometry is baked into the decal atlas and dropped)
    wm = [o for o in bpy.data.objects if o.name.startswith("wordmark_")]
    pts = [o.matrix_world @ V(c) for o in wm for c in o.bound_box]
    lo, hi = bbox(pts)
    hw = max(abs(lo.x), abs(hi.x)) + 0.03
    z0, z1 = lo.z - 0.02, hi.z + 0.02
    G.set_group("cab")
    B.CAB.quad_patch("decal_wordmark", "paint", "front", [(-hw, z0), (hw, z0), (hw, z1), (-hw, z1)], off=0.0018,
                     nu=4, nv=1)
    dec = bpy.data.objects["decal_wordmark"]
    dec["decal_rect"] = [-hw, hw, z0, z1]
    return subpaths, strokes, wm


# ---------------------------------------------------------------- decal atlas (wordmark band)
def raster_decal(wm_objs, rect, res):
    """Rasterise the wordmark stroke boxes (front faces, x/z plane) into an RGBA atlas: band v 0.75..1.0 =
    the decal quad's UV rectangle. Seen from the front, the viewer's left is +X."""
    x0, x1, z0, z1 = rect
    ss = 4
    w, h = res * ss, res // 4 * ss
    xs = (np.arange(w) + 0.5) / w           # u 0..1 -> x from +hw (viewer left) to -hw
    zs = (np.arange(h) + 0.5) / h
    X = x1 - xs[None, :] * (x1 - x0)
    Z = z0 + zs[:, None] * (z1 - z0)
    X = np.broadcast_to(X, (h, w))
    Z = np.broadcast_to(Z, (h, w))
    alpha = np.zeros((h, w), dtype=bool)
    for o in wm_objs:
        vs = [o.matrix_world @ v.co for v in o.data.vertices]
        ymax = max(v.y for v in vs)
        front = [(v.x, v.z) for v in vs if v.y > ymax - 1e-4]
        if len(front) < 3:
            continue
        cx = sum(p[0] for p in front) / len(front)
        cz = sum(p[1] for p in front) / len(front)
        poly = sorted(front, key=lambda p: math.atan2(p[1] - cz, p[0] - cx))
        inside = np.ones((h, w), dtype=bool)
        n = len(poly)
        for i in range(n):
            ax, az = poly[i]
            bx, bz = poly[(i + 1) % n]
            inside &= ((bx - ax) * (Z - az) - (bz - az) * (X - ax)) >= 0
        alpha |= inside
    a = alpha.reshape(h // ss, ss, w // ss, ss).mean(axis=(1, 3))
    img = np.zeros((res, res, 4), dtype=np.float32)
    img[..., :3] = 1.0
    band = img[res - res // 4:, :, :]
    band[..., 3] = a
    return img


# ---------------------------------------------------------------- 2. pieces, parts, door split, mirror quads
def part_of(o):
    n, g = o.name, o.get("group")
    if g == "wheels":
        m = re.match(r"wheel_([FR])([LR])", n)
        return f"WHEEL_{m.group(1)}{m.group(2)}"
    if n.startswith("brake_disc_F_"):
        return "WHEEL_F" + side_of(n)
    if n.startswith("caliper_F_"):
        return "STEER_F" + side_of(n)
    if n.startswith("mudflap_"):
        return "MUDFLAP_R" + side_of(n)
    if n.startswith("front_mudflap_") and not n.startswith("front_mudflap_clamp"):
        return "MUDFLAP_F" + side_of(n)
    if n.startswith(("wiper_arm", "wiper_blade", "wiper_pivot")):
        return "WIPER_L" if n.endswith("0") else "WIPER_R"
    if n.startswith("side_glass_"):
        return "GLASS_Door" + side_of(n)
    if n.startswith(DOOR_PIECES):
        return "DOOR_" + side_of(n)
    if n == "windscreen":
        return "GLASS_Windscreen"
    if n.startswith("MIRROR_"):
        return n
    if g in ("cab", "mirrors"):
        return "CAB_Body"
    return "CHASSIS"


def bake_only(o):
    mats = {s.material.name for s in o.material_slots if s.material}
    if mats == {"gap"}:
        return True
    return o.name.startswith(("frame_bolt_", "wordmark_", "mirror_main_glass", "mirror_wide_glass",
                              "mirror_kerb_glass", "front_mirror_glass"))


def split_doors(shell, coll):
    """Cut both doors out of the solidified cab shell along the A4 shut lines (rear y, top z 3.00, front polyline
    door_front_y) and close the cut edges with a 28 mm rim (door edge / aperture flange)."""
    hw = G.CAB_HALF_W
    me = shell.data
    bm = bmesh.new()
    bm.from_mesh(me)
    zs = [B.CAB_Z0 - 0.03, 1.90, 2.14, 2.40, 2.70, 3.03]

    def cut(s, co, no, pred):
        faces = [f for f in bm.faces if s * f.calc_center_median().x > hw - 0.24 and pred(f.calc_center_median())]
        if not faces:
            return
        edges = list({e for f in faces for e in f.edges})
        verts = list({v for f in faces for v in f.verts})
        bmesh.ops.bisect_plane(bm, geom=verts + edges + faces, plane_co=co, plane_no=no, dist=1e-5)

    for s in (-1, 1):
        cut(s, (0, B.DOOR_REAR, 0), (0, 1, 0), lambda c: B.CAB_Z0 - 0.05 < c.z < 3.06)
        cut(s, (0, 0, 3.00), (0, 0, 1), lambda c: B.DOOR_REAR - 0.05 < c.y < 1.45)
        for za, zb in zip(zs, zs[1:]):
            ya, yb = B.door_front_y(max(za, B.CAB_Z0)), B.door_front_y(min(zb, 3.0))
            no = V((0, zb - za, -(yb - ya))).normalized()
            cut(s, (0, ya, za), no, lambda c, za=za, zb=zb: za - 0.04 < c.z < zb + 0.04 and c.y > B.DOOR_REAR)
    bm.faces.ensure_lookup_table()

    def in_door(c, s):
        return (s * c.x > hw - 0.24 and B.CAB_Z0 - 0.01 < c.z < 3.0 and B.DOOR_REAR < c.y < B.door_front_y(c.z))

    out = {}
    paint_idx = [i for i, m in enumerate(me.materials) if m and m.name == "paint"][0]
    interior_idx = [i for i, m in enumerate(me.materials) if m and m.name == "interior"][0]
    for s in (-1, 1):
        sd = "L" if s < 0 else "R"
        dbm = bm.copy()
        dbm.faces.ensure_lookup_table()
        bmesh.ops.delete(dbm, geom=[f for f in dbm.faces if not in_door(f.calc_center_median(), s)], context="FACES")
        add_rim(dbm, paint_idx, interior_idx)
        dme = bpy.data.meshes.new(f"door_shell_{s}")
        dbm.to_mesh(dme)
        dbm.free()
        for m in me.materials:
            dme.materials.append(m)
        ob = bpy.data.objects.new(f"door_shell_{s}", dme)
        coll.objects.link(ob)
        ob["group"] = "cab"
        out[sd] = ob
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if in_door(f.calc_center_median(), -1)
                               or in_door(f.calc_center_median(), 1)], context="FACES")
    add_rim(bm, paint_idx, interior_idx)
    bm.to_mesh(me)
    bm.free()
    me.update()
    return out


def add_rim(bm, paint_idx, interior_idx, depth=0.028):
    """Extrude the open boundary of the outer (non-interior) skin inwards along the face normal."""
    bm.normal_update()
    edges = [e for e in bm.edges if e.is_boundary and e.link_faces[0].material_index != interior_idx]
    if not edges:
        return
    nrm = {}
    for e in edges:
        for v in e.verts:
            nrm.setdefault(v, V()).__iadd__(e.link_faces[0].normal)
    new = {v: bm.verts.new(v.co - n.normalized() * depth) for v, n in nrm.items()}
    for e in edges:
        a, b = e.verts
        f0 = e.link_faces[0]
        # keep the winding consistent with the adjacent face (rim normal points across the cut)
        loop = [l for l in f0.loops if l.edge == e][0]
        if loop.vert == a:
            quad = (b, a, new[a], new[b])
        else:
            quad = (a, b, new[b], new[a])
        try:
            f = bm.faces.new(quad)
            f.material_index = paint_idx
            f.smooth = False
        except ValueError:
            pass


def pca_frame(points):
    P = np.array([tuple(p) for p in points])
    c = P.mean(axis=0)
    w, vec = np.linalg.eigh(np.cov((P - c).T))
    return V(c), [V(vec[:, i]) for i in range(3)], w      # ascending variance: [0] = thinnest = normal


def mirror_quads(coll):
    """MIRROR_* render-texture quads on the reflective face of each mirror glass (names = interior manifest)."""
    names = {"mirror_main_glass_-1": "MIRROR_MainL", "mirror_main_glass_1": "MIRROR_MainR",
             "mirror_wide_glass_-1": "MIRROR_WideL", "mirror_wide_glass_1": "MIRROR_WideR",
             "mirror_kerb_glass": "MIRROR_Kerb", "front_mirror_glass": "MIRROR_Front"}
    out = {}
    for src, dst in names.items():
        o = bpy.data.objects[src]
        pts = world_verts(o)
        c, axes, var = pca_frame(pts)
        n, a1, a2 = axes
        if n.dot(G.EYE - c) < 0:
            n = -n
        up = a2 if abs(a2.z) >= abs(a1.z) else a1
        if up.z < 0:
            up = -up
        right = n.cross(up).normalized()        # frame (X=right, Y=normal, Z=up) is right-handed
        up = right.cross(n).normalized()
        du = [(p - c).dot(right) for p in pts]
        dv = [(p - c).dot(up) for p in pts]
        dn = max((p - c).dot(n) for p in pts)
        hu, hv = (max(du) - min(du)) / 2 - 0.002, (max(dv) - min(dv)) / 2 - 0.002
        cc = c + n * (dn + 0.0006)
        bm = bmesh.new()
        corners = ((-1, -1), (-1, 1), (1, 1), (1, -1))          # winding -> face normal = +n (towards the eye)
        vs = [bm.verts.new(cc + right * (su * hu) + up * (sv * hv)) for su, sv in corners]
        f = bm.faces.new(vs)
        uvl = bm.loops.layers.uv.new("UVMap")
        for lp, uv in zip(f.loops, ((0, 0), (0, 1), (1, 1), (1, 0))):
            lp[uvl].uv = uv
        me = bpy.data.meshes.new(dst)
        bm.to_mesh(me)
        bm.free()
        me.materials.append(G.mat("mirror"))
        ob = bpy.data.objects.new(dst, me)
        coll.objects.link(ob)
        ob["group"] = "mirrors"
        ob["frame"] = [list(cc), list(right), list(n), list(up)]      # origin, X, Y(normal), Z(up)
        ob["size_m"] = [2 * hu, 2 * hv]
        out[dst] = ob
    return out


def light_group(pname, mname, x):
    if mname == "led_drl":
        return "DRL"
    if pname.startswith("proj_lens"):
        return "LOW_BEAM"
    if pname.startswith("hb_led"):
        return "HIGH_BEAM"
    if pname.startswith(("indicator_", "side_repeater")) or (pname.startswith("rear_lens") and mname == "lens_amber"):
        return "IND_L" if x < 0 else "IND_R"
    if pname.startswith("rear_lens"):
        return "TAIL_BRAKE" if mname == "lens_red" else "REVERSE" if mname == "lens_clear" else "NONE"
    if pname.startswith("marker_front_led"):
        return "MARKER_FRONT"
    if pname.startswith("side_marker"):
        return "MARKER_SIDE"
    if pname.startswith("marker_rear"):
        return "MARKER_REAR"
    if pname.startswith("fog_led"):
        return "FOG"
    if pname.startswith("work_lamp_lens"):
        return "WORK"
    return "NONE"


def slot_of(pname, mname):
    if mname == "lens_clear":
        return "Lights" if pname.startswith("rear_lens") else "Glass"
    return MAT_SLOT.get(mname, "Trim")


def game_materials():
    for slot, name in SLOT_MAT.items():
        m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
        m.use_nodes = True
        m["slot"] = slot
    return {s: bpy.data.materials[n] for s, n in SLOT_MAT.items()}


PRIORITY = {"interior": 0.30, "curtain": 0.30, "gap": 0.5, "chassis": 0.75, "grease": 0.75}


def to_game_piece(o, gm):
    """Swap authoring materials for slot materials; store per-face data before the swap:
    uv 'Atlas' (filled later), 'Decal' (wordmark quad only), 'Data' (x = light group, y = emissive mask),
    colour 'Col' (glass tint; white elsewhere), face attribute 'prio' (texel priority)."""
    me = o.data
    names = [m.name if m else "" for m in me.materials]
    keep_uv = [tuple(d.uv) for d in me.uv_layers[0].data] if o.name.startswith("MIRROR_") else None
    for uvl in list(me.uv_layers):
        me.uv_layers.remove(uvl)
    me.uv_layers.new(name="Atlas")
    me.uv_layers.new(name="Decal")
    me.uv_layers.new(name="Data")
    col = me.color_attributes.new("Col", "BYTE_COLOR", "CORNER")
    prio = me.attributes.new("prio", "FLOAT", "FACE")
    slots = []
    for p in me.polygons:
        mn = names[p.material_index] if p.material_index < len(names) else ""
        sl = slot_of(o.name, mn)
        if sl not in slots:
            slots.append(sl)
    new_idx = {sl: i for i, sl in enumerate(slots)}
    dl = me.uv_layers["Data"].data
    de = me.uv_layers["Decal"].data
    cd = col.data
    is_decal = o.name.startswith("decal_")
    rect = o.get("decal_rect")
    tint_of = {"glass": (0.80, 0.86, 0.83), "glass_tint": (0.45, 0.50, 0.48), "lens_clear": (0.95, 0.95, 0.95)}
    face_slot = []
    for p in me.polygons:
        mn = names[p.material_index] if p.material_index < len(names) else ""
        sl = slot_of(o.name, mn)
        face_slot.append(sl)
        grp = light_group(o.name, mn, p.center.x) if sl == "Lights" else "NONE"
        gi = LIGHT_GROUPS.index(grp)
        pr = PRIORITY.get(mn, 1.0)
        if o.get("group") == "frame" and p.normal.z < -0.6:
            pr *= 0.6
        if "Ri_" in o.name or "Li_" in o.name:
            pr *= 0.6
        prio.data[p.index].value = pr
        tint = tint_of.get(mn, (1, 1, 1))
        for li in p.loop_indices:
            dl[li].uv = (gi, 1.0 if gi else 0.0)
            cd[li].color = (*[c ** (1 / 2.2) for c in tint], 1.0)
            if is_decal and rect:
                co = me.vertices[me.loops[li].vertex_index].co
                u = (rect[1] - co.x) / (rect[1] - rect[0])
                v = 0.75 + 0.25 * (co.z - rect[2]) / (rect[3] - rect[2])
                de[li].uv = (min(max(u, 0.0), 1.0), min(max(v, 0.75), 1.0))
            else:
                de[li].uv = (0.002, 0.002)
    at = me.uv_layers["Atlas"].data
    if keep_uv:
        for i, uv in enumerate(keep_uv):
            at[i].uv = uv
    elif "Glass" in face_slot:     # planar 0-1 per pane (wiper sweep / grime masks in the glass shader)
        gl = [p for p, sl in zip(me.polygons, face_slot) if sl == "Glass"]
        vs = [me.vertices[i].co for p in gl for i in p.vertices]
        lo, hi = bbox(vs)
        ext = hi - lo
        ax = sorted(range(3), key=lambda i: -ext[i])[:2]
        a0, a1 = (ax[0], ax[1]) if ax[0] != 2 else (ax[1], ax[0])
        for p in gl:
            for li in p.loop_indices:
                co = me.vertices[me.loops[li].vertex_index].co
                at[li].uv = ((co[a0] - lo[a0]) / max(ext[a0], 1e-6), (co[a1] - lo[a1]) / max(ext[a1], 1e-6))
    for p, sl in zip(me.polygons, face_slot):
        p.material_index = new_idx[sl]
    me.materials.clear()
    for sl in slots:
        me.materials.append(gm[sl])
    o["slots"] = slots


# ---------------------------------------------------------------- 3. hidden faces
def viewpoints():
    pts = []
    cy = -1.6
    for r, hs in ((3.4, (0.3, 1.2, 2.4, 4.2)), (6.0, (0.3, 1.0, 1.8, 3.2, 5.5)), (13.0, (0.4, 1.8, 4.0, 8.0))):
        for k in range(24):
            a = 2 * math.pi * (k + 0.5 * (r > 5)) / 24
            for h in hs:
                pts.append(V((r * math.cos(a), cy + 1.4 * r * math.sin(a), h)))
    pts += [V((x, y, 9.5)) for x in (-3.0, 0.0, 3.0) for y in (-5.0, -1.5, 2.0)]
    for dx in (-0.15, 0.0, 0.15):
        for dz in (-0.12, 0.0, 0.12):
            pts.append(G.EYE + V((dx, 0.0, dz)))
    pts += [V((0.55, 0.45, 2.50)), V((0.0, -0.45, 2.0)), V((0.0, -0.45, 1.75)), V((0.0, 0.3, 2.9))]
    return pts


TRANSPARENT_SLOTS = ("Glass", "MirrorRT")
MOVING = ("DOOR_", "GLASS_Door", "WHEEL_", "STEER_", "WIPER_", "MUDFLAP_")


def occluder_bvh(objs):
    verts, polys = [], []
    for o in objs:
        me = o.data
        base = len(verts)
        verts += [v.co.copy() for v in me.vertices]
        sl = o.get("slots", [])
        for p in me.polygons:
            if sl and sl[p.material_index] in TRANSPARENT_SLOTS:
                continue
            polys.append([base + i for i in p.vertices])
    if not polys:
        return None
    return BVHTree.FromPolygons(verts, polys, all_triangles=False, epsilon=0.0)


def remove_hidden(pieces):
    t0 = time.time()
    vps = viewpoints()
    groups = {}
    for o in pieces:
        part = o["part"]
        key = "STATIC" if not part.startswith(MOVING) else re.sub(r"^GLASS_Door", "DOOR_", part)
        key = key.replace("STEER_", "WHEEL_")
        groups.setdefault(key, []).append(o)
    removed = tested = 0
    for key, objs in groups.items():
        if key.startswith(("WIPER_", "MUDFLAP_")):
            continue
        bvh = occluder_bvh(objs)
        if bvh is None:
            continue
        for o in objs:
            if o["part"].startswith(("GLASS_", "MIRROR_")) or o.name.startswith("decal_"):
                continue
            me = o.data
            sl = o.get("slots", [])
            hidden = []
            for p in me.polygons:
                if sl and sl[p.material_index] in TRANSPARENT_SLOTS:
                    continue
                tested += 1
                n = p.normal
                c = p.center
                samples = [c] + [c + (me.vertices[i].co - c) * 0.8 for i in list(p.vertices)[:4]]
                vis = False
                for k, s in enumerate(samples):
                    org = s + n * 0.003
                    cand = []
                    for v in vps:
                        d = v - org
                        ln = d.length
                        dd = d / ln
                        cs = n.dot(dd)
                        if cs > 0.02:
                            cand.append((-cs, dd, ln))
                    cand.sort(key=lambda t: t[0])
                    for _, dd, ln in cand:
                        if bvh.ray_cast(org, dd, ln)[0] is None:
                            vis = True
                            break
                    if vis:
                        break
                    if k == 0 and p.area < 0.0004:
                        break
                if not vis:
                    hidden.append(p.index)
            if hidden:
                bm = bmesh.new()
                bm.from_mesh(me)
                bm.faces.ensure_lookup_table()
                bmesh.ops.delete(bm, geom=[bm.faces[i] for i in hidden], context="FACES")
                bm.to_mesh(me)
                bm.free()
                removed += len(hidden)
    for o in list(pieces):
        if len(o.data.polygons) == 0:
            pieces.remove(o)
            bpy.data.objects.remove(o)
    print(f"hidden faces removed {removed}/{tested} in {time.time() - t0:.0f} s")
    return removed, tested


# ---------------------------------------------------------------- 4. UV atlas
def mirrored_wheel(o):
    return o["part"] in ("WHEEL_FR", "WHEEL_RR", "STEER_FR")


def uv_islands(me, uvl, faces):
    """Union-find of faces sharing an edge with matching UVs on both ends."""
    parent = {f: f for f in faces}

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a
    fs = set(faces)
    edge_map = {}
    for f in faces:
        poly = me.polygons[f]
        li = list(poly.loop_indices)
        for k in range(len(li)):
            a, b = li[k], li[(k + 1) % len(li)]
            va, vb = me.loops[a].vertex_index, me.loops[b].vertex_index
            key = (min(va, vb), max(va, vb))
            ua, ub = tuple(uvl[a].uv), tuple(uvl[b].uv)
            if va > vb:
                ua, ub = ub, ua
            edge_map.setdefault(key, []).append((f, (round(ua[0], 6), round(ua[1], 6)), (round(ub[0], 6), round(ub[1], 6))))
    for lst in edge_map.values():
        for i in range(1, len(lst)):
            if lst[i][1:] == lst[0][1:] and lst[i][0] in fs and lst[0][0] in fs:
                ra, rb = find(lst[0][0]), find(lst[i][0])
                if ra != rb:
                    parent[ra] = rb
    isl = {}
    for f in faces:
        isl.setdefault(find(f), []).append(f)
    return list(isl.values())


def unwrap_atlases(pieces):
    t0 = time.time()
    for slot in BAKED:
        mname = SLOT_MAT[slot]
        objs = [o for o in pieces if mname in [m.name for m in o.data.materials] and not mirrored_wheel(o)]
        if not objs:
            continue
        for o in objs:
            o.data.uv_layers.active = o.data.uv_layers["Atlas"]
        select(objs)
        bpy.ops.object.mode_set(mode="EDIT")
        for o in objs:
            bm = bmesh.from_edit_mesh(o.data)
            mi = [m.name for m in o.data.materials].index(mname)
            for f in bm.faces:
                f.select = f.material_index == mi
            bmesh.update_edit_mesh(o.data)
        bpy.ops.uv.smart_project(angle_limit=math.radians(62), island_margin=0.0, area_weight=0.0,
                                 correct_aspect=True, scale_to_bounds=False)
        bpy.ops.object.mode_set(mode="OBJECT")
        # texel priority: scale islands about their centre (interior skin, chassis underside, inner duals smaller)
        for o in objs:
            me = o.data
            mi = [m.name for m in me.materials].index(mname)
            faces = [p.index for p in me.polygons if p.material_index == mi]
            uvl = me.uv_layers["Atlas"].data
            pr = me.attributes["prio"].data
            for isl in uv_islands(me, uvl, faces):
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
        bpy.ops.object.mode_set(mode="EDIT")
        for o in objs:
            bm = bmesh.from_edit_mesh(o.data)
            mi = [m.name for m in o.data.materials].index(mname)
            for f in bm.faces:
                f.select = f.material_index == mi
            bmesh.update_edit_mesh(o.data)
        margin = 0.004 if ATLAS_RES[slot] >= 2048 else 0.006
        bpy.ops.uv.pack_islands(rotate=True, margin_method="FRACTION", margin=margin, shape_method="CONCAVE")
        bpy.ops.object.mode_set(mode="OBJECT")
        print(f"atlas {slot}: {len(objs)} pieces, {time.time() - t0:.0f} s")
    # right wheels / right caliper: mirrored copy of the left UVs (identical geometry)
    by_name = {o.name: o for o in pieces}
    for o in pieces:
        if not mirrored_wheel(o):
            continue
        src_name = re.sub(r"wheel_([FR])R", r"wheel_\1L", o.name).replace("_F_1", "_F_-1")
        src = by_name.get(src_name)
        if src is None:
            print("WARN no UV source for", o.name)
            continue
        transfer_uv_mirror(src, o)


def transfer_uv_mirror(src, dst):
    sm = src.data
    bvh = BVHTree.FromPolygons([v.co for v in sm.vertices], [list(p.vertices) for p in sm.polygons])
    suv = sm.uv_layers["Atlas"].data
    dm = dst.data
    duv = dm.uv_layers["Atlas"].data
    for p in dm.polygons:
        c = p.center.copy()
        c.x = -c.x
        loc, nrm, idx, dist = bvh.find_nearest(c)
        if idx is None:
            continue
        sp = sm.polygons[idx]
        sv = [(sm.vertices[sm.loops[li].vertex_index].co, suv[li].uv.copy()) for li in sp.loop_indices]
        for li in p.loop_indices:
            q = dm.vertices[dm.loops[li].vertex_index].co.copy()
            q.x = -q.x
            best = min(sv, key=lambda t: (t[0] - q).length_squared)
            duv[li].uv = best[1]


# ---------------------------------------------------------------- 5. bake
def setup_world():
    w = bpy.data.worlds.get("bake_world") or bpy.data.worlds.new("bake_world")
    w.use_nodes = True
    w.light_settings.distance = 0.5
    bpy.context.scene.world = w


def emit_override(mats, mode):
    """Route a value of every HIGH material into an Emission shader (EMIT bake). Modes: albedo (clean colour,
    paint = white), rdm (R roughness, G dirt mask, B metallic), pmask (1 on paint)."""
    for m in mats:
        nt = m.node_tree
        out = next((n for n in nt.nodes if n.type == "OUTPUT_MATERIAL" and n.is_active_output), None) or \
            next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL")
        if "_orig" not in m:
            lk = out.inputs["Surface"].links
            m["_orig"] = [lk[0].from_node.name, lk[0].from_socket.identifier] if lk else ["", ""]
        em = nt.nodes.get("BAKE_EMIT") or nt.nodes.new("ShaderNodeEmission")
        em.name = "BAKE_EMIT"
        for n in [n for n in nt.nodes if n.name.startswith("BAKE_V")]:
            nt.nodes.remove(n)
        bsdf = next((n for n in nt.nodes if n.type == "BSDF_PRINCIPLED"), None)
        gm = next((n for n in nt.nodes if n.label == "grime_mix"), None)
        gr = next((n for n in nt.nodes if n.label == "grime_rough"), None)

        def src(sock_owner, sock_name, default):
            if sock_owner is None:
                return default
            s = sock_owner.inputs[sock_name]
            if s.links:
                return s.links[0].from_socket
            dv = s.default_value
            return tuple(dv) if hasattr(dv, "__len__") else float(dv)

        def feed(target, value):
            if isinstance(value, bpy.types.NodeSocket):
                nt.links.new(value, target)
            elif isinstance(value, tuple):
                target.default_value = value if len(target.default_value) == len(value) else (*value[:3], 1.0)
            else:
                if hasattr(target.default_value, "__len__"):
                    target.default_value = (value, value, value, 1.0)
                else:
                    target.default_value = value
        if mode == "albedo":
            if m.name == "paint":
                v = (1.0, 1.0, 1.0, 1.0)
            elif gm is not None:
                s = gm.inputs[6]
                v = s.links[0].from_socket if s.links else tuple(s.default_value)
            elif bsdf is not None:
                v = src(bsdf, "Base Color", (0.5, 0.5, 0.5, 1))
            else:
                v = (0.02, 0.02, 0.02, 1.0)      # thin glass (not baked onto opaque slots)
            feed(em.inputs["Color"], v)
        elif mode == "rdm":
            cc = nt.nodes.new("ShaderNodeCombineColor")
            cc.name = "BAKE_V_cc"
            rough = gr.inputs[1].default_value if gr is not None else src(bsdf, "Roughness", 0.5)
            feed(cc.inputs[0], rough)
            if gm is not None and gm.inputs[0].links:
                feed(cc.inputs[1], gm.inputs[0].links[0].from_socket)
            else:
                feed(cc.inputs[1], generic_dirt(nt))
            feed(cc.inputs[2], src(bsdf, "Metallic", 0.0))
            nt.links.new(cc.outputs[0], em.inputs["Color"])
        elif mode == "pmask":
            em.inputs["Color"].default_value = (1, 1, 1, 1) if m.name == "paint" else (0, 0, 0, 1)
            for lk in list(em.inputs["Color"].links):
                nt.links.remove(lk)
        em.inputs["Strength"].default_value = 1.0
        nt.links.new(em.outputs[0], out.inputs["Surface"])


def generic_dirt(nt):
    """Road film for materials without their own grime: 0.55 * clamp((0.9 - z) / 0.9) * noise."""
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    geo.name = "BAKE_V_geo"
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    sep.name = "BAKE_V_sep"
    nt.links.new(geo.outputs["Position"], sep.inputs[0])
    m1 = nt.nodes.new("ShaderNodeMath")
    m1.name = "BAKE_V_m1"
    m1.operation = "SUBTRACT"
    m1.inputs[0].default_value = 0.9
    nt.links.new(sep.outputs[2], m1.inputs[1])
    m2 = nt.nodes.new("ShaderNodeMath")
    m2.name = "BAKE_V_m2"
    m2.operation = "MULTIPLY"
    m2.use_clamp = True
    m2.inputs[1].default_value = 0.55 / 0.9
    nt.links.new(m1.outputs[0], m2.inputs[0])
    return m2.outputs[0]


def emit_restore(mats):
    for m in mats:
        nt = m.node_tree
        if "_orig" not in m:
            continue
        name, ident = m["_orig"]
        out = next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL")
        if name:
            fn = nt.nodes[name]
            sock = next(s for s in fn.outputs if s.identifier == ident)
            nt.links.new(sock, out.inputs["Surface"])
        for n in [n for n in nt.nodes if n.name.startswith(("BAKE_V", "BAKE_EMIT"))]:
            nt.nodes.remove(n)
        del m["_orig"]


def mute_micro_bumps(mats, mute=True):
    """Fine procedural bumps (orange peel, plastic grain, chassis noise) alias at atlas density; they are a
    shader detail map in the game. Image bumps (tread, honeycomb, checker plate, louvres) stay in the bake."""
    for m in mats:
        for n in m.node_tree.nodes:
            if n.type in ("TEX_NOISE", "TEX_VORONOI") and n.inputs["Scale"].default_value >= 250:
                for lk in n.outputs[0].links:
                    if lk.to_node.type == "BUMP":
                        lk.to_node.mute = mute
                for out in n.outputs:
                    for lk in out.links:
                        if lk.to_node.type == "BUMP":
                            lk.to_node.mute = mute


def new_float_image(name, res):
    im = bpy.data.images.get(name)
    if im:
        bpy.data.images.remove(im)
    im = bpy.data.images.new(name, res, res, alpha=False, float_buffer=True, is_data=True)
    im.colorspace_settings.name = "Non-Color"
    return im


def img_array(im):
    a = np.empty(len(im.pixels), dtype=np.float32)
    im.pixels.foreach_get(a)
    return a.reshape(im.size[1], im.size[0], 4)


def bake_atlases(pieces, high, a):
    """Bake proxies: STATIC = all baked-slot faces except the wheels, WHEELS = left wheels + left caliper only
    (right ones share their UVs). Every proxy material carries an image node; one bake call fills all slots."""
    t0 = time.time()
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.use_denoising = False
    sc.render.bake.margin = 16
    sc.render.bake.margin_type = "EXTEND"
    setup_world()
    coll = new_collection("BAKE_PROXY")
    proxies = {}
    for key, pred in (("STATIC", lambda o: not o["part"].startswith(("WHEEL_", "STEER_"))),
                      ("WHEELS", lambda o: o["part"] in ("WHEEL_FL", "WHEEL_RL", "STEER_FL"))):
        objs = [copy_object(o, o.name + "_bk", coll) for o in pieces if pred(o) and
                any(m.name in [SLOT_MAT[s] for s in BAKED] for m in o.data.materials)]
        select(objs, objs[0])
        if len(objs) > 1:
            bpy.ops.object.join()
        px = bpy.context.view_layer.objects.active
        px.name = "PROXY_" + key
        bm = bmesh.new()
        bm.from_mesh(px.data)
        keep = {i for i, m in enumerate(px.data.materials) if m and m.get("slot") in BAKED}
        bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.material_index not in keep], context="FACES")
        bm.to_mesh(px.data)
        bm.free()
        px.data.uv_layers.active = px.data.uv_layers["Atlas"]
        px.data.uv_layers["Atlas"].active_render = True
        proxies[key] = px
    res = {s: max(64, int(ATLAS_RES[s] * a.bake_scale)) for s in BAKED}
    imgs = {s: {} for s in BAKED}
    dummy = new_float_image("bake_dummy", 64)
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
        for s, m in gms.items():
            n = m.node_tree.nodes["BAKE_IMG"]
            if only and s not in only:
                n.image = dummy
            else:
                if pass_name not in imgs[s]:
                    imgs[s][pass_name] = new_float_image(f"bake_{s}_{pass_name}", res[s])
                n.image = imgs[s][pass_name]
            m.node_tree.nodes.active = n
    high_mats = sorted({sl.material for o in high for sl in o.material_slots if sl.material}, key=lambda m: m.name)
    for o in bpy.data.objects:
        o.hide_render = True
    high_wheel = [o for o in high if o["part"] in ("WHEEL_FL", "WHEEL_RL", "STEER_FL")]
    high_static = [o for o in high if not o["part"].startswith(("WHEEL_", "STEER_"))]

    def run(pass_name, btype, key, samples, only=None, **kw):
        px = proxies[key]
        hs = high_static if key == "STATIC" else high_wheel
        set_targets(pass_name, only)
        sc.cycles.samples = samples
        for o in bpy.data.objects:
            o.hide_render = True
        px.hide_render = False
        if btype == "AO":
            select([px], px)
            bpy.ops.object.bake(type="AO", margin=16, use_clear=False, target="IMAGE_TEXTURES")
        else:
            for o in hs:
                o.hide_render = False
            select(hs + [px], px)
            bpy.ops.object.bake(type=btype, use_selected_to_active=True, cage_extrusion=a.cage, max_ray_distance=
                                a.cage * 2.5, margin=16, use_clear=False, target="IMAGE_TEXTURES", **kw)
        print(f"  bake {pass_name} {key}: {time.time() - t0:.0f} s")
    for key in ("STATIC", "WHEELS"):
        only = None if key == "STATIC" else ("Trim", "Metal")
        mute_micro_bumps(high_mats, True)
        run("N", "NORMAL", key, 8, only, normal_space="TANGENT")
        mute_micro_bumps(high_mats, False)
        emit_override(high_mats, "albedo")
        run("ALB", "EMIT", key, 16, only)
        emit_override(high_mats, "rdm")
        run("RDM", "EMIT", key, 16, only)
        if key == "STATIC":
            emit_override(high_mats, "pmask")
            run("PM", "EMIT", key, 8, ("Paint",))
        emit_restore(high_mats)
        run("AO", "AO", key, a.ao_samples, only)
    for o in bpy.data.objects:
        o.hide_render = False
    out = {}
    for s in BAKED:
        out[s] = {k: img_array(im) for k, im in imgs[s].items()}
    for px in proxies.values():
        bpy.data.objects.remove(px)
    print(f"bakes done in {time.time() - t0:.0f} s")
    return out


def lin2srgb(x):
    x = np.clip(x, 0, 1)
    return np.where(x <= 0.0031308, 12.92 * x, 1.055 * np.power(x, 1 / 2.4) - 0.055)


def down2(a):
    return a.reshape(a.shape[0] // 2, 2, a.shape[1] // 2, 2, a.shape[2]).mean(axis=(1, 3))


def save_png(arr, path, alpha=True):
    h, w = arr.shape[:2]
    im = bpy.data.images.new(os.path.basename(path), w, h, alpha=alpha, float_buffer=False, is_data=True)
    if arr.shape[2] == 3:
        arr = np.concatenate([arr, np.ones((h, w, 1), dtype=np.float32)], axis=2)
    im.pixels.foreach_set(np.clip(arr, 0, 1).astype(np.float32).ravel())
    im.filepath_raw = path
    im.file_format = "PNG"
    im.save()
    bpy.data.images.remove(im)


def compose_textures(baked, decal, out_dir):
    """C = albedo (sRGB) + roughness; N = tangent normal (OpenGL +Y); M = AO, dirt, metallic (Paint: paint mask)."""
    files = {}
    for s, b in baked.items():
        alb, rdm, ao, nrm = b["ALB"], b["RDM"], b["AO"], b["N"]
        Ct = np.dstack([lin2srgb(alb[..., :3]), rdm[..., 0:1]])
        thirdc = b["PM"][..., 0:1] if s == "Paint" else rdm[..., 2:3]
        Mt = np.dstack([ao[..., 0:1], np.clip(rdm[..., 1:2], 0, 1), thirdc, np.ones_like(thirdc)])
        Nt = nrm[..., :3].copy()
        sets = {"C": Ct, "N": Nt, "M": Mt}
        for kind, arr in sets.items():
            cur = arr.astype(np.float32)
            for tier, div in TIERS.items():
                if tier != "High":
                    cur = down2(cur)
                    if kind == "N":
                        v = cur * 2 - 1
                        v /= np.maximum(np.linalg.norm(v, axis=2, keepdims=True), 1e-6)
                        cur = v * 0.5 + 0.5
                d = os.path.join(out_dir, "textures", tier)
                os.makedirs(d, exist_ok=True)
                p = os.path.join(d, f"T_Ext_{s}_{kind}.png")
                save_png(cur, p, alpha=kind != "N")
                files.setdefault(s, {}).setdefault(kind, {})[tier] = {"path": rel(p), "size": int(cur.shape[0])}
    cur = decal
    for tier in TIERS:
        if tier != "High":
            cur = down2(cur)
        d = os.path.join(out_dir, "textures", tier)
        p = os.path.join(d, "T_Ext_Decal.png")
        save_png(cur, p)
        files.setdefault("Decal", {}).setdefault("RGBA", {})[tier] = {"path": rel(p), "size": int(cur.shape[0])}
    return files


def rel(p):
    return os.path.relpath(p, REPO).replace("\\", "/")


# ---------------------------------------------------------------- 6. LODs, pivots, hierarchy
def decimate_pieces(pieces, target, floor_tris=40, lights_min=0.5):
    """Bisection on a global collapse ratio; small pieces are left alone, emissive/glass pieces keep >= 50%."""
    dec = [o for o in pieces if tris_of(o) > floor_tris and not o.name.startswith(("decal_", "MIRROR_"))]
    fixed = sum(tris_of(o) for o in pieces if o not in dec)
    base = {o.name: tris_of(o) for o in dec}

    def ratio_for(o, r):
        sl = o.get("slots", [])
        lo = lights_min if ("Lights" in sl or "Glass" in sl) else 0.02
        return min(1.0, max(r, lo))
    for o in dec:
        md = o.modifiers.new("lod", "DECIMATE")
        md.decimate_type = "COLLAPSE"
        md.use_collapse_triangulate = True
    lo_r, hi_r = 0.01, 1.0
    for _ in range(9):
        r = (lo_r + hi_r) / 2
        for o in dec:
            o.modifiers["lod"].ratio = ratio_for(o, r)
        dg = bpy.context.evaluated_depsgraph_get()
        n = fixed
        for o in dec:
            me = o.evaluated_get(dg).to_mesh()
            me.calc_loop_triangles()
            n += len(me.loop_triangles)
            o.evaluated_get(dg).to_mesh_clear()
        if n > target:
            hi_r = r
        else:
            lo_r = r
    for o in dec:
        o.modifiers["lod"].ratio = ratio_for(o, lo_r)
    apply_modifiers(dec)
    for o in dec:
        o.data.set_sharp_from_angle(angle=math.radians(42))
    return lo_r


def frames(pieces_by_part, mirrors):
    """Pivot frames in the A2 frame: (origin, X, Y, Z)."""
    X, Y, Z = V((1, 0, 0)), V((0, 1, 0)), V((0, 0, 1))
    fx, rx = G.FRONT_TRACK / 2, G.REAR_TRACK / 2
    f = {"CHASSIS": (ROOT_A2, X, Y, Z), "CAB_Body": (CAB_MOUNT, X, Y, Z), "GLASS_Windscreen": (CAB_MOUNT, X, Y, Z)}
    for s, sd in ((-1, "L"), (1, "R")):
        f[f"WHEEL_F{sd}"] = (V((s * fx, 0.0, G.WHEEL_Z)), X, Y, Z)
        f[f"STEER_F{sd}"] = (V((s * (fx - 0.05), 0.0, G.WHEEL_Z)), X, Y, Z)
        f[f"WHEEL_R{sd}"] = (V((s * rx, -WB, G.WHEEL_Z)), X, Y, Z)
        door = pieces_by_part.get(f"DOOR_{sd}", [])
        pts = [p for o in door if o.name.startswith("door_shell_") for p in world_verts(o)]
        yh = max(p.y for p in pts) + 0.004
        f[f"DOOR_{sd}"] = (V((s * G.CAB_HALF_W, yh, 1.60)), X, Y, Z)
        f[f"GLASS_Door{sd}"] = f[f"DOOR_{sd}"]
        for kind, top in (("R", 0.86), ("F", 0.66)):
            mf = [p for o in pieces_by_part.get(f"MUDFLAP_{kind}{sd}", []) for p in world_verts(o)]
            if mf:
                lo, hi = bbox(mf)
                f[f"MUDFLAP_{kind}{sd}"] = (V(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, hi.z)), X, Y, Z)
    for k, nm in ((0, "WIPER_L"), (1, "WIPER_R")):
        piv = V(bpy.data.objects[f"wiper_pivot{k}"]["centre"])
        n = B.CAB.normal_front(2.06, piv.x)
        up = V((0, -n.z, n.y)).normalized()        # along the glass, upwards
        xa = up.cross(n).normalized()
        f[nm] = (piv, xa, up, n)
    for nm, ob in mirrors.items():
        o_, xa, ya, za = (V(v) for v in ob["frame"])
        f[nm] = (o_, xa, ya, za)
    return f


def set_pivot(ob, origin, X, Y, Z):
    R = Matrix((X, Y, Z)).transposed().to_4x4()
    T = Matrix.Translation(origin) @ R
    ob.data.transform(T.inverted())
    ob.matrix_world = T


def finalize_mesh(ob):
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bmesh.ops.triangulate(bm, faces=bm.faces[:], quad_method="BEAUTY", ngon_method="BEAUTY")
    bm.to_mesh(ob.data)
    bm.free()
    me = ob.data
    used = sorted({p.material_index for p in me.polygons})
    mats = [me.materials[i] for i in used]
    remap = {i: k for k, i in enumerate(used)}
    idx = [remap[p.material_index] for p in me.polygons]
    me.materials.clear()
    for m in mats:
        me.materials.append(m)
    for p, i in zip(me.polygons, idx):
        p.material_index = i
    if "prio" in me.attributes:
        me.attributes.remove(me.attributes["prio"])
    me.color_attributes.active_color = me.color_attributes["Col"]
    me.uv_layers.active = me.uv_layers["Atlas"]


PARENT = {"DOOR_L": "CAB_Body", "DOOR_R": "CAB_Body", "GLASS_DoorL": "DOOR_L", "GLASS_DoorR": "DOOR_R",
          "GLASS_Windscreen": "CAB_Body", "WIPER_L": "CAB_Body", "WIPER_R": "CAB_Body", "WHEEL_FL": "STEER_FL",
          "WHEEL_FR": "STEER_FR"}
ANIM = {   # Blender local axis, Unity local axis, Unity convention
    "WHEEL_FL": {"spin": ("X", "X", "forward roll = positive angle about local +X")},
    "WHEEL_FR": {"spin": ("X", "X", "forward roll = positive angle about local +X")},
    "WHEEL_RL": {"spin": ("X", "X", "forward roll = positive angle about local +X")},
    "WHEEL_RR": {"spin": ("X", "X", "forward roll = positive angle about local +X")},
    "STEER_FL": {"steer": ("Z", "Y", "right turn = positive angle about local +Y (Unity), road-wheel angle")},
    "STEER_FR": {"steer": ("Z", "Y", "right turn = positive angle about local +Y (Unity), road-wheel angle")},
    "DOOR_L": {"open": ("Z", "Y", "open = +80 deg about local +Y (Unity)")},
    "DOOR_R": {"open": ("Z", "Y", "open = -80 deg about local +Y (Unity)")},
    "WIPER_L": {"wipe": ("Z", "Y", "sweep up = -95 deg about local +Y (Unity); local +Y = glass normal")},
    "WIPER_R": {"wipe": ("Z", "Y", "sweep up = -95 deg about local +Y (Unity); local +Y = glass normal")},
    "MUDFLAP_RL": {"swing": ("X", "X", "+-20 deg about local +X")}, "MUDFLAP_RR": {"swing": ("X", "X", "+-20 deg")},
    "MUDFLAP_FL": {"swing": ("X", "X", "+-20 deg about local +X")}, "MUDFLAP_FR": {"swing": ("X", "X", "+-20 deg")},
}
DOOR_OPEN_BLENDER = {"DOOR_L": -80.0, "DOOR_R": 80.0}
WIPE_BLENDER = -95.0 * -1    # Blender angle for the sweep (Unity angle = -Blender angle under the axis mapping)


def lod_pieces(master, lod, coll):
    if lod == 0:
        keep = list(master)
    elif lod == 3:
        keep = [o for o in master if any(k in o.name for k in LOD3_KEEP) and not o.name.startswith("MIRROR_")]
    else:
        drop = LOD2_DROP if lod == 2 else LOD1_DROP
        keep = [o for o in master if not any(k in o.name for k in drop)
                and not (lod == 2 and o.name.startswith("MIRROR_"))]
    out = []
    for o in keep:
        c = copy_object(o, f"{o.name}__L{lod}", coll)
        c["part"] = o["part"]
        c["slots"] = list(o.get("slots", []))
        if lod == 3:
            p = c["part"]
            if p.startswith(("DOOR_", "WIPER_")):
                c["part"] = "CAB_Body"
            elif p.startswith("GLASS_Door"):
                c["part"] = "GLASS_Windscreen"
            elif p.startswith(("MUDFLAP_", "STEER_")):
                c["part"] = "CHASSIS"
        out.append(c)
    return out


def join_parts(pieces):
    groups = {}
    for o in pieces:
        groups.setdefault(o["part"], []).append(o)
    out = {}
    for part, objs in groups.items():
        select(objs, objs[0])
        if len(objs) > 1:
            bpy.ops.object.join()
        ob = bpy.context.view_layer.objects.active
        ob["part"] = part
        out[part] = ob
    return out


def sockets(master):
    """Unity sockets (empties): lights, axles, kingpin, exhaust, eye point."""
    def centre(pred):
        pts = [p for o in master if pred(o) for p in world_verts(o)]
        if not pts:
            return None
        lo, hi = bbox(pts)
        return (lo + hi) / 2
    out = {}
    for s, sd in ((-1, "L"), (1, "R")):
        out[f"LIGHT_LowBeam_{sd}"] = ("CAB_Body", centre(lambda o: o.name.startswith(f"proj_lens_{s}_")))
        out[f"LIGHT_HighBeam_{sd}"] = ("CAB_Body", centre(lambda o: o.name.startswith(f"hb_led_{s}")))
        out[f"LIGHT_Fog_{sd}"] = ("CHASSIS", centre(lambda o: o.name.startswith("fog_led") and
                                                    s * sum(v.co.x for v in o.data.vertices) > 0))
        out[f"LIGHT_RearLamp_{sd}"] = ("CHASSIS", centre(lambda o: o.name.startswith("rear_lens_") and side_of(o.name)
                                                         == sd))
    out["LIGHT_Work"] = ("CAB_Body", centre(lambda o: o.name.startswith("work_lamp_lens")))
    out["EXHAUST_OUT"] = ("CHASSIS", centre(lambda o: o.name.startswith("exhaust_out")))
    out["EYE_POINT"] = ("CAB_Body", G.EYE.copy())
    out["CAB_MOUNT_REF"] = ("CAB_Body", CAB_MOUNT.copy())
    out["CAB_TILT_PIVOT"] = ("CHASSIS", B.PIVOT.copy())
    out["AXLE_FRONT"] = ("CHASSIS", V((0, 0, G.WHEEL_Z)))
    out["AXLE_REAR"] = ("CHASSIS", V((0, -WB, G.WHEEL_Z)))
    out["FIFTH_WHEEL_KINGPIN"] = ("CHASSIS", V((0, -WB + G.FIFTH_LEAD, G.FIFTH_H)))
    return {k: v for k, v in out.items() if v[1] is not None}


def kdop_hull(points, name, coll, ndir=100):
    """Convex hull of the extreme points along ndir Fibonacci directions (<= 2*ndir-4 triangles)."""
    P = np.array([tuple(p) for p in points])
    ga = math.pi * (3 - math.sqrt(5))
    sel = set()
    for i in range(ndir):
        z = 1 - 2 * (i + 0.5) / ndir
        r = math.sqrt(1 - z * z)
        d = np.array([r * math.cos(ga * i), r * math.sin(ga * i), z])
        sel.add(int(np.argmax(P @ d)))
    bm = bmesh.new()
    for i in sel:
        bm.verts.new(P[i])
    bmesh.ops.convex_hull(bm, input=bm.verts[:])
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    coll.objects.link(ob)
    return ob


def collision(master, coll):
    def pts(pred):
        return [p for o in master if pred(o) for p in world_verts(o)]
    cab = pts(lambda o: o["part"] in ("CAB_Body", "DOOR_L", "DOOR_R", "GLASS_Windscreen") and o.get("group") != "mirrors")
    chas = [o for o in master if o["part"] == "CHASSIS"]
    out = {"COL_Cab": kdop_hull(cab, "COL_Cab", coll)}
    lower = [p for o in chas if o.get("group") == "lower" for p in world_verts(o)]
    out["COL_ChassisFront"] = kdop_hull(lower, "COL_ChassisFront", coll)
    mid = [p for o in chas if o.get("group") == "frame" for p in world_verts(o) if -3.25 < p.y < -1.0]
    out["COL_ChassisMid"] = kdop_hull(mid, "COL_ChassisMid", coll)
    rear = [p for o in chas if o.get("group") == "frame" for p in world_verts(o) if p.y <= -3.25 and p.z > 0.3]
    out["COL_ChassisRear"] = kdop_hull(rear, "COL_ChassisRear", coll)
    return out


def export_lod(lod, master, mirrors, a, manifest, coll):
    t0 = time.time()
    pieces = lod_pieces(master, lod, coll)
    raw = sum(tris_of(o) for o in pieces)
    ratio = 1.0
    if lod in TRI_TARGET:
        ratio = decimate_pieces(pieces, TRI_TARGET[lod], floor_tris=40 if lod < 3 else 12,
                                lights_min=0.5 if lod < 3 else 0.25)
    by_part = {}
    for o in master:
        by_part.setdefault(o["part"], []).append(o)
    fr = frames(by_part, mirrors)
    parts = join_parts(pieces)
    sfx = f"_LOD{lod}"
    root = bpy.data.objects.new(f"TruckExterior{sfx}", None)
    coll.objects.link(root)
    root.matrix_world = Matrix.Translation(ROOT_A2)
    objs = {}
    for part, ob in parts.items():
        set_pivot(ob, *fr[part])
        finalize_mesh(ob)
        ob.name = part + sfx
        ob.data.name = ob.name
        objs[part] = ob
    if True:   # rig consistency: STEER_F* exists in every LOD (empty when the caliper is dropped)
        for sd in ("L", "R"):
            if f"STEER_F{sd}" not in objs:
                e = bpy.data.objects.new(f"STEER_F{sd}{sfx}", None)
                coll.objects.link(e)
                e.matrix_world = Matrix.Translation(fr[f"STEER_F{sd}"][0])
                objs[f"STEER_F{sd}"] = e
    for part, ob in objs.items():
        par = objs.get(PARENT.get(part, ""), root)
        mw = ob.matrix_world.copy()
        ob.parent = par
        ob.matrix_parent_inverse = Matrix.Identity(4)
        ob.matrix_world = mw
    socks = sockets(master)
    empties = {}
    for nm, (parent, p) in socks.items():
        e = bpy.data.objects.new(nm if lod == 0 else nm + sfx, None)
        coll.objects.link(e)
        e.empty_display_size = 0.08
        par = objs.get(parent, root)
        e.parent = par
        e.matrix_world = Matrix.Translation(p)
        empties[nm] = (e, parent, p)
    cols = {}
    if lod == 0:
        cols = collision(master, coll)
        for nm, ob in cols.items():
            set_pivot(ob, ROOT_A2, V((1, 0, 0)), V((0, 1, 0)), V((0, 0, 1)))
            ob.parent = root
            ob.matrix_parent_inverse = Matrix.Identity(4)
            ob.matrix_world = Matrix.Translation(ROOT_A2)
    # ---- manifest entry
    info = {"file": None, "root": root.name, "objects": {}, "empties": {}, "collision": {}, "tris_total": 0,
            "tris_before_decimation": raw, "decimate_ratio": round(ratio, 4)}
    for part, ob in objs.items():
        par = ob.parent
        e = {"role": part, "parent": par.name, "tris": tris_of(ob),
             "materials": [m.name for m in ob.data.materials] if ob.type == "MESH" else [],
             "pivot_unity_vehicle": a2u_point(ob.matrix_world.translation),
             "local_position_unity": a2u(par.matrix_world.inverted() @ ob.matrix_world.translation)}
        R = ob.matrix_world.to_3x3()
        if R != Matrix.Identity(3):
            e["axes_unity_vehicle"] = {"X": a2u(R.col[0]), "Y": a2u(R.col[2]), "Z": a2u(R.col[1])}
        if part in ANIM:
            e["animation"] = {k: {"local_axis_blender": v[0], "local_axis_unity": v[1], "axis_unity_vehicle":
                                  a2u(R.col["XYZ".index(v[0])]), "convention": v[2]} for k, v in ANIM[part].items()}
        if part.startswith("MIRROR_"):
            e["size_m"] = [round(x, 4) for x in mirrors[part]["size_m"]]
            e["normal_unity_vehicle"] = a2u(R.col[1])
        if part.startswith("WHEEL_"):
            pts = [ob.matrix_world @ v.co for v in ob.data.vertices]
            c = ob.matrix_world.translation
            e["tyre_outer_radius_m"] = round(max(math.hypot(p.y - c.y, p.z - c.z) for p in pts), 4)
            lo, hi = bbox(pts)
            e["width_m"] = round(hi.x - lo.x, 4)
        info["objects"][ob.name] = e
        info["tris_total"] += e["tris"]
    for nm, (eo, parent, p) in empties.items():
        info["empties"][eo.name] = {"parent": eo.parent.name, "position_unity_vehicle": a2u_point(p),
                                    "local_position_unity": a2u(eo.parent.matrix_world.inverted() @ p)}
    for nm, ob in cols.items():
        info["collision"][nm] = {"tris": tris_of(ob), "verts": len(ob.data.vertices), "convex": True,
                                 "parent": root.name}
    # ---- export
    os.makedirs(a.out, exist_ok=True)
    fbx = os.path.join(a.out, f"SM_TruckExterior_LOD{lod}.fbx")
    select([root] + list(root.children_recursive), root)
    bpy.ops.export_scene.fbx(filepath=fbx, use_selection=True, object_types={"EMPTY", "MESH"},
                             apply_unit_scale=True, apply_scale_options="FBX_SCALE_ALL", axis_forward="Z", axis_up="Y",
                             bake_space_transform=True, use_mesh_modifiers=False, mesh_smooth_type="FACE",
                             use_tspace=True, colors_type="SRGB", prioritize_active_color=True, add_leaf_bones=False,
                             bake_anim=False, path_mode="STRIP", embed_textures=False, use_custom_props=False)
    info["file"] = rel(fbx)
    info["file_bytes"] = os.path.getsize(fbx)
    info["build_s"] = round(time.time() - t0, 1)
    manifest["lods"][f"LOD{lod}"] = info
    print(f"LOD{lod}: {info['tris_total']} tris (raw {raw}, ratio {ratio:.3f}), {len(objs)} objects -> {fbx}")
    return root, objs


# ---------------------------------------------------------------- 7. glass interface
def glass_interface(master, path):
    ws = [o for o in master if o.name == "windscreen"][0]
    me = ws.data
    pts = [v.co.copy() for v in me.vertices]
    lo, hi = bbox(pts)
    xb, xt = B.CFG["ws_bottom_x"], B.CFG["ws_top_x"]
    grid = []
    for zi in range(5):
        z = B.WS_Z0 + (B.WS_Z1 - B.WS_Z0) * zi / 4
        row = []
        for xi in range(7):
            hx = xb + (xt - xb) * zi / 4
            x = -hx + 2 * hx * xi / 6
            p = V(B.CAB.front_pt(z, x, 0.004))
            n = B.CAB.normal_front(z, x)
            row.append({"a2": [round(c, 4) for c in p], "unity_cab": a2u(p - CAB_MOUNT), "normal_unity": a2u(n)})
        grid.append(row)

    def corner(x, z, off=0.004):
        p = V(B.CAB.front_pt(z, x, off))
        return {"a2": [round(c, 4) for c in p], "unity_cab": a2u(p - CAB_MOUNT)}
    e = 0.012
    sides = {}
    for s, sd in ((-1, "L"), (1, "R")):
        poly = [(B.WIN_REAR, B.BELT_Z), (B.win_front(B.BELT_Z), B.BELT_Z), (B.win_front(B.WIN_TOP), B.WIN_TOP),
                (B.WIN_REAR, B.WIN_TOP)]
        sides[sd] = {
            "object": f"GLASS_Door{sd}_LOD0 (child of DOOR_{sd}_LOD0: moves with the door)",
            "outline_a2": [[round(c, 4) for c in B.CAB.side_pt(z, y, s, 0.0045)] for y, z in poly],
            "outline_unity_cab": [a2u(V(B.CAB.side_pt(z, y, s, 0.0045)) - CAB_MOUNT) for y, z in poly],
            "outer_surface_x_m": round(s * (G.CAB_HALF_W + 0.0045), 4),
            "front_edge": "follows the A-pillar: y = win_front(z) (body.py)",
            "black_frame_width_m": 0.035,
        }
    data = {
        "asset": "TRAKT exterior A6 - glazing owned by the exterior (single windscreen + door glass)",
        "generator": "tools/blender/truck/exterior/a6_export.py (glass_interface)",
        "frames": {"a2": "Blender/A2: Z up, +Y forward, origin = ground under the front axle, driver = -X",
                   "unity_cab": "Unity axes (x, z, y) relative to CAB_MOUNT_REF (= interior origin, CabPivot)",
                   "cab_mount_ref_a2": list(CAB_MOUNT)},
        "glass_model": "single surface (thin-sheet shader), 4 mm outside the shell skin; the laminated pane is "
                       "~6 mm thick: inner face = outer surface - 6 mm along the normal",
        "windscreen": {
            "object": "GLASS_Windscreen_LOD0 (child of CAB_Body_LOD0)",
            "rake_deg_from_vertical": B.RAKE,
            "glass_edge_z_m": [round(B.WS_Z0 - e, 4), round(B.WS_Z1 + e, 4)],
            "visible_opening_z_m": [B.WS_Z0, B.WS_Z1],
            "half_width_bottom_top_m": [xb, xt],
            "outline_corners_glass_edge": {k: corner(x, z) for k, (x, z) in {
                "bottom_left": (-xb - e, B.WS_Z0 - e), "bottom_right": (xb + e, B.WS_Z0 - e),
                "top_right": (xt + e, B.WS_Z1 + e), "top_left": (-xt - e, B.WS_Z1 + e)}.items()},
            "frit_on_exterior_glass_m": {"bottom": 0.035 + e, "top": 0.10 + e, "sides": 0.028 + e,
                                         "note": "black ceramic band printed on the exterior glass (frit_* geometry, "
                                                 "Trim slot) - the interior must not add a second frit band"},
            "daylight_opening_corners": {k: corner(x, z) for k, (x, z) in {
                "bottom_left": (-xb + 0.028, B.WS_Z0 + 0.035), "bottom_right": (xb - 0.028, B.WS_Z0 + 0.035),
                "top_right": (xt - 0.028, B.WS_Z1 - 0.10), "top_left": (-xt + 0.028, B.WS_Z1 - 0.10)}.items()},
            "surface_grid_outer_5x7": grid,
            "bbox_a2": [[round(c, 4) for c in lo], [round(c, 4) for c in hi]],
        },
        "side_glass": sides,
        "interior_changes_needed": [
            "drop CAB_Glass from the interior FBX (or hide it at runtime when the exterior is present): the exterior "
            "windscreen/door glass is the only glass",
            "windscreen inner trim (A-pillar trims, header, dash top edge, interior frit band) must end on the inner "
            "glass face = surface_grid_outer_5x7 points - 6 mm along normal_unity; glass top edge is 2.972 m (A2 z), "
            "not 3.02 m",
            "remove the interior frit band (ws_frit*) or move it to the exterior glass inner face; exterior frit "
            "widths are listed above",
            "door glass: interior door card window opening = side_glass outline minus the 35 mm black frame",
        ],
    }
    # measured comparison with the committed interior glass (LOD2 FBX), if present
    ip = os.path.join(REPO, "art-source", "truck", "interior", "export", "SM_CabInterior_LOD2.fbx")
    if os.path.exists(ip) and os.path.getsize(ip) > 1000:
        before = set(bpy.data.objects)
        bpy.ops.import_scene.fbx(filepath=ip, axis_forward="Z", axis_up="Y")
        new = [o for o in bpy.data.objects if o not in before]
        ig = next((o for o in new if o.name.startswith("CAB_Glass")), None)
        cmp_ = {}
        if ig is not None:
            ivs = [ig.matrix_world @ v.co for v in ig.data.vertices]
            front = [p for p in ivs if p.y > 0.9]
            ilo, ihi = bbox(front)
            bvh = BVHTree.FromPolygons([ig.matrix_world @ v.co for v in ig.data.vertices],
                                       [list(p.vertices) for p in ig.data.polygons])
            offs = []
            for row in grid:
                for g in row:
                    p = V(g["a2"])
                    n = V((g["normal_unity"][0], g["normal_unity"][2], g["normal_unity"][1]))
                    hit = bvh.ray_cast(p, -n, 0.3)
                    if hit[0] is not None:
                        offs.append(hit[3])
            cmp_["interior_windscreen_z_range_m"] = [round(ilo.z, 4), round(ihi.z, 4)]
            cmp_["interior_windscreen_behind_exterior_m"] = {
                "min": round(min(offs), 4) if offs else None, "max": round(max(offs), 4) if offs else None,
                "mean": round(sum(offs) / len(offs), 4) if offs else None, "samples": len(offs)}
        mir = {}
        for o in new:
            if o.name.startswith("MIRROR_") and o.type == "MESH":
                c = sum((o.matrix_world @ v.co for v in o.data.vertices), V()) / len(o.data.vertices)
                nm = o.name.split("_LOD")[0]
                mir[nm] = [round(x, 4) for x in c]
        cmp_["interior_mirror_quad_centres_a2"] = mir
        data["measured_vs_interior_lod2"] = cmp_
        for o in new:
            bpy.data.objects.remove(o)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
    print("WROTE", path)
    return data


# ---------------------------------------------------------------- 8. QA renders with the game materials
def preview_materials(tex, livery, dirt=0.5, drl=1.0):
    """Cycles stand-in of the shader contract (Kamion/TruckExterior), High textures."""
    lv = LIVERIES[livery]

    def img(slot, kind):
        p = os.path.join(REPO, tex[slot][kind]["High"]["path"])
        im = bpy.data.images.load(p, check_existing=True)
        im.colorspace_settings.name = "sRGB" if (kind == "C" or kind == "RGBA") else "Non-Color"
        return im
    for slot in SLOT_MAT:
        m = bpy.data.materials[SLOT_MAT[slot]]
        nt = m.node_tree
        for n in list(nt.nodes):
            nt.nodes.remove(n)
        out = nt.nodes.new("ShaderNodeOutputMaterial")
        if slot == "Glass":
            col = nt.nodes.new("ShaderNodeVertexColor")
            col.layer_name = "Col"
            tr = nt.nodes.new("ShaderNodeBsdfTransparent")
            nt.links.new(col.outputs["Color"], tr.inputs["Color"])
            gl = nt.nodes.new("ShaderNodeBsdfGlossy")
            gl.inputs["Roughness"].default_value = 0.0
            fr = nt.nodes.new("ShaderNodeLayerWeight")
            fr.inputs["Blend"].default_value = 0.16
            mx = nt.nodes.new("ShaderNodeMixShader")
            nt.links.new(fr.outputs["Fresnel"], mx.inputs[0])
            nt.links.new(tr.outputs[0], mx.inputs[1])
            nt.links.new(gl.outputs[0], mx.inputs[2])
            nt.links.new(mx.outputs[0], out.inputs[0])
            continue
        b = nt.nodes.new("ShaderNodeBsdfPrincipled")
        nt.links.new(b.outputs[0], out.inputs[0])
        if slot == "MirrorRT":
            b.inputs["Base Color"].default_value = (0.9, 0.9, 0.9, 1)
            b.inputs["Metallic"].default_value = 1.0
            b.inputs["Roughness"].default_value = 0.03
            continue
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
        if slot == "Paint":
            mixp = nt.nodes.new("ShaderNodeMix")
            mixp.data_type = "RGBA"
            mixp.blend_type = "MULTIPLY"
            mixp.inputs[0].default_value = 1.0
            nt.links.new(tc.outputs["Color"], mixp.inputs[6])
            mixp.inputs[7].default_value = (*lv["_PaintColor"], 1)
            base = mixp.outputs[2]
            r = nt.nodes.new("ShaderNodeMix")
            r.data_type = "FLOAT"
            nt.links.new(sm.outputs[2], r.inputs[0])
            nt.links.new(tc.outputs["Alpha"], r.inputs[2])
            r.inputs[3].default_value = lv["_PaintRoughness"]
            rough = r.outputs[0]
            metal = M.math_node(nt, "MULTIPLY", sm.outputs[2], lv["_PaintMetallic"])
            coat = M.math_node(nt, "MULTIPLY", sm.outputs[2], lv["_ClearCoat"])
            nt.links.new(coat, b.inputs["Coat Weight"])
            b.inputs["Coat Roughness"].default_value = 0.03
            # decal (uv1)
            du = nt.nodes.new("ShaderNodeUVMap")
            du.uv_map = "Decal"
            td = nt.nodes.new("ShaderNodeTexImage")
            td.image = img("Decal", "RGBA")
            td.extension = "CLIP"
            nt.links.new(du.outputs[0], td.inputs[0])
            md = nt.nodes.new("ShaderNodeMix")
            md.data_type = "RGBA"
            nt.links.new(td.outputs["Alpha"], md.inputs[0])
            nt.links.new(base, md.inputs[6])
            md.inputs[7].default_value = (*lv["_DecalColor"], 1)
            base = md.outputs[2]
            mm = nt.nodes.new("ShaderNodeMix")
            mm.data_type = "FLOAT"
            nt.links.new(td.outputs["Alpha"], mm.inputs[0])
            nt.links.new(metal, mm.inputs[2])
            mm.inputs[3].default_value = lv["_DecalMetallic"]
            metal = mm.outputs[0]
        else:
            rough = tc.outputs["Alpha"]
            metal = sm.outputs[2]
        mixd = nt.nodes.new("ShaderNodeMix")
        mixd.data_type = "RGBA"
        nt.links.new(dmask, mixd.inputs[0])
        nt.links.new(base, mixd.inputs[6])
        mixd.inputs[7].default_value = (*DUST, 1)
        nt.links.new(mixd.outputs[2], b.inputs["Base Color"])
        rr = M.math_node(nt, "ADD", rough, M.math_node(nt, "MULTIPLY", dmask, 0.35), clamp=True)
        nt.links.new(rr, b.inputs["Roughness"])
        nt.links.new(metal, b.inputs["Metallic"])
        if slot == "Lights":
            dv = nt.nodes.new("ShaderNodeUVMap")
            dv.uv_map = "Data"
            sp = nt.nodes.new("ShaderNodeSeparateXYZ")
            nt.links.new(dv.outputs[0], sp.inputs[0])
            on = {"DRL": 14.0 * drl, "MARKER_FRONT": 2.0 * drl, "MARKER_SIDE": 1.5 * drl, "MARKER_REAR": 1.5 * drl,
                  "TAIL_BRAKE": 0.0}
            acc = None
            for gname, strength in on.items():
                if strength <= 0:
                    continue
                gi = LIGHT_GROUPS.index(gname)
                cmp_ = nt.nodes.new("ShaderNodeMath")
                cmp_.operation = "COMPARE"
                cmp_.inputs[1].default_value = gi
                cmp_.inputs[2].default_value = 0.25
                nt.links.new(sp.outputs[0], cmp_.inputs[0])
                cr = nt.nodes.new("ShaderNodeMix")
                cr.data_type = "RGBA"
                cr.blend_type = "MULTIPLY"
                cr.inputs[0].default_value = 1.0
                cr.inputs[6].default_value = (*LIGHT_COLOUR[gname], 1)
                ccol = nt.nodes.new("ShaderNodeCombineColor")
                k = M.math_node(nt, "MULTIPLY", cmp_.outputs[0], strength)
                for i in range(3):
                    nt.links.new(k, ccol.inputs[i])
                nt.links.new(ccol.outputs[0], cr.inputs[7])
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
            if acc is not None:
                nt.links.new(acc, b.inputs["Emission Color"])
                b.inputs["Emission Strength"].default_value = 1.0


def qa_renders(a, tex, lod_roots, manifest):
    if not a.renders:
        return []
    os.makedirs(a.renders, exist_ok=True)
    sc = bpy.context.scene
    S.setup_render("1600x900", a.samples)
    S.yard()
    for o in bpy.data.objects:
        if o.get("group") == "backdrop":
            o.hide_render = False
    out = []

    def show_only(lod):
        for k, r in lod_roots.items():
            for o in [r] + list(r.children_recursive):
                o.hide_render = k != lod
                if o.name.startswith("COL_"):
                    o.hide_render = True

    def cam(view, res=None):
        c = S.CAMS[view]
        cm = S.add_camera("cam_" + view, c["loc"], c.get("target"), c.get("lens", 45), c.get("ortho"), c.get("rot"))
        sc.camera = cm
        if res:
            sc.render.resolution_x, sc.render.resolution_y = res

    def render(name, label):
        S.stamp(label)
        sc.render.filepath = os.path.join(a.renders, name)
        bpy.ops.render.render(write_still=True)
        out.append(sc.render.filepath)
        print("WROTE", sc.render.filepath)
    S.lighting("overcast")
    show_only(0)
    for livery in ("white", "dark"):
        preview_materials(tex, livery)
        cam("34przod", (1600, 900))
        t = manifest["lods"]["LOD0"]["tris_total"]
        render(f"34przod_{livery}_lod0.jpg", f"TRAKT A6 eksport | LOD0 {t} tr. | materiały gry (atlasy) | "
                                             f"{LIVERIES[livery]['label']} | pochmurno")
    preview_materials(tex, "white")
    cam("zbl_reflektor", (1600, 900))
    render("zbl_reflektor_white_lod0.jpg", "TRAKT A6 eksport | LOD0 | zbliżenie: wypalone szczeliny i lampy")
    cam("zbl_stopnie", (1600, 900))
    render("zbl_drzwi_white_lod0.jpg", "TRAKT A6 eksport | LOD0 | drzwi wycięte z kabiny, stopnie")
    for lod in sorted(lod_roots):
        show_only(lod)
        cam("34przod", (960, 540))
        t = manifest["lods"][f"LOD{lod}"]["tris_total"]
        render(f"lod{lod}_34przod.jpg", f"LOD{lod}: {t} trójkątów")
    # pivot debug: doors open, front wheels steered, wipers up, mudflaps swung, axis gizmos
    show_only(0)
    objs = {o.name: o for o in lod_roots[0].children_recursive}
    gizmos = []
    for nm, o in objs.items():
        part = nm.replace("_LOD0", "")
        if part in ANIM or part.startswith(("WHEEL_", "STEER_", "MIRROR_")):
            gizmos += axis_gizmo(o, part)
    rot = {"DOOR_L": ("Z", math.radians(DOOR_OPEN_BLENDER["DOOR_L"] * 0.85)),
           "DOOR_R": ("Z", math.radians(DOOR_OPEN_BLENDER["DOOR_R"] * 0.85)),
           "STEER_FL": ("Z", math.radians(25)), "STEER_FR": ("Z", math.radians(25)),
           "WIPER_L": ("Z", math.radians(WIPE_BLENDER * 0.6)), "WIPER_R": ("Z", math.radians(WIPE_BLENDER * 0.6)),
           "MUDFLAP_RL": ("X", math.radians(20)), "MUDFLAP_RR": ("X", math.radians(20))}
    saved = {}
    for part, (ax, ang) in rot.items():
        o = objs.get(part + "_LOD0")
        if o is None:
            continue
        saved[o.name] = o.matrix_basis.copy()
        o.matrix_basis = o.matrix_basis @ Matrix.Rotation(ang, 4, ax)
    S.lighting("overcast")
    pv = S.add_camera("cam_pivots", (-7.2, 6.4, 4.6), (-0.4, -1.2, 1.2), 38)
    sc.camera = pv
    sc.render.resolution_x, sc.render.resolution_y = 1600, 900
    render("pivoty_34.jpg", "A6 piwoty: drzwi otwarte 68°, koła skręcone 25°, wycieraczki, chlapacze; osie: "
                            "czerwona = X, zielona = Y Unity (góra), niebieska = Z Unity (przód)")
    top = S.add_camera("cam_top", (0.0, -1.6, 30.0), None, 45, 9.5, (0, 0, 0))
    sc.camera = top
    render("pivoty_gora.jpg", "A6 piwoty z góry (ortho): skręt kół wokół osi zwrotnicy, zawiasy drzwi")
    for nm, mb in saved.items():
        bpy.data.objects[nm].matrix_basis = mb
    for g in gizmos:
        bpy.data.objects.remove(g)
    return out


def axis_gizmo(o, part):
    """Coloured arrows for the pivot frame of `o`: Blender local X (red), Z = Unity Y (green), Y = Unity Z (blue)."""
    made = []
    L = 0.32 if part.startswith(("DOOR_", "WHEEL_", "STEER_")) else 0.18
    for ax, rgb in (("X", (1, 0.05, 0.05)), ("Z", (0.05, 1, 0.1)), ("Y", (0.1, 0.3, 1))):
        mname = "gizmo_" + ax
        m = bpy.data.materials.get(mname)
        if m is None:
            m = bpy.data.materials.new(mname)
            m.use_nodes = True
            bs = m.node_tree.nodes["Principled BSDF"]
            bs.inputs["Base Color"].default_value = (*rgb, 1)
            bs.inputs["Emission Color"].default_value = (*rgb, 1)
            bs.inputs["Emission Strength"].default_value = 3.0
        bm = bmesh.new()
        bmesh.ops.create_cone(bm, cap_ends=True, segments=10, radius1=0.012, radius2=0.012, depth=L)
        bm.verts.ensure_lookup_table()
        for v in bm.verts:
            v.co.z += L / 2
        me = bpy.data.meshes.new("gz")
        bm.to_mesh(me)
        bm.free()
        me.materials.append(m)
        g = bpy.data.objects.new(f"gizmo_{o.name}_{ax}", me)
        bpy.context.scene.collection.objects.link(g)
        g.parent = o
        g.matrix_parent_inverse = Matrix.Identity(4)
        g.matrix_basis = {"X": Matrix.Rotation(math.radians(90), 4, "Y"), "Y": Matrix.Rotation(math.radians(-90), 4, "X"),
                          "Z": Matrix.Identity(4)}[ax]
        made.append(g)
    return made


# ---------------------------------------------------------------- manifest pieces
def texel_density(master, tex_res):
    out = {}
    for slot in BAKED:
        mn = SLOT_MAT[slot]
        a3 = auv = 0.0
        for o in master:
            if mirrored_wheel(o):
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
                li = list(p.loop_indices)
                uv = [uvl[i].uv for i in li]
                s = 0.0
                for k in range(1, len(uv) - 1):
                    s += abs((uv[k][0] - uv[0][0]) * (uv[k + 1][1] - uv[0][1]) - (uv[k + 1][0] - uv[0][0]) *
                             (uv[k][1] - uv[0][1])) / 2
                auv += s
        res = tex_res[slot]
        d = res * math.sqrt(auv / a3) if a3 > 0 else 0
        out[slot] = {"area_m2": round(a3, 2), "uv_coverage": round(auv, 3),
                     "px_per_m": {t: round(d / div) for t, div in TIERS.items()}}
    return out


def contract(tex, td):
    return {
        "name": "Kamion/TruckExterior (Shader Graph, URP Lit opaque; Glass = transparent; MirrorRT = unlit RT)",
        "uv0 'Atlas'": "unique atlas UV per slot (right wheels + right caliper reuse the left wheels' UVs mirrored)",
        "uv1 'Decal'": "Paint slot only: decal atlas UV (T_Ext_Decal); (0.002, 0.002) = transparent texel elsewhere",
        "uv2 'Data'": "x = light group id (light_groups), y = emissive mask (1 on lamp emitters); 0 elsewhere",
        "color 'Col'": "sRGB-encoded tint for Glass (windscreen green, lens clear); white elsewhere",
        "textures": "T_Ext_<Slot>_C (RGB albedo sRGB, A roughness), _N (tangent normal, OpenGL +Y), _M (R AO, G dirt "
                    "mask at full strength, B metallic; Paint: B = paint mask), all linear except C.rgb",
        "albedo": "C.rgb; Paint: C.rgb * _PaintColor; then lerp(albedo, _DirtColor, saturate(M.g * _Dirt)); Paint: "
                  "lerp(albedo, _DecalColor, Decal.a)",
        "roughness": "C.a; Paint: lerp(C.a, _PaintRoughness, M.b); + 0.35 * M.g * _Dirt",
        "metallic": "M.b (Trim/Metal/Lights); Paint: _PaintMetallic * M.b, decal -> _DecalMetallic",
        "occlusion": "M.r (URP: indirect/ambient only)",
        "clear_coat": "Paint: _ClearCoat * M.b (URP Complex Lit clear coat, optional on Medium/Low)",
        "emission": "Lights: _LightState[uv2.x] (RGB x intensity, 16x1 texture or array written by the light "
                    "controller) * uv2.y; tail/brake share TAIL_BRAKE (tail ~0.25, brake 1.0)",
        "_Dirt": "0 = washed, 0.5 = look of the A4 renders, 1 = very dirty",
        "_DirtColor": list(DUST),
        "light_groups": {i: g for i, g in enumerate(LIGHT_GROUPS)},
        "light_colours_linear": LIGHT_COLOUR,
        "texel_density": td,
    }


# ---------------------------------------------------------------- main
def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    p = argparse.ArgumentParser()
    p.add_argument("--out", default=os.path.join(REPO, "art-source", "truck", "exterior", "export"))
    p.add_argument("--renders", default=os.path.join(REPO, "docs", "reports", "visual", "truck-A6-exterior"))
    p.add_argument("--no-renders", action="store_true")
    p.add_argument("--bake-scale", type=float, default=1.0)
    p.add_argument("--ao-samples", type=int, default=256)
    p.add_argument("--samples", type=int, default=128)
    p.add_argument("--cage", type=float, default=0.02)
    p.add_argument("--lods", default="0,1,2,3")
    p.add_argument("--blend", default="")
    a = p.parse_args(argv)
    a.out = os.path.abspath(a.out)            # Blender resolves relative output paths against the drive root
    a.renders = "" if a.no_renders else os.path.abspath(a.renders)
    t0 = time.time()
    subpaths, strokes, wm = build_source()
    srcs = [o for o in bpy.data.objects if o.type == "MESH" and o.get("group") in TRUCK_GROUPS]
    apply_modifiers(srcs)
    bake_transforms(srcs)
    for o in srcs:
        o["part"] = part_of(o)
    # wiper pivots (before anything moves): centre of wiper_pivot{k}
    for k in (0, 1):
        pv = bpy.data.objects[f"wiper_pivot{k}"]
        lo, hi = bbox(world_verts(pv))
        pv["centre"] = list((lo + hi) / 2)
    decal_rect = bpy.data.objects["decal_wordmark"]["decal_rect"]
    decal = raster_decal(wm, decal_rect, DECAL_RES)
    # HIGH = untouched full-detail copy (bake source)
    hcoll = new_collection("HIGH")
    high = []
    for o in srcs:
        if o.name.startswith("decal_"):
            continue
        h = copy_object(o, "HI_" + o.name, hcoll)
        h["part"] = o["part"]
        high.append(h)
    # game pieces
    gcoll = new_collection("GAME")
    doors = split_doors(bpy.data.objects["cab_shell"], gcoll)
    mirrors = mirror_quads(gcoll)
    pieces = []
    for o in srcs + list(doors.values()) + list(mirrors.values()):
        if bake_only(o):
            continue
        if o.users_collection[0] != gcoll:
            for c in list(o.users_collection):
                c.objects.unlink(o)
            gcoll.objects.link(o)
        o["part"] = part_of(o)
        pieces.append(o)
    for o in [o for o in srcs if bake_only(o)]:
        bpy.data.objects.remove(o)
    for o in list(bpy.data.objects):
        if o.type == "MESH" and o.get("group") in ("interior_proxy", "mirrors_cam", "figure"):
            bpy.data.objects.remove(o)
    gm = game_materials()
    for o in pieces:
        to_game_piece(o, gm)
    tri_pieces = sum(tris_of(o) for o in pieces)
    removed, tested = remove_hidden(pieces)
    print(f"pieces: {len(pieces)}, tris {tri_pieces} -> {sum(tris_of(o) for o in pieces)}")
    unwrap_atlases(pieces)
    baked = bake_atlases(pieces, high, a)
    tex = compose_textures(baked, decal, a.out)
    for o in high:
        bpy.data.objects.remove(o)
    master = pieces
    td = texel_density(master, {s: ATLAS_RES[s] for s in BAKED})
    manifest = {"asset": "TRAKT tractor exterior (concept B), track A6", "generator": rel(__file__) if False else
                "tools/blender/truck/exterior/a6_export.py", "lods": {}}
    gi = glass_interface(master, os.path.join(REPO, "art-source", "truck", "exterior", "glass_interface.json"))
    lcoll = new_collection("LODS")
    roots = {}
    for lod in [int(x) for x in a.lods.split(",")]:
        root, objs = export_lod(lod, master, mirrors, a, manifest, lcoll)
        roots[lod] = root
    for o in master:
        o.hide_render = True
        o.hide_viewport = True
    manifest.update(meta(tex, td, removed, tested, tri_pieces, gi))
    man_path = os.path.join(a.out, "truck_exterior_manifest.json")
    with open(man_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=1, ensure_ascii=False)
    print("WROTE", man_path)
    if a.blend:
        bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(a.blend))
    if a.renders:
        manifest["qa_renders"] = [rel(x) for x in qa_renders(a, tex, roots, manifest)]
        with open(man_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=1, ensure_ascii=False)
    print(f"A6 exterior done in {time.time() - t0:.0f} s")


def physics_crosscheck():
    """Compare the art dimensions with the physics definition (tractor_4x2_generic.vehicle.json, tyre json)."""
    d = os.path.join(REPO, "game", "Assets", "_Project", "Vehicle", "Physics", "Definitions", "Data")
    res = {"source": rel(d)}
    try:
        veh = json.load(open(os.path.join(d, "tractor_4x2_generic.vehicle.json"), encoding="utf-8"))
        tyre = json.load(open(os.path.join(d, "tire_315_80_r22_5.tire.json"), encoding="utf-8"))
    except OSError as e:
        res["error"] = str(e)
        return res
    ax = {x["name"]: x for x in veh["axles"]}
    wb_phys = ax["front"]["positionZ"] - ax["rear"]["positionZ"]
    rows = [
        ("wheelbase_m", WB, wb_phys),
        ("front_track_m", G.FRONT_TRACK, ax["front"]["trackWidth"]),
        ("rear_track_m (dual-pair centres)", G.REAR_TRACK, ax["rear"]["trackWidth"]),
        ("tyre radius: mesh free / physics rolling", round(G.TYRE_R, 4), tyre["radius"]),
        ("wheel centre height (art, static loaded) / physics rolling radius", G.WHEEL_Z, tyre["radius"]),
        ("fifth wheel height (art) / physics fifthWheel.position.y", G.FIFTH_H, veh["fifthWheel"]["position"]["y"]),
        ("fifth wheel lead (art) / physics fifthWheel.position.z", G.FIFTH_LEAD, veh["fifthWheel"]["position"]["z"]),
        ("cab mount (art CAB_MOUNT_REF, Unity y,z) / physics cab.mountCenter",
         [1.15, round(WB + CAB_MOUNT.y, 3)], [veh["cab"]["mountCenter"]["y"], veh["cab"]["mountCenter"]["z"]]),
        ("rear axle Unity z / physics rear positionZ", 0.0, ax["rear"]["positionZ"]),
    ]
    res["rows"] = []
    for name, art, phys in rows:
        ok = art == phys if not isinstance(art, (int, float)) else abs(art - phys) < 1e-3
        res["rows"].append({"item": name, "art": art, "physics": phys, "match": bool(ok)})
    return res


def meta(tex, td, removed, tested, tri_pieces, gi):
    return {
        "units": "metres",
        "unity_axes": "+X right (passenger side), +Y up, +Z forward; driver at -X (LHD)",
        "frame_mapping": "A2/Blender (x, y, z) -> Unity (x, z, y); FBX axis_forward=Z, axis_up=Y, bake_space_transform,"
                         " FBX_SCALE_ALL (same as the interior). Unity import: Scale Factor 1, Convert Units on, Bake "
                         "Axis Conversion off. Positions below are in the Unity vehicle frame unless marked local.",
        "origin": {"name": "TruckExterior_LODn root", "unity_vehicle": [0.0, 0.0, 0.0],
                   "a2_frame": list(ROOT_A2),
                   "note": "ground under the rear axle centre = physics vehicle frame (VehicleModel, axles positionZ)."
                           " Put the root at the vehicle body origin; CAB_Body moves with the cab suspension."},
        "cab_body": {"pivot": "CAB_MOUNT_REF = interior origin (CabPivot)", "unity_vehicle": a2u_point(CAB_MOUNT),
                     "note": "parent CAB_Body_LODn and CabInterior_LODn under the same cab-suspension transform with "
                             "localPosition 0: the interior then sits exactly in the exterior"},
        "rig_note": "Use the LOD0 hierarchy as the rig (transforms). For LOD1-3 parent each part mesh under the LOD0 "
                    "transform of the same role (CAB_Body, DOOR_L, WHEEL_FL, ...) and put the renderers in a "
                    "LODGroup. LOD3 merges doors, wipers, door glass and mudflaps into CAB_Body / GLASS_Windscreen / "
                    "CHASSIS and has no MIRROR_* quads (LOD2 neither).",
        "lod_targets": {"LOD0": "<= ~100k", "LOD1": "40-45k", "LOD2": "14-15k", "LOD3": "~3k (traffic / impostor "
                                                                                    "distance)"},
        "lod_screen_size_suggestion": {"LOD0": 0.45, "LOD1": 0.18, "LOD2": 0.07, "LOD3": 0.015, "cull": 0.004},
        "hidden_faces": {"removed": removed, "tested": tested, "tris_before_cleanup": tri_pieces,
                         "method": "ray visibility from ~400 exterior points (3 rings x 24 azimuths, 0.3-8 m high, top"
                                   " views) + in-cab eye points; moving parts (doors, wheels, steering, wipers, "
                                   "mudflaps) tested only against themselves; glass treated as transparent"},
        "slots": {s: SLOT_MAT[s] for s in SLOT_MAT},
        "tiers": {"High": "LOD0-1 + High textures", "Medium": "LOD1-2 + Medium textures", "Low": "LOD2-3 + Low "
                                                                                                  "textures",
                  "texture_compression": "ASTC: C 6x6 (High) / 8x8, N 5x5 (High) / 6x6, M 8x8, Decal 6x6; all "
                                         "power-of-two squares, mipmaps on; N and M linear, C sRGB"},
        "textures": tex,
        "liveries": LIVERIES,
        "shader_contract": contract(tex, td),
        "glass": {"owner": "exterior", "interface": "art-source/truck/exterior/glass_interface.json",
                  "objects": ["GLASS_Windscreen", "GLASS_DoorL", "GLASS_DoorR"],
                  "measured_vs_interior": gi.get("measured_vs_interior_lod2", {})},
        "mirrors": {"note": "MIRROR_* quads (uv0 0-1, u = local +X, v = local up) on the mirror glass, normal = local "
                            "+Z (Unity) towards the driver's eye; same names as the interior manifest. With the "
                            "exterior present, use these and disable the interior CAB_ShellPlaceholder + its "
                            "MIRROR_* quads (one quad per mirror)."},
        "physics_crosscheck": physics_crosscheck(),
        "dims_reference": "art-source/truck/dims.json",
    }


if __name__ == "__main__":
    main()
