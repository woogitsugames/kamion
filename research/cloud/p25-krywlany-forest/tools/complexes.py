import pickle,json,collections,csv
import numpy as np, shapely
from shapely import wkt
from shapely.geometry import shape
from shapely.ops import unary_union
from pyproj import Transformer
from esri import esri_poly
T=Transformer.from_crs(4326,2180,always_xy=True)
inv=pickle.load(open('inv.pkl','rb'))
osm={(t,i):(wkt.loads(g),tg) for t,i,g,tg in inv['forests']}
pt=[(f,wkt.loads(f['geom'])) for f in pickle.load(open('ptlz.pkl','rb'))]
bdl=[(f['properties'],shapely.transform(shape(f['geometry']),lambda a:np.column_stack(T.transform(a[:,0],a[:,1]))).buffer(0)) for f in json.load(open('bdl_items.json'))['features']]
nlp=[(f['attributes'],esri_poly(f['geometry'])) for f in json.load(open('bdl_nlp_items.json')) if f.get('geometry')]
st=pickle.load(open('stations.pkl','rb'))
K=[('K1','Las Solnicki',[('relation',11022876)]),
   ('K2','Las Zwierzyniecki z Lasem Komunalnym',[('way',59421874),('way',59421872),('way',59421873)]),
   ('K3','zadrzewienie olszowo-osikowe na N/NW od lotniska (OSM natural=scrub)',[('way',234039558),('way',1329697013)]),
   ('K4','lasek przy S/SE krawędzi lotniska',[('way',797866399)]),
   ('K5','pas brzozowy między ul. Mickiewicza a E krawędzią lotniska',[('way',797866400)])]
out=[]
for kid,name,ids in K:
    g=unary_union([osm[i][0] for i in ids]); gb=g.buffer(5)
    mem=[(f['id'],f['rodzaj'],f['kat'],round(p.area/1e4,2)) for f,p in pt if p.intersects(gb) and p.intersection(gb).area>0.5*p.area]
    ptl_area=sum(p.intersection(g).area for f,p in pt if p.intersects(g))/1e4
    lp=sum(p.intersection(g).area for a,p in bdl if p.intersects(g))/1e4
    own=collections.defaultdict(float)
    for a,p in nlp:
        if p.intersects(g): own[a['owner_cat_name'].strip()]+=p.intersection(g).area/1e4
    lp_odz=sorted(set(a['adr_for'][:14].strip() for a,p in bdl if p.intersects(g) and p.intersection(g).area>0.3*p.area))
    nlp_odz=sorted(set(a['adress_forest'][:15].strip() for a,p in nlp if p.intersects(g) and p.intersection(g).area>0.3*p.area))
    ed=collections.Counter()
    for s in st:
        if s['osm'] in [f"{t}/{i}" for t,i in ids]: ed[(s['obiekt'],s['strona'])]+=10
    c=T.transform(g.centroid.x,g.centroid.y,direction='INVERSE')
    out.append(dict(id=kid,nazwa=name,osm=[f"{t}/{i}" for t,i in ids],osm_tags=[osm[i][1] for i in ids],pow_osm_ha=round(g.area/1e4,2),pow_ptlz_w_obrysie_osm_ha=round(ptl_area,2),ptlz=mem,
       bdl_lp_ha=round(lp,2),bdl_lp_oddzialy=lp_odz,bdl_poza_lp_ha={k:round(v,2) for k,v in own.items()},bdl_poza_lp_oddzialy=nlp_odz,krawedz_m={f"{a}/{b}":v for (a,b),v in sorted(ed.items())},lat=round(c[1],6),lon=round(c[0],6)))
    o=out[-1]; print(kid,name,o['pow_osm_ha'],o['pow_ptlz_w_obrysie_osm_ha'],'LP',o['bdl_lp_ha'],o['bdl_lp_oddzialy'][:3],len(o['bdl_lp_oddzialy']),'NLP',o['bdl_poza_lp_ha'],o['bdl_poza_lp_oddzialy'],'\n   PTLZ n',len(mem),[m for m in sorted(mem,key=lambda m:-m[3])[:5]],'\n   edges',o['krawedz_m'])
json.dump(out,open('complexes.json','w'),ensure_ascii=False,indent=1)
print(collections.Counter(s['osm'] for s in st).most_common(12))
