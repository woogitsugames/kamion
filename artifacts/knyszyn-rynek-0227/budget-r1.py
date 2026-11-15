import re
from pathlib import Path

def read(p):
 d={}; last=None
 for line in p.read_text(encoding='utf8').splitlines():
  m=re.match(r'^([^:]+): .*?drawsEst=(\d+).*?trisExact=(\d+)',line)
  if m: last=m.group(1); d[last]=[int(m.group(2)),int(m.group(3)),0]
  else:
   m=re.match(r'^  (.+?) instanced .*?trianglesExact (\d+)',line)
   if m and m.group(1) in d: d[m.group(1)][2]=int(m.group(2))
 return d
root=Path('artifacts/knyszyn-rynek-0227')
for tier in ('Low-clear','High-clear','Low-dusk','High-dusk'):
 a=read(root/'before'/tier/'stats.txt');b=read(root/'r1'/tier/'stats.txt');same=a.keys()&b.keys()
 print(tier, 'common',len(same),'new',len(b.keys()-a.keys()))
 for i,label in ((0,'drawsEst'),(1,'tris_mesh'),(2,'tris_instanced')):
  x=max(same,key=lambda k:b[k][i]-a[k][i]); print(label,'max before',max((v[i],k) for k,v in a.items()),'after',max((v[i],k) for k,v in b.items()),'max increase',x,b[x][i]-a[x][i])
 for k in ('rynek-owner-03','rynek-owner-04','rynek-owner-05','rynek-owner-06','rynek-owner-07','rynek-owner-08'):
  if k in b: print(k,b[k])
