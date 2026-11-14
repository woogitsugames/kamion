# Buduje manifest.csv z: osm/overpass_raw.json, metadanych Panoramax (pmx1.json), plików w files/, kamer (cams.json).
# Uzycie: python3 -I tools/build_manifest.py <pmx_search.json> <cams.json>
import json,csv,hashlib,math,os,sys
D=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
pmx={x['id'][:8]:x for x in json.load(open(sys.argv[1]))['features']}
cams=json.load(open(sys.argv[2]))
DATE='2026-11-14'
cols='id kategoria przedmiot wartość jednostka status metoda cytat url_źródła url_pliku licencja autor data_dostępu sha256 lat lon kierunek_deg kurs_toru_deg opis_co_widać duplikat_sha256 typ_znaku montaż tło wymiary kamery_kontrolne uwagi'.split()
rows=[]
def add(**k):
    r={c:'' for c in cols}; r.update(k); r['id']=f"R2-{len(rows)+1:03d}"; r['data_dostępu']=DATE; rows.append(r); return r
def brg(a,b):
    la1,lo1,la2,lo2=map(math.radians,(a[0],a[1],b[0],b[1]))
    y=math.sin(lo2-lo1)*math.cos(la2); x=math.cos(la1)*math.sin(la2)-math.sin(la1)*math.cos(la2)*math.cos(lo2-lo1)
    return math.degrees(math.atan2(y,x))%360
def dist(a,b):
    return math.hypot((b[0]-a[0])*111320,(b[1]-a[1])*111320*math.cos(math.radians(a[0])))
def track(x):
    c=x['geometry']['coordinates']
    for l in x['links']:
        if l['rel']=='next': n=l['geometry']['coordinates']; return round(brg((c[1],c[0]),(n[1],n[0])),0)
    for l in x['links']:
        if l['rel']=='prev': n=l['geometry']['coordinates']; return round(brg((n[1],n[0]),(c[1],c[0])),0)
    return 'UNVERIFIED'
def camvis(lat,lon):
    out=[]
    for c in cams:
        d=dist((c['lat'],c['lon']),(lat,lon))
        if d>350: continue
        off=abs((brg((c['lat'],c['lon']),(lat,lon))-c['az']+180)%360-180)
        if off<=c['fov']/2: out.append(f"{c['id']} ({d:.0f} m, {off:.0f}° od osi)")
    return '; '.join(out) or 'żadna (≤350 m i w FOV)'
