"""TRAKT - can a camera in front of the truck see the cab interior through the exterior skin?

    blender -b --factory-startup --python-exit-code 1 --python tools/blender/truck/front_leak.py -- \
        [--exterior .../SM_TruckExterior_LOD0.fbx] [--interior .../SM_CabInterior_LOD0.fbx] [--report OUT.json]
        [--zone x0,x1,z0,z1] [--map] [--detail]

Review r6 E-N2 / ADR 0047 r7: the black "holes" at the wrapped corners of the T bar were holes - the game camera
truck-34 saw the cab interior through the exterior. Imports the exported exterior LODn and the interior exactly as
check_fit.py nests them and casts rays from a fan of eye points in front of the cab (truck-34 and its mirror image,
straight ahead, low, high, side) through a grid on the plane y = GRID_Y covering the mask, the T bar, the wrapped
corners, the lamps and the cowl. Per ray the first surface decides: exterior glass is transparent, exterior faces
count only when they face the eye (the game culls back faces), interior faces count from both sides (strictest
reading). A ray leaks when it reaches the interior without having passed through a window (GLASS_*; a clear lamp
lens is no window).
Exit code 1 when any eye point has a leaking ray inside the zone.
"""
import json
import os
import sys

import bpy
from mathutils import Vector as V
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import check_fit as CF  # noqa: E402

EXT_ORIGIN = (0.0, -3.70, 0.0)
GRID_Y = 1.40
# x0, x1, z0, z1 [m] on the plane y = GRID_Y. r7b: mask + T bar + corners + cowl (z 1.25-1.95 m). r7c: the whole
# front of the cab, from the bumper below the tilt joint (cab lower edge 1.225 m) to the roof: the header above the
# windscreen and the joint leaked too. Rays through the windscreen do not count (they pass a window).
ZONE = (-1.34, 1.34, 1.00, 3.72)
STEP = 0.01
EYES = {   # A2 frame (y forward, z up, origin under the front axle)
    "truck-34": (-6.8, 7.8, 2.1),
    "truck-34-mirror": (6.8, 7.8, 2.1),
    "front": (0.0, 12.0, 1.7),
    "front-low": (-3.0, 9.0, 0.6),
    "front-high": (3.5, 8.0, 3.6),
    "side-34": (-9.0, 4.5, 1.8),
}


def build(objs_kind):
    vs, fs, owner = [], [], []
    for o, kind in objs_kind:
        me = o.data
        me.calc_loop_triangles()
        mw = o.matrix_world
        b = len(vs)
        vs += [mw @ v.co for v in me.vertices]
        for t in me.loop_triangles:
            mat = me.materials[t.material_index].name if me.materials else ""
            fs.append([b + i for i in t.vertices])
            owner.append((kind, o.name.split("_LOD")[0], mat))
    return BVHTree.FromPolygons(vs, fs), owner


