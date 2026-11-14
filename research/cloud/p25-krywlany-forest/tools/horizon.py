import pickle,json,math
import numpy as np
from shapely import wkt
from shapely.geometry import Point,LineString
from shapely.ops import unary_union,nearest_points
from pyproj import Transformer
T=Transformer.from_crs(4326,2180,always_xy=True)
inv=pickle.load(open('inv.pkl','rb'))
pt=[(f,wkt.loads(f['geom'])) for f in pickle.load(open('ptlz.pkl','rb'))]
big=unary_union([g for f,g in pt if f['rodzaj']=='las' and g.area>=10000])
sel={'D303':'Dywizjonu 303','KUR':'Jacka Kuronia','MICK':'Adama Mickiewicza','CIOL':'Konstantego Ciołkowskiego'}
out={}
for k,v in sel.items():
    ds=[];bs=[]
    for i,l,h in inv['roads'][v]:
        l=wkt.loads(l)
        for s in np.arange(0,l.length,20):
            p=l.interpolate(s); q=nearest_points(p,big)[1]
            d=p.distance(q); ds.append(d); bs.append(math.degrees(math.atan2(q.x-p.x,q.y-p.y))%360)
    ds=np.array(ds); bs=np.array(bs)
    sect=['N','NE','E','SE','S','SW','W','NW']
    import collections
    c=collections.Counter(sect[int(((b+22.5)%360)//45)] for b in bs)
    out[k]=dict(n=len(ds),d_p10=round(float(np.percentile(ds,10))),d_p50=round(float(np.percentile(ds,50))),d_p90=round(float(np.percentile(ds,90))),d_max=round(float(ds.max())),udzial_le30m=round(float((ds<=30).mean()),2),udzial_gt200m=round(float((ds>200).mean()),2),kierunek_najblizszego_lasu=dict(c.most_common(4)))
    print(k,out[k])
json.dump(out,open('horizon_dist.json','w'),ensure_ascii=False,indent=1)
