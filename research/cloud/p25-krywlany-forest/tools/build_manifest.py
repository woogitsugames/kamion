# Buduje manifest.csv i files_index.csv z danych pośrednich (data/*.csv, *.json) i opisów kadrów (frames_desc.py).
import csv,json,hashlib,os,sys,collections,urllib.parse
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import frames_desc as FD
S=sys.argv[1] if len(sys.argv)>1 else '.'      # katalog roboczy z plikami pośrednimi i pobranymi obrazami
OUT=sys.argv[2] if len(sys.argv)>2 else '.'
DA='2026-11-14'
COLS=['id','kategoria','element','parametr','wartość','jednostka','osm_id','lat','lon','kierunek_deg','odległość_od_krawędzi_m','data_zdjęcia','sezon','pora_dnia','opis_co_widać','url_źródła','licencja','autor','data_dostępu','status','uwagi','url_pliku','sha256']
rows=[]
def add(**k):
    r={c:'' for c in COLS}; r.update(k); r['id']='C68-%03d'%(len(rows)+1); r['data_dostępu']=DA; rows.append(r); return r
U_OSM='https://www.openstreetmap.org/'; L_OSM='ODbL 1.0 (© OpenStreetMap contributors)'
U_BDOT='https://opendata.geoportal.gov.pl/bdot10k/schemat2021/20/2061_GML.zip'; L_GUG='dane PZGiK udostępniane bezpłatnie (art. 40a ust. 2 pkt 1 Pgik); źródło: GUGiK'
U_BDL='https://www.bdl.lasy.gov.pl/portal/mapy'; L_BDL='informacja publiczna/o środowisku — ponowne wykorzystanie wg Regulaminu BDL cz. V (podać źródło, czas wytworzenia i pozyskania)'
U_NMPT='https://opendata.geoportal.gov.pl/NumDaneWys/NMPT/78825/78825_1436515_N-34-107-C-b-4-3.asc'  # + arkusze -3-2, -3-3, -3-4 i NMT z WCS — pełna lista w sources.md
def sha256(fn): return hashlib.sha256(open(fn,'rb').read()).hexdigest()
# ---------------- A. obszar ----------------
cx=json.load(open(f'{S}/complexes.json'))
for c in cx:
    osm=';'.join(c['osm']); tg=c['osm_tags'][0]
    add(kategoria='obszar',element=f"{c['id']} {c['nazwa']}",parametr='powierzchnia obiektu OSM',wartość=c['pow_osm_ha'],jednostka='ha',osm_id=osm,lat=c['lat'],lon=c['lon'],url_źródła=U_OSM+c['osm'][0],licencja=L_OSM,autor='OpenStreetMap contributors',status='SOURCED',
        uwagi=f"tagi: {'landuse='+tg['landuse'] if 'landuse' in tg else 'natural='+tg.get('natural','')}; leaf_type={tg.get('leaf_type','brak')}; powierzchnia liczona w EPSG:2180 (tools/inv.py); Overpass 2026-11-14T16:46:28Z")
    top=sorted(c['ptlz'],key=lambda m:-m[3])[:6]
    add(kategoria='obszar',element=f"{c['id']} {c['nazwa']}",parametr='powierzchnia BDOT10k PTLZ w obrysie OSM',wartość=c['pow_ptlz_w_obrysie_osm_ha'],jednostka='ha',osm_id=osm,lat=c['lat'],lon=c['lon'],url_źródła=U_BDOT,licencja=L_GUG,autor='GUGiK',status='SOURCED',
        uwagi=f"{len(c['ptlz'])} obiektów OT_PTLZ_A; największe (lokalnyId, rodzaj/kategoria, ha): "+'; '.join(f"{m[0]} {m[1]}/{m[2]} {m[3]}" for m in top))
    own=', '.join(f"{k} {v} ha" for k,v in c['bdl_poza_lp_ha'].items() if v>=0.3)
    add(kategoria='obszar',element=f"{c['id']} {c['nazwa']}",parametr='zarządca/własność wg BDL (powierzchnia wydzieleń w obrysie OSM)',wartość=(f"PGL LP {c['bdl_lp_ha']} ha" if c['bdl_lp_ha']>=0.3 else '')+('; ' if c['bdl_lp_ha']>=0.3 and own else '')+own,jednostka='ha',osm_id=osm,lat=c['lat'],lon=c['lon'],url_źródła=U_BDL,licencja=L_BDL,autor='BULiGL / PGL LP',status='SOURCED',
        uwagi=('LP: RDLP Białystok, Nadl. Dojlidy, obręb 1, leśn. 09 Solnicki Las, oddz. '+', '.join(x.split('-')[-1] for x in c['bdl_lp_oddzialy'])+' (PUL 2017–2026, stan 2026). ' if c['bdl_lp_oddzialy'] else '')+('Poza LP (PUL, stan 2023): oddz. '+', '.join(c['bdl_poza_lp_oddzialy']) if c['bdl_poza_lp_oddzialy'] else ''))
    for k,v in c['krawedz_m'].items():
        ob,side=k.split('/')
        nm={'D303':'ul. Dywizjonu 303','MICK':'ul. Mickiewicza','CIOL':'ul. Ciołkowskiego','AERO':'granica lotniska (OSM aeroway=aerodrome)'}[ob]
        az={'N':0,'NE':45,'E':90,'SE':135,'S':180,'SW':225,'W':270,'NW':315}[side]
        add(kategoria='obszar',element=f"{c['id']} {c['nazwa']}",parametr=f"długość krawędzi lasu widocznej z: {nm}, strona {side}",wartość=v,jednostka='m',osm_id=osm,lat=c['lat'],lon=c['lon'],kierunek_deg=(az+90)%180,url_źródła=U_NMPT,licencja=L_GUG,autor='GUGiK; obliczenia własne',status='ESTIMATED',
            uwagi=f"liczba stacji co 10 m wzdłuż osi (OSM), na których ściana lasu (CHM≥5 m i mediana CHM na 15 m ≥10 m, punkt w PTLZ) leży ≤80 m od osi po stronie {side}; kierunek_deg = oś krawędzi (mod 180°), normalna ku lasowi ≈{az}°; tools/chm_edges.py, complexes.py; dokładność ±10 m na koniec odcinka")
