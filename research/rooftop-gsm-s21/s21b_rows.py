"""Uzupełnienie s21b (K67-083+): kadry naziemne KartaView/Panoramax/Commons i pomiary proporcją do kondygnacji.
Importowane przez build_manifest.py (wiersze dopisywane PO K67-082, numeracja ciągła). Opisy = tylko to, co widać w obejrzanych kadrach
(pełny kadr ≤ 960 px + wycinek 3–5×). Kierunek = kurs z toru GPS sekwencji (geograficzny), zgodny z polem heading API KartaView
(sprawdzone dla każdego kadru: tools/s21b/track.py); wyjątek opisano w wierszu."""

KV_LIC = 'CC BY-SA 4.0 (warunki KartaView) — referencja, nie tekstura'
KV_API = 'https://api.kartaview.org/2.0/photo/?sequenceId=%s (pole fileurlProc)'
BIAZET = 'wieżowiec M57 (Andersa 38; lokalizacja wg M57, tu nie powtarzam)'

KV = [
    # (plik, photo_id, seq, user, lat, lon, kurs, brg_do_celu, odl_m, czas, cel, przypisany, parametr, wartość, opis, status, uwagi, wycinki)
    ('kv_1326673605.jpg', '1326673605', '3686129', '479', '53.151072', '23.169827', 301.5, 333, 267, '2021-06-23 10:34:19', BIAZET, True,
     'sylwetka instalacji na tle nieba', '2 wysokie maszty kratowe + ok. 8 krótszych masztów/wsporników',
     'Ostatnie 3 kondygnacje wieży (żółty tynk, poziome pasma okien w białych ramach) ponad koronami drzew, po prawej stronie estakady. '
     'Na dachu na tle jasnoniebieskiego nieba i cumulusa: (1) wysoki maszt kratowy przy lewym końcu (szczyt SW/narożnik W) — ciemnoszara krata, '
     'na nim 2–3 białe czasze radiolinii po lewej stronie i skośne odciągi do dachu; (2) najwyższy maszt kratowy w środku długości — krata szara, '
     'w górnej ok. 1/3 pionowe panele, u podstawy rozchodzące się zastrzały/odciągi; (3) między nimi 3 krótkie wsporniki rurowe z białymi panelami '
     '(po 1–2 panele) ok. 0,5–1 kondygnacji nad attyką; (4) po prawej 4–5 krótszych masztów kratowych/rurowych z panelami i białymi czaszami '
     '(ok. 1–1,5 kondygnacji); (5) na narożniku przy szczycie: białe panele przymocowane do elewacji, wystające ponad attykę; na samym szczycie SW '
     'po lewej szare skrzynki/panele na wysięgnikach. Kolory: panele białe/jasnoszare matowe (bez połysku), czasze białe, kraty masztów '
     'szare — pod światło ciemnoszare. Mocowanie: maszty stoją na dachu (podstawa za attyką niewidoczna), duży maszt W z odciągami.',
     'VERIFIED_WIZJA', 'najlepszy kadr; pomiary proporcją K67-094…096; obejrzany pełny kadr i wycinek 3× i 5× (files/kv_1326673605_wyc3x.jpg, _pomiar.jpg)',
     ['kv_1326673605_wyc3x.jpg', 'kv_1326673605_pomiar.jpg']),
    ('kv_1326673581.jpg', '1326673581', '3686129', '479', '53.150468', '23.171384', 303.1, 324, 379, '2021-06-23 10:34:13', BIAZET, True,
     'sylwetka instalacji na tle nieba', 'jw. — 2 wysokie maszty + krótkie', 'Ta sama jazda, 6 s wcześniej: wieża mała, przy prawej części kadru nad drzewami (ok. 70 px szer. w 960). '
     'W wycinku 5×: lewy maszt kratowy z 2 białymi czaszami, wyższy maszt środkowy z panelami w górnej części, 3 wsporniki z białymi panelami '
     'między nimi, po prawej krótkie maszty z czaszami. Z tej odległości panele czytelne jako białe prostokąty, czasze jako białe kropki, '
     'kraty jako szare kreski grubości 2–4 px (z 4000).', 'VERIFIED_WIZJA', 'drugi odczyt pomiarów K67-094…095 (files/kv_1326673581_pomiar.jpg)', ['kv_1326673581_pomiar.jpg']),
    ('kv_993062010.jpg', '993062010', '2769366', '37458', '53.151179', '23.169503', 302.4, 336, 248, '2019-08-25 11:51:00', BIAZET, True,
     'sylwetka instalacji na tle nieba', '2 wysokie maszty + 3 grupy paneli + 6–8 czasz', 'Kamera szerokokątna (wypukła perspektywa), wieża przy prawej krawędzi za barierą estakady, '
     'czyste niebo. Wycinek 3×: lewy maszt kratowy z 2–3 białymi czaszami; najwyższy maszt środkowy z białymi panelami w górnej części i zastrzałami u podstawy; '
     'między nimi 3 grupy białych paneli na krótkich wspornikach (po 1–2 panele); po prawej 4 krótkie maszty z białymi czaszami (ok. 6–8 czasz łącznie) '
     'i panelami; na narożniku elewacji szczytu białe panele na ścianie (2 + 2) sięgające attyki. Kolory jak w 2021: panele białe matowe, '
     'krata szara. Dolne kondygnacje zasłonięte barierą i drzewami.', 'VERIFIED_WIZJA', 'stan 2019 zgodny z 2021 (te same dwa wysokie maszty)', ['kv_993062010_wyc3x.jpg']),
    ('kv_993061738.jpg', '993061738', '2769366', '37458', '53.150740', '23.170647', 302.7, 328, 326, '2019-08-25 11:50:56', BIAZET, True,
     'sylwetka z ~330 m przez korony drzew', 'czasze i maszty widoczne fragmentarycznie', 'Wieża za koronami drzew po prawej. W wycinku 4×: nad attyką białe czasze '
     '(5–6 białych kropek) i cienkie szare kreski masztów; oba wysokie maszty zasłonięte liśćmi. Wniosek dla gry: z ~300 m przy zasłonie drzew '
     'najbardziej widoczne są białe czasze i panele, kraty prawie znikają.', 'VERIFIED_WIZJA', 'kadr słabszy; tylko do opisu czytelności z dystansu', ['kv_993061738_wyc4x.jpg']),
    ('kv_1326673557.jpg', '1326673557', '3686129', '479', '53.149926', '23.172925', 298.6, 319, 491, '2021-06-23 10:34:07', BIAZET, False,
     'sylwetka', 'cel niewidoczny', 'Estakada, akumulator ciepła po lewej, drzewa po prawej; wieży w kadrze nie widać (zasłonięta drzewami).', 'VERIFIED_WIZJA', 'negatyw — nieprzypisany', []),
    ('kv_993061478.jpg', '993061478', '2769366', '37458', '53.150303', '23.171806', 302.2, 322, 411, '2019-08-25 11:50:52', BIAZET, False,
     'sylwetka', 'cel niewidoczny', 'Estakada pod bramownicą drogowskazów, drzewa po prawej; wieży w kadrze nie widać.', 'VERIFIED_WIZJA', 'negatyw — nieprzypisany', []),
    ('kv_1326672625.jpg', '1326672625', '3686129', '479', '53.125862', '23.185140', 337.8, 343, 937, '2021-06-23 10:27:41', 'Skorupska 17', False,
     'sylwetka', 'cel niewidoczny', 'Rondo przy pawilonach handlowych; na wprost niskie budynki usługowe i słup linii WN. Budynku przy Skorupskiej 17 (937 m) nie widać — zasłonięty.',
     'VERIFIED_WIZJA', 'negatyw — nieprzypisany; napisy firmowe w kadrze, nie odtwarzamy', []),
    ('kv_1326672621.jpg', '1326672621', '3686129', '479', '53.125782', '23.185201', 335.4, 342, 947, '2021-06-23 10:27:38', 'Skorupska 17', False,
     'sylwetka', 'cel niewidoczny', 'To samo rondo 3 s wcześniej: pawilony, słup WN, drzewa; celu brak.', 'VERIFIED_WIZJA', 'negatyw — nieprzypisany; napisy firmowe, nie odtwarzamy', []),
    ('kv_2634225507.jpg', '2634225507', '11712048', '—', '53.152543', '23.119834', 46.6, 74, 384, '2026-10-04 09:24:01', 'Hallera 19', False,
     'sylwetka', 'cel niewidoczny', 'Chodnik osiedlowy; po obu stronach bloki 5 kond. (żółte/zielone balkony) zasłaniają widok w kierunku Hallera 19 (cel 27° w prawo od osi).',
     'VERIFIED_WIZJA', 'negatyw — nieprzypisany', []),
    ('kv_2634225487.jpg', '2634225487', '11712048', '—', '53.151794', '23.118482', 62.2, 67, 497, '2026-10-04 09:23:06', 'Hallera 19', False,
     'sylwetka', 'cel niewidoczny', 'Kamera skierowana w dół na przejście dla pieszych; nieba i dachów prawie brak w kadrze.', 'VERIFIED_WIZJA', 'negatyw — nieprzypisany', []),
    ('kv_5062497.jpg', '5062497', '10733', '—', '53.159093', '23.129905', None, None, 686, '2016-07-19 12:02:56', 'Hallera 19', False,
     'sylwetka', 'cel niewidoczny', 'Dwujezdniowa droga między ekranami akustycznymi, znak ograniczenia 70; za ekranami drzewa i domy jednorodzinne; bloku przy Hallera 19 nie widać.',
     'VERIFIED_WIZJA', 'negatyw; heading API 214° NIEZGODNY z torem (89°) — kierunek UNVERIFIED', []),
]

