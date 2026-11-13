"""Buduje manifest.csv G10 z lokalnego PBF (odczyt) + ustalen ze zrodel.
Uruchom: python -I build_g10.py <osm_all.json> <named.json> <out_dir>
osm_all.json / named.json: ekstrakty z Data/raw/osm/podlaskie-261108.osm.pbf (patrz files/osm_truck_tags_bialystok.csv)."""
import json, csv, sys, collections

osm_all = json.load(open(sys.argv[1], encoding='utf-8'))
named = json.load(open(sys.argv[2], encoding='utf-8'))
out = sys.argv[3]
O = {x['id']: x for x in osm_all}


def pos(ids):
    pts = [(O[i]['lat'], O[i]['lon']) for i in ids if i in O]
    if not pts:
        return ('', '')
    return (round(sum(p[0] for p in pts) / len(pts), 6), round(sum(p[1] for p in pts) / len(pts), 6))


def tagstr(ids, keys):
    c = collections.Counter(json.dumps({k: v for k, v in O[i]['tags'].items() if k in keys}, ensure_ascii=False, sort_keys=True) for i in ids if i in O)
    return ' | '.join(f'{k} x{n}' for k, n in c.most_common())


ACC = '2026-11-13'
OSMSRC = 'Data/raw/osm/podlaskie-261108.osm.pbf (Geofabrik, odczyt lokalny; ekstrakt files/osm_truck_tags_bialystok.csv)'
BJ = 'https://www.bialystok.pl/pl/wiadomosci/aktualnosci/zmiany-w-ruchu-wokol-ulicy-suchowolca.html'
BJ2 = 'https://www.bialystok.pl/pl/wiadomosci/utrudnienia-w-ruchu-na-wlotach-skrzyzowan-ulic.html'
JARD = 'https://radio.jard.pl/zmiany-w-organizacji-ruchu-w-bialymstoku-ciezarowki-pojada-nowa-trasa/'
U794 = 'https://www.bip.bialystok.pl/resource/file/download-file/id.45342'
ODBL = 'ODbL 1.0 (c) OpenStreetMap contributors'
OSMA = 'społeczność OSM'

doj = [x['id'] for x in named if x['name'] == 'Dojlidy Fabryczne' and x['tags'].get('maxweight') == '3.5']
suc = [221207573, 221207572, 210488455, 279864419, 279864415]
mey = [701419770, 548181621, 548181626, 665619503, 987107368, 432917764]
mick = [x['id'] for x in named if x['name'] == 'Adama Mickiewicza' and x['tags'].get('maxweight') == '8']
mil = [23982073, 216687044, 216687045, 1329465434, 237966280, 236771601, 614205245]
bran = [i for i, x in O.items() if x['name'] == 'Jana Klemensa Branickiego' and x['tags'].get('maxweight') == '8']
zwi = [i for i, x in O.items() if x['name'] == 'Zwierzyniecka' and x['tags'].get('maxweight') == '8']
niew = [i for i, x in O.items() if x['name'] == 'Niewodnicka' and x['tags'].get('maxweight') == '15']
axl10 = [i for i, x in O.items() if x['tags'].get('maxaxleload') == '10' and x['name'] in ('Szosa Knyszyńska', 'Szosa Ełcka', 'Ełcka')]
dg = [i for i, x in O.items() if x['tags'].get('maxweight') == '3.5' and x['tags'].get('hgv') == 'no' and x['hw'] in ('residential', 'unclassified', 'tertiary', 'living_street') and 53.105 < x['lat'] < 53.119 and 23.184 < x['lon'] < 23.2005]
mh = [257367425, 257367428, 175157471, 237915062, 615607647, 893929329, 194922744, 237917983, 264107049, 264107054, 249640396, 263729763]
axl = [i for i, x in O.items() if x['tags'].get('maxaxleload') == '11.5' and 53.147 < x['lat'] < 53.168 and 23.14 < x['lon'] < 23.176]
tollS8 = [i for i, x in O.items() if 'toll:hgv' in x['tags']]
hgvyes = [238234008, 665624262, 751949264, 188180420]
trk = [x['id'] for x in named if x['name'] == 'Jacka Kuronia'][:6]

