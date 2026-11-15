import json, math, sys
from pyproj import Transformer
R='/workspace/kamion/.claude/worktrees/agent-ab851075007c7ffbb/'
d=json.load(open(R+'docs/reports/map/dk65_route_plan.json'))['variants']['A_old_road']
pl=d['polyline']; ways=d['ways']
t=Transformer.from_crs('EPSG:2180','EPSG:4326',always_xy=True)
tiles={'dk65-01':(768779,595199),'dk65-02':(768779,597247),'dk65-03':(766731,597247),'dk65-04':(766731,599295),'dk65-05':(766731,601343),
'dk65-06':(766731,603391),'dk65-07':(764683,603391),'dk65-08':(764683,605439),'dk65-09':(762635,605439),'dk65-10':(762635,607487),'dk65-11':(762635,609535),
'knyszyn-s':(760587,609535),'knyszyn':(760587,611583),'knyszyn-w':(758539,611583),'(-3,0)knyszynska':(770827,595199)}
def tile(x,y):
  for k,(x0,y0) in tiles.items():
    if x0<=x<x0+2048 and y0<=y<y0+2048: return k
  return '?'
cum=[0]
for i in range(1,len(pl)): cum.append(cum[-1]+math.dist(pl[i-1],pl[i]))
print('len',cum[-1],file=sys.stderr)
out=[]
kms=[8.8]+list(range(9,29))+[16.7,24.6,21.65,11.5,12.5,13.5,14.5,15.5]
kms=sorted(k for k in kms if k<=28.4)
for km in kms:
  s=km*1000
  i=next(i for i in range(1,len(cum)) if cum[i]>=s)
  f=(s-cum[i-1])/(cum[i]-cum[i-1]); x=pl[i-1][0]+f*(pl[i][0]-pl[i-1][0]); y=pl[i-1][1]+f*(pl[i][1]-pl[i-1][1])
  dx=pl[i][0]-pl[i-1][0]; dy=pl[i][1]-pl[i-1][1]; brg=(math.degrees(math.atan2(dx,dy)))%360
  lon,lat=t.transform(x,y)
  w=next((w for w in ways if w['km_start']<=km<=w['km_end']+1e-6),None)
  out.append(dict(km=km,x=round(x,1),y=round(y,1),lat=round(lat,6),lon=round(lon,6),bearing_grid=round(brg,1),tile=tile(x,y),
    way=w['way_id'] if w else None,highway=w and w['highway'],ref=w and w['ref'],name=w and w['name'],lanes=w and w['lanes'],maxspeed=w and w['maxspeed'],bridge=w and w['bridge']))
json.dump(out,open(sys.argv[1],'w'),ensure_ascii=False,indent=1)
for o in out: print(o)
tb={}
for k,(x0,y0) in tiles.items():
  a=t.transform(x0,y0); b=t.transform(x0+2048,y0+2048); tb[k]=[round(a[0],5),round(a[1],5),round(b[0],5),round(b[1],5)]
json.dump(tb,open(sys.argv[2],'w'),indent=1); print(tb)
