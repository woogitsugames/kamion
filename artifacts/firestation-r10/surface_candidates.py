"""Artifact-only source-field candidates. No production writes or runtime acceptance.
Run: uv run --project tools/worldgen python artifacts/firestation-r10/surface_candidates.py
"""
import hashlib,json,sys
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent/'surface-candidates';OUT.mkdir(exist_ok=True)
SRC=ROOT/'art-source/world/materials/_src/sets_fire_station.py';text=SRC.read_text();pin=hashlib.sha256(SRC.read_bytes()).hexdigest();sys.path.insert(0,str(SRC.parent))
import pbrkit as K
cases={
 'current':text,
 'glass_clinker':text.replace('"clinker_linear": [0.47, 0.29, 0.115]','"clinker_linear": [0.27, 0.135, 0.060]').replace('hall_glass = np.array([0.170, 0.180, 0.195]','hall_glass = np.array([0.102, 0.108, 0.117]').replace('if glass is not None:                      # big hall glazing','if glass is not None:\n            sky = (0.90 + 0.06 * np.clip(gv / max(gmax, 1e-3), 0, 1) ** 1.3)[..., None]\n            # big hall glazing'),
}
fields={};proof={'status':'ARTIFACT_ONLY_NO_RUNTIME_ACCEPTANCE','source_sha256':pin,'parameters':{'hall_glass_linear':[.102,.108,.117],'hall_only_gradient':[.90,.06,1.3],'clinker_linear':[.27,.135,.060]},'preserved':{}}
for name,code in cases.items():
 ns={'__file__':str(SRC),'__name__':'artifact_fire_station'};exec(compile(code,str(SRC),'exec'),ns)
 fields[name]=ns['fire_station'](1024)
 if name=='current':layout=ns['LAYOUT']
 rgb=np.uint8(np.clip(np.rint(K.srgb_encode(fields[name].albedo)*255),0,255));Image.fromarray(rgb).save(OUT/(name+'-source-albedo.png'))
X,Y=fields['current'].c.xy();v=14-Y
intended=np.zeros(X.shape,bool)
for key in ('brick','win_arch','win_round'):
 r=layout[key];intended|=(X>=r['u'][0]-.05)&(X<r['u'][1]+.05)&(v>=r['v'][0]-.05)&(v<r['v'][1]+.05)
a,b=fields.values()
assert np.array_equal(a.albedo[~intended],b.albedo[~intended]),'Unexpected protected albedo change'
for k in ('height','rough','metal','joint','elem_id'):
 assert np.array_equal(getattr(a,k),getattr(b,k)),k
 proof['preserved'][k]='ALL_FIELDS_EXACT'
proof['preserved']['albedo']='EXACT_OUTSIDE_BRICK_ARCH_ROUND_INCLUDING_ALL_CLEAN_PAINT_ROOF_TRIM_FLAG_AND_OFFICE_GLASS'
proof['changed_pixels']=int(np.any(a.albedo!=b.albedo,axis=2).sum())
sheet=Image.new('RGB',(960,600),'white');dr=ImageDraw.Draw(sheet)
for ci,name in enumerate(cases):
 im=Image.open(OUT/(name+'-source-albedo.png'))
 for ri,key in enumerate(('win_arch','win_round','brick')):
  r=layout[key];box=(round(r['u'][0]/14*1024),round((1-r['v'][1]/14)*1024),round(r['u'][1]/14*1024),round((1-r['v'][0]/14)*1024));crop=im.crop(box);crop.thumbnail((450,165));sheet.paste(crop,(ci*480+10,ri*190+25));dr.text((ci*480+10,ri*190+5),name+' / '+key+' / UNLIT SOURCE',fill='black')
sheet.save(OUT/'surface-source-compare.jpg',quality=95)
assert hashlib.sha256(SRC.read_bytes()).hexdigest()==pin
(OUT/'proof.json').write_text(json.dumps(proof,indent=2));print(json.dumps(proof,indent=2))
