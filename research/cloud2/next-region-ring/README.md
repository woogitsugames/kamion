# R9 — next-region-ring: dostępność otwartych danych dla obrzeży Białegostoku (S8 / S19 / DK8 / DK19 / DK65)

**Data:** 2026-11-14 · **Gałąź:** `research/cloud2-next-region-ring` · **Wierszy manifestu:** 371 (WORKING_VALUE 2, ESTIMATED 244, SOURCED 119, UNVERIFIED 6) · **Obejrzanych kadrów:** 38 (32 Panoramax + 6 KartaView; PX31 = duplikat PX26) · **Samokontrola:** 75 wierszy (seed 20261114): {'PASS': 74, 'FAIL': 1} — 1 FAIL poprawiony (opis PX20).

> Raport planistyczny, **propozycja — nie decyzja**. Praca przerwana na polecenie lidera (limit sesji): sekcja „Luki” wymienia, czego nie zebrano.

## 1. Cel i metoda
Sprawdzić, czy dla pierścienia dróg wokół Białegostoku są otwarte dane potrzebne pipeline'owi `tools/worldgen` (OSM, NMT 1 m, ortofoto, BDOT10k, LoD1/LoD2 — te same warstwy co w `Data/Regions/*/region.yaml`) oraz zdjęcia referencyjne do pętli visual-QA.
- OSM: Overpass, mirror `maps.mail.ru` (overpass-api.de, kumi, private.coffee niedostępne przez proxy sesji; pełny tekst zapytań, czas UTC i `timestamp_osm_base` w `overpass/_log.jsonl` i `sources.md`). Wyniki przycięte do bboxu w EPSG:2180 (`tools/osm_analyze.py`, `tools/summaries.py`).
- GUGiK: WFS skorowidzów ORTO/NMT/NMPT 2018–2026 (27 zapytań, wszystkie HTTP 200), WMS GetFeatureInfo BDOT10k i ModeleBudynkow3D, WFS PRG, HEAD plików na opendata.geoportal.gov.pl.
- Zdjęcia: Panoramax `/api/search`, KartaView `/2.0/photo` (161 punktów co 600 m wzdłuż korytarzy), Commons `geosearch` (częściowo — 429). Mapillary pominięto (brak tokenu).
- Każda liczba w manifeście pochodzi z pliku wygenerowanego skryptem (`tools/build_manifest.py`), nie z pamięci.

## 2. Ustalenia o sieci (ważne: „ring S8” nie istnieje w OSM)
- **S8 kończy się na węźle Białystok Zachód** (lon ≈ 23.031). Dalej na wschód biegnie DK8 jako `highway=trunk` ref `8;65` (ul. Gen. Kleeberga / Gen. Maczka — „Trasa Generalska”), potem `8;19` na północ (al. Tysiąclecia PP → Jurowce → Białystok Północ).
- **S19** od węzła Białystok Zachód na północ jest w OSM jako `motorway` ref `S19;65` (9.63 km w bboxie, liczone po obu jezdniach); dalszy ciąg `construction=motorway`, część południowa `proposed=motorway`.
- Węzły `Porosły`, `Księżyno`, `Dojlidy` z treści zadania **nie występują** jako `motorway_junction`. W bboxie jest 11 węzłów (5 nazw):

| Nazwa w OSM | Tag nazwy | ref | OSM node | lat, lon |
|---|---|---|---|---|
| Choroszcz | name | unsigned_ref=92 | node 1940503816 | 53.160046, 22.993638 |
| Choroszcz | name | unsigned_ref=92 | node 1908957192 | 53.158669, 23.001879 |
| Białystok Zachód | name | unsigned_ref=93 | node 3160890725 | 53.156056, 23.016674 |
| Białystok Zachód | name | 10 | node 4236127140 | 53.159227, 23.025540 |
| Białystok Zachód | name | unsigned_ref=93 | node 2081020070 | 53.153653, 23.030749 |
| Białystok Północ (proposed:name) | jak w nawiasie | proposed:ref=7 | node 1154993008 | 53.217839, 23.154995 |
| Jurowce (loc_name) | jak w nawiasie | brak ref | node 1154984451 | 53.196757, 23.155501 |
| Jurowce (loc_name) | jak w nawiasie | brak ref | node 1838303448 | 53.197718, 23.155756 |
| Białystok Północ (proposed:name) | jak w nawiasie | proposed:ref=7 | node 1838303608 | 53.218690, 23.159635 |
| Wasilków (proposed:name) | jak w nawiasie | proposed:ref=6 | node 1166095461 | 53.220518, 23.214169 |
| Wasilków (proposed:name) | jak w nawiasie | proposed:ref=6 | node 2183661977 | 53.222370, 23.218069 |

Jedyny węzeł z tagiem `ref` to Białystok Zachód (`ref=10`); pozostałe mają `unsigned_ref` (92, 93) albo tylko `proposed:name`/`loc_name` — **nazwy „Białystok Północ”, „Wasilków”, „Jurowce” nie są potwierdzone tagiem `name`** (UNVERIFIED jako nazwy oficjalne).

