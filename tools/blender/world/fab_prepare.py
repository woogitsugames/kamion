"""Blender worker for fab/prepare.py; local licensed outputs only, never tracked."""
import json
import sys
from pathlib import Path

import bpy
import bmesh
from mathutils import Vector


def triangles(obj):
    obj.data.calc_loop_triangles()
    return len(obj.data.loop_triangles)


def thin_cards(obj, budget):
    """Remove whole smallest disconnected cards when collapse reaches its floor.

    Scan vegetation contains thousands of disconnected two-triangle leaf cards.
    Collapse cannot reduce those below one triangle each. Keeping the largest
    complete islands preserves UVs and avoids slicing cards into ragged triangles.
    """
    mesh = obj.data
    parent = list(range(len(mesh.vertices)))
    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    for edge in mesh.edges:
        a, b = map(find, edge.vertices)
        parent[b] = a
    islands = {}
    for face in mesh.polygons:
        islands.setdefault(find(face.vertices[0]), []).append(face)
    groups = sorted(islands.values(), key=lambda fs: (-sum(f.area for f in fs), fs[0].index))
    keep, count = set(), 0
    for faces in groups:
        size = sum(len(f.vertices) - 2 for f in faces)
        if count + size <= budget:
            keep.update(f.index for f in faces)
            count += size
    if not keep:
        raise ValueError("Disconnected-card thinning cannot fit any island")
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bm.faces.ensure_lookup_table()
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.index not in keep], context="FACES")
    bm.to_mesh(mesh)
    bm.free()


def main(request):
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    bpy.ops.import_scene.fbx(filepath=request["source"], use_anim=False)
    meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    if not meshes:
        raise ValueError("No meshes in Fab FBX")
    bpy.ops.object.select_all(action="DESELECT")
    for obj in meshes:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    bpy.ops.object.join()
    source = bpy.context.object
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    # Metric dimensions come from FBX importer, not guessed per asset.
    lo = Vector(tuple(min(v.co[i] for v in source.data.vertices) for i in range(3)))
    hi = Vector(tuple(max(v.co[i] for v in source.data.vertices) for i in range(3)))
    center = Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z))
    for vertex in source.data.vertices:
        vertex.co -= center
        # Project props use glTF (-East, Up, North). Blender exporter maps
        # (x,y,z) -> (x,z,-y), so bake the XY half-turn into vertices.
        vertex.co.x *= -1
        vertex.co.y *= -1
    dims = list(hi - lo)
    before = triangles(source)
    mat = bpy.data.materials.new(request["prototype"])
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    bsdf = nodes.get("Principled BSDF")
    textures = request.get("textures", {})
    for channel, socket in (("basecolor", "Base Color"), ("roughness", "Roughness"),
                            ("metalness", "Metallic"), ("opacity", "Alpha")):
        if channel not in textures:
            continue
        tex = nodes.new("ShaderNodeTexImage")
        tex.image = bpy.data.images.load(textures[channel])
        if channel != "basecolor":
            tex.image.colorspace_settings.name = "Non-Color"
        mat.node_tree.links.new(tex.outputs["Color"], bsdf.inputs[socket])
    if "normal" in textures:
        tex = nodes.new("ShaderNodeTexImage")
        tex.image = bpy.data.images.load(textures["normal"])
        tex.image.colorspace_settings.name = "Non-Color"
        normal = nodes.new("ShaderNodeNormalMap")
        mat.node_tree.links.new(tex.outputs["Color"], normal.inputs["Color"])
        mat.node_tree.links.new(normal.outputs["Normal"], bsdf.inputs["Normal"])
    if "opacity" in textures:
        mat.surface_render_method = "DITHERED"
    # Do not clear materials (project rule). Every face points to our final slot.
    source.data.materials.append(mat)
    index = len(source.data.materials) - 1
    for face in source.data.polygons:
        face.material_index = index
    destination = Path(request["output"])
    destination.mkdir(parents=True, exist_ok=True)
    lods = []
    objects = []
    for lod, budget in enumerate(request["budgets"]):
        obj = source.copy()
        obj.data = source.data.copy()
        bpy.context.collection.objects.link(obj)
        bpy.ops.object.select_all(action="DESELECT")
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        obj.name = request["prototype"] + (".lod" + str(lod) if lod else "")
        # Collapse modifier preserves UVs and silhouette; measure actual output,
        # repeat if Blender's estimate overshoots the absolute triangle budget.
        for _ in range(5):
            count = triangles(obj)
            if count <= budget:
                break
            modifier = obj.modifiers.new("mobile_lod", "DECIMATE")
            modifier.ratio = min(0.99, budget / count * 0.98)
            modifier.use_collapse_triangulate = True
            bpy.ops.object.modifier_apply(modifier=modifier.name)
        count = triangles(obj)
        if count > budget:
            thin_cards(obj, budget)
            count = triangles(obj)
        # Some source leaf cards contain duplicate corners. Clean the reduced
        # topology before counting/exporting instead of relying on exporter repair.
        obj.data.validate(verbose=False, clean_customdata=True)
        obj.data.update()
        count = triangles(obj)
        if count > budget or count == 0:
            raise ValueError(f"LOD {lod} invalid triangle count: {count}/{budget}")
        path = destination / (request["prototype"] + ".lod" + str(lod) + ".glb")
        bpy.ops.export_scene.gltf(filepath=str(path), export_format="GLB", use_selection=True,
                                  export_yup=True, export_animations=False, export_cameras=False,
                                  export_lights=False, export_materials="EXPORT")
        lods.append({"lod": lod, "path": str(path), "triangles": count, "budget": budget})
        objects.append(obj)
    bpy.ops.object.select_all(action="DESELECT")
    for obj in objects:
        obj.select_set(True)
    combined = destination / (request["prototype"] + ".glb")
    bpy.ops.export_scene.gltf(filepath=str(combined), export_format="GLB", use_selection=True,
                              export_yup=True, export_animations=False, export_cameras=False,
                              export_lights=False, export_materials="EXPORT")
    report = {"variant": request["variant"], "source_triangles": before,
              "path": str(combined),
              "dimensions_m": dims, "scale_status": "FBX declared units; placement scale WORKING_VALUE",
              "foliage_reduction": "collapse then smallest disconnected card removal when required",
              "lods": lods}
    (destination / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main(json.loads(Path(sys.argv[sys.argv.index("--") + 1]).read_text(encoding="utf-8")))
