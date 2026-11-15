"""Buduje manifest.csv K69 z danych w tym katalogu (osm_spacing_summary.json, frames.json) i tabel wpisanych niżej.
Uruchom: python3 -I build_manifest.py  (z katalogu research/night-lamps-s21)."""
import csv, json, os

HERE = os.path.dirname(os.path.abspath(__file__))
ACC = '2026-11-15'
COLS = ['id', 'kategoria', 'ulica', 'way_id', 'element', 'parametr', 'wartość', 'jednostka', 'lat', 'lon', 'kierunek_deg',
        'data_godzina', 'opis_co_widać', 'ułamek_jezdni_oświetlony', 'halo', 'url_źródła', 'licencja', 'autor', 'data_dostępu',
        'status', 'uwagi', 'plik', 'url_pliku', 'sha256_pliku']
rows = []


def add(**kw):
    r = {c: '' for c in COLS}
    r.update({k: ('' if v is None else v) for k, v in kw.items()})
    r['data_dostępu'] = r['data_dostępu'] or ACC
    rows.append(r)


# ---------- 1. odcinki: rozstaw z OSM ----------
OSM_URL = 'https://api.openstreetmap.org/api/0.6/map (kafle 0,01°, bbox 53.095–53.165 N, 23.120–23.215 E; plik osm-street-lamps.json)'
summ = json.load(open(os.path.join(HERE, 'osm_spacing_summary.json')))
for name, n, sides, ways, npairs, mn, med, mx, p25, p75 in summ:
    if npairs < 10 and name != 'Kombatantów':
        continue
    rows_s = {k: v for k, v in sides.items()}
    uk = 'jednostronny' if len([k for k in rows_s if k in ('L', 'P') and rows_s[k] >= 3]) == 1 else 'obustronny (oba rzędy ≥ 3 lampy)'
    add(kategoria='odcinek', ulica=name, way_id=';'.join(str(w) for w in ways), element='latarnie OSM highway=street_lamp',
        parametr='rozstaw kolejnych słupów w rzędzie (min / mediana / max; p25–p75)',
        wartość='%s / %s / %s; %s–%s' % (mn, med, mx, p25, p75), jednostka='m',
        opis_co_widać='n_par=%d, n_lamp=%d, rzędy względem osi way: %s; układ: %s (z OSM; nie z kadrów)' % (npairs, n, rows_s, uk),
        url_źródła=OSM_URL, licencja='ODbL 1.0', autor='OpenStreetMap contributors', status='SOURCED (OSM, obliczenie)' if npairs >= 10 else 'ESTIMATED (n<10)',
        uwagi='odstępy 5–80 m; > 80 m odrzucone jako brak mapowania; lampy ≤ 25 m od osi nazwanej drogi; pary tylko w obrębie tego samego way i rzędu')

# ---------- 1b. ulice trasy: ortofoto z C60 (bez powtarzania) ----------
C60 = 'research/cloud/p17-dusk-lighting/ortho_lamp_spacing.csv (gałąź origin/research/cloud-p17-dusk-lighting; recenzja docs/reports/REVIEW-2026-11-14-s20-cloud-m60-compare.md)'
for ul, v, n, uk in [('gen. Andersa', '41,6 (39,5–43,3)', 6, 'rząd w pasie dzielącym; rzędy boczne 38,7 i 42,2 m'),
                     ('gen. Maczka', '40,4 (39,5–41,0)', 6, 'pas dzielący; recenzja odtworzyła 40,3/39,8/39,5'),
                     ('Al. Tysiąclecia PP (odc. płd.)', '34,8 (33,6–36,7)', 7, 'pas dzielący'),
                     ('Sokólska', '32,4 (26,3–35,5)', 5, 'jednostronnie, z cieni, niska pewność')]:
    add(kategoria='odcinek', ulica=ul, element='słupy z ortofoto GUGiK (C60)', parametr='rozstaw mediana (zakres)', wartość=v, jednostka='m',
        opis_co_widać='n_par=%d; %s' % (n, uk), url_źródła=C60, licencja='GUGiK (dane otwarte)', autor='C60 (chmura s20)',
        status='SOURCED_SECONDARY', uwagi='przywołane, NIE mierzone ponownie (zakres M60); n<10 — kryterium ≥10 par spełniają odcinki OSM powyżej')