cols = ['id', 'ulica', 'odcinek_od_do', 'lat', 'lon', 'ograniczenie', 'wartość', 'godziny', 'podstawa_prawna', 'znak_mapillary_key', 'osm_way_id', 'osm_tag_obecny', 'zgodne_z_OSM', 'url_źródła', 'licencja', 'autor', 'data_dostępu', 'status', 'uwagi']
R = []


def row(**k):
    k.setdefault('znak_mapillary_key', 'BRAK (Mapillary API niedostępne bez tokenu; patrz README)')
    k.setdefault('godziny', 'UNVERIFIED (brak informacji w źródle)')
    k.setdefault('autor', '')
    k.setdefault('data_dostępu', ACC)
    k['id'] = f'G10-{len(R) + 1:03d}'
    la, lo = k.pop('pos', ('', ''))
    k['lat'], k['lon'] = la, lo
    R.append({c: k.get(c, '') for c in cols})


NEWS = 'Artykuł prasowy/portal — tylko referencja, nie pobrano'
OFF = 'Dokument/komunikat urzędowy (art. 4 pkt 2 pr. aut.; numer pkt UNVERIFIED)'

row(ulica='Dojlidy Fabryczne', odcinek_od_do='rondo Meyera (Nowowarszawska) → Ks. S. Suchowolca (część zakazu Meyera–Plażowa)', pos=pos(doj),
    ograniczenie='Zakaz wjazdu pojazdów ciężarowych > 3,5 t (tranzyt przeniesiony na Kuronia–Dywizjonu 303–Ciołkowskiego)', wartość='3,5 t',
    godziny='UNVERIFIED (brak godzin w komunikatach; wyjątki dostaw nieznane)',
    podstawa_prawna='Stała organizacja ruchu ZDM Białystok (nr zatwierdzenia UNVERIFIED); znak B-5 lub B-18 UNVERIFIED',
    osm_way_id=';'.join(map(str, doj)), osm_tag_obecny=tagstr(doj, ('maxweight', 'hgv', 'maxaxleload')), zgodne_z_OSM='TAK',
    url_źródła=BJ + ' ; ' + BJ2, licencja=OFF + ' (portal UM Białystok)', autor='UM Białystok / ZDM', status='SOURCED',
    uwagi='Komunikat 2025-11-19/21; bialystokonline 2025-11-20: "przekierowanie ruchu ciężarowego powyżej 3,5 tony". Znaki ciężarowe w późniejszym etapie; data 1 I 2026 tylko z podsumowania wyszukiwarki (Poranny, nie pobrano) = UNVERIFIED. hgv=no + maxweight=3.5 w OSM blokuje też dostawy; wyjątki UNVERIFIED.')
row(ulica='Ks. Stanisława Suchowolca', odcinek_od_do='Dojlidy Fabryczne → skrzyżowanie Plażowa/Kuronia (tag OSM kończy się na węźle Plażowa/Kuronia)', pos=pos(suc),
    ograniczenie='Zakaz wjazdu pojazdów ciężarowych > 3,5 t', wartość='3,5 t', podstawa_prawna='Jak G10-001',
    osm_way_id=';'.join(map(str, suc)), osm_tag_obecny=tagstr(suc, ('maxweight', 'hgv')), zgodne_z_OSM='TAK', url_źródła=BJ2, licencja=OFF,
    autor='UM Białystok / ZDM', status='SOURCED',
    uwagi='Komunikat 2025-12-01 (wymiana tablic 2-5 XII 2025) podaje zakres "między Plażową a Ciołkowskiego"; prasa: "między rondem Meyera a Plażową". Sprzeczny opis zakresu = UNVERIFIED; OSM zgadza się z wariantem Meyera–Plażowa.')
row(ulica='Rondo A.B. Meyera / Nowowarszawska (DK19)', odcinek_od_do='ramiona ronda i dojazd Nowowarszawska', pos=pos(mey),
    ograniczenie='Tag 3,5 t / hgv=no na ramionach ronda; źródło urzędowe nie wymienia ronda wprost', wartość='3,5 t', podstawa_prawna='UNVERIFIED',
    osm_way_id=';'.join(map(str, mey)), osm_tag_obecny=tagstr(mey, ('maxweight', 'hgv')), zgodne_z_OSM='BRAK', url_źródła=BJ, licencja=OFF,
    autor='UM Białystok', status='UNVERIFIED',
    uwagi='Komunikat opisuje zmiany pasów na rondzie, nie zakaz. Ryzyko: hgv=no na samym rondzie odcina trasę ciężarówek, jeśli znak stoi dopiero za rondem.')
