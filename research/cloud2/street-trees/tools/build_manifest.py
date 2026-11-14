# -*- coding: utf-8 -*-
"""Buduje manifest.csv pakietu R5 (street-trees) z danych w data/ i opisów kadrów (tools/frame_notes.py).
Uruchom z katalogu pakietu:  uv run --with shapely --with pyproj python -I tools/build_manifest.py
(-I: bez katalogu bieżącego na sys.path; tools/ dodawane jawnie niżej).
"""
import csv, json, os, sys, math
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import frame_notes  # noqa: E402
from shapely.geometry import LineString, Point  # noqa: E402
from shapely.strtree import STRtree  # noqa: E402
from pyproj import Transformer  # noqa: E402

D = lambda *p: os.path.join(ROOT, 'data', *p)
ACC = '2026-11-14'
COLS = ['id', 'kategoria', 'przedmiot', 'wartość', 'jednostka', 'status', 'metoda', 'cytat', 'url_źródła', 'url_pliku',
        'licencja', 'autor', 'data_dostępu', 'sha256', 'lat', 'lon', 'kierunek_deg', 'opis_co_widać', 'duplikat_sha256',
        'uwagi', 'obszar', 'data_zdjęcia', 'sezon', 'ulica_osm_najbliższa', 'odległość_od_osi_m', 'front', 'żywopłot',
        'plik_lokalny', 'sha_stabilny']
rows = []
def add(kat, przedmiot, wart, jedn, status, metoda, cytat='', url='', url_pliku='', lic='', autor='', sha='', uwagi='', **kw):
    r = dict.fromkeys(COLS, '')
    r.update({'id': 'R5-%03d' % (len(rows) + 1), 'kategoria': kat, 'przedmiot': przedmiot, 'wartość': wart, 'jednostka': jedn,
              'status': status, 'metoda': metoda, 'cytat': cytat, 'url_źródła': url, 'url_pliku': url_pliku, 'licencja': lic,
              'autor': autor, 'data_dostępu': ACC, 'sha256': sha, 'uwagi': uwagi})
    r.update(kw)
    rows.append(r)
    return r['id']

# ---------------------------------------------------------------- źródła (stałe)
PBF = 'https://download.openstreetmap.fr/extracts/europe/poland/podlaskie.osm.pbf'
PBF_SHA = '82939b5fdbe78f09a4f85a08086c2eb228b6c14e002f13516a24e6d90dfa396c'
OSM = dict(url=PBF, lic='ODbL 1.0 (© autorzy OpenStreetMap)', autor='OpenStreetMap contributors', sha=PBF_SHA,
           plik_lokalny='files/osm/podlaskie.osm.pbf', sha_stabilny='nie (ekstrakt dzienny; stan 2026-11-13T01:06:06Z)')
M_OSM = ('pyosmium na ekstrakcie PBF (state 2026-11-13T01:06:06Z, pobrano 2026-11-14 17:10 UTC), granica = relacja 2910925 '
         '(admin_level=8 Białystok); tools/osm_extract_trees.py + tools/osm_stats.py; zapytanie równoważne: tools/q_trees.overpassql '
         '(Overpass nieosiągalny 17:05–17:10 UTC)')
M_ROW = ('tools/row_spacing.py: drzewo → najbliższa oś jezdni OSM ≤ 15 m (EPSG:2180), pikietaż wzdłuż osi, strona L/P; '
         'szpaler = ≥ 4 drzewa po tej samej stronie tej samej drogi z odstępem ≤ 30 m i |Δodsunięcia| ≤ 3 m')
LASKA = dict(url='https://doi.org/10.1515/biorc-2015-0013', lic='© UAM Poznań, all rights reserved — tylko cytat (plik nie w fetch.py)',
             autor='Grażyna Łaska (2015), Biodiv. Res. Conserv. 38: 9–24')
NIK = dict(url='https://www.nik.gov.pl/kontrole/wyniki-kontroli-nik/pobierz,lbi~i_23_006_202410081310371728385837~id0~01,typ,kj.pdf',
           url_pliku='https://www.nik.gov.pl/kontrole/wyniki-kontroli-nik/pobierz,lbi~i_23_006_202410081310371728385837~id0~01,typ,kj.pdf',
           lic='dokument urzędowy (informacja publiczna)', autor='NIK Delegatura w Białymstoku, LBI.403.7.2023',
           sha='28913903f9c5e79a4f9d42d46a873c6443853188e77708511b2789bead3ab8e6', plik_lokalny='files/docs/nik_bialystok_2024.pdf', sha_stabilny='tak')
BIP_PAGE = 'https://www.bip.bialystok.pl/postepowania/zamowienia/kompleksowa-pielegnacja-drzew-i-krzewow-w-pasach-drogowych-na-terenie-miasta-bialegostoku-wraz-z-nasadzeniami.html'
BIP2 = dict(url=BIP_PAGE, url_pliku='https://www.bip.bialystok.pl/resource/19414/Za%25C5%2582%25C4%2585ccznik+nr+2+-+Szczeg%25C3%25B3%25C5%2582owy+opis+przedmiotu+zam%25C3%25B3wienia.pdf',
            lic='dokument urzędowy BIP (informacja publiczna)', autor='UM Białystok, Departament Gospodarki Komunalnej, DGK-IV.271.2.2017, zał. nr 2',
            sha='9aeff6bacafdb7e7b488008515508afb8f666206cfd1e63b1d2c9946ed22b592', plik_lokalny='files/docs/bip2017_zal2_opz.pdf', sha_stabilny='tak')
BIP3 = dict(url=BIP_PAGE, url_pliku='https://www.bip.bialystok.pl/resource/19414/Za%25C5%2582%25C4%2585cznik+nr+3+-+Wykaz+lokalizacji+wraz+z+ilo%25C5%259Bci%25C4%2585+ro%25C5%259Blin+do+piel%25C4%2599gancji+obj%25C4%2599tych+umow%25C4%2585.pdf',
            lic='dokument urzędowy BIP (informacja publiczna)', autor='UM Białystok, Departament Gospodarki Komunalnej, DGK-IV.271.2.2017, zał. nr 3',
            sha='426f4e2bb26b6e8f1e0f5eeb35391f25a89cf1ddf4b5c170beeb7db6bb8b4661', plik_lokalny='files/docs/bip2017_zal3_wykaz.pdf', sha_stabilny='tak')
Z2019 = dict(url='https://www.bialystok.pl/resource/14062/32307/Ziele%25C5%2584+w+Bia%25C5%2582ymstoku+2019.pdf',
             url_pliku='https://www.bialystok.pl/resource/14062/32307/Ziele%25C5%2584+w+Bia%25C5%2582ymstoku+2019.pdf',
             lic='dokument urzędowy UM Białystok', autor='UM Białystok, „Zieleń w Białymstoku 2019”',
             sha='283813dca695d4e4bb2efe1d7254544d405f3e499a25c2d83a50f1af84d2a1a6', plik_lokalny='files/docs/zielen_bialystok_2019.pdf', sha_stabilny='tak')
DU22 = dict(url='https://eli.gov.pl/eli/DU/2022/1518/ogl', url_pliku='https://eli.gov.pl/api/acts/DU/2022/1518/text/O/D20221518.pdf',
            lic='akt prawny (Dz.U.) — domena publiczna', autor='Minister Infrastruktury, rozp. z 24.06.2022, Dz.U. 2022 poz. 1518',
            sha='fe1380ff495c2f293e6d2ab19a5b164105cc776845702f16e0cf54dbaf2da9c5', plik_lokalny='files/docs/D20221518.pdf', sha_stabilny='tak')
DU16 = dict(url='https://eli.gov.pl/eli/DU/2016/124/ogl', url_pliku='https://eli.gov.pl/api/acts/DU/2016/124/text/O/D20160124.pdf',
            lic='akt prawny (Dz.U.) — domena publiczna', autor='obwieszczenie MIiB — t.j. rozp. MTiGM z 2.03.1999, Dz.U. 2016 poz. 124',
            sha='c83b35b8f999fd780c2fe7548ed099a22c3d33c7a813f5676211ca2825b410b1', plik_lokalny='files/docs/D20160124.pdf', sha_stabilny='tak')
UTD = dict(url='https://doi.org/10.2737/RDS-2016-0005', url_pliku='https://www.fs.usda.gov/rds/archive/products/RDS-2016-0005/RDS-2016-0005.zip',
           lic='dane rządu USA (USDA Forest Service Research Data Archive; brak ograniczeń użycia w metadanych)',
           autor='McPherson E.G., van Doorn N.S., Peper P.J. (2016) Urban tree database; opis: PSW-GTR-253, doi:10.2737/PSW-GTR-253',
           sha='c0c888e2531ca58b673b7c18a30a01cbd33e90bd8b041fb3483e394bd8664faf', plik_lokalny='files/docs/utd/RDS-2016-0005.zip', sha_stabilny='tak')
