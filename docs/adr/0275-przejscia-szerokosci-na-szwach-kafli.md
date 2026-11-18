# ADR 0275 — Przejścia szerokości jezdni i pobocza na szwach kafli i na końcu override (`roads/seam_taper.py`)
Status: Proposed (chmura D, runda 5, zadanie D15, gałąź `seam-taper-0275`; bez Unity i bez `Data/raw`), 2026-11-16. Do scalenia przez lidera.
Powiązane: ADR 0224 (QA szwów, `qa/seams.py` — tym PR wchodzi do gita), 0233 (`lanes_follow_width`), 0272 (pobocze jako
dane, `roads/xsec.py` — na main od feb542757, scalenie `rail-dk65-s22`), 0214 / 0220 (przekrój K1), 0095 (profil `width`),
decyzja lidera s23 (HANDOVER 16.11 05:5x: szew `dk65-11` | `knyszyn-s` bez override w `knyszyn-s`, przejście jako osobna poprawka).

## Kontekst
Kafel buduje drogi z własnego grafu i własnych overrides. Gdy przekrój autorski kończy się na szwie, obie połowy drogi
spotykają się ze skokiem krawędzi. Przypadek z zadania (main feb542757): `dk65-opaska-k1` w `dk65-06…11` daje
6,6 m jezdni + 2 × 0,35 m asfaltu = 7,30 m, a w `knyszyn-s` reguła 0272 `g-single-ground` daje 6,6 + 2 × 0,08 = 6,76 m →
skok 0,27 m na stronę (krawędź gruntu: 4,40 | 4,38 m od osi). Skoki szerokości jezdni: 5 dróg na szwach kafli miejskich
i `knyszyn-s` | `dw671-tykocin-01` (0,10–0,50 m na stronę, tabela w „Wynik”). Ten sam skok powstaje **wewnątrz** kafla,
gdy override pobocza obejmuje część wayów łańcucha: w `dk65-06` kod `mat` zmienia się w jednej stacji na granicy
`w208187096` (0,35 + 0,75 m) / `w1151531610` (0,08 + 1,00 m), 81 m przed końcem łańcucha (szerokość jezdni ma tam
wygładzanie 15 m z `prepare_chain`, pobocze nie miało żadnego).

Przepis: Dz.U. 2022 poz. 1518 (PTB2022; tekst z `https://api.sejm.gov.pl/eli/acts/DU/2022/1518/text.html`, czytany
2026-11-16) **§ 17 ust. 6**: „Zmianę szerokości pasa ruchu projektuje się na krzywej przejściowej lub prostej przejściowej
w sposób płynny, bez widocznych załamań krawędzi. W trudnych warunkach dopuszcza się inne zaprojektowanie zmiany szerokości
pasa ruchu.” Rozporządzenie nie podaje długości ani skosu takiej zmiany i nie mówi nic o zmianie szerokości pobocza
(§ 23 podaje tylko szerokości). W tekście nie ma też „klina” dla zmiany szerokości jezdni (jedyne wystąpienie: klin
naprowadzający przed pasem do skrętu w lewo, definicja skrzyżowania skanalizowanego). Długość przejścia jest więc **ESTIMATED**.

## Decyzja
1. **Reguła oparta na danych obu kafli, symetryczna.** Kafel czyta z gita dane sąsiadów (`region.yaml` → wspólna krawędź
   bbox, `roads.graph.json`, `overrides.yaml`; nigdy `generated/` ani geometrię) i tym samym kodem (`Nw.load` + 3 przebiegi
   rozwidleń) liczy **przekrój nominalny** końca łańcucha sąsiada na szwie — czyli to, co sąsiad zbudowałby sam, przed
   jakimkolwiek przejściem. Końce paruje się po `osm_way` i położeniu (≤ 0,5 m, wzajemnie najbliższe). Oba kafle układają
   dwie połowy jednej krzywej S: `v(x) = A + (B − A)·smoothstep(0,5 + x/L)`; na szwie obie strony dają średnią wartości
   nominalnych (wyrażenie symetryczne `0,5·(a + b)`; pobocze w całych centymetrach `(a + b + 1) // 2`), nachylenie jest
   ciągłe. Odrzucone: przejście w całości po jednej stronie wg porządku kafli (też wymaga danych sąsiada, a przesuwa cały
   klin na kafel, którego pomiar lider uznał za ważniejszy) i wspólny plik szwów w gicie (drugi nośnik prawdy, starzeje się).
2. **Długość** `L = RATIO × największy skok krawędzi` (krawędź jezdni, krawędź asfaltu = półszerokość + część utwardzona,
   zewnętrzna krawędź części gruntowej), `RATIO = 100`, w granicach `MIN_LEN_M = 20` … `MAX_LEN_M = 80` m i nie więcej niż
   2 × długość krótszego z dwóch łańcuchów (koniec przy węźle zachowuje swoją szerokość). Wszystkie trzy liczby ESTIMATED
   (średni skos krawędzi 1:100, największy 1:67). Dla 0,27 m: L = 27 m, po 13,5 m w każdym kaflu.
