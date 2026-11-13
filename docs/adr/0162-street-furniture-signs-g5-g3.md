# ADR 0162 — meble uliczne i tablice kierunkowe wg badań G5 / G3
Status: Proposed (agent furn-0162, s16, gałąź `furn-0162`), 2026-11-13. Do scalenia przez lidera.

## Kontekst
Badanie G5 (`research/g5-street-furniture`, dokumenty BKM / ZDM Białystok) pokazało, że generator mebli odbiega od
standardów miasta: wiata 4 m czarna z ciemnymi szybami zamiast modułowej wiaty BKM 7 m w RAL 3020, latarnie GP 12 m
(ZDM: oprawy „do 11 m”) bez szarej podstawy i wnęki, słup energetyczny 10 m w kontroli kolizji a 12 m w siatce.
Badanie G3 (`research/gptpro/3-s8-signs`, przegląd `docs/reports/REVIEW-2026-11-13-s16-gptpro-g2-g3.md`) dało treść
tablic 2024 dla Putry i al. Tysiąclecia, której gra nie miała. Zakres: tylko meble, tablice, materiały mebli
(addytywnie), `docs/LICENSES.md`; drogi, bariery W, pozy kamer (0161) i roślinność (0163) — nie.

## Decyzje
### 1. Wiata BKM (G5-001 / G5-005 / G5-004, SOURCED)
- Prototyp `props.bus_shelter_bkm(modules, colour)`: moduł 2 m, dach n × 2 m + 2 × 0,5 m (5 / 7 / 9 m), dach 2,6 m nad
  chodnikiem na niskiej krawędzi, ściana 1,07 m, 0,55 m nawisu z tyłu na wspornikach Y, 1,4 m od słupów tylnych do
  krawędzi od jezdni; szyby 0,6 × 0,99 m od 0,15 m (3 rzędy × 2 na moduł, 1 na ścianie bocznej); ławka 0,4 m
  (2 + 3 listwy) w module −x, dwie gabloty w module +x, rynna + rura spustowa, stelaż D-15 typ B nad dachem
  0,55 × 0,805 m (oba lica), niebieska tablica informacyjna na krawędzi od jezdni **bez logo i tekstu przewoźnika**.
- Odczyt z rysunków, WORKING_VALUE: spadek dachu 0,25 m ku tyłowi (2019: 0,26/1,7 m; 2020: 0,21/1,95 m), profil
  słupa 80 × 60, pręty 40 mm, gablota 0,92 × 0,78 m od 1,1 m. Strona jezdni = wysoka krawędź (stelaż typ A/C/F „od
  strony jezdni” jest na wysokim końcu rzutu bocznego 2020).
- Materiały: `shelter_paint` = jeden atlas (`furniture_textures.shelter_atlas`: RAL 3020, grafit,
  drewno, rozkład, tablica, stelaż), `shelter_glass_clear` (przezroczyste szkło hartowane — model `car_glass/screen`
  jak ekrany; stare `shelter_glass` było prawie czarną płytą), dach z poliwęglanu dymionego jako pole tego samego atlasu (2 sloty zamiast 4). LOD1 ≈ 1/3 trójkątów.
- Warianty: `bus_shelter` (3 moduły, standard), `bus_shelter_5m`, `bus_shelter_9m` w proporcji zamówienia 2020
  (44 / 29 / 7 z 80 — SOURCED); `bus_shelter_black` (starsze grafitowe, G5-020) 15 % — WORKING_VALUE. Wybór
  deterministyczny z położenia przystanku (przeżywa reimport). D-15 jest na stelażu wiaty — osobny słupek D-15 przy
  wiacie usunięty.
- Polityka LOD wariantów: `InstanceImporter.cs` i `build_world.instance_ends` — `StartsWith("bus_shelter")` zamiast
  równości (inaczej warianty znikałyby na 120 m zamiast 300 m). **Jedyna zmiana poza zakresem plików — do akceptacji lidera.**
- Krawężnik przystankowy 16 cm (G5): geometria dróg — zgłoszone do 0161, nie zmieniane.

### 2. U-12a / U-12 / U-5a (G5-010, SOURCED)
Prototypy `railing_u12a` (+ `railing_u12a_post`), `fence_u12`, `pylon_u5a`; materiały `paint_ral1012`, `paint_ral3020`.
**W danych regionu ich nie ma** (OSM/BDOT10k: brak `barrier=guard_rail/handrail`, słupków U-5a) — rozstawiono 0 sztuk.
Balustrada na murach oporowych zostaje ocynkowana (to nie panel U-12a; poprawiony opis w `furniture.py`).

