"""Blender CPU artifact export only. No production source/assets touched.
blender -b --factory-startup -P artifacts/firestation-r10/export_fir_proxy.py
"""
import json
from pathlib import Path
import bpy
import numpy as np

out=Path(__file__).resolve().parent/'shape-candidates'
d=json.loads((out/'fir-proxy-source-model.json').read_text())
for ob in list(bpy.data.objects):bpy.data.objects.remove(ob,do_unlink=True)
for lod,data in enumerate(d['lods']):
    name='landmark_fire_station_jrg2'+('' if lod==0 else f'.lod{lod}')
    v=np.array(data['V']);en=v[:,:1]*d['axis_u']+v[:,1:2]*d['axis_v']+(np.array(d['axis_origin'])-np.array(d['anchor'][:2]))
    vb=np.c_[-en[:,0],-en[:,1],v[:,2]]
    mesh=bpy.data.meshes.new(name);mesh.from_pydata(vb.tolist(),[],data['F'])
    layer=mesh.uv_layers.new(name='UVMap');i=0
    for faceuv in data['UV']:
        for uv in faceuv:layer.data[i].uv=uv;i+=1
    names=sorted(set(data['M']))
    for name_mat in names:
        mat=bpy.data.materials.get(name_mat) or bpy.data.materials.new(name_mat)
        mat.use_nodes=True;mesh.materials.append(mat)
    for p,mat in zip(mesh.polygons,data['M']):p.material_index=names.index(mat)
    mesh.update();ob=bpy.data.objects.new(name,mesh);bpy.context.scene.collection.objects.link(ob)
bpy.ops.export_scene.gltf(filepath=str(out/'fir-proxy-artifact.glb'),export_format='GLB',export_yup=True,
    export_materials='EXPORT',export_image_format='NONE',export_animations=False,export_cameras=False,export_lights=False)
print('FIR_PROXY_ARTIFACT_EXPORT_OK')
