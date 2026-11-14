# ADR 0203 — trasa ciężarówki Białystok → Knyszyn (D64): plan kafli i pierwszy kafel `bialystok-maczka`
Status: Proposed (agent world-builder/geo-worldgen, s20, gałąź `bialystok-dk65-0203`), 2026-11-14. Do scalenia przez lidera.
Powiązane: D63, D64 (`docs/11`), ADR 0166 (potok dla regionu ≠ C), ADR 0174 (import regionu), brief
`docs/owner/S20-REGION-RING-BRIEF.md`. Kolejne: ADR 0204 (Knyszyn), ADR 0205 (korytarz).

## Kontekst
Właściciel (D64): rozbudowa Białegostoku w stronę wylotu na Knyszyn, potem droga do Knyszyna, potem Knyszyn; zwykłą
drogą, nie ekspresówką; DROGI NAJPIERW (wierna sieć dróg, budynki LoD1 bez szlifu). Trasa i podział na kafle są
policzone z przypiętego wyciągu OSM (`podlaskie-261108.osm.pbf`, sha w `Data/SourceManifests`), skryptem
`tools/worldgen/qa/dk65_route_plan.py` → `docs/reports/map/dk65_route_plan.json` (+ `.png`): lista dróg z `way_id`,
węzły, ronda, mosty, ograniczenia, budowy w pasie 600 m, przecięcia granic administracyjnych, kafle. Liczby niżej
pochodzą z tego pliku.

## Część 1 — trasa (plan)
Start: Andersa w kaflu C (węzeł DK65 najbliżej 778700, 596300); koniec: Rynek w Knyszynie.

**Uwaga: w OSM (edycja 2026-10-20/21) numer 65 między Białymstokiem a Dobrzyniewem leży na otwartej drodze
ekspresowej `S19;65`** (`highway=motorway`, 4,8 km trasy). Stara droga przez Fasty i Dobrzyniewo Duże nie ma już
numeru (`secondary`, bez `ref`). Dlatego są dwa warianty, a odcinek km 5,9–16,7 wariantu A **nie jest podpisany
jako DK65**:

| | A „stara droga” (przyjęty roboczo) | B „DK65 wg oznakowania” |
|---|---|---|
| długość | 28,44 km | 30,73 km |
| klasy | trunk 8;65 4,53 km · trunk 19;65/65 1,39 km · secondary bez ref 10,47 km · primary 65 11,14 km · DW671 0,47 km | trunk 8;65 8,10 km · **motorway S19;65 4,81 km + łącznice 0,84 km** · primary 65 14,94 km |
| przebieg | Andersa → Maczka → Kleeberga → łącznica → rondo Pamięci Męczeństwa Kresowian (DW669) → Szosa Ełcka → Szosa Knyszyńska → Fasty (Ełcka) → Dobrzyniewo Duże (Studzienna) → rondo z DK65 → DK65 → Knyszyn (Obozowa) → rondo DK65/DW671 → Tykocka → Rynek | Andersa → Maczka → Kleeberga do węzła z S19 → S19 → węzeł Dobrzyniewo → DK65 → dalej jak A |
| zgodność z D64 | tak (bez ekspresówki) | nie (4,8 km ekspresówki) |

Wariant A przyjęty jako WORKING_ASSUMPTION, bo D64 mówi „zwykłą drogą, nie ekspresówką”, a zdjęcia właściciela
z DK65 pokazują jedną jezdnię 2×1 z budową obok (zgodne z odcinkiem km 16,7–25 obu wariantów). Od ronda
(767641, 603483; km 16,66 wariantu A) oba warianty są identyczne.

Wariant A — odcinki (km liczone od startu; `way_id` wszystkich 94 odcinków w JSON):
| km | droga | klasa / ref | pasy (OSM) | uwagi |
|---|---|---|---|---|
| 0,00–1,04 | Gen. Andersa | trunk 19;65 → 65, jezdnia jednokier. | 3/2/3/2 | kafel C; zjazd łącznicy DK19 km 0,78 |
| 1,04–5,19 | Gen. Maczka | trunk 65 → 8;65 (od km 1,39), jednokier. | 2 i 3 na przemian | wiadukty km 0,93–1,15, 1,24–1,26, 1,68–1,85, 4,07–4,09; 11 węzłów z łącznicami `trunk_link` |
| 5,19–5,93 | Gen. Kleeberga | trunk 8;65 | 2 | wiadukt km 5,45–5,61 |
| 5,93–6,18 | łącznica | trunk_link | 1–2 | zjazd z DK8/65 |
| 6,18–6,19 | Rondo Pamięci Męczeństwa Kresowian | secondary 669 | 2 | rondo (772534, 595343) |
| 6,19–7,20 | Szosa Ełcka | secondary | 1–2 | granica miasta km 7,14 (772066, 596171) |
| 7,20–10,94 | Szosa Knyszyńska | secondary | 2 | Dobrzyniewska (km 8,12), Dzikowska (10,69); most km 10,85–10,94 |
| 10,94–16,15 | Fasty: Ełcka | secondary | 2 | Białostocka/Kościelna (km 13,13), Szkolna (14,35) |
| 16,15–16,66 | Dobrzyniewo Duże: Studzienna | secondary | 2 | |
| 16,66–16,79 | rondo (767641, 603483) | primary 65 | 1 | połączenie ze śladem DK65 z węzła S19 |
| 16,79–25,96 | DK65 | primary 65 | 2 | droga 1392B (km 18,77); budowa S19 wzdłuż drogi km 16,7–25,0 |
| 25,96–27,80 | Knyszyn: Obozowa | primary 65 | 2 | granica miasta km 25,95 (761870, 610632); most km 26,96–26,98 |
| 27,80–27,83 | rondo DK65/DW671 (760632, 611993) | primary 65 | — | |
| 27,83–28,44 | Tykocka → Rynek | secondary 671 / residential | 2 | |