M_UTD = ('tools/utd_allometry.py na TS3_Raw_tree_data.csv: mediana i kwartyle pomierzonych drzew ulicznych w regionach chłodnych '
         '(MidWst Minneapolis, NoEast Queens, LoMidW Indianapolis, NMtnPr Fort Collins; gdy gatunku brak — TpIntW/PacfNW/InlVal); '
         'klasy obwodu = π·DBH (pierśnica 1,37 m), jak klasy Łaski 2015 (obwód na 1,2 m)')
EKR = lambda pid, slug, who: dict(url=f'https://e-katalogroslin.pl/plants/{pid},{slug}', lic='© Związek Szkółkarzy Polskich — tylko cytat (plik nie w fetch.py)',
                                  autor=who, sha_stabilny='nie (PDF generowany przy pobraniu)')
PMC = dict(url='https://doi.org/10.1007/s00484-018-1534-2', lic='CC BY 4.0', autor='Czernecki B., Nowosad J., Jabłońska K. (2018) Int. J. Biometeorol. 62: 1297–1309 (PMC6028898)')
PMC_FIG = dict(PMC, url_pliku='https://cdn.ncbi.nlm.nih.gov/pmc/blobs/2596/6028898/4d8b5330cc86/484_2018_1534_Fig2_HTML.jpg',
               sha='a7e145742d7b805692fee1bf4183434cf0aa5e4a845e2aa80baf3642f91cccce', plik_lokalny='files/docs/pheno/fig2.jpg', sha_stabilny='tak')
M_FIG = ('odczyt z Fig. 2 (wykres pudełkowy, 52 stacje IMGW-PIB, 2007–2014, cała Polska): pozycja mediany i pudełka (p25–p75) w pikselach '
         'obrazu powiększonego do 1900 px, oś: 1 I = 215 px, 1 XII = 1756 px → 4,614 px/dzień; kontrola: Fl.Cor. odczyt 70 = tekst 70, '
         'Lf.Bet. odczyt 301 = tekst 301; niepewność ±3 dni')

# ================================================================ A. OSM
st = json.load(open(D('osm_stats.json')))
rs = json.load(open(D('row_spacing.json')))
b = st['bialystok']
add('osm', 'natural=tree w granicach Białegostoku — liczba węzłów', b['n_tree'], 'szt.', 'ESTIMATED', M_OSM, **OSM)
add('osm', 'kompletność tagu species (natural=tree, Białystok)', b['tag_pct']['species'], '%', 'ESTIMATED', M_OSM,
    uwagi=f"{b['tag_count']['species']} z {b['n_tree']}; species:pl {b['tag_pct']['species:pl']} %, taxon 0 %", **OSM)
add('osm', 'kompletność tagu genus', b['tag_pct']['genus'], '%', 'ESTIMATED', M_OSM, uwagi=f"{b['tag_count']['genus']} z {b['n_tree']}", **OSM)
lt = dict(b['leaf_type'])
add('osm', 'kompletność tagu leaf_type', b['tag_pct']['leaf_type'], '%', 'ESTIMATED', M_OSM,
    uwagi=f"broadleaved {lt.get('broadleaved')}, needleleaved {lt.get('needleleaved')}, brak {lt.get('(brak)')}; wśród otagowanych iglaste = "
          f"{round(100 * lt.get('needleleaved', 0) / (lt.get('broadleaved', 0) + lt.get('needleleaved', 0)), 1)} %", **OSM)
add('osm', 'kompletność tagu height', b['tag_pct']['height'], '%', 'ESTIMATED', M_OSM,
    uwagi=f"n = {len(b['height_m'])} wartości liczbowych, zakres {b['height_m'][0]}–{b['height_m'][-1]} m; circumference {b['tag_pct']['circumference']} %, diameter_crown 0 %", **OSM)
sp = b['species']
add('osm', 'gatunki w tagu species — najczęstszy', f"{sp[0][0]}: {sp[0][1]}", 'szt.', 'ESTIMATED', M_OSM,
    uwagi='pozostałe: ' + ', '.join(f'{a} {n}' for a, n in sp[1:]) + f"; denotation=natural_monument: {dict(b['denotation']).get('natural_monument')} — tag species opisuje głównie pomniki przyrody i aleje dębowe, NIE skład drzew ulicznych", **OSM)
add('osm', 'natural=tree_row w Białymstoku', b['n_tree_row'], 'szt. (linie)', 'ESTIMATED', M_OSM, uwagi='tagi: tylko leaf_type (broadleaved/mixed), bez gatunków', **OSM)
add('osm', 'barrier=hedge w Białymstoku', b['n_hedge'], 'szt. (linie)', 'ESTIMATED', M_OSM, uwagi=f"tag height tylko na {dict(b['hedge_tag_keys']).get('height', 0)}; brak species", **OSM)
c = st['trasa_c']
add('osm', 'trasa C (kafel 53,1499–53,1672 N; 23,1437–23,1761 E): natural=tree / tree_row / hedge', f"{c['n_tree']} / {c['n_tree_row']} / {c['n_hedge']}", 'szt.', 'ESTIMATED', M_OSM,
    uwagi='jedyne drzewo: Prunus avium, 24 m, pomnik przyrody (zgodne z G7 #29; drugi pomnik z G7 leży 13 m poniżej południowej krawędzi kafla)', obszar='trasa_c', **OSM)
dj = st['dojlidy']
add('osm', 'Dojlidy (kafel 53,096–53,114 N; 23,176–23,206 E): natural=tree / tree_row / hedge', f"{dj['n_tree']} / {dj['n_tree_row']} / {dj['n_hedge']}", 'szt.', 'ESTIMATED', M_OSM,
    uwagi='5 drzew bez gatunku (4 broadleaved, 1 needleleaved) — OSM bezużyteczny dla Dojlid', obszar='dojlidy', **OSM)
add('szpaler', 'szpalery wykryte z OSM (Białystok): liczba rzędów / drzew w rzędach', f"{rs['n_rows']} / {rs['n_trees_in_rows']}", 'szt.', 'ESTIMATED', M_ROW,
    uwagi=f"{rs['n_trees_within_15m_of_road_axis']} z {rs['n_trees_total']} drzew OSM leży ≤ 15 m od osi jezdni; 0 rzędów w kaflu trasy C i w Dojlidach", **OSM)
g = rs['gap_m']
add('szpaler', 'odstęp między sąsiednimi drzewami w szpalerze — mediana (wszystkie odstępy)', g['median'], 'm', 'ESTIMATED', M_ROW,
    uwagi=f"n = {g['n']} odstępów; p10 {g['p10']}, p25 {g['p25']}, p75 {g['p75']}, p90 {g['p90']}", **OSM)
g2 = rs['gap_m_per_row_median']
add('szpaler', 'odstęp typowy rzędu (mediana median rzędów)', g2['median'], 'm', 'ESTIMATED', M_ROW,
    uwagi=f"n = {g2['n']} rzędów; p10 {g2['p10']}, p25 {g2['p25']}, p75 {g2['p75']}, p90 {g2['p90']}", **OSM)
a = rs['axis_offset_m']
add('szpaler', 'odsunięcie pnia od osi jezdni OSM — mediana', a['median'], 'm', 'ESTIMATED', M_ROW,
    uwagi=f"n = {a['n']} drzew; p10 {a['p10']}, p25 {a['p25']}, p75 {a['p75']}, p90 {a['p90']}; oś OSM na drogach dwujezdniowych = oś jednej jezdni", **OSM)
k = rs['kerb_offset_m_est']
add('szpaler', 'odsunięcie pnia od krawężnika — oszacowanie', k['median'], 'm', 'ESTIMATED',
    M_ROW + '; krawężnik = oś − połowa szerokości jezdni (tag width, inaczej lanes × 3,25 m, inaczej 5,5 m dla residential / 7 m) — szerokości pasów to WORKING_VALUE',
    uwagi=f"p10 {k['p10']}, p25 {k['p25']}, p75 {k['p75']}, p90 {k['p90']}; niepewność ±1 m (dokładność geometrii OSM i założonej szerokości); ogon > 6 m = rzędy za chodnikiem/na skwerach", **OSM)
import statistics as S
for cls, lab in (('residential', 'ulice lokalne (highway=residential)'), ('tertiary', 'ulice zbiorcze (tertiary)'), ('secondary', 'ulice główne (secondary)')):
    R = [r for r in rs['rows'] if r['highway'] == cls]
    add('szpaler', f'odstęp w rzędzie — {lab}: mediana median rzędów', round(S.median(r['gap_median'] for r in R), 2), 'm', 'ESTIMATED', M_ROW,
        uwagi=f"{len(R)} rzędów, {sum(r['n'] for r in R)} drzew; odsunięcie od krawężnika (oszac.) mediana {round(S.median(r['kerb_offset_median'] for r in R), 2)} m", **OSM)