row(ulica='Jacka Kuronia – Dywizjonu 303 – Konstantego Ciołkowskiego', odcinek_od_do='ciąg wyznaczony dla ruchu ciężarowego > 3,5 t jako objazd Dojlid', pos=(53.1062, 23.1923),
    ograniczenie='Trasa wyznaczona dla tranzytu ciężarowego (nie zakaz)', wartość='trasa', podstawa_prawna='Organizacja ruchu (UM Białystok); akt UNVERIFIED',
    osm_way_id=';'.join(map(str, trk)) + ' (Kuronia, próbka)', osm_tag_obecny='highway=trunk, bez hgv=designated (Kuronia)', zgodne_z_OSM='BRAK',
    url_źródła=JARD + ' ; ' + BJ2, licencja=NEWS + ' / ' + OFF, autor='Radio JARD za UM Białystok 2025-11-24', status='SOURCED',
    uwagi='Cytat: "skierować je na ciąg Kuronia–Dywizjonu 303–Ciołkowskiego". Klasa trunk w OSM jest zgodna. Podpowiedź routingu = authored override, nie ograniczenie.')
row(ulica='Adama Mickiewicza', odcinek_od_do='Jacka Kuronia → Konstantego Ciołkowskiego (OSM: od węzła Kuronia do węzła Ciołkowskiego; 2 krótkie way bez tagu: 671082729, 616184918)', pos=pos(mick),
    ograniczenie='Zakaz wjazdu pojazdów > 8 t', wartość='8 t',
    podstawa_prawna='Organizacja ruchu ZDM Białystok 2025 (nr UNVERIFIED); znak B-18 lub B-5 z tabliczką UNVERIFIED',
    osm_way_id=';'.join(map(str, mick)), osm_tag_obecny='maxweight=8 x%d' % len(mick), zgodne_z_OSM='TAK', url_źródła=JARD + ' ; ' + BJ,
    licencja=NEWS + ' / ' + OFF, autor='UM Białystok', status='SOURCED',
    uwagi='Cytat: "zakaz wjazdu pojazdów ciężarowych powyżej 8 ton" (Radio JARD 2025-11-24). 2 krótkie way bez tagu = luka lub łącznik.')
row(ulica='Czesława Miłosza / Branickiego (odcinek północny) / B. Chrobrego / Nowowarszawska (osiedlowa)', odcinek_od_do='rejon 53,124–53,129 N, 23,181–23,189 E', pos=pos(mil),
    ograniczenie='OSM: hgv=no + maxgvweightrating:hgv 8 t (3,5 t na Nowowarszawskiej osiedlowej), wyjątek "none @ delivery"', wartość='8 t / 3,5 t',
    podstawa_prawna='UNVERIFIED — brak źródła urzędowego', osm_way_id=';'.join(map(str, mil)),
    osm_tag_obecny=tagstr(mil, ('hgv', 'maxgvweightrating:hgv', 'maxgvweightrating:hgv:conditional', 'maxweight')), zgodne_z_OSM='BRAK', url_źródła=OSMSRC,
    licencja=ODBL, autor=OSMA, status='UNVERIFIED',
    uwagi='Tylko OSM (edycje do 2026-06-29). Klucz maxgvweightrating:hgv NIE jest czytany przez build_route_graph (czyta maxweight:hgv / maxweight); hgv=no jest czytane, więc krawędzie są blokowane bez wyjątku dostaw.')
row(ulica='Jana Klemensa Branickiego', odcinek_od_do='cała ulica (%d way z maxweight=8)' % len(bran), pos=pos(bran),
    ograniczenie='Plan 2018: klasa 12 t (zielona); OSM: 8 t', wartość='OSM 8 t vs plan 2018 12 t',
    podstawa_prawna='Plan ograniczeń ruchu pojazdów ciężarowych (UM Białystok), załącznik do uchw. LI/794/18, rys. 1-7, s. 23',
    osm_way_id=';'.join(map(str, bran)), osm_tag_obecny='maxweight=8', zgodne_z_OSM='NIE', url_źródła=U794, licencja=OFF, autor='UM Białystok', status='UNVERIFIED',
    uwagi='Rozbieżność wartości; plan z 2018 mógł się zdezaktualizować (zaostrzenie po 2018 możliwe). Wymaga zdjęcia znaku lub aktualnego projektu organizacji ruchu.')
