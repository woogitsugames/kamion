import json
import math
from pathlib import Path

p=Path(__file__).resolve().parent
fit=json.loads((p/'photo-pose-fit.json').read_text())
s=min(fit['solutions'],key=lambda x:x['cost'])
e,n,z,h,pitch,roll,f,d=s['parameters']
h,pitch=map(math.radians,[h,pitch])
cams=json.loads((p/'cameras.json').read_text())
cams['cameras']=[c for c in cams['cameras'] if not c['id'].startswith('ec-')]
cams['cameras'] += [
    dict(id='ec-ref073128',type='persp',kind='driver_eye',seat='file',
         fov_deg=math.degrees(2*math.atan(1080/f)),pos=[e,n,z],
         look_at=[e+math.sin(h)*math.cos(pitch)*100,n+math.cos(h)*math.cos(pitch)*100,z+math.sin(pitch)*100],
         note='WORKING_VALUE photographic resection; no roll. Full photo height, central1920 of2340 render versus3840 photo. Rakoon CC BY3.0'),
    dict(id='ec-single-head',type='persp',kind='driver_eye',seat='file',fov_deg=35,
         pos=[580,-970,230],look_at=[624.25,-1083.96,252],note='Diagnostic only, WORKING_VALUE pose'),
    dict(id='ec-multi-head',type='persp',kind='driver_eye',seat='file',fov_deg=35,
         pos=[670,-1020,230],look_at=[718.26,-1133.29,252],note='Diagnostic only, WORKING_VALUE pose')]
(p/'cameras.json').write_text(json.dumps(cams,indent=2)+'\n',encoding='utf-8')
print('Additional cameras:',len(cams['cameras']))
