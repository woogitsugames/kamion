from pathlib import Path
import json,re,runpy,sys,hashlib
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path.cwd();ART=ROOT/'artifacts/car-paint-r1';OUT=ART/'r4-plate-review';OUT.mkdir(exist_ok=True)
conditions=['Low-clear','Low-overcast','High-clear','High-overcast']
ids=['r10_front_04','r10_rear_04','g_dirt_level_0','g_dirt_level_1','g_dirt_level_2','g_dirt_level_3','r4_rear_target_3']
fields=['cameraParents','vehicleHierarchy','regionRoots','view','projection','pixelRect','targetWidth','targetHeight','pixelWidth','pixelHeight','fov','aspect','near','far','pipelineScale','upscalingFilter','fsrSharpness','fsrOverride','post','glassFast','giRect','regionState']
def oldroot(condition,camera):return ART/('r4-rear-controls-v2' if camera=='r4_rear_target_3' else 'r4-focus-r1')/condition/('level3' if camera=='r4_rear_target_3' else '')
def mat(d):return np.array([[d[f'e{i}{j}'] for j in range(4)] for i in range(4)])
sys.argv=['native','plate-focus'];native=runpy.run_path(str(ART/'r4-native-uv-audit.py'))
manifest=json.loads((ROOT/'Data/Regions/bialystok-industrial-c/generated/world_manifest.json').read_text())
cars=[i for c in manifest['chunks'] for i in json.loads((ROOT/c['instances']['file']).read_text())['instances'] if i['p'].startswith(('car_','van_'))]
rows=[]
for cond in conditions:
 pairs=[]
 for camera in ids:
  current=ART/'r4-plate-focus'/cond;old=oldroot(cond,camera)
  b=json.loads((old/'poses'/f'{camera}-begin.json').read_text());a=json.loads((current/'poses'/f'{camera}-begin.json').read_text());end=json.loads((current/'poses'/f'{camera}-end.json').read_text())
  dif=[f for f in fields if a[f]!=b[f]];within=[f for f in fields if a[f]!=end[f]]
  assert not dif and not within,(camera,cond,dif,within)
  assert len(a['plateMaterials'])==1
  p=a['plateMaterials'][0];assert p['localCorners'] and p['version']==1 and p['shader']=='Kamion/World Car Plate'
  before=np.asarray(Image.open(old/f'{camera}.png').convert('RGB'));after=np.asarray(Image.open(current/f'{camera}.png').convert('RGB'));assert before.shape==after.shape
  h,w=before.shape[:2];vp=mat(a['projection'])@mat(a['view']);region=mat(a['regionRoots'][0]['localToWorld']);cam=np.array(list(a['cameraParents'][0]['worldPosition'].values()))
  rois=[];excluded=np.zeros((h,w),bool)
  for c in cars:
   co=np.cos(c['yaw']);si=np.sin(c['yaw']);world=region@np.array([[co,0,-si,c['e']],[0,1,0,c['z']],[si,0,co,c['n']],[0,0,0,1]])
   if np.linalg.norm(world[:3,3]-cam)>35:continue
   for prim in native['native_geometry'][(c['p'],0)]:
    if prim['material']!='M_car_plate':continue
    for face in range(2):
     v=prim['position'][face*2:face*2+2].reshape(-1,3);xyz=(world@np.column_stack([v,np.ones(len(v))]).T).T
     normal=world[:3,:3]@prim['normal'][face*2].mean(0)
     if np.dot(normal,cam-xyz[:,:3].mean(0))<=0:continue
     clip=(vp@xyz.T).T
     if np.any(clip[:,3]<=0):continue
     ndc=clip[:,:2]/clip[:,3,None];pixel=np.column_stack([(ndc[:,0]+1)*w/2,(1-ndc[:,1])*h/2])
     lo=np.floor(pixel.min(0)-3).astype(int);hi=np.ceil(pixel.max(0)+3).astype(int)
     x0,y0=np.maximum(lo,[0,0]);x1,y1=np.minimum(hi,[w,h])
     if x1-x0<5 or y1-y0<3:continue
     excluded[y0:y1,x0:x1]=True
     rois.append(dict(prototype=c['p'],e=c['e'],n=c['n'],face=face,box=[int(x0),int(y0),int(x1),int(y1)],distance=float(np.linalg.norm(xyz[:,:3].mean(0)-cam))))
  delta=np.abs(after.astype(np.int16)-before.astype(np.int16));outside=delta[~excluded]
  row=dict(condition=cond,camera=camera,reference='P0 same-frame forced3 (not historical R3)' if camera=='r4_rear_target_3' else 'P0 focus same production grime',pose_diff=dif,within_frame_diff=within,plate_binding=p,plate_projected_rois=sorted(rois,key=lambda r:r['distance']),nonplate_mae=float(outside.mean()),nonplate_changed_gt2_fraction=float(np.mean(np.max(outside,axis=1)>2)),excluded_fraction=float(excluded.mean()))
  rows.append(row)
  # Preserve aspect and show full pair; no image alignment or synthetic before.
  panel=Image.new('RGB',(960,246),(18,18,18));d=ImageDraw.Draw(panel);d.text((5,3),f'{cond} {camera} | P0 / P2',fill='white')
  for j,array in enumerate([before,after]):
   im=Image.fromarray(array);im.thumbnail((480,222));panel.paste(im,(480*j,24))
  pairs.append(panel)
  selected=sorted(rois,key=lambda r:r['distance'])[:3]
  if selected:
   crop=Image.new('RGB',(960,70+160*len(selected)),(20,20,20));draw=ImageDraw.Draw(crop);draw.text((5,3),f'{cond} {camera} P0/P2 projected plate ROIs (occlusion visually checked)',fill='white')
   for k,roi in enumerate(selected):
    x0,y0,x1,y1=roi['box'];draw.text((5,28+160*k),f"{roi['prototype']} E{roi['e']} N{roi['n']}",fill='white')
    for j,array in enumerate([before,after]):
     im=Image.fromarray(array).crop((x0,y0,x1,y1));im.thumbnail((470,120));scale=min(470/im.width,120/im.height,4)
     im=im.resize((int(im.width*scale),int(im.height*scale)),Image.Resampling.NEAREST);crop.paste(im,(j*480,50+160*k))
   crop.save(OUT/f'{cond}-{camera}-plate-crops.jpg',quality=94)
 for page in range(0,len(pairs),3):
  sheet=Image.new('RGB',(960,246*len(pairs[page:page+3])),(0,0,0))
  for j,panel in enumerate(pairs[page:page+3]):sheet.paste(panel,(0,j*246))
  sheet.save(OUT/f'{cond}-pairs{page//3+1:02}.jpg',quality=93)
out=dict(frames=28,matched_p0_frames=28,poses_exact=True,method='Independent parsed begin/end packets; conservative native LOD0 plate projection mask, no GPU object-ID/occlusion mask. Nonplate residual includes any unmasked projection/filter edge.',rows=rows)
(ART/'r4-plate-focus-validation.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(dict(frames=28,pose_exact=True,max_nonplate_mae=max(r['nonplate_mae'] for r in rows),max_changed_gt2_fraction=max(r['nonplate_changed_gt2_fraction'] for r in rows))))
