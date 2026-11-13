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
- Materiały (3 sloty zamiast 4): `shelter_paint` = jeden atlas (`furniture_textures.shelter_atlas`: RAL 3020, grafit,
  drewno, rozkład, tablica, stelaż), `shelter_glass_clear` (przezroczyste szkło hartowane — model `car_glass/screen`
  jak ekrany; stare `shelter_glass` było prawie czarną płytą), `shelter_roof_pc` (poliwęglan dymiony). LOD1 ≈ 1/3 trójkątów.
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

## Dowody
(uzupełniane w trakcie: build_world, fidelity, import, kamery kontrolne Low/High, sondy, pary sbs, budżet Low)

## Konsekwencje
- Nowe prototypy i tablice = nowe siatki/tekstury; budżet Low mierzony na kamerach trasy (sekcja „Dowody”).
- Treść tablic G3 (ODbL baza faktów, zdjęcia CC BY-SA/CC0) — wpis w `docs/LICENSES.md`, atrybucja na ekran licencji.