Liczby z OSM dla wariantu A: 3 ronda, 7 mostów/wiaduktów, 75 węzłów trasy z innymi drogami (30 z drogą klasy ≥
tertiary lub łącznicą), 1 sygnalizacja i 14 przejść oznaczonych na węzłach trasy, 0 przejazdów kolejowych w poziomie.
Ograniczenia dla ciężarówek: brak `hgv=no`, `maxweight`, `maxheight` na całej trasie; `maxaxleload=11.5` do km 6,18,
`maxaxleload=10` dalej (stara droga i DK65) — do uwzględnienia w danych pojazdu (ADR 0164), nie blokuje przejazdu.

Budowa ekspresówki (OSM, pas 600 m od trasy): `highway=construction` motorway 16,6 km przy km 16,7–25,0 (ostatnia
edycja 2026-09-28), łącznice i drogi serwisowe w budowie (unclassified 5,8 km, secondary 2,4 km km 22,7–25,0,
primary 230 m przy km 25,0 — przełożenie DK65 przy węźle), `proposed` motorway 33,6 km (2026-09-13). Droga
`proposed ref=65` (way 1028944175, 4,6 km) leży na wschód od miasta (785902, 587893 → 787253, 591980) — nie
dotyczy tej trasy. Daty ortofoto i NMT względem robót sprawdza agent kafla (0205) przy ingest.

Granice administracyjne na trasie A (TERYT z tagów `teryt:terc` relacji OSM): Białystok **2061** km 0–7,14; powiat
białostocki **2002** (gm. Dobrzyniewo Duże 2002032) km 7,14–23,67 i 25,22–25,95; powiat moniecki **2008** (gm.
Knyszyn 2008043) km 23,67–25,22 i od 25,95.

## Część 2 — podział na kafle (plan dla 0203, 0204, 0205 i następnych)
Siatka 2048 m kafla C: x = 776971 + 2048·i, y = 595199 + 2048·j (EPSG:2180). `xy` = punkt trasy A na krawędzi
kafla (dokładność ~1 m; agent kafla przyciąga do węzła brzegowego swojego grafu).