## 3. Proponowany obszar
| | wartość |
|---|---|
| bbox EPSG:2180 (xmin, ymin, xmax, ymax) | 764683, 584959, 787211, 605439 |
| narożniki WGS84 (lat, lon) | SW 53.064290,22.951921 · SE 53.052659,23.287293 · NE 53.236295,23.305653 · NW 53.248004,22.968855 |
| rozmiar | 22 528 × 20 480 m = 461.4 km² = 11 × 10 kafli 2048 m |
| siatka | zgodna z `bialystok-industrial-c` (origin 776971, 595199) — kafel istniejącego regionu jest kaflem tej siatki |
| powiaty | 2061 Białystok 22.2 % · **2002 białostocki** 77.8 % |
| gminy (PRG, wersja 2026-11-03) | Białystok 22.2 %, Wasilków 17.7 %, Dobrzyniewo Duże 16.3 %, Choroszcz 15.9 %, Juchnowiec Kościelny 6.8 %, Turośń Kościelna 5.6 %, Supraśl 5.5 %, Grabówka 5.4 %, Zabłudów 4.5 % |

**Uwaga do zadania:** powiat białostocki ma TERYT **2002**, nie 2010 (GetFeatureInfo BDOT10k: „Powiat białostocki” → `2002_GPKG.zip`; PRG `JPT_KOD_JE=2002…`). 2010 to inny powiat — paczka `2010_GPKG.zip` istnieje, ale nie dotyczy tego obszaru.
Bbox to obwiednia planistyczna; do budowy wystarczy korytarz — osie motorway/trunk/primary przecinają 161 komórek 600 m (ok. 58 km²).

## 4. OSM — drogi główne (klasy niższe: LUKA, patrz §9)
Długość w km (jezdnie rozdzielone liczone osobno) i pokrycie tagów w % długości:

| klasa | km | lanes | maxspeed | surface | width | turn:lanes | destination | lit | oneway | layer | bridge |
|---|---|---|---|---|---|---|---|---|---|---|---|
| motorway | 19.25 | 100.0 | 100.0 | 100.0 | 0.0 | 11.4 | 1.9 | 0.0 | 99.1 | 3.3 | 3.3 |
| motorway_link | 4.56 | 100.0 | 90.4 | 64.0 | 0.0 | 21.3 | 58.1 | 0.0 | 100.0 | 2.8 | 2.8 |
| trunk | 80.79 | 96.3 | 95.8 | 96.6 | 0.2 | 26.4 | 7.8 | 16.8 | 83.3 | 7.0 | 4.4 |
| trunk_link | 15.28 | 90.2 | 46.6 | 88.3 | 0.0 | 29.2 | 55.7 | 4.6 | 93.8 | 1.1 | 1.1 |
| primary | 39.05 | 99.8 | 90.4 | 97.9 | 0.0 | 17.9 | 12.8 | 44.8 | 87.6 | 5.2 | 0.8 |
| primary_link | 8.14 | 58.9 | 20.2 | 98.3 | 0.0 | 4.9 | 73.0 | 74.6 | 99.6 | 0.6 | 0.6 |

`layer`/`bridge` to udział odcinków na obiektach, nie miara kompletności. W budowie/proponowane: construction:motorway 27.81 km, proposed:motorway 19.51 km, construction:motorway_link 4.8 km, proposed:primary 11.08 km.
Wnioski dla generatora: `lanes`, `maxspeed`, `surface` praktycznie kompletne na motorway/trunk/primary; **`width` ≈ 0 %** (szerokość z przepisów/ortofoto, jak dotąd); `turn:lanes` 11–29 %, `destination` na łącznicach 56–73 %, na jezdniach głównych 2–13 %; `lit` 0 % na S8/S19 i 17 % na trunk — oświetlenie trzeba wyprowadzać z `highway=street_lamp` (1891 w bboxie) i ortofoto.

