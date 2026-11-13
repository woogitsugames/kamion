#!/usr/bin/env python3
"""P12: generator manifest.csv (UTF-8 BOM, RFC 4180, przecinki — konwencja jak G10).

Sekcje (kolumny wspólne):
  landmark (P12-001..039)   — obiekty charakterystyczne widoczne z dróg
  typologia (P12-040..045)  — klasy zabudowy przy drogach (census z LoD1+BDOT10k+ortofoto)
  wyposażenie (P12-046..)   — przystanki/wiaty, bollardy, znaki, latarnie, ekrany, drogowskazy wlotowe
  generator_ruchu (P12-...) — zakłady/magazyny z bramami (pozycja bramy z OSM, jeśli mapowana)

Wejście: data/landmarks.json, data/landmark-colors.json, data/matched-with-roads.json,
         data/road-geom.json, data/region-summary.json, data/osm-pois.json,
         data/typologia.json, data/typologia-colors.json
Wyjście: manifest.csv (obok skryptu: research/mistral/p12-dojlidy-landmarks/manifest.csv)
"""
import csv, json, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
D = lambda n: os.path.join(HERE, '..', 'data', n)
OUT = os.path.join(HERE, '..', 'manifest.csv')

DATA_DOST = '2026-11-13'
OSM_LIC = 'ODbL 1.0 (c) OpenStreetMap contributors'
GUGIK_LIC = 'GUGiK — otwarte dane (PZGiK; ortofoto WMS StandardResolution)'
OSM_AUT = 'społeczność OSM'
GUGIK_AUT = 'GUGiK'
EP = 'https://www.openstreetmap.org/'

L = json.load(open(D('landmarks.json')))
C = {c['id']: c for c in json.load(open(D('landmark-colors.json')))}
MWR = {b['osm_id']: b for b in json.load(open(D('matched-with-roads.json')))}
ROADS = json.load(open(D('road-geom.json')))['roads']
RS = json.load(open(D('region-summary.json')))
POIS = json.load(open(D('osm-pois.json')))
TYP = json.load(open(D('typologia.json')))
TYPC = json.load(open(D('typologia-colors.json')))

# ---------- pomocnicze ----------
def near_road(lat, lon, skip_service=True):
    """najbliższa droga (nazwa, odległość_m) wg geometrii OSM; service tylko awaryjnie"""
    def d_ps(px, py, ax, ay, bx, by):
        dx, dy = bx-ax, by-ay
        t = 0 if (dx*dx+dy*dy) == 0 else max(0, min(1, ((px-ax)*dx+(py-ay)*dy)/(dx*dx+dy*dy)))
        return math.hypot((px-(ax+t*dx))*66900, (py-(ay+t*dy))*111000)
    best = (1e9, '', '')
    for r in ROADS:
        if skip_service and (r['hw'] == 'service' or not r['name']):
            continue
        g = r['geom']
        for i in range(len(g)-1):
            d = d_ps(lat, lon, g[i][0], g[i][1], g[i+1][0], g[i+1][1])
            if d < best[0]:
                best = (d, r['name'], r['hw'])
    return best

def near_gate(lat, lon):
    best = (1e9, None)
    for g in RS['bramy']:
        d = math.hypot((g['lat']-lat)*111000, (g['lon']-lon)*66900)
        if d < best[0]:
            best = (d, g)
    return best

HEADER = ['id', 'kategoria', 'nazwa_opisowa', 'lat', 'lon', 'wysokość_m', 'źródło_wysokości',
          'kolor', 'materiał', 'widoczny_z_drogi', 'odległość_m', 'url_źródła', 'licencja',
          'autor', 'data_dostępu', 'status', 'uwagi']
rows = []
def add(**kw):
    r = {k: '' for k in HEADER}
    r['data_dostępu'] = DATA_DOST
    r.update(kw)
    rows.append(r)

