"""Build manifest.csv + files/ for M64 (K64) in the research output directory."""
import sys, os, csv, json, hashlib, shutil, urllib.parse
from PIL import Image

S = sys.argv[1]            # scratchpad
OUT = sys.argv[2]          # research/krywlany-airfield-s21
FILES = os.path.join(OUT, 'files')
os.makedirs(FILES, exist_ok=True)
info = json.load(open(S + '/m64/info.json'))
VR = {r['id']: r for r in json.load(open(S + '/m64/view_results.json'))}
ACC = '2026-11-15'
ORTHO_SRC = ('GUGiK ortofotomapa, WMS PZGIK/ORTO/WMS/HighResolution (warstwa Raster, EPSG:2180); arkusz N-34-107-C-b-3-4 '
             '(pas, pole wzlotów) / N-34-107-C-b-3-2 (część N: hangary, płot N), aktualność 2025-04-18, piksel 0,05 m, '
             'zgłoszenie GK-FOTO.6201.5.2025 (skorowidz SkorowidzeWgAktualnosci, GetFeatureInfo 2026-11-15)')
ORTHO_LIC = 'dane PZGiK (GUGiK) — udostępniane bez opłat; dane urzędowe'
NMPT_SRC = ('GUGiK NMPT, lot 2023-09-15 (ulistniony), 0,5 m, PL-EVRF2007-NH: opendata.geoportal.gov.pl/NumDaneWys/NMPT/78825/ '
            'arkusze N-34-107-C-b-3-2, -3-4, -4-3 (sha256 w sources.md)')
NMT_SRC = 'GUGiK NMT, WCS PZGIK/NMT/GRID1/WCS/DigitalTerrainModelFormatTIFF (DTM_PL-KRON86-NH_TIFF, 1 m)'
OSM_SRC = 'https://api.openstreetmap.org/api/0.6/map?bbox=23.150,53.095,23.192,53.1075 (pobrano 2026-11-15 09:41 UTC)'
OSM_LIC = 'ODbL 1.0 © autorzy OpenStreetMap'

COLS = ['id', 'kategoria', 'element', 'parametr', 'wartość', 'jednostka', 'lat', 'lon', 'osm_id', 'kierunek_deg', 'wysokość_oka_m',
        'data_zdjęcia', 'sezon', 'pora_dnia', 'opis_co_widać', 'url_źródła', 'licencja', 'autor', 'data_dostępu', 'status', 'uwagi',
        'plik', 'url_pliku', 'sha256']
rows = []


def add(**k):
    r = {c: '' for c in COLS}
    r.update({kk: ('' if v is None else str(v)) for kk, v in k.items()})
    r['id'] = f'K64-{len(rows) + 1:03d}'
    if not r['data_dostępu']:
        r['data_dostępu'] = ACC
    rows.append(r)
    return r['id']


