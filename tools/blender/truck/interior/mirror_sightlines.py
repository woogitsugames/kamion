"""ADR 0104: eye-to-glass obstruction by interior trim (not the reflected R46 field).

Run with Blender --python-exit-code 1 --python <this file> -- --report <json>.
Uses exterior-manifest glass centres/axes and builder glass-adjuster targets; excludes
transparent glass and removed interior shell placeholders. --include-exterior also
includes opaque exported exterior geometry. This diagnoses visibility of the glass,
not compliance of the reflected field; confirm against rendered frames.
"""
import argparse
from collections import Counter
import json
import math
import os
import re
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
    parser.add_argument("--include-exterior", action="store_true", help="include opaque exterior FBX geometry")
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
    manifest = json.load(open(os.path.join(BI.REPO, "art-source/truck/exterior/export/truck_exterior_manifest.json")))
    lod = manifest["lods"]["LOD0"]
    if args.include_exterior:
        bpy.ops.import_scene.fbx(filepath=os.path.join(BI.REPO, manifest["lods"]["LOD0"]["file"]))
        for obj in bpy.context.selected_objects:
            info = lod["objects"].get(obj.name)
            if obj.type == "MESH" and info and not info["role"].startswith(("GLASS_", "MIRROR_")):
                objects.append(obj)
        bpy.context.view_layer.update()
        dg = bpy.context.evaluated_depsgraph_get()
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
    eye_unity = lod["empties"]["EYE_POINT"]["position_unity_vehicle"]
    # Match the ocular point rather than hard-coding the front-axle offset.
    def axis(v):
        return Vector((v[0], v[2], v[1]))
    offset = BI.EYE - axis(eye_unity)
    # Read authored targets from their owning source rather than maintain another target table.
    builder = open(os.path.join(BI.REPO, "game/Assets/_Project/Editor/Setup/TruckAssetBuilder.cs")).read()
    targets = re.findall(r'\{ "(MIRROR_[^"]+)", \(([-\d.]+)f, ([-\d.]+)f\)', builder)
    aims = {role: (math.radians(float(yaw)), math.radians(float(pitch))) for role, yaw, pitch in targets}
    if set(aims) != {"MIRROR_MainR", "MIRROR_WideL", "MIRROR_WideR"}:
        raise ValueError("MirrorAim source format/roles changed; update audit parser")
    results = {}
    for info in lod["objects"].values():
        role = info["role"]
        if not role.startswith("MIRROR_"):
            continue
        centre = axis(info["pivot_unity_vehicle"]) + offset
        x = axis(info["axes_unity_vehicle"]["X"])
        y = axis(info["axes_unity_vehicle"]["Y"])
        if role in aims:
            yaw, pitch = aims[role]
            direction = axis((math.sin(yaw) * math.cos(pitch), math.sin(pitch), -math.cos(yaw) * math.cos(pitch)))
            want = (direction - (centre - BI.EYE).normalized()).normalized()
            normal = axis(info["normal_unity_vehicle"]).normalized()
            turn = normal.rotation_difference(want)
            if abs(turn.angle) > math.radians(10.0001):
                raise ValueError(f"{role}: adjuster exceeds builder limit")
            x, y = turn @ x, turn @ y
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
    scope = "Interior and opaque exterior" if args.include_exterior else "Interior only; exterior obstruction excluded"
    output = dict(scope=scope + "; glass adjustment from TruckAssetBuilder; no transparency attenuation or reflected-field compliance verdict", results=results)
    os.makedirs(os.path.dirname(os.path.abspath(args.report)), exist_ok=True)
    with open(args.report, "w") as report:
        json.dump(output, report, indent=2)
    print("MIRROR_SIGHTLINES", json.dumps(output))


if __name__ == "__main__":
    main()