### Obiekty
| obiekt | liczba / długość |
|---|---|
| man_made=bridge (obrysy obiektów): liczba way | 85 szt. — łączna długość 8.49 km (jezdnie osobno) |
| tunnel pozostałe (przejścia, przepusty drogowe, service): liczba way | 459 szt. — łączna długość 7.33 km (jezdnie osobno) |
| bridge pieszo-rowerowe: liczba way | 272 szt. — łączna długość 7.14 km (jezdnie osobno) |
| bridge na primary/secondary/tertiary: liczba way | 90 szt. — łączna długość 3.96 km (jezdnie osobno) |
| bridge na trunk(+link): liczba way | 51 szt. — łączna długość 3.71 km (jezdnie osobno) |
| bridge na drogach niższych klas: liczba way | 116 szt. — łączna długość 1.71 km (jezdnie osobno) |
| tunnel na trunk/primary/secondary/tertiary: liczba way | 16 szt. — łączna długość 1.31 km (jezdnie osobno) |
| bridge w budowie/proponowane: liczba way | 18 szt. — łączna długość 0.98 km (jezdnie osobno) |
| bridge na motorway(+link): liczba way | 18 szt. — łączna długość 0.76 km (jezdnie osobno) |
| bridge kolejowe (rail + nieczynne): liczba way | 26 szt. — łączna długość 0.61 km (jezdnie osobno) |
| Mosty/wiadukty z nazwą (name lub bridge:name na way z bridge na motorway/trunk/primary) | 0 szt. — name na tych way to nazwa ulicy, nie obiektu |
| barrier=wall: długość | 39.46 km — 530 way |
| barrier=wall + wall=noise_barrier: długość | 27.82 km — 176 way |
| barrier=guard_rail: długość | 23.85 km — 87 way |
| barrier=wall (inne wall=*): długość | 0.1 km — 11 way |
| barrier=cable_barrier: długość | 0.04 km — 2 way |
| barrier=noise_barrier: długość | 0.0 km — 0 way |
| Ekrany (wall=noise_barrier) z tagiem height | 0.0 % — 0/176 way |
| Ekrany (wall=noise_barrier) z tagiem material | 0.0 % — 0/176 way |
| Ekrany (wall=noise_barrier) z tagiem colour | 0.0 % — 0/176 way |
| highway=services (MOP z usługami) | 0 szt. |
| highway=rest_area | 5 szt. — wszystkie nazwane to MOR-y rowerowe (operator=Green Velo), nie MOP-y drogowe |
| amenity=fuel | 63 szt. — w tym fuel:HGV_diesel=yes: 14 |
| amenity=parking z hgv=yes/designated/only | 1 szt. |
| highway=toll_gantry | 2 szt. |
| amenity=weighbridge | 0 szt. |
| highway=traffic_signals (węzły/way) | 507 szt. |
| highway=street_lamp (węzły/way) | 1891 szt. |
| traffic_sign=* (węzły/way) | 346 szt. |
| highway=milestone (węzły/way) | 89 szt. |
| highway=speed_camera (węzły/way) | 3 szt. |
| man_made=gantry (węzły/way) | 3 szt. |

- Ekrany akustyczne są tagowane `barrier=wall` + `wall=noise_barrier`, **nie** `barrier=noise_barrier` (0 obiektów) — zapytanie z treści zadania dałoby zero.
- **MOP-ów drogowych w bboxie nie ma**: 0 × `highway=services`; nazwane `rest_area` to MOR-y rowerowe.
- Żaden most na motorway/trunk/primary nie ma `bridge:name`.

## 5. GUGiK
| produkt | stan dla bboxu | źródło |
|---|---|---|
| Ortofoto RGB, najnowsza mozaika | 100 % pokrycia; {'2024|0.25': 1.8, '2025|0.05': 35.2, '2025|0.1': 63.0} (rok\|piksel m → % pow.); daty 2024-05-27..2025-05-27 | WFS `ORTO/WFS/Skorowidze` |
| Ortofoto 0,05 m | tylko 36.7 % bboxu (miasto: 2025-04-18; także 2021, 2023; 1:1000 z 2022 i 2024) | j.w. |
| Ortofoto 0,25 m RGB (obecnie używane w pipeline) | 100 % z 2024 (118 arkuszy, 4,7 GB), także 2022 i 2020 | j.w. |
| NMT 1 m (ARC/INFO ASCII GRID, PL-EVRF2007-NH) | 100 %; {'2022|1.00 m': 0.9, '2024|1.00 m': 0.9, '2025|1.00 m': 98.2} | WFS `NumerycznyModelTerenuEVRF2007` |
| NMPT | 98.2 %; {'2025|0.50 m': 35.2, '2025|1.00 m': 63.0} (0,5 m tylko miasto) | WFS `NumerycznyModelPokryciaTerenuEVRF2007` |
| BDOT10k powiat 2061 (Białystok) — paczka GPKG: data modyfikacji pliku | Sat, 03 Oct 2026 00:50:00 GMT Last-Modified | WMS GetFeatureInfo (warstwa Powiaty) → link; HEAD pliku |
| Modele 3D budynków LoD1 2024, powiat 2061 (Białystok) — liczba budynków | 36971 szt. | WMS GetFeatureInfo warstwa Modele_3D_budynkow_LoD1_2024 |
| Modele 3D budynków LoD1 2022, powiat 2061 (Białystok) — liczba budynków | 35840 szt. | WMS GetFeatureInfo warstwa Modele_3D_budynkow_LoD1_2022 |
| Modele 3D budynków LoD2 2017, powiat 2061 (Białystok) — liczba budynków | 30628 szt. | WMS GetFeatureInfo warstwa Modele_3D_budynkow_LoD2_2017 |
| Modele 3D budynków LoD1 2025, powiat 2061 — dostępność pod wzorcem URL | 404 Not Found kod HTTP | HEAD (wzorzec URL z LoD1 2024 z podmienionym rokiem) |
| BDOT10k powiat 2002 (białostocki) — paczka GPKG: data modyfikacji pliku | Sat, 03 Oct 2026 00:52:51 GMT Last-Modified | WMS GetFeatureInfo (warstwa Powiaty) → link; HEAD pliku |
| Modele 3D budynków LoD1 2024, powiat 2002 (białostocki) — liczba budynków | 96708 szt. | WMS GetFeatureInfo warstwa Modele_3D_budynkow_LoD1_2024 |
| Modele 3D budynków LoD1 2022, powiat 2002 (białostocki) — liczba budynków | 95243 szt. | WMS GetFeatureInfo warstwa Modele_3D_budynkow_LoD1_2022 |
| Modele 3D budynków LoD2 2017, powiat 2002 (białostocki) — liczba budynków | 72351 szt. | WMS GetFeatureInfo warstwa Modele_3D_budynkow_LoD2_2017 |
| Modele 3D budynków LoD1 2025, powiat 2002 — dostępność pod wzorcem URL | 404 Not Found kod HTTP | HEAD (wzorzec URL z LoD1 2024 z podmienionym rokiem) |

