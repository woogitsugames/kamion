"""Build manifest.csv + files/ for M63 (K63) — research/plant-gates-s21."""
import sys, os, csv, json, hashlib, math, re, urllib.parse
import xml.etree.ElementTree as ET
from PIL import Image
from pyproj import Transformer

S = sys.argv[1]; OUT = sys.argv[2]
FILES = os.path.join(OUT, 'files'); os.makedirs(FILES, exist_ok=True)
info = json.load(open(S + '/m63/info.json'))
T = Transformer.from_crs(4326, 2180, always_xy=True)
ACC = '2026-11-15'
P20 = 'origin/research/mistral-p20-plant-gates @822bfe317, research/mistral/p20-plant-gates/manifest.csv'
ORTHO = ('GUGiK ortofotomapa WMS PZGIK/ORTO/WMS/HighResolution (Raster, EPSG:2180); arkusze N-34-107-C-b-4-1 (A) i N-34-107-C-b-3-2 (B), '
         '2025-04-18, 0,05 m, GK-FOTO.6201.5.2025 (skorowidz SkorowidzeWgAktualnosci)')
NMPT = ('GUGiK NMPT lot 2023-09-15, 0,5 m, PL-EVRF2007-NH (opendata.geoportal.gov.pl/NumDaneWys/NMPT/78825/: N-34-107-C-b-3-2, -4-1, -4-3) '
        'minus NMT 1 m WCS DTM_PL-KRON86-NH_TIFF')
OSMU = 'https://api.openstreetmap.org/api/0.6/map?bbox=23.182,53.1025,23.2005,53.1075 (2026-11-15 10:18 UTC)'
LIC_G = 'dane PZGiK (GUGiK), bez opłat'
LIC_O = 'ODbL 1.0 © autorzy OpenStreetMap'
COLS = ['id', 'obiekt', 'element', 'parametr', 'wartość', 'jednostka', 'lat', 'lon', 'osm_id', 'kierunek_deg', 'odległość_m', 'data_zdjęcia', 'sezon',
        'pora_dnia', 'opis_co_widać', 'url_źródła', 'licencja', 'autor', 'data_dostępu', 'status', 'uwagi', 'p20', 'plik', 'url_pliku', 'sha256']
rows = []

# polygons for distance
root = ET.parse(S + '/m63/osm/plants.osm').getroot()
N = {n.get('id'): (float(n.get('lon')), float(n.get('lat'))) for n in root.findall('node')}
POLY = {}
for w in root.findall('way'):
    if w.get('id') in ('471492583', '513010463'):
        POLY[w.get('id')] = [T.transform(*N[x.get('ref')]) for x in w.findall('nd')]


def pdist(lat, lon, wid):
    p = T.transform(lon, lat); P = POLY[wid]; best = 1e9
    for a, b in zip(P, P[1:]):
        dx, dy = b[0] - a[0], b[1] - a[1]; L2 = dx * dx + dy * dy
        t = max(0, min(1, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / L2))
        best = min(best, math.hypot(a[0] + t * dx - p[0], a[1] + t * dy - p[1]))
    return round(best, 1)


def add(**k):
    r = {c: '' for c in COLS}
    r.update({kk: ('' if v is None else str(v)) for kk, v in k.items()})
    r['id'] = f'K63-{len(rows) + 1:03d}'
    r['data_dostępu'] = r['data_dostępu'] or ACC
    rows.append(r)