# ---------- 1. LANDMARKI ----------
# ręczna kuracja: (wysokość, źródło_wysokości, status, extra_uwagi)
# wysokość 'U' = UNVERIFIED, liczba = LoD1 2024 (GUGiK), '0' = płaszczyzna/nawierzchnia
H = {
 1:('0','nawierzchnia pasa startowego; elewacja lotniska ok. 153 m n.p.m. (Wikipedia PL — Port lotniczy Białystok-Krywlany)','SOURCED','pas 09R/27L asfaltobeton 1350×30 m (Wikipedia PL); zdjęcia: files/P12-A01.jpg (ortofoto GUGiK), files/P12-P03-lotnisko.jpg (Commons CC BY-SA 3.0)'),
 2:('0','nawierzchnia pasa startowego (trawa)','SOURCED','pas 09L/27R trawa 860×160 m (Wikipedia PL); zdjęcie: files/P12-A01.jpg (ortofoto GUGiK)'),
 3:('0','płaszczyzna płyty postojowej (trawa)','SOURCED','zdjęcie: files/P12-A02.jpg (ortofoto GUGiK)'),
 4:('U','UNVERIFIED (obiekt nieujęty w dostarczonym zbiorze LoD1; brak height w OSM)','UNVERIFIED','hangar Aeroklubu Białostockiego przy płycie; zdjęcia: files/P12-A02.jpg (ortofoto), files/P12-P03-lotnisko.jpg (Commons CC BY-SA 3.0)'),
 5:('U','UNVERIFIED (brak height w OSM; silo poza budynkami LoD1)','UNVERIFIED','building=silo przy płycie postojowej; zdjęcie: files/P12-A03.jpg (ortofoto GUGiK)'),
 6:('3.4','GUGiK LoD1 2024 (measuredHeight)','SOURCED','Sekcja Modelarska Aeroklubu Białostockiego; zdjęcie: files/P12-A02.jpg (ortofoto GUGiK)'),
 7:('0','płaszczyzna zrzutowiska (trawa)','SOURCED','leisure=pitch 13 994 m2; rozpoznawalny układ pasów zrzutowiska; zdjęcie: files/P12-A03.jpg (ortofoto GUGiK)'),
 8:('15.05','GUGiK LoD1 2024 (measuredHeight)','SOURCED','największa hala kafla (28 212 m2); zdjęcie: files/P12-A07.jpg (ortofoto GUGiK)'),
 9:('12.17','GUGiK LoD1 2024 (measuredHeight)','SOURCED','druk przemysłowy (strona firmy — patrz sources.md); zdjęcie: files/P12-A08.jpg (ortofoto GUGiK)'),
 10:('12.72','GUGiK LoD1 2024 (measuredHeight)','SOURCED','wyposażenie gastronomiczne (lista lokatorów SSSE — patrz sources.md); zdjęcie: files/P12-A09.jpg (ortofoto GUGiK)'),
 11:('18.92','GUGiK LoD1 2024 (measuredHeight)','SOURCED','produkcja opakowań z tworzyw sztucznych (strona firmy — patrz sources.md); zdjęcie: files/P12-A10.jpg (ortofoto GUGiK)'),
 12:('18.09','GUGiK LoD1 2024 (measuredHeight)','SOURCED','5 kondygnacji (BDOT10k) — wieżowiec biurowy BPN-T; zdjęcie: files/P12-A10.jpg (ortofoto GUGiK)'),
 13:('6.01','GUGiK LoD1 2024 (measuredHeight)','SOURCED','operator: producent tekstyliów (strona firmy — patrz sources.md); zdjęcie: files/P12-A08.jpg (ortofoto GUGiK)'),
 14:('U','UNVERIFIED (hala poza zbiorem LoD1; brak height w OSM)','UNVERIFIED','strefa landuse=industrial 33 133 m2 (Centrum magazynowo-dystrybucyjne); bramy z placami manewrowymi od Dywizjonu 303; zdjęcie: files/P12-A04.jpg (ortofoto GUGiK)'),
 15:('U','UNVERIFIED (hale poza zbiorem LoD1)','UNVERIFIED','dwa budynki (3 734 + 8 053 m2); operator UNVERIFIED; zdjęcie: files/P12-A06.jpg (ortofoto GUGiK)'),
 16:('U','UNVERIFIED (obiekt w budowie — stan z ortofoto 2024/2025; docelowo hala przemysłowa)','UNVERIFIED','19 420 m2, landuse=construction 52 150 m2; inwestor UNVERIFIED (patrz sources.md); zdjęcie: files/P12-A05.jpg (ortofoto GUGiK)'),
 17:('U','UNVERIFIED (brak height w OSM/LoD1; słupy trakcyjne 110 kV typowo 25–45 m — nie ekstrapolowano)','UNVERIFIED','ogrodzona stacja RPZ11 110/15 kV; zdjęcie: files/P12-A08.jpg (ortofoto GUGiK)'),
 18:('24.44','GUGiK LoD1 2024 (measuredHeight) — najwyższy budynek kafla','SOURCED','5 kondygnacji (BDOT10k); zdjęcia: files/P12-A11.jpg (ortofoto GUGiK), files/P12-P04-sad.jpg (Commons CC BY-SA 3.0)'),
 19:('12.22','GUGiK LoD1 2024 (measuredHeight)','SOURCED','zdjęcie: files/P12-A11.jpg (ortofoto GUGiK)'),
 20:('14.85','GUGiK LoD1 2024 (pawilon E1, najwyższy kompleksu; pawilon A bez measuredHeight w zbiorze)','SOURCED','kompleks pawilonów A-F; lądowisko śmigłowcowe przy pawilonie A/E (OSM helipad 883 m2, 53.107688, 23.187375); zdjęcie: files/P12-A12.jpg (ortofoto GUGiK)'),
 21:('5.27','GUGiK LoD1 2024 (measuredHeight)','SOURCED','plac manewrowy WORD; zdjęcie: files/P12-A13.jpg (ortofoto GUGiK)'),
 22:('11.67','GUGiK LoD1 2024 (measuredHeight)','SOURCED','obiekt w ogrodzonej strefie (landuse=military 12 010 m2); zdjęcie: files/P12-A13.jpg (ortofoto GUGiK)'),
 23:('13.23','GUGiK LoD1 2024 (measuredHeight)','SOURCED','3 kondygnacje (BDOT10k); zdjęcie: files/P12-A14.jpg (ortofoto GUGiK)'),
 24:('11.64','GUGiK LoD1 2024 (measuredHeight)','SOURCED','kamienica przy rondzie Ciołkowskiego/Mickiewicza; zdjęcie: files/P12-A17.jpg (ortofoto GUGiK)'),
 25:('6.69','GUGiK LoD1 2024 (measuredHeight)','SOURCED','hala parterowa z parkingiem (bez znaków towarowych w opisie); zdjęcie: files/P12-A13.jpg (ortofoto GUGiK)'),
 26:('6.39','GUGiK LoD1 2024 (measuredHeight)','SOURCED','parterowy pawilon spółdzielczy na osiedlu; zdjęcie: files/P12-A16.jpg (ortofoto GUGiK)'),
 27:('16.3','GUGiK LoD1 2024 (maks. w zespole; bloki 3-kondygnacyjne 9,9–16,3 m)','SOURCED','układ wokół Niedźwiedziej/Żubrów; zdjęcie: files/P12-A15.jpg (ortofoto GUGiK)'),
 28:('15.31','GUGiK LoD1 2024 (measuredHeight)','SOURCED','dominant wysokościowy północnego wlotu Mickiewicza; zdjęcie: files/P12-A17.jpg (ortofoto GUGiK)'),
 29:('11.24','GUGiK LoD1 2024 (measuredHeight)','SOURCED','2 kondygnacje (BDOT10k); zdjęcie: files/P12-A18.jpg (ortofoto GUGiK)'),
 30:('U','UNVERIFIED (man_made=mast; brak height w OSM, poza budynkami LoD1)','UNVERIFIED','maszt 1: 53.115871, 23.177037 (trójnóg przy Zwierzynieckiej); maszt 2: 53.108915, 23.191592 (strefa ABW); zdjęcia: files/P12-A17.jpg, files/P12-A13.jpg (ortofoto GUGiK)'),
 31:('U','UNVERIFIED (poza kaflem — brak LoD1; hala warzelni bez height w OSM)','UNVERIFIED','kominy browaru widoczne z Dywizjonu 303 (z kafla) i z Dojlidy Fabryczne; zdjęcia: files/P12-A21.jpg (ortofoto), files/P12-P01-browar-panorama.jpg i files/P12-P02-browar-fasada.jpg (Commons CC BY-SA 3.0/4.0); fasada ceglana czerwona (ESTIMATED ze zdjęcia P12-P02)'),
 32:('U','UNVERIFIED (storage_tank ×30; brak height w OSM)','UNVERIFIED','rozpoznawalny "las" cylindrów; zdjęcie: files/P12-A21.jpg (ortofoto GUGiK)'),
 33:('U','UNVERIFIED (poza kaflem — brak LoD1; building:levels=1 w OSM)','UNVERIFIED','hala producenta sklejki (strona firmy — patrz sources.md); kominy: 53.113289, 23.198542 i 53.114204, 23.201536 (wys. UNVERIFIED); zdjęcie: files/P12-A22.jpg (ortofoto GUGiK)'),
 34:('U','UNVERIFIED (poza kaflem — brak LoD1; man_made=works bez height w OSM)','UNVERIFIED','produkcja przyrządów i uchwytów (katalog firm — patrz sources.md); zdjęcie: files/P12-A23.jpg (ortofoto GUGiK)'),
 35:('U','UNVERIFIED (poza kaflem — brak LoD1; man_made=works bez height w OSM)','UNVERIFIED','produkcja armatury i kotłów (strona firmy — patrz sources.md); zdjęcie: files/P12-A24.jpg (ortofoto GUGiK)'),
 36:('U','UNVERIFIED (poza kaflem — brak LoD1; man_made=works bez height w OSM)','UNVERIFIED','odlewnia metali (katalog firm — patrz sources.md); zdjęcie: files/P12-A23.jpg (ortofoto GUGiK)'),
 37:('U','UNVERIFIED (poza kaflem — brak LoD1; wieża kościoła bez height w OSM)','UNVERIFIED','parafia Dojlidy, start budowy 1980 (OSM start_date); zdjęcie: files/P12-A25.jpg (ortofoto GUGiK)'),
 38:('6.69','GUGiK LoD1 2024 (mediana wysokości altan w N=9 z próby LoD1)','ESTIMATED','trzy ROD: im. Adama Mickiewicza (156 739 m2), Ekologiczny (61 820 m2), Relaks (134 332 m2); zadrzewione osiedla altan; zdjęcie: files/P12-A19.jpg (ortofoto GUGiK)'),
 39:('U','UNVERIFIED (poza kaflem — brak LoD1; castle_type=palace bez height w OSM)','UNVERIFIED','pałac fabrykanta z pocz. XX w. (Dojlidy Fabryczne 23); Pałac Lubomirskich (Suchowolca 26, 53.109637, 23.204708) ok. 480 m na S; zdjęcia: files/P12-A26.jpg (ortofoto GUGiK), files/P12-P05-palac-hasbacha.jpg (Commons CC BY-SA 3.0)'),
}

