"""Offline emissive scan photobase bake; invoked by fab/grass_surface.py."""
import json
import sys
from pathlib import Path

import bpy


def main(request):
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    bpy.ops.import_scene.gltf(filepath=request["mesh"])
    meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    source = next(o for o in meshes if o.name == request["prototype"])
    for obj in list(bpy.context.scene.objects):
        if obj != source:
            bpy.data.objects.remove(obj, do_unlink=True)
    world = source.matrix_world.copy()
    source.parent = None
    source.matrix_world = world
    bpy.context.view_layer.objects.active = source
    source.select_set(True)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    material = bpy.data.materials.new("fab_grass_emissive_bake")
    material.use_nodes = True
    material.surface_render_method = "DITHERED"
    nodes, links = material.node_tree.nodes, material.node_tree.links
    output = nodes.get("Material Output")
    image = nodes.new("ShaderNodeTexImage")
    image.image = bpy.data.images.load(request["basecolor"])
    emission = nodes.new("ShaderNodeEmission")
    links.new(image.outputs["Color"], emission.inputs["Color"])
    transparent = nodes.new("ShaderNodeBsdfTransparent")
    cutoff = nodes.new("ShaderNodeMath")
    cutoff.operation = "GREATER_THAN"
    cutoff.inputs[1].default_value = .5
    links.new(image.outputs["Alpha"], cutoff.inputs[0])
    mix = nodes.new("ShaderNodeMixShader")
    links.new(cutoff.outputs[0], mix.inputs[0])
    links.new(transparent.outputs[0], mix.inputs[1])
    links.new(emission.outputs[0], mix.inputs[2])
    links.new(mix.outputs[0], output.inputs["Surface"])
    source.data.materials.append(material)
    for face in source.data.polygons:
        face.material_index = len(source.data.materials) - 1
    for item in request["instances"]:
        obj = source.copy()
        obj.data = source.data
        bpy.context.collection.objects.link(obj)
        obj.location = (item["x"], item["y"], 0)
        obj.rotation_euler = (0, 0, item["yaw"])
    bpy.data.objects.remove(source, do_unlink=True)
    bpy.ops.mesh.primitive_plane_add(size=request["tile_m"], location=(0, 0, -.005))
    floor = bpy.context.object
    floor_material = bpy.data.materials.new("neutral_grass_floor_emissive")
    floor_material.use_nodes = True
    nodes = floor_material.node_tree.nodes
    emission = nodes.new("ShaderNodeEmission")
    emission.inputs["Color"].default_value = (*request["floor_linear_rgb"], 1)
    floor_material.node_tree.links.new(emission.outputs[0], nodes.get("Material Output").inputs["Surface"])
    floor.data.materials.append(floor_material)
    bpy.ops.object.camera_add(location=(0, 0, 10))
    camera = bpy.context.object
    camera.rotation_euler = (0, 0, 0)
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = request["tile_m"]
    scene = bpy.context.scene
    scene.camera = camera
    scene.render.engine = "BLENDER_EEVEE_NEXT"
    scene.render.resolution_x = scene.render.resolution_y = request["resolution"]
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "None"
    scene.view_settings.exposure = 0
    scene.view_settings.gamma = 1
    scene.world.color = (0, 0, 0)
    scene.render.film_transparent = False
    scene.render.filepath = request["output"]
    scene.render.image_settings.color_depth = "8"
    bpy.ops.wm.save_as_mainfile(filepath=str(Path(request["output"]).with_suffix(".blend")))
    bpy.ops.render.render(write_still=True)


if __name__ == "__main__":
    main(json.loads(Path(sys.argv[sys.argv.index("--") + 1]).read_text(encoding="utf-8")))
