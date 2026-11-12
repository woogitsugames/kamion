"""Named mirror-support obstruction from the design eye; source geometry, not GPU pixels."""
import os, sys, json, math
from pathlib import Path
import bpy
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/blender/truck/exterior'))
import body as B, geom as G, materials as M
bpy.ops.wm.read_factory_settings(use_empty=True)
G.STATE['coll']=bpy.context.scene.collection
M.build_library('white',clay=True)
B.set_shape('modern',1.5)
B.cab_shell()
if len(sys.argv[sys.argv.index('--')+1:]) > 1:
 import inspect
 offset=float(sys.argv[-1])
 source=inspect.getsource(B.mirrors).replace('p1 = V((xh - s * 0.08, yh + 0.012, zh))', 'p1 = V((xh - s * 0.08, yh + 0.012, zh)) + rot @ V((0, '+str(offset)+', 0))')
 exec(source,B.__dict__)
B.mirrors('classic',front=True)
bpy.context.view_layer.update()
dg=bpy.context.evaluated_depsgraph_get(); verts=[]; faces=[];owners=[]
for obj in bpy.data.objects:
 if obj.type!='MESH' or not obj.name.startswith('mirror_arm_'):continue
 ev=obj.evaluated_get(dg); mesh=ev.to_mesh();base=len(verts)
 verts.extend([obj.matrix_world@v.co for v in mesh.vertices])
 for p in mesh.polygons:faces.append([base+i for i in p.vertices]);owners.append(obj.name)
 ev.to_mesh_clear()
bvh=BVHTree.FromPolygons(verts,faces)
man=json.load(open(ROOT/'art-source/truck/exterior/export/truck_exterior_manifest.json'))['lods']['LOD0']
axis=lambda a:Vector((a[0],a[2],a[1]))
result={}
for info in man['objects'].values():
 role=info['role']
 if not role.startswith(('MIRROR_Main','MIRROR_Wide')):continue
 c=axis(info['pivot_unity_vehicle']);x=axis(info['axes_unity_vehicle']['X']);y=axis(info['axes_unity_vehicle']['Y']);n=axis(info['normal_unity_vehicle'])
 eye=axis(man['empties']['EYE_POINT']['position_unity_vehicle'])
 # Source Blender coordinates differ from export vehicle frame by front axle longitudinal offset.
 offset=B.EYE-eye;c+=offset;eye=B.EYE
 targets={'MIRROR_MainR':(17.,-2.),'MIRROR_WideL':(-29.,-10.),'MIRROR_WideR':(29.,-10.)}
 # Extract actual targets rather than assuming them.
 import re
 src=(ROOT/'game/Assets/_Project/Editor/Setup/TruckAssetBuilder.cs').read_text()
 targets={r:(float(a),float(b)) for r,a,b in re.findall(r'\{ "(MIRROR_[^"]+)", \(([-\d.]+)f, ([-\d.]+)f\)',src)}
 if role in targets:
  yaw,pitch=map(math.radians,targets[role]);want=Vector((math.sin(yaw)*math.cos(pitch),-math.cos(yaw)*math.cos(pitch),math.sin(pitch)))
  nn=(want-(c-eye).normalized()).normalized();turn=n.rotation_difference(nn);x=turn@x;y=turn@y
 hits={}
 for i in range(40):
  for j in range(60):
   p=c+x*info['size_m'][0]*((i+.5)/40-.5)+y*info['size_m'][1]*((j+.5)/60-.5);ray=p-eye
   hit=bvh.ray_cast(eye,ray.normalized(),ray.length-.002)
   if hit[0] is not None:
    name=owners[hit[2]];hits[name]=hits.get(name,0)+1
 result[role]={'samples':2400,'blocked':sum(hits.values()),'fraction':sum(hits.values())/2400,'by_object':hits}
print(json.dumps(result,indent=2))
out=Path(sys.argv[sys.argv.index('--')+1])
out.write_text(json.dumps(result,indent=2))


