# ADR 0100: Węzły r3 — P-21 jako analityczne czworokąty, nawierzchnie autorskie, oznakowanie Putry N / MA-010 / rozdział wsch.

Status: przyjęty (world-builder, junctions-r3), 2026-11-11. Wynika z `docs/reports/visual/REVIEW-2026-11-11-s10-0095.md`
(„Lista poprawek na węzły r3”). Powiązane: ADR 0077, 0086 (kontrakt `_Tint` — nietknięty), 0093, 0095. Dowody:
`artifacts/junctions-r3/` (REPORT.md, zones*/ = ortofoto | ortofoto + kwadraty P-21, trace/ = wycinki z siatką 1 m,
plan_*/ = ortofoto | generator, renders_*/ = kamery kontrolne Unity).

## Kontekst
- **P-21 połamany (P0-1).** `through_lines.paint_zones` sumował obramowanie i pasy w jeden wielokąt shapely, ciął go
  `constrained_delaunay` z segmentacją 1,5 m i drapował tylko w narożnikach trójkątów. Długie trójkąty nad wypukłą
  (spadek poprzeczny) jezdnią i nad nakładającymi się łatami/taśmami chowały się pod asfalt między narożnikami
  (zmierzone b0: do 2,6 cm pod powierzchnią przy uniesieniu farby 6 mm) — z góry i z oczu: fragmenty, „Z”, same ramki.
  Ten sam błąd (siatka 1 m) dawał ciemne plamki w belkach zebr autorskich (`painted_crossing`).
- Dodatkowo kąty i obrysy pól nie zgadzały się z ortofoto: oś `chevron_axis` przy s 1440 leżała na jednej krawędzi pola
  (wszystkie pasy po jednej stronie), wielokąt nosa s 1440 1–1,5 m na SW od malowania, pasmo s 1440 to na ortofoto pasy
  równoległe pod ~29° do osi wiszące na jednej linii obramowania (recenzja nazwała je jodełką), jodełka DK8 ma wierzchołki
  do nosa (generator rysował odwrotnie) i sięga E −806, a w małych polach przy n10015785253 rozstaw pasów to ~0,5 m.
- **Putry N, MA-010 (P0-2):** łaty przejazdu przez pas dzielący i dolny pierścień bez linii (pary „na wprost” krzyżują się
  = skrzyżowanie, generator nic nie maluje). Plac przy przejeździe Putry N to kostka, generator kładł asfalt.
- **Rozdział jezdni wsch. (P1-2/P1-3):** główna (2 pasy) i łącznica (OSM `lanes=3`) startują z jednego węzła
  n1832975577 jako jedna łata 14,9 m z jedną linią przebiegającą ukośnie przez całą jezdnię.
- **Materiały (P1-5..P1-8):** murki 0,6 m wzdłuż pasa dzielącego DK8, szwy łat, smugi na pasie betonu.

## Decyzja
1. **`roads/p21_hatch.py` — P-21 analitycznie.** Każdy pas = pudełko ∩ wielokąt pola zredukowane do czworokąta między
   dwiema liniami krawędzi pasa (części < 0,35 m na którejkolwiek krawędzi = fragment przy wierzchołku, odrzucany).
   Obramowanie = 1 czworokąt na krawędź wielokąta, wewnętrzne narożniki fazowane (mitre ≤ 3 × szerokość). Jeden kąt na
   pole: `chevron_axis` (łamana; pasy lustrzane, `chevron_apex: tip|nose` z ortofoto) albo `axis` + `stripe_rel_deg`;
   `stripe_az_deg` (bezwzględny) dalej czytany. `stripe_w_m`, `stripe_gap_m` per pole (odczyt z ortofoto), `border_edges`
   — które krawędzie mają linię obramowania. Test `tests/gis/test_p21_hatch.py`: każdy pas i każdy odcinek obramowania
   to wypukły czworokąt, boki pasa równoległe (< 0,5°), kierunek pasa = kierunek jego pola (< 0,5°), pasy się nie
   nakładają, nie wychodzą poza pole; jodełka symetryczna względem osi.
2. **Drapowanie bez zanurzeń (`p21_hatch.drape_lift`)**: komórki ≤ 0,35 m wzdłuż czworokąta; w każdej komórce próbka
   powierzchni w środku i środkach krawędzi; narożniki podnoszone o największą nadwyżkę powierzchni nad płaszczyzną farby;
   komórka nad uskokiem > 3 cm odrzucana (liczona). To samo dla `painted_crossing` (belki zebr, kwadraty P-11 jako
   czworokąty) i `painted_arrow` (triangulacja 0,5 m). Raport `painted_zones[].max_lift_m`, test: ≤ 3 cm.
3. **`kind: paved_apron`** (`roads/aprons.py`, na początku `markings.build_markings`): trójkąty jezdni w warstwie `road`
   przycięte analitycznie do wielokąta (shapely, triangulacja kawałków), część wewnątrz dostaje materiał nawierzchni
   (`sett | paving | concrete | asphalt`), z, UV, UV1, COL interpolowane barycentrycznie — powierzchnia nie przesuwa się,
   kolizja (osobna siatka) bez zmian. UV kostki = metry w planie. Test `tests/gis/test_aprons.py` (pole i wysokości).
4. **`kind: guardrail`** (`streetscape/furniture.py`, addytywnie): bariera W na słupkach po łamanej autorskiej na
   wyspach rozdzielających (generator stawia bariery tylko z reguł mostu / pasa dzielącego / nasypu).
5. **Krawężnik pasa dzielącego** (`network.assign_sides`): stacja wiejska przerobiona na miejską medianę z krawężnikiem
   zachowywała głębokość rowu (0,60 m) jako wysokość krawężnika → teraz `KERB_HEIGHT` 0,13 m.
6. **Szwy łat**: materiał łaty skrzyżowania = większość materiałów silnikowych ramion (`standards.surface_material`, z
   udziałem „świeżego” SMA), a nie surowego materiału sekcji — łaty między dwoma ramionami SMA nie są już jaśniejszymi
   prostokątami w poprzek jezdni.
7. **UV w metrach**: pas `curb_concrete` szerszy niż 0,4 m (kod chodnika 0 = beton) dostaje UV planu w metrach zamiast
   UV górnej płaszczyzny krawężnika (u wzdłuż, v w poprzek, fugi co 1 m) — smugi E −830…−770 N 82.
8. Override'y z ortofoto (wszystkie z `reason` i wycinkiem w `artifacts/junctions-r3/trace|zones*|plan*`): pola P-21
   (DK8 przód, s1440 nos i pasmo, n10015785253 × 3), Putry N (2 × P-1, 2 × P-7a, P-7b, plac `paved_apron` paving), MA-010
   (P-1 pierścienia, P-1 wlotu ramienia płd.), zatoka s 1060 (2 × `paved_apron` sett na końcach), rozdział wsch.
   (`paint_clear` ukośnej linii, P-1, P-2b, jodełka, wyspa, bariera, P-21 boczne, P-1e), bariera na wyspie E −782,
   n10015785253 SE (4 × `paint_clear` strzałek na wprost, 2 strzałki naprowadzające). Kamery: `r3_*` (6).

## Wynik
LICZBY_PLACEHOLDER

## Otwarte
OTWARTE_PLACEHOLDER