Skorowidze 2026 (ORTO/NMT/NMPT) i 2018: 0 arkuszy w bboxie. Pełne zestawienie rocznik × rozdzielczość: `gugik/skorowidze_coverage.json`; lista arkuszy rekomendowanych mozaik z URL: `gugik/skorowidze_sheets_recommended.csv`.

### Szacunek rozmiaru pobrania (ESTIMATED)
| zestaw | rozmiar |
|---|---|
| Mozaika ORTO_RGB_najnowsza: suma rozmiarów plików | 56.9 GB |
| Mozaika ORTO_RGB_najnowsza_piksel<=0.10: suma rozmiarów plików | 57.1 GB |
| Mozaika ORTO_RGB_najnowsza_piksel_0.05: suma rozmiarów plików | 35.8 GB |
| NMPT 0.50 m 2025: szacowany rozmiar 34 arkuszy mozaiki | 5.08 GB |
| NMPT 1.00 m 2025: szacowany rozmiar 82 arkuszy mozaiki | 3.06 GB |
| NMT 1.00 m 2022: szacowany rozmiar 1 arkuszy mozaiki | 0.04 GB |
| NMT 1.00 m 2024: szacowany rozmiar 3 arkuszy mozaiki | 0.04 GB |
| NMT 1.00 m 2025: szacowany rozmiar 115 arkuszy mozaiki | 4.28 GB |
| NMPT: szacowany rozmiar całej mozaiki (ASC) | 8.14 GB |
| NMT: szacowany rozmiar całej mozaiki (ASC) | 4.36 GB |
| BDOT10k powiat 2061 GPKG.zip — rozmiar | 15.6 MB |
| Modele 3D budynków LoD1 2024, powiat 2061 — rozmiar ZIP | 12.8 MB |
| Modele 3D budynków LoD1 2022, powiat 2061 — rozmiar ZIP | 12.7 MB |
| Modele 3D budynków LoD2 2017, powiat 2061 — rozmiar ZIP | 23.5 MB |
| Modele 3D drzew LoD1 2023, powiat 2061 — rozmiar ZIP | 1.07 GB |
| BDOT10k powiat 2002 GPKG.zip — rozmiar | 90.3 MB |
| Modele 3D budynków LoD1 2024, powiat 2002 — rozmiar ZIP | 23.9 MB |
| Modele 3D budynków LoD1 2022, powiat 2002 — rozmiar ZIP | 23.3 MB |
| Modele 3D budynków LoD2 2017, powiat 2002 — rozmiar ZIP | 34.1 MB |
| Modele 3D drzew LoD1 2023, powiat 2002 — rozmiar ZIP | 45.77 GB |

Ortofoto: suma `wlk_pliku_mb` ze skorowidza. NMT/NMPT: skorowidz nie podaje rozmiaru — średni `Content-Length` z HEAD próby 6 arkuszy/grupę × liczba arkuszy. **Modele 3D drzew powiatu 2002 to 45,8 GB** — nie pobierać w całości.

## 6. Zdjęcia z poziomu jezdni
| źródło | wynik |
|---|---|
| Panoramax | 653 zdjęć w obwiedni bboxu, 14 sekwencji; wg roku {'2019': 613, '2020': 1, '2025': 6, '2026': 33}; 613 z 2 przejazdów z 2019 r. (S8 → Trasa Generalska → DK8/19 na północ, tam i z powrotem, kadr co ok. 75 m, aparat telefonu, FOV 59°) |
| Panoramax po 2024 r. | 40 zdjęć — punktowe zdjęcia POI (obejrzane PX32: miejsce pamięci w lesie; PX33: wnętrze lokalu), **0 % komórek korytarzy** |
| KartaView | 16 sekwencji przecina korytarze (lata 2016, 2018, 2019, 2021, 2026); API zwraca ok. 1 zdjęcie/sekwencję/zapytanie, więc 263 to dolne ograniczenie; pokrycie komórek korytarzy 52.2 % |
| Commons | zebrano tylko 7 z 24 punktów (429): L01: 0, L02: 119, L03: 0, L04: 53, L05: 0, L06: 149, L07: 179 plików w promieniu 1 km; zera niespójne z sąsiadami → UNVERIFIED |
| Mapillary | POMINIĘTO (brak tokenu) — LUKA |

