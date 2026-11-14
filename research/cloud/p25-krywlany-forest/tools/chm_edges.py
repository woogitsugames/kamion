# Profile poprzeczne CHM (NMPT-NMT) od osi drogi / ogrodzenia lotniska w głąb lasu.
# Wejście: inv.pkl (OSM), ptlz.pkl (BDOT10k PTLZ), bdl_items.json (BDL), sheets/ (NMPT 2023-09-15 0,5 m), dem/ (NMT 1 m, NMPT 2025-04-18 1 m)
import pickle,json,math,csv,sys,collections
import numpy as np, shapely
from shapely import wkt
from shapely.geometry import Point,LineString,shape,box
from shapely.ops import unary_union,linemerge
from shapely.strtree import STRtree
from pyproj import Transformer
from chm_lib import CHM
T=Transformer.from_crs(4326,2180,always_xy=True)
inv=pickle.load(open('inv.pkl','rb')); aero=wkt.loads(inv['aero'])
F=wkt.loads(pickle.load(open('F.pkl','rb'))); shapely.prepare(F)
pt=[(f,wkt.loads(f['geom'])) for f in pickle.load(open('ptlz.pkl','rb'))]
pt_tree=STRtree([g for f,g in pt])
bdl=[(f['properties'],shapely.transform(shape(f['geometry']),lambda a:np.column_stack(T.transform(a[:,0],a[:,1]))).buffer(0)) for f in json.load(open('bdl_items.json'))['features']]
bdl_tree=STRtree([g for p,g in bdl])
from esri import esri_poly
nlp=[(f['attributes'],esri_poly(f['geometry'])) for f in json.load(open('bdl_nlp_items.json')) if f.get('geometry')]
nlp_tree=STRtree([g for a,g in nlp])
osmf=[(t,i,wkt.loads(g),tg) for t,i,g,tg in inv['forests']]; osm_tree=STRtree([g for t,i,g,tg in osmf])
chm=CHM()
STEP=10.0; DMAX=100.0; DS=0.5
dist=np.arange(0,DMAX+DS,DS)
sel={'D303':'Dywizjonu 303','MICK':'Adama Mickiewicza','KUR':'Jacka Kuronia','CIOL':'Konstantego Ciołkowskiego'}
def label(P):
    r={'bdl':'','ptlz':'','ptlz_kat':'','osm':''}
    for i in bdl_tree.query(P,predicate='intersects'): r['bdl']=bdl[i][0]['adr_for']; break
    if not r['bdl']:
        for i in nlp_tree.query(P,predicate='intersects'): r['bdl']=nlp[i][0]['adress_forest']; break
    if not r['bdl']:
        best=(40.0,None)
        for i in bdl_tree.query(P.buffer(40)):
            d=bdl[i][1].distance(P)
            if d<best[0]: best=(d,'~'+bdl[i][0]['adr_for'])
        for i in nlp_tree.query(P.buffer(40)):
            d=nlp[i][1].distance(P)
            if d<best[0]: best=(d,'~'+nlp[i][0]['adress_forest'])
        if best[1]: r['bdl']=best[1]
    for i in pt_tree.query(P,predicate='intersects'): r['ptlz']=pt[i][0]['id']; r['ptlz_kat']=pt[i][0]['rodzaj']+'/'+str(pt[i][0]['kat']); break
    best=None
    for i in osm_tree.query(P,predicate='intersects'):
        if best is None or osmf[i][2].area<best[2].area: best=osmf[i]
    if best: r['osm']=f"{best[0]}/{best[1]}"
    return r