MAT = {
 'srebrno-szara (ocynk)': ('dach: srebrno-szara (ocynk)', 'blacha stalowa ocynkowana (ESTIMATED z barwy na ortofoto GUGiK)'),
 'jasna/biała': ('dach: jasna/biała', 'pokrycie bitumiczne/płyta (ESTIMATED z ortofoto GUGiK)'),
 'jasnoszara': ('dach: jasnoszara', 'pokrycie bitumiczne/blacha jasna (ESTIMATED z ortofoto GUGiK)'),
 'szara': ('dach: szara', 'płyta żelbetowa z papą (LoD1 roofType=1000 — dach płaski) lub blacha (ESTIMATED)'),
 'grafitowa/ciemnoszara': ('dach: grafitowa/ciemnoszara', 'blacha lakierowana/papa (ESTIMATED z ortofoto GUGiK)'),
 'antracytowa': ('dach: antracytowa', 'blacha lakierowana/papa (ESTIMATED z ortofoto GUGiK)'),
 'czarna': ('dach: czarna', 'papa (ESTIMATED z ortofoto GUGiK)'),
 'czerwona/rdzawa (dachówka lub blacha lakierowana)': ('dach: czerwona/rdzawa', 'dachówka ceramiczna lub blacha lakierowana (ESTIMATED z ortofoto GUGiK)'),
 'czerwonorudawa (rozbielona dachówka)': ('dach: czerwonorudawa', 'dachówka ceramiczna (ESTIMATED z ortofoto GUGiK)'),
 'zielona': ('dach: zielona', 'blacha lakierowana (ESTIMATED z ortofoto GUGiK)'),
 'niebieska': ('dach: niebieska', 'blacha lakierowana (ESTIMATED z ortofoto GUGiK)'),
}

