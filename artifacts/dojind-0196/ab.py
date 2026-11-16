import sys, json, yaml, numpy as np
sys.path.insert(0,'.'); sys.path.insert(0,'roads')
from streetscape import buildings_mesh as BM
ov=yaml.safe_load(open('../../Data/Regions/bialystok-dojlidy/overrides.yaml',encoding='utf8'))['overrides']
fc=json.load(open('../../Data/Regions/bialystok-dojlidy/buildings.geojson',encoding='utf8'))
class HF:
    def sample(s,e,n): return np.zeros(len(np.atleast_1d(e)))
class Buf:
    def __init__(s): s.t={}
    def add(s,layer,mat,V,UV,T,src=None,UV1=None):
        k=(src,layer); s.t.setdefault(k,{}); s.t[k][mat]=s.t[k].get(mat,0)+len(T)
def run(ovr, sel):
    blds=[b for b in BM.load(fc,(780043,590079),ovr) if sel(b)]
    buf=Buf(); rep={}
    BM.build(buf,blds,HF(),lambda e,n: np.zeros(len(e)),None,None,rep)
    return buf,rep
old=[o for o in ov if not(o['id'].startswith('kuronia2-') or o.get('kind') in ('wall_gates','facade_rules','runway_markings'))]
for title,sel in (('Kuronia 2',lambda b:'941cfc23' in b['id'] or 'kuronia2' in b['id']),('north hall (gates)',lambda b:'2BE4B431' in b['id']),('ALL buildings of the tile',lambda b:True)):
    print(title)
    for name,o in (('  before',old),('  after ',ov)):
        buf,rep=run(o,sel)
        tot={}; mats={}
        for (src,layer),m in buf.t.items():
            tot[layer]=tot.get(layer,0)+sum(m.values()); mats.setdefault(layer,set()).update(m)
        print(name,{k:tot[k] for k in ('buildings','buildings_low')},'materials',{k:len(mats[k]) for k in ('buildings','buildings_low')},rep['hall_wall_runoff_tris'])
