"""TRAKT A6 — fit check between the exported exterior (owner of the glazing) and the cab interior.

    blender -b --factory-startup --python-exit-code 1 --python tools/blender/truck/check_fit.py -- \
        [--exterior art-source/truck/exterior/export/SM_TruckExterior_LOD0.fbx]
        [--interior art-source/truck/interior/export/SM_CabInterior_LOD1.fbx] [--report OUT.json]

Both FBX files are imported with Blender's default axis handling (it reads the files' GlobalSettings, so the result
is the A2/Blender frame: Z up, +Y forward, origin = ground under the front axle); the exterior root goes to
(0, -WB, 0), the interior root to CAB_MOUNT_REF - exactly how the A7 prefab nests them. Checks:
 1. penetration: every vertex of the interior meshes that stay visible with the exterior present (CAB_Interior,
    steering wheel, stalks, pedals, displays, ...; not CAB_ShellPlaceholder / CAB_Glass_Windows) is ray-tested from
    inside the cab (origins on the cab centre line at the vertex height). A vertex is OUTSIDE when the exterior
    shell, doors or glass is hit before the vertex is reached (tolerance 3 mm). Such vertices show through the glass
    or poke through the skin (crossing counts: glass once, or the opaque skin twice = inner and outer layer). Vertices within 10 mm of an exterior surface are reported as "contacts" (they
    touch the seal / frit and cannot be seen), not as penetrations. Limit: 0 vertices outside in the windscreen /
    side-glass zone, <= 0.2 % elsewhere.
Exit code 1 on failure.
"""
import json
import math
import os
import sys

import bpy
from mathutils import Matrix, Vector as V
from mathutils.bvhtree import BVHTree

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EXT_SHELL = ("CAB_Body", "DOOR_L", "DOOR_R", "GLASS_Windscreen", "GLASS_DoorL", "GLASS_DoorR")
INT_SKIP = ("CAB_ShellPlaceholder", "CAB_Glass_Windows", "MIRROR_")
TOL = 0.003
CONTACT = 0.010    # a vertex nearer than this to the exterior skin / glass counts as contact, not penetration
CAB_MOUNT_A2 = (0.0, 0.225, 1.15)    # interior origin (CAB_MOUNT_REF) in A2 = exterior manifest cab_body pivot


def arg(argv, k, d):
    return argv[argv.index(k) + 1] if k in argv else d


def import_fbx(path, origin_a2):
    """Import with Blender's default axis handling. The importer honours the file's GlobalSettings (written by the
    same exporter), so the result is already the A2 frame (Z up, +Y forward, driver -X); the file root is then put
    at its A2 position (exterior: ground under the rear axle (0, -WB, 0), interior: CAB_MOUNT_REF) - exactly how the
    A7 prefab nests the two. (Raw FBX = (-x, z, y) of A2 = Unity with X negated; see exterior/check_export.py.)"""
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    bpy.context.view_layer.update()
    root = [o for o in new if o.parent is None]
    r = root[0].matrix_world.translation.copy()
    fix = Matrix.Translation(V(origin_a2) - r)
    for o in root:
        o.matrix_world = fix @ o.matrix_world
    bpy.context.view_layer.update()
    return new


