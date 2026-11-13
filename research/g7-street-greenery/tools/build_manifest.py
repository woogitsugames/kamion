"""Builds manifest.csv and mapillary_sample.csv for G7 (street greenery). Run with the worldgen venv python (-I).
Inputs: photo_rows.json (scratch, Commons metadata re-verified 2026-11-13), tools/house_streets_agg.json, Data/raw/mapillary/posesje/manifest.jsonl.
"""
import csv, json, collections
S = 'C:/Users/matma/AppData/Local/Temp/claude/883ada59a1ed007c/06b2245c-0b4a-4b25-b7cc-3632571cf10e/scratchpad/'
R = 'C:/Users/matma/Documents/Claude/kamion/'
OUT = R + 'research/g7-street-greenery/'
rows = json.load(open(S + 'photo_rows.json', encoding='utf-8'))
DA = '2026-11-13'
cols = ['id', 'ulica', 'lat', 'lon', 'gatunek', 'wysokość_m', 'typ', 'sezon', 'metoda', 'url_źródła', 'licencja', 'autor', 'data_dostępu', 'status', 'uwagi']
M = []


def add(**k):
    r = {c: '' for c in cols}
    r.update(k)
    r['data_dostępu'] = r['data_dostępu'] or DA
    M.append(r)


H = 'wysokość_m'
obs = {
    'G7-P01': ('Wołkowyska', 'Thuja occidentalis (żywopłot wysoki + żywotnik kolumnowy); Picea sp. w tle', 'żywopłot 2,0-2,5; kolumnowy ok. 5-6', 'żywopłot/szpaler', 'wczesna wiosna (bez liści)', 'Wizualne oszacowanie ±1 m względem płotu sztachetowego (1,2-1,6 m) i słupa latarni.', 'Wysoki ciemny żywopłot iglasty po lewej wzdłuż płotu drewnianego, żywotniki kolumnowe przy bramie; brak drzew przyulicznych; ulica asfaltowa z chodnikiem z kostki po jednej stronie.'),
    'G7-P02': ('Kowieńska', 'Picea pungens/abies; Thuja occidentalis kolumnowa', 'świerki ok. 8-12; żywotniki ok. 4-6', 'drzewo (ogród)', 'wczesna wiosna', 'Wizualne oszacowanie ±2 m (proporcja do dwukondygnacyjnego domu).', 'Zieleń tylko w ogrodzie za płotem sztachetowym/murowanym; iglaki zasłaniają front; brak nasadzeń w pasie drogowym.'),
    'G7-P03': ('Grodzieńska', 'Betula sp. (bez liści), Thuja, Picea', 'brzoza ok. 10-12', 'drzewo (ogród)/krzew', 'wczesna wiosna', 'Wizualne oszacowanie ±2 m.', 'Płot sztachetowy brązowy ok. 1,2 m; za nim niskie krzewy i iglaki; wysoka brzoza (bezlistna) nad dachem.'),
    'G7-P04': ('Wileńska', 'Picea pungens, Thuja occidentalis kolumnowa, drzewa liściaste bezlistne', 'świerk ok. 10-14; żywotnik ok. 6-8', 'szpaler/drzewo (ogród)', 'wczesna wiosna', 'Wizualne oszacowanie ±2 m.', 'Duże iglaki w narożnych ogrodach, płoty drewniane ok. 1,5 m; chodnik z kostki po jednej stronie.'),
    'G7-P05': ('Wileńska', 'krzewy niskie (Berberis/Cotoneaster? UNVERIFIED), Picea abies', 'krzewy 0,8-1,2; świerk 10-12', 'krzew + drzewo (ogród)', 'wczesna wiosna', 'Wizualne oszacowanie ±0,3 m (krzewy), ±2 m (świerk).', 'Niski żywopłot/obsadzenie krzewami przed płotem sztachetowym; wysoki świerk w narożniku skrzyżowania.'),
    'G7-P06': ('Wileńska', 'krzewy ozdobne niskie (gatunek UNVERIFIED), Picea, drzewa bezlistne', 'krzewy 0,7-1,2; drzewa 10-14', 'krzew + drzewo (ogród)', 'wczesna wiosna', 'Wizualne oszacowanie ±0,3 m (krzewy).', 'Szeroki pas niskich krzewów przed ceglano-sztachetowym ogrodzeniem; za nim bezlistne drzewa i świerki; brak drzew przyulicznych.'),
    'G7-P07': ('Lidzka', 'krzewy niskie (gatunek UNVERIFIED), Picea, drzewa liściaste bezlistne', 'krzewy 0,7-1,2; drzewa 10-14', 'krzew + drzewo (ogród)', 'wczesna wiosna', 'Wizualne oszacowanie ±0,3 m.', 'Narożnik: niskie krzewy przed murkiem ceglanym z płotkiem; bezlistne drzewa 10-14 m w ogrodach; słup latarniowy, brak drzew w pasie drogowym.'),
    'G7-P08': ('Wileńska', 'Forsythia sp., Picea pungens/abies, Thuja kolumnowa', 'forsycja 1,5-2; iglaki 6-10', 'krzew + drzewo (ogród)', 'wczesna wiosna (kwitnąca forsycja)', 'Wizualne oszacowanie ±1 m.', 'Zabudowa szeregowa/bliźniacza: forsycja i iglaki przy furtce; bezlistne drzewo; ulica bez drzew przyulicznych.'),
    'G7-P09': ('Racławicka', 'żywopłot liściasty niski strzyżony (gatunek UNVERIFIED, bez liści), Picea pungens', 'żywopłot 1,0-1,3; świerki 8-12', 'żywopłot/drzewo (ogród)', 'wczesna wiosna', 'Wizualne oszacowanie ±0,3 m.', 'Narożny żywopłot liściasty przy zjeździe, za nim niebieskie świerki; ulica sąsiednia względem rdzenia tile.'),
    'G7-P10': ('Aleja Tysiąclecia Państwa Polskiego (nazwa OSM; sąsiedztwo Andersa)', 'młode drzewo liściaste na 3 palikach (gatunek UNVERIFIED)', 'ok. 4-5', 'drzewo przyuliczne młode', 'lato (VII, ulistnione)', 'Wizualne oszacowanie ±1 m względem pieszego i płotu ok. 1,8 m.', 'Jedno z nielicznych nasadzeń przyulicznych: młode drzewko w trawniku między chodnikiem a ogrodzeniem; trawnik koszony.'),
    'G7-P11': ('Łańcucka', 'Thuja occidentalis (Smaragd/Brabant)', 'żywopłot 2,0-2,5 (nad płotem 1,3 m)', 'żywopłot', 'wczesna wiosna', 'Wizualne oszacowanie ±0,5 m względem płotu i balustrady balkonu.', 'Strzyżony żywopłot z żywotnika nad czerwonym płotem drewnianym i murowanymi słupkami; szerokość ok. 0,8-1,2 m.'),
    'G7-P12': ('Łańcucka', 'Thuja occidentalis (Brabant/Smaragd)', 'żywopłot 2,5-3,0', 'żywopłot', 'wczesna wiosna', 'Wizualne oszacowanie ±0,5 m względem okna/balustrady; zaokrąglony narożnik.', 'Bardzo wysoki gęsty żywopłot z żywotnika przystrzyżony w łuk na zakręcie; sięga okapu parterowej części domu.'),
}
for r in rows:
    ul, gat, h, typ, sez, met, uw = obs[r['id']]
    add(**{'id': r['id'], 'ulica': ul, 'lat': r['lat'], 'lon': r['lon'], 'gatunek': gat, H: h, 'typ': typ, 'sezon': sez,
           'metoda': met + ' Współrzędne = geotag Commons (pozycja aparatu; azymut UNVERIFIED).', 'url_źródła': r['page'],
           'licencja': r['lic'], 'autor': r['author'], 'status': 'ESTIMATED',
           'uwagi': uw + ' Plik: files/' + r['file'] + '. Zdjęcie ' + r['date'] + '; odległość od osi najbliższej ulicy z grafu drogowego tile: ' + str(r['dist']) + ' m.'})
