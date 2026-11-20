# ADR 0306 — D94: szersze pasy, ochrona separatorów i tor zestawu 16,5 m

Status: Proposed — końcowa walidacja G3 w toku, 2026-11-20. Decyzja właściciela **D94** (docs/11).
Gałąź road-widen-s24. Powiązane: ADR 0301 (baza pomiarowa), 0095/0077 (położenie i lane_edges),
0233 (lane_follow), 0218/0274/0280/0289 (rondo i tor naczepy), 0300 (route_obstacles).

## Kontekst

Właściciel chce +0,25 m/pas dla grywalności i przejazdu zestawu 16,5 m bez przeciwnego pasa.
Stałe przesuwanie jezdni jednokierunkowych w prawo powodowało w C błędne separatory DK8/parking,
linie poza asfaltem i przeszkody na pasie. Decyzja właściciela 20.11: kierunek wzrostu wynika z geometrii
sąsiadów; przy braku przestrzeni ograniczamy poszerzenie. Liczba pasów pozostaje pomiarowa.
PTB2022 §17 ust.5 i §58 ust.3 wymagają przejazdu pojazdu miarodajnego, bez naszego wzoru poszerzenia
ani promienia krawężnika (tekst api.sejm.gov.pl/eli/acts/DU/2022/1518/text.html przeczytany 19.11).
Kryterium D94 stanowi tor naszego zestawu. Poniższe wartości projektowe są **GAMEPLAY / WORKING_VALUE**.

## Decyzja

1. standards.GAMEPLAY_LANE_WIDEN_M=0.25. network.gameplay_widen działa raz po pomiarach i overrides,
   przed łańcuchami. Razem aktualizuje lane_w, lane_edges, width, width_profile, edge_line_spacing,
   center_offset i center_offset_profile. Zachowuje liczbę pasów i opaski. Zero wyłącza reguły D94.
   Podłoga BDOT nie zastępuje już dodatkowego D94; nie ma stałego „w prawo” ani GROW_RIGHT_MAX_M.
2. widening_clearance używa niezmiennego snapshotu nieposzerzonych dróg, z lokalnymi profilami
   szerokości i położenia. Uwzględnia dwukierunkowe drogi parkingowe/serwisowe, ten sam layer/bridge.
   Kolejne sekcje tej samej drogi nie są sąsiadem. Próby co około8 m (minimum3), |dot|≥0,9,
   rzeczywisty dystans≤40 m. Sama obwiednia STRtree zakrzywionej drogi nie wystarcza.
3. Na każdej stronie/stacji najpierw wybiera najbliższego sąsiada. Przeciwbieżne oneway poza pierścieniem
   zachowują CAŁY bazowy median, także >12 m. Inni sąsiedzi zachowują bliską szczelinę do12 m,
   a nadwyżkę dzielą po połowie: nie wolno wydać jej dwukrotnie. 12 m nie jest pomiarem ortofoto.
   Nie tworzymy nowej szczeliny, jeśli bazowe nawierzchnie już się nakładają.
4. Wzrost idzie ku większemu luzowi, przy równym luzie symetrycznie. Przy braku miejsca jest mniejszy
   lub zerowy. Minimum ze stacji obowiązuje całą sekcję, więc ograniczenie jest lokalne do sekcji.
   Brak sąsiadów daje wzrost symetryczny. Ślad w provenance: gameplay_clearance_m, gameplay_widen_m,
   gameplay_widen_limited_m, gameplay_shift_left_m. Pomiar bazowego położenia sprawdzamy osobno.
5. curve_widen pozostaje dla dwukierunkowych dwupasowych GP/G/Z bez lane_edges, R<200 m:
   pas≥2,48+2×(offtracking+0,10) m, maksymalnie +1 m/pas. Model swept_path.Combination,
   rampa około20 m; bez15 m przy węźle≥3 i40 m od szwu. lane_follow prowadzi oba pasy symetrycznie.
6. Rondo kompaktowe: promień wlotu≥12 m, wylotu≥15 m, narożniki16 m. Ring Knyszyna5,00→5,25 m,
   projektowany lane_w_m +0,25 m. Szerokie łuki zgodne ze zdjęciem drona właściciela nr9.
7. Parking w435369082: klasaD kończy wyszukiwanie przecięcia krawędzi/przycięcie przed zmianą stycznej
   >45°. Stary solver sięgał za zakręt pętli (trim40,44/81,57 m). Dwa lokalne T pozostają oddzielne,
   gdy CAŁE aktualne grupy mają wyłącznie klasęD, bez roundabout/compact, a długość łącznika i minimalna
   fizyczna odległość między grupami wynoszą≥2 szerokości najszerszej jezdni. Solver dzieli łącznik między
   oba łuki. Reguła nie rozdziela grup z drogą publiczną/rondem.
