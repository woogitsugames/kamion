"""Metric UV audit of visible soft dashboard; source generation only."""
import json,sys
from pathlib import Path
import bpy,numpy as np
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/blender/truck/interior'))
import build_interior as BI
import a6_export as EX
saved=sys.argv;sys.argv=[saved[0],'--','--out','artifacts/cab-r1/uv-source','--no-backdrop'];args=BI.parse_args();sys.argv=saved
BI.build(args)
objects=[o for o in bpy.data.objects if o.type=='MESH' and not o.get('decal') and EX.group_of(o.name) not in ('CAB_ShellPlaceholder','CAB_Glass_Windows','CAB_Glass') and not EX.group_of(o.name).startswith('MIRROR_')]
BI.fit_to_exterior(objects);bpy.context.view_layer.update()
obj=bpy.data.objects['dash_main'];m=obj.data;uv=m.uv_layers['UVMap'].data;rows=[];degenerate=0
for p in m.polygons:
 if p.material_index!=0 or p.normal.z<.35:continue
 loops=list(p.loop_indices)
 for j in range(1,len(loops)-1):
  ids=[loops[0],loops[j],loops[j+1]]
  a=[np.array(obj.matrix_world@m.vertices[m.loops[i].vertex_index].co) for i in ids]
  b=[np.array(uv[i].uv) for i in ids]
  A=np.column_stack((a[1]-a[0],a[2]-a[0]));B=np.column_stack((b[1]-b[0],b[2]-b[0]))
  if np.linalg.norm(np.cross(A[:,0],A[:,1]))<1e-10:continue
  s=np.linalg.svd(B@np.linalg.pinv(A),compute_uv=False)
  if s[-1]<1e-8:degenerate+=1;continue
  rows.append({'anisotropy':float(s[0]/s[-1]),'uv_per_m_min':float(s[-1]),'uv_per_m_max':float(s[0]),'centre':list(map(float,sum(a)/3))})
values=np.array([r['anisotropy'] for r in rows]);dens=np.array([(r['uv_per_m_min']*r['uv_per_m_max'])**.5 for r in rows])
result={'scope':'Source UVMap in metres after fit; visible upward soft-dashboard triangles only, no AO atlas or game-FBX claim.','triangles':len(rows),'degenerate_uv_triangles':degenerate,'anisotropy_p50_p95_max':list(map(float,np.percentile(values,[50,95,100]))),'uv_per_m_p05_p50_p95':list(map(float,np.percentile(dens,[5,50,95]))),'worst':sorted(rows,key=lambda r:r['anisotropy'],reverse=True)[:12]}
(ROOT/'artifacts/cab-r1/dash-uv-audit.json').write_text(json.dumps(result,indent=2));print('DASH_UV_AUDIT',json.dumps(result))
