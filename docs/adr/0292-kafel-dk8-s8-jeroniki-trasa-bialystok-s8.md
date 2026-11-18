# ADR 0292 — kafel `dk8-s8-jeroniki` (+ `bialystok-porosly`): ciągła trasa Białystok → S8

Status: Proposed (agent dk8-s8-s24, 2026-11-18). Numer nadany przez lidera.
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

## Liczby i źródła
WYNIKI — uzupełniane po krokach (sekcja „Dowody”).

## Odrzucone
- Trasa przez Warszawską (`dk65-01` → jeroniki): brak wjazdu na DK8 W w grafie OSM; jedyna ścieżka = przejazd
  w pasie dzielącym `access=no`.
- Model przejazdu pod DK8 (tunel 221522232) teraz: wymaga flagi pomostu na zakres stacji (ADR 0288 Otwarte 7/11).

## Otwarte
(uzupełniane)

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
