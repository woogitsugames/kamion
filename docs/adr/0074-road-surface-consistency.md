# ADR 0074: Spójność nawierzchni — oznakowanie, pasy, wysepki i słupy sprawdzane na wygenerowanej geometrii

Status: przyjęty (world-builder, roadgeo r9), 2026-11-10. Zgłoszenie właściciela P0
`artifacts/owner/bugs/2026-11-10-lane-into-island.webp` („pas wjeżdża w wysepkę”, „mapa jest pełna błędów”),
audyt `artifacts/map-audit-r9/BUGS.md` (MA-001/002/009/010/016/017).

## Kontekst
Zrzut z telefonu: Andersa na północ (trasa startowa G3-B, s ≈ 1330 m), wlot „z sygnalizacją”, lewy pas ze strzałką
„na wprost” kończy się na wysepce z trawą i krawężnikiem. Miejsce: przejazd przez pas dzielący przy wyjeździe
straży pożarnej (węzły OSM n12620261934 / n12620261936, E −297 N −191, 53,1569 N 23,1556 E).
Prawda w terenie (Mapillary CC BY-SA 489105227073974 i 1202945651056199, 2024-07-26): trzy pasy z liniami
przerywanymi, **bez strzałek i bez linii zatrzymania**, sygnalizatory „emergency” po obu stronach, pas dzielący ciągły
(z barierą), dopiero za bramownicą rozdział 2 pasy na wiadukt + 1 na łącznicę z P-21.

Generator nie miał żadnego testu, że warstwy (taśmy jezdni, łaty skrzyżowań, krawężniki, wysepki, oznakowanie,
słupy) się zgadzają; każda była poprawna „sama w sobie”.

## Przyczyny (u źródła)
1. **`traffic_signals=emergency` = sygnalizacja skrzyżowania.** `roadgraph` oznacza każdy węzeł w 15 m od sygnalizatora
   (`signals_nearby`), a `junctions.build_junctions` brał każdy `highway=traffic_signals` w promieniu 25 m. Skutek: P-14,
   P-2a, S-1 z wysięgnikiem na wyjeździe straży i na rozwidleniu n2840742308.
2. **Nos pasa dzielącego na ukośnej cięciwie.** Nos „median” (`junctions.compute_corners`, rodzaj `nose`, przy trimach)
   łączy krawędzie dwóch jezdni na ich trimach. Gdy trimy się różnią (łuk krawężnika tylko po jednej stronie: 7,8 m vs
   16,7 m), „półokrąg” rozpinał się na ukośnej cięciwie 13 m i leżał na lewym pasie jezdni północnej — to jest wysepka
   ze zrzutu.
3. **Strzałki P-8 / P-2a na każdym końcu odcinka z `turn:lanes`.** OSM dzieli drogę w węźle zjazdu, a `turn:lanes`
   opisuje rozdział dalej. Strzałki „na wprost” i linie ciągłe stały przed wyjazdem straży.
4. **Rozwidlenie 3 → 2 + 1 bez ciągłości pasów.** OSM rysuje każdą jezdnię na jej osi i łączy je w jednym węźle, więc
   wiadukt (2 pasy) był wycentrowany pod środkowym pasem jezdni 3-pasowej; lewy pas wjeżdżał w krawężnik/kapę wiaduktu
   (Andersa przed Rondem Putry i przed Rondem Bieżeństwa, MA-016).
5. **Oznakowanie ze stałą szerokością odcinka.** Linie krawędziowe P-7b i linie pasów jezdni jednokierunkowych brały
   `hw` ze środka odcinka, a strzałki z `lane_layout` bez sprawdzenia szerokości w miejscu malowania; przy zmianie
   szerokości (łącznica 5,5 → 7,5 m, droga 2-pasowa o szerokości 4 m) farba leżała na krawężniku.

## Decyzja
- `roads/consistency.py` — kontrola na wygenerowanej geometrii (indeks trójkątów 2D + okno wysokości 0,8 m, więc
  wiadukt nie myli się z drogą pod nim): `marking_off_carriageway`, `obstacle_in_lane` (pas ± (szer./2 − 0,45 m)),
  `lane_blind_end` (pas, który może jechać prosto, przeprowadzony krzywą Hermite’a przez łatę skrzyżowania do pasu o tym
  samym numerze od prawej na ramieniu wylotowym tej samej drogi OSM), `arrow_no_exit` (kierunek z `turn:lanes` bez
  ramienia), `prop_on_carriageway` (podstawa słupa ≥ 0,2 m wewnątrz jezdni), `furniture_in_lane`. Każdy przypadek ma
  E/N, lat/lon, łańcuch/węzeł, drogi OSM i flagę `on_route` (G3-A, G3-B z `gate3_segment.json`, obie jezdnie w 30 m).
  Wynik: `generated/road_consistency_qa.json`, test `tests/gis/test_road_consistency.py` (trasa = 0, kafel = ratchet).
- Sygnalizacja `emergency` nie czyni skrzyżowania sygnalizowanym (`Junction.emergency_signals`); stawiane są słupy z
  ciemnymi głowicami `signal_head_off` (stan spoczynkowy; na zdjęciu 2024 żółte — WORKING_VALUE), bez wysięgnika.
- Nos pasa dzielącego: trimy obu jezdni wyrównane „na równi” wzdłuż wspólnego kierunku przed wypchnięciem nosa.
- `markings._lanes_continue`: brak P-8 i P-2a, gdy wylotowe ramię to ta sama droga OSM z tymi samymi `turn:lanes`.
- `network.align_forks`: przy rozwidleniu / włączeniu jezdni jednokierunkowych, gdy liczby pasów gałęzi sumują się do
  liczby pasów jezdni pojedynczej, pasy są przydzielane od lewej, a oś każdej gałęzi przesuwana w węźle pod przydzielone
  pasy; pełne przesunięcie trzyma się, aż krawędzie gałęzi rozejdą się o 6 m (klin otwarty), potem zanika (smoothstep,
  max(40 m, 20 × przesunięcie)). Lista: `roads_qa.json → summary.fork_shifts` (WORKING_VALUE: 6 m, 40 m, 20×).
- `markings.strip` przyjmuje boczne położenie zależne od stacji: P-7b i linie pasów jednokierunkowych idą za krawędzią;
  strzałka nie jest malowana, gdy nie mieści się w jezdni w miejscu malowania (licznik w `roads_qa`).
- Ręczne poprawki tylko jako `authored_overrides` z uzasadnieniem i referencją (bez zmian w tej rundzie).

## Konsekwencje
- Kafel: przed 222 przypadki (na G3: 26), wynik po zmianach i ratchet — `artifacts/roadgeo-r9/STATUS.md` i test.
- Kontrola wykrywa też wiele błędów z audytu (MA-001/002/009/010/015/016/018) — stały, automatyczny strażnik.
- Nie wykrywa: garbów nawierzchni (MA-012), złej szerokości z BDOT (MA-011/018) — to osobne kontrole (ADR 0075).
- Przesunięcia rozwidleń zmieniają geometrię łącznic i wiaduktów o 0,5–5 m na długości do ~100 m; ortofoto 2024
  (`ortho_0p25m.tif`) jest do weryfikacji (WORKING_VALUE), test `test_route_corridor` pilnuje przejezdności.