def sha(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()


def put_ortho(name):
    src = f'{S}/m64/ortho/{name}'
    dst = f'{FILES}/ortho_{name}'
    im = Image.open(src).convert('RGB')
    im.thumbnail((1600, 1600))
    im.save(dst, quality=82)
    return 'files/ortho_' + name, sha(dst)


ORTHO_URLS = {}
for line in open(S + '/m64/ortho/urls.txt'):
    pass


def ortho_url(name):
    # urls.txt lines alternate URL / extent; map by order of creation is fragile -> recompute from file listing log
    return ORTHO_URL.get(name, '')


ORTHO_URL = json.load(open(S + '/m64/ortho/url_map.json'))


def commons(title):
    p = info[title]
    ii = p['imageinfo'][0]
    em = ii.get('extmetadata', {})
    lic = em.get('LicenseShortName', {}).get('value', '')
    import re
    art = re.sub('<[^>]+>', '', em.get('Artist', {}).get('value', '')).strip()
    page = 'https://commons.wikimedia.org/wiki/' + urllib.parse.quote(title.replace(' ', '_'), safe=':')
    return page, ii['url'].split('?')[0], lic, art, ii.get('sha1', '')


def put_frame(title):
    import re
    slug = re.sub(r'[^A-Za-z0-9_-]+', '_', title[5:].rsplit('.', 1)[0]).strip('_')
    src = f'{S}/m64/dl/{slug}.jpg'
    dst = f'{FILES}/{slug}.jpg'
    im = Image.open(src).convert('RGB')
    im.thumbnail((1600, 1600))
    im.save(dst, quality=82)
    return 'files/' + slug + '.jpg', sha(dst)


# ---------------------------------------------------------------- nawierzchnia
add(kategoria='nawierzchnia', element='pas 09R/27L', parametr='nawierzchnia i wymiary wg AIP', wartość='odsyłacz: C58-029 (M58) — 1350 × 30 m, CONC/ASPH',
    jednostka='m', lat='53.100906', lon='23.173246', osm_id='way 958211700',
    url_źródła='research/cloud/p15-dojlidy-details/manifest.csv (C58-029) → karta VFR AD 4 EPBK 2-1, eAIP VFR AIRAC AMDT VFR 11/26',
    licencja='dokument urzędowy PAŻP (fakt, nie kopia karty)', autor='PAŻP', status='SOURCED',
    uwagi='Nie powtarzam ustalenia M58; recenzja M58 sprawdziła kartę AIP (render 200 dpi). OSM: aeroway=runway, surface=asphalt, width=30, length=1350 (sprawdzone 2026-11-15).')
f, h = put_ortho('rwy_mid_005.jpg')
add(kategoria='nawierzchnia', element='pas 09R/27L', parametr='wygląd nawierzchni (ortofoto 0,05 m, środek pasa)',
    wartość='jasnoszara, jednolita; słabe podłużne pasma różnych odcieni szarości (ślady rozkładania warstwy wzdłuż osi); bez widocznych spękań, łat, mchu ani trawy w szczelinach w GSD 0,05 m',
    lat='53.100906', lon='23.173246', osm_id='way 958211700', opis_co_widać='wycinek 48 × 27 m: górna linia krawędziowa, kreska osi, groty progu przesuniętego przy lewej krawędzi kadru, reszta jednolity jasnoszary asfalt z podłużnymi pasmami',
    url_źródła=ORTHO_SRC, licencja=ORTHO_LIC, autor='GUGiK', status='SOURCED',
    uwagi='opis z obrazu (arkusz N-34-107-C-b-3-4, 2025-04-18, 0,05 m). Szczeliny < 5 cm i drobne spękania są poniżej rozdzielczości — „brak spękań” znaczy tylko „niewidoczne w GSD 0,05 m”. Kolor opisem, bez RGB. Wniosek dla gry: asfalt pasa wyraźnie jaśniejszy i czystszy niż jezdnie miejskie; nie stosować łat asphalt_worn (por. ADR 0196 „za zniszczony”).',
    plik=f, url_pliku=ORTHO_URL['rwy_mid_005.jpg'], sha256=h)
f, h = put_ortho('rwy_W_01.jpg')
add(kategoria='nawierzchnia', element='pas 09R/27L — koniec W i wylot drogi kołowania', parametr='wygląd nawierzchni (ortofoto 0,1 m)',
    wartość='jasnoszara jak w środku pasa; przy oznaczniku „09” kilka małych ciemniejszych plam; łuk żółtej linii z drogi kołowania na oś pasa; za końcem nawierzchni pas odkrytej, przesuszonej ziemi i trawa brązowozielona (kwiecień)',
    lat='53.1011', lon='23.1640', osm_id='way 958211700; way 958211699', opis_co_widać='koniec W pasa 120 × 68 m: oznacznik 09 + R, linie krawędziowe, strzałka w osi, wylot drogi kołowania na NW, trawa wokół',
    url_źródła=ORTHO_SRC, licencja=ORTHO_LIC, autor='GUGiK', status='SOURCED', plik=f, url_pliku=ORTHO_URL['rwy_W_01.jpg'], sha256=h,
    uwagi='oznakowanie (09R, strzałki, linie) opisane w M58 §2.2 — tu tylko nawierzchnia.')
f, h = put_ortho('rwy_E_01.jpg')
add(kategoria='nawierzchnia', element='pas 09R/27L — koniec E (pętla do zawracania)', parametr='wygląd nawierzchni (ortofoto 0,1 m)',
    wartość='jasnoszara, jednolita; trójkątne poszerzenie po stronie N z żółtą pętlą do zawracania; za krawędzią E rząd małych jasnych elementów w trawie',
    lat='53.10075', lon='23.1825', osm_id='way 958211700', opis_co_widać='koniec E 120 × 68 m: oznacznik 27 L, żółta pętla, poszerzenie N, linie krawędziowe; trawa brązowozielona',
    url_źródła=ORTHO_SRC, licencja=ORTHO_LIC, autor='GUGiK', status='SOURCED', plik=f, url_pliku=ORTHO_URL['rwy_E_01.jpg'], sha256=h,
    uwagi='elementy za krawędzią E opisał M58 („6 jasnych elementów co ~6 m”) — odsyłacz, typ nadal UNVERIFIED.')
add(kategoria='nawierzchnia', element='pas 09R/27L', parametr='spadek poprzeczny (korona)', wartość='1,2–1,6 (obie strony od osi)', jednostka='%',
    lat='53.100906', lon='23.173246', osm_id='way 958211700', url_źródła=NMPT_SRC, licencja=ORTHO_LIC, autor='GUGiK', status='ESTIMATED',
    uwagi='metoda: NMPT 2023 (0,5 m) w 7 przekrojach co 200 m (s = 100…1300 m od węzła 8866086772), mediana 5 komórek wzdłuż osi w punktach −14/−7/0/+7/+14 m; (z_oś − z_±14)/14. Wyniki N 1,29–1,57 %, S 1,21–1,50 %. Niepewność ±0,7 % (błąd NMPT 0,10 m na 14 m). Pas ma koronę — ważne dla widoczności (§3: dalsza połowa pasa chowa się za osią).')
add(kategoria='nawierzchnia', element='pas 09R/27L', parametr='spadek podłużny', wartość='0,34 (rośnie ku E: 150,99 m przy s=100 → 155,09 m przy s=1300)', jednostka='%',
    lat='53.100906', lon='23.173246', osm_id='way 958211700', url_źródła=NMPT_SRC, licencja=ORTHO_LIC, autor='GUGiK', status='ESTIMATED',
    uwagi='metoda: NMPT 2023 w osi pasa, (155,09 − 150,99)/1200 m. OSM ele=155 (bez daty pomiaru). Rzędne PL-EVRF2007-NH.')
add(kategoria='nawierzchnia', element='pas 09R/27L — otoczenie', parametr='wały w NMT 2018 vs NMPT 2023', wartość='w NMT pojedyncze nasypy ~2 m (np. E 779250: 152,98 m przy N 589940 wobec 150,9 obok); w NMPT 2023 brak — teren łagodnie opada od osi pasa',
    lat='53.1012', lon='23.1734', url_źródła=NMT_SRC + '; ' + NMPT_SRC, licencja=ORTHO_LIC, autor='GUGiK', status='SOURCED',
    uwagi='potwierdza obserwację M58 (C58-056) innym źródłem (NMPT 2023 zamiast ortofoto). Dla gry: teren z NMT 2018 przy pasie wymaga spłaszczenia, inaczej fałszywa przesłona kamery krywlany_runway. Profile: E 778900 / 779250 / 779600, N 589760–589990 co 10 m.')
add(kategoria='nawierzchnia', element='pas 09L/27R (trawiasty)', parametr='szerokość: AIP vs OSM', wartość='AIP 840 × 160 m GRASS (SUP 02/26: zwężenie do 80 m) — odsyłacz M58 §2.1; OSM way 303368859: width=245, length=860, surface=grass',
    jednostka='m', lat='53.102241', lon='23.171011', osm_id='way 303368859', url_źródła=OSM_SRC + '; M58 §2.1', licencja=OSM_LIC, autor='społeczność OSM / PAŻP', status='SOURCED',
    uwagi='rozbieżność OSM 245 m vs AIP 160/80 m: do gry brać AIP. Na ortofoto 2025 pas trawiasty nie ma wyraźnych granic — trawa pola wzlotów jednolita (granica UNVERIFIED).')
f, h = put_ortho('twy_W_005.jpg')
add(kategoria='nawierzchnia', element='droga kołowania W (od końca W pasa do płyty)', parametr='szerokość nawierzchni', wartość='15,4', jednostka='m',
    lat='53.102200', lon='23.162950', osm_id='way 958211699 (aeroway=taxiway, L=191 m, bez tagu surface)',
    opis_co_widać='odcinek drogi kołowania biegnący ukośnie: jasnoszary asfalt jak pas, żółta linia osiowa, bez linii krawędziowych; w trawie po obu stronach okrągłe żółte elementy',
    url_źródła=ORTHO_SRC, licencja=ORTHO_LIC, autor='GUGiK', status='ESTIMATED', plik=f, url_pliku=ORTHO_URL['twy_W_005.jpg'], sha256=h,
    uwagi='metoda: ortofoto 0,05 m; odstęp krawędzi w poziomie 370 px × cos(33,7°) = 308 px = 15,4 m (±0,3 m). Początek: węzeł 8866086768 (53.102670, 23.162421, przy płycie); koniec: węzeł 8866086772 (53.101098, 23.163318, koniec W pasa).')
add(kategoria='nawierzchnia', element='drogi kołowania — wszystkie', parametr='liczba obiektów aeroway=taxiway w bbox', wartość='12 (958211699 — główna W; 795232294, 1320699105, 1320699106 — przy lądowiskach śmigłowców; 1320699940–1320699947 — krótkie odcinki przy płycie betonowej)',
    jednostka='szt.', osm_id='jw.', url_źródła=OSM_SRC, licencja=OSM_LIC, autor='społeczność OSM', status='SOURCED',
    uwagi='tylko 958211699 łączy pas z płytą; pozostałe to dojazdy do stanowisk śmigłowców na zachodnim krańcu (FATO way 1234358815, TLOF 1/2 way 1320699103/104). Nawierzchnia małych dróg: z ortofoto jak płyta (beton) — UNVERIFIED dla każdej osobno.')
f, h = put_ortho('twy_W_005.jpg')
add(kategoria='nawierzchnia', element='droga kołowania W', parametr='elementy przy krawędziach', wartość='okrągłe żółte elementy w trawie ok. 2,5 m od krawędzi, co ok. 15,6 m', jednostka='m',
    lat='53.102200', lon='23.162950', osm_id='way 958211699', url_źródła=ORTHO_SRC, licencja=ORTHO_LIC, autor='GUGiK', status='ESTIMATED',
    uwagi='odstęp z ortofoto 0,05 m (313 px). Czy to oprawy świetlne, czy znaczniki — UNVERIFIED (brak kadru z bliska, AIP AD 4 nie opisuje świateł wg M58).', plik=f, url_pliku=ORTHO_URL['twy_W_005.jpg'], sha256=h)
f, h = put_ortho('apron_015.jpg')
add(kategoria='nawierzchnia', element='płyta postojowa betonowa', parametr='wymiary i nawierzchnia',
    wartość='OSM surface=concrete; obrys: boki 174,2 / 160,5 m (dłuższe) i 49,2 / 70,0 m; na ortofoto jasnoszare płyty betonowe z siatką spoin, żółte linie prowadzenia (łuki stanowisk), ciemne plamy oleju na stanowisku, śmigłowiec na stanowisku E',
    jednostka='m', lat='53.103189', lon='23.162948', osm_id='way 616186583 (aeroway=apron)', opis_co_widać='płyta 200 × 112 m: siatka płyt, żółte łuki, oznaczenie stanowiska „1” w żółtym sześcioboku, samolot jednosilnikowy przy krawędzi W, krąg wiatrowskazu, lądowisko z żółtymi krzyżami (SW)',
    url_źródła=OSM_SRC + '; ' + ORTHO_SRC, licencja=OSM_LIC + '; ' + ORTHO_LIC, autor='OSM / GUGiK', status='SOURCED', plik=f, url_pliku=ORTHO_URL['apron_015.jpg'], sha256=h,
    uwagi='płyta jest przy zachodnim krańcu lotniska (część LPR/aeroklubu), ponad 450 m od ul. Dywizjonu 303 na wschód od ronda — z dróg publicznych niewidoczna (brak kadru).')
f, h = put_ortho('apron_005.jpg')
add(kategoria='nawierzchnia', element='płyta postojowa betonowa', parametr='moduł płyt betonowych', wartość='ok. 5 × 5', jednostka='m',
    lat='53.103050', lon='23.163000', osm_id='way 616186583', opis_co_widać='wycinek 40 × 22,5 m: siatka spoin ukośnie do kadru, żółta linia z ciemną obwódką z grotami, skupisko ciemnych plam (olej) ok. 8 × 9 m na stanowisku',
    url_źródła=ORTHO_SRC, licencja=ORTHO_LIC, autor='GUGiK', status='ESTIMATED', plik=f, url_pliku=ORTHO_URL['apron_005.jpg'], sha256=h,
    uwagi='metoda: odstęp równoległych spoin 100–110 px × 0,05 m = 5,0–5,5 m (±0,5 m).')
f, h = put_ortho('hangars_015.jpg')
add(kategoria='nawierzchnia', element='płyta postojowa trawiasta (aeroklub)', parametr='nawierzchnia i stan',
    wartość='OSM surface=grass, obrys 84 × 142 m; na ortofoto (kwiecień) trawa mocno wydeptana, duże płaty gołej piaszczystej ziemi przed hangarem; samoloty i szybowce na trawie',
    jednostka='m', lat='53.104152', lon='23.164840', osm_id='way 234838629 (aeroway=apron, surface=grass)', opis_co_widać='hangar z ciemnoszarym dachem dwuspadowym, szybowce w rzędzie na E od hangaru, samolot żółty dwupłat i biały jednopłat na S, zabudowa gospodarcza i namioty na W, jezdnia Dywizjonu 303 w rogu NW',
    url_źródła=OSM_SRC + '; ' + ORTHO_SRC, licencja=OSM_LIC + '; ' + ORTHO_LIC, autor='OSM / GUGiK', status='SOURCED', plik=f, url_pliku=ORTHO_URL['hangars_015.jpg'], sha256=h,
    uwagi='w sierpniu 2023 (kadr K64 P11-080) trawa przed hangarem zielona i skoszona; kolor sezonowy patrz wiersz trawy.')
add(kategoria='nawierzchnia', element='trawa pola wzlotów', parametr='kolor i wysokość sezonowa z kadrów',
    wartość='sierpień 2023 (P11-080, P11-079, P11-099): soczyście zielona, skoszona nisko za płotem; po stronie drogi (poza płotem) wyższa, z kwiatami; lipiec 2020 (P11-076): zielona, skoszona; kwiecień 2025 (ortofoto): brązowozielona z pasami koszenia',
    lat='53.105805', lon='23.166742', status='SOURCED', url_źródła='kadry K64 (wiersze kadr) + ortofoto 2025-04-18',
    uwagi='wysokość trawy: niska (skoszona) — liczbowo UNVERIFIED (brak skali przy ziemi); trawa poza płotem ok. 0,3–0,6 m z porównania do panelu płotu ~1,7 m (M58) — ESTIMATED, zgrubnie.')
add(kategoria='nawierzchnia', element='stara płyta z płyt betonowych (2011–2012)', parametr='stan w 2011–2012',
    wartość='popękane płyty betonowe z trawą i mchem w spoinach, pas z płyt prowadzący do hangaru aeroklubu',
    lat='53.104579', lon='23.164566', status='SOURCED', url_źródła='kadry „Krywlany Białystok Nowy hangar”, „… flota”, „… Nowy hangar z oddali” (CC BY-SA 3.0)',
    uwagi='stan sprzed przebudowy (pas asfaltowy z 2018 r. wg ADR 0196). Dziś: na ortofoto 2025 przed hangarem 229040230 nadal płyty — gra może je użyć jako „starą płytę”, ale stan spoin w 2025 UNVERIFIED.')

AIPU = 'https://docs.pansa.pl/ais/eaipvfr/AIRAC%20AMDT%20VFR%2011-26_2026_10_29/documents/Root_WePub/AIP%20VFR/AD/EPBK/2/AD_4_EPBK_2-1.pdf'
AIPS = 'karta VFR AD 4 EPBK 2-1 (AERODROME CHART), data karty 11 JUN 2026, stopka AIRAC AMDT VFR 06/26; obowiązujące wydanie eAIP VFR AIRAC AMDT VFR 11/26; PDF sha256 6a0bff7c6bf743f34d19234277799deaeffdbfc31b44eef47a9846d004e4046a'
add(kategoria='nawierzchnia', element='pas 09R/27L — pas startowy (strip)', parametr='wymiary STRIP wg AIP', wartość='1470 × 150 (napis na karcie: „STRIP 1470 x 150”)', jednostka='m',
    lat='53.100906', lon='23.173246', osm_id='way 958211700', url_źródła=AIPU, licencja='dokument urzędowy PAŻP (fakt z karty, karta nie kopiowana)', autor='PAŻP', status='SOURCED',
    uwagi=AIPS + '. Szerokość utwardzona 30 m vs pas startowy (strip) 150 m: w terenie strip = skoszona trawa wokół asfaltu, bez widocznej granicy na ortofoto 2025. M58 tej liczby nie podaje.')
add(kategoria='nawierzchnia', element='pas 09L/27R (trawiasty) — strip', parametr='wymiary STRIP wg AIP', wartość='900 × 225 (napis: „STRIP 900 x 225”); RWY 840 × 160 GRASS', jednostka='m',
    lat='53.102241', lon='23.171011', osm_id='way 303368859', url_źródła=AIPU, licencja='dokument urzędowy PAŻP (fakt z karty)', autor='PAŻP', status='SOURCED', uwagi=AIPS)
add(kategoria='nawierzchnia', element='drogi kołowania — oznaczenia AIP', parametr='oznaczenia na karcie', wartość='A i B (między płytą a pasem 09R/27L, przy końcu W), C (od płyty aeroklubu ku polu wzlotów)',
    url_źródła=AIPU, licencja='dokument urzędowy PAŻP (fakt z karty)', autor='PAŻP', status='SOURCED',
    uwagi=AIPS + '. Przypisanie liter do way OSM: A ≈ 958211699 (ESTIMATED z położenia na karcie); B, C — UNVERIFIED.')
add(kategoria='obiekt', element='wiatrowskazy wg AIP', parametr='liczba symboli na karcie', wartość='2 (na N od pasa trawiastego i na S od pasa 09R/27L, ok. naprzeciw oznacznika 27)', jednostka='szt.',
    url_źródła=AIPU, licencja='dokument urzędowy PAŻP (fakt z karty)', autor='PAŻP', status='SOURCED',
    uwagi=AIPS + '. Zgodne z węzłami OSM 5920347042 (N) i 7437888765 (S); trzeci wiatrowskaz OSM (11436697402, przy płycie LPR) nie jest na karcie.')

# ---------------------------------------------------------------- obiekty
add(kategoria='obiekt', element='hangar aeroklubu (budynek z wrotami, „nowy hangar”)', parametr='wymiary w rzucie (OSM)', wartość='25,6 × 37,7', jednostka='m',
    lat='53.103819', lon='23.162504', osm_id='way 229040230 (building=hangar, aeroway=hangar; addr. Ciołkowskiego 2)', url_źródła=OSM_SRC, licencja=OSM_LIC, autor='społeczność OSM', status='SOURCED')
add(kategoria='obiekt', element='hangar aeroklubu', parametr='wysokość (NMPT − NMT)', wartość='p95 8,8; max 10,6; p50 7,7', jednostka='m',
    lat='53.103819', lon='23.162504', osm_id='way 229040230', url_źródła=NMPT_SRC + '; ' + NMT_SRC, licencja=ORTHO_LIC, autor='GUGiK', status='ESTIMATED',
    uwagi='metoda: NMPT 2023 w obrysie OSM zwężonym o 1 m minus mediana NMT w pierścieniu 3–8 m poza obrysem (teren 150,67 m). max obejmuje maszty/wiatrowskaz na dachu.')
f, h = put_frame('File:Krywlany Białystok Nowy hangar.jpg')
pg, fu, lic, art, s1 = commons('File:Krywlany Białystok Nowy hangar.jpg')
add(kategoria='obiekt', element='hangar aeroklubu', parametr='wygląd (kadr 2012)',
    wartość='płaski dach; dwa piętrowe skrzydła z tynkiem w kolorze zgaszonego różu/fioletu, z odpryskami; środkiem wrota hangarowe z niebieskich paneli, nad nimi pas przeszklenia w szarych szprosach; na dachu prawego skrzydła wiatrowskaz biało-czerwony i maszty antenowe',
    lat='53.104579', lon='23.164566', osm_id='way 229040230', kierunek_deg='238 (ESTIMATED z geometrii: kamera → środek obrysu; ±15°)', data_zdjęcia='2012-08-04', sezon='lato', pora_dnia='dzień',
    opis_co_widać='front hangaru przez starą płytę z płyt betonowych z trawą w spoinach; dwa auta po prawej, drzewa w tle', url_źródła=pg, licencja=lic + ' (referencja, nie tekstura; atrybucja)', autor=art,
    status='SOURCED', plik=f, url_pliku=fu, sha256=h, uwagi=f'sha1 oryginału Commons {s1}. Stan z 2012 r.; z drogi publicznej budynek zasłonięty (brak kadru z Dywizjonu 303) — UNVERIFIED czy widoczny.')
add(kategoria='obiekt', element='stary hangar (drewniany, dach dwuspadowy)', parametr='wymiary w rzucie (OSM)', wartość='21,6 × 40,6', jednostka='m',
    lat='53.104607', lon='23.164571', osm_id='way 304300294 (building=hangar)', url_źródła=OSM_SRC, licencja=OSM_LIC, autor='społeczność OSM', status='SOURCED')
add(kategoria='obiekt', element='stary hangar', parametr='wysokość (NMPT − NMT)', wartość='kalenica max 8,5; p95 8,3; p50 6,2; p10 4,1', jednostka='m',
    lat='53.104607', lon='23.164571', osm_id='way 304300294', url_źródła=NMPT_SRC + '; ' + NMT_SRC, licencja=ORTHO_LIC, autor='GUGiK', status='ESTIMATED',
    uwagi='metoda jak wyżej (teren 151,26 m). Rozrzut p10–max odpowiada dachowi dwuspadowemu: okap ~4 m, kalenica ~8,5 m.')
f, h = put_frame('File:Krywlany Białystok Stary hangar.jpg')
pg, fu, lic, art, s1 = commons('File:Krywlany Białystok Stary hangar.jpg')
add(kategoria='obiekt', element='stary hangar', parametr='wygląd (kadr 2012)',
    wartość='dach dwuspadowy kryty ciemnoszarą papą; szczyt z poszarzałych desek z pasem okien; otwarte wrota środkowe, boczne skrzydła wrót i drzwi z desek pomalowanych na niebiesko (wyblakłe, łuszczące się); dobudówki z jednospadowymi daszkami po bokach',
    lat='53.104940', lon='23.165121', osm_id='way 304300294', kierunek_deg='UNVERIFIED', data_zdjęcia='2012-08-04', sezon='lato', pora_dnia='dzień',
    opis_co_widać='hangar od strony pola wzlotów: szybowce w środku, człowiek przy wrotach, trawa z kwiatami na pierwszym planie, drzewa liściaste z lewej',
    url_źródła=pg, licencja=lic + ' (referencja, nie tekstura; atrybucja)', autor=art, status='SOURCED', plik=f, url_pliku=fu, sha256=h,
    uwagi=f'sha1 oryginału {s1}. Na ortofoto 2025 dach nadal ciemnoszary — kształt bez zmian; kolor wrót w 2025 UNVERIFIED (z drogi widać szczyt szary i czerwonobrązową szopę przed nim: kadry P11-076, P11-080).')
add(kategoria='obiekt', element='budynek LPR (hangar śmigłowców)', parametr='wymiary / wysokość', wartość='rzut wg OSM boki 21,1 / 24,1 m; NMPT − NMT: p95 9,7, max 12,6, p50 8,3', jednostka='m',
    lat='53.103142', lon='23.160890', osm_id='way 1234358789 (emergency=air_rescue_service)', url_źródła=OSM_SRC + '; ' + NMPT_SRC, licencja=OSM_LIC + '; ' + ORTHO_LIC, autor='OSM / GUGiK', status='ESTIMATED',
    uwagi='max 12,6 m = maszt na dachu (kadr 2012). Najbliższa droga publiczna (Dywizjonu 303 przy rondzie) ok. 450 m — widoczność z drogi UNVERIFIED (brak kadru).')
f, h = put_frame('File:Krywlany Białystok Lotnicze Pogotowie ratunkowe.jpg')
pg, fu, lic, art, s1 = commons('File:Krywlany Białystok Lotnicze Pogotowie ratunkowe.jpg')
add(kategoria='obiekt', element='budynek LPR', parametr='wygląd (kadr 2012)',
    wartość='biało-jasnoszary budynek: część hangarowa z dachem łukowym, w szczycie łukowe okno w szprosach, duża brama z poziomymi panelami w kolorze morskim; obok część dwukondygnacyjna z płaskim dachem; maszt i wiatrowskaz biało-czerwony',
    lat='53.103158', lon='23.160957', osm_id='way 1234358789', kierunek_deg='UNVERIFIED', data_zdjęcia='2012-08-04', sezon='lato', pora_dnia='dzień',
    opis_co_widać='dwa żółte śmigłowce ratunkowe na płycie przed budynkiem, ogrodzenie z paneli, pole trawy na pierwszym planie, ściana lasu liściastego w tle',
    url_źródła=pg, licencja=lic + ' (referencja, nie tekstura; atrybucja)', autor=art, status='SOURCED', plik=f, url_pliku=fu, sha256=h,
    uwagi=f'sha1 oryginału {s1}. Napisy/barwy operatora śmigłowców — nie odtwarzamy (malowanie generyczne).')
f, h = put_ortho('white_obj_005.jpg')
add(kategoria='obiekt', element='biała hala namiotowa (bez obiektu w OSM)', parametr='wymiary w rzucie', wartość='ok. 30 × 20,5', jednostka='m',
    lat='53.104250', lon='23.168936', osm_id='brak w OSM (2026-11-15)', opis_co_widać='biały dach dwuspadowy (jaśniejsza i ciemniejsza połać), cztery kratowe maszty w narożach, długi cień na NW; wokół ubita ziemia',
    url_źródła=ORTHO_SRC, licencja=ORTHO_LIC, autor='GUGiK', status='ESTIMATED', plik=f, url_pliku=ORTHO_URL['white_obj_005.jpg'], sha256=h,
    uwagi='metoda: boki z ortofoto 0,05 m (601 px i 410 px). Obiekt ok. 150 m na SE od jezdni Dywizjonu 303, przy płocie N.')
add(kategoria='obiekt', element='biała hala namiotowa', parametr='wysokość okapu (z cienia)', wartość='ok. 5,4', jednostka='m',
    lat='53.104250', lon='23.168936', url_źródła=ORTHO_SRC, licencja=ORTHO_LIC, autor='GUGiK', status='ESTIMATED',
    uwagi='metoda: cień narożnika dachu 221 px × 0,025 m (wycinek 2×) = 5,5 m, azymut cienia 332°; wysokość Słońca 44,4° (azymut Słońca 149° ⇒ 09:00 UTC 2025-04-18, wzór NOAA uproszczony, m64 tools sun.py) → H = 5,5 × tan 44,4° = 5,4 m. M58 przyjął 43,7° dla tego samego lotu — różnica < 0,1 m. Maszty narożne wyższe od dachu — ich wysokość UNVERIFIED (cień poza wycinkiem).')
add(kategoria='obiekt', element='biała hala namiotowa', parametr='kiedy istnieje', wartość='na ortofoto 2025-04-18 JEST; w NMPT 2023-09-15 BRAK (0,3 m nad terenem); w NMPT z WCS (DSM_PL-KRON86-NH) też BRAK',
    lat='53.104250', lon='23.168936', url_źródła=NMPT_SRC + '; WCS PZGIK/NMPT/GRID1/WCS/DigitalSurfaceModel (x 778930–778975, y 590205–590245, max 152,2 m)', licencja=ORTHO_LIC, autor='GUGiK', status='UNVERIFIED',
    uwagi='obiekt prawdopodobnie tymczasowy (hala namiotowa) — czy stoi dziś, UNVERIFIED. Uwaga: brak namiotu w WCS podważa wniosek M68, że WCS = lot 2025-04-18 (albo namiot postawiono między lotem NMPT a lotem ortofoto). Do gry: NIE stawiać bez nowego dowodu.')
for wid, lat, lon, name, fn in [('5920347042', '53.104039', '23.171309', 'wiatrowskaz przy płocie N (78 m od granicy lotniska)', 'windsock1_005.jpg'),
                                ('7437888765', '53.099476', '23.172763', 'wiatrowskaz na S od pasa', 'windsock2_005.jpg'),
                                ('11436697402', '53.103058', '23.161619', 'wiatrowskaz przy płycie betonowej (W)', 'windsock3_005.jpg')]:
    f, h = put_ortho(fn)
    add(kategoria='obiekt', element=name, parametr='położenie i oznaczenie wokół', wartość='biały pierścień na trawie: średnica zewnętrzna ok. 17,4 m, szerokość ok. 1,3 m; maszt w środku', jednostka='m',
        lat=lat, lon=lon, osm_id=f'node {wid} (aeroway=windsock)', opis_co_widać='biały pierścień, w środku cień masztu z rękawem; sam rękaw widoczny z góry jako jasny stożek przy podstawie',
        url_źródła=ORTHO_SRC, licencja=ORTHO_LIC, autor='GUGiK', status='ESTIMATED', plik=f, url_pliku=ORTHO_URL[fn], sha256=h,
        uwagi='metoda: średnica 348 px × 0,05 m (pomiar na 3 wiatrowskazach: 17,4 / 17,4 / 17,5 m). Pierścień przy płycie W ułożony z jasnych bloczków.')
add(kategoria='obiekt', element='wiatrowskazy na polu wzlotów', parametr='wysokość masztu do rękawa (z cienia)', wartość='4,5 (node 5920347042); 3,8 (node 7437888765)', jednostka='m',
    lat='53.104039', lon='23.171309', osm_id='node 5920347042; node 7437888765', url_źródła=ORTHO_SRC, licencja=ORTHO_LIC, autor='GUGiK', status='ESTIMATED',
    uwagi='metoda: długość cienia od podstawy do początku cienia rękawa (4,55 m i 3,92 m, wycinki 4×) × tan 44,4°; azymut cienia 328–329° zgodny z cieniem hali namiotowej. ±0,5 m (ostrość cienia, nachylenie terenu).')
add(kategoria='obiekt', element='wiatrowskazy', parametr='kolor rękawa (z kadrów)', wartość='2012: biało-czerwone pasy (na dachu hangaru aeroklubu i przy LPR); 2023: pomarańczowy rękaw przy starym hangarze (P11-080, wycinek)',
    status='SOURCED', url_źródła='kadry K64: Nowy hangar, Lotnicze Pogotowie (2012), P11-080 (2023)',
    uwagi='kolor rękawów na polu wzlotów (pierścienie) z bliska UNVERIFIED — na ortofoto jasne (wyblakłe lub biało-czerwone przy słabej rozdzielczości).')
f, h = put_ortho('rwy_Nedge_01.jpg')
add(kategoria='obiekt', element='oświetlenie krawędzi i progu pasa', parametr='jest/brak', wartość='UNVERIFIED: przy krawędzi N pojedyncze małe żółte elementy (2 na 240 m odcinku); przy drodze kołowania regularne żółte elementy co ~15,6 m; za końcem E rząd jasnych elementów (M58)',
    lat='53.10125', lon='23.1665', osm_id='brak aeroway=*light w OSM', url_źródła=ORTHO_SRC, licencja=ORTHO_LIC, autor='GUGiK', status='UNVERIFIED',
    plik=f, url_pliku=ORTHO_URL['rwy_Nedge_01.jpg'], sha256=h,
    uwagi='w żadnym kadrze nie widać opraw z bliska; AIP AD 4 EPBK nie opisuje świateł (M58 §2.1). Do gry: bez świateł krawędziowych do czasu dowodu.')
add(kategoria='obiekt', element='parking przy aeroklubie (ul. Krywlany)', parametr='liczba i powierzchnia', wartość='19 pól amenity=parking (street_side, prostopadłe, kostka), łącznie 2091 m²',
    jednostka='m²', lat='53.1045', lon='23.1630', osm_id='way 1385339664…1385339687 (19 obiektów)', url_źródła=OSM_SRC, licencja=OSM_LIC, autor='społeczność OSM', status='SOURCED',
    uwagi='powierzchnie liczone z obrysów (rzut równokątny lokalny, ±2 %).')
f, h = put_ortho('gate_main_005.jpg')
add(kategoria='obiekt', element='brama wjazdowa części aeroklubu (od ul. Dywizjonu 303 / Krywlany)', parametr='typ i szerokość',
    wartość='stalowa brama ramowa w linii płotu, na wjeździe z popękanych płyt betonowych; długość ramy w rzucie ok. 5,5 m', jednostka='m',
    lat='53.105040', lon='23.164720', osm_id='node 4759528833 (barrier=gate)', opis_co_widać='asfaltowa droga rowerowa wzdłuż jezdni, na przecięciu z wjazdem pas czerwonej kostki; ukośna rama bramy, za nią plac z płyt betonowych, dach budynku 304300297 (jasnoszary) w prawym dolnym rogu',
    url_źródła=ORTHO_SRC, licencja=ORTHO_LIC, autor='GUGiK', status='ESTIMATED', plik=f, url_pliku=ORTHO_URL['gate_main_005.jpg'], sha256=h,
    uwagi='długość: 110 px × 0,05 m w rzucie (po audycie; wcześniej 124 px ≈ 6 m). Wysokość, kolor, liczba skrzydeł: UNVERIFIED (brak kadru). Brama E od Mickiewicza — odsyłacz M58 §3 (C58-069).')
add(kategoria='obiekt', element='inne budynki aeroklubu przy wjeździe', parametr='wysokość (NMPT − NMT)', wartość='304300297 modelarnia 9 × 27,5 m: p50 3,6; 1232848101 namiot spadochronowy 11,4 × 16,1 m: p50 3,9; 304300295: 4,5; 304300296: p50 4,0 / p95 6,1',
    jednostka='m', lat='53.104966', lon='23.165139', osm_id='way 304300297, 1232848101, 304300295, 304300296', url_źródła=NMPT_SRC + '; ' + OSM_SRC, licencja=ORTHO_LIC + '; ' + OSM_LIC, autor='GUGiK / OSM', status='ESTIMATED',
    uwagi='metoda jak dla hangarów. Wygląd z drogi: z P11-076 i P11-080 widać przed starym hangarem niską szopę z czerwonobrązową ścianą i jasnym dachem jednospadowym (to najpewniej 304300297 lub sąsiedni) — przypisanie UNVERIFIED.')
add(kategoria='obiekt', element='tablice i ogrodzenie', parametr='odsyłacz', wartość='płot N/W/S, czerwone tabliczki „LOTNISKO”, banery (napis firmowy, nie odtwarzamy), brama E — ustalenia M58 §3 i recenzji M58 §5.3; nie powtarzam',
    status='SOURCED', url_źródła='research/cloud/p15-dojlidy-details/README.md §3; docs/reports/REVIEW-2026-11-14-s20-cloud-m58.md §5.3')
add(kategoria='obiekt', element='wysoki cienki maszt na W od starego hangaru', parametr='położenie / wysokość', wartość='UNVERIFIED',
    lat='53.105805', lon='23.166742', status='UNVERIFIED', url_źródła='kadr P11-080 (prawa część kadru, nad drzewami)',
    uwagi='na P11-080 widać cienki maszt wyższy od drzew; w OSM brak man_made=mast w bbox; w NMPT pojedynczy pręt nie jest wiarygodny. Nie stawiać w grze bez dowodu.')

# ---------------------------------------------------------------- geometria widoku
for pid in ['R1', 'R2', 'R3', 'R4', 'R5', 'F1', 'F2', 'F3']:
    r = VR[pid]
    for hk, hv in (('h2.5', 2.5), ('h1.7', 1.7)):
        x = r[hk]
        clr = x['clearance_near_m']
        if clr < -0.10:
            verdict = 'ZASŁONIĘTY'
        elif clr < 0.10 or x['cross_section_visible_of_31'] < 31:
            verdict = 'NA GRANICY' if clr >= -0.10 else 'ZASŁONIĘTY'
        else:
            verdict = 'WIDOCZNY'
        if pid == 'R1' and hv == 2.5:
            verdict = 'ZASŁONIĘTY (bliższa krawędź za grzbietem terenu; część dalszej połowy na granicy błędu)'
        if pid == 'F1':
            verdict = 'WIDOCZNY (prześwit < błąd NMPT)'
        if pid in ('R2', 'R3', 'F2'):
            verdict = 'NA GRANICY: bliższa krawędź tuż ponad terenem (prześwit ≈ błąd NMPT 0,10 m), dalsza krawędź schowana za koroną pasa; trawa ≥ 0,1 m przy krawędzi zasłania całość'
        val = (f"D={x['D']} m; azymut {x['bearing_deg']}°; z_teren={x['z_ground']} m; z_oka={x['z_eye']} m; z_pasa={x['z_target']} m; "
               f"kąt do bliższej krawędzi {x['alpha_target_deg']}°; rozpiętość pionowa pasa {abs(x['runway_vertical_extent_deg']):.3f}° "
               f"(≈{abs(x['runway_vertical_extent_deg']) * 27:.1f} px przy 1080 px / 40° pionowo); najwyższa przeszkoda {x['obs_h_above_eye']:+.2f} m względem oka w {x['obs_at_m']} m; "
               f"prześwit linii wzroku min {x['clearance_near_m']:+.2f} m (do bliższej krawędzi) / {x['clearance_far_m']:+.2f} m (do dalszej); przekrój pasa widoczny w {x['cross_section_visible_of_31']}/31 punktach → {verdict}")
        add(kategoria='geometria_widoku', element=f"{pid}: {r['name']}", parametr=f'widoczność pasa 09R/27L, oko {hv} m', wartość=val, jednostka='m / °',
            lat=r['lat'], lon=r['lon'], kierunek_deg=x['bearing_deg'], wysokość_oka_m=hv, url_źródła=NMPT_SRC + '; ' + OSM_SRC, licencja=ORTHO_LIC + '; ' + OSM_LIC,
            autor='GUGiK / OSM', status='ESTIMATED',
            uwagi=f"EPSG:2180 E={r['E']} N={r['N']}; NMT w punkcie {r['nmt_ground']} m. Wzór w README §3 (m64 tools viewgeo.py). Cel = najbliższy punkt krawędzi pasa (s={r['s_target']} m od węzła 8866086772, nawierzchnia s∈[−11,4; 1342,4] wg M58).")

# ---------------------------------------------------------------- kamery
cams = [
    ('krywlany_runway (istniejąca, ADR 0196) — POTWIERDZONA', '53.101282', '23.185276', '252.5', 1.7,
     'pozycja gry lokalnie (21,1; −121,0) = EPSG:2180 E 780064,1 N 589958,0; heading 252,5°, fov 14°, pitch −0,6° — bez zmian',
     'z NMPT 2023: przekrój pasa widoczny 31/31, kąt do pętli −1,02°, rozpiętość 0,12° (≈16 px przy obiektywie 14°); prześwit +0,05 m — wynik zgodny z renderem ADR 0196 r4 (pas = ciemna wstęga). Warunek: teren gry przy pasie bez wałów z NMT 2018.'),
    ('krywlany_runway_alt (propozycja, 45 m na NNW od istniejącej)', '53.101691', '23.184993', '240', 1.7,
     'EPSG:2180 E 780042,5 N 590002,3 (1 m na zewnątrz płotu N, odcinek przy narożniku NE); patrzy wzdłuż pasa ku WSW',
     'skan płotu co 50 m (63 punkty): jedyny punkt z przekrojem 31/31 i największą rozpiętością pionową (0,39°) przy oku 1,7 m. Pozycja względem płotu ±1 m (kierunek przesunięcia na odcinku ukośnym przybliżony) — ESTIMATED.'),
    ('krywlany_road_p11_080 (droga przy rondzie, porównanie z kadrem P11-080)', '53.105805', '23.166742', '210', 1.6,
     'pozycja kamery kadru P11-080 (EXIF Commons) = EPSG:2180 E 778795,2 N 590388,2, lokalnie (−1247,8; 309,2); 7 m od way 671082746 ul. Krywlany; heading 210° ±10 (ESTIMATED: stary hangar way 304300294 w azymucie 227,7° leży 17,7° na prawo od środka kadru przy HFOV ~66° — WORKING_VALUE)',
     'pas z tego miejsca zasłonięty (punkt R1: grzbiet terenu 152,4 m ok. 240 m na S); w kadrze: płot zielony z tabliczką, skoszona trawa, samoloty, stary hangar, las — kamera do porównania z P11-080 1:1'),
    ('krywlany_road_truck (oko kierowcy ciężarówki, Dywizjonu 303 naprzeciw progu 09R)', '53.104427', '23.170405', '178.5', 2.5,
     'EPSG:2180 E 779049,1 N 590249,4 na osi jezdni S (way 443103344); heading 178,5° (prostopadle do pasa); fov 30–40°',
     'punkt R2: D=371 m, kąt −0,38°, rozpiętość pasa 0,03° (<1 px przy 1080/40°): kadr ma pokazać płot, pole i las — pasa nie da się wskazać (zgodnie z P11-099 i werdyktem M58). Drugi wariant: heading 85° (wzdłuż drogi jak P11-099, ESTIMATED z punktu zbiegu jezdni 7,6° na prawo od środka).'),
]
for name, lat, lon, hd, eye, pos, why in cams:
    add(kategoria='kamera', element=name, parametr='pozycja / azymut / wysokość oka', wartość=pos, lat=lat, lon=lon, kierunek_deg=hd, wysokość_oka_m=eye,
        url_źródła=NMPT_SRC + '; Data/Regions/bialystok-dojlidy/control_cameras_place.authored.json (origin EPSG:2180 780043, 590079)', licencja=ORTHO_LIC, autor='GUGiK / repo',
        status='ESTIMATED', uwagi=why)

# ---------------------------------------------------------------- kadry
FR = [
    ('File:20230814 174819 August 2023 in Białystok.jpg', 'P11-080', '53.105805', '23.166742', '210 (ESTIMATED, jak kamera krywlany_road_p11_080)', '2023-08-14', 'lato', 'późne popołudnie',
     'Za zielonym płotem panelowym z drutem kolczastym i czerwoną tabliczką: skoszona zielona trawa pola wzlotów, 5–6 małych samolotów na trawie, stary hangar z ciemnym dachem dwuspadowym, przed nim jasny dach szopy, pomarańczowy rękaw wiatrowskazu na maszcie, wysoki cienki maszt i drzewa po prawej, linia lasu na horyzoncie',
     'za płotem: TAK. Pas: nie da się wskazać. 7 m od way 671082746 (ul. Krywlany), ok. 30 m od Dywizjonu 303'),
    ('File:20230814 174936 August 2023 in Białystok.jpg', 'P11-079', '53.105811', '23.166776', 'UNVERIFIED', '2023-08-14', 'lato', 'późne popołudnie',
     'Asfaltowa droga rowerowa z przerywaną linią i chodnik z płyt; po prawej płot lotniska z dwoma dużymi banerami reklamowymi (napis firmowy, nie odtwarzamy), za płotem zielone pole; w głębi znaki B-33 „70”, B-36, C-13 i długi płot budowy z białej blachy po drugiej stronie drogi',
     'za płotem: TAK (pole, bez obiektów). 7,5 m od way 671082746'),
    ('File:20230814 175446 August 2023 in Białystok.jpg', 'P11-099', '53.104439', '23.170385', '85 (ESTIMATED: punkt zbiegu drogi 7,6° na prawo od środka, oś jezdni 92,5°; ±5°)', '2023-08-14', 'lato', 'późne popołudnie',
     'Widok wzdłuż ul. Dywizjonu 303 na E: dwujezdniowa droga z latarniami dwuramiennymi, droga rowerowa i chodnik z kostki po prawej; za nimi zielony płot panelowy, skoszona zielona trawa lotniska i linia lasu; w oddali po lewej duży biały budynek',
     'za płotem: TAK (trawa, las, pasa nie widać). 1,2 m od way 443103344 — najbliżej pasa (R2)'),
    ('File:20230814 174527 August 2023 in Białystok.jpg', 'P11-078', '53.106378', '23.167019', 'UNVERIFIED', '2023-08-14', 'lato', 'późne popołudnie',
     'Rondo kpt. Wünschego: wyspa z trawą, znaki A-7 i C-12, tablice prowadzące biało-czerwone; za rondem płaskie pole lotniska z płotem i banerami, rząd słupków biało-czerwonych, ciągła linia lasu na horyzoncie',
     'za płotem: TAK (pole, las). 9,4 m od way 631662841'),
    ('File:20200726 082324 Dywizjonu 303 Street in Białystok.jpg', 'P11-076', '53.105844', '23.167361', '226 (ESTIMATED: stary hangar w azymucie 233,8° leży 8,2° na prawo od środka; ±10°)', '2020-07-26', 'lato', 'rano',
     'Słupki biało-czerwone z łańcuchami na pierwszym planie, jezdnia, żółte przęsła w pasie dzielącym; za drugą jezdnią płot panelowy, skoszona zielona trawa, żółty samolot rolniczy i biały mały samolot, stary hangar z ciemnoszarym dachem i szarym drewnianym szczytem, szopa z czerwonobrązową ścianą, las sosnowy',
     'za płotem: TAK. 0,6 m od way 671082741 (Dywizjonu 303)'),
    ('File:20200726 082250 Rondo Kapitana Kazimierza Wünschego in Białystok.jpg', '—', '53.108056', '23.163611', '172 (ESTIMATED: stary hangar prawie w środku kadru, azymut 170,5° z pozycji EXIF; pozycja niepewna)', '2020-07-26', 'lato', 'rano',
     'Rondo z trawiastą wyspą, tablice prowadzące biało-czerwone, latarnie; w tle za płotem stary hangar z ciemnym dachem, pole i las; po prawej zarośla liściaste',
     'za płotem: TAK (hangar w tle). Pozycja EXIF zaokrąglona do sekund (84 m od osi Dywizjonu 303) — treść pokazuje rondo kpt. Wünschego, więc kamera stoi na rondzie; lat/lon UNVERIFIED ±80 m'),
    ('File:20240623 140546 June 2024 in Białystok.jpg', 'P11-022', '53.100470', '23.188374', '290 (ESTIMATED, M58 C58-027)', '2024-06-23', 'lato', 'dzień',
     'Zjazd z ul. Mickiewicza do zielonej stalowej bramy ramowej lotniska z żółtą tablicą; słupki biało-czerwone; przez bramę widać kawałek łąki, po obu stronach wysoki las liściasty',
     'za płotem: tylko łąka przez bramę, pasa nie widać (punkt F3: drzewa 3–4 m nad okiem 12 m od bramy). 4,7 m od way 206333509'),
    ('File:20240623 140411 June 2024 in Białystok.jpg', 'P11-023', '53.099078', '23.189562', 'ok. 333 (ESTIMATED: wzdłuż osi way 977514047, 153,2° + 180°; ±10°)', '2024-06-23', 'lato', 'dzień',
     'Ul. Mickiewicza na N: jezdnia, droga rowerowa i chodnik, tablica miejscowości; po obu stronach wysoki las i zarośla — lotniska nie widać',
     'kadr z drogi bez widoku lotniska (dowód zasłonięcia od E). 6,6 m od way 977514047'),
    ('File:20240623 140200 June 2024 in Białystok.jpg', 'P11-024', '53.098874', '23.189751', 'ok. 333 (ESTIMATED jak wyżej)', '2024-06-23', 'lato', 'dzień',
     'Ul. Mickiewicza na N: jezdnia, droga rowerowa z rowerzystami, chodnik z kostki; po obu stronach gęsty wysoki las liściasty — lotniska nie widać',
     'kadr z drogi bez widoku lotniska. 9,1 m od way 977514047'),
    ('File:20230814 175724 August 2023 in Białystok.jpg', 'P11-056', '53.104182', '23.176891', 'UNVERIFIED', '2023-08-14', 'lato', 'późne popołudnie',
     'Skrzyżowanie z boczną drogą: przejście z czerwonym przejazdem rowerowym, znaki A-7 i D-6, tablica z nazwą ulicy; dookoła płaskie pola z wysoką trawą i chwastami, las na horyzoncie po lewej',
     'kierunek kadru niepewny; zielonego płotu ani lotniska nie da się wskazać — kadr przypisany do drogi (13,4 m od way 443103344), nie do lotniska'),
    ('File:Krywlany Białystok Nowy hangar z oddali.jpg', '—', '', '', 'UNVERIFIED', '2012-08-04', 'lato', 'dzień',
     'Hangar aeroklubu z różowofioletowym tynkiem i niebieskimi wrotami, wiatrowskaz biało-czerwony na dachu; przed nim pas z popękanych płyt betonowych z trawą w spoinach; po lewej dwupłat na trawie, parking i drzewa',
     'z terenu lotniska (nie z drogi); brak współrzędnych w Commons'),
    ('File:Lotnisko na Krywlanach.jpg', '—', '', '', 'UNVERIFIED', '2011-03-27', 'wiosna (przedwiośnie)', 'dzień',
     'Pole wzlotów przedwiośniem: płowa trawa, stara płyta betonowa, jednosilnikowy górnopłat i dwupłat, w tle żółty śmigłowiec przy budynku, ściana lasu iglastego, po prawej piętrowy budynek z masztem i wiatrowskazem',
     'z terenu lotniska; kolor trawy wczesną wiosną (płowy) — odniesienie sezonowe'),
    ('File:Krywlany Białystok flota.jpg', '—', '', '', 'UNVERIFIED', '2012-08-04', 'lato', 'dzień',
     'Rząd samolotów na trawie (dwupłat, samolot rolniczy żółty, górnopłat, mniejsze) za starą płytą z płyt betonowych z trawą w spoinach; w tle niski pas drzew',
     'z terenu lotniska; samoloty — napisy i znaki rejestracyjne nie do odtworzenia'),
    ('File:Krywlany Białystok AN-2 i Wilga.jpg', '—', '', '', 'UNVERIFIED', '2012-08-04', 'lato', 'dzień',
     'Skoszona zielona trawa z pasami koszenia, dwupłat i kilka małych samolotów, w tle stary hangar z ciemnym dachem dwuspadowym, drzewa liściaste',
     'z terenu lotniska; potwierdza wygląd starego hangaru od strony pola'),
    ('File:Podlaska Straż Graniczna patrol lotniczy.jpg', '—', '', '', 'UNVERIFIED', '2011-03-27', 'wiosna (przedwiośnie)', 'dzień',
     'Górnopłat na płycie, płowa trawa, droga kołowania ze starych płyt, zwarta ściana lasu iglasto-liściastego bez liści na horyzoncie',
     'z terenu lotniska; ściana lasu na S/W (por. M68)'),
    ('File:Krywlany Białystok Stary hangar.jpg', '—', '53.104940', '23.165121', 'UNVERIFIED', '2012-08-04', 'lato', 'dzień', 'patrz wiersz obiektu „stary hangar — wygląd”', 'z terenu lotniska'),
    ('File:Krywlany Białystok Nowy hangar.jpg', '—', '53.104579', '23.164566', '238 (ESTIMATED)', '2012-08-04', 'lato', 'dzień', 'patrz wiersz obiektu „hangar aeroklubu — wygląd”', 'z terenu lotniska'),
    ('File:Krywlany Białystok Lotnicze Pogotowie ratunkowe.jpg', '—', '53.103158', '23.160957', 'UNVERIFIED', '2012-08-04', 'lato', 'dzień', 'patrz wiersz obiektu „budynek LPR — wygląd”', 'z terenu lotniska'),
]
for title, p11, lat, lon, hd, dt, se, pd, desc, note in FR:
    f, h = put_frame(title)
    pg, fu, lic, art, s1 = commons(title)
    lic2 = lic + (' (referencja, nie tekstura; atrybucja)' if 'SA' in lic else '')
    add(kategoria='kadr', element='lotnisko z drogi / od płotu' if title.startswith('File:20') else 'lotnisko — obiekty (z terenu lotniska)',
        parametr='kadr — co widać (OBEJRZANY)', wartość=p11, lat=lat, lon=lon, kierunek_deg=hd, wysokość_oka_m='ok. 1,6 (pieszy)', data_zdjęcia=dt, sezon=se, pora_dnia=pd,
        opis_co_widać=desc, url_źródła=pg, licencja=lic2, autor=art, status='SOURCED', uwagi=note + f'; sha1 oryginału {s1}; plik = miniatura ≤1600 px (thumb.php)',
        plik=f, url_pliku=fu, sha256=h)

REJ = [
    ('File:20230814 175442 August 2023 in Białystok.jpg', 'jezdnia Dywizjonu 303 i płot budowy z białej blachy po stronie N — lotnisko za plecami'),
    ('File:20230814 175444 August 2023 in Białystok.jpg', 'płot budowy z blachy, czerwona droga rowerowa, pole na N — nie lotnisko'),
    ('File:20230814 174522 August 2023 in Białystok.jpg', 'pole z nawłocią i budowa hali za płotem z blachy po stronie N — nie lotnisko'),
    ('File:20200726 083529 ul. Dywizjonu 303.jpg', 'brama ogródków działkowych — nie lotnisko'),
    ('File:20240623 140740 June 2024 in Białystok.jpg', 'furtka i płot z siatki ogródków działkowych przy Mickiewicza — nie lotnisko'),
    ('File:20240623 140941 June 2024 in Białystok.jpg', 'brama ogrodu działkowego z tablicą — nie lotnisko'),
    ('File:20240623 141118 June 2024 in Białystok.jpg', 'skrzyżowanie z ul. Karpińskiego, hala magazynowa, flagi firmowe — nie lotnisko'),
    ('File:20230814 173923 August 2023 in Białystok.jpg', 'budynek biurowy przy Dywizjonu 303 (N od ronda) — nie lotnisko'),
    ('File:20230814 174221 August 2023 in Białystok.jpg', 'ciąg pieszo-rowerowy przy wierzbach, Dywizjonu 303 na N od ronda — nie lotnisko'),
    ('File:20230814 174308 August 2023 in Białystok.jpg', 'skrzyżowanie z sygnalizacją i biurowcem — nie lotnisko'),
    ('File:20200726 082054 Dywizjonu 303 Street in Białystok.jpg', 'Dywizjonu 303 przy ogródkach i hali — nie lotnisko'),
    ('File:Krywlany Białystok Pomnik lotników.jpg', 'głaz z tablicą pamiątkową w ogródku (napis instytucji, nie odtwarzamy) — obiekt drobny, poza zakresem widoku z drogi'),
]
for t, why in REJ:
    pg, fu, lic, art, s1 = commons(t)
    add(kategoria='kadr', element='odrzucony po obejrzeniu', parametr='kadr — co widać (OBEJRZANY, ODRZUCONY)', wartość='—', opis_co_widać=why,
        url_źródła=pg, licencja=lic, autor=art, status='UNVERIFIED', url_pliku=fu,
        uwagi='nie liczony jako kadr lotniska; pliku nie zapisano w files/')

with open(os.path.join(OUT, 'manifest.csv'), 'w', newline='', encoding='utf-8') as fh:
    w = csv.DictWriter(fh, fieldnames=COLS, lineterminator='\n')
    w.writeheader()
    w.writerows(rows)
print('rows', len(rows))
import collections
print(collections.Counter(r['kategoria'] for r in rows), collections.Counter(r['status'] for r in rows))