# drogi widoczności — ręczne nadpiszenie tam, gdzie najbliższa droga w geometrii to service;
# forma: id -> (droga, odległość_m) ; brak wpisu = najbliższa droga nie-service z OSM
WIDOK = {
 1: ('ul. Dywizjonu 303', 150), 2: ('ul. Dywizjonu 303', 145),
 3: ('ul. Krywlany (droga lotniskowa)', 55), 4: ('ul. Krywlany (droga lotniskowa)', 40),
 5: ('ul. Krywlany (droga lotniskowa)', 60), 6: ('ul. Krywlany (droga lotniskowa)', 45),
 7: ('ul. Krywlany (droga lotniskowa)', 160),
 8: ('ul. Franciszka Karpińskiego', 50), 9: ('ul. Jacka Kuronia', 60),
 10: ('ul. Jacka Kuronia', 45), 11: ('ul. Myśliwska', 60), 12: ('ul. Żurawia', 60),
 13: ('ul. Jacka Kuronia', 30), 14: ('ul. Dywizjonu 303', 95),
 15: ('ul. Pułkownika Czesława Hake', 50), 16: ('ul. Spadochroniarzy', 95),
 17: ('ul. Jacka Kuronia', 80), 18: ('ul. Adama Mickiewicza', 45),
 19: ('ul. Adama Mickiewicza', 25), 20: ('ul. Żurawia', 80), 21: ('ul. Wiewiórcza', 15),
 22: ('ul. Żurawia', 60), 23: ('ul. Adama Mickiewicza', 30), 24: ('ul. Konstantego Ciołkowskiego', 20),
 25: ('ul. Wiewiórcza', 30), 26: ('ul. Sokola', 15), 27: ('ul. Niedźwiedzia', 25),
 28: ('ul. Adama Mickiewicza', 20), 29: ('ul. Żwirki i Wigury', 35),
 30: ('ul. Zwierzyniecka / ul. Żurawia', 15),
 31: ('ul. Dywizjonu 303 (z kafla, sylwetka) / Dojlidy Fabryczne', 600),
 32: ('ul. Dywizjonu 303 (z kafla) / Dojlidy Fabryczne', 650),
 33: ('ul. Jacka Kuronia / Żurawia (sylweta kominów)', 400),
 34: ('ul. Jacka Kuronia (odcinek południowy)', 250),
 35: ('ul. Dojlidy Fabryczne', 550), 36: ('ul. Jacka Kuronia / Franciszka Karpińskiego', 300),
 37: ('ul. Dojlidy Fabryczne (wieża) / Dywizjonu 303 (sylwetka)', 360),
 38: ('ul. Adama Mickiewicza', 30),
 39: ('ul. Dojlidy Fabryczne (od Ronda Hasbacha)', 65),
}

for l in L:
    n = int(l['id'].split('-')[1])
    c = C[l['id']]
    h, zr, st, extra = H[n]
    wys = h if h != 'U' else 'UNVERIFIED'
    zr_out = zr if h != 'U' else 'UNVERIFIED (brak pomiaru — patrz uwagi)'
    kol = MAT.get(c.get('roof_color_name') or '', ('UNVERIFIED (brak próby z ortofoto)', 'UNVERIFIED'))
    droga, dist = WIDOK[n]
    mwr = MWR.get(l.get('osm_way') or 0) or {}
    if mwr.get('road_name') and n not in WIDOK:
        droga = 'ul. ' + mwr['road_name']; dist = round(mwr['road_dist'])
    url = EP + ('way/%d' % l['osm_way']) if l.get('osm_way') else \
          ('https://www.openstreetmap.org/?mlat=%s&mlon=%s#map=19/%s/%s' % (l['lat'], l['lon'], l['lat'], l['lon']))
    if n in (1, 2):
        url += ' ; https://pl.wikipedia.org/wiki/Port_lotniczy_Bia%C5%82ystok-Krywlany'
    if n == 37:
        url += ' ; https://www.parafiansm.pl'
    lic = OSM_LIC + ' / ' + GUGIK_LIC
    if n in (31,):
        lic = OSM_LIC + ' / ' + GUGIK_LIC + ' / CC BY-SA 3.0 + CC BY-SA 4.0 (zdjęcia Wikimedia Commons)'
    if n in (18, 39):
        lic = OSM_LIC + ' / ' + GUGIK_LIC + ' / CC BY-SA 3.0 (zdjęcie Wikimedia Commons)'
    if n in (4,):
        lic = OSM_LIC + ' / ' + GUGIK_LIC + ' / CC BY-SA 3.0 (zdjęcie Wikimedia Commons)'
    uw = (l['uwagi'] + '; ' + extra).strip()
    if l.get('poza_kaflem'):
        uw += '; [poza kaflem — widoczne z dróg kafla/na jego krawędzi]'
    add(id=l['id'], kategoria='landmark', nazwa_opisowa=l['nazwa'],
        lat=l['lat'], lon=l['lon'], wysokość_m=wys, źródło_wysokości=zr_out,
        kolor=kol[0] + '; elewacja UNVERIFIED (brak legalnych zdjęć ulicznych — patrz README)' if n not in (31,)
             else kol[0] + '; fasada: czerwona cegła (ESTIMATED ze zdjęcia Commons P12-P02)',
        materiał=kol[1] + '; elewacja UNVERIFIED' if n != 31 else kol[1] + '; fasada: cegła pełna czerwona (ESTIMATED ze zdjęcia)',
        widoczny_z_drogi=droga, odległość_m=dist, url_źródła=url, licencja=lic,
        autor=OSM_AUT + ' / ' + GUGIK_AUT, status=st, uwagi=uw)

