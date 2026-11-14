from shapely.geometry import Polygon
from shapely.ops import unary_union
def esri_poly(g):
    outs=[];holes=[]
    for r in g['rings']:
        if len(r)<4: continue
        a=sum((x2-x1)*(y2+y1) for (x1,y1),(x2,y2) in zip(r,r[1:]))
        (outs if a>0 else holes).append(Polygon(r).buffer(0))   # Esri: pierścień zewnętrzny zgodnie z ruchem wskazówek zegara
    if not outs: outs,holes=holes,[]
    u=unary_union(outs)
    return u.difference(unary_union(holes)) if holes else u