add(kategoria='odcinek', ulica='Kuronia / Mickiewicza / Dywizjonu 303 / Wysockiego', element='latarnie', parametr='rozstaw', wartość='UNVERIFIED',
    opis_co_widać='w OSM < 3 latarnie na ulicę; pas ortofoto Kuronia nie trafił w oś (zakręt) — nie mierzono', url_źródła=OSM_URL,
    status='UNVERIFIED', uwagi='luka: pomiar ortofoto 0,1 m/px wymaga ok. 450 m pasa na ≥ 10 par (tools/strip.py)')

# ---------- 1c. tagi OSM ----------
for par, val in [('lamp_mount=bent_mast', 701), ('lamp_mount=straight_mast', 256), ('lamp_mount=angled_mast', 4),
                 ('light:count=1', 348), ('light:count=2', 213), ('light:count=3', 23), ('light:count=4', 10),
                 ('lamp_type=sodium', 21), ('light:method=led (4) + lamp_type=led (1)', '4+1'), ('support=pole', 39)]:
    add(kategoria='oprawa', ulica='Białystok (bbox jw.)', element='tag OSM węzłów street_lamp (n=1443)', parametr=par, wartość=str(val),
        jednostka='węzłów', url_źródła=OSM_URL, licencja='ODbL 1.0', autor='OpenStreetMap contributors', status='SOURCED (OSM)',
        uwagi='tag lamp_type=sodium/led jest nieaktualny po wymianach 2023–2025 (dokumenty ZDM niżej) — nie używać jako barwy')

# ---------- 2/3. kadry ----------
frames = json.load(open(os.path.join(HERE, 'frames.json')))
for f in frames:
    add(**f)

# ---------- 2b. typy opraw (sylwetki) ----------
TYPES = [
    ('T1', 'dwuramienna łukowa („pastorał” podwójny) w pasie dzielącym', 'Maczka, Andersa (Putry), Al. Tysiąclecia PP',
     'jasnoszary/biały metaliczny słup stożkowy; rozwidlenie ok. 0,9 h; dwa ramiona wznoszą się łukiem i kończą płaską oprawą lekko uniesioną; wysięg każdego ramienia 0,13–0,17 h (ESTIMATED z 3eba62ce: 145/880 i 115/880 px, perspektywa); długość głowicy ok. 0,07 h',
     'kadry: b0948023, 9c0cc814, 75326b64, a3a2db1c, 6ad5b307, 3eba62ce, 5f92573a, 86106e2b, 6af663fb, aa64b81d (10)'),
    ('T2', 'jednoramienna łukowa przy krawędzi jezdni, płaska oprawa', 'Al. Tysiąclecia PP, Andersa (Putry), Kalinowskiego, Kołłątaja, Lipowa (2006)',
     'jak T1, jedno ramię nad jezdnią; wysięg 0,13–0,17 h (ESTIMATED, sylwetka jak T1); na ulicach osiedlowych/śródmieścia niższe słupy',
     'kadry: 4033e6b8, 3eba62ce, 86106e2b, cm_kal, cm_kol, ov_10c97958, cm_014, ov_10510274 (8)'),
    ('T3', 'ozdobna jednoramienna (łabędzia szyja / pastorał ozdobny) na smukłym słupie', 'Lipowa (deptak), Plac NZS',
     'ciemny, smukły słup ozdobny; jedno łukowe ramię z oprawą zwisającą; dekoracje świąteczne w XII', 'kadry: cm_016, cm_017, cm_014 (3)'),
    ('T4', 'ozdobna wielokulowa (2–4 kule na poprzeczce/kandelabrze)', 'Rynek Kościuszki',
     'niskie słupy ozdobne z 2 (cm_018) lub 3–4 (ef5f02ef) kulistymi kloszami; światło ciepłe', 'kadry: cm_018, ov_ef5f02ef, ov_9e8c0919 (3)'),
    ('T5', 'parkowa post-top (klosz na szczycie słupa)', 'osiedle przy Swobodnej',
     'szary stalowy słup ok. 4–5 m (ESTIMATED, niska pewność), klosz grzybkowy; zimna/neutralna biel', 'kadry: pnx c1a5e40e (3 lampy w jednym kadrze), c0c6954b (słup bez oprawy) — < 3 kadrów, typ NIEKOMPLETNY'),
]
for t, name, where, sil, fr in TYPES:
    add(kategoria='oprawa', ulica=where, element=t + ' ' + name, parametr='sylwetka (słup + ramię + oprawa)', wartość=sil, jednostka='h = wysokość punktu świetlnego',
        opis_co_widać=fr, url_źródła='kadry w tym manifeście (kategoria kadr/oprawa)', licencja='—', autor='K69 (opis)', status='ESTIMATED' if t in ('T1', 'T2') else 'VERIFIED_WIZJA',
        uwagi='h bezwzględne: UNVERIFIED (dokumenty ZDM: „określenie wysokości słupów, długości wysięgników … leży w gestii Wykonawcy”); gra: GP 11 m')
