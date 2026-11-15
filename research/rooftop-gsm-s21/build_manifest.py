"""Buduje manifest.csv K67. Uruchom: python3 -I build_manifest.py (z katalogu research/rooftop-gsm-s21)."""
import csv, os, hashlib, json

HERE = os.path.dirname(os.path.abspath(__file__))
ACC = '2026-11-15'
COLS = ['id', 'kategoria', 'element', 'parametr', 'wartość', 'jednostka', 'lat', 'lon', 'osm_id', 'kierunek_deg', 'odległość_m', 'data_zdjęcia',
        'sezon', 'pora_dnia', 'opis_co_widać', 'url_źródła', 'licencja', 'autor', 'data_dostępu', 'status', 'uwagi', 'plik', 'sha256_pliku']
rows = []


def add(**kw):
    r = {c: '' for c in COLS}
    r.update(kw)
    r['data_dostępu'] = ACC
    rows.append(r)


def sha(fn):
    return hashlib.sha256(open(os.path.join(HERE, 'files', fn), 'rb').read()).hexdigest()


AND = 'https://www.andrew.com/products/base-station-antennas/antennas/itemffv4q4-65a-r7'
AND2 = 'https://es.andrew.com/products/base-station-antennas/antennas/itemrrzzvvq4q4-65dr8'
MW2 = 'https://es.andrew.com/products/microwave/antennas/vhlp2-23-d'
MW1 = 'https://es.andrew.com/products/microwave/antennas/vhlp1-23-d'
RRU = 'https://www.hytera.com/en/product-new/4g5g/macro-base-station/rru5800.html'
DS = 'karta katalogowa producenta (nazwa w URL, nie w opisie)'

# ---------------- 1. katalog elementów ----------------
E = [
    ('antena sektorowa panelowa — długa (wielopasmowa)', 'wymiary W×S×G', '2688 × 498 × 197', 'mm', 'jasnoszary matowy radom z laminatu szklanego (RAL 7035 wg karty)', AND2, 'SOURCED', '„Length 2688 mm”, „Width 498 mm”, „Depth 197 mm”, „Light Gray (RAL 7035)”; masa 56,5 kg; pochylenie elektryczne 2–12°'),
    ('antena sektorowa panelowa — krótka', 'wymiary W×S×G', '1499 × 498 × 197', 'mm', 'jasnoszary matowy (RAL 7035)', AND, 'SOURCED', '„Length 1499 mm”, masa 35 kg; pochylenie elektryczne 4–18° (pasma niskie), 2–12° (wysokie)'),
    ('antena radioliniowa (czasza z radomem) 0,6 m', 'średnica nominalna', '0,6', 'm', 'czasza biała, radom szary (wariant „White Antenna, Grey Radome”)', MW2, 'SOURCED', '„0.6 m | 2 ft”; masa 6,7 kg; rura montażowa 48–120 mm'),
    ('antena radioliniowa 0,3 m', 'średnica nominalna', '0,3', 'm', 'jw.', MW1, 'SOURCED', '„0.3 m | 1 ft”; masa 4,08 kg'),
    ('antena radioliniowa 0,9 / 1,2 m', 'średnica nominalna', '0,9 / 1,2', 'm', 'UNVERIFIED', '', 'UNVERIFIED', 'kart nie pobrano; na dachach Białegostoku w ortofoto nie zidentyfikowano'),
    ('moduł radiowy zdalny (RRU) przy antenie', 'wymiary W×S×G', '425 × 296 × 130', 'mm', 'UNVERIFIED w karcie (kadry: szare/białe skrzynki — brak kadrów z bliska)', RRU, 'SOURCED', '„425 mm × 296 mm ×130 mm”, 18,3 kg, IP65; typowo 1–3 na sektor — UNVERIFIED'),
    ('szafa/kontener techniczny na dachu', 'rzut', 'ok. 2 × 1 (prostokąty przy końcu bloku Kopernika 5A)', 'm', 'jasnoszare (ortofoto)', 'ortofoto GUGiK (files/ortho_kopernika.jpg)', 'ESTIMATED',
     'metoda: wymiar w px × 0,10 m/px; karty szaf — nie zweryfikowano (strony producentów puste/HTML); wysokość UNVERIFIED'),
    ('rama balastowa / stalowa krzyżowa pod maszt (X)', 'rozpiętość ramion', 'ok. 12 (11–13)', 'm', 'stal ocynk. szara (ortofoto)', 'ortofoto GUGiK (files/ortho_skor_z.jpg, 0,05 m/px z WMS)', 'ESTIMATED',
     'metoda: ramię od (290,340) do (490,485) px = 247 px × 0,05 m/px; Skorupska 17; rama zajmuje całą szerokość dachu'),
    ('maszt rurowy z odciągami na dachu', 'liczba odciągów / promień kotwienia', '6–8 / ok. 3–4', '— / m', 'stal ocynk.; odciągi cienkie', 'ortofoto GUGiK (files/ortho_asy_z.jpg, ortho_skor_z.jpg)', 'ESTIMATED',
     'promień = odległość punktów kotwienia od osi masztu w px × 0,05 m/px; OSM node 11285970200 tower:construction=guyed_tube'),
    ('maszt kratowy 3-nożny na dachu', 'wysokość nad dachem', '10–12 (środkowy), ok. 4–6 (koniec NE)', 'm', 'stal ocynk. szara', 'docs/reports/REVIEW-2026-11-14-s20-mistral-m57.md §4, §6', 'SOURCED_SECONDARY',
     'jedyny dach z wysokością z kadrów (wieżowiec przy Andersa — odsyłacz do M57, lokalizacji nie powtarzam)'),
    ('koryto kablowe (drabinkowe) po dachu', 'szerokość', 'ok. 0,4–0,5', 'm', 'stal ocynk., jasne', 'ortofoto GUGiK (files/ortho_skor_z.jpg)', 'ESTIMATED',
     'metoda: 8–10 px × 0,05 m/px; prowadzone wzdłuż attyki od masztu do narożników z antenami'),
    ('wysięgnik/maszt narożny przy attyce z antenami', 'położenie', 'narożniki dachu (Skorupska 17: NE i SW; Dobra 3: NW)', '—', 'szare', 'ortofoto GUGiK', 'VERIFIED_WIZJA (rzut)', 'wysokość nad attyką UNVERIFIED (brak kadrów z boku)'),
    ('anteny sektorowe — rozmieszczenie', 'liczba sektorów / kąt', '3 sektory co ~120° (przyjęcie typowe) — UNVERIFIED dla Białegostoku', '—', '—', '', 'UNVERIFIED',
     'w rzucie ortofoto pojedyncze panele nierozróżnialne; M57: panele wzdłuż krawędzi SE wieżowca'),
]
for el, par, val, j, kol, url, st, uw in E:
    add(kategoria='element', element=el, parametr=par, wartość=val, jednostka=j, opis_co_widać='kolor: ' + kol, url_źródła=url,
        licencja='fakty z karty (bez kopiowania)' if 'andrew' in url or 'hytera' in url else ('GUGiK, dane otwarte' if 'ortofoto' in url else ''),
        autor=DS if 'andrew' in url or 'hytera' in url else '', status=st, uwagi=uw)