L = [r for r in rs['rows'] if r['name'] == 'Lipowa']
add('szpaler', 'ul. Lipowa — drzewa w rzędach OSM / odstęp', f"{sum(r['n'] for r in L)} / {min(r['gap_median'] for r in L)}–{max(r['gap_median'] for r in L)}", 'szt. / m', 'ESTIMATED', M_ROW,
    uwagi=f"{len(L)} rzędów; odsunięcie od osi mediana {round(S.median(r['axis_offset_median'] for r in L), 2)} m; kontrola krzyżowa: BIP 2017 zał. 3 podaje dla Lipowej 97 drzew liściastych (R5 wiersz BIP) — OSM na Lipowej jest kompletny",
    lat=53.133628, lon=23.151303, **OSM)
P = [r for r in rs['rows'] if r['name'] == 'Świętego Ojca Pio']
add('szpaler', 'ul. Świętego Ojca Pio — drzewa w rzędach OSM / odstęp', f"{sum(r['n'] for r in P)} / {min(r['gap_median'] for r in P)}–{max(r['gap_median'] for r in P)}", 'szt. / m', 'ESTIMATED', M_ROW,
    uwagi='najgęstszy szpaler w mieście (młode nasadzenia w gęstym rozstawie); BIP 2017 zał. 3: 150 drzew liściastych od Mickiewicza do Zwierzynieckiej', lat=53.118441, lon=23.168132, **OSM)
W = [r for r in rs['rows'] if r['name'] in ('Wspólna', 'Pracownicza', 'Zielna', 'Krucza', 'Zachodnia')]
add('szpaler', 'ulice domów z rzędami drzew (Wspólna, Pracownicza, Zielna, Krucza, Zachodnia — os. Nowe Miasto): odstęp / odsunięcie od osi',
    f"{round(S.median(r['gap_median'] for r in W), 2)} / {round(S.median(r['axis_offset_median'] for r in W), 2)}", 'm / m', 'ESTIMATED', M_ROW,
    uwagi=f"{len(W)} rzędów, {sum(r['n'] for r in W)} drzew; odsunięcie od osi ~4–5 m przy jezdni ~5,5 m → pień ok. 1,2–2,4 m od krawężnika (w pasie trawnika między jezdnią a chodnikiem)", lat=53.108303, lon=23.136007, **OSM)

# ================================================================ B. Łaska 2015
T1 = 'Tab. 1 (s. 12): „Number of species and individuals of the synanthropic flora … along the four main roads in Białystok”'
M_L = 'odczyt tabeli z PDF artykułu (pdftotext -layout); inwentaryzacja terenowa 2011, 4 transekty 100 × 30 m po obu stronach ulicy (Raginisa 200 m)'
add('gatunki', 'inwentaryzacja dendroflory przy 4 głównych drogach (2011): osobniki / gatunki', '837 / 36', 'szt.', 'SOURCED', M_L,
    cytat='„the presence of 837 trees and bushes representing a total of 36 species including 25 tree species (69.4%) and 11 bush species (30.6%)”',
    uwagi='już cytowane w research/gptpro/p10-street-greenery-2 (P10-002…004); tu pełna tabela gatunków i klasy wysokości', **LASKA)
TREES = [('Acer platanoides', 'klon zwyczajny', (10, 30, 131, 124)), ('Acer negundo', 'klon jesionolistny', (18, 35, 0, 0)), ('Tilia cordata', 'lipa drobnolistna', (9, 0, 14, 26)),
         ('Prunus domestica', 'śliwa domowa', (6, 10, 6, 9)), ('Thuja sp.', 'żywotnik', (30, 0, 0, 0)), ('Betula pendula', 'brzoza brodawkowata', (4, 14, 0, 3)),
         ('Acer pseudoplatanus', 'klon jawor', (0, 0, 10, 10)), ('Acer tataricum', 'klon tatarski', (0, 16, 0, 0)), ('Malus sylvestris', 'jabłoń dzika', (9, 2, 2, 1)),
         ('Salix fragilis', 'wierzba krucha', (2, 2, 0, 7)), ('Fraxinus excelsior', 'jesion wyniosły', (0, 6, 1, 1)), ('Sorbus aucuparia', 'jarząb pospolity', (0, 8, 0, 0)),
         ('Robinia pseudoacacia', 'robinia akacjowa', (7, 0, 0, 0)), ('Pinus sylvestris', 'sosna zwyczajna', (0, 0, 3, 3)), ('Liriodendron tulipifera', 'tulipanowiec', (6, 0, 0, 0)),
         ('Quercus rubra', 'dąb czerwony', (1, 2, 2, 0)), ('Populus nigra', 'topola czarna', (0, 0, 0, 5)), ('Populus balsamifera', 'topola balsamiczna', (0, 5, 0, 0)),
         ('Salix caprea', 'wierzba iwa', (0, 3, 0, 0)), ('Picea pungens', 'świerk kłujący', (3, 0, 0, 0)), ('Morus nigra', 'morwa czarna', (0, 0, 3, 0)),
         ('Quercus robur', 'dąb szypułkowy', (0, 0, 0, 2)), ('Picea abies', 'świerk pospolity', (2, 0, 0, 0)), ('Magnolia acuminata', 'magnolia', (1, 0, 0, 1)),
         ('Rhus typhina', 'sumak octowiec', (1, 0, 0, 0))]
TOT = sum(sum(t[2]) for t in TREES)
assert len(TREES) == 25, len(TREES)
json.dump({'source': 'Łaska 2015 Tab. 1', 'transects': ['Raginisa', 'Andersa', 'Narodowych Sił Zbrojnych', 'Jana Pawła II'],
           'trees': [{'species': s, 'pl': p, 'counts': c, 'total': sum(c), 'share_pct': round(100 * sum(c) / TOT, 1)} for s, p, c in TREES], 'total_trees': TOT},
          open(D('laska2015_table1_trees.json'), 'w'), ensure_ascii=False, indent=1)
add('gatunki', 'drzewa (25 taksonów drzewiastych) w 4 transektach — suma', TOT, 'szt.', 'ESTIMATED', M_L + '; suma wierszy 25 taksonów drzew z Tab. 1 (837 minus 11 gatunków krzewów)',
    cytat=T1, uwagi='podział drzewo/krzew wg tekstu („25 tree species … 11 bush species”); Thuja liczona w artykule do drzew; dane: data/laska2015_table1_trees.json', **LASKA)
for s, p, cnt in TREES[:13]:
    add('gatunki', f'{p} ({s}) — liczba w 4 transektach / udział wśród drzew', f"{sum(cnt)} / {round(100 * sum(cnt) / TOT, 1)}", 'szt. / %', 'SOURCED' , M_L + f'; udział = liczba / {TOT} (obliczenie własne)',
        cytat=f'{T1}: {s} — Raginisa {cnt[0] or "-"}, Andersa {cnt[1] or "-"}, NSZ {cnt[2] or "-"}, Jana Pawła II {cnt[3] or "-"}, Total {sum(cnt)}',
        uwagi=('liczba SOURCED, udział % = obliczenie własne' + ('; KOREKTA do P10-004: tam „Fraxinus excelsior 35” — w Tab. 1 jest 8 (35 to Acer negundo na Andersa)' if s == 'Fraxinus excelsior' else '')), **LASKA)
AND = [(s, p, c[1]) for s, p, c in TREES if c[1]]
tot_and = sum(x[2] for x in AND)
add('gatunki', 'transekt Andersa (53°8′57″N 23°10′25″E, trasa C): skład drzew', '; '.join(f'{p} {n} ({round(100 * n / tot_and)} %)' for s, p, n in sorted(AND, key=lambda x: -x[2])), 'szt. (%)', 'SOURCED',
    M_L + f'; udział = liczba / {tot_and} drzew transektu (obliczenie własne)', cytat=T1 + ' — kolumna „2 Andersa st.”',
    uwagi='krzewy transektu (głóg 25, trzmielina 10, bez koralowy 10) pominięte; 100 % liściaste („Along Andersa Street, only deciduous trees were identified (100%)”)', obszar='trasa_c', lat=53.149258, lon=23.173733, **LASKA)
add('gatunki', 'udział gatunków iglastych wśród gatunków drzew przy głównych drogach', '16', '% gatunków', 'SOURCED', M_L,
    cytat='„Out of the total of 25 tree species, 21 species were deciduous trees (84%) … and four species represented coniferous trees (16%)”',
    uwagi=f'udział osobników iglastych (Thuja 30, Pinus 6, Picea 5) = 41 / {TOT} = {round(100 * 41 / TOT, 1)} % (obliczenie własne)', **LASKA)
T3 = 'Tab. 3 (s. 19): „Contribution of trees in different height and thickness classes to the transects in Białystok”'
add('wymiary', 'drzewa przyuliczne ≤ 10 m od jezdni (171 szt., 4 transekty): klasy wysokości', '0–2 m 4,7 %; 2,1–5 m 32,7 %; 5,1–10 m 53,8 %; 10,1–15 m 3,5 %; 15,1–20 m 5,3 %', '%', 'SOURCED', M_L,
    cytat=T3 + ' — Total: 8 (4.7), 56 (32.7), 92 (53.8), 6 (3.5), 9 (5.3), ∑ 171', uwagi='pomiary tylko dla rzędów i pojedynczych drzew ≤ 10 m od drogi, bez kęp', **LASKA)
