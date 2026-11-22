# ADR 0327 — Budżet trójkątów kafla C po fali 7: decymacja spękań, margines 1,99 -> 2,00 M

Status: propozycja (gałąź `budget-w7-s24`, nie scalone). Źródło: 4 czerwone testy budżetu po fali 7 (ADR 0323-0326).

## Kontekst

Estymata klatki (`build_world.mesh_budget`, model „legacy”: wszystko w 1,6 km, bez okluzji) kamery `stretch_04` kafla
`bialystok-industrial-c` wzrosła z 1 978 101 (fala 6) do **2 013 521** (fala 7): roads +26 217 (zalewki i spękania ADR
0323 — `markings` w regionie 100 612 -> 149 848), forest_hlod +3 835 (druga ściana ADR 0324), terrain +2 784 (rów),
props +1 449, water +1 069 (kępy trawy `verge_tufts`). Limity: 2 000 000 (`test_hero_bridge`, `test_typology_0238`,
`test_world_v31`) i 1 990 000 (`test_budget_0221::test_region_c_frame_budget_has_margin`, margines 0,5 %).

## Decyzja

1. **Decymacja polilinii spękań** (`roads/decals.py: _decimate_polyline`, wywołana w `seal_band`): Douglas-Peucker w układzie
   łańcucha (s wzdłuż, lat w poprzek), tolerancja = 0,25 szerokości pasa (3-5 cm zalewka, 1,5 cm włosowate), cięciwa
   <= 3 m, zawsze wierzchołek przy koronie jezdni. Wysokość liczona na nowo w każdym zachowanym wierzchołku. Gęstość,
   szerokość, materiał i reguły rozmieszczenia bez zmian (tylko mniej wierzchołków na tej samej linii). Tolerancja 0,6
   (−41 % więcej) odrzucona: prostuje spękania (decyzja lidera).
2. **Margines testu `test_region_c_frame_budget_has_margin`: 1 990 000 -> 2 000 000** (zrównany z pozostałymi trzema
   testami i bezpiecznikiem 2 M z docs/06 §6). Uzasadnienie pomiarem — niżej.

## Wyniki

- Region C (przebudowa na kodzie gałęzi): `decals.seal_cracks` 20 398 trójkątów (1 043 spękania; przed decymacją ok. 49 000),
  `markings` 149 848 -> 123 508. `stretch_04`: **2 013 521 -> 1 996 151** (roads 624 990 -> 607 620). Syntetycznie
  (4 x 900 m klasy L) −58 % trójkątów spękań. Zostaje 6 151 trójkątów (0,3 %) ponad stary margines 1,99 M.
- Pomiar playera (build #5 `0.1.0 (770ea8d900)`, `-regions`, scena `knyszyn-w`, 1920x1080, 90 s, `pc-metrics.ps1`;
  `artifacts/full-build-5-s24/pc/20261122-180753` i `...-180954`). Build #5 ma spękania **bez** decymacji.
  Maszyna: GTX 1070, i5-10400F — **nie referencyjna**, wynik informacyjny (kind=informational, gate_eligible=false),
  progi WORKING_VALUE:

  | klasa | tier / FPS | GPU p50 / p95 / p99 [ms] | klatka p50 / p95 / p99 [ms] | CPU gł. p95 [ms] | trójkąty p95 | draw calls p95 |
  |---|---|---|---|---|---|---|
  | zalecany | High / 60 | 7,29 / 7,82 / 8,32 | 16,67 / 16,67 / 16,67 | 4,37 | 3 165 136 | 1 462 |
  | min | Low / 30 | 9,75 / 11,02 / 11,26 | 33,33 / 33,34 / 33,34 | 4,56 | 1 041 804 | 775 |

  Zapas: High/60 GPU p95 = 47 % budżetu klatki 16,67 ms; Low/30 GPU p95 = 33 % z 33,3 ms. 14 klatek (0,27 %) > 16,7 ms
  przy High, 0 > 33,3 ms. Scena pomiaru dźwiga 3,17 M trójkątów (p95), więc różnica 6 151 (0,3 %) w estymacie C jest
  poniżej szumu pomiaru.
- Ograniczenia pomiaru: scena `knyszyn-w`, nie kafel C (`stretch_04`); jedna maszyna, GPU słabsze od zalecanej klasy
  D74 (więc zapas na zalecanej będzie nie mniejszy), ale to nie jest dowód na referencję. Estymata „legacy” liczy też
  geometrię, której runtime nie rysuje (LOD: `markings` znika na LOD2, kępy trawy tylko < 500 m).
- Testy: patrz STATUS.md (`tests/gis` 1-4, 6, 7 po przebudowie C).

## Konsekwencje

- Estymata `stretch_04` ma 3 849 trójkątów (0,2 %) zapasu do 2 M: kolejna fala dodająca geometrię w kadrze C wymaga
  decymacji lub osobnej decyzji; ratchet nie rośnie powyżej 2 000 000.
- Zmiana kształtu spękań: mniej wijące się w skali < 3-5 cm (poniżej szerokości pasa); do oceny wzrokowej
  (`artifacts/budget-w7-s24/vqa`).
- Otwarte: cięcie drugiej ściany lasu / kęp trawy (~1,5 tys.) nie zrobione; pomiar `stretch_04` w playerze (kamera trasy
  kafla C) poza zakresem.

## Ocena wzrokowa (visual-qa, kafel C, High 1920x1080, clear; edytor, nie player)

Przed = dane fali 7 (spękania bez decymacji), po = ta gałąź; ten sam import, te same kamery
(`artifacts/budget-w7-s24/vqa/crack-before|crack-after`, kamery `crack_*` ustawione na pasach `decal_seal`, wysokość oka 1,1 i 2,5 m).
Pary `crack_a_low` i `crack_c_low`: spękania (poprzeczne, podłużne, łata) wyglądają tak samo; różnicy nie widać gołym
okiem. Kamery standardowe (`stretch_01..04`, `route_putry_approach`, `driver_andersa_to_putry`, `.../vqa/after`): w kabinie
spękań prawie nie widać (kafel C = drogi klasy A/S/GP, niska stawka) — bez zmian względem „przed". Brak oceny visual-critic
(subagent nie uruchamia subagentów); ocena własna agenta.
