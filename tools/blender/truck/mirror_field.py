"""TRAKT - does the class VI front mirror really show the road in front of the bumper (own vehicle in the way)?

    blender -b --factory-startup --python-exit-code 1 --python tools/blender/truck/mirror_field.py -- \
        [--exterior .../SM_TruckExterior_LOD0.fbx] [--interior .../SM_CabInterior_LOD0.fbx] [--report OUT.json]
        [--min 0.95]

UN Regulation No 46, para 15.2.4.6.1 (class VI; consolidated text OJ EU L 237, 8.8.2014, CELEX 42014X0808(02), the
source of ADR 0042): the driver must see at least a flat horizontal part of the road bounded by (a) the transverse
vertical plane through the outermost point of the front of the cab, (b) the transverse plane 2000 mm in front of it,
(c) the longitudinal plane through the outermost side of the vehicle on the driver's side, (d) the longitudinal plane
2000 mm outside the outermost side opposite the driver; the front corner opposite the driver may be rounded off with
a radius of 2000 mm.

The EditMode test MirrorFieldOfVisionTests projects that field into the mirror camera (MirrorOptics.Build: camera at
the mirror image of the eye, half field = atan(s / d) + 2 s / R) but leaves the own vehicle out. This tool repeats the
same optics on the exported FBX (glass frame from the manifest next to the exterior FBX) and adds what the test
cannot: (1) the eye must see the glass (exterior + interior, windows transparent), (2) the reflected ray from the
glass to every field point must not end in the truck (cab nose, visor, bumper). A field point counts when it is in
the view cone and the segment glass -> ground is free. Exit code 1 below --min coverage or when the glass is hidden.
"""
import json
import math
import os
import sys

import bpy
from mathutils import Vector as V
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import check_fit as CF  # noqa: E402

WB = 3.70
RADIUS = 0.30            # TruckAssetBuilder.MirrorRadius("MIRROR_Front") (R46 minimum for class VI: 300 mm)
SIDE = 1.275             # half of the 2.55 m combination width (MirrorFieldOfVisionTests.Side)
N = 41                   # field grid per axis (5 cm x 11 cm cells)
ROLE = "MIRROR_Front"
MIRROR_CLEAR = 0.25      # m round every MIRROR_* glass centre (and the class VI arm above its head): not "the front"