# pomiary proporcją do kondygnacji (kadry 2021, oba z jazdy na NW estakadą)
H_STORY = '3,5–3,8 m (41,8 m / 11 kond. = 3,8 m wg MISTRAL-TASKS-10 §M67 i M57; dolna granica 3,5 m — typowa kondygnacja biurowa, WORKING_VALUE)'
POM = [
    ('maszt kratowy środkowy (najwyższy)', '9,7–11,0',
     'kv_1326673605: szczyt y=1050, attyka y=1178 → 128 px; podziałka kondygnacji (góra pasma okien) 1200→1246 = 46 px → 2,78 kond.; '
     'kv_1326673581: 1201→1288 = 87 px / 30 px = 2,90 kond.; 2,78–2,90 × 3,5–3,8 m',
     'nad attyką (podstawa za attyką niewidoczna → do dachu +0,5–1,5 m, UNVERIFIED). Zgodne z M57-FIX (9–12 m). KONFLIKT z LIDAR 2025-04-18: przy środku krawędzi SE '
     'tylko 5,25 m (K67-054) — możliwy demontaż/obniżenie po 2021 albo inny punkt; NIE rozstrzygam'),
    ('maszt kratowy przy końcu W (z czaszami, odciągi)', '8,4–9,5',
     'kv_1326673605: szczyt y=1077, attyka szczytu SW y=1188 → 111 px / 46 = 2,41 kond.; kv_1326673581: 1215→1290 = 75 px / 30 = 2,50 kond.; 2,41–2,50 × 3,5–3,8 m',
     'nad attyką; LIDAR 2025 ≥ 10,95 m nad dachem (K67-053) — różnica 1,5–2,5 m mieści się w zasłoniętej podstawie + skrócie perspektywy (maszt dalej od kamery niż elewacja SE)'),
    ('krótkie maszty kratowe/rurowe przy końcu NE (2 najwyższe z 4–5)', '4,4–5,1',
     'kv_1326673605: szczyty y=1117 i 1120, attyka y=1178 → 58–61 px / 46 = 1,26–1,33 kond. × 3,5–3,8 m',
     'nad attyką; zgodne z LIDAR 2025 4,55–5,35 m (K67-055…058)'),
]