# ---------------- B. gatunek ----------------
def fnum(x):
    try: return float(str(x).replace(',','.'))
    except Exception: return None
lp=list(csv.DictReader(open(f'{S}/bdl_wydzielenia.csv',encoding='utf-8')))
near=lambda r: min(int(r['d_D303']),int(r['d_MICK']),int(r['d_CIOL']),int(r['d_AERO']))<=80
st=[r for r in lp if r['area_type']=='D-STAN' and r['H_gat_pan_m']]
A=sum(float(r['pow_ha']) for r in st); cs=collections.defaultdict(float)
for r in st: cs[r['gat_pan']]+=float(r['pow_ha'])
add(kategoria='gatunek',element='K1 Las Solnicki — wszystkie drzewostany LP w oknie (132 wydz.)',parametr='udział powierzchniowy gatunku panującego',wartość='; '.join(f"{k} {100*v/A:.1f}%" for k,v in sorted(cs.items(),key=lambda kv:-kv[1])),jednostka='% pow.',osm_id='relation/11022876',url_źródła='https://ogcapi.bdl.lasy.gov.pl/collections/RDLP_Bialystok_wydzielenia/items?bbox=23.140,53.078,23.215,53.118',licencja=L_BDL,autor='BULiGL / PGL LP',status='SOURCED',uwagi=f"suma {A:.2f} ha; SO sosna, BRZ brzoza, OL olsza, DB dąb, ŚW świerk, JS jesion; data/bdl_wydzielenia.csv")
Hw=sum(float(r['H_gat_pan_m'])*float(r['pow_ha']) for r in st)/A; Aw=sum(float(r['wiek'])*float(r['pow_ha']) for r in st)/A
add(kategoria='gatunek',element='K1 Las Solnicki — wszystkie drzewostany LP w oknie',parametr='wysokość gat. panującego, średnia ważona powierzchnią (BDL)',wartość=f"{Hw:.1f}",jednostka='m',osm_id='relation/11022876',url_źródła=U_BDL,licencja=L_BDL,autor='BULiGL / PGL LP',status='SOURCED',uwagi=f"zakres 3–31 m; wiek średni ważony {Aw:.0f} lat (6–162); opis taksacyjny (StandDescriptionData), stan 2026")
for r in lp:
    if r['area_type']!='D-STAN' or not near(r) or not r['sklad']: continue
    dn=', '.join(f"{k[2:]} {r[k]} m" for k in ('d_D303','d_MICK','d_CIOL','d_AERO') if int(r[k])<=80)
    add(kategoria='gatunek',element=f"BDL {' '.join(r['adr_for'].split())} (K1/K2, LP)",parametr='skład: udział·gatunek(wiek [lat], H [m], pierśnica [cm])',wartość=r['sklad'],jednostka='—',osm_id='',lat=r['lat'],lon=r['lon'],url_źródła=f"https://www.bdl.lasy.gov.pl/portal/BULiGL.BDL.Reports/Map/StandDescriptionData?arodesIntNum={r['a_i_num']}&aYear={r['a_year']}&adressForest={urllib.parse.quote(r['adr_for'])}&jointOwnership=false&label=owner_cat_name",licencja=L_BDL,autor='BULiGL / PGL LP',status='SOURCED',
        uwagi=f"gat. panujący {r['gat_pan']}, {r['wiek']} lat, H {r['H_gat_pan_m']} m, bonitacja {r['bonitacja']}; pow. {r['pow_ha']} ha; siedlisko {r['siedlisko']}; zwarcie (kod BDL) {r['zwarcie']}; zadrzewienie {r['zadrzewienie']}; podszyt pokrycie {r['podszyt_pokrycie'] or 'brak'}: {r['podszyt_gat'] or '—'}; odległość wydzielenia od: {dn}")
