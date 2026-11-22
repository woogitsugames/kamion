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