add(id='G7-O01', ulica='tile (wszystkie)', gatunek='barrier=hedge', typ='żywopłot', metoda='pyosmium na lokalnym PBF podlaskie-261108 (2026-11-08), ways barrier=hedge przecinające bbox tile EPSG:2180 [776971,595199,779019,597247]; skrypt tools/osm_tile_greenery.py', **{'url_źródła': 'https://download.geofabrik.de/europe/poland/podlaskie-261108.osm.pbf'}, licencja='ODbL 1.0 (c) OpenStreetMap contributors', autor='społeczność OSM', status='SOURCED', uwagi='WYNIK 0 (zero) ways barrier=hedge w tile. OSM nie zawiera żywopłotów — brak wpisu nie dowodzi braku żywopłotu w terenie (zdjęcia G7-P01, P11, P12 pokazują ich dużo).')
add(id='G7-O02', ulica='tile (wszystkie)', gatunek='natural=tree_row', typ='szpaler', metoda='j.w.', **{'url_źródła': 'https://download.geofabrik.de/europe/poland/podlaskie-261108.osm.pbf'}, licencja='ODbL 1.0 (c) OpenStreetMap contributors', autor='społeczność OSM', status='SOURCED', uwagi='WYNIK 0 ways natural=tree_row w tile.')
add(id='G7-O03', ulica='(północny skraj tile, nie przy ulicy domów)', lat='53.163997', lon='23.148236', gatunek='Prunus avium (wiśnia ptasia), pomnik przyrody', **{H: '24 (tag height)'}, typ='drzewo', sezon='n/d', metoda='węzeł OSM 6763732952, tagi: height=24, circumference=2.61 m; ref:CRFOP 114945', **{'url_źródła': 'https://www.openstreetmap.org/node/6763732952'}, licencja='ODbL 1.0', autor='społeczność OSM (dane CRFOP/GDOŚ)', status='SOURCED', uwagi='Jedno z dwóch natural=tree w tile. Pomnik przyrody, nie typowe drzewo przyuliczne.')
add(id='G7-O04', ulica='(południowy skraj tile)', lat='53.149787', lon='23.148593', gatunek='Quercus robur (dąb szypułkowy), pomnik przyrody', **{H: '20 (tag height)'}, typ='drzewo', sezon='n/d', metoda='węzeł OSM 6763732994, height=20, circumference=3.2 m; ref:CRFOP 94088', **{'url_źródła': 'https://www.openstreetmap.org/node/6763732994'}, licencja='ODbL 1.0', autor='społeczność OSM (dane CRFOP/GDOŚ)', status='SOURCED', uwagi='Drugie natural=tree w tile (łącznie 2 węzły).')
add(id='G7-B01', ulica='tile (ulice domów: Kowieńska, Lidzka, Skidelska, Wołkowyska, Świsłocka, Wileńska, Grodzieńska)', gatunek='OT_OIPR_P "drzewo lub grupa drzew"', typ='drzewo', metoda='Data/Regions/bialystok-industrial-c/generated/streetscape_sources.json (BDOT10k, wycinek tile): 71 punktów drzewo/grupa drzew, 15 kępa krzewów, 7 mały las; w buforze 12 m od osi ulic domów: 0 punktów (tools/tile_crowns_and_frames.py)', **{'url_źródła': 'https://www.geoportal.gov.pl (BDOT10k powiat 2061; plik lokalny Data/raw/gugik/bdot10k-2061)'}, licencja='dane otwarte GUGiK (art. 40a ust. 2 pkt 1 Pgik)', autor='GUGiK', status='SOURCED', uwagi='BDOT10k 1:10 000 nie inwentaryzuje drzew przyulicznych ani ogrodowych; brak gatunku i wysokości. Użyteczne tylko jako dowód braku większych skupisk.')
meas = [('G7-T01', 'Quercus robur (dąb szypułkowy)', '18', 'ul. Słonimska, Białystok', 'dojrzałe, ok. 180 lat; obwód pnia 263 cm; DBH 84 cm; CBH 3 m; korona 10x13 m'),
        ('G7-T02', 'Populus x canadensis (topola kanadyjska)', '22', 'Park Stary przy Pl. Piłsudskiego', 'ok. 90 lat; obwód 350 cm; DBH 111,5; CBH 10 m; korona 25x22 m'),
        ('G7-T03', 'Acer platanoides (klon zwyczajny)', '20', 'Zespół pałacowo-ogrodowy Branickich (sąsiedztwo ul. Legionowej)', 'sędziwe, ok. 170 lat; obwód 300 cm; DBH 96; CBH 3 m; korona 18x22 m (park, drzewo solitarne)'),
        ('G7-T04', 'Tilia cordata (lipa drobnolistna)', '7', 'Rynek Kościuszki przy ratuszu', 'młode, ok. 20 lat; obwód 58 cm; DBH 18,5; CBH 1,3 m; korona 4,6x5,4 m')]