add('wymiary', 'drzewa przyuliczne (171 szt.): klasy obwodu pnia na 1,2 m', '0–50 cm 24,0 %; 51–100 cm 56,1 %; 101–150 cm 13,5 %; 151–200 cm 5,3 %; 201–250 cm 0,6 %; 251–300 cm 0,6 %', '%', 'SOURCED', M_L,
    cytat=T3 + ' — Total: 41 (24.0), 96 (56.1), 23 (13.5), 9 (5.3), 1 (0.6), 1 (0.6), ∑ 171', **LASKA)
add('wymiary', 'transekt Andersa (72 drzewa, 8 gatunków): klasy wysokości', '2,1–5 m 27,8 %; 5,1–10 m 72,2 %', '%', 'SOURCED', M_L,
    cytat=T3 + ' — Transect 2 – Andersa st.: 20 (27.8), 52 (72.2), ∑ 72', uwagi='już w P10-003; tu dla kompletu tabeli generatora', obszar='trasa_c', **LASKA)
add('wymiary', 'transekt Raginisa (36 drzew, śródmieście, rzędy nasadzone): klasy wysokości', '0–2 m 22,2 %; 2,1–5 m 30,6 %; 5,1–10 m 5,6 %; 10,1–15 m 16,7 %; 15,1–20 m 25,0 %', '%', 'SOURCED', M_L,
    cytat=T3 + ' — Transect 1 – Raginisa st.: 8 (22.2), 11 (30.6), 2 (5.6), 6 (16.7), 9 (25.0), ∑ 36', **LASKA)
add('wymiary', 'najwyższe drzewa szpalerowe (lipa drobnolistna, klon jesionolistny) — wysokość', '16–17', 'm', 'SOURCED', M_L,
    cytat='„The highest species, in the height class of 15.1-20 m (25%), were specimens of Tilia cordata and Acer negundo which reached 16-17 m in height. They were of anthropogenic origin and formed rows.”', **LASKA)
add('wymiary', 'Andersa — wysokość najwyższych drzew w rzędach (klon jesionolistny, klon zwyczajny, jesion wyniosły)', 'ok. 7', 'm', 'SOURCED', M_L,
    cytat='„along Andersa Street … the highest specimens of Acer negudo, A. platanoides and Fraxinus excelsior (ca. 7 m high) were of anthropogenic origin and formed tree rows”',
    uwagi='stan 2011; do 2026 drzewa starsze o 15 lat', obszar='trasa_c', **LASKA)
add('szpaler', 'Andersa — odległość rzędów drzew od jezdni (3 rzędy po jednej stronie)', '2 / 10 / 15', 'm', 'SOURCED', M_L,
    cytat='„On one side, there were three tree rows with Acer platanoides, A. negundo and Fraxinus excelsior L., planted in a succession at a distance of 2 m, 10 m and 15 m from the road. On the other side of Andersa Street, there was a row of trees with Acer platanoides right next to the route.”',
    uwagi='już w P10-003; stan 2011 — po przebudowach nieaktualne w części (kadry 2019–2021: rzędy młodych drzew za ścieżką)', obszar='trasa_c', **LASKA)
add('szpaler', 'gęstość drzew i krzewów w transektach (Andersa / Raginisa / NSZ / Jana Pawła II)', '3,0 / 1,4 / 3,6 / 4,7', 'szt. / 100 m²', 'SOURCED', M_L,
    cytat='„The tree density in the investigated transect was 3 specimens per 100 m2” (Andersa); „1.4 specimens per 100 m2” (Raginisa); „3.6 specimens per 100 m2” (NSZ); „reaching 4.7 specimens per 100 m2” (Jana Pawła II)',
    uwagi='obejmuje krzewy i kępy samosiewów', **LASKA)

# ================================================================ C. NIK
add('gatunki', 'kompleksowa inwentaryzacja zieleni Białegostoku — istnienie', 'brak', '', 'SOURCED', 'odczyt PDF wystąpienia pokontrolnego NIK (pdftotext), s. 24',
    cytat='„Miasto nie posiadało opracowanej aktualnej kompleksowej inwentaryzacji zieleni na obszarze gminy. … w Białymstoku zinwentaryzowana jest zieleń na terenie niektórych parków.”',
    uwagi='potwierdza lukę G7 („brak rejestru drzew przyulicznych”); wniosek o informację publiczną nie da rejestru gatunków', **NIK)
add('gatunki', 'ewidencja gatunków drzew usuwanych i sadzonych przez Urząd', 'brak', '', 'SOURCED', 'jw., s. 30',
    cytat='„Urząd nie ewidencjonował gatunków i odmian usuniętych i nasadzonych drzew.”', **NIK)
add('gatunki', 'drzewa posadzone przez Miasto na gruntach gminnych 2020–2023 (rekompensata ubytków)', '3681 (729 / 1184 / 1061 / 707)', 'szt.', 'SOURCED', 'jw., s. 28',
    cytat='„Miasto usunęło łącznie 5.406 drzew (odpowiednio: 1.241, 1.325, 1.486, 1.354) … a w ramach rekompensaty za dokonane ubytki nasadziło 3.681 drzew (odpowiednio: 729, 1.184, 1.061, 707) i 68.288 sztuk krzewów”',
    uwagi='ok. 920 młodych drzew rocznie → istotny udział drzew „na palikach” w krajobrazie ulic', **NIK)

# ================================================================ D. BIP 2017 + Zieleń 2019
M_B = 'odczyt PDF załącznika do SIWZ (pdftotext -layout)'
add('wymiary', 'materiał do nasadzeń w pasach drogowych — obwód pnia na wys. 1 m', '14–16', 'cm', 'SOURCED', M_B + ', zał. 2 s. 3 pkt 1.1',
    cytat='„bryła korzeniowa w balocie, wyodrębniony prosty pień oraz ukształtowana korona na wysokości 1,8 – 2,0 m , a obwód pnia mierzony na wysokości 1 m - 14 - 16 cm.”', **BIP2)
add('wymiary', 'młode drzewo uliczne — wysokość osadzenia korony (pień bez gałęzi)', '1,8–2,0', 'm', 'SOURCED', M_B + ', zał. 2 s. 3 pkt 1.1',
    cytat='„ukształtowana korona na wysokości 1,8 – 2,0 m”', uwagi='G7 #7 przyjmował 1,3 m min dla młodych — dla nasadzeń miejskich w pasie drogowym właściwe 1,8–2,0 m', **BIP2)
add('wymiary', 'palikowanie młodych drzew ulicznych', '3 paliki, ⌀ 6–9 cm, poprzeczki u góry; pielęgnacja: paliki ⌀ 6–8 cm, długość 2 m', '', 'SOURCED', M_B + ', zał. 2 s. 1 i s. 4',
    cytat='„Każde drzewo należy przymocować taśmą do 3 palików. Paliki powinny być połączone u góry drewnianymi poprzeczkami. Paliki powinny być okorowane, zaimpregnowane o średnicy 6-9 cm.”; „palików drewnianych o średnicy 6-8cm i długości 2 m (po ustawieniu ok. ¼ długości palika powinna znajdować…”',
    uwagi='paliki 2 m wbite na ok. 1/4 → ok. 1,5 m nad ziemią; zgodne z kadrami (R5 kv993066550)', **BIP2)
add('wymiary', 'dół sadzenia drzewa / misa', '70 × 70 × 70 cm; misa ściółkowana korą ≥ 5 cm', '', 'SOURCED', M_B + ', zał. 2 s. 4 pkt 1.2',
    cytat='„Drzewa należy sadzić we wcześniej przygotowane doły o wymiarach 70 x 70 x 70 cm.”; „Wokół drzew należy wykonać misy, powierzchnię mis wyściółkować przekompostowaną korą (warstwą kory o grubości minimum 5 cm)”',
    uwagi='do gry: ciemny krąg kory ⌀ ok. 1 m wokół młodego drzewa (średnica misy — WORKING_VALUE)', **BIP2)
PAL = [('lipy', 'Lipa drobnolistna (Tilia cordata), ‘Green Spire’, lipa srebrzysta (Tilia tomentosa), ‘Varsaviensis’', 'TAK'),
       ('klony', 'Klon zwyczajny ‘Drummondii’, ‘Faassen’s Black’, ‘Royal Red’, klon kulisty ‘Globosum’, klon jawor ‘Leopoldi’, klon polny, ‘Elsrijk’, klon tatarski ‘Ginnala’, klon jesionolistny ‘Flamingo’', 'TAK'),
       ('jesiony', 'Jesion wyniosły (Fraxinus excelsior), ‘Pendula’, jesion pensylwański (Fraxinus pensylvanica), ‘Crispa’', 'TAK'),
       ('kasztanowce', 'Kasztanowiec biały (Aesculus hippocastanum), kasztanowiec czerwony (Aesculus carnea)', 'TAK'),
       ('jarzęby', 'Jarząb pospolity (Sorbus aucuparia ‘Edulis’), Jarząb szwedzki (Sorbus Intermedia)', 'TAK'),
       ('robinia', 'Robinia akacjowa kulista (Robinia pseudoacacia ‘Umbraculifera’)', 'TAK (tylko forma kulista)'),
       ('dęby', 'Dąb szypułkowy, kolumnowy ‘Fastigiata’, piramidalny, dąb czerwony', 'TAK'),
       ('inne liściaste', 'Głóg ‘Paul’s Scarlet’, grab ‘Fastigiata’, grusza ‘Chanticleer’, leszczyna turecka, śliwa wiśniowa ‘Woodii’, wiśnia ‘Kanzan’, topola Simona ‘Fastigiata’, topola włoska ‘Italica’, wierzba biała ‘Tristis’', 'TAK')]
