# ADR 0288 — pętla S8 ↔ DW671 ↔ Tykocin: 15 kafli, pierwsze 5 zbudowane, przekrój S8 klasy S

Status: Proposed (agenci s8-loop-s23 / s23b / s23c, 2026-11-16…17). Numer potwierdzony przez lidera (0287 = knyszyn-look).
Powiązane: D82 (kierunek Podlasia), D63 (najpierw przejezdne), D64 (zgoda na S8), ADR 0203 (siatka kafli 2048 m),
0278 (plan mapy, kafel `dk8-s8-jeroniki`), 0231 (pierścień Tykocin/Mońki), 0235 (streaming), 0272 (pobocza, pomiar
z ortofoto), 0275 (przejścia przekroju na szwach), 0285 (trasy łączące), `docs/owner/MAP-DECISIONS-2026-11-16.md` (b),
research `research/mistral-s8-loop-s23/` + kontrola `docs/reports/QA-2026-11-16-mistral-s8.md`.

## Decyzja
1. **15 kafli pętli** na siatce ADR 0203 (x = 776971 + 2048·i, y = 595199 + 2048·j), w kolejności jazdy od `dk65-01`:
   `s8-01` (−5,0; węzły Białystok Zachód i Choroszcz), `s8-02` (−6,0), `s8-03` (−7,0; węzeł Tykocin), `s8-04` (−8,0),
   `s8-05` (−9,0), `s8-06` (−9,−1), `s8-07` (−10,−1; węzeł Rzędziany), `s8-08` (−11,−1), `s8-09` (−12,−1),
   `s8-10` (−12,−2), `s8-11` (−13,−2; węzeł Jeżewo), `s8-12` (−14,−2), `dw671-jezewo-01` (−13,−1), `-02` (−13,0),
   `-03` (−13,1). Rejestr: `tools/worldgen/regions.py` (blok ADR 0288), plan i trasy kontrolne:
   `tools/worldgen/qa/s8_loop_plan.py` → `docs/reports/map/s8_loop_plan.{json,png}` (trasy kontrolne łącznie 26,07 km,
   ten sam przypięty pbf co `build_region.py`), test `tests/gis/test_s8_loop.py`.
2. **Zbudowane teraz: `s8-01` … `s8-05`** (ingest → build_region → build_world → export-route → import Win64). Pozostałe
   10 kafli = sama definicja (`overrides.yaml`, `route_endpoints.json`); `s8-09…12` i `dw671-jezewo-*` leżą na zachód od
   okna OSM potoku (22,80 E) — wymagają szerszego `osm_extract.BBOX_WGS84` (jest na gałęzi world2-s23).
3. **Przekrój S8 jako `authored_overrides`** generowane skryptem `tools/worldgen/qa/s8_xsec_overrides.py` (blok między
   znacznikami w `Data/Regions/s8-0x/overrides.yaml`, `--check` w CI): jezdnia klasy S zamiast reguły klasy A
   wyśrodkowanej na way OSM. Od krawędzi przy pasie dzielącym: opaska 0,20 m, n × 3,50 m, 2,75 m utwardzone
   (pas awaryjny 2,50 m + 0,25 m do osi linii) → jezdnia 9,95 m (2 pasy) / 13,45 m (3 pasy); po stronie pasa
   dzielącego generator dokłada 0,50 m asfaltu (`PAVED_SHOULDER_MEDIAN`), więc asfalt 2-pasowej jezdni = 10,45 m.
   Oś dwóch pasów głównych 0,25 m w lewo od way OSM; trzeci pas (włączania / wyłączania) dochodzi z zewnątrz.
   Pas dzielący: trawa + żwirowa opaska, bez krawężnika; bariera stalowa jak dotąd z reguły generatora.
   **s24 (17.11, nowy PC): przesunięcie per way do pasa dzielącego.** Rozstaw osi jezdni z grafu (p50 odległości do
   najbliższej jezdni S8 przeciwnego kierunku, próbki co 10 m po wszystkich kaflach — jedna wartość na way, więc way
   przez szew ma to samo przesunięcie po obu stronach). Gdy odstęp linii wewn. bez korekty (rozstaw − 7,5 m) > 4,8 m
   i rozstaw ≤ 12,8 m, jezdnia przesuwa się dodatkowo o (rozstaw − 12,0)/2, krok 0,05 m, max 0,5 m → cel 4,5 m (QA
   wiersz 78). Rozstaw > 12,8 m (jezdnie na osobnych obiektach / rozchodzące się w węźle) bez zmian. Dotyczy 8 way
   (s8-04: 100133887 +0,25, 251431118 +0,15). Odrzucone warianty: próg 13,0 m (way 536222216-218 w s8-02 dostały
   +0,45/+0,50 między way z 0 → P-7b na trawie, r8) i korekta także w zakresie (+0,1 m na way 183625710/305447698 →
   5 próbek P-7b na trawie w s8-02, r9); oba usunięte (r10: 0).