row(ulica='Zwierzyniecka', odcinek_od_do='%d way z maxweight=8' % len(zwi), pos=pos(zwi),
    ograniczenie='Plan 2018: 12 t (zielona); OSM: 8 t', wartość='OSM 8 t vs plan 2018 12 t', podstawa_prawna='Jak G10-007',
    osm_way_id=';'.join(map(str, zwi)), osm_tag_obecny='maxweight=8', zgodne_z_OSM='NIE', url_źródła=U794, licencja=OFF, autor='UM Białystok', status='UNVERIFIED', uwagi='Jak G10-007.')
row(ulica='Warszawska', odcinek_od_do='way 842154286 (53,127 N 23,183 E); way 178218020 i 1307309377 tylko goods=delivery', pos=pos([842154286]),
    ograniczenie='OSM: maxweight="12 t", hgv=no, goods=delivery — tagi sprzeczne', wartość='12 t / hgv=no', podstawa_prawna='UNVERIFIED',
    osm_way_id='842154286;178218020;1307309377', osm_tag_obecny=tagstr([842154286], ('maxweight', 'hgv', 'goods')), zgodne_z_OSM='NIE', url_źródła=OSMSRC,
    licencja=ODBL, autor=OSMA, status='UNVERIFIED',
    uwagi='hgv=no (> 3,5 t zakazane) i maxweight 12 t nie mogą opisywać tego samego znaku. KRTG: flaga no-truck zablokuje krawędź. Do sprawdzenia w terenie.')
row(ulica='Śródmieście (strefa żółta planu: ulice wewnątrz obwodnicy śródmiejskiej)', odcinek_od_do='rejon rynek Kościuszki / Lipowa / Sienkiewicza — nazwy UNVERIFIED (mapa, nazwy częściowo nieczytelne)', pos=(53.1325, 23.1590),
    ograniczenie='Plan 2018: ulice centrum w klasie 3,5 t (żółta)', wartość='3,5 t',
    podstawa_prawna='Plan UM, załącznik do uchw. LI/794/18, s. 23; tekst s. 22: "pow. 3.5 t, z wyłączeniem niezbędnych dostaw"',
    osm_way_id='BRAK', osm_tag_obecny='praktycznie brak tagów hgv/maxweight w centrum (patrz csv)', zgodne_z_OSM='BRAK', url_źródła=U794, licencja=OFF, autor='UM Białystok', status='SOURCED',
    uwagi='Stan 2018. Strefa poza kaflem gry i poza trasą S8/DK8/DK19; ważna przy dostawach do centrum.')
row(ulica='Gen. W. Andersa, Gen. S. Maczka, Al. Tysiąclecia P.P., Wasilkowska, K. Ciołkowskiego, S8/DK8/DK19/DK65', odcinek_od_do='kafel Putry/Andersa i dojazdy', pos=(53.1560, 23.1560),
    ograniczenie='Plan 2018: klasa 40 t dla wszystkich (czerwona) = brak ograniczenia tonażowego poza ogólnokrajowymi', wartość='brak limitu (40 t)',
    podstawa_prawna='Plan UM s. 23 (legenda "40t dla wszystkich")', osm_way_id='dziesiątki (patrz csv)',
    osm_tag_obecny='brak maxweight/hgv; maxaxleload=11.5 na %d way kafla' % len(axl), zgodne_z_OSM='TAK', url_źródła=U794, licencja=OFF, autor='UM Białystok', status='SOURCED',
    uwagi='Zgodne: główna trasa ciężka bez zakazów. Ścieżka gry Andersa → Putry → S8 bez znanych zakazów tonażowych.')
