"""Source-only cab seat/armrest surface intersections. No export or source asset writes."""
import json,sys
from pathlib import Path
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import intersect_ray_tri
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/blender/truck/interior'))
import build_interior as BI
import a6_export as EX
saved=sys.argv;sys.argv=[saved[0],'--','--out','artifacts/cab-r1/seat-source','--no-backdrop'];args=BI.parse_args();sys.argv=saved
BI.build(args)
objects=[o for o in bpy.data.objects if o.type=='MESH' and not o.get('decal') and EX.group_of(o.name) not in ('CAB_ShellPlaceholder','CAB_Glass_Windows','CAB_Glass') and not EX.group_of(o.name).startswith('MIRROR_')]
BI.fit_to_exterior(objects);bpy.context.view_layer.update()
cache={}
def mesh(obj):
 if obj.name in cache:return cache[obj.name]
 ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();m.calc_loop_triangles()
 points=[obj.matrix_world@v.co for v in m.vertices];faces=[tuple(t.vertices) for t in m.loop_triangles];ev.to_mesh_clear()
 tree=BVHTree.FromPolygons(points,faces,all_triangles=True)
 result=(points,faces,tree);cache[obj.name]=result;return result

def intersections(a,b):
 pa,fa,ta=mesh(a);pb,fb,tb=mesh(b);candidates=ta.overlap(tb);hits=set()
 for ia,ib in candidates:
  aa=[pa[i] for i in fa[ia]];bb=[pb[i] for i in fb[ib]]
  for edge,triangle in ((aa,bb),(bb,aa)):
   for i in range(3):
    start,end=edge[i],edge[(i+1)%3];direction=end-start;length=direction.length
    if length<1e-9:continue
    direction/=length;hit=intersect_ray_tri(*triangle,direction,start,True)
    if hit is not None and -1e-6 <= (hit-start).dot(direction) <= length+1e-6:hits.add(tuple(round(x,6) for x in hit))
 return {'candidate_pairs':len(candidates),'intersection_points':len(hits),'points_ahead_of_hpoint':sum(p[1]>BI.HPT.y for p in hits),'bounds':None if not hits else {'min':list(map(min,zip(*hits))),'max':list(map(max,zip(*hits)))}}

seats={prefix:[o for o in objects if o.name.startswith(prefix+'_') and not any(token in o.name for token in ('armrest','arm_pivot','rail','base','gaiter','bellows','damper'))] for prefix in ('drv','pas')}
wheel=[o for o in objects if o.name.startswith(('wheel_rim','spoke_','wheel_hub','hub_gap'))]
report={'scope':'Source surfaces after fit_to_exterior. Exact edge/triangle intersections; no solid containment test, no claim about game FBX. 0.025 variant moves door armrests outward only. Rear hinge contact may be intentional.','states':{},'selectors':{'seats':{p:[o.name for o in ss] for p,ss in seats.items()},'wheel':[o.name for o in wheel],'arms':[o.name for o in objects if 'armrest' in o.name]}}
for shift in (0,.025):
 if shift:
  for prefix,side in (('drv',1),('pas',-1)):
   for obj in objects:
    if obj.name.startswith('door_armrest_'+str(-side)):obj.location.x-=side*shift
  bpy.context.view_layer.update();cache.clear()
 rows=[]
 for prefix in ('drv','pas'):
  side=-1 if prefix=='drv' else 1
  arms=[o for o in objects if o.name.startswith((prefix+'_armrest','door_armrest_'+str(side)))]
  for arm in arms:
   for seat in seats[prefix]:
    hit=intersections(arm,seat)
    if hit['candidate_pairs']:rows.append(dict(a=arm.name,b=seat.name,**hit))
 report['states'][str(shift)]={'armrest_pairs':rows}
 if not shift:
  rows=[]
  for w in wheel:
   for seat in seats['drv']:
    hit=intersections(w,seat)
    if hit['candidate_pairs']:rows.append(dict(a=w.name,b=seat.name,**hit))
  report['wheel_seat_pairs']=rows
(ROOT/'artifacts/cab-r1/seat-intersections.json').write_text(json.dumps(report,indent=2));print('SEAT_INTERSECTIONS_RESULT: OK')