8. Korekta pomiarowa: dk8-placement-a, w882366266, N146,58..335,85, center_offset -0,50→-0,18 m.
   GUGiK HR/ortho_lane_fit: 9/15 profili, dwa pasy we wszystkich9, MAD granic0,07/0,07/0,05 m.
   Rzeczywiste N180,001/219,979/260,008: linia między pasami -0,30/-0,10/-0,05 m od OSM.
   Szerokość/liczba pasów bez zmian; dk8-placement-b nadal -0,55 m. Dowód:
   artifacts/road-widen-s24/dk8-correct-edge-strips.png. Wcześniejsza diagnoza przypisująca te stacje do b
   została wycofana: projekcja zatrzymywała się na końcu niewłaściwej krawędzi. STATUS zachowuje historię.
9. Odziedziczone L/D: limit BDOT std+0,25; klasaD ignoruje BDOT, które obejmuje zatoki/podjazdy.
   Autorski swing rynek→dk65-w usunięto we wcześniejszym etapie D94.

## Domena kontroli przejazdu parkingu

Po naprawie geometrii pozostawał fałszywy blind_end: trim8,911+3=11,911 m przekraczał długość10,745 m.
Polyline klipował centrum, normalna Hermite'a wypychała skrajną próbkę poza cap. _outbound_probe_s
ogranicza cel do max(trim,min(trim+3,L-1)), po ograniczeniu trim do[0,L]. Margines1 m wobec skrajnej
próbki0,9 m. Długie ramię zachowuje pełne3 m. Jedna stacja obowiązuje dla fan_l, pasów, q_end/c_out/ob/q1/z1.
Cały przejazd nadal jest klasyfikowany. SurfaceIndex, DRIVABLE, kategorie i ratchety bez zmian.
Regresja używa rzeczywistych trójkątów krótkiego zakrzywionego i długiego ramienia: falseNone znika,
prawdziwy krawężnik wewnątrz przejazdu nadal jest wykrywany. Odrzucony prototyp rezerwy4 m nie jest rozwiązaniem.

## Walidacja G3

Zakończone build_world + export-route C i Knyszyn, fidelity C i road_consistency.
W toku route_links, combo_lane_check C/Knyszyn i trzy wymagane moduły pytest. Kod c06c16ea2. Bez edytora Unity.
Niezależna recenzja offline: docs/reports/visual/2026-11-20-road-widen-geometry.md.

| C | przed (r7) | G3 | cel |
|---|---:|---:|---:|
| fidelity absent_on_ortho przy trasie |1|0|≤1, cel0|
| marking_off_carriageway |6|2|≤3|
| obstacle_in_lane |3|2|≤2|
| lane_blind_end na trasie |3|1|≤1|
| lane_blind_end cały kafel |45|32|≤55|

G3 fidelity: oś p95 0,044→0,044 m; krawędź p95 1,625→2,032 m (pogorszenie, nadal poniżej istniejącego ratchetu2,36 m).
Knyszyn road_consistency: G2b blind7/obstacle6/trasa1→G3 3/5/0.

G2b przed korektą QA/dystansu: wyspy0, marking0, obstacle2, blind41, trasa2;
43passed/1failed/1xfailed. Jedyna porażka: nieistniejący cel krótkiego ramienia opisany wyżej.
Referencja/progi fidelity bez zmian. Mały komponent N120 około27 m od trasy jest poza istniejącym pasmem
raportowania przy trasie; nie dodano wyjątku.

| Knyszyn opposite/kerb/off_hard | r8 | G2b |
|---|---|---|
| DK65→DW671 W, środek pasa |0/5/0|0/5/0|
| DK65→DW671 W, swing w swoim pasie |0/0/0|0/0/0|
| DK65→DK65 W |0/0/0|0/0/0|

Historycznie przed D94: DK65→DW671 W0/23/5, DK65→DK65 W0/16/0. Player r8 poprzedniego agenta:
0 wyjątków; ciągnik/prawe koła naczepy na asfalcie, lewe5,8 s na zaprojektowanym fartuchu.
To dowód historyczny, nie przejazd po G3. Tykocin opposite109→7 (swing0), Kleeberga/dk65-05/knyszyn-s/w0/0/0
również pochodzą z wcześniejszych przebudów.

## Testy i konsekwencje

Testy przekrojów mierzonych: GAMEPLAY=0 przez tests/gis/conftest.py; test_road_widen_0306 ustawia0,25.
Regresje: kierunek, dwukierunkowy parking, oba boki zajęte, warstwy, lokalne profile, wspólny budżet,
median20 m, najbliższy sąsiad przed dalszym przeciwnym, odległa droga z nakładającą obwiednią,
parkingowe T oraz rzeczywisty blocker w krótkim ramieniu QA. Ratchety fidelity/consistency bez zmian.
Po scaleniu pozostałe kafle wymagają regeneracji, export-route i route_links; szwy dopiero po obu stronach.
Tutaj pełna walidacja obejmuje C i Knyszyn. Poza zakresem: skręty ulicami Rynku Knyszyna z przeciwnym pasem,
globalny katalog regionów i złote trasy po fali przebudów. Nie oznacza to zerowego combo dla całej sieci.
