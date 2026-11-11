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
    parser.add_argument("--exterior-lod", type=int, choices=(0, 1, 2), default=0, help="Low uses exterior LOD2 but keeps interior and mirror glass LOD0")
    parser.add_argument("--open-housing-ablation", action="store_true", help="diagnostic only: omit flat forward housing caps")
    parser.add_argument("--housing-recess-mm", type=float, default=0, help="diagnostic only: recess backing behind adjustable glass")
    parser.add_argument("--preview-dir", default="", help="clay/magenta source visibility renders, NOT game-material evidence")
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
    bpy.context.view_layer.update()
    manifest = json.load(open(os.path.join(BI.REPO, "art-source/truck/exterior/export/truck_exterior_manifest.json")))
    lod = manifest["lods"]["LOD0"]
    def axis(v):
        return Vector((v[0], v[2], v[1]))
    offset = BI.EYE - axis(lod["empties"]["EYE_POINT"]["position_unity_vehicle"])
    roles = {info["role"]: info for info in lod["objects"].values()}
    caps = []
    for side in ("L", "R"):
        main, wide = roles["MIRROR_Main" + side], roles["MIRROR_Wide" + side]
        centre = axis(main["pivot_unity_vehicle"]) + offset
        up = axis(main["axes_unity_vehicle"]["Y"])
        right = axis(main["axes_unity_vehicle"]["X"])
        normal = axis(main["normal_unity_vehicle"])
        down = (axis(wide["pivot_unity_vehicle"]) + offset - centre).dot(up)
        caps.append((centre, right, up, normal, main["size_m"][0] / 2 + .025,
                     down - wide["size_m"][1] / 2 - .025, main["size_m"][1] / 2 + .025))
    omitted = 0
    moved = 0
    if args.include_exterior:
        outer = manifest["lods"]["LOD" + str(args.exterior_lod)]
        bpy.ops.import_scene.fbx(filepath=os.path.join(BI.REPO, outer["file"]))
        for obj in bpy.context.selected_objects:
            info = outer["objects"].get(obj.name)
            if obj.type == "MESH" and info and not info["role"].startswith(("GLASS_", "MIRROR_")):
                objects.append(obj)
        if args.preview_dir and args.exterior_lod != 0:
            # Runtime keeps the LOD0 glass quads on Low. Opaque LOD0 parts stay hidden in the preview.
            bpy.ops.import_scene.fbx(filepath=os.path.join(BI.REPO, lod["file"]))
        bpy.context.view_layer.update()
        dg = bpy.context.evaluated_depsgraph_get()
    for obj in objects:
        evaluated = obj.evaluated_get(dg)
        mesh = evaluated.to_mesh()
        base = len(vertices)
        world_points = [obj.matrix_world @ v.co for v in mesh.vertices]
        if obj.name == "CAB_Body_LOD" + str(args.exterior_lod) and args.housing_recess_mm:
            depth = args.housing_recess_mm / 1000
            for i, point in enumerate(world_points):
                for c, r, u, n, w, lo, hi in caps:
                    delta = point - c
                    d = delta.dot(n)
                    if abs(delta.dot(r)) <= w - .019 and lo + .019 <= delta.dot(u) <= hi - .019 and -depth < d <= .002:
                        world_points[i] = point - n * (d + depth)
                        moved += 1
                        break
        vertices.extend(world_points)
        if args.preview_dir and obj.name == "CAB_Body_LOD" + str(args.exterior_lod) and args.housing_recess_mm:
            inverse = obj.matrix_world.inverted()
            if len(mesh.vertices) != len(obj.data.vertices):
                raise ValueError("Imported CAB_Body has unexpected modifiers; cannot preview by vertex index")
            for vertex, world in zip(obj.data.vertices, world_points):
                vertex.co = inverse @ world
            obj.data.update()
        for face in mesh.polygons:
            points = [world_points[i] for i in face.vertices]
            face_normal = (points[1] - points[0]).cross(points[2] - points[0]).normalized()
            if args.open_housing_ablation and obj.name == "CAB_Body_LOD" + str(args.exterior_lod) and any(
                face_normal.dot(n) > .995 and all(abs((p - c).dot(r)) <= w and lo <= (p - c).dot(u) <= hi
                                                  and -.012 <= (p - c).dot(n) <= .002 for p in points)
                for c, r, u, n, w, lo, hi in caps
            ):
                omitted += 1
                continue
            faces.append([base + i for i in face.vertices])
            owners.append(obj.name)
        evaluated.to_mesh_clear()
    bvh = BVHTree.FromPolygons(vertices, faces)
    eye_unity = lod["empties"]["EYE_POINT"]["position_unity_vehicle"]
    # Match the ocular point rather than hard-coding the front-axle offset.
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
            if args.preview_dir and args.include_exterior:
                from mathutils import Matrix
                obj = bpy.data.objects[role + "_LOD0"]
                obj.matrix_world = Matrix.Translation(centre) @ turn.to_matrix().to_4x4() @ Matrix.Translation(-centre) @ obj.matrix_world
        width, height = info["size_m"][:2]
        blockers = Counter()
        blocker_gaps = {}
        nu, nv = 15, 21
        for i in range(nu):
            for j in range(nv):
                point = centre + x * width * ((i + .5) / nu - .5) + y * height * ((j + .5) / nv - .5)
                ray = point - BI.EYE
                hit = bvh.ray_cast(BI.EYE, ray.normalized(), ray.length - .002)
                if hit[0] is not None:
                    owner = owners[hit[2]]
                    blockers[owner] += 1
                    blocker_gaps.setdefault(owner, []).append((point - hit[0]).length)
        results[role] = dict(samples=nu * nv, blocked=sum(blockers.values()),
                             visible_fraction=1 - sum(blockers.values()) / (nu * nv), blockers=dict(blockers),
                             blocker_distance_to_glass_m={name: dict(min=min(gaps), max=max(gaps), mean=sum(gaps) / len(gaps))
                                                          for name, gaps in blocker_gaps.items()})
    scope = "Interior and opaque exterior" if args.include_exterior else "Interior only; exterior obstruction excluded"
    output = dict(scope=scope + "; glass adjustment from TruckAssetBuilder; no transparency attenuation or reflected-field compliance verdict",
                  exterior_lod=args.exterior_lod, housing_cap_faces_omitted=omitted, housing_vertices_recessed=moved, results=results)
    os.makedirs(os.path.dirname(os.path.abspath(args.report)), exist_ok=True)
    with open(args.report, "w") as report:
        json.dump(output, report, indent=2)
    print("MIRROR_SIGHTLINES", json.dumps(output))
    if args.preview_dir:
        preview(args.preview_dir, objects, roles, axis, offset)