for i, g, h, loc, u in meas:
    add(**{'id': i, 'ulica': loc, 'gatunek': g, H: h, 'typ': 'drzewo', 'sezon': 'n/d',
           'metoda': 'Pomiar dendrometryczny + i-Tree Eco (Tab. 2, s. 15 dokumentu), SGGW dla UM Białystok, 15.09.2022: Total Tree Height, Crown Base Height, Crown Width NS/EW',
           'url_źródła': 'https://www.bialystok.pl/resource/26984/66421/Ekspertza+-+wycena+us%25C5%2582ug+ekosystemowych.pdf',
           'licencja': 'dokument urzędowy (art. 4 pkt 2 pr. aut.; zamówiony przez UM Białystok)', 'autor': 'M. Suchocka, K. Kais (SGGW) dla UM Białystok', 'status': 'SOURCED',
           'uwagi': u + '. Lokalizacja bez współrzędnych w źródle (UNVERIFIED). Tab. 2 w pdftotext ma przemieszane kolumny; przyporządkowanie odtworzone z kolejności DBH 84/111,5/96/18,5 zgodnej z obwodami 263/350/300/58 cm.'})
sp = [('G7-S01', 'Tilia cordata (lipa drobnolistna)', '20-25', 'jajowata, zwarta; szer. 10-15 m', 'https://www.ebben.nl/pl/treeebb/ticordat-tilia-cordata/pdf/'),
      ('G7-S02', 'Acer platanoides (klon zwyczajny)', '20-30', 'kulista, zwarta; szer. 15-20 m', 'https://www.ebben.nl/pl/treeebb/acplatan-acer-platanoides/pdf'),
      ('G7-S03', 'Fraxinus excelsior (jesion wyniosły)', '25-30', 'kulista, półotwarta; szer. 20-25 m', 'https://www.ebben.nl/pl/treeebb/frexcels-fraxinus-excelsior/pdf/'),
      ('G7-S04', 'Aesculus hippocastanum (kasztanowiec biały)', '20-30', 'kulista/owalna/szerokojajowata, zwarta; szer. 16-20 m', 'https://www.ebben.nl/pl/treeebb/aehippoc-aesculus-hippocastanum/pdf'),
      ('G7-S05', 'Betula pendula (brzoza brodawkowata)', '15-20', 'wąskojajowata, otwarta; szer. 6-12 m', 'https://www.ebben.nl/pl/treeebb/bependul-betula-pendula/pdf/'),
      ('G7-S06', 'Tilia x europaea (lipa holenderska)', '30-40', 'szerokopiramidalna, półotwarta; szer. 15-20 m', 'https://www.ebben.nl/pl/treeebb/tieuropa-tilia-x-europaea/pdf/'),
      ('G7-S07', 'Carpinus betulus (grab pospolity)', '15-20', 'szerokojajowata, zwarta; szer. 12-15 m', 'https://www.ebben.nl/pl/treeebb/cabetulu-carpinus-betulus/pdf'),
      ('G7-S08', 'Picea abies (świerk pospolity)', '30-55', 'wąskopiramidalna, zwarta; szer. 8-10 m', 'https://www.ebben.nl/pl/treeebb/piabies-picea-abies/pdf/'),
      ('G7-S09', 'Thuja occidentalis Smaragd', '4-6', 'kolumnowa, zwarta; szer. 1-1,8 m', 'https://www.ebben.nl/pl/treeebb/thosmara-thuja-occidentalis-smaragd/pdf'),
      ('G7-S10', 'Thuja occidentalis Brabant', '15-20', 'piramidalna, zwarta; szer. 3-6 m', 'https://www.ebben.nl/pl/treeebb/thobraba-thuja-occidentalis-brabant/pdf/'),
      ('G7-S11', 'Ligustrum vulgare Atrovirens (ligustr)', '3-4 (krzew)', 'szer. 3-4 m', 'https://www.ebben.nl/pl/treeebb/livatrov-ligustrum-vulgare-atrovirens/pdf'),
      ('G7-S12', 'Tilia cordata Greenspire (odmiana ulicowa)', '16-20', 'wąskojajowata/piramidalna, zwarta; szer. 7-10 m', 'https://www.ebben.nl/pl/treeebb/ticgreen-tilia-cordata-greenspire/pdf/')]
