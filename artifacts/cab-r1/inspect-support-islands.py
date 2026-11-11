"""Inspect disconnected, position-welded support islands in exported CAB_Body meshes."""
import sys,json
from pathlib import Path
import bpy
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/blender/truck/exterior'))
import geom as G,body as B,materials as M
bpy.ops.wm.read_factory_settings(use_empty=True);G.STATE['coll']=bpy.context.scene.collection;M.build_library('white',clay=True);B.set_shape('modern',1.5);B.cab_shell();B.mirrors('classic',True)
bpy.context.view_layer.update()
supports=[]
from mathutils import Matrix
for side in (-1,1):
 base=Vector(B.CAB.side_pt(2.90,B.win_front(2.90)+.02,side,0.))
 xh,yh=side*1.5,base.y-.10
 for name,zb,zh in (('top',2.84,2.74),('bot',2.26,2.20)):
  p0=Vector(B.CAB.side_pt(zb,B.win_front(zb)+.012,side,-.012));p1=Vector((xh-side*.08,yh+.012,zh));d=p1-p0
  matrix=Matrix.Translation((p0+p1)/2)@d.to_track_quat('X','Z').to_matrix().to_4x4()
  supports.append((f'mirror_arm_{name}_{side}',matrix,Vector((d.length,.04,.07))))
for o in list(bpy.data.objects):bpy.data.objects.remove(o,do_unlink=True)
manifest=json.load(open(ROOT/'art-source/truck/exterior/export/truck_exterior_manifest.json'))['lods']['LOD0']
axis=lambda p:Vector((p[0],p[2],p[1]))
offset=axis(manifest['empties']['EYE_POINT']['position_unity_vehicle'])-B.EYE
unity=lambda p:[round(v,7) for v in (p.x,p.z,p.y)]
data=[]
for name,matrix,dim in supports:
 side=-1 if name.endswith('_-1') else 1
 base=Vector(B.CAB.side_pt(2.90,B.win_front(2.90)+.02,side,0.))
 rot=B.mirror_aim(Vector((side*1.5,base.y-.10,2.60)),(side*.06,-1.,-.02))
 data.append(dict(name=name,start=unity(matrix@Vector((-dim.x/2,0,0))+offset),end=unity(matrix@Vector((dim.x/2,0,0))+offset),right=unity(matrix.to_3x3()@Vector((0,1,0))),up=unity(matrix.to_3x3()@Vector((0,0,1))),shift=unity(rot@Vector((0,.08,0))),halfWidth=.020,halfHeight=.035))
(ROOT/'artifacts/cab-r1/cab_mirror_supports.json').write_text(json.dumps(dict(status='WORKING_VALUE: 80 mm rear attachment clearance; source box geometry, no third-party assets',supports=data),indent=2))
report={}
for lod in range(3):
 bpy.ops.import_scene.fbx(filepath=str(ROOT/f'art-source/truck/exterior/export/SM_TruckExterior_LOD{lod}.fbx'))
 objs=list(bpy.context.selected_objects);body=next((o for o in objs if o.name==f'CAB_Body_LOD{lod}'),None)
 if body is None:print([o.name for o in objs]);raise ValueError('body missing')
 vertices=[body.matrix_world@v.co for v in body.data.vertices]
 parents=list(range(len(vertices)))
 def find(i):
  while parents[i]!=i:parents[i]=parents[parents[i]];i=parents[i]
  return i
 def union(a,b):parents[find(a)]=find(b)
 welded={}
 for i,p in enumerate(vertices):
  key=tuple(round(x,4) for x in p)
  if key in welded:union(i,welded[key])
  else:welded[key]=i
 for face in body.data.polygons:
  for i in face.vertices[1:]:union(face.vertices[0],i)
 components={}
 for i in range(len(vertices)):components.setdefault(find(i),[]).append(i)
 rows=[]
 for name,matrix,dim in supports:
  inv=matrix.inverted();matches=[]
  for ids in components.values():
   points=[inv@vertices[i] for i in ids]
   if len(points)<4:continue
   if all(abs(p.x)<=dim.x*.5+.002 and abs(p.y)<=dim.y*.5+.002 and abs(p.z)<=dim.z*.5+.002 for p in points):
    matches.append({'vertices':len(ids),'min':list(map(min,zip(*points))),'max':list(map(max,zip(*points)))})
  rows.append({'name':name,'source_origin':list(matrix.translation),'dims':list(dim),'components':matches})
 report[str(lod)]=rows
 for o in objs:bpy.data.objects.remove(o,do_unlink=True)
print(json.dumps(report,indent=2));(ROOT/'artifacts/cab-r1/support-islands.json').write_text(json.dumps(report,indent=2))


