# ADR 0326 — brama z OSM stoi na własnej drodze, nie w poprzek sąsiedniej jezdni

Status: Proposed (agent fix-b4-s24, 2026-11-22). Numer nadany przez lidera.
Powiązane: build #4 (`artifacts/full-build-4-s24/STATUS.md`, P1, klatka t=250 s), ADR 0300 (przeszkody na trasie
autopilota), ADR 0302 (podróż przez kafle).

## Problem

Na gen. Maczka (kafel `bialystok-maczka`, lok. ~(377, 2)) zielona brama przesuwna stała w poprzek prawej jezdni
i ciężarówka przejeżdżała przez nią. Źródło: węzeł `osm:node/13072640312` (`barrier=gate`) leży na
`highway=track` (way/1422488642), ok. 5 m za krawędzią jezdni. `streetscape.furniture.misc_points` szukał
najbliższego łańcucha drogowego w odległości 6 m **od krawędzi** (`nearest_chain(net, q, 6.0)`, d = |lat| − hw)
i stawiał każdą bramę na osi tego łańcucha, obróconą w poprzek. Polna droga nie jest w sieci dróg, więc
„najbliższa” była Maczka. Tego samego rodzaju trafienia: `bialystok-mickiewicza` osm:node/6002495021
(service=emergency_access) i `tykocin` osm:node/3052214622 (prywatny podjazd).

Żadna kontrola tego nie łapała: bramy są instancjami propów (`street_props.glb`), a nie trójkątami chunków, więc
`qa/route_obstacles.py` (ADR 0300) ich nie widział, a `tests/gis/route_corridor.py` jawnie pomija `*_gate`.

## Decyzja

1. `furniture.gate_pose(net, proto, q)`: brama idzie w poprzek łańcucha tylko wtedy, gdy węzeł leży na jego
   jezdni (|lat| ≤ hw + `GATE_ON_CARRIAGEWAY_TOL_M` = 1,0 m, WORKING_VALUE), czyli gdy jest to brama na tej
   drodze. Węzeł poza jezdnią należy do bocznej drogi spoza sieci: brama zostaje na węźle, przęsło równolegle do
   drogi (boczna droga dochodzi zwykle pod kątem prostym). Szlaban: wysięgnik wyśrodkowany na węźle.
2. Jeśli przęsło bramy (zakres x prototypu: brama przesuwna −4,2…4,2 m, szlaban 0…5,2 m) wchodzi na jezdnię
   innego łańcucha (+0,3 m), brama jest pomijana i zapisana w raporcie (`gates_dropped_on_carriageway`).
   Lepiej brak bramy niż zamknięta droga publiczna.
3. `qa/route_obstacles.py`: instancje bram w kopercie trasy (start + linki korytarza) są kolizjami
   (`prop|<proto>|<src>`). Test danych `tests/gis/test_gate_pose_0326.py::test_no_gate_across_a_route_lane` dla
   wszystkich kafli korytarzy + testy jednostkowe `gate_pose`.

## Konsekwencje

- Brama na polnej drodze przy Maczka stoi tam, gdzie w OSM, równolegle do jezdni; jezdnia wolna.
- Brama na drodze z sieci (np. wjazd na teren zakładu modelowany jako service) zachowuje się jak dotąd.
- Orientacja bramy poza siecią jest przybliżona (równolegle do najbliższej drogi), bo źródła streetscape nie
  zawierają geometrii dróg `highway=track/service` spoza sieci. Dokładniej: dodać te drogi do
  `streetscape/sources.py` i obracać bramę w poprzek jej własnej drogi (otwarte).

## Dodatek (ta sama gałąź fix-b4-s24): szwy kafla przy przyciętym kikucie

`test_world_roads::test_junction_seams_are_watertight` (5 otwartych szwów na C) i
`::test_mesh_matches_generated_centreline` (3,55 m) zaczęły padać po seam-knw-s24 (`meshing.seam_shear`,
`clip_parts_to_box`). Diagnoza (build C w procesie, `artifacts/fix-b4-s24/diag_c.py`):

- **szwy** — wszystkie 5 to skrzyżowania 2–12 m od krawędzi kafla, których krótki łańcuch do szwu ma
  `meta["seam_clip"]`: ribbon był przycinany do kafla, patch skrzyżowania nie. Wspólna krawędź końca ramienia
  przecinała krawędź kafla, więc w ribbonie została rozcięta (wierzchołek T), a patch wystawał do sąsiada (podwójna
  nawierzchnia). **Poprawka generatora:** `seam_clip_pred(net, junctions)` przycina też patche tych skrzyżowań tym
  samym prostokątem — oba wycinki mają ten sam punkt cięcia. Test porównuje dla tych skrzyżowań odcinki końca
  ramienia przycięte do kafla (Liang–Barsky, ta sama interpolacja liniowa co `_clip_poly`).
- **centreline** — wiersz końcowy łańcucha kończącego się na szwie leży wzdłuż linii szwu (N' = N + kT, N'·N = 1),
  czyli za końcem łańcucha; `Polyline.project` przycina stację do końca i zwraca odległość radialną (3,55 m przy
  k ≈ 1,7). Geometria jest poprawna (szerokość mierzona prostopadle do osi zachowana) — **błędny był pomiar testu**:
  dla wierzchołków rzutowanych na koniec łańcucha offset boczny jest teraz mierzony na normalnej końca.
  Granica 0,2 m bez zmian.

`test_terrain_walls` (5 punktów steep_grass przy e=1024,2 n=-955,5): json C w repo pochodził z 16e3a5aea; build tego
samego kafla na kodzie main 1c0596b94 (i z tą gałęzią) daje 0 punktów steep_grass — ratchet 0 bez zmian, json
odświeżony przebudową C.

Sprawdzenie bez pełnego builda (`artifacts/fix-b4-s24/gate_check.py`, sieć z `pipeline.build_network`):
`bialystok-mickiewicza` osm:node/6002495021 leży na modelowanej drodze service=emergency_access (hw 2,75 m), ale
8,4 m przęsła wchodzi na jezdnię trasy — brama pominięta. Otwarte: dopasowanie szerokości bramy do szerokości
jej drogi (prototyp ma stałe 8 m), wtedy taka brama mogłaby zostać.
