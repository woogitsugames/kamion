"""Read-only metric UV inspection of the actual exported cab FBX."""
import json
from pathlib import Path
import bpy
import numpy as np
ROOT = Path(__file__).resolve().parents[2]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(ROOT/'art-source/truck/interior/export/SM_CabInterior_LOD0.fbx'))
objects=[]; rows=[]
for obj in bpy.data.objects:
 if obj.type!='MESH':continue
 mesh=obj.data;mesh.calc_loop_triangles()
 points=[obj.matrix_world@v.co for v in mesh.vertices]
 objects.append({'name':obj.name,'bounds':{'min':list(map(min,zip(*points))),'max':list(map(max,zip(*points)))},'materials':[m.name for m in mesh.materials]})
 if not mesh.uv_layers:continue
 uv=mesh.uv_layers[0].data
 for tri in mesh.loop_triangles:
  if not mesh.materials[tri.material_index].name.startswith('MI_Cab_Plastic'):continue
  a=[np.array(points[i]) for i in tri.vertices];centre=sum(a)/3
  normal=np.cross(a[1]-a[0],a[2]-a[0]);length=np.linalg.norm(normal)
  if length<1e-10 or normal[2]/length<.35:continue
  b=[np.array(uv[i].uv) for i in tri.loops]
  A=np.column_stack((a[1]-a[0],a[2]-a[0]));B=np.column_stack((b[1]-b[0],b[2]-b[0]))
  s=np.linalg.svd(B@np.linalg.pinv(A),compute_uv=False)
  rows.append({'object':obj.name,'centre':list(map(float,centre)),'anisotropy':float(s[0]/max(s[-1],1e-12)),'uv_per_m_min':float(s[-1]),'uv_per_m_max':float(s[0])})
result={'scope':'Actual exported LOD0 FBX, upward plastic triangles, UV0; bounds in reimported Blender world axes. Includes other plastic parts; filter positions before attributing to dash.','objects':objects,'upward_plastic_triangles':len(rows),'worst':sorted(rows,key=lambda r:r['anisotropy'],reverse=True)[:40],'triangles':rows}
(ROOT/'artifacts/cab-r1/export-uv-audit.json').write_text(json.dumps(result,indent=2))
print('EXPORT_UV_AUDIT',len(rows),'triangles; worst',result['worst'][:3])