### 3. Latarnie i słup energetyczny
- `standards.LAMP["GP"]` 12 → 11 m (ZDM PFU „do 11 m”, SOURCED). Wnęka drzwiczek 0,60 × 0,13 m na LOD0 (dolna
  krawędź 0,5 m — UNVERIFIED), dolne 0,3 m słupa szare — pas w atlasie `furniture_galv` (bez nowego materiału);
  maszt zatopiony pod wiaduktem liczy pas od własnej stopy (`Mesh.ground_z`).
- Słup energetyczny: jedna wysokość 12 m (siatka, zawieszenie przewodów H − 0,3 m, `GROUND_PROP_H`); seria słupa
  w regionie UNVERIFIED (G5).

### 4. Tablice wg G3 (treść z odczytu; tarcze własne; Mapillary CC BY-SA = tylko treść)
- `signs.panel_board`: panele piętrowe, strzałki ↑ ← → ↗ (zamiast strzałek „w dół”), „Centrum” niebieskim w białym
  polu, owale PL / BY, tarcze 675 żółte. `e1_cross_board` (E-1 ze schematem skrzyżowania), `vms_board` (LED).
  `landmarks.py`: klucze tablicy `arrow`, `panels`, `style`, `lat_shift_m`.
- **Rozstrzygnięcie „andersa-gantry”**: G3-P012/P013 (2024) pokazują na *pierwszym* portalu (przed rozwidleniem)
  nadal Augustów / Kuźnica / Centrum na jednej tablicy (↗); Centrum jako osobny panel ze strzałką w lewo jest na
  *drugim* portalu przed rondem (G3-P001..P004 2024 i C001..C004 CC0 2021). Ujednolicono oba do stanu 2024:
  pierwszy — strzałki ↑↑ / ↗, treść bez zmian; `andersa-putry-portal-p40` — 4 panele (W/E ↑ nad Centrum ←; W/E ↑ nad
  Augustów/Kuźnica PL BY →) i kolumny z ortofoto (10,8 m, ~30 m przed starą stacją, która była WORKING_VALUE).
- Nowe (w obszarze regionu, pozycje z ortofoto 0,08 m): E-1 P009 (portal N 310,6 nad jezdnią na południe,
  „Kuźnica B.”), VMS P010 (bramownica ITS N 236,0 nad obiema jezdniami, tablica tylko nad jezdnią na południe),
  portal P005–P008 (N ~119, 3 tablice).
- **Poza regionem — nie dodane**: E-14 „Kowno (Kaunas) LT 236” (MN009, ~7,7 km na N od środka kafla), „S8 Warszawa /
  Tykocin Złotoria 500 m” (MLY-S8-010, ~13,5 km na W). Wymagają następnego kafla (G2).
- D-15: piktogram poprawiony na autobus z boku bez napisu „BUS”.

### 5. Kadry z recenzji s16b
- 297817 (duże drzewa z lewej): roślinność — zgłoszone do 0163, bez zmian.
- 1801374 (brak dwuramiennej latarni x 0,68): WYNIK — patrz sekcja „Dowody”.

### 6. Budżet: tablica nad jezdnią = 1 materiał
Każda tablica `board_OB_*` miała 3 submesze (lico, szary tył `board_back`, szyny `steel_galv`) = 3 instancjonowane
draw calle; 5 nowych tablic al. Tysiąclecia dawało +15. `export.py` dokleja pod lico w teksturze tablicy pas 16 px
w kolorze `board_back` (0,21/0,22/0,22 lin. → sRGB 126/128/128), `props.board` mapuje tył i szyny na środek pasa
(`BOARD_BAND`). Tył zostaje gładki i szary (ADR 0127), lico nie próbkuje pasu (test). Dotyczy też istniejących tablic
Andersa/Putry (−2 draw na tablicę).

## Dowody
- Czysty A/B (`artifacts/furn-0162/tools/ab_run.ps1`, `ab_b2.ps1`): A = origin/main (kod + dane) → build_world →
  import → kamery; B = gałąź. Budżet Low (clear, 48 kamer, `budget-low.txt`, draws = zwykłe + instancjonowane):
  przed redukcją max +24 (g3b-rondo-putry-approach), po redukcji max **+10** (g3b-rondo-putry-approach: 3 nowe
  konstrukcje + 5 tablic z G3 2024), g3a-rondo-bie-approach +3, putry-above +1, route-putry-entry-signs +1,
  route-putry-approach −5, driver-andersa-to-putry −10, stretch-01..05 0…−4; tris max +1,0 % (edge-north,
  route-putry-approach).