def first_surface(bvh, owner, eye, d, far=40.0):
    """-> (kind, name, mat, point, through_glass, culled) of the first surface the game would draw on this ray;
    culled = exterior back faces skipped on the way (name of the last one)."""
    o, glass, culled = eye, False, ""
    for _ in range(64):
        loc, nrm, idx, dist = bvh.ray_cast(o, d, far)
        if idx is None:
            return None
        kind, name, mat = owner[idx]
        o = loc + d * 1e-4
        if kind == "EXT":
            if "Glass" in mat:
                glass = glass or name.startswith("GLASS_")    # lamp lenses are clear too, but no window
                continue
            if nrm.dot(d) > 0.0:     # back face: culled in the game
                culled = f"{name}/{mat}"
                continue
        return kind, name, mat, loc, glass, culled
    return None


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ext = os.path.join(CF.REPO, CF.arg(argv, "--exterior", "art-source/truck/exterior/export/SM_TruckExterior_LOD0.fbx"))
    itr = os.path.join(CF.REPO, CF.arg(argv, "--interior", "art-source/truck/interior/export/SM_CabInterior_LOD0.fbx"))
    rep = CF.arg(argv, "--report", "")
    zone = tuple(float(v) for v in CF.arg(argv, "--zone", ",".join(str(v) for v in ZONE)).split(","))
    bpy.ops.wm.read_factory_settings(use_empty=True)
    objs = [(o, "EXT") for o in CF.import_fbx(ext, EXT_ORIGIN) if o.type == "MESH" and not o.name.startswith("COL_")]
    objs += [(o, "INT") for o in CF.import_fbx(itr, CF.CAB_MOUNT_A2)
             if o.type == "MESH" and not o.name.startswith(CF.INT_SKIP)]
    bpy.context.view_layer.update()
    bvh, owner = build(objs)
    x0, x1, z0, z1 = zone
    nx, nz = int(round((x1 - x0) / STEP)) + 1, int(round((z1 - z0) / STEP)) + 1
    out, fail = {}, False
    for ename, e in EYES.items():
        eye = V(e)
        leaks, who, rows, bbox, hb, samples = 0, {}, [], None, None, []
        for iz in range(nz):
            z = z1 - iz * STEP
            line = ""
            for ix in range(nx):
                x = x0 + ix * STEP
                d = (V((x, GRID_Y, z)) - eye).normalized()
                h = first_surface(bvh, owner, eye, d)
                if h is None:
                    line += " "
                elif h[0] == "INT" and not h[4]:
                    leaks += 1
                    key = f"{h[1]}/{h[2]}" + (f" (behind culled {h[5]})" if h[5] else "")
                    who[key] = who.get(key, 0) + 1
                    bbox = (x, x, z, z) if bbox is None else (min(bbox[0], x), max(bbox[1], x), min(bbox[2], z),
                                                              max(bbox[3], z))
                    p = h[3]
                    hb = [p.x, p.x, p.y, p.y, p.z, p.z] if hb is None else [min(hb[0], p.x), max(hb[1], p.x),
                                                                              min(hb[2], p.y), max(hb[3], p.y),
                                                                              min(hb[4], p.z), max(hb[5], p.z)]
                    if leaks % 97 == 1:
                        samples.append([round(x, 2), round(z, 2)] + [round(c, 3) for c in p])
                    line += "#"
                else:
                    line += "g" if h[4] else "."
            rows.append(f"z={z:.2f} {line}")
        out[ename] = {"rays": nx * nz, "leaks": leaks,
                      "grid_bbox_x0x1z0z1": [round(v, 2) for v in bbox] if bbox else None,
                      "hit_bbox_x0x1y0y1z0z1": [round(v, 3) for v in hb] if hb else None,
                      "interior_seen": dict(sorted(who.items(), key=lambda kv: -kv[1])[:6])}
        if "--detail" in argv:
            out[ename]["samples_gridx_gridz_hitxyz"] = samples[:12]
        fail |= leaks > 0
        print(f"[front_leak] {ename}: {leaks} / {nx * nz} rays reach the interior past the skin; grid bbox "
              f"{out[ename]['grid_bbox_x0x1z0z1']}, hit bbox {out[ename]['hit_bbox_x0x1y0y1z0z1']}")
        if leaks:
            print("[front_leak]   seen:", out[ename]["interior_seen"])
        if "--map" in argv and leaks:
            print("\n".join(r[:7] + r[7::2] for k, r in enumerate(rows) if k % 2 == 0))
    res = {"exterior": os.path.basename(ext), "interior": os.path.basename(itr), "zone": zone, "step_m": STEP,
           "eyes": out, "pass": not fail}
    if rep:
        os.makedirs(os.path.dirname(os.path.abspath(rep)), exist_ok=True)
        json.dump(res, open(rep, "w", encoding="utf-8"), indent=1)
    print("[front_leak]", "PASS" if not fail else "FAIL")
    if fail:
        sys.exit(1)


if __name__ == "__main__":
    main()