4. **Brak włazów kanalizacyjnych w jezdni klas A/S**: `roads/xsec_rules.yaml` → `drainage.no_manhole_classes: [A, S]`
   (czytane w `streetscape/fab_details.py`; moduły `roads/*.py` bez zmian, więc raporty fidelity innych kafli nie tracą ważności). To jedyna zmiana kodu generatora; dotyczy też
   innych kafli z `highway=motorway` przy ich następnej przebudowie.
5. **Streaming:** `tile_graph.py` — korytarz `s8-01..s8-05` (4 portale, przerwa 0,0 m), pamięć z importu Win64
   17.11; `Data/Streaming/route_links.yaml` — link `dk65-01-s8-corner` (S8 przez narożnik `dk65-01`, 578 m),
   link `s8-03-to-s8-04` (trasy kontrolne obu kafli leżały o jeden pas od siebie na szwie: 3,5 m), korytarz `s8-loop`.
6. **Katalog:** 5 wpisów w `region_catalog.json`, nowa grupa „S8”.

## Liczby i źródła
| wielkość | wartość | źródło |
|---|---|---|
| asfalt jezdni 2-pasowej S8 | 10,35–10,65 m | QA 16.11 wiersze 81, 82 (ortofoto GUGiK WMS, ±0,3 m) |
| odstęp wewn. linii krawędziowych (pas dzielący) | 3,8–4,85 m, mediana ~4,5 | QA wiersz 78 (8 stacji) |
| odstęp krawędzi asfaltu | 3,45–4,0 m, mediana 3,6 | QA wiersz 78 |
| rozstaw osi jezdni (OSM) | p50 12,12 m (s8-02), 12,52 m (s8-04) | `roads.graph.json`, pomiar skryptem 17.11 |
| pas ruchu S | 3,50 m | PTB2022 (Dz.U. 2022 poz. 1518) § 17 ust. 1 |
| pas awaryjny S | 2,50 m | PTB2022 § 23 ust. 6 |
| pobocze gruntowe przy pasie awaryjnym | 1,25 m | PTB2022 § 23 ust. 10 pkt 1 |
| DW671 asfalt (kafle `dw671-jezewo-*`, do użycia) | mediana 6,95 m | QA 16.11 (stacje „czyste”, ADR 0272) |
| opaska 0,20 m, 0,25 m do osi linii, przesunięcie osi 0,25 m | — | WORKING_VALUE |

Wynik reguły przed zmianą (zmierzone 17.11): jezdnia 9,5 m na osi OSM → odstęp jezdni ≈ 2,6 m (12,12 − 9,5), brak pasa
awaryjnego (pobocze utwardzone 1,00 m); odcinki 3-pasowe 12 m przy rozstawie osi ~12,1 m stykały się — na wiadukcie
`s8-01` krawężnik pomostu stał w pasie sąsiedniej jezdni (`road_consistency_qa.json`: `obstacle_in_lane` 44,
`marking_off_carriageway` 29 na trasie).
Po zmianie (z modelu): odstęp linii wewnętrznych = rozstaw osi − 2 × 3,75 m = 4,6–5,0 m; odstęp krawędzi asfaltu =
rozstaw osi − 2 × 4,45 m = 3,2–3,6 m. Wartości z przebudowy i renderów: sekcja „Dowody”.

Pamięć importu Win64 (WORLD_MEMORY, 17.11, przed zmianą przekroju): Low 88,1 / 62,4 / 60,3 / 55,8 / 50,8 MB, High
185,2 / 154,0 / 144,3 / 132,5 / 130,8 MB (`s8-01` … `s8-05`). Trasy kontrolne: 2102 / 2084 / 2050 / 2133 / 843 m.

