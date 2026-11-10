"""TRAKT — what hides the near-side forward view from the driver's eye point (A-pillar wedge).

    blender -b --factory-startup --python tools/blender/truck/pillar_obstruction.py -- \
        [--exterior .../SM_TruckExterior_LOD0.fbx] [--interior .../SM_CabInterior_LOD1.fbx] [--report OUT.json]

Imports the exported exterior + interior exactly as check_fit.py nests them and casts rays from the eye point
(dims.json driver_eye_point_m) in the horizontal plane and at +-6 deg pitch, azimuth -90 (left) .. +20 deg, step
0.25 deg. A ray is blocked when its first non-glass hit lies within 3.5 m (cab, trims, mirrors). Reports, per pitch,
the blocked spans in the left-front sector (-80 .. -10 deg) with the objects that block, and the total blocked angle.
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

EYE = V((-0.55, 0.45, 2.50))
SECTOR = (-80.0, -10.0)


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ext = os.path.join(CF.REPO, CF.arg(argv, "--exterior", "art-source/truck/exterior/export/SM_TruckExterior_LOD0.fbx"))
    itr = os.path.join(CF.REPO, CF.arg(argv, "--interior", "art-source/truck/interior/export/SM_CabInterior_LOD1.fbx"))
    rep = CF.arg(argv, "--report", "")
    bpy.ops.wm.read_factory_settings(use_empty=True)
    objs = [o for o in CF.import_fbx(ext, (0.0, -3.70, 0.0)) if o.type == "MESH" and not o.name.startswith("COL_")]
    objs += [o for o in CF.import_fbx(itr, CF.CAB_MOUNT_A2) if o.type == "MESH" and not o.name.startswith(CF.INT_SKIP)]
    bpy.context.view_layer.update()
    vs, fs, owner = [], [], []
    for o in objs:
        me = o.data
        me.calc_loop_triangles()
        mw = o.matrix_world
        b = len(vs)
        vs += [mw @ v.co for v in me.vertices]
        for t in me.loop_triangles:
            mat = me.materials[t.material_index].name if me.materials else ""
            if "Glass" in mat:
                continue
            fs.append([b + i for i in t.vertices])
            owner.append(o.name.split("_LOD")[0])
    bvh = BVHTree.FromPolygons(vs, fs)
    out = {}
    for pitch in (-6.0, 0.0, 6.0):
        spans, cur, total = [], None, 0.0
        a = SECTOR[0]
        while a <= SECTOR[1] + 1e-6:
            ra, rp = math.radians(a), math.radians(pitch)
            d = V((math.sin(ra) * math.cos(rp), math.cos(ra) * math.cos(rp), math.sin(rp)))
            loc, nrm, idx, dist = bvh.ray_cast(EYE, d, 3.5)
            if idx is not None:
                total += 0.25
                if cur is None:
                    cur = {"from": a, "to": a, "objects": {}}
                cur["to"] = a
                cur["objects"][owner[idx]] = cur["objects"].get(owner[idx], 0) + 1
                if "--hits" in argv and pitch == 0.0 and abs(a - round(a)) < 1e-6:
                    print(f"HIT az {a:.0f}: {owner[idx]} at ({loc.x:.3f}, {loc.y:.3f}, {loc.z:.3f}) dist {dist:.2f}")
            elif cur is not None:
                spans.append(cur)
                cur = None
            a += 0.25
        if cur is not None:
            spans.append(cur)
        for s in spans:
            s["width_deg"] = round(s["to"] - s["from"] + 0.25, 2)
        out[f"pitch_{pitch:+.0f}"] = {"blocked_deg_in_sector": round(total, 2), "spans": spans}
        print(f"OBSTRUCTION pitch {pitch:+.0f}: blocked {total:.2f} deg of {SECTOR}; " +
              "; ".join(f"[{s['from']:.1f}..{s['to']:.1f}] {s['width_deg']} deg {s['objects']}" for s in spans))
    if rep:
        json.dump(out, open(rep, "w", encoding="utf-8"), indent=1)


if __name__ == "__main__":
    main()
