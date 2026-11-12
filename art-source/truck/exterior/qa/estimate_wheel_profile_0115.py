"""Read-only meridian selection estimate using the actual production DP function."""
import ast,math,json
from pathlib import Path
r=Path(__file__).resolve().parents[4]
c=ast.parse((r/'tools/blender/truck/exterior/chassis.py').read_text(encoding='utf-8-sig'))
a=ast.parse((r/'tools/blender/truck/exterior/a6_export.py').read_text(encoding='utf-8-sig'))
dims=json.loads((r/'art-source/truck/dims.json').read_text(encoding='utf8'))
g={'math':math,'TYRE_R':dims['values']['tyre_diameter_m']['value']/2}
f=next(n for n in c.body if isinstance(n,ast.FunctionDef) and n.name=='tyre_profile')
exec(compile(ast.Module(body=[f],type_ignores=[]),'<canonical tyre_profile>','exec'),g)
assign={n.targets[0].id:ast.literal_eval(n.value) for n in c.body if isinstance(n,ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0],ast.Name) and n.targets[0].id in ('RIM_PROF','RIM_INNER')}
reduce=next(n for n in a.body if isinstance(n,ast.FunctionDef) and n.name=='reduce_round'); dp=next(n for n in reduce.body if isinstance(n,ast.FunctionDef) and n.name=='dp')
rows=[]
for label,profile in [('rim',assign['RIM_PROF']+assign['RIM_INNER'][::-1]),('tyre',g['tyre_profile']()[0])]:
 for tol in (.004,.006,.008,.010,.012,.015,.02,.03):
  env={'math':math,'pts':profile,'tol':tol,'keep':set()};exec(compile(ast.Module(body=[dp],type_ignores=[]),'<canonical reduce_round.dp>','exec'),env);env['dp'](0,len(profile)-1)
  k=sorted(env['keep']);rows.append({'piece':label,'tolerance_m':tol,'retained_profile_indices':k,'profile_faces':len(k)-1,'unculled_tris_20_columns':40*(len(k)-1),'unculled_tris_40_columns':80*(len(k)-1)})
out=r/'artifacts/truck-r4/wheel-profile-estimates.json';out.write_text(json.dumps({'note':'WORKING_VALUE estimates on regular unculled grid. Uses actual canonical meridian and DP source. Not Blender geometry, FBX, triangle budget or visual acceptance; UV/culling guards may retain extra cells.','rows':rows},indent=2),encoding='utf8')
for row in rows: print(row['piece'],row['tolerance_m'],row['profile_faces'],row['unculled_tris_20_columns'],row['unculled_tris_40_columns'])
