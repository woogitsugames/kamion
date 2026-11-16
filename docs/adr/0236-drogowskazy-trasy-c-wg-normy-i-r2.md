# ADR 0236 — drogowskazy (znaki E) trasy C wg rozporządzenia i researchu R2
Status: Proposed (agent world, s21 chmura D runda 2, gałąź `signs-c-0236`), 2026-11-15. Do scalenia przez lidera.
Powiązane: research R2 (`research/cloud2/direction-signs-route-c`, PR #62) i jego recenzja
`docs/reports/REVIEW-2026-11-15-s21-cloudD-62-direction-signs-route-c.md` (SCAL z erratą), research R1
(`research/cloud2/traffic-signs-catalog`), ADR 0069/0127/0139/0162 (bramownice, rozmiary z kadrów), 0125 (`gate3_sign`).
Kod nieuruchomiony w Unity (chmura): `build_world` C, import i kamery kontrolne wykonuje lider.

## Kontekst
- Recenzja R2 (sekcja 4): wiersz tablicy `overhead_board(row_m=0.62)` jest WORKING_VALUE ponad normą; brak E-1 na
  bramownicy ~500 m przed rondem Putry (R2-079); wymiary tablic w R2 = UNVERIFIED (errata E3).
- Stan generatora przed zmianą (pomiar z `art-source/world/props/props_meta.json` i kodu): tablice regułowe E-2/E-2a
  miały litery 66 mm (tablice 0,85–1,47 × 0,18–0,31 m), E-1 przed rondem 74 mm na stałym polu 2,44 × 2,0 m, tablice
  na bramownicach bez `size_m` wiersz 0,62 m (tablica 5-wierszowa na wysięgniku p37: 4,6 × 3,3 m).

## Źródło normatywne (sprawdzone 2026-11-15)
Załącznik nr 1 do rozporządzenia MI z 3.07.2003 w sprawie szczegółowych warunków technicznych dla znaków i sygnałów
drogowych…, t.j. **Dz.U. 2019 poz. 2311** (PDF ELI `D20192311-c1.pdf`, sha256 `f94925ec…b550543`). Nie ma nowszego
tekstu jednolitego; nowelizacje 2021 poz. 438 i 2066, 2022 poz. 2377, 2026 poz. 132 nie zmieniają tabel użytych niżej
(lista nowelizacji za R1, API ELI). Strony = strony PDF. Tabele 1.9 i 9.5.x są rastrami — odczytane z renderu 110 dpi.

| Co | Wartość | Gdzie |
|---|---|---|
| Litery d: grupy IV/V/VI/VII | 132 / 162 / 210 / 282 mm | Tab. 1.8 s. 16 |
| Grupy liter E-1 / E-2 | średnie: VI,V,IV / VI,V; duże: VII,VI,V,IV / VII,VI | Tab. 1.9 s. 17 |
| Pas pisma | 10 gr (wiersz 8 gr + interlinia 2 gr), d = 6 gr | pkt 1.4.1 s. 15 |
| Długość napisu | szerokości liter w gr, odstęp 1,5 gr, między wyrazami 4,5 gr („Łącko” = 21,99 gr) | Tab. 1.10 s. 18–19 |
| Drogowskaz tablicowy | średnie: b 1200, b1 500 (kolejny kierunek 350), d 210, d1 162; duże: 1500/600 (450), 282/210 | Tab. 9.5.4 s. 457, rys. 9.5.20 |
| Numer drogi na tablicy (d = 210) | h 270, d1 162, m 122; samodzielny E-15: h **300** | Tab. 9.5.3 s. 452, pkt 6.3.7.8 s. 290 |
| Owal „PL” (d = 210) | 240 × 352 mm | Tab. 9.5.5 s. 457 |
| Strzałka | średnie 150/60/270/120, duże 200/80/360/160 mm | Tab. 9.5.6 s. 458 |
| Ramka | średnie e 20, c 5, r 50 mm; linie E-1 a 150 / a1 75 mm | Tab. 9.5.1–9.5.2 s. 450–451, pkt 6.3.1.2 |
| Położenie | E-1: 100 m przed skrzyżowaniem w miastach (lub bliżej); E-2: do 50 m; E-15: do 50 m za skrzyżowaniem; E-14: ok. 200 m za | pkt 6.3.1.4, 6.3.2.2, 6.3.7.8, 6.3.6.4 |
| Nad jezdnią | dolna krawędź ≥ 5,00 m | Tab. 1.11 (2022 poz. 2377) |

**Weryfikacja uwagi D4 (`row_m` 0,62 m):** dotyczy. Recenzent wyliczył ≤ 0,56 m z d ≤ 420 mm; dokładniej: wiersz kolejnego
kierunku to 350 mm (średnie), 450 mm (duże), 610 mm tylko dla „wielkich” (autostrady). 0,62 m ≈ wiersz autostradowy.
Pomiar z kadru czołowego 2019 (ADR 0139): tablice bramownicy Andersa 0,82 m (2 wiersze) i 1,20 m (3 wiersze) —
Tab. 9.5.4 „średnie” daje 0,85 i 1,20 m. Rzeczywiste tablice trasy C mają więc d = 210 mm.

## Decyzja
1. `streetscape/sign_norms.py` — liczby normy z cytatem tabeli/punktu; `signs.py` rysuje E-1/E-2/E-2b z tych liczb:
   wysokość liter, długość napisu wg Tab. 1.10 (glif zastępczy DejaVu ściskany do długości normowej), numery dróg wg
   Tab. 9.5.3, owale, strzałki, ramka, wiersze 0,50 + 0,35 m. `size_m` z kadru nadal wygrywa (ADR 0139/0162; wymiary
   istniejących override'ów bez zmian — z nich wynika d 184–268 mm, w zakresie IV–VII).
2. Domyślna tablica nad jezdnią: d = 210 mm, wiersz 0,35 m (było 0,62 m).
3. Tablice regułowe bez dowodu zdjęciowego (wyloty rond, początki łącznic): d = 132 mm (grupa „małe”, WORKING_VALUE —
   wg pkt 1.2.1 droga krajowa to „średnie”/„duże”, ale 3-metrowa tablica w miejscu, którego nie pokazuje żaden kadr,
   byłaby gorsza niż mała); E-1 przed rondem: d = 132 mm (IV, dozwolona dla E-1). Stacje reguł bez zmian; tablica
   odsunięta tak, by krawędź była ≥ 0,50 m od jezdni (pkt 1.5.3).
4. Trasa C wg R2 (authored overrides, każdy z `r2`, kadrem i `reason`):
   - `andersa-putry-e1-advance-gantry` — E-1 z rozwidloną strzałką na bramownicy kratowej (R2-079). Stopy słupów z
     ortofoto GUGiK WMS HighResolution 0,03 m/px (belka 13,4 m, ±1 m); kadr R2-066 jest 42 m przed nią. Tablica
     3,3 × 1,8 m z proporcji kadru (±10 %).
   - `andersa-putry-cantilever-p37` — tablica zmieniona z listy 5 wierszy (4,6 × 3,3 m) na E-1 ze schematem
     skrzyżowania 4,6 × 1,85 m (R2-081). Recenzja przypisała R2-081 do portalu p40; z geometrii (kadr 46 m przed
     wysięgnikiem, tablica za ekranem estakady) jest to tablica wysięgnika p37. „Centrum” zostaje (stan 2024, G3).
   - E-15 „8 | 19 / E 67” po obu stronach wylotu N ronda Putry (R2-017) i „19 / 65” po obu stronach Andersa za
     wlotem łącznicy z ronda Bieżeństwa (R2-077) — `gate3_sign` z nowymi licami `E-15`/`E-16` (h = 300 mm).
     Stacje ESTIMATED z szerokości tabliczki na kadrze (założony kąt obiektywu), ≤ 50 m za skrzyżowaniem.
   - E-1 z reguły przy portalu p40 (6 m od bramownicy; kadry G3/R2 pokazują tam tylko portal) jest usuwana:
     `signs_route.drop_rule_diagrams_near_gantries` (≤ 40 m od authored bramownicy).
5. Treści: tylko miejscowości, numery dróg, „Centrum”. `furniture.direction_boards` przechodzi przez `brand_filter`
   (wcześniej tylko `_arm_label`). Test: regex zakazanych słów na wszystkich tekstach tablic C i `destination` grafu.
6. Budżet (kompensacja nowej bramownicy, bez utraty wyglądu z bliska):
   - kratownica bramownic/wysięgników: LOD0 krzyżulce 3-ścienne (było 4), LOD1 krzyżulce jako płaskie paski zwrócone
     na zewnątrz (2 trójkąty zamiast 6): bramownica 14 m 1008/480 → **792/208**, wysięgnik 528/240 → 412/108;
   - tablica LOD1: lico + tył (4 trójkąty zamiast 28); tarcza: obrzeże tylko od zewnątrz (koło 240 → 176, bezstratnie).

## Budżet — szacunek per kamera (reguły `build_world.mesh_budget`, instancje o pozycjach w gicie)
Tablice kierunkowe w C (instancje, `streetscape_qa.json`): przed 10 na bramownicach + 21 regułowych (4 E-1, 9 E-2,
8 E-2a) = 31; po: 11 + 20 = 31 (+1 nowa E-1 na bramownicy, −1 regułowa E-1), +4 słupki E-15 (2 prototypy, po 32/20 trójkątów, 1 materiał każdy), bramownice 5 → 6.
Materiały tablic: +1 OB, −1 E-1, +2 E-15 = +2 (bez wpływu na `materials_*` kafli).
`uv run --project tools/worldgen python tests/gis/test_direction_signs_0236.py` (Δ trójkątów High / Low):
stretch_04 (2 022 535) **−224 / 0**; route_onramp_andersa_above (1 993 338) **−544 / +40**; route_onramp_andersa −544 / +40;
fire_station_above −168 / −264; stretch_05_docks −264 / 0; driver_andersa_to_putry −924 / +48; putry_above −852 / −1084;
route_putry_approach −1384 / −1536; route_putry_entry_signs −1380 / −1472; g3b_eye_s1482 −1752 / −1508;
g3b_rondo_putry_approach −1444 / −1512; fire_station_route −924 / −504; fire_station_ref7197 −216 / −208;
**fire_station_abeam +448 / −208** (1 183 284; nowa bramownica 121 m od kamery w LOD0); pozostałe 0.
Nie wliczono (pozycji nie ma w gicie): −64 na każdą tarczę kołową w LOD0, −24 na każdą tablicę regułową w LOD1 —
obie poprawki tylko zmniejszają wynik. Dodatnie: +448 High na jednej kamerze (0,04 %, 41 % pod limitem 2 M) oraz
+40/+48 Low na trzech (dwa słupki E-15 w LOD1). Dokładne liczby: `mesh_budget.frame_estimate` po `build_world`.

## Kontrola wizualna (chmura: tylko lica)
Lica wyrenderowane i obejrzane obok kadrów R2 (kv 0303, 0313, 0281; pmx 6ded8ec0): układ wierszy, pola numerów
(czerwone/zielone/żółte), owale PL/BY, białe pole „Centrum”, rozwidlona strzałka — zgodne. Różnice świadome: krój
zastępczy; schemat skrzyżowania p37 ma napis górny nad osią, na zdjęciu jest z lewej u góry; dwie tabliczki E-15
obok siebie mają wspólny szary podkład 30 mm. Sceny 3D, kamery kontrolne i `visual-critic` — lider.

## Otwarte
1. E-14 za rondem Putry (R2-018): treść znana (Korycin, Suchowola, Augustów, Suwałki, Kaunas), kilometry UNVERIFIED —
   nie postawiono (nie zmyślamy odległości). Wymaga kadru z bliska.
2. Tablice wlotu zachodniego Maczka → Putry (R2-013…016) i Maczka W (R2-082/083): region `bialystok-maczka` (P2 recenzji).
   Zespół przed rondem Bieżeństwa od SE (R2-074…076) leży poza trasą startową — nie dodano (budżet stretch_04).
3. Stan 2026 wszystkich tablic UNVERIFIED (kadry 2019/2021/2024). Stacje E-15 ±10 m.
4. `gate3_sign` po lewej stronie (pas dzielący): jeśli generator nie ma tam pasa, wpis trafi do `stale`
   (`test_every_gate3_sign_is_placed`) — wtedy `at_en` z ortofoto.
5. LOD1 kratownicy na Low (25–400 m): do oceny na kamerze `driver_andersa_to_putry` Low (portal 73 m).
6. Barwa zielona poza polem tolerancji (R1 §3.3) — bez zmian, osobna decyzja.
