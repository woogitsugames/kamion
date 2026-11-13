"""Count OSM greenery objects in tile bialystok-industrial-c (read-only from local PBF, ODbL).
Run: tools/worldgen/.venv/Scripts/python.exe -I research/g7-street-greenery/tools/osm_tile_greenery.py
"""
import json, collections, sys, math
import osmium
from pyproj import Transformer
from shapely.geometry import Point, LineString, box
from shapely.ops import unary_union
PBF='C:/Users/matma/Documents/Claude/kamion/Data/raw/osm/podlaskie-261108.osm.pbf'
BB=(776971.0,595199.0,779019.0,597247.0)
to2180=Transformer.from_crs(4326,2180,always_xy=True)
to4326=Transformer.from_crs(2180,4326,always_xy=True)
x0,y0=to4326.transform(BB[0]-200,BB[1]-200); x1,y1=to4326.transform(BB[2]+200,BB[3]+200)
tile=box(*BB)
class H(osmium.SimpleHandler):
    def __init__(s):
        super().__init__(); s.trees=[]; s.rows=[]; s.hedges=[]; s.streets=[]; s.other=[]
    def node(s,n):
        if n.location.valid() and x0<=n.location.lon<=x1 and y0<=n.location.lat<=y1:
            t=dict(n.tags)
            if t.get('natural')=='tree':
                x,y=to2180.transform(n.location.lon,n.location.lat)
                s.trees.append(dict(id=n.id,x=x,y=y,lat=n.location.lat,lon=n.location.lon,tags=t))
    def way(s,w):
        t=dict(w.tags)
        try:
            pts=[to2180.transform(n.lon,n.lat) for n in w.nodes if n.location.valid()]
        except Exception: return
        if len(pts)<2: return
        ls=LineString(pts)
        if not ls.intersects(box(BB[0]-100,BB[1]-100,BB[2]+100,BB[3]+100)): return
        if t.get('natural')=='tree_row': s.rows.append(dict(id=w.id,geom=ls,tags=t))
        elif t.get('barrier')=='hedge': s.hedges.append(dict(id=w.id,geom=ls,tags=t))
        elif 'highway' in t and t.get('name'): s.streets.append(dict(id=w.id,geom=ls,tags=t))
        elif t.get('natural') in('scrub','wood') or t.get('landuse') in('forest',): s.other.append(dict(id=w.id,tags=t,area=ls.length))
h=H(); h.apply_file(PBF,locations=True)
out=dict(trees=[(t['id'],round(t['x'],1),round(t['y'],1),round(t['lat'],6),round(t['lon'],6),t['tags']) for t in h.trees if tile.contains(Point(t['x'],t['y']))])
out['rows']=[(r['id'],round(r['geom'].intersection(tile).length,1),r['tags']) for r in h.rows if r['geom'].intersects(tile)]
out['hedges']=[(r['id'],round(r['geom'].intersection(tile).length,1),r['tags']) for r in h.hedges if r['geom'].intersects(tile)]
print('trees in tile',len(out['trees']),'rows',len(out['rows']),'hedges',len(out['hedges']))
print('tree tags:',collections.Counter(k for t in out['trees'] for k in t[5]).most_common(15))
print('species:',collections.Counter(t[5].get('species') or t[5].get('genus') for t in out['trees']))
print('leaf_type',collections.Counter(t[5].get('leaf_type') for t in out['trees']))
print('rows tags',[(r[0],r[1],r[2]) for r in out['rows']][:20])
print('hedges',[(r[0],r[1],r[2]) for r in out['hedges']][:20])
# street density
names=['Kowieńska','Lidzka','Skidelska','Wołkowyska','Świsłocka','Wileńska','Sokólska','Generała Władysława Andersa','Andersa']
bystreet=collections.defaultdict(list)
for s in h.streets:
    n=s['tags']['name']
    bystreet[n].append(s)
res={}
for n in sorted(bystreet):
    segs=[s['geom'].intersection(tile) for s in bystreet[n]]
    L=sum(g.length for g in segs if not g.is_empty)
    if L<30: continue
    res[n]=L
print(len(res),'named streets in tile')
tp=[Point(t[1],t[2]) for t in out['trees']]
rowgeo=[r['geom'].intersection(tile) for r in h.rows]
hedgeg=[r['geom'].intersection(tile) for r in h.hedges]
dump={}
for n,L in sorted(res.items(),key=lambda kv:-kv[1]):
    line=unary_union([s['geom'] for s in bystreet[n]]).intersection(tile)
    row=dict(length_m=round(L,1),highway=bystreet[n][0]['tags']['highway'])
    for d in(15,25):
        buf=line.buffer(d)
        row[f'trees_{d}m']=sum(1 for p in tp if buf.contains(p))
        row[f'rowlen_{d}m']=round(sum(g.intersection(buf).length for g in rowgeo if not g.is_empty),1)
        row[f'hedgelen_{d}m']=round(sum(g.intersection(buf).length for g in hedgeg if not g.is_empty),1)
    dump[n]=row
json.dump(dict(out=out,streets=dump),open('C:/Users/matma/Documents/Claude/kamion/research/g7-street-greenery/tools/osm_tile_greenery.json','w'),ensure_ascii=False,default=str)
for n,r in dump.items(): print(n,r)