row(ulica='Rondo Putry, Andersa, Maczka, Al. Tysiąclecia (kafel)', odcinek_od_do='kafel bialystok-industrial-c', pos=pos(axl),
    ograniczenie='maxaxleload=11,5 t (OSM) na %d way kafla' % len(axl), wartość='11,5 t',
    podstawa_prawna='UNVERIFIED (dyrektywa 96/53/WE cytowana w docs jako UNVERIFIED; klasa nośności drogi krajowej)',
    osm_way_id='%d way (lista w csv)' % len(axl), osm_tag_obecny='maxaxleload=11.5', zgodne_z_OSM='TAK', url_źródła=OSMSRC, licencja=ODBL, autor=OSMA, status='UNVERIFIED',
    uwagi='LUKA POTOKU: tools/worldgen/roadgraph.py (whitelist l.34 i l.110) nie przenosi maxaxleload / maxlength / maxweight:hgv / hgv:conditional do roads.graph.json, więc KRTG v2 ma 0 limitów mimo tagów w OSM. Wpływ na grę zerowy (limit = parametr 11,5 t, "równy = dozwolony").')
row(ulica='Rondo Putry; Andersa (wiadukty); ronda Żołnierzy Wyklętych i Wolnej Ukrainy; Sulika; Al. Niepodległości/Paderewskiego', odcinek_od_do='ways z maxheight=default', pos=pos(mh),
    ograniczenie='maxheight=default (brak znaku B-16; limit ustawowy 4,0 m z ładunkiem)', wartość='4,0 m (ustawowy)',
    podstawa_prawna='Prawo o ruchu drogowym art. 61 ust. 10 (t.j. Dz.U. 2024 poz. 1251): pojazd z ładunkiem maksymalnie 4 m',
    osm_way_id=';'.join(map(str, mh)), osm_tag_obecny='maxheight=default', zgodne_z_OSM='TAK', url_źródła='https://api.sejm.gov.pl/eli/acts/DU/2024/1251/text.html',
    licencja='Akt prawny (art. 4 pkt 1 pr. aut.)', autor='Sejm RP', status='SOURCED',
    uwagi='Rzeczywista skrajnia pionowa pod wiaduktem Putry UNVERIFIED; "default" jest parsowane jako brak limitu (poprawnie). Brak znaków B-16 na sprawdzonym zdjęciu Mapillary (patrz README).')
row(ulica='Bitwy Białostockiej', odcinek_od_do='way 178208423 (droga w kaflu)', pos=pos([178208423]),
    ograniczenie='OSM: hgv=no, goods=delivery', wartość='hgv=no (> 3,5 t)', podstawa_prawna='UNVERIFIED',
    osm_way_id='178208423', osm_tag_obecny=tagstr([178208423], ('hgv', 'goods')), zgodne_z_OSM='BRAK',
    url_źródła=OSMSRC + ' ; https://www.radio.bialystok.pl/wiadomosci/index/id/203883', licencja=ODBL, autor=OSMA, status='UNVERIFIED',
    uwagi='Jedyne źródło: OSM. Znalezione komunikaty UM o Bitwy Białostockiej dotyczą jednokierunkowości drogi dojazdowej (od 2025-11-20), nie zakazu ciężarówek. hgv=no z goods=delivery jest sprzeczne. 6 krawędzi no-truck w KRTG kafla pochodzi m.in. stąd.')
row(ulica='Sokólska', odcinek_od_do='way 188396757 (kafel)', pos=pos([188396757]), ograniczenie='OSM: hgv=no', wartość='hgv=no', podstawa_prawna='UNVERIFIED',
    osm_way_id='188396757', osm_tag_obecny='hgv=no', zgodne_z_OSM='BRAK', url_źródła=OSMSRC, licencja=ODBL, autor=OSMA, status='UNVERIFIED',
    uwagi='Brak źródła urzędowego i zdjęcia znaku; ulica osiedlowa w kaflu. Do weryfikacji fotografią znaku.')
row(ulica='Niewodnicka', odcinek_od_do='%d way, ok. 53,098–53,114 N, 23,060–23,082 E' % len(niew), pos=pos(niew),
    ograniczenie='OSM: maxweight=15, hgv=designated, goods=permissive', wartość='15 t', podstawa_prawna='UNVERIFIED',
    osm_way_id=';'.join(map(str, niew)), osm_tag_obecny=tagstr(niew, ('maxweight', 'hgv', 'goods')), zgodne_z_OSM='BRAK', url_źródła=OSMSRC, licencja=ODBL, autor=OSMA, status='UNVERIFIED',
    uwagi='Zarządca i znak nieustalone; maxweight=15 razem z hgv=designated to prawdopodobnie limit mostu/nawierzchni — UNVERIFIED.')
