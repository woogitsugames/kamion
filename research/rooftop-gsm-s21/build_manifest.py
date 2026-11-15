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
     'promień = odległość punktów kotwienia od osi masztu w px × 0,05 m/px; OSM node 11285970200 tower:construction=guyed_tube; wysokość nad dachem (Zwierzyniecka 4) ≥ 8,55 m z LIDAR 2025-04-18 (K67-042)'),
    ('maszt kratowy 3-nożny na dachu', 'wysokość nad dachem', '9–12 (wieżowiec, M57-FIX #88); ok. 4–6 (koniec NE)', 'm', 'stal ocynk. szara', 'docs/reports/REVIEW-2026-11-14-s20-mistral-m57.md §4, §6; PR #88 (M57-FIX)', 'SOURCED_SECONDARY',
     'wieżowiec — odsyłacz do M57 (lokalizacji nie powtarzam). Kontrola LIDAR 2025-04-18: najwyższy maszt (koniec SW / narożnik W, z odciągami) ≥ 10,95 m; pozostałe 4,55–5,35 m (K67-053…058)'),
    ('koryto kablowe (drabinkowe) po dachu', 'szerokość', 'ok. 0,4–0,5', 'm', 'stal ocynk., jasne', 'ortofoto GUGiK (files/ortho_skor_z.jpg)', 'ESTIMATED',
     'metoda: 8–10 px × 0,05 m/px; prowadzone wzdłuż attyki od masztu do narożników z antenami'),
    ('wysięgnik/maszt narożny przy attyce z antenami', 'położenie', 'narożniki dachu (Skorupska 17: NE i SW; Dobra 3: NW)', '—', 'szare', 'ortofoto GUGiK', 'VERIFIED_WIZJA (rzut)', 'wysokość nad dachem z LIDAR 2025-04-18: Skorupska 17 NE/SW/W 4,35–4,75 m, Dobra 3 NW 7,65 m (K67-037…039, 041)'),
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
    ('Dobra 3 (bursa, OSM man_made=antenna)', '53.138052', '23.180663', 'node/12327277193; way/219837368', 'Dobra 3', 'dobra_c',
     'przy narożniku NW skrzydła skupisko masztów/wsporników z talerzami; przy węźle skrzydeł (E) maszt kratowy z talerzem; między nimi rama z szafami i koryto kablowe; reszta dachu: panele PV (wycinek przecentrowany ortho_dobra_c — cały dach skrzydła NW w kadrze)'),
    ('Zwierzyniecka 4 (dom asystenta, 11 kond., 34 m wg OSM)', '53.119647', '23.149357', 'node/11285970200; way/284157362', 'Zwierzyniecka 4', 'asy_z',
     'na podwyższonej części SE dachu maszt w środku z promieniście rozchodzącymi się odciągami, wokół ok. 8 okrągłych elementów (kotwy/obciążniki — UNVERIFIED)'),
    ('Hallera 19 (blok, OSM man_made=tower)', '53.153529', '23.125354', 'node/4360427819; way/224735846', 'Hallera 19', 'hallera19',
     'na dachu nadbudówki maszynowni i drobne urządzenia; masztu z antenami w rzucie nie rozpoznano'),
    ('Kopernika 5A / 7 (bloki 12 kond. wg OSM)', '53.121630', '23.143090', 'way/86631571; way/86631624', 'Kopernika 5A / 7', 'kopernika',
     'na wschodnim końcu bloku płn. skupisko prostokątnych urządzeń (szafy ok. 2 × 1 m) i drobnych wsporników; na bloku płd. podobne skupisko w środku długości'),
]
# --- M67-FIX: wysokości z LIDAR GUGiK 2025-04-18 (tools/lidar_masts.py → out/lidar_masts.json)
LM = json.load(open(os.path.join(HERE, 'out', 'lidar_masts.json')))
SK = json.load(open(os.path.join(HERE, 'out', 'skorowidz.json')))
LKEY = {'Skorupska 17': 'skorupska17', 'Dobra 3': 'dobra3', 'Zwierzyniecka 4': 'zwierzyniecka4', 'Hallera 19': 'hallera19', 'Kopernika 5A / 7': 'kopernika5a'}
LIDAR_URL = {k: [f for f in v['LIDAR'] if f.get('akt_data') == '2025-04-18'][0]['url_do_pobrania'] for k, v in SK.items()}
LIDAR_URL['wiezowiec_m57'] = 'https://opendata.geoportal.gov.pl/NumDaneWys/DanePomiaroweLAZ/83268/83268_1745956_N-34-107-C-b-1-2-3-2.laz'
LIDAR_UTC = {k: v['urzadzenia'][0]['utc_szczytu'][11:16] for k, v in LM.items()}
METH = ('LIDAR GUGiK 12 p/m² (2025-04-18, PL-EVRF2007-NH): h = Z_max w walcu r = 1 m − dominanta Z dachu w pierścieniu 2–6 m; '
        '± 0,15 m (ESTIMATED) i wynik jako DOLNA granica (odstęp punktów ≈ 0,29 m — szczyt cienkiej rury może nie mieć trafienia)')