def u2a(v):              # Unity vehicle frame (x right, y up, z forward, origin rear axle) -> A2 direction
    return V((v[0], v[2], v[1]))


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ext = os.path.join(CF.REPO, CF.arg(argv, "--exterior", "art-source/truck/exterior/export/SM_TruckExterior_LOD0.fbx"))
    itr = os.path.join(CF.REPO, CF.arg(argv, "--interior", "art-source/truck/interior/export/SM_CabInterior_LOD0.fbx"))
    rep = CF.arg(argv, "--report", "")
    need = float(CF.arg(argv, "--min", "0.95"))
    dims = json.load(open(os.path.join(CF.REPO, "art-source/truck/dims.json"), encoding="utf-8"))
    eye = V(dims["values"]["driver_eye_point_m"]["value"])
    man = json.load(open(os.path.join(os.path.dirname(ext), "truck_exterior_manifest.json"), encoding="utf-8"))
    info = next(v for v in man["lods"]["LOD0"]["objects"].values() if v.get("role") == ROLE)
    pu = info["pivot_unity_vehicle"]
    centre = V((pu[0], pu[2] - WB, pu[1]))
    normal = u2a(info["normal_unity_vehicle"]).normalized()
    up = u2a(info["axes_unity_vehicle"]["Y"]).normalized()
    gw, gh = info["size_m"]

    bpy.ops.wm.read_factory_settings(use_empty=True)
    eo = [o for o in CF.import_fbx(ext, (0.0, -WB, 0.0)) if o.type == "MESH" and not o.name.startswith("COL_")]
    io = [o for o in CF.import_fbx(itr, CF.CAB_MOUNT_A2) if o.type == "MESH" and not o.name.startswith(CF.INT_SKIP)]
    bpy.context.view_layer.update()
    vs, fs, owner = [], [], []
    mcs = []
    for o in eo:        # mirror heads are not the vehicle front
        if o.name.startswith("MIRROR_"):
            mcs.append(sum((o.matrix_world @ v.co for v in o.data.vertices), V()) / len(o.data.vertices))
    front_y, front_who = -1e9, ""
    for o, kind in [(o, "EXT") for o in eo] + [(o, "INT") for o in io]:
        me = o.data
        me.calc_loop_triangles()
        mw = o.matrix_world
        b = len(vs)
        pts = [mw @ v.co for v in me.vertices]
        vs += pts
        name = o.name.split("_LOD")[0]
        if kind == "EXT" and not name.startswith(("MIRROR_", "WIPER_")) and "mirror" not in name.lower():
            used = {i for t in me.loop_triangles for i in t.vertices
                    if "MirrorRT" not in (me.materials[t.material_index].name if me.materials else "")}
            for i in used:
                # R46 15.2.4.6.1 (a): front of the vehicle cab; mirrors and their arms are not the vehicle front
                if pts[i].y > front_y and all((pts[i] - mc).length > MIRROR_CLEAR for mc in mcs)                         and not (pts[i].z > centre.z and pts[i].y > centre.y - 0.12 and abs(pts[i].x - centre.x) < 0.2):
                    front_y, front_who = pts[i].y, name
        for t in me.loop_triangles:
            mat = me.materials[t.material_index].name if me.materials else ""
            if "Glass" in mat or (name.startswith("MIRROR_") and "Mirror" in mat):
                continue
            fs.append([b + i for i in t.vertices])
            owner.append(name)
    bvh = BVHTree.FromPolygons(vs, fs)

    # MirrorOptics.Build
    cam = eye - 2.0 * (eye - centre).dot(normal) * normal
    f = centre - cam
    d = f.length
    f /= d
    right = up.cross(f).normalized()          # Unity LookRotation(f, up): right = up x f (left-handed), mirrored here
    upc = f.cross(right).normalized()
    if upc.dot(up) < 0:
        upc = -upc
    hh = math.atan(gw * 0.5 / d) + gw / RADIUS
    vh = math.atan(gh * 0.5 / d) + gh / RADIUS
    th, tv = math.tan(hh), math.tan(vh)

    # (1) the glass from the eye
    seen = tot = 0
    block = {}
    rt = up.cross(normal).normalized()
    for i in range(9):
        for j in range(9):
            p = centre + rt * gw * (i / 8 - 0.5) * 0.96 + up * gh * (j / 8 - 0.5) * 0.96
            tot += 1
            dd = p - eye
            loc, nrm, idx, dist = bvh.ray_cast(eye, dd.normalized(), dd.length - 0.012)
            if idx is None:
                seen += 1
            else:
                block[owner[idx]] = block.get(owner[idx], 0) + 1

    # (2) the field
    x0, x1, y0, y1 = -SIDE, SIDE + 2.0, front_y, front_y + 2.0
    incone = free = cnt = 0
    who, rows, hb = {}, [], None
    for b in range(N):
        y = y1 - (y1 - y0) * b / (N - 1)
        line = ""
        for a in range(N):
            x = x0 + (x1 - x0) * a / (N - 1)
            # corner opposite the driver may be rounded off with R 2000 mm
            cx, cy = x1 - 2.0, y1 - 2.0
            if x > cx and y > cy and math.hypot(x - cx, y - cy) > 2.0:
                line += " "
                continue
            cnt += 1
            g = V((x, y, 0.0))
            v = g - cam
            z = v.dot(f)
            if z <= 1e-4 or abs(v.dot(right) / z) > th or abs(v.dot(upc) / z) > tv:
                line += "o"
                continue
            incone += 1
            # the convex glass: the ray to this field point leaves the glass at the matching point of the quad
            q = (centre + rt * (1.0 if rt.dot(right) > 0 else -1.0) * (v.dot(right) / z / th) * gw * 0.5
                 + up * (v.dot(upc) / z / tv) * gh * 0.5)
            dd = g - q
            loc, nrm, idx, dist = bvh.ray_cast(q + dd.normalized() * 0.02, dd.normalized(), dd.length - 0.03)
            if idx is None:
                free += 1
                line += "."
            else:
                who[owner[idx]] = who.get(owner[idx], 0) + 1
                hb = [loc.x, loc.x, loc.y, loc.y, loc.z, loc.z] if hb is None else [
                    min(hb[0], loc.x), max(hb[1], loc.x), min(hb[2], loc.y), max(hb[3], loc.y), min(hb[4], loc.z),
                    max(hb[5], loc.z)]
                line += "#"
        rows.append(f"y={y:5.2f} {line}")
    out = {"regulation": "UN R46 para 15.2.4.6.1 (OJ EU L 237, 8.8.2014)",
           "front_plane_y_a2": round(front_y, 4), "front_plane_part": front_who,
           "field_x0x1y0y1_a2": [round(v, 3) for v in (x0, x1, y0, y1)], "grid_points": cnt,
           "glass_centre_a2": [round(c, 4) for c in centre], "glass_size_m": [gw, gh], "radius_m": RADIUS,
           "axis_pitch_deg": round(math.degrees(math.asin(f.z)), 1),
           "half_field_deg": [round(math.degrees(hh), 1), round(math.degrees(vh), 1)],
           "glass_visible_from_eye": round(seen / tot, 3), "glass_blockers": block,
           "field_in_view_cone": round(incone / cnt, 4), "field_seen_past_own_vehicle": round(free / cnt, 4),
           "field_blockers": dict(sorted(who.items(), key=lambda kv: -kv[1])[:6]),
           "blocker_hits_bbox_x0x1y0y1z0z1": [round(v, 3) for v in hb] if hb else None, "min_required": need}
    out["pass"] = out["glass_visible_from_eye"] >= 0.999 and out["field_seen_past_own_vehicle"] >= need
    print("\n".join(rows))
    print("[mirror_field] legend: . seen  # own vehicle in the way  o outside the mirror image; driver side left, "
          "far edge on top")
    for k, v in out.items():
        print(f"[mirror_field] {k}: {v}")
    if rep:
        os.makedirs(os.path.dirname(os.path.abspath(rep)), exist_ok=True)
        json.dump(out, open(rep, "w", encoding="utf-8"), indent=1)
    print("[mirror_field]", "PASS" if out["pass"] else "FAIL")
    if not out["pass"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
