"""Render the isolated linden study from eight azimuths for each geometry LOD.

Example, run from this worktree after generating the study GLB:
  blender -b --factory-startup -P artifacts/knyszyn-rynek-0227/linden-review.py

Optional after ``--``: --glb PATH --out PATH. Both must remain under artifacts.
Images are inspection aids, not Unity output or visual acceptance.
"""
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[2]
ART = (ROOT / "artifacts").resolve()
ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def option(name, default):
    if name not in ARGS:
        return default
    index = ARGS.index(name) + 1
    if index >= len(ARGS):
        raise ValueError(f"{name} requires a path")
    return Path(ARGS[index])


def under_artifacts(path):
    path = path.resolve()
    if not path.is_relative_to(ART):
        raise ValueError(f"Path must be inside {ART}: {path}")
    return path


def main():
    source = under_artifacts(option("--glb", ART / "knyszyn-rynek-0227/linden-study/tree_linden_park_study.glb"))
    output = under_artifacts(option("--out", ART / "knyszyn-rynek-0227/linden-study/review"))
    if not source.is_file():
        raise FileNotFoundError(source)
    output.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(source))
    models = {}
    for lod, name in (("lod0", "tree_linden_park_0"), ("lod1", "tree_linden_park_0.lod1")):
        matches = [o for o in bpy.context.scene.objects if o.type == "MESH" and o.name == name]
        if len(matches) != 1:
            raise RuntimeError(f"Expected exactly one {name} mesh, found {len(matches)}")
        models[lod] = matches[0]
    points = [obj.matrix_world @ Vector(corner) for obj in models.values() for corner in obj.bound_box]
    center = Vector([(min(p[i] for p in points) + max(p[i] for p in points)) / 2 for i in range(3)])
    width = max(max(p.x for p in points)-min(p.x for p in points), max(p.y for p in points)-min(p.y for p in points))
    height = max(p.z for p in points)-min(p.z for p in points)
    if min(width, height) <= 0:
        raise RuntimeError("Invalid tree bounds")

    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 32
    scene.cycles.use_denoising = True
    scene.render.resolution_x = scene.render.resolution_y = 1024
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    scene.world = bpy.data.worlds.new("Neutral studio")
    scene.world.use_nodes = True
    background = scene.world.node_tree.nodes.get("Background")
    background.inputs["Color"].default_value = (.30, .30, .30, 1.)
    background.inputs["Strength"].default_value = .8
    scene.view_settings.view_transform = "Standard"

    light_data = bpy.data.lights.new("Soft daylight", "AREA")
    light_data.energy = 1600
    light_data.shape = "DISK"
    light_data.size = max(width, height)
    light = bpy.data.objects.new("Soft daylight", light_data)
    scene.collection.objects.link(light)
    light.location = center + Vector((width, -width, height))
    light.rotation_euler = (center-light.location).to_track_quat("-Z", "Y").to_euler()

    camera_data = bpy.data.cameras.new("Review camera")
    camera = bpy.data.objects.new("Review camera", camera_data)
    scene.collection.objects.link(camera)
    scene.camera = camera
    camera_data.type = "ORTHO"
    camera_data.ortho_scale = max(height, width * math.sqrt(2)) * 1.20
    distance = max(width, height) * 3.0
    # Looking horizontally at crown centre keeps every comparison at the same elevation.
    for lod, model in models.items():
        for other in models.values():
            other.hide_render = other != model
        for step in range(8):
            angle = 2 * math.pi * step / 8
            camera.location = center + Vector((distance*math.cos(angle), distance*math.sin(angle), 0.))
            camera.rotation_euler = (center-camera.location).to_track_quat("-Z", "Y").to_euler()
            scene.render.filepath = str(output / f"{lod}-az{step*45:03d}.png")
            bpy.ops.render.render(write_still=True)
    print(f"Rendered 16 study views to {output}")


if __name__ == "__main__":
    main()