# ---------- 2. TYPOLOGIA ----------
TYP_NAZ = {
 'dom_jednorodzinny': 'Domy jednorodzinne przy drogach (bufor 30 m)',
 'gospodarcze_i_inne': 'Budynki gospodarcze i inne (garaże/magazyny/osobowe przy drogach)',
 'handlowo_usługowy': 'Budynki handlowo-usługowe',
 'blok_wielorodzinny': 'Bloki wielorodzinne',
 'hala_przemysłowa': 'Hale przemysłowo-magazynowe',
 'altana_ROD': 'Altany ogrodów działkowych (ROD)',
}
TYP_MAT = {
 'dom_jednorodzinny': 'dachy dwuspadowe (ESTIMATED z ortofoto); pokrycie wg próby kolorów; elewacje UNVERIFIED (typowo cegła/tynk — nie ekstrapolowano)',
 'gospodarcze_i_inne': 'parterowe, dachy dwuspadowe/płaskie (ESTIMATED z ortofoto)',
 'handlowo_usługowy': 'parterowe pawilony, dachy płaskie (LoD1 roofType=1000)',
 'blok_wielorodzinny': 'płyta wielkopłytowa (ESTIMATED — typ zabudowy lat 80.); dachy płaskie płyta/papa (LoD1 roofType=1000)',
 'hala_przemysłowa': 'konstrukcja stalowa, ściana kasetonowa blacha (ESTIMATED); dach płaski (LoD1 roofType=1000)',
 'altana_ROD': 'drewno (ESTIMATED — typowa konstrukcja altan); dach dwuspadowy blacha/ondoferm (ESTIMATED z ortofoto)',
}
TYP_COL_EXTRA = {
 'dom_jednorodzinny': 'dominanty barw dachu: szara 34,0%, grafitowa 14,6%, ocynk 14,1%, czerwonorudawa+czerwona 14,4% (N=745 próbek)',
 'gospodarcze_i_inne': 'barwy dachu zbliżone do domów (szara/ocynk dominują)',
 'handlowo_usługowy': 'dachy płaskie szara/jasnoszara',
 'blok_wielorodzinny': 'szara 66,7% (płyta/papa) (N=18 próbek)',
 'hala_przemysłowa': 'szara 28,6%, ocynk 23,8%, jasnoszara 19,0%, biała 14,3% (N=21 próbek)',
 'altana_ROD': 'szara 71,4% (N=7 próbek)',
}
TOT = sum(v['n_buf30'] for v in TYP.values())
for i, (k, v) in enumerate(TYP.items()):
    n = 40 + i
    kol = TYPC['klasy'].get(k, {})
    add(id='P12-%03d' % n, kategoria='typologia',
        nazwa_opisowa=('%s — %d z %d budynków bufora = %.1f%%' % (TYP_NAZ[k], v['n_buf30'], TOT, 100.0*v['n_buf30']/TOT)),
        lat=53.107162, lon=23.179805, wysokość_m=v['h_med'],
        źródło_wysokości='GUGiK LoD1 2024 (mediana measuredHeight; p10=%s, p90=%s)' % (v['h_p10'], v['h_p90']),
        kolor=('dachy: ' + (', '.join('%s %.1f%%' % (kk, vv) for kk, vv in list(kol.get('rozklad_kolorow', {}).items())[:4]) if kol else 'UNVERIFIED')),
        materiał=TYP_MAT[k], widoczny_z_drogi='drogi główne regionu (bufor 30 m)', odległość_m=30,
        url_źródła='https://www.geoportal.gov.pl/ (LoD1/BDOT10k) ; ' + EP + ' (OSM)',
        licencja=GUGIK_LIC + ' / ' + OSM_LIC, autor=GUGIK_AUT + ' / ' + OSM_AUT,
        status='SOURCED' if k in ('dom_jednorodzinny', 'blok_wielorodzinny', 'hala_przemysłowa') else 'ESTIMATED',
        uwagi=('census: wszystkie budynki kafla (1307) przypisane do klas wg BDOT10k/OSM; bufor 30 m od dróg '
               'bez service (911 budynków); odległości budynków od drogi: p50=21 m, p90=55 m, max 214 m; '
               'kolory dachów: mediana RGB w dysku r=min(√(A/π)/2, 8 m) z ortofoto GUGiK 0,5 m/px (metoda w tools/frames_colors.py); '
               + TYP_COL_EXTRA[k] +
               '; wysokość mediana=%s m (N_h=%d)' % (v['h_med'], v['n_h'])))

# ---------- 3. WYPOSAŻENIE ----------
wid = 46  # licznik id
# wiaty/przystanki
for p in RS['przystanki']:
    d_nm = (p['name'] or '').split('/')[0].split(' NŻ')[0].strip()
    shelter = p.get('shelter') == 'yes'
    add(id='P12-%03d' % wid, kategoria='wyposażenie',
        nazwa_opisowa=('Przystanek %s — %s' % (p['name'], 'wiata' if shelter else 'słupek (bez wiaty)')),
        lat=p['lat'], lon=p['lon'], wysokość_m='UNVERIFIED' if shelter else 'n/d (słupek)',
        źródło_wysokości='UNVERIFIED (typ wiaty: stare — oszklona czerwona "modern" ok. 2,7 m; nowe od 2026 — antracytowe aluminium z półokrągłym dachem; wysokości z rysunków ZDiT niedostępne)' if shelter else 'n/d (słupek)',
        kolor='stare: czerwona ramka + szkło; nowe (od 2026): antracyt — UNVERIFIED dla tego przystanku' if shelter else 'UNVERIFIED',
        materiał='stare: stal + szkło; nowe: aluminium (Radio Białystok — wymiana 90 szt. w mieście)' if shelter else 'UNVERIFIED',
        widoczny_z_drogi='ul. ' + d_nm, odległość_m=0,
        url_źródła=('https://www.openstreetmap.org/?mlat=%s&mlon=%s#map=19/%s/%s' % (p['lat'], p['lon'], p['lat'], p['lon'])) +
                   ' ; https://www.radio.bialystok.pl/wiadomosci/index/id/262755',
        licencja=OSM_LIC + ' / Radio Białystok (informacja — tylko referencja)',
        autor=OSM_AUT, status='UNVERIFIED' if shelter else 'SOURCED',
        uwagi=('highway=bus_stop%s; %s' % (' + shelter=yes' if shelter else '',
               'wiaty w regionie wg ZDiT: stare oszklone czerwone "modern"; od 2026 wymiana na antracytowe aluminium z półokrągłym dachem typ "Stare Miasto" (Radio Białystok 2026, 4,1 mln zł, 90 szt. w mieście); który wariant stoi tu — UNVERIFIED' if shelter else 'przystanek na żądanie/wyłącznie słupek'))
        )
    wid += 1

# bollardy (grupa 4 szt.)
bol = [p for p in POIS if p.get('tags', {}).get('barrier') == 'bollard' and p.get('in_tile')]
add(id='P12-%03d' % wid, kategoria='wyposażenie',
    nazwa_opisowa='Bollardy stałe (grupa 4 szt.) — zatoka przy Żurawia/Wiewiórcza',
    lat=bol[0]['lat'], lon=bol[0]['lon'], wysokość_m='UNVERIFIED (typowo 0,7–1,0 m — nie pomierzono)',
    źródło_wysokości='UNVERIFIED', kolor='UNVERIFIED', materiał='stal/stalbeton (ESTIMATED z ortofoto)',
    widoczny_z_drogi='ul. Żurawia', odległość_m=5,
    url_źródła=EP + 'node/%d' % bol[0]['id'],
    licencja=OSM_LIC, autor=OSM_AUT, status='ESTIMATED',
    uwagi='pozycje: ' + '; '.join('%s,%s' % (b['lat'], b['lon']) for b in bol) + ' (barrier=bollard, bollard=fixed)')