for i, g, h, k, u in sp:
    add(**{'id': i, 'ulica': 'gatunek - wymiary katalogowe (nie Białystok)', 'gatunek': g, H: h, 'typ': 'parametr gatunku', 'sezon': 'n/d',
           'metoda': 'karta TreeEbb (szkółka Ebben, NL): pola Wysokość/Szerokość/Kształt/Struktura korony; odczyt 2026-11-13 z PDF (pdftotext). ' + k,
           'url_źródła': u, 'licencja': 'fakty botaniczne (zakresy liczbowe); nie kopiowano tekstu ani zdjęć', 'autor': 'Ebben (katalog TreeEbb)', 'status': 'SOURCED',
           'uwagi': 'Wymiary dojrzałego drzewa wg szkółki holenderskiej (klimat cieplejszy niż Białystok); w mieście bywają niższe (por. G7-T03: klon 170 lat = 20 m). W generatorze używać jako SUFIT, nie średnią. Dla Thuja Brabant i Smaragd: wysokość drzewa niestrzyżonego; żywopłot strzyżony niższy (G7-P11/P12).'})
agg = json.load(open(OUT + 'tools/house_streets_agg.json', encoding='utf-8'))
for key, i in (('all7 d=8', 'G7-C01'), ('all7 d=12', 'G7-C02'), ('Kowienska-Wolkowyska-Lidzka-Swislocka-Wilenska (tile core) d=8', 'G7-C03'), ('Skidelska d=8', 'G7-C04')):
    a = agg[key]
    add(**{'id': i, 'ulica': key.replace(' d=', ' ; bufor od osi (m): '), 'gatunek': 'korony z ortofoto (bez rozróżnienia gatunków; iglaste wg jasności)',
           'typ': 'statystyka koron', 'sezon': 'V 2024 (ortofoto 2024-05-27, ulistnione)',
           'metoda': 'Data/Regions/bialystok-industrial-c/plot_canopy.json (detektor kanał G/luma na ortofoto GUGiK 0,25 m; wygenerowany w repo) + tools/house_streets_agg.py. Długość ulic %.0f m; korony r>=1,25 m = drzewa, r<1,25 m = krzewy.' % a['L'],
           'url_źródła': 'https://mapy.geoportal.gov.pl (ORTO 2024; plik lokalny)', 'licencja': 'dane otwarte GUGiK', 'autor': 'GUGiK; detektor: projekt', 'status': 'ESTIMATED',
           'uwagi': 'drzew %d (%.1f/100 m osi, obie strony łącznie), krzewów %d (%.1f/100 m); iglastych %d%% (detektor prawdopodobnie zaniża, por. zdjęcia); promień korony: mediana %.2f m, kwartyle %.2f-%.2f, p90 %.2f; koron r>=4 m: %d.' % (a['trees'], a['trees_per100m'], a['shrubs'], a['shrubs_per100m'], round(a['conifer_share_trees'] * 100), a['r_med'], a['r_p25'], a['r_p75'], a['r_p90'], a['big_ge4'])})
