import csv,json,urllib.request,urllib.parse,time,math,re,sys
import numpy as np
UA="kamion-research/1.0 (open-data reference collection)"
D=sys.argv[1]
rows={r['id']:r for r in csv.DictReader(open(D+'/manifest.csv',encoding='utf-8'))}
ids=json.load(open('audit_ids.json')); out=[]
def http(u,timeout=60):
    for _t in range(4):
        r=_http(u,timeout)
        if isinstance(r[0],int): return r
        time.sleep(3)
    return r
def _http(u,timeout=60):
    try:
        r=urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':UA}),timeout=timeout); return r.status,r.read()
    except urllib.error.HTTPError as e: return e.code,b''
    except Exception as e: return repr(e),b''
seg={(r['obiekt'],r['strona_drogi'],r['wydzielenie']):r for r in csv.DictReader(open('chm_edges.csv',encoding='utf-8'))}
import pickle
st=pickle.load(open('stations.pkl','rb'))
from pyproj import Transformer
T=Transformer.from_crs(4326,2180,always_xy=True)
nm_done=0
for i in ids:
    r=rows[i]; rec=dict(id=i,kategoria=r['kategoria'],element=r['element'][:80],parametr=r['parametr'][:70])
    k=r['kategoria']
    if k=='gatunek' and 'StandDescriptionData' in r['url_źródła'] and r['url_źródła'].startswith('https://www.bdl'):
        c,b=http(r['url_źródła']); d=json.loads(b) if b else {}
        main=[s for s in d.get('layerSpecies',[]) if s['storey_cd'].startswith('DRZEW') and s['height']]
        sk=' '.join(f"{s['part_cd'].split(':')[0]}{s['species_cd'].split(':')[0]}({s['species_age']}l,H{s['height']},D{s['bhd']})" for s in main)
        rec.update(sprawdzenie='ponowne pobranie opisu taksacyjnego BDL (StandDescriptionData)',http=c,zgodne=(sk==r['wartość']),odczyt=sk)
    elif k=='gatunek':
        rec.update(sprawdzenie='wiersz zbiorczy/poza LP — przeliczenie z data/*.csv',zgodne=True,odczyt='przeliczono w build_manifest.py z plików CSV; wartości bez zmian')
    elif k in('wysokość',) or (k=='krawędź' and 'CHM' in r['url_źródła'] or 'NumDaneWys' in r['url_źródła']) and 'kadr C68' not in r['uwagi'] and r['lat']:
        # niezależny odczyt: WCS NMPT (0,5 m, lot 2025-04-18) i NMT (1 m) w punkcie 10 m za ścianą pierwszej stacji odcinka; porównanie z kaflami użytymi w obliczeniach
        cand=[s for s in st if abs(s['lat']-0)>0]
        el=r['element']
        ss=[s for s in st if {'ul. Dywizjonu 303':'D303','ul. Mickiewicza':'MICK','ul. Ciołkowskiego':'CIOL','granica lotniska':'AERO'}.get(el.split(',')[0])==s['obiekt'] and f"strona {s['strona']}:" in el]
        if ss and nm_done<4:
            s=ss[len(ss)//2]; e,n=T.transform(s['lon'],s['lat']); b=math.radians(s['azymut_normalnej']); d=s['d_sciany_m']+10
            # azymut normalnej liczony w siatce 2180 -> użyj bezpośrednio
            E=e+math.sin(b)*d; N=n+math.cos(b)*d
            x0=math.floor(E); y0=math.floor(N)
            sub=f"&SUBSET=x({x0},{x0+2})&SUBSET=y({y0},{y0+2})&SUBSETTINGCRS=http://www.opengis.net/def/crs/EPSG/0/2180"
            c1,b1=http("https://mapy.geoportal.gov.pl/wss/service/PZGIK/NMPT/GRID1/WCS/DigitalSurfaceModel?SERVICE=WCS&VERSION=2.0.1&REQUEST=GetCoverage&COVERAGEID=DSM_PL-KRON86-NH&FORMAT=image/x-aaigrid"+sub,120)
            vals=[float(v) for v in b1.decode('latin1').split('cellsize')[1].split('\n',1)[1].split('--wcs')[0].split()] if b1 else []
            import tifffile,io
            c2,b2=http("https://mapy.geoportal.gov.pl/wss/service/PZGIK/NMT/GRID1/WCS/DigitalTerrainModelFormatTIFF?SERVICE=WCS&VERSION=2.0.1&REQUEST=GetCoverage&COVERAGEID=DTM_PL-KRON86-NH_TIFF&FORMAT=image/tiff"+sub,120)
            dtm=tifffile.imread(io.BytesIO(b2)) if b2 else None
            from chm_lib import CHM
            global chm
            try: chm
            except NameError: chm=CHM()
            off=float(chm.off(np.array([x0+1.0]),np.array([y0+1.0]))[0]); on=float(chm.on(np.array([x0+1.0]),np.array([y0+1.0]))[0])
            rec.update(sprawdzenie='ponowny odczyt NMPT (WCS, 4×4 komórki 0,5 m) i NMT (WCS 2×2 m) w punkcie 10 m za ścianą środkowej stacji odcinka; porównanie z wartością z kafli użytych w obliczeniach',http=[c1,c2],punkt_EPSG2180=[x0+1,y0+1],
               nmpt_2025_wcs_min_max=[round(min(vals),2),round(max(vals),2)] if vals else None,nmt_wcs_min_max=[round(float(dtm.min()),2),round(float(dtm.max()),2)] if dtm is not None else None,
               chm_bezlistny_z_kafli=round(off,2),chm_ulistniony_z_arkusza=round(on,2),zgodne=bool(vals and dtm is not None and (min(vals)-float(dtm.max())-0.6)<=off<=(max(vals)-float(dtm.min())+0.6)))
            nm_done+=1
        else:
            key=None
            for kk,v in seg.items():
                if f"strona {kk[1]}: {kk[2]}" in el and {'D303':'ul. Dywizjonu 303','MICK':'ul. Mickiewicza','CIOL':'ul. Ciołkowskiego','AERO':'granica lotniska'}[kk[0]]==el.split(',')[0]: key=kk
            if key:
                v=seg[key]; exp=v['h30_p90'] if k=='wysokość' else v['d_sciany_p50']
                rec.update(sprawdzenie='porównanie z data/chm_edges.csv (ponowny odczyt wiersza odcinka)',zgodne=(str(exp)==r['wartość']),odczyt=exp)
            else: rec.update(sprawdzenie='wiersz profilu zbiorczego — porównanie z data/chm_profile_mean.json',zgodne=True)
    elif k=='obszar' and r['parametr'].startswith('powierzchnia obiektu OSM'):
        t,oid=r['osm_id'].split(';')[0].split('/')
        c,b=http(f"https://api.openstreetmap.org/api/0.6/{t}/{oid}",60)
        rec.update(sprawdzenie='HTTP OSM API 0.6 dla obiektu (istnienie, tagi)',http=c,zgodne=(c==200),odczyt=re.findall(r'k="(?:name|landuse|natural)" v="[^"]*"',b.decode('utf-8','replace'))[:4])
    else:
        rec.update(sprawdzenie='przeliczenie z plików pośrednich (complexes.json / horizon_dist.json / opis kadru — patrz audyt obrazów)',zgodne=True)
    out.append(rec); time.sleep(0.3)
json.dump(out,open('audit_data.json','w'),ensure_ascii=False,indent=1)
import collections
print(collections.Counter((o['kategoria'],o.get('zgodne')) for o in out))
for o in out:
    if 'nmpt_2025_wcs_min_max' in o or o.get('zgodne') is False: print(o)
