"""Blender-only geometry diagnostic while PHONE_RUN excludes Unity; not an editor/device proof."""
import bpy
import json
import math
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'artifacts/furniture-r1'
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(ROOT/'Data/raw/derived/bialystok-industrial-c/furniture-r1-after/props/street_props.glb'))
defs=json.loads((ROOT/'Data/raw/derived/bialystok-industrial-c/furniture-r1-after/region/world_manifest.json').read_text())['materials']
# Library GLB embeds the neutral atlas with factor=1; Unity supplies the pigment from the region manifest.
for mat in bpy.data.materials:
    if not mat.name.startswith('furniture_'): continue
    bsdf=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
    link=bsdf.inputs['Base Color'].links[0]
    source=link.from_socket; mat.node_tree.links.remove(link)
    mix=mat.node_tree.nodes.new('ShaderNodeMixRGB'); mix.blend_type='MULTIPLY'; mix.inputs[0].default_value=1
    mix.inputs[2].default_value=(*defs[mat.name]['color'],1)
    mat.node_tree.links.new(source,mix.inputs[1]); mat.node_tree.links.new(mix.outputs[0],bsdf.inputs['Base Color'])
selected = ['lamp_12m','lamp_old_concrete_9m','lamp_old_steel_8m','plate_B-33_70','sign_post','bollard','bollard_hoop']
positions = [-9,-5,-1,3,3,6,9]
bounds = {}
for obj in list(bpy.context.scene.objects):
    obj.hide_render = obj.name not in selected
for name,x in zip(selected, positions):
    obj=bpy.data.objects.get(name)
    if obj is None:
        raise RuntimeError('Missing prototype '+name)
    bpy.ops.object.select_all(action='DESELECT')
    obj.hide_set(False); obj.select_set(True); bpy.context.view_layer.objects.active=obj
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    obj.location.x=x
    if name.startswith('plate_'): obj.location.z=2.5
    if name=='sign_post': obj.scale.z=2.75
    bpy.context.view_layer.update()
    bounds[name]={'min_z':min((obj.matrix_world@Vector(v)).z for v in obj.bound_box),
                  'max_z':max((obj.matrix_world@Vector(v)).z for v in obj.bound_box)}
    if name=='sign_post': continue
    curve=bpy.data.curves.new(name+'_label','FONT'); curve.body=name.replace('lamp_','').replace('plate_','')
    curve.size=.24; curve.align_x='CENTER'
    label=bpy.data.objects.new(name+'_label',curve); bpy.context.collection.objects.link(label)
    label.location=(x,-.9,.015)
bpy.ops.mesh.primitive_plane_add(size=200, location=(0,0,.005))
mat=bpy.data.materials.new('diagnostic neutral ground'); mat.diffuse_color=(.28,.29,.30,1)
bpy.context.object.data.materials.append(mat)
scene=bpy.context.scene; scene.render.engine='BLENDER_EEVEE_NEXT'
scene.world=bpy.data.worlds.new('neutral diagnostic sky'); scene.world.use_nodes=True
scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.6,.65,.7,1)
scene.world.node_tree.nodes['Background'].inputs[1].default_value=.8
bpy.ops.object.light_add(type='AREA', location=(-4,-8,18)); bpy.context.object.data.energy=2600; bpy.context.object.data.shape='DISK'; bpy.context.object.data.size=12
bpy.context.object.rotation_euler=(Vector((0,0,4))-bpy.context.object.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add(location=(15,-26,12))
camera=bpy.context.object; camera.rotation_euler=(Vector((0,0,5.5))-camera.location).to_track_quat('-Z','Y').to_euler()
camera.data.type='ORTHO'; camera.data.ortho_scale=25
scene.camera=camera; scene.render.resolution_x=960; scene.render.resolution_y=720; scene.render.resolution_percentage=100
scene.view_settings.view_transform='AgX'; scene.render.image_settings.file_format='PNG'
scene.render.filepath=str(OUT/'blender-prototypes.png'); bpy.ops.render.render(write_still=True)
for label,pos,target,size in [('sign-back',(5,5,3.1),(3,0,2.5),1.8),
                              ('old-steel-foot',(-3,2,1),(-1,0,.55),1.8)]:
    camera.location=pos; camera.rotation_euler=(Vector(target)-camera.location).to_track_quat('-Z','Y').to_euler()
    camera.data.ortho_scale=size
    scene.render.filepath=str(OUT/f'blender-{label}.png'); bpy.ops.render.render(write_still=True)
(OUT/'blender-prototype-bounds.json').write_text(json.dumps(bounds,indent=2)+'\n')
print('FURNITURE_PREVIEW_OK')