wid += 1

# znaki PL:A-11a (przystanek na żądanie)
a11 = [p for p in POIS if 'PL:A-11a' in (p.get('tags', {}).get('traffic_sign') or '') and p.get('in_tile')]
add(id='P12-%03d' % wid, kategoria='wyposażenie',
    nazwa_opisowa='Znaki PL:A-11a (przystanek na żądanie) — 8 szt. przy progach zwalniających',
    lat=a11[0]['lat'], lon=a11[0]['lon'], wysokość_m='n/d (znak na pionie progu)',
    źródło_wysokości='n/d', kolor='UNVERIFIED (tabliczka biała/czarna wg wzoru znaku)', materiał='n/d',
    widoczny_z_drogi='ul. Żurawia / ul. Wiewiórcza', odległość_m=0,
    url_źródła=EP + 'node/%d' % a11[0]['id'], licencja=OSM_LIC, autor=OSM_AUT, status='SOURCED',
    uwagi='pozycje: ' + '; '.join('%s,%s' % (a['lat'], a['lon']) for a in a11) + '; wszystkie na traffic_calming=bump')
wid += 1

# latarnie
lamp = [p for p in POIS if p.get('tags', {}).get('highway') == 'street_lamp']
add(id='P12-%03d' % wid, kategoria='wyposażenie',
    nazwa_opisowa='Latarnie uliczne — pokrycie OSM zerowe (1 obiekt w wyciągu)',
    lat=lamp[0]['lat'], lon=lamp[0]['lon'], wysokość_m='UNVERIFIED (brak height w OSM; typ ZDiT 8–10 m — nie ekstrapolowano)',
    źródło_wysokości='UNVERIFIED', kolor='UNVERIFIED', materiał='UNVERIFIED',
    widoczny_z_drogi='ul. Bolesława Prusa', odległość_m=2,
    url_źródła=EP + 'node/%d' % lamp[0]['id'], licencja=OSM_LIC, autor=OSM_AUT, status='UNVERIFIED',
    uwagi='LUKA: OSM mapuje w kaflu tylko tę 1 latarnię; oświetlenie dróg głównej sieci (Mickiewicza, Kuronia, Dywizjonu 303, Ciołkowskiego, Wiewiórcza) nie ma pokrycia w OSM — do weryfikacji Mapillary/KartaView (obecnie niedostępne: patrz README)')
wid += 1

# ekrany akustyczne
add(id='P12-%03d' % wid, kategoria='wyposażenie',
    nazwa_opisowa='Ekrany akustyczne — brak (0 obiektów w OSM kafla; brak śladów na ortofoto)',
    lat=53.1062, lon=23.1855, wysokość_m='n/d (brak obiektu)', źródło_wysokości='n/d',
    kolor='n/d', materiał='n/d', widoczny_z_drogi='korytarz tranzytu Kuronia–Dywizjonu 303–Ciołkowskiego',
    odległość_m=0, url_źródła=EP, licencja=OSM_LIC, autor=OSM_AUT, status='SOURCED',
    uwagi='weryfikacja: zapytanie Overpass o barrier=wall/noise + przegląd kadru ortofoto wzdłuż Dywizjonu 303 — brak konstrukcji ekranowych; UNVERIFIED czy planowane w ramach przebudowy hali sportowej przy Ciołkowskiego')
wid += 1

# ogrodzenia zakładów
add(id='P12-%03d' % wid, kategoria='wyposażenie',
    nazwa_opisowa='Ogrodzenia zakładów (barrier=fence) — 88 odcinków; strefy ogrodzone: lotnisko, BPN-T, zakłady Kuronia/Karpińskiego, ABW',
    lat=53.108958, lon=23.192319, wysokość_m='UNVERIFIED (typowo 2,0–2,5 m — nie pomierzono)',
    źródło_wysokości='UNVERIFIED', kolor='UNVERIFIED (na ortofoto: siatka zielonoszara/łoś — ESTIMATED)',
    materiał='siatka ogrodzeniowa stalowa (ESTIMATED z ortofoto)',
    widoczny_z_drogi='wzdłuż ul. Żurawia, Jacka Kuronia, Franciszka Karpińskiego', odległość_m=0,
    url_źródła=EP, licencja=OSM_LIC, autor=OSM_AUT, status='ESTIMATED',
    uwagi='geometria odtwarzalna z wyciągu Overpass (tools/parse_osm.py); pozycja wiersza = ogrodzona strefa przy Żurawia 69 (landuse=military 12 010 m2)')
wid += 1

# drogowskazy E-* / tablice wlotowe
WLOTY = [
 ('Tablice drogowe na wlocie: skrzyżowanie Suchowolca/Plażowa/Kuronia', 'Ks. Stanisława Suchowolca', ['Ks. Stanisława Suchowolca', 'Plażowa', 'Jacka Kuronia']),
 ('Tablice drogowe na wlocie: skrzyżowanie Ciołkowskiego/Mickiewicza', 'Konstantego Ciołkowskiego', ['Konstantego Ciołkowskiego', 'Adama Mickiewicza']),
 ('Tablice drogowe na wlocie: skrzyżowanie Ciołkowskiego/Dywizjonu 303', 'Konstantego Ciołkowskiego', ['Konstantego Ciołkowskiego', 'Dywizjonu 303']),
]
def road_cross(names):
    """punkt przecięcia dróg z geometrii OSM (para najbliższych punktów)"""
    rds = [r for r in ROADS if r['name'] in names]
    best = (1e9, None, None)
    for i in range(len(rds)):
        for j in range(i+1, len(rds)):
            for a in rds[i]['geom']:
                for b in rds[j]['geom']:
                    d = math.hypot((a[0]-b[0])*111000, (a[1]-b[1])*66900)
                    if d < best[0]:
                        best = (d, a, b)
    if best[1] is None:
        return None
    return ((best[1][0]+best[2][0])/2, (best[1][1]+best[2][1])/2, best[0])