# ---------------- 2. dachy ----------------
uke = json.load(open(os.path.join(HERE, 'uke_match.json')))
D = [
    ('Skorupska 17 (budynek biurowy, 4 kond. wg OSM)', '53.133953', '23.180958', 'node/6172736368; way/258938254', 'Skorupska 17', 'skor_z',
     'rama krzyżowa (X) przez całą szerokość dachu z masztem w środku i odciągami; koryta kablowe wzdłuż obu dłuższych attyk do narożników NE i SW; przy narożnikach skupiska drobnych elementów (anteny na wspornikach)'),
    ('Dobra 3 (bursa, OSM man_made=antenna)', '53.138052', '23.180663', 'node/12327277193; way/219837368', 'Dobra 3', 'dobra3',
     'przy narożniku NW skrzydła — skupisko masztów/wsporników z kilkoma talerzami (w dobra_z na krawędzi kadru); w środku dachu rama z urządzeniami; liniowe trasy kabli; reszta dachu: panele PV'),
    ('Zwierzyniecka 4 (dom asystenta, 11 kond., 34 m wg OSM)', '53.119647', '23.149357', 'node/11285970200; way/284157362', 'Zwierzyniecka 4', 'asy_z',
     'na podwyższonej części SE dachu maszt w środku z promieniście rozchodzącymi się odciągami, wokół ok. 8 okrągłych elementów (kotwy/obciążniki — UNVERIFIED)'),
    ('Hallera 19 (blok, OSM man_made=tower)', '53.153529', '23.125354', 'node/4360427819; way/224735846', 'Hallera 19', 'hallera19',
     'na dachu nadbudówki maszynowni i drobne urządzenia; masztu z antenami w rzucie nie rozpoznano'),
    ('Kopernika 5A / 7 (bloki 12 kond. wg OSM)', '53.121630', '23.143090', 'way/86631571; way/86631624', 'Kopernika 5A / 7', 'kopernika',
     'na wschodnim końcu bloku płn. skupisko prostokątnych urządzeń (szafy ok. 2 × 1 m) i drobnych wsporników; na bloku płd. podobne skupisko w środku długości'),
]
for name, lat, lon, osm, key, img, opis in D:
    u = uke.get(key.split(' /')[0].replace('Kopernika 5A', 'Kopernika 5a'), {}) if key != 'Kopernika 5A / 7' else None
    if key == 'Kopernika 5A / 7':
        ukes = 'UKE: 2 lokalizacje (Kopernika 5a: operator B; Mikołaja Kopernika 7: operator A), pasma LTE800/LTE1800/5G3600 (+GSM900 dla B)'
    elif u and u.get('n_wierszy'):
        ukes = 'UKE: operator %s, pasma %s' % ('/'.join(u['operatorzy']), ', '.join(u['pasma']))
    else:
        ukes = 'UKE: brak dopasowania adresu w 4 wykazach (LTE800/1800, GSM900, 5G3600) — UNVERIFIED'
    add(kategoria='dach', element=name, parametr='wysokość masztu nad dachem', wartość='UNVERIFIED', jednostka='m', lat=lat, lon=lon, osm_id=osm,
        kierunek_deg='nadir (ortofoto)', data_zdjęcia='data arkusza UNVERIFIED (mozaika WMS HighResolution)', sezon='wiosna (liście rozwijające się — z obrazu)',
        pora_dnia='dzień (cienie na NW)', opis_co_widać=opis, url_źródła='https://mapy.geoportal.gov.pl/wss/service/PZGIK/ORTO/WMS/HighResolution (GetMap EPSG:4326, tools/ortho_crop.py)',
        licencja='GUGiK — dane otwarte', autor='GUGiK', status='VERIFIED_WIZJA (rzut) / UNVERIFIED (wysokość)',
        uwagi=ukes + '. Wysokości nie da się wiarygodnie odczytać z ortofoto (przechył budynku, brak czytelnego cienia masztu); kadrów z boku nie pozyskano (Commons 429)',
        plik='files/ortho_%s.jpg' % img, sha256_pliku=sha('ortho_%s.jpg' % img))