Pokrycie korytarzy (komórki 600 m z ≥ 1 zdjęciem w promieniu 500 m):

| ref | komórek | Panoramax % | KartaView % |
|---|---|---|---|
| (trunk_link bez ref) | 42 | 54.8 | 81.0 |
| 19 | 33 | 12.1 | 42.4 |
| 65 | 32 | 6.2 | 50.0 |
| (primary_link bez ref) | 22 | 9.1 | 40.9 |
| 678 | 17 | 0.0 | 5.9 |
| 8;65 | 17 | 100.0 | 100.0 |
| 8;19 | 16 | 100.0 | 100.0 |
| 669 | 15 | 0.0 | 13.3 |
| (trunk bez ref) | 10 | 10.0 | 10.0 |
| 8 | 10 | 100.0 | 100.0 |
| S8 | 9 | 100.0 | 100.0 |
| S19;65 | 8 | 0.0 | 0.0 |
| 19;65 | 7 | 14.3 | 100.0 |
| 676 | 6 | 50.0 | 100.0 |
| (motorway_link bez ref) | 6 | 83.3 | 83.3 |
| 19;65;676 | 3 | 0.0 | 100.0 |
| 19;676 | 1 | 0.0 | 100.0 |
| 19;678 | 1 | 0.0 | 0.0 |
| (primary bez ref) | 1 | 0.0 | 0.0 |

Azymut: `view:azimuth` z API (kompas telefonu). Dla 25 z 28 pierwszych kadrów różni się od kursu wyliczonego z toru o ≤ 23°, dla 3 kadrów na odcinku północnym o 51–54° (PX17–PX19) — kolumna `kurs_z_toru_deg` w manifeście.

