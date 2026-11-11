"""Measure ACTUAL Editor-imported mip QA clones; native and max1024 size proxy.
No Android hardware/ASTC or temporal acceptance is implied.
"""
import json
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent/'actual-alpha-mips'
layout=json.loads((ROOT/'art-source/world/landmarks/fire_station_jrg2/atlas_layout.json').read_text())['alpha'];rows={}
for scale in ('native','max1024'):
 base=OUT/scale;imports={p:(base/p/'import.txt').read_text() for p in ('before','after')};result={'imports':imports,'mips':{}}
 for after in sorted((base/'after').glob('mip*.png')):
  before=base/'before'/after.name;a=np.array(Image.open(before));b=np.array(Image.open(after));assert a.shape==b.shape;h,w=a.shape[:2];record={}
  for name in ('fence_bay','gate_bay','lettering','number','conifer_bough'):
   r=layout[name];x0,x1=[int(x*w) for x in r['u']];y0,y1=h-int(r['v'][1]*h),h-int(r['v'][0]*h)
   aa=a[y0:y1,x0:x1];bb=b[y0:y1,x0:x1]
   if not aa.size:continue
   ac,bc=aa[:,:,3]>=128,bb[:,:,3]>=128
   record[name]={'size':[x1-x0,y1-y0],'alpha128_before':float(ac.mean()),'alpha128_after':float(bc.mean()),'changed_cutoff_pixels':int(np.count_nonzero(ac!=bc)),'changed_alpha_pixels':int(np.count_nonzero(aa[:,:,3]!=bb[:,:,3])),'max_abs_alpha_difference':int(np.abs(aa[:,:,3].astype(int)-bb[:,:,3]).max()),'all_RGBA_exact':bool(np.array_equal(aa,bb))}
  result['mips'][after.stem]=record
 rows[scale]=result
 # Per-region comparison, displayed at fixed size, thresholded so letter/fence coverage is legible.
 for region in ('lettering','fence_bay','conifer_bough'):
  sheet=Image.new('RGB',(960,660),'white');dr=ImageDraw.Draw(sheet);dr.text((8,5),scale+' '+region+' / actual imported Editor mips; cutoff128 / NOT phone-GPU/temporal proof',fill='black')
  for i,mip in enumerate(list(result['mips'])[:8]):
   r=layout[region]
   for j,phase in enumerate(('before','after')):
    im=Image.open(base/phase/(mip+'.png'));w,h=im.size;box=(int(r['u'][0]*w),h-int(r['v'][1]*h),int(r['u'][1]*w),h-int(r['v'][0]*h));crop=im.crop(box)
    if not crop.width or not crop.height:continue
    aa=np.array(crop)[:,:,3];color=np.where((aa>=128)[:,:,None],[40,55,40],[220,225,230]).astype('uint8');crop=Image.fromarray(color);crop.thumbnail((225,100));crop=crop.resize((225,100),Image.Resampling.NEAREST);x=(i%4)*240;y=35+(i//4)*300+j*130;sheet.paste(crop,(x,y));dr.text((x+4,y+102),mip+' '+phase,fill='black')
  sheet.save(base/(region+'-mip-coverage.jpg'),quality=95)
(OUT/'comparison.json').write_text(json.dumps({'status':'ACTUAL_EDITOR_MIPS; max1024 SIZE_PROXY; Editor-decoded Android-target ASTC_6x6; phone GPU/temporal UNVERIFIED','results':rows},indent=2));print(json.dumps(rows,indent=2))

