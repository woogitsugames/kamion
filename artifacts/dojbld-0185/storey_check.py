import sys, json, yaml, numpy as np
sys.path.insert(0,'tools/worldgen')
from streetscape import buildings_mesh as BM
ov=yaml.safe_load(open('Data/Regions/bialystok-dojlidy/overrides.yaml',encoding='utf8'))['overrides']
fc=json.load(open('Data/Regions/bialystok-dojlidy/buildings.geojson'))
t=json.load(open('Data/Regions/bialystok-dojlidy/terrain.json'))
a=np.fromfile(t['encoding']['file'],dtype='<u2').reshape(2049,2049)*t['encoding']['scale_m_per_unit']+t['encoding']['offset_m']
x0,y0,x1,y1=t['bbox']; ox,oy=780043,590079
bl=BM.load(fc,(ox,oy),ov)
ch=[];clamped=0;n=0
for b in bl:
    if b['typ']=='roof': continue
    c=np.asarray(b['poly'].exterior.coords)
    i=np.clip(np.round(ox+c[:,0]-x0).astype(int),0,2048); j=np.clip(np.round(y1-(oy+c[:,1])).astype(int),0,2048)
    zref=float(np.median(a[j,i]))
    h0=float(b['props'].get('height_m') or 6.0); h1=BM.roof_height(b,zref)
    if abs(h1-h0)>1e-9: n+=1
    if h1<=BM.LOD1_DATUM_MIN*h0+1e-6 or h1==2.5: clamped+=1
    s0=BM.storey_plan(b['typ'],h0,b['props'])[0]; s1=BM.storey_plan(b['typ'],h1,b['props'])[0]
    if s0!=s1: ch.append((b['id'][-14:],b['typ'],b['props'].get('storeys'),round(h0,2),round(h1,2),s0,s1))
print('buildings',len(bl),'height changed',n,'clamped',clamped,'storeys changed',len(ch))
for r in ch: print(r)
m0=m1=tot=0
for b in bl:
    if b['typ']=='roof' or not b['props'].get('storeys'): continue
    c=np.asarray(b['poly'].exterior.coords)
    i=np.clip(np.round(ox+c[:,0]-x0).astype(int),0,2048); j=np.clip(np.round(y1-(oy+c[:,1])).astype(int),0,2048)
    zref=float(np.median(a[j,i])); h0=float(b['props'].get('height_m') or 6.0); h1=BM.roof_height(b,zref)
    if b['typ'] not in('house','office','block'): continue
    tot+=1; nb=int(b['props']['storeys'])
    m0+=BM.storey_plan(b['typ'],h0,b['props'])[0]==nb; m1+=BM.storey_plan(b['typ'],h1,b['props'])[0]==nb
print('house/office/block with BDOT storeys',tot,'generator == BDOT: before',m0,'after',m1)
