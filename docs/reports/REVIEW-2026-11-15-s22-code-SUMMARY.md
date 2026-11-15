# Recenzje kodu s22 (chmura D, runda 3, D9) — podsumowanie dla lidera

Data: 2026-11-15. Część A (#109–#116, ten plik + 8 raportów) i część B (#117–#125, drugi agent, ta sama gałąź `reviews-code-s22`).
Pełne raporty: `docs/reports/REVIEW-2026-11-15-s22-code-<nr>.md`. Chmura niczego nie scala ani nie zatwierdza; werdykty są też
komentarzami w PR. main w chwili recenzji: `bfe10923f`.

## Część A — #109–#116

| PR | gałąź / ADR | werdykt | najważniejsze poprawki | kolejność |
|---|---|---|---|---|
| #109 | fences-0239 / 0239 | **SCAL** (po EditMode + kadrach Low/High) | P2: kamery `r10_fence_*`, `furniture-fence` nie istnieją w `control_cameras.json`; P2: brak `DepthNormals` (SSAO Ultra) | 1 |
| #110 | shadows-0240 / 0240 | **SCAL** (po `setup-project` bez diffu, EditMode, VQA Low clear) | P2: komendy VQA z kamerami G3 wymagają `-Gate3 …/gate3_cameras.json`; P2: kryterium acne przy 0,4/0,3 | 2 |
| #111 | gpu-ab-0241 / 0241 | **SCAL** (po EditMode + `-DryRun`) | P2: ujednolicić kamery A/B z #110 (`s0212/s1282` vs `s0412/s1682`); po #110 wariant `thinshadow-on` | 3 |
| #113 | jackknife-0228 / 0228 | **SCAL** (po EditMode/PlayMode) | P1 (przed feel testem B-075, nie przed scaleniem): prześwit 7 mm naczepa–kabina → scenariusz skrętu 55–60° z `ContactPoints == 0`, ewentualnie korekta geometrii pudła | 4 |
| #115 | ring-0231 / 0231 | **SCAL** | P2: VQA `-Scene World_<id>` (nie `WorldC`); po budowie kafli odświeżyć katalog regionów (#104) i `tile_graph.json` (#114) | 5 |
| #114 | streaming-0235 / 0235 (baza #104 ✓) | **FIX** | P1: streaming opt-in (`stream=1`) do pomiaru PSS/klatek A16 — dziś włącza się sam w APK `-Regions d67`; P1: odrodzenie nad pustką po wyładowaniu kafla startowego | 6 |
| #116 | g3-poses-0246 / 0246 | **SCAL** (po EditMode + próbie `-Only 1-2`) | P2: `CaptureCameraTier.Apply` woła pełne `QualityProfileApplier.Apply` (opis „tylko kamera” nieścisły); P2: `g3_poses.json` w APK Release | 7 |
| #112 | regionpacks-0234 / 0234 | **FIX** | P1: paczki bez scen `_Tile` (#114); P1: `RegionPackService.Prepare` robi globalne `UnloadAll(true)` — wyklucza dwa regiony naraz. Albo licznik referencji, albo w ADR 0234/0235 zapis „streaming tylko między regionami w APK”. Załącznika A (menu) nie nakładać przed decyzją | 8 |

Żaden PR części A nie zmienia `ProjectSettings/`, `Packages/`, asmdef ani wspólnych scen/prefabów (sprawdzone na liście plików).
#110 zmienia assety tierów (`QualityProfile.asset`, `URP_Low.asset`) zgodnie z fabryką i migracją `revision 240` — lider
potwierdza `setup-project` bez diffu. Zero nowych alokacji w pętli jazdy; fizyka w stałym kroku (#113 w rdzeniu, #114 rebase
w `FixedUpdate` z `DefaultExecutionOrder(-950)`).

## Konflikty

### Tekstowe (scalenie próbne wszystkich 8 gałęzi po kolei na `bfe10923f`)
Kolejność próby: #109 → #110 → #111 → #112 → #114 → #113 → #115 → #116. Jedyne konflikty:
- `STATUS.md` (add/add lub content) w #109, #110, #111, #112, #114 → przy każdym scaleniu wersja main (pliki robocze agentów).
- `docs/PERFORMANCE_BUDGETS.md` #109 × #111 (obie dopisują sekcję w tym samym miejscu, ~l. 202) → zachować obie sekcje.
Kod C# i Python scala się automatycznie. Pary sprawdzone `git merge-tree`:
- **#109 × #110**: `RegionImporter.cs` — inne hunki (#110 l. ~305 `_LowNoShadow`, #109 l. ~459 shader siatki); po scaleniu oba obecne. Semantycznie spójne: #110 wyklucza `fence_*_mesh` ze swojej reguły (`ThinShadowCasterPolicy.IsThinMaterial`), cień siatki wyłącza #109 (`FenceMeshCoverage.CastsShadow=false`).
- **#110 × #111**: `RenderOverrides.cs` — po scaleniu oba zestawy (`ThinShadows` w `Any/Parse/Describe/ApplyTo` i hak `GpuAbOverrides`). `QualityProfile.CurrentRevision = 240` i koniec łańcucha migracji należą do #110; #111 nie podbija rewizji → kolejność nie psuje migracji.
- **#109 × #111**: tylko dokumenty.
- `QualityProfileApplier.cs`: zmienia go tylko #111 (1 linia); #116 tylko woła `Apply`.

### #112 (paczki) × #114 (streaming) — konflikt koncepcyjny, bez wspólnych plików
| | #112 regionpacks-0234 | #114 streaming-0235 |
|---|---|---|
| jednostka treści | pełna scena `World_<id>[_High]` w bundlu + `common` + `<id>-data` | scena `World_<id>[_High]_Tile` (sam root regionu + trasa) w APK przez `-Regions` |
| ile regionów naraz | **jeden** (`Prepare` → `UnloadAll(true)`; `activeSceneChanged` zwalnia bundle) | **2–4** kafle (bieżący + sąsiedzi, budżet MB) |
| ładowanie | `SceneManager.LoadScene` (Single) po `Prepare` | `LoadSceneAsync(Additive)` + aktywacja chunków ≤ 2 ms/klatkę |
| wykrycie dostępności | `Application.CanStreamedLevelBeLoaded` po wczytaniu bundla | `CanStreamedLevelBeLoaded(_Tile)` **raz przy instalacji** streamera |

Skutek: po scaleniu obu bez poprawek region z paczki nigdy nie będzie sąsiadem do streamingu (szew zamknięty, co jest
bezpieczne), a gdyby ktoś dopiął `Prepare` do streamera, wczytanie sąsiada zniszczyłoby obiekty bieżącego regionu.
Do tego `common` dubluje w pamięci materiały/ciężarówkę z APK przy przejściu C (APK) → region z paczki (44–74 MB ESTIMATED),
a budżet świata A16 Low z #114 to 200 MB.
**Rekomendacja:** scalić **#114 najpierw** (po FIX P1: opt-in) — korytarz D67 w APK mieści się w ≤ 2 GB wg ADR 0229 i to jest
dziś jedyny kanał (sideload). **#112 potem** z jedną z dwóch dróg do wyboru przez lidera/właściciela:
(a) pakować też `_Tile` i przejść na licznik referencji bundli per region (`Acquire/Release` w `IRegionPackProvider`, wołane
przez `WorldStreamer.BeginLoad/BeginUnload`), albo (b) zapisać w ADR 0234 i 0235, że streaming działa tylko między regionami
w APK, a region z paczki to pojedyncza scena z zamkniętymi szwami. Załącznik A (menu) nakładać dopiero po tej decyzji.
Scalenie #112 przed #114 jest technicznie bezpieczne (runtime nieużywany), ale utrwala model „jeden region”.

### Inne zależności danych
- #115 nie dodaje `region.yaml` (powstanie przy `build_region`) → po budowie kafli pierścienia padnie test świeżości
  `test_tile_graph_0235` (#114) i test katalogu regionów (#104), dopóki nie uruchomi się `tile_graph.py` i
  `export-region-catalog.py`. Dopisać oba do kroku regeneracji mapy.

## Proponowana kolejność scalania #109–#116
1. **#109** fences (STATUS → main) → 2. **#110** shadows (`setup-project` bez diffu) → 3. **#111** gpu-ab (`PERFORMANCE_BUDGETS.md` = obie sekcje; dodać wariant `thinshadow-on`)
→ 4. **#113** jackknife (osobny obszar; P1 przed feel testem) → 5. **#115** ring (definicja) → 6. **#114** streaming po FIX P1 (opt-in, odrodzenie)
→ 7. **#116** g3-poses (po #110, żeby zrzuty A16 pokazały docelowy Low) → 8. **#112** regionpacks po FIX P1 albo z zapisanym ograniczeniem.
#109–#111 to rendering Low — po nich jeden reimport C (`import-region.ps1 -Region bialystok-industrial-c -SkipCopy`) + VQA Low/High +
A16, najlepiej w ramach planowanej jednej przebudowy C (HANDOVER s22).

## Testy (chmura, bez Unity/GPU/telefonu/Data/raw)
| PR | uruchomione | wynik |
|---|---|---|
| #109 | `pytest tests/gis/test_dojbld_0185.py test_furniture_0120.py test_furniture_r1.py` | 33 passed |
| #110 | `thin_shadow_audit.py --check` | nie odtworzone (`street_props.glb` = wskaźnik LFS w klonie) |
| #111 | `pytest tools/perf/tests` | 61 passed |
| #112 | `estimate-region-packs.py` | tabela = ADR §7 |
| #113 | `dotnet test tools/physics-runner -c Release` (.NET 8 user-local); pełny runner | 295/295; 145 scenariuszy / 879 checków PASS |
| #114 | `pytest tests/gis/test_tile_graph_0235.py` | 7 passed |
| #115 | `pytest tests/gis/test_ring_0231.py test_knyszynska_0208.py` | 42 passed |
| #116 | `dotnet test tests/g3poses/G3PoseTests.csproj`; `pytest tests/gate3`; `g3_poses.py check` | 16/16; 24 passed + 1 fail znany z main; OK (42) |
| scalenie 8 PR | `pytest tests/gis tests/gate3` (bez znanego faila gate3) + `tools/perf/tests` (61 passed) na scaleniu wszystkich 8 gałęzi | **1391 passed, 54 skipped, 4 xfailed, 3 failed** — dokładnie 3 znane faile main (forest_0187 edge texture, road_fidelity stale, world_v31 forest HLOD); 0 nowych |

**Nowy znany czerwony test spoza listy preambuły:** `tests/gate3/test_gate3_meta.py::test_evidence_apk_info_legacy_and_dirty`
pada na czystym main `bfe10923f` (`discover_apk_info` zwraca `git_sha=None` dla nazwy `…-f6abb8b001-dirty.apk`). Nie jest
związany z żadnym PR części A.
Nieuruchomione wszędzie: kompilacja Unity, EditMode/PlayMode, visual-qa, APK, A16 — komendy w raportach.

## Budżet
- Render: #109 0 tris/0 draws (zweryfikowane: brak zmian generatora; 15 719 m płotu panelowego w C wg `streetscape_qa.json`),
  #110 tylko w dół (casterzy cieni Low, ESTIMATED), #111/#112/#115/#116 0, #113 0 (CPU +0,4 µs/krok wg autora).
  **#114: kadr przy szwie renderuje dwa kafle** — bez szacunku i pomiaru; region C już 2,02 M tris High (`stretch_04`).
  Zmierzyć na telefonie przed włączeniem streamingu domyślnie.
- Pamięć: #114 świadomie przekracza 200 MB Low na parach C+Maczka (277 MB), Maczka+Kleeberga (310), Kleeberga+Knyszyńska (273)
  (ESTIMATED z ADR 0229) przy PSS C 900–926 MB / cel 1000 MB. #112 `common` +44–74 MB przy przejściu APK → paczka.

## Część B — #117–#125
_(dopisuje drugi agent w tym pliku)_

## Część B — #117–#125 (recenzent D9-B)

| PR | gałąź / ADR | werdykt | najważniejsze poprawki | kolejność |
|---|---|---|---|---|
| #117 | controls-0243 / 0243 | **SCAL** (po EditMode/PlayMode + A/B `mirrorrate` A16) | P2: płynność okienek 10 Hz / wypukłych 1,9 Hz na Low do oceny właściciela; zapisane 900° zostaje po migracji v5 (logcat `range=`) | dowolnie (C#) |
| #118 | perf-loop-0244 / 0244 | **SCAL** (po EditMode/PlayMode + Profiler A16) | P2: otwarte P1 raycasty i `WriteSummary` jako osobne zadania z pomiarem | dowolnie (C#) |
| #119 | tests-hygiene-0245 / 0245 | **SCAL** | zmienia strumień losowy płaszcza lasu we wszystkich regionach z BDOT, więc scalić **przed** przebudową C; P2: zapisać to w ADR | C-1 |
| #120 | summer-cd-0216b / 0216b | **SCAL** (po EditMode) | P2: `lamp_policy()` bierze pierwszy override (walidacja ≤ 1); `STATUS.md` z main | C-2 |
| #122 | dojlidy-0242 / 0242 | **SCAL** (po kompilacji C# + renderze Dojlid) | musi wejść **przed #123** (baseline i `storey_plan`) | C-3 |
| #123 | typology-0238 / 0238 | **FIX** | P1 `test_typology_0238.py:305` ma wpisane na sztywno `2022535`, test pada po budget-fix (1 986 314); P1 baseline Dojlid przeliczyć po #122 (`:324` pada w scaleniu); P1 konflikt `storey_plan` z #122 (usunąć zduplikowane `lo, hi`) | C-4 (rebase po #122) |
| #124 | signs-c-0236 / 0236 | **SCAL** (po przebudowie C + kamerach Low) | P1-L: po buildzie `gate3_landmarks.stale` i kratownica LOD1 na Low; P2: skip `test_every_gate3_sign_is_placed` zawęzić do 4 nowych E-15 | C-5 |
| #125 | kerbs-0237 / 0237 | **SCAL** (łatka haka osobnym commitem) | P1-L: `0237-build-world-hook.patch` nałożyć po budget-fix, przed przebudową; P2: zamiast `.patch` rebase z hakiem w kodzie; P2: próg `test_yard_wear` | C-6 |

### Pytania lidera — rozstrzygnięcia
- **#124, skip i progi:** skip `test_gate3_landmarks.py:142` zdejmuje się sam po przebudowie, bo `signs_route.py:407` zawsze
  zapisuje `diagrams_replaced`. Jest więc uczciwy, ale za szeroki (P2). Progi LOD1 kratownicy 300→200 i 150→100 wynikają ze
  zmiany konstrukcji (krzyżulce LOD1 jako paski). Przeliczone prototypy: bramownica 16 m LOD1 552 → 232, wysięgnik 240 → 112.
  Tablica 0,85 m wynika z Tab. 9.5.4, a LOD1 tablicy = 4 tris z nowej konstrukcji. **Uczciwe.**
- **#123, `BASE_M` 1,5:** pomiar odtworzony niezależnie. n = 8821, mediana `h − 3n` = 1,50, MAE 1,295 (1,5) < 1,353 (2,0) < 1,365 (1,0).
  Wartość 2,0 z recenzji była gorsza od dotychczasowej. **Autor ma rację.**
- **#125, behaton:** pobrałem skan Poly Haven `concrete_pavers` (1,92 m) i policzyłem autokorelację FFT: 274,7 mm wzdłuż i
  319,7 mm na dwa rzędy, czyli liczby autora. Kostka była o 37 % za długa i trzeba ją zmniejszyć (×0,732).
  **Mnożnik ×1,16 z recenzji działał w złą stronę.**
- **#125, łatka a budget-fix-s21:** `git apply --check` przechodzi na drzewie main + budget-fix + wszystkie PR C/D. Budget-fix
  zmienia w `build_world.py` tylko `_src_tally` (diagnostyka), więc hunki nie kolidują. Decymacja obrzeży z budget-fix
  (`paved._edge_keep`) obejmuje też nowe materiały `EDGED` z #125.

### Konflikty grupy C/D — scalenie próbne
Kolejność próby: `origin/main` → budget-fix-s21 → #120 → #123 → #124 → #125 → #122.
- Jedyny **rzeczywisty** konflikt jest w `streetscape/buildings_mesh.py:storey_plan` (#122 × #123). Rozwiązanie: zostawić
  `if p.get("storeys_fixed"): return …` z #122 i usunąć jego linię `lo, hi = …`, którą #123 przeniósł wyżej. Gdyby linia
  została, nadpisałaby zakres kondygnacji kamienicy. To cichy błąd.
- `overrides.yaml` C i Dojlid (#120 × #125, oba dopisują na końcu): suma bloków. YAML poprawny, bez duplikatów id
  (C 190, Dojlidy 47 wpisów).
- `docs/LICENSES.md` (#123) i `docs/adr/README.md` (#119 × #125): suma. `STATUS.md`: add/add w każdym PR, brać wersję z main.
- `stage.py` (#124 +1, #125 +5, budget-fix), `materials.py` (#122, #123, #125), `props.py`/`furniture.py` (#124, #120,
  budget-fix): git scala czysto.
- Testy w scaleniu próbnym (`test_typology_0238`, `test_dojlidy_0242`, `test_pavements_0237`, `test_direction_signs_0236`,
  `test_summer_cd_0216b`, `test_lamp_led_0216`, `test_dojbld_0185`, `test_dojind_0196`, `test_budget_0221`, `test_gate3_landmarks`,
  `test_g3b_lowread`, `test_furniture_0162`): **150 passed, 2 failed, 2 skipped, 1 xfailed**. Oba faile pochodzą z #123
  (P1 wyżej).

### Budżet kamer C (High; ESTIMATED do `build_world`)
| kamera | main | budget-fix-s21 | #123 | #124 | #125 / #120 / #122 | suma |
|---|---|---|---|---|---|---|
| stretch_04 | 2 022 535 | 1 986 314 | −693 | −224 | 0 | **≈ 1 985 397** |
| route_onramp_andersa_above | 1 993 338 | 1 966 981 | −885 | −544 | 0 | **≈ 1 965 552** |
| route_onramp_andersa | 1 884 422 | 1 852 645 | −1 053 | −544 | 0 | ≈ 1 851 048 |
| fire_station_abeam | 1 183 284 | ≤ main | −382 | +448 | 0 | +66 względem main |

Low: stretch_04 938 349 −299 (#123). Słupki E-15 z #124 dają +40/+48 na 3 kamerach; #123 kompensuje to z nawiązką
(−227…−279). Delty #123 odtworzyłem harness'em autora, a baseline wygenerowałem niezależnie kodem z main (wyszedł
identyczny). Delty #124 zgadzają się z przeliczonymi prototypami. #125 daje 0 tris z konstrukcji (asercja w
`pavements.run`). Wpływ #119 (las) jest UNVERIFIED, to szum. Materiały: +6 submeshy LOD0 C (#123) i +1…3 (#125), bez
ryzyka przy budżecie draws High 800 (stretch_04 ma 153).

### Kolejność scalania C/D i jedna przebudowa
1. budget-fix-s21 (0221, lokalnie) → 2. #119 → 3. #120 → 4. #122 → 5. #123 po FIX (rebase na main z #122, nowy baseline Dojlid,
bez `2022535`) → 6. #124 → 7. #125 + commit z łatką haka. #117 i #118 można scalić niezależnie (C#).
Potem **jedna przebudowa**:
1. opcjonalnie `uv run tools/worldgen/build_region.py --region bialystok-industrial-c` (BASE_M 1,5 i tagi OSM z #123; wymaga
   Data/raw, po nim ponowny pomiar);
2. `uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region bialystok-industrial-c` oraz `--region bialystok-dojlidy`;
3. `pwsh scripts/import-region.ps1 -Region bialystok-industrial-c -Build` (i Dojlidy);
4. `uv run --project tools/worldgen python -m pytest tests/gis -q` (gate3 ma się wykonać, nie skip);
5. kontrola `streetscape_qa.json`: `mesh_budget.frame_estimate` (stretch_04 < 2 M), `pavements.tris_in == tris_out`, `gate3_landmarks.stale`;
6. visual-qa WorldC Low/High i Dojlidy;
7. `pwsh scripts/test.ps1 -Platform EditMode`;
8. APK + pomiar na A16.

### Testy części B (chmura)
`dotnet test` (SDK 8.0 user-local): controls-runner 13/13 (#117), loop-runner 30/30 (#118). pytest na gałęziach (deselect znanego
`test_frame_budget_with_forest_hlod`):

| PR | wynik |
|---|---|
| #124 | 295 passed, 3 skipped |
| #125 | 119 passed, 2 skipped |
| #123 | 250 passed, 5 skipped, 1 xfailed |
| #120 | 90 passed, 1 skipped |
| #122 | 173 passed, 4 skipped, 1 xfailed |
| #119 | 27 passed, 1 skipped (LFS), 1 xfailed; na main te same pliki: 3 failed |

Nieuruchomione: Unity (EditMode/PlayMode), build_world, kamery, visual-critic, APK, A16.