add(kategoria='dach', element='wieżowiec przy Kwadrat Park — ODSYŁACZ do M57', parametr='wysokość masztów nad dachem', wartość='10–12 (środkowy kratowy), 4–6 (koniec NE), ok. 9,5 (W, gra)', jednostka='m',
    url_źródła='docs/reports/REVIEW-2026-11-14-s20-mistral-m57.md; origin/research/mistral-p14-office-tower', status='SOURCED_SECONDARY',
    uwagi='lokalizacji i układu nie powtarzam (zakres M57); UKE: 2 operatorzy (B, C) pod adresem budynku — zgodne z M57 (2 decyzje)')

# ---------------- 3. kadry (obejrzane) — ortofoto bez instalacji i kontekst ----------------
for img, opis in [('tys10a', 'Al. Tysiąclecia 10A (16 kond.): dach pokryty panelami PV; masztów GSM brak'),
                  ('waszyngtona36', 'Waszyngtona 36 (15 kond., 55 m): liczne urządzenia HVAC, świetliki; masztów z antenami nie widać'),
                  ('lakowa7', 'Łąkowa 7 (13 kond.): urządzenia wentylacyjne; masztów nie widać'),
                  ('kraszewskiego45a', 'Kraszewskiego 45A/B (13 kond.): urządzenia wentylacyjne; masztów nie widać'),
                  ('mieszka11', 'Mieszka I 11 (12 kond.): nadbudówki klatek; masztów nie widać'),
                  ('waska4', 'Wąska 4 (12 kond.): nadbudówki; masztów nie widać'),
                  ('wasilkowska47', 'Wasilkowska 47 (12 kond.): falista linia (kabel/rura) po dachu; masztów nie widać'),
                  ('towarowa8a', 'Towarowa 8A (12 kond.): nadbudówki klatek; masztów nie widać'),
                  ('skorupska17', 'Skorupska 17 — kontekst 80 m (rama X i koryta widoczne, por. skor_z)'),
                  ('dobra3', 'Dobra 3 — kontekst 80 m: skupisko przy narożniku NW, trasy kabli, PV'),
                  ('asystenta', 'Zwierzyniecka 4 — kontekst 80 m: budynek silnie „przechylony” w ortofoto (widać elewację SW)')]:
    add(kategoria='kadr', element='ortofoto dachu (rzut)', parametr='obecność instalacji GSM', wartość='nie' if 'nie widać' in opis or 'brak' in opis else 'tak', jednostka='—',
        kierunek_deg='nadir', data_zdjęcia='UNVERIFIED (mozaika WMS)', sezon='wiosna', pora_dnia='dzień', opis_co_widać=opis,
        url_źródła='GUGiK WMS ORTO HighResolution', licencja='GUGiK — dane otwarte', autor='GUGiK', status='VERIFIED_WIZJA',
        uwagi='negatyw: z 8 sprawdzonych wysokich bloków bez przypisania OSM/UKE żaden nie ma widocznego masztu (próba nielosowa)' if 'nie widać' in opis or 'brak' in opis else '',
        plik='files/ortho_%s.jpg' % img, sha256_pliku=sha('ortho_%s.jpg' % img))