nl=list(csv.DictReader(open(f'{S}/bdl_poza_lp.csv',encoding='utf-8')))
for r in nl:
    if r['wlasnosc']=='prywatne' or not near(r): continue
    dn=', '.join(f"{k[2:]} {r[k]} m" for k in ('d_D303','d_MICK','d_CIOL','d_AERO') if int(r[k])<=80)
    add(kategoria='gatunek',element=f"BDL {' '.join(r['adr_for'].split())} (poza LP, {r['wlasnosc']})",parametr='skład: udział·gatunek(wiek [lat], H [m], pierśnica [cm])',wartość=r['sklad'] or 'brak warstwy drzew w opisie',jednostka='—',lat=r['lat'],lon=r['lon'],url_źródła='https://mapserver.bdl.lasy.gov.pl/ArcGIS/rest/services/WMS_BDL_kat_wlasnosci/MapServer/6',licencja=L_BDL,autor='BULiGL (PUL lasów niepaństwowych)',status='SOURCED',
        uwagi=f"opis taksacyjny: StandDescriptionData arodesIntNum={r['a_i_num']}; własność: {r['wlasnosc']}; stan {r['a_year']}; pow. {r['pow_ha']} ha; siedlisko {r['siedlisko']}; zwarcie {r['zwarcie']}; zadrzewienie {r['zadrzewienie']}; podszyt pokrycie {r['podszyt_pokrycie'] or 'brak'}: {r['podszyt_gat'] or '—'}; odległość od: {dn}; OL.S olsza szara, OS osika, TP topola, CZM czeremcha, IWA wierzba iwa, GB grab, KL klon")
