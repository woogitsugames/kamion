"""TRAKT — how much of every mirror glass the driver really sees from the eye point.

    blender -b --factory-startup --python tools/blender/truck/mirror_visibility.py -- \
        [--exterior .../SM_TruckExterior_LOD0.fbx] [--interior .../SM_CabInterior_LOD1.fbx] [--report OUT.json]

Imports the exported exterior + interior exactly as check_fit.py nests them. Every MIRROR_* quad of the exterior is
sampled on a grid (barycentric points of its triangles); a sample is visible when the ray from the eye point
(dims.json driver_eye_point_m) reaches it without hitting opaque geometry (glass slots are transparent, the mirror's
own triangles are skipped). Reports the visible share per mirror, the direction of its centre from the eye (azimuth
right of straight ahead, pitch) and what blocks the hidden samples. Review r6 follow-up of ADR 0042 / 0047.
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
N = 6   # barycentric subdivisions per triangle


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ext = os.path.join(CF.REPO, CF.arg(argv, "--exterior", "art-source/truck/exterior/export/SM_TruckExterior_LOD0.fbx"))
    itr = os.path.join(CF.REPO, CF.arg(argv, "--interior", "art-source/truck/interior/export/SM_CabInterior_LOD1.fbx"))
    rep = CF.arg(argv, "--report", "")
    bpy.ops.wm.read_factory_settings(use_empty=True)
    objs = [o for o in CF.import_fbx(ext, (0.0, -3.70, 0.0)) if o.type == "MESH" and not o.name.startswith("COL_")]
    objs += [o for o in CF.import_fbx(itr, CF.CAB_MOUNT_A2) if o.type == "MESH" and not o.name.startswith(CF.INT_SKIP)]
    bpy.context.view_layer.update()
    vs, fs, owner, mirrors = [], [], [], {}
    for o in objs:
        me = o.data
        me.calc_loop_triangles()
        mw = o.matrix_world
        b = len(vs)
        vs += [mw @ v.co for v in me.vertices]
        name = o.name.split("_LOD")[0]
        for t in me.loop_triangles:
            mat = me.materials[t.material_index].name if me.materials else ""
            if name.startswith("MIRROR_") and "Mirror" in mat:
                mirrors.setdefault(name, []).append([mw @ me.vertices[i].co for i in t.vertices])
                continue
            if "Glass" in mat:
                continue
            fs.append([b + i for i in t.vertices])
            owner.append(name)
    bvh = BVHTree.FromPolygons(vs, fs)
    out = {}
    for name, tris in sorted(mirrors.items()):
        seen = total = 0
        block = {}
        cen = V((0, 0, 0))
        for a, b_, c in tris:
            for i in range(N):
                for j in range(N - i):
                    u, v = (i + 1 / 3) / N, (j + 1 / 3) / N
                    p = a + (b_ - a) * u + (c - a) * v
                    cen += p
                    total += 1
                    d = p - EYE
                    loc, nrm, idx, dist = bvh.ray_cast(EYE, d.normalized(), d.length - 0.012)
                    if idx is None:
                        seen += 1
                    else:
                        block[owner[idx]] = block.get(owner[idx], 0) + 1
        cen /= total
        d = (cen - EYE).normalized()
        out[name] = {"visible": round(seen / total, 3), "azimuth_right_deg": round(math.degrees(math.atan2(d.x, d.y)), 1),
                     "pitch_deg": round(math.degrees(math.asin(d.z)), 1), "centre": [round(x, 3) for x in cen],
                     "blockers": dict(sorted(block.items(), key=lambda kv: -kv[1])[:4])}
        print(f"MIRROR {name}: visible {100 * seen / total:.0f} % az {out[name]['azimuth_right_deg']} pitch "
              f"{out[name]['pitch_deg']} centre {out[name]['centre']} blockers {out[name]['blockers']}")
    if rep:
        json.dump(out, open(rep, "w", encoding="utf-8"), indent=1)


if __name__ == "__main__":
    main()
