"""Blender geometry diagnostic only; Unity/phone validation remains mandatory."""
import json
import math
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
MAIN = Path('C:/Users/matma/Documents/Claude/kamion')
cams = json.loads((OUT / 'cameras.json').read_text(encoding='utf-8'))['cameras']
for stage, source in [('before', MAIN), ('after', ROOT)]:
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    sc = bpy.context.scene
    sc.render.engine = 'BLENDER_EEVEE_NEXT'
    sc.render.resolution_x, sc.render.resolution_y = 960, 540
    sc.render.resolution_percentage = 100
    world = bpy.data.worlds.new(stage)
    world.use_nodes = True
    world.node_tree.nodes['Background'].inputs['Color'].default_value = (.65, .67, .7, 1)
    world.node_tree.nodes['Background'].inputs['Strength'].default_value = .8
    sc.world = world
    root = bpy.data.objects.new('world_root', None)
    root.rotation_euler.z = math.pi
    sc.collection.objects.link(root)
    for i, j in [(1,3), (1,4), (2,3), (2,4)]:
        old = set(bpy.data.objects)
        bpy.ops.import_scene.gltf(filepath=str(source / f'Data/raw/derived/bialystok-industrial-c/world/chunk_{i}_{j}.low.glb'))
        for ob in set(bpy.data.objects) - old:
            if ob.type != 'MESH' or ob.name.split('.')[0] not in {'road', 'bridge', 'terrain_lod2', 'markings'}:
                bpy.data.objects.remove(ob, do_unlink=True)
            else:
                ob.parent = root
    for mat in bpy.data.materials:
        if mat.use_nodes:
            bsdf = mat.node_tree.nodes.get('Principled BSDF')
            if bsdf:
                bsdf.inputs['Roughness'].default_value = .85
    bpy.ops.object.light_add(type='SUN', rotation=(math.radians(28), math.radians(-15), math.radians(50)))
    bpy.context.object.data.energy = 1.4
    bpy.context.object.data.angle = .3
    for cam in cams:
        cd = bpy.data.cameras.new(cam['id'])
        co = bpy.data.objects.new(cam['id'], cd)
        sc.collection.objects.link(co)
        co.location = cam['pos']
        co.rotation_euler = (Vector(cam['look_at']) - co.location).to_track_quat('-Z','Y').to_euler()
        cd.angle = 2 * math.atan(math.tan(math.radians(cam['fov_deg'])/2)*16/9)
        cd.clip_end = 1000
        sc.camera = co
        sc.render.filepath = str(OUT / 'geometry-preview' / f'{stage}-{cam["id"]}.png')
        Path(sc.render.filepath).parent.mkdir(exist_ok=True)
        bpy.ops.render.render(write_still=True)
