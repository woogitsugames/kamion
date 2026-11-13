# P14 — źródła (wieżowiec Andersa 38, Białystok)

Data dostępu do wszystkich źródeł online: **2026-11-13** (chyba że zaznaczono inaczej).
Zakazane źródła (Google Maps / Street View / Earth / 3D Tiles) **nie były używane**.
Konwencja statusów jak w G10/P12: SOURCED (źródło potwierdza) / ESTIMATED (metoda jawnie podana) / UNVERIFIED (brak legalnego źródła).

## 1. OSM (ODbL)

| Element | Dane | URL |
|---|---|---|
| way/219260018 | „Biazet / Biazet S.A.", Andersa 38, building=office, building:levels=11, height=41, source:geometry=EGiB, source:building=BDOT; centroid 53.153231, 23.168022 | https://www.openstreetmap.org/way/219260018 |
| API | pełna geometria (14 wierzchołków; krawędzie pasują do ADR 0180: szczyty ~16 m, długie ściany ~37 m) | https://api.openstreetmap.org/api/0.6/way/219260018/full.json |
| Circle K (wiata) | way/236606116, building=roof, Circle K, 53.152585, 23.167858 — zasuwa parter szczytu SW z widoków z drogi | https://www.openstreetmap.org/way/236606116 |

## 2. GUGiK (dane otwarte; Prawo geodezyjne i kartograficzne art. 40a; komercyjne użycie OK)

| Zasób | Zawartość | URL / uwagi |
|---|---|---|
| BDOT10k + LoD1 2024 + LoD2 2017 (przez dane kafla bialystok-industrial-c w repo) | bdot:2BE4B431-CA0F-1BF0-E053-CC2BA8C0D140, 11 kondygnacji, „siedziba firmy lub firm", h LoD1 2024 = **41,81 m**, h LoD2 2017 = 41,52 m, teren 140,56 m EVRF2007, dach płaski (1130), powierzchnia 610,5 m² | Data/Regions/bialystok-industrial-c/buildings.geojson (gałąź main); atrybucja: Źródło danych: Główny Urząd Geodezji i Kartografii (www.geoportal.gov.pl) |
| Ortofotomapa HighResolution (WMS) | 3 kadry rzutu z góry: 320 m (0,40 m/px), 160 m (0,20 m/px), 80 m (0,10 m/px), środek na wieży, EPSG:2180 [778573,54; 595663,57] | https://mapy.geoportal.gov.pl/wss/service/PZGIK/ORTO/WMS/HighResolution (warstwa Raster); data nalotu: 2024 (arkusz 2024-05-27 wg manifestów repo; UNVERIFIED dla mozaiki WMS) |
| NMPT / NMPP (modele wysokości) | **UNVERIFIED — niedostępne**: wszystkie endpointy PZGIK (NMPT/NMPP GRID1 WMS/WCS) odpowiadają HTTP 401 (jak odnotowano już w P12) | np. https://mapy.geoportal.gov.pl/wss/service/PZGIK/NMPP/GRID1/WMS/ShadedRelief → 401 |

## 3. Wikimedia Commons

