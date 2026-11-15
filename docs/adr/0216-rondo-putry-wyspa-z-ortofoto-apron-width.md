# ADR 0216 — rondo Putry: krawężnik wyspy z ortofoto (`apron_width`, `island_curb_radius`) i dwa rzędy podpór pomostu SW
Status: Proposed (agent world-builder, s20, gałąź `putry-ring-0198b` na bazie `piers-0198` = PR #82, sesja w chmurze),
2026-11-15. Numer 0216 do potwierdzenia przez lidera (0214 = `dk65-tiles2-0214`, 0215 = `dk65-d65-data`; 0216 nie
występuje na żadnej gałęzi `origin/*` w dniu zapisu). Do scalenia po weryfikacji w Unity.
Powiązane: ADR 0198 (rzędy podpór per pomost, konflikt pomostu SW), 0123 (`apron: asphalt`, `pier_lines_en`),
0077 (`center_offset`, MA-010), 0095 (profile `[t, wartość]`), 0117 (bariery przy podporach).

## Kontekst
- ADR 0198 zostawił na pomoście SW estakady A (`c:w173956078`) przęsło **79,0 m**: rzędy wyspowe 86,0 i 111,0 m
  czekały w `pier_lines_en_held`, bo w wygenerowanym świecie krawędź wyspy ronda leżała pod osią pomostu SW.
- Decyzja właściciela 2026-11-15: **poprawić geometrię ronda, potem dołożyć dwa rzędy**.
- Sesja bez Unity, bez `Data/raw`, bez `build_world`. Geometria w planie pochodzi z etapu dróg generatora na płaskim
  modelu terenu (`tools/worldgen/qa/check_piers_vs_roads.py`, ten sam kod co `build_world`).

## Pomiar (wszystko WORKING_VALUE)
- Źródło: ortofoto GUGiK, WMS `PZGIK/ORTO/WMS/HighResolution`, `GetMap` EPSG:2180, okno E −640…−480, N −80…+80
  (BBOX 777355, 596143, 777515, 596303), 3200 × 3200 px = 0,05 m/px, pobrane 2026-11-15. Tylko referencja, plik nie
  jest w repo (dwa podglądy ≤ 960 px w `artifacts/putry-ring-0198b/`). Rozdzielczość źródłowa mozaiki i data nalotu:
  UNVERIFIED. Bez Google. OSM: cztery drogi pierścienia `junction=roundabout` (180144451 S, 257367425 W,
  257367424 N, 257367428 E) — OSM nie ma obrysu wyspy.
- Metoda: siatka 1 m w układzie lokalnym nałożona na powiększone wycinki (3–6×); odczyt „na oko” krawędzi asfaltu
  przy jasnym pasie krawężnika wyspy, **38 punktów**, dokładność ±0,3 m (dwa punkty w szczelinie między pomostami
  ±0,5 m). Części wyspy pod pomostami są niewidoczne i nie mają punktów. Punkty: `tests/gis/test_putry_ring_0216.py`
  (`KERB`).
- Wyspa nie ma opaski z kostki: asfalt dochodzi do krawężnika, za nim żwir i trawa (część N) albo żwir z barierą
  (strona SW przy pomoście SW). Czy jasny pas to sam krawężnik, czy krawężnik z wąskim pasem za nim: UNVERIFIED.
- Krawężnik względem krawędzi jezdni z generatora: W +0,0…+0,45 m, N +0,15…+0,7 m, E +0,25…+0,6 m. Reguła
  (`ROUNDABOUT_APRON_W` = 2,0 m opaski) stawiała krawężnik wyspy 1,3–2,5 m za głęboko.
- Strona S (`w180144451`, 46 m): w metrach na LEWO od osi OSM krawężnik wyspy +6,3 (s 3 m) / +5,0 (6) / +4,0 (9) /
  +3,7 (11,5) / +3,57 (15) / +3,47 (19), dalej nos: +4,4 (23) / +6,3 (26,7) / +7,2 (27,2); krawężnik chodnika po
  prawej −3,8 (8) / −3,3 (12,5) / −2,6 (19) / −2,5 (23,5). Między s 10 a 20 m prawdziwa jezdnia (6,1–7,0 m, dwa
  pasy) leży NA osi OSM. Override MA-010 (`center_offset: 2.9` na całej długości) jest słuszny tylko na wschodnim
  końcu; na odcinku przy wyspie wsunął lewy pas i opaskę na prawdziwą wyspę (krawężnik średnio 3,6 m, najwyżej 4,9 m
  za głęboko).
- Narożnik NW wyspy: łuk o promieniu 12,0 m (najmniejsze kwadraty, 12 punktów, środek E −561,3 N 41,8, reszty
  ≤ 0,13 m).

## Decyzja
1. **Generator, `roads/network.py`:** pole `set: {apron_width: <m>}` na krawędziach pierścienia = odległość krawędzi
   jezdni od krawężnika wyspy (`Section.apron_w`; zakres 0,2–4,0 m, poza zakresem albo na krawędzi niebędącej
   rondem → `overrides_stale`). Bez pola obowiązuje reguła 2,0 m — inne ronda bez zmian. Zero nie jest dozwolone:
   pas o szerokości 0 dałby zdegenerowane trójkąty w siatce. Układ pasów nie jest ruszany.
2. **Generator, `roads/junctions.py`:** pole węzła `island_curb_radius` = promień łuku krawężnika między dwiema
   jezdniami pierścienia (narożnik wyspy ronda wydłużonego). Dotyczy tylko tego narożnika; `curb_radius` zmieniałby
   wszystkie narożniki skrzyżowania.
3. **Dane, `overrides.yaml` regionu C (jawne authored_overrides, przeżywają reimport):**
   - `putry-ring-island-kerb` (4 drogi pierścienia): `apron: asphalt`, `apron_width: 0.4` (średnia z trzech
     zakresów);
   - `putry-ring-s-placement` (MA-010) jako profil: oś 1,2 m w lewo / 7,2 m na zachodnim końcu, 0,25 → 0,15 m / 6,0 m
     dla t 0,25–0,42, powrót do wartości MA-010 (2,9 m / 7,0 m) od t 0,62 — na wschód od nosa wyspy nic się nie
     zmienia;
   - `putry-ring-island-nw-corner` (`n3890183128`): `island_curb_radius: 10.0` — największa wartość, która mieści
     się na 38,7 m drogi N (reguła 12 m spadała do 8,4 m).
4. **Podpory, `viaduct_underdeck.json`:** pomost SW dostaje rzędy **89,0 i 109,0 m** (osie E −565,12 N 9,11 oraz
   E −548,38 N −1,83); `pier_lines_en_held` usunięte. Rzędy z ADR 0198 (86,0 / 111,0 m) stoją 1,65 i 1,94 m od
   asfaltu, czyli poza jezdnią, ale w keep-out generatora (ok. 2,5 m) — dlatego 89,0 / 109,0: 1 m stacji od obu końców
   wolnego okna 88–110 m.

## Wynik (zmierzony na płaskim modelu terenu)
| Miara | ADR 0198 | ADR 0216 |
|---|---|---|
| krawężnik wyspy vs 38 punktów ortofoto, średnia / p95 / max | 2,02 / 4,72 / 4,93 m | **0,46 / 1,24 / 1,37 m** |
| strona S (pod pomostem SW), średnia / max | 3,64 / 4,93 m | 0,18 / 0,81 m |
| pole wyspy w linii krawężnika | 1388 m² | 1679 m² |
| opaska `apron_sett` na rondzie Putry | 313,8 m² | 0 |
| wolne okno pary kolumn pod pomostem SW | brak (62–133 m zajęte) | 88–110 m |
| pomost SW: rzędy / max przęsło | 6 / 79,0 m | **8 / 32,5 m** |
| pomost NE: max przęsło | 33,7 m | 33,7 m (bez zmian) |

- Przęsła SW: 19,5 / 20,5 / 16,5 / 32,5 / 20,0 / 26,5 / 26,0 / 26,0 / 25,8 m. Kolumny nowych rzędów 3,06 i 2,84 m od
  jezdni; `BLOCKED_COLS` pusty; najmniejsza odległość kolumny od jezdni 2,53 m (rząd 135,5 m, jak w ADR 0198).
  Rzędy NE 82,5 / 106,0 m zyskały zapas (3,03 → 4,63 m, 2,60 → 4,20 m).
- Zmiana powierzchni jezdnej: −302 m² (wyspa rośnie do prawdziwego krawężnika), +32,5 m² (prawa krawędź drogi S
  dochodzi do krawężnika chodnika, E −567…−550, N −18…−8). Poza rondem Putry nic.
- Narożniki pierścienia: NW R 10,0 (było 8,4); pozostałe trzy narożniki wyspy i wszystkie zewnętrzne bez zmian.
- Dowody: `artifacts/putry-ring-0198b/ortho-overlay-island.jpg`, `ortho-overlay-sw-deck-rows.jpg`,
  `piers_vs_roads.txt/.json`. Ortofoto: Źródło danych: Główny Urząd Geodezji i Kartografii (www.geoportal.gov.pl).

## Konsekwencje
- Po `build_world` zmienią się: jezdnie i płyty skrzyżowań ronda Putry, spec `viaduct_putry_underdeck.spec.json`
  (16 rzędów zamiast 14), kolizje, bariery przy podporach (ADR 0117), `roads_qa.json`, `fidelity_qa.json`, trasa
  startowa (styka się z rondem w węźle `n2629251371`; krawędzi pierścienia nie używa). Budżet: +4 kolumny, mniej
  trójkątów opaski — do zmierzenia przez lidera.
- Sygnalizator `putry-ring-s-approach-signal-island` (E −545,0 N 40,0) stoi teraz 1,8 m za krawężnikiem na wyspie
  (ortofoto: 1,6 m). Sondy póz `sbs-g3-b-182011943700132-probe-00` / `-01` (klasa C, GPS zdjęcia) wypadają 0,07 m i
  1,6 m za nowym krawężnikiem wyspy (dotąd na opasce) — do przeglądu przy SBS, nie zmieniane.

## Otwarte / niezweryfikowane
- Brak renderów i SBS (bez Unity): pętla wizualna u lidera (putry-above, g3b_eye_s1582, g3b_eye_s1632,
  route-putry-approach, driver-andersa-to-putry; Low i High).
- Droga S: między t 0,42 a 0,62 oś przesuwa się o 2,75 m na ok. 9 m; wstęga poza płytami skrzyżowań ma tam ok. 4 m —
  linia pasów może być na niej skośna. Sprawdzić w putry-above oraz kadr MA-010 (`au_r_s1160`: prawy pas nie może
  wjeżdżać w trójkątną wysepkę).
- Narożnik NW: krawężnik nadal do 1,4 m poza prawdziwym (promień 10 zamiast 12 m — ogranicza długość drogi N).
- Narożnik SE i wschodni krawężnik pod pomostami: niewidoczne na ortofoto, kształt z reguły (łuk 8,4 m).
- Stacje rzędów pozostają WORKING_VALUE (słupy zasłonięte pomostami); rytm SW 32,5 / 20,0 / 26,5 m nie jest równy.
- Pełna maska keep-out (place, działki) i `pier_cols_on_carriageway == []` — dopiero po `build_world`.
- `test_road_fidelity.py::test_report_not_stale` pada do czasu `fidelity/run.py` z `Data/raw`.