for grp, lst, ok in PAL:
    add('gatunki', f'paleta nasadzeń uzupełniających w pasach drogowych (UM 2017) — {grp}', ok, 'na liście', 'SOURCED', M_B + ', zał. 2 s. 4–5 pkt 1.3',
        cytat='„1.3 Gatunki i odmiany drzew liściastych do nasadzeń uzupełniających w pasach drogowych ulic na terenie Białegostoku” — ' + lst,
        uwagi='lista dopuszczonych gatunków, bez liczb sztuk; zapis nazw jak w dokumencie', **BIP2)
add('gatunki', 'platan (Platanus) i brzoza (Betula) na liście nasadzeń ulicznych UM 2017', 'NIE (brak na liście)', '', 'SOURCED', M_B + ', zał. 2 s. 4–5 pkt 1.3 — przeszukanie całej listy',
    cytat='lista 1.3 (Grupa I i II) nie zawiera rodzajów Platanus ani Betula', uwagi='platan niepotwierdzony w Białymstoku żadnym źródłem pakietu → nie używać w generatorze; brzoza pojawia się w planie nasadzeń antysmogowych 2019 i w inwentaryzacji 2011 (21 szt.)', **BIP2)
add('zywoplot', 'iglaki dopuszczone do nasadzeń w pasach drogowych (UM 2017) — żywotniki', 'TAK', 'na liście', 'SOURCED', M_B + ', zał. 2 s. 6 pkt 2.2',
    cytat='„Żywotnik zachodni ‘Brabant’ (Thuja occidentalis \'Brabant\'); Żywotnik zachodni ‘Szmaragd’ (Thuja occidentalis \'Smaragd\'); Żywotnik zachodni (Thuja occidentalis)”',
    uwagi='materiał: pojemnik min. C3, szerokość roślin ok. 30–40 cm', **BIP2)
add('zywoplot', 'krzewy żywopłotowe na liście UM 2017 (pasy drogowe)', 'ligustr pospolity ‘Atrovirens’, berberysy (18 pozycji), irga błyszcząca, tawuły, pęcherznica, śnieguliczka, dereń', 'na liście', 'SOURCED', M_B + ', zał. 2 s. 6–8 pkt 3.3',
    cytat='„Ligustr pospolity \'Atrovirens\' (Ligustrum vulgare \'Atrovirens\')”; „Berberys Thunberga ‘Atropurpurea ‘(Berberis Thunbergii ‘Atropurpurea ’)”; „Irga błyszcząca (Cotoneaster lucidus)”',
    uwagi='grab jako krzew żywopłotowy nie występuje (tylko drzewo ‘Fastigiata’)', **BIP2)
add('gatunki', 'drzewa i krzewy w stałej pielęgnacji w pasach drogowych (umowa 2017–2020) — razem', '3207 liściastych; 643 iglastych (drzewa i krzewy); 17 990 krzewów liściastych', 'szt.', 'SOURCED', M_B + ', zał. 3 s. 3 (wiersze sum 2017–2020)',
    cytat='„Wykaz lokalizacji wraz z przewidywaną ilością roślin do pielęgnacji w ramach miesięcznego wynagrodzenia objętych umową” — wiersz „2017: 3207 643 17990 6700 712 11000 2520”',
    uwagi='tylko nasadzenia objęte umową pielęgnacyjną (młode), nie wszystkie drzewa uliczne; przypisanie liczb do kolumn wg pozycji w PDF', **BIP3)
for ul, val, cyt, extra in [
    ('gen. W. Andersa (od fabryki dywanów do ul. Wasilkowskiej) — trasa C', '228 drzew liściastych; 1082 krzewy liściaste', '„gen. W. Andersa od Fabryki Dywanów AGNELLA do ul. Wasilkowskiej 228 1082”', dict(obszar='trasa_c')),
    ('gen. S. Maczka z rondem Putry i rozjazdami w Al. 1000-lecia PP do Andersa — trasa C', '527 drzew liściastych; 1546 krzewów liściastych', '„gen. S. Maczka od AUCHAN wraz z drogami serwisowymi, ul. J. Karskiego, Rondem Putry i rozjazdami w ul. 1000 Lecia P.P. - do granicy miasta, do Fabryki Dywanów AGNELLA na ul. gen. W. Andersa 527 1546”', dict(obszar='trasa_c')),
    ('Lipowa (od Malmeda do siedziby Lasów Państwowych)', '97 drzew liściastych', '„Lipowa od ul. I. Malmeda do siedziby Lasów Państwowych (wraz z drzewami przy Księgarni Technicznej) 97”', {}),
    ('Św. o. Pio (od Mickiewicza do Zwierzynieckiej)', '150 drzew liściastych', '„Św. o Pio od ul. Mickiewicza do ul. Zwierzynieckiej 150”', {}),
    ('Al. J. Piłsudskiego (od kościoła św. Rocha do ronda Lussy)', '94 drzewa liściaste; 20 iglastych; 1125 krzewów; 2400 róż', '„Al.. J. Piłsudskiego od Kościoła Św. Rocha do Ronda A. P. Lussy 94 20 1125 2400 10000”', {}),
    ('gen. Sosabowskiego / gen. Sulika (od Wasilkowskiej do szosy Baranowickiej)', '1225 drzew liściastych; 4337 krzewów liściastych', '„gen. S. Sosabowskiego, gen. N. Sulika od ul. Wasilkowskiej do Szosy Baranowickiej wraz z rondem i rozjazdami 1225 4337”', {})]:
    add('gatunki', f'nasadzenia w pielęgnacji 2017–2020: {ul}', val, 'szt.', 'SOURCED', M_B + ', zał. 3', cytat=cyt,
        uwagi='gatunków brak; przypisanie liczb do kolumn (drzewa liściaste / iglaste / krzewy / róże) wg pozycji w PDF — przy wierszach z 2 liczbami pierwsza = drzewa liściaste, druga = krzewy liściaste', **dict(BIP3, **extra))
add('gatunki', 'nasadzenia „antysmogowe” w pasach drogowych planowane na 2019 — gatunki', 'brzoza brodawkowata (drzewo); pęcherznica kalinolistna, kalina koralowa, dereń biały (krzewy); winobluszcz, rdest Auberta (pnącza)', '', 'SOURCED', 'odczyt PDF (pdftotext), s. 38 rozdz. 15',
    cytat='„Planuje się nasadzenia następujących gatunków: pęcherznica kalinolistna, kalina koralowa, dereń biały, brzoza brodawkowata, winobluszcz pięciolistkowy odm. murowa, winobluszcz pięciolistkowy ‘Engelmannii’, rdest Auberta”',
    uwagi='koszt: „drzewa – 400,00 zł/szt., krzewy – 22,00 zł/szt.”', **Z2019)

# ================================================================ E. Przepisy
M_D = 'odczyt PDF Dz.U. (pdftotext -layout); przeszukanie całego tekstu na: drzew, zieleń, krzew, żywopł'
add('przepisy', 'Dz.U. 2022 poz. 1518 — liczbowa odległość drzew od krawędzi jezdni', 'brak w rozporządzeniu', '', 'SOURCED', M_D,
    cytat='jedyne wystąpienie słowa „drzewa”: § 59 ust. 4 (s. 22) „Przeszkodami w polu widoczności nie są pojedyncze drzewa, konstrukcje wsporcze urządzeń drogi … jeżeli zostało to potwierdzone analizą widoczności”',
    uwagi='rozporządzenie z 2022 r. nie zawiera odpowiednika dawnego § 53 (3,0 m); numer paragrafu cytatu o widoczności — wg kontekstu strony 22 PDF (UNVERIFIED numer §, strona pewna)', **DU22)
add('przepisy', 'Dz.U. 2022 poz. 1518 § 26 — strefa bez przeszkód przy v > 50 km/h', 'wymagana (szerokość nieokreślona liczbowo w rozporządzeniu)', '', 'SOURCED', M_D + '; s. 8',
    cytat='„§ 26. 1. Droga, na której prędkość dopuszczalna wynosi więcej niż 50 km/h, powinna mieć strefę bez przeszkód. Jeżeli nie można zaprojektować strefy bez przeszkód, projektuje się barierę ochronną.”',
    uwagi='do gry: na odcinkach 70 km/h (Andersa, DK8) drzewa nie stoją tuż przy krawężniku albo są za barierą — zgodne z kadrami KartaView', **DU22)