add(kategoria='oprawa', ulica='trasa C', element='T1/T2', parametr='pochylenie oprawy w terenie', wartość='0…+10 (uniesione, ESTIMATED z sylwetek 2019); dopuszczalna regulacja uchwytu LED 0…−20°', jednostka='°',
    opis_co_widać='na 3eba62ce i b0948023 płaskie głowice lekko uniesione ku końcowi ramienia', url_źródła='kadry 3eba62ce, b0948023; ZDM-VII.7021.1.14.2023 s. 2 pkt 2i', status='ESTIMATED',
    uwagi='pochylenie po wymianie LED — UNVERIFIED (brak kadrów 2024+ z trasy)')

# ---------- 4. barwa: dokumenty ZDM ----------
EZ = 'https://miastobialystok.ezamawiajacy.pl/pn/miastobialystok/demand/notice/public/%s/details'
docs = [
    ('93688', 'ZDM-VII.7021.1.14.2023 (zał. 9 do SWZ ZDM-XIV.271.31.2023), s. 1 pkt 2a', 'gen. W. Andersa; al. 1000-lecia PP; gen. S. Maczka',
     '„temperatura barwowa diod dla opraw oświetlenia ulicznego 4000°K”', '4000', 'Zał. nr 9 do SWZ - Warunki techniczne.pdf',
     '05301ed100b3f6988e2e3b077060ad8adef2d960458a169070ca2a863fca3a92'),
    ('120561', 'ZDM-VII.7021.1.4.2024 (zał. 9 do SWZ ZDM-XIV.271.3.2024), s. 1 pkt 2a–b', 'W. Wysockiego',
     '„temperatura barwowa diod dla opraw oświetlenia ulicznego 4000°K”; „…doświetlenia przejść dla pieszych 5700°K”', '4000 (przejścia 5700)',
     'Zał. nr 9 do SWZ - Warunki techniczne.zip → ZDM-VII.7021.1.4.2024.pdf', 'fffc44b5cad73a0a377346b20c984706352f8006f03ce113e9b98c497d701134 (ZIP)'),
    ('122716', 'ZDM-VII.7021.1.7.2024 (zał. 9 do SWZ ZDM-XIV.271.13.2024), s. 1 pkt 2a–b; s. 3 pkt 3a', 'A. Mickiewicza; J. Kuronia; Dywizjonu 303',
     '„temperatura barwowa diod dla opraw oświetlenia ulicznego 4000°K”; przejścia 5700°K; parkowe 4000°K', '4000 (przejścia 5700)',
     'Zał. nr 9 i 10 do SWZ - Warunki tech., schematy.zip → ZDM-VII.7021.1.7.2024.pdf', '(ZIP 3 037 570 B; sha256 w sources.md)'),
]
for nid, ref, streets, quote, val, fn, sha in docs:
    for st in streets.split('; '):
        add(kategoria='barwa', ulica=st, element='oprawy LED (projekt wymiany)', parametr='CCT z warunków technicznych ZDM', wartość=val, jednostka='K',
            opis_co_widać=quote, url_źródła=EZ % nid + ' — ' + ref, licencja='dokument urzędowy', autor='Zarząd Dróg Miejskich UM Białystok',
            status='SOURCED', uwagi='to wymaganie przetargu; montaż w terenie: zamówienie udzielone (TED 658997-2023 / 769998-2024), stan 2026 z kadrów — UNVERIFIED', plik=fn, sha256_pliku=sha)
