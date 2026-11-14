import re,pickle,json
from shapely.geometry import Polygon
from shapely import wkt
from shapely.ops import unary_union
from pyproj import Transformer
T=Transformer.from_crs(4326,2180,always_xy=True)
inv=pickle.load(open('inv.pkl','rb'))
aero=wkt.loads(inv['aero'])
roads={k:unary_union([wkt.loads(l) for i,l,h in v]) for k,v in inv['roads'].items()}
x=open('bdot/PL.PZGiK.335.2061/BDOT10k/PL.PZGiK.335.2061__OT_PTLZ_A.xml',encoding='utf-8-sig').read()
feats=[]
for m in re.finditer(r'<ot:OT_PTLZ_A .*?</ot:OT_PTLZ_A>',x,re.S):
    s=m.group(0)
    lid=re.search(r'<ot:lokalnyId>(.*?)<',s).group(1)
    rodz=re.search(r'<ot:rodzaj>(.*?)<',s).group(1)
    kat=re.search(r'<ot:kategoria>(.*?)<',s); kat=kat.group(1) if kat else None
    wer=re.search(r'<ot:wersja>(.*?)<',s).group(1)
    ext=re.search(r'<gml:exterior>.*?<gml:posList>(.*?)<',s,re.S).group(1).split()
    ints=[i.split() for i in re.findall(r'<gml:interior>.*?<gml:posList>(.*?)<',s,re.S)]
    f=lambda a:[(float(a[i]),float(a[i+1])) for i in range(0,len(a),2)]
    p=Polygon(f(ext),[f(i) for i in ints]).buffer(0)
    feats.append(dict(id=lid,rodzaj=rodz,kat=kat,wersja=wer,geom=p))
print(len(feats))
pickle.dump([{**f,'geom':f['geom'].wkt} for f in feats],open('ptlz.pkl','wb'))
sel=['Dywizjonu 303','Adama Mickiewicza','Jacka Kuronia','Konstantego Ciołkowskiego']
# study window
from shapely.geometry import box
w=T.transform(23.140,53.078); e=T.transform(23.215,53.118)
win=box(w[0],w[1],e[0],e[1])
for f in sorted(feats,key=lambda f:-f['geom'].area):
    p=f['geom']
    if not p.intersects(win): continue
    dd={k[:5]:round(p.distance(roads[k])) for k in sel}; da=round(p.distance(aero))
    if min(min(dd.values()),da)<=80 and p.area>2000:
        c=T.transform(p.centroid.x,p.centroid.y,direction='INVERSE')
        print(f['id'][:13],f['rodzaj'],f['kat'],round(p.area/1e4,2),dd,da,round(c[1],5),round(c[0],5))
for k in sel:
    b=roads[k].bounds; print(k,[round(v,5) for v in T.transform(b[0],b[1],direction='INVERSE')+T.transform(b[2],b[3],direction='INVERSE')], round(roads[k].length))