add('przepisy', 'Dz.U. 2022 poz. 1518 § 80 — wysokość skrajni jezdni (klasy GP, G, Z, L, D) / chodnika', '4,50 / 2,50', 'm', 'SOURCED', M_D + '; s. 19',
    cytat='„§ 80. 1. Wysokość skrajni powinna być nie mniejsza niż: … 2) 4,50 m – w przypadku skrajni jezdni drogi klasy GP, G, Z, L lub D; 3) 2,50 m – w przypadku skrajni chodnika, drogi dla rowerów lub drogi dla pieszych i rowerów”',
    uwagi='do gry: gałęzie nad jezdnią nie niżej niż 4,5 m, nad chodnikiem 2,5 m (podkrzesanie koron drzew przy jezdni)', **DU22)
add('przepisy', 'Dz.U. 2022 poz. 1518 § 113 — utrzymanie roślinności a skrajnia', 'roślinność nie może ingerować w skrajnię ani ograniczać widoczności', '', 'SOURCED', M_D + '; s. 28',
    cytat='„2) roślinności w pasie drogowym w sposób, który umożliwia jej prawidłową wegetację oraz uniemożliwia jej negatywny wpływ na drogę w trakcie rozrostu, a w szczególności ingerencję w skrajnię lub ograniczanie widoczności”', **DU22)
add('przepisy', 'poprzednie warunki techniczne (rozp. z 2.03.1999, t.j. Dz.U. 2016 poz. 124) § 53 ust. 3 — odległość pnia od krawędzi jezdni', '≥ 3,0', 'm', 'SOURCED', M_D + '; s. 23 PDF tekstu jednolitego',
    cytat='„3. Odległość pnia drzewa od krawędzi jezdni nie powinna być mniejsza niż 3,0 m, a w wypadku przebudowy albo remontu drogi dopuszcza się mniejszą odległość, jeśli będą spełnione pozostałe warunki określone w rozporządzeniu.”',
    uwagi='przepis obowiązywał przy projektowaniu ulic do 20.09.2022 (większość istniejących ulic Białegostoku); utrata mocy — wiersz niżej', **DU16)
add('przepisy', 'poprzednie warunki techniczne § 53 ust. 1 — minimalna szerokość pasa zieleni z rzędem drzew / żywopłotem', '≥ 3,0', 'm', 'SOURCED', M_D + '; s. 23',
    cytat='„§ 53. 1. Szerokość pasa zieleni, zapewniająca wystarczające warunki jej wegetacji i pielęgnacji powinna wynosić co najmniej 3,0 m, jeżeli jest to rząd drzew, żywopłot lub pasmo krzewów.”', **DU16)
add('przepisy', 'utrata mocy rozporządzenia z 1999 r. / wejście w życie nowego', '21.09.2022', 'data', 'SOURCED', M_D + '; Dz.U. 2022 poz. 1518 s. 29 (§ 117 i odnośnik 4)',
    cytat='„§ 117. Rozporządzenie wchodzi w życie z dniem 21 września 2022 r.”; odnośnik 4: „Niniejsze rozporządzenie było poprzedzone rozporządzeniem Ministra Transportu i Gospodarki Morskiej z dnia 2 marca 1999 r. …” „…które traci moc z dniem 21 września 2022 r.”',
    uwagi='odnośnik wymienia trzy rozporządzenia (drogi publiczne 1999, obiekty inżynierskie 2000, autostrady płatne 2002); sformułowanie o utracie mocy dla pierwszego: „tracą moc w dniu wejścia w życie niniejszego rozporządzenia”', **DU22)
add('przepisy', 'miejskie standardy zieleni / standard sadzenia drzew przyulicznych w Białymstoku (odstęp, odsunięcie)', 'nie znaleziono', '', 'UNVERIFIED',
    'wyszukiwanie: bialystok.pl, bip.bialystok.pl, zapytania „standardy zieleni Białystok zarządzenie”; znalezione tylko standardy Warszawy, Krakowa, Lublina, Olsztyna (nie użyte)',
    uwagi='NIK 2024 (s. 24) potwierdza brak kompleksowych opracowań; odstępy w grze brać z pomiaru OSM (wiersze „szpaler”)')

# ================================================================ F. Allometria UTD
utd = json.load(open(D('utd_allometry.json')))
PLN = {'Tilia cordata': 'lipa drobnolistna', 'Acer platanoides': 'klon zwyczajny', 'Fraxinus pennsylvanica': 'jesion pensylwański (zamiennik jesionu wyniosłego — F. excelsior w UTD tylko z Kalifornii)',
       'Aesculus hippocastanum': 'kasztanowiec biały', 'Betula pendula': 'brzoza brodawkowata', 'Robinia pseudoacacia': 'robinia akacjowa',
       'Acer negundo': 'klon jesionolistny', 'Pyrus calleryana': 'grusza drobnoowocowa', 'Tilia tomentosa': 'lipa srebrzysta'}
for sp_, pl in PLN.items():
    o = utd[sp_]
    for gcl in o['girth_classes']:
        if gcl['n'] < 5: continue
        add('wymiary', f'{pl} ({sp_}) — obwód {gcl["girth_cm"]} cm: wysokość mediana (p25–p75) / średnica korony mediana (p25–p75)',
            f"{gcl['H_med']} ({gcl['H_p25']}–{gcl['H_p75']}) / {gcl['crown_med']} ({gcl['crown_p25']}–{gcl['crown_p75']})", 'm / m', 'ESTIMATED', M_UTD,
            cytat='TS3_Raw_tree_data.csv, kolumny „DBH (cm)”, „TreeHt (m)”, „AvgCdia (m)”', uwagi=f"n = {gcl['n']}; regiony: {', '.join(o['regions'])}; drzewa uliczne USA — przenosić przez obwód, nie przez wiek", **UTD)
for sp_ in ('Tilia cordata', 'Acer platanoides'):
    for ac in utd[sp_]['age_classes']:
        if ac['n'] < 5: continue
        add('wymiary', f'{PLN[sp_]} — wiek od posadzenia {ac["age"]} lat (USA): wysokość / średnica korony / obwód / podstawa korony',
            f"{ac['H_med']} ({ac['H_p25']}–{ac['H_p75']}) / {ac['crown_med']} ({ac['crown_p25']}–{ac['crown_p75']}) / {ac['girth_med_cm']} / {ac['crown_base_med']}", 'm / m / cm / m', 'ESTIMATED', M_UTD,
            cytat='TS3_Raw_tree_data.csv, kolumny „Age”, „TreeHt (m)”, „AvgCdia (m)”, „CrnBase”', uwagi=f"n = {ac['n']}; korona/wysokość mediana {ac['crown_over_H_med']}; TEMPO WZROSTU USA — w Białymstoku wolniejsze (wiersz kalibracji niżej)", **UTD)
add('wymiary', 'kalibracja wieku do Białegostoku: lipa drobnolistna ok. 20 lat, obwód 58 cm, wysokość 7 m (pomiar SGGW 2022)', 'wiek_Białystok ≈ 2 × wiek_UTD przy tym samym obwodzie', '', 'WORKING_VALUE',
    'porównanie jednego pomiaru z research/g7-street-greenery (G7-T04: lipa 58 cm / 7 m / ok. 20 lat) z UTD: obwód 51–100 cm osiągany w USA w wieku ok. 8–12 lat',
    uwagi='jedna kotwica (n = 1) → tylko wartość robocza; wysokość dla obwodu zgodna: UTD lipa 51–100 cm → 9,5 m (7,1–11), Białystok 7 m; Łaska 2015: obwody 51–100 cm ↔ wysokości 5,1–10 m')
add('wymiary', 'jarząb szwedzki (Sorbus intermedia) — wysokość / korona wg wieku', 'brak danych', '', 'UNVERIFIED', 'gatunku brak w UTD (TS3) i w inwentaryzacji Łaski 2015; na liście nasadzeń UM 2017 jest',
    uwagi='sufity gatunkowe — patrz research/g7-street-greenery (Ebben); do gry użyć bryły „małe drzewo kuliste 6–10 m” jako WORKING_VALUE')
add('wymiary', 'platan klonolistny — wysokość / korona', 'nie dotyczy (gatunek niepotwierdzony w Białymstoku)', '', 'UNVERIFIED', 'brak w OSM (species), Łasce 2015, liście UM 2017 i na 54 kadrach', uwagi='nie generować')

