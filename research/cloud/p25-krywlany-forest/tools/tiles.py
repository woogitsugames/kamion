import pickle,json,math
from shapely import wkt
from shapely.geometry import box
from shapely.ops import unary_union,linemerge
from pyproj import Transformer
T=Transformer.from_crs(4326,2180,always_xy=True)
inv=pickle.load(open('inv.pkl','rb')); aero=wkt.loads(inv['aero'])
pt=pickle.load(open('ptlz.pkl','rb'))
w=T.transform(23.135,53.075); e=T.transform(23.225,53.122); win=box(w[0],w[1],e[0],e[1])
F=unary_union([wkt.loads(f['geom']) for f in pt if wkt.loads(f['geom']).intersects(win)])
pickle.dump(F.wkt,open('F.pkl','wb'))
sel={'D303':'Dywizjonu 303','MICK':'Adama Mickiewicza','KUR':'Jacka Kuronia','CIOL':'Konstantego Ciołkowskiego'}
lines={k:unary_union([wkt.loads(l) for i,l,h in inv['roads'][v]]) for k,v in sel.items()}
lines['AERO']=aero.exterior
need=[]
for k,l in lines.items():
    z=l.buffer(100).intersection(F.buffer(100)) if k!='D303' else l.buffer(110)
    need.append(z)
    print(k,round(l.length),round(z.area/1e4,1))
Z=unary_union(need)
S=250;tiles=[]
x0,y0,x1,y1=Z.bounds
for i in range(int(x0//S),int(x1//S)+1):
    for j in range(int(y0//S),int(y1//S)+1):
        if box(i*S,j*S,(i+1)*S,(j+1)*S).intersects(Z): tiles.append((i*S,j*S))
print(len(tiles),Z.bounds)
json.dump(tiles,open('tiles.json','w'))
