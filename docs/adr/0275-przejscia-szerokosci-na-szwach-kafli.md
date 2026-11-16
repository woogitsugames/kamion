# ADR 0275 — Przejścia szerokości jezdni i pobocza na szwach kafli i na końcu override (`roads/seam_taper.py`)
Status: Proposed (chmura D, runda 5, zadanie D15, gałąź `seam-taper-0275`; bez Unity i bez `Data/raw`), 2026-11-16. Do scalenia przez lidera.
Powiązane: ADR 0224 (QA szwów, `qa/seams.py` — tym PR wchodzi do gita), 0233 (`lanes_follow_width`), 0272 (pobocze jako
dane, `roads/xsec.py` — **nie na main**, treść w `rail-dk65-s22`), 0214 / 0220 (przekrój K1), 0095 (profil `width`),
decyzja lidera s23 (HANDOVER 16.11 05:5x: szew `dk65-11` | `knyszyn-s` bez override w `knyszyn-s`, przejście jako osobna poprawka).

## Kontekst
Kafel buduje drogi z własnego grafu i własnych overrides. Gdy przekrój autorski kończy się na szwie, obie połowy drogi
spotykają się ze skokiem krawędzi. Przypadek z zadania (stan `rail-dk65-s22`): `dk65-opaska-k1` w `dk65-06…11` daje
6,6 m jezdni + 2 × 0,35 m asfaltu = 7,30 m, a w `knyszyn-s` reguła 0272 `g-single-ground` daje 6,6 + 2 × 0,08 = 6,76 m →
skok 0,27 m na stronę (krawędź gruntu: 4,40 | 4,38 m od osi). Na main (bez 0272) skoki są w szerokości jezdni:
5 dróg na szwach kafli miejskich i `knyszyn-s` | `dw671-tykocin-01` (0,10–0,50 m na stronę, tabela w „Wynik”).
Ten sam skok powstaje **wewnątrz** kafla, gdy override pobocza obejmuje część wayów łańcucha (kody `mat` 0272 zmieniają się
na granicy sekcji w jednej stacji; szerokość jezdni ma tam już wygładzanie 15 m z `prepare_chain`).

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
   - z ADR 0272: szerokości utwardzonej i gruntowej części pobocza w kodzie `mat` stacji (`apply_shoulders`, po każdym
     `assign_sides`), rozdzielczość 1 cm; ta sama funkcja zamienia skok kodów między sekcjami jednego łańcucha (koniec
     override wewnątrz kafla) na krzywą S wyśrodkowaną na skoku. Bez `roads.xsec` funkcja nic nie robi.
   Nie jest mieszana zmiana rodziny profilu (krawężnik ↔ pobocze) — to zostaje FAIL w `qa/seams.py`.
4. **`qa/seams.py` (z PR #106, ADR 0224) w gicie**, zaktualizowane: buduje sieci jak generator łącznie z przejściami
   (`build_nets`), więc wiersze szerokości porównują to, co stoi na szwie; nowe wiersze `krawędź asfaltu L/P [m od osi]`
   z tolerancją 0,02 m; wiersz `przejście szerokości (ADR 0275)` ze statusem **PRZEJŚCIE** (dane nominalne różne, generator
   je łączy) i wartościami nominalnymi; `--no-taper` pokazuje kafle osobno. `lanes_follow_width`: wiersz „pasy × szer.
   pasa” liczy lokalną szerokość pasa `lane_w_at(hw)` (fałszywy FAIL „3,10 vs 3,55” na `dk65-11` | `knyszyn-s` znika);
   „szer. jezdni ostatni build” jest N/D dla sekcji z profilem szerokości (`roads_qa` niesie maksimum sekcji).
   Override `seam-knyszyn-s-field-road-98071886` z #106 **nie** został przeniesiony (szerokość łączy przejście; oświetlenie
   tej drogi zostaje FAIL do decyzji).

## Styk z ADR 0272 / `rail-dk65-s22`
- Ten PR nie kopiuje 0272. `seam_taper.py` importuje `roads.xsec` opcjonalnie (`X = None` na main); po scaleniu z
  `rail-dk65-s22` część „pobocze” włącza się sama. Sprawdzone na próbnym scaleniu `origin/rail-dk65-s22` (cbe8e416e) +
  ta gałąź (bez konfliktów; `network.py`, `meshing.py`, `rail_approach.py` nietknięte przez ten PR): szew `dk65-11` |
  `knyszyn-s` — krawędź asfaltu 3,65 | 3,38 m (FAIL, `--no-taper`) → **3,52 | 3,52 m**, pobocze 0,22 + 0,88 m po obu
  stronach; testy poboczy (6, na main pomijane) zielone.
- Pliki wspólne: `pipeline.py` (3 linie po `abreast_forks` i po obu `assign_sides`), `build_world.py` (2 klucze w
  `roads_qa.json`: `seam_tapers`, `seam_shoulders`). `meshing.build_side_strip` czyta `mat` per stacja (0272), więc kody
  zmieniające się co stację nie wymagają zmian w siatce.