# ================================================================ G. Szkółki / żywopłoty
M_E = 'odczyt karty odmiany (PDF generowany ze strony e-katalogroslin.pl, pdftotext)'
E1 = EKR(7170, 'zywotnik-zachodni-smaragd_thuja-occidentalis-smaragd', 'Związek Szkółkarzy Polskich; opis: Szkółka Roślin Ozdobnych Wiesław Szydło')
E2 = EKR(7109, 'zywotnik-zachodni-brabant_thuja-occidentalis-brabant', 'Związek Szkółkarzy Polskich; opis: Wiesław Szydło')
E3 = EKR(3735, 'ligustr-pospolity_ligustrum-vulgare', 'Związek Szkółkarzy Polskich; opis: TOMŻYŃSKI Szkółka Roślin')
add('zywoplot', 'żywotnik ‘Smaragd’ — wysokość / szerokość w wieku 10 lat', '2,5 / 0,7', 'm / m', 'SOURCED', M_E, cytat='„W wieku 10 lat roślina osiąga około 2,5 m wysokości i 0,7 m szerokości.”', uwagi='docelowa wysokość w karcie: „od 5 m do 10 m”', **E1)
add('zywoplot', 'żywotnik ‘Smaragd’ — rozstaw sadzenia w rzędzie', '0,5–0,6', 'm', 'SOURCED', M_E, cytat='„Odmiana polecana na nieformowane żywopłoty … Gęstość sadzenia w rzędzie: co 0,5-0,6 m.”', **E1)
add('zywoplot', 'żywotnik ‘Brabant’ — wysokość / średnica w wieku 10 lat', '3,5 / 1,5', 'm / m', 'SOURCED', M_E, cytat='„dorastające w wieku 10 lat do 3,5 m wysokości i 1,5 m średnicy. Stare egzemplarze mogą osiągać nawet ponad 15 m wysokości i ponad 2 m średnicy.”', **E2)
add('zywoplot', 'żywotnik ‘Brabant’ — rozstaw sadzenia w rzędzie', '0,6–0,8', 'm', 'SOURCED', M_E, cytat='„polecana do sadzenia w ogrodach przydomowych i parkach jako roślina szpalerowa i żywopłotowa. Gęstość sadzenia w rzędzie: co 0,6-0,8 m.”', **E2)
add('zywoplot', 'ligustr pospolity — wysokość krzewu / żywopłotu strzyżonego', '2–3 (do 5 nie cięty) / do 2,5', 'm', 'SOURCED', M_E, cytat='„dorastający do 2-3 m wysokości, w optymalnych warunkach i nie cięty osiąga nawet do 5 m”; „Przez regularne cięcie można uzyskać żywopłoty do 2,5 m wysokości.”',
    uwagi='„Do niedawna najpopularniejszy krzew żywopłotowy.”; kwitnie VI–VII (białe wiechy), owoce czarne od VIII przez zimę', **E3)
add('zywoplot', 'grab pospolity, berberys Thunberga — wysokość / rozstaw żywopłotu', 'brak danych w pakiecie', '', 'UNVERIFIED', 'karty e-katalogroslin dla tych gatunków nie zostały otwarte (wyszukiwarka serwisu wymaga JS); gatunki są na liście UM 2017 (berberysy) / tylko jako drzewo (grab ‘Fastigiata’)',
    uwagi='wysokości z kadrów: żywopłoty liściaste 1,5–3 m (wiersze kadrów); gatunek liściastych z kadrów nierozpoznany')

# ================================================================ H. Fenologia
add('fenologia', 'kwitnienie leszczyny (najwcześniejsza wiosna) — średni dzień roku, Polska 2007–2014', 70, 'DOY (11 III)', 'SOURCED', 'tekst artykułu (PMC, sekcja Results)',
    cytat='„from the earliest spring (flowering of hazel occurring on 70 days of the year on average), to late autumn (leaf falling of silver birch occurring on 301 days of the year on average)”', uwagi='52 stacje IMGW-PIB, cała Polska; nie tylko Podlasie', **PMC)
add('fenologia', 'opadanie liści brzozy brodawkowatej (BBCH 97) — średni dzień roku, Polska 2007–2014', 301, 'DOY (28 X)', 'SOURCED', 'tekst artykułu (PMC, sekcja Results)',
    cytat='„leaf falling of silver birch occurring on 301 days of the year on average”', **PMC)
for nm, doy, box, date in [('rozwój liści brzozy brodawkowatej (BBCH 11)', 108, '103–113', '18 IV'), ('kwitnienie kasztanowca białego (BBCH 60)', 124, '120–128', '4 V'),
                           ('kwitnienie robinii akacjowej (BBCH 60)', 145, '141–150', '25 V'), ('kwitnienie lipy drobnolistnej (BBCH 60)', 171, '166–179', '20 VI'),
                           ('przebarwianie liści kasztanowca (BBCH 94)', 271, '269–278', '28 IX'), ('przebarwianie liści brzozy (BBCH 94)', 282, '274–288', '9 X'),
                           ('opadanie liści brzozy (BBCH 97) — odczyt kontrolny z wykresu', 301, '297–309', '28 X')]:
    add('fenologia', f'{nm} — mediana, Polska 2007–2014', doy, f'DOY ({date})', 'ESTIMATED', M_FIG,
        cytat='Fig. 2: „Dates of selected phenological season’s onset among all analyzed stations in Poland in the period of 2007–2014 … Box and whisker plots denote to percentile values of 0.05, 0.25, 0.50, 0.75, and 0.95”',
        uwagi=f'pudełko p25–p75: DOY {box}; wartości ogólnopolskie — dla Białegostoku (północny wschód) wiosna zwykle później; poprawka regionalna UNVERIFIED', **PMC_FIG)
add('fenologia', 'poprawka terminów fenologicznych dla Białegostoku względem mediany krajowej', 'brak źródła', 'dni', 'UNVERIFIED',
    'nie znaleziono otwartych danych stacyjnych (IMGW danepubliczne — brak fenologii; PEP725 wymaga rejestracji); Jabłońska i in. 2015 (doi:10.3161/15052249PJE2015.63.3.002) nie otwarto',
    uwagi='kontrola z kadrów Białegostoku (wiersze kadrów): 7–9 V liście rozwinięte/jasne; 20–22 V pełne ulistnienie; 4 X lipy przy Lipowej jeszcze zielone; 6 i 11 XI drzewa bezlistne')

# ================================================================ I. Kadry
tr = Transformer.from_crs(4326, 2180, always_xy=True)
roads = [r for r in json.load(open(D('osm_roads.json')))['elements'] if r['tags'].get('name')]
lines = [LineString([tr.transform(x, y) for x, y in r['geom']]) for r in roads]
tree = STRtree(lines)
def nearest(lat, lon):
    p = Point(tr.transform(lon, lat)); best = (1e9, '')
    for i in tree.query(p.buffer(80)):
        d = lines[i].distance(p)
        if d < best[0]: best = (d, roads[i]['tags']['name'])
    return (best[1], round(best[0], 1)) if best[1] else ('(brak nazwanej drogi ≤ 80 m)', '')
frames = []
for x in json.load(open(D('frames_kv_px.json'))):
    if x['fid'] not in frame_notes.N: continue
    frames.append(dict(fid=x['fid'], src=x['src'], url=x['page'], url_pliku=x['url'], lic=x['license'].replace('CC-BY-SA-4.0', 'CC BY-SA 4.0') + ' (referencja, nie tekstura)',
                       autor=x['author'], sha=x['sha256'], lat=x['lat'], lon=x['lon'], kier=(round(float(x['heading']), 1) if x['heading'] is not None else 'UNVERIFIED'),
                       date=x['date'].replace('T', ' '), kmet=('KartaView API 1.0 nearby-photos, pole heading' if x['src'] == 'KartaView' else 'Panoramax API /search, pole view:azimuth')))
for x in json.load(open(D('frames_commons.json'))):
    frames.append(dict(fid=x['fid'], src='Wikimedia Commons', url=x['descurl'], url_pliku=x['thumburl'], lic=x['license'] + (' (referencja, nie tekstura)' if 'BY' in x['license'] else ''),
                       autor=x['artist'], sha=x['sha256'], lat=float(x['lat']), lon=float(x['lon']), kier='UNVERIFIED', date=x['date'],
                       kmet='Commons: brak GPSImgDirection w metadanych API'))
frames.sort(key=lambda f: ({'trasa_c': 0, 'dojlidy': 1, 'miasto': 2}[frame_notes.N[f['fid']][0]], f['date']))
seen = {}
for f in frames:
    ob, ul, sez, opis, uw, front, hedge = frame_notes.N[f['fid']]
    nm, dist = nearest(f['lat'], f['lon'])
    rid = add('kadr', f"kadr {f['src']} {f['fid']} — {ul}", '', '', 'ESTIMATED', 'obejrzano obraz ≤ 960 px (narzędzie Read) 2026-11-14; ' + f['kmet'],
              url=f['url'], url_pliku=f['url_pliku'], lic=f['lic'], autor=f['autor'], sha=f['sha'], lat='%.6f' % f['lat'], lon='%.6f' % f['lon'], kierunek_deg=f['kier'],
              opis_co_widać=opis, duplikat_sha256=seen.get(f['sha'], ''), uwagi=uw, obszar=ob, data_zdjęcia=f['date'], sezon=sez, ulica_osm_najbliższa=nm,
              **{'odległość_od_osi_m': dist, 'front': front, 'żywopłot': hedge, 'plik_lokalny': f"files/frames/{f['fid']}.jpg", 'sha_stabilny': 'tak'})
    seen.setdefault(f['sha'], rid)