def world_tris(objs):
    vs, fs = [], []
    for o in objs:
        me = o.data
        me.calc_loop_triangles()
        b = len(vs)
        mw = o.matrix_world
        vs += [mw @ v.co for v in me.vertices]
        fs += [[b + i for i in t.vertices] for t in me.loop_triangles]
    return vs, fs


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ext = os.path.join(REPO, arg(argv, "--exterior", "art-source/truck/exterior/export/SM_TruckExterior_LOD0.fbx"))
    itr = os.path.join(REPO, arg(argv, "--interior", "art-source/truck/interior/export/SM_CabInterior_LOD1.fbx"))
    rep = arg(argv, "--report", "")
    bpy.ops.wm.read_factory_settings(use_empty=True)
    em = json.load(open(os.path.join(os.path.dirname(ext), "truck_exterior_manifest.json"), encoding="utf-8"))
    eo = [o for o in import_fbx(ext, em["origin"]["a2_frame"]) if o.type == "MESH"
          and o.name.split("_LOD")[0] in EXT_SHELL]
    io = [o for o in import_fbx(itr, CAB_MOUNT_A2) if o.type == "MESH" and not o.name.startswith(INT_SKIP)]
    bpy.context.view_layer.update()
    glass = [o for o in eo if o.name.startswith("GLASS_")]
    opaque = [o for o in eo if o not in glass]
    bvh_g = BVHTree.FromPolygons(*world_tris(glass))
    bvh_o = BVHTree.FromPolygons(*world_tris(opaque))

    def hits(bvh, org, d, L):
        n, t = 0, 0.0
        while t < L - TOL:
            h = bvh.ray_cast(org + d * t, d, L - TOL - t)
            if h[0] is None:
                break
            n += 1
            t += h[3] + 1e-4
        return n
    # sanity: exterior windscreen must be at A2 y ~ 1.0-1.45, z ~1.9-2.97 (B2: lower glass edge 1.928 m)
    ws = [o for o in eo if o.name.startswith("GLASS_Windscreen")][0]
    wv = [ws.matrix_world @ v.co for v in ws.data.vertices]
    frame_ok = 0.9 < max(p.y for p in wv) < 1.5 and 1.85 < min(p.z for p in wv) < 2.1
    res = {"exterior": os.path.relpath(ext, REPO).replace("\\", "/"),
           "interior": os.path.relpath(itr, REPO).replace("\\", "/"),
           "frame_check_windscreen_a2": bool(frame_ok), "objects": {}, "outside_samples": []}
    total = outside = outside_glass = 0
    for o in io:
        mw = o.matrix_world
        n_out = 0
        for v in o.data.vertices:
            p = mw @ v.co
            total += 1
            bad = False
            for org in (V((0.0, max(-0.75, min(1.0, p.y)), p.z)),        # lateral (side walls / doors)
                        V((p.x * 0.4, 0.05, max(1.5, min(3.5, p.z))))):   # from the cab centre (front / corners)
                d = p - org
                L = d.length
                if L < 1e-4:
                    continue
                # outside = beyond the glass (1 crossing) or through the whole skin (inner + outer layer = 2
                # crossings); a vertex inside the 30 mm shell wall or behind a lamp pocket is hidden, not outside
                if hits(bvh_g, org, d / L, L) >= 1 or hits(bvh_o, org, d / L, L) >= 2:
                    bad = True
                    break
            if bad:
                # within CONTACT of an exterior surface = touching (hidden behind the frit / seal), not poking out
                dmin = min(b.find_nearest(p)[3] for b in (bvh_g, bvh_o))
                if dmin < CONTACT:
                    res["contacts"] = res.get("contacts", 0) + 1
                    continue
                n_out += 1
                in_glass_zone = 2.04 < p.z < 2.98 and (p.y > 0.6 or abs(p.x) > 1.0)
                outside_glass += in_glass_zone
                if sum(1 for q in res["outside_samples"] if q["object"] == o.name) < 2000:
                    res["outside_samples"].append({"object": o.name, "a2": [round(c, 3) for c in p],
                                                   "glass_zone": bool(in_glass_zone)})
        outside += n_out
        res["objects"][o.name] = {"verts": len(o.data.vertices), "outside": n_out}
    res["verts_tested"] = total
    res["verts_outside"] = outside
    res["verts_outside_glass_zone"] = outside_glass
    res["outside_fraction"] = round(outside / max(1, total), 5)
    ok = frame_ok and outside_glass == 0 and res["outside_fraction"] <= 0.002
    res["pass"] = bool(ok)
    print(json.dumps({k: v for k, v in res.items() if k != "outside_samples"}, indent=1))
    for s in res["outside_samples"]:
        print("  OUT", s)
    if rep:
        with open(os.path.join(REPO, rep) if not os.path.isabs(rep) else rep, "w", encoding="utf-8") as f:
            json.dump(res, f, indent=1)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