### Obejrzane kadry (opis = tylko to, co widać; pełne opisy w manifest.csv)
| id | kadr | data | lat, lon | azymut ° | obiekt |
|---|---|---|---|---|---|
| R9-309 | PX01 | 2019-08-15 | 53.164125, 22.955723 | 101 | S8 przed zach. skrajem bboxu — ekran akustyczny |
| R9-310 | PX02 | 2019-08-15 | 53.161941, 22.974756 | 115 | S8 — obiekt nad drogą (żółto-zielony) |
| R9-311 | PX03 | 2019-08-15 | 53.160596, 22.990343 | 109 | S8 — dojazd do węzła Choroszcz (pas wyłączania) |
| R9-312 | PX04 | 2019-08-15 | 53.158552, 23.002063 | 104 | S8 — węzeł Choroszcz, tablica odległości |
| R9-313 | PX05 | 2019-08-15 | 53.157642, 23.007126 | 112 | Wiadukt nad S8 (ul. Podleśna wg OSM) |
| R9-314 | PX06 | 2019-08-15 | 53.156228, 23.015799 | 108 | S8 — rejon węzła Białystok Zachód (stan 2019, przed budową S19) |
| R9-315 | PX07 | 2019-08-15 | 53.155326, 23.020883 | 108 | S8 — odcinek leśny przed końcem drogi ekspresowej (stan 2019) |
| R9-316 | PX08 | 2019-08-15 | 53.153492, 23.031008 | 106 | Koniec S8 / początek DK8 — długi ekran akustyczny |
| R9-317 | PX09 | 2019-08-15 | 53.150513, 23.047539 | 110 | DK8 (Trasa Generalska, zach.) — ekran + roboty drogowe 2019 |
| R9-318 | PX10 | 2019-08-15 | 53.149436, 23.057546 | 101 | DK8 — plac budowy wiaduktu (2019), mur z bloczków |
| R9-319 | PX11 | 2019-08-15 | 53.152775, 23.076029 | 85 | Estakada w ciągu DK8 (ul. Gen. Kleeberga) |
| R9-320 | PX12 | 2019-08-15 | 53.155648, 23.086330 | 86 | Estakada w ciągu DK8 (ul. Gen. Kleeberga), druga |
| R9-321 | PX13 | 2019-08-15 | 53.159747, 23.112377 | 105 | Kładka dla pieszych nad Trasą Generalską |
| R9-322 | PX14 | 2019-08-15 | 53.159421, 23.120945 | 101 | Biały wiadukt łukowy nad Trasą Generalską (ul. Lodowa wg OSM) |
| R9-323 | PX15 | 2019-08-15 | 53.159104, 23.130971 | 98 | Trasa Generalska — ekrany przezroczyste po obu stronach |
| R9-324 | PX16 | 2019-08-15 | 53.159495, 23.146706 | 113 | Węzeł DK8/DK19/DK65 (Maczka × al. Tysiąclecia) — łącznica w prawo |
| R9-325 | PX17 | 2019-08-15 | 53.159948, 23.151826 | 59 | DK8/DK19 (al. Tysiąclecia PP) — ekran trójdzielny |
| R9-326 | PX18 | 2019-08-15 | 53.196399, 23.155638 | 58 | Niebieski wiadukt łukowy — węzeł Jurowce |
| R9-327 | PX19 | 2019-08-15 | 53.216241, 23.156110 | 49 | Węzeł Białystok Północ (nazwa proponowana w OSM) — rozwidlenie |
| R9-328 | PX20 | 2019-09-01 | 53.219913, 23.155677 | 176 | Węzeł Białystok Północ — widok w kierunku południowym |
| R9-329 | PX21 | 2019-09-01 | 53.199456, 23.155135 | 160 | Niebieski wiadukt łukowy — węzeł Jurowce (od północy) |
| R9-330 | PX22 | 2019-09-01 | 53.159967, 23.151582 | 204 | Węzeł DK8/DK19/DK65 — wiadukt nad skrzyżowaniem z sygnalizacją (roboty 2019) |
| R9-331 | PX23 | 2019-09-01 | 53.159399, 23.125289 | 272 | Biały wiadukt łukowy (ul. Lodowa) — widok od wschodu |
| R9-332 | PX24 | 2019-09-01 | 53.159745, 23.115834 | 272 | Kładka dla pieszych nad Trasą Generalską — widok od wschodu |
| R9-333 | PX25 | 2019-09-01 | 53.154305, 23.027025 | 280 | S8 — rejon węzła Białystok Zachód, kierunek zachodni (stan 2019) |
| R9-334 | PX26 | 2019-09-01 | 53.156441, 23.014934 | 278 | Wiadukt nad S8 (ul. Podleśna) — widok od wschodu |
| R9-335 | PX27 | 2019-09-01 | 53.159579, 22.996764 | 280 | S8 — węzeł Choroszcz, pas włączania (kier. zachodni) |
| R9-336 | PX28 | 2019-09-01 | 53.164024, 22.964553 | 272 | S8 — odcinek otwarty przed doliną (kier. zachodni) |
| R9-337 | PX29 | 2019-08-15 | 53.158227, 23.094645 | 83 | DK8 — przejazd w wykopie pod wiaduktem (tunnel=yes wg OSM) |
| R9-338 | PX30 | 2019-09-01 | 53.159593, 23.143251 | 268 | Estakada DK8 ul. Gen. Maczka — widok w kierunku zachodnim |
| R9-339 | PX31 | 2019-09-01 | 53.156441, 23.014934 | 278 | (duplikat PX26) Wiadukt nad S8 (ul. Podleśna) — widok od wschodu |
| R9-340 | PX32 | 2025-10-03 | 53.136550, 23.249502 | 207 | Panoramax 2025 — miejsce pamięci w lesie (nie droga) |
| R9-341 | PX33 | 2026-06-29 | 53.126045, 23.152032 | 242 | Panoramax 2026 (MapComplete) — wnętrze lokalu (nie droga) |
| R9-342 | KV01 | 2019-08-04 | 53.220247, 23.213413 | 59.76 | DK19 — rejon węzła Wasilków (2019) |
| R9-343 | KV02 | 2021-06-23 | 53.140438, 23.201179 | 2.54 | DK65 — skrzyżowanie przy wiaduktach Sosabowskiego/Sulika (kadr boczny) |
| R9-344 | KV03 | 2021-06-23 | 53.146805, 23.180756 | 305.55 | DK19/DK65 — wykop z murem oporowym, kominy w tle |
| R9-345 | KV04 | 2021-06-23 | 53.150865, 23.170368 | 303.05 | DK19/DK65 ul. Gen. Andersa — wjazd na estakadę |
| R9-346 | KV05 | 2019-08-25 | 53.125988, 23.232227 | 253.46 | Wylot wschodni — tablica przed rondem, bramownica z VMS (2019) |
| R9-347 | KV06 | 2019-08-04 | 53.220256, 23.169532 | 81.71 | DK19 za węzłem Białystok Północ — jedna jezdnia, ekran brązowy |

## 7. Punkty rozpoznawalne do bramki etapu (24)
Dla wszystkich: OSM jest, NMT 1 m 2025 jest, LoD1 2024 i LoD2 2017 w paczce powiatu. Różnicuje je ortofoto i zdjęcia.

