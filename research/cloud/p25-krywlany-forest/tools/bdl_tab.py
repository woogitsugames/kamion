import json,glob,collections,csv,pickle
import numpy as np, shapely
from shapely.geometry import shape
from shapely import wkt
from shapely.ops import unary_union
from pyproj import Transformer
T=Transformer.from_crs(4326,2180,always_xy=True)
inv=pickle.load(open('inv.pkl','rb')); aero=wkt.loads(inv['aero'])
sel={'D303':'Dywizjonu 303','MICK':'Adama Mickiewicza','KUR':'Jacka Kuronia','CIOL':'Konstantego Ciołkowskiego'}
roads={k:unary_union([wkt.loads(l) for i,l,h in inv['roads'][v]]) for k,v in sel.items()}
items=json.load(open('bdl_items.json'))['features']
out=[]
for f in items:
    p=f['properties']; g=shapely.transform(shape(f['geometry']),lambda a:np.column_stack(T.transform(a[:,0],a[:,1]))).buffer(0)
    try: d=json.load(open(f"bdl_sd/{p['a_i_num']}.json"))
    except Exception: d={}
    ls=d.get('layerSpecies') or []; ly=d.get('layer') or []
    gd=(d.get('generalData') or [{}])[0]
    main=[s for s in ls if s['storey_cd'].startswith('DRZEW') and s['height']]
    sklad=' '.join(f"{s['part_cd'].split(':')[0]}{s['species_cd'].split(':')[0]}({s['species_age']}l,H{s['height']},D{s['bhd']})" for s in main)
    pod=[s['species_cd'].split(':')[1] for s in ls if s['storey_cd'].startswith('PODSZ')]
    podc=[l['standdensity_index'] for l in ly if l['storey_cd'].startswith('PODSZ')]
    drz=[l for l in ly if l['storey_cd'].startswith('DRZEW')]
    c=T.transform(g.centroid.x,g.centroid.y,direction='INVERSE')
    dd={k:round(g.distance(r)) for k,r in roads.items()}; dd['AERO']=round(g.distance(aero))
    out.append(dict(adr_for=p['adr_for'],a_i_num=p['a_i_num'],a_year=p['a_year'],area_type=p['area_type'],pow_ha=p['sub_area'],siedlisko=p['site_type'],
      gat_pan=p['species_cd'],wiek=p['spec_age'],H_gat_pan_m=main[0]['height'] if main else '',D_cm=main[0]['bhd'] if main else '',bonitacja=main[0]['site_class_cd'].split(':')[0] if main else '',
      sklad=sklad,zwarcie=drz[0]['density_cd'].split(':')[0] if drz else '',zadrzewienie=drz[0]['standdensity_index'] if drz else '',zmieszanie=drz[0]['mixture_cd'].split(':')[0] if drz else '',
      podszyt_gat='; '.join(pod),podszyt_pokrycie=podc[0] if podc else '',pokrywa=(d.get('generalData2') or [{}])[0].get('veg_cover_cd',''),
      lat=round(c[1],6),lon=round(c[0],6),**{'d_'+k:v for k,v in dd.items()}))
out.sort(key=lambda r:r['adr_for'])
w=csv.DictWriter(open('bdl_wydzielenia.csv','w',newline='',encoding='utf-8'),fieldnames=list(out[0].keys())); w.writeheader(); w.writerows(out)
near=[r for r in out if min(r['d_D303'],r['d_MICK'],r['d_AERO'],r['d_CIOL'],r['d_KUR'])<=80 and r['area_type']=='D-STAN']
for r in near: print(r['adr_for'],r['pow_ha'],r['siedlisko'],r['sklad'],'| zw',r['zwarcie'],r['zadrzewienie'],'| podsz',r['podszyt_pokrycie'],r['podszyt_gat'][:70],'|',{k[2:]:r[k] for k in r if k.startswith('d_') and r[k]<=80})
# area-weighted stats all stands
st=[r for r in out if r['area_type']=='D-STAN' and r['H_gat_pan_m']]
A=sum(r['pow_ha'] for r in st); print('n',len(st),'ha',A)
cs=collections.defaultdict(float)
for r in st: cs[r['gat_pan']]+=r['pow_ha']
print({k:round(100*v/A,1) for k,v in cs.items()})
H=np.array([float(r['H_gat_pan_m']) for r in st]);W=np.array([r['pow_ha'] for r in st]);AG=np.array([r['wiek'] for r in st])
print('H mean w',(H*W).sum()/W.sum(),'min',H.min(),'max',H.max(),'age w',(AG*W).sum()/W.sum(),AG.min(),AG.max())