def mmm(vals):
    v = sorted(vals)
    med = v[len(v) // 2] if len(v) % 2 else (v[len(v) // 2 - 1] + v[len(v) // 2]) / 2
    return ('%.1f / %.1f / %.1f (n = %d)' % (v[0], med, v[-1], len(v))).replace('.', ',')


def tel(k):
    return [u['h'] for u in LM[k]['urzadzenia'] if u.get('telecom') is True]


LIDAR_SUMMARY = {
    'skorupska17': (mmm(tel('skorupska17')), 'MEASURED (LIDAR)', METH + '. Maszt środkowy na ramie X ≥ 11,55 m; wsporniki narożne 4,35–4,75 m.'),
    'dobra3': (mmm(tel('dobra3')), 'MEASURED (LIDAR)', METH + '. Maszt przy węźle skrzydeł ≥ 9,55 m; narożnik NW ≥ 7,65 m.'),
    'zwierzyniecka4': (mmm(tel('zwierzyniecka4')), 'MEASURED (LIDAR)', METH + '. Jeden maszt rurowy z odciągami ≥ 8,55 m nad podwyższoną częścią SE (n = 1). Element przy krawędzi N (h = 5,85 m, szczyt 2 punkty) — przynależność telekom. UNVERIFIED, poza statystyką.'),
    'hallera19': ('brak urządzeń > 1,3 m nad dachem', 'MEASURED (LIDAR) — negatyw', METH + '. Najwyższe elementy: nadbudówki 1,05–1,25 m; tag OSM man_made=tower NIEPOTWIERDZONY w danych 2025.'),
    'kopernika5a': (mmm(tel('kopernika5a')), 'MEASURED (LIDAR)', METH + '. Wsporniki/platformy przy końcach bloków 2,55–3,35 m (w granicy ≤ 3 m z art. 29 ust. 4 lub tuż ponad); identyfikacja jako telekom. z rzutu (ortho_kopernika_n/_s).'),
}
for name, lat, lon, osm, key, img, opis in D:
    u = uke.get(key.split(' /')[0].replace('Kopernika 5A', 'Kopernika 5a'), {}) if key != 'Kopernika 5A / 7' else None
    if key == 'Kopernika 5A / 7':
        ukes = 'UKE: 2 lokalizacje (Kopernika 5a: operator B; Mikołaja Kopernika 7: operator A), pasma LTE800/LTE1800/5G3600 (+GSM900 dla B)'
    elif u and u.get('n_wierszy'):
        ukes = 'UKE: operator %s, pasma %s' % ('/'.join(u['operatorzy']), ', '.join(u['pasma']))
    else:
        ukes = 'UKE: brak dopasowania adresu w 4 wykazach (LTE800/1800, GSM900, 5G3600) — UNVERIFIED'
    rk = LKEY[key]
    hv, hst, hnote = LIDAR_SUMMARY[rk]
    add(kategoria='dach', element=name, parametr='wysokość urządzeń telekom. nad dachem (min / mediana / max)', wartość=hv, jednostka='m', lat=lat, lon=lon, osm_id=osm,
        kierunek_deg='nadir (ortofoto) + LIDAR', data_zdjęcia='2025-04-18 (LIDAR i ortofoto wg skorowidzy WFS GUGiK)', sezon='wiosna (liście rozwijające się — z obrazu)',
        pora_dnia='LIDAR %s UTC' % LIDAR_UTC[rk], opis_co_widać=opis,
        url_źródła='LIDAR: %s; ortofoto: https://mapy.geoportal.gov.pl/wss/service/PZGIK/ORTO/WMS/HighResolution (tools/ortho_crop.py)' % LIDAR_URL[rk],
        licencja='GUGiK — dane otwarte', autor='GUGiK', status=hst,
        uwagi=ukes + '. ' + hnote,
        plik='files/ortho_%s.jpg' % img, sha256_pliku=sha('ortho_%s.jpg' % img))
add(kategoria='dach', element='wieżowiec przy Kwadrat Park — ODSYŁACZ do M57', parametr='wysokość masztów nad dachem', wartość='9–12 (M57-FIX #88); kontrola LIDAR: ' + mmm(tel('wiezowiec_m57')), jednostka='m',
    url_źródła='docs/reports/REVIEW-2026-11-14-s20-mistral-m57.md; PR #88 (research/mistral-p14-office-tower-fix-s21); LIDAR ' + LIDAR_URL['wiezowiec_m57'], status='SOURCED_SECONDARY + MEASURED (LIDAR)',
    uwagi='lokalizacji i układu nie powtarzam (zakres M57); UKE: 2 operatorzy (B, C). LIDAR 2025-04-18: maszt z odciągami przy końcu SW / narożniku W ≥ 10,95 m; przy środku krawędzi SE tylko 5,25 m — masztu 10–12 m w środku krawędzi SE w danych 2025 NIE MA (do rozstrzygnięcia w M57)')

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
ELI = 'https://api.sejm.gov.pl/eli/acts/DU/2026/524/text.pdf (t.j. Dz.U. 2026 poz. 524, obwieszczenie z 27.03.2026; ISAP WDU20260000524)'
add(kategoria='przepis', element='Prawo budowlane art. 29 ust. 3 pkt 3 lit. a', parametr='zgłoszenie (bez pozwolenia) — instalacje radiokomunikacyjne na obiektach', wartość='> 3 m i ≤ 12 m', jednostka='m',
    opis_co_widać='„wysokości większej niż 3 m i nie większej niż 12 m” (instalowanie urządzeń technicznych, w tym instalacji radiokomunikacyjnych, na obiektach budowlanych)',
    url_źródła=ELI, licencja='akt prawny', status='VERIFIED (ELI/ISAP)', uwagi='brzmienie potwierdzone w tekście jednolitym 2026 (s. 26 PDF): „… antenowe konstrukcje wsporcze, o wysokości większej niż 3 m i niewiększej niż 12 m”; wcześniej cytat ze strony wtórnej standardyprawa.pl; sha256 PDF 4a33b840883a10aa6f68d3cd85ac673a727b6b822ef092b1b97efbcdfda57826')
add(kategoria='przepis', element='Prawo budowlane art. 29 ust. 4 pkt 3 lit. a', parametr='bez pozwolenia i zgłoszenia', wartość='≤ 3 m', jednostka='m',
    opis_co_widać='instalacje radiokomunikacyjne na obiektach budowlanych „… oraz antenowa konstrukcja wsporcza, o wysokości niewiększej niż 3 m”', url_źródła=ELI, licencja='akt prawny', status='VERIFIED (ELI/ISAP)',
    uwagi='brzmienie potwierdzone w t.j. 2026 (s. 27 PDF); por. art. 29 ust. 1 pkt 37 lit. b: wolno stojące maszty bezodciągowe dla urządzeń radiokomunikacyjnych ≤ 7 m — zgłoszenie (nie dotyczy dachów)')
add(kategoria='przepis', element='Rozp. MI z 12.01.2021 w sprawie przeszkód lotniczych (Dz.U. 2021 poz. 264) § 35 ust. 1', parametr='oznakowanie nocne przeszkody < 45 m npt', wartość='światła małej intensywności typu A lub B na szczycie', jednostka='—',
    opis_co_widać='„Oznakowanie nocne przeszkody lotniczej o wysokości mniejszej niż 45 m powyżej poziomu otaczającego terenu lub wody”', url_źródła='https://api.sejm.gov.pl/eli/acts/DU/2021/264/text.html',
    licencja='akt prawny', status='SOURCED', uwagi='kolor świateł — tekst odsyła do Załącznika 14 ICAO (tab. 6-1), nie podaje; tekst jednolity Dz.U. 2025 poz. 903 — nie sprawdzono')
add(kategoria='przepis', element='jw. § 46 ust. 1 pkt 1', parametr='zwolnienie z oznakowania dziennego', wartość='budynki mieszkalne/użyteczności publicznej, chyba że dominanta przewyższa budynek o ≥ 5 m', jednostka='—',
    opis_co_widać='wg odczytu § 46 ust. 1 pkt 1 (parafraza; dominanta niezdefiniowana w rozporządzeniu)', url_źródła='https://api.sejm.gov.pl/eli/acts/DU/2021/264/text.html', licencja='akt prawny', status='SOURCED',
    uwagi='czy maszt GSM na dachu jest „dominantą” — UNVERIFIED (interpretacja); ŻADEN z obejrzanych dachów nie pokazuje biało-czerwonego malowania (rzut ortofoto)')
add(kategoria='przepis', element='Wykaz UKE pozwoleń radiowych (GSM/UMTS/LTE/5G)', parametr='kolumny wykazu', wartość='operator, nr decyzji, rodzaj, data ważności, dł./szer. geogr., miejscowość, lokalizacja (adres), IdStacji, TERYT', jednostka='—',
    opis_co_widać='wykaz NIE zawiera wysokości anteny n.p.t./n.p.m. ani azymutów', url_źródła='https://bip.uke.gov.pl/pozwolenia-radiowe/wykaz-pozwolen-radiowych-tresci/stacje-gsm-umts-lte-5gnr-oraz-cdma,12,0.html (pliki xlsx „stan na 2026-10-26”)',
    licencja='informacja publiczna', autor='UKE', status='SOURCED', uwagi='Białystok w 4 plikach (LTE800, LTE1800, GSM900, 5G3600): 419 wierszy, 124 lokalizacje; sha256 plików w sources.md')


# ================= M67-FIX (r2): nowe wiersze K67-036+ (ID dotychczasowych 001–035 bez zmian) =================
ROOFNAME = {'skorupska17': 'Skorupska 17', 'dobra3': 'Dobra 3', 'zwierzyniecka4': 'Zwierzyniecka 4', 'hallera19': 'Hallera 19',
            'kopernika5a': 'Kopernika 5A / 7', 'wiezowiec_m57': 'wieżowiec M57 (kontrola)'}
for rk, v in LM.items():
    for u in v['urzadzenia']:
        add(kategoria='pomiar_lidar', element='%s — %s' % (ROOFNAME[rk], u['opis']), parametr='wysokość nad lokalnym dachem (szczyt − dach)',
            wartość=('≥ %.2f' % u['h']).replace('.', ','), jednostka='m', kierunek_deg='LIDAR (chmura punktów)',
            data_zdjęcia='2025-04-18 %s UTC (gps_time punktu szczytu)' % u['utc_szczytu'][11:19], sezon='wiosna', pora_dnia='przedpołudnie',
            opis_co_widać='Z_top %.2f, 2. punkt %.2f, Z_dachu %.2f m n.p.m. (PL-EVRF2007-NH); punktów w walcu %d, w tym > 1 m nad dachem %d; offset od punktu dachu dx %.2f / dy %.2f m (EPSG:2180)'
                          % (u['Z_top'], u['Z_top2'], u['Z_base'], u['n_pts_walec'], u['n_pts_powyzej_base_1m'], u['dx'], u['dy']),
            url_źródła=LIDAR_URL[rk], licencja='GUGiK — dane otwarte (bezpłatne, art. 40a Pgik)', autor='GUGiK',
            status='MEASURED (LIDAR)' if u.get('telecom') else 'MEASURED (LIDAR) — element nietelekom./kontrola',
            uwagi=METH + '; profil boczny: out/prof_%s_%s_zS.png / _zW.png (obejrzane)' % (rk, u['id']),
            plik='out/prof_%s_%s_zS.png' % (rk, u['id']),
            sha256_pliku=hashlib.sha256(open(os.path.join(HERE, 'out', 'prof_%s_%s_zS.png' % (rk, u['id'])), 'rb').read()).hexdigest())

# metoda cieni — kontrola krzyżowa (Zwierzyniecka 4)
add(kategoria='pomiar_cień', element='Zwierzyniecka 4 — maszt rurowy (kontrola metodą cieni)', parametr='wysokość nad dachem — dolna granica z cienia',
    wartość='> 5,6 (zgodne z LIDAR ≥ 8,55)', jednostka='m', kierunek_deg='nadir', data_zdjęcia='2025-04-18 (skorowidz WFS: arkusz N-34-107-C-b-3-1, 0,05 m); godzina z azymutu cienia',
    sezon='wiosna', pora_dnia='ok. 08:30 UTC (z azymutu cienia)',
    opis_co_widać='cień masztu i odciągów biegnie od podstawy (763,655 px) na NW, az. cienia ≈ 319° (Δ −83 / +95 px) → az. Słońca ≈ 139° → 08:30 UTC ± 20 min → elewacja 41,8° (± 1,5°) [tools/sun.py, NOAA]; '
                  'koniec cienia niewidoczny — wchodzi w cień podwyższonej części dachu po ≥ 126 px = 6,3 m; h ≥ 6,3 × tan 41,8° = 5,6 m',
    url_źródła='https://mapy.geoportal.gov.pl/wss/service/PZGIK/ORTO/WMS/HighResolution (files/shadow_zwierzyniecka4.jpg)', licencja='GUGiK — dane otwarte', autor='GUGiK',
    status='ESTIMATED (dolna granica)', uwagi='na Skorupskiej 17, Dobrej 3 i Kopernika cień masztu pada w cień własny budynku / dziedziniec — nieczytelny (obejrzane shadow_*.jpg); dlatego metoda główna = LIDAR',
    plik='files/shadow_zwierzyniecka4.jpg', sha256_pliku=sha('shadow_zwierzyniecka4.jpg'))

# nowe wycinki ortofoto (przecentrowane na położenie urządzeń z LIDAR, z uwzględnieniem przechyłu)
for img, opis in [('ortho_dobra_c', 'Dobra 3 — PRZECENTROWANY (45 m, 0,05 m/px): całe skrzydło NW; narożnik NW: maszty/wsporniki z anteną panelową i talerzami; węzeł skrzydeł: maszt kratowy z talerzem; koryto kablowe łączy oba z ramą z szafami; cień budynku w dziedzińcu NE'),
                  ('ortho_kopernika_s', 'Kopernika (blok płd.), 35 m: przy końcu W wsporniki z antenami przy attyce; w środku długości stos szarych szaf/urządzeń z wysięgnikiem; budynek przechylony — widać elewację S'),
                  ('ortho_kopernika_n', 'Kopernika (blok płn.), 35 m: przy końcu E ogrodzona platforma z szafami, maszty przy narożnikach platformy, koryta; budynek przechylony — widać elewację N'),
                  ('shadow_skorupska17', 'Skorupska 17 (50 m): rama X z masztem i panelami na szczycie, koryta do narożników NE i SW; cień budynku na NW — cień masztu w cieniu budynku (nieczytelny)'),
                  ('shadow_dobra3', 'Dobra 3 (50 m): maszt przy węźle skrzydeł; cień masztu w zacienionym dziedzińcu — nieczytelny'),
                  ('shadow_zwierzyniecka4', 'Zwierzyniecka 4 (50 m): maszt rurowy z 8 obciążnikami odciągów na podwyższonej części SE; cień masztu na NW (pomiar K67-059)'),
                  ('shadow_kopernika5a', 'Kopernika (50 m): urządzenia przy końcach bloków; cienie krótkie (2,5–3,4 m) przy attyce')]:
    add(kategoria='kadr', element='ortofoto dachu (rzut, 0,05 m/px)', parametr='obecność instalacji GSM', wartość='tak', jednostka='—', kierunek_deg='nadir',
        data_zdjęcia='2025-04-18 wg skorowidza (mozaika WMS — arkusz najnowszy; UNVERIFIED, że WMS pokazuje właśnie ten arkusz)', sezon='wiosna', pora_dnia='przedpołudnie (cienie na NW)',
        opis_co_widać=opis, url_źródła='GUGiK WMS ORTO HighResolution (tools/ortho_crop.py, tools/shadow_crops.py)', licencja='GUGiK — dane otwarte', autor='GUGiK',
        status='VERIFIED_WIZJA', uwagi='M67-FIX r2', plik='files/%s.jpg' % img, sha256_pliku=sha('%s.jpg' % img))

# mapy wysokości LIDAR (obejrzane)
for rk in ['skorupska17', 'dobra3', 'zwierzyniecka4', 'hallera19', 'kopernika5a', 'wiezowiec_m57']:
    add(kategoria='kadr', element='mapa wysokości nad dachem z LIDAR (70 m, 0,25 m/kom.)', parametr='skupiska > 1 m nad dachem', wartość='zob. out/lidar_roofs.json', jednostka='—',
        kierunek_deg='nadir (siatka EPSG:2180, zbieżność południków ≈ 3°)', data_zdjęcia='2025-04-18', sezon='wiosna', pora_dnia='przedpołudnie',
        opis_co_widać=ROOFNAME[rk] + ': mapa obejrzana; wybór urządzeń w masts_xy.json', url_źródła=LIDAR_URL[rk], licencja='GUGiK — dane otwarte', autor='GUGiK',
        status='VERIFIED_WIZJA', uwagi='tools/lidar_roofs.py', plik='out/lidar_%s.png' % rk,
        sha256_pliku=hashlib.sha256(open(os.path.join(HERE, 'out', 'lidar_%s.png' % rk), 'rb').read()).hexdigest())

# kadry naziemne Commons (pobrane z przerwami; log prób: out/commons_log.json)
CL = json.load(open(os.path.join(HERE, 'out', 'commons_log.json')))
COPIS = json.load(open(os.path.join(HERE, 'commons_opisy.json')))
seen = set()
for r in CL:
    if not r.get('plik') or r['title'] in seen:
        continue
    seen.add(r['title'])
    fn = os.path.basename(r['plik'])
    o = COPIS.get(fn, {})
    add(kategoria='kadr_naziemny', element=r['title'], parametr=o.get('parametr', 'sylwetka dachu na tle nieba'), wartość=o.get('wartość', ''), jednostka='—',
        lat=(r.get('gps') or [''])[0] or '', lon=(r.get('gps') or ['', ''])[1] or '', kierunek_deg=o.get('kierunek', 'UNVERIFIED'),
        data_zdjęcia=r.get('data_zdjecia', ''), sezon=o.get('sezon', ''), pora_dnia=o.get('pora', ''), opis_co_widać=o.get('opis', 'NIEOBEJRZANE'),
        url_źródła=r.get('page', ''), licencja=r.get('licencja', ''), autor=r.get('user', ''), status='VERIFIED_WIZJA' if o else 'UNVERIFIED',
        uwagi=o.get('uwagi', ''), plik='files/' + fn, sha256_pliku=sha(fn))
fails = sorted({r['title'] for r in CL if not r.get('plik')} - seen - {r['title'] for r in CL if r.get('note')})
other = sorted({'%s — %s' % (r['title'], r['note']) for r in CL if r.get('note')})
add(kategoria='luka', element='Commons — kadry niepobrane (HTTP 429)', parametr='tytuły', wartość='%d' % len(fails), jednostka='szt.',
    opis_co_widać='; '.join(fails) + ('. Inne: ' + '; '.join(other) if other else ''), url_źródła='https://commons.wikimedia.org/w/api.php', status='UNVERIFIED',
    uwagi='%d prób API w %s (przerwy ≥ 6 s, po 429 — 60 s), UA generyczny, bez obcych CDN; log: out/commons_log.json' % (len(CL), CL[0]['ts_utc'][:10] if CL else ''))

for i, r in enumerate(rows, 1):
    r['id'] = 'K67-%03d' % i
with open(os.path.join(HERE, 'manifest.csv'), 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=COLS)
    w.writeheader(); w.writerows(rows)
print(len(rows))