row(ulica='Szosa Knyszyńska / Szosa Ełcka / Ełcka', odcinek_od_do='NW i N wylot z miasta, %d way' % len(axl10), pos=pos(axl10),
    ograniczenie='OSM: maxaxleload=10 t (nacisk osi)', wartość='10 t < 11,5 t', podstawa_prawna='UNVERIFIED',
    osm_way_id=';'.join(map(str, axl10)), osm_tag_obecny='maxaxleload=10', zgodne_z_OSM='BRAK', url_źródła=OSMSRC, licencja=ODBL, autor=OSMA, status='UNVERIFIED',
    uwagi='RYZYKO DLA ROUTINGU po naprawie luki w roadgraph: limit 10 t < parametr ciężarówki 11,5 t = brak trasy. Nie na trasie gry. Potwierdzić źródło (PZDW nie wymienia ograniczeń dla tych dróg).')
row(ulica='Obrzeża: Żółtkowska, Kościuszki, Łąkowa, Al. Niepodległości (zach.), Topole i in.', odcinek_od_do='38 way maxweight=10 + 15 way 15 t + Topole 24 t', pos=(53.09, 23.05),
    ograniczenie='OSM: maxweight=10 t / 15 t / 24 t (Topole 301984687, hgv=no)', wartość='10/15/24 t', podstawa_prawna='UNVERIFIED',
    osm_way_id='patrz csv (filtr maxweight)', osm_tag_obecny='maxweight=10 (38), 15 (15), 24 (1)', zgodne_z_OSM='BRAK', url_źródła=OSMSRC, licencja=ODBL, autor=OSMA, status='UNVERIFIED',
    uwagi='Drogi powiatowe/gminne i obrzeża; brak potwierdzenia źródłowego.')
row(ulica='Osiedle Dojlidy Górne (Żurawia, Wilcza, Wiewiórcza, Myśliwska, Niedźwiedzia, Sarnia i in.)', odcinek_od_do='53,105–53,119 N, 23,184–23,200 E', pos=pos(dg),
    ograniczenie='OSM: maxweight=3,5 + hgv=no na %d way' % len(dg), wartość='3,5 t',
    podstawa_prawna='UNVERIFIED (prawdopodobnie ten sam pakiet co Dojlidy 2025)',
    osm_way_id=';'.join(map(str, dg[:60])) + (';…' if len(dg) > 60 else ''), osm_tag_obecny='maxweight=3.5; hgv=no', zgodne_z_OSM='BRAK', url_źródła=OSMSRC, licencja=ODBL, autor=OSMA, status='UNVERIFIED',
    uwagi='Wyszukiwanie nie potwierdziło znaków na tych ulicach. Nie na trasie gry; ulice mieszkalne — tag wiarygodny.')
row(ulica='Wasilkowska; rondo Chodakowskiego (DW676)', odcinek_od_do='kilka way', pos=pos(hgvyes), ograniczenie='OSM: hgv=yes (trasa dla HGV)', wartość='hgv=yes', podstawa_prawna='UNVERIFIED',
    osm_way_id=';'.join(map(str, hgvyes)), osm_tag_obecny='hgv=yes; maxaxleload=11.5', zgodne_z_OSM='TAK', url_źródła=OSMSRC, licencja=ODBL, autor=OSMA, status='UNVERIFIED',
    uwagi='Spójne z planem 2018 (Wasilkowska czerwona = 40 t dla wszystkich).')
row(ulica='S8 (Białystok – obwodnica)', odcinek_od_do='%d way motorway z toll:hgv=yes' % len(tollS8), pos=pos(tollS8[:6]),
    ograniczenie='Płatny przejazd pojazdów > 3,5 t (e-TOLL); maxspeed:hgv=80', wartość='opłata; 80 km/h',
    podstawa_prawna='System e-TOLL; Prawo o ruchu drogowym art. 20 — UNVERIFIED szczegóły',
    osm_way_id='%d way (csv)' % len(tollS8), osm_tag_obecny='toll:hgv=yes; maxspeed:hgv=80', zgodne_z_OSM='TAK',
    url_źródła='https://etollbialystok.pl/ ; https://linqo.pl/wiadomosci/mapy-platnych-odcinkow-drog-w-systemie-e-toll/', licencja=NEWS, status='UNVERIFIED',
    uwagi='Oficjalna lista odcinków (etoll.gov.pl) NIE pobrana; status DK8/DK19/DK65 w Białymstoku UNVERIFIED. Opłata nie jest ograniczeniem ruchu — informacja ekonomiczna.')