| id | punkt | lat, lon | OSM | ortofoto RGB | kadry | Panoramax r=300 m | KartaView (sekw.) |
|---|---|---|---|---|---|---|---|
| L01 | Węzeł Choroszcz (S8) | 53.160046, 22.993638 | node 1940503816; node 1908957192 | 2025-05-25 / 0.1 m | PX03, PX04, PX27 | 10 | 8 |
| L02 | Węzeł Białystok Zachód (S8/S19/DK8) | 53.156056, 23.016674 | node 3160890725; node 4236127140 (ref=10); node 2081020070 | 2025-05-25 / 0.1 m | PX06, PX07, PX25 | 10 | 4 |
| L03 | Bramownice poboru opłat na S8 (highway=toll_gantry) | 53.156832, 23.011651 | node 8860869965; node 8860869966 | 2025-05-25 / 0.1 m | **brak** | 10 | 4 |
| L04 | Wiadukt ul. Podleśna nad S8 (żółto-zielony) | 53.157139, 23.010408 | way 183641838 | 2025-05-25 / 0.1 m | PX05, PX26 | 10 | 4 |
| L05 | Żółto-zielony obiekt nad S8 (footway wg OSM) | 53.16144, 22.977677 | way 297344552 | 2025-05-25 / 0.1 m | PX02 | 11 | 4 |
| L06 | Ekran akustyczny na końcu S8 / początku DK8 | 53.152765, 23.034554 | way 1570885060; way 1571341516 | 2025-05-25 / 0.1 m | PX08 | 11 | 8 |
| L07 | Wiadukt nad DK8 (tertiary, zach. część Trasy Generalskiej) | 53.148996, 23.059188 | way 1266830099; way 1266830101 (man_made=bridge, 242 m) | 2025-05-25 / 0.1 m | PX10 | 22 | 5 |
| L08 | Estakada DK8 ul. Gen. Kleeberga (171 m) | 53.153192, 23.077431 | way 242989862; way 242989866 | 2025-04-18 / 0.05 m | PX11 | 20 | 5 |
| L09 | Estakada DK8 ul. Gen. Kleeberga (160 m) | 53.155868, 23.08658 | way 242987870; way 301459395 | 2025-04-18 / 0.05 m | PX12 | 16 | 4 |
| L10 | Przejazd DK8 w wykopie pod wiaduktem (tunnel=yes, 77 m) | 53.158827, 23.0967 | way 23982181; way 76073122 | 2025-04-18 / 0.05 m | PX29 | 16 | 6 |
| L11 | Kładka dla pieszych nad Trasą Generalską | 53.15974, 23.114182 | way 320734383; way 1308878270 | 2025-04-18 / 0.05 m | PX13, PX24 | 16 | 4 |
| L12 | Biały wiadukt łukowy ul. Lodowa nad Trasą Generalską | 53.159364, 23.123258 | way 126214244 | 2025-04-18 / 0.05 m | PX14, PX23 | 18 | 4 |
| L13 | Estakada DK8 ul. Gen. Maczka (173 m) | 53.159411, 23.141165 | way 173990798; way 173990799 | 2025-04-18 / 0.05 m | PX30 | 16 | 8 |
| L14 | Węzeł DK8/DK19/DK65 (Maczka / al. Tysiąclecia PP / Andersa) | 53.159168, 23.151131 | way 23844386; way 173985170; way 25447143; way 173985172 | 2025-04-18 / 0.05 m | PX16, PX22 | 27 | 10 |
| L15 | Ekran trójdzielny (beton/panel/szkło) al. Tysiąclecia PP | 53.159478, 23.152126 | way 319142226; way 319142227; way 319142228 | 2025-04-18 / 0.05 m | PX17 | 26 | 10 |
| L16 | Niebieski wiadukt łukowy — węzeł Jurowce (DK8/DK19) | 53.197791, 23.155698 | way 239748580; node 1838303448; node 1154984451 | 2025-05-12 / 0.1 m | PX18, PX21 | 16 | 8 |
| L17 | Węzeł Białystok Północ (proposed:name w OSM) | 53.217839, 23.154995 | node 1154993008; node 1838303608; way 188844674; way 188844677 | 2025-05-12 / 0.1 m | PX19, PX20 | 14 | 6 |
| L18 | Węzeł Wasilków (proposed:name w OSM), DK19 | 53.220518, 23.214169 | node 1166095461; node 2183661977 | 2025-05-12 / 0.1 m | KV01 | 0 | 1 |
| L19 | Mosty S19 (82–83 m) na odcinku S19;65 | 53.177635, 23.033319 | way 241580474; way 241580477; way 241580472; way 241580478 | 2025-05-25 / 0.1 m | **brak** | 0 | 0 |
| L20 | Estakada DK19/DK65 ul. Gen. Andersa (196 m) | 53.151774, 23.167485 | way 177876107; way 177895177 | 2025-04-18 / 0.05 m | KV04 | 0 | 5 |
| L21 | Przejazd DK19/DK65 w wykopie (tunnel=yes, 77 m), widok na kominy | 53.146198, 23.182344 | way 175157471; way 237915062 | 2025-04-18 / 0.05 m | KV03 | 0 | 2 |
| L22 | Wiadukty DK65 ul. Sosabowskiego / Sulika (120 m + 80 m) | 53.140638, 23.199932 | way 175054483; way 262041392; way 175054484; way 262041391 | 2025-04-18 / 0.05 m | KV02 | 0 | 3 |
| L23 | Tunele DW669 al. Niepodległości (2 × ok. 95 m) | 53.128211, 23.088106 | way 318134425; way 318134438; way 318134424; way 318134432 | 2025-04-18 / 0.05 m | **brak** | 0 | 0 |
| L24 | Wiadukt DK19 nad torami/drogą za węzłem Białystok Północ (95 m) | 53.220392, 23.171269 | way 211148007 | 2025-05-12 / 0.1 m | KV06 | 0 | 1 |

Najmocniejsze wizualnie (potwierdzone na obrazie): biały łuk ul. Lodowej (L12), niebieski podwójny łuk w Jurowcach (L16), żółto-zielony wiadukt ul. Podleśnej (L04), wykopy z murami i zielonym oczepem (L10, L21), kominy widoczne z DK19/DK65 (KV03), ekran trójdzielny beton/panel/szkło (L15).

