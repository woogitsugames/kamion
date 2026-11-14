import json,csv,pickle,collections
from esri import esri_poly
from shapely import wkt
from shapely.ops import unary_union
from pyproj import Transformer
T=Transformer.from_crs(4326,2180,always_xy=True)
inv=pickle.load(open('inv.pkl','rb')); aero=wkt.loads(inv['aero'])
sel={'D303':'Dywizjonu 303','MICK':'Adama Mickiewicza','KUR':'Jacka Kuronia','CIOL':'Konstantego Ciołkowskiego'}
roads={k:unary_union([wkt.loads(l) for i,l,h in inv['roads'][v]]) for k,v in sel.items()}
out=[]
for f in json.load(open('bdl_nlp_items.json')):
    a=f['attributes']; g=esri_poly(f['geometry'])
    try: d=json.load(open(f"bdl_sd_nlp/{a['arodes_int_num']}.json"))
    except Exception: d={}
    ls=d.get('layerSpecies') or []; ly=d.get('layer') or []
    main=[s for s in ls if s['storey_cd'].startswith('DRZEW') and s['height']]
    sklad=' '.join(f"{s['part_cd'].split(':')[0]}{s['species_cd'].split(':')[0]}({s['species_age']}l,H{s['height']},D{s['bhd']})" for s in main)
    pod=[s['species_cd'].split(':')[1] for s in ls if s['storey_cd'].startswith('PODSZ')]
    podc=[l['standdensity_index'] for l in ly if l['storey_cd'].startswith('PODSZ')]
    drz=[l for l in ly if l['storey_cd'].startswith('DRZEW')]
    c=T.transform(g.centroid.x,g.centroid.y,direction='INVERSE')
    dd={k:round(g.distance(r)) for k,r in roads.items()}; dd['AERO']=round(g.distance(aero))
    out.append(dict(adr_for=a['adress_forest'].strip(),a_i_num=a['arodes_int_num'],a_year=a['a_year'],wlasnosc=a['owner_cat_name'].strip(),area_type=a['area_type_cd'].strip(),pow_ha=a['sub_area'],siedlisko=(a['site_type_cd'] or '').strip(),
      gat_pan=(a['species_cd_d'] or '').strip(),wiek=a['species_age'],H_gat_pan_m=main[0]['height'] if main else '',D_cm=main[0]['bhd'] if main else '',sklad=sklad,
      zwarcie=drz[0]['density_cd'] if drz else '',zadrzewienie=drz[0]['standdensity_index'] if drz else '',podszyt_gat='; '.join(pod),podszyt_pokrycie=podc[0] if podc else '',
      lat=round(c[1],6),lon=round(c[0],6),**{'d_'+k:v for k,v in dd.items()}))
out.sort(key=lambda r:r['adr_for'])
w=csv.DictWriter(open('bdl_poza_lp.csv','w',newline='',encoding='utf-8'),fieldnames=list(out[0].keys())); w.writeheader(); w.writerows(out)
print(len(out))
for r in out:
    if r['wlasnosc']!='prywatne' and min(r['d_D303'],r['d_MICK'],r['d_CIOL'],r['d_AERO'])<=80: print(r['adr_for'],r['wlasnosc'],r['pow_ha'],r['siedlisko'],r['sklad'],'| zw',r['zwarcie'],r['zadrzewienie'],'| podsz',r['podszyt_pokrycie'],r['podszyt_gat'][:60],'|',{k[2:]:r[k] for k in r if k.startswith('d_') and r[k]<=80})
g=[r for r in out if r['wlasnosc']=='gminne']
print('gminne ha',sum(float(str(r['pow_ha']).replace(',','.')) for r in g), collections.Counter(r['adr_for'][:15] for r in g))