F=[ # id8, plik, opis
('e11bd6e4','pmx_e11bd6e4.jpg','Jezdnia 2-pasowa w stronę E; bramownica kratowa nad jezdnią z zieloną tablicą-schematem: góra „65 Bobrowniki PL BY / 19 Lublin”, odgałęzienie w prawo „8 E 67 Augustów / 19 Kuźnica PL BY”, trzeci wiersz zaklejony żółtą taśmą; w tle druga bramownica z 2 zielonymi tablicami; po prawej żółta tablica „Objazd / Obowiązuje w dniach 24.04.2019-31.08.2019” i znak „70”; po lewej znak „70”; za barierą po prawej 3 tablice na 2 słupkach: brązowa „↑ 16km Uzdrowisko Supraśl”, białe „Sanktuarium Święta Woda ↗”, „Sanktuarium Miłosierdzia Bożego ↗”'),
('8376e36d','pmx_8376e36d.jpg','Bramownica kratowa (2 słupy kratowe + rygiel kratowy) nad jezdnią; lewa zielona tablica „↑ 65 Bobrowniki PL BY / 19 Lublin ↑”; prawa zielona „8 E 67 Augustów / 19 Kuźnica PL BY ↗”, pod spodem wiersz zaklejony żółtą taśmą; na obu słupach bramownicy niebieskie tablice z 3 strzałkami w górę i symbolem zakazu ciężarówek na lewym pasie; ekran akustyczny po prawej, słup energetyczny kratowy'),
('b27d2652','pmx_b27d2652.jpg','Bramownica kratowa; zielona tablica-schemat (krzyż dróg): góra „65 Bobrowniki PL BY / 19 Lublin”, lewo „8 E 67 Augustów / 19 Kuźnica PL …”, po prawej pole żółte i wiersz zaklejony; na słupach niebieskie tablice „Zmiana organizacji ruchu” z trójkątem ostrzegawczym; żółty znak roboty drogowe; po prawej na 2 słupkach białe tablice z brązowym napisem „← Sanktuarium Święta Woda”, „Sanktuarium Miłosierdzia Bożego →”; piesi i rowerzysta przy ekranie akustycznym'),
('6248550a','pmx_6248550a.jpg','Łuk jezdni przed estakadą; 2 niebieskie tablice ze strzałkami pasów (w lewo; w lewo+prosto) z czarno-żółtą pasiastą tabliczką; 2 niebieskie tablice z symbolem zakazu i „250m”; po prawej biała tablica: pomarańczowa cysterna, niebieskie koło ze strzałkami prosto/w lewo, tabliczka „Nie dotyczy zaopatrzenia”; w tle bramownica z zielonymi tablicami'),
('9f85aac8','pmx_9f85aac8.jpg','Dojazd do ronda pod estakadą; bramownica kratowa z 3 zielonymi tablicami: lewa „← 8 E 67 Augustów / 19 Kuźnica PL BY”; środkowa dwupolowa „↑ 65 Bobrowniki PL BY / 19 Lublin” nad „← 8 E 67 Augustów / 19 Kuźnica PL BY”; prawa mała z żółtym polem, zaklejonym wierszem i strzałką →; znaki pierwszeństwo + ustąp po obu stronach, roboty drogowe, znak ślepej drogi; strzałki na jezdni'),
('03ec4841','pmx_03ec4841.jpg','Wlot na rondo pod estakadą na żółtych słupach; po obu stronach znak pierwszeństwa nad znakiem „ustąp”; strzałki kierunkowe na 3 pasach; autobus miejski na rondzie; małe niebieskie znaki w tle; brak tablic kierunkowych z nazwami'),
('844e35c7','pmx_844e35c7.jpg','Linia zatrzymania przed rondem; wysięgnik sygnalizatora z 3 małymi niebieskimi znakami strzałek nad pasami (w lewo; w lewo+prosto; w prawo); sygnalizatory; po obu stronach „ustąp” nad znakiem ruchu okrężnego; kominy w tle; brak tablic kierunkowych z nazwami'),
('6ded8ec0','pmx_6ded8ec0.jpg','Jezdnia 2-pasowa na N, ekran akustyczny po prawej; po obu stronach jezdni na słupkach czerwone tabliczki „8” „19” nad zieloną „E 67”; po obu stronach zakaz wyprzedzania przez ciężarówki nad „70”; po lewej tył bramownicy kratowej nad przeciwną jezdnią; niebieski znak nakazu ze strzałką na wysepce'),
('9ff60a64','pmx_9ff60a64.jpg','Jezdnia na N; bramownica z pomostem i barierkami rozpięta w poprzek — rygiel sięga nad naszą jezdnię do słupa po prawej; po lewej nad przeciwną jezdnią panele tablicy widziane od tyłu; pod nią tył prostokątnego znaku na 2 słupkach; ekran akustyczny po prawej; brak czytelnych tablic kierunkowych'),
('7196532e','pmx_7196532e.jpg','Jezdnia na N; po lewej tył bramownicy kratowej z tablicą nad przeciwną jezdnią; ekran akustyczny po prawej, las; brak czytelnych tablic kierunkowych'),
('5f92573a','pmx_5f92573a.jpg','Łuk jezdni w lewo, las; po prawej znak końca obszaru zabudowanego (sylwetka przekreślona); dalej po prawej ciemna prostokątna tablica odległości z nagłówkiem numerów dróg i 5 wierszami (na wycinku 3×: Korycin, Suchowola, Augustów, Suwałki, Kaunas; liczby km nieczytelne); po lewej tył znaku'),
('390ca2c2','pmxhd_390ca2c2.jpg','Jezdnia na N, las po obu stronach, latarnie dwuramienne; po lewej tył znaku trójkątnego; brak tablic kierunkowych'),
]
fr={}
for i8,fn,op in F:
    x=pmx[i8]; c=x['geometry']['coordinates']; p=x['properties']
    asset='hd' if fn.startswith('pmxhd') else 'sd'
    sha=hashlib.sha256(open(f'{D}/files/{fn}','rb').read()).hexdigest()
    tr=track(x); az=p.get('view:azimuth')
    uw=f"plik files/{fn}; data zdjęcia {p['datetime']}; oglądany 960 px + wycinki 3×"
    if tr!='UNVERIFIED' and abs((az-tr+180)%360-180)>25: uw+=f"; UWAGA: view:azimuth z API ({az}°) odbiega od kursu toru ({tr:.0f}°) i od obrazu (oś jezdni na wprost) — do gry użyj kursu toru"
    fr[i8]=add(kategoria='kadr',przedmiot=f'Panoramax {x["id"]}',status='SOURCED',metoda='Panoramax API /api/search (bbox); view:azimuth z API; kurs toru = azymut do następnego kadru sekwencji (ESTIMATED)',cytat=f'"view:azimuth": {az}',url_źródła=[l['href'] for l in x['links'] if l['rel']=='self'][0],url_pliku=x['assets'][asset]['href'],licencja='CC BY-SA 4.0',autor=x['providers'][0]['name'],sha256=sha,lat=f'{c[1]:.6f}',lon=f'{c[0]:.6f}',kierunek_deg=az,kurs_toru_deg=tr,opis_co_widać=op,uwagi=uw)