## 8. Co już było w repo / co nowe
| temat | było | nowe w R9 |
|---|---|---|
| kafle następnych regionów | `research/gptpro/2-next-regions` (5 kafli zach.), `p6-next-regions-2` (K01–K06, w tym K06 „DK8/S8”) — kafle 2×2 km wokół zakładów | obwiednia całego pierścienia na tej samej siatce, przegląd danych dla 461 km² |
| S19 Krynice–Białystok Zachód otwarta 20.10.2026 | `p6-next-regions-2` §3.2 (SOURCED) | stan w OSM: `motorway S19;65`, mosty, brak jakichkolwiek zdjęć |
| źródła GUGiK dla powiatu 2061 | `Data/SourceManifests/gugik-*-2061.json` | powiat 2002: URL-e, rozmiary, liczby budynków, daty; korekta TERYT |
| ograniczenia TIR, znaki S8 | `research/g10-*`, `gptpro/3-s8-signs`, `p7-s8-signs-2` | nie powtarzano |
| zdjęcia | Mapillary/KartaView dla regionów C i Dojlidy | pokrycie Panoramax/KartaView korytarzy pierścienia, 38 obejrzanych kadrów |

## 9. Ryzyka i luki
1. **Nie zebrano (limit sesji):** długości i tagi klas secondary/tertiary/residential/service oraz **budynki (liczba, % `building:levels`/`height`)** — zapytania Overpass w kaflach 4×4 przerwane po 10/16 kafli dróg; budynków nie zaczęto. Komenda w `STATUS.md`.
2. **Commons:** tylko 7/24 punktów, wyniki zerowe niewiarygodne; nie obejrzano żadnego pliku z Commons.
3. **Zdjęcia są stare.** Wszystkie kadry dróg pochodzą z 2016–2021; na części widać roboty z 2019 r. (PX09, PX10, PX22). Węzeł Białystok Zachód na kadrach z 2019 r. nie ma jeszcze obiektów S19 (PX06, PX07, PX25).
4. **S19 (`S19;65`), DW669 z tunelami, DW678: 0–6 % pokrycia zdjęciami.** L19 i L23 nie mają żadnego kadru; L03 (bramownice opłat) bez rozpoznawalnego kadru.
5. **Ortofoto 0,05 m tylko w granicach miasta**; poza nim 0,10 m (2025) — wystarcza na osie i pasy, słabiej na oznakowanie poziome. 1,8 % bboxu ma tylko 0,25 m z 2024.
6. **Ortofoto i NMT są z IV–V 2025, S19 otwarto X 2026** — trzeba sprawdzić na rastrze, czy pokazują stan docelowy czy budowę (nie sprawdzono; UNVERIFIED).
7. **LoD2 to stan 2017**, LoD1 2025 nie istnieje pod wzorcem URL (404). Hale przy węźle Choroszcz i wzdłuż S8 nowsze niż 2017 będą tylko w LoD1.
8. `width` ≈ 0 %, `lit` niekompletne, nazwy 3 z 5 węzłów nieoficjalne, brak `bridge:name`.
9. Overpass: użyto jednego mirrora (maps.mail.ru); zapytań nie powtórzono na drugim serwerze. Daty danych: `timestamp_osm_base` 2026-11-14T17:08–17:21Z.
10. Samokontrola: dla wierszy OSM i pokrycia zdjęciami kontrola polegała na ponownym przeliczeniu z zapisanego surowego wyniku, nie na ponownym zapytaniu.

## 10. Rekomendowana kolejność pozyskania
1. BDOT10k 2002 (90 MB) + LoD1 2024 2002 (24 MB) + LoD2 2002 (34 MB) — małe, per powiat, od razu.
2. NMT 1 m 2025 dla kafli korytarza (ok. 37 MB/arkusz 1:5000).
3. Ortofoto 0,25 m RGB 2024 dla korytarza (jak w obecnym pipeline, ok. 40 MB/arkusz), a 0,05/0,10 m 2025 tylko dla kafli z punktami z §7 (ok. 1 GB/arkusz 0,05 m).
4. Dokończyć Overpass (drogi niższych klas, budynki), najlepiej z wycinka Geofabrik już używanego przez `tools/worldgen`.
5. Zdjęcia: Mapillary przez `tools/refs` (lider ma token) dla S19 i DW669; zdjęcia właściciela dla L02, L03, L19, L23.
6. NMPT i modele drzew — dopiero gdy potrzebne; drzewa 2002 tylko wycinkami.

## 11. Pliki
`manifest.csv` · `sources.md` · `audit_20_percent.json` · `fetch.py` (38 kadrów, 24,9 MB, sha256) · `overpass/` (surowe wyniki 2,6 MB + zbiorcze) · `gugik/` · `panoramax/` · `kartaview/` · `commons/` · `tools/` (wszystkie skrypty) · `STATUS.md`. Kadry Panoramax/KartaView: CC BY-SA 4.0 — referencja, nie tekstura.