## Wynik (dane z gita, main 639da4e54; `docs/reports/SEAMS-2026-11-16.md`)
| szew | droga | jezdnia nominalna A \| B | na szwie | w kaflu |
|---|---|---|---|---|
| `bialystok-kleeberga` \| `bialystok-maczka` | w272531949 service | 5,50 \| 5,00 m | 5,25 m | 12,5 m |
| `bialystok-kleeberga` \| `bialystok-knyszynska` | w222579345 service | 5,50 \| 6,00 m | 5,75 m | 12,5 m |
| `bialystok-kleeberga` \| `bialystok-knyszynska` | w224161424 service | 5,00 \| 4,00 m | 4,50 m | 10,4 m (łańcuch 10,4 m) |
| `bialystok-kleeberga` \| `bialystok-knyszynska` | w561326924 trunk_link | 5,50 \| 6,00 m | 5,75 m | 12,5 m |
| `knyszyn-s` \| `dw671-tykocin-01` | w98071886 unclassified | 5,70 \| 5,50 m | 5,60 m | 10,0 m |

Korytarz DK65 (`dk65-01…11`, `knyszyn*`, `dk65-monki-01`) na main: 0 przejść (szerokości zgodne); po `rail-dk65-s22`
dojdzie para `dk65-11` | `knyszyn-s` (pobocze). `bialystok-industrial-c`: 0 przejść.

## Budżet
Siatka jezdni i pasów bocznych ma stacje co 2 m niezależnie od szerokości (`meshing.stations`), więc przejście nie zmienia
liczby trójkątów wstęgi ani profili bocznych. Zależne od kształtu krawędzi są tylko paski trawy za krawężnikiem
(`_emit_verge`, uproszczenie Douglasa-Peuckera 2,5 cm): na 12,5 m przejścia ≤ 7 stacji × 2 rzędy × 2 trójkąty ≈ ≤ 28 tris
na stronę. Szacunek (ESTIMATED, nie zmierzone — bez przebudowy): ≤ ~60 tris na koniec łańcucha, ≤ ~0,6 tys. tris łącznie
na 10 końców w 5 kaflach. Kamery regionu C: **0** (żaden łańcuch `bialystok-industrial-c` nie ma przejścia — sąsiad
`bialystok-maczka` zgodny na wszystkich 7 drogach szwu; `streetscape_qa.json` / `mesh_budget.frame_estimate` bez zmian).
Czas `build_network` razem z wczytaniem grafów sąsiadów: 0,1–1,9 s na kafel (pomiar w chmurze, 21 kafli).

## Walidacja
- `tests/gis/test_seam_taper_0275.py`: syntetyczne 7,30 | 6,76 m (skok na szwie < 1e-9 m, L = 27 m, 13,5 m w kaflu,
  monotoniczność, ciągłość nachylenia, linia środkowa na osi), determinizm i niezależność od kolejności kafli, plan z
  samych końców sąsiada, krótki łańcuch, sekcje ADR 0095 pomijane, brak zmian przy zgodnych przekrojach; pobocza 0272
  (4 warianty kierunku waya / łańcucha, strona w układzie świata, rampa wewnątrz kafla) — pomijane bez `roads.xsec`;
  dane z gita: każda droga przecięta szwem ma po `build_network` tę samą półszerokość po obu stronach, przejścia w parach,
  idempotencja, `seam_taper=False`.
- `tests/gis/test_seams_0224.py` (z #106, zaktualizowany): + przejście 0,2 m, + `lanes_follow_width`, + szew
  `dk65-11` | `knyszyn-s` bez FAIL na drodze trasy; xfail K1 zdjęty (0233 jest na main).

## Otwarte
1. `RATIO` / `MIN_LEN_M` / `MAX_LEN_M` — ESTIMATED; do oceny na renderze szwów (lider) i ewentualnie pomiaru klinów na ortofoto.
2. Zmiana rodziny profilu na szwie (pobocze wiejskie ↔ krawężnik płaski): DK8 `w257367422` (`industrial-c` | `maczka`) i
   `w261104557` (`kleeberga` | `knyszynska`) — krawędź asfaltu różni się o 1,0 m (FAIL w raporcie). Wynika z reguły
   „fast” liczonej per łańcuch w `assign_sides`; poza zakresem (wymaga decyzji, która strona ma rację).
3. Wysokość (niweleta) na szwie nie jest mieszana (ADR 0214 „Otwarte 4”, różne roczniki NMT).
4. Przejście stoi w połowie w każdym kaflu — tam, gdzie kończy się override, a nie tam, gdzie w terenie zmienia się
   nawierzchnia (jak styk km 25,32 z ADR 0233, który jest autorskim profilem `width`). Znany styk w terenie → profil `width`.
5. `generated/*` nieprzebudowane (zakaz rundy 5): `roads_qa.json` nie ma jeszcze kluczy `seam_tapers` / `seam_shoulders`.

## Odtworzenie
```
uv run --project tools/worldgen python -m pytest tests/gis -k "seam or taper or 0275 or 0224" -q
uv run --project tools/worldgen python -m tools.worldgen.qa.seams --json docs/reports/SEAMS-2026-11-16.json --md <plik.md>   # --no-taper: kafle osobno
```