def preview(directory, opaque, roles, axis, offset):
    """Uniform clay geometry and magenta glass distinguish occlusion from missing mirror texture content."""
    allowed = {obj.name for obj in opaque}
    clay = bpy.data.materials.new("Audit_Clay")
    clay.diffuse_color = (.18, .18, .18, 1)
    glass = bpy.data.materials.new("Audit_Glass_Magenta")
    glass.diffuse_color = (1, 0, 1, 1)
    for obj in bpy.data.objects:
        is_mirror = obj.name.startswith("MIRROR_") and obj.name.endswith("_LOD0")
        if obj.type != "MESH":
            continue
        obj.hide_render = obj.name not in allowed and not is_mirror
        material = glass if is_mirror else clay
        for i in range(len(obj.data.materials)):
            obj.data.materials[i] = material
        if not obj.data.materials:
            obj.data.materials.append(material)
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.display.shading.light = "STUDIO"
    scene.display.shading.color_type = "MATERIAL"
    scene.display.shading.show_shadows = False
    scene.display.shading.show_cavity = True
    scene.render.resolution_x, scene.render.resolution_y = 960, 444
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    os.makedirs(directory, exist_ok=True)
    for side in ("L", "R"):
        centre = sum((axis(roles["MIRROR_" + name + side]["pivot_unity_vehicle"]) + offset
                      for name in ("Main", "Wide")), Vector()) / 2
        camera = bpy.data.objects.new("AuditEye_" + side, bpy.data.cameras.new("AuditEye_" + side))
        scene.collection.objects.link(camera)
        camera.location = BI.EYE
        camera.rotation_euler = (centre - BI.EYE).to_track_quat("-Z", "Y").to_euler()
        camera.data.sensor_fit = "VERTICAL"
        camera.data.sensor_height = 24
        camera.data.lens = 24 / (2 * math.tan(math.radians(20)))
        scene.camera = camera
        scene.render.filepath = os.path.abspath(os.path.join(directory, "mirror-" + side + ".png"))
        bpy.ops.render.render(write_still=True)


if __name__ == "__main__":
    main()

