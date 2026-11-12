from source_fields import ROOT,OUT,glb
import hashlib,json,numpy as np,sys
stage=sys.argv[1]if len(sys.argv)>1 else'lane-field'
a=json.loads((OUT/'native-before.json').read_text());b=json.loads((OUT/f'native-{stage}.json').read_text());baseline={(x['scene'],x['path']):x for x in a['meshes']};rows=[];cache={}
for row in b['meshes']:
 old=baseline[(row['scene'],row['path'])]
 for field in ('positions','normals','indices','uv0','vertices','submeshes'):assert row[field]==old[field],(row['path'],field)
 if not row['hasUv1']:continue
 name=row['path'].split('#')[1];parts=name.split('_');chunk='_'.join(parts[:2]);layer='_'.join(parts[2:])
 if chunk not in cache:cache[chunk]=glb(ROOT/f'Data/raw/derived/bialystok-industrial-c/world/chunk_{chunk}.glb')
 d,acc=cache[chunk];node=next(n for n in d['nodes']if n['name']==layer);ys=[]
 for p in d['meshes'][node['mesh']]['primitives']:
  attrs=p['attributes'];mat=d['materials'][p['material']]['name'];n=len(acc(attrs['POSITION']))
  if'TEXCOORD_1'in attrs:y=np.float32(1)-acc(attrs['TEXCOORD_1'])[:,1]
  else:y=np.full(n,5. if layer=='road'and mat in ('road_asphalt','road_asphalt_new')else 0.)
  ys.extend(y)
 expected=np.array(ys,dtype='<f2').astype('<f4');h=hashlib.sha256(expected.tobytes()).hexdigest();assert h==row['uv1y'],(row['path'],h,row['uv1y']);rows.append(dict(scene=row['scene'],path=row['path'],uv1y_sha256=h))
out=dict(stage=stage,geometry_normals_indices_uv0_identical_meshes=len(b['meshes']),uv1y_original_source_halfquantized_exact=len(rows),note='Native uploaded UV1.y compared against originalraw y unflipped1f-y then quantizedfloat16 then decodedfloat32. Only intended missing-asphalt sentinel supplies5, other missingchannels0. This proves paint age untouched; no visualPASS.',rows=rows)
(OUT/f'{stage}-native-age-proof.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items()if k!='rows'}))