def side_name(b):
    return ['N','NE','E','SE','S','SW','W','NW'][int(((b+22.5)%360)//45)]
stations=[]
def run(name,line,wayid,other,normals=(1,-1),dmin=3.0):
    L=line.length; n=int(L//STEP)
    for k in range(n+1):
        s=k*STEP; p=line.interpolate(s); q=line.interpolate(min(L,s+1.0)) if s+1.0<=L else line.interpolate(s-1.0)
        dx,dy=(q.x-p.x,q.y-p.y) if s+1.0<=L else (p.x-q.x,p.y-q.y)
        l=math.hypot(dx,dy)
        if l==0: continue
        tx,ty=dx/l,dy/l
        for sg in normals:
            nx,ny=sg*ty,-sg*tx   # sg=+1: prawa strona wzgl. kierunku digitalizacji
            E=p.x+nx*dist; N=p.y+ny*dist
            h=chm.on(E,N)
            if np.isnan(h).mean()>0.2: continue
            h=np.nan_to_num(h,nan=0.0); h=np.clip(h,0,60)
            # inna nitka tej samej drogi w odległości < 40 m po tej stronie -> pomiń (pas rozdziału)
            if other is not None and LineString([(p.x+nx*2,p.y+ny*2),(p.x+nx*40,p.y+ny*40)]).intersects(other): continue
            # ściana lasu: pierwszy d>=dmin, gdzie mediana h w [d,d+15] >= 10 m i h(d)>=5
            w=int(15/DS); dw=None
            for i in range(int(dmin/DS),len(dist)-w):
                if h[i]>=5 and np.median(h[i:i+w])>=10: dw=i; break
            if dw is None: continue
            d_wall=dist[dw]
            if d_wall>80: continue
            Pin=Point(p.x+nx*(d_wall+10),p.y+ny*(d_wall+10))
            if not F.contains(Pin): continue
            lab=label(Pin)
            # płaszcz: ciągła roślinność >=1 m bezpośrednio przed ścianą (przerwy <=1 m)
            j=dw; last=dw; gap=0
            while j>int(dmin/DS):
                if h[j-1]>=1.0: gap=0; last=j-1
                else:
                    gap+=1
                    if gap>int(1/DS): break
                j-=1
            j=last
            mant=h[j:dw]; m_w=(dw-j)*DS
            i30=h[dw:dw+int(30/DS)]; i5=h[dw:dw+int(5/DS)]
            p90=np.percentile(i30,90)
            rise=next((x for x in range(dw,len(h)) if h[x]>=0.8*p90),dw); rise_w=(rise-dw)*DS
            hoff=np.nan_to_num(chm.off(E,N),nan=np.nan)
            o30=hoff[dw:dw+int(30/DS)]
            bn=(math.degrees(math.atan2(nx,ny)))%360
            la_lo=T.transform(p.x,p.y,direction='INVERSE')
            stations.append(dict(obiekt=name,way=wayid,s_m=round(s),lat=round(la_lo[1],6),lon=round(la_lo[0],6),strona=side_name(bn),azymut_normalnej=round(bn),d_sciany_m=d_wall,
                plaszcz_szer_m=m_w,plaszcz_h50=float(np.median(mant)) if len(mant) else 0.0,plaszcz_h90=float(np.percentile(mant,90)) if len(mant) else 0.0,
                h30_p50=float(np.percentile(i30,50)),h30_p90=float(p90),h30_max=float(i30.max()),h5_p50=float(np.percentile(i5,50)),h5_p90=float(np.percentile(i5,90)),
                narastanie_m=rise_w,h30off_p50=float(np.nanpercentile(o30,50)) if np.isfinite(o30).any() else '',h30off_p90=float(np.nanpercentile(o30,90)) if np.isfinite(o30).any() else '',
                prof=([float('nan')]*max(0,int(20/DS)-dw)+h[max(0,dw-int(20/DS)):dw+int(40/DS)].tolist()), raw30=i30.tolist(), raw5=i5.tolist(), **lab))
for key,nm in sel.items():
    ways=[(i,wkt.loads(l)) for i,l,h in inv['roads'][nm]]
    allu=unary_union([l for i,l in ways])
    for i,l in ways:
        other=unary_union([m for j,m in ways if j!=i and not m.touches(l)] or [LineString()])
        other=None if other.is_empty else other
        run(key,l,i,other)
    print(key,len(stations),flush=True)
# ogrodzenie/granica lotniska: normalna na zewnątrz
ext=aero.exterior
sg=1 if not aero.contains(Point(ext.interpolate(5).x + (ext.interpolate(6).y-ext.interpolate(5).y)*3, ext.interpolate(5).y-(ext.interpolate(6).x-ext.interpolate(5).x)*3)) else -1
run('AERO',LineString(ext.coords),'aerodrome',None,normals=(sg,),dmin=0.0)
print('AERO',len(stations))
pickle.dump(stations,open('stations.pkl','wb'))