add(id='G7-C05', ulica='Andersa / Aleja Tysiąclecia (odcinek ok. 53,157 N 23,152 E)', lat='53.1568', lon='23.1519', typ='kontrola wzrokowa ortofoto', sezon='V 2024',
    metoda='przycięcie ortofoto 260x300 m obejrzane wzrokowo', **{'url_źródła': 'ortofoto GUGiK 2024 (lokalnie)'}, licencja='dane otwarte GUGiK', autor='GUGiK', status='ESTIMATED',
    uwagi='Jezdnie i pas środkowy (trawa) bez widocznych koron dojrzałych drzew; zieleń to dzikie zadrzewienia po wschodniej stronie i ogrody zabudowy jednorodzinnej po zachodniej. Młode palikowane drzewka (G7-P10) są poniżej rozdzielczości.')
add(id='G7-M01', ulica='analogiczne ulice domów w Białymstoku (Mickiewicza/Bojary, Piasta II, Zaścianki, Jakimy) - 27 kadrów', typ='próba kadrów (front posesji od ulicy)', sezon='VII-IX 2017-2024',
    metoda='Wzrokowa klasyfikacja 27 kadrów Mapillary (Data/raw/mapillary/posesje, P06-P33 bez P11): H = ciągły żywopłot/krzewy >=1,2 m, S = niskie krzewy/kwiaty/bluszcz, N = samo ogrodzenie. Wynik: H 7 (26%), S 6 (22%), N 14 (52%). Lista: mapillary_sample.csv',
    **{'url_źródła': 'https://www.mapillary.com/app/?pKey=<id> (id w mapillary_sample.csv)'}, licencja='CC BY-SA 4.0 (zdjęcia nie kopiowane do files/; tylko klasyfikacja)', autor='autorzy Mapillary (w manifeście repo)', status='ESTIMATED',
    uwagi='Jednostka = kadr, nie posesja (kadr obejmuje 1-8 posesji); próba mała, jeden klasyfikujący; ulice poza tile. Mapillary API bez tokenu niedostępne - użyto kadrów już pobranych do repo (manifest w repo).')