# ---------------- C/D. wysokość i krawędź z CHM ----------------
seg=list(csv.DictReader(open(f'{S}/chm_edges.csv',encoding='utf-8')))
NM={'D303':'ul. Dywizjonu 303','MICK':'ul. Mickiewicza','CIOL':'ul. Ciołkowskiego','AERO':'granica lotniska'}
for r in seg:
    if int(r['dlugosc_m'])<50: continue
    el=f"{NM[r['obiekt']]}, strona {r['strona_drogi']}: {r['wydzielenie']}"
    add(kategoria='wysokość',element=el,parametr='CHM (NMPT−NMT) pas 0–30 m od ściany lasu: p90',wartość=r['h30_p90'],jednostka='m',osm_id=r['osm'],lat=r['lat'],lon=r['lon'],kierunek_deg=r['azymut_normalnej'],url_źródła=U_NMPT,licencja=L_GUG,autor='GUGiK; obliczenia własne',status='ESTIMATED',
        uwagi=f"p50={r['h30_p50']} m; p10={r['h30_p10']} m; max={r['h30_max']} m; pas 0–5 m: p50={r['h5_p50']} m, p90={r['h5_p90']} m; odcinek {r['dlugosc_m']} m ({r['n_stacji']} profili co 10 m, próbka co 0,5 m); NMPT ulistniony 2023-09-15; ten sam pas z NMPT bezlistnego 2025-04-18 (WCS, 1 m): p50={r['h30_bezlistny_p50']} m, p90={r['h30_bezlistny_p90']} m; PTLZ {r['ptlz_id']} ({r['ptlz_kat']}); kierunek_deg = azymut normalnej od osi ku lasowi; ~ przed adresem BDL = najbliższe wydzielenie ≤40 m")
    add(kategoria='krawędź',element=el,parametr='odległość osi drogi/granicy lotniska → ściana lasu (okap koron ≥5 m): mediana',wartość=r['d_sciany_p50'],jednostka='m',osm_id=r['osm'],lat=r['lat'],lon=r['lon'],kierunek_deg=r['azymut_normalnej'],odległość_od_krawędzi_m=r['d_sciany_p50'],url_źródła=U_NMPT,licencja=L_GUG,autor='GUGiK; obliczenia własne',status='ESTIMATED',
        uwagi=f"p10={r['d_sciany_p10']} m, p90={r['d_sciany_p90']} m; płaszcz (ciągła roślinność ≥1 m tuż przed ścianą): szer. mediana {r['plaszcz_szer_p50']} m, p75 {r['plaszcz_szer_p75']} m, udział profili z płaszczem ≥2 m: {r['plaszcz_udzial_ge2m']}, wys. płaszcza (p90 w profilu, mediana) {r['plaszcz_h90_p50'] or '—'} m; narastanie wysokości od okapu do 0,8·p90: mediana {r['narastanie_p50']} m, p90 {float(r['narastanie_p90']):.1f} m; odcinek {r['dlugosc_m']} m; NMPT 2023-09-15; podszytu pod zwartym okapem NMPT nie widzi")
pm=json.load(open(f'{S}/chm_profile_mean.json'))
for d in (-10,-5,-2,-1,0,1,2,3,5,8,12,20):
    i=pm['d_rel_m'].index(float(d))
    add(kategoria='krawędź',element='profil poprzeczny ściany lasu — wszystkie odcinki łącznie',parametr=f"CHM w odległości {d:+d} m od okapu (− = przed lasem): mediana",wartość=pm['p50'][i],jednostka='m',url_źródła=U_NMPT,licencja=L_GUG,autor='GUGiK; obliczenia własne',status='ESTIMATED',uwagi=f"p25={pm['p25'][i]} m, p75={pm['p75'][i]} m; n={pm['n']} profili (Mickiewicza, Ciołkowskiego, Dyw. 303, lotnisko); data/chm_profile_mean.json; NMPT 2023-09-15")
# ---------------- E. horyzont (odległości) ----------------
hd=json.load(open(f'{S}/horizon_dist.json'))
for k,v in hd.items():
    nm={'D303':'ul. Dywizjonu 303','KUR':'ul. Kuronia','MICK':'ul. Mickiewicza','CIOL':'ul. Ciołkowskiego'}[k]
    add(kategoria='horyzont',element=nm,parametr='odległość z osi drogi do najbliższego lasu (PTLZ rodzaj=las ≥1 ha): mediana',wartość=v['d_p50'],jednostka='m',url_źródła=U_BDOT,licencja=L_GUG,autor='GUGiK; OSM; obliczenia własne',status='ESTIMATED',
        uwagi=f"p10={v['d_p10']} m, p90={v['d_p90']} m, max={v['d_max']} m; udział długości drogi z lasem ≤30 m: {v['udzial_le30m']}; >200 m: {v['udzial_gt200m']}; kierunek do najbliższego lasu (liczba stacji co 20 m): {v['kierunek_najblizszego_lasu']}; tools/horizon.py")
# ---------------- F. kadry ----------------
pp={('PX%02d'%r['n']):r for r in json.load(open(f'{S}/pano_pick.json'))}
cw={('C'+str(r['pageid'])):r for r in json.load(open(f'{S}/commons_want.json'))}
geo=json.load(open(f'{S}/frame_geo.json'))
files=[]
def turl(u,w=1280):
    base,name=u.rsplit('/',1); return base.replace('/commons/','/commons/thumb/')+'/'+name+f'/{w}px-'+name
