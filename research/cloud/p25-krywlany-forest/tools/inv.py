import json,sys
from shapely.geometry import Polygon,LineString,MultiPolygon,Point
from shapely.ops import unary_union,polygonize,linemerge
from pyproj import Transformer
T=Transformer.from_crs(4326,2180,always_xy=True)
d=json.load(open('osm1.json'))
def pts(g): return [T.transform(p['lon'],p['lat']) for p in g]
roads={};forests=[];aero=None;fences=[];runways=[]
for e in d['elements']:
    t=e.get('tags',{})
    if e['type']=='way':
        g=pts(e['geometry'])
        if t.get('highway') and t.get('name'):
            roads.setdefault(t['name'],[]).append((e['id'],LineString(g),t.get('highway')))
        elif t.get('aeroway')=='aerodrome': aero=Polygon(g)
        elif t.get('aeroway')=='runway': runways.append((e['id'],LineString(g),t))
        elif t.get('barrier')=='fence': fences.append((e['id'],LineString(g)))
        elif (t.get('landuse')=='forest' or t.get('natural') in('wood','scrub')) and len(g)>=4 and g[0]==g[-1]:
            forests.append(('way',e['id'],Polygon(g).buffer(0),t))
    else:
        if t.get('landuse')=='forest' or t.get('natural')=='wood':
            outer=[];inner=[]
            for m in e['members']:
                if m['type']=='way' and 'geometry' in m:
                    (outer if m['role']!='inner' else inner).append(LineString(pts(m['geometry'])))
            po=unary_union(list(polygonize(linemerge(outer) if len(outer)>1 else outer)))
            pi=unary_union(list(polygonize(linemerge(inner) if len(inner)>1 else inner))) if inner else None
            forests.append(('relation',e['id'],(po.difference(pi) if pi else po).buffer(0),t))
keyroads={k:unary_union([x[1] for x in v]) for k,v in roads.items()}
sel=['Dywizjonu 303','Adama Mickiewicza','Jacka Kuronia','Konstantego Ciołkowskiego']
print('aero area ha',aero.area/1e4, 'centroid', T.transform(*aero.centroid.coords[0],direction='INVERSE'))
rows=[]
for typ,i,p,t in forests:
    dd={k:p.distance(keyroads[k]) for k in sel}
    da=p.distance(aero)
    if min(min(dd.values()),da)<=80:
        c=T.transform(p.centroid.x,p.centroid.y,direction='INVERSE')
        rows.append((typ,i,t.get('landuse') or t.get('natural'),t.get('leaf_type'),t.get('name'),round(p.area/1e4,2),{k[:6]:round(v) for k,v in dd.items()},round(da),round(c[1],5),round(c[0],5)))
rows.sort(key=lambda r:-r[5])
for r in rows: print(r)
import pickle
pickle.dump({'forests':[(a,b,c.wkt,t) for a,b,c,t in forests],'roads':{k:[(i,l.wkt,h) for i,l,h in v] for k,v in roads.items()},'aero':aero.wkt,'fences':[(i,l.wkt) for i,l in fences],'runways':[(i,l.wkt,t) for i,l,t in runways]},open('inv.pkl','wb'))
