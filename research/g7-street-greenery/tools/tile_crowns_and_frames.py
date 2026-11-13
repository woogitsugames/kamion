"""Per-street crown stats from plot_canopy.json (ortho-derived, repo), BDOT10k trees, and Mapillary frames near target streets.
Run: tools/worldgen/.venv/Scripts/python.exe -I research/g7-street-greenery/tools/tile_crowns_and_frames.py"""
import json, math, collections, statistics as st
from shapely.geometry import Point, LineString, shape
from shapely.ops import unary_union
from pyproj import Transformer
R='C:/Users/matma/Documents/Claude/kamion/'
O=(777995.0,596223.0)
BB=(776971.0,595199.0,779019.0,597247.0)
g=json.load(open(R+'Data/Regions/bialystok-industrial-c/roads.graph.json'))
pc=json.load(open(R+'Data/Regions/bialystok-industrial-c/plot_canopy.json'))
ss=json.load(open(R+'Data/Regions/bialystok-industrial-c/generated/streetscape_sources.json'))
crowns=[(c[0]+O[0],c[1]+O[1],c[2],c[3],c[4]) for c in pc['crowns']]
print('crowns',len(crowns), 'params',pc['params'], 'counts',pc['counts'])
streets=['Kowieńska','Lidzka','Skidelska','Wołkowyska','Świsłocka','Wileńska','Sokólska','Generała Władysława Andersa','Michała Motoszko','Olsztyńska','Racławicka','Grodzieńska','Buska','Łańcucka']
lines=collections.defaultdict(list)
for e in g['edges']:
    n=e['attrs'].get('name',{}).get('v')
    if n in streets: lines[n].append(LineString(e['geometry']))
bd=[Point(f['geometry']['coordinates']) for f in ss['bdot10k']['OT_OIPR_P']]
bdl=[shape(f['geometry']) for f in ss['bdot10k']['OT_OIPR_L'] if 'drzew' in f['props'].get('rodzaj','') or True]
print('OIPR_L rodzaj',collections.Counter(f['props'].get('rodzaj') for f in ss['bdot10k']['OT_OIPR_L']))
print('OIPR_P rodzaj',collections.Counter(f['props'].get('rodzaj') for f in ss['bdot10k']['OT_OIPR_P']))
res={}
for n,ls in lines.items():
    u=unary_union(ls)
    L=u.length
    dual = n.startswith('General')
    Lr = L/2 if dual else L
    row=dict(length_m=round(L,1),length_eff_m=round(Lr,1))
    for d in (12,30):
        buf=u.buffer(d)
        cs=[c for c in crowns if buf.contains(Point(c[0],c[1]))]
        trees=[c for c in cs if c[2]>=1.25 or True]
        row[f'crowns_{d}m']=len(cs)
        row[f'crowns_per100m_{d}m']=round(len(cs)/Lr*100,1)
        row[f'bdot_trees_{d}m']=sum(1 for p in bd if buf.contains(p))
        rr=[c[2] for c in cs if c[2]>=1.0]
        if rr:
            q=st.quantiles(rr,n=10) if len(rr)>=10 else None
            row[f'radius_median_{d}m']=round(st.median(rr),2)
            row[f'radius_p90_{d}m']=round(q[-1],2) if q else None
            row[f'conifer_share_{d}m']=round(sum(1 for c in cs if c[3])/len(cs),2)
            row[f'big_r>=3_{d}m']=sum(1 for c in cs if c[2]>=3)
    res[n]=row
    print(n,row)
json.dump(res,open(R+'research/g7-street-greenery/tools/tile_crowns.json','w'),ensure_ascii=False,indent=1)
# whole-tile crown radius histogram
rs=[c[2] for c in crowns]
print('tile radius deciles',[round(x,2) for x in st.quantiles(rs,n=10)], 'conifer share',round(sum(c[3] for c in crowns)/len(crowns),2))
# mapillary frames near target streets
fr=[json.loads(l) for l in open(R+'Data/raw/mapillary/bialystok-industrial-c/manifest.jsonl')]
t=Transformer.from_crs(4326,2180,always_xy=True)
out=[]
for f in fr:
    x,y=t.transform(f['lon'],f['lat']); p=Point(x,y)
    best=min(((u.distance(p),n) for n,u in ((n,unary_union(ls)) for n,ls in lines.items())))
    if best[0]<30 and BB[0]<x<BB[2] and BB[1]<y<BB[3]:
        out.append((best[1],round(best[0]),f['id'],f['captured_at'],round(f['compass_angle'])))
print(len(fr),'frames; near target streets:',collections.Counter(o[0] for o in out))
for o in sorted(out)[:80]: print(o)