# ---------------- 4. przepisy / UKE ----------------
add(kategoria='przepis', element='Prawo budowlane art. 29 ust. 3 pkt 3 lit. a', parametr='zgłoszenie (bez pozwolenia) — instalacje radiokomunikacyjne na obiektach', wartość='> 3 m i ≤ 12 m', jednostka='m',
    opis_co_widać='„wysokości większej niż 3 m i nie większej niż 12 m” (instalowanie urządzeń technicznych, w tym instalacji radiokomunikacyjnych, na obiektach budowlanych)',
    url_źródła='https://standardyprawa.pl/akt/20/art/3647 (tekst ustawy; do potwierdzenia w ISAP)', licencja='akt prawny', status='SOURCED', uwagi='ust. 4 pkt 3 lit. a: do 3 m — bez zgłoszenia')
add(kategoria='przepis', element='Prawo budowlane art. 29 ust. 4 pkt 3 lit. a', parametr='bez pozwolenia i zgłoszenia', wartość='≤ 3 m', jednostka='m',
    opis_co_widać='instalacje radiokomunikacyjne na obiektach budowlanych o „wysokości nie większej niż 3 m”', url_źródła='https://standardyprawa.pl/akt/20/art/3647', licencja='akt prawny', status='SOURCED', uwagi='')
add(kategoria='przepis', element='Rozp. MI z 12.01.2021 w sprawie przeszkód lotniczych (Dz.U. 2021 poz. 264) § 35 ust. 1', parametr='oznakowanie nocne przeszkody < 45 m npt', wartość='światła małej intensywności typu A lub B na szczycie', jednostka='—',
    opis_co_widać='„Oznakowanie nocne przeszkody lotniczej o wysokości mniejszej niż 45 m powyżej poziomu otaczającego terenu lub wody”', url_źródła='https://api.sejm.gov.pl/eli/acts/DU/2021/264/text.html',
    licencja='akt prawny', status='SOURCED', uwagi='kolor świateł — tekst odsyła do Załącznika 14 ICAO (tab. 6-1), nie podaje; tekst jednolity Dz.U. 2025 poz. 903 — nie sprawdzono')
add(kategoria='przepis', element='jw. § 46 ust. 1 pkt 1', parametr='zwolnienie z oznakowania dziennego', wartość='budynki mieszkalne/użyteczności publicznej, chyba że dominanta przewyższa budynek o ≥ 5 m', jednostka='—',
    opis_co_widać='wg odczytu § 46 ust. 1 pkt 1 (parafraza; dominanta niezdefiniowana w rozporządzeniu)', url_źródła='https://api.sejm.gov.pl/eli/acts/DU/2021/264/text.html', licencja='akt prawny', status='SOURCED',
    uwagi='czy maszt GSM na dachu jest „dominantą” — UNVERIFIED (interpretacja); ŻADEN z obejrzanych dachów nie pokazuje biało-czerwonego malowania (rzut ortofoto)')
add(kategoria='przepis', element='Wykaz UKE pozwoleń radiowych (GSM/UMTS/LTE/5G)', parametr='kolumny wykazu', wartość='operator, nr decyzji, rodzaj, data ważności, dł./szer. geogr., miejscowość, lokalizacja (adres), IdStacji, TERYT', jednostka='—',
    opis_co_widać='wykaz NIE zawiera wysokości anteny n.p.t./n.p.m. ani azymutów', url_źródła='https://bip.uke.gov.pl/pozwolenia-radiowe/wykaz-pozwolen-radiowych-tresci/stacje-gsm-umts-lte-5gnr-oraz-cdma,12,0.html (pliki xlsx „stan na 2026-10-26”)',
    licencja='informacja publiczna', autor='UKE', status='SOURCED', uwagi='Białystok w 4 plikach (LTE800, LTE1800, GSM900, 5G3600): 419 wierszy, 124 lokalizacje; sha256 plików w sources.md')

for i, r in enumerate(rows, 1):
    r['id'] = 'K67-%03d' % i
with open(os.path.join(HERE, 'manifest.csv'), 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=COLS)
    w.writeheader(); w.writerows(rows)
print(len(rows))