### s24 — przebudowa wszystkich 6 kafli (r8/r10, nowy PC, worktree LF) — zmierzone
Pas dzielący z sieci, którą budują meshe (`tools/worldgen/qa/s8_median_gap.py`, próbki co 10 m, p50 [p10–p90]):
| kafel | linie wewn. przed (s23) | linie wewn. po (s24) | krawędzie asfaltu po | udział 4,0–4,8 m (linie) |
|---|---|---|---|---|
| s8-01 | 4,84 | 4,72 [3,88–6,27] | 3,32 | 39 % |
| s8-02 | 4,87 | 4,84 [4,47–6,58] | 3,44 | 44 % |
| s8-03 | 5,52 | 5,16 [2,92–7,20] | 3,76 | 14 % |
| s8-04 | 5,00 | **4,61** [4,26–5,25] | 3,21 | 68 % |
| s8-05 | 4,62 | 4,34 [4,25–4,68] | 2,94 | 93 % |
| dk65-01 | 6,56 | 6,56 (bez zmian, rozstaw 13,86 m) | 5,16 | 0 % |
p90 > 5,5 m w s8-01..03 = odcinki przy wiaduktach i węzłach (rozstaw osi OSM 13–14,8 m), bez pomiaru → Otwarte 8.
Krawędzie asfaltu 2,9–3,4 m < zmierzone 3,45–4,0 m: generator kładzie 0,20 m opaski + 0,50 m asfaltu
(`PAVED_SHOULDER_MEDIAN`) od osi linii do krawędzi, ortofoto ~0,45 m → Otwarte 9.
road_consistency_qa (r10): s8-04 0 (było obstacle_in_lane 85 przy dziurze przejazdu), s8-05 0, s8-02 10, s8-03 8,
s8-01 22 (wszystko `lane_blind_end` / `arrow_no_exit` przy łącznicach — jak w s23), dk65-01 12 (jak przed).
qa.seams r10 (s8-01..05, dk65-01, dk65-03; 6 szwów): **0 FAIL, 0 UWAGA**. Fidelity r10 exit=0 dla 6 kafli.
WORLD_MEMORY import Win64 (s24) Low / High MB: s8-01 88,6 / 185,6; s8-02 62,9 / 154,5; s8-03 60,7 / 144,6;
s8-04 53,5 / 130,1; s8-05 50,9 / 130,9; dk65-01 69,6 / 169,5 (było 68,2 / 165,9). Trasy: 2102 / 2084 / 2050 /
2133 / 843 m. Rendery: `artifacts/s8-loop-s24/vqa-r8/*`, `vqa-r10/{s8-02,s8-05,dk65-01}` (nowe kamery
`s8_corner_eye`, `s8_corner_top` w `dk65-01/control_cameras_place.authored.json`).
Manifesty: region.yaml s23 miały `manifest_sha256` liczone z checkoutu CRLF (stary PC, autocrlf=true); s24 buduje z
checkoutu LF (= kanon, jak dk65-01 na main) → build_region przepisał je dla s8-01..05.

## Odrzucone
- **Reguła klasy w `xsec_rules.yaml` zamiast nadpisań** (`match: {class: [A], ref: S8}`): zmieniłaby też `dk65-01`
  i każdy przyszły kafel bez pomiaru położenia osi; przesunięcia osi (`center_offset`) i tak nie da się wyrazić regułą.
  Do rozważenia po zmierzeniu położenia osi OSM na ortofoto (Otwarte 3).
- **Link z trasy kontrolnej `dk65-01` na S8**: niemożliwy w obrębie kafla — patrz Otwarte 1. Trasy `dk65-01` nie zmieniono.

## Otwarte
1. **Ciągła trasa Białystok → S8 wymaga kafla `dk8-s8-jeroniki`** (ADR 0278, zdefiniowany, niezbudowany). Jezdnia
   S8 w stronę Warszawy (way 305447699) tylko ścina południowo-zachodni narożnik `dk65-01`: w grafie skierowanym
   węzeł na szwie z `s8-01` (768779,0; 595332,7) jest osiągalny wyłącznie z węzła na szwie południowym (769340,8;
   595199,0) — łącznice węzła Białystok Zachód w tę stronę leżą w `dk8-s8-jeroniki`. Potrzebne: budowa tego kafla
   + dwa linki (`dk65-01` → szew południowy, przejazd przez `dk8-s8-jeroniki` do szwu z narożnikiem `dk65-01`).
2. `dk65-01` (ADR 0205): dwa way S8 w narożniku kafla (183639794, 305447699) dostały te same nadpisania (skrypt,
   `TILES`) i kafel jest przebudowywany — bez tego jezdnie przeskakiwały w bok o ok. 1,0 m na szwie z `s8-01`
   (qa.seams: „droga urywa się na szwie”). Jezdnie `S19;65` w `dk65-01` zostają na regule klasy A (brak pomiaru).
