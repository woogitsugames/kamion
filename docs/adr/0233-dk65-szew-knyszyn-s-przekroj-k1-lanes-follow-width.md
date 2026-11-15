# ADR 0233 — DK65: jeden przekrój K1 przez szwy `dk65-10` | `dk65-11` | `knyszyn-s`, poszerzenie na km 25,32 (`lanes_follow_width`)
Status: Proposed (agent world-builder `dk65-r4-s21`, s21, gałąź `dk65-r4-s21`), 2026-11-15. Do scalenia przez lidera.
Powiązane: ADR 0214 (kafle 06…11, „Otwarte 1”: skok 0,45 m/stronę na szwie 10/11), 0204 / 0212 (przekrój DK65 w `knyszyn*`:
7,5 m, linie 7,1 m), 0220 (K1 w kaflach 01–05, `edge_line_spacing` — nie na main), 0095 (profil `width` wzdłuż krawędzi),
research K1 `research/dk65-knyszyn-refs/README.md`, D63–D67 (`docs/11`).

## Kontekst
ADR 0214 dał kaflom `dk65-06…10` przekrój K1 (2 × 3,1 + 2 × 0,2 = 6,6 m → linie krawędziowe 6,2 m), a `dk65-11` zostawił na
zestawie `knyszyn-s` (7,5 m → linie 7,1 m), żeby szew z `knyszyn-s` był identyczny. Skutek: skok przekroju na szwie 10/11
(osobne sceny, brak wygładzenia) i przekrój niezgodny z K1 na szwie 11/`knyszyn-s` (K1: km 24,6 = 6,0 m, km 25,0 = 6,1 m).

**Pomiar** (ortofoto GUGiK WMS HighResolution 0,1 m, arkusze 2025-05-25/27; wyprostowany pasek wzdłuż osi OSM km 24,05–26,15,
para linii krawędziowych w blokach 10 m; `artifacts/dk65-r4-s21/tools/seam_strip.py`, wynik `seam/ortho/seam_strip.json`,
obejrzane `view_330_520.jpg`, `view_800_1100.jpg`):

| odcinek (km trasy A) | kafel | rozstaw linii krawędziowych (mediany 100 m) |
|---|---|---|
| 24,05–24,65 | `dk65-10`, `dk65-11` | 6,0 m |
| 24,65–25,31 | `dk65-11`, `knyszyn-s` (szew km 24,83) | 6,2 m (bloki 6,0–6,3; przy zatoce/zjazdach km 24,85–24,93 odczyty 6,5–6,8 od krawędzi zjazdu) |
| 25,32–25,49 | `knyszyn-s` | 7,1–7,5 m, linie **przerywane** — od styku nawierzchni (nowa warstwa) 862–874 m za szwem 10/11 |
| 25,49–26,15 | `knyszyn-s` | 6,7–6,8 m, linie ciągłe (przekrój z ADR 0204 / 0212) |

Czyli przekrój K1 kończy się nie na szwie kafli ani na granicy drogi OSM (way 27718745 kończy się na km 25,65), tylko na
styku nawierzchni km 25,32 — **484 m w głąb krawędzi grafu `w27718745:897574813-1134817563` w `knyszyn-s`**.

**Stan zbudowany przed zmianą** (`tools/worldgen/qa/seam_section.py` na chunkach GLB, przekroje 2 m od szwu):

| szew | asfalt A \| B | linie A \| B | Δ wysokości osi | Δ boczne punktu trasy |
|---|---|---|---|---|
| `dk65-10` \| `dk65-11` | 8,60 \| 9,50 m | 6,22 \| 7,10 m | +0,082 m | 0,149 m |
| `dk65-11` \| `knyszyn-s` | 9,50 \| 9,50 m | 7,10 \| 7,10 m (K1: 6,0–6,4) | 0,000 m | 0,000 m |

## Decyzja
1. **`dk65-11`**: wpis `dk65-xsec-k1` dosłownie z `dk65-06…10` zamiast `dk65-carriageway-width` (test „verbatim 06…11”).
2. **`knyszyn-s` — jedyna zmiana danych tego kafla** (poza kamerami, p. 4): nowy wpis `dk65-k1-section-to-km25.32` **po**
   wspólnym `dk65-carriageway-width` (ten zostaje nietknięty — identyczny w `knyszyn`, `knyszyn-w`, `dk65-monki-01`),
   cel = jedna krawędź `w27718745:897574813-1134817563`:
   `set: {edge_strip: 0.2, lanes_follow_width: true, width: [[0, 6.6], [0.586, 6.6], [0.601, 7.5], [1, 7.5]]}` —
   pierwsze 484 m = przekrój K1 (6,6 m → linie 6,2 m), przejście 12 m (+ 15 m wygładzania szerokości generatora), dalej
   7,5 m jak dotąd. `width` sekcji (maksimum profilu) zostaje 7,5 m, więc testy 0204 / 0212 / 0209 przechodzą bez zmian.
   Linie przerywane km 25,32–25,49 malowane jako ciągłe (jak wszędzie — „Otwarte”).
