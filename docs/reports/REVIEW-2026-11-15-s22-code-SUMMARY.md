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
| scalenie 8 PR | `pytest tests/gis tests/gate3` + `tools/perf/tests` na `rv-combo` | _wynik dopisany niżej_ |

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
