"""ADR 0104: eye-to-glass obstruction by interior trim (not the reflected R46 field).

Run with Blender --python-exit-code 1 --python <this file> -- --report <json>.
Uses exterior-manifest glass centres/axes; excludes transparent glass and the removed
interior shell placeholders. Exterior housings and glass-adjuster rotation are NOT
modelled: this is an interior obstruction diagnostic, not a compliance verdict.
"""
import argparse
from collections import Counter
import json
import os
import sys

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import a6_export as EX
import build_interior as BI


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", required=True)
    args = parser.parse_args(argv)
    saved = sys.argv
    sys.argv = [saved[0], "--", "--out", "artifacts", "--no-backdrop"]
    build_args = BI.parse_args()
    sys.argv = saved
    BI.build(build_args)
    dg = bpy.context.evaluated_depsgraph_get()
    vertices, faces, owners = [], [], []
    objects = [o for o in bpy.data.objects if o.type == "MESH" and not o.get("decal")
               and EX.group_of(o.name) not in ("CAB_ShellPlaceholder", "CAB_Glass_Windows", "CAB_Glass")
               and not EX.group_of(o.name).startswith("MIRROR_")]
    BI.fit_to_exterior(objects)
    for obj in objects:
        evaluated = obj.evaluated_get(dg)
        mesh = evaluated.to_mesh()
        base = len(vertices)
        vertices.extend(obj.matrix_world @ v.co for v in mesh.vertices)
        for face in mesh.polygons:
            faces.append([base + i for i in face.vertices])
            owners.append(obj.name)
        evaluated.to_mesh_clear()
    bvh = BVHTree.FromPolygons(vertices, faces)
    manifest = json.load(open(os.path.join(BI.REPO, "art-source/truck/exterior/export/truck_exterior_manifest.json")))
    lod = manifest["lods"]["LOD0"]
    eye_unity = lod["empties"]["EYE_POINT"]["position_unity_vehicle"]
    # Match the ocular point rather than hard-coding the front-axle offset.
    def axis(v):
        return Vector((v[0], v[2], v[1]))
    offset = BI.EYE - axis(eye_unity)
    results = {}
    for info in lod["objects"].values():
        role = info["role"]
        if not role.startswith("MIRROR_"):
            continue
        centre = axis(info["pivot_unity_vehicle"]) + offset
        x = axis(info["axes_unity_vehicle"]["X"])
        y = axis(info["axes_unity_vehicle"]["Y"])
        width, height = info["size_m"][:2]
        blockers = Counter()
        nu, nv = 15, 21
        for i in range(nu):
            for j in range(nv):
                point = centre + x * width * ((i + .5) / nu - .5) + y * height * ((j + .5) / nv - .5)
                ray = point - BI.EYE
                hit = bvh.ray_cast(BI.EYE, ray.normalized(), ray.length - .002)
                if hit[0] is not None:
                    blockers[owners[hit[2]]] += 1
        results[role] = dict(samples=nu * nv, blocked=sum(blockers.values()),
                             visible_fraction=1 - sum(blockers.values()) / (nu * nv), blockers=dict(blockers))
    output = dict(scope="Interior-only obstruction, nominal modelled glass, no exterior housings or adjuster rotation", results=results)
    os.makedirs(os.path.dirname(os.path.abspath(args.report)), exist_ok=True)
    with open(args.report, "w") as report:
        json.dump(output, report, indent=2)
    print("MIRROR_SIGHTLINES", json.dumps(output))


if __name__ == "__main__":
    main()