3. **Generator — nowy klucz `lanes_follow_width`** (`roads/network.py`: `EdgeSection.lane_follow`, `lane_w_at(hw)`).
   Profil `width` z ADR 0095 opisuje pas, który poszerza się przy wysepce: układ pasów trzyma szerokość pasa z
   najszerszego miejsca. Tu zmienia się cały przekrój drogi dwukierunkowej — przy starej regule linia środkowa
   wyszłaby 0,45 m obok osi (`lat_c = −hw + edge_strip + lanes_fwd × lane_w`), a punkt trasy 0,30 m od punktu w `dk65-11`.
   Z `lanes_follow_width` pasy dzielą **lokalną** szerokość: `lane_w_at(hw) = (2·hw − 2·edge_strip) / lanes` — linia
   środkowa na osi, środki pasów ±1,55 m (K1) → ±1,775 m (7,5 m). Użyte w: `markings.lane_layout` (linie, trasa, QA
   spójności, strzałki), punkt trasy w `build_world`, łaty i koleiny (`decals`), UV zużycia (`meshing`, `_paint_uv1`).
   **Bez klucza `lane_w_at()` zwraca `lane_w` — żaden inny region się nie zmienia** (test `test_lane_follow_is_opt_in`).
   Podział krawędzi grafu w locie odrzucony: identyfikatory krawędzi czytają trasa, navgraph, QA i testy szwów.
4. **Kamery szwu** (`artifacts/dk65-r4-s21/tools/seam_cams.py` → `control_cameras_place.authored.json`; dopisane, nic
   nie usunięte): widoki z góry 66,3 × 37,3 m (oko 40 m, fov 50) wyśrodkowane **na punkcie szwu** — ten sam kadr w obu
   kaflach szwu (każdy rysuje swoją połowę): `seam_n_top40` (10), `seam_s_top40`, `seam_w_top40` (11), `seam_e_top40`,
   `k1_widening_top40` (`knyszyn-s`) + widoki kierowcy `seam_n_drive`, `seam_s_drive`, `seam_w_drive`, `seam_e_drive`,
   `k1_widening_drive`. Pary: ortofoto WMS 0,1 m tego samego kadru (`seam/ortho/pair_*.jpg`), sklejki
   `seam/<tag>/seam-<a>-<b>-<tier>.jpg`.
5. **Narzędzie QA `tools/worldgen/qa/seam_section.py`**: przekrój zbudowanej jezdni po obu stronach szwu z chunków GLB
   (asfalt, osie linii, wysokość osi ekstrapolowana do szwu, boczne położenie punktu trasy).

## Wynik (r4)
Stan zbudowany po przebudowie r4 (`seam_section.py`, `artifacts/dk65-r4-s21/seam/built_after_r4.json`, przekroje 2 m od szwu):

| szew | asfalt A \| B | linie A \| B | Δ wysokości osi | punkt trasy A \| B (Δ) |
|---|---|---|---|---|
| `dk65-10` \| `dk65-11` | 8,60 \| 8,60 m | 6,22 \| 6,20 m | +0,082 m (bez zmian, „Otwarte 4”) | −1,55 \| −1,55 m (0,00) |
| `dk65-11` \| `knyszyn-s` | 8,58 \| 8,58 m | 6,20 \| 6,19 m | 0,000 m | −1,549 \| −1,549 m (0,00) |

Asfalt 8,6 m = jezdnia 6,6 m + 2 × 1,0 m pobocza utwardzonego profilu zamiejskiego („Otwarte 5”). Załom osi 0,0° / 0,001°.
Przebudowane i zaimportowane (Low + High): `dk65-07…11`, `knyszyn-s`. `dk65-06`: po scaleniu `origin/main` (b4e42ef34)
obowiązuje `generated` z main (Ełcka 6,6 m, D66) — przebudowa r4 tego kafla z tej gałęzi (Ełcka 6,9 m) odrzucona; zmiana
`dk65-06/overrides.yaml` z tej gałęzi to wyłącznie komentarz. `generated` kafla `knyszyn-s` nie jest commitowane
(tylko `overrides.yaml`, kamery authored, `route_start.json`, `region_catalog.json`: routeLengthM 2420,66 → 2420,72) —
lider przebudowuje `knyszyn-s` po scaleniu.
Kafle 07…11 zbudowano generatorem sprzed scalenia main (tunnel-0211, construction 0215, cycleways) — po scaleniu nie
przebudowywano; `lane_w_of()` (poprawka po pełnym pytest) nie zmienia wyniku dla `EdgeSection`.