3. **Co jest mieszane.**
   - półszerokość jezdni `Chain.hw` (`apply_widths`, w `pipeline.build_network` po `abreast_forks`); sekcje w strefie
     przejścia dostają `lane_follow` (ADR 0233, provenance `derived:seam_taper (ADR 0275)`), inaczej linia środkowa
     dwukierunkowej jezdni wyszłaby z osi o połowę zmiany szerokości. Sekcje z `lane_edges` albo profilem `width` bez
     `lanes_follow_width` (pomiar ADR 0095) nie są mieszane — wpis `skipped` w raporcie;
   - szerokości utwardzonej i gruntowej części pobocza (ADR 0272) w kodzie `mat` stacji (`apply_shoulders`, po każdym
     `assign_sides`), rozdzielczość 1 cm; wartości nominalne z `xsec.resolve` (override > OSM `shoulder=*` > reguła
     klasy). Ta sama funkcja zamienia skok kodów między sekcjami jednego łańcucha (koniec override wewnątrz kafla) na
     krzywą S wyśrodkowaną na skoku (połowa długości ograniczona miejscem do sąsiedniego skoku / końca odcinka bez
     krawężnika).
   Nie jest mieszana zmiana rodziny profilu (krawężnik ↔ pobocze) — to zostaje FAIL w `qa/seams.py`.
4. **`qa/seams.py` (z PR #106, ADR 0224) w gicie**, zaktualizowane: buduje sieci jak generator łącznie z przejściami
   (`build_nets`), więc wiersze szerokości porównują to, co stoi na szwie; nowe wiersze `krawędź asfaltu L/P [m od osi]`
   z tolerancją 0,02 m; wiersz `przejście szerokości (ADR 0275)` ze statusem **PRZEJŚCIE** (dane nominalne różne, generator
   je łączy) i wartościami nominalnymi; `--no-taper` pokazuje kafle osobno. `lanes_follow_width`: wiersz „pasy × szer.
   pasa” liczy lokalną szerokość pasa `lane_w_at(hw)` (fałszywy FAIL „3,10 vs 3,55” na `dk65-11` | `knyszyn-s` znika);
   „szer. jezdni ostatni build” jest N/D dla sekcji z profilem szerokości (`roads_qa` niesie maksimum sekcji).
   Override `seam-knyszyn-s-field-road-98071886` z #106 **nie** został przeniesiony (szerokość łączy przejście; oświetlenie
   tej drogi zostaje FAIL do decyzji).

## Styk z ADR 0272 (na main)
- `seam_taper.py` używa `roads.xsec` wprost (`resolve`, `SHOULDER_CODE`, `LEGACY`); nie zmienia `xsec.py`,
  `xsec_rules.yaml`, `network.py`, `meshing.py` ani `rail_approach.py`. Pierwsza wersja gałęzi (przed feb542757) miała
  import opcjonalny i była sprawdzana na próbnym scaleniu — po scaleniu main obejście usunięte.
- `meshing.build_side_strip` czyta `mat` per stacja i liczy profil `side_profile` dla każdej stacji osobno, więc kody
  zmieniające się co stację nie wymagają zmian w siatce; poprawka #138 P2-1 (stacja pożyczona bierze `mat` następnej)
  działa jak dotąd. Odbiorcy `side_shoulder()` (`rail_approach`, `fab_details`, `furniture`) dostają w strefie przejścia
  wartości pośrednie (np. 0,22 + 0,88 m).
- Haki: `pipeline.py` (po `abreast_forks` i po obu `assign_sides`), `build_world.py` (2 klucze w `roads_qa.json`:
  `seam_tapers`, `seam_shoulders`).

## Wynik (dane z gita po scaleniu main feb542757; `docs/reports/SEAMS-2026-11-16.md`)
| szew | droga | nominalnie A \| B | na szwie | w kaflu |
|---|---|---|---|---|
| `dk65-11` \| `knyszyn-s` | w27718745 primary (trasa) | pobocze 0,35 + 0,75 \| 0,08 + 1,00 m (asfalt 7,30 \| 6,76 m) | 0,22 + 0,88 m (asfalt 7,04 m) | 13,5 m |
| `bialystok-kleeberga` \| `bialystok-maczka` | w272531949 service | jezdnia 5,50 \| 5,00 m | 5,25 m | 12,5 m |
| `bialystok-kleeberga` \| `bialystok-knyszynska` | w222579345 service | jezdnia 5,50 \| 6,00 m | 5,75 m | 12,5 m |
| `bialystok-kleeberga` \| `bialystok-knyszynska` | w224161424 service | jezdnia 5,00 \| 4,00 m | 4,50 m | 10,4 m (łańcuch 10,4 m) |
| `bialystok-kleeberga` \| `bialystok-knyszynska` | w561326924 trunk_link | jezdnia 5,50 \| 6,00 m | 5,75 m | 12,5 m |
| `knyszyn-s` \| `dw671-tykocin-01` | w98071886 unclassified | jezdnia 5,70 \| 5,50 m | 5,60 m | 10,0 m |