7. **Przejazd pod S8 w `s8-04`** (way 222577653, `tunnel=yes`, `layer=-1`): wycięcie generatora zostawiało ok. 12 m
   dziury w obu jezdniach S8 (`obstacle_in_lane` 85, na trasie kontrolnej s 1548–1560 m). `bridge: true` (ADR 0206)
   zamykał dziury, ale flaga obejmuje cały way — 2 km S8 stawało się pomostem z krawężnikami i balustradami
   (render `vqa-r6/s8-04`). Przyjęto: way 222577653 poza grafem (`graph_filter.authored.json`), S8 w poziomie
   terenu, droga lokalna kończy się przy nasypie. Do zrobienia: flaga pomostu na zakres stacji i model przejazdu.
3. Położenie osi way OSM względem pasów (0,25 m, trzeci pas na zewnątrz) = WORKING_VALUE: zmierzyć
   `tools/worldgen/qa/ortho_xsec.py` na stacjach „czystych” każdego way, osobno odcinki 3-pasowe.
4. Łącznice (`motorway_link`): reguła klasy A bez zmian; pomiar QA: 7,85–7,95 m asfaltu, 1 pas ~5,75 m między liniami.
5. MOP-y, ekrany, bramownice e-TOLL, oznakowanie węzłów — po etapie „przejezdne” (D63).
6. Styki z `dw671-tykocin-*`, `tykocin`, `monki-*` powstają dopiero przy `s8-12` / `dw671-jezewo-*`.
8. (s24) Pas dzielący przy wiaduktach / węzłach (rozstaw osi > 12,8 m: s8-02/03 way 98599908, 183625709, 251431131,
   672979683; dk65-01 183639794, 305447699 — odstęp linii 5,6–7,3 m) bez pomiaru ortofoto: zmierzyć `ortho_xsec.py`
   i ewentualnie przesunąć tak samo.
9. (s24) Krawędzie asfaltu przy pasie dzielącym 0,25 m za blisko (model 0,70 m od osi linii, ortofoto ~0,45 m):
   wymaga parametru szerokości utwardzenia od strony pasa dzielącego per sekcja (dziś stała `PAVED_SHOULDER_MEDIAN`).
10. (s24) `dk65-01` render `s8_corner_eye`: między jezdnią S8 a równoległą łącznicą stoi podniesiony separator
    (krawężnik) zamiast malowanego klina — do sprawdzenia z ortofoto przy kaflu `dk8-s8-jeroniki`.
11. (s24) Przejazd pod S8 w `s8-04` nadal poza grafem (pkt 7) — S8 bez dziury i bez pomostu (render vqa-r8 route-*,
    road_consistency 0).

## Odtworzenie
```
uv run --project tools/worldgen python tools/worldgen/qa/s8_loop_plan.py
uv run --project tools/worldgen tools/worldgen/ingest.py --region s8-0x
uv run tools/worldgen/build_region.py --region s8-0x
uv run --project tools/worldgen python tools/worldgen/qa/s8_xsec_overrides.py [--check]
uv run --project tools/worldgen python tools/worldgen/qa/s8_median_gap.py [--ref <rev>] [--json out.json]
pwsh tools/worldgen/qa/s8_loop_s24.ps1 -Phase world|unity|post|pytest -Tiles <ids> -Tag <tag>   # s24, kolejność kroków
uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region s8-0x --context
uv run --project tools/worldgen python scripts/export-route.py --region s8-0x
uv run --project tools/worldgen tools/worldgen/fidelity/run.py --region s8-0x --fetch
python scripts/export-region-catalog.py --check
uv run --project tools/worldgen python tools/worldgen/streaming/tile_graph.py
uv run --project tools/worldgen python tools/worldgen/streaming/route_links.py
pwsh scripts/import-region.ps1 -Region s8-0x -BuildTarget Win64
pwsh scripts/visual-qa.ps1 -Scene World_s8-0x_High -Tier High -Pc -Width 1920 -Height 1080 -Lighting clear -BuildTarget Win64
```

## Dowody
`artifacts/s8-loop-s23/` (main): `run/*.exit` + logi kroków, `vqa/` (przed zmianą przekroju), `vqa-r3/` (po zmianie),
`seams/` (qa.seams). Uzupełnienie liczb po przebudowie: STATUS.md gałęzi `s8-loop-s23`.