T=[ # kadr, typ, treść, montaż, tło
('e11bd6e4','E-1 (wizualnie; tablica przeddrogowskazowa-schemat)','65 Bobrowniki PL BY | 19 Lublin (na wprost); 8 E 67 Augustów | 19 Kuźnica PL BY (w prawo); 3. wiersz zaklejony (2019)','bramownica kratowa nad jezdnią','zielone; numery krajowe czerwone, E 67 zielone z białą ramką'),
('8376e36d','E-2 ×2 (wizualnie; drogowskazy tablicowe nad pasami)','L: ↑ 65 Bobrowniki PL BY | 19 Lublin; P: 8 E 67 Augustów | 19 Kuźnica PL BY ↗ + wiersz zaklejony (2019)','bramownica kratowa: 2 słupy kratowe + rygiel kratowy','zielone'),
('b27d2652','E-1 (wizualnie; schemat skrzyżowania-krzyż)','65 Bobrowniki PL BY | 19 Lublin (góra); 8 E 67 Augustów | 19 Kuźnica PL … (lewo); pole żółte + wiersz zaklejony (prawo)','bramownica kratowa','zielone'),
('9f85aac8','E-2 ×3 (wizualnie) przed rondem','L: ← 8 E 67 Augustów | 19 Kuźnica PL BY; Ś: ↑ 65 Bobrowniki PL BY | 19 Lublin / ← 8 E 67 Augustów | 19 Kuźnica PL BY; P: pole żółte + zaklejone →','bramownica kratowa','zielone'),
('6ded8ec0','E-15 (wizualnie; numery dróg) ×2 strony + numer trasy E','8 | 19 (czerwone) nad E 67 (zielone)','pojedynczy słupek, po obu stronach jezdni','czerwone / zielone'),
('5f92573a','E-14 (wizualnie; tablica szlaku drogowego)','nagłówek numerów dróg; Korycin, Suchowola, Augustów, Suwałki, Kaunas; km UNVERIFIED (nieczytelne)','słupek(i) po prawej; liczba słupków UNVERIFIED','ciemne (niebieskawe w cieniu) — kolor UNVERIFIED'),
('e11bd6e4','E-22 (wizualnie; drogowskazy do obiektów turystycznych) ×3','↑ 16km Uzdrowisko Supraśl; Sanktuarium Święta Woda ↗; Sanktuarium Miłosierdzia Bożego ↗','2 słupki, 3 tablice jedna pod drugą','górna brązowa z białym napisem; dolne białe z brązowym napisem i piktogramem'),
('b27d2652','E-22 (wizualnie) ×2','← Sanktuarium Święta Woda; Sanktuarium Miłosierdzia Bożego →','2 słupki','białe z brązowym napisem'),
]
for i8,typ,tr,mon,tlo in T:
    f=fr[i8]
    add(kategoria='tablica',przedmiot=tr,status='ESTIMATED',metoda=f'odczyt z kadru {f["id"]} (wycinek 3×); pozycja = pozycja KADRU, tablica leży przed kadrem wzdłuż kursu toru w odległości UNVERIFIED; lico zwrócone przeciwnie do kursu toru',url_źródła=f['url_źródła'],licencja='CC BY-SA 4.0 (referencja, nie tekstura)',autor=f['autor'],lat=f['lat'],lon=f['lon'],kierunek_deg=f['kurs_toru_deg'],kurs_toru_deg=f['kurs_toru_deg'],typ_znaku=typ,montaż=mon,tło=tlo,wymiary='UNVERIFIED (nie zmierzono — przerwano przed krokiem pomiaru)',kamery_kontrolne=camvis(float(f['lat']),float(f['lon'])),uwagi=f'kadr {f["id"]}, stan 2019-08-15; kierunek_deg = kierunek jazdy, dla którego tablica jest przeznaczona; kamery liczone geometrycznie do pozycji kadru (ESTIMATED)')