Plus 1 rampa wewnątrz kafla: `dk65-06`, łańcuch `c:w1151531610:10712325637-10712325634`, s = 1393 m, obie strony, 27 m.
`qa/seams.py`: FAIL 43 (`--no-taper`) → 19, PRZEJŚCIE 11; pozostałe szwy korytarza DK65 i `bialystok-industrial-c`: 0 przejść.
Asfalt na szwie 7,04 m zamiast 7,03 m: średnia części utwardzonej 21,5 cm zaokrąglona do 22 cm (ta sama w obu kaflach).

## Budżet
Siatka jezdni i pasów bocznych ma stacje co 2 m niezależnie od szerokości (`meshing.stations`), więc przejście nie zmienia
liczby trójkątów wstęgi ani profili bocznych. Zależne od kształtu krawędzi są tylko paski trawy za krawężnikiem
(`_emit_verge`, uproszczenie Douglasa-Peuckera 2,5 cm): na 12,5 m przejścia ≤ 7 stacji × 2 rzędy × 2 trójkąty ≈ ≤ 28 tris
na stronę. Szacunek (ESTIMATED, nie zmierzone — bez przebudowy): ≤ ~60 tris na koniec łańcucha, ≤ ~0,6 tys. tris łącznie
na 10 końców jezdni w 5 kaflach; przejścia pobocza (`dk65-11`, `knyszyn-s`, `dk65-06`) — 0 (profil wiejski nie ma paska trawy
za krawężnikiem, liczba stacji bez zmian). Kamery regionu C: **0** (żaden łańcuch `bialystok-industrial-c` nie ma przejścia — sąsiad
`bialystok-maczka` zgodny na wszystkich 7 drogach szwu; `streetscape_qa.json` / `mesh_budget.frame_estimate` bez zmian).
Czas `build_network` razem z wczytaniem grafów sąsiadów: 0,1–1,9 s na kafel (pomiar w chmurze, 21 kafli).

## Walidacja
- `tests/gis/test_seam_taper_0275.py`: syntetyczne 7,30 | 6,76 m (skok na szwie < 1e-9 m, L = 27 m, 13,5 m w kaflu,
  monotoniczność, ciągłość nachylenia, linia środkowa na osi), determinizm i niezależność od kolejności kafli, plan z
  samych końców sąsiada, krótki łańcuch, sekcje ADR 0095 pomijane, brak zmian przy zgodnych przekrojach; pobocza 0272
  (`dk65-opaska-k1` przeciw regule klasy: 4 warianty kierunku waya / łańcucha, strona w układzie świata, rampa wewnątrz kafla);
  dane z gita: każda droga przecięta szwem ma po `build_network` tę samą półszerokość po obu stronach, przejścia w parach,
  idempotencja, `seam_taper=False`.
- `tests/gis/test_seams_0224.py` (z #106, zaktualizowany): + przejście 0,2 m, + `lanes_follow_width`, + szew
  `dk65-11` | `knyszyn-s` bez FAIL na drodze trasy; xfail K1 zdjęty (0233 jest na main).
- `tests/gis/test_dk65_seam_knyszyn_0233.py::test_lane_follow_is_opt_in`: dopuszcza `lane_follow` pochodne z przejścia
  (`knyszyn-s`, `w98071886`).

## Otwarte
1. `RATIO` / `MIN_LEN_M` / `MAX_LEN_M` — ESTIMATED; do oceny na renderze szwów (lider) i ewentualnie pomiaru klinów na ortofoto.
2. Zmiana rodziny profilu na szwie (pobocze wiejskie ↔ krawężnik płaski): DK8 `w257367422` (`industrial-c` | `maczka`) i
   `w261104557` (`kleeberga` | `knyszynska`) — krawędź asfaltu różni się o 1,0 m (FAIL w raporcie). Wynika z reguły
   „fast” liczonej per łańcuch w `assign_sides`; poza zakresem (wymaga decyzji, która strona ma rację).
3. Wysokość (niweleta) na szwie nie jest mieszana (ADR 0214 „Otwarte 4”, różne roczniki NMT).
4. Przejście stoi w połowie w każdym kaflu — tam, gdzie kończy się override, a nie tam, gdzie w terenie zmienia się
   nawierzchnia (jak styk km 25,32 z ADR 0233, który jest autorskim profilem `width`). Znany styk w terenie → profil `width`.
5. `generated/*` nieprzebudowane (zakaz rundy 5): kafle `dk65-06`, `dk65-11`, `knyszyn-s`, `dw671-tykocin-01`,
   `bialystok-kleeberga`, `bialystok-knyszynska`, `bialystok-maczka` wymagają `build_world`, żeby przejścia stanęły w
   geometrii; `roads_qa.json` nie ma jeszcze kluczy `seam_tapers` / `seam_shoulders`. Render szwów — lider.

## Odtworzenie
```
uv run --project tools/worldgen python -m pytest tests/gis -k "seam or taper or 0275 or 0224" -q
uv run --project tools/worldgen python -m tools.worldgen.qa.seams --json docs/reports/SEAMS-2026-11-16.json --md <plik.md>   # --no-taper: kafle osobno
```
