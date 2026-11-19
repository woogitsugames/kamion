# ADR 0292 — kafel `dk8-s8-jeroniki` (+ `bialystok-porosly`): ciągła trasa Białystok → S8

Status: Proposed (agent dk8-s8-s24, 2026-11-18). Numer nadany przez lidera.

## Dowody
`artifacts/dk8-s8-s24/` (main): `run/*.exit|log`, `vqa-r5/dk8-s8-jeroniki`, `vqa-r6/bialystok-porosly` (+ `small/`), `seams/seams-r6.md`, `ortho/` (wycinki ortofoto GUGiK 2024, tylko referencja).
Powiązane: ADR 0278 (plan mapy: definicje obu kafli, siatka (−4,−1) i (−3,−1)), 0288 (pętla S8, Otwarte 1), 0285 (trasy
łączące), 0275 (szwy), 0204/0288 pkt 7 (`graph_filter` tunelu), D63 (najpierw przejezdne), D82.

## Kontekst
ADR 0288 Otwarte 1: pętla S8 (`s8-01..05`) jest odcięta od miasta. Jezdnia S8 w stronę Warszawy (way 305447699) ścina
narożnik `dk65-01` i wchodzi do niego ze szwu południowego (769340,8; 595199,0) = północna krawędź `dk8-s8-jeroniki`.

**Ustalenie z grafu skierowanego (zbudowany `dk8-s8-jeroniki`, `pipeline.effective_graph` + `roadgraph.to_digraph`):**
węzeł S8 W na szwie z `dk65-01` jest osiągalny z węzłów brzegowych kafla tylko przez:
1. DK8 W (`trunk`, ref 8;65, way 889307875 / trunk_link 615607622) od **wschodniej** krawędzi = szew z `bialystok-porosly`
   (1527 m, same jezdnie DK8 → S8) — jedyna legalna ścieżka;
2. S8 E (183639794) i łącznicę 1151440428 od północy — ale wyłącznie przez przejazd w pasie dzielącym DK8
   (way 1571341511/1571341512, `highway=service`, `access=no`) = zawrotka, odrzucone.