## Budżet
Draws / tris: nie mierzono (zmiana szerokości przekroju, bez nowych obiektów; telefon poza zadaniem). `WORLD_MEMORY`
z `artifacts/dk65-r4-s21/logs/import-<kafel>-r4.log` (Low / High, MB razem): `dk65-07` 61,2 / 138,6; `dk65-08` 57,8 / 125,1;
`dk65-09` 54,4 / 125,3; `dk65-10` 50,9 / 119,2; `dk65-11` 50,0 / 114,8; `knyszyn-s` 41,4 / 107,5. Porównania A/B z r3 nie
ma (logi r3 nie zawierają tej linii w tym worktree) — UNVERIFIED, że bez zmian.

## Walidacja
- `tests/gis/test_dk65_seam_knyszyn_0233.py` + `test_dk65_seams_0214.py` po scaleniu main: 39 passed (w tym geometria
  zbudowana obu szwów, tolerancja 0,1 m).
- Pełny `pytest tests/gis` (po scaleniu main, przebieg 1): 1420 passed, 7 failed, 3 xfailed. 6 błędów = sekcje
  duck-typed w testach bez `lane_w_at` / `lane_follow` → poprawione (`network.lane_w_of`, 92 passed na tych plikach).
  7.: `test_road_fidelity.py::test_report_not_stale` — `fidelity_qa.json` (`bialystok-industrial-c`) nieaktualny już na
  `origin/main` (5 plików generatora), nie z tego zadania. Przebieg 2: <!-- PYTEST2 -->
- EditMode: 628 testów, 626 passed, 1 skipped, 0 failed (po `scripts/export-region-catalog.py`; przed: 1 failed —
  `knyszyn-s` routeLengthM), `artifacts/tests/editmode-20261115-2149*.xml`.
- Pętla wizualna (Low + High, 1920 × 1080, clear): `artifacts/dk65-r4-s21/seam/r4/seam-*-{low,high}.jpg` (sklejka obu
  połówek szwu | ortofoto WMS 0,1 m), `widening-knyszyn-s-*.jpg`, `<kafel>/r4/view/grid-*.jpg`. Obejrzane: oba szwy —
  krawędzie asfaltu, linie krawędziowe i oś przechodzą przez szew bez uskoku; poszerzenie km 25,32 jako płynny klin.
  Różnice wobec ortofoto: linie przerywane / podwójna ciągła („Otwarte 1”), pobocze utwardzone szersze niż w terenie.
  Wada kamer: `seam_s_drive` (11) i `seam_e_drive` (`knyszyn-s`) stoją wewnątrz naczepy ciężarówki QA (start trasy =
  punkt szwu) — kadr bezużyteczny („Otwarte 7”). `visual-critic`: nie uruchamiano (do lidera).

## Otwarte
1. Linie krawędziowe przerywane km 25,32–25,49 (nowa nawierzchnia, kreski szerokie) i przy zjazdach / zatoce km 24,85–25,0;
   podwójna ciągła na osi przy szwie 11/`knyszyn-s` (ortofoto) — generator maluje ciągłe krawędziowe i przerywaną oś.
   Mechanizm `edge_line_dashed` jest w ADR 0220 (nie na main).
2. Oś jezdni względem osi OSM: +0,5…+0,9 m (w lewo w kierunku Knyszyna) na km 24,85–25,05, poza tym ±0,3 m — bez
   `center_offset` (wymagałoby tej samej wartości po obu stronach szwu).
3. Odcinek 7,1–7,5 m (km 25,32–25,49) zbudowany jako 7,1 m; 6,7–6,8 m dalej też 7,1 m (WORKING_VALUE z 0212).
4. Δ wysokości osi na szwie 10/11 wynika z roku NMT (10: 2025, 11: 2022 — pin z ADR 0214); mieści się w ±0,1 m, ale
   teren obok jezdni różni się tam do 0,48 m (bez zmian).
5. Pobocze utwardzone 1,0 m profilu zamiejskiego (asfalt 8,6 m przy zmierzonych ~7,1–7,5 m) — parametr globalny, jak w 0214.
6. Telefon: nie mierzono (zadanie bez adb). `visual-critic`: do lidera.
7. Kamery `seam_s_drive` / `seam_e_drive` wewnątrz naczepy ciężarówki QA — przesunąć oko ≥ 25 m przed punkt szwu
   (`seam_cams.py`) i wyrenderować ponownie.

## Odtworzenie
```
uv run --project tools/worldgen python artifacts/dk65-r4-s21/tools/seam_strip.py . artifacts/dk65-r4-s21/seam/ortho     # pasek WMS 0,1 m
uv run --project tools/worldgen python artifacts/dk65-r4-s21/tools/seam_cams.py --ortho artifacts/dk65-r4-s21/seam/ortho  # kamery + pary
pwsh artifacts/dk65-r4-s21/tools/chain.ps1 -Tiles dk65-10,dk65-11,knyszyn-s -Tag r4 -High                               # build_world + import + vqa
uv run --project tools/worldgen python tools/worldgen/qa/seam_section.py artifacts/dk65-r4-s21/seam/built_after_r4.json after-r4
uv run --project tools/worldgen python -m pytest -q tests/gis/test_dk65_seam_knyszyn_0233.py tests/gis/test_dk65_seams_0214.py
```