for nazwa, glowna, names in WLOTY:
    cr = road_cross(names)
    add(id='P12-%03d' % wid, kategoria='wyposażenie',
        nazwa_opisowa=nazwa + ' — nowe tablice kierunkowe (ZDM, XII 2025)',
        lat=(cr[0] if cr else ''), lon=(cr[1] if cr else ''),
        wysokość_m='n/d (tablice na wjeździe)', źródło_wysokości='n/d',
        kolor='UNVERIFIED (tablice kierunkowe błękitne/czarne wg wzoru — do potwierdzenia zdjęciem)',
        materiał='n/d', widoczny_z_drogi='ul. ' + glowna, odległość_m=0,
        url_źródła='https://www.bialystok.pl/pl/wiadomosci/utrudnienia-w-ruchu-na-wlotach-skrzyzowan-ulic.html',
        licencja='Dokument/komunikat urzędowy (UM Białystok) — tylko referencja',
        autor='UM Białystok / ZDM', status='UNVERIFIED',
        uwagi=('komunikat ZDM (wymiana tablic 2–5 XII 2025) wymienia ten wlot; pozycja = przecięcie osi jezdni '
               'z geometrii OSM (ESTIMATED, dokładność ~10 m); treść konkretnych drogowskazów E-* (numery drogowe '
               'kierunku) UNVERIFIED; w OSM brak tagów destination/direction na wlotach'))
    wid += 1