row(ulica='Cała sieć dróg', odcinek_od_do='Polska', ograniczenie='Zakaz ruchu pojazdów > 12 t w weekendy/święta (wakacje, długie weekendy) z wyjątkami', wartość='12 t DMC',
    godziny='wg rozporządzenia; godziny UNVERIFIED', podstawa_prawna='Rozporządzenie Ministra Infrastruktury (zakazy ruchu wg GITD); numer UNVERIFIED',
    osm_way_id='n/d', osm_tag_obecny='nie mapowane w OSM (słusznie)', zgodne_z_OSM='BRAK', url_źródła='https://www.gov.pl/web/gitd/zakazy-ruchu-dla-ciezarowek',
    licencja=OFF + ' (GITD)', autor='GITD', status='UNVERIFIED',
    uwagi='Strona GITD znaleziona w wynikach wyszukiwania, treści nie pobrano. Dla gry: opcjonalne zdarzenie kalendarzowe, nie dane grafu.')
row(ulica='Cała sieć dróg', odcinek_od_do='Polska', ograniczenie='Wysokość pojazdu z ładunkiem ≤ 4,0 m; szerokość z ładunkiem wg art. 61 ust. 6', wartość='4,0 m',
    podstawa_prawna='Prawo o ruchu drogowym art. 61 ust. 10 (t.j. Dz.U. 2024 poz. 1251)', osm_way_id='n/d', osm_tag_obecny='n/d', zgodne_z_OSM='TAK',
    url_źródła='https://api.sejm.gov.pl/eli/acts/DU/2024/1251/text.html', licencja='Akt prawny (art. 4 pkt 1 pr. aut.)', autor='Sejm RP', status='SOURCED',
    uwagi='Długość zestawu (16,5 / 18,75 m) i masa 40 t NIE zweryfikowane w tej sesji = UNVERIFIED (rozp. o warunkach technicznych pojazdów; ELI 2016/2022 wygasło 2024-04-03, nowa podstawa nieustalona).')
row(ulica='Znaki B-5, B-16, B-18', odcinek_od_do='semantyka', ograniczenie='B-5: DMC > 3,5 t (lub wartość na tabliczce); B-16: wartość na znaku = skrajnia minus 0,5 m; B-18: rzeczywista masa', wartość='n/d',
    podstawa_prawna='Rozporządzenie w sprawie znaków i sygnałów drogowych (Dz.U. 2002 nr 170 poz. 1393; ELI potwierdzony)', osm_way_id='n/d', osm_tag_obecny='n/d', zgodne_z_OSM='BRAK',
    url_źródła='https://api.sejm.gov.pl/eli/acts/DU/2002/1393 ; https://ltesty.pl/znak-zakazu,B-5/ ; https://40ton.net/oznakowanie-wysokosci-wiaduktow-polsce-traktowac-znaki-dochodzi-zlamania-prawa/',
    licencja='Akt prawny; strony komercyjne tylko referencja', status='SOURCED',
    uwagi='Znaczenie znaków z podsumowań wyszukiwarki (pełnych stron nie pobrano). B-16 3,8 m na znaku = skrajnia ok. 4,3 m; maxheight w OSM powinno odpowiadać wartości ze znaku.')
row(ulica='Lokalna ulica osiedlowa w Białymstoku (nazwa nieznana)', odcinek_od_do='n/d', ograniczenie='WSA Białystok II SA/Bk 438/13: nieważność organizacji ruchu z B-18 > 8 t wydanej bez zbadania nośności', wartość='8 t (unieważnione)',
    podstawa_prawna='Wyrok WSA w Białymstoku, sygn. II SA/Bk 438/13', osm_way_id='n/d', osm_tag_obecny='n/d', zgodne_z_OSM='BRAK',
    url_źródła='https://www.rp.pl/samorzad/art5323201-zakaz-wjazdu-dla-ciezarowek-musi-poprzedzac-analiza-techniczna', licencja=NEWS, autor='Rzeczpospolita 2013-10-22', status='SOURCED',
    uwagi='Kontekst prawny: tonażowe B-18 wymagają uzasadnienia technicznego; istotne dla wiarygodności tagów 8 t.')
