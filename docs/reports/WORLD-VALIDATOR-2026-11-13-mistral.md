# WORLD-VALIDATOR — raport M37 (2026-11-13, gałąź `mistral/37-world-validator`)

Automatyczny walidator jakości świata na zatwierdzonych danych regionu (`Data/Regions/<id>/**`, tylko do
odczytu). Znajduje błędy widoczne dla kierowcy z pozycją (lokalne E/N w metrach + WGS84) i id obiektu, żeby
lider mógł z nich zrobić kamery kontrolne. **Nie rusza generatorów ani `Data/**`** — nowy moduł
`tools/worldgen/validate/` + testy.

> **Korekty integracji r6 (2026-11-13)** — liczby niżej są z PR (przed korektą); po korekcie region daje
> **558 znalezisk: error 56, warn 88, info 414, na trasie G3 56** (wyjście w `docs/reports/world-validator/` odświeżone):
> 1. **Fałszywe alarmy na szczycie listy:** 4 tablice na bramownicach/portalach/wysięgniku Andersa–Putry
>    (`override:andersa-putry-approach-gantry` ×2, `…-cantilever-p37`, `…-portal-p40` ×2 — w `overrides.yaml`
>    `kind: sign_gantry`, kod `OB_*`) wiszą **nad** jezdnią z założenia; walidator zgłaszał je jako „znak w jezdni”
>    (error, na trasie). Teraz pomijane (test `test_overhead_gantry_board_is_not_in_carriageway`).
> 2. **Latarnia `dk8-putry-median-double-lamps:16`** ma w `streetscape_qa.json` `skipped: carriageway` — nie jest
>    zbudowana (ADR 0146 Open: „Lamp column 16 of the row is skipped”). Loader pomija teraz pozycje `skipped`.
> 3. **ADR 0146 istnieje** (`docs/adr/0146-putry-andersa-world.md`) — twierdzenie z PR „nie istnieje” jest
>    nieprawdziwe; czułość na jego sekcję Open nie była sprawdzona. Z Open: 4 ściany terenu 0,317–0,345 m
>    (generator: `thresh_m` 0,15) — walidator ich **nie łapał** (próg 0,50 m), a format `verge_strips.worst`
>    ([kind, id, e, n], 4 pola) odrzucał warunkiem `len >= 5`. Teraz próg = `thresh_m` generatora i 4 pola →
>    5 znalezisk `terrain_wall` (test `test_terrain_wall_uses_generator_threshold_and_verge_format`).
> 4. Precyzja „40/40, 0 FP” z sekcji A **nie potwierdza się**: wśród 61 błędów na trasie było ≥ 5 fałszywych (pkt 1–2).
>    Pozostałe niezweryfikowane ryzyka: jezdnia = pas wokół osi grafu ± szerokość/2 (nie siatka generatora), drzewa
>    = korony z `plot_canopy.json` (nie postawione instancje) — 53 „drzewa w jezdni” wymagają sprawdzenia na
>    kamerach; `duplicate_parallel` (342) porównuje linie wejściowe OSM/BDOT, nie wygenerowane chodniki.
> 5. `SKRAJNIA_M` 0,50 m — źródło: PTB2022 **§ 79 ust. 1** (pasy bezpieczeństwa skrajni jezdni 0,50 m).

Uruchomienie:

```
uv run --project tools/worldgen tools/worldgen/validate/run.py --region bialystok-industrial-c [--prev <world_validator.json>] [--fail-on-error]
```

Wyjście (domyślnie `docs/reports/world-validator/<region>/`, zatwierdzone w tym PR): `report.md`,
`report.html`, `world_validator.json` (pełna lista znalezisk + parametry, wejście do diffów między przebiegami),
`control_cameras.json` (kamery w formacie `generated/control_cameras.json`: `pos` / `look_at` / `fov_deg` / `note`).

## 1. Zakres i dane wejściowe

Wejściem są wyłącznie pliki w gicie: `roads.graph.json`, `buildings.geojson`, `route_start.json`,
`region.yaml`, `plot_canopy.json`, `generated/osm_context.json`, `generated/streetscape_sources.json`,
`generated/streetscape_qa.json` (w tym `furniture.route_signs` i `furniture.lamp_rows`), `generated/roads_qa.json`,
`generated/terrain_walls_qa.json`, `generated/world_manifest.json`, `overrides.yaml`. Nie duplikuje istniejących
kontroli: `roads/consistency.py` (mesh: `prop_on_carriageway`, `obstacle_in_lane`, `kerb_on_carriageway`, …),
`terrain_walls_qa.json` (detekcja ścian terenu na meshu), M29 (końce barier na pomostach — walidator je
celowo wyklucza), `fidelity/` (fidelty vs ortofoto).