def sha(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()


def put(src, name):
    dst = f'{FILES}/{name}'
    im = Image.open(src).convert('RGB'); im.thumbnail((1600, 1600)); im.save(dst, quality=82)
    return 'files/' + name, sha(dst)


def commons(title):
    p = info[title]; ii = p['imageinfo'][0]; em = ii.get('extmetadata', {})
    lic = em.get('LicenseShortName', {}).get('value', '')
    art = re.sub('<[^>]+>', '', em.get('Artist', {}).get('value', '')).strip()
    page = 'https://commons.wikimedia.org/wiki/' + urllib.parse.quote(title.replace(' ', '_'), safe=':')
    return page, ii['url'].split('?')[0], lic, art, ii.get('sha1', '')


def slug(t):
    return re.sub(r'[^A-Za-z0-9_-]+', '_', t[5:].rsplit('.', 1)[0]).strip('_')


# ---------------- identification / segments
add(obiekt='A', element='segment', parametr='obrys OSM (way 471492583)', wartość='15 węzłów / 14 boków, obwód 515,7 m, pow. 13 712 m²; EPSG:2180 E[780648,2; 780790,8] N[590300,3; 590468,3]',
    jednostka='m', lat='53.104484', lon='23.195067', osm_id='way 471492583 (building=industrial)', url_źródła=OSMU, licencja=LIC_O, autor='społeczność OSM', status='SOURCED',
    p20='przejęte z P20-001, sprawdzone (identyczne)', uwagi='Boki: m.in. 133,9 m (ściana ESE) i 83,8 m (ściana NNE od ul. Kuronia, węzły 4656499194 → 4656499193). OSM obejmuje część N (A1+A3); hala S jest poza tym obrysem (w EGiB wg P20 razem).')
add(obiekt='A', element='segment', parametr='działka ewidencyjna', wartość='206101_1.0021.767/20 (obręb Dojlidy)', lat='53.104900', lon='23.195650',
    url_źródła='https://integracja.gugik.gov.pl/cgi-bin/KrajowaIntegracjaEwidencjiGruntow (GetFeatureInfo, E 780730 N 590400)', licencja=LIC_G, autor='GUGiK / starosta', status='SOURCED',
    p20='przejęte z P20 §1, sprawdzone (działka); id budynku EGiB 206101_1.0021.1495_BUD — usługa nie zwróciła warstwy budynków → UNVERIFIED')
add(obiekt='A', element='segment', parametr='wysokość LoD1 2024 (cały obrys)', wartość='18,92', jednostka='m', status='UNVERIFIED',
    p20='P20-003 — nie sprawdzone w s21 (brak dostępu do pliku LoD1 dla budynku); liczba używana tylko jako „co ma dziś gra”',
    uwagi='Wg NMPT (niżej) 18,9 m to wartość zbliżona tylko do wysokiej części A1; dla A3 i hali S za dużo o 4–6 m.')
for seg, val, box, note in [
    ('A1 — wysoka hala (NE), dach płaski z rzędami świetlików', 'mediana 18,13; zakres 17,7 (SW) – 18,8 (NE)', 'E[780674; 780790] N[590314; 590462]',
     'P20-004 (18,19) przejęte, sprawdzone (różnica 0,06 m). Dach lekko opada ku SW (~1,1 m na 130 m, profil co 10 m) — ESTIMATED; w grze płaski 18,1–18,4 m wystarczy.'),
    ('A3 — niższy pas po stronie NW/W hali A1', 'ok. 12,5 (12,4–12,6)', 'E[780648; 780726] N[590334; 590468]',
     'P20-006 (12,43) przejęte, sprawdzone. Mediana okna P20 13,39 jest zawyżona przez komórki A1 w oknie — użyć 12,5. Uskok A1→A3 widać na kadrze P11-094 (stosunek wysokości 0,69 → 12,7 m przy 18,4 m).'),
    ('hala S (dawne „A2” + „A4” P20) — JEDEN dach dwuspadowy z kalenicą E–W', 'okap N ok. 13,2–13,5; kalenica ok. 15,4–15,5 (N≈590264); okap S ok. 13,5', 'E[780550; 780706] N[590210; 590312]',
     'FIX P20-005/P20-007: „A2 = 14,32 m” i „A4 = 12,97 m” to nie osobne segmenty, tylko dwie strony tego samego dachu (profil N–S co 6 m przy E 780640: 13,24 → 15,50 → 13,51). Mediana okien P20 powtórzona: 14,35 / 13,83.'),
    ('łącznik A1 ↔ hala S + zbiornik okrągły', 'łącznik 10–12; zbiornik ok. 12', 'E[780657; 780713] N[590300; 590346]', 'P20-008 (element 16,65 m) — nie potwierdzony jako osobny segment (pojedyncze komórki dachowych urządzeń) → odrzucone.')]:
    add(obiekt='A', element='segment', parametr='wysokość ' + seg, wartość=val, jednostka='m', url_źródła=NMPT, licencja=LIC_G, autor='GUGiK', status='ESTIMATED',
        uwagi='metoda: nDSM = NMPT 2023 (0,5 m) − NMT (1 m, KRON86; różnica układów ~0,1–0,2 m nie korygowana); komponenty spójne nDSM > 4 m w przedziałach 1,5 m, mediana; ' + box + '. ' + note.split(' — ')[0] if False else 'metoda: nDSM = NMPT 2023 (0,5 m) − NMT (1 m, KRON86; różnica układów ~0,1–0,2 m nie korygowana); komponenty spójne nDSM > 4 m, mediana; ' + box,
        p20=note)
add(obiekt='A', element='segment', parametr='uskoki wysokości', wartość='A1→A3: 18,1→12,5 m wzdłuż krawędzi NW hali A1 (na ścianie NNE ok. 66 m od narożnika E); A1→łącznik/hala S: 17,7→10–12 m przy S narożniku A1; hala S: brak uskoku (dach dwuspadowy)',
    url_źródła=NMPT + '; kadr P11-094', licencja=LIC_G, autor='GUGiK', status='ESTIMATED', p20='FIX P20-009…011: uskok A2→A4 nie istnieje (jedna hala z kalenicą)',
    uwagi='Położenie uskoku na ścianie NNE: przecięcie promienia z kadru P11-094 (x=1325 px / 1600) z linią ściany OSM, kalibracja kamery na narożnikach OSM (HFOV 68,7°).', plik='files/ndsm_A.png')
add(obiekt='B', element='segment', parametr='obrys OSM (way 513010463)', wartość='7 węzłów / 6 boków, obwód 450,9 m, pow. 11 173 m²: 151,1 (NW, wzdłuż ul. Kuronia) / 74,3 / 138,8 (SE) / 4,4 / 12,3 / 69,8 m',
    jednostka='m', lat='53.105195', lon='23.186953', osm_id='way 513010463 (building=industrial, man_made=works)', url_źródła=OSMU, licencja=LIC_O, autor='społeczność OSM', status='SOURCED',
    p20='przejęte z P20-013, sprawdzone (identyczne)')
add(obiekt='B', element='segment', parametr='działka ewidencyjna', wartość='206101_1.0021.767/29', url_źródła='KIEG GetFeatureInfo (E 780175 N 590417)', licencja=LIC_G, autor='GUGiK / starosta', status='SOURCED',
    p20='przejęte z P20 §1, sprawdzone (działka); id budynku EGiB UNVERIFIED')
add(obiekt='B', element='segment', parametr='wysokość LoD1 2024', wartość='12,72', jednostka='m', status='UNVERIFIED', p20='P20-015 — nie sprawdzone w s21')
for seg, val, note in [
    ('B-hala główna (ciemnoszara)', 'mediana 12,5–12,9 (okna P20 B-M/B-E); komponent 12,7', 'P20-017/018/019 (11,94 / 12,03 / 12,04) — przejęte w granicy ±0,7 m; różnica = inny lot NMPT (P20: WCS) i układ wysokości; do gry 12,5 ±0,5 m'),
    ('B-pas frontowy W (dwukondygnacyjny blok biurowy od ul. Mickiewicza)', '9,6–10,1 (profil 4–10 m od lica, co 5 m wzdłuż 70 m)', 'FIX P20-016 (10,97 z okna mieszającego front i halę) → 9,6–10,1 m'),
    ('B-niski pas NW wzdłuż ul. Kuronia', 'ok. 5,7–6,3', 'P20-020 (5,24) przejęte z poprawką (+0,5 m)'),
    ('B-aneks E', 'ok. 9–11 (mała powierzchnia ~130 m²)', 'P20-022 (8,99) — UNVERIFIED (za mało komórek, 124 w oknie P20)')]:
    add(obiekt='B', element='segment', parametr='wysokość ' + seg, wartość=val, jednostka='m', url_źródła=NMPT, licencja=LIC_G, autor='GUGiK', status='ESTIMATED', p20=note,
        uwagi='metoda jak dla A; mapa wysokości files/ndsm_B.png', plik='files/ndsm_B.png')
add(obiekt='B', element='segment', parametr='„ciemniejsza, wyższa część frontowa” z P11-063 — rozstrzygnięcie',
    wartość='Ciemna (antracytowa) jest HALA GŁÓWNA 12,5 m, a „długa niższa biała hala” to niski pas NW 5,7–6,3 m wzdłuż Kuronia; od Mickiewicza stoi dwukondygnacyjny jasny blok biurowy 9,6–10,1 m z dwiema ciemnymi skrzyniami na napisy firmowe, wysuniętymi ponad attykę bloku',
    url_źródła='kadry P11-063, 182855, 141331, 182816 + NMPT', status='ESTIMATED',
    p20='FIX P20-023: P20 porównał front z halą tylko liczbowo; kadry pokazują, że „wyższa ciemna” to hala główna widziana za niskim pasem, a ciemne skrzynie napisów to wyższe elementy frontu',
    uwagi='wysokość skrzyń napisów nad blokiem biurowym: ok. 1,5–2,5 m (proporcja na kadrze 182855 do wysokości bloku 10 m) — ESTIMATED zgrubnie')

# ---------------- walls A
A_FR = 'File:20230903 135016 September 2023 in Białystok.jpg'
add(obiekt='A', element='ściana', parametr='ściana NNE (od ul. Kuronia), długość i podział', wartość='83,8 m (OSM): 0–65,8 m wysoka część A1 (ok. 18,4 m), 65,8–83,8 m niższa część A3 (ok. 12,5–12,7 m)',
    jednostka='m', lat='53.105375', lon='23.196035', osm_id='way 471492583 (węzły 4656499194→4656499193)', url_źródła='kadr P11-094 + OSM + NMPT', status='ESTIMATED',
    p20='FIX P20-024…: P20 nazywa tę ścianę „wschodnią” i liczy bramy „od końca północnego” — kadr P11-094 i OSM pokazują ścianę NNE od Kuronia, liczenie od narożnika E',
    uwagi='kalibracja kamery P11-094 na narożnikach OSM (E 43,1 m, N 105 m od kamery): f = 1170 px przy 1600 px (HFOV 68,7°, zgodne z typowym telefonem); pozycje = przecięcie promieni z linią ściany')
add(obiekt='A', element='ściana', parametr='ściana NNE — okładzina', wartość='jasnoszare panele warstwowe układane poziomo; moduł (wysokość panelu) ok. 1,0–1,1 m; pionowe styki co kilka paneli; brak pasa okien i okien w części A1; w części A3 okna w dwóch poziomach w pionowym pasie (klatka?)',
    jednostka='m', url_źródła='kadr P11-094 (wycinki 1,5–3×) + P11-095', status='ESTIMATED',
    p20='P20-024/025/026/027/028 przejęte, sprawdzone dla A1; FIX P20-028: „okna BRAK” nie dotyczy części A3 (okna) ani ściany ESE przy narożniku',
    uwagi='moduł: 25 px na panel przy wysokości ściany 423 px (= 18,4 m) → 1,09 m; drugi odczyt (P11-095): ok. 5,2 panelu na wysokość bramy')
add(obiekt='A', element='ściana', parametr='ściana NNE — cokół', wartość='ciemnoszary pas u dołu ok. 0,9 m', jednostka='m', url_źródła='kadr P11-094 (20 px / 423 px × 18,4 m)', status='ESTIMATED',
    p20='P20-029 (~1,0 m) przejęte z poprawką (0,9)', uwagi='materiał UNVERIFIED (cokół betonowy lub ciemny panel)')
add(obiekt='A', element='ściana', parametr='ściana NNE — attyka / krawędź dachu', wartość='cienka obróbka blacharska, bez wyraźnej attyki', url_źródła='kadr P11-094', status='SOURCED', p20='przejęte z P20-030, sprawdzone')
add(obiekt='A', element='ściana', parametr='ściana NNE — napis firmowy', wartość='duża biała tablica z napisem w lewej części ściany — napis firmowy, nie odtwarzamy (w grze: jasna gładka tablica bez treści albo brak)', url_źródła='kadr P11-094', status='SOURCED',
    p20='przejęte z P20-031, sprawdzone')
add(obiekt='A', element='latarnia', parametr='lampy na ścianie NNE (liczba, położenie, wysokość)', wartość='4 lampy (naświetlacze na krótkich wysięgnikach) w 7,8 / 24,5 / 40,5 / 57,8 m od narożnika E, ok. 8,3 m nad terenem; 1 lampa na części A3',
    jednostka='m', url_źródła='kadr P11-094 (wycinki)', status='ESTIMATED', p20='P20-032/055 (4 szt. „pod okapem”) przejęte z poprawką: lampy na ok. 45 % wysokości, nie pod okapem',
    uwagi='pozycje z kalibracji kamery; wysokość = (wysokość lampy w px / wysokość ściany w px) × 18,4 m')
add(obiekt='A', element='ściana', parametr='ściana ESE (od parkingu) — okładzina i otwory', wartość='te same jasnoszare panele poziome; przy narożniku E pionowy pas 2–3 okien i napis firmowy (nie odtwarzamy); dalsza część ściany (ok. 130 m) — bram i okien nie widać (UNVERIFIED)',
    jednostka='', url_źródła='kadry P11-094, P11-095, P11-122 (8866)', status='SOURCED', p20='FIX P20-036 (UNVERIFIED) → częściowo opisana',
    uwagi='na ortofoto 2025: przed ścianą ESE parking osobowy (rzędy aut); brak placu manewrowego dla ciężarówek')
add(obiekt='A', element='ściana', parametr='ściana W/NW części A3 (od placu)', wartość='na ortofoto 2025 przy ścianie W części A3 stoją naczepy/ciężarówki — prawdopodobnie doki; liczby i typu bram nie widać (brak kadru)',
    url_źródła=ORTHO, licencja=LIC_G, autor='GUGiK', status='UNVERIFIED', p20='nowe (P20 nie opisał)', plik='files/ortho_A_all_025.jpg',
    uwagi='dojazd z ul. Kuronia przy narożniku NW; do potwierdzenia nowym kadrem')
add(obiekt='A', element='ściana', parametr='ściany hali S (S i W)', wartość='na kadrach z ul. Karpińskiego (2024-06-23 124755, 124743, z jadącego auta): jasnoszara okładzina, ciemniejszy poziomy pas, przybudówki techniczne; linia dachu szczytu W wznosi się — zgodne z dachem dwuspadowym z NMPT',
    url_źródła='kadry 124755, 124743', status='UNVERIFIED', p20='P20-036 („południowa UNVERIFIED”) — nadal UNVERIFIED w szczegółach',
    uwagi='kadry rozmyte w ruchu, przypisanie do hali S z pozycji GPS (26 m i 52 m od obrysu EGiB wg P20) — ESTIMATED')
add(obiekt='A', element='ściana', parametr='dach A1', wartość='płaski, jasnoszara membrana; świetliki w regularnej siatce co ok. 9,7 m', jednostka='m', url_źródła=ORTHO, licencja=LIC_G, autor='GUGiK', status='ESTIMATED',
    plik='files/ortho_A_NNE_005.jpg', p20='nowe', uwagi='odstęp świetlików 195 px × 0,05 m')

# ---------------- gates A
G = [('brama 1 (bliżej narożnika E)', '11,9–17,0 m od narożnika E (środek 14,5 m; 0,17 długości ściany 83,8 m)', 'ok. 5,1–5,3', 'ok. 6,4 (proporcja do ściany) / ok. 5,5–5,9 (5,2–5,9 modułu panelu)'),
     ('brama 2', '51,1–57,8 m od narożnika E (środek 54,5 m; 0,65 długości)', 'ok. 6,7–7,4', 'ok. 6,8 (proporcja do ściany)')]
for name, pos, wd, ht in G:
    add(obiekt='A', element='brama', parametr=f'{name}: położenie na ścianie NNE', wartość=pos, jednostka='m', url_źródła='kadr P11-094 + OSM', status='ESTIMATED',
        p20='FIX P20-044/047 (0,60 i 0,80 „od końca N”): ułamki z obrazu bez perspektywy; po kalibracji 0,17 i 0,65 od narożnika E', uwagi='dwie kalibracje (narożniki z OSM / z NMPT) różnią się o ≤ 3 m')
    add(obiekt='A', element='brama', parametr=f'{name}: szerokość × wysokość', wartość=f'{wd} × {ht}', jednostka='m', url_źródła='kadry P11-094, P11-095', status='ESTIMATED',
        p20='FIX P20-043/046 (4,5–5,0 × 4,5–5,0): niedoszacowane — proporcja do wysokości ściany 18,4 m (NMPT) daje ponad 6 m',
        uwagi='szerokość: przecięcie promieni krawędzi bramy ze ścianą (±0,5 m dla bramy 1, ±1 m dla bramy 2); wysokość: stosunek pikseli brama/ściana na tej samej pionowej linii × 18,4 m (±0,5 m). Karty katalogowe bram przemysłowych podają maks. 6000 mm wysokości (bez większych na zamówienie) — wynik ~6,4 m jest na granicy; niepewność wysokości ściany i pionu kamery ±10 %.')
add(obiekt='A', element='brama', parametr='liczba bram w ścianie NNE', wartość='2', jednostka='szt.', url_źródła='kadry P11-094, P11-095', status='SOURCED', p20='przejęte z P20-038, sprawdzone')
add(obiekt='A', element='brama', parametr='typ, podział, okienka, kolor', wartość='szare skrzydła w ramie ciemniejszej obróbki, bez okienek; powierzchnia z gęstymi poziomymi przetłoczeniami — z kadru nie da się rozstrzygnąć, czy to brama segmentowa (sekcje ~0,5 m), czy rolowana',
    url_źródła='kadr P11-095 (wycinek 3× z autokontrastem), P11-094', status='UNVERIFIED',
    p20='FIX P20-039/040 („segmentowa”, „~5 pionowych paneli”): pionowych paneli nie ma — podział jest poziomy; typ UNVERIFIED; P20-041/042 (bez okienek, szara) przejęte, sprawdzone')
add(obiekt='A', element='brama', parametr='dojazd / rampa przed bramami NNE', wartość='brak: przed bramami trawiasta skarpa w dół do chodnika i ogrodzenie; brak utwardzonego podjazdu (ortofoto 2025 i kadry)', url_źródła=ORTHO + '; kadry P11-094/095',
    licencja=LIC_G, status='SOURCED', plik='files/ortho_A_NNE_005.jpg', p20='FIX P20-048 („płaski asfalt przed bramami”) → trawa, brak dojazdu',
    uwagi='bramy od strony Kuronii wyglądają na nieużywane / awaryjne — w grze bez podjazdu')
add(obiekt='A', element='brama', parametr='typowe wymiary bram przemysłowych (karta katalogowa, bez nazwy producenta w grze)', wartość='„Szerokość światła … Maks.: 8000 mm; Wysokość światła … 6000 mm”; „Wysokość sekcji: 545 mm”',
    url_źródła='https://www.assaabloyentrance.com/master-blueprint/pl/product-assets/commercial-industrial-doors/oh1042p/downloads/product-datasheet/product_datasheet_assa_abloy_oh1042p_psdi_pl-pl.pdf (pkt 1.2.1; sha256 5168698126ec…4c86)',
    licencja='dokument producenta — cytat faktów', status='SOURCED', p20='P20-049 przejęte, cytat sprawdzony i poprawiony do brzmienia z pliku')
add(obiekt='A', element='brama', parametr='typowe wymiary bram (specyfikacja techniczna)', wartość='„szerokość maksymalna - 4500mm, z kształtownikiem usztywniającym od 4500mm do 8000mm; wysokość maksymalna - 6000mm”',
    url_źródła='https://staszynska.pl/wp-content/uploads/2019/02/STASZY%C5%83SKA-Bramy-segmentowe-przemys%C5%82owe-specyfikacja-techniczna.pdf (sha256 ce1e7b553755…acc)', licencja='dokument producenta — cytat faktów',
    status='SOURCED', p20='przejęte z P20-050, cytat sprawdzony')

# ---------------- surroundings A
add(obiekt='A', element='ogrodzenie', parametr='typ, kolor, wysokość, położenie', wartość='lekkie ogrodzenie z jasnoszarej (ocynkowanej) siatki/paneli drucianych na cienkich słupkach, u dołu skarpy przy chodniku; ok. 1,5–2,0 m; ok. 8–10 m od ściany NNE',
    jednostka='m', url_źródła='kadry P11-094, P11-095 (wycinki) + ortofoto 0,05 m', status='ESTIMATED',
    p20='P20-051 (siatka na słupkach) przejęte; FIX P20-052 (~2,0 m z kadru 134854 ze 129 m) — wysokość z bliższych kadrów 1,5–2,0 m; P20-053 (brak białego płotu panelowego) przejęte, sprawdzone',
    uwagi='wysokość: słupki ~45 px przy bramie 155 px (bliżej kamery niż ściana, więc górna granica) — zgrubnie')
add(obiekt='A', element='ogrodzenie', parametr='skarpa i zieleń u podstawy ściany NNE', wartość='trawiasta skarpa opadająca od cokołu do chodnika; 2 młode drzewka; żywopłotu NIE widać',
    url_źródła='kadry P11-094, P11-095', status='SOURCED', p20='FIX P20-057 („niski strzyżony żywopłot”) → brak żywopłotu w kadrach 2023')
add(obiekt='A', element='latarnia', parametr='latarnie uliczne przy ścianie NNE', wartość='latarnia z jednym łukowym wysięgnikiem przy jezdni po stronie kamery (P11-094, prawa krawędź kadru)', url_źródła='kadr P11-094', status='SOURCED',
    p20='P20-054 („2 szt. po przeciwnej stronie”) — nie potwierdzam liczby; widać 1 latarnię', uwagi='typ oprawy UNVERIFIED')
add(obiekt='A', element='znak', parametr='znak przed kamerą P11-094 (pozycja)', wartość='słupek ze znakiem widzianym od tyłu (tarcza prostokątna, typ UNVERIFIED — możliwe D-6), ok. 6 m od kamery w azymucie ok. 230°',
    jednostka='m', lat='53.105410', lon='23.196910', url_źródła='kadr P11-094 (podstawa słupka y=775/900 px, f=1170 px, oko 1,6 m, kamera ~poziomo)', status='ESTIMATED',
    p20='P20-056 UNVERIFIED → pozycja ESTIMATED; typ nadal UNVERIFIED', uwagi='d = 1,6 m × f / (y_podstawy − y_horyzontu) = 1,6 × 1170 / 325 ≈ 5,8 m (±2 m przy nieznanym pochyleniu kamery). Korekta dla gry: znak ~6 m przed kamerą kontrolną P11-094, na chodniku przy przejściu.')

# ---------------- walls / gates B
add(obiekt='B', element='ściana', parametr='blok biurowy W/SW (od ul. Mickiewicza)', wartość='2 kondygnacje: góra jasna (kremowa), dół ciemnoszary z cegłą/klinkierem (UNVERIFIED materiał) i pasmowymi oknami w ciemnych ramach z balustradkami; poziomy czerwony pas nad parterem; dwie antracytowe skrzynie z napisem firmowym (nie odtwarzamy) wyższe od bloku',
    url_źródła='kadry P11-063 (wycinek 3×), 141331, 182855', status='SOURCED', p20='nowe (P20-058 UNVERIFIED „w toku”)')
add(obiekt='B', element='ściana', parametr='niski pas NW wzdłuż ul. Kuronia', wartość='jasna (kremowa) górna część, dół ciemnoszary z oknami, czerwony pas; na dachu ażurowa szara osłona urządzeń HVAC; przy narożniku NE czerwony portal/daszek nad wejściem',
    url_źródła='kadry 182855, 182816, 182815, 151220', status='SOURCED', p20='nowe')
add(obiekt='B', element='ściana', parametr='hala główna — okładzina', wartość='antracytowe (ciemnoszare) panele; od N poziome panele z pionowymi stykami co kilka m; od S widoczne pionowe styki; szczyt E z napisem firmowym (nie odtwarzamy); dach płaski ze świetlikami pasmowymi (ortofoto)',
    url_źródła='kadry 182816, 141331 + ortofoto', status='SOURCED', p20='nowe', plik='files/ortho_B_all_02.jpg')
add(obiekt='B', element='brama', parametr='bramy / doki', wartość='ściana SE przy narożniku E: co najmniej 2 doki z numerami (tablice „1”, „2”) i czerwonymi uszczelnieniami/osłonami w ciemnych wysuniętych obudowach; od Kuronii i Mickiewicza bram brak (wejścia osobowe)',
    url_źródła='kadr 141331 (wycinek), 182815/182816, ortofoto (plac przy ścianie SE)', status='ESTIMATED', p20='FIX P20-059 (UNVERIFIED) → doki na ścianie SE',
    uwagi='wymiary doków UNVERIFIED (kadr z ~150 m przez bramę przesuwną)')
add(obiekt='B', element='ogrodzenie', parametr='ogrodzenie i brama wjazdowa', wartość='ciemnoszare ogrodzenie panelowe; stalowa brama przesuwna z kratownicą (ukośne pręty) na wjeździe od ul. Mickiewicza (2019 i 2024)',
    url_źródła='kadry 141331, 6724 (2019, wycinek)', status='SOURCED', p20='FIX P20-060 (UNVERIFIED) → opisane',
    uwagi='czerwono-żółte ogrodzenie w pasie dzielącym Kuronii (kadry 182815/182816) to wygrodzenie drogowe, nie płot zakładu')

# ---------------- frames
FR = [
    # (title, obj, pos-from, desc, kierunek, note)
    (A_FR, 'A', 'P11-094', 'Narożnik E hali A z drugiej strony jezdni: z lewej mocno skrócona ściana ESE z pionowym napisem, po prawej ściana NNE z dużą tablicą napisu, dwiema szarymi bramami i 4 lampami; na końcu ściany niższa część z oknami; skarpa trawiasta, lekkie ogrodzenie, chodnik, latarnia', '242,5 (ESTIMATED z kalibracji na narożnikach OSM)', 'najlepszy kadr A dla artysty (ściana NNE, bramy)'),
    ('File:20230903 135017 September 2023 in Białystok.jpg', 'A', 'P11-095', 'Ten sam narożnik z bliższego miejsca: brama 1 prawie od frontu, okna przy narożniku na ścianie ESE, w głębi parking; skarpa i ogrodzenie z drutu', 'UNVERIFIED', 'kadr A nr 2: brama 1 i ogrodzenie'),
    ('File:8866 November 2022 in Białystok.jpg', 'A', 'P11-122', 'Wieczór, listopad: narożnik E od strony parkingu — ściana ESE z napisem i pionowym pasem okien, ściana NNE z napisem i bramą; pełny parking aut', 'UNVERIFIED', 'GPS EXIF wypada WEWNĄTRZ budynku (E 780748,9 N 590422,6) — błędna pozycja, kamera stała na parkingu SE; kadr A nr 3 (ściana ESE)'),
    ('File:20230903 134854 September 2023 in Białystok.jpg', 'A', '—', 'Droga rowerowa i chodnik wzdłuż Kuronii na W; w osi kadru długa jasna hala ok. 130 m dalej (najpewniej A — narożnik E w azymucie 274°), z prawej przy jezdni ogrodzenie z czerwonymi słupkami', 'ok. 270 (ESTIMATED z osi drogi)', 'szczegółów hali nie da się odczytać; ogrodzenie z kadru to wygrodzenie przy jezdni, nie płot zakładu'),
    ('File:20230903 134802 September 2023 in Białystok.jpg', 'A', '—', 'Chodnik i droga rowerowa na W, pole po prawej; na lewej krawędzi fragment hali A z częścią napisu, ok. 200 m', 'UNVERIFIED', 'kontekst odległego widoku'),
    ('File:20240623 124755 June 2024 in Białystok.jpg', 'A', '—', 'Z jadącego auta (rozmyte): po lewej szara długa hala z małym logo i masztami flagowymi, po prawej budynki biurowe', 'UNVERIFIED', 'pozycja 26 m na S od hali S (wg obrysu EGiB z P20) → przypisanie do hali S ESTIMATED'),
    ('File:20240623 124743 June 2024 in Białystok.jpg', 'A', '—', 'Z jadącego auta: dwie duże szare hale z placem składowym między nimi; prawa hala z ciemniejszym poziomym pasem, przybudówką techniczną i linią dachu wznoszącą się w prawo', 'UNVERIFIED', 'prawa hala = najpewniej szczyt W hali S (ESTIMATED)'),
    ('File:20240623 124644 June 2024 in Białystok.jpg', 'B', 'P11-063', 'Skrzyżowanie Mickiewicza/Kuronia: po prawej narożnik B — dwie antracytowe skrzynie z napisem, jasne fragmenty ścian, pasmo okien w ciemnych ramach, w głębi niższa jasna hala', 'ok. 100 (M58 C58-002, ESTIMATED)', 'kamera 104 m od obrysu OSM (> 60 m) — kadr referencyjny z zadania'),
    ('File:20240623 141331 June 2024 in Białystok.jpg', 'B', '—', 'Od S przez zamkniętą bramę przesuwną: dwukondygnacyjny blok biurowy (jasna góra, ciemny dół z oknami, czerwony pas), za nim antracytowa hala z napisem i doki z numerami i czerwonymi osłonami', 'UNVERIFIED', 'najlepszy kadr B nr 2 (blok + hala + doki)'),
    ('File:20230814 182855 August 2023 in Białystok.jpg', 'B', '—', 'Od NW zza Kuronii: długi niski jasny pas z czerwonym paskiem i ciemnym cokołem, na dachu urządzenia, za nim wyższa ciemna hala; z prawej blok biurowy z dwiema ciemnymi skrzyniami napisu; na pierwszym planie barierki', 'UNVERIFIED', 'najlepszy kadr B nr 1 (rozstrzyga „ciemna wyższa + biała niższa”)'),
    ('File:20230814 182815 August 2023 in Białystok.jpg', 'B', '—', 'Od NE zza Kuronii i skarpy: szczyt E antracytowej hali z napisem, czerwony portal nad wejściem, niski jasny pas z oknami; z lewej srebrne zbiorniki (sąsiedni obiekt)', 'UNVERIFIED', ''),
    ('File:20230814 182816 August 2023 in Białystok.jpg', 'B', '—', 'Jak wyżej, kadr przesunięty: lepiej widać poziome panele hali, osłonę HVAC na dachu niskiego pasa i czerwony portal', 'UNVERIFIED', 'najlepszy kadr B nr 3 (okładzina hali i niskiego pasa)'),
    ('File:20230910 151220 September 2023 in Białystok.jpg', 'B', '—', 'Od N zza Kuronii: cała długość B — niski jasny pas z czerwonym paskiem, nad nim ciemna hala, latarnie, trawnik i chodnik', 'UNVERIFIED', 'brak GPS'),
    ('File:6721 Ulica Jacka Kuronia, Bialystok November 2019.jpg', 'B', '—', 'Listopad 2019: Kuronia na E; po prawej B — ciemna górna część, jasny dół z czerwonym pasem, ogrodzenie', 'UNVERIFIED', 'brak GPS; stan 2019 (budynek już stoi)'),
    ('File:6724 Jacka Kuronia street in Bialystok November 2019.jpg', 'B', '—', 'Listopad 2019: Kuronia na E; po prawej B z czerwonym portalem wejścia, ciemną ścianą z małym napisem, kratownicowa brama przesuwna i ogrodzenie panelowe', 'UNVERIFIED', 'brak GPS; potwierdza bramę i portal'),
    ('File:20230910 151311 September 2023 in Białystok.jpg', 'B', '—', 'Droga rowerowa na W; po prawej daleko długa jasna hala (niski pas B), w osi inny biurowiec z napisem', 'UNVERIFIED', 'kamera ok. 75 m od obrysu (> 60 m) — tylko kontekst'),
]
REJ = [
    ('File:20230903 135135 September 2023 in Białystok.jpg', 'A', 'P11-093: ulica, latarnie, zieleń, biurowce w tle — hali A nie widać', 'przejęte odrzucenie z P20-063, sprawdzone'),
    ('File:8865 November 2022 in Białystok.jpg', 'A', 'samochód nauki jazdy na przejściu, w tle inny budynek — hali A nie widać', 'FIX P20-070 (UNVERIFIED) → odrzucony'),
    ('File:8864 November 2022 in Białystok.jpg', 'A', 'inny zakład za murem betonowym (napis firmowy innej firmy)', 'nowe odrzucenie'),
    ('File:8868 November 2022 in Białystok.jpg', 'A', 'inny zakład (hala z napisem innej firmy, mur betonowy)', 'nowe odrzucenie'),
    ('File:8867 November 2022 in Białystok.jpg', 'A', 'domy jednorodzinne za łąką', 'nowe odrzucenie'),
    ('File:8870 November 2022 in Białystok.jpg', 'A', 'biała hala z drabiną zewnętrzną i portiernią, czerwone słupki ogrodzenia — inna hala', 'FIX P20-071 (UNVERIFIED, przypisany do A) → odrzucony'),
    ('File:8869 November 2022 in Białystok.jpg', 'A', 'droga rowerowa i latarnie, po prawej fragment białej hali (nie do przypisania)', 'nowe odrzucenie'),
    ('File:20230903 134826 September 2023 in Białystok.jpg', 'A', 'inny zakład (napis innej firmy, mur z pnączami)', 'nowe odrzucenie'),
    ('File:6697 Adama Mickiewicza 94 Street in Białystok November 2019.jpg', 'B', 'drewniany dom jednorodzinny', 'FIX P20 §7 („seria B z 2019”) — nie B'),
    ('File:6698 Adama Mickiewicza 87 Street in Białystok November 2019.jpg', 'B', 'drewniany dom z czerwonym dachem i sklepami', 'jw.'),
    ('File:6703 Adama Mickiewicza Street in Białystok November 2019.jpg', 'B', 'przystanek autobusowy', 'jw.'),
    ('File:6706 Adama Mickiewicza Street in Białystok November 2019.jpg', 'B', 'skrzyżowanie z sygnalizacją, ulica w dal', 'jw.'),
    ('File:6709 Adama Mickiewicza Street in Białystok November 2019 in Bialystok.jpg', 'B', 'stacja transformatorowa przed szkołą', 'jw.'),
    ('File:6710 Adama Mickiewicza Street in Białystok November 2019 in Bialystok.jpg', 'B', 'widok wzdłuż Mickiewicza na centrum', 'jw.'),
    ('File:DSC 6711 Adama Mickiewicza Street in Białystok.jpg', 'B', 'budynek biurowy z łukową elewacją za płotem', 'jw.'),
    ('File:6712 Adama Mickiewicza Street in Białystok November 2019.jpg', 'B', 'zakład za płotem z cegły i stali (inny)', 'jw.'),
    ('File:6719 Jacka Kuronia Street in Białystok.jpg', 'B', 'skrzyżowanie, Kuronia na E — B poza kadrem', 'jw.'),
    ('File:6722 Intersection of Mickiewicza and Kuronia street in Bialystok 2019.jpg', 'B', 'skrzyżowanie i domy po drugiej stronie — B nie widać', 'jw.'),
    ('File:6726 November 2019 in Bialystok ulica Kuronia.jpg', 'B', 'srebrny zbiornik z drabiną za bramą kratownicową — wg ortofoto zbiorniki należą do obiektu na E od B', 'jw.'),
    ('File:6727 Ulica Kuronia w Białymstoku November 2019.jpg', 'B', 'hala w budowie (bloczki, rusztowania) — nie do przypisania', 'jw.'),
    ('File:20240623 124711 June 2024 in Białystok.jpg', 'B', 'odległe hale za polem', 'nowe odrzucenie'),
    ('File:20240623 124718 June 2024 in Białystok.jpg', 'B', 'skrzyżowanie z przejściem, hale daleko', 'nowe odrzucenie'),
    ('File:20240623 124734 June 2024 in Białystok.jpg', 'B', 'przeszklony biurowiec', 'nowe odrzucenie'),
    ('File:20230814 182947 August 2023 in Białystok.jpg', 'B', 'gmach sądu', 'nowe odrzucenie'),
    ('File:20230910 151312 September 2023 in Białystok.jpg', 'B', 'rowerzyści na drodze rowerowej, hale daleko', 'nowe odrzucenie'),
    ('File:20200726 083613 Sąd Rejonowy w Białymstoku, ul. Mickiewicza 103.jpg', 'B', 'gmach sądu i ulica', 'nowe odrzucenie'),
    ('File:20200726 084244 Żurawia Street in Białystok.jpg', 'B', 'chodnik i tuje przy ul. Żurawiej', 'nowe odrzucenie'),
    ('File:20240623 141702 June 2024 in Białystok.jpg', 'B', 'gmach sądu z parkingiem', 'nowe odrzucenie'),
    ('File:20240623 141915 June 2024 in Białystok.jpg', 'B', 'Kuronia na E, budynki daleko', 'nowe odrzucenie'),
]
GEO = {}
for line in open(S + '/m63/geo.txt'):
    p = line.split(None, 3)
    if len(p) == 4:
        GEO[p[3].strip()] = (float(p[1]), float(p[2]))
GEO['File:8866 November 2022 in Białystok.jpg'] = (53.1050889, 23.19588618)
for title, ob, p11, desc, hd, note in FR:
    pg, fu, lic, art, s1 = commons(title)
    ii = info[title]['imageinfo'][0]; dt = ii['extmetadata'].get('DateTimeOriginal', {}).get('value', '')[:10]
    lat, lon = GEO.get(title, ('', ''))
    dist = ''
    if lat:
        dist = pdist(lat, lon, '471492583' if ob == 'A' else '513010463')
    f, h = put(f'{S}/m63/dl/{slug(title)}.jpg', slug(title) + '.jpg')
    mon = int(dt[5:7]) if dt else 0
    se = {12: 'zima', 1: 'zima', 2: 'zima', 3: 'wiosna', 4: 'wiosna', 5: 'wiosna', 6: 'lato', 7: 'lato', 8: 'lato', 9: 'lato (wrzesień)', 10: 'jesień', 11: 'jesień'}.get(mon, '')
    add(obiekt=ob, element='kadr', parametr='kadr — co widać (OBEJRZANY)', wartość=p11, lat=f'{lat:.6f}' if lat else 'UNVERIFIED (brak GPS)', lon=f'{lon:.6f}' if lon else '',
        osm_id='way 471492583' if ob == 'A' else 'way 513010463', kierunek_deg=hd, odległość_m=dist, data_zdjęcia=dt, sezon=se,
        pora_dnia='wieczór' if title.startswith('File:88') else 'dzień', opis_co_widać=desc, url_źródła=pg, licencja=lic, autor=art, status='SOURCED',
        uwagi=(note + '; ' if note else '') + f'sha1 oryginału {s1}; plik = miniatura ≤1600 px', p20=('kadr P20' if p11 != '—' or 'Kuronia' in title else 'nowy'), plik=f, url_pliku=fu, sha256=h)
for title, ob, desc, p20n in REJ:
    pg, fu, lic, art, s1 = commons(title)
    add(obiekt=ob, element='kadr', parametr='kadr — co widać (OBEJRZANY, ODRZUCONY)', wartość='—', opis_co_widać=desc, url_źródła=pg, licencja=lic, autor=art, url_pliku=fu,
        status='UNVERIFIED', p20=p20n, uwagi='nie liczony jako kadr obiektu; pliku nie zapisano')

# extra files: ortho + nDSM maps
for n in ('A_NNE_005.jpg', 'A_all_025.jpg', 'B_all_02.jpg'):
    put(f'{S}/m63/ortho/{n}', 'ortho_' + n)
for n in ('ndsm_A.png', 'ndsm_B.png'):
    shutil = __import__('shutil'); shutil.copy(f'{S}/m63/{n}', f'{FILES}/{n}')
with open(os.path.join(OUT, 'manifest.csv'), 'w', newline='', encoding='utf-8') as fh:
    w = csv.DictWriter(fh, fieldnames=COLS, lineterminator='\n'); w.writeheader(); w.writerows(rows)
import collections
print('rows', len(rows), collections.Counter(r['element'] for r in rows), collections.Counter(r['status'] for r in rows))