| region (id) | i,j | bbox EPSG:2180 | km trasy | m | wejście xy → wyjście xy | powiat | kto |
|---|---|---|---|---|---|---|---|
| `bialystok-industrial-c` | 0,0 | 776971,595199 – 779019,597247 | 0–1,53 | 1528 | … → 776971, 596279 | 2061 | jest |
| **`bialystok-maczka`** | −1,0 | 774923,595199 – 776971,597247 | 1,53–3,58 | 2053 | 776971, 596279 → 774923, 596186 | 2061 (100 %) | **0203 (ten ADR)** |
| `bialystok-kleeberga` | −2,0 | 772875,595199 – 774923,597247 | 3,58–5,80 | 2219 | 774923, 596186 → 772875, 595512 | 2061 (100 %) | następny agent miasta |
| `bialystok-knyszynska` | −3,0 | 770827,595199 – 772875,597247 | 5,80–8,76 | 2958 | 772875, 595512 → 770827, 597007 | 2061 (31 %) + 2002 | następny agent miasta |
| `dk65-01` | −4,0 | 768779,595199 – 770827,597247 | 8,76–9,39 | 631 | 770827, 597007 → 770245, 597247 | 2002 | 0205 |
| `dk65-02` (Fasty S) | −4,1 | 768779,597247 – 770827,599295 | 9,39–11,80 | 2401 | 770245, 597247 → 768779, 598817 | 2002 | 0205 |
| `dk65-03` | −5,1 | 766731,597247 – 768779,599295 | 11,80–12,28 | 484 | 768779, 598818 → 768695, 599295 | 2002 | 0205 |
| `dk65-04` (Fasty N) | −5,2 | 766731,599295 – 768779,601343 | 12,28–14,36 | 2078 | 768695, 599295 → 768335, 601343 | 2002 | 0205 |
| `dk65-05` (Dobrzyniewo) | −5,3 | 766731,601343 – 768779,603391 | 14,36–16,56 | 2200 | 768335, 601343 → 767661, 603391 | 2002 | 0205 |
| `dk65-06` (rondo DK65) | −5,4 | 766731,603391 – 768779,605439 | 16,56–18,26 | 1703 | 767661, 603391 → 766731, 604722 | 2002 | 0205 |
| `dk65-07` | −6,4 | 764683,603391 – 766731,605439 | 18,27–19,13 | 865 | 766731, 604722 → 766246, 605439 | 2002 | 0205 |
| `dk65-08` | −6,5 | 764683,605439 – 766731,607487 | 19,13–21,49 | 2354 | 766246, 605439 → 764683, 607186 | 2002 | 0205 |
| `dk65-09` | −7,5 | 762635,605439 – 764683,607487 | 21,49–21,84 | 352 | 764683, 607187 → 764499, 607487 | 2002 | 0205 |
| `dk65-10` | −7,6 | 762635,607487 – 764683,609535 | 21,84–24,45 | 2614 | 764498, 607488 → 762893, 609535 | 2002 + 2008 | 0205 |
| `dk65-11` | −7,7 | 762635,609535 – 764683,611583 | 24,45–24,83 | 376 | 762892, 609536 → 762636, 609810 | 2002 + 2008 | 0205 |
| `knyszyn-s` | −8,7 | 760587,609535 – 762635,611583 | 24,83–27,25 | 2420 | 762635, 609811 → 760986, 611583 | 2008 (+2002) | 0204 |
| `knyszyn` | −8,8 | 760587,611583 – 762635,613631 | 27,25–28,44 | 1190 | 760986, 611583 → Rynek 761058, 612417 | 2008 | 0204 |

Granice odpowiedzialności: **miasto** = kafle i ≥ −3; **korytarz 0205** = kafle od (−4,0) do (−7,7), szew z miastem
na x = 770827 (trasa y ≈ 597007), szew z Knyszynem na x = 762635 (trasa y ≈ 609811); **Knyszyn 0204** = (−8,7)
i (−8,8), ewentualnie (−9,8) dla zachodniej części miasta (decyzja 0204). Kolejność budowy korytarza: od `dk65-11`
albo od `dk65-06` (odcinek ze zdjęć właściciela i budową) — decyzja 0205; pierwsze dwa kafle miasta po `maczka`
nie są jeszcze przydzielone. Cztery kafle mają < 650 m trasy (`dk65-01`, `-03`, `-09`, `-11`): są potrzebne dla
ciągłości, ale poza pasem drogi mogą zostać samym terenem (bez budynków i roślinności poza ~300 m od osi).

Rzeczy wspólne, których ten ADR **nie** zmienia (żeby trzech agentów nie edytowało tego samego):
1. `tools/worldgen/osm_extract.py`: `BBOX_WGS84 = (22.98, 53.05, 23.32, 53.20)` obcina korytarz od ~km 9 i cały
   Knyszyn, a cache (`Data/raw/derived/*.pkl`) jest kluczowany tylko sha pliku pbf. Zmianę robi **0205** (potrzebuje
   jej pierwszy): `BBOX_WGS84 = (22.80, 53.05, 23.32, 53.38)` + bbox w kluczu cache; 0204 bierze ten sam commit.
   Po zmianie trzeba potwierdzić, że region C i Dojlidy wychodzą bajt w bajt (`test_export_is_deterministic`).
2. `regions.Region.teryt_powiat` to jeden kod. Kafle 2002/2008 i kafel `bialystok-knyszynska` (2061 + 2002)
   potrzebują BDOT10k/LoD1 innego powiatu albo dwóch — rozszerzenie pola na listę robi pierwszy agent, który trafi
   na kafel dwupowiatowy (0205: `dk65-10`); kody 2002 i 2008 potwierdzone tagami `teryt:terc` w OSM.
3. `regions.py`: każdy agent dopisuje tylko swoje wpisy; id i bbox z tabeli wyżej są zarezerwowane.

## Pytania do właściciela
1. Wariant A (stara droga przez Fasty i Dobrzyniewo Duże, bez numeru w OSM) czy B (S19 do węzła Dobrzyniewo)?
   Roboczo A. Jeśli pamięta Pan inny przejazd (np. stara DK65 już zamknięta/przebudowana) — proszę o informację.
2. Budowa przy km 16,7–25: OSM pokazuje nową jezdnię w budowie po obu stronach DK65 i przełożenie DK65 przy km 25;
   zdjęcia z 2026-07 (żółte oznakowanie, C-…) są nowsze niż typowe ortofoto. Które miejsca mają objazd?

## Część 3 — kafel `bialystok-maczka` (wyniki)
(uzupełniane po buildzie)