Warszawska (tertiary, osiągalna z trasy `dk65-01`, szew 769448,5) nie ma wjazdu na DK8 W: rondo przy (770130, 594900)
łączy się tylko z DK8 E (zjazd 221522234) i z Warszawską po północnej stronie. Sam `dk8-s8-jeroniki` nie wystarcza —
potrzebny jest też `bialystok-porosly` (ADR 0278 #1, kolejny w kolejce planu) i link w `bialystok-knyszynska`
(Kleeberga prosto na południe zamiast zjazdu na rondo Kresowian: węzeł brzegowy way 606396500 (772286,3; 595199,0)
osiągalny z wejścia trasy kontrolnej knyszynska — sprawdzone na grafie).

## Decyzja
1. **Zbudowane dwa kafle** wg ADR 0278 (definicje bez zmian: piny NMT 2025 jeroniki / 2022 porosly, trasy kontrolne
   „do miasta”): ingest → build_region → build_world `--context` → export-route → import Win64 → visual-qa High.
   Kolejność kroków: `tools/worldgen/qa/dk8_s8_s24.ps1` (jak `s8_loop_s24.ps1`).
2. **Przekrój S8 w jeroniki** = te same `authored_overrides` co w `dk65-01` dla way 183639794 / 305447699 (przechodzą przez
   szew): `tools/worldgen/qa/s8_xsec_overrides.py` `TILES += dk8-s8-jeroniki`. Rozstaw osi (`spacing()`) liczony nadal
   tylko z 6 kafli ADR 0288 (`SPACING_TILES`): końce tych way w jeroniki rozchodzą się w węźle (p50 > 12,8 m, extra 0
   w obu wariantach), a ich dołączenie zmieniłoby jedynie tekst `reason` w `dk65-01`/`s8-01` (13,86 → 13,78 m) i wymusiło
   przebudowę kafli bez zmiany geometrii.
3. **Tunel 221522232 poza grafem** (`Data/Regions/dk8-s8-jeroniki/graph_filter.authored.json`): przejazd drogi lokalnej
   pod DK8 i Warszawską; cięcie generatora zostawiało ~15 m dziury w obu jezdniach DK8 i w Warszawskiej (r2:
   `obstacle_in_lane` 90, w tym 32 na trasie kontrolnej i 31 na linku). Jak `s8-04` (ADR 0288 pkt 7).
4. **Linki** (`Data/Streaming/route_links.yaml`, cel `s8`, `-route_to s8`): `knyszynska-kleeberga-s` (replaces_route
   bialystok-knyszynska), `porosly-dk8-w`, `jeroniki-dk8-to-s8`; dalej istniejący `dk65-01-s8-corner` → `s8-01`.
   Korytarz `bialystok-s8`: C → Maczka → Kleeberga → Knyszyńska → Porosły → Jeroniki → dk65-01 → s8-01 … s8-12.
   Test `test_links_stay_in_their_tile_and_replace_only_knyszyn` dopuszcza `replacesRoute = bialystok-knyszynska`.
5. **Katalog:** 2 wpisy w grupie „S8” przed `s8-01`.
6. **Pas dzielący DK8 w jeroniki** — nowe nadpisanie `side_left` / `side_right: median_rural` (`roads/network.py`, tylko
   stacje pasa dzielącego, opt-in; żaden istniejący kafel go nie używa): reguła dawała krawężnikowy pas dzielący URBAN
   (ścieżka po stronie zewnętrznej), `porosly` — wiejski; ortofoto = trawa + bariera bez krawężnika. Nadpisanie
   `dk8-median-rural` na 12 way DK8 w `Data/Regions/dk8-s8-jeroniki/overrides.yaml` (qa.seams jeroniki | porosly
   2 FAIL → 0).
7. **Porosly — zapory krawędzi świata:** import przerywał `WorldEdgeBuilder` („closure rows overlap”). Narzędzie
   `tools/worldgen/qa/edge_closures_check.py` (port `ReadExits`/`PlanClosures` + test cięcia rzędów krzyżujących się
   z `ResolveClosures`; sprawdzone: wszystkie pary krzyżujące jeroniki / knyszynska / dk65-01 = „cut”, kafle się
   importują) wskazało 2 przyczyny: `service` 1155215350 × residential 245695246 (szew N, rzędy się krzyżują, osie nie są
   przed rzędem drugiej drogi → nie cięte) i pętla `service` 248109972 (szew S, dwa wyjścia 6,8 m, przeciwne kierunki →
   równoległe rzędy). `graph_filter.authored.json` porosly = tylko te 2 way; 3 wcześniejsze trafienia „na oko” cofnięte (r7).
9. **Wysokość na szwie porosly | jeroniki** (piny NMT 2022 / 2025): `tools/worldgen/qa/seam_z.py` (wspólne węzły
   brzegowe dwóch kafli, asfalt z GLB, `--overrides` wypisuje nadpisania). r6: DK8 E −0,341 m, DK8 W −0,450 m, 439766168
   +0,249, 255111421 +0,212 → `authored_overrides` `seam-z-w*` (`target: {node}`, `set: {z}` = średnia) w obu kaflach.
   porosly nie przyjmuje z na węźle DK8 W (profil wyznacza tam rampa na most 615609890, +3,3 %), więc jeroniki
   dostaje dla 889307875 wysokość porosly 137,23 m (wpis porosly zostaje bez skutku — zmiana pliku wymusiłaby
   przebudowę porosly). r8: wszystkie 6 węzłów |dz| ≤ 0,086 m (DK8 E −0,023, DK8 W −0,040).
8. `tools/worldgen/streaming/route_links.py`: `head_from: route:<kafel>` (wygładzenie początku linku na koniec trasy
   sąsiada) — potrzebne dla `knyszynska-kleeberga-s` (0,86 m) i `porosly-dk8-w` (`head_from: link:`, 0,65 m).

## Liczby i źródła (zmierzone 18.11)
| wielkość | wartość | źródło |
|---|---|---|
| trasa kontrolna jeroniki (S8 z N → DK8 E) | 1586,32 m | `route_start.json` |
| trasa kontrolna porosly (DK8 W → Kleeberga N) | 1590,44 m | `route_start.json` |
| linki: knyszynska-kleeberga-s / porosly-dk8-w / jeroniki-dk8-to-s8 / dk65-01-s8-corner | 667 / 1560 / 1528 / 578 m | `route_links.json` |
| nowy odcinek koniec trasy kleeberga → szew s8-01 | 4333 m | suma linków |
| złącza korytarza bialystok-s8 (11 par) | 0,0–0,001 m | `route_links.json` corridors |
| ślad zestawu (ciągnik + naczepa 13,6 m) poza nawierzchnią, 4 linki | 0 / 15085, 6510, 15439, 5620 pkt | `qa/link_swept_check.py` |
| WORLD_MEMORY jeroniki Low / High (total) | 94,4 / 217,9 MB | import Win64 r7 (r8: patrz STATUS) |
| WORLD_MEMORY porosly Low / High (total) | 118,6 / 286,0 MB | import Win64 r7 |
| najcięższe 3 kafle korytarza (bez zmian: C+Maczka+Kleeberga) | 434,1 / 1044,2 MB | `tile_graph.json` |
| nowe okna: Kleeberga+Knyszyńska+Porosły / narożnik 2×2 (Knysz., Poros., Jeron., dk65-01) | 391,2 / 902,7; 398,4 / 933,0 MB | `tile_graph.json` |
| narożnik 2×2 + przypięty C | 522,6 / 1200,0 MB (< 850 / 2000 i < 640 / 1450 w `StreamingPolicy`) | j.w. |
| DK8 jezdnia (trunk, 2 pasy): asfalt / rozstaw linii krawędziowych | p50 8,55 m / p50 8,4 m (26 stacji co 50 m, 5 way) | `qa/ortho_xsec.py` (WMS GUGiK); generator 8,0 m |
| wysokość S8 na szwie jeroniki / dk65-01 | dz −0,023 / +0,039 m | `qa/s8_seam_z.py` |
| road_consistency na trasie: jeroniki r5 / porosly r6 | 0 / 25 (11 marking_off_carriageway, 5 obstacle_in_lane przy łącznicach wiaduktu 1266830099/100, 3 furniture, 4 arrow_no_exit, 2 lane_blind_end) | `generated/road_consistency_qa.json` |
| qa.seams r8 (5 kafli, 72 drogi) | 0 FAIL na drogach tras; 3 FAIL poza: service 309106711 porosly/knyszynska, 2 research K1 dk65-01/knyszynska (istniejące) | `artifacts/dk8-s8-s24/seams/seams-r8.md` |
| wysokość na szwie porosly / jeroniki r8 (6 węzłów) i knyszynska / porosly (14 z asfaltem) | max |dz| 0,086 / 0,075 m | `qa/seam_z.py`, `seams/seam_z-r8.json`, `seam_z-r7.json` |

## Testy (18.11)
- pytest tests/gis r6: 2482 passed, 5 failed, 1 skipped, 2 xfailed (53 min). Po poprawkach / ponownym uruchomieniu:
  `test_committed_graph_is_fresh` i `test_export_is_deterministic` — pass (wyścig z plikami przebudowywanymi w trakcie
  przebiegu); `test_every_graph_reader_is_classified` — naprawione (klasyfikacja); zostają 2: skok z 0,437 m (Otwarte 8)
  i fidelity industrial-c (Otwarte 9).
- EditMode Win64 r6: 1348, 1252 passed, 2 failed (Otwarte 7), 94 skipped.

## Odrzucone
- Trasa przez Warszawską (`dk65-01` → jeroniki): brak wjazdu na DK8 W w grafie OSM; jedyna ścieżka = przejazd
  w pasie dzielącym `access=no`.
- Model przejazdu pod DK8 (tunel 221522232) teraz: wymaga flagi pomostu na zakres stacji (ADR 0288 Otwarte 7/11).

## Otwarte
1. 309106711 (service, porosly | knyszynska) pobocze krawężnik / krawężnik płaski — poza trasą.
2. porosly road_consistency na trasie 25 (łącznice wiaduktu 1266830099/100, włączenie DK8) — kafel „przejezdny” (D63).
3. Włazy kanalizacyjne w pasie ruchu DK8 (trunk; `no_manhole_classes` = A, S) — render route-s0159 obu kafli.
4. Tunel 221522232 (jeroniki) i przejazd awaryjny 1571341511/12 poza grafem — model przejazdu przy fladze pomostu na
   zakres stacji (ADR 0288 Otwarte 7/11).
5. Wpis `seam-z-w889307875` w porosly bez skutku (rampa mostu) — usunąć przy następnej przebudowie porosly.
6. `qa.seams` nie mierzy wysokości; `qa/seam_z.py` warto dołączyć do kroku `post` wszystkich kafli.
7. EditMode 2 FAIL poza zakresem (bez zmian C#): `ArtPrefabs_HavePinnedGuids`, `LightPostPolicy…Glass` — wynik r8 w STATUS.
8. Budżety `StreamingPolicy` bez zmian (podnosi agent DK19); okna korytarza w tabeli mieszczą się w obu wariantach.

## Odtworzenie
```
pwsh -File tools/worldgen/qa/dk8_s8_s24.ps1 -Phase ingest -Tiles dk8-s8-jeroniki,bialystok-porosly
uv run --project tools/worldgen python tools/worldgen/qa/s8_xsec_overrides.py [--check]
pwsh -File tools/worldgen/qa/dk8_s8_s24.ps1 -Phase world -Context -Tiles dk8-s8-jeroniki,bialystok-porosly -Tag <tag>
pwsh -File tools/worldgen/qa/dk8_s8_s24.ps1 -Phase unity -Tiles dk8-s8-jeroniki,bialystok-porosly -Tag <tag>
pwsh -File tools/worldgen/qa/dk8_s8_s24.ps1 -Phase post -Tiles dk8-s8-jeroniki,bialystok-porosly -Tag <tag>
pwsh -File tools/worldgen/qa/dk8_s8_s24.ps1 -Phase pytest -Tag <tag>
pwsh -File tools/worldgen/qa/dk8_s8_s24.ps1 -Phase editmode -Tag <tag>
uv run --project tools/worldgen python tools/worldgen/qa/ortho_xsec.py measure dk8-s8-jeroniki 1379858308,197904075,303988444,1567973365,825177452 50 artifacts/dk8-s8-s24/ortho/dk8
```