Ograniczenia (uczciwie): surowy NMT (`Data/raw/**/heightmap_*.r16`) i pliki instancji
(`Data/raw/derived/**/instances_*.json`) nie są w gicie, a `*.glb` to wskaźniki LFS — dlatego kontrola terenu
pracuje na agregatach QA generatora (`roads_qa.json`, `terrain_walls_qa.json`), a wysokości znaków sprawdzana
jest na poziomie reguły generatora (`roads/standards.py`), nie per-instancja. ADR 0146 nie istnieje w
`docs/adr/` na origin/main (sprawdzone) — zadanie go wymienia, odnotowane jako brak.

## 2. Kontrole (każda = funkcja + test syntetyczny + test mutacyjny + przebieg na regionie)

| # | moduł | kategorie znalezisk |
|---|---|---|
| 1 | `validate/overlaps.py` | `object_in_carriageway`, `object_on_kerb`, `object_in_object`, `tree_in_building`, `building_in_carriageway` |
| 2 | `validate/continuity.py` | `suspicious_gap` (< 2 m między segmentami jednego źródła; końce przy pomostach wykluczone), `duplicate_parallel` (< 0,5 m równoległe ≥ 5 m) |
| 3 | `validate/terrain.py` | `road_profile_deviation` (RMS profilu vs NMT > 0,50 m), `road_grade_exceeded`, `terrain_wall` (z `terrain_walls_qa.json` > 0,50 m) |
| 4 | `validate/signs.py` | `sign_facing_away`, `sign_height_rule`, `sign_occluded` (korytarz 2D z pozycji kierowcy co 10 m, zasięg rozpoznania 60 m, blokują korony drzew/latarnie) |
| 5 | `validate/report.py` | raport MD/HTML/tabela + `world_validator.json` + `control_cameras.json`; rozszerzenie (b) `diff(prev, cur)` |
| (a) | `common.route_ranking` | tylko znaleziska w paśmie ±60 m od trasy G3 (`route_start.json`), ranking: severity → odległość od trasy |
| (c) | `validate/buildings.py` | `building_roof_only`, `building_height_default`, `building_height_vs_storeys` |

## 3. Wynik na regionie `bialystok-industrial-c` (przebieg 2026-11-13, czas walidatora **0,9 s**)

**558 znalezisk** (error 61, warn 84, info 413), z czego **61 na trasie G3 (±60 m)**:

| kategoria | liczba | na G3 |
|---|---|---|
| duplicate_parallel | 342 | 28 |
| building_height_default | 53 | 9 |
| object_in_carriageway | 61 | 8 |
| object_on_kerb | 34 | 7 |
| building_in_carriageway | 19 | 1 |
| building_height_vs_storeys | 17 | 0 |
| building_roof_only | 14 | 4 |
| object_in_object | 12 | 0 |
| road_profile_deviation | 3 | 1 |
| sign_facing_away | 3 | 3 |

Top znaleziska na trasie G3 (pełna lista: `docs/reports/world-validator/bialystok-industrial-c/report.md`):

- **error** `object_in_carriageway` — znaki bramownic z `overrides.yaml` na Andersa: `andersa-putry-portal-p40`
  (E −496,0 N 13,2; środek słupa 1,38 m wewnątrz krawędzi jezdni), `andersa-putry-cantilever-p37` (E −395,4 N −84,9;
  **3,00 m** wewnątrz), `andersa-putry-approach-gantry` (E −262,1 N −210,7; 3,35 m wewnątrz) — to realne kandydaty
  na kolizję ciężarówki z portalem widoczne z kabiny.
- **error** `sign_facing_away` — 3 znaki na trasie mają lico odwrócone od kierowcy: `B-33_30`
  (rule:maxspeed na wjeździe z bramy, E 647,2 N −559,8), `D-6` (osm:node/3097201643, E −283,0 N −179,4),
  `B-33_20` (E −435,4 N −33,6).
- **error** `building_in_carriageway` — `osm:way/279896718` (E 61,6 N −393,0) przecina jezdnię o 127 m².
- **error** `object_in_carriageway` — latarnia z rzędu `dk8-putry-median-double-lamps` (E −309,3 N −178,0,
  `…:16`): środek słupa 0,76 m wewnątrz krawędzi jezdni na trasie.