frame_row={}
for k,d in FD.F.items():
    g=geo.get(k,{})
    if k.startswith('PX'):
        p=pp[k]; fn=f'{S}/dl/{k}.jpg'; sh=sha256(fn)
        dt=p['datetime']; hh=int(dt[11:13])
        base=dict(lat=round(p['lat'],6),lon=round(p['lon'],6),kierunek_deg=p['geom_azimuth'],data_zdjęcia=dt[:10],sezon='lato',pora_dnia='południe' if hh<15 else 'późne popołudnie',
            url_źródła=f"https://api.panoramax.xyz/api/collections/{p['collection']}/items/{p['id']}",licencja='CC BY-SA 4.0 — referencja, nie tekstura',autor=f"{p['producer']} (Panoramax)",url_pliku=p['url'],sha256=sh)
        note=f"Panoramax item {p['id']}; kierunek = azymut geometryczny z sąsiednich pozycji sekwencji (kamera patrzy w przód — potwierdzone obrazem); view:azimuth API={p['view_azimuth']}°, EXIF GPSImgDirection={p['exif_dir']} ref={p['exif_ref']} (magnetyczny — nieużyty); plik {os.path.getsize(fn)} B 2560×1920 — pomniejszyć do ≤1600 px; Podlasie, DK19 poza obszarem Krywlan"
        files.append(dict(id=k,url_pliku=p['url'],sha256=sh,sha1='',bytes=os.path.getsize(fn),url_miniatury='',sha256_miniatury=''))
    else:
        c=cw[k]; tf=f'{S}/thumb/{k}.jpg'; tsh=sha256(tf); of=f'{S}/orig/{k}.jpg'; osh=sha256(of) if os.path.exists(of) else ''
        dt=c['date'] or ''; hh=int(dt[11:13]) if len(dt)>12 else None; mm=int(dt[5:7]) if dt else 0
        sez={12:'zima',1:'zima',2:'zima',3:'przedwiośnie',4:'wiosna (bezlistnie)',5:'wiosna',6:'lato',7:'lato',8:'lato',9:'jesień',10:'jesień',11:'jesień'}.get(mm,'')
        pora='' if hh is None else ('rano' if hh<10 else 'południe' if hh<15 else 'późne popołudnie' if hh<19 else 'wieczór')
        kier=d.get('kier',('UNVERIFIED','—'))
        page='https://commons.wikimedia.org/wiki/'+urllib.parse.quote(c['title'].replace(' ','_'))
        base=dict(lat=round(c['lat'],6),lon=round(c['lon'],6),kierunek_deg=kier[0],data_zdjęcia=dt[:10],sezon=sez,pora_dnia=pora,url_źródła=page,licencja=d.get('lic',c['lic']+(' — referencja, nie tekstura' if 'SA' in c['lic'] else '')),autor=c['artist'],url_pliku=c['url'],sha256=osh)
        note=f"kierunek: {kier[1]}; geotag z Commons (pozycja aparatu, dokładność nieznana); "+("oryginał pobrany, " if osh else "ORYGINAŁ NIEPOBRANY (upload.wikimedia.org HTTP 429, retry-after 600 s) — ")+f"sha1 oryginału wg API Commons={c['sha1']} ({c['size']} B, {c['w']}×{c['h']}); obejrzano miniaturę 1280 px: {turl(c['url'])} sha256={tsh}"
        files.append(dict(id=k,url_pliku=c['url'],sha256=osh,sha1=c['sha1'],bytes=c['size'],url_miniatury=turl(c['url']),sha256_miniatury=tsh))
    pl=d['plaszcz']
    r=add(kategoria='kadr',element=d['el'],parametr='kadr: '+d['typ'],wartość=k,jednostka='—',odległość_od_krawędzi_m=g.get('d_m',''),opis_co_widać=d['opis'],status='SOURCED',
        uwagi=f"gatunek z kadru: {d['gat']}; wysokość ESTIMATED: {(d['H'][0]+' m — '+d['H'][1]) if d['H'] else 'nie szacowano'}; płaszcz/podszyt: {pl[1]}; najbliższy PTLZ las/zagajnik: {g.get('ptlz_id','')} ({g.get('ptlz','')}, {g.get('ptlz_ha','')} ha) {g.get('d_m','')} m od geotagu"+('' if g.get('d_m',999)<=80 else ' — >80 m: kadr horyzontu, nie skraju')+"; "+note,**base)
    frame_row[k]=r['id']
    if d['typ']=='krawędź' and d['H']:
        add(kategoria='krawędź',element=d['el'],parametr='wysokość ściany lasu z kadru',wartość=d['H'][0],jednostka='m',lat=base['lat'],lon=base['lon'],kierunek_deg=base['kierunek_deg'],data_zdjęcia=base['data_zdjęcia'],sezon=base['sezon'],pora_dnia=base['pora_dnia'],url_źródła=base['url_źródła'],licencja=base['licencja'],autor=base['autor'],status='ESTIMATED',uwagi=f"kadr {r['id']} ({k}); metoda: {d['H'][1]}")
        if pl[0] not in (None,'—'):
            add(kategoria='krawędź',element=d['el'],parametr='szerokość płaszcza krzewów/młodnika z kadru',wartość=pl[0],jednostka='m',lat=base['lat'],lon=base['lon'],kierunek_deg=base['kierunek_deg'],data_zdjęcia=base['data_zdjęcia'],sezon=base['sezon'],pora_dnia=base['pora_dnia'],url_źródła=base['url_źródła'],licencja=base['licencja'],autor=base['autor'],status='ESTIMATED',uwagi=f"kadr {r['id']} ({k}); {pl[1]}; szerokość oceniana wzrokowo w proporcji do szerokości pasa ruchu (~3,5 m) / chodnika (~2 m); ±50 %")
    if d['typ']=='horyzont':
        add(kategoria='horyzont',element=d['el'],parametr='kształt i ton linii lasu na horyzoncie',wartość={'C136151985':'ciągła, gładka, łagodnie falista; ciemna, z jaśniejszym pasem zarośli u podstawy','C136151967':'ciągła, równa, cienka, ciemna','C136151968':'brak ściany lasu; cienka linia drzew','C94000344':'niska, cienka, przerywana kępami','PX30':'osobne zwarte bryły, górna linia falista drobno ząbkowana; ciemna','PX40':'ciągła, ciemna, drobno ząbkowana (wierzchołki świerków)'}[k],jednostka='opis',lat=base['lat'],lon=base['lon'],kierunek_deg=base['kierunek_deg'],data_zdjęcia=base['data_zdjęcia'],sezon=base['sezon'],pora_dnia=base['pora_dnia'],url_źródła=base['url_źródła'],licencja=base['licencja'],autor=base['autor'],status='ESTIMATED',uwagi=f"kadr {r['id']} ({k}); ocena wzrokowa")