Nowe dla P14 (nie występują w docs/REFERENCES.md ani w zapytaniach, którymi budowany był artifacts/refs/kwadrat-park/INDEX.md — patrz README sekcja „Deduplikacja").

| Plik | Licencja | Autor | Data (EXIF) | URL | Rola w P14 |
|---|---|---|---|---|---|
| 20200711 073045 Generała Władysława Andersa 38, Białystok.jpg | CC BY 3.0 | Rakoon | 2020-07-11 07:30 | https://commons.wikimedia.org/wiki/File:20200711_073045_Genera%C5%82a_W%C5%82adys%C5%82awa_Andersa_38,_Bia%C5%82ystok.jpg | **szczyt SW + fragment ściany SE + dach z masztami** (zdjęcie tytułowane adresem wieży) |
| 20210328 105711 … Podlaskie Centrum Rolno–Towarowe (ul. Andersa).jpg | CC0 | Rakoon | 2021-03-28 10:57 | https://commons.wikimedia.org/wiki/File:20210328_105711_March_2021_in_Bia%C5%82ystok_Podlaskie_Centrum_Rolno%E2%80%93Towarowe_(ul._Andersa).jpg | **długa ściana od strony giełdy/parkingu, parter** |
| 20210328 115626 … (Andersa Street).jpg | CC0 | Rakoon | 2021-03-28 11:56 | https://commons.wikimedia.org/wiki/File:20210328_115626_March_2021_in_Bia%C5%82ystok_Podlaskie_Centrum_Rolno%E2%80%93Towarowe_(Andersa_Street).jpg | **długa ściana + dach z masztami** |
| 20200711 065632 Podlaskie Centrum Rolno–Towarowe, Andersa Street.jpg | CC BY 3.0 | Rakoon | 2020-07-11 06:56 | https://commons.wikimedia.org/wiki/File:20200711_065632_Podlaskie_Centrum_Rolno%E2%80%93Towarowe,_Andersa_Street.jpg | kontekst (wieży brak w kadrze) |
| 20200711 072453 Andersa Street in Białystok July 2020.jpg | CC BY 3.0 | Rakoon | 2020-07-11 07:24 | https://commons.wikimedia.org/wiki/File:20200711_072453_Andersa_Street_in_Bia%C5%82ystok_July_2020.jpg | kontekst (wieży brak w kadrze) |
| 20200711 073116 Andersa Street in Białystok July 2020.jpg | CC BY 3.0 | Rakoon | 2020-07-11 07:31 | https://commons.wikimedia.org/wiki/File:20200711_073116_Andersa_Street_in_Bia%C5%82ystok_July_2020.jpg | kontekst (wieży brak w kadrze) |
| 20201102 152417 Generala Andersa 38A Białystok.jpg | CC0 | Rakoon | 2020-11-02 15:24 | https://commons.wikimedia.org/wiki/File:20201102_152417_Generala_Andersa_38A_Bia%C5%82ystok.jpg | rozstrzygnięcie adresowe: 38A to NISKI budynek biurowy przy parkingu, nie wieża (wieży brak w kadrze) |
| 20201102 152422 38A Generala Andersa Street in Białystok.jpg | CC0 | Rakoon | 2020-11-02 15:24 | https://commons.wikimedia.org/wiki/File:20201102_152422_38A_Generala_Andersa_Street_in_Bia%C5%82ystok.jpg | j.w. |
| 20191211 Wojewoda podlaski … Andersa Białystok 001.jpg | CC BY 3.0 PL | Podlaski Urząd Wojewódzki w Białymstoku | 2019-12-11 12:33 | https://commons.wikimedia.org/wiki/File:20191211_Wojewoda_podlaski_na_otwarciu_nowej_hali_targowej_przy_ul._gen._W%C5%82adys%C5%82awa_Andersa_Bia%C5%82ystok_001.jpg | kontekst (wnętrze nowej hali giełdy; wieży brak) |
| 20191211 … 003.jpg | CC BY 3.0 PL | Podlaski Urząd Wojewódzki w Białymstoku | 2019-12-11 12:37 | https://commons.wikimedia.org/wiki/File:20191211_Wojewoda_podlaski_na_otwarciu_nowej_hali_targowej_przy_ul._gen._W%C5%82adys%C5%82awa_Andersa_Bia%C5%82ystok_003.jpg | kontekst (j.w.) |

Zdjęcia Commons już znane (z docs/REFERENCES.md oraz 5 zapytań, którymi generowany był artifacts/refs/kwadrat-park/INDEX.md; **nie dubluję ich w P14**): 20200711 065340 ENEA…, 20210425 100840…, 20210425 101130…, 20220725 124240…, 20240219 084626…, 7199 May 2021… (te 6 trafia na zapytania INDEX) oraz pliki z REFERENCES (7197, 7204, 20240626 103137, EC Białystok, Andersa, Maczka 1/2/3, Krzysztof Putra Roundabout, 20201102 152339, 20210904 101250, 20241222 122132).

## 4. KartaView (CC BY-SA 4.0)

Klatki pobrane w wariancie lth (1280×960, ≤1600 px). Pozycje/headingi z API (6 miejsc). Strona szczegółów sekwencji: https://kartaview.org/details/{sequence}/{index}/track-info.

| ID klatki | Sekwencja | Data | Pozycja kamery (WGS84) | Kierunek [°] | Odległość do wieży [m] | URL pliku |
|---|---|---|---|---|---|---|
| 7119873 | 14055 | 2016-08-24 | 53.151612, 23.167985 | 357,40 | 179 | https://storage2.openstreetcam.org/files/photo/2016/8/24/lth/14055_47b84_57bd4ca51c79d.jpg |
| 7119874 | 14055 | 2016-08-24 | 53.151429, 23.168448 | 359,44 | 201 | https://storage2.openstreetcam.org/files/photo/2016/8/24/lth/14055_7967e_57bd4ca5eaeec.jpg |
| 7119875 | 14055 | 2016-08-24 | 53.151241, 23.168926 | 357,86 | 228 | https://storage2.openstreetcam.org/files/photo/2016/8/24/lth/14055_e71d3_57bd4ca6d5e7a.jpg |
| 7119876 | 14055 | 2016-08-24 | 53.151048, 23.169423 | 357,78 | 259 | https://storage2.openstreetcam.org/files/photo/2016/8/24/lth/14055_ffff1_57bd4ca7cd49b.jpg |
| 7119872 | 14055 | 2016-08-24 | 53.151778, 23.167524 | 357,63 | 164 | https://storage2.openstreetcam.org/files/photo/2016/8/24/lth/14055_ff07a_57bd4ca432e35.jpg |
| 993062122 | 2769366 | 2019-08-25 | 53.151394, 23.168937 | 301,70 | 212 | https://storage13.openstreetcam.org/files/photo/2020/7/17/lth/2769366_79b96_5f11bae63918c.jpg |
| 1326673613 | 3686129 | 2021-06-23 | 53.151269, 23.169290 | 302,36 | 233 | https://storage13.openstreetcam.org/files/photo/2021/6/24/lth/3686129_2afed_60d4636fda994.jpg |

Sekwencja 14055 (2016): kamera skierowana na N (357°–359°), wieża 3–19° od osi kadru — szczyt SW frontalnie, ściana SE pod kątem. Sekwencje 2769366 (2019) i 3686129 (2021): kamera skierowana na NW (~302°), wieża 36–42° na prawo od osi (hFoV 70,4° dla seq. 3686129 — na granicy/na zewnątrz kadru).

## 5. UKE — wykaz pozwoleń radiowych dla stacji bazowych (BIP, źródło urzędowe)

Rejestr „Stacje GSM, UMTS, LTE, 5G/NR oraz CDMA", stan na **2026-02-25**:
https://bip.uke.gov.pl/pozwolenia-radiowe/wykaz-pozwolen-radiowych-tresci/stacje-gsm-umts-lte-5gnr-oraz-cdma,12,90.html

Wpisy dla lokalizacji **Białystok, gen. Władysława Andersa 38** (współrzędne rejestru 23°10'05" E, 53°09'12" N = 23,168056, 53,153333 — zgodne z centroidem wieży w granicach ~15 m):

| Operator | Nr decyzji | Rodzaj | Data ważności | IdStacji | Technologie (pliki rejestru) |
|---|---|---|---|---|---|
| P4 sp. z o.o. (Play) | MNET/4/2043/13/25 | zmP | 2033-12-31 | BIA1035 | gsm900, gsm1800, umts900, umts2100, lte800, lte900, lte1800, lte2100, lte2600, 5g2100, 5g2600, 5g3600 |
| T-Mobile Polska S.A. | MNET/11/96018/15/26 | zmP | 2032-03-31 | 24026 | gsm1800, umts2100, lte800, lte1800, lte2100, lte2600, 5g2100, 5g3600 |

Sąsiednie wpisy (nie na wieży): P4 „Generała Andersa 87, dz. nr 85/1" (53°09'27" N, 23°09'11" E ≈ 53,1575, 23,1531, IdStacji BIA1065, ważne do 2035-04-30) oraz T-Mobile „gen. Władysława Andersa 5, 553/27" (53°08'51" N, 23°10'38" E ≈ 53,1475, 23,1772, IdStacji 24039).

Wnioski: na dachu wieży działają **dwie instalacje radiowe** (Play + T-Mobile) — urzędowe potwierdzenie masztorów/anten na dachu. Rejestr **nie podaje** wysokości instalacji — wysokości masztów nad dachem: patrz manifest (ESTIMATED z proporcji do kondygnacji 3,69 m, skonfrontowane z UKE jako potwierdzeniem istnienia).

BIP miasta Białystok: wyszukiwanie „Andersa 38" w zasobach BIP nie dało dostępnego dokumentu pozwolenia/zgłoszenia dot. wieży (wyniki 404/niedostępne) — brak wpisu poza UKE.

## 6. Źródła sprawdzone negative / niedostępne

| Źródło | Wynik | Data |
|---|---|---|
| Panoramax (api.panoramax.xyz, bbox 23,140–23,190 × 53,143–53,172, limit 500) | **0 klatek w promieniu 800 m od wieży**; najbliższe ~1,2 km (stanton, 2019-08/09, CC BY-SA 4.0) — bezużyteczne dla ścian | 2026-11-13 |
| Openverse (api.openverse.org) | zapytania „Białystok Andersa" / „Kwadrat Park" / „Biazet": 0 wyników (część zapytań przerwała się 504 — jak w P12/dusk-sodium) | 2026-11-13 |
| KartaView — reszta okolicy | sekwencje 14055/2769366/3686129 wzdłuż Andersa (91 klatek w promieniu 500 m od punktów kontrolnych); brak nagrań od N/NE/E (teren prywatny giełdy i parkingu) | 2026-11-13 |
| Commons geosearch (gsradius 800/2500 wokół wieży) | 0 geotagowanych zdjęć w promieniu ~2,3 km — zdjęcia Commons znajdowano tylko zapytaniami tekstowymi | 2026-11-13 |
| Mapillary | brak tokenu w narzędziach badania → zgodnie z zasadą: UNVERIFIED; para richlv 177786140912399 / 178689077481862 (2020-08-15, CC BY-SA 4.0) jest już udokumentowana w ADR 0180 i docs/LICENSES.md — nie dubluję | 2026-11-13 |