add(kategoria='barwa', ulica='Andersa, 1000-lecia, Maczka (stan przed wymianą)', element='oprawy istniejące', parametr='moc opraw demontowanych',
    wartość='70, 100, 150, 250', jednostka='W', opis_co_widać='„oprawami oświetleniowymi typu […] oraz oprawy tunelowe o mocach 70, 100, 150, 250 W”',
    url_źródła=EZ % '93688' + ' — ZDM-VII.7021.1.14.2023 s. 1', licencja='dokument urzędowy', autor='ZDM UM Białystok', status='SOURCED',
    uwagi='nazwy handlowe typów opraw pominięte (zasada: bez marek); moce typowe dla wysokoprężnych sodowych — wniosek, nie cytat')
add(kategoria='barwa', ulica='trasa C (2023/2024)', element='oprawy LED', parametr='redukcja nocna', wartość='100 % do 22:00; 70 % 22:00–5:00; 100 % od 5:00',
    jednostka='% strumienia', opis_co_widać='„od godz. 22 do godz. 5 – poziom 70% strumienia świetlnego”', url_źródła=EZ % '93688' + ' — s. 2 pkt 2g; także 122716 s. 2 pkt 2h',
    licencja='dokument urzędowy', autor='ZDM UM Białystok', status='SOURCED', uwagi='przejścia dla pieszych (2024): 100 % całą noc')
add(kategoria='barwa', ulica='trasa C (2023/2024)', element='oprawy LED', parametr='regulacja pochylenia oprawy', wartość='wysięgnik 0…−20° (2023) / 0…−15° (2024); szczyt słupa 0…20° / 0…15°',
    jednostka='°', opis_co_widać='„od 0° do -20° dla zamocowania na wysięgniku i od 0° do 20° dla zamocowania na szczycie słupa”',
    url_źródła=EZ % '93688' + ' — s. 2 pkt 2i; 122716 s. 2 pkt 2j', licencja='dokument urzędowy', autor='ZDM UM Białystok', status='SOURCED',
    uwagi='zakres regulacji uchwytu, nie faktyczne nachylenie w terenie')
add(kategoria='barwa', ulica='trasa C (2023/2024)', element='oprawy LED', parametr='klosz / Ra / skuteczność', wartość='płaski hartowany; Ra ≥ 70; ≥ 130 lm/W',
    jednostka='—', opis_co_widać='„klosz oprawy płaski - wykonany z hartowanego szkła”; „współczynnik Ra ≥ 70”', url_źródła=EZ % '93688' + ' — s. 1 pkt 2b–d',
    licencja='dokument urzędowy', autor='ZDM UM Białystok', status='SOURCED', uwagi='płaski klosz = pełne odcięcie (zgodne z założeniem 0191)')
add(kategoria='barwa', ulica='Dojlidy (122716)', element='oprawy istniejące', parametr='moc opraw demontowanych', wartość='70, 100, 150, 250 (SWZ: także 400)', jednostka='W',
    opis_co_widać='„oprawami oświetleniowymi o mocach 70, 100, 150, 250”', url_źródła=EZ % '122716' + ' — ZDM-VII.7021.1.7.2024 s. 1; SWZ pkt 3.4', licencja='dokument urzędowy',
    autor='ZDM UM Białystok', status='SOURCED', uwagi='wysokość słupów i długość wysięgników „leży w gestii Wykonawcy” (s. 4 pkt 12) — w dokumentach brak liczb')
for nr, d, streets in [('658997-2023', '2023-10-30', 'Maczka (wynik postępowania 2023)'), ('769998-2024', '2024-12-17', 'Kuronia, Mickiewicza, Dywizjonu 303 (ZDM-XIV.271.13.2024)')]:
    add(kategoria='barwa', ulica=streets, element='ogłoszenie o udzieleniu zamówienia (TED)', parametr='zamówienie udzielone', wartość=d, jednostka='data',
        url_źródła='https://ted.europa.eu/pl/notice/-/detail/%s (treść przez API v3 /notices/search)' % nr, licencja='dokument urzędowy UE', autor='Miasto Białystok',
        status='SOURCED', uwagi='udzielenie ≠ montaż; data montażu UNVERIFIED')

for i, r in enumerate(rows, 1):
    r['id'] = 'K69-%03d' % i
with open(os.path.join(HERE, 'manifest.csv'), 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=COLS)
    w.writeheader()
    w.writerows(rows)
print(len(rows), 'wierszy')