add(kategoria='horyzont',element='Dywizjonu 303 — kadr P11-056',parametr='stosunek wysokości linii lasu do widocznych budynków',wartość='UNVERIFIED',jednostka='—',lat=53.104182,lon=23.176891,url_źródła='https://commons.wikimedia.org/wiki/File:20230814_175724_August_2023_in_Bia%C5%82ystok.jpg',licencja='CC0',autor='Rakoon',status='UNVERIFIED',uwagi=f"kadr {frame_row['C136151985']}: w kadrze nie ma budynku na tle lasu — nad linię drzew wystaje tylko cienka wieża i widać czerwone dachy poniżej linii koron; ilościowego stosunku nie da się odczytać. Jakościowo: linia lasu wyżej niż dachy zabudowy niskiej")
w=csv.DictWriter(open(f'{OUT}/manifest.csv','w',newline='',encoding='utf-8'),fieldnames=COLS,lineterminator='\n'); w.writeheader(); w.writerows(rows)
w=csv.DictWriter(open(f'{OUT}/files_index.csv','w',newline='',encoding='utf-8'),fieldnames=list(files[0].keys()),lineterminator='\n'); w.writeheader(); w.writerows(files)
json.dump(FD.REJECTED,open(f'{OUT}/data/rejected_frames.json','w'),ensure_ascii=False,indent=1)
print(len(rows),collections.Counter(r['kategoria'] for r in rows),collections.Counter(r['status'] for r in rows),len(files),sum(int(f['bytes']) for f in files))