# ---------- 4. GENERATORY RUCHU ----------
# (nazwa, opis, lat_centroid, lon_centroid, osm_way_or_None, strona/źródło dodatkowe, status, uwagi)
GEN = [
 ('Centrum logistyczno-produkcyjne KAN (magazyn 28 212 m2)', 'magazyn logistyczny — produkcja i logistyka instalacji sanitarnych',
  53.104351, 23.19079, 471492581, 'https://kan-therm.com/pl/kontakt/', 'SOURCED',
  'brama: najbliższy barrier=gate/lift_gate z OSM (53.103498, 23.190006, ~110 m od centroidu — metoda dopasowania: odległość euklidesowa); place manewrowe od Karpińskiego'),
 ('Masterpress S.A. (druk przemysłowy)', 'drukarnia etykiet — dostawy masą',
  53.105609, 23.191144, 234838499, 'https://masterpress.com/pl/contact/', 'SOURCED',
  'brama OSM (lift_gate 53.106018, 23.192241, ~85 m); adres Jacka Kuronia 4'),
 ('Bravilor Bonamat Sp. z o.o. (producent wyposażenia gastronomicznego)', 'hala produkcyjno-magazynowa w SSSE',
  53.10533, 23.187331, 513010463, 'https://ssse.com.pl/lokalizacja/bravilor-polska/', 'SOURCED',
  'brama OSM (gate 53.105887, 23.187439, ~60 m); adres Jacka Kuronia 2'),
 ('Rosti Poland Sp. z o.o. (produkcja opakowań z tworzyw sztucznych)', 'hala produkcyjna 13 578 m2',
  53.103746, 23.193953, 252332077, 'https://www.rosti.com/', 'SOURCED',
  'brama OSM (gate 53.103204, 23.193609, ~65 m); adres Myśliwska 18'),
 ('Białostocki Park Naukowo-Technologiczny (Inkubator, Żurawia 71)', 'park technologiczny — magazyny/laboratoria firmy BPN-T Sp. z o.o.',
  53.106874, 23.193275, 275237239, 'https://bpnt.bialystok.pl/kontakt/', 'SOURCED',
  'brama OSM (gate 53.107451, 23.193443, ~65 m); miejsca postojowe i place manewrowe od Żurawia'),
 ('Hurtowe centrum magazynowe PSS "Społem" Białystok (Dywizjonu 303 8)', 'centrum magazynowo-dystrybucyjne sieci handlowej — ruch TIR dostawczych',
  53.105347, 23.171971, 1525885366, 'https://www.spolembialystok.eu/ ; https://www.dlahandlu.pl/hurtowe-centrum-magazynowe', 'SOURCED',
  'najbliższa brama OSM 386 m od centroidu (53.104147, 23.177389) — brama wjazdowa z D303 UNVERIFIED (dokładne wjazdy niedomapowane); strefa landuse=industrial 33 133 m2'),
 ('Hale magazynowe Pułkownika Czesława Hake 9/11', 'hale magazynowe 11 787 m2 — operator UNVERIFIED',
  53.105761, 23.169482, 1329697011, '', 'UNVERIFIED',
  'katalogi firm wskazują producenta tekstyliów (monitorfirm.pb.pl — tylko referencja); brama OSM 288 m — wjazd z Hake UNVERIFIED'),
 ('Kontri Sp. z o.o. (producent tekstyliów technicznych)', 'hala produkcyjna Jacka Kuronia 3',
  53.106752, 23.191379, 538810163, 'https://kontri.pl/pl/contact.html', 'SOURCED',
  'brama OSM (gate 53.107292, 23.192212, ~80 m)'),
 ('Hala w budowie — Spadochroniarzy 2 (19 420 m2)', 'budowa hali przemysłowo-magazynowej; inwestor UNVERIFIED',
  53.106974, 23.173746, 1535030699, '', 'UNVERIFIED',
  'landuse=construction 52 150 m2; najbliższa brama OSM 208 m — wjazd UNVERIFIED; kontekst: przetargi SSSE na działki przy BPN-T wygrały firmy logistyczna i gastronomiczna (jartom.com — tylko referencja); od 2028 w sąsiedztwie hala sportowa przy Ciołkowskiego'),
 ('Art-Glas (hurtownia szkła budowlanego)', 'hurtownia szkła — dostawy płaskiego szkła ciężarówkami',
  53.110372, 23.185822, 210878360, 'https://artglas.com.pl/', 'SOURCED',
  'brama OSM (gate 53.110652, 23.185712, ~30 m); adres Wiewiórcza 4'),
 ('Zintronic (producent systemów kamer i monitoringu)', 'budynek produkcyjno-biurowy, Modzelewskiego 2',
  53.110368, 23.186025, 1192357612, 'https://zintronic.com/monitoring-bialystok', 'SOURCED',
  'brama OSM (gate 53.110652, 23.185712, ~40 m)'),
 ('Lotnisko Białystok-Krywlany (baza Aeroklubu Białostockiego)', 'lotnisko sportowe — paliwo lotnicze, hangary, szkolenia; zarządca Aero Partner',
  53.101615, 23.172908, None, 'https://pl.wikipedia.org/wiki/Port_lotniczy_Bia%C5%82ystok-Krywlany', 'SOURCED',
  'właściciel: Aeroklub Białostocki (Wikipedia PL); bramy ogrodzenia lotniska: najbliższa OSM 53.099362, 23.177153 (378 m — mapa bram niepełna); plany lotniska pasażerskiego (investmap 29.10.2026) — patrz README'),
 ('Browar Dojlidy (Dojlidy Fabryczne 28)', 'browar — dostawy słodu/piwa cysternami i ciężarówkami; poza kaflem',
  53.106122, 23.203755, 221826898, '', 'SOURCED',
  'brama UNVERIFIED (poza kaflem; wjazd od Dojlidy Fabryczne); ~30 zbiorników storage_tank; operator: ogólnokrajowy producent piwa (bez marki w opisie — patrz sources.md)'),
 ('Biaform S.A. (producent sklejki, Dojlidy Fabryczne 24)', 'hala produkcyjna z suszarniami — dostawy drewna; poza kaflem',
  53.113602, 23.201396, 221209538, 'https://biaform.com.pl/kontakt/', 'SOURCED',
  'brama UNVERIFIED (poza kaflem; wjazd od Dojlidy Fabryczne); 2 kominy man_made=chimney'),
 ('Zakład produkcji przyrządów i uchwytów (BISON-BIAL, Myśliwska 13)', 'fabryka uchwytów tokarskich; poza kaflem',
  53.103528, 23.197561, 658448323, 'https://e-podlasie.pl (katalog — tylko referencja)', 'UNVERIFIED',
  'brama UNVERIFIED (poza kaflem; wjazd od Myśliwska/Dojlidy Fabryczne); man_made=works w OSM bez nazwy operatora'),
 ('NIBE-BIAWAR (producent armatury i kotłów, ul. Prof. Andrzeja Kalicińskiego 1)', 'zakład produkcyjny; poza kaflem',
  53.103364, 23.202254, 674071951, 'https://biawar.com.pl/kontakt-2/', 'SOURCED',
  'brama UNVERIFIED (poza kaflem; wjazd od Dojlidy Fabryczne/Kalicińskiego); man_made=works w OSM'),
 ('Odlewnia Białystok S.A. (Myśliwska 11)', 'odlewnia metali — dostawy złomu i wyrobów; poza kaflem',
  53.104296, 23.197727, 315456645, 'https://www.cylex-polska.pl/ (katalog — tylko referencja)', 'UNVERIFIED',
  'brama UNVERIFIED (poza kaflem); man_made=works w OSM bez height/nazwy'),
]
for nazwa, opis, lat, lon, way, strona, st, uw in GEN:
    wid += 1
    d, g = near_gate(lat, lon)
    gate_ok = d < 250 and g is not None
    mwr = MWR.get(way or 0) or {}
    h = mwr.get('lod_h')
    h_out = ('%.2f' % h) if h else 'UNVERIFIED'
    zr_h = 'GUGiK LoD1 2024 (measuredHeight hali)' if h else 'UNVERIFIED (brak pomiaru LoD1 dla obiektu)'
    dist, droga, _hw = near_road(lat, lon)
    if not droga:
        droga, dist = 'UNVERIFIED (poza wyciągiem OSM kafla)', ''
    url = (EP + 'way/%d' % way) if way else ('https://www.openstreetmap.org/?mlat=%s&mlon=%s#map=19/%s/%s' % (lat, lon, lat, lon))
    urls = url + (' ; ' + strona if strona else '')
    lic = OSM_LIC + (('/ strona firmy (informacja — tylko referencja)' if st == 'UNVERIFIED' else ' / strona firmy (informacja — tylko referencja)') if strona else '')
    add(id='P12-%03d' % wid, kategoria='generator_ruchu',
        nazwa_opisowa=nazwa + ' — ' + opis,
        lat=(g['lat'] if gate_ok else lat), lon=(g['lon'] if gate_ok else lon),
        wysokość_m=h_out, źródło_wysokości=zr_h,
        kolor='patrz wpis landmark w sekcji landmark (dach z ortofoto GUGiK)',
        materiał='hala: konstrukcja stalowa + kasetony (ESTIMATED); elewacja UNVERIFIED',
        widoczny_z_drogi='ul. ' + droga, odległość_m=round(dist),
        url_źródła=urls, licencja=lic, autor=OSM_AUT, status=st,
        uwagi=uw + ('; POZYCJA WIERSZA = brama OSM (barrier=%s)' % g['barrier'] if gate_ok else '; POZYCJA WIERSZA = centroid zakładu (brama UNVERIFIED)'))

# ---------- zapis ----------
with open(OUT, 'w', newline='', encoding='utf-8-sig') as f:
    w = csv.DictWriter(f, fieldnames=HEADER, quoting=csv.QUOTE_MINIMAL)
    w.writeheader()
    for r in rows:
        w.writerow(r)
print('manifest.csv:', len(rows), 'wierszy ->', os.path.abspath(OUT))
print('  landmarki:', sum(1 for r in rows if r['kategoria'] == 'landmark'),
      '| typologia:', sum(1 for r in rows if r['kategoria'] == 'typologia'),
      '| wyposażenie:', sum(1 for r in rows if r['kategoria'] == 'wyposażenie'),
      '| generatory:', sum(1 for r in rows if r['kategoria'] == 'generator_ruchu'))