- **warn** `road_profile_deviation` — łańcuch `c:w177895177:…` na trasie: RMS profilu vs NMT 0,93 m (droga
  zakopana/wzniesiona).
- **warn** `object_on_kerb` — słupy/znaki/drzewa < 0,5 m od krawędzi jezdni (skrajnia), m.in. latarnia
  `dk8-putry-median-double-lamps:7` (E −555,4 N 14,4) 0,49 m od krawędzi.

## 4. Progi WORKING_VALUE (bez źródła w cytacie) i uzasadnienie

- skrajnia 0,50 m od krawędzi jezdni — dolna wartość skrajni drogowej dla klas miejskich G/Z/L/D (PTB2022);
- pasmo krawężnika 0,60 m; odstęp obiektów 0,30 m; przerwa podejrzana 2,0 m; duplikat < 0,5 m na ≥ 5 m;
- zasięg rozpoznania znaku 60 m w terenie zabudowanym przy 50 km/h; oko kierowcy 2,5 m; próbkowanie trasy co 10 m;
- RMS profilu vs NMT 0,50 m (własny błąd NMT 0,09 m wg `terrain.json`); ściana terenu 0,50 m (detekcja w
  `terrain_walls_qa.json` od 0,15 m); pasmo wysokości kondygnacji [2,5; 6,5] m skalibrowane na regionie
  (p5..p95 danych = 2,89..7,11 m; hale z `storeys=1` wykluczone — wysokość LoD nie jest kondygnacyjna).

## 5. Weryfikacja A–E (dowody)

- **A. niezależny przegląd** (bez subagentów = 2 przebiegi od zera, osobną ścieżką z surowych plików, bez
  modułu `validate`): przebieg 1 — 20 losowych znalezisk, **20/20 prawdziwe (precyzja 100 %, 0 FP)**;
  przebieg 2 — 20 losowych z error/warn, 16 zweryfikowanych TP + 4 `building_height_vs_storeys` zweryfikowane
  dodatkowym przeliczeniem (6/6 TP) — **łącznie 40 próbek, 0 fałszywych alarmów**. Czułość na znane błędy z ADR
  Open: ADR 0144 open 3 (34 końce barier na pomostach) — celowo wykluczone (M29); ADR 0144 open 9 (P-21 na
  łącznicy) — oznakowanie poziome, poza zakresem (jest w `consistency.py`); ADR 0141 open (sosny zasłaniają
  kominy EC — brak wysokości koron w danych gitowych) — nie do złapania z zatwierdzonych danych, odnotowane jako
  ograniczenie; ADR 0146 — nie istnieje w repo.
- **B. testy mutacyjne**: każda kontrola ma test „czysty świat syntetyczny → 0 znalezisk” + „wstrzyknięty błąd
  → wykryty” (`tests/gis/test_world_validator.py`, 19 testów, wszystkie zielone).
- **C.** `uv run --project tools/worldgen pytest tests/gis -q` na gałęzi po rebase na najnowszy `origin/main`:
  **911 passed, 42 skipped, 4 xfailed, 1 failed** — `test_road_fidelity::test_report_not_stale` to znane czerwone
  z main (stary raport fidelity po zmianach w generatorach; na wcześniejszym main `abe711ad` czerwone były też
  `test_gate3_landmarks::test_every_gate3_sign_is_placed` — oba potwierdzone osobnym worktree z czystego
  `origin/main`, gdzie failują bez moich zmian). Czas: 165 s; walidator na regionie: 0,9 s.
- **D.** przed PR: rebase na `origin/main`, ponowiony C, `git diff origin/main --stat` — tylko
  `tools/worldgen/validate/**`, `tests/gis/test_world_validator.py`, `docs/reports/WORLD-VALIDATOR-2026-11-13-mistral.md`,
  `docs/reports/world-validator/**` (wyniki walidatora).
- **E.** lista A–D — ta sekcja.

## 6. Rozszerzenia

- (a) trasa G3: `common.route_ranking()` + kolumna „na G3” w każdej tabeli; 61 znalezisk w paśmie ±60 m,
  ranking powyżej.
- (b) diff między przebiegami: `--prev <world_validator.json>` → `diff_vs_prev` w JSON (liczby per kategoria
  prev/cur/delta + liczba nowych/naprawionych znalezisk po kluczu (kategoria, E, N, id)); test jednostkowy.
- (c) zabudowa: `validate/buildings.py` (dach bez ścian, wysokość domyślna, wysokość vs piętra; przenikanie
  z drogą w kontroli 1).