add(id='G7-M02', ulica='Andersa (Aleja Tysiąclecia / Bieżeństwa) - ok. 30 kadrów w tile', typ='próba kadrów (pas drogowy)', sezon='VII-X 2017-2024',
    metoda='Przegląd arkuszy kadrów Mapillary przy osi Andersa (ID kadrów w Data/raw/mapillary/posesje/manifest.jsonl, lat 53,150-53,161): pas środkowy i pobocza trawiaste, młode palikowane drzewka (2024), po zachodniej stronie gęste dzikie zadrzewienie 8-15 m, w ogrodach świerki Picea pungens/abies i klon (Acer) przy przejściu, ekrany akustyczne, wyspy ronda: sucha trawa bez krzewów',
    **{'url_źródła': 'https://www.mapillary.com/app/?pKey=<id>'}, licencja='CC BY-SA 4.0 (nie kopiowano)', autor='autorzy Mapillary', status='ESTIMATED',
    uwagi='Liczba drzew/100 m dla Andersa UNVERIFIED - brak zliczenia; wniosek jakościowy.')
add(id='G7-U01', ulica='Andersa, Wileńska, Sokólska', typ='UNVERIFIED',
    metoda='Brak miejskiego rejestru drzew w otwartych danych bialystok.pl (katalog Data/raw/refs/bialystok-open-data: parki, skwery, lasy, pomniki przyrody); WebSearch 2026-11-13 nie znalazł inwentaryzacji drzew przyulicznych ani projektów nasadzeń ZDM z gatunkami dla tych ulic',
    **{'url_źródła': 'brak'}, licencja='n/d', autor='n/d', status='UNVERIFIED',
    uwagi='Proporcje gatunków drzew przyulicznych Białegostoku nie są udokumentowane; wartości gatunkowe w README = WORKING_VALUE. Do uzupełnienia: wniosek o informację publiczną do ZDM/Wydziału Ochrony Środowiska UM Białystok (inwentaryzacja drzew w pasach drogowych).')
with open(OUT + 'manifest.csv', 'w', newline='', encoding='utf-8-sig') as f:
    w = csv.DictWriter(f, fieldnames=cols)
    w.writeheader()
    w.writerows(M)
print(len(M), collections.Counter(r['status'] for r in M))
# mapillary sample
cls = {'H': ['P07', 'P08', 'P09', 'P10', 'P12', 'P14', 'P19'], 'S': ['P06', 'P13', 'P16', 'P17', 'P28', 'P29']}
fr = [json.loads(l) for l in open(R + 'Data/raw/mapillary/posesje/manifest.jsonl', encoding='utf-8')]
out = []
for f in fr:
    ref = f.get('ref')
    if not ref or ref == 'P11':
        continue
    c = 'H' if ref in cls['H'] else ('S' if ref in cls['S'] else 'N')
    out.append([ref, f['id'], f['lat'], f['lon'], round(f['compass_angle']), f['captured_at'], c, 'https://www.mapillary.com/app/?pKey=' + f['id'], 'CC BY-SA 4.0', f['author']])
out.sort()
with open(OUT + 'mapillary_sample.csv', 'w', newline='', encoding='utf-8-sig') as fh:
    w = csv.writer(fh)
    w.writerow(['ref', 'mapillary_id', 'lat', 'lon', 'azymut_deg', 'data', 'klasa_frontu(H/S/N)', 'url', 'licencja', 'autor'])
    w.writerows(out)
print(len(out), collections.Counter(o[6] for o in out))