row(ulica='Drogi wojewódzkie w Białymstoku (DW676, DW678, DW669, DW675)', odcinek_od_do='w granicach miasta', ograniczenie='Tabela ograniczeń tonażowych PZDW: brak pozycji dla Białegostoku (najbliższe: DW671 12/10 t Jasionówka–Tykocin, DW668 most Karwowo 15 t)', wartość='brak',
    podstawa_prawna='Wykaz ograniczeń PZDW Białystok', osm_way_id='n/d', osm_tag_obecny='brak maxweight na tych drogach', zgodne_z_OSM='TAK', url_źródła='https://www.pzdw.bialystok.pl/?page_id=38',
    licencja=OFF, autor='PZDW Białystok', status='SOURCED', uwagi='Odczyt przez streszczenie narzędzia; strona bez daty aktualizacji; wartości innych DW nie przepisane.')
row(ulica='Poleska / Towarowa (wiadukt, obwodnica śródmieścia)', odcinek_od_do='wiadukt Towarowa–Poleska', ograniczenie='Komentarz czytelnika Porannego sugeruje zakaz ciężarówek na pękniętym wiadukcie; brak źródła urzędowego', wartość='UNVERIFIED',
    podstawa_prawna='UNVERIFIED', osm_way_id='BRAK', osm_tag_obecny='BRAK', zgodne_z_OSM='BRAK',
    url_źródła='https://poranny.pl/bialystok-pekniety-most-na-wiadukcie-towarowa-poleska-w-kierunku-centrum-kawalki-betonu-spadaja-na-ulice/ar/13783920', licencja=NEWS, status='UNVERIFIED',
    uwagi='Strona zwróciła 403; informacja tylko z podsumowania wyszukiwarki — niska wiarygodność. Nie używać do overrides.')
row(ulica='Strefa płatnego parkowania (śródmieście); parkingi dla ciężarówek', odcinek_od_do='SPP wg uchwały XVI/258/19 (projekt 2019 pobrany: abonament tylko DMC ≤ 3,5 t)',
    ograniczenie='Brak znalezionych zakazów postoju ciężarówek ani miejskich parkingów TIR; abonament mieszkańca tylko ≤ 3,5 t', wartość='n/d',
    godziny='SPP pn-pt 9:00-17:00 (projekt 2019; aktualne brzmienie UNVERIFIED)', podstawa_prawna='Uchwała Rady Miasta Białystok XVI/258/19 (tekst jednolity 2025 — nie pobrano)',
    osm_way_id='n/d', osm_tag_obecny='n/d', zgodne_z_OSM='BRAK', url_źródła='https://www.bip.bialystok.pl/resource/file/download-file/id.54422', licencja=OFF, autor='Rada Miasta Białystok', status='UNVERIFIED',
    uwagi='Parkingi TIR (komercyjne) to temat zlecenia G2, nie G10.')
row(ulica='Plażowa', odcinek_od_do='północ: 53,123–53,127 N, 23,218 E (hgv=no); 481600106 maxweight=8', pos=pos([595888121, 482709612, 481600106]),
    ograniczenie='OSM: hgv=no (7 way), maxweight=8 (1 way)', wartość='hgv=no / 8 t', podstawa_prawna='UNVERIFIED',
    osm_way_id='595888121;808951897;482709612;482709613;482709614;1308260984;481600106', osm_tag_obecny='hgv=no; maxweight=8', zgodne_z_OSM='BRAK', url_źródła=OSMSRC + ' ; ' + BJ,
    licencja=ODBL, autor=OSMA, status='UNVERIFIED',
    uwagi='Plażowa jest wymieniona w komunikacie o zmianie organizacji ruchu, ale bez zakazu ciężarówek; tag OSM niepotwierdzony.')

with open(out + '/manifest.csv', 'w', encoding='utf-8-sig', newline='') as f:
    w = csv.DictWriter(f, fieldnames=cols)
    w.writeheader()
    w.writerows(R)
print(len(R), collections.Counter(r['status'] for r in R), collections.Counter(r['zgodne_z_OSM'] for r in R), 'dg', len(dg), 'axl', len(axl), 'axl10', len(axl10), 'mick', len(mick), 'bran', len(bran), 'zwi', len(zwi), 'niew', len(niew))