K = [r for r in rows if r['kategoria'] == 'kadr']
fid2id = {r['plik_lokalny'].split('/')[-1][:-4]: r['id'] for r in K}
SF = [r for r in K if r['front'] == 'jednorodzinna']
cnt = lambda h: sum(1 for r in SF if r['żywopłot'] == h)
ids = lambda h: ', '.join(r['id'] for r in SF if r['żywopłot'] == h)
M_K = f'zliczenie kadrów z frontem posesji domu jednorodzinnego (n = {len(SF)}; Dojlidy, Nowe Miasto, Dziesięciny, rejon Św. Ojca Pio; lato/wiosna 2020–2023); jeden kadr = jeden front (dominująca posesja)'
add('zywoplot', 'ulice domów — fronty z żywopłotem/rzędem iglastym (żywotnik)', f"{cnt('iglasty')} / {len(SF)} = {round(100 * cnt('iglasty') / len(SF))}", 'kadry / %', 'ESTIMATED', M_K, uwagi='kadry: ' + ids('iglasty') + '; G7 #15/#18: 40 % posesji z żywopłotem × 70 % tuja = 28 % — zgodne')
add('zywoplot', 'ulice domów — fronty z żywopłotem liściastym', f"{cnt('liściasty')} / {len(SF)} = {round(100 * cnt('liściasty') / len(SF))}", 'kadry / %', 'ESTIMATED', M_K, uwagi='kadry: ' + ids('liściasty') + '; wyżej niż G7 (40 % × 30 % = 12 %) — mała próba')
add('zywoplot', 'ulice domów — luźny szpaler wysokich iglaków przy ogrodzeniu (nie strzyżony)', f"{cnt('szpaler_iglasty_luźny')} / {len(SF)} = {round(100 * cnt('szpaler_iglasty_luźny') / len(SF))}", 'kadry / %', 'ESTIMATED', M_K, uwagi='kadry: ' + ids('szpaler_iglasty_luźny'))
add('zywoplot', 'ulice domów — fronty bez żywopłotu', f"{cnt('brak')} / {len(SF)} = {round(100 * cnt('brak') / len(SF))}", 'kadry / %', 'ESTIMATED', M_K, uwagi='kadry: ' + ids('brak') + '; G7 #17: 35 %')
add('zywoplot', 'żywopłot/rząd z żywotnika przy domach — wysokość z kadrów', 'młody rząd 1,2–1,8; ściana dojrzała 2,0–3,0', 'm', 'ESTIMATED',
    'kotwica: ogrodzenie posesji 1,5 m (WORKING_VALUE, zakres 1,4–1,8 m); wysokość = krotność wysokości ogrodzenia odczytana z kadru',
    uwagi=f"kadry: {fid2id['cm20200726084244']} (młode, poniżej ogrodzenia), {fid2id['cm20230805102222']} (wierzchołki tuż nad płotem), {fid2id['cm20200726084948']} (ok. 1,3× ogrodzenia), {fid2id['cm20200726085220']} (wyraźnie ponad ogrodzeniem z banerami); ±0,5 m; G7 #19: 2,0–2,5 m, ADR 0170: 2,4–3,6 m")
add('zywoplot', 'żywopłot liściasty przy domach — wysokość z kadrów', '1,5–1,8 (strzyżony przy siatce); ok. 2,2 (blok za płotem); ok. 3 (ściana nieformowana)', 'm', 'ESTIMATED',
    'kotwice: ogrodzenie 1,5 m (WORKING_VALUE), samochód kombi 1,45–1,5 m (WORKING_VALUE)',
    uwagi=f"kadry: {fid2id['cm20200801183320']}, {fid2id['cm20220612161639']}, {fid2id['cm20200726085539']}; ±0,5 m; G7 #20 podawał 0,8–1,5 m — kadry letnie pokazują wyższe")
add('zywoplot', 'rozstaw młodych żywotników w rzędzie przy ogrodzeniu — z kadru', '0,9–1,4', 'm', 'ESTIMATED',
    f"kadr {fid2id['cm20230805102222']}: 13–16 wierzchołków na długości ogrodzenia między słupkami; długość ogrodzenia oszacowana z szerokości elewacji domu (2 osie okien ≈ 9–10 m) z poprawką na perspektywę",
    uwagi='niepewność duża (±0,3 m); szkółki zalecają 0,5–0,8 m — w terenie sadzone rzadziej')
add('wymiary', 'ul. Lipowa — drzewa szpalerowe (pokrój stożkowy, zwarta korona): wysokość / średnica korony / podstawa korony', '8–9,5 / 3,7–4,2 / 2,5–3,5', 'm', 'ESTIMATED',
    f"kadr {fid2id['cm20201004144314']} (widok czołowy 4 drzew): odstęp pni = 6,8 m (mediana OSM dla Lipowej) jako skala; wysokość drzewa = 1,2 × odstęp, korona = 0,55 × odstęp; kontrola: wierzchołki między 3. a 4. kondygnacją (parter usługowy ~4 m + 2 × ~3 m)",
    uwagi=f"kadry pomocnicze: {fid2id['cm20200712161619']}, {fid2id['cm20210522101909']}; ±1 m; korona/wysokość ≈ 0,45 (węższa niż lipa gatunkowa 0,5–0,6 z G7 #13 — odmiana stożkowa)")
add('szpaler', 'ul. Lipowa — odsunięcie pnia od krawężnika (drzewo w chodniku, krata + osłona pnia)', 'ok. 1,0', 'm', 'ESTIMATED',
    f"kadry {fid2id['cm20210313102027']} i {fid2id['cm20210522101909']}: krata wokół pnia styka się z pasem przykrawężnikowym; skala — szerokość ławki ~1,8 m i kraty ~1,5 m (WORKING_VALUE)",
    uwagi='±0,4 m; pomiar OSM dla Lipowej: oś→pień 5,5–6,5 m (jezdnia + pasy postojowe); osłona pnia ok. 1,8 m wysokości')
add('wymiary', 'Andersa — młode drzewa w rzędzie na palikach: wysokość', '4–5', 'm', 'ESTIMATED',
    f"kadry {fid2id['kv7119879']} (2016), {fid2id['kv993066550']} (2019), {fid2id['kv1326673765']} (2021): porównanie z tablicą znaku na słupkach (~3–3,5 m, WORKING_VALUE) stojącą bliżej kamery i z palikami 1,5 m",
    uwagi='±1 m; zgodne z G7 #24 (3,5–5 m); drzewa stoją za ścieżką/pasem trawnika, nie przy krawężniku', obszar='trasa_c')
add('szpaler', 'trasa C (Andersa–wiadukt–DK8): kadry letnie z drzewami w regularnym rzędzie w pasie drogowym', f"3 / 22", 'kadry', 'ESTIMATED',
    'zliczenie 22 obejrzanych kadrów trasy C (KartaView 18 + Panoramax 4; 2016–2021)',
    uwagi=f"rzędy młodych drzew: {fid2id['kv7119879']}, {fid2id['kv993066550']}, {fid2id['kv1326673765']}; pozostałe 19: brak drzew przy jezdni (trawnik, ekrany, wiadukt) albo masa zadrzewień/las za barierą; potwierdza G7 #23 (0 dojrzałych drzew przyulicznych / 100 m)", obszar='trasa_c')
add('fenologia', 'Białystok — stan ulistnienia z datowanych kadrów', '13 III bezlistne; 7–9 V liście młode/rozwijające się; 20–22 V pełne ulistnienie (pojedyncze drzewo jeszcze gołe); 4 X zielone z początkiem żółknięcia; 6 XI i 11 XI bezlistne, liście na ziemi', '', 'ESTIMATED',
    'daty z EXIF/metadanych kadrów (DateTimeOriginal Commons, datetime Panoramax); stan odczytany z obrazu',
    uwagi='kadry: ' + ', '.join(fid2id[k] for k in ['cm20210313102027', 'cm20220507153630', 'cm20200508104031', 'cm20200509123619', 'cm20200520103649', 'cm20210522101909', 'cm20201004144314', 'cm20201106155038', 'px0e1d9bd7', 'pxcbcb62c5']) + '; różne lata (2020–2026) — rozrzut międzyroczny ±7–10 dni')

with open(os.path.join(ROOT, 'manifest.csv'), 'w', newline='', encoding='utf-8') as fh:
    w = csv.DictWriter(fh, fieldnames=COLS, quoting=csv.QUOTE_MINIMAL)
    w.writeheader(); w.writerows(rows)
import collections
print(len(rows), collections.Counter(r['kategoria'] for r in rows), collections.Counter(r['status'] for r in rows))
print('kadry', len(K), collections.Counter(r['obszar'] for r in K), 'SF', len(SF), collections.Counter(r['żywopłot'] for r in SF))
for r in K: print(r['id'], r['plik_lokalny'].split('/')[-1], r['ulica_osm_najbliższa'], r['odległość_od_osi_m'], r['kierunek_deg'])