- pytest `tests/gis`: 1016 passed / 1 failed / 3 xfailed (18,6 min); jedyny błąd = test oczekujący `lamp_12m` (GP 12 → 11 m) — poprawiony, `test_streetscape.py` 59/59; wcześniej poprawiona lista bramownic (+3 z G3). EditMode 498/498 (w tym
  `InstancePolicyShelterTests`, prefiks `bus_shelter` w `InstanceImporter.Policy`).
- Pary (zdjęcie / przed Low / po Low / po High): `artifacts/furn-0162/pairs/` — wiaty BKM czerwone (sondy), portal
  P005–P008, E-1 P009, VMS P010, p40 wg 2024 czytelne; tył bramownic gładki szary.
- Kadry P1 (Panoramax CC BY-SA, tylko referencja): P1-110 (Tysiąclecia, 2019) i P1-096 / P1-132 (Maczka) — latarnie
  dwuramienne „Y” w pasie dzielącym, białe/jasnoszare; zgodne z `lamp_double_10m` i rzędem z ortofoto. Wiat ani
  tablic w tych kadrach brak. P9-401 (OSM↔GTFS przystanki, ≤ 30 m) — przystanki 1000-lecia PP są w danych OSM
  regionu; nieużyte do zmian (UNVERIFIED paczka).
- 1801374: rząd latarni z ortofoto jest w świecie, ale kamera sbs ma inną pozę/odchylenie niż zdjęcie i latarnia
  z x ≈ 0,68 zdjęcia nie trafia w ten sam punkt kadru gry — do sprawdzenia po korekcie póz kamer (0161), OTWARTE.
- Recenzja s17 (`docs/reports/visual/REVIEW-2026-11-13-s17-0162.md`, SCAL warunkowo) — poprawki i sondy r3/r4
  (overcast, Low+High, pary `artifacts/furn-0162/pairs/probe-*-r3.jpg` i `-r4.jpg`):
  - P1 pas 0,3 m u stopy latarni (był czarny, sRGB 15 przy maszcie 70 na High): tekstura pasa pod `steel_galv`
    (metal 0,9) 112 → 206 (r3: 46, nadal ciemnoszary) → **232** (r4: 58 / maszt 70 High, 83 / 94 Low) — jasnoszary,
    o krok ciemniejszy od cynku, bez ciemnej stopy jak na P1-110. ZAMKNIĘTE. Wnęka drzwiczek na LOD0 — P2, bez zmian.
  - P1 margines VMS P010: czcionka zmniejszana do ≤ 90 % szerokości panelu; „5 MIN” / „7 MIN” mają margines. ZAMKNIĘTE.
    LED bez emisji — P2, otwarte.
  - P2 wiata grafitowa (`bus_shelter_black`) bez niebieskiego pasa informacyjnego (G5-020 Lipowa). ZAMKNIĘTE.
  - P2 peron/utwardzenie pod wiatą — w 0161 (krawężnik przystankowy); brud/AO na stopach wiat — otwarte.
- Przegląd P7 / M45: bramownica A Andersa — „675 Centrum” to 3. wiersz tej samej tablicy (nie dzielić), bez zmian.
  Portal od północy (G3-P005..P008, 2019 P7-001 i 2024): lewa 675 Centrum / 65 Bobrowniki PL BY / 19 Lublin, środkowy
  mały panel ↑ 675 Centrum, prawa 8 E67 Warszawa / 65 Ełk — wszystkie trzy w danych (`tysiaclecia-s-putry-portal`,
  `lanes: [1]` = środek) i widoczne na `probe-f162-tys-portal-g3p005.jpg`. Najazd od południa (2022) bez „Centrum”.
- **Decyzja właściciela D62**: +10 draws Low na `g3b-rondo-putry-approach` (421 → 431) za 3 prawdziwe konstrukcje
  2024 al. Tysiąclecia — przyjęte. Dalsza redukcja (tablice scalone z bramownicą w jeden mesh) — nie robiona.

## Konsekwencje
- Nowe prototypy i tablice = nowe siatki/tekstury; budżet Low mierzony na kamerach trasy (sekcja „Dowody”).
- Treść tablic G3 (ODbL baza faktów, zdjęcia CC BY-SA/CC0) — wpis w `docs/LICENSES.md`, atrybucja na ekran licencji.
