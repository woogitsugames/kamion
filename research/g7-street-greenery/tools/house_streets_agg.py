"""Aggregate ortho-derived crowns (plot_canopy.json) along the house streets of tile C. Run with worldgen venv python -I."""
import json, statistics as st, collections
from shapely.geometry import Point, LineString
from shapely.ops import unary_union
R='C:/Users/matma/Documents/Claude/kamion/'
O=(777995.0,596223.0)
g=json.load(open(R+'Data/Regions/bialystok-industrial-c/roads.graph.json'))
pc=json.load(open(R+'Data/Regions/bialystok-industrial-c/plot_canopy.json'))
cr=[(c[0]+O[0],c[1]+O[1],c[2],c[3],c[4]) for c in pc['crowns']]
H=['Kowieńska','Lidzka','Skidelska','Wołkowyska','Świsłocka','Wileńska','Grodzieńska']
res={}
def q(a,n):
    a=sorted(a); 
    return round(a[min(len(a)-1,int(n*len(a)))],2)
out={}
for grp,names in (('Kowienska-Wolkowyska-Lidzka-Swislocka-Wilenska (tile core)',['Kowieńska','Lidzka','Wołkowyska','Świsłocka','Wileńska']),('Skidelska',['Skidelska']),('all7',H)):
    u=unary_union([LineString(e['geometry']) for e in g['edges'] if e['attrs'].get('name',{}).get('v') in names])
    L=u.length
    for d in (8,12,20):
        b=u.buffer(d)
        c=[x for x in cr if b.contains(Point(x[0],x[1]))]
        t=[x for x in c if x[2]>=1.25]; s=[x for x in c if x[2]<1.25]
        dec=[x for x in t if not x[3]]; con=[x for x in t if x[3]]
        o=dict(L=round(L,1),n_crowns=len(c),trees=len(t),shrubs=len(s),trees_per100m=round(len(t)/L*100,1),shrubs_per100m=round(len(s)/L*100,1),
               conifer_share_trees=round(len(con)/max(1,len(t)),2),
               r_med=round(st.median([x[2] for x in t]),2) if t else None,r_p25=q([x[2] for x in t],.25) if t else None,r_p75=q([x[2] for x in t],.75) if t else None,r_p90=q([x[2] for x in t],.9) if t else None,
               r_dec_med=round(st.median([x[2] for x in dec]),2) if dec else None, r_con_med=round(st.median([x[2] for x in con]),2) if con else None,
               big_ge4=sum(1 for x in t if x[2]>=4))
        out[f'{grp} d={d}']=o
        print(grp,d,o)
json.dump(out,open(R+'research/g7-street-greenery/tools/house_streets_agg.json','w'),ensure_ascii=False,indent=1)
