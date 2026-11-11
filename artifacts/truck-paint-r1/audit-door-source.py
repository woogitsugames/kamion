import bpy,json,sys,os,hashlib
from pathlib import Path
from mathutils import Vector
import numpy as np
root=Path(__file__).resolve().parents[2]
source=root/'art-source/truck/exterior/export/SM_TruckExterior_LOD0.fbx'
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(source),use_custom_normals=True)
rows=[]
for o in bpy.data.objects:
 if o.type!='MESH' or not o.name.startswith('DOOR_'):continue
 me=o.data;me.calc_loop_triangles();me.calc_tangents(uvmap=me.uv_layers.active.name)
 samples=[];triangles=[]
 for tri in me.loop_triangles:
  slot=me.materials[tri.material_index]
  if slot is None or 'Paint' not in slot.name:continue
  points=[o.matrix_world@me.vertices[i].co for i in tri.vertices]
  centre=sum(points,Vector())/3
  normal=o.matrix_world.to_3x3()@tri.normal
  area=(points[1]-points[0]).cross(points[2]-points[0]).length*.5
  triangles.append(dict(centre=list(centre),normal=list(normal),area=area))
  for li in tri.loops:
   loop=me.loops[li];co=o.matrix_world@me.vertices[loop.vertex_index].co
   n=(o.matrix_world.to_3x3()@loop.normal).normalized();t=(o.matrix_world.to_3x3()@loop.tangent).normalized();uv=me.uv_layers.active.data[li].uv
   samples.append(dict(co=list(co),normal=list(n),tangent=list(t),sign=loop.bitangent_sign,uv=list(uv)))
 rows.append(dict(name=o.name,matrix=[list(r) for r in o.matrix_world],bounds=[list(o.matrix_world@Vector(c)) for c in o.bound_box],paintTriangles=triangles,paintLoopSamples=samples))
out=root/'artifacts/truck-paint-r1/door-source-mesh.json'
out.write_text(json.dumps(dict(source=str(source.relative_to(root)),sha256=hashlib.sha256(source.read_bytes()).hexdigest(),rows=rows),indent=2))
print('DOOR_SOURCE_AUDIT_OK',len(rows),str(out))
