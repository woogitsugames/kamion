import re,json,pickle,math
from shapely.geometry import Polygon,Point
from shapely.strtree import STRtree
from shapely import wkt
from pyproj import Transformer
T=Transformer.from_crs(4326,2180,always_xy=True)
def load(fn):
    x=open(fn,encoding='utf-8-sig').read(); out=[]
    for m in re.finditer(r'<ot:OT_PTLZ_A .*?</ot:OT_PTLZ_A>',x,re.S):
        s=m.group(0)
        lid=re.search(r'<ot:lokalnyId>(.*?)<',s).group(1); rodz=re.search(r'<ot:rodzaj>(.*?)<',s).group(1)
        kat=re.search(r'<ot:kategoria>(.*?)<',s); kat=kat.group(1) if kat else None
        ext=re.search(r'<gml:exterior>.*?<gml:posList>(.*?)<',s,re.S).group(1).split()
        f=lambda a:[(float(a[i]),float(a[i+1])) for i in range(0,len(a),2)]
        out.append((lid,rodz,kat,Polygon(f(ext)).buffer(0)))
    return out
P=load('bdot/PL.PZGiK.335.2061/BDOT10k/PL.PZGiK.335.2061__OT_PTLZ_A.xml')+load('bdot/PL.PZGiK.335.2002/BDOT10k/PL.PZGiK.335.2002__OT_PTLZ_A.xml')
P=[p for p in P if p[1] in('las','zagajnik')]
tree=STRtree([p[3] for p in P])
def near(lat,lon):
    pt=Point(*T.transform(lon,lat)); i=tree.nearest(pt); p=P[i]
    return dict(ptlz_id=p[0],ptlz=p[1]+'/'+str(p[2]),ptlz_ha=round(p[3].area/1e4,2),d_m=round(pt.distance(p[3]),1))
out={}
for r in json.load(open('pano_pick.json')): out['PX%02d'%r['n']]=near(r['lat'],r['lon'])
for r in json.load(open('commons_want.json')):
    if r.get('lat') is not None: out['C'+str(r['pageid'])]=near(r['lat'],r['lon'])
json.dump(out,open('frame_geo.json','w'),indent=0)
for k,v in out.items(): print(k,v)