EXTRA = [
    dict(kategoria='luka', element='Panoramax — pokrycie wokół dachów', parametr='zdjęcia w bbox ±0,006° lat / ±0,010° lon', wartość='0 / 0 / 0 / 29 / 1 / 0', jednostka='szt.',
         opis_co_widać='Skorupska 17 / Dobra 3 / Zwierzyniecka 4 / Hallera 19 / Kopernika 5A / wieżowiec. Hallera: 29 zdjęć z 2019-08/09 w 630–670 m, wszystkie skierowane bokiem (cel 68–99° od osi) — nieprzydatne. '
                       'Kopernika: 1 zdjęcie 2026-06-29 (771 m, cel −11° od osi) — obejrzane: wnętrze lokalu gastronomicznego, nie ulica; nie pobrano do files/.',
         url_źródła='https://api.panoramax.xyz/api/search?bbox=… (tools/s21b/pnx.py); zdjęcie Kopernika: https://api.panoramax.xyz/api/collections/a7cf963f-8d1c-4bac-9717-e3149f5f9fff/items/4d84fb34-70b1-4921-b941-bd84697dd8da',
         licencja='CC BY-SA 4.0', status='UNVERIFIED', uwagi='zapytanie 2026-11-15 ok. 14:06 UTC'),
    dict(kategoria='luka', element='KartaView — pokrycie wokół dachów', parametr='zdjęcia skierowane na cel (|Δ| < 35°)',
         wartość='Zwierzyniecka 4: 0 (< 1600 m); Kopernika 5A: 0 (< 1600 m); Dobra 3: tylko ≥ 1295 m; Skorupska 17: ≥ 885 m (2 obejrzane, cel zasłonięty); Hallera 19: 79 (< 900 m; 3 obejrzane, cel zasłonięty); wieżowiec: 41 (< 900 m; 6 obejrzanych, 4 przypisane)', jednostka='—',
         opis_co_widać='Przeszukano 15 sekwencji z Białegostoku (ok. 30 tys. zdjęć: siatka 9 zapytań /photo/?lat&lng&radius=500 na dach + pełne listy sekwencji). Kierunek z toru GPS (sprawdzony z heading API).',
         url_źródła='https://api.kartaview.org/2.0/photo/ (tools/s21b/kvgrid.py, kvseq.py, kvnear.py, kvpick.py)', licencja='CC BY-SA 4.0', status='UNVERIFIED',
         uwagi='sekwencja 2016 (photo 7119871…7119881) — pliki proc HTTP 404, nieobejrzane'),
    dict(kategoria='luka', element='Commons — kadry dachów z masztami (s21b)', parametr='obejrzane / przypisane', wartość='48 / 0', jednostka='szt.',
         opis_co_widać='Geosearch 600 m (Skorupska 17, Dobra 3 — po 17 najbliższych) + tytuły z Openverse (Zwierzyniecka, Kopernika, Hallera, Skorupska, Dobra). Geosearch dla Zwierzynieckiej 4, Hallera 19, Kopernika 5A i wieżowca: HTTP 429 przez ok. 40 min (log out/commons_s21b_log.json). '
                       'Żaden kadr nie pokazuje dachu celu z instalacją; 3 kandydaty z identyfikacją UNVERIFIED (akademiki z Kopernika 7ecfa0059e, wieżowiec przy Hallera ec5a9b577e, elewacja biurowca 4425e8c956).',
         url_źródła='https://commons.wikimedia.org/w/api.php (list=geosearch, prop=imageinfo|coordinates)', status='UNVERIFIED',
         uwagi='pauzy ≥ 5 s, po 429 backoff 120/240/480/600 s, UA generyczny, tylko domeny Wikimedia; miniatury przez thumburl z API'),
    dict(kategoria='dach', element='Zwierzyniecka 4 — rodzaj masztu wg OSM', parametr='tagi node 11285970200', wartość='man_made=mast, tower:construction=guyed_tube, communication:radio=yes', jednostka='—',
         lat='53.119647', lon='23.149357', osm_id='node/11285970200; way/284157362 (building=dormitory, building:levels=11, height=34)',
         opis_co_widać='Maszt na odciągach jest w OSM opisany jako RADIOWY (communication:radio, odsyłacz do wykazu obiektów nadawczych), bez communication:mobile_phone; w budynku OSM ma też studio radia akademickiego. '
                       'Wniosek: na Zwierzynieckiej 4 to najpewniej maszt nadawczy UKF, nie stacja GSM — w README dach liczony w rozkładzie „maszt dachowy”, ale NIE jako stacja GSM (operatorzy UKE: brak).',
         url_źródła='https://api.openstreetmap.org/api/0.6/map?bbox=23.1488,53.1192,23.1500,53.1200 (pobrane 2026-11-15)', licencja='ODbL', autor='współtwórcy OSM', status='SOURCED (OSM)',
         uwagi='height=34 i building:levels=11 → 3,1 m/kond. (OSM, UNVERIFIED wobec LIDAR: dach 35,2 m npt)'),
]
