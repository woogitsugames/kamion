import json, numpy as np
from shapely.geometry import shape
t=json.load(open('Data/Regions/bialystok-dojlidy/terrain.json'))
a=np.fromfile(t['encoding']['file'],dtype='<u2').reshape(2049,2049)*t['encoding']['scale_m_per_unit']+t['encoding']['offset_m']
x0,y0,x1,y1=t['bbox']
fc=json.load(open('Data/Regions/bialystok-dojlidy/buildings.geojson'))
D=[]
for ft in fc['features']:
    p=ft['properties']
    if p.get('ground_z_evrf2007') is None: continue
    g=shape(ft['geometry']); pg=max(getattr(g,'geoms',[g]),key=lambda q:q.area)
    c=np.asarray(pg.exterior.coords)
    i=np.clip(np.round(c[:,0]-x0).astype(int),0,2048); j=np.clip(np.round(y1-c[:,1]).astype(int),0,2048)
    zs=a[j,i]
    D.append((np.median(zs)-p['ground_z_evrf2007'], zs.min()-p['ground_z_evrf2007'], p['height_m'], pg.area, p['id'], p['height_source']))
d=np.array([x[0] for x in D]); m=np.array([x[1] for x in D])
print(len(D),'of',len(fc['features']),'median-base: mean %.2f p5 %.2f p50 %.2f p95 %.2f min %.2f max %.2f'%(d.mean(),*np.percentile(d,[5,50,95]),d.min(),d.max()))
print('min-base: p5 %.2f p50 %.2f p95 %.2f'%tuple(np.percentile(m,[5,50,95])))
for x in sorted(D,key=lambda x:-abs(x[0]))[:12]: print([round(float(v),2) if not isinstance(v,str) else v[-30:] for v in x])