o=json.load(open(f'{D}/osm/overpass_raw.json')); nodes={e['id']:e for e in o['elements'] if e['type']=='node'}
UO='zapytanie osm/overpass_query.overpassql, 2026-11-14T17:10:40Z, lustro maps.mail.ru; surowy wynik osm/overpass_raw.json'
for e in o['elements']:
    t=e.get('tags',{})
    if e['type']=='way' and any(k.startswith('destination') for k in t):
        n=[nodes[i] for i in e['nodes']]; m=n[len(n)//2]
        dt={k:v for k,v in t.items() if k.startswith('destination')}
        add(kategoria='osm_destination',przedmiot=f"way {e['id']} ({t.get('highway')}; name={t.get('name','brak tagu')}; ref={t.get('ref','brak tagu')})",wartość=json.dumps(dt,ensure_ascii=False),status='SOURCED',metoda=UO,cytat='; '.join(f'{k}={v}' for k,v in dt.items()),url_źródła=f"https://www.openstreetmap.org/way/{e['id']}/history/{e['version']}",licencja='ODbL 1.0',autor='© OpenStreetMap contributors',lat=f"{m['lat']:.6f}",lon=f"{m['lon']:.6f}",kierunek_deg=round(brg((n[0]['lat'],n[0]['lon']),(n[-1]['lat'],n[-1]['lon'])),0),uwagi=f"pozycja = środkowy węzeł way; kierunek = azymut pierwszy→ostatni węzeł (oneway={t.get('oneway')}); tag OSM, nie odczyt fizycznej tablicy; wersja {e['version']} z {e['timestamp']}")
g=nodes[11877183092]
add(kategoria='osm_fakt',przedmiot='man_made=gantry w bbox',wartość=1,jednostka='szt.',status='SOURCED',metoda=UO,cytat='man_made=gantry',url_źródła='https://www.openstreetmap.org/node/11877183092',licencja='ODbL 1.0',autor='© OpenStreetMap contributors',lat=g['lat'],lon=g['lon'],kierunek_deg='UNVERIFIED',uwagi='jedyna bramownica otagowana w OSM; bramownice z kadrów R2-001..R2-005 nie mają tagu („brak tagu”)')
add(kategoria='osm_fakt',przedmiot='węzły traffic_sign=PL:E-* w bbox',wartość=0,jednostka='szt.',status='SOURCED',metoda=UO+'; jedyny traffic_sign w bbox: node 2482696231 PL:B-1',cytat='traffic_sign=PL:B-1',url_źródła='https://www.openstreetmap.org/node/2482696231',licencja='ODbL 1.0',autor='© OpenStreetMap contributors',kierunek_deg='UNVERIFIED',uwagi='brak tagu dla wszystkich tablic E-*; 0 relacji type=destination_sign; 0 highway=motorway_junction')
for nm in ('Rondo Krzysztofa Jakuba Putry Wicemarszałka Sejmu RP','Rondo Pamięci Bieżeństwa 1915 roku'):
    w=[e for e in o['elements'] if e['type']=='way' and e.get('tags',{}).get('name')==nm][0]; n=nodes[w['nodes'][0]]
    add(kategoria='osm_fakt',przedmiot='nazwa ronda w OSM',wartość=nm,status='SOURCED',metoda=UO,cytat=f'name={nm}',url_źródła=f"https://www.openstreetmap.org/way/{w['id']}",licencja='ODbL 1.0',autor='© OpenStreetMap contributors',lat=f"{n['lat']:.6f}",lon=f"{n['lon']:.6f}",kierunek_deg='UNVERIFIED',uwagi='w OSM nie ma ulicy „Bieżeńców/Bieżeństwa” wśród dróg klasy ≥ tertiary w bbox; jest rondo o tej nazwie')
seen={}
for r in rows:
    if r['sha256']:
        if r['sha256'] in seen: r['duplikat_sha256']=seen[r['sha256']]
        else: seen[r['sha256']]=r['id']
w=csv.DictWriter(open(f'{D}/manifest.csv','w',newline='',encoding='utf-8'),fieldnames=cols); w.writeheader(); w.writerows(rows)
print(len(rows))
